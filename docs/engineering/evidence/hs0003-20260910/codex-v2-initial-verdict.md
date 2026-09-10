VERDICT: FAIL

## Verdict
- FAIL

## Evidence
- `sha256sum docs/engineering/evidence/hs0003-20260910/claude-v1-response-final.md` — matched the provided V1 final SHA `232937ccb2dc91473c07091032aeb8916744aa9c4789008a685a0d95d1fe07fa`.
- `bash scripts/acceptance-hs-kickoff.sh` — current candidate baseline passed, `CHECKED: 12`, exit 0.
- `cd humansearch && uv run --no-sync pytest -q tests/test_hs_0003.py` — `15 passed`.
- `cd humansearch && uv run --no-sync pytest -q` — `277 passed`.
- `uv run --no-sync ruff check . && uv run --no-sync mypy .` — both passed.
- `bash scripts/acceptance-hs-kickoff-mutations.sh` — `CHECKED: 37`, exit 0.
- `bash scripts/acceptance-principles-check.sh` — `VERDICT: PASS`, `CHECKED: 34`.

핵심 반례는 baseline이 아니라 임시 사본 변형에서 나왔습니다.

| Case | Result | Meaning |
|---|---:|---|
| `PR #13` → `PR #13１` | rc=0 | V1 반례 재현. 전각 숫자 suffix가 붙어도 처분표가 통과합니다. |
| `PR #13` → `ｘPR #13` | rc=0 | V2 추가 반례. 전각 x prefix가 붙어도 처분표가 통과합니다. |
| workflow+SOT `hs-kickoff (` → `ｘhs-kickoff (` | rc=0 | V1의 “처분표만 해당” 판단이 틀렸습니다. workflow/SOT 필수 스텝 이름도 우회됩니다. |
| workflow+SOT `hѕ-kickoff (` | rc=1 | span 내부 위장은 잡습니다. |
| `PR #13` → ASCII `PR #131` | rc=1 | 기존 ASCII control은 유지됩니다. |

## Gaps
- 구현자가 제시한 묶음 지문 `07ce9970f7bce...`은 계산 방식이 없어서 재현하지 못했습니다. 파일별 SHA는 V1과 일치했지만, bundle hash 자체는 증명되지 않았습니다.
- V1의 13개 private mutant 중 `metadata-skip`은 임시 사본에서 재현했습니다. 메타데이터 비교를 죽여도 `tests/test_hs_0003.py`가 `15 passed`로 살아남습니다. SHA 선행 검사 때문에 blocker는 아닙니다.

## Risks
- 제품 후보는 그대로 커밋하면 안 됩니다. HS-00.03 종료 조건의 “전각·동형 문자로 착수 검사 대상 이름을 위장하는 입력 거부”를 만족하지 못합니다.

### Findings

| Finding | Status | Severity | Required for HS-00.03? | Evidence |
|---|---|---:|---:|---|
| raw 선택과 shadow 경계 불일치로 다른 이름이 보호 이름으로 인정됨 | REPRODUCED | 높음 | 예 | [check-hs-kickoff-identities.py](/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/hs-0003-20260910/scripts/verify/check-hs-kickoff-identities.py:138)는 shadow span 내부 치환만 실패로 봅니다. [acceptance-hs-kickoff.sh](/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/hs-0003-20260910/scripts/acceptance-hs-kickoff.sh:87)는 raw regex로 처분 행을 선택하고, [acceptance-hs-kickoff.sh](/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/hs-0003-20260910/scripts/acceptance-hs-kickoff.sh:227)는 raw substring으로 CI 배선을 찾습니다. |
| helper에 newline 하나만 들어오면 rc=0 | REPRODUCED | 낮음 | 단독으로는 아니오 | `printf '\n' | python3 scripts/verify/check-hs-kickoff-identities.py ...` → rc=0. 실제 empty disposition shell path는 rc=1로 실패했습니다. |
| invalid UTF-8 stdin이 helper에서 rc=0 | REPRODUCED | 낮음 | 단독으로는 아니오 | `printf 'hs-kickoff\377\n' \| python3 ...` → rc=0. 실제 disposition 파일 suffix invalid byte는 shell path에서 “PR #13 행 없음”으로 rc=1이었습니다. |
| metadata-skip mutant 생존 | REPRODUCED | 낮음 | 아니오 | metadata 비교를 `if False and ...`로 죽인 임시 사본도 `15 passed`. SHA 검사([check-hs-kickoff-identities.py](/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/hs-0003-20260910/scripts/verify/check-hs-kickoff-identities.py:61))가 먼저 막습니다. |

### V1 대비

| Topic | V1 | V2 |
|---|---|---|
| Overall verdict | PASS | FAIL |
| `PR #13１` | 재현, 계약 밖 중간 위험 | 재현, 계약 안쪽 종료 차단으로 판단 |
| workflow/SOT 우회 | 해당 없음 또는 통하지 않음 | `ｘhs-kickoff (`로 acceptance rc=0 재현 |
| normal controls | 유지 | 유지 확인 |
| empty newline | 낮음 | 재현, shell path는 별도 실패 |
| invalid UTF-8 | 낮음 | 재현, shell path는 별도 실패 |
| metadata-skip | 생존, blocker 아님 | 재현, blocker 아님 |
| bundle hash | 재현 못 함 | 재현 못 함 |

최종 판정: 현재 GREEN 후보는 커밋 가능한 상태가 아닙니다. raw 선택과 helper shadow 판정이 같은 비교 기준을 써야 하고, 특히 토큰 바로 앞뒤의 치환 문자가 shadow에서 ASCII 경계 문자가 되는 경우를 실패로 닫아야 합니다.
