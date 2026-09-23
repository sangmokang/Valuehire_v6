"""Both runtimes must load one canonical JD skill and its executable dependencies."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class SharedJDSkillTest(unittest.TestCase):
    def test_runtime_entrypoints_resolve_to_one_source(self):
        for name in ('jd', 'jd-channels', 'position-register'):
            canonical = (ROOT / '.agents/skills' / name / 'SKILL.md').resolve(strict=True)
            for runtime in ('.codex', '.claude'):
                entry = ROOT / runtime / 'skills' / name / 'SKILL.md'
                self.assertEqual(entry.resolve(strict=True), canonical)
                self.assertEqual(entry.read_bytes(), canonical.read_bytes())

    def test_referenced_dependencies_exist(self):
        for name in ('docs/sot/jd-connected-registration.md',
                     'docs/sot/jd-aside-operations.md',
                     'scripts/jd_channels/__main__.py',
                     'scripts/jd_channels/registration.py',
                     'contracts/jd-registration.json'):
            self.assertGreater((ROOT / name).stat().st_size, 0)

    def test_no_machine_specific_fallback_or_per_runtime_logic(self):
        skill = (ROOT / '.agents/skills/jd/SKILL.md').read_text()
        self.assertNotIn('/Users/', skill)
        self.assertIn('BLOCKED_DEPENDENCY', skill)
        self.assertIn('python3 -m jd_channels packet', skill)
        self.assertIn('python3 -m jd_channels readback', skill)

    def test_linkedin_registration_requires_explicit_storage_without_send(self):
        contract = json.loads((ROOT / 'contracts/jd-registration.json').read_text())
        registration = contract['channels']['linkedin_rps']['registration']
        self.assertEqual(registration['operation'], 'message_template_save')
        self.assertTrue(registration['requires_explicit_user_request'])
        self.assertEqual(registration['visibility'], 'Anyone in my organization')
        self.assertFalse(registration['candidate_send_authorized'])
        self.assertIn('reopen', registration['completion_evidence'])


if __name__ == '__main__':
    unittest.main()
