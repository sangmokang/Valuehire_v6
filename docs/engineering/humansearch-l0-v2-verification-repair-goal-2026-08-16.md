# HumanSearch L0 v2 실행 프롬프트 재검증·수리 목표 (2026-08-16)

## 1층 — 결론

기존 실행 지시서는 화면 분류의 정답은 맞지만, 실제 실행을 맡기기에는 다섯 군데가 덜 닫혀 있습니다.
서버 검사가 어느 변경을 검사했는지 빠지고, 시작 검사 실패를 무시할 수 있으며, 다른 검증자가 원본을
바꿀 수 있고, 중단 뒤 이어갈 때 두 곳에서 추측이 필요합니다. 이 다섯 곳을 고치기 전에는 최종
실행 지시서로 내보내지 않습니다.

현재 제품 코드와 실제 채용 사이트는 건드리지 않습니다. 선행 변경 세 건을 합치는 일과 회수 가능한
저장소 기록 여덟 건을 지우는 일도 자동으로 하지 않습니다. 이번 판단에서 사장님이 바로 결정할 것은
없고, 수리·재검증·서버 검사까지 끝난 문서만 다음 실행 지시서로 드립니다.

## 2층 — 판단 근거

화면 분류 계약 자체는 세 입력 역할, 다섯 결과, 열여섯 정상 조합으로 서로 맞습니다. 문제는 구현을
시작하고 검증하고 다시 이어가는 절차입니다. 현재 지시서는 새 작업 폴더에서 시작 검사가 실패해도
중단하라는 문장이 없고, 서버 검사 결과가 현재 변경을 대상으로 했는지 확인할 값을 수집하지 않습니다.
또 다른 검증자에게 명령 실행 권한을 넓게 주어, 말로만 금지한 원본 변경을 기술적으로는 할 수 있습니다.

버린 길은 세 가지입니다. 첫째, 기존 문서가 길고 대체로 잘돼 있다는 이유로 그대로 통과시키지
않습니다. 둘째, 회수 가능한 저장소 기록을 자동 삭제해 시작 검사를 억지로 초록으로 만들지 않습니다.
그 기록은 복구 수단일 수 있어 삭제에는 별도 판단이 필요합니다. 셋째, 검증자에게 명령 권한을 모두
빼앗아 실행 증거 없이 의견만 받지 않습니다. 대신 버릴 수 있는 복제본에서 제한된 검사만 실행하게
합니다.

판단이 틀리면 두 방향으로 깨집니다. 너무 느슨하면 다른 변경의 서버 검사 결과를 이번 결과로 잘못
세거나 원본이 검증 중 바뀔 수 있습니다. 너무 엄격하면 안전한 구현도 시작 단계에서 멈춥니다. 그래서
모든 중단은 이유와 다시 시작할 조건을 남기고, 삭제·강제 갱신·자동 합치기는 계속 금지합니다.

### 결정 카드

**무엇을** — 기존 v2 문서의 제품 계약은 유지하고 실행·검증·재개 경계 다섯 곳만 고칩니다.

**왜** — 제품 정답을 다시 설계할 필요는 없지만, 현재 절차로는 가짜 서버 합격과 원본 변경 가능성을
배제할 수 없기 때문입니다.

**버린 길** — 문서를 그대로 통과시키는 길과 저장소 기록을 자동 삭제하는 길을 버렸습니다. 전자는
검증 구멍을 남기고, 후자는 복구 가능한 자료를 되돌리기 어렵게 지웁니다.

**대가** — 실행 지시서가 더 길어지고, 기존 저장소 시작 검사가 빨간 상태면 제품 구현은 실제로
멈춥니다.

**되돌리기** — 수리가 과도하다고 확인되면 이번 문서 전용 변경 기록만 되돌리면 됩니다. 제품 코드와
운영 자료는 이번 범위에 없으므로 되돌림 비용은 문서 재검증입니다.

## 3층 — 계약·증거

### 1. 현재 상태

- 기준 작업 폴더: `worktrees/docs-snapshot`
- 기준 변경: `63da16c772cdce21d7a46a301fa818f99f7b6c99`
- 원격 요청: #15, 상태 `OPEN`, 병합 가능 상태 `clean`
- 선행 요청 #13, #14, #15: 현재 모두 아직 합쳐지지 않음
- 제품 코드·실제 사이트·로그인·후보자 자료: 실행 0회

`docs/sot/humansearch-l0-surface-contract.md:31-80`은 입력 세 개, 결과 다섯 개, 정상 입력 열여섯
조합을 정합니다. 이 줄들은 제품 분류의 정답을 정하는 부분이며 이번 수리에서 바꾸지 않습니다.

`docs/engineering/goal-prompts/codex-humansearch-l0-surface-classifier-v2-2026-08-16.md:263-271`은
새 작업 폴더에서 시작 검사를 실행하지만, 실패 수가 0이어야 한다는 다음 단계 조건을 적지 않았습니다.

`docs/engineering/goal-prompts/codex-humansearch-l0-surface-classifier-v2-2026-08-16.md:775-783`은
네 코드 지문을 비교한다고 쓰면서 실제로는 로컬·원격 가지·검토 요청 세 개만 읽고, 서버 실행 대상
지문을 읽지 않습니다.

`docs/engineering/goal-prompts/codex-humansearch-l0-surface-classifier-v2-2026-08-16.md:592-616`은
Claude에 파일 편집 도구는 막지만 제한 없는 Bash를 허용합니다. Bash로 파일·Git·원격을 바꿀 수
있으므로 말로만 읽기 전용이라고 한 상태입니다.

### 2. 시작 검사 재현

```text
$ bash scripts/session-status.sh
HEAD: 63da16c (ahead 2 / behind 1)
ORIGIN: 4fdef31
RED: 1/19 (acceptance-0-7.sh 제외 — CI 담당)
```

→ 문서 작업 가지에서 시작 검사를 끝까지 다시 실행했습니다. 열아홉 검사 중 하나가 실패하므로 현재
저장소는 새 제품 구현을 시작할 수 있는 상태가 아닙니다.

```text
$ SECRET_PATTERNS_FILE= bash scripts/acceptance-0-2.sh
FAIL: .secret-patterns 없음/빈 파일 — AC 판정 불가
```

→ 분리된 문서 작업 폴더에는 Git에 넣지 않는 실제 비밀 패턴 파일이 없어 검사가 실행 불가 성적 2로
끝났습니다. 실행 불가는 합격이 아닙니다.

```text
$ SECRET_PATTERNS_FILE= bash scripts/acceptance-0-2.sh
PASS: no secret-pattern match in any tracked file, .env not tracked
FAIL: unreachable 객체 8건 잔존 (reflog expire/gc --prune=now 미완)
```

→ 원본 작업 폴더에는 실제 패턴 파일이 있지만, 다시 살릴 수 있는 Git 기록 여덟 건이 남아 검사
성적 1로 끝났습니다. 이를 지우는 명령은 복구 자료를 없앨 수 있으므로 이번 작업에서 실행하지 않습니다.

### 3. 근본 원인

이전 검증은 문서의 설계 의미와 명령 존재 여부를 주로 확인했고, 시작 검사를 끝까지 기다리지
않았습니다. 그래서 실제 빨간 결과와 “실패하면 반드시 멈춘다”는 문장 부재가 함께 놓쳤습니다. 서버
검사도 결과 이름과 성공 여부만 확인했지, 그 검사가 현재 코드 지문을 대상으로 했는지까지 계약에
넣지 않았습니다. 읽기 전용 검증은 도구 이름만 막고 명령 실행의 실제 쓰기 능력을 제거하지 않았습니다.

### 4. 단일 인수 기준

**AC-L0-PROMPT-REPAIR-1:** 최종 v2 실행 지시서는 현재 화면 분류 계약을 바꾸지 않으면서, 시작 검사
실패·서버 검사 대상 불일치·검증자 원본 변경·불명확한 가지 재개·미저장 검증 기록 중 하나라도 있으면
제품 변경 없이 멈추고, 다섯 위험이 모두 해소된 경우에만 다음 단계로 진행하도록 명령과 판정 조건을
완전히 제시해야 합니다.

가짜 합격 모습은 다음과 같습니다.

- 시작 검사에 실패가 있어도 다음 단계로 넘어갑니다.
- 서버 검사 대상 코드 지문을 읽지 않고 이름과 성공 표시만 셉니다.
- 건너뛰거나 취소된 서버 검사를 합격으로 셉니다.
- Claude가 원본 작업 폴더에서 제한 없는 명령을 실행합니다.
- 가지는 있지만 작업 폴더가 없을 때 “예상한 변경”을 실행자가 추측합니다.
- 검증 기록이 아직 기록으로 고정되지 않은 정상 상태를 재개 규칙이 불법 변경으로 오인합니다.

### 5. Harness 게이트

- Gate 0: 현재 `RED: 1/19`. 자동 삭제로 닫지 않으며 최종 실행 지시서가 이 상태를 반드시 차단합니다.
- Gate 1: 이 문서의 단일 인수 기준으로 수리 범위를 고정합니다.
- Gate 2: 기존 `worktrees/docs-snapshot`과 PR #15를 재사용합니다. 새 가지·작업 폴더·검토 요청을
  중복 생성하지 않습니다.
- Gate 3: 문서 수리만 수행합니다. 제품 코드·시험·의존 파일은 변경하지 않습니다.
- Gate 4: 정본 대조, 저장소 검사, 형식 보조 검사, Claude V1, Codex V2, 서버 검사를 실행합니다.
- Gate 5: 기존 PR #15의 일반 업로드만 허용합니다. 합치기와 자동 합치기는 금지합니다.
- Gate 6: PR이 합쳐지지 않았으므로 종료 정리는 실행하지 않습니다.

### 6. 적대검증 정조준

1. 시작 검사 결과에서 실패 수를 실제로 읽고 0이 아니면 멈추는가.
2. 서버 실행 대상 지문과 로컬·원격·검토 요청 지문을 모두 비교하는가.
3. 관측된 서버 검사 중 성공이 아닌 모든 결과를 막는가.
4. 검증자는 버릴 수 있는 복제본에서만 명령을 실행하고 원본 전후 상태가 같은가.
5. 가지 전용 재개가 변경 기록의 단계·시도 번호·파일 범위를 기계적으로 검사하는가.
6. 아직 기록으로 고정되지 않은 goal 로그가 허용되는 시점과 재개 방법이 명확한가.
7. 기존 세 역할·다섯 결과·열여섯 조합과 제품 비범위가 그대로인가.

### 7. 실제로 읽은 정본과 규칙

- 사용자 제공 `AGENTS.md` 전체 본문
- `/Users/kangsangmo/.codex/skills/strict/SKILL.md`
- `/Users/kangsangmo/.claude/skills/harness/SKILL.md`
- `docs/sot/INDEX.md`
- `docs/sot/humansearch-l0-surface-contract.md`
- `docs/sot/verification-commands.md`
- `docs/sot/coding-principles.md`
- `docs/sot/git-workflow.md`
- `docs/sot/hook-contracts.md`

### 8. 비범위

- HumanSearch 제품 구현과 시험 추가
- 선행 PR #13, #14, #15 합치기
- 회수 가능한 Git 기록 삭제, 강제 정리, 가지 강제 갱신
- 실제 포털, 브라우저, 로그인, 세션, 자격증명, 후보자 개인정보
- 후보 등록·발송·배포·자동 합치기
- L2, L3, runner, C1 구현

### 9. 검증 로그

수리 뒤 로컬 검사, Claude V1 원문, Codex V2 재현표, 원격 서버 검사 결과를 아래에 원문으로
이어 붙입니다. 실행하지 못한 항목은 합격으로 바꾸지 않고 `NOT_RUN`으로 남깁니다.

### 10. 적대 검증 로그

#### 10.1 Claude V1 실행

첫 실행은 내용상 `VERDICT: PASS`였지만 `VERDICT:` 앞에 진행 문장 한 줄을 출력해 형식 위반으로
기각했습니다. 허용된 형식 재시도 1회를 다음 명령으로 실행했습니다. 원본 저장소가 아니라
`/var/folders/4h/jphmynjn2jl54cqy8d_ddhkh0000gn/T/humansearch-l0-doc-v1.Q8HLuQ/repo`의
일회용 clone에서만 실행했습니다.

```bash
env -u ANTHROPIC_API_KEY claude --safe-mode --no-session-persistence \
  --permission-mode dontAsk --tools Read,Grep,Bash \
  --allowedTools Read Grep \
    'Bash(git status --short*)' 'Bash(git rev-parse *)' 'Bash(git log *)' \
    'Bash(git show *)' 'Bash(git diff *)' 'Bash(git diff-tree *)' \
    'Bash(git ls-files *)' 'Bash(bash verify.sh)' \
    'Bash(bash scripts/check-docs-sot.sh)' \
    'Bash(bash scripts/acceptance-verify-ac-m.sh)' \
    'Bash(bash scripts/session-status.sh)' 'Bash(bash -n *)' \
    'Bash(sed -n *)' 'Bash(nl -ba *)' 'Bash(rg *)' 'Bash(grep *)' \
  --disallowedTools Edit Write NotebookEdit \
    'Bash(git add *)' 'Bash(git commit *)' 'Bash(git push *)' \
    'Bash(git checkout *)' 'Bash(git switch *)' 'Bash(git reset *)' \
    'Bash(git clean *)' 'Bash(git restore *)' 'Bash(git fetch *)' \
    'Bash(git pull *)' 'Bash(git merge *)' 'Bash(git rebase *)' \
    'Bash(git update-ref *)' 'Bash(gh *)' 'Bash(curl *)' \
    'Bash(rm *)' 'Bash(mv *)' 'Bash(cp *)' 'Bash(tee *)' \
    'Bash(touch *)' 'Bash(mkdir *)' 'Bash(sed -i *)' \
    'Bash(python *)' 'Bash(node *)' 'Bash(perl *)' \
  -p '이것은 같은 감사의 허용된 1회 형식 재시도입니다. 직전 답변은 내용상 PASS였으나 VERDICT 전에 진행 문장을 출력해 무효였습니다. 답변의 첫 바이트부터 정확히 `VERDICT: PASS` 또는 `VERDICT: FAIL`로 시작하십시오. 그 앞에 공백, 인사, 진행 설명, 메타 문장을 절대 쓰지 마십시오. 도구 사용 중 진행 메시지도 최종 답변에 포함하지 마십시오.

현재 clone의 아래 문서와 63da16c..HEAD diff를 다시 독립 확인하십시오: docs/engineering/humansearch-l0-v2-verification-repair-goal-2026-08-16.md, docs/engineering/goal-prompts/codex-humansearch-l0-surface-classifier-v2-2026-08-16.md, docs/sot/humansearch-l0-surface-contract.md, docs/sot/verification-commands.md, docs/sot/git-workflow.md, docs/sot/hook-contracts.md, scripts/session-status.sh. 공격축은 계약 3 roles/5 states/16 조합/fail-closed/L2-L3 분리, tombstone, Gate0의 RED·UNKNOWN·0/0·누락·접미사 차단, branch-only resume와 evidence buffer, Claude clone/권한/target 지문, CI의 run headSha와 push+pull_request 및 모든 관측 check, 금지 scope, goal 주장 정확성입니다. 원격 gh는 NOT_RUN으로 분리하십시오.

첫 줄 뒤에는 결론, 판단 근거, 기술 상세 순서로 쓰고, 모든 finding에 심각도·file:line·재현 근거·영향을 포함하십시오. 실행한 명령은 출력과 함께 보존하고 실행 못한 것은 NOT_RUN으로 쓰십시오. 직전 저심각 관측인 git 읽기 명령의 clone 내부 쓰기 가능성과 pytest의 clone 내부 코드 실행·네트워크 가능성도 숨기지 마십시오. 한국어 존칭체로 작성하십시오.'
```

→ 명령 표면은 Read/Grep와 명시한 Bash 규칙으로 제한했고, 원격 명령과 파일·Git 변경 명령은 다시
deny했습니다. 이 실행 뒤 target의 HEAD·전체 status·refs 지문은 모두 `yes`로 같았습니다.

Claude V1의 유효한 원문은 다음과 같습니다.

VERDICT: PASS

## 결론

63da16c..HEAD의 두 문서 변경(실행 프롬프트 v2 수리 + 수리 goal 신설)을 이 clone에서 독립 재확인한 결과, 공격축 전부에서 계약 위반이나 가짜 합격 경로를 찾지 못했습니다. Gate 0 정규식은 8종 적대 입력 중 정확한 `RED: 0/N` 한 줄만 통과시키는 것을 실제 실행으로 확인했고, 금지 scope(제품 코드·스크립트·CI·SoT) 변경은 0건이며, goal 문서가 인용한 구 판본 file:line 주장은 전부 63da16c 실물과 일치했습니다. 남은 것은 저심각 관측 3건과 이번 세션 권한 거부로 인한 NOT_RUN 항목들이며, 어느 것도 판정을 뒤집지 않습니다.

## 판단 근거

이번 감사에서 실행하지 못한 것을 먼저 밝힙니다. 이번 세션의 권한 모드가 저장소 스크립트 실행(`bash scripts/session-status.sh`, `acceptance-0-2.sh`)과 `gh` 호출(오프라인 `--help` 포함)을 거부했으므로, goal 문서의 시작 검사 재현 출력(`RED: 1/19`, unreachable 객체 8건)과 PR #13/#14/#15·#15 OPEN 상태 주장은 **NOT_RUN**입니다. 다만 이 clone에는 `origin/main` ref 자체가 없어(아래 증거) `session-status.sh`를 실행했더라도 원본 worktree의 수치를 재현할 수 없는 환경이었습니다. 판정은 (1) 문서·스크립트 원문 정독, (2) 저장소 코드 실행이 아닌 순수 셸(`printf`/`grep`)로 수행한 Gate 0 정규식 실증, (3) 63da16c 시점 파일과의 대조로 구성했습니다.

PASS로 판정한 이유는, 다섯 공격축(시작 검사, CI 대상 지문, 검증자 격리, branch-only 재개, evidence buffer)이 모두 "실패를 명시적 exit code로 닫는" 방향으로 수리됐고, 발견한 잔여 구멍이 전부 (a) 탐지 장치(지문 대조 exit 24)가 뒤에서 받치거나 (b) 과차단(fail-closed) 방향이기 때문입니다. 반대로 FAIL로 볼 근거였을 "가짜 합격이 가능한 경로"는 재현하지 못했습니다.

## 기술 상세

### 1. diff 범위와 금지 scope — 위반 0건

```
$ git diff --stat 63da16c..HEAD
 ...ansearch-l0-surface-classifier-v2-2026-08-16.md | 205 ++++++++++++++++++---
 ...ch-l0-v2-verification-repair-goal-2026-08-16.md | 172 +++++++++++++++++
 2 files changed, 349 insertions(+), 28 deletions(-)
```

→ 변경은 문서 2개뿐입니다. `humansearch/` 제품 코드, `scripts/`, `.github/workflows/`, `docs/sot/` 변경 0건으로, goal 문서의 Gate 3 주장("문서 수리만 수행")과 일치합니다.

### 2. 계약 축 — 3 roles / 5 states / 16 조합 / fail-closed / L2-L3 분리

`docs/sot/humansearch-l0-surface-contract.md:37-41`(role 정확히 3개), `:57-63`(state 정확히 5개), `:72-82`(2×8=16 조합 완전 결정표, role 우선순위 금지), `:50-53`(비-enum·비-bool 입력은 `InvalidObservation` — fail-closed), `:94-95`·`:130-137`(`transition`/`RECHECK`/`RUNNING`/`STOP`은 L2/L3/runner 소유). 프롬프트 §5 해석표(`:219-229`)와 §9 시험 형상(`:404-419`, 16+4+5=25개)이 계약과 모순 없이 일치합니다.

### 3. Gate 0 — RED·UNKNOWN·0/0·누락·접미사 차단 (실증)

프롬프트 `:268-279`의 판정 블록을 정독하고, 정규식을 순수 셸로 실증했습니다.

```
$ printf '%s\n' 'RED: 0/19 (acceptance-0-7.sh 제외 — CI 담당)' 'RED: 1/19 (…)' \
  'RED: 0/0 (…)' 'RED: UNKNOWN' 'RED: UNKNOWN (검사 스크립트 0개 — 탐색 실패)' \
  'RED: 0/19 (…) extra' 'RED: 00/19 (…)' 'RED: 0/19' \
  | grep -En '^RED: 0/[1-9][0-9]* \(acceptance-0-7\.sh 제외 — CI 담당\)$'
1:RED: 0/19 (acceptance-0-7.sh 제외 — CI 담당)
```

→ 8종 입력 중 정확한 형식의 실패 0건 줄만 통과했습니다. `RED: 1/19`, `0/0`, `UNKNOWN` 2종, 접미사 부가, `00/19`, 괄호 누락은 전부 불일치 → exit 23. `scripts/session-status.sh:52-55`(검사 0개 → `RED: UNKNOWN` + exit 1)와 `:14-15`(git 조회 실패 → UNKNOWN + exit 1)가 rc 검사(`:273`)에 걸리고, RED 줄 0개·2개 이상은 `red_line_count -ne 1`(`:272-273`)이 잡습니다. 우회 금지 문구(`.secret-patterns` 복사·객체 자동 삭제 금지)도 `:283-284`에 명시돼 있습니다.

### 4. branch-only 재개와 evidence buffer

`:255-258`(commit별 `git diff-tree` 파일 대조, 제목만 보고 통과 금지), `:310-321`(phase별 허용 파일 표 + 범위 밖·중복·trailer 누락 시 BLOCKED), `:323-333`(buffer 정의, 미커밋 허용 파일 goal 정확히 1개, 소실 시 재구성 금지·fresh 재실행). §11 `:548-568`이 attempt/RED SHA를 trailer로 기계 추출해 RED 불변을 diff로 강제합니다(0개·2개 이상 → exit 22).

### 5. Claude V1 — clone 격리·권한·target 지문

`:634-724`: `--no-local --no-hardlinks` clone + detach, target 절대 경로 미노출, `ANTHROPIC_API_KEY` 제거, allowlist는 읽기 git + 지정 검사만, denylist가 쓰기 git·`gh`·`curl`·파일 조작·인터프리터를 재차 차단, 실행 전후 HEAD/전체 status/ref 해시 3중 지문 불일치 시 판정 무관 exit 24, claude 실패 rc → exit 25. temp 정리 trap의 경로 가드(`:643-651`)도 안전합니다.

### 6. CI_WAIT — run headSha·push+pull_request·전 관측 check

`:894-904`(3자 SHA 불일치 → exit 26), `:916-926`(`gh run list --commit "$EXPECTED_SHA"` + `gh pr checks`), `:933-946`(모든 `headSha`=EXPECTED, push·pull_request 각 1건 이상 아니면 NOT_RUN, 관측 run 전부 completed+success, check 전부 bucket=pass, run/check 0개=NOT_RUN→BLOCKED, 45분 timeout). `.github/workflows/verify.yml:5-9`가 실제로 `push`(모든 branch)+`pull_request`를 트리거하므로 두 event 요구는 달성 가능한 조건입니다. §21 완료 판정(`:996-998`)과 상태표 `:104`의 HANDOFF 조건도 이와 정합합니다.

### 7. goal 주장 정확성 (63da16c 실물 대조)

- `git rev-parse 63da16c` → `63da16c772cdce21d7a46a301fa818f99f7b6c99` — goal의 기준 SHA와 일치.
- 구 판본 `:263-271` = 시작 검사 4줄 + 실패 조건 없는 해설 ✓, `:592-616` = `--allowedTools Read,Grep,Bash`(무제한 Bash) ✓, `:775-783` = "네 SHA를 비교한다"고 쓰고 3개만 읽음 ✓ — 세 인용 모두 `git show 63da16c:<file>` 실물과 일치.
- tombstone 2건(`codex-humansearch-autoloop-L0-2026-08-16.md`, `humansearch-L0-kickoff-2026-08-16.md`): 코드 블록 0개(grep 실증), 대체 문서·정본 지시, commit 보존 비약속 문구 확인 ✓.

### Finding — 저심각 관측 (판정 불변)

- **[LOW] Claude allowlist의 git 읽기 명령이 쓰기 능력을 보유** — `:670-674`의 `Bash(git log *)`/`Bash(git diff *)` 등은 `--output=<경로>` 옵션으로 파일 쓰기가 가능합니다. 재현 근거: git 자체 옵션 사양(이번 세션 실행은 권한 거부로 NOT_RUN ※). 영향: clone 내부 쓰기는 폐기로 무해하고 target 쓰기는 지문 대조(exit 24)가 탐지하지만, target·clone 밖 임의 경로 쓰기는 탐지 범위 밖입니다.
- **[LOW] pytest 경유 임의 코드 실행·네트워크** — `:675`의 `uv run … pytest *`는 clone 안의 conftest·테스트 코드를 그대로 실행하며 네트워크 차단이 없습니다. 영향: 피감사 코드가 감사 중 실행되는 구조적 잔여 위험이나, 오염은 clone에 국한되고 target 지문 대조가 원본 변조를 잡습니다.
- **[LOW] EVIDENCE 준비 구간의 buffer 정의 공백** — `:323`은 buffer 창을 "PLAN 뒤 ~ REVIEW 직전"으로 한정하는데, REVIEW commit 후 EVIDENCE append 중 재개하면 goal+next prompt dirty가 창 밖이 됩니다. 영향: 오독 시 BLOCKED(과차단) 방향이라 가짜 합격이 아닌 중단으로 귀결됩니다.

### NOT_RUN 목록

- `bash scripts/session-status.sh`·`acceptance-0-2.sh` 재현 실행 — 이번 세션 권한 모드가 저장소 스크립트 실행을 거부. 또한 이 clone은 `git remote -v` 결과 origin이 `worktrees/docs-snapshot`이고 ref가 `task/docs-snapshot` 하나뿐(`git for-each-ref` 실증)이라 `origin/main` 부재로 원본 수치 재현이 애초에 불가능했습니다.
- `gh` 전부(PR #13/#14/#15 병합 상태, #15 OPEN·clean, `gh run list --commit`·`gh pr checks --json event,workflow` 플래그 존재 확인) — 원격 및 로컬 help 호출 모두 거부 ※.
- linked worktree를 `git clone`할 때 `origin/main` ref가 clone에 생기는지의 실증 — worktree 생성이 필요한 쓰기 작업이라 미실행 ※ (통상 git 동작상 source의 로컬 main이 복제된다고 추정).
- goal §7이 읽었다는 `AGENTS.md`·`~/.codex`·`~/.claude` skill 파일 본문 — 저장소 밖이라 미검증 ※.
CLAUDE_RC=0
TARGET_HEAD_UNCHANGED=yes
TARGET_STATUS_UNCHANGED=yes
TARGET_REFS_UNCHANGED=yes

→ Claude는 최종 PASS를 냈지만 저심각 관측 3건을 남겼습니다. Codex V2는 PASS라는 결론을 그대로
받지 않고 세 항목 전부와 Claude가 실행하지 못한 clone의 `origin/main` 조건을 다시 공격했습니다.

#### 10.2 Codex V2 재현·조치

| ID | Claude 판정 | Codex 재현 명령 | 재현 결과 | SOT/AC 대조 | 최종 조치 |
|---|---|---|---|---|---|
| V1-1 | LOW: `git *`가 `--output` 쓰기 가능 | `git help log`, `git help diff`에서 `--output` 검색 | 일치 | target 격리만으로 clone 밖 쓰기를 예방하지 못함 | exact Git 명령 + native sandbox로 수정 |
| V1-2 | LOW: pytest 임의 코드·network | no-network sandbox에서 fresh `uv`와 `curl` 반례 | 일치 | network 없는 test 실행과 사전 dependency 준비 필요 | pre-sync + offline `uv` + native sandbox로 수정 |
| V1-3 | LOW: REVIEW 뒤 EVIDENCE buffer 공백 | prompt `323-333` fresh line 대조 | 일치 | 재개가 안전해도 과차단 가능 | buffer 창을 EVIDENCE commit 직전까지 확장 |
| V2-1 | Claude NOT_RUN: clone의 `origin/main` 불명확 | 일회용 clone의 refs와 source ref를 대조 | 위험 확인 | stale local `main`을 base로 세면 diff 증거가 틀릴 수 있음 | source `origin/main` SHA를 clone ref에 명시 주입·대조 |

→ Claude finding 3건은 모두 재현됐고 숨기거나 기각한 항목은 0건입니다. Codex는 추가로 clone의 기준
ref가 source local `main`에 의존할 수 있는 반례를 찾아 같은 수정 묶음에 포함했습니다.

```text
$ git help log | col -b | rg -n -- '--output'
1690:       --output=<file>
1693:       --output-indicator-new=<char>, --output-indicator-old=<char>,
1694:       --output-indicator-context=<char>

$ git help diff | col -b | rg -n -- '--output|external-diff|textconv'
112:       --output=<file>
115:       --output-indicator-new=<char>, --output-indicator-old=<char>,
116:       --output-indicator-context=<char>
602:       textconv filter will be ignored.
725:       --textconv, --no-textconv
728:       textconv filters are typically a one-way conversion, the resulting
730:       this reason, textconv filters are enabled by default only for git-
1421:       diff.<driver>.textconv
1431:       diff.<driver>.cachetextconv
```

→ Claude의 첫 finding은 실제 Git option으로 재현됐습니다. wildcard를 없애고 diff에는
`--no-ext-diff --no-textconv`와 고정 파일 목록을 넣었습니다.

```text
$ sandbox-exec -n no-network env -i ... uv run --project humansearch pytest -q humansearch/tests/test_package_boundary.py
Using CPython 3.14.1 interpreter at: /opt/homebrew/opt/python@3.14/bin/python3.14
Creating virtual environment at: humansearch/.venv
  × Failed to download `typing-extensions==4.16.0`
  ├─▶ Request failed after 3 retries in 6.2s
  ├─▶ Failed to fetch:
  │   `https://files.pythonhosted.org/packages/49/d3/b8441a820a491ddfc024b0b0cf0393375b75ea13866d9c66727e54c2fc80/typing_extensions-4.16.0-py3-none-any.whl`
  ├─▶ error sending request for url
  │   (https://files.pythonhosted.org/packages/49/d3/b8441a820a491ddfc024b0b0cf0393375b75ea13866d9c66727e54c2fc80/typing_extensions-4.16.0-py3-none-any.whl)
  ├─▶ client error (Connect)
  ├─▶ dns error
  ╰─▶ failed to lookup address information: nodename nor servname provided, or
      not known
EXIT=1

$ uv sync --project humansearch --frozen
Installed 12 packages in 67ms

$ sandbox-exec -n no-network env -i ... UV_OFFLINE=1 uv run --project humansearch --offline pytest -q humansearch/tests/test_package_boundary.py
.                                                                        [100%]
1 passed in 0.01s
EXIT=0
```

→ network를 먼저 닫으면 fresh clone의 dependency 준비가 실패한다는 반례를 재현했습니다. 그래서
Claude 실행 전 trusted parent 단계에서 lockfile대로 sync한 뒤, Claude test는 offline으로 고정했습니다.

```text
NATIVE_SANDBOX_TEST: PASS

.                                                                        [100%]
1 passed in 0.00s

NETWORK_SANDBOX: BLOCKED

curl: (56) CONNECT tunnel failed, response 403
HTTP/1.1 403 Forbidden
Content-Type: text/plain
X-Proxy-Error: blocked-by-allowlist

<sandbox_violations>
deny network-outbound example.com:443 (user denied)
</sandbox_violations>
```

→ 실제 Claude native sandbox 설정에서 exact pytest는 통과했고 외부 network는 403으로 차단됐습니다.
`failIfUnavailable=true`와 `allowUnsandboxedCommands=false`도 넣어 sandbox 없는 조용한 실행을 막았습니다.

#### 10.3 수리 뒤 Claude V1 재검증과 Codex V2 재공격

`c701a3340e950f1f8155bc390dd4716e81c8cf5b`를 다음 일회용 clone에서 다시 검사했습니다.

```text
/var/folders/4h/jphmynjn2jl54cqy8d_ddhkh0000gn/T/humansearch-l0-doc-final.hrGgmU/repo
```

→ 원본 worktree가 아니라 폐기 가능한 clone 경로에서 읽기 전용 검증을 실행했습니다.

Claude의 유효 판정 첫 줄과 target 불변 증거는 다음과 같습니다.

```text
VERDICT: PASS
CLAUDE_RC=0
TARGET_HEAD_UNCHANGED=yes
TARGET_STATUS_UNCHANGED=yes
TARGET_REFS_UNCHANGED=yes
```

→ 원본 target의 commit, working tree, ref는 바뀌지 않았습니다. 다만 PASS 안에 저심각 finding과
`NOT_RUN`이 남아 있었으므로 완료로 세지 않고 Codex가 전부 다시 공격했습니다.

| ID | Claude 판정 | Codex 재현 | 결과 | 조치 |
|---|---|---|---|---|
| V1F-1 | LOW: 최종 V1/V2 증거 미완료 | 이 문서의 마지막 닫힌 단계와 commit을 대조 | 일치 | 새 commit에서 V1과 V2를 다시 실행하고 원문을 append |
| V1F-2 | LOW: REVIEW 전 dirty 규칙이 활성 RED/GREEN 파일까지 막음 | prompt의 evidence buffer 문장과 phase 허용 표 대조 | 일치 | open phase 표식과 RED/GREEN별 dirty 허용 범위를 명시 |
| V1F-3 | LOW: sandbox 기본 `TMPDIR`가 clone 밖이라 `mktemp` 검사 실패 | Claude 출력의 `Operation not permitted`와 기본 `/var/folders/...` 경로 대조 | 일치 | clone 안 `.audit-tmp`를 만들고 Claude 환경의 `TMPDIR`로 고정 |
| V1F-4 | 제한: 상세 diff 허용 파일만 보여 범위 밖 변경을 독립 확인하지 못함 | exact allowlist와 `origin/main...HEAD` 전체 name-status 부재 대조 | 일치 | option wildcard 없는 전체 경로 name-status 명령을 추가 |
| V1F-5 | 제한: portal constant script 실제 8개를 Claude가 못 셈 | 아래 `git ls-tree`로 원격 branch를 독립 조회 | 정확히 8개 일치 | 예상 목록을 유지하고 다음 V1에서도 preparation gate로 재검사 |

→ Claude가 남긴 항목을 Codex가 하나씩 재현했고, 미완료 1건은 다음 검증으로 넘기며 나머지는 문서
수리 또는 독립 조회로 닫았습니다.

```text
$ git ls-tree -r --name-only origin/task/humansearch-g3-portal-constants -- scripts \
  | LC_ALL=C sort | grep '^scripts/acceptance-hs-portal-constants.*\.sh$'
scripts/acceptance-hs-portal-constants-hardening.sh
scripts/acceptance-hs-portal-constants-hardening2.sh
scripts/acceptance-hs-portal-constants-hardening3.sh
scripts/acceptance-hs-portal-constants-hardening4.sh
scripts/acceptance-hs-portal-constants-hardening5.sh
scripts/acceptance-hs-portal-constants-hardening6.sh
scripts/acceptance-hs-portal-constants-mutations.sh
scripts/acceptance-hs-portal-constants.sh
```

→ finding 5건을 숨기거나 기각하지 않았습니다. V1F-2~4는 프롬프트 수리로 닫았고, V1F-1은 이
수리 commit 뒤의 새 Claude V1과 Codex V2 증거가 생겨야만 닫힙니다. V1F-3 때문에 Claude sandbox
안에서 실행되지 못했던 `verify.sh`와 `acceptance-verify-ac-m.sh`는 아직 `NOT_RUN`이며, 다음 V1에서
실제 성공 출력이 나오기 전에는 완료로 바꾸지 않습니다.

#### 10.4 최종 Claude V1 시도 1 기각

`4627ddb60091b2db0df9814acbfcdacb8a149e09`를
`/var/folders/4h/jphmynjn2jl54cqy8d_ddhkh0000gn/T/humansearch-l0-doc-v1-final.noatLV/repo`에서
검사한 Claude는 첫 줄 `VERDICT: PASS`와 target 불변 3건을 냈습니다. 그러나 성공의 필수 조건으로
정한 두 검사가 다음처럼 끝났습니다.

```text
$ bash verify.sh                          (exit 1)
mktemp: mkstemp failed on /var/folders/4h/.../T/tmp.qZCSSn3pWC: Operation not permitted
mktemp: mkstemp failed on /var/folders/4h/.../T/tmp.FELLwGO5cW: Operation not permitted

$ bash scripts/acceptance-verify-ac-m.sh  (exit 2)
mktemp: mkdtemp failed on /var/folders/4h/.../T/tmp.fDWI9Q0sC4: Operation not permitted
NOT_RUN: mktemp 실패
CHECKED: 0
```

→ 상위 `claude` process에 준 `TMPDIR`가 Claude의 Bash 명령에는 보존되지 않았습니다. 따라서 PASS라는
문구와 관계없이 이 시도는 기각했습니다. 원본 target의 HEAD·전체 status·refs 지문은 모두 `yes`로
불변이었습니다.

Claude가 추가한 저심각 finding도 Codex가 재현했습니다.

| ID | Claude 판정 | Codex 재현 | 최종 조치 |
|---|---|---|---|
| V1FF-1 | LOW: Claude mypy가 구현자보다 약함 | Claude allowlist의 `mypy humansearch/src`와 LOCAL_VERIFY의 `mypy --strict src tests` 대조 | exact 명령을 `--strict humansearch/src humansearch/tests`로 일치시킴 |
| V1FF-2 | LOW: bare `mktemp`가 제한된 임시 경로에서 실패 | 위 `verify.sh`·AC-M 실제 출력으로 재현 | 각 허용 검사 명령 자체에 clone 내부 `TMPDIR`를 inline 고정 |

→ 두 finding 모두 받아들였고 기각해 숨긴 finding은 0건입니다. 다음 V1에서 inline `TMPDIR`로 두 검사가
실제 성공하기 전까지 V1F-1은 미완료입니다.

#### 10.5 inline 환경 재시도 실패와 wrapper 결정

`d06a4db5244018dff070511b87e6671d31c1b9eb`의 inline `TMPDIR` 수리를 같은 native sandbox에서
다시 실행한 결과 Claude의 판정은 `VERDICT: FAIL`이었습니다.

```text
$ TMPDIR="$PWD/.audit-tmp" bash verify.sh
mktemp: mkstemp failed on /var/folders/4h/.../T/tmp.CH1J8rCLIF: Operation not permitted
exit 1

$ TMPDIR="$PWD/.audit-tmp" bash scripts/acceptance-verify-ac-m.sh
mktemp: mkdtemp failed on /var/folders/4h/.../T/tmp.4an7dx0D0N: Operation not permitted
NOT_RUN: mktemp 실패
CHECKED: 0
exit 2
```

→ Claude가 명령을 시작하는 경계에서 inline 환경까지 덮으므로 V1P-1을 재현했습니다. `env -i`를
exact allowlist에 넣은 smoke도 Claude 권한 matcher가 실행을 거부해 `SMOKE: FAIL`·두 명령
`NOT_RUN`으로 끝났습니다. 두 실패를 합격으로 바꾸지 않았습니다.

Codex V2는 환경 전달에 더는 의존하지 않고, Claude가 허용된 `bash <tracked-file> <fixed-id>`를 시작한
뒤 그 파일 본문에서 clone 내부 환경을 export하는 전용 wrapper를 선택했습니다. wrapper는 임의 명령
인자를 받지 않고 고정 ID 외에는 exit 64, clone 내부 audit 디렉터리가 없으면 exit 66으로 닫힙니다.
제품 source·test·dependency는 바꾸지 않습니다. 다음 Claude smoke에서 wrapper 경로로 `verify.sh`와
AC-M 25가 실제 성공하기 전에는 이 결정도 완료로 세지 않습니다.

첫 wrapper smoke는 두 exact 명령이 allowlist를 통과했지만, wrapper의 첫 `git rev-parse`가 native
sandbox에서 실패해 둘 다 `BLOCKED: not inside a Git worktree`, exit 65로 끝났습니다. 이 실패도
`SMOKE: FAIL`로 보존했습니다. Claude의 현재 디렉터리는 이미 parent가 clone root로 고정하므로 wrapper의
중복 Git 탐지를 제거하고, 현재 디렉터리에 `verify.sh`, L0 SOT, wrapper 자신이 모두 있는지를 sentinel로
검사하도록 바꿨습니다. 다음 smoke에서 자식 검사들의 실제 Git 사용까지 통과해야만 수리로 인정합니다.

두 번째 wrapper smoke도 `verify` exit 1, AC-M exit 2·`CHECKED: 0`으로 실패했습니다. wrapper 안에서
export한 환경도 sandbox가 자식 process를 만들 때 다시 덮으므로 환경 전달과 wrapper 방식 모두
기각했습니다. 실패한 wrapper는 최종 diff에서 삭제했습니다.

Claude 공식 sandbox 문서의 임시 디렉터리 계약과 `sandbox.filesystem.allowWrite` 권장 방식을 적용해,
native sandbox가 실제 사용하는 OS 임시 디렉터리를 쓰기 허용하고 home 읽기·network·unsandboxed
escape는 계속 닫는 direct-command smoke를 실행했습니다. 첫 smoke는 `verify.sh`는 성공했지만 Git의
home config 탐색이 막혀 AC-M이 `NOT_RUN: git 저장소가 아니다`로 실패했습니다. 기존 하네스처럼
`GIT_CONFIG_GLOBAL=/dev/null`, `GIT_CONFIG_SYSTEM=/dev/null`을 상위 환경에 고정한 두 번째 smoke 결과는
다음과 같습니다.

```text
SMOKE: PASS
bash verify.sh -> exit 0
PASS: no secret-pattern match in any tracked file, .env not tracked
bash scripts/acceptance-verify-ac-m.sh -> exit 0
CHECKED: 25
```

→ 두 exact 명령을 각각 한 번 실행했고 필수 로컬 검사 둘이 처음으로 native sandbox 안에서 실제
성공했습니다. 따라서 최종 하네스는 실패한 wrapper를 쓰지 않고, exact Bash allowlist + OS 임시 경로
`allowWrite` + Git config 차단 조합을 사용합니다. 이 설정으로 전체 최종 V1을 다시 실행하기 전에는
아직 완료로 세지 않습니다.

#### 10.6 최종 Claude V1 유효 판정

`a5ca9726f58e0deb5c3b9bbf956792f3f817ed41`을 다음 일회용 clone에서 검사했습니다.

```text
AUDIT_REPO=/var/folders/4h/jphmynjn2jl54cqy8d_ddhkh0000gn/T/humansearch-l0-doc-v1-accepted.mGd8JC/repo
CLAUDE_RC=0
VERDICT: PASS

# 1) 결론

a5ca972의 문서 하네스는 현재 상태로 배송해도 됩니다. 요구된 검증 축 전부(3 roles/5 states/16조합/fail-closed/L2-L3 분리, tombstone, Gate0 exact RED 차단, branch-only checkpoint와 evidence buffer, origin/main 주입, 전 범위 diff, exact Bash allowlist, sandbox allowWrite 경계, target 지문, CI 규칙, 금지 scope)을 원문과 diff로 대조했고, 계약 모순·검증 우회·권한 확장·증거 과장을 찾지 못했습니다. 이전 실패 4종(상위 TMPDIR, inline TMPDIR, env -i, wrapper)은 최종 diff에서 실제로 제거됐고, 공식 allowWrite direct command 방식이 그 자리를 대체했음을 commit 단위로 확인했습니다. 필수 검사 3종을 직접 실행해 verify.sh exit 0, docs SOT exit 0, AC-M exit 0에 CHECKED: 25를 모두 얻었습니다.

session-status는 RED: 4/19를 보고했으며 이를 성공으로 바꾸지 않습니다. 이 빨간 상태는 결함이 아니라 v2 지시서의 Gate 0이 차단하도록 설계된 바로 그 상황입니다.

NOT_RUN: gh 원격 조회, RED 4/19 중 acceptance-0-2 외 3건의 개별 식별, home의 brief-lint. 원격과 home은 sandbox 경계로 차단했습니다.

# 2) 판단 근거

origin/main..HEAD 전체 변경 경로를 먼저 확인한 뒤 수리 commit 체인과 상세 diff를 읽었습니다. 필수 로컬 검사와 wrapper 삭제, allowlist 교체는 실측과 일치했습니다. RED라는 이유만으로 FAIL로 바꾸지 않은 이유는 Gate 0이 정확히 그 상태를 exit 23으로 차단하기 때문입니다. OS 임시 루트 allowWrite는 exact Bash, home 읽기 차단, network 0, target 지문 대조가 함께 남고 좁은 대안 4종이 모두 실증 실패했으므로 낮음 관찰로 남겼습니다.

# 3) 낮음 관찰

1. [낮음] allowWrite가 OS 임시 루트 전체입니다. exact Bash allowlist와 network 0으로 실질 위험은 낮고, 좁은 대안 4종의 실패 뒤 선택했습니다.
2. [낮음] 수리 goal의 중간 판본 문구 `--strict humansearch/src humansearch/tests`와 최종 allowlist `cd humansearch && uv run --offline mypy --strict src tests`의 문자열은 다르지만 이력 보존이고 엄격도는 같습니다.
3. [정보] clone은 RED 4/19, 원본 worktree 기록은 RED 1/19입니다. Gate 0 해소 전에는 구현이 BLOCKED됩니다.

# 4) 실행 출력

$ bash verify.sh -> exit 0
PASS: no secret-pattern match in any tracked file, .env not tracked

$ bash scripts/check-docs-sot.sh -> exit 0
OK: docs/sot 재구성 AC 전부 충족

$ bash scripts/acceptance-verify-ac-m.sh -> exit 0
CHECKED: 25

$ bash scripts/session-status.sh -> exit 0
HEAD: a5ca972 (ahead 10 / behind 1)
ORIGIN: 4fdef31
RED: 4/19 (acceptance-0-7.sh 제외 — CI 담당)

TARGET_HEAD_UNCHANGED=yes
TARGET_STATUS_UNCHANGED=yes
TARGET_REFS_UNCHANGED=yes
```

→ 첫 줄 형식, 필수 로컬 검사 3종, 빨간 상태의 비합격 처리, target 불변 3종이 모두 충족돼 이 V1을
유효 판정으로 채택했습니다. 원격 조회와 home helper는 실행하지 않은 것으로 그대로 남겼습니다.

#### 10.7 최종 Codex V2 재현·재공격

| ID | Claude 관찰 | Codex 재현 | 판정 |
|---|---|---|---|
| FINAL-1 | OS 임시 루트 `allowWrite`가 전용 하위 경로보다 넓음 | native sandbox에서 좁은 상위·inline TMPDIR, `env -i`, wrapper 실패와 공식 `allowWrite` direct smoke 성공을 대조 | 재현·수용. exact 명령, home/network 차단, target 지문을 함께 유지하는 의도적 대가 |
| FINAL-2 | 중간 mypy 수리 문구와 최종 exact 문자열이 다름 | goal 452행과 prompt의 최종 allowlist를 직접 대조 | 재현·수용. 중간 finding의 당시 조치 기록이며 최종 명령은 구현자와 같은 cwd·strict·src·tests |
| FINAL-3 | clone RED 4/19, target RED 1/19 | target에서 `bash scripts/session-status.sh`를 fresh 실행 | 재현. target은 `RED: 1/19`; 둘 다 Gate 0 exact 정규식에 불일치해 제품 변경 없이 BLOCKED |
| FINAL-4 | final diff의 제품·script·CI 변경 net 0 | `git diff --name-status origin/main...HEAD -- humansearch scripts .github contracts hooks suppressions.yaml verify.sh` | 출력 0줄. transient wrapper는 최종 diff에서 삭제됨 |
| FINAL-5 | Gate 0 적대 입력은 정확한 한 줄만 통과 | 8개 입력을 같은 `grep -E` 정규식으로 실행 | 정확한 `RED: 0/19 (...)` 1개만 match |
| FINAL-6 | 필수 로컬 검사 성공 | target에서 verify, docs SOT, AC-M을 재실행 | exit 0, exit 0, exit 0·`CHECKED: 25` |

→ Claude finding 2건은 모두 Codex가 재현했고 숨기거나 기각한 finding은 0건입니다. 두 항목은 가짜
합격이 아니라 명시된 대가·이력 차이이므로 수리 loop를 더 열지 않았습니다. 제품 변경을 막아야 하는
현재 Gate 0 빨간 상태도 fresh target 출력으로 다시 확인했습니다.
