"""HS-13.02c — 합본 JD(한 문서에 2개 이상 포지션) 경고 필드.

계약: docs/engineering/humansearch-hs13-position-brief-goal-2026-09-10.md §4 "JD 합본" 행.

거부 근거는 러너가 관찰해 적는 구조화 입력 `JdSource.position_count` 다(HS-13.01b).
머리 줄 휴리스틱(`포지션:`·`Position:`·`직무:`·`## ` 제목이 2개 이상)은 **경고 전용**이다 —
단일 JD 의 `포지션:`+`직무:` 오탐과 `## A`/`## B` 미탐이 Codex 2차 실측 반례였기 때문에,
잡히더라도 `ok` 를 건드리지 않는다.

시계·파일·네트워크 접근 0, 전부 순수 함수다.
"""

from __future__ import annotations

import hashlib

from humansearch.brief import FidelityReport, JdSource, verify_fidelity


def _jd(text: str) -> JdSource:
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return JdSource(text=text, raw_sha256=digest, provided_by="U1")


# 한 포지션짜리 JD 인데 머리 줄이 둘이다 — 휴리스틱이 잡는 **오탐**.
_SINGLE_JD_TWO_HEADS = (
    "포지션: 검색 엔지니어\n"
    "직무: 랭킹 모델을 설계하고 검증한다\n"
    "자격: 파이썬으로 파이프라인을 작성할 수 있다\n"
)

# 진짜 합본 — 마크다운 제목 두 개.
_MERGED_MARKDOWN_JD = (
    "## 검색 엔지니어\n"
    "랭킹 모델을 설계하고 검증한다\n"
    "## 데이터 엔지니어\n"
    "스트리밍 파이프라인을 운영한다\n"
)

# 머리 줄이 하나뿐 — 경고 없음.
_SINGLE_HEAD_JD = "포지션: 검색 엔지니어\n랭킹 모델을 설계하고 검증한다\n"

_ENGLISH_TWO_HEADS = (
    "Position: Search Engineer\n"
    "랭킹 모델을 설계하고 검증한다\n"
    "Position: Data Engineer\n"
    "스트리밍 파이프라인을 운영한다\n"
)


# --- 1. 오탐이어도 경고는 뜬다(그리고 ok 는 그대로) ---------------------------


def test_single_jd_with_position_and_role_heads_is_hinted_but_still_ok() -> None:
    jd = _jd(_SINGLE_JD_TWO_HEADS)
    report = verify_fidelity(jd, _SINGLE_JD_TWO_HEADS)
    assert report.multi_position_hint == (
        "포지션: 검색 엔지니어",
        "직무: 랭킹 모델을 설계하고 검증한다",
    )
    assert report.ok is True


# --- 2. 마크다운 제목 2개도 잡는다 --------------------------------------------


def test_two_markdown_headings_are_hinted() -> None:
    jd = _jd(_MERGED_MARKDOWN_JD)
    report = verify_fidelity(jd, _MERGED_MARKDOWN_JD)
    assert report.multi_position_hint == ("## 검색 엔지니어", "## 데이터 엔지니어")
    assert report.ok is True


def test_english_position_prefix_is_hinted() -> None:
    jd = _jd(_ENGLISH_TWO_HEADS)
    report = verify_fidelity(jd, _ENGLISH_TWO_HEADS)
    assert report.multi_position_hint == (
        "Position: Search Engineer",
        "Position: Data Engineer",
    )


# --- 3. 1개 이하면 빈 튜플 ----------------------------------------------------


def test_one_head_line_produces_no_hint() -> None:
    jd = _jd(_SINGLE_HEAD_JD)
    assert verify_fidelity(jd, _SINGLE_HEAD_JD).multi_position_hint == ()


def test_no_head_line_produces_no_hint() -> None:
    text = "랭킹 모델을 설계하고 검증한다\n스트리밍 파이프라인을 운영한다\n"
    assert verify_fidelity(_jd(text), text).multi_position_hint == ()


# --- 4. ok 는 경고에 흔들리지 않는다 -------------------------------------------


def test_hint_does_not_change_ok_in_either_direction() -> None:
    """경고가 있어도 통과하고, 경고가 있는 채로 결함이 있으면 그 결함으로만 떨어진다."""
    jd = _jd(_MERGED_MARKDOWN_JD)
    dropped = _MERGED_MARKDOWN_JD.replace("스트리밍 파이프라인을 운영한다\n", "")
    report = verify_fidelity(jd, dropped)
    assert report.multi_position_hint == ("## 검색 엔지니어", "## 데이터 엔지니어")
    assert report.missing == ("스트리밍 파이프라인을 운영한다",)
    assert report.ok is False

    # 같은 JD·완전한 렌더링이면 경고가 둘이어도 ok.
    assert verify_fidelity(jd, _MERGED_MARKDOWN_JD).ok is True


def test_report_ok_ignores_multi_position_hint_directly() -> None:
    hinted = FidelityReport(
        missing=(),
        extra_condition=(),
        jd_line_count=2,
        rendered_line_count=2,
        extra_lines=(),
        multi_position_hint=("포지션: 가", "포지션: 나"),
    )
    assert hinted.ok is True


def test_multi_position_hint_defaults_to_empty() -> None:
    report = FidelityReport(missing=(), extra_condition=(), jd_line_count=1, rendered_line_count=1)
    assert report.multi_position_hint == ()
