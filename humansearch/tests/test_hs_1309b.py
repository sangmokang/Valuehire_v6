"""HS-13.09b — 재발송 승인을 패킷·attempt·수신자 계약에 결합한다.

계약: docs/engineering/humansearch-hs13-position-brief-goal-2026-09-10.md §5 send_ledger.py
      Approval · §7 D9 — 이 착수 프롬프트가 확정한 결합 계약이 문서보다 정본이다.

`Approval` 은 이제 어떤 패킷·어떤 attempt 를 여는 승인인지, 그리고 승인자가 팀
수신자 계약(contracts/humansearch/team-recipients.json) 의 to∪cc 안인지까지 스스로
증명해야 한다. `open_new_attempt` 는 셋 중 하나라도 어긋나면 `BriefInputError` 로
거부한다 — 다른 패킷의 승인을 빌려 쓰거나, 낡은 attempt 번호로 만든 승인을 재사용하거나,
계약 밖 사람의 서명으로 재시도를 여는 것을 전부 막는다.
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from pathlib import Path

import pytest

from humansearch.brief import (
    Approval,
    BriefInputError,
    SendIntent,
    SendState,
    load_attempt,
    record_intent,
)
from humansearch.brief import open_new_attempt as _raw_open_new_attempt

_PACKET_ID = "86e1abcd-0a1b2c3d"
_OTHER_PACKET_ID = "86e1abcd-1a2b3c4d"
_AT = datetime(2026, 9, 10, 3, 20, 0, tzinfo=UTC)
_LATER = datetime(2026, 9, 10, 4, 0, 0, tzinfo=UTC)
_EVEN_LATER = datetime(2026, 9, 10, 5, 0, 0, tzinfo=UTC)

# contracts/humansearch/team-recipients.json 의 실제 to·cc 주소(정본 계약 파일 그대로).
_CONTRACT_TO = "sangmokang@valueconnect.kr"
_CONTRACT_CC = "rogan@valueconnect.kr"


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()




def open_new_attempt(
    dir: Path,
    packet_id: str,
    channel: str,
    *,
    approval: Approval,
    at: datetime,
    recipients_sha256: str | None = None,
    body_sha256: str | None = None,
) -> tuple[SendIntent, bool]:
    retry_seed = f"재시도 본문 {approval.from_attempt + 1}"
    return _raw_open_new_attempt(
        dir,
        packet_id,
        channel,
        approval=approval,
        at=at,
        recipients_sha256=recipients_sha256 or _sha256("정정된 수신자"),
        body_sha256=body_sha256 or _sha256(retry_seed),
    )


def _intent(packet_id: str = _PACKET_ID, channel: str = "gmail") -> SendIntent:
    return SendIntent(
        packet_id=packet_id,
        channel=channel,
        attempt=1,
        recipients_sha256=_sha256("수신자"),
        body_sha256=_sha256("본문"),
        recorded_at=_AT,
        state=SendState.INTENT,
    )


def _approval(
    *,
    approved_by: str = _CONTRACT_TO,
    packet_id: str = _PACKET_ID,
    from_attempt: int = 1,
    search_query: str = 'in:sent subject:"[포지션]"',
    search_checked_at: str = "2026-09-10T04:00:00+00:00",
    reason: str = "발송함에서 찾지 못해 재시도를 승인한다",
) -> Approval:
    return Approval(
        approved_by=approved_by,
        search_query=search_query,
        search_checked_at=search_checked_at,
        reason=reason,
        packet_id=packet_id,
        from_attempt=from_attempt,
    )


def test_open_new_attempt_accepts_contract_to_address_matching_packet_and_latest_attempt(
    tmp_path: Path,
) -> None:
    directory = tmp_path / "ledger"
    record_intent(directory, _intent())
    fresh, created = open_new_attempt(
        directory, _PACKET_ID, "gmail", approval=_approval(), at=_LATER
    )
    assert created is True
    assert fresh.attempt == 2
    assert fresh.approval == _approval()


def test_open_new_attempt_rejects_approval_bound_to_a_different_packet(tmp_path: Path) -> None:
    directory = tmp_path / "ledger"
    record_intent(directory, _intent())
    with pytest.raises(BriefInputError):
        open_new_attempt(
            directory,
            _PACKET_ID,
            "gmail",
            approval=_approval(packet_id=_OTHER_PACKET_ID),
            at=_LATER,
        )


def test_open_new_attempt_rejects_approval_from_an_attempt_that_is_not_latest(
    tmp_path: Path,
) -> None:
    directory = tmp_path / "ledger"
    record_intent(directory, _intent())
    open_new_attempt(directory, _PACKET_ID, "gmail", approval=_approval(from_attempt=1), at=_LATER)
    # 최신은 이제 attempt 2 인데, from_attempt=1 로 만든 승인은 낡았다 — 재사용을 막아야 한다.
    with pytest.raises(BriefInputError):
        open_new_attempt(
            directory,
            _PACKET_ID,
            "gmail",
            approval=_approval(from_attempt=1),
            at=_EVEN_LATER,
        )


def test_open_new_attempt_rejects_approver_outside_team_recipients_contract(
    tmp_path: Path,
) -> None:
    directory = tmp_path / "ledger"
    record_intent(directory, _intent())
    with pytest.raises(BriefInputError):
        open_new_attempt(
            directory,
            _PACKET_ID,
            "gmail",
            approval=_approval(approved_by="someone@example.com"),
            at=_LATER,
        )


def test_open_new_attempt_accepts_a_cc_address_from_the_contract(tmp_path: Path) -> None:
    directory = tmp_path / "ledger"
    record_intent(directory, _intent())
    fresh, created = open_new_attempt(
        directory,
        _PACKET_ID,
        "gmail",
        approval=_approval(approved_by=_CONTRACT_CC),
        at=_LATER,
    )
    assert created is True
    assert fresh.approval is not None
    assert fresh.approval.approved_by == _CONTRACT_CC


def test_open_new_attempt_round_trips_approval_binding_fields_through_the_ledger_file(
    tmp_path: Path,
) -> None:
    directory = tmp_path / "ledger"
    record_intent(directory, _intent())
    open_new_attempt(directory, _PACKET_ID, "gmail", approval=_approval(), at=_LATER)
    reloaded = load_attempt(directory, _PACKET_ID, "gmail", 2)
    assert reloaded is not None
    assert reloaded.approval == _approval()


def test_open_new_attempt_records_the_new_attempt_digest_instead_of_copying_a1(
    tmp_path: Path,
) -> None:
    directory = tmp_path / "ledger"
    record_intent(directory, _intent())
    body_sha256 = _sha256("정정된 본문")
    recipients_sha256 = _sha256("정정된 수신자")
    fresh, created = open_new_attempt(
        directory,
        _PACKET_ID,
        "gmail",
        approval=_approval(reason="정정된 본문과 수신자를 확인하고 재시도를 승인한다"),
        at=_LATER,
        body_sha256=body_sha256,
        recipients_sha256=recipients_sha256,
    )
    assert created is True
    assert fresh.body_sha256 == body_sha256
    assert fresh.recipients_sha256 == recipients_sha256
    reloaded = load_attempt(directory, _PACKET_ID, "gmail", 2)
    assert reloaded is not None
    assert reloaded.body_sha256 == body_sha256
    assert reloaded.recipients_sha256 == recipients_sha256


def test_open_new_attempt_requires_no_change_reason_when_digest_is_unchanged(
    tmp_path: Path,
) -> None:
    directory = tmp_path / "ledger"
    first = _intent()
    record_intent(directory, first)
    with pytest.raises(BriefInputError):
        open_new_attempt(
            directory,
            _PACKET_ID,
            "gmail",
            approval=_approval(reason="발송함에서 찾지 못해 재시도를 승인한다"),
            at=_LATER,
            body_sha256=first.body_sha256,
            recipients_sha256=first.recipients_sha256,
        )


def test_open_new_attempt_accepts_unchanged_digest_with_explicit_no_change_reason(
    tmp_path: Path,
) -> None:
    directory = tmp_path / "ledger"
    first = _intent()
    record_intent(directory, first)
    fresh, created = open_new_attempt(
        directory,
        _PACKET_ID,
        "gmail",
        approval=_approval(reason="정정 없음 — 발송함에서 찾지 못해 재시도를 승인한다"),
        at=_LATER,
        body_sha256=first.body_sha256,
        recipients_sha256=first.recipients_sha256,
    )
    assert created is True
    assert fresh.body_sha256 == first.body_sha256
    assert fresh.recipients_sha256 == first.recipients_sha256
