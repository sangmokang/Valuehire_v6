"""Deterministic HS-02.03 coverage classification for evidence manifests."""

from __future__ import annotations

from dataclasses import dataclass

__all__ = ["EvidenceCoverageResult", "classify_evidence_coverage"]


@dataclass(frozen=True, slots=True)
class EvidenceCoverageResult:
    """Closed coverage decision without raw manifest values."""

    coverage_status: str
    coverage_reason: str
    last_observed_y_px: int


def classify_evidence_coverage(manifest: object) -> EvidenceCoverageResult:
    """Classify one HS evidence manifest without browser, storage, or network I/O."""

    return EvidenceCoverageResult(
        coverage_status="partial",
        coverage_reason="coverage_not_implemented",
        last_observed_y_px=0,
    )
