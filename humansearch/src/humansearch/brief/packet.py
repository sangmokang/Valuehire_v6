"""HS-13.09 — 서치 패킷을 git 밖 디렉터리에 0600 으로 저장하고 독립 readback 으로 대조한다.

계약: docs/engineering/humansearch-hs13-position-brief-goal-2026-09-10.md §5 packet.py · §7 D7.
후보자 PII 는 파일에만 남는다 — 이 모듈은 표준출력·로그를 한 줄도 내지 않는다.
시계·네트워크 접근 0. 저장 위치는 호출자가 Path 로 주입한다(경로 리터럴 0).
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import re
import tempfile
import threading
import typing
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import fields, is_dataclass
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from types import UnionType
from typing import Union, get_args, get_origin

from .types import JdSource, PositionSpec, _reject
from .types_packet import _PACKET_ID, SearchPacket

__all__ = [
    "PacketStore",
    "canonical_store_dir",
    "ensure_store_dir",
    "from_json",
    "packet_id",
    "require_channel",
    "to_json",
]

# D7: 디렉터리 0700 · 파일 0600. 값을 한 곳에만 두어 모듈끼리 갈라지지 않게 한다.
DIR_MODE = 0o700
FILE_MODE = 0o600

_HINTS: dict[type, dict[str, object]] = {}


def _hints(cls: type) -> dict[str, object]:
    """`from __future__ import annotations` 로 문자열이 된 필드 타입을 실제 타입으로 푼다."""
    cached = _HINTS.get(cls)
    if cached is None:
        cached = dict(typing.get_type_hints(cls))
        _HINTS[cls] = cached
    return cached


def encode_value(value: object, path: str = "value") -> object:
    """frozen dataclass 묶음을 JSON 이 담을 수 있는 값으로 바꾼다(date/Enum/튜플 포함)."""
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, Enum):
        return encode_value(value.value, path)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, tuple):
        return [encode_value(item, f"{path}[{index}]") for index, item in enumerate(value)]
    if isinstance(value, dict):
        encoded: dict[str, object] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                _reject(f"{path} 의 키가 문자열이 아니다")
            encoded[key] = encode_value(item, f"{path}.{key}")
        return encoded
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: encode_value(getattr(value, field.name), f"{path}.{field.name}")
            for field in fields(value)
        }
    _reject(f"{path} 를 JSON 으로 옮길 수 없다: {type(value).__name__}")


def dumps_value(value: object) -> str:
    """결정적 JSON 직렬화 — 같은 값은 항상 같은 바이트열이어야 readback 해시가 성립한다."""
    return json.dumps(
        encode_value(value), ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )


def _decode_union(hint: object, raw: object, path: str) -> object:
    members = [arg for arg in get_args(hint) if arg is not type(None)]
    if raw is None:
        if len(members) == len(get_args(hint)):
            _reject(f"{path} 는 null 일 수 없다")
        return None
    if len(members) != 1:
        _reject(f"{path} 의 계약 타입이 두 갈래를 넘는다")
    return _decode(members[0], raw, path)


def _decode_tuple(hint: object, raw: object, path: str) -> object:
    if not isinstance(raw, list):
        _reject(f"{path} 는 리스트여야 한다")
    members = get_args(hint)
    if len(members) == 2 and members[1] is Ellipsis:
        return tuple(_decode(members[0], item, f"{path}[{i}]") for i, item in enumerate(raw))
    if len(members) != len(raw):
        _reject(f"{path} 의 원소 수가 {len(members)} 가 아니다: {len(raw)}")
    return tuple(_decode(members[i], raw[i], f"{path}[{i}]") for i in range(len(members)))


def _decode_dataclass(hint: type, raw: object, path: str) -> object:
    if not isinstance(raw, dict):
        _reject(f"{path} 는 객체여야 한다")
    names = {field.name for field in fields(hint)}
    keys = {str(key) for key in raw}
    unknown = tuple(sorted(keys - names))
    if unknown:
        _reject(f"{path} 에 계약에 없는 키가 있다: {unknown}")
    missing = tuple(sorted(names - keys))
    if missing:
        _reject(f"{path} 에 계약 필드가 빠졌다: {missing}")
    hints = _hints(hint)
    arguments = {name: _decode(hints[name], raw[name], f"{path}.{name}") for name in sorted(names)}
    factory = typing.cast("typing.Callable[..., object]", hint)
    return factory(**arguments)


def _decode(hint: object, raw: object, path: str) -> object:
    origin = get_origin(hint)
    if origin is UnionType or origin is Union:
        return _decode_union(hint, raw, path)
    if origin is tuple:
        return _decode_tuple(hint, raw, path)
    if hint is str:
        if not isinstance(raw, str):
            _reject(f"{path} 는 문자열이어야 한다")
        return raw
    if hint is int:
        if isinstance(raw, bool) or not isinstance(raw, int):
            _reject(f"{path} 는 정수여야 한다")
        return raw
    if hint is datetime:
        return _decode_datetime(raw, path)
    if hint is date:
        return _decode_date(raw, path)
    if isinstance(hint, type):
        if issubclass(hint, Enum):
            for member in hint:
                if member.value == raw:
                    return member
            _reject(f"{path} 는 계약에 없는 값이다")
        if is_dataclass(hint):
            return _decode_dataclass(hint, raw, path)
    _reject(f"{path} 의 계약 타입을 해석할 수 없다")


def _decode_datetime(raw: object, path: str) -> datetime:
    if not isinstance(raw, str):
        _reject(f"{path} 는 ISO 문자열이어야 한다")
    try:
        return datetime.fromisoformat(raw)
    except ValueError:
        _reject(f"{path} 가 ISO datetime 형식이 아니다")


def _decode_date(raw: object, path: str) -> date:
    if not isinstance(raw, str):
        _reject(f"{path} 는 ISO 문자열이어야 한다")
    try:
        return date.fromisoformat(raw)
    except ValueError:
        _reject(f"{path} 가 ISO date 형식이 아니다")


def loads_value(hint: type, text: str) -> object:
    """계약 타입을 알고 JSON 을 되돌린다. 계약 밖 모양은 전부 BriefInputError."""
    if not isinstance(text, str):
        _reject("복원할 JSON 은 문자열이어야 한다")
    try:
        raw = json.loads(text)
    except json.JSONDecodeError:
        _reject("JSON 을 읽을 수 없다(손상된 파일)")
    return _decode(hint, raw, hint.__name__)


def jd_text_sha8(jd: JdSource) -> str:
    """packet_id 의 내용 식별자 — jd.text 의 sha256 앞 8자리."""
    return hashlib.sha256(jd.text.encode("utf-8")).hexdigest()[:8]


def packet_id(position: PositionSpec, jd: JdSource) -> str:
    """`{clickup_id}-{sha8}`. 날짜를 담지 않는다 — 시계 인자도 받지 않는다(HS-13.09c).

    같은 포지션·같은 JD 는 언제 만들어도 같은 식별자여야 한다. 날짜가 섞이면 자정을 넘긴
    재생성이 새 장부 파일 이름을 얻어 승인 없이 재발송이 열린다(§7 D9). 생성 날짜는
    `SearchPacket.created_on` 이 따로 남긴다 — 기록은 남되 동일성 판정에는 끼지 않는다.
    """
    # sha8 은 코드가 원문에서 직접 계산한다 — 호출자가 준 raw_sha256(원본 파일 출처 해시)을 쓰면
    # 같은 원문에 hash+id 를 같이 바꿔 새 장부 namespace 를 열 수 있다(Codex 10차).
    value = f"{position.clickup_task_id}-{jd_text_sha8(jd)}"
    if not _PACKET_ID.fullmatch(value):
        _reject(f"packet_id 가 계약 형식과 다르다: {value!r}")
    return value


def to_json(packet: SearchPacket) -> str:
    """패킷을 결정적 JSON 으로. 이 문자열이 파일 내용이자 readback 대조 기준이다."""
    if not isinstance(packet, SearchPacket):
        _reject("to_json(packet) 은 SearchPacket 이어야 한다")
    return dumps_value(packet)


def from_json(text: str) -> SearchPacket:
    """to_json 의 역함수. 알 수 없는 키·필드 누락·타입 불일치는 전부 거부한다."""
    restored = loads_value(SearchPacket, text)
    if not isinstance(restored, SearchPacket):
        _reject("패킷 JSON 이 SearchPacket 으로 복원되지 않았다")
    return restored


def ensure_store_dir(path: Path) -> Path:
    """저장 디렉터리를 0700 으로 보장하고 **정규 경로**를 돌려준다. symlink·느슨한 권한은 거부(D7).

    돌려주는 값이 잠금 파일·패킷 파일 경로의 뿌리가 된다. 정규화하지 않으면 같은
    디렉터리를 두 이름으로 부른 호출자가 서로 다른 잠금을 잡고, 한 패킷이 이름마다
    한 번씩 발송 권한을 얻는다(Codex V1 F83-2). `resolve()` 가 그 이름들을 하나로 합친다.
    """
    if not isinstance(path, Path):
        _reject("저장 디렉터리는 Path 여야 한다")
    # exists() 는 symlink 를 따라가므로 먼저 본다 — 링크를 통해 0700 밖으로 새는 것을 막는다.
    if path.is_symlink():
        _reject(f"저장 디렉터리가 symlink 다: {path.name}")
    if not path.exists():
        try:
            path.mkdir(mode=DIR_MODE, parents=True)
        except FileExistsError:
            pass  # 다른 호출자가 먼저 만들었다 — 아래 권한 검사가 그대로 판정한다
        except OSError as error:
            _reject(f"저장 디렉터리를 만들지 못했다: {error.__class__.__name__}")
        else:
            os.chmod(path, DIR_MODE)  # umask 가 깎은 비트를 되돌린다
            return canonical_store_dir(path)
    if not path.is_dir():
        _reject(f"저장 경로가 디렉터리가 아니다: {path.name}")
    mode = os.stat(path).st_mode & 0o777
    if mode != DIR_MODE:
        _reject(f"저장 디렉터리 권한이 0700 이 아니다: {mode:04o}")
    return canonical_store_dir(path)


def canonical_store_dir(path: Path) -> Path:
    """저장 루트의 유일한 이름. 잠금·패킷 경로는 전부 이 값에서 나온다."""
    try:
        return path.resolve(strict=True)
    except OSError as error:
        _reject(f"저장 디렉터리 경로를 정규화하지 못했다: {error.__class__.__name__}")


def read_store_file(target: Path) -> str:
    """저장 파일 한 개를 읽는다. 읽기 실패는 조용히 넘기지 않는다(P3)."""
    try:
        return target.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        _reject(f"저장 파일을 읽지 못했다: {error.__class__.__name__}")


def write_store_file(directory: Path, target: Path, text: str) -> Path:
    """같은 디렉터리 임시 파일에 쓰고 os.replace 로 원자 교체한다. 결과는 항상 0600."""
    handle, name = tempfile.mkstemp(dir=str(directory), prefix=".packet-", suffix=".tmp")
    temporary = Path(name)
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, FILE_MODE)
        os.replace(temporary, target)
        fsync_directory(directory)
    except OSError as error:
        temporary.unlink(missing_ok=True)
        _reject(f"저장 파일을 쓰지 못했다: {error.__class__.__name__}")
    return target


def fsync_directory(directory: Path) -> None:
    """디렉터리 엔트리(이름)를 안정 저장한다 — 원자적 가시성은 전원 장애 뒤 영속성을 뜻하지 않는다(Codex 9차)."""
    handle = os.open(directory, os.O_RDONLY)
    try:
        os.fsync(handle)
    finally:
        os.close(handle)


def require_packet_id(value: object) -> str:
    """경로 조립 전에 식별자를 검사한다 — `..` 같은 조각이 디렉터리를 벗어나지 못하게."""
    if not isinstance(value, str) or not _PACKET_ID.fullmatch(value):
        _reject("packet_id 형식이 아니다")
    return value


# 발송 장부(send_ledger)와 패킷 저장이 **같은 디렉터리의 같은 flock 파일**을 쓴다 —
# 잠금 파일 경로가 다르면 그것은 잠금이 아니다. `packet` 은 패킷 파일 전체를 덮는 예약 채널이고,
# 실제 채널 잠금은 언제나 이 잠금을 먼저 잡고 안쪽으로 들어간다(획득 순서가 하나뿐 = 교착 없음).
PACKET_LOCK_CHANNEL = "packet"

_CHANNEL = re.compile(r"[a-z]+")


def require_channel(value: object) -> str:
    """채널 이름은 소문자 알파벳만 — 경로 조각이 되므로 구분자·상위 이동을 원천 차단한다."""
    if not isinstance(value, str) or not _CHANNEL.fullmatch(value):
        _reject("channel 은 소문자 알파벳만 허용한다")
    return value


def _lock_path(directory: Path, packet_id: str, channel: str) -> Path:
    return directory / f"{require_packet_id(packet_id)}.{require_channel(channel)}.lock"


_held = threading.local()


@contextmanager
def _flock(directory: Path, packet_id: str, channel: str) -> Iterator[None]:
    """잠금 파일 하나를 배타적으로 잡는다. 잠금 파일도 0600 이고 지우지 않는다.

    같은 스레드의 재진입은 깊이만 센다(Codex 9차: 새 fd 로 flock 을 다시 잡으면 자기 자신에 교착).
    다른 스레드·다른 프로세스는 flock 이 막는다.
    """
    key = str(_lock_path(directory, packet_id, channel))
    depth: dict[str, int] = getattr(_held, "depth", None) or {}
    _held.depth = depth
    if depth.get(key, 0) > 0:
        depth[key] += 1
        try:
            yield
        finally:
            depth[key] -= 1
        return
    handle = os.open(key, os.O_CREAT | os.O_RDWR, FILE_MODE)
    try:
        os.fchmod(handle, FILE_MODE)
        fcntl.flock(handle, fcntl.LOCK_EX)
        depth[key] = 1
        try:
            yield
        finally:
            depth[key] = 0
            fcntl.flock(handle, fcntl.LOCK_UN)
    finally:
        os.close(handle)


@contextmanager
def _channel_lock(directory: Path, packet_id: str, channel: str) -> Iterator[None]:
    """한 패킷·한 채널의 장부 조작을 프로세스 간 직렬화한다.

    채널 잠금은 패킷 잠금 안쪽에서만 잡는다 — 패킷 파일을 바꾸는 `PacketStore.save` 와
    장부를 움직이는 `record_intent`·`claim_send` 가 같은 잠금 앞에 줄을 서야, save 의
    "발송 intent 없음" 확인과 교체 사이로 청구가 끼어들지 못한다(Codex 13차 F83-2).
    """
    if require_channel(channel) == PACKET_LOCK_CHANNEL:
        with _flock(directory, packet_id, channel):
            yield
        return
    with _flock(directory, packet_id, PACKET_LOCK_CHANNEL), _flock(directory, packet_id, channel):
        yield


class PacketStore:
    """패킷 파일 저장소. 디렉터리 0700 · 파일 0600 · 원자 교체 · 독립 readback."""

    def __init__(self, dir: Path) -> None:
        self.dir = ensure_store_dir(dir)

    def path_for(self, packet_id: str) -> Path:
        """`<packet_id>.packet.json` 의 절대 경로."""
        return self.dir / f"{require_packet_id(packet_id)}.packet.json"

    def save(self, packet: SearchPacket) -> Path:
        """같은 packet_id 재저장은 내용이 같으면 no-op, 다르면 덮어쓴다 — 어느 쪽이든 파일 1개.

        확인(발송 intent 유무)과 교체를 **패킷 잠금 하나 안에서** 끝낸다. 둘이 갈라져 있으면
        "intent 없음" 을 본 뒤 청구가 끼어들어, 승인된 본문이 아닌 패킷이 저장된 채로
        발송 권한만 살아남는다(Codex 13차 F83-2 — 순서를 뒤집은 반례).
        """
        text = to_json(packet)
        target = self.path_for(packet.packet_id)
        with _channel_lock(self.dir, packet.packet_id, PACKET_LOCK_CHANNEL):
            if target.is_file() and read_store_file(target) == text:
                return target
            # 잠금은 다른 스레드·다른 프로세스를 막는다. 같은 스레드가 확인 도중 청구를 끼워 넣는
            # 재진입 경로는 잠금이 막지 못하므로, 확인 전후로 장부가 그대로인지도 본다.
            before = self._send_intent_files(packet.packet_id)
            if target.is_file() and self._has_send_intent(packet.packet_id):
                _reject("발송 intent 가 있는 packet_id 는 다른 패킷 내용으로 저장할 수 없다")
            if self._send_intent_files(packet.packet_id) != before:
                _reject("저장을 확인하는 동안 발송 intent 가 생겼다 — 이 패킷은 저장하지 않는다")
            return write_store_file(self.dir, target, text)

    def _send_intent_files(self, packet_id: str) -> frozenset[str]:
        """이 packet_id 의 발송 attempt 파일 이름들. 묘비라 사라지지 않으므로 집합 비교가 성립한다."""
        prefix = f"{require_packet_id(packet_id)}."
        return frozenset(
            entry.name
            for entry in self.dir.iterdir()
            if entry.is_file()
            and entry.name.startswith(prefix)
            and entry.name.endswith(".sent.json")
        )

    def _has_send_intent(self, packet_id: str) -> bool:
        return bool(self._send_intent_files(packet_id))

    def load(self, packet_id: str) -> SearchPacket:
        """저장된 패킷을 복원한다. 파일 부재·손상 JSON 은 전부 거부."""
        target = self.path_for(packet_id)
        if not target.is_file():
            _reject("패킷 파일이 없다")
        return from_json(read_store_file(target))

    def readback(self, packet: SearchPacket) -> bool:
        """저장 파일을 독립적으로 다시 읽어 to_json 해시가 같은지 (P9)."""
        target = self.path_for(packet.packet_id)
        if not target.is_file():
            _reject("readback 할 패킷 파일이 없다")
        stored = read_store_file(target)
        expected = to_json(packet)
        if stored != expected:
            return False
        # 바이트가 같아도 한 번 더 복원해 본다 — 파일만 보고 같은 패킷이 나와야 진짜 readback 이다.
        return to_json(from_json(stored)) == expected
