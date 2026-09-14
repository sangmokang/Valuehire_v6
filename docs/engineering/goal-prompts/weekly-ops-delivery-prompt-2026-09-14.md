# 착수 프롬프트 — weekly-ops를 main에 배송 가능한 PR 사슬로 만든다 (2026-09-14)

/strict · harness 게이트 0~6 적용. 저장소 `/Users/kangsangmo/Desktop/Valuehire_v6`. 메인 작업트리에서 소스를 고치지 않는다. 모든 코드 변경은 `worktrees/<NAME>/`(브랜치 `task/<NAME>`) 안에서만 한다.

## 0. 상위 목표 (한 문장)

`worktrees/weekly-ops-skill`(task/weekly-ops-skill, HEAD ad91d53)에 갇힌 67커밋·11,813줄을, **각 PR이 자기 base 대비 3,000줄 미만**이고 **사슬의 마지막 트리가 정본 트리와 동일**한 PR 사슬로 잘라 origin에 올리고 CI 초록까지 확인한다. 이 프롬프트는 배송만 한다. Supabase 파이프 복구(v3 WU-1~8)와 Golden v2 발행 엔진 구현은 다음 프롬프트다.

## 1. 오늘 확인된 실측 (2026-09-14 07:58~08:40 KST, 이 숫자를 전제로 한다)

| 항목 | 값 | 확인 명령 |
|---|---|---|
| weekly-ops HEAD vs main | 67커밋, 38파일, +11,813 −44 | `git diff --shortstat main...task/weekly-ops-skill` |
| origin 대비 미푸시 | 55커밋 | `git rev-list --count origin/task/weekly-ops-skill..task/weekly-ops-skill` |
| 기존 스택 1 (d594e36) vs main | 13커밋, 29파일, +8,739 −36 → **3,000줄 위반** | `git diff --shortstat main...task/weekly-ops-skill-stack-1` |
| 스택 2 증분 | +592 −17 | `git diff --shortstat task/weekly-ops-skill-stack-1...task/weekly-ops-skill-stack-2` |
| 스택 3 증분 | +2,742 −251 | `git diff --shortstat task/weekly-ops-skill-stack-2...task/weekly-ops-skill-stack-3` |
| 스택 3 트리 = weekly-ops HEAD 트리 | diff 0 | `git diff --stat task/weekly-ops-skill-stack-3 task/weekly-ops-skill` |
| split/p1-weekly-evidence-infra vs main | 2커밋(b61fec9, 3fc86cc), +2,807 −18 | `git diff --shortstat main...split/p1-weekly-evidence-infra` |
| PII 게이트 상태 | weekly-ops HEAD에는 `EMAIL_PATTERN`/`find_sensitive_values`가 남아 있음(contract_gate.py 11곳 등). 3fc86cc는 이를 제거함. **두 방향이 공존** | `/usr/bin/grep -c "EMAIL_PATTERN\|find_sensitive_values" worktrees/weekly-ops-skill/.agents/skills/weekly-ops/scripts/*.py` |
| Golden 발행 | `contracts/weekly-ops/notion-golden-sample-v1.json`: `CONTRACT_ONLY_NOT_EXECUTABLE`, `publication_allowed=false`. 병합해도 노션 자동 발행은 NOT_RUN | 파일 4~5행 |
| 검증 도구 | `worktrees/weekly-ops-skill/verify.sh`, `scripts/acceptance-weekly-ops-skill.sh`(599줄), `tests/weekly_ops/` 7파일 | `ls` |

## 2. 결정 카드 — 코드 전에 사장님 답 2건 (WU-0에서 goal 문서에 기록)

1. **PII 정본**: (A) 3fc86cc 방향 = 내부 전용 도구이므로 이메일·전화 정규식 차단과 후보자 필드 차단을 제거(2026-09-05 결정, [[project-shadow-dashboard-pii-policy]]와 일관) / (B) weekly-ops HEAD 방향 = 10라운드 강화한 차단을 유지.
   - 기본값 없음. 답이 없으면 WU-1 이후 진행 금지.
   - A를 고르면 `test_weekly_gate_pii_values.py`와 acceptance의 `pii-value-bypass` 변조 검사도 함께 제거된다(3fc86cc가 이미 그렇게 함). B를 고르면 3fc86cc는 폐기한다. 어느 쪽이든 `access_token/api_key/credential` 차단(비밀값)은 남긴다.
2. **첫 PR의 base**: (A) split/p1(2,807줄)을 첫 PR로 쓰고 나머지 11커밋을 2~3개로 재분할 / (B) 13커밋을 처음부터 새로 3등분. 권장 A — 이미 잘려 있고 3,000줄 아래다.

## 3. 범위 / 비범위

- 범위: 커밋 재배치(rebase·cherry-pick·squash), PII 결정 반영, PR 사슬 생성, CI 초록 확인, 각 PR 본문에 base/head·diff 크기·발행 NOT_RUN 명시.
- 비범위: 새 기능, Golden v2 발행 엔진, Supabase 적재 복구, ChatGPT 사이트 연동, PR 병합(병합은 사장님만, `USER_MERGE_ONLY`).

## 4. 작업 단위 — 순서 고정, 한 WU = 한 워크트리 = 인수 기준 1개

### WU-0 — 결정 기록 (코드 0줄)
- 워크트리 `worktrees/weekly-ops-delivery-goal`. `docs/engineering/weekly-ops-delivery-goal-2026-09-14.md` 신설. §1 실측표, §2 결정 2건의 답과 시각, PR 사슬 계획표(PR 번호 자리 비움), 비범위를 적는다.
- AC-0: `test -f docs/engineering/weekly-ops-delivery-goal-2026-09-14.md && /usr/bin/grep -c "결정 1\|결정 2" docs/engineering/weekly-ops-delivery-goal-2026-09-14.md` → 2 이상. 음성: 결정 답이 비어 있으면 문서에 `PENDING`이 남고, 이 경우 WU-1 착수 금지.

### WU-1 — PII 정본 통일 (결정 1 반영)
- 워크트리 `worktrees/weekly-ops-pii-unify`, base = task/weekly-ops-skill.
- A면 3fc86cc를 cherry-pick하고 충돌을 풀어 HEAD에서 `EMAIL_PATTERN`/`PHONE_PATTERN`/`find_sensitive_values`와 후보자 콘텐츠 필드 차단을 제거. B면 3fc86cc를 쓰지 않고 이 WU는 "결정 B, 변경 0"으로 goal 문서에 기록하고 종료.
- AC-1(A): `/usr/bin/grep -rc "EMAIL_PATTERN\|find_sensitive_values" .agents/skills/weekly-ops/scripts/ | /usr/bin/grep -v ":0"` → 출력 0줄. 동시에 `/usr/bin/grep -c "access_token\|api_key\|credential" .agents/skills/weekly-ops/scripts/schema_gate.py` → 1 이상(비밀값 차단은 남음). 양성: `uv run pytest tests/weekly_ops -q` → `passed`, `failed` 0. 음성: 결제 전 HEAD에서 같은 grep을 돌리면 0줄이 아니어야 한다(대조군).
- AC-1(B): `git diff --stat task/weekly-ops-skill HEAD | tail -1` → 출력 없음(변경 0).

### WU-2 — PR 사슬 재분할
- 워크트리 `worktrees/weekly-ops-chain`. 정본 트리 T = WU-1 결과 HEAD.
- 브랜치 `deliver/weekly-ops-1`(base main), `deliver/weekly-ops-2`(base 1), `deliver/weekly-ops-3`(base 2), 필요하면 4. 결정 2가 A면 1번은 split/p1 내용에서 시작.
- 각 브랜치는 **자기 base 대비 독립적으로 초록**이어야 한다(스택 2·3 커밋 메시지의 "intermediate branches failed closed" 경고를 그대로 인정하고, 중간 브랜치에서 의존이 끊기면 그 검사를 같은 PR 안으로 옮긴다).
- AC-2a(크기, P11): 각 N에 대해 `git diff --shortstat <base>...deliver/weekly-ops-N` → insertions+deletions < 3,000. 4개 이하의 PR. 음성: 기존 `task/weekly-ops-skill-stack-1`에 같은 명령을 돌리면 8,775로 위반이 재현돼야 한다(대조군).
- AC-2b(동등성): `git diff --stat deliver/weekly-ops-<마지막> <T>` → 출력 없음. 음성: 마지막에서 파일 하나를 되돌린 임시 커밋으로 같은 명령을 돌리면 1줄 이상 나와야 한다.
- AC-2c(각 브랜치 초록): 각 N에서 `./verify.sh` → 마지막 줄 `VERDICT: PASS`; `bash scripts/acceptance-weekly-ops-skill.sh` → `CHECKED` 수를 그대로 기록하고 exit 0. 1번 브랜치에는 이 스크립트가 아직 없을 수 있다. 없으면 "없음"으로 기록하고 있는 검사(`make red-ledger`, 원칙 검사 34개)만 돈다. 없는 검사를 통과했다고 쓰지 않는다.
- AC-2d(발행 공백 명시): 각 PR 본문에 `publication_allowed=false · Golden v2 미구현 · 노션 자동 발행 NOT_RUN` 문장과 base/head·diff 줄 수를 넣는다. `gh pr view <N> --json body -q .body | /usr/bin/grep -c "NOT_RUN"` → 1 이상.

### WU-3 — 푸시·PR·CI
- `git push -u origin deliver/weekly-ops-N` 순서대로. PR은 `gh pr create --base <base 브랜치>`로 사슬을 건다(2번의 base는 deliver/weekly-ops-1, main이 아님).
- AC-3: `gh pr checks <N> --json name,state --jq '[.[]|select(.state!="SUCCESS")]|length'` → 0, **pull_request 이벤트 기준**([[feedback-ci-green-check-event-type]]: push 초록/pull_request 빨강이 공존하니 `gh run list --event pull_request --branch deliver/weekly-ops-N -L1`로 이벤트를 확인). 음성: 검사 하나를 일부러 깨뜨린 임시 커밋에서 같은 명령이 1 이상을 내는지 1회 확인 후 되돌린다.
- 완료 선언은 여기까지. 병합은 하지 않는다.

## 5. 인수 기준 요약 (모두 명령·기대 출력·양성/음성·최소 건수)

| AC | 명령 | 기대 | 정본 조항 |
|---|---|---|---|
| 0 | grep "결정 1\|결정 2" goal 문서 | ≥2 | harness 게이트 1 |
| 1 | grep EMAIL_PATTERN/find_sensitive_values scripts/ | A: 0줄 / B: 변경 0 | 결정 1 |
| 2a | git diff --shortstat base...N | 각 <3,000, PR ≤4 | coding-principles P11 |
| 2b | git diff --stat 마지막 T | 빈 출력 | 동등성 |
| 2c | ./verify.sh, acceptance | PASS, exit 0, CHECKED 수 기록 | harness 게이트 4 |
| 2d | PR 본문 grep NOT_RUN | ≥1 | weekly-ops-contract "발행 NOT_RUN" |
| 3 | gh pr checks (pull_request) | 실패 0 | harness 게이트 5 |

## 6. 하지 말 것

- 메인 작업트리에서 파일을 고치지 마라. 워크트리에 bare `git stash`/`git stash pop` 금지.
- 3,000줄을 맞추려고 테스트를 지우거나 검사기를 약화시키지 마라. 줄 수는 커밋 재배치로만 줄인다.
- 검사가 없는 브랜치에서 "통과"라고 쓰지 마라. "없음"이라고 써라.
- 외부 검증자(Codex)에 넘기기 전에 커밋하라([[feedback-external-verifier-can-overwrite-worktree]]).
- 병합하지 마라. PR 링크와 CI 상태만 보고한다.
- 후보자 실명·연락처·자격증명 값을 goal 문서·PR 본문·로그에 넣지 마라.
- 다른 세션이 main 작업트리에 남긴 미추적 파일(`verification-trust-core-hardening-goal-2026-09-14.md`, `scripts/verify/fixtures/...`)을 건드리지 마라.

## 7. 보고 형식 (3층)

1층 결론 3줄: PR 사슬 N개 링크, 각 diff 줄 수, CI 상태(pull_request 이벤트).
2층 판단 근거: 결정 1·2의 답, 재분할 경계와 이유, 없는 검사 목록.
3층 증거 원문: AC-0~3 명령과 출력을 그대로. 숫자는 출력 그대로, "약" 금지.
마지막에 5줄 결정 카드: 사장님이 병합 순서를 정하는 데 필요한 것만.
