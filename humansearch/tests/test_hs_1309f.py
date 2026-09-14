"""HS-13.09f — Codex V1 10차 나머지 반례.

① packet_id 의 sha8 은 호출자가 준 `raw_sha256` 이 아니라 코드가 `jd.text` 에서 직접 계산한다
   (같은 원문에 hash+id 를 같이 바꾸면 새 장부 namespace 가 열렸다).
② TeamMail 의 to·cc 는 도메인만이 아니라 `team-recipients.json` 의 구성원이어야 한다.
③ `HUMANSEARCH_CONTRACTS_DIR` 의 pytest 경계는 수신자 계약 로더에도 똑같이 적용된다.
④ 장부 소스 어디에도 "발송 허가를 받는다" 류의 권한 귀속 문구가 없어야 한다(claim_send 뿐).
"""

from __future__ import annotations

import hashlib
import inspect
import re
from pathlib import Path

import pytest

from humansearch.brief import (
    BriefInputError,
    JdSource,
    PositionSpec,
    TeamMail,
    packet_id,
)
from humansearch.brief import send_claim as send_claim_module
from humansearch.brief import send_ledger as send_ledger_module
from humansearch.brief.policy import CONTRACTS_DIR_ENV
from humansearch.brief.recipients import load_recipients

_JD_TEXT = "주요업무\n• 실험을 설계한다.\n자격요건\n• 실험 설계 경험이 있다.\n"
_TEXT_SHA = hashlib.sha256(_JD_TEXT.encode("utf-8")).hexdigest()


def _position() -> PositionSpec:
    return PositionSpec("86e1abcd", "예시 고객사", "프로덕트 매니저", None, "정규직", "서울", None)


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# --- ① packet_id 는 원문 해시 -----------------------------------------------------


def test_packet_id_uses_a_hash_of_the_jd_text_not_the_caller_supplied_digest() -> None:
    same_text_a = JdSource(_JD_TEXT, "0" * 64, "U1")
    same_text_b = JdSource(_JD_TEXT, "1" * 64, "U1")
    expected = f"86e1abcd-{_TEXT_SHA[:8]}"
    assert packet_id(_position(), same_text_a) == expected
    assert packet_id(_position(), same_text_b) == expected


def test_packet_id_changes_when_the_text_changes() -> None:
    a = packet_id(_position(), JdSource(_JD_TEXT, _TEXT_SHA, "U1"))
    b = packet_id(_position(), JdSource(_JD_TEXT + "• 추가 줄\n", _TEXT_SHA, "U1"))
    assert a != b


# --- ② 수신자는 계약 구성원 -----------------------------------------------------------


def _mail(to: tuple[str, ...], cc: tuple[str, ...]) -> TeamMail:
    body = "본문"
    return TeamMail(
        subject="[포지션]예시 고객사, 프로덕트 매니저",
        to=to,
        cc=cc,
        body=body,
        body_sha256=_sha256(body),
    )


def test_contract_members_are_accepted() -> None:
    contract = load_recipients()
    assert _mail(contract.to, contract.cc).to == contract.to
    assert _mail(contract.first_live_to_only, ()).cc == ()


@pytest.mark.parametrize(
    "to, cc",
    [
        (("arbitrary@valueconnect.kr",), ()),
        (("sangmokang@valueconnect.kr",), ("arbitrary@valueconnect.kr",)),
        (("sangmokang@valueconnect.kr", "someone-else@valueconnect.kr"), ()),
    ],
)
def test_same_domain_address_outside_the_contract_is_rejected(
    to: tuple[str, ...], cc: tuple[str, ...]
) -> None:
    with pytest.raises(BriefInputError):
        _mail(to, cc)


# --- ③ recipients 로더의 환경변수 경계 ------------------------------------------------


def test_contracts_dir_env_is_refused_for_recipients_outside_pytest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from humansearch.brief.policy import policy

    policy()  # 정책 캐시를 먼저 채워도 수신자 로더는 따로 경계를 지켜야 한다(Codex 10차 재현 순서)
    monkeypatch.setenv(CONTRACTS_DIR_ENV, str(tmp_path))
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    with pytest.raises(BriefInputError):
        load_recipients()


# --- ④ 권한 귀속 문구 0 -----------------------------------------------------------------


def test_ledger_sources_never_attribute_send_permission_outside_claim_send() -> None:
    ledger_source = inspect.getsource(send_ledger_module)
    claim_source = inspect.getsource(send_claim_module)
    forbidden = re.compile(r"발송 허가를 받|발송할 수 있다|발송 권한을 (얻|받)")
    assert forbidden.search(ledger_source) is None
    # claim 모듈에서도 허가를 '받는다' 는 서술은 오직 claim_send 문서 안에서만 허용한다
    for line in claim_source.splitlines():
        if forbidden.search(line):
            assert "claim_send" in line or "True" in line, line
