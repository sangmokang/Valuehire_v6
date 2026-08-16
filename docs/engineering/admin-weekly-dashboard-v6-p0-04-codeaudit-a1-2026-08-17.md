CODEAUDIT SPEC v2

1. verdict

감사자 `/root/p0_04_codeaudit_a1` 판정: `PASS_MICRO_ONLY`.

P0-04는 구현 확인입니다. 후보 `f53e9c9d0edfcd1e66d3f59b691908978a7c6927`는 루트 발행을 막고, admin 앱들이 잡힐 workspace 경계 `apps/*`를 정확히 선언합니다. 부모 AC-01은 계속 `PARTIAL_PARENT_AC`입니다.

Severity: P0 0, P1 0, correctness/security/data-integrity P2 0, LOW 1. External effects: 0. Source worktree: clean/unchanged. Disposable locator: `/tmp/p0-04-audit.VJ13L1`.

2. requirement/claim matrix

| ID | 요구/주장 | 판정 | 근거 | 공백/반증 | 심각도 |
|---|---|---|---|---|---|
| R1 | 원 요청 해시 일치 | 구현 확인 | `b00f70061c0958bc1c818fb9e74334abb604fc8fe7e9d82e4228fc2c95d7c9da` | 없음 | 없음 |
| R2 | P0-03 dependency 증거 일치 | 구현 확인 | `ac26ece...` commit 존재, raw audit sha256 `dc2706...b6109` 일치 | 없음 | 없음 |
| R3 | Phase0 P0-04 계약/허용 파일 준수 | 구현 확인 | [atomic-plan](/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/admin-weekly-dashboard-v6-p0-04-root-private-workspace-a1/docs/engineering/admin-weekly-dashboard-v6-atomic-plan-phase0-2026-08-17.md:64) P0-04 시작, line 70 허용 파일 | 없음 | 없음 |
| R4 | root `package.json` parsed `private=true` | 구현 확인 | [package.json](/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/admin-weekly-dashboard-v6-p0-04-root-private-workspace-a1/package.json:2) boolean true | scripts/name/engines/dependencies 추가 없음 | 없음 |
| R5 | `pnpm-workspace.yaml` exactly one `apps/*` | 구현 확인 | [pnpm-workspace.yaml](/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/admin-weekly-dashboard-v6-p0-04-root-private-workspace-a1/pnpm-workspace.yaml:1) `packages`, line 2 `apps/*` | extra/wrong/comment/no-newline 모두 RED | 없음 |
| R6 | canonical GREEN exit 0, counts 1+1 => target 2 | 구현 확인 | `checkedPrivateFields=1 workspacePatternCount=1 targetCount=2` | target 값은 스크립트 hard-code지만 별도 JSON/YAML 파싱으로 실제 1+1 확인 | 없음 |
| R7 | RED checkout 의도 실패 | 구현 확인 | RED `bc3e803...` exit 1, `reason=private-missing-or-malformed` | RED가 pass할 필요는 없음 | 없음 |
| R8 | required mutations RED | 구현 확인 | `private=false` exit 1, `remove apps/*` exit 1 | `private=false` receipt는 workspace를 처리하지 않아 `workspacePatternCount=0` | LOW |
| R9 | P0-02/P0-03 regression 없음 | 구현 확인 | `node-version` exit 0, `pnpm-version` exit 0 | broader repo는 RED 유지 | 없음 |
| R10 | forbidden scope 없음 | 구현 확인 | diff files exactly 4, outside_allowed `[]` | lockfile/CI/apps/admin/SOT 변경 없음 | 없음 |
| R11 | parent remains partial | 구현 확인 | [controller](/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/admin-weekly-dashboard-v6-p0-04-root-private-workspace-a1/docs/engineering/admin-weekly-dashboard-v6-controller-goal-2026-08-17.md:200) AC-01은 P0-02~P0-12/P0-04A 포함 | install/lint/typecheck/unit/build/start/CI NOT_RUN | 없음 |

3. key-flow

계약 흐름은 root JSON field + workspace YAML file -> selector `root-workspace` -> receipt입니다. [check-admin-foundation.sh](/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/admin-weekly-dashboard-v6-p0-04-root-private-workspace-a1/scripts/verify/check-admin-foundation.sh:19)는 JSON을 파싱하고, line 48은 workspace 파일을 정확한 byte 문자열과 비교합니다.

실행 원문 핵심:

```text
bash scripts/verify/check-admin-foundation.sh root-workspace
PASS: root package is private and pnpm workspace declares exactly apps/*
ADMIN_FOUNDATION_ROOT_WORKSPACE checkedPrivateFields=1 workspacePatternCount=1 targetCount=2 ... reason=null
EXIT:0
```

4. missed-better-answer

더 나은 구현은 `target_count=2`를 먼저 박아두기보다, `checkedPrivateFields + workspacePatternCount`를 처리 뒤 계산하는 방식입니다. 현재 GREEN은 별도 파싱으로 실제 1+1이 입증되어 PASS지만, 실패 receipt에서는 처리하지 않은 workspace까지 target에 포함한 것처럼 보일 수 있습니다.

또 하나의 LOW: [check-admin-foundation.sh](/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/admin-weekly-dashboard-v6-p0-04-root-private-workspace-a1/scripts/verify/check-admin-foundation.sh:28)는 `status`를 초기화하지 않아 `env status=7`이면 정상 파일도 false RED가 됩니다. 사업 영향은 자동 검증 환경에 같은 환경변수가 있으면 정상 후보를 실패로 오판하는 정도이며, 잘못된 후보를 통과시키지는 않습니다.

5. adversarial rebuttal

가장 강한 반론: “`targetCount=2`가 hard-coded라면 GREEN receipt를 믿으면 안 된다.”

반박: receipt 단독으로 믿지 않았습니다. `node -e` 별도 파싱 결과 `privateType=boolean`, `patterns=["apps/*"]`, `patternCount=1`, raw workspace bytes `"packages:\n  - apps/*\n"`였습니다. 따라서 후보의 target 2는 실제 component 1+1과 일치합니다.

수정 결론: 후보 PASS는 유지합니다. 단, mutation receipt의 target-count 정직성은 완벽하지 않아 LOW로 기록합니다.

6. evidence ledger

| 주장 | 판정 | 1차 근거 | 강도 | 미확인 |
|---|---|---|---|---|
| candidate HEAD 정확 | 확인 | `git rev-parse HEAD -> f53e9c9...` | high | 없음 |
| RED commit 정확 | 확인 | `git cat-file -t bc3e803... -> commit` | high | 없음 |
| allowed diff exact | 확인 | `diff_file_count 4`, `outside_allowed []` | high | 없음 |
| canonical GREEN | 확인 | exit 0, counts `1/1/2` | high | pnpm runtime discovery |
| required mutations | 확인 | both exit 1 | high | receipt count semantics partly weak |
| broader baseline | 확인 | source `RED: 1/19`, clone `RED: 2/19`; `acceptance-0-2` exit 2 | high | full repo PASS |
| syntax | 확인 | `bash -n ...` exit 0 | medium | lsp diagnostics tool not available/applicable for shell/json/yaml |
| exposure | 확인 | forbidden path/field rg exit 1; secrets only doc non-scope line | medium | external services not contacted |

7. repetition result

반복 질문 조사는 이번 micro contract의 요구 범위가 아닙니다. 현재 제공된 원본 요청 파일과 저장소 증거만 확인했고, 과거 대화 전역 검색은 하지 않았습니다.

8. validation limits

NOT_RUN: actual pnpm 11.22 workspace discovery, install, lint, typecheck, unit, build, start, CI, external services. `scripts/verify.sh`와 `scripts/diff-check.sh`는 source에 파일이 없어 `MISSING/NOT_RUN`으로 분리했습니다.

검증 명령: canonical RED/GREEN, P0-02/P0-03 selectors, `session-status`, `acceptance-0-2`, `bash -n`, allowed diff recompute, commit trailer inspection, exposure rg, disposable mutations. Writer/commit summary trailers는 참고 주장일 뿐 PASS 근거로 세지 않았습니다.

9. prioritized next action

다음 micro로 진행 가능합니다: `P0-04A-generated-artifact-ignore`.

후속 개선 우선순위는 LOW 1개입니다. `root-workspace` selector에서 `status=0` 초기화 또는 `if ! actual_private="$(...)"; then ... fi` 형태로 바꾸고, `targetCount`는 실제 처리 count 합으로 산출하면 mutation receipt까지 더 정직해집니다.
