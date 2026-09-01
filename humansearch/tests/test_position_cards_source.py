"""Acceptance tests for the position_cards Supabase read (Phase E, issue #55).

Every scenario injects a fake ``http_get`` so the suite never touches the
network — the counter-AC is that a network error, a schema drift, and a
genuinely empty table must land in three *different* code paths, never
collapsed into the same "PASS + empty list" outcome.
"""

from __future__ import annotations

import json

import pytest

from humansearch.admin_weekly_dashboard.contracts import MetricStatus, SourceFailureReason
from humansearch.admin_weekly_dashboard.position_cards_source import (
    HttpGet,
    PositionCardRow,
    PositionCardsResult,
    fetch_position_cards,
)

VALID_ROW = {
    "id": "pc-1",
    "company_name": "Acme",
    "imported_at": "2026-08-30T00:00:00+09:00",
    "last_updated_at": "2026-08-31T00:00:00+09:00",
}


def _fixture_api_key() -> str:
    """A fixture value shaped like a Supabase key but never a real credential."""

    return "not-a-real-supabase-service-role-key"


def _ok_get(body: object, *, status: int = 200) -> HttpGet:
    encoded = json.dumps(body).encode("utf-8")
    expected_key = _fixture_api_key()

    def _http_get(url: str, timeout: float, api_key: str) -> tuple[int, bytes]:
        assert "select=id%2Ccompany_name%2Cimported_at%2Clast_updated_at" in url
        assert api_key == expected_key
        return status, encoded

    return _http_get


def test_fetch_position_cards_returns_pass_with_only_contract_fields() -> None:
    result = fetch_position_cards(
        base_url="https://example.supabase.co",
        api_key=_fixture_api_key(),
        http_get=_ok_get([VALID_ROW]),
    )

    assert isinstance(result, PositionCardsResult)
    assert result.state.status is MetricStatus.PASS
    assert result.state.reason is None
    assert result.rows == (
        PositionCardRow(
            id="pc-1",
            company_name="Acme",
            imported_at="2026-08-30T00:00:00+09:00",
            last_updated_at="2026-08-31T00:00:00+09:00",
        ),
    )


def test_fetch_position_cards_never_carries_fields_outside_the_contract() -> None:
    poisoned_row = dict(VALID_ROW, raw_clickup_payload="secret", jd_text="x", tags=["a"])

    result = fetch_position_cards(
        base_url="https://example.supabase.co",
        api_key=_fixture_api_key(),
        http_get=_ok_get([poisoned_row]),
    )

    assert result.state.status is MetricStatus.FAIL
    assert result.state.reason is SourceFailureReason.CONTRACT_MISMATCH
    assert result.rows == ()


def test_fetch_position_cards_rejects_a_row_missing_a_contract_field() -> None:
    incomplete_row = {k: v for k, v in VALID_ROW.items() if k != "last_updated_at"}

    result = fetch_position_cards(
        base_url="https://example.supabase.co",
        api_key=_fixture_api_key(),
        http_get=_ok_get([incomplete_row]),
    )

    assert result.state.status is MetricStatus.FAIL
    assert result.state.reason is SourceFailureReason.CONTRACT_MISMATCH
    assert result.rows == ()


def test_fetch_position_cards_network_error_is_fail_not_pass_with_empty_rows() -> None:
    def _raising_get(url: str, timeout: float, api_key: str) -> tuple[int, bytes]:
        raise ConnectionError("connection refused")

    result = fetch_position_cards(
        base_url="https://example.supabase.co",
        api_key=_fixture_api_key(),
        http_get=_raising_get,
    )

    assert result.state.status is MetricStatus.FAIL
    assert result.state.reason is SourceFailureReason.SOURCE_UNAVAILABLE
    assert result.rows == ()


def test_fetch_position_cards_timeout_is_fail_not_pass_with_empty_rows() -> None:
    def _timeout_get(url: str, timeout: float, api_key: str) -> tuple[int, bytes]:
        raise TimeoutError("timed out")

    result = fetch_position_cards(
        base_url="https://example.supabase.co",
        api_key=_fixture_api_key(),
        http_get=_timeout_get,
    )

    assert result.state.status is MetricStatus.FAIL
    assert result.state.reason is SourceFailureReason.SOURCE_TIMEOUT
    assert result.rows == ()


def test_fetch_position_cards_http_error_status_is_fail() -> None:
    result = fetch_position_cards(
        base_url="https://example.supabase.co",
        api_key=_fixture_api_key(),
        http_get=_ok_get({"message": "column jd_text does not exist"}, status=400),
    )

    assert result.state.status is MetricStatus.FAIL
    assert result.state.reason is SourceFailureReason.CONTRACT_MISMATCH
    assert result.rows == ()


def test_fetch_position_cards_non_list_payload_is_fail() -> None:
    result = fetch_position_cards(
        base_url="https://example.supabase.co",
        api_key=_fixture_api_key(),
        http_get=_ok_get({"unexpected": "object"}),
    )

    assert result.state.status is MetricStatus.FAIL
    assert result.state.reason is SourceFailureReason.CONTRACT_MISMATCH
    assert result.rows == ()


def test_fetch_position_cards_genuinely_empty_table_is_pass_with_empty_rows() -> None:
    """A real empty table is a truthful PASS — distinct from every FAIL path above."""

    result = fetch_position_cards(
        base_url="https://example.supabase.co",
        api_key=_fixture_api_key(),
        http_get=_ok_get([]),
    )

    assert result.state.status is MetricStatus.PASS
    assert result.state.reason is None
    assert result.rows == ()


def test_fetch_position_cards_rejects_blank_base_url() -> None:
    with pytest.raises(ValueError):
        fetch_position_cards(base_url="  ", api_key=_fixture_api_key(), http_get=_ok_get([]))


def test_fetch_position_cards_rejects_blank_api_key() -> None:
    with pytest.raises(ValueError):
        fetch_position_cards(
            base_url="https://example.supabase.co", api_key="", http_get=_ok_get([])
        )


def test_position_cards_result_rejects_rows_on_a_non_pass_state() -> None:
    from humansearch.admin_weekly_dashboard.contracts import SourceState

    with pytest.raises(ValueError):
        PositionCardsResult(
            state=SourceState(
                status=MetricStatus.FAIL, reason=SourceFailureReason.SOURCE_UNAVAILABLE
            ),
            rows=(
                PositionCardRow(
                    id="pc-1",
                    company_name="Acme",
                    imported_at="2026-08-30T00:00:00+09:00",
                    last_updated_at="2026-08-31T00:00:00+09:00",
                ),
            ),
        )
