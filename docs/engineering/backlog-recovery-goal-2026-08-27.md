# 밀린 산출물 회수와 관문 급소 수리 — goal (2026-08-27)

> 등급 L1(이 문서 자체는 계획·분석) · 실행 WU는 L2~L3 · 기준 HEAD `3094eef`
> 읽은 SOT: `docs/sot/coding-principles.md` · `docs/sot/git-workflow.md` · `docs/sot/verification-commands.md` · `docs/sot/mechanism-registry.yaml`
> **이 저장소에 `docs/sot/30-strict-mode-contract.md`·`31-strict-recurrence-ledger.md`·`package.json` 은 없다**(실측). strict SOT-30 §2의 `npm run wt`·`npm run check`·`strict:gate` 는 이 레포에 배선되지 않았으므로 core 계약만 적용하고 워크트리는 `git worktree add`, 검증은 `docs/sot/verification-commands.md` 의 실제 명령을 쓴다. R4 재발 원장은 이 레포에 없으므로 `docs/engineering/` 의 과거 판정서를 대체 근거로 인용한다.

## 상위 목표 (1문장)

**완성됐는데 git 밖에 있는 작업을 되찾고, 그것을 통과시킬 관문이 가짜 합격을 막게 만든다.**
성공 신호 1개: 미추적 산출물 0건 + 가짜 합격 스크립트가 관문에서 종료값 1로 거부됨.

## 현재 상태 (실측 · 추측 금지)

### 사실 1 — 완성된 코드가 git 밖에 있다 (가장 심각)

```
?? tools/strict/checkpoint-gate.mjs
?? tools/strict/checkpoint-js-scan.mjs
?? tests/checkpoint-gate.test.mjs
?? tests/checkpoint-gate-mutation.test.mjs
?? docs/sot/features/            ← SOT 디렉토리 통째로 미추적
 M scripts/check-docs-sot.sh     ← +410줄 (기능 정본 카탈로그 검사)
 M docs/sot/humansearch-browser-contract.md  (+85/-38)
```

제품 코드·시험·**SOT 정본**이 커밋되지 않은 채 5일 방치. `docs/sot/coding-principles.md` P15①(작업트리가 커밋 상태와 일치할 때만 배송)과 정면 충돌한다.

### 사실 2 — 문서 왕복이 26개 쌓였다

미추적 39건 중 **26건이 `feature-sot-v1-*`/`v2-*` 프롬프트·판정서**다. 한 작업의 검증 왕복이 파일 26개로 남았다. 이 저장소는 이미 문서 22,971줄 대 제품 코드 636줄이다.

### 사실 3 — 관문이 가짜 합격을 통과시킨다 (재현됨)

```
scripts/verify/run-acceptance.sh:47   pass_lines=$(grep -c 'PASS' "$out")
```
→ 출력에 `PASS` 글자가 1회 있으면 합격. `echo "PASS: forged"; exit 0` 스크립트가 종료값 0으로 통과함을 실행으로 확인(2026-08-27).
CI에서 이 관문을 거치는 검사 **26개**. 거치지 않는 독립 방어선은 2개(`verify.sh`, `scan-data-exposure.sh`).

```
scripts/verify/check-ci-step-integrity.sh:85-96
```
→ 막는 것은 `if` 조건부·`continue-on-error`·`echo bash *.sh`·`bash -n *.sh` 4종뿐. `run: true` 는 통과함을 실행으로 확인.

```
scripts/acceptance-semantic-mutations.sh:68-73
```
→ 무력화 표본 5종(`exit 0`/`true`/no-op/빈 파일/`echo "검사했습니다"`)이 **전부 PASS 글자를 안 찍는 형태**다. 관문이 그것만 잡는다.

### 사실 4 — 좀비 codex 작업이 이어받기를 막는다

`task-mt2fczj5-uvnd1j` 가 132시간째 `running`. 이후 Resume 요청 2건이 각각 2초·1초 만에 실패(`Task ... is still running`).
**단, 그 좀비가 파일을 남기지는 않았다** — 좀비 로그 마지막은 `2026-08-21T04:09:23Z`(KST 13:09)이고 미추적 파일 수정 시각은 `08-22 00:33~01:51`로 11시간 뒤다. 좀비가 만들던 `docs/engineering/audit-six-wu-goal.md` 는 현재 존재하지 않는다.

### 사실 5 — 급소 수리 범위는 처음 추정보다 작다 (자기 정정)

2026-08-27 1차 조사에서 "판정 형식 불명 3개"라 적었으나, 실제로 돌려 보니 `acceptance-0-5.sh` 는 `PASS: 0-5 완료 — …` 를 찍고 관문을 정상 통과한다. `acceptance-ci-step-integrity.sh:31` 도 `printf 'PASS: %s — %s\n'` 을 갖고 있다. 1차 조사의 grep 이 줄머리 앵커(`^\s*`)를 써서 조건문 뒤 출력들을 놓쳤다. **"반나절이라는 추정에 근거가 없다"는 지적은 유지하되, 형식 불일치의 규모는 축소 정정한다.**

## 근본 원인

배송의 마지막 구간(커밋 → PR → 병합)만 사람 손에 있고 기계 강제가 없다. `docs/sot/git-workflow.md:23` 이 자동 병합을 금지한 것은 의도된 설계지만, **커밋조차 안 된 산출물을 잡는 장치는 없다.** P15①은 `make ship` 을 전제하는데 이 레포에는 `make` 도 `package.json` 도 없다.

## WU 분해 (AC 1개 = 검증 1개 = 커밋 1개)

의존 관계: WU-0 → WU-1 → WU-2 → WU-3. WU-4는 무의존(병렬 가능).

| WU | AC (EARS) | 검증 명령 | 등급 | 선행 |
|---|---|---|---|---|
| **WU-0** | If 좀비 codex 작업이 running 이면, then 취소 후 Resume 요청이 성공해야 한다 | `codex-companion.mjs status --all` 에 running 0건 · 새 Resume 종료 정상 | L0 | — |
| **WU-1a** | If `tools/strict/checkpoint-*.mjs` 와 그 시험이 미추적이면, then 시험 통과를 확인한 뒤 한 커밋으로 회수해야 한다 | `node --test tests/checkpoint-gate*.test.mjs` exit 0 · `git status --short` 에 해당 4건 0 | L2 | WU-0 |
| **WU-1b** | If `docs/sot/features/` 와 `check-docs-sot.sh` 변경이 미추적이면, then 검사 통과 확인 후 회수해야 한다 | `bash scripts/check-docs-sot.sh` exit 0 · 해당 항목 `git status` 0 | L3(SOT 수정) | WU-1a |
| **WU-1c** | If `feature-sot-v1/v2-*` 문서 26건이 미추적이면, then 최종본만 남기고 중간 왕복은 폐기하거나 1개로 합쳐야 한다 | `git status --short \| grep -c '^??'` 가 5 이하 | L1 | WU-1b |
| **WU-2a** | If 인수 검사가 종료값 0인데 판정 형식이 계약과 다르면, then 관문이 종료값 1로 거부해야 한다 | 위조 표본 `echo "PASS: forged"; exit 0` → 관문 exit 1 | L2 | WU-1c |
| **WU-2b** | If 무력화 표본에 "PASS 글자를 찍는 위조"가 없으면, then 6번째 표본으로 추가하고 그것이 차단돼야 한다 | `acceptance-semantic-mutations.sh` 가 6종 × 전량에서 CHECKED 증가 · exit 0 | L2 | WU-2a |
| **WU-2c** | If CI 스텝이 `run: true`·`printf PASS` 같은 no-op 이면, then 무결성 검사가 거부해야 한다 | 반례 워크플로 → `check-ci-step-integrity.sh` exit 1 | L2 | WU-2b |
| **WU-3** | If 충돌 PR(#14·#15·#29)이 8일 이상 열려 있으면, then 닫거나 최신 main 위로 재발행해야 한다 | `gh pr list --state open` 에 CONFLICTING 0건 | L1 | WU-2c |
| **WU-4** | If `~/.codex/config.toml` 의 `pre_tool_use` 가 `enabled=false` 이면, then 왜 꺼졌는지 확인한 뒤 오너 승인으로만 되돌려야 한다 | 오너 판단 기록 + 변경 시 전후 해시 | L3(외부 환경) | 무의존 |

## 예외 케이스 표 (R1 — 표에 없는 상황은 임의 판단 금지, 중단 후 표 갱신)

| 상황 | 처리 |
|---|---|
| 좀비 취소가 실패한다 | **명시적 중단.** 강제 종료 시도 금지 — 프로세스 정체 미확인 |
| checkpoint-gate 시험이 실패한다 | **명시적 중단.** 미완성 코드일 수 있으므로 커밋하지 않고 보고 |
| `docs/sot/features/` 가 기존 SOT 계약과 충돌한다 | **명시적 중단.** SOT 우선(§7), 오너 확정 필요 |
| feature-sot 문서 26건 중 어느 것이 최종본인지 모호하다 | **명시적 중단.** 폐기 판단은 오너 몫 |
| 관문을 엄격하게 바꿨더니 기존 검사 중 일부가 빨간불이 된다 | **자동 처리** — 그 검사의 판정 출력을 계약 형식에 맞춘다(검사 약화 금지) |
| 관문 수정이 26개 검사 전량 재실행을 요구한다 | **자동 처리** — 전량 실행하고 출력 숫자 그대로 기록 |
| 충돌 PR 안에 본선에 없는 유일한 산출물이 있다 | **명시적 중단.** 닫기 전 오너 확인 |
| codex 훅이 꺼진 이유가 확인 안 된다 | **명시적 중단.** 켜지 않는다 |
| 그 외 전부 | **명시적 중단 + 사유 기록 + 이 표 갱신안 제시** |

## 비범위

- PR 병합 실행(USER_MERGE_ONLY)
- HumanSearch 기능 추가(L2 서치 순회 등) — 이 goal과 무관, 병행 가능
- GitHub 요금제 변경이 필요한 branch protection 강제 — 개인 계정+비공개는 403(기확인)
- codex 환경 파일의 임의 수정

## 적대 검증 로그

(후기록 — V1/V2 판정 본문을 여기에 append)
