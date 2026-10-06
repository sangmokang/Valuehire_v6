VERDICT: FAIL

# 결론

현재 변경분을 그대로 합쳐 매일 보고를 신뢰하시면 안 됩니다. 결함 표시가 붙은 요청을 합쳐도 되는 것으로 알릴 수 있고, 잘못된 조회 자료도 정해진 방식으로 거절하지 못합니다. 합치기를 제한하는 현재 설정은 확인했지만, 보고 기능의 결함을 고친 뒤 다시 검증해야 합니다.

판정 앞부분의 범위와 미확인: 저장소 파일은 수정하지 않았습니다. 임시 입력은 모두 `/private/tmp`의 `tempfile`로 만들고 삭제했습니다. 원격에는 쓰지 않았습니다. `scripts/pr-triage.sh`의 실제 온라인 실행은 그 내부가 `gh api graphql -f`로 조회하며 HTTP POST를 사용하므로, 이번 GET 전용 조건에 따라 **건너뛰었습니다**. 초기 표본에 `gh pr view`를 5회 사용했으나 CLI 내부 전송 방식이 GET이라고 입증할 수 없어 그 출력은 판정 근거에서 제외하고 같은 표본을 REST GET으로 다시 조회했습니다. 예약 workflow, 실제 이슈 생성·댓글, 서버 병합 거절, 과거 ruleset의 실제 적용, 임시 실험 PR은 쓰기 금지와 기본 브랜치 미병합 때문에 **미확인**입니다. `rulesets/23568184/versions` GET은 HTTP 404였고 재시도하지 않았습니다. 과거 상태는 저장소 증거 파일이라는 한계가 있습니다. `gh api .../actions/workflows/pr-triage.yml` GET도 HTTP 404였으며, 현재 기본 브랜치에 workflow가 아직 없어 예상되는 결과로 해석했습니다. 추정은 결함 본문에서 따로 표시했습니다.

# 판단 근거

병합 전 판정: **REQUEST_CHANGES**.

선택한 해석은 “초록 = 사용자가 병합 후보로 믿을 수 있는 상태”, “입력 오류 = 종료값 2”입니다. [goal 인수 기준](/private/tmp/claude-501/-Users-kangsangmo-Desktop-Valuehire-v6/01a97eee-4b0b-44ba-8764-555a8234ab73/scratchpad/v1clone/docs/engineering/merge-governance-goal-2026-10-07.md:84)은 CI 실패·충돌·결함 라벨을 빨강으로, CLEAN과 검사 성공만 초록으로, 조회·형식 실패를 2로 정합니다. “현재 라벨이 11개뿐이니 라벨 20개 제한은 무해하다”는 해석은 버렸습니다. PR별 라벨이 늘면 같은 코드가 조용히 판정을 바꾸기 때문입니다. 틀렸다면 21번째 라벨을 포함한 원격 응답과 입력 fixture가 같은 결과를 내야 하는데, 아래에서 달랐습니다.

“기본 인수 시험 통과 = 전체 입력 계약 통과”도 버렸습니다. 새로 만든 정상 형식의 경계 입력에서는 통과했지만, 빠진 필드와 부분 오류 응답에서 계약이 깨졌습니다. 반대로 `mergeStateStatus`가 UNKNOWN·HAS_HOOKS·UNSTABLE인 반례, CI 결과 null, 정확히 100개, 101개 잘림은 기대대로 처리됐으므로 이 부분을 결함으로 적지 않았습니다.

보호 규칙은 변경 전의 `acceptance` 배포 요구 하나가 변경 후 PR 필수·Actions 앱의 `verify`·main 최신 기준으로 바뀌었습니다. 이는 **설정 항목의 교체**이지 단순 삭제는 아닙니다. 현재 설정의 우회자 0, main 적용을 GET으로 확인했습니다. 다만 변경 전 배포 요구가 실제로 항상 무가치했다는 역사적 결론과 서버가 모든 경우에 거절한다는 실험 주장은 이 세션에서 독립 재현하지 못했습니다. 저장소의 [실험 기록](/private/tmp/claude-501/-Users-kangsangmo-Desktop-Valuehire-v6/01a97eee-4b0b-44ba-8764-555a8234ab73/scratchpad/v1clone/docs/engineering/evidence/merge-governance-20261007/probe-matrix.md:17)을 보조 증거로만 인정합니다.

# 기술 상세와 증거 원문

## 1. [높음] 원문 제목: “결함 라벨이 조회 범위·표기 방식에 따라 사라져 초록으로 바뀜”

- 원인: [scripts/pr-triage.sh:28 — GraphQL 라벨을 첫 20개만 조회](/private/tmp/claude-501/-Users-kangsangmo-Desktop-Valuehire-v6/01a97eee-4b0b-44ba-8764-555a8234ab73/scratchpad/v1clone/scripts/pr-triage.sh:28), [scripts/pr-triage.sh:50 — 정확히 소문자 `needs-fix`만 비교](/private/tmp/claude-501/-Users-kangsangmo-Desktop-Valuehire-v6/01a97eee-4b0b-44ba-8764-555a8234ab73/scratchpad/v1clone/scripts/pr-triage.sh:50). [acceptance-pr-triage.sh:48 — 라벨 하나만 넣는 시험](/private/tmp/claude-501/-Users-kangsangmo-Desktop-Valuehire-v6/01a97eee-4b0b-44ba-8764-555a8234ab73/scratchpad/v1clone/scripts/acceptance-pr-triage.sh:48)이 이 경계를 놓쳤습니다.
- 사업 영향: 리뷰에서 재현한 결함이 남은 요청을 사장님께 “병합 가능”으로 알립니다. 라벨 누락의 경우 GitHub가 돌려준 자료만 보면 누락을 알아낼 방법도 없습니다.
- 반례: `CLEAN`, `MERGEABLE`, CI `SUCCESS`인 #7에 `Needs-Fix` 하나를 주면 `rc=0; 🟢 병합 가능 (1)`. 소문자 `needs-fix`를 21번째에 둔 전체 21개 라벨 입력은 빨강이지만, 실제 `labels(first:20)`가 반환할 앞 20개만 주면 `rc=0; 🟢 병합 가능 (1)`. GitHub의 라벨 명칭을 사용자가 다른 대소문자로 만들 수 있는지의 원격 실험은 수행하지 않았으므로 그 경로는 조건부 위험이고, 20개 제한은 코드상 확정입니다. 현재 저장소 라벨 목록은 GET 기준 11개라 현재 #123에서는 재현되지 않았습니다.

무엇을: 라벨 목록의 총수·페이지를 확인해 끝까지 가져오고, 결함 라벨 이름의 대소문자 정책을 명시한 뒤 비교하십시오.
왜: 일부 라벨만 받은 응답은 초록을 증명하지 못합니다.
버린 길: 첫 20개에서 못 찾으면 라벨 없음으로 보는 현재 방식입니다.
대가: 추가 페이지 조회와 입력 검증이 필요합니다.
되돌리기: 새 조회가 실패하면 종료값 2로 판정을 중단하게 하면 됩니다.

## 2. [높음] 원문 제목: “부분 오류와 잘못된 노드가 정상 판정 또는 다른 종료값으로 빠짐”

- 원인: [scripts/pr-triage.sh:38-41 — 총수와 배열 길이만 검사](/private/tmp/claude-501/-Users-kangsangmo-Desktop-Valuehire-v6/01a97eee-4b0b-44ba-8764-555a8234ab73/scratchpad/v1clone/scripts/pr-triage.sh:38), [scripts/pr-triage.sh:43-69 — 판정 jq의 오류를 종료값 2로 바꾸지 않음](/private/tmp/claude-501/-Users-kangsangmo-Desktop-Valuehire-v6/01a97eee-4b0b-44ba-8764-555a8234ab73/scratchpad/v1clone/scripts/pr-triage.sh:43). GraphQL의 `errors`와 PR 필드의 형식, `labels.nodes`의 배열 여부를 확인하지 않습니다.
- 사업 영향: 부분 실패한 조회에서 초록 댓글이 나갈 수 있고, 형식 오류에서는 명시한 실패 계약이 무너집니다. `labels.nodes:null`이면 결함 라벨을 몰라도 초록으로 분류합니다.
- 반례 원문: `updatedAt` 누락 → `rc=5`, `jq: ... strptime/1 requires string inputs`; `updatedAt:"not-date"` → `rc=5`, `date ... does not match format`; `nodes:[null]` → `rc=5`; `labels:{"nodes":null}` + CLEAN/SUCCESS → `rc=0`, 초록 1건; `errors:[{"message":"partial failure"}]`와 겉보기에 완전한 data → `rc=0`, 초록 1건. 요구값은 형식·조회 실패에서 2입니다.

무엇을: GraphQL 오류 존재, 모든 노드의 필수 필드·타입·날짜·라벨·커밋 구조를 먼저 검증하고 판정 단계 실패를 2로 변환하십시오.
왜: 배열 길이만 맞는 부분 응답은 완전한 정보가 아닙니다.
버린 길: jq의 `//`·`[]?`로 빠진 데이터를 정상값처럼 취급하는 방식입니다.
대가: 조회 형식이 바뀌면 명시적으로 실패해 유지 보수가 필요합니다.
되돌리기: 새 검증으로 오탐이 생기면 해당 필드의 허용 범위만 증거와 함께 조정하십시오.

## 3. [중간] 원문 제목: “실패·충돌이 초안 또는 스택 뒤에 가려짐”

- 원인: [scripts/pr-triage.sh:48-53 — 스택·초안을 실패·충돌보다 먼저 판정](/private/tmp/claude-501/-Users-kangsangmo-Desktop-Valuehire-v6/01a97eee-4b0b-44ba-8764-555a8234ab73/scratchpad/v1clone/scripts/pr-triage.sh:48). [goal AC-5:84 — 실패·충돌을 빨강으로 요구](/private/tmp/claude-501/-Users-kangsangmo-Desktop-Valuehire-v6/01a97eee-4b0b-44ba-8764-555a8234ab73/scratchpad/v1clone/docs/engineering/merge-governance-goal-2026-10-07.md:84)과 [시험:58 — 초안 실패를 노랑으로 기대](/private/tmp/claude-501/-Users-kangsangmo-Desktop-Valuehire-v6/01a97eee-4b0b-44ba-8764-555a8234ab73/scratchpad/v1clone/scripts/acceptance-pr-triage.sh:58)이 서로 다릅니다.
- 사업 영향: 즉시 고쳐야 할 실패를 대기 목록으로 밀어 운영 우선순위를 잘못 잡게 합니다. 사용자 원칙의 “실패를 초록으로 보이지 말 것”은 지키지만 AC-5의 빨강 요구는 지키지 못합니다.
- 반례 원문: `base=task/parent, mergeable=CONFLICTING, mergeStateStatus=DIRTY` → `rc=0`, “스택 PR” 노랑. `isDraft=true, CI=FAILURE` → `rc=0`, “초안(Draft)” 노랑.

무엇을: 빨강과 노랑이 동시에 해당할 때의 우선순위를 goal과 시험에 하나로 정하고 구현하십시오.
왜: 지금은 같은 입력에 대해 요구 문서와 시험이 다른 답을 강제합니다.
버린 길: 현재 시험의 초안 우선을 아무 설명 없이 정본으로 간주하는 방식입니다.
대가: 빨강 수와 운영 알림량이 달라집니다.
되돌리기: 의도적으로 초안 우선을 택한다면 AC-5를 수정하고 그 이유를 기록하십시오.

## 4. [중간] 원문 제목: “대체·중복 5건 중 일부는 실제 대체 근거가 부족함”

- 원인: [goal:121-128 — 서로 다른 대체 판단을 한 묶음에 집계](/private/tmp/claude-501/-Users-kangsangmo-Desktop-Valuehire-v6/01a97eee-4b0b-44ba-8764-555a8234ab73/scratchpad/v1clone/docs/engineering/merge-governance-goal-2026-10-07.md:121). #120과 #121의 현재 head 트리는 GET으로 둘 다 `fff4f91ec2eb6e6dd1a6d4735012bcba488fd36b`로 확인되어 동일 주장은 지지됩니다. #118→#121은 비교 GET에서 `status:ahead, ahead_by:2, behind_by:0`여서 조상 관계 주장도 지지됩니다. 그러나 #121→#123은 별도 리뷰 경로에 대한 **결정 주장**이지 같은 코드·트리로 대체되었다는 증거가 아닙니다. #119→이 goal/스크립트, #108→main도 모든 고유 내용의 대체 여부를 보여 주는 커밋·트리 대조가 없습니다. 특히 [파일 대조표:108 — 5개 변경 파일 모두 main과 동일하지 않음](/private/tmp/claude-501/-Users-kangsangmo-Desktop-Valuehire-v6/01a97eee-4b0b-44ba-8764-555a8234ab73/scratchpad/v1clone/docs/engineering/evidence/merge-governance-20261007/pr-vs-main-file-identity.tsv:14)과 goal의 “고유분 보존 여부만 결정”이라는 문장이 스스로 완료 판정을 유보합니다.
- 사업 영향: 여전히 고유한 내용을 가진 PR을 중복으로 처리해 폐기할 수 있습니다. 5건 전체를 확정된 중복으로 읽으면 과신입니다.

무엇을: #121·#119·#108의 고유 변경을 파일·커밋 단위로 현재 대체물과 대조해 미이관분을 표시하십시오.
왜: 운영 방향 결정과 내용 이관 완료는 다른 주장입니다.
버린 길: 제목이나 결정을 트리 동일성으로 대체하는 방식입니다.
대가: 세 PR의 고유분 수작업 판정이 필요합니다.
되돌리기: 완전 대체 근거가 없으면 “사람 결정”으로 재분류하십시오.

## 5. [낮음] 원문 제목: “문서의 적용·발송 완료로 읽히는 문구가 현재 원격 상태보다 앞섬”

- 원인: [git-workflow.md:31 — 매일 댓글을 남긴다고 현재형 서술](/private/tmp/claude-501/-Users-kangsangmo-Desktop-Valuehire-v6/01a97eee-4b0b-44ba-8764-555a8234ab73/scratchpad/v1clone/docs/sot/git-workflow.md:31). [goal:100 — 아직 실행 안 됨이라고 정확히 표기](/private/tmp/claude-501/-Users-kangsangmo-Desktop-Valuehire-v6/01a97eee-4b0b-44ba-8764-555a8234ab73/scratchpad/v1clone/docs/engineering/merge-governance-goal-2026-10-07.md:100)과 어긋납니다. 원격 workflow GET은 404, `pr-triage` 라벨 이슈 GET은 빈 목록입니다.
- 사업 영향: 운영자가 이미 매일 보고를 받고 있다고 오해할 수 있습니다. 현재는 병합 후 실제 실행 확인이 필요합니다.

무엇을: 기본 브랜치 반영 전·후 상태를 문장으로 구분하십시오.
왜: 정본의 현재형 설명이 실제 운영 상태를 앞섭니다.
버린 길: 미실행 표시를 goal에만 남기는 방식입니다.
대가: 반영 시 문서를 다시 갱신해야 합니다.
되돌리기: 첫 예약 실행과 댓글 확인 후 현재형으로 바꾸십시오.

## 통과한 반증과 인수 기준별 판정

`bash scripts/verify/run-acceptance.sh scripts/acceptance-pr-triage.sh` → 종료값 0, `CHECKED: 25`, `VERDICT: PASS`, runner `OK(... 판정 26건 ...)`. `bash scripts/acceptance-principles-check.sh` → 0, `PASS 34/34`. `bash scripts/verify/check-mechanism-registry.sh` → 0, `CHECKED: 21`이고 `pr-triage-ci` 포함입니다. 따라서 CI 등록과 기본 시험 실행 자체는 확인했습니다. 시험은 위의 누락 필드·부분 오류·라벨 페이지 경계를 증명하지 않습니다.

`mergeStateStatus=UNKNOWN`, `HAS_HOOKS`, `UNSTABLE` 각각 CLEAN/SUCCESS 대신 넣은 fixture → 모두 종료값 0, 초록 0건, “판정 불가” 노랑. `statusCheckRollup:null` → 종료값 0, 초록 0건, “CI 결과 없음” 노랑. `totalCount=0,nodes=[]` → 종료값 0, “열린 PR 0개”와 각 칸 없음. 100개 정확히 → 종료값 0, 100건 출력. `totalCount=101,nodes=100개` → 종료값 2, 잘림 오류. 위 시도는 현재 코드를 **깨뜨리지 못했습니다**. `mergeable=UNKNOWN`과 `mergeStateStatus=CLEAN, CI=SUCCESS`라는 서로 모순된 fixture는 초록 1건이었으나, GitHub가 실제로 이 조합을 반환한다는 증거가 없어 조건부 위험으로만 남깁니다.

- AC-1: 현재 원격 main SHA `55240f77ff52bb240ab1205e46ad2567c7f0b7ae`; #122는 `clean`, head `e58fa879...`, Actions 앱 15368의 `verify` 두 건 모두 `completed/success`. 현재 규칙에 PR·verify·strict가 모두 있어 설정과 후보 상태는 **지지**됩니다. 서버 병합 성공은 미실험입니다. #122의 goal 문서가 S2 두 건과 Windows 미검증을 기록하므로 “기술적으로 통과 가능”과 “제품적으로 승인 완료”는 구별해야 합니다.
- AC-2: 현 규칙의 필수 검사 항목은 확인. #74는 `dirty`, 과거 검사 실패로 확인했습니다. 최신 base의 실패 PR 서버 거절은 저장소 실험 기록만 있고 독립 실행은 미확인입니다.
- AC-3: PR 필수 규칙과 우회자 0을 확인. 직접 push 422는 저장소 실험 기록만 확인했습니다.
- AC-4: `strict_required_status_checks_policy:true`, #85는 `behind`이며 head의 옛 `verify` 두 건은 모두 성공. 옛 초록이 병합 가능으로 보이지 않는다는 부분은 확인했고 실제 서버 405는 미확인입니다.
- AC-5: 기본 fixture는 통과했지만 결함 1~3으로 **실패**입니다.
- AC-6: 현재 ruleset GET에서 `bypass_actors:[]`, `current_user_can_bypass:"never"`; 적용 규칙 GET도 같은 id의 두 규칙입니다. **통과**입니다.

원격 GET 표본 5건의 핵심 원문: #122 `clean/open/draft=false/labels=[]`; #123 `clean/open/draft=false/labels=["needs-fix"]`; #120 `blocked/open/draft=true`; #85 `behind/open/draft=false`; #74 `dirty/open/mergeable=false`. 모두 [after-rule-pr-state.tsv — 당시 상태표](/private/tmp/claude-501/-Users-kangsangmo-Desktop-Valuehire-v6/01a97eee-4b0b-44ba-8764-555a8234ab73/scratchpad/v1clone/docs/engineering/evidence/merge-governance-20261007/after-rule-pr-state.tsv:1)의 해당 행과 일치합니다. 원격 열린 PR 수는 GET 기준 55개입니다. [triage 저장 증거:27-28 — 초록 #122 한 건](/private/tmp/claude-501/-Users-kangsangmo-Desktop-Valuehire-v6/01a97eee-4b0b-44ba-8764-555a8234ab73/scratchpad/v1clone/docs/engineering/evidence/merge-governance-20261007/triage-after-rule-change.md:27)은 현재 표본과 일치하고, 다른 초록 PR은 이 증거에는 없습니다. 55건 전부의 최신 검사 결과를 GET으로 재산출하지 않았으므로 전체 분류 수 21/1/33은 독립 검증이 아닙니다.

변경 전·후 설정 원문 요지: 전 파일은 `required_deployments:[acceptance]`, `bypass_actors:[]`; 후 파일과 현재 GET은 `pull_request(required_approving_review_count:0)`, `required_status_checks(context:"verify",integration_id:15368,strict:true)`, `bypass_actors:[]`. 현재 배포 GET은 0건, 환경 GET은 `acceptance` 한 개입니다. 이 결과는 현재 설정을 입증하며, 과거 배포가 항상 0건이었다는 역사적 주장은 입증하지 않습니다. [verify.yml:8,23 — PR 이벤트와 실제 job 이름 `verify`](/private/tmp/claude-501/-Users-kangsangmo-Desktop-Valuehire-v6/01a97eee-4b0b-44ba-8764-555a8234ab73/scratchpad/v1clone/.github/workflows/verify.yml:8)은 규칙의 검사 이름과 일치합니다. [pr-triage.yml:7-17 — 예약·수동 이벤트와 명시 권한](/private/tmp/claude-501/-Users-kangsangmo-Desktop-Valuehire-v6/01a97eee-4b0b-44ba-8764-555a8234ab73/scratchpad/v1clone/.github/workflows/pr-triage.yml:7), [동 파일:37-50 — `set -euo pipefail`, 판정 뒤 이슈 생성·댓글](/private/tmp/claude-501/-Users-kangsangmo-Desktop-Valuehire-v6/01a97eee-4b0b-44ba-8764-555a8234ab73/scratchpad/v1clone/.github/workflows/pr-triage.yml:37)을 보아 스크립트가 비정상 종료하면 댓글 단계에 도달하지 않습니다. 예약·수동 실행은 기본 브랜치 파일로만 되므로 PR head 코드 실행 경로는 이 정적 검토에서 찾지 못했습니다. concurrency 그룹 하나와 열린 이슈 1건 조회는 동시 실행에 따른 중복 생성을 막지만, 실제 첫 실행은 미확인입니다. 이슈 쓰기 권한은 필요 범위로 보입니다.

검토 종료 상태: HEAD `e09df7a998487393864c500bbb044e31c0a07574`, 기준 `55240f7`, 차이 22파일이며 `git status --short --branch`는 `## task/merge-governance-20261007...origin/task/merge-governance-20261007` 한 줄뿐입니다. 저장소 변경은 없습니다.
