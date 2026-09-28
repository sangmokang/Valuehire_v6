"""Minimal Supabase PostgREST transport for the codeitsearch pipeline.

Mirrors ``tools/invoice/storage_remote.py``: stdlib only, service-role key from the
environment, and every failure raised rather than swallowed.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

__all__ = ("SupabaseError", "credentials", "delete", "insert", "next_id", "select")


class SupabaseError(Exception):
    """Raised when Supabase cannot prove the requested operation succeeded."""


def credentials() -> tuple[str, str]:
    url = (
        os.environ.get("SUPABASE_URL")
        or os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
        or ""
    ).rstrip("/")
    key = (
        os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        or os.environ.get("SUPABASE_SECRET_KEY")
        or ""
    )
    if not url or not key:
        raise SupabaseError(
            "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set "
            "(NEXT_PUBLIC_SUPABASE_URL / SUPABASE_SECRET_KEY also accepted)"
        )
    return url, key


def _request(
    method: str,
    path: str,
    *,
    payload: Any | None = None,
    prefer: str | None = None,
) -> Any:
    url, key = credentials()
    headers = {"apikey": key, "Authorization": f"Bearer {key}"}
    data = None
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if prefer:
        headers["Prefer"] = prefer
    request = urllib.request.Request(
        f"{url}/rest/v1/{path}", data=data, method=method, headers=headers
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read()
    except urllib.error.HTTPError as error:
        detail = error.read().decode(errors="replace")[:600]
        raise SupabaseError(f"Supabase HTTP {error.code} on {method} {path}: {detail}") from error
    except urllib.error.URLError as error:
        raise SupabaseError(f"Supabase network error: {error.reason}") from error
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError as error:
        raise SupabaseError(f"Supabase returned invalid JSON for {method} {path}") from error


def select(table: str, query: list[tuple[str, str]]) -> list[dict[str, Any]]:
    rows = _request("GET", f"{table}?{urllib.parse.urlencode(query)}")
    return rows if isinstance(rows, list) else []


def delete(table: str, query: list[tuple[str, str]]) -> list[dict[str, Any]]:
    """Delete matching rows. ``query`` must be non-empty — an unfiltered delete is refused."""
    if not query:
        raise SupabaseError("refusing an unfiltered delete")
    rows = _request(
        "DELETE", f"{table}?{urllib.parse.urlencode(query)}", prefer="return=representation"
    )
    return rows if isinstance(rows, list) else []


UNIQUE_VIOLATION = "23505"


def _is_pk_conflict(error: Exception, column: str) -> bool:
    """True only for a primary-key clash on the column we allocate ourselves.

    jobmarket_positions also carries a natural unique key (uq_jmp). Retrying that one
    would just re-send the same rows four times and hide a real duplicate.
    """
    text = str(error)
    return UNIQUE_VIOLATION in text and ("_pkey" in text or f"Key ({column})=" in text)


def insert(
    table: str,
    rows: list[dict[str, Any]],
    *,
    chunk: int = 200,
    assign_ids: str | None = None,
    attempts: int = 4,
) -> int:
    """Insert rows in chunks, returning the number Supabase echoed back.

    ``assign_ids`` names a primary-key column this client must fill itself, for tables
    whose identity sequence lags an earlier bulk import. That allocation reads
    ``max(id)+1``, so two concurrent runs can pick the same block; the insert then fails
    with ``23505``. Rather than corrupt or half-write, re-read the max and retry the
    whole batch — the ids are ours to choose, so a retry is safe and idempotent.
    """
    written = 0
    for start in range(0, len(rows), chunk):
        batch = rows[start : start + chunk]
        for attempt in range(1, attempts + 1):
            if assign_ids:
                base = next_id(table, column=assign_ids)
                for offset, row in enumerate(batch):
                    row[assign_ids] = base + offset
            try:
                echoed = _request("POST", table, payload=batch, prefer="return=representation")
            except SupabaseError as error:
                if assign_ids and attempt < attempts and _is_pk_conflict(error, assign_ids):
                    continue
                raise
            if not isinstance(echoed, list) or len(echoed) != len(batch):
                raise SupabaseError(
                    f"{table}: expected {len(batch)} rows echoed, got "
                    f"{len(echoed) if isinstance(echoed, list) else type(echoed).__name__}"
                )
            written += len(echoed)
            break
    return written


def next_id(table: str, *, column: str = "id") -> int:
    """Return max(column)+1, for tables whose identity sequence lags a bulk import."""
    rows = select(table, [("select", column), ("order", f"{column}.desc"), ("limit", "1")])
    return int(rows[0][column]) + 1 if rows else 1
