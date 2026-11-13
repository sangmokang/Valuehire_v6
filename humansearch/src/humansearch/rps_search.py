"""One-shot CLI for a verified search in the existing Aside Recruiter tab."""

import argparse
import json
import re
import uuid
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Protocol

from .rps_search_contract import PlanValidationError, SearchPlan, SearchStatus
from .rps_search_driver import (
    RpsDriftError,
    RpsFilterPort,
    RpsTransportError,
    run_verified_filters,
)
from .rps_search_port import AsideRpsPort, RpsResultTimeout

_RUN_ID = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
_PNG_HEADER = b"\x89PNG\r\n\x1a\n"


class RpsSearchPort(RpsFilterPort, Protocol):
    def wait_result_count(self) -> int: ...

    def capture_screenshot(self) -> bytes: ...

    def close(self) -> None: ...


@dataclass(frozen=True, slots=True)
class SearchResult:
    status: SearchStatus
    position_ref: str
    filters_verified: bool
    result_count: int | None
    screenshot_path: str | None

    def to_dict(self) -> dict[str, object]:
        output = asdict(self)
        output["status"] = self.status.value
        return output


def execute_search(
    plan: SearchPlan,
    port: RpsSearchPort,
    *,
    artifacts_dir: Path,
    run_id: str,
) -> SearchResult:
    """Run the vertical slice; browser acknowledgements alone never mean success."""

    filtered = run_verified_filters(plan, port)
    if filtered.status is not None:
        return SearchResult(filtered.status, plan.position_ref, False, None, None)
    try:
        result_count = port.wait_result_count()
    except RpsDriftError:
        return SearchResult(SearchStatus.DRIFTED, plan.position_ref, True, None, None)
    except (RpsResultTimeout, RpsTransportError):
        return SearchResult(SearchStatus.FAILED, plan.position_ref, True, None, None)
    try:
        screenshot_path = _save_screenshot(
            port.capture_screenshot(), artifacts_dir=artifacts_dir, run_id=run_id
        )
    except (OSError, RpsTransportError, ValueError):
        return SearchResult(
            SearchStatus.FAILED, plan.position_ref, True, result_count, None
        )
    return SearchResult(
        SearchStatus.COMPLETED,
        plan.position_ref,
        True,
        result_count,
        str(screenshot_path),
    )


def main(
    argv: Sequence[str] | None = None,
    *,
    port_factory: Callable[[], RpsSearchPort] = AsideRpsPort,
    artifacts_dir: Path = Path(".artifacts/rps-search"),
    run_id_factory: Callable[[], str] = lambda: uuid.uuid4().hex,
) -> int:
    parser = argparse.ArgumentParser(prog="python -m humansearch.rps_search")
    parser.add_argument("--plan", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        payload = json.loads(args.plan.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise PlanValidationError("plan must be an object")
        plan = SearchPlan.from_mapping(payload)
    except (OSError, ValueError, RecursionError):
        _print_result(SearchResult(SearchStatus.FAILED, "-", False, None, None))
        return 2

    port: RpsSearchPort | None = None
    try:
        port = port_factory()
        result = execute_search(
            plan,
            port,
            artifacts_dir=artifacts_dir,
            run_id=run_id_factory(),
        )
    except (OSError, RpsTransportError, RpsDriftError):
        result = SearchResult(SearchStatus.FAILED, plan.position_ref, False, None, None)
    finally:
        if port is not None:
            port.close()
    _print_result(result)
    return 0 if result.status is SearchStatus.COMPLETED else 2


def _save_screenshot(screenshot: bytes, *, artifacts_dir: Path, run_id: str) -> Path:
    if not _RUN_ID.fullmatch(run_id) or not screenshot.startswith(_PNG_HEADER):
        raise ValueError("invalid screenshot artifact")
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    destination = artifacts_dir / f"{run_id}.png"
    destination.write_bytes(screenshot)
    screenshots = sorted(
        artifacts_dir.glob("*.png"), key=lambda path: path.stat().st_mtime, reverse=True
    )
    for expired in screenshots[20:]:
        expired.unlink()
    return destination


def _print_result(result: SearchResult) -> None:
    print(json.dumps(result.to_dict(), ensure_ascii=False, separators=(",", ":")))


if __name__ == "__main__":
    raise SystemExit(main())
