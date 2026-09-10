"""HS-13.01b — 브리프 운영 상수 계약 로더 (골격).

RED 단계: 필드와 서명만 있고 판정은 없다.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

__all__ = [
    "BriefPolicy",
    "load_brief_policy",
    "override_policy_for_tests",
    "policy",
]


@dataclass(frozen=True)
class BriefPolicy:
    """브리프·서치 패킷이 쓰는 운영 상수. 소유자는 계약 파일 하나뿐이다."""

    version: int
    linkedin_inmail_max_chars: int
    subject_prefixes: tuple[str, ...]
    subject_search_suffix: str
    profile_url_prefixes: tuple[str, ...]
    team_mail_domain: str
    clickup_position_list_id: str
    default_search_location: str


def load_brief_policy(path: Path | None = None) -> BriefPolicy:
    """계약 파일을 읽어 검증한다."""

    raise NotImplementedError("HS-13.01b GREEN 에서 구현한다")


def policy() -> BriefPolicy:
    """모듈 단일 로더. 최초 1회만 읽고 캐시한다."""

    raise NotImplementedError("HS-13.01b GREEN 에서 구현한다")


@contextmanager
def override_policy_for_tests(replacement: BriefPolicy) -> Iterator[BriefPolicy]:
    """시험 전용 — 정책을 임시로 갈아끼우고 반드시 원복한다."""

    raise NotImplementedError("HS-13.01b GREEN 에서 구현한다")
    yield replacement
