CODEAUDIT SPEC v2

1. verdict

`P0-03-pnpm-version-pin`은 micro 범위에서 `PASS_MICRO_ONLY / 구현 확인`입니다. 후보 `bf12c3015ae2e4ade8b62c2d3168d77cdaaa0c8f`는 루트 `package.json`을 실제 JSON으로 파싱 가능하게 만들고, `packageManager`를 정확히 `pnpm@11.22.0` 하나만 둡니다.

단, 이것은 `PARTIAL_PARENT_AC`입니다. Corepack 실행, pnpm 설치, admin lint/typecheck/unit/build/start, CI 소비는 모두 `NOT_RUN`입니다. 저장소 전체도 PASS가 아니며 원본 baseline은 `RED 1/19`, disposable clone은 로컬 `main` 참조 부재 topology 때문에 `RED 2/19`입니다.

- source: `/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/admin-weekly-dashboard-v6-p0-03-pnpm-version-pin-a2`
- original request: `/Users/kangsangmo/.codex/tmp/admin-weekly-plan-audit.wnWRAS/original-user-request.md`
- original sha256/bytes: `b00f70061c0958bc1c818fb9e74334abb604fc8fe7e9d82e4228fc2c95d7c9da` / `22817`
- dependency checkpoint: `dbb55566b9f656800892b7373678444641989432`
- P0-02 audit sha/bytes 재확인: `fb4daed9a6606f0a1a950b3f7b021c2268f9e91cc12831f779f381c4d5115afe` / `8919`
- RED: `9beac4336cd97d4617cf1ae9e0f394416fa47ea3`
- candidate: `bf12c3015ae2e4ade8b62c2d3168d77cdaaa0c8f`
- disposable clone: `/tmp/codeaudit-p0-03.MPhnAp/clone`
- severity counts: `P0=0, P1=0, correctness/security/data-integrity core P2=0`
- external side effect count: `0`
- source clean after audit: `git status --short` empty, HEAD unchanged

2. matrix

| ID | 요구/주장 | 판정 | 근거 | 반증/공백 | 심각도 |
|---|---|---|---|---|---|
| R1 | root `packageManager` 정확히 `pnpm@11.22.0` | 구현 확인 | `package.json:2` 값, Node readback `{packageManager:"pnpm@11.22.0", fieldType:"string", keys:["packageManager"]}` | 없음 | 없음 |
| R2 | canonical verifier GREEN, checked=1 target=1 | 구현 확인 | `bash scripts/verify/check-admin-foundation.sh pnpm-version` exit `0`, `checkedPackageManagerFields=1 targetCount=1 reason=null` | 없음 | 없음 |
| R3 | RED 커밋에서 missing package가 RED | 구현 확인 | RED exit `1`, `checkedPackageManagerFields=0 targetCount=0 reason=missing-package-json` | 없음 | 없음 |
| R4 | missing/malformed/non-string/other value fail closed | 구현 확인 | clone edge exits 모두 `1`: missing field, malformed JSON, non-string, other value | missing field/malformed는 targetCount 0이나 계약은 RED 요구 | 없음 |
| R5 | mutation `pnpm@11.22.1` RED target=1 | 구현 확인 | mutation exit `1`, `checkedPackageManagerFields=1 targetCount=1 reason=package-manager-mismatch` | 없음 | 없음 |
| R6 | 허용 파일만 변경 | 구현 확인 | base..candidate: P0-03 goal, `package.json`, verifier 3개만 변경 | forbidden diff for `.github`, `docs/sot`, `.node-version`, lock/workspace/apps = empty | 없음 |
| R7 | package JSON 최소 shape | 구현 확인 | raw file 3 lines, keys only `packageManager`, no `private/name/scripts/deps/engines/workspaces` | 다음 P0-04가 private/workspace 담당 | 없음 |
| R8 | node regression 없음 | 구현 확인 | `bash scripts/verify/check-admin-foundation.sh node-version` exit `0`, `targetCount=1` | runtime manager consumption은 NOT_RUN | 없음 |
| R9 | Lore trailers parse | 구현 확인 | RED/candidate 각각 `Constraint`, `Rejected`, `Confidence`, `Scope-risk`, `Directive`, `Tested`, `Not-tested`를 `git interpret-trailers --parse`로 분리 파싱 | commit message는 직접 증거가 아니라 보조 기록 | 없음 |
| R10 | source/clone baseline 분리 | 구현 확인 | source `RED: 1/19`, clone `RED: 2/19`; clone `MAIN_REF=none`, `ORIGIN_MAIN_REF=4fdef31...` | clone 추가 RED는 topology 차이 | 없음 |

3. key-flow

진입점은 `bash scripts/verify/check-admin-foundation.sh pnpm-version`입니다. `scripts/verify/check-admin-foundation.sh:4-10`은 selector를 고르고, `:40-43`은 기대값 `pnpm@11.22.0`, 파일 `package.json`, count 초기값을 정합니다. `:47-50`은 파일 부재를 `missing-package-json` RED로 냅니다. `:53-67`은 Node의 `JSON.parse`로 실제 JSON을 읽고 `packageManager` 존재·타입을 검사합니다. `:69-87`은 정상/형식 오류/누락/비문자열을 분기하고, `:94-98`은 값 불일치를 RED로 만듭니다. `:100-101`은 PASS receipt를 출력합니다.

생산 설정 경로는 `package.json packageManager -> Corepack/pnpm selector`입니다. 이번 micro는 그 직접 selector만 증명하며, goal 문서 `docs/engineering/admin-weekly-dashboard-v6-p0-03-pnpm-version-pin-goal-2026-08-17.md:35`도 Corepack 실행·pnpm install·admin lifecycle·CI를 `NOT_RUN`으로 제한합니다.

4. missed-better-answer

더 나은 보고는 “P0-03 micro PASS”와 “AC-01/product PASS”를 분리해야 합니다. 이 후보는 pnpm 버전 선택자만 맞춥니다. root private/workspace, lockfile, admin 앱, dependency install, CI wiring은 다음 micro 또는 금지 범위입니다.

또한 writer report와 commit `Tested:` trailer만으로 성공을 세면 안 됩니다. 이번 감사는 같은 명령을 source와 disposable clone에서 재실행했고, 그 재실행 결과만 최종 근거로 세었습니다.

5. adversarial rebuttal

가장 강한 반박: “`packageManager` 값 하나가 있어도 실제 Corepack이나 pnpm이 그 값을 소비하는지 증명하지 못한다.”

반박 후 결론: 맞습니다. 그래서 Corepack/pnpm execution은 `NOT_RUN`으로 남깁니다. 하지만 P0-03 계약의 단일 관찰 결과는 “파싱 가능한 root `package.json`의 `packageManager` exact value + canonical verifier targetCount=1”입니다. 이 범위에서는 RED/GREEN/edge/mutation이 모두 재현됐으므로 micro는 PASS입니다.

6. evidence ledger

| 주장 | 판정 | 1차 근거 | 강도 | 미확인 |
|---|---|---|---|---|
| 후보 JSON | 확인 | `package.json` raw: `{"packageManager":"pnpm@11.22.0"}` only | 강함 | 없음 |
| GREEN | 확인 | source exit `0`: `ADMIN_FOUNDATION_PNPM_VERSION checkedPackageManagerFields=1 targetCount=1 expected=pnpm@11.22.0 reason=null` | 강함 | 없음 |
| RED | 확인 | RED exit `1`: `reason=missing-package-json`, checked `0`, target `0` | 강함 | 없음 |
| edge RED | 확인 | missing field/malformed/non-string/other exits all `1` | 강함 | 없음 |
| mutation | 확인 | `pnpm@11.22.1` exit `1`, checked `1`, target `1` | 강함 | 없음 |
| broader checks | 확인 | `verify.sh` exit `0`; `session-status.sh` exit `0`, source `RED 1/19`; `acceptance-0-2.sh` exit `2` known `.secret-patterns` gap | 중간 | 전체 저장소 PASS 아님 |
| syntax/diff | 확인 | `bash -n` exit `0`; `git diff --check` exit `0`; diff files exactly 3 | 강함 | 없음 |
| trailers | 확인 | RED/candidate trailers parse separately with required 7 keys | 중간 | trailer 내용은 실행 증거 아님 |
| effects | 확인 | 외부 서비스/네트워크/install 미실행, local temp clone mutation only | 중간 | 시스템콜 수준 네트워크 계측은 안 함 |

7. repetition result

검색 범위는 현재 제공된 task payload와 repository-local evidence뿐입니다. 현재 보이는 범위에서 `P0-03 a2` 감사 요청은 1회입니다. 전역 대화 보관함 검색 도구는 사용하지 않았으므로 “전체 역사상 몇 번째”는 미확인입니다.

8. validation limits

실행한 명령과 결과: `pnpm-version` GREEN exit `0`; RED commit canonical exit `1`; mutation exit `1`; edge 4종 exit `1`; `node-version` regression exit `0`; `bash -n` exit `0`; `git diff --check` exit `0`; `verify.sh` exit `0`; source `session-status.sh` exit `0 RED 1/19`; clone `session-status.sh` exit `0 RED 2/19`; `acceptance-0-2.sh` exit `2`.

증명하지 않은 것: Corepack 실행, pnpm install, admin install/lint/typecheck/unit/build/start, CI, production runtime consumption. 모두 goal상 `NOT_RUN`이며 PASS 근거로 세지 않았습니다.

9. prioritized next action

다음 안전 행동은 P0-04 root private workspace micro로 넘어가되, P0-03의 PASS 범위를 확장해서 말하지 않는 것입니다. P0-04에서는 `private`, workspace 선언, 그리고 그에 맞는 RED/GREEN/mutation을 별도 계약으로 검증해야 합니다.
