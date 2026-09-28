# PRD → Task 그래프 → 자동 PR + Observer 경계 — 적용 리서치와 실행 프롬프트 (2026-09-28)

> 등급 L1(계획·분석). 실행 WU는 L2~L3이며 각자 `$strict`로 돈다.
> 읽은 SOT: `docs/sot/strict-workflow.md` · `docs/sot/git-workflow.md` · `docs/sot/verification-commands.md` · `docs/sot/coding-principles.md`
> 참조 진단: `docs/engineering/throughput-architecture-diagnosis-goal-2026-08-27.md`
> 참조 브랜치(미병합): `origin/task/pr37-resolution-codex-20260910`(work-unit-policy.yaml), `origin/task/wu-tdd-context-contract-20260910`(WU manifest)

## 0. 입력 — 외부 글 요지 (사장님 공유 스크린샷)

멀티 에이전트 플랫폼을 PRD → 태스크 → 태스크 간 의존성 → 자동 PR 흐름으로 돌리고, 주요 태스크에서만 사람이 리뷰하게 설계한 경험담.

1. **검증이 병목이 된다** — 작은 변경에도 전체 검증 사이클을 돌리는 건 비용 대비 효용이 낮다. 불필요한 테스트를 지우고 하네스의 검증 루프를 다시 점검하라.
2. **Software Factory는 단순하다** — 태스크에 *의도와 검증 방식*을 담고, *의존성*을 그리고, *사람이 리뷰할 지점*을 붙이는 것이 전부. 핵심은 사람의 인지부하를 얼마나 줄이느냐. 에이전트끼리 끝낼 결정과 사람에게 올릴 결정(Escalation)을 나눈다.
3. **멀티 에이전트의 경계는 사람과 닿는 곳에 긋는다** — 구현/검증 에이전트 역할 분리는 하네스가 이미 잘 한다. 사람은 **Observer 에이전트 하나하고만** 대화하고, Observer가 방향을 잡고 사람의 결정이 필요한 것만 함께 논의한다.

## 1. 우리 저장소 실측 (2026-09-28, 추측 없음)

| 지표 | 8/27 진단 | 오늘 | 출처 |
|---|---|---|---|
| 열린 PR | 12 | **47** (Draft 11) | `list_pull_requests state=open` |
| 가장 오래된 열린 PR | #13 (15일) | #13 (**47일**) | 동일 |
| 마지막 병합 | 8/21 → 8/27 일괄 | **9/10** (#80·#81), 이후 18일 병합 0 | 동일 |
| 원격 `task/` 브랜치 | 91 | **143** | `git branch -r \| grep -c task/` |
| 8/27 AC-1 목표(7일 내 ≤4건) | — | **미달, 4배 악화** | — |

진단 문서의 결론("만드는 게 아니라 들이는 게 병목, 병합 게이트가 오너 1명")은 그대로 유효하고 **더 심해졌다.** 외부 글의 1·2·3이 우리 상황에 정확히 대응한다.

## 2. 글의 3개 주장 ↔ 우리 저장소 대응

### 2-1. "검증이 병목" — 우리는 *기계 검증*보다 *사람 검증*이 병목

- 기계 쪽: CI `verify.yml`은 변경 경로와 무관하게 **26스텝 전량**을 돈다(`verification-commands.md` 표). `hooks/pre-push`는 `scripts/acceptance-*.sh` **글로브 전량**을 재실행한다. 문서 한 줄 수정 PR도 HumanSearch G2 게이트·Invoice PostgreSQL 런타임 게이트까지 돈다. 실측 3.2~4.8분이라 CI 자체는 치명적이지 않지만, **로컬 pre-push 전량 재실행이 동시 세션 16개에서 곱해진다.**
- 사람 쪽(진짜 병목): `git-workflow.md` "자동 병합 금지 — 오너가 diff를 실제로 읽는 것이 P11의 존재 이유". 모든 PR이 같은 무게로 오너에게 온다. **문서 전용 PR과 `hooks/**` 수정 PR의 리뷰 비용이 같다.**
- 적용: 검증을 없애는 게 아니라 **변경 표면 → 필요한 게이트만** 돌리는 라우팅(아래 WU-B). 단, 전량 실행은 `main` push와 야간에 유지(안전망 손실 없음). "불필요한 테스트 삭제"는 이 저장소에서는 비범위 — 진단 문서가 이미 "방어선 자체는 정당"으로 판정했다.

### 2-2. "태스크 = 의도 + 검증 방식 + 의존성 + 리뷰 지점" — 우리는 4개 중 2개만 있다

| 요소 | 우리 저장소 현황 |
|---|---|
| 의도 | ✅ WU manifest `claim` + `acceptance_criterion` (EARS) |
| 검증 방식 | ✅ `regression_commands` · `adversarial_commands` · counter-AC |
| **의존성** | ❌ 없음. PR 제목에 "(#97 스택)"처럼 **사람 손으로 적는다.** HS-02.01 → 02.02 → 02.03, HS-03.01 → 03.02 순서가 어디에도 기계 판독 형태로 없다 |
| **리뷰 지점** | △ `work-unit-policy.yaml`에 `high_risk.paths`가 있지만 **미병합 브랜치에만** 있고, "오너 리뷰 필수 / 에이전트 검증으로 충분" 구분이 아니라 "실행 리뷰 필요" 구분이다 |

게다가 WU 정책·manifest 자체가 `main`에 없다(#37 계열 미병합). **공장의 설계도가 적체 속에 갇혀 있다.**

### 2-3. "사람은 Observer 하나와만 대화" — 우리는 사람이 16개 세션과 직접 대화한다

- 진단 문서 실측: 동시 대화 세션 16개(동시 busy 4). 8/25 main 작업트리 오염이 이 동시성의 결과로 추정됨.
- 사장님이 세션마다 지시·확인·병합 판단을 따로 한다 → 결정이 세션에 흩어지고 PR 47건이 누구의 결정 대기인지 한눈에 안 보인다.
- 이미 있는 재료: #107 "사장님 결정 이력을 ADR로 남긴다"(미병합), `session-status.sh`의 `RED: N/M`. Observer가 이 둘을 자기 입력/출력으로 쓰면 된다.

## 3. 적용안 — 순서가 핵심이다

**반대 가설(가장 유력)**: "적체가 문제인데 또 인프라(그래프·라우터·Observer)를 만들면 PR이 늘어 적체가 더 커진다." → 맞다. 그래서 **WU-0(적체 해소)을 먼저, 새 인프라 PR은 WU-0 성공 신호 이후에만** 연다. Observer는 코드가 아니라 *프롬프트 + 기존 파일*로 먼저 시작한다.

| 순서 | WU | 산출물 | 오너 리뷰 등급 |
|---|---|---|---|
| 0 | 적체 분류·해소 (Observer의 첫 업무) | 47건 분류표 1개 + 병합/폐기/재기반 실행 | 결정만(분류표 승인) |
| A | Observer 운영 프롬프트 고정 | 이 문서 §5 프롬프트 → `.claude/agents/observer.md` | 1회 |
| B | 태스크 그래프 + 리뷰 등급 | `docs/sot/task-graph.yaml` + 검사기 | 필수(SOT·검사기) |
| C | 변경 표면 기반 게이트 라우팅 | `scripts/verify/route-gates.sh` + pre-push 연동 | 필수(`hooks/**`) |
| D | 저위험 등급 자동 병합 | 규칙 개정 ADR 먼저 | **사장님 결정 사항** |

### 오너 결정이 필요한 것 (Observer가 올릴 Escalation 목록의 첫 3건)

1. **`git-workflow.md` "자동 병합 금지" 개정 여부** — 제안: `review_tier: auto`(문서 `docs/engineering/**`만, 실행 파일 0개, CI 초록)는 Observer가 병합, `owner`는 지금처럼 사장님. 이 규칙은 P11의 존재 이유로 명시돼 있으므로 **에이전트가 스스로 바꾸지 않는다.** ADR로 결정받는다.
2. **47건 중 폐기 후보의 폐기 승인** — 브랜치 삭제는 유실 위험(8/27 반대가설 C: 62개 중 44개가 미회수 자산). 폐기 전 회수 확인 필수.
3. **동시 세션 상한** — Observer 1 + 구현 세션 N. N을 몇으로 둘지(제안: 3).

## 4. 태스크 그래프 스키마 초안 (WU-B 입력)

기존 WU manifest를 대체하지 않고 **위에 한 층** 얹는다. WU manifest = 태스크 내부 계약, task-graph = 태스크 간 관계와 사람 개입 지점.

```yaml
# docs/sot/task-graph.yaml (초안)
version: 1
tasks:
  - id: HS-02.01
    prd: humansearch            # 상위 요구사항 묶음
    intent: "열람 증거 계약을 고정한다"
    wu_manifest: docs/engineering/work-units/hs-02-01.yaml   # 의도·검증 방식은 여기가 정본
    depends_on: []
    review_tier: owner          # owner | observer | auto
    review_reason: "SOT 계약 신설"
    pr: 85
    state: in_review            # planned | in_progress | in_review | merged | dropped
  - id: HS-02.02
    depends_on: [HS-02.01]
    review_tier: observer
    pr: 93
```

`review_tier` 판정 규칙(검사기가 강제, 사람이 낮출 수 없음):
- `work-unit-policy.yaml`의 `high_risk.paths`를 건드리면 → 무조건 `owner`
- DB 마이그레이션·외부 효과(P4/P9)·개인정보 경로 → `owner`
- 실행 파일 0개 + `docs/engineering/**`만 → `auto` 후보(§3 결정 1 승인 전까지는 `observer`)
- 그 외 → `observer` (Observer가 V1 적대 검증 판정 본문을 확보한 뒤 오너에게 "읽을 필요 없음" 요약 1줄로 올림)

## 5. 프롬프트

### 5-1. Observer 에이전트 시스템 프롬프트 (WU-A 산출물 원안)

```
너는 Valuehire v6의 Observer다. 사장님은 너하고만 대화한다. 구현·검증·advisor 세션에는
사장님이 직접 개입하지 않는다. 너의 일은 코드를 쓰는 게 아니라 세 가지다.

1) 방향 유지 — 구현이 길어질수록 원래 의도에서 벗어나는지 감시한다.
   기준은 docs/sot/task-graph.yaml의 intent와 각 WU manifest의 AC/counter-AC다.
   구현 세션의 PR diff가 intent 밖 파일을 건드리면 그 세션에 되돌리라고 지시한다.
2) 결정 분류 — 올라온 결정을 둘로 나눈다.
   - 에이전트끼리 끝낼 결정: 구현 방식, 리팩터 범위, 테스트 추가, review_tier가 observer/auto인 병합.
     너가 결정하고 docs/adr/에 한 줄 남긴다. 사장님께 올리지 않는다.
   - 사장님께 올릴 결정(Escalation): review_tier=owner PR의 병합, SOT·원칙(P1~P24) 개정,
     외부 효과(발송·결제·계정), 개인정보 경로, 폐기(브랜치 삭제), 예산·우선순위 변경.
3) 인지부하 절감 — 사장님께는 한 번에 "결정 카드"만 보낸다. 카드 형식:
   [결정 N] 한 줄 질문
   - 배경 3줄 이내 (PR 번호·파일·실측 숫자)
   - 선택지 2~3개, 추천 1개와 이유
   - 안 정하면 무엇이 막히는가 (의존 태스크 ID)
   diff 원문·판정서 전문을 사장님께 붙이지 않는다. 필요하면 링크만.

매 대화 시작 시 반드시 실측한다(추측 금지):
- bash scripts/session-status.sh 의 RED 줄
- 열린 PR 수, 가장 오래된 PR 나이, 마지막 병합일
- task-graph에서 state=in_review 이면서 depends_on이 모두 merged인 태스크(= 지금 병합 가능한 것)
그리고 첫 메시지는 "지금 사장님 결정이 필요한 카드 N장 / 제가 처리한 것 M건" 두 줄로 시작한다.

금지:
- 사장님 승인 없이 git-workflow.md의 자동 병합 금지 규칙을 바꾸거나 우회하지 않는다.
- review_tier를 낮추지 않는다(검사기 판정이 정본).
- 실행하지 않은 검증을 PASS로 적지 않는다(NOT_RUN / BLOCKED 구분).
- 적체가 열린 PR 10건을 넘는 동안에는 새 인프라 PR을 열지 않는다. 적체 해소가 먼저다.
```

### 5-2. WU-0 실행 프롬프트 — 적체 47건 분류 (Observer의 첫 과업)

```
목표 1문장: 열린 PR 47건을 "지금 병합 / 재기반 후 병합 / 합쳐서 재제출 / 폐기(회수 확인 후)"
4개로 분류하고, 사장님 결정이 필요한 것만 결정 카드로 올린다.
성공 신호: 7일 내 열린 PR ≤ 10, 같은 기간 merged 증가 ≥ 20.

절차:
1. PR마다 실측: mergeable 상태, 현재 HEAD의 verify CI 결과(P23: 현재 SHA 귀속),
   추가 줄 중 docs/engineering/** 비율, 실행 파일 수, 건드린 high_risk 경로.
2. 의존 관계 복원: 제목·본문의 "스택", "#NN 선행", HS-xx.yy 번호로 depends_on을 추정하고
   추정임을 표시한다. 이것이 task-graph.yaml의 첫 데이터가 된다.
3. 분류 규칙:
   - 실행 파일 0개 + CI 초록 + 충돌 없음 → "지금 병합" 묶음 (카드 1장으로 일괄 승인 요청)
   - 충돌만 있음 → base 머지로 재기반(리베이스·force-push 금지), CI 초록 확인 후 위 묶음으로
   - 같은 파일(특히 verification-commands.md)을 다투는 PR 여럿 → 하나로 합쳐 재제출 제안
   - 대체된 PR(예: 후속 v2가 전량 포함) → 폐기 후보. 폐기 전 커밋이 다른 브랜치에 포함됐는지
     git branch -r --contains 로 확인한 결과를 카드에 붙인다
   - #99처럼 "병합 대상 아님" 명시 → 분류에서 제외, 보존만
4. 산출물: 분류표 1개(PR 번호·분류·근거 1줄·depends_on). docs/engineering/에 1파일만.
   판정서·프롬프트 왕복 파일을 늘리지 않는다.
counter-AC:
- 새 PR을 닫기만 해서 숫자를 줄이면 실패(merged 증가분으로 확인).
- 폐기한 브랜치의 커밋이 어디에도 남지 않으면 실패.
- stale SHA의 CI 초록을 근거로 "지금 병합" 분류하면 실패.
```

### 5-3. WU-B·C 착수 프롬프트 (WU-0 성공 신호 이후에만)

```
$strict L2. 목표: 태스크 간 의존성과 사람 리뷰 지점을 기계 판독 가능하게 만들고,
변경 표면에 필요한 게이트만 pre-push에서 돌린다.

WU-B1 claim: task-graph.yaml에서 순환 의존·존재하지 않는 선행·잘못 낮춘 review_tier는 거부된다.
  AC: When task-graph.yaml이 검사될 때, the system shall 순환·미존재 depends_on·
      high_risk 경로를 건드리는데 owner가 아닌 태스크가 하나라도 있으면 exit 1.
  counter-AC: A→B→A 순환이 통과한다 / hooks/** 수정 태스크가 review_tier: auto로 통과한다.
WU-B2 claim: PR 본문의 Task ID와 task-graph가 일치하지 않으면 CI가 실패한다.
WU-C1 claim: 변경 파일 목록 → 게이트 집합 매핑이 결정적이고, 매핑에 없는 경로는 전량 실행으로 떨어진다(fail-closed).
  counter-AC: 매핑에 없는 새 디렉터리 변경이 게이트 0개로 통과한다 /
              route-gates.sh 자체를 수정한 PR이 부분 실행으로 통과한다(자기 수정은 전량).
  비범위: CI verify.yml의 main·야간 전량 실행은 그대로 둔다. 검사 삭제 없음.

선행: work-unit-policy.yaml·manifest 검사기(#37 계열)가 main에 먼저 들어와야 한다.
      안 들어와 있으면 BLOCKED로 기록하고 그 병합을 결정 카드로 올린다.
```

## 6. 비범위 / 한계

- 테스트·acceptance 삭제 — 진단 문서가 방어선 유지로 판정. 글의 "불필요한 테스트 삭제"는 게이트 라우팅으로 대체한다.
- Observer를 코드/서비스로 구현 — 먼저 프롬프트 + 기존 파일(`session-status.sh`, `docs/adr/`, task-graph)로 운영해보고 2주 뒤 판단.
- 자동 병합 — §3 결정 1의 ADR 승인 전까지 설계만 한다.
- 47건 분류의 의존 관계는 PR 제목 기반 **추정**이다. WU-0에서 실측으로 확정한다.
