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


class TestCompanyIsolation:
    """반례 C — 다른 회사 스냅샷에 Codeit 값이 단 한 건도 섞이면 안 된다."""

    WRTN = {
        "source": "https://wrtn.career.greetinghr.com",
        "company_key": "wrtn",
        "company": "뤼튼테크놀로지스",
        "platform": "wrtn_careers",
        "snapshot_date": "2026-09-28",
        "positions": [
            {"posting_id": "abc123", "title": "백엔드 엔지니어", "group": "Tech",
             "job": "소프트웨어 엔지니어링", "exp": "경력 (3~10년)",
             "etype": "정규직", "status": "상시 채용"},
        ],
    }

    def test_no_codeit_value_leaks_into_another_company(self):
        rows = ingest_positions.build_rows(self.WRTN)
        blob = json.dumps(rows, ensure_ascii=False)
        assert "codeit" not in blob.lower()
        assert "코드잇" not in blob
        assert rows[0]["company_norm"] == "wrtn"
        assert rows[0]["platform"] == "wrtn_careers"
        assert rows[0]["source_file"].startswith("wrtnsearch/")

    def test_unknown_detail_url_is_left_empty_not_invented(self):
        # 레지스트리에 wrtn 의 detail_url_template 이 없다 — 지어내면 안 된다.
        rows = ingest_positions.build_rows(self.WRTN)
        assert rows[0]["url"] is None

    def test_absent_location_is_not_defaulted_to_seoul(self):
        rows = ingest_positions.build_rows(self.WRTN)
        assert rows[0]["location"] is None

    def test_unknown_company_key_fails_loudly(self):
        with pytest.raises(KeyError, match="unknown company_key"):
            ingest_positions.build_rows({**self.WRTN, "company_key": "nosuchco"})

    def test_codeit_snapshot_still_gets_its_real_values(self):
        rows = ingest_positions.build_rows(SNAPSHOT)
        assert rows[0]["company_norm"] == "codeit"
        assert rows[0]["location"] == "서울"
        assert rows[0]["url"].startswith("https://careers.codeit.com/c/")


class TestWriteBeforeDelete:
    """운영 DB다 — PostgREST 에 트랜잭션이 없으므로 순서가 유일한 안전장치다."""

    def _run(self, monkeypatch, tmp_path, insert_fails=False):
        calls = []

        def fake_select(table, query):
            return []

        def fake_delete(table, query):
            calls.append(("delete", table, dict(query)))
            return []

        def fake_insert(table, rows, **kwargs):
            calls.append(("insert", table, len(rows)))
            if insert_fails and table == ingest_positions.POSITIONS_TABLE:
                raise supabase_io.SupabaseError("boom")
            return len(rows)

        monkeypatch.setattr(ingest_positions, "select", fake_select)
        monkeypatch.setattr(ingest_positions, "delete", fake_delete)
        monkeypatch.setattr(ingest_positions, "insert", fake_insert)
        path = tmp_path / "snap.json"
        path.write_text(json.dumps(SNAPSHOT, ensure_ascii=False), encoding="utf-8")
        return calls, path

    def test_nothing_is_deleted_before_the_insert_succeeds(self, monkeypatch, tmp_path):
        calls, path = self._run(monkeypatch, tmp_path)
        ingest_positions.main([str(path)])
        kinds = [c[0] for c in calls]
        assert kinds[0] == "insert", f"first call must be an insert, got {kinds}"
        first_delete = kinds.index("delete")
        assert kinds[:first_delete].count("insert") >= 1

    def test_a_failing_insert_deletes_nothing(self, monkeypatch, tmp_path):
        calls, path = self._run(monkeypatch, tmp_path, insert_fails=True)
        with pytest.raises(supabase_io.SupabaseError):
            ingest_positions.main([str(path)])
        assert not [c for c in calls if c[0] == "delete"], "실패한 실행이 기존 행을 지웠다"

    def test_each_run_gets_its_own_source_file(self):
        a = ingest_positions.build_rows({**SNAPSHOT, "run_id": "A"})[0]["source_file"]
        b = ingest_positions.build_rows({**SNAPSHOT, "run_id": "B"})[0]["source_file"]
        assert a != b
        prefix = ingest_positions.source_prefix_for(SNAPSHOT)
        assert a.startswith(prefix) and b.startswith(prefix)

    def test_dry_run_writes_nothing(self, monkeypatch, tmp_path):
        def explode(*args, **kwargs):
            raise AssertionError("--dry-run must not touch Supabase")

        for name in ("select", "delete", "insert"):
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

    def test_retry_re_reads_the_max_instead_of_reusing_the_clashing_id(self, monkeypatch):
        # next_id 를 상수로 고정하면 "재조회로 id 가 바뀌는지" 를 검증하지 못한다.
        attempts = {"n": 0}
        allocations = iter([5, 11])

        def fake_request(method, path, *, payload=None, prefer=None):
            attempts["n"] += 1
            if attempts["n"] == 1:
                raise supabase_io.SupabaseError(
                    '{"code":"23505","message":"violates unique constraint \\"x_pkey\\""}'
                )
            return payload

        monkeypatch.setattr(supabase_io, "_request", fake_request)
        monkeypatch.setattr(supabase_io, "next_id", lambda *a, **k: next(allocations))
        rows = [{"a": 1}, {"a": 2}]
        assert supabase_io.insert("t", rows, assign_ids="id") == 2
        assert attempts["n"] == 2
        assert [r["id"] for r in rows] == [11, 12], "재시도가 같은 id 를 다시 썼다"

    def test_a_natural_key_conflict_is_not_retried(self, monkeypatch):
        attempts = {"n": 0}

        def fake_request(method, path, *, payload=None, prefer=None):
            attempts["n"] += 1
            raise supabase_io.SupabaseError(
                '{"code":"23505","message":"violates unique constraint \\"uq_jmp\\""}'
            )

        monkeypatch.setattr(supabase_io, "_request", fake_request)
        monkeypatch.setattr(supabase_io, "next_id", lambda *a, **k: 5)
        with pytest.raises(supabase_io.SupabaseError):
            supabase_io.insert("t", [{"a": 1}], assign_ids="id")
        assert attempts["n"] == 1, "자연 키 충돌을 재시도했다"
