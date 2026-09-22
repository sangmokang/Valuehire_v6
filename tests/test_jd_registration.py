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

    def test_standing_user_exclusions_are_preserved_outside_portal_fields(self):
        tmp, p = write(source([
            unit("C1", "company", "company", "- 회사 소개"),
            unit("D1", "duties", "core", "- 업무"),
        ], excluded_units=[{
            "id": "X_COND_DEADLINE",
            "section": "conditions",
            "reason": "standing_user_exclusion: omit 채용 시 마감 boilerplate",
            "full": "- 접수 기간: 채용 시 마감",
            "source": "fixture",
        }]))
        self.addCleanup(tmp.cleanup)
        packet = build_packet(load(p), "saramin")
        self.assertEqual(packet["status"], "READY_FOR_UI")
        self.assertEqual(packet["excluded_units"][0]["id"], "X_COND_DEADLINE")
        body = packet["fields"]["offerComment"]["value"] + packet["fields"]["chargeWork"]["value"]
        self.assertNotIn("채용 시 마감", body)

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



if __name__ == "__main__":
    unittest.main()
