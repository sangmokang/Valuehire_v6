# Search 회사·조직 사전조사 정본

## 정상 실행 순서
JD를 읽은 직후 외부 후보자 탐색보다 먼저 회사 식별 → 기존 회사 조사 조회 → 공개정보/현재·과거 재직자 조사 → 조직/인재 패턴 → JD별 검색 가설 → 검색 계획을 만든다. 상위 계약은 [후보 서치](candidate-search.md)다. 증거가 빈약하면 부족함을 명시하고 JD 중심 확장 검색을 하며 회사 조사 완료를 꾸미지 않는다.

## 회사 식별과 조사 범위
회사명·영문명·서비스/브랜드·홈페이지·산업·제품·위치와 JD의 포지션·조직·직무·seniority·기술/경험/도메인을 원문에서 분리한다. 미표기 필드는 unknown이다. 회사 이름만으로 동일 회사를 확정하지 않고 공식 도메인과 서비스/주소/산업 등 추가 근거를 대조한다. 회사 식별이 모호하면 다른 회사 재직자를 섞지 않는다.

공식 Team/About/Leadership·채용 페이지·공개 인터뷰·발표자 소개·GitHub·LinkedIn 공개 프로필 및 공개 검색으로 조사한다. 공식 페이지가 연결한 회사 도메인을 우선한다. 검색 snippet은 발견용 잠정 근거이며 경력/현재재직/보고관계 확정 근거가 아니다. 타인의 게시물에 좋아요/공유한 내용, 추천 프로필 목록, 고객사 협업 프로젝트를 본인의 재직 경력으로 해석하지 않는다. 로그인·CAPTCHA·접근 제한을 우회하지 않는다.

## 저장 단위와 근거
Company, Organization, People, Employment, Evidence, Talent Pattern, Search Hypothesis를 하나의 회사 조사 묶음으로 저장한다. 새 외부 서비스나 병렬 후보 DB는 만들지 않는다. 로컬 immutable snapshot(내용을 바꾸지 않는 시점 사본)을 기존 ignored artifacts에 보존하고, 외부 저장이 승인된 실행만 기존 recruiting_archive.run 경로로 같은 묶음을 아카이브한다. URL·관찰 시각·실제 자료 시점을 유지한다. 수집 시각이 최신이어도 오래된 인터뷰의 현재 재직을 오늘 사실로 바꾸지 않는다.

People 필드: 이름, 직책, 직무, 조직, seniority, 이전 회사/직무, 주요 경력, 학력, 기술/전문영역, 산업 경험, 공개 프로필 URL. 각 값은 Evidence와 확인 수준에 연결한다. Employment는 회사 ID, 사람 ID, current/former/unknown, 재직 기간과 기준 시각을 분리한다. Organization 관계는 confirmed/inferred/unknown으로 분리하며 추정 보고선을 사실로 쓰지 않는다. 빈 값은 허용하지만 임의 보충은 금지한다.

동일인 연결은 안정적인 공개 프로필 URL 또는 직접 연결 근거로만 한다. 이름 일치는 충분하지 않다. 두 출처가 한 사람을 가리킨다는 증거 없이는 별도 관찰로 둔다. URL이 없는 중요한 사실은 확정 패턴과 자동 검색 확장에서 제외하고 보완 대상으로 남긴다. 동일 사실의 변경은 이전 observation을 보존한 새 observation으로 저장한다. 충돌을 최신 값 하나로 조용히 덮어쓰지 않는다.

## 조직과 Talent Pattern
JD 직무 관련 조직·책임자·유사 직무·seniority·이전 회사·산업·기술·협업 관계·최근 합류·퇴사자 이동을 가능한 범위에서 분석한다. 책임자 미확인은 공석을 뜻하지 않는다. 같은 회사 직책만으로 상하관계를 만들지 않는다.

패턴은 참여 사람/재직 관찰 ID·근거 ID·분석 범위·표본 수·확인 가능한 분모·자료 시점을 가진다. 소수 또는 직무 편중 표본은 회사 전체 채용 기준으로 일반화하지 않는다. 확인된 표본 수를 직원 전체 비중으로 바꾸지 않는다. 서로 다른 인물의 반복 근거가 없으면 반복 패턴 대신 단일 관찰로 쓴다. 출신 회사/학력은 관찰 가능하지만 필수조건·점수 가산·탈락 조건으로 변환하지 않는다.

## Search Hypothesis와 평가 연결
포지션별 가설은 다음을 분리한다.
- JD explicit requirements: 원문 필수 요건 및 우대 요건
- observed organization patterns: 확인된 표본의 역할·산업·기술과 한계
- priority discovery: 우선 탐색 직무·실제 경험과 근거
- expansion discovery: 전이 가능한 경험과 검증할 가설
- discrepancy: JD와 관찰의 차이 및 확인 질문
- channel plan: 사람인/잡코리아/LinkedIn/RPS 검색어와 필터 의도

계획에서 실제 화면까지 hypothesis ID, company snapshot hash, JD ID/hash, 계획 query, 적용 query/filters, 관찰 시각, listing 증거를 연결한다. UI에서 지원을 확인하지 않은 연산자는 실제 적용됐다고 말하지 않는다. 불확실한 검색어는 탐색 실험으로 기록한다.

후보 평가 A JD 직접 일치(기존 고정 100점), B 조직 패턴과의 유사성(별도 관찰), C 전이 경험, D 추가 확인을 각각 기록한다. B가 낮거나 unknown이어도 A 또는 추천 gate를 변경하지 않는다. 기존 팀에서 Go가 관찰되면 확장 검색은 가능하나 JD의 Python 필수를 삭제할 수 없다. 새 가설도 후보자 연락 권한을 만들지 않는다.

## 재사용과 최신성
같은 회사는 canonical domain 기반 company key로 먼저 찾는다. 조회 시 as_of와 freshness 기준을 명시하고 오래된 사실/현재 상태/충돌/이번 JD에 필요한 빈칸을 반환한다. 회사 묶음은 재사용하지만 새 JD의 가설은 새로 생성한다. 직무·과거 재직 구간 등 역사적 사실과 현재 재직·조직 책임자 등 변동 사실을 구분한다. 공개 원문이 바뀌면 이전 snapshot을 보존한다.

현재 상태를 확정하는 데 재확인이 필요한 정보가 남으면 표기하고 검색 전략의 강한 제약으로 사용하지 않는다. 공개 직원이 적은 스타트업은 충분한 조직 분모를 알 수 없다는 사실 자체를 저장한다.

## 검증 계약
최소 처음 회사/기존 회사/동명 회사/소표본/현·전 재직 혼합/JD-패턴 차이/다중 출처 동일인/변경 정보/근거·URL 없음/실제 검색 반영을 시험한다. 원문 의미의 사실 검증과 JSON 형식·참조 검증은 별개다. 단위시험 PASS를 라이브 수집·메일·원격 DB 완료로 확대하지 않는다.

반례는 임시 공간에서 원문 저장소를 바꾸지 않고 실행한다. 근거 검증을 no-op으로 바꿨을 때 시험이 실패하는지 확인한다. 기존 회귀시험을 삭제하거나 완화하지 않는다. 모든 실행 증거는 명령·종료값·시각·코드 SHA와 연결한다.

## 완료 보고
이전/새 흐름, 변경 파일, 재사용/신규 기능, 저장 구조, 실제 호출 위치, 정상/반례 시험, 사람 또는 에이전트의 의미 판독 단계, 제한사항을 보고한다. 실제 회사 예시는 JD→회사/현·전 재직자→조직→패턴→가설→실제 로그인 후보 검색까지 연결해야 한다. 일부 채널 차단이나 전역 컨택 미확인을 숨기지 않는다.

## 실행 인터페이스

기존 기록 조회는 후보 서치보다 먼저 실행한다. `--homepage`에는 확인된 회사 공식 홈페이지를 사용한다.

```sh
python3 scripts/company_intelligence.py --load-company \
  --homepage https://example.com --store-dir artifacts/company-intelligence
python3 scripts/company_intelligence.py --input artifacts/RUN/company-input.json \
  --store-dir artifacts/company-intelligence --summary artifacts/RUN/company-summary.json
python3 scripts/recruiting_browser.py search \
  --url https://www.jobkorea.co.kr/corp/person/find \
  --company-snapshot artifacts/company-intelligence/COMPANY/snapshot-HASH.json \
  --query-index 0 --run-id RUN --output artifacts/RUN/jobkorea-q0.json
```

입력은 `run_id`, `jd.source_url/captured_at/company/position`, `company_intelligence.as_of/observations`다. `company.identity_evidence`와 사람·재직 관찰의 `evidence`에는 `url`, `observed_at`이 필요하다. 원문 날짜는 `published_at`, 인용은 `excerpt`, 로컬 캡처는 `capture_path`에 보존한다. `person` 관찰과 `employment` 관찰을 `person_id`로 연결한다. 상세 예제와 경계 입력은 `tests/test_company_intelligence.py`를 참조한다.

`manual_hypothesis.priority/expansion`은 조사자가 해석한 검색어를 담는다. `evidence_urls`로 같은 입력의 JD/회사/사람 근거를 연결해야 한다. URL 존재 검사는 해석의 진실성을 입증하지 않으므로 각 검색어의 JD 또는 조직 근거와 확장 이유를 보고서에서 검토한다. `pattern_hard_filter`와 `organization_match_changes_jd_score`는 true를 허용하지 않는다. 수동 가설도 JD 필수조건을 바꾸지 못한다.

브라우저는 snapshot hash와 ready 상태, 선택 쿼리가 계획 안에 있는지 확인한 뒤 검색한다. 출력의 `company_snapshot`에 JD URL·가설·hash·요청 쿼리를 기록한다. 조건 태그 일치는 검색어 적용 증거일 뿐이다. 전체 인재 수와 같거나 직무 무관 결과가 반복되면 `effective_result_validation`을 유효 검색 성공으로 바꾸지 말고, 원본은 진단 자료로 보존한 뒤 단일 키워드/관찰된 UI 필터로 재검색한다.

`profile --local-only`는 로컬 원문을 보존하고 외부 아카이브를 호출하지 않는다. 재사용 Company Intelligence는 도메인별 불변 JSON snapshot 저장소이며 SQLite/Supabase 이중 저장과 별개다. 실제 후보 원문·평가의 이중 저장은 기존 아카이버의 승인 및 readback 계약을 따른다.
