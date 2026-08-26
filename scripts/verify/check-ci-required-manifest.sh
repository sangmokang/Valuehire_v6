#!/usr/bin/env bash
# check-ci-required-manifest.sh — 서버 자동검사의 필수 구조를 명부와 양방향으로 대조한다.
#
# 왜 필요한가:
#   check-ci-step-integrity.sh 는 스텝을 "조용히 끄는 것"을 막는다. 그러나 스스로 적어둔
#   대로 스텝을 **삭제**하는 것은 막지 못하고, `on:` 트리거를 없애 워크플로가 아예 실행되지
#   않게 만드는 것도 보지 않는다. pre-push 의 문자열 훑기는 우회가 계속 나왔다.
#   여기서는 필수 조건을 명부(docs/sot/ci-required-manifest.yaml)에 적고 워크플로를 실제
#   YAML 로 파싱해 **양방향**으로 맞춘다 — 명부에 있는데 워크플로에 없어도, 워크플로가
#   명부에 없는 인수 검사를 돌려도 불합격이다.
#
# 판정 기준은 표시 이름이 아니라 **안정된 job id · step id** 다. 이름은 복사·위조가 자유롭다.
#
# 입력 : $1 = 명부 경로 (기본 docs/sot/ci-required-manifest.yaml)
#        WORKFLOW_FILE = 워크플로 경로 (기본은 명부의 workflow: 값)
# 출력 : 항목마다 PASS:/FAIL:, 마지막 줄 `CHECKED: <대조 항목 수>`
# exit : 0 = 전부 통과 | 1 = 위반 | 2 = 스캔 무효(명부·워크플로 없음/파싱 실패/대조 0건)
#
# 막지 못하는 것: 같은 커밋에서 이 검사기와 명부를 함께 약화하는 공격. 둘 다 그 커밋의
#   내용이기 때문이다. 그것은 외부 required check 와 승인 규칙의 몫이며 여기서 다 막는다고
#   주장하지 않는다.
set -uo pipefail

MANIFEST="${1:-docs/sot/ci-required-manifest.yaml}"

if [ ! -f "$MANIFEST" ]; then
  echo "NOT_RUN: 명부가 없다 — $MANIFEST (fail-closed)"
  echo "CHECKED: 0"
  exit 2
fi

# 저장소가 실제로 가진 인수 검사 목록. 읽지 못하면 통과가 아니라 무효다.
SCRIPT_LIST=$(mktemp) || {
  echo "NOT_RUN: 임시 파일 생성 실패"
  echo "CHECKED: 0"
  exit 2
}
trap 'rm -f "$SCRIPT_LIST"' EXIT
if ! git ls-files 'scripts/acceptance-*.sh' > "$SCRIPT_LIST"; then
  echo "NOT_RUN: 인수 검사 목록을 읽지 못했다 (git ls-files 실패 · fail-closed)"
  echo "CHECKED: 0"
  exit 2
fi
if [ ! -s "$SCRIPT_LIST" ]; then
  echo "FAIL: 저장소에 인수 검사가 0개 — 대상 0개는 합격이 아니다 (P20)"
  echo "CHECKED: 0"
  exit 2
fi

ruby -rpsych -rdate -e '
manifest_path, script_list_path, workflow_override = ARGV

def bail(msg, code)
  puts msg
  puts "CHECKED: 0"
  exit code
end

begin
  manifest = Psych.safe_load(File.read(manifest_path), permitted_classes: [Date, Time])
rescue Psych::Exception => e
  bail("FAIL: 명부 파싱 실패 — #{e.message.lines.first.to_s.strip}", 2)
end
bail("FAIL: 명부가 매핑이 아니다 — #{manifest_path}", 2) unless manifest.is_a?(Hash)

workflow_path = workflow_override.to_s.empty? ? manifest["workflow"] : workflow_override
bail("FAIL: 대조할 워크플로 경로가 없다 (명부의 workflow: 누락)", 2) if workflow_path.to_s.empty?
bail("FAIL: 워크플로가 없다 — #{workflow_path} (fail-closed)", 2) unless File.file?(workflow_path)

begin
  wf = Psych.safe_load(File.read(workflow_path), aliases: true, permitted_classes: [Date, Time])
rescue Psych::Exception => e
  bail("FAIL: 워크플로 파싱 실패 — #{e.message.lines.first.to_s.strip}", 2)
end
bail("FAIL: 워크플로가 매핑이 아니다 — #{workflow_path}", 2) unless wf.is_a?(Hash)

errors = []
passes = []
checked = 0

# ── 실행 조건 ────────────────────────────────────────────────────────────────
# Psych 는 YAML 1.1 규칙으로 `on:` 을 boolean true 키로 읽는다. "on" 문자열이 아니다.
# 이 함정을 모르면 트리거 검사가 조용히 0건이 된다(2026-08-27 실측).
triggers = wf.key?(true) ? wf[true] : wf["on"]
required_triggers = manifest["required_triggers"] || []
if required_triggers.empty?
  errors << "MANIFEST_NO_TRIGGERS: 명부에 required_triggers 가 없다 — 실행 조건을 아무도 지키지 않는다"
end
present = case triggers
          when Hash  then triggers.keys.map(&:to_s)
          when Array then triggers.map(&:to_s)
          when String then [triggers]
          else []
          end
# 키가 있다고 실행되는 것이 아니다. 2026-08-27 V1 실측: push 를 남기고
# `branches: ["never-such-branch"]` 나 `paths-ignore: ["**"]` 를 걸면 워크플로가
# 영원히 실행되지 않는데도 통과했다. 필터까지 봐야 "실행 조건이 살아 있다"고 말할 수 있다.
BLOCKING_FILTERS = %w[branches-ignore paths paths-ignore tags tags-ignore].freeze
required_triggers.each do |t|
  checked += 1
  name = t.to_s
  unless present.include?(name)
    errors << "TRIGGER_MISSING: `on:` 에 #{name} 가 없다 (현재: #{present.empty? ? "없음" : present.join(", ")}) — " \
              "실행 조건이 사라지면 검사는 시작조차 하지 않는다"
    next
  end
  cfg = triggers.is_a?(Hash) ? triggers[name] : nil
  if cfg.is_a?(Hash)
    bad = cfg.keys.map(&:to_s) & BLOCKING_FILTERS
    unless bad.empty?
      errors << "TRIGGER_FILTERED: `on.#{name}` 에 #{bad.join(", ")} 필터가 있다 — " \
                "트리거를 남겨두고 필터로 도달 불가하게 만들면 검사는 영원히 돌지 않는다"
      next
    end
    if cfg.key?("branches")
      list = Array(cfg["branches"]).map(&:to_s)
      unless list.include?("**")
        errors << "TRIGGER_NARROWED: `on.#{name}.branches` 가 #{list.inspect} — " \
                  "모든 브랜치(`**`)를 덮지 않으면 이 워크플로는 일부 push 에서 돌지 않는다"
        next
      end
    end
  end
  passes << "TRIGGER #{name}"
end

jobs = wf["jobs"]
bail("FAIL: jobs 를 읽지 못했다 — 검사 대상 0개는 합격이 아니다", 2) unless jobs.is_a?(Hash) && !jobs.empty?

# ── 셸 교체 금지 (2026-08-27 V1 F2 · 치명) ──────────────────────────────────
# GitHub 의 기본 bash 셸은 `bash -e` 로 돈다. `shell:` 을 직접 지정하면 `-e` 가 붙지
# 않으므로, 다줄 run 에서 **마지막 줄 외의 실패가 전부 무시된다**. 스텝을 하나도
# 건드리지 않고 최상위 `defaults` 한 블록만 넣어도 워크플로 전체가 그렇게 된다.
# 실측: 다줄 스텝 13개 중 10개의 중간 실패가 조용히 사라졌다.
def check_shell(node, label, errors)
  return unless node.is_a?(Hash)
  if node.key?("shell")
    errors << "SHELL_OVERRIDE: #{label} 이 shell 을 직접 지정한다 (#{node["shell"].inspect}) — " \
              "기본 셸의 -e 가 사라져 다줄 run 의 중간 실패가 무시된다"
  end
  d = node["defaults"]
  return unless d.is_a?(Hash)
  r = d["run"]
  return unless r.is_a?(Hash)
  if r.key?("shell")
    errors << "SHELL_OVERRIDE: #{label}.defaults.run 이 shell 을 지정한다 (#{r["shell"].inspect}) — " \
              "스텝을 하나도 건드리지 않고 워크플로 전체의 실패 전파를 끌 수 있다"
  end
end

checked += 1
check_shell(wf, "workflow", errors)
jobs.each { |jn, job| checked += 1; check_shell(job, "jobs.#{jn}", errors) }

# ── 필수 job ─────────────────────────────────────────────────────────────────
(manifest["required_jobs"] || []).each do |rj|
  checked += 1
  jid = rj.is_a?(Hash) ? rj["id"] : rj
  job = jobs[jid]
  if job.nil?
    errors << "JOB_MISSING: 필수 job `#{jid}` 가 워크플로에 없다"
    next
  end
  errors << "JOB_CONDITIONAL: jobs.#{jid} 에 if 가 있다 — job 을 통째로 끌 수 있다" if job.key?("if")
  errors << "JOB_CONTINUE_ON_ERROR: jobs.#{jid} 가 실패를 무시한다" if job["continue-on-error"]
  steps = job["steps"]
  unless steps.is_a?(Array) && !steps.empty?
    errors << "JOB_NO_STEPS: jobs.#{jid} 에 스텝이 없다 — 빈 job 은 항상 초록이다"
    next
  end
  passes << "JOB #{jid}"
end

# 워크플로 전체에서 id 로 스텝을 찾되, 어느 job 소속인지도 함께 본다.
# (필수 스텝을 조건이 붙은 다른 job 으로 옮기는 우회를 막는다)
steps_by_id = {}
jobs.each do |jname, job|
  next unless job.is_a?(Hash)
  (job["steps"] || []).each_with_index do |st, i|
    next unless st.is_a?(Hash)
    sid = st["id"]
    next if sid.nil?
    (steps_by_id[sid.to_s] ||= []) << [jname.to_s, st, i]
  end
end

# 실행처럼 보이지만 실패를 삼키는 꼬리. 문자 클래스로 쓴 것은 이 소스 자체가 P13 약화
# 탐지 패턴에 걸리지 않게 하기 위해서다(저장소 선례와 같은 이유).
# 전체 run 에 적용하는 금지 형태. 여기 있는 것은 "정상 코드에는 나올 이유가 없는" 것만
# 둔다 — 필수 명령 줄에 꼬리를 붙이는 공격은 아래 "단독 줄" 규칙이 막는다.
SWALLOW = [
  [/[|][|]\s*true\s*$/,        "오류를 무시하는 꼬리"],
  [/[|][|]\s*:\s*$/,           "오류를 무시하는 꼬리(:)"],
  [/;\s*true\s*$/,             "세미콜론 뒤 무조건 성공"],
  [/;\s*:\s*$/,                "세미콜론 뒤 무조건 성공(:)"],
  [/[|][|]\s*exit\s+0\s*$/,    "오류를 성공 종료로 바꾸는 꼬리"],
  [/\Aset\s+\+e\b/,            "오류 전파를 끄는 설정 (set +e)"],
  [/\Aset\s+\+o\s+errexit\b/, "오류 전파를 끄는 설정 (set +o errexit)"],
  [/\Aset\s+-e\s*\+/,          "오류 전파를 끄는 설정 (set -e+…)"],
  [/\Atrap\s+.*\bERR\b/,       "ERR 트랩으로 실패를 가로챈다"],
]

# 실제로 실행되는 줄만 남긴다. 주석·빈 줄을 걷어내고, heredoc 본문은 데이터이지
# 명령이 아니므로 통째로 건너뛴다(heredoc 안에 명령을 적어 위장하는 것을 막는다).
def executable_lines(run)
  return [] unless run.is_a?(String)
  out = []
  heredoc_end = nil
  run.each_line do |raw|
    line = raw.rstrip
    if heredoc_end
      heredoc_end = nil if line.strip == heredoc_end
      next
    end
    stripped = line.strip
    next if stripped.empty?
    next if stripped.start_with?("#")
    if (m = stripped.match(/<<-?\s*[\x27"]?([A-Za-z_][A-Za-z0-9_]*)[\x27"]?/))
      heredoc_end = m[1]
    end
    out << stripped
  end
  out
end

def scan_swallow(run, label, errors, swallow)
  return unless run.is_a?(String)
  run.each_line do |line|
    stripped = line.strip
    next if stripped.empty? || stripped.start_with?("#")
    swallow.each do |re, why|
      if stripped =~ re
        errors << "RUN_SWALLOWS_ERROR: #{label} 의 `#{stripped}` — #{why}. " \
                  "명령 앞부분이 그대로여도 실패가 전파되지 않으면 검사가 아니다"
      end
    end
  end
end

# ── 필수 step ────────────────────────────────────────────────────────────────
required_steps = manifest["required_steps"] || []
required_steps.each do |rs|
  checked += 1
  sid = rs["id"].to_s
  want_job = rs["job"].to_s
  found = steps_by_id[sid]

  if found.nil? || found.empty?
    errors << "STEP_MISSING: 필수 스텝 id `#{sid}` 가 워크플로에 없다 — " \
              "삭제·주석 처리·id 변경 중 하나다"
    next
  end
  if found.size > 1
    errors << "STEP_DUPLICATE_ID: step id `#{sid}` 가 #{found.size}곳에 있다 — 어느 것이 판정 대상인지 정할 수 없다"
    next
  end

  job_name, step, idx = found.first
  label = "jobs.#{job_name}.steps[#{idx}](id=#{sid})"

  if !want_job.empty? && job_name != want_job
    errors << "STEP_WRONG_JOB: `#{sid}` 가 명부의 job `#{want_job}` 이 아니라 `#{job_name}` 에 있다 — " \
              "필수 스텝을 다른 job 으로 옮기면 그 job 의 조건이 검사를 끌 수 있다"
    next
  end

  # 조건: 명부에 allow_if 로 사유를 적은 스텝만 허용한다. 판정 기준은 id 이므로
  # 표시 이름을 다른 스텝에 복사해도 예외 권한이 따라가지 않는다.
  if step.key?("if")
    reason = rs["allow_if"]
    if reason.to_s.empty?
      errors << "STEP_CONDITIONAL: #{label} 에 if 가 있다 (#{step["if"].inspect}) — " \
                "명부에 allow_if 사유가 없다. 조건이 거짓이면 실행되지 않고도 초록이다"
    else
      passes << "STEP #{sid} — if 허용 (#{reason.to_s.lines.first.to_s.strip})"
    end
  end

  errors << "STEP_CONTINUE_ON_ERROR: #{label} 이 실패를 무시한다 — 빨개져야 할 검사가 초록으로 남는다" \
    if step["continue-on-error"]

  if rs["uses_contains"]
    u = step["uses"].to_s
    errors << "STEP_USES_MISMATCH: #{label} 의 uses 가 `#{rs["uses_contains"]}` 를 담지 않는다 (현재: #{u.inspect})" \
      unless u.include?(rs["uses_contains"].to_s)
  end

  run = step["run"]
  commands = rs["must_run_commands"] || []
  contains = rs["must_run_contains"] || []

  if (!commands.empty? || !contains.empty?) && !run.is_a?(String)
    errors << "STEP_NO_RUN: #{label} 에 run 이 없다 — 명부는 이 스텝이 명령을 돌리기를 요구한다"
    next
  end

  # must_run_commands — 그 명령이 **그 줄에서 단독으로** 실행돼야 한다.
  #
  # 2026-08-27 V1 실측: 부분 문자열 대조는 아래를 전부 "명령이 있다"로 셌다.
  #   `bash x.sh || true; echo done` · `bash x.sh | cat` · `bash x.sh &`
  #   `echo "bash x.sh"` · `printf '%s\n' "bash x.sh"` · `: bash x.sh` · `# bash x.sh`
  # 앞뒤에 무엇이 붙어도 문자열은 그대로 있기 때문이다. 그래서 "포함"이 아니라
  # "그 줄 전체가 이 명령"을 요구한다. 꼬리를 붙이는 순간 단독이 아니게 되어 걸린다.
  unless commands.empty?
    lines = executable_lines(run)
    commands.each do |cmd|
      target = cmd.to_s.strip
      if lines.include?(target)
        passes << "STEP #{sid} — `#{target}`"
      else
        near = lines.find { |l| l.include?(target) }
        detail = near ? " (비슷한 줄: `#{near}`)" : ""
        errors << "STEP_COMMAND_NOT_STANDALONE: #{label} 의 run 에 `#{target}` 가 " \
                  "단독 줄로 없다#{detail} — 앞뒤에 무엇이든 붙으면 실패가 전파되지 않을 수 있다"
      end
    end
  end

  # must_run_contains — 인라인 본문 스텝용. 단독 줄을 요구할 수 없는 자리에만 쓴다.
  # 주석은 걷어내고 본다. 주석에만 남은 명령은 실행되지 않는다.
  unless contains.empty?
    body = executable_lines(run).join("\n")
    contains.each do |frag|
      if body.include?(frag.to_s)
        passes << "STEP #{sid} ~ `#{frag}`"
      else
        errors << "STEP_FRAGMENT_MISSING: #{label} 의 실행되는 줄에 `#{frag}` 가 없다 — " \
                  "주석 처리되었거나 사라졌다"
      end
    end
  end

  scan_swallow(run, label, errors, SWALLOW)
end

# 명부가 요구하지 않는 스텝도 실패를 삼키면 안 된다.
jobs.each do |jname, job|
  next unless job.is_a?(Hash)
  (job["steps"] || []).each_with_index do |st, i|
    next unless st.is_a?(Hash)
    slabel = "jobs.#{jname}.steps[#{i}](id=#{st["id"].inspect})"
    scan_swallow(st["run"], slabel, errors, SWALLOW)
    # 스텝 하나만 shell 을 바꿔도 그 스텝의 다줄 run 은 -e 없이 돈다.
    check_shell(st, slabel, errors)
  end
end

# ── 인수 검사 양방향 대조 ────────────────────────────────────────────────────
acc = manifest["acceptance_scripts"] || {}
required_scripts = (acc["required"] || []).map(&:to_s)
excluded_entries = acc["excluded"] || []
excluded_scripts = []
excluded_entries.each do |e|
  checked += 1
  unless e.is_a?(Hash) && !e["path"].to_s.empty?
    errors << "EXCLUDED_MALFORMED: 제외 항목에 path 가 없다 — #{e.inspect}"
    next
  end
  if e["reason"].to_s.strip.empty?
    errors << "EXCLUDED_NO_REASON: `#{e["path"]}` 를 사유 없이 CI 에서 뺐다 — " \
              "사유 없는 제외는 만료 없는 억제와 같다 (P13③)"
    next
  end
  excluded_scripts << e["path"].to_s
  passes << "EXCLUDED #{e["path"]}"
end

overlap = required_scripts & excluded_scripts
overlap.each do |p|
  errors << "SCRIPT_BOTH_LISTS: `#{p}` 가 required 와 excluded 양쪽에 있다 — 판정이 모순이다"
end

# 워크플로가 실제로 실행하는 인수 검사(구조 파싱으로 추출)
executed = []
jobs.each do |_jn, job|
  next unless job.is_a?(Hash)
  (job["steps"] || []).each do |st|
    next unless st.is_a?(Hash)
    run = st["run"]
    next unless run.is_a?(String)
    run.each_line do |line|
      stripped = line.strip
      next if stripped.empty? || stripped.start_with?("#")
      stripped.scan(%r{scripts/acceptance-[A-Za-z0-9._-]+\.sh}).each { |m| executed << m }
    end
  end
end
executed.uniq!

# 방향 ①: 워크플로가 돌리는데 명부에 없다
(executed - required_scripts).each do |p|
  checked += 1
  errors << "EXECUTED_NOT_REGISTERED: 워크플로가 `#{p}` 를 실행하는데 명부 required 에 없다 — " \
            "명부는 CI 가 무엇을 돌리는지의 정본이어야 한다"
end

# 방향 ②: 명부가 요구하는데 워크플로가 돌리지 않는다
(required_scripts - executed).each do |p|
  checked += 1
  errors << "REGISTERED_NOT_EXECUTED: 명부가 `#{p}` 를 요구하는데 워크플로의 실행 줄에 없다 — " \
            "pre-push 글로브에만 잡히는 검사는 없는 것으로 친다 (P15③)"
end

# 방향 ③: 저장소에 있는데 어느 목록에도 없다 (새 인수 검사의 조용한 누락)
on_disk = File.read(script_list_path).split("\n").map(&:strip).reject(&:empty?)
on_disk.each do |p|
  checked += 1
  if required_scripts.include?(p) || excluded_scripts.include?(p)
    passes << "SCRIPT #{p}"
  else
    errors << "SCRIPT_UNREGISTERED: `#{p}` 가 명부의 required 에도 excluded 에도 없다 — " \
              "새 인수 검사는 CI 에서 실행하거나 사유를 적고 빼야 한다"
  end
end

# 방향 ④: 명부에 적힌 스크립트가 실제로 존재하는가
(required_scripts + excluded_scripts).uniq.each do |p|
  checked += 1
  unless on_disk.include?(p)
    errors << "SCRIPT_NOT_ON_DISK: 명부의 `#{p}` 가 저장소에 없다 — 죽은 등록이다"
  end
end

if checked.zero?
  puts "FAIL: 대조 항목이 0개 — 검사할 것이 없어서 통과하는 것은 합격이 아니다 (P20)"
  puts "CHECKED: 0"
  exit 2
end

passes.each { |p| puts "PASS: #{p}" }
if errors.empty?
  puts "PASS: 필수 구조 #{checked}건이 명부와 양방향으로 일치"
  puts "CHECKED: #{checked}"
  exit 0
else
  errors.each { |e| puts "FAIL: #{e}" }
  puts "CHECKED: #{checked}"
  exit 1
end
' "$MANIFEST" "$SCRIPT_LIST" "${WORKFLOW_FILE:-}"
