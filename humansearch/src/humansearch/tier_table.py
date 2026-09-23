"""The one loader for code-owned school/company tiers (``contracts/*-tier.json``); Jev never decides
a tier. A table scores only when APPROVED, fully approved and free of synthetic markers."""

import json
import re
import unicodedata
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from humansearch.organization_shadow import _exact_keys, _mapping, _text

UNLISTED = "UNLISTED"
APPROVED = "APPROVED"
_STATUSES = frozenset({"SYNTHETIC_PLACEHOLDER_OWNER_TO_FILL", APPROVED})
_TIER_VERDICTS = frozenset({"SUPPORTED", "PARTIAL"})  # a tier alone never rejects a candidate
_MARKERS = ("synthetic", "placeholder")
_DAY = re.compile(r"[0-9]{4}-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])")
_PLURAL = {"school": "schools", "company": "companies"}
Kind = Literal["school", "company"]


@dataclass(frozen=True, slots=True)
class TierTable:
    kind: str
    version: str
    status: str
    ranks: Mapping[str, int]
    verdicts: Mapping[str, str]
    entries: Mapping[str, str]
    aliases: Mapping[str, str]
    approval: Mapping[str, str] | None

    @property
    def approved(self) -> bool:
        return self.status == APPROVED


def load_tier_table(path: Path, kind: Kind) -> TierTable:
    return tier_table_from(json.loads(path.read_text(encoding="utf-8")), kind)


def tier_table_from(raw: object, kind: Kind) -> TierTable:
    plural = _PLURAL[kind]
    root = _mapping(raw, f"{kind}_tier")
    _exact_keys(root, {f"{kind}_tier_version", "status", "approval", "tiers", plural, "aliases"},
                f"{kind}_tier")
    version = _text(root[f"{kind}_tier_version"], "tier version")
    if root["status"] not in _STATUSES:
        raise ValueError("tier table status is undefined")
    ranks, verdicts = _tiers(root["tiers"])
    entries: dict[str, str] = {}
    synthetic = _marked(version)
    for name, value in _mapping(root[plural], plural).items():
        entry = _mapping(value, f"{plural}[]")
        _exact_keys(entry, {"tier", "synthetic"}, f"{plural}[]")
        if entry["tier"] not in ranks or not isinstance(entry["synthetic"], bool):
            raise ValueError(f"{plural}[] has an undefined tier or synthetic flag")
        key = normalize_name(_text(name, "tier name"))
        if key in entries:
            raise ValueError(f"two {plural} names normalize to the same key")
        entries[key] = str(entry["tier"])
        synthetic = synthetic or entry["synthetic"] or _marked(name)
    aliases: dict[str, str] = {}
    for alias, target in _mapping(root["aliases"], "aliases").items():
        key = normalize_name(_text(alias, "alias"))
        if key in entries or key in aliases:  # F17: an alias may never shadow a row or another alias
            raise ValueError(f"a tier alias collides with a {kind} name or another alias")
        aliases[key] = normalize_name(_text(target, "alias"))
    if set(aliases.values()) - set(entries):
        raise ValueError("tier aliases point to an unknown name")
    synthetic = synthetic or any(_marked(alias) for alias in aliases)
    approved = root["status"] == APPROVED
    if approved and synthetic:
        raise ValueError("an APPROVED tier table cannot hold synthetic entries")
    return TierTable(kind, version, str(root["status"]), ranks, verdicts, entries, aliases,
                     _approval(root["approval"], required=approved))


def resolve_tier(names: Sequence[str], table: TierTable) -> tuple[str | None, int | None]:
    """Best-ranked tier and the index it came from; unmapped names stay UNLISTED, never zero."""
    best: tuple[int, int, str] | None = None
    for index, name in enumerate(names):
        key = normalize_name(name)
        tier = table.entries.get(table.aliases.get(key, key))
        candidate = (table.ranks[tier] if tier else len(table.ranks) + 1, index, tier or UNLISTED)
        best = candidate if best is None or candidate < best else best
    return (None, None) if best is None else (best[2], best[1])


def normalize_name(name: str) -> str:
    """Comparison key: NFKC (NFD Hangul, full-width forms), no whitespace or invisible format
    characters such as U+200B, casefold."""
    text = unicodedata.normalize("NFKC", name)
    return "".join(c for c in text if not c.isspace() and unicodedata.category(c) != "Cf").casefold()


def _tiers(raw: object) -> tuple[dict[str, int], dict[str, str]]:
    if not isinstance(raw, list) or not raw:
        raise ValueError("tiers must be a nonempty list")
    ranks: dict[str, int] = {}
    verdicts: dict[str, str] = {}
    for item in raw:
        entry = _mapping(item, "tiers[]")
        _exact_keys(entry, {"tier", "rank", "verdict"}, "tiers[]")
        tier, rank = _text(entry["tier"], "tier"), entry["rank"]
        if tier == UNLISTED or tier in ranks or isinstance(rank, bool) or not isinstance(rank, int):
            raise ValueError("tiers[] has an invalid tier or rank")
        if entry["verdict"] not in _TIER_VERDICTS:
            raise ValueError("tiers[] verdict must be SUPPORTED or PARTIAL")
        ranks[tier], verdicts[tier] = rank, str(entry["verdict"])
    if sorted(ranks.values()) != list(range(1, len(ranks) + 1)):
        raise ValueError("tier ranks must be exactly 1..n")  # UNLISTED ranks n + 1
    return ranks, verdicts


def _approval(raw: object, *, required: bool) -> Mapping[str, str] | None:
    if raw is None and not required:
        return None
    record = _mapping(raw, "approval")
    _exact_keys(record, {"approved_by", "approved_at", "source"}, "approval")
    fields = {key: _text(value, f"approval.{key}") for key, value in record.items()}
    if not _DAY.fullmatch(fields["approved_at"]):
        raise ValueError("approval.approved_at must be YYYY-MM-DD")
    return fields


def _marked(text: str) -> bool:
    return any(marker in normalize_name(text) for marker in _MARKERS)
