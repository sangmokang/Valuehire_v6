#!/usr/bin/env bash
# acceptance-ci-step-integrity.sh — 보호 CI step의 정확한 선언 계약을 공격한다.
set -uo pipefail

unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_OBJECT_DIRECTORY \
      GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_COMMON_DIR GIT_PREFIX GIT_QUARANTINE_PATH

REPO=$(git rev-parse --show-toplevel 2>/dev/null) || {
  echo "NOT_RUN: git 저장소가 아니다"; echo "CHECKED: 0"; exit 2
}
cd "$REPO" || exit 2
CHECKER="$REPO/scripts/verify/check-ci-step-integrity.sh"
RUNNER="$REPO/scripts/verify/run-acceptance.sh"
WF="$REPO/.github/workflows/verify.yml"
CONTRACT="$REPO/docs/sot/ci-required-steps.json"
if [ ! -f "$CHECKER" ] || [ ! -f "$RUNNER" ] || [ ! -f "$WF" ] || [ ! -f "$CONTRACT" ]; then
  echo "FAIL: 검사기·runner·workflow·계약 중 하나가 없다"; echo "CHECKED: 0"; exit 2
fi

SNAPSHOT=$(git status --porcelain)
TMP=$(mktemp -d) || { echo "NOT_RUN: mktemp 실패"; echo "CHECKED: 0"; exit 2; }
trap 'ruby -rfileutils -e "FileUtils.remove_entry(ARGV[0]) if File.exist?(ARGV[0])" "$TMP"' EXIT

fail=0
checked=0
record() {
  local ok="$1" desc="$2" detail="$3"
  checked=$((checked + 1))
  if [ "$ok" -eq 0 ]; then printf 'PASS: %s — %s\n' "$desc" "$detail"
  else printf 'FAIL: %s — %s\n' "$desc" "$detail"; fail=1; fi
}

expect_rc() {
  local desc="$1" workflow="$2" contract="$3" wanted="$4" rc=0 output
  output=$(bash "$CHECKER" "$workflow" "$contract" 2>&1) || rc=$?
  if [ "$rc" -eq "$wanted" ]; then
    record 0 "$desc" "exit=$rc"
  else
    record 1 "$desc" "expected exit=$wanted actual=$rc output=${output//$'\n'/ | }"
  fi
}

expect_pass_output() {
  local desc="$1" workflow="$2" contract="$3" rc=0 output count
  output=$(bash "$CHECKER" "$workflow" "$contract" 2>&1) || rc=$?
  count=$(printf '%s\n' "$output" | sed -n 's/^CHECKED: //p' | tail -1)
  if [ "$rc" -eq 0 ] && [ "${count:-0}" -ge 1 ] 2>/dev/null; then
    record 0 "$desc" "exit=0 CHECKED=$count"
  else
    record 1 "$desc" "exit=$rc CHECKED=${count:-없음} output=${output//$'\n'/ | }"
  fi
}

mutate_run() {
  local name="$1" needle="$2" replacement="$3" path
  path="$TMP/$name.yml"
  cp "$WF" "$path"
  ruby -e 'p,n,r=ARGV; s=File.read(p); abort("needle missing") unless s.include?(n); File.write(p,s.sub(n,r))' \
    "$path" "$needle" "$replacement"
  printf '%s' "$path"
}

TARGET='        run: bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-a4.sh'
G2_TARGET='          bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-gates.sh'

# 정상·허용 사례
expect_pass_output "현재 정상 workflow" "$WF" "$CONTRACT"

p="$TMP/nonprotected-setup.yml"; cp "$WF" "$p"
ruby -e 'p=ARGV[0]; s=File.read(p).sub("    steps:\n", "    steps:\n      - name: 설명용 비보호 setup\n        run: echo setup 설명\n"); File.write(p,s)' "$p"
expect_rc "설명용 echo가 있는 비보호 setup step" "$p" "$CONTRACT" 0

p="$TMP/metadata.yml"; cp "$WF" "$p"
ruby -e 'p=ARGV[0]; s=File.read(p).sub("name: verify", "name: verify-metadata-change"); File.write(p,s)' "$p"
expect_rc "안전 명령과 무관한 workflow metadata 변경" "$p" "$CONTRACT" 0

output=$(bash "$CHECKER" "$WF" "$CONTRACT" 2>&1); rc=$?
if [ "$rc" -eq 0 ] && printf '%s\n' "$output" | grep -q '^ALLOWED: 인수 검사 0-5'; then
  record 0 "이유가 기록된 0-5 조건부 step" "정확한 if 허용"
else
  record 1 "이유가 기록된 0-5 조건부 step" "exit=$rc 또는 ALLOWED 출력 없음"
fi

# 필수 counter-AC 1~3: wrapper·문자열·주석은 명령 실행 증거가 아니다.
p=$(mutate_run counter-01 "$G2_TARGET" '          echo scripts/verify/run-acceptance.sh scripts/acceptance-hs-gates.sh')
expect_rc "counter-01 echo 정확 경로" "$p" "$CONTRACT" 1

p=$(mutate_run counter-02 "$G2_TARGET" '          printf "%s\n" scripts/verify/run-acceptance.sh scripts/acceptance-hs-gates.sh')
expect_rc "counter-02 printf 정확 경로" "$p" "$CONTRACT" 1

p=$(mutate_run counter-03 "$G2_TARGET" '          true # bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-gates.sh')
expect_rc "counter-03a true 뒤 주석" "$p" "$CONTRACT" 1

p=$(mutate_run counter-04 "$G2_TARGET" '          : # bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-gates.sh')
expect_rc "counter-03b colon 뒤 주석" "$p" "$CONTRACT" 1

# 필수 counter-AC 4: 이름은 유지하고 run만 변경한다.
p=$(mutate_run counter-05 "$TARGET" '        run: true')
expect_rc "counter-04 step 이름 유지·run 변경" "$p" "$CONTRACT" 1

# 필수 counter-AC 5: 같은 job 안 같은 이름을 중복하고 하나만 정상으로 둔다.
p="$TMP/counter-06.yml"; cp "$WF" "$p"
ruby -rpsych -rdate -e 'p=ARGV[0]; d=Psych.safe_load(File.read(p), aliases:true, permitted_classes:[Date,Time]); a=d["jobs"]["verify"]["steps"]; t=a.find{|s| s["name"]=="인수 검사 hs-a4 (대용량·산출물 차단이 실제로 도는가)"}; a << Marshal.load(Marshal.dump(t)); File.write(p,Psych.dump(d))' "$p"
expect_rc "counter-05 동일 이름 step 중복" "$p" "$CONTRACT" 1

# 필수 counter-AC 6: 다른 job에 정상 명령을 두고 원래 step은 무력화한다.
p="$TMP/counter-07.yml"; cp "$WF" "$p"
ruby -rpsych -rdate -e 'p=ARGV[0]; d=Psych.safe_load(File.read(p), aliases:true, permitted_classes:[Date,Time]); t=d["jobs"]["verify"]["steps"].find{|s| s["name"]=="인수 검사 hs-a4 (대용량·산출물 차단이 실제로 도는가)"}; t["run"]="true"; d["jobs"]["decoy"]={"runs-on"=>"ubuntu-latest","steps"=>[{"name"=>"decoy","run"=>"bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-a4.sh"}]}; File.write(p,Psych.dump(d))' "$p"
expect_rc "counter-06 다른 job 정상·원래 step 무력화" "$p" "$CONTRACT" 1

# 필수 counter-AC 7: 첫 명령만 정상이고 뒤에서 성공으로 덮는다.
p=$(mutate_run counter-08 "$TARGET" $'        run: |\n          bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-a4.sh\n          exit 0')
expect_rc "counter-07 multi-line 뒤 exit 0" "$p" "$CONTRACT" 1

# 필수 counter-AC 8: workflow와 계약을 함께 echo로 약화해도 승인되지 않는다.
p="$TMP/counter-09.yml"; c="$TMP/counter-09.json"; cp "$WF" "$p"; cp "$CONTRACT" "$c"
ruby -e 'p=ARGV[0]; s=File.read(p).sub("        run: bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-a4.sh", "        run: echo scripts/verify/run-acceptance.sh scripts/acceptance-hs-a4.sh"); File.write(p,s)' "$p"
ruby -rjson -e 'p=ARGV[0]; d=JSON.parse(File.read(p)); t=d["protected_steps"].find{|s| s["name"]=="인수 검사 hs-a4 (대용량·산출물 차단이 실제로 도는가)"}; t["run_lines"]=["echo scripts/verify/run-acceptance.sh scripts/acceptance-hs-a4.sh"]; File.write(p,JSON.pretty_generate(d)+"\n")' "$c"
expect_rc "counter-08 workflow·계약 동시 약화" "$p" "$c" 1

# 필수 counter-AC 9: 검사기 자체를 exit 0으로 비운 사본은 runner가 거부한다.
noop="$TMP/checker-noop.sh"; printf '#!/usr/bin/env bash\nexit 0\n' > "$noop"; chmod +x "$noop"
rc=0; bash "$RUNNER" "$noop" >/dev/null 2>&1 || rc=$?
if [ "$rc" -ne 0 ]; then record 0 "counter-09 checker 전체 exit 0" "runner exit=$rc"
else record 1 "counter-09 checker 전체 exit 0" "runner exit=0"; fi

# EARS 추가 경계
p=$(mutate_run syntax-wrapper "$TARGET" '        run: bash -n scripts/acceptance-hs-a4.sh')
expect_rc "bash -n wrapper" "$p" "$CONTRACT" 1

p="$TMP/deleted.yml"; cp "$WF" "$p"
ruby -rpsych -rdate -e 'p=ARGV[0]; d=Psych.safe_load(File.read(p), aliases:true, permitted_classes:[Date,Time]); d["jobs"]["verify"]["steps"].reject!{|s| s["name"]=="인수 검사 hs-a4 (대용량·산출물 차단이 실제로 도는가)"}; File.write(p,Psych.dump(d))' "$p"
expect_rc "보호 step 삭제" "$p" "$CONTRACT" 1

p="$TMP/renamed.yml"; cp "$WF" "$p"
ruby -e 'p=ARGV[0]; s=File.read(p).sub("인수 검사 hs-a4 (대용량·산출물 차단이 실제로 도는가)", "이름 바꾼 hs-a4"); File.write(p,s)' "$p"
expect_rc "보호 step 이름 변경" "$p" "$CONTRACT" 1

p="$TMP/step-if.yml"; cp "$WF" "$p"
ruby -e 'p=ARGV[0]; s=File.read(p).sub("      - name: 인수 검사 hs-a4", "      - name: 인수 검사 hs-a4\n        if: ${{ false }}"); File.write(p,s)' "$p"
expect_rc "허용되지 않은 step if" "$p" "$CONTRACT" 1

p="$TMP/step-continue.yml"; cp "$WF" "$p"
ruby -e 'p=ARGV[0]; s=File.read(p).sub("      - name: 인수 검사 hs-a4", "      - name: 인수 검사 hs-a4\n        continue-on-error: false"); File.write(p,s)' "$p"
expect_rc "continue-on-error 키 존재" "$p" "$CONTRACT" 1

p="$TMP/job-if.yml"; cp "$WF" "$p"
ruby -e 'p=ARGV[0]; s=File.read(p).sub("    runs-on: ubuntu-latest", "    if: ${{ false }}\n    runs-on: ubuntu-latest"); File.write(p,s)' "$p"
expect_rc "보호 job if" "$p" "$CONTRACT" 1

expect_rc "workflow 파일 없음" "$TMP/no-workflow.yml" "$CONTRACT" 2
expect_rc "계약 파일 없음" "$WF" "$TMP/no-contract.json" 2
printf 'jobs: [broken\n' > "$TMP/broken.yml"
expect_rc "workflow 파싱 불가" "$TMP/broken.yml" "$CONTRACT" 2
printf '{broken\n' > "$TMP/broken.json"
expect_rc "계약 파싱 불가" "$WF" "$TMP/broken.json" 2
printf '{"schema_version":1,"workflow":".github/workflows/verify.yml","protected_steps":[]}\n' > "$TMP/zero.json"
expect_rc "counter-10 보호 대상 0개" "$WF" "$TMP/zero.json" 2

current=$(git status --porcelain)
if [ "$current" = "$SNAPSHOT" ]; then record 0 "원본 저장소 상태 불변" "before/after 동일"
else record 1 "원본 저장소 상태 불변" "변경 발생"; fi

printf 'CHECKED: %d\n' "$checked"
if [ "$fail" -eq 0 ]; then echo "VERDICT: PASS"; else echo "VERDICT: FAIL"; fi
exit "$fail"
