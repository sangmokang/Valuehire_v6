#!/usr/bin/env bash
# pr-triage.sh — 열린 PR 을 GitHub 상태만으로 🔴/🟡/🟢 세 칸에 나눠 마크다운으로 출력한다.
#
# 왜 (2026-10-07 merge-governance goal):
#   열린 PR 55개가 전부 BLOCKED 로 보여서 "지금 내가 봐야 하는 PR"을 알 수 없었다.
#   판정 근거는 GitHub 이 계산한 값(mergeStateStatus·mergeable·statusCheckRollup)뿐이다.
#   LLM 리뷰 장부·로컬 파일은 읽지 않는다 — 어디서 돌려도 같은 답이 나와야 한다.
#
# 사용법:
#   scripts/pr-triage.sh                 # gh 로 현재 저장소를 조회
#   scripts/pr-triage.sh --input f.json  # 조회 결과(GraphQL 응답 JSON)로 판정만 (시험용)
#
# 리뷰에서 재현된 결함은 GitHub 이 모른다. 작성자는 자기 PR 에 "변경 요청"을 걸 수 없으므로
# PR 에 needs-fix 라벨을 달아 표시한다 — 이 라벨은 CLEAN 보다 우선해 🔴 로 보낸다.
#
# 종료값: 0 = 판정 출력 완료 / 2 = 조회·입력·형식 실패(판정하지 못함, P3)
set -uo pipefail

STALE_DAYS=14
input=""
if [ "${1:-}" = "--input" ]; then
  input="${2:-}"
  [ -n "$input" ] && [ -f "$input" ] || { echo "FAIL: --input 파일이 없다 — ${input:-<빈 값>}" >&2; exit 2; }
elif [ $# -gt 0 ]; then
  echo "FAIL: 알 수 없는 인자 — $*" >&2; exit 2
fi

QUERY='query($owner:String!,$name:String!){repository(owner:$owner,name:$name){pullRequests(states:OPEN,first:100,orderBy:{field:UPDATED_AT,direction:DESC}){totalCount nodes{number title url isDraft baseRefName mergeable mergeStateStatus updatedAt labels(first:100){totalCount nodes{name}} files(first:100){totalCount nodes{path}} commits(last:1){nodes{commit{statusCheckRollup{state}}}}}}}}'

if [ -z "$input" ]; then
  repo=$(gh repo view --json nameWithOwner --jq .nameWithOwner) || { echo "FAIL: 저장소 조회 실패" >&2; exit 2; }
  raw=$(gh api graphql -f query="$QUERY" -F owner="${repo%/*}" -F name="${repo#*/}") || { echo "FAIL: PR 조회 실패" >&2; exit 2; }
else
  raw=$(cat "$input") || { echo "FAIL: 입력 읽기 실패" >&2; exit 2; }
fi

# 형식 검사: 모르는 것은 통과가 아니다. GraphQL 부분 오류, 필드 누락·타입 오류, PR 100건 초과·라벨 100개
# 초과로 잘린 목록은 판정하지 않는다(라벨이 잘리면 needs-fix 를 놓쳐 🟢 로 둔갑한다 — V1 2026-10-07).
printf '%s' "$raw" | jq -e '
  def iso: type=="string" and test("^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$");
  def node_ok: type=="object"
    and (.number|type=="number") and (.title|type=="string") and (.url|type=="string")
    and (.isDraft|type=="boolean") and (.baseRefName|type=="string")
    and (.mergeable|type=="string") and (.mergeStateStatus|type=="string") and (.updatedAt|iso)
    and (.labels|type=="object") and (.labels.nodes|type=="array")
    and (.labels.totalCount == (.labels.nodes|length))
    and all(.labels.nodes[]; type=="object" and (.name|type=="string"))
    and (.files|type=="object") and (.files.totalCount|type=="number") and (.files.nodes|type=="array")
    and all(.files.nodes[]; type=="object" and (.path|type=="string"))
    and (.commits|type=="object") and (.commits.nodes|type=="array") and ((.commits.nodes|length) <= 1)
    and all(.commits.nodes[]; type=="object" and (.commit|type=="object")
      and (.commit.statusCheckRollup == null
           or ((.commit.statusCheckRollup|type=="object") and (.commit.statusCheckRollup.state|type=="string"))));
  (has("errors")|not)
  and (.data.repository.pullRequests
       | (.totalCount|type=="number") and (.nodes|type=="array")
         and (.totalCount == (.nodes|length)) and all(.nodes[]; node_ok))
' >/dev/null 2>&1 || { echo "FAIL: 조회 결과 형식 오류·부분 오류 또는 잘린 목록 — 판정하지 않는다" >&2; exit 2; }

now=$(date -u +%s)
out=$(printf '%s' "$raw" | jq -r --argjson now "$now" --argjson stale "$STALE_DAYS" '
  def ci: (.commits.nodes[0].commit.statusCheckRollup.state // "NONE");
  def wf: any(.files.nodes[].path; startswith(".github/workflows/"));
  def files_cut: .files.totalCount != (.files.nodes|length);
  def safe: gsub("[\r\n]+"; " ") | gsub("(?<c>[\\[\\]`<>#@])"; "\\\(.c)");
  def age: (($now - (.updatedAt|fromdateiso8601)) / 86400 | floor);
  def verdict:
    if .baseRefName != "main" then ["Y", "스택 PR(base=\(.baseRefName)) — 아래 PR 이 먼저 병합돼야 한다"]
    elif .isDraft then ["Y", "초안(Draft)"]
    elif ([.labels.nodes[].name | ascii_downcase] | index("needs-fix")) then ["R", "리뷰 결함 미해결(needs-fix 라벨)"]
    elif .mergeable == "CONFLICTING" then ["R", "main 과 충돌"]
    elif (ci == "FAILURE" or ci == "ERROR") then ["R", "CI 실패"]
    elif wf then ["Y", "workflow 변경 — 자기 검사를 약화했을 수 있어 diff 확인 필요"]
    elif files_cut then ["Y", "변경 파일 100개 초과 — workflow 변경 여부 확인 불가"]
    elif (.mergeable == "MERGEABLE" and .mergeStateStatus == "CLEAN" and ci == "SUCCESS") then ["G", "필수 검사 통과·충돌 없음·main 최신"]
    elif .mergeStateStatus == "BEHIND" then ["Y", "main 보다 뒤처짐 — Update branch 후 CI 재실행"]
    elif (ci == "PENDING" or ci == "EXPECTED") then ["Y", "CI 진행 중"]
    elif ci == "NONE" then ["Y", "CI 결과 없음"]
    else ["Y", "판정 불가(merge=\(.mergeStateStatus), ci=\(ci)) — 다시 조회"]
    end;
  .data.repository.pullRequests.nodes
  | map(. + {v: verdict, a: age})
  | def line: "- [#\(.number)](\(.url)) \(.title|safe) — \(.v[1])" + (if .a >= $stale then " · \(.a)일 미변경" else "" end);
    def section($k; $h): (map(select(.v[0]==$k))) as $xs
      | "### \($h) (\($xs|length))", (if ($xs|length)==0 then "- 없음" else ($xs|sort_by(.number)|.[]|line) end), "";
    "## PR 관제 — 열린 PR \(length)개", "",
    section("R"; "🔴 즉시 확인"),
    section("G"; "🟢 병합 가능"),
    section("Y"; "🟡 사람 결정·대기"),
    "판정 근거: GitHub mergeStateStatus·mergeable·최신 커밋 검사 결과·needs-fix 라벨만 사용. 병합은 사람이 직접 한다."
') || { echo "FAIL: 판정 단계 실패 — 출력하지 않는다" >&2; exit 2; }
printf '%s\n' "$out"
