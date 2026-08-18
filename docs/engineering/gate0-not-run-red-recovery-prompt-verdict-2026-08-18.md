# Gate 0 복구 실행 프롬프트 적대 검증 판정 — 2026-08-18

VERDICT: PASS

## 1층 — 결론

실행 프롬프트는 그대로 투입할 수 있습니다. 이미 검증된 수정안을 다시 만들지 않고, 사용자 문서 변경을 별도로 보존하며, 오래 조용한 검사가 진짜 멈춘 경우까지 구분하도록 요구합니다.

첫 외부 검토는 안전장치에 막혔고, 다음 검토에서는 실제 결함 제기와 재검증이 있었습니다. 마지막 현재판은 외부 검토와 Codex 재공격 모두 중간 이상 결함 0건으로 합격했습니다.

## 2층 — 판단 근거

Claude는 현재판에서 task 작업선 업로드와 기본 작업선 직접 업로드 금지, 사장님 병합 전 완료 금지, 병합 뒤 실패 0건 재검증이 서로 충돌하지 않는다고 판정했습니다. Codex는 이 판정을 그대로 받지 않고 현재 PR 머리 커밋과 서버 검사, 정본 줄, 로컬 제외 규칙을 다시 읽었습니다.

Claude가 중간 검토에서 “보존용 `.omx` 파일이 작업 상태를 바꾼다”고 지적했지만, Codex 재현에서는 `.git/info/exclude`가 `.omx/`를 이미 제외해 현재 저장소에서는 그 구체적 원인이 성립하지 않았습니다. 다만 다른 환경에 기대는 설계가 되는 것은 맞으므로 raw manifest 파일을 아예 만들지 않고 표준 출력 파이프에서 전체 지문만 계산하도록 더 강하게 고쳤습니다.

Codex는 Claude가 놓친 두 가지도 먼저 보강했습니다. 시간초과 때 부모만 끝내고 자식·손자·잠금을 남기는 가짜 종료를 막았고, 새 goal 문서를 dirty 메인 작업 폴더에 쓰지 않도록 PR별 clean worktree 소유권을 고정했습니다.

### 결정 카드

**무엇을** — 최종 현재판과 마지막 Claude PASS를 채택합니다.

**왜** — 중간 FAIL의 유효한 이식성 우려를 구조적으로 제거했고, 실제로 틀린 원인 설명은 Codex가 재현 명령으로 정정했으며, 마지막 현재판을 다시 외부 검토했습니다.

**버린 길** — 첫 Claude PASS만 믿는 방법과 `.git/info/exclude`가 있으니 수정하지 않는 방법을 버렸습니다. 전자는 자식 프로세스 잔존과 기록 위치를 놓쳤고, 후자는 다른 clone에서 깨질 수 있습니다.

**대가** — 실행 프롬프트가 자식 프로세스 회수와 보존 지문 readback까지 요구해 구현·검증량이 늘었습니다.

**되돌리기** — 관측성 요구가 과도하다고 확인되면 별도 PR만 닫을 수 있습니다. PR #23과 문서 배송 PR은 독립돼 영향받지 않습니다.

## 3층 — Claude V1 원문과 Codex V2 재현

### V1-0 — 도구 안전장치 거부, 판정 무효

첫 요청은 저장소 공격 검증을 강한 표현으로 요청했고 Claude 안전장치가 답변 생성을 거부했습니다.

```text
API Error: Fable 5's safeguards flagged this message (https://www.anthropic.com/legal/aup). This sometimes happens with safe, normal conversations. Claude Code can't respond to this message with Fable 5.

Try rephrasing the request in a new session or change your model.

Request ID: req_011Ce8fCKAJanAoF7ojp8cMf
```

→ 판정 본문이 없으므로 PASS나 FAIL이 아니라 미판정이었습니다. 문구를 품질·안전 검토로 바꾸고 Sonnet 모델로 재실행해 이 임시 상태를 해소했습니다.

### V1-1 — 초안 PASS 뒤 Codex가 선제 보강

두 번째 호출은 초안에 `VERDICT: PASS`를 냈습니다. 현재 수치, `scripts/session-status.sh:63`의 출력 은폐, `docs/sot/git-workflow.md:15,19`의 작업선·직접 push 금지, `hooks/pre-push:18-32`의 재귀 전례를 대조했습니다. 다만 이 판정 뒤 Codex가 다음 두 누락을 발견했으므로 이 PASS는 현재판의 최종 판정으로 쓰지 않았습니다.

1. 제한 시간이 부모 셸만 끝내면 자식·손자·잠금이 남을 수 있었습니다.
2. 조정 goal을 어느 작업 폴더에 쓰는지 모호해 dirty 메인 작업 폴더를 건드릴 수 있었습니다.

→ 둘을 프롬프트에 보강한 뒤 현재판을 Claude에 다시 보냈습니다. 초안 PASS로 검증을 종료하지 않았습니다.

### V1-2 — 보강판 FAIL 원문

실행 명령 전문:

```bash
env -u ANTHROPIC_API_KEY claude --model sonnet --safe-mode \
  --add-dir /Users/kangsangmo/Desktop/Valuehire_v6 \
  --tools Read --permission-mode dontAsk --no-session-persistence --effort medium \
  -p "docs/engineering/goal-prompts/codex-gate0-not-run-red-recovery-2026-08-18.md의 현재 버전을 읽기 전용으로 최종 재검토하십시오. 직전 PASS 뒤 Codex가 두 보강을 넣었습니다: dirty 파일을 NUL 안전 manifest의 항목 수와 SHA-256으로 전후 대조하고, session-status timeout/TERM/INT/HUP 때 자식·손자 프로세스와 잠금까지 회수하도록 요구했습니다. 또한 goal 문서 위치를 PR별 clean worktree로 고정했습니다. 이 보강이 문서 안에서 모순·실행 불가·새 손실 위험을 만들었는지, 기존의 task push 승인/main push·merge 금지/owner merge 전 BLOCKED/merge 뒤 RED 0/M 계약과 충돌하는지 확인하십시오. 중간 이상 결함이면 FAIL, 없으면 PASS입니다. 파일을 수정하거나 Bash를 실행하지 마십시오.

[출력 형식]
첫 줄은 VERDICT: PASS 또는 VERDICT: FAIL. 이어서 결론, 판단 근거, 기술 상세 순서의 한국어 존칭체. 확인 못 한 것은 ※. 결함은 심각도·file:line·영향을 적으십시오. 표나 코드 블록 바로 아래에는 화살표 해석을 붙이십시오."
```

→ 저장소 명령을 허용하지 않고 보강된 문서 내부 모순만 보게 한 호출입니다.

판정 본문 전문:

```text
VERDICT: FAIL

## 결론

두 보강 중 프로세스 회수(자식·손자·잠금) 요구는 실행 가능하고 기존 계약과 충돌하지 않습니다만, dirty 파일 보존 검증용 manifest 저장 위치(`.omx/state/gate0-recovery/`)가 `.gitignore`에 없어 이 문서가 요구하는 "전후 `git status --porcelain=v1 -z` 완전 동일" 증명 자체를 문서에 쓰인 대로는 만족시킬 수 없는 자기모순을 만듭니다. 이는 dirty 파일 손실 감지 절차의 신뢰성을 해치는 중간 등급 결함이므로 FAIL입니다.

## 판단 근거

manifest는 "ref나 checkout 상태를 바꾸기 전"에 한 번 만들고 끝에 다시 만들어 항목 수·SHA-256·`git status --porcelain=v1 -z`가 "완전히 같은지" 증명해야 합니다. 그런데 manifest 파일 자체가 `.omx/state/gate0-recovery/`에 생성되고, 저장소 `.gitignore`는 `.omc/`만 무시하며 `.omx/`는 어디에도 없습니다. 따라서 manifest를 최초로 만드는 순간 그 자체가 새 untracked 항목이 되어, 시작과 끝 상태가 구조적으로 달라집니다.

기존 task push 승인/main push·merge 금지/오너 merge 전 BLOCKED/merge 뒤 RED 0/M 계약과는 직접 충돌하지 않습니다. goal 문서를 PR별 clean worktree에 고정한 것도 역할 분담과 일치합니다.

## 기술 상세

- [중간] prompt:184,292 vs `.gitignore:1-3` — `.omx/state/gate0-recovery/` 경로가 `.gitignore`에 없어 manifest 생성 자체가 untracked 항목을 늘립니다.
- [낮음, 참고] `.omx` 명칭이 기존 `.omc/` 관례와 다릅니다.
- 프로세스 회수 보강은 기존 stdout 3줄 계약과 충돌하지 않습니다.
```

→ Claude는 manifest 파일 생성이 상태 비교를 오염시킨다고 판정했습니다. Codex는 이 원인을 그대로 믿지 않고 Git의 전체 제외 규칙을 재현했습니다.

### Codex V2-1 — Claude FAIL 원인 재현

```text
$ git check-ignore -v --no-index .omx/state/gate0-recovery/dirty-before.manifest
.git/info/exclude:7:.omx/ .omx/state/gate0-recovery/dirty-before.manifest
check_ignore_rc=0

$ sed -n '1,3p' .gitignore
# OMC / Claude Code 로컬 상태
.omc/
.claude/settings.local.json
```

→ Claude는 `.gitignore`만 읽고 Git의 로컬 제외 파일을 놓쳤습니다. 현재 저장소에서는 `.omx/`가 실제로 무시되므로 “manifest가 반드시 status를 바꾼다”는 원인은 재현되지 않았습니다. 그러나 clone마다 `.git/info/exclude`가 다를 수 있다는 이식성 위험은 남아, raw 파일 생성을 없애는 더 강한 수정으로 반영했습니다.

수정 뒤 계약:

```text
raw manifest 파일 생성 0건
NUL 안전 스트림 → 즉시 SHA-256 1개
기록 값 = 항목 수 + 전체 지문만
Phase E 끝 = 같은 계산 + 관측성 PR 증거 댓글 + gh pr view --comments readback
```

→ Git 제외 설정과 무관하게 dirty 작업 폴더에 새 파일을 만들지 않습니다. 민감한 경로나 본문도 PR에 올리지 않습니다.

### V1-3 — raw 파일 제거판 PASS

Claude는 raw 파일 제거 뒤 현재판을 다시 읽고 `VERDICT: PASS`를 냈습니다. 다만 Phase D PR이 이미 merge된 뒤 끝 지문을 어느 저장소 기록에 남기는지가 낮은 절차 공백이라고 지적했습니다. 이를 관측성 PR의 증거 댓글과 readback으로 고친 뒤 최종 호출을 한 번 더 실행했습니다.

### V1-FINAL — 현재판 최종 PASS

실행 명령 전문:

```bash
env -u ANTHROPIC_API_KEY claude --model sonnet --safe-mode \
  --add-dir /Users/kangsangmo/Desktop/Valuehire_v6 \
  --tools Read --permission-mode dontAsk --no-session-persistence --effort low \
  -p "docs/engineering/goal-prompts/codex-gate0-not-run-red-recovery-2026-08-18.md 현재 버전의 마지막 변경만 읽기 전용 확인하십시오. Phase D goal에 dirty manifest 시작 항목 수·전체 SHA-256을 merge 전에 기록하고, Phase E 후 관측성 PR 댓글에 시작·끝 값과 일치 여부만 남긴 뒤 readback하도록 했으며 이 작업의 PR 증거 댓글 쓰기를 승인 범위에 추가했습니다. 이 변경이 main push·merge 금지, 민감 경로 비공개, owner merge 전 BLOCKED, 최종 RED 0/M과 모순되거나 새로운 중간 이상 위험을 만드는지 판정하십시오. 파일 수정과 Bash 금지. 첫 줄 VERDICT: PASS 또는 VERDICT: FAIL, 이어 한국어 결론과 결함 file:line·영향. 확인 못 한 것은 ※."
```

→ 최종 수정된 현재 파일만 읽는 호출이며 파일·Git·원격 변경 권한을 주지 않았습니다.

판정 본문 전문:

```text
VERDICT: PASS

결론: 이번 변경은 dirty manifest의 시작 항목 수·전체 SHA-256을 Phase D clean worktree goal 문서에 PR merge 전에 기록하고, Phase E 종료 후 관측성 PR 댓글에는 시작·끝 값과 일치 여부만 남긴 뒤 `gh pr view --comments`로 readback하도록 규정합니다. 이 PR 댓글 쓰기 권한은 승인 범위 문구에 명시적으로 추가돼 있습니다.

- main push/merge 금지: 문서 전 구간에서 `main` 직접 push·자동 merge를 금지하고, PR 병합은 오너 결정으로만 남깁니다. manifest·댓글 절차는 merge 자체를 수행하지 않으므로 모순이 없습니다.
- 민감 경로 비공개: 댓글에는 두 값과 일치 판정만 남기며 내용이나 민감한 경로는 퍼뜨리지 않습니다.
- owner merge 전 BLOCKED: PR merge 전 시작 지문 기록 뒤 오너 merge를 기다리는 구조가 유지됩니다.
- 최종 RED 0/M: `RED: 0/M`, `M>0`, `UNKNOWN` 0건 요건은 수정되지 않았습니다.

새로운 중간 이상 위험을 발견하지 못했습니다. manifest 계산은 dirty 작업 폴더에 파일을 만들지 않도록 금지됐고, 댓글 정보는 개수·해시·일치 여부뿐입니다.

※ 실제 GitHub 저장소의 공개/비공개 설정은 문서만으로 확인하지 않았습니다.
```

→ 현재판 V1은 중간 이상 결함 0건입니다. 저장소 공개 여부와 무관하게 댓글에는 경로·본문이 없고 전체 지문만 있어 민감정보 노출 경계도 유지됩니다.

### Codex V2-2 — 현재 사실과 Claude 주장 재검증

```json
{"baseRefOid":"4fdef31fe75c8519091cebe8a6c4cbf5be1893ae","headRefOid":"3ec842f7975a0de87fb17f155798e0338d884b09","mergeStateStatus":"CLEAN","number":23,"state":"OPEN","statusCheckRollup":[{"conclusion":"SUCCESS","name":"verify","status":"COMPLETED"},{"conclusion":"SUCCESS","name":"verify","status":"COMPLETED"}],"url":"https://github.com/sangmokang/Valuehire_v6/pull/23"}
```

→ Claude 초안 검토에서는 원격 조회가 막혔지만 Codex가 현재 원격을 직접 다시 읽었습니다. PR #23의 현재 머리 SHA는 로컬 task 브랜치와 같고 서버 검사 두 개가 성공했습니다.

```text
$ nl -ba docs/sot/git-workflow.md | sed -n '14,23p'
15 작업 1개 = worktree 1개 = 브랜치 1개 = 인수 기준 1개.
19 - `main` 보호. 직접 push 금지. **오너 본인도 예외 없음**
21 - PR = 인수 기준 1개. **squash merge**, 머지 후 브랜치 삭제
23 - **자동 병합 금지.**

$ nl -ba scripts/session-status.sh | sed -n '57,67p'
57 red=0
58 while IFS= read -r c; do
63   SECRET_PATTERNS_FILE= bash "$c" >/dev/null 2>&1 || red=$((red + 1))
64 done <<< "$checks"
66 printf 'RED: %d/%d (%s 제외 — CI 담당)\n' "$red" "$total" "$EXCLUDED"
67 exit "$rc"
```

→ 기존 코드는 진행 출력을 숨기고 시간 제한이 없습니다. 프롬프트의 별도 관측성 PR은 실제 결함을 겨냥하며, 직접 push·자동 merge 금지는 정본과 일치합니다.

### V1/V2 교차표

| 항목 | Claude V1 | Codex V2 | 최종 판정 |
|---|---|---|---|
| 기존 PR #23 현재성 | 초안에서 로컬 SHA만 확인, 원격은 미확인 | 현재 원격 SHA·CLEAN·CI SUCCESS 2개 재확인 | PASS |
| timeout 자식 회수 | 보강 뒤 충돌 없음 | 초안 누락을 먼저 찾아 자식·손자·잠금 0건 AC 추가 | PASS |
| goal 기록 위치 | PR별 clean worktree 분리 타당 | dirty main에 새 goal을 쓸 모호함 제거 확인 | PASS |
| `.omx` manifest 오염 | 보강판에서 FAIL | 현재는 `.git/info/exclude`로 재현 불가, 이식성 위험은 raw 파일 제거로 해소 | PASS, Claude 원인 일부 정정 |
| merge 뒤 끝 지문 기록 | 낮은 절차 공백 | 관측성 PR 댓글 + readback으로 영속화 | PASS |
| task push와 main 금지 | 충돌 없음 | SOT 15·19·21·23행 재현 | PASS |
| merge 전 완료 우회 | counter-AC로 차단 | `BLOCKED`와 최종 `RED: 0/M` 동시 요구 재확인 | PASS |

→ Claude가 잡은 내 설계 결함 1건은 이식성 위험으로 채택해 더 강하게 고쳤고, Codex가 Claude 판정에서 바로잡은 과장·누락은 2건입니다: `.git/info/exclude` 누락으로 인한 원인 과장 1건, 초안에서 자식 프로세스 회수·goal 위치를 놓친 누락 1묶음입니다.

## 최종 판정

`VERDICT: PASS`. 현재 실행 프롬프트에는 중간 이상 미해결 결함이 없습니다. 실제 코드 구현·PR 생성·병합 뒤 `RED: 0/M` 증명은 이 문서의 미래 실행 범위이며, 이번 판정은 프롬프트 품질만 승인합니다.
