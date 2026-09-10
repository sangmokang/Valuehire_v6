"""HS-13.01b — 브리프 운영 상수 계약 로더 (P22).

1,899자 경계·팀 메일 도메인·공개 프로필 URL 접두·메일 제목 접두·ClickUp 포지션
리스트 id·기본 검색 지역은 **`contracts/humansearch/brief-policy.json` 한 곳**이
소유한다. 같은 값을 코드에 다시 적으면 두 곳이 조용히 갈라지고, 갈라진 뒤에는
어느 쪽이 정본인지 실행해 봐야만 알 수 있다.

이 모듈만 계약 파일을 읽는다. 다른 모듈은 `policy()` 로 값을 받는다.
`policy()` 는 최초 1회 로드 후 캐시한다 — 값 타입 생성마다 파일을 열면 순수
함수라는 §5 계약(시계·네트워크·파일 접근 0)을 사실상 어기게 된다.

의존 방향은 policy → types 한 방향이다. `types.py` 는 순환을 피하려고
함수 본문 안에서 `policy` 를 import 한다(모듈 최상단 import 금지).
"""

from __future__ import annotations

import json
import os
import re
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from .types import _reject

__all__ = [
    "BriefPolicy",
    "load_brief_policy",
    "override_policy_for_tests",
    "policy",
]

CONTRACTS_DIR_ENV = "HUMANSEARCH_CONTRACTS_DIR"
_CONTRACT_RELPATH = ("humansearch", "brief-policy.json")
_CONTRACT_VERSION = 1
_DOMAIN = re.compile(r"[a-z0-9.-]+\.[a-z]{2,}")
_DIGITS = re.compile(r"[0-9]+")


@dataclass(frozen=True)
class BriefPolicy:
    """브리프·서치 패킷이 쓰는 운영 상수. 소유자는 계약 파일 하나뿐이다."""

    version: int
    linkedin_inmail_max_chars: int
    subject_prefixes: tuple[str, ...]
    subject_search_suffix: str
    profile_url_prefixes: tuple[str, ...]
    team_mail_domain: str
    clickup_position_list_id: str
    default_search_location: str
    allowed_search_locations: tuple[str, ...]


def _repo_root() -> Path:
    """`contracts/` 디렉터리를 가진 첫 상위 디렉터리를 저장소 루트로 본다."""

    for parent in Path(__file__).resolve().parents:
        if (parent / "contracts").is_dir():
            return parent
    _reject("저장소 루트를 찾지 못했다(상위 어디에도 contracts/ 가 없다)")


def _default_contract_path() -> Path:
    override = os.environ.get(CONTRACTS_DIR_ENV)
    base = Path(override) if override else _repo_root() / "contracts"
    return base.joinpath(*_CONTRACT_RELPATH)


def _read_contract(path: Path) -> dict[str, object]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as error:
        _reject(f"브리프 정책 계약 파일을 읽지 못했다: {path.name} ({type(error).__name__})")
    try:
        raw: object = json.loads(text)
    except json.JSONDecodeError as error:
        _reject(f"브리프 정책 계약 파일이 JSON 이 아니다: {path.name} ({error.msg})")
    if not isinstance(raw, dict):
        _reject("브리프 정책 계약의 최상위는 객체여야 한다")
    return cast(dict[str, object], raw)


def _require_positive_int(root: dict[str, object], key: str) -> int:
    value = root.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        _reject(f"브리프 정책의 {key} 는 정수여야 한다: {value!r}")
    if value <= 0:
        _reject(f"브리프 정책의 {key} 는 1 이상이어야 한다: {value}")
    return value


def _require_nonempty_str(root: dict[str, object], key: str) -> str:
    value = root.get(key)
    if not isinstance(value, str) or not value.strip():
        _reject(f"브리프 정책의 {key} 는 비어 있지 않은 문자열이어야 한다: {value!r}")
    return value


def _require_prefix_list(root: dict[str, object], key: str) -> tuple[str, ...]:
    value = root.get(key)
    if not isinstance(value, list):
        _reject(f"브리프 정책의 {key} 는 배열이어야 한다: {value!r}")
    items: list[str] = []
    for item in cast(list[object], value):
        if not isinstance(item, str) or not item.strip():
            _reject(f"브리프 정책의 {key} 에 빈 접두가 있다")
        if item in items:
            _reject(f"브리프 정책의 {key} 에 중복 접두가 있다: {item!r}")
        items.append(item)
    if not items:
        _reject(f"브리프 정책의 {key} 가 비어 있다(빈 접두 목록은 검사를 무효화한다)")
    return tuple(items)


def load_brief_policy(path: Path | None = None) -> BriefPolicy:
    """계약 파일을 읽어 검증한다. 어떤 위반이든 `BriefInputError`.

    `path` 가 None 이면 환경변수 `HUMANSEARCH_CONTRACTS_DIR` 아래
    `humansearch/brief-policy.json`, 환경변수가 없으면 저장소 루트의
    `contracts/humansearch/brief-policy.json` 을 읽는다.
    """

    target = _default_contract_path() if path is None else path
    root = _read_contract(target)

    version = root.get("version")
    if isinstance(version, bool) or version != _CONTRACT_VERSION:
        _reject(f"브리프 정책의 version 은 {_CONTRACT_VERSION} 이어야 한다: {version!r}")

    domain = _require_nonempty_str(root, "team_mail_domain")
    if not _DOMAIN.fullmatch(domain):
        _reject(f"브리프 정책의 team_mail_domain 형식이 올바르지 않다: {domain!r}")

    list_id = _require_nonempty_str(root, "clickup_position_list_id")
    if not _DIGITS.fullmatch(list_id):
        _reject(f"브리프 정책의 clickup_position_list_id 는 숫자여야 한다: {list_id!r}")

    default_location = _require_nonempty_str(root, "default_search_location")
    allowed_locations = _require_location_list(root, "allowed_search_locations")
    if default_location not in allowed_locations:
        _reject(
            "브리프 정책의 default_search_location 이 allowed_search_locations 밖이다: "
            f"{default_location!r}"
        )

    return BriefPolicy(
        version=_CONTRACT_VERSION,
        linkedin_inmail_max_chars=_require_positive_int(root, "linkedin_inmail_max_chars"),
        subject_prefixes=_require_prefix_list(root, "subject_prefixes"),
        subject_search_suffix=_require_nonempty_str(root, "subject_search_suffix"),
        profile_url_prefixes=_require_prefix_list(root, "profile_url_prefixes"),
        team_mail_domain=domain,
        clickup_position_list_id=list_id,
        default_search_location=default_location,
        allowed_search_locations=allowed_locations,
    )


def _require_location_list(root: dict[str, object], key: str) -> tuple[str, ...]:
    """D12 허용 지역 목록 — 비어 있지 않고, 각 항목은 공백 없는 정확한 문자열, 중복 0."""
    value = root.get(key)
    if not isinstance(value, list) or not value:
        _reject(f"브리프 정책의 {key} 는 비어 있지 않은 목록이어야 한다")
    items: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item or item != item.strip():
            _reject(f"브리프 정책의 {key} 항목은 앞뒤 공백 없는 문자열이어야 한다: {item!r}")
        if item in items:
            _reject(f"브리프 정책의 {key} 에 같은 지역이 두 번 있다: {item!r}")
        items.append(item)
    return tuple(items)


_loaded: BriefPolicy | None = None
_override: BriefPolicy | None = None


def policy() -> BriefPolicy:
    """모듈 단일 로더. 최초 1회만 계약 파일을 읽고 그 뒤로는 캐시를 돌려준다."""

    global _loaded
    if _override is not None:
        return _override
    if _loaded is None:
        _loaded = load_brief_policy()
    return _loaded


@contextmanager
def override_policy_for_tests(replacement: BriefPolicy) -> Iterator[BriefPolicy]:
    """시험 전용 — 정책을 임시로 갈아끼우고 블록을 벗어나면 반드시 원복한다.

    이름에 `for_tests` 를 박아둔 이유: 운영 경로에서 이 함수를 부르면 계약 파일이
    아니라 호출자가 정책의 소유자가 되고, 그 순간 P22 가 무너진다.
    """

    global _override
    if "PYTEST_CURRENT_TEST" not in os.environ:
        _reject(
            "override_policy_for_tests 는 pytest 실행 중에만 부를 수 있다 — 운영 경로의 정책 소유자는 계약 파일뿐이다"
        )
    if not isinstance(replacement, BriefPolicy):
        _reject("override_policy_for_tests 는 BriefPolicy 만 받는다")
    previous = _override
    _override = replacement
    try:
        yield replacement
    finally:
        _override = previous
