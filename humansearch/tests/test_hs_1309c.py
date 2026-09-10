"""HS-13.09c — packet_id 에서 날짜를 뺀다(같은 포지션·같은 JD 는 언제 만들어도 같은 패킷이다).

계약: docs/engineering/humansearch-hs13-position-brief-goal-2026-09-10.md §7 D9 · §5 packet.py.

왜 바꾸나(Codex 5차 높음): `packet_id` 가 `{yyyymmdd}-{clickup}-{sha8}` 이면 자정을 넘긴 뒤
같은 포지션·같은 JD 로 만든 패킷이 **새 장부 파일 이름**을 갖는다. 장부는 파일 이름으로
at-most-once 를 지키므로(D9), 이름이 갈리는 순간 승인 없이 재발송이 열린다.
날짜는 식별자에서 빼고 `SearchPacket.created_on` 필드로 따로 남긴다 — 기록은 남되
동일성 판정에는 끼지 않는다.

시계·네트워크 접근 0. 날짜는 전부 호출자가 주입한다.
"""

from __future__ import annotations

import hashlib
import inspect
import json
import os
from datetime import UTC, date, datetime
from pathlib import Path

import pytest

from humansearch.brief import (
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
    SearchPacket,
    SendIntent,
    SendState,
    SourceRef,
    TeamMail,
    from_json,
    may_send,
    packet_id,
    record_intent,
    to_json,
)

# --- 합성 자료 (실명 0) -------------------------------------------------------

_JD_TEXT = "직무: 데이터 엔지니어\n요구: 스트리밍 파이프라인 3년"
_OTHER_JD_TEXT = "직무: 데이터 엔지니어\n요구: 배치 파이프라인 5년"
_RAW_SHA = hashlib.sha256(_JD_TEXT.encode("utf-8")).hexdigest()
_OTHER_RAW_SHA = hashlib.sha256(_OTHER_JD_TEXT.encode("utf-8")).hexdigest()
_CLICKUP = "86e1c0de"
_DAY_A = date(2026, 9, 10)
_DAY_B = date(2026, 9, 11)
_AT_A = datetime(2026, 9, 10, 23, 50, 0, tzinfo=UTC)
_LEAD_URL = "https://www.linkedin.com/in/example-lead"

# 날짜가 붙어 있던 옛 형식. 새 계약에서는 거부되어야 한다.
_LEGACY_PACKET_ID = "20260910-abc-deadbeef"


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _position(clickup: str = _CLICKUP) -> PositionSpec:
    return PositionSpec(clickup, "예시 고객사", "데이터 엔지니어", None, "정규직", "서울", None)


def _jd(text: str = _JD_TEXT) -> JdSource:
    return JdSource(text, _sha256(text), "U1")


def _packet(
    *,
    identifier: str | None = None,
    created_on: date = _DAY_A,
    jd: JdSource | None = None,
) -> SearchPacket:
    source = _jd() if jd is None else jd
    body = "예시 문구\n내부 공유 본문"
    return SearchPacket(
        packet_id=packet_id(_position(), source) if identifier is None else identifier,
        created_on=created_on,
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
                headline="데이터 엔지니어",
                linkedin_url=_LEAD_URL,
                education="예시대학원 석사",
                career="예시사 3년",
                match_reasons=("스트리밍 파이프라인 경험",),
                check_points=("도메인 적합성",),
                evidence=CandidateEvidence(("스트리밍",), 1, 2, "석사", 2, (24, 18), 2, 8, 10),
                score=ScoreBreakdown(30, 15, 15, 15),
                email=EmailContact("lead@example.org", "https://example.org/lab", "연구실"),
                degree=ConnectionDegree.SECOND,
                source_note="공개 프로필 URL 일치",
            ),
        ),
        mail=TeamMail(
            subject="[포지션]예시 고객사, 데이터 엔지니어",
            to=("sangmokang@valueconnect.kr",),
            cc=(),
            body=body,
            body_sha256=_sha256(body),
        ),
        boolean_queries=('("Data Engineer" OR 데이터) AND 파이프라인',),
        inmails=((_LEAD_URL, "안녕하세요, 포지션을 제안드립니다."),),
    )


def _ledger(tmp_path: Path) -> Path:
    directory = tmp_path / "ledger"
    directory.mkdir(mode=0o700)
    os.chmod(directory, 0o700)
    return directory


def _intent(identifier: str, recorded_at: datetime = _AT_A) -> SendIntent:
    return SendIntent(
        packet_id=identifier,
        channel="gmail",
        attempt=1,
        recipients_sha256=_sha256("sangmokang@valueconnect.kr"),
        body_sha256=_sha256("본문"),
        recorded_at=recorded_at,
        state=SendState.INTENT,
    )


# --- 1. packet_id 는 날짜를 담지 않는다 ---------------------------------------


def test_packet_id_is_clickup_and_sha8_without_any_date() -> None:
    value = packet_id(_position(), _jd())
    assert value == f"{_CLICKUP}-{_RAW_SHA[:8]}"
    # 날짜 조각이 들어오면 하이픈이 하나 더 생긴다 — 조각 수로 못을 박는다.
    assert value.count("-") == 1


def test_packet_id_takes_no_clock_parameter() -> None:
    """시계를 받지 않아야 날짜가 다시 끼어들 길이 막힌다(변이 ⓐ 정조준)."""
    names = tuple(inspect.signature(packet_id).parameters)
    assert names == ("position", "jd")


def test_packet_id_is_identical_for_the_same_position_and_jd() -> None:
    """자정을 넘겨 다시 만들어도 같은 값 — 호출에 날짜가 없으므로 날짜로 갈릴 수 없다."""
    first = packet_id(_position(), _jd())
    second = packet_id(_position(), _jd())
    assert first == second
    assert _packet(created_on=_DAY_A).packet_id == _packet(created_on=_DAY_B).packet_id


def test_packet_id_changes_when_the_jd_hash_changes() -> None:
    assert _OTHER_RAW_SHA[:8] != _RAW_SHA[:8]
    assert packet_id(_position(), _jd(_OTHER_JD_TEXT)) == f"{_CLICKUP}-{_OTHER_RAW_SHA[:8]}"
    assert packet_id(_position(), _jd(_OTHER_JD_TEXT)) != packet_id(_position(), _jd())


def test_packet_id_rejects_clickup_id_outside_contract_shape() -> None:
    with pytest.raises(BriefInputError):
        packet_id(_position("86e1/../etc"), _jd())


# --- 2. 정규식 계약 — 옛 날짜 형식은 거부 ------------------------------------


def test_search_packet_rejects_legacy_dated_packet_id() -> None:
    with pytest.raises(BriefInputError):
        _packet(identifier=_LEGACY_PACKET_ID)


def test_search_packet_accepts_the_dateless_packet_id() -> None:
    packet = _packet()
    assert packet.packet_id == f"{_CLICKUP}-{_RAW_SHA[:8]}"


# --- 3. created_on 은 필드로 남는다 -------------------------------------------


def test_created_on_survives_json_round_trip() -> None:
    original = _packet(created_on=_DAY_B)
    restored = from_json(to_json(original))
    assert restored == original
    assert restored.created_on == _DAY_B
    assert json.loads(to_json(original))["created_on"] == "2026-09-11"


def test_created_on_rejects_a_datetime() -> None:
    """datetime 은 date 의 하위 타입이라 그냥 두면 JSON 왕복이 깨진다."""
    with pytest.raises(BriefInputError):
        _packet(created_on=datetime(2026, 9, 10, 12, 0, tzinfo=UTC))  # type: ignore[arg-type]


# --- 4. AC (§7 D9) — 날짜가 바뀌어도 재발송이 열리지 않는다 --------------------


def test_next_day_rebuild_cannot_open_a_second_send(tmp_path: Path) -> None:
    """날짜 A 에 intent 를 남기고 날짜 B 로 같은 포지션·JD 패킷을 다시 만들면 발송 0."""
    directory = _ledger(tmp_path)
    day_a = _packet(created_on=_DAY_A)
    recorded, created = record_intent(directory, _intent(day_a.packet_id))
    assert created is True
    assert recorded.attempt == 1

    day_b = _packet(created_on=_DAY_B)
    assert day_b.packet_id == day_a.packet_id
    assert day_b.created_on != day_a.created_on

    assert may_send(directory, day_b.packet_id, "gmail") is False
    again, created_again = record_intent(directory, _intent(day_b.packet_id))
    assert created_again is False
    assert again.attempt == 1
    # 장부 파일은 여전히 한 개다 — 이름이 갈렸다면 두 개가 됐을 것이다.
    assert sorted(p.name for p in directory.glob("*.sent.json")) == [
        f"{day_a.packet_id}.gmail.a1.sent.json"
    ]
