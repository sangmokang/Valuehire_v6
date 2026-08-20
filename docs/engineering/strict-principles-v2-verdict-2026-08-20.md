# Strict 원칙 새 맥락 Codex V2 판정 — 2026-08-20

V2_VERDICT: PASS

## Verdict

- PASS
- OVERALL_STRICT: PASS, with ledger finalization pending
- Canonical agent identifier: `/root/strict_principles_v2_final_r2`

## Evidence

- Direct SOT load: `docs/sot/coding-principles.md` has P1-P22 at lines 16-37, §1-B-1..5 at lines 45-49, V-1..5 at lines 55-59, and direct-load rule at line 63.
- `docs/sot/principles.yaml` has the same 32 IDs, each with `mechanism_found` including `stages: ["strict", "pre-push", "ci"]`.
- `hooks/pre-push:47` directly runs `bash scripts/acceptance-principles-check.sh`.
- `.github/workflows/verify.yml:28-29` runs the same command unconditionally in CI.
- `scripts/verify/check-pre-push-runtime.sh:28-45` uses random temp/probe/marker/exit values; lines 72-75 require all three runtime signals: hook exit `1`, marker file, and exact `BLOCKED` output.

Command results:

```text
bash scripts/acceptance-principles-check.sh
exit 0
VERDICT: PASS
MECHANISMS: PASS 32/32 strict-contract-bindings
WIRING: PASS pre-push=1 ci=1
CHECKED: 32
```

```text
bash scripts/acceptance-principles-mutations.sh
exit 0
CHECKED: 40
VERDICT: PASS
```

This covered deletion, missing/empty SOT, duplicate/unknown IDs, self-exclusion, zero-target, comment/echo/dead-code/if-false/fingerprint/path-fingerprint, CI weakening, false verdict, artifact missing/hash mismatch, memory missing/truncated, and 500/501 boundary.

```text
bash scripts/verify/check-mechanism-registry.sh
exit 0
CHECKED: 6
```

```text
bash scripts/acceptance-verify-ac-m.sh
exit 0
CHECKED: 31
```

```text
bash scripts/verify/check-strict-principles-skills.sh
exit 0
VERDICT: PASS
COMMON_CONTRACT: PASS byte-identical
ENGINE_ORDER: PASS Codex/Claude platform-only difference
LINES: codex=306 claude=306
CHECKED: 2
```

```text
bash scripts/acceptance-guard-global-skill-files.sh
exit 0
CHECKED: 8
```

```text
bash verify.sh
exit 0
PASS: no secret-pattern match in any tracked file, .env not tracked
```

Runtime proof reattack, scratch-only and cleaned:

```text
marker_swallow: rejected exit=1
output_exit_only: rejected exit=1
output_only: rejected exit=1
exit_only: rejected exit=1
found_not_executed: rejected exit=1
SCRATCH_ABSENT_EXIT=0
```

V1 evidence:

- Raw Claude log exists and hash matches the V1 report:
  `bc602b90052543ae1adffa211a5de8d39f68594081738bc509507b3f8786fc9a`.
- V1 report lines 563-645 record final Claude V1 `VERDICT: PASS`, CLI exit `0`, `api_error_status: null`, and the same command counts I reproduced: 32, 40, 6, 31, 2, and `verify.sh` PASS.

## Gaps at V2 completion

The checked-in verdict ledger was stale before finalization:

```text
bash scripts/verify/check-strict-verdict-ledger.sh
exit 1
VERDICT: FAIL
ARTIFACT_HASH_MISMATCH: v1=docs/engineering/strict-principles-v1-verdict-2026-08-20.md
CHECKED: 4
FAILURES: 1
```

Current V1 artifact hash differed from the old ledger, which still stored stale `V1=NOT_RUN`. Per the V2 task contract, this expected pre-finalization state did not fail the code verdict and must be updated after this report.

## Risks

- Guard limitation is real and documented: same-UID users can still forge content plus state; acceptance reproduces that as a known limit, not a hidden bypass.
- Existing V1 notes mention a broader “OS temp directory class” detection idea; V2 agreed with V1 not counting that as a defect because it is not a concrete fixed fingerprint or explicit contract breach.
- Worktree contamination check: final `git status --porcelain=v1` matched the initial status; guard state files were absent after unlock.

## 커밋 상태 secret scan 수정 후 V2 재확인

```text
V2_RECHECK: PASS
OVERALL_STRICT: PASS
Canonical verifier: /root/strict_principles_v2_final_r2
```

최종 통합 검사에서 미추적 runtime helper가 커밋되면 기존 secret scanner가 `MARKER_TOKEN="..."`을 자격증명 대입 형태로 차단하는 결함을 발견했다. 구현자는 기능을 바꾸지 않고 변수명을 `MARKER_PROOF`로 수정했다. V2가 이 최소 변경을 읽기 전용으로 재검증했다.

```text
bash -n verification scripts + hooks/pre-push                  exit 0
bash scripts/verify/check-pre-push-runtime.sh                  exit 0
bash scripts/acceptance-principles-check.sh                    exit 0, CHECKED 32
bash scripts/acceptance-principles-mutations.sh                exit 0, CHECKED 40
bash scripts/verify/check-mechanism-registry.sh                exit 0, CHECKED 6
bash scripts/acceptance-verify-ac-m.sh                          exit 0, CHECKED 31
bash scripts/verify/check-strict-principles-skills.sh          exit 0, CHECKED 2
bash scripts/acceptance-guard-global-skill-files.sh            exit 0, CHECKED 8
bash verify.sh                                                 exit 0
isolated tracked-file secret scan                              exit 0
```

V2는 marker file의 정확한 `MARKER_PROOF`, hook exit 1, 정확한 `BLOCKED` 출력의 3중 조건이 그대로 유지됨을 확인했다. comment/output/exit-only, found-but-not-executed, swallowed-failure scratch 공격은 모두 helper exit 1이었다. guard는 `lock→check→unlock` 모두 exit 0, 상태 파일 없음, 전역 스킬 모드 644 복구를 확인했다. 저장소 파일은 수정하지 않았다.
