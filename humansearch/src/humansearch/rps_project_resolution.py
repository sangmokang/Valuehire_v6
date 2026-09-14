"""Plan-only RPS project resolution boundary."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Literal


class RpsProjectStatus(str, Enum):
    """Closed states for plan-only RPS project resolution."""

    INVALID_INPUT = "INVALID_INPUT"
    QUERY_FAILED = "QUERY_FAILED"
    RECONCILE_REQUIRED = "RECONCILE_REQUIRED"
    MAPPING_CONFLICT = "MAPPING_CONFLICT"
    AMBIGUOUS = "AMBIGUOUS"
    CREATE_REQUIRED = "CREATE_REQUIRED"
    REUSE = "REUSE"


@dataclass(frozen=True, slots=True)
class RpsProjectResolution:
    """Plan-only result; never grants write permission."""

    status: RpsProjectStatus
    position_id: str | None
    project_id: str | None
    reason: str
    plan_only: bool = True
    allows_write: bool = False


@dataclass(frozen=True, slots=True)
class _Target:
    position_id: str
    customer_id: str
    customer_name: str
    position_title: str
    account_scope: str


@dataclass(frozen=True, slots=True)
class _Observation:
    observation_id: str
    account_scope: str
    query_scope: str
    observed_at: datetime
    query_error: str | None
    all_pages_loaded: bool
    stale: bool
    projects: Sequence[_Project]


@dataclass(frozen=True, slots=True)
class _ObservationLimit:
    reference_time: datetime
    max_age_seconds: int


@dataclass(frozen=True, slots=True)
class _Project:
    project_id: str
    customer_id: str | None
    position_id: str | None
    customer_name: str | None
    position_title: str | None
    name: str | None


@dataclass(frozen=True, slots=True)
class _ProjectLink:
    account_scope: str
    project_id: str
    position_id: str


@dataclass(frozen=True, slots=True)
class _ResolutionInput:
    target: _Target
    observation: _Observation
    project_links: Sequence[_ProjectLink]
    mapped_project_id: str | None
    pending_creation_intent: bool


def resolve_rps_project(payload: object) -> RpsProjectResolution:
    """Resolve a project from a completed observation without external writes."""

    if not isinstance(payload, dict):
        return _result(RpsProjectStatus.INVALID_INPUT, None, None, "payload must be an object")
    parsed = _resolution_input(payload)
    if isinstance(parsed, RpsProjectResolution):
        return parsed
    return _resolve_observed_projects(parsed)


def _resolution_input(payload: Mapping[str, object]) -> _ResolutionInput | RpsProjectResolution:
    target = _target(payload)
    position_id = target.position_id if target is not None else _optional_text(payload, "position_id")
    if target is None:
        return _result(
            RpsProjectStatus.INVALID_INPUT,
            position_id,
            None,
            "target identity fields must be non-empty strings",
        )
    observation = _observation(payload.get("observation"))
    if observation is None or observation.account_scope != target.account_scope:
        return _result(
            RpsProjectStatus.QUERY_FAILED,
            target.position_id,
            None,
            "observation identity, scope, account, time, and projects must be complete",
        )
    observation_limit = _observation_limit(payload.get("observation_limit"))
    if observation_limit is None or not _within_observation_limit(observation, observation_limit):
        return _result(
            RpsProjectStatus.QUERY_FAILED,
            target.position_id,
            None,
            "observation was outside the permitted time window",
        )
    project_links = _project_links(payload.get("project_links"))
    if project_links is None:
        return _result(
            RpsProjectStatus.INVALID_INPUT,
            target.position_id,
            None,
            "project_links must be a list of project link objects",
        )
    mapped_project_id = _mapped_project_id(payload.get("mapped_project_id"))
    if mapped_project_id is False:
        return _result(
            RpsProjectStatus.INVALID_INPUT,
            target.position_id,
            None,
            "mapped_project_id must be null or a non-empty string",
        )
    expected_scope = (
        "account-projects" if mapped_project_id is None else f"project-by-id:{mapped_project_id}"
    )
    if observation.query_scope != expected_scope:
        return _result(
            RpsProjectStatus.QUERY_FAILED, target.position_id, None,
            "observation query scope did not match the required target lookup",
        )
    pending_creation_intent = payload.get("pending_creation_intent")
    if type(pending_creation_intent) is not bool:
        return _result(
            RpsProjectStatus.INVALID_INPUT,
            target.position_id,
            None,
            "pending_creation_intent must be a bool",
        )
    return _ResolutionInput(
        target=target,
        observation=observation,
        project_links=tuple(project_links),
        mapped_project_id=mapped_project_id,
        pending_creation_intent=pending_creation_intent,
    )


def _resolve_observed_projects(context: _ResolutionInput) -> RpsProjectResolution:
    target = context.target
    projects = context.observation.projects
    if _query_failed(context.observation) or _has_conflicting_duplicate_ids(projects):
        return _result(
            RpsProjectStatus.QUERY_FAILED,
            target.position_id,
            None,
            "project observation is incomplete, stale, errored, or internally conflicting",
        )
    if context.pending_creation_intent:
        return _result(
            RpsProjectStatus.RECONCILE_REQUIRED,
            target.position_id,
            None,
            "existing creation intent must be reconciled before another create decision",
        )
    if _target_link_exists(target, context.project_links) and context.mapped_project_id is None:
        return _result(
            RpsProjectStatus.MAPPING_CONFLICT,
            target.position_id,
            None,
            "project link for the target exists but no mapped project id was supplied",
        )
    if context.mapped_project_id is not None:
        return _resolve_mapped_project(context, projects)
    return _resolve_unmapped_projects(context, projects)


def _resolve_mapped_project(
    context: _ResolutionInput, projects: Sequence[_Project]
) -> RpsProjectResolution:
    target = context.target
    mapped_project_id = context.mapped_project_id
    if mapped_project_id is None:
        return _result(
            RpsProjectStatus.INVALID_INPUT,
            target.position_id,
            None,
            "mapped project id was required for mapped resolution",
        )
    by_id = {project.project_id: project for project in projects}
    mapped = by_id.get(mapped_project_id)
    if mapped is None or not _has_target_id_evidence(mapped, target):
        return _result(
            RpsProjectStatus.MAPPING_CONFLICT,
            target.position_id,
            None,
            "mapped project id was absent or did not match the target evidence",
        )
    if _link_conflict(mapped.project_id, target, context.project_links) or _target_link_conflict(
        mapped.project_id, target, context.project_links
    ):
        return _mapping_conflict(target.position_id)
    return _result(
        RpsProjectStatus.REUSE,
        target.position_id,
        mapped.project_id,
        "mapped project id matched the target evidence",
    )


def _resolve_unmapped_projects(
    context: _ResolutionInput, projects: Sequence[_Project]
) -> RpsProjectResolution:
    target = context.target
    matching_ids = {
        project.project_id for project in projects if _has_target_id_evidence(project, target)
    }
    has_name_only_match = any(_has_name_only_evidence(project, target) for project in projects)
    has_partial_target_id_evidence = any(
        _has_partial_target_id_evidence(project, target) for project in projects
    )
    has_unknown_identity_evidence = any(_lacks_identity_evidence(project) for project in projects)
    if matching_ids and (
        has_name_only_match or has_partial_target_id_evidence or has_unknown_identity_evidence
    ):
        return _result(
            RpsProjectStatus.AMBIGUOUS,
            target.position_id,
            None,
            "stable target evidence was mixed with unresolved project evidence",
        )
    if len(matching_ids) == 1:
        project_id = next(iter(matching_ids))
        if _link_conflict(project_id, target, context.project_links) or _target_link_conflict(
            project_id, target, context.project_links
        ):
            return _mapping_conflict(target.position_id)
        return _result(
            RpsProjectStatus.REUSE,
            target.position_id,
            project_id,
            "exactly one project matched customer and position id evidence",
        )
    if len(matching_ids) > 1:
        return _result(
            RpsProjectStatus.AMBIGUOUS,
            target.position_id,
            None,
            "multiple projects matched customer and position id evidence",
        )
    if has_name_only_match:
        return _result(
            RpsProjectStatus.AMBIGUOUS,
            target.position_id,
            None,
            "visible names matched without stable customer and position id evidence",
        )
    if has_partial_target_id_evidence:
        return _result(
            RpsProjectStatus.AMBIGUOUS,
            target.position_id,
            None,
            "partial stable target identity was observed without enough evidence to exclude it",
        )
    if has_unknown_identity_evidence:
        return _result(
            RpsProjectStatus.AMBIGUOUS,
            target.position_id,
            None,
            "at least one observed project lacked customer, position, and visible name evidence",
        )
    return RpsProjectResolution(
        status=RpsProjectStatus.CREATE_REQUIRED,
        position_id=target.position_id,
        project_id=None,
        reason="complete fresh observation found no project for the target",
    )


def _mapping_conflict(position_id: str) -> RpsProjectResolution:
    return _result(
        RpsProjectStatus.MAPPING_CONFLICT,
        position_id,
        None,
        "selected project was already linked to another position",
    )


def _result(
    status: RpsProjectStatus, position_id: str | None, project_id: str | None, reason: str
) -> RpsProjectResolution:
    return RpsProjectResolution(
        status=status,
        position_id=position_id,
        project_id=project_id,
        reason=reason,
    )


def _target(payload: Mapping[str, object]) -> _Target | None:
    position_id = _required_text(payload, "position_id")
    customer_id = _required_text(payload, "customer_id")
    customer_name = _required_text(payload, "customer_name")
    position_title = _required_text(payload, "position_title")
    account_scope = _required_text(payload, "account_scope")
    if position_id is None:
        return None
    if customer_id is None:
        return None
    if customer_name is None:
        return None
    if position_title is None:
        return None
    if account_scope is None:
        return None
    return _Target(
        position_id=position_id,
        customer_id=customer_id,
        customer_name=customer_name,
        position_title=position_title,
        account_scope=account_scope,
    )


def _observation(raw: object) -> _Observation | None:
    if not isinstance(raw, dict):
        return None
    observation_id = _required_text(raw, "observation_id")
    account_scope = _required_text(raw, "account_scope")
    query_scope = _required_text(raw, "query_scope")
    observed_at = _datetime(raw.get("observed_at"))
    projects = _projects(raw.get("projects"))
    if (
        observation_id is None
        or account_scope is None
        or query_scope is None
        or observed_at is None
        or projects is None
    ):
        return None
    query_error_raw = raw.get("query_error")
    query_error: str | None
    if query_error_raw is None:
        query_error = None
    elif isinstance(query_error_raw, str):
        query_error = query_error_raw
    else:
        return None
    all_pages_loaded = raw.get("all_pages_loaded")
    stale = raw.get("stale")
    if type(all_pages_loaded) is not bool or type(stale) is not bool:
        return None
    return _Observation(
        observation_id=observation_id,
        account_scope=account_scope,
        query_scope=query_scope,
        observed_at=observed_at,
        query_error=query_error,
        all_pages_loaded=all_pages_loaded,
        stale=stale,
        projects=tuple(projects),
    )


def _projects(raw: object) -> list[_Project] | None:
    if not isinstance(raw, list):
        return None
    projects: list[_Project] = []
    for item in raw:
        if not isinstance(item, dict):
            return None
        project_id = _required_text(item, "project_id")
        if project_id is None:
            return None
        customer_id = _optional_project_text(item, "customer_id")
        if customer_id is False:
            return None
        position_id = _optional_project_text(item, "position_id")
        if position_id is False:
            return None
        customer_name = _optional_project_text(item, "customer_name")
        if customer_name is False:
            return None
        position_title = _optional_project_text(item, "position_title")
        if position_title is False:
            return None
        name = _optional_project_text(item, "name")
        if name is False:
            return None
        projects.append(
            _Project(
                project_id=project_id,
                customer_id=customer_id,
                position_id=position_id,
                customer_name=customer_name,
                position_title=position_title,
                name=name,
            )
        )
    return projects


def _mapped_project_id(raw: object) -> str | None | Literal[False]:
    if raw is None:
        return None
    if isinstance(raw, str) and raw.strip():
        return raw.strip()
    return False


def _observation_limit(raw: object) -> _ObservationLimit | None:
    if not isinstance(raw, dict):
        return None
    reference_time = _datetime(raw.get("reference_time"))
    max_age_seconds = raw.get("max_age_seconds")
    if reference_time is None:
        return None
    if type(max_age_seconds) is not int or max_age_seconds <= 0:
        return None
    return _ObservationLimit(
        reference_time=reference_time,
        max_age_seconds=max_age_seconds,
    )


def _within_observation_limit(
    observation: _Observation, observation_limit: _ObservationLimit
) -> bool:
    age_seconds = (observation_limit.reference_time - observation.observed_at).total_seconds()
    return 0 <= age_seconds <= observation_limit.max_age_seconds


def _project_links(raw: object) -> list[_ProjectLink] | None:
    if not isinstance(raw, list):
        return None
    links: list[_ProjectLink] = []
    for item in raw:
        if not isinstance(item, dict):
            return None
        account_scope = _required_text(item, "account_scope")
        project_id = _required_text(item, "project_id")
        position_id = _required_text(item, "position_id")
        if account_scope is None or project_id is None or position_id is None:
            return None
        links.append(
            _ProjectLink(
                account_scope=account_scope,
                project_id=project_id,
                position_id=position_id,
            )
        )
    return links


def _query_failed(observation: _Observation) -> bool:
    return (
        (observation.query_error is not None and bool(observation.query_error.strip()))
        or not observation.all_pages_loaded
        or observation.stale
    )


def _has_conflicting_duplicate_ids(projects: Sequence[_Project]) -> bool:
    seen: dict[str, tuple[str | None, str | None, str | None, str | None]] = {}
    for project in projects:
        signature = (
            project.customer_id,
            project.position_id,
            project.customer_name,
            project.position_title,
        )
        existing = seen.get(project.project_id)
        if existing is not None and existing != signature:
            return True
        seen[project.project_id] = signature
    return False


def _has_target_id_evidence(project: _Project, target: _Target) -> bool:
    return project.customer_id == target.customer_id and project.position_id == target.position_id


def _link_conflict(
    project_id: str, target: _Target, project_links: Sequence[_ProjectLink]
) -> bool:
    return any(
        link.account_scope == target.account_scope
        and link.project_id == project_id
        and link.position_id != target.position_id
        for link in project_links
    )


def _target_link_exists(target: _Target, project_links: Sequence[_ProjectLink]) -> bool:
    return any(
        link.account_scope == target.account_scope and link.position_id == target.position_id
        for link in project_links
    )


def _target_link_conflict(
    project_id: str, target: _Target, project_links: Sequence[_ProjectLink]
) -> bool:
    return any(
        link.account_scope == target.account_scope
        and link.position_id == target.position_id
        and link.project_id != project_id
        for link in project_links
    )


def _has_name_only_evidence(project: _Project, target: _Target) -> bool:
    visible_customer = project.customer_name == target.customer_name
    visible_position = project.position_title == target.position_title
    visible_name = project.name == f"{target.customer_name} {target.position_title}"
    lacks_stable_evidence = project.customer_id is None or project.position_id is None
    return lacks_stable_evidence and (visible_customer or visible_position or visible_name)


def _has_partial_target_id_evidence(project: _Project, target: _Target) -> bool:
    customer_matches_without_position = (
        project.customer_id == target.customer_id and project.position_id is None
    )
    position_matches_without_customer = (
        project.position_id == target.position_id and project.customer_id is None
    )
    return customer_matches_without_position or position_matches_without_customer


def _lacks_identity_evidence(project: _Project) -> bool:
    return (
        project.customer_id is None
        and project.position_id is None
        and project.customer_name is None
        and project.position_title is None
        and project.name is None
    )


def _required_text(mapping: Mapping[str, object], key: str) -> str | None:
    value = mapping.get(key)
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _optional_text(mapping: Mapping[str, object], key: str) -> str | None:
    value: Any = mapping.get(key)
    if value is None:
        return None
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _optional_project_text(mapping: Mapping[str, object], key: str) -> str | None | Literal[False]:
    if key not in mapping or mapping[key] is None:
        return None
    value: Any = mapping[key]
    if isinstance(value, str):
        return value.strip() or None
    return False


def _datetime(raw: object) -> datetime | None:
    if not isinstance(raw, str) or not raw.strip():
        return None
    normalized = raw.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed
