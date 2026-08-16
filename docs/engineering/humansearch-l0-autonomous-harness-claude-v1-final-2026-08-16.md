# HumanSearch L0 자율 하네스 — Claude V1 최종 원문 (2026-08-16)

## 보존 범위

첫 full V1의 낮은 위험 관찰 세 건을 Codex V2가 전부 재현하고 두 곳을 교정한 뒤, 같은 범위를 다시
검증한 최종 회차입니다. 아래 명령, 입력 prompt, 출력은 요약하지 않은 원문입니다.

## 정확한 실행 명령

```bash
/bin/bash -o pipefail -c 'env -u ANTHROPIC_API_KEY claude --safe-mode --no-session-persistence --permission-mode dontAsk --tools Read,Grep,Bash --allowedTools Read,Grep,Bash --disallowedTools Edit,Write --effort high -p < /tmp/humansearch-l0-v1-final-prompt.txt 2>&1 | tee /tmp/humansearch-l0-v1-iteration2.out'
```

→ API key와 쓰기 권한을 제거하고 현재 staged 문서 전체를 읽기 전용으로 다시 검증했습니다.

## 입력 prompt 전문

```text
당신은 구현자가 아닌 독립 적대검증자입니다. 저장소나 GitHub 상태를 절대 바꾸지 마십시오. Bash는 읽기 전용 조회와 문서 검사만 사용하며 commit, add, push, PR 수정, 파일 쓰기, 테스트 대상 변경을 금지합니다.

검증 대상 저장소는 /Users/kangsangmo/Desktop/Valuehire_v6/worktrees/docs-snapshot 입니다. 이 검증은 제품 구현 완료 판정이 아니라, 장기 부재 중 나중에 실행할 자율 구현 프롬프트와 그 L0 계약을 지금 배송해도 되는지에 대한 사전 문서 판정입니다. 따라서 현재 staged 상태와 PR #15 원격 head가 아직 옛 판본인 사실 자체만으로 FAIL하지 마십시오. 대신 현재 staged 파일 전체가 commit/push/PR #15 갱신 후 안전한 실행 정본과 검증 기록이 될 수 있는지를 판정하고, 원격 배송 완료 여부는 NOT_RUN으로 분리하십시오.

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

→ 첫 V1 뒤 교정된 v2, goal, Claude 원문, Codex V2 기록까지 포함한 staged 전체의 배송 가능성을
정조준했습니다.

## 출력 전문

````text
VERDICT: PASS

# 1) 결론

지금 커밋 대기(staged) 상태로 올려둔 문서 10개는 그대로 commit·push하고 PR #15를 갱신해도 됩니다. 15개 점검 관점 전부를 문서 원문과 실제 저장소·명령으로 대조했고, 계약 모순, 잘못된 실행 절차, 검증 우회, 복원 불가 상태, 권한 확장 중 어느 것도 찾지 못했습니다. 장기 부재 중 자동 실행될 지시서로서 "준비가 안 되면 아무것도 바꾸지 않고 멈춘다"는 구조가 문서 전체에서 기계적으로 닫혀 있음을 확인했습니다.

이 판정의 범위는 "이 문서 묶음을 배송해도 되는가"까지입니다. 실제 commit·push·PR #15 갱신과 그 후의 서버 자동 검사(CI)는 실행하지 않았으므로 원격 배송 완료 여부는 NOT_RUN(실행 안 함)으로 분리합니다. 사장님이 결정하실 일은 "이 내용을 커밋해서 PR #15에 올린다" 하나입니다. 참고로 교정 문서 스스로가 "교정 뒤 Claude 전체 검증을 한 번 더 실행해야 최종 합격"이라고 적어 두었는데, 지금 이 검증이 바로 그 재실행에 해당합니다.

**먼저 밝히는 건너뛴 것·확인 못 한 것·재시도한 것:**

- `scripts/session-status.sh`는 직접 실행하지 않았습니다(원격 조회를 포함하는 스크립트로, 이전 검증에서 시간 초과 이력이 있음). 대신 그 출력이 담던 핵심 값 `origin/main=682f00e`를 `git rev-parse origin/main`으로 직접 재확인했습니다 — NOT_RUN 대체 확인.
- PR #15의 현재 CI 검사 상태는 조회하지 않았습니다. 원격 배송 자체가 NOT_RUN 범위이기 때문입니다.
- v2 프롬프트가 미래에 만들 시험 25개, 변조 검사(mutation), CI 초록불은 모두 미래 실행 계약이므로 당연히 NOT_RUN입니다.
- brief-lint(문서 형식 자동 점검 도구) 실행은 첫 시도에서 종료값 추출이 섞여 나와 위반 건수만 뽑는 형태로 한 번 다시 실행했습니다. 결과는 아래에 있습니다.

# 2) 판단 근거

**왜 PASS인가.** FAIL 사유로 지정된 다섯 부류를 15개 관점 전부에 대조했고, 문서의 주장 하나하나를 제가 같은 저장소에서 같은 명령으로 재현했습니다. 특히 문서에 적힌 "사실"들 — 공백 오류 위치, 클린룸 계획의 줄번호, 파일 지문(SHA-256), Claude CLI 플래그 실재, PR #13이 가져올 검사 스크립트 8개, 선행 PR 3개의 미병합 상태 — 이 전부 실측과 일치했습니다. 과장이나 허위 기재를 한 건도 찾지 못했습니다.

**버린 해석들.**

- "선행 PR #13/#14가 아직 열려 있으니 FAIL"이라는 해석은 버렸습니다. v2 프롬프트는 세 PR 병합이 증명되기 전에는 코드를 0줄도 바꾸지 않고 멈추도록 설계되어 있어, 미병합은 결함이 아니라 이 설계가 방어하는 바로 그 상황입니다.
- "클린룸 계획 377행이 L0에 전이(transition) 표를 요구하는데 새 SOT는 전이를 뺐으니 계약 모순"이라는 해석도 버렸습니다. 새 SOT가 이 충돌을 인지하고 같은 계획의 241~243행(전체 흐름도)과 396~398행(L2/L3 위임)을 근거로 계층을 나눴으며, 충돌 시 SOT 우선·중간안 금지 규칙(SOT 149~151행)이 실행자의 임의 해석을 봉쇄하기 때문입니다.
- "새 SOT 파일 추가가 기존 자동 검사에 걸릴 수 있으니 위험"이라는 해석도 검사 후 버렸습니다. 문서 검사기와 검사 장치 명부(mechanism registry) 대조기를 직접 읽어, 새 파일 추가를 막는 규칙이 없음을 확인했습니다.
- "AGENTS.md가 없는데 체크리스트에 [x]로 표시했으니 허위"라는 해석도 버렸습니다. 교정 문서가 "worktree 파일이 아니라 세션 주입 계약"이라고 출처를 정확히 밝혔고, v2가 실행 시점에 "없는 파일을 있다고 가정하지 않는다"로 위험을 닫습니다.

**이 판정이 틀리면 무엇이 깨지는가.** 이 문서들은 오너 부재 중 AI가 홀로 구현할 때의 유일한 규칙서입니다. 제가 놓친 구멍이 있다면 무인 실행자가 모순된 화면 관측을 로그인 성공으로 분류하는 코드를 만들거나, 검증을 건너뛴 채 완료 보고를 하거나, 실제 채용 포털에 닿을 수 있습니다. 그래서 아래에 모든 재현 증거를 남깁니다.

# 3) 기술 상세

## 3-1. staged 상태·공백·diff 내용 (관점 1, 2)

```
git status --short          → 10개 파일 전부 staged (M 4, A 6), 미추적·미스테이지 변경 0
git diff --cached --check   → 출력 0줄, exit 0
git diff --stat (unstaged)  → 출력 0줄
```
→ 커밋 대기 파일 10개 외에 어떤 잔여 변경도 없고 공백 오류도 없는지 물었고, 전부 깨끗했습니다. 좋은 소식입니다. (참고: Codex V2 기록 시점에는 8개 staged + 검증 기록 1개 미추적이었는데, 지금은 검증 기록 2개까지 staged로 승격된 정상 진행입니다.)

수정 4건의 staged diff를 전부 열어봤습니다. `premerge-a3-a4-v1-verdict-2026-08-09.md`는 117행 끝 공백 한 칸 제거뿐이고, 이 공백이 실제 결함이었는지 재현했습니다:

```
$ git diff-tree --check 68fded1
docs/engineering/premerge-a3-a4-v1-verdict-2026-08-09.md:117: trailing whitespace.  (exit 2)
```
→ 현재 커밋에 실제로 공백 오류가 있고 staged 수정이 그것만 고친다는 교정 문서 34행의 주장이 사실로 재현됐습니다. `docs/sot/INDEX.md` diff는 새 SOT 링크 한 줄 추가뿐이라 새 계약이 정본 색인에 추적됩니다(INDEX.md:9). **관점 2 충족.**

두 폐기 문서(autoloop·kickoff)의 diff는 본문 전체를 폐기 안내로 교체한 것입니다 — 아래 3-9에서 별도 판정합니다.

## 3-2. L0 계약 고정 (관점 3)

`docs/sot/humansearch-l0-surface-contract.md` 직접 대조:

| 요구 | 실제 위치 | 확인 |
|---|---|---|
| 입력 role 정확히 3개 | 39~41행 | `AUTHENTICATED_SURFACE`, `HUMAN_AUTH_SURFACE`, `CHALLENGE_SURFACE` |
| 출력 상태 정확히 5개 | 59~63행 | `UNKNOWN/HUMAN_AUTH/AUTHENTICATED/CHALLENGE/DRIFTED` |
| 정상 16조합 전수 | 72~79행 | 유효성 False×8 + True×(빈 1 + 단일 3 + 다중 4 = 8) = 16, 산수 일치 |
| 잘못된 입력 fail-closed | 50~53행 | 객체 아님·bool 아님·enum 아닌 role → `InvalidObservation` 예외, "문자열이 우연히 enum 값과 같아도 거부" |
| RECHECK/AUTH_CONFLICT/RUNNING/STOP 배제 | 94~95행, 132~135행 | L0 API에서 명시 배제, L2/L3/runner에 소유권 배정 |

→ 다섯 항목 모두 문서에 실재하고 서로 모순이 없습니다. **관점 3 충족.**

## 3-3. 클린룸 계획과의 모순 해소 (관점 4)

계획 원문의 인용 줄번호를 `nl -ba`로 재확인했습니다:

```
241  UNKNOWN → AUTHENTICATED → RUNNING
242      └──→ HUMAN_AUTH ──…──→ RECHECK → AUTHENTICATED
243      └──→ CHALLENGE / AUTH_CONFLICT ──→ STOP
377  | L0 | … 다섯 상태 … 전이와 의미 role schema를 먼저 고정 … transition table 전수 … |
397  | L2 | … HUMAN_AUTH→RECHECK→AUTHENTICATED … |
398  | L3 | 캡차·2FA·세션 충돌은 terminal … retry 0 |
261~263  authenticated_surface / human_auth_surface / challenge_surface
```
→ 새 SOT의 세 role 이름은 계획 261~263행에서 그대로 왔고, "전이는 후속 계층 소유"라는 분리도 계획 397~398행이 이미 스스로 나눠 둔 구조입니다. 즉 임의 설계가 아니라 문서 내부 역할 분리의 명문화입니다. 377행에 남는 "전이 표" 문구와의 잔여 충돌은 SOT 149~151행의 충돌 해소 규칙(계획이 이 문서와 다르면 이 문서를 따르고, 실행자는 중간안 없이 중단)이 닫습니다. **관점 4 충족.**

## 3-4. 선행 병합 게이트의 shell 흐름 (관점 5)

v2 프롬프트 147~176행의 스크립트를 검토하고 도구 실재를 확인했습니다.

- `set -euo pipefail` 아래에서 `gh`/`jq` 부재·실패 시 즉시 비정상 종료 — fail-closed. `jq`는 `/usr/bin/jq`로 실재 확인.
- `state != MERGED`, `base != main`, `mergeCommit.oid` 부재 중 하나라도 걸리면 `blocked=1` 후 최종 `exit 20`.
- squash merge(여러 커밋을 하나로 합쳐 병합) 증명은 GitHub의 `mergeCommit.oid`를 읽어 `git merge-base --is-ancestor <oid> origin/main`으로 검사하고, 143행이 "원래 head commit의 ancestry를 요구하면 안 된다"고 함정을 명시 — 저장소 규칙 `docs/sot/git-workflow.md:21`("PR = 인수 기준 1개. **squash merge**")과 일치.
- `|| object_rc=$?` 패턴으로 `set -e` 조기 종료 없이 실패 코드를 보존 — 흐름 정확.

현재 원격 실황(읽기 전용 조회):

```json
#13 OPEN mergeCommit:null | #14 OPEN mergeCommit:null | #15 OPEN head:68fded1 mergeCommit:null
```
→ 지금 이 프롬프트를 실행하면 정확히 `BLOCKED`로 멈춥니다. 결함이 아니라 설계 의도의 확인입니다. **관점 5 충족.** (병합·배송은 NOT_RUN.)

## 3-5. worktree 생성과 재개 문법 (관점 6)

v2 244행의 primary root(원본 작업 폴더) 탐지 명령을 이 하위 worktree 안에서 직접 실행했습니다:

```
$ git worktree list --porcelain | sed -n '1s/^worktree //p'
/Users/kangsangmo/Desktop/Valuehire_v6
```
→ 하위 worktree에서 시작해도 첫 항목은 항상 primary root이므로 중첩 생성이 없습니다. 좋은 소식입니다. `test -n` 실패 시 추측 경로 금지+BLOCKED(252행), path/branch 불일치 시 자동 삭제·reset 금지(258~259행)도 명시돼 있습니다.

재개 문법(277~294행): `Phase:` trailer가 있는 커밋만 공식 진행점, PLAN 1개 → 시도(attempt)별 RED→GREEN→REVIEW → 통과한 시도만 EVIDENCE 1개, 번호 빈틈없이 증가, 중복·순서 붕괴·소유권 미증명 dirty tree·중복 PR은 전부 BLOCKED, force push 금지. CI 재시도(285~287행)는 기존 EVIDENCE를 지우지 않고 다음 시도를 새로 만들며 최종 완료점은 최대 시도 번호의 EVIDENCE — 복원 모순이 없습니다. trailer 추출 문법 `%(trailers:key=…,valueonly)`도 이 저장소의 git에서 실제 동작함을 확인했습니다. **관점 6 충족.**

## 3-6. RED 25개 수집과 runtime import (관점 7)

- 검산: 결정표 16 + 잘못된 입력 4 + Hypothesis(속성 기반 자동 시험 도구) 5 = 25. 380행 "정확히 25개", 완료 판정 842행과 일치.
- 360~365행이 "파일 최상단 import는 수집 자체를 중단시키므로 금지, 각 test 본문이 부르는 `load_subject()` 안에서 import, 매개변수는 enum 없이도 만들 수 있는 member-name 문자열"까지 구체적으로 지시 — 수집 25개 성공 + 실행만 기능 부재로 실패하는 구조가 실제로 성립합니다.
- 전제 확인: `humansearch/` 패키지 골격은 실재하고(`pyproject.toml`, `src/humansearch/__init__.py`의 `PACKAGE_NAME="humansearch"` 6행, `tests/test_package_boundary.py`), `auth_surface.py`만 없으며, `pyproject.toml` 7~8행 주석이 "hypothesis는 순수 판정 함수가 처음 생길 때 추가"라고 예고 — RED에서 추가하라는 지시와 정합. **관점 7 충족.**

## 3-7. GREEN 불변과 LOCAL_VERIFY (관점 8)

- GREEN 직후 `git diff -- humansearch/tests humansearch/pyproject.toml humansearch/uv.lock`이 비어야 하고(456행), LOCAL_VERIFY에서 현재 시도의 RED 커밋을 trailer로 정확히 한 개 찾아(0개나 2개면 exit 22) `git diff --exit-code <RED_SHA>..HEAD`로 커밋 이력 차원에서도 불변을 증명합니다(509~529행). 구현 허용 범위는 파일 1개·구조 7요소·금지 목록(전이 API, 후속 상태, 포털 문구, 입출력, 예외 삼킴)으로 고정(423~448행). **관점 8 충족.**

## 3-8. G2/G3 게이트·zsh 안전성·mutation (관점 9)

- G2 계열 3개(`acceptance-hs-gates.sh`, `-mutations.sh`, `-antiforge.sh`)는 `ls scripts/`로 현재 저장소에 실재함을 확인했습니다.
- G3는 하나를 고정 기입하지 않고 `find`로 이름 규칙 전체를 열거해 전량 실행하며 2개 미만이면 exit 21(496~506행). PR #13의 변경 파일을 조회한 결과 `acceptance-hs-portal-constants*` 스크립트가 **정확히 8개** 추가됩니다(본체 1, hardening 6, mutations 1) — 병합 후 게이트가 8개 전부를 돕니다.
- 반복은 `while IFS= read -r … <<<"…"` 형태라 zsh(이 Mac의 기본 셸)에서도 목록이 합쳐지거나 쪼개지는 사고가 없습니다.
- mutation(일부러 한 줄을 망가뜨려 시험이 잡는지 보는 검사, 550~568행): `apply_patch`로만 변조·복구(git checkout/reset/stash 금지), 복구 후 통과+`git diff --exit-code` clean 재확인, "임시 잘못된 코드는 commit·push·stash 어디에도 남기지 않는다" 명시. **관점 9 충족.**

## 3-9. Claude V1 / Codex V2 / 폐기 문서 (관점 10, 13)

v2 593~596행 명령의 여섯 조건(API key 제거, safe-mode, 세션 비보존, dontAsk, Read/Grep/Bash 허용, Edit/Write 차단)이 한 명령에 모두 있고, 설치된 CLI에서 플래그 실재를 직접 확인했습니다:

```
--safe-mode / --no-session-persistence / --tools / --allowedTools / --disallowedTools → 전부 실재
--permission-mode choices: acceptEdits, auto, bypassPermissions, manual, dontAsk, plan → dontAsk 실재
```
→ 미래 실행자가 존재하지 않는 플래그로 좌초할 위험이 없습니다. 좋은 소식입니다. 재호출 상한은 형식 재실행 1회 + 대상 교정 1회 후 BLOCKED로 유한(618~621행)이고, Codex V2는 모든 지적을 같은 명령으로 재현하며 기각 항목은 PR 본문에 원문·재현 전문을 요약 없이 공개, 0건이면 "없음" 표기(653~655행). **관점 10 충족.**

폐기 문서 2개는 실행 명령이 0개인 순수 안내문이고, 대체 문서·정본 계약을 가리키며, "branch 정리나 squash merge 뒤 특정 commit이 회수될 수 있으므로 보존을 약속하지 않습니다"(양쪽 14~16행)라고 정직하게 적었습니다. **관점 13 충족.**

## 3-10. CI 실패 복귀·오인 방지·금지 목록·모델 (관점 11, 12, 14)

- EVIDENCE 뒤 CI에서 코드 결함이 나오면 기존 증거를 보존한 채 다음 시도의 전체 사슬을 재수행하고 최종 완료점은 최대 시도의 EVIDENCE(285~287, 793~795행) — 모호성 없음.
- "check 0개는 PASS가 아니라 NOT_RUN; BLOCKED"(797행), 완료 조건 "관측 CI check 1개 이상, 모두 green, skip/cancel 0개"(849행), 45분 timeout은 BLOCKED(798행). **관점 11 충족.**
- 권한 밖 목록(59~66행)과 완료 판정(851행)이 main 직접 push, merge, auto-merge, deploy, 실제 포털, browser, login, credential, PII, 등록, 발송을 모두 금지하고, 다음 C1은 오너 재석+별도 승인 필요·"장기 부재 중 자동 실행 금지" 첫 줄 경고를 요구(698~707행). **관점 12 충족.**
- `gpt-5.6-sol`/`xhigh`는 오너가 지정한 이 세션 자체의 지정이며 미지원 시 무단 하향 없이 변경 0 BLOCKED(37~39행). **관점 14 충족.**

## 3-11. 장기 무인 실행 병리 상태 (관점 15)

brief-lint 부재→NOT_RUN 기록+수동 점검(874~883행), Claude 실패→유한 2회 후 BLOCKED, CI timeout→45분 후 BLOCKED, dirty worktree→BLOCKED, 중복 branch/PR→재사용 또는 BLOCKED, 수정 loop→최대 3회(109행). 어느 병리도 무한 반복이나 임의 복구로 흐르지 않습니다. **관점 15 충족.**

## 3-12. 문서 주장의 추가 재현 (제가 별도로 공격한 부분)

```
$ shasum -a 256 <tracked 클린룸 문서> <다른 worktree의 원본>
04c03a11bf0b88ad… (두 파일 동일)

$ brief-lint.sh × 3 (교정 goal, 새 SOT, v2 프롬프트)
브리핑 계약 기계 검사: 위반 0건 — 3개 파일 전부, exit 0
```
→ "비추적 원본을 byte 단위 동일하게 회수했다"(교정 goal 153~154행)와 "brief-lint 위반 0건"(151행) 주장이 모두 사실로 재현됐습니다. 좋은 소식입니다.

배송을 막을 수 있는 기존 자동 검사도 직접 읽었습니다. `scripts/check-docs-sot.sh`는 필수 5개 파일의 존재·크기만 검사하고 추가 파일을 금지하지 않으며, `docs/sot/mechanism-registry.yaml` 대조기는 특정 검사 장치 문구만 봅니다. PR #14의 파일 크기 게이트는 `humansearch/src, extension/src, bot/src`만 검사하므로 883줄짜리 v2 문서는 대상이 아닙니다. → 이 커밋이 나중에 병합될 선행 게이트들과 충돌할 경로를 찾지 못했습니다.

## 3-13. 결함 아닌 관찰 (심각도 낮음, FAIL 사유 아님)

1. **[낮음] "최종 V1" 명명의 시차.** `claude-v1-…md` 8행은 보존된 출력을 "최종 V1"이라 부르지만, 교정 goal 171행과 codex-v2 94행은 "교정 뒤 V1을 한 번 더 실행해야 최종 PASS"라고 명시합니다. 실제로 보존된 V1 출력의 줄번호 인용(예: ":573-575")은 교정 전 판본 기준이라 현재 v2(592~611행)와 어긋납니다. 이는 원문 그대로 보존 원칙의 자연스러운 결과이고, 미결 상태를 문서가 정직하게 공개하므로 배송을 막지 않습니다. 그대로 두면: 후일 독자가 줄번호를 따라가다 잠시 혼동할 수 있는 정도이며, 지금 이 검증이 요구된 재실행이므로 이 판정을 기록에 추가하시면 그 미결도 닫힙니다.
2. **[낮음] SOT 문구와 시험 4번의 폭 차이.** SOT 50~53행의 잘못된 입력 열거에는 "`matched_roles`가 frozenset이 아님"이 문자 그대로는 없는데, v2의 잘못된 입력 시험 4개 중 하나가 이를 요구합니다(371행). SOT 33~34행이 필드 타입을 frozenset으로 고정하고 GREEN의 검증기가 "각 필드의 runtime type을 검증"(434행)하므로 모순이 아니라 더 엄격한 fail-closed이며, v2가 명시적이어서 실행 갈림도 없습니다. 그대로 두면: 영향 없음.
3. **[낮음] AGENTS.md 부재.** 저장소 전체 검색에서 파일이 없음을 재현했습니다. 교정 goal 131행이 "세션 주입 계약"이라고 출처를 정확히 표기했고, v2 203~204행이 실행 시점 가정 금지를 지시하므로 허위가 아닙니다. 그대로 두면: 영향 없음.

**최종 재확인:** 계약 모순 0건, 검증 우회 경로 0건, 무한 반복 경로 0건, 권한 확장 0건, 복원 불가 상태 0건, 문서 주장 대비 실측 불일치 0건. 낮음 관찰 3건은 실행 안전에 영향이 없습니다. 따라서 **현재 staged 문서 10개는 commit·push하여 PR #15의 실행 정본과 검증 기록으로 배송해도 됩니다.** 원격 배송(commit/push/PR 갱신)과 그 후 CI, `session-status.sh` 실행, PR #15 CI 상태는 NOT_RUN입니다. 이후 순서는 "PR #15 갱신 → #13/#14/#15 오너 병합 → v2 프롬프트 투입"입니다.
````

→ 최종 첫 줄은 `VERDICT: PASS`입니다. 원격 commit·push·PR 갱신·CI는 이 출력 시점에
`NOT_RUN`이므로 뒤의 저장소 Gate와 PR Gate로 별도 증명합니다.
