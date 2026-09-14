"""Pure shape validation for HS-02.01 evidence manifests."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Final, TypeGuard
from urllib.parse import urlparse

__all__ = [
    "SUPPORTED_EVIDENCE_SCHEMA_VERSION",
    "EvidenceValidationError",
    "EvidenceValidationResult",
    "validate_evidence_manifest",
]

type JsonObject = Mapping[str, object]

SUPPORTED_EVIDENCE_SCHEMA_VERSION: Final = "humansearch.evidence.v1"

_SHA256_RE: Final = re.compile(r"^[0-9a-f]{64}$")
_REQUIRED_FIELDS: Final[frozenset[str]] = frozenset(
    {
        "evidence_id",
        "run_id",
        "position_ref",
        "channel",
        "candidate_ref",
        "candidate_ref_state",
        "source_url",
        "source_url_hash",
        "observed_at",
        "browser_context_ref",
        "search_condition_ref",
        "document_height_px",
        "height_state",
        "viewport_width_px",
        "viewport_height_px",
        "segments",
        "coverage_status",
        "coverage_reason",
        "last_observed_y_px",
        "extracted_fields",
        "company_duties",
        "company_duties_state",
        "company_aliases",
        "observed_contact_fields",
        "readback_status",
    }
)
_OPTIONAL_FIELDS: Final[frozenset[str]] = frozenset(
    {"height_observation_note", "readback_at", "readback_failure_reason"}
)
_ALLOWED_FIELDS: Final = _REQUIRED_FIELDS | _OPTIONAL_FIELDS
_CHANNELS: Final = frozenset({"saramin", "jobkorea", "linkedin_rps"})
_CANDIDATE_REF_STATES: Final = frozenset({"observed", "not_observed", "not_available"})
_HEIGHT_STATES: Final = frozenset(
    {"observed_stable", "observed_changed", "not_observed", "not_applicable"}
)
_COVERAGE_STATUSES: Final = frozenset({"complete", "partial", "failed"})
_COMPANY_DUTIES_STATES: Final = frozenset(
    {"observed", "observed_empty", "not_observed", "not_available", "redacted"}
)
_READBACK_STATUSES: Final = frozenset({"not_run", "matched", "mismatch", "blocked"})
_SEGMENT_STATUSES: Final = frozenset({"observed", "failed", "redacted"})
_VALUE_STATES: Final = frozenset(
    {"observed_value", "observed_empty", "not_observed", "not_available", "redacted"}
)
_ALIAS_BASES: Final = frozenset(
    {"same_profile", "same_company_page", "operator_confirmed", "not_confirmed"}
)


@dataclass(frozen=True, slots=True)
class EvidenceValidationError:
    """One sanitized validation error without raw manifest values."""

    path: str
    code: str
    message: str


@dataclass(frozen=True, slots=True)
class EvidenceValidationResult:
    """Closed validation result for one evidence manifest input."""

    valid: bool
    errors: tuple[EvidenceValidationError, ...]


class _Collector:
    def __init__(self) -> None:
        self._errors: list[EvidenceValidationError] = []

    def add(self, path: str, code: str, message: str) -> None:
        self._errors.append(EvidenceValidationError(path=path, code=code, message=message))

    def result(self) -> EvidenceValidationResult:
        errors = tuple(self._errors)
        return EvidenceValidationResult(valid=not errors, errors=errors)


def validate_evidence_manifest(
    manifest: object,
    *,
    schema_version: str = SUPPORTED_EVIDENCE_SCHEMA_VERSION,
) -> EvidenceValidationResult:
    """Validate one HS-02.01 evidence manifest without I/O or raw value echoing."""

    errors = _Collector()
    if schema_version != SUPPORTED_EVIDENCE_SCHEMA_VERSION:
        errors.add("$schema_version", "unsupported_schema_version", "unsupported evidence schema")
        return errors.result()
    if not isinstance(manifest, Mapping):
        errors.add("$", "manifest_not_object", "manifest must be an object")
        return errors.result()
    if not all(isinstance(key, str) for key in manifest):
        errors.add("$", "manifest_key_type", "manifest keys must be strings")
        return errors.result()
    typed_manifest = manifest

    for field in sorted(_REQUIRED_FIELDS - typed_manifest.keys()):
        errors.add(field, "missing_required_field", "required field is missing")
    for field in sorted(set(typed_manifest) - _ALLOWED_FIELDS):
        errors.add(field, "unexpected_field", "field is not part of the evidence contract")

    _validate_top_level_scalars(typed_manifest, errors)
    _validate_candidate_ref(typed_manifest, errors)
    _validate_height(typed_manifest, errors)
    _validate_segments(_object_sequence(typed_manifest.get("segments")), errors)
    _validate_extracted_object(typed_manifest.get("extracted_fields"), "extracted_fields", errors)
    _validate_extracted_object(
        typed_manifest.get("observed_contact_fields"), "observed_contact_fields", errors
    )
    _validate_company_duties(typed_manifest, errors)
    _validate_company_aliases(typed_manifest.get("company_aliases"), errors)
    _validate_readback(typed_manifest, errors)
    return errors.result()


def _validate_top_level_scalars(manifest: Mapping[object, object], errors: _Collector) -> None:
    for field in (
        "evidence_id",
        "run_id",
        "position_ref",
        "browser_context_ref",
        "search_condition_ref",
        "coverage_reason",
    ):
        if field in manifest:
            _require_non_empty_string(manifest[field], field, errors)
    _require_enum(manifest.get("channel"), "channel", _CHANNELS, errors)
    _require_url(manifest.get("source_url"), "source_url", errors)
    _require_sha256(manifest.get("source_url_hash"), "source_url_hash", errors)
    _require_rfc3339(manifest.get("observed_at"), "observed_at", errors)
    _require_integer(manifest.get("viewport_width_px"), "viewport_width_px", errors)
    _require_integer(manifest.get("viewport_height_px"), "viewport_height_px", errors)
    _require_integer(manifest.get("last_observed_y_px"), "last_observed_y_px", errors)
    _require_enum(manifest.get("coverage_status"), "coverage_status", _COVERAGE_STATUSES, errors)
    if manifest.get("coverage_status") == "complete" and manifest.get(
        "coverage_reason"
    ) != "all_segments_observed":
        errors.add("coverage_reason", "state_value_mismatch", "complete coverage requires its fixed reason")


def _validate_candidate_ref(manifest: Mapping[object, object], errors: _Collector) -> None:
    state = manifest.get("candidate_ref_state")
    _require_enum(state, "candidate_ref_state", _CANDIDATE_REF_STATES, errors)
    ref = manifest.get("candidate_ref")
    if state == "observed":
        if not _is_non_empty_string(ref):
            errors.add("candidate_ref", "state_value_mismatch", "observed candidate_ref must be present")
    elif state in {"not_observed", "not_available"} and ref is not None:
        errors.add("candidate_ref", "state_value_mismatch", "unobserved candidate_ref must be null")


def _validate_height(manifest: Mapping[object, object], errors: _Collector) -> None:
    state = manifest.get("height_state")
    _require_enum(state, "height_state", _HEIGHT_STATES, errors)
    height = manifest.get("document_height_px")
    if state == "observed_stable":
        _require_integer(height, "document_height_px", errors)
    elif state in {"observed_changed", "not_observed", "not_applicable"}:
        if height is not None:
            errors.add("document_height_px", "state_value_mismatch", "unstable or unobserved height must be null")
        note = manifest.get("height_observation_note")
        if state in {"observed_changed", "not_observed"} and not _is_non_empty_string(note):
            errors.add(
                "height_observation_note",
                "missing_conditional_field",
                "height note is required for changed or unobserved height",
            )
    if state == "observed_changed" and manifest.get("coverage_status") == "complete":
        errors.add(
            "coverage_status",
            "state_value_mismatch",
            "changed height cannot be marked complete",
        )


def _validate_segments(segments: Sequence[object] | None, errors: _Collector) -> None:
    if segments is None:
        return
    if not isinstance(segments, Sequence) or isinstance(segments, (str, bytes, bytearray)):
        errors.add("segments", "invalid_array", "segments must be a non-empty array")
        return
    if not segments:
        errors.add("segments", "invalid_array", "segments must be a non-empty array")
        return
    for index, segment in enumerate(segments):
        path = f"segments[{index}]"
        if not isinstance(segment, Mapping):
            errors.add(path, "invalid_object", "segment must be an object")
            continue
        _require_integer(segment.get("segment_index"), f"{path}.segment_index", errors)
        _require_integer(segment.get("top_y_px"), f"{path}.top_y_px", errors)
        _require_integer(segment.get("bottom_y_px"), f"{path}.bottom_y_px", errors)
        top = segment.get("top_y_px")
        bottom = segment.get("bottom_y_px")
        if _is_int(top) and _is_int(bottom) and bottom <= top:
            errors.add(f"{path}.bottom_y_px", "invalid_coordinate", "bottom_y_px must exceed top_y_px")
        _require_sha256(segment.get("capture_sha256"), f"{path}.capture_sha256", errors)
        if "text_sha256" in segment and segment.get("text_sha256") is not None:
            _require_sha256(segment.get("text_sha256"), f"{path}.text_sha256", errors)
        _require_non_empty_string(segment.get("capture_ref"), f"{path}.capture_ref", errors)
        status = segment.get("segment_status")
        _require_enum(status, f"{path}.segment_status", _SEGMENT_STATUSES, errors)
        if status == "failed" and not _is_non_empty_string(segment.get("failure_reason")):
            errors.add(
                f"{path}.failure_reason",
                "missing_conditional_field",
                "failed segment requires a failure reason",
            )


def _validate_extracted_object(value: object, path: str, errors: _Collector) -> None:
    if value is None:
        return
    if not isinstance(value, Mapping):
        errors.add(path, "invalid_object", "field collection must be an object")
        return
    if not all(isinstance(key, str) for key in value):
        errors.add(path, "invalid_object", "field collection keys must be strings")
        return
    for name, wrapper in value.items():
        _validate_field_wrapper(wrapper, f"{path}.{name}", errors)


def _validate_field_wrapper(wrapper: object, path: str, errors: _Collector) -> None:
    if not isinstance(wrapper, Mapping):
        errors.add(path, "invalid_object", "field wrapper must be an object")
        return
    state = wrapper.get("state")
    _require_enum(state, f"{path}.state", _VALUE_STATES, errors)
    if "value" not in wrapper:
        errors.add(f"{path}.value", "missing_required_field", "field wrapper value is missing")
    value = wrapper.get("value")
    if state == "observed_value" and value is None:
        errors.add(f"{path}.value", "state_value_mismatch", "observed value cannot be null")
    if state in {"not_observed", "not_available", "redacted"} and value is not None:
        errors.add(f"{path}.value", "state_value_mismatch", "unobserved value must be null")
    if state == "observed_empty" and value not in ("", (), [], {}):
        errors.add(f"{path}.value", "state_value_mismatch", "observed empty must use an empty value")
    _validate_source_segment_indexes(wrapper.get("source_segment_indexes"), f"{path}.source_segment_indexes", errors)
    if "evidence_note" in wrapper and wrapper.get("evidence_note") is not None:
        _require_non_empty_string(wrapper.get("evidence_note"), f"{path}.evidence_note", errors)


def _validate_company_duties(manifest: Mapping[object, object], errors: _Collector) -> None:
    state = manifest.get("company_duties_state")
    _require_enum(state, "company_duties_state", _COMPANY_DUTIES_STATES, errors)
    duties_value = manifest.get("company_duties")
    duties = _object_sequence(duties_value)
    if duties is None:
        if "company_duties" in manifest:
            errors.add("company_duties", "invalid_array", "company_duties must be an array")
        return
    if state == "observed" and not duties:
        errors.add("company_duties", "state_value_mismatch", "observed company duties must be non-empty")
    if state in {"observed_empty", "not_observed", "not_available", "redacted"} and duties:
        errors.add("company_duties", "state_value_mismatch", "unobserved company duties must be empty")
    for index, duty in enumerate(duties):
        path = f"company_duties[{index}]"
        if not isinstance(duty, Mapping):
            errors.add(path, "invalid_object", "company duty must be an object")
            continue
        _require_non_empty_string(duty.get("company_observed_name"), f"{path}.company_observed_name", errors)
        for optional_field in ("company_alias_ref", "role_title", "date_range"):
            if optional_field in duty and duty.get(optional_field) is not None:
                _require_non_empty_string(duty.get(optional_field), f"{path}.{optional_field}", errors)
        state_value = duty.get("duty_state")
        _require_enum(state_value, f"{path}.duty_state", _VALUE_STATES, errors)
        duty_text = duty.get("duty_text")
        if state_value == "observed_value" and not _is_non_empty_string(duty_text):
            errors.add(f"{path}.duty_text", "missing_conditional_field", "observed duty requires text")
        if state_value in {"not_observed", "not_available", "redacted"} and duty_text is not None:
            errors.add(f"{path}.duty_text", "state_value_mismatch", "unobserved duty text must be absent")
        _validate_source_segment_indexes(duty.get("source_segment_indexes"), f"{path}.source_segment_indexes", errors)


def _validate_company_aliases(value: object, errors: _Collector) -> None:
    aliases = _object_sequence(value)
    if aliases is None:
        if value is not None:
            errors.add("company_aliases", "invalid_array", "company_aliases must be an array")
        return
    for index, alias in enumerate(aliases):
        path = f"company_aliases[{index}]"
        if not isinstance(alias, Mapping):
            errors.add(path, "invalid_object", "company alias must be an object")
            continue
        _require_non_empty_string(alias.get("alias_text"), f"{path}.alias_text", errors)
        if "canonical_company_ref" in alias and alias.get("canonical_company_ref") is not None:
            _require_non_empty_string(
                alias.get("canonical_company_ref"), f"{path}.canonical_company_ref", errors
            )
        _require_enum(alias.get("alias_basis"), f"{path}.alias_basis", _ALIAS_BASES, errors)
        _validate_source_segment_indexes(alias.get("source_segment_indexes"), f"{path}.source_segment_indexes", errors)


def _validate_readback(manifest: Mapping[object, object], errors: _Collector) -> None:
    status = manifest.get("readback_status")
    _require_enum(status, "readback_status", _READBACK_STATUSES, errors)
    if status in {"matched", "mismatch", "blocked"}:
        _require_rfc3339(manifest.get("readback_at"), "readback_at", errors)
    if status in {"mismatch", "blocked"} and not _is_non_empty_string(
        manifest.get("readback_failure_reason")
    ):
        errors.add(
            "readback_failure_reason",
            "missing_conditional_field",
            "failed readback requires a reason",
        )


def _require_enum(value: object, path: str, allowed: frozenset[str], errors: _Collector) -> None:
    if not isinstance(value, str) or value not in allowed:
        errors.add(path, "invalid_enum", "value is outside the allowed set")


def _require_non_empty_string(value: object, path: str, errors: _Collector) -> None:
    if not _is_non_empty_string(value):
        errors.add(path, "invalid_string", "value must be a non-empty string")


def _require_integer(value: object, path: str, errors: _Collector) -> None:
    if not _is_int(value) or value < 0:
        errors.add(path, "invalid_integer", "value must be an integer greater than or equal to zero")


def _require_sha256(value: object, path: str, errors: _Collector) -> None:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        errors.add(path, "invalid_sha256", "value must be a lowercase sha256 hex string")


def _require_url(value: object, path: str, errors: _Collector) -> None:
    if not isinstance(value, str):
        errors.add(path, "invalid_url", "value must be an http or https URL")
        return
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        errors.add(path, "invalid_url", "value must be an http or https URL")


def _require_rfc3339(value: object, path: str, errors: _Collector) -> None:
    if not isinstance(value, str):
        errors.add(path, "invalid_timestamp", "value must be an RFC3339 timestamp")
        return
    try:
        normalized = value.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        errors.add(path, "invalid_timestamp", "value must be an RFC3339 timestamp")
        return
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        errors.add(path, "invalid_timestamp", "timestamp must include a timezone")


def _validate_source_segment_indexes(value: object, path: str, errors: _Collector) -> None:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        errors.add(path, "invalid_array", "source_segment_indexes must be a non-empty array")
        return
    if not value:
        errors.add(path, "invalid_array", "source_segment_indexes must be a non-empty array")
        return
    for index, item in enumerate(value):
        _require_integer(item, f"{path}[{index}]", errors)


def _object_sequence(value: object) -> Sequence[object] | None:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return None
    return value


def _is_non_empty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value)


def _is_int(value: object) -> TypeGuard[int]:
    return type(value) is int
