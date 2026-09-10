#!/usr/bin/env bash
# acceptance-hs-1309-paths.sh — 패킷·발송 장부가 git 으로 새는 경로가 막혀 있는가 (HS-13.09)
#
# 계약: docs/engineering/humansearch-hs13-position-brief-goal-2026-09-10.md §7 D7 · §9 HS-13.09
#   EARS : If 서치 패킷(*.packet.json)이나 발송 장부(*.sent.json)가 저장소에 들어오려 하면,
#          then .gitignore 와 공용 판정기·훅이 그 경로를 막아야 한다
#   출력 : 항목마다 PASS:/FAIL:/NOT_RUN: 을 전부 출력하고 마지막 줄에 `CHECKED: <검사 수>`
#   exit : 0 = PASS | 1 = FAIL | 2 = NOT_RUN
#   불변식: CHECKED 는 정확히 EXPECTED_CHECKED 여야 한다 — 검사가 사라져도 초록이면 가짜다(P20)
#
# 무엇을 판정하나 (3건):
#   1  .gitignore 가 두 패턴(*.packet.json·*.sent.json)을 담고 합성 경로에 **실제로 적용**된다
#   2  공용 판정기 scripts/scan-data-exposure.sh 가 그 경로를 금지로 **실행 판정**한다
#      (+ 정상 파일은 통과시키는 대조군, + 훅 목록에도 같은 두 패턴이 있는가)
#   3  brief 모듈에 `~/.humansearch`·`/Users/` 같은 절대·홈 경로 리터럴이 0건이다
#
# 쓰기 규칙: 저장소에 아무 파일도 만들지 않는다. 합성 파일은 mktemp 저장소에만 만든다.
# 왜 실행 판정인가(P16): 판정기 소스에 문자열이 있는지로 보면 "적혀는 있는데 안 걸리는"
#   경우를 놓친다. 2026-08-09 실측에서 dump.DB 가 그렇게 통과했다.
set -uo pipefail

unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_OBJECT_DIRECTORY \
      GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_COMMON_DIR GIT_PREFIX GIT_QUARANTINE_PATH

REPO=$(git rev-parse --show-toplevel 2>/dev/null) || { echo "NOT_RUN: git 저장소가 아니다"; echo "CHECKED: 0"; exit 2; }
cd "$REPO" || { echo "NOT_RUN: 저장소 루트로 이동 실패"; echo "CHECKED: 0"; exit 2; }

# grep 이 ugrep 으로 가려져 있을 수 있다 — 절대경로로 고정하고 자기검사한다(2026-08-25 실측).
G=/usr/bin/grep
[ -x "$G" ] || { echo "NOT_RUN: $G 가 없다"; echo "CHECKED: 0"; exit 2; }
printf 'canary\n' | $G -q canary || { echo "NOT_RUN: grep 자기검사 실패"; echo "CHECKED: 0"; exit 2; }

JUDGE=scripts/scan-data-exposure.sh
HOOK=hooks/pre-commit
BRIEF_DIR=humansearch/src/humansearch/brief
EXPECTED_CHECKED=3

for required in .gitignore "$JUDGE" "$HOOK"; do
  [ -f "$required" ] || { echo "NOT_RUN: 필수 파일 없음 — $required"; echo "CHECKED: 0"; exit 2; }
done

fail=0
checked=0
pass()   { checked=$((checked + 1)); printf 'PASS: %s\n' "$1"; }
failed() { checked=$((checked + 1)); printf 'FAIL: %s\n' "$1"; fail=1; }

# ── 1) .gitignore 가 두 패턴을 담고 실제로 적용되는가 ────────────────────────
# 목록에 적혀 있는지(문자열)와 실제로 걸리는지(git check-ignore)를 둘 다 본다.
# 표기만 보면 끝 슬래시·앵커 차이로 "적혀는 있는데 안 걸리는" 경우를 놓친다(AC-A4 §1 근거).
ignore_bad=""
for pattern in '*.packet.json' '*.sent.json'; do
  $G -qxF -- "$pattern" .gitignore || ignore_bad="${ignore_bad} ${pattern}(목록없음)"
done
for sample in \
  "20260910-86e1abcd-0a1b2c3d.packet.json" \
  "packets/20260910-86e1abcd-0a1b2c3d.packet.json" \
  "20260910-86e1abcd-0a1b2c3d.gmail.a1.sent.json" \
  "packets/20260910-86e1abcd-0a1b2c3d.gmail.a2.sent.json"
do
  git check-ignore -q "$sample" || ignore_bad="${ignore_bad} ${sample}(미적용)"
done
if [ -z "$ignore_bad" ]; then
  pass ".gitignore 가 *.packet.json·*.sent.json 을 담고 하위 경로까지 실제로 무시한다"
else
  failed ".gitignore 가 패킷·발송 장부를 덮지 않는다 — 누락:${ignore_bad}"
fi

# ── 2) 공용 판정기가 그 경로를 금지로 판정하는가 (실행 검증) ────────────────
# 가장 좁은 호출: tracked 모드. 임시 저장소에 합성 파일 1개를 스테이지하고 판정기를 태운다.
judge_blocks() {
  # judge_blocks <합성 경로>  → 0 = 금지로 잡았다 / 1 = 못 잡았다 / 2 = 실행 불가
  local target="$1" tmp rc=0 out=""
  tmp=$(mktemp -d) || return 2
  [ -n "$tmp" ] && [ -d "$tmp" ] || return 2
  cp "$JUDGE" "$tmp/judge.sh" || { rm -rf "$tmp"; return 2; }
  out=$(
    cd "$tmp" || exit 9
    git init -q .
    git config user.email a@b.c
    git config user.name t
    mkdir -p "$(dirname "$target")"
    printf '{}\n' > "$target"
    printf 'ok\n' > README.md
    git add "$target" README.md >/dev/null 2>&1
    bash judge.sh tracked 2>&1
  )
  rc=$?
  rm -rf "$tmp"
  [ "$rc" -eq 1 ] || return 1
  printf '%s\n' "$out" | $G -qF "$target" || return 1
  return 0
}

# 대조군 — 정상 파일까지 막으면 그것은 게이트가 아니라 벽이다.
judge_passes_control() {
  local tmp rc=0
  tmp=$(mktemp -d) || return 2
  [ -n "$tmp" ] && [ -d "$tmp" ] || return 2
  cp "$JUDGE" "$tmp/judge.sh" || { rm -rf "$tmp"; return 2; }
  (
    cd "$tmp" || exit 9
    git init -q .
    git config user.email a@b.c
    git config user.name t
    printf 'ok\n' > README.md
    printf 'x = 1\n' > note.py
    git add README.md note.py >/dev/null 2>&1
    bash judge.sh tracked
  ) >/dev/null 2>&1
  rc=$?
  rm -rf "$tmp"
  [ "$rc" -eq 0 ] || return 1
  return 0
}

judge_bad=""
for sample in \
  "x.packet.json" "packets/x.packet.json" \
  "x.gmail.a1.sent.json" "packets/x.gmail.a2.sent.json"
do
  judge_blocks "$sample" || judge_bad="${judge_bad} ${sample}(미차단)"
done
judge_passes_control || judge_bad="${judge_bad} 대조군(정상파일까지_차단)"
# 훅과 판정기의 목록이 갈라지면 한쪽만 막는 비대칭이 생긴다(scan-data-exposure.sh 주석 근거).
for pattern in '*.packet.json' '*.sent.json'; do
  $G -qF -- "$pattern" "$JUDGE" || judge_bad="${judge_bad} ${pattern}(판정기목록)"
  $G -qF -- "$pattern" "$HOOK"  || judge_bad="${judge_bad} ${pattern}(훅목록)"
done
if [ -z "$judge_bad" ]; then
  pass "판정기가 패킷·발송 장부 경로를 실행으로 차단하고 정상 파일은 통과시킨다(훅 목록 동치)"
else
  failed "판정기·훅이 패킷·발송 장부 경로를 막지 않는다 — 누락:${judge_bad}"
fi

# ── 3) brief 모듈에 홈·절대 경로 리터럴이 0건인가 ───────────────────────────
# 저장 위치는 호출자가 주입한다(§5 "시계·경로는 호출자가 준다"). 모듈이 경로를 박아 두면
# 시험이 실제 홈 디렉터리를 건드리고, 그 순간 후보자 PII 가 개발기에 남는다.
literal_bad=""
brief_files=0
if [ ! -d "$BRIEF_DIR" ]; then
  literal_bad=" ${BRIEF_DIR}(디렉터리없음)"
else
  for f in "$BRIEF_DIR"/*.py; do
    [ -f "$f" ] || continue
    brief_files=$((brief_files + 1))
    hits=$($G -cE '~/\.humansearch|/Users/' "$f")
    rc=$?
    if [ "$rc" -gt 1 ]; then
      literal_bad="${literal_bad} ${f}(검사실행실패)"
      continue
    fi
    [ "$hits" -eq 0 ] || literal_bad="${literal_bad} ${f}(${hits}건)"
  done
  [ "$brief_files" -ge 1 ] || literal_bad=" brief/*.py 0개(스캔무효·P20)"
fi
if [ -z "$literal_bad" ]; then
  pass "brief 모듈 ${brief_files}개에 홈·절대 경로 리터럴 0건"
else
  failed "brief 모듈에 홈·절대 경로 리터럴이 있다 — 위반:${literal_bad}"
fi

echo "CHECKED: $checked"
if [ "$checked" -ne "$EXPECTED_CHECKED" ]; then
  echo "FAIL: CHECKED $checked ≠ 기대 $EXPECTED_CHECKED — 검사가 사라지거나 늘었다"
  exit 1
fi
exit "$fail"
