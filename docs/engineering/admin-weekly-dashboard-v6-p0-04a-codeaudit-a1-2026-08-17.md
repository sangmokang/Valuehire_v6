## 1. verdict

감사자 ID: `/root/p0_04a_codeaudit_a1`.

**REQUEST_CHANGES.** P0-04A의 실제 ignore 구현은 목표 숫자 `5/5/0/5`로 통과하지만, RED와 후보 커밋 둘 다 Lore trailer를 실제 줄이 아니라 리터럴 `\n` 한 줄로 넣었습니다. 사용자가 명시적으로 금지한 계약 위반이라 합격 불가입니다.

추가로 tracked canary 변이는 `trackedForbiddenArtifactCount=1`을 잡지만 실패 사유가 `tracked-forbidden-artifact`가 아니라 `required-path-not-ignored`로 먼저 떨어집니다. 차단은 되지만 실패 이유가 부정확합니다.

## 2. matrix

| ID | 요구/주장 | 판정 | 근거 | 공백/반증 | 심각도 |
|---|---|---|---|---|---|
| R1 | 후보 HEAD와 원본 요청 해시 확인 | 구현 확인 | HEAD `02c7f0e`; original sha256 `b00f700...c9da` | 없음 | 없음 |
| R2 | 허용 파일 3개만 변경 | 구현 확인 | `base..candidate`: `.gitignore`, goal doc, `scripts/verify/check-admin-foundation.sh` | app/package/lock/CI diff 0 | 없음 |
| R3 | RED는 의도 실패 | 구현 확인 | RED exit 1, `required=5 checked=2 tracked=0 target=5` | 없음 | 없음 |
| R4 | 후보 canonical GREEN | 구현 확인 | candidate exit 0, `required=5 checked=5 tracked=0 target=5` | 없음 | 없음 |
| R5 | 기존 ignore 보존 + 최소 추가 | 구현 확인 | `.gitignore:16-18`은 `/apps/admin/test-results/`, `/playwright-report/`, `/coverage/`만 추가 | 삭제된 기존 규칙 없음 | 없음 |
| R6 | Lore trailer는 실제 git-native여야 함 | 불일치 | raw commit line 4와 parsed trailer가 `Constraint:` 한 값에 `\nRejected:\nConfidence:`를 포함 | RED/후보 모두 동일 | 높음: 감사 추적 계약 실패 |
| R7 | tracked artifact adversarial RED | 부분 구현 | force-add canary 후 exit 1, `trackedForbiddenArtifactCount=1` | reason이 `tracked-forbidden-artifact`가 아니라 `required-path-not-ignored` | 중간: 원인 진단 혼선 |
| R8 | parent AC-01 remains partial | 구현 확인 | controller `:200`이 AC-01에 P0-02~P0-12/P0-04A 포함 명시 | admin lifecycle NOT_RUN | 없음 |

## 3. key-flow

생산 경로는 문서와 코드가 맞습니다: synthetic path 목록은 `scripts/verify/check-admin-foundation.sh:104-110`에 5개로 고정되고, `:115-119`에서 `git check-ignore`, `:121-127`에서 `git ls-files` 추적 산출물 스캔을 합니다. 후보 `.gitignore:16-18`은 누락된 admin 테스트 산출물 3개만 anchored rule로 추가합니다.

독립 검사도 `git check-ignore -v`가 5개 모두 exit 0을 반환했고, `git ls-files -- node_modules apps/admin/.next apps/admin/test-results apps/admin/playwright-report apps/admin/coverage` 결과 count는 0이었습니다. 정상 소스 경로 `apps/admin/package.json`, `apps/admin/src/app/page.tsx`, `package.json`, 스크립트, 문서는 check-ignore exit 1이라 숨지 않았습니다.

## 4. missed-better-answer

작성자가 놓친 더 좋은 처리 2개가 있습니다.

첫째, 커밋 메시지는 `git interpret-trailers --parse`로 확인했어야 합니다. 현재는 `Constraint:` 하나의 값 안에 모든 trailer가 들어가므로 Lore protocol을 만족하지 않습니다.

둘째, tracked artifact 검사에서는 `git check-ignore`가 tracked/index 파일을 기본적으로 ignore 대상으로 세지 않는 특성을 반영해야 합니다. `git check-ignore --no-index`로 ignore rule coverage를 따로 증명하거나, tracked scan을 먼저 검사해 `reason=tracked-forbidden-artifact`를 정확히 내는 편이 낫습니다.

## 5. adversarial rebuttal

강한 반론: “후보 구현은 실제로 5개 경로를 무시하고 tracked count도 0이므로 실사용 문제는 없다.”

반박 후 결론: 맞습니다. 런타임 ignore 기능 자체는 통과입니다. 그러나 이번 계약은 구현뿐 아니라 RED/후보 커밋의 Lore trailer 형식까지 PASS BAR에 포함했고, “리터럴 `\n`은 대체물이 아니다”라고 못 박았습니다. 따라서 micro 구현은 양호하지만 제출물은 계약 실패입니다.

## 6. evidence ledger

- disposable locator: `/tmp/p0-04a-codeaudit.keDW0l/repo`, `/tmp/p0-04a-codeaudit.keDW0l/verify-repo`, `/tmp/p0-04a-mutations.YSF0Is`
- base `7e7fe3`: node/pnpm/root selectors exit 0; `artifact-ignore` unsupported exit 2
- RED `3963ad7`: canonical exit 1, `5/2/0/5`, reason `required-path-not-ignored`
- candidate `02c7f0e`: canonical exit 0, `5/5/0/5`, reason `null`
- regression clone: node 0, pnpm 0, root 0, artifact 0, `bash -n` 0, `git diff --check` 0, `session-status` 0 with clone `RED: 2/19`, `verify.sh` 0, `acceptance-0-2` 2
- source topology: status clean, `session-status` 0 with `RED: 1/19`, `acceptance-0-2` 2, `verify.sh` 0
- mutations: remove `node_modules/` exit 1 `5/4/0/5`; remove `.next/` exit 1 `5/4/0/5`; force-add tracked canary exit 1 `5/4/1/5`
- parsed trailers: `git interpret-trailers --parse` exit 0 but parses one malformed `Constraint:` value containing literal `\n`; separate `Rejected`, `Confidence`, `Scope-risk`, `Directive`, `Tested`, `Not-tested` trailers are not real records
- exposure scan: modified files only flagged `.gitignore:26` `.secret-patterns` rule name; no exposed secret value found
- NOT_RUN: admin install/lint/typecheck/unit/build/start/CI/artifact generation/network/install/external services
- external effects: 0 outside local disposable clones; source status remained clean

## 7. repetition

반복 질문 조사는 이번 범위 요구가 아니어서 저장 세션 검색은 하지 않았습니다. 현재 감사는 제공된 P0-04A 계약과 로컬 저장소 증거만 대상으로 했습니다.

## 8. limits

`acceptance-0-2`는 source와 clone 모두 exit 2입니다. 이는 `.secret-patterns` 없음/빈 파일 때문이며, 계약에 명시된 parent partial/baseline RED로 분리했습니다. 실제 admin lifecycle과 CI는 의도적으로 실행하지 않았으므로 AC-01 전체 완료는 증명하지 않습니다.

LSP 진단은 대상이 `.gitignore`, shell, markdown이라 실행 가능한 언어 서버 검사가 없었습니다. 대신 `bash -n`, canonical selectors, diff-check, mutation tests를 실행했습니다.

## 9. prioritized next action

1. RED와 후보 커밋 메시지를 amend/recreate해서 Lore trailers를 실제 개별 줄로 저장하십시오.
2. tracked artifact branch는 tracked scan을 먼저 실패시키거나 `git check-ignore --no-index`를 써서 `checkedIgnoredPathCount=5, trackedForbiddenArtifactCount=1, reason=tracked-forbidden-artifact`가 나오게 고치십시오.
3. 같은 canonical/regression/mutation 명령을 다시 돌려 P0-04A를 재감사하십시오.
