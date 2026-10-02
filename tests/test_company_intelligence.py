import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


spec = importlib.util.spec_from_file_location(
    "company_intelligence",
    Path(__file__).parents[1] / "scripts/company_intelligence.py",
)
company_intelligence = importlib.util.module_from_spec(spec)
spec.loader.exec_module(company_intelligence)


def evidence(url="https://example.com/evidence", **kw):
    item = {"url": url, "observed_at": "2026-09-22T00:00:00+09:00"}
    item.update(kw)
    return [item]


def jd(company_name="번개장터", status="confirmed", homepage="https://team.bgzt.co.kr"):
    return {
        "source_url": "https://team.bgzt.co.kr/job_posting/NPLSRGT2",
        "captured_at": "2026-09-22T00:00:00+09:00",
        "company": {
            "name": company_name,
            "english_name": "Bungaejangter",
            "brand_names": ["번개장터"],
            "homepage": homepage,
            "industry": "C2C commerce",
            "location": "Seoul",
            "identity_status": status,
            "identity_evidence": evidence("https://team.bgzt.co.kr"),
        },
        "position": {
            "title": "Backend Engineer",
            "organization": "Platform",
            "function": "engineering",
            "seniority": "senior",
            "location": "Seoul",
            "hard_requirements": [
                {"key": "python", "label": "Python", "evidence_urls": ["https://team.bgzt.co.kr/job_posting/NPLSRGT2"]},
                {"key": "traffic", "label": "large traffic", "evidence_urls": ["https://team.bgzt.co.kr/job_posting/NPLSRGT2"]},
            ],
            "preferred": [{"key": "commerce", "label": "commerce domain"}],
            "technologies": ["Python"],
        },
    }


def payload(*observations, company_name="번개장터", status="confirmed", homepage="https://team.bgzt.co.kr"):
    return {
        "run_id": "run-1",
        "jd": jd(company_name=company_name, status=status, homepage=homepage),
        "company_intelligence": {
            "as_of": "2026-09-22T00:00:00+09:00",
            "observations": list(observations),
        },
    }


def person(person_id="person-1", name="김검색", url="https://www.linkedin.com/in/person-1", **kw):
    data = {
        "id": person_id,
        "type": "person",
        "name": name,
        "profile_url": url,
        "current_title": "Senior Backend Engineer",
        "function": "engineering",
        "seniority": "senior",
        "skills": ["Python", "Go"],
        "domains": ["commerce", "large traffic"],
        "previous_companies": ["Naver"],
        "education": "public profile school",
        "confidence": "confirmed",
        "snippet_only": False,
        "evidence": evidence(url),
        "collected_at": "2026-09-22T00:00:00+09:00",
    }
    data.update(kw)
    return data


def employment(person_id="person-1", status="current", url="https://www.linkedin.com/in/person-1", **kw):
    data = {
        "id": "employment-" + person_id,
        "type": "employment",
        "person_id": person_id,
        "company_name": "번개장터",
        "employment_status": status,
        "title": "Senior Backend Engineer",
        "organization": "Platform",
        "function": "engineering",
        "seniority": "senior",
        "start": "2024-01",
        "end": None if status == "current" else "2025-01",
        "confidence": "confirmed",
        "snippet_only": False,
        "evidence": evidence(url),
        "collected_at": "2026-09-22T00:00:00+09:00",
    }
    data.update(kw)
    return data


class CompanyIntelligenceTest(unittest.TestCase):
    def test_new_company_persists_immutable_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = company_intelligence.run(payload(person(), employment()), tmp)
            first = Path(result["snapshot_path"])
            self.assertTrue(first.exists())
            second = Path(company_intelligence.run(payload(person(), employment()), tmp)["snapshot_path"])
            self.assertEqual(first, second)
            snapshot = json.loads(first.read_text())
            self.assertEqual(snapshot["company"]["identity_status"], "confirmed")

    def test_existing_company_cache_is_loaded_with_staleness(self):
        with tempfile.TemporaryDirectory() as tmp:
            old = payload(person("old", "이전사람"), employment("old"))
            old["company_intelligence"]["as_of"] = "2026-01-01T00:00:00+09:00"
            company_intelligence.run(old, tmp)
            fresh = company_intelligence.run(payload(
                person("new", "새사람", "https://www.linkedin.com/in/new"),
                employment("new", url="https://www.linkedin.com/in/new"),
            ), tmp)
            self.assertEqual(fresh["cache"]["previous_snapshot_count"], 1)
            self.assertTrue(fresh["cache"]["stale"])
            snapshot = json.loads(Path(fresh["snapshot_path"]).read_text())
            self.assertEqual({item["id"] for item in snapshot["raw_observations"]},
                             {"old", "employment-old", "new", "employment-new"})

    def test_same_company_name_different_homepage_uses_distinct_company_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            a = company_intelligence.run(payload(person(), employment(), homepage="https://team.bgzt.co.kr"), tmp)
            b = company_intelligence.run(payload(person(), employment(), homepage="https://other.example.com"), tmp)
            self.assertNotEqual(a["cache"]["company_key"], b["cache"]["company_key"])

    def test_corrupt_cached_snapshot_is_rejected_not_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            first = company_intelligence.run(payload(person(), employment()), tmp)
            Path(first["snapshot_path"]).write_text("{bad json")
            with self.assertRaisesRegex(company_intelligence.CompanyIntelligenceError, "corrupt cached snapshot"):
                company_intelligence.run(payload(person("new"), employment("new")), tmp)

    def test_cached_snapshot_hash_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            first = company_intelligence.run(payload(person(), employment()), tmp)
            path = Path(first["snapshot_path"])
            data = json.loads(path.read_text())
            data["people"][0]["name"] = "tampered but valid json"
            path.write_text(json.dumps(data, ensure_ascii=False))
            with self.assertRaisesRegex(company_intelligence.CompanyIntelligenceError, "hash mismatch"):
                company_intelligence.run(payload(person("new"), employment("new")), tmp)

    def test_ambiguous_company_keeps_people_out_of_hypothesis(self):
        result = company_intelligence.build_snapshot(payload(person(), employment(), status="ambiguous"))
        self.assertEqual(result["status"], "blocked_company_identity")
        self.assertEqual(result["search_hypothesis"]["priority"], [])

    def test_sparse_startup_profiles_are_not_generalized(self):
        result = company_intelligence.build_snapshot(payload(person()))
        self.assertIn("sample_size", result["talent_patterns"]["limits"][0])

    def test_current_and_former_employment_are_explicit(self):
        result = company_intelligence.build_snapshot(payload(
            person("a", "현재"),
            employment("a", "current"),
            person("b", "과거", "https://www.linkedin.com/in/former"),
            employment("b", "former", "https://www.linkedin.com/in/former"),
            person("c", "미확인", "https://www.linkedin.com/in/unknown"),
            employment("c", "unknown", "https://www.linkedin.com/in/unknown", end=None),
        ))
        statuses = {item["person_id"]: item["employment_status"] for item in result["employment"]}
        self.assertEqual(statuses, {"a": "current", "b": "former", "c": "unknown"})
        confirmed_org = result["organization"]["confirmed_relationships"]
        self.assertEqual(confirmed_org, [{"organization": "Platform", "person_ids": ["a"]}])

    def test_rejects_mismatched_company_and_current_role_with_end_date(self):
        bad_company = employment(company_name="다른회사")
        with self.assertRaisesRegex(company_intelligence.CompanyIntelligenceError, "company mismatch"):
            company_intelligence.build_snapshot(payload(person(), bad_company))
        ended_current = employment(end="2025-01")
        with self.assertRaisesRegex(company_intelligence.CompanyIntelligenceError, "current employment cannot have end"):
            company_intelligence.build_snapshot(payload(person(), ended_current))

    def test_jd_and_org_pattern_difference_expands_without_changing_hard_requirements(self):
        result = company_intelligence.build_snapshot(payload(
            person(skills=["Go"], domains=["large traffic"]),
            employment(),
        ))
        self.assertIn("python", result["search_hypothesis"]["hard_requirements"])
        expanded = " ".join(result["search_hypothesis"]["expansion"])
        self.assertIn("Go", expanded)
        self.assertNotIn("go", result["search_hypothesis"]["hard_requirements"])

    def test_same_person_multiple_sources_merged_by_stable_url_not_name(self):
        same = person("alias", "김검색", "https://github.com/person-1", skills=["Python"])
        same["same_person_as"] = "person-1"
        same["identity_evidence"] = evidence("https://example.com/person-identity")
        other = person("other", "김검색", "https://www.linkedin.com/in/other")
        result = company_intelligence.build_snapshot(payload(person(), same, other))
        names = [item["name"] for item in result["people"]]
        self.assertEqual(len(names), 2)
        self.assertEqual(names.count("김검색"), 2)

    def test_same_article_url_can_support_multiple_distinct_people_without_profile_url(self):
        article_url = "https://blog.example.com/global-team-interview"
        jayden = person("article-jayden", "Jayden")
        jayden.pop("profile_url")
        jayden["evidence"] = evidence(article_url)
        riri = person("article-riri", "Riri")
        riri.pop("profile_url")
        riri["evidence"] = evidence(article_url)
        result = company_intelligence.build_snapshot(payload(jayden, riri))
        self.assertEqual({item["id"] for item in result["people"]}, {"article-jayden", "article-riri"})
        for item in result["people"]:
            self.assertEqual(item["profile_urls"], [])

    def test_changed_profile_facts_preserve_conflict(self):
        changed = person(skills=["Kotlin"], current_title="Staff Backend Engineer")
        changed["same_person_as"] = "person-1"
        changed["identity_evidence"] = evidence("https://example.com/person-identity")
        result = company_intelligence.build_snapshot(payload(person(skills=["Python"]), changed))
        conflicts = result["conflicts"]
        self.assertIn({"person_id": "person-1", "field": "skills"}, [
            {"person_id": item["person_id"], "field": item["field"]} for item in conflicts
        ])
        conflict = next(item for item in conflicts if item["person_id"] == "person-1" and item["field"] == "skills")
        self.assertEqual(len(conflict["observations"]), 2)
        self.assertTrue(all("collected_at" in item and "evidence_urls" in item for item in conflict["observations"]))

    def test_missing_or_invalid_evidence_rejected(self):
        bad = person()
        bad["evidence"] = []
        with self.assertRaisesRegex(company_intelligence.CompanyIntelligenceError, "evidence"):
            company_intelligence.build_snapshot(payload(bad))
        bad_url = person(url="javascript:alert(1)")
        with self.assertRaisesRegex(company_intelligence.CompanyIntelligenceError, "unsupported URL"):
            company_intelligence.build_snapshot(payload(bad_url))
        missing_time = person()
        missing_time["evidence"] = [{"url": "https://example.com/no-time"}]
        with self.assertRaisesRegex(company_intelligence.CompanyIntelligenceError, "observed_at"):
            company_intelligence.build_snapshot(payload(missing_time))

    def test_search_plan_uses_patterns_for_channel_queries(self):
        result = company_intelligence.build_snapshot(payload(
            person("a", previous_companies=["Naver"], skills=["Python", "Go"], domains=["commerce"]),
            employment("a"),
        ))
        queries = result["channel_search_plan"]["linkedin_rps"]
        self.assertTrue(any("commerce" in item for item in queries))
        self.assertFalse(any("Consider" in item for item in queries))
        self.assertFalse(any("Naver" in item for item in queries))
        self.assertEqual(result["talent_patterns"]["observed_previous_companies"][0]["person_ids"], ["a"])

    def test_manual_hypothesis_drives_natural_channel_queries_without_changing_hard_requirements(self):
        data = payload(person("a", previous_companies=["Naver"], skills=["Go"], domains=["commerce"]), employment("a"))
        data["manual_hypothesis"] = {
            "role": "Global Team Lead",
            "priority": ["크로스보더", "글로벌 커머스"],
            "expansion": ["플랫폼 사업개발"],
            "required": ["해외향 사업 리드"],
            "evidence_urls": ["https://team.bgzt.co.kr/job_posting/NPLSRGT2"],
            "pattern_hard_filter": False,
            "organization_match_changes_jd_score": False,
        }
        result = company_intelligence.build_snapshot(data)
        queries = result["channel_search_plan"]["jobkorea"]
        self.assertTrue(any("크로스보더" in item for item in queries))
        self.assertTrue(any("플랫폼 사업개발" in item for item in queries))
        self.assertEqual(result["search_hypothesis"]["hard_requirements"], ["python", "traffic"])
        self.assertNotIn("Naver", " ".join(queries))

    def test_manual_hypothesis_rejects_unlinked_source_url(self):
        data = payload(person(), employment())
        data["manual_hypothesis"] = {
            "priority": ["크로스보더"],
            "evidence_urls": ["https://unlinked.example.com/evidence"],
        }
        with self.assertRaisesRegex(company_intelligence.CompanyIntelligenceError, "manual_hypothesis references URL"):
            company_intelligence.build_snapshot(data)

    def test_manual_hypothesis_rejects_gating_flags(self):
        for field in ("pattern_hard_filter", "organization_match_changes_jd_score"):
            data = payload(person(), employment())
            data["manual_hypothesis"] = {
                "priority": ["크로스보더"],
                "evidence_urls": ["https://team.bgzt.co.kr/job_posting/NPLSRGT2"],
                field: True,
            }
            with self.assertRaisesRegex(company_intelligence.CompanyIntelligenceError, field):
                company_intelligence.build_snapshot(data)

    def test_manual_hypothesis_rejects_queries_without_explicit_evidence_urls(self):
        data = payload(person(), employment())
        data["manual_hypothesis"] = {
            "priority": ["크로스보더"],
            "expansion": [],
            "evidence_urls": [],
        }
        with self.assertRaisesRegex(company_intelligence.CompanyIntelligenceError, "manual_hypothesis.evidence_urls required"):
            company_intelligence.build_snapshot(data)

    def test_manual_hypothesis_rejects_previous_employer_as_direct_query(self):
        data = payload(person(previous_companies=["Naver"]), employment())
        data["manual_hypothesis"] = {
            "priority": ["Naver"],
            "evidence_urls": ["https://team.bgzt.co.kr/job_posting/NPLSRGT2"],
        }
        with self.assertRaisesRegex(company_intelligence.CompanyIntelligenceError, "previous employer"):
            company_intelligence.build_snapshot(data)

    def test_patterns_use_only_current_confirmed_company_people(self):
        current = person("current", skills=["QA"], domains=["mobile testing"], previous_companies=["Line"])
        former = person("former", "과거", "https://www.linkedin.com/in/former", skills=["Python"], domains=["AI"])
        tentative = person("tentative", "잠정", "https://www.linkedin.com/in/tentative",
                           confidence="tentative", skills=["Rust"], domains=["infra"])
        result = company_intelligence.build_snapshot(payload(
            current, employment("current"),
            former, employment("former", "former", "https://www.linkedin.com/in/former"),
            tentative, employment("tentative", "unknown", "https://www.linkedin.com/in/tentative"),
        ))
        plan = " ".join(result["channel_search_plan"]["linkedin_rps"])
        self.assertIn("mobile testing", plan)
        self.assertNotIn("AI", plan)
        self.assertNotIn("Python", plan)
        self.assertNotIn("Line", plan)

    def test_function_mismatch_does_not_seed_position_specific_queries(self):
        data = payload(
            person("eng", skills=["BackendOnly"], domains=["AI agent"]),
            employment("eng"),
        )
        data["jd"]["position"]["function"] = "quality assurance"
        data["jd"]["position"]["title"] = "QA Manager"
        data["jd"]["position"]["organization"] = "QA"
        result = company_intelligence.build_snapshot(data)
        plan = " ".join(result["channel_search_plan"]["jobkorea"])
        self.assertNotIn("BackendOnly", plan)
        self.assertNotIn("AI agent", plan)
        self.assertEqual(result["talent_patterns"]["relevant_current_employee_sample_size"], 0)

    def test_stale_current_employment_and_status_conflicts_do_not_contribute_patterns(self):
        old_evidence = evidence(
            "https://example.com/old-interview",
            observed_at="2026-09-22T00:00:00+09:00",
            published_at="2025-01-01",
        )
        stale_person = person("stale", skills=["AncientSkill"], domains=["old domain"], evidence=old_evidence)
        stale_employment = employment("stale", evidence=old_evidence)
        conflict_person = person("conflict", url="https://www.linkedin.com/in/conflict", skills=["ConflictSkill"], domains=["conflict"])
        result = company_intelligence.build_snapshot(payload(
            stale_person,
            stale_employment,
            conflict_person,
            employment("conflict", status="current", url="https://www.linkedin.com/in/conflict"),
            employment("conflict", status="former", url="https://www.linkedin.com/in/conflict", end=None),
        ))
        plan = " ".join(result["channel_search_plan"]["jobkorea"])
        self.assertNotIn("AncientSkill", plan)
        self.assertNotIn("ConflictSkill", plan)
        self.assertTrue(any(item["type"] == "employment_status_conflict" for item in result["conflicts"]))

    def test_former_employment_allows_unknown_end_date(self):
        result = company_intelligence.build_snapshot(payload(
            person("former", url="https://www.linkedin.com/in/former"),
            employment("former", status="former", url="https://www.linkedin.com/in/former", end=None),
        ))
        self.assertIsNone(result["employment"][0]["end"])

    def test_snippet_only_cannot_confirm_key_fact(self):
        snippet = person(snippet_only=True, confidence="confirmed")
        with self.assertRaisesRegex(company_intelligence.CompanyIntelligenceError, "snippet"):
            company_intelligence.build_snapshot(payload(snippet))

    def test_unknown_observation_type_and_unsupported_identity_merge_rejected(self):
        with self.assertRaisesRegex(company_intelligence.CompanyIntelligenceError, "unsupported observation type"):
            company_intelligence.build_snapshot(payload({"id": "x", "type": "team"}))
        alias = person("alias", "김검색", "https://github.com/person-1")
        alias["same_person_as"] = "person-1"
        with self.assertRaisesRegex(company_intelligence.CompanyIntelligenceError, "identity_evidence"):
            company_intelligence.build_snapshot(payload(person(), alias))

    def test_evidence_retains_excerpt_published_at_and_assertions(self):
        item = person(evidence=evidence("https://example.com/profile",
                                        excerpt="PM at company",
                                        published_at="2025-12-01",
                                        source_label="profile",
                                        asserts={"current_title": "PM at company"}))
        result = company_intelligence.build_snapshot(payload(item))
        self.assertEqual(result["people"][0]["evidence"][0]["excerpt"], "PM at company")
        self.assertEqual(result["people"][0]["evidence"][0]["asserts"]["current_title"], "PM at company")

    def test_top_level_evidence_preserves_same_url_distinct_excerpts(self):
        article_url = "https://blog.example.com/global-team-interview"
        jayden = person("article-jayden", "Jayden", evidence=evidence(article_url, excerpt="Jayden runs global marketing"))
        jayden.pop("profile_url")
        riri = person("article-riri", "Riri", evidence=evidence(article_url, excerpt="Riri works on localization"))
        riri.pop("profile_url")
        result = company_intelligence.build_snapshot(payload(jayden, riri))
        excerpts = [item.get("excerpt") for item in result["evidence"] if item["url"] == article_url]
        self.assertEqual(excerpts, ["Jayden runs global marketing", "Riri works on localization"])

    def test_stale_or_conflicted_person_fields_do_not_seed_patterns(self):
        stale_profile = person(
            "stale-person",
            skills=["LegacySkill"],
            domains=["legacy domain"],
            evidence=evidence("https://example.com/old-profile", published_at="2025-01-01"),
        )
        fresh_employment = employment("stale-person", evidence=evidence("https://example.com/current-employment"))
        conflicted = person("conflicted", url="https://www.linkedin.com/in/conflicted", skills=["Python"])
        changed = person("changed", url="https://github.com/conflicted", skills=["Kotlin"])
        changed["same_person_as"] = "conflicted"
        changed["identity_evidence"] = evidence("https://example.com/conflicted-identity")
        result = company_intelligence.build_snapshot(payload(
            stale_profile,
            fresh_employment,
            conflicted,
            changed,
            employment("conflicted", url="https://www.linkedin.com/in/conflicted"),
        ))
        plan = " ".join(result["channel_search_plan"]["jobkorea"])
        self.assertNotIn("LegacySkill", plan)
        self.assertNotIn("legacy domain", plan)
        self.assertNotIn("Python", plan)
        self.assertNotIn("Kotlin", plan)

    def test_cli_writes_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "input.json"
            input_path.write_text(json.dumps(payload(person(), employment()), ensure_ascii=False))
            out_path = Path(tmp) / "summary.json"
            rc = company_intelligence.main([
                "--input", str(input_path),
                "--store-dir", str(Path(tmp) / "store"),
                "--summary", str(out_path),
            ])
            self.assertEqual(rc, 0)
            self.assertTrue(json.loads(out_path.read_text())["ok"])


if __name__ == "__main__":
    unittest.main()
