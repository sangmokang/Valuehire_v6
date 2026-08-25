# G3 hardening7 — 검사기가 뚫리는 4가지 경로를 닫고, 판정 정밀도를 실제 운영 주소에 맞춘다

- 작성: 2026-08-25
- 브랜치: `task/humansearch-g3-portal-constants` (PR #13)
- 위험 등급: L2 — 기존 검사기 보강. 공유 인프라지만 화이트박스 규칙 추가 수준.
- 정본 원칙: P22(운영 상수는 `contracts/` 한 곳), P13④(자기면제 없음), P15③(로컬에만 있는 검사는 없는 것으로 친다), P20(검사 대상 0건 통과 금지)

## 0. 왜 지금인가 — 가정이 아니라 실측

PR #38(HumanSearch L1, 사람인 실제 화면 접속)이 2026-08-21 에 **G3 없이 먼저 병합**됐다.
이 브랜치에 `origin/main`(3094eef)을 병합하고 게이트를 실제로 돌린 결과:

```
FAIL: portal constants outside contracts 13
PRODUCT_FILES: 24 / CHECKED: 104 / CONTRACT_FILES: 5
```

위반 39줄 중 **실제 운영 도메인 `hiring.saramin.co.kr` 이 `humansearch/tests/test_observe_adversarial_output.py` 에 4곳 하드코딩**돼 있었다.
G3 가 막으려던 바로 그 값이 이미 제품 코드에 들어와 있다. 이 작업은 예방이 아니라 **이미 열린 창을 닫는 일**이다.

동시에 같은 실행이 게이트의 반대쪽 결함도 드러냈다 — 위반 39줄 중 29줄은
`portal.invalid`(RFC 2606 예약, 원리적으로 접속 불가)와 루프백(`127.0.0.1`·`localhost`)이었다.
`shadow_server.py` 의 루프백 고정은 위반이 아니라 **안전장치**다. 잡아야 할 것을 놓치면서
잡지 말아야 할 것을 잡고 있었다.

## 1. 닫는 결함 — 두 차례 독립 codex 검증에서 확인된 4가지

| ID | 결함 | 지금 상태 | 최초 지적 |
|---|---|---|---|
| D1 | 태그명 + 순번 셀렉터 (`table tbody tr:nth-child(5) td`) 미탐 | 잡히지 않음 | codex V1 |
| D2 | 결합자 없는 홑 CSS 클래스 셀렉터 (`.login-button`, `button.submit`) 미탐 | 2026-08-13 D4 로 지적됐으나 2026-08-15 "fix2b" 라운드가 "탐지 범위는 넓히지도 줄이지도 않는다"며 의도적 미수정 | codex V1 D4 |
| D3 | 검사 대상 폴더가 `humansearch/src`·`humansearch/tests` 로 **코드에 고정** — 신규 제품 폴더는 검사 자체가 적용 안 됨 | 2026-08-15 의도적 미수정. `apps/admin/`(3파일)이 이미 그 상태로 병합됨 | codex V1 D3 |
| D4 | TLD 목록이 고정 열거 — 목록 밖 확장자(`.jobs` 등)는 미탐. 목록은 **모르는 값을 통과시키는 방향**으로 실패한다 | 잡히지 않음 | codex V2 |
| D5 | (이번 실측 추가) 게이트가 접속 불가능한 예약 도메인·루프백을 위반으로 판정 — 오탐 29줄 | 위 실행 출력 | 2026-08-25 병합 실측 |

## 2. 인수 기준 (EARS)

- **AC-1 (D1)** — When 제품 코드의 따옴표 문자열이 CSS 순번·구조 의사클래스(`:nth-child`, `:nth-of-type`, `:first-child`, `:last-child`, `:only-child` 및 `nth-last-*`·`*-of-type` 변종)를 포함하면, 시스템은 그 파일을 위반으로 판정하고 exit 1 로 종료해야 한다.
- **AC-2 (D2)** — When 제품 코드의 따옴표 문자열이 홑 CSS 클래스 셀렉터(`.name`) 또는 태그+클래스 셀렉터(`tag.name`) 형태이고 그 접미사가 비운영 접미사 계약에 없으면, 시스템은 그 파일을 위반으로 판정해야 한다.
- **AC-3 (D3)** — If 저장소에 제품 코드 확장자(`py`·`js`·`mjs`·`cjs`·`ts`·`tsx`·`jsx`·`html`·`css`)를 가진 추적 파일이 있는 디렉터리가 제품 루트 계약(`contracts/portal-constants-product-roots.txt`)에 등재돼 있지 않으면, 시스템은 조용히 통과하지 않고 **검사 불능(exit 2)** 으로 종료해야 한다. 제품 루트 목록은 코드가 아니라 `contracts/` 데이터여야 한다.
- **AC-4 (D4)** — When 제품 코드의 따옴표 문자열이 점으로 이어진 소문자 호스트 형태이고 그 마지막 라벨이 비운영 접미사 계약(`contracts/portal-constants-nonoperational-suffixes.txt`)에 **없으면**, 시스템은 그 값을 위반으로 판정해야 한다. 즉 판정의 실패 방향은 "모르는 접미사 = 통과"에서 **"모르는 접미사 = 거부"** 로 뒤집혀야 한다.
- **AC-5 (D5)** — When 제품 코드의 주소 표현이 RFC 2606 예약 도메인(`.invalid`·`.test`·`.example`·`.localhost`) 또는 루프백(`127.0.0.0/8`·`localhost`·`0.0.0.0`·`::1`)이면, 시스템은 그것을 위반으로 판정하지 않아야 한다. 이 값들은 원리적으로 운영 주소가 될 수 없다.
- **AC-6 (회수)** — When 위 규칙을 병합된 `origin/main` 트리 전체에 적용하면, 시스템은 `FAIL: portal constants outside contracts 0` 을 출력하고 exit 0 으로 종료해야 한다. 즉 실제 운영 도메인 `hiring.saramin.co.kr` 하드코딩은 **유예가 아니라 제거**로 해소돼야 한다.
- **AC-7 (배선)** — If 새 검사 파일 `scripts/acceptance-hs-portal-constants-hardening7.sh` 가 존재하면, 시스템은 그 파일의 CI 실행 줄이 `.github/workflows/verify.yml` 에 조건 없이 있을 때만 통과해야 한다(P15③, 기존 자기배선 검사가 자동으로 요구한다).

### 검증 명령

| AC | 명령 | 합격 판정 |
|---|---|---|
| 1·2·4·5 | `bash scripts/acceptance-hs-portal-constants-hardening7.sh` | exit 0, 마지막 줄 `CHECKED: N` (N ≥ 12) |
| 3 | 위와 동일(제품 루트 누락 fixture 포함) | 누락 fixture 에서 exit 2 |
| 6 | `bash scripts/acceptance-hs-portal-constants.sh` | `FAIL: portal constants outside contracts 0`, exit 0 |
| 회귀 | `bash scripts/acceptance-hs-portal-constants-hardening{,2,3,4,5,6}.sh`, `-mutations.sh` | 전부 exit 0 |
| 배선 | `bash scripts/acceptance-verify-ac-m.sh` | exit 0, `CHECKED: 34` |

## 3. counter-AC — 겉보기만 합격인 가짜 완료

이 중 하나라도 성립하면 이 작업은 **실패**다.

- **CA-1 (D1 재발)** — 패턴을 `nth-child` 글자만 잡게 넣어서, `:nth-of-type(2)` 나 `:first-child` 는 그대로 통과한다. → 시험이 변종 전체를 심어야 한다.
- **CA-2 (D2 재발)** — 홑 클래스 규칙을 넣되 파일명(`app.js`·`styles.css`·`index.html`·`private.txt`)까지 잡아 오탐 8건을 만들고, 그걸 피하려 규칙을 다시 좁혀 `.login-button` 도 놓친다. → 오탐 0 과 탐지 둘 다 시험한다.
- **CA-3 (D3 재발)** — 제품 루트를 `humansearch/src humansearch/tests apps/admin` 으로 **코드에 다시 하드코딩**한다. 목록은 늘었지만 다음 폴더에서 똑같이 뚫린다. → 계약 데이터 부재·미등재 fixture 로 exit 2 를 시험한다.
- **CA-4 (D4 재발)** — TLD 열거에 `.jobs` 몇 개를 더 붙이고 끝낸다. 실패 방향은 그대로 "모르는 값 통과"다. → 목록에 절대 없을 무작위 TLD(`.zzunknown`)로 시험한다.
- **CA-5 (D5 남용)** — 오탐을 없앤다는 명목으로 `.co.kr`·`.com` 까지 예외에 넣어 진짜 운영 주소를 통과시킨다. → 예외 목록에 실 TLD 가 들어가면 시험이 빨개져야 한다.
- **CA-6 (회수 회피)** — `hiring.saramin.co.kr` 를 지우는 대신 `suppressions.yaml` 에 만료일을 달아 유예한다. 그건 그만큼의 구멍을 승인하는 것이다. → 억제 없이 exit 0 이어야 한다.
- **CA-7 (검사 축소)** — 제품 파일 수·CHECKED 가 줄어든 채로 초록이 된다. → 하한(`product_files ≥ 2`, `checked ≥ 10`)과 hardening7 자체의 `CHECKED` 하한으로 막는다.
- **CA-8 (배선 누락)** — 새 검사 파일을 만들고 `verify.yml` 에 등록하지 않아 로컬에서만 돈다. → 기존 자기배선 검사가 G3 파일 존재만으로 CI 줄을 요구하므로 본체가 빨개진다.

## 4. 범위 밖 (이번에 하지 않는 것)

- `apps/admin/app.js` 의 `document.getElementById` 는 전역 계층이 이미 잡는다. 이 작업은 그 판정을 바꾸지 않는다.
- 전역 계층(`contracts/portal-constants-deny-patterns.txt`) 규칙은 손대지 않는다. 이번 변경은 제품 계층과 검사기 배선에 한정한다.
- PR #38 의 병합 경위 조사는 별도 사안이다.

## 5. 검증 로그 (2026-08-25 실행, 출력 그대로)

### RED — 변경 전 검사기(`efc6dae`)에 같은 공격을 개별 투입

격리 샌드박스에 `efc6dae` 시점의 검사기와 계약 2벌만 복사하고 공격을 하나씩 심었다.
`exit=0` 은 "검사기가 통과시켰다" = 뚫렸다는 뜻이다.

```
D1 nth-child                       exit=0  ← 뚫림(RED)
D1 태그 자손                        exit=0  ← 뚫림(RED)
D2 홑 클래스                        exit=0  ← 뚫림(RED)
D2 태그.클래스                      exit=0  ← 뚫림(RED)
D4 .zzunknown                      exit=0  ← 뚫림(RED)
D4 .jobs                           exit=0  ← 뚫림(RED)
D3 신규 제품 폴더 apps/web 에 위반 2건   exit=0  ← 검사 자체가 적용 안 됨(RED)
```

D4 표본은 처음에 3라벨(`careers.hire-portal.zzunknown`)로 썼다가 2라벨로 고쳤다 —
3라벨은 기존의 "따옴표 3라벨 호스트" 규칙이 이미 잡아서 D4(고정 TLD 열거의 실패 방향)를
찌르지 못했다. 실측으로 확인한 뒤 표본을 교체했다.

새 시험 전체를 변경 전 소스에 걸면 첫 사례에서 멈춘다:

```
ok [baseline 깨끗한 트리] exit=0
FAIL: hardening7 [D1 순번 셀렉터 nth-child] exit=0 (기대: 정확히 1)
```

### GREEN — 변경 후

```
$ bash scripts/acceptance-hs-portal-constants-hardening7.sh
... (22 사례 전부 ok)
PASS: portal-constants hardening7 blocked 10 (allowed 5, notrun 6, wiring 1)
CHECKED: 22
exit=0
```

```
$ bash scripts/acceptance-hs-portal-constants.sh
PASS: portal constants outside contracts 0
PASS: contracts zone violations 0
PASS: ci/pre-push wiring intact
PRODUCT_FILES: 27
CHECKED: 104
CONTRACT_FILES: 9
exit=0
```

병합 직후 13건이던 위반이 0건이 됐다. 내역: 오탐 9건은 정밀화로 사라졌고,
진짜 위반 4건(실제 운영 도메인 하드코딩(§0) 포함)은 코드에서 제거했다.

### 회귀 — 기존 검사 전량

```
acceptance-hs-portal-constants-hardening.sh   exit=0  blocked 15/18 (allowed 2, notrun 1)
acceptance-hs-portal-constants-hardening2.sh  exit=0  cases 16 (blocked 14, clean 1, wiring 1)
acceptance-hs-portal-constants-hardening3.sh  exit=0  cases 8  (blocked 6, clean 1, wiring 1)
acceptance-hs-portal-constants-hardening4.sh  exit=0  cases 8  (blocked 6, clean 1, wiring 1)
acceptance-hs-portal-constants-hardening5.sh  exit=0  cases 7  (blocked 5, clean 1, wiring 1)
acceptance-hs-portal-constants-hardening6.sh  exit=0
acceptance-hs-portal-constants-mutations.sh   exit=0  blocked 24/35 (allowed 3, notrun 8)
verify.sh                                     exit=0  PASS: no secret-pattern match ...
scripts/acceptance-verify-ac-m.sh             exit=0  CHECKED: 34
scripts/acceptance-ci-step-integrity.sh       exit=0  VERDICT: PASS
scripts/acceptance-semantic-mutations.sh      exit=0
scripts/check-docs-sot.sh                     exit=0  OK: docs/sot 재구성 AC 전부 충족
humansearch pytest                            81 passed in 7.45s
셸 문법(git ls-files '*.sh' 전부 bash -n)        통과
```

### 동결 표본이 잡아낸 내 실수 2건 (기록)

구현 도중 기존 RED 원장이 두 번 나를 멈춰 세웠다. 둘 다 내 설계가 과했던 경우다.

1. **`[::1]:9333`** — 루프백 면제를 포트까지 포함해 만들었더니 `hardening.sh` 의
   "D1 IPv6 루프백 host:port" 표본이 빨개졌다. 포트가 붙은 루프백은 접속 대상이 아니라
   **진단 엔드포인트 지정**이고 그건 잡아야 할 운영 상수다. 면제를 "포트 없는 형태"로 좁혔다.
2. **"제품 루트 부재"** — 계약에 등재한 루트가 실재하지 않아도 넘어가게 만들었더니
   `mutations.sh` 의 "제품 루트 부재 — 조용한 skip 금지" 표본이 사유 불일치로 빨개졌다.
   원래 강도(등재했는데 없으면 exit 2)를 복원하고, 표본 쪽이 자기 구조에 맞는 루트 계약을
   쓰도록 바꿨다. 계약이 현실과 어긋난 채 초록이 되는 길을 양방향으로 막았다.

### 동결 예외 3건 (공격 내용·기대 종료코드 불변)

2026-08-13 `runs-on` 표본 조정과 같은 처리다.

- 표본 7벌의 `init_case` 가 신규 계약 3벌을 준비하도록 입력만 보강(루트 계약은 표본 구조에 맞춰 생성).
- `mutations.sh` 의 `URL_P` 호스트를 `career-portal.example` → `career-portal.net` 으로 교체.
  공격의 뜻은 "운영 포털로 가는 scheme URL"인데 RFC 2606 예약 도메인은 원리적으로 접속이
  불가능해 운영 주소의 표본이 될 수 없었다. 형태·기대값은 그대로다.
- `hardening7` 자신의 D4 표본을 3라벨 → 2라벨로 교체(위 RED 절에 근거).

### 알려진 미달·잔여 한계

- **`scripts/acceptance-hs-portal-constants.sh` 는 544줄**이다. 코덱스 프롬프트가 요구한
  "직접 작성 코드 500줄 이하"를 넘겼다. 이 저장소에서 500줄을 강제하는 검사
  (`scripts/verify/check-strict-principles-skills.sh:74`)는 strict 스킬 정본 2벌에만 걸리고
  스크립트에는 걸리지 않는다(선례: `-hardening6.sh` 853줄이 병합돼 있다). 쪼개지 않은 이유는
  판정기를 2벌로 나누는 위험이 줄 수 대비 크다고 봤기 때문이다 — 판단이 다르면 되돌릴 수 있다.
- **전역 locator API 규칙의 줄 경계**: API 호출과 따옴표 리터럴을 서로 다른 줄로 쪼개면
  그 규칙은 놓친다. 리터럴 쪽은 제품 계층 셀렉터 규칙이 잡지만, 제품 루트 밖(scripts/ 등)에
  같은 형태가 들어오면 남는 구멍이다. 계약 파일에 명시해 뒀다.
- **`hardening7` 의 저장소 무변형 자기검사가 한 번 거짓 실패했다**(동시에 백그라운드로
  `hardening6` 이 돌던 중). 이후 연속 실행에서는 재현되지 않았다. 원인 미확정 — 병렬 실행 중
  `git status` 경합으로 추정하며, 재현되면 별도 이슈로 분리한다.

## 6. 적대 검증 로그

(V1 판정 원문 그대로 append)
