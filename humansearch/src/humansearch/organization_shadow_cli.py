"""Organization shadow review CLI. Live Jev needs ``--live-jev`` and ``TYPESAFE_API_KEY``;
``delivery_status`` reports whether a request was attempted."""

import argparse
import json
import os
import sys
import tempfile
from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict
from datetime import date, datetime
from pathlib import Path
from typing import Any, Never

from humansearch.organization_reference import (
    CohortKey,
    EmploymentStatus,
    ReferenceObservation,
    RoleEvidence,
    build_pattern_snapshot,
)
from humansearch.organization_shadow import ShadowConfig, load_shadow_config, run_shadow_review
from humansearch.organization_shadow_jev import TypeSafeJevJudge
from humansearch.recruiting_review import (
    Criterion,
    CriterionStatus,
    ExperiencePeriod,
    review_candidate,
)


class CountingJudge:
    """Builds the SDK client right before the first request and counts every attempt, so a
    timeout or 5xx after sending still reports EXTERNAL_JEV (never under-report delivery)."""

    def __init__(self, factory: Callable[[], TypeSafeJevJudge]) -> None:
        self.request_attempts = 0
        self._factory = factory
        self._judge: TypeSafeJevJudge | None = None

    def evaluate(self, *, state: Mapping[str, object], questions: Mapping[str, Mapping[str, Any]],
                 model: str, timeout_seconds: float) -> Mapping[str, object]:
        self._judge = self._judge or self._factory()
        self.request_attempts += 1
        return self._judge.evaluate(state=state, questions=questions, model=model,
                                    timeout_seconds=timeout_seconds)

    def close(self) -> None:
        if self._judge is not None:
            self._judge.close()


def delivery(judge: CountingJudge | None) -> dict[str, object]:
    attempts = 0 if judge is None else judge.request_attempts
    return {"delivery_status": "EXTERNAL_JEV" if attempts else "LOCAL_ONLY", "request_attempts": attempts}


class SafeInputError(ValueError):
    """Input error carrying a field name but never the rejected value."""

    def __init__(self, field: str) -> None:
        super().__init__(field)
        self.field = field


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a local-only organization shadow review")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--live-jev", action="store_true")
    args = parser.parse_args(argv)
    judge: CountingJudge | None = None
    try:
        payload = _load_input(args.input)
        config = load_shadow_config(args.config)
        if args.live_jev and os.environ.get("TYPESAFE_API_KEY", "").strip():
            judge = CountingJudge(TypeSafeJevJudge)
        try:
            result = _evaluate(payload, config=config, judge=judge)
        finally:
            if judge is not None:
                judge.close()
        _write_atomic(args.output, {**result, **delivery(judge)})
    except SafeInputError as error:
        _fail("invalid_input", judge, field=error.field)
    except OSError, ValueError, TypeError, json.JSONDecodeError:
        _fail("invalid_input_or_config", judge)
    except Exception:  # noqa: BLE001 - the CLI must not print raw SDK or candidate data.
        _fail("shadow_execution_failed", judge)
    return 0


def _load_input(path: Path) -> Mapping[str, object]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    root = _mapping(raw, "input")
    _exact_keys(
        root,
        {
            "as_of",
            "known_denominator",
            "criteria",
            "relevant_experience",
            "a_input_fingerprint",
            "jd_evidence",
            "candidate_evidence",
            "reference_observations",
        },
        "input",
    )
    return root


def _evaluate(
    payload: Mapping[str, object], *, config: ShadowConfig, judge: CountingJudge | None
) -> Mapping[str, object]:
    as_of = _date(payload["as_of"], "as_of")
    criteria = _criteria(payload["criteria"])
    periods = _experience(payload["relevant_experience"])
    fingerprint = _mapping(payload["a_input_fingerprint"], "a_input_fingerprint")
    jd_evidence = _role_evidence(payload["jd_evidence"], "jd_evidence")
    candidate_evidence = _role_evidence(payload["candidate_evidence"], "candidate_evidence")
    observations = _observations(payload["reference_observations"])
    denominator = _optional_nonnegative_int(payload["known_denominator"], "known_denominator")
    a_review = review_candidate(
        criteria=criteria,
        relevant_experience=periods,
        as_of=as_of,
        input_fingerprint=fingerprint,
    )
    snapshot = build_pattern_snapshot(
        observations,
        as_of=as_of,
        known_denominator=denominator,
        pattern_version=config.pattern_version,
        minimum_cohort_size=config.minimum_cohort_size,
        minimum_distinct_people=config.minimum_distinct_people,
        stale_after_days=config.stale_after_days,
    )
    result = run_shadow_review(
        a_review=a_review,
        jd_evidence=jd_evidence,
        candidate_evidence=candidate_evidence,
        pattern_snapshot=snapshot,
        config=config,
        judge=judge,
    )
    semantic = result.semantic
    return {
        "a": asdict(result.a_review),
        "semantic": {
            "status": semantic.status.value,
            "error_code": semantic.error_code,
            "b_organization_similarity": semantic.organization_similarity,
            "c_transferable_experience": semantic.transferable_experience,
            "d_additional_checks": semantic.additional_checks,
        },
        "ledger": {
            "schema_version": result.schema_version,
            "model_version": semantic.model_version,
            "question_version": semantic.question_version,
            "threshold_version": semantic.threshold_version,
            "pattern_version": semantic.pattern_version,
            "input_hash": semantic.input_hash,
            "primitive_answers": semantic.primitive_answers,
            "answer_metadata": {
                name: {
                    "probabilities_available": "probabilities" in answer,
                    "confidence_available": "confidence" in answer,
                }
                for name, answer in semantic.primitive_answers.items()
            },
            "human_review_status": semantic.human_review_status.value,
        },
    }


def _criteria(raw: object) -> tuple[Criterion, ...]:
    values = _list(raw, "criteria")
    parsed: list[Criterion] = []
    for index, value in enumerate(values):
        field = f"criteria[{index}]"
        item = _mapping(value, field)
        _exact_keys(item, {"key", "label", "weight", "status", "required", "evidence"}, field)
        parsed.append(
            Criterion(
                key=_text(item["key"], f"{field}.key"),
                label=_text(item["label"], f"{field}.label"),
                weight=_number(item["weight"], f"{field}.weight"),
                status=CriterionStatus(_text(item["status"], f"{field}.status")),
                required=_boolean(item["required"], f"{field}.required"),
                evidence=_strings(item["evidence"], f"{field}.evidence", allow_empty=True),
            )
        )
    return tuple(parsed)


def _experience(raw: object) -> tuple[ExperiencePeriod, ...]:
    values = _list(raw, "relevant_experience")
    parsed: list[ExperiencePeriod] = []
    for index, value in enumerate(values):
        field = f"relevant_experience[{index}]"
        item = _mapping(value, field)
        _exact_keys(item, {"start", "end"}, field)
        end = item["end"]
        parsed.append(
            ExperiencePeriod(
                start=_date(item["start"], f"{field}.start"),
                end=None if end is None else _date(end, f"{field}.end"),
            )
        )
    return tuple(parsed)


def _observations(raw: object) -> tuple[ReferenceObservation, ...]:
    values = _list(raw, "reference_observations")
    parsed: list[ReferenceObservation] = []
    for index, value in enumerate(values):
        field = f"reference_observations[{index}]"
        item = _mapping(value, field)
        _exact_keys(
            item,
            {
                "observation_id",
                "person_id",
                "cohort",
                "employment_status",
                "observation_date",
                "source_timestamp",
                "evidence_ids",
                "role_evidence",
            },
            field,
        )
        parsed.append(
            ReferenceObservation(
                observation_id=_text(item["observation_id"], f"{field}.observation_id"),
                person_id=_text(item["person_id"], f"{field}.person_id"),
                cohort=_cohort(item["cohort"], f"{field}.cohort"),
                employment_status=EmploymentStatus(
                    _text(item["employment_status"], f"{field}.employment_status")
                ),
                observation_date=_date(item["observation_date"], f"{field}.observation_date"),
                source_timestamp=_datetime(item["source_timestamp"], f"{field}.source_timestamp"),
                evidence_ids=_strings(item["evidence_ids"], f"{field}.evidence_ids"),
                role_evidence=_role_evidence(item["role_evidence"], f"{field}.role_evidence"),
            )
        )
    return tuple(parsed)


def _cohort(raw: object, field: str) -> CohortKey:
    item = _mapping(raw, field)
    _exact_keys(
        item,
        {"canonical_company_id", "role_family", "seniority", "team_product_scope"},
        field,
    )
    scope = item["team_product_scope"]
    return CohortKey(
        canonical_company_id=_text(item["canonical_company_id"], f"{field}.canonical_company_id"),
        role_family=_text(item["role_family"], f"{field}.role_family"),
        seniority=_text(item["seniority"], f"{field}.seniority"),
        team_product_scope=None if scope is None else _text(scope, f"{field}.team_product_scope"),
    )


def _role_evidence(raw: object, field: str) -> RoleEvidence:
    item = _mapping(raw, field)
    names = {
        "primary_role_family",
        "responsibilities",
        "ownership_scope",
        "production_operating",
        "product_stage",
        "domain_problems",
        "technical_environment",
    }
    _exact_keys(item, names, field)
    return RoleEvidence(
        primary_role_family=_text(item["primary_role_family"], f"{field}.primary_role_family"),
        responsibilities=_strings(item["responsibilities"], f"{field}.responsibilities"),
        ownership_scope=_strings(item["ownership_scope"], f"{field}.ownership_scope"),
        production_operating=_strings(
            item["production_operating"], f"{field}.production_operating"
        ),
        product_stage=_strings(item["product_stage"], f"{field}.product_stage"),
        domain_problems=_strings(item["domain_problems"], f"{field}.domain_problems"),
        technical_environment=_strings(
            item["technical_environment"], f"{field}.technical_environment"
        ),
    )


def _mapping(value: object, field: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping) or any(not isinstance(key, str) for key in value):
        raise SafeInputError(field)
    return value


def _list(value: object, field: str) -> list[object]:
    if not isinstance(value, list):
        raise SafeInputError(field)
    return value


def _exact_keys(value: Mapping[str, object], expected: set[str], field: str) -> None:
    unknown = sorted(set(value) - expected)
    missing = sorted(expected - set(value))
    if unknown:
        raise SafeInputError(f"{field}.{unknown[0]}")
    if missing:
        raise SafeInputError(f"{field}.{missing[0]}")


def _text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SafeInputError(field)
    return value


def _strings(value: object, field: str, *, allow_empty: bool = False) -> tuple[str, ...]:
    values = _list(value, field)
    if (not values and not allow_empty) or any(
        not isinstance(item, str) or not item.strip() for item in values
    ):
        raise SafeInputError(field)
    return tuple(item for item in values if isinstance(item, str))


def _number(value: object, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise SafeInputError(field)
    return float(value)


def _boolean(value: object, field: str) -> bool:
    if not isinstance(value, bool):
        raise SafeInputError(field)
    return value


def _optional_nonnegative_int(value: object, field: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise SafeInputError(field)
    return value


def _date(value: object, field: str) -> date:
    try:
        return date.fromisoformat(_text(value, field))
    except ValueError as error:
        raise SafeInputError(field) from error


def _datetime(value: object, field: str) -> datetime:
    try:
        return datetime.fromisoformat(_text(value, field))
    except ValueError as error:
        raise SafeInputError(field) from error


def _write_atomic(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            delete=False,
        ) as stream:
            temporary = Path(stream.name)
            os.chmod(temporary, 0o600)
            json.dump(payload, stream, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def _fail(code: str, judge: CountingJudge | None, *, field: str | None = None) -> Never:
    """A failure after a request (e.g. the output write) still reports that data may have left."""
    payload: dict[str, object] = {"ok": False, "error_code": code, **delivery(judge)}
    if field is not None:
        payload["field"] = field
    print(json.dumps(payload, sort_keys=True), file=sys.stderr)
    raise SystemExit(2)


if __name__ == "__main__":
    raise SystemExit(main())
