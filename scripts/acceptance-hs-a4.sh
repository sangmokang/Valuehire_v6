#!/usr/bin/env bash
# acceptance-hs-a4.sh — 대용량 파일과 PII 산출물 경로가 커밋되지 못하는가 (AC-A4)
#
# 계약: docs/engineering/humansearch-v6-implementation-plan-2026-08-08.md §6 Phase A / AC-A4
#   EARS : If 1MB 를 넘는 파일 또는 DB·아티팩트 경로가 커밋되려 하면,
#          then pre-commit 과 CI 가 양쪽 다 차단해야 한다
#   출력 : exit 0 = PASS | exit 1 = FAIL | exit 2 = NOT_RUN
#   stdout: 항목마다 PASS:/FAIL:/NOT_RUN: 을 전부 출력하고, 마지막 줄에 `CHECKED: <검사 수>`
#   불변식: 0건 검사는 통과가 아니다 (P20)
#
# 왜 이 검사가 필요한가 (2026-08-08 실측):
#   ① hooks/pre-commit 에 파일 크기 검사가 0건이었다.
#   ② artifacts/ · *.db · *.sqlite* · data/ · private-reviews/ 가 .gitignore 대상이 아니었다.
#   구현 계획 §8 은 후보자 개인정보 보호를 이 두 장치 위에 세웠는데 **둘 다 없었다**.
#   Phase 0 에서 SQLite 가 생기는 순간 구멍이 열린 채로 시작하게 된다.
#
# 텍스트 단언이 아니라 실행으로 검사한다 (P16):
#   임시 저장소를 만들어 훅을 실제로 돌리고 종료코드를 본다. 소스에 문자열이 있는지로
#   판정하지 않는다 — 문자열은 있는데 동작하지 않는 경우를 잡지 못하기 때문이다.
set -uo pipefail

REPO=$(git rev-parse --show-toplevel 2>/dev/null) || { echo "NOT_RUN: git 저장소가 아니다"; echo "CHECKED: 0"; exit 2; }
cd "$REPO"

MAX_BYTES=1048576
fail=0
checked=0

ok()  { checked=$((checked + 1)); printf 'PASS: %s\n' "$1"; }
bad() { checked=$((checked + 1)); printf 'FAIL: %s\n' "$1"; fail=1; }

# ── 1) .gitignore 가 산출물 경로를 덮는가 ───────────────────────────────────
# git check-ignore 로 판정한다. .gitignore 본문을 grep 하면 표기 차이(끝 슬래시·와일드카드)
# 때문에 "적혀는 있는데 실제로는 안 걸리는" 경우를 놓친다.
for p in artifacts/x.png data/humansearch.sqlite3 humansearch.db run.sqlite private-reviews/x.md; do
  if git check-ignore -q "$p"; then
    ok "gitignore 적용 — $p"
  else
    bad "gitignore 미적용 — $p (개인정보·대용량 산출물이 추적 대상이다)"
  fi
done

# ── 2) 이미 추적 중인 파일에 위반이 없는가 (CI 가 매번 보는 것과 같은 검사) ──
big=0
while IFS= read -r -d '' f; do
  sz=$(git cat-file -s ":$f" 2>/dev/null) || continue
  if [ "$sz" -gt "$MAX_BYTES" ]; then
    printf '  큰 파일: %s (%s 바이트)\n' "$f" "$sz"
    big=$((big + 1))
  fi
done < <(git ls-files -z)
if [ "$big" -eq 0 ]; then
  ok "추적 파일 중 ${MAX_BYTES} 바이트 초과 0건"
else
  bad "추적 파일 중 ${MAX_BYTES} 바이트 초과 ${big}건"
fi

# ── 3) pre-commit 이 실제로 차단하는가 (임시 저장소에서 실행) ────────────────
run_hook_case() {
  # run_hook_case <설명> <파일경로> <내용생성함수>
  local desc="$1" path="$2" maker="$3"
  local tmp rc=0
  tmp=$(mktemp -d)
  git init -q "$tmp"
  mkdir -p "$tmp/hooks" "$tmp/scripts"
  cp hooks/pre-commit hooks/pre-push "$tmp/hooks/"
  cp verify.sh "$tmp/"
  cp .secret-patterns.default "$tmp/"
  cp .check-weakening-patterns "$tmp/"
  cp .gitignore "$tmp/"
  [ -f suppressions.yaml ] && cp suppressions.yaml "$tmp/"
  chmod +x "$tmp/hooks/pre-commit" "$tmp/hooks/pre-push"
  (
    cd "$tmp" || exit 9
    git config core.hooksPath hooks
    git config user.email a@b.c
    git config user.name t
    mkdir -p "$(dirname "$path")"
    "$maker" "$path"
    git add -f "$path" >/dev/null 2>&1
    bash hooks/pre-commit
  ) >/dev/null 2>&1
  rc=$?
  rm -rf "$tmp"
  if [ "$rc" -ne 0 ]; then
    ok "pre-commit 차단 확인 — $desc (exit=$rc)"
  else
    bad "pre-commit 통과함 — $desc (차단되어야 한다)"
  fi
}

make_big()   { dd if=/dev/zero of="$1" bs=1024 count=1200 status=none; }
make_small() { printf 'x\n' > "$1"; }

run_hook_case "1MB 초과 파일"        "big.bin"                    make_big
run_hook_case "SQLite 파일"          "data/humansearch.sqlite3"   make_small
run_hook_case "아티팩트 스크린샷"    "artifacts/nav.png"          make_small

# ── 4) 대조군: 정상 파일은 통과해야 한다 (차단이 전부 막는 것이면 게이트가 아니다) ──
tmp=$(mktemp -d)
git init -q "$tmp"
mkdir -p "$tmp/hooks"
cp hooks/pre-commit hooks/pre-push "$tmp/hooks/"
cp verify.sh .secret-patterns.default .check-weakening-patterns .gitignore "$tmp/"
[ -f suppressions.yaml ] && cp suppressions.yaml "$tmp/"
chmod +x "$tmp/hooks/pre-commit" "$tmp/hooks/pre-push"
rc=0
(
  cd "$tmp" || exit 9
  git config core.hooksPath hooks
  git config user.email a@b.c
  git config user.name t
  printf '# hello\n' > README.md
  git add README.md >/dev/null 2>&1
  bash hooks/pre-commit
) >/dev/null 2>&1
rc=$?
rm -rf "$tmp"
if [ "$rc" -eq 0 ]; then
  ok "정상 파일은 통과 (차단과 통과가 한 쌍)"
else
  bad "정상 파일까지 차단됨 (exit=$rc) — 게이트가 아니라 벽이다"
fi

# ── 5) 같은 검사가 CI 에도 있는가 (P15③ — 로컬에만 있는 검사는 없는 것으로 친다) ──
WF=.github/workflows/verify.yml
if [ ! -f "$WF" ]; then
  bad "$WF 없음 — CI 등가물을 확인할 수 없다"
else
  ACTIVE=$(grep -v '^[[:space:]]*#' "$WF")
  if printf '%s\n' "$ACTIVE" | grep -q 'cat-file -s'; then
    ok "CI 에 크기 검사 본문 존재 (cat-file -s)"
  else
    bad "CI 에 크기 검사 본문이 없다 — 로컬 훅은 우회 옵션으로 건너뛸 수 있다 (P15③)"
  fi
fi

if [ "$checked" -eq 0 ]; then
  echo "FAIL: 검사 항목 0개 — 0건 처리로 통과는 금지한다 (P20)"
  echo "CHECKED: 0"
  exit 1
fi

printf 'CHECKED: %d\n' "$checked"
exit "$fail"
