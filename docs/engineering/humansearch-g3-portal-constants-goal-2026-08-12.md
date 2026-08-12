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

(V1 codex · V2 재현 후 이 절에 append)
