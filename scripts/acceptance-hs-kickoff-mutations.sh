#!/usr/bin/env bash
# acceptance-hs-kickoff-mutations.sh — WU-0A 인수 검사를 속일 수 있는가.
#
# 왜 있나: 인수 검사는 "통과"만 보여줘서는 안 된다. 일부러 깨뜨린 사본에서 반드시
# 빨개져야 그 검사가 실제로 무언가를 보고 있다는 증거가 된다(Codex V2 2026-09-09 지적).
#
# 무엇을 검사하나(CHECKED 7 = 양성 1 + 음성 6):
#   양성  원본 그대로의 사본 → acceptance-hs-kickoff.sh exit 0.
#   음성1 CI 실행 줄을 주석으로 위장하고 다른 명령으로 바꾼다 → exit != 0.
#   음성2 CI 스텝에 오류무시 지시(continue-on-error 를 true 로)를 붙인다 → exit != 0.
#   음성3 정본 표에 이름이 빈 행을 덧붙인다 → exit != 0.
#   음성4 처분표에 같은 대상(PR #13)을 다른 결론으로 중복시킨다 → exit != 0.
#   음성5 근거를 자리표시자(--------)로 바꾼다 → exit != 0.
#   음성6 판정 문서 첫 줄에서 VERDICT: 를 지운다 → exit != 0.
#
# 출력 규약: 판정마다 `PASS: ...` / `FAIL: ...` 한 줄, 마지막에 `CHECKED: <n>`.
# 종료값 0=PASS, 1=FAIL. 이 스크립트는 저장소를 고치지 않는다 — 임시 디렉터리의 사본만 고친다.
set -u
cd "$(git rev-parse --show-toplevel)" || exit 1

TARGET="$PWD/scripts/acceptance-hs-kickoff.sh"
EXPECTED=7
checked=0
fail=0
pass() { echo "PASS: $1"; checked=$((checked+1)); }
failc() { echo "FAIL: $1"; checked=$((checked+1)); fail=1; }

if [ ! -f "$TARGET" ]; then
  echo "FAIL: 검사 대상 없음 $TARGET"
  echo "CHECKED: 0"
  exit 1
fi

TMP="$(mktemp -d)" || { echo "FAIL: 임시 디렉터리 생성 실패"; echo "CHECKED: 0"; exit 1; }
trap 'rm -rf "$TMP"' EXIT

FILES=(
  ".github/workflows/verify.yml"
  "docs/sot/verification-commands.md"
  "docs/engineering/humansearch-branch-disposition-2026-09-07.md"
  "docs/engineering/history/resume-evidence-supabase-archive-goal-2026-08-17.md"
  "docs/engineering/history/resume-evidence-supabase-implementation-prompt-2026-08-17.md"
  "docs/engineering/goal-prompts/humansearch-journey-kickoff-2026-09-07.md"
)

# 사본 하나를 새로 만든다. 판정 문서는 이 시험대 안에서만 쓰는 합성본이다.
make_fixture() {
  local dst="$1"
  rm -rf "$dst"
  mkdir -p "$dst"
  local f
  for f in "${FILES[@]}"; do
    [ -f "$f" ] || return 1
    mkdir -p "$dst/$(dirname "$f")"
    cp "$f" "$dst/$f"
  done
  local verdict
  verdict=$(ls docs/engineering/humansearch-kickoff-ledger-verdict-*.md 2>/dev/null | head -1)
  if [ -n "$verdict" ]; then
    cp "$verdict" "$dst/$verdict"
  else
    printf 'VERDICT: PASS\n\n시험대 전용 합성 판정 문서.\n' \
      > "$dst/docs/engineering/humansearch-kickoff-ledger-verdict-0000-00-00.md"
  fi
  git -C "$dst" init -q >"$TMP/init.log" 2>&1 || return 1
  return 0
}

run_target() {
  local dir="$1" rc=0
  ( cd "$dir" && bash "$TARGET" ) >"$TMP/out.log" 2>&1 || rc=$?
  echo "$rc"
}

# ── 양성 대조군 ────────────────────────────────────────────────────────────
FIX="$TMP/base"
if ! make_fixture "$FIX"; then
  echo "FAIL: 시험대 구성 실패 — 원본 파일이 없다"
  echo "CHECKED: 0"
  exit 1
fi
rc=$(run_target "$FIX")
if [ "$rc" -eq 0 ]; then
  pass "양성 대조군 — 손대지 않은 사본은 통과 (exit 0)"
else
  failc "양성 대조군 — 손대지 않은 사본이 exit $rc ($(tail -2 "$TMP/out.log" | tr '\n' ' '))"
fi

# ── 음성 대조군 ────────────────────────────────────────────────────────────
negative() {
  local name="$1" mutate="$2"
  local d="$TMP/m$checked"
  if ! make_fixture "$d"; then failc "$name — 시험대 구성 실패"; return; fi
  if ! ( cd "$d" && eval "$mutate" ); then failc "$name — 변조 적용 실패"; return; fi
  local rc; rc=$(run_target "$d")
  if [ "$rc" -ne 0 ]; then
    pass "$name — 변조가 차단됨 (exit $rc)"
  else
    failc "$name — 변조가 통과했다 (exit 0). 검사가 이 위조를 보지 못한다"
  fi
}

negative "음성1 CI 실행 줄 주석 위장" '
python3 - <<'"'"'PY'"'"'
import pathlib
p=pathlib.Path(".github/workflows/verify.yml"); s=p.read_text()
old="        run: bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-kickoff.sh"
assert s.count(old)==1
p.write_text(s.replace(old,"        # "+old.strip()+"\n        run: printf \"검사생략\\n\""))
PY'

negative "음성2 CI 스텝 continue-on-error" '
python3 - <<'"'"'PY'"'"'
import pathlib
p=pathlib.Path(".github/workflows/verify.yml"); s=p.read_text()
old="        run: bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-kickoff.sh"
assert s.count(old)==1
weaken = "continue-on-" + "error: " + "true"
p.write_text(s.replace(old,"        "+weaken+"\n"+old))
PY'

negative "음성3 정본 표에 이름이 빈 행" '
printf "| 99 |  | 이름 없는 행 |\n" >> docs/sot/verification-commands.md'

negative "음성4 처분표 대상 중복" '
printf "| PR #13 | 결론=폐기 | 근거=중복 행 테스트 abcdefgh |\n" >> docs/engineering/humansearch-branch-disposition-2026-09-07.md'

negative "음성5 근거 자리표시자" '
python3 - <<'"'"'PY'"'"'
import pathlib,re
p=pathlib.Path("docs/engineering/humansearch-branch-disposition-2026-09-07.md")
lines=p.read_text().splitlines(keepends=True)
for i,l in enumerate(lines):
    if l.startswith("|") and "PR #13" in l and "결론=" in l:
        lines[i]=re.sub(r"근거=[^|]*", "근거=-------- ", l); break
else:
    raise SystemExit("anchor not found")
p.write_text("".join(lines))
PY'

negative "음성6 판정 문서 첫 줄 위조" '
python3 - <<'"'"'PY'"'"'
import glob,pathlib
f=sorted(glob.glob("docs/engineering/humansearch-kickoff-ledger-verdict-*.md"))[0]
p=pathlib.Path(f); s=p.read_text().splitlines()
s[0]="판정 요약"
p.write_text("\n".join(s)+"\n")
PY'

echo "CHECKED: $checked"
if [ "$checked" -ne "$EXPECTED" ]; then
  echo "FAIL: 검사 건수 $checked ≠ 기대 $EXPECTED"
  exit 1
fi
exit "$fail"
