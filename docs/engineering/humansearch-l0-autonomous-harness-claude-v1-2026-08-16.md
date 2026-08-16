# HumanSearch L0 자율 하네스 — Claude V1 원문 (2026-08-16)

## 보존 범위

첫 교정 전 실행은 terminal session에만 출력되어 raw stdout 파일로 남지 않았습니다. 해당 FAIL의
finding과 조치는
`docs/engineering/humansearch-l0-autonomous-harness-repair-goal-2026-08-16.md`에 보존합니다.
아래는 그 finding을 반영한 뒤 실행한 첫 full V1의 정확한 명령, 입력 prompt, 출력 전문입니다. 이
PASS의 낮은 위험 관찰을 Codex V2가 교정한 뒤 실행한 최종 V1은 별도 final 문서에 보존합니다.

## 정확한 실행 명령

```bash
/bin/bash -o pipefail -c 'env -u ANTHROPIC_API_KEY claude --safe-mode --no-session-persistence --permission-mode dontAsk --tools Read,Grep,Bash --allowedTools Read,Grep,Bash --disallowedTools Edit,Write --effort high -p < /tmp/humansearch-l0-v1-final-prompt.txt 2>&1 | tee /tmp/humansearch-l0-v1-final.out'
```

→ API key를 제거하고 읽기 명령만 무인 승인했으며 파일 편집 도구를 차단했습니다. 출력은 아래에
한 글자도 요약하지 않고 보존합니다.

## 입력 prompt 전문

```text
당신은 구현자가 아닌 독립 적대검증자입니다. 저장소나 GitHub 상태를 절대 바꾸지 마십시오. Bash는 읽기 전용 조회와 문서 검사만 사용하며 commit, add, push, PR 수정, 파일 쓰기, 테스트 대상 변경을 금지합니다.

검증 대상 저장소는 /Users/kangsangmo/Desktop/Valuehire_v6/worktrees/docs-snapshot 입니다. 이 검증은 제품 구현 완료 판정이 아니라, 장기 부재 중 나중에 실행할 자율 구현 프롬프트와 그 L0 계약을 지금 배송해도 되는지에 대한 사전 문서 판정입니다. 따라서 현재 staged 상태와 PR #15 원격 head가 아직 옛 판본인 사실 자체만으로 FAIL하지 마십시오. 대신 현재 staged 파일이 commit/push/PR #15 갱신 후 안전한 실행 정본이 될 수 있는지를 판정하고, 원격 배송 완료 여부는 NOT_RUN으로 분리하십시오.

반드시 직접 읽을 파일:
- docs/engineering/goal-prompts/codex-humansearch-l0-surface-classifier-v2-2026-08-16.md
- docs/sot/humansearch-l0-surface-contract.md
- docs/engineering/humansearch-l0-autonomous-harness-repair-goal-2026-08-16.md
- docs/engineering/humansearch-v6-clean-room-rebuild-goal-2026-08-12.md
- docs/engineering/goal-prompts/codex-humansearch-autoloop-L0-2026-08-16.md
- docs/engineering/goal-prompts/humansearch-L0-kickoff-2026-08-16.md
- AGENTS.md가 실제 파일로 있으면 그 파일, 없으면 staged 문서가 인용하는 저장소 규칙

반드시 직접 확인할 명령과 관점:
1. git status --short, git diff --cached --check, git diff --cached --name-status, git diff --cached -- 위 대상 파일.
2. docs/sot/INDEX.md에서 새 SOT가 추적되는지.
3. L0가 현재 화면의 순수 분류로 고정됐는지: 정확히 3 roles, 5 outputs, 정상 16조합, invalid object/runtime 입력 fail-closed. RECHECK/AUTH_CONFLICT/RUNNING/STOP이 L0에서 빠지고 L2/L3/runner로 분리됐는지.
4. 기존 clean-room 계획의 241행 상태 흐름과 377행 L0 항목 사이 모순을 근거 있게 해소했는지. 새 SOT가 임의 설계가 아니라 문서 내부 역할 분리인지.
5. 선행 PR #13/#14/#15를 모두 fresh origin/main ancestry로 확인하기 전 제품 code 0이라는 게이트가 실제 shell 흐름으로 fail-closed인지. squash merge도 GitHub mergeCommit.oid로 올바르게 증명하는지.
6. 새 worktree 생성이 어느 현재 worktree에서 시작해도 primary root 아래에만 생기는지, 재개 checkpoint grammar가 PLAN과 attempt별 RED/GREEN/REVIEW/EVIDENCE 및 CI 재시도를 모순 없이 복원하는지.
7. RED가 제품 모듈 부재 중에도 collect-only 정확히 25개를 만들고 actual run만 기능 부재로 실패하도록 runtime import를 구체적으로 지시하는지. test/property/invalid input 수가 합계와 맞는지.
8. GREEN이 test 기대값·dependency·lock 불변을 증명하고 최소 구현만 허용하는지.
9. G2/G3 gate를 hardcode 하나로 누락하지 않는지. zsh에서도 파일 목록 반복이 안전한지. mutation이 잘못된 code를 commit/stash에 남기지 않는지.
10. Claude V1 명령이 API key 제거, safe-mode, no persistence, dontAsk, Read/Grep/Bash 허용, Edit/Write 차단을 동시에 만족하는지. 재호출에 유한 상한이 있는지. Codex V2가 모든 finding을 재현하며, Claude 지적을 기각하면 PR 본문에 원문과 재현 전문을 공개하는지.
11. EVIDENCE 뒤 CI code 실패가 새 attempt로 돌아갈 수 있고 final EVIDENCE가 모호하지 않은지. 관측 CI 0/skip/cancel을 PASS로 오인하지 않는지.
12. main 직접 push, merge, auto-merge, deploy, live portal, browser, login, credential, PII, registration, send가 금지되고 다음 C1은 owner-gated로 멈추는지.
13. 폐기 문서가 실행 불가능한 tombstone이고 회수 불가능할 수 있는 특정 commit 보존을 거짓 약속하지 않는지.
14. 모델 gpt-5.6-sol/xhigh는 오너의 명시적 실행 세션 지정으로만 쓰이며, 사용할 수 없을 때 무단 downgrade하지 않고 변경 0 BLOCKED인지.
15. brief-lint helper 부재, Claude 실패, CI timeout, dirty worktree, 중복 branch/PR처럼 장기 무인 실행에서 생길 수 있는 상태가 무한 loop나 임의 복구로 이어지지 않는지.

각 finding은 실제 file:line, 재현 명령, 전체 출력 또는 필요한 최소 완전 출력으로 증명하십시오. 찾지 못한 문제를 만들지 말고, 실행하지 못한 항목은 NOT_RUN으로 표시하십시오. 사실과 추론을 분리하십시오. 최종 VERDICT는 현재 staged 문서 내용이 commit/push되어도 되는지 PASS 또는 FAIL입니다. 사소한 문체 선호만으로 FAIL하지 말고, 계약 모순·잘못된 실행·검증 우회·복원 불가·권한 확장처럼 실제 안정성을 해치는 결함만 FAIL로 판정하십시오.

[출력 형식 — 반드시 지킬 것]
읽는 사람은 기술 배경이 없는 사업 책임자다. 판정 내용은 절대 축소하지 말고, 표현만 풀어 써라.
첫 줄은 정확히 VERDICT: PASS 또는 VERDICT: FAIL.
1) 결론: 결정할 사항을 쉬운 말로 쓴다.
2) 판단 근거: 왜, 버린 해석, 틀리면 무엇이 깨지는지 쓴다.
3) 기술 상세: 명령·출력·file:line·finding을 하나도 생략하지 않는다.
- 전문용어는 첫 등장 문장 안에서 괄호로 풀어 쓴다.
- 출력·코드 블록·표 바로 아래에 “→ 뭘 시켰나 / 뭐가 나왔나 / 좋은 소식인가 나쁜 소식인가” 해석을 붙인다.
- 결함마다 심각도와 그대로 둘 때의 사업/운영 영향을 쓴다.
- 설계 결정을 지적하면 무엇을/왜/버린 대안/대가/되돌리는 법을 쓴다.
- 건너뛴 것·확인 못 한 것·재시도한 것을 앞부분에 쓴다.
- 한국어 존칭체로 쓰고 초등학생용 비유는 쓰지 않는다.
```

→ staged 문서가 배송 가능한지, 장기 무인 실행이 fail-closed인지, L0 계약과 Harness가 모순 없는지를
정조준했습니다.

## 출력 전문

````text
VERDICT: PASS

# 1) 결론

지금 staged(커밋 대기 상태)로 올려둔 문서 8개는 그대로 commit·push하고 PR #15를 갱신해도 됩니다. 나중에 장기 부재 중 자동 실행될 지시서로서, 계약 모순·검증 우회·무한 반복·권한 확장으로 이어지는 결함을 찾지 못했습니다. 실제 채용 사이트·로그인·후보자 정보에 닿는 어떤 경로도 열려 있지 않고, 준비가 안 되면 아무것도 바꾸지 않고 멈추는 구조가 문서 전체에서 일관되게 확인됐습니다.

다만 이 판정은 "문서를 배송해도 되는가"까지입니다. 실제 commit/push/PR #15 갱신, 그 후의 서버 검사(CI)는 아직 실행되지 않았으므로 **원격 배송 완료 여부는 NOT_RUN(실행 안 함)** 으로 분리합니다. 사업 책임자께서 결정하실 것은 "이 staged 내용을 커밋해 PR #15에 올린다" 하나입니다.

**먼저 밝히는 미확인·건너뛴 항목:**
- `bash scripts/session-status.sh`를 제 검증 환경에서 직접 실행하려 했으나 2분 제한에서 timeout으로 중단됐습니다(원격 조회 포함 스크립트로 추정). 이 스크립트의 최신 출력은 NOT_RUN이며, 대신 harness 교정 문서에 기록된 과거 출력과 `git rev-parse origin/main` 값이 일치함을 별도로 확인했습니다.
- v2 프롬프트에 적힌 Claude 검증 명령을 실제로 실행해보지는 않았습니다(실행 자체가 검증 범위 밖). 대신 명령의 모든 플래그가 현재 설치된 CLI에 실재하는지는 `claude --help`로 확인했습니다.
- 문서가 지시하는 미래의 테스트 25개 수집, mutation(일부러 코드를 망가뜨려 시험이 잡는지 보는 검사), CI green은 모두 미래 실행 계약이므로 당연히 NOT_RUN입니다.

# 2) 판단 근거

**왜 PASS인가.** FAIL 사유로 지정된 다섯 부류(계약 모순, 잘못된 실행, 검증 우회, 복원 불가, 권한 확장)를 15개 관점 전부에 대조했고, 각 관점에서 문서 내용이 실제 저장소 자산(스크립트 이름, 패키지 구조, 선행 PR의 파일 목록, CLI 플래그, SOT 규칙)과 맞아떨어졌습니다. 특히 위험한 지점 세 곳 — ① 선행 작업 미완료인데 코드를 시작하는 경로, ② 모순된 화면 관측을 "로그인 성공"으로 잘못 분류하는 경로, ③ 무인 실행 중 무한 반복·임의 복구 경로 — 이 모두 명시적으로 차단돼 있습니다.

**버린 해석들.**
- "선행 PR #13/#14가 아직 OPEN이고 PR #15 원격 head가 옛 판본이니 FAIL"이라는 해석은 버렸습니다. 이번 판정의 대상은 "지금 배송해도 되는 문서인가"이고, v2 프롬프트 자체가 세 PR 병합 전에는 코드를 0줄도 바꾸지 않도록 설계돼 있으므로, 미병합 상태는 결함이 아니라 이 설계가 방어하는 바로 그 상황입니다.
- "클린룸 계획 377행이 L0에 '전이(transition) 표'를 요구하는데 새 SOT는 전이를 L0에서 뺐으니 계약 모순"이라는 해석도 버렸습니다. 새 SOT가 이 충돌을 알고서 근거(같은 계획의 241행 흐름도와 392~398행 L2/L3 위임)를 들어 해소했고, 충돌 시 SOT 우선이라는 규칙을 SOT §9와 v2 불변식 2에 이중으로 박아 실행자가 중간안을 만들 수 없게 했기 때문입니다.
- "G3 게이트 스크립트가 현재 브랜치에 없으니 실행 불가 결함"이라는 해석도 버렸습니다. 그 스크립트 8개는 선행 PR #13이 가져오며, v2는 PR #13 병합 확인 후에만 그 단계에 도달합니다. 병합 후에도 스크립트가 2개 미만이면 exit 21로 멈추는 안전장치까지 있습니다.

**이 판정이 틀리면 무엇이 깨지는가.** 이 문서들은 오너 부재 중 AI가 홀로 코드를 만들 때의 유일한 헌법입니다. 제가 놓친 계약 구멍이 있다면, 무인 실행자가 모순 화면을 인증 성공으로 분류하는 코드를 만들거나, 검증을 건너뛰고 완료 보고를 하거나, 실제 채용 포털에 닿을 수 있습니다. 그래서 아래 기술 상세에 모든 확인 증거를 남깁니다.

# 3) 기술 상세

## 3-1. staged 상태와 공백 검사 (관점 1, 2)

```
$ git status --short                        → 8개 파일 모두 staged(M 6, A... 실제로는 M 4, A 4)
$ git diff --cached --check                 → 출력 없음, exit 0
$ git diff --cached --name-status           → M 4건, A 4건 (요청서와 정확히 일치)
```
→ staged 문서에 공백 오류(trailing whitespace 등)가 0건임을 확인시켰고, 결과는 깨끗했습니다. 좋은 소식입니다.

수정된 `premerge-a3-a4-v1-verdict-2026-08-09.md`의 staged diff는 117행 끝 공백 한 칸 제거뿐입니다. 이것이 실제 결함이었는지 재현했습니다:

```
$ git diff-tree --check 68fded1
docs/engineering/premerge-a3-a4-v1-verdict-2026-08-09.md:117: trailing whitespace.
```
→ 현재 커밋(68fded1)에 실제로 공백 오류가 있고, staged 수정이 그것을 고친다는 harness 교정 문서 34행의 주장이 사실로 재현됐습니다. 좋은 소식입니다.

`docs/sot/INDEX.md` staged diff는 새 SOT 한 줄 추가뿐이며(`+ [humansearch-l0-surface-contract.md](...)`), 새 계약이 정본 색인에 추적됩니다. **관점 2 충족.**

## 3-2. L0 계약의 고정 (관점 3)

`docs/sot/humansearch-l0-surface-contract.md`:
- 입력 role 정확히 3개: 37~41행 (`AUTHENTICATED_SURFACE`, `HUMAN_AUTH_SURFACE`, `CHALLENGE_SURFACE`)
- 출력 상태 정확히 5개: 57~63행 (`UNKNOWN/HUMAN_AUTH/AUTHENTICATED/CHALLENGE/DRIFTED`)
- 완전 결정표 16조합: 72~79행. 검산: 유효성 False×부분집합 8 + True×{빈 집합 1 + 단일 3 + 다중 4} = 8+8=16. **산수 일치.**
- 잘못된 입력 fail-closed(안전한 쪽으로 실패): 50~53행 — 객체가 아니거나, bool이 아니거나, enum이 아닌 role이면 `InvalidObservation` 예외. "문자열이 우연히 enum 값과 같아도 거부"까지 명시.
- `RECHECK/AUTH_CONFLICT/RUNNING/STOP` 제외: 94~95행이 L0 API에서 명시적으로 배제하고, 132~135행(§7)이 L2/L3/runner에 소유권을 배정. **관점 3 충족.**

## 3-3. 241행/377행 모순 해소의 근거 (관점 4)

클린룸 계획 원문을 직접 읽어 대조했습니다.
- `humansearch-v6-clean-room-rebuild-goal-2026-08-12.md:241-243` — 로그인 흐름도에 `RECHECK`, `RUNNING`, `STOP`, `AUTH_CONFLICT` 포함 (사실).
- 같은 파일 `:377` — Phase L0 표는 다섯 상태만 요구 (사실).
- 같은 파일 `:397-398` — L2가 `HUMAN_AUTH→RECHECK→AUTHENTICATED` 전이를, L3가 캡차·세션 충돌 terminal을 소유 (사실).
- role 이름 3개는 같은 계획 `:262-264`의 의미 role 목록에서 그대로 가져옴 (사실).

→ 새 SOT의 "L0=순수 분류, 전이=후속 계층"은 임의 설계가 아니라 계획 문서가 이미 스스로 나눠 놓은 계층을 명문화한 것입니다. 남는 충돌(377행의 "전이 표" 문구)은 SOT `:149-151`의 충돌 해소 규칙("계획이 이 문서와 다르면 이 문서를 따르고, 실행자는 중간안을 만들지 않고 중단")이 닫습니다. **관점 4 충족.**

## 3-4. 선행 병합 게이트의 shell 흐름 (관점 5)

v2 프롬프트 `:147-176`의 script를 검토했습니다.
- `set -euo pipefail` 아래에서 `gh`나 `jq`가 없거나 실패하면 즉시 비정상 종료 → fail-closed.
- `state!=MERGED`, `base!=main`, `mergeCommit` 부재 중 하나라도 걸리면 `blocked=1`, 최종 `exit 20`.
- squash merge 증명: GitHub의 `mergeCommit.oid`(squash로 main에 실제 얹힌 커밋)를 읽어 `git merge-base --is-ancestor <oid> origin/main`으로 조상 여부를 검사. `:143` "원래 head commit의 ancestry를 요구하면 안 된다"고 squash 함정을 명시. 저장소 규칙 `docs/sot/git-workflow.md:21`("PR = 인수 기준 1개. **squash merge**")과 일치.
- `|| object_rc=$?` 패턴으로 `set -e` 조기 종료를 피하면서 실패 코드를 보존 — 흐름 정확.
- 차단 시 행동 `:181-187`: 파일 생성 0, polling·auto-merge 금지.

실제 GitHub 현황(읽기 전용 조회):
```
PR #13 OPEN mergeCommit:null | PR #14 OPEN mergeCommit:null | PR #15 OPEN head:68fded1
```
→ 세 PR 모두 미병합입니다. 즉 이 프롬프트를 지금 실행하면 정확히 `BLOCKED`로 멈춥니다. 이는 결함이 아니라 설계 의도의 확인이며, 오너가 세 PR을 순서대로 병합한 뒤에만 구현이 시작됩니다. **관점 5 충족.** (원격 배송·병합은 NOT_RUN.)

## 3-5. worktree 생성과 재개 문법 (관점 6)

- `:243-252`: `git worktree list --porcelain`의 첫 항목(Git이 보장하는 primary worktree)에서 절대 경로를 구해 그 아래에만 생성. `test -n` 실패 시 추측 경로 금지 + BLOCKED. 어느 worktree에서 시작해도 중첩 생성이 없습니다.
- `:277-294` checkpoint 문법: `Phase:` trailer가 있는 commit만 공식 진행점, PLAN 1개 → attempt별 RED→GREEN→REVIEW → 통과한 attempt만 EVIDENCE 1개, `Attempt: N` 빈틈없이 증가, 중복/순서 붕괴 시 BLOCKED, dirty(미커밋 변경) worktree는 소유권 증명 실패 시 덮어쓰지 않고 BLOCKED, 기존 PR 재사용, force push 금지. CI 재시도는 `:285-287`이 "EVIDENCE를 지우지 않고 다음 attempt를 새로 만들며 최종 완료점은 가장 큰 attempt의 EVIDENCE"로 정의 — 복원 모순 없음. **관점 6 충족.**

## 3-6. RED의 25개 수집과 runtime import (관점 7)

- `:360-365`: 파일 최상단 import 금지 이유("수집 자체가 중단됨")를 적시하고, 각 test 본문이 부르는 `load_subject()` 안에서 `humansearch.auth_surface`를 import, 매개변수는 enum 이전에도 만들 수 있는 member-name 문자열 사용 — collect-only 25개 정상 수집 + 실제 실행만 기능 부재로 실패하는 구조를 구체적으로 지시.
- 수 검산: 결정표 16 + invalid 4 + Hypothesis(속성 기반 자동 시험 도구) 5 = 25. `:380` "정확히 25개" 및 완료 판정 `:820`과 일치.
- 현재 `humansearch/pyproject.toml`에 hypothesis가 없고 주석(7~8행)이 "순수 판정 함수가 처음 생길 때 추가"라고 예고 — RED에서 추가하는 지시와 정합. **관점 7 충족.**

## 3-7. GREEN 불변 증명 (관점 8)

- `:456` GREEN 직후 `git diff -- humansearch/tests humansearch/pyproject.toml humansearch/uv.lock`가 비어야 함.
- `:509` LOCAL_VERIFY에서 `git diff --exit-code <RED_SHA>..HEAD -- (test·의존성·lock 경로)`로 커밋 이력 차원에서도 불변 증명.
- 구현 허용 범위 `:423-447`: 파일 1개, 구조 7요소 고정, 금지 목록(전이 API, 후속 상태, portal 문구, I/O, 예외 삼킴)까지 명시. **관점 8 충족.**

> [관찰 — 심각도 낮음] `<RED_SHA>`가 "Phase: RED trailer를 읽어 확정"이라고만 돼 있어 attempt가 2개 이상이면 어느 RED인지 한 줄 명시가 없습니다. 다만 §7의 attempt 문법(현재 attempt = 가장 큰 번호)과 SHIP 전제 `:713`("RED 이후 기대값 변경 0")이 의미를 닫아 주므로 실행 안정성을 해치지 않습니다. 그대로 두면: 다중 attempt에서 실행자가 첫 RED를 골라 diff가 헛되이 실패할 수 있으나, 그 결과는 위험한 통과가 아니라 보수적인 재검토이므로 사업 영향 없음.

## 3-8. G2/G3 게이트와 zsh 안전성, mutation 복구 (관점 9)

- `:493-506`: G2 계열 3개(`acceptance-hs-gates.sh`, `-mutations`, `-antiforge`)는 현재 브랜치에 실재함을 `ls scripts/`로 확인. G3는 하나를 hardcode하지 않고 `find`로 `acceptance-hs-portal-constants*.sh` 전부를 열거·전량 실행하며 2개 미만이면 exit 21.
- PR #13 브랜치의 파일 목록을 조회한 결과 해당 이름의 스크립트가 **8개** 추가됩니다(`acceptance-hs-portal-constants.sh` 외 hardening 6종, mutations 1종). 병합 후 게이트가 실제로 8개 전부를 돌립니다.
- 반복은 `while IFS= read -r` + here-string으로, zsh/bash 어느 쪽에서도 단어 분리 사고가 없는 형태입니다.
- mutation `:534-548`: `apply_patch`로 한 줄만 변조→실패 확인→`apply_patch`로만 원복(`git checkout/reset/stash` 금지)→targeted 재통과→`git diff --exit-code` clean 확인→"임시 잘못된 코드는 commit·push·stash 어디에도 남기지 않는다" 명시. **관점 9 충족.**

## 3-9. Claude V1 / Codex V2 (관점 10)

v2 `:573-575`의 명령: `env -u ANTHROPIC_API_KEY claude --safe-mode --no-session-persistence --permission-mode dontAsk --tools Read,Grep,Bash --allowedTools Read,Grep,Bash --disallowedTools Edit,Write -p ...`

```
$ claude --help | grep ...
--allowedTools / --disallowedTools / --no-session-persistence / --safe-mode / --tools  → 전부 실재
--permission-mode choices: acceptEdits, auto, bypassPermissions, manual, dontAsk, plan → dontAsk 실재
```
→ 요구된 6개 조건(API key 제거, safe-mode, 무persistence, dontAsk, Read/Grep/Bash 허용, Edit/Write 차단)이 한 명령에 모두 있고, 플래그가 설치된 CLI에 실재합니다. 좋은 소식입니다. 실행 전후 `git status --short`로 변경 0 증명(`:596`)도 요구합니다.

- 재호출 상한 `:598-601`: 형식 위반 재실행 1회 + 대상 교정 재실행 1회, 둘 다 소진 시 BLOCKED — 유한.
- Codex V2 `:608-635`: 모든 finding을 fresh `nl -ba`와 동일 명령 재실행으로 재현하고, **기각한 항목은 PR 본문에 원문 심각도·제목·file:line·명령·출력과 Codex 재현 전문을 요약 없이 전부 공개, 0개면 "없음" 표기**. 관점 10의 요구와 문자 그대로 일치. **충족.**

## 3-10. EVIDENCE 후 CI 실패와 CI 오인 방지 (관점 11)

- `:285-287` + `:771-773`: CI에서 code 결함 발견 시 기존 EVIDENCE를 보존한 채 다음 attempt의 전체 사슬(FIX_RED→…→EVIDENCE→SHIP)을 재수행. 최종 완료점 = 최대 attempt의 EVIDENCE — 모호성 없음.
- `:775` "check 0개는 PASS가 아니라 NOT_RUN; BLOCKED", `:827` 완료 조건 "관측된 CI check 1개 이상, 모두 green, skip/cancel 0개", `:776` 45분 timeout은 BLOCKED. **충족.**

## 3-11. 금지 목록과 owner-gated C1 (관점 12)

`:59-66` 권한 밖: main 직접 수정·push, merge, auto-merge, 배포, PR #13/14/15 대리 merge, 실제 포털, browser/MCP, 로그인, 세션, 자격증명, 후보자 개인정보, 등록, 발송, L2/L3/runner/C1, `--no-verify`. `:676-685` 다음 prompt는 실행용이 아닌 owner-gated 인수인계이며 첫 줄에 "장기 부재 중 자동 실행 금지" 경고 필수, C1은 오너 재석 + 별도 L3 승인 요구. `:684`의 accessible-name/text-free blocker 언급은 클린룸 계획 `:273-274`의 실제 조항과 일치. **충족.**

## 3-12. 폐기 문서 (관점 13)

두 tombstone(폐기 표지) 모두 실행 명령이 0개인 순수 안내문이고, 대체 문서와 정본 계약을 가리키며, "branch 정리나 squash merge 뒤 특정 commit이 회수될 수 있으므로 **보존을 약속하지 않습니다**"(autoloop `:14-15`, kickoff `:14-15`)라고 정직하게 적었습니다. 실제로 PR #15가 squash 병합되면 옛 본문이 담긴 중간 커밋은 회수 불가능해질 수 있으므로 이 문구가 사실에 부합합니다. **충족.**

## 3-13. 모델 지정 (관점 14)

`:37-39`: `gpt-5.6-sol`/`xhigh`는 "오너가 지정한 이 자율 실행 세션 자체의 지정"이며, runtime이 지원하지 않으면 "조용히 낮은 모델로 바꾸지 말고 **변경 0으로 BLOCKED** 보고". **충족.**

## 3-14. 장기 무인 실행의 병리 상태 (관점 15)

| 상태 | 문서의 처리 | 위치 |
|---|---|---|
| brief-lint helper 부재 | `NOT_RUN` 기록 + 9개 질문 수동 답변, 실패 은폐 금지 | v2 `:852-861` |
| Claude 실패/빈 출력 | 유한 재시도 2회 후 BLOCKED | `:598-601` |
| CI timeout | 45분 상한, 완료로 쓰지 않고 BLOCKED | `:776` |
| dirty worktree | 소유권 증명 실패 시 덮어쓰기·폐기 금지, BLOCKED | `:291-292` |
| 중복 branch/PR | 기존 재사용, PR 2개 이상이면 BLOCKED | `:293`, `:735-736` |
| 수정 loop 폭주 | 최대 3회, 4번째 결함은 BLOCKED | `:109` |

→ 어느 병리 상태도 무한 loop나 임의 복구로 흐르지 않고 전부 유한 상한 + fail-closed 종료로 수렴합니다. **충족.**

## 3-15. 잔여 관찰 (FAIL 아님)

- [관찰 — 심각도 낮음] `AGENTS.md`는 저장소에 실재하지 않는데(`ls: AGENTS.md: No such file or directory`), harness 교정 문서 `:131` 체크리스트가 "사용자 제공 AGENTS.md"를 [x]로 표시합니다. "사용자 제공"(세션에 주입된 규칙)이라는 표기라 거짓은 아니고, v2 `:203-204`가 "없는 파일을 있다고 가정하지 않는다"로 실행 시점 위험을 닫습니다. 그대로 두면: 실행 영향 없음, 후일 독자가 파일을 찾다 잠시 혼동할 수 있는 정도입니다.
- [관찰 — 심각도 낮음] attempt 2 이상에서 EVIDENCE가 "다음 owner-gated prompt 파일을 만든다"(`:674-676`)를 다시 만나는데, 파일이 이미 있으면 갱신인지 신규인지 한 줄이 없습니다. 같은 경로를 덮어쓰는 자연스러운 해석만 가능하고 안전 경계에는 영향이 없습니다.

**결론 재확인:** 계약 모순 0건, 검증 우회 경로 0건, 무한 loop 경로 0건, 권한 확장 0건, 복원 불가 상태 0건. 낮음 관찰 3건(RED_SHA 다중 attempt 표기, AGENTS.md 체크 표기, next prompt 재생성)은 모두 실행 안전에 영향이 없습니다. 따라서 **현재 staged 문서는 commit·push하여 PR #15의 실행 정본으로 배송해도 됩니다.** 원격 배송(commit/push/PR 갱신)과 그 후 CI는 NOT_RUN이며, 실행 순서는 "PR #15 갱신 → #13/#14/#15 오너 병합 → v2 프롬프트 투입"입니다.
````

→ 첫 줄은 `VERDICT: PASS`입니다. 낮은 위험 관찰 세 건은 다음 Codex V2에서 각각 다시 재현합니다.
