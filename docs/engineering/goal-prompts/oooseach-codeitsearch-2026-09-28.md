# OOOsearch 실행 프롬프트 — 자사 채용공고 기반 인재 서치 (2026-09-28)

`<회사>` 자리만 바꿔 재사용한다: 코드잇 / 뤼튼테크놀로지스 / 스푼랩스 / 여기어때 / 번개장터.
Windows(사장님 메인 PC)와 macOS(MacBook Pro) 양쪽에서 같은 프롬프트로 돈다.

---

너는 Valuehire v6 저장소에서 `<회사>`의 자사 채용공고를 기준으로 라이브 인재 서치를 수행한다.
절차의 정본은 `.claude/skills/codeitsearch/SKILL.md` 다. 읽고 그대로 따른다.

## 대상
- 회사: `<회사>` — `contracts/humansearch/company-careers-sources.json` 에서 항목을 읽는다.
  `harvest.status` 가 `unmapped` 면 같은 파일의 `discovery` 5단계를 먼저 돌려 규칙을 확정하고
  파일을 갱신한 뒤 진행한다. 모르는 채로 `mapped` 로 올리지 않는다.
- 채널: 사람인 → (확장 예정) 잡코리아, 링크드인 RPS.

## 브라우저 (이미 준비됨 — 새로 로그인·자격증명 입력 금지)
- 사장님 **Aside 브라우저**에 채널 로그인 세션이 살아 있다.
- 접속 경로 둘 중 살아 있는 쪽을 쓴다:
  (a) Claude Chrome 확장 — `list_connected_browsers` → `select_browser`.
      확장이 붙은 프로필과 로그인한 프로필이 **다를 수 있다**. 다르면 `switch_browser`.
  (b) CDP 원격 디버깅 — `curl http://127.0.0.1:9225/json/version` 로 확인
      (`contracts/humansearch/saramin-markers.json` 의 `diagnostic_ports`).
- **자격증명 자동 입력 금지.** 로그인 화면이면 멈추고 사장님께 알린다(계정 잠금 위험).

## 사람인 인증 판정 (여기서 가장 많이 속는다)
- `hiring.saramin.co.kr/home` 이 "채용센터 홈"으로 보여도 **로그인 증거가 아니다.**
- `/talent-pool/main/search` → `/talent-pool/main/tutorial` 리다이렉트도 **증거가 아니다.**
  tutorial 은 비로그인도 열리는 공개 페이지다.
- 권위 있는 신호 2개만 본다:
  1. `/zf_user/memcom/talent-pool/main/search` 가 `/zf_user/auth?ut=c` 로 튕기는가
  2. tutorial 페이지 `인재풀 바로가기` CTA 의 **href** 가 `auth?ut=c` 로 렌더되는가
  하나라도 해당하면 **미인증**. 개인회원 로그인과 기업회원 로그인은 별개다.
- 마커 계약: `AfterLoginMenu_logged-menu__`(인증) / `Gnb_login-menu__`(미인증) /
  `ReCaptchaVerify_wrapper__`(캡차 — 즉시 STOP).

## 단계
1. **포지션 전량 수집** → `tools/codeitsearch/data/<company>_positions_<date>.json`
   → `python tools/codeitsearch/ingest_positions.py <snapshot> --dry-run` 으로 세그먼트 분포 확인
   → 실적재. 기존 `jobmarket_positions` 를 쓴다(새 테이블 만들지 않는다). 멱등하다.
   - `get_page_text` 가 `javascript_tool` 보다 안정적이다. JS 는 간헐적으로
     `[BLOCKED: Cookie/query string data]` 로 거부되니 재시도 대신 `get_page_text` 로 바꾼다.
2. **세그멘테이션 + 키워드 확장** — 새 직무를 만나면 `keywords.py` 에 계층을 추가한다.
   **국문과 영문을 모두** 넣는다. "업계 고수가 자기 일을 실제로 부르는 말"을 `expanded` 에 넣는 것이
   이 파이프라인의 핵심 레버다.
3. **필터 구조 전수 매핑** — 검색 전에 필터 팝업을 하나씩 열어 내부까지 `read_page` 로 뜬다.
   버튼·체크박스·범위·저장된 검색조건까지 전부. 결과를
   `contracts/humansearch/saramin-filter-map.json` 에 확정해 쓰고 `page_snapshots` 에 저장한다.
   **기록 없이 검색을 시작하지 않는다.**
4. **라이브 서치** — `page_trace.py open-job` 으로 잡을 열고, 방문·리스팅 페이지를 **전부**
   `record` 한다(`visit`/`listing`/`filter_open`/`filter_apply`/`profile`/`auth_wall`/`blocked`).
   - 새 검색 전 **이전 필터·키워드 리셋 필수**(안 지우면 이전 결과가 그대로 나온다).
   - 봇 회피: 카드 간격 3~8초 지터, 같은 URL 연속 2회 금지, 한 키워드당 최대 20페이지 →
     더 보려면 **키워드 교체**.
   - **몇 명 찾고 멈추지 않는다.** 최고의 매칭이 나올 때까지 키워드를 바꿔가며 계속 찾는다.
     중단하려면 `abort_reason` 을 반드시 남긴다(조용한 종료 금지).
5. **채점** — `scoring.py`. 총점은 **코드가** 계산한다. LLM 은 축별 근거만 낸다.
   - 하드제외: 프리랜서 / 12개월 미만 단기이직 2회+ / 전문대(사람인·잡코리아만) / 비-http URL
   - 이직은 **회사 단위 groupby** 후 `unique_companies - 1` — 승진은 이직이 아니다
   - **인서울 가중치** 는 `contracts/humansearch/in-seoul-universities.json` 에서 읽는다
   - 등록 문턱 **60**(humansearch 70, 자동발송 85와 섞지 말 것)
6. **메일 보고** — `compose_mail.py` 로 본문을 만들고 Gmail MCP 로 발송.
   - 제목 `[aisearch]Claude-win <회사> – <포지션> – N candidates`, 라벨 `aisearch`
   - 수신 sangmokang / kcs / rogan / julian @valueconnect.kr
   - **표 금지, 리스팅 형태.** 적합근거가 길어 표 칸에 넣으면 레이아웃이 깨진다.
   - 발송 단위는 (1) 포지션 1건마다 즉시 / (2) 세그먼트 묶음 완료 후 1회 — 지정 없으면 (2).
7. **마감** — `page_trace.py close-job`, 그리고
   `uv run --with pytest python -m pytest tools/codeitsearch/tests -q`.

## 안전선
- **후보에게 보내는 발송 0회.** 이직제안·InMail·쪽지·지원요청 버튼을 누르지 않는다.
  메일은 내부 4인 보고용만이다.
- 자격증명 입력 0, 캡차 우회 0, 사장님 탭·창 닫기 0.
- 증거(URL + 본문 + `page_snapshots` 기록) 없는 후보는 후보가 아니다.
  `profile_url` 은 href 문자 그대로 복사한다.
- 같은 방식으로 2회 이상 막히면 멈추고 원인을 기록한 뒤 다음 포지션으로 넘어간다.
