"""HS-13.09e — Codex V1 8차 반례 3건의 회귀 시험.

① claim_send 와 open_new_attempt 의 교차 경합: 청구가 마커를 만든 뒤 기록을 쓰기 전에 승인 재시도가
   a2 를 열고 a1 을 ABANDONED 로 접으면, 낡은 a1 기억으로 SEND_CLAIMED 를 덮어써 a1·a2 둘 다 발송 권한을
   얻었다 → `_append` 는 디스크 최신본과 CAS 대조하고, 공개 진입점은 채널 잠금(flock) 아래에서만 움직인다.
   a2 생성 뒤 a1 ABANDONED 전에 죽은 장부는 읽기 시 복구(append)한다(§5 open_new_attempt 계약).
② SearchPacket.packet_id 가 position·jd 에서 도출한 값과 다르면 새 발송 namespace 가 열린다 → 타입이 결합 강제.
③ 공개된 override_policy_for_tests 로 운영 경로가 D12 를 우회 → 패키지 공개 API 에서 제거, pytest 밖 호출 거부,
   SearchPacket 조립 시 현재 계약으로 필터 재검증.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import threading
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import pytest

import humansearch.brief as brief_pkg
from humansearch.brief import (
    Approval,
    BriefInputError,
    CandidateEvidence,
    CandidateLead,
    Claim,
    CompanyBrief,
    ConnectionDegree,
    EmailContact,
    JdPacket,
    JdSource,
    PositionSpec,
    ScoreBreakdown,
    SearchFilters,
    SearchPacket,
    SendIntent,
    SendState,
    SourceRef,
    TeamMail,
    claim_send,
    load_attempt,
    load_intent,
    open_new_attempt,
    record_intent,
)
from humansearch.brief import send_claim as send_claim_module
from humansearch.brief import send_ledger as send_ledger_module
from humansearch.brief.policy import override_policy_for_tests, policy

_JD_TEXT = "직무: 프로덕트 매니저\n요구: 실험 설계 경험 3년"
_RAW_SHA = hashlib.sha256(_JD_TEXT.encode("utf-8")).hexdigest()
_CLICKUP = "86e1abcd"
_PACKET_ID = f"{_CLICKUP}-{_RAW_SHA[:8]}"
_AT = datetime(2026, 9, 10, 3, 20, 0, tzinfo=UTC)
_CLAIM_AT = datetime(2026, 9, 10, 3, 30, 0, tzinfo=UTC)
_LATER = datetime(2026, 9, 10, 4, 0, 0, tzinfo=UTC)


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _intent() -> SendIntent:
    return SendIntent(
        packet_id=_PACKET_ID,
        channel="gmail",
        attempt=1,
        recipients_sha256=_sha256("sangmokang@valueconnect.kr"),
        body_sha256=_sha256("본문"),
        recorded_at=_AT,
        state=SendState.INTENT,
    )


def _approval(from_attempt: int) -> Approval:
    return Approval(
        approved_by="sangmokang@valueconnect.kr",
        search_query='in:sent subject:"[포지션]"',
        search_checked_at="2026-09-10T04:00:00+00:00",
        reason="발송함에서 찾지 못해 재시도를 승인한다",
        packet_id=_PACKET_ID,
        from_attempt=from_attempt,
    )


def _ledger(tmp_path: Path) -> Path:
    directory = tmp_path / "ledger"
    directory.mkdir(mode=0o700)
    return directory


def _claim(directory: Path, attempt: int, at: datetime = _CLAIM_AT) -> tuple[SendIntent, bool]:
    return claim_send(directory, _PACKET_ID, "gmail", attempt, at=at, evidence="발송 직전 청구")


def _reopen(directory: Path, from_attempt: int) -> tuple[SendIntent, bool]:
    return open_new_attempt(
        directory, _PACKET_ID, "gmail", approval=_approval(from_attempt), at=_LATER
    )


# --- ① 교차 경합 -------------------------------------------------------------------


def test_stale_claim_cannot_overwrite_an_attempt_abandoned_meanwhile(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """마커 생성과 기록 사이에 승인 재시도가 끼어들면 청구는 실패해야 하고 a1 은 ABANDONED 로 남는다."""
    directory = _ledger(tmp_path)
    record_intent(directory, _intent())

    @contextlib.contextmanager
    def no_lock(*_: object) -> Iterator[None]:
        yield

    monkeypatch.setattr(send_ledger_module, "_channel_lock", no_lock)
    monkeypatch.setattr(send_claim_module, "_channel_lock", no_lock)
    real_create = send_ledger_module._create_exclusive
    fired = False

    def create_then_reopen(directory_: Path, target: Path, text: str) -> bool:
        nonlocal fired
        won = real_create(directory_, target, text)
        if not fired:
            fired = True
            _reopen(
                directory, 1
            )  # 경합 상대: a2 생성 + a1 ABANDONED (첫 호출 = 청구 마커 직후에만)
        return won

    monkeypatch.setattr(send_claim_module, "_create_exclusive", create_then_reopen)
    with pytest.raises(BriefInputError):
        _claim(directory, 1)
    first = load_attempt(directory, _PACKET_ID, "gmail", 1)
    second = load_attempt(directory, _PACKET_ID, "gmail", 2)
    assert first is not None and first.state is SendState.ABANDONED
    assert SendState.SEND_CLAIMED not in {step.state for step in first.transitions}
    assert second is not None and second.state is SendState.INTENT
    _, won = _claim(directory, 2, at=_LATER)
    assert won is True


def _contention_round(directory: Path) -> None:
    directory.mkdir(mode=0o700)
    record_intent(directory, _intent())
    barrier = threading.Barrier(2)

    def claim_side() -> str:
        barrier.wait(timeout=5)
        try:
            _, won = _claim(directory, 1)
        except BriefInputError:
            return "rejected"
        return "won" if won else "lost"

    def reopen_side() -> str:
        barrier.wait(timeout=5)
        _, opened = _reopen(directory, 1)
        return "opened" if opened else "not-opened"

    with ThreadPoolExecutor(max_workers=2) as pool:
        claim_result = pool.submit(claim_side)
        reopen_result = pool.submit(reopen_side)
        outcomes = (claim_result.result(), reopen_result.result())
    assert outcomes[1] == "opened"
    first = load_attempt(directory, _PACKET_ID, "gmail", 1)
    second = load_attempt(directory, _PACKET_ID, "gmail", 2)
    assert first is not None and first.state is SendState.ABANDONED
    assert second is not None and second.state is SendState.INTENT
    assert [a for a in (first, second) if a.state is SendState.SEND_CLAIMED] == []


def test_claim_and_reopen_under_contention_never_arm_two_attempts(tmp_path: Path) -> None:
    """잠금 아래에서는 어떤 순서로 끝나도 SEND_CLAIMED 가 두 attempt 에 동시에 남지 않는다."""
    for index in range(12):
        _contention_round(tmp_path / f"ledger-{index}")


def test_reading_recovers_an_attempt_left_unsent_behind_a_newer_one(tmp_path: Path) -> None:
    """a2 파일은 생겼는데 a1 ABANDONED 를 쓰기 전에 죽은 장부 — 읽기만 해도 a1 이 ABANDONED 로 닫힌다."""
    directory = _ledger(tmp_path)
    record_intent(directory, _intent())
    first_path = directory / f"{_PACKET_ID}.gmail.a1.sent.json"
    second_payload: dict[str, Any] = json.loads(first_path.read_text(encoding="utf-8"))
    second_payload["attempt"] = 2
    second_payload["recorded_at"] = _LATER.isoformat()
    second_payload["approval"] = {
        "approved_by": "sangmokang@valueconnect.kr",
        "search_query": 'in:sent subject:"[포지션]"',
        "search_checked_at": "2026-09-10T04:00:00+00:00",
        "reason": "발송함에서 찾지 못해 재시도를 승인한다",
        "packet_id": _PACKET_ID,
        "from_attempt": 1,
    }
    second_path = directory / f"{_PACKET_ID}.gmail.a2.sent.json"
    second_path.write_text(json.dumps(second_payload, ensure_ascii=False), encoding="utf-8")
    os.chmod(second_path, 0o600)

    latest = load_intent(directory, _PACKET_ID, "gmail")
    assert latest is not None and latest.attempt == 2
    recovered = load_attempt(directory, _PACKET_ID, "gmail", 1)
    assert recovered is not None
    assert recovered.state is SendState.ABANDONED
    assert recovered.transitions[-1].at == _LATER
    with pytest.raises(BriefInputError):
        _claim(directory, 1)
    _, won = _claim(directory, 2, at=_LATER)
    assert won is True


def test_lock_file_is_left_next_to_the_ledger_with_owner_only_mode(tmp_path: Path) -> None:
    directory = _ledger(tmp_path)
    record_intent(directory, _intent())
    lock = directory / f"{_PACKET_ID}.gmail.lock"
    assert lock.is_file()
    assert (lock.stat().st_mode & 0o777) == 0o600


# --- ② packet_id 결합 --------------------------------------------------------------


_LEAD_URL = "https://www.linkedin.com/in/example-%EC%98%88%EC%8B%9C-000001/"
_DAY_A = date(2026, 9, 10)


def _position() -> PositionSpec:
    return PositionSpec(_CLICKUP, "예시 고객사", "프로덕트 매니저", None, "정규직", "서울", None)


def _jd() -> JdSource:
    return JdSource(_JD_TEXT, _RAW_SHA, "U1")


def _packet(identifier: str, filters: SearchFilters | None = None) -> SearchPacket:
    source = _jd()
    body = "예시 문구\n내부 공유 본문"
    kwargs: dict[str, Any] = {}
    if filters is not None:
        kwargs["search_filters"] = filters
    return SearchPacket(
        packet_id=identifier,
        created_on=_DAY_A,
        position=_position(),
        jd=source,
        company=CompanyBrief(
            legal_name=Claim("예시 주식회사", ("C1",)),
            sources=(SourceRef("C1", "https://example.com/about", "회사 소개", _DAY_A),),
        ),
        jd_packet=JdPacket("gmail 본문", "링크드인 본문", "회사 소개 필드", "JD 본문 필드"),
        candidates=(
            CandidateLead(
                display_name="예시 후보",
                headline="프로덕트 매니저",
                linkedin_url=_LEAD_URL,
                education="예시대학원 석사",
                career="예시사 3년",
                match_reasons=("실험 설계 경험",),
                check_points=("도메인 적합성",),
                evidence=CandidateEvidence(("실험",), 1, 2, "석사", 2, (24, 18), 2, 8, 10),
                score=ScoreBreakdown(30, 15, 15, 15),
                email=EmailContact("lead@example.org", "https://example.org/lab", "연구실"),
                degree=ConnectionDegree.SECOND,
                source_note="공개 프로필 URL 일치",
            ),
        ),
        mail=TeamMail(
            subject="[포지션]예시 고객사, 프로덕트 매니저",
            to=("sangmokang@valueconnect.kr",),
            cc=(),
            body=body,
            body_sha256=_sha256(body),
        ),
        boolean_queries=('("Product Manager" OR PM) AND 실험',),
        inmails=((_LEAD_URL, "안녕하세요, 포지션을 제안드립니다."),),
        **kwargs,
    )


def test_search_packet_accepts_the_id_derived_from_position_and_jd() -> None:
    assert _packet(_PACKET_ID).packet_id == _PACKET_ID


@pytest.mark.parametrize(
    "decoy",
    [f"86other00-{_RAW_SHA[:8]}", f"{_CLICKUP}-deadbeef", "86other00-deadbeef"],
)
def test_search_packet_rejects_a_well_formed_but_unbound_id(decoy: str) -> None:
    with pytest.raises(BriefInputError):
        _packet(decoy)


# --- ③ 정책 override 경계 ------------------------------------------------------------


def test_override_is_not_part_of_the_public_package_api() -> None:
    assert "override_policy_for_tests" not in brief_pkg.__all__
    assert not hasattr(brief_pkg, "override_policy_for_tests")


def test_override_refuses_to_run_outside_pytest(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    wider = replace(policy(), allowed_search_locations=("South Korea", "Japan"))
    with pytest.raises(BriefInputError), override_policy_for_tests(wider):
        pass


def test_packet_revalidates_filters_against_the_current_contract() -> None:
    wider = replace(
        policy(), allowed_search_locations=("South Korea", "Japan"), default_search_location="Japan"
    )
    with override_policy_for_tests(wider):
        stale = SearchFilters(location="Japan")
    assert stale.location == "Japan"
    with pytest.raises(BriefInputError):
        _packet(_PACKET_ID, filters=stale)
    assert (
        _packet(_PACKET_ID, filters=SearchFilters(location="South Korea")).search_filters.location
        == "South Korea"
    )
