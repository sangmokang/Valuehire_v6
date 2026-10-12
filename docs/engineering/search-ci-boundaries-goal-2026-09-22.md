# Search 경계 오류 수정 목표

## 결론

사람과 조사 시점이 섞이지 않도록 기존 처리의 검증을 강화한다. 실제 채용사이트 검색과 발송은 이번 작업에서 실행하지 않는다.

현재 기준은 eaaee6219ed63d8ed4be1d52a3977216a15e5a03이다. 원 작업공간의 JD 변경은 별도이며 /Users/kangsangmo/Desktop/Valuehire_search_ci_boundaries_20260922의 task/search-ci-boundaries-20260922에서만 수정한다. 사용자 금지에 따라 커밋·원격 전달·외부 DB 쓰기는 실행하지 않는다.

## 계약과 반례

- CI-01: When raw observation ID가 중복되면 입력 오류로 차단한다. 반례: 다른 이름/프로필이 같은 ID로 자동 병합됨. 서로 다른 ID와 동일인 근거를 가진 명시적 병합은 유지한다. 캐시의 완전히 동일한 정규화 관찰 재등장은 중복 저장하지 않는다.
- CI-02: If published_at을 제공하면 날짜·연월·시간대 포함 시각으로 유효해야 한다. 반례: 깨진 날짜가 최신 사실로 통과함. 누락은 허용하며 잘못된 입력은 CompanyIntelligenceError다.
- CI-03: When 과거 as_of로 실행하면 이후 snapshot을 재사용하지 않는다. 입력의 미래 수집/관찰 시각은 거부한다. 반례: 9월 기술이 1월 검색에 유입됨. 과거 snapshot은 삭제·수정하지 않는다.
- CI-04: When 검색 계획을 만들면 JD 제목·기술·요건의 사람이 읽는 문구를 개별 검색어로 보존한다. 반례: Go/commerce가 Python/Backend를 대체함. 조직 신호는 확장 검색으로 유지하며 AND 강제 결합·출신회사 필수조건 변환을 금지한다.
- CI-05: When 실행 증빙을 수집하면 공백 아닌 run_id를 브라우저 호출 전 검사한다. 반례: local-only로 실행 연결을 우회함.
- CI-06: When 표본 수를 보고하면 실제 패턴 생성 자격/기여자와 모수가 구별돼야 한다. 반례: 잠정 인물 1명이 확정 패턴 표본 1명으로 보임.
- 파일 보호: When 원문 JSON을 저장하면 기존 atomic 0600 방식을 재사용한다. 반례: 공개 읽기 권한의 기존 파일을 덮어써도 그대로 0644임.

## 검증과 작업 단위

회사 처리와 브라우저 경계를 독립 작업으로 나눠 실패 시험부터 실행하고 최소 수정 후 회귀한다. 기존 시험은 삭제하지 않으며 모순된 입력 예제만 새 계약에 맞게 수정하고 이유를 기록한다.

검증 명령은 python3 -m unittest tests.test_company_intelligence tests.test_recruiting_browser tests.test_recruiting_archive 및 기존 가상환경에서 PYTHONPATH=humansearch/src python -m pytest humansearch/tests/test_recruiting_review.py다. 기존 변이 시험과 이번 경계별 실패 주입, git diff --check를 실행한다. 설치·실제 외부 수집은 금지한다.

독립 검토는 설치된 Claude의 도구 없는 코드 대조와 새 맥락의 로컬 실행 재현으로 구별한다. 독립 엔진이 직접 실행하지 못한 검증을 실행 PASS로 만들지 않는다. 근거는 artifacts/ci-boundaries에 명령·종료값·시각·파일 지문과 함께 남긴다.

## 범위와 되돌리기

배송 상태 목표는 LOCAL_ONLY(로컬 수정 검증)다. 운영 화면 신설·DB 변경은 없어 SKELETON/마이그레이션은 해당 없다. 외부 브라우저 실증은 사용자 금지로 NOT_RUN이다.

영향은 company_intelligence 입력/검색계획과 recruiting_browser 증빙 파일이다. 기존 회사 snapshot은 변경하지 않는다. 되돌리기는 별도 작업공간의 변경 패치를 역적용하며 원 작업공간과 기존 저장 데이터에는 영향이 없다.

무엇을: 기존 함수의 입력·시간·검색 경계를 수정한다.
왜: 확인된 정합성 결함을 가장 작은 변경으로 닫는다.
버린 길: 새 프레임워크와 대규모 파일 분리는 이번 요청 범위를 벗어난다.
대가: 기존 company_intelligence.py 881줄은 P11의 600줄 한도를 이미 넘으며 이번 최소 수정에서 전체 Strict 합격으로 숨길 수 없다.
되돌리기: 이 작업의 diff만 역적용한다. 데이터 이전은 없다.

## 근거 장부

현재 정본 coding-principles.md, principles.yaml, strict-workflow.md, company-intelligence.md를 읽었다. acceptance-principles-check.sh는 34/34, 종료값 0이다. 이는 원칙 배선 검증이며 제품 전체 합격이 아니다. 상세 결과는 완료 보고서에 연결한다.
