# 검증 권한 최종 로컬 실행 로그 — 2026-08-19

대상 구현 커밋: `16f75a5e9695d69d2075a1c48cc4e1a19aa1c410`

아래는 명령 전문, 출력 전문, 종료값입니다. 로컬 결과의 상태는 `POLICY_REVIEW_REQUIRED`이며 공식 원격 판정이 아닙니다.

```text
$ bash -n scripts/acceptance-verification-authority.sh
EXIT=0
$ bash -n scripts/verify/run-verification-authority-mutations.sh
EXIT=0
$ ruby -c scripts/verify/verification_authority.rb
Syntax OK
EXIT=0
$ ruby -c scripts/verify/verification_authority/mutations.rb
Syntax OK
EXIT=0
$ ruby -c scripts/verify/verification_authority/recovery.rb
Syntax OK
EXIT=0
$ ruby -e require "yaml"; ARGV.each { |path| YAML.safe_load(File.read(path), aliases: false); puts "YAML_OK: #{path}" } -- .github/workflows/verify.yml docs/sot/verification-protected-surface.yaml docs/sot/verification-requirements.yaml scripts/verify/fixtures/verification-authority/sha/01-valid-pr-head.yaml scripts/verify/fixtures/verification-authority/sha/02-old-check-sha.yaml scripts/verify/fixtures/verification-authority/sha/03-pr-head-changed.yaml scripts/verify/fixtures/verification-authority/sha/04-check-name-mismatch.yaml scripts/verify/fixtures/verification-authority/sha/05-workflow-mismatch.yaml scripts/verify/fixtures/verification-authority/sha/06-missing-sha.yaml scripts/verify/fixtures/verification-authority/sha/07-incomplete-check.yaml scripts/verify/fixtures/verification-authority/sha/08-valid-merge-group.yaml scripts/verify/fixtures/verification-authority/sha/09-forged-success.yaml scripts/verify/fixtures/verification-authority/sha/10-unrelated-merge-group.yaml scripts/verify/fixtures/verification-authority/sha/11-protected-change.yaml scripts/verify/fixtures/verification-authority/recovery/01-second-target-failure.yaml scripts/verify/fixtures/verification-authority/recovery/02-permission-restore-failure.yaml scripts/verify/fixtures/verification-authority/recovery/03-state-write-failure.yaml scripts/verify/fixtures/verification-authority/recovery/04-partial-corruption.yaml scripts/verify/fixtures/verification-authority/recovery/05-forced-termination.yaml scripts/verify/fixtures/verification-authority/recovery/06-recovery-fails-again.yaml scripts/verify/fixtures/verification-authority/recovery/07-delete-attempt.yaml
YAML_OK: .github/workflows/verify.yml
YAML_OK: docs/sot/verification-protected-surface.yaml
YAML_OK: docs/sot/verification-requirements.yaml
YAML_OK: scripts/verify/fixtures/verification-authority/sha/01-valid-pr-head.yaml
YAML_OK: scripts/verify/fixtures/verification-authority/sha/02-old-check-sha.yaml
YAML_OK: scripts/verify/fixtures/verification-authority/sha/03-pr-head-changed.yaml
YAML_OK: scripts/verify/fixtures/verification-authority/sha/04-check-name-mismatch.yaml
YAML_OK: scripts/verify/fixtures/verification-authority/sha/05-workflow-mismatch.yaml
YAML_OK: scripts/verify/fixtures/verification-authority/sha/06-missing-sha.yaml
YAML_OK: scripts/verify/fixtures/verification-authority/sha/07-incomplete-check.yaml
YAML_OK: scripts/verify/fixtures/verification-authority/sha/08-valid-merge-group.yaml
YAML_OK: scripts/verify/fixtures/verification-authority/sha/09-forged-success.yaml
YAML_OK: scripts/verify/fixtures/verification-authority/sha/10-unrelated-merge-group.yaml
YAML_OK: scripts/verify/fixtures/verification-authority/sha/11-protected-change.yaml
YAML_OK: scripts/verify/fixtures/verification-authority/recovery/01-second-target-failure.yaml
YAML_OK: scripts/verify/fixtures/verification-authority/recovery/02-permission-restore-failure.yaml
YAML_OK: scripts/verify/fixtures/verification-authority/recovery/03-state-write-failure.yaml
YAML_OK: scripts/verify/fixtures/verification-authority/recovery/04-partial-corruption.yaml
YAML_OK: scripts/verify/fixtures/verification-authority/recovery/05-forced-termination.yaml
YAML_OK: scripts/verify/fixtures/verification-authority/recovery/06-recovery-fails-again.yaml
YAML_OK: scripts/verify/fixtures/verification-authority/recovery/07-delete-attempt.yaml
EXIT=0
$ ruby -e require "psych"; ARGV.each { |path| Psych.safe_load(File.read(path), [], [], false); puts "PSYCH_OK: #{path}" } -- .github/workflows/verify.yml docs/sot/verification-protected-surface.yaml docs/sot/verification-requirements.yaml scripts/verify/fixtures/verification-authority/sha/01-valid-pr-head.yaml scripts/verify/fixtures/verification-authority/sha/02-old-check-sha.yaml scripts/verify/fixtures/verification-authority/sha/03-pr-head-changed.yaml scripts/verify/fixtures/verification-authority/sha/04-check-name-mismatch.yaml scripts/verify/fixtures/verification-authority/sha/05-workflow-mismatch.yaml scripts/verify/fixtures/verification-authority/sha/06-missing-sha.yaml scripts/verify/fixtures/verification-authority/sha/07-incomplete-check.yaml scripts/verify/fixtures/verification-authority/sha/08-valid-merge-group.yaml scripts/verify/fixtures/verification-authority/sha/09-forged-success.yaml scripts/verify/fixtures/verification-authority/sha/10-unrelated-merge-group.yaml scripts/verify/fixtures/verification-authority/sha/11-protected-change.yaml scripts/verify/fixtures/verification-authority/recovery/01-second-target-failure.yaml scripts/verify/fixtures/verification-authority/recovery/02-permission-restore-failure.yaml scripts/verify/fixtures/verification-authority/recovery/03-state-write-failure.yaml scripts/verify/fixtures/verification-authority/recovery/04-partial-corruption.yaml scripts/verify/fixtures/verification-authority/recovery/05-forced-termination.yaml scripts/verify/fixtures/verification-authority/recovery/06-recovery-fails-again.yaml scripts/verify/fixtures/verification-authority/recovery/07-delete-attempt.yaml
PSYCH_OK: .github/workflows/verify.yml
PSYCH_OK: docs/sot/verification-protected-surface.yaml
PSYCH_OK: docs/sot/verification-requirements.yaml
PSYCH_OK: scripts/verify/fixtures/verification-authority/sha/01-valid-pr-head.yaml
PSYCH_OK: scripts/verify/fixtures/verification-authority/sha/02-old-check-sha.yaml
PSYCH_OK: scripts/verify/fixtures/verification-authority/sha/03-pr-head-changed.yaml
PSYCH_OK: scripts/verify/fixtures/verification-authority/sha/04-check-name-mismatch.yaml
PSYCH_OK: scripts/verify/fixtures/verification-authority/sha/05-workflow-mismatch.yaml
PSYCH_OK: scripts/verify/fixtures/verification-authority/sha/06-missing-sha.yaml
PSYCH_OK: scripts/verify/fixtures/verification-authority/sha/07-incomplete-check.yaml
PSYCH_OK: scripts/verify/fixtures/verification-authority/sha/08-valid-merge-group.yaml
PSYCH_OK: scripts/verify/fixtures/verification-authority/sha/09-forged-success.yaml
PSYCH_OK: scripts/verify/fixtures/verification-authority/sha/10-unrelated-merge-group.yaml
PSYCH_OK: scripts/verify/fixtures/verification-authority/sha/11-protected-change.yaml
PSYCH_OK: scripts/verify/fixtures/verification-authority/recovery/01-second-target-failure.yaml
PSYCH_OK: scripts/verify/fixtures/verification-authority/recovery/02-permission-restore-failure.yaml
PSYCH_OK: scripts/verify/fixtures/verification-authority/recovery/03-state-write-failure.yaml
PSYCH_OK: scripts/verify/fixtures/verification-authority/recovery/04-partial-corruption.yaml
PSYCH_OK: scripts/verify/fixtures/verification-authority/recovery/05-forced-termination.yaml
PSYCH_OK: scripts/verify/fixtures/verification-authority/recovery/06-recovery-fails-again.yaml
PSYCH_OK: scripts/verify/fixtures/verification-authority/recovery/07-delete-attempt.yaml
EXIT=0
$ bash scripts/acceptance-verification-authority.sh --output /tmp/verification-authority-final-report.json
$ ruby scripts/verify/verification_authority.rb authority-check
PROTECTED: paths=12 enforcement=DETECT_ONLY external=4
AUTHORITY: llm_report=FAIL candidate_policy_official_token=0 protected=DETECT_ONLY
EXIT=0
$ ruby scripts/verify/verification_authority.rb contract-self-test
CONTRACT_SELF_TEST: negative_cases=6 blocked=6
EXIT=0
$ ruby scripts/verify/verification_authority.rb wiring-check
WIRING: ci_direct=1 pre_push_runtime=1 artifact=1
EXIT=0
$ bash scripts/verify/run-verification-authority-mutations.sh
BLOCKED: verifier_early_exit_zero
  broke: verifier line 2 exits zero before checking
  command: bash scripts/acceptance-verification-authority.sh
  actual_exit: 1
  expected: early verifier exit must fail the real acceptance and pre-push entrypoint
  survived: false
BLOCKED: ci_echo_command
  broke: CI direct command is replaced with echo
  command: ruby scripts/verify/verification_authority.rb wiring-check
  actual_exit: 1
  expected: echo is not direct execution
  survived: false
BLOCKED: ci_comment_only
  broke: CI command remains only as a comment
  command: ruby scripts/verify/verification_authority.rb wiring-check
  actual_exit: 1
  expected: comment-only command must not count as wiring
  survived: false
BLOCKED: ci_dead_code_before_command
  broke: CI exits successfully before the verifier command
  command: ruby scripts/verify/verification_authority.rb wiring-check
  actual_exit: 1
  expected: an earlier successful exit must make the verifier dead code
  survived: false
BLOCKED: artifact_sha_unbound
  broke: artifact identity is no longer bound to the target SHA
  command: ruby scripts/verify/verification_authority.rb wiring-check
  actual_exit: 1
  expected: artifact name and path must both bind to github.sha
  survived: false
BLOCKED: output_sha_comment_only
  broke: output path is fixed while GITHUB_SHA remains only in a comment
  command: ruby scripts/verify/verification_authority.rb wiring-check
  actual_exit: 1
  expected: GITHUB_SHA in a comment must not validate a fixed output path
  survived: false
BLOCKED: required_checker_deleted
  broke: required checker file is deleted
  command: ruby scripts/verify/verification_authority.rb contract-self-test
  actual_exit: 1
  expected: deleted checker cannot validate
  survived: false
BLOCKED: required_registry_renamed
  broke: canonical requirements registry is renamed
  command: ruby scripts/verify/verification_authority.rb contract-self-test
  actual_exit: 1
  expected: canonical registry name is required
  survived: false
BLOCKED: mutation_case_deleted
  broke: one required mutation ID is deleted
  command: ruby scripts/verify/verification_authority.rb mutation-catalog-check
  actual_exit: 1
  expected: required mutation ID deletion must fail
  survived: false
BLOCKED: mutation_case_and_expected_count_lowered
  broke: mutation ID and expected count are lowered together
  command: ruby scripts/verify/verification_authority.rb mutation-catalog-check
  actual_exit: 1
  expected: lowering case and count together must fail intrinsic inventory
  survived: false
BLOCKED: counterexample_emptied
  broke: a requirement counterexample list is emptied
  command: ruby scripts/verify/verification_authority.rb contract-self-test
  actual_exit: 1
  expected: empty counterexample must fail closed schema
  survived: false
BLOCKED: verifier_wiring_removed
  broke: verifier path text remains while execution wiring is removed
  command: ruby scripts/verify/verification_authority.rb wiring-check
  actual_exit: 1
  expected: path existence without an executed stage must fail
  survived: false
BLOCKED: manifest_and_checker_weakened
  broke: protected manifest and checker inventory are weakened together
  command: ruby scripts/verify/verification_authority.rb protected-check
  actual_exit: 1
  expected: contract inventory must catch manifest and checker joint weakening
  survived: false
BLOCKED: authority_implicit_verified_backdoor
  broke: candidate policy implicitly returns VERIFIED without return syntax
  command: ruby scripts/verify/verification_authority.rb authority-check
  actual_exit: 1
  expected: implicit official-state backdoor must fail candidate-policy inspection
  survived: false
BLOCKED: mutation_runner_early_success
  broke: mutation runner prints a forged summary and returns before cases run
  command: bash scripts/acceptance-verification-authority.sh
  actual_exit: 1
  expected: forged mutation summary without per-case evidence must fail the outer verifier
  survived: false
BLOCKED: verified_sha_replaced_with_old_sha
  broke: successful check SHA is replaced with an old SHA
  command: ruby scripts/verify/verification_authority.rb sha-one scripts/verify/fixtures/verification-authority/sha/02-old-check-sha.yaml
  actual_exit: 0
  expected: old successful check must become STALE
  survived: false
BLOCKED: pr_head_sha_changed
  broke: PR head moves while old evidence is reused
  command: ruby scripts/verify/verification_authority.rb sha-one scripts/verify/fixtures/verification-authority/sha/03-pr-head-changed.yaml
  actual_exit: 0
  expected: changed PR head must make old evidence STALE
  survived: false
BLOCKED: required_check_name_changed
  broke: required check name is changed
  command: ruby scripts/verify/verification_authority.rb sha-one scripts/verify/fixtures/verification-authority/sha/04-check-name-mismatch.yaml
  actual_exit: 0
  expected: required check mismatch must FAIL
  survived: false
BLOCKED: workflow_identity_changed
  broke: workflow identity is changed
  command: ruby scripts/verify/verification_authority.rb sha-one scripts/verify/fixtures/verification-authority/sha/05-workflow-mismatch.yaml
  actual_exit: 0
  expected: workflow identity mismatch must FAIL
  survived: false
BLOCKED: forged_success_fixture
  broke: LLM report forges a successful GitHub check value
  command: ruby scripts/verify/verification_authority.rb sha-one scripts/verify/fixtures/verification-authority/sha/09-forged-success.yaml
  actual_exit: 0
  expected: LLM or local forged success must FAIL authority source
  survived: false
BLOCKED: rollback_permission_restore_failure
  broke: permission restoration fails during rollback
  command: ruby scripts/verify/verification_authority.rb recovery-one permission_restore_failure
  actual_exit: 0
  expected: permission restore failure must retain state
  survived: false
BLOCKED: rollback_state_delete_attempt
  broke: incomplete rollback tries to delete its state file
  command: ruby scripts/verify/verification_authority.rb recovery-one delete_attempt
  actual_exit: 0
  expected: incomplete rollback state deletion must be refused
  survived: false
CONTROL_OK: normal_control
  broke: clean isolated repository control
  command: ruby scripts/verify/verification_authority.rb verify-all --no-mutations
  actual_exit: 0
  expected: clean control must run all non-recursive checks
  survived: not_applicable
  original_repository_unchanged[verifier_early_exit_zero]: true
  original_repository_unchanged[ci_echo_command]: true
  original_repository_unchanged[ci_comment_only]: true
  original_repository_unchanged[ci_dead_code_before_command]: true
  original_repository_unchanged[artifact_sha_unbound]: true
  original_repository_unchanged[output_sha_comment_only]: true
  original_repository_unchanged[required_checker_deleted]: true
  original_repository_unchanged[required_registry_renamed]: true
  original_repository_unchanged[mutation_case_deleted]: true
  original_repository_unchanged[mutation_case_and_expected_count_lowered]: true
  original_repository_unchanged[counterexample_emptied]: true
  original_repository_unchanged[verifier_wiring_removed]: true
  original_repository_unchanged[manifest_and_checker_weakened]: true
  original_repository_unchanged[authority_implicit_verified_backdoor]: true
  original_repository_unchanged[mutation_runner_early_success]: true
  original_repository_unchanged[verified_sha_replaced_with_old_sha]: true
  original_repository_unchanged[pr_head_sha_changed]: true
  original_repository_unchanged[required_check_name_changed]: true
  original_repository_unchanged[workflow_identity_changed]: true
  original_repository_unchanged[forged_success_fixture]: true
  original_repository_unchanged[rollback_permission_restore_failure]: true
  original_repository_unchanged[rollback_state_delete_attempt]: true
  original_repository_unchanged[normal_control]: true
MUTATIONS: total=23 blocked=22 survived=0 controls=1
EXIT=0
$ ruby scripts/verify/verification_authority.rb sha-fixtures
SHA_CASE: 01-valid-pr-head.yaml expected=LOCAL_CANDIDATE actual=LOCAL_CANDIDATE
SHA_CASE: 02-old-check-sha.yaml expected=STALE actual=STALE
SHA_CASE: 03-pr-head-changed.yaml expected=STALE actual=STALE
SHA_CASE: 04-check-name-mismatch.yaml expected=FAIL actual=FAIL
SHA_CASE: 05-workflow-mismatch.yaml expected=FAIL actual=FAIL
SHA_CASE: 06-missing-sha.yaml expected=FAIL actual=FAIL
SHA_CASE: 07-incomplete-check.yaml expected=UNVERIFIED actual=UNVERIFIED
SHA_CASE: 08-valid-merge-group.yaml expected=LOCAL_CANDIDATE actual=LOCAL_CANDIDATE
SHA_CASE: 09-forged-success.yaml expected=FAIL actual=FAIL
SHA_CASE: 10-unrelated-merge-group.yaml expected=FAIL actual=FAIL
SHA_CASE: 11-protected-change.yaml expected=POLICY_REVIEW_REQUIRED actual=POLICY_REVIEW_REQUIRED
SHA_FIXTURES: total=11 states=FAIL,LOCAL_CANDIDATE,POLICY_REVIEW_REQUIRED,STALE,UNVERIFIED
EXIT=0
$ ruby scripts/verify/verification_authority.rb recovery-fixtures
RECOVERY_CASE: second_target_failure status=SECOND_TARGET_FAILED state_present=true
RECOVERY_CASE: permission_restore_failure status=PERMISSION_RESTORE_FAILED state_present=true
RECOVERY_CASE: state_write_failure status=STATE_WRITE_FAILED state_present=true
RECOVERY_CASE: partial_corruption status=CORRUPT state_present=true
RECOVERY_CASE: forced_termination status=KILLED state_present=true
RECOVERY_CASE: recovery_fails_again status=RECOVERY_FAILED_AGAIN state_present=true
RECOVERY_CASE: rollback_state_delete_attempt status=DELETE_REFUSED state_present=true
RECOVERY_CASE: repeated_recover status=RECOVERED state_present=false attempts=idempotent
RECOVERY_FIXTURES: total=8
EXIT=0
$ ruby scripts/verify/verification_authority.rb derived-state-check
DERIVED_STATE: tamper_overwritten=1 required_fields=6
EXIT=0
$ ruby scripts/verify/verification_authority.rb structural-limit-check
STRUCTURAL_LIMIT: three_way_survived=true enforcement=DETECT_ONLY original_unchanged=true
EXIT=0
AUTHORITY_RESULT: POLICY_REVIEW_REQUIRED
TARGET_SHA: 16f75a5e9695d69d2075a1c48cc4e1a19aa1c410
WORKFLOW_IDENTITY: .github/workflows/verify.yml@verify
REQUIRED_CHECK: verify
UNREGISTERED: 22
MUTATION_SURVIVED: 0
REPORT: /tmp/verification-authority-final-report.json
EXIT=0
$ bash verify.sh
PASS: no secret-pattern match in any tracked file, .env not tracked
EXIT=0
$ bash hooks/pre-commit
EXIT=0
$ git diff --check
EXIT=0
$ git diff --check origin/main...HEAD
EXIT=0
$ git status --porcelain
EXIT=0
OVERALL_EXIT=0
```
