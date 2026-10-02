import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from jd_channels.registration import build_packet, counts, readback_compare  # noqa: E402
from jd_channels.units import UnitError, load  # noqa: E402


def unit(uid, section, kind, full, **kw):
    return {
        "id": uid,
        "section": section,
        "kind": kind,
        "meaning": f"meaning {uid}",
        "full": full,
        "compact": kw.pop("compact", full),
        "source": "fixture",
        **kw,
    }


def source(units, **kw):
    base = {
        "company": "테스트회사",
        "position": "QA Manager",
        "source_url": "https://example.invalid/job",
        "captured_at": "2026-09-22T00:00:00+09:00",
        "source_status": "OK",
        "jd_id": "fixture-1",
        "company_slug": "testco",
        "position_slug": "qa-manager",
        "units": units,
    }
    base.update(kw)
    return base


def write(payload):
    tmp = tempfile.TemporaryDirectory()
    p = Path(tmp.name) / "source.json"
    p.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return tmp, p


class RegistrationPacketTest(unittest.TestCase):
    def test_saramin_two_2000_fields_preserve_all_units_once(self):
        tmp, p = write(source([
            unit("C1", "company", "company", "- 회사 연혁: 2021년 설립"),
            unit("T1", "team", "core", "- AI QA 문화를 만드는 팀"),
            unit("D1", "duties", "core", "- 테스트 케이스 작성 및 수행"),
            unit("Q1", "requirements", "core", "- SDLC 품질관리 5년 이상"),
            unit("P1", "preferred", "core", "- 생성형 AI 제품 경험"),
            unit("R1", "process", "core", "- 서류 전형 > 실무 인터뷰 > 합격 안내"),
        ]))
        self.addCleanup(tmp.cleanup)
        packet = build_packet(load(p), "saramin")
        self.assertEqual(packet["status"], "READY_FOR_UI")
        self.assertEqual(set(packet["fields"]), {"hiringTitle", "offerComment", "chargeWork"})
        self.assertLessEqual(packet["fields"]["offerComment"]["counts"]["codepoints"], 2000)
        self.assertLessEqual(packet["fields"]["chargeWork"]["counts"]["codepoints"], 2000)
        assigned = [uid for field in packet["assignments"].values() for uid in field]
        self.assertEqual(assigned, ["C1", "T1", "R1", "D1", "Q1", "P1"])
        text = packet["fields"]["offerComment"]["value"] + packet["fields"]["chargeWork"]["value"]
        self.assertIn("밸류커넥트를 통해", text)
        self.assertNotIn("https://", text)

    def test_jobkorea_has_separate_proposal_and_two_position_fields(self):
        tmp, p = write(source([
            unit("C1", "company", "company", "- 회사 소개: 글로벌 AI 서비스"),
            unit("T1", "team", "core", "- Global팀은 제품 관점에서 사업을 실행"),
            unit("G1", "growth", "extra", "- 글로벌 스케일 문제 해결 경험"),
            unit("D1", "duties", "core", "- 비즈니스 기회를 프로덕트로 전환"),
            unit("Q1", "requirements", "core", "- 5년 이상 프로덕트 경력"),
            unit("P1", "preferred", "core", "- 크로스보더 이커머스 경험"),
            unit("R1", "process", "core", "- 서류 전형 > 1차 인터뷰 > 최종 합격"),
        ]))
        self.addCleanup(tmp.cleanup)
        packet = build_packet(load(p), "jobkorea")
        self.assertEqual(packet["status"], "READY_FOR_UI")
        self.assertEqual(packet["proposal_status"], "NOT_VERIFIED")
        self.assertIn("proposalMessage", packet["fields"])
        self.assertIn("EXEC_WORK", packet["fields"])
        self.assertIn("ST", packet["fields"])
        self.assertLessEqual(packet["fields"]["proposalMessage"]["counts"]["codepoints"], 3000)
        self.assertLessEqual(packet["fields"]["EXEC_WORK"]["counts"]["codepoints"], 1000)
        self.assertLessEqual(packet["fields"]["ST"]["counts"]["codepoints"], 1000)
        assigned = [uid for field in packet["assignments"].values() for uid in field]
        self.assertEqual(assigned, ["C1", "T1", "G1", "R1", "D1", "Q1", "P1"])

    def test_explicit_user_exclusions_are_preserved_outside_portal_fields(self):
        tmp, p = write(source([
            unit("C1", "company", "company", "- 회사 소개"),
            unit("D1", "duties", "core", "- 업무"),
        ], excluded_units=[{
            "id": "X_DOCUMENTS",
            "section": "documents",
            "reason": "explicit_user_exclusion: user requested support-documents boilerplate removal",
            "full": "- 이력서는 자유 양식으로 제출",
            "source": "fixture",
        }]))
        self.addCleanup(tmp.cleanup)
        packet = build_packet(load(p), "saramin")
        self.assertEqual(packet["status"], "READY_FOR_UI")
        self.assertEqual(packet["excluded_units"][0]["id"], "X_DOCUMENTS")
        self.assertEqual(packet["presentation_contract"]["company_intro"], "bullet_first_concise")
        body = packet["fields"]["offerComment"]["value"] + packet["fields"]["chargeWork"]["value"]
        self.assertNotIn("이력서는 자유 양식", body)

    def test_jobkorea_overflow_whole_units_to_proposal(self):
        long = "- " + "주요업무" * 300
        tmp, p = write(source([
            unit("C1", "company", "company", "- 회사 소개"),
            unit("D1", "duties", "core", long),
            unit("Q1", "requirements", "core", "- 필수 요건"),
            unit("P1", "preferred", "core", "- 우대 사항"),
        ]))
        self.addCleanup(tmp.cleanup)
        packet = build_packet(load(p), "jobkorea")
        self.assertEqual(packet["status"], "READY_FOR_UI")
        self.assertIn("D1", packet["assignments"]["proposalMessage"])
        self.assertNotIn("D1", packet["assignments"]["EXEC_WORK"])
        self.assertIn("D1", packet["permanent_overflow_units"])

    def test_refuses_non_ok_source_status(self):
        tmp, p = write(source([unit("Q1", "requirements", "core", "- 필수")], source_status="NEEDS_SOURCE_REVIEW"))
        self.addCleanup(tmp.cleanup)
        with self.assertRaises(UnitError):
            build_packet(load(p), "saramin")

    def test_excluded_units_require_explicit_user_reason(self):
        tmp, p = write(source([
            unit("D1", "duties", "core", "- 업무"),
        ], excluded_units=[{
            "id": "X1",
            "section": "documents",
            "reason": "renderer_drop",
            "full": "- 삭제",
            "source": "fixture",
        }]))
        self.addCleanup(tmp.cleanup)
        with self.assertRaisesRegex(UnitError, "explicit_user_exclusion"):
            load(p)

    def test_rejects_url_email_and_direct_apply_text(self):
        tmp, p = write(source([
            unit("Q1", "requirements", "core", "- 지원은 apply@example.com 으로 해주세요"),
        ]))
        self.addCleanup(tmp.cleanup)
        packet = build_packet(load(p), "saramin")
        self.assertEqual(packet["status"], "BLOCKED")
        self.assertIn("FORBIDDEN_TEXT", packet["errors"][0])

    def test_saramin_blocks_ascii_apostrophe_before_html_entity_corruption(self):
        tmp, p = write(source([
            unit("C1", "company", "company", "- 회사 비전: Let's build AI"),
            unit("D1", "duties", "core", "- 업무"),
        ]))
        self.addCleanup(tmp.cleanup)
        packet = build_packet(load(p), "saramin")
        self.assertEqual(packet["status"], "BLOCKED")
        self.assertTrue(any("UNSUPPORTED_APOSTROPHE:offerComment" in e for e in packet["errors"]))

    def test_readback_position_complete_does_not_verify_proposal(self):
        tmp, p = write(source([
            unit("D1", "duties", "core", "- 업무"),
            unit("P1", "preferred", "core", "- 우대"),
        ]))
        self.addCleanup(tmp.cleanup)
        packet = build_packet(load(p), "jobkorea")
        observed = {
            "channel": "jobkorea",
            "position_id": "1600000",
            "readback_kind": "persisted_reopen",
            "fresh_saved_position": True,
            "fields": {
                "GI_PSTN": packet["fields"]["GI_PSTN"]["value"],
                "EXEC_WORK": packet["fields"]["EXEC_WORK"]["value"],
                "ST": packet["fields"]["ST"]["value"],
            },
        }
        result = readback_compare(packet, observed)
        self.assertEqual(result["position_status"], "COMPLETE")
        self.assertEqual(result["proposal_status"], "NOT_VERIFIED")
        self.assertEqual(result["status"], "PARTIAL")

    def test_readback_rejects_blocked_packet(self):
        tmp, p = write(source([
            unit("Q1", "requirements", "core", "- 지원은 apply@example.com 으로 해주세요"),
        ]))
        self.addCleanup(tmp.cleanup)
        packet = build_packet(load(p), "saramin")
        self.assertEqual(packet["status"], "BLOCKED")
        observed = {
            "channel": "saramin",
            "position_id": "1833000",
            "readback_kind": "persisted_reopen",
            "fresh_saved_position": True,
            "fields": {name: field["value"] for name, field in packet["fields"].items()},
        }
        result = readback_compare(packet, observed)
        self.assertEqual(result["status"], "FAIL")
        self.assertTrue(any("PACKET_NOT_READY" in e for e in result["errors"]))

    def test_readback_rejects_packet_metadata_tamper(self):
        tmp, p = write(source([
            unit("C1", "company", "company", "- 회사 소개"),
            unit("D1", "duties", "core", "- 업무"),
        ]))
        self.addCleanup(tmp.cleanup)
        packet = build_packet(load(p), "saramin")

        tampered = copy.deepcopy(packet)
        tampered["fields"]["offerComment"]["persistent"] = False
        observed = {
            "channel": "saramin",
            "position_id": "1833000",
            "readback_kind": "persisted_reopen",
            "fresh_saved_position": True,
            "fields": {
                "hiringTitle": tampered["fields"]["hiringTitle"]["value"],
                "chargeWork": tampered["fields"]["chargeWork"]["value"],
            },
        }
        result = readback_compare(tampered, observed)
        self.assertEqual(result["status"], "FAIL")
        self.assertTrue(any("PACKET_PERSISTENT_TAMPER:offerComment" in e for e in result["errors"]))

        tampered = copy.deepcopy(packet)
        tampered["fields"]["hiringTitle"]["value"] = "X" * 80
        tampered["fields"]["hiringTitle"]["counts"]["codepoints"] = 2
        observed = {
            "channel": "saramin",
            "position_id": "1833000",
            "readback_kind": "persisted_reopen",
            "fresh_saved_position": True,
            "fields": {name: field["value"] for name, field in tampered["fields"].items()},
        }
        result = readback_compare(tampered, observed)
        self.assertEqual(result["status"], "FAIL")
        self.assertTrue(any("PACKET_VALUE_OVER_LIMIT:hiringTitle" in e for e in result["errors"]))

    def test_readback_rejects_excluded_units_tamper(self):
        tmp, p = write(source([
            unit("C1", "company", "company", "- 회사 소개"),
            unit("D1", "duties", "core", "- 업무"),
        ], excluded_units=[{
            "id": "X_DOCUMENTS",
            "section": "documents",
            "reason": "explicit_user_exclusion: user requested removal",
            "full": "- 지원서류",
            "source": "fixture",
        }]))
        self.addCleanup(tmp.cleanup)
        packet = build_packet(load(p), "saramin")
        tampered = copy.deepcopy(packet)
        tampered["excluded_units"] = []
        observed = {
            "channel": "saramin",
            "position_id": "1833000",
            "readback_kind": "persisted_reopen",
            "fresh_saved_position": True,
            "fields": {name: field["value"] for name, field in tampered["fields"].items()},
        }
        result = readback_compare(tampered, observed)
        self.assertEqual(result["status"], "FAIL")
        self.assertTrue(any("PACKET_SOURCE_HASH_MISMATCH" in e for e in result["errors"]))

    def test_readback_rejects_noncanonical_packet_value_and_field_errors(self):
        tmp, p = write(source([
            unit("C1", "company", "company", "- 회사 소개"),
            unit("D1", "duties", "core", "- 업무"),
        ]))
        self.addCleanup(tmp.cleanup)
        packet = build_packet(load(p), "saramin")

        tampered = copy.deepcopy(packet)
        tampered["fields"]["offerComment"]["value"] = "A→B"
        tampered["fields"]["offerComment"]["counts"] = counts("AB")
        observed = {
            "channel": "saramin",
            "position_id": "1833000",
            "readback_kind": "persisted_reopen",
            "fresh_saved_position": True,
            "fields": {name: field["value"] for name, field in tampered["fields"].items()},
        }
        result = readback_compare(tampered, observed)
        self.assertEqual(result["status"], "FAIL")
        self.assertTrue(any("PACKET_VALUE_NOT_CANONICAL:offerComment" in e for e in result["errors"]))

        tampered = copy.deepcopy(packet)
        tampered["fields"]["offerComment"]["errors"] = ["FORGED_FIELD_ERROR"]
        observed["fields"] = {name: field["value"] for name, field in tampered["fields"].items()}
        result = readback_compare(tampered, observed)
        self.assertEqual(result["status"], "FAIL")
        self.assertTrue(any("PACKET_FIELD_ERRORS:offerComment" in e for e in result["errors"]))

    def test_readback_rejects_noncanonical_observed_value_over_raw_limit(self):
        tmp, p = write(source([
            unit("D1", "duties", "core", "- 업무"),
            unit("P1", "preferred", "core", "- 우대"),
        ]))
        self.addCleanup(tmp.cleanup)
        packet = build_packet(load(p), "jobkorea")
        tampered = copy.deepcopy(packet)
        tampered["fields"]["GI_PSTN"]["value"] = "é" * 50
        tampered["fields"]["GI_PSTN"]["counts"] = counts("é" * 50)
        observed = {
            "channel": "jobkorea",
            "position_id": "1600000",
            "readback_kind": "persisted_reopen",
            "fresh_saved_position": True,
            "fields": {
                "GI_PSTN": "e\u0301" * 50,
                "EXEC_WORK": tampered["fields"]["EXEC_WORK"]["value"],
                "ST": tampered["fields"]["ST"]["value"],
            },
        }
        result = readback_compare(tampered, observed)
        self.assertEqual(result["position_status"], "FAIL")
        self.assertEqual(result["status"], "FAIL")
        self.assertTrue(any("OBSERVED_VALUE_NOT_CANONICAL:GI_PSTN" in e for e in result["errors"]))

    def test_readback_rejects_assignment_without_unit_text_and_zero_units(self):
        tmp, p = write(source([
            unit("C1", "company", "company", "- 회사 소개"),
            unit("D1", "duties", "core", "- 업무"),
        ]))
        self.addCleanup(tmp.cleanup)
        packet = build_packet(load(p), "saramin")

        tampered = copy.deepcopy(packet)
        tampered["fields"]["offerComment"]["value"] = "후속 절차는 밸류커넥트를 통해 안내드립니다."
        tampered["fields"]["offerComment"]["counts"] = counts(tampered["fields"]["offerComment"]["value"])
        observed = {
            "channel": "saramin",
            "position_id": "1833000",
            "readback_kind": "persisted_reopen",
            "fresh_saved_position": True,
            "fields": {name: field["value"] for name, field in tampered["fields"].items()},
        }
        result = readback_compare(tampered, observed)
        self.assertEqual(result["status"], "FAIL")
        self.assertTrue(any("PACKET_UNIT_TEXT_MISSING:offerComment:C1" in e for e in result["errors"]))

        tampered = copy.deepcopy(packet)
        tampered["units"] = []
        tampered["assignments"] = {"offerComment": [], "chargeWork": []}
        observed["fields"] = {name: field["value"] for name, field in tampered["fields"].items()}
        result = readback_compare(tampered, observed)
        self.assertEqual(result["status"], "FAIL")
        self.assertIn("PACKET_ZERO_UNITS", result["errors"])

    def test_readback_rejects_observed_extra_fields_and_assignment_tamper(self):
        tmp, p = write(source([
            unit("C1", "company", "company", "- 회사 소개"),
            unit("D1", "duties", "core", "- 업무"),
        ]))
        self.addCleanup(tmp.cleanup)
        packet = build_packet(load(p), "saramin")
        observed = {
            "channel": "saramin",
            "position_id": "1833000",
            "readback_kind": "persisted_reopen",
            "fresh_saved_position": True,
            "fields": {name: field["value"] for name, field in packet["fields"].items()} | {"unknown": "x"},
        }
        result = readback_compare(packet, observed)
        self.assertEqual(result["status"], "FAIL")
        self.assertIn("OBSERVED_EXTRA_FIELDS:['unknown']", result["errors"])

        tampered = copy.deepcopy(packet)
        tampered["assignments"]["offerComment"].append("D1")
        observed["fields"].pop("unknown")
        result = readback_compare(tampered, observed)
        self.assertEqual(result["status"], "FAIL")
        self.assertTrue(any("PACKET_UNIT_ASSIGNMENT_MISMATCH" in e for e in result["errors"]))

    def test_readback_requires_persisted_reopen_for_position(self):
        tmp, p = write(source([
            unit("D1", "duties", "core", "- 업무"),
            unit("P1", "preferred", "core", "- 우대"),
        ]))
        self.addCleanup(tmp.cleanup)
        packet = build_packet(load(p), "jobkorea")
        observed = {
            "channel": "jobkorea",
            "position_id": "1600000",
            "readback_kind": "editor",
            "fields": {
                "GI_PSTN": packet["fields"]["GI_PSTN"]["value"],
                "EXEC_WORK": packet["fields"]["EXEC_WORK"]["value"],
                "ST": packet["fields"]["ST"]["value"],
            },
        }
        result = readback_compare(packet, observed)
        self.assertEqual(result["position_status"], "FAIL")
        self.assertEqual(result["status"], "FAIL")
        self.assertIn("POSITION_NOT_PERSISTED_REOPEN", result["errors"])
        self.assertIn("FRESH_SAVED_POSITION_REQUIRED", result["errors"])

    def test_readback_requires_explicit_fresh_saved_position(self):
        tmp, p = write(source([
            unit("D1", "duties", "core", "- 업무"),
            unit("P1", "preferred", "core", "- 우대"),
        ]))
        self.addCleanup(tmp.cleanup)
        packet = build_packet(load(p), "jobkorea")
        observed = {
            "channel": "jobkorea",
            "position_id": "1600000",
            "readback_kind": "persisted_reopen",
            "fields": {
                "GI_PSTN": packet["fields"]["GI_PSTN"]["value"],
                "EXEC_WORK": packet["fields"]["EXEC_WORK"]["value"],
                "ST": packet["fields"]["ST"]["value"],
            },
        }
        result = readback_compare(packet, observed)
        self.assertEqual(result["position_status"], "FAIL")
        self.assertEqual(result["status"], "FAIL")
        self.assertIn("FRESH_SAVED_POSITION_REQUIRED", result["errors"])

    def test_jobkorea_transient_mismatch_does_not_poison_position(self):
        tmp, p = write(source([
            unit("C1", "company", "company", "- 회사 소개"),
            unit("D1", "duties", "core", "- 업무"),
            unit("P1", "preferred", "core", "- 우대"),
        ]))
        self.addCleanup(tmp.cleanup)
        packet = build_packet(load(p), "jobkorea")
        observed = {
            "channel": "jobkorea",
            "position_id": "1600000",
            "proposal_id": "proposal-1",
            "readback_kind": "persisted_reopen",
            "fresh_saved_position": True,
            "fields": {
                "GI_PSTN": packet["fields"]["GI_PSTN"]["value"],
                "EXEC_WORK": packet["fields"]["EXEC_WORK"]["value"],
                "ST": packet["fields"]["ST"]["value"],
                "proposalMessage": "112default",
            },
        }
        result = readback_compare(packet, observed)
        self.assertEqual(result["position_status"], "COMPLETE")
        self.assertEqual(result["proposal_status"], "NOT_SAVED")
        self.assertEqual(result["status"], "PARTIAL")
        self.assertEqual(result["mismatches"], ["proposalMessage"])

    def test_jobkorea_accepts_explicit_disabled_title_binding(self):
        tmp, p = write(source([
            unit("D1", "duties", "core", "- 업무"),
            unit("P1", "preferred", "core", "- 우대"),
        ]))
        self.addCleanup(tmp.cleanup)
        packet = build_packet(load(p), "jobkorea")
        observed = {
            "channel": "jobkorea",
            "position_id": "1600000",
            "readback_kind": "persisted_reopen",
            "fresh_saved_position": True,
            "fields": {
                "EXEC_WORK": packet["fields"]["EXEC_WORK"]["value"],
                "ST": packet["fields"]["ST"]["value"],
            },
            "field_bindings": {
                "GI_PSTN": {
                    "kind": "existing_disabled_title",
                    "disabled": True,
                    "value": packet["fields"]["GI_PSTN"]["value"],
                    "canonical_identity": {
                        "company": packet["source"]["company"],
                        "position": packet["source"]["position"],
                    },
                }
            },
        }
        result = readback_compare(packet, observed)
        self.assertEqual(result["position_status"], "COMPLETE")
        self.assertEqual(result["status"], "PARTIAL")
        self.assertIn("GI_PSTN", result["bound_fields"])

    def test_jobkorea_rejects_arbitrary_disabled_title_binding(self):
        tmp, p = write(source([
            unit("D1", "duties", "core", "- 업무"),
            unit("P1", "preferred", "core", "- 우대"),
        ]))
        self.addCleanup(tmp.cleanup)
        packet = build_packet(load(p), "jobkorea")
        observed = {
            "channel": "jobkorea",
            "position_id": "1600000",
            "readback_kind": "persisted_reopen",
            "fresh_saved_position": True,
            "fields": {
                "EXEC_WORK": packet["fields"]["EXEC_WORK"]["value"],
                "ST": packet["fields"]["ST"]["value"],
            },
            "field_bindings": {
                "GI_PSTN": {
                    "kind": "existing_disabled_title",
                    "disabled": True,
                    "value": "임의 제목",
                    "canonical_identity": {
                        "company": packet["source"]["company"],
                        "position": packet["source"]["position"],
                    },
                }
            },
        }
        result = readback_compare(packet, observed)
        self.assertEqual(result["position_status"], "FAIL")
        self.assertEqual(result["status"], "FAIL")
        self.assertIn("OBSERVED_MISSING_FIELDS:['GI_PSTN']", result["errors"])

    def test_jobkorea_uses_st_spare_for_overflow_core_and_process(self):
        duty = "- P&L/손익 기반 우선순위 조정 " + "업무 " * 32
        requirement = "- " + "필수요건 " * 190
        preferred = "- " + "우대경험 " * 25
        tmp, p = write(source([
            unit("C1", "company", "company", "- 회사 소개"),
            unit("BW01", "duties", "core", duty),
            unit("BQ01", "requirements", "core", requirement),
            unit("BP01", "preferred", "core", preferred),
            unit("BR01", "process", "core", "- 서류 전형 > 1차 인터뷰 > 최종 합격"),
        ], position="Product Manager(Global)"))
        self.addCleanup(tmp.cleanup)
        packet = build_packet(load(p), "jobkorea")

        self.assertEqual(packet["status"], "READY_FOR_UI")
        self.assertEqual(packet["assignments"]["EXEC_WORK"], ["BQ01"])
        self.assertEqual(packet["assignments"]["ST"], ["BW01", "BP01", "BR01"])
        self.assertNotIn("BW01", packet["assignments"]["proposalMessage"])
        self.assertNotIn("BR01", packet["assignments"]["proposalMessage"])
        self.assertLessEqual(packet["fields"]["EXEC_WORK"]["counts"]["codepoints"], 1000)
        self.assertLessEqual(packet["fields"]["ST"]["counts"]["codepoints"], 1000)
        self.assertIn("[주요 업무]", packet["fields"]["ST"]["value"])
        self.assertIn("[채용 절차]", packet["fields"]["ST"]["value"])
        self.assertEqual(packet["permanent_overflow_units"], [])


    def test_packet_level_errors_and_source_hash_cannot_claim_complete(self):
        tmp, path = write(source([unit('D1', 'duties', 'core', '품질을 검증합니다.')]))
        self.addCleanup(tmp.cleanup)
        packet = build_packet(load(path), 'saramin')
        observed = {'channel': 'saramin', 'position_id': 'fixture-position',
                    'readback_kind': 'persisted_reopen', 'fresh_saved_position': True,
                    'fields': {k: v['value'] for k, v in packet['fields'].items()}}
        for change in ({'errors': ['UNRESOLVED_SOURCE']}, {'source_hash': 'tampered'}):
            with self.subTest(change=change):
                bad = copy.deepcopy(packet)
                bad.update(change)
                self.assertEqual(readback_compare(bad, observed)['status'], 'FAIL')


    def test_source_identity_and_proposal_proof_are_separate(self):
        tmp, path = write(source([unit('D1', 'duties', 'core', '품질을 검증합니다.')]))
        self.addCleanup(tmp.cleanup)
        packet = build_packet(load(path), 'jobkorea')
        observed = {'channel': 'jobkorea', 'position_id': 'fixture', 'proposal_id': 'p1',
                    'readback_kind': 'persisted_reopen', 'fresh_saved_position': True,
                    'fields': {k: v['value'] for k, v in packet['fields'].items()}}
        self.assertNotEqual(readback_compare(packet, observed)['status'], 'COMPLETE')
        observed['fresh_saved_proposal'] = True
        self.assertEqual(readback_compare(packet, observed)['status'], 'COMPLETE')
        packet['source']['company'] = '다른회사'
        self.assertEqual(readback_compare(packet, observed)['status'], 'FAIL')

    def test_bare_direct_apply_paths_are_blocked(self):
        for text in ('example.co.kr/careers', '당사 홈페이지에서 지원해 주시기 바랍니다',
                     '채용 페이지에서 접수해 주세요'):
            with self.subTest(text=text):
                tmp, path = write(source([unit('D1', 'duties', 'core', text)]))
                self.addCleanup(tmp.cleanup)
                self.assertEqual(build_packet(load(path), 'saramin')['status'], 'BLOCKED')
        tmp, path = write(source([unit('D1', 'duties', 'core', 'ASP.NET 및 Socket.IO 개발 경험')]))
        self.addCleanup(tmp.cleanup)
        self.assertEqual(build_packet(load(path), 'saramin')['status'], 'READY_FOR_UI')

    def test_cli_json_roundtrip_and_invalid_channel_exit(self):
        tmp, path = write(source([unit('D1', 'duties', 'core', '검증 업무')]))
        self.addCleanup(tmp.cleanup)
        packet = build_packet(load(path), 'saramin')
        observed = {'channel': 'saramin', 'position_id': 'fixture',
                    'readback_kind': 'persisted_reopen', 'fresh_saved_position': True,
                    'fields': {k: v['value'] for k, v in packet['fields'].items()}}
        folder = Path(tmp.name)
        for invalid in (False, True):
            if invalid:
                packet['channel'] = observed['channel'] = 'linkedin_rps'
            for name, value in [('packet', packet), ('observed', observed)]:
                (folder / (name + '.json')).write_text(json.dumps(value, ensure_ascii=False))
            code = ('import sys;sys.path.insert(0,"scripts");'
                    'from jd_channels.registration import main;sys.exit(main())')
            result = subprocess.run([sys.executable, '-c', code, 'readback', '--packet',
                                     str(folder / 'packet.json'), '--observed',
                                     str(folder / 'observed.json'), '--output',
                                     str(folder / 'result.json')], cwd=ROOT, capture_output=True)
            self.assertEqual(result.returncode, 2 if invalid else 0, result.stderr)
            data = json.loads((folder / 'result.json').read_text())
            self.assertEqual(data['status'], 'FAIL' if invalid else 'COMPLETE')


if __name__ == "__main__":
    unittest.main()
