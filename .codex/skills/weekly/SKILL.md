---
name: weekly
description: ValueHire weekly operations workflow for ClickUp, Gmail, AI Search, customer news, Notion, admin reporting, and the SQL-backed Weekly Brief. Use when the user invokes $weekly or asks to prepare, audit, publish, or improve a weekly report, weekly meeting page, 주간 KPI, 후보자·고객사 follow-up, or a Notion weekly document.
---

# Weekly

차주 월요일 회의 자료를 만드는 ValueHire 주간 운영 정식 절차다. 기본 보고 언어는 한국어다. 숫자는 추정하지 않고, 원문 근거와 집계 의미를 보존한다.

## 정본과 기간

- 저장소의 `.codex/skills/weekly/SKILL.md`를 정본으로 취급하고 `.claude/skills/weekly/SKILL.md`는 같은 바이트의 Claude용 복사본으로 유지한다. `~/.codex/skills/weekly`와 `~/.claude/skills/weekly`는 로컬 설치본일 뿐 정본이 아니다.
- `docs/sot/29-weekly-machine-spec.md`, `docs/sot/14-weekly-screen-columns.md`, 대상 회의록의 `WEEKLY_KPI` 계약을 먼저 읽는다.
- 자동화·cron을 다룰 때만 `docs/sot/13-scheduled-agents-registry.md`를 추가로 읽는다.
- 기본 집계 구간은 KST 반열린 구간 `[지난 월요일 00:00, 이번 월요일 00:00)`이다. 문서에는 사람이 읽는 종료일을 일요일로 표시한다.
- 필수 파일이나 정식 러너가 없으면 성공한 척하지 않는다. 현재 ClickUp API, Gmail/Supabase 원문, 저장 DB를 읽기 전용 대체 근거로 사용하고 누락된 정본과 영향 범위를 적는다.

## 차주 선생성·매일 누적 갱신

- 작성 요청을 받은 당일에 **차주 월요일 문서를 즉시 생성**한다. 월요일 당일에는 그날 회의 문서를 대상으로 삼고, 화~일요일에는 다가오는 월요일을 대상으로 삼는다.
- `Date`는 회의일, `Duration`은 회의일의 **직전 월요일부터 일요일**까지다. 예: 2026-11-02 회의 문서는 `2026-10-26~2026-11-01`이다.
- 회의 전까지는 페이지 상단에 `진행 중 스냅샷 · YYYY-MM-DD HH:mm KST 기준`을 표시하고 **매일 누적 갱신**한다. 그날까지 확인된 실측만 넣고, 아직 전수 집계하지 못한 값은 0 대신 `미집계(사유)`로 둔다.
- 갱신할 때 같은 `Date`와 `Name(FY26Wxx)`의 페이지를 먼저 찾아 그 페이지 하나만 수정한다. 매일 새 페이지를 만들거나 수기 섹션을 통째로 덮어쓰지 않는다.
- 월요일 갱신에서만 직전 월~일 구간을 최종 확정한다. 진행 중 스냅샷을 주간 최종 실적으로 표현하지 않는다.
- 정기 실행은 `com.valuehire.weekly-daily`가 매일 20:30 KST에 이 스킬을 다시 호출한다. 자동 실행은 Gmail·ClickUp·AI Search·뉴스를 읽고 회의록 Markdown과 Notion만 갱신하며, 외부 메일·메시지 발송이나 후보자/포지션 상태 변경은 하지 않는다.
- 다른 PC에서는 Git pull 후 `bash scripts/install-weekly-daily-launchd.sh`로 등록하고 `launchctl print gui/$(id -u)/com.valuehire.weekly-daily`로 다음 실행 시각과 설치 상태를 확인한다. 운영 키가 저장소 `.env.local`에 없으면 `WEEKLY_DAILY_ENV_FILE=<절대경로>`를 설치기에 전달한다.

## 조사 순서

1. Gmail 실제 외부 송부를 제목·수신자·최초 발송 기준으로 중복 제거해 고객사 실제 추천을 집계한다. 내부 전달, `Re:`/`FW:`, 동일 제목 재전송은 신규 추천에서 제외한다.
2. ClickUp 후보자·포지션·AI Search 정본 리스트를 확인한다. 신규 카드 수와 고유 후보 수, 신규 소싱과 과거 추천 역매칭을 분리한다.
3. AI Search 상세 결과 메일·로그에서 검색 모집단, 프로필 정독, 접촉 발송, 내부 추천 판정을 추출한다.
4. 고객사 피드백, 후보자 회신, 확정 일정, 장기 미회신을 근거 날짜와 함께 정리한다. 토트·두나무처럼 사용자가 지목한 고객사는 별도 최우선 Follow-up으로 올린다.
5. 고객사 뉴스는 기사 발행일과 원문을 확인한다. 수집 시각을 발행일로 대체한 레코드는 주간 신규 뉴스로 세지 않는다.
6. 여행·행사 등 오너 메모가 추가되면 공식 시간표·운영 공지를 확인하고, 확정 정보와 좌석·영업시간 등 재확인 항목을 나눈다.

## Notion 샘플과 admin 교차검증

- 공용 상세 검증 지침은 [`docs/engineering/weekly-portable-validation-prompt-2026-11-09-v2.2.md`](../../../docs/engineering/weekly-portable-validation-prompt-2026-11-09-v2.2.md)다. Codex와 Claude는 같은 파일을 읽고 절차를 적용한다.
- 회의록 형식·구조·편집 경계를 점검할 때 W45 원형 샘플(https://app.notion.com/p/valueconnect/FY26W45-406345c17dca81a8951cc7f778b91c48)과 W46 live 사례(https://app.notion.com/p/valueconnect/FY26W46-40d345c17dca8194995ccd15dd9c1210)를 모두 연다. W45는 원형, W46은 live 형식 사례로 역할을 구분한다. 둘의 수치·정의·주차별 내용을 현재 기본값으로 복사하지 않는다.
- Weekly 실행에서 `admin.valuehire.cc`의 인증된 실제 화면도 확인하고 같은 기간·cutoff·지표정의로 Notion 본문·표·속성과 대사한다. 합계가 같다는 사실만으로 일치 판정하지 말고 공통 ID 기준 행/집합 차이를 확인한다. admin은 독립적인 화면/집계 근거이며 Weekly Brief/SQL 정본을 대체하지 않는다.
- admin 또는 Notion 인증·조회·페이지네이션이 실패하면 시도한 범위와 영향 지표를 완료 증거에 기록한다. 그 소스를 검증한 것으로 표시하지 말고, 소스가 필요한 KPI는 보류/미검증으로 남긴다.
- W46 조사 요약에 나온 `8/20`과 `40%/35%` 충돌은 과거 오류 사례다. 이를 지금의 정답·다음 주 값으로 사용하지 않는다. 수락/거절 검색의 첫 페이지도 전수로 간주하지 않는다.
- 기존 회의록 검토는 읽기 전용이 기본이다. 실제 주간 보고 갱신·게시 요청은 이 스킬의 정상 경로 및 저장·재조회 게이트에 따르며, 단순히 샘플 URL을 제공했다는 이유로 페이지를 수정하지 않는다.

## 지표 의미를 섞지 말 것

다음 지표를 항상 별도 행으로 보고한다.

- `프로필 정독`: 상세 보고서에서 실제 검토한 프로필 수
- `접촉 발송`: 채널별 발송 이벤트 수. 채널 간 중복을 제거하지 못했다면 `최소 N건`, `고유 인원 아님`이라고 명시한다.
- `내부 추천 판정`: AI Search가 내부 추천 등급으로 분류한 후보 수
- `고객사 실제 추천`: Gmail 외부 발송을 중복 제거한 실제 고객사 송부 수
- `ClickUp 역매칭`: 원시 카드 수와 고유 후보 수를 함께 적고 신규 소싱에서 제외한다.

공통 후보 ID로 연결되지 않은 `내부 추천 판정 → 고객사 실제 추천`은 전환율로 계산하지 않는다. 사람 수와 발송 이벤트 수를 합산하지 않는다.

## Notion 데이터베이스 속성

주간 페이지를 만들거나 갱신할 때 아래 속성을 먼저 채운다.

- `Name`: `FY26Wxx`
- `Duration`: 조사한 월요일부터 일요일까지의 날짜 범위. **비워두지 않는다.**
- `Date`: 회의일
- `Week`: 주차 숫자
- `달성`: 고객사 실제 추천 수
- `추천목표`: 주간 목표
- `지난주추천숫자`: 동일 집계 기준의 전주 수치
- `목표대비달성율`: 데이터베이스 수식 또는 검증된 계산값
- `신규고객사`, `신규포지션`: 집계 기준을 짧게 병기
- `Strong후보자`, `Urgent Project`: 근거가 있을 때만 채운다.

`Duration`, `Date`, `Week`가 없으면 검색·정렬이 어렵기 때문에 게시 완료로 보지 않는다.

## Notion 본문 시각 계약

Notion에서 보이는 문서는 Markdown 저장본을 그대로 붙여 넣지 말고 **네이티브 블록**으로 구성한다.

1. 상단 콜아웃: 집계 기간, 한 줄 결론, 최우선 의사결정 1~3개
2. KPI 스냅샷: 추천 달성률, AI Search, 포지션, 고객사 숫자를 짧은 표 또는 2열 구조로 배치
3. 이번 주 액션: 체크박스 또는 짧은 표로 담당 액션·기한을 먼저 노출
4. 고객사 피드백과 후보자 Follow-up: 고객사별 표, 긴 근거는 토글 안에 배치
5. 고객사 뉴스와 확정 일정
6. 여행·행사 등 운영 메모: 추천안과 대안을 분리하고 시간표를 표로 표시
7. 데이터 품질·집계 주의사항: 마지막 토글 또는 콜아웃

금지:

- `##`, `|---|`, 링크 문법이 화면에 그대로 보이는 원시 Markdown
- 전체 문서를 단일 텍스트 블록에 붙여 문단·표·불릿이 이어 붙는 상태
- 빈 `Duration`이나 제목 없는 페이지
- 상세 근거를 상단 요약보다 먼저 길게 노출

참고 시각 위계는 `https://valuehire-weekly-operations.sangmokang.chatgpt.site`의 요약 → KPI → 액션 → 상세 순서를 따른다. 색상·카드 UI를 억지로 복제하지 말고 Notion의 콜아웃, 제목, 표, 불릿, 체크박스, 토글을 사용한다.

## 게시 경로와 실패 대체

정식 경로:

```bash
npm run weekly-brief:refresh
node tools/harness/weekly-recap.mjs --publish-weekly --md=<weekly-markdown-path>
```

- Weekly Brief는 `provenance=sql_rpc:weekly_brief_snapshot`을 요구한다. 운영 숫자를 `public/dashboard/weekly-brief.html`에 수기로 복사하지 않는다.
- Notion API integration이 데이터베이스에 접근할 수 없으면 로그인된 Notion 브라우저를 사용한다. 기존 `FY26Wxx` 페이지를 먼저 찾아 중복 생성을 막고, 속성과 본문을 네이티브 블록으로 편집한다.
- 브라우저 대체 경로에서도 원시 Markdown 단일 붙여넣기는 금지한다. 네이티브 블록 생성이 실패하면 게시 실패로 처리하고 다시 구성한다.

## 재조회 검증

게시 후 같은 Notion 페이지를 다시 읽고 다음을 확인한다.

- 제목이 정확한 `FY26Wxx`이고 중복 페이지가 없다.
- `Duration`, `Date`, `Week`, `달성`, `추천목표`가 화면에 표시된다.
- 상단 요약, AI Search, 고객사 실제 추천, 고객사 Follow-up, 여행·행사 메모 등 요청된 핵심 섹션이 존재한다.
- 본문이 단일 텍스트 블록이 아니며 제목·표·불릿·토글 등 여러 네이티브 블록으로 나뉜다.
- 샘플로 최소 10개 상세 항목을 원문과 대조하고 숫자·이름·일정이 일치한다.
- 진행 중 문서는 마지막 갱신 시각이 당일이고, 같은 주차 페이지가 정확히 1개인지 확인한다.

검증에 실패하면 URL만 보고 완료라고 하지 말고 같은 페이지를 수정한 뒤 재조회한다.

## 완료 증거

- 회의록 Markdown 경로와 Notion 페이지 URL
- `Duration`, `Date`, `Week` 및 KPI 속성 재조회 결과
- 프로필 정독 / 접촉 발송 / 내부 추천 판정 / 고객사 실제 추천의 각 수치와 출처
- 토트·두나무 등 최우선 Follow-up과 예정 일정
- Notion 네이티브 블록 수와 샘플 원문 대조 결과
- 테스트, Git 커밋·PR 또는 배포 결과
