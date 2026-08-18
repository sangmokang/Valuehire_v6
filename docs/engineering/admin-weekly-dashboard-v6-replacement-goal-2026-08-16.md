# 관리자 주간 대시보드 전면교체 목표·구현 프롬프트 — 2026-08-16

> 작성자: Codex 본체
> 현재 단계: 요구사항 확정과 구현 프롬프트 작성만 완료 대상으로 삼는다. 제품 코드 작성·ClickUp 쓰기·운영 전환은 아직 시작하지 않는다.
> 위험 등급: L3 — Gmail 개인정보, ClickUp 운영 쓰기, 관리자 인증, 기존 서비스 전환이 한 작업에 걸쳐 있다.

## 1층 — 결론

새 관리자 화면은 기존 프로그램을 고치는 방식이 아니라 빈 저장소에 새로 만든다. 다만 과거 4·5·6세대에서 찾은 후보 기록은 버리지 않고, 새 저장소가 이해하는 한 가지 형식으로 옮겨 주간 실적에 이어 붙인다.

sangmokang 발신함에서 실제 표본을 확인했다. 추천 표식으로 시작한 메일 5건과 포지션 표식으로 시작한 메일 1건 모두 한 통 안에 글자 본문과 꾸민 본문이 함께 있었고, 그중 4건에는 이전 대화가 숨은 구조로 붙어 있었다. 따라서 메일 대화방 전체도, 글자 본문 전체도 그대로 복사하면 안 된다. 한 번 보낸 그 메시지에서 이전 대화와 자동 서명을 제거한 업무 본문만 ClickUp에 넣어야 한다.

현재 ClickUp 목록도 읽기 전용으로 확인했다. 추천은 고객사추천 칸에 넣을 수 있다. 포지션은 세부 직무 칸이 12개로 나뉘어 있지만 “일반 엔지니어” 칸은 없다. 직무를 한 칸으로 확정할 근거가 부족하면 임의로 기타에 숨기지 않고 임시 수집 칸에 남겨 사람이 분류하게 한다.

월요일 회의가 2026년 34주차라면 보고 대상은 8월 9일 일요일 자정부터 8월 16일 일요일 자정 직전까지다. 즉 8월 9일 일요일부터 8월 15일 토요일에 실제로 일어난 일만 센다.

아직 정하거나 받아야 할 것은 다섯 가지다. 새 관리자 화면의 개발 기반, 월요일 회의를 찾을 구글 캘린더 일정의 고유값, 인증된 기존 화면 캡처, 메일·후보 자료 보관기간, 분류가 애매한 포지션을 운영자가 언제까지 정리할지다. 아래 프롬프트는 이 값이 확정되지 않아도 계약·합성 시험·화면 골격까지 진행하되, 실제 계정 수집·ClickUp 쓰기·운영 주소 교체 앞에서는 반드시 멈추게 작성했다.

## 2층 — 판단 근거

### 결정 카드 1 — 기존 세대와 실행상 완전히 분리한다

> **무엇을** — 새 관리자 제품은 `apps/admin`이라는 독립 경계에 만들고, 실행 중에는 4·5세대 저장소·파일·환경값·데이터베이스를 읽지 않는다.
> **왜** — 현재 6세대 저장소에는 관리자 제품이 없으므로 부분 수정보다 새 경계를 세우는 편이 실제 상태와 맞다. 과거 후보 기록은 중립적인 반출 파일을 한 번 받아 새 데이터베이스에 적재한다.
> **버린 길** — 4세대 화면을 복사하거나 iframe으로 감싸는 길은 버린다. 모양만 같아도 오래된 집계 방식과 실행 의존성이 다시 들어오기 때문이다.
> **대가** — 관리자 인증, 화면 기반, 데이터 저장소, 배포 단위를 처음부터 정해야 해서 첫 화면까지 시간이 더 든다.
> **되돌리기** — 새 서비스는 별도 주소에서 먼저 띄우고 기존 주소의 연결만 되돌린다. 데이터 적재는 원본 세대와 반출 지문을 남겨 재실행할 수 있게 한다.

### 결정 카드 2 — 메일은 대화방이 아니라 개별 메시지의 업무 본문만 쓴다

> **무엇을** — Gmail의 개별 메시지 조회만 사용한다. 꾸민 본문에서 `gmail_quote` 계열 이전 대화와 `gmail_signature` 계열 자동 서명을 제거한 뒤 글자로 바꾼다. 꾸민 본문이 없을 때만 글자 본문의 인용 시작점을 잘라낸다.
> **왜** — 실제 표본 6건 중 4건에서 꾸민 본문에 이전 대화 구조가 있었다. 기존 4세대 방식처럼 첫 `text/plain` 전체를 선택하면 과거 답장까지 ClickUp에 복사될 수 있다.
> **버린 길** — Gmail 대화방 전체 조회, 첫 글자 본문 무조건 채택, 첨부파일 포함, 본문 유사도만으로 자동 합치기를 버린다.
> **대가** — 드물게 작성자가 일부러 인용한 문장이나 서명 안의 업무 정보를 제거할 수 있다. 원문 메시지 고유값과 본문 지문을 남겨 재검토할 수 있게 한다.
> **되돌리기** — 본문 추출 규칙에 버전을 붙인다. 새 규칙이 틀리면 Gmail의 같은 메시지를 다시 읽어 새 버전으로 재생성하되 기존 ClickUp 글을 조용히 덮지 않고 변경안으로 남긴다.

### 결정 카드 3 — 주차 이름과 집계 기간을 분리한다

> **무엇을** — 주차 이름은 회의가 속한 국제 주차 번호를 사용하고, 실적 기간은 그 주의 직전 일요일부터 토요일까지로 따로 저장한다.
> **왜** — “34주차 회의”와 “그 회의에서 보는 8월 9~15일 실적”은 같은 뜻이 아니다. 두 값을 섞으면 월요일 기준 기존 집계가 되살아난다.
> **버린 길** — 4세대의 월요일 00:00부터 다음 월요일 00:00 방식, 자료를 가져온 시각으로 사건 시각을 대신하는 방식을 버린다.
> **대가** — 회의 날짜, 실적 시작, 실적 종료를 모두 저장해야 한다. 늦게 들어온 자료는 이미 확정한 보고서를 새 판으로 추가해야 한다.
> **되돌리기** — 경계 계산 함수를 한 곳에 두고, 주차별 원자료는 보존한다. 경계 해석이 바뀌면 새 판을 계산하되 과거 판은 삭제하지 않는다.

### 결정 카드 4 — 포지션은 현재 ClickUp 상태명에만 넣는다

> **무엇을** — 실행 직전에 ClickUp 목록의 실제 상태명을 읽고 저장된 계약과 같은지 검사한다. 정확히 한 직무로 정해질 때만 그 상태로 옮기며, 애매하면 `scraped`에 둔다.
> **왜** — 현재 목록에는 일반 “엔지니어” 상태가 없고 `backend/fullstack/cto`, `ai/ml/data`, `frontend`, `app`, `devops/sre/security/qa`처럼 나뉜다. 제목과 본문 근거 없이 한 곳을 고르면 주간 실적과 운영 보드가 함께 틀어진다.
> **버린 길** — 모든 엔지니어를 backend로 보내는 길과 애매한 항목을 자동으로 `etc`에 보내는 길을 버린다.
> **대가** — 일부 메일은 사람 확인이 필요하고 “분류 완료” 숫자가 바로 늘지 않는다.
> **되돌리기** — 분류 계약 파일만 새 판으로 바꾸고, 아직 쓰지 않은 항목을 다시 분류한다. 이미 쓴 항목은 변경 의도와 확인 결과를 남긴 뒤 이동한다.

### 결정 카드 5 — AI Search 숫자는 합계보다 원자료를 먼저 보존한다

> **무엇을** — 4·5·6세대의 AI Search와 Human Search에서 후보 한 건이 발견될 때마다 원자료 행을 보존하고, 주간 합계는 그 행에서 계산한다.
> **왜** — 합계만 남기면 나중에 세대·검색 방식·채널·포지션별로 왜 숫자가 달라졌는지 분석할 수 없다.
> **버린 길** — 주간 숫자만 저장하거나 이름이 같은 후보를 가져오는 시점에 삭제하는 길을 버린다.
> **대가** — 저장량과 개인정보 관리 부담이 늘고, “발견 건수”와 “겹치지 않는 후보 수”를 따로 설명해야 한다.
> **되돌리기** — 원자료는 그대로 두고 계산 규칙 버전만 바꾼다. 잘못된 반출 묶음은 출처와 지문으로 격리하고 새 묶음을 적재한다.

### 지금 확인된 어려움과 미확정

1. **개발 기반 미확정** — 6세대 저장소는 부트스트랩 상태이며 관리자 웹 기술 선택이 없다. 이 문서는 `apps/admin` 경계만 확정하고 특정 틀의 설치는 첫 설계 기록에서 결정하게 한다.
2. **구글 캘린더 일정 고유값 미확정** — “매주 월요일 회의”라는 뜻은 알지만 실제 캘린더·반복 일정 고유값은 받지 못했다. 그 전까지 날짜 계산은 가능해도 “그날 회의가 실제 열렸는지”는 확인할 수 없다.
3. **화면 원본 미확인** — 운영 주소는 로그인 화면으로 이동됐다. 인증된 현재 화면 캡처를 얻지 못했으므로 “같은 모양”의 픽셀 기준은 아직 없다. 4세대 코드나 정적 HTML을 시각 원본으로 복사하지 않는다.
4. **메일 보관 정책 미확정** — 저장소에는 본문을 절대 두지 않는다. 새 데이터베이스에 정제 본문을 얼마나 오래 둘지는 개인정보 보관 정책으로 확정해야 하며, 보관기간·열람권한·삭제 명령이 확정되기 전에는 실제 수집과 ClickUp 쓰기를 시작하지 않는다.
5. **일반 엔지니어 분류 없음** — 현재 ClickUp 실제 상태명에 일반 엔지니어가 없다. 세부 직무를 판단할 근거가 없는 경우 자동 완료시키지 않는다.

## 3층 — 구현 프롬프트와 증거

## 구현 프롬프트 — 이 절을 통째로 실행자에게 전달한다

### 0. 역할과 최종 목표

너는 ValueHire 6세대 관리자 제품의 구현자다. 기존 관리자 코드를 다듬지 말고 주간 대시보드부터 새 코드로 교체한다.

최종 성공은 다음 네 문장으로만 정의한다.

1. 6세대만 있는 깨끗한 작업 환경에서 관리자 제품이 빌드·시험·실행된다.
2. 월요일 회의에 직전 일요일~토요일의 추천·포지션·AI/Human Search 실적이 근거 행까지 내려가며 표시된다.
3. Gmail 한 메시지에서 이전 대화·자동 서명·첨부파일을 제외한 그 당시 업무 본문만 ClickUp에 한 번 등록되고, 실제 등록 결과를 다시 읽어 확인한다.
4. 4·5·6세대 후보 발견 원자료가 출처별로 모두 남아 나중에 다시 집계할 수 있다.

운영 ClickUp 쓰기, 운영 주소 교체, 배포, 메일 발송, 기존 데이터 삭제는 이 프롬프트만으로 허가되지 않는다. 읽기 전용 점검과 별도 시험 환경 구현까지 마친 뒤 멈춘다.

### 1. 시작 자격과 정본

1. 먼저 `AGENTS.md`, `docs/sot/INDEX.md`, `docs/sot/coding-principles.md`, `docs/sot/verification-commands.md`, `docs/sot/git-workflow.md`, `docs/sot/hook-contracts.md`를 전부 읽는다.
2. `bash scripts/session-status.sh`가 세 줄 모두 끝나지 않으면 시작 자격을 `NOT_RUN`으로 기록한다. 멈춘 이유를 조사하되 합격으로 바꾸지 않는다.
3. 이 문서를 새 작업의 목표 문서로 삼되, 실제 구현 전 `docs/engineering/admin-weekly-dashboard-<phase>-goal-YYYY-MM-DD.md`를 단계별로 만든다.
4. 한 단계당 새 worktree와 `task/<name>` 브랜치를 사용한다. `main`에서 구현하지 않는다.
5. 기존 기능 검색 없이 만들지 않는다. 다만 4·5세대 코드는 읽기 전용 결함 증거로만 보며 복사·import·실행 호출하지 않는다.

```text
SOT precedence:
AGENTS.md
  > docs/sot/*
  > this goal contract
  > phase goal
  > implementation
  > tests
```

→ 무엇이 충돌할 때 어느 문서를 따라야 하는지 고정한다. 시험을 구현에 맞춰 고치는 일을 막는 기준이다.

### 2. 절대 경계

다음 중 하나라도 생기면 실패다.

- 실행 코드가 `/Valuehire_v4`, `/Valuehire_v5` 또는 형제 저장소 경로를 읽는다.
- 실행 코드가 이번 조사에만 사용한 4세대 `.env.local` 또는 그 안의 비밀값을 읽는다.
- 4·5세대 패키지, 모듈, 정적 HTML, 데이터베이스 연결값을 import하거나 실행한다.
- 대시보드가 4세대 정적 HTML을 iframe으로 띄운다.
- 운영 시점 집계가 과거 데이터베이스를 직접 조회한다.
- 개인정보 원문·메일 주소·제목·본문·후보 이력서를 git, 일반 로그, 시험 fixture에 넣는다.
- 조회 실패를 0건으로 바꿔 표시한다.
- ClickUp 요청을 보냈다는 사실만으로 등록 성공을 센다.
- 모호한 직무를 `etc`나 임의의 엔지니어 상태로 자동 확정한다.

과거 자료 이동은 다음 중립 반출 계약만 허용한다.

```ts
type LegacyExportEnvelope = {
  schema_version: "candidate-discovery-export/v1";
  source_generation: "v4" | "v5" | "v6";
  source_system: "aisearch" | "humansearch";
  exported_at: string;
  row_count: number;
  sha256: string;
  rows_uri: string;
};
```

→ 새 제품은 과거 프로그램을 아는 대신 버전이 붙은 반출 봉투만 안다. `v4`라는 출처 표시는 분석용 자료값이지 실행 의존성이 아니다.

### 3. 고정 계약과 운영값 분리

운영 주소·목록 고유값·시간대·메일 계정·직무 상태명은 코드에 흩어 쓰지 말고 `contracts/admin-weekly-dashboard/*.json` 한 곳에서 읽는다. 비밀값은 계약 파일에 넣지 않는다.

초기 읽기 전용 확인값은 아래와 같다. 실행 직전에 API로 다시 읽고 다르면 쓰기를 막는다.

```json
{
  "timezone": "Asia/Seoul",
  "recommendation_list_id": "901814621142",
  "recommendation_target_status": "고객사추천",
  "position_list_id": "901814621569",
  "position_statuses": [
    "scraped",
    "backend/fullstack/cto",
    "ai/ml/data",
    "po/pm/기획",
    "frontend",
    "designer",
    "sales/bd",
    "marketing",
    "devops/sre/security/qa",
    "hr/finance/strategy/etc",
    "c-level",
    "app",
    "etc",
    "closedpositions",
    "complete"
  ],
  "allowed_mailboxes": [
    "sangmokang@valueconnect.kr",
    "kcs@valueconnect.kr",
    "julian@valueconnect.kr",
    "rogan@valueconnect.kr"
  ],
  "internal_recipient_domain": "valueconnect.kr"
}
```

→ 2026-08-16 읽기 전용 조회에서 실제 존재한 값이다. 미래에 상태명이 바뀌면 조용히 잘못된 칸에 쓰지 않고 계약 불일치로 멈춘다.

### 4. 주간 경계 계약

회의 날짜는 구글 캘린더 반복 일정의 실제 인스턴스 날짜를 사용한다. 주차는 그 날짜가 속한 국제 주차의 월요일을 기준점으로 계산한다. 따라서 공휴일로 같은 주 화요일에 회의가 옮겨져도 실적 창은 바뀌지 않는다. 일정 고유값이 아직 없으면 계산 시험까지만 만들고 운영 자동화를 시작하지 않는다.

```ts
type WeeklyWindow = {
  meeting_instance_date_kst: string;
  week_anchor_monday_kst: string;
  meeting_iso_week: string;
  event_start_kst: string;
  event_end_exclusive_kst: string;
  timezone: "Asia/Seoul";
};

function weeklyWindow(meetingInstanceDateKst: LocalDate): WeeklyWindow {
  const weekAnchorMonday = meetingInstanceDateKst.startOfIsoWeek();
  return {
    meeting_instance_date_kst: meetingInstanceDateKst.toISODate(),
    week_anchor_monday_kst: weekAnchorMonday.toISODate(),
    meeting_iso_week: meetingInstanceDateKst.toISOWeekLabel(),
    event_start_kst: weekAnchorMonday.minusDays(8).atStartOfDay(),
    event_end_exclusive_kst: weekAnchorMonday.minusDays(1).atStartOfDay(),
    timezone: "Asia/Seoul"
  };
}
```

→ 회의가 속한 주의 월요일에서 8일 전인 일요일 00:00부터 1일 전인 일요일 00:00 직전까지 센다. 종료 시각은 포함하지 않으므로 정확히 일요일~토요일이다. 같은 주 안에서 회의 요일이 바뀌어도 창은 유지된다.

필수 시험값:

```text
meeting=2026-08-17
meeting_iso_week=2026-W34
event_start=2026-08-09T00:00:00+09:00
event_end_exclusive=2026-08-16T00:00:00+09:00
```

→ 현재 주차의 실제 예시다. 이 값이 월요일 8월 10일부터 시작하면 기존 방식이 새어 들어온 것이므로 실패다.

사건 시각은 Gmail `internalDate`, AI/Human Search의 실제 발견 시각 또는 실행 시각을 쓴다. 가져온 시각은 별도 기록한다. 원래 시각이 없으면 추정하지 말고 격리한다.

### 5. Gmail 선별 계약

Gmail 검색식은 후보를 넓게 찾는 도구일 뿐 최종 판정이 아니다. 모든 페이지를 읽은 뒤 코드가 개별 메시지 헤더를 다시 검사한다.

```ts
type RecruitKind = "recommendation" | "position";

function qualifyMessage(message: GmailMessage): RecruitKind | null {
  assert(ALLOWED_MAILBOXES.has(canonicalAddress(message.sourceMailbox)));
  assert(canonicalAddress(message.fromHeader) === canonicalAddress(message.sourceMailbox));
  assert(message.labelIds.includes("SENT"));
  assert(withinHalfOpenWindow(message.internalDate, ACTIVE_WEEKLY_WINDOW));

  const subject = message.subject.normalize("NFKC");
  const kind = subject.startsWith("[추천]")
    ? "recommendation"
    : subject.startsWith("[포지션]")
      ? "position"
      : null;
  if (!kind) return null;

  // Re:/Fwd:/FW: 뒤에 태그가 있는 제목은 '태그로 시작'하지 않으므로 제외한다.
  const recipients = parseAddresses([
    ...message.to,
    ...message.cc,
    ...message.bcc
  ]);
  const hasExternal = recipients.some(
    address => canonicalDomain(address) !== "valueconnect.kr"
  );
  return hasExternal ? kind : null;
}
```

→ 네 명의 보낸편지함, 실제 From 헤더, 정확한 사건 시간, 제목 첫 글자의 태그, 외부 수신자 한 명 이상을 모두 코드로 재검사한다. 제목 앞 공백이나 Re/Fwd 접두어도 허용하지 않으며, 대소문자만 바꾼 내부 주소는 외부로 세지 않는다. 별칭 발신이 실제로 필요하면 별도 계약에 등록하기 전에는 거부한다.

메일은 반드시 `messages.get(messageId, format=full)`로 한 건씩 읽는다. `threads.get`과 대화방 단위 조회는 금지한다. `threadId`는 추적용 값일 뿐 본문 조회 키가 아니다.

제목에서 업무 구조값을 만드는 문법도 결정론적으로 고정한다.

```text
[추천] <고객사>, <포지션> - <후보자>
[포지션] <고객사>, <포지션>

client boundary   = 태그 뒤 첫 comma 또는 ". "
candidate boundary = 추천 제목의 마지막 " - "
```

→ 실제 익명 표본에서 추천 5건은 고객사·포지션·후보자 세 값, 포지션 1건은 고객사·포지션 두 값으로 모두 분리됐다. 원문 값은 보존하되 비교용 값만 NFKC·공백·존칭 꼬리를 정규화한다. 문법에 맞지 않으면 추측하지 않고 `manual_review`이며 ClickUp 쓰기를 막는다.

### 6. 그 당시 업무 본문 추출 계약

본문 추출 결과는 다음 세 값을 구분한다.

```ts
type ExtractedMailBody = {
  message_id: string;
  extractor_version: string;
  business_body_text: string;
  business_body_sha256: string;
  source_part: "sanitized_html" | "plain_fallback";
};
```

→ ClickUp에는 `business_body_text`만 넣는다. 원본 MIME, 첨부파일, 이전 대화, 자동 서명은 넣지 않는다.

추출 순서는 고정한다.

1. 파일 이름이 있는 MIME part는 첨부파일로 보고 제외한다.
2. `text/html`이 있으면 안전한 HTML 파서로 읽는다. 정규식만으로 HTML을 자르지 않는다.
3. `.gmail_quote`, `.gmail_quote_container`, `blockquote[type="cite"]`를 제거한다.
4. `.gmail_signature`, `.gmail_signature_prefix`, `[data-smartmail="gmail_signature"]`를 제거한다.
5. `script`, `style`, 추적 이미지와 위험한 속성을 제거하고 문단·목록·줄바꿈을 보존해 글자로 바꾼다.
6. HTML이 없을 때만 `text/plain`을 쓴다. 첫 인용 경계(`^>`, `On … wrote:`, `보낸 사람:`, `From:`, `Original Message`, `Forwarded message`)부터 뒤를 자르고 표준 서명 구분선 뒤를 제거한다.
7. NFKC, 줄끝, 연속 빈 줄만 정규화한다. 사람 이름·회사명·금액·전화번호·URL을 임의로 고치지 않는다.
8. 결과가 비었으면 ClickUp 쓰기를 금지하고 `manual_review`로 남긴다.

실제 sangmokang 표본에서 파생한 시험 조건은 원문을 fixture로 복사하지 말고 합성 메일로 재현한다.

```text
samples=6
recommendation=5
position=1
all_have_text_plain=6
all_have_text_html=6
html_with_gmail_quote=4
with_attachments=4
external_recipient_counts=[1,1,2,1,1,1]
```

→ 원문 개인정보 없이 구조만 고정한 수치다. 최소한 “꾸민 본문 인용 4건 제거”, “첨부 4건 무시”, “본문이 두 종류여도 한 번만 등록” 시험을 만들어야 한다.

### 7. 중복 방지와 외부 쓰기 계약

중복은 서로 다른 두 문제로 나눈다.

1. **같은 메일 재처리 방지** — `(mailbox, gmail_message_id, kind, target_list_id)` 데이터베이스 고유 제약으로 막는다.
2. **같은 업무 대상 중복 방지** — 추천은 정규화한 `(고객사, 포지션, 후보자)`, 포지션은 `(고객사, 포지션)`이 정확히 같을 때 기존 ClickUp 항목과 연결한다.

유사도 숫자 하나로 자동 합치지 않는다. 정확히 같지 않지만 비슷한 경우는 `manual_review`다. 이미 처리한 메일의 본문이 바뀌었다고 기존 ClickUp 설명을 조용히 덮지 않는다.

```text
DISCOVERED
  -> INTENT_RECORDED
  -> WRITE_STARTED
  -> READBACK_VERIFIED
  -> COUNTED_IN_WEEKLY

failure branches:
  DISCOVERED -> DUPLICATE_LINKED
  DISCOVERED -> MANUAL_REVIEW
  WRITE_STARTED -> UNKNOWN_OUTCOME -> RECONCILE_BEFORE_RETRY
  any state -> FAILED(reason)
```

→ 네트워크가 끊겨 성공 여부를 모르면 곧바로 다시 만들지 않는다. ClickUp을 먼저 다시 읽어 기존 항목을 찾은 뒤에만 재시도한다.

외부 쓰기 순서:

1. 데이터베이스 잠금 또는 원자적 상태 전이로 한 작업자만 권리를 얻는다.
2. 멱등키와 쓰려는 내용을 먼저 기록한다.
3. ClickUp 현재 목록 상태명과 기존 항목을 다시 읽는다.
4. 기본 실행은 dry-run이다.
5. 별도 오너 승인값이 그 실행에만 제공된 경우에만 한 번 쓴다.
6. 생성된 task id를 다시 읽고 목록·상태·본문 지문을 확인한다.
7. 확인된 건만 `READBACK_VERIFIED`로 바꾸고 주간 실적에 센다.

추천 task는 목록 `901814621142`, 상태 `고객사추천`, 설명은 정제 업무 본문만 사용한다. 포지션 task는 목록 `901814621569`에 만들고 분류기가 확정한 실제 상태명으로 옮긴다.

### 8. 포지션 직무 분류 계약

분류기는 ClickUp 상태명을 자유 생성하지 못한다. 반환값은 현재 계약에 있는 직무 상태 하나 또는 `UNCLASSIFIED`뿐이다.

```ts
type PositionCategory =
  | "backend/fullstack/cto"
  | "ai/ml/data"
  | "po/pm/기획"
  | "frontend"
  | "designer"
  | "sales/bd"
  | "marketing"
  | "devops/sre/security/qa"
  | "hr/finance/strategy/etc"
  | "c-level"
  | "app"
  | "etc"
  | "UNCLASSIFIED";
```

→ `scraped`, `closedpositions`, `complete`는 직무가 아니라 수집·종료 상태이므로 분류기의 성공 반환값이 아니다. `UNCLASSIFIED` 항목만 임시로 `scraped`에 둔다.

분류 규칙:

- 제목에서 고객사와 포지션 이름을 결정론적으로 파싱하고 본문은 보조 근거로 쓴다.
- 명시적 직무 사전을 `contracts/admin-weekly-dashboard/position-taxonomy.json`에 둔다.
- 한 포지션이 정확히 한 직무 규칙에만 걸릴 때 자동 확정한다.
- 두 직무 이상에 걸리거나 “Engineer/엔지니어/개발자”만 있으면 `UNCLASSIFIED`다.
- LLM은 분류 제안을 만들 수 있지만 운영 상태를 직접 쓰지 못한다. 제안 입력 지문·프롬프트 버전·허용 enum 검사 결과를 남기고, 결정론 규칙 또는 사람 확인을 통과해야 한다.
- `재무`, `회계`, `인사`, `HR`, `finance`, `strategy`가 명확하면 `hr/finance/strategy/etc` 후보가 된다. `etc`는 명시적으로 다른 직무가 아니라고 판정된 경우에만 쓰며 모름의 기본값이 아니다.

### 9. 원자료 장부

최소 데이터 경계는 다음과 같다. 실제 데이터베이스 문법은 선택한 저장소에 맞추되 의미와 고유 제약은 바꾸지 않는다.

```text
weekly_windows
  id, meeting_instance_date_kst, week_anchor_monday_kst, meeting_iso_week,
  event_start_kst, event_end_exclusive_kst, timezone,
  revision, frozen_at, supersedes_id

mail_events
  id, mailbox, gmail_message_id, gmail_thread_id_for_audit,
  kind, sent_at, encrypted_subject, normalized_subject_hmac,
  external_recipient_count, external_recipient_domain_hmacs,
  extractor_version, business_body_ciphertext, business_body_sha256,
  ingested_at
  UNIQUE(mailbox, gmail_message_id)

mail_business_records
  id, mail_event_id, kind,
  encrypted_client_name, encrypted_position_title,
  encrypted_candidate_name_nullable, business_key_hmac,
  parse_contract_version, parse_state, parse_failure_reason
  UNIQUE(mail_event_id)

clickup_registrations
  id, mail_event_id, target_list_id, target_status,
  idempotency_key, state, clickup_task_id,
  intended_at, attempted_at, readback_verified_at, failure_reason
  UNIQUE(mail_event_id, target_list_id)
  UNIQUE(idempotency_key)

sourcing_runs
  id, source_generation, source_system, source_run_id,
  triggered_at, completed_at, position_count,
  export_sha256, source_row_count, accepted_row_count,
  rejected_row_count, import_state

candidate_discoveries
  id, sourcing_run_id, source_generation, source_system,
  source_record_id, position_source_id, position_title,
  channel, discovered_at, candidate_key_type, candidate_source_key_hmac,
  raw_payload_uri, raw_payload_sha256, imported_at
  UNIQUE(source_generation, source_system, source_record_id)

candidate_discovery_import_errors
  id, sourcing_run_id, source_row_ordinal,
  source_row_sha256, raw_payload_uri, rejection_reason,
  created_at

weekly_snapshots
  id, weekly_window_id, revision, generated_at,
  metric_contract_version, payload, provenance
  UNIQUE(weekly_window_id, revision)
```

→ 메일 원문, 메일에서 파싱한 고객사·포지션·후보 구조값, ClickUp 결과, 후보 발견, 반출 거부 행, 주간 판을 따로 둔다. 합계가 틀리면 어느 원자료 행에서 생겼는지 거꾸로 찾을 수 있어야 한다. 이름으로 만든 비교키는 평문 해시가 아니라 서버 비밀키로 만든 HMAC(= 원문을 되찾기 어렵게 비밀키를 섞은 지문)을 쓴다.

원자료 원칙:

- 4·5·6세대에서 발견한 모든 후보 행을 보존한다. 같은 후보로 보이는 행도 적재 단계에서 삭제하지 않는다.
- 원시 발견 건수, 고유 후보 수, 실행 수, 대상 포지션 수를 별도 계산한다.
- 고유 후보 계산은 분석용 파생값이며 원자료 삭제 근거가 아니다.
- 원자료 전체 내용은 git에 넣지 않고 서버 암호화·역할별 열람·보관기간 삭제가 적용된 접근 제한 저장소에 둔다. 데이터베이스에는 URI와 지문을 둔다.
- 반출 행 수와 새 저장소의 합격·거부 행 수 합이 일치해야 한다. 거부는 이유별 수치를 남긴다.
- 원래 사건 시각이 없는 행은 `imported_at`으로 과거 주차를 꾸미지 않고 격리한다.
- 주간 snapshot을 회의용으로 확정한 뒤 늦은 사건이 들어오면 기존 행을 UPDATE하지 않는다. 이전 판을 가리키는 새 revision과 증가·감소 내역을 만든다.

### 10. 주간 대시보드 표시 계약

첫 화면은 기존 운영 화면의 정보 밀도와 배치를 시각 참고로 삼되, 새 구성요소로 다시 만든다. 인증된 운영 화면 캡처가 없으면 픽셀 일치 판정을 하지 말고 `NOT_RUN`으로 둔다.

주간 카드에는 최소 다음을 표시한다.

- 추천: 조건에 맞는 메일 수, 정확한 업무 대상 수, ClickUp 재확인 완료 수, 중복 연결 수, 사람 확인 대기 수, 실패 수.
- 포지션: 조건에 맞는 메일 수, 직무 확정 및 ClickUp 재확인 완료 수, 분류 대기 수, 실패 수.
- AI/Human Search: 원시 후보 발견 행 수, 고유 후보 수, 실행 수, 포지션 수, 세대별·방식별·채널별 분해.
- 자료 상태: 마지막 성공 시각, 마지막 시도 시각, 지연, `PASS/FAIL/NOT_RUN`, 주간 판 번호.

자료를 못 읽으면 0을 표시하지 않는다. `미집계`와 이유를 표시한다. 현재 상태와 해당 주간 사건을 섞지 않는다.

숫자는 SQL 또는 순수 계산 함수가 만들고 입력 지문과 계산 버전을 함께 저장한다. LLM이 숫자를 작성하거나 메일 본문에서 합계를 추측하지 않는다.

주간 숫자 정의는 다음처럼 고정한다. 모두 `event_start_kst <= event_time < event_end_exclusive_kst`인 원자료만 대상으로 한다.

```text
recommendation_mail_events
  = count(mail_events where kind=recommendation by sent_at)

recommendation_business_unique
  = count(distinct mail_business_records.business_key_hmac
          where kind=recommendation and parse_state=PASS by mail sent_at)

recommendation_clickup_verified
  = count(clickup_registrations where linked mail kind=recommendation
          and state=READBACK_VERIFIED by mail sent_at, as of snapshot time)

recommendation_duplicate_linked / recommendation_manual_review / recommendation_failed
  = count(each registration outcome by linked mail sent_at, as of snapshot time)

position_mail_events
  = count(mail_events where kind=position by sent_at)

position_clickup_verified / position_unclassified / position_failed
  = count(each outcome by linked mail sent_at, as of snapshot time)

sourcing_raw_discoveries
  = count(candidate_discoveries by discovered_at)

sourcing_source_unique_candidates
  = count(distinct candidate_source_key_hmac where candidate_key_type=profile_identity
          by discovered_at)

sourcing_runs
  = count(distinct sourcing_run_id whose triggered_at is in window)

sourcing_positions
  = count(distinct position_source_id among discoveries in window)
```

→ 메일 실적은 “ClickUp에 뒤늦게 넣은 날”이 아니라 고객사에 보낸 날의 주차에 귀속한다. snapshot 시각 뒤에 확인 상태가 바뀌면 새 revision에서만 반영한다. 출처가 다른 후보를 한 사람이라고 단정할 근거가 없으므로 전사 통합 고유 후보 수는 신원 연결 계약 전까지 `NOT_RUN`이며, 화면에는 출처 안에서 확인 가능한 고유 수라고 적는다.

### 11. 구현 단계와 멈춤점

각 단계는 RED 시험 → 최소 구현 → 검증 → 별도 커밋을 지킨다.

#### Phase A — 발견과 계약

- 관리자 기술 기반·인증·데이터 저장소 선택 기록.
- 구글 캘린더 일정 고유값 계약.
- 메일·후보 원자료의 보관기간, 열람 역할, 삭제·재처리 명령 계약. 이 값이 없으면 Phase C 실제 계정 수집으로 넘어가지 않는다.
- ClickUp 두 목록 읽기 전용 스키마 스냅샷과 지문.
- 인증된 기존 화면 캡처와 시각 판정 기준.
- 4·5·6세대 neutral export 목록과 행 수 대조 계획.

종료 조건: 미확정값이 문서에 이름·오너·기한과 함께 있거나 확정돼 있다. 운영 쓰기 없음.

#### Phase B — 순수 계약과 데이터베이스

- 주간 경계, 제목 선별, 외부 수신자 판정, 본문 추출, 직무 분류 순수 함수.
- 합성 MIME 시험과 속성 기반 시험.
- 원자료·상태 전이·고유 제약 마이그레이션.
- 중립 반출 importer의 dry-run과 행 수 대조.

종료 조건: 네트워크 없이 순수 시험이 통과하고, 외부 효과 모듈은 네트워크 차단 시 성공으로 위장하지 않는다.

#### Phase C — 읽기 전용 연결과 그림자 화면

- 네 Gmail 계정 읽기 전용 수집.
- ClickUp 기존 항목·목록 상태 읽기 전용 대조.
- 주간 snapshot 계산 API.
- 별도 주소의 새 주간 대시보드.
- 실제 화면 캡처마다 visual verdict를 저장하고 다음 수정 전에 판정한다.

종료 조건: 실제 한 주 자료를 dry-run으로 재현하고 각 숫자에서 원자료 목록까지 내려간다. 운영 쓰기 없음.

#### Phase D — 제한된 1건 라이브 검증

오너가 별도 승인한 실행에서만 추천 1건 또는 포지션 1건을 쓴다. intent 선기록, 한 번 쓰기, readback을 모두 증명한다. 이 프롬프트 실행자는 승인이 없으면 여기서 멈춘다.

#### Phase E — 운영 주소 전환

오너가 인증된 화면 비교, 숫자 대조, 롤백 명령을 확인한 뒤에만 주소 연결을 바꾼다. 기존 서비스 삭제는 별도 작업이다.

### 12. 기계 인수 기준

1. 깨끗한 6세대 checkout에 형제 저장소가 없어도 build·test·start가 된다.
2. 실행 의존성 그래프에 legacy importer와 4·5세대 경로가 없다.
3. `2026-08-17` 월요일 회의와 `2026-08-18` 화요일로 이동한 같은 주 회의가 모두 정확히 `2026-W34`, `[2026-08-09T00:00:00+09:00, 2026-08-16T00:00:00+09:00)`를 반환한다.
4. 제목이 `Re: [추천]...`, `[기타]...`, 내부 수신자뿐인 메일, 받은편지함 메일은 모두 제외된다.
5. 개별 메시지 합성 fixture에서 `gmail_quote` 이전 대화, Gmail 자동 서명, 첨부파일, 중복 HTML 대체 본문이 ClickUp 업무 본문에 0글자 들어간다.
6. 동시에 같은 Gmail message id를 두 번 처리해도 데이터베이스 intent와 ClickUp task가 각각 1개다.
7. 쓰기 응답 직후 연결이 끊긴 시험에서 재시도 전에 readback을 실행하며 task를 두 개 만들지 않는다.
8. ClickUp 상태명이 계약과 하나라도 다르면 쓰기는 실패하고 읽기 전용 보고만 남는다.
9. 일반 `Engineer`만 있는 포지션은 `UNCLASSIFIED`이고 `etc`나 backend로 자동 확정되지 않는다.
10. neutral export의 `source_row_count = accepted_row_count + rejected_row_count`이며 중복 원자료도 행으로 보존된다.
11. 자료 조회 실패 주차는 0이 아니라 `NOT_RUN`과 이유가 화면에 나온다.
12. 주간 카드의 모든 숫자는 API 응답의 provenance와 원자료 조회 링크를 가진다.
13. 운영 쓰기 승인값이 없으면 Gmail/ClickUp 읽기는 가능하지만 ClickUp POST/PUT은 구조적으로 호출되지 않는다.
14. 기존 관리자 화면 캡처와 새 화면 캡처 비교가 없으면 시각 완료 판정은 `NOT_RUN`이다.
15. `bash verify.sh`와 해당 Phase의 새 시험·형 검사·정적 검사가 모두 실제 처리 건수를 출력하고 0건 검사는 실패한다.

### 13. 가짜 합격을 깨는 반대 시험

- 4세대 저장소 폴더를 잠시 보이지 않게 해 새 앱을 실행한다. 깨지면 clean-room 실패다.
- `gmail_quote` 제거 한 줄을 고장 내 이전 대화가 시험에 나타나고 RED가 되는지 확인한 뒤 원복한다.
- 데이터베이스 고유 제약을 고장 내 동시 처리 시험이 중복을 잡는지 확인한 뒤 원복한다.
- ClickUp write 응답만 성공하고 readback이 다른 상태를 돌려줄 때 전체 판정이 FAIL인지 확인한다.
- Gmail 조회 실패를 빈 배열로 바꾸는 변이를 넣어 0건이 아니라 NOT_RUN 시험이 실패하는지 확인한 뒤 원복한다.
- 월요일 시작 경계를 넣어 8월 9일 일요일 사건이 빠지는 것을 시험이 잡는지 확인한 뒤 원복한다.
- AI 후보 두 행의 후보 키를 같게 만들어도 원시 행 수는 2, 고유 후보 수만 1인지 확인한다.
- ClickUp 상태 하나를 임의로 바꿔 쓰기가 차단되는지 확인한다.

### 14. 검증과 보고

각 Phase에서 다음 순서를 지킨다.

1. 저장소 정본 명령과 Phase 전용 시험 실행.
2. 실제 처리 파일·시험·원자료 행 수 확인.
3. 비밀·개인정보 노출 검사.
4. 외부 경계 변경 시 읽기 전용 실제 연결 1건. 쓰기는 Phase D 승인 후 1건만.
5. Claude CLI를 API 키 환경변수 없이 실행해 1차 적대검증.
6. Codex가 Claude 지적을 각 file:line과 실행으로 다시 공격해 CONFIRM/REFUTE/PARTIAL로 판정.
7. 목표 문서에 명령 전문, 판정 전문, 재검증 결과를 append.
8. PR까지만 만들고 머지·배포·운영 전환은 하지 않는다.

완료 보고는 결론 → 판단 근거 → 증거 원문 순서로 쓴다. `PASS/FAIL/NOT_RUN`을 숨기지 않는다. 명령이나 수치 표 아래에는 그 결과가 좋은지 나쁜지 해석을 붙인다.

## 현재 상태와 코드 근거

- `README.md:7` — 6세대 저장소가 아직 소스 코드 없는 부트스트랩 단계라고 선언한다. 따라서 이 작업은 리팩터링이 아니라 신설이다.
- `humansearch/src/humansearch/__init__.py:1-6` — 현재 6세대 제품 코드는 HumanSearch 경계 이름만 있고 관리자 route가 없다.
- `/Users/kangsangmo/Desktop/Valuehire_v4/app/(admin)/admin/dashboard/page.tsx:2-14` — 기존 관리자 대시보드는 정적 `weekly-brief.html`을 iframe으로 전면 표시한다.
- `/Users/kangsangmo/Desktop/Valuehire_v4/tools/gmail-recommendation-clickup-sync/run.mjs:113-169` — 기존 검색은 제목에 단어가 포함된 발신 메일을 찾고 개별 메시지를 읽지만 수신자 헤더를 보존·검사하지 않는다.
- `/Users/kangsangmo/Desktop/Valuehire_v4/tools/gmail-recommendation-clickup-sync/lib/gmail-body.mjs:16-40` — 기존 본문 추출은 첫 `text/plain` 전체를 반환하며 이전 대화·자동 서명을 제거하지 않는다.
- `/Users/kangsangmo/Desktop/Valuehire_v4/tools/gmail-recommendation-clickup-sync/lib/parse-subject.mjs:45-70` — 기존 파서는 답장·전달 접두어를 벗긴 뒤 태그를 허용한다. 이번 “태그로 시작” 계약과 다르다.
- `/Users/kangsangmo/Desktop/Valuehire_v4/supabase/migrations/20260725090000_weekly_brief_snapshot.sql:13-72` — 기존 주간 집계는 월요일 시작 7일 창을 사용한다. 새 일요일~토요일 계약과 다르다.
- `/Users/kangsangmo/Desktop/Valuehire_v4/supabase/migrations/20260516120002_sourcing_results.sql:5-33` — 4세대에는 검색 실행과 결과 행 스키마가 있어 원자료 반출 대상이 존재한다.
- `/Users/kangsangmo/Desktop/Valuehire_v5/tools/multi_position_sourcing/humansearch_supabase_sync.py:31-83` — 5세대 Human Search는 이력서 원문과 후보 결과를 서로 다른 행으로 만드는 매핑이 있다.
- `/Users/kangsangmo/Desktop/Valuehire_v5/scripts/humansearch_supabase_backfill.py:120-152` — 5세대 backfill은 실행과 후보 행을 적재하므로 반출 시 실행-결과 연결을 보존해야 한다.
- `docs/sot/coding-principles.md:18-37` — 조용한 실패 금지, 외부 효과 재확인, 수치는 코드 계산, 데이터 git 금지, 운영값·비밀 분리를 정본으로 요구한다.
- `docs/sot/verification-commands.md:8-16` — 이 저장소는 make/npm 저장소가 아니며 현재 로컬 검증·worktree·배송 명령을 따로 정의한다.

→ 위 줄들은 “왜 전면 신설인가”, “기존 메일·주간 로직의 무엇을 버려야 하나”, “과거 후보 원자료가 어디에 있나”를 직접 보여준다. 4·5세대 파일은 읽기 전용 근거일 뿐 새 실행 경로가 아니다.

## 읽기 전용 실제 확인 증거

### Gmail 표본 확인

실행 범위: 연결된 `sangmokang@valueconnect.kr` 계정의 보낸편지함에서 제목이 `[추천]` 또는 `[포지션]`으로 시작하고 외부 수신자가 있는 메시지를 검색한 뒤, thread API가 아니라 6개 message id를 batch message API로 읽었다. 원문 제목·주소·본문·message id는 개인정보 때문에 이 문서와 git에 넣지 않았다. 원본 위치는 연결된 Gmail 계정이며, 읽은 6개 직렬화 응답의 SHA-256 내용 지문은 `73c27f77cf6785c9a83dbd7a4336ef7b2c95f5781ce3c0de4405a923e06b43b0`이다.

```json
{
  "samples": 6,
  "recommendation": 5,
  "position": 1,
  "exact_subject_start": 6,
  "external_recipient_counts": [1, 1, 2, 1, 1, 1],
  "text_plain_parts": 6,
  "text_html_parts": 6,
  "html_gmail_quote_present": 4,
  "gmail_signature_structure_present": 2,
  "messages_with_attachments": 4,
  "subject_business_parse_success": 6
}
```

→ 한 메시지 단위로 읽어도 이전 대화가 그 메시지의 HTML 안에 들어갈 수 있음을 확인했다. 글자 본문에서 인용 표시를 찾은 것은 2건뿐이었지만 꾸민 본문 구조에서는 4건이 잡혔다. 제목 6건은 익명 구조 검사에서 모두 고객사·포지션·후보자 필요값으로 분리됐다. “thread를 안 읽었으니 본문 전체가 안전하다”는 가정과 “plain만 보면 된다”는 가정이 모두 틀렸다. 내용 지문 계산 첫 시도는 이 실행 환경에 `TextEncoder`가 없어 실패했고, 개인정보를 파일로 내리지 않는 순수 JavaScript 계산으로 다시 실행했다.

### ClickUp 목록 확인

실행 명령은 운영 토큰을 출력하지 않는 읽기 전용 GET만 수행했다.

```bash
node --env-file=/Users/kangsangmo/Desktop/Valuehire_v4/.env.local - <<'NODE'
const token = process.env.CLICKUP_API_TOKEN || process.env.CLICKUP_TOKEN;
if (!token) {
  console.log(JSON.stringify({status:"NOT_RUN", reason:"token_missing"}));
  process.exit(0);
}
const ids = ["901814621142", "901814621569"];
for (const id of ids) {
  const res = await fetch(`https://api.clickup.com/api/v2/list/${id}`, {headers:{Authorization:token}});
  if (!res.ok) {
    console.log(JSON.stringify({list_id:id,status:"FAIL",http:res.status}));
    continue;
  }
  const data = await res.json();
  console.log(JSON.stringify({
    list_id:id,
    status:"PASS",
    list_name:data.name,
    statuses:(data.statuses||[]).map(s=>({status:s.status,type:s.type,orderindex:s.orderindex})),
    custom_fields:(data.fields||[]).map(f=>({name:f.name,type:f.type,required:Boolean(f.required)}))
  }));
}
NODE
```

→ stdin으로 ClickUp `/api/v2/list/{id}`를 읽고 목록 이름·상태명만 출력했다. POST·PUT·DELETE는 호출하지 않았다.

```json
{"list_id":"901814621142","status":"PASS","list_name":"FY26CandidstesStatus","statuses":[{"status":"ai sourcing","type":"open","orderindex":0},{"status":"제안(추천대기)","type":"unstarted","orderindex":1},{"status":"추천","type":"custom","orderindex":2},{"status":"고객사추천","type":"custom","orderindex":3},{"status":"코딩테스트사전과제","type":"custom","orderindex":4},{"status":"서류탈락","type":"custom","orderindex":5},{"status":"코딩테스트 사전과제 탈락","type":"custom","orderindex":6},{"status":"면접후탈락","type":"custom","orderindex":7},{"status":"셀프드롭(서류, 면접)","type":"custom","orderindex":8},{"status":"1차 면접/coffee chat","type":"custom","orderindex":9},{"status":"2차면접","type":"custom","orderindex":10},{"status":"3차면접","type":"custom","orderindex":11},{"status":"포지션중단","type":"custom","orderindex":12},{"status":"최종합격","type":"custom","orderindex":13},{"status":"셀프드롭(최종합격후)","type":"custom","orderindex":14},{"status":"입사","type":"custom","orderindex":15},{"status":"입사후퇴사","type":"custom","orderindex":16},{"status":"회고후보자","type":"done","orderindex":17},{"status":"추천하려다fail","type":"closed","orderindex":18}],"custom_fields":[]}
{"list_id":"901814621569","status":"PASS","list_name":"FY26ClientsPosition","statuses":[{"status":"scraped","type":"open","orderindex":0},{"status":"backend/fullstack/cto","type":"custom","orderindex":1},{"status":"ai/ml/data","type":"custom","orderindex":2},{"status":"po/pm/기획","type":"custom","orderindex":3},{"status":"frontend","type":"custom","orderindex":4},{"status":"designer","type":"custom","orderindex":5},{"status":"sales/bd","type":"custom","orderindex":6},{"status":"marketing","type":"custom","orderindex":7},{"status":"devops/sre/security/qa","type":"custom","orderindex":8},{"status":"hr/finance/strategy/etc","type":"custom","orderindex":9},{"status":"c-level","type":"custom","orderindex":10},{"status":"app","type":"custom","orderindex":11},{"status":"etc","type":"custom","orderindex":12},{"status":"closedpositions","type":"done","orderindex":13},{"status":"complete","type":"closed","orderindex":14}],"custom_fields":[]}
{"task_id":"86exbvqg6","status":"PASS","list_id":"901814621569","current_status":"marketing","description_present":true,"description_chars":4525,"custom_fields":[]}
```

→ 추천 목표 상태와 포지션 직무 상태가 현재 실제로 존재한다. 사용자가 준 포지션 예시 task도 같은 목록에 있고 본문이 있다. task 이름과 본문은 출력하지 않았다.

### 운영 화면 접근 확인

```text
{"final_url":"https://admin.valuehire.cc/login?next=%2Fadmin%2Fdashboard","http_code":200,"redirects":1}
```

→ 인증 없는 읽기에서는 로그인 화면까지만 확인됐다. 현재 대시보드 모양의 실제 캡처는 아직 `NOT_RUN`이며 시각 일치 완료를 주장할 수 없다.

### 시작 자격 확인

```bash
bash scripts/session-status.sh
```

→ 저장소 정본이 정한 시작 자격 검사를 실행했다. 아래 두 줄 뒤 90초 넘게 끝나지 않아 직접 중단했다.

```text
HEAD: 682f00e (synced)
ORIGIN: 682f00e
```

→ `bash scripts/session-status.sh`가 정본상 필요한 세 번째 `RED: N/M` 줄을 내지 않고 90초 넘게 멈춰 중단했다. 시작 자격은 PASS가 아니라 `NOT_RUN`이다. 이 문서 작성은 가능하지만 제품 구현 전 원인을 풀어야 한다.

## 정본 준수 체크

- [x] `AGENTS.md` — 사용자 제공 전문을 현재 작업의 최상위 계약으로 읽었다.
- [x] `docs/sot/INDEX.md` — 정본 목록을 읽었다.
- [x] `docs/sot/coding-principles.md` — P1~P22와 검증 체제를 읽었다.
- [x] `docs/sot/verification-commands.md` — 실제 gate 명령을 읽었다.
- [x] `docs/sot/git-workflow.md` — main 보호와 worktree 규칙을 읽었다.
- [x] `docs/sot/hook-contracts.md` — 훅이 보장하는 것과 보장하지 않는 것을 읽었다.
- [x] 4·5세대 코드는 근거로만 읽고 현재 저장소에 복사하지 않았다.
- [x] Gmail과 ClickUp은 읽기 전용으로만 확인했다.
- [ ] 인증된 운영 화면 캡처 — 로그인 세션을 이 환경에서 사용할 수 없어 `NOT_RUN`.
- [ ] 구글 캘린더 반복 일정 고유값 — 연결 도구와 값이 없어 `NOT_RUN`.
- [ ] 제품 시험·빌드·라이브 쓰기 — 구현 전이므로 `NOT_RUN`.

## 이번 문서의 비범위

- 관리자 제품 코드 생성과 의존성 설치.
- Gmail 원문·주소·후보자 정보의 저장소 보관.
- ClickUp task 생성·수정·이동.
- 운영 주소 전환, 배포, 기존 서비스 삭제.
- 과거 데이터 실제 반출·적재.
- 구글 캘린더 일정 생성·변경.
- git commit, push, PR, merge.

## 적대 검증 로그

### 1차 — Claude CLI: NOT_RUN

검증자 신분은 로컬 Claude CLI다. 첫 실행은 저장소 폴더에서 시작 훅과 함께 멈춰 판정 본문 0자였고 직접 중단했다.

```bash
env -u ANTHROPIC_API_KEY claude -p < docs/engineering/admin-weekly-dashboard-v6-review-prompt-2026-08-16.md
```

→ API 키 환경변수를 제거하고 원 검토 프롬프트를 전달했다. 수분 동안 판정이 한 글자도 나오지 않아 중단했으므로 통과가 아니다.

```text
NO_OUTPUT — interrupted after repeated 30-second polls; verdict body length=0
```

→ 빈 출력과 중단 뒤 종료 성적 0은 판정 성공이 아니다. 같은 저장소의 시작 자격 검사도 세 번째 줄 전에 멈춘 사실과 함께, 저장소 훅 개입 가능성을 의심했다.

저장소 훅을 피하려고 작업 폴더를 `/private/tmp`로 바꾸고 절대경로의 같은 검토 요청을 새 세션으로 실행했다.

```bash
env -u ANTHROPIC_API_KEY claude -p < /Users/kangsangmo/Desktop/Valuehire_v6/docs/engineering/admin-weekly-dashboard-v6-review-prompt-2026-08-16.md
```

→ 목표 문서와 근거 파일을 읽는 원 검토를 중립 폴더에서 다시 시켰다. 이번에는 Claude 서비스가 안전장치 오탐으로 요청을 거부해 판정이 생성되지 않았다.

```text
API Error: Fable 5's safeguards flagged this message (https://www.anthropic.com/legal/aup). This sometimes happens with safe, normal conversations. Claude Code can't respond to this message with Fable 5.

Try rephrasing the request in a new session or change your model.

Learn more: https://support.claude.com/en/articles/15363606

Request ID: req_011Ce5YWMm1D61sEiT8kGNza
SessionEnd hook [node "${CLAUDE_PLUGIN_ROOT}/scripts/session-end.mjs"] failed: Hook cancelled
SessionEnd hook [node "${CLAUDE_PLUGIN_ROOT}/scripts/session-lifecycle-hook.mjs" SessionEnd] failed: Hook cancelled
```

→ 프로그램 종료 성적은 1로 불합격이었다. 제품 결함 판정이 아니라 검증 요청 자체가 서비스에서 거절된 것이다.

계정·목록 고유값과 공격 표현을 빼고 목표 문서를 직접 읽는 짧은 품질검토 요청으로 1회 재시도했다.

```bash
env -u ANTHROPIC_API_KEY claude -p < /Users/kangsangmo/Desktop/Valuehire_v6/docs/engineering/admin-weekly-dashboard-v6-review-prompt-retry-2026-08-16.md
```

→ §8-7 출력 형식은 그대로 둔 채 요청 표현만 줄였다. 같은 안전장치 오탐으로 다시 거절돼 1차 검증은 `NOT_RUN`으로 확정했다.

```text
API Error: Fable 5's safeguards flagged this message (https://www.anthropic.com/legal/aup). This sometimes happens with safe, normal conversations. Claude Code can't respond to this message with Fable 5.

Try rephrasing the request in a new session or change your model.

Learn more: https://support.claude.com/en/articles/15363606

Request ID: req_011Ce5YowgASJMBRsktj4rqH
SessionEnd hook [node "${CLAUDE_PLUGIN_ROOT}/scripts/session-end.mjs"] failed: Hook cancelled
SessionEnd hook [node "${CLAUDE_PLUGIN_ROOT}/scripts/session-lifecycle-hook.mjs" SessionEnd] failed: Hook cancelled
```

→ 프로그램 종료 성적은 다시 1이었다. Claude의 PASS/FAIL 본문, 결함 수, file:line은 존재하지 않으므로 만들어 내거나 Codex 의견으로 대체하지 않는다.

### 2차 — Codex 재공격

Claude 주장이 생성되지 않아 재현할 외부 지적은 0건이다. 대신 같은 12개 검토 질문으로 목표 문서를 양방향으로 다시 공격했고 다음 여섯 결함을 직접 확인·수정했다.

1. `CONFIRM→FIXED` — 제목 앞 공백을 지운 뒤 태그를 허용하면 “태그로 시작” 계약보다 넓어진다. 현재 `admin-weekly-dashboard-v6-replacement-goal-2026-08-16.md:226-253`은 원 제목의 첫 글자를 검사하고 Re/Fwd·앞 공백을 거부한다. 틀린 메일이 신규 실적으로 들어가는 경로를 닫았다.
2. `CONFIRM→FIXED` — 회의가 같은 주 화요일로 이동하면 월요일 단언이 작업을 멈췄다. 현재 같은 문서 `:177-215`는 실제 회의 날짜가 속한 주의 월요일을 기준점으로 삼고 월·화 회의가 같은 창을 내는 인수 기준 `:548`을 둔다.
3. `CONFIRM→FIXED` — 메일 장부에 고객사·포지션·후보 구조값이 없어 정확 중복키를 재계산할 수 없었다. 현재 같은 문서 `:390-410`은 암호화 구조값과 비밀키 지문, 메시지·목록 고유 제약을 분리한다.
4. `CONFIRM→FIXED` — 보관 정책이 미확정이라고만 쓰고 실제 수집 중지점과 연결하지 않았다. 현재 같은 문서 `:66`, `:506-515`는 기간·권한·삭제 명령이 없으면 실제 계정 수집으로 넘어가지 못하게 한다.
5. `CONFIRM→FIXED` — 결론은 미확정 3개라고 했지만 본문에는 화면 원본과 보관 정책까지 5개가 있었다. 현재 같은 문서 `:17`, `:61-67`은 다섯 가지를 같은 목록으로 맞췄다.
6. `CONFIRM→FIXED` — “고유 후보”의 범위와 주간 귀속 시점이 없어서 같은 숫자를 여러 방식으로 만들 수 있었다. 현재 같은 문서 `:463-500`은 메일은 발신 시각, 후보는 발견 시각으로 귀속하고 출처를 넘는 전사 고유 후보 수는 신원 연결 계약 전까지 `NOT_RUN`으로 둔다.

→ 여섯 건은 모두 프롬프트 내부 모순 또는 가짜 집계 경로였고 수정했다. 외부 검증자가 확인한 결함은 아니므로 Claude 판정으로 표시하지 않았다.

### 검증 결론

`Codex 판정: Phase A 전달 가능 / 제품 구현 완료 NOT_RUN / Claude 1차 NOT_RUN`

- 목표 문서는 4·5세대 실행 의존성 0, 개별 메시지 현재 본문, 주간 일요일~토요일, ClickUp 재확인, 원자료 우선 보존을 기계 조건으로 갖췄다.
- 개발 기반, 캘린더 일정 고유값, 인증 화면 캡처, 보관 정책, 모호 직무 처리기한은 `admin-weekly-dashboard-v6-replacement-goal-2026-08-16.md:17`, `:61-67`에 공개된 중지 조건이다.
- 시작 자격 검사는 `:677-690`처럼 `NOT_RUN`이고 제품 코드·시험·화면은 만들지 않았으므로 구현 완료를 주장하지 않는다.
- Claude 1차 판정이 없으므로 strict 전체 검증은 미완료다. 서비스 오탐이 풀린 뒤 같은 두 검토 프롬프트 중 하나를 다시 실행해야 한다.

### 문서 검증 실행

```bash
bash /Users/kangsangmo/.claude/skills/strict/brief-lint.sh docs/engineering/admin-weekly-dashboard-v6-replacement-goal-2026-08-16.md
```

→ 사장님 보고 형식에서 결론·결정 카드·출력 해석 누락이 있는지 보조 검사했다. 이 도구는 서버가 강제하지 않으므로 품질 합격증으로 쓰지 않는다.

```text
=== docs/engineering/admin-weekly-dashboard-v6-replacement-goal-2026-08-16.md ===
  코드블록 25개 · 표 0개 (면제 0개) / 해석 누락 0개
  1층(결론): 줄 7 / 본문 630자
  1층 기술 표기: 없음 (※ 한글 전문용어는 못 잡는다 — 사람이 본다)
  결정 카드 5건 (※ 내용이 판단에 쓸 만한지는 못 잰다 — 사람이 본다)
  증거 보관 경로: 임시 외 실재 파일 8건 (※ 그 파일이 이 주장의 증거인지는 못 잰다)

브리핑 계약 기계 검사: 위반 0건 (문서 1개)

이 검사가 못 보는 것 (사람이 봐야 하는 것):
  · 설명이 실제로 말이 되는지 — 출력과 무관한 문장도 통과한다
  · 결정 카드 내용이 판단에 쓸 만한지 — 한 글자여도 통과한다
  · 증거 파일이 그 주장과 관련 있는지 — 존재하기만 하면 통과한다
  · 결론이 쉬운 말인지 — 한글 전문용어는 잡지 못한다
  ※ 이 검사는 홈 폴더에만 있어 서버 자동 검사에 없다 — 회사 차원의 합격 근거가 아니다(P15③).
```

→ 명백한 형식 누락은 0건이다. 사람이 판단해야 하는 내용 정확성은 위 Codex 재공격과 실제 Gmail·ClickUp 읽기로 따로 확인했다.

```bash
bash verify.sh
bash scripts/check-docs-sot.sh
```

→ 저장소가 정한 비밀 검사와 정본 문서 연결 검사를 실행했다. 두 검사 모두 통과했다.

```text
PASS: no secret-pattern match in any tracked file, .env not tracked
PASS: docs/sot/INDEX.md 존재, 1050바이트 (<=20000)
PASS: docs/sot/coding-principles.md 존재, 15405바이트 (<=20000)
PASS: docs/sot/hook-contracts.md 존재, 4455바이트 (<=20000)
PASS: docs/sot/git-workflow.md 존재, 2225바이트 (<=20000)
PASS: docs/sot/verification-commands.md 존재, 6736바이트 (<=20000)
PASS: hooks/pre-commit 가 docs/sot/hook-contracts.md 를 계약으로 참조
PASS: hooks/pre-push 가 docs/sot/hook-contracts.md 를 계약으로 참조
PASS: scripts/install-hooks.sh 가 docs/sot/hook-contracts.md 를 계약으로 참조
PASS: scripts/session-status.sh 가 docs/sot/hook-contracts.md 를 계약으로 참조
PASS: scripts/acceptance-0-7.sh 가 docs/sot/hook-contracts.md 를 계약으로 참조
OK: docs/sot 재구성 AC 전부 충족
```

→ `verify.sh`는 추적 파일만 보므로 아직 미추적 상태인 이번 새 문서 3개는 아래에서 같은 패턴으로 별도 검사했다.

```bash
bash scripts/scan-data-exposure.sh all
```

→ 현재 추적 파일 검사는 통과했지만 과거 기록 전량 단계가 10분 동안 새 출력을 내지 않아 중단했다. 끝나지 않은 검사는 합격이 아니므로 history 결과는 `NOT_RUN`이다.

```text
PASS: 추적 파일 83개 검사, 위반 0건
NO_OUTPUT — history scan interrupted after 10 minutes; exit=130
```

→ 현재 파일 83개는 통과했지만 과거 git 기록 전체는 확인하지 못했다. 이번 변경은 새 문서뿐이고 과거 기록을 바꾸지 않지만, 전체 검증 완료라고 부르지는 않는다.

새 문서 직접 검사의 첫 명령은 임시 패턴 파일을 지우는 `rm -f`가 도구 정책에 막혀 실행 전에 거부됐다. 같은 내용을 임시 파일 없는 입력 연결로 다시 실행했다.

```bash
bash scripts/scan-data-exposure.sh pii
grep -lEif <(cat .secret-patterns.default .secret-patterns | tr -d '\r' | grep -vE '^[[:space:]]*(#|$)') -- docs/engineering/admin-weekly-dashboard-v6-*.md
rg -n '\b[0-9a-f]{16}\b' docs/engineering/admin-weekly-dashboard-v6-*.md
```

→ 현재 추적 파일의 개인정보 적재 형태와 새 문서 3개의 비밀값·Gmail 메시지 고유값을 검사했다. 두 검색은 “발견되면 실패”로 실행했으며 발견 0건이었다.

```text
PASS: csv/tsv/sql 0개 검사(추적 83개 중), 개인정보 적재 0건
PASS: new documents 3개 secret-pattern match 0건
PASS: Gmail message id 0건
```

→ 새 문서에는 실제 메일 본문·제목·주소별 수신자·message id·접속 키가 들어가지 않았다. 계정 이름과 목록 고유값은 사용자가 제공했거나 읽기 전용 계약값으로 승인된 범위다.
