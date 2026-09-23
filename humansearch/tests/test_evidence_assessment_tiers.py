"""AC-13..AC-16, AC-18, AC-19: school tiers, fixtures, career fallback, table approval, provenance."""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from typing import Any

import pytest
from ea_support import (
    APPROVAL,
    CONFIG_PATH,
    FIXTURE_EVIDENCE_SPECS,
    PLURAL,
    TABLE_PATHS,
    FakeJudge,
    constructor_spy,
    ev,
    fixture_evidence,
    job,
    live_config,
    owner_table,
    payload,
    raw_table,
    repo_table,
    run,
    run_cli,
    school_payload,
    strings_in,
)

from humansearch import evidence_assessment_cli as cli
from humansearch.tier_table import resolve_tier, tier_table_from


# AC-13 -------------------------------------------------------------------------------------------
def test_school_tier_t1_earns_weight_without_jev() -> None:
    judge = FakeJudge("CONTRADICTED")
    result = run(school_payload("합성제일대학교"), judge)
    assert judge.calls == [] and result["school_tier"]["tier"] == "T1"
    assert result["assessment"]["verdict"] == "SUPPORTED"
    assert result["coverage"]["supported_score"] == 30.0


@pytest.mark.parametrize("name", [
    "Owner First University", "SFU", "  sfu ", unicodedata.normalize("NFD", "합성제일대학교"),
    "합성제일\u00a0대학교", "합성제일대학교\u3000", "합성제일\u200b대학교",
], ids=["alias", "short", "spaced", "nfd", "nbsp", "ideographic_space", "zero_width"])
def test_school_tier_alias_and_unicode_map_to_same_tier(name: str) -> None:
    result = run(school_payload(name), FakeJudge("CONTRADICTED"))
    assert result["school_tier"]["tier"] == "T1" and result["school_tier"]["matched_school"] == name


def test_school_tier_unlisted_without_career_is_unknown_not_zero() -> None:
    result = run(school_payload("미등록 합성대학교"), FakeJudge("CONTRADICTED"))
    assert result["school_tier"]["tier"] == "UNLISTED" and result["school_tier"]["basis"] == "school"
    assert result["projection"]["proposed_criterion_status"] == "unknown"
    assert result["coverage"]["unknown_weight"] == 30.0 and result["coverage"]["confirmed_weight"] == 0.0


def test_school_tier_highest_of_two_is_recorded() -> None:
    tier = run(school_payload("합성지역대학교", "합성중앙대학교"), None)["school_tier"]
    assert (tier["tier"], tier["matched_school"], tier["education_index"]) == ("T2", "합성중앙대학교", 1)


def test_school_tier_name_never_reaches_jev_state() -> None:
    judge = FakeJudge("SUPPORTED")
    run(payload(education=[{"school_name": "합성제일대학교", "degree": "bachelor", "major": "CS",
                            "graduated_on": None}]), judge)
    assert not [value for value in strings_in(judge.calls[0]["state"]) if "합성제일" in value]


# AC-14 -------------------------------------------------------------------------------------------
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
KOREAN_NAME = re.compile(r"[김이박최정강조윤장임한오서신권황안송류홍][가-힣]{1,2}\s?(님|씨|후보자)")


def test_fixture_schema_matches_data_sot_shapes() -> None:
    patterns = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))["source_locator_patterns"]
    assert {kind for kind, _, _, _ in FIXTURE_EVIDENCE_SPECS} | {"career_summary"} == set(patterns)
    for kind, record, locator, _ in FIXTURE_EVIDENCE_SPECS:
        assert re.fullmatch(patterns[kind], locator) and re.fullmatch(r"[A-Za-z0-9_.:-]{1,128}", record)
    assert run(payload(fixture_evidence()[:5]), None)["assessment"]["status"] == "not_run"


def test_fixture_schema_has_no_real_contact_or_name() -> None:
    assert EMAIL.search("reach me at someone" + "@" + "example.com")  # positive control
    assert KOREAN_NAME.search("홍길동" + " 님")  # positive control
    for path in (*Path(__file__).parent.glob("*evidence_assessment*.py"), CONFIG_PATH,
                 *TABLE_PATHS.values(), Path(__file__).parent / "ea_support.py"):
        text = path.read_text(encoding="utf-8")
        assert EMAIL.search(text) is None and KOREAN_NAME.search(text) is None, path


# AC-15 -------------------------------------------------------------------------------------------
@pytest.mark.parametrize(("company", "choice", "expected"), [
    ("합성테크", "SUPPORTED", "SUPPORTED"), ("합성솔루션", "SUPPORTED", "PARTIAL"),
    ("합성테크", "PARTIAL", "PARTIAL"), ("미등록 합성회사", "SUPPORTED", "PARTIAL"),
    ("합성테크", "NOT_STATED", "NOT_STATED"), ("합성테크", "CONTRADICTED", "CONTRADICTED"),
    ("합성테크", "CONFLICTING", "CONFLICTING"), ("합성테크", None, None),
], ids=["t1_supported", "t3_supported", "t1_partial", "unlisted_supported", "not_stated",
        "contradicted", "conflicting", "jev_error"])
def test_career_fallback_combination_table(company: str, choice: str | None, expected: str | None) -> None:
    judge = FakeJudge(choice or "SUPPORTED", raises=None if choice else RuntimeError("down"))
    result = run(school_payload(career=[job(company)], evidence=[]), judge)
    tier, assessment = result["school_tier"], result["assessment"]
    assert tier["basis"] == "career" and tier["matched_company"] == company and len(judge.calls) == 1
    assert assessment["verdict"] == expected
    assert assessment["status"] == ("completed" if choice else "error")
    assert assessment["requires_human_review"] is (expected not in ("SUPPORTED", "PARTIAL", "NOT_STATED"))
    assert judge.calls[0]["state"] == {"requirement": "Runs large backend systems",
                                       "evidence": {"E1": "Ran the order platform on call."}}


@pytest.mark.parametrize("education", [(), ("미등록 합성대학교", "Unknown Sample College")],
                         ids=["no_education", "all_unlisted"])
def test_career_fallback_replaces_missing_school(education: tuple[str, ...]) -> None:
    career = [job("미등록 합성회사", "Did sales."), job("합성테크(주)", "Built payment systems.")]
    judge = FakeJudge("SUPPORTED")
    result = run(school_payload(*education, career=career), judge)
    tier = result["school_tier"]
    assert (tier["basis"], tier["company_tier"], tier["career_index"]) == ("career", "T1", 1)
    assert judge.calls[0]["state"]["evidence"] == {"E1": "Built payment systems."}
    assert not [s for s in strings_in(judge.calls[0]["state"]) if "합성테크" in s]


def test_career_fallback_skipped_when_school_is_listed() -> None:
    judge = FakeJudge("CONTRADICTED")
    result = run(school_payload("합성중앙대학교", career=[job("합성테크")]), judge)
    assert judge.calls == [] and result["school_tier"]["basis"] == "school"
    assert result["assessment"]["verdict"] == "PARTIAL"


# AC-16 -------------------------------------------------------------------------------------------
@pytest.mark.parametrize(("kind", "career"), [("school", None), ("company", [job("합성테크")]),
                                            ("school", [job("합성테크")])],
                         ids=["school_table", "company_table", "school_table_on_career_path"])
def test_table_status_unapproved_never_scores(kind: str, career: Any) -> None:
    names = () if career else ("합성제일대학교",)
    result = run(school_payload(*names, career=career, evidence=[] if career else None),
                 FakeJudge("SUPPORTED"), **{PLURAL[kind]: repo_table(kind)})
    assert result["assessment"]["verdict"] == "SUPPORTED" and result["assessment"]["status"] == "completed"
    assert result["projection"] is None and result["coverage"] is None
    assert result["assessment"]["requires_human_review"] is True
    status = result["school_tier"]["table_status" if kind == "school" else "company_table_status"]
    assert status == "SYNTHETIC_PLACEHOLDER_OWNER_TO_FILL"


def _bad(kind: str, case: str) -> dict[str, Any]:
    raw, owner = raw_table(kind), owner_table(kind)
    first, *_, last = owner[PLURAL[kind]]  # F17: T1 first row, T3 last row
    return {
        "status_only": raw | {"status": "APPROVED", "approval": APPROVAL},
        "marker_in_version": owner | {f"{kind}_tier_version": "tier-placeholder-v1"},
        "marker_in_name": owner | {PLURAL[kind]: {"Synthetic Row": {"tier": "T1", "synthetic": False}},
                                   "aliases": {}},
        "marker_in_alias": owner | {"aliases": owner["aliases"] | {"Synthetic Alias": next(iter(
            owner[PLURAL[kind]]))}},
        "marker_fullwidth": owner | {PLURAL[kind]: {"\uff33ynthetic Row": {"tier": "T1", "synthetic": False}},
                                     "aliases": {}},
        "alias_unknown": owner | {"aliases": {"Ghost": "Nobody"}},
        "name_collision": owner | {PLURAL[kind]: {"Row A": {"tier": "T1", "synthetic": False},
                                                  "rowa": {"tier": "T3", "synthetic": False}}, "aliases": {}},
        "alias_shadows_entry": owner | {"aliases": owner["aliases"] | {f" {first} ": last}},
        "alias_collision": owner | {"aliases": owner["aliases"] | {"Dup Alias": first, "dupalias": last}},
        "rank_gap": owner | {"tiers": [tier | {"rank": tier["rank"] * 10} for tier in owner["tiers"]]},
        "flag_left": owner | {PLURAL[kind]: {"Row": {"tier": "T1", "synthetic": True}}, "aliases": {}},
        "flag_missing": owner | {PLURAL[kind]: {"Row": {"tier": "T1"}}, "aliases": {}},
        "approval_by_blank": owner | {"approval": APPROVAL | {"approved_by": " "}},
        "approval_at_bad": owner | {"approval": APPROVAL | {"approved_at": "2026-9-23"}},
        "approval_source_missing": owner | {"approval": {"approved_by": "o", "approved_at": "2026-09-23"}},
        "approval_null": owner | {"approval": None},
        "status_missing": {k: v for k, v in owner.items() if k != "status"},
        "status_undefined": owner | {"status": "DRAFT"},
        "tier_rejects": owner | {"tiers": [owner["tiers"][0] | {"verdict": "CONTRADICTED"},
                                          *owner["tiers"][1:]]},
    }[case]


@pytest.mark.parametrize("kind", ["school", "company"])
@pytest.mark.parametrize("case", ["status_only", "marker_in_version", "marker_in_name",
                                  "marker_in_alias", "marker_fullwidth", "alias_unknown",
                                  "name_collision", "alias_shadows_entry", "alias_collision",
                                  "rank_gap", "flag_left",
                                  "flag_missing", "approval_by_blank", "approval_at_bad",
                                  "approval_source_missing", "approval_null", "status_missing",
                                  "status_undefined", "tier_rejects"])
def test_table_status_loader_rejects(kind: str, case: str, tmp_path: Path,
                                    monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(ValueError):
        tier_table_from(_bad(kind, case), kind)  # type: ignore[arg-type]
    (path := tmp_path / "t.json").write_text(json.dumps(_bad(kind, case), ensure_ascii=False))
    monkeypatch.setattr(cli, "TIER_PATHS", TABLE_PATHS | {kind: path}, raising=False)  # code-only seam
    run_cli(tmp_path, payload(), code=2)


@pytest.mark.parametrize("kind", ["school", "company"])
@pytest.mark.parametrize("case", ["self_alias", "aliases_share_target"])
def test_table_status_loader_accepts_aliases_that_agree(kind: str, case: str) -> None:
    """F17 must not reject an alias that resolves to the row it already names."""
    owner = owner_table(kind)
    first = next(iter(owner[PLURAL[kind]]))
    extra = {"self_alias": {f" {first} ": first},
             "aliases_share_target": {"Dup Alias": first, "dupalias": first}}[case]
    table = tier_table_from(owner | {"aliases": owner["aliases"] | extra}, kind)  # type: ignore[arg-type]
    assert resolve_tier(["Dup Alias", first], table)[0] == owner[PLURAL[kind]][first]["tier"]


@pytest.mark.parametrize("kind", ["school", "company"])
def test_table_status_cli_reads_only_repo_tables(kind: str, tmp_path: Path) -> None:
    """F15: no CLI argument can swap in an outside APPROVED table; injection is assess_evidence-only."""
    (path := tmp_path / "approved.json").write_text(json.dumps(owner_table(kind), ensure_ascii=False))
    for extra in ((f"--{kind}-tiers", str(path)), (f"--{kind}-tiers={path}",)):
        assert run_cli(tmp_path, school_payload("Owner First University"), *extra, code=2) == {}
    tier = run_cli(tmp_path, school_payload("SFU"))["school_tier"]
    assert (tier["school_tier_version"], tier["table_status"]) == (repo_table("school").version,
                                                                   repo_table("school").status)
    assert tier["company_tier_version"] == repo_table("company").version


def test_table_status_approved_owner_copy_scores() -> None:
    result = run(school_payload(career=[job("합성테크")], evidence=[]), FakeJudge("SUPPORTED"))
    assert result["school_tier"]["table_status"] == result["school_tier"]["company_table_status"]
    assert result["school_tier"]["table_status"] == "APPROVED"
    assert result["coverage"]["supported_score"] == 30.0 and not result["assessment"]["requires_human_review"]


# AC-18 -------------------------------------------------------------------------------------------
def test_provenance_school_uses_education_index_not_evidence() -> None:
    result = run(school_payload("미등록 합성대학교", "합성제일대학교"), None)
    assert result["projection"]["evidence_ids"] == [] == result["assessment"]["evidence_ids"]
    assert result["school_tier"]["education_index"] == 1 and result["fingerprint"]["evidence_ids"]


def test_provenance_career_uses_only_its_summary() -> None:
    career = [job("미등록 합성회사", "Did sales."), job("합성테크", "Built payment systems.")]
    result = run(school_payload(career=career), FakeJudge("PARTIAL"))
    assert result["projection"]["evidence_ids"] == ["career:1"] == result["assessment"]["evidence_ids"]


# AC-19 (CLI production call shape) ---------------------------------------------------------------
def test_career_only_input_completes(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("TYPESAFE_API_KEY", "synthetic-key-not-real")
    constructor_spy(monkeypatch, FakeJudge("SUPPORTED"))
    result = run_cli(tmp_path, school_payload(career=[job("합성테크")], evidence=[]), "--live-jev",
                     cfg=live_config())
    assert result["assessment"]["status"] == "completed" and result["school_tier"]["basis"] == "career"
    assert result["assessment"]["evidence_ids"] == ["career:0"] and result["request_attempts"] == 1


def test_career_only_input_needs_evidence_or_career(tmp_path: Path) -> None:
    assert run_cli(tmp_path, school_payload(evidence=[]), code=2) == {}


def test_career_only_input_other_requirement_is_not_run(tmp_path: Path) -> None:
    result = run_cli(tmp_path, payload([], career=[job("합성테크")]))
    assert (result["assessment"]["status"], result["assessment"]["error_reason"]) == ("not_run", "no_evidence")


def test_career_only_input_rejects_forged_career_evidence(tmp_path: Path) -> None:
    forged = ev("Built payment systems.", source_type="career_summary", locator="career:0")
    assert run_cli(tmp_path, school_payload(career=[job("합성테크")], evidence=[forged]), code=2) == {}
