# Invoice 스킬 목표·검증 계약 — 2026-09-01

## 결론

이번 단계는 밸류커넥트 주식회사가 발행하는 채용 수수료 청구서를 Codex와 Claude에서 같은 규칙으로 만들 수 있게 하고, 사용자 제공 예시 2건을 **메일로 보내지 않은 검수용 PDF**로 제시하는 데서 멈춘다.

최종 발송 전에 사용자가 결정할 것은 세 가지다. 부가가치세를 별도·포함·비대상 중 무엇으로 처리할지, 최종 인보이스 번호 규칙을 둘지, 계좌 예금주를 문서에 표시할지다. 이 중 금액을 바꾸는 부가가치세 기준이 미확정인 동안에는 스킬이 메일을 보내면 안 된다.

## 판단 근거

- 사용자 예시 두 건은 결정 연봉의 정확히 20%를 수수료로 제시한다. 따라서 검수본의 기본 수수료율은 20%로 계산하되, 두 예시에서 추론한 값임을 계약에 남긴다.
- “입사 후 14일 이내”는 별도 영업일 조정 지시가 없으므로 입사일에 달력 날짜 14일을 더한다. 주말·공휴일 조정은 계약서 원문이 없어서 적용하지 않는다.
- 부가가치세 기준 없이 “총 청구 금액”을 최종 확정하면 실제 수금액이 달라질 수 있다. 검수본은 수수료와 같은 금액을 “세금 처리 전 검수용 총액”으로 표시하고, 최종 모드와 메일 발송을 차단한다.
- 후보자 이름과 금액이 든 생성물은 git에 넣지 않고 `artifacts/invoices/` 아래에만 둔다. 추적 문서와 시험에는 실제 예시 이름을 기록하지 않는다.

> **무엇을** — 하나의 계산·렌더러를 두 프로젝트 스킬이 함께 호출하고, 두 `SKILL.md`의 업무 계약은 바이트 단위로 같게 유지한다.
> **왜** — 계산 규칙이 Codex와 Claude에서 갈라지면 같은 입사 건에 서로 다른 금액이나 기한이 발행될 수 있다.
> **버린 길** — 각 스킬 안에 별도 Python 스크립트를 복사하는 방식은 중복 수정과 불일치 위험 때문에 기각한다.
> **대가** — 두 스킬은 이 저장소의 `tools/invoice/`와 `contracts/invoice/` 경로가 있어야 완전하게 동작한다.
> **되돌리기** — 이 작업 브랜치의 신규 경로와 SOT 색인 한 줄을 제거하면 기존 제품 동작에 영향 없이 원복된다.

## 현재 상태와 회수 결과

- 위험등급은 L3다. SOT 수정, 3개 초과 파일, 금액 계산, 계좌 정보, 후보자 개인정보, 메일 외부 효과를 함께 다룬다.
- 시작 커밋은 `b7240936827032d5ee6791fa8cdb7d62ef6584b4`다.
- 시작 `main`에는 다른 작업의 미추적 파일 `docs/engineering/admin-weekly-dashboard-phase-e-position-cards-goal-2026-09-01.md`가 있었고, 이 작업은 해당 파일을 건드리지 않는 전용 worktree에서 수행한다.
- 저장소에는 기존 `invoice` 또는 `인보이스` 구현이 없었다. 프로젝트 Claude 스킬은 `.claude/skills/<name>/SKILL.md` 형태이고, 프로젝트 Codex 스킬 디렉터리는 아직 없었다.
- PDF 생성 라이브러리는 설치되어 있지 않지만 Google Chrome 152 실행 파일이 있어, 표준 라이브러리로 HTML을 만들고 Chrome의 headless 인쇄 기능으로 PDF를 만든다. 새 패키지는 추가하지 않는다.
- `omx explore`는 Rust `cargo`가 없어 종료값 1로 실패했다. 같은 방법을 반복하지 않고 `rg` 직접 검색과 파일 직접 읽기로 회수했다.

## 근본 원인

채용 수수료 인보이스의 계산식, 기한, 발행자, 계좌, 세금 처리, 개인정보 보관, 메일 승인 경계를 한데 묶은 정본과 실행기가 없다. 지금은 모델이 매번 양식과 계산을 다시 추론해야 하므로 금액·기한·발송 대상이 조용히 달라질 수 있다.

## 범위

### 포함

- `docs/sot/invoice.md` 업무 정본과 `docs/sot/INDEX.md` 색인
- `contracts/invoice/invoice-v1.json` 기계 판독용 상수 계약
- 하나의 Python 계산·HTML·PDF 렌더러와 런타임 시험
- `.codex/skills/invoice`와 `.claude/skills/invoice`의 동일 업무 계약
- 사용자 제공 입력 2건의 검수용 PDF·PNG 미리보기
- Gmail 발송 전 요약, 명시 승인, 발송 결과 재확인 규칙

### 비범위

- 이번 턴의 실제 메일 발송
- 세금계산서 발행, 국세청 연동, 회계 분개
- 계약서 원문 판독 또는 고객사별 수수료율 자동 추출
- 회사 등록번호·주소·대표자·예금주의 임의 보완
- main 병합, push, PR, 배포

## T 계약: 합격 조건과 가짜 합격

T는 이 문서, `docs/sot/invoice.md`, `contracts/invoice/invoice-v1.json`의 합집합이다.

### AC-1 — 수수료 계산

- EARS 단언: **When** 유효한 결정 연봉을 입력하면, 시스템은 입력된 수수료 금액을 받지 않고 정본의 20% 수수료율을 Decimal 연산으로 적용해 원 단위 금액을 계산해야 한다.
- 검증 명령: `python3 -m unittest discover -s tools/invoice/tests -v`
- 기대값: 60,000,000원은 12,000,000원, 40,000,000원은 8,000,000원이며 전체 시험이 0건이 아닌 상태로 성공한다.
- counter-AC: 예시 수수료를 그대로 복사하거나, 부동소수점 오차를 반올림 결과로 숨기거나, 입력 JSON이 수수료를 덮어쓸 수 있으면 가짜 합격이다.

### AC-2 — 납부 기한

- EARS 단언: **When** 입사일을 입력하면, 시스템은 달력 날짜로 14일을 더한 날짜를 납부 기한으로 계산해야 한다.
- 검증 명령: `python3 -m unittest discover -s tools/invoice/tests -v`
- 기대값: 2026-09-01은 2026-09-15이고 월말·윤년 경계도 실제 날짜 연산으로 통과한다.
- counter-AC: 문자열의 일 숫자만 14 증가시키거나, 주말을 근거 없이 다음 영업일로 미루면 가짜 합격이다.

### AC-3 — 문서 내용

- EARS 단언: **When** 검수용 인보이스를 렌더하면, 시스템은 발행자, 수신 회사, 입사자명, 입사일, 직책, 결정 연봉, 요청 수수료, 총 청구 금액, 납부 기한, 은행, 계좌번호를 한 페이지에 표시해야 한다.
- 검증 명령: `python3 -m unittest discover -s tools/invoice/tests -v`
- 기대값: HTML 의미 구조 시험이 필수 항목을 모두 찾고, 검수용일 때 세금 미확정 문구와 DRAFT 표식을 찾는다.
- counter-AC: PDF 파일만 존재하지만 필수 필드가 빠지거나, 계산용 입력 수수료 문구가 그대로 노출되거나, 은행 계좌가 잘리면 가짜 합격이다.

### AC-4 — 실제 PDF와 레이아웃

- EARS 단언: **When** Chrome 렌더러가 준비된 환경에서 예시를 생성하면, 시스템은 `%PDF-` 서명의 1페이지 A4 PDF와 실제 페이지 PNG 미리보기를 만들어야 한다.
- 검증 명령: `python3 tools/invoice/generate_invoice.py --input <검수 JSON> --output <PDF>`와 `sips -s format png <PDF> --out <PNG>`를 예시 2건에 실행한다.
- 기대값: 두 PDF가 비어 있지 않고, 두 PNG에서 글자·표·계좌·금액이 페이지 밖으로 넘치거나 겹치지 않는다.
- counter-AC: HTML 스크린샷만 보고 PDF를 확인했다고 하거나, 파일이 2페이지로 밀렸거나, 한글이 네모로 깨지면 가짜 합격이다.

### AC-5 — Codex·Claude 공통 스킬

- EARS 단언: **Where** 프로젝트가 Codex 또는 Claude에서 열리면, 각 플랫폼은 `invoice` 스킬을 발견하고 같은 SOT와 같은 렌더러를 호출해야 한다.
- 검증 명령: `PATH=/usr/bin:/bin:/usr/sbin:/sbin python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py .codex/skills/invoice`, 같은 명령을 `.claude/skills/invoice`에 실행, 그리고 `cmp .codex/skills/invoice/SKILL.md .claude/skills/invoice/SKILL.md`. 이 머신의 기본 Homebrew Python에는 검증기 의존 모듈 PyYAML이 없고 시스템 Python에는 있으므로, 제품 의존성을 추가하지 않고 검증기 실행 인터프리터를 고정한다.
- 기대값: 두 빠른 검사가 성공하고 `cmp` 종료값이 0이다.
- counter-AC: 한 플랫폼에만 파일이 있거나, 두 설명·발송 승인 규칙이 다르거나, 두 스킬이 서로 다른 계산 코드를 호출하면 가짜 합격이다.

### AC-6 — 메일 외부 효과

- EARS 단언: **While** `send_enabled=false`, 세금 기준이 미확정, 검수본이거나 사용자가 최종 발송 직전 요약을 승인하지 않은 경우, 시스템은 Gmail 발송 도구를 호출하지 않아야 한다.
- EARS 단언: **When** 모든 차단 조건이 해제되고 사용자가 수신자·첨부 SHA-256·금액·납부 기한을 확인해 발송을 승인하면, 시스템은 1회만 발송하고 Gmail 결과의 메시지 식별자를 다시 읽어 보고해야 한다.
- 검증 명령: 스킬 계약 정적 검사와 V1/V2의 권한 경계 공격. 실제 메일 발송은 이번 범위에서 `SKIPPED`가 아니라 의도적 비범위이며, 최종 제품 완료가 아니라 검수 단계 완료만 판정한다.
- counter-AC: “PDF 생성해”를 발송 승인으로 해석하거나, 같은 승인으로 재시도 발송하거나, 첨부 없이 성공을 보고하면 가짜 합격이다.

### AC-7 — 개인정보와 데이터 안전

- EARS 단언: **When** 실제 후보자 입력과 산출물을 만들면, 시스템은 이를 git 무시 경로 `artifacts/invoices/`에만 저장하고 추적 파일에는 실제 후보자 값을 쓰지 않아야 한다.
- 검증 명령: `git status --short`와 `git check-ignore -v artifacts/invoices/<파일>` 및 `bash scripts/scan-data-exposure.sh tracked`.
- 기대값: 실제 입력·PDF·PNG가 git 추적 후보에 나타나지 않고 데이터 노출 검사가 성공한다.
- counter-AC: 시험 fixture, goal, 로그, 파일명에 실제 후보자 이름을 넣으면 가짜 합격이다.

### AC-8 — 오류·경계

- EARS 단언: **If** 필수 문자열이 비거나, 날짜가 잘못되거나, 연봉이 0 이하이거나 정수가 아니거나, 계약 파일이 손상되거나, Chrome이 없으면 시스템은 이유가 있는 오류와 0이 아닌 종료값을 반환해야 한다.
- 검증 명령: 단위시험과 Chrome 경로 변조 실행.
- 기대값: 정상 입력은 통과하고 잘못된 입력 각 종류는 올바른 이유로 실패한다.
- counter-AC: 빈 값을 `-`로 바꾸어 계속 만들거나, PDF 생성 실패 뒤 HTML만 남기고 성공 종료하면 가짜 합격이다.

## 입출력·오류·경계 계약

### 입력 JSON

```json
{
  "invoice_number": "DRAFT-YYYYMMDD-NNN",
  "issue_date": "YYYY-MM-DD",
  "company_name": "비어 있지 않은 문자열",
  "candidate_name": "비어 있지 않은 문자열",
  "start_date": "YYYY-MM-DD",
  "position": "비어 있지 않은 문자열",
  "annual_salary_krw": 1,
  "draft": true
}
```

- `annual_salary_krw` 대신 `annual_salary_manwon`을 쓸 수 있지만 둘을 함께 쓰거나 둘 다 빼면 거부한다. 만원 값의 원화 변환은 코드가 수행한다.
- 알 수 없는 키, `fee_amount`, `requested_fee`, `total_amount` 입력은 거부한다.
- `annual_salary_krw`는 불리언이 아닌 양의 정수이고 1원 이상 10,000,000,000원 이하만 허용한다.
- 문자열은 앞뒤 공백을 제거한 뒤 1~120자다. HTML 예약 문자는 출력에서 이스케이프한다.
- 날짜는 ISO 달력 날짜여야 한다. 시간대는 문서 날짜 계산에 사용하지 않는다.
- `draft=false`는 정본의 세금·발송 조건이 확정되기 전까지 거부한다.

### 출력

- `<output>.pdf`: A4 1페이지 PDF
- `<output>.html`: 같은 내용의 검증 가능한 중간 산출물
- `<output>.metadata.json`: 계산 결과, 계약 버전, 입력 파일과 PDF의 SHA-256. 실제 후보자 정보가 포함되므로 `artifacts/` 밖에서는 생성하지 않는다.
- stdout: 상태, 출력 경로, 수수료, 납부 기한, PDF SHA-256. 후보자 이름은 출력하지 않는다.

### 오류

- 입력·계약 위반: 종료값 2와 `INPUT_ERROR:` 또는 `CONTRACT_ERROR:`
- 렌더러 부재·PDF 실패: 종료값 3과 `RENDER_ERROR:`
- 성공: 종료값 0과 `VERDICT: PASS`, 생성 파일 수 `CHECKED: 3`
- 부분 파일을 성공으로 보고하지 않는다. 실패 시 같은 실행에서 생성한 임시 파일은 최종 경로로 승격하지 않는다.

### 동시성·재시도

- 임시 파일은 출력 경로와 같은 디렉터리의 고유 임시 디렉터리에 만들고, 완성 뒤 교체한다.
- 이미 존재하는 출력은 `--overwrite` 없이는 거부한다.
- 메일은 첨부 SHA-256을 멱등키로 삼아 같은 파일의 중복 발송을 차단해야 한다. Gmail 도구 실패는 자동 재발송하지 않고 사용자에게 결과를 보고한다.

## Harness 게이트 계획

| 게이트 | 이번 작업의 증거 |
|---|---|
| 0 | 원칙 직접 로드, 시작 HEAD·오염·기존 구현 회수, 전용 worktree |
| 1 | 이 문서의 EARS AC·counter-AC·입출력·오류·경계 계약 |
| 2 | 렌더러가 없어서 실패하는 RED 시험을 먼저 실행 |
| 3 | 최소 구현으로 GREEN, 계산식·날짜·입력 검증 뮤테이션 |
| 3.5 | `$invoice` → SOT/계약 → CLI → HTML → Chrome PDF → Gmail 승인 경계 호출 경로 |
| 4 | 단위시험, 스킬 검사, SOT 검사, 저장소 검증, 예시 2건 실제 렌더·시각 확인 |
| 5 | 로컬 검수 브랜치와 산출물 링크. 메일·push·PR은 수행하지 않음 |
| 6 | 사용자 검수 뒤 별도 승인 단계에서만 최종 설정·발송·병합 |

## G/V1/V2/T 적대 검증 정조준

- G: 이 세션의 Codex가 SOT·계약·렌더러·스킬·검수본을 만든다.
- V1: `ANTHROPIC_API_KEY`를 제거한 Claude CLI가 입력 위조, 금액·날짜 경계, HTML 주입, 2페이지 넘침, 세금 미확정 발송, 중복 발송, 두 스킬 드리프트, 검사 대상 0건을 읽기 전용으로 공격한다.
- V2: 새 Codex 검증자가 V1의 모든 재현 명령과 파일 위치를 다시 실행하고, V1의 과장·누락 및 PDF 시각 맹점을 재공격한다.
- T: 이 문서 + 기능 SOT + JSON 계약. 셋이 갈리면 완료로 판정하지 않는다.

## 롤백·영향 반경·데이터 안전

- 영향 반경: 신규 `invoice` 경로, SOT 색인, git 무시 산출물뿐이다. 기존 HumanSearch 제품 경로는 호출하지 않는다.
- 롤백: 작업 브랜치를 삭제하거나 신규 경로와 INDEX 항목을 되돌린다. 운영 DB·외부 계정·기존 산출물에는 되돌릴 변경이 없다.
- 데이터 안전 AC: 실제 이름이 추적 파일·커밋·터미널 전체 출력에 남지 않고, Gmail 호출은 0건이어야 한다.
- 복구 불변조건: PDF 생성이 부분 실패하면 최종 PDF를 성공 산출물로 남기지 않으며, 재실행은 `--overwrite` 명시 없이는 기존 파일을 덮지 않는다.

## 검증 장부

| 시각 | 커밋/세션 | 명령 | 상태 | 전체 출력 위치 또는 결과 |
|---|---|---|---|---|
| 2026-09-01T10:31:20+09:00 | `b724093` / Codex goal `01a05a91-015b-7ad2-8dce-02b4b37df66a` | `sed -n '1,1000p' docs/sot/coding-principles.md` | PASS | 파일 직접 로드, P11 hard 600 LOC 확인 |
| 2026-09-01T10:31:28+09:00 | 동일 | `sed -n '1,1000p' docs/sot/principles.yaml` | PASS | 장부 34항목 직접 로드 |
| 2026-09-01T10:31:32+09:00 | 동일 | `bash scripts/acceptance-principles-check.sh` | PASS | `MECHANISMS: PASS 34/34`, `WIRING: PASS pre-push=1 ci=1`, `CHECKED: 34` |
| 2026-09-01 | 동일 | `omx explore --prompt ...` | FAIL | `cargo was not found`; `rg` 직접 검색으로 경로 변경 |
| 2026-09-01 | 동일 | 구현 전 `python3 -m unittest discover -s tools/invoice/tests -v` | RED | 9개 시험이 `NotImplementedError`로 실패해 구현 전 가짜 초록이 아님을 확인 |
| 2026-09-01 | 동일 | 구현 후 같은 단위시험·`py_compile` | PASS | 9개 시험 성공, 계산·기한·입력·계약 경계 포함 |
| 2026-09-01 | 동일 | 수수료율 20%를 10%로 바꾼 격리 뮤테이션 | PASS | 9개 중 계산·HTML 2개가 실패해 변조를 실제로 탐지 |
| 2026-09-01 | 동일 | Chrome headless 첫 렌더 | FAIL→RECOVERED | PDF 완성 후 Chrome 프로세스가 끝나지 않아 timeout; 완성 서명·EOF 대기 뒤 프로세스 그룹을 종료하는 경계로 수정 |
| 2026-09-01T11:06:41+09:00 | 동일 | 예시 2건 PDF·PNG 생성과 직접 시각 검사 | PASS | 각 1페이지 A4, 201,221/200,953 bytes, 한글·금액·기한·계좌 잘림/겹침 없음; PDF SHA-256은 검수 산출물 metadata와 일치 |
| 2026-09-01T11:06:41+09:00 | 동일 | `bash scripts/acceptance-invoice.sh` + CI 래퍼 | PASS | 단위시험 9개, `CHECKED: 6`; Codex/Claude 스킬 바이트 동등 |
| 2026-09-01T11:06:41+09:00 | 동일 | CI 무력화·명부 검사 | PASS | ci-step-integrity 14건, semantic-mutations 28개×5종, mechanism registry 31건 |
| 2026-09-01T11:06:41+09:00 | 동일 | SOT·추적 개인정보·비밀·Strict 원칙 검사 | PASS | 추적 224개 위반 0, 원칙 34/34 및 pre-push/CI 배선 성공 |
| 2026-09-01 | Claude Code `2.1.251` V1 | 읽기 전용 적대 검증 첫 완료본 | FAIL | 계약 변조 시험의 잘못된 경로 실패, delivery 상수 미잠금, 고정 CHECKED, 템플릿 토큰 주입, rg 오류 가짜 PASS, 메일 강제 주체 과장 발견 |
| 2026-09-01 | 동일 V1 재실행 | 이전 반례 직접 재현 | PASS | 검수 단계 blocker 없음, 최종 발행·메일 BLOCKED 유지; PDF 시각은 독립 증거로 분리 |
| 2026-09-01 | Codex G 후속 | V1 잔여 위험 회귀 보강 | PASS | 단위시험 12개: 계약 문자열 토큰 방어, HALF_UP, 평년/윤일, 3산출물·metadata SHA·overwrite, artifact 경로 탈출 추가 |
| 2026-09-01 | vision 독립 검증 | 최종 재생성 PNG 2건 직접 검사 | PASS | A4 1페이지, 한글, 금액·계좌, 표 정렬, DRAFT, 잘림·겹침 이상 없음; 재생성 뒤 재검사에서도 변화 없음 |
| 2026-09-01T11:41:09+09:00 | Codex G | 최종 예시 PDF 재생성 | PASS | 001 SHA `e877600979c15f1e6508b4cd49f303fa134149e6361463a3bf848940770ed50c`, 002 SHA `bb5a4b991a7a6be15af649449fc67cf1069f0d780120981682dd901a4c358079`; 각 1페이지, `CHECKED: 3` |
| 2026-09-01T11:41:09+09:00 | Codex G | V1 산출물 보존 | PASS | `.omx/artifacts/claude-invoice-v1-20260901.md`, SHA `b648efce965485658d34adab631a7c8d0ed4f39155fc9552a729296347f22d9a` |

## 적대 검증 로그

### V1

- 실행 명령: `env -u ANTHROPIC_API_KEY claude --safe-mode --strict-mcp-config -p --tools 'Read,Grep,Glob,Bash' --dangerously-skip-permissions --no-session-persistence --output-format text <V1 prompt>`
- 실행 정체성: 로컬 Claude Code `2.1.251`; CLI가 모델 세부 식별자는 출력하지 않음.
- 첫 두 시도는 프로젝트 MCP 초기화와 과도한 범위로 결과를 반환하지 못해 합격 증거로 세지 않았다. 최소 모드 준비 프로브 `CLAUDE_V1_READY` 뒤 범위를 나눠 실행했다.
- 첫 완료본은 `FAIL`, 수정 뒤 재실행은 `PASS`. 최종 원문·프롬프트·후속 조치 보존 위치와 해시는 위 검증 장부와 같다.
- V1 이후 남은 지적도 추가 수정했으므로 최종 판정 권한은 fresh V2에 둔다.

### V2

- 첫 실행 `FAIL`: 제품 반례가 아니라 AC-5에 적힌 기본 `python3`가 PyYAML을 찾지 못한 환경 문제와 신규 파일 미커밋 상태를 병합 blocker로 판정했다. 동일 공식 검증기는 위의 시스템 Python 명령으로 두 스킬 모두 `Skill is valid!`를 반환했다.
- 조치: AC-5 명령을 실제 통과한 인터프리터로 고정하고, 모든 신규 파일을 로컬 검수 브랜치에 Lore 체크포인트로 커밋한 뒤 같은 fresh V2를 재실행한다.
