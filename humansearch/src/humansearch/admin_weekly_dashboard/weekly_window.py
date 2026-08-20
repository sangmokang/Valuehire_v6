"""Sunday-to-Saturday reporting windows derived from a meeting ISO week."""

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from typing import TypedDict
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")


class WeeklyWindowPayload(TypedDict):
    """Public, JSON-safe representation of a weekly window."""

    meeting_instance_date_kst: str
    week_anchor_monday_kst: str
    meeting_iso_week: str
    event_start_kst: str
    event_end_exclusive_kst: str
    timezone: str


@dataclass(frozen=True)
class WeeklyWindow:
    """A meeting label paired with its preceding Sunday-to-Saturday event window."""

    meeting_instance_date_kst: str
    week_anchor_monday_kst: str
    meeting_iso_week: str
    event_start_kst: str
    event_end_exclusive_kst: str
    timezone: str
    _event_start: datetime = field(repr=False)
    _event_end_exclusive: datetime = field(repr=False)

    def contains(self, occurred_at: datetime) -> bool:
        """Return whether an aware instant belongs to this half-open event window."""

        if occurred_at.tzinfo is None or occurred_at.utcoffset() is None:
            raise ValueError("occurred_at must be timezone-aware")
        occurred_at_kst = occurred_at.astimezone(KST)
        return self._event_start <= occurred_at_kst < self._event_end_exclusive

    def to_payload(self) -> WeeklyWindowPayload:
        """Return the public window fields without internal datetime helpers."""

        return {
            "meeting_instance_date_kst": self.meeting_instance_date_kst,
            "week_anchor_monday_kst": self.week_anchor_monday_kst,
            "meeting_iso_week": self.meeting_iso_week,
            "event_start_kst": self.event_start_kst,
            "event_end_exclusive_kst": self.event_end_exclusive_kst,
            "timezone": self.timezone,
        }


def weekly_window(meeting_date_kst: str) -> WeeklyWindow:
    """Build the stable reporting window for a KST meeting date."""

    try:
        meeting_date = date.fromisoformat(meeting_date_kst)
    except ValueError as error:
        raise ValueError("meeting_date_kst must be an ISO date") from error

    week_anchor_monday = meeting_date - timedelta(days=meeting_date.weekday())
    event_start_date = week_anchor_monday - timedelta(days=8)
    event_end_date = week_anchor_monday - timedelta(days=1)
    event_start = datetime.combine(event_start_date, time.min, tzinfo=KST)
    event_end_exclusive = datetime.combine(event_end_date, time.min, tzinfo=KST)
    iso_year, iso_week, _ = meeting_date.isocalendar()

    return WeeklyWindow(
        meeting_instance_date_kst=meeting_date.isoformat(),
        week_anchor_monday_kst=week_anchor_monday.isoformat(),
        meeting_iso_week=f"{iso_year:04d}-W{iso_week:02d}",
        event_start_kst=event_start.isoformat(),
        event_end_exclusive_kst=event_end_exclusive.isoformat(),
        timezone="Asia/Seoul",
        _event_start=event_start,
        _event_end_exclusive=event_end_exclusive,
    )
