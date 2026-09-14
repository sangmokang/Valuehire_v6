"""Plan-only RPS project resolution boundary."""

from dataclasses import dataclass
from enum import Enum


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


def resolve_rps_project(payload: object) -> RpsProjectResolution:
    """Return a safe callable skeleton before behavior is implemented."""

    position_id = payload.get("position_id") if isinstance(payload, dict) else None
    if not isinstance(position_id, str) or not position_id.strip():
        position_id = None
    return RpsProjectResolution(
        status=RpsProjectStatus.INVALID_INPUT,
        position_id=position_id,
        project_id=None,
        reason="resolution skeleton does not yet evaluate observations",
    )
