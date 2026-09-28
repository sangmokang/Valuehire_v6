---
name: codeitsearch
description: 자사 채용 페이지를 성실히 업데이트하는 기업(코드잇·뤼튼테크놀로지스·스푼랩스·여기어때·번개장터 등)의 포지션 전량을 수집→Supabase 적재→세그멘테이션한 뒤, 사람인(추후 잡코리아·링크드인) 인재풀에서 국문+영문 키워드를 총동원해 적합 인재를 찾고, [aisearch]Claude-win 메일로 리스팅 형태 보고까지 수행한다. 트리거 — "codeitsearch", "coditsearch", "<회사>search"(wrtnsearch·spoonlabssearch·goodchoicesearch·bunjangsearch), "코드잇 서치", "포지션 순회 서치", "인재풀 서치", "자사 채용공고 서치".
---

# OOOsearch — 자사 채용공고 기반 인재 서치 파이프라인

`codeitsearch`는 이 프레임의 **첫 인스턴스**다. 회사만 바꾸면 `wrtnsearch`, `spoonlabssearch`,
`goodchoicesearch`, `bunjangsearch` 가 같은 절차로 돈다. 회사별로 다른 것은
`contracts/humansearch/company-careers-sources.json` 한 파일뿐이고, 나머지 단계·규칙·산출물은 동일하다.

크로스플랫폼이다 — Windows(사장님 메인 PC)와 macOS(MacBook Pro)에서 같은 명령이 돈다.
경로는 항상 저장소 루트 기준 상대경로로 쓰고, 셸 전용 문법에 의존하지 않는다.

## 절대 규칙

1. **후보에게 보내는 발송은 0회.** 이직제안·InMail·쪽지·지원요청 버튼을 누르지 않는다.
   메일은 오직 내부 4인 보고용이다.
2. **자격증명 자동 입력 금지.** 로그인 화면이 뜨면 멈추고 사장님께 알린다(계정 잠금 위험).
3. **증거 없는 후보는 후보가 아니다.** `profile_url`은 href 문자 그대로 복사하고, 방문한 페이지는
   전부 `page_snapshots`에 남긴다.
4. **총점은 코드가 계산한다.** LLM은 축별 근거만 낸다. 총점·등급을 LLM이 쓰면 무효.
5. **몇 명 찾고 멈추지 않는다.** 키워드를 교체해가며 계속 탐색한다. 중단하려면
   `abort_reason`을 반드시 남긴다(조용한 종료 금지).

## 0단계 — 회사 확정

`contracts/humansearch/company-careers-sources.json`에서 회사 항목을 읽는다.
`harvest.status`가 `unmapped`이면 같은 파일의 `discovery` 5단계를 먼저 돌려 규칙을 확정하고
파일을 갱신한 뒤 진행한다. **모르는 채로 `mapped`로 승격하지 않는다.**

## 1단계 — 포지션 전량 수집 → Supabase

브라우저(Chrome MCP)로 채용 리스트를 순회한다. 코드잇 기준 실측값:

- 페이지네이션은 `?page=N`, **0-base**, 7페이지, 10건/페이지, 총 62건
- 상세 링크 셀렉터 `a[href^="/c/"]`, `posting_id`는 `/c/` 뒤 세그먼트
- 카드가 반응형으로 **3벌 중복 렌더**된다 → 앞 10개만 취하거나 `posting_id`로 dedupe

수집 팁(실측):
- `get_page_text`가 `javascript_tool`보다 안정적이다. JS 실행은 간헐적으로
  `[BLOCKED: Cookie/query string data]`로 거부된다 — 이때는 재시도하지 말고 `get_page_text`로 바꾼다.
- JS에서 `await`/`setTimeout`/`.click()` 조합은 특히 자주 막힌다. 페이지 이동은 `navigate`로 한다.

스냅샷 JSON을 `tools/codeitsearch/data/<company>_positions_<date>.json`에 쓰고 적재한다:

```bash
python tools/codeitsearch/ingest_positions.py tools/codeitsearch/data/<snapshot>.json --dry-run
python tools/codeitsearch/ingest_positions.py tools/codeitsearch/data/<snapshot>.json
```

- 대상 테이블은 **기존 `jobmarket_positions`**다(새 테이블 만들지 않는다). 요약은 `jobmarket_snapshots`.
- `(platform, snapshot_date, source_file)` 기준 delete→insert 라 **재실행이 멱등**하다.
- `jobmarket_positions.id`는 과거 벌크 적재로 시퀀스가 어긋나 있어 `next_id()`로 명시 할당한다.

## 2단계 — 세그멘테이션 + 국문·영문 키워드 확장

`tools/codeitsearch/segmentation.py` + `keywords.py`가 담당한다.

- 세그먼트는 snake_case (`software_engineering`, `product_design`, `sales` …).
- **`searchable` 판정**: 정규직 + 상시채용 + 강사·멘토/인재풀/콘텐츠파트너 아님.
  프리랜서·계약직·인턴 포지션은 적재는 하되 인재 서치 대상이 아니다.
- 키워드는 4계층 — `core` / `expanded` / `stack` / `preferred`.
  **국문과 영문을 모두 넣는다.** 한 언어만 넣으면 한글로만 직무를 쓰는 국내 경력자와
  영문 타이틀만 쓰는 시니어가 번갈아 누락된다. 테스트가 이를 강제한다
  (`test_sourceable_segments_carry_both_korean_and_english`).
- 새 직무를 만나면 `keywords.py`에 계층을 추가한다. "업계 고수가 실제로 자기 일을 부르는 말"을
  `expanded`에 넣는 것이 이 파이프라인의 핵심 레버다.

## 3단계 — 채널 인증 확인 (사람인)

**여기서 대부분 막힌다. 아래 판정을 그대로 따른다.**

계약: `contracts/humansearch/saramin-markers.json`

| 신호 | 의미 |
|---|---|
| `AfterLoginMenu_logged-menu__` / `AfterLoginMenu_company-info__wrapper__` 존재 | 기업 인증됨 |
| `Gnb_login-menu__` 존재 | 미인증 |
| `ReCaptchaVerify_wrapper__` 존재 | 캡차 — 즉시 STOP |

**함정 (2026-09-28 실측):**
- `hiring.saramin.co.kr/home`이 "채용센터 홈"으로 보여도 **기업 로그인 증거가 아니다.**
- `/zf_user/memcom/talent-pool/main/search` → `/talent-pool/main/tutorial` 리다이렉트도
  **로그인 증거가 아니다.** tutorial은 비로그인도 열리는 공개 온보딩 페이지다.
- **권위 있는 신호 2개**: (a) `/talent-pool/main/search`가 `/zf_user/auth?ut=c`로 튕기는가,
  (b) tutorial 페이지의 `인재풀 바로가기` CTA href가 서버에서 `auth?ut=c`로 렌더되는가.
  둘 중 하나라도 해당하면 **미인증**이다.
- 개인회원 로그인과 기업회원 로그인은 **별개**다. 개인으로 로그인돼 있어도 인재풀은 막힌다.
- 확장이 붙은 Chrome 프로필과 사장님이 로그인한 프로필이 **다를 수 있다.**
  `list_connected_browsers` → `switch_browser`로 확인하고, 그래도 안 되면 사장님께
  "확장이 붙은 창에서 기업회원 로그인" 또는 "그 창에 확장 설치"를 요청한다.
- repo 계약은 CDP 포트(9225)도 지원한다. `curl http://127.0.0.1:9225/json/version`로 살아있는지 확인.

## 4단계 — 필터 구조 전수 매핑 (검색 전 필수)

**검색을 시작하기 전에 필터 UI를 끝까지 이해하고 저장한다.** 팝업 안쪽까지 들어가서
버튼·체크박스·범위 슬라이더·저장된 검색조건까지 전부 기록한다.

절차:
1. `read_page --filter interactive`로 필터 영역의 모든 요소와 ref를 뜬다.
2. 필터를 **하나씩 열어** 팝업 내부를 다시 `read_page`로 뜬다 (`action: filter_open`).
3. 각 필터의 (이름, 입력 타입, 선택지 전체, 적용 시 URL/요청 변화)를 기록한다.
4. 전부 `page_snapshots`에 `interactive_elements`로 저장한다.
5. 매핑 결과를 `contracts/humansearch/saramin-filter-map.json`에 확정해 쓴다.

기록 없이 검색을 시작하지 않는다 — 다음 실행에서 같은 탐색을 반복하게 된다.

## 5단계 — 라이브 서치

```bash
JOB=$(python tools/codeitsearch/page_trace.py open-job \
        --command codeitsearch --params-file params.json --requested-by claude-win)
python tools/codeitsearch/page_trace.py record --job-id "$JOB" --snapshot-file snaps.json
```

- **방문 페이지와 리스팅 페이지를 모두 저장한다.** `action`은
  `visit` / `listing` / `filter_open` / `filter_apply` / `profile` / `auth_wall` / `blocked` 중 하나.
- 새 검색 전 **이전 필터·키워드를 반드시 리셋**한다(안 지우면 이전 결과가 그대로 나온다).
- 봇 회피: 카드 클릭 간격 지터(3~8초), 같은 URL 연속 2회 열지 않기, 페이지 내 카드 순서 랜덤,
  한 키워드당 최대 20페이지 → 더 보려면 **키워드를 교체**한다.
- 캡차·2FA 감지 즉시 STOP, `action: blocked`로 기록.

## 6단계 — 채점 (`scoring.py`)

- 하드제외: **프리랜서** / **12개월 미만 단기이직 2회+** / 전문대(사람인·잡코리아만, 링크드인 제외)
  / 비-http profile_url.
- 이직 횟수는 **회사 단위 groupby 후 `unique_companies - 1`**. 같은 회사 내 승진은 이직이 아니다.
- 단기이직 카운트에서 **현재 재직 중인 회사는 제외**한다(3개월차는 아직 이직한 게 아니다).
- 배점 100 = 직무적합 40 + 학벌 25 + 재직안정성 20 + 우대 15.
  **인서울 가중치**는 `contracts/humansearch/in-seoul-universities.json`에서 읽는다(코드 하드코딩 금지).
- 열람 순서(triage): 인서울+OTW → 인서울+Non-OTW(현직 2년+) → 그 외+OTW → 그 외+Non-OTW(2년+)
  → 나머지는 버리지 않고 `triage_deferred`.
- **aisearch 등록 문턱은 60** (humansearch 70, 자동발송 85와 섞지 말 것).

## 7단계 — 메일 보고

```bash
python tools/codeitsearch/compose_mail.py --results results.json --out mail.json
```

- 제목: `[aisearch]Claude-win <회사> – <포지션> – N candidates`
- 수신: sangmokang / kcs / rogan / julian @valueconnect.kr (4인)
- 라벨: `aisearch`
- **본문은 표가 아니라 리스팅.** 적합근거가 길어 표 칸에 넣으면 레이아웃이 깨진다.
  블록 구조: `Summary` → `회사/조직 맥락` → `Top candidates` → 후보별
  `Current/Location/Education/Sources/Career Summary/Why Match/Risks / Gaps` → `Candidate Pool / Hiring Insight`.
- **발송 단위는 둘 중 하나를 사장님이 고른다.**
  (1) 포지션 1건 끝날 때마다 즉시 발송, (2) 세그먼트로 묶인 포지션군 완료 후 1회 발송.
  지정이 없으면 **(2) 세그먼트 단위**를 기본으로 한다 — 세그멘테이션을 한 이유와 맞는다.
- 후보가 0명이면 0명이라고 쓰고 사유를 적는다. 빈 결과를 성과처럼 포장하지 않는다.

발송은 에이전트가 Gmail MCP(`send_message` → `label_message`)로 한다.

> **알려진 제약**: 현재 Gmail 커넥터에 `gmail.labels` / `gmail.modify` 스코프가 없어
> 라벨 생성·부착이 거부된다(`Insufficient scope`). 사장님이 한 번 스코프를 승인하거나
> Gmail에서 `aisearch` 라벨을 직접 만들어야 한다. 그 전까지는 제목 프리픽스로만 식별된다.

## 8단계 — 마감

```bash
python tools/codeitsearch/page_trace.py close-job --job-id "$JOB" --status done --summary-file summary.json
uv run --with pytest python -m pytest tools/codeitsearch/tests -q
```

`--status`는 `done` / `blocked` / `failed`. 막혔으면 `blocked` + `--error`에 사유를 남긴다.

## 확장 (잡코리아 · 링크드인)

`company-careers-sources.json`의 `channels`에 `jobkorea`, `linkedin`이 `planned`로 있다.
채널을 추가할 때 필요한 것은:
1. 인증 마커 계약 (`contracts/humansearch/<channel>-markers.json`)
2. 필터 구조 매핑 (4단계를 그 채널에 대해 수행)
3. `scoring.py`의 채널별 예외 — 링크드인은 **학교 하드컷 없음**
4. `page_trace.py`의 `platform` 값만 바꾸면 기록은 그대로 돈다
