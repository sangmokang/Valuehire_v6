# Search 경계 수정 최종 재검증

## 결론

지적된 여섯 오류는 해결됐다. 같은 범위의 검토를 끝내고 다음 개발의 출발점으로 사용해도 된다. 이번에는 새 코드 결함을 확인하지 않아 코드를 추가 수정하지 않았다.

다만 바로 병합·운영 완료로 처리할 수 있다는 의견은 불완전하다. 다른 계열 모델의 독립 검증, 파일 크기 규칙 처리, 원격 자동 검사는 완료되지 않았다. 실제 후보 검색·메일·운영 저장소 작업도 실행하지 않았다.

## 판단 근거

- 코드 판단: CI-01~CI-06 모두 해결 확인. 이번 좁은 범위에서 추가 수정이 필요한 기능 결함은 발견하지 못했다.
- 아키텍처 판단: 현재 분리 유지. 회사 근거 검증·저장, 브라우저 수집, 평가, 보관의 책임을 재설계할 필요가 없다.
- 진행 판단: 여섯 경계 검증 종료, 로컬 개발 기준선 사용 가능. 전체 병합 전 판정은 REQUEST_CHANGES 유지다. 이는 여섯 버그가 남았다는 뜻이 아니라 파일 크기 규칙과 필수 검증 미완료를 자동 면제하지 않는다는 뜻이다.

HEAD(현재 기준 커밋)는 eaaee6219ed63d8ed4be1d52a3977216a15e5a03, 작업 브랜치는 task/search-ci-boundaries-20260922다. 미커밋 수정본이므로 커밋 번호만으로 시험 대상을 특정하지 않았다. 변경 파일 지문과 실제 변경 내역을 함께 보존했다. 작업 경로는 /Users/kangsangmo/Desktop/Valuehire_search_ci_boundaries_20260922다.

## 여섯 지적의 판정과 반대 증거

수정 전 실패는 이전 원 코드 재현 로그를 검토한 것이며 이번 실행으로 새로 만든 기록이라고 주장하지 않는다. 수정 후와 변이 시험(검증 로직을 일부러 끈 사본)은 이번에 새로 실행했다. S2는 잘못된 검색·평가 근거를 만들 수 있는 중간 결함, S3는 근거의 표본을 과장하는 낮은 결함의 기존 등급이다.

| 항목 | 판정 | 수정 전 실패 경로 | 수정 위치·방어 | 실제 회귀시험과 반대 증거 |
| --- | --- | --- | --- | --- |
| CI-01 / S2 | 해결 확인 | Alice/Bob이 같은 raw ID로 합쳐짐 | scripts/company_intelligence.py:586 `_reject_duplicate_observation_ids`가 입력 중복 거부; :240 `_build_people`가 명시 병합 이름 충돌 보존 | test_duplicate_raw_person_observation_id_is_rejected 통과. distinct ID+동일인 근거 병합 및 동일 캐시 재사용도 통과하므로 정상 병합까지 금지한 수정이 아님 |
| CI-02 / S2 | 해결 확인 | 잘못된 published_at이 날짜 검사 통과 | scripts/company_intelligence.py:700 `_evidence`, :793 `_parse_source_date`, `_source_date`가 유효 형식 요구 | test_invalid_published_at_does_not_bypass_freshness 통과. 정상 연월·날짜·시간대 포함 시각 3형식도 통과 |
| CI-03 / S2 | 해결 확인 | 미래 캐시를 과거 실행에 합침 | scripts/company_intelligence.py:97 `run`, :919 `_merge_cached_observations`가 미래 캐시 제외; :596 미래 관찰 차단 | test_future_cached_snapshot_is_not_merged_into_past_as_of 통과. 과거 캐시 재사용·동일 실행·이전 파일 바이트 보존 통과 |
| CI-04 / S2 | 해결 확인 | Go/commerce가 JD 검색어를 대체 | scripts/company_intelligence.py:532 `_build_channel_plan`이 JD 제목·요건 label·기술을 개별 검색어로 유지 | test_channel_plan_keeps_jd_anchors_when_company_patterns_differ 통과. 4채널 모두 JD 기본어와 확장어 존재; 수동 확장어가 많아도 기본어 유지. 단일 검색어 실행이 전체 검색 완료를 증명하지는 않음 |
| CI-05 / S2 | 해결 확인 | run_id 없이 브라우저 호출·증빙 저장 | scripts/recruiting_browser.py:142 `main`에서 search/profile/snapshot 선검증 | test_search_requires_nonempty_run_id_before_browser 및 profile/local-only, snapshot 차단 시험 통과. 유효 ID 경로도 통과. 독립 JD 캡처는 이 계약의 예외로 유지 |
| CI-06 / S3 | 해결 확인 | 잠정 인물도 표본 1명으로 집계 | scripts/company_intelligence.py:398 `_build_patterns`가 실제 기여자 수 집계 | test_pattern_sample_size_counts_actual_contributors 통과. 잠정·오래된·빈 패턴 인물은 0, 재직 확인 인원은 별도 필드로 유지 |

→ 여섯 회귀시험은 정상 코드에서 성공했고 각 방어를 끈 사본에서는 실제 단언 실패로 끝났다. 단순히 함수가 존재한다는 이유로 해결 판정하지 않았다.

CI-02의 과거 재현 로그에는 잘못된 날짜를 허용한 단언 실패와 시간대 없는 값의 TypeError가 함께 있다. 후자는 freshness 우회 성공의 증거로 계산하지 않았다. 과거 병렬 수정이 섞인 red.log와 URL 충돌로 먼저 실패한 최초 시간 시험도 정식 RED 증거에서 제외한다. 정정된 six-original.json과 개별 로그만 참조한다.

## 저장과 시험의 보존

브라우저는 recruiting_archive.persist를 재사용한다. 고유 임시 파일을 소유자만 읽고 쓸 수 있는 0600 권한으로 만든 뒤 완성된 파일로 교체한다. 기존 0644 출력 덮어쓰기, 정상 JSON 내용, 기존 고정 .tmp 파일을 건드리지 않는 시험이 통과했다. 출력 권한 방어를 제거한 사본은 해당 단언에서 실패했다.

기존 테스트 삭제는 0개다. 새 테스트는 회사 11개, 브라우저 4개, 보관 1개다. 기존 예제의 ID와 과거 시각을 새 계약에 맞췄고, JD의 Python을 무조건 제외하던 예제는 과거 인물만 가진 FormerOnlySkill로 바꿔 제외 단언을 유지했다. 충돌 예제도 PriorConflictSkill로 바꿔 같은 방어를 검사한다. skip/xfail 추가나 단언을 없애서 통과시키는 변경은 확인하지 못했다.

입력→build_snapshot/run→channel_search_plan→recruiting_browser의 resolve_keyword→수집·저장의 연결을 확인했다. 브라우저 시험은 합성 반환값으로 연결과 선차단을 검사한다. 실제 사이트의 검색 결과 관련성은 증명하지 않는다.

## 실행 명령과 결과

모든 아래 명령은 지정된 작업공간에서 이번에 실행했다. 원칙 연결 검사 통과는 모든 제품 원칙 준수의 증명이 아니다.

| 실행 명령 | 종료값 | 결과 |
| --- | --- | --- |
| python3 -m unittest tests.test_company_intelligence tests.test_recruiting_browser tests.test_recruiting_archive | 0 | 68개 통과 |
| PYTHONPATH=humansearch/src /Users/kangsangmo/Desktop/Valuehire_v6/humansearch/.venv/bin/python -m pytest humansearch/tests/test_recruiting_review.py | 0 | 19개 통과, 기존 hypothesis 환경 사용 |
| python3 artifacts/ci-boundaries/targeted-mutations.py | 0 | 여섯 경계+출력 권한 7개 탐지, 각 정상본 0/고장 사본 1 |
| python3 artifacts/ci-boundaries/legacy-mutations.py | 0 | 기존 변이 5개 탐지, 모두 실제 FAIL 단언이며 ERROR 아님 |
| bash scripts/acceptance-principles-check.sh | 0 | 34/34 연결 확인 |
| git diff --check | 0 | 공백 오류 없음 |

→ 회귀 87개와 변이 12개를 새로 확인했다. 변이 사본의 종료값 1은 예상한 방어 실패이고, 이를 확인하는 러너의 종료값 0은 탐지 성공이다. 추가 설치나 외부 운영 데이터 쓰기는 없었다. 보관 단위시험의 임시 SQLite와 로컬 시험 서버는 합성 검증 범위다.

## 파일 크기와 통합 조건

company_intelligence.py는 969줄, 가장 긴 함수 `_build_patterns`는 91줄이다. `_build_employment` 69줄, `_build_people` 68줄이며 함수 100줄 한도는 넘지 않는다. 브라우저 208줄·최장 함수 63줄, 보관 246줄·최장 함수 88줄이다. 회사 모듈에 입력 검증·패턴 생성·저장 책임이 함께 있지만 함수로 나뉘어 있다. 이번 여섯 방어를 닫기 위해 대규모 분리가 필요하다는 근거는 없다.

무엇을: 파일 크기 정리는 이번 기능 검증에서 분리한다.
왜: 사용자가 이번 작업에서 추출을 하지 말라고 명시했고, 여섯 계약은 현재 함수 경계에서 검증됐다.
버린 대안: 600줄을 맞추려고 지금 대규모 재배치하는 방법은 새 변경과 재검증 범위를 늘려 제외했다.
대가: P11의 파일 hard 600 초과는 남으며 후속 정리가 곧 병합 예외 승인을 뜻하지 않는다.
되돌리는 법: 이번에는 추출하지 않아 되돌릴 코드 변경이 없다. 후속 후보는 순수 입력·날짜 검증 함수군의 동작 보존 추출이며, 공유 상수·예외·호출 의존성을 먼저 확인해야 한다.

다른 계열 모델 검토 V1은 이번 NOT_RUN이다. 이전 실제 반환은 Credit balance is too low였으며 현재 계정 상태를 다시 확인하지 않았다. 유효한 V1 결과를 재현하는 V2도 NOT_RUN이다. 같은 모델의 검토로 대체하거나 크레딧 부족을 코드 실패로 계산하지 않는다. 실제 사이트 시험·설치본 반영·원격 CI·독립 인간 검토도 이번 NOT_RUN이다.

## 원 답변의 대조와 더 나은 결론

| 주장 | 판정 | 근거·한계 |
| --- | --- | --- |
| 여섯 결함 수정 및 87개/12개 통과 | 정확 | 현재 소스와 이번 실행으로 재확인 |
| 수정본은 별도 작업공간에 보존 | 정확 | 지정 경로의 현재 branch/status 및 변경 파일 지문 |
| 다섯 번째 쉘 | 미확인 | 사용자의 명칭으로만 취급; 전체 세션 보관 이력 조사 안 함 |
| 광범위한 추가 감사를 그만두자 | 수용 | 이번 범위의 회귀·변이 증거가 닫힘 |
| 통과하면 곧바로 commit→push→PR/CI | 불완전 | 작업 권한, P11 처리, 독립 검증, 테스트 기대값 변경 커밋 정책이 별도로 남음 |

→ 가장 강한 반론은 PR을 열어 원격 검사를 받는 행위와 최종 병합은 다르다는 것이다. 맞다. 따라서 통합 준비는 진행할 수 있지만 이번 로컬 통과만으로 병합·운영 승인을 내리지는 않는다. 로컬 커밋/초안 PR 준비와 실제 게시 권한도 구분한다.

## 요청한 다섯 질문

1. 여섯 항목은 모두 닫혔는가: 이번 명시 계약과 시험 범위에서는 모두 해결 확인이다.
2. 다음 개발 기준선으로 써도 되는가: 가능하다. 미커밋 파일 지문·변경 내역을 포함한 로컬 기준선이다.
3. root/JD 변경이 섞였는가: 아니다. 두 작업공간의 변경 파일 집합은 겹치지 않는다. 원 작업공간의 JD 7개 변경 파일은 가져오거나 수정하지 않았다.
4. 필요한 것은 버그 수정인가, 정리인가: 이번 범위의 추가 버그 수정은 필요하지 않다. 남은 것은 별도 파일 크기 정리와 통합 조건 처리다.
5. commit/push/PR로 넘어가도 되는가: 검토 가능한 커밋 구성·PR 본문 초안 준비는 가능하다. 실제 commit/push/PR는 이번에 실행하지 않았고, 병합 가능 판정도 아니다. 기존 P5/P15에 따라 테스트 기대값 변경의 분리 필요성을 먼저 점검해야 한다.

## 근거 원문과 작업 경계

[실행 시각·명령·종료값](../../artifacts/ci-boundaries/final-revalidation/executions.json), [unittest 원문](../../artifacts/ci-boundaries/final-revalidation/unittest.log), [pytest 원문](../../artifacts/ci-boundaries/final-revalidation/pytest.log), [7개 변이 원문](../../artifacts/ci-boundaries/final-revalidation/targeted-results.json), [5개 변이 원문](../../artifacts/ci-boundaries/final-revalidation/legacy-results.json), [검토한 변경 내역](../../artifacts/ci-boundaries/final-revalidation/reviewed.patch), [변경 파일 지문](../../artifacts/ci-boundaries/final-revalidation/before-hashes.json)을 보존했다. 이는 로컬 기록이며 원격 CI 영수증이 아니다.

기존 변경 7개는 회사 조사 SOT, 세 구현 파일, 대응 세 테스트다. 이 재검증에서는 그 7개 파일의 바이트가 시작과 끝에 동일했다. 이번 새 산출물은 이 보고서와 통합 준비 프롬프트, 로컬 실행 로그다. 과거 수정 보고서와 프롬프트는 당시 기록으로 보존했다.

반복 질문은 제공된 대화의 앞선 여섯 경계 수정 요청과 이번 최종 재검증 요청까지만 확인했다. 전역 순번은 미확인이다. 조용한 실패 검사기 자체의 변경은 이번 범위가 아니므로 별도 검사기 공격 회귀는 해당 없음으로 처리했다.

[다음 실행 프롬프트](search-ci-integration-preparation-prompt-2026-09-22.md)는 통합 준비만 지시한다. 이번 여섯 경계에 대한 광범위한 추가 감사는 종료한다.
