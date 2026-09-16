#!/usr/bin/env ruby
# check-hs-0302-ci-wiring.rb — hs-0302 인수 검사의 CI 스텝이 "정확히 그 명령 하나"인가.
#
# 왜 문자열 검사로는 부족한가 (Codex V1 3차 실측): `if:`·`continue-on-error`·`run: echo`
# 만 찾으면 실행 줄 끝에 논리 OR 로 참을 덧붙이는 형태를 놓친다. 인수 검사가 실패해도
# 셸이 0 을 돌려주므로 CI 는 초록인데, 문자열 검사는 그것을 오류무시로 보지 않는다.
# 명령이 "있는가" 와 "실패가 전파되는가" 는 서로 다른 계약이다.
#
# 사용: ruby check-hs-0302-ci-wiring.rb <workflow.yml>
# 출력: WIRING_OK: ... (exit 0) | WIRING_BAD: ... (exit 1) | WIRING_ERROR: ... (exit 2)
#
# 판정 본문은 이 파일 한 곳에만 둔다. 인수 스크립트는 진짜 워크플로와 그 꼬리를 심은
# 임시 사본에 **같은 검사기**를 돌려 통과와 차단을 한 쌍으로 증명한다.
require 'psych'

NEEDLE = 'acceptance-hs-0302.sh'
EXPECTED_RUN = 'bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-0302.sh'
SHELL_OPERATORS = ['||', '&&', ';', '|', '$(', '`'].freeze

path = ARGV[0]
if path.nil? || !File.file?(path)
  puts "WIRING_ERROR: 워크플로 파일을 열 수 없다 — #{path.inspect}"
  exit 2
end

begin
  doc = Psych.load_file(path)
rescue StandardError => e
  puts "WIRING_ERROR: YAML 파싱 실패 — #{e.class}"
  exit 2
end

hits = []
((doc.is_a?(Hash) ? doc['jobs'] : nil) || {}).each do |job_name, job|
  (((job || {})['steps']) || []).each_with_index do |step, index|
    next unless step.is_a?(Hash)
    run = step['run']
    next unless run.is_a?(String) && run.include?(NEEDLE)
    hits << [job_name, index, step, run]
  end
end

if hits.size != 1
  puts "WIRING_BAD: hs-0302 실행 스텝이 #{hits.size}개 — 정확히 1개여야 한다"
  exit 1
end

job_name, index, step, run = hits[0]
problems = []
problems << "run 이 정확한 단일 명령이 아니다: #{run.strip.inspect}" unless run.strip == EXPECTED_RUN
SHELL_OPERATORS.each do |op|
  problems << "run 에 셸 제어 연산자 #{op} 가 있다" if run.include?(op)
end
problems << '조건부 스텝(if)이다' if step.key?('if')
problems << '오류를 무시한다(continue-on-error)' if step['continue-on-error']

if problems.empty?
  puts "WIRING_OK: #{job_name} 스텝 #{index} 의 run 이 정확한 단일 명령이다"
  exit 0
end
problems.each { |line| puts "WIRING_BAD: #{line}" }
exit 1
