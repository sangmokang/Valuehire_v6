# 회사 단위 서치 착수 프롬프트 — `OOOsearch` (2026-09-29)

사용법: `/clear` 후 아래 `---` 이하를 붙여넣고, 첫 줄의 `{COMPANY}` 와 `{CAREERS_URL}`(모르면 `unknown`)만 바꿉니다.

---

`/strict` L1 · `search` 스킬 · Aside 브라우저만 사용. 대상 회사: **{COMPANY}** · 채용 페이지: **{CAREERS_URL}**

목표: {COMPANY}가 지금 채용 중인 포지션을 모두 파악하고, 쉬운 포지션부터 3개 채널(사람인·잡코리아·LinkedIn RPS)에서 우수 후보를 찾는다. 연 프로필과 목록 화면은 모두 SQLite·Supabase에 저장해 다시 읽어 확인하고, 내부 4명에게 브리핑 메일을 보낸 뒤 사장님께 짧게 보고한다.

## 절대 규칙 (어기면 그 자리에서 멈춤)
- **거짓 보고 금지.** 보고의 숫자는 모두 이 실행에서 만든 파일의 `wc -l`·`jq length`·readback 결과에서 나와야 한다. 확인하지 않은 것은 `NOT_RUN`·`확인되지 않음`으로 쓴다. "저장됨"은 readback이 같은 ID 집합을 돌려줄 때만 쓴다.
- 후보자에게 이메일·InMail·연결 요청·포지션 제안을 보내지 않는다. 메일은 내부 4명에게만 보낸다.
- Chrome·Playwright·CDP 금지. Aside에 이미 열린 RPS·사람인·잡코리아 탭을 탭 id로 재사용하고, 사장님 활성 탭을 빼앗지 않는다(`docs/sot/search-query-and-filter-rules.md` 2026-09-28 절).
- 로그인·CAPTCHA·"multiple sign-ins"는 우회하지 않는다. `BLOCKED / 채널 / 화면 / 사장님이 할 일 한 가지`를 기록하고 다른 채널로 계속 진행한다.
- 프로필은 한 번에 하나씩 연다. 병렬 열람·대량 탭 금지.
- 새 DB·테이블·프레임워크를 만들지 않는다. 기존 아카이버(`http://localhost:7777`, SQLite + Supabase 자동 동기화)와 `artifacts/search-*/bin/` 도구를 재사용한다.
- 후보 개인정보가 담긴 산출물은 `artifacts/`(gitignore 대상)에만 둔다. git에 넣지 않는다.

## 0. 시작 게이트 (전부 통과해야 1단계로 간다)
실행 폴더: `RUN=artifacts/company-{COMPANY_SLUG}-$(date +%Y%m%d)` (슬러그는 영문 소문자). 아래 결과를 `$RUN/gate0.txt`에 저장한다.
1. **정본 확보.** 회사 조사 정본과 스크립트는 아직 main에 없고 `origin/task/cross-pc-handoff-20260922`에만 있다. 이 브랜치를 읽기 전용으로 꺼낸다: `git worktree add --detach worktrees/ci-sot-ro origin/task/cross-pc-handoff-20260922`. 이미 있으면 재사용한다. 다음을 읽는다: `docs/sot/candidate-search.md`, `docs/sot/company-intelligence.md`, `scripts/company_intelligence.py`, `scripts/recruiting_browser.py`, `scripts/recruiting_archive.py`, `.agents/skills/search/SKILL.md`. main에서는 `docs/sot/search-query-and-filter-rules.md`를 읽는다. 파일 하나라도 없으면 `BLOCKED_SOT_MISSING`으로 멈춘다.
2. **아카이버 상태.** `curl -s -m 5 http://localhost:7777/api/health`가 `"ok":true`여야 한다. 아니면 멈춘다.
3. **중복 작업 확인.** 최근 1시간 안에 수정된 `artifacts/*` 폴더를 나열한다(`find artifacts -maxdepth 1 -mmin -60`). 이름에 {COMPANY}가 들어간 폴더가 있으면 다른 세션이 작업 중이므로 `BLOCKED_CONCURRENT`로 멈춘다. 다른 회사 폴더는 건드리지 않고 기록만 한다.
4. **이미 한 일 확인.** 모든 `artifacts/*/ledger/mail_log.jsonl`과 `mail_log*.jsonl`에서 {COMPANY} 관련 발송 이력을, `opened*.jsonl`에서 이미 연 URL을 모아 `$RUN/prior.json`에 저장한다. 오늘 이미 같은 회사 브리핑을 보냈으면 멈추고 보고한다.
5. **채널 접근 확인.** Aside에서 RPS 검색 화면, 사람인 기업회원 인재풀, 잡코리아 인재검색을 실제로 열어 로그인 상태를 스크린샷으로 남긴다.

## 1. 채용 페이지 → JD 전수 수집 → 세그먼트
- 회사를 먼저 식별한다. 공식 도메인과 서비스·업종·주소로 확정하고(회사명만으로 확정 금지), `company_intelligence.py --load-company --homepage <공식홈>`으로 기존 조사가 있으면 불러온다.
- 공식 채용 페이지(없으면 원티드·사람인·잡코리아·LinkedIn Jobs의 회사 공고)에서 **현재 열린 포지션 전부**를 수집한다. 포지션마다 원문 텍스트, URL, 관찰 시각, 스크린샷을 `$RUN/jd/J##.{txt,png}`에 저장한다. `$RUN/jd/index.jsonl`에는 포지션마다 `{jd_id, title, url, source, observed_at, 경력요건, 필수, 우대, 근무지}` 한 줄씩 쓴다.
- AC-1: `wc -l < $RUN/jd/index.jsonl`이 채용 페이지 화면에 보인 공고 수와 같아야 한다. 화면 수는 스크린샷에서 직접 센다. 다르면 이유를 적는다. 0건이면 `BLOCKED_NO_JD`로 멈춘다.
- 비슷한 포지션끼리 묶는다(직군 × 시니어리티, 예: `BE-시니어`, `데이터-주니어`). 결과는 `$RUN/segments.json`에 `{segment_id, jd_ids[], 묶은 이유}`로 저장한다. 모든 JD는 정확히 한 세그먼트에 속해야 한다(AC-2: 세그먼트에 속한 jd_id의 합집합 = index의 jd_id 집합, 중복 0).

## 2. 핵심어 추출 → 서치 방향 확정
세그먼트마다 `$RUN/plan/S##.md`에 다음을 쓴다.
- JD 원문 기준으로 핵심 업무, 필수, 우대, 원문에 없는 조건(추가 금지)을 적는다.
- 핵심어마다 변형을 적는다: 영문·한글·띄어쓰기/붙여쓰기·약어·정식명, 그 직무 최상위 실무자들이 쓰는 용어(mutual jargon), 제외어. 예: `Kubernetes·쿠버네티스·k8s`, `A/B 테스트·AB테스트·ABtest`.
- 100점 배점표를 적고(합계 100), 이 배점표를 해당 세그먼트의 모든 JD에 쓴다. JD마다 다르게 해야 하면 JD별로 버전을 나눈다.
- 이 계획을 `search` 스킬 4단계(Search Hypothesis)의 입력으로 삼는다. 회사 조사가 끝난 뒤(3단계) `company_intelligence.py --input ... --summary ...`로 가설을 확정하고 snapshot hash를 기록한다.

## 3. 회사 조직 이해 — 현·전 직원 프로필 확보
- LinkedIn(RPS의 current/past company 필터)과 사람인·잡코리아(회사명 키워드)에서 {COMPANY} 현·전 직원을 찾는다. 공개 웹의 Team/About 페이지, 인터뷰, 발표 자료도 함께 본다.
- 직원 프로필은 **후보가 아니라 조직 표본**이다. `$RUN/org/people.jsonl`에 기록하고, 후보 원장에는 넣지 않는다. current·former·unknown을 나누고, 이름만 같은 사람을 동일인으로 합치지 않는다.
- `$RUN/org/summary.md`에 세그먼트 관련 조직 구성, 직원들이 쓰는 실무 용어, 이전 회사·경력 흐름, 학력 분포를 쓴다. 각 항목에는 표본 수와 한계를 적는다. 여기서 얻은 새 용어는 2단계 변형 목록에 보탠다. 조직 패턴은 검색을 넓히는 데만 쓰고, JD 필수요건을 빼거나 점수를 올리는 데 쓰지 않는다.
- 연 프로필과 목록 화면은 모두 6단계 방식으로 저장한다.

## 4. 후보 서치 — 쉬운 세그먼트부터
- 순서는 8단계의 난이도 순위(쉬운 것부터)를 따른다. 난이도 순위는 이 단계 전에 1차로 만들고 서치 결과로 갱신한다.
- 채널 순서는 RPS 1촌 → 2촌·3촌 → 사람인 → 잡코리아로 하되, 막힌 채널은 건너뛰고 기록한다.
- 한 조합에는 핵심어 변형 한 세트를 쓴다. 조합마다 `$RUN/listings/combos.jsonl`에 `{segment, channel, 입력어, 화면에서 다시 읽은 적용 검색어·필터, 총 인원, 페이지, 관찰 시각, 스크린샷}`을 남긴다. 검색어와 필터는 입력 후 화면에서 다시 읽는다. 사람인은 경력 하한·상한을 모두 쓰고 조합마다 필터를 바꾼다(SOT 참조).
- **키워드를 놓치지 않는다.** 2단계 변형 목록의 각 항목이 적어도 한 조합에 쓰였는지 `$RUN/plan/S##-coverage.md`에 표로 남긴다. 안 쓴 변형에는 이유를 적는다.
- 인원 상한은 없다. 새 조합에서 새로 적합한 후보가 연속 2개 조합 동안 0명이면 그 세그먼트를 끝내고, 종료 사유를 적는다.
- 판정 근거는 후보 본인 원문에만 둔다. 회사명·학교·직함 한 줄, Similar Profiles, 다른 후보 카드는 근거가 되지 않는다. 국적은 쓰지 않는다. 학력은 SOT 학력 절에 따라 보조 참고로만 쓴다.

## 5. 조직 관점 리뷰 — 왜 잘 맞는가
상세 검토한 후보마다 원장에 네 가지를 따로 쓴다: **A** JD 직접 일치(100점, 항목별 근거 인용), **B** {COMPANY} 조직 패턴과의 유사성(3단계 표본과 비교, 점수에 영향 없음), **C** 전이 가능한 경험, **D** 제안 전 확인할 것. "왜 잘 맞는가"는 A와 B를 합쳐 2~3문장으로 쓰고, 인용 근거는 후보 본인 원문에 실제로 있어야 한다.

## 6. 전수 저장 — SQLite + Supabase, 근거 보존
- 목록 화면(조합의 각 페이지)과 연 프로필 **전부**를 즉시 아카이버에 저장한다. 익스텐션 자동 캡처가 안 되면 `POST http://localhost:7777/api/archive`로 직접 보낸다. 추천하지 않은 후보, 중복, 직원 표본도 저장한다.
- 연 URL은 모두 `$RUN/ledger/opened.jsonl`에, 목록 화면은 모두 `$RUN/ledger/listings.jsonl`에 한 줄씩 남긴다. 각 줄에는 `url, kind(profile|listing|org), channel, observed_at, archive_local_id, screenshot`을 넣는다.
- readback: `artifacts/codeit-search-20260922/verify_storage.py`를 이 실행의 run_id에 맞게 복사해 돌린다. SQLite와 Supabase의 ID 집합, url, 본문, 스크린샷 참조를 대조한 결과를 `$RUN/ledger/storage_verify.json`에 저장한다.
- AC-6 (이 셋이 모두 맞아야 "저장 완료"라고 쓴다):
  - (a) `opened.jsonl`과 `listings.jsonl`의 고유 URL 수 = SQLite의 이 run_id 레코드 수 = Supabase 레코드 수
  - (b) `id_set_equal: true`
  - (c) 음성 대조군 1건: 원장에 있는 URL 하나를 대조 목록에서 일부러 빼고 돌렸을 때 불일치가 검출되어야 한다. 대조군 결과도 파일로 남긴다.
  하나라도 틀리면 `PARTIAL`로 보고하고 빠진 URL 목록을 남긴다. 스크린샷 원본이 클라우드에 올라갔는지는 따로 적는다(검증 안 했으면 `NOT_RUN`).

## 7. 브리핑 메일 — 내부 4명
- 받는 사람: sangmokang·kcs·julian·rogan @valueconnect.kr. 이 실행 지시가 이 4명에 대한 발송 승인이다. 후보자 연락은 승인 범위가 아니다.
- 도구: `artifacts/search-20260928-r2/bin/send_mail.py`를 `$RUN/bin/`에 복사하고, `TO`가 이 4명인지 확인한 뒤 `AGENT=claudecode`로 보낸다. 제목은 `[aisearch]claudecode [{COMPANY} 회사 서치] 포지션 N·추천 N·조건부 N`처럼 쓴다. 보내기 전에 모든 mail_log에서 같은 제목·run_id로 이미 보낸 게 없는지 확인한다.
- 본문 순서:
  1. **맨 위: 포지션 난이도 순위(쉬운 것부터)**. 8단계 표를 넣는다.
  2. 조직 요약(3단계, 표본 수와 한계 포함)
  3. 세그먼트별 후보 표: 판정(추천/조건부/보류) · 매칭 점수 · 채널 · 촌수 · **1촌이면 이메일/컨택 주소**(본인 Contact info에 보인 값만, 없으면 `확인되지 않음`) · 현재 회사·직무 · 학력 · 주요 경력 · 왜 잘 맞는가(A+B) · 확인할 것 · 프로필 URL
  4. 같은 포지션에 이미 연락한 후보는 별도 표로 둔다
  5. 저장 대조 결과(AC-6 숫자)와 미완료·재개 지점
- 이메일 규칙: 1촌은 공개 프로필의 Contact info를 실제로 열어 확인한다. 이메일을 추정하거나 만들어내지 않는다. `@valueconnect.kr`, 리크루터 서명, InMail 기록, 다른 후보 카드에 있는 주소는 후보 것으로 쓰지 않는다.
- 발송 전 QA: 본문에 인용한 모든 문장이 그 후보의 원문 파일에 있는지 `artifacts/search-20260924/bin/qa_quotes.py` 방식으로 확인한다(miss=0). 발송 후에는 message_id와 발송 시각을 mail_log에 남긴다.

## 8. 포지션 난이도 순위 (쉬운 것부터)
`$RUN/difficulty.md`에 JD마다 한 줄씩 쓴다. 근거는 **실측값만** 쓴다.
- **후보 풀 크기**: 대표 핵심어 조합의 사람인 총 인원, RPS 결과 수, 잡코리아 결과 수. 화면에서 읽은 숫자와 스크린샷 경로를 함께 적는다.
- **채용 기준 높이**: 필수요건 수, 경력 하한, 희소 기술·도메인 요구, 리더급 여부, 학위·자격 요구
- **실제 수확**: 이 실행에서 찾은 추천·조건부 후보 수
- 정렬 규칙은 표 위에 한 줄로 적는다(예: 풀 크기 내림차순 → 기준 높이 오름차순). 이 순위는 추정이며 이유를 한 줄씩 붙인다. 풀 크기를 재지 못한 JD는 `미측정`으로 표 맨 아래에 둔다.

## 9. 자동화 누락 백브리핑 (사장님께)
실행 중 사람 손이 들어갔거나 반복 수작업이었던 지점을 `$RUN/automation_gaps.md`에 모은다. 항목마다 `무엇 / 몇 번 반복 / 드는 시간 / 자동화 방법 한 줄 / 우선순위`를 쓴다. 예: 채용 페이지 JD 수집, 난이도 풀 크기 측정, 변형 커버리지 표, 1촌 Contact info 열기, readback. 이 파일은 메일에 넣지 않고 최종 보고에 요약한다.

## 10. 최종 보고 (한 번, 짧게)
```
VERDICT: COMPLETE | PARTIAL | BLOCKED
{COMPANY} / 포지션 N (세그먼트 N) / RPS 상세 N · 사람인 상세 N · 잡코리아 상세 N / 추천 N · 조건부 N · 기접촉 N / 1촌 이메일 확인 N
저장: SQLite N = Supabase N = 원장 N (id_set_equal, 대조군 검출 여부)
메일: message_id / 발송 시각
쉬운 포지션 Top3: ...
자동화 누락 Top3: ...
남은 문제·재개 지점: ...
```
모든 숫자 옆에 그 숫자를 만든 파일 경로를 적는다. 증거 원문은 붙이지 않는다.
