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
    """운영 DB다 — PostgREST 에 트랜잭션이 없으므로 순서가 유일한 안전장치다.

    ① insert → ② 검증 → ③ 요약 → ④ 이전 실행분 delete.
    """

    def _harness(self, monkeypatch, tmp_path, *, insert_fails=False,
                 verified_rows=None, snapshot_insert_fails=False, extra_rows=()):
        calls = []
        stale = f"{ingest_positions.source_prefix_for(SNAPSHOT)}#run-OLD"
        rows_in_db = [{"id": 1, "source_file": stale, "company_norm": "codeit"}, *extra_rows]

        def fake_select(table, query):
            fields = dict(query)
            if fields.get("select") == "posting_id":
                # 검증 조회
                n = len(SNAPSHOT["positions"]) if verified_rows is None else verified_rows
                return [{"posting_id": f"p{i}"} for i in range(n)]
            if table == ingest_positions.POSITIONS_TABLE:
                return rows_in_db
            return []

        def fake_delete(table, query):
            calls.append(("delete", table, dict(query)))
            return []

        def fake_insert(table, rows, **kwargs):
            calls.append(("insert", table, len(rows)))
            if insert_fails and table == ingest_positions.POSITIONS_TABLE:
                raise supabase_io.SupabaseError("boom")
            if snapshot_insert_fails and table == ingest_positions.SNAPSHOTS_TABLE:
                raise supabase_io.SupabaseError("snapshot boom")
            return len(rows)

        monkeypatch.setattr(ingest_positions, "select", fake_select)
        monkeypatch.setattr(ingest_positions, "delete", fake_delete)
        monkeypatch.setattr(ingest_positions, "insert", fake_insert)
        path = tmp_path / "snap.json"
        path.write_text(json.dumps(SNAPSHOT, ensure_ascii=False), encoding="utf-8")
        return calls, path

    def test_insert_comes_before_any_delete(self, monkeypatch, tmp_path):
        calls, path = self._harness(monkeypatch, tmp_path)
        assert ingest_positions.main([str(path)]) == 0
        kinds = [c[0] for c in calls]
        assert kinds[0] == "insert"
        assert "delete" in kinds
        assert kinds.index("insert") < kinds.index("delete")

    def test_a_failing_insert_deletes_nothing(self, monkeypatch, tmp_path):
        calls, path = self._harness(monkeypatch, tmp_path, insert_fails=True)
        with pytest.raises(supabase_io.SupabaseError):
            ingest_positions.main([str(path)])
        assert not [c for c in calls if c[0] == "delete"]

    def test_a_failed_verification_deletes_nothing(self, monkeypatch, tmp_path):
        # insert 응답은 성공했지만 되읽기가 모자란 경우 — 기존 행을 지우면 안 된다 (codex 3차).
        calls, path = self._harness(monkeypatch, tmp_path, verified_rows=3)
        assert ingest_positions.main([str(path)]) == 1
        assert not [c for c in calls if c[0] == "delete"], "검증 실패인데 기존 행을 지웠다"

    def test_snapshot_row_is_written_before_the_cleanup(self, monkeypatch, tmp_path):
        calls, path = self._harness(monkeypatch, tmp_path, snapshot_insert_fails=True)
        with pytest.raises(supabase_io.SupabaseError):
            ingest_positions.main([str(path)])
        assert not [c for c in calls if c[0] == "delete"], "요약 행 실패인데 정리를 진행했다"

    def test_another_company_with_the_same_prefix_is_not_deleted(self, monkeypatch, tmp_path):
        other = {"id": 99,
                 "source_file": f"{ingest_positions.source_prefix_for(SNAPSHOT)}#run-OTHER",
                 "company_norm": "someoneelse"}
        calls, path = self._harness(monkeypatch, tmp_path, extra_rows=(other,))
        assert ingest_positions.main([str(path)]) == 0
        deletes = [c for c in calls if c[0] == "delete"
                   and c[1] == ingest_positions.POSITIONS_TABLE]
        assert len(deletes) == 1
        assert deletes[0][2]["id"] == "in.(1)", deletes[0][2]

    def test_stale_selection_uses_ids_never_a_like_pattern(self, monkeypatch, tmp_path):
        calls, path = self._harness(monkeypatch, tmp_path)
        ingest_positions.main([str(path)])
        for _, table, query in [c for c in calls if c[0] == "delete"]:
            assert not any("like" in str(v) for v in query.values()), query

    def test_each_run_gets_its_own_source_file(self):
        a = ingest_positions.build_rows({**SNAPSHOT, "run_id": "A"})[0]["source_file"]
        b = ingest_positions.build_rows({**SNAPSHOT, "run_id": "B"})[0]["source_file"]
        assert a != b
        prefix = ingest_positions.source_prefix_for(SNAPSHOT)
        assert a.startswith(prefix) and b.startswith(prefix)

    def test_two_runs_in_the_same_second_get_different_source_files(self):
        a = ingest_positions.build_rows(dict(SNAPSHOT))[0]["source_file"]
        b = ingest_positions.build_rows(dict(SNAPSHOT))[0]["source_file"]
        assert a != b

    def test_empty_snapshot_fails_instead_of_indexing_row_zero(self, monkeypatch, tmp_path):
        def explode(*a, **k):
            raise AssertionError("must not touch Supabase for an empty snapshot")

        for name in ("select", "delete", "insert"):
            monkeypatch.setattr(ingest_positions, name, explode)
        path = tmp_path / "snap.json"
        path.write_text(json.dumps({**SNAPSHOT, "positions": []}, ensure_ascii=False),
                        encoding="utf-8")
        assert ingest_positions.main([str(path)]) == 1

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


class TestReview20260930:
    """2026-09-30 이어받기 검토(codex V1 지적, Claude 재현)."""

    WRTN = TestCompanyIsolation.WRTN

    @pytest.mark.parametrize(
        "override",
        [{"company_key": "codeit"},                 # 뤼튼 스냅샷에 codeit 키
         {"company": "코드잇"},                      # 회사명만 어긋남
         {"platform": "codeit_careers"}],           # 플랫폼만 어긋남
    )
    def test_snapshot_that_disagrees_with_the_registry_is_refused(self, override):
        # 어긋난 채로 통과하면 뤼튼 행에 https://careers.codeit.com/c/... 가 붙었다.
        with pytest.raises(ValueError):
            ingest_positions.build_rows({**self.WRTN, **override})

    def test_matching_snapshots_still_build(self):
        assert ingest_positions.build_rows(self.WRTN)
        assert ingest_positions.build_rows(SNAPSHOT)

    def test_only_rows_carrying_the_run_marker_are_stale(self, monkeypatch, tmp_path):
        # 접두사만 보면 '<prefix>-archive' 같은 같은 회사의 별도 출처까지 지웠다.
        archive = {"id": 3,
                   "source_file": f"{ingest_positions.source_prefix_for(SNAPSHOT)}-archive",
                   "company_norm": "codeit"}
        calls, path = TestWriteBeforeDelete()._harness(
            monkeypatch, tmp_path, extra_rows=(archive,))
        assert ingest_positions.main([str(path)]) == 0
        deletes = [c for c in calls if c[0] == "delete"
                   and c[1] == ingest_positions.POSITIONS_TABLE]
        assert [d[2]["id"] for d in deletes] == ["in.(1)"]

    def test_summary_cleanup_also_requires_the_run_marker(self, monkeypatch, tmp_path):
        prefix = ingest_positions.source_prefix_for(SNAPSHOT)
        calls, path = TestWriteBeforeDelete()._harness(monkeypatch, tmp_path)
        inner = ingest_positions.select

        def select(table, query):
            if table == ingest_positions.SNAPSHOTS_TABLE:
                return [{"source_file": f"{prefix}#run-OLD"},
                        {"source_file": f"{prefix}-archive"}]
            return inner(table, query)

        monkeypatch.setattr(ingest_positions, "select", select)
        assert ingest_positions.main([str(path)]) == 0
        removed = [c[2]["source_file"] for c in calls
                   if c[0] == "delete" and c[1] == ingest_positions.SNAPSHOTS_TABLE]
        assert removed == [f"eq.{prefix}#run-OLD"]

    def test_searchable_posting_without_keywords_is_refused(self, monkeypatch, tmp_path):
        # 매핑 안 된 직무명(영문 등)은 segment=unsegmented, 검색어 0개인데 searchable=True 로
        # 적재돼 검색에서 조용히 빠졌다. 적재 전에 멈춰야 한다.
        def explode(*a, **k):
            raise AssertionError("must not touch Supabase")

        for name in ("select", "delete", "insert"):
            monkeypatch.setattr(ingest_positions, name, explode)
        position = {**self.WRTN["positions"][0], "job": "Software Engineering"}
        path = tmp_path / "snap.json"
        path.write_text(json.dumps({**self.WRTN, "positions": [position]}, ensure_ascii=False),
                        encoding="utf-8")
        assert ingest_positions.main([str(path)]) == 1
