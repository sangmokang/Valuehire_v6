#!/usr/bin/env bash
# check-ci-step-integrity.sh — 서버 자동검사의 스텝을 조용히 끄지 못하게 한다.
#
# 왜 필요한가:
#   hooks/pre-push 는 워크플로를 문자열로 훑어 `if: false` 만 잡는다. 그래서
#   `if: ${{ false }}`, `if: github.event_name == 'never'`, `continue-on-error: true`
#   같은 변형은 그대로 통과했다(2026-08-12 V1 D4 실측: 데이터 노출 검사 스텝을 영구히
#   꺼도 인수검사·pre-commit·pre-push 가 전부 초록이었다).
#   문자열 규칙은 하나 추가할 때마다 우회가 하나씩 는다. 그래서 여기서는 워크플로를
#   실제 YAML 로 파싱해 "조건이 붙었는가 / 실패를 무시하는가"를 구조로 본다.
#
# 계약: verify 워크플로의 모든 job·step 은 조건 없이 실행되고 실패를 전파해야 한다.
#       정당한 예외는 이 파일에 이유와 함께 적고, 적히지 않은 예외는 전부 불합격이다.
#
# 막지 못하는 것: 스텝 자체를 삭제하는 것. 그것은 mechanism-registry 와 pre-push 의
#       실행줄 검사가 맡는다. 여기서 다 막는다고 주장하지 않는다.
set -uo pipefail

WORKFLOW="${1:-.github/workflows/verify.yml}"
if [ ! -f "$WORKFLOW" ]; then
  echo "FAIL: 워크플로 파일이 없다 — $WORKFLOW (fail-closed)"
  echo "CHECKED: 0"
  exit 2
fi

ruby -rpsych -rdate -e '
workflow_path = ARGV[0]

# 이름으로 지정한 예외. 이유 없이 늘리지 않는다.
ALLOWED_STEP_IF = {
  "인수 검사 0-5 (push · CI 연결)" =>
    "origin/main==main 을 보는 검사라 main push 에서만 의미가 있다. PR 실행에서 요구하면 상시 실패한다.",
}

begin
  doc = Psych.safe_load(File.read(workflow_path), aliases: true, permitted_classes: [Date, Time])
rescue Psych::Exception => e
  puts "FAIL: 워크플로 파싱 실패 — #{e.message.lines.first.to_s.strip}"
  puts "CHECKED: 0"
  exit 2
end

errors = []
checked = 0

jobs = doc.is_a?(Hash) ? doc["jobs"] : nil
unless jobs.is_a?(Hash) && !jobs.empty?
  puts "FAIL: jobs 를 읽지 못했다 — 검사 대상 0개는 합격이 아니다"
  puts "CHECKED: 0"
  exit 2
end

jobs.each do |job_name, job|
  next unless job.is_a?(Hash)
  checked += 1
  errors << "JOB_CONDITIONAL: jobs.#{job_name} 에 if 가 있다 — job 을 통째로 끌 수 있다" if job.key?("if")
  errors << "JOB_CONTINUE_ON_ERROR: jobs.#{job_name} 이 실패를 무시한다" if job["continue-on-error"]

  steps = job["steps"]
  unless steps.is_a?(Array) && !steps.empty?
    errors << "JOB_NO_STEPS: jobs.#{job_name} 에 스텝이 없다 — 빈 job 은 항상 초록이다"
    next
  end

  steps.each_with_index do |step, i|
    next unless step.is_a?(Hash)
    checked += 1
    label = step["name"] || step["uses"] || "steps[#{i}]"

    if step.key?("if")
      reason = ALLOWED_STEP_IF[step["name"]]
      if reason
        puts "ALLOWED: #{label} — if 허용 (#{reason})"
      else
        errors << "STEP_CONDITIONAL: jobs.#{job_name}.#{label} 에 if 가 있다 (#{step["if"].inspect}) — " \
                  "조건부 스텝은 조건이 거짓이면 실행되지 않고도 초록이다"
      end
    end

    if step["continue-on-error"]
      errors << "STEP_CONTINUE_ON_ERROR: jobs.#{job_name}.#{label} 이 실패를 무시한다 — " \
                "빨개져야 할 검사가 초록으로 남는다"
    end

    run = step["run"]
    if run.is_a?(String)
      # 실행처럼 보이지만 실행하지 않는 형태.
      run.each_line do |line|
        stripped = line.strip
        next if stripped.empty? || stripped.start_with?("#")
        if stripped =~ /\Aecho\s+(bash|sh)\s+\S+\.sh/
          errors << "STEP_ECHO_ONLY: jobs.#{job_name}.#{label} 의 `#{stripped}` 는 실행이 아니라 출력이다"
        end
        if stripped =~ /\A(bash|sh)\s+-n\s+\S+\.sh/
          errors << "STEP_SYNTAX_ONLY: jobs.#{job_name}.#{label} 의 `#{stripped}` 는 문법 검사일 뿐 실행이 아니다"
        end
      end
    end
  end
end

if errors.empty?
  puts "PASS: 조건부·오류무시 스텝 없음 (job·step #{checked}개 검사)"
  puts "CHECKED: #{checked}"
  exit 0
else
  errors.each { |e| puts "FAIL: #{e}" }
  puts "CHECKED: #{checked}"
  exit 1
end
' "$WORKFLOW"
