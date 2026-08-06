---
name: gptreview
description: ChatGPT.com에서 코드에 대한 적대적(비판적) 리뷰를 받는다. 브라우저 탭을 열어 프롬프트를 자동 입력하고 응답을 자동으로 읽어와 저장한다. "챗지피티로 리뷰", "gpt한테 검토받아", "적대적 검증" 등에서 트리거.
---

# /gptreview — ChatGPT 적대적 코드 리뷰

코드를 ChatGPT.com에 자동으로 올리고, 가장 냉정한 비판을 받아 로컬에 저장한다.
이 스킬을 실행하는 Claude Code 세션 자신이 `mcp__claude-in-chrome__*` 도구를 **직접 호출**한다.
Node.js 스크립트로 브라우저를 대신 제어하지 않는다 — 브라우저 제어는 도구 호출로만 가능하다.

## 절대 규칙 — 로그인은 사용자 몫

**비밀번호를 어떤 필드에도 입력하지 않는다.** 사용자가 이미 승인/제공했더라도 예외 없다.

- claude-in-chrome은 사용자의 기존 Chrome 세션을 공유하므로 평소 로그인되어 있다면 그대로 사용된다.
- 로그인이 안 되어 있는 게 확인되면, 사용자에게 "ChatGPT 로그인이 필요합니다. 브라우저에서 직접 로그인해주세요"라고 안내하고 로그인 완료 확인을 받은 뒤에만 다음 단계로 진행한다.
- 이메일 자동 입력도 하지 않는다 (아이디를 다르게 쓰고 있을 수 있음). 전부 사용자가 직접.

## 실행 절차

### 0. 도구 준비
브라우저 도구가 로드되어 있지 않으면 먼저 로드한다:
```
ToolSearch query: "select:mcp__claude-in-chrome__tabs_context_mcp,mcp__claude-in-chrome__navigate,mcp__claude-in-chrome__computer,mcp__claude-in-chrome__read_page,mcp__claude-in-chrome__tabs_create_mcp,mcp__claude-in-chrome__get_page_text,mcp__claude-in-chrome__find"
```

### 1. 리뷰 대상 결정
- 인자로 파일 경로가 오면 `Read`로 읽는다.
- 인자가 없으면 `git diff` / `git diff --staged` 결과를 대상으로 삼는다.
- 대상이 없으면 사용자에게 어떤 파일/코드를 리뷰할지 묻는다.
- 코드가 50KB를 넘으면 핵심 파일 위주로 추리고, 잘라냈다는 사실을 사용자에게 알린다 (silent truncation 금지).

### 2. 브라우저 탭 준비
```
mcp__claude-in-chrome__tabs_context_mcp({ createIfEmpty: true })
mcp__claude-in-chrome__tabs_create_mcp()
mcp__claude-in-chrome__navigate({ tabId, url: "https://chatgpt.com/" })
```

### 3. 로그인 상태 확인
`mcp__claude-in-chrome__get_page_text` 또는 `read_page`(filter: "interactive")로 페이지를 확인한다.
- "메시지 입력" / "Message ChatGPT" 같은 채팅 입력창이 보이면 → 로그인됨, 4단계로.
- "로그인" / "Log in" 버튼만 보이면 → 로그인 안 됨.
  - 사용자에게 알린다: "ChatGPT 로그인이 필요합니다. 브라우저 탭에서 직접 로그인해주세요. 완료되면 알려주세요."
  - 사용자 확인이 올 때까지 다음 단계로 진행하지 않는다. (다시 로그인 상태 확인 후 진행)
  - CAPTCHA나 2단계 인증이 뜨면 그것도 사용자가 직접 처리하게 하고, 절대 우회를 시도하지 않는다.

### 4. 새 대화 시작 + 프롬프트 입력
`find({ query: "new chat button" })`으로 새 대화 버튼을 찾거나, 이미 빈 대화면 생략한다.

아래 템플릿으로 프롬프트를 조립한다:

```
다음 코드를 가장 냉정하게 비판해줘.

평가 관점:
- 보안 취약점 (OWASP Top 10, 입력 검증, 인증/인가)
- 성능 문제 (메모리 누수, 알고리즘 복잡도, N+1 쿼리)
- 유지보수성 (복잡도, 스타일, 가독성)
- 엣지 케이스 (경계값, 예상 못한 입력)
- 에러 핸들링 (실패 경로, 타임아웃, 재시도)
- 테스트 커버리지 (테스트 불가능한 부분)

각 문제마다: (1) 문제 설명 (2) 왜 문제인지 (3) 구체적 개선안.
모르는 부분은 말하지 말고 확실한 문제만 지적해줘.

---
[여기에 코드 또는 git diff]
```

사용자가 추가 지시사항(`--extra "..."`)을 줬으면 프롬프트 끝에 덧붙인다.

`find({ query: "message input box" })`로 입력창을 찾고,
`mcp__claude-in-chrome__computer({ action: "left_click", ref: ... })`로 클릭 후
`mcp__claude-in-chrome__computer({ action: "type", text: fullPrompt })`로 입력한다.
입력창에 텍스트가 다 들어갔는지 스크린샷으로 확인한 뒤 Enter로 전송한다.

### 5. 응답 대기 및 수집
응답이 스트리밍되는 동안 "생성 중지" 버튼이 떠 있다. `computer({action:"wait", duration:5})`를 반복하며
`read_page({filter:"interactive"})`로 정지 버튼이 사라졌는지 확인한다 (최대 12회, 총 1분 정도).
끝나면 `get_page_text`로 최신 응답 텍스트를 추출한다.

### 6. 결과 저장
`Write` 도구로 프로젝트 루트에 저장:

```
gptreview-<YYYYMMDD-HHMMSS>.md
```

내용:
```markdown
# ChatGPT 적대적 코드 리뷰

**날짜**: <타임스탬프>
**대상**: <파일 경로 또는 "git diff">

## 원본 코드
\`\`\`
<코드>
\`\`\`

## ChatGPT 리뷰 결과

<get_page_text로 추출한 실제 응답 전문>
```

### 7. 사용자에게 보고
저장된 파일 경로와 핵심 지적사항 3~5개를 요약해서 대화창에 보여준다. 전체 리뷰는 파일을 확인하도록 안내한다.

## 실패/중단 처리
- 로그인 대기가 3분을 넘으면 사용자에게 계속할지 물어본다.
- ChatGPT 응답이 1분 넘게 안 끝나면 중간 상태라도 저장하고 사용자에게 알린다.
- 브라우저 도구 호출이 2~3회 연속 실패하면 재시도를 멈추고 무엇이 실패했는지 사용자에게 보고한다 (같은 실패를 반복하지 않는다).
