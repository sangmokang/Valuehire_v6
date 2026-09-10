"""HS-13.01c — 서치 지역은 계약 허용 목록 안의 값만(D12).

`SearchFilters.location` 은 `contracts/humansearch/brief-policy.json` 의
`allowed_search_locations` 안에 있어야 하고, 기본값(`default_search_location`)도 그 안에 있어야
계약 자체가 로드된다. 지역을 넓히는 일은 코드가 아니라 계약 파일 편집 = 오너 결정이다.

계약: docs/engineering/humansearch-hs13-position-brief-goal-2026-09-10.md §5 SearchFilters · §7 D12.
"""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from humansearch.brief import (
    BriefInputError,
    SearchFilters,
    load_brief_policy,
    policy,
)
from humansearch.brief.policy import override_policy_for_tests


def _payload(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "version": 1,
        "linkedin_inmail_max_chars": 1899,
        "subject_prefixes": ["[포지션]", "[ValuehireSearch][포지션]"],
        "subject_search_suffix": " | ValuehireSearch",
        "profile_url_prefixes": [
            "https://www.linkedin.com/in/",
            "https://kr.linkedin.com/in/",
            "https://linkedin.com/in/",
        ],
        "team_mail_domain": "valueconnect.kr",
        "clickup_position_list_id": "901814621569",
        "default_search_location": "South Korea",
        "allowed_search_locations": ["South Korea"],
    }
    base.update(overrides)
    return base


def _write(tmp_path: Path, payload: dict[str, object]) -> Path:
    target = tmp_path / "brief-policy.json"
    target.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return target


def test_default_location_comes_from_contract_and_is_allowed() -> None:
    loaded = policy()
    assert loaded.allowed_search_locations == ("South Korea",)
    assert SearchFilters().location == "South Korea"
    assert SearchFilters(location="South Korea").location == "South Korea"


def test_location_outside_the_allowed_list_is_rejected() -> None:
    with pytest.raises(BriefInputError):
        SearchFilters(location="Japan")


@pytest.mark.parametrize("bad", ["", "   ", "south korea", "South Korea "])
def test_blank_or_inexact_location_is_rejected(bad: str) -> None:
    with pytest.raises(BriefInputError):
        SearchFilters(location=bad)


def test_widening_the_contract_list_actually_admits_the_new_location() -> None:
    wider = replace(
        policy(),
        allowed_search_locations=("South Korea", "Japan"),
        default_search_location="Japan",
    )
    with override_policy_for_tests(wider):
        assert SearchFilters().location == "Japan"
        assert SearchFilters(location="South Korea").location == "South Korea"
    with pytest.raises(BriefInputError):
        SearchFilters(location="Japan")


def test_contract_rejects_default_outside_allowed_list(tmp_path: Path) -> None:
    target = _write(
        tmp_path,
        _payload(default_search_location="Japan", allowed_search_locations=["South Korea"]),
    )
    with pytest.raises(BriefInputError):
        load_brief_policy(target)


@pytest.mark.parametrize(
    "value",
    [[], [""], ["South Korea", ""], "South Korea", ["South Korea", "South Korea"], None],
)
def test_contract_rejects_malformed_allowed_list(tmp_path: Path, value: object) -> None:
    payload = _payload()
    payload["allowed_search_locations"] = value
    target = tmp_path / "brief-policy.json"
    target.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(BriefInputError):
        load_brief_policy(target)


def test_contract_without_allowed_list_is_rejected(tmp_path: Path) -> None:
    payload = _payload()
    del payload["allowed_search_locations"]
    target = tmp_path / "brief-policy.json"
    target.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(BriefInputError):
        load_brief_policy(target)
