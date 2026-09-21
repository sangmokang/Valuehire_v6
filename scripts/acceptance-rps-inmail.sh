#!/usr/bin/env bash
# RPS InMail 골든 구조 인수 시험 (goal: docs/engineering/goal-prompts/rps-inmail-logic-rebuild-2026-09-22.md)
#
# 판정은 종료값으로만 낸다. 종료값 0 = 전 항목 PASS, 1 = 한 항목이라도 FAIL.
# 검사 대상 0개는 합격이 아니다 — 각 AC 는 최소 건수를 직접 센다.
set -uo pipefail
cd "$(dirname "$0")/.."

PASS=0; FAIL=0
run() { # run <AC 이름> <python 파일>
  local name="$1" f="$2" out rc
  out="$(python3 "$f" 2>&1 </dev/null)"; rc=$?
  if [ "$rc" -eq 0 ]; then echo "PASS $name"; PASS=$((PASS+1));
  else echo "FAIL $name (rc=$rc)"; echo "$out" | sed 's/^/     /'; FAIL=$((FAIL+1)); fi
}

TD="$(mktemp -d)"; trap 'rm -rf "$TD"' EXIT

# ── AC-0 골든이 기존 검사기에서 불합격한다는 동작 RED ────
cat > "$TD/ac0.py" <<'PY'
"""기존 API 만으로 재는 동작 RED. 볼드·섹션·불릿은 금지 대상이 아니다."""
import sys; sys.path.insert(0, 'scripts')
from pathlib import Path
from jd_channels.checks import scan_inmail
bad = []
for f in ('rps_wrtn_golden.txt', 'rps_bunjang_golden.txt'):
    t = Path(f'outputs/_golden/{f}').read_text(encoding='utf-8').strip()
    hits = sorted({h.rule for h in scan_inmail(t)})
    print(f, hits)
    if hits:
        bad.append((f, hits))
raise SystemExit(1 if bad else 0)
PY
run AC-0-골든금지0건 "$TD/ac0.py"
# ── AC-1 골든 샘플이 통과해야 한다 (양성 대조군) ─────────────────
cat > "$TD/ac1.py" <<'PY'
import sys; sys.path.insert(0, 'scripts')
from pathlib import Path
from jd_channels.checks import scan_inmail, inmail_structure
bad = []
files = ('rps_wrtn_golden.txt', 'rps_bunjang_golden.txt')
assert len(files) == 2, '검사 대상 0개는 합격이 아니다'
for f in files:
    t = Path(f'outputs/_golden/{f}').read_text(encoding='utf-8').strip()
    hits = sorted({h.rule for h in scan_inmail(t)})
    st = sorted({h.rule for h in inmail_structure(t)})
    print(f, '금지', hits, '구조', st)
    if hits or st:
        bad.append(f)
raise SystemExit(1 if bad else 0)
PY
run AC-1-골든통과 "$TD/ac1.py"

# ── AC-2 AI 티 나는 원고는 여전히 걸러야 한다 (음성 대조군) ───────
cat > "$TD/ac2.py" <<'PY'
import sys; sys.path.insert(0, 'scripts')
from jd_channels.checks import scan_inmail
bad = ("안녕하세요 전혜인 매니저님\n"
       "귀하의 경력을 주목하여 연락드립니다 \U0001F642\n"
       "{{first_name}}님께 좋은 기회가 될 것입니다\n")
rules = {h.rule for h in scan_inmail(bad)}
want = {'INMAIL_NAME_HARDCODED', 'INMAIL_STOCK_PHRASE', 'INMAIL_EMOJI', 'INMAIL_RAW_VAR'}
missing = want - rules
print('잡은 규칙', sorted(rules))
if missing:
    print('놓친 규칙', sorted(missing)); raise SystemExit(1)
if len(rules) < 4:
    print('규칙 4개 미만'); raise SystemExit(1)
PY
run AC-2-AI티차단 "$TD/ac2.py"

# ── AC-3 생성 원고가 골든 구조를 따라야 한다 ─────────────────────
cat > "$TD/ac3.py" <<'PY'
import re, sys; sys.path.insert(0, 'scripts')
from jd_channels.units import load
from jd_channels.render import render
bad = []
for u in ('wrtn__finance-data-analyst', 'bunjang__core-product-pm'):
    b = render(load(f'outputs/_units/{u}.json'), 'linkedin_rps').body
    sec = len(re.findall(r'^■ ', b, re.M))
    bul = len(re.findall(r'^• ', b, re.M))
    bold = len(re.findall(r'\*\*', b)) // 2
    print(u, '섹션', sec, '불릿', bul, '볼드', bold, '자', len(b))
    if not (sec >= 4 and bul >= 8 and bold >= 5 and len(b) <= 1899):
        bad.append(u)
raise SystemExit(1 if bad else 0)
PY
run AC-3-생성구조 "$TD/ac3.py"

# ── AC-4 핵심 조건이 남아야 한다 ─────────────────────────────────
cat > "$TD/ac4.py" <<'PY'
import re, sys; sys.path.insert(0, 'scripts')
from jd_channels.units import load
from jd_channels.render import render
MUST = {
    'wrtn__finance-data-analyst': [
        ('연차', ['5년']),
        ('대체 인정 조건', ['준하는 경험', '5년+']),
        ('평판 조회 단계', ['Reference Check', '레퍼런스']),
        ('고용형태', ['정규직']),
    ],
    'bunjang__core-product-pm': [
        ('성과 중심 사고', ['Outcome']),
        ('최소 실험 단위', ['MVP']),
        ('협업 범위', ['Cross-functional']),
        ('고용형태', ['정규직']),
    ],
}
bad = []
for u, reqs in MUST.items():
    b = render(load(f'outputs/_units/{u}.json'), 'linkedin_rps').body
    for label, alts in reqs:
        if not any(a in b for a in alts):
            print(f'{u}: 누락 {label} {alts}'); bad.append((u, label))
    if u.startswith('bunjang') and not re.search(r'^※ ', b, re.M):
        print(f'{u}: 평가 우선순위 ※ 줄 누락'); bad.append((u, 'note'))
if not bad:
    print('핵심 조건 전건 보존')
raise SystemExit(1 if bad else 0)
PY
run AC-4-핵심조건 "$TD/ac4.py"

# ── counter-AC 제3의 JD 에서도 같은 구조가 나와야 한다 ───────────
cat > "$TD/cac1.py" <<'PY'
"""골든 하드코딩 방지. rps_* 필드가 하나도 없는 가상 JD 도 같은 구조여야 한다."""
import json, re, sys, tempfile; sys.path.insert(0, 'scripts')
from pathlib import Path
from jd_channels.units import load
from jd_channels.render import render
def unit(uid, sec, full, **kw):
    return {'id': uid, 'section': sec, 'kind': 'core', 'meaning': f'fixture {uid}',
            'full': full, 'compact': full, 'source': 'FIXTURE', **kw}
units = [unit('T1', 'team', '가상팀은 가상 제품의 전 여정을 설계합니다.'),
         unit('R1', 'role', '가상 역할의 본질을 정의하고 운영합니다.')]
units += [unit(f'W{i}', 'duties', f'- 가상 업무 {i}') for i in range(1, 6)]
units += [unit(f'Q{i}', 'requirements', f'- 가상 자격 {i}') for i in range(1, 4)]
units += [unit(f'P{i}', 'preferred', f'- 가상 우대 {i}') for i in range(1, 4)]
units += [unit('N1', 'conditions', '- 정규직 / 경력 3년 이상'),
          unit('S1', 'process', '- 서류 → 면접 → 최종')]
doc = {'company': '가상컴퍼니', 'position': 'Fixture Engineer',
       'source_url': 'fixture://none', 'captured_at': '2026-01-01T00:00:00+00:00',
       'source_status': 'FIXTURE', 'jd_id': 'FIXTURE', 'company_slug': 'fixture',
       'position_slug': 'engineer', 'units': units}
with tempfile.TemporaryDirectory() as tmp:
    p = Path(tmp) / 'u.json'
    p.write_text(json.dumps(doc, ensure_ascii=False), encoding='utf-8')
    b = render(load(p), 'linkedin_rps').body
sec = len(re.findall(r'^■ ', b, re.M)); bul = len(re.findall(r'^• ', b, re.M))
print('제3 JD 섹션', sec, '불릿', bul, '자', len(b))
raise SystemExit(0 if sec >= 4 and bul >= 8 else 1)
PY
run CAC-1-제3JD구조 "$TD/cac1.py"

# ── counter-AC 영문 용어를 한글로 풀면 실패해야 한다 (G4) ────────
cat > "$TD/cac2.py" <<'PY'
import sys; sys.path.insert(0, 'scripts')
from jd_channels.checks import inmail_structure
ok = "\n".join([
    "안녕하세요. 테크 전문 서치펌 밸류커넥트의 헤드헌터 강상모입니다.", "",
    "현재 **가상컴퍼니** Data Analyst 포지션을 제안드립니다.", "",
    "가상컴퍼니는 **사용자 100만+**를 보유한 회사입니다.", "",
    "■ Position | Data Analyst", "", "**Mission**", "KPI/Metric 체계를 만듭니다.", "",
    "■ Key Responsibilities",
    "• KPI 정의", "• SQL 추출", "• BI 구축", "• Reporting", "",
    "■ Requirements", "• **5년+**", "• SQL", "• Finance Domain", "",
    "■ Preferred", "• **FinOps**", "• dbt", "• **Audit Trail**", "",
    "■ Process", "서류 → 실무 → Culture Fit → Reference Check → Offer", "",
    "관심 있으시면 LinkedIn 수락 또는 간단한 회신만 주셔도 상세 JD를 공유드리겠습니다."])
translated = ok.replace('Reference Check', '평판 조회').replace('Culture Fit', '조직 적합도')
a = sorted({h.rule for h in inmail_structure(ok)})
b = sorted({h.rule for h in inmail_structure(translated)})
print('원본', a, '/ 한글로 푼 판', b)
if a: print('정상 원고가 불합격했다'); raise SystemExit(1)
if 'INMAIL_TERM_TRANSLATED' not in b: print('G4 위반을 못 잡았다'); raise SystemExit(1)
PY
run CAC-2-영문용어보존 "$TD/cac2.py"

# ── counter-AC 산문 일색 원고는 구조 검사에서 불합격해야 한다 ────
cat > "$TD/cac3.py" <<'PY'
"""2026-09-22 에 만든 산문 8문단 판을 다시 넣으면 불합격해야 한다."""
import sys; sys.path.insert(0, 'scripts')
from pathlib import Path
from jd_channels.checks import inmail_structure
p = Path('outputs/run-20260921/wrtn__finance-data-analyst__199492/linkedin_rps_inmail.txt')
if not p.exists():
    print('산문판 없음 — 음성 대조군을 세울 수 없다'); raise SystemExit(1)
rules = sorted({h.rule for h in inmail_structure(p.read_text(encoding='utf-8').strip())})
print('산문판 구조 판정', rules)
raise SystemExit(0 if rules else 1)
PY
run CAC-3-산문판불합격 "$TD/cac3.py"

# ── AC-5 회귀 ────────────────────────────────────────────────────
echo "--- AC-5 회귀: python3 -m unittest tests.test_jd_channels"
if python3 -m unittest tests.test_jd_channels </dev/null 2>&1 | tail -3 | grep -q '^OK'; then
  echo "PASS AC-5-회귀"; PASS=$((PASS+1))
else
  echo "FAIL AC-5-회귀"; python3 -m unittest tests.test_jd_channels </dev/null 2>&1 | tail -20 | sed 's/^/     /'; FAIL=$((FAIL+1))
fi

echo
echo "VERDICT: $([ "$FAIL" -eq 0 ] && echo PASS || echo FAIL)"
echo "PASS=$PASS FAIL=$FAIL TOTAL=$((PASS+FAIL))"
echo "CHECKED: $((PASS+FAIL))"
[ "$((PASS+FAIL))" -ge 9 ] || { echo "검사 항목이 8개 미만 — 검사 대상 0개는 합격이 아니다"; exit 2; }
exit $([ "$FAIL" -eq 0 ] && echo 0 || echo 1)
