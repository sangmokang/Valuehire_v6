"""Evidence-backed grouping for per-candidate AI Search Gmail alerts."""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import replace
from typing import Literal
from zoneinfo import ZoneInfo

from .evidence import AiSearchRun

_KST = ZoneInfo("Asia/Seoul")
_RUN_ID = re.compile(
    r"(?:실행\s*(?:ID|아이디)|run\s*id)\s*[:：#]\s*([A-Za-z0-9][A-Za-z0-9._:-]{2,127})",
    re.IGNORECASE,
)


def grouping_evidence(run: AiSearchRun, subject: str, body_text: str) -> tuple[str | None, str]:
    """Return a grouping key only when a per-candidate alert has run evidence."""

    if not _is_candidate_alert(run):
        return None, "not_candidate_alert"
    run_id = _explicit_run_id(subject, body_text)
    if run_id is not None:
        return f"run:{run.actor}:{run_id}", "explicit_run_id"
    if run.company.startswith("NOT_RUN:") or run.position.startswith("NOT_RUN:"):
        return None, "missing_batch_group_evidence"
    received_date = run.executed_at.astimezone(_KST).date().isoformat()
    key = f"daily\x1f{run.actor}\x1f{run.company}\x1f{run.position}\x1f{received_date}"
    return key, "same_actor_company_position_date"


def group_gmail_runs(runs: Sequence[AiSearchRun]) -> tuple[AiSearchRun, ...]:
    """Merge only runs sharing an evidence-backed key; preserve ungrouped reasons."""

    keyed: dict[str, list[AiSearchRun]] = {}
    ungrouped: list[AiSearchRun] = []
    for run in runs:
        if run.batch_group_key is None:
            ungrouped.append(run)
        else:
            keyed.setdefault(run.batch_group_key, []).append(run)
    for group in keyed.values():
        if len(group) == 1:
            ungrouped.append(
                replace(group[0], batch_grouping_reason="no_matching_message_for_group_key")
            )
        else:
            ungrouped.append(_merge_group(group))
    return tuple(ungrouped)


def _explicit_run_id(subject: str, body_text: str) -> str | None:
    match = _RUN_ID.search(f"{subject}\n{body_text}")
    return match.group(1) if match is not None else None


def _is_candidate_alert(run: AiSearchRun) -> bool:
    return (
        run.candidate_counts_complete
        and len(run.candidates) == 1
        and run.unparsed_candidates == 0
        and run.excluded_candidates == 0
    )


def _merge_group(group: Sequence[AiSearchRun]) -> AiSearchRun:
    ordered = sorted(group, key=lambda run: (run.executed_at, run.source_run_id))
    first = ordered[0]
    period_start, period_end, period_reason = _merged_period(ordered)
    return AiSearchRun(
        actor=first.actor,
        source_run_id=first.batch_group_key or first.source_run_id,
        company=_merged_context(ordered, "company"),
        position=_merged_context(ordered, "position"),
        channels=tuple(sorted({channel for run in ordered for channel in run.channels})),
        executed_at=first.executed_at,
        candidates=tuple(candidate for run in ordered for candidate in run.candidates),
        contacts=tuple(contact for run in ordered for contact in run.contacts),
        verification_checks=first.verification_checks,
        actor_evidence=first.actor_evidence,
        search_period_start=period_start,
        search_period_end=period_end,
        search_period_reason=period_reason,
        unparsed_candidates=sum(run.unparsed_candidates for run in ordered),
        excluded_candidates=sum(run.excluded_candidates for run in ordered),
        candidate_counts_complete=all(run.candidate_counts_complete for run in ordered),
        candidate_counts_reason=_count_reason(ordered),
        source_message_ids=tuple(
            sorted({message_id for run in ordered for message_id in run.source_message_ids})
        ),
        batch_grouping_reason=first.batch_grouping_reason,
    )


def _merged_context(runs: Sequence[AiSearchRun], field: Literal["company", "position"]) -> str:
    raw_values = [run.company if field == "company" else run.position for run in runs]
    values = {value for value in raw_values if not value.startswith("NOT_RUN:")}
    if len(values) == 1:
        return values.pop()
    if not values:
        return f"NOT_RUN:{field}_not_parsed"
    return f"NOT_RUN:{field}_conflict"


def _merged_period(runs: Sequence[AiSearchRun]) -> tuple[str | None, str | None, str | None]:
    periods = {
        (run.search_period_start, run.search_period_end)
        for run in runs
        if run.search_period_start is not None
    }
    if len(periods) == 1:
        start, end = periods.pop()
        return start, end, None
    if len(periods) > 1:
        return None, None, "search_period_conflict"
    return None, None, "search_period_not_found"


def _count_reason(runs: Sequence[AiSearchRun]) -> str | None:
    if all(run.candidate_counts_complete for run in runs):
        return None
    return next(
        run.candidate_counts_reason for run in runs if run.candidate_counts_reason is not None
    )
