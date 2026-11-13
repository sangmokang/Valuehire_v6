"""Pure contracts for one existing LinkedIn Recruiter search tab."""

from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from typing import TypeGuard
from urllib.parse import urlsplit

from .auth_surface import AuthSurfaceState

_PLAN_FIELDS = frozenset(
    {
        "position_ref",
        "project_ref",
        "keywords",
        "job_titles",
        "network",
        "seniority",
        "locations",
    }
)
_FILTER_FIELDS = ("keywords", "job_titles", "network", "seniority", "locations")
_RPS_PREFIX = "/talent/hire/"
_RPS_SUFFIX = "/discover/recruiterSearch"


class SearchStatus(str, Enum):
    """Small public result vocabulary for the vertical slice."""

    COMPLETED = "completed"
    BLOCKED_SESSION_CONFLICT = "blocked_session_conflict"
    MANUAL_ACTION_REQUIRED = "manual_action_required"
    FILTER_MISMATCH = "filter_mismatch"
    TARGET_NOT_FOUND = "target_not_found"
    TARGET_AMBIGUOUS = "target_ambiguous"
    DRIFTED = "drifted"
    FAILED = "failed"


class PlanValidationError(ValueError):
    """Raised before browser access when a plan is incomplete or overpowered."""


class TargetSelectionError(RuntimeError):
    """Raised unless exactly one approved existing RPS page can be attached."""

    def __init__(self, status: SearchStatus) -> None:
        super().__init__(status.value)
        self.status = status


@dataclass(frozen=True, slots=True)
class SearchPlan:
    """Canonical filter input. It deliberately contains no URL or CDP command."""

    position_ref: str
    project_ref: str
    keywords: tuple[str, ...]
    job_titles: tuple[str, ...]
    network: tuple[str, ...]
    seniority: tuple[str, ...]
    locations: tuple[str, ...]

    @classmethod
    def from_mapping(cls, payload: Mapping[str, object]) -> SearchPlan:
        if not isinstance(payload, Mapping) or set(payload) != _PLAN_FIELDS:
            raise PlanValidationError("plan fields are invalid")
        position_ref = _text(payload["position_ref"], "position_ref")
        project_ref = _text(payload["project_ref"], "project_ref")
        filters = {
            name: _text_list(payload[name], name)
            for name in _FILTER_FIELDS
        }
        return cls(
            position_ref=position_ref,
            project_ref=project_ref,
            keywords=filters["keywords"],
            job_titles=filters["job_titles"],
            network=filters["network"],
            seniority=filters["seniority"],
            locations=filters["locations"],
        )

    def filter_items(self) -> tuple[tuple[str, tuple[str, ...]], ...]:
        return tuple((name, getattr(self, name)) for name in _FILTER_FIELDS)


@dataclass(frozen=True, slots=True)
class RpsTarget:
    """An already-open target selected without title/order heuristics."""

    url: str
    project_ref: str
    target_id: str


@dataclass(frozen=True, slots=True)
class RpsSurface:
    """Privacy-reduced readback from the selected RPS page."""

    auth_state: AuthSurfaceState
    contract_valid: bool
    session_conflict: bool
    project_ref: str | None


def select_rps_target(targets: list[object], allowed_origin: str) -> RpsTarget:
    """Return exactly one approved existing RPS page or a closed failure."""

    if not _valid_origin(allowed_origin):
        raise TargetSelectionError(SearchStatus.DRIFTED)
    matches: list[RpsTarget] = []
    for item in targets:
        target = _candidate_target(item, allowed_origin)
        if target is not None:
            matches.append(target)
    if not matches:
        raise TargetSelectionError(SearchStatus.TARGET_NOT_FOUND)
    if len(matches) > 1:
        raise TargetSelectionError(SearchStatus.TARGET_AMBIGUOUS)
    return matches[0]


def preflight_status(
    plan: SearchPlan, target: RpsTarget, surface: RpsSurface
) -> SearchStatus | None:
    """Return ``None`` only when the browser may receive filter input."""

    if surface.session_conflict:
        return SearchStatus.BLOCKED_SESSION_CONFLICT
    if not surface.contract_valid or surface.auth_state is AuthSurfaceState.DRIFTED:
        return SearchStatus.DRIFTED
    if surface.auth_state is not AuthSurfaceState.AUTHENTICATED:
        return SearchStatus.MANUAL_ACTION_REQUIRED
    if target.project_ref != plan.project_ref or surface.project_ref != plan.project_ref:
        return SearchStatus.FAILED
    return None


def _candidate_target(item: object, allowed_origin: str) -> RpsTarget | None:
    if not isinstance(item, Mapping) or item.get("type") != "page":
        return None
    url = item.get("url")
    if not isinstance(url, str):
        return None
    project_ref = _project_ref(url, allowed_origin)
    if project_ref is None:
        return None
    target_id = item.get("targetId")
    if not _nonempty_string(target_id):
        return None
    return RpsTarget(
        url=url,
        project_ref=project_ref,
        target_id=target_id,
    )


def _project_ref(url: str, allowed_origin: str) -> str | None:
    try:
        parsed = urlsplit(url)
    except ValueError:
        return None
    origin = f"{parsed.scheme}://{parsed.netloc}"
    if origin != allowed_origin or parsed.username is not None or parsed.password is not None:
        return None
    path = parsed.path.rstrip("/")
    matched_suffix = next(
        (
            suffix
            for suffix in (f"{_RPS_SUFFIX}/advanced", _RPS_SUFFIX)
            if path.endswith(suffix)
        ),
        None,
    )
    if not path.startswith(_RPS_PREFIX) or matched_suffix is None:
        return None
    project_ref = path[len(_RPS_PREFIX) : -len(matched_suffix)]
    if not project_ref or "/" in project_ref:
        return None
    return project_ref


def _valid_origin(value: str) -> bool:
    try:
        parsed = urlsplit(value)
        _ = parsed.port
    except ValueError:
        return False
    return (
        value.isascii()
        and parsed.scheme == "https"
        and bool(parsed.hostname)
        and not parsed.path
        and not parsed.query
        and not parsed.fragment
        and parsed.username is None
        and parsed.password is None
    )


def _text(value: object, name: str) -> str:
    if type(value) is not str or not value.strip():
        raise PlanValidationError(f"{name} must be a non-empty string")
    return value.strip()


def _text_list(value: object, name: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not value:
        raise PlanValidationError(f"{name} must be a non-empty list")
    values = tuple(_text(item, name) for item in value)
    if len(set(values)) != len(values):
        raise PlanValidationError(f"{name} contains duplicate values")
    return values


def _nonempty_string(value: object) -> TypeGuard[str]:
    return type(value) is str and bool(value)
