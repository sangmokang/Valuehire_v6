# AI-native RA 기획 패킷 최신 기준 결합 — Claude V1 원문

## 결론

Claude는 기획 문서 결합 자체에는 결함이 없다고 확인했지만, 작업 도중 공식 기준이 이동했으므로 이번 작업을 완료로 인정할 수 없다고 판정했습니다. 미해결 차단은 1건이며 최신 기준에서 전체 검증을 다시 해야 합니다.

## 판단 근거

첫 호출은 Claude의 안전 필터가 요청을 오인해 파일이나 명령을 검사하기 전에 종료됐으므로 검증으로 세지 않았습니다. 두 번째 호출은 Sonnet 안전 모드에서 실제 결합 작업공간을 직접 읽고 필수 명령을 실행했으며, 시작 기준 `0f8541e…`와 현재 기준 `34e4ccf…`의 차이를 재현했습니다.

## 실행자와 명령

- 실행자: Claude Code Sonnet, `--safe-mode`, 쓰기·원격 접근 금지, 읽기 도구와 로컬 Bash만 허용.
- 실행 위치: `/Users/kangsangmo/Desktop/Valuehire_v6-wt-ai-native-ra-revalidate-20260818`
- 첫 호출 결과: 안전 필터 거부, 성적 1, 검증 미실행.
- 두 번째 호출 결과: `VERDICT: FAIL`, 성적 0, 판정 본문 확보.

```bash
env -u ANTHROPIC_API_KEY claude --model sonnet --safe-mode --strict-mcp-config --mcp-config '{"mcpServers":{}}' --disable-slash-commands --no-chrome --no-session-persistence --permission-mode bypassPermissions --tools Read,Grep,Glob,Bash -p '<아래 실행 프롬프트 원문 전체>'
```

→ 인증 키를 환경에서 제거하고 Claude의 저장소 쓰기·원격 접근을 금지한 채, 아래 프롬프트 전문을 전달해 실제 작업공간을 읽고 검사하게 한 명령입니다.

## 실행 프롬프트 원문

<!-- lint:skip -->
````text
현재 디렉터리의 AI-native RA 기획 문서 결합 상태를 읽기 전용으로 품질 감사하십시오. 이전 보고를 신뢰하지 말고 실제 파일과 명령 결과를 직접 확인하십시오. 저장소 파일 수정, commit, fetch, push, PR, merge, rebase, 외부 네트워크 접근은 금지합니다. 임시 fixture 안에서만 반대 시험용 파일 변경이 가능합니다. .secret-patterns의 내용은 읽거나 출력하지 마십시오.

작업 디렉터리: /Users/kangsangmo/Desktop/Valuehire_v6-wt-ai-native-ra-revalidate-20260818

직접 확인할 기준:
- 시작 main/origin/main: 0f8541ef7f56fdf43f12f90c81ec4bd1b0233711
- 목표 문서 선행 commit: 0e34b892fdf21f9a03a61dc913a8931a86f0159e
- 원본 기획 commit: 39a3c5302cb29c2cd25147c4f4a5880e804cfb70
- cherry-pick 결과: f8e031b7f5d13b4bd72e30d5240e1ff3d5e2983c
- 검증 중 main/origin/main이 34e4ccff88ce776d06e3001734005a34b169f7eb로 이동한 정황이 있습니다. 시작 SHA 불변 조건 위반인지 직접 확인하십시오.

반드시 직접 읽을 파일:
docs/engineering/ai-native-ra-planning-packet-main-integration-revalidation-goal-2026-08-18.md
docs/engineering/ai-native-ra-search-orchestration-goal-2026-08-17.md
docs/engineering/ai-native-ra-search-orchestration-plan-2026-08-17.md
docs/engineering/goal-prompts/ai-native-ra-search-orchestration/README.md
docs/engineering/goal-prompts/ai-native-ra-search-orchestration/p00a-data-ownership-owner-decision.md
docs/engineering/ai-native-ra-p00a-ownership-contract-repair-goal-2026-08-18.md
docs/sot/INDEX.md
docs/sot/coding-principles.md
docs/sot/git-workflow.md
docs/sot/hook-contracts.md
docs/sot/verification-commands.md
.github/workflows/verify.yml

직접 실행할 확인:
1. pwd, git status --short --branch, git log --oneline -4, git rev-parse HEAD HEAD^ HEAD^^ main origin/main.
2. 39a3c530과 f8e031b의 stable patch-id 및 파일 목록 비교.
3. git diff --check, git diff 0f8541e..HEAD --check, 추적 파일의 git conflict marker 검색.
4. AC-PLAN-1 원문 명령을 직접 실행하여 prompts=28, required_sections=11, atomic_commands=28, p00a_owned_artifacts=3, links=all-present, exit 0 확인.
5. mktemp 임시 사본에 필요한 문서만 복제하고 P00A 작업 소유 범위의 scripts/acceptance-ai-ra-p00a.sh 한 줄만 제거한 뒤 같은 AC-PLAN-1이 0이 아닌 값인지 확인.
6. P00A 작업 소유 범위가 정확히 세 산출물만 갖는지 절 경계로 확인.
7. 28개 p*.md의 작업 소유 범위, 원자적 인수 기준, 공통 strict 실행 지시를 모두 읽는 기존 감사 명령을 직접 실행하여 28/27/27/2가 재현되는지 확인. 수정하지 마십시오.
8. VERIFY_SCAN_SOURCE=index bash verify.sh, bash scripts/acceptance-hs-gates.sh, bash scripts/acceptance-0-2-unreachable-content.sh, bash scripts/session-status.sh 실행 결과를 직접 확인.
9. verification-commands.md의 17단계와 verify.yml의 17단계를 대조. task branch에서 main-only 조건인 acceptance-0-5가 실행 제외되는 것이 정본대로인지, 그 상태를 전체 17단계 통과라고 표현해도 되는지 판단.
10. 목표 문서보다 기획 패킷이 뒤에 기록됐는지, P00A 실제 오너 결정이나 HumanSearch 제품 구현이 추가되지 않았는지, worktree가 깨끗한지 확인.
11. 새 worktree에서 .secret-patterns가 없어 acceptance-0-2.sh가 exit 2였고, 기존 main worktree의 무시된 같은 파일을 내용 노출 없이 symlink한 뒤 acceptance-0-2.sh PASS와 session-status RED 0/20으로 복구됐다는 설명을 파일 존재·symlink 여부·명령 결과만으로 확인. 민감 내용은 열지 마십시오.
12. 시작 main SHA가 현재 main/origin/main과 다르면 unresolved BLOCKER로 세고 최신 main 재검증 필요를 결론에 적으십시오.

결함은 실제 명령이나 file:line으로 재현된 것만 세십시오. 각 결함에 심각도, 그대로 두면 생기는 사업 영향, 미해결 여부를 적고 unresolved BLOCKER 수를 명시하십시오. 첫 줄은 정확히 VERDICT: PASS 또는 VERDICT: FAIL입니다.

[출력 형식 — 반드시 지킬 것]
읽는 사람은 기술 배경이 없는 사업 책임자다. 판정 내용은 절대 축소하지 말고, 표현만 풀어 써라.
1) 문서 맨 앞에 "결론". 결정할 사항 1개당 1~2문장, 전체 분량 상한 없음. 전문용어는 풀어 쓰더라도 결론에서는 쓰지 마라.
2) 그다음 "판단 근거": 왜 그렇게 봤는지, 갈림길에서 왜 이 해석을 골랐는지, 버린 해석은 왜 버렸는지, 이 판정이 틀리면 무엇이 깨지는지.
3) 그다음부터 기술 상세·명령·출력·file:line 전문. 증거는 하나도 생략하지 마라.
- 전문용어는 첫 등장 문장 안에서 괄호로 풀어 써라. 뒤에 몰아 쓴 용어집은 무효다.
- 터미널 출력·코드 블록·표를 붙였으면 바로 아래에 "→ 뭘 시켰나 / 뭐가 나왔나 / 좋은 소식인가 나쁜 소식인가" 1~3줄을 달아라.
- 첫 줄에 VERDICT: PASS|FAIL 한 줄을 두어라. 그 한 줄은 결론의 일부가 아니라 기계가 읽는 표식이므로 결론 제목 앞에 온다.
- file:line 을 인용하면 그 줄이 무슨 일을 하는 줄인지 한 마디 덧붙여라.
- 결함마다 심각도 라벨을 붙이고, 그 옆에 그대로 두면 사업/운영에 무슨 일이 생기는지 한 문장으로 덧붙여라.
- 설계 결정을 지적할 때는 "무엇을 / 왜 / 버린 대안 / 대가 / 되돌리는 법" 5줄로 적어라.
- 이번에 건너뛴 것·확인하지 못한 것·중간에 실패해서 다시 한 것을 판정 앞부분에 명시해라.
- 추정과 확인된 사실을 구분 표시해라.
- 한국어 존칭체. 초등학생용 비유는 쓰지 마라.
````

→ 실제 작업공간과 파일·명령을 직접 읽게 했고, 시작 기준 이동을 발견하면 반드시 차단으로 판정하도록 한 프롬프트 전문입니다.

## Claude V1 판정 원문

<!-- lint:skip -->
````text
VERDICT: FAIL

# 결론

1. 문서 내용 자체(기획 패킷, P00A 소유권 계약, 반대 시험, 28개 실행 프롬프트 감사)는 이번 감사에서 실행한 모든 검사를 실제로 통과했습니다. 문서를 옮겨 붙이는 과정에서 내용이 깨지거나 누락된 흔적은 없습니다.

2. 다만 이 작업이 "완료됐다"고 인정하려면 반드시 지켜야 한다고 스스로 정한 조건 하나가 지금 깨져 있습니다. 이 작업을 시작할 때 "여기서부터 시작한다"고 못 박은 공식 저장소의 기준 지점이, 작업 도중 이 작업과 무관한 다른 작업 때문에 한 걸음 더 앞으로 이동했습니다. 문서 내용끼리는 겹치지 않아 당장 파일이 깨지는 위험은 낮지만, "시작할 때 고정한 기준이 끝날 때까지 그대로여야 한다"는 이번 작업 고유의 완료 조건은 지금 충족되지 않습니다.

3. 따라서 지금 이 상태를 "결합 완료, 병합 가능"으로 확정해서는 안 됩니다. 최신 공식 기준을 다시 받아 그 위에서 전체 점검을 한 번 더 돌린 뒤에 완료를 선언해야 합니다. 이것이 이번 감사에서 확정한 유일한 미해결 차단 사유(1건)입니다.

4. 지난번 지적됐던 "P00A(정보 책임자 결정 담당 항목)가 만들어야 할 산출물 3개 중 하나가 빠져도 검사가 눈치채지 못한다"는 결함은 실제로 고쳐졌고, 고친 검사가 결함을 다시 주입했을 때 정확히 잡아내는 것도 직접 확인했습니다. 이 부분은 추가 조치가 필요 없습니다.

5. 서버가 자동으로 돌리는 17단계 점검 목록과, 사람이 참고하는 안내 문서의 17단계 목록은 순서와 이름이 완전히 일치합니다. 다만 그중 1단계는 원래부터 "정식 메인 브랜치에서만 실행한다"고 정해져 있고, 이번 작업 브랜치에서는 그 규칙대로 실행되지 않았습니다. 이것은 설계대로 작동한 것이라 결함은 아니지만, "17단계 전부 통과"라고 보고하면 실제로 돌지 않은 1단계까지 통과한 것처럼 오해를 줄 수 있어 표현을 구분해야 합니다.

---

# 판단 근거

가장 큰 갈림길은 "기준 지점이 움직였다"는 사실을 어떻게 해석할 것인가였습니다. 두 가지 해석이 가능했습니다.

- 해석 A: 다른 작업자가 정상적으로 자기 작업을 커밋한 것뿐이고, 이 작업이 손댄 파일과 겹치지 않으니 사실상 문제없다.
- 해석 B: 겹치는 파일이 없더라도, 이번 작업 자체가 "시작 기준과 종료 기준이 같아야 완료로 인정한다"는 조건을 스스로 정해 놓았고, 그 조건이 지금 깨져 있으니 완료를 선언할 자격이 없다.

저는 해석 B를 택했습니다. 이유는 이 감사 대상 문서(ai-native-ra-planning-packet-main-integration-revalidation-goal-2026-08-18.md) 자신이 시작과 종료의 공식 기준이 같아야 한다고 완료 조건으로 명시했고, 사용자가 시작 SHA가 바뀌면 최신 main 재검증 필요를 차단으로 세라고 지시했기 때문입니다. 파일이 겹치지 않는다는 사실은 위험이 낮다는 근거는 될 수 있어도 조건을 충족했다는 근거는 될 수 없습니다.

두 번째 갈림길은 "17단계 전부 실행됐다고 말해도 되는가"였습니다. 이 저장소의 두 정본 파일(verification-commands.md와 verify.yml)이 똑같이 "1단계는 main 브랜치에서만 돈다"고 명문화하고 있으므로, 작업 브랜치에서 그 1단계가 안 도는 것은 결함이 아니라 설계입니다. 다만 사업 책임자에게 "17단계 다 통과"라고만 보고하면, 실제로 1단계는 아예 실행되지 않았다는 사실이 가려집니다. 그래서 결함으로는 세지 않되, 보고 표현은 구분해야 한다고 판단했습니다.

---

# 기술 상세 · 명령 · 출력

## 1. 기본 상태 확인

```bash
pwd
git status --short --branch
git log --oneline -4
git rev-parse HEAD HEAD^ HEAD^^ main origin/main
```
→ 뭘 시켰나: 지금 어느 폴더, 어느 브랜치, 어느 커밋에 있는지 확인.
→ 뭐가 나왔나:
```
/Users/kangsangmo/Desktop/Valuehire_v6-wt-ai-native-ra-revalidate-20260818
## task/ai-native-ra-packet-revalidate-20260818
f8e031b Preserve the reviewed AI-native RA plan before owner decisions
0e34b89 Establish the proof boundary before integrating the RA packet
0f8541e docs(engineering): ...
f8e031b7f5d13b4bd72e30d5240e1ff3d5e2983c   (HEAD)
0e34b892fdf21f9a03a61dc913a8931a86f0159e   (HEAD^)
0f8541ef7f56fdf43f12f90c81ec4bd1b0233711   (HEAD^^)
34e4ccff88ce776d06e3001734005a34b169f7eb   (main)
34e4ccff88ce776d06e3001734005a34b169f7eb   (origin/main)
```
→ 좋은 소식/나쁜 소식: 브랜치·작업공간은 지시된 대로 맞으나, main과 origin/main이 지시된 시작값(0f8541e...)이 아니라 34e4ccf...로 이동해 있음을 직접 확인. 나쁜 소식(핵심 차단 사유).

## 2. 저장소 구성 — 이 이동이 이 worktree 안에서 생긴 일이 아님을 확인

```bash
git show --stat --format="" 34e4ccf
comm -12 <(git show --format="" --name-only 34e4ccf | sort) <(git diff --name-only 0f8541e..HEAD | sort)
```
→ 뭘 시켰나: 새로 생긴 main 커밋과 이 작업 브랜치가 같은 파일을 건드렸는지 대조.
→ 뭐가 나왔나: 34e4ccf는 codex-position-map-p0-impl-addendum-2026-08-18.md 한 파일만 수정. 교집합 명령은 출력 없음.

## 3. cherry-pick 무결성

```bash
git diff-tree -p 39a3c530 | git patch-id --stable
git diff-tree -p f8e031b | git patch-id --stable
```
→ 두 결과 모두 939e1f771ccf7e3867d1b712034c4a428a5c737c로 같고, 파일 목록도 39개·3917줄 삽입으로 같습니다.

## 4. diff와 충돌 표시

```bash
git diff --check
git diff 0f8541e..HEAD --check
git grep -n -E "^(<<<<<<<|=======|>>>>>>>)" -- .
```
→ 앞 두 명령은 성적 0, 마지막은 일치 0건을 뜻하는 성적 1입니다. 충돌 표시는 없습니다.

## 5. AC-PLAN-1 정상·반대 시험

```text
PASS planning_packet goal=1 plan=1 prompts=28 required_sections=11 atomic_commands=28 p00a_owned_artifacts=3 links=all-present
AC_PLAN_1_RC=0
COUNTER_AC_PLAN_1_RC=1
```
→ 정상 문서 묶음은 합격하고, P00A 소유권 한 줄만 제거한 임시 사본은 불합격했습니다.

## 6. P00A와 28개 소유권 후보

```text
P00A owned artifacts=3
SUMMARY prompts=28 goal_required_but_not_owned=27 script_exact_required_but_not_owned=27 script_generic_wording_requires_interpretation=2
```
→ P00A는 정확히 세 산출물만 소유합니다. 다른 27개 문서의 유사 후보는 재현됐지만 이번 범위에서는 수정하지 않았습니다.

## 7. 핵심 검사

```text
VERIFY_SCAN_SOURCE=index bash verify.sh: PASS, rc=0
bash scripts/acceptance-hs-gates.sh: ruff/mypy/pytest/runtime import PASS, rc=0
bash scripts/acceptance-0-2-unreachable-content.sh: CHECKED 13, PASS, rc=0
bash scripts/scan-data-exposure.sh all: tracked 153, history blobs 688, violations 0, rc=0
bash scripts/session-status.sh:
HEAD: f8e031b (ahead 2 / behind 1)
ORIGIN: 34e4ccf
RED: 0/20 (acceptance-0-7.sh 제외 — CI 담당)
```
→ 로컬 검사 실패는 0건이지만 공식 기준은 시작보다 한 기록 앞서 있습니다.

## 8. 17단계 대조

verification-commands.md의 17개 행과 verify.yml의 17개 이름은 순서와 내용이 일치했습니다. 8번째 acceptance-0-5 단계는 두 파일 모두 main 브랜치에서만 실행하도록 정합니다. 작업 브랜치에서는 “main 전용 1단계 제외 16단계 실행 대상, 로컬 스크립트 직접 실행은 통과”로 표현해야 합니다.

## 9. 작업 범위와 청결 상태

```text
git status --porcelain: output empty
P00A actual owner-decision artifacts: 0
HumanSearch product implementation changes: 0
.secret-patterns: ignored symlink to the existing main-worktree local file; content not read
```
→ 목표 문서가 기획 패킷보다 먼저 기록됐고 작업 브랜치는 깨끗하며 금지된 제품 작업은 없습니다.

# 결함 목록

[BLOCKER / 미해결 1건] 기준 브랜치 지문 이동
- 재현: git rev-parse main origin/main은 34e4ccff88ce776d06e3001734005a34b169f7eb이며 시작값 0f8541ef7f56fdf43f12f90c81ec4bd1b0233711과 다릅니다.
- 사업 영향: 최신 공식 기준에서 실제로 검증받지 않은 상태를 완료로 승인하게 됩니다.
- 미해결 여부: 미해결. 최신 main에서 전체 재검증이 필요합니다.

[정보/표현 주의, 결함 아님] 서버 17단계 전부 PASS 표현
- 작업 브랜치에서는 main 전용 한 단계가 서버에서 실행 대상이 아닙니다. 로컬 스크립트는 통과했지만 서버 17개를 모두 실행했다고 쓰면 과장입니다.

미해결 BLOCKER 수: 1건.

# 건너뛴 것·다시 한 것

- 충돌 표시 검색 종료 코드를 처음에 파이프 뒤에서 잘못 읽을 뻔해 파이프 없이 다시 확인했습니다.
- session-status.sh가 120초를 넘어 백그라운드에서 끝난 뒤 결과를 확인했습니다.
- 서버 자동 검사의 인라인 단계들은 V1에서 개별 재실행하지 않았습니다. Codex가 앞선 결합 검증에서 실행했다는 주장은 V2에서 별도 재현해야 합니다.
````

→ Claude 판정의 고정값은 `VERDICT: FAIL`, 미해결 차단 1건입니다. 원문은 표현만 정리한 부분 없이 이 블록에 보존했으며, V2는 각 근거를 다시 실행해야 합니다.

## 첫 호출 실패 기록

```text
API Error: Fable 5's safeguards flagged this message. Claude Code can't respond to this message with Fable 5.
Details: [reasoning_extraction]
exit=1
```

→ 첫 호출은 검증을 시작하지 못했으므로 V1 판정으로 세지 않았고, 모델과 표현을 바꾼 새 세션에서 위 판정을 받았습니다.
