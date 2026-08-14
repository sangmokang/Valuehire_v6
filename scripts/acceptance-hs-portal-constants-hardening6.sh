#!/usr/bin/env bash
# acceptance-hs-portal-constants-hardening6.sh — G3 CI 작업과 자동 실행 조건의 우회를
# 독립 표본으로 증명한다. 기존 RED 원장 3벌의 공격 내용과 기대값은 바꾸지 않는다.
#
# 계약:
#   N1 G3 명령을 담은 작업에 작업 수준 if 키가 있으면 정확히 exit 1
#   N2 G3 명령을 담은 작업에 작업 수준 continue-on-error: true가 있으면 정확히 exit 1
#   N3 워크플로가 수동 실행 전용이면 정확히 exit 1
#   N4 G3 단계·작업 기본값·워크플로 기본값의 shell 키가 있으면 정확히 exit 1
#   N5 G3 명령을 담은 작업에 runs-on 키가 없으면 정확히 exit 1
#   N6 G3 단계·작업 기본값·워크플로 기본값의 working-directory 키가 있으면 정확히 exit 1
#   N7 G3 단계·작업·워크플로 env의 BASH_ENV·ENV·SHELLOPTS·PATH 키가 있으면 정확히 exit 1
#   N8 runs-on은 비어 있지 않은 문자열 또는 그런 문자열의 비어 있지 않은 목록만 허용
#   다른 무해한 env 키는 허용하며 정확히 exit 0
#   정상 표본은 push와 pull_request 자동 실행 조건 및 runs-on을 가지며 정확히 exit 0
set -euo pipefail

unset GIT_DIR GIT_INDEX_FILE GIT_OBJECT_DIRECTORY GIT_WORK_TREE GIT_COMMON_DIR
unset GIT_ALTERNATE_OBJECT_DIRECTORIES

REPO=$(git rev-parse --show-toplevel) || {
  echo "FAIL: repository root unavailable"
  exit 1
}
cd "$REPO"

SCANNER_SOURCE=${G3_SCANNER_SOURCE:-scripts/acceptance-hs-portal-constants.sh}
GLOBAL_PATTERNS_SOURCE=${G3_GLOBAL_PATTERNS_SOURCE:-contracts/portal-constants-deny-patterns.txt}
PRODUCT_PATTERNS_SOURCE=${G3_PRODUCT_PATTERNS_SOURCE:-contracts/portal-constants-deny-patterns-product.txt}
MODE=${1:-all}

case "$MODE" in
  all|n1|n2|n3|step_shell|job_default_shell|workflow_default_shell|missing_runs_on|step_shell_duplicate|job_default_shell_duplicate|missing_runs_on_duplicate|step_shell_after_safe|job_default_shell_after_safe|missing_runs_on_after_safe|step_working_directory|job_default_working_directory|workflow_default_working_directory|step_bash_env|job_bash_env|workflow_bash_env|step_env|job_shellopts_env|workflow_path_env|safe_env|runs_on_null|runs_on_empty_list|runs_on_false) ;;
  *)
    echo "FAIL: usage: $0 [all|n1|n2|n3|step_shell|job_default_shell|workflow_default_shell|missing_runs_on|step_shell_duplicate|job_default_shell_duplicate|missing_runs_on_duplicate|step_shell_after_safe|job_default_shell_after_safe|missing_runs_on_after_safe|step_working_directory|job_default_working_directory|workflow_default_working_directory|step_bash_env|job_bash_env|workflow_bash_env|step_env|job_shellopts_env|workflow_path_env|safe_env|runs_on_null|runs_on_empty_list|runs_on_false]"
    exit 1
    ;;
esac

for required in "$SCANNER_SOURCE" "$GLOBAL_PATTERNS_SOURCE" "$PRODUCT_PATTERNS_SOURCE"; do
  if [ ! -f "$required" ]; then
    echo "FAIL: required G3 source missing: $required"
    exit 1
  fi
done
if ! command -v ruby >/dev/null 2>&1; then
  echo "FAIL: Ruby YAML parser unavailable"
  exit 1
fi

SNAP0=$(git status --porcelain)
SANDBOX=$(mktemp -d "$REPO/.g3-hardening6.XXXXXX")
cleanup() { rm -rf -- "$SANDBOX"; }
trap cleanup EXIT
trap 'cleanup; trap - EXIT; exit 143' TERM
trap 'cleanup; trap - EXIT; exit 130' INT
trap 'cleanup; trap - EXIT; exit 129' HUP

G3_NAMES="acceptance-hs-portal-constants acceptance-hs-portal-constants-mutations acceptance-hs-portal-constants-hardening acceptance-hs-portal-constants-hardening2 acceptance-hs-portal-constants-hardening3 acceptance-hs-portal-constants-hardening4 acceptance-hs-portal-constants-hardening5 acceptance-hs-portal-constants-hardening6"

write_commands() {
  local indent="$1" g
  for g in $G3_NAMES; do
    printf '%sbash scripts/%s.sh\n' "$indent" "$g"
  done
}

write_wf() {
  local d="$1" variant="$2"
  {
    printf 'name: verify\n'
    case "$variant" in
      n3)              printf 'on:\n  workflow_dispatch:\n' ;;
      n3_paths_ignore) printf 'on:\n  push:\n    paths-ignore:\n      - "**"\n  pull_request:\n    paths-ignore:\n      - "**"\n' ;;
      *)               printf 'on:\n  push:\n  pull_request:\n' ;;
    esac
    case "$variant" in
      workflow_default_shell)             printf 'defaults:\n  run:\n    shell: echo {0}\n' ;;
      workflow_default_working_directory) printf 'defaults:\n  run:\n    working-directory: fake-checks\n' ;;
      workflow_bash_env)                  printf 'env:\n  BASH_ENV: .g3-early-success.sh\n' ;;
      workflow_path_env)                  printf 'env:\n  PATH: /tmp/fake-bin\n' ;;
      safe_env)                           printf 'env:\n  SAFE_WORKFLOW_FLAG: enabled\n' ;;
    esac
    printf 'jobs:\n'
    if [ "$variant" = n1_needs ]; then
      printf '  gate:\n    runs-on: ubuntu-latest\n    if: false\n    steps:\n      - run: echo skipped\n'
      printf '  verify:\n    needs: gate\n'
    else
      printf '  verify:\n'
    fi
    case "$variant" in
      missing_runs_on|missing_runs_on_duplicate) ;;
      runs_on_null)                       printf '    runs-on:\n' ;;
      runs_on_empty_list)                 printf '    runs-on: []\n' ;;
      runs_on_false)                      printf '    runs-on: false\n' ;;
      *)                                  printf '    runs-on: ubuntu-latest\n' ;;
    esac
    case "$variant" in
      n1)            printf '    if: false\n' ;;
      n2)            printf '    continue-on-error: %s\n' 'true' ;;
      n2_expression) printf '    continue-on-error: ${{ true }}\n' ;;
      job_default_shell|job_default_shell_duplicate) printf '    defaults:\n      run:\n        shell: echo {0}\n' ;;
      job_default_working_directory)                 printf '    defaults:\n      run:\n        working-directory: fake-checks\n' ;;
      job_bash_env)                                  printf '    env:\n      BASH_ENV: .g3-early-success.sh\n' ;;
      job_shellopts_env)                             printf '    env:\n      SHELLOPTS: errexit\n' ;;
      safe_env)                                      printf '    env:\n      SAFE_JOB_FLAG: enabled\n' ;;
    esac
    printf '    steps:\n      - name: g3\n'
    case "$variant" in
      step_shell|step_shell_duplicate) printf '        shell: echo {0}\n' ;;
      step_working_directory)          printf '        working-directory: fake-checks\n' ;;
      step_bash_env)                    printf '        env:\n          BASH_ENV: .g3-early-success.sh\n' ;;
      step_env)                         printf '        env:\n          ENV: .g3-early-success.sh\n' ;;
      safe_env)                         printf '        env:\n          SAFE_STEP_FLAG: enabled\n' ;;
    esac
    printf '        run: |\n'
    write_commands '          '
    case "$variant" in
      step_shell_duplicate)
        printf '      - name: g3 duplicate safe step\n        run: |\n'
        write_commands '          '
        ;;
      job_default_shell_duplicate|missing_runs_on_duplicate)
        printf '  verify_backup:\n    runs-on: ubuntu-latest\n    steps:\n      - name: g3 duplicate safe job\n        run: |\n'
        write_commands '          '
        ;;
      step_shell_after_safe)
        printf '      - name: g3 unsafe step after safe step\n        shell: echo {0}\n        run: |\n'
        write_commands '          '
        ;;
      job_default_shell_after_safe)
        printf '  verify_unsafe:\n    runs-on: ubuntu-latest\n    defaults:\n      run:\n        shell: echo {0}\n    steps:\n      - name: g3 unsafe job after safe job\n        run: |\n'
        write_commands '          '
        ;;
      missing_runs_on_after_safe)
        printf '  verify_unsafe:\n    steps:\n      - name: g3 job missing runs-on after safe job\n        run: |\n'
        write_commands '          '
        ;;
    esac
  } > "$d/.github/workflows/verify.yml"
}

assert_fixture_shape() {
  local wf="$1" want_if="$2" want_coe="$3" want_auto="$4" shape
  shape=$(ruby -ryaml -e '
    data = YAML.safe_load(File.read(ARGV.fetch(0)), [], [], false)
    trigger = data.key?("on") ? data["on"] : data[true]
    events = case trigger
             when String then [trigger]
             when Array then trigger
             when Hash then trigger.keys
             else []
             end.map(&:to_s)
    job = data.fetch("jobs").fetch("verify")
    puts "JOB_IF=#{job.key?("if") ? job["if"] : "ABSENT"}"
    puts "JOB_CONTINUE_ON_ERROR=#{job.key?("continue-on-error") ? job["continue-on-error"] : "ABSENT"}"
    puts "AUTO_TRIGGER=#{events.any? { |event| ["push", "pull_request"].include?(event) }}"
  ' "$wf") || {
    echo "FAIL: hardening6 fixture is not valid YAML"
    exit 1
  }
  if [ "$shape" != "$(printf 'JOB_IF=%s\nJOB_CONTINUE_ON_ERROR=%s\nAUTO_TRIGGER=%s' "$want_if" "$want_coe" "$want_auto")" ]; then
    echo "FAIL: hardening6 fixture has the wrong YAML ownership"
    printf '%s\n' "$shape"
    exit 1
  fi
  printf '%s\n' "$shape"
}

assert_n1_needs_shape() {
  local wf="$1" shape
  shape=$(ruby -ryaml -e '
    data = YAML.safe_load(File.read(ARGV.fetch(0)), [], [], false)
    jobs = data.fetch("jobs")
    puts "G3_JOB_NEEDS=#{jobs.fetch("verify").fetch("needs", "ABSENT")}"
    gate = jobs.fetch("gate")
    puts "GATE_IF=#{gate.key?("if") ? gate["if"] : "ABSENT"}"
  ' "$wf") || {
    echo "FAIL: hardening6 N1 needs fixture is not valid YAML"
    exit 1
  }
  if [ "$shape" != $'G3_JOB_NEEDS=gate\nGATE_IF=false' ]; then
    echo "FAIL: hardening6 N1 needs fixture has the wrong YAML ownership"
    printf '%s\n' "$shape"
    exit 1
  fi
  printf '%s\n' "$shape"
}

assert_n2_expression_shape() {
  local wf="$1" shape
  shape=$(ruby -ryaml -e '
    data = YAML.safe_load(File.read(ARGV.fetch(0)), [], [], false)
    value = data.fetch("jobs").fetch("verify").fetch("continue-on-error")
    puts "JOB_CONTINUE_ON_ERROR_CLASS=#{value.class}"
    puts "JOB_CONTINUE_ON_ERROR=#{value}"
  ' "$wf") || {
    echo "FAIL: hardening6 N2 expression fixture is not valid YAML"
    exit 1
  }
  if [ "$shape" != "$(printf 'JOB_CONTINUE_ON_ERROR_CLASS=String\nJOB_CONTINUE_ON_ERROR=%s' '${{ true }}')" ]; then
    echo "FAIL: hardening6 N2 expression fixture has the wrong YAML ownership"
    printf '%s\n' "$shape"
    exit 1
  fi
  printf '%s\n' "$shape"
}

assert_n3_paths_ignore_shape() {
  local wf="$1" shape
  shape=$(ruby -ryaml -e '
    data = YAML.safe_load(File.read(ARGV.fetch(0)), [], [], false)
    trigger = data.key?("on") ? data["on"] : data[true]
    puts "PUSH_PATHS_IGNORE=#{trigger.fetch("push").fetch("paths-ignore").join(",")}"
    puts "PULL_REQUEST_PATHS_IGNORE=#{trigger.fetch("pull_request").fetch("paths-ignore").join(",")}"
  ' "$wf") || {
    echo "FAIL: hardening6 N3 filtered fixture is not valid YAML"
    exit 1
  }
  if [ "$shape" != $'PUSH_PATHS_IGNORE=**\nPULL_REQUEST_PATHS_IGNORE=**' ]; then
    echo "FAIL: hardening6 N3 filtered fixture has the wrong YAML ownership"
    printf '%s\n' "$shape"
    exit 1
  fi
  printf '%s\n' "$shape"
}

assert_execution_shape() {
  local wf="$1" want_runs_on="$2" want_step_shell="$3"
  local want_job_shell="$4" want_workflow_shell="$5" shape
  shape=$(ruby -ryaml -e '
    data = YAML.safe_load(File.read(ARGV.fetch(0)), [], [], false)
    job = data.fetch("jobs").fetch("verify")
    step = job.fetch("steps").find do |candidate|
      candidate.is_a?(Hash) && candidate["run"].to_s.include?("acceptance-hs-portal-constants.sh")
    end
    abort "G3 step missing" unless step
    job_defaults = job["defaults"]
    workflow_defaults = data["defaults"]
    puts "RUNS_ON=#{job.fetch("runs-on", "ABSENT")}"
    puts "STEP_SHELL=#{step.fetch("shell", "ABSENT")}"
    puts "JOB_DEFAULT_SHELL=#{job_defaults.is_a?(Hash) && job_defaults["run"].is_a?(Hash) ? job_defaults["run"].fetch("shell", "ABSENT") : "ABSENT"}"
    puts "WORKFLOW_DEFAULT_SHELL=#{workflow_defaults.is_a?(Hash) && workflow_defaults["run"].is_a?(Hash) ? workflow_defaults["run"].fetch("shell", "ABSENT") : "ABSENT"}"
  ' "$wf") || {
    echo "FAIL: hardening6 execution fixture is not valid YAML"
    exit 1
  }
  if [ "$shape" != "$(printf 'RUNS_ON=%s\nSTEP_SHELL=%s\nJOB_DEFAULT_SHELL=%s\nWORKFLOW_DEFAULT_SHELL=%s' \
    "$want_runs_on" "$want_step_shell" "$want_job_shell" "$want_workflow_shell")" ]; then
    echo "FAIL: hardening6 execution fixture has the wrong YAML ownership"
    printf '%s\n' "$shape"
    exit 1
  fi
  printf '%s\n' "$shape"
}

assert_working_directory_shape() {
  local wf="$1" want_step="$2" want_job="$3" want_workflow="$4" shape
  shape=$(ruby -ryaml -e '
    data = YAML.safe_load(File.read(ARGV.fetch(0)), [], [], false)
    job = data.fetch("jobs").fetch("verify")
    step = job.fetch("steps").find { |candidate| candidate.is_a?(Hash) && candidate["run"].to_s.include?("acceptance-hs-portal-constants.sh") }
    abort "G3 step missing" unless step
    job_run = job["defaults"].is_a?(Hash) ? job["defaults"]["run"] : nil
    workflow_run = data["defaults"].is_a?(Hash) ? data["defaults"]["run"] : nil
    puts "STEP_WORKING_DIRECTORY=#{step.fetch("working-directory", "ABSENT")}"
    puts "JOB_DEFAULT_WORKING_DIRECTORY=#{job_run.is_a?(Hash) ? job_run.fetch("working-directory", "ABSENT") : "ABSENT"}"
    puts "WORKFLOW_DEFAULT_WORKING_DIRECTORY=#{workflow_run.is_a?(Hash) ? workflow_run.fetch("working-directory", "ABSENT") : "ABSENT"}"
  ' "$wf") || {
    echo "FAIL: hardening6 working-directory fixture is not valid YAML"
    exit 1
  }
  if [ "$shape" != "$(printf 'STEP_WORKING_DIRECTORY=%s\nJOB_DEFAULT_WORKING_DIRECTORY=%s\nWORKFLOW_DEFAULT_WORKING_DIRECTORY=%s' "$want_step" "$want_job" "$want_workflow")" ]; then
    echo "FAIL: hardening6 working-directory fixture has the wrong YAML ownership"
    printf '%s\n' "$shape"
    exit 1
  fi
  printf '%s\n' "$shape"
}

assert_env_shape() {
  local wf="$1" want_step="$2" want_job="$3" want_workflow="$4" shape
  shape=$(ruby -ryaml -e '
    data = YAML.safe_load(File.read(ARGV.fetch(0)), [], [], false)
    job = data.fetch("jobs").fetch("verify")
    step = job.fetch("steps").find { |candidate| candidate.is_a?(Hash) && candidate["run"].to_s.include?("acceptance-hs-portal-constants.sh") }
    abort "G3 step missing" unless step
    keys = ->(owner) { owner.is_a?(Hash) && owner["env"].is_a?(Hash) ? owner["env"].keys.map(&:to_s).sort.join(",") : "ABSENT" }
    puts "STEP_ENV_KEYS=#{keys.call(step)}"
    puts "JOB_ENV_KEYS=#{keys.call(job)}"
    puts "WORKFLOW_ENV_KEYS=#{keys.call(data)}"
  ' "$wf") || {
    echo "FAIL: hardening6 env fixture is not valid YAML"
    exit 1
  }
  if [ "$shape" != "$(printf 'STEP_ENV_KEYS=%s\nJOB_ENV_KEYS=%s\nWORKFLOW_ENV_KEYS=%s' "$want_step" "$want_job" "$want_workflow")" ]; then
    echo "FAIL: hardening6 env fixture has the wrong YAML ownership"
    printf '%s\n' "$shape"
    exit 1
  fi
  printf '%s\n' "$shape"
}

assert_runs_on_shape() {
  local wf="$1" want_class="$2" want_value="$3" shape
  shape=$(ruby -ryaml -e '
    value = YAML.safe_load(File.read(ARGV.fetch(0)), [], [], false).fetch("jobs").fetch("verify").fetch("runs-on")
    puts "RUNS_ON_CLASS=#{value.class}"
    puts "RUNS_ON_VALUE=#{value.inspect}"
  ' "$wf") || {
    echo "FAIL: hardening6 runs-on fixture is not valid YAML"
    exit 1
  }
  if [ "$shape" != "$(printf 'RUNS_ON_CLASS=%s\nRUNS_ON_VALUE=%s' "$want_class" "$want_value")" ]; then
    echo "FAIL: hardening6 runs-on fixture has the wrong YAML value"
    printf '%s\n' "$shape"
    exit 1
  fi
  printf '%s\n' "$shape"
}

assert_duplicate_shape() {
  local wf="$1" expected="$2" shape
  shape=$(ruby -ryaml -e '
    data = YAML.safe_load(File.read(ARGV.fetch(0)), [], [], false)
    g3_jobs = data.fetch("jobs").values.select do |job|
      job.is_a?(Hash) && job["steps"].is_a?(Array) && job["steps"].any? do |step|
        step.is_a?(Hash) && step["run"].to_s.include?("acceptance-hs-portal-constants.sh")
      end
    end
    g3_steps = g3_jobs.flat_map do |job|
      job["steps"].select do |step|
        step.is_a?(Hash) && step["run"].to_s.include?("acceptance-hs-portal-constants.sh")
      end
    end
    puts "G3_JOBS=#{g3_jobs.length}"
    puts "G3_STEPS=#{g3_steps.length}"
    puts "RUNS_ON=#{g3_jobs.map { |job| job.fetch("runs-on", "ABSENT") }.join(",")}"
    puts "STEP_SHELLS=#{g3_steps.map { |step| step.fetch("shell", "ABSENT") }.join(",")}"
    puts "JOB_DEFAULT_SHELLS=#{g3_jobs.map { |job| job["defaults"].is_a?(Hash) && job["defaults"]["run"].is_a?(Hash) ? job["defaults"]["run"].fetch("shell", "ABSENT") : "ABSENT" }.join(",")}"
  ' "$wf") || {
    echo "FAIL: hardening6 duplicate fixture is not valid YAML"
    exit 1
  }
  if [ "$shape" != "$expected" ]; then
    echo "FAIL: hardening6 duplicate fixture has the wrong YAML ownership"
    printf '%s\n' "$shape"
    exit 1
  fi
  printf '%s\n' "$shape"
}

total=0
blocked=0
allowed=0
wiring=0
CASE_DIR=""

init_case() {
  total=$((total + 1))
  CASE_DIR="$SANDBOX/case-$total"
  mkdir -p "$CASE_DIR/scripts" "$CASE_DIR/contracts" "$CASE_DIR/hooks" \
    "$CASE_DIR/.github/workflows" "$CASE_DIR/humansearch/src/humansearch" \
    "$CASE_DIR/humansearch/tests" "$CASE_DIR/lib" "$CASE_DIR/.tmp" \
    "$CASE_DIR/fake-checks/scripts"
  git -C "$CASE_DIR" init -q
  cp "$SCANNER_SOURCE" "$CASE_DIR/scripts/acceptance-hs-portal-constants.sh"
  local f
  for f in mutations hardening hardening2 hardening3 hardening4 hardening5 hardening6; do
    printf '#!/usr/bin/env bash\n# wiring probe placeholder\n' \
      > "$CASE_DIR/scripts/acceptance-hs-portal-constants-$f.sh"
  done
  local fake_name
  for fake_name in $G3_NAMES; do
    printf '#!/usr/bin/env bash\n%s %s\n' 'exit' '0' \
      > "$CASE_DIR/fake-checks/scripts/$fake_name.sh"
    chmod +x "$CASE_DIR/fake-checks/scripts/$fake_name.sh"
  done
  printf '%s %s\n' 'exit' '0' > "$CASE_DIR/.g3-early-success.sh"
  cp "$GLOBAL_PATTERNS_SOURCE" "$CASE_DIR/contracts/portal-constants-deny-patterns.txt"
  cp "$PRODUCT_PATTERNS_SOURCE" "$CASE_DIR/contracts/portal-constants-deny-patterns-product.txt"
  cp hooks/pre-push "$CASE_DIR/hooks/pre-push"
  chmod +x "$CASE_DIR/hooks/pre-push"
  write_wf "$CASE_DIR" ok
  printf 'PACKAGE_NAME = "humansearch"\n' > "$CASE_DIR/humansearch/src/humansearch/__init__.py"
  printf 'def test_boundary():\n    assert True\n' > "$CASE_DIR/humansearch/tests/test_boundary.py"
  local i
  for i in 1 2 3 4 5 6 7 8; do
    printf 'safe fixture %s\n' "$i" > "$CASE_DIR/lib/filler-$i.txt"
  done
  git -C "$CASE_DIR" add -A
}

run_scanner() {
  SCAN_RC=0
  SCAN_OUT=$(cd "$CASE_DIR" && TMPDIR="$CASE_DIR/.tmp" \
    bash scripts/acceptance-hs-portal-constants.sh 2>&1) || SCAN_RC=$?
}

expect_case() {
  local label="$1" want="$2" needle="$3"
  run_scanner
  if [ "$SCAN_RC" -ne "$want" ]; then
    echo "FAIL: hardening6 [$label] exit=$SCAN_RC (기대: 정확히 $want)"
    printf '%s\n' "$SCAN_OUT"
    exit 1
  fi
  if ! printf '%s\n' "$SCAN_OUT" | grep -qE "$needle"; then
    echo "FAIL: hardening6 [$label] 이유가 다르다 (exit=$SCAN_RC)"
    printf '%s\n' "$SCAN_OUT"
    exit 1
  fi
  case "$want" in
    0) allowed=$((allowed + 1)) ;;
    1) blocked=$((blocked + 1)) ;;
  esac
  printf 'ok [%s] exit=%s\n' "$label" "$want"
}

WIRE_RE='^FAIL: ci/pre-push wiring broken [1-9][0-9]*$'

init_case
assert_fixture_shape "$CASE_DIR/.github/workflows/verify.yml" ABSENT ABSENT true
assert_execution_shape "$CASE_DIR/.github/workflows/verify.yml" ubuntu-latest ABSENT ABSENT ABSENT
expect_case "hardening6 baseline" 0 '^PASS: ci/pre-push wiring intact$'

if [ "$MODE" = all ] || [ "$MODE" = step_working_directory ]; then
  init_case
  write_wf "$CASE_DIR" step_working_directory
  git -C "$CASE_DIR" add -A
  assert_working_directory_shape "$CASE_DIR/.github/workflows/verify.yml" fake-checks ABSENT ABSENT
  expect_case "N6 step-level working-directory key" 1 "$WIRE_RE"
fi

if [ "$MODE" = all ] || [ "$MODE" = job_default_working_directory ]; then
  init_case
  write_wf "$CASE_DIR" job_default_working_directory
  git -C "$CASE_DIR" add -A
  assert_working_directory_shape "$CASE_DIR/.github/workflows/verify.yml" ABSENT fake-checks ABSENT
  expect_case "N6 job defaults.run.working-directory key" 1 "$WIRE_RE"
fi

if [ "$MODE" = all ] || [ "$MODE" = workflow_default_working_directory ]; then
  init_case
  write_wf "$CASE_DIR" workflow_default_working_directory
  git -C "$CASE_DIR" add -A
  assert_working_directory_shape "$CASE_DIR/.github/workflows/verify.yml" ABSENT ABSENT fake-checks
  expect_case "N6 workflow defaults.run.working-directory key" 1 "$WIRE_RE"
fi

if [ "$MODE" = all ] || [ "$MODE" = step_bash_env ]; then
  init_case
  write_wf "$CASE_DIR" step_bash_env
  git -C "$CASE_DIR" add -A
  assert_env_shape "$CASE_DIR/.github/workflows/verify.yml" BASH_ENV ABSENT ABSENT
  expect_case "N7 step env BASH_ENV key" 1 "$WIRE_RE"
fi

if [ "$MODE" = all ] || [ "$MODE" = job_bash_env ]; then
  init_case
  write_wf "$CASE_DIR" job_bash_env
  git -C "$CASE_DIR" add -A
  assert_env_shape "$CASE_DIR/.github/workflows/verify.yml" ABSENT BASH_ENV ABSENT
  expect_case "N7 job env BASH_ENV key" 1 "$WIRE_RE"
fi

if [ "$MODE" = all ] || [ "$MODE" = workflow_bash_env ]; then
  init_case
  write_wf "$CASE_DIR" workflow_bash_env
  git -C "$CASE_DIR" add -A
  assert_env_shape "$CASE_DIR/.github/workflows/verify.yml" ABSENT ABSENT BASH_ENV
  expect_case "N7 workflow env BASH_ENV key" 1 "$WIRE_RE"
fi

if [ "$MODE" = all ] || [ "$MODE" = step_env ]; then
  init_case
  write_wf "$CASE_DIR" step_env
  git -C "$CASE_DIR" add -A
  assert_env_shape "$CASE_DIR/.github/workflows/verify.yml" ENV ABSENT ABSENT
  expect_case "N7 step env ENV key" 1 "$WIRE_RE"
fi

if [ "$MODE" = all ] || [ "$MODE" = job_shellopts_env ]; then
  init_case
  write_wf "$CASE_DIR" job_shellopts_env
  git -C "$CASE_DIR" add -A
  assert_env_shape "$CASE_DIR/.github/workflows/verify.yml" ABSENT SHELLOPTS ABSENT
  expect_case "N7 job env SHELLOPTS key" 1 "$WIRE_RE"
fi

if [ "$MODE" = all ] || [ "$MODE" = workflow_path_env ]; then
  init_case
  write_wf "$CASE_DIR" workflow_path_env
  git -C "$CASE_DIR" add -A
  assert_env_shape "$CASE_DIR/.github/workflows/verify.yml" ABSENT ABSENT PATH
  expect_case "N7 workflow env PATH key" 1 "$WIRE_RE"
fi

if [ "$MODE" = all ] || [ "$MODE" = safe_env ]; then
  init_case
  write_wf "$CASE_DIR" safe_env
  git -C "$CASE_DIR" add -A
  assert_env_shape "$CASE_DIR/.github/workflows/verify.yml" SAFE_STEP_FLAG SAFE_JOB_FLAG SAFE_WORKFLOW_FLAG
  expect_case "harmless env keys remain allowed" 0 '^PASS: ci/pre-push wiring intact$'
fi

if [ "$MODE" = all ] || [ "$MODE" = runs_on_null ]; then
  init_case
  write_wf "$CASE_DIR" runs_on_null
  git -C "$CASE_DIR" add -A
  assert_runs_on_shape "$CASE_DIR/.github/workflows/verify.yml" NilClass nil
  expect_case "N8 runs-on null" 1 "$WIRE_RE"
fi

if [ "$MODE" = all ] || [ "$MODE" = runs_on_empty_list ]; then
  init_case
  write_wf "$CASE_DIR" runs_on_empty_list
  git -C "$CASE_DIR" add -A
  assert_runs_on_shape "$CASE_DIR/.github/workflows/verify.yml" Array '[]'
  expect_case "N8 runs-on empty list" 1 "$WIRE_RE"
fi

if [ "$MODE" = all ] || [ "$MODE" = runs_on_false ]; then
  init_case
  write_wf "$CASE_DIR" runs_on_false
  git -C "$CASE_DIR" add -A
  assert_runs_on_shape "$CASE_DIR/.github/workflows/verify.yml" FalseClass false
  expect_case "N8 runs-on false" 1 "$WIRE_RE"
fi

if [ "$MODE" = all ] || [ "$MODE" = step_shell ]; then
  init_case
  write_wf "$CASE_DIR" step_shell
  git -C "$CASE_DIR" add .github/workflows/verify.yml
  assert_execution_shape "$CASE_DIR/.github/workflows/verify.yml" ubuntu-latest 'echo {0}' ABSENT ABSENT
  expect_case "N4 step-level shell key" 1 "$WIRE_RE"
fi

if [ "$MODE" = all ] || [ "$MODE" = job_default_shell ]; then
  init_case
  write_wf "$CASE_DIR" job_default_shell
  git -C "$CASE_DIR" add .github/workflows/verify.yml
  assert_execution_shape "$CASE_DIR/.github/workflows/verify.yml" ubuntu-latest ABSENT 'echo {0}' ABSENT
  expect_case "N4 job defaults.run.shell key" 1 "$WIRE_RE"
fi

if [ "$MODE" = all ] || [ "$MODE" = workflow_default_shell ]; then
  init_case
  write_wf "$CASE_DIR" workflow_default_shell
  git -C "$CASE_DIR" add .github/workflows/verify.yml
  assert_execution_shape "$CASE_DIR/.github/workflows/verify.yml" ubuntu-latest ABSENT ABSENT 'echo {0}'
  expect_case "N4 workflow defaults.run.shell key" 1 "$WIRE_RE"
fi

if [ "$MODE" = all ] || [ "$MODE" = missing_runs_on ]; then
  init_case
  write_wf "$CASE_DIR" missing_runs_on
  git -C "$CASE_DIR" add .github/workflows/verify.yml
  assert_execution_shape "$CASE_DIR/.github/workflows/verify.yml" ABSENT ABSENT ABSENT ABSENT
  expect_case "N5 missing runs-on key" 1 "$WIRE_RE"
fi

if [ "$MODE" = all ] || [ "$MODE" = step_shell_duplicate ]; then
  init_case
  write_wf "$CASE_DIR" step_shell_duplicate
  git -C "$CASE_DIR" add .github/workflows/verify.yml
  assert_duplicate_shape "$CASE_DIR/.github/workflows/verify.yml" $'G3_JOBS=1\nG3_STEPS=2\nRUNS_ON=ubuntu-latest\nSTEP_SHELLS=echo {0},ABSENT\nJOB_DEFAULT_SHELLS=ABSENT'
  expect_case "N4 bad step plus duplicate safe step" 1 "$WIRE_RE"
fi

if [ "$MODE" = all ] || [ "$MODE" = job_default_shell_duplicate ]; then
  init_case
  write_wf "$CASE_DIR" job_default_shell_duplicate
  git -C "$CASE_DIR" add .github/workflows/verify.yml
  assert_duplicate_shape "$CASE_DIR/.github/workflows/verify.yml" $'G3_JOBS=2\nG3_STEPS=2\nRUNS_ON=ubuntu-latest,ubuntu-latest\nSTEP_SHELLS=ABSENT,ABSENT\nJOB_DEFAULT_SHELLS=echo {0},ABSENT'
  expect_case "N4 bad job defaults plus duplicate safe job" 1 "$WIRE_RE"
fi

if [ "$MODE" = all ] || [ "$MODE" = missing_runs_on_duplicate ]; then
  init_case
  write_wf "$CASE_DIR" missing_runs_on_duplicate
  git -C "$CASE_DIR" add .github/workflows/verify.yml
  assert_duplicate_shape "$CASE_DIR/.github/workflows/verify.yml" $'G3_JOBS=2\nG3_STEPS=2\nRUNS_ON=ABSENT,ubuntu-latest\nSTEP_SHELLS=ABSENT,ABSENT\nJOB_DEFAULT_SHELLS=ABSENT,ABSENT'
  expect_case "N5 missing runs-on plus duplicate safe job" 1 "$WIRE_RE"
fi

if [ "$MODE" = all ] || [ "$MODE" = step_shell_after_safe ]; then
  init_case
  write_wf "$CASE_DIR" step_shell_after_safe
  git -C "$CASE_DIR" add .github/workflows/verify.yml
  assert_duplicate_shape "$CASE_DIR/.github/workflows/verify.yml" $'G3_JOBS=1\nG3_STEPS=2\nRUNS_ON=ubuntu-latest\nSTEP_SHELLS=ABSENT,echo {0}\nJOB_DEFAULT_SHELLS=ABSENT'
  expect_case "N4 unsafe step after duplicate safe step" 1 "$WIRE_RE"
fi

if [ "$MODE" = all ] || [ "$MODE" = job_default_shell_after_safe ]; then
  init_case
  write_wf "$CASE_DIR" job_default_shell_after_safe
  git -C "$CASE_DIR" add .github/workflows/verify.yml
  assert_duplicate_shape "$CASE_DIR/.github/workflows/verify.yml" $'G3_JOBS=2\nG3_STEPS=2\nRUNS_ON=ubuntu-latest,ubuntu-latest\nSTEP_SHELLS=ABSENT,ABSENT\nJOB_DEFAULT_SHELLS=ABSENT,echo {0}'
  expect_case "N4 unsafe job defaults after duplicate safe job" 1 "$WIRE_RE"
fi

if [ "$MODE" = all ] || [ "$MODE" = missing_runs_on_after_safe ]; then
  init_case
  write_wf "$CASE_DIR" missing_runs_on_after_safe
  git -C "$CASE_DIR" add .github/workflows/verify.yml
  assert_duplicate_shape "$CASE_DIR/.github/workflows/verify.yml" $'G3_JOBS=2\nG3_STEPS=2\nRUNS_ON=ubuntu-latest,ABSENT\nSTEP_SHELLS=ABSENT,ABSENT\nJOB_DEFAULT_SHELLS=ABSENT,ABSENT'
  expect_case "N5 missing runs-on after duplicate safe job" 1 "$WIRE_RE"
fi

if [ "$MODE" = all ] || [ "$MODE" = n1 ]; then
  init_case
  write_wf "$CASE_DIR" n1
  git -C "$CASE_DIR" add .github/workflows/verify.yml
  assert_fixture_shape "$CASE_DIR/.github/workflows/verify.yml" false ABSENT true
  expect_case "N1 job-level if key" 1 "$WIRE_RE"

  init_case
  write_wf "$CASE_DIR" n1_needs
  git -C "$CASE_DIR" add .github/workflows/verify.yml
  assert_n1_needs_shape "$CASE_DIR/.github/workflows/verify.yml"
  expect_case "N1 skipped prerequisite job" 1 "$WIRE_RE"
fi

if [ "$MODE" = all ] || [ "$MODE" = n2 ]; then
  init_case
  write_wf "$CASE_DIR" n2
  git -C "$CASE_DIR" add .github/workflows/verify.yml
  assert_fixture_shape "$CASE_DIR/.github/workflows/verify.yml" ABSENT true true
  expect_case "N2 job-level continue-on-error true" 1 "$WIRE_RE"

  init_case
  write_wf "$CASE_DIR" n2_expression
  git -C "$CASE_DIR" add .github/workflows/verify.yml
  assert_n2_expression_shape "$CASE_DIR/.github/workflows/verify.yml"
  expect_case "N2 job-level continue-on-error expression" 1 "$WIRE_RE"
fi

if [ "$MODE" = all ] || [ "$MODE" = n3 ]; then
  init_case
  write_wf "$CASE_DIR" n3
  git -C "$CASE_DIR" add .github/workflows/verify.yml
  assert_fixture_shape "$CASE_DIR/.github/workflows/verify.yml" ABSENT ABSENT false
  expect_case "N3 workflow_dispatch-only trigger" 1 "$WIRE_RE"

  init_case
  write_wf "$CASE_DIR" n3_paths_ignore
  git -C "$CASE_DIR" add .github/workflows/verify.yml
  assert_n3_paths_ignore_shape "$CASE_DIR/.github/workflows/verify.yml"
  expect_case "N3 automatic events filtered out" 1 "$WIRE_RE"
fi

if [ "$MODE" = all ]; then
  total=$((total + 1))
  if ! grep -v '^[[:space:]]*#' .github/workflows/verify.yml | grep -qE \
    '^[[:space:]]*bash scripts/acceptance-hs-portal-constants-hardening6\.sh[[:space:]]*$'; then
    echo "FAIL: hardening6 자신이 CI 실행 줄에 없다"
    exit 1
  fi
  blocked=$((blocked + 1))
  wiring=1
  printf 'ok [%s]\n' "hardening6 자기 배선(CI 실행 줄)"
fi

cleanup
trap - EXIT
SNAP1=$(git status --porcelain)
if [ "$SNAP0" != "$SNAP1" ]; then
  echo "FAIL: hardening6 시험이 원본 저장소를 변형했다"
  exit 1
fi

echo "PASS: portal-constants hardening6 cases $total (blocked-mutations $((blocked - wiring)), clean-baselines $allowed, wiring-present $wiring)"
