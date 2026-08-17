# HumanSearch L0 자율 하네스 — Codex V2 재공격 (2026-08-16)

## 1층 — 결론

Claude V1의 합격 판정을 그대로 승인하지 않고 낮은 위험 관찰 세 건을 전부 다시 읽었습니다. 두 건은
잘못된 실행보다 보수적 중단으로 끝나는 문제였지만, 장기 무인 실행의 복원성을 높이기 위해 문구와
명령을 더 정확하게 고쳤습니다. 한 건은 저장소 파일과 세션 계약의 차이였으며 사실을 명시했습니다.

## 2층 — 판단 근거

검증자가 “낮은 위험”이라고 붙인 항목도 실행자가 여러 시도를 거치면 해석 갈림이 될 수 있습니다.
그래서 현재 시도의 RED commit을 trailer로 정확히 한 개 고르는 명령을 넣고, 다음 인계 문서가 이미
있을 때는 중복 생성하지 않고 같은 파일에 근거를 보존하며 갱신하도록 고정했습니다.

`AGENTS.md`는 이 worktree에 실제 파일로 없지만 사용자가 이번 세션에 본문 전체를 제공했습니다. 이를
저장소 파일이라고 가장하지 않고 “세션 주입 계약”이라고 goal에 명시했습니다.

## 3층 — 재현 증거

### 1. finding 재현표

| ID | Claude 판정 | Codex 재현 | SOT/AC 대조 | 최종 조치 |
|---|---|---|---|---|
| V1-L1 | 낮음 — 다중 attempt의 `<RED_SHA>` 선택이 한 줄 부족 | 기존 v2 509·519행에서 현재 attempt 선택 명령이 없음을 확인 | 위험한 통과는 아니지만 Gate 4의 재현성이 부족 | 현재 최대 attempt의 RED를 trailer로 찾고 정확히 한 개가 아니면 exit 22로 중단하도록 수정 |
| V1-L2 | 낮음 — repo에 `AGENTS.md` 파일 없음 | `test -e AGENTS.md` exit 1 재현 | 사용자가 세션 본문을 직접 제공했으므로 계약 부재가 아님 | goal에 “worktree 파일이 아니라 세션 주입 계약”이라고 명시 |
| V1-L3 | 낮음 — attempt 2에서 owner-gated prompt 생성/갱신 구분 부족 | 기존 v2 674~687행에 기존 파일 분기 없음 확인 | 중복 문서가 생기면 다음 단계 정본이 갈릴 수 있음 | 같은 경로가 있으면 근거를 보존해 갱신하고 날짜 변경 중복 파일을 금지 |

→ 세 항목 모두 재현했습니다. V1-L1과 V1-L3은 안전성을 더 높이는 교정으로 수용했고, V1-L2는
사실관계를 더 정확히 썼습니다. 기각해 숨긴 Claude finding은 없습니다.

### 2. staged 상태 재현

```text
git status --short
M  docs/engineering/goal-prompts/codex-humansearch-autoloop-L0-2026-08-16.md
A  docs/engineering/goal-prompts/codex-humansearch-l0-surface-classifier-v2-2026-08-16.md
M  docs/engineering/goal-prompts/humansearch-L0-kickoff-2026-08-16.md
A  docs/engineering/humansearch-l0-autonomous-harness-repair-goal-2026-08-16.md
A  docs/engineering/humansearch-v6-clean-room-rebuild-goal-2026-08-12.md
M  docs/engineering/premerge-a3-a4-v1-verdict-2026-08-09.md
M  docs/sot/INDEX.md
A  docs/sot/humansearch-l0-surface-contract.md
?? docs/engineering/humansearch-l0-autonomous-harness-claude-v1-2026-08-16.md

git diff --cached --check
exit 0, 출력 없음
```

→ Claude 실행 직후 기존 staged 여덟 파일은 그대로였고 Claude 원문 파일 하나만 Codex가 새로
만들었습니다. Claude가 저장소를 고치지 않았고 공백 오류도 없다는 뜻입니다.

### 3. 선행 PR의 현재 원격 상태

```json
{"baseRefName":"main","headRefOid":"918f0b683d8ea28454715669285891b021c39df1","mergeCommit":null,"number":13,"state":"OPEN","url":"https://github.com/sangmokang/Valuehire_v6/pull/13"}
{"baseRefName":"main","headRefOid":"b4fd4a803a716ccd55e60932e4abe6b190347b23","mergeCommit":null,"number":14,"state":"OPEN","url":"https://github.com/sangmokang/Valuehire_v6/pull/14"}
{"baseRefName":"main","headRefOid":"68fded1c61064df276a98df73be8b2359739b797","mergeCommit":null,"number":15,"state":"OPEN","url":"https://github.com/sangmokang/Valuehire_v6/pull/15"}
```

→ 세 PR 모두 아직 병합되지 않았습니다. 새 구현 프롬프트는 이 상태에서 제품 변경 0으로 멈추도록
설계돼 있어 현재 미병합 상태를 성공으로 오인하지 않습니다.

### 4. 정본 회수와 CLI 권한 재현

```text
04c03a11bf0b88ad3f84efbf37a3b237d735d471941f8fe5c23f39ce57273faf  docs/engineering/humansearch-v6-clean-room-rebuild-goal-2026-08-12.md
04c03a11bf0b88ad3f84efbf37a3b237d735d471941f8fe5c23f39ce57273faf  /Users/kangsangmo/Desktop/Valuehire_v6/worktrees/humansearch-clean-room-plan/docs/engineering/humansearch-v6-clean-room-rebuild-goal-2026-08-12.md

--allowedTools, --allowed-tools <tools...>
--disallowedTools, --disallowed-tools <tools...>
--no-session-persistence
--permission-mode <mode>
--safe-mode
--tools <tools...>
```

→ 비추적 클린룸 문서를 byte 단위로 같은 tracked 문서로 회수했습니다. Claude 명령에 쓴 읽기 허용,
쓰기 차단, 세션 비보존, 안전 모드 플래그도 현재 CLI에 실제로 있습니다.

### 5. G3 반복문 반대 방향 공격

```text
g3_count=2
would_run=scripts/acceptance-hs-portal-constants.sh
would_run=scripts/acceptance-hs-portal-constants-hardening.sh
```

→ 두 줄 목록이 하나로 합쳐지거나 공백으로 쪼개지지 않고 각각 한 번씩 순회했습니다. 이름 규칙으로
찾은 스크립트를 전량 실행한다는 계약이 zsh에서도 유지됩니다.

## 최종 판정

Claude V1의 실제 finding 세 건을 모두 재현했고 숨기거나 요약 기각한 항목은 0건입니다. 두 교정 뒤
같은 전체 V1을 다시 실행했고 최종 판정도 `VERDICT: PASS`였습니다. 최종 원문은
`docs/engineering/humansearch-l0-autonomous-harness-claude-v1-final-2026-08-16.md`에 보존합니다.
