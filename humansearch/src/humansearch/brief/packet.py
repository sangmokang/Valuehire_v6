"""HS-13.09 — 서치 패킷을 git 밖 디렉터리에 0600 으로 저장하고 독립 readback 으로 대조한다.

계약: docs/engineering/humansearch-hs13-position-brief-goal-2026-09-10.md §5 packet.py · §7 D7.
후보자 PII 는 파일에만 남는다 — 이 모듈은 표준출력·로그를 한 줄도 내지 않는다.
시계·네트워크 접근 0. 저장 위치는 호출자가 Path 로 주입한다(경로 리터럴 0).
"""

from __future__ import annotations

import json
import os
import tempfile
import typing
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
    "ensure_store_dir",
    "from_json",
    "packet_id",
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
    arguments = {
        name: _decode(hints[name], raw[name], f"{path}.{name}") for name in sorted(names)
    }
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


def packet_id(position: PositionSpec, jd: JdSource) -> str:
    """`{clickup_id}-{sha8}`. 날짜를 담지 않는다 — 시계 인자도 받지 않는다(HS-13.09c).

    같은 포지션·같은 JD 는 언제 만들어도 같은 식별자여야 한다. 날짜가 섞이면 자정을 넘긴
    재생성이 새 장부 파일 이름을 얻어 승인 없이 재발송이 열린다(§7 D9). 생성 날짜는
    `SearchPacket.created_on` 이 따로 남긴다 — 기록은 남되 동일성 판정에는 끼지 않는다.
    """
    value = f"{position.clickup_task_id}-{jd.raw_sha256[:8]}"
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
    """저장 디렉터리를 0700 으로 보장한다. symlink·느슨한 권한은 거부(D7)."""
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
            return path
    if not path.is_dir():
        _reject(f"저장 경로가 디렉터리가 아니다: {path.name}")
    mode = os.stat(path).st_mode & 0o777
    if mode != DIR_MODE:
        _reject(f"저장 디렉터리 권한이 0700 이 아니다: {mode:04o}")
    return path


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
        os.chmod(temporary, FILE_MODE)
        os.replace(temporary, target)
    except OSError as error:
        temporary.unlink(missing_ok=True)
        _reject(f"저장 파일을 쓰지 못했다: {error.__class__.__name__}")
    return target


def require_packet_id(value: object) -> str:
    """경로 조립 전에 식별자를 검사한다 — `..` 같은 조각이 디렉터리를 벗어나지 못하게."""
    if not isinstance(value, str) or not _PACKET_ID.fullmatch(value):
        _reject("packet_id 형식이 아니다")
    return value


class PacketStore:
    """패킷 파일 저장소. 디렉터리 0700 · 파일 0600 · 원자 교체 · 독립 readback."""

    def __init__(self, dir: Path) -> None:
        self.dir = ensure_store_dir(dir)

    def path_for(self, packet_id: str) -> Path:
        """`<packet_id>.packet.json` 의 절대 경로."""
        return self.dir / f"{require_packet_id(packet_id)}.packet.json"

    def save(self, packet: SearchPacket) -> Path:
        """같은 packet_id 재저장은 내용이 같으면 no-op, 다르면 덮어쓴다 — 어느 쪽이든 파일 1개."""
        text = to_json(packet)
        target = self.path_for(packet.packet_id)
        if target.is_file() and read_store_file(target) == text:
            return target
        return write_store_file(self.dir, target, text)

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
