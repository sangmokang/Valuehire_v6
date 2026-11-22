# Valuehire v6 AI Search Operations v1
## PRD · 데이터/업무 계약 · 화면 명세 · WU 실행계획

- 문서 ID: `VH6-AISO-SOT-001`
- 버전: `1.0.0-draft-for-baseline`
- 작성 기준일: `2026-09-30`, 시간대 `Asia/Seoul`
- 제품 책임자: 강상모 / Value Connect
- 대상 경로: `https://admin.valuehire.cc/ai-search-list`
- 개발 대상: **Valuehire_v6**. v4/v5는 인수·대조 대상이지 신규 기능 개발 대상이 아니다.
- 문서 상태: **사용자 요구를 반영한 SOT 등록안 / 현재 저장소·물리 DB 매핑 검증 전**
- 실행 상태: **구현·운영 마이그레이션·배포·실제 후보자 발송을 수행하지 않았다.**
- 권장 등록 위치: `docs/sot/ai-search-operations.md`. 실제 저장소의 SOT 규약이 다르면 WU-00에서 위치를 확정한다.

> 이 기능은 “AI가 찾은 사람을 나열하는 페이지”가 아니다. AI가 만든 검토 업무를 팀이 실제 제안·후보자 확보로 전환하는 과정을, 증거 있는 기록으로 관리하는 운영 화면이다. 기술 실행 완료, 내부 보고메일 발송, 후보자 실제 제안 발송, 고객사 추천은 서로 다른 사건이다.

---

## 0. 문서의 권한과 사실 판정

### 0.1 이 문서가 고정하는 것

사용자 경험, 기록 단위, 발송 판정, 업무량 집계, 주간 경계, 중복 처리, 완료 조건은 이 문서의 제품 계약이다. 저장소에 등록된 뒤 변경하려면 변경 이유·영향받는 규칙 ID·회귀시험을 함께 기록한다.

그러나 실제 테이블명·배포 SHA·스케줄러·SDK·포털 API를 확인한 것처럼 만들지 않는다. WU-00/01에서 코드·스키마 근거와 매핑을 채우고, 그 뒤에 DDL을 확정한다. `CREATE TABLE IF NOT EXISTS`로 기존 스키마 충돌을 감추는 방식은 금지한다.

우선순위는 사용자 최신 명시 요구 → 저장소의 안전·승인 경계 → 승인된 본 계약 → 실행 WU → 임시 채팅 순이다. 본 문서와 기존 SOT가 충돌하면 충돌하는 범위만 차단하고 관련 없는 로컬 작업은 계속할 수 있다. 과거 다른 작업의 브랜치 SHA·배포 승인을 이 작업에 재사용하지 않는다.

### 0.2 현재까지 확인한 근거와 한계

**SRC-U1: 사용자 제공 화면 3장, 2026-09-30.** AI Search 표, ClickUp 집계, Fleet-job 화면이 별도 탭으로 존재한다. 후보 요약의 행 높이가 크게 달라지고, 최신 500개 표시 제한, 미분석 0점, 근거 공란 상태의 점수, 취소와 실패의 혼합 표시, 월요일 시작 주간 그래프가 보인다. 화면 숫자는 화면에 표시된 값일 뿐, 정합성이 검증된 DB 사실로 취급하지 않는다.

**SRC-L1: `붙여넣은 마크다운(1)(20260929-171945).md`의 기존 작업 기록.** 기존 평가 함수 `review_candidate` 보존, SQLite·Supabase 저장 후 필드 대조, 별도 worktree·검증·승인 경계 등의 지시가 확인된다. 이 기록은 현재 checkout 및 운영 배포를 직접 검증한 결과가 아니다.

**SRC-L2: 같은 기록의 위클리 감사 부분.** v4의 `weekly_brief_snapshot`과 v6의 `contracts/admin-weekly-dashboard/metric-contract-v1.json`, `source-contract-v1.json`이 언급된다. 월요일/일요일 경계와 FY 주차 라벨 충돌이 기록돼 있다. 기존 집계 함수가 있는지 먼저 확인할 이유이지, 새 집계 함수를 무조건 만들어야 한다는 근거가 아니다.

**SRC-L3: 같은 기록의 2026-09-28 내부 브리핑 규칙.** 제목 접두사 `[aisearch]claudecode` / `[aisearch]codex`, Gmail `aisearch` 자동 분류가 기록돼 있다. 더 오래된 “aisearch 라벨이 없다”는 진단을 최신 사실처럼 반복하지 않는다. 계정·권한별 현재 상태는 다시 확인한다.

**SRC-M1: Gmail에서 직접 읽은 최근 내부 보고메일.** 제목 `[aisearch]claudecode [집중 서치 2차] 코드잇 부트캠프 교육 운영 유닛 리드 — RPS 추천 6·조건부 4`, message ID `1a0edb6857bb3ab3`. 발신·수신이 본인 계정이며 본문에 후보자에게 연락하지 않았다고 명시돼 있다. 내부 보고 발송과 후보자 제안을 분리해야 하는 실제 사례다. 본 문서는 그 메일의 후보자 개인정보를 복제하지 않는다.

**미확인:** 현행 v6 HEAD와 배포 대상 브랜치, 실제 관리자 경로의 서버 코드, 운영 Supabase 전체 스키마/RLS, SQLite별 쓰기 주체, 세 포털 발송이력 수집 범위, 연결 가능한 계정 수. 대상 웹페이지는 이번 작성 환경에서 본문을 직접 읽지 못했다. 이것을 서비스 장애의 증거로 해석하지 않는다.

### 0.3 SOT 산출물의 관계

- 본 Markdown: 제품 목적·규칙·UX·인수조건의 정본.
- `contracts/ai-search-operations/v1.json`: WU-01에서 만드는 실행 가능한 타입·상태·지표 계약. 본 문서의 규칙 ID를 참조하며 임의의 별도 규칙을 갖지 않는다.
- WU 카드와 테스트: 위 두 계약을 구현·검증한다. 구현에 맞추려고 기대값을 낮추지 않는다.
- 매핑표: 논리 엔터티 → 실제 테이블/뷰/컬럼/함수/파일:줄/권한을 기록한다. 기존 객체 재사용을 기본값으로 한다.

변경 시 문서·기계 계약·테스트를 같은 WU에서 정합하게 수정한다. 문서와 JSON 중 어느 것이든 불일치하면 계약 검사 실패다.

---

## 1. 제품 목표와 완료의 의미

### 1.1 해결할 질문

1. AI가 누구를 어느 포지션으로 언제 찾았고, 어떤 자료로 판단했는가?
2. 강상모 계정의 사람인·잡코리아·LinkedIn에서 실제 제안이 확인되는가? 다른 팀원의 활동은 어디까지 관측되는가?
3. 검토할 일, 제안할 일, 발송 여부를 확인할 일이 각각 얼마나 남았는가?
4. 이번 주 팀이 처리한 업무량과 실제 발송·응답·이력서 확보는 얼마인가?
5. 기록 누락·동기화 장애·연락 이력 미확인 때문에 숫자를 믿을 수 없는 부분은 어디인가?

### 1.2 제품 성공 조건

- 새 AI Search 결과가 구조화 DB에 먼저 남고, 동일한 저장 결과에서 웹 표시와 내부 보고메일이 생성된다.
- 사람인·잡코리아·LinkedIn 발송은 각각 증거와 관측 범위를 보여 준다. 확인되지 않은 채널은 초록색 완료로 위장하지 않는다.
- 전체 DB를 대상으로 검색한다. 화면에 먼저 불러온 500개만 검색하지 않는다.
- 재검색·재시도·메일 재수집이 후보자 수, 업무량, 발송 수를 부풀리지 않는다.
- 카드·상세·그래프·위클리가 같은 정의와 같은 스냅샷을 사용한다.
- 후보자 표는 짧고 읽기 쉽고, 근거·원문·전체 이력은 상세 패널에서 확인한다.
- 이관 이후에도 기존 기록을 보존하며, 증빙 없는 과거 기록을 신규 실적으로 바꾸지 않는다.

### 1.3 범위

**v1 필수:** 구조화 결과 수집, 기존 DB 재사용, SQLite 내구성 있는 임시 저장/재전송, Supabase 웹 정본, 내부 보고메일 유지, 세 채널 이력 추적, 간결한 표·상세·전역 검색, 검토/제안대기/보류/제외 처리, 주간 유입·처리·백로그·실발송, 출처별 최신성·완전성 표시, 과거 자료의 통제된 편입.

**후속 확장:** 관심 응답 → 이력서 확보 → 고객사 추천 → 면접 → 성사 연결. 기존 ATS/Gmail/ClickUp의 증거를 재사용하며, 신규 회계·매출예측 시스템을 이 작업에서 만들지 않는다.

**비범위:** 후보자 자동 대량 발송, 포털 로그인 우회, CAPTCHA 회피, 새 브라우저 자동화 프레임워크, Jev/평가모델 교체, 기존 점수 가중치 변경, 새 ATS·CRM, 전면 디자인시스템 교체, Elasticsearch/벡터DB/Kafka 등 신규 인프라.

기존에 승인돼 운영 중인 내부 보고메일 경로는 보존하되, 개발 테스트가 실메일을 보내서는 안 된다. 이 문서 자체는 외부 발송이나 운영 DB 쓰기 승인이 아니다.

---

## 2. 핵심 규칙 — 구현자가 바꾸면 안 되는 것

- **R-01 구분:** `AI 결과 생성 ≠ 내부 보고 발송 ≠ 후보자 제안 ≠ 고객사 추천 ≠ 채용 성사`.
- **R-02 정본:** 승인·반영된 운영 기록과 웹/위클리 집계의 정본은 Supabase/Postgres다. SQLite는 로컬 원장·아웃박스·캐시이며 독립적인 두 번째 운영 정본이 아니다. 기존 승인 SOT와 충돌하면 이 관계를 먼저 조정한다.
- **R-03 저장 우선:** 결과 저장과 보고 발송 예약을 내구성 있게 처리한 다음 부수효과를 수행한다. 메일 성공을 결과 저장 성공으로 대신하지 않는다.
- **R-04 불명 보존:** 자료 없음은 `null/unknown`이다. 미분석은 0점이 아니며, 이력 조회 실패는 미발송이 아니다.
- **R-05 증거 기반:** 외부 제안의 확인 상태를 LLM 설명, 버튼 클릭, 내부 메일, ClickUp 완료, 잔여 크레딧 변화만으로 정하지 않는다.
- **R-06 세 가지 단위:** 사람 수, 후보자×포지션 업무 수, 실제 제안 메시지-수신자 수를 분리한다.
- **R-07 재실행 안전:** 같은 입력·원천 사건 재수집은 같은 정체성을 유지한다. 새로운 실행 시각을 중복방지 키에 넣어 재시도를 신규 데이터로 만들지 않는다.
- **R-08 이력:** 재평가·수정·제외·재개·발송 검증 취소의 이력을 보존한다. 최신 화면을 바꿔도 과거 회의 자료를 몰래 덮어쓰지 않는다.
- **R-09 주간:** KST 일요일 00:00 이상, 다음 일요일 00:00 미만. 집계 사건의 실제 발생시각을 사용한다.
- **R-10 보안:** 기존 인증·권한 경계를 유지한다. UI뿐 아니라 API·RPC·뷰·증빙 파일 접근에도 적용한다.
- **R-11 인수:** v4/v5의 화면 동작과 데이터는 필요한 부분만 이관한다. 구형 전체 코드를 v6에 복사하지 않는다.
- **R-12 점수:** 현재 승인된 평가 함수를 유지한다. 요약 표시 개선이 점수 재설계로 번지지 않게 한다.
- **R-13 범위 완전성:** 실제로 관측한 계정·기간·페이지·채널을 기록한다. 부분 수집을 전체 완료라고 부르지 않는다.
- **R-14 업무와 시스템:** 사용자 검토/발송과 시스템의 중복정리/포지션 종료를 같은 생산성 실적으로 세지 않는다.
- **R-15 업무 유입:** 레거시를 읽어왔다는 이유만으로 전부 오늘의 처리대기 업무로 만들지 않는다.
- **R-16 규모 통제:** 한 번에 한 원자 WU만 구현한다. 새 기능과 무관한 전역 정리를 끼워 넣지 않는다.

---

## 3. 화면 명세

### 3.1 정보 구조

대상 URL은 유지한다. 화면의 중심을 `AI Search 운영`으로 바꾼다.

- 기본 뷰: **처리할 후보**. 사람의 다음 행동이 필요한 업무만 표시.
- 보조 뷰: **전체 서치 기록**. 과거·미분석·부분 결과·보관 자료 포함.
- 보조 뷰: **주간 성과**. 주간 유입·처리·실제 발송·백로그.
- 진단 뷰: **실행·동기화 상태**. 기존 Fleet-job과 ClickUp 원천 상태를 운영 진단으로 이동. 삭제하지 않는다.

이것은 별도 시스템 4개가 아니라 같은 페이지의 뷰다. 기존 `ClickUp 시각화`는 원천 관측 화면으로 남길 수 있지만, ClickUp task 수를 새 화면의 고유 후보 수로 그대로 대체하지 않는다. 기존 후보자 표의 **칸반 컬럼은 제거**한다. 다른 메뉴의 Kanban 기능은 이 작업에서 삭제하지 않는다.

### 3.2 상단

상단에 기간, 담당자, 포지션, 원천, 제안 채널, 업무 상태, 증거 상태, 점수 범위 필터를 둔다. 기본 담당 범위는 강상모 계정이며, 실제 계정 ID를 확인해 연결한다. 표시 이름 문자열로 소유자를 판정하지 않는다.

수치 카드의 권장 순서:

`신규 업무 | 검토 처리 | 실제 제안 | 남은 업무 | 7일 초과 대기`

카드의 단위를 바로 표기한다. 예를 들어 실제 제안 카드에는 `제안 12건 · 10명 · 11매칭`처럼 서로 다른 단위를 명시한다. 수치는 예시일 뿐 시드 데이터나 실제 실적이 아니다. 클릭하면 동일한 필터·집계 스냅샷의 증빙 목록을 연다.

현재 주는 `진행 중` 배지, 마감한 주는 `스냅샷 버전`을 표시한다. `페이지 조회시각`, `원천별 최종 성공 수집`, `중앙 반영시각`을 구분한다.

### 3.3 후보자 표 — 고정 7컬럼

1. **후보자**: 이름, 현직 회사/직함 한 줄, 원본 프로필 링크. 이름이 없으면 원천 ID로 표시하고 실명을 만들어내지 않는다.
2. **서치 일시**: 최근 관측 시각 `MM.DD HH:mm KST`. 작은 보조문구로 최초 관측·재검색 횟수를 제공한다. 현재 범위의 관측과 이관 시각은 분리한다.
3. **제안 발송**: 대표 상태와 채널 배지. `확인됨`, `검증 대기`, `미발송(관측범위)`, `확인 불가`를 분리한다. 확인됨에는 실제 발송시각·발신자·증빙 진입점을 붙인다.
4. **프로필 요약**: 최대 3줄. `학력 1줄 / 현·직전 핵심 경력 1줄 / 관련 경력 기간 1줄`. 학력 미확인은 그대로 표기하고 추정하지 않는다.
5. **적합도·근거**: `82/100`처럼 점수를 먼저 보여 주고 아래에 근거 2개와 확인 필요 1개 이내. 근거는 각 70자 이내, 확인 필요는 60자 이내를 표시 목표로 한다. 원문은 손실 없이 보존한다.
6. **매칭 포지션**: 고객사·서치 포지션명·모집 회차 식별자. 제목이 같아도 다른 채용 건을 합치지 않는다.
7. **담당·다음 행동**: 담당자와 `검토`, `제안 준비`, `발송 확인`, `보류`, `제외` 등 상태/액션. 이 컬럼은 칸반 링크를 대체하는 운영 행동이다.

점수와 “왜 잘 맞는지”를 한 셀로 통합한다. 점수가 높은 것과 근거가 충분한 것은 다른 속성이므로 `근거 부족`, `구버전 점수`, `재확인 필요`를 별도 배지로 표시한다.

### 3.4 요약 규칙

프로필 텍스트는 DB의 검증된 구조화 자료에서 만들고, LLM이 학력·회사·재직 기간을 보충하지 않는다. 화면을 열 때마다 LLM을 다시 호출하지 않는다. 기존 요약기가 있으면 재사용하고, 없으면 먼저 결정론적 템플릿과 줄 제한을 사용한다.

정확한 날짜가 있어 총 경력을 계산할 때는 겹치는 재직 기간을 중복 합산하지 않는다. 연도만 있거나 일부 이력이 없으면 `확인된 경력`, `약`, `기간 미확인`을 구분하고 과도한 정밀도를 표시하지 않는다. `현재`는 프로필을 관측한 날짜 기준임을 보존한다.

관련 경력과 전체 경력을 같은 값으로 만들지 않는다. 점수 0은 “유효한 평가의 실제 결과가 0”일 때만 표시한다. 점수가 존재하지만 출처·버전·근거가 검증되지 않은 레거시는 삭제하지 말고 `레거시 100/100 · 근거 미확인` 같은 구분을 사용한다. 해당 값은 기본 우선순위 정렬의 신뢰 가능한 점수로 사용하지 않는다.

### 3.5 시각적 기준

권장 기본 행 높이 112~136px, 본문 13~14px, 여백 12~16px. 화면 밀도 `기본/촘촘하게`를 제공하되 큰 글자 확대에서도 데이터에 접근할 수 있어야 한다. 장문은 line-clamp하고 키보드로도 상세를 열 수 있게 한다.

발송 확인은 초록, 확인대기는 호박색, 실패는 빨강, 알 수 없음은 회색을 권장하되 **색만으로 구분하지 않고 텍스트·아이콘을 함께 사용**한다. 전체 줄을 진한 색으로 채우지 않는다. 표 헤더와 후보자 식별 부분을 고정하되 작은 화면에서 클릭이 가려지지 않게 한다.

1440px에서는 핵심 7컬럼을 읽을 수 있게 배치한다. 1024px 이하에서는 프로필·근거를 접어 상세로 옮길 수 있지만 후보자·포지션·발송·다음 행동은 남긴다. 기존 디자인 컴포넌트를 우선 사용한다.

### 3.6 상세 패널

행 클릭 시 우측 상세 패널을 열고 직접 접근 가능한 URL 상태를 유지한다.

- 후보/포지션 식별, 프로필 전체 요약과 출처.
- 평가 버전·JD 버전·근거·리스크·원문 관측 시각.
- 최초 발견 → 재검색 → 내부 보고 → 검토 → 실제 제안 → 후속 반응의 타임라인.
- 채널별 실제 발신 계정, 메시지/제안 ID, 발송 시각, 확인 시각, 증빙.
- 담당자 변경, 검토 결정, 보류 사유/재검토일, 제외 사유.

`발송 완료로 표시` 버튼은 만들지 않는다. 수동 기록은 `발송했다고 기록 / 증빙 제출`이며, 검증 전까지 실제 발송 KPI에 포함되지 않는다. 한 채널이 확인됐더라도 다른 채널의 상태를 확인됨으로 복제하지 않는다.

### 3.7 검색

전역 검색은 Supabase의 권한 있는 전체 대상에서 실행한다. 후보 이름/별칭, 회사, 직함, 포지션, 검증된 요약의 검색용 텍스트를 검색한다. 비공개 원문 전체를 브라우저에 내려 검색하지 않는다.

검색은 Unicode 정규화, 영문 대소문자, 공백 정리를 적용한다. 한글/영문 이름을 모두 지원하되 근거 없는 음역 추측을 같은 인물 확정에 사용하지 않는다. 공백으로 분리한 검색어는 기본 AND, 각 검색어는 지정 필드들 사이 OR로 정의한다. `%`, `_`, 따옴표는 사용자 문자열로 처리하고 SQL 구문으로 해석하지 않는다. q 최대 200자.

기본 page size 50, 선택 25/50/100. 서버 정렬 키와 고유 ID를 tie-breaker로 사용하는 안정적인 페이지네이션. 결과 총수·적용 필터·수집 불완전 여부를 표시한다. 권한 없는 기록의 존재가 총수나 facet에서 유출되면 안 된다.

`미처리 고적합`, `발송 검증 대기`, `7일 초과`, `이번 주 신규`, `최근 제안`은 저장된 필터 프리셋이다. 고적합 임계값은 기존 승인 기준을 재사용하며, 확인되지 않으면 임의로 80점을 고정하지 않는다. 전체 기록 기본 정렬은 최근 서치 일시 내림차순, 처리할 후보 기본 정렬은 기한 초과 우선 → 대기 시작 오래된 순 → ID로 고정한다.

---

## 4. 데이터 정체성과 논리 스키마

### 4.1 단위

- `candidate_id`: 실제 인물. 여러 채널의 프로필이 연결될 수 있다.
- `position_opening_id`: 고객사의 특정 채용 건. 고객사+직무명 텍스트만으로 대체하지 않는다.
- `match_id`: **candidate_id × position_opening_id**의 업무/매칭 단위. 같은 채용 건 재검색은 새 match가 아니다.
- `run_id`: AI Search를 수행한 논리 실행. 재시도는 같은 run의 attempt로 남긴다. 사용자가 새로 요청한 재검색은 새 run이다.
- `observation_id`: run에서 특정 원천의 후보를 관측한 사건.
- `assessment_id`: 특정 후보 자료·JD·평가 버전에 대한 평가 결과.
- `outreach_id`: **실제로 전송된 메시지 × 수신 후보자**. 하나의 메일에 여러 수신자가 있으면 후보자별 전송을 구분한다.
- `work_event_id`: 검토·대기 유입·제외·재개 등 해당 match의 업무 상태 변화.

기본 표는 match 단위이며 최신 관측·평가를 투영한다. 상세에는 반복 검색 이력이 남는다. 전체 원천 관측 수를 보고 싶을 때만 별도의 관측 이력 보기로 이동한다.

### 4.2 공통 타입 및 필드

아래는 **논리 계약**이다. 테이블을 이 이름으로 모두 새로 만들라는 지시가 아니다. 기존 객체를 먼저 매핑한다.

`ID`: 기존 정본 ID와 호환되는 opaque string. 실제 UUID/문자열 타입은 WU-01 매핑표에 고정한다. `UTC_TS`: timezone을 포함한 ISO-8601 입력, 중앙 저장은 `timestamptz`, 로컬은 UTC ISO 문자열 또는 기존 일관된 epoch 단위. 단위 혼용 금지. `?`는 nullable, 나머지는 필수다.

모든 운영 엔터티는 조직/접근 범위, stable ID, schema_version, created_at 또는 recorded_at을 가진다. 원천 사건에는 occurred_at과 observed_at/ingested_at을 분리한다. 원래 시각이 없으면 occurred_at=null이며 현재 시각을 대입하지 않는다. 수정 가능한 투영에는 optimistic concurrency용 version을 둔다.

### 4.3 CandidateIdentity — 기존 후보 DB 재사용

필드: `identity_id`, `candidate_id`, `provider`, `account_scope?`, `provider_subject_id`, `canonical_profile_url?`, `verification_method`, `verified_at?`, `source_ref`.

고유키: provider가 ID를 전역 보장하면 `(provider, provider_subject_id)`, 계정 범위라면 `(provider, account_scope, provider_subject_id)`. account_scope의 null 의미와 고유 제약을 물리 매핑에서 고정한다.

이름·회사 유사도만으로 인물을 합치지 않는다. LinkedIn 공개 URL과 RPS ID의 관계도 실제 확인 근거가 있어야 한다. 확인되지 않으면 `possible_duplicate`로 연결 후보만 표시한다. 병합은 별도 감사 가능한 작업이며 원래 ID→정본 ID alias를 보존한다. 병합으로 제거된 중복 업무는 시스템 조정이지 팀 성과가 아니다.

### 4.4 PositionOpening — 기존 포지션 DB 재사용

필드: `position_opening_id`, `client_id`, `display_name`, `jd_version`, `status`, `source_refs`, `canonical_parent_id?`.

같은 회사·같은 제목으로 다시 열린 채용 건은 명시된 opening ID로 구분한다. SCRAPED 분류나 phase-out 고객사를 자동 업무 유입에서 제외하는 기존 승인 규칙이 있으면 공용 규칙을 재사용한다. 기존 요구에 있는 TwelveLabs phase-out와 SCRAPED 제외의 정확한 적용 범위는 WU-00에서 확인한다. 이를 이유로 기존 역사·증빙을 삭제하지 않는다.

### 4.5 SearchRun

필드: `run_id`, `parent_run_id?`, `request_key`, `requested_by`, `executor_engine`, `executor_version?`, `machine_id?`, `status`, `requested_at`, `started_at?`, `finished_at?`, `last_heartbeat_at?`, `scope`, `coverage_status`, `error_code?`.

status: `queued | running | waiting_human | partial | completed | failed | cancelled`.

scope에는 대상 opening IDs, 원천·계정, 실행 범위와 중단 사유를 구조화한다. 하나의 run이 여러 포지션을 다룰 수 있지만 결과마다 opening ID가 있어야 한다. `completed`는 해당 run의 선언된 범위를 완료했다는 뜻이며 모든 시장 후보를 찾았다는 뜻이 아니다. `cancelled`와 `waiting_human`을 failed로 합치지 않는다. 오래된 heartbeat는 상태 확인 경고이지 자동 실패 확정이 아니다.

### 4.6 SearchObservation

필드: `observation_id`, `run_id`, `candidate_id?`, `position_opening_id?`, `match_id?`, `source_system`, `origin_platform?`, `acquisition_method`, `source_account_id?`, `source_record_id`, `source_locator`, `source_revision?`, `occurred_at?`, `observed_at`, `ingested_at`, `evidence_ref`, `payload_hash`, `link_state`.

acquisition_method: `live_portal | archive | email_backfill | clickup_import | legacy_db`.

LinkedIn 출신 프로필을 Supabase 아카이브에서 읽었다면 origin_platform=linkedin, acquisition_method=archive다. 이것을 “오늘 LinkedIn에서 새로 검색”으로 표시하지 않는다.

`link_state=linked | unresolved | ambiguous | rejected`이다. linked인 경우 candidate_id·position_opening_id·match_id가 모두 존재해야 한다.

고유 관측키는 `(run_id, source_system, source_record_id, source_locator, source_revision)`에 해당하는 stable key다. 원천 ID의 범위가 계정별이면 source_account_id를 포함한다. 값이 같은 재수집은 1건, 같은 키 다른 핵심 payload는 conflict로 격리한다. 새로 관측된 실제 원문 버전은 별도 revision이다.

candidate/opening 미해결 기록은 orphan/quarantine에서 보존한다. 미연결 결과를 삭제하거나 임의의 기존 포지션으로 붙이지 않는다. 정본 match 목록·처리 업무에는 미해결 기록을 섞지 않는다.

### 4.7 Assessment

필드: `assessment_id`, `match_id`, `observation_id`, `candidate_snapshot_ref`, `jd_version`, `scoring_version`, `assessed_at`, `score_status`, `score_value?`, `legacy_score_value?`, `operational_intent`, `evidence_quality`, `profile_summary`, `fit_bullets`, `risk_bullets`, `evidence_refs`, `input_hash`, `result_hash`, `supersedes_assessment_id?`.

score_status: `scored | unscored | failed | legacy_unverified`. score_value는 scored일 때 0..100, unscored/failed일 때 null. legacy_unverified는 원래 숫자를 별도 원본 필드/스냅샷에 보존하되 정본 scored로 승격하지 않는다. 기존 정밀도를 저장하고 반올림은 표시 계층에서만 한다.

evidence_quality: `sufficient | limited | conflict | unknown`. fit_bullets/risk_bullets 각 항목은 `text + evidence_refs`다. 화면 표시를 짧게 만들었다고 전체 근거를 잘라 저장하지 않는다.

`operational_intent=review | contact | record_only | unknown`은 기존 결과 구분의 의미를 보존하는 값이다. `legacy_score_value`는 원래 숫자가 있을 때만 보존한다. profile_summary는 `education_line`, `career_line`, `experience_line`, `as_of`, `evidence_refs`로 구조화한다.

새 실행이 실패했다고 과거의 검증된 점수를 삭제하지 않는다. 현재 유효 JD 버전에 대한 최신 평가와 이전 평가를 구분한다. JD 버전이 바뀌면 과거 점수를 현재 점수인 것처럼 표시하지 않는다. 기존 review_candidate 및 승인 scoring contract를 수정하지 않는 회귀시험이 필수다.

### 4.8 Match / 업무 투영

필드: `match_id`, `candidate_id`, `position_opening_id`, `first_discovered_at?`, `last_observed_at?`, `latest_valid_assessment_id?`, `owner_id?`, `review_state`, `outreach_state`, `queue_state`, `next_action`, `hold_until?`, `version`.

고유키: `(조직 범위, candidate_id, position_opening_id)`.

review_state: `pending | ready | held | excluded`.

outreach_state는 §5의 증거로 계산한다. queue_state: `not_enrolled | open | closed_business | closed_system`. next_action은 상태의 결정론적 투영이며 LLM이 임의 생성한 상태값이 아니다.

중요: Match는 읽기 편의를 위한 현재 상태다. 주간 이력을 이것만 보고 역산하지 않는다. 원천 관측·평가·WorkEvent·Outreach에서 재현 가능해야 한다.

### 4.9 WorkEvent

필드: `work_event_id`, `match_id`, `event_type`, `previous_state`, `next_state`, `actor_id?`, `actor_kind`, `owner_id_at_event?`, `occurred_at`, `recorded_at`, `reason_code?`, `reason_text?`, `source_ref?`, `command_id`, `expected_version?`.

actor_kind: `human | ai | system | unknown`.

event_type: `enrolled | review_ready | held | excluded | verified_contact_closed | reopened | owner_changed | system_removed | corrected`.

제외/보류/재개/시스템 정리에는 이유가 필수다. 보류는 업무를 삭제하지 않으며 백로그 안에 남는다. 임의의 과거 시각으로 업무를 바꾸는 입력은 기본 비활성화하고 관리자 보정 경로에서만 사유와 근거를 받는다.

같은 command_id는 한 번만 반영한다. version 충돌은 409와 최신 상태를 반환한다. 다른 사용자의 결정을 마지막 쓰기로 덮어쓰지 않는다. 검증된 발송이 취소되면 필요한 경우 업무를 자동 재개하되, 원래 업무가 별도 사유로 제외된 상태라면 무조건 재개하지 않는 reducer 규칙을 테스트한다.

### 4.10 Outreach와 Match 연결

Outreach 필드: `outreach_id`, `channel`, `sender_account_id`, `sender_actor_id?`, `recipient_identity_id`, `provider_message_id?`, `source_event_key`, `message_type`, `occurred_at?`, `observed_at`, `recorded_at`, `verification_state`, `evidence_method`, `evidence_ref?`, `content_hash?`, `delivery_state`, `reply_state`, `verification_revision`, `corrects_outreach_id?`.

channel: `saramin | jobkorea | linkedin | email`. verification_state: `unknown | claimed | verified | conflict | rejected | revoked`.

email은 이미 운영 중인 후보 대상 이메일 경로가 확인될 때만 연결하는 확장 가능 값이다. 새 이메일 발송 기능을 만들라는 지시가 아니다. v1 채널별 필수 인수 대상은 사람인·잡코리아·LinkedIn이다.

message_type: `candidate_proposal | follow_up | connection_request | internal_report | unknown`. 내부 보고는 보고 엔터티에 두는 것이 기본이며, 원천 공용 메시지 테이블을 쓰는 경우 반드시 이 타입으로 격리한다. LinkedIn 연결 요청을 InMail 제안으로 세지 않는다.

고유키는 provider 메시지 ID가 있으면 `(channel, sender_account_id, provider_message_id, recipient_identity_id)`다. 없으면 공식 화면의 안정적인 원천 사건 키를 사용한다. 시간·본문이 같다고 별개의 발송을 섣불리 병합하지 않는다. 구분할 수 없는 충돌은 ambiguous로 격리한다. collected_at을 새 ID 생성에 사용하지 않는다.

OutreachMatchLink 필드: `outreach_id`, `match_id`, `link_state`, `link_basis`, `evidence_ref`, `linked_at`, `linked_by?`. 고유키 `(outreach_id, match_id)`. link_state는 `unresolved | ambiguous | verified | rejected`이며 verified만 매칭별 발송 판정에 사용한다.

한 메시지에 두 포지션이 실제로 제안됐으면 메시지 전송은 1건, 확인된 매칭은 2건일 수 있다. 본문/원천의 명시 근거 없이 현재 보고 있는 포지션으로 붙이지 않는다. 연결이 모호하면 실제 발송 사건은 보존하되 해당 match의 발송 KPI에는 넣지 않는다.

### 4.11 InternalReport

필드: `report_id`, `run_id`, `report_version`, `snapshot_ref`, `snapshot_hash`, `engine`, `recipient_set_ref`, `status`, `provider_message_id?`, `sent_at?`, `last_error?`, `idempotency_key`.

고유키: `(run_id, report_version, recipient_set_ref)`. status: `queued | sending | sent_unverified | sent_verified | failed | unknown`.

기존 제목 접두사를 유지한다. 본문에 run ID, 결과 범위, 평가/관측 한계, 원문 링크, 웹 상세 링크를 포함한다. 수신자 allowlist를 재사용한다. ai 결과의 “추천 N명”을 고객사 추천 실적으로 처리하지 않는다.

### 4.12 SourceCoverage / SyncRun

필드: `source`, `account_id`, `scope_hash`, `coverage_from?`, `coverage_to?`, `last_attempt_at`, `last_success_at?`, `cursor?`, `pages_read`, `pagination_exhausted`, `coverage_status`, `error_code?`, `ingestion_run_id`, `central_ack_at?`.

coverage_status: `complete | partial | blocked | stale | unknown`.

complete는 **명시된 원천/계정/기간/조회 조건 안에서만** 성립한다. 채널별 페이지를 끝까지 읽었는지, 날짜 범위를 다뤘는지, 필터가 걸렸는지, 로그인 계정이 맞는지 검사한다. 동기화가 실패해도 last_success_at을 현재 시각으로 덮어쓰지 않는다.

### 4.13 저장·조회 제약

nullable 필드가 포함된 복합 UNIQUE의 null 동작을 추정하지 않는다. 원천별 키를 정규화한 non-null stable key 또는 실제 DB 버전에 맞는 명시적 제약을 사용하고, null 원천 revision의 반복 입력도 중복 방지 시험에 포함한다.

모든 FK·UNIQUE·상태/점수 CHECK는 애플리케이션 검사뿐 아니라 가능한 DB 제약으로 보장한다. 중앙 기록 여러 개를 하나의 업무 단위로 반영할 때 단일 트랜잭션/검증된 서버 함수로 처리한다. PostgREST 요청을 여러 번 보냈다고 전체 원자성이 생겼다고 주장하지 않는다.

Supabase 쓰기에는 사용자/서비스별 최소 권한을 적용하고, RLS를 우회하는 서버 키를 브라우저에 두지 않는다. 뷰/RPC의 호출 권한도 별도 시험한다. SQLite는 연결마다 foreign_keys 적용을 검증하고 짧은 트랜잭션·bounded busy retry를 사용한다. SQLite 파일을 여러 기계의 공동 운영 DB로 공유하지 않는다.

---
## 5. 실제 발송 판정 계약

### 5.1 긍정 증거

`verified`에는 최소한 채널, 실제 발신 계정, 수신 후보의 안정적 식별, 발송 사건, 확인 가능한 원천 증거가 필요하다. 해당 포지션 발송으로 표시하려면 verified OutreachMatchLink까지 필요하다.

허용할 수 있는 evidence_method는 `provider_api_readback`, `authenticated_history_readback`이다. 수동 제출 자료는 `manual_claim`에서 시작하며 별도 승인된 검증 정책 없이 자동으로 verified로 바꾸지 않는다. 캡처 해시는 자료가 변하지 않았다는 검사이지 진실성 자체의 증명이 아니다.

- API를 제공하는 경로: 발송/이력의 provider ID와 읽기 재조회로 계정·수신자·상태를 확인한다.
- 공식 API를 사용할 수 없는 포털: 이미 허용된 로그인 세션과 기존 어댑터를 이용해 발송 내역/대화 상세를 읽고 사건을 확인한다. 자동화 권한이나 공식 기능이 있다고 가정하지 않는다.
- 메시지 ID를 확인할 수 없는 화면: 안정적인 내역 식별 및 발신자·수신자·내용/포지션·발송시각을 검증할 수 있는 경우만 채택한다. 모호하면 `conflict/unknown`으로 남긴다.

로그인됨, 크레딧 차감, 발송 버튼 클릭, 성공 토스트만 단독으로 기록됨, 메시지 탭 존재, 내부 보고메일의 문장, ClickUp 완료 상태는 verified 근거가 아니다.

### 5.2 행의 대표 상태

우선순위는 아래와 같다. 다른 채널의 미확인 상태는 상세에 그대로 남긴다.

1. 이 match에 verified 제안이 하나 이상 연결됨 → **발송 확인됨**.
2. 발송 주장/전송 시도/상충 증거는 있으나 verified가 없음 → **검증 대기**.
3. 요구된 계정·채널·기간의 조회가 complete이고 연결된 발송이 0임 → **미발송(관측범위)**. 그 범위를 tooltip/상세에 표시한다.
4. 그 밖의 경우 → **확인 불가**. 이력 누락·권한 오류·미연결 등 사유를 표시한다.

DB에 보내지 않았음을 뜻하는 전역 `sent=false`를 무근거 기본값으로 넣지 않는다. 채널·기간 한정 음성 관측은 `no_send_observed_in_scope`로 표현한다. 전송 실패 증거가 있어도 다른 시도나 다른 채널 발송이 없었다는 증거는 아니다.

실제 발송 자체를 확인했지만 정확한 발생시각이 없는 경우 그 한계를 보존한다. “발송 확인됨 · 시각 미확인”은 허용하되 특정 주의 시간 확인 실적에는 편입하지 않는다.

### 5.3 발송·수신·응답의 분리

발송 확인은 배달 완료나 읽음이 아니다. delivery_state=`unknown | delivered | bounced`, reply_state=`unknown | none_observed | replied | interested | declined`를 별도 관리한다. 포털의 pending InMail은 그 상태가 실제 발송을 뜻하는지 원문을 확인한 뒤 매핑한다. 상대 응답 대기를 미발송으로 임의 해석하지 않는다.

발송 이후 bounce가 확인되어도 발송 사건 자체를 삭제하지 않는다. 발송 건수, 반송, 유효한 후속 연결을 따로 표시한다. 관심 응답은 자동 회신이나 단순 거절과 구분한다.

### 5.4 세 채널의 연결 완료 조건

사람인·잡코리아·LinkedIn 각각 다음을 기록한다.

`계정 식별 → 접근 범위 → 발송이력 읽기 → 후보자 연결 → 포지션 연결 → 중복 제거 → 중앙 저장 → 재조회 → 웹 증빙 확인`.

채널별 상태는 `미구현 / 로컬 시험 통과 / 접근 차단 / 부분 관측 / 라이브 읽기 검증 완료`로 분리한다. 세 어댑터 코드가 있다고 해서 세 채널 추적 완료로 보고하지 않는다. 라이브 읽기는 이미 발송한 과거 기록을 사용하며, 시험을 위해 새 후보자에게 연락하지 않는다.

강상모 계정의 관측과 팀 전체 관측을 혼합하지 않는다. `강상모 3개 채널 중 2개 관측`, `팀 계정 관측 1/4` 같은 표현은 실제 확인된 분모가 있을 때만 사용한다. 분모를 확인하지 못하면 `추가 계정 범위 미확인`으로 쓴다.

---

## 6. 쓰기 경로·동기화·내부 메일

### 6.1 목표 흐름

```text
기존 AIsearch producer (Claude Code / Codex / 기존 실행기)
  → 동일한 결과 envelope 검증
  → 로컬 실행: SQLite 원장 + 중앙 반영 outbox를 한 트랜잭션으로 저장
  → 중앙 수신: ID·버전·중복·권한 검증 후 Supabase에 원자적 반영
  → 동일 결과 snapshot으로 내부 보고 예약
  → readback 및 ACK
  → 웹 목록 / 상세 / 위클리
  → 내부 보고 dispatcher: 승인된 수신자에게만 발송 및 재조회

사람인 / 잡코리아 / LinkedIn / Gmail 기존 발송이력
  → 읽기 전용 수집 어댑터
  → 근거 검증·정체성/포지션 연결
  → 같은 중앙 원장
```

중앙 서버에서 실행하는 producer는 같은 계약과 저장 서비스를 직접 사용한다. 이를 위해 로컬 SQLite를 억지로 거치지 않는다. 같은 기능의 HTTP/SDK 어댑터를 여러 개 만들지 않는다.

### 6.2 SQLite와 Supabase의 관계

각 로컬 outbox 항목은 `operation_id`, `entity_key`, `payload`, `payload_hash`, `schema_version`, `created_at`, `attempt_count`, `next_attempt_at`, `status`, `central_ack_ref?`, `last_error_code?`를 가진다.

status: `pending | in_flight | synced | failed | conflict`. 동일 operation_id의 동일 payload는 한 번의 논리 반영, 다른 payload는 conflict다. 중앙 저장 성공 응답 후 readback의 ID·핵심 필드·hash가 일치할 때만 synced 처리한다. 정규화된 표현의 hash를 쓰며, DB의 공백·JSON 키 순서 차이로 거짓 불일치를 만들지 않는다.

payload hash에는 업무 데이터·원천 버전만 넣는다. 재시도 횟수, 수집 시각, 전송 시각, 임시 경로를 넣어 동일 내용을 새 사건으로 만들지 않는다. 원천 관측의 실제 시각은 해당 계약에 따라 payload의 업무 필드로 보존한다.

Supabase 장애 시 로컬 기록은 보존한다. 웹에는 마지막으로 확인한 중앙 상태와 지연 경고가 남는다. 서로 다른 기계의 SQLite 파일을 실시간 합쳐 추정 KPI를 만들지 않는다. 중앙 장애 중 내부 보고도 기본적으로 대기시킨다. 별도 승인된 장애 보고를 보낸다면 “중앙 미반영”을 명시하고 공식 위클리 실적으로 처리하지 않는다.

대상 없는 최신 데이터 덮어쓰기, 전체 테이블 교체, SQLite→Supabase 무조건 overwrite는 금지한다. 새 검증 자료가 기존보다 오래됐으면 기존 투영을 뒤로 돌리지 않되 원천 관측은 보존한다.

### 6.3 외부 메일 부수효과

결과 commit과 보고 예약은 같은 저장 경계에 둔다. DB commit과 Gmail 전송을 하나의 분산 트랜잭션처럼 취급하지 않는다.

- DB 반영 실패: 보고 전송 0회, 로컬 원장 보존.
- DB 성공/보고 실패: 결과는 웹에 남고 보고만 재시도 대상.
- Gmail 성공 응답 후 ACK 기록 전에 중단: 상태는 unknown 또는 sent_unverified. report ID를 포함한 기존 메시지를 조회해 해결한다.
- 전송 여부를 확인할 수 없음: 무조건 재전송하지 않는다. 중복 가능성을 표시하고 보수적으로 보류한다.

애플리케이션 idempotency key만으로 Gmail의 exactly-once 전송을 보장했다고 주장하지 않는다. 라벨링 실패도 “보고 전송 실패”와 별도 처리한다. Gmail send 응답은 Message를 반환하지만, 이 시스템의 sent_verified는 읽기 재확인까지 포함하는 더 엄격한 운영 계약이다.

### 6.4 자동 및 수동 갱신

새로 구조화한 AI Search 결과는 저장 완료 후 웹 조회에 반영한다. 포털/Gmail/ClickUp 기존 이력은 **매시간 조정 수집**을 기본 요구로 하되 기존 관리형 스케줄러를 재사용한다. 웹브라우저가 열려 있어야 도는 setInterval만으로 운영 동기화를 대체하지 않는다.

`지금 동기화`는 기존 수집 작업을 예약하고 상태를 보여 주는 기능이다. 브라우저에서 포털/메일 자격증명에 접근하지 않는다. 같은 계정·원천 범위의 실행이 진행 중이면 새 실행 대신 기존 run을 반환한다.

자동·수동 경로는 같은 handler와 중복방지 규칙을 사용한다. 페이지 새로고침은 발송·동기화·LLM 재평가를 일으키지 않는다. 권한 만료/로그인 challenge는 bounded retry 후 blocked 처리하고, 기존 허용된 human handoff를 사용한다.

---

## 7. 업무 유입·처리·백로그 계약

### 7.1 업무로 편입되는 조건

전체 검색 관측과 사람에게 넘기는 업무를 분리한다. 신규 structured result는 기존 승인된 AIsearch 결과 구분을 `operational_intent=review | contact | record_only | unknown`으로 손실 없이 매핑한다.

- resolved 후보자와 opening이 있고, 운영 대상 포지션이며, intent=review/contact인 새 match는 1회 enrolled가 된다.
- 이미 enrolled된 match의 재검색은 관측만 추가한다.
- record_only/unknown, 미연결 결과, 부적합·오류 기록은 전체 서치 기록에 보존하되 자동 업무 유입에 넣지 않는다. 운영자가 명시적으로 편입할 수 있다.
- 원천에 intent가 없으면 임의 점수 임계값으로 만들어내지 않는다. 미분류 기록으로 남긴다.
- 레거시 이관은 기본 not_enrolled다. 별도 재활성화 결정이 있어야 현재 업무가 된다.
- 동일 opening의 기존 verified 발송이 이미 있으면 새 검색만으로 제안대기 업무를 만들지 않는다. 후속 연락이 필요하면 사유 있는 reopened로 관리한다.

### 7.2 업무 종료

**업무상 종료:** 현재 열린 업무에 대한 verified 제안 연결로 `closed_business/sent`, 사람의 명시적 검토 제외로 `closed_business/excluded`.

**시스템상 제거:** 중복 병합, 잘못된 연결 정정, 고객사/포지션 운영 범위 제외, 포지션 종료로 `closed_system`. 시스템 제거는 업무 처리 성과가 아니다.

ready(제안 준비), held(보류), 발송 검증 대기는 모두 열린 업무다. 보류로 옮겨도 전체 백로그는 줄지 않는다. 백로그는 `검토대기 + 제안대기 + 검증대기 + 보류`로 분해하여 보인다.

처리 담당자와 발송 계정 소유자는 다를 수 있다. 검토는 해당 human actor, 실제 제안은 검증된 sender actor에게 귀속한다. 수집기를 실행한 Claude/Codex나 로그인한 현재 관리자에게 실적을 자동 귀속하지 않는다. 발신자 미확인은 별도 그룹이며 팀 전체 실적이라고 추정하지 않는다.

### 7.3 재개와 보정

재개에는 사유가 필요하다. 하루에 동일 match를 여러 번 닫았다 열었다 해도 고유 처리량은 1건이다. 그러나 백로그 수지에는 모든 유효 전이가 들어가야 한다. 이 두 수치를 섞지 않는다.

늦게 발견된 과거 발송은 발송 사건의 실제 주에 반영한다. 현재 열려 있는 잘못된 대기를 해소하는 조정은 그 조정이 실제로 발생한 시각의 시스템 보정으로 남길 수 있다. 과거 발송을 오늘 새로 보냈다고 기록하거나 과거 업무 사건을 조용히 재작성하지 않는다.

---

## 8. 지표 계약

### 8.1 공통 집계 컨텍스트

모든 지표는 다음을 명시한다.

`metric_id, metric_version, window_start, window_end, timezone, as_of, snapshot_id/revision, scope, coverage_status, numerator_unit, denominator_unit, evidence_membership`.

주간은 `[일요일 00:00 KST, 다음 일요일 00:00 KST)`다. 예: `2026-09-20 00:00+09:00 ≤ t < 2026-09-27 00:00+09:00`는 9월 20~26일이다. UTC 저장 경계는 9월 19일 15:00Z~9월 26일 15:00Z다.

기본 week_key는 KST week_start 날짜다. FY 라벨은 기존 사업 주차 매핑을 검증한 뒤 사용한다. ISO 주차에 임의 ±n을 적용하지 않는다. 미해결이면 날짜 범위를 표시하고 FY는 비워 둔다.

occurred_at이 없는 사건은 기간 확인 KPI에서 제외하고 `발생시각 미확인`으로 따로 센다. imported_at/ingested_at으로 대체하지 않는다. 부분 수집 상태의 0건은 `관측 0건 · 범위 불완전`이며 확정 0과 다르다.

담당자 필터는 `업무 담당자`와 `실발신자`를 구분한다. 업무 지표의 담당자는 해당 사건/시점의 담당자를 사용하고, 발송 지표의 실발신자는 실제 sender actor를 사용한다. 현재 담당자로 과거 실적을 소급 귀속하지 않는다. 포지션/담당자 필터에 연결할 수 없는 외부 발송은 미연결 그룹으로 분리한다.

### 8.2 지표 정의

**M-01 새 업무 유입** — window 안의 최초 enrolled WorkEvent가 있는 distinct match_id. 재검색, run 재시도, legacy import는 제외. 단위 `매칭 업무`.

**M-02 AI 서치 관측** — window 안에 실제 관측된 distinct observation_id 및 별도의 distinct candidate_id. 과거 관측을 이관한 시간은 사용하지 않는다. archive 검색도 acquisition_method별로 분리한다. 업무 유입과 합산하지 않는다.

**M-03 검토 처리** — window 안의 human actor가 수행한 review_ready/held/excluded 중 유효한 결정이 있는 distinct match_id. 같은 항목 반복 클릭은 1건. 검토 처리 1건이 업무 종료 1건을 뜻하지 않는다.

**M-04 제안 전송 건수** — window 안의 occurred_at이 확인된, verification_state=verified인 candidate_proposal/follow_up Outreach의 distinct outreach_id. 후보자별 message delivery 단위. 연결요청·보고메일·실패·수동주장·충돌은 제외. follow_up은 하위 항목으로 분리한다.

**M-05 제안 대상 인원** — M-04의 distinct canonical candidate_id. 계정별 하위합은 같은 후보가 겹칠 수 있으므로 전체와 단순 합이 다를 수 있음을 표시한다. 후보 정체성 미해결 사건은 미연결 수로 분리한다.

**M-06 최초 제안 매칭** — 각 match에 처음 연결된 verified candidate_proposal의 occurred_at이 window 안에 있는 distinct match_id. 후보 1명/포지션 2개는 2매칭 가능. follow_up으로 증가하지 않는다. 포지션 연결이 모호하면 제외한다.

**M-07 업무상 고유 처리량** — window 안에 closed_business로 전이된 distinct match_id. sent와 human excluded를 구분하여 표기한다. 동일 match가 두 유형을 거쳤으면 마지막 유효 업무 종료 유형으로 분류하여 하위합이 전체와 일치하게 한다. 시스템 제거는 제외한다.

**M-08 기말 백로그** — window_end 직전(진행 중이면 as_of)의 enrolled 상태 중 queue_state=open인 distinct match_id. 보류 포함. 단계별 수의 합이 총수와 같아야 한다. 현재 Match 상태가 아니라 해당 시점까지 유효한 WorkEvent로 계산한다.

**M-09 기한 초과 대기** — M-08 중 현재 열린 업무 구간의 opened_at부터 기준시각까지 7×24시간 이상인 match 수. 보류 포함 총수와 재검토일이 지난 보류 수를 구분한다. 재개 전 누적 대기 기간은 상세에 따로 보여 준다. opened_at이 없으면 대기 기간 미확인이다.

**M-10 기간 내 업무처리율** — `|M-07의 match 집합 ∩ A| / |A|`, A는 기초 open 업무, 기간 내 신규 enrolled, 기간 내 reopened의 distinct 합집합. 분모 0은 null/“대상 없음”. 시스템 제거는 분자에 넣지 않는다. 이 비율은 사람·시간 투입을 측정한 가동률이 아니라 기간 내 업무 처리 비율이다.

**M-11 백로그 수지** — 전이 횟수 기반: `B_end = B_start + new_enroll_transitions + reopen_transitions − business_close_transitions − system_remove_transitions`. M-07은 고유 업무 수이며 이 공식의 business_close_transitions와 같다고 가정하지 않는다. held/ready/owner_changed는 수지 증감 0이다.

**M-12 내부 보고** — window 안의 sent_verified InternalReport 수. 실제 제안과 다른 카드/진단에 둔다. 제목의 “추천 6명”은 고객사 추천 KPI가 아니다.

### 8.3 주간 그래프

기본 4주: 마지막 마감 4주. 현재 진행 중 주를 보려면 `이번 주 포함`을 명시한다. 위클리에서 특정 회의 주를 선택하면 그 주를 끝으로 한 4주를 표시한다.

그래프 1: 신규 업무 vs 고유 업무 처리량, 나란한 막대. 그래프 2: 기말 백로그, 독립 막대. 제안 전송은 채널별 하위 분석으로 제공한다. 서로 다른 단위의 수치를 같은 “후보 수”로 겹쳐 그리지 않는다.

막대 클릭 시 해당 주·metric ID·snapshot ID의 증거 목록을 연다. 부분 수집 주는 사선/경고/빈 구간으로 표시하고 완전 관측 주와 같은 의미의 0 막대로 만들지 않는다.

### 8.4 용량과 수익의 해석

기본 운영 판단은 신규 유입, 실제 제안, 검토 처리, 백로그/노후화로 한다. 이 숫자만으로 “팀 생산능력 100%”나 사람별 업무시간을 추정하지 않는다. 후보 난이도·포지션·관측 계정 수가 다를 수 있다.

선택적인 `최근 완전 관측 4주 평균 실제 제안 처리량`은 충분한 완전 관측 주가 있을 때만 표시한다. 백로그/평균 처리량을 계산할 경우 신규 유입 0이라는 가정의 참고 추정치로 표시하며, 평균 0·관측 주 부족이면 null이다. v1 필수 기능은 아니다.

후속 퍼널은 실제 관심 응답·첨부 이력서 확보·고객사 추천 사건을 match에 연결해 구현한다. 같은 기간의 신규 발송 수로 오래된 후보의 이번 주 응답을 나눠 “응답률”로 만들지 않는다. 전환율은 발송 코호트와 관측 기간을 맞춰 별도 계약한다. 예상 수수료나 가공 매출을 핵심 성과로 표시하지 않는다.

### 8.5 스냅샷과 지연 수집

기존 Weekly snapshot 구조를 재사용한다. snapshot에는 metric_version, 범위, as_of, source watermarks, membership IDs, 데이터 hash, 보정 이유/이전 버전을 둔다.

같은 snapshot의 카드·그래프·드릴다운은 같은 membership을 읽는다. 이후 후보의 이름/현직이 바뀌어도 당시 수치의 근거 ID는 유지한다. 과거 발송의 늦은 수집 또는 중복 병합으로 수치가 바뀌면 revised snapshot을 생성하고 차이를 표시한다. 이미 진행한 회의의 버전을 삭제하지 않는다.

불변성은 통상 운영상 수정 방지를 뜻한다. 개인정보 보존/삭제 요구가 있으면 기존 정책에 따라 원문을 처리하고 제한된 감사 메타데이터만 남긴다. “영원히 원문 삭제 불가” 정책을 신설하지 않는다.

### 8.6 수지 검산 예시 — 합성 데이터

기초 10건, 신규 6건, 재개 전이 1건, 제안 종료 전이 4건, 사람 제외 종료 전이 2건, 시스템 제거 전이 1건이면 기말은 `10+6+1−4−2−1=10`건이다.

한 match가 같은 주에 종료→재개→재종료되면 종료 전이는 2회여도 M-07 고유 처리량은 1건이다. 같은 사람에게 같은 포지션으로 LinkedIn과 사람인 두 번 발송하면 M-04=2, M-05=1, M-06=1이다. 하나의 메시지에 두 포지션을 명확히 제안했다면 M-04=1, M-05=1, M-06=2일 수 있다.

---

## 9. 서버/API 계약

실제 endpoint 명칭은 기존 v6 라우트와 충돌하지 않게 WU-01에서 확정한다. 아래는 필요한 기능 계약이며 새 서버 프레임워크를 도입하라는 뜻이 아니다.

### 9.1 읽기

- 목록: q, view, owner, opening, source, acquisition_method, outreach_channel, review_state, outreach_state, score_range, period, sort, cursor, page_size.
- 상세: match_id로 관측·평가·업무·발송·증빙의 권한 있는 기록을 반환.
- 지표: metric version + 기간 + 범위 + snapshot 식별자로 값과 coverage 반환.
- 지표 상세: metric_id + snapshot_id로 membership 결과를 페이지네이션.
- 동기화 상태: source/account별 범위·최종 성공·오류·진행 상태.

응답 공통: `data`, `next_cursor?`, `total_count?`, `as_of`, `scope`, `coverage`, `warnings`, `contract_version`.

period의 의미는 view별로 명확히 한다. 전체 기록은 observed_at 필터, 신규 업무는 enrolled_at, 실제 제안은 occurred_at, 백로그는 시점 상태다. 하나의 숨겨진 date 필터를 모든 지표에 무차별 적용하지 않는다. KPI 클릭은 그 지표 전용 기간 의미를 유지한다.

### 9.2 쓰기

검토/제외/보류/재개/담당자 변경은 `match_id + command_id + expected_version + action + reason/hold_until`을 받는 기존 권한 경로에 통합한다. 증빙 제출은 별도 claim으로 저장한다. `verified=true`를 일반 클라이언트가 직접 쓰는 endpoint는 없다.

v1 신규 후보자 발송 endpoint는 없다. 추후 명시적 승인으로 도입할 때 메시지 내용·수신자·채널·중복연락·거부 여부·권한·실발송 증빙을 다루는 별도 PRD/WU가 필요하다.

수동 동기화는 서버의 기존 job 예약 기능을 사용한다. command 중복은 같은 결과, version 충돌은 409, 인증 실패는 401, 권한 없음은 403, 유효성 오류는 422, 지원하지 않는 동작은 명시적 오류다. 오류를 빈 목록/성공 200으로 감추지 않는다.

### 9.3 성능 목표와 방법

합성 10,000매칭/50,000관측/30,000발송 규모의 지정된 시험 환경에서 첫 페이지 50행의 서버 응답 p95 2초 이내를 목표로 한다. 환경·쿼리·반복 횟수를 함께 기록한다. 달성했다고 주장하려면 실측이 있어야 한다.

기존 Postgres 인덱스와 검색 기능을 우선 쓴다. 느리면 실행계획으로 병목을 확인한 뒤 필요한 인덱스만 추가한다. 한글 검색에 적합한지 검증 없이 영어 FTS 설정을 도입하지 않는다. SQLite 검색을 웹 정본 검색의 대체물로 만들지 않는다.

---

## 10. 레거시 인수와 운영 전환

### 10.1 이관 순서

원본 스냅샷/백업 → 읽기 전용 인벤토리 → 샘플 드라이런 → 충돌/누락표 → 전체 드라이런 → 승인된 배치 편입 → readback/대조 → shadow 화면 → 허용된 운영 전환.

각 원천의 실제 단위를 확인한다. Supabase/SQLite에 JSON 원장이 45행 저장됐다는 사실이 후보 45명을 뜻하지 않을 수 있다. snapshot 1개 안의 후보 여러 명을 전개할 때 원본 ID와 내부 locator를 보존한다.

### 10.2 소스별 원칙

- v4/v5 DB: source_db/table/pk와 원래 시각·상태·점수·원문 hash 보존.
- 내부 보고메일: source mailbox/message ID + 본문 내 후보/포지션 locator로 분해. 추천/조건부 등 AI 판정은 원래 의미를 보존. 메일 날짜를 자동으로 서치 일시로 확정하지 않는다.
- 아카이브/로컬 JSON: manifest·schema·candidate 단위 여부 확인 후 공통 envelope로 변환.
- ClickUp: parent/subtask와 실제 candidate/opening의 관계 확인. 상태 complete를 검토 완료/발송 완료로 자동 변환하지 않는다.

같은 사건이 DB·메일·ClickUp에서 관측되면 원천 근거는 모두 보존하고 같은 정본 사건으로만 연결한다. 이름·제목·날짜가 비슷하다는 이유만으로 사건을 자동 병합하지 않는다.

### 10.3 대조표

원천별 원본 수 = 성공 변환 + 중복으로 연결 + 미연결/격리 + 정책상 제외 + 오류의 합으로 설명되어야 한다. 삭제해서 숫자를 맞추지 않는다.

필수 대조: distinct source key 수, distinct candidate 수, distinct match 수, assessment 수, verified outreach 수, occurred_at 누락, orphan FK, hash 충돌, 격리 사유. 서로 다른 단위를 1:1로 억지 비교하지 않는다.

### 10.4 전환과 되돌리기

운영 전환은 feature flag 또는 기존 라우트 전환 방식으로 작게 수행한다. v6 새 writer가 정본인 범위를 고정하고 v4/v5와 동시 이중 쓰기를 막는다. 구형 화면을 되돌리더라도 구형 writer를 자동 재활성화하지 않는다.

롤백은 먼저 읽기/UI/dispatcher를 이전 안전 상태로 돌린다. 신규 증빙 테이블을 DROP하거나 이관 행을 무조건 삭제하는 것을 기본 롤백으로 쓰지 않는다. 마이그레이션은 additive를 우선하고 복구 리허설을 한다.

구형 경로 제거는 새 경로의 신규 결과·과거 이력·권한·동기화가 검증되고, 최소 두 번의 완전 관측 주간 집계 대조가 끝난 뒤 별도 WU로 수행한다. 이 조건은 향후 실행 게이트이며 이번 문서 작성에서 수행한 일이 아니다.

---
## 11. WU 실행계획 — 34개 원자 단위

### 11.1 분할 판정

“DB 전체 구현”, “세 채널 연동”, “대시보드 전면 리팩터링”은 한 WU로 너무 크다. 이 계획은 데이터 의미/저장/전송/조회/화면/운영을 분리하고, 세 채널의 **로컬 구현과 실제 읽기 검증도 각각 분리**했다. WU가 많다는 것은 새 서비스나 DB를 많이 만든다는 뜻이 아니라, 변경·검증·되돌리기 경계를 작게 잡는다는 뜻이다.

각 WU는 제품 불변식 한 묶음, 작은 변경 표면, 독립 인수조건과 rollback을 가져야 한다. 기본 목표는 직접 작성 생산 코드 300줄 이하, 테스트 포함 직접 작성 diff 700줄 이하, 직접 수정 코드 파일 6개 이하다. 이것은 리뷰 목표이며 줄수를 맞추려고 함수/테스트를 숨기거나 압축하지 않는다. 저장소 기존 상한이 더 엄격하면 그것을 따른다.

다음 하나라도 맞으면 **코딩 전** 자식 WU로 다시 나눈다: 다른 외부 시스템을 동시에 변경, 서로 독립적인 두 실패/복구 경계, 예상 diff 초과, 두 개 이상의 새 원천 포맷, 인증체계나 평가모델 변경 필요. 자식 WU는 부모 요구/AC를 그대로 상속하고 새 업무 의미를 추가하지 않는다. 특히 WU-23은 원천 포맷 수를 인수 단계에서 확정하며, 포맷이 여러 개면 format별 자식 WU로 쪼갠다.

기존 구현이 이미 충족하는 WU는 재사용/회귀 증거를 남기고 `LOCAL_PASS, no_code_change=true`로 처리할 수 있다. WU 숫자를 채우기 위해 중복 구현하지 않는다.

처음 요청하는 실행은 **WU-00만**이다. 이 문서를 받았다는 이유로 전체 WU를 한 세션에서 구현/배포하지 않는다. 현재 승인된 실행 범위가 한 WU라면 완료 보고 후 다음 WU로 자동 진행하지 않는다.

### 11.2 공통 작업 절차

`작업 범위/기반 SHA 고정 → 실패 테스트 RED → 최소 구현 GREEN → 관련 회귀 → 반례 검증 → diff/보안 검토 → 인수 증거 → 승인된 로컬 커밋/후속 단계`

별도 worktree를 사용하되 기존 dirty 작업을 reset/stash/강제 checkout하지 않는다. 정확한 기반 SHA와 테스트 명령은 WU-00에서 확정한다. 과거 예시 SHA를 붙여넣지 않는다. 새 세션은 SOT 전체의 핵심 규칙과 현재 WU 카드를 읽고, 그 WU의 필요한 파일만 추가로 읽는다.

상태는 `NOT_STARTED / READY / IN_PROGRESS / LOCAL_PASS / STAGING_VERIFIED / LIVE_VERIFIED / BLOCKED / FAIL`로 구분한다. LOCAL_PASS는 외부 연동 성공이 아니다. 문서/계약만인 WU-00/01은 실제 저장소 증거/계약 검사 완료로 LOCAL_PASS를 판정한다.

권한 게이트: 로컬 문서/코드/합성시험, 허용된 read-only 조사, staging 쓰기, 운영 migration, 운영 bulk 편입, 배포, scheduler 등록, 내부 실메일 각각을 구분한다. 후보자 실제 메시지 발송은 이 계획의 승인 대상에 포함되지 않는다. push/PR도 AGENTS와 사용자 승인 범위를 따른다.

기본 병렬화는 하지 않는다. WU-10/11/12는 WU-09 계약이 고정되고 서로 다른 worktree/어댑터 파일을 쓸 때만 병렬화할 수 있다. 공통 schema/enum/registry 변경은 부모 WU에 반영한 뒤 다시 기반을 맞춘다. DB writer/운영 수집은 같은 계정을 두 에이전트가 동시에 변경하지 않는다.

검증자는 가능한 새 맥락에서 계약·diff·시험을 읽는다. 독립 검증 도구가 실행되지 않았으면 NOT_RUN/BLOCKED로 표시하고 수행했다고 쓰지 않는다. 기존 strict workflow가 요구하는 검증을 우회하지 않는다. 목표 없는 검증 라운드를 무한히 추가하지 않는다.

### 11.3 WU별 카드

#### WU-00 — 기존 구현·실행 경로 인수

- 선행: 없음.
- 범위/산출물: AGENTS/SOT, 현재 worktree·dirty 파일·동시 작업, v6 기준 SHA, 관리자 URL의 실제 배포 경로, v4/v5/v6의 읽기/쓰기 주체, DB/SQLite schema와 기존 스케줄러를 읽기 전용으로 매핑한다. 결과는 현황표·충돌표·재사용표·권한표·테스트 실행 명령이다.
- 인수/반례: 각 확인 항목에 저장소 경로:줄 또는 허용된 read-only 조회 결과를 붙인다. 미확인은 NOT_VERIFIED로 남긴다. 특히 후보 단위 행인지 JSON snapshot인지, 동일 이름 테이블이 같은 의미인지 확인한다.
- 비범위/중단: 기반 브랜치 또는 정본 DB 권한이 불명확하면 관련 물리 변경을 차단한다. 연결이 없는 사실과 데이터가 없는 사실을 구분한다. 코드·스키마·메일·스케줄러 변경은 0건.
- 되돌리기: 읽기 전용. 생성한 인수 문서만 되돌릴 수 있다. 사용자 작업 파일은 건드리지 않는다.

#### WU-01 — 제품 계약·물리 매핑·합성 fixture 고정

- 선행: WU-00.
- 범위/산출물: 규칙 R-01~16, 데이터 nullable/고유키/상태, M-01~12, API 의미, 실제 테이블 매핑을 계약 파일에 등록한다. 기존 계약과 중복되는 규칙은 참조한다. 최소 합성 fixture와 기대값을 만든다.
- 인수/반례: 금지 상태·누락 키·유효 점수 0과 unscored null·내부 보고와 후보 제안 구분을 계약 시험에서 확인한다. 논리 엔터티마다 reuse/extend/new와 이유가 한 가지로 결정된다.
- 비범위/중단: 기존 SOT와 충돌한 항목의 의미를 구현자가 임의 확정하면 FAIL. DDL·UI·포털 어댑터 구현은 제외.
- 되돌리기: 문서/계약 변경만 되돌린다. 운영 데이터는 없다.

#### WU-02 — 후보자·채용 건 식별과 연결

- 선행: WU-01.
- 범위/산출물: 기존 candidate/opening ID를 재사용하는 작은 resolver를 구현한다. 확정 alias와 미해결/가능 중복을 구분한다. 자동 fuzzy merge를 만들지 않는다.
- 인수/반례: 동명이인 분리, 같은 제목의 다른 채용 건 분리, 검증된 다중 프로필 통합, 미확정 RPS↔공개 URL 연결 격리를 통과한다.
- 비범위/중단: 원천 ID 범위를 모르거나 기존 resolver와 책임이 겹치면 관련 연결만 BLOCKED. 병합 UI/대규모 정리 제외.
- 되돌리기: 신규 resolver 호출을 해제한다. 기존 후보 ID를 재발급하지 않는다.

#### WU-03 — 실행·관측 저장 경계

- 선행: WU-01.
- 범위/산출물: SearchRun·SearchObservation의 기존 저장소 확장과 로컬/시험 Postgres migration을 만든다. 상태·원천키·시각·FK/UNIQUE·접근권한을 다룬다.
- 인수/반례: 재시도 같은 관측 1건, 같은 키 다른 payload conflict, cancelled/failed 분리, timestamp 누락 보존, 권한 없는 읽기/쓰기 거부를 실제 시험 DB에서 검증한다.
- 비범위/중단: 기존 테이블을 복제하거나 운영 migration을 실행하면 FAIL. Match/점수/Outreach/UI는 제외.
- 되돌리기: 시험 DB에서 additive migration 복구 시험. 운영 DROP 문을 기본 rollback으로 제안하지 않는다.

#### WU-04 — 매칭·평가 저장 경계

- 선행: WU-02, WU-03.
- 범위/산출물: Match·Assessment의 고유키, 버전·nullable 점수·근거 참조·현재 투영을 기존 객체에 확장한다. operational_intent와 legacy 점수 보존을 포함한다.
- 인수/반례: 동일 후보×opening의 여러 run이 1 match, 서로 다른 opening은 2 match, 재평가 이력 보존, JD 버전 변경 경고, score 0/null 구분을 검증한다.
- 비범위/중단: 기존 점수 함수 변경 또는 LLM 새 호출 경로를 추가하면 FAIL. 외부 발송·새 전체 프로필 DB 제외.
- 되돌리기: 새 투영의 읽기를 중단하고 원천 이력은 유지한다.

#### WU-05 — AIsearch 결과 수신·저장 hook

- 선행: WU-04.
- 범위/산출물: 현재 실제 producer에서 공통 envelope를 받아 검증·중복 제거·관측/평가 저장·허용된 업무 편입 예약·보고 예약을 수행하는 단일 저장 경계를 연결한다.
- 인수/반례: 실제 producer의 가짜 결과를 기존 호출 경로로 넣었을 때 DB 재조회가 일치한다. 중간 실패에서 반쪽 결과/중복 예약 0건. JSON snapshot 속 후보별 locator가 유지된다.
- 비범위/중단: 새 AIsearch 엔진을 작성하거나 기존 생산 경로를 그대로 둔 미사용 저장 함수만 만들면 FAIL. 운영 호출 제외.
- 되돌리기: producer hook feature flag를 끈다. 기존 결과 생성은 보존한다.

#### WU-06 — SQLite 원장·outbox 내구성

- 선행: WU-01.
- 범위/산출물: 기존 로컬 원장의 결과와 outbox를 한 트랜잭션으로 저장하는 최소 확장을 한다. schema_version, operation_id, bounded busy retry, 재시작 복구를 구현한다.
- 인수/반례: 강제 중단/롤백/재시작 이후 유실 없음, 중복 operation 1건, foreign_keys 활성화, 두 writer 충돌 시 거짓 성공 없음.
- 비범위/중단: 원격 전송·웹 정본 검색·공유 SQLite 서버화 제외. 디스크/권한 오류를 성공으로 처리하면 FAIL.
- 되돌리기: 기존 로컬 쓰기 경로로 복구하되 outbox와 원장은 보존한다.

#### WU-07 — 중앙 동기화·readback·충돌 처리

- 선행: WU-05, WU-06.
- 범위/산출물: 로컬 outbox를 기존 서버 수신 경계로 전달하고 ID·핵심필드·정규 hash를 readback한 뒤 ACK한다. 순서가 뒤집힌 재수집과 제한된 재시도를 다룬다.
- 인수/반례: 중앙 commit 후 ACK 유실을 재현해도 정본 1건. 한쪽 실패에서 synced 금지. 오래된 관측이 최신 검증 투영을 덮어쓰지 않음.
- 비범위/중단: 새 큐 서비스/양방향 멀티마스터/무조건 overwrite 제외. 충돌 기록을 지워 재시도하면 FAIL.
- 되돌리기: 동기화 consumer 정지. 미처리 outbox 보존; 기존 중앙 데이터 삭제 없음.

#### WU-08 — 내부 보고메일 동일 snapshot 연결

- 선행: WU-05.
- 범위/산출물: 기존 메일 렌더러/dispatcher를 저장된 report snapshot에 연결한다. 제목 접두사, 수신자 allowlist, 웹 링크, report ID, 전송/라벨 상태를 보존한다.
- 인수/반례: 웹 투영과 메일의 후보·포지션·평가 버전 일치. DB 실패 시 전송 0회, 전송 후 ACK 유실 시 조회 후 보류/복구, 내부 보고가 제안 KPI 0건. 외부 호출은 fake adapter로 시험한다.
- 비범위/중단: 실제 메일 발송은 별도 승인 전 금지. 자동 재전송으로 불확실한 성공을 덮으면 FAIL.
- 되돌리기: 새 dispatcher만 중지한다. 기존의 승인된 보고 기능을 무조건 삭제하지 않는다.

#### WU-09 — 발송 증거·메시지/매칭 연결 계약 구현

- 선행: WU-01, WU-02.
- 범위/산출물: 기존 outreach 원장/연결 객체를 재사용하거나 최소 확장한다. typed evidence, verification revision, 채널/계정/수신자 키, 미연결 사건, pure status reducer를 구현한다.
- 인수/반례: 내부 메일/클릭/수동주장으로 verified 불가, 모호한 포지션 연결 금지, 메시지 1건↔2매칭 구분, 증거 충돌/검증 취소 보존, 권한 없는 verified 쓰기 거부.
- 비범위/중단: 실제 포털 접근과 전송 제외. 범용 이벤트 플랫폼을 만드는 것도 제외.
- 되돌리기: 새 발송 투영을 끄되 수집 원문 참조와 검증 이력은 유지한다.

#### WU-10 — 사람인 이력 어댑터 — 로컬

- 선행: WU-09.
- 범위/산출물: 강상모의 사람인 계정 범위를 확인할 수 있는 기존 경로에 읽기 전용 parser/adapter를 연결한다. 페이지·계정·발송시각·제안 ID·수신자·포지션·coverage를 변환한다.
- 인수/반례: 비식별 실제 구조 fixture로 발송/미발송 관측/로그인 만료/부분 페이지/중복 페이지/포지션 미확인을 검사한다. live_verified는 아직 false다.
- 비범위/중단: 발송 API/버튼 클릭, 로그인 우회, 무한 탐색 제외. 이용량 합계만 있으면 후보별 추적은 BLOCKED로 표시.
- 되돌리기: 이 채널 수집기만 비활성화. 다른 채널 로컬 작업은 계속한다.

#### WU-11 — 잡코리아 이력 어댑터 — 로컬

- 선행: WU-09.
- 범위/산출물: 강상모의 잡코리아 계정 범위와 기존 이용 권한을 기준으로 읽기 전용 이력 변환을 구현한다. 잔여 이용권 집계와 실제 후보별 제안을 분리한다.
- 인수/반례: 발송 내역/계정 불일치/미결제·권한 오류/페이지 누락/시각 없는 사건을 fixture로 검증한다. 접근 실패에서 0건 미발송으로 반환하지 않는다.
- 비범위/중단: 이용권 구매·권한 변경·실제 제안 전송 제외. 기존 수집기를 복제하지 않는다.
- 되돌리기: 이 채널만 중지하고 마지막 성공 범위와 차단 사유를 보존한다.

#### WU-12 — LinkedIn 이력 어댑터 — 로컬

- 선행: WU-09.
- 범위/산출물: 기존 허용된 Recruiter/RPS/InMail 읽기 경로를 사용한다. seat/계정·실제 발신자·수신자·메시지 유형·포지션·상태를 분리한다.
- 인수/반례: 메시지 탭만 존재/연결요청/pending InMail/다른 담당자 발신/본문 비공개/동일 후보 다중 포지션을 fixture로 검증한다.
- 비범위/중단: 비공식 API를 새로 가정하거나 자동 브라우저 탐색을 확대하지 않는다. 공개 ID와 RPS ID를 추정 병합하면 FAIL.
- 되돌리기: LinkedIn adapter만 비활성화한다. 다른 채널의 성공 상태는 유지한다.

#### WU-13 — 업무 상태·결정 이력·동시성

- 선행: WU-04, WU-09.
- 범위/산출물: WorkEvent와 현재 투영의 최소 reducer/저장 command를 구현한다. enrolled/검토/보류/제외/발송 종료/재개/담당 변경/시스템 제거, version 충돌을 다룬다.
- 인수/반례: 보류 백로그 유지, 시스템 제거 성과 제외, 재검색 재편입 금지, verified 발송 전 종료 금지, 동시 두 사용자 변경에서 409, 중복 command 1회 반영.
- 비범위/중단: UI 구현·후보자 전송 제외. 현재 상태 하나만 저장해 과거 주간을 역산하면 FAIL.
- 되돌리기: 새 command를 차단하고 append 이력은 유지한다. 무조건 역이벤트 생성은 하지 않는다.

#### WU-14 — 주간 사건 지표

- 선행: WU-05, WU-08, WU-09, WU-13.
- 범위/산출물: M-01/02/04/05/06/12의 공통 기간·권한·원천 범위 query를 구현한다. 내부보고/고유인물/매칭/전송을 다른 지표로 반환한다.
- 인수/반례: 일요일 KST 경계, 발생일과 이관일 차이, 동일인 다중 채널, 메시지 다중 포지션, 수동주장/연결요청 제외를 고정 expected 값으로 검증한다.
- 비범위/중단: 업무 백로그·그래프 UI·주차 offset 보정 제외. 클라이언트 임의 합산으로 총수를 만들면 FAIL.
- 되돌리기: 새 지표 노출을 차단한다. 기존 Weekly 계약은 별도 승인 없이 교체하지 않는다.

#### WU-15 — 백로그·처리량·수지 지표

- 선행: WU-13, WU-14.
- 범위/산출물: M-03/07/08/09/10/11을 event시점 기준으로 계산한다. 고유 처리 업무와 상태 전이 횟수를 분리하고 사유별 수지를 제공한다.
- 인수/반례: 종료→재개→재종료, 보류, 시스템 정리, 발신자/검토자 불일치, 분모0, 오래된 이력 누락을 검증한다. 수지 공식과 상태 재생 결과가 동일하다.
- 비범위/중단: 가동률/시간당 생산성/매출액 추정 제외. 이벤트 수를 고유 처리량으로 쓰면 FAIL.
- 되돌리기: 해당 지표만 숨기고 사건 데이터와 기존 지표는 유지한다.

#### WU-16 — Weekly snapshot·동일 근거 드릴다운

- 선행: WU-14, WU-15.
- 범위/산출물: 기존 스냅샷 객체에 버전·수집 범위·membership·보정 이력을 연결한다. 카드·그래프·상세가 같은 snapshot으로 조회되게 한다.
- 인수/반례: 스냅샷 후 늦은 발송 수집 시 기존 버전 유지/새 버전 차이 표시, 카드 N=드릴다운 고유 N, 후보 이름 갱신이 과거 membership을 변경하지 않음을 확인한다.
- 비범위/중단: 새 데이터웨어하우스/모든 임의 검색의 영구 스냅샷 시스템 제외.
- 되돌리기: 새 snapshot reader를 해제한다. 기존 회의 자료는 삭제하지 않는다.

#### WU-17 — 목록·검색·상세 읽기 API

- 선행: WU-04, WU-09, WU-13.
- 범위/산출물: 기존 서버에 권한 있는 전역검색·필터·정렬·cursor·상세를 연결한다. 7컬럼 DTO와 null/오류/coverage 계약을 지킨다.
- 인수/반례: 501번째 이후 후보 검색, 동점/동일시각 pagination, q 특수문자/한글·영문, total_count와 권한 필터, 미인증/비소속 사용자 거부.
- 비범위/중단: 화면에 로드한 배열 필터만으로 전역검색 구현 또는 비공개 원문 전체 브라우저 전송은 FAIL.
- 되돌리기: 새 route를 끄고 기존 read 경로를 유지한다.

#### WU-18 — 후보자 표·간결한 요약

- 선행: WU-17.
- 범위/산출물: 기존 관리자 UI의 7컬럼 표를 구현하고 칸반 컬럼을 제거한다. 점수+근거 통합, 3줄 프로필, 발송 배지, stale/unknown/legacy 표시를 다룬다.
- 인수/반례: 긴 학력·경력, 실제0점/미분석, 100점 근거부족, 이름없음, 다중채널의 화면 fixture와 1440/1024 폭 검증. 핵심값은 줄임으로 잃지 않고 상세로 접근 가능.
- 비범위/중단: 새 디자인시스템·점수함수 변경·다른 Kanban 메뉴 삭제 제외.
- 되돌리기: 표 feature flag를 돌린다. 데이터는 바꾸지 않는다.

#### WU-19 — 상세 패널·검토 행동

- 선행: WU-18, WU-13.
- 범위/산출물: 상세 타임라인·평가 근거·채널 증거와 검토/보류/제외/담당 변경을 연결한다. URL 직접 진입·키보드·409 충돌 화면을 포함한다.
- 인수/반례: 발송 완료 수동 조작 없음, claim은 검증대기, 미권한 증빙 차단, 다른 사용자의 최신 결정을 덮지 않음, 패널 닫기/재진입 상태 보존.
- 비범위/중단: 원문 무제한 공개·실제 제안 발송 버튼·새 활동 CRM 제외.
- 되돌리기: 행동 버튼을 비활성화하고 읽기 상세만 남길 수 있다.

#### WU-20 — 필터·프리셋·URL 상태

- 선행: WU-18, WU-17.
- 범위/산출물: 기간 의미, 담당자/포지션/채널/발송상태 필터, 저장 프리셋, 페이지·정렬을 URL state로 연결한다. 서버 조건을 그대로 사용한다.
- 인수/반례: 뒤로가기/직접URL/새로고침의 같은 조건, q 변경 시 cursor 초기화, unknown 점수가 높은점수 필터에 섞이지 않음, KPI scope 전달 보존.
- 비범위/중단: 전역검색엔진 교체·지표 공식 재구현 제외.
- 되돌리기: 새 프리셋만 제거해도 기본 목록 API는 유지된다.

#### WU-21 — 운영 카드·4주 그래프

- 선행: WU-16, WU-18, WU-20.
- 범위/산출물: 신규/검토/제안/백로그/노후화 카드와 마감4주 그래프·클릭 드릴다운을 연결한다. 소스별 부분관측과 현재주 배지를 표시한다.
- 인수/반례: 카드·막대·드릴다운의 snapshot/기간/단위 동일, 부분주0과 확정0 구분, 현주 포함 옵션, chart 접근성 및 빈 데이터 표시.
- 비범위/중단: 프론트엔드 별도 KPI 계산·가공 수익 예측·월요일 주간 재도입은 FAIL.
- 되돌리기: 신규 카드/그래프만 숨긴다. 원장 조회는 유지한다.

#### WU-22 — v4/v5 DB 이관 변환기

- 선행: WU-02, WU-05.
- 범위/산출물: 확인된 구형 원천 schema에서 공통 envelope로 변환하는 재실행 가능한 dry-run importer를 작성한다. 원천 PK·원시상태·원래시각·legacy점수를 보존한다.
- 인수/반례: 두 번 읽어 같은 정본 수, unknown0 구분, orphan/오류 격리, 원본 수 분해표, imported_at의 주간 실적 편입 0건.
- 비범위/중단: 운영 bulk write·원본 삭제·다른 schema 추정 파싱 제외. v4/v5 스키마가 다르면 파일/fixture를 분리하되 공용 규칙 복제 금지.
- 되돌리기: 변환 결과는 시험 공간에서만 제거 가능. 원본 DB는 읽기 전용 유지.

#### WU-23 — 내부메일·snapshot 편입 변환기

- 선행: WU-05, WU-08, WU-22.
- 범위/산출물: 검증된 내부 보고 포맷/structured snapshot을 common envelope로 편입한다. 메일/문서 내부 후보 locator, unknown 검색시각, 원천 간 연결을 보존한다.
- 인수/반례: 보고 한통의 후보 여러명 분리, 다중 포지션 보존, 원본 snapshot행 수와 후보 수 구분, 내부메일 발송→제안 0, parse 모호성을 자동 성공시키지 않음.
- 비범위/중단: 모든 역사적 메일의 만능 LLM 파서·실제 재발송·본문 원문 git 저장 제외. 포맷이 여러 개면 구현 전 포맷별 자식 WU로 분할한다.
- 되돌리기: 시험 편입만 되돌린다. 원문/보고메일은 삭제하지 않는다.

#### WU-24 — 수동·정기 수집 조정 경로

- 선행: WU-07, WU-10, WU-11, WU-12, WU-17.
- 범위/산출물: 기존 scheduler에 붙일 동일한 매시간/수동 handler를 구현한다. 계정·원천별 lock/cursor/최종성공/오류/coverage를 기록한다. 등록은 하지 않는다.
- 인수/반례: 수동과 자동 동시호출의 중복실행 없음, 완료 cursor 이후 중복제거, 실패 시 last_success 불변, 페이지 새로고침 외부효과0.
- 비범위/중단: 별도 daemon·클라우드 큐·브라우저 setInterval 정본화·운영 cron 등록 제외.
- 되돌리기: 새 handler 라우팅을 끈다. cursor와 마지막 성공 영수증은 보존한다.

#### WU-25 — 교차 경계 실패·회귀 시험

- 선행: WU-08, WU-16, WU-19, WU-20, WU-21, WU-22, WU-23, WU-24.
- 범위/산출물: 실제 기존 entrypoint에서 producer→저장→보고예약→조회→업무→발송이력→Weekly를 합성/허용된 비식별 fixture로 시험한다. 장애 지점을 강제로 넣는다.
- 인수/반례: §12 인수조건의 기능·중복·시각·불명·강제중단 반례 통과. 실제 호출 경로를 통과하고 미사용 mock-only 구현이 아님을 증명한다.
- 비범위/중단: 결함 수정과 무관한 전면 refactor 제외. 핵심 실패를 xfail/skip으로 돌려 PASS하면 FAIL.
- 되돌리기: 테스트 전용 변경만 제거 가능. 발견한 결함은 해당 소유 WU로 돌린다.

#### WU-26 — 권한·증빙 노출·성능 검증

- 선행: WU-25, WU-17, WU-19, WU-21.
- 범위/산출물: 기존 schema/API에서부터 시행한 RLS 시험을 다시 통합 검증한다. 미인증/비소속/일반권한/서버역할의 데이터·count·뷰·RPC·증빙 URL과 검색 부하를 검사한다.
- 인수/반례: 개인정보/키 브라우저노출0, 임의 verified쓰기0, count/facet 누출0, §9.3 환경에서 성능 측정 및 query plan 근거. 달성하지 못한 목표는 수치와 원인을 보고한다.
- 비범위/중단: RLS 우회·공개 전환으로 성능을 맞추거나 성능 수치를 만들어내면 FAIL. 새로운 부하 인프라 도입 제외.
- 되돌리기: 부하시험 데이터만 안전하게 정리한다. 권한을 완화하는 rollback 금지.

#### WU-27 — 격리 환경 인수·복구 리허설

- 선행: WU-25, WU-26.
- 범위/산출물: 허용된 staging에서 migration/producer/저장/readback/UI/Weekly/백업·복구를 검증한다. 내부메일은 fake 또는 별도 승인한 본인수신 시험만 사용한다.
- 인수/반례: 변경 SHA·migration version·계약 hash·배포 환경·AC 결과·rollback 영수증이 묶인다. 로컬 통과와 staging 통과를 구분한다.
- 비범위/중단: 운영 채널의 새 후보자 연락은 금지. staging 자격증명이 없으면 BLOCKED이며 local_pass를 live로 승격하지 않는다.
- 되돌리기: 리허설대로 이전 앱 버전/flag를 복구하고 증거는 보존한다.

#### WU-28S — 사람인 라이브 읽기 검증

- 선행: WU-27, WU-10.
- 범위/산출물: 권한이 확인된 강상모 계정에서 기존 발송이력 표본을 읽어 중앙 기록·웹까지 대조한다. 후보자 신규 발송은 없다.
- 인수/반례: 계정·원천사건·수신자·발송시각·포지션·readback·웹 증빙·coverage 영수증을 남긴다. 실제 해당 포지션 증거가 없으면 그 연결은 미확인이다.
- 비범위/중단: 권한/결제/로그인 challenge 또는 안정적인 이력 식별 불가 시 해당 채널 BLOCKED. 다른 채널 성공을 복제하지 않는다.
- 되돌리기: 해당 collector만 정지하고 검증한 과거 사건은 보존한다.

#### WU-28J — 잡코리아 라이브 읽기 검증

- 선행: WU-27, WU-11.
- 범위/산출물: 권한이 확인된 강상모 잡코리아 계정의 과거 발송 이력을 같은 절차로 읽고 대조한다.
- 인수/반례: 후보자별 실제 이력과 수집 범위가 일치한다. 이용량 합계만 확인한 것을 후보별 추적완료로 판정하지 않는다.
- 비범위/중단: 수집 불가이면 blocked/partial을 그대로 남긴다. 구매/발송 등 부수효과 없음.
- 되돌리기: 이 collector만 중지하고 마지막 성공 상태는 유지한다.

#### WU-28L — LinkedIn 라이브 읽기 검증

- 선행: WU-27, WU-12.
- 범위/산출물: 허용된 seat/계정에서 기존 메시지·InMail을 읽어 발신자/수신자/포지션 연결을 검증한다.
- 인수/반례: 메시지 탭 숫자가 아닌 실제 사건 증거, 타 담당자 발신 분리, 공개/RPS identity 근거, 원장·웹의 동일성 확인.
- 비범위/중단: 비공개 본문/권한/계정 불일치이면 관련 연결 BLOCKED. 신규 연결요청/InMail 0회.
- 되돌리기: LinkedIn 수집기만 중단한다. 다른 원천의 verified 상태를 변경하지 않는다.

#### WU-29 — 승인된 운영 스키마·데이터 편입

- 선행: WU-27.
- 범위/산출물: 운영 쓰기 승인이 있는 경우에만 백업 후 additive migration과 checkpointed 이관을 실행한다. 범위·배치·중단 기준을 사전에 적고 readback으로 대조한다.
- 인수/반례: 원천수 분해표 일치, orphan/hash conflict 격리, 구형 writer 이중쓰기 없음, 신규업무/제안 실적 부풀림0, 배치 재개 안전.
- 비범위/중단: 승인·백업·복구 증거 없으면 NOT_AUTHORIZED. DROP/무조건 전체 overwrite/공유자원 광범위 변경 금지.
- 되돌리기: writer를 멈추고 읽기/UI 전환을 되돌릴 수 있다. 새 증거 원장 삭제로 rollback하지 않는다.

#### WU-30 — 운영 화면·스케줄러 점진 전환

- 선행: WU-29.
- 범위/산출물: 배포/스케줄러/내부보고의 각각 명시된 승인 범위 안에서 feature flag를 열고 정기/수동 경로를 검증한다. 채널별 실제 검증 상태를 그대로 노출한다.
- 인수/반례: 배포 SHA, 인증/권한, 신규 결과 웹 반영, 수동/자동 같은 범위, 내부메일 동일 snapshot, 위클리 동일근거, rollback 조작 증거. 세 채널 전체완료 표시는 WU-28S/J/L이 모두 LIVE_VERIFIED일 때만 가능.
- 비범위/중단: 한 채널 미검증이면 제품 전체완료 선언 금지. 부분 출시는 범위를 명시한 별도 승인 아래 가능하며 채널이 초록으로 위장되지 않아야 한다.
- 되돌리기: 읽기 flag와 dispatcher/scheduler를 단계적으로 중지. 이전 writer를 자동 재활성화하지 않는다.

#### WU-31 — 관측 후 구형 경로 축소

- 선행: WU-30, WU-28S, WU-28J, WU-28L.
- 범위/산출물: 최소 두 번의 완전 관측 주간 대조와 인수승인 후 사용하지 않는 구형 read/write 경로만 제거한다. 이력·증거는 유지한다.
- 인수/반례: 참조/호출 추적상 새 경로 사용, 운영지표 대조, 회귀 통과, 복구 가능성, 삭제 대상이 실제 미사용이라는 근거.
- 비범위/중단: 조건이 충족되기 전 제거 금지. 전면 저장소 청소·다른 브라우저/매칭 작업 제거 제외.
- 되돌리기: 코드 경로 복구만 가능하게 유지하고 DB 이력은 보존한다.

### 11.4 실제 WU 착수 카드의 필수 항목

각 실행 시 아래를 한 카드에 작성한다. 문서만 길게 늘리지 말고 해당 WU에 필요한 값만 채운다.

```text
WU ID / SOT 버전 및 hash / 기반 SHA / worktree
한 문장 목표 / 이번에 보장할 규칙 ID
수정 허용 파일 / 읽기 참조 파일 / 변경 금지 파일
재사용 함수·테이블 / 입력·출력·오류·권한
선행 WU 상태 / 미확인 가정 / 예상 변경 규모
RED 재현 명령과 기대 실패 / GREEN 명령과 기대값
회귀 범위 / 공격적 반례 / 외부효과 허용 범위
인수 증거 저장 위치 / rollback / stop 조건
결과: 실제 변경, 실행한 시험, 미실행 시험, 남은 위험, 다음 WU
```

실행 완료 보고는 `결론 → 사용자에게 필요한 결정 최대 2개 → 변경/시험/미실행 증거` 순서로 한다. “테스트 통과”만 쓰지 말고 테스트 수집 개수·명령·exit code·실패/skip 수를 기록한다. 시험 0개 수집은 PASS가 아니다.

---

## 12. 인수조건과 적대적 반례

아래는 테스트해야 할 계약이다. 이 문서를 작성한 시점에 실제 애플리케이션에서 통과했다고 주장하는 결과표가 아니다. 각 AC는 구현 WU의 RED/GREEN/회귀 증거와 연결한다.

| ID | 시험 입력/반례 | 기대 결과 | 주 소유 WU |
|---|---|---|---|
| AC-01 | 같은 AI 결과를 3회 저장 | 같은 원천 사건/매칭 1건, 중복 보고 예약 없음 | 03~08 |
| AC-02 | 같은 후보·같은 opening을 새 run으로 검색 | match 1개, run/관측 이력만 증가 | 04~05 |
| AC-03 | 같은 후보·다른 opening | match 2개, 고유 후보 1명 | 02~04 |
| AC-04 | 이름이 같은 다른 두 후보 | 정체성 근거 없으면 분리 유지 | 02 |
| AC-05 | 공개 LinkedIn URL과 RPS ID 관계 미확인 | 자동 병합 금지, possible_duplicate | 02,12 |
| AC-06 | 미분석/평가오류/실제 0점 | null/실패/0을 각각 다르게 저장·표시 | 01,04,18 |
| AC-07 | 프로필 근거 없는 레거시 100점 | 숫자 원본 보존, legacy 경고, 검증점수로 승격 안 함 | 04,18,22 |
| AC-08 | 501번째 이후의 이름 검색 | 전체 DB 검색에서 조회됨 | 17,20 |
| AC-09 | 내부 보고메일에 “추천 100명” | 내부 보고만 증가, 후보제안/고객사추천 0 | 08,09,14,23 |
| AC-10 | 포털 발송 버튼 클릭만 기록 | verified 불가 | 09~12 |
| AC-11 | 사용자 수동 “보냈음” 입력 | claim/검증대기, 확인된 제안 KPI 제외 | 09,19 |
| AC-12 | 메시지 탭/크레딧 변화만 존재 | 후보·포지션별 발송 확정 불가 | 10~12 |
| AC-13 | 같은 provider message를 다시 수집 | 동일 outreach 1건 | 09~12 |
| AC-14 | 후보 1명·opening 1개·채널 2개 발송 | 전송 2, 인원 1, 최초제안매칭 1 | 09,14 |
| AC-15 | 메시지 1개에 명시된 opening 2개 | 전송 1, 인원 1, 확인된 매칭 2 | 09,14 |
| AC-16 | 후보는 맞지만 어느 포지션인지 모름 | 사건 보존, match 발송 확정/KPI 편입 금지 | 09~12 |
| AC-17 | 포털/Gmail 권한 만료 | blocked/unknown, 미발송 0으로 위장 안 함 | 10~12,24 |
| AC-18 | 목록 첫 페이지만 수집 | partial, 전체 범위 완료 금지 | 10~12,24 |
| AC-19 | 다른 담당자가 보낸 메시지 | 실제 발신자 귀속, 강상모로 자동 귀속 금지 | 12,14 |
| AC-20 | 제안 후 bounce 또는 거절 응답 | 발송 사건 유지, 전달/응답 상태 별도 | 09,14 |
| AC-21 | 같은 업무를 종료→재개→재종료 | 고유처리 1, 종료전이 2, 수지 일치 | 13,15 |
| AC-22 | 검토대기를 보류로 이동 | 총 백로그 불변, 단계별 값만 변경 | 13,15 |
| AC-23 | 시스템 중복 제거/포지션 종료 | 시스템 조정, 사람 처리실적 제외 | 13,15 |
| AC-24 | 두 사용자가 같은 version에 변경 | 한 변경만 반영, 다른 요청 409 | 13,19 |
| AC-25 | 처리율 분모0 | null/대상없음; 0%나100% 임의 표시 금지 | 15,21 |
| AC-26 | 일요일 00:00 KST 경계 사건 | 앞 주 제외/해당 주 포함, UTC 변환 일치 | 14~16 |
| AC-27 | 오래전 발송을 오늘 이관 | 당시 발송주 대상, 오늘 제안/신규업무로 세지 않음 | 14,22~23 |
| AC-28 | occurred_at 없는 발송 사건 | 실제발송 상태와 별개로 주간 시간확인 KPI 제외 | 09,14 |
| AC-29 | snapshot 생성 후 지연수집·identity병합 | 이전 버전 보존, 새 버전과 차이 표시 | 16 |
| AC-30 | 카드·그래프·드릴다운 조회 | 같은 snapshot·범위·단위·membership | 16,21 |
| AC-31 | DB 성공 후 ACK 전에 프로세스 중단 | 재시도해 중앙 반영 1건, readback 후 synced | 06~07 |
| AC-32 | Gmail 전송 성공 가능/응답 또는 ACK 유실 | 조회로 조정; 불확실할 때 무조건 재전송 없음 | 08 |
| AC-33 | 자동/수동 동기화 동시 실행 | 같은 scope의 중복실행/중복사건 없음 | 24 |
| AC-34 | 미인증·다른 조직 사용자·직접 RPC | 데이터/count/facet/증빙 유출 없음 | 03~04,09,17,26 |
| AC-35 | 일반 클라이언트가 verified 직접 쓰기 | 서버/DB 권한 검사 거부 | 09,26 |
| AC-36 | 원문·프로필에 명령문/HTML 포함 | 데이터로만 처리, 스크립트 실행·도구호출·점수조작 없음 | 05,08,17~19 |
| AC-37 | 한 run 부분실패/취소/오래된 대기 | partial/cancelled/waiting 구분, 일괄 실패·완료 아님 | 03,18,24 |
| AC-38 | 새 요약 표시 적용 전후 평가 | 같은 평가 입력의 기존 점수 결과 불변 | 04,18,25 |
| AC-39 | 레거시 수천 건 편입 | 자동 신규업무 유입 0; 편입 분해표로 원본수 설명 | 22~23 |
| AC-40 | 목록/통계에서 팀 계정 일부만 관측 | 관측 계정·기간·채널 한계 표시, 팀 전체라고 안 함 | 14~17,21,24 |

독립 검증자는 최소 다음 고의 변이를 넣어 시험이 실제로 실패하는지 확인한다: 내부보고를 제안으로 분류, unknown을 false로 접기, occurred_at 대신 imported_at 사용, 재시도에 새 ID 생성, 보류를 백로그에서 제거, 시스템 정리를 고유 처리량에 합산. 변이는 시험 환경에서만 적용하고 실제 코드에 남기지 않는다.

---

## 13. 출시 판정

### 13.1 단계별 의미

**SPEC_READY:** 요구·계약·매핑·인수조건이 구현할 만큼 명확하다. 제품이 구현됐다는 뜻이 아니다.

**LOCAL_PASS:** 실제 경로를 통과하는 합성/비식별 fixture 시험이 통과했다. 운영 계정·실메일·실제 포털 작동을 주장하지 않는다.

**STAGING_VERIFIED:** 격리 환경에서 migration, 저장/재조회, 화면, 지표, 권한, 복구가 검증됐다.

**PARTIAL_LIVE:** 명시적으로 승인된 범위만 운영에 노출했다. 미관측 채널·누락 데이터·미완료 기능을 화면과 보고에서 표시한다. 전체 제품 완료는 아니다.

**FULL_LIVE_VERIFIED:** WU-28S/J/L의 실제 읽기 검증, 운영 신규 결과 저장/웹/내부보고, 공통 Weekly 지표, 보안·복구 증거까지 충족한다.

**LEGACY_RETIRE_READY:** FULL_LIVE_VERIFIED 이후 두 번의 완전 관측 주간 대조와 별도 인수승인을 충족했다.

### 13.2 전체 완료에 필요한 증거

- 확인한 v6 기준/배포 SHA와 실제 대상 URL의 코드 경로.
- 기존 객체를 어떻게 재사용했는지의 최종 DB 매핑 및 migration version.
- 새 AI Search 한 실행의 원천 결과→중앙 기록→웹→내부 보고 snapshot 대조.
- 강상모의 세 채널별 실제 기존 발송 이력과 페이지 증빙의 대조.
- verified/unknown/partial/실패 시나리오가 화면에서 구분되는 증거.
- 전체 DB 검색, 후보/매칭/전송의 별도 집계, 주간 경계·snapshot·백로그 수지 대조.
- 미인증/비소속/일반 권한 거부와 개인정보/키 노출 방지 시험.
- 자동 및 수동 갱신의 동일 handler, 중복실행 방지, 마지막 성공시각 보존.
- 보존되는 구형 자료·격리 자료·미연결 자료의 위치와 수.
- 원복 절차, 수행한 리허설, 아직 NOT_RUN/BLOCKED인 항목.

모든 기능이 구현된 것처럼 보이는 화면 한 장, mock 데이터 데모, 테스트 “초록”만으로 완료를 선언하지 않는다.

---

## 14. 구현 전에 계속 확인할 위험

### 14.1 가장 큰 위험 다섯 가지

**발송 허위확정:** AI 설명이나 내부메일을 실발송으로 세는 위험. R-01/05와 AC-09~20으로 차단한다.

**두 DB의 경쟁 정본:** SQLite와 Supabase가 서로 덮어쓰거나 데이터가 다른 위험. 로컬 원장/중앙 확정 관계와 operation ID/readback을 고정한다.

**주간 실적 왜곡:** 재검색·레거시 이관·시스템 정리·미관측을 성과로 집계하는 위험. 사건 시각, 고유 단위, 수지 전이, coverage를 분리한다.

**SOT와 실제 구현의 혼동:** 과거 문서에 쓰였다는 이유로 지금 동작한다고 믿는 위험. WU-00의 실제 근거와 단계별 완료 상태로 막는다.

**과한 작업 범위:** UX 개선을 하며 평가엔진·브라우저·ATS까지 갈아엎는 위험. WU별 허용 파일, 변경 규모, 비범위를 고정한다.

### 14.2 이 문서를 받는 Claude에게 금지하는 보고

- “Supabase와 SQLite를 완벽 동기화했습니다” — 양쪽 ID·필드·해시/readback 증거 없이 금지.
- “세 채널 발송을 모두 추적합니다” — 채널별 라이브 읽기 증거 없이 금지.
- “전부 미발송입니다” — 계정·기간·원천 범위가 불완전하면 금지.
- “이번 주 신규 후보 N명입니다” — import/중복/매칭을 후보 수로 혼용하면 금지.
- “칸반을 삭제했습니다” — 요청은 이 표의 칸반 컬럼 제거이며 다른 메뉴 삭제가 아니다.
- “PRD대로 전체 구현/배포했습니다” — 현재 승인 WU와 외부효과 범위를 넘기면 금지.

### 14.3 출처 확인 메모

제품 요구와 화면 판정은 사용자 제공 자료에 근거한다. 과거 작업 기록은 현재 코드 검증의 대체물이 아니다. 외부 기술 사실은 다음 공식 문서의 동작을 확인해 반영했다. 구현 시 설치된 실제 버전과 다시 대조한다.

- Supabase RLS: `https://supabase.com/docs/guides/database/postgres/row-level-security`
- Supabase views/호출자 권한: `https://supabase.com/docs/guides/database/views`
- SQLite transactions/동시 writer: `https://www.sqlite.org/lang_transaction.html`
- SQLite foreign keys/연결별 설정: `https://www.sqlite.org/foreignkeys.html`
- Gmail send 응답: `https://developers.google.com/workspace/gmail/api/reference/rest/v1/users.messages/send`
- Gmail Message 식별 필드: `https://developers.google.com/workspace/gmail/api/reference/rest/v1/users.messages`

이 링크는 새 라이브러리 도입 권장이 아니라, 상태·권한·원자성을 잘못 가정하지 않기 위한 근거다.

---

## 15. 첫 실행의 정확한 요청

지금은 **WU-00만 수행**한다. 이 문서를 SOT 규약에 맞춰 등록할 준비를 하고, 실제 구현 인수·물리 매핑·충돌표를 작성한다. 기존 root worktree 변경, 새로운 기능 코드, 운영 DDL, 외부 발송, scheduler 등록, push/PR/배포를 하지 않는다.

완료 보고에는 “무엇을 확인했는지”, “어느 과거 가정이 틀렸는지”, “무엇을 재사용할지”, “어떤 항목은 아직 증명하지 못했는지”, “WU-01 전에 꼭 필요한 결정이 있는지”를 적는다. 확인하지 못한 부분을 채우려고 테이블·함수·권한을 만들어내지 않는다.

**완료 기준은 문서의 길이가 아니라, 다음 WU의 구현자가 의미·범위·증거·중단 조건을 추측할 필요가 없는 상태다.**
