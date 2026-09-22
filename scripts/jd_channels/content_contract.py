"""Cross-channel content-quality and placement evidence contracts."""
from __future__ import annotations

import re
from collections.abc import Callable
from typing import Any

from .units import JDSource, Unit


def company_intro_errors(src: JDSource) -> list[str]:
    """Reject label-only intros separately from source-unit coverage."""
    company = src.by_section("company")
    if not company:
        return ["COMPANY_INTRO_MISSING"]
    text = " ".join(unit.full.strip() for unit in company)
    factual = re.sub(r"^[\s\-•·]+|[\s|:/·\-]+", "", text)
    errors: list[str] = []
    if len(factual) < 55:
        errors.append("COMPANY_INTRO_TOO_THIN")
    if not any(src.by_section(section) for section in ("team", "role", "growth")):
        errors.append("COMPANY_INTRO_ROLE_LINK_MISSING")
    return errors


def placement_audit(
    src: JDSource,
    proposal: list[Unit],
    persistent: dict[str, list[Unit]],
    limits: dict[str, int],
    render: Callable[[list[Unit]], str],
    order: Callable[[list[Unit]], list[Unit]],
) -> tuple[list[dict[str, Any]], list[str]]:
    """Show whether every transient unit could still fit in a persistent field."""
    rows: list[dict[str, Any]] = []
    unused: list[str] = []
    for unit in proposal:
        required: dict[str, int] = {}
        remaining: dict[str, int] = {}
        fit: dict[str, bool] = {}
        for field, units in persistent.items():
            current = len(render(units))
            candidate = len(render(order(units + [unit])))
            required[field] = candidate - current
            remaining[field] = limits[field] - current
            fit[field] = candidate <= limits[field]
        reserved = unit.section == "company"
        movable = any(fit.values()) and not reserved
        if movable:
            unused.append(unit.id)
        reason = (
            "company_intro_reserved_for_candidate_proposal"
            if reserved else
            "persistent_space_unused"
            if movable else
            "no_persistent_field_can_fit_whole_unit"
        )
        rows.append({
            "unit_id": unit.id,
            "section": unit.section,
            "required_chars": required,
            "remaining_chars": remaining,
            "movable": movable,
            "final_reason": reason,
        })
    return rows, unused
