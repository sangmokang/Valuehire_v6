from __future__ import annotations

from copy import deepcopy
from typing import cast

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from humansearch.evidence_coverage import classify_evidence_coverage
from humansearch.evidence_validation import validate_evidence_manifest

HASH = "a" * 64
URL_HASH = "b" * 64


def _field(value: object, state: str = "observed_value") -> dict[str, object]:
    return {
        "value": value,
        "state": state,
        "source_segment_indexes": [0],
    }


def _segment(
    index: int,
    top: int,
    bottom: int,
    *,
    status: str = "observed",
) -> dict[str, object]:
    segment: dict[str, object] = {
        "segment_index": index,
        "top_y_px": top,
        "bottom_y_px": bottom,
        "capture_sha256": HASH,
        "text_sha256": HASH,
        "capture_ref": f"protected://captures/ev_coverage/{index}.png",
        "segment_status": status,
    }
    if status == "failed":
        segment["failure_reason"] = "capture failed"
    return segment


def _manifest(segments: list[dict[str, object]], *, height: int = 1200) -> dict[str, object]:
    return {
        "evidence_id": "ev_coverage",
        "run_id": "run_coverage",
        "position_ref": "CU-123",
        "channel": "linkedin_rps",
        "candidate_ref": "cand_001",
        "candidate_ref_state": "observed",
        "source_url": "https://www.linkedin.com/in/example",
        "source_url_hash": URL_HASH,
        "observed_at": "2026-09-14T10:00:00+09:00",
        "browser_context_ref": "aside://profile/main/tab/1",
        "search_condition_ref": "search_001",
        "document_height_px": height,
        "height_state": "observed_stable",
        "viewport_width_px": 1280,
        "viewport_height_px": 720,
        "segments": segments,
        "coverage_status": "partial",
        "coverage_reason": "pending classifier output",
        "last_observed_y_px": 0,
        "extracted_fields": {
            "name": _field("Jane Candidate"),
        },
        "company_duties": [
            {
                "company_observed_name": "Example Corp",
                "role_title": "Engineer",
                "date_range": "2020-2024",
                "duty_text": "Built internal tools",
                "duty_state": "observed_value",
                "source_segment_indexes": [0],
            }
        ],
        "company_duties_state": "observed",
        "company_aliases": [],
        "observed_contact_fields": {
            "email": _field(None, "not_observed"),
        },
        "readback_status": "not_run",
    }


def test_complete_requires_observed_segments_covering_full_stable_height() -> None:
    manifest = _manifest([_segment(1, 500, 1200), _segment(0, 0, 500)])

    result = classify_evidence_coverage(manifest)

    assert result.coverage_status == "complete"
    assert result.coverage_reason == "all_segments_observed"
    assert result.last_observed_y_px == 1200


def test_middle_gap_is_partial_with_gap_reason() -> None:
    manifest = _manifest([_segment(0, 0, 400), _segment(1, 500, 1200)])

    result = classify_evidence_coverage(manifest)

    assert result.coverage_status == "partial"
    assert result.coverage_reason == "segment_gap"
    assert result.last_observed_y_px == 1200


def test_trailing_gap_is_partial_and_records_last_observed_boundary() -> None:
    manifest = _manifest([_segment(0, 0, 720)])

    result = classify_evidence_coverage(manifest)

    assert result.coverage_status == "partial"
    assert result.coverage_reason == "trailing_gap"
    assert result.last_observed_y_px == 720


def test_failed_and_redacted_segments_do_not_prove_complete_coverage() -> None:
    failed = _manifest([_segment(0, 0, 800), _segment(1, 800, 1200, status="failed")])
    redacted = _manifest([_segment(0, 0, 800), _segment(1, 800, 1200, status="redacted")])

    assert classify_evidence_coverage(failed).coverage_status == "partial"
    assert classify_evidence_coverage(failed).coverage_reason == "trailing_gap"
    assert classify_evidence_coverage(redacted).coverage_status == "partial"
    assert classify_evidence_coverage(redacted).coverage_reason == "trailing_gap"


def test_zero_height_without_observed_segments_is_not_complete() -> None:
    manifest = _manifest([_segment(0, 0, 1, status="failed")], height=0)

    result = classify_evidence_coverage(manifest)

    assert result.coverage_status == "partial"
    assert result.coverage_reason == "no_observed_segments"
    assert result.last_observed_y_px == 0


def test_zero_height_with_observed_segment_is_not_complete() -> None:
    manifest = _manifest([_segment(0, 0, 1)], height=0)

    result = classify_evidence_coverage(manifest)

    assert result.coverage_status == "partial"
    assert result.coverage_reason == "zero_document_height"
    assert result.last_observed_y_px == 1


def test_failed_segment_in_middle_reports_segment_gap() -> None:
    manifest = _manifest(
        [
            _segment(0, 0, 400),
            _segment(1, 400, 500, status="failed"),
            _segment(2, 500, 1200),
        ]
    )

    result = classify_evidence_coverage(manifest)

    assert result.coverage_status == "partial"
    assert result.coverage_reason == "segment_gap"


def test_changed_height_is_never_promoted_to_complete() -> None:
    manifest = _manifest([_segment(0, 0, 1200)])
    manifest["height_state"] = "observed_changed"
    manifest["document_height_px"] = None
    manifest["height_observation_note"] = "height changed while scrolling"

    result = classify_evidence_coverage(manifest)

    assert result.coverage_status == "partial"
    assert result.coverage_reason == "height_observed_changed"
    assert result.last_observed_y_px == 1200


def test_unknown_height_remains_partial_even_with_observed_segment() -> None:
    manifest = _manifest([_segment(0, 0, 1200)])
    manifest["height_state"] = "not_observed"
    manifest["document_height_px"] = None
    manifest["height_observation_note"] = "document height was not available"

    result = classify_evidence_coverage(manifest)

    assert result.coverage_status == "partial"
    assert result.coverage_reason == "height_not_observed"
    assert result.last_observed_y_px == 1200


def test_not_applicable_height_remains_partial() -> None:
    manifest = _manifest([_segment(0, 0, 1200)])
    manifest["height_state"] = "not_applicable"
    manifest["document_height_px"] = None

    result = classify_evidence_coverage(manifest)

    assert result.coverage_status == "partial"
    assert result.coverage_reason == "height_not_applicable"
    assert result.last_observed_y_px == 1200


def test_invalid_manifest_is_failed_without_echoing_private_values() -> None:
    manifest = _manifest([_segment(0, 0, 1200)])
    manifest["source_url"] = "candidate-private-url"

    result = classify_evidence_coverage(manifest)

    assert result.coverage_status == "failed"
    assert result.coverage_reason == "invalid_manifest"
    assert result.last_observed_y_px == 0
    assert "candidate-private-url" not in repr(result)


def test_classification_output_can_update_manifest_to_validate_again() -> None:
    manifest = _manifest([_segment(0, 0, 600), _segment(1, 600, 1200)])
    result = classify_evidence_coverage(manifest)
    updated = deepcopy(manifest)
    updated["coverage_status"] = result.coverage_status
    updated["coverage_reason"] = result.coverage_reason
    updated["last_observed_y_px"] = result.last_observed_y_px

    assert validate_evidence_manifest(updated).valid is True


@given(
    first_end=st.integers(min_value=1, max_value=999),
    gap=st.integers(min_value=1, max_value=50),
    tail=st.integers(min_value=1, max_value=950),
)
@settings(max_examples=60, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_hypothesis_detects_any_middle_gap_as_partial(
    first_end: int,
    gap: int,
    tail: int,
) -> None:
    height = max(first_end + gap + tail, 2)
    manifest = _manifest(
        [
            _segment(0, 0, first_end),
            _segment(1, first_end + gap, height),
        ],
        height=height,
    )

    result = classify_evidence_coverage(manifest)

    assert result.coverage_status == "partial"
    assert result.coverage_reason == "segment_gap"


@given(
    splits=st.lists(st.integers(min_value=1, max_value=200), min_size=1, max_size=8),
)
@settings(max_examples=60, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_hypothesis_accepts_full_cover_even_when_segments_are_out_of_order(
    splits: list[int],
) -> None:
    top = 0
    segments: list[dict[str, object]] = []
    for index, height in enumerate(splits):
        bottom = top + height
        segments.append(_segment(index, top, bottom))
        top = bottom
    manifest = _manifest(list(reversed(segments)), height=top)

    result = classify_evidence_coverage(manifest)

    assert result.coverage_status == "complete"
    assert result.coverage_reason == "all_segments_observed"
    assert result.last_observed_y_px == top


def test_input_manifest_is_not_mutated() -> None:
    manifest = _manifest([_segment(0, 0, 1200)])
    before = deepcopy(manifest)

    classify_evidence_coverage(manifest)

    assert manifest == before


def test_bool_coordinates_are_failed_through_parent_validator() -> None:
    manifest = _manifest([_segment(0, 0, 1200)])
    segments = cast(list[dict[str, object]], manifest["segments"])
    segments[0]["bottom_y_px"] = True

    result = classify_evidence_coverage(manifest)

    assert result.coverage_status == "failed"
    assert result.coverage_reason == "invalid_manifest"
    assert result.last_observed_y_px == 0


def test_invalid_negative_coordinate_does_not_become_last_observed_y() -> None:
    manifest = _manifest([_segment(0, 0, 1200)])
    segments = cast(list[dict[str, object]], manifest["segments"])
    segments[0]["bottom_y_px"] = -7

    result = classify_evidence_coverage(manifest)

    assert result.coverage_status == "failed"
    assert result.coverage_reason == "invalid_manifest"
    assert result.last_observed_y_px == 0
