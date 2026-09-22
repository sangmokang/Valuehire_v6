# 착수 프롬프트 — RPS InMail 작성 로직 재수립 (2026-09-22)

/ clear 이후 이 파일만 읽고 시작한다. 이전 대화 맥락을 가정하지 않는다.

## 0. 한 줄

2026-09-22에 만든 RPS InMail 작성 로직이 **사장님 골든 샘플과 정반대**였다.
검사기가 골든 샘플을 불합격시킨다. 골든에서 규칙을 역산해 다시 세운다.

## 1. 무엇이 틀렸나 — 실측

```bash
python3 - <<'PY'
import sys; sys.path.insert(0,'scripts')
from pathlib import Path
from jd_channels.checks import scan_inmail, inmail_tone
for f in ('rps_wrtn_golden.txt','rps_bunjang_golden.txt'):
    t=Path(f'outputs/_golden/{f}').read_text().strip()
    print(f, sorted({h.rule for h in scan_inmail(t)}), inmail_tone(t))
PY
```

현재 출력(고치기 전 기준선):

```
rps_wrtn_golden.txt     ['INMAIL_MARKDOWN'] {'bullet_ratio': 0.444, 'ending_repeat': 0.143, ...}
rps_bunjang_golden.txt  ['INMAIL_MARKDOWN'] {'bullet_ratio': 0.462, 'ending_repeat': 0.074, ...}
```

→ 사장님이 실제로 쓰는 원고 2건을 내 검사기가 둘 다 불합격시킨다. 검사기가 틀렸다.

| 항목 | 골든(정답) | 2026-09-22에 내가 만든 것 | 결과 |
|---|---|---|---|
| 구조 | `■ 섹션` 5개 + `•` 불릿 | 산문 8문단, 불릿 0개 | 정반대 |
| 불릿 비율 | 0.44~0.46 | 0.0 | SOT L4·L5가 "0에 가까워야"로 규정 |
| 볼드 `**` | 7~12개 | 0개 | `INMAIL_MARKDOWN`으로 금지시킴 |
| 어미 반복률 | 0.074~0.143 | 0.333 | AI 티는 내 쪽이 더 심했다 |
| 길이 | 1,067~1,308자 | 1,360자 | 골든이 더 짧고 정보 밀도가 높다 |

## 2. 골든에서 역산한 실제 규칙

### 2.1 뼈대 (두 골든 공통)

```
안녕하세요. 테크 전문 서치펌 밸류커넥트의 헤드헌터 강상모입니다.

현재 **{회사명}** {포지션명} 포지션을 제안드립니다.

{회사 2~3문장 압축 — 제품·규모·성장 숫자를 볼드로}

■ Position | {포지션명}

**Mission**
{이 역할의 본질 1~2문장}
{이 포지션이 무엇과 다른지 한 문장 — "단순 재무분석보다는 ... 역량이 중요한 포지션입니다"}

■ Key Responsibilities
• {5개 내외}

■ Requirements   (또는 ■ Looking for)
• {3~4개}

■ Preferred
• {3~4개}

※ {원문 Note의 평가 우선순위}

■ Process
{단계 → 단계 → ... 한 줄}

{소프트 터치 1문장 — 이직 의사 없어도 봐도 좋다}

관심 있으시면 LinkedIn 수락 또는 간단한 회신만 주셔도 상세 JD와 조직 관련 내용을 공유드리겠습니다.
```

### 2.2 문체 규칙 (골든 역산)

| # | 규칙 | 근거 |
|---|---|---|
| G1 | **섹션 헤더는 `■ `** 로 시작하고 5개 내외 | 두 골든 모두 5개 |
| G2 | **불릿은 `• `** 를 쓴다. 불릿 비율 0.35~0.55 가 정상 | 0.444 / 0.462 |
| G3 | **`**볼드**` 를 쓴다.** 숫자·핵심 역량·포지션명에 건다. 7~12개 | 12 / 7 |
| G4 | **영문 업계 용어를 한글로 풀지 않는다** — KPI/Metric, SQL/Query, BI/Data Governance, FinOps, DW/BI, Audit Trail, Cross-functional, MVP, OKR, Reference Check, Offer, Culture Fit | 두 골든 전반 |
| G5 | **호칭은 "테크 전문 서치펌 밸류커넥트의 헤드헌터 강상모"** — "전문", "헤드헌터"를 빼지 않는다 | 두 골든 첫 줄 |
| G6 | **회사 소개는 2~3문장**으로 압축한다. 불릿으로 7줄 늘어놓지 않는다 | 두 골든 |
| G7 | **네거티브 지표를 넣지 않는다** — 영업손실, 인원수는 InMail 본문에서 뺀다. 매출·성장·투자·사용자 규모만 | 골든에 영업손실·인원 없음 |
| G8 | **`Mission` 블록**에 역할의 본질과 "이 포지션이 무엇과 다른지"를 쓴다 | 두 골든 |
| G9 | **원문 Note(평가 우선순위)는 `※` 한 줄**로 보존한다 | 번개장터 골든 `※ 중고거래 경험 자체보다...` |
| G10 | **클로징은 "LinkedIn 수락 또는 간단한 회신"** — 이력서 요구를 앞세우지 않는다 | 두 골든 마지막 줄 |
| G11 | **소프트 터치는 클로징 직전**에 둔다. 도입부에 넣어 늘어뜨리지 않는다 | 뤼튼 골든 |
| G12 | 길이는 **1,000~1,400자**가 정상 범위. 1,899자는 상한이지 목표가 아니다 | 1,067 / 1,308 |

### 2.3 긴 JD 압축 기준 (번개장터 4,166자 → 1,067자)

원문의 A/B/C 축과 Note는 **이름을 유지한 채** 한 줄로 접는다.
- `A. 서비스 기능 기획/출시 (Feature Delivery)` + 3줄 → `• 신규 Feature 기획·출시 및 Data 기반 실험/고도화`
- `[Note] 중고거래 도메인 경험보다...` → `※ 중고거래 경험 자체보다 **구조적 문제 해결 및 실험 역량**을 더 중요하게 봅니다.`
- 성장 기회 6줄 → 회사 소개 문단의 `누적 가입자 **2천만+, DAU 100만+**` 로 흡수

**접어도 사라지면 안 되는 것**: 필수/우대 구분, 연차, 대체 인정 조건, 고용형태, 전형 단계, Note의 평가 우선순위.

## 3. 고칠 파일

| 파일 | 무엇을 |
|---|---|
| `scripts/jd_channels/checks.py` | `INMAIL_MARKDOWN` 삭제(볼드·`■`·`•`는 정상). `inmail_tone` 의 해석을 뒤집는다 — 불릿 비율이 **너무 낮으면** 경고 |
| `scripts/jd_channels/render.py` | RPS 프로파일을 산문 병합이 아니라 **섹션+불릿 구조**로 렌더하도록 교체 |
| `docs/sot/linkedin-rps-inmail.md` | L4·L5 전면 교체. "불릿 없이 이어지는 글" → G1~G12 |
| `~/.claude/skills/jd-channels/SKILL.md` | §3.7 전면 교체 |
| `tests/test_jd_channels.py` | `test_inmail_rejects_ai_tells`, `test_inmail_good_body_passes` 재작성 |
| `outputs/_units/*.json` | RPS 렌더에 쓸 영문 용어 보존 표현 추가 |

## 4. 인수 기준 (실행 명령 + 기대 출력)

### AC-1 골든 샘플이 통과해야 한다 (양성 대조군)

```bash
python3 - <<'PY'
import sys; sys.path.insert(0,'scripts')
from pathlib import Path
from jd_channels.checks import scan_inmail
bad=[]
for f in ('rps_wrtn_golden.txt','rps_bunjang_golden.txt'):
    t=Path(f'outputs/_golden/{f}').read_text().strip()
    h=sorted({x.rule for x in scan_inmail(t)})
    print(f, h)
    if h: bad.append(f)
raise SystemExit(1 if bad else 0)
PY
```
기대: 두 줄 모두 `[]`, 종료값 0. **하나라도 판정이 뜨면 실패.**

### AC-2 AI 티 나는 원고는 여전히 걸러야 한다 (음성 대조군)

같은 검사기에 아래를 넣으면 **최소 4개 규칙**이 떠야 한다.
```
안녕하세요 전혜인 매니저님
귀하의 경력을 주목하여 연락드립니다 🙂
{{first_name}}님께 좋은 기회가 될 것입니다
```
기대: `INMAIL_NAME_HARDCODED`, `INMAIL_STOCK_PHRASE`, `INMAIL_EMOJI`, `INMAIL_RAW_VAR` 포함.

### AC-3 생성 원고가 골든 구조를 따라야 한다

```bash
python3 -c "
import sys,re; sys.path.insert(0,'scripts')
from jd_channels.units import load
from jd_channels.render import render
for u in ('wrtn__finance-data-analyst','bunjang__core-product-pm'):
    b=render(load(f'outputs/_units/{u}.json'),'linkedin_rps').body
    print(u, '섹션',len(re.findall(r'^■ ',b,re.M)), '불릿',len(re.findall(r'^• ',b,re.M)), '볼드',len(re.findall(r'\*\*',b))//2, '자',len(b))
"
```
기대: 각 줄에서 섹션 ≥4, 불릿 ≥8, 볼드 ≥5, 자 ≤1899.

### AC-4 핵심 조건이 남아야 한다

두 원고에서 아래가 모두 발견돼야 한다.
- 뤼튼: `5년`, `준하는 경험` 또는 `5년+`, `Reference Check` 또는 `레퍼런스`
- 번개장터: `Outcome`, `MVP`, `Cross-functional`, `※` 로 시작하는 평가 우선순위 줄

### AC-5 회귀

```bash
python3 -m unittest tests.test_jd_channels
```
기대: `OK`, 실패 0건. 기존 25개 중 InMail 관련 4개는 재작성 대상이다.

### counter-AC (가짜 합격 시나리오)

- 검사기에서 `INMAIL_MARKDOWN`만 지우고 렌더러는 그대로 두면 AC-1은 통과하지만 AC-3이 실패한다. 둘 다 통과해야 한다.
- 골든 샘플을 그대로 출력하도록 하드코딩하면 AC-1~4를 통과한다. **번개장터·뤼튼 두 JD 모두에서 unit 데이터로부터 렌더**돼야 하며, 세 번째 JD(임의 fixture)를 넣어도 같은 구조가 나와야 한다.
- 불릿 비율만 맞추고 영문 용어를 한글로 풀면 G4 위반이다. AC-4로 잡는다.

## 5. 하지 말 것

- RPS 등록(`Update current`)은 로직이 AC를 모두 통과한 뒤에만 다시 한다. 지금 저장된 템플릿은 2026-09-22에 교체한 산문판이며 골든 기준에 맞지 않는다.
- Send 버튼은 어떤 경우에도 누르지 않는다.
- 사람인·잡코리아 원고 구조는 이번 범위가 아니다. 그쪽은 포털 필드 구조가 달라 산문+불릿 혼합이 맞다.

## 6. 미해결로 남은 것 (이번 재수립과 별개)

- 사람인 중복 2건(2026.06.22 / 2026.06.19, 발송 이력 0건) 종료 미완료. 사람인에는 삭제 기능이 없고 "종료"만 있다.
- 잡코리아 중복 1건(ID 1455314, 그룹 1413734) 삭제 미완료. 백업은 `artifacts/portal-edit-20260922/jobkorea-1455314-backup.txt`.
- RPS 템플릿 `[제안]뤼튼, Finance Data Analyst (FP&A) ver1.0`(소유자 Sanghyuk Lee)이 별도로 존재. 타인 소유라 건드리지 않았다.

## 7. 참고 파일

- 골든 원문: `outputs/_golden/rps_wrtn_golden.txt`, `outputs/_golden/rps_bunjang_golden.txt`
- JD 원문: `outputs/_sources/wrtn__finance-data-analyst.json`, `outputs/_sources/bunjang__core-product-pm.json`
- 현재 포털 저장본 장부: `artifacts/portal-edit-20260922/ledger.md`
- RPS 저장 절차 상세: `~/.claude/skills/linkedin-rps-jd-set-builder/SKILL.md` (R0 Send 금지, R11 Update current, R12 visibility)
