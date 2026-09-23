"""Shared synthetic fixtures for the evidence-assessment acceptance tests (goal AC-1..AC-19)."""

from __future__ import annotations

import dataclasses
import functools
import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pytest

from humansearch import evidence_assessment_cli as cli
from humansearch.evidence_assessment import EvidenceVerdict, assess_evidence, load_evidence_config
from humansearch.tier_table import TierTable, load_tier_table, tier_table_from

ROOT = Path(__file__).parents[2]
CONFIG_PATH = ROOT / "contracts/jev-evidence-assessment.json"
TABLE_PATHS = {"school": ROOT / "contracts/school-tier.json",
               "company": ROOT / "contracts/company-tier.json"}
PLURAL = {"school": "schools", "company": "companies"}
APPROVAL = {"approved_by": "owner-test", "approved_at": "2026-09-23", "source": "test-injection"}
VERDICTS = [item.value for item in EvidenceVerdict]
EXPECTED_PROJECTION = {"SUPPORTED": "met", "PARTIAL": "partial", "NOT_STATED": "unknown",
                       "CONTRADICTED": "unmet", "CONFLICTING": None}


@functools.cache
def config() -> Any:
    return load_evidence_config(CONFIG_PATH)


def raw_table(kind: str) -> dict[str, Any]:
    return dict(json.loads(TABLE_PATHS[kind].read_text(encoding="utf-8")))


def owner_table(kind: str) -> dict[str, Any]:
    """Test-only APPROVED copy: synthetic markers removed, approval complete (code injection)."""
    raw = raw_table(kind)

    def fix(text: str) -> str:
        return text.replace("Synthetic", "Owner").replace("synthetic", "owner")

    return raw | {
        f"{kind}_tier_version": fix(raw[f"{kind}_tier_version"]), "status": "APPROVED",
        "approval": APPROVAL,
        PLURAL[kind]: {fix(k): v | {"synthetic": False} for k, v in raw[PLURAL[kind]].items()},
        "aliases": {fix(k): fix(v) for k, v in raw["aliases"].items()},
    }


@functools.cache
def approved(kind: str) -> TierTable:
    return tier_table_from(owner_table(kind), kind)  # type: ignore[arg-type]


def repo_table(kind: str) -> TierTable:
    return load_tier_table(TABLE_PATHS[kind], kind)  # type: ignore[arg-type]


def ev(text: str, *, source_type: str = "gmail_rec", record: str = "gmail-message-101",
       locator: str = "body:paragraph:1") -> dict[str, object]:
    return {
        "source_type": source_type, "source_record_id": record, "source_locator": locator,
        "occurred_at": "2026-08-01T09:00:00+09:00", "collected_at": "2026-09-20T10:00:00+09:00",
        "text": text, "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
    }


def school(name: str) -> dict[str, object]:
    return {"school_name": name, "degree": "bachelor", "major": "CS", "graduated_on": "2015-02"}


def job(company: str, summary: str = "Ran the order platform on call.") -> dict[str, object]:
    return {"company_name": company, "title": "Backend engineer", "start": "2019-03",
            "end": None, "summary": summary}


def payload(evidence: list[dict[str, object]] | None = None, *,
            requirement_id: str = "backend_operations",
            text: str = "Operates production backend services", weight: float = 40,
            education: list[dict[str, object]] | None = None,
            career: list[dict[str, object]] | None = None) -> dict[str, object]:
    return {
        "candidate_ref": "cand-pseudo-0001", "candidate_version": "cv-3",
        "position_ref": "pos-synthetic-01", "position_version": "pv-2",
        "requirement": {"requirement_id": requirement_id, "text": text, "weight": weight},
        "education": education or [], "career": career or [],
        "evidence": [ev("Ran the payment API on call.")] if evidence is None else evidence,
    }


def school_payload(*names: str, career: list[dict[str, object]] | None = None,
                   evidence: list[dict[str, object]] | None = None) -> dict[str, object]:
    return payload(evidence, requirement_id="school_tier", text="Runs large backend systems",
                   weight=30, education=[school(name) for name in names], career=career)


def jev_response(choice: str, *, confidence: float = 0.9, model: str = "jev-1.13.0") -> dict[str, Any]:
    probabilities = {name: 0.05 for name in VERDICTS} | {choice: 0.8}
    return {"model": model,
            "answers": {"q1": {"type": "choice", "choice": choice,
                               "probabilities": probabilities, "confidence": confidence}},
            "usage": {"input_tokens": 10, "output_tokens": 2}}


class FakeJudge:
    def __init__(self, choice: str = "SUPPORTED", *, confidence: float = 0.9,
                 raises: Exception | None = None, raw: Mapping[str, object] | None = None) -> None:
        self.choice, self.confidence, self.raises, self.raw = choice, confidence, raises, raw
        self.calls: list[dict[str, Any]] = []

    def evaluate(self, *, state: Mapping[str, object], questions: Mapping[str, Any],
                 model: str, timeout_seconds: float) -> Mapping[str, object]:
        self.calls.append({"state": state, "questions": questions, "model": model,
                           "timeout_seconds": timeout_seconds})
        if self.raises is not None:
            raise self.raises
        return self.raw if self.raw is not None else jev_response(self.choice, confidence=self.confidence)

    def close(self) -> None:
        return None


def run(data: Mapping[str, object], judge: Any, cfg: Any = None, schools: Any = None,
        companies: Any = None) -> dict[str, Any]:
    return dict(assess_evidence(data, config=cfg or config(), school_tiers=schools or approved("school"),
                                company_tiers=companies or approved("company"), judge=judge))


def run_cli(tmp_path: Path, data: Mapping[str, object], *extra: str, cfg: Any = None,
            code: int = 0) -> dict[str, Any]:
    """The CLI takes no tier-table paths (F15): it reads the repository contracts only."""
    source, output = tmp_path / "input.json", tmp_path / "output.json"
    source.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    argv = ["--input", str(source), "--output", str(output), *extra]
    try:
        assert cli.main(argv, config=cfg) == code
    except SystemExit as stop:
        assert stop.code == code
        assert not output.exists()
        return {}
    return dict(json.loads(output.read_text(encoding="utf-8")))


def live_config() -> Any:
    return dataclasses.replace(config(), live_calls_allowed=True)


def constructor_spy(monkeypatch: pytest.MonkeyPatch, judge: Any) -> list[int]:
    calls: list[int] = []

    def build(*args: object, **kwargs: object) -> Any:
        calls.append(1)
        return judge

    monkeypatch.setattr(cli, "TypeSafeJevJudge", build)
    return calls


def strings_in(value: object) -> list[str]:
    if isinstance(value, Mapping):
        return [s for key, item in value.items() for s in [str(key), *strings_in(item)]]
    if isinstance(value, list | tuple):
        return [s for item in value for s in strings_in(item)]
    return [str(value)]


FIXTURE_EVIDENCE_SPECS = [
    ("gmail_rec", "gmail-message-101", "body:paragraph:2", "Operated payment API on call rotation."),
    ("gmail_reply", "gmail-message-102", "body:paragraph:1", "Client asked about Kafka depth."),
    ("resume_attachment", "gmail-message-101", "att:resume-synthetic-01.pdf:page:3:block:7",
     "Led migration of order service to event streaming."),
    ("rps_card", "rps-profile-0001", "card:experience:1", "Backend engineer at synthetic company."),
    ("clickup", "clickup-task-77", "comment:938472", "Recruiter note: strong on-call ownership."),
    ("note", "note-synthetic-1", "note:1", "Phone screen: prefers backend platform work."),
]


def fixture_evidence() -> list[dict[str, object]]:
    return [ev(text, source_type=kind, record=record, locator=locator)
            for kind, record, locator, text in FIXTURE_EVIDENCE_SPECS]
