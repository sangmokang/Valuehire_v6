"""Evidence assessment CLI. Live Jev needs ``--live-jev``, a key (``AI_GATEWAY_API_KEY`` for the Vercel
AI Gateway, else ``TYPESAFE_API_KEY``) and permission in the repository contract itself;
``delivery_status`` reports whether a request was attempted and ``jev_call`` what answered it."""

import argparse
import json
import os
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Never

from humansearch.evidence_assessment import EvidenceConfig, assess_evidence, load_evidence_config
from humansearch.organization_shadow import _mapping
from humansearch.organization_shadow_cli import CountingJudge, _same_file, _write_atomic, delivery
from humansearch.organization_shadow_jev import TypeSafeJevJudge
from humansearch.tier_table import load_tier_table

GATEWAY_URL = "https://ai-gateway.vercel.sh/typesafe"

CONTRACT_PATH = Path(__file__).resolve().parents[3] / "contracts/jev-evidence-assessment.json"
# F15: tier tables come only from the repository; other tables enter through assess_evidence(...).
TIER_PATHS = {kind: CONTRACT_PATH.parent / f"{kind}-tier.json" for kind in ("school", "company")}


def main(argv: Sequence[str] | None = None, *, config: EvidenceConfig | None = None) -> int:
    """``config`` is code injection for tests; a ``--config`` file may never enable live calls."""
    parser = argparse.ArgumentParser(description="Run one evidence assessment")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--config", type=Path, default=CONTRACT_PATH)
    parser.add_argument("--live-jev", action="store_true")
    args = parser.parse_args(argv)
    judge: CountingJudge | None = None
    # F16: the repository contract is protected even when an outside --config is read.
    if _same_file(args.output, [args.input, args.config, CONTRACT_PATH, *TIER_PATHS.values()]):
        _stop("output_collision", judge)
    try:
        payload = _mapping(json.loads(args.input.read_text(encoding="utf-8")), "input")
        settings = config or _file_config(args.config)
        schools = load_tier_table(TIER_PATHS["school"], "school")
        companies = load_tier_table(TIER_PATHS["company"], "company")
        live = args.live_jev and settings.live_calls_allowed
        gateway_key = os.environ.get("AI_GATEWAY_API_KEY", "").strip()
        has_key = gateway_key or os.environ.get("TYPESAFE_API_KEY", "").strip()
        judge = CountingJudge(lambda: _judge(gateway_key)) if live and has_key else None
        try:
            result = assess_evidence(payload, config=settings, school_tiers=schools,
                                     company_tiers=companies, judge=judge)
        finally:
            if judge is not None:
                judge.close()
        _write_atomic(args.output, {**delivery(judge), **result,
                                    "jev_call": _call_record(judge, settings, gateway_key)})
    except (OSError, ValueError, TypeError):
        _stop("invalid_input_or_config", judge)
    except Exception:  # noqa: BLE001 - the CLI must not print raw SDK or candidate data.
        _stop("evidence_assessment_failed", judge)
    return 0


def _stop(code: str, judge: CountingJudge | None) -> Never:
    """A failure after a request (e.g. the output write) still reports that data may have left."""
    print(json.dumps({"ok": False, "error_code": code, **delivery(judge)}, sort_keys=True),
          file=sys.stderr)
    raise SystemExit(2)


def _judge(gateway_key: str) -> TypeSafeJevJudge:
    """The Gateway key wins: direct TypeSafe signup is closed (2026-09-24)."""
    if gateway_key:
        return TypeSafeJevJudge(api_key=gateway_key, base_url=GATEWAY_URL)
    return TypeSafeJevJudge()


def _call_record(judge: CountingJudge | None, settings: EvidenceConfig,
                 gateway_key: str) -> dict[str, object] | None:
    """Which endpoint and model answered; "jev" floats, so the response metadata is the only trace."""
    if judge is None or not judge.request_attempts:
        return None
    response = judge.last_response or {}
    return {"endpoint": GATEWAY_URL if gateway_key else "typesafe-sdk-default",
            "requested_model": settings.model_version, "response_model": response.get("model"),
            "provider_metadata": response.get("provider_metadata")}


def _file_config(path: Path) -> EvidenceConfig:
    config = load_evidence_config(path)
    if config.live_calls_allowed and path.resolve() != CONTRACT_PATH:
        raise ValueError("only the repository contract may allow live Jev calls")
    return config


if __name__ == "__main__":
    raise SystemExit(main())
