# 엔진별 Aside 화면 조작과 함정 (2026-10-05 실측)

목차: 공통 / Cursor / ChatGPT / Gemini / 응답 파싱 / 재시도

## 공통
- AppleScript `execute (tab id T of window id W) javascript` 로 DOM 을 읽고 쓴다. 격리 월드라 합성 클릭으로 Radix·Angular 메뉴가 안 열릴 수 있다.
- JS 파일은 heredoc(`<<'EOF'`)이나 `printf '%s'` 로 쓴다. zsh `echo` 는 `\n` 을 실제 줄바꿈으로 바꿔 JS 를 깨뜨린다. zsh 에서 `$SHA:h…` 는 경로 수식어 → `"${SHA}:path"`.
- 긴 지시문은 base64 로 넘겨 `decodeURIComponent(escape(atob(b64)))` 로 복원한다.
- 실제 클릭(cliclick)은 최후 수단: ① `document.readyState==complete` ② Aside activate + 대상 탭을 활성 탭으로 ③ **클릭 직전 전면 앱이 Aside 인지 재확인**(아니면 클릭 금지 — 터미널에 클릭이 떨어진다) ④ 클릭 ⑤ 결과(메뉴 열림·칩 생성)로 확인 ⑥ 3회까지 좌표 재계산 ⑦ 원래 앱 activate. 좌표 = `screenX + rect.x`, `screenY + (outerHeight-innerHeight) + rect.y`. 창이 이미 활성이면 두 번 클릭은 메뉴를 열었다 닫는다.
- 가려진(hidden) 탭은 오버레이 메뉴를 그리지 않는다. 설정 확인은 메뉴 대신 설정 페이지 URL 로.

## Cursor (cursor.com/agents, Cloud Agent)
- 새 채팅: `/agents` 로 이동 → 저장소 버튼 `aria-label="sangmokang/Valuehire_v6"`, 모델 버튼 텍스트 `/^Grok [0-9]/`("Try Grok Bot" 버튼과 구분), 입력창 `div[contenteditable=true]`, 전송 `button[aria-label="Send message"]`. 세션 URL `/agents/bc-…`.
- Cloud Agent 는 저장소를 직접 clone 해 SHA 를 확인한다(저장소 전체 접근). 원격에 uv·Python 3.14 가 없어 정식 `uv run pytest` 는 대체로 NOT_RUN.
- 사용량: `/dashboard/spending` 의 "Cursor Models … N% used", "On-demand spending is currently disabled". 선불 크레딧 "자동 적용" 문구가 있으면 보고.
- 오류: "Agent encountered an error"(모델 반복 루프) → 새 세션 1회 재시도. 3,500줄 PR 1개 ≈ 포함 사용량 8%p(Pro).

## ChatGPT (프로젝트 LLMCodeReview)
- 새 대화: 프로젝트 URL 로 이동 → 입력창 `[contenteditable=true]`(보이는 것) → **GitHub 칩: `@GitHub` 를 `insertText` 로 넣고 나타난 버튼(텍스트가 "GitHub"로 시작, "Triage" 포함)을 JS click** → 칩 확인은 `innerHTML` 에 `app-mention-name` + `github`. 실패 시에만 실제 클릭(+ 버튼 `aria-label="파일 등 추가"`).
- 큰 붙여넣기(ClipboardEvent paste)는 자동 첨부 "붙여넣은 텍스트"가 된다 → `button[aria-label="붙여넣은 텍스트 첨부 제거"]` 존재로 확인. 본문에 "첨부 마지막 줄/END 표식을 먼저 확인, 안 보이면 TRUNCATED" 지시를 짧게 덧붙인다.
- 전송 `button[aria-label="보내기"]` — 첨부 처리 중엔 잠깐 비활성 → 최대 30초 재시도. 대화 URL `/c/<id>`.
- 응답 영역: `article`·`data-message-author-role` 이 없을 수 있다 → `main.innerText` 전체를 읽는다. 생성 중 표시는 `button[aria-label="중지"]`.
- GitHub 플러그인으로 PR CI 상태까지 조회한다(Grok 은 안 함).

## Gemini (gemini.google.com/app)
- 입력창 `div[aria-label="Gemini 프롬프트 입력"]`(Quill). **paste 이벤트는 무시됨 → `execCommand("insertText")` 로 넣는다.** 길이 검증: 입력창 textContent 길이 = 원문 글자 수 − 줄바꿈 수(정확히 일치해야 누락 없음).
- 전송 `aria-label="메시지 보내기"`, 대화 URL `/app/<id>`, 응답 `model-response`, 생성 중 `aria-label*="중지"`.
- GitHub: `/apps` 의 "확장 프로그램 사용 또는 사용 중지" 스위치가 false 면 미연결 → 켜지 말고 묶음 붙여넣기. "업로드 및 도구 → 더보기 → 코드 가져오기" 경로도 있다(저장소 URL 가져오기).
- "업그레이드" 버튼이 보이면 무료 요금제 가능성 — 한도 문구 감시.

## 응답 파싱
- JSON 은 `<<<TAG … TAG>>>` 표식 사이. 화면 렌더링이 역슬래시를 지우거나(`"$SANDBOX/"` 의 따옴표) `\n` 을 실제 줄바꿈으로 바꾼다 → 검사기는 `json.loads(strict=False)` + 오류 위치 직전 따옴표 이스케이프 복구(최대 40회)를 하고 `_repaired` 표시를 남긴다. 원문은 그대로 보존.
- `tests_executed` 가 문자열 배열로 올 수 있다(검사기에서 처리).

## 재시도 (gpoll2 / mpoll)
| 상황 | 처리 |
|---|---|
| "연결이 해제되었습니다" + 중지 버튼 있음 | 서버 생성 중 → 대기, 3분마다 대화 URL 재오픈 |
| 연결 해제·오류 + 중지 없음 + 결과 없음 2분 | 같은 대화 "다시 시도/재생성" 클릭(최대 2회) |
| 그래도 실패 | 종료값 7 → 드라이버가 새 대화로 1회 재시작 |
| 60분 초과 | 종료값 2, 장부 기록 후 정지 |
