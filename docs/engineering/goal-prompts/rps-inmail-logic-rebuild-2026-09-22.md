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

## 8. PR #104 인계 재개 계약 — 2026-09-22

현재 결론: 전체 합격 및 병합 가능 판정은 금지합니다. 기능 시험, 검사 신뢰성, 저장소 CI, 병합 준비를 따로 판정합니다. 과거 성공 출력은 현재 실행 증거를 대신하지 않습니다.

판단 근거: 시작 HEAD는 `baf20dc65426e664041d3eee2dddedab29e87dc1`, 원격 base는 `fc6beedc78019862bc2f1b3bf4c4ad3bbd8e845b`입니다. 작업트리는 clean이었습니다. main 미커밋 79개 파일/심링크를 저장소 밖 `Valuehire_v6-session-backup-20260922-101700`에 복사하고 파일 SHA-256/링크 대상을 대조했습니다. main은 수정하지 않습니다.

위험등급 L3. 읽은 정본: strict-workflow.md, coding-principles.md, principles.yaml, verification-commands.md, git-workflow.md, linkedin-rps-inmail.md. AGENTS.md/CLAUDE.md 물리 파일과 work-unit-policy.yaml은 이 작업트리에 없습니다. 제공된 AGENTS 지침을 적용하며 누락 정책을 임의 생성하지 않습니다. 코드 한도는 P11 hard 600줄입니다.

### 이번 작업 단위와 계약

- WU1: When 출력만 필수조건을 삭제·추가·의미 변경하면 조건 검사는 실패해야 합니다. 동의 표현/빈 조건/선택 조건/기존 fixture의 정상 범위를 함께 시험합니다. 입력은 기존 UnitDoc와 본문 문자열, 출력은 Hit 목록이며 JSON/DB/API 스키마 변경은 없습니다. 반례: 원문까지 같이 바꾸고 보존 성공이라고 주장하기, 조건 종류만 일치시키기.
- WU2: When 검사 핵심 파일이 base 대비 추가·변경·삭제되면 외부에서 보존한 작은 비교기는 `VERIFICATION_CORE_CHANGED` 검토 필요 상태를 반환해야 합니다. 입력은 검토자가 확인한 불변 base/head SHA, 출력은 변경 경로와 종료값입니다. 잘못된 ref/조회 오류는 실패 처리합니다. 비핵심 변경 대조군은 통과해야 합니다. 반례: PASS/VERDICT/CHECKED 출력 위조, 비교기·기준 ref·워크플로 동시 변조. 새 파일은 기존 base에 없는 이상 이미 신뢰된 비교기가 아닙니다. 선행 병합/외부 필수 검사 설정 없이는 신뢰성 해결로 표시하지 않습니다.
- WU3: When 저장된 RPS ver2를 새로 조회하면 저장 전 canonical 본문과 회사·직무·조건·이메일·URL을 대조해야 합니다. 목록만 확인/로컬 재렌더/저장 알림은 성공이 아닙니다. 허용 정규화는 확인된 서식과 줄바꿈만이며 숫자·조건·URL을 변경하지 않습니다. 원본 부재나 접근 불가는 미검증으로 보존합니다. 후보 발송 금지.
- WU4: When 최신 SHA CI가 실패하면 기존 문제라도 Repository CI=FAIL, Merge readiness=NOT_READY여야 합니다. suppression 연장·약화·기능 PR에 만료 해결 혼합 금지.

### 검증 및 중단 경계

원칙 로드/검사 원문은 `private-reviews/startup.log`에 명령·시각·SHA·세션과 함께 보존합니다. 인수 원명령은 `bash scripts/verify/run-acceptance.sh scripts/acceptance-rps-inmail.sh`, 회귀는 `python3 -m unittest discover -s tests`입니다. 우회 공격은 mktemp 격리 저장소에서만 수행합니다. V1은 외부 Claude 실행, V2는 새 맥락의 별도 교차검토로 실행 여부를 기록합니다. 같은 엔진 하위 에이전트를 독립 V1로 부르지 않습니다.

제품 배송 상태는 NOT_APPLICABLE(내부 생성/검사 도구, 배포 표면 변경 없음), RPS 저장 조회 결과는 별도 운영 증거입니다. DB 변경 없음. 롤백은 이번 추가 커밋만 역순 revert하며 다른 세션 원본/심링크를 되돌리지 않습니다. 영향 범위는 조건 판정·검증 핵심 변경 탐지·기존 운영 문서이며 새 기능/프레임워크/장부를 추가하지 않습니다.

무엇을 — 기존 코드와 문서의 좁은 보완 및 신뢰 경계의 명시.
왜 — HEAD가 작성한 성공 문구로 HEAD 검사의 신뢰성을 증명할 수 없습니다.
버린 길 — 출력 패턴만 더 요구하는 방식은 모든 패턴을 위조하면 우회됩니다.
대가 — 신뢰된 기준과 외부 실행 강제는 이 PR만으로 성립하지 않을 수 있습니다.
되돌리기 — 이번 보완 커밋만 revert하고 보존 사본은 유지합니다.

### 재개 결과와 네 상태 (원격 전달 전 기록)

- Feature verification: 지원한 조건 범위의 인수 12/12, 단위 회귀 50/50 PASS. 기존 30 + 조건 9 + 핵심 변경 탐지 11. 9종 구현 고장 주입 모두 차단하고 복구본은 통과했다.
- Verification integrity: FAIL. `echo PASS; exit 0` 및 VERDICT/PASS/CHECKED 전부 위조가 기존 래퍼를 통과했다. 새 비교기의 로컬 변경 탐지는 PASS지만 외부 필수 검사 배선은 미적용이다.
- Repository CI: 시작 원격 SHA baf20dc의 push/PR verify 둘 다 FAIL. base/head 격리 재현에서 suppression 두 항목(2026-09-15)이 2026-09-22에 만료돼 동일 실패. 별도 기존 이슈 #71/#72에 속하며 이 PR에서는 억제를 바꾸지 않았다. 최종 원격 SHA 결과는 PR 본문에 새로 조회해 기록한다.
- Merge readiness: NOT_READY. 위 미해결, 외부 검증 미실행, active JD 연계 누락을 기능 PASS로 덮지 않는다.

조건 비교는 원문 full을 고정한 채 본문만 바꾼다. 5년→3년, 이상→이하, 정규직→계약직, 수습 3개월→6개월, 지원한 조건 종류의 임의 추가를 차단한다. 5년 이상↔5년+와 기존 정상 4개 JD는 통과한다. 선택(extra) 조건은 삭제해도 필수 조건으로 승격하지 않는다. 자유로운 동의어·복잡한 범위·부정문·필수/우대 간 의미 이동 전체를 이해하는 자연어 판정기는 아니므로 그 의미를 보장하지 않는다.

RPS 조회: 새 Aside 세션 `2026-09-22_s9As92eub6VtTEwx`에서 Settings → Message templates → View로 동일 제목·소유자의 ver2.0 두 행을 각각 조회했다. 두 본문은 모두 저장 전 후보 파일 `outputs/run-20260922/rps_inmail_wrtn.txt`와 1,445자로 일치. 정규화: 쌍을 이룬 Markdown 볼드 표식 제거, CRLF→LF, 앞뒤 공백 제거만 허용. 회사·직무·조건 모두 일치, 본문 이메일/URL은 없음, 별도 서명 이메일은 확인. 과거 1,497자 저장 기록과 안정적 ID 연결은 UNRESOLVED이므로 historical E2E PASS는 주장하지 않는다. 추가 저장·삭제·발송 없음.

동시 변경: 루트 작업트리는 다른 세션이 `task/cross-pc-handoff-20260922`로 전환하고 eaaee62를 커밋했다. 시작 사본 79개는 SHA/링크 재대조 79/79 일치하며 다른 세션 원본을 되돌리지 않았다. PR 작업트리도 검증 중 7e0baae로 이동했다. 그 변경은 되돌리지 않고 커밋된 코드 기준으로 원명령을 재실행했다. 최초 CI-step-integrity 원본 불변 검사는 이 동시 변경 중 FAIL했고, 상태 고정 후 같은 원명령은 24/24 PASS였다.

### 적대 검증 로그

원문은 기존 ignored `private-reviews/`에 보존한다. `startup.log`(정본 전체 로드·원칙), `condition-followup.log`(조건 RED/GREEN), `trust-followup.log`(성공 문구 위조 RED·변경 감지), `ci-followup.log`(GitHub 응답·base/head 만료 재현), `final-feature.log`, `principles-mutations-final.log`, `mutation-rerun.log` 및 `mutation-rerun/*.log`, `size-check.log`, `preservation.log`, `rps-fresh-1.json`, `rps-fresh-2.json`, `rps-roundtrip.log`. 이 경로는 커밋되지 않는 로컬 증거이며 CI 영수증으로 부르지 않는다.

V1 외부 Claude CLI를 API 환경 및 기존 로그인 경로로 각각 실행했으나 응답 없음 오류/90초 시간 초과로 판정을 얻지 못했다(`v1-availability.log`, `v1-login-availability.log`). V1=NOT_RUN, V1 판정 재현 V2도 NOT_RUN. 별도 Codex 교차검토는 외부 독립 검증으로 부르지 않는다. 따라서 Strict 전체 PASS 불가.

파일/함수 한도 검사: 이번 직접 코드 파일은 600줄 이하, Python 함수는 100줄 이하. 동일 줄수 계산기로 격리 사본 600 통과/601 거부 확인. 기존 원칙 mutation은 고유 500/501 fixture 41건 통과이며 이것을 P11 600 경계 증거와 혼동하지 않는다. 기존 PR 전체는 약 6,602줄 추가여서 P11의 PR 3,000줄 초과도 남은 제약이다. 이번 요청의 최소 보완 범위에서 이전 PR 전체를 재설계/분할하지 않았다.

`brief-lint.sh`는 이 저장소에서 찾지 못해 선택 문서 검사 SKIPPED. 제출 전 9문항은 과장/미확인 숨김/표 해석/전문용어 풀이/버린 대안·대가/추정 표시를 직접 확인한다. 미해결을 완료로 표시하지 않는다.

## 9. 외부 검증 경계 후속 — 2026-09-22

결론(시작): 검사 대상 밖에서 실행할 코드와 GitHub의 강제 설정을 분리해 검증합니다. 현재 HEAD `66101c317ca555ee6d52134b7535ce567f5fe346`에는 외부 호출이 없고 필수 체크는 Actions 앱의 `verify`뿐입니다. L3, 운영 배송 NOT_APPLICABLE. 기존 goal만 확장하며 새 장부/서비스는 만들지 않습니다.

범위는 verification-integrity 한 건입니다. suppression, JD, 파서, 포털 저장, main 병합/배포는 제외합니다. 루트의 현재 다른 세션 변경 7개는 `Valuehire_v6-integrity-backup-20260922-134632`에 보존/대조했고 원본은 수정하지 않습니다. 정본 직접 로드 및 원칙 검사 34건은 `private-reviews/external-startup.log`에 기록합니다.

### 계약과 반례

- When GitHub PR 이벤트가 도착하면 신뢰된 workflow 정의는 보호된 main을 대상으로 한 이벤트의 base/head 전체 SHA로 비교해야 합니다. 다른 base 브랜치는 거부합니다. HEAD의 환경파일/인수/비교기/출력은 기준 선택에 참여하지 않습니다.
- When checker, acceptance, 경로목록, workflow/helper가 바뀌면 base의 검토된 검사기로 탐지해야 합니다. HEAD를 checkout하거나 실행하지 않습니다. base에 검사기가 없으면 실패하며 HEAD 사본으로 대체하지 않습니다.
- When core 변경이 있으면 종료값 20을 일반 기능 PASS로 덮지 않습니다. 정상 core 개발은 GitHub의 현재 base/head `reviewDecision=APPROVED`와 기존 보호 규칙(승인 1건 이상·stale 철회·마지막 pusher 외 승인·관리자 적용)으로 판단합니다. PR 개설자와 실제 push한 사람이 다를 수 있으므로 자체 리뷰 목록/커밋 author를 신뢰하지 않습니다.
- When 기능/무관 파일만 바뀌면 별도 승인 없이 통과해야 합니다. 빈/오형식 SHA, Git/API 실패, 이벤트 이후 HEAD/base 이동은 실패 처리합니다.
- Counter-AC: 성공 문자열 전체 위조, 검사기 자기 제외, helper 호출 제거, 공격자 base=HEAD, HEAD에 동명 성공 job 추가. 마지막 공격은 로컬 코드 시험으로 GitHub 설정의 강제를 증명할 수 없으며 별도 외부 적용 증거가 필요합니다.

입출력: GitHub 이벤트 JSON + repository/event-name 환경, GitHub 읽기 API, Git 객체 → 실제 종료값(0=변경 없음 또는 유효 검토, 20=검토 대기, 그 외=실패). 새로운 DB/API/서명/서비스 없음. 외부 API는 PR 현재 SHA와 기존 리뷰/권한 읽기에만 사용합니다. 승인 뒤 새 push는 다른 HEAD라 자동 승계하지 않습니다.

WU: 격리 RED → 작은 trusted workflow와 기존 테스트 확장 → 동일 공격 GREEN 및 회귀 → 외부 강제 가능성/부트스트랩 차단 기록 → 정상 훅으로 커밋/push와 최종 SHA CI 조회. 저장소 설정을 약화하거나 가짜 성공 체크를 원격에 발행하지 않습니다. 롤백은 이 후속 커밋만 revert. 전체 PR 또는 다른 세션 변경은 되돌리지 않습니다.

### 실행 결과

- RED: `private-reviews/external-red.log`에서 현재 HEAD의 후보-controlled checker/acceptance/helper/base override 5종이 모두 exit 0으로 우회됨을 재현했습니다.
- GREEN(로컬 workflow runtime): `python3 -m unittest tests.test_verification_core` 22건 PASS. 정상 기능 변경은 0, 정상 core 변경은 20, checker PASS 변조·성공 문자열 위조·core 목록 축소·helper 제거·base override·동명 후보 workflow 추가는 20 또는 fail-closed입니다. GitHub native `reviewDecision` APPROVED와 보호 규칙이 유지될 때만 정상 core 변경을 0으로 허용합니다.
- 회귀: `python3 -m unittest tests.test_jd_channels tests.test_rps_conditions tests.test_verification_core` 61건 PASS, `bash scripts/verify/run-acceptance.sh scripts/acceptance-rps-inmail.sh` 12/12 PASS, `bash scripts/acceptance-principles-check.sh` 34/34 PASS.
- 실제 PR 데이터 로컬 실행: `private-reviews/external-live-bootstrap.log`에서 PR #104 base `fc6beedc78019862bc2f1b3bf4c4ad3bbd8e845b`에 trusted checker가 없어 exit 1 fail-closed. HEAD 사본으로 대체하지 않았습니다.
- Repository CI: 이 후속 변경 push 전 최신 원격 SHA `66101c317ca555ee6d52134b7535ce567f5fe346`의 기존 `verify` 두 실행은 suppression 만료로 FAIL입니다. 이는 이번 verification-integrity 코드의 로컬 PASS와 분리합니다.
- Merge readiness: 코드 측 준비는 진행됐지만 외부 required workflow/source-pinned 강제는 미적용입니다. `main` base에 workflow+checker가 먼저 신뢰 반영되고 required workflow 또는 동등한 외부 강제가 실제 적용되기 전에는 Verification integrity와 Merge readiness를 PASS로 표시하지 않습니다.
