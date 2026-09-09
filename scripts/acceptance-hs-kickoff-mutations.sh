#!/usr/bin/env bash
# acceptance-hs-kickoff-mutations.sh — WU-0A 인수 검사를 속일 수 있는가.
#
# 왜 있나: 인수 검사는 "통과"만 보여줘서는 안 된다. 일부러 깨뜨린 사본에서 반드시
# 빨개져야 그 검사가 실제로 무언가를 보고 있다는 증거가 된다(Codex V2 2026-09-09 지적).
#
# 무엇을 검사하나(CHECKED 26 = 양성 7 + 음성 19):
#   양성  원본 그대로의 사본 → acceptance-hs-kickoff.sh exit 0.
#   음성1 CI 실행 줄을 주석으로 위장하고 다른 명령으로 바꾼다 → exit != 0.
#   음성2 CI 스텝에 오류무시 지시(continue-on-error 를 true 로)를 붙인다 → exit != 0.
#   음성3 정본 표에 이름이 빈 행을 덧붙인다 → exit != 0.
#   음성4 처분표에 같은 대상(PR #13)을 다른 결론으로 중복시킨다 → exit != 0.
#   음성5 근거를 자리표시자(--------)로 바꾼다 → exit != 0.
#   음성6 판정 문서 첫 줄에서 VERDICT: 를 지운다 → exit != 0.
#   음성7 정답 실행 줄을 env 값 안에 미끼로 숨기고 실제 run 은 다른 명령으로 바꾼다 → exit != 0.
#   음성8 정본 표의 행 번호를 중복시킨다 → exit != 0.
#   음성9 진짜 처분 행을 코드 블록 안으로 숨긴다 → exit != 0.
#   양성2 코드 블록 안의 가짜 처분 행은 처분으로 세지 않는다 → exit 0(판정이 흔들리지 않는다).
#   음성11 run 키를 두 번 두고 뒤쪽을 다른 명령으로 덮어쓴다 → exit != 0.
#   음성12 조건 키를 따옴표로 감싸("if") 스텝을 끈다 → exit != 0.
#   음성13 오류무시 키를 따옴표로 감싼다 → exit != 0.
#   음성14 근거를 코드 스팬으로 감싼 뜻 없는 영숫자로 바꾼다 → exit != 0.
#   음성15 3칸 들여쓴 코드 펜스로 진짜 처분 행을 감싼다 → exit != 0.
#   양성3 워크플로 전체 들여쓰기를 옮긴다(의미 동등) → exit 0.
#   양성4 스텝에 timeout-minutes 를 끼운다(정상 설정) → exit 0.
#   음성16 스텝을 지우고 앞 스텝의 여러 줄 문자열 안에 머리글·실행 줄을 숨긴다 → exit != 0.
#   음성17 조건 키를 콜론 앞 공백으로 쓴다(if : false) → exit != 0.
#   음성18 run 키를 콜론 앞 공백으로 한 번 더 써서 덮어쓴다 → exit != 0.
#   음성19 물결표 펜스로 진짜 처분 행을 감싼다 → exit != 0.
#   양성5 run 값을 따옴표로 감싼다(같은 명령) → exit 0.
#   양성6 run 줄 뒤에 주석을 붙인다 → exit 0.
#   양성7 run 을 한 줄짜리 블록 스칼라로 쓴다 → exit 0.
#
# 음성은 종료값만 보지 않는다 — 기대한 실패 사유가 출력에 있어야 한다. 무관한 이유로
# 빨개진 것을 "막았다"로 세면 검사가 무엇을 보는지 알 수 없다(Codex V2 3회차 지적).
#   음성10 근거를 뜻 없는 영숫자(abcdefgh)로 바꾼다 → exit != 0.
#
# 출력 규약: 판정마다 `PASS: ...` / `FAIL: ...` 한 줄, 마지막에 `CHECKED: <n>`.
# 종료값 0=PASS, 1=FAIL. 이 스크립트는 저장소를 고치지 않는다 — 임시 디렉터리의 사본만 고친다.
set -u
cd "$(git rev-parse --show-toplevel)" || exit 1

TARGET="$PWD/scripts/acceptance-hs-kickoff.sh"
EXPECTED=26
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
  "scripts/verify/list-workflow-steps.py"
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
tree_hash() {
  find "$1" -type f -not -path '*/.git/*' | LC_ALL=C sort | xargs shasum 2>/dev/null | shasum | cut -d' ' -f1
}

# 변조해도 판정이 바뀌면 안 되는 시험(과잉 차단 방지). 기대 종료값 0.
positive() {
  local name="$1" mutate="$2"
  local d="$TMP/p$checked"
  if ! make_fixture "$d"; then failc "$name — 시험대 구성 실패"; return; fi
  local before after
  before=$(tree_hash "$d")
  if ! ( cd "$d" && eval "$mutate" ); then failc "$name — 변조 적용 실패(종료값)"; return; fi
  after=$(tree_hash "$d")
  if [ "$before" = "$after" ]; then failc "$name — 변조가 파일을 바꾸지 못했다(시험 무효)"; return; fi
  local rc; rc=$(run_target "$d")
  if [ "$rc" -eq 0 ]; then
    pass "$name — 판정이 흔들리지 않음 (exit 0)"
  else
    failc "$name — 무해한 변조에 FAIL 을 냈다 (exit $rc). 과잉 차단이다"
  fi
}

negative() {
  local name="$1" mutate="$2" expect="$3"
  local d="$TMP/m$checked"
  if ! make_fixture "$d"; then failc "$name — 시험대 구성 실패"; return; fi
  local before after
  before=$(tree_hash "$d")
  if ! ( cd "$d" && eval "$mutate" ); then failc "$name — 변조 적용 실패(종료값)"; return; fi
  after=$(tree_hash "$d")
  # 변조가 실제로 파일을 바꾸지 않았는데 "차단됨"으로 세면 거짓 초록이 된다.
  if [ "$before" = "$after" ]; then failc "$name — 변조가 파일을 바꾸지 못했다(시험 무효)"; return; fi
  local rc; rc=$(run_target "$d")
  if [ "$rc" -eq 0 ]; then
    failc "$name — 변조가 통과했다 (exit 0). 검사가 이 위조를 보지 못한다"
  elif ! /usr/bin/grep -q -- "$expect" "$TMP/out.log"; then
    failc "$name — 빨개지긴 했으나 사유가 다르다 (exit $rc, 기대 '$expect' 없음: $(/usr/bin/grep -m1 '^FAIL' "$TMP/out.log"))"
  else
    pass "$name — 기대한 사유로 차단됨 (exit $rc, '$expect')"
  fi
}

negative "음성1 CI 실행 줄 주석 위장" '
python3 - <<'"'"'PY'"'"'
import pathlib
p=pathlib.Path(".github/workflows/verify.yml"); s=p.read_text()
old="        run: bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-kickoff.sh"
assert s.count(old)==1
p.write_text(s.replace(old,"        # "+old.strip()+"\n        run: printf \"검사생략\\n\""))
PY' 'CI 배선 불량'

negative "음성2 CI 스텝 continue-on-error" '
python3 - <<'"'"'PY'"'"'
import pathlib
p=pathlib.Path(".github/workflows/verify.yml"); s=p.read_text()
old="        run: bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-kickoff.sh"
assert s.count(old)==1
weaken = "continue-on-" + "error: " + "true"
p.write_text(s.replace(old,"        "+weaken+"\n"+old))
PY' 'CI 배선 불량'

negative "음성3 정본 표에 이름이 빈 행" '
printf "| 99 |  | 이름 없는 행 |\n" >> docs/sot/verification-commands.md' 'CI 스텝 불일치'

negative "음성4 처분표 대상 중복" '
printf "| PR #13 | 결론=폐기 | 근거=중복 행 테스트 abcdefgh |\n" >> docs/engineering/humansearch-branch-disposition-2026-09-07.md' '처분이 둘 이상'

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
PY' '근거가 자리표시자'

negative "음성6 판정 문서 첫 줄 위조" '
python3 - <<'"'"'PY'"'"'
import glob,pathlib
f=sorted(glob.glob("docs/engineering/humansearch-kickoff-ledger-verdict-*.md"))[0]
p=pathlib.Path(f); s=p.read_text().splitlines()
s[0]="판정 요약"
p.write_text("\n".join(s)+"\n")
PY' '판정 문서 없음'

negative "음성7 env 미끼로 실행 줄 위장" '
python3 - <<'"'"'PY'"'"'
import pathlib
p=pathlib.Path(".github/workflows/verify.yml"); s=p.read_text()
old="        run: bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-kickoff.sh"
assert s.count(old)==1
bait = "        env:\n          BAIT: |\n" + "            " + old.strip() + "\n        run: printf \"검사생략\\n\""
p.write_text(s.replace(old, bait))
PY' 'CI 배선 불량'

negative "음성8 정본 표 행 번호 중복" '
python3 - <<'"'"'PY'"'"'
import pathlib,re
p=pathlib.Path("docs/sot/verification-commands.md"); lines=p.read_text().splitlines(keepends=True)
for i,l in enumerate(lines):
    m=re.match(r"^\| 29 \|", l)
    if m:
        lines[i]=re.sub(r"^\| 29 \|", "| 28 |", l); break
else:
    raise SystemExit("anchor not found")
p.write_text("".join(lines))
PY' 'CI 스텝 불일치'

negative "음성9 진짜 처분 행을 코드 블록 안으로 숨김" '
python3 - <<'"'"'PY'"'"'
import pathlib
p=pathlib.Path("docs/engineering/humansearch-branch-disposition-2026-09-07.md")
fence = chr(96)*3
lines=p.read_text().splitlines(keepends=True)
for i,l in enumerate(lines):
    if l.startswith("|") and "PR #13" in l and "결론=" in l:
        lines[i] = fence + "\n" + l + fence + "\n"; break
else:
    raise SystemExit("anchor not found")
p.write_text("".join(lines))
PY' '행 없음'

positive "양성2 코드 블록 안 가짜 처분 행" '
python3 - <<'"'"'PY'"'"'
import pathlib
p=pathlib.Path("docs/engineering/humansearch-branch-disposition-2026-09-07.md")
fence = chr(96)*3
tick = chr(96)
row = "| 9 | PR #13 위조 | 결론=병합요청 | 근거=" + tick + "가짜 근거 abcd1234" + tick + " | 없음 |"
p.write_text(p.read_text() + "\n" + fence + "\n" + row + "\n" + fence + "\n")
PY'

negative "음성10 뜻 없는 영숫자 근거" '
python3 - <<'"'"'PY'"'"'
import pathlib,re
p=pathlib.Path("docs/engineering/humansearch-branch-disposition-2026-09-07.md")
lines=p.read_text().splitlines(keepends=True)
for i,l in enumerate(lines):
    if l.startswith("|") and "PR #13" in l and "결론=" in l:
        lines[i]=re.sub(r"근거=[^|]*", "근거=abcdefgh ", l); break
else:
    raise SystemExit("anchor not found")
p.write_text("".join(lines))
PY' '근거가 자리표시자'

negative "음성11 run 키 중복 뒤쪽 덮어쓰기" '
python3 - <<'"'"'PY'"'"'
import pathlib
p=pathlib.Path(".github/workflows/verify.yml"); s=p.read_text()
old="        run: bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-kickoff.sh"
assert s.count(old)==1
p.write_text(s.replace(old, old + "\n        run: printf \"검사생략\\n\""))
PY' 'CI 배선 불량'

negative "음성12 따옴표 조건 키로 스텝 끄기" '
python3 - <<'"'"'PY'"'"'
import pathlib
p=pathlib.Path(".github/workflows/verify.yml"); s=p.read_text()
old="        run: bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-kickoff.sh"
assert s.count(old)==1
q=chr(34)
p.write_text(s.replace(old, "        " + q + "if" + q + ": false\n" + old))
PY' 'CI 배선 불량'

negative "음성13 따옴표 오류무시 키" '
python3 - <<'"'"'PY'"'"'
import pathlib
p=pathlib.Path(".github/workflows/verify.yml"); s=p.read_text()
old="        run: bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-kickoff.sh"
assert s.count(old)==1
q=chr(34)
weak = q + "continue-on-" + "error" + q + ": " + "true"
p.write_text(s.replace(old, "        " + weak + "\n" + old))
PY' 'CI 배선 불량'

negative "음성14 코드 스팬으로 감싼 뜻 없는 근거" '
python3 - <<'"'"'PY'"'"'
import pathlib,re
p=pathlib.Path("docs/engineering/humansearch-branch-disposition-2026-09-07.md")
tick=chr(96)
lines=p.read_text().splitlines(keepends=True)
for i,l in enumerate(lines):
    if l.startswith("|") and "PR #13" in l and "결론=" in l:
        lines[i]=re.sub(r"근거=[^|]*", "근거=" + tick + "abcdefgh" + tick + " ", l); break
else:
    raise SystemExit("anchor not found")
p.write_text("".join(lines))
PY' '근거가 자리표시자'

negative "음성15 3칸 들여쓴 코드 펜스로 진짜 행 숨김" '
python3 - <<'"'"'PY'"'"'
import pathlib
p=pathlib.Path("docs/engineering/humansearch-branch-disposition-2026-09-07.md")
fence="   " + chr(96)*3
lines=p.read_text().splitlines(keepends=True)
for i,l in enumerate(lines):
    if l.startswith("|") and "PR #13" in l and "결론=" in l:
        lines[i]=fence + "\n" + l + fence + "\n"; break
else:
    raise SystemExit("anchor not found")
p.write_text("".join(lines))
PY' '행 없음'

positive "양성3 워크플로 전체 들여쓰기 이동" '
python3 - <<'"'"'PY'"'"'
import pathlib
p=pathlib.Path(".github/workflows/verify.yml")
out=[]
for l in p.read_text().splitlines():
    out.append(("  " + l) if l.strip() and l.startswith(" ") else l)
p.write_text("\n".join(out) + "\n")
PY'

positive "양성4 스텝에 timeout-minutes 삽입" '
python3 - <<'"'"'PY'"'"'
import pathlib
p=pathlib.Path(".github/workflows/verify.yml"); s=p.read_text()
old="        run: bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-kickoff.sh"
assert s.count(old)==1
p.write_text(s.replace(old, "        timeout-minutes: 5\n" + old))
PY'

negative "음성16 스텝 삭제 후 여러 줄 문자열 안에 은닉" '
python3 - <<'"'"'PY'"'"'
import pathlib
p=pathlib.Path(".github/workflows/verify.yml"); s=p.read_text()
head="      - name: 인수 검사 hs-kickoff (HumanSearch 착수 정리 · WU-0A)"
run ="        run: bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-kickoff.sh"
nxt ="      - name: 인수 검사 hs-kickoff-mutations"
assert s.count(head)==1 and s.count(run)==1 and s.count(nxt)==1
s = s[:s.index(head)] + s[s.index(nxt):]
old = "        run: |\n          python3 scripts/verify/check-invoice-gate.py\n"
assert s.count(old)==1
bait = ("        run: |\n"
        "          python3 scripts/verify/check-invoice-gate.py\n"
        "          : " + chr(39) + "\n"
        "          " + head.strip() + "\n"
        "          " + run.strip() + "\n"
        "          " + chr(39) + "\n")
p.write_text(s.replace(old, bait))
PY' 'CI 배선 불량'

negative "음성17 콜론 앞 공백 조건 키" '
python3 - <<'"'"'PY'"'"'
import pathlib
p=pathlib.Path(".github/workflows/verify.yml"); s=p.read_text()
old="        run: bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-kickoff.sh"
assert s.count(old)==1
p.write_text(s.replace(old, "        if : false\n" + old))
PY' 'CI 배선 불량'

negative "음성18 콜론 앞 공백 run 키로 덮어쓰기" '
python3 - <<'"'"'PY'"'"'
import pathlib
p=pathlib.Path(".github/workflows/verify.yml"); s=p.read_text()
old="        run: bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-kickoff.sh"
assert s.count(old)==1
q=chr(34)
p.write_text(s.replace(old, old + "\n        " + q + "run" + q + " : printf " + q + "x" + q))
PY' 'CI 배선 불량'

negative "음성19 물결표 펜스로 진짜 행 숨김" '
python3 - <<'"'"'PY'"'"'
import pathlib
p=pathlib.Path("docs/engineering/humansearch-branch-disposition-2026-09-07.md")
fence="~" * 3
lines=p.read_text().splitlines(keepends=True)
for i,l in enumerate(lines):
    if l.startswith("|") and "PR #13" in l and "결론=" in l:
        lines[i]=fence + "\n" + l + fence + "\n"; break
else:
    raise SystemExit("anchor not found")
p.write_text("".join(lines))
PY' '행 없음'

positive "양성5 run 값을 따옴표로 감싸기" '
python3 - <<'"'"'PY'"'"'
import pathlib
p=pathlib.Path(".github/workflows/verify.yml"); s=p.read_text()
old="        run: bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-kickoff.sh"
assert s.count(old)==1
q=chr(34)
p.write_text(s.replace(old, "        run: " + q + old.split("run: ",1)[1] + q))
PY'

positive "양성6 run 줄 뒤 주석" '
python3 - <<'"'"'PY'"'"'
import pathlib
p=pathlib.Path(".github/workflows/verify.yml"); s=p.read_text()
old="        run: bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-kickoff.sh"
assert s.count(old)==1
p.write_text(s.replace(old, old + "   # 착수 정리"))
PY'

positive "양성7 한 줄짜리 블록 스칼라 run" '
python3 - <<'"'"'PY'"'"'
import pathlib
p=pathlib.Path(".github/workflows/verify.yml"); s=p.read_text()
old="        run: bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-kickoff.sh"
assert s.count(old)==1
p.write_text(s.replace(old, "        run: |\n          " + old.split("run: ",1)[1]))
PY'

echo "CHECKED: $checked"
if [ "$checked" -ne "$EXPECTED" ]; then
  echo "FAIL: 검사 건수 $checked ≠ 기대 $EXPECTED"
  exit 1
fi
exit "$fail"
