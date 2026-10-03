# Aside 브라우저 제어 프랙티스 — AISearch 적용 (SOT)

- 제정: 2026-10-03, 사장님 지시("Aside 브라우저의 자동화 기능·브라우저 제어기법을 모두 숙지해 AISearch 에 적용")
- 적용: Claude·Codex AISearch(`search` 스킬, `[aisearch]` 메일을 내는 모든 서치 세션)의 사람인·잡코리아·LinkedIn RPS·Gmail 화면 작업
- 상위 정본: 접속 권한·사람 개입·LinkedIn 범위는 `humansearch-browser-contract.md`, 검색어·필터·사이트별 관찰은 `search-query-and-filter-rules.md`. 이 문서는 둘과 충돌하지 않는 **실행 방법**만 정한다. 충돌하면 두 정본이 이긴다.

## 1층 — 결론

AISearch 는 사장님 Aside 브라우저의 **이미 로그인된 기존 탭**을 다음 우선순위의 제어 경로 하나로 다룬다.

1. **claude-in-chrome MCP**(Aside 에 붙은 Claude 확장) — 붙어 있으면 이것만 쓴다.
2. **AppleScript `execute … javascript`** — 확장이 세션에 안 붙어 있을 때.
3. **CDP 진단 포트**(`/json/list` + 탭별 WebSocket) — Aside 가 이미 포트를 켠 채로 떠 있을 때만. 포트를 켜려고 재시작하지 않는다.

어느 경로든 공통 안전선은 같다: 새 창·새 탭 0, 탭·창 닫기 0, 사장님 메인 창 활성 탭 변경 0, 자격증명 입력 0, 발송 0. 로그인·캡차·2단계 인증·"multiple sign-ins" 를 만나면 멈추고 사람을 부른다.

Aside 자체의 AI 에이전트(Agent Tabs·Ultrabrowse·에이전트 비밀번호 관리자)는 AISearch 세션이 원격으로 조종하는 대상이 아니다. 그 탭 묶음은 "다른 사용자의 작업"으로 보고 건드리지 않는다.

## 2층 — 판단 근거

**왜 기존 탭 재사용인가** — LinkedIn Recruiter 는 좌석 1개다. 새 탭·새 프로필은 새 세션이 되어 "multiple sign-ins" 충돌을 내고, 자동화 전용 프로필은 2026-07-18 Cloudflare 봇 차단의 실제 원인이었다(`humansearch-v6-founding-spec-2026-08-07.md` §3-2). 2026-09-28 사장님 재발 금지 지시도 같다(`search-query-and-filter-rules.md` 2026-09-28 절).

**왜 이 우선순위인가** — MCP 는 화면 캡처·접근성 트리·클릭 좌표를 한 도구로 주고 사장님이 붙여 둔 경로라 권한 경계가 가장 좁다. AppleScript 는 확장이 없어도 되지만 JS 반환값(문자열)만 받는다. CDP 는 가장 넓은 능력(쿠키·저장소·탭 생성까지)을 열기 때문에 마지막이다(`humansearch-browser-contract.md` §3·§10).

**버린 길** — 포트를 켜기 위한 Aside 재시작(2026-08-14 실측에서 잡코리아 로그인 화면·RPS 계약 선택 화면으로 복원됨), Playwright `connectOverCDP` 전체 attach(탭이 많으면 멈춤), Chrome 사용(Gmail 필터·라벨 작업 포함 Aside 로만 한다는 2026-09-28 지시).

**대가** — 경로가 셋이라 사이트별 요령이 경로마다 조금 다르다. 아래 3층 §4 표가 그 차이를 한 곳에 모은다.

## 3층 — 정본 계약

### 1. Aside 가 무엇인지 (공개 자료 기준, 2026-10-03 조회)

| 항목 | 내용 | AISearch 에서의 의미 |
|---|---|---|
| 정체 | Chromium 기반 독립 데스크톱 AI 브라우저(YC F25). 2026-08-14 실측 내부 엔진 Chrome 151 | Chromium 의 AppleScript 사전·DevTools 프로토콜·탭 백그라운드 스로틀링 규칙이 그대로 적용된다 |
| Agent Tabs | Aside 에이전트 작업별 AI 탭 그룹. 재시작 후 지난 작업 탭이 다시 열리던 버그 수정 기록 있음 | 이 그룹의 탭은 다른 작업자 소유로 보고 재사용 대상에서 뺀다 |
| 에이전트 탭 비포커스 | Blink 를 패치해 에이전트가 연 탭이 포커스를 뺏거나 팝업을 띄우지 않게 함 | 우리 세션의 탭에는 적용된다는 보장이 없다 → 숨김 탭 스로틀링(§4) 규칙을 그대로 지킨다 |
| 추론 모드·Ultrabrowse | 작업별 추론 단계 선택, 최상위 Ultrabrowse 는 장기 자율 실행 | 사장님이 Aside 안에서 직접 맡기는 작업용. AISearch 세션이 조종하지 않는다 |
| 에이전트 비밀번호 관리자 | 작업 단위 범위 권한·접근 감사 로그·Secure Enclave 암호화, 비밀번호를 모델에 노출하지 않음 | AISearch 는 여기에도 접근하지 않는다. 로그인은 언제나 사람 몫 |
| 민감 동작 승인 | 결제·게시·메시지는 사용자 승인 대기(마케팅 문구, 개인정보처리방침에는 명시 없음 ※) | 승인 화면이 떠도 대신 누르지 않는다. 발송 0 원칙은 이 기능과 무관하게 유지 |
| 로컬 메모리 | 기기 안 마크다운 파일로 저장, 작업 기록·산출물은 로컬 데이터 디렉터리 | 후보 원문을 Aside 메모리에 쌓지 않는다. 산출물은 AISearch 아티팩트 경로로만 |

※ = 공개 리뷰·검색 요약 기준이며 aside.com·docs.aside.com 원문은 이 저장소 클라우드 세션에서 네트워크 정책으로 직접 확인하지 못했다. Aside 의 외부 제어 API·MCP·CLI 공개 여부는 확인되지 않았다(§8 `NOT_RUN`).

### 2. 시작 절차 (모든 경로 공통, 매 세션)

1. **경로 판정** — MCP 도구(`tabs_context_mcp`)가 응답하고 Aside 장치가 보이면 경로 1. 아니면 `osascript` 로 Aside 창 목록이 읽히면 경로 2. 아니면 `curl -s http://127.0.0.1:<포트>/json/version` 이 200 이면 경로 3. 셋 다 안 되면 `BLOCKED_NO_CONTROL_PATH` 로 보고하고 멈춘다. 포트 번호는 기억값으로 고정하지 않고 실행 시 확인한다(2026-08-14·08-15 실측값은 45111).
2. **탭 인벤토리** — 전 창의 (창 id, 탭 id, URL, 제목, 활성 여부)를 파일로 남긴다. 순번이 아니라 **id** 로만 가리킨다.
3. **점유 판정** — 최근 1시간 산출물·실행 중 스크립트에 그 탭 id 가 있거나, Aside Agent Tabs 그룹에 속하면 다른 작업 소유다. 건드리지 않는다.
4. **탭 배정** — 보이는 탭이 필요한 일(RPS 결과 목록 수집·사람인 이력서 캡처)은 "자기 창의 활성 탭"인 기존 RPS/사람인 탭. 숨김이어도 되는 일(RPS 프로필 본문 읽기·사람인 목록 수집)은 비활성 기존 탭. 사장님 메인 창의 활성 탭은 바꾸지 않는다.
5. **쓸 탭이 하나도 없을 때만** 사장님께 한 줄 알리고 새 탭 1개를 연다. 작업 후에도 닫지 않는다.
6. **로그인 상태 확인** — URL 이 아니라 화면 DOM 마커로 판정한다(`humansearch-l0-surface-contract.md`). 로그인·계약 선택·캡차·2단계 인증·multiple sign-ins 화면이면 즉시 §6 중단 코드.

### 3. 경로별 기법

#### 경로 1 — claude-in-chrome MCP

- 시작 때 ToolSearch 로 `tabs_context_mcp, navigate, computer, read_page, get_page_text, find` 를 한 번에 불러온다. `tabs_create_mcp`·`tabs_close_mcp` 는 불러오더라도 §2-5 예외 밖에서는 호출하지 않는다.
- `tabs_context_mcp` 로 장치 id 와 탭 목록을 먼저 확인한다(2026-09-14 확인 장치 id `0c136c08` — 값은 바뀔 수 있으니 매번 다시 읽는다).
- 읽기는 `get_page_text`(본문) → `read_page`(구조·ref) → `find`(요소 찾기) 순으로 가벼운 것부터. 클릭은 `find`/`read_page` 의 ref 기반으로 하고, 좌표 클릭(`computer`)은 ref 가 없을 때만.
- 증거 화면은 `computer` 스크린샷으로 남기고, 후보 원문·URL·관찰 시각과 같은 화면인지 대조한다.
- 확장이 조작 중인 탭에서는 다른 확장(예: Valuehire 프로필 아카이버)이 `activeTab` 권한 오류로 캡처하지 못한다 → 본문을 읽은 직후 아카이버 서버 API 로 저장한다(`rps-candidate-ledger-v2-2026-09-17.md` "프로필 아카이빙").

#### 경로 2 — AppleScript (확장 미연결)

- 전제: Aside 의 "Apple Events 의 JavaScript 허용"이 켜져 있어야 한다(Chromium 표준 메뉴 `보기 > 개발자`). 꺼져 있으면 켜는 것은 사람 몫이다. 2026-09-28 세션은 이 경로로 실제 수집했다.
- 앱 이름은 실행 전 `osascript -e 'id of application "Aside"'` 로 확인한다.
- 탭은 **id** 로 지정하고, 창·탭 id 는 `-e` 문자열에 붙여 넣지 말고 `on run argv` 인자로 넘긴다(문자열에 넣으면 실수형으로 바뀌어 실패한다).

```bash
# 인벤토리: 창id<TAB>탭id<TAB>URL (한 줄에 탭 하나)
osascript -e 'tell application "Aside"
  set out to ""
  repeat with w in windows
    repeat with t in tabs of w
      set out to out & (id of w) & tab & (id of t) & tab & (URL of t) & linefeed
    end repeat
  end repeat
  return out
end tell'

# 특정 탭에서 JS 실행 (반환값은 문자열 하나 → JS 쪽에서 JSON.stringify)
osascript -e 'on run argv' \
  -e 'tell application "Aside" to execute (tab id (item 2 of argv as integer) of window id (item 1 of argv as integer)) javascript (item 3 of argv)' \
  -e 'end run' "$WIN_ID" "$TAB_ID" "$JS"
```

- 탭 이동은 새 탭 대신 기존 탭의 `URL` 을 바꾼다(`set URL of tab id … to …`).
- 결과는 반환값으로 받아 곧바로 파일에 쓴다. 페이지 `localStorage` 에 쌓지 않는다(이전 세션 기록 때문에 저장 한도 초과).
- 화면 캡처는 `screencapture -l <CGWindowID>` 로 창 단위로 한다. AppleScript 창 id 는 CGWindowID 가 아니다 — CGWindowID 는 `CGWindowListCopyWindowInfo`(소유자 이름 Aside, 창 제목)로 따로 찾는다.

#### 경로 3 — CDP 진단 포트 (이미 켜져 있을 때만)

- 생존 판정은 `/json/version` 200 **그리고** 대상 탭 존재. 응답이 없다고 브라우저가 죽었다고 보지 않고, 재시작·재실행하지 않는다.
- `/json/list` 에서 대상 탭 하나의 `webSocketDebuggerUrl` 에만 raw WebSocket 으로 붙어 `Runtime.evaluate` 한다(파이썬 `websocket-client` 는 `suppress_origin=True`). 전체 attach(`connectOverCDP`) 금지.
- `Target.createTarget`·`Target.activateTarget`·`Page.bringToFront`·`Target.closeTarget`·`Network.*`·`Storage.*` 쿠키 계열은 호출하지 않는다. 2026-08-15 프롬프트의 "수집 직전 `Page.bringToFront`"는 2026-09-28 지시(메인 창 활성 탭 변경 금지)로 대체됐다 — 보이는 탭이 필요하면 §2-4 배정으로 해결한다.
- 다른 탭의 URL 을 그대로 로그·증거에 남기지 않는다(`hs-observe-url-crash-goal-2026-08-25.md`).

### 4. 공통 제어 요령 (Chromium 동작 기반, 경로 무관)

| 현상 | 원인 | 요령 |
|---|---|---|
| 숨김·가려진 탭에서 타이머가 분 단위로 느려짐 | `document.visibilityState=hidden` 백그라운드 스로틀링 | 대기는 `setTimeout` 이 아니라 바깥(셸·도구 호출) 루프의 폴링으로 한다 |
| RPS 결과 목록이 페이지당 5명만 잡힘 | 화면에 보일 때만 카드를 그림 | 보이는 탭에서 수집, 스크롤 후 카드 수가 멈출 때까지 재수집 |
| `el.focus()` 가 반응 없음 | 창이 앞에 없으면 포커스 이벤트가 안 남 | `focusin` 등 필요한 이벤트를 직접 보낸다 |
| 자동완성 칩이 안 붙음 | 사이트가 click 하나로는 반응 안 함 | `pointerdown → mousedown → mouseup → click` 순서로 보낸다 |
| 한 입력칸이 다른 칸 입력을 날림 | 미확정 입력 폐기 | 칸마다 Return 으로 확정하고 검색 전에 필터 요약을 다시 읽는다 |
| 새로고침 후 보조 함수가 사라짐 | 주입 스크립트는 문서 수명 | 새로고침·이동 뒤 보조 스크립트를 다시 주입하고 빈 상태부터 확인 |
| 본문 텍스트가 안 읽힘 | 닫힌 shadow DOM(사람인 상세 이력서) | 보이는 탭 창 단위 캡처로 읽는다 |
| IIFE 결과가 null | 평가 경로가 마지막 식 값을 못 받음 | `({...})` 객체 직접 반환식이나 `JSON.stringify(...)` 로 끝낸다 |

### 5. 사람 수준 페이싱과 안전선

- 카드·프로필 클릭 간격에 지터를 둔다. 같은 URL 을 연달아 두 번 열지 않는다.
- 같은 방식으로 두 번 막히면 그 후보·조합은 "확인 실패"로 기록하고 넘어간다.
- 발송(InMail·연결 요청·제안·후보 메일) 클릭 0. Aside 의 민감 동작 승인 창도 대신 누르지 않는다.
- 자격증명·인증번호·보안문자 입력 0, 재로그인 시도 0, 다른 세션 로그아웃 0.
- 탭·창 닫기 0, 브라우저 재시작 0, Aside 설정 변경 0(Apple Events JS 허용 포함 — 사람 몫).
- 내부 브리핑 메일 제목 접두사 `[aisearch]claudecode `·`[aisearch]codex `, Gmail 필터·라벨 작업은 Aside 에서만.

### 6. 중단 코드 (만나면 PII 없는 한 줄 보고 후 멈춤, 자동 재개 없음)

| 코드 | 조건 |
|---|---|
| `BLOCKED_NO_CONTROL_PATH` | MCP·AppleScript·CDP 세 경로 모두 응답 없음 |
| `BLOCKED_HUMAN_AUTH` | 로그인 화면·RPS 계약 선택 화면·세션 만료 |
| `BLOCKED_CHALLENGE` | 캡차·2단계 인증·보안 확인 |
| `BLOCKED_SESSION_CONFLICT` | RPS "multiple sign-ins" |
| `BLOCKED_TAB_OWNERSHIP` | 쓸 기존 탭이 모두 다른 작업 소유이고 새 탭 허락을 못 받음 |
| `BLOCKED_JS_DISABLED` | AppleScript JS 실행이 꺼져 있음 |

### 7. 세션 종료

- 다음 세션을 위해 사용한 탭 id·마지막 URL·용도를 산출물에 남긴다(탭은 그대로 둔다).
- 수집 결과·증거·SHA 는 AISearch 아티팩트 경로에, 프로필 본문은 아카이버 API 로 저장한다. 원문·PII 는 Git 에 넣지 않는다.

### 8. `NOT_RUN` 장부

| 항목 | 상태 | 완료로 바꾸는 증거 |
|---|---|---|
| Aside 공식 문서(docs.aside.com) 원문 대조 | NOT_RUN — 클라우드 세션 네트워크 차단 | 로컬 세션에서 원문 확인 후 §1 갱신 |
| Aside 외부 제어 API·MCP·CLI 존재 여부 | NOT_RUN | 공식 문서 근거 |
| Aside 에이전트 탭 비포커스 패치가 외부(MCP·AppleScript·CDP) 탭에도 적용되는지 | NOT_RUN | 숨김 탭에서 RPS 카드 수 비교 실측 |
| `Emulation.setFocusEmulationEnabled` 로 숨김 탭 렌더링 유지 | NOT_RUN — 후보 기법일 뿐 | 메인 창 변경 없이 카드 수가 보이는 탭과 같아지는 실측 |
| 앱 이름 `"Aside"` 의 AppleScript 사전 지원 범위(`execute`, `set URL`) | 2026-09-28 `execute` 사용 기록만 있음 | 로컬 `sdef` 확인 |

### 9. 근거

- 저장소: `search-query-and-filter-rules.md`(2026-09-27·09-28), `humansearch-browser-contract.md` §2-1·§3·§4·§10, `humansearch-v6-founding-spec-2026-08-07.md` §3-1~3-3, `humansearch-journey-master-plan-2026-08-14.md` 72행, `goal-prompts/codex-5position-search-2026-08-15.md`, `goal-prompts/rps-candidate-ledger-v2-2026-09-17.md`
- 공개 자료(2026-10-03 검색): <https://aside.com/features/browser-agent>, <https://docs.aside.com/changelog/native>, <https://www.ycombinator.com/companies/aside>, <https://www.eesel.ai/blog/aside-ai-browser>
- Chromium 백그라운드 스로틀링·포커스: <https://groups.google.com/a/chromium.org/g/blink-dev/c/XRqy8mIOWps>, <https://developer.chrome.com/blog/remote-debugging-port>
