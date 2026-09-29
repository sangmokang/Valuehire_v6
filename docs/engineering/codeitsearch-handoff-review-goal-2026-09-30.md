# codeitsearch 이어받기 검토 goal — 2026-09-30

## 결론 (1층)

다른 PC에서 만든 `feat/codeitsearch-aisearch-module`(PR #113, HEAD 0f83c64)을 이어받아 검토했다.
기존 147개 시험은 전부 통과했지만, 실제 포털 표기로 넣어 보면 **학교 판정 3종·적재 3종·메일 1종**이 틀린다.
이 goal은 그 8건(MAJOR)을 고친다. MINOR는 목록만 남기고 사장님 확인을 받는다.

## 판단 근거 (2층)

- 4차 수정은 3차가 만든 회귀 18건 중 3건만 되살렸다. 전수 생성 비교(67개 표기, b536e30 대 0f83c64)로 15건 잔존 확인.
- 사람인·잡코리아는 학교를 `학교명(지역)`·`대학교(4년)`·`대학(2,3년)` 형식으로 준다. 저장소 수집 기록(`artifacts/`)에서
  `한국외국어대학교(용인)` 343건, `(2,3년)` 107건 실측. 현재 계약은 이 형식을 모른다.
- 적재 쪽 3건은 codex V1 이 모의 DB 로 재현했고 Claude 가 독립 재현했다.

## 인수 기준 (EARS)

| # | EARS 단언 | 검증 명령 |
|---|---|---|
| AC-1 | When 학교명이 3차 이전에 world_top 이던 명문대 하위 기관 표기이면, 시스템은 world_top 을 반환해야 한다 | `pytest ...::TestReview20260930::test_third_round_regressions_the_fourth_round_missed` 15/15 |
| AC-2 | When 학교명이 `Berkeley College`·`Cornell College` 처럼 이름만 겹치는 별개 학교이면, 시스템은 other 를 반환해야 한다 | `test_different_institutions_stay_out_of_world_top` 10/10 + `test_excluding_berkeley_college_keeps_berkeleys_own_colleges` 2/2 |
| AC-3 | When 포털이 분교를 `학교명(지역)` 으로 주면, 시스템은 other 를 반환해야 한다 | `test_portal_parenthesised_branch_campuses_are_not_in_seoul` 16/16 |
| AC-4 | When 학교명·학력에 `(2,3년)`·`초대졸` 표기가 있거나 서울 소재 전문대 이름이면, 시스템은 two_year 로 판정하고 사람인·잡코리아에서 하드제외해야 한다 | `test_seoul_two_year_colleges_are_two_year` 8/8 + `test_portal_two_year_degree_labels_are_hard_excluded` 4/4 |
| AC-5 | If 스냅샷의 회사명·플랫폼이 레지스트리의 company_key 항목과 다르면, 시스템은 행을 만들지 않고 실패해야 한다 | `test_snapshot_that_disagrees_with_the_registry_is_refused` 3/3 |
| AC-6 | When 이전 실행분을 정리할 때, 시스템은 `<prefix>#run-` 표지를 가진 행만 삭제해야 한다(포지션·요약 두 표 모두) | `test_only_rows_carrying_the_run_marker_are_stale`, `test_summary_cleanup_also_requires_the_run_marker` |
| AC-7 | If 검색 대상 공고가 검색어 0개이면, 시스템은 Supabase 를 건드리지 않고 종료값 1 로 멈춰야 한다 | `test_searchable_posting_without_keywords_is_refused` |
| AC-8 | If 후보 0명 보고에 사유가 없으면 거부하고, While 실행 상태가 blocked 이면 "문턱 넘은 후보 없음" 대신 차단을 제목·본문에 밝혀야 한다 | `TestReview20260930` (test_compose_mail) 2/2 |

### counter-AC (가짜 완료)

- 허용어에 지명(`california`, `michigan` 등)을 풀어 AC-1 을 통과시키고 Flint·Merced·Mississauga 를 다시 여는 것 → 기존 `test_satellite_campuses_*`·`test_widening_*` 와 AC-2 목록이 막는다.
- 괄호가 붙은 모든 이름을 other 로 내려 AC-3 을 통과시키는 것 → `test_seoul_campus_qualifiers_stay_in_seoul` 9건이 막는다.
- `대학` 만으로 전문대 판정 → `test_four_year_and_graduate_labels_are_not_hard_excluded` 가 막는다.
- 기존 147개 시험을 고치거나 지워 통과 → 기존 시험 파일은 추가만 한다(삭제·수정 0줄).

## 입출력·오류 계약

- `school_tier(school: str|None, contract) -> Literal[in_seoul, world_top, national, other, two_year]` — 예외 없음.
- `build_rows(snapshot) -> list[row]`; 레지스트리 불일치는 `ValueError`(새로 추가), 모르는 key 는 기존대로 `KeyError`.
- `ingest_positions.main(argv) -> int`; 검색어 없는 검색 대상이 있으면 네트워크 호출 0회, 반환 1.
- `compose(results) -> mail`; 빈 후보 + 사유 없음은 `ValueError`. `results.status` 가 `blocked`/`failed` 면 제목에 `BLOCKED`/`FAILED`.

## 비범위

- CI(`verify.yml`)에 codeitsearch 시험 배선 — 공용 CI 변경이라 사장님 결정 사항으로 올린다.
- MINOR 목록(아래 검증 로그 참조) — 확인 후 처리.
- 운영 Supabase 쓰기·삭제, 사람인 실검색, 메일 발송 — 실행하지 않는다. 배송 상태: `LOCAL_ONLY`(코드·계약 변경, 운영 반영 없음).

## 롤백·영향 반경

- 계약 JSON(`in-seoul-universities.json`, `company-careers-sources.json` 미변경)과 `tools/codeitsearch/` 만 바뀐다. 다른 모듈의 소비자 없음(`rg in-seoul-universities` 로 확인).
- 되돌리기: 이 goal 의 수정 커밋 1개를 `git revert` 하면 0f83c64 동작으로 복귀한다.
- 데이터 안전: 삭제 범위는 좁아지기만 한다(AC-6). 넓어지는 변경 없음.
