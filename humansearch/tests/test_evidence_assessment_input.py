"""AC-8 fingerprint and AC-9 evidence identity / input rejection."""

from __future__ import annotations

import dataclasses
import json
import os
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from ea_support import approved, config, ev, job, owner_table, payload, run, school

from humansearch import evidence_assessment as ea
from humansearch import evidence_assessment_cli as cli
from humansearch.evidence_assessment import evidence_id
from humansearch.tier_table import tier_table_from


def _hash(data: dict[str, object] | None = None, **tables: Any) -> str:
    return str(run(data or payload(), None, **tables)["fingerprint"]["input_sha256"])


def _changed_table(kind: str) -> Any:
    raw = owner_table(kind)
    first = next(iter(raw["tiers"]))
    return tier_table_from(raw | {"tiers": [first | {"verdict": "PARTIAL"}, *raw["tiers"][1:]]},
                           kind)  # type: ignore[arg-type]


# AC-8 --------------------------------------------------------------------------------------------
@pytest.mark.parametrize("field", ["model_version", "question_version", "mapping_version",
                                   "access_policy_version"])
def test_fingerprint_changes_with_each_version(field: str) -> None:
    changed = dataclasses.replace(config(), **{field: "jev-9.9.9" if field == "model_version" else "v-x"})
    assert _hash(cfg=changed) != _hash()


def _requirement(**change: object) -> dict[str, object]:
    data = payload()
    data["requirement"] = dict(data["requirement"]) | change  # type: ignore[call-overload]
    return data


@pytest.mark.parametrize("variant", [
    lambda: {"data": payload() | {"candidate_version": "cv-4"}},
    lambda: {"data": payload() | {"position_version": "pv-3"}},
    lambda: {"data": payload([ev("Ran the payment API on call!")])},
    lambda: {"data": _requirement(text="Operates production backend services!")},
    lambda: {"data": _requirement(weight=41)},
    lambda: {"data": payload(education=[school("합성중앙대학교")])},
    lambda: {"data": payload(career=[job("합성테크")])},
    lambda: {"cfg": dataclasses.replace(config(), confidence_floor=0.61)},
    lambda: {"schools": _changed_table("school")},
    lambda: {"companies": _changed_table("company")},
    lambda: {"schools": dataclasses.replace(approved("school"), version="school-tier-owner-v9")},
], ids=["candidate_version", "position_version", "evidence_one_char", "requirement_text",
        "requirement_weight", "education", "career", "confidence_floor", "school_table",
        "company_table", "school_version"])
def test_fingerprint_changes_with_input(variant: Callable[[], dict[str, Any]]) -> None:
    kwargs = variant()
    assert _hash(kwargs.pop("data", None), **kwargs) != _hash()


def test_fingerprint_changes_with_questions(monkeypatch: pytest.MonkeyPatch) -> None:
    before = _hash()
    monkeypatch.setattr(ea, "QUESTIONS", {"q1": dict(ea.QUESTIONS["q1"]) | {"instructions": "x"}})
    assert _hash() != before


def test_fingerprint_stable_for_order_and_collected_at() -> None:
    first = [ev("alpha work", locator="body:paragraph:1"), ev("beta work", locator="body:paragraph:2")]
    assert _hash(payload(first)) == _hash(payload(list(reversed(first))))
    recollected = [item | {"collected_at": "2026-09-22T00:00:00+09:00"} for item in first]
    assert _hash(payload(recollected)) == _hash(payload(first))


# AC-9 --------------------------------------------------------------------------------------------
def _ids(evidence: list[dict[str, object]]) -> list[str]:
    return list(run(payload(evidence), None)["fingerprint"]["evidence_ids"])


def test_evidence_identity_location_and_record_are_distinct() -> None:
    assert len(_ids([ev("same", locator="body:paragraph:1"), ev("same", locator="body:paragraph:2")])) == 2
    assert len(_ids([ev("same", record="gmail-message-1"), ev("same", record="gmail-message-2")])) == 2


def test_evidence_identity_duplicate_merges_to_one() -> None:
    once = ev("same")
    ids = _ids([once, once | {"collected_at": "2026-09-21T00:00:00+09:00"}])
    assert ids == [evidence_id("gmail_rec", "gmail-message-101", "body:paragraph:1",
                               str(once["text_sha256"]))]


def test_evidence_identity_text_length_boundary() -> None:
    assert len(_ids([ev("가" * 1500)])) == 1  # 1,500 characters are allowed
    for bad in (payload([ev("가" * 1501)]), payload(career=[job("합성테크", "가" * 1501)])):
        with pytest.raises(ValueError):
            run(bad, None)
    assert run(payload(career=[job("합성테크", "가" * 1500)]), None)["assessment"]["status"] == "not_run"


def test_evidence_identity_career_needs_contract_source() -> None:
    patterns = {k: v for k, v in config().source_locator_patterns.items() if k != "career_summary"}
    with pytest.raises(ValueError):
        run(payload(career=[job("합성테크")]), None,
            dataclasses.replace(config(), source_locator_patterns=patterns))


@pytest.mark.parametrize("data", [
    payload([ev("first"), ev("second")]),
    payload([ev("text") | {"text_sha256": "0" * 64}]),
    payload([ev(f"item {n}", locator=f"body:paragraph:{n}") for n in range(6)]),
    payload([]),
    payload([ev("bad locator", locator="paragraph-4")]),
    _requirement(weight=-1),
    _requirement(weight=101),
    payload(career=[job("합성테크") | {"start": "2019-13"}]),
    payload(career=[job("합성테크") | {"end": "soon"}]),
    payload(career=[job(" ")]),
    payload(career=[job("합성테크") | {"title": ""}]),
], ids=["same_locator_other_text", "hash_mismatch", "six_items", "empty", "locator", "weight_low",
        "weight_high", "career_start", "career_end", "career_company", "career_title"])
def test_evidence_identity_rejects_invalid(data: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        run(data, None)


# AC-20 (F14) -------------------------------------------------------------------------------------
@pytest.mark.parametrize("target", ["input", "config", "school", "company", "symlink", "hardlink", "dotdot"])
def test_output_collision_refused_without_writing(target: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
                                                  capsys: pytest.CaptureFixture[str]) -> None:
    (source := tmp_path / "in.json").write_text(json.dumps(payload()), encoding="utf-8")
    files = {"input": source} | {k: tmp_path / f"{k}.json" for k in ("config", "school", "company",
                                                                     "symlink", "hardlink")}
    for kind, origin in (("config", cli.CONTRACT_PATH), *cli.TIER_PATHS.items()):
        files[kind].write_bytes(origin.read_bytes())
    monkeypatch.setattr(cli, "TIER_PATHS", {kind: files[kind] for kind in cli.TIER_PATHS})  # tmp copies
    files["dotdot"] = tmp_path / "missing-dir" / ".." / "in.json"  # F18: equal only after resolve()
    files["symlink"].symlink_to(source)
    os.link(source, files["hardlink"])
    before = {path.name: path.read_bytes() for path in tmp_path.iterdir()}
    with pytest.raises(SystemExit) as stop:
        cli.main(["--input", str(source), "--output", str(files[target]), "--config", str(files["config"])])
    assert stop.value.code == 2 and json.loads(capsys.readouterr().err)["error_code"] == "output_collision"
    assert {path.name: path.read_bytes() for path in tmp_path.iterdir()} == before


def test_output_collision_protects_contract_with_outside_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
                                                                capsys: pytest.CaptureFixture[str]) -> None:
    """F16: an outside --config must not drop the repository contract from the collision list."""
    (source := tmp_path / "in.json").write_text(json.dumps(payload()), encoding="utf-8")
    (contract := tmp_path / "contract.json").write_bytes(cli.CONTRACT_PATH.read_bytes())
    (outside := tmp_path / "outside.json").write_bytes(cli.CONTRACT_PATH.read_bytes())
    monkeypatch.setattr(cli, "CONTRACT_PATH", contract)  # tmp copy stands in for the repo contract
    before = contract.read_bytes()
    with pytest.raises(SystemExit) as stop:
        cli.main(["--input", str(source), "--output", str(contract), "--config", str(outside)])
    assert stop.value.code == 2 and json.loads(capsys.readouterr().err)["error_code"] == "output_collision"
    assert contract.read_bytes() == before
