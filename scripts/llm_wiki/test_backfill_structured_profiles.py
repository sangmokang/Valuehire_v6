"""구조화 프로필 복구(backfill) 계획·적용 계약 시험.

실제 Supabase·SQLite 를 쓰지 않는다. 전송 계층은 FakeTransport 로 바꿔 끼운다.
계약(EARS):
  - 원격 행이 없으면 절대 쓰지 않는다(부분 행 INSERT 금지).
  - 원격 structured_json 이 이미 있으면 절대 덮어쓰지 않는다.
  - 로컬 structured_json 이 JSON 으로 안 읽히거나 _meta.input_hash 가 없으면 보낸다고 하지 않는다.
  - dry-run 은 쓰기 요청 0건.
  - 적용 시 모든 쓰기 URL 에 서버측 보호 조건 structured_json=is.null 이 붙는다.
  - 쓰기 1건마다 장부 1줄(local_id·내용 지문·매치 행 수)이 남는다.
"""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.llm_wiki import backfill_structured_profiles as bf

VALID = json.dumps({"salary_man": 8000, "total_years": 7, "_meta": {"source": "t", "input_hash": "h1"}})


def _local(local_id: str, body: str = VALID) -> bf.LocalRow:
    return bf.LocalRow(local_id=local_id, site="linkedin_recruiter", structured_json=body)


class FakeTransport:
    def __init__(self, remote: dict[str, bool | None]):
        # remote[local_id] = None → 원격 행 없음, False → 비어 있음, True → 이미 채워짐
        self.remote = remote
        self.reads: list[str] = []
        self.writes: list[tuple[str, dict]] = []

    def get_remote_state(self, local_ids: list[str]) -> dict[str, bool]:
        self.reads.append(",".join(local_ids))
        return {i: self.remote[i] for i in local_ids if self.remote.get(i) is not None}

    def patch(self, url_query: str, body: dict) -> int:
        self.writes.append((url_query, body))
        local_id = url_query.split("local_id=eq.")[1].split("&")[0]
        return 1 if self.remote.get(local_id) is False else 0


class PlanTests(unittest.TestCase):
    def test_selects_only_present_and_empty_remote_rows(self):
        rows = [_local("a"), _local("b"), _local("c")]
        plan = bf.plan_backfill(rows, {"a": False, "b": True})  # c 는 원격에 없음
        self.assertEqual([r.local_id for r in plan.to_fill], ["a"])
        self.assertEqual(plan.skipped_filled, ["b"])
        self.assertEqual(plan.skipped_absent, ["c"])

    def test_invalid_local_json_is_never_planned(self):
        rows = [_local("x", "not json"), _local("y", json.dumps({"salary_man": 1}))]  # y 는 _meta 없음
        plan = bf.plan_backfill(rows, {"x": False, "y": False})
        self.assertEqual(plan.to_fill, [])
        self.assertEqual(sorted(plan.skipped_invalid), ["x", "y"])

    def test_plan_counts_sum_to_input(self):
        rows = [_local("a"), _local("b"), _local("c"), _local("d", "{")]
        plan = bf.plan_backfill(rows, {"a": False, "b": True, "d": False})
        total = len(plan.to_fill) + len(plan.skipped_filled) + len(plan.skipped_absent) + len(plan.skipped_invalid)
        self.assertEqual(total, 4)


class ApplyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.ledger = Path(self.tmp.name) / "ledger.jsonl"

    def tearDown(self):
        self.tmp.cleanup()

    def test_dry_run_sends_no_writes(self):
        t = FakeTransport({"a": False})
        plan = bf.plan_backfill([_local("a")], t.get_remote_state(["a"]))
        result = bf.apply_plan(t, plan, self.ledger, apply=False)
        self.assertEqual(t.writes, [])
        self.assertEqual(result.written, 0)
        self.assertFalse(self.ledger.exists())

    def test_apply_guards_every_write_with_is_null_and_writes_ledger(self):
        t = FakeTransport({"a": False, "b": False})
        plan = bf.plan_backfill([_local("a"), _local("b")], t.get_remote_state(["a", "b"]))
        result = bf.apply_plan(t, plan, self.ledger, apply=True)
        self.assertEqual(len(t.writes), 2)
        for url_query, body in t.writes:
            self.assertIn("structured_json=is.null", url_query)
            self.assertEqual(set(body), {"structured_json"})
        lines = [json.loads(l) for l in self.ledger.read_text().splitlines()]
        done = [l for l in lines if l["phase"] == "done"]
        self.assertEqual(len(done), 2)  # 쓰기 1건 = intent 1줄 + done 1줄
        self.assertEqual({l["local_id"] for l in done}, {"a", "b"})
        self.assertTrue(all(len(l["sha256"]) == 64 and l["matched"] == 1 for l in done))
        self.assertEqual(result.written, 2)

    def test_apply_reports_zero_match_as_not_written(self):
        # 계획 뒤 다른 주체가 먼저 채운 경우: 서버 보호 조건이 0행 매치 → 쓰지 않은 것으로 센다
        t = FakeTransport({"a": False})
        plan = bf.plan_backfill([_local("a")], t.get_remote_state(["a"]))
        t.remote["a"] = True
        result = bf.apply_plan(t, plan, self.ledger, apply=True)
        self.assertEqual(result.written, 0)
        self.assertEqual(result.unmatched, ["a"])


class LedgerDurabilityTests(unittest.TestCase):
    """V1 결함 4: 응답을 못 받은 행도 장부로 추적할 수 있어야 한다."""

    def test_intent_is_written_before_patch_and_error_is_recorded(self):
        class Boom(FakeTransport):
            def patch(self, url_query, body):
                if "local_id=eq.b" in url_query:
                    self.writes.append((url_query, body))  # 시도는 했으나 응답을 잃은 경우
                    raise OSError("connection lost")
                return super().patch(url_query, body)

        t = Boom({"a": False, "b": False, "c": False})
        plan = bf.plan_backfill([_local("a"), _local("b"), _local("c")], t.get_remote_state(["a", "b", "c"]))
        with tempfile.TemporaryDirectory() as d:
            ledger = Path(d) / "l.jsonl"
            with self.assertRaises(OSError):
                bf.apply_plan(t, plan, ledger, apply=True)
            lines = [json.loads(l) for l in ledger.read_text().splitlines()]
        phases = [(l["local_id"], l["phase"]) for l in lines]
        self.assertEqual(phases, [("a", "intent"), ("a", "done"), ("b", "intent"), ("b", "error")])
        self.assertIn("connection lost", lines[-1]["error"])
        self.assertEqual(len(t.writes), 2)  # c 는 시도되지 않았다


class StructuredValidityTests(unittest.TestCase):
    """V1 결함 5: 표식 존재가 아니라 최소 내용 규약을 본다."""

    def _plan_one(self, body):
        return bf.plan_backfill([_local("x", body)], {"x": False})

    def test_meta_only_object_is_invalid(self):
        self.assertEqual(self._plan_one(json.dumps({"_meta": {"source": "t", "input_hash": "h1"}})).to_fill, [])

    def test_non_string_or_empty_hash_is_invalid(self):
        for h in (123, True, "", None):
            self.assertEqual(self._plan_one(json.dumps({"salary_man": 1, "_meta": {"source": "t", "input_hash": h}})).to_fill, [], h)

    def test_missing_source_is_invalid(self):
        self.assertEqual(self._plan_one(json.dumps({"salary_man": 1, "_meta": {"input_hash": "h1"}})).to_fill, [])

    def test_all_fields_null_is_invalid(self):
        self.assertEqual(self._plan_one(json.dumps({"salary_man": None, "major": None, "_meta": {"source": "t", "input_hash": "h1"}})).to_fill, [])


class RestTransportTests(unittest.TestCase):
    """V1 결함 1: 실제 전송 객체의 질의·본문·반환 조건·오류 전파를 고정한다."""

    def _transport(self, responder):
        calls = []

        def opener(req, timeout):
            calls.append(req)
            return responder(req)

        return bf.RestTransport("https://x.supabase.co", "k", opener=opener), calls

    def test_get_remote_state_query_and_mapping(self):
        class R:
            def __enter__(self): return self
            def __exit__(self, *a): return False
            def read(self): return json.dumps([{"local_id": "a", "structured_json": None}, {"local_id": "b", "structured_json": {"k": 1}}]).encode()
        t, calls = self._transport(lambda req: R())
        state = t.get_remote_state(["a", "b"])
        self.assertEqual(state, {"a": False, "b": True})
        self.assertEqual(calls[0].get_method(), "GET")
        self.assertIn("select=local_id,structured_json", calls[0].full_url)
        self.assertIn("local_id=in.(", calls[0].full_url)

    def test_patch_sends_guard_body_and_representation(self):
        class R:
            def __enter__(self): return self
            def __exit__(self, *a): return False
            def read(self): return json.dumps([{"local_id": "a"}]).encode()
        t, calls = self._transport(lambda req: R())
        n = t.patch("local_id=eq.a&structured_json=is.null", {"structured_json": {"k": 1}})
        self.assertEqual(n, 1)
        req = calls[0]
        self.assertEqual(req.get_method(), "PATCH")
        self.assertIn("structured_json=is.null", req.full_url)
        self.assertEqual(req.get_header("Prefer"), "return=representation")
        self.assertEqual(json.loads(req.data), {"structured_json": {"k": 1}})

    def test_http_error_propagates_not_zero(self):
        import urllib.error

        def boom(req):
            raise urllib.error.HTTPError(req.full_url, 401, "unauthorized", {}, None)
        t, _ = self._transport(boom)
        with self.assertRaises(urllib.error.HTTPError):
            t.patch("local_id=eq.a&structured_json=is.null", {"structured_json": {}})


class CredsTests(unittest.TestCase):
    def test_missing_creds_is_not_run_exit_2(self):
        with tempfile.NamedTemporaryFile("w", suffix=".env", delete=False) as f:
            f.write("OTHER=1\n")
        with self.assertRaises(SystemExit) as cm:
            bf.load_creds(Path(f.name))
        self.assertEqual(cm.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
