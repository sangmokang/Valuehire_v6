import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import page_trace  # noqa: E402


class TestStatusMapping:
    def test_blocked_is_stored_as_failed_because_of_the_check_constraint(self):
        # search_jobs.status 는 done/failed/running 만 받는다. blocked 를 그대로 쓰면 23514.
        assert page_trace.DB_STATUS["blocked"] == "failed"

    def test_unknown_status_is_refused(self, monkeypatch):
        monkeypatch.setattr(page_trace, "_request", lambda *a, **k: None, raising=False)
        with pytest.raises(ValueError, match="unknown status"):
            page_trace.close_job(1, "paused", {}, None)

    def test_outcome_keeps_the_real_word(self, monkeypatch):
        captured = {}

        def fake_request(method, path, *, payload=None, prefer=None):
            captured["payload"] = payload

        monkeypatch.setattr("supabase_io._request", fake_request)
        page_trace.close_job(7, "blocked", {"positions": 62}, "auth wall")
        assert captured["payload"]["status"] == "failed"
        assert captured["payload"]["result_summary"]["outcome"] == "blocked"
        assert captured["payload"]["result_summary"]["positions"] == 62


class TestRecordValidation:
    def test_unknown_action_is_refused(self):
        with pytest.raises(ValueError, match="unknown action"):
            page_trace.record(1, [{"action": "scrolled", "url": "https://x"}])

    def test_snapshot_without_url_is_refused(self):
        with pytest.raises(ValueError, match="needs the url"):
            page_trace.record(1, [{"action": "visit"}])

    def test_listing_is_an_accepted_action(self):
        # 리스팅 페이지 저장은 사장님 요구사항 — 액션 목록에서 빠지면 안 된다.
        assert "listing" in page_trace.ACTIONS
        assert "filter_open" in page_trace.ACTIONS
        assert "auth_wall" in page_trace.ACTIONS
