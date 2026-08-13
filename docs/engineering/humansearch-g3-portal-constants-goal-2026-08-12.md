# HumanSearch G3 — 포털 상수·locator 경계 검사기 (goal · 2026-08-12)

## §1⑪ 사장님 브리핑 (결론 먼저)

### 결론

이번 작업은 "채용 사이트 주소·화면 위치 규칙 같은 운영 고정값을 코드 속에 몰래 박아 넣는 것"을
컴퓨터가 자동으로 잡아내는 검사기를 새로 만드는 일입니다. 고정값이 있어도 되는 곳은 저장소의
계약 폴더 한 곳뿐이고, 그 밖의 제품 코드에서 발견되면 내 컴퓨터에서 올리기 직전과 GitHub 서버
양쪽에서 빨간불이 나게 합니다. 사장님이 지금 결정하실 것은 없습니다 — 작업이 끝나면 병합 여부를
결정 카드로 보고드립니다.

### 판단 근거 (갈림길과 버린 길)

**무엇을** — 금지 패턴을 두 계층으로 나눴습니다: ① 저장소 전체에 거는 것(화면 요소를 찾는 명령어, 브라우저 원격조종 포트, 채용 포털 상표 주소), ② 제품 코드에만 거는 것(모든 인터넷 주소·도메인·호스트:포트 모양).
**왜** — "모든 인터넷 주소를 저장소 전체에서 금지"하면 지금 깨끗한 저장소가 즉시 불합격됩니다. 파이썬 부품 목록 파일(`humansearch/uv.lock:13` — 부품 내려받기 주소를 정당하게 담은 줄)과 기존 보안 검사기(`scripts/acceptance-secret-webhook-vendor.sh:196` — 시험용 주소를 담은 줄)가 오탐되기 때문입니다. 반대로 화면 요소 찾기 명령어(querySelector 등)는 저장소 어디에도 없음을 실측(전역 검색 0건)으로 확인했으므로 저장소 전체에 걸 수 있습니다.
**버린 길** — (a) 단일 계층 전역 금지는 위 정당한 파일들이 오탐돼 거짓 불합격(사전감사 벡터 7). (b) 검사기·scripts/ 폴더를 검사에서 빼는 오탐 회피는 자기면제 금지 원칙(P13④)과 벡터 3·6 위반. 시험용 가짜 값은 면제 대신 "조각 조립"(문자열을 쪼개 적어 원문 검색에 안 걸리게 하는 관례, `scripts/acceptance-hs-cleanroom-mutations.sh:67-80` — 기존 시험이 같은 기법을 쓰는 줄)으로 해결합니다.
**대가** — 제품 코드 범위가 검사기 안의 목록(`humansearch/src`·`humansearch/tests`)이라, 제품 폴더가 새로 생기면 목록에 한 줄을 추가해야 합니다(§7 비범위에 명시). 패턴 계층을 잘못 나누면 오탐(개발 정지) 또는 미탐(v4의 "같은 주소 18개 파일 산재" 재발) — 두 방향 모두 mutation(일부러 고장 내서 검사가 작동하는지 보는 시험)으로 막았습니다.
**되돌리기** — 병합 후 문제가 생기면 이 변경 한 건만 되무르면 됩니다(신규 파일 4개 삭제 + 설정 2곳 원복, §1⑧). 비용은 PR 1개입니다.

---

## §1① 현재 상태 (file:line 증거)

| ID | 사실 | 증거 |
|---|---|---|
| S-1 | G3 검사기·계약·goal 문서가 origin/main에 없다 | `git cat-file -e origin/main:scripts/acceptance-hs-portal-constants.sh` → ABSENT (사전감사 판정 §C1, 2026-08-12 fresh 재확인: branch grep exit 1, 파일 3종 No such file) |
| S-2 | CI는 수동 열거 목록이다 — G3 줄이 없다 | `.github/workflows/verify.yml:28-46` (G1 8줄·G2 3줄 수동 나열) |
| S-3 | 로컬 pre-push는 글로브 자동 수집이다 | `hooks/pre-push:112-113` (`find . -maxdepth 2 -name 'acceptance-*.sh'`) — S-2와의 비대칭이 사전감사 벡터 1(치명) |
| S-4 | 제품 코드는 현재 2파일이다 | `humansearch/src/humansearch/__init__.py`, `humansearch/tests/test_package_boundary.py` — 두 파일 다 URL·포트·selector 모양 0건 (실측) |
| S-5 | 전역 금지가 불가능한 정당 리터럴이 존재한다 | `humansearch/uv.lock:13-50`(pypi URL 수백), `scripts/acceptance-hs-a3.sh:80`(`ws://127.0.0.1:9338`), `scripts/acceptance-secret-webhook-vendor.sh:196`(example.com URL), `.claude/skills/gptreview/SKILL.md:38`(chatgpt.com), `.secret-patterns.default:73-90`(도메인 주석), `docs/sot/coding-principles.md:37`(saramin.co.kr·9222 인용) |
| S-6 | locator API·XPath·CDP 포트 대역·포털 브랜드 도메인은 비문서 트리에 0건 | `git grep -nE 'querySelector|CSS_SELECTOR|find_element|page\.locator|getElementsBy|remote-debugging-port|:922[0-9]'` → exit 1 (매치 없음); 브랜드 도메인 dotted 형태도 비문서 0건 |
| S-7 | 재사용할 fail-closed 골격이 있다 | `scripts/acceptance-hs-cleanroom.sh:14-48`(계약 부재·빈 패턴·깨진 regex·열거 실패 → exit 2), `contracts/cleanroom-deny-patterns.txt:1-2`(자기 비매치 표현 관례) |
| S-8 | pre-commit이 검사 약화 리터럴을 차단한다 | `hooks/pre-commit:93-113` + `.check-weakening-patterns` 9종 — 새 스크립트의 탐지용 리터럴은 조각 조립 필수 |

→ 뭘 확인했나: G3가 없는 현재 상태와, 검사기를 설계할 때 지켜야 할 지형(오탐 지뢰·재사용 골격·약화 탐지)을 전부 실행·인용으로 채웠습니다.
→ 의미: S-2와 S-3의 비대칭(서버는 수동 목록, 로컬은 자동 수집)이 이번 작업이 반드시 막아야 할 1순위 구멍입니다.

## §1② 근본 원인

v4 실측(P22 근거): 운영 상수가 코드에 박히는 것을 막는 **기계 장치가 없어서** `saramin.co.kr`이
18파일, 디버그 포트가 9파일, 셀렉터가 10파일 54곳으로 복제됐다. 원칙(P22·웹 자동화 5조 1번
"셀렉터는 코드가 아니라 데이터다")은 문서에 있지만, v6에서 아직 CI·pre-push 어느 쪽도 이것을
검사하지 않는다. 제품 코드가 본격적으로 생기기 전(현재 2파일)에 경계를 세워야 비용이 최소다.

## §1③ 인수 기준 — AC 1개 (EARS)

**AC-G3**: While 저장소에 제품 코드가 존재하는 동안, If 운영 상수·portal locator(URL·포트·도메인·
CSS selector·XPath·CDP 포트)가 저장소 루트의 정확한 `contracts/` 밖에 존재하면, Then 시스템은
로컬(pre-push)과 CI 양쪽에서 **정확히 exit 1**로 거부해야 한다. 깨끗한 트리는 **정확히 exit 0**이며
검사 파일 수(PRODUCT_FILES ≥ 2, CHECKED ≥ 10, CONTRACT_FILES ≥ 2)를 보고해야 한다.

- 검증 명령: `bash scripts/acceptance-hs-portal-constants.sh` (검사기 본체)
  + `bash scripts/acceptance-hs-portal-constants-mutations.sh` (mutation 시험 전량)
- counter-AC (가짜 완료의 모습 — 사전감사 벡터 9개 편입, 최소 목록):
  1. 검사기가 pre-push에만 있고 CI verify.yml에 실행 줄이 없음 (벡터 1)
  2. 제품 코드에 심은 가짜 URL·포트·도메인·selector를 못 잡음
  3. 검사 대상 0건인데 exit 0 (벡터 4)
  4. CI 줄을 주석·echo·`if:` 거짓 조건·오류 무시 옵션으로 무력화해도 통과 (벡터 2)
  5. 존재하지 않는 제품 루트를 조용히 skip
  6. 검사기가 자기 자신·scripts/·contracts/를 디렉터리·확장자 단위로 면제 (벡터 3)
  7. contracts/ 안의 정당한 값을 오탐해 깨끗한 트리가 거짓 불합격 (벡터 7)
  8. 무관한 파일을 세서 검사 건수 부풀림 — 제품 코드 수를 독립 대조로 잡는다 (벡터 4)
  9. 깨진 regex·빈 패턴·빈 문자열 매치를 "위반 없음"으로 오해 (벡터 5)
  10. 시험용 고정 파일명만 겨냥한 연출 (벡터 6)
  11. exit 2·127 충돌을 "차단 성공"으로 셈 — 가짜 값은 정확히 exit 1만 성공 (벡터 9)

## §1⑩ 계약 스펙 (T — 채점 기준표)

### 검사기 `scripts/acceptance-hs-portal-constants.sh`

- 입력: 없음 (git 저장소 루트에서 실행. `git ls-files -z`로 추적 파일 전량 열거)
- 출력(stdout):
  - `PASS: portal constants outside contracts 0` 또는 `FAIL: portal constants outside contracts <n>`
  - `PASS: contracts zone violations 0` 또는 `FAIL: contracts zone violations <n>`
  - `PASS: ci/pre-push wiring intact` 또는 `FAIL: ci/pre-push wiring broken <n>`
  - `PRODUCT_FILES: <n>` / `CHECKED: <n>` / `CONTRACT_FILES: <n>`
- exit code **3상태 규율** (사전감사 벡터 9 봉쇄):
  - **정확히 0** = 깨끗한 트리 (위반 0 · 배선 온전 · 하한 충족)
  - **정확히 1** = 위반 발견 (금지값 매치, contracts 구역 위반, 배선 훼손)
  - **정확히 2** = 검사 불능 (패턴 계약 부재/빈 파일/깨진 regex/빈 문자열 매치, 파일 열거 실패,
    파일 읽기 오류, 제품 루트 부재, PRODUCT_FILES < 2, CHECKED < 10, CONTRACT_FILES < 2)

### contracts/ 경계 정의 (지시문 요구 — 명시)

- **허용 경계는 저장소 루트의 정확한 `contracts/` 접두 경로뿐이다.** `git ls-files`가 내는
  저장소 상대 경로에 대해 `contracts/*` 정확 접두 매치만 허용 구역이다.
  `humansearch/contracts-evil/…`, `a/contracts/…`, `contracts-evil/…` 같은 부분 문자열·유사
  경로는 전부 검사 대상이다 (사전감사 벡터 8).
- contracts/ 안의 값은 "허용된 데이터"다 — 금지 패턴을 적용하지 않는다. 대신 구역 자체를
  검사한다: 정규 파일(mode 100644)만 허용, 실행 권한(100755)·심볼릭 링크(120000) 금지,
  확장자 허용 목록(.txt .json .yaml .yml .md) 밖 금지 → 위반 시 exit 1.
- `docs/` 정확 접두 경로 중 **문서 확장자(md·yaml·yml·txt·html)이면서 실행 권한 없는 정규
  파일(100644)**만 금지 패턴을 적용하지 않는다(제품 코드가 아니며, `docs/sot/coding-principles.md:37`가
  v4 사례 인용으로 포털 도메인을 정당하게 담는다). 그 조건을 벗어난 docs/ 파일(실행 코드·실행
  권한 문서)은 전역 검사 대상이다 — 통 면제는 은닉 경로가 된다(V1 결함 D5로 축소).
  면제된 문서는 CHECKED에 세지 않는다 — 카운트 부풀리기에 못 쓴다.
- 그 밖의 모든 추적 파일(검사기 자신·scripts/·hooks/·.github/·.claude/·루트 파일 포함)은
  **전역 패턴 계약**으로 검사한다. 자기면제 없음.
- 제품 코드 루트 = `humansearch/src/` + `humansearch/tests/` (검사기 상단에 명시된 목록).
  이 경로들은 전역 패턴에 **더해** 제품 전용 패턴 계약으로 검사한다. 루트 부재 = exit 2.

### 패턴 계약 2벌 (데이터, contracts/ 안)

- `contracts/portal-constants-deny-patterns.txt` — 전역(비문서·비contracts 전 추적 파일):
  DOM/드라이버 locator API(querySelector·getElementsBy·CSS_SELECTOR·find_element·.locator( 등),
  XPath 리터럴, CDP 원격 디버그 포트 대역(`:922x`)·플래그, 채용 포털 브랜드 도메인(dotted 형태).
  전부 자기 비매치 표현(`…[r]` 괄호 기법, `cleanroom-deny-patterns.txt:1-2` 방식).
- `contracts/portal-constants-deny-patterns-product.txt` — 제품 코드 전용(추가 적용):
  모든 scheme URL(`…://`), 일반 도메인 리터럴(TLD 집합), `호스트:포트`, 따옴표 CSS id/결합자
  셀렉터, 포트 대입문.
- 두 파일 다: `#` 주석·빈 줄 무시, 유효 패턴 0개면 exit 2, 깨진 표현식이면 exit 2,
  빈 문자열에 매치되는 표현식이면 exit 2 (G1 `acceptance-hs-cleanroom.sh:34-43` 방어 재사용).

### 배선(wiring) 자기 검사 — 검사기 본체에 내장

- `.github/workflows/verify.yml`에서 주석 제거 후, `bash scripts/acceptance-hs-portal-constants.sh`
  와 `bash scripts/acceptance-hs-portal-constants-mutations.sh` 각각이 **정확한 실행 줄**
  (`^[[:space:]]*bash scripts/<이름>$` — 접두 echo·옵션·파이프·후미 무력화 불가)로 존재해야 한다.
- 그 실행 줄을 담은 스텝 블록(직전 `- name:`부터 다음 `- name:` 전까지)에 `if:` 조건이나
  오류 무시 설정(continue-on-error)이 있으면 배선 훼손 → exit 1.
- `hooks/pre-push`가 존재·실행 가능하고 글로브 수집식(`-name 'acceptance-*.sh'`)을 담아야 하며,
  검사기 자신이 그 수집 계약(maxdepth 2·PUSH-PERFORMING 헤더 없음·DEFERRED 목록 밖)을 만족해야
  한다 → 아니면 exit 1. (pre-push가 실제 그 find를 실행한다는 것 자체는 `hooks/pre-push:112-148`
  소스와 hook-contracts.md:34가 정본이고, 이 검사는 그 계약과의 정합만 본다 — 한계는 §7)

### mutation 시험 `scripts/acceptance-hs-portal-constants-mutations.sh`

- mktemp 샌드박스 git 저장소들에서 수행. 원본 저장소는 절대 변형하지 않는다(검증기 오염 금지 —
  2026-08-09 교훈). 종료 시 `git status --porcelain` 불변 확인.
- 깨끗한 baseline = **정확히 exit 0** + PRODUCT_FILES가 시험이 독립 계산한 수와 일치.
- 가짜 값 심기(파일명·확장자·경로·값 다양화) = **정확히 exit 1** + 올바른 FAIL 줄
  (`rc -eq 1`로만 성공 판정 — `rc -ne 0` 금지, 벡터 9·11).
- 검사 불능 유도(패턴 부재·빈 파일·깨진 regex·빈 매치·제품 루트 부재·제품 0건) = **정확히 exit 2**.
- contracts/ 정당 값 = exit 0 (오탐 방어), 유사 경로 위장 = exit 1 (경계 방어).
- CI 무력화 변형(주석·삭제·echo·후미 무력화·조건 거짓·오류 무시) 각각 = exit 1.
- 시험 소스의 가짜 값·무력화 문자열은 전부 조각 조립 — 시험 파일 자신이 검사기와
  pre-commit 약화 탐지(`.check-weakening-patterns`)에 걸리지 않게.

## §1④ Harness Gate 0~6 계획

| Gate | 내용 | 상태 |
|---|---|---|
| 0 | 계약 SHA 대조(04c03a11… 일치) · main==origin(682f00e) · RED 0/19 · G3 흔적 0건 fresh 확인 | 통과 (2026-08-12) |
| 1 | issue #12 (G3 단언 1개) + 이 goal 문서 | 통과 |
| 2 | worktree `humansearch-g3-portal-constants` · RED = mutation 시험 커밋 + 실패 실행 증명 | 진행 |
| 3 | GREEN = 검사기 + 계약 2벌 + verify.yml 배선 + SOT 갱신 (RED 파일 불변) | 대기 |
| 3.5 | 배선 증명: pre-push 글로브 실측 + verify.yml 실행 줄 + 검사기 내장 배선 검사 | 대기 |
| 4 | §5 검증 명령 전량 실행, 출력 숫자 그대로 본 문서에 보존 | 대기 |
| 5 | push(pre-push 전량 재실행) → PR(issue·SHA·검증·적대검증 로그) → CI 초록 | 대기 |
| 6 | 오너 위임 조건(CI 초록+V1·V2+codeaudit) 충족 시 squash merge 후 즉시 정지 | 대기 |

→ 뭘 보여주나: 이번 작업이 밟는 관문 순서와 현재 위치입니다. 실패 시험을 먼저 커밋하고(2), 최소 구현(3), 검증(4), 적대검증 통과 뒤에만 배송(5~6)합니다.
→ 의미: 어느 관문도 건너뛰지 않았음을 이 표와 아래 검증 출력으로 대조할 수 있습니다.

## §1⑤ codex 적대검증 정조준 항목 (V1)

가짜 완료 / CI·pre-push 배선 불일치 / 0건 수집 통과 / mutation 우회(고정 파일명 연출·조각 조립
누락) / 자기면제(디렉터리·확장자) / 정상 트리 오탐 / 카운트 부풀리기 / exit code 혼동(2·127을
차단 성공으로 셈) / contracts 경계 부분 문자열 매치. codex는 인터넷 차단 환경이므로 로컬 저장소
공격만 요구하고 GitHub 실측은 V2 몫.

## §1⑥ SOT 체크리스트

- 읽음: `docs/sot/INDEX.md`, `coding-principles.md`(P2·P3·P5·P13·P15·P16·P20·P22·웹5조1),
  `verification-commands.md`, `hook-contracts.md`, `git-workflow.md`. 저장소 AGENTS.md/CLAUDE.md 없음(ls 확인).
- 이 변경이 SOT를 수정하는가: **한다** — `docs/sot/verification-commands.md`의 CI 스텝 표에
  G3 줄 추가(스텝 16→17). 검사기가 실제 명령으로 성립한 뒤에만 갱신(문서 선행 금지).
  `mechanism-registry.yaml`은 건드리지 않는다(§7).

## §1⑦ 비범위

- B1~B5·L0·C(fresh capture)·브라우저 extension·native-host 일절 없음. 제품·사업 동작 추가 없음.
- 실제 포털 URL·selector 수집·구현 없음 — 금지 패턴은 모양·브랜드 dotted 형태만 담는다.
- `docs/sot/mechanism-registry.yaml` 등재는 하지 않는다 — 검사기가 배선 검사를 내장하므로 중복이고,
  AC-M CHECKED=25 고정 불변식과의 상호작용 검증이 이 AC 범위를 벗어난다. 필요하면 후속 AC.
- 제품 루트 목록의 자동 발견(신규 제품 폴더 자동 편입)은 후속 — 현재는 검사기 상단 목록이 정본.
- v1~v5 소스·테스트·fixture 열람·복사 없음 (클린룸 유지).

## §1⑧ 롤백 절차

merge 후 문제 시: ① `git revert <squash SHA>` 한 커밋이면 끝(신규 파일 4개 삭제 + verify.yml·SOT
표 원복이 전부다 — 기존 파일 동작 변경 없음). ② revert가 검사·테스트 파일을 건드리므로 P15②에
따라 revert PR에 삭제 단언 목록을 자동 노출한다. 비용: PR 1개.

## §1⑨ 영향 반경 (blast radius)

- 이 검사기가 **오탐**하면: 모든 push·CI가 막힌다(pre-push 글로브 + verify.yml). 완화: mutation
  baseline + 실저장소 전량 검증 + V1·V2. 긴급 탈출은 suppressions.yaml(만료일 필수)이 아니라
  revert PR이 정본(§1⑧).
- **미탐**하면: 포털 상수 하드코딩이 다시 산재하기 시작한다(v4 재발) — 단 G3 이전 상태와 동일할
  뿐 더 나빠지지는 않는다.
- PII·인증·과금 경로 접촉 없음(검사기는 읽기 전용, 저장소 텍스트만 읽는다). 데이터 안전 AC 불요.
  단 L3 등급 유지 — 공유 검증 인프라(CI·pre-push)를 건드리기 때문.

## 검증 출력 (Gate 4 — 출력 숫자 그대로, 2026-08-12 13:53~14:05 KST)

### RED 증명 (구현 부재 상태, 커밋 9bab751 직전)

```text
$ bash scripts/acceptance-hs-portal-constants.sh
bash: scripts/acceptance-hs-portal-constants.sh: No such file or directory
exit=127

$ bash scripts/acceptance-hs-portal-constants-mutations.sh
FAIL: required G3 implementation missing: scripts/acceptance-hs-portal-constants.sh
exit=1
```
→ 뭘 했나: 구현이 없는 상태에서 검사기와 mutation 시험을 실행했습니다.
→ 결과: 검사기는 파일 부재(127), 시험은 "구현 없음"이라는 올바른 이유의 exit 1.
→ 의미: RED 가 문법 오류가 아니라 기대 동작 부재로 빨갛다는 증명입니다 — 좋은 소식.

### GREEN (커밋 b3a3db0)

```text
$ bash scripts/acceptance-hs-portal-constants.sh
PASS: portal constants outside contracts 0
PASS: contracts zone violations 0
PASS: ci/pre-push wiring intact
PRODUCT_FILES: 2
CHECKED: 49
CONTRACT_FILES: 3
exit=0

$ bash scripts/acceptance-hs-portal-constants-mutations.sh   # 마지막 줄
PASS: portal-constants mutations blocked 24/35 (allowed 3, notrun 8)
exit=0
```
→ 뭘 했나: 깨끗한 실제 저장소에서 검사기를, 고장 샌드박스 35개에서 mutation 시험을 돌렸습니다.
→ 결과: 실저장소는 위반 0(제품 2·비문서 49·계약 3파일), 시험은 차단 24건(전부 정확히 exit 1)·
  허용 3건(정확히 0)·검사불능 8건(정확히 2) 전부 기대값 일치.
→ 의미: 오탐(깨끗한데 빨강)과 미탐(가짜 값 통과)과 exit code 혼동이 모두 없다는 뜻 — 좋은 소식.

### 회귀 전량 (마지막 줄 :: exit)

```text
G1 8종: cleanroom(CHECKED: 58)·mutations(10/10)·absolute-paths(3/3)·absolute-contexts(7/7)
        ·colon-paths(4/4)·file-urls(2/2)·hook-env(5/5)·hook-env-mutations(6/6) — 전부 exit=0
G2 3종: gates(COLLECTED: 1)·gates-mutations(6/6)·gates-antiforge(3/3) — 전부 exit=0
AC-S1: acceptance-secret-webhook-vendor.sh CHECKED: 32 exit=0
AC-M : acceptance-verify-ac-m.sh CHECKED: 25 exit=0
기존  : acceptance-0-2(PASS)·0-5(PASS)·0-6(PASS)·hs-a3(CHECKED: 25)·hs-a4(CHECKED: 30) — 전부 exit=0
verify.sh exit=0 · bash -n 추적 셸 28개 전부 통과
```
→ 뭘 했나: 오늘 병합분(AC-S1·AC-M)을 포함한 기존 검사 전부를 다시 돌렸습니다.
→ 결과: 전부 exit 0 — G3 추가가 기존 검사를 하나도 깨지 않았습니다. 좋은 소식.

### 배선 실측 (pre-push 실호출 + RED 원장)

```text
$ bash hooks/pre-push origin https://github.com/sangmokang/Valuehire_v6.git </dev/null
pre-push: 검사 19개 실행
  ok  ./scripts/acceptance-hs-portal-constants-mutations.sh
  ok  ./scripts/acceptance-hs-portal-constants.sh
  (나머지 17개 전부 ok)
pre-push exit=0

$ bash scripts/session-status.sh
HEAD: b3a3db0 (ahead 2 / behind 0)
ORIGIN: 682f00e
RED: 0/21 (acceptance-0-7.sh 제외 — CI 담당)
```
→ 뭘 했나: 코드 올리기 직전 문지기를 실제로 호출하고, 미해결 검사 원장을 다시 계산했습니다.
→ 결과: G3 검사기 2개가 글로브(이름 규칙 자동 수집)로 저절로 편입돼 실행됐고, 실패 0/21.
→ 의미: 로컬 배선은 실행으로 증명됐습니다. 분모는 지시서 전망(20)과 달리 21 — G3 가 검사기와
  mutation 시험 2개 파일을 추가했기 때문이며, 실측치를 그대로 보고합니다.

### RED 불변 증명

```text
$ git diff 9bab751 -- scripts/acceptance-hs-portal-constants-mutations.sh | wc -l
0
```
→ 뭘 했나: RED 커밋과 현재 시점의 시험 파일을 줄 단위로 비교했습니다.
→ 결과: 차이 0줄 — GREEN 구현이 시험의 기대값·단언을 한 글자도 바꾸지 않았습니다 (P5·P15④).
→ 의미: 구현이 시험에 맞춰 채점 기준을 몰래 고치는 부정이 없었다는 뜻 — 좋은 소식입니다.

## 적대 검증 로그 (V1·V2 — 판정 원문 100% 보존)

### V1 — codex (2026-08-12, VERDICT: FAIL)

- 검증자 신분: 실제 codex CLI 세션 `019ff45c-457f-70d1-a9ad-0377a4a1992d`, companion job `task-mspmla0l-r4fofr`,
  실행 명령 50개(판정 말미 장부), job log `~/.claude/plugins/data/codex-openai-codex/state/humansearch-g3-portal-constants-39cbd6bf44ef0c67/jobs/task-mspmla0l-r4fofr.log`
- 원문 보관: `.claude/private-reviews/codex-g3-verdict-2026-08-12.md` (SHA-256 `641d08277c87e79cb4e65fdcda197909bf40c6c364c01926b77786e93409dc5e`)
  — 비공개 폴더는 git 추적 밖이므로, 아래에 원문 전문을 그대로 붙여 이 goal 문서에도 100% 보존한다(이관·보존 수행: Claude, 2026-08-12 14:45 KST).
- 참고(정직 보고): 검증 에이전트 기동이 모델 안전장치 오작동으로 2회 실패해 3차 시도(운전자 모델 교체)로 성공했다. 검증 주체는 codex CLI 로 동일.
- codex 환경 제약: 임시 파일 생성이 금지돼 검사기·시험의 완주 실행은 불가 → 규칙 대조·경로 분기 직접 실행으로 대체(판정문에 명시). 그 공백은 아래 V2 가 실검사기로 메웠다.

### V2 — 격리 재현 (기억 리셋 관점, 실검사기 실행)

codex 는 자기 환경에서 검사기를 완주하지 못했으므로, V2 가 결함 5건 전부를 **실제 검사기 + mktemp 샌드박스**로 재현했다.

| 결함 | codex 주장 | V2 재현 결과 | 판정 |
|---|---|---|---|
| D1 새 표현 8종 미탐 | 규칙 대조로 8/8 미탐 | 샌드박스 8케이스 전부 scanner exit **0** (미탐 재현) | 일치 · 확정 |
| D2 CI run 블록 선행 exit 0 / set +e | 배선 자기검사 통과 | 두 변형 모두 scanner exit **0** (수용 재현) | 일치 · 확정 |
| D3 PUSH-PERFORMING 머리말 | 훅 skip + 자기검사 통과 | scanner exit **0** + pre-push:123 head-20 매치로 skip 분기 확인 | 일치 · 확정 |
| D4 mktemp 실패 → exit 1 | 자기 환경 3회 실측 | TMPDIR 방식은 이 환경서 재현 불가(macOS mktemp 이 시스템 임시경로 우선) → PATH 에 실패하는 가짜 mktemp 주입으로 scanner exit **1** 재현 | 일치 · 확정 (재현 방법만 상이) |
| D5 docs/ 전체 면제 | 경로 분기 실행 | docs/*.py 셀렉터 payload → scanner exit **0** (은닉 재현) | 일치 · 확정 |

→ 뭘 보여주나: codex 가 간접 증거(규칙 대조)로 주장한 결함 5건을, V2 가 실제 검사기를 돌려 하나씩 다시 확인한 대조표입니다.
→ 결과·의미: 5건 전부 재현됐습니다. 두 검증이 독립적으로 같은 결론에 도달했으므로 FAIL 판정은 과장이 아니었고, 수정이 필요하다는 뜻입니다.

- codex FAIL 의 과장: **0건**. codex PASS 측 주장(카운트 2·49·3 정직, contracts 구역 방어, exit 규율, RED 불변, 현재 배선 연결)도 V2/기존 실행과 모두 일치.
- 정정: 0건 (D4 의 재현 경로만 환경 차이로 교체).

### 조치 — 2차 RED→GREEN (RED2 `37d2fa7` · GREEN2 `dfccaa7`)

결함 5건 전부 `scripts/acceptance-hs-portal-constants-hardening.sh`(2차 RED 정본, 18케이스)로 먼저 실패를 증명한 뒤 봉쇄했다.

```text
$ bash scripts/acceptance-hs-portal-constants-hardening.sh   # RED2 시점 (b3a3db0 구현 기준)
ok [hardening baseline] exit=0
FAIL: hardening [D1 IPv4 비루프백 host:port] exit=0 (기대: 정확히 1)
exit=1

$ bash scripts/acceptance-hs-portal-constants-hardening.sh   # GREEN2 (dfccaa7) 이후
PASS: portal-constants hardening blocked 15/18 (allowed 2, notrun 1)
exit=0
```
→ 뭘 했나: 보강 시험을 수정 전과 수정 후의 검사기에 각각 돌렸습니다.
→ 결과: 수정 전에는 첫 미탐 사례에서 실패(올바른 이유의 빨강), 수정 후에는 18케이스 전부 기대값 일치.
→ 의미: 결함 봉쇄가 시험으로 먼저 정의되고 구현이 따라갔다는 증명 — 좋은 소식입니다.

```text
GREEN2 후 재검증 전량 (2026-08-12 14:38~14:44 KST):
  실저장소 검사기 exit=0 (PRODUCT_FILES 2 · CHECKED 50 · CONTRACT_FILES 3)
  원 mutation 24/35 (allowed 3, notrun 8) exit=0 · RED/RED2 파일 diff 0줄
  G1 8종 · G2 3종 · AC-S1 · AC-M · 0-2/0-5/0-6/a3/a4 · verify.sh 전부 exit=0
  bash -n 추적 셸 29개 통과 · pre-push 실호출 검사 20개 전부 ok (G3 3종 자동 수집)
  session-status → RED: 0/22
```
→ 뭘 했나: 1차 때 돌린 검증 전량을 보강 후 같은 방식으로 재실행했습니다.
→ 결과: 전부 통과. 검사 분모는 19→22 (G3 파일 3개 추가분).
→ 의미: 보강이 기존 검사를 하나도 깨지 않았습니다.

### 남는 한계 (수용 근거)

- 제품 루트 밖(scripts/ 등)의 원시 CSS 문자열·일반 URL 은 전역 계층으로 못 잡는다 — 전역화하면
  동결된 RED 시험 소스(`scripts/acceptance-hs-portal-constants-mutations.sh:47`의 따옴표 `#` fixture)와
  기존 검사기 fixture 가 오탐된다(2026-08-12 실측). codex 도 이를 결함이 아닌 설계 대가로 분류했다.
- 문자열 조각·이스케이프 조립, 빌드 산출물 검사는 계약 §1⑦ 명시 비범위 (codex 동일 분류).
- `humansearch/` 바로 아래의 비코드 파일(pyproject.toml·uv.lock 등)은 제품 계층 밖이다 — 이 파일들은
  패키지 배포 주소 같은 정당한 URL 을 담으므로 제품 계층을 적용하면 오탐된다. 코드가 아닌 설정에
  운영 상수를 숨기는 경로는 전역 계층(locator API·CDP·브랜드)까지만 막는다 (codeaudit 독자 공격 실측).

### V2-codeaudit 교차 감사 (2026-08-12, 판정: 구현 확인)

- 변경 반경 fresh 대조: `git diff 682f00e..HEAD --stat` → 기대한 8파일뿐(검사기 3·계약 2·verify.yml·SOT·goal). 외부 파일 접촉 0.
- CI 배선 원문: G3 스텝에 정확한 실행 줄 3개, 조건·오류무시 없음.
- 감사자 독자 공격 3종: 대문자 TLD → exit 1 차단 ✓ / 깊은 제품 경로 → exit 1 차단 ✓ /
  제품 루트 밖 `humansearch/env-probe.cfg` URL → exit 0 (위 한계로 문서화, 결함 아님 판정).
- 요구사항 R1~R10(검사기·3상태·최소수 보고·양쪽 배선·벡터 11 봉쇄·RED 불변·경계·절대경계·SOT·적대검증) 전부 구현 확인.
  유일한 미확인: CI 러너에서의 실제 실행 — push 후 CI 초록으로 해소한다(범위상 로컬에서 증명 불가).

### V1 판정 원문 (100% — 아래 전문은 수정 없이 그대로다)

---8<--- codex verdict 원문 시작 ---8<---

VERDICT: FAIL

# 결론

새 품질 검사는 현재 상태로 승인하면 안 됩니다. 금지해야 할 새 주소·포트·화면 위치 표현 8종을 알아보지 못했고, 서버 검사도 실행 줄보다 먼저 끝내거나 실패를 무시하도록 만들면 정상으로 받아들였습니다.

로컬 검사 역시 파일 머리말 하나로 건너뛰게 만들 수 있는데 자기검사는 이를 발견하지 못했습니다. 또한 검사 자체를 시작할 수 없는 상황을 약속된 결과 번호 2가 아니라 위반 번호 1로 잘못 보고했습니다.

현재 파일 수 보고값, 현재 서버·로컬 연결, 계약 폴더의 현재 상태는 맞았습니다. 그러나 이 실행 환경이 새 임시 파일 생성을 금지하여 복제본 고장 주입과 35건 전량 시험은 끝까지 실행하지 못했으며, 이 공백은 합격으로 처리하지 않았습니다.

지정된 판정 파일에는 쓰지 못했습니다. 읽기 전용 실행 환경이 파일 생성 요청을 거부했으므로, 지시대로 판정 전문을 이 화면에 남깁니다.

# 판단 근거

## 판정 기준

종료 코드(exit code, 프로그램이 끝날 때 운영체제에 돌려주는 숫자)는 다음 계약으로 채점했습니다.

- 0: 깨끗하고 검사가 정상적으로 완료됨
- 1: 실제 규칙 위반이 발견됨
- 2: 검사를 신뢰할 수 있게 수행하지 못함

가장 상위의 인수 기준은 `docs/engineering/humansearch-g3-portal-constants-goal-2026-08-12.md:48-51`입니다. 이 줄은 운영 상수와 화면 위치 정보가 루트의 정확한 `contracts/` 밖에 있으면 로컬과 서버 양쪽에서 정확히 1로 거부하라고 정합니다.

반면 같은 문서 `:93-99`는 `docs/` 전체를 면제하고, 일반 주소·도메인·포트 규칙은 두 제품 폴더에만 적용합니다. 구현은 이 좁은 상세 규칙을 따르지만, 사용자가 이번에 다시 제시한 전체 금지 단언과 충돌합니다.

좁은 상세 규칙이 전체 단언을 축소한다고 해석하는 길은 버렸습니다. 그 해석을 택하면 `docs/run-portal.py`, `scripts/portal-config.toml`, 제품 코드 안의 새 주소 형식이 금지 대상이 아니라는 결론이 되며, “정확한 계약 폴더 밖에는 존재할 수 없다”는 인수 기준이 사실상 성립하지 않기 때문입니다.

이 판정이 틀리면 서버와 로컬 화면에는 검사가 연결된 것처럼 보이지만 실제 검사를 하지 않거나, 새로운 형식의 포털 고정값이 제품 코드에 들어가도 승인되는 일이 생깁니다.

## 앞부분에 공개하는 확인 공백과 재시도

- 깨끗한 원본에서 검사기를 세 번 직접 실행했지만, 세 번 모두 운영체제가 임시 파일 생성을 거부했습니다. 따라서 깨끗한 트리가 실제 검사기에서 0을 반환한다는 단언은 이번 환경에서 확인하지 못했습니다.
- 35건 고장 주입 시험도 임시 복제 저장소를 만들지 못해 첫 사례 전에 중단됐습니다. 35건 전량 통과는 건너뜀입니다.
- 새 위반을 복제 저장소의 추적 파일로 추가해 전체 검사기의 반환값을 확인하는 실험은 수행하지 못했습니다. 대신 검사기가 실제 사용하는 두 규칙 파일과 경로 분기 코드를 그대로 실행해 탐지·미탐을 확인했습니다. 전체 복제 실행과 같다고 과장하지 않습니다.
- GitHub 서버에서 실제 작업을 실행하는 실험은 인터넷 차단 조건 때문에 건너뛰었습니다.
- 첫 제품 파일 수 계산은 널 문자 구분을 이 환경의 `awk`가 예상대로 처리하지 못해 1로 잘못 나왔습니다. 줄 단위 `git ls-files`로 다시 계산해 2임을 확인했습니다.
- 첫 서버 연결 모의 실험은 줄바꿈 문자를 실제 줄로 풀지 않아 정상 사례까지 거부했습니다. 실제 여러 줄 입력으로 재실행해 교정했습니다.
- 35건 구성 수의 첫 계산은 셸의 `do`를 사례로 잘못 세어 36이 됐습니다. 반복 항목을 다시 세어 28+7=35로 교정했습니다.
- 문서 면제 조사 첫 명령은 삭제 동작이 들어 있어 셸 시작 전에 차단됐습니다. 임시 파일을 사용하지 않는 방법으로 다시 실행했습니다. 차단된 요청은 명령 수에 넣지 않았습니다.
- 판정 파일 생성은 읽기 전용 제한으로 거부됐습니다. 파일이 없으므로 문서 형식 검사도 실행하지 못했습니다.
- 위 항목 외에는 건너뛴 검증 항목이 없습니다. 원본 저장소를 바꾸는 명령은 실행하지 않았습니다.

## 주요 결함

### 결함 1 — 높음: 금지 대상 표현 8종이 통과합니다

제품 코드에 적용되는 전역·제품 규칙을 함께 실행했을 때 다음이 모두 미탐이었습니다.

- 일반 사설 주소와 포트: `10.77.4.9:9444`
- 목록에 없는 `.ai` 도메인
- 공백으로 연결된 CSS 화면 위치 표현
- 속성 기반 CSS 화면 위치 표현
- 공백이 들어간 XPath
- 따옴표로 감싼 브라우저 제어 포트
- 설정 자료형의 `PORT: 9333`
- IPv6 주소와 포트

그대로 두면 새로운 포털이나 설정 표기법을 쓰는 순간 운영 고정값이 코드에 들어가도 병합될 수 있습니다.

### 결함 2 — 치명적: 서버 실행 줄이 있어도 실제 검사를 건너뛸 수 있습니다

서버 자동검사(CI, 변경을 원격 서버에서 자동 판정하는 절차)의 실행 줄 앞에 `exit 0`을 넣거나, 실패 시 중단하는 설정을 `set +e`로 끈 뒤 마지막에 성공 명령을 두면 배선 자기검사는 정상으로 판정했습니다.

실제 셸 실행에서도 검사기가 실패했는데 전체 실행 묶음은 0으로 끝났습니다. 그대로 두면 서버 설정에 검사 줄이 보이면서도 실제 정책 위반을 승인할 수 있습니다.

### 결함 3 — 높음: 로컬 검사를 건너뛰는 머리말을 자기검사가 놓칩니다

로컬 업로드 직전 검사(pre-push, 개발자가 변경을 올리기 직전에 로컬에서 실행되는 검사)는 파일 첫 20줄에 `# PUSH-PERFORMING`이 있으면 그 파일을 건너뜁니다.

G3 자기검사는 실제 실행 대상 목록을 대조하지 않고 파일 이름 수만 셉니다. 따라서 해당 머리말을 추가하면 로컬 훅은 G3를 건너뛰지만 G3의 연결 검사는 정상으로 판정합니다.

그대로 두면 로컬과 서버 양쪽에서 거부한다는 계약 중 로컬 절반이 조용히 사라질 수 있습니다.

### 결함 4 — 중간: 검사 불능이 약속된 2가 아니라 1로 샙니다

검사기는 시작하자마자 임시 파일 생성 명령 `mktemp`를 네 번 실행하지만 실패를 별도로 처리하지 않습니다. 이번 환경에서 그 명령이 실패하자 실제 반환값은 1이었습니다.

그대로 두면 운영자는 규칙 위반과 검사 환경 고장을 구분하지 못하고, 자동화도 잘못된 원인으로 대응할 수 있습니다.

### 결함 5 — 높음: `docs/` 전체 면제가 상위 계약과 충돌합니다

`docs/` 경로는 확장자나 실행 권한과 관계없이 검사에서 즉시 제외됩니다. 따라서 `docs/run-portal.py` 같은 실행 파일에 포털 주소나 화면 위치 표현을 넣어도 G3는 읽지 않습니다.

현재 문서 5개가 전역 규칙과 실제로 일치하므로 문서 오탐을 피하려는 이유는 확인됐습니다. 그러나 “문서 확장자만 면제” 또는 “실행 불가능한 문서만 면제”가 아니라 디렉터리 전체를 면제했습니다.

그대로 두면 문서 폴더가 운영 코드나 설정을 숨기는 허용 구역으로 사용될 수 있습니다.

## 설계 결정 평가

**무엇을** — 전역에는 좁은 규칙을 적용하고, 일반 주소·도메인·포트 규칙은 `humansearch/src`와 `humansearch/tests`에만 추가 적용했습니다.

**왜** — 저장소 전체에 일반 주소 규칙을 적용하면 패키지 잠금 파일과 기존 검사기의 시험 자료가 잘못 거부되기 때문입니다.

**버린 대안** — 파일 역할별 허용 목록, 특정 잠금 파일과 시험 자료만 제한적으로 제외하는 방식, 또는 계약 자료 여부를 구조적으로 표시하는 방식은 채택하지 않았습니다.

**대가** — 제품 폴더 밖의 운영 설정과 새 도메인·포트·화면 위치 형식이 통과하며, 전체 금지라는 상위 계약과 실제 검사 범위가 달라졌습니다.

**되돌리는 법** — `docs/` 전체 면제를 문서 확장자·비실행 파일 조건으로 축소하고, 제품 밖 설정 파일에도 주소·포트·CSS·XPath 규칙을 적용한 뒤, 현재 정당한 자료는 좁은 파일별 예외로 옮기면 됩니다.

# 기술 상세

## 1. 새 위반 사례 반증

검사기는 `scripts/acceptance-hs-portal-constants.sh:93-103`에서 `grep`과 규칙 파일을 사용해 파일 내용을 검사합니다. 이 줄은 일치하면 위반 수를 올리고, 검사 오류면 오류 수를 올립니다.

제품 파일은 `:130-135`에서 전역 규칙과 제품 규칙을 모두 적용합니다. 새 확장자도 `git ls-files`에 추적되기만 하면 같은 분기에 들어가므로 확장자 자체는 면제되지 않습니다.

실행한 탐지 대조 전문은 다음과 같습니다.

```text
$ [새 표현을 제품 규칙에 직접 대조]
mixed-case URL | rc=0 | DETECTED | ENDPOINT = "HtTpS://jobs-r9.attacker.dev/v2"
different localhost port | rc=0 | DETECTED | REMOTE = "localhost:9444"
different IPv4 port | rc=1 | MISSED | REMOTE = "10.77.4.9:9444"
internal hostname port | rc=1 | MISSED | REMOTE = "grid.internal:9444"
new TLD domain | rc=0 | DETECTED | PORTAL = "jobs-r9.example.ai"
CSS descendant | rc=1 | MISSED | LOGIN = ".account-card input"
CSS attribute | rc=1 | MISSED | LOGIN = "[data-testid=sign-in]"
XPath whitespace | rc=1 | MISSED | LOGIN = "//input [@name=email]"
camelCase CDP port | rc=1 | MISSED | cdpPort = 9333
new extension content | rc=0 | DETECTED | ENDPOINT = "ftp://files-r9.example.org/a"
split runtime URL | rc=1 | MISSED | ENDPOINT = "https" + "://" + "10.77.4.9:9333"
escaped runtime URL | rc=1 | MISSED | ENDPOINT = r"https:\x2f\x2fjobs-r9\x2eexample\x2eai"
exit=0
```

→ 뭘 시켰나: 구현자가 쓰지 않은 값과 표현을 제품 규칙에 입력했습니다.  
→ 뭐가 나왔나: 대소문자 URL·localhost·FTP는 잡았지만 여러 포트·CSS·XPath 표현은 놓쳤습니다.  
→ 좋은 소식인가 나쁜 소식인가: 일부 일반화는 됐지만 전체 계약을 만족하지 못하므로 나쁜 소식입니다.

위의 `jobs-r9.example.ai`는 `.example` 부분이 기존 도메인 규칙에 걸린 사례라 순수 `.ai` 검증이 아니었습니다. 이를 교정해 `jobs-r9.vendor.ai`로 다시 실행했습니다.

```text
$ [전역 규칙과 제품 규칙을 모두 적용한 독립 재검사]
IPv4 non-loopback port | global_rc=1 product_rc=1 | MISSED | REMOTE = "10.77.4.9:9444"
unlisted .ai domain | global_rc=1 product_rc=1 | MISSED | PORTAL = "jobs-r9.vendor.ai"
CSS descendant selector | global_rc=1 product_rc=1 | MISSED | LOGIN = ".account-card input"
CSS attribute selector | global_rc=1 product_rc=1 | MISSED | LOGIN = "[data-testid=sign-in]"
XPath with whitespace | global_rc=1 product_rc=1 | MISSED | LOGIN = "//input [@name=email]"
quoted CDP port | global_rc=1 product_rc=1 | MISSED | CDP_PORT = "9333"
mapping CDP port | global_rc=1 product_rc=1 | MISSED | CDP_PORT: 9333
IPv6 loopback port | global_rc=1 product_rc=1 | MISSED | REMOTE = "[::1]:9333"
exit=0
```

→ 뭘 시켰나: 제품 파일이 실제로 거치는 두 규칙을 합쳐 8개 새 위반을 대조했습니다.  
→ 뭐가 나왔나: 8개 모두 두 규칙에서 일치하지 않았습니다.  
→ 좋은 소식인가 나쁜 소식인가: AC-G3의 금지 범위를 실제로 빠져나가므로 나쁜 소식입니다.

반증 기록: “다른 가짜 값·새 파일 형식에서도 잡힐 것”을 두 규칙 동시 대조로 반증 시도했고, 8개 반례가 성공했습니다.

다만 복제 저장소에 이 내용을 추적 파일로 추가한 뒤 전체 검사기가 0을 내는 모습은 임시 파일 생성 제한 때문에 재현하지 못했습니다. 위 결론은 규칙 대조 실행과 `scripts/acceptance-hs-portal-constants.sh:93-139`의 실제 호출 경로를 결합한 것입니다.

## 2. 서버·로컬 연결

현재 서버 설정은 `.github/workflows/verify.yml:48-54`에서 G3 본체와 고장 주입 시험을 연속 실행합니다. 이 줄은 두 스크립트를 현재 서버 검사에 등록합니다.

현재 로컬 훅은 `hooks/pre-push:112-113`에서 이름 모양 수집(glob, 파일명 규칙으로 여러 파일을 찾는 방식)을 사용합니다. 실제 열거 결과에도 두 G3 파일이 있었습니다.

```text
$ [현재 서버의 정확한 실행 줄과 로컬 수집 결과]
CI exact lines:
53:          bash scripts/acceptance-hs-portal-constants.sh
54:          bash scripts/acceptance-hs-portal-constants-mutations.sh
pre-push collected G3 files:
./scripts/acceptance-hs-portal-constants-mutations.sh
./scripts/acceptance-hs-portal-constants.sh
glob expression source:
110:# 글로브로 찾는다. 고정 목록이면 새로 추가된 인수 스크립트를 조용히 누락한다
111:# (2026-08-07 실측: acceptance-9-9.sh 를 추가해도 "검사 2개 실행"으로 통과).
112:found=$(find . -maxdepth 2 \( -name 'verify.sh' -o -name 'acceptance-*.sh' \) \
113:        -not -path './worktrees/*' -not -path './.git/*' | LC_ALL=C sort)
exit=0
```

→ 뭘 시켰나: 서버의 정확한 명령 줄과 로컬 훅이 실제로 찾는 파일을 독립 열거했습니다.  
→ 뭐가 나왔나: 현재 체크아웃에서는 양쪽 모두 같은 두 G3 파일을 가리킵니다.  
→ 좋은 소식인가 나쁜 소식인가: 현재 연결 상태 자체는 좋은 소식입니다.

배선 판정 함수는 `scripts/acceptance-hs-portal-constants.sh:152-167`에 있습니다. 이 줄은 정확한 명령 문자열과 같은 단계 안의 `if:` 및 `continue-on-error`를 검사합니다.

첫 모의 실행은 줄바꿈 입력 실수로 모든 사례가 거부돼 무효였습니다.

```text
valid PARSER_RC=1 (REJECTED)
commented PARSER_RC=1 (REJECTED)
echo PARSER_RC=1 (REJECTED)
suffix PARSER_RC=1 (REJECTED)
condition PARSER_RC=1 (REJECTED)
ignore-error PARSER_RC=1 (REJECTED)
early-exit-bypass PARSER_RC=1 (REJECTED)
disable-errexit-bypass PARSER_RC=1 (REJECTED)
exit=0
```

→ 뭘 시켰나: 서버 연결 판정 코드를 여러 설정 문자열에 적용하려 했습니다.  
→ 뭐가 나왔나: 줄바꿈이 실제 줄이 아니라 문자 두 개로 들어가 정상 사례까지 실패했습니다.  
→ 좋은 소식인가 나쁜 소식인가: 잘못 구성한 실험이므로 판정 근거로 쓰지 않고 바로 교정했습니다.

교정 실행 결과는 다음과 같습니다.

```text
valid PARSER_RC=0 (ACCEPTED)
commented PARSER_RC=1 (REJECTED)
echo PARSER_RC=1 (REJECTED)
suffix PARSER_RC=1 (REJECTED)
condition PARSER_RC=1 (REJECTED)
ignore-error PARSER_RC=1 (REJECTED)
early-exit-bypass PARSER_RC=0 (ACCEPTED)
disable-errexit-bypass PARSER_RC=0 (ACCEPTED)
exit=0
```

→ 뭘 시켰나: 같은 판정 코드에 실제 여러 줄 설정을 넣었습니다.  
→ 뭐가 나왔나: 계약에 열거된 주석·echo·후미 무력화·조건·오류 무시는 잡았지만, 앞선 종료와 실패 중단 해제는 정상으로 받아들였습니다.  
→ 좋은 소식인가 나쁜 소식인가: 열거된 변형 방어는 좋지만 실제 실행을 보장하지 못하므로 전체 판정은 나쁩니다.

실제 셸 동작도 확인했습니다.

```text
early-exit block overall=0 output=''
set-plus-e block overall=0
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
mktemp: mkstemp failed on /private/tmp/tmp.mEEVL3BSzQ: Operation not permitted
exit=0
```

→ 뭘 시켰나: 서버와 같은 실패 시 중단 셸에서 앞선 종료와 실패 중단 해제 변형을 실제 실행했습니다.  
→ 뭐가 나왔나: 첫 변형은 검사기를 전혀 실행하지 않고 0, 둘째는 검사기가 실패했는데도 전체가 0이었습니다.  
→ 좋은 소식인가 나쁜 소식인가: 서버 검사 무력화가 실제로 성립하므로 나쁜 소식입니다.

로컬 머리말 우회도 실행했습니다.

```text
injected_header_hook_action=SKIP scanner_found_self=2 scanner_wiring_result=ACCEPT
current_self_header_matches=no
exit=0
```

→ 뭘 시켰나: G3 파일 상단에 로컬 훅이 건너뛰는 표식이 있다고 가정하고, 훅의 분기와 G3 자기검사의 파일 수 판정을 그대로 실행했습니다.  
→ 뭐가 나왔나: 훅은 건너뛰지만 G3 자기검사는 정상으로 판정했습니다. 현재 원본에는 그 표식이 없습니다.  
→ 좋은 소식인가 나쁜 소식인가: 현재는 연결됐지만 연결 훼손을 자기검사가 막지 못하므로 나쁜 소식입니다.

반증 기록: “정확한 실행 줄이 있으면 반드시 실행된다”를 앞선 종료와 실패 중단 해제로 반증 시도했고 성공했습니다. “로컬 파일 이름 수가 2면 둘 다 실행된다”를 머리말 표식으로 반증 시도했고 성공했습니다.

## 3. 보고 숫자 독립 대조

첫 널 문자 방식은 잘못된 결과를 냈습니다.

```text
humansearch/src/humansearch/__init__.py
INDEPENDENT_PRODUCT_FILES=1
exit=0
```

→ 뭘 시켰나: 널 문자로 구분한 제품 파일 목록을 `awk`로 세려 했습니다.  
→ 뭐가 나왔나: 실제 존재하는 시험 파일을 누락해 1로 잘못 셌습니다.  
→ 좋은 소식인가 나쁜 소식인가: 계산 방법의 실패이며 구현 결함 증거가 아니므로 다른 방법으로 재실행했습니다.

교정한 독립 열거입니다.

```text
humansearch/src/humansearch/__init__.py
humansearch/tests/test_package_boundary.py
INDEPENDENT_PRODUCT_FILES=2
exit=0
```

→ 뭘 시켰나: 추적 파일을 줄 단위로 다시 열거했습니다.  
→ 뭐가 나왔나: 제품 파일은 정확히 2개였습니다.  
→ 좋은 소식인가 나쁜 소식인가: 문서에 기록된 `PRODUCT_FILES: 2`와 맞으므로 좋은 소식입니다.

`CHECKED`의 독립 열거 전문입니다.

```text
.check-weakening-patterns
.claude/settings.json
.claude/skills/gptreview/SKILL.md
.claude/skills/verify/SKILL.md
.claude/skills/verify/local-checks.sh
.github/workflows/verify.yml
.gitignore
.secret-patterns.default
README.md
SKILLS_GUIDE.md
hooks/pre-commit
hooks/pre-push
humansearch/.python-version
humansearch/pyproject.toml
humansearch/src/humansearch/__init__.py
humansearch/tests/test_package_boundary.py
humansearch/uv.lock
scripts/acceptance-0-2.sh
scripts/acceptance-0-5.sh
scripts/acceptance-0-6.sh
scripts/acceptance-0-7.sh
scripts/acceptance-hs-a3.sh
scripts/acceptance-hs-a4.sh
scripts/acceptance-hs-cleanroom-absolute-contexts.sh
scripts/acceptance-hs-cleanroom-absolute-paths.sh
scripts/acceptance-hs-cleanroom-colon-paths.sh
scripts/acceptance-hs-cleanroom-file-urls.sh
scripts/acceptance-hs-cleanroom-hook-env-mutations.sh
scripts/acceptance-hs-cleanroom-hook-env.sh
scripts/acceptance-hs-cleanroom-mutations.sh
scripts/acceptance-hs-cleanroom.sh
scripts/acceptance-hs-gates-antiforge.sh
scripts/acceptance-hs-gates-mutations.sh
scripts/acceptance-hs-gates.sh
scripts/acceptance-hs-portal-constants-mutations.sh
scripts/acceptance-hs-portal-constants.sh
scripts/acceptance-secret-webhook-vendor.sh
scripts/acceptance-verify-ac-m.sh
scripts/check-docs-sot.sh
scripts/hs_import_spy.py
scripts/install-hooks.sh
scripts/scan-data-exposure.sh
scripts/session-status.sh
scripts/verify/check-mechanism-registry.sh
scripts/verify/fixtures/mechanism-registry/dead-target.yaml
scripts/verify/fixtures/mechanism-registry/missing-path.yaml
scripts/verify/fixtures/mechanism-registry/normal.yaml
suppressions.yaml
verify.sh
INDEPENDENT_CHECKED=49
exit=0
```

→ 뭘 시켰나: `contracts/`와 `docs/`를 제외한 추적 파일을 검사기와 같은 경계로 열거했습니다.  
→ 뭐가 나왔나: 정확히 49개였습니다.  
→ 좋은 소식인가 나쁜 소식인가: 문서의 `CHECKED: 49`와 맞고 불필요한 문서 파일을 세지 않았으므로 좋은 소식입니다.

계약 파일 수입니다.

```text
contracts/cleanroom-deny-patterns.txt
contracts/portal-constants-deny-patterns-product.txt
contracts/portal-constants-deny-patterns.txt
INDEPENDENT_CONTRACT_FILES=3
exit=0
```

→ 뭘 시켰나: 루트의 정확한 계약 경로 아래 추적 파일을 셌습니다.  
→ 뭐가 나왔나: 3개였습니다.  
→ 좋은 소식인가 나쁜 소식인가: 문서의 `CONTRACT_FILES: 3`과 맞으므로 좋은 소식입니다.

원본 검사기의 내용 검사 부분을 임시 파일 없이 동일하게 실행한 결과입니다.

```text
READONLY_EQUIVALENT forbidden=0 zones=0 errors=0 PRODUCT_FILES=2 CHECKED=49 CONTRACT_FILES=3
exit=0
```

→ 뭘 시켰나: 현재 추적 파일에 두 규칙을 적용하고 경계·수를 독립 계산했습니다.  
→ 뭐가 나왔나: 현재 내용 위반 0, 계약 구역 위반 0, 읽기 오류 0, 수치 2·49·3이었습니다.  
→ 좋은 소식인가 나쁜 소식인가: 현재 저장소 내용과 수치는 깨끗하다는 좋은 소식이지만, 검사기 자체의 깨끗한 0 실행을 대신 증명하지는 않습니다.

반증 기록: “무관한 파일을 세어 숫자를 부풀렸다”를 독립 목록으로 반증 시도했으나 실패했습니다. 보고 수치는 독립 열거와 일치했습니다.

## 4. 자기 자신·스크립트·계약·문서 제외 여부

`scripts/acceptance-hs-portal-constants.sh:105-139`의 경로 분기는 다음과 같습니다.

- `contracts/*`: 내용 규칙을 적용하지 않고 파일 형식·권한만 검사합니다.
- `docs/*`: 아무 검사와 집계 없이 즉시 건너뜁니다.
- 제품 두 경로: 전역·제품 규칙을 모두 적용합니다.
- 나머지 전부: 전역 규칙만 적용합니다.

따라서 검사기 자신과 `scripts/`는 디렉터리 단위로 제외되지 않았습니다. 그러나 제품 전용 규칙에만 있는 원시 CSS·일반 URL·일반 포트는 `scripts/`에서 탐지하지 못합니다. 형식상 전역 검사 대상이지만 의미상 중요한 규칙이 적용되지 않는 부분 면제입니다.

실제 문서 파일을 전역 규칙에 대조한 결과입니다.

```text
docs/engineering/evidence-2026-08-06/llm-failure-cases.md
docs/engineering/humansearch-g3-portal-constants-goal-2026-08-12.md
docs/engineering/humansearch-v6-founding-spec-2026-08-07.md
docs/engineering/v6-coding-principles-goal-2026-08-06.md
docs/sot/coding-principles.md
DOCS_GLOBAL_PATTERN_MATCH_FILES=5
exit=0
```

→ 뭘 시켰나: 문서 면제가 없었다면 전역 규칙에 걸릴 현재 문서를 찾았습니다.  
→ 뭐가 나왔나: 정당한 설명 자료 5개가 일치했습니다.  
→ 좋은 소식인가 나쁜 소식인가: 면제 필요성은 확인됐지만 디렉터리 전체 면제는 지나치게 넓습니다.

경로 분기를 새 이름으로 실행한 결과입니다.

```text
contracts/allowed.json => CONTRACT_ZONE
x/contracts/locator.py => GLOBAL_ONLY
contracts-evil/locator.json => GLOBAL_ONLY
humansearch/src/humansearch/contracts/locator.json => GLOBAL_PLUS_PRODUCT
docs/run-portal.py => SKIPPED_DOCS
scripts/portal-config.toml => GLOBAL_ONLY
humansearch/src/humansearch/new_suffix.xyz => GLOBAL_PLUS_PRODUCT
exit=0
```

→ 뭘 시켰나: 정확한 계약 경로, 유사 경로, 중첩 경로, 문서 실행 파일, 새 확장자를 경로 분기에 넣었습니다.  
→ 뭐가 나왔나: 계약 유사 경로와 새 확장자는 올바르게 검사됐지만 `docs/run-portal.py`는 건너뛰었습니다.  
→ 좋은 소식인가 나쁜 소식인가: 경계 문자열 처리는 좋지만 문서 전체 면제는 나쁜 소식입니다.

반증 기록: “검사기 자신과 `scripts/`를 몰래 완전 제외했다”를 경로 분기로 반증 시도했으나 실패했습니다. 둘 다 전역 검사를 받습니다. “문서 면제가 안전하다”는 실행 파일 경로로 반증 시도했고 성공했습니다.

## 5. 깨끗한 원본의 정확한 0

직접 실행 3회의 전문입니다.

```text
$ bash scripts/acceptance-hs-portal-constants.sh
git: warning: confstr() failed with code 5; using /tmp instead
mktemp: mkstemp failed on /var/folders/.../tmp.SOPAeVlmrT: Operation not permitted
exit=1

$ TMPDIR=/private/tmp bash scripts/acceptance-hs-portal-constants.sh
git: warning: confstr() failed with code 5; using /tmp instead
mktemp: mkstemp failed on /private/tmp/tmp.qTVR3vmmzQ: Operation not permitted
exit=1

$ TMPDIR=<지정 scratchpad> bash scripts/acceptance-hs-portal-constants.sh
git: warning: confstr() failed with code 5; using /tmp instead
mktemp: mkstemp failed on <지정 scratchpad>/tmp.A47xFux9SL: Operation not permitted
exit=1
```

→ 뭘 시켰나: 기본 위치, `/private/tmp`, 사용자가 지정한 판정 폴더를 각각 임시 위치로 사용해 원본 검사기를 실행했습니다.  
→ 뭐가 나왔나: 세 경우 모두 규칙 검사 전에 임시 파일 생성이 거부됐고 1로 끝났습니다.  
→ 좋은 소식인가 나쁜 소식인가: 깨끗한 트리 0을 확인하지 못했고 검사 불능도 잘못 분류했으므로 나쁜 소식입니다.

`scripts/acceptance-hs-portal-constants.sh:35-38`은 `mktemp` 네 번을 아무 오류 처리 없이 실행하는 줄입니다. `set -e` 때문에 실패 상태 1이 그대로 바깥으로 나갑니다. `:50-67`의 패턴 오류 처리에는 도달하지도 못합니다.

반증 기록: “깨끗한 트리는 정확히 0”을 직접 실행으로 반증 시도했으며, 이 환경에서는 검사 불능 1이 재현됐습니다. 저장소 내용의 오탐은 독립 스캔에서 발견되지 않았지만, 본체 0은 미확인입니다.

## 6. 검사 불능과 고장 주입 시험의 반환값 규율

35건 고장 주입 시험(mutation, 일부러 고장을 넣어 검사 민감도를 확인하는 시험)의 직접 실행 결과입니다.

```text
$ TMPDIR=/private/tmp bash scripts/acceptance-hs-portal-constants-mutations.sh
git: warning: confstr() failed with code 5; using /tmp instead
git: warning: confstr() failed with code 5; using /tmp instead
mktemp: mkdtemp failed on /private/tmp/tmp.l0VczR6Ifx: Operation not permitted
exit=1
```

→ 뭘 시켰나: 내장된 35개 고장 시험을 실행했습니다.  
→ 뭐가 나왔나: 임시 복제 저장소 생성 단계에서 중단되어 실제 사례는 하나도 실행되지 않았습니다.  
→ 좋은 소식인가 나쁜 소식인가: 전량 시험 결과를 독립 확인할 수 없었으므로 나쁜 소식입니다.

규칙 표현식(regex, 특정 문자 모양을 찾는 규칙)의 기초 반환값과 시험 판정 조건을 별도로 실행했습니다.

```text
grep invalid_expression_rc=2 empty_matching_rc=0 missing_file_rc=2
violation-crash-2 actual=2 expected=1 => HARNESS_REJECTS
violation-command-not-found-127 actual=127 expected=1 => HARNESS_REJECTS
true-violation-1 actual=1 expected=1 => HARNESS_ACCEPTS
invalid-pattern-2 actual=2 expected=2 => HARNESS_ACCEPTS
exit=0
```

→ 뭘 시켰나: 깨진 표현식·빈 문자열 일치·파일 부재 결과와 `actual != expected` 비교를 실행했습니다.  
→ 뭐가 나왔나: 2와 127은 위반 성공 1로 세지 않았고, 정확한 1과 검사 불능 2만 각각 받아들였습니다.  
→ 좋은 소식인가 나쁜 소식인가: 고장 시험의 비교 규율은 좋은 소식입니다.

`scripts/acceptance-hs-portal-constants-mutations.sh:123-141`은 실제 반환값이 기대값과 다르면 즉시 시험 전체를 실패시키는 줄입니다. 이 때문에 2나 127을 “차단 성공”으로 잘못 세는 문제는 소스와 독립 실행에서 발견되지 않았습니다.

35개 구성 수는 처음 36으로 잘못 계산한 뒤 교정했습니다.

```text
EXPLICIT_INIT_CASES=28 CI_LOOP_VARIANTS=8 TOTAL_DECLARED_CASES=36
```

→ 뭘 시켰나: 명시 사례와 서버 변형 반복 항목을 자동 계산했습니다.  
→ 뭐가 나왔나: 셸 예약어를 항목으로 잘못 세어 36이 됐습니다.  
→ 좋은 소식인가 나쁜 소식인가: 계산식 오류이므로 교정 전 결과는 증거로 쓰지 않았습니다.

```text
EXPLICIT_INIT_CASES=28 CI_LOOP_VARIANTS=7 TOTAL_DECLARED_CASES=35
exit=0
```

→ 뭘 시켰나: 반복 목록에서 예약어를 제외해 다시 계산했습니다.  
→ 뭐가 나왔나: 선언된 사례는 정확히 35개였습니다.  
→ 좋은 소식인가 나쁜 소식인가: 문서의 35건 주장과 일치하므로 좋은 소식입니다.

반증 기록: “2나 127도 위반 차단으로 센다”를 비교 조건 실행으로 반증 시도했으나 실패했습니다. 정확히 1만 위반 성공으로 셉니다. 다만 35건 자체의 실제 완주는 미확인입니다.

## 7. 계약 경계

현재 계약 파일은 모두 올바른 일반 파일 권한입니다.

```text
100644 9ff24d6f85ad7e8c126c51aabeaac4a836892a2a 0 contracts/cleanroom-deny-patterns.txt
100644 3e13c2b7cce37969ec024b6f51a450e738ede88e 0 contracts/portal-constants-deny-patterns-product.txt
100644 d2243d7565ddaa07bd2c30c5bbe02910611ebc31 0 contracts/portal-constants-deny-patterns.txt
exit=0
```

→ 뭘 시켰나: 추적된 계약 파일의 저장 모드를 열거했습니다.  
→ 뭐가 나왔나: 현재 세 파일 모두 비실행 일반 파일인 100644입니다.  
→ 좋은 소식인가 나쁜 소식인가: 현재 계약 구역은 깨끗하므로 좋은 소식입니다.

`scripts/acceptance-hs-portal-constants.sh:107-125`의 계약 구역 판정을 새 모드와 확장자로 실행했습니다.

```text
contracts/data.json mode=100644 ZONE_VIOLATIONS=0 scanner_exit_if_otherwise_clean=0
contracts/executable.txt mode=100755 ZONE_VIOLATIONS=1 scanner_exit_if_otherwise_clean=1
contracts/link.json mode=120000 ZONE_VIOLATIONS=1 scanner_exit_if_otherwise_clean=1
contracts/run.sh mode=100644 ZONE_VIOLATIONS=1 scanner_exit_if_otherwise_clean=1
contracts/UPPER.YAML mode=100644 ZONE_VIOLATIONS=0 scanner_exit_if_otherwise_clean=0
exit=0
```

→ 뭘 시켰나: 실행 파일, 심볼릭 링크, 금지 확장자, 대문자 허용 확장자를 같은 판정식에 넣었습니다.  
→ 뭐가 나왔나: 실행 파일·링크·셸 파일은 1로 거부하고 정상 데이터 파일은 허용했습니다.  
→ 좋은 소식인가 나쁜 소식인가: 계약 구역 자체의 권한·확장자 방어는 좋은 소식입니다.

`x/contracts/`, `contracts-evil/`, 중첩 `contracts/`가 허용 구역으로 분류되지 않는 것도 앞선 경로 실행에서 확인했습니다.

반증 기록: “유사 계약 경로가 허용된다”를 세 경로로 반증 시도했으나 실패했습니다. “계약 폴더에 실행 파일을 둘 수 있다”를 모드 판정으로 반증 시도했으나 실패했습니다. 전체 복제 저장소에서 실제 1을 확인하는 단계는 건너뜀입니다.

## 8. 표현 변형과 범위 한계

탐지에 성공한 새 변형은 다음과 같습니다.

- 대소문자가 섞인 URL
- 다른 localhost 포트
- FTP 주소
- 새 확장자의 제품 파일
- 대소문자가 섞인 `querySelector`
- 대소문자가 섞인 JobKorea 도메인

탐지에 실패한 계약 대상은 앞서 확인한 8개입니다. 특히 `contracts/portal-constants-deny-patterns-product.txt:9-10`은 도메인 끝부분을 고정 목록으로 제한하는 줄이고, `:12-13`은 localhost와 두 루프백 주소만 포트 형태로 인정하는 줄입니다. `:15-20`은 CSS ID·명시 결합자와 좁은 포트 대입 형태만 인정합니다.

제품 밖 전역 규칙의 추가 결과입니다.

```text
product | unlisted .ai TLD | rc=1 | MISSED | PORTAL = "jobs-r9.vendor.ai"
product | quoted CDP port | rc=1 | MISSED | CDP_PORT = "9333"
product | mapping CDP port | rc=1 | MISSED | CDP_PORT: 9333
product | IPv6 loopback port | rc=1 | MISSED | REMOTE = "[::1]:9333"
global | selector API mixed case | rc=0 | DETECTED | DOCUMENT.QUERYSELECTOR("#login-r9")
global | raw CSS id in scripts | rc=1 | MISSED | LOGIN_SELECTOR = "#login-r9"
global | raw CSS descendant in scripts | rc=1 | MISSED | LOGIN_SELECTOR = ".card-r9 input"
global | ordinary URL outside product | rc=1 | MISSED | ENDPOINT = "https://jobs-r9.vendor.ai"
global | portal brand mixed case | rc=0 | DETECTED | ENDPOINT = "https://WWW.JOBKOREA.CO.KR"
exit=0
```

→ 뭘 시켰나: 제품의 새 도메인·포트와 제품 밖 스크립트의 원시 화면 위치·일반 URL을 각 적용 계층에 대조했습니다.  
→ 뭐가 나왔나: API 이름과 알려진 포털 브랜드만 잡았고 원시 화면 위치와 일반 주소는 놓쳤습니다.  
→ 좋은 소식인가 나쁜 소식인가: 제품 밖 운영 설정을 막지 못하므로 나쁜 소식입니다.

문자열 분할과 이스케이프 표현은 모두 통과했습니다. 사용자가 명시한 대로 “상수를 실행 시 결합해 해석하는 것”은 계약 §1⑦의 비범위이므로 결함이 아니라 알려진 한계로 분류합니다.

- `ENDPOINT = "https" + "://" + "10.77.4.9:9333"` — 알려진 한계
- `r"https:\x2f\x2fjobs-r9\x2eexample\x2eai"` — 실행 시 해석이 필요한 표현이므로 알려진 한계
- 빌드 산출물 — 이번 검증에서 건너뛴 비범위이며 결함으로 세지 않음

반증 기록: 대소문자·새 확장자는 잡았습니다. 새 도메인 끝부분·새 포트 표기·CSS·XPath·IPv6는 반례가 성공했습니다. 문자열 분할·이스케이프는 통과했지만 명시된 비범위로 분류했습니다.

# 계약·구현 원문 근거

- `docs/engineering/humansearch-g3-portal-constants-goal-2026-08-12.md:48-51` — 전체 AC-G3와 0·1 반환 및 최소 수치를 정하는 줄입니다.
- 같은 문서 `:68-123` — 세 상태, 정확한 계약 경계, 문서 면제, 제품 두 루트, 서버·로컬 연결 규칙을 정하는 줄입니다.
- 같은 문서 `:125-136` — 35건 시험이 0·1·2를 정확히 구분해야 한다고 정하는 줄입니다.
- `scripts/acceptance-hs-portal-constants.sh:35-40` — 임시 파일 네 개를 만들고 종료 시 지우는 줄입니다. 생성 실패 처리가 없습니다.
- 같은 파일 `:48-68` — 패턴 파일 부재·빈 내용·깨진 표현식·빈 문자열 일치를 2로 바꾸는 줄입니다.
- 같은 파일 `:81-84` — 추적 파일 열거 실패를 2로 바꾸는 줄입니다.
- 같은 파일 `:93-103` — 실제 내용 탐지와 읽기 오류 집계를 수행하는 줄입니다.
- 같은 파일 `:105-139` — 계약·문서·제품·그 밖의 파일 경계를 나누는 줄입니다.
- 같은 파일 `:152-167` — 서버 실행 줄과 조건·오류 무시 설정을 문자열로 검사하는 줄입니다.
- 같은 파일 `:169-187` — 서버 두 실행 줄과 로컬 파일 이름 수를 확인하는 줄입니다.
- 같은 파일 `:209-227` — 검사 오류와 하한 미달은 2, 실제 위반·연결 훼손은 1로 끝내는 줄입니다.
- `scripts/acceptance-hs-portal-constants-mutations.sh:123-141` — 실제 반환값이 기대값과 정확히 같아야 사례를 세는 줄입니다.
- 같은 파일 `:172-243` — 제품·스크립트·계약 경계·서버 연결 고장 사례를 정의하는 줄입니다.
- 같은 파일 `:260-303` — 검사 불능과 수치 사례를 정의하는 줄입니다.
- `contracts/portal-constants-deny-patterns.txt:7-29` — 전역 API·XPath·브라우저 포트·포털 브랜드 규칙입니다.
- `contracts/portal-constants-deny-patterns-product.txt:6-20` — 제품 URL·도메인·포트·CSS·포트 대입 규칙입니다.
- `.github/workflows/verify.yml:48-54` — 현재 서버가 G3 본체와 35건 시험을 호출하는 줄입니다.
- `hooks/pre-push:112-113` — 로컬 훅이 인수 스크립트를 파일 이름으로 수집하는 줄입니다.
- `hooks/pre-push:121-149` — 머리말 표식이 있으면 해당 검사를 건너뛰는 줄입니다.
- `docs/sot/verification-commands.md:20-28` — 서버 검사 목록에 G3를 네 번째 단계로 기록하는 줄입니다.

# 추가 실행 증거

규칙 계약 자체는 현재 유효했습니다.

```text
contracts/portal-constants-deny-patterns.txt EFFECTIVE=16 EMPTY_PROBE_RC=1
contracts/portal-constants-deny-patterns-product.txt EFFECTIVE=6 EMPTY_PROBE_RC=1
exit=0
```

→ 뭘 시켰나: 주석·빈 줄을 제외한 유효 규칙 수와 빈 문자열 일치 여부를 검사했습니다.  
→ 뭐가 나왔나: 전역 16개, 제품 6개이며 어느 파일도 빈 문자열에 일치하지 않았습니다.  
→ 좋은 소식인가 나쁜 소식인가: 현재 규칙 파일의 문법·공백 방어는 좋은 소식입니다.

두 셸 파일의 문법도 유효했습니다.

```text
$ bash -n scripts/acceptance-hs-portal-constants.sh scripts/acceptance-hs-portal-constants-mutations.sh
(no output)
exit=0
```

→ 뭘 시켰나: 두 셸 파일의 문법을 실행 없이 검사했습니다.  
→ 뭐가 나왔나: 문법 오류가 없었습니다.  
→ 좋은 소식인가 나쁜 소식인가: 문법 측면은 좋은 소식이지만 발견된 논리 결함을 상쇄하지는 않습니다.

RED 고장 시험 파일은 GREEN 이후 변경되지 않았습니다.

```text
$ git diff --exit-code 9bab751..HEAD -- scripts/acceptance-hs-portal-constants-mutations.sh
(no output)
exit=0
```

→ 뭘 시켰나: 고장 시험 파일이 RED 커밋 뒤에 결과에 맞춰 몰래 수정됐는지 대조했습니다.  
→ 뭐가 나왔나: 차이가 없었습니다.  
→ 좋은 소식인가 나쁜 소식인가: 시험을 사후 조작한 증거가 없으므로 좋은 소식입니다.

# 원본 무변형 확인

작업 시작 전과 종료 직전 모두 다음과 같았습니다.

```text
$ git status --porcelain=v1 --untracked-files=all
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
exit=0
```

→ 뭘 시켰나: 원본 저장소의 수정·추가 파일 존재 여부를 전부 확인했습니다.  
→ 뭐가 나왔나: 상태 출력이 비어 있어 추적 변경과 미추적 파일이 없습니다.  
→ 좋은 소식인가 나쁜 소식인가: 원본을 변형하지 않았으므로 좋은 소식입니다.

# 실제 셸 명령 장부

1. `codeaudit` 지침 파일 전체 읽기 — 성공.
2. 시작 시 `git status --porcelain=v1 --untracked-files=all` — 깨끗함.
3. `git log --oneline --decorate -8` — `9bab751`, `b3a3db0`, `7f589d6`, 현재 `e80a50a` 확인.
4. `git show --stat e80a50a` — 현재 추가 커밋은 계약 문서만 변경.
5. 저장소 내부 `AGENTS.md` 검색 — 없음.
6. 계약 문서 줄번호 포함 읽기 — 성공.
7. G3 본체 줄번호 포함 전체 읽기 — 성공.
8. 전역 패턴 파일 전체 읽기 — 성공.
9. 제품 패턴 파일 전체 읽기 — 성공.
10. 35건 시험 파일 전체 읽기 — 성공.
11. 서버 설정 파일 관련 범위 읽기 — 성공.
12. 로컬 훅 관련 범위 읽기 — 성공.
13. 검증 명령 문서의 G3 항목 검색 — 성공.
14. RED 이후 시험 파일 차이 검사 — 차이 없음.
15. 기본 임시 위치에서 G3 직접 실행 — 임시 파일 거부, 1.
16. `/private/tmp`에서 G3 직접 실행 — 임시 파일 거부, 1.
17. 지정 판정 폴더 접근권한 확인 — 디렉터리 읽기 가능.
18. 지정 판정 폴더를 임시 위치로 G3 실행 — 생성 거부, 1.
19. 지정 판정 폴더 기존 내용 열거 — 기존 `g3-green` 자료 3개 확인.
20. 35건 시험 직접 실행 — 임시 복제 저장소 생성 거부, 1.
21. 널 문자 방식 제품 파일 계산 — 잘못된 1, 폐기.
22. 제품 시험 디렉터리 실파일 확인 — 시험 파일 존재.
23. 시험 파일 무시 여부 확인 — 무시되지 않음.
24. 시험 파일 추적 상태 확인 — 추적됨.
25. 제품 파일 단순 열거 — 2개 확인.
26. 교정 제품 파일 계산 — 2.
27. 전체 검사 대상 독립 열거 — 49.
28. 계약 파일 독립 열거 — 3.
29. 임시 파일 없는 내용·경계 독립 검사 — 위반 0, 2·49·3.
30. 두 규칙 파일 유효 규칙·빈 문자열 검사 — 16·6, 정상.
31. 첫 새 표현 묶음 검사 — 탐지와 미탐 혼재.
32. 추가 표현 묶음 검사 — 새 도메인·포트·제품 밖 원시 표현 미탐.
33. 두 규칙 합산 8개 반례 검사 — 모두 미탐.
34. 서버 배선 첫 모의 실행 — 줄바꿈 입력 오류로 무효.
35. 서버 배선 교정 모의 실행 — 표준 훼손 차단, 새 우회 2개 허용.
36. 새 서버 우회 실제 셸 실행 — 전체 결과 0 재현.
37. 현재 서버 실행 줄과 로컬 수집 결과 대조 — 동일 G3 두 파일 확인.
38. 임시 파일 없는 문서 영향 검사 — 문서 5개가 전역 규칙과 일치.
39. 정확·유사·중첩·문서·새 확장자 경로 분기 실행 — 문서만 전면 제외.
40. 현재 계약 파일 저장 모드 열거 — 모두 100644.
41. 계약 파일 모드·확장자 분기 실행 — 실행·링크·셸 파일 거부.
42. 깨진 규칙과 시험 반환값 비교 실행 — 2·127을 위반 성공으로 세지 않음.
43. 첫 35건 구성 수 계산 — 잘못된 36, 폐기.
44. 교정 35건 구성 수 계산 — 35.
45. 중간 원본 상태 확인 — 깨끗함.
46. 로컬 머리말 우회 실행 — 훅은 건너뛰고 자기검사는 정상 판정.
47. 새 반례가 기존 시험에 있는지 검색 — 해당 새 값·서버 우회 사례 없음.
48. 두 셸 파일 문법 검사 — 성공.
49. 문서 형식 검사기 소스 읽기 — 성공, 판정 파일 생성 불가로 실제 적용은 건너뜀.
50. 최종 원본 상태 확인 — 깨끗함.

실행 전에 정책으로 거부된 문서 조사 명령 1개와 파일 생성 요청 1개는 실제 셸 명령 수에 넣지 않았습니다.

COMMANDS_RUN: 50

Codex session ID: 019ff45c-457f-70d1-a9ad-0377a4a1992d
Resume in Codex: codex resume 019ff45c-457f-70d1-a9ad-0377a4a1992d

---8<--- codex verdict 원문 끝 ---8<---

### V1 2차 — codex (2026-08-12, VERDICT: FAIL — 수정 후 상태 fb512e1 재판정)

- 검증자 신분: 실제 codex CLI 세션 `019ff482-c681-7563-9a08-1e687bbd4934`, companion job `task-mspo3dni-8ltnc9`, 실행 명령 52개, 소요 38분. 이번엔 판정 파일을 직접 작성함.
- 원문 보관: `.claude/private-reviews/codex-g3-verdict2-2026-08-12.md` (SHA-256 `661fcb4fd8e926868ed71de0971d9bedf21de909319343df1f11fd5f3e733a8a`) + 아래 전문 100%.
- 판정 요지: **1차 결함 5건(D1~D5)의 봉쇄는 전부 "구현 확인"** (R1~R5). RED 불변도 확인(N6).
  단 신규 결함 — N1 새 직접 표현 10종 미탐(높음) · N2 CI run 블록을 셸 `if false; then`으로 감싸면
  실행 0회인데 배선 검사 통과(치명) · N3 hardening CI 줄 삭제 무방비(높음) · N4 pre-push 선행
  exit 0(중간, 0-7 이 백업) · N5 hardening 요약 숫자에 배선 확인 1건 혼입(높음) · N7 문서 2곳이
  D5 이전 설명 잔존(중간).

### 조치 — 3차 RED→GREEN (RED3 `8e00bff` · GREEN3 `918b882`)

- RED3 (`scripts/acceptance-hs-portal-constants-hardening2.sh`, 16케이스): codex 의 payload 10종
  원문 그대로 + 셸 감싸기 + 이물질 줄 + hardening 줄 삭제 + pre-push 선행 exit 0. 커밋 직전
  실측: `FAIL: hardening2 [N1-1 미등재 .biz 도메인] exit=0 (기대: 정확히 1)` → exit 1 (올바른 이유의 RED).
- GREEN3 (`918b882`):
  · N2 — G3 스텝 블록을 **허용 목록**으로 검사(주석·빈 줄·`run: |`·G3 실행 줄 외 전부 배선 훼손).
    셸 제어문·선행 종료·실패 중단 해제·echo·후미 무력화가 한 규칙으로 잡힌다.
  · N3 — 존재하는 G3 파일 전부의 CI 줄을 검사기가 요구(파일 목록 → 요구 자동 파생) + pre-push
    무조건 `exit 0` 줄 거부. 잔여 한계: 검사 파일 자체 삭제는 diff·P13 라벨·RED 원장 분모로 노출.
  · N1 — 제품 계층 범주 확장: 따옴표 3라벨 호스트·단일라벨 호스트:포트·1자리 포트·따옴표 포트 키·
    CDP 대역 값(9200~9399 대입)·따옴표 값 CSS 속성·id 자손·백틱 인용·절대/술어 XPath·TLD 대폭 확장.
  · N5 — hardening2 요약이 차단·baseline·배선확인을 분리 보고 (`blocked-mutations 14, clean-baselines 1,
    wiring-present 1`). 동결된 hardening 의 `blocked 15/18` 은 배선 확인 1건 포함으로 **읽어야 한다**(정오표).
  · N7 — goal §1⑩ docs 면제 문구와 전역 패턴 주석을 조건부 면제로 일치.
  · N4 — pre-push 선행 exit 0 가드 추가, acceptance-0-7 백업은 그대로 유지.

```text
GREEN3 재검증 (2026-08-12 15:36~15:47 KST):
  hardening2: cases 16 (blocked-mutations 14, clean-baselines 1, wiring-present 1) exit=0
  동결 회귀: mutations 24/35 exit=0 · hardening 15/18 exit=0 · RED 파일 3벌 diff 0줄
  실저장소 검사기 exit=0 (PRODUCT_FILES 2 · CHECKED 51 · CONTRACT_FILES 3)
  G1 8종·G2 3종·AC-S1·AC-M·0-2/0-5/0-6/a3/a4·verify.sh·bash -n 30개 전부 exit=0
  pre-push 실호출: 검사 21개 전부 ok · session-status → RED: 0/23
```
→ 뭘 했나: 3차 봉쇄 후 1·2차와 같은 검증 전량을 다시 돌렸습니다.
→ 결과: 전부 통과. 분모 23은 G3 검사 파일 4개(본체+시험 3벌) 추가분입니다.
→ 의미: 2차 판정의 신규 결함까지 시험으로 고정해 봉쇄했고 기존 검사는 하나도 깨지 않았습니다.

### V1 2차 판정 원문 (100% — 아래 전문은 수정 없이 그대로다)

---8<--- codex verdict 2차 원문 시작 ---8<---

VERDICT: FAIL

# 결론

현재 상태로는 승인하시면 안 됩니다. 오늘 낮에 확인한 다섯 문제에 맞춘 예시는 모두 막혔지만, 같은 종류의 값을 다른 흔한 방식으로 적은 10개 사례가 아무 문제 없는 것으로 받아들여졌습니다.

서버의 세 검사 명령을 실행하지 않는 조건 안에 넣어도 모든 자체 점검이 정상으로 끝났습니다. 서버 목록에서 새 보강 시험 한 줄만 지워도 남은 검사들은 이를 알아채지 못했습니다.

새 보강 시험 파일과 원래 시험 파일은 만든 뒤 바뀌지 않았고, 18개라는 전체 숫자도 맞습니다. 다만 “15개를 막았다”는 숫자에는 실제로 고장을 심어 막은 사례가 아니라 현재 서버 목록에 자기 줄이 있다는 확인 1개가 섞여 있습니다.

문서 폴더 안의 실행용 파일을 숨기던 기존 문제, 임시 작업공간을 만들 수 없을 때의 잘못된 보고, 기존 서버·로컬 우회 예시는 실제로 고쳐졌습니다. 따라서 구현자의 “다섯 재현 사례 수정” 주장은 맞지만, “더는 우회할 수 없다”는 주장은 틀립니다.

## 먼저 공개하는 건너뜀·미확인·재시도

- 확인한 사실: 현재 작업 위치는 `fb512e11ab1ff725d9992aead782c0a3b787ac6a`이고 원본 작업 공간은 감사 전후 모두 깨끗했습니다.
- 확인한 사실: 인터넷은 사용하지 않았고, 저장소 밖 서비스에도 접속하지 않았습니다.
- ※ 미확인: 실제 GitHub 서버는 인터넷 차단 조건 때문에 실행하지 못했습니다. 대신 동일한 Bash 실행 묶음을 로컬 복제본에서 실행했고, 실행 결과가 0이며 출력이 0바이트인 것을 확인했습니다.
- ※ 건너뜀: G1·G2와 저장소 전체 제품 시험은 다시 돌리지 않았습니다. 이번 판정 범위인 G3 본체, 원래 35건, 새 18건, 세 G3 파일의 셸 문법은 모두 새로 실행했습니다.
- ※ 한계: 새로운 표기법을 무한히 전수할 수는 없습니다. 이번에는 1차에서 쓰지 않은 직접 표기 10종, 서버 설정 2종, 로컬 훅 설정 1종을 추가 공격했습니다.
- 재시도 1: 읽기 전용 탐색 도구는 Rust 실행 파일이 없어 시작하지 못했습니다. 표준 저장소 검색으로 같은 범위를 다시 확인했습니다.
- 재시도 2: 따옴표가 겹치는 세 입력을 처음에는 문자 그대로의 `\x27`·`\x60`으로 잘못 전달했습니다. 그 결과는 결함 근거에서 제외하고, 실제 작은따옴표와 역따옴표를 넣어 다시 실행했습니다.
- 재시도 3: 새 표현 10종 묶음은 처음 5종 뒤에 입력 전달이 중단됐습니다. 앞 5종은 유효한 결과로 보존하고, 뒤 5종을 별도 복제본에서 다시 실행했습니다.
- 재시도 4: 18건 수를 처음 정적 계산할 때 함수 안의 증가 문장 자체를 한 번 더 더해 19라고 잘못 셌습니다. 함수 호출 17회와 함수 밖 증가 1회로 다시 계산해 18임을 확인했습니다.
- 재시도 5: 동결 파일 비교 명령 두 번과 독립 재현 명령 한 번은 명령 전달기의 변수 해석 오류로 제품 검사 전에 중단됐습니다. 파일 변경은 없었고, 변수 표기만 바꿔 다시 실행했습니다.
- 재시도 6: 지정 경로에 패치로 직접 쓰는 작업은 패치 도구의 작업 저장소 경계에 막혔습니다. 저장소 안 임시 문서를 패치로 만든 뒤 지정 경로로 복사하고 임시 문서를 다시 패치로 삭제하는 방식으로 바꿨습니다.

→ 뭘 공개했나: 실행하지 못한 외부 확인, 범위 밖 회귀시험, 조사 도구 실패, 입력 전달 실수와 재계산을 판정 앞부분에 모두 적었습니다.  
→ 뭐가 나왔나: G3 핵심 판단에는 실행 공백이 없고, 실제 GitHub 서버만 ※ 미확인입니다.  
→ 좋은 소식인가 나쁜 소식인가: 판정 근거는 로컬에서 재현됐지만 실제 서버 이력은 증명하지 못했으므로 제한적으로 나쁜 소식입니다.

# 판단 근거

## 판정 기준과 갈림길

종료 코드(exit code, 프로그램이 끝날 때 운영체제에 돌려주는 숫자)는 계약대로 0은 정상 완료, 1은 실제 위반 발견, 2는 신뢰할 수 있는 검사를 시작하거나 끝내지 못함으로 채점했습니다.

CI(변경을 서버에서 자동으로 검사하는 절차)는 실행 명령이 글자로 적혀 있는지만 보지 않고 실제로 실행되는지를 기준으로 판단했습니다. `if false; then` 안의 명령은 파일에 보이지만 Bash가 실행하지 않으므로 배선이 온전하다고 볼 수 없습니다.

정규식(문자 모양을 찾는 규칙) 목록의 현재 항목만 금지 범위라고 보는 좁은 해석은 버렸습니다. `docs/engineering/humansearch-g3-portal-constants-goal-2026-08-12.md:48-51`은 주소·포트·도메인·화면 위치·XPath가 정확한 계약 폴더 밖에 있으면 로컬과 서버 양쪽에서 1로 거부하라고 정하며, `:107-109`도 제품 코드의 일반 도메인·호스트와 포트·화면 위치·포트 대입을 범주로 적습니다.

TLD(인터넷 도메인의 마지막 부분) 목록을 현재 파일에 열거한 항목만 계약이라고 보는 해석도 버렸습니다. 1차에서 `.ai`가 목록에 없다는 이유로 결함이었고 이번 수정은 일부 끝자리만 더했으므로, 같은 제품 경로의 직접적인 `.biz` 표기를 정상으로 받는 것은 같은 결함 종류입니다.

CSS selector(웹 화면의 특정 요소를 찾는 표현)와 XPath(웹 화면 구조에서 요소를 찾는 경로 표현)는 한 가지 따옴표나 한 가지 술어 모양에만 한정된다는 문서가 없습니다. 이번 반례는 조각을 합치거나 문자를 숨기지 않은 한 줄짜리 직접 값이므로 사용자가 명시한 비범위가 아닙니다.

반대로 다음은 결함으로 세지 않았습니다. 제품 루트 밖의 원시 CSS·일반 URL, `humansearch/` 바로 아래 비코드 설정, 문자열 조각 조립, 문자 이스케이프, 빌드 산출물은 사용자가 수용 한계로 명시했기 때문입니다. 실행 권한 없는 `.md`·`.yaml`·`.yml`·`.txt`·`.html` 문서의 면제도 이번 지시의 설계 범위로 받아들였습니다.

이 해석이 틀리면 제품 코드에 `{"port": 9333}`, `portal:9444`, `'#login input'` 같은 값이 들어가도 품질 검사에 합격하고, 서버 설정에는 검사 명령 세 줄이 보이지만 실제로는 한 줄도 실행되지 않는 상태를 승인하게 됩니다.

## 요구사항별 최종 판정

| ID | 요구 | 판정 | 핵심 근거 | 반증 결과 | 심각도와 사업 영향 |
|---|---|---|---|---|---|
| R1 | 1차 미탐 8종 재검사 | 구현 확인 | 두 최종 패턴 직접 대조 8/8 탐지, 독립 깊은 경로 `.ai`도 1 | “고정 파일명만 겨냥”을 새 경로·새 확장자로 반증 시도했으나 실패 | 해당 8종은 해소됨 |
| R2 | D2 두 우회 봉쇄 | 구현 확인 | 선행 `exit 0`, `set +e` 각각 배선 훼손 1 | 독립 복제본에서도 각각 1 | 해당 두 예시는 해소됨 |
| R3 | D3 세 G3 파일 머리말 봉쇄 | 구현 확인 | 본체·원 시험·보강 시험 세 파일 모두 머리말 주입 시 1 | 보강 시험이 직접 시험하지 않은 세 번째 파일도 독립 실행에서 1 | 해당 예시는 해소됨 |
| R4 | D4 임시 작업공간 실패는 2 | 구현 확인 | 소스 35-40행 가드, 가짜 `mktemp` 실행 결과 2와 정확한 문구 | “1이 샐 것”을 재현 시도했으나 실패 | 운영자가 위반과 환경 고장을 구분 가능 |
| R5 | D5 문서 폴더 통 면제 축소 | 구현 확인 | `.py` 1, 실행 가능 `.HTML` 1, 비실행 `.MD` 0 | 새 파일명·대문자 확장자로 반증 시도했으나 실패 | 문서 폴더를 코드 은닉처로 쓰던 기존 구멍 해소 |
| N1 | 새 직접 표현 공격 | 미구현 | 제품 루트의 10종이 모두 본체 0 | “확장된 규칙이 같은 범주 변형도 잡을 것”을 반증했고 반례 10건 성공 | 높음 — 운영 주소·포트·화면 위치가 다시 코드에 박혀도 병합 가능 |
| N2 | 서버 명령이 실제 실행되는지 | 미구현 | 셸 `if false; then` 안에 세 줄을 넣자 본체·35건·18건 모두 0, 실제 묶음도 0·출력 0바이트 | “정확한 실행 줄 검사가 실행을 증명한다”를 반증했고 우회 성공 | 치명적 — 서버 화면은 정상인데 G3 전체가 한 번도 실행되지 않은 변경 승인 가능 |
| N3 | 보강 시험 자체의 서버 배선 | 미구현 | 보강 시험 줄 삭제 뒤 본체 0·원 시험 0·서버 묶음 0 | 보강 시험을 수동 실행해야만 1; 삭제된 서버에서는 그 1이 발생 불가 | 높음 — 향후 다섯 결함의 회귀 방어를 서버에서 조용히 제거 가능 |
| N4 | 로컬 훅의 실제 실행 | 부분 구현 | 훅 2행 `exit 0` 뒤 G3 본체·35건·18건 모두 0, 실제 훅도 0·무출력 | 저장소 전체의 별도 0-7 시험은 이 훅 변형을 1로 차단 | 중간 — G3 자체의 로컬 자기보호는 사라지지만 현재 서버의 별도 장치가 백업 |
| N5 | 시험 연출·숫자·종료값 | 부분 구현 | 전체 18은 맞고 14건만 실제 1, 1건은 2, 2건은 0, 나머지 1건은 현재 줄 존재 확인 | 정확한 종료값 혼동과 고정 파일명 겨냥은 발견 못함; 자기 배선 음성 시험은 빠짐 | 높음 — “15개 차단”이라는 숫자가 서버에서 시험 제거를 막는다는 잘못된 확신 제공 |
| N6 | RED 파일 불변 | 구현 확인 | 두 파일의 Git 객체와 SHA-256이 기준 커밋과 HEAD에서 동일, 후속 접촉 커밋 없음 | “GREEN이 시험을 바꿨다”를 반증 시도했으나 실패 | 시험 원본 보존 신뢰 가능 |
| N7 | 계약과 설명 일치 | 불일치 | goal 93-95행과 전역 패턴 주석 2행은 여전히 docs 전체 면제라고 설명하지만 본체는 조건부 면제 | “문서도 수정됐다”는 해석을 현재 줄로 반증 | 중간 — 다음 수정자가 낡은 설명을 따라 방어를 되돌릴 위험 |

→ 뭘 대조했나: 사용자의 다섯 검증 항목을 기존 결함, 새 공격, 시험 정직성, 동결성, 문서 일치로 분해했습니다.  
→ 뭐가 나왔나: 기존 다섯 예시는 고쳐졌지만 새 결함 세 축과 문서 불일치가 확인됐습니다.  
→ 좋은 소식인가 나쁜 소식인가: 일부 수정은 진짜이나 최종 봉쇄는 아니므로 전체로는 나쁜 소식입니다.

## 갈림길에서 버린 해석

1. “18건이 통과했으니 합격”은 버렸습니다. 18건은 이미 아는 표현과 설정만 재현하며, 실제로 새 직접 표현 10개와 셸 조건문을 포함하지 않습니다.
2. “명령 줄이 정확히 존재하니 실행된다”는 해석은 버렸습니다. 로컬 Bash 실행에서 조건문 안의 세 줄이 0바이트 출력으로 한 번도 실행되지 않았습니다.
3. “보강 시험이 자기 줄을 확인하니 삭제를 막는다”는 해석은 버렸습니다. 그 줄을 지우면 확인 주체도 서버에서 사라지고, 남은 두 명령은 0으로 끝났습니다.
4. “로컬 훅 선행 종료도 최종 우회”는 일부 버렸습니다. G3 자체는 놓쳤지만 별도 `acceptance-0-7.sh`가 1로 차단했으므로 저장소 전체 서버 방어까지 사라진 것은 아닙니다.
5. “패턴 파일에 적지 않은 표현은 계약 밖”은 버렸습니다. 상위 계약이 범주를 먼저 정하고 패턴 파일은 그 범주를 구현하는 수단이기 때문입니다.

## 설계 결정 카드 1 — 제품 표현을 유한 패턴 목록으로 막기

**무엇을** — 제품 파일의 주소·포트·화면 위치를 정규식 목록으로 찾습니다.  
**왜** — 현재 저장소에 새 부품을 추가하지 않고 빠르게 전 파일을 검사하며, 패턴 파일만 늘릴 수 있기 때문입니다.  
**버린 대안** — 언어별 구문 분석과 설정 형식별 키 검증, 또는 제품 코드에서 외부 값을 전부 금지하고 계약 로더만 허용하는 구조는 채택하지 않았습니다.  
**대가** — 따옴표·키 이름·경로 문법이 바뀔 때마다 직접 값도 통과하며, 이번에 10종이 실제 0으로 끝났습니다.  
**되돌리는 법** — 포트·도메인·화면 위치별로 문법 가족을 먼저 정의하고 음성 시험을 늘리거나, 제품 코드가 계약 로더 외 문자열 상수를 갖지 못하게 검사 범위를 뒤집은 뒤 정상 자료를 좁게 허용하시면 됩니다.

## 설계 결정 카드 2 — 서버 설정을 문자열로 읽어 실행 여부 판단하기

**무엇을** — `awk`가 스텝 안의 정확한 두 실행 줄과 일부 금지 줄을 문자열로 찾습니다.  
**왜** — 별도 YAML 처리기 없이 저장소 기본 도구만으로 빠르게 배선 손상을 찾기 위해서입니다.  
**버린 대안** — 실행 증명 표식, 구조화된 YAML 검사, G3 전용 단일 실행 스크립트와 외부 독립 점검은 쓰지 않았습니다. `hooks/pre-push:82-85`도 문자열 파싱은 변형마다 새 우회가 생긴다고 이미 기록합니다.  
**대가** — 셸 조건문처럼 금지 목록에 없는 제어문을 넣으면 명령은 보이지만 실행되지 않으며, 이번 로컬 실행에서 그대로 재현됐습니다.  
**되돌리는 법** — G3 세 명령을 하나의 전용 실행 스크립트로 고정하고, 서버 설정은 구조적으로 읽어 조건·셸 변경을 거부하며, 실행 후 독립 표식을 확인하는 별도 단계로 검증하시면 됩니다.

## 설계 결정 카드 3 — 문서 확장자와 Git 권한으로 문서 면제하기

**무엇을** — `docs/` 중 다섯 문서 확장자이며 Git 모드가 100644인 파일만 검사에서 뺍니다.  
**왜** — 현재 정당한 문서가 포털 사례를 포함해 전역 규칙의 오탐을 만들기 때문입니다.  
**버린 대안** — 문서 전체 면제와 문서별 허용 목록 중 전자는 D5 때문에 폐기됐고, 후자는 채택하지 않았습니다.  
**대가** — 구현은 좁아졌지만 goal 계약과 패턴 주석은 옛 전체 면제를 계속 설명합니다.  
**되돌리는 법** — goal 93-95행과 패턴 주석 2행을 현재 조건으로 고치고, 다섯 확장자의 허용·실행 권한 거부 사례를 정본 시험에 함께 고정하시면 됩니다.

# 기술 상세

## 1. 현재 상태와 계약 원문

`docs/engineering/humansearch-g3-portal-constants-goal-2026-08-12.md:48-51`은 금지 범주와 양쪽 거부를 정하는 줄입니다.

```text
48:**AC-G3**: While 저장소에 제품 코드가 존재하는 동안, If 운영 상수·portal locator(URL·포트·도메인·
49-CSS selector·XPath·CDP 포트)가 저장소 루트의 정확한 `contracts/` 밖에 존재하면, Then 시스템은
50-로컬(pre-push)과 CI 양쪽에서 **정확히 exit 1**로 거부해야 한다. 깨끗한 트리는 **정확히 exit 0**이며
51-검사 파일 수(PRODUCT_FILES ≥ 2, CHECKED ≥ 10, CONTRACT_FILES ≥ 2)를 보고해야 한다.
```

→ 뭘 확인했나: 가장 상위의 합격 기준을 읽었습니다.  
→ 뭐가 나왔나: 표현 종류 전체와 로컬·서버 양쪽 거부를 요구합니다.  
→ 좋은 소식인가 나쁜 소식인가: 새 반례와 직접 충돌하므로 나쁜 소식입니다.

`scripts/acceptance-hs-portal-constants.sh:35-40`은 임시 작업공간 실패를 2로 바꾸는 줄입니다.

```text
35 # 임시 작업공간 생성 실패는 위반(1)이 아니라 검사 불능(2)이다 — set -e 에 맡기면
36 # mktemp 의 1 이 그대로 새어 나가 규칙 위반과 환경 고장이 구분되지 않는다 (V1 결함 D4).
37 GCLEAN=$(mktemp) || { echo "FAIL: temp workspace unavailable"; exit 2; }
38 PCLEAN=$(mktemp) || { echo "FAIL: temp workspace unavailable"; exit 2; }
39 FILES=$(mktemp) || { echo "FAIL: temp workspace unavailable"; exit 2; }
40 ERRS=$(mktemp) || { echo "FAIL: temp workspace unavailable"; exit 2; }
```

→ 뭘 확인했나: 네 번의 임시 파일 생성 각각에 같은 보호가 있는지 읽었습니다.  
→ 뭐가 나왔나: 실패 문구와 숫자 2가 네 줄 모두에 명시됐습니다.  
→ 좋은 소식인가 나쁜 소식인가: D4에는 좋은 소식입니다.

`scripts/acceptance-hs-portal-constants.sh:129-150`은 문서 면제와 제품 경로를 나누는 줄입니다.

```text
129     docs/*)
130       # 문서 면제는 디렉터리 전체가 아니라 "문서 확장자 + 정규 비실행 파일"에만 준다.
131       # 통 면제는 docs/run-portal.py 같은 실행 코드의 은닉 경로가 된다 (V1 결함 D5).
132       lower=$(printf '%s' "$path" | tr '[:upper:]' '[:lower:]')
133       mode=$(git ls-files -s -- "$path" | awk '{print $1}')
134       case "$lower" in
135         *.md|*.yaml|*.yml|*.txt|*.html)
136           if [ "$mode" = "100644" ]; then continue; fi
137           ;;
138       esac
139       # 문서 형식이 아니거나 실행 가능한 docs 파일 → 전역 검사로 계속 진행
140       ;;
141   esac
142   checked=$((checked + 1))
143   case "$path" in
144     humansearch/src/*|humansearch/tests/*)
145       product_files=$((product_files + 1))
146       scan_with "$path" "$GCLEAN" global
147       scan_with "$path" "$PCLEAN" product
148       ;;
149     *)
150       scan_with "$path" "$GCLEAN" global
```

→ 뭘 확인했나: 문서와 제품 파일이 실제로 어느 규칙으로 가는지 읽었습니다.  
→ 뭐가 나왔나: 다섯 문서 확장자·100644만 면제되고 제품 두 루트는 두 패턴 모두 적용됩니다.  
→ 좋은 소식인가 나쁜 소식인가: D5 수정은 좋지만 goal의 옛 설명과 달라 문서 불일치는 나쁜 소식입니다.

`scripts/acceptance-hs-portal-constants.sh:165-182`는 서버 배선을 문자열로 판정하는 줄입니다.

```text
165 ci_line_ok() {
166   local tgt="$1"
167   awk -v tgt="$tgt" '
168     function flush() { if (has && ok) good = 1 }
169     /^[[:space:]]*-[[:space:]]*name:/ { flush(); has = 0; ok = 1 }
170     {
171       line = $0
172       sub(/^[[:space:]]+/, "", line)
173       sub(/[[:space:]]+$/, "", line)
174       if (line == tgt) has = 1
175       if (line ~ /^if:/) ok = 0
176       if (index(line, "continue" "-on-" "error") > 0) ok = 0
177       # run 블록 안의 선행 종료·실패 중단 해제는 "줄은 있지만 실행되지 않는" 우회다 (V1 결함 D2)
178       if (line ~ /^exit([[:space:]]|$)/) ok = 0
179       if (line ~ /^set[[:space:]]+\+e([[:space:]]|$)/) ok = 0
180     }
181     END { flush(); exit good ? 0 : 1 }
182   ' "$WF"
```

→ 뭘 확인했나: 서버 실행 여부를 어떤 문장으로 거부하는지 읽었습니다.  
→ 뭐가 나왔나: YAML의 `if:`와 두 특정 셸 문장만 막고 `if false; then`은 막지 않습니다.  
→ 좋은 소식인가 나쁜 소식인가: 이미 아는 두 예시는 막지만 같은 원인의 새 우회가 남아 나쁜 소식입니다.

`scripts/acceptance-hs-portal-constants.sh:198-214`는 G3 이름 3종 모두의 첫 20줄을 확인하는 줄입니다.

```text
198   found_self=$(find . -maxdepth 2 -name 'acceptance-*.sh' \
199     -not -path './worktrees/*' -not -path './.git/*' | grep -cF 'acceptance-hs-portal-constants')
200   if [ "$found_self" -lt 2 ]; then
201     wire_bad "글로브 수집 재현에서 검사기·mutation 이 다 잡히지 않는다 (found=$found_self)"
202   fi
203   # pre-push 는 파일 첫 20줄의 건너뛰기 표식을 보고 검사를 CI 로 넘긴다. G3 파일에 그
204   # 표식이 붙으면 로컬 절반이 조용히 사라지므로 여기서 차단한다 (V1 결함 D3).
205   G3_MARK=$(printf '# PUSH-%s' 'PERFORMING')
206   while IFS= read -r g3f; do
207     if [ -z "$g3f" ]; then continue; fi
208     if head -20 "$g3f" | grep -qF "$G3_MARK"; then
209       wire_bad "G3 검사 파일이 pre-push 건너뛰기 표식을 달고 있다: $g3f"
210     fi
211   done <<G3LIST
212 $(find . -maxdepth 2 -name 'acceptance-hs-portal-constants*.sh' \
213     -not -path './worktrees/*' -not -path './.git/*')
214 G3LIST
```

→ 뭘 확인했나: 구현자가 말한 “G3 파일 3종의 첫 20줄”이 이름 고정 두 개가 아닌 전체 이름 모양인지 읽었습니다.  
→ 뭐가 나왔나: `acceptance-hs-portal-constants*.sh` 전체를 확인하며 독립 실행에서도 세 파일 모두 1이었습니다.  
→ 좋은 소식인가 나쁜 소식인가: D3에는 좋은 소식입니다.

## 2. 깨끗한 현재 저장소와 두 정본 시험 실행 전문

```text
$ bash scripts/acceptance-hs-portal-constants.sh
PASS: portal constants outside contracts 0
PASS: contracts zone violations 0
PASS: ci/pre-push wiring intact
PRODUCT_FILES: 2
CHECKED: 50
CONTRACT_FILES: 3
RC=0
```

→ 뭘 시켰나: 현재 HEAD의 G3 본체를 실행했습니다.  
→ 뭐가 나왔나: 현재 내용은 0, 수치는 2·50·3, 배선은 정상이라고 보고했습니다.  
→ 좋은 소식인가 나쁜 소식인가: 현재 저장소 내용 자체에는 좋은 소식이지만 새 공격까지 증명하지는 않습니다.

```text
$ bash scripts/acceptance-hs-portal-constants-mutations.sh
ok [clean baseline] exit=0
ok [product scheme URL (.py)] exit=1
ok [product bare domain (tests/.py)] exit=1
ok [product host:port (무작위 파일명)] exit=1
ok [product selector API (.js)] exit=1
ok [product XPath literal] exit=1
ok [product quoted CSS id] exit=1
ok [scripts/ selector API — scripts 면제 금지] exit=1
ok [검사기 자신에 심은 selector — 자기면제 금지] exit=1
ok [루트 파일 CDP 플래그] exit=1
ok [hooks/ 포털 브랜드 도메인] exit=1
ok [루트 contracts/ 정당 값 — 오탐 금지] exit=0
ok [contracts-evil/ 유사 경로 위장] exit=1
ok [중첩 가짜 contracts/ 경로] exit=1
ok [contracts/ 실행 권한 파일] exit=1
ok [contracts/ 허용 확장자 밖] exit=1
ok [CI 무력화: self_commented] exit=1
ok [CI 무력화: self_missing] exit=1
ok [CI 무력화: echo_prefixed] exit=1
ok [CI 무력화: suffixed] exit=1
ok [CI 무력화: if_false] exit=1
ok [CI 무력화: coe] exit=1
ok [CI 무력화: sibling_missing] exit=1
ok [pre-push 부재] exit=1
ok [pre-push 실행권한 제거] exit=1
ok [pre-push 글로브 수집식 제거] exit=1
ok [전역 패턴 계약 부재] exit=2
ok [전역 패턴 계약 빈 파일] exit=2
ok [깨진 정규식] exit=2
ok [빈 문자열 매치 정규식] exit=2
ok [제품 패턴 계약 깨짐] exit=2
ok [제품 루트 부재 — 조용한 skip 금지] exit=2
ok [제품 파일 0건 — 0건 통과 금지] exit=2
ok [위반+깨진 패턴 동시 — 2 우선] exit=2
ok [제품 5파일 깨끗] exit=0
PASS: portal-constants mutations blocked 24/35 (allowed 3, notrun 8)
RC=0
```

→ 뭘 시켰나: 9bab751에서 고정된 원래 35건을 현재 본체에 실행했습니다.  
→ 뭐가 나왔나: 24건 거부, 3건 허용, 8건 검사 불능을 모두 기대 숫자로 판정해 전체 0이었습니다.  
→ 좋은 소식인가 나쁜 소식인가: 기존 정본이 살아 있다는 좋은 소식입니다.

```text
$ bash scripts/acceptance-hs-portal-constants-hardening.sh
ok [hardening baseline] exit=0
ok [D1 IPv4 비루프백 host:port] exit=1
ok [D1 미등재 .ai 도메인] exit=1
ok [D1 CSS 자손 셀렉터] exit=1
ok [D1 CSS 속성 셀렉터] exit=1
ok [D1 공백 XPath] exit=1
ok [D1 따옴표 CDP 포트] exit=1
ok [D1 매핑형 CDP 포트] exit=1
ok [D1 IPv6 루프백 host:port] exit=1
ok [D2 run 블록 선행 exit 0] exit=1
ok [D2 run 블록 실패 중단 해제] exit=1
ok [D3 검사기 머리말 표식] exit=1
ok [D3 mutation 시험 머리말 표식] exit=1
ok [D4 임시공간 생성 실패] exit=2
ok [D5 docs 실행 코드 은닉] exit=1
ok [D5 정당한 문서 인용 — 오탐 금지] exit=0
ok [D5 실행권한 달린 문서 위장] exit=1
ok [hardening 자기 배선(CI 실행 줄)]
PASS: portal-constants hardening blocked 15/18 (allowed 2, notrun 1)
RC=0
```

→ 뭘 시켰나: 37d2fa7에서 고정된 새 18건을 현재 본체에 실행했습니다.  
→ 뭐가 나왔나: 전체는 0이지만 실제 1은 14건이고 자기 배선 1건은 종료 숫자 없는 현재 상태 확인입니다.  
→ 좋은 소식인가 나쁜 소식인가: 다섯 기존 결함 재현에는 좋지만 “15개 차단” 해석에는 주의가 필요합니다.

## 3. 1차 반례 8종의 최종 패턴 직접 대조

```text
V1-1 IPv4 | global=NO | product=YES | overall=BLOCKED
V1-2 .ai | global=NO | product=YES | overall=BLOCKED
V1-3 CSS descendant | global=NO | product=YES | overall=BLOCKED
V1-4 CSS attribute | global=NO | product=YES | overall=BLOCKED
V1-5 XPath whitespace | global=YES | product=NO | overall=BLOCKED
V1-6 quoted port | global=NO | product=YES | overall=BLOCKED
V1-7 mapped port | global=NO | product=YES | overall=BLOCKED
V1-8 IPv6 | global=NO | product=YES | overall=BLOCKED
```

→ 뭘 시켰나: 1차의 정확한 8개 값을 전역·제품 패턴에 각각 직접 넣었습니다.  
→ 뭐가 나왔나: XPath는 전역 패턴, 나머지 7개는 제품 패턴에서 잡혔고 전체 8/8이 차단됐습니다.  
→ 좋은 소식인가 나쁜 소식인가: D1의 기존 8개에 한해서는 좋은 소식입니다.

고정 파일명 연출을 반증하기 위해 새 깊은 경로와 `.conf` 확장자를 사용한 독립 결과입니다.

```text
CASE: anti-theater: original .ai payload in new deep path and new extension (want 1)
  forbidden(product): humansearch/src/deep/randomized/value-482.conf
FAIL: portal constants outside contracts 1
PASS: contracts zone violations 0
PASS: ci/pre-push wiring intact
PRODUCT_FILES: 3
CHECKED: 51
CONTRACT_FILES: 3
RC=1
```

→ 뭘 시켰나: hardening에 없는 파일명·깊은 경로·확장자에 기존 `.ai` 값을 넣었습니다.  
→ 뭐가 나왔나: 제품 위반 1로 거부됐습니다.  
→ 좋은 소식인가 나쁜 소식인가: 구현이 고정 파일명만 겨냥하지 않았다는 좋은 소식입니다.

## 4. D2·D3·D4·D5 독립 복제 실행 전문

```text
CASE: D2 independent: run block exit 0 before scanner (want 1)
  wiring: CI 에 검사기 실행 줄이 없거나 무력화됨: bash scripts/acceptance-hs-portal-constants.sh
  wiring: CI 에 mutation 실행 줄이 없거나 무력화됨: bash scripts/acceptance-hs-portal-constants-mutations.sh
PASS: portal constants outside contracts 0
PASS: contracts zone violations 0
FAIL: ci/pre-push wiring broken 2
PRODUCT_FILES: 2
CHECKED: 50
CONTRACT_FILES: 3
RC=1

CASE: D2 independent: run block set +e before scanner (want 1)
  wiring: CI 에 검사기 실행 줄이 없거나 무력화됨: bash scripts/acceptance-hs-portal-constants.sh
  wiring: CI 에 mutation 실행 줄이 없거나 무력화됨: bash scripts/acceptance-hs-portal-constants-mutations.sh
PASS: portal constants outside contracts 0
PASS: contracts zone violations 0
FAIL: ci/pre-push wiring broken 2
PRODUCT_FILES: 2
CHECKED: 50
CONTRACT_FILES: 3
RC=1

CASE: D3 independent: marker in head-20 of acceptance-hs-portal-constants.sh (want 1)
  wiring: G3 검사 파일이 pre-push 건너뛰기 표식을 달고 있다: ./scripts/acceptance-hs-portal-constants.sh
PASS: portal constants outside contracts 0
PASS: contracts zone violations 0
FAIL: ci/pre-push wiring broken 1
PRODUCT_FILES: 2
CHECKED: 50
CONTRACT_FILES: 3
RC=1

CASE: D3 independent: marker in head-20 of acceptance-hs-portal-constants-mutations.sh (want 1)
  wiring: G3 검사 파일이 pre-push 건너뛰기 표식을 달고 있다: ./scripts/acceptance-hs-portal-constants-mutations.sh
PASS: portal constants outside contracts 0
PASS: contracts zone violations 0
FAIL: ci/pre-push wiring broken 1
PRODUCT_FILES: 2
CHECKED: 50
CONTRACT_FILES: 3
RC=1

CASE: D3 independent: marker in head-20 of acceptance-hs-portal-constants-hardening.sh (want 1)
  wiring: G3 검사 파일이 pre-push 건너뛰기 표식을 달고 있다: ./scripts/acceptance-hs-portal-constants-hardening.sh
PASS: portal constants outside contracts 0
PASS: contracts zone violations 0
FAIL: ci/pre-push wiring broken 1
PRODUCT_FILES: 2
CHECKED: 50
CONTRACT_FILES: 3
RC=1

CASE: D4 independent: mktemp unavailable (want 2 + message)
FAIL: temp workspace unavailable
RC=2

CASE: D5 independent: non-document .py under docs (want 1)
  forbidden(global): docs/random-runner-271.py
FAIL: portal constants outside contracts 1
PASS: contracts zone violations 0
PASS: ci/pre-push wiring intact
PRODUCT_FILES: 2
CHECKED: 51
CONTRACT_FILES: 3
RC=1

CASE: D5 independent: executable document extension under docs (want 1)
  forbidden(global): docs/random-operator-314.HTML
FAIL: portal constants outside contracts 1
PASS: contracts zone violations 0
PASS: ci/pre-push wiring intact
PRODUCT_FILES: 2
CHECKED: 51
CONTRACT_FILES: 3
RC=1

CASE: D5 independent: non-executable document under docs (want 0)
PASS: portal constants outside contracts 0
PASS: contracts zone violations 0
PASS: ci/pre-push wiring intact
PRODUCT_FILES: 2
CHECKED: 50
CONTRACT_FILES: 3
RC=0

SOURCE_WORKTREE_STATUS=CLEAN
```

→ 뭘 시켰나: 구현자의 18건 함수를 재사용하지 않고 현재 저장소를 새로 복제해 D2·D3·D4·D5를 심었습니다.  
→ 뭐가 나왔나: 금지 사례는 정확히 1, 검사 불능은 2, 허용 문서는 0이며 원본은 깨끗했습니다.  
→ 좋은 소식인가 나쁜 소식인가: 기존 네 결함의 봉쇄에는 좋은 소식입니다.

## 5. 새 직접 표현 10종 — 전체 검사기 실행 전문

아래 값은 모두 추적된 `humansearch/src/` 또는 `humansearch/tests/` 안의 한 파일에 한 줄로 직접 적었습니다. 조각 조립·이스케이프·빌드 산출물은 없습니다.

```text
NEW_PAYLOAD: N1 unlisted common TLD
PATH: humansearch/src/deep/net/value-771.py
PAYLOAD: PORTAL = "jobs.vendor.biz"
PASS: portal constants outside contracts 0
PASS: contracts zone violations 0
PASS: ci/pre-push wiring intact
PRODUCT_FILES: 3
CHECKED: 51
CONTRACT_FILES: 3
RC=0

NEW_PAYLOAD: N2 single-label hostname with port
PATH: humansearch/tests/deep/net/value-772.cfg
PAYLOAD: REMOTE = "portal:9444"
PASS: portal constants outside contracts 0
PASS: contracts zone violations 0
PASS: ci/pre-push wiring intact
PRODUCT_FILES: 3
CHECKED: 51
CONTRACT_FILES: 3
RC=0

NEW_PAYLOAD: N3 valid one-digit port
PATH: humansearch/src/deep/net/value-773.toml
PAYLOAD: REMOTE = "10.77.4.9:8"
PASS: portal constants outside contracts 0
PASS: contracts zone violations 0
PASS: ci/pre-push wiring intact
PRODUCT_FILES: 3
CHECKED: 51
CONTRACT_FILES: 3
RC=0

NEW_PAYLOAD: N4 JSON quoted port key
PATH: humansearch/tests/deep/net/value-774.json
PAYLOAD: {"port": 9333}
PASS: portal constants outside contracts 0
PASS: contracts zone violations 0
PASS: ci/pre-push wiring intact
PRODUCT_FILES: 3
CHECKED: 51
CONTRACT_FILES: 3
RC=0

NEW_PAYLOAD: N5 camelCase port variable
PATH: humansearch/src/deep/net/value-775.js
PAYLOAD: cdpPort = 9333
PASS: portal constants outside contracts 0
PASS: contracts zone violations 0
PASS: ci/pre-push wiring intact
PRODUCT_FILES: 3
CHECKED: 51
CONTRACT_FILES: 3
RC=0

NEW_PAYLOAD: N6 CSS attribute with quoted value
PATH: humansearch/tests/deep/ui/value-776.js
PAYLOAD: LOGIN = '[data-testid="sign-in"]'
PASS: portal constants outside contracts 0
PASS: contracts zone violations 0
PASS: ci/pre-push wiring intact
PRODUCT_FILES: 3
CHECKED: 51
CONTRACT_FILES: 3
RC=0

NEW_PAYLOAD: N7 CSS id followed by descendant
PATH: humansearch/src/deep/ui/value-777.py
PAYLOAD: LOGIN = "#login input"
PASS: portal constants outside contracts 0
PASS: contracts zone violations 0
PASS: ci/pre-push wiring intact
PRODUCT_FILES: 3
CHECKED: 51
CONTRACT_FILES: 3
RC=0

NEW_PAYLOAD: N8 CSS JavaScript template literal
PATH: humansearch/src/deep/ui/value-778.js
PAYLOAD: LOGIN = `#login`
PASS: portal constants outside contracts 0
PASS: contracts zone violations 0
PASS: ci/pre-push wiring intact
PRODUCT_FILES: 3
CHECKED: 51
CONTRACT_FILES: 3
RC=0

NEW_PAYLOAD: N9 absolute XPath
PATH: humansearch/tests/deep/ui/value-779.py
PAYLOAD: LOGIN = "/html/body/input"
PASS: portal constants outside contracts 0
PASS: contracts zone violations 0
PASS: ci/pre-push wiring intact
PRODUCT_FILES: 3
CHECKED: 51
CONTRACT_FILES: 3
RC=0

NEW_PAYLOAD: N10 XPath functional predicate
PATH: humansearch/src/deep/ui/value-780.py
PAYLOAD: LOGIN = '//input[contains(@name, "email")]'
PASS: portal constants outside contracts 0
PASS: contracts zone violations 0
PASS: ci/pre-push wiring intact
PRODUCT_FILES: 3
CHECKED: 51
CONTRACT_FILES: 3
RC=0

SOURCE_WORKTREE_STATUS=CLEAN
```

→ 뭘 시켰나: 1차와 겹치지 않는 주소·포트·CSS·XPath 직접 표기 10종을 각각 새 복제본에 심고 본체를 실행했습니다.  
→ 뭐가 나왔나: 10개 모두 위반 0, 전체 0으로 정상 승인됐습니다.  
→ 좋은 소식인가 나쁜 소식인가: 계약 범위 안의 새로운 우회가 실제로 남았으므로 나쁜 소식입니다.

반증 기록: “새 규칙이 표현 가족 전체를 막았을 것”을 `.biz`, 한 단어 호스트, JSON 키, 중첩 따옴표, 역따옴표, 절대·함수형 XPath로 반증 시도했고 10건 모두 반증에 성공했습니다.

## 6. 새 서버 우회 — 셸 조건문 안에 세 줄 넣기

워크플로(workflow, 서버 자동검사에서 어떤 명령을 어떤 순서로 실행할지 적는 파일)를 다음처럼 바꿨습니다.

```text
48      - name: HumanSearch G3 포털 상수·locator 경계
52        run: |
53          if false; then
54          bash scripts/acceptance-hs-portal-constants.sh
55          bash scripts/acceptance-hs-portal-constants-mutations.sh
56          bash scripts/acceptance-hs-portal-constants-hardening.sh
57          fi
```

→ 뭘 시켰나: 정확한 세 실행 줄은 남기고, 셸이 실행하지 않는 조건 안에 넣었습니다.  
→ 뭐가 나왔나: 현재 문자열 검사는 세 줄을 그대로 정상 배선으로 인정했습니다.  
→ 좋은 소식인가 나쁜 소식인가: 명령 존재와 실행이 다르므로 나쁜 소식입니다.

```text
LOCAL_SCANNER_ON_MUTATED_WORKFLOW:
PASS: portal constants outside contracts 0
PASS: contracts zone violations 0
PASS: ci/pre-push wiring intact
PRODUCT_FILES: 2
CHECKED: 50
CONTRACT_FILES: 3
RC=0

LOCAL_MUTATIONS_ON_MUTATED_WORKFLOW:
PASS: portal-constants mutations blocked 24/35 (allowed 3, notrun 8)
RC=0

LOCAL_HARDENING_ON_MUTATED_WORKFLOW:
PASS: portal-constants hardening blocked 15/18 (allowed 2, notrun 1)
RC=0

CI_RUN_BLOCK_SIMULATION: RC=0 OUTPUT_BYTES=0
SOURCE_WORKTREE_STATUS=CLEAN
```

→ 뭘 시켰나: 변형된 서버 설정을 보면서 G3 세 파일을 로컬에서 각각 실행한 뒤, 조건문을 Bash의 실패 즉시 중단 모드로 그대로 실행했습니다.  
→ 뭐가 나왔나: 세 자기검사는 모두 0이었고 실제 서버 묶음 모의 실행은 출력 없이 0이었습니다.  
→ 좋은 소식인가 나쁜 소식인가: G3 전체를 한 번도 실행하지 않고 승인할 수 있으므로 치명적으로 나쁜 소식입니다.

반증 기록: “정확한 실행 줄 + 선행 `exit 0`·`set +e` 차단이면 서버 실행이 보장된다”를 셸 조건문으로 반증 시도했고 성공했습니다.

## 7. 보강 시험 자기 배선의 순환 결함

```text
MUTATED_WORKFLOW_WITH_HARDENING_LINE_REMOVED:
52        run: |
53          bash scripts/acceptance-hs-portal-constants.sh
54          bash scripts/acceptance-hs-portal-constants-mutations.sh

SCANNER_RESULT:
PASS: portal constants outside contracts 0
PASS: contracts zone violations 0
PASS: ci/pre-push wiring intact
PRODUCT_FILES: 2
CHECKED: 50
CONTRACT_FILES: 3
RC=0

MUTATION_RESULT_LAST_LINE:
PASS: portal-constants mutations blocked 24/35 (allowed 3, notrun 8)
RC=0

HARDENING_IF_MANUALLY_RUN:
ok [hardening baseline] exit=0
ok [D1 IPv4 비루프백 host:port] exit=1
ok [D1 미등재 .ai 도메인] exit=1
ok [D1 CSS 자손 셀렉터] exit=1
ok [D1 CSS 속성 셀렉터] exit=1
ok [D1 공백 XPath] exit=1
ok [D1 따옴표 CDP 포트] exit=1
ok [D1 매핑형 CDP 포트] exit=1
ok [D1 IPv6 루프백 host:port] exit=1
ok [D2 run 블록 선행 exit 0] exit=1
ok [D2 run 블록 실패 중단 해제] exit=1
ok [D3 검사기 머리말 표식] exit=1
ok [D3 mutation 시험 머리말 표식] exit=1
ok [D4 임시공간 생성 실패] exit=2
ok [D5 docs 실행 코드 은닉] exit=1
ok [D5 정당한 문서 인용 — 오탐 금지] exit=0
ok [D5 실행권한 달린 문서 위장] exit=1
FAIL: hardening 자신이 CI(.github/workflows/verify.yml) 실행 줄에 없다 — 로컬에만 있는 검사는 없는 것으로 친다 (P15③)
RC=1

SIMULATED_CI_G3_STEP_AFTER_REMOVAL_RC=0
SOURCE_WORKTREE_STATUS=CLEAN
```

→ 뭘 시켰나: 서버 설정에서 hardening 한 줄만 지우고 남은 두 실제 명령과, 삭제된 hardening을 수동으로 각각 실행했습니다.  
→ 뭐가 나왔나: 서버에 남는 두 명령은 모두 0이고, 서버에서 사라진 hardening만 수동 실행할 때 1이었습니다.  
→ 좋은 소식인가 나쁜 소식인가: 자기 자신이 실행돼야만 자기 삭제를 알 수 있어 서버 독립 방어가 아니므로 나쁜 소식입니다.

반증 기록: “hardening의 자기 배선 검사가 자기 삭제를 막는다”를 실제 한 줄 삭제로 반증 시도했고 성공했습니다.

## 8. 로컬 훅 선행 종료와 저장소 전체 백업

```text
MUTATED_PRE_PUSH_HEAD:
1 #!/usr/bin/env bash
2 exit 0
3 # pre-push — push 시점 로컬 강제 장치 (P15)

SCANNER_RESULT:
PASS: portal constants outside contracts 0
PASS: contracts zone violations 0
PASS: ci/pre-push wiring intact
PRODUCT_FILES: 2
CHECKED: 50
CONTRACT_FILES: 3
RC=0

MUTATION_RESULT_LAST_LINE:
PASS: portal-constants mutations blocked 24/35 (allowed 3, notrun 8)
RC=0

HARDENING_RESULT_LAST_LINE:
PASS: portal-constants hardening blocked 15/18 (allowed 2, notrun 1)
RC=0

ACTUAL_PRE_PUSH_RESULT: RC=0 OUTPUT_BYTES=0
SOURCE_WORKTREE_STATUS=CLEAN
```

→ 뭘 시켰나: 로컬 업로드 직전 훅의 두 번째 줄에서 정상 종료하게 만들고 G3 세 검사와 훅 자체를 실행했습니다.  
→ 뭐가 나왔나: G3는 배선 정상으로 보고했고 세 시험과 실제 훅이 모두 0, 실제 훅 출력은 0바이트였습니다.  
→ 좋은 소식인가 나쁜 소식인가: G3 자체의 로컬 배선 증명에는 나쁜 소식입니다.

저장소 전체의 별도 `acceptance-0-7.sh`를 같은 변형에 실행한 결과입니다.

```text
CROSS_GATE_ACCEPTANCE_0_7_ON_EARLY_EXIT_HOOK:
[1/6] 검사기 자기 제외 → BLOCKED
[2/6] 검사 약화(실패 무시) → BLOCKED
[3/6] 만료일 없는 억제 → BLOCKED
[4/6] LLM 출력→판정 필드 → BLOCKED
[5/6] 미커밋 상태로 push → PASSED ← 결함, 차단되지 않음 (훅ON=0 · 훅OFF=0)
[6/6] 가짜 외부효과 모듈 → BLOCKED
RESULT: 차단되지 않았거나 시연이 무효인 항목이 있다. exit 1
RC=1
```

→ 뭘 시켰나: G3 밖의 기존 훅 검증 장치가 조기 종료 훅을 잡는지 확인했습니다.  
→ 뭐가 나왔나: 5번째 시연이 통과해 전체 1로 거부했습니다.  
→ 좋은 소식인가 나쁜 소식인가: G3의 구멍은 남지만 현재 저장소 전체 서버 검사에는 백업이 있어 제한적인 좋은 소식입니다.

## 9. hardening 시험의 연출·숫자·종료값 감사

`scripts/acceptance-hs-portal-constants-hardening.sh:109-126`은 기대 숫자와 실제 숫자를 정확히 비교하는 줄입니다.

```text
109 expect_case() {
110   local label="$1" want="$2" needle="$3"
111   run_scanner
112   if [ "$SCAN_RC" -ne "$want" ]; then
113     echo "FAIL: hardening [$label] exit=$SCAN_RC (기대: 정확히 $want)"
114     printf '%s\n' "$SCAN_OUT"
115     exit 1
116   fi
117   if [ -n "$needle" ] && ! printf '%s\n' "$SCAN_OUT" | grep -qE "$needle"; then
118     echo "FAIL: hardening [$label] 이유가 다르다 (exit=$SCAN_RC)"
119     printf '%s\n' "$SCAN_OUT"
120     exit 1
121   fi
122   case "$want" in
123     0) allowed=$((allowed + 1)) ;;
124     1) blocked=$((blocked + 1)) ;;
125     2) notrun=$((notrun + 1)) ;;
126   esac
```

→ 뭘 확인했나: 2나 127을 1처럼 세는지 소스에서 확인했습니다.  
→ 뭐가 나왔나: 기대 숫자와 정확히 같아야 하고, 이유 문장도 맞아야 합니다.  
→ 좋은 소식인가 나쁜 소식인가: 종료 숫자 혼동은 발견하지 못했으므로 좋은 소식입니다.

```text
INDEPENDENT_OUTPUT_COUNTS ok_total=18 exit0=2 exit1=14 exit2=1 self_wire_without_exit=1
79:  total=$((total + 1))
238:total=$((total + 1))
INIT_CASE_INVOCATIONS=17
EXTRA_TOTAL_INCREMENTS_AFTER_CASE_DEFINITIONS=1
COMPUTED_TOTAL=18
```

→ 뭘 시켰나: 실행 출력의 종류를 독립 집계하고, 소스의 사례 함수 호출과 별도 증가를 다시 셌습니다.  
→ 뭐가 나왔나: 전체 18은 정확하지만 실제 1은 14이며, 자기 배선 현재 상태 확인이 15번째 blocked로 분류됩니다.  
→ 좋은 소식인가 나쁜 소식인가: 총수는 정직하지만 “15개 차단”은 실제 음성 공격 15개가 아니므로 나쁜 소식입니다.

고정 파일명 겨냥은 발견하지 못했습니다. hardening의 여러 사례는 고정 이름을 사용하지만 본체는 모든 추적 제품 파일을 열거하며, 새 깊은 경로와 `.conf`의 기존 `.ai` 값도 1로 막았습니다. 반대로 이번 새 미탐은 이름을 바꿔서가 아니라 표현 규칙 자체가 좁아서 생겼습니다.

hardening은 D3에서 본체와 원 mutation 두 파일만 직접 변형하고 자기 자신은 변형하지 않습니다. 그러나 본체의 와일드카드 경로가 세 번째 파일도 잡는지는 별도 복제 실행으로 확인했으므로 구현 결함으로 세지 않고 시험 범위 공백으로만 기록합니다.

## 10. RED 불변과 실제 RED 실행

RED(수정 전 시험이 올바른 이유로 실패하는 상태)와 GREEN(구현 뒤 같은 시험이 통과하는 상태)을 과거 커밋에서 다시 실행했습니다.

```text
RED1_AT_9bab751:
FAIL: required G3 implementation missing: scripts/acceptance-hs-portal-constants.sh
RC=1

RED2_AT_37d2fa7:
ok [hardening baseline] exit=0
FAIL: hardening [D1 IPv4 비루프백 host:port] exit=0 (기대: 정확히 1)
PASS: portal constants outside contracts 0
PASS: contracts zone violations 0
PASS: ci/pre-push wiring intact
PRODUCT_FILES: 3
CHECKED: 15
CONTRACT_FILES: 2
RC=1

ANCESTOR 9bab751 -> HEAD: YES
ANCESTOR 37d2fa7 -> HEAD: YES
ANCESTOR dfccaa7 -> HEAD: YES
```

→ 뭘 시켰나: 두 RED 시점의 정확한 커밋을 별도 복제해 당시 시험을 실행하고 현재 HEAD의 조상인지 확인했습니다.  
→ 뭐가 나왔나: RED1은 구현 부재, RED2는 첫 IPv4 미탐이라는 올바른 이유로 각각 1이었습니다.  
→ 좋은 소식인가 나쁜 소식인가: RED 순서는 실제였으므로 좋은 소식입니다.

Git 객체 ID와 SHA-256(파일 내용이 같으면 같은 값이 나오는 지문) 대조 전문입니다.

```text
FROZEN_FILE=scripts/acceptance-hs-portal-constants-mutations.sh
BASE=9bab751
BASE_BLOB=0cf07fa078a8856255369b3fff255f8c31334d18
HEAD_BLOB=0cf07fa078a8856255369b3fff255f8c31334d18
BASE_SHA256=84b6bad0465a208513a81f6abbd0a2ae65e05ae16839f5855ec1e0fab0905210
HEAD_SHA256=84b6bad0465a208513a81f6abbd0a2ae65e05ae16839f5855ec1e0fab0905210
DIFF_RC=0
DIFF_OUTPUT=<empty>
LATER_TOUCH_COMMITS=<none>

FROZEN_FILE=scripts/acceptance-hs-portal-constants-hardening.sh
BASE=37d2fa7
BASE_BLOB=bb5e3ee7378418b6f1ded80678eb0b0bd488e726
HEAD_BLOB=bb5e3ee7378418b6f1ded80678eb0b0bd488e726
BASE_SHA256=5e05339f7e23f19ceabc9c113713e34831fef9c44ba0a5c4eba416d6e06da57f
HEAD_SHA256=5e05339f7e23f19ceabc9c113713e34831fef9c44ba0a5c4eba416d6e06da57f
DIFF_RC=0
DIFF_OUTPUT=<empty>
LATER_TOUCH_COMMITS=<none>
```

→ 뭘 시켰나: 각 정본 생성 커밋과 현재 HEAD의 파일 내용·차이·후속 접촉 이력을 비교했습니다.  
→ 뭐가 나왔나: 두 파일 모두 객체와 지문이 같고 차이와 후속 접촉이 없습니다.  
→ 좋은 소식인가 나쁜 소식인가: RED 불변 주장은 사실이므로 좋은 소식입니다.

## 11. 문서와 구현 불일치

SOT(single source of truth, 팀이 최종 기준으로 삼는 문서)인 `docs/sot/verification-commands.md:27`은 G3 단계에 hardening까지 포함한다고 적습니다.

```text
27 | 4 | HumanSearch G3 포털 상수·locator 경계 | 인라인 — `acceptance-hs-portal-constants.sh` + `-mutations` + `-hardening` (운영 상수·locator 는 contracts/ 한 곳 · P22, exit 0/1/2 3상태, hardening 은 V1 적대검증 결함 5종 봉쇄 증명) |
44 **CI는 고정 목록이고 로컬 `pre-push`는 글로브(이름 규칙 자동 수집)다.** ... **새 `scripts/acceptance-*.sh`를 추가하는 PR은 `verify.yml`과 이 표 양쪽에 자기 줄을 함께 넣어야 한다.**
```

→ 뭘 확인했나: hardening의 서버 등록이 필수인지 정본 문서에서 읽었습니다.  
→ 뭐가 나왔나: hardening 포함과 새 스크립트의 서버 줄 필수가 명시돼 있습니다.  
→ 좋은 소식인가 나쁜 소식인가: 본체가 그 줄 삭제를 거부하지 않으므로 나쁜 소식입니다.

반면 goal과 패턴 주석은 D5 이전 설명을 유지합니다.

```text
docs/engineering/humansearch-g3-portal-constants-goal-2026-08-12.md:93-95
93 - `docs/` 정확 접두 경로는 문서이므로 금지 패턴을 적용하지 않는다
95   단 CHECKED에 세지 않고 별도 보고하지도 않는다

contracts/portal-constants-deny-patterns.txt:2
2 # 적용: docs/·contracts/ 를 뺀 모든 추적 파일 (검사기 자신·scripts/·hooks/ 포함, 자기면제 없음).
```

→ 뭘 확인했나: D5 수정 뒤 계약과 패턴 주석도 같이 바뀌었는지 읽었습니다.  
→ 뭐가 나왔나: 본체는 조건부 면제인데 두 설명은 문서 전체 면제라고 남아 있습니다.  
→ 좋은 소식인가 나쁜 소식인가: 현재 실행은 고쳤지만 다음 유지보수 기준이 갈라져 나쁜 소식입니다.

## 12. 수용 한계와 이번 결함의 경계

결함으로 세지 않은 항목은 다음과 같습니다.

- `scripts/` 등 제품 루트 밖의 원시 CSS·일반 URL: 문서화된 한계입니다.
- `humansearch/pyproject.toml`·`humansearch/uv.lock` 같은 직속 비코드 설정: 문서화된 한계입니다.
- 문자열 조각 조립, `\xNN` 같은 문자 숨김, 여러 조각의 런타임 결합: 사용자가 명시한 비범위입니다.
- 컴파일·생성 뒤에만 나타나는 값: 사용자가 명시한 빌드 산출물 비범위입니다.
- 실행 권한 없는 허용 문서 확장자의 포털 사례 인용: 이번 D5 설계상 허용입니다.

이번 결함으로 센 10개 값은 모두 제품 루트 안의 추적 파일에 한 줄짜리 직접 문자열 또는 직접 숫자로 적었습니다. JavaScript 역따옴표는 조각 조립이나 문자 숨김이 아니라 언어의 직접 문자열 표기이므로 비범위로 돌리지 않았습니다.

## 13. 최종 반증 의무 기록

- X: “1차 8개가 여전히 샌다”를 Y: 두 최종 패턴 직접 대조와 깊은 새 경로 전체 실행으로 반증 시도했으나 실패했습니다. 8개는 모두 막혔습니다.
- X: “D2의 `exit 0`·`set +e`가 여전히 샌다”를 Y: 독립 복제 워크플로 주입으로 반증 시도했으나 실패했습니다. 둘 다 1입니다.
- X: “D3 세 번째 hardening 파일은 머리말로 빠진다”를 Y: 세 파일 각각 머리말 주입으로 반증 시도했으나 실패했습니다. 모두 1입니다.
- X: “D4가 여전히 1을 낸다”를 Y: PATH 앞에 실패하는 `mktemp`를 넣어 반증 시도했으나 실패했습니다. 정확히 2입니다.
- X: “D5가 여전히 docs 전체를 건너뛴다”를 Y: 새 `.py`, 실행 가능한 대문자 `.HTML`, 비실행 대문자 `.MD`로 반증 시도했으나 실패했습니다. 결과는 1·1·0입니다.
- X: “새 패턴이 같은 범주의 흔한 직접 표현까지 봉쇄한다”를 Y: 10개 새 값으로 반증 시도했고 성공했습니다. 전부 0입니다.
- X: “서버의 정확한 세 줄 검사가 실제 실행을 증명한다”를 Y: 셸 조건문으로 반증 시도했고 성공했습니다. 자체 점검 3개와 실제 묶음이 모두 0입니다.
- X: “hardening 자기 배선이 자기 삭제를 막는다”를 Y: 서버 줄 삭제로 반증 시도했고 성공했습니다. 서버에 남는 명령은 모두 0입니다.
- X: “G3가 로컬 훅의 조기 종료를 감지한다”를 Y: 훅 2행 `exit 0`으로 반증 시도했고 성공했습니다. 단 저장소 전체 별도 시험은 1로 백업 차단합니다.
- X: “GREEN이 RED 시험을 고쳤다”를 Y: 객체 ID·SHA-256·diff·후속 이력으로 반증 시도했으나 실패했습니다. 두 정본은 불변입니다.
- X: “18과 15는 모두 실제 고장 주입 수다”를 Y: 출력 종류와 소스 호출 수로 반증 시도했습니다. 18은 맞지만 실제 1은 14이고 자기 줄 현재 상태 확인 1개가 blocked에 포함됩니다.

## 14. 명령·출력 장부와 최종 상태

실행 명령은 병렬로 보낸 독립 명령도 각각 한 개로 세고, 계획 갱신·파일 패치·대기 호출은 세지 않았습니다. 명령 전달기 문법 오류로 셸이 시작되지 않은 두 건도 세지 않았고, 셸이 실제 시작된 뒤 실패한 탐색·따옴표 명령은 셌습니다.

주요 명령 전문은 위 각 절에 출력과 함께 붙였습니다. 나머지 조사 명령은 다음과 같습니다.

```text
1  pwd + codeaudit SKILL.md 전체 읽기 + AGENTS.md 검색
2  omx explore 경로 탐색 → cargo 부재로 실패
3  git status/rev-parse/log
4  rg --files 대상 파일 열거
5  goal 적대검증·계약 검색
6  본체 전체 줄번호 열람
7  hardening 전체 줄번호 열람
8  패턴 두 벌 줄번호 열람
9~19 goal·본체·mutation·workflow·hook·두 커밋을 구간별 열람
20 본체 실행
21 원 mutation 35건 실행
22 hardening 18건 실행
23 1차 8종 패턴 직접 대조
24 현재 workflow G3 줄 열람
25 pre-push 전체와 관련 표식 검색
26 새 표현 10종 1차 패턴 대조
27 잘못 전달된 \x27·\x60 대조 — 결함 근거 제외
28 따옴표 전달 명령이 zsh 확장 오류로 실패 — 재시도
29 실제 따옴표·역따옴표 3종 대조
30 독립 D2/D3/D4/D5 복제 실행
31 새 표현 앞 5종 전체 검사 실행
32 새 표현 뒤 5종 재실행
33 셸 조건문 서버 우회 실행
34 hardening 서버 줄 삭제 실행
35 pre-push 선행 종료 실행
36 hardening 출력 독립 집계
37 잘못된 19 계산을 18로 재계산
38 RED 정본 Git 객체·SHA-256 비교
39 RED1·RED2 과거 커밋 실행
40 계약·SOT·구현 교차 검색
41 최종 git 상태·diff 검사·HEAD 확인
42 G3 세 셸 파일 bash -n
43 SOT·goal·패턴 주석 정확 줄 열람
44 pre-push 조기 종료를 acceptance-0-7로 교차 실행
45 약화 패턴·다른 보호 장치 저장소 전역 검색
46 판정 파일 상위 디렉터리 생성·확인
47 판정 임시 파일을 지정 경로로 복사
48 strict brief-lint 1차 형식 검사
49 형식 검사 출력을 덧붙이기 위해 판정 파일을 임시 작업 파일로 복사
50 갱신한 판정 파일을 지정 경로로 다시 복사
51 strict brief-lint 2차 형식 검사
52 판정 파일 첫 줄·마지막 줄·형식 숫자·저장소 청결 최종 확인
```

→ 뭘 정리했나: 실제 셸이 시작된 명령 52개의 목적을 빠짐없이 적었습니다.  
→ 뭐가 나왔나: 핵심 실행 출력은 위에 전문으로 보존했고, 조사·열람 명령은 이 장부에 목적을 남겼습니다.  
→ 좋은 소식인가 나쁜 소식인가: 재현 가능성과 누락 확인에는 좋은 소식입니다.

브리핑 형식 검사 1차 출력 전문입니다. 이 숫자는 문서 형식만 증명하며 G3 합격 근거가 아닙니다.

```text
코드블록 25개 (예시 제외 0개) / 해석 누락 0개 · 부실 0개
표 해석: 이상 없음
1층(결론): 줄 3 / 본문 360자
1층 전문용어: 0개
결정 카드 3건 완비 / 불완전 0건
증거 보관 경로: 이상 없음 (실재 확인 2건)
브리핑 계약 기계 검사: 위반 0건 (문서 1개)
※ 형식만 센다. 설명이 이해되는지·위험의 무게가 보존됐는지는 사람이 본다.
※ 이 검사는 홈 폴더에만 있어 서버 자동 검사에 없다 — 회사 차원의 합격 근거가 아니다.
```

→ 뭘 시켰나: strict 브리핑 계약 검사기로 판정서의 세 층 구조, 용어, 코드 출력 해설, 설계 카드, 보관 경로를 셌습니다.  
→ 뭐가 나왔나: 위반 0건이었습니다.  
→ 좋은 소식인가 나쁜 소식인가: 형식에는 좋은 소식이지만 구현 품질 판정과는 무관합니다.

최종 정적 상태는 다음과 같습니다.

```text
git status --short --branch
## task/humansearch-g3-portal-constants

git rev-parse HEAD
fb512e11ab1ff725d9992aead782c0a3b787ac6a

git diff --check
<출력 없음, exit 0>

bash -n scripts/acceptance-hs-portal-constants.sh scripts/acceptance-hs-portal-constants-mutations.sh scripts/acceptance-hs-portal-constants-hardening.sh
BASH_N_RC=0
```

→ 뭘 시켰나: 감사 뒤 원본 변경 여부, 현재 커밋, 공백 오류, 세 셸 파일 문법을 확인했습니다.  
→ 뭐가 나왔나: 원본은 깨끗하고 HEAD는 지정값이며 차이 오류와 셸 문법 오류가 없습니다.  
→ 좋은 소식인가 나쁜 소식인가: 감사가 원본을 오염시키지 않았다는 좋은 소식입니다.

## 최종 조치 우선순위

1. 서버 G3 단계 안의 셸 제어문을 허용하지 말고, 세 명령의 실제 실행 증거를 독립 확인하셔야 합니다. 이 항목이 고쳐지기 전에는 병합 승인 금지입니다.
2. hardening 줄을 본체 또는 별도 독립 장치가 요구하게 하고, “줄 삭제 → 서버 단계 1” 음성 시험을 RED3로 먼저 고정하셔야 합니다.
3. 이번 10개 직접 표현을 새 RED3에 각각 넣고, 유한 TLD 열거·포트 키·CSS·XPath 문법을 범주 단위로 다시 설계하셔야 합니다.
4. G3가 `hooks/pre-push`의 선행 종료와 실제 G3 실행 목록을 확인하게 하되, 현재 `acceptance-0-7` 백업도 유지하셔야 합니다.
5. goal 93-95행과 전역 패턴 주석 2행을 현재 문서 면제 구현과 일치시키셔야 합니다.

COMMANDS_RUN: 52

---8<--- codex verdict 2차 원문 끝 ---8<---

### V1 3차 — codex (2026-08-12, VERDICT: FAIL — 2차 조치 후 상태 fb512e1 재판정)

- 검증자 신분: 실제 codex CLI 세션 `019ff4c3-66ad-7770-aa3b-ccad42b201c4`, companion job `task-mspqlrt5-yala6g`, 실행 명령 264개, 소요 38분.
- 원문 보관: `.claude/private-reviews/codex-g3-verdict3-2026-08-12.md` (SHA-256 `b8707591bbda286c2ef98a7eaed66f582d8a145fd5ea6db0b5369cf144ffd35f`) + 아래 전문 100%.
- 판정 요지: 2차 조치 5개(N1~N5·N7)의 이행은 전부 "구현 확인". 단 **신규 FAIL — F1 CI 스텝의 env
  값 문자열 안에 가짜 G3 단계를 넣으면 실행 0회인데 배선 통과(치명) · F2 의미 기반 화면 찾기 API
  4종(get_by_role/label/test_id/text)+element[attr] CSS 미탐(높음) · F3 검사기 :13 주석이 D5 이전
  통 면제 설명 잔존(중간)**.

### 조치 — 4차 RED→GREEN (RED4 `09c19b4` · GREEN4 `30270fd`)

- RED4 (`scripts/acceptance-hs-portal-constants-hardening3.sh`, 8케이스): codex F1 env 우회 원문 재현 +
  F2 payload 5종(get-by-* 4 + element[attr]). 커밋 직전 실측:
  `FAIL: hardening3 [F1 env 값 속 가짜 G3 단계] exit=0 (기대: 정확히 1)` → exit 1 (올바른 이유의 RED).
  ※ RED4 는 자기 매칭을 피하려 라벨·주석에서 API 이름을 조각으로만 적는다(표현만 조정, 단언 불변).
- GREEN4 (`30270fd`):
  · F1(치명) — 배선 검사를 **들여쓰기 기반 run 블록 파싱**으로 교체. `run: |` 리터럴 블록만 실행
    칸으로 인정하고, `env:` 서브트리(값 문자열)는 통째 배제한다. env 값 속 가짜 단계·셸 감싸기가
    모두 배선 훼손(exit 1)으로 잡힌다. 스텝 레벨 `if:`/`continue-on-error` 도 스텝 단위로 추적해
    조건부 실행을 훼손으로 본다(동결 mutations if_false 회귀 방어).
  · F2(높음) — 전역 계층에 get_by_* 계열(role·label·test_id·text·placeholder·title·alt_text) 추가,
    제품 계층에 element[attr] CSS 추가.
  · F3(중간) — 검사기 :13 주석을 조건부 docs 면제로 일치.

```text
GREEN4 재검증 (2026-08-12 16:46~16:58 KST):
  hardening3: cases 8 (blocked-mutations 6, clean-baselines 1, wiring-present 1) exit=0
  동결 회귀: mutations 24/35 · hardening 15/18 · hardening2 16 · 전부 exit=0 · RED 파일 4벌 diff 0줄
  실저장소 검사기 exit=0 (PRODUCT_FILES 2 · CHECKED 52 · CONTRACT_FILES 3)
  env 우회·셸 감싸기 → wiring broken exit 1 (V2 재현)
  G1 8·G2 3·AC-S1·AC-M·0-2/0-5/0-6/a3/a4·verify.sh·bash -n 31개 전부 exit=0
  (0-2 는 RED4 재커밋 고아객체로 1회 FAIL → git gc 후 PASS)
  pre-push 실호출: 검사 22개 전부 ok · session-status → RED: 0/24
```
→ 뭘 했나: 3차 신규 결함 3건을 시험으로 고정·봉쇄한 뒤 검증 전량을 다시 돌렸습니다.
→ 결과: 전부 통과. 분모 24는 G3 검사 파일 5개(본체+시험 4벌) 추가분입니다.
→ 의미: env 값 은닉·셸 감싸기 같은 구체 우회는 닫혔습니다.

### 남는 근본 한계 (수용 근거 — 결정 카드로 사장님 판단 대상)

**무엇을** — 배선 검사는 워크플로를 텍스트로 읽어 "정확한 실행 줄이 실제 run 블록에 있는가"를 본다.
**왜** — 이 저장소엔 YAML 구조 파서도, 새 의존성을 넣을 계약 허용도 없다(절대 경계). BSD awk 로 하는
들여쓰기 파싱은 알려진 구체 우회(env 값 은닉·셸 감싸기·조건 키)를 닫는다.
**버린 대안** — 완전한 YAML 파서 도입(의존성 금지 위반) · "실제 CI 실행 영수증"을 남기는 러너 재설계
(G3 범위 밖의 인프라 작업).
**대가** — codex 3차가 지적한 근본("텍스트로는 CI 실제 실행을 증명 못 한다")은 **완전 해소가 아니다**.
새로운 텍스트 배치 우회가 이론적으로 또 나올 수 있다. 이는 `hooks/pre-push:82-85` 가 이미 자인한
**저장소 공통 한계**이며 G3 단독으로 풀 수 없다.
**되돌리는 법** — 실제 실행 영수증(CI가 검사 목록·결과를 기계적으로 공개)을 후속 AC 로 만들면 텍스트
파싱 방어 전체를 폐기할 수 있다. 이 한계를 issue #12 후속으로 남긴다.

**판단 필요:** ⑴ 이 상태(구체 우회 봉쇄 + 실행 영수증은 후속 AC)로 G3 를 병합할지, ⑵ 실행 영수증
인프라까지 이 PR 에 포함할지(범위 대폭 확대). 저는 ⑴을 권합니다 — G3 의 원 단언(운영 상수는
contracts/ 밖 제품 코드에 존재 불가)은 충족됐고, 배선 검사의 근본 강화는 저장소 전체 공통 과제라
G3 에 묶기보다 별도 AC 가 맞습니다.

### V1 3차 판정 원문 (100% — 아래 전문은 수정 없이 그대로다)

---8<--- codex verdict 3차 원문 시작 ---8<---

VERDICT: FAIL

# 결론

구현자가 약속한 다섯 조치 가운데, 이전에 지적했던 열 가지 금지 사례와 단순한 실행 방해 사례는 모두 막혔습니다. 그러나 서버가 자동 검사를 전혀 실행하지 않는 설정을 정상이라고 잘못 승인하는 새로운 우회가 확인됐으므로 최종 승인은 불가합니다.

제품 프로그램 안에 화면 요소를 찾는 일반적인 명령 네 가지를 직접 적어도 자동 검사가 정상으로 승인했습니다. 그대로 병합하면 화면 규칙이 여러 프로그램에 다시 흩어져도 회사의 자동 장치가 놓칠 수 있습니다.

요청하신 문서 두 곳은 실제 동작과 맞게 고쳐졌습니다. 다만 검사 프로그램의 첫머리 설명 한 곳에는 예전 설명이 남아 있어, 다음 수정자가 적용 범위를 잘못 이해할 위험이 있습니다.

# 판단 근거

## 확인 범위, 건너뛴 것, 실패 후 다시 한 것

- 확인된 사실: 인터넷은 전혀 사용하지 않았습니다. 현재 저장소 `HEAD`의 코드, Git 객체, 로컬 임시 복제본과 실행 결과만 사용했습니다.
- 확인된 사실: 실제 GitHub 서버에는 접속하지 않았습니다. CI(코드를 올릴 때 GitHub 서버가 자동으로 실행하는 검사)의 실제 원격 실행은 인터넷 차단 때문에 건너뛰었습니다. 대신 같은 설정 파일을 로컬 YAML(YAML은 자동 실행 절차를 적는 구조화된 설정 형식입니다) 해석기로 읽어, 실제 실행 칸에는 G3 명령이 0개이고 실행되지 않는 환경값 안에만 4개가 있음을 확인했습니다.
- 확인된 사실: G3 본체, 원래 35건 시험, 1차 보강 18건, 2차 보강 16건, `acceptance-0-7` 백업과 셸 문법을 실행했습니다. 저장소 전체의 G1·G2 및 모든 제품 시험은 이번 G3 최종 독립 검증 범위가 아니어서 다시 실행하지 않았습니다.
- ※ GitHub 서비스 자체가 이 변조 파일을 실제로 받아 실행하는 장면은 확인하지 못했습니다. 다만 로컬 YAML 구조 해석 결과와 실제 실행 칸의 값은 확인됐으므로, “G3 명령이 실행 칸에 없다”는 판정에는 추정이 없습니다.
- 첫 실행 묶음은 임시 출력 파일을 지우는 명령이 안전 정책에 막혀 셸이 시작되지 않았습니다. 삭제 없는 직접 실행으로 바꿨고, 차단된 요청은 명령 수에서 제외했습니다.
- 본체를 긴 실행 묶음으로 돌린 두 차례는 도구의 대기 경계에서 출력이 끝까지 회수되지 않았습니다. 본체를 단독 실행하고 실행 중인 세션을 끝까지 기다리는 방식으로 다시 실행해 전체 출력과 종료 상태를 확보했습니다.
- 동결성 첫 대조는 zsh가 공백이 든 문자열을 두 인자로 나누지 않아 잘못된 Git 객체명을 만들었습니다. 그 결과는 폐기하고 세 파일을 각각 명시한 명령으로 재실행했습니다.
- 가짜 서버 단계의 YAML 구조를 세는 첫 Ruby 명령은 설치된 구버전에 `filter_map` 기능이 없어 마지막 집계만 실패했습니다. 앞부분의 구조 출력은 유효했으며, 호환되는 `map`과 `compact`로 다시 실행해 `실행 칸 0개 / 환경값 1개`를 확인했습니다.
- 한 검토 갈래에서 언어 서버 진단 도구 호출이 거부됐습니다. 셸 파일은 `bash -n` 문법 검사와 실제 공격 실행으로 대체했습니다.
- 원본 작업 디렉터리에는 파일을 추가하거나 수정하지 않았습니다. 공격 입력은 임시 복제본에서만 만들었습니다.

## 최종 판정으로 가른 해석

첫째, “2차에 적힌 정확한 사례만 막았으면 합격”이라는 해석은 버렸습니다. 사용자는 이번에 처음 시도하는 우회까지 요구했고, 수용한다고 명시한 한계 밖에서 새 결함이 하나라도 나오면 실패라고 정했습니다. 실제로 두 종류의 새 우회가 그 범위 밖에서 성공했습니다.

둘째, “서버 설정 파일 어딘가에 정확한 명령 문자열 네 줄이 있으면 실제 실행도 보장된다”는 해석은 버렸습니다. 유효한 설정 파일의 환경값 안에 그 네 줄을 넣자 본체가 정상으로 판정했지만, 구조 해석 결과 실제 실행 칸에는 네 줄이 하나도 없었습니다.

셋째, “`get_by_role` 같은 명령은 CSS 표현이 아니므로 G3 대상이 아니다”라는 좁은 해석은 버렸습니다. 정본은 운영 주소·포트·셀렉터를 계약 폴더 한 곳에만 두라고 하고, 웹 자동화 원칙도 화면 요소를 찾는 규칙은 코드가 아니라 데이터라고 정합니다. 현재 전역 규칙도 `querySelector`, `find_element`, `.locator(` 등 화면 요소 찾기 명령 자체를 금지하므로, 같은 목적의 일반 명령 네 가지는 범위 안입니다.

넷째, “문서가 아직 전혀 고쳐지지 않았다”는 해석도 버렸습니다. 요청하신 N7의 정확한 두 곳인 goal 93~97행과 전역 패턴 주석 2~4행은 실제 조건부 면제로 일치합니다. 검사기 머리말 13행의 옛 문구는 별도 잔여 결함으로 분리했습니다.

이 판정이 틀렸다고 가정하면, 실제 실행 칸에 G3 명령이 하나도 없는 서버 설정이 안전하다고 승인되고, 제품 안에 직접 들어간 화면 찾기 규칙도 안전하다고 승인됩니다. 두 경우 모두 G3가 막으려는 “검사가 존재하는 척만 하거나 운영 규칙이 코드 여러 곳에 다시 퍼지는 상태”가 배포 전에 걸러지지 않습니다.

## 요구사항별 판정

여기서 exit code(프로그램이 끝날 때 남기는 숫자로, 이 검사에서는 0은 정상, 1은 위반, 2는 검사 불능을 뜻합니다)를 사용해 각 주장을 판정했습니다.

| ID | 구현자 주장 또는 사용자 검증 항목 | 판정 | 확인된 근거 | 반증 결과 | 영향 |
|---|---|---|---|---|---|
| R1 / N1 | 2차 금지 입력 10종을 각각 정확히 1로 거부 | 구현 확인 | `hardening2` 10종 전부 `exit=1`; 독립 임시 저장소 10/10도 본체 `RC=1` | 같은 원문이 단지 시험에만 있고 본체는 놓칠 가능성을 독립 실행으로 반증 시도했으나 실패 | 이전에 발견한 주소·포트·화면 위치 열 가지는 다시 들어오지 못합니다. |
| R2 / N2 | G3 실행 구역은 주석·빈 줄·`run: |`·정확한 G3 실행 줄만 허용 | 부분 구현 | `if false; then`, `fi`, `exit 0`, `set +e`, `true`, `echo`는 모두 1 | 유효한 YAML 환경값 안에 가짜 G3 구역을 넣자 본체가 0으로 통과; 실제 실행 칸의 G3 명령은 0개 | 치명적 — 서버 최종 검사가 한 번도 실행되지 않은 변경을 정상으로 승인할 수 있습니다. |
| R3 / N3 | 존재하는 G3 파일마다 자기 CI 실행 줄을 자동 요구 | 구현 확인 | 현재 4파일 자동 파생; `hardening` 및 `hardening2` 줄을 각각 지우면 1; 새 다섯째 파일을 추가해도 1 | 수동 고정 목록이어서 새 파일을 놓칠 가능성을 새 파일 추가로 반증 시도했으나 실패 | 현재 파일을 남긴 채 실행 줄만 제거하는 회귀는 서버 등록 누락으로 숨지 못합니다. |
| R4 / N4 | `hooks/pre-push`의 선행 `exit 0` 거부와 `acceptance-0-7` 백업 유지 | 구현 확인 | 선행 `exit 0` 변형은 본체 1; `acceptance-0-7`은 6/6 차단 후 0 | G3 자체 가드를 끄더라도 별도 백업이 사라졌을 가능성을 0-7 실실행으로 반증 시도했으나 실패 | 로컬 검사 전체를 첫 줄에서 끝내는 기존 우회는 두 장치 중 적어도 하나에 걸립니다. |
| R5 / N7 | goal과 전역 패턴 주석을 조건부 문서 면제로 일치 | 구현 확인 | goal 93~97행과 전역 패턴 2~4행이 같은 조건 | 두 곳 중 하나가 여전히 전체 문서 면제라고 쓰였을 가능성을 원문 대조로 반증 시도했으나 실패 | 요청하신 두 기준 문구는 다음 수정자가 같은 조건으로 읽을 수 있습니다. |
| R6 | 세 RED 파일 동결 | 구현 확인 | 각 기준 커밋과 HEAD의 Git blob 식별자가 같고 세 diff가 모두 0 | 후속 커밋이 RED 원장을 고쳐 시험을 맞췄을 가능성을 객체와 파일 로그로 반증 시도했으나 실패 | 과거 실패 증거를 바꿔 합격을 연출하지 않았습니다. |
| R7 | 수용 한계 밖의 새로운 우회가 없어야 함 | 미구현 | 가짜 YAML 환경값 배선과 화면 찾기 명령 4종이 본체 0 | 새로운 직접 변형으로 반증했고 두 축 모두 성공 | 서버 검사 부재와 화면 규칙 재분산을 자동 승인할 수 있으므로 전체 판정은 FAIL입니다. |

→ 무엇을 대조했나: 구현자의 다섯 주장, 동결성, 새 우회 의무를 각각 독립 판정했습니다.  
→ 무엇이 나왔나: 기존 재현은 고쳤지만 핵심 보장 두 축에 새 우회가 남았습니다.  
→ 좋은 소식인가 나쁜 소식인가: 네 항목의 구체 조치는 확인됐으나 최종 승인 기준에는 나쁜 소식입니다.

## 결함 목록

### F1. 치명적 — 실행되지 않는 환경값을 실제 서버 실행으로 오인합니다

그대로 두면 누군가 실제 G3 단계를 없애고 동일한 네 줄을 환경값에 보관하는 것만으로 서버의 최종 방어를 0회로 만들 수 있으며, 저장소 검사기는 이를 정상으로 승인합니다.

**무엇을** — `.github/workflows/verify.yml`을 구조화된 설정으로 읽지 않고, 들여쓰기와 소유 관계를 무시한 텍스트 줄 목록으로 읽습니다.  
**왜** — 별도 구성 해석기 없이 허용 목록(미리 정한 줄만 통과시키는 방식)으로 셸 감싸기와 이물질을 한 번에 막으려 한 선택입니다.  
**버린 대안** — YAML을 구조적으로 읽어 실제 `jobs.*.steps[*].run` 값만 검사하는 방법을 채택하지 않았습니다.  
**대가** — 실행되지 않는 `env.NOTE` 문자열 안의 가짜 `- name:`, `run: |`, G3 네 줄을 실제 단계라고 오인합니다.  
**되돌리는 법** — YAML 구조를 읽어 실제 단계의 `run` 값에 네 줄이 각각 존재하는지 확인하고, 환경값·주석·다른 문자열 안의 일치는 세지 않도록 바꾸면 됩니다. 이 변형을 RED 시험에 먼저 고정해야 합니다.

### F2. 높음 — 일반적인 화면 찾기 명령 네 종류를 놓칩니다

그대로 두면 로그인 버튼·이메일 입력칸·시험용 식별자·로그인 문구를 찾는 규칙이 제품 코드에 직접 들어가도 병합될 수 있고, 채용 사이트 화면이 바뀔 때 여러 파일을 동시에 수리해야 하는 과거 문제가 재발합니다.

**무엇을** — 정규식(문자 모양을 찾아내는 규칙)에 미리 적은 API 이름과 CSS·XPath 모양만 금지합니다.  
**왜** — 모든 문자열을 금지할 때 생기는 거짓 경보를 피하면서 알려진 화면 찾기 표현을 차단하려는 선택입니다.  
**버린 대안** — 지원하는 브라우저 도구의 화면 찾기 API 전체를 범주로 관리하거나, 제품 코드가 계약 로더 이외의 화면 찾기 값을 만들지 못하게 구조적으로 제한하는 방식을 채택하지 않았습니다.  
**대가** — `get_by_role`, `get_by_label`, `get_by_test_id`, `get_by_text`와 `button[type="submit"]` 같은 새 직접 표현이 규칙에 맞지 않아 통과합니다.  
**되돌리는 법** — 사용 중인 브라우저 도구의 의미 기반 화면 찾기 API 계열과 빠진 CSS 계열을 계약 패턴에 추가하고 각각 RED 시험을 만들거나, 계약 로더 외의 화면 찾기 호출 자체를 금지하는 구조 검사로 전환하면 됩니다.

### F3. 중간 — 검사기 머리말의 문서 면제 설명이 실제 동작과 다릅니다

그대로 두면 다음 수정자가 `docs/` 전체를 검사 제외 대상으로 오해해, 이미 고친 실행 파일 은닉 문제를 다시 만들 수 있습니다.

`scripts/acceptance-hs-portal-constants.sh:13`은 “`docs/`는 문서라 금지 패턴 대상이 아니다”라고 적습니다. 하지만 같은 파일 `:127-138`은 다섯 문서 확장자이면서 Git 모드가 `100644`인 파일만 제외합니다. 요청하신 N7 두 곳은 고쳤으므로 N7 이행 자체는 인정하되, 이 세 번째 설명은 새 잔여 불일치로 분리합니다.

# 기술 상세와 증거 원문

## 1. 현재 상태와 깨끗한 기준선

현재 커밋은 `bcf804a87dc86d1d52d86442bf4ff2518bea7e71`입니다. `git status --short`는 출력이 없었고, `git diff --check`도 출력 없이 0이었습니다.

```text
$ bash scripts/acceptance-hs-portal-constants.sh
PASS: portal constants outside contracts 0
PASS: contracts zone violations 0
PASS: ci/pre-push wiring intact
PRODUCT_FILES: 2
CHECKED: 51
CONTRACT_FILES: 3
SCANNER_RC=0
```

→ 뭘 시켰나: 현재 HEAD의 G3 본체를 변조 없이 실행했습니다.  
→ 뭐가 나왔나: 현재 트리는 위반 0, 배선 정상, 제품 2개·검사 51개·계약 3개로 0이었습니다.  
→ 좋은 소식인가 나쁜 소식인가: 깨끗한 기준선이 성립한다는 좋은 소식이지만 우회 방어를 증명하지는 않습니다.

셸 문법 검사도 출력 없이 0이었습니다.

```text
$ bash -n scripts/acceptance-hs-portal-constants.sh scripts/acceptance-hs-portal-constants-mutations.sh scripts/acceptance-hs-portal-constants-hardening.sh scripts/acceptance-hs-portal-constants-hardening2.sh hooks/pre-push scripts/acceptance-0-7.sh
<출력 없음>
RC=0
```

→ 뭘 시켰나: 판정에 사용한 셸 파일 여섯 개가 문법적으로 읽히는지 확인했습니다.  
→ 뭐가 나왔나: 문법 오류가 없었습니다.  
→ 좋은 소식인가 나쁜 소식인가: 실행 전제에는 좋은 소식이나 동작의 완전성 증거는 아닙니다.

## 2. 원래 35건과 1차 보강 18건 회귀

```text
$ bash scripts/acceptance-hs-portal-constants-mutations.sh
ok [clean baseline] exit=0
ok [product scheme URL (.py)] exit=1
ok [product bare domain (tests/.py)] exit=1
ok [product host:port (무작위 파일명)] exit=1
ok [product selector API (.js)] exit=1
ok [product XPath literal] exit=1
ok [product quoted CSS id] exit=1
ok [scripts/ selector API — scripts 면제 금지] exit=1
ok [검사기 자신에 심은 selector — 자기면제 금지] exit=1
ok [루트 파일 CDP 플래그] exit=1
ok [hooks/ 포털 브랜드 도메인] exit=1
ok [루트 contracts/ 정당 값 — 오탐 금지] exit=0
ok [contracts-evil/ 유사 경로 위장] exit=1
ok [중첩 가짜 contracts/ 경로] exit=1
ok [contracts/ 실행 권한 파일] exit=1
ok [contracts/ 허용 확장자 밖] exit=1
ok [CI 무력화: self_commented] exit=1
ok [CI 무력화: self_missing] exit=1
ok [CI 무력화: echo_prefixed] exit=1
ok [CI 무력화: suffixed] exit=1
ok [CI 무력화: if_false] exit=1
ok [CI 무력화: coe] exit=1
ok [CI 무력화: sibling_missing] exit=1
ok [pre-push 부재] exit=1
ok [pre-push 실행권한 제거] exit=1
ok [pre-push 글로브 수집식 제거] exit=1
ok [전역 패턴 계약 부재] exit=2
ok [전역 패턴 계약 빈 파일] exit=2
ok [깨진 정규식] exit=2
ok [빈 문자열 매치 정규식] exit=2
ok [제품 패턴 계약 깨짐] exit=2
ok [제품 루트 부재 — 조용한 skip 금지] exit=2
ok [제품 파일 0건 — 0건 통과 금지] exit=2
ok [위반+깨진 패턴 동시 — 2 우선] exit=2
ok [제품 5파일 깨끗] exit=0
PASS: portal-constants mutations blocked 24/35 (allowed 3, notrun 8)
RC=0
```

→ 뭘 시켰나: 최초 RED 원장 35건을 현재 본체에 다시 실행했습니다.  
→ 뭐가 나왔나: 위반 24건은 1, 허용 3건은 0, 검사 불능 8건은 2였고 전체 시험은 0이었습니다.  
→ 좋은 소식인가 나쁜 소식인가: 최초 방어 회귀가 없다는 좋은 소식입니다.

```text
$ bash scripts/acceptance-hs-portal-constants-hardening.sh
ok [hardening baseline] exit=0
ok [D1 IPv4 비루프백 host:port] exit=1
ok [D1 미등재 .ai 도메인] exit=1
ok [D1 CSS 자손 셀렉터] exit=1
ok [D1 CSS 속성 셀렉터] exit=1
ok [D1 공백 XPath] exit=1
ok [D1 따옴표 CDP 포트] exit=1
ok [D1 매핑형 CDP 포트] exit=1
ok [D1 IPv6 루프백 host:port] exit=1
ok [D2 run 블록 선행 exit 0] exit=1
ok [D2 run 블록 실패 중단 해제] exit=1
ok [D3 검사기 머리말 표식] exit=1
ok [D3 mutation 시험 머리말 표식] exit=1
ok [D4 임시공간 생성 실패] exit=2
ok [D5 docs 실행 코드 은닉] exit=1
ok [D5 정당한 문서 인용 — 오탐 금지] exit=0
ok [D5 실행권한 달린 문서 위장] exit=1
ok [hardening 자기 배선(CI 실행 줄)]
PASS: portal-constants hardening blocked 15/18 (allowed 2, notrun 1)
RC=0
```

→ 뭘 시켰나: 1차 독립 검증에서 나온 18건을 현재 본체에 다시 실행했습니다.  
→ 뭐가 나왔나: 동결된 요약의 `blocked 15`에는 자기 배선 확인 1건이 포함되고, 실제 변조 차단은 14건으로 읽어야 하지만 전체 시험은 0이었습니다.  
→ 좋은 소식인가 나쁜 소식인가: 동결된 숫자의 정오표대로 읽으면 좋은 소식이며, 사용자가 결함으로 세지 말라고 한 수용 한계입니다.

## 3. 2차 금지 입력 10종과 RED3 16건

2차 원문은 `docs/engineering/humansearch-g3-portal-constants-goal-2026-08-12.md:1545-1646`에 다음 열 가지를 보존합니다. 해당 줄들은 순서대로 `.biz` 도메인, 단일 이름 호스트와 포트, 한 자리 포트, 따옴표 포트 키, camelCase 포트 변수, 따옴표 값 CSS 속성, id 자손, 백틱 id, 절대 XPath, 함수 술어 XPath를 기록합니다.

```text
1  PORTAL = "jobs.vendor.biz"
2  REMOTE = "portal:9444"
3  REMOTE = "10.77.4.9:8"
4  {"port": 9333}
5  cdpPort = 9333
6  LOGIN = '[data-testid="sign-in"]'
7  LOGIN = "#login input"
8  LOGIN = `#login`
9  LOGIN = "/html/body/input"
10 LOGIN = '//input[contains(@name, "email")]'
```

→ 뭘 확인했나: 2차 판정 원문의 금지 입력과 RED3 소스 `scripts/acceptance-hs-portal-constants-hardening2.sh:143-182`의 입력을 한 줄씩 대조했습니다.  
→ 뭐가 나왔나: 열 값이 의미와 철자까지 대응하며, 각 시험은 기대값을 정확히 1로 둡니다.  
→ 좋은 소식인가 나쁜 소식인가: 2차 원문이 축약되거나 다른 값으로 바뀌지 않았다는 좋은 소식입니다.

```text
$ bash scripts/acceptance-hs-portal-constants-hardening2.sh
ok [hardening2 baseline] exit=0
ok [N1-1 미등재 .biz 도메인] exit=1
ok [N1-2 단일 라벨 호스트:포트] exit=1
ok [N1-3 한 자리 포트] exit=1
ok [N1-4 JSON 따옴표 포트 키] exit=1
ok [N1-5 camelCase 포트 변수] exit=1
ok [N1-6 따옴표 값 CSS 속성] exit=1
ok [N1-7 CSS id 자손] exit=1
ok [N1-8 백틱 CSS id] exit=1
ok [N1-9 절대 XPath] exit=1
ok [N1-10 함수형 XPath] exit=1
ok [N2 셸 if-false 감싸기] exit=1
ok [N2 블록 내 이물질 줄(true)] exit=1
ok [N3 hardening 실행 줄 삭제] exit=1
ok [N3 pre-push 선행 exit 0] exit=1
ok [hardening2 자기 배선(CI 실행 줄)]
PASS: portal-constants hardening2 cases 16 (blocked-mutations 14, clean-baselines 1, wiring-present 1)
RC=0
```

→ 뭘 시켰나: RED3 정본 16건을 현재 본체로 실행했습니다.  
→ 뭐가 나왔나: 열 가지 금지 입력과 네 가지 변조가 각각 정확히 1이었고, 정상 기준선은 0, 자기 등록도 존재했습니다.  
→ 좋은 소식인가 나쁜 소식인가: 2차에 지적한 정확한 재현들이 봉쇄됐다는 좋은 소식입니다.

독립 임시 저장소 열 개에서도 각 입력은 동일하게 아래 결과를 냈습니다.

```text
FAIL: portal constants outside contracts 1
PASS: contracts zone violations 0
PASS: ci/pre-push wiring intact
PRODUCT_FILES: 3
CHECKED: 17
CONTRACT_FILES: 2
RC=1
```

→ 뭘 시켰나: RED3 시험 함수를 믿지 않고, 입력마다 별도 Git 저장소를 만들어 본체만 실행했습니다.  
→ 뭐가 나왔나: 10/10이 금지 파일 1개를 보고하고 정확히 1로 끝났습니다.  
→ 좋은 소식인가 나쁜 소식인가: 시험 장치와 본체가 서로 짜고 초록을 낸 것이 아니라는 좋은 소식입니다.

`contracts/portal-constants-deny-patterns-product.txt:9-35`는 TLD 확장, 3라벨 호스트, 한 자리부터의 포트, 따옴표·백틱 CSS, XPath와 포트 대입 범주를 담는 줄입니다. 이 규칙에 열 값을 직접 대조한 결과도 모두 정규식 매치 성공이었습니다.

## 4. 단순 배선 훼손과 파일별 자동 요구

`scripts/acceptance-hs-portal-constants.sh:159-172`는 `acceptance-hs-portal-constants*.sh` 파일을 현재 파일 목록에서 찾아 허용 명령 목록을 만드는 줄입니다. 같은 파일 `:178-197`은 단계 안에서 빈 줄·주석·정확한 G3 명령·`run: |`만 허용하는 `ci_line_ok` 함수이고, `:203-208`은 발견한 각 파일에 대해 그 함수를 호출하는 줄입니다. `:219-220`은 주석을 제거한 pre-push에서 순수한 `exit 0` 한 줄을 거부합니다.

```text
CASE ci_if_fi rc=1
FAIL: ci/pre-push wiring broken 4

CASE ci_exit0 rc=1
FAIL: ci/pre-push wiring broken 4

CASE ci_set_true rc=1
FAIL: ci/pre-push wiring broken 4

CASE ci_echo rc=1
FAIL: ci/pre-push wiring broken 4

CASE delete_hardening rc=1
FAIL: ci/pre-push wiring broken 1

CASE delete_hardening2 rc=1
FAIL: ci/pre-push wiring broken 1

CASE prep_exit0 rc=1
wiring: pre-push 에 무조건 exit 0 줄이 있다 — 훅이 검사 전에 통과한다

CASE auto_new_g3 rc=1
wiring: CI 실행 줄이 없거나 블록이 오염됨: bash scripts/acceptance-hs-portal-constants-extra.sh
```

→ 뭘 시켰나: 임시 복제본에서 `if/fi`, `exit 0`, `set +e`와 `true`, `echo`, 두 보강 줄 삭제, pre-push 선행 종료, 새 다섯째 G3 파일을 각각 만들었습니다.  
→ 뭐가 나왔나: 모든 변형이 정확히 1이었고, 새 파일도 자동으로 실행 줄을 요구받았습니다.  
→ 좋은 소식인가 나쁜 소식인가: 구현자가 열거한 단순 변형과 N3 자동 파생은 실제로 동작한다는 좋은 소식입니다.

## 5. pre-push 백업 실행

```text
$ bash scripts/acceptance-0-7.sh
=== 전제 검사: 훅 인프라 ===
OK: 훅 파일 4종 + settings.json 존재

=== 시연 (샌드박스 · 각 시연마다 훅 ON/OFF 대조) ===
[1/6] 검사기 자기 제외 → BLOCKED (훅ON=1 · 훅OFF=0) ✓ 훅이 원인
         BLOCKED: 검사기 자기 제외 — scripts/acceptance-0-6.sh 가 자기 자신을 검사 대상에서 뺀다 (P13)
[2/6] 검사 약화(실패 무시) → BLOCKED (훅ON=1 · 훅OFF=0) ✓ 훅이 원인
         BLOCKED: 검사 약화 패턴 추가 — scripts/acceptance-0-2.sh (P13). 정당하면 suppressions.yaml 에 expiry 와 함께 등록하라
[3/6] 만료일 없는 억제 → BLOCKED (훅ON=1 · 훅OFF=0) ✓ 훅이 원인
         BLOCKED: 억제 항목 1건 중 expiry 가 0건뿐 — 만료일 없는 억제는 영구화된다 (P13)
[4/6] LLM 출력→판정 필드 → BLOCKED (훅ON=1 · 훅OFF=0) ✓ 훅이 원인
         BLOCKED: LLM 출력을 판정 수치로 변환 — src/scoring.js. 판정 수치는 순수 함수가 만든다 (P14)
[5/6] 미커밋 상태로 push → BLOCKED (훅ON=1 · 훅OFF=0) ✓ 훅이 원인
         BLOCKED: 작업트리가 깨끗하지 않다 — 미커밋/미추적 변경이 있는 상태의 push (P15)
[6/6] 가짜 외부효과 모듈 → BLOCKED (훅ON=1 · 훅OFF=0) ✓ 훅이 원인
         BLOCKED: 외부 효과를 표방하는데 네트워크 호출이 0건 — src/portal-login.js. 시뮬레이션 의심 (P4)

OK: 원본 저장소 무변경 확인 (da39a3ee5e6b4b0d3255bfef95601890afd80709)

PASS: 위반 6 종이 전부 차단됨 (각 건 훅 OFF 대조 통과)
RC=0
```

→ 뭘 시켰나: N4가 말한 별도 로컬 훅 백업을 실제로 여섯 공격과 대조군까지 실행했습니다.  
→ 뭐가 나왔나: 훅이 있을 때만 6/6이 차단됐고 전체 시험은 0이었습니다.  
→ 좋은 소식인가 나쁜 소식인가: N4 백업 유지 주장에는 좋은 소식입니다.

`hooks/pre-push:54-60`은 `acceptance-0-7`을 로컬 재귀 때문에 서버로 넘긴다고 설명하는 줄이고, `:93-97`은 서버 실행 줄이 사라지면 차단하는 줄입니다. 독립 변조에서 0-7의 서버 줄을 지우자 다음과 같이 1이었습니다.

```text
CASE acceptance_0_7_ci_backup rc=1
BLOCKED: acceptance-0-7 가 CI(.github/workflows/verify.yml)의 실행 줄에 없다
BLOCKED: ./scripts/acceptance-0-7.sh 가 PUSH-PERFORMING 을 선언했으나 CI 의 실행 줄에 없다 — 아무도 실행하지 않는다
pre-push: 검사 21개 실행
```

→ 뭘 시켰나: 별도 백업의 서버 실행 줄 자체를 삭제했습니다.  
→ 뭐가 나왔나: pre-push가 두 이유로 삭제를 차단했습니다.  
→ 좋은 소식인가 나쁜 소식인가: 백업이 명목상 존재만 하는 것이 아니라는 좋은 소식입니다.

## 6. 새 우회 1 — 환경값 속 가짜 G3 단계

변조한 임시 복제본의 실제 줄은 다음과 같습니다.

```text
48  - name: harmless note carrier
49    run: echo "G3 disabled; payload lives only in env NOTE"
50    env:
51      NOTE: |
52        - name: fake G3 포털 상수·locator 경계
53          run: |
54            bash scripts/acceptance-hs-portal-constants.sh
55            bash scripts/acceptance-hs-portal-constants-mutations.sh
56            bash scripts/acceptance-hs-portal-constants-hardening.sh
57            bash scripts/acceptance-hs-portal-constants-hardening2.sh
```

→ 뭘 시켰나: 실제 G3 단계를 삭제하고, harmless 단계의 실행 명령은 `echo`로 둔 뒤 환경값 `NOTE` 안에 가짜 단계와 정확한 네 줄을 넣었습니다.  
→ 뭐가 나왔나: 설정은 유효하지만 네 줄은 환경 문자열일 뿐입니다.  
→ 좋은 소식인가 나쁜 소식인가: 실제 서버 실행을 흉내만 내는 상태이므로 나쁜 소식입니다.

```text
$ bash scripts/acceptance-hs-portal-constants.sh
PASS: portal constants outside contracts 0
PASS: contracts zone violations 0
PASS: ci/pre-push wiring intact
PRODUCT_FILES: 2
CHECKED: 51
CONTRACT_FILES: 3
SCANNER_RC=0
```

→ 뭘 시켰나: 위 변조 상태에서 현재 G3 본체를 실행했습니다.  
→ 뭐가 나왔나: 배선이 온전하다고 보고하며 정상 0으로 끝났습니다.  
→ 좋은 소식인가 나쁜 소식인가: 실행 0회를 정상으로 오인했으므로 치명적인 나쁜 소식입니다.

```text
STEP_INDEX=4
STEP_NAME="harmless note carrier"
RUN="echo \"G3 disabled; payload lives only in env NOTE\""
NOTE_HAS_G3=true
RUN_FIELDS_WITH_G3=0
ENV_NOTE_FIELDS_WITH_G3=1
CARRIER_RUN="echo \"G3 disabled; payload lives only in env NOTE\""

$ /bin/bash -c 'echo "G3 disabled; payload lives only in env NOTE"'
G3 disabled; payload lives only in env NOTE
```

→ 뭘 시켰나: Ruby YAML 해석기로 실제 단계 구조를 읽고 G3 문자열이 `run`과 `env.NOTE` 중 어디에 속하는지 센 뒤, 실제 `run` 값만 실행했습니다.  
→ 뭐가 나왔나: 실행 칸의 G3는 0개, 환경값의 G3는 1개였고 실제 실행은 `echo` 한 줄뿐이었습니다.  
→ 좋은 소식인가 나쁜 소식인가: 문자열 존재와 실제 실행이 다르다는 반증이 완성됐으므로 나쁜 소식입니다.

처음 시도한 배치는 `env.NOTE` 뒤에 실제 `run: echo`를 두어 텍스트 검사가 그 `echo`까지 같은 가짜 구역의 이물질로 보고 1을 냈습니다. 이를 숨기지 않고 실패한 공격으로 기록합니다. 유효한 YAML에서 실제 `run`을 `env`보다 앞에 둔 두 번째 배치가 0으로 우회했습니다.

## 7. 새 우회 2 — 화면 찾기 명령 네 종류

임시 복제본의 제품 파일에 다음 네 줄을 각각 직접 추가하고 Git 추적 대상으로 넣었습니다. 조각 조립, 이스케이프, 빌드 결과물은 사용하지 않았습니다.

```text
humansearch/src/humansearch/role_locator_probe.py:1
LOGIN_BUTTON = page.get_by_role("button", name="Sign in")

humansearch/tests/test_label_locator_probe.py:1
EMAIL_FIELD = page.get_by_label("Email address")

humansearch/src/humansearch/testid_locator_probe.py:1
SUBMIT = page.get_by_test_id("submit-login")

humansearch/src/humansearch/text_locator_probe.py:1
LOGIN_LINK = page.get_by_text("Log in")
```

→ 뭘 시켰나: 제품 루트 안에 Playwright의 의미 기반 locator(웹 화면 요소를 역할·라벨·식별자·문구로 찾는 표현) 네 종류를 한 줄씩 직접 넣었습니다.  
→ 뭐가 나왔나: 네 파일이 실제 Git 추가 대상으로 잡혔습니다.  
→ 좋은 소식인가 나쁜 소식인가: 정본상 계약 폴더에 있어야 할 화면 찾기 규칙이 제품 코드에 직접 들어간 나쁜 상태입니다.

```text
$ bash scripts/acceptance-hs-portal-constants.sh
PASS: portal constants outside contracts 0
PASS: contracts zone violations 0
PASS: ci/pre-push wiring intact
PRODUCT_FILES: 6
CHECKED: 55
CONTRACT_FILES: 3
SCANNER_RC=0
```

→ 뭘 시켰나: 네 금지 표현을 함께 심은 임시 복제본에서 본체를 실행했습니다.  
→ 뭐가 나왔나: 금지값 0, 배선 정상, 전체 0으로 잘못 승인했습니다.  
→ 좋은 소식인가 나쁜 소식인가: G3의 화면 규칙 단일 출처 보장이 깨졌으므로 나쁜 소식입니다.

현재 전역과 제품 규칙을 합쳐 직접 대조한 추가 새 표현도 모두 “매치 없음”인 1을 냈습니다. 여기서 `grep RC=1`은 G3의 위반 1과 다른 뜻으로, 문자열 규칙이 해당 입력을 찾지 못했다는 의미입니다.

```text
semantic_role RC=1 PAYLOAD=LOGIN_BUTTON = page.get_by_role("button", name="Sign in")
semantic_label RC=1 PAYLOAD=EMAIL_FIELD = page.get_by_label("Email address")
semantic_testid RC=1 PAYLOAD=SUBMIT = page.get_by_test_id("submit-login")
semantic_text RC=1 PAYLOAD=LOGIN_LINK = page.get_by_text("Log in")
css_element_attribute RC=1 PAYLOAD=LOGIN_BUTTON = 'button[type="submit"]'
```

→ 뭘 시켰나: 전역 규칙과 제품 규칙의 주석·빈 줄을 빼고 다섯 새 표현을 직접 검색 규칙에 넣었습니다.  
→ 뭐가 나왔나: 다섯 표현 모두 어느 금지 규칙에도 맞지 않았습니다. 네 의미 기반 명령은 위 본체 실행으로도 우회가 확인됐고, 요소명+속성 CSS는 규칙 대조로 확인했습니다.  
→ 좋은 소식인가 나쁜 소식인가: 열 가지 과거 표현을 막은 뒤에도 같은 계약 범주의 새 직접 표현이 남았으므로 나쁜 소식입니다.

이 공격은 사용자가 결함으로 세지 말라고 한 다음 한계와 겹치지 않습니다: 제품 루트 밖 원시 CSS·일반 URL, `humansearch/` 직속 비코드 설정, 문자열 조각 조립, 이스케이프, 빌드 산출물, G3 파일 자체 삭제, 동결 숫자 정오표를 사용하지 않았습니다.

`docs/sot/coding-principles.md:37`은 운영 상수·URL·포트·셀렉터를 `contracts/*.json` 한 곳에 둔다는 P22를 정하는 줄입니다. 같은 문서 `:45`는 셀렉터는 코드가 아니라 데이터이며 계약 폴더 한 곳에서 관리한다고 정합니다. `contracts/portal-constants-deny-patterns.txt:9-16`은 기존 화면 찾기 API 이름 목록을, 제품 규칙 `:22-31`은 일부 CSS·XPath 모양을 잡는 줄이지만 위 새 API와 요소명+속성 형태는 포함하지 않습니다.

## 8. RED 세 파일 동결성

```text
=== RED1 ===
BASE_BLOB=0cf07fa078a8856255369b3fff255f8c31334d18
HEAD_BLOB=0cf07fa078a8856255369b3fff255f8c31334d18
DIFF_RC=0
=== RED2 ===
BASE_BLOB=bb5e3ee7378418b6f1ded80678eb0b0bd488e726
HEAD_BLOB=bb5e3ee7378418b6f1ded80678eb0b0bd488e726
DIFF_RC=0
=== RED3 ===
BASE_BLOB=1497768d1b36e8592f99c3172f05c0258a0381a8
HEAD_BLOB=1497768d1b36e8592f99c3172f05c0258a0381a8
DIFF_RC=0
=== post-base file logs (all should be empty) ===
<출력 없음>
```

→ 뭘 시켰나: RED1은 `9bab751`, RED2는 `37d2fa7`, RED3는 `8e00bff`의 파일 객체와 HEAD 객체를 비교하고 기준 이후 해당 파일 로그도 조회했습니다.  
→ 뭐가 나왔나: 세 쌍의 객체 식별자가 각각 같고 세 diff가 모두 0이며 후속 파일 변경 로그가 없습니다. 네 기준 커밋 `9bab751`, `37d2fa7`, `8e00bff`, `918b882`도 모두 HEAD의 조상으로 확인됐습니다.  
→ 좋은 소식인가 나쁜 소식인가: RED 원장을 사후 수정하지 않았다는 좋은 소식입니다.

## 9. N7 두 곳과 남은 세 번째 설명

`docs/engineering/humansearch-g3-portal-constants-goal-2026-08-12.md:93-97`은 문서 확장자가 md·yaml·yml·txt·html이고 실행 권한 없는 정규 파일일 때만 제외한다고 정하는 줄입니다.

```text
93  - docs/ 정확 접두 경로 중 문서 확장자(md·yaml·yml·txt·html)이면서 실행 권한 없는 정규
94    파일(100644)만 금지 패턴을 적용하지 않는다
95    ... 그 조건을 벗어난 docs/ 파일은
96    전역 검사 대상이다 — 통 면제는 은닉 경로가 된다
97    면제된 문서는 CHECKED에 세지 않는다
```

→ 뭘 확인했나: N7이 지목한 goal 설명을 읽었습니다.  
→ 뭐가 나왔나: 전체 문서 폴더 면제가 아니라 확장자와 권한을 함께 보는 조건부 면제입니다.  
→ 좋은 소식인가 나쁜 소식인가: 첫 번째 N7 문구는 고쳐졌습니다.

`contracts/portal-constants-deny-patterns.txt:2-4`는 전역 패턴의 적용 범위를 설명하는 줄입니다.

```text
2  적용: contracts/ 와 "문서 확장자(md·yaml·yml·txt·html)이며 실행 권한 없는 docs/ 파일"을 뺀
3        모든 추적 파일 ... 그 밖의 docs/ 파일
4        (실행 코드·실행 권한 문서)은 검사 대상이다
```

→ 뭘 확인했나: N7이 지목한 전역 패턴 주석을 읽었습니다.  
→ 뭐가 나왔나: goal과 같은 조건부 면제를 설명합니다.  
→ 좋은 소식인가 나쁜 소식인가: 두 번째 N7 문구도 고쳐졌습니다.

반면 `scripts/acceptance-hs-portal-constants.sh:13`은 다음과 같습니다. 이 줄은 검사기 첫머리에서 경계 규칙을 요약합니다.

```text
13  # docs/ 는 문서라 금지 패턴 대상이 아니며 CHECKED 에 세지 않는다(카운트 부풀리기 차단).
```

→ 뭘 확인했나: 같은 규칙을 요약하는 검사기 자체 설명도 교차 확인했습니다.  
→ 뭐가 나왔나: 조건을 쓰지 않아 `docs/` 전체가 제외되는 것처럼 읽히며 실제 `:127-138`과 다릅니다.  
→ 좋은 소식인가 나쁜 소식인가: 요청한 두 곳의 이행은 인정하지만 남은 설명 불일치는 나쁜 소식입니다.

## 10. 수용 한계 분류

다음은 이번에 결함으로 세지 않았습니다.

- 제품 루트 밖의 원시 CSS와 일반 URL
- `humansearch/` 바로 아래의 비코드 설정
- 문자열 조각 조립
- 문자 이스케이프
- 빌드 산출물
- G3 검사 파일 자체 삭제가 자동 요구 목록에서도 함께 빠지는 잔여 경로. 이는 diff, P13 라벨, RED 원장 분모 감소로 노출된다는 문서화된 한계입니다.
- 동결된 hardening의 `blocked 15/18`에 자기 배선 1건이 포함된 숫자. 정오표에 따라 변조 차단 14건, 허용 2건, 검사 불능 1건, 배선 확인 1건으로 읽었습니다.
- 실제 GitHub 서버 실행. 인터넷 차단으로 실행하지 못했으며, 로컬 구조 해석과 검사기 실행으로 대체했습니다.

## 11. 최종 반증 장부

- “2차 입력 10종 중 하나라도 여전히 0일 것”을 RED3와 독립 저장소 10개로 반증 시도했으나 실패했습니다. 10/10이 정확히 1이었습니다.
- “`if false; then ... fi`, `exit`, `set`, `true`, `echo` 중 하나가 허용 목록을 빠져나갈 것”을 각각 반증 시도했으나 실패했습니다. 모두 정확히 1이었습니다.
- “hardening 또는 hardening2 실행 줄 하나를 지워도 본체가 0일 것”을 반증 시도했으나 실패했습니다. 둘 다 1이었습니다.
- “새 G3 파일이 자동 요구 목록에 안 들어갈 것”을 다섯째 파일로 반증 시도했으나 실패했습니다. 새 파일의 실행 줄을 요구하며 1이었습니다.
- “pre-push 두 번째 줄의 무조건 `exit 0`이 통과할 것”을 반증 시도했으나 실패했습니다. 본체가 1이었습니다.
- “acceptance-0-7 백업이 이름만 남고 실제 차단하지 못할 것”을 여섯 위반과 훅 ON/OFF 대조로 반증 시도했으나 실패했습니다. 6/6에서 훅만이 차단 원인이었습니다.
- “세 RED 파일이 후속 커밋에서 바뀌었을 것”을 Git 객체와 로그로 반증 시도했으나 실패했습니다. 세 파일 모두 최초 객체와 같습니다.
- “N7 두 문구 중 하나가 옛 전체 면제를 유지할 것”을 원문으로 반증 시도했으나 실패했습니다. 두 문구 모두 조건부 면제입니다.
- “정확한 G3 네 줄이 있으면 실제 서버 단계일 것”을 환경값 블록으로 반증했고 성공했습니다. 본체 0, 실제 실행 칸 G3 0개였습니다.
- “현재 화면 찾기 규칙이 같은 목적의 일반 API도 잡을 것”을 네 직접 호출로 반증했고 성공했습니다. 제품 파일 4개가 추가됐는데도 본체 0이었습니다.
- “CSS 범주 확장이 요소명+속성 직접 표현도 잡을 것”을 `button[type="submit"]`로 반증했고 규칙 대조에서 성공했습니다. ※ 이 다섯 번째 CSS 값은 별도 본체 복제 실행 없이 규칙과 본체 호출 경로 대조로 확인했습니다.

## 12. 최종 상태와 제출 형식 확인

판정서 작성 전 마지막 원본 저장소 상태는 변경 없음이었고, 공백 오류 검사도 0이었습니다. 이 판정서는 지정된 `/private/tmp` 경로에만 제출하며 저장소 파일은 남기지 않습니다.

브리핑 형식 검사 결과는 아래에 기록합니다. 이 숫자는 문서의 세 층 구조와 설명 형식만 검사하며, G3 품질 합격 근거가 아닙니다.

```text
=== .codex-g3-verdict3-2026-08-12.md ===
  코드블록 21개 · 표 1개 (면제 0개) / 해석 누락 0개
  1층(결론): 줄 3 / 본문 268자
  1층 기술 표기: 없음 (※ 한글 전문용어는 못 잡는다 — 사람이 본다)
  결정 카드 2건 (※ 내용이 판단에 쓸 만한지는 못 잰다 — 사람이 본다)
  증거 보관 경로: 임시 외 실재 파일 2건 (※ 그 파일이 이 주장의 증거인지는 못 잰다)

브리핑 계약 기계 검사: 위반 0건 (문서 1개)
```

→ 뭘 시켰나: strict 브리핑 형식 검사기로 결론·판단 근거·증거 해설·설계 카드 등을 점검합니다.  
→ 뭐가 나왔나: 코드·표 해석 누락 0개, 결론의 기계 검출 전문용어 없음, 설계 카드 2건, 전체 위반 0건이었습니다.  
→ 좋은 소식인가 나쁜 소식인가: 형식 확인일 뿐 구현 판정과는 무관합니다.

명령 수는 독립 검증 다섯 갈래가 보고한 165개와 최종 통합 검증자의 외부 명령·파이프라인 99개를 합산했습니다. 도구 대기 확인, 실행 전에 거부된 요청, 파일 패치 동작은 세지 않았습니다.

COMMANDS_RUN: 264

---8<--- codex verdict 3차 원문 끝 ---8<---

### V2-codeaudit 2차 (2026-08-13, 구현자 자체 감사 — 판정: 결함 1건 발견·봉쇄)

codex 3차 이후 배송 대기 중, 구현자가 자기 코드를 codeaudit 로 재감사했다. codex 3라운드가
못 본 각도에서 **치명 결함 1건**을 실행으로 재현했다.

- **A2 (치명)** — 실제 G3 CI 스텝을 지우고 임의 리터럴 스칼라 키(`description:`/`note:`/`summary:`/
  `run-name:`/`comment:`/`memo:` 등 `키: |`) 안에 가짜 G3 단계를 숨기면 배선 검사가 실행 0회를
  정상으로 오인한다(exit 0). 이는 V1 3차 F1(env 값 은닉)과 **동형**이며, GREEN4 가 `env:` 하나만
  배제해 다른 키로 우회가 남은 미봉이었다(상관 블라인드스팟 — codex 도 구현자도 env 만 봤다).

```text
[description: | 은닉]  exit=0   [note: | 은닉]     exit=0
[summary: | 은닉]      exit=0   [run-name: | 은닉] exit=0
[G3 스텝 통삭제]        exit=1   ← 대조군은 정상 차단
```
→ 뭘 했나: 진짜 G3 스텝을 지우고 여러 이름의 여러 줄 텍스트 칸에 가짜 5줄을 숨겨 검사기를 돌렸다.
→ 뭐가 나왔나: 네 종류 전부 통과(exit 0). 단순 삭제만 차단됐다.
→ 의미: 나쁜 소식. 서버 검사에 G3 가 등록된 것처럼 보이지만 실제로는 한 번도 안 돌 수 있었다.

### 조치 — 5차 RED→GREEN (RED5 `f4b4bae` · GREEN5 `3f9ee88` + SOT `f3d4be3`)

- RED5 (`scripts/acceptance-hs-portal-constants-hardening4.sh`, 8케이스): 6개 키 이름으로 은닉을
  재현. 커밋 직전 실측: `FAIL: hardening4 [리터럴 스칼라 은닉: description] exit=0` → exit 1(올바른 RED).
- GREEN5: 배선 파서의 `env:` 특수 배제를 **"run: | 이 아닌 모든 `키: |`/`키: >` 리터럴/폴디드
  블록 스칼라 하위를 실행 칸에서 배제"** 로 일반화. 키 이름 열거 대신 리터럴 스칼라 전체를 한 번에
  닫는다 — 새 키 이름으로 우회할 여지를 원리적으로 없앤다.

```text
GREEN5 재검증 (2026-08-13 00:43~00:52 KST):
  hardening4: cases 8 (blocked-mutations 6, clean-baselines 1, wiring-present 1) exit=0
  A2 우회 4종(description/note/summary/run-name) → 전부 wiring broken exit 1 · 정상 6줄 스텝 exit 0
  동결 회귀: mutations 24/35·hardening 15/18·hardening2 16·hardening3 8 전부 exit 0 · RED 5벌 diff 0줄
  실저장소 검사기 exit 0 (PRODUCT_FILES 2·CHECKED 53·CONTRACT_FILES 3)
  G1 8·G2 3·AC-S1·AC-M·0-2/0-5/0-6/a3/a4·verify.sh·bash -n 32개 전부 exit 0
  pre-push 실호출: 검사 23개 전부 ok · session-status → RED 0/25
```
→ 뭘 했나: 결함을 시험으로 먼저 고정·봉쇄한 뒤 검증 전량을 다시 돌렸다.
→ 결과: 전부 통과. A2 우회는 이제 전부 차단, 정상 설정은 통과.
→ 의미: env 만 막던 미봉을 리터럴 스칼라 일반 배제로 닫아, 같은 부류의 우회를 원리적으로 없앴다.

**남는 근본 한계(불변):** "텍스트로 CI 실제 실행 영수증을 증명 못 한다"는 저장소 공통 한계는 이번에도
그대로다(hooks/pre-push:82-85). 이번 조치는 알려진 구체 우회를 닫은 것이지 실행 영수증을 만든 것이
아니다 — 실행 영수증 인프라는 여전히 issue #12 후속 AC 로 남긴다.


### V1·V2·V3 (2026-08-13, PR #13 검증 라운드) — VERDICT: FAIL, 결함 11건

만든 사람(G) ≠ 검증하는 사람 원칙으로 3단 교차 검증했다. 원문 2건은 아래 파일에 100% 보존한다.

- V1 (codex) 판정 원문: `docs/engineering/humansearch-g3-v1-verdict-2026-08-13.md` (713줄)
  — VERDICT G3: FAIL · 결함 11건(치명 1·높음 5·중간 3·낮음 2).
- V3 (codex 가 Claude 의 V2 분석을 재감시) 조립본: `docs/engineering/humansearch-g3-v3-claude-audit-2026-08-13.md` (386줄)

결함 요약(codex 원문 심각도·file:line 보존):

| ID | 심각도 | 위치 | 그대로 두면 |
|---|---|---|---|
| D1 | 치명 | `acceptance-hs-portal-constants.sh:188-243` | 서버 검사를 실행 안 하는 설정이 정상으로 인정됨(잡 레벨 `if: false` 우회) |
| D2 | 높음 | `:257-267` | 로컬 사전 차단을 꺼도 검사기가 온전하다고 보고 |
| D3 | 높음 | `:31,143-150` | src·tests 밖 새 제품 폴더의 일반 URL 미탐 |
| D4 | 높음 | 전역/제품 패턴 | 단순 클래스 표현(`"button.submit"`) 등 통과 |
| D5 | 높음 | 제품 패턴 | 분할·인코딩 주소 통과(※ V2 재현 실패 — codex 고유 입력 필요) |
| D6 | 높음 | `coding-principles.md:26` | +4,318줄이 저장소 3,000줄 상한(P11③) 초과 |
| D7~D9 | 중간 | (원문 표 참조) | 뮤테이션 tautology / 읽기실패 exit 코드 / 문서 면제 |
| D10~D11 | 낮음 | (원문 표 참조) | IPv4 규칙 중복 / goal 끝 공백 |

V2(Claude) 격리 재현 + V3(codex 재감시) 교차:

| 결함 | V2 재현 | V3(codex가 Claude 감시) |
|---|---|---|
| D1(치명) | 실제 YAML 파서로 `verify.if=False` 확인 + 검사기 "wiring intact" → 재현 | 주장1 **확인(맞음)** — 가짜 조작 아님 |
| D3(높음) | 새 폴더 일반 URL만 → PASS 0(미탐), selector·브랜드는 잡힘 → 재현 | 주장2 **확인(맞음)** — selector 오염 아님 |
| D4(높음) | `"button.submit"` 미탐 직접 확인 | (미판정 — codex V3 병렬분할 중단) |
| D6(높음) | 규칙(P11③)·변경량(4,318) 직접 확인 | (미판정) |
| D5(높음) | **재현 실패** — 내 분할·인코딩 입력은 오히려 잡힘 → 미확인으로 내림 | (미판정) |

**Claude 자기 정정(§6-4):** 최초 "codex 11건 다 정당" 및 "D3=문서화된 비범위라 결함 아님" 두 주장을 정정한다. D3 은 goal 자신의 counter-AC 5(새 제품경로 조용한 누락=가짜합격)와 충돌하므로 codex 의 높음 결함 판정이 맞다. D5 는 내 입력으로 재현 안 돼 미확인이다.

**결론:** 치명 D1 이 3중 확인(codex V1 발견 → Claude V2 실제 파서 재현 → codex V3 재감시 확인)됐으므로 **병합 보류**. D1·D3·D4 새 RED 고정 후 수정, D6 은 PR 분할 필요. 검증자 신분: codex CLI 실행(codex-companion), 판정 파일 쓰기는 격리 정책으로 거부돼 화면 출력을 이 세션이 저장소로 옮김(2026-08-13).
