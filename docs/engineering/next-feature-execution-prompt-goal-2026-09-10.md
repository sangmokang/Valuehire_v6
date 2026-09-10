# 다음 기능 구현 실행 프롬프트 v2 — goal (2026-09-10)

기준 커밋: `origin/main` fc6beed. 위험등급 L1(문서 산출물, 동작 변경 없음).
직전 산출물: Codex 답변 2건(executor 프롬프트 v1 + Issue 자동화 설계)의 적대 감사(2026-09-10, 이 세션).

## 1층 — 결론

이 문서는 다음 기능을 만들 때 실행자에게 그대로 건네는 지시문(§3)과, 그 지시문이 Codex 초안과 어디가 왜 다른지(§2)를 담는다.

사장님이 결정할 것 세 가지다.

1. 본줄기에 직접 올라간 미전송 커밋 f12ea33(Strict 공통 계약 문서 추가)을 그대로 둘지, 작업 가지로 옮겨 정식 검토를 거칠지. 이 커밋은 작업 가지가 아니라 본줄기에 직접 만들어졌고, 아직 저장소에 없는 작업 단위 정책 파일을 정본으로 지목한다.
2. Work Unit 정책(PR 하나에 작업 단위 최대 5개)을 현행 규칙(PR 하나 = 합격 조건 1개)보다 먼저 확정할지. 정책 파일은 아직 검토 중인 가지에만 있고, 그 가지의 추가분은 3,139줄로 PR 크기 상한 3,000줄을 넘는다.
3. Issue부터 PR까지의 자동화를 어디까지 허용할지. 현행 정본은 원격 전송·PR 생성·병합을 사람 승인으로 못 박고 있어, 자동화는 정본 개정과 승인이 먼저다.

§3의 지시문은 위 셋이 어느 쪽으로 결정돼도 동작하도록 "있으면 따르고, 없으면 현행 규칙"으로 분기시켜 두었다.

## 2층 — 판단 근거

### Codex 초안 대비 바뀐 점

| # | Codex v1 | v2 | 왜 |
|---|---|---|---|
| 1 | 필독에 `AGENTS.md` | 제거 | 어느 브랜치·워크트리에도 없다(`git log --all -- AGENTS.md` 0건). 없는 파일을 정본이라 부르면 실행자가 멈추거나 지어낸다(2026-09-07 SOT-30 팬텀 사고와 같은 유형) |
| 2 | 필독에 `docs/sot/work-unit-policy.yaml`, WU 1~5개 | `docs/sot/INDEX.md`에 등재된 경우에만 읽고, 없으면 `git-workflow.md`의 "PR = 인수 기준 1개" | 파일은 미병합 가지에만 있다. main의 정본은 아직 PR=AC 1개다 |
| 3 | strict 두 사본이 다르면 `BLOCKED` | 사본은 `cmp`로 대조하되, 차이가 있으면 보고만 하고 원칙 정본(`coding-principles.md`) 로드 실패일 때만 BLOCKED | 감사 시점에 두 사본은 409줄 차이였다. 그대로면 모든 기능 작업이 0번 단계에서 정지한다. 이후 f12ea33이 동일화했지만 새 머신에서는 다시 갈릴 수 있다(f12ea33 goal 문서 "잔여 위험") |
| 4 | "RED 커밋은 push 불가" | "인수 스크립트 RED와 hs·invoice 시험 RED는 훅이 막는다. 그 외 시험 RED는 훅이 보지 않는다. 어느 쪽이든 RED는 로컬에 두고 `--no-verify`는 쓰지 않는다" | `hooks/pre-push:122`는 `verify.sh`·`acceptance-*.sh`만 찾고, 단위시험은 `acceptance-hs-gates.sh:81`·`acceptance-invoice.sh:84`를 통해서만 돈다. 규칙은 같되 근거를 사실대로 적는다 |
| 5 | "자동 코드 예산 검사" | 검사기 없음을 명시하고 손 측정 명령을 지정 | `scripts/`·`scripts/verify/`·CI에 파일·함수 줄수 검사기가 없다. `principles.yaml:106-114`의 PASS는 문구 대조기 실존만 뜻한다 |
| 6 | 첫 GREEN 뒤 자동 push·Draft PR | push·PR은 사람 승인 뒤 수동 | Codex 자기 계약(`~/.codex/skills/strict/SKILL.md` "자동 실행은 CHECKPOINT까지")과 f12ea33의 `strict-workflow.md` §5가 금지한다 |
| 7 | 게이트 순서가 두 답변에서 달랐음(1차: codeaudit→push, 2차: push→codeaudit) | codeaudit → 적대검증 → push 로 고정 | strict 스킬 §5 순서. 원격에 올린 뒤 감사하면 감사 결과가 원격 이력에 남지 않는다 |
| 8 | 상태 머신을 CI가 강제 | 상태 전이는 로컬 판정기 + 사람 규율임을 명시 | 개인 계정 private repo라 브랜치 보호·룰셋이 403(2026-09-10 재실측). GitHub가 막아주는 것은 없다 |
| 9 | 없음 | 착수 전 동시 세션·열린 PR 확인 단계 추가 | 2026-09-05 동시 세션으로 작업 소실 1건. 오늘도 Codex 세션 3개가 다른 워크트리에서 돌고 있었다 |
| 10 | 없음 | CI 초록불을 event 종류(push/pull_request)로 구분해 읽기 | 같은 SHA에서 push=성공·pull_request=실패가 공존한 실측(메모리 2026-08-27) |

→ Codex 초안의 문장 10개를 현재 저장소와 대조한 결과다. 4개는 없는 파일·없는 검사기·불가능한 강제를 사실처럼 적은 것이라 근거를 바로잡았고, 6개는 규칙은 두되 우회 조건과 확인 절차를 보탰다. 규칙 자체를 뒤집은 항목은 6번(자동 push 금지) 하나다.

### 결정 카드 1 — 기준 커밋을 f12ea33이 아니라 origin/main으로 둔 것

> **무엇을** — 이 문서와 지시문의 기준을 `origin/main`(fc6beed)으로 잡았다.
> **왜** — f12ea33은 본줄기에 직접 만들어져 아직 원격에 없고, 존재하지 않는 파일을 정본으로 지목한다. 이 위에 쌓으면 그 커밋의 운명에 이 문서가 묶인다.
> **버린 길** — 로컬 main(f12ea33) 기준. `strict-workflow.md`를 확정 정본으로 인용할 수 있어 지시문이 짧아지지만, 사장님이 f12ea33을 되돌리면 이 문서가 없는 파일을 가리키게 된다.
> **대가** — 지시문에 "INDEX에 있으면" 분기가 늘어 8줄 길어졌다.
> **되돌리기** — f12ea33이 PR로 병합되면 분기 문구를 지우는 1줄 수정 커밋.

### 결정 카드 2 — RED를 로컬에만 두는 현행 규칙을 유지한 것

> **무엇을** — v1과 같이 RED 커밋은 로컬 증명 경계로 두고 원격에 올리지 않는다.
> **왜** — 현행 정본(`git-workflow.md`, strict 스킬, f12ea33 초안)이 모두 그렇게 적었고, 이 문서는 정본을 바꾸는 자리가 아니다.
> **버린 길** — RED를 push해 CI가 빨강→초록 전이를 SHA로 기록하게 하는 안. P5 ①(RED 이후 시험 파일 불변)을 CI가 검사할 기준 SHA가 생긴다는 장점이 있다.
> **대가** — RED가 있었다는 증거가 실행자의 진술과 로컬 커밋 해시에만 남는다. P17(증거는 만든 자가 쓸 수 없다) 방향과 어긋난다.
> **되돌리기** — `git-workflow.md` 개정으로 "RED push 허용 조건(신규 시험 파일만 변경·구현 파일 변경 0)"을 정하면 지시문 §3-6의 두 문장을 바꾼다.

### 감사에서 확인 못 한 것

- Codex가 어느 체크아웃에서 v1을 썼는지(※ `work-unit-policy.yaml`을 인용한 것으로 보아 PR #37 계열 워크트리로 추정).
- 미병합 검사기 워크트리(`task/file-size-gate`, `wu3b-checkpoint-function-budget`)의 내용. 지시문은 그것들을 "회수 대상"으로만 언급한다.
- V1 독립 검증은 L1이라 실행하지 않았다(`NOT_APPLICABLE`). 사장님이 원하면 이 문서를 codex 읽기 전용 검증에 넘긴다.

## 3층 — 실행 프롬프트 v2 (실행자에게 그대로 전달)

```text
당신은 Valuehire v6의 기능 구현 executor다. 아래 순서를 건너뛰지 않는다.
첫 보고 줄은 반드시 `VERDICT: PASS | FAIL | NOT_RUN | BLOCKED` 중 하나로 시작한다.

## 0. 착수 자격
0-1. 현재 HEAD와 origin/main을 확인한다: `git rev-parse --short HEAD origin/main`.
     두 값이 다르면 그 사실을 첫 보고에 적는다. 로컬 main에 직접 만든 커밋이 있으면 작업을 시작하지 않고 보고한다.
0-2. `bash scripts/session-status.sh`를 실행해 3번째 줄 `RED: N/M`을 그대로 적는다. N>0이면 새 작업을 시작하지 않는다.
     이 명령은 인수 스크립트 28개를 실제로 돌리므로 수 분이 걸린다. 120초 제한을 걸지 말고 끝까지 기다린다.
     N>0이면 어느 스크립트인지 이름을 찾는다(아래 한 줄). `acceptance-0-2`(로컬 전용 `.secret-patterns` 부재)와 `acceptance-0-5`(main ≠ origin/main)는
     코드 결함이 아니라 환경·상태 문제이므로 원인을 해소한 뒤 다시 센다. 그 밖의 RED는 새 작업보다 먼저 닫는다.
     `for c in scripts/acceptance-*.sh verify.sh; do SECRET_PATTERNS_FILE= bash "$c" >/dev/null 2>&1 || echo "FAIL $c"; done`
0-3. 동시 세션을 센다: `ps -Ao pid,etime,command | grep -E 'codex app-server|claude' | grep -v grep`.
     `gh pr list --state open --json number,headRefName`으로 같은 주제의 열린 PR이 있는지 본다. 있으면 중복 착수하지 않고 보고한다.
0-4. 정본을 직접 읽는다. 메모리·이전 보고서로 대신하지 않는다.
     - `docs/sot/INDEX.md` — 여기 등재된 파일만 정본이다. 등재되지 않은 파일명을 정본이라 부르지 않는다.
     - `docs/sot/coding-principles.md`, `docs/sot/principles.yaml`, `docs/sot/git-workflow.md`, `docs/sot/verification-commands.md`
     - INDEX에 `strict-workflow.md`가 있으면 그 순서를, `work-unit-policy.yaml`이 있으면 그 필드를 따른다. 없으면 이 프롬프트의 §2·§3이 현행이다.
     - `hooks/pre-push`, `.github/workflows/verify.yml`, 대상 기능의 마이그레이션·API 계약·타입·시험·호출부
0-5. `bash scripts/acceptance-principles-check.sh`를 실행하고 종료값과 출력 전체를 보고에 붙인다. 0이 아니면 BLOCKED.
0-6. `cmp ~/.codex/skills/strict/SKILL.md ~/.claude/skills/strict/SKILL.md`. 다르면 차이 줄수만 보고하고 계속한다.
     멈추는 조건은 0-4의 원칙 정본을 못 읽었을 때뿐이다.

## 1. 계약 고정 (코드 작성 전)
- 사용자 결과 한 문장, EARS 형식 인수 기준(When/While/If ... 시스템은 ... 해야 한다), 검증 명령과 기대 출력.
- counter-AC: 가짜 구현·조건 무시·권한 우회·빈 결과 은폐·실패 은폐 시나리오 각 1개 이상.
- 입력·출력·오류 Type, null·누락·빈 값·최소·최대 경계, 권한·동시성·재시도·멱등성.
- API request/response 스키마. DB를 건드리면 실제 테이블·컬럼·제약·마이그레이션·기존 데이터 호환성. 안 건드리면 `DB_CONTRACT: NOT_APPLICABLE`과 근거.
- Type은 확정된 DB/API/도메인 계약의 코드 표현이다. 새 원칙으로 만들지 않는다. 외부 입력과 DB 결과에는 런타임 검증을 둔다. 컴파일 성공은 계약 충족 증거가 아니다.
- 계약은 `docs/engineering/<주제>-goal-<YYYY-MM-DD>.md`에 적고, 사장님 승인 전에는 구현을 시작하지 않는다.

## 2. 작업 단위
- 현행 정본(`git-workflow.md`): 워크트리 1개 = 브랜치 1개 = PR 1개 = 인수 기준 1개. 브랜치 수명 48시간.
- INDEX에 `work-unit-policy.yaml`이 있을 때만 그 파일의 `max_units_per_pr`·`claims_per_unit`을 따른다. 없으면 PR당 인수 기준 1개다.
- 각 단위는 ID, 반증 가능한 주장 1개, 선행 단위, 변경 파일·호출 경로, 위험등급, 검증 명령과 기대 출력, 반례 1~3개, 완료 커밋을 갖는다.
- 파일 단위·시간 단위로 나누지 않는다.

## 3. RED → GREEN
3-1. `git worktree add worktrees/<name> -b task/<name> origin/main`. 메인 작업트리에서 소스를 고치지 않는다.
     생성 직후 `cp ../../.secret-patterns .`(gitignore된 로컬 전용 파일)을 한다. 없으면 `acceptance-0-2`가 "판정 불가"로 빨개진다(2026-09-10 실측). `verify.sh`는 커밋된 기본 패턴만으로도 돈다.
3-2. 구현이 없어서 실패하는 시험을 먼저 쓰고 실제로 실행해 실패 이유를 확인한다. 문법·import 오류로 실패하면 RED가 아니다.
3-3. RED 커밋을 만든다. RED는 로컬 증명 경계다. 원격에 올리지 않는다.
     사실 관계: `hooks/pre-push`는 루트·scripts/의 `verify.sh`·`acceptance-*.sh`만 돌린다. humansearch 시험은 `acceptance-hs-gates.sh`, invoice 시험은 `acceptance-invoice.sh`를 통해 돈다. 그 밖의 시험 RED는 훅이 보지 않지만 규칙은 같다. `git push --no-verify`는 어떤 경우에도 쓰지 않는다.
3-4. RED 이후 구현 커밋에서 시험 파일의 기대값을 바꾸지 않는다. 기대값 변경은 단독 커밋이며 삭제된 단언 목록을 커밋 메시지에 적는다.
     이 규칙을 검사하는 자동 장치는 아직 없다(`principles.yaml` P5·P15는 문구 대조만 PASS). 따라서 `git diff <RED_SHA>..HEAD -- '<시험 파일 glob>'`을 보고에 그대로 붙인다.
3-5. 최소 구현 → 첫 GREEN 실행 → 회귀시험 → counter-AC 실제 실행 → 단위 완료 커밋.
3-6. 실패한 검사는 `NOT_RUN`이나 `SKIPPED`로 바꾸지 않는다. 원명령을 다시 실행해 PASS가 될 때까지 진행 중이다.

## 4. 코드 예산 (P11)
- 수치는 `docs/sot/coding-principles.md`의 P11 행에서 매 실행마다 읽는다. 이 프롬프트에 복제하지 않는다.
- 자동 검사기가 아직 없다. 다음을 직접 실행해 보고에 붙인다:
  `git diff --stat origin/main..HEAD | tail -1` (PR 전체 줄수)
  `git diff --name-only origin/main..HEAD | xargs wc -l | sort -n | tail -5` (변경 파일 줄수)
  가장 긴 신규·수정 함수의 줄수를 이름과 함께 적는다.
- 생성물·마이그레이션·픽스처 면제는 goal에 먼저 적는다. 래퍼·재수출·이동으로 한도를 피하지 않는다.
- 초과 시 분할이 먼저다. 미병합 검사기(`task/file-size-gate`, `wu3b-checkpoint-function-budget`)를 새로 짜지 말고 회수한다.

## 5. 최종 게이트 (모든 단위 GREEN 뒤, 순서 고정)
  전체 검증(`bash verify.sh` + `scripts/verify/run-acceptance.sh`로 `scripts/acceptance-*.sh` 전량)
  → 읽기 전용 codeaudit
  → 독립 적대검증(다른 모델 계열, 읽기 전용, 판정 본문·반증 기록 필수)
  → 작업트리 clean 확인(`git status --porcelain` 빈 출력)
  → [사람 승인] push → [사람 승인] PR 생성
  → `bash scripts/verify/check-verified-sha.sh`로 로컬 HEAD·원격 HEAD·CI 검사 SHA 일치 확인
  → CI 결과는 event별로 읽는다: `gh run list --commit <SHA> --json event,conclusion` 에서 push·pull_request 둘 다 success여야 한다
  → 사장님 리뷰 → squash merge(사장님 실행) → 별도 배포 승인 → 운영 readback
- push·PR·merge·deploy는 자동 실행하지 않는다. 현행 정본이 사람 승인 경계로 못 박았다. 자동화는 정본 개정과 승인 뒤의 별도 작업이다.
- 브랜치 보호·룰셋은 이 저장소에서 사용할 수 없다(개인 계정 private). "CI가 막아준다"고 쓰지 않는다. 막는 것은 위 순서와 사람이다.
- 이전 커밋의 초록불을 현재 커밋의 증거로 쓰지 않는다.

## 6. LLMOps
- 기능에 실제 LLM 입력·출력·모델·프롬프트가 포함될 때만 평가셋·품질 지표·환각/개인정보/주입 검사·비용·버전·전후 비교를 추가한다.
- 실행 가능한 평가셋이 저장소에 없으면 `LLMOPS: NOT_IMPLEMENTED`로 적고 별도 작업으로 뺀다. 일반 CI를 LLMOps 증거라 부르지 않는다.

## 7. 완료 보고 (§8 브리핑 계약)
첫 줄 `VERDICT:`. 이어서 결론(전문용어 0개, 사장님이 결정할 것 포함) → 판단 근거(선택·버린 길·틀리면 깨지는 것) → 증거 원문.
증거 원문에는 다음을 순서대로 넣는다.
  1. 사용자 결과  2. 계약과 Type/API/DB 결정  3. 작업 단위 목록  4. RED 실행 출력·GREEN 실행 출력
  5. counter-AC·적대검증 판정 원문  6. 코드 예산 측정 출력  7. 실행한 모든 명령·종료값·핵심 출력
  8. PR 생성 여부와 승인 시각  9. 로컬 HEAD·원격 HEAD·CI SHA·event별 결과  10. 확인하지 못한 것  11. 남은 위험과 롤백 명령
출력·표 바로 아래에 `→ 무엇을 시켰나 / 무엇이 나왔나 / 좋은 소식인가` 1~3줄을 붙인다. 추정에는 ※를 붙인다.

다음은 완료가 아니다: 문서만 작성, Type만 선언, 시험 파일 존재, Draft PR 열림, 로컬 PASS만 있음, 원격 CI가 다른 SHA를 검사함, NOT_RUN을 PASS로 바꿈, 기대값을 구현과 같은 커밋에서 낮춤, 자기 검사만으로 적대검증을 대체함.
```

→ 위 블록이 실행자에게 그대로 건네는 지시문 전문이다. 인용한 파일·스크립트는 모두 fc6beed에 실재함을 확인했고(§증거 장부), 없는 파일은 "INDEX에 있으면"으로만 언급했다. 사람 승인 지점은 push·PR·merge·deploy 네 곳이다.

### 자동화 확장을 위한 전제 (사장님 결정 3에 대한 부록)

Issue → PR 자동화는 다음 순서 외에는 안정성을 주장할 수 없다.

1. `docs/sot/git-workflow.md`에 "자동 push·PR 생성을 허용하는 조건"을 조항으로 넣고 승인한다. 이것이 0번 단계다. 없으면 자동화 첫 실행이 정본 위반이다.
2. Issue 필드 강제는 GitHub Issue Forms(`.github/ISSUE_TEMPLATE/*.yml`, `validations.required: true`)로 한다. 봇이 필요 없다. 현재 템플릿은 0개다.
3. 코드 예산·시험 파일 불변·SHA 귀속 검사기를 먼저 CI에 올린다. 검사기 없는 규칙을 자동화가 "지켰다"고 보고할 수 없다.
4. 열린 PR 23개와 워크트리 약 100개를 먼저 줄인다. 병목은 제작이 아니라 병합이다(2026-08-27 진단과 동일). 생성 자동화는 큐를 늘린다.
5. 그 뒤에야 첫 GREEN 이후의 push·Draft PR 자동화를 L0~L1 등급에 한정해 시험한다. L3(DB·권한·개인정보·외부 발송·CI/훅 변경)은 계속 사람 승인이다.

## 증거 장부

| 주장 | 근거 | 실행 시각(KST) |
|---|---|---|
| `AGENTS.md` 어느 브랜치에도 없음 | `git log --all --oneline -- AGENTS.md` → 0건 | 2026-09-10 19:3x |
| `work-unit-policy.yaml`은 미병합 가지에만 | `git branch --contains d07f613` → `task/pr37-resolution-*`; `git ls-tree task/wu-tdd-context-contract-20260910` → 존재 | 19:4x |
| strict 사본 차이 | 감사 시 `diff | grep -c '^[<>]'` → 409, f12ea33 이후 → 0 | 19:3x / 19:41 |
| pre-push 범위 | `hooks/pre-push:122-123`(글로브: 이름 규칙으로 파일을 모으는 방식), `:9`(--no-verify 우회 명시) | 19:3x |
| 코드 예산 검사기 부재 | `ls scripts scripts/verify`·`grep -i 'size\|budget\|LOC' verify.yml` → 0건 | 19:3x |
| 브랜치 보호 불가 | `gh api repos/{owner}/{repo}/branches/main/protection` → HTTP 403 | 19:3x |
| f12ea33 본줄기 직접 커밋 | `git reflog show main -4` → `commit: Unify strict workflow...`; `origin/main`=fc6beed | 19:4x |
| WU 검사기 가지 3,139줄 | `git diff --stat main task/wu-tdd-context-contract-20260910 | tail -1` → 27 files, 3139 insertions | 19:4x |
| 원칙 검사기 통과 | `bash scripts/acceptance-principles-check.sh` → `VERDICT: PASS`, `CHECKED: 34`, exit 0 (HEAD f12ea33) | 19:41 |
| 새 워크트리 RED 2/29의 정체 | `bash scripts/session-status.sh` → `RED: 2/29`; 직접 실행 `acceptance-0-2.sh` → `FAIL: .secret-patterns 없음/빈 파일`, `acceptance-0-5.sh` → `FAIL: origin/main(fc6beed) != main(f12ea33)` | 20:0x |

→ 위 표는 이 문서의 모든 사실 주장을 명령으로 되짚을 수 있게 한 것이다. 시각이 `x`로 끝난 항목은 분 단위를 기록하지 않았다는 뜻이며, 명령은 그대로 재실행할 수 있다.

## 비범위

- 정본(`docs/sot/*`) 수정은 하지 않았다. 필요한 개정은 1층의 결정 사항으로만 올렸다.
- f12ea33의 처분, PR #37·`task/wu-tdd-context-contract-20260910`의 병합 여부는 사장님 결정이다.
- 이 문서는 로컬 커밋까지만 한다. push·PR은 승인 뒤 수동이다.
