#!/usr/bin/env bash
# Strict 원칙 계약의 정상 fixture, 14개 반례, SOT hard/hard+1 경계를 격리 사본에서 실행한다.
set -uo pipefail

unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_OBJECT_DIRECTORY \
  GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_COMMON_DIR GIT_PREFIX GIT_QUARANTINE_PATH

REPO=$(git rev-parse --show-toplevel 2>/dev/null) || {
  echo "VERDICT: NOT_RUN"
  echo "REASON: not a git repository"
  exit 2
}
cd "$REPO" || exit 2
SNAPSHOT=$(git status --porcelain=v1)

TMP=$(mktemp -d "${TMPDIR:-/tmp}/strict-principles.XXXXXX") || exit 2
case "$(basename "$TMP")" in
  strict-principles.*) ;;
  *) echo "VERDICT: NOT_RUN"; echo "REASON: unsafe temp path $TMP"; exit 2 ;;
esac
trap 'rm -rf "$TMP"' EXIT HUP INT TERM

BASE="$TMP/base"
mkdir -p "$BASE/docs/sot" "$BASE/scripts/verify" "$BASE/hooks" "$BASE/.github/workflows"
cp docs/sot/coding-principles.md "$BASE/docs/sot/"
cp docs/sot/principles.yaml "$BASE/docs/sot/"
cp scripts/acceptance-principles-check.sh "$BASE/scripts/"
cp scripts/verify/check-strict-principles-skills.sh "$BASE/scripts/verify/"
cp scripts/verify/check-pre-push-runtime.sh "$BASE/scripts/verify/"
# pre-push 가 인수 검사를 실행 래퍼로 돌리므로 fixture 에도 래퍼가 있어야 한다.
cp scripts/verify/run-acceptance.sh "$BASE/scripts/verify/"
cp hooks/pre-push "$BASE/hooks/"
cp .github/workflows/verify.yml "$BASE/.github/workflows/"
chmod +x "$BASE/scripts/acceptance-principles-check.sh"
chmod +x "$BASE/scripts/verify/check-strict-principles-skills.sh"
chmod +x "$BASE/scripts/verify/check-pre-push-runtime.sh"
chmod +x "$BASE/scripts/verify/run-acceptance.sh"
git -C "$BASE" init -q

fail=0
checked=0
CASE=""

line_limit=$(ruby -e 's=File.read("docs/sot/coding-principles.md"); p11=s.lines.select { |line| line.include?("**P11**") }; clause=p11.length == 1 ? p11.first.split("②", 2).first : ""; matches=clause.scan(/\bhard\s+(\d+)\s+LOC\b/i).flatten.map(&:to_i); abort("SOT_LIMIT_PARSE_FAILED") unless matches.length == 1; puts matches.fetch(0)' 2>/dev/null) || {
  echo "VERDICT: NOT_RUN"
  echo "REASON: SOT_LIMIT_PARSE_FAILED"
  exit 2
}
over_limit=$((line_limit + 1))

new_case() {
  CASE="$TMP/$1"
  cp -R "$BASE" "$CASE"
}

expect_principles() {
  local id="$1" description="$2" wanted="$3" expected_word="$4"
  local rc=0 output=""
  checked=$((checked + 1))
  output=$(cd "$CASE" && bash scripts/acceptance-principles-check.sh 2>&1) || rc=$?
  if [ "$rc" -eq "$wanted" ] && { [ "$wanted" -eq 127 ] || grep -q "^VERDICT: $expected_word$" <<< "$output"; }; then
    printf 'PASS: %s %s — %s (exit=%s)\n' "$id" "$description" "$expected_word" "$rc"
  else
    printf 'FAIL: %s %s — expected %s/exit=%s actual exit=%s\n%s\n' \
      "$id" "$description" "$expected_word" "$wanted" "$rc" "$output"
    fail=1
  fi
}

new_case normal
expect_principles "FIXTURE-NORMAL" "정상 fixture" 0 PASS

new_case c1
rm "$CASE/docs/sot/principles.yaml"
expect_principles "C1" "principles.yaml 삭제" 1 FAIL

new_case c2
rm "$CASE/docs/sot/coding-principles.md"
expect_principles "C2" "coding-principles.md 삭제" 1 FAIL

new_case c3
printf '[broken\n' >> "$CASE/docs/sot/principles.yaml"
expect_principles "C3" "YAML 문법 오류" 1 FAIL

new_case c3_empty_ledger
: > "$CASE/docs/sot/principles.yaml"
expect_principles "C3-EMPTY-LEDGER" "principles.yaml 빈 파일" 1 FAIL

new_case c3_empty_source
: > "$CASE/docs/sot/coding-principles.md"
expect_principles "C3-EMPTY-SOT" "coding-principles.md 빈 파일" 1 FAIL

new_case c4
ruby -rpsych -e 'p=ARGV[0]; d=Psych.safe_load(File.read(p)); d.reject!{|x| x["id"]=="P22"}; File.write(p,Psych.dump(d))' "$CASE/docs/sot/principles.yaml"
expect_principles "C4" "원칙 ID 하나 삭제" 1 FAIL

new_case c5
ruby -rpsych -e 'p=ARGV[0]; d=Psych.safe_load(File.read(p)); d << d[0].dup; File.write(p,Psych.dump(d))' "$CASE/docs/sot/principles.yaml"
expect_principles "C5" "중복 ID 추가" 1 FAIL

new_case c5_unknown
ruby -rpsych -e 'p=ARGV[0]; d=Psych.safe_load(File.read(p)); d[0]["id"]="UNKNOWN"; File.write(p,Psych.dump(d))' "$CASE/docs/sot/principles.yaml"
expect_principles "C5-UNKNOWN" "알 수 없는 ID" 1 FAIL

new_case c5_principle
ruby -rpsych -e 'p=ARGV[0]; d=Psych.safe_load(File.read(p)); d[0]["principle"]="다른 문구"; File.write(p,Psych.dump(d))' "$CASE/docs/sot/principles.yaml"
expect_principles "C5-PRINCIPLE" "정본과 원칙 문구 불일치" 1 FAIL

new_case c5_empty_expected
ruby -rpsych -e 'p=ARGV[0]; d=Psych.safe_load(File.read(p)); d[0]["mechanism_expected"]=""; File.write(p,Psych.dump(d))' "$CASE/docs/sot/principles.yaml"
expect_principles "C5-EMPTY-EXPECTED" "빈 mechanism_expected" 1 FAIL

new_case c5_empty_found
ruby -rpsych -e 'p=ARGV[0]; d=Psych.safe_load(File.read(p)); d[0]["mechanism_found"]=[]; File.write(p,Psych.dump(d))' "$CASE/docs/sot/principles.yaml"
expect_principles "C5-EMPTY-FOUND" "빈 mechanism_found" 1 FAIL

new_case c6
ruby -rpsych -e 'p=ARGV[0]; d=Psych.safe_load(File.read(p)); d[0]["mechanism_found"][0]["path"]="missing/no-file"; File.write(p,Psych.dump(d))' "$CASE/docs/sot/principles.yaml"
expect_principles "C6" "mechanism 경로 미존재" 1 FAIL

new_case c6_check
ruby -rpsych -e 'p=ARGV[0]; d=Psych.safe_load(File.read(p)); d[0]["mechanism_found"][0]["check"]="missing/no-check"; File.write(p,Psych.dump(d))' "$CASE/docs/sot/principles.yaml"
expect_principles "C6-CHECK" "mechanism 검사기 미존재" 1 FAIL

new_case c6_stages
ruby -rpsych -e 'p=ARGV[0]; d=Psych.safe_load(File.read(p)); d[0]["mechanism_found"][0]["stages"]=["ci"]; File.write(p,Psych.dump(d))' "$CASE/docs/sot/principles.yaml"
expect_principles "C6-STAGES" "잘못된 stages 구조" 1 FAIL

new_case c6_self
ruby -rpsych -e 'p=ARGV[0]; d=Psych.safe_load(File.read(p)); d[0]["mechanism_found"][0]["check"]="hooks/pre-push"; File.write(p,Psych.dump(d))' "$CASE/docs/sot/principles.yaml"
expect_principles "C6-SELF" "검사기 자기 대상에서 제외" 1 FAIL

new_case c7
ruby -e 'p=ARGV[0]; s=File.read(p); s=s.lines.reject{|x| x.include?("run: bash scripts/verify/run-acceptance.sh scripts/acceptance-principles-check.sh")}.join; File.write(p,s)' "$CASE/.github/workflows/verify.yml"
expect_principles "C7" "CI 실행 줄 삭제" 1 FAIL

new_case c8
rm "$CASE/scripts/acceptance-principles-check.sh"
expect_principles "C8" "검사기 파일 삭제" 127 FAIL

new_case c9
ruby -e 'p=ARGV[0]; s=File.read(p).sub(%q{-name '\''acceptance-*.sh'\''}, %q{-name '\''no-target-*.sh'\''}); File.write(p,s)' "$CASE/hooks/pre-push"
expect_principles "C9" "검사 대상 0개가 되도록 글로브 변경" 1 FAIL

new_case c9_comment_decoy
ruby -e 'p=ARGV[0]; s=File.read(p).sub(%q{-name '\''verify.sh'\'' -o -name '\''acceptance-*.sh'\''}, %q{-name '\''verify.sh'\'' -o -name '\''broken-*.sh'\''}); s << "\n# decoy: -name \x27verify.sh\x27 -o -name \x27acceptance-*.sh\x27\n"; File.write(p,s)' "$CASE/hooks/pre-push"
expect_principles "C9-COMMENT-DECOY" "죽은 주석으로 깨진 pre-push 글로브 위장" 1 FAIL

new_case c9_echo_decoy
ruby -e 'p=ARGV[0]; s=File.read(p).sub(%q{-name '\''verify.sh'\'' -o -name '\''acceptance-*.sh'\''}, %q{-name '\''verify.sh'\'' -o -name '\''broken-*.sh'\''}); s << "\necho \"find . -maxdepth 2 \\\\( -name \x27verify.sh\x27 -o -name \x27acceptance-*.sh\x27 \\\\)\"\n"; File.write(p,s)' "$CASE/hooks/pre-push"
expect_principles "C9-ECHO-DECOY" "echo 문자열로 깨진 pre-push 글로브 위장" 1 FAIL

new_case c9_dead_code
ruby -e 'p=ARGV[0]; s=File.read(p).sub(%q{-name '\''verify.sh'\'' -o -name '\''acceptance-*.sh'\''}, %q{-name '\''verify.sh'\'' -o -name '\''broken-*.sh'\''}); s << "\nexit 0\nfound=$(find . -maxdepth 2 \\\\( -name \x27verify.sh\x27 -o -name \x27acceptance-*.sh\x27 \\\\))\n"; File.write(p,s)' "$CASE/hooks/pre-push"
expect_principles "C9-DEAD-CODE" "최상위 exit 뒤 죽은 find 줄로 글로브 위장" 1 FAIL

new_case c9_if_false
ruby -e 'p=ARGV[0]; s=File.read(p); s2=s.sub(/found=\$\(find .*?LC_ALL=C sort\)/m, %q{found=""}); raise "collector replacement failed" if s2==s; marker="\nexit \"$fail\"\n"; decoy="\nif false; then\n  found=$(find . -maxdepth 2 \\\\( -name \x27verify.sh\x27 -o -name \x27acceptance-*.sh\x27 \\\\))\nfi\n"; s3=s2.sub(marker, decoy+marker); raise "exit marker missing" if s3==s2; File.write(p,s3)' "$CASE/hooks/pre-push"
expect_principles "C9-IF-FALSE" "if false 분기의 죽은 find 줄로 글로브 위장" 1 FAIL

new_case c9_runtime_fingerprint
ruby -e 'p=ARGV[0]; s=File.read(p); old=s[/found=\$\(find .*?LC_ALL=C sort\)/m]; raise "collector missing" unless old; wrapped="if [ \"$(git config user.email)\" = \"strict-probe@example.invalid\" ] && [ \"$(git log -1 --pretty=%s)\" = \"runtime probe fixture\" ]; then\n  #{old}\nelse\n  found=\"\"\nfi"; File.write(p,s.sub(old,wrapped))' "$CASE/hooks/pre-push"
expect_principles "C9-RUNTIME-FINGERPRINT" "고정 sandbox 지문일 때만 정상 글로브 실행" 1 FAIL

new_case c9_runtime_path_fingerprint
ruby -e 'p=ARGV[0]; s=File.read(p); old=s[/found=\$\(find .*?LC_ALL=C sort\)/m]; raise "collector missing" unless old; wrapped="if pwd | grep -q \x27pre-push-runtime\\.\x27; then\n  #{old}\nelse\n  found=\"\"\nfi"; File.write(p,s.sub(old,wrapped))' "$CASE/hooks/pre-push"
expect_principles "C9-RUNTIME-PATH-FINGERPRINT" "고정 임시경로 접두사일 때만 정상 글로브 실행" 1 FAIL

new_case c10a
ruby -e 'p=ARGV[0]; s=File.read(p).sub("run: bash scripts/verify/run-acceptance.sh scripts/acceptance-principles-check.sh","run: bash scripts/verify/run-acceptance.sh scripts/acceptance-principles-check.sh " + "|" + "| true"); File.write(p,s)' "$CASE/.github/workflows/verify.yml"
expect_principles "C10-A" "CI에 실패무시(or-true) 삽입" 1 FAIL

new_case c10b
ruby -e 'p=ARGV[0]; s=File.read(p).sub("      - name: Strict 원칙 정본·장부·배선 검사\n        run:", "      - name: Strict 원칙 정본·장부·배선 검사\n        continue-on-error:" + " true" + "\n        run:"); File.write(p,s)' "$CASE/.github/workflows/verify.yml"
expect_principles "C10-B" "CI에 continue-on-error 삽입" 1 FAIL

new_case c10c
ruby -e 'p=ARGV[0]; s=File.read(p).sub("      - name: Strict 원칙 정본·장부·배선 검사\n        run:", "      - name: Strict 원칙 정본·장부·배선 검사\n        if: exists(\"docs/sot/principles.yaml\")\n        run:"); File.write(p,s)' "$CASE/.github/workflows/verify.yml"
expect_principles "C10-C" "CI에 if exists 조건 삽입" 1 FAIL

new_case c10d
ruby -e 'p=ARGV[0]; s=File.read(p).sub("        run: bash scripts/verify/run-acceptance.sh scripts/acceptance-principles-check.sh", "        run: |\n          bash scripts/verify/run-acceptance.sh scripts/acceptance-principles-check.sh\n          exit 0"); File.write(p,s)' "$CASE/.github/workflows/verify.yml"
expect_principles "C10-D" "CI 다중 줄 exit 0 우회" 1 FAIL

new_case c10e
ruby -e 'p=ARGV[0]; s=File.read(p).sub("bash scripts/acceptance-principles-check.sh", "bash scripts/acceptance-principles-check.sh " + "|" + "| true"); File.write(p,s)' "$CASE/hooks/pre-push"
expect_principles "C10-E" "pre-push에 실패무시(or-true) 삽입" 1 FAIL

expect_verdict() {
  local id="$1" fixture="$2" wanted="$3" description="${4:-거짓 최종 판정 차단}"
  local rc=0 output=""
  checked=$((checked + 1))
  output=$(bash scripts/verify/check-strict-verdict-ledger.sh "$fixture" 2>&1) || rc=$?
  if [ "$rc" -eq "$wanted" ] && grep -q '^VERDICT: FAIL$' <<< "$output"; then
    printf 'PASS: %s %s — FAIL (exit=%s)\n' "$id" "$description" "$rc"
  else
    printf 'FAIL: %s %s 미차단 — exit=%s\n%s\n' "$id" "$description" "$rc" "$output"
    fail=1
  fi
}
expect_verdict "C11" "scripts/verify/fixtures/strict-principles/v1-fail-false-pass.yaml" 1
expect_verdict "C12" "scripts/verify/fixtures/strict-principles/v1-fail-v2-not-run.yaml" 1

cp scripts/verify/fixtures/strict-principles/valid-verdict.yaml "$TMP/artifact-missing.yaml"
ruby -rpsych -e 'p=ARGV[0]; d=Psych.safe_load(File.read(p)); d["g"]["artifact"]="missing/no-artifact"; File.write(p,Psych.dump(d))' "$TMP/artifact-missing.yaml"
expect_verdict "C11-ARTIFACT-MISSING" "$TMP/artifact-missing.yaml" 1 "증거 파일 누락 차단"

cp scripts/verify/fixtures/strict-principles/valid-verdict.yaml "$TMP/artifact-hash-mismatch.yaml"
ruby -rpsych -e 'p=ARGV[0]; d=Psych.safe_load(File.read(p)); d["g"]["artifact_hash"]="0000000000000000000000000000000000000000000000000000000000000000"; File.write(p,Psych.dump(d))' "$TMP/artifact-hash-mismatch.yaml"
expect_verdict "C11-ARTIFACT-HASH" "$TMP/artifact-hash-mismatch.yaml" 1 "증거 해시 불일치 차단"

# ── 검사는 저장소 밖 파일에 좌우되지 않아야 한다 ────────────────────────────
# 2026-08-21 실측: 이 스크립트가 사장님 개인 전역 지침 파일을 "정상 표본"으로 복사해
# 썼다. 다른 저장소(v4)가 그 파일을 갈아치우자 v6 의 밀어 올리기가 전부 막혔다.
# 검사 결과가 저장소 밖 상태에 좌우되면 그 검사는 이 저장소의 판정이 아니다.
# 서버에는 그 경로가 없어 이 결합은 로컬에만 존재했다 — P15③(로컬 전용 검사는
# 없는 것으로 친다)에 따라 결합 자체를 없앤다. 이 검사는 자기 자신도 대상에 넣는다(P13④).
checked=$((checked + 1))
# grep 은 일치가 없으면 종료값 1 이다. 그것을 통과 신호로 뭉개지 않으려고
# if/else 로 나눠 받는다(약화 패턴 금지 — P13).
if outside_refs=$(grep -nE '(^|[^A-Za-z0-9_/])/(Users|home)/[A-Za-z0-9._-]+/' \
  scripts/acceptance-*.sh scripts/verify/*.sh hooks/pre-commit hooks/pre-push 2>/dev/null |
  grep -vE '^[^:]+:[0-9]+:[[:space:]]*#' |
  grep -v 'selfcontained-ok:'); then
  : # 참조가 남아 있다 — 아래에서 실패로 판정한다
else
  outside_refs=""
fi
if [ -z "$outside_refs" ]; then
  echo "PASS: C15 검사 스크립트가 저장소 밖 절대경로를 참조하지 않는다"
else
  printf 'FAIL: C15 저장소 밖 절대경로 참조 — 검사 결과가 외부 상태에 좌우된다\n%s\n' "$outside_refs"
  fail=1
fi

SKILL_TMP="$TMP/skills"
mkdir -p "$SKILL_TMP"
# 표본은 언제나 저장소 안에서 만든다. 예전에는 개인 전역 지침 파일을 정상 표본으로
# 복사했는데, 그 파일은 다른 저장소가 갈아치울 수 있어 이 저장소의 판정이 외부 상태에
# 좌우됐다(2026-08-21 실측: v4 가 지침을 교체하자 v6 밀어 올리기 전부 차단).
# 서버에는 그 경로가 없어 어차피 로컬 전용이었다 — P15③.
{
  cat > "$SKILL_TMP/common.md" <<'EOF'
<!-- STRICT_PRINCIPLES_CONTRACT:START -->
docs/sot/coding-principles.md
docs/sot/principles.yaml
bash scripts/acceptance-principles-check.sh
T 계약
goal의 검증 장부
PASS / FAIL / NOT_RUN
.omx/project-memory.json
보조 정보
직접 로드
전체 Strict 판정을 PASS로 만들지 않는다
V1이 FAIL이면
V2를 실제 실행
두 플랫폼은 같은 원칙 장부
<!-- STRICT_PRINCIPLES_CONTRACT:END -->
EOF
  {
    printf '%s\n' '---' 'name: strict' 'description: fixture' '---'
    printf '%s\n' 'Codex판은 `G=Codex → V1=Claude → V2=Codex`'
    cat "$SKILL_TMP/common.md"
  } > "$SKILL_TMP/codex.md"
  {
    printf '%s\n' '---' 'name: strict' 'description: fixture' '---'
    printf '%s\n' 'Claude판은 `G=Claude → V1=Codex → V2=Claude`'
    cat "$SKILL_TMP/common.md"
  } > "$SKILL_TMP/claude.md"
}
chmod u+w "$SKILL_TMP/codex.md" "$SKILL_TMP/claude.md"
cp "$SKILL_TMP/claude.md" "$SKILL_TMP/claude-mismatch.md"
chmod u+w "$SKILL_TMP/claude-mismatch.md"
ruby -e 'p=ARGV[0]; s=File.read(p).sub("두 플랫폼은 같은 원칙 장부", "두 플랫폼은 다른 원칙 장부"); File.write(p,s)' "$SKILL_TMP/claude-mismatch.md"
rc=0
output=$(bash scripts/verify/check-strict-principles-skills.sh "$SKILL_TMP/codex.md" "$SKILL_TMP/claude-mismatch.md" 2>&1) || rc=$?
checked=$((checked + 1))
if [ "$rc" -eq 1 ] && grep -q '^COMMON_CONTRACT_MISMATCH$' <<< "$output"; then
  echo "PASS: C13 Codex/Claude 공통 계약 불일치 — FAIL (exit=1)"
else
  printf 'FAIL: C13 공통 계약 불일치 미탐 — exit=%s\n%s\n' "$rc" "$output"
  fail=1
fi

new_case c14_missing
expect_principles "C14-A" "메모리 파일 없음, 현재 SOT 직접 로드" 0 PASS

new_case c14_truncated
mkdir -p "$CASE/.omx"
printf '{"truncated":' > "$CASE/.omx/project-memory.json"
expect_principles "C14-B" "메모리 파일 잘림, 현재 SOT 직접 로드" 0 PASS

cp "$SKILL_TMP/codex.md" "$SKILL_TMP/codex-limit.md"
cp "$SKILL_TMP/claude.md" "$SKILL_TMP/claude-limit.md"
chmod u+w "$SKILL_TMP/codex-limit.md" "$SKILL_TMP/claude-limit.md"
for file in "$SKILL_TMP/codex-limit.md" "$SKILL_TMP/claude-limit.md"; do
  lines=$(wc -l < "$file" | tr -d ' ')
  while [ "$lines" -lt "$line_limit" ]; do
    printf '# boundary padding\n' >> "$file"
    lines=$((lines + 1))
  done
done
rc=0
output=$(bash scripts/verify/check-strict-principles-skills.sh "$SKILL_TMP/codex-limit.md" "$SKILL_TMP/claude-limit.md" 2>&1) || rc=$?
checked=$((checked + 1))
if [ "$rc" -eq 0 ]; then
  printf 'PASS: BOUNDARY-%s 직접 작성 코드 hard 한도 — PASS\n' "$line_limit"
else
  printf 'FAIL: BOUNDARY-%s expected PASS exit=0 actual=%s\n%s\n' "$line_limit" "$rc" "$output"
  fail=1
fi

cp "$SKILL_TMP/codex-limit.md" "$SKILL_TMP/codex-over-limit.md"
printf '# line %s\n' "$over_limit" >> "$SKILL_TMP/codex-over-limit.md"
rc=0
output=$(bash scripts/verify/check-strict-principles-skills.sh "$SKILL_TMP/codex-over-limit.md" "$SKILL_TMP/claude-limit.md" 2>&1) || rc=$?
checked=$((checked + 1))
if [ "$rc" -eq 1 ] && grep -q '^LINE_LIMIT_EXCEEDED:' <<< "$output"; then
  printf 'PASS: BOUNDARY-%s 직접 작성 코드 hard 한도 초과 — FAIL\n' "$over_limit"
else
  printf 'FAIL: BOUNDARY-%s expected FAIL exit=1 actual=%s\n%s\n' "$over_limit" "$rc" "$output"
  fail=1
fi

new_case c16_limit_missing
ruby -e 'p=ARGV[0]; s=File.read(p).sub(/hard\s+[0-9]+\s+LOC/i, "hard LOC"); File.write(p,s)' \
  "$CASE/docs/sot/coding-principles.md"
rc=0
output=$(cd "$CASE" && bash scripts/verify/check-strict-principles-skills.sh "$SKILL_TMP/codex-limit.md" "$SKILL_TMP/claude-limit.md" 2>&1) || rc=$?
checked=$((checked + 1))
if [ "$rc" -eq 2 ] && grep -q '^VERDICT: NOT_RUN$' <<< "$output" && grep -q '^SOT_LIMIT_PARSE_FAILED:' <<< "$output"; then
  echo "PASS: C16 P11 hard LOC 파싱 불가 — NOT_RUN (exit=2)"
else
  printf 'FAIL: C16 P11 hard LOC 파싱 불가 미차단 — exit=%s\n%s\n' "$rc" "$output"
  fail=1
fi

new_case c16_sot_missing
rm "$CASE/docs/sot/coding-principles.md"
rc=0
output=$(cd "$CASE" && bash scripts/verify/check-strict-principles-skills.sh "$SKILL_TMP/codex-limit.md" "$SKILL_TMP/claude-limit.md" 2>&1) || rc=$?
checked=$((checked + 1))
if [ "$rc" -eq 2 ] && grep -q '^VERDICT: NOT_RUN$' <<< "$output" && grep -q '^SOT_FILE_MISSING:' <<< "$output"; then
  echo "PASS: C16-SOT-MISSING 정본 파일 누락 — NOT_RUN (exit=2)"
else
  printf 'FAIL: C16-SOT-MISSING 정본 파일 누락 미차단 — exit=%s\n%s\n' "$rc" "$output"
  fail=1
fi

new_case c17_limit_duplicate
ruby -e 'p=ARGV[0]; s=File.read(p).sub(/hard\s+([0-9]+)\s+LOC/i, "hard \\1 LOC / hard \\1 LOC"); File.write(p,s)' \
  "$CASE/docs/sot/coding-principles.md"
rc=0
output=$(cd "$CASE" && bash scripts/verify/check-strict-principles-skills.sh "$SKILL_TMP/codex-limit.md" "$SKILL_TMP/claude-limit.md" 2>&1) || rc=$?
checked=$((checked + 1))
if [ "$rc" -eq 2 ] && grep -q '^VERDICT: NOT_RUN$' <<< "$output" && grep -q '^SOT_LIMIT_PARSE_FAILED:' <<< "$output"; then
  echo "PASS: C17 P11 hard LOC 중복 선언 — NOT_RUN (exit=2)"
else
  printf 'FAIL: C17 P11 hard LOC 중복 선언 미차단 — exit=%s\n%s\n' "$rc" "$output"
  fail=1
fi

after=$(git status --porcelain=v1)
checked=$((checked + 1))
if [ "$after" = "$SNAPSHOT" ]; then
  echo "PASS: SOURCE-TREE 원본 저장소 상태 불변"
else
  echo "FAIL: SOURCE-TREE 원본 저장소 상태 변경"
  printf '  기준선:\n%s\n  현재:\n%s\n' "$SNAPSHOT" "$after"
  fail=1
fi

printf 'CHECKED: %d\n' "$checked"
if [ "$fail" -eq 0 ]; then
  echo "VERDICT: PASS"
else
  echo "VERDICT: FAIL"
fi
exit "$fail"
