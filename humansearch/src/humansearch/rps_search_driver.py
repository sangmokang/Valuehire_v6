"""Verified filter application for one existing Recruiter search target."""

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, TypeGuard

from .rps_search_contract import (
    RpsSurface,
    RpsTarget,
    SearchPlan,
    SearchStatus,
    TargetSelectionError,
    preflight_status,
    select_rps_target,
)

_CONTRACT_PATH = (
    Path(__file__).resolve().parents[3]
    / "contracts"
    / "humansearch"
    / "rps-search-v1.json"
)
_FILTER_FIELDS = ("keywords", "job_titles", "network", "seniority", "locations")
_READBACK_ATTEMPTS = 3


class RpsDriftError(RuntimeError):
    """Raised when a contracted browser marker or control cannot be found."""


class RpsTransportError(RuntimeError):
    """Raised when the fixed browser channel fails without exposing page data."""


@dataclass(frozen=True, slots=True)
class FilterContract:
    """Semantic labels for one Recruiter filter control."""

    labels: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RpsUiContract:
    """Validated selector and label data used by the fixed browser adapter."""

    allowed_origin: str
    fields: Mapping[str, FilterContract]
    submit_labels: tuple[str, ...]
    authenticated_selectors: tuple[str, ...]
    human_auth_selectors: tuple[str, ...]
    challenge_selectors: tuple[str, ...]
    session_conflict_text: tuple[str, ...]
    result_count_selectors: tuple[str, ...]
    loading_selectors: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class FilterExecution:
    """Privacy-reduced outcome before result observation."""

    status: SearchStatus | None
    filters_verified: bool
    submitted: bool


class RpsFilterPort(Protocol):
    """The only browser effects the verified filter workflow may request."""

    def list_targets(self) -> list[object]: ...

    def attach(self, selected: RpsTarget) -> None: ...

    def observe_surface(self) -> RpsSurface: ...

    def prepare_search(self) -> None: ...

    def input_filter(self, field_name: str, value: str, delay_ms: int) -> None: ...

    def read_filter(
        self, field_name: str, expected: tuple[str, ...], attempt: int
    ) -> tuple[str, ...]: ...

    def submit_search(self) -> None: ...


def run_verified_filters(plan: SearchPlan, port: RpsFilterPort) -> FilterExecution:
    """Apply filters in canonical order and submit only after two readback gates."""

    contract = load_rps_ui_contract()
    try:
        selected = select_rps_target(port.list_targets(), contract.allowed_origin)
        port.attach(selected)
        blocked = preflight_status(plan, selected, port.observe_surface())
        if blocked is not None:
            return FilterExecution(blocked, False, False)
        port.prepare_search()

        filter_items = _execution_filter_items(plan)
        for field_name, values in filter_items:
            for value in values:
                port.input_filter(
                    field_name,
                    value,
                    deterministic_delay_ms(plan.position_ref, field_name, value),
                )
            if not _verified(port, field_name, values):
                return FilterExecution(SearchStatus.FILTER_MISMATCH, False, False)

        for field_name, values in filter_items:
            if not _verified(port, field_name, values):
                return FilterExecution(SearchStatus.FILTER_MISMATCH, False, False)

        port.submit_search()
        return FilterExecution(None, True, True)
    except TargetSelectionError as exc:
        return FilterExecution(exc.status, False, False)
    except RpsDriftError:
        return FilterExecution(SearchStatus.DRIFTED, False, False)
    except RpsTransportError:
        return FilterExecution(SearchStatus.FAILED, False, False)


def deterministic_delay_ms(position_ref: str, field_name: str, value: str) -> int:
    """Return stable human-scale jitter without global randomness or fixed spacing."""

    material = f"{position_ref}\0{field_name}\0{value}".encode()
    digest = hashlib.sha256(material).digest()
    return 800 + int.from_bytes(digest[:2], "big") % 801


def _execution_filter_items(
    plan: SearchPlan,
) -> tuple[tuple[str, tuple[str, ...]], ...]:
    items = []
    for field_name, values in plan.filter_items():
        if field_name == "keywords":
            values = (" AND ".join(values),)
        items.append((field_name, values))
    return tuple(items)


def load_rps_ui_contract() -> RpsUiContract:
    """Load the small data contract; malformed selector data fails closed."""

    try:
        raw = json.loads(_CONTRACT_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError, RecursionError) as exc:
        raise RpsDriftError("RPS UI contract is unavailable") from exc
    if not isinstance(raw, dict) or raw.get("version") != 1:
        raise RpsDriftError("RPS UI contract version is invalid")
    allowed_origin = raw.get("allowed_origin")
    raw_fields = raw.get("fields")
    if allowed_origin != "https://www.linkedin.com" or not isinstance(raw_fields, dict):
        raise RpsDriftError("RPS UI contract target is invalid")
    if tuple(raw_fields) != _FILTER_FIELDS:
        raise RpsDriftError("RPS UI field contract is incomplete")
    fields: dict[str, FilterContract] = {}
    for field_name in _FILTER_FIELDS:
        field = raw_fields.get(field_name)
        if not isinstance(field, dict) or not _string_list(field.get("labels")):
            raise RpsDriftError("RPS UI field labels are invalid")
        fields[field_name] = FilterContract(labels=tuple(field["labels"]))
    return RpsUiContract(
        allowed_origin=allowed_origin,
        fields=fields,
        submit_labels=_required_strings(raw, "submit_labels"),
        authenticated_selectors=_required_strings(raw, "authenticated_selectors"),
        human_auth_selectors=_required_strings(raw, "human_auth_selectors"),
        challenge_selectors=_required_strings(raw, "challenge_selectors"),
        session_conflict_text=_required_strings(raw, "session_conflict_text"),
        result_count_selectors=_required_strings(raw, "result_count_selectors"),
        loading_selectors=_required_strings(raw, "loading_selectors"),
    )


def _verified(
    port: RpsFilterPort, field_name: str, expected: tuple[str, ...]
) -> bool:
    for attempt in range(_READBACK_ATTEMPTS):
        if port.read_filter(field_name, expected, attempt) == expected:
            return True
    return False


def _required_strings(raw: Mapping[str, object], name: str) -> tuple[str, ...]:
    value = raw.get(name)
    if not _string_list(value):
        raise RpsDriftError(f"RPS UI {name} is invalid")
    return tuple(value)


def _string_list(value: object) -> TypeGuard[list[str]]:
    return isinstance(value, list) and bool(value) and all(
        type(item) is str and bool(item) for item in value
    )
