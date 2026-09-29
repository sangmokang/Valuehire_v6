# 회사 단위 서치 착수 프롬프트 — `OOOsearch` v2.1 (2026-09-29)

사용법: `/clear` 후 아래 `---` 이하를 붙여넣고, 첫 줄의 `{COMPANY}`, `{SLUG}`(영문 소문자·하이픈), `{CAREERS_URL}`(모르면 `unknown`)만 바꿉니다.

이력: v1(fa0ef48) → Codex 적대 검증 2회 + rescue 실측 1회 + ChatGPT 안 대조 → v2. 반영 내역은 문서 끝 "v2 변경 근거".

---

`/strict` L1 · `search` 스킬 · 브라우저는 Aside만. 대상: **{COMPANY}** · 슬러그: **{SLUG}** · 채용 페이지: **{CAREERS_URL}**

목표: {COMPANY}의 공개 포지션 전부를 파악하고 난이도를 매긴다. 쉬운 포지션부터 사람인·잡코리아·LinkedIn RPS에서 우수 후보를 찾는다. 연 화면은 모두 SQLite·Supabase에 저장하고 다시 읽어 확인한다. 내부 4명에게 브리핑 메일을 보내고 사장님께 짧게 보고한다.

이번 목표는 시스템 개선이 아니다. 기존 스킬·스크립트·아카이버·메일 도구를 그대로 쓴다. 새 DB·테이블·스키마·프레임워크·점수 모델을 만들지 않고, 관련 없는 코드는 고치지 않는다.

## 절대 규칙 (어기면 그 단계에서 멈추고 BLOCKED)
- **거짓 보고 금지.** 보고와 메일의 숫자는 모두 이 실행의 파일에서 계산한다. 확인하지 않은 값은 `미확인`, 실행하지 않은 단계는 `NOT RUN`으로 쓴다. `DONE`은 실행 증거 파일이 있을 때만 쓴다.
- 후보자에게 이메일·InMail·연결 요청·포지션 제안을 보내지 않는다. 메일은 아래 내부 4명에게만 보낸다.
- Chrome·Playwright·CDP를 쓰지 않는다. Aside에 이미 열린 탭을 탭 id로 재사용하고, 사장님 활성 탭을 빼앗지 않는다(`docs/sot/search-query-and-filter-rules.md` 2026-09-28 절).
- 로그인·CAPTCHA·"multiple sign-ins"는 우회하지 않는다. `BLOCKED / 채널 / 화면 / 사장님이 할 일 한 가지`를 기록하고, 막히지 않은 채널로 계속 진행한다.
- 프로필은 한 번에 하나씩 연다. 병렬 열람과 대량 탭 열기를 하지 않는다.
- 후보 개인정보 산출물은 `artifacts/`(gitignore 대상)에만 둔다.
- **멈춤 신호** — 아래 중 하나가 보이면 즉시 멈추고 원인을 적는다: 같은 검색·명령을 결과 변화 없이 3회 반복, 인증 루프, 저장 실패를 무시하고 다음 단계로 진행, 사이트 실패를 성공으로 기록, 서치와 무관한 코드 수정. 정지 뒤에는 ① 원인 확인 ② 기존 기능으로 해결 가능한지 확인 ③ 최소 우회 1회 ④ 안 되면 그 단계만 BLOCKED로 두고 독립된 나머지 작업은 계속한다. 이 상황이 2번 이상 반복되면 `/codex:rescue`를 백그라운드로 불러 진단만 받는다(코드 수정 금지).

## 고정 경로
- 저장소 루트: `ROOT=/Users/kangsangmo/Desktop/Valuehire_v6`. 모든 상대 경로의 기준이다.
- 정본 워크트리(읽기 전용): `SOT=$ROOT/worktrees/cross-pc-handoff-20260922`. `git -C $SOT rev-parse HEAD`가 `git -C $ROOT rev-parse origin/task/cross-pc-handoff-20260922`와 같아야 한다. 다르거나 워크트리가 없으면 `BLOCKED_SOT`로 멈춘다(새 워크트리를 만들거나 브랜치를 옮기지 않는다).
- 실행 폴더: `RUN=$ROOT/artifacts/company-{SLUG}-<YYYYMMDD-HHMM>`. `RUN_ID`는 이 폴더 이름과 같다.
- 회사 조사 저장소: `CI=$ROOT/artifacts/company-intelligence`

## 0. 시작 게이트 — 결과는 `$RUN/gate0.md`
1. **정본 읽기.** `$SOT/docs/sot/candidate-search.md`, `$SOT/docs/sot/company-intelligence.md`, `$SOT/.agents/skills/search/SKILL.md`, `$SOT/scripts/company_intelligence.py`, `$SOT/scripts/recruiting_archive.py`, `$ROOT/docs/sot/search-query-and-filter-rules.md`를 읽는다. 하나라도 없으면 `BLOCKED_SOT`로 멈춘다.
2. **중복 실행 확인 — `$RUN`을 만들기 전에 한다.** `find $ROOT/artifacts -maxdepth 1 -type d -name "*{SLUG}*" -mmin -120`에서 결과가 나오고, 그 폴더의 `OWNER` 파일에 적힌 pid가 살아 있으면(`kill -0`) `BLOCKED_CONCURRENT`로 멈춘다. 이 검사를 통과한 뒤에 `$RUN`과 하위 폴더(`jd ledger captures archive-ledger listings profiles org plan mail bin`)를 만들고, `OWNER`에 `$$`와 시작 시각을 적는다.
3. **아카이버 상태.** `curl -s -m 5 http://127.0.0.1:7777/api/health`의 결과가 `"ok":true`여야 한다. 응답의 `dbPath`를 기록하고, 이 값이 4번 설정 파일의 `sqlite_path`와 같은지 확인한다.
4. **저장 설정 준비.** `cp $ROOT/artifacts/codeit-search-20260922/archive-config.json $RUN/archive-config.json`. 비밀값이 담긴 파일이므로 내용을 출력하지 않는다.
5. **이미 한 일 확인.** `find $ROOT/artifacts -type f \( -name 'mail_log*.jsonl' -o -name 'opened*.jsonl' \)`를 재귀로 모두 읽는다. 기존 필드명(`at`, `archive_resp.id` 등)은 그대로 둔 채 {COMPANY} 관련 발송 이력과 이미 연 URL을 추려 `$RUN/prior.json`에 저장한다. 오늘 같은 회사 브리핑이 이미 발송됐으면 멈추고 보고한다.
6. **메일 도구 확인.** `grep -n "^TO=" $ROOT/artifacts/search-20260928-r2/bin/send_mail.py`의 결과가 정확히 `sangmokang@ kcs@ rogan@ julian@valueconnect.kr` 4개여야 한다. 수신 주소는 이 코드에 적힌 값만 쓰고, 이름으로 주소를 만들어내지 않는다. 다르면 메일 단계를 `BLOCKED_RECIPIENT`로 둔다.
7. **채널 접근.** Aside에서 RPS 검색, 사람인 기업회원 인재풀, 잡코리아 인재검색을 실제로 열고 로그인 상태 스크린샷을 `$RUN/gate0-*.png`로 남긴다.

## 저장 규칙 (모든 단계 공통) — 연 화면은 전부 저장한다
- 화면을 하나 열 때마다(채용 페이지, 목록 한 페이지, 프로필, 직원 프로필, Contact info) 캡처 JSON `$RUN/captures/C####.json` = `{"url","title","text","run_id":"$RUN_ID","kind":"careers|listing|profile|org|contact","channel","query","filters","page","jd_or_segment"}`을 쓴다. 같은 `text`를 `$RUN/profiles/C####.txt`에도 저장한다(메일 인용 QA의 원문 파일). 그다음 곧바로 아래를 실행한다.
  `python3 $SOT/scripts/recruiting_archive.py --config $RUN/archive-config.json --capture $RUN/captures/C####.json --ledger $RUN/archive-ledger/C####.json`
  종료값 0과 원장의 `"state":"verified"`가 나와야 저장이 끝난 것이다. 이 스크립트가 SQLite와 Supabase 양쪽을 다시 읽어 대조한다. 실패하면 원장의 `error`를 기록하고 한 번 재시도한다. 그래도 실패하면 그 캡처를 `저장 실패`로 두고 계속 진행한다. 저장 실패를 숨기지 않는다.
- 스크린샷은 `$RUN/screen/C####.png`로 로컬에 저장한다. 이 스크립트는 이미지를 클라우드에 올리지 않는다. 클라우드 이미지 저장은 `artifacts/codeit-search-20260922/store_screenshot_objects.py`로 시도할 수 있고, 시도하지 않았으면 `NOT RUN`으로 보고한다.
- 캡처 ID(C####)가 단위다. 같은 URL이라도 다른 페이지·필터·시각이면 캡처가 따로 생긴다. URL 개수로 저장 수를 세지 않는다.
- `$RUN/actions.jsonl`에 사람 손이 든 작업을 한 줄씩 남긴다: `{step, action, started_at, ended_at, manual:true|false, note}`. 9단계에서 쓴다.

## 1. 채용 페이지 → JD 전수 수집 → 세그먼트
- **회사 식별.** 공식 도메인과 서비스·업종·주소로 확정한다(회사명만으로 확정 금지). 기존 조사부터 불러온다: `python3 $SOT/scripts/company_intelligence.py --store-dir $CI --load-company --homepage <공식홈>`. 법인명·영문명·한글명·서비스명·옛 이름 등 **회사명 표기 변형 목록**을 `$RUN/company_aliases.json`에 근거 URL과 함께 적는다. 이 목록은 4·5단계의 전직자 제외에 쓴다.
- **JD 수집.** 공식 채용 페이지를 연다. 공식 페이지가 없으면 원티드·사람인·잡코리아·LinkedIn Jobs의 회사 공고를 쓰고 출처를 적는다. 페이지네이션·탭·직군 필터·지역 필터를 전부 넘기고, 넘긴 상태마다 캡처한다. JD 제목만 보지 말고 본문을 연다. 포지션마다 원문을 `$RUN/jd/J##.txt`에 저장하고 저장 규칙대로 아카이브한다.
- `$RUN/jd/index.jsonl` 한 줄 = `{jd_id, title, url, source, observed_at, 팀/조직, seniority, 요구경력, 핵심업무, 필수[], 우대[], 기술/도메인[], 산업경험, 조직특성, 필수키워드[]}`. 원문에 없는 칸은 `미확인`으로 두고 추측으로 채우지 않는다.
- **AC-1:** 채용 페이지의 모든 페이지·탭에서 보인 공고 ID의 합집합(`$RUN/jd/seen_ids.txt`) = index의 jd_id 집합. 차이가 있으면 이유를 적는다. 0건이면 `BLOCKED_NO_JD`.
- **세그먼트.** 직무군 × 조직 × seniority × 기술/도메인을 기준으로 묶는다. 사실상 같은 포지션이거나 후보 풀이 겹치면 같은 세그먼트로 둔다. `$RUN/segments.json` = `[{segment_id, jd_ids[], 묶은 이유}]`. **AC-2:** 모든 jd_id가 정확히 한 세그먼트에만 속한다.

## 2. 핵심어 → 검색 방향 (search 스킬 4단계)
세그먼트마다 `$RUN/plan/S##.md`를 쓴다.
- **개념 목록.** JD에서 반드시 검색에 들어가야 할 핵심 개념을 적는다(직무명·핵심 기술·도메인).
- **개념별 변형.** 한/영, 띄어쓰기, 약어/풀네임, 동의어, 옛 명칭, 유사 회사에서 쓰는 직무명, 실무자 용어(mutual jargon)를 적는다. 예: `Product Manager·PM·프로덕트 매니저·프로덕트매니저·서비스기획`. 변형은 개념 안에서만 늘린다. 개념끼리 곱해서 조합을 폭발시키지 않는다.
- **채널 변환.** 세 채널에 같은 개념을 쓰되 각 채널 문법에 맞춰 바꾼다(RPS 불리언·필터, 사람인 키워드·경력 하한/상한, 잡코리아 키워드). 채널마다 기준이 달라지면 안 된다.
- **배점표.** 합계 100점, 항목마다 `met=1·partial=0.5·unmet=0·unknown=0`으로 계산한다(`$SOT/docs/sot/candidate-search.md` §3). 가능하면 `humansearch.recruiting_review.review_candidate()`로 계산하고, 없으면 같은 규칙을 파일에 적고 `NOT RUN`으로 표시한다.
- 3단계가 끝나면 `python3 $SOT/scripts/company_intelligence.py --store-dir $CI --input $RUN/company-input.json --summary $RUN/company-summary.json`으로 가설을 확정하고 snapshot hash를 기록한다. 조직 패턴은 검색을 넓히는 데만 쓰고, 필수요건을 빼거나 점수를 바꾸지 않는다.

## 3. 조직 이해 — 현·전 직원 (후보가 아님)
- RPS(current/past company = {COMPANY}), 사람인·잡코리아(회사명 변형 키워드), 공식 Team/About·인터뷰·발표 자료에서 JD와 관련된 현·전 직원을 찾는다. 연 화면은 모두 `kind:"org"`로 저장한다.
- `$RUN/org/people.jsonl` = `{person_id, current|former|unknown, 직무, 팀, 경력수준, 이전회사[], 기술/도메인[], 학력, 근거 캡처ID}`. 이름만 같으면 동일인으로 합치지 않는다. 직원은 후보 원장에 넣지 않는다.
- `$RUN/org/summary.md`에는 세그먼트별로 실제 구성원, 유사 직무, 리더·조직, 반복되는 이전 회사·경력 흐름, 실무 용어를 쓴다. **표본 수와 한계를 반드시 적는다.** 몇 명의 공개 프로필로 회사 전체 채용 기준을 단정하지 않는다. 새로 알게 된 용어는 2단계 변형 목록에 보탠다.

## 4. 후보 서치 — 쉬운 세그먼트부터
- 8단계의 **예상 난이도**(검색 전, `JD 요건 기준 예상`)로 순서를 정한다.
- 채널 순서: RPS 1촌 → 2·3촌 → 사람인 → 잡코리아. 막힌 채널은 건너뛰고 기록한다.
- 조합마다 `$RUN/listings/combos.jsonl`에 `{combo_id, segment, channel, 개념, 입력어, 화면에서 다시 읽은 적용 검색어·필터, 총 인원, 본 페이지, 캡처ID[], 새로 찾은 적합 후보 수}`를 남긴다. 입력한 뒤에는 화면에서 검색어·필터를 다시 읽는다(SOT의 사람인·RPS 입력 함정 참조). 조합마다 결과 페이지를 계속 넘긴다. 한 페이지 전체에서 새 관련 후보가 0명이거나 결과 끝에 닿았을 때만 그 조합을 멈추고, 본 페이지 번호를 기록한다.
- **키워드 누락 금지 규칙.** 2단계의 모든 개념 × 모든 변형은 채널마다 적어도 한 조합에 들어가야 한다(문법상 불가하면 이유 기록). 결과는 `$RUN/plan/S##-coverage.md` 표로 남긴다. 이 커버리지를 채우기 전에는 세그먼트를 끝내지 않는다.
- **확장 순서**(커버리지를 채운 뒤에도 후보가 부족하거나 질이 낮을 때): 직무명 변형 → 핵심 기술 변형 → 한/영 → 유사 직무 → 유사 회사 → 인접 산업. 확장 조합이 연속 2개 동안 새 적합 후보 0명이면 그 세그먼트를 끝내고 이유를 적는다. 결과가 충분한 키워드는 더 변형하지 않는다.
- 인원 상한은 없다. 기준을 낮춰 인원을 늘리지 않는다.

## 5. 후보 평가 — 이 순서로, 앞에서 걸리면 뒤로 가지 않는다
원장: `$RUN/ledger/candidates.jsonl`, 후보 한 명당 한 줄. 동일인은 채널 내부 ID·프로필 URL 같은 식별자로만 합친다. URL 표기 차이나 이름 띄어쓰기 차이로 같은 사람을 여러 명으로 세지 않는다.
1. **대상 회사 현·과거 재직 → HARD EXCLUDE.** 후보 원문 경력 항목의 **소속 회사(고용주) 칸**이 `company_aliases.json`의 표기와 일치하면 즉시 `excluded_target_company`로 두고 근거 캡처ID를 적는다. 이 후보는 더 평가하지 않고, 추천 목록과 메일 추천 명단에 넣지 않는다. 기록은 남긴다. 설명 본문에 고객사·협업사·프로젝트로 회사명이 나오는 것은 재직이 아니다. 이름이 비슷하다는 것만으로도 제외하지 않고 `확인 필요`로 둔다.
2. **JD 필수요건.** 항목마다 met/partial/unmet/unknown과 원문 인용을 적는다.
3. **핵심 업무·도메인 경력.** 원문 인용과 함께 적는다.
4. **재직 안정성.** 경력마다 시작·종료 월을 원문대로 적는다. 사유가 원문에 명시된 계약직·프로젝트직·인턴·인수합병·조직 폐쇄·그룹 내 이동은 감점하지 않는다. 사유를 지어내지 않는다. 기본 규칙(조정 가능): **최근 5년 안에 예외 사유 없는 12개월 미만 재직이 2회면 −15점, 3회 이상이면 −30점이고 판정은 최대 `조건부`.** 해당하면 `잦은 이직 리스크` 표시와 재직기간 근거를 적는다.
5. **언어·근무 요건.** JD가 요구할 때만 확인한다: 한국어 업무 수행, 한국 시장 경험, 국내 근무 가능, 취업자격. 원문에 없으면 `미확인`으로 둔다. **국적·외국인 여부는 점수나 판단에 쓰지 않고, 다른 요건의 대리변수로도 쓰지 않는다.**
6. **학력.** 100점 배점에는 JD와 직접 관련된 전공·학위·연구·전문교육만 넣는다. 학교 이름·순위로는 점수를 더하거나 빼지 않는다. `docs/sot/search-query-and-filter-rules.md`의 학교 순위는 **같은 점수·같은 직무 근거를 가진 후보끼리의 순서를 정할 때만** 쓰고, 후보 본인 원문에 학교가 확인될 때만 쓴다. 학력이 실무 경력보다 앞서지 않는다.
7. **종합.** A(JD 직접 일치, 100점 − 안정성 감점)를 계산한다. B(조직 패턴 유사성: 3단계 표본과 이전 회사·경력 흐름·기술 비교, 점수에 반영하지 않음), C(전이 가능한 경험), D(제안 전 확인할 것)를 적는다. "왜 잘 맞는가"는 A와 B를 합쳐 2~3문장으로 쓴다. 판정은 추천/조건부/보류/제외 중 하나다.
- 원장 필드: `candidate_id, 이름, 채널·채널ID, 프로필 URL(공개/Recruiter), 현재/최근 회사·직무, 핵심 경력, 학력, 주요 기술/도메인, 촌수, 이메일·출처·확인시각 또는 확인되지 않음, 항목별 점수와 인용, 안정성 감점, A/B/C/D, 판정·사유, 기접촉 이력(확인한 시스템·기간), 근거 캡처ID[]`. 확인하지 않은 칸은 `미확인`으로 둔다.
- **이메일.** 상세 검토한 1촌은 공개 프로필의 Contact info를 실제로 연다(`kind:"contact"`로 저장). 본인 화면에 보인 값만 쓴다. 이메일을 추측하거나 만들어내지 않는다. `@valueconnect.kr`, 리크루터 서명, InMail 기록, 다른 후보 카드의 주소는 후보 것으로 쓰지 않는다. 2·3촌이라도 본인 화면에 보이면 기록한다.
- **AC-5 (점수 재계산):** 원장의 항목별 met/partial/unmet/unknown과 배점표로 A를 다시 계산했을 때 기록된 A와 모든 후보에서 같아야 한다. 결과는 `$RUN/ledger/score_recheck.txt`(불일치 0)에 둔다.

## 6. 저장 검증 — 저장 완료라고 쓰기 전에
아래 네 검사 결과를 `$RUN/ledger/storage_check.json`에 쓴다.
- (a) **캡처 하나하나**에 대해: 원장 `archive-ledger/C####.json`이 있고, `state=="verified"`이며, `result.id`가 (b)의 SQLite 집합과 Supabase 집합에 모두 들어 있다. 이 원장 상태는 `recruiting_archive.py`가 캡처마다 SQLite·Supabase 양쪽에서 url·본문·run_id·captured_at을 다시 읽어 대조한 결과다. 하나라도 어긋나는 캡처ID는 나열한다.
- (b) SQLite `SELECT id FROM archives WHERE run_id='$RUN_ID'`의 ID 집합 = Supabase `profile_archives?run_id=eq.$RUN_ID`의 `local_id` 집합 = 원장들의 `result.id` 집합. 결과가 1000건이면 페이지를 나눠 읽는다. 집합이 0건이면 실패로 본다.
- (c) 음성 대조군: 원장 ID 하나를 뺀 집합으로 (b)를 다시 비교했을 때 불일치가 검출되어야 한다. 검출되지 않으면 검사기 자체가 고장이다.
- (d) 모든 프로필 캡처가 원장 후보나 직원 표본 중 한 곳에 연결되어 있다(연결 안 된 캡처 0).
넷 다 맞아야 **텍스트 저장** `DONE`이다. 하나라도 틀리면 `PARTIAL`로 두고 빠진 목록을 남긴다. 화면 이미지의 클라우드 저장은 이 검사와 별개인 상태(`DONE` 또는 `NOT RUN`)로 따로 보고한다. 이미지를 확인하지 않은 채 "화면까지 양쪽 저장"이라고 쓰지 않는다.

## 7. 브리핑 메일 — 내부 4명
- **발송 게이트.** ① 0단계 6번이 통과했고 ② 인용 QA에서 miss가 0이며 ③ 같은 제목이 보낸편지함에 없어야 한다. 저장이 `PARTIAL`이어도 보낼 수 있다. 다만 그때는 제목에 `[PARTIAL]`을 붙이고 본문 맨 위에 빠진 목록을 적는다.
- **인용 QA.** 후보 행마다 "왜 잘 맞는가"와 "핵심 경력"은 후보 원문 인용을 **2개 이상** 포함하고, 인용은 `<q data-src="profiles/C####.txt">…</q>`로 감싼다. 발송 전에 모든 `<q>`의 텍스트가(공백 정규화 후) `data-src` 파일 안에 실제로 있는지 검사하고 결과를 `$RUN/mail/qa.txt`(`quotes=N miss=0 rows_under_2=0`)에 쓴다. `data-src`가 없는 인용, 다른 후보의 파일을 가리키는 인용, 인용이 2개 미만인 후보 행, `quotes=0`은 모두 실패로 본다.
- **도구.** `cp $ROOT/artifacts/search-20260928-r2/bin/send_mail.py $RUN/bin/`. 실행: `cd $RUN/bin && AGENT=claudecode python3 send_mail.py {SLUG} "<제목>" $RUN/mail/briefing.html`. 제목에 `RUN_ID`를 넣는다. 예: `[{COMPANY} 회사 서치 {RUN_ID}] 포지션 N·추천 N·조건부 N`. 스크립트가 `[aisearch]claudecode ` 접두사를 붙이고, 보낸편지함에 같은 제목이 있으면 `DUPLICATE_EXISTS`와 함께 rc=2로 멈춘다. 이 스크립트는 최근 3일만 검색하고, 발송이 끝난 뒤에야 로그를 쓴다. 그래서 재시도하기 전에는 반드시 Gmail MCP `search_threads`로 기간 제한 없이 `in:sent "{RUN_ID}"`를 검색한다. 1건이라도 나오면 다시 보내지 않고 그 message_id를 기록한다.
- **발송 후.** `$RUN/ledger/mail_log.jsonl`에 있는 message_id를 Gmail에서 다시 조회해(`in:sent` 제목 검색) 수신자 4명과 message_id를 확인한다.
- **본문 순서.**
  1. **맨 위 — 포지션 난이도 순위(쉬운 것부터).** 8단계 표를 넣고, 각 행에 `실측` 또는 `JD 요건 기준 예상`을 표시한다.
  2. 조직 요약: 표본 수와 한계, 평가에 반영한 부분
  3. 세그먼트별 추천·조건부 후보 표: 이름 · 현재 회사·직무 · 핵심 경력 · 학력 · 매칭 점수(안정성 감점 표시) · 왜 잘 맞는가 · 강점 · 확인할 것 · 촌수 · **이메일/컨택(본인 화면 값 또는 확인되지 않음)** · 출처 URL
  4. 같은 포지션에 이미 연락한 후보 표(별도)
  5. 집계: 채널별 조합 수, 목록 결과 수, 상세 열람 수, 중복 제거 후 후보 수, 대상사 재직자 제외 수
  6. 저장 검증 숫자(6단계)와 미완료·재개 지점

## 8. 포지션 난이도 순위 — 쉬운 것부터
`$RUN/difficulty.md`, JD마다 한 행씩 쓴다.
- **검색 전(예상):** 요구 경력 범위, 필수요건 수, 필수 기술의 희소성, 산업·도메인 제한, 요건 조합의 희소성을 본다. 이 행에는 반드시 `JD 요건 기준 예상`이라고 쓴다.
- **검색 후(실측):** 대표 조합의 채널별 총 인원(화면 숫자와 캡처ID), 새로 찾은 추천·조건부 수를 더해 행을 갱신하고 `실측`이라고 쓴다. 검색하지 않은 JD는 `예상`으로 둔다.
- 정렬 규칙(예: 실측 풀 크기 내림차순 → 필수요건 수 오름차순)을 표 위에 한 줄로 적는다. 각 행에는 판단 근거를 1~3줄로 붙인다. "채용 기준이 낮다"는 말은 근거 없이 쓰지 않는다.

## 9. 적대적 검증 1회 → 자동화 백브리핑
- **발송 전 1회.** `/codex:adversarial-review`를 백그라운드로 실행해(묻지 말 것) `$RUN`의 원장·커버리지·저장 검증·메일 초안을 검토시킨다. 다음을 중점으로 본다: 키워드·변형 누락, 채널 간 기준 불일치, 중복 계수, 열었는데 저장 안 된 화면, 원문에 없는 추천 근거, 추측한 학력·경력·연락처, 키워드만 맞는데 높은 점수, 너무 이른 종료 또는 무의미한 변형 반복, 대상사 전직자 혼입, 회사명 변형 누락으로 놓친 전직자, 잦은 이직인데 높은 점수, 계약직·인턴을 잘못 감점, 국적 대리변수 사용, 확인 안 된 언어·취업자격, 학교 이름의 과도한 영향. 결함은 최소 범위로만 고치거나 다시 검색한다. 전체를 처음부터 다시 돌리지 않는다. 추가 검증 라운드는 돌리지 않는다.
- **자동화 백브리핑.** `$RUN/actions.jsonl`에서 실제로 반복된 수작업만 뽑아 `$RUN/automation_gaps.md`에 쓴다. 항목 형식: `반복 작업 / 횟수·소요(actions 근거) / 불편 / 자동화 효과 / 구현 난이도 / 지금 필요한가`. 측정하지 않은 값은 `추정`이라고 쓴다. 자동화는 이번에 구현하지 않는다.

## 10. 최종 보고 (터미널, 한 번, 짧게)
```
VERDICT: COMPLETE | PARTIAL | BLOCKED     RUN_ID
단계  0 게이트 / 1 JD / 2 전략 / 3 조직 / 4 서치 / 5 평가 / 6 저장 / 7 메일 / 8 난이도 / 9 검증·자동화
상태  DONE|PARTIAL|BLOCKED|NOT RUN — 단계마다 한 줄, 근거 파일 경로 포함
{COMPANY}: 포지션 N(세그먼트 N) · 쉬운 Top3(실측/예상 표시)
서치: 채널별 조합 N · 상세 N · 중복 제거 후보 N · 추천 N · 조건부 N · 대상사 제외 N · 1촌 이메일 확인 N
저장: 캡처 N = verified N · SQLite N = Supabase N = 원장 N · 대조군 검출 Y/N · 클라우드 이미지 DONE|NOT RUN
메일: 수신 4명 · message_id · 발송 시각 (또는 BLOCKED 사유)
적대 검증: 발견 N · 수정 N · 남은 불확실성
자동화 Top3: …
어디까지 실제 실행했고 무엇이 남았는지: 한 줄
```
숫자는 모두 파일에서 계산하고, 옆에 그 파일 경로를 적는다. 증거 원문은 붙이지 않는다.

---

## v2 변경 근거 (실행자는 읽지 않아도 됨)
| 지적 | 출처 | 반영 위치 |
|---|---|---|
| 대상사 현·전 재직자 HARD EXCLUDE 누락 | Codex adv(ChatGPT 규칙) | §1 회사명 변형, §5-1 |
| 학교 순위 가감점 충돌 | Codex adv | §5-6 (배점 제외, 동점 정렬에만) |
| 잦은 이직 감점·예외 누락 | Codex adv | §5-4 |
| 국적·언어·취업자격 | ChatGPT | §5-5 |
| 검증기가 원장을 안 봄·스크린샷 바이너리 미검증 | Codex adv #1·#2 | 저장 규칙, §6 (a)(b)(c)(d) |
| verify_storage.py 복사 실행 불가 | Codex adv #3, rescue | `recruiting_archive.py` 캡처 단위 저장·양측 readback으로 교체 |
| qa_quotes.py가 메일 본문을 검사하지 않음 | Codex adv #4, rescue | §7 `<q data-src>` 인용 QA |
| run_id 중복 발송 검사 불가 | Codex adv #5, rescue | §7 제목에 RUN_ID → 기존 in:sent 제목 검사 |
| 수신 주소 추측 | ChatGPT, Codex adv | §0-6 코드에서 확인 |
| 첫 페이지만 수집 | Codex adv #6 | §1 페이지네이션·AC-1 합집합 |
| 변형을 다 쓰기 전 종료 | Codex adv #7 | §4 커버리지 선행 |
| 고유 URL 수 비교 오류 | Codex adv #8 | 저장 규칙: 캡처ID 단위 |
| `--store-dir` 누락 | Codex adv #9, rescue | §1·§2 |
| 자기 폴더를 동시 실행으로 오판 | Codex adv #10 | §0-2 생성 전 검사·OWNER pid |
| recruiting_browser.py는 잡코리아 전용 | Codex adv #11 | 참조 제거 |
| 저장 부분 실패 시 발송 규칙 | Codex adv #12 | §7 게이트 `[PARTIAL]` |
| 점수 재계산 검사 없음 | Codex adv #13 | §5 AC-5 |
| 자동화 백브리핑 근거 없음 | Codex adv #14 | actions.jsonl, §9 |
| 예상/실측 난이도 혼동 | Codex adv(2차) | §8 |
| 캡처별 양측 대조·이미지 별도 상태·QA 인용 최소 2개·기간 무제한 중복 검사·페이지 순회·고용주 칸 한정 제외·profiles 원문 파일 | Codex 확인 검증(v2 REVISE) | 저장 규칙, §4, §5-1, §6, §7 |
| 학교 순위의 동점 정렬 사용 유지 | 사장님 9/23 결정·SOT 9/28 (Codex는 금지 권고) | §5-6 — 사장님 확인 필요 |
| 단계별 DONE/PARTIAL/BLOCKED/NOT RUN | ChatGPT | §10 |
| 멈춤 신호·rescue 개입 조건 | ChatGPT §11 | 절대 규칙 |
