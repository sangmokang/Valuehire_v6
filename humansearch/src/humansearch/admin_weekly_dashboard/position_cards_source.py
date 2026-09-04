"""Reads `public.pipeline_position_cards` from Supabase via PostgREST.

The only fields this module ever requests, parses, or returns are the four
already approved in `source-contract-v1.json` (id, company_name,
imported_at, last_updated_at) — see `EXPECTED_SUPABASE_SOURCES["position_cards"]`
in source_contract.py, which this module treats as the single source of
truth for the select clause.

The three counter-AC failure modes (network error, HTTP/schema error, a
row shaped outside the contract) each return through a distinct branch
before any row is constructed, so none of them can be quietly reported as
"PASS with an empty list" the way a broad `except: return []` would.
A genuinely empty but well-formed response is the only way to reach a PASS
with zero rows, and it does so via the same row-validation path as a
non-empty response — there is no separate "empty" short-circuit to drift
out of sync with it.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass

from .contracts import MetricStatus, SourceFailureReason, SourceState
from .source_contract import EXPECTED_SUPABASE_SOURCES

_TABLE, _FIELDS, _ = EXPECTED_SUPABASE_SOURCES["position_cards"]
_SCHEMA, _, _TABLE_NAME = _TABLE.partition(".")

HttpGet = Callable[[str, float, str], "tuple[int, bytes]"]


@dataclass(frozen=True, init=False)
class PositionCardRow:
    """One position_cards row restricted to the contract's select_fields."""

    id: str
    company_name: str
    imported_at: str
    last_updated_at: str

    def __init__(
        self,
        *,
        id: str,
        company_name: str,
        imported_at: str,
        last_updated_at: str,
    ) -> None:
        for name, value in (
            ("id", id),
            ("company_name", company_name),
            ("imported_at", imported_at),
            ("last_updated_at", last_updated_at),
        ):
            if not isinstance(value, str) or not value:
                raise TypeError(f"{name} must be a non-empty string")
        object.__setattr__(self, "id", id)
        object.__setattr__(self, "company_name", company_name)
        object.__setattr__(self, "imported_at", imported_at)
        object.__setattr__(self, "last_updated_at", last_updated_at)


@dataclass(frozen=True, init=False)
class PositionCardsResult:
    """A truthful PASS/FAIL/NOT_RUN classification plus the rows it verified."""

    state: SourceState
    rows: tuple[PositionCardRow, ...]

    def __init__(self, *, state: SourceState, rows: tuple[PositionCardRow, ...]) -> None:
        if not isinstance(state, SourceState):
            raise TypeError("state must be a SourceState")
        if not isinstance(rows, tuple) or not all(
            isinstance(row, PositionCardRow) for row in rows
        ):
            raise TypeError("rows must be a tuple of PositionCardRow")
        if state.status is not MetricStatus.PASS and rows:
            raise ValueError("a non-PASS result must not carry rows")
        object.__setattr__(self, "state", state)
        object.__setattr__(self, "rows", rows)


def _fail(reason: SourceFailureReason) -> PositionCardsResult:
    return PositionCardsResult(state=SourceState(status=MetricStatus.FAIL, reason=reason), rows=())


def fetch_position_cards(
    *,
    base_url: str,
    api_key: str,
    http_get: HttpGet | None = None,
    timeout: float = 10.0,
) -> PositionCardsResult:
    """Query position_cards through PostgREST and classify the outcome.

    `http_get` is injectable so callers (and this module's own tests) never
    need a live network to exercise the network-error, schema-mismatch, and
    empty-table branches — it defaults to a real HTTP call via `urllib`.
    """

    if not isinstance(base_url, str) or not base_url.strip():
        raise ValueError("base_url must be a non-empty string")
    if not isinstance(api_key, str) or not api_key.strip():
        raise ValueError("api_key must be a non-empty string")

    getter = http_get if http_get is not None else _urllib_get
    url = _build_url(base_url)

    try:
        status_code, body = getter(url, timeout, api_key)
    except TimeoutError:
        return _fail(SourceFailureReason.SOURCE_TIMEOUT)
    except urllib.error.URLError as error:
        # urlopen wraps a real socket timeout as URLError(reason=TimeoutError(...)),
        # never as a bare TimeoutError — the bare-exception branch above only ever
        # fires for an injected test double, not the real network path.
        if isinstance(error.reason, TimeoutError):
            return _fail(SourceFailureReason.SOURCE_TIMEOUT)
        return _fail(SourceFailureReason.SOURCE_UNAVAILABLE)
    except OSError:
        return _fail(SourceFailureReason.SOURCE_UNAVAILABLE)

    if status_code == 401 or status_code == 403:
        return _fail(SourceFailureReason.PERMISSION_DENIED)
    if status_code == 429 or 500 <= status_code <= 599:
        return _fail(SourceFailureReason.SOURCE_UNAVAILABLE)
    if status_code != 200:
        return _fail(SourceFailureReason.CONTRACT_MISMATCH)

    try:
        payload = json.loads(body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return _fail(SourceFailureReason.CONTRACT_MISMATCH)

    if not isinstance(payload, list):
        return _fail(SourceFailureReason.CONTRACT_MISMATCH)

    expected_keys = set(_FIELDS)
    rows: list[PositionCardRow] = []
    for item in payload:
        if not isinstance(item, dict) or set(item) != expected_keys:
            return _fail(SourceFailureReason.CONTRACT_MISMATCH)
        try:
            rows.append(
                PositionCardRow(
                    id=_as_str(item["id"]),
                    company_name=_as_str(item["company_name"]),
                    imported_at=_as_str(item["imported_at"]),
                    last_updated_at=_as_str(item["last_updated_at"]),
                )
            )
        except TypeError:
            return _fail(SourceFailureReason.CONTRACT_MISMATCH)

    return PositionCardsResult(state=SourceState(status=MetricStatus.PASS), rows=tuple(rows))


def _as_str(value: object) -> str:
    if not isinstance(value, str):
        raise TypeError("field value must be a string")
    return value


def _build_url(base_url: str) -> str:
    query = urllib.parse.urlencode({"select": ",".join(_FIELDS)})
    return f"{base_url.rstrip('/')}/rest/v1/{_TABLE_NAME}?{query}"


def _urllib_get(url: str, timeout: float, api_key: str) -> tuple[int, bytes]:
    request = urllib.request.Request(
        url,
        headers={"apikey": api_key, "Authorization": f"Bearer {api_key}"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as error:
        return error.code, error.read()
