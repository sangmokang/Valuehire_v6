from __future__ import annotations

from copy import deepcopy
from dataclasses import FrozenInstanceError
from typing import cast

import pytest

from humansearch.evidence_validation import (
    SUPPORTED_EVIDENCE_SCHEMA_VERSION,
    validate_evidence_manifest,
)

HASH = "a" * 64
URL_HASH = "b" * 64


def _field(value: object, state: str = "observed_value") -> dict[str, object]:
    return {
        "value": value,
        "state": state,
        "source_segment_indexes": [0],
    }


def _valid_manifest() -> dict[str, object]:
    return {
        "evidence_id": "ev_001",
        "run_id": "run_001",
        "position_ref": "CU-123",
        "channel": "linkedin_rps",
        "candidate_ref": "cand_001",
        "candidate_ref_state": "observed",
        "source_url": "https://www.linkedin.com/in/example",
        "source_url_hash": URL_HASH,
        "observed_at": "2026-09-14T10:00:00+09:00",
        "browser_context_ref": "aside://profile/main/tab/1",
        "search_condition_ref": "search_001",
        "document_height_px": 1200,
        "height_state": "observed_stable",
        "viewport_width_px": 1280,
        "viewport_height_px": 720,
        "segments": [
            {
                "segment_index": 0,
                "top_y_px": 0,
                "bottom_y_px": 720,
                "capture_sha256": HASH,
                "text_sha256": HASH,
                "capture_ref": "protected://captures/ev_001/0.png",
                "segment_status": "observed",
            }
        ],
        "coverage_status": "partial",
        "coverage_reason": "last visible segment ends before stable document height",
        "last_observed_y_px": 720,
        "extracted_fields": {
            "name": _field("홍길동"),
            "headline": _field("", "observed_empty"),
            "portfolio": _field(None, "not_available"),
        },
        "company_duties": [
            {
                "company_observed_name": "Example Corp",
                "company_alias_ref": "alias_001",
                "role_title": "Engineer",
                "date_range": "2020-2024",
                "duty_text": "Built internal tools",
                "duty_state": "observed_value",
                "source_segment_indexes": [0],
            }
        ],
        "company_duties_state": "observed",
        "company_aliases": [
            {
                "alias_text": "Example Corp",
                "canonical_company_ref": "company_001",
                "alias_basis": "operator_confirmed",
                "source_segment_indexes": [0],
            }
        ],
        "observed_contact_fields": {
            "email": _field(None, "not_observed"),
        },
        "readback_status": "not_run",
    }


def _error_codes(manifest: object, *, schema_version: str = SUPPORTED_EVIDENCE_SCHEMA_VERSION) -> set[str]:
    return {error.code for error in validate_evidence_manifest(manifest, schema_version=schema_version).errors}


def _error_paths(manifest: object) -> set[str]:
    return {error.path for error in validate_evidence_manifest(manifest).errors}


def test_accepts_sot_shaped_manifest_without_io_or_coverage_algorithm() -> None:
    result = validate_evidence_manifest(_valid_manifest())

    assert result.valid is True
    assert result.errors == ()


def test_result_and_errors_are_frozen_and_typed() -> None:
    manifest = _valid_manifest()
    del manifest["source_url_hash"]

    result = validate_evidence_manifest(manifest)

    assert result.valid is False
    assert result.errors
    assert result.errors[0].path == "source_url_hash"
    assert result.errors[0].code == "missing_required_field"
    with pytest.raises(FrozenInstanceError):
        result.errors = ()  # type: ignore[misc]


def test_input_error_is_closed_for_non_mapping_payload() -> None:
    result = validate_evidence_manifest(["not", "a", "mapping"])

    assert result.valid is False
    assert result.errors[0].path == "$"
    assert result.errors[0].code == "manifest_not_object"


def test_rejects_missing_required_field_without_echoing_private_value() -> None:
    manifest = _valid_manifest()
    manifest["evidence_id"] = "PRIVATE-CANDIDATE-NAME-DO-NOT-ECHO"
    del manifest["observed_at"]

    result = validate_evidence_manifest(manifest)

    assert ("observed_at", "missing_required_field") in {
        (error.path, error.code) for error in result.errors
    }
    rendered = repr(result.errors)
    assert "PRIVATE-CANDIDATE-NAME-DO-NOT-ECHO" not in rendered


def test_rejects_negative_integer_and_bool_as_number() -> None:
    negative = _valid_manifest()
    negative["viewport_height_px"] = -1
    bool_number = _valid_manifest()
    bool_number["last_observed_y_px"] = True

    assert "invalid_integer" in _error_codes(negative)
    assert "invalid_integer" in _error_codes(bool_number)


def test_rejects_unsupported_schema_version_without_manifest_key() -> None:
    manifest = _valid_manifest()

    result = validate_evidence_manifest(manifest, schema_version="humansearch.evidence.v2")

    assert result.valid is False
    assert result.errors[0].path == "$schema_version"
    assert result.errors[0].code == "unsupported_schema_version"
    assert "schema_version" not in manifest


def test_rejects_candidate_ref_state_value_contradictions() -> None:
    missing_ref = _valid_manifest()
    missing_ref["candidate_ref"] = None
    wrong_null = _valid_manifest()
    wrong_null["candidate_ref_state"] = "not_observed"

    assert "state_value_mismatch" in _error_codes(missing_ref)
    assert "state_value_mismatch" in _error_codes(wrong_null)


def test_rejects_height_state_value_and_note_contradictions() -> None:
    changed = _valid_manifest()
    changed["height_state"] = "observed_changed"
    changed["document_height_px"] = 1200
    changed["coverage_status"] = "complete"

    assert _error_codes(changed) >= {"state_value_mismatch", "missing_conditional_field"}
    assert {"document_height_px", "height_observation_note", "coverage_status"} <= _error_paths(
        changed
    )


def test_rejects_company_duties_state_array_contradictions() -> None:
    empty_observed = _valid_manifest()
    empty_observed["company_duties"] = []
    empty_observed["company_duties_state"] = "observed"
    non_empty_not_observed = _valid_manifest()
    non_empty_not_observed["company_duties_state"] = "not_observed"

    assert "state_value_mismatch" in _error_codes(empty_observed)
    assert "state_value_mismatch" in _error_codes(non_empty_not_observed)


def test_rejects_segment_coordinate_type_and_shape_errors() -> None:
    manifest = _valid_manifest()
    segment = cast(list[dict[str, object]], deepcopy(manifest["segments"]))[0]
    segment["bottom_y_px"] = 0
    segment["segment_index"] = True
    manifest["segments"] = [segment]

    assert _error_paths(manifest) >= {"segments[0].bottom_y_px", "segments[0].segment_index"}


def test_rejects_hash_shape_and_failed_segment_without_reason() -> None:
    manifest = _valid_manifest()
    segment = cast(list[dict[str, object]], deepcopy(manifest["segments"]))[0]
    segment["capture_sha256"] = "not-a-hash"
    segment["segment_status"] = "failed"
    manifest["segments"] = [segment]

    assert _error_paths(manifest) >= {"segments[0].capture_sha256", "segments[0].failure_reason"}


def test_rejects_extracted_field_and_contact_shapes() -> None:
    manifest = _valid_manifest()
    manifest["extracted_fields"] = {"name": {"value": "Jane", "state": "not_observed"}}
    manifest["observed_contact_fields"] = {"email": {"value": "a@example.com", "state": "hidden"}}

    assert _error_paths(manifest) >= {
        "extracted_fields[0].source_segment_indexes",
        "extracted_fields[0].value",
        "observed_contact_fields[0].state",
    }


def test_rejects_company_duty_and_alias_shapes() -> None:
    manifest = _valid_manifest()
    manifest["company_duties"] = [
        {
            "company_observed_name": "Example Corp",
            "duty_state": "observed_value",
            "source_segment_indexes": [],
        }
    ]
    manifest["company_aliases"] = [
        {
            "alias_text": "Example Corp",
            "alias_basis": "same_guess",
            "source_segment_indexes": [0],
        }
    ]

    assert _error_paths(manifest) >= {
        "company_duties[0].source_segment_indexes",
        "company_duties[0].duty_text",
        "company_aliases[0].alias_basis",
    }


def test_rejects_readback_conditional_fields() -> None:
    manifest = _valid_manifest()
    manifest["readback_status"] = "blocked"

    assert _error_paths(manifest) >= {"readback_at", "readback_failure_reason"}


def test_rejects_required_array_and_object_fields_even_when_none_or_string() -> None:
    manifest = _valid_manifest()
    manifest["segments"] = "not-an-array"
    manifest["extracted_fields"] = None
    manifest["observed_contact_fields"] = None
    manifest["company_aliases"] = None

    result = validate_evidence_manifest(manifest)

    assert result.valid is False
    assert {error.path for error in result.errors} >= {
        "segments",
        "extracted_fields",
        "observed_contact_fields",
        "company_aliases",
    }
    assert {error.code for error in result.errors} >= {"invalid_array", "invalid_object"}


def test_validates_optional_readback_fields_when_not_required() -> None:
    manifest = _valid_manifest()
    manifest["readback_status"] = "not_run"
    manifest["readback_at"] = "not-a-timestamp"
    manifest["readback_failure_reason"] = ""

    assert _error_paths(manifest) >= {"readback_at", "readback_failure_reason"}


def test_error_paths_do_not_echo_unknown_top_level_or_extracted_field_names() -> None:
    private_top_level = "candidate_email_jane.doe@example.com"
    private_field_name = "phone_010-1234-5678"
    manifest = _valid_manifest()
    manifest[private_top_level] = "secret"
    manifest["extracted_fields"] = {
        private_field_name: {
            "value": "secret",
            "state": "not_observed",
            "source_segment_indexes": [],
        }
    }

    result = validate_evidence_manifest(manifest)

    assert result.valid is False
    assert "unknown_fields[0]" in {error.path for error in result.errors}
    assert {"extracted_fields[0].value", "extracted_fields[0].source_segment_indexes"} <= {
        error.path for error in result.errors
    }
    rendered_errors = repr(result.errors)
    assert private_top_level not in rendered_errors
    assert private_field_name not in rendered_errors
    assert "jane.doe@example.com" not in rendered_errors
    assert "010-1234-5678" not in rendered_errors
