import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/position_packet.py'
spec = importlib.util.spec_from_file_location('position_packet', SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def packet():
    source = '주요 업무\n제품 개발 3년 이상\n자사 지원: https://example.com/apply'
    return dict(title='AI 개발자', fields=['회사 소개\n밸류커넥트를 통해 지원', '주요 업무\n제품 개발 3년 이상'],
                source_text=source, source_sha256=hashlib.sha256(source.encode()).hexdigest(),
                source_lines=source.splitlines(),
                excluded_lines=[dict(text=source.splitlines()[-1], reason='직접 지원 경로 제거')],
                allowed_additions=['회사 소개', '밸류커넥트를 통해 지원'],
                forbidden_literals=['https://example.com/apply'], limit=2000, title_limit=35)


class PacketTests(unittest.TestCase):
    def assert_rejected(self, data):
        self.assertEqual(module.validate(data)['status'], 'FAIL')

    def test_valid(self):
        self.assertEqual(module.validate(packet())['status'], 'PASS')

    def test_missing_fact_changed_number_and_order(self):
        for value in ['주요 업무', '주요 업무\n제품 개발 4년 이상', '제품 개발 3년 이상\n주요 업무']:
            with self.subTest(value=value):
                data = packet()
                data['fields'][1] = value
                self.assert_rejected(data)

    def test_unapproved_addition(self):
        data = packet()
        data['fields'][0] += '\n연봉 1억원 보장'
        self.assert_rejected(data)

    def test_source_ledger_and_hash(self):
        for key, value in [('source_sha256', '0' * 64), ('source_lines', ['주요 업무'])]:
            data = packet()
            data[key] = value
            self.assert_rejected(data)

    def test_exclusion_requires_reason_and_source(self):
        for excluded in [[dict(text='없는 줄', reason='삭제')], [dict(text='주요 업무', reason='')],
                         [dict(text='주요 업무', reason='삭제')] * 2]:
            data = packet()
            data['excluded_lines'] = excluded
            self.assert_rejected(data)

    def test_forbidden_and_brand(self):
        data = packet()
        data['fields'][0] += '\nhttps://example.com/apply'
        data['allowed_additions'].append('https://example.com/apply')
        self.assert_rejected(data)
        data = packet()
        data['fields'][0] = '회사 소개'
        self.assert_rejected(data)

    def test_field_cap_even_if_config_increased(self):
        for size in [2000, 2001, 2100]:
            data = packet()
            value = '밸류커넥트' + '가' * (size - 5)
            data['fields'][0] = value
            data['allowed_additions'] = [value]
            data['limit'] = 9999
            self.assertEqual(module.validate(data)['status'], 'PASS' if size == 2000 else 'FAIL')

    def test_utf16_cap(self):
        data = packet()
        data['fields'][0] = '밸류커넥트' + '😀' * 1000
        data['allowed_additions'] = [data['fields'][0]]
        self.assert_rejected(data)

    def test_title_boundary(self):
        for size in [35, 36]:
            data = packet()
            data['title'] = '가' * size
            data['title_limit'] = 9999
            self.assertEqual(module.validate(data)['status'], 'PASS' if size == 35 else 'FAIL')

    def test_schema(self):
        for key, value in [('fields', ['a']), ('fields', [1, 2]), ('limit', True),
                           ('title', ''), ('source_text', None), ('allowed_additions', 'x')]:
            data = packet()
            data[key] = value
            self.assert_rejected(data)

    def test_whitespace_normalization(self):
        data = packet()
        data['fields'][1] = '주요\u200b 업무\r\n제품  개발 3년 이상'
        self.assertEqual(module.validate(data)['status'], 'PASS')

    def test_readback_exact_and_missing(self):
        data = packet()
        observed = {key: copy.deepcopy(data[key]) for key in ['title', 'fields']}
        observed['fields'][0] = observed['fields'][0].replace('\n', '\r\n')
        self.assertEqual(module.readback(data, observed)['status'], 'PASS')
        observed['fields'][0] += ' '
        self.assertEqual(module.readback(data, observed)['status'], 'FAIL')
        self.assertEqual(module.readback(data, {})['status'], 'FAIL')

    def test_repeated_source_and_empty_forbidden_list(self):
        data = packet()
        data['fields'][1] += '\n주요 업무'
        self.assert_rejected(data)
        data = packet()
        data['forbidden_literals'] = []
        data['fields'][0] += '\n지원하기'
        data['allowed_additions'].append('지원하기')
        self.assert_rejected(data)

    def test_cli(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'packet.json'
            path.write_text(json.dumps(packet()), encoding='utf-8')
            result = subprocess.run([sys.executable, str(SCRIPT), 'validate', '--packet', str(path)],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(json.loads(result.stdout)['status'], 'PASS')
            path.write_text('{}', encoding='utf-8')
            result = subprocess.run([sys.executable, str(SCRIPT), 'validate', '--packet', str(path)],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertEqual(json.loads(result.stdout)['status'], 'FAIL')


if __name__ == '__main__':
    unittest.main()
