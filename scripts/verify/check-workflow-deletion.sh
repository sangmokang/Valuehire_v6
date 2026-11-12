#!/usr/bin/env bash
# check-workflow-deletion.sh — CI 워크플로에서 실행되는 검사가 사라졌는가 (P13 삭제형 약화)
#
# 사용: check-workflow-deletion.sh <HEAD 판 파일> <인덱스 판 파일 | 빈 파일(삭제)>
# 출력: exit 0 (삭제 없음) | exit 1 (삭제 있음 — stdout 에 job/step 위치만, 내용은 출력하지 않음)
#       exit 2 (파싱·실행 실패 — 호출자는 차단으로 처리한다, fail-closed)
#
# 왜 YAML 구조인가 (V1 Codex 2026-11-12, thread 01a1cffa-ad63-7011-8ab4-18b1d3fb08e7):
#   줄 텍스트로 세면 ① 삭제한 스텝 문구를 env 문자열에 남기는 미끼 ② 앵커(run: &a |)·
#   flow 형식(- {name:, run:}) ③ run 이 첫 키인 스텝의 형제 키 오탐 — 셋 다 뚫리거나 오탐한다.
#   그래서 실제 실행 단위만 센다: jobs.*.steps[*] 의 name · uses · run(줄 단위, 주석·빈 줄 제외)
#   와 job 수준 uses. env·with·주석·다른 키의 문자열은 "남아 있는 검사"로 치지 않는다.
#   다중집합 비교라 순서 이동은 삭제가 아니고, 명령 수정은 옛 줄이 사라지므로 삭제다.
#
# 막지 못하는 것: 같은 명령 줄을 실행되지 않는 다른 run 안(heredoc 본문 등)이나 조건부 스텝으로
#   옮기는 것. 조건부·오류무시 스텝은 check-ci-step-integrity.sh 가 CI 에서 본다.
set -uo pipefail

if [ "$#" -ne 2 ] || [ ! -f "$1" ] || [ ! -f "$2" ]; then
  echo "ERROR: 사용법 — $0 <old> <new> (두 파일 모두 존재해야 한다)"
  exit 2
fi

ruby -rpsych -rdate -e '
def units(path)
  text = File.read(path)
  return [] if text.strip.empty?
  doc = Psych.safe_load(text, aliases: true, permitted_classes: [Date, Time])
  raise "최상위가 매핑이 아니다" unless doc.is_a?(Hash)
  jobs = doc["jobs"]
  return [] if jobs.nil?
  raise "jobs 가 매핑이 아니다" unless jobs.is_a?(Hash)
  out = []
  jobs.each do |jid, job|
    raise "job #{jid} 가 매핑이 아니다" unless job.is_a?(Hash)
    out << ["#{jid}", "job-uses", job["uses"].to_s] if job.key?("uses")
    steps = job["steps"] || []
    raise "job #{jid} 의 steps 가 배열이 아니다" unless steps.is_a?(Array)
    steps.each_with_index do |st, i|
      raise "job #{jid} step #{i + 1} 이 매핑이 아니다" unless st.is_a?(Hash)
      where = "#{jid}/step#{i + 1}"
      out << [where, "name", st["name"].to_s] if st.key?("name")
      out << [where, "uses", st["uses"].to_s] if st.key?("uses")
      if st.key?("run")
        st["run"].to_s.each_line do |l|
          s = l.strip
          next if s.empty? || s.start_with?("#")
          out << [where, "run", s]
        end
      end
    end
  end
  out
end

begin
  old_u = units(ARGV[0])
  new_u = units(ARGV[1])
rescue StandardError => e
  puts "ERROR: 워크플로 판정 불가 — #{e.message.lines.first.to_s.strip}"
  exit 2
end

remain = Hash.new(0)
new_u.each { |_, k, v| remain[[k, v]] += 1 }
gone = []
old_u.each do |where, k, v|
  if remain[[k, v]] > 0
    remain[[k, v]] -= 1
  else
    gone << "#{where}:#{k}"
  end
end
if gone.empty?
  puts "OK: 삭제된 실행 단위 0건 (HEAD #{old_u.size}개 대조)"
  exit 0
end
puts "DELETED: #{gone.size}건 — #{gone.uniq.first(10).join(", ")}"
exit 1
' "$1" "$2"
