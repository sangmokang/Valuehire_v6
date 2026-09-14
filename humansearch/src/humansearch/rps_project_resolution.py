"""Plan-only RPS project resolution boundary."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
from typing import Any


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
    account_scope: str
    query_error: str | None
    all_pages_loaded: bool
    stale: bool


@dataclass(frozen=True, slots=True)
class _Project:
    project_id: str
    customer_id: str | None
    position_id: str | None
    customer_name: str | None
    position_title: str | None
    name: str | None


def resolve_rps_project(payload: object) -> RpsProjectResolution:
    """Resolve a project from a completed observation without external writes."""

    if not isinstance(payload, dict):
        return _result(RpsProjectStatus.INVALID_INPUT, None, None, "payload must be an object")
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
            RpsProjectStatus.INVALID_INPUT,
            target.position_id,
            None,
            "observation must match the target account scope",
        )
    projects = _projects(payload.get("projects"))
    if projects is None:
        return _result(
            RpsProjectStatus.INVALID_INPUT,
            target.position_id,
            None,
            "projects must be a list of project objects",
        )
    mapped_project_id = _mapped_project_id(payload.get("mapped_project_id"))
    if mapped_project_id is False:
        return _result(
            RpsProjectStatus.INVALID_INPUT,
            target.position_id,
            None,
            "mapped_project_id must be null or a non-empty string",
        )
    pending_creation_intent = payload.get("pending_creation_intent")
    if type(pending_creation_intent) is not bool:
        return _result(
            RpsProjectStatus.INVALID_INPUT,
            target.position_id,
            None,
            "pending_creation_intent must be a bool",
        )
    if _query_failed(observation) or _has_conflicting_duplicate_ids(projects):
        return _result(
            RpsProjectStatus.QUERY_FAILED,
            target.position_id,
            None,
            "project observation is incomplete, stale, errored, or internally conflicting",
        )
    if pending_creation_intent:
        return _result(
            RpsProjectStatus.RECONCILE_REQUIRED,
            target.position_id,
            None,
            "existing creation intent must be reconciled before another create decision",
        )
    by_id = {project.project_id: project for project in projects}
    if isinstance(mapped_project_id, str):
        mapped = by_id.get(mapped_project_id)
        if mapped is None or not _has_target_id_evidence(mapped, target):
            return _result(
                RpsProjectStatus.MAPPING_CONFLICT,
                target.position_id,
                None,
                "mapped project id was absent or did not match the target evidence",
            )
        return _result(
            RpsProjectStatus.REUSE,
            target.position_id,
            mapped.project_id,
            "mapped project id matched the target evidence",
        )
    matching_ids = {
        project.project_id for project in projects if _has_target_id_evidence(project, target)
    }
    if len(matching_ids) == 1:
        return _result(
            RpsProjectStatus.REUSE,
            target.position_id,
            next(iter(matching_ids)),
            "exactly one project matched customer and position id evidence",
        )
    if len(matching_ids) > 1:
        return _result(
            RpsProjectStatus.AMBIGUOUS,
            target.position_id,
            None,
            "multiple projects matched customer and position id evidence",
        )
    if any(_has_name_only_evidence(project, target) for project in projects):
        return _result(
            RpsProjectStatus.AMBIGUOUS,
            target.position_id,
            None,
            "visible names matched without stable customer and position id evidence",
        )
    return RpsProjectResolution(
        status=RpsProjectStatus.CREATE_REQUIRED,
        position_id=target.position_id,
        project_id=None,
        reason="complete fresh observation found no project for the target",
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
    account_scope = _required_text(raw, "account_scope")
    if account_scope is None:
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
        account_scope=account_scope,
        query_error=query_error,
        all_pages_loaded=all_pages_loaded,
        stale=stale,
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
        projects.append(
            _Project(
                project_id=project_id,
                customer_id=_optional_text(item, "customer_id"),
                position_id=_optional_text(item, "position_id"),
                customer_name=_optional_text(item, "customer_name"),
                position_title=_optional_text(item, "position_title"),
                name=_optional_text(item, "name"),
            )
        )
    return projects


def _mapped_project_id(raw: object) -> str | None | bool:
    if raw is None:
        return None
    if isinstance(raw, str) and raw.strip():
        return raw.strip()
    return False


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


def _has_name_only_evidence(project: _Project, target: _Target) -> bool:
    visible_customer = project.customer_name == target.customer_name
    visible_position = project.position_title == target.position_title
    visible_name = project.name == f"{target.customer_name} {target.position_title}"
    lacks_stable_evidence = project.customer_id is None or project.position_id is None
    return lacks_stable_evidence and (visible_customer or visible_position or visible_name)


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
