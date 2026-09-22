"""Regression from saved JobKorea field capture on 2026-09-22."""
import unittest
from test_jd_registration import source, unit, write
from jd_channels.registration import build_packet
from jd_channels.units import load


class BulletStorageTest(unittest.TestCase):
    def test_jobkorea_substitutes_observed_unsafe_bullet_before_entry(self):
        tmp, path = write(source([unit('D1', 'duties', 'core', '• API 사업 리드')]))
        self.addCleanup(tmp.cleanup)
        packet = build_packet(load(path), 'jobkorea')
        self.assertEqual(packet['fields']['EXEC_WORK']['value'], '[주요 업무]\n- API 사업 리드')
        self.assertEqual(packet['fields']['EXEC_WORK']['portal_changes'][0]['from'], '•')
        self.assertIn('•', build_packet(load(path), 'saramin')['fields']['chargeWork']['value'])
