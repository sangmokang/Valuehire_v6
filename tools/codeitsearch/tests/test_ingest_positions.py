import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import ingest_positions  # noqa: E402
import supabase_io  # noqa: E402

SNAPSHOT = json.loads(
    (ROOT / "data" / "codeit_positions_2026-09-28.json").read_text(encoding="utf-8")
)


class TestBuildRows:
    def test_one_row_per_position(self):
        rows = ingest_positions.build_rows(SNAPSHOT)
        assert len(rows) == len(SNAPSHOT["positions"])

    def test_required_columns_are_present(self):
        row = ingest_positions.build_rows(SNAPSHOT)[0]
        for column in (
            "snapshot_date", "platform", "company", "source_file",
            "core_keywords_json", "key_phrases_json", "preferred_keywords_json",
        ):
            assert row[column] is not None, column

    def test_natural_unique_key_is_unique_across_the_snapshot(self):
        # uq_jmp = (snapshot_date, platform, segment, title, company, url, source_file).
        # 두 행이 같은 키를 가지면 적재가 23505 로 깨진다.
        rows = ingest_positions.build_rows(SNAPSHOT)
        keys = [
            (r["snapshot_date"], r["platform"], r["segment"], r["title"],
             r["company"], r["url"], r["source_file"])
            for r in rows
        ]
        assert len(keys) == len(set(keys))

    def test_snapshot_row_counts_match_the_rows(self):
        rows = ingest_positions.build_rows(SNAPSHOT)
        summary = ingest_positions.build_snapshot_row(SNAPSHOT, rows)
        assert summary["total_positions"] == len(rows)
        assert sum(summary["per_segment_json"].values()) == len(rows)


class TestDestructiveWriteSafety:
    """운영 DB다 — insert 가 실패해도 이전 스냅샷이 사라지면 안 된다."""

    def test_failed_insert_restores_the_backup(self, monkeypatch, tmp_path, capsys):
        previous = [{"id": 1, "title": "old"}, {"id": 2, "title": "older"}]
        calls = {"deleted": 0, "restored": None}

        def fake_select(table, query):
            return previous if any(k == "select" and v == "*" for k, v in query) else []

        def fake_delete(table, query):
            calls["deleted"] += 1
            return previous

        def fake_insert(table, rows, **kwargs):
            if rows is previous:
                calls["restored"] = list(rows)
                return len(rows)
            raise supabase_io.SupabaseError("Supabase HTTP 500 boom")

        monkeypatch.setattr(ingest_positions, "select", fake_select)
        monkeypatch.setattr(ingest_positions, "delete", fake_delete)
        monkeypatch.setattr(ingest_positions, "insert", fake_insert)
        monkeypatch.setattr(ingest_positions, "next_id", lambda *a, **k: 1000)

        path = tmp_path / "snap.json"
        path.write_text(json.dumps(SNAPSHOT, ensure_ascii=False), encoding="utf-8")

        with pytest.raises(supabase_io.SupabaseError):
            ingest_positions.main([str(path)])

        assert calls["deleted"] == 1
        assert calls["restored"] == previous
        assert "restored 2 previous rows" in capsys.readouterr().err

    def test_dry_run_writes_nothing(self, monkeypatch, tmp_path):
        def explode(*args, **kwargs):
            raise AssertionError("--dry-run must not touch Supabase")

        for name in ("select", "delete", "insert", "next_id"):
            monkeypatch.setattr(ingest_positions, name, explode)
        path = tmp_path / "snap.json"
        path.write_text(json.dumps(SNAPSHOT, ensure_ascii=False), encoding="utf-8")
        assert ingest_positions.main([str(path), "--dry-run"]) == 0


class TestIdRetry:
    def test_pk_conflict_is_retried_but_a_natural_key_conflict_is_not(self, monkeypatch):
        pk_error = supabase_io.SupabaseError(
            'HTTP 409: {"code":"23505","message":"duplicate key value violates unique '
            'constraint \\"jobmarket_positions_pkey\\""}'
        )
        natural_error = supabase_io.SupabaseError(
            'HTTP 409: {"code":"23505","message":"duplicate key value violates unique '
            'constraint \\"uq_jmp\\""}'
        )
        assert supabase_io._is_pk_conflict(pk_error, "id") is True
        assert supabase_io._is_pk_conflict(natural_error, "id") is False

    def test_insert_retries_once_then_succeeds(self, monkeypatch):
        attempts = {"n": 0}

        def fake_request(method, path, *, payload=None, prefer=None):
            attempts["n"] += 1
            if attempts["n"] == 1:
                raise supabase_io.SupabaseError(
                    '{"code":"23505","message":"violates unique constraint \\"x_pkey\\""}'
                )
            return payload

        monkeypatch.setattr(supabase_io, "_request", fake_request)
        monkeypatch.setattr(supabase_io, "next_id", lambda *a, **k: 5)
        rows = [{"a": 1}, {"a": 2}]
        assert supabase_io.insert("t", rows, assign_ids="id") == 2
        assert attempts["n"] == 2
        assert [r["id"] for r in rows] == [5, 6]
