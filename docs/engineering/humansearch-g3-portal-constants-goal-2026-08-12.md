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
- `docs/` 정확 접두 경로는 문서이므로 금지 패턴을 적용하지 않는다(제품 코드가 아니며,
  `docs/sot/coding-principles.md:37`가 v4 사례 인용으로 포털 도메인을 정당하게 담는다).
  단 CHECKED에 세지 않고 별도 보고하지도 않는다 — 카운트 부풀리기에 못 쓴다.
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

