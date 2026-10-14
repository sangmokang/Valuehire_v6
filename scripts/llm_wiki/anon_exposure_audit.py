"""익명(anon) 키 노출 감사기 — RED 단계 골격. 동작은 test_anon_exposure.py 의 계약으로 채운다."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class ObjectStat:
    name: str
    count: int | None
    error: str | None = None


@dataclass
class Verdict:
    status: str = "PASS"
    failures: list[str] = field(default_factory=list)


def parse_anon_zero_objects(markdown: str) -> list[str]:
    return []


def judge(stats: list[ObjectStat], objects: list[str]) -> Verdict:
    return Verdict()


def collect(base: str, key: str, objects: list[str], counter=None) -> list[ObjectStat]:
    return []


def load_anon_creds(env_path: Path) -> tuple[str, str]:
    return "", ""
