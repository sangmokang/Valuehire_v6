"""HS-13.05 — 팀 수신자 계약 파일 로더 (D2).

`mail.py` 가 이 모듈을 그대로 재수출하므로 공개 이름은 `mail.load_recipients` 로도
같은 함수다. 파일을 나눈 이유는 하나뿐이다 — `mail.py` 를 P11 의 300줄 아래로
유지하면서 계약 파싱(파일 I/O)과 본문 조립(순수 함수)을 눈으로 갈라 두려는 것.

검증은 전부 여기 한 곳에 있다. 같은 검사를 `Recipients.__post_init__` 에도 적으면
로더의 도메인 검사를 지워도 시험이 초록이 되어 §11 변이 ⑤("`load_recipients` 가
도메인 검사 생략")를 놓친다. 검사는 한 자리에만 둔다.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from .policy import CONTRACTS_DIR_ENV, _repo_root, policy
from .types import _reject, _require_email

__all__ = ["Recipients", "load_recipients"]

_CONTRACT_RELPATH = ("humansearch", "team-recipients.json")
_CONTRACT_VERSION = 1


@dataclass(frozen=True)
class Recipients:
    """팀 수신자 계약 파일의 내용(D2)."""

    to: tuple[str, ...]
    cc: tuple[str, ...]
    first_live_to_only: tuple[str, ...]


def _default_recipients_path() -> Path:
    override = os.environ.get(CONTRACTS_DIR_ENV)
    base = Path(override) if override else _repo_root() / "contracts"
    return base.joinpath(*_CONTRACT_RELPATH)


def _read_contract(path: Path) -> dict[str, object]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as error:
        _reject(f"팀 수신자 계약 파일을 읽지 못했다: {path.name} ({type(error).__name__})")
    try:
        raw: object = json.loads(text)
    except json.JSONDecodeError as error:
        _reject(f"팀 수신자 계약 파일이 JSON 이 아니다: {path.name} ({error.msg})")
    if not isinstance(raw, dict):
        _reject("팀 수신자 계약의 최상위는 객체여야 한다")
    return cast(dict[str, object], raw)


def _require_addresses(
    root: dict[str, object],
    key: str,
    seen: set[str],
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    value = root.get(key)
    if not isinstance(value, list):
        _reject(f"팀 수신자 계약의 {key} 는 배열이어야 한다: {value!r}")
    domain = f"@{policy().team_mail_domain}"
    addresses: list[str] = []
    for item in cast(list[object], value):
        if not isinstance(item, str):
            _reject(f"팀 수신자 계약의 {key} 항목은 문자열이어야 한다: {item!r}")
        _require_email(item, f"팀 수신자 계약의 {key}")
        if not item.endswith(domain):
            _reject(f"팀 수신자 계약의 {key} 에 계약 도메인 밖 주소가 있다")
        if item in seen:
            _reject(f"팀 수신자 계약에 중복 주소가 있다: {item}")
        seen.add(item)
        addresses.append(item)
    if not addresses and not allow_empty:
        _reject(f"팀 수신자 계약의 {key} 가 비어 있다(발송 대상 0명은 발송이 아니다)")
    return tuple(addresses)


def load_recipients(path: Path | None = None) -> Recipients:
    """팀 수신자 계약 파일을 읽어 검증한다. 어떤 위반이든 `BriefInputError`.

    `path` 가 None 이면 `policy.py` 와 같은 규칙으로 찾는다 — 환경변수
    `HUMANSEARCH_CONTRACTS_DIR` 아래, 없으면 저장소 루트의 `contracts/` 아래
    `humansearch/team-recipients.json`.
    """

    target = _default_recipients_path() if path is None else path
    root = _read_contract(target)

    version = root.get("version")
    if isinstance(version, bool) or version != _CONTRACT_VERSION:
        _reject(f"팀 수신자 계약의 version 은 {_CONTRACT_VERSION} 이어야 한다: {version!r}")

    seen: set[str] = set()
    to = _require_addresses(root, "to", seen, allow_empty=False)
    cc = _require_addresses(root, "cc", seen, allow_empty=True)
    first_live = _require_addresses(root, "first_live_to_only", set(), allow_empty=False)
    outside = tuple(sorted(set(first_live) - set(to)))
    if outside:
        _reject(f"팀 수신자 계약의 first_live_to_only 가 to 밖의 주소를 담고 있다: {outside}")
    return Recipients(to=to, cc=cc, first_live_to_only=first_live)
