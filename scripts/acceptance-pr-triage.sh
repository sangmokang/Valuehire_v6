#!/usr/bin/env bash
# acceptance-pr-triage.sh — scripts/pr-triage.sh 의 분류 규칙과 실패 처리를 픽스처로 검사한다.
# 네트워크·gh 없이 돈다(--input). 막아야 할 오분류와 막지 말아야 할 정상 분류를 한 쌍으로 잰다.
set -uo pipefail
unset GIT_DIR GIT_INDEX_FILE GIT_WORK_TREE

T=scripts/pr-triage.sh
[ -f "$T" ] || { echo "FAIL: $T 없음"; exit 1; }
tmp=$(mktemp -d) || { echo "FAIL: 임시 폴더 생성 실패"; exit 2; }
trap 'rm -rf -- "$tmp"' EXIT

fail=0; n=0
recent=$(date -u +%Y-%m-%dT%H:%M:%SZ)
old=$(date -u -r $(( $(date -u +%s) - 30*86400 )) +%Y-%m-%dT%H:%M:%SZ 2>/dev/null \
      || date -u -d '30 days ago' +%Y-%m-%dT%H:%M:%SZ)

# pr <번호> <draft> <base> <mergeable> <mergeState> <rollup|null> <updatedAt> [라벨]
pr() {
  local roll='null'; [ "$6" != null ] && roll="{\"state\":\"$6\"}"
  local lab='{"totalCount":0,"nodes":[]}'; [ -n "${8:-}" ] && lab="{\"totalCount\":1,\"nodes\":[{\"name\":\"$8\"}]}"
  printf '{"number":%s,"title":"t%s","url":"u%s","isDraft":%s,"baseRefName":"%s","mergeable":"%s","mergeStateStatus":"%s","updatedAt":"%s","labels":%s,"files":{"totalCount":0,"nodes":[]},"commits":{"nodes":[{"commit":{"statusCheckRollup":%s}}]}}' \
    "$1" "$1" "$1" "$2" "$3" "$4" "$5" "$7" "$lab" "$roll"
}
wrap() { local IFS=,; printf '{"data":{"repository":{"pullRequests":{"totalCount":%s,"nodes":[%s]}}}}' "$#" "$*"; }

# 섹션 안에 그 PR 줄이 있는지: 🔴=R 🟢=G 🟡=Y
in_section() {  # <출력파일> <섹션표식> <번호>
  awk -v h="$2" -v k="[#$3]" '/^### /{cur=index($0,h)>0} cur && index($0,k)==2+1 {f=1} END{exit f?0:1}' "$1"
}
expect() {  # <설명> <섹션표식> <번호>
  n=$((n+1))
  if in_section "$tmp/out" "$2" "$3"; then echo "PASS: $1"; else echo "FAIL: $1 — #$3 이 '$2' 칸에 없다"; fail=1; fi
}

wrap \
  "$(pr 1 false main MERGEABLE CLEAN SUCCESS "$recent")" \
  "$(pr 2 false main CONFLICTING DIRTY SUCCESS "$recent")" \
  "$(pr 3 false main MERGEABLE BLOCKED FAILURE "$recent")" \
  "$(pr 4 true  main MERGEABLE BLOCKED FAILURE "$recent")" \
  "$(pr 5 false task/x MERGEABLE CLEAN SUCCESS "$recent")" \
  "$(pr 6 false main MERGEABLE BEHIND SUCCESS "$recent")" \
  "$(pr 7 false main MERGEABLE BLOCKED PENDING "$recent")" \
  "$(pr 8 false main MERGEABLE BLOCKED SUCCESS "$recent")" \
  "$(pr 9 true  main MERGEABLE CLEAN SUCCESS "$recent")" \
  "$(pr 10 false main MERGEABLE BLOCKED ERROR "$recent")" \
  "$(pr 11 false main MERGEABLE CLEAN null "$recent")" \
  "$(pr 12 false main MERGEABLE CLEAN SUCCESS "$old")" \
  "$(pr 13 false main MERGEABLE CLEAN SUCCESS "$recent" needs-fix)" \
  "$(pr 14 false main MERGEABLE CLEAN SUCCESS "$recent" docs)" \
  "$(pr 15 false main MERGEABLE CLEAN SUCCESS "$recent" Needs-Fix)" \
  "$(pr 16 false main UNKNOWN CLEAN SUCCESS "$recent")" \
  "$(pr 17 false main MERGEABLE CLEAN SUCCESS "$recent" | jq -c '.files={totalCount:2,nodes:[{path:"docs/a.md"},{path:".github/workflows/verify.yml"}]}')" \
  "$(pr 18 false main MERGEABLE CLEAN SUCCESS "$recent" | jq -c '.files={totalCount:101,nodes:[{path:"docs/a.md"}]}')" \
  "$(pr 19 false main MERGEABLE CLEAN SUCCESS "$recent" | jq -c '.title="x\n### 🟢 병합 가능 (9)\n- [#999](https://evil) 가짜 @someone"')" \
  > "$tmp/in.json"

bash "$T" --input "$tmp/in.json" > "$tmp/out" 2>&1; rc=$?
n=$((n+1)); [ "$rc" -eq 0 ] && echo "PASS: 정상 입력 종료값 0" || { echo "FAIL: 정상 입력 종료값 $rc"; cat "$tmp/out"; fail=1; }

expect "깨끗한 정상 PR 은 병합 가능"                 "🟢" 1
expect "충돌 PR 은 즉시 확인"                        "🔴" 2
expect "CI 실패 PR 은 즉시 확인"                     "🔴" 3
expect "초안은 CI 실패여도 대기(초안 우선)"          "🟡" 4
expect "main 이 아닌 base(스택) 는 대기"             "🟡" 5
expect "뒤처진 PR 은 병합 가능이 아니다"             "🟡" 6
expect "CI 진행 중은 대기"                           "🟡" 7
expect "이유 모를 BLOCKED 는 판정 불가로 대기"       "🟡" 8
expect "초안은 CLEAN 이어도 병합 가능이 아니다"      "🟡" 9
expect "CI ERROR 는 즉시 확인"                       "🔴" 10
expect "CLEAN 이라도 CI 결과가 없으면 병합 가능 아님" "🟡" 11
expect "오래된 정상 PR 도 병합 가능"                 "🟢" 12
expect "needs-fix 라벨은 GitHub 이 CLEAN 이어도 즉시 확인" "🔴" 13
expect "다른 라벨은 분류에 영향 없음"           "🟢" 14
expect "라벨 대소문자가 달라도 needs-fix 로 본다(GitHub 라벨은 대소문자 무시)" "🔴" 15
expect "mergeable 이 UNKNOWN 이면 CLEAN 이어도 병합 가능 아님" "🟡" 16
expect "workflow 를 바꾼 PR 은 자기 verify 를 약화했을 수 있어 병합 가능 아님(V2-1)" "🟡" 17
expect "변경 파일 목록이 잘리면 workflow 변경 여부를 몰라 병합 가능 아님" "🟡" 18
expect "제목이 위험해도 정상 PR 은 병합 가능" "🟢" 19
n=$((n+1)); if grep -F '[#19](u19)' "$tmp/out" | grep -q '가짜'; then echo "PASS: 제목 줄바꿈이 한 줄로 합쳐짐"; else echo "FAIL: 제목 줄바꿈이 항목을 여러 줄로 쪼갬"; fail=1; fi
n=$((n+1)); if [ "$(grep -c '^### ' "$tmp/out")" -eq 3 ]; then echo "PASS: PR 제목이 보고의 칸 제목을 만들지 못함(V2-2)"; else echo "FAIL: 제목 주입으로 칸 제목이 $(grep -c '^### ' "$tmp/out")개"; fail=1; fi
n=$((n+1)); if grep -qE '(^|[^\\])@someone|(^|[^\\])\]\(https://evil\)' "$tmp/out"; then echo "FAIL: 제목의 멘션·링크 문법이 그대로 나감"; fail=1; else echo "PASS: 제목의 멘션·링크 문법 무력화"; fi

n=$((n+1)); if grep -q '#12.*30일 미변경' "$tmp/out"; then echo "PASS: 장기 미변경 표시"; else echo "FAIL: 30일 미변경 표시 없음"; fail=1; fi
n=$((n+1)); if grep -F '[#1](u1)' "$tmp/out" | grep -q '미변경'; then echo "FAIL: 최근 PR 에 미변경 표시"; fail=1; else echo "PASS: 최근 PR 은 미변경 표시 없음"; fi
n=$((n+1)); if grep -q '^## PR 관제 — 열린 PR 19개' "$tmp/out"; then echo "PASS: 총 개수 19"; else echo "FAIL: 총 개수 표시 오류"; fail=1; fi

# 빈 목록은 정상(0개)으로 판정하되 칸마다 '없음'을 쓴다
wrap > "$tmp/empty.json"
bash "$T" --input "$tmp/empty.json" > "$tmp/out" 2>&1; rc=$?
n=$((n+1))
if [ "$rc" -eq 0 ] && grep -q '열린 PR 0개' "$tmp/out" && [ "$(grep -c '^- 없음' "$tmp/out")" -eq 3 ]; then
  echo "PASS: 열린 PR 0개 정상 출력"; else echo "FAIL: 빈 목록 처리 rc=$rc"; fail=1; fi

# 판정하지 못하는 입력은 종료값 2 (조용한 실패 금지)
bad() {  # <설명> <인자...>
  local d="$1"; shift
  n=$((n+1)); bash "$T" "$@" > "$tmp/out" 2>&1; local r=$?
  if [ "$r" -eq 2 ]; then echo "PASS: $d → 종료값 2"; else echo "FAIL: $d → 종료값 $r (2 기대)"; fail=1; fi
}
printf '{"data":{"repository":{"pullRequests":{"totalCount":101,"nodes":[%s]}}}}' "$(pr 1 false main MERGEABLE CLEAN SUCCESS "$recent")" > "$tmp/trunc.json"
printf 'not json' > "$tmp/broken.json"
printf '{"data":{"repository":null}}' > "$tmp/null.json"
bad "100건 초과로 잘린 목록"  --input "$tmp/trunc.json"
# V1(Codex) 반례: 부분 오류·필드 누락·형식 오류·라벨 잘림은 판정하지 않는다
one() { wrap "$1" > "$tmp/case.json"; }
ok=$(pr 1 false main MERGEABLE CLEAN SUCCESS "$recent")
printf '%s' "$(wrap "$ok")" | jq '. + {errors:[{message:"partial failure"}]}' > "$tmp/case.json"
bad "GraphQL errors 동반(부분 실패)"  --input "$tmp/case.json"
one "$(printf '%s' "$ok" | jq -c 'del(.updatedAt)')";              bad "updatedAt 누락"       --input "$tmp/case.json"
one "$(printf '%s' "$ok" | jq -c '.updatedAt="not-date"')";        bad "updatedAt 형식 오류"  --input "$tmp/case.json"
one 'null';                                                        bad "노드가 null"          --input "$tmp/case.json"
one "$(printf '%s' "$ok" | jq -c '.labels.nodes=null')";           bad "라벨 목록 null"       --input "$tmp/case.json"
one "$(printf '%s' "$ok" | jq -c '.labels.totalCount=101')";       bad "라벨 목록 잘림"       --input "$tmp/case.json"
one "$(printf '%s' "$ok" | jq -c 'del(.isDraft)')";                bad "isDraft 누락"         --input "$tmp/case.json"
one "$(printf '%s' "$ok" | jq -c '.commits.nodes="x"')";           bad "commits 형식 오류"    --input "$tmp/case.json"
one "$(printf '%s' "$ok" | jq -c 'del(.files)')";                  bad "files 누락"           --input "$tmp/case.json"
one "$(printf '%s' "$ok" | jq -c '.files.nodes=[{path:1}]')";      bad "files 경로 타입 오류" --input "$tmp/case.json"
bad "JSON 아님"               --input "$tmp/broken.json"
bad "저장소 응답 null"        --input "$tmp/null.json"
bad "없는 입력 파일"          --input "$tmp/nope.json"
bad "--input 값 누락"         --input
bad "알 수 없는 인자"         --bogus

echo "CHECKED: $n"
if [ "$fail" -eq 0 ]; then echo "VERDICT: PASS"; exit 0; else echo "VERDICT: FAIL"; exit 1; fi
