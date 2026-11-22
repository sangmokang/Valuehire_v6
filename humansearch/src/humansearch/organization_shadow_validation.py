"""Strict validation for untrusted Jev response payloads."""

import contextlib
import math
from collections.abc import Mapping
from typing import Any

_SUM_TOLERANCE = 1e-6  # probabilities sum to one within this absolute tolerance
_REPORTED_HALF_UNIT = 0.005  # Jev answers carry two decimals


def validate_response(
    raw: Mapping[str, object],
    *,
    questions: Mapping[str, Mapping[str, Any]],
    model_version: str,
) -> Mapping[str, Mapping[str, object]]:
    root = _mapping(raw, "response")
    _exact_keys(root, {"model", "answers", "usage"}, "response")
    if root["model"] != model_version:
        raise ValueError("response model does not match pinned model")
    answers = _mapping(root["answers"], "answers")
    _exact_keys(answers, set(questions), "answers")
    usage = _mapping(root["usage"], "usage")
    _exact_keys(usage, {"input_tokens", "output_tokens"}, "usage")
    for name in usage:
        _nonnegative_int(usage[name], f"usage.{name}")
    validated: dict[str, Mapping[str, object]] = {}
    for name, question in questions.items():
        answer = _mapping(answers[name], f"answers.{name}")
        primitive = question["type"]
        if answer.get("type") != primitive:
            raise ValueError("answer primitive does not match question")
        if primitive == "noul":
            _exact_keys(answer, {"type", "noul"}, f"answers.{name}")
            _probability(answer["noul"], f"answers.{name}.noul")
        elif primitive == "choice":
            _validate_choice(name, answer, question)
        else:
            _validate_score(name, answer, question)
        validated[name] = dict(answer)
    return validated


def _validate_choice(name: str, answer: Mapping[str, object], question: Mapping[str, Any]) -> None:
    _exact_keys(answer, {"type", "choice", "probabilities", "confidence"}, f"answers.{name}")
    criteria = _mapping(question["criteria"], f"questions.{name}.criteria")
    choice = _text(answer["choice"], f"answers.{name}.choice")
    if choice not in criteria:
        raise ValueError("choice is not in configured criteria")
    _validate_probabilities(answer["probabilities"], set(criteria), f"answers.{name}")
    _probability(answer["confidence"], f"answers.{name}.confidence")


def _validate_score(name: str, answer: Mapping[str, object], question: Mapping[str, Any]) -> None:
    _exact_keys(
        answer,
        {"type", "score", "legend", "probabilities", "confidence"},
        f"answers.{name}",
    )
    criteria = question["criteria"]
    if not isinstance(criteria, list):
        raise TypeError("score criteria must be a list")
    score = _number(answer["score"], f"answers.{name}.score")
    if score < 0 or score > len(criteria) - 1:
        raise ValueError("score is outside configured range")
    expected = {str(index): value for index, value in enumerate(criteria)}
    if _mapping(answer["legend"], f"answers.{name}.legend") != expected:
        raise ValueError("score legend differs from configured criteria")
    probabilities = _validate_probabilities(
        answer["probabilities"], set(expected), f"answers.{name}.probabilities"
    )
    # typesafe-sdk ScoreAnswer.score is "the probability-weighted average of the rubric levels".
    # Jev reports the score and each probability rounded to two decimals on their own (live call,
    # 2026-10-12), so the score must lie in the band that rounding can explain.
    low, high = _feasible_mean_band(probabilities)
    slack = _REPORTED_HALF_UNIT + _SUM_TOLERANCE
    if score < low - slack or score > high + slack:
        raise ValueError("score differs from its probability-weighted average")
    _probability(answer["confidence"], f"answers.{name}.confidence")


def _feasible_mean_band(reported: Mapping[str, float]) -> tuple[float, float]:
    """Lowest and highest mean of true probabilities within half a unit of each reported value."""

    levels = sorted((int(level), value) for level, value in reported.items())
    floor = [max(0.0, value - _REPORTED_HALF_UNIT) for _, value in levels]
    room = [value + _REPORTED_HALF_UNIT - low for (_, value), low in zip(levels, floor, strict=True)]
    base = sum(level * low for (level, _), low in zip(levels, floor, strict=True))

    def extreme(order: list[int]) -> float:
        remaining, mean = max(0.0, 1.0 - sum(floor)), base
        for index in order:
            added = min(remaining, room[index])
            mean, remaining = mean + levels[index][0] * added, remaining - added
        return mean

    indexes = list(range(len(levels)))
    return extreme(indexes), extreme(indexes[::-1])


def _validate_probabilities(raw: object, expected: set[str], field: str) -> Mapping[str, float]:
    probabilities = _mapping(raw, field)
    _exact_keys(probabilities, expected, field)
    values = {key: _probability(value, f"{field}.{key}") for key, value in probabilities.items()}
    if not math.isclose(sum(values.values()), 1.0, abs_tol=_SUM_TOLERANCE):
        raise ValueError("probabilities must sum to one")
    return values


def _mapping(value: object, field: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping) or any(not isinstance(key, str) for key in value):
        raise ValueError(f"{field} must be an object with string keys")
    return value


def _exact_keys(value: Mapping[str, object], expected: set[str], field: str) -> None:
    if set(value) != expected:
        raise ValueError(f"{field} has missing or unknown fields")


def _text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a nonempty string")
    return value


def _number(value: object, field: str) -> float:
    number = math.nan
    if not isinstance(value, bool) and isinstance(value, int | float):
        with contextlib.suppress(OverflowError):  # JSON ints can exceed float range
            number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{field} must be a finite number")
    return number


def _probability(value: object, field: str) -> float:
    result = _number(value, field)
    if result < 0 or result > 1:
        raise ValueError(f"{field} is outside its allowed range")
    return result


def _nonnegative_int(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{field} must be a non-negative integer")
    return value
