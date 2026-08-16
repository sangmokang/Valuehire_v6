"""Runtime acceptance tests for the Sunday-to-Saturday reporting window."""

from datetime import datetime
from zoneinfo import ZoneInfo

from humansearch.admin_weekly_dashboard import weekly_window


KST = ZoneInfo("Asia/Seoul")


def test_weekly_window_returns_sunday_to_saturday_for_monday_meeting() -> None:
    window = weekly_window("2026-08-17")

    assert window.meeting_iso_week == "2026-W34"
    assert window.week_anchor_monday_kst == "2026-08-17"
    assert window.event_start_kst == "2026-08-09T00:00:00+09:00"
    assert window.event_end_exclusive_kst == "2026-08-16T00:00:00+09:00"


def test_weekly_window_is_stable_when_meeting_moves_within_iso_week() -> None:
    monday = weekly_window("2026-08-17")
    tuesday = weekly_window("2026-08-18")

    assert monday.meeting_iso_week == tuesday.meeting_iso_week == "2026-W34"
    assert monday.event_start_kst == tuesday.event_start_kst
    assert monday.event_end_exclusive_kst == tuesday.event_end_exclusive_kst


def test_weekly_window_includes_start_and_excludes_end_boundary() -> None:
    window = weekly_window("2026-08-17")

    assert window.contains(datetime(2026, 8, 9, 0, 0, 0, tzinfo=KST))
    assert window.contains(datetime(2026, 8, 15, 23, 59, 59, tzinfo=KST))
    assert not window.contains(datetime(2026, 8, 16, 0, 0, 0, tzinfo=KST))

