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

# ⚠️ git 훅은 GIT_DIR·GIT_INDEX_FILE 등을 자식 프로세스로 export 한다. 그 상태에서는
# 임시 저장소로 `cd` 해도 git 명령이 **실제 저장소**에 붙는다 — 2026-08-09 실측:
# `git push` 중 이 검사가 돌면서 실제 워크트리 인덱스에 테스트 파일 12개가 스테이지되고
# README.md 가 덮어써졌다(push 는 fail-closed 로 막혀 원격에는 안 갔다).
# 검증기가 검증 대상을 오염시키면 그 판정은 무효다. 여기서 상속을 끊는다.
unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_OBJECT_DIRECTORY \
      GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_COMMON_DIR GIT_PREFIX GIT_QUARANTINE_PATH

REPO=$(git rev-parse --show-toplevel 2>/dev/null) || { echo "NOT_RUN: git 저장소가 아니다"; echo "CHECKED: 0"; exit 2; }
cd "$REPO"

# 자기 오염 감지 — 이 검사가 끝난 뒤 저장소 상태가 시작과 달라지면 판정 자체가 무효다.
SNAP0=$(git status --porcelain)

MAX_BYTES=1048576
fail=0
checked=0
TMPDIRS=""
# 중단 시 임시 디렉터리를 남기지 않는다.
trap 'for d in $TMPDIRS; do [ -n "$d" ] && [ -d "$d" ] && rm -rf "$d"; done' EXIT

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
#
# ⚠️ 대상 수(seen)를 반드시 센다(2026-08-12 V1 적대검증 D7). 이전 판은 큰 파일 수(big)만
# 세고 대상 수를 안 봐서, **추적 파일이 0개인 빈 저장소에서도 "초과 0건"으로 성공**했다.
# 0건 처리를 통과로 세는 것이 P20 이 금지하는 공허 통과다. 검사 대상이 없으면 그것은
# "깨끗함"이 아니라 "검사기가 대상을 못 찾음"이며 fail-closed 로 처리한다.
# (CI 쪽 verify.yml 은 이미 `n -eq 0` 에서 exit 2 로 같은 방어를 한다 — 로컬만 비어 있었다.)
big=0
seen=0
while IFS= read -r -d '' f; do
  seen=$((seen + 1))
  sz=$(git cat-file -s ":$f" 2>/dev/null) || continue
  if [ "$sz" -gt "$MAX_BYTES" ]; then
    printf '  큰 파일: %s (%s 바이트)\n' "$f" "$sz"
    big=$((big + 1))
  fi
done < <(git ls-files -z)
if [ "$seen" -eq 0 ]; then
  bad "추적 파일 0개 — 스캔 무효 (P20 · 검사 대상을 못 찾은 것이지 깨끗한 것이 아니다)"
elif [ "$big" -eq 0 ]; then
  ok "추적 파일 ${seen}개 중 ${MAX_BYTES} 바이트 초과 0건"
else
  bad "추적 파일 ${seen}개 중 ${MAX_BYTES} 바이트 초과 ${big}건"
fi

# ── 3) pre-commit 이 실제로 차단하는가 (임시 저장소에서 실행) ────────────────
run_hook_case() {
  # run_hook_case <설명> <파일경로> <내용생성함수> <기대 차단사유 정규식>
  #
  # ⚠️ 종료코드만 보면 안 된다. 훅이 **다른 이유로** exit 1 을 내도 "차단 확인"으로
  # 읽히기 때문이다(거짓 초록). 그래서 stderr 의 BLOCKED 사유까지 대조한다.
  local desc="$1" path="$2" maker="$3" want="$4"
  local tmp rc=0 out=""
  # mktemp 실패를 통과로 처리하면 검증기가 오염원이 된다: tmp="" 일 때 `cd ""` 는
  # rc=0 이라 현재 디렉터리(= 실제 저장소)에 머물고, git config·git add 가 거기서 돈다
  # (2026-08-09 실측: user.name·hooksPath 가 덮어써지고 1.2MB 파일이 스테이지됐다).
  tmp=$(mktemp -d) || { bad "임시 저장소 생성 실패 — $desc (fail-closed)"; return; }
  if [ -z "$tmp" ] || [ ! -d "$tmp" ]; then
    bad "임시 저장소 경로가 비었거나 디렉터리가 아니다 — $desc (fail-closed)"
    return
  fi
  git init -q "$tmp"
  mkdir -p "$tmp/hooks" "$tmp/scripts"
  cp hooks/pre-commit hooks/pre-push "$tmp/hooks/"
  cp verify.sh "$tmp/"
  cp .secret-patterns.default "$tmp/"
  cp .check-weakening-patterns "$tmp/"
  cp .gitignore "$tmp/"
  [ -f suppressions.yaml ] && cp suppressions.yaml "$tmp/"
  chmod +x "$tmp/hooks/pre-commit" "$tmp/hooks/pre-push"
  # 한 번만 실행하고 종료코드와 출력(BLOCKED 사유)을 함께 받는다.
  out=$(
    cd "$tmp" || exit 9
    git config core.hooksPath hooks
    git config user.email a@b.c
    git config user.name t
    mkdir -p "$(dirname "$path")"
    "$maker" "$path"
    git add -f "$path" >/dev/null 2>&1
    bash hooks/pre-commit 2>&1
  )
  rc=$?
  rm -rf "$tmp"
  if [ "$rc" -eq 0 ]; then
    bad "pre-commit 통과함 — $desc (차단되어야 한다)"
  elif printf '%s\n' "$out" | grep -qE "$want"; then
    ok "pre-commit 차단 확인 — $desc (exit=$rc · 사유 일치)"
  else
    bad "pre-commit 이 막긴 했으나 사유가 다르다 — $desc (기대: $want / 실제: ${out%%$'\n'*})"
  fi
}

make_big()   { dd if=/dev/zero of="$1" bs=1024 count=1200 status=none; }
make_small() { printf 'x\n' > "$1"; }

SZ='1MB 초과 파일'
PATHRULE='산출물·데이터 경로'
run_hook_case "1MB 초과 파일"          "big.bin"                    make_big   "$SZ"
run_hook_case "SQLite 파일"            "data/humansearch.sqlite3"   make_small "$PATHRULE"
run_hook_case "아티팩트 스크린샷"      "artifacts/nav.png"          make_small "$PATHRULE"
# 하위 디렉터리 우회 (2026-08-09 보안 재검증에서 뚫린 경로)
run_hook_case "하위 경로 아티팩트"     "src/artifacts/nav.png"      make_small "$PATHRULE"
run_hook_case "하위 경로 데이터"       "tools/data/cand.json"       make_small "$PATHRULE"
# SQLite 사이드카 — WAL 은 아직 본체에 반영 안 된 행 전체를 담는다
run_hook_case "SQLite WAL 사이드카"    "humansearch.db-wal"         make_small "$PATHRULE"
# 후보자 덤프의 실제 형식
run_hook_case "JSONL 덤프"             "candidates.jsonl"           make_small "$PATHRULE"
# 대문자 확장자 — case 비교는 대소문자를 구분한다(2026-08-09 실측: dump.DB 통과)
run_hook_case "대문자 확장자"          "dump.DB"                    make_small "$PATHRULE"
# 디렉터리 규칙만으로 걸려야 하는 것들. 확장자 규칙과 겹치지 않아 규칙을 분리 검증한다
# (data/humansearch.sqlite3 는 확장자에도 걸려 디렉터리 규칙의 작동을 증명하지 못한다)
run_hook_case "디렉터리 규칙(확장자 무해)" "data/notes.txt"          make_small "$PATHRULE"
run_hook_case "비공개 리뷰 경로"       "private-reviews/r.md"       make_small "$PATHRULE"

# ── 3-b) 크기를 인덱스 blob 에서 재는가 (계약서 명시 사항) ────────────────────
# add 후 작업트리만 작은 내용으로 덮어써도 인덱스에는 큰 blob 이 남는다.
# 작업트리를 재는 구현(wc -c 등)으로 바꾸면 이 케이스만 빨개진다.
tmp=$(mktemp -d) || bad "임시 저장소 생성 실패 (인덱스 측정 검사)"
if [ -n "$tmp" ] && [ -d "$tmp" ]; then
  TMPDIRS="$TMPDIRS $tmp"
  git init -q "$tmp"; mkdir -p "$tmp/hooks"
  cp hooks/pre-commit hooks/pre-push "$tmp/hooks/"
  cp verify.sh .secret-patterns.default .check-weakening-patterns .gitignore "$tmp/"
  [ -f suppressions.yaml ] && cp suppressions.yaml "$tmp/"
  chmod +x "$tmp/hooks/pre-commit" "$tmp/hooks/pre-push"
  out=$(
    cd "$tmp" || exit 9
    git config core.hooksPath hooks; git config user.email a@b.c; git config user.name t
    dd if=/dev/zero of=payload.bin bs=1024 count=1200 status=none
    git add -f payload.bin >/dev/null 2>&1
    printf 'x\n' > payload.bin          # 작업트리만 작게 덮어쓴다
    bash hooks/pre-commit 2>&1
  )
  rc=$?
  rm -rf "$tmp"
  if [ "$rc" -ne 0 ] && printf '%s\n' "$out" | grep -q '1MB 초과 파일'; then
    ok "인덱스 blob 기준 측정 확인 (작업트리 덮어쓰기로 우회 불가)"
  else
    bad "작업트리 덮어쓰기로 크기 검사를 우회했다 (rc=$rc) — 인덱스가 아니라 작업트리를 재고 있다"
  fi
fi

# ── 3-c) rename 이 검사 대상에 포함되는가 ────────────────────────────────────
tmp=$(mktemp -d) || bad "임시 저장소 생성 실패 (rename 검사)"
if [ -n "$tmp" ] && [ -d "$tmp" ]; then
  git init -q "$tmp"; mkdir -p "$tmp/hooks"
  cp hooks/pre-commit hooks/pre-push "$tmp/hooks/"
  cp verify.sh .secret-patterns.default .check-weakening-patterns .gitignore "$tmp/"
  [ -f suppressions.yaml ] && cp suppressions.yaml "$tmp/"
  chmod +x "$tmp/hooks/pre-commit" "$tmp/hooks/pre-push"
  out=$(
    cd "$tmp" || exit 9
    git config user.email a@b.c; git config user.name t
    # 씨앗 커밋은 훅을 붙이기 **전에** 만든다. 훅 우회 옵션을 쓰면 그 리터럴 자체가
    # 검사 약화 패턴이라 이 스크립트가 커밋되지 않는다(2026-08-09 실측 — 훅이 나를 막았다).
    printf 'notes\n' > notes.txt
    git add notes.txt >/dev/null 2>&1
    git commit -q -m seed >/dev/null 2>&1
    git config core.hooksPath hooks
    git mv notes.txt leak.db >/dev/null 2>&1
    bash hooks/pre-commit 2>&1
  )
  rc=$?
  rm -rf "$tmp"
  if [ "$rc" -ne 0 ] && printf '%s\n' "$out" | grep -q '산출물·데이터 경로'; then
    ok "rename 도 검사 대상 (git mv 로 우회 불가)"
  else
    bad "git mv 로 검사를 우회했다 (rc=$rc) — diff-filter 에 R 이 빠졌다"
  fi
fi

# ── 3-d) 정상 소스가 '조용히' 사라지지 않는가 (P3) ───────────────────────────
# gitignore 디렉터리 규칙에 앵커가 없으면 src/data/schema.json 같은 정상 소스가
# 아무 메시지 없이 무시된다. 하위 경로 산출물은 훅이 '소리 내어' 막는 쪽이 옳다.
if git check-ignore -q src/data/schema.json; then
  bad "src/data/schema.json 이 조용히 무시된다 — gitignore 디렉터리 규칙에 앵커가 없다 (P3)"
else
  ok "하위 경로 정상 소스는 조용히 사라지지 않는다 (앵커 확인)"
fi

# ── 4) 대조군: 정상 파일은 통과해야 한다 (차단이 전부 막는 것이면 게이트가 아니다) ──
tmp=$(mktemp -d)
git init -q "$tmp"
mkdir -p "$tmp/hooks"
cp hooks/pre-commit hooks/pre-push "$tmp/hooks/"
cp verify.sh .secret-patterns.default .check-weakening-patterns .gitignore "$tmp/"
[ -f suppressions.yaml ] && cp suppressions.yaml "$tmp/"
# pre-commit 이 부르는 별도 검사기도 함께 옮긴다. 훅은 검사기가 없으면 fail-closed 로
# 차단하므로(P20), 픽스처가 의존물을 빠뜨리면 이 대조군이 "정상 파일까지 차단됨"으로
# 빨개진다 — 훅에 의존을 추가할 때 이 목록도 같이 늘려야 한다.
mkdir -p "$tmp/scripts/verify"
for dep in scripts/verify/check-workflow-deletion.sh; do
  [ -f "$dep" ] && cp "$dep" "$tmp/$dep"
done
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
  # 판정기가 두 벌이 되면 갈린다(이 저장소가 이미 겪은 사고 — hooks/pre-commit §1 주석).
  # CI 본문은 이제 공용 판정기(scripts/scan-data-exposure.sh)로 옮겼으므로 CI↔판정기
  # 대조는 필요 없다 — 같은 파일이다. 남은 갈림길은 **훅 ↔ 판정기** 한 곳뿐이다.
  # 훅은 '스테이지된 것'만 보므로 별도 코드로 남아 있고, 그래서 목록이 갈라질 수 있다.
  miss=""
  for pat in '\*/artifacts/\*' '\*/data/\*' '\*\.db-\*' '\*\.jsonl' '\*/private-reviews/\*' '\*\.parquet'; do
    if ! grep -q -- "$pat" scripts/scan-data-exposure.sh; then miss="${miss} ${pat}(판정기)"; fi
    if ! grep -q -- "$pat" hooks/pre-commit;              then miss="${miss} ${pat}(훅)"; fi
  done
  if [ -z "$miss" ]; then
    ok "훅과 공용 판정기의 금지 경로 패턴이 동치 (하위경로·사이드카·덤프·비공개리뷰 포함)"
  else
    bad "훅과 판정기의 경로 패턴이 갈렸다 — 누락:${miss} (판정기 2벌 · P15③)"
  fi
fi

# ── 6) 공용 데이터 노출 판정기 — 문자열이 아니라 **실행**으로 검증한다 ──────────
#
# 왜 공용 스크립트인가(2026-08-12 V1 적대검증 D4): 이전 판은 CI 워크플로 본문에 특정
# 문자열이 있는지만 봤다. 그래서 크기검사 스텝에 `if: ${{ false }}` 를 넣어 영구히 꺼도
# 인수검사·pre-commit·pre-push 가 전부 초록이었다(V2 재현). 규칙을 두 벌로 적으면 항상
# 이렇게 갈라진다 — 판정을 스크립트 하나로 모으고, CI 도 인수검사도 **같은 것을 실행**한다.
JUDGE=scripts/scan-data-exposure.sh

if [ ! -f "$JUDGE" ] || [ ! -x "$JUDGE" ]; then
  bad "공용 판정기 없음/실행불가 — $JUDGE (D1·D2 방어가 존재하지 않는다)"
else
  # 임시 저장소에서 실제 시나리오를 만들고 판정기를 그대로 태운다.
  judge_case() {
    # judge_case <설명> <모드> <시나리오함수> <기대 exit>
    local desc="$1" mode="$2" scenario="$3" want="$4" tmp rc=0
    tmp=$(mktemp -d) || { bad "임시 저장소 생성 실패 — $desc (fail-closed)"; return; }
    [ -d "$tmp" ] || { bad "임시 저장소 경로 없음 — $desc (fail-closed)"; return; }
    cp "$JUDGE" "$tmp/judge.sh"
    ( cd "$tmp" || exit 9
      git init -q .
      git config user.email a@b.c; git config user.name t
      "$scenario"
      bash judge.sh "$mode"
    ) >/dev/null 2>&1
    rc=$?
    rm -rf "$tmp"
    if [ "$rc" -eq "$want" ]; then
      ok "판정기 실행 — $desc (exit=$rc)"
    else
      bad "판정기 실행 — $desc (기대 exit=$want, 실제 $rc)"
    fi
  }

  # D1: 큰 파일을 커밋한 뒤 다음 커밋에서 지운다. 현재 파일 목록에는 없지만 기록에는 남는다.
  sc_history_big() {
    local oid; oid=$(dd if=/dev/zero bs=1024 count=1200 2>/dev/null | git hash-object -w --stdin)
    git update-index --add --cacheinfo 100644,"$oid",exports/candidates.csv
    git commit -q -m one
    git update-index --force-remove exports/candidates.csv
    printf 'ok\n' > README.md; git add README.md; git commit -q -m two
  }
  sc_history_clean() { printf 'ok\n' > README.md; git add README.md; git commit -q -m one; }

  # D2: 후보자 개인정보 컬럼 조합. 1MB 미만이고 확장자가 허용 목록이라 크기·경로로는 안 잡힌다.
  sc_pii_csv() {
    printf 'name,email,phone,school,profile_url\n홍길동,a@b.c,010-1234-5678,서울대,https://x/1\n' > cand.csv
    git add cand.csv; git commit -q -m pii
  }
  sc_pii_sql() {
    printf "INSERT INTO candidates(name,email,phone,school) VALUES('홍','a@b.c','010-1','서울대');\n" > seed.sql
    git add seed.sql; git commit -q -m pii
  }
  # 대조군 — 정상 CSV·마이그레이션 SQL 은 막히면 안 된다. 전부 막는 건 게이트가 아니라 벽이다.
  sc_ok_csv() {
    printf 'position,count,stage\nAX Sales,20,screening\n' > metrics.csv
    git add metrics.csv; git commit -q -m ok
  }
  sc_ok_sql() {
    printf 'CREATE TABLE positions(id INTEGER PRIMARY KEY, title TEXT NOT NULL);\n' > 001_init.sql
    git add 001_init.sql; git commit -q -m ok
  }

  judge_case "기록에만 남은 1MB 초과 파일을 잡는다 (D1)"      history "sc_history_big"   1
  judge_case "깨끗한 기록은 통과시킨다 (차단과 통과가 한 쌍)" history "sc_history_clean" 0
  judge_case "후보자 컬럼 CSV 를 잡는다 (D2)"                 pii     "sc_pii_csv"       1
  judge_case "후보자 컬럼 SQL 을 잡는다 (D2)"                 pii     "sc_pii_sql"       1
  judge_case "정상 지표 CSV 는 통과시킨다 (오탐 대조군)"      pii     "sc_ok_csv"        0
  judge_case "정상 마이그레이션 SQL 은 통과시킨다 (오탐 대조군)" pii  "sc_ok_sql"        0

  # 검토 기준선(.data-exposure-reviewed). 규칙을 약화시키지 않으면서 사람이 확인한
  # 파일만 통과시킨다. 차단과 통과를 한 쌍으로 잰다.
  sc_reviewed_ok() {
    printf "INSERT INTO candidates(name,email) VALUES('홍','a@b.c');\n" > seed.sql
    git add seed.sql
    printf '%s\t%s\t%s\n' "$(git cat-file blob :seed.sql | shasum -a 256 | cut -d" " -f1)" \
      "seed.sql" "확인함 — 자리표시자" > .data-exposure-reviewed
    git add .data-exposure-reviewed; git commit -q -m reviewed
  }
  sc_reviewed_stale() {
    printf "INSERT INTO candidates(name,email) VALUES('홍','a@b.c');\n" > seed.sql
    git add seed.sql
    printf '%s\t%s\t%s\n' "$(printf 0%.0s $(seq 64))" "seed.sql" "낡은 해시" \
      > .data-exposure-reviewed
    git add .data-exposure-reviewed; git commit -q -m stale
  }
  sc_reviewed_dead() {
    printf 'ok\n' > README.md; git add README.md
    printf '%s\t%s\t%s\n' "$(printf 0%.0s $(seq 64))" "gone.sql" "지워진 경로" \
      > .data-exposure-reviewed
    git add .data-exposure-reviewed; git commit -q -m dead
  }

  judge_case "검토 기준선에 적힌 파일은 통과시킨다"              pii "sc_reviewed_ok"     0
  judge_case "해시가 어긋난 기준선은 통과시키지 않는다"          pii "sc_reviewed_stale"  1
  judge_case "죽은 기준선 항목은 그 자체가 불합격이다"           pii "sc_reviewed_dead"   1
fi

# D4: CI 가 그 판정기를 **실행 줄**에서 부르는가 + 그 스텝이 조건으로 꺼져 있지 않은가.
# 문자열 대조가 남지만, 판정 본문은 위에서 실제 실행으로 검증했으므로 여기서는
# "배선이 살아 있는가"만 본다 — 두 벌 판정기 문제가 사라진다.
WF=.github/workflows/verify.yml
if [ ! -f "$WF" ]; then
  bad "CI 워크플로 없음 — $WF"
else
  if grep -qE "^[[:space:]]*run:[[:space:]]*(bash[[:space:]]+)?\.?/?${JUDGE//\//\\/}" "$WF"; then
    ok "CI 가 공용 판정기를 실행 줄에서 호출한다"
  else
    bad "CI 가 공용 판정기를 호출하지 않는다 — 로컬 전용 검사가 된다 (P15③)"
  fi
  # 판정기를 부르는 스텝 블록 안에 if: 가 있으면 영구 비활성화가 가능하다.
  if awk -v j="$JUDGE" '
      /^[[:space:]]*- name:/ { inblk=1; hasif=0; hasjudge=0 }
      inblk && /^[[:space:]]*if:/ { hasif=1 }
      inblk && index($0, j) { hasjudge=1 }
      inblk && hasjudge && hasif { print "DISABLED"; exit }
    ' "$WF" | grep -q DISABLED; then
    bad "판정기 스텝에 if: 조건이 붙어 있다 — 영구 비활성화가 가능하다 (P13)"
  else
    ok "판정기 스텝에 비활성화 조건 없음"
  fi
fi

if [ "$checked" -eq 0 ]; then
  echo "FAIL: 검사 항목 0개 — 0건 처리로 통과는 금지한다 (P20)"
  echo "CHECKED: 0"
  exit 1
fi

# ⚠️ 이름을 증명 범위에 맞춘다(2026-08-12 V1 적대검증 D3 · V2 재현 확인).
# `git status --porcelain` 은 **추적/미추적 파일 상태만** 본다. git 설정(`git config`),
# 참조(refs), 내부 객체(.git/objects), 과거 기록, 무시된 파일은 보지 못하고, 중간에
# 오염시켰다가 되돌린 사실도 원리상 볼 수 없다. V2 재현: 검사 도중 `git config` 를 바꾸고
# 객체 1개를 저장해도(객체 파일 45→46) 이 비교는 "동일"로 나왔다.
# 따라서 "저장소 무오염"이라 부르면 과장이다 — 실제로 증명한 범위만 이름에 담는다.
SNAP1=$(git status --porcelain)
if [ "$SNAP0" != "$SNAP1" ]; then
  checked=$((checked + 1))
  echo "FAIL: 이 검사가 작업트리를 오염시켰다 — 시작/종료 파일 상태가 다르다 (판정 무효)"
  printf '%s\n' "$SNAP1" | sed 's/^/       /'
  fail=1
else
  checked=$((checked + 1))
  echo "PASS: 작업트리 무오염 (git status 기준 — git 설정·내부 객체·참조는 범위 밖)"
fi

printf 'CHECKED: %d\n' "$checked"
exit "$fail"
