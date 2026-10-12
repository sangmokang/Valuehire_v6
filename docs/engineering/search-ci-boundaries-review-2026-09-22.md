# Search 여섯 경계 수정 검토

## 결론

지적된 여섯 오류를 고치고 시험으로 확인했다. 다음 개발의 출발점으로 쓸 수 있지만, 전체 규칙 준수와 운영 사용 완료 판정은 보류한다.

독립 검증은 계정 크레딧 부족으로 실행되지 않았다. 기존 회사 조사 파일의 크기 제한 위반도 남았다. 이번에는 실제 채용사이트와 운영 저장소·메일을 조작하지 않았다.

## 판단 근거와 범위

기능 회귀 판정은 PASS, 전체 humanreview 병합 판정은 REQUEST_CHANGES다. 전체 Strict PASS를 주장하지 않는다. 상태는 LOCAL_ONLY(별도 로컬 수정본 검증)이며 원 작업공간과 설치된 전역 Search 실행본에는 이 변경을 병합하지 않았다.

외부 의견은 사실이 아닌 결함 가설로 취급했다. 현재 HEAD(기준 커밋)는 eaaee6219ed63d8ed4be1d52a3977216a15e5a03이다. 외부 포장 파일과 같다고 가정하지 않고 실제 코드·시험·정본을 읽었다. 원 작업공간의 JD 변경은 별도 작업으로 남겼다.

가장 강한 반론은 기존 스킬 절차에서 에이전트가 JD 필터를 보완하고, 관찰 ID를 올바르게 부여하며, 최신 순서로만 실행하면 문제가 드러나지 않는다는 것이다. 그러나 입력 계약은 이 조건을 강제하지 않았고 원 코드의 반례가 이를 입증했다. 절차가 코드 검증을 대신한다는 해석은 채택하지 않았다. 기존 52개 단위시험과 19개 평가 시험은 다시 통과했지만 이번 여섯 오류의 부재를 증명하지 않았다.

아키텍처 유지 의견은 수용했다. 회사 조사 검증·시점 저장, UI 수집, 결정적 JD 평가, 아카이브의 역할을 바꾸지 않았다. 새로운 제품 서비스·DB·프레임워크는 추가하지 않았다.

**무엇을** — 기존 함수의 ID·날짜·시점·검색·실행 증빙·표본 수 검증을 보강한다.
**왜** — 확인된 오류가 다른 사람의 경력 혼합과 검색 근거 왜곡을 만들기 때문이다.
**버린 길** — 전면 재설계와 별도 저장 시스템은 원인을 직접 줄이지 않아 제외했다.
**대가** — 같은 관찰 ID를 다른 내용으로 재사용하던 입력은 실패하며 기존 크기 한도 초과는 남는다.
**되돌리기** — 이 작업의 diff(기준 코드와의 변경 내역)만 역적용한다. 기존 저장 자료는 갱신하거나 삭제하지 않았다.

사용자의 명시적 수정 요청에 따라 읽기 전용 감사 뒤 구현까지 수행했다. 커밋·메일·후보 연락·라이브 채용사이트·운영 DB 쓰기는 금지 범위로 유지했다. 임시 SQLite와 127.0.0.1 시험 서버는 사용자가 지정한 기존 아카이브 단위시험의 합성 환경이다.

과거 메일 및 후보 검색 결과는 이번에 외부 서비스를 조회하지 않아 당시 보고서 이상의 사실로 확인하지 않았다. 질문 반복 횟수는 이번 결정에 필요하지 않아 보관 세션 전수 검색을 하지 않았으며 전역 횟수를 주장하지 않는다.

최초 혼합 실행 red.log는 병렬 수정이 섞여 정식 수정 전 증거로 쓰지 않는다. 최초 미래 캐시 시험도 안정 프로필 URL 충돌로 멈춰 시간 역행의 올바른 실패 증거가 아니었다. URL을 분리한 예제로 원 HEAD에서 다시 실행한 six-original.json과 개별 CI 로그를 사용했다.

## 여섯 지적의 수정 전후

RED→GREEN은 정상 기대를 단언한 시험이 기존 코드에서는 실패하고 수정본에서는 통과했다는 뜻이다. 심각도 S2는 검색·평가 근거가 잘못될 수 있는 중간 결함, S3는 표본 보고가 과장되는 낮은 결함으로 유지한다.

| 항목 | 최종 상태 | 수정 전 재현 | 수정 위치와 동작 | 수정 후 |
| --- | --- | --- | --- | --- |
| CI-01 / S2 | 해결 확인 | 다른 이름·URL의 같은 ID가 오류 없이 병합 | scripts/company_intelligence.py:586 중복 관찰 ID 거부, :240 명시 병합 이름 충돌 보존, :919 동일 캐시 관찰만 중복 제거 | 중복 거부, 서로 다른 ID와 동일인 근거의 병합 유지 |
| CI-02 / S2 | 해결 확인 | not-a-date가 거부되지 않음; 시간대 없는 시각은 기존 구현에서 TypeError도 발생 | scripts/company_intelligence.py:700 제공된 날짜 검증, :793 날짜·연월·시간대 포함 시각 파싱 | 잘못된 날짜·빈 값·null·시간대 없는 값 거부, 정상 3형식 유지 |
| CI-03 / S2 | 해결 확인 | 9월 캐시를 1월 실행에서 previous_snapshot_count=1로 사용 | scripts/company_intelligence.py:97, :919 미래 캐시 제외, :596 미래 수집·관찰 시각 거부 | 미래 사람·기술 제외, 정상 캐시 재사용·반복 실행·이전 파일 바이트 보존 |
| CI-04 / S2 | 해결 확인 | Backend/Python JD에서 commerce와 Go만 생성 | scripts/company_intelligence.py:532 제목·요건 label·기술을 개별 기본 검색어로 보존 | 4개 채널에 Backend Engineer/Python/large traffic 및 Go/commerce 유지 |
| CI-05 / S2 | 해결 확인 | run_id 없이 실제 수집 호출 경로 진입 | scripts/recruiting_browser.py:142 CLI의 search/profile/snapshot 입력 선검증 | 공백·누락 시 브라우저 전 실패, local-only에도 적용 |
| CI-06 / S3 | 해결 확인 | tentative 인물+confirmed 재직의 표본이 1 | scripts/company_intelligence.py:398 실제 패턴 기여자만 표본 수로 계산 | 잠정·오래된 인물·패턴 값 없는 인물의 기여 표본 0 |

→ 모든 지적은 현재 코드의 실제 결함으로 확인됐다. 여섯 항목의 수정 전 시험은 종료값 1, 수정본의 해당 시험은 0이다. 종료값은 프로그램 실행 결과이며 0은 성공, 1은 여기서 기대 단언 실패다. 원본 재현의 CI-02에는 잘못된 날짜를 허용하는 단언 실패와 시간대 없는 값의 기존 오류가 함께 있으며, 후자를 날짜 우회 성공 증거로 혼동하지 않는다.

## 저장 보호와 기존 시험 보존

브라우저 출력 경로는 임의의 --output을 허용하고 상위 디렉터리 권한을 보장하지 않았다. 기존 0644(다른 사용자 읽기 가능) 파일 덮어쓰기에서 0600(소유자만 읽고 쓰기)로 바뀌지 않는 반례를 재현했다. recruiting_browser.persist_output은 기존 recruiting_archive.persist를 재사용한다. archive.persist와 동일 구현이 있던 company_intelligence._persist는 같은 폴더의 고유 임시 파일을 0600으로 만든 뒤 원자적으로 교체한다. 이전의 고정 .tmp 이름에 남은 권한이나 심볼릭 링크를 따라 쓰지 않는다. DB 처리 계약은 변경하지 않았다.

기존 시험을 삭제하거나 skip/xfail로 건너뛰지 않았다. 기존 ID 중복 예제에는 별도 관찰 ID를 부여했고, 과거 as_of 예제의 수집 시각도 과거로 맞췄다. Python은 JD 기본 검색어여서 무조건 제외할 수 없으므로, 과거 재직자는 FormerOnlySkill, 충돌 필드는 PriorConflictSkill로 바꿔 동일한 제외 단언을 유지했다. tentative Rust 제외 단언도 추가했다. 새 시간 시험과 캐시 시험은 반복 입력 구성을 줄였으며 모든 핵심 단언을 유지했다.

실제 호출 연결은 company_intelligence.main → run/build_snapshot → channel_search_plan → recruiting_browser.main → load_company_plan/resolve_keyword → Aside 호출과 출력 저장이다. 시험에서는 Aside 경계에 합성 반환값을 넣어 호출 전 차단과 출력 연결을 검증했다. 실제 로그인 사이트가 검색어를 받아 관련 후보를 반환하는지까지 입증한 것은 아니다.

## 실행 증거

| 실행 명령 | 종료값 | 현재 확인 범위 |
| --- | --- | --- |
| python3 -m unittest tests.test_company_intelligence tests.test_recruiting_browser tests.test_recruiting_archive | 0 | 68개, 회사 41 + 브라우저 13 + 아카이브 14 |
| PYTHONPATH=humansearch/src /Users/kangsangmo/Desktop/Valuehire_v6/humansearch/.venv/bin/python -m pytest humansearch/tests/test_recruiting_review.py | 0 | 기존 환경의 pytest 19개, hypothesis 6.165.10 사용, 설치 없음 |
| python3 artifacts/ci-boundaries/targeted-mutations.py | 0 | 여섯 경계+출력 권한 변이 7개, 정상본 0/고장 사본 1, 단언 실패 확인 |
| python3 artifacts/ci-boundaries/legacy-mutations.py | 0 | 기존 5개 변이 재실행, 해시·직무·오래된 정보·상태 충돌·출신회사 검색 차단 |
| python3 -m py_compile scripts/company_intelligence.py scripts/recruiting_browser.py scripts/recruiting_archive.py | 0 | Python 구문 검사 |
| bash scripts/acceptance-principles-check.sh | 0 | 원칙 연결 34/34, 제품 전체 준수 판정 아님 |
| git diff --check | 0 | 변경 내용 공백 오류 없음 |
| 직접 작성 파일/함수 크기 검사 | 1 | company_intelligence.py 969/600줄로 초과; 해당 시험 파일 599줄, 함수 100줄 초과 없음 |
| Claude 독립 V1 실행 | 1 | Credit balance is too low, 검토 응답 없음 |

→ 자동 회귀 87개와 고장 사본 12개를 확인했다. 자동 시험과 독립 엔진 검증은 별개다. Claude 결과는 BLOCKED이며, 유효한 V1 판정이 없어 그 판정을 재현하는 V2도 NOT_RUN이다. 이 둘을 같은 계열 하위 에이전트의 완료 문구로 대체하지 않았다. 독립 인간 검토도 NOT_RUN이며 이번 로컬 수정에서는 별도 필수 승인으로 추가하지 않았다.

원문 로그는 [최종 실행 장부](../../artifacts/ci-boundaries/final-executions.json), [단위시험](../../artifacts/ci-boundaries/final-unittest.log), [평가 시험](../../artifacts/ci-boundaries/review-pytest.log), [원 코드 재현](../../artifacts/ci-boundaries/six-original.json), [신규 변이](../../artifacts/ci-boundaries/targeted-mutations.json), [기존 변이](../../artifacts/ci-boundaries/legacy-mutations/final-mutations-summary.json), [Claude 실제 반환](../../artifacts/ci-boundaries/parent-claude-v1.json)에 있다. 임시 재현 소스도 original-reproduction 폴더에 복사해 남겼다. 문서의 코드 위치는 처리 책임을 가리키며 로그의 입력·출력과 함께 읽어야 한다.

## 변경 파일과 작업 경계

수정 파일은 scripts/company_intelligence.py, scripts/recruiting_browser.py, scripts/recruiting_archive.py, 대응 tests/test_*.py 세 개, docs/sot/company-intelligence.md다. 새 문서는 이 보고서, 같은 날짜 goal, 다음 실행 프롬프트 세 개다. 새 제품 서비스·DB·검사기·ledger는 추가하지 않았다. artifacts의 변이 실행 파일은 이번 검증용이며 제품 경로에 설치하지 않았다.

작업 branch는 task/search-ci-boundaries-20260922이고 HEAD는 eaaee6219ed63d8ed4be1d52a3977216a15e5a03이다. 변경은 미커밋이므로 HEAD만으로 수정본을 식별하지 않는다. [코드 지문](../../artifacts/ci-boundaries/code-manifest.json)과 changes.patch를 함께 보존한다. 실제 보존 경로는 /Users/kangsangmo/Desktop/Valuehire_search_ci_boundaries_20260922이다. 이전 /tmp 경로는 검증 당시의 작업 위치이며 보존 완료 후 이동했다.

## 다음 단계 판단

1. 이 여섯 오류를 닫은 로컬 개발 기준선으로 사용할 수 있다. 전체 Strict 합격이나 병합·배포 준비 완료 기준선으로는 아직 사용할 수 없다. 기존 881줄이던 회사 조사 파일은 969줄이며 600줄 제한 초과를 해결하지 않았다. 이를 숨기거나 임의 예외로 만들지 않았다.
2. 운영에는 공개정보의 의미·동일인 근거를 사람이/에이전트가 확인하는 작업, 실제 사이트 UI와 접근 권한, 검색 결과의 직무 적합성, RPS 범위, 과거 컨택 이력, 양쪽 저장 및 화면 증빙 readback이 남는다. 이번 입력 검증은 공개 프로필의 진실성을 보증하지 않는다. JD 기본어를 계획에 남겼다고 전체 검색식을 모두 실행한 것도 아니다. 새 계획의 query-index는 재확인해야 한다.
3. 무관한 JD 변경은 이번 diff에 포함되지 않았다. 원 작업공간의 기존 JD 파일은 수정·복원·커밋하지 않았다. 전역 설치본도 갱신하지 않아 실제 실행에 반영하려면 별도 변경 반영 단계가 필요하다.

[다음 실행 프롬프트](search-ci-next-execution-prompt-2026-09-22.md)는 이번 여섯 경계와 증거만 재검토하도록 범위를 고정한다. 독립 검증 가능 여부와 크기 제한 문제는 별도로 표시하며, 운영 검색·메일 권한을 재사용하도록 지시하지 않는다.

문서 형식 검사 brief-lint는 세 문서 합계 위반 0건이다. 이는 형식 검사이며 기능·운영 합격 근거가 아니다. 상세 출력은 artifacts/ci-boundaries/brief-lint-final.log에 보존했다.
