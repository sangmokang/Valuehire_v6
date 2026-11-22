VERDICT: PASS

# 결론

V1(Codex)이 지적한 두 가지 큰 결함, 즉 결함 표시가 붙은 PR을 "병합 가능"으로 알리는 문제와 잘못되거나 불완전한 조회 결과를 정상으로 판정하는 문제는 현재 버전(c5c5757)에서 모두 고쳐졌습니다. V1 판정서에 적힌 반례를 하나도 빼지 않고 다시 넣었는데, 전부 막혔습니다. 실제 GitHub에서 받은 55건도 새로 강화한 검사를 그대로 통과했고 분류 결과(즉시 확인 21 / 병합 가능 1 / 대기 33)도 저장된 증거와 같습니다. 정상 입력을 지나치게 거부하는 문제도 보이지 않았습니다. 병합 규칙의 실제 설정은 문서 내용과 일치하고, 우회할 수 있는 권한자도 없습니다.

다만 막을 정도는 아닌 결함 4건이 남아 있습니다(아래 S3 3건, 조건부 S2 1건). 가장 중요한 것은 공개 저장소라는 점입니다. 외부 기여자가 자기 PR 안에서 검사 파일을 약하게 고치면 그 PR이 매일 보고에 "병합 가능"으로 뜰 수 있습니다. 이 위험 자체는 goal 문서에 R-1로 이미 적혀 있습니다. 하지만 이번에 추가된 매일 보고가 그런 PR에도 "필수 검사 통과"라는 문구를 붙인다는 점은 문서에 없습니다.

## 건너뜀·미확인·추정 (앞부분 고지)

- **건너뜀(쓰기 금지)**: workflow 예약 실행, 이슈 생성·댓글, 포크 PR로 `verify` 위조 시연, 줄바꿈이 들어간 PR 제목 생성은 실행하지 않았습니다. 모두 GitHub 쓰기가 필요하기 때문입니다.
- **미확인**: 사장님 계정의 저장소 구독(watch) 상태를 확인하려 `GET repos/.../subscription`을 호출했지만 `notifications` 권한이 없어 404가 나왔습니다. 그래서 "봇 댓글이 메일로 간다"는 goal의 전제는 확인하지 못했습니다.
- **추정**: GitHub가 PR 제목에 줄바꿈을 허용하는지는 실측하지 못했습니다. 결함 V2-2는 코드 수준에서만 재현했고 실제 악용 가능성은 추정입니다. 포크 PR의 `pull_request` workflow가 PR 쪽 workflow 파일로 돈다는 것은 GitHub 공개 동작에 근거한 추정이고, 이 세션에서 시연하지는 않았습니다.
- **실패 후 재시도**: 없음.
- **실행 위치**: 임시 파일은 `mktemp -d`로 만든 `/var/folders/.../tmp.Gj97GpOkjb` 아래에만 두었습니다. 워크트리는 수정하지 않았습니다(`git status --short` 0줄). GitHub는 GET과 GraphQL 조회만 사용했습니다.

# 판단 근거

- **선택한 해석**: "🟢 = 사람이 병합 후보로 믿어도 되는 상태", "판정할 수 없는 입력 = 종료값 2". V1과 같은 해석입니다.
- **버린 해석 1**: "픽스처 시험이 통과하면 실제 응답도 통과한다." V1은 실제 GraphQL 실행을 건너뛰었고, 나중에 추가된 형식 검사(정규식 날짜, totalCount 일치, 노드 타입)는 픽스처로만 검증됐습니다. 이것이 서로 연관된 맹점일 수 있어 실제로 실행해 보았습니다. **틀렸다면 깨지는 것**: 실제 응답이 형식 검사에 걸려 매일 workflow가 종료값 2로 실패하고, 보고가 한 번도 나가지 않습니다. 실측 결과는 rc 0, 55건이므로 이 위험은 반증됐습니다.
- **버린 해석 2**: "V1 결함 3(초안 실패를 🔴로)은 동작 결함이다." 판단 근거는 V2-공격 3에 있습니다. V1이 지적한 것은 문서와 시험이 서로 맞지 않는다는 결함이었고, 이 지적은 정당했습니다. 그러나 "운영 우선순위를 잘못 잡게 한다"는 사업 영향 서술은 과장으로 판정했습니다.
- **PASS로 판정한 이유**: 인수 기준 AC-1~6과 counter-AC가 막으려던 "가짜 🟢"는 모두 막혔습니다. 남은 결함은 (1) goal이 이미 받아들인 위험 R-1의 범위 서술 부족, (2) 조건부 표시 위조, (3) 문서 숫자가 어긋난 것입니다. 이 중 어떤 것도 이번 변경의 인수 기준을 깨지 않습니다.
- **틀렸다면 깨지는 것**: GitHub가 PR 제목에 줄바꿈을 그대로 저장한다면 V2-2는 S2로 올라갑니다. 외부인이 보고에 가짜 🟢 칸을 만들 수 있게 되기 때문입니다.

# 기술 상세와 증거 원문

## 집계표

| 구분 | 건수 | 내용 |
|---|---|---|
| V1이 잡은 결함 | 5건(+조건부 1) | 1 라벨 잘림·대소문자, 2 부분 오류·형식, 3 AC-5와 시험 모순, 4 대체 근거 부족, 5 정본 시제. 조건부: mergeable UNKNOWN+CLEAN |
| V1 결함의 현재 상태 | 5건 모두 NOT_REPRODUCIBLE(수정됨) | 1·2는 반례를 직접 다시 넣어 확인, 3·4·5는 문서 대조로 확인 |
| V2가 잡은 V1의 과장 | 1건 | 결함 3의 사업 영향 서술(아래 공격 3) |
| V2가 잡은 V1의 누락 | 4건 | V2-1 `verify` 검사 이름 결합 범위(조건부 S2), V2-2 제목 주입(S3), V2-3 문서 숫자 어긋남(S3), V2-4 알림 전제 미확인(S3) |
| V1의 미실행을 V2가 메움 | 1건 | 실제 GraphQL 실행(양성 대조군). V1은 POST라서 건너뜀 → V2 실행 rc 0, 55건 |

→ 해석: V1이 지적한 것은 모두 고쳐졌습니다. V2가 새로 찾은 것은 병합을 막을 정도의 결함은 아니고, 위험 서술의 범위와 문서 정확성 문제입니다.

## 1. V1 결함 1·2 반례 재투입 (HEAD c5c5757)

정상 PR #7(MERGEABLE/CLEAN/SUCCESS)을 기준으로 필드 하나씩 바꿔 `bash scripts/pr-triage.sh --input <f>`에 넣었습니다.

```
[control_ok] rc=0 | 🔴 즉시 확인 (0) | 🟢 병합 가능 (1) | - [#7](u7) t7 — 필수 검사 통과·충돌 없음·main 최신
[needs_fix_mixedcase] rc=0 | 🔴 즉시 확인 (1) | 🟢 병합 가능 (0) | - [#7](u7) t7 — 리뷰 결함 미해결(needs-fix 라벨)
[needs_fix_upper] rc=0 | 🔴 즉시 확인 (1) | 🟢 병합 가능 (0) | ...
[label21_full] rc=0 | 🔴 즉시 확인 (1) | 🟢 병합 가능 (0) | ...
[label21_truncated20] rc=2 | FAIL: 조회 결과 형식 오류·부분 오류 또는 잘린 목록 — 판정하지 않는다
[label101_trunc100] rc=2 | FAIL: ...
[updatedAt_missing] rc=2 | FAIL: ...
[updatedAt_notdate] rc=2 | FAIL: ...
[nodes_null] rc=2 | FAIL: ...
[labels_nodes_null] rc=2 | FAIL: ...
[errors_partial] rc=2 | FAIL: ...
[errors_empty_array] rc=2 | FAIL: ...
[errors_null] rc=2 | FAIL: ...
```
→ 해석: V1 반례(Needs-Fix, 21번째 라벨, 앞 20개만 받은 라벨, updatedAt 누락·"not-date", nodes [null], labels.nodes null, errors 동반)는 전부 🔴 또는 종료값 2가 됐습니다. 판정: **결함 1 NOT_REPRODUCIBLE, 결함 2 NOT_REPRODUCIBLE**. 무변경 대조군은 🟢 1이므로 시험 자체는 살아 있습니다. `errors:[]`와 `errors:null`까지 거부하는 점은 과잉 거부 쪽에 가깝지만, GitHub는 오류가 없으면 `errors` 키 자체를 보내지 않습니다. 실제 응답에서 `has_errors:false`를 확인했으므로 무해합니다.

수정 지점:
- `scripts/pr-triage.sh:28` — 조회 쿼리. `labels(first:100){totalCount nodes{name}}`로 라벨을 100개까지 받고 총수를 함께 받습니다.
- `scripts/pr-triage.sh:39-56` — 형식 검사 게이트. errors 키 존재, 노드 타입, ISO 날짜, 라벨·PR 총수 일치를 검사하고, 하나라도 어긋나면 종료값 2를 냅니다.
- `scripts/pr-triage.sh:65` — needs-fix 판정. `ascii_downcase`로 소문자로 바꿔 비교합니다.
- `scripts/pr-triage.sh:84` — 판정 단계 jq 실패를 종료값 2로 바꿉니다.

## 2. V1 PASS 판정 재공격

### (a) 실제 GitHub 응답 양성 대조군 — 반증 실패(통과)

```
$ bash scripts/pr-triage.sh > live.md   → rc=0
## PR 관제 — 열린 PR 55개
### 🔴 즉시 확인 (21)
### 🟢 병합 가능 (1)
- [#122](https://github.com/sangmokang/Valuehire_v6/pull/122) feat(herdr): ... — 필수 검사 통과·충돌 없음·main 최신
### 🟡 사람 결정·대기 (33)
```
같은 쿼리로 받은 원본 응답의 형태는 다음과 같습니다.
```
{"has_errors":false,"total":55,"n":55,"mergeable":{"CONFLICTING":9,"MERGEABLE":46},
 "mss":{"BEHIND":30,"BLOCKED":1,"CLEAN":14,"DIRTY":9,"UNSTABLE":1},
 "ci":{"FAILURE":21,"SUCCESS":32},"maxlabels":1,"commitsLen":[1],"updatedAtSample":"2026-10-06T16:44:14Z"}
```
→ 해석: 실제 응답은 날짜 정규식(소수점 초 없음), 총수 일치, commits 길이 1을 모두 만족합니다. 강화된 형식 검사가 실제 데이터를 거부하지 않습니다. 분류 21/1/33은 저장된 `triage-after-rule-change.md`와 같습니다. CI 상태 합계 21+32=53이고, 나머지 2건(#77·#78)은 statusCheckRollup이 null입니다.

CLEAN인데 🟢가 아닌 13건의 이유도 실제 데이터로 하나씩 대조했습니다.
```
123 false main MERGEABLE CLEAN SUCCESS needs-fix   → 🔴(라벨)
121/118/119 true main ... CLEAN SUCCESS            → 🟡(초안)
96 97 87 94 90 true <stack> CLEAN SUCCESS         → 🟡(스택·초안)
93 89 false task/hs-resume-evidence-contract CLEAN SUCCESS → 🟡(스택)
77 78 false task/... CLEAN null                     → 🟡(스택, CI 없음)
```
→ 해석: 🟢가 하나뿐인 것은 과소 판정이 아니라 규칙대로 나온 결과입니다.

### (b) statusCheckRollup·mergeable·mergeStateStatus의 열거값 밖 입력 — 반증 실패(통과)

```
state=[SUCCESS] 🟢1 | [FAILURE] CI 실패 | [PENDING] CI 진행 중 | [ERROR] CI 실패 | [EXPECTED] CI 진행 중
state=[success]/[NEUTRAL]/[SKIPPED]/[""]/[" SUCCESS"] → 🟢0, "판정 불가(...) — 다시 조회"
rollup={} → rc=2 | rollup.state=null → rc=2
mergeable=[mergeable]/[MERGEABLE_]/[""] → 🟢0 판정 불가
mss=[clean]/HAS_HOOKS/UNKNOWN/UNSTABLE/DRAFT/[""] → 🟢0 판정 불가
```
→ 해석: 🟢 조건(`:68`)이 세 값 모두 정확히 일치해야 한다는 허용 목록 방식이라서, 모르는 값은 전부 🟡로 떨어집니다. 대소문자가 다르거나 앞에 공백이 붙은 SUCCESS도 🟢가 되지 않습니다.

### (c) jq `//`가 오류를 삼키는 지점 — 반증 실패(🟢 둔갑 없음)

남은 `//`는 두 곳입니다. `scripts/pr-triage.sh:60`(CI 상태가 없으면 "NONE")과 `.github/workflows/pr-triage.yml:44`(열린 관제 이슈 번호가 없으면 빈 값)입니다.
```
commits.nodes=[]            → rc=0 🟢0 "CI 결과 없음"
statusCheckRollup 키 자체 없음 → rc=0 🟢0 "CI 결과 없음"
```
→ 해석: `:60`의 `//`는 키가 빠진 응답을 null로 흡수합니다. 형식 검사 `:50`의 `== null`도 키 누락을 null로 봅니다. 따라서 "키 누락"과 "CI 없음"을 구분하지 못하는 것은 맞습니다. 그러나 결과가 🟡이므로 🟢로 둔갑하지는 않습니다. 결함이 아니라 관찰로만 기록합니다. 워크플로의 `//`는 이슈를 새로 만드는 분기로만 이어지고 판정에는 영향이 없습니다.

### (d) 과잉 거부 — 반증 실패(실데이터 기준 없음)

```
n=0   rc=0 "열린 PR 0개"   | n=100 rc=0 🟢100 | totalCount=101,nodes=100 → rc=2
updatedAt 미래            → rc=0 🟢1
알 수 없는 필드 추가·최상위 extensions → rc=0 🟢1
updatedAt "…14.123Z"(소수점 초) → rc=2
```
→ 해석: 정상 입력은 모두 통과합니다. 소수점 초가 있는 날짜는 거부되지만 GitHub의 DateTime은 소수점 초를 쓰지 않으며, 실제 응답에서도 그렇게 확인했습니다. GitHub가 형식을 바꾸면 종료값 2로 멈추는데, 실패를 숨기지 않는 방향이므로 허용합니다. 열린 PR이 101건 이상이 되면 매일 실패하는 것은 설계된 동작입니다(현재 55건).

### (e) workflow 실패가 조용한 성공으로 끝나는가 — 반증 실패(정적 분석, 실행은 NOT_RUN)

- `.github/workflows/pr-triage.yml:37` — `set -euo pipefail`. 이후 모든 명령이 실패하면 즉시 중단합니다.
- `:38` — 스크립트가 종료값 2를 내면 이 줄에서 단계가 실패합니다. 댓글 단계(`:50`)에는 도달하지 않으며, 실패한 job으로 표시됩니다.
- `:44`·`:46` — `num=$(gh …)` 형태의 대입이라 명령 치환이 실패하면 errexit가 걸립니다.
- `:50` — 마지막 줄인 댓글 게시가 실패하면 단계도 실패합니다. 마지막의 `echo PASS`는 그다음에만 실행됩니다.

→ 해석: 성공처럼 끝나는 경로는 찾지 못했습니다. 남는 것은 "실패했을 때 누가 알게 되는가"입니다. 예약 workflow가 실패하면 GitHub는 workflow 파일을 마지막으로 수정한 사람에게 메일을 보냅니다(사용자가 알림 설정을 끄지 않았다면). 이 동작은 미확인입니다.

### (f) ruleset 실제 값과 우회 구멍 — 주장과 일치, 구멍 없음(1건 범위 지적)

```
rulesets 목록: {"enforcement":"active","id":23568184,"name":"main-pr-verify-gate","source_type":"Repository","target":"branch"}  ← 단 1개
23568184: bypass_actors:[], current_user_can_bypass:"never", include:["refs/heads/main"],
  rules: pull_request(required_approving_review_count:0), required_status_checks([{"context":"verify","integration_id":15368}], strict:true)
rules/branches/main: 같은 ruleset_id 의 위 두 규칙만
branches/main/protection: 404 "Branch not protected"   (고전 보호 없음, git-workflow.md 한계 절과 일치)
branches/main: {"protected":true}
repo: visibility "public", allow_forking true
actions/permissions/fork-pr-contributor-approval: {"approval_policy":"first_time_contributors"}
actions/permissions/workflow: {"default_workflow_permissions":"read","can_approve_pull_request_reviews":false}
```
→ 해석: goal 문서와 `docs/sot/git-workflow.md`에 적힌 ruleset id, 규칙 2종, strict 설정, 우회자 0은 실제 값과 일치합니다. 다른 ruleset이나 고전 보호 규칙 때문에 생기는 우회 경로도 없습니다. 다만 아래 V2-1에서 보듯, 필수 검사 `verify`는 GitHub Actions가 낸 같은 이름의 검사라면 무엇이든 인정됩니다. 이것은 우회자 0과는 다른 축의 구멍입니다.

## 3. V1 FAIL 판정의 과장·오탐 공격

- **결함 3(초안·스택 뒤에 실패가 가려짐)**: 판정은 **부분 과장**입니다. V1 시점의 AC-5는 "CI 실패·충돌·결함 라벨 → 빨강"이라고만 적었고, 시험 `:60`은 "초안 실패 → 🟡"를 기대했습니다. 문서와 시험이 서로 다른 답을 요구했다는 지적은 정당합니다. 그러나 "즉시 고쳐야 할 실패를 대기로 밀어 우선순위를 잘못 잡게 한다"는 사업 영향은 과장입니다. 초안·스택 PR은 그 자체로 병합 대상이 아니므로, 그 CI 실패는 사장님이 지금 확인할 일이 아니라 작성 중인 상태입니다. 또 이 순서는 🟢 둔갑을 만들지 않습니다. 현재 AC-5(goal:84)가 판정 순서 ①을 명시해 모순은 해소됐습니다.
- **결함 1의 대소문자 부분**: GitHub 라벨 이름은 대소문자를 구분하지 않고 유일하므로 `needs-fix`와 `Needs-Fix`가 함께 존재할 수는 없습니다. 하지만 누군가 라벨 이름을 `Needs-Fix`로 바꾸면 옛 코드는 놓쳤을 것입니다. V1도 조건부라고 적었으므로 과장은 아닙니다.
- **결함 4·5**: 정당합니다. 현재 goal의 C 절은 2건(#118·#120)으로 줄었고, `git-workflow.md:31`은 "기본 브랜치에 들어간 뒤부터 … 첫 예약 실행 확인 전까지는 수동 실행만 확인된 상태"로 고쳐졌습니다.
- **V1 미실행 고지의 정확성**: V1이 "`gh api graphql`은 POST라서 건너뛰었다"고 밝힌 것은 정직한 고지였습니다. 그러나 그 결과 형식 강화 이후의 실제 응답 검증이 비어 있었습니다. V2가 이번에 메웠습니다(2-(a)).

## 4. 남은 결함

### V2-1 [S2, 조건부·NOT_TESTED] 원문 제목: "외부 포크 PR이 자기 `verify`를 만들어 매일 보고에 🟢 '필수 검사 통과'로 뜰 수 있음"

- 위치: `scripts/pr-triage.sh:68` — 🟢 조건. GitHub의 CLEAN과 SUCCESS만 봅니다. 위치: ruleset 23568184의 `required_status_checks` — 검사 이름이 `verify`이고 integration_id가 15368(GitHub Actions)이기만 하면 인정됩니다.
- 원인: 필수 검사는 이름과 발행 앱에만 묶여 있고 어떤 workflow 파일이 냈는지는 보지 않습니다. 공개 저장소이고 포크 PR 승인은 "첫 기여자만" 필요합니다(`approval_policy:first_time_contributors`). 따라서 두 번째로 기여하는 외부인이 `verify.yml`을 약화하거나, `verify`라는 이름의 job을 가진 새 workflow를 추가하면 자동 실행됩니다(추정: `pull_request` 이벤트는 병합 커밋의 workflow 파일로 돈다는 GitHub 공개 동작에 근거). goal의 R-1과 `git-workflow.md` 한계 절은 "PR이 자기 `verify.yml`을 약화"만 적고 있어, 새 workflow 추가와 외부 포크 경로가 빠져 있습니다.
- 사업 영향: 매일 보고가 그런 PR에 "필수 검사 통과·충돌 없음·main 최신"이라는 🟢 문구를 붙입니다. 사장님이 diff를 보지 않고 🟢만 믿고 병합하면 외부 코드가 main에 들어갑니다. 병합은 사람이 해야 하고 우회자도 0이므로 자동으로 뚫리지는 않습니다. 그래서 S1이 아니라 S2로 판정했습니다.
- 재현 명령: 쓰기 금지 때문에 실행하지 않았습니다. 정적 근거는 위 2-(f)의 GET 원문입니다.

설계 지적:
- 무엇을: 🟢 조건에 "PR이 `.github/workflows/`를 건드리지 않음"을 추가하거나(바꿨다면 🟡 "workflow 변경 — diff 확인"), 최소한 R-1 서술을 "새 workflow 추가·외부 포크 포함"으로 넓히십시오.
- 왜: 🟢 문구가 "필수 검사 통과"라고 주장하는데, 그 검사가 PR 자신이 정의한 것일 수 있습니다.
- 버린 길: ruleset에 workflow 경로 고정(required workflows)을 거는 방법입니다. 개인 계정 요금제에서 쓸 수 있는지 미확인이고, 규칙 구조를 다시 짜야 합니다.
- 대가: GraphQL 쿼리에 `files(first:100){nodes{path}}`를 더해야 하며, 파일이 100개를 넘을 때의 잘림 처리도 함께 필요합니다.
- 되돌리기: 해당 조건 한 줄과 시험 한 쌍을 지우면 됩니다.

### V2-2 [S3, 조건부] 원문 제목: "PR 제목의 줄바꿈·마크다운이 보고 본문에 그대로 들어가 가짜 칸을 만들 수 있음"

- 위치: `scripts/pr-triage.sh:76` — 한 줄 출력 서식. `\(.title)`을 이스케이프 없이 넣습니다.
- 원인: 제목 안의 줄바꿈, `### `, `[...](...)`, `@멘션`을 처리하지 않습니다.
- 재현(코드 수준):
```
title="x\n### 🟢 병합 가능 (9)\n- [#999](https://evil) 가짜"  → rc=0
### 🟢 병합 가능 (1)
- [#7](u7) x
### 🟢 병합 가능 (9)
- [#999](https://evil) 가짜 — 필수 검사 통과·충돌 없음·main 최신
```
→ 해석: 외부인이 연 PR의 제목으로 이슈 댓글 안에 가짜 🟢 칸과 가짜 링크를 만들 수 있습니다. GitHub가 PR 제목의 줄바꿈을 저장하는지는 미확인입니다. 줄바꿈이 없어도 `@멘션`이나 링크 문법은 그대로 렌더링됩니다.
- 사업 영향: 보고를 오독하거나 외부 링크를 누를 위험이 있고, 멘션 알림 스팸이 생길 수 있습니다.
- 조치안: 제목에서 `\n\r`을 공백으로 바꾸고, `[`, `]`, `@`, `` ` ``를 이스케이프하십시오(`gsub`). 시험 한 쌍이 필요합니다.

### V2-3 [S3] 원문 제목: "정본·goal의 숫자가 수정 후 코드와 어긋남"

- `docs/sot/verification-commands.md:51` — 인수 검사 목록 행. "분류 규칙 14종 … 조회·형식 실패 6종"이라고 적혀 있지만, 실제 시험은 분류 16건과 종료값 2 사례 14건입니다(`acceptance-pr-triage.sh:57-72`, `:94-111`).
- `docs/engineering/merge-governance-goal-2026-10-07.md:70` — 설계 카드. "69줄 스크립트"라고 적혀 있지만 실제는 `wc -l` 기준 85줄입니다.
- 사업 영향: 정본 숫자를 믿고 시험 범위를 판단하면 형식 실패 방어 8종을 놓쳤다고 오판할 수 있습니다. 동작에는 영향이 없습니다.

### V2-4 [S3, 미확인] 원문 제목: "매일 댓글이 사장님 메일로 간다는 전제를 확인하지 않음"

- `.github/workflows/pr-triage.yml:4` — 주석 "댓글은 GitHub 기본 알림(메일)으로 사장님께 간다".
- 원인: 이슈는 github-actions 봇이 만들고 댓글도 봇이 답니다. 사장님은 그 이슈에 참여하지도 멘션되지도 않으므로, 저장소를 "모든 활동"으로 구독하고 있어야만 메일이 갑니다. 구독 상태 GET은 권한 부족으로 404였습니다.
- 사업 영향: 보고가 매일 게시돼도 아무도 받지 못할 수 있습니다.
- 조치안: 병합 후 첫 실행에서 메일 수신을 확인하십시오(goal R-4 NOT_RUN 항목과 합쳐서). 안 오면 이슈 본문에 `@sangmokang`을 멘션하면 됩니다.

## 5. 반증 기록(깨뜨리려다 실패한 것)

| 시도 | 기대한 깨짐 | 실제 |
|---|---|---|
| 실제 GraphQL 응답을 새 형식 검사에 넣음 | 종료값 2(과잉 거부) | rc 0, 55건, 21/1/33 |
| rollup state 소문자·공백·NEUTRAL·SKIPPED·빈 문자열 | 🟢 둔갑 | 모두 🟡 판정 불가 |
| mergeable·mergeStateStatus 열거값 밖 | 🟢 둔갑 | 모두 🟡 |
| commits.nodes 빈 배열·rollup 키 누락 | 🟢 둔갑 | 🟡 CI 결과 없음 |
| needs-fix 단독 라벨(index 0이 거짓으로 취급되는지) | 🟢 둔갑 | 🔴(jq에서 0은 참) |
| 0·100·101건 | 경계 오류 | 0 정상, 100 정상, 101 → 2 |
| errors 키 변형(빈 배열·null) | 부분 오류 통과 | 2 |
| workflow 명령 실패가 성공으로 끝나는 경로 | 조용한 성공 | 정적으로 찾지 못함(errexit·명령 치환 대입) |
| 다른 ruleset·고전 보호·bypass | 우회 | ruleset 1개, 고전 404, bypass [] |

## 6. 인수 시험 실행 원문

```
$ bash scripts/verify/run-acceptance.sh scripts/acceptance-pr-triage.sh
PASS: 정상 입력 종료값 0
PASS: 깨끗한 정상 PR 은 병합 가능
PASS: 충돌 PR 은 즉시 확인
PASS: CI 실패 PR 은 즉시 확인
PASS: 초안은 CI 실패여도 대기(초안 우선)
PASS: main 이 아닌 base(스택) 는 대기
PASS: 뒤처진 PR 은 병합 가능이 아니다
PASS: CI 진행 중은 대기
PASS: 이유 모를 BLOCKED 는 판정 불가로 대기
PASS: 초안은 CLEAN 이어도 병합 가능이 아니다
PASS: CI ERROR 는 즉시 확인
PASS: CLEAN 이라도 CI 결과가 없으면 병합 가능 아님
PASS: 오래된 정상 PR 도 병합 가능
PASS: needs-fix 라벨은 GitHub 이 CLEAN 이어도 즉시 확인
PASS: 다른 라벨은 분류에 영향 없음
PASS: 라벨 대소문자가 달라도 needs-fix 로 본다(GitHub 라벨은 대소문자 무시)
PASS: mergeable 이 UNKNOWN 이면 CLEAN 이어도 병합 가능 아님
PASS: 장기 미변경 표시
PASS: 최근 PR 은 미변경 표시 없음
PASS: 총 개수 16
PASS: 열린 PR 0개 정상 출력
PASS: 100건 초과로 잘린 목록 → 종료값 2
PASS: GraphQL errors 동반(부분 실패) → 종료값 2
PASS: updatedAt 누락 → 종료값 2
PASS: updatedAt 형식 오류 → 종료값 2
PASS: 노드가 null → 종료값 2
PASS: 라벨 목록 null → 종료값 2
PASS: 라벨 목록 잘림 → 종료값 2
PASS: isDraft 누락 → 종료값 2
PASS: commits 형식 오류 → 종료값 2
PASS: JSON 아님 → 종료값 2
PASS: 저장소 응답 null → 종료값 2
PASS: 없는 입력 파일 → 종료값 2
PASS: --input 값 누락 → 종료값 2
PASS: 알 수 없는 인자 → 종료값 2
CHECKED: 35
VERDICT: PASS
OK(run-acceptance): scripts/acceptance-pr-triage.sh — 판정 36건, CHECKED 35
RUNNER_RC=0
```
→ 해석: goal AC-5에 적힌 기대값 `VERDICT: PASS`, `CHECKED: 35`와 일치합니다. 이 시험은 `.github/workflows/verify.yml:239-242`에 CI 단계로 등록돼 있습니다. 다만 V2-1·V2-2를 잡는 시험은 없습니다.

검증 종료 상태: 워크트리 HEAD c5c5757, `git status --short` 0줄, 원격 쓰기 0회.
