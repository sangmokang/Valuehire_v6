# Jev WU1 최소 마감 판정 (2026-09-28)

## 결론

WU1 기능은 사장님 핵심 규칙 4개를 모두 지키며, 고칠 코드는 없습니다.
main에 올리는 데 필요한 것은 사장님 승인 2개뿐입니다. ① 이 브랜치의 로컬 커밋 25개 push, ② 만료된 검사 예외 2건 처리(기한 연장 권고).
실제 업무 사용 전에는 별도로 ③ 라이브 호출 스위치 켜기, ④ 학교·회사 등급표 실제 값 승인이 필요합니다(병합과 무관한 다음 단계).

## 판단 근거

- 5상태 보존: 가짜 Jev가 다섯 상태를 각각 답하게 해 보니, 결과의 `verdict`가 입력과 모두 같았습니다.
- NOT_STATED: 불합격(`unmet`)이 아니라 "모름"(`unknown`)으로 넘어가며, 점수 기록에서 `unknown_weight`(모름 비중)로 따로 셉니다. 사람 검토 표시는 붙지 않습니다.
  - 한계: `supported_score`(뒷받침 점수)만 보면 NOT_STATED와 CONTRADICTED가 둘 다 0입니다. 차이는 `confirmed_weight`(확인된 비중)에만 나타납니다. 나중에 화면에 띄울 때는 두 칸을 함께 보여 줘야 합니다.
- CONTRADICTED/CONFLICTING: 둘 다 `requires_human_review=true`(사람 검토 필요)로 표시됩니다. CONTRADICTED는 `unmet` "제안"만 만들며, 이 제안을 기존 점수 함수에 넣는 코드는 저장소에 없습니다. 따라서 자동 탈락 경로도 없습니다.
- 기존 점수(`review_candidate`) 불변: `evidence_assessment.py`는 `review_candidate`를 import조차 하지 않습니다(`CriterionStatus` 이름표만 가져옴). 기존 점수 함수를 부르는 곳은 조직 shadow CLI 하나뿐이고, 그 결과를 읽기만 합니다.
- CI 빨간불의 정체: 9/23 CI는 29단계 중 12번째 "억제 만료 스캔"에서 멈췄습니다. 그래서 뒤 17단계는 원격에서 한 번도 돌지 않았습니다. 이번에 로컬 사전 푸시 검사로 인수 검사 28개를 대신 돌려 모두 통과를 확인했습니다. 다만 인수 스크립트가 아닌 CI 인라인 단계(히스토리 스캔·데이터 노출 스캔 등)는 원격 실행 전까지 미확인입니다.
- 병합 잠금: 보호 규칙 조회는 요금제 403이라 읽을 수 없습니다. 그러나 PR 상태가 `BLOCKED`(막힘)가 아니라 `UNSTABLE`(검사 실패)이고, 9/25 main 직접 push가 성공했습니다. ※ 추정: 리뷰 강제는 지금 시행되지 않고 있습니다.

### 결정 카드 — 만료 억제 2건

> **무엇을** — `suppressions.yaml`의 `ci-transfer-guarantee`·`p13-deletion-blindspot` 기한을 2026-10-31로 연장하는 한 줄짜리 PR을 main에 올립니다. 9/30 만료 예정인 `gate-scope-gaps`도 함께 연장합니다.
> **왜** — 두 항목은 CI 무결성의 방어 심도이지 개인정보·인증 결함이 아닙니다. 해제 PR 체인(#74→#75→#77)은 #75가 충돌 상태라 재정렬부터 해야 하는 큰 일이며, WU1과는 무관합니다.
> **버린 길** — (a) 체인 재정렬 후 해제: 이번 목적 대비 과대합니다. (b) 빨간 CI 그대로 병합: "CI 초록 전 완료 없음" 규칙을 어깁니다.
> **대가** — 두 우회 구멍이 한 달 더 열려 있습니다(비밀 게이트 3중은 영향 없음).
> **되돌리기** — 해당 PR revert 한 번으로 되돌아갑니다. 되돌리면 모든 CI가 다시 빨간불이 됩니다.

## 병합 경로 (사람 실행)

1. 억제 연장 PR → main 병합 (main CI 초록 복구)
2. `task/jev-evidence-assessment-wu1-split` 로컬 25커밋 push → #110 갱신
3. #109 병합 → #110 base를 main으로 변경 → CI 초록 확인 → #110 병합
4. 통짜판 `task/jev-evidence-assessment-wu1`(ffdbee9)은 관계없는 검색 작업 위에 얹혀 있고 Gateway 수정이 빠져 있으므로 쓰지 않습니다

## 증거 원문 (2026-09-28 20:0x KST, HEAD e002a1d)

```
$ uv run --frozen pytest -q (WU1 관련 7파일)   → 241 passed, rc=0
$ uv run --frozen pytest -q (humansearch 전체) → 452 passed, rc=0
$ bash ./verify.sh                             → PASS 비밀 스캔, EXIT=0
$ hooks/pre-push 수동 실행                     → 검사 28개 실행, ok 28, EXIT=0, 341초
$ git merge-tree --write-tree origin/main e002a1d → 충돌 없음(rc=0)
```
→ 코드·시험 쪽은 모두 합격입니다. 원격 CI만 억제 만료 때문에 빨간불입니다.

탐침(가짜 Jev, 비중 40):
```
SUPPORTED     proj=met      human=False supported=40 unknown=0  confirmed=40
PARTIAL       proj=partial  human=False supported=20 unknown=0  confirmed=40
NOT_STATED    proj=unknown  human=False supported=0  unknown=40 confirmed=0
CONTRADICTED  proj=unmet    human=True  supported=0  unknown=0  confirmed=40
CONFLICTING   proj=None     human=True  coverage=null
judge=None -> not_run, 투영·점수 없음, 사람 검토 true
합성(미승인) 학교표 -> 투영 없음, 사람 검토 true
contract live_calls_allowed: False
```
→ 다섯 상태가 모두 손실 없이 유지됩니다. 모름과 반대 진술이 서로 다른 칸으로 구분됩니다.

## 확인 못 한 것

- V1(독립 엔진 적대검증): 이번 세션에서는 코드를 바꾸지 않아 새로 돌리지 않았습니다(`NOT_RUN`). 기존 코드는 이전 세션에서 V1을 3차례 받았습니다(인계서 B절).
- CI 인라인 단계(히스토리 blob 스캔·데이터 노출 스캔·셸 문법·패턴 자기오염): 원격 실행 전까지 미확인입니다.
