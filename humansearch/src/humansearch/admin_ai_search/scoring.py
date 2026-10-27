"""Deterministic four-axis AI Search candidate scoring."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from typing import cast

SCORE_CONTRACT_VERSION = "admin-ai-search-score/v2"
SCORE_COMPONENT_KEYS = (
    "education",
    "job_fit",
    "difficult_work",
    "job_description_logic",
)
EXPECTED_SCORE_WEIGHTS = {
    "education": 40,
    "job_fit": 40,
    "difficult_work": 10,
    "job_description_logic": 10,
}


type ScoreComponents = dict[str, int]


def load_score_contract(raw: object) -> tuple[str, dict[str, int]]:
    if not isinstance(raw, Mapping):
        raise TypeError("score_contract must be an object")
    version = raw.get("version")
    weights = raw.get("weights")
    if version != SCORE_CONTRACT_VERSION:
        raise ValueError("unsupported AI Search score contract")
    if weights != EXPECTED_SCORE_WEIGHTS:
        raise ValueError("AI Search score weights do not match the v2 contract")
    return version, cast(dict[str, int], dict(weights))


def calculate_candidate_score(components: Mapping[str, int], weights: Mapping[str, int]) -> int:
    _validate_components(components)
    _validate_weights(weights)
    numerator = sum(components[key] * weights[key] for key in SCORE_COMPONENT_KEYS)
    return (numerator + 50) // 100


def score_input_hash(version: str, components: Mapping[str, int]) -> str:
    if not isinstance(version, str) or not version.strip():
        raise ValueError("score contract version must be non-blank")
    _validate_components(components)
    payload = json.dumps(
        {"components": dict(components), "version": version},
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def validate_score_provenance(
    score: int | None,
    version: str | None,
    components: ScoreComponents | None,
    input_hash: str | None,
    contract_version: str,
    weights: Mapping[str, int],
) -> None:
    if score is None:
        return
    if version != contract_version:
        raise ValueError("candidate score contract version does not match evidence contract")
    if components is None or input_hash is None:
        raise ValueError("candidate score provenance is incomplete")
    if score != calculate_candidate_score(components, weights):
        raise ValueError("candidate score does not match deterministic calculation")
    if input_hash != score_input_hash(version, components):
        raise ValueError("candidate score input hash does not match components")


def _validate_components(components: Mapping[str, int]) -> None:
    if set(components) != set(SCORE_COMPONENT_KEYS):
        raise ValueError("score components do not match the v2 contract")
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 100
        for value in components.values()
    ):
        raise ValueError("score components must be integers from 0 to 100")


def _validate_weights(weights: Mapping[str, int]) -> None:
    if dict(weights) != EXPECTED_SCORE_WEIGHTS or sum(weights.values()) != 100:
        raise ValueError("score weights do not match the v2 contract")
