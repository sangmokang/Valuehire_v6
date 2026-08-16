CODEAUDIT SPEC v2

1. verdict

감사자 `/root/p0_03_codeaudit_a1` 판정: `PASS_MICRO_ONLY`.

P0-03은 구현 확인입니다. 후보 `3265336f11772aa475b3586db12cfb6e23d8c87f`는 루트 `package.json`의 실제 JSON 필드 `packageManager`를 정확히 `pnpm@11.22.0`으로 두고, canonical selector가 `checkedPackageManagerFields=1,targetCount=1`로 exit 0을 냅니다.

단, 부모 AC-01은 계속 `PARTIAL_PARENT_AC`입니다. Corepack provisioning, pnpm 11.22.0 실제 실행, admin install/lint/typecheck/unit/build/start/CI는 `NOT_RUN`입니다.

Severity counts: P0 0, P1 0, correctness/security/data-integrity P2 0, LOW 1. External side effect count: 0. Source worktree final status: clean.

2. requirement/claim matrix

| ID | 요구/주장 | 판정 | 근거 | 공백/반증 | 심각도 |
|---|---|---|---|---|---|
| R1 | 원 요청 해시 일치 | 구현 확인 | `sha256=b00f70061...7c9da` | 없음 | 없음 |
| R2 | dependency P0-02 PASS evidence/hash 확인 | 구현 확인 | metadata line 12, raw file hash `fb4daed9...15afe` | 없음 | 없음 |
| R3 | allowed files exact 3개 | 구현 확인 | base..candidate: `package.json`, verifier, goal doc | forbidden 파일 없음 | 없음 |
| R4 | actual parsed `packageManager=pnpm@11.22.0` | 구현 확인 | `package.json:2` | 키는 `packageManager` 1개뿐 | 없음 |
| R5 | RED commit fails missing package.json | 구현 확인 | disposable RED exit 1, `checked=0,target=0` | 없음 | 없음 |
| R6 | Candidate GREEN targetCount exactly 1 | 구현 확인 | source/clone exit 0, `checked=1,target=1` | 없음 | 없음 |
| R7 | P0-02 selector no regression | 구현 확인 | `node-version` exit 0, `checkedVersionFiles=1,targetCount=1` | 없음 | 없음 |
| R8 | mutation pnpm@11.22.1 fails with targetCount=1 | 구현 확인 | disposable mutation exit 1, mismatch | 없음 | 없음 |
| R9 | malformed/missing/non-string cannot pass | 구현 확인 | malformed/non-string/missing/fake string all exit 1 | 없음 | 없음 |
| R10 | production path honestly scoped | 구현 확인 | goal doc lines 43-45, verifier lines 19-43 | Corepack/pnpm execution `NOT_RUN` | 없음 |
| R11 | broader baseline not called PASS | 구현 확인 | source `RED: 1/19`, clone `RED: 2/19` | repo PASS 아님 | 없음 |
| R12 | verifier robustness against ambient env | 부분 이슈 | `scripts/verify/check-admin-foundation.sh:26-28` | `status=7` 환경에서 정상 JSON도 거짓 실패 | LOW |

3. key-flow

Entrypoint: `bash scripts/verify/check-admin-foundation.sh pnpm-version`.

`scripts/verify/check-admin-foundation.sh:6-10`은 `pnpm-version` selector와 expected `pnpm@11.22.0`을 고정합니다.  
`scripts/verify/check-admin-foundation.sh:12-16`은 `package.json` 부재를 `targetCount=0` 실패로 냅니다.  
`scripts/verify/check-admin-foundation.sh:18-25`는 Ruby JSON parser로 실제 `packageManager` 필드를 읽고 string 타입만 허용합니다.  
`scripts/verify/check-admin-foundation.sh:34-43`은 값이 정확히 같을 때만 `checkedPackageManagerFields=1,targetCount=1` PASS receipt를 냅니다.

Configuration contract proof는 있습니다. Actual Corepack/pnpm consumption proof는 없습니다.

4. missed-better-answer

필수 누락은 없습니다. 더 나은 구현은 `status=0`을 command substitution 전에 초기화하거나 `if ! actual="$(...)"; then ... fi` 형태로 바꿔 환경 변수 `status`에 의한 거짓 실패를 막는 것입니다. 이 결함은 틀린 pnpm 값을 통과시키지 않으므로 micro PASS를 깨지는 않습니다.

5. adversarial rebuttal

가장 강한 반론: “검증기가 Ruby에 의존하고 Corepack/pnpm을 실제로 실행하지 않았으니 pnpm pin을 증명하지 못했다.”

반박: 이 micro의 단일 observable result는 실제 pnpm 실행이 아니라 root `package.json`의 parsed `packageManager` 값과 direct selector receipt입니다. Ruby는 검증기 구현 의존성이고 제품 runtime path가 아닙니다. 다만 Ruby 없는 환경에서 canonical command 실행은 이 감사에서 증명하지 않았으므로 portability는 validation limit입니다.

추가 공격 결과:
- malformed JSON: exit 1, `targetCount=1`, `checkedPackageManagerFields=0`
- non-string field: exit 1
- missing field `{}`: exit 1
- fake string-only JSON: exit 1
- mismatch `pnpm@11.22.1`: exit 1, `checkedPackageManagerFields=1,targetCount=1`

6. evidence ledger

Auditor ID: `/root/p0_03_codeaudit_a1`  
Disposable locator: `/tmp/p0-03-codeaudit-a1.HDZhQG/clone`

Hashes:
- base/checkpoint: `36b13a2c3d81e56d2e1e29fa71b72e9cf43d90ca`
- RED: `7677ca4af774010ee0b21e68d0cdd574d7e787b9`
- candidate: `3265336f11772aa475b3586db12cfb6e23d8c87f`
- original request sha256: `b00f70061c0958bc1c818fb9e74334abb604fc8fe7e9d82e4228fc2c95d7c9da`
- P0-02 raw audit sha256: `fb4daed9a6606f0a1a950b3f7b021c2268f9e91cc12831f779f381c4d5115afe`

Raw command results:
```text
pnpm-version GREEN: exit 0
PASS: package.json packageManager equals pnpm@11.22.0
ADMIN_FOUNDATION_PNPM_VERSION checkedPackageManagerFields=1 targetCount=1 expected=pnpm@11.22.0 actual=pnpm@11.22.0 reason=null

RED commit: exit 1
FAIL: package.json missing
ADMIN_FOUNDATION_PNPM_VERSION checkedPackageManagerFields=0 targetCount=0 expected=pnpm@11.22.0 reason=missing-package-json

mutation pnpm@11.22.1: exit 1
ADMIN_FOUNDATION_PNPM_VERSION checkedPackageManagerFields=1 targetCount=1 expected=pnpm@11.22.0 actual=pnpm@11.22.1 reason=package-manager-mismatch
```

Other validation:
- `bash scripts/verify/check-admin-foundation.sh node-version`: exit 0
- `bash verify.sh`: exit 0
- `bash scripts/acceptance-0-2.sh`: exit 2, known `.secret-patterns` baseline
- `bash scripts/session-status.sh`: source `RED: 1/19`, clone `RED: 2/19`
- `git diff --check`: exit 0
- `bash -n scripts/verify/check-admin-foundation.sh`: exit 0
- LSP diagnostics: 3 files diagnosticCount 0, but `tsc skipped: no tsconfig found`
- AST-grep: NOT_RUN effectively, tool reports not installed
- secret scanners `git-secrets/gitleaks/detect-secrets/trufflehog`: NOT_AVAILABLE
- rg secret/PII scan on changed files: no matches

7. repetition result

반복 질문 여부는 미확인입니다. 이 감사는 제공된 현재 task payload, 지정 파일, git history, 저장소 증거만 사용했습니다. 별도 보관 대화 검색은 수행하지 않았습니다.

8. validation limits

`NOT_RUN`: Corepack provisioning, pnpm 11.22.0 execution, admin install, lint, typecheck, unit, build, start, CI, external services, push/PR/merge/deploy/email/calendar/ClickUp.

Ruby-less clean environment에서 canonical selector가 실행되는지는 검증하지 않았습니다. 현 verified environment에서는 Ruby JSON parser가 실행되어 PASS/RED/변이를 모두 재현했습니다.

9. prioritized next action

다음 micro로 진행 가능합니다: P0-04는 P0-03 PASS checkpoint를 dependency로 삼아야 합니다.

선택적 LOW hardening: `scripts/verify/check-admin-foundation.sh`의 `status` 변수를 selector 내부에서 초기화하거나 `if ! actual=...` 구조로 바꿔 ambient shell variable에 의한 거짓 실패를 제거하십시오.
