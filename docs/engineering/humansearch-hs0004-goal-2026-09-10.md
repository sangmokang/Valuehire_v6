# HS-00.04 — 검증 워크플로 실행 0건 우회를 막는다

## 결론

검증 워크플로의 단계가 온전해도 워크플로 시작 조건이 삭제되거나 경로·브랜치·이벤트 필터로 좁아지면 검사가 한 번도 실행되지 않을 수 있다. HS-00.04는 현재 저장소가 의도한 모든 브랜치 push와 필터 없는 pull request 시작 조건을 기존 CI 무결성 판정기에 고정한다.

이번 세션은 HS-00.04 한 개 작업 단위만 수행한다. 원격 push·PR 생성·merge·운영 쓰기는 하지 않으며, 종료 상태는 검증된 로컬 커밋과 커밋 후 Git 지문 대조로 제한한다.

## 판단 근거와 시작 자격

- 위험 등급: L3. 공유 검증 워크플로가 실행되는 조건과 그 무력화 방어를 바꾼다.
- 선행 완료 기록: HS-00.03 `c28270c1ea6153d4ea0aae83a8562981b2564269`; 그 안의 구현 커밋은 `a2c79f08240cb5be287e8624ed07121ad14dd9ab`이다.
- 시작 시 저장소: 루트 `HEAD=main=origin/main=fc6beedc78019862bc2f1b3bf4c4ad3bbd8e845b`, 추적 변경 0건. 새 작업은 선행 로컬 계보 `c28270c...`에서 분기했다.
- 소유: 최초 브랜치/작업공간 `task/hs-0004-20260910`/`worktrees/hs-0004-20260910`는 독립 검토자의 범위 위반으로 오염되어 증거 보존만 한다. 유효한 소유 작업선은 브랜치 `task/hs-0004-recovery-20260910`, 작업공간 `worktrees/hs-0004-recovery-20260910`, 세션 `hs0004-spec-review-recovery`다.
- 시작 시 중복: 같은 WU 이름의 브랜치·작업공간·커밋은 0건이었다. 이후 최초 독립 검토자가 범위를 위반해 원래 작업선에 커밋·구현을 만들어 현재는 오염 작업선과 recovery 작업선이 각각 존재한다. 오염 작업선은 증거 보존만 하며 소유·구현·판정에 쓰지 않는다. 관련 온라인 작업은 열린 Issue #69이며 HS-00.04 전용 Issue·PR은 없었다.
- 기존 담당 경계: `scripts/verify/check-ci-step-integrity.sh`와 `scripts/acceptance-ci-step-integrity.sh`가 조건부 job·step과 오류 무시를 이미 검사하지만 `on` 시작 조건의 의미는 검사하지 않는다. 새 검사기나 CI 단계를 만들지 않고 이 기존 경계를 보강한다.
- 현재 main 차이: `c28270c...` 이후 main은 같은 CI 무결성 파일에 concurrency·timeout 보강을 포함한다. HS-00.04는 trigger 계약만 소유하며 concurrency·timeout 변경을 가져오거나 되돌리지 않는다. 후속 전달 시 main과 충돌을 수동 재검토한다.
- 시작 검사: Strict 원칙 정본 2개 직접 읽기와 `bash scripts/acceptance-principles-check.sh`는 `CHECKED: 34`, 종료값 0이었다. `scripts/session-status.sh` readback은 선행 HEAD가 main보다 ahead 33/behind 12, 미해결 RED가 `6/31`이며 `acceptance-0-7.sh`는 CI 담당 제외임을 확인했다.
- `AGENTS.md`: 저장소 루트 파일은 없었고 사용자가 이번 세션 입력에 전체 내용을 직접 제공했다. 다른 저장소의 파일로 대체하지 않았다.

## EARS Spec — 한 개 인수 기준

**AC HS-00.04-1.** When 저장소의 `verify` GitHub Actions 워크플로를 CI 무결성 판정기가 읽으면, 시스템은 모든 브랜치 push와 기본 pull request 활동을 경로 필터 없이 시작하고 수동 실행을 유지하는 계약만 승인하며, 시작 이벤트 삭제·축소된 브랜치/활동 필터·`paths`·`paths-ignore`로 검증 실행이 0건이 될 수 있는 사본은 실패시켜야 한다.

검증 명령은 다음 한 개다.

```text
bash scripts/verify/run-acceptance.sh scripts/acceptance-ci-step-integrity.sh
```

기대 출력은 정상 워크플로 1건과 정상 의미 변형이 통과하고, 아래 음성 변이 전부가 기대 종료값으로 거부되며, `CHECKED`가 0이 아니고 마지막 줄이 `VERDICT: PASS`인 것이다. 종료값은 프로그램의 성적으로 0은 합격, 0이 아니면 불합격이다.

## DB API 계약

`NOT_APPLICABLE`. 이 WU는 추적된 YAML 파일을 읽어 판정만 하며 데이터베이스 연결·조회·쓰기를 하지 않는다.

- 테이블·컬럼·키: 해당 없음.
- request/response: DB 요청과 응답 0건.
- 오류 코드: DB 오류 코드 없음. 파일/파싱 오류와 계약 불일치만 아래 CLI 계약으로 처리한다.
- tenant/RLS: tenant 데이터와 행 단위 접근 정책을 사용하지 않는다.
- unique/idempotency: DB 멱등키가 없다. 같은 파일을 반복 판정하면 같은 종료값과 판정 종류를 내야 한다.
- write-ahead/readback: 외부 효과와 쓰기가 없어 해당 없음. 입력 파일은 읽기 전용으로 한 번 파싱하고 원본 작업공간 불변을 전후 비교한다.
- migration/rollback: 스키마와 migration 0건. rollback은 구현 커밋 revert와 RED 재실행이다.

## WU 카드 — 포함·제외·계약·소유

### 사용자 결과

코드나 문서만 바꾼 push와 일반 pull request에서도 검증 워크플로가 통째로 생략되는 설정을 로컬 게이트가 거부한다.

### 포함

- 최상위 trigger 키 `on`의 YAML 의미. YAML 1.1 파서가 plain `on`을 boolean key로 읽는 경우와 따옴표 `"on"`을 문자열 key로 읽는 경우를 같은 의미로 처리한다.
- `push`: 모든 브랜치를 포함하고 경로·태그·제외 필터가 없는 현재 의미.
- `pull_request`: GitHub 기본 활동을 사용하고 branch/path/type 필터가 없는 현재 의미.
- `workflow_dispatch`: 수동 실행 진입점의 존재. 입력 정의는 시작 무결성과 무관하므로 허용한다.
- 기존 job/step 조건·오류 무시·echo/syntax-only 검사는 그대로 유지한다. V1/V2가 찾은 중복 key와 비-mapping job/step의 검사 대상 0건은 같은 워크플로 무효화 경계로 fail-closed 한다.
- 원본 저장소 상태 전후 동일성.

### 제외

- 앞 단계가 `GITHUB_ENV`·`GITHUB_PATH`로 뒤 단계 실행 환경을 바꾸는 HS-00.05.
- concurrency 그룹·timeout 정책의 신규 설계 또는 current main 보강 cherry-pick.
- GitHub 저장소 Actions 활성화 설정, branch protection, required checks, commit-message skip, 포크 승인 정책.
- GitHub Actions의 전체 top-level/event schema allowlist. 이번 WU는 `on`과 같은 boolean slot으로 합쳐지는 YAML 1.1 key만 충돌로 닫고, 알 수 없는 추가 event 허용 계약은 유지한다.
- 원격 GitHub Actions 실행 영수증, 실제 push·PR·merge.
- HumanSearch 포털·브라우저·후보자 데이터·DB·메시지 발송.

### 입력·출력·오류·경계

호출은 기존과 같이 `bash scripts/verify/check-ci-step-integrity.sh [WORKFLOW]`다.

- 입력: UTF-8 GitHub Actions YAML 경로 하나. 생략 시 `.github/workflows/verify.yml`. UTF-8 BOM은 내용이 같은 정상 입력으로 허용한다.
- 정상 출력: 승인된 trigger와 기존 job/step 계약의 PASS 설명, `CHECKED: N` (`N>0`), 종료값 0.
- 계약 위반 출력: `FAIL: TRIGGER_CONTRACT: ...`를 포함하고 종료값 1.
- 파일 없음·권한/읽기 오류·YAML 파싱 실패·top-level mapping 아님·trigger를 구조적으로 읽을 수 없음: `FAIL:`과 `CHECKED: 0`, 종료값 2.
- plain/quoted `on`: 한 가지 표현만 존재하면 동등하게 읽는다. 같은 top-level mapping에 plain 또는 quoted `on`이 두 번 있거나 plain/quoted 표현이 함께 있으면 값이 같더라도 덮어쓰기 가능한 모호한 입력으로 `FAIL:`·`CHECKED: 0`·종료값 2다.
- boolean/case 충돌: YAML 1.1 boolean 집합 `yes/no/true/false/on/off`의 대소문자 변형이나 명시적 `!!bool` key가 실제 `on`과 함께 있으면 AST와 값 계층이 다른 key를 고를 수 있으므로 종료값 2다. 실제 `on` 하나만 plain/quoted/명시적 string tag로 존재하는 정상 입력은 허용하고 `!!bool on`은 거부한다. 값 계층에서 `"on"`/`true` 후보가 정확히 하나가 아니면 trigger를 임의 순서로 고르지 않고 구조 오류로 닫는다.
- scalar/sequence shorthand: `on: push`는 GitHub의 유효한 단일 event 표기이므로 구조 오류가 아니라 필수 event 두 개 누락의 계약 위반 종료값 1이다. `on: [push, pull_request, workflow_dispatch]`처럼 필수 세 event를 모두 포함하면 각 event가 `null`인 mapping과 의미 동등하므로 종료값 0이다. 알 수 없는 event 추가는 아래 추가-event 계약을 따른다.
- event 구조: `on` 하위 모든 mapping에서 동일 key가 두 번 있거나 merge key `<<`·비문자 key가 있으면 값 계층의 병합/덮어쓰기와 GitHub 해석이 갈릴 수 있으므로 `FAIL:`·`CHECKED: 0`·종료값 2다. 따라서 event 이름뿐 아니라 `push.branches`와 `workflow_dispatch.inputs` 내부 중복도 거부한다. `on` 하위 alias는 바깥 anchor의 검사되지 않은 mapping을 끌어올 수 있으므로 값과 무관하게 구조 오류로 거부한다. sequence 원소도 문자열 event만 허용한다.
- `push`: `null`, 빈 mapping, 또는 `branches: ["**"]`만 정상 의미로 인정한다. `branches: ["**"]` 외 다른 key나 음수 패턴은 거부한다. tag 전용/필터는 거부한다.
- `pull_request`: `null` 또는 빈 mapping만 인정한다. `types`, `branches`, `branches-ignore`, `paths`, `paths-ignore`를 포함한 축소는 거부한다.
- `workflow_dispatch`: `null` 또는 mapping을 인정한다. mapping의 `inputs` 의미는 이 WU가 평가하지 않는다.
- 알 수 없는 추가 event는 실행 0 우회를 만들지 않으므로 이 WU만으로 거부하지 않는다. 필수 세 event의 의미는 반드시 유지한다.
- job/step 구조: top-level·`jobs`·각 job mapping·각 step mapping의 중복 key는 종료값 2다. `jobs`의 각 값과 `steps`의 각 원소가 mapping이 아니면 검사 가능한 job/step 0건을 trigger `CHECKED`로 가리지 않고 `CHECKED: 0`, 종료값 2다. 유효 mapping이지만 steps가 없거나 비어 있으면 기존처럼 계약 위반 종료값 1이다.
- 재시도·동시성: 순수 파일 판정이라 재시도 상태가 없고 동시 호출끼리 공유 쓰기가 없다.

## counter-AC와 반박 논리

| 반례 | 실패 조건 | 기대 출력 |
|---|---|---|
| 가장 강한 정상 대조군 | `"on"`으로 따옴표 처리하고 `push: {}`, `pull_request: {}`, `workflow_dispatch` inputs를 둔 의미 동등 사본을 과잉 차단 | 종료값 0, trigger PASS, `CHECKED>0` |
| 가장 강한 실패 반례 | `push`와 `pull_request` 모두 `paths-ignore: ["docs/**"]`로 좁혀 문서 전용 변경에서 실행 0 가능 | 종료값 1, `TRIGGER_CONTRACT` |
| 항상 허용 변이 | trigger 검사를 무조건 true로 바꿔 모든 음성 사본 생존 | 인수 검사 종료값 비0, 해당 음성 기대 불일치 |
| 항상 거부 변이 | trigger 검사를 무조건 false로 바꿔 정상·의미 동등 사본도 거부 | 인수 검사 종료값 비0, 정상 대조 실패 |
| 검사 배선 누락 변이 | checker에서 trigger 검사 호출을 제거 | 음성 사본 하나 이상 생존하여 인수 검사 실패 |
| 데이터 오류 변이 | YAML 파싱 불가, top-level list, duplicate top-level `on`, duplicate event key, trigger 0개 | checker 종료값 2; `FAIL:`과 `CHECKED: 0` |
| V1/V2 boolean 충돌 | literal `true:`/case-changed `On:`과 실제 `on`을 함께 둬 AST와 값 계층이 서로 다른 trigger를 판정 | checker 종료값 2; `FAIL:`과 `CHECKED: 0` |
| YAML 1.1 boolean 전집 | `yes/Yes/YES` 등 다른 boolean key를 실제 plain/quoted `on` 앞뒤에 둬 값 slot을 가로챔 | checker 종료값 2; `FAIL:`과 `CHECKED: 0` |
| 명시적 tag slot 충돌 | `!!bool yes/true/TRUE`를 축소된 실제 `on` 앞뒤에 둬 값 계층의 첫 trigger 후보를 바꿈 | checker 종료값 2; `FAIL:`과 `CHECKED: 0`; `!!bool on` 단독도 거부 |
| YAML 의미 불일치 | `on` mapping에 merge key `<<`, 비문자 event key, sequence 비문자 원소를 넣어 Psych만 의미를 확장 | checker 종료값 2; `FAIL:`과 `CHECKED: 0` |
| 하위 중복 덮어쓰기 | `push.branches`나 `workflow_dispatch.inputs`를 두 번 써 마지막 안전 값으로 앞의 축소 값을 은닉 | checker 종료값 2; `FAIL:`과 `CHECKED: 0` |
| alias 중복 은닉 | `on` 밖 anchor에 중복 `branches`를 둔 뒤 `push: *alias`로 마지막 안전 값만 값 계층에 노출 | checker 종료값 2; `FAIL:`과 `CHECKED: 0` |
| 유효 scalar/BOM | `on: push`를 구조 오류로 분류하거나 UTF-8 BOM 정상 workflow를 파싱 오류로 과잉 차단 | scalar는 종료값 1과 누락 event, BOM 정상 사본은 종료값 0 |
| 검사 대상 0 은닉 | duplicate `jobs`/job/step key 또는 non-mapping job/step으로 실제 검사 가능한 대상을 없앰 | checker 종료값 2; `FAIL:`과 `CHECKED: 0` |
| 읽기 실패 | 존재하지만 읽기 권한이 없는 입력에서 Ruby stack trace로 종료 | checker 종료값 2; `FAIL:`과 `CHECKED: 0` |
| 의미 동등 축약형 | `on: [push, pull_request, workflow_dispatch]`를 구조가 다르다는 이유로 거부하거나 필수 event가 빠진 sequence를 승인 | 필수 세 event가 있으면 종료값 0, 하나라도 빠지면 종료값 1 |
| 과잉 차단 변이 | quoted `on`, 빈 mapping, workflow_dispatch inputs, 알 수 없는 추가 event를 이유 없이 거부 | 정상 대조군 종료값 0 요구가 변이를 실패시킴 |
| event 삭제 | push 또는 pull_request 또는 workflow_dispatch 제거 | 종료값 1, 누락 event 이름 포함 |
| branch 축소 | `push.branches: [main]`, `branches-ignore`, `tags` | 종료값 1, push 범위 축소 설명 |
| PR 활동 축소 | `pull_request.types: [opened]` | 종료값 1, pull_request 범위 축소 설명 |
| path 축소 | push/PR의 `paths` 또는 `paths-ignore` | 종료값 1, 경로 필터 설명 |

반박: 스텝 본문과 이름을 모두 검사하므로 충분하다는 주장은 워크플로가 시작되지 않으면 그 검사가 실행될 기회 자체가 없다는 점에서 기각한다. `on:` 문자열 존재만 보는 기존 `acceptance-0-5.sh`도 주석이나 축소 필터의 의미를 판별하지 못하므로 독립 방어가 아니다.

## 코드 예산

- 정본 한도: 직접 작성 코드 파일 soft 300 / hard 600 LOC, 함수 soft 60 / hard 100 LOC, 이 WU diff hard 3,000줄.
- 시작 줄수: `check-ci-step-integrity.sh` 111, `acceptance-ci-step-integrity.sh` 100, `verify.yml` 287, `verification-commands.md` 102.
- 소유 파일: `scripts/verify/check-ci-step-integrity.sh`, `scripts/acceptance-ci-step-integrity.sh`, `docs/sot/verification-commands.md`, 이 goal과 `docs/engineering/evidence/hs0004-20260910/`. 별도 Python 회귀는 이 shell WU의 canonical acceptance와 중복이라 만들지 않는다.
- V1/V2 전 재산정: checker 195줄, acceptance 231줄이며 직접 증가량은 각각 84줄, 131줄이다. 최초 예상 40/80을 넘었으나 두 파일 모두 soft 300 아래다. 감사 반례 보강 후에도 checker 280줄 이하, acceptance 300줄 이하, 함수 hard 100 아래를 유지한다.
- 생성 파일·fixture 예외: 없음. 임시 고장 YAML은 `mktemp` 아래에서만 생성하고 커밋하지 않는다.
- diff 기준: main이 아니라 선행 WU 완료 `c28270c...` 대비 HS-00.04 단독 diff를 센다. main 직행 PR은 누적 계보와 충돌하므로 만들지 않는다.
- 경계 실증: 기존 코드 예산 판정기로 600줄 정상 사본 PASS, 601줄 고장 사본 FAIL, 대상 0개 FAIL을 실행한다.

## Harness·검증 순서

1. Gate 0: Git·worktree·Issue/PR·소유·미해결 RED·이전 readback과 current main 차이를 회수한다.
2. Gate 1: 이 EARS/DB 비해당/입출력·오류·경계/counter-AC/예산을 커밋하고 독립 검토 PASS를 받는다.
3. Gate 2: 기존 acceptance 파일에 정상/음성 사본만 추가해 실제 빠진 동작 때문에 RED임을 확인하고 독립 시험 검토 뒤 RED 전용 커밋을 만든다.
4. Draft PR: 원격 작업 승인이 없으므로 `NOT_RUN`으로 기록한다.
5. Gate 3: 기존 Ruby/Psych 판정기에 최소 trigger 검사를 추가한다. RED 기대값·단언·skip은 바꾸지 않는다.
6. Gate 3.5: CI의 기존 `ci-step-integrity` 스텝 → acceptance → checker → trigger 판정 호출 경로를 정적·동적 출력으로 증명한다.
7. Gate 4/AUDIT: 정조준, HS-00.01~03, G2, shell, 원칙, `verify.sh`, mutation, Codeaudit, 별도 적대 변이, 실제 Claude V1, 새 맥락 Codex V2 순서로 실행한다.
8. CHECKPOINT: 감사 대상과 같은 지문만 GREEN 커밋하고 Git blob/SHA를 다시 읽는다.

## 영향·데이터 안전·되돌리기

- 영향 반경: CI trigger 정적 판정과 그 시험. 제품 런타임·포털·DB에는 영향 없음.
- 데이터 안전 AC: When 모든 검증과 변이를 실행하면, 시스템은 원본 작업공간 밖 임시 사본만 변경하고 후보자·인증·운영 데이터를 읽거나 쓰지 않아야 한다.
- 배송 상태: `NOT_APPLICABLE`. 내부 검증 도구 변경이며 운영 URL·인증·DB·배포 SHA·라이브 업무 영수증을 만들지 않는다.
- 롤백: GREEN 구현 커밋만 revert하고 RED 커밋을 유지한 채 정조준 명령이 trigger 반례에서 다시 실패하는지 확인한다. Spec과 증거는 역사로 유지한다.

## 결정 카드

> **무엇을** — 기존 CI 무결성 판정기의 YAML 구조 검사에 필수 trigger 의미를 추가한다.<br>
> **왜** — 새 장치를 만들지 않고 이미 CI에 배선된 한 판정기에서 실행 0 우회를 막을 수 있다.<br>
> **버린 길** — `acceptance-hs-kickoff.sh`에 HumanSearch 전용 문자열 검사를 추가하는 길은 전체 verify 워크플로의 시작 조건을 중복 판정하고 HS-00.05와 경계를 섞어 기각한다.<br>
> **대가** — 현재 저장소의 넓은 실행 정책을 의도적으로 고정하므로 향후 비용 절감을 위한 path filter는 별도 계약 변경과 시험 갱신 없이는 쓸 수 없다.<br>
> **되돌리기** — 구현 커밋 revert 후 RED 회귀로 보호가 사라졌음을 확인한다.

## 읽은 정본과 외부 의미 근거

- 사용자 제공 AGENTS 계약, `/Users/kangsangmo/.codex/skills/strict/SKILL.md`.
- `docs/sot/coding-principles.md`, `docs/sot/principles.yaml`, `docs/sot/git-workflow.md`, `docs/sot/verification-commands.md`.
- `docs/sot/humansearch-browser-contract.md`, `docs/sot/humansearch-l0-surface-contract.md`.
- `docs/engineering/humansearch-next-issues-wu-2026-09-10.md`, HS-00.01~03 goal·증거, `humansearch-workflow-env-debt-2026-09-10.md`.
- GitHub 공식 workflow syntax: branch/path/type 필터는 시작 범위를 좁히며, path/branch 필터로 건너뛴 required check는 pending에 남을 수 있다. 이 근거는 계약 의미 확인용이며 원격 실행 증거가 아니다.

## 적대 검증 로그

독립 Spec 검토와 모든 RED 추가 검토는 각각 PASS했다. canonical은 최초 37개에서 V1/V2 반례를 거쳐 52→90→92→100→101→105개로 강화됐으며, 각 새 결함은 테스트 전용 커밋에서 먼저 RED로 재현한 뒤 최소 GREEN을 적용했다. Codeaudit는 nested semantic key 결함을 한 번 FAIL로 잡은 뒤 최종 PASS했고, 실제 Claude V1은 boolean 집합·BOM·scalar·nested duplicate, explicit bool tag·alias, binary semantic `on`, explicit non-string tag·독립 merge mutation을 순차로 찾아 RED 보강을 이끌었다. 마지막 Claude V1은 후보 지문 `74fe789f...`에서 `VERDICT: PASS`, 새 Codex V2도 같은 지문에서 `VERDICT: PASS`였다.

최종 로컬 검증은 targeted 74 passed, G2 Ruff 46·mypy 46·pytest 285, 원칙 34, mutation 105/16/41/37, checker 핵심 mutant 14/14, 별도 적대 반례 16/16, `verify.sh` PASS다. checker 280줄·acceptance 299줄, 최대 함수 상한 27/15줄이다. 독립 V1/V2 검토 당시 누적 구현 diff는 558 insertions/20 deletions이었고 판정 원문·완료 서술을 반영한 구현 커밋 직전 4파일 diff는 560 insertions/20 deletions으로 모두 예산 안이다. 600 허용·601 거부·대상 0 거부도 동일 예산 판정기로 실증했다. 전체 판정 원문·실패 후 재시도·NOT_RUN은 `docs/engineering/evidence/hs0004-20260910/verification-ledger.md`와 동 디렉터리의 V1/V2 판정서에 보존한다.
