"""Exercise exclusion semantics through the actual packet generation path."""
import unittest
from test_jd_registration import source, unit, write
from jd_channels.registration import build_packet
from jd_channels.units import load


class CopyPolicyTest(unittest.TestCase):
    def packet(self, text, channel):
        tmp, path = write(source([unit('D1', 'duties', 'core', text)]))
        self.addCleanup(tmp.cleanup)
        return build_packet(load(path), channel)

    def test_process_variants_are_blocked_in_both_channels(self):
        for joiner in ('/', '·', ' 또는 ', '\n또는\n', ' 및 '):
            for channel in ('saramin', 'jobkorea'):
                with self.subTest(joiner=joiner, channel=channel):
                    text = f'※ 전형 절차는 일정 및 상황에 따라 일부 추가{joiner}생략될 수 있습니다.'
                    self.assertEqual(self.packet(text, channel)['status'], 'BLOCKED')

    def test_equivalent_process_phrasing_is_blocked(self):
        for text in ('상황에 따라 면접 단계가 생략되거나 추가될 수 있습니다.',
                     '채용 과정은 필요에 따라 일부 단계를 생략할 수 있습니다.',
                     '면접 전형이 상황에 따라 추가될 수 있습니다.'):
            self.assertEqual(self.packet(text, 'saramin')['status'], 'BLOCKED')

    def test_boilerplate_is_blocked(self):
        for text in ('[지원서류]\n자유 양식 이력서 제출',
                     '📢 지원 전 확인해주세요',
                     '허위 기재 시 합격 취소', '고용 형태 / 정규직',
                     '- 정규직', '접수 기간 / 채용 시 마감',
                     '근무지 / 서초 오피스', '회사 주소: 마제스타시티 타워2 7층'):
            with self.subTest(text=text):
                self.assertEqual(self.packet(text, 'jobkorea')['status'], 'BLOCKED')

    def test_substantive_facts_remain_allowed(self):
        for text in ('서류 → 1차 → 2차 → 처우 협의 → 최종 합격',
                     '후보자 동의 후 레퍼런스 체크가 진행될 수 있습니다.',
                     '서비스에 API 기능을 추가하고 불필요한 운영 단계를 생략합니다.',
                     '필수 포트폴리오: 제품 설계 사례 2건', '경력 6년 이상',
                     '입사 후 적응을 위한 수습 3개월',
                     '정규직(상호 합의 시 계약직 전환 가능)'):
            for channel in ('saramin', 'jobkorea'):
                with self.subTest(text=text, channel=channel):
                    self.assertEqual(self.packet(text, channel)['status'], 'READY_FOR_UI')
