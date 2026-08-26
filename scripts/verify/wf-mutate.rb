# wf-mutate.rb — 워크플로 사본에 무력화를 주입한다 (인수 검사 전용 도구).
#
# 왜 별 파일인가: 주입 코드를 인수 검사 안에 인라인 루비 문자열로 두면 셸 따옴표가 세 겹이
# 되어 읽을 수도 고칠 수도 없고, 무엇보다 **주입이 조용히 빗나가도 알 수 없다**.
# 2026-08-27 에 실제로 그 일이 있었다(워크플로에 id: 줄 하나가 늘자 sub 가 아무것도 바꾸지
# 못했고, 공격하지 않은 원본이 그대로 통과해 "막았다"로 기록될 뻔했다).
#
# 계약: 주입이 실제로 파일을 바꾸지 못하면 **exit 1**. 호출자는 그것을 "공격 실패"로
#       다뤄야 하며 합격으로 세면 안 된다.
#
# 사용법: ruby wf-mutate.rb <workflow.yml> <종류> [인자...]
#   append-run  <문자열>            필수 대상 스텝 run 끝에 이어 붙인다
#   prepend-run <문자열>            그 스텝 run 앞에 한 줄 넣는다
#   wrap-run    <틀>                run 전체를 틀로 감싼다. 틀 안의 CMD 가 원래 명령으로 치환된다
#   step-shell  <step id> <shell>   그 스텝에 shell 을 지정한다
#   job-shell   <job id>  <shell>   그 job 의 defaults.run.shell 을 지정한다
#   workflow-shell <shell>          최상위 defaults.run.shell 을 지정한다
#   trigger-filter <트리거> <키> <값>  트리거를 남기고 도달 불가 필터를 건다
#   true-key            원문 `on:` 은 그대로 두고 최상위 `true:` 키를 덧붙인다
#                       (YAML 1.1 에서 `on` 이 boolean 으로 읽히는 것을 이용한 충돌)
#   contains-echo <step id> <조각>   그 스텝의 run 을 조각을 인용한 echo 한 줄로 바꾼다

require "psych"

TARGET_STEP = "hs-a4".freeze

path = ARGV[0]
kind = ARGV[1]
abort("usage: wf-mutate.rb <workflow> <kind> [args...]") if path.nil? || kind.nil?

before = File.read(path)

# 텍스트로 직접 바꾸는 변형은 Psych 왕복(주석 소실)을 거치지 않는다.
if kind == "true-key"
  raise "on: 블록을 찾지 못했다" unless before =~ /^on:\n/
  after = before.sub(/^permissions:/m, "true:\n  push:\n  pull_request:\npermissions:")
  if after == before
    warn "MUTATION_NO_OP: 주입이 파일을 바꾸지 못했다 (#{kind})"
    exit 1
  end
  File.write(path, after)
  puts "MUTATED: #{kind}"
  exit 0
end

doc = Psych.safe_load(before, aliases: true)
abort("워크플로를 매핑으로 읽지 못했다") unless doc.is_a?(Hash)

def find_step(doc, id)
  doc["jobs"].each_value do |job|
    next unless job.is_a?(Hash)
    (job["steps"] || []).each do |s|
      return s if s.is_a?(Hash) && s["id"].to_s == id
    end
  end
  nil
end

case kind
when "append-run"
  step = find_step(doc, TARGET_STEP) or abort("대상 스텝 없음: #{TARGET_STEP}")
  abort("대상 스텝에 run 이 없다") unless step["run"].is_a?(String)
  step["run"] = step["run"].rstrip + " " + ARGV[2].to_s + "\n"
when "prepend-run"
  step = find_step(doc, TARGET_STEP) or abort("대상 스텝 없음: #{TARGET_STEP}")
  abort("대상 스텝에 run 이 없다") unless step["run"].is_a?(String)
  step["run"] = ARGV[2].to_s + "\n" + step["run"]
when "wrap-run"
  step = find_step(doc, TARGET_STEP) or abort("대상 스텝 없음: #{TARGET_STEP}")
  abort("대상 스텝에 run 이 없다") unless step["run"].is_a?(String)
  template = ARGV[2].to_s
  abort("틀에 CMD 자리가 없다") unless template.include?("CMD")
  step["run"] = template.sub("CMD", step["run"].strip) + "\n"
when "step-shell"
  step = find_step(doc, ARGV[2].to_s) or abort("대상 스텝 없음: #{ARGV[2]}")
  step["shell"] = ARGV[3].to_s
when "job-shell"
  job = doc["jobs"][ARGV[2].to_s] or abort("대상 job 없음: #{ARGV[2]}")
  job["defaults"] = { "run" => { "shell" => ARGV[3].to_s } }
when "workflow-shell"
  doc["defaults"] = { "run" => { "shell" => ARGV[2].to_s } }
when "trigger-filter"
  # Psych 는 YAML 1.1 규칙으로 `on:` 을 boolean true 키로 읽는다.
  key = doc.key?(true) ? true : "on"
  triggers = doc[key]
  abort("on: 을 매핑으로 읽지 못했다") unless triggers.is_a?(Hash)
  abort("대상 트리거 없음: #{ARGV[2]}") unless triggers.key?(ARGV[2].to_s)
  triggers[ARGV[2].to_s] = { ARGV[3].to_s => [ARGV[4].to_s] }
when "true-key"
  # 원문 텍스트에 최상위 `true:` 블록을 덧붙인다. Psych 는 `on:` 과 `true:` 를 같은 키로
  # 합치므로, 검사기가 GitHub 이 트리거로 보는 노드가 아닌 쪽을 읽을 수 있다.
  raise "이 변형은 텍스트로 직접 쓴다"
when "contains-echo"
  step = find_step(doc, ARGV[2].to_s) or abort("대상 스텝 없음: #{ARGV[2]}")
  step["run"] = "echo " + ARGV[3].to_s.inspect + "\n"
else
  abort("알 수 없는 변형 종류: #{kind}")
end

after = Psych.dump(doc)
if after == before
  warn "MUTATION_NO_OP: 주입이 파일을 바꾸지 못했다 (#{kind}) — 공격이 실행되지 않았다"
  exit 1
end
File.write(path, after)
puts "MUTATED: #{kind}"
