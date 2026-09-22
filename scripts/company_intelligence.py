#!/usr/bin/env python3
"""Validate and snapshot JD-specific company intelligence for Search runs.

The input is intentionally a manually researched JSON document. This module
does not crawl sites; it validates evidence-linked observations, preserves
uncertainty, and turns the findings into a JD-specific search hypothesis.
"""

import argparse
import hashlib
import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse


class CompanyIntelligenceError(Exception):
    pass


ALLOWED_IDENTITY = {"confirmed", "ambiguous", "unconfirmed"}
ALLOWED_CONFIDENCE = {"confirmed", "inferred", "tentative"}
ALLOWED_EMPLOYMENT = {"current", "former", "unknown"}
STALE_DAYS = 90


def build_snapshot(document):
    _require_mapping(document, "document")
    jd = _require_mapping(document.get("jd"), "jd")
    company = _validate_company(_require_mapping(jd.get("company"), "jd.company"))
    position = _validate_position(_require_mapping(jd.get("position"), "jd.position"))
    source_url = _url(jd.get("source_url"), "jd.source_url")
    captured_at = _instant(jd.get("captured_at"), "jd.captured_at")
    intelligence = _require_mapping(document.get("company_intelligence"), "company_intelligence")
    as_of = _instant(intelligence.get("as_of"), "company_intelligence.as_of")
    observations = intelligence.get("observations")
    if not isinstance(observations, list):
        raise CompanyIntelligenceError("company_intelligence.observations must be a list")

    raw_observations = [_observation(obs) for obs in observations]
    people, conflicts = _build_people(raw_observations)
    person_conflicted_fields = _person_conflicted_fields(conflicts)
    employment, employment_conflicts = _build_employment(raw_observations, people, company, as_of)
    organization = _build_organization(employment)
    patterns = _build_patterns(people, employment, position, as_of, person_conflicted_fields)
    conflicts.extend(employment_conflicts)
    manual_hypothesis = _validate_manual_hypothesis(document.get("manual_hypothesis"), company, source_url, position, raw_observations)

    if company["identity_status"] != "confirmed":
        status = "blocked_company_identity"
        hypothesis = {
            "hard_requirements": [item["key"] for item in position["hard_requirements"]],
            "priority": [],
            "expansion": [],
            "jd_org_differences": [],
            "blocked_reason": "company identity is not confirmed",
        }
        channel_plan = {channel: [] for channel in ("jobkorea", "saramin", "linkedin_rps", "rps")}
    else:
        status = "ready"
        hypothesis = _build_hypothesis(position, patterns, manual_hypothesis)
        channel_plan = _build_channel_plan(position, patterns, hypothesis)

    snapshot = {
        "schema_version": "company-intelligence-v1",
        "run_id": _text(document.get("run_id"), "run_id"),
        "status": status,
        "jd": {
            "source_url": source_url,
            "captured_at": captured_at,
            "position": position,
        },
        "company": company,
        "people": people,
        "employment": employment,
        "organization": organization,
        "talent_patterns": patterns,
        "search_hypothesis": hypothesis,
        "manual_hypothesis": manual_hypothesis,
        "channel_search_plan": channel_plan,
        "conflicts": conflicts,
        "evidence": _collect_evidence(company, people, employment),
        "raw_observations": raw_observations,
        "as_of": as_of,
    }
    snapshot["snapshot_hash"] = _hash(snapshot)
    return snapshot


def run(document, store_dir, *, stale_after_days=STALE_DAYS):
    initial = build_snapshot(document)
    root = Path(store_dir)
    company_dir = root / initial["company"]["company_key"]
    company_dir.mkdir(parents=True, exist_ok=True)

    previous = []
    for path in company_dir.glob("snapshot-*.json"):
        loaded = _load_snapshot(path)
        if loaded["company"].get("homepage") != initial["company"]["homepage"]:
            raise CompanyIntelligenceError("cached company homepage mismatch")
        if loaded.get("snapshot_hash") != initial["snapshot_hash"]:
            previous.append((path, loaded))

    document = _merge_cached_observations(document, previous)
    snapshot = build_snapshot(document)
    previous.sort(key=lambda item: item[1].get("as_of", ""))
    stale = False
    if previous:
        latest_as_of = _parse(previous[-1][1].get("as_of"))
        current_as_of = _parse(snapshot["as_of"])
        stale = latest_as_of is None or current_as_of is None or (
            current_as_of - latest_as_of
        ).days > stale_after_days

    path = company_dir / ("snapshot-" + snapshot["snapshot_hash"][:16] + ".json")
    if path.exists():
        existing = json.loads(path.read_text())
        if existing.get("snapshot_hash") != snapshot["snapshot_hash"]:
            raise CompanyIntelligenceError("snapshot path hash collision")
    else:
        _persist(path, snapshot)

    return {
        "ok": True,
        "snapshot_path": str(path),
        "snapshot_hash": snapshot["snapshot_hash"],
        "status": snapshot["status"],
        "cache": {
            "company_key": company_dir.name,
            "previous_snapshot_count": len(previous),
            "stale": stale,
            "stale_after_days": stale_after_days,
        },
        "search_hypothesis": snapshot["search_hypothesis"],
        "channel_search_plan": snapshot["channel_search_plan"],
    }


def load_company(store_dir, homepage):
    company_key = _company_key(homepage)
    company_dir = Path(store_dir) / company_key
    snapshots = []
    for path in company_dir.glob("snapshot-*.json"):
        snapshots.append(_load_snapshot(path))
    snapshots.sort(key=lambda item: item.get("as_of", ""))
    return {"ok": True, "company_key": company_key, "snapshots": snapshots}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input")
    parser.add_argument("--store-dir", required=True)
    parser.add_argument("--summary")
    parser.add_argument("--load-company", action="store_true")
    parser.add_argument("--homepage")
    parser.add_argument("--as-of")
    parser.add_argument("--stale-after-days", type=int, default=STALE_DAYS)
    args = parser.parse_args(argv)
    try:
        if args.load_company:
            if not args.homepage:
                raise CompanyIntelligenceError("--load-company requires --homepage")
            summary = load_company(args.store_dir, args.homepage)
        else:
            if not args.input:
                raise CompanyIntelligenceError("--input is required unless --load-company is used")
            document = json.loads(Path(args.input).read_text())
            if args.as_of:
                document.setdefault("company_intelligence", {})["as_of"] = args.as_of
            summary = run(document, args.store_dir, stale_after_days=args.stale_after_days)
        encoded = json.dumps(summary, ensure_ascii=False, indent=2)
        if args.summary:
            _persist(Path(args.summary), summary)
        print(encoded)
        return 0
    except Exception as exc:  # noqa: BLE001 - CLI boundary
        error = str(exc) if isinstance(exc, CompanyIntelligenceError) else type(exc).__name__
        print(json.dumps({"ok": False, "error": error}, ensure_ascii=False), file=sys.stderr)
        return 1


def _validate_company(company):
    evidence = _evidence(company.get("identity_evidence"), "jd.company.identity_evidence")
    status = company.get("identity_status")
    if status not in ALLOWED_IDENTITY:
        raise CompanyIntelligenceError("jd.company.identity_status must be confirmed/ambiguous/unconfirmed")
    homepage = _url(company.get("homepage"), "jd.company.homepage")
    return {
        "name": _text(company.get("name"), "jd.company.name"),
        "english_name": _optional_text(company.get("english_name")),
        "brand_names": _text_list(company.get("brand_names", []), "jd.company.brand_names"),
        "homepage": homepage,
        "company_key": _company_key(homepage),
        "industry": _optional_text(company.get("industry")),
        "location": _optional_text(company.get("location")),
        "identity_status": status,
        "identity_evidence": evidence,
    }


def _validate_position(position):
    hard = position.get("hard_requirements", [])
    if not isinstance(hard, list):
        raise CompanyIntelligenceError("jd.position.hard_requirements must be a list")
    hard_requirements = []
    for index, item in enumerate(hard):
        mapping = _require_mapping(item, f"jd.position.hard_requirements[{index}]")
        urls = mapping.get("evidence_urls", [])
        if not isinstance(urls, list) or not urls:
            raise CompanyIntelligenceError("hard requirement evidence_urls required")
        hard_requirements.append(
            {
                "key": _key(mapping.get("key"), "hard requirement key"),
                "label": _text(mapping.get("label"), "hard requirement label"),
                "evidence_urls": [_url(url, "hard requirement evidence URL") for url in urls],
            }
        )
    return {
        "title": _text(position.get("title"), "jd.position.title"),
        "organization": _optional_text(position.get("organization")),
        "function": _optional_text(position.get("function")),
        "seniority": _optional_text(position.get("seniority")),
        "location": _optional_text(position.get("location")),
        "hard_requirements": hard_requirements,
        "preferred": position.get("preferred", []),
        "technologies": _text_list(position.get("technologies", []), "jd.position.technologies"),
    }


def _build_people(observations):
    by_id = {}
    profile_owner = {}
    conflicts = []
    for item in observations:
        if item["type"] != "person":
            continue
        raw_profile_url = item.get("profile_url")
        profile_url = _url(raw_profile_url, "person.profile_url") if raw_profile_url else None
        canonical = item.get("same_person_as") or item["id"]
        canonical = _text(canonical, "person same_person_as")
        if item.get("same_person_as"):
            identity_evidence = _evidence(item.get("identity_evidence"), "person.identity_evidence")
        else:
            identity_evidence = []
        if profile_url:
            if profile_url in profile_owner and profile_owner[profile_url] != canonical:
                raise CompanyIntelligenceError("profile URL cannot belong to two people")
            profile_owner[profile_url] = canonical
        normalized = {
            "id": canonical,
            "source_observation_ids": [item["id"]],
            "name": _text(item.get("name"), "person.name"),
            "profile_urls": [profile_url] if profile_url else [],
            "current_title": _optional_text(item.get("current_title")),
            "function": _optional_text(item.get("function")),
            "seniority": _optional_text(item.get("seniority")),
            "previous_companies": _text_list(item.get("previous_companies", []), "person.previous_companies"),
            "education": _optional_text(item.get("education")),
            "skills": _text_list(item.get("skills", []), "person.skills"),
            "domains": _text_list(item.get("domains", []), "person.domains"),
            "confidence": item["confidence"],
            "snippet_only": item["snippet_only"],
            "evidence": item["evidence"],
            "identity_evidence": identity_evidence,
            "collected_at": item["collected_at"],
        }
        existing = by_id.get(canonical)
        if existing is None:
            by_id[canonical] = normalized
            continue
        existing["source_observation_ids"].extend(normalized["source_observation_ids"])
        existing["profile_urls"] = sorted(set(existing["profile_urls"]) | set(normalized["profile_urls"]))
        existing["evidence"].extend(normalized["evidence"])
        existing["identity_evidence"].extend(normalized["identity_evidence"])
        for field in ("current_title", "function", "seniority", "education", "skills", "domains", "previous_companies"):
            before = existing.get(field)
            after = normalized.get(field)
            if after in (None, [], ""):
                continue
            if before in (None, [], ""):
                existing[field] = after
            elif before != after:
                conflicts.append(
                    {
                        "type": "person_field_conflict",
                        "person_id": canonical,
                        "field": field,
                        "values": [before, after],
                        "observations": [
                            _conflict_observation(existing, field, before),
                            _conflict_observation(normalized, field, after),
                        ],
                    }
                )
                if isinstance(before, list) and isinstance(after, list):
                    existing[field] = sorted(set(before) | set(after))
    return list(by_id.values()), conflicts


def _build_employment(observations, people, company, as_of):
    person_ids = {person["id"] for person in people}
    employment = []
    conflicts = []
    accepted_names = {company["name"], company["english_name"], *company["brand_names"]}
    accepted_names = {name.casefold() for name in accepted_names if name}
    for item in observations:
        if item["type"] != "employment":
            continue
        person_id = _text(item.get("person_id"), "employment.person_id")
        if person_id not in person_ids:
            raise CompanyIntelligenceError("employment references unknown person_id")
        status = item.get("employment_status")
        if status not in ALLOWED_EMPLOYMENT:
            raise CompanyIntelligenceError("employment_status must be current, former, or unknown")
        company_name = _text(item.get("company_name"), "employment.company_name")
        if company_name.casefold() not in accepted_names:
            raise CompanyIntelligenceError("employment company mismatch")
        if status == "current" and item.get("end"):
            raise CompanyIntelligenceError("current employment cannot have end")
        evidence = item["evidence"]
        freshness = _freshness(evidence, as_of)
        employment.append(
            {
                "id": item["id"],
                "person_id": person_id,
                "company_name": company_name,
                "employment_status": status,
                "title": _optional_text(item.get("title")),
                "organization": _optional_text(item.get("organization")),
                "function": _optional_text(item.get("function")),
                "seniority": _optional_text(item.get("seniority")),
                "start": _optional_text(item.get("start")),
                "end": _optional_text(item.get("end")),
                "confidence": item["confidence"],
                "snippet_only": item["snippet_only"],
                "evidence": evidence,
                "freshness": freshness,
                "collected_at": item["collected_at"],
            }
        )
    by_person = defaultdict(list)
    for item in employment:
        by_person[item["person_id"]].append(item)
    for person_id, rows in by_person.items():
        statuses = {row["employment_status"] for row in rows if row["confidence"] == "confirmed"}
        if "current" in statuses and "former" in statuses:
            for row in rows:
                row["has_status_conflict"] = True
            conflicts.append(
                {
                    "type": "employment_status_conflict",
                    "person_id": person_id,
                    "statuses": sorted(statuses),
                    "evidence": [
                        {
                            "employment_id": row["id"],
                            "status": row["employment_status"],
                            "urls": [ev["url"] for ev in row["evidence"]],
                            "source_dates": [ev.get("published_at") or ev["observed_at"] for ev in row["evidence"]],
                        }
                        for row in rows
                    ],
                }
            )
        else:
            for row in rows:
                row["has_status_conflict"] = False
    return employment, conflicts


def _build_organization(employment):
    confirmed = defaultdict(list)
    inferred = defaultdict(list)
    for item in employment:
        if item["employment_status"] != "current":
            continue
        if item.get("has_status_conflict") or item.get("freshness", {}).get("stale_for_current_fact"):
            continue
        org = item.get("organization") or "unknown"
        bucket = confirmed if item["confidence"] == "confirmed" and not item["snippet_only"] else inferred
        bucket[org].append(item["person_id"])
    return {
        "confirmed_relationships": [{"organization": key, "person_ids": sorted(value)} for key, value in sorted(confirmed.items())],
        "inferred_relationships": [{"organization": key, "person_ids": sorted(value)} for key, value in sorted(inferred.items())],
    }


def _build_patterns(people, employment, position, as_of, conflicted_fields=None):
    conflicted_fields = conflicted_fields or {}
    previous = Counter()
    skills = Counter()
    domains = Counter()
    seniority = Counter()
    provenance = {
        "previous": defaultdict(lambda: {"person_ids": set(), "evidence_urls": set()}),
        "skills": defaultdict(lambda: {"person_ids": set(), "evidence_urls": set()}),
        "domains": defaultdict(lambda: {"person_ids": set(), "evidence_urls": set()}),
        "seniority": defaultdict(lambda: {"person_ids": set(), "evidence_urls": set()}),
    }
    people_by_id = {person["id"]: person for person in people}
    current_people = {
        item["person_id"]
        for item in employment
        if item["employment_status"] == "current"
        and item["confidence"] == "confirmed"
        and not item["snippet_only"]
        and not item.get("has_status_conflict")
        and not item.get("freshness", {}).get("stale_for_current_fact")
        and _employment_matches_position(item, position)
    }
    fallback_current_people = {
        item["person_id"]
        for item in employment
        if item["employment_status"] == "current"
        and item["confidence"] == "confirmed"
        and not item["snippet_only"]
        and not item.get("has_status_conflict")
        and not item.get("freshness", {}).get("stale_for_current_fact")
    }
    for person in people:
        if person["id"] not in current_people or person["confidence"] != "confirmed" or person["snippet_only"]:
            continue
        if _freshness(person["evidence"], as_of)["stale_for_current_fact"]:
            continue
        evidence_urls = {item["url"] for item in person["evidence"]}
        person_conflicts = conflicted_fields.get(person["id"], set())
        if "previous_companies" not in person_conflicts:
            previous.update(person.get("previous_companies", []))
            for value in person.get("previous_companies", []):
                provenance["previous"][value]["person_ids"].add(person["id"])
                provenance["previous"][value]["evidence_urls"].update(evidence_urls)
        if "skills" not in person_conflicts:
            skills.update(person.get("skills", []))
            for value in person.get("skills", []):
                provenance["skills"][value]["person_ids"].add(person["id"])
                provenance["skills"][value]["evidence_urls"].update(evidence_urls)
        if "domains" not in person_conflicts:
            domains.update(person.get("domains", []))
            for value in person.get("domains", []):
                provenance["domains"][value]["person_ids"].add(person["id"])
                provenance["domains"][value]["evidence_urls"].update(evidence_urls)
        if person.get("seniority") and "seniority" not in person_conflicts:
            seniority[person["seniority"]] += 1
            provenance["seniority"][person["seniority"]]["person_ids"].add(person["id"])
            provenance["seniority"][person["seniority"]]["evidence_urls"].update(evidence_urls)
    limit = (
        "sample_size="
        + str(len(current_people))
        + "; observed patterns are scoped to confirmed current employees with direct evidence"
    )
    return {
        "sample_size": len(current_people),
        "current_employee_sample_size": len(fallback_current_people),
        "relevant_current_employee_sample_size": len(current_people),
        "raw_people_count": len(people_by_id),
        "sample_limited": True,
        "limits": [
            limit,
            "patterns are limited to current employees whose function or organization matches the JD when available",
            "stale current-employment evidence, snippets, former employees and conflicted employment statuses are excluded from automatic patterns",
            "do not generalize as company-wide hiring criteria",
        ],
        "observed_previous_companies": _top(previous, provenance["previous"]),
        "observed_skills": _top(skills, provenance["skills"]),
        "observed_domains": _top(domains, provenance["domains"]),
        "observed_seniority": _top(seniority, provenance["seniority"]),
        "requirement_boundary": "Observed patterns are soft sourcing signals, not JD hard requirements.",
    }


def _build_hypothesis(position, patterns, manual_hypothesis=None):
    hard_keys = [item["key"] for item in position["hard_requirements"]]
    jd_tech = {tech.casefold() for tech in position["technologies"]}
    observed_skills = [item["value"] for item in patterns["observed_skills"]]
    observed_domains = [item["value"] for item in patterns["observed_domains"]]
    previous_companies = [item["value"] for item in patterns["observed_previous_companies"]]
    priority = []
    if manual_hypothesis:
        priority.extend(manual_hypothesis["priority"])
    for value in observed_domains + observed_skills:
        if value not in priority:
            priority.append(value)
    expansion = []
    expansion_signals = []
    if manual_hypothesis:
        expansion.extend(manual_hypothesis["expansion"])
        expansion_signals.extend(manual_hypothesis["expansion"])
    differences = []
    for skill in observed_skills:
        if skill.casefold() not in jd_tech and skill.casefold() not in hard_keys:
            expansion.append(f"Consider {skill} as an expansion signal from observed team profiles")
            if skill not in expansion_signals:
                expansion_signals.append(skill)
            differences.append({"jd": "technology", "observed_pattern": skill, "action": "expand search, keep separate from hard requirements"})
    return {
        "hard_requirements": hard_keys,
        "priority": priority,
        "expansion": expansion,
        "expansion_signals": expansion_signals,
        "jd_org_differences": differences,
        "transferable_experience": observed_domains,
        "observed_previous_companies": previous_companies,
        "manual_override": manual_hypothesis,
        "boundary": "Do not reject candidates only because they differ from observed company patterns.",
    }


def _build_channel_plan(position, patterns, hypothesis):
    queries = []
    search_signals = list(hypothesis["priority"])
    for item in hypothesis.get("expansion_signals", []):
        if item not in search_signals:
            search_signals.append(item)
    for item in hypothesis["transferable_experience"]:
        if item not in search_signals:
            search_signals.append(item)
    for skill in patterns["observed_skills"]:
        if skill["value"] not in search_signals:
            search_signals.append(skill["value"])
    for signal in search_signals[:8]:
        queries.append(signal)
    if not queries:
        queries.append(position["title"])
    return {
        "jobkorea": queries,
        "saramin": queries,
        "linkedin_rps": queries,
        "rps": queries,
    }


def _observation(obs):
    item = _require_mapping(obs, "observation")
    item_type = item.get("type")
    if item_type not in {"person", "employment"}:
        raise CompanyIntelligenceError("unsupported observation type")
    evidence = _evidence(item.get("evidence"), "observation.evidence")
    confidence = item.get("confidence")
    if confidence not in ALLOWED_CONFIDENCE:
        raise CompanyIntelligenceError("observation confidence must be confirmed/inferred/tentative")
    snippet_only = bool(item.get("snippet_only", False))
    if snippet_only and confidence == "confirmed":
        raise CompanyIntelligenceError("snippet-only observation cannot be confirmed")
    return {
        **item,
        "id": _text(item.get("id"), "observation.id"),
        "type": item_type,
        "confidence": confidence,
        "snippet_only": snippet_only,
        "evidence": evidence,
        "collected_at": _instant(item.get("collected_at"), "observation.collected_at"),
    }


def _validate_manual_hypothesis(value, company, source_url, position, observations):
    if value is None:
        return None
    manual = _require_mapping(value, "manual_hypothesis")
    for flag in ("pattern_hard_filter", "organization_match_changes_jd_score"):
        if manual.get(flag) is True:
            raise CompanyIntelligenceError(f"manual_hypothesis.{flag} must be false")
    allowed_urls = {source_url}
    for item in position["hard_requirements"]:
        allowed_urls.update(item["evidence_urls"])
    for item in company["identity_evidence"]:
        allowed_urls.add(item["url"])
    for item in observations:
        for evidence in item["evidence"]:
            allowed_urls.add(evidence["url"])
    explicit_urls = []
    for key in ("evidence_urls", "source_urls"):
        if key in manual:
            explicit_urls.extend(_url_list(manual[key], f"manual_hypothesis.{key}"))
    priority = _text_list(manual.get("priority", []), "manual_hypothesis.priority")
    expansion = _text_list(manual.get("expansion", []), "manual_hypothesis.expansion")
    if (priority or expansion) and not explicit_urls:
        raise CompanyIntelligenceError("manual_hypothesis.evidence_urls required for query signals")
    for url in explicit_urls:
        if url not in allowed_urls:
            raise CompanyIntelligenceError("manual_hypothesis references URL not present in JD/company evidence")
    previous_employers = {
        item.casefold()
        for obs in observations
        if obs["type"] == "person"
        for item in _text_list(obs.get("previous_companies", []), "person.previous_companies")
    }
    for signal in priority + expansion:
        if signal.casefold() in previous_employers:
            raise CompanyIntelligenceError("manual_hypothesis query cannot be a previous employer")
    return {
        "role": _optional_text(manual.get("role")),
        "min_years": manual.get("min_years"),
        "required": _text_list(manual.get("required", []), "manual_hypothesis.required"),
        "priority": priority,
        "expansion": expansion,
        "pattern": _text_list(manual.get("pattern", []), "manual_hypothesis.pattern"),
        "weights": manual.get("weights", []),
        "run_id": _optional_text(manual.get("run_id")),
        "status": _optional_text(manual.get("status")),
        "pattern_hard_filter": bool(manual.get("pattern_hard_filter", False)),
        "organization_match_changes_jd_score": bool(manual.get("organization_match_changes_jd_score", False)),
        "company_evidence": _text_list(manual.get("company_evidence", []), "manual_hypothesis.company_evidence"),
        "evidence_urls": sorted(set(explicit_urls)),
        "boundary": "Manual hypotheses can guide discovery queries only; they do not change JD hard requirements or scoring gates.",
    }


def _collect_evidence(company, people, employment):
    seen = {}
    for item in company["identity_evidence"]:
        seen[_evidence_key(item)] = item
    for row in people + employment:
        for item in row["evidence"]:
            seen[_evidence_key(item)] = item
    return list(seen.values())


def _evidence_key(item):
    excerpt = item.get("excerpt") or ""
    excerpt_hash = hashlib.sha256(excerpt.encode("utf-8")).hexdigest()[:12]
    return (item["url"], item["observed_at"], excerpt_hash)


def _conflict_observation(observation, field, value):
    return {
        "source_observation_ids": list(observation.get("source_observation_ids", [])),
        "value": value,
        "collected_at": observation.get("collected_at"),
        "evidence_urls": [item["url"] for item in observation.get("evidence", [])],
    }


def _person_conflicted_fields(conflicts):
    out = defaultdict(set)
    for item in conflicts:
        if item.get("type") == "person_field_conflict":
            out[item["person_id"]].add(item["field"])
    return out


def _evidence(value, field):
    if not isinstance(value, list) or not value:
        raise CompanyIntelligenceError(field + " evidence required")
    out = []
    for index, item in enumerate(value):
        if isinstance(item, str):
            raise CompanyIntelligenceError(f"{field}[{index}].observed_at required")
        mapping = _require_mapping(item, f"{field}[{index}]")
        observed_at = mapping.get("observed_at")
        if not observed_at:
            raise CompanyIntelligenceError(f"{field}[{index}].observed_at required")
        evidence = {
            "url": _url(mapping.get("url"), f"{field}[{index}].url"),
            "observed_at": _instant(observed_at, f"{field}[{index}].observed_at"),
        }
        for optional in ("excerpt", "published_at", "source_label", "capture_path"):
            if optional in mapping:
                evidence[optional] = _optional_text(mapping.get(optional))
        if "asserts" in mapping:
            evidence["asserts"] = _require_mapping(mapping["asserts"], f"{field}[{index}].asserts")
        out.append(
            evidence
        )
    return out


def _url(value, field):
    text = _text(value, field)
    parsed = urlparse(text)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise CompanyIntelligenceError("unsupported URL in " + field)
    return text


def _url_list(value, field):
    if not isinstance(value, list):
        raise CompanyIntelligenceError(field + " must be a list")
    return [_url(item, f"{field}[{index}]") for index, item in enumerate(value)]


def _instant(value, field):
    text = _text(value, field)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        raise CompanyIntelligenceError(field + " must be ISO 8601") from None
    if parsed.tzinfo is None:
        raise CompanyIntelligenceError(field + " must include timezone")
    return parsed.astimezone(timezone.utc).isoformat()


def _parse(value):
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, TypeError, AttributeError):
        return None


def _freshness(evidence, as_of):
    as_of_dt = _parse(as_of)
    dates = []
    stale_dates = []
    for item in evidence:
        source_date = item.get("published_at") or item["observed_at"]
        parsed = _parse_source_date(source_date)
        if parsed is None:
            continue
        age_days = (as_of_dt - parsed).days if as_of_dt else None
        row = {
            "url": item["url"],
            "source_date": source_date,
            "age_days": age_days,
        }
        dates.append(row)
        if age_days is not None and age_days > STALE_DAYS:
            stale_dates.append(row)
    return {
        "checked_at": as_of,
        "stale_after_days": STALE_DAYS,
        "source_dates": dates,
        "stale_for_current_fact": bool(dates) and len(stale_dates) == len(dates),
    }


def _parse_source_date(value):
    if not value:
        return None
    text = str(value).strip()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
        text = text + "T00:00:00+00:00"
    elif re.fullmatch(r"\d{4}-\d{2}", text):
        text = text + "-01T00:00:00+00:00"
    parsed = _parse(text)
    if parsed is not None:
        return parsed
    return None


def _employment_matches_position(item, position):
    position_function = _normalize_match_text(position.get("function"))
    position_org = _normalize_match_text(position.get("organization"))
    item_function = _normalize_match_text(item.get("function"))
    item_org = _normalize_match_text(item.get("organization"))
    if position_function and item_function and position_function == item_function:
        return True
    if position_org and item_org and (position_org in item_org or item_org in position_org):
        return True
    if not position_function and not position_org:
        return True
    return False


def _normalize_match_text(value):
    if not value:
        return ""
    return re.sub(r"[^0-9a-z가-힣]+", " ", value.casefold()).strip()


def _text(value, field):
    if not isinstance(value, str) or not value.strip():
        raise CompanyIntelligenceError(field + " must be a nonempty string")
    return value.strip()


def _optional_text(value):
    if value is None:
        return None
    if not isinstance(value, str):
        raise CompanyIntelligenceError("optional text field must be string or null")
    value = value.strip()
    return value or None


def _text_list(value, field):
    if not isinstance(value, list):
        raise CompanyIntelligenceError(field + " must be a list")
    out = []
    for index, item in enumerate(value):
        text = _text(item, f"{field}[{index}]")
        if text not in out:
            out.append(text)
    return out


def _key(value, field):
    text = _text(value, field).casefold()
    if not re.fullmatch(r"[a-z0-9_.-]+", text):
        raise CompanyIntelligenceError(field + " must be a stable key")
    return text


def _require_mapping(value, field):
    if not isinstance(value, dict):
        raise CompanyIntelligenceError(field + " must be an object")
    return value


def _top(counter, provenance=None):
    rows = []
    for value, count in counter.most_common():
        row = {"value": value, "count": count}
        if provenance is not None:
            row["person_ids"] = sorted(provenance[value]["person_ids"])
            row["evidence_urls"] = sorted(provenance[value]["evidence_urls"])
        rows.append(row)
    return rows


def _company_key(homepage):
    parsed = urlparse(_url(homepage, "company.homepage"))
    domain = parsed.netloc.casefold()
    if domain.startswith("www."):
        domain = domain[4:]
    digest = hashlib.sha256(domain.encode("utf-8")).hexdigest()[:10]
    return _slug(domain) + "-" + digest


def _slug(value):
    lowered = value.casefold()
    slug = re.sub(r"[^a-z0-9가-힣]+", "-", lowered).strip("-")
    return slug or "company"


def _hash(payload):
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _load_snapshot(path):
    try:
        loaded = json.loads(Path(path).read_text())
    except (OSError, ValueError) as exc:
        raise CompanyIntelligenceError("corrupt cached snapshot: " + str(path)) from exc
    snapshot_hash = loaded.get("snapshot_hash")
    if not snapshot_hash:
        raise CompanyIntelligenceError("cached snapshot missing hash: " + str(path))
    without_hash = {key: value for key, value in loaded.items() if key != "snapshot_hash"}
    if _hash(without_hash) != snapshot_hash:
        raise CompanyIntelligenceError("cached snapshot hash mismatch: " + str(path))
    return loaded


def _merge_cached_observations(document, previous):
    if not previous:
        return document
    merged = json.loads(json.dumps(document, ensure_ascii=False))
    observations = []
    seen = set()
    for _, snapshot in previous:
        for item in snapshot.get("raw_observations", []):
            marker = _hash(item)
            if marker not in seen:
                observations.append(item)
                seen.add(marker)
    for item in merged["company_intelligence"].get("observations", []):
        marker = _hash(item)
        if marker not in seen:
            observations.append(item)
            seen.add(marker)
    merged["company_intelligence"]["observations"] = observations
    return merged


def _persist(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as out:
        json.dump(value, out, ensure_ascii=False, indent=2)
        out.flush()
        os.fsync(out.fileno())
    os.replace(tmp, path)


if __name__ == "__main__":
    sys.exit(main())
