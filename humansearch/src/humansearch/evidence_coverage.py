"""Deterministic HS-02.03 coverage classification for evidence manifests."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import TypeGuard

from humansearch.evidence_validation import validate_evidence_manifest

__all__ = ["EvidenceCoverageResult", "classify_evidence_coverage"]

type JsonMapping = Mapping[object, object]


@dataclass(frozen=True, slots=True)
class EvidenceCoverageResult:
    """Closed coverage decision without raw manifest values."""

    coverage_status: str
    coverage_reason: str
    last_observed_y_px: int


def classify_evidence_coverage(manifest: object) -> EvidenceCoverageResult:
    """Classify one HS evidence manifest without browser, storage, or network I/O."""

    if not validate_evidence_manifest(manifest).valid:
        return EvidenceCoverageResult(
            coverage_status="failed",
            coverage_reason="invalid_manifest",
            last_observed_y_px=_last_observed_y(manifest),
        )
    if not isinstance(manifest, Mapping):
        return EvidenceCoverageResult(
            coverage_status="failed",
            coverage_reason="invalid_manifest",
            last_observed_y_px=0,
        )

    height_state = manifest["height_state"]
    last_observed_y_px = _last_observed_y(manifest)
    if height_state == "observed_changed":
        return _partial("height_observed_changed", last_observed_y_px)
    if height_state == "not_observed":
        return _partial("height_not_observed", last_observed_y_px)
    if height_state == "not_applicable":
        return _partial("height_not_applicable", last_observed_y_px)

    document_height = manifest["document_height_px"]
    if not _is_int(document_height):
        return EvidenceCoverageResult(
            coverage_status="failed",
            coverage_reason="invalid_manifest",
            last_observed_y_px=last_observed_y_px,
        )

    intervals = _observed_intervals(manifest)
    if _covers_height(intervals, document_height):
        return EvidenceCoverageResult(
            coverage_status="complete",
            coverage_reason="all_segments_observed",
            last_observed_y_px=document_height,
        )

    reason = _partial_reason(manifest, intervals, document_height)
    return _partial(reason, last_observed_y_px)


def _partial(reason: str, last_observed_y_px: int) -> EvidenceCoverageResult:
    return EvidenceCoverageResult(
        coverage_status="partial",
        coverage_reason=reason,
        last_observed_y_px=last_observed_y_px,
    )


def _partial_reason(manifest: JsonMapping, intervals: Sequence[tuple[int, int]], height: int) -> str:
    if not intervals:
        return "no_observed_segments"
    if height == 0:
        return "zero_document_height"
    cursor = 0
    for top, bottom in intervals:
        if top > cursor:
            return "segment_gap"
        cursor = max(cursor, bottom)
    if cursor < height:
        return "trailing_gap"
    return "segment_gap"


def _covers_height(intervals: Sequence[tuple[int, int]], height: int) -> bool:
    if not intervals:
        return False
    if height == 0:
        return False
    cursor = 0
    for top, bottom in intervals:
        if top > cursor:
            return False
        cursor = max(cursor, bottom)
        if cursor >= height:
            return True
    return cursor >= height


def _observed_intervals(manifest: JsonMapping) -> list[tuple[int, int]]:
    intervals: list[tuple[int, int]] = []
    segments = manifest.get("segments")
    if not _is_sequence(segments):
        return intervals
    for segment in segments:
        if not isinstance(segment, Mapping) or segment.get("segment_status") != "observed":
            continue
        top = segment.get("top_y_px")
        bottom = segment.get("bottom_y_px")
        if _is_int(top) and _is_int(bottom) and bottom > top:
            intervals.append((top, bottom))
    return sorted(intervals)


def _last_observed_y(manifest: object) -> int:
    if not isinstance(manifest, Mapping):
        return 0
    segments = manifest.get("segments")
    if not _is_sequence(segments):
        return 0
    observed_bottoms: list[int] = []
    for segment in segments:
        if not isinstance(segment, Mapping) or segment.get("segment_status") != "observed":
            continue
        bottom = segment.get("bottom_y_px")
        if _is_int(bottom):
            observed_bottoms.append(bottom)
    return max(observed_bottoms, default=0)

def _is_sequence(value: object) -> TypeGuard[Sequence[object]]:
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray))


def _is_int(value: object) -> TypeGuard[int]:
    return type(value) is int
