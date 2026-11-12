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
#   그래서 실제 실행 단위만 센다: jobs.*.steps[*] 의 name · uses · run(줄 단위, 빈 줄만 제외)
#   와 job 수준 uses, 그리고 on 트리거 이벤트 이름. env·with·주석·다른 키의 문자열은 "남아 있는 검사"로 치지 않는다.
#   다중집합 비교라 순서 이동은 삭제가 아니고, 명령 수정은 옛 줄이 사라지므로 삭제다.
#
# 막지 못하는 것(삭제가 아닌 추가형 무력화 — 범위 밖): defaults.run.shell 교체, job/step if·continue-on-error 추가
#   (if·continue-on-error 는 CI 의 check-ci-step-integrity.sh 가 본다), 트리거 필터(branches 등) 변경.
#   그리고 같은 명령 줄을 실행되지 않는 다른 run 안(heredoc 본문 등)이나 조건부 스텝으로
#   옮기는 것. 조건부·오류무시 스텝은 check-ci-step-integrity.sh 가 CI 에서 본다.
set -uo pipefail

if [ "$#" -ne 2 ] || [ ! -f "$1" ] || [ ! -f "$2" ]; then
  echo "ERROR: 사용법 — $0 <old> <new> (두 파일 모두 존재해야 한다)"
  exit 2
fi

ruby -rpsych -rdate -e '
# run 블록 안에서는 셸 주석을 판별하지 않는다 — 비어 있지 않은 모든 줄이 실행 단위다.
# 텍스트로 셸 주석을 가리려던 시도는 V1 2·3·5·6·7차에서 연달아 뚫렸다(인라인 주석·중첩 따옴표·
# extglob @(#|x)·줄 이어짐 뒤 # 줄이 실제로 실행됨). 판별할 수 없는 것을 판별하지 않는다.
# 대가: run 안 주석만 바꿔도 삭제로 본다(보수적 오탐). run 밖 YAML 주석은 파서가 버리므로 통과한다.

def units(path)
  text = File.read(path)
  return [] if text.strip.empty?
  doc = Psych.safe_load(text, aliases: true, permitted_classes: [Date, Time])
  raise "최상위가 매핑이 아니다" unless doc.is_a?(Hash)
  jobs = doc["jobs"]
  return [] if jobs.nil?
  raise "jobs 가 매핑이 아니다" unless jobs.is_a?(Hash)
  out = []
  # 트리거 이벤트도 실행 단위다 — pull_request 를 지우면 PR 에서 CI 가 아예 돌지 않는다(V2 2026-11-12).
  # YAML 1.1 에서 키 on 은 true 로 읽힌다.
  trig = doc.key?("on") ? doc["on"] : doc[true]
  events = case trig
           when String then [trig]
           when Array then trig.map(&:to_s)
           when Hash then trig.keys.map(&:to_s)
           when nil then []
           else raise "on 형식을 알 수 없다"
           end
  events.each { |e| out << ["on", "event", e] }
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
          next if s.empty?
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
