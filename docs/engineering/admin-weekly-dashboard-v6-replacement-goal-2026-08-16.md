# 관리자 주간 대시보드 v6 전면교체 목표·실행 계약 — 2026-08-16

> 문서 상태: 구현 기준 v2
> 적용 저장소: Valuehire_v6
> 위험 등급: L3 — 관리자 인증, 고객 메일, 후보자 자료, ClickUp 운영 쓰기와 서비스 전환이 함께 걸린다.
> 이 문서 전체가 실행 계약이다. 앞부분은 구현 금지문이 아니라 범위·권한·중지점을 설명한다.

## 1층 — 결론

새 관리자 주간 대시보드는 기존 프로그램을 고치거나 복사하지 않고 Valuehire_v6 안에 새 제품으로 만든다. 기존 세대는 실행 중에 전혀 필요하지 않아야 하며, 과거 후보 자료는 정해진 반출 형식으로만 한 번 받아온다.

첫 구현은 새 제품이 이 저장소의 자동 검사에서 빠지지 않게 연결하는 일부터 시작한다. 그다음 메일·고객사 업무·후보 발견 기록을 덮어쓰지 않는 장부와 주간 계산을 만들고, 마지막에 읽기 전용 실제 자료로 숫자를 대조한다.

현재 문서만으로 빈 제품 틀, 날짜·숫자 계산, 가짜 자료 시험, 기록 장부와 **가짜 자료 기반** 미리보기 화면까지 구현할 수 있다. 실제 한 주의 미리보기 화면, 고객 메일 수집, 고객사 업무 등록, 운영 주소 연결은 아래 외부 입력과 사업 오너의 단계별 승인이 없으면 실행하지 않는다.

## 2층 — 확정한 결정

### 결정 카드 1 — 새 관리자 제품은 apps/admin에 독립시킨다

> **무엇을** — 웹 화면, 관리자 API, 메일·ClickUp 작업 실행기는 apps/admin 아래 하나의 독립 제품으로 만든다.
> **왜** — 현재 humansearch는 Python 검증 경계이며 관리자 웹 제품이 아니다. 두 제품을 한 패키지에 섞으면 배포와 장애 범위가 얽힌다.
> **버린 길** — humansearch 안에 임시 웹 화면을 만든 뒤 나중에 옮기는 길을 버린다. 임시 경계가 운영 경계로 굳을 가능성이 높다.
> **대가** — Node 제품 검사를 루트 검사·서버 검사·정본 문서에 새로 연결해야 한다.
> **되돌리기** — apps/admin 전체를 독립 브랜치에서 제거하면 기존 Python 검증 경계는 그대로 남는다.

### 결정 카드 2 — 기술 기반을 이 문서에서 고정한다

> **무엇을** — Node 24.19.0, pnpm 11.22.0, Next.js 16.3.1, React 19.2.8, TypeScript 6.0.3, ESLint 10.8.1, Vitest 4.1.10, Playwright 1.62.1, Prisma 7.9.1과 PostgreSQL 17.11을 사용한다.
> **왜** — 2026-08-16 지원 중인 LTS·안정판과 실제 lint 명령까지 고정해 구현자가 핵심 기반을 임의 선택하지 않게 한다. 현재 작업기의 Node 22.19.0·pnpm 10.33.0은 문서 검증 환경일 뿐 제품 버전 계약이 아니다.
> **버린 길** — 기반을 Phase 0에서 다시 고르는 길과 여러 시험기·여러 데이터 접근 도구를 함께 넣는 길을 버린다.
> **대가** — 새 major 전환은 별도 호환성 검증이 필요하며, TypeScript compiler API 의존 도구의 peer range를 먼저 확인해야 한다.
> **되돌리기** — 버전 변경은 별도 결정 기록과 잠금 파일 차이, 전체 검증 결과를 가진 독립 작업으로만 한다.

### 결정 카드 3 — 원자료·파생 결과·외부 쓰기를 서로 다른 장부에 둔다

> **무엇을** — 받은 사실, 본문 추출판, 업무 대상, ClickUp 쓰기 시도, 재조회 결과, 상태 변화, 주간 보고판을 서로 다른 뒤에만 덧붙이는 장부로 저장한다.
> **왜** — 한 행을 계속 고치면 예전 본문·예전 상태·회의 당시 숫자를 다시 증명할 수 없다.
> **버린 길** — 메일 한 행과 ClickUp 한 행에 현재값만 저장하는 단순 구조를 버린다.
> **대가** — 표와 조회가 늘고 현재 상태를 계산하는 읽기 모델이 필요하다.
> **되돌리기** — 원자료 장부는 유지하고 읽기 모델과 계산 버전만 교체한다.

### 결정 카드 4 — 중복 방지는 메일이 아니라 업무 대상에서 한 번 더 잠근다

> **무엇을** — 같은 메일 재처리와 같은 고객사·포지션·후보 조합 재처리를 별도 고유 제약으로 막는다.
> **왜** — 서로 다른 메일 두 통이 같은 추천을 담을 수 있으므로 메시지 고유값만으로는 ClickUp 중복을 막지 못한다.
> **버린 길** — 제목·본문 유사도 점수로 자동 합치거나 ClickUp 조회만 믿는 길을 버린다.
> **대가** — 정확히 같지 않은 비슷한 항목은 사람이 확인해야 하며 자동 처리율이 낮아질 수 있다.
> **되돌리기** — 비교용 정규화 버전을 새로 만들되 기존 연결과 원문 지문은 삭제하지 않는다.

### 결정 카드 5 — Google Calendar 표시 주차와 실적 기간을 분리한다

> **무엇을** — 화면의 회의 주차 라벨은 오너가 확인한 Google Calendar 표시 규칙을 쓰고, 내부 기간 key와 실적 구간은 날짜로 고정한다. 실적은 회의가 속한 월요일보다 8일 전 일요일부터 1일 전 일요일 직전까지 센다.
> **왜** — 월요일 34주차 회의가 보는 실적은 34주차 월요일부터가 아니라 바로 전 일요일부터 토요일까지이기 때문이다.
> **버린 길** — Google Calendar가 ISO 주차를 표시한다고 추측하는 길, 기존 세대의 월요일 시작 집계, 자료를 가져온 시각으로 사건 시각을 대신하는 길을 버린다.
> **대가** — 표시 주차 규칙이 오기 전에는 라벨을 NOT_RUN으로 보여 주고, 회의 날짜·실적 시작·끝·보고 생성 시각을 모두 저장해야 한다.
> **되돌리기** — 원자료는 그대로 두고 새 계산 버전으로 새 보고판을 만든다. 기존 보고판은 고치지 않는다.

## 2.1 지금 외부에서 받아야 하는 값과 정확한 중지점

| 필요한 값 | 오너 | 값이 없을 때 가능한 일 | 값이 없을 때 금지되는 일 |
|---|---|---|---|
| Google Calendar의 calendar id와 반복 일정 id | 사업 오너 | 날짜를 직접 넣는 주간 계산·시험 | 실제 회의 자동 탐색 |
| Google Calendar UI의 locale·주차 표시 설정과 기준 예시 2건(연말 경계 1건 포함) | 사업 오너 | 날짜 기반 기간 계산과 내부 period key | 화면 주차 라벨 PASS |
| 인증된 기존 대시보드 캡처와 기준 화면 크기 | 사업 오너 | 정보 구조와 새 화면 골격 | 시각 동일 판정 |
| 메일·후보 원자료 보관기간, 열람 역할, 삭제 승인자 | 사업 오너 | 합성 자료와 빈 DB 구조 | 실제 메일·과거 후보 자료 적재 |
| KMS/Secret Manager 종류, key URI, key 관리자와 rotation/파기 절차 | 보안·인프라 오너 | 임시 key의 합성 암호화 시험 | 실제 개인정보 암호화·적재 |
| 네 Gmail 계정의 Workspace 위임 설정 | Google Workspace 관리자 | 합성 시험 | 네 계정 실제 읽기 |
| Google OIDC client, 허용 ADMIN_ORIGIN, callback 등록 | Google Workspace 관리자 | auth adapter 합성 시험 | 실제 관리자 로그인 |
| ClickUp 운영 쓰기 승인 | 사업 오너 | 읽기·dry-run·가짜 서버 시험 | task 생성·수정·상태 이동 |
| v4/v5/v6 × aisearch/humansearch 6개 source pair의 export manifest 또는 “자료 없음” 확인 | 데이터 오너 | 6종 합성 importer·coverage 시험 | 실제 과거/현재 discovery 숫자 PASS |
| 운영 주소와 배포 대상 | 사업 오너 | 로컬·시험 주소 실행 | admin.valuehire.cc 연결 |
| 모호한 포지션 확인 기한 | 운영 오너 | UNCLASSIFIED 보관 | 자동 완료 숫자 판정 |

→ 위 값은 구현자가 추측할 기술 선택이 아니라 외부 계정·운영 정책이다. 값 하나가 없다고 전체 작업을 멈추지 않고, 표의 오른쪽 범위만 NOT_RUN으로 남긴다.

## 3층 — 실행 계약

## 3. 역할·권한·정본

너는 Valuehire_v6 관리자 주간 대시보드 구현자다. 이 문서 전체를 새 작업의 목표 계약으로 사용한다.

정본 우선순위:

~~~text
현재 세션에 주입된 AGENTS 지침 또는 저장소 AGENTS.md
  > docs/sot/*
  > 이 목표 계약
  > Phase별 goal 문서
  > 구현
  > 시험
~~~

→ 저장소에 AGENTS.md 파일이 없더라도 현재 세션에 실제로 주입된 지침이 있으면 그 지침을 기록하고 진행한다. 둘 다 없으면 AGENTS를 만들어 냈다고 주장하지 말고 docs/sot를 최상위 저장소 정본으로 사용한다.

허가 범위:

- 로컬 파일 작성, 의존성 잠금, 합성 시험, 로컬 PostgreSQL 시험, 읽기 전용 Gmail·Calendar·ClickUp 확인.
- Phase별 task 브랜치·worktree 생성, 커밋, PR 생성.
- 이 문서 작성 작업 자체와 Phase 0~3은 운영 ClickUp 쓰기·배포·운영 주소 연결을 허가하지 않는다. Phase 4의 정확히 한 task만 이 문서와 별개의 오너 live-write 지시, 유효한 LiveWriteApproval, Phase 0~3 GREEN이 모두 있을 때 허용한다.
- Phase 5 배포·운영 주소 연결도 이 문서와 별개의 오너 cutover 지시와 Phase 5 진입조건이 모두 있어야 허용된다. 이 문서만으로는 허가가 아니다.
- bulk ClickUp 쓰기, 메일 발송, 기존 자료 삭제, PR merge는 허가하지 않는다.

## 4. 현재 저장소 기준과 첫 번째 작업

현재 HEAD 기준 사실:

- README.md:7은 아직 제품 소스가 없는 부트스트랩 상태라고 말한다.
- humansearch/src/humansearch/__init__.py는 Python 검증 경계이며 관리자 제품 코드가 아니다.
- 루트 verify.sh는 현재 추적 파일 비밀 검사다.
- hooks/pre-push는 scripts/acceptance-*.sh를 이름 규칙으로 수집한다.
- .github/workflows/verify.yml은 서버에서 실행할 검사를 고정 목록으로 가진다.
- docs/sot/verification-commands.md:43은 새 인수 스크립트를 만들면 서버 설정과 명령표를 함께 갱신하라고 요구한다.

따라서 첫 구현 AC는 화면이 아니라 새 Node 제품 검사가 로컬·push 전·서버 세 곳에서 실제로 실행되는지다.

현재 작업 시작 검사:

~~~text
HEAD: 4fdef31 (synced)
ORIGIN: 4fdef31
RED: 1/19 (acceptance-0-7.sh 제외 — CI 담당)
~~~

→ 기존 빨간불 1건은 scripts/acceptance-0-2.sh가 발견한 도달 불가능 Git 객체 8건이다. 이번 문서 변경으로 생긴 실패가 아니며 숨기지 않는다. 새 Phase는 자기 전용 검사를 별도로 RED에서 GREEN으로 만들고, 전체 저장소 성적은 기존 실패 1건을 포함해 보고한다.

## 5. 고정 저장소 구조

~~~text
/
  package.json
  pnpm-lock.yaml
  pnpm-workspace.yaml
  .node-version
  apps/
    admin/
      package.json
      next.config.ts
      prisma/
        schema.prisma
        migrations/
      src/
        app/
          admin/dashboard/page.tsx
          api/admin/weekly-snapshots/[periodKey]/route.ts
        auth/
        contracts/
        domain/
        db/
        integrations/
          gmail/
          google-calendar/
          clickup/
        jobs/
        ui/
      tests/
        unit/
        integration/
        e2e/
  contracts/
    admin-weekly-dashboard/
      runtime-config.schema.json
      position-taxonomy.schema.json
      candidate-discovery-export-v1.schema.json
      weekly-snapshot-v1.schema.json
  scripts/
    acceptance-admin-foundation.sh
    acceptance-admin-domain.sh
    acceptance-admin-db.sh
    acceptance-admin-connectors.sh
    acceptance-admin-ui.sh
~~~

→ 관리자 제품은 apps/admin 밖의 Python 모듈을 import하지 않는다. contracts 아래 파일은 코드와 사람이 함께 읽는 버전 계약이고, 개인정보나 비밀값을 담지 않는다.

루트 package.json은 private workspace만 선언한다. 새 검사는 다음 네 곳을 한 AC 안에서 함께 갱신한다.

1. scripts/acceptance-admin-*.sh
2. .github/workflows/verify.yml의 실제 실행 단계
3. docs/sot/verification-commands.md의 명령표
4. docs/sot/mechanism-registry.yaml의 검사 장치 명부

hooks/pre-push가 새 스크립트를 이미 자동 수집한다면 훅을 고치지 않는다. 기존 기능 검색과 실행 증거 없이 훅을 다시 작성하지 않는다.

`acceptance-admin-foundation.sh`는 `scripts/acceptance-admin-*.sh`의 실제 집합과 CI 고정 목록의 admin 집합이 정확히 같은지 비교한다. 한쪽에서 하나를 빼는 mutation이 RED가 되어야 한다. 각 admin acceptance는 마지막에 다음 machine-readable receipt를 정확히 한 줄 출력한다.

~~~text
ADMIN_GATE_JSON={"gate":"admin-db","verdict":"PASS|FAIL|NOT_RUN","targetCount":1,"evidenceSha256":"...","reason":null}
~~~

→ 각 gate가 무엇을 실제로 검사했고 몇 건을 처리했는지 남기는 영수증이다. Phase별 required gate에서 `NOT_RUN`, receipt 누락, `targetCount=0`은 전체 PASS가 아니다. 외부 입력 때문에 의도적으로 못 도는 live gate는 해당 Phase의 expected NOT_RUN으로 보존하되 그 Phase 완료로 세지 않는다. `acceptance-admin-db.sh`는 fenced lease, 단일 write intent, state/readback projection의 실제 PostgreSQL 동시성 시험을 실행해야 하며 소스 문자열 검색으로 대신하지 않는다.

data exposure의 고정 명령은 `bash scripts/scan-data-exposure.sh admin`이다. Phase 0에서 기존 판정기에 admin mode를 추가하고, build·test 직후 `apps/admin/.next`, `apps/admin/test-results`, `apps/admin/playwright-report`, `apps/admin/coverage`, admin application log root를 실제 순회한다. 합성 canary를 각 root에 하나씩 넣은 mutation fixture가 RED가 되어야 하며 대상 root·파일 수 0은 NOT_RUN이다. 같은 명령을 acceptance, pre-push, CI, `docs/sot/verification-commands.md`, `docs/sot/mechanism-registry.yaml`에 등록한다.

## 6. 기술 기반 계약

고정 버전:

~~~json
{
  "node": "24.19.0",
  "pnpm": "11.22.0",
  "next": "16.3.1",
  "react": "19.2.8",
  "react-dom": "19.2.8",
  "typescript": "6.0.3",
  "@types/node": "24.13.3",
  "eslint": "10.8.1",
  "eslint-config-next": "16.3.1",
  "vitest": "4.1.10",
  "fast-check": "4.9.0",
  "@playwright/test": "1.62.1",
  "openid-client": "6.8.5",
  "prisma": "7.9.1",
  "@prisma/client": "7.9.1",
  "@prisma/adapter-pg": "7.9.1",
  "postgresql": "17.11"
}
~~~

→ npm 의존성은 범위 기호 없이 package.json과 pnpm-lock.yaml에 고정한다. Node는 루트 `.node-version`과 `engines.node`, pnpm은 루트 `packageManager`에 각각 고정한다. PostgreSQL 통합 시험은 Docker Compose의 `postgres:17.11-alpine`을 사용하고 구현 PR에서 image digest까지 잠근다. 명시 버전이 해석되지 않거나 peer/runtime 계약을 만족하지 않으면 임의 버전으로 바꾸지 말고 `VERSION_CONTRACT_FAIL`로 중지한다. 버전 변경은 별도 결정 기록·잠금 차이·전체 검증을 가진 독립 작업이다.

구현 원칙:

- Next.js App Router와 TypeScript strict 모드.
- lint는 제거된 `next lint`가 아니라 `eslint . --max-warnings=0`으로 실행한다.
- PostgreSQL이 운영 원장이다. SQLite를 운영 원장으로 사용하지 않는다.
- Prisma Client를 쓰되, 고유 제약·뒤에만 덧붙이는 강제·권한은 검토 가능한 SQL migration으로 만든다.
- Vitest 하나로 순수·통합 시험을 실행하고 Playwright 하나로 브라우저 시험을 실행한다.
- Next.js 요청 처리기 안에 주간 배치를 숨기지 않는다. jobs 아래 명시적 명령으로 실행한다.
- Turborepo, 별도 상태관리 도구, UI kit, 두 번째 ORM, 두 번째 시험기는 도입하지 않는다.
- 각 새 의존성은 package.json 설명 또는 Phase goal에 사용 위치와 제거 조건을 한 줄 남긴다.

## 7. v4·v5 실행 의존성 0 계약

다음은 실패다.

- apps/admin 실행 코드가 Valuehire_v4, Valuehire_v5, 형제 저장소 절대경로를 읽는다.
- 과거 저장소의 환경파일, 데이터베이스, 패키지, 모듈, 정적 HTML, CSS, SQL 함수를 import하거나 실행한다.
- /admin/dashboard가 iframe으로 과거 HTML을 띄운다.
- 운영 집계가 과거 DB를 직접 조회한다.
- 빌드·시험·start가 형제 저장소가 없으면 실패한다.

허용:

- goal 문서에서 과거 코드의 결함을 file:line 근거로 설명한다.
- 과거 저장소가 별도 실행으로 만든 candidate-discovery-export/v1 파일을 가져온다.
- 화면에서 유지할 정보 순서와 지표 의미를 관찰 근거로 다시 정의한다.

클린룸 시험은 새 worktree를 임시 부모 폴더에 복제하는 방식이 아니라 git archive 또는 깨끗한 checkout으로 만들고, 형제 저장소 경로가 없는 상태에서 install, build, test, start를 실행한다. 검사 대상 파일 수가 0이면 PASS가 아니라 NOT_RUN이다.

## 8. 운영 설정·비밀·권한

추적 가능한 설정 모양은 `contracts/admin-weekly-dashboard/runtime-config.schema.json`에 둔다. 실제 mailbox 주소를 포함한 runtime-config.json은 배포 설정 저장소에서 주입하고 gitignore하며, 저장소에는 예시 주소도 넣지 않는다.

~~~ts
type RuntimeConfig = {
  timezone: "Asia/Seoul";
  internalRecipientDomains: ["valueconnect.kr"];
  allowedMailboxRefs: [
    "sangmokang",
    "kcs",
    "julian",
    "rogan"
  ];
  mailboxDirectorySource: "ADMIN_GMAIL_MAILBOX_DIRECTORY_JSON";
  clickup: {
    recommendationListId: "901814621142";
    recommendationStatus: "고객사추천";
    positionListId: "901814621569";
    expectedPositionStatuses: [
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
    ];
  };
  calendar: {
    calendarId: string | null;
    recurringEventId: string | null;
    displayLocale: string | null;
    weekLabelContractVersion: string | null;
  };
  retentionPolicyVersion: string | null;
  manualReviewDueHours: number | null;
};
~~~

→ 네 mailbox ref는 사용자 요구의 담당자 범위를 고정하지만 실제 주소는 담지 않는다. 배포 설정은 각 ref를 `valueconnect.kr` 내부 주소 하나에 정확히 매핑하고 시작 시 HMAC directory와 대조한다. null 값은 알려지지 않은 외부 입력이다. null을 빈 문자열이나 기본 보관기간으로 바꾸지 않는다. 각 값이 막는 기능만 NOT_RUN으로 표시한다.

비밀:

- DATABASE_URL
- Google Workspace 위임 서비스 계정 키 또는 Secret Manager 참조
- ClickUp token
- HMAC key와 payload envelope encryption key-provider 참조
- 관리자 로그인 OpenID Connect 비밀

비밀은 저장소·일반 로그·시험 fixture·브라우저 응답에 들어가지 않는다. 환경변수 이름과 필수 여부만 .env.example에 둔다. 실제 값은 비밀 저장소에서 주입한다.

Gmail과 Calendar 자동 읽기는 Google Workspace 도메인 전체 위임을 사용하며 최소 권한은 gmail.readonly와 calendar.events.readonly다. gmail.modify, 메일 발송 권한은 요청하지 않는다.

비교키는 HMAC-SHA-256이며 key provider의 불변 version을 모든 지문 행에 남긴다. 개인정보 payload는 AES-256-GCM envelope encryption을 사용하고 payload마다 새 96-bit nonce와 data key를 만든다. DB에는 key-provider key version, 암호화된 data key, nonce, auth tag, ciphertext 지문만 두며 평문 key는 저장하지 않는다. 구현 환경의 KMS 또는 Secret Manager 종류와 key URI가 확정되지 않으면 합성 시험은 임시 key provider로 할 수 있지만 실제 자료 적재는 `NOT_RUN(KEY_PROVIDER_MISSING)`이다.

관리자 로그인은 Google OpenID Connect Authorization Code + PKCE로 신원을 확인한다. callback은 `{ADMIN_ORIGIN}/api/auth/callback/google` 한 곳이며 issuer, audience, azp, nonce, state, exp, email_verified와 hosted domain `valueconnect.kr`을 모두 검사한다. 검증된 계정이라도 admin_users에 활성 행이 있어야 접근시킨다. 세션은 DB에 token hash만 저장하고 로그인 때 회전하며 최대 8시간 뒤 만료한다. cookie는 `HttpOnly`, `Secure`(localhost만 예외), `SameSite=Lax`, `Path=/`이고 고정 이름을 쓴다. 역할은 owner, operator, viewer 세 가지다.

최초 owner는 일반 웹 요청이 아니라 `pnpm --filter admin admin:bootstrap-owner --email <valueconnect.kr>` 한 번으로 pending grant를 만든다. 첫 유효 OIDC login이 해당 email HMAC과 subject를 원자적으로 결합하고 `OWNER_BOOTSTRAPPED` audit event를 남긴다. 활성 owner가 한 명이라도 생기면 이 명령은 DB 제약과 명령 양쪽에서 거부된다. 이후 사용자·역할 변경은 owner API와 audit event로만 한다.

GET이 아닌 admin API는 세션에 묶인 CSRF token, 정확한 ADMIN_ORIGIN의 Origin/Host, 역할 권한을 함께 검사한다. token은 응답 body나 log에 남기지 않는다. 사용자·역할·보관정책·manual review·write approval 변경은 요청 전후 값을 HMAC한 audit event를 같은 transaction에 남기며 audit 저장 실패 시 본 작업도 실패한다.

## 9. 주간 기간 계약

~~~ts
type WeeklyWindow = {
  meetingInstanceStartKst: string;
  periodKey: string;
  calendarWeekLabel: string | null;
  calendarWeekLabelStatus: "PASS" | "FAIL" | "NOT_RUN";
  weekLabelContractVersion: string | null;
  isoAnchorKey: string;
  weekAnchorMondayKst: string;
  eventStartKst: string;
  eventEndExclusiveKst: string;
  timezone: "Asia/Seoul";
};

function weeklyWindow(
  meetingStart: ZonedDateTime,
  weekLabelContract: ValidatedGoogleCalendarWeekLabelContract | null
): WeeklyWindow {
  const kst = meetingStart.withTimeZone("Asia/Seoul");
  const monday = startOfIsoWeek(kst);
  const eventStart = monday.minus({ days: 8 }).startOfDay();
  const eventEndExclusive = monday.minus({ days: 1 }).startOfDay();
  const display = resolveGoogleCalendarWeekLabel(kst, weekLabelContract);
  return {
    meetingInstanceStartKst: kst.toISOString(),
    periodKey: `${dateKey(eventStart)}--${dateKey(eventEndExclusive.minus({ days: 1 }))}`,
    calendarWeekLabel: display.label,
    calendarWeekLabelStatus: display.status,
    weekLabelContractVersion: display.contractVersion,
    isoAnchorKey: isoWeekKey(monday),
    weekAnchorMondayKst: monday.toISOString(),
    eventStartKst: eventStart.toISOString(),
    eventEndExclusiveKst: eventEndExclusive.toISOString(),
    timezone: "Asia/Seoul"
  };
}
~~~

→ 2026-08-17 월요일과 같은 주 2026-08-18 화요일로 옮긴 회의는 모두 `2026-08-09--2026-08-15`와 [2026-08-09 00:00 KST, 2026-08-16 00:00 KST)를 반환해야 한다. 시작은 포함하고 끝은 제외한다. `isoAnchorKey=2026-W34`는 내부 진단값일 뿐 화면 라벨의 근거가 아니다. Google Calendar 표시 계약이 없으면 `calendarWeekLabel=null`, status=NOT_RUN이다. 계약은 있지만 기준 예시와 계산 결과가 다르면 label=null, status=FAIL이다. 두 경우 모두 ISO 숫자를 대신 표시하지 않는다.

Calendar 값이 없으면 jobs 명령은 --meeting-start 값을 요구한다. 값을 추측해 이번 주를 자동 선택하지 않는다.

취소된 회의 인스턴스는 보고를 자동 확정하지 않는다. 같은 periodKey에 둘 이상의 유효 회의가 있으면 정확한 한 건을 고를 수 없으므로 MANUAL_REVIEW다.

## 10. Gmail 메시지 선별 계약

Gmail 검색식은 후보를 줄이는 장치일 뿐 판정기가 아니다. messages.list의 모든 page token을 끝까지 읽고 각 결과를 messages.get(messageId, format=full)로 다시 읽는다. threads.get은 금지한다.

~~~ts
type RecruitKind = "recommendation" | "position";

function qualifyMessage(message: GmailMessage, window: WeeklyWindow): RecruitKind | null {
  assert(ALLOWED_MAILBOXES.has(canonicalAddress(message.sourceMailbox)));
  assert(canonicalAddress(message.from) === canonicalAddress(message.sourceMailbox));
  assert(message.labelIds.includes("SENT"));
  const eventMillis = parseGmailInternalDateMillis(message.internalDate);
  assert(toEpochMillis(window.eventStartKst) <= eventMillis);
  assert(eventMillis < toEpochMillis(window.eventEndExclusiveKst));

  const rawSubject = message.subject;
  const kind =
    rawSubject.startsWith("[추천]") ? "recommendation" :
    rawSubject.startsWith("[포지션]") ? "position" :
    null;
  if (!kind) return null;

  const recipients = parseAddresses(message.to, message.cc, message.bcc);
  return recipients.some(address => canonicalDomain(address) !== "valueconnect.kr")
    ? kind
    : null;
}
~~~

→ 제목 앞 공백, Re:, Fwd:, FW:, 받은편지함 메일, 내부 수신자뿐인 메일은 제외된다. 외부 수신자가 To·Cc·Bcc 중 한 명 이상이면 포함한다. 별칭 발신은 계약에 추가되기 전까지 거부한다.

→ `[추천]`·`[포지션]`은 **raw 제목의 첫 문자부터 ASCII `[`로 정확히** 시작할 때만 선별 조건이다. 선별을 통과한 뒤 업무값 파싱용 사본에만 NFKC를 적용한다. 전각 괄호, BOM, zero-width 문자, 앞 공백을 NFKC나 trim으로 살려서 포함하지 않는다. 본문에 같은 글자가 있거나 인용된 이전 메일 제목에 태그가 있어도 선별하지 않는다.

수집 실행은 mailbox마다 다음을 남긴다.

- 시작·종료 시각과 주간 범위
- list page 수, 후보 message 수, full message 성공·실패 수
- 마지막 page token 또는 완료 표식
- 429·5xx 재시도 횟수와 최종 상태
- verdict `PASS | FAIL | NOT_RUN`, completeness `COMPLETE | PARTIAL | NONE` 및 이유

한 페이지라도 끝까지 읽지 못하면 그 mailbox의 completeness는 PARTIAL, verdict는 FAIL, 주간 값은 null이다. PARTIAL을 네 번째 판정으로 사용하지 않는다.

현재 실제 표본 범위는 sangmokang 보낸편지함 6건뿐이다.

~~~text
recommendation=5
position=1
text_plain=6
text_html=6
html_with_gmail_quote=4
html_with_gmail_signature=2
with_attachments=4
external_recipient_counts=[1,1,2,1,1,1]
~~~

→ 개인정보 원문 없이 구조만 남긴 수치다. kcs, julian, rogan은 실제 표본 미확인으로 표시하고 Phase 3 첫 읽기 전용 실행에서 계정별 표본 수 또는 0건 이유를 기록한다.

## 11. 제목 파싱과 업무 대상 계약

허용 문법:

~~~text
[추천] <고객사>, <포지션> - <후보자>
[포지션] <고객사>, <포지션>

고객사 경계 = 태그 뒤 첫 comma 또는 ". "
후보자 경계 = 추천 제목의 마지막 " - "
~~~

→ 실제 6건 표본은 이 문법으로 분리됐다. 문법이 맞지 않거나 한 제목이 여러 포지션·후보자로 해석되면 추측하지 않고 MANUAL_REVIEW다.

원문 표시값은 NFKC와 공백만 정리한다. 비교값은 소문자화 가능한 문자는 소문자화하고, 공백·구두점·후보자 존칭 꼬리를 계약 버전에 따라 정리한다. 고객사·포지션·후보 원문은 암호화하고 비교키는 서버 비밀키 HMAC으로 만든다.

~~~ts
recommendationBusinessKey =
  hmacSha256(secretKeyForVersion(keyVersion),
             canonicalBytes(kind, normalizedClient, normalizedPosition, normalizedCandidate));

positionBusinessKey =
  hmacSha256(secretKeyForVersion(keyVersion),
             canonicalBytes(kind, normalizedClient, normalizedPosition));
~~~

→ 평문 이름 해시는 사전 대입으로 되찾기 쉬우므로 금지한다. HMAC key version을 함께 저장하고 키 교체 때 과거 지문을 조용히 덮지 않는다.

비교키 비밀을 교체할 때는 자동 수집과 ClickUp 쓰기를 잠시 멈추고, 새 버전 지문을 기존 business object에 추가한 뒤 구·신 버전 모두에서 중복이 0인지 대조한다. 대조가 끝나기 전에는 새 키만으로 신규 business object를 만들지 않는다.

## 12. 그 당시 보낸 업무 본문 추출 계약

MIME part 선택 순서:

1. 파일 이름 또는 attachment disposition이 있는 part는 제외한다.
2. multipart/alternative 안에서 text/html 한 개를 우선한다.
3. HTML은 DOM parser로 읽고 정규식만으로 자르지 않는다.
4. gmail_quote, gmail_quote_container, blockquote[type=cite]를 제거한다.
5. gmail_signature, gmail_signature_prefix, data-smartmail=gmail_signature를 제거한다.
6. script, style, image, 추적 요소와 모든 위험 속성을 버리고 문단·목록·줄바꿈을 글자로 바꾼다.
7. HTML이 없을 때만 text/plain을 사용하고 첫 인용 경계와 표준 서명 구분선 뒤를 자른다.
8. NFKC, 줄끝, 연속 빈 줄만 정리한다. 이름·회사·금액·전화번호·URL 내용을 고치지 않는다.
9. 결과가 비었거나 제거 전후 차이가 비정상적으로 크면 MANUAL_REVIEW다.

~~~ts
type MailBodyExtraction = {
  gmailMessageRecordId: string;
  extractorVersion: string;
  inputSha256: string;
  sourcePart: "sanitized_html" | "plain_fallback";
  businessBodyPayloadRefId: string;
  businessBodyHmac: string;
  hmacKeyVersion: string;
  removedQuoteNodes: number;
  removedSignatureNodes: number;
  extractedAt: string;
};
~~~

→ ClickUp description에는 복호화한 business body text만 넣는다. 제목, message id, 자동등록 문구, 이전 대화, 서명, 첨부파일, 추적 표식은 description에 넣지 않는다.

같은 Gmail message에서 extractor v2가 다른 본문을 만들면 v1 행을 UPDATE하지 않는다. 새 추출판을 추가하고, 이미 ClickUp task가 있으면 본문 변경 제안을 만들 뿐 자동 덮어쓰지 않는다.

실제 메일 원본을 저장할지는 보관 정책이 결정한다. 정책이 없으면 합성 fixture만 사용하고 실제 수집은 NOT_RUN이다. 원본을 저장하도록 승인되면 접근 제한 object storage에 암호화하고 URI·지문·삭제 예정 시각만 DB에 둔다.

## 13. 포지션 분류 계약

반환값은 실제 ClickUp 상태 하나 또는 UNCLASSIFIED다.

~~~ts
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
  | "UNCLASSIFIED";
~~~

→ scraped, closedpositions, complete는 직무가 아니다. UNCLASSIFIED만 임시로 scraped에 둔다. etc는 자동 분류 결과로 사용하지 않는다.

position-taxonomy.json 각 규칙은 id, version, targetStatus, priority, exactPhrases, includeTokens, excludeTokens을 가진다.

초기 의미:

- backend/fullstack/cto: backend, back-end, fullstack, full-stack, server, 서버, 백엔드, 풀스택, CTO
- ai/ml/data: AI, ML, machine learning, data scientist, data engineer, 데이터, 머신러닝, MLOps
- po/pm/기획: product manager, product owner, PO, PM, 서비스기획, 상품기획
- frontend: frontend, front-end, 프론트엔드
- designer: designer, design, UX, UI, 디자인
- sales/bd: sales, business development, BD, 영업, 사업개발
- marketing: marketing, marketer, 마케팅
- devops/sre/security/qa: DevOps, SRE, security, QA, 인프라, 보안, 테스트
- hr/finance/strategy/etc: HR, 인사, 채용, finance, accounting, 재무, 회계, strategy, 전략
- c-level: CEO, COO, CFO, CSO와 명시적 대표·임원. CTO는 위 backend 분류를 우선한다.
- app: iOS, Android, mobile, Flutter, React Native, 모바일, 앱

exact phrase 한 개가 고유하게 일치할 때만 자동 확정한다. 두 상태가 동시에 일치하거나 Engineer, 엔지니어, 개발자만 있거나 규칙이 하나도 없으면 UNCLASSIFIED다. LLM 제안은 운영 상태를 직접 쓰지 못한다.

## 14. PostgreSQL 원장 계약

아래는 의미 계약이다. 실제 migration은 PostgreSQL 제약, foreign key, CHECK, index, 권한과 뒤에만 덧붙이는 trigger를 포함해야 한다.

~~~text
cryptographic_key_versions
  purpose, version, provider_key_uri, state,
  active_from, verify_until_nullable, retired_at_nullable,
  destroyed_at_nullable, destroy_receipt_sha256_nullable
  UNIQUE(purpose, version)
  UNIQUE(purpose) WHERE state = 'ACTIVE'

cryptographic_key_state_events
  id, purpose, version, from_state_nullable, to_state,
  actor, occurred_at, evidence_sha256

pii_payload_refs
  id, payload_kind, key_provider, kek_version, retention_policy_version,
  purge_after, created_at

pii_payload_blobs
  payload_ref_id, ciphertext_uri, ciphertext_sha256,
  encrypted_data_key, nonce_96bit, auth_tag, stored_at
  UNIQUE(payload_ref_id)

pii_payload_lifecycle_events
  id, payload_ref_id, event_type, policy_version,
  actor, occurred_at, evidence_sha256

gmail_source_mailboxes
  id, mailbox_address_hmac, hmac_key_version, active,
  created_at, disabled_at_nullable
  UNIQUE(hmac_key_version, mailbox_address_hmac)

gmail_messages
  id, source_mailbox_id, provider_metadata_payload_ref_id,
  kind, sent_at, rfc2822_date, raw_message_payload_ref_id_nullable,
  retention_policy_version, purge_after, ingested_at

gmail_message_lookup_keys
  id, gmail_message_record_id, provider_message_key_hmac,
  hmac_key_version, active_until, created_at
  UNIQUE(hmac_key_version, provider_message_key_hmac)

gmail_body_extractions
  id, gmail_message_record_id, extractor_version, input_sha256,
  source_part, business_body_payload_ref_id, business_body_hmac,
  removed_quote_nodes, removed_signature_nodes,
  retention_policy_version, purge_after, extracted_at
  UNIQUE(gmail_message_record_id, extractor_version, input_sha256)

gmail_body_selection_events
  id, gmail_message_record_id, extraction_id,
  previous_extraction_id_nullable, selected_at, reason, actor

gmail_body_active_selections
  gmail_message_record_id, extraction_id, selection_event_id
  UNIQUE(gmail_message_record_id)

business_objects
  id, kind, target_list_id, client_payload_ref_id,
  position_payload_ref_id, candidate_payload_ref_id_nullable,
  parse_contract_version,
  retention_policy_version, purge_after, created_at

business_object_keys
  id, business_object_id, kind, target_list_id,
  hmac_key_version, business_key_hmac, active_from,
  active_to_nullable, created_at
  UNIQUE(kind, target_list_id, hmac_key_version, business_key_hmac)

mail_business_links
  gmail_message_record_id, business_object_id, link_reason, linked_at
  UNIQUE(gmail_message_record_id, business_object_id)

mail_processing_reviews
  id, gmail_message_record_id, stage, reason_code,
  status, assigned_role, opened_at, resolved_at_nullable,
  resolution_event_sha256_nullable

admin_users
  id, subject, email_hmac, role, active, created_at, disabled_at_nullable
  UNIQUE(subject)

admin_bootstrap_grants
  id, email_hmac, role, state, issued_at, consumed_at_nullable,
  bound_subject_nullable
  CHECK(role = 'owner')
  UNIQUE(email_hmac) WHERE state = 'pending'

admin_sessions
  id, admin_user_id, token_hash, issued_at, rotated_at,
  expires_at, revoked_at_nullable, auth_context_sha256
  UNIQUE(token_hash)

access_audit_events
  id, admin_user_id, action, resource_type,
  resource_id_hmac, occurred_at, outcome

retention_policies
  version, raw_mail_days, extracted_body_days,
  candidate_payload_days, derived_identifier_days,
  audit_days, effective_at, approved_by
  UNIQUE(version)

data_deletion_events
  id, resource_type, resource_id_hmac, policy_version,
  requested_at, executed_at_nullable, outcome,
  storage_delete_receipt_sha256_nullable,
  key_destroy_receipt_sha256_nullable, evidence_sha256_nullable

live_write_approvals
  id, owner_admin_user_id, approved_scope,
  target_mail_message_record_id, target_business_object_id,
  issued_at, expires_at, consumed_at_nullable, state
  UNIQUE(id)

live_write_approval_events
  id, approval_id, from_state_nullable, to_state,
  actor, occurred_at, evidence_sha256

clickup_registration_targets
  id, business_object_id, target_list_id, desired_status,
  current_state, current_state_event_id, lease_epoch,
  clickup_task_id_nullable, created_at
  UNIQUE(business_object_id, target_list_id)

clickup_registration_state_events
  id, registration_target_id, sequence_no, from_state_nullable, to_state,
  reason, actor, occurred_at, evidence_sha256_nullable
  UNIQUE(registration_target_id, sequence_no)

clickup_write_leases
  id, registration_target_id, lease_epoch, lease_token_hash,
  lease_owner, leased_at, expires_at, released_at_nullable,
  release_reason_nullable
  UNIQUE(registration_target_id, lease_epoch)
  UNIQUE(registration_target_id) WHERE released_at IS NULL

clickup_write_attempts
  id, registration_target_id, approval_id, write_lease_id,
  lease_epoch, idempotency_key,
  request_fingerprint_sha256, request_body_sha256, started_at,
  response_received_at_nullable, response_http_status_nullable,
  response_body_sha256_nullable, outcome
  UNIQUE(idempotency_key)
  UNIQUE(registration_target_id)
  UNIQUE(approval_id)

clickup_readbacks
  id, registration_target_id, attempt_id_nullable, readback_type,
  observed_task_id_nullable, observed_status_nullable,
  observed_body_sha256_nullable, matched, ambiguity_count,
  read_at, evidence_sha256

clickup_body_change_proposals
  id, registration_target_id, old_extraction_id, new_extraction_id,
  proposal_state, created_at
  UNIQUE(registration_target_id, old_extraction_id, new_extraction_id)

legacy_export_batches
  id, schema_version, source_generation, source_system,
  exported_at, row_count, sha256, rows_payload_ref_id, imported_at
  UNIQUE(source_generation, source_system, sha256)

legacy_export_rows
  id, export_batch_id, source_row_ordinal, source_record_id_nullable,
  source_row_sha256, raw_payload_ref_id, import_state,
  rejection_reason_nullable, retention_policy_version,
  purge_after, imported_at
  UNIQUE(export_batch_id, source_row_ordinal)

sourcing_runs
  id, source_generation, source_system, source_run_id,
  triggered_at_nullable, completed_at_nullable, created_at
  UNIQUE(source_generation, source_system, source_run_id)
  UNIQUE(id, source_generation, source_system)

native_discovery_batches
  id, source_generation, source_system, adapter_version,
  triggered_at_nullable, completed_at_nullable,
  collected_at, row_count, evidence_sha256

candidate_discovery_facts
  id, sourcing_run_id_nullable, run_identity_quality,
  legacy_export_row_id_nullable,
  native_discovery_batch_id_nullable, native_row_ordinal_nullable,
  source_generation, source_system,
  source_record_id_nullable, position_source_id_nullable,
  position_title_payload_ref_id_nullable, channel, discovered_at_nullable,
  candidate_key_type, candidate_source_key_hmac_nullable,
  raw_payload_ref_id, raw_payload_sha256,
  retention_policy_version, purge_after, created_at
  UNIQUE(legacy_export_row_id)
  UNIQUE(native_discovery_batch_id, native_row_ordinal)
  CHECK(exactly one of legacy_export_row_id or
        (native_discovery_batch_id and native_row_ordinal) is present)
  CHECK(run_identity_quality in real, batch_synthetic, row_synthetic, unknown)
  CHECK(run_identity_quality = real iff sourcing_run_id is present)
  FOREIGN KEY(sourcing_run_id, source_generation, source_system)
    REFERENCES sourcing_runs(id, source_generation, source_system)

weekly_reporting_periods
  id, period_key, iso_anchor_key, calendar_week_label_nullable,
  calendar_week_label_status, week_label_contract_version_nullable,
  week_anchor_monday_kst, event_start_kst,
  event_end_exclusive_kst, timezone
  UNIQUE(period_key)

source_watermarks
  id, source_kind, table_name, ordering_column,
  lower_bound_nullable, upper_bound_nullable, cursor_nullable,
  collected_as_of_at, row_count, query_digest_sha256,
  status, reason_nullable, evidence_sha256, created_at

metric_source_requirements
  metric_contract_version, metric_key, source_kind, table_name,
  required_completeness, created_at
  UNIQUE(metric_contract_version, metric_key, source_kind, table_name)

weekly_discovery_source_coverage
  weekly_snapshot_id, source_generation, source_system,
  status, completeness, accepted_count_nullable,
  rejected_count_nullable, quarantined_count_nullable,
  raw_discovery_count_nullable, source_unique_count_nullable,
  real_run_count_nullable, position_count_nullable,
  source_watermark_id, reason_nullable
  UNIQUE(weekly_snapshot_id, source_generation, source_system)

weekly_snapshots
  id, weekly_reporting_period_id, revision, meeting_instance_start_kst,
  as_of_at, generated_at, metric_contract_version,
  query_digest_sha256, payload_sha256, payload_json, provenance_json,
  supersedes_snapshot_id_nullable
  UNIQUE(weekly_reporting_period_id, revision)

weekly_snapshot_watermarks
  weekly_snapshot_id, source_watermark_id
  UNIQUE(weekly_snapshot_id, source_watermark_id)
~~~

→ 본문 추출·선택 사건, 검토, 접근 기록, 삭제 사건, 상태 사건, 쓰기 시도, 재조회, legacy row, 후보 발견 사실, source watermark, weekly snapshot은 UPDATE와 DELETE를 앱 역할에서 금지한다. 수정은 새 행으로만 표현한다. active selection과 current_state만 읽기 성능을 위한 현재값이며 같은 transaction의 최신 사건과 다르면 저장을 거부한다.

PII를 불변 원장 행 안에 직접 넣지 않는다. 원장 표는 무작위 `pii_payload_refs.id`만 보존하고 실제 ciphertext/object URI는 `pii_payload_blobs`에 둔다. 앱 역할은 blob을 UPDATE·DELETE할 수 없다. 별도 retention 역할은 만료·정책·승인자를 검사하는 `purge_pii_payload(payload_ref_id, policy_version)` procedure만 실행할 수 있다. procedure는 object storage 삭제와 암호화 data key 파기를 확인한 뒤 blob 행을 삭제하고 lifecycle/deletion event를 덧붙인다. 원장 ref에는 plaintext HMAC을 두지 않으며 payload 없는 tombstone만 남는다. 실제 payload가 계속 복호화 가능하거나 URI만 null 처리한 경우 삭제 성공이 아니다.

Gmail mailbox 주소, provider message id, thread id는 불변 `gmail_messages` 행에 평문으로 두지 않는다. 주소는 runtime config에서 `gmail_source_mailboxes`의 HMAC과 대조하고, provider id 묶음은 `provider_metadata_payload_ref_id`가 가리키는 암호화 payload에 둔다. 수집 중복 조회는 기간 제한이 있는 `gmail_message_lookup_keys`를 사용한다. derived identifier 만료 시 lookup key를 retention procedure로 제거하고 key version을 더 이상 비교에 쓰지 못하게 해야 하며, AC는 purge 뒤 provider message를 id로 재조회할 수 없음을 증명한다.

`business_object_keys`, body HMAC, candidate source key처럼 중복 방지에 쓰는 파생 식별자는 익명 자료가 아니라 통제 대상 pseudonymous data다. retention policy의 `derived_identifier_days`와 key version 폐기 시각을 적용하고, 만료 뒤 compare API가 그 key version을 쓰지 못해야 한다. 더 오래 보존하려면 오너가 목적·기간을 정책에 명시해야 하며 기본 무기한 보존은 금지한다.

key state는 `ACTIVE -> VERIFY_ONLY -> RETIRED -> DESTROYED` 단방향이다. purpose마다 신규 지문을 쓰는 ACTIVE key는 정확히 하나여야 한다. claim·compare·encrypt procedure는 key 표를 확인하고 ACTIVE만 새 write에, ACTIVE+VERIFY_ONLY만 과거 대조에 쓴다. RETIRED·DESTROYED key 사용, ACTIVE 0개/복수개, state event와 projection 불일치는 DB가 거부한다. `DESTROYED`는 key provider 영수증 없이는 기록할 수 없다.

`claim_business_object(...)` DB procedure만 business object와 key를 만들 수 있다. 활성 HMAC key version 각각으로 지문을 계산하고 transaction advisory lock을 잡아 구·신 key 어느 쪽에서도 기존 object가 없는 경우에만 object를 하나 만든다. key rotation은 `business_object_keys`에 새 행을 추가하며 과거 key 행을 덮어쓰지 않는다.

current_state는 빠른 조회용 복사값이다. 같은 transaction에서 추가된 가장 최신 상태 사건과 일치하지 않으면 commit을 실패시킨다. `gmail_body_active_selections`도 같은 방식으로 최신 selection event와 extraction을 정확히 가리켜야 한다.

`create_weekly_snapshot(...)` DB procedure는 metric contract의 `metric_source_requirements`와 제공된 typed watermark 집합을 대조한다. required source가 하나라도 빠지거나 table/order 의미가 다르면 snapshot을 만들지 않는다. 미수집 source도 watermark 행 자체는 `status=NOT_RUN`, `row_count=0`, reason과 evidence를 가져야 하며 누락으로 표현하지 않는다.

같은 procedure는 `(v4|v5|v6) × (aisearch|humansearch)` 여섯 source pair의 coverage 행을 정확히 하나씩 요구한다. export나 native adapter가 없으면 숫자를 0으로 만들지 않고 nullable count + `status=NOT_RUN` + reason을 저장한다. 실제로 0건임을 증명한 complete manifest/watermark가 있을 때만 `status=PASS`, count=0이다.

## 15. ClickUp 중복 방지·쓰기 계약

추천 task:

- list id 901814621142
- status 고객사추천
- title: 고객사, 포지션 - 후보자
- description: 추출한 업무 본문만

포지션 task:

- list id 901814621569
- status: 분류 결과. UNCLASSIFIED면 scraped
- title: [포지션]고객사, 포지션
- description: 추출한 업무 본문만

title의 고객사·포지션·후보자는 원문 표시값에서 NFKC와 공백만 정리하며 존칭을 새로 넣거나 빼지 않는다. description readback 비교는 줄끝과 줄 끝 공백만 정리한 뒤 sha256을 계산한다.

ClickUp 기존 task 확인은 열린 task와 닫힌 task를 포함해 모든 page를 끝까지 읽는다. 한 page라도 실패하면 기존 항목이 없다고 판정하지 않는다. 목록 지문은 list id, 정렬된 status 이름·type, 정렬된 custom field 이름·type의 canonical JSON sha256이다. 쓰기 직전에 다시 계산한 지문이 계약과 다르면 POST·PUT을 호출하지 않는다.

업무 대상 확보:

~~~text
1. 모든 활성 HMAC key version으로 business key를 계산한다.
2. claim_business_object(...)가 지문별 transaction advisory lock을 정렬 순서로 잡는다.
3. business_object_keys의 구·신 key를 모두 조회해 기존 object 하나를 반환하거나 새 object 하나를 만든다.
4. 같은 transaction에서 확보한 business object를 잠근다.
5. mail_business_links를 추가한다.
6. clickup_registration_targets를 INSERT ON CONFLICT.
7. `claim_clickup_write_lease(registration_target_id, approval_id)`가 승인과 target을 검증한다.
8. procedure가 registration target을 잠그고 lease_epoch을 1 올린 뒤, 미해제 lease가 없을 때만 lease를 만든다.
9. 같은 transaction에서 그 target의 유일한 clickup_write_attempt를 선기록하고 approval consumption event를 추가한다.
~~~

→ 서로 다른 Gmail message 두 건이 동시에 같은 추천을 처리해도 business object 1개, registration target 1개, ClickUp POST 최대 1회여야 한다.

메일 처리 상태와 ClickUp 등록 상태를 섞지 않는다.

~~~text
mail:
  DISCOVERED -> PARSED -> PRIMARY_LINKED
  PARSED -> DUPLICATE_LINKED
  DISCOVERED|PARSED -> MANUAL_REVIEW
  any nonterminal -> FAILED

clickup registration target:
  INTENT_RECORDED -> PREWRITE_READBACK
  -> WRITE_LEASED -> WRITE_STARTED
  -> RESPONSE_RECEIVED
  -> POSTWRITE_READBACK_VERIFIED
  -> COUNTABLE

WRITE_STARTED -> UNKNOWN_OUTCOME
UNKNOWN_OUTCOME -> RECONCILING
RECONCILING -> POSTWRITE_READBACK_VERIFIED
RECONCILING -> MANUAL_REVIEW
any nonterminal -> FAILED
~~~

→ 메일 결과는 mail_business_links 또는 mail_processing_reviews에 남고, 외부 쓰기 상태만 clickup_registration_state_events에 남는다. 상태 사건의 sequence_no는 직전 값보다 정확히 1 커야 하며 from_state가 현재 projection과 다르면 저장을 거부한다. 요청을 보냈다는 이유만으로 COUNTABLE로 가지 않는다.

POST adapter는 자동 HTTP 재시도를 끈다. claim procedure는 256-bit random lease token을 호출자에게 한 번만 돌려주고 DB에는 SHA-256 hash만 저장한다. raw token은 attempt·event·audit·일반 log에 남기지 않는다. network call 직전에 `registration_target_id + lease_epoch + hash(lease token)`이 현재 미해제 lease와 일치하고 만료 전인지 DB에서 다시 확인한다. `clickup_write_attempts.registration_target_id`의 고유 제약 때문에 다른 idempotency key나 새 lease로 두 번째 POST intent를 만들 수 없다. lease가 만료되거나 process가 죽으면 새 lease는 POST가 아니라 RECONCILING readback에만 쓸 수 있다. fencing token이 맞지 않는 worker는 어떤 외부 쓰기도 호출하지 않는다.

앱 역할은 approval, lease, write attempt 표에 직접 INSERT·UPDATE하지 못하고 위 procedure만 실행한다. procedure는 한 transaction에서 approval이 active·미만료·미소비인지, approval의 business object가 registration target의 business object와 같은지, approval의 mail record가 그 business object에 실제 연결됐는지 검사한다. 하나라도 다르면 approval을 소비하지 않고 lease·attempt도 만들지 않는다. 성공할 때만 approval state/consumed_at projection과 `live_write_approval_events`를 함께 기록한다.

쓰기 승인:

~~~ts
type LiveWriteApproval = {
  approvalId: string;
  ownerAdminUserId: string;
  approvedScope: "one_clickup_task";
  targetMailMessageRecordId: string;
  targetBusinessObjectId: string;
  expiresAt: string;
  issuedAt: string;
};
~~~

→ 승인값은 한 업무 대상과 만료시각에 묶인다. Phase 0~3 빌드에서는 write adapter가 구조적으로 비활성화되어 승인값을 넣어도 POST·PUT이 불가능해야 한다.

응답 유실:

1. WRITE_STARTED 뒤 응답을 받지 못하면 UNKNOWN_OUTCOME을 추가한다.
2. 즉시 재시도하지 않는다.
3. 결정론적 title을 같은 business parser로 읽고 body 지문까지 비교해 ClickUp을 재조회한다.
4. 정확히 한 task만 맞으면 연결하고 readback을 남긴다.
5. 0개 또는 2개 이상이면 MANUAL_REVIEW다. 자동 POST를 다시 하지 않는다.

현재 두 ClickUp 목록은 custom field가 비어 있으므로 원격 idempotency marker가 있다고 가정하지 않는다.

## 16. 과거 AI Search·Human Search 반출 계약

새 제품은 과거 프로그램이나 DB를 읽지 않고 다음 envelope와 JSONL row만 받는다.

~~~ts
type CandidateDiscoveryExportEnvelopeV1 = {
  schemaVersion: "candidate-discovery-export/v1";
  sourceGeneration: "v4" | "v5" | "v6";
  sourceSystem: "aisearch" | "humansearch";
  exportedAt: string;
  rowCount: number;
  rowsSha256: string;
  rowsUri: string;
};

type CandidateDiscoveryExportRowV1 = {
  sourceRowOrdinal: number;
  sourceRecordId: string | null;
  sourceRunId: string | null;
  runIdentityQuality: "real" | "batch_synthetic" | "row_synthetic" | "unknown";
  triggeredAt: string | null;
  completedAt: string | null;
  discoveredAt: string | null;
  positionSourceId: string | null;
  positionTitle: string | null;
  channel: string;
  candidateIdentity: {
    type: "profile_url" | "platform_id" | "email" | "unknown";
    value: string | null;
  };
  rawPayload: Record<string, unknown>;
};
~~~

→ envelope rowCount는 JSONL 실제 행 수와 같아야 한다. sourceRecordId가 같아도 batch와 ordinal이 다르면 서로 다른 원자료 행으로 보존한다.

`sourceRunId`가 실제 시스템이 낸 값일 때만 `runIdentityQuality=real`이고 `sourcing_runs`에 연결한다. 없는 run id를 행마다 만들어 실행 수를 부풀리거나 batch id를 실제 run처럼 세지 않는다. synthetic·unknown 행은 그대로 보존하되 실행 수에서 제외하고 별도 품질 지표로 보고한다.

반출 파일은 git에 넣지 않는다. 접근 제한 저장소의 URI, 전체 지문, 행별 지문만 v6 DB에 둔다. legacy와 v6 native discovery 모두 raw payload를 `pii_payload_refs` + `pii_payload_blobs`로 저장해 URI·ciphertext 지문·보관정책·삭제 예정일을 동일하게 적용한다. native fact도 raw URI 없는 hash-only 행을 허용하지 않는다. import 결과는 ACCEPTED, REJECTED, QUARANTINED 중 하나이며 다음이 항상 성립해야 한다.

~~~text
row_count = accepted_count + rejected_count + quarantined_count
~~~

→ 사건 시각이 없으면 imported_at으로 과거 주차를 꾸미지 않고 QUARANTINED로 둔다. 반출 원자료 행 수와 주간 후보 발견 수를 섞지 않는다. 주간 원시 발견 건수는 검증을 통과해 candidate discovery fact가 된 행을 중복 제거 없이 세고, 고유 후보 수만 파생 지문을 distinct로 센다.

## 17. 주간 snapshot과 지표 계약

회의용 기본 snapshot은 회의 시작시각을 as_of_at으로 사용한다. 각 source watermark는 그 snapshot에 포함할 마지막 원자료 행·상태 사건·수집 cursor를 고정한다. 나중에 들어온 자료나 상태 변경은 기존 snapshot을 고치지 않고 더 높은 watermark와 새 as_of_at을 가진 revision을 하나 더 만든다.

모든 지표 응답:

~~~ts
type MetricResult = {
  value: number | null;
  status: "PASS" | "FAIL" | "NOT_RUN";
  completeness: "COMPLETE" | "PARTIAL" | "NONE";
  reason: string | null;
  contractVersion: string;
  computedAt: string;
  provenance: Array<{
    source: string;
    rowCount: number;
    watermarkId: string;
    drilldownHref: string;
  }>;
};
~~~

→ 자료를 읽지 못하면 value는 0이 아니라 null이다. 일부 page만 읽었으면 `status=FAIL`, `completeness=PARTIAL`이며 화면에서 숫자처럼 정상 표시하지 않는다. 저장소 SOT의 판정은 PASS·FAIL·NOT_RUN 세 상태만 쓴다.

지표:

~~~text
recommendation_mail_events
  = recommendation qualified Gmail messages by sent_at

recommendation_business_unique
  = distinct recommendation business objects linked from window mail events

recommendation_clickup_verified
  = recommendation registration targets linked from qualified recommendation
    mail events inside the event window, whose POSTWRITE_READBACK_VERIFIED
    transition occurred at or before as_of_at and inside the state-event watermark

recommendation_duplicate_linked
  = mail links marked DUPLICATE_LINKED by mail sent_at

recommendation_manual_review / recommendation_failed
  = outcomes from mail_processing_reviews by mail sent_at and as_of_at

position_mail_events
  = position qualified Gmail messages by sent_at

position_clickup_verified / position_unclassified / position_failed
  = position registration events and processing reviews by linked mail sent_at and as_of_at

sourcing_import_rows / sourcing_import_rejected / sourcing_import_quarantined
  = legacy export row outcomes, reported separately from weekly discoveries

sourcing_raw_discoveries
  = candidate_discovery_facts by discovered_at without distinct

sourcing_source_unique_candidates
  = distinct candidate_source_key_hmac inside each source system

sourcing_runs
  = distinct real source run ids whose triggered_at is in the event window

sourcing_run_identity_non_real_rows
  = discovery rows whose run identity quality is batch_synthetic,
    row_synthetic, or unknown; never included in sourcing_runs

sourcing_positions
  = distinct position source ids among discoveries in the event window
~~~

→ 출처를 넘는 전사 고유 후보 수는 신원 연결 계약이 생기기 전까지 NOT_RUN이다. 같은 사람처럼 보여도 원자료 행을 삭제하거나 합치지 않는다.

snapshot query는 사건 시각의 주간 반개방 구간과 snapshot에 연결된 source별 typed watermark를 모두 적용한다. 각 watermark는 `table_name + ordering_column + lower/upper bound + row_count + query_digest` 의미를 가져야 하며 Gmail cursor, ClickUp state sequence, legacy ordinal, native fact id를 하나의 모호한 숫자로 섞지 않는다. 상태 지표는 occurred_at이 as_of_at 이하인 상태 사건 중 해당 표의 upper bound 안의 것만 사용한다.

과거 snapshot 재현 시험은 같은 as_of_at, metric version, query digest, source watermarks를 넣었을 때 payload 지문이 byte-for-byte 같아야 한다.

## 18. 관리자 API·화면 계약

라우트:

- GET /api/admin/weekly-snapshots/{periodKey}?revision=latest
- GET /api/admin/weekly-snapshots/{periodKey}/metrics/{metricKey}/rows
- GET /admin/dashboard

응답은 contracts/admin-weekly-dashboard/weekly-snapshot-v1.schema.json으로 검사한다. 알 수 없는 metric key, 잘못된 period key, 권한 없음, source NOT_RUN을 서로 다른 오류로 반환한다.

HTTP 응답은 private, no-store이며 서버 로그에 본문·제목·메일주소·후보 이름을 남기지 않는다.

권한:

- viewer는 합계·상태·익명화된 provenance만 읽고 본문·고객사·후보자 drilldown은 읽지 못한다.
- operator는 업무상 필요한 drilldown과 manual review를 처리할 수 있지만 사용자 관리·보관 정책·운영 쓰기 승인은 못 한다.
- owner는 사용자·정책·승인을 관리할 수 있다.
- 민감 drilldown 열람, 본문 복호화, 정책 변경, 승인 소비는 access_audit_events에 남긴다.
- 비활성 사용자와 역할 없는 사용자는 페이지와 API 모두 403이며, UI에서 숨기는 것만으로 권한을 대신하지 않는다.

화면 정보 순서:

1. 관리자 공통 내비게이션과 주간 브리프 제목
2. 회의 주차·실적 기간·revision 선택
3. 전체 자료 상태와 마지막 성공·시도 시각
4. 추천 카드와 원자료 drilldown
5. 포지션 카드와 분류 대기 drilldown
6. AI/Human Search 출처별 원시 발견·고유·실행·포지션 수
7. FAIL·NOT_RUN 이유와 COMPLETE·PARTIAL·NONE 완전성

기존 화면의 iframe, 정적 HTML, CSS를 복사하지 않는다. 인증된 reference screenshot이 없으면 접근성 있는 새 골격과 정보 구조까지만 PASS이며 시각 동일은 `BLOCKED_UI_REFERENCE/NOT_RUN`이다. 이 blocker는 Phase 0~4의 데이터·API 구현을 막지 않고 Phase 5의 visual parity PASS만 막는다.

접근성:

- 키보드로 주차·revision·drilldown 이동 가능
- 상태를 색만으로 구분하지 않음
- 표 머리글과 카드 제목을 읽기 도구가 구분
- 좁은 화면에서 숫자와 상태 이유가 잘리지 않음

## 19. 구현 Phase와 진입·종료 조건

각 Phase는 한 인수조건, 한 worktree, 한 task 브랜치, 한 PR을 원칙으로 더 작게 쪼갠다. Phase 이름 하나가 PR 하나라는 뜻이 아니다.

### Phase 0 — 저장소 제품 기반

구현:

- 고정 구조와 버전의 apps/admin 빈 제품
- root workspace와 lockfile
- 로컬·pre-push·CI에 같은 admin foundation 검사 연결
- 정본 명령표와 mechanism registry 갱신

종료:

- 깨끗한 checkout에서 pnpm install --frozen-lockfile, lint, typecheck, unit test, build가 실제 대상 수를 출력하고 통과
- `.node-version`, `engines.node`, `packageManager`, package.json, lockfile이 고정 버전과 정확히 일치하며 package 해석 실패는 `VERSION_CONTRACT_FAIL`이다.
- 새 acceptance script가 로컬과 CI 양쪽에 등록됨
- 검사 명령을 고장 내면 acceptance가 RED가 됨

### Phase 1 — 순수 도메인 계약

구현:

- 주간 경계, Gmail 판정, 제목 parser, 본문 extractor, taxonomy
- 합성 MIME와 속성 기반 시험
- runtime config와 네 JSON Schema

종료:

- 네트워크 없이 합성 시험 통과
- sangmokang 구조 6건을 합성 fixture로 재현
- kcs·julian·rogan 실제 표본은 SAMPLE_SCOPE_LIMITATION으로 남음

### Phase 2 — PostgreSQL 원장

진입:

- PostgreSQL 17.11, Prisma 7.9.1, Vitest 4.1.10은 이 문서 고정값과 일치
- 보관 정책이 없어도 synthetic data migration 시험은 가능

구현:

- 모든 표·제약·뒤에만 덧붙이는 권한
- illegal state transition 차단
- 업무 대상 동시 dedupe
- legacy importer dry-run
- v4/v5/v6 × aisearch/humansearch 여섯 source pair 합성 fixture와 coverage matrix
- snapshot as-of 재현

종료:

- digest가 잠긴 `postgres:17.11-alpine` Docker Compose service에서 migration up/down 정책과 integration test 통과
- 여섯 source pair 모두 합성 import/count가 통과하고 실제 export가 없는 pair는 NOT_RUN으로 남음
- 서로 다른 message 두 건의 같은 business key 동시 처리에서 task target 1개
- UPDATE·DELETE 금지 표의 mutation이 DB에서 실패

### Phase 3 — 읽기 전용 연결과 그림자 화면

진입:

- 합성 자료와 명시적 `--meeting-start`만 쓰는 그림자 화면은 Phase 2 통과만 요구한다.
- 실제 한 주 Gmail·ClickUp read-only dry-run은 보관 정책, 접근 역할, 삭제 명령, Gmail 읽기 권한, ClickUp token을 요구한다.
- Calendar 권한은 실제 회의 자동 탐색에만 필요하다. 명시적 `--meeting-start`를 쓰면 Calendar 수집 상태는 NOT_RUN으로 남긴다.

구현:

- 네 mailbox 읽기 전용 수집
- Calendar 실제 인스턴스 또는 명시적 meeting start
- ClickUp 목록·기존 task 읽기와 schema fingerprint
- 제공된 v4/v5 export import와 v6 aisearch/humansearch native discovery adapter read-only 수집
- weekly snapshot API와 별도 시험 주소 화면

종료:

- 실제 한 주를 dry-run으로 재현
- mailbox별 qualified 표본 수, 0건이면 선별 전 후보 수와 제외 reason code 분포, text/plain·text/html·quote·signature·attachment MIME 분포를 개인정보 없이 기록
- 여섯 discovery source pair 각각 accepted/rejected/quarantined/raw/unique/real-run/position count 또는 NOT_RUN reason을 기록
- 모든 카드가 원자료 행과 watermark로 내려감
- 외부 source 실패가 0으로 보이지 않음
- ClickUp POST·PUT 호출 수 0

### Phase 4 — 제한된 ClickUp 1건

진입:

- 유효한 LiveWriteApproval 1건
- 오너가 dry-run 대상·title·description·상태를 확인

구현:

- intent, 한 번의 POST, readback
- 응답 유실 reconciliation

종료:

- 승인 대상 한 건만 READBACK_VERIFIED
- 다른 모든 write 호출 0
- 중복 task 0

### Phase 5 — 시각 승인과 운영 전환

진입:

- 인증된 기존·새 화면 캡처
- 운영 배포 대상과 rollback 명령
- 오너의 별도 전환 승인

종료:

- visual verdict와 숫자 대조
- 운영 주소 전환 후 읽기 smoke
- 기존 서비스 삭제 없음

→ 인증된 기존 화면 캡처가 없으면 Phase 5는 `BLOCKED_UI_REFERENCE/NOT_RUN`이며 운영 전환으로 넘어가지 않는다.

## 20. 기계 인수 기준

1. AC-01: 형제 저장소 없이 clean checkout에서 고정 Node·pnpm으로 admin install, ESLint, typecheck, test, build, start가 된다.
2. AC-02: 새 admin acceptance가 pre-push 자동 수집과 CI 고정 목록 양쪽에서 실제 실행된다.
3. AC-03: runtime dependency graph와 build output에 v4·v5 경로·module·asset·DB endpoint가 0건이다.
4. AC-04: 2026-08-17과 같은 주 2026-08-18 회의가 모두 `2026-08-09--2026-08-15`와 정확한 일~토 반개방 구간을 반환한다.
5. AC-05: Google Calendar 표시 규칙이 없으면 week label은 null+NOT_RUN이고, 승인된 연말 경계 예시 2건을 통과해야만 라벨이 PASS다.
6. AC-06: Re/Fwd, 앞 공백, 내부 수신자뿐, 받은편지함, 기간 밖 메시지와 본문에만 태그가 있는 메시지는 모두 제외된다.
7. AC-07: 합성 MIME에서 quote, signature, attachment, 중복 alternative가 ClickUp body에 0글자 들어간다.
8. AC-08: extractor v1과 v2가 모두 남고 이미 등록된 task에는 change proposal만 생긴다.
9. AC-09: 서로 다른 Gmail message 두 건이 같은 business key를 동시에 처리해도 business object, registration target, 활성 lease, write attempt가 각각 1개다. 서로 다른 idempotency key로 attempt를 만들면 DB가 거부한다.
10. AC-10: POST 성공 뒤 응답 유실 시 재조회 전 두 번째 POST는 0회다.
11. AC-11: ClickUp 재조회가 0건 또는 복수건이면 MANUAL_REVIEW이며 blind retry는 0회다.
12. AC-12: ClickUp 상태 fingerprint가 다르면 write adapter 호출 수가 0이다.
13. AC-13: 일반 Engineer만 있는 포지션은 UNCLASSIFIED이며 scraped 외 직무로 자동 확정되지 않는다.
14. AC-14: legacy export는 동일 sourceRecordId 행도 batch+ordinal별로 모두 보존한다.
15. AC-15: row_count는 accepted+rejected+quarantined와 같다.
16. AC-16: 같은 as_of와 source별 typed watermarks로 snapshot을 재계산하면 payload sha256이 같다. 한 source의 upper bound나 query digest를 바꾸면 payload가 달라지거나 계약 오류가 나고 required watermark를 빼면 snapshot 생성이 실패한다.
17. AC-17: source 실패는 metric value null과 FAIL·NOT_RUN 이유로 표시되며 0이 아니다. 부분 수집은 verdict FAIL, completeness PARTIAL이다.
18. AC-18: API의 모든 metric은 contract version, computed time, typed watermark, row count, drilldown link를 가진다.
19. AC-19: owner approval이 없으면 빌드 산출물의 ClickUp POST·PUT 경로가 구조적으로 비활성화된다.
20. AC-20: 인증된 reference screenshot이 없으면 visual parity는 `BLOCKED_UI_REFERENCE/NOT_RUN`이고 Phase 5 전환이 차단된다.
21. AC-21: 비밀·메일 원문·메일주소·후보 개인정보가 git과 일반 로그에서 0건이다.
22. AC-22: viewer는 집계만 읽고 민감 drilldown은 403이며, operator와 owner의 민감 열람은 audit event를 남긴다. 변조·만료 OIDC token과 비활성 user session은 거부된다.
23. AC-23: 만료된 실제 payload는 retention procedure가 object+ciphertext/data key와 Gmail provider lookup key를 제거하고 lifecycle/deletion event를 남긴다. purge 뒤 복호화와 provider-id 재조회가 모두 실패하고 불변 원장은 무작위 tombstone만 남는다.
24. AC-24: ClickUp description readback은 업무 본문 외 메타데이터 0글자와 canonical body 지문 일치를 증명한다.
25. AC-25: ClickUp 기존 task page 하나를 실패시키면 “기존 task 없음”이 아니라 verdict FAIL, completeness PARTIAL로 쓰기가 차단된다.
26. AC-26: registration target current_state와 최신 sequence state event가 다르면 transaction이 실패한다.
27. AC-27: active body selection이 최신 selection event·extraction과 다르면 transaction이 실패한다.
28. AC-28: legacy와 native candidate fact 모두 유효한 raw payload ref·URI·policy·purge_after를 가지며 hash-only raw fact는 DB가 거부한다.
29. AC-29: HMAC key rotation 중 구·신 지문이 같은 business object에 연결되고 새 key만 사용한 중복 object 생성은 거부된다.
30. AC-30: real run id만 sourcing_runs에 포함되고 synthetic·unknown identity 행은 별도 품질 수치로만 보고된다.
31. AC-31: Phase 3 첫 read-only 실행은 네 mailbox 각각의 qualified 수·0건 이유·MIME 분포와 수집 완전성을 남기며 계정 하나라도 증거가 없으면 전체 PASS가 아니다.
32. AC-32: 최초 owner bootstrap은 한 번만 성공하고 첫 OIDC subject 결합 뒤 재실행·두 번째 pending owner grant가 DB에서 거부된다.
33. AC-33: v4/v5/v6 × aisearch/humansearch 여섯 source pair가 snapshot마다 정확히 한 coverage 행을 가지며, 미제공 source는 nullable count+NOT_RUN이다. 증명된 empty manifest만 PASS+0을 허용한다.
34. AC-34: approval의 mail/business object와 다른 registration target으로 lease를 청구하면 approval 소비, lease, attempt, 외부 호출이 모두 0이다.
35. AC-35: derived identifier 보관기간이 끝난 key version은 compare·dedupe API에서 거부되고 key 폐기 event/receipt가 없으면 purge PASS가 아니다.
36. AC-36: Google OIDC의 wrong issuer/audience/azp, nonce 불일치, state replay, exp 만료, email_verified=false, hosted domain 불일치 각각이 401이고 session·user binding을 만들지 않는다.
37. AC-37: GET이 아닌 admin API는 wrong Origin/Host, CSRF 누락·재사용, 부족한 role을 각각 403으로 막고 성공한 mutation과 거부된 민감 시도 모두 audit evidence를 남긴다.
38. AC-38: purpose마다 ACTIVE write key는 정확히 하나다. ACTIVE 0개/복수개, RETIRED·DESTROYED key 사용, key state projection/event 불일치를 DB가 거부한다.
39. AC-39: `bash scripts/scan-data-exposure.sh admin`이 build/test/log root 각각의 canary mutation을 잡고, target root·file 0건이면 exit 2+NOT_RUN이다. 같은 명령이 acceptance·pre-push·CI·두 SOT 명부에서 실제 실행된다.
40. AC-40: DB·receipt·일반 log 어디에도 raw ClickUp lease token이 남지 않고 hash가 다른 token의 외부 호출 수는 0이다.

## 21. 가짜 합격을 깨는 시험

- business object key 고유 제약이나 claim lock을 제거하면 AC-09가 RED가 되어야 한다.
- 서로 다른 message id를 같은 business key로 동시에 넣어 task target 2개가 생기면 실패해야 한다.
- 같은 registration target에 서로 다른 idempotency key 두 개로 write attempt를 넣으면 두 번째 INSERT가 실패해야 한다.
- 만료된 fencing token을 가진 worker가 POST adapter를 부르면 network spy 호출 수가 0이어야 한다.
- raw lease token을 attempt나 log에 한 번 기록하면 secret/data exposure 시험이 실패해야 한다.
- 추출판 INSERT를 UPDATE로 바꾸면 AC-08이 실패해야 한다.
- active body selection을 최신 selection event와 다른 extraction으로 바꾸면 transaction이 실패해야 한다.
- UNKNOWN_OUTCOME에서 readback 없이 WRITE_STARTED로 되돌리면 DB가 거부해야 한다.
- source watermark를 FAIL로 바꾸면 화면이 0을 표시하는 구현이 실패해야 한다.
- snapshot query에서 as_of 조건 또는 source-specific upper bound를 빼면 과거 payload 재현 시험이 실패해야 한다.
- required source watermark 하나를 빼면 snapshot 생성 procedure가 실패해야 한다.
- legacy importer를 sourceRecordId distinct로 바꾸면 행 수 대조가 실패해야 한다.
- Gmail 두 번째 page를 실패시키면 첫 page 수만 정상 숫자로 표시하는 구현이 실패해야 한다.
- ClickUp 상태 하나를 바꾸면 POST가 차단되어야 한다.
- v4 폴더를 보이지 않게 하면 build가 계속 통과해야 한다.
- reference screenshot을 빼면 시각 PASS가 NOT_RUN으로 바뀌어야 한다.
- 승인 대상과 다른 mail record id를 넣으면 write 호출이 0이어야 한다.
- viewer에게 operator drilldown URL을 직접 호출시키면 403과 audit outcome이 남아야 한다.
- retention policy version 없이 실제 data row를 넣으면 DB가 거부해야 한다.
- purge event만 넣고 payload blob/object를 남기면 AC-23이 실패해야 한다.
- Gmail provider lookup key를 남긴 채 payload만 지우면 AC-23이 실패해야 한다.
- native candidate fact의 raw payload ref 또는 URI를 빼면 AC-28이 실패해야 한다.
- synthetic run id를 real로 바꾸면 sourcing_runs와 품질 수치 시험이 실패해야 한다.
- 다른 source_generation/source_system의 real run에 fact를 연결하면 composite FK가 거부해야 한다.
- 여섯 discovery source pair 중 하나를 coverage에서 빼거나 미제공 pair를 PASS+0으로 바꾸면 AC-33이 실패해야 한다.
- Google Calendar 표시 계약 없이 ISO week를 화면 라벨로 반환하면 AC-05가 실패해야 한다.
- ClickUp description에 message id나 자동등록 문구 한 글자를 넣으면 AC-24가 실패해야 한다.
- state event sequence를 건너뛰거나 from_state를 바꾸면 DB가 거부해야 한다.
- approval의 business object 또는 mail link와 다른 target으로 lease를 청구하면 lease·attempt·외부 호출이 모두 0이어야 한다.
- key state event 없이 ACTIVE projection을 바꾸거나 같은 purpose ACTIVE key를 둘로 만들면 AC-38이 실패해야 한다.
- OIDC claims 검사를 하나씩 끄거나 admin mutation의 Origin·CSRF 검사를 빼면 AC-36/37이 실패해야 한다.
- admin artifact root 하나를 scanner에서 빼거나 CI 등록을 지우면 AC-39가 실패해야 한다.
- 실제 mailbox 주소 하나를 tracked runtime config나 문서 예시에 넣으면 AC-21이 실패해야 한다.

## 22. 검증·보고·중지 계약

각 AC에서 다음 순서를 지킨다.

1. 시작 검사와 기존 RED 수 기록
2. Phase goal 작성
3. 새 worktree와 task 브랜치 생성
4. 실패하는 인수 시험 작성
5. 최소 구현
6. 대상 시험, lint, typecheck, build, root 검증 실행
7. 비밀·개인정보·legacy dependency 검사
8. 외부 경계면 읽기 전용 smoke
9. Claude CLI 1차 적대검증
10. Codex가 Claude 증거를 재현하고 누락·과장을 재공격
11. goal 문서에 전체 명령·출력·해석을 보존
12. Phase 0~3과 일반 구현은 PR까지만 만들고 merge·배포·운영 쓰기를 중지한다. Phase 4/5는 이 문서와 별개의 오너 지시와 해당 진입조건이 있을 때 승인된 한 건/전환 범위만 실행하고, 그 밖의 write와 PR merge는 중지한다.

Claude 판정이 빈 출력, 서비스 거절, 한 줄 완료이면 PASS가 아니다. 한 번 표현을 줄여 재시도하고, 그래도 실패하면 CLAUDE_NOT_RUN을 남긴다. 외부 검증이 없음을 Codex 의견으로 바꾸어 쓰지 않는다.

완료 보고는 결론, 판단 근거, 증거 원문 순서로 쓴다. PASS, FAIL, NOT_RUN과 별도 completeness를 숨기지 않는다. 처리 대상 수가 0이면 성공이 아니라 NOT_RUN이다.

## 23. 현재 근거와 비범위

현재 근거:

- README.md:7 — v6는 제품 소스가 없는 부트스트랩이다.
- docs/sot/coding-principles.md — 실행 가능한 인수조건, 세 상태, 외부 쓰기 선기록·재조회, 코드 집계, 0건 가짜 합격 금지를 요구한다.
- docs/sot/verification-commands.md:43 — 새 acceptance는 CI와 명령표를 함께 갱신해야 한다.
- docs/sot/git-workflow.md:15-23 — 한 작업·한 worktree·한 인수조건·한 PR과 main 보호를 요구한다.
- Valuehire_v4 app/(admin)/admin/dashboard/page.tsx — 기존 화면은 iframe이므로 복사 대상이 아니다.
- Valuehire_v4 weekly brief 계산 — 월요일 시작이라 새 일~토 계약과 다르다.
- Gmail 읽기 전용 표본 — sangmokang 6건에서 HTML·plain 동시 존재, quote 4건, attachment 4건을 확인했다.
- ClickUp 읽기 전용 표본 — 추천 목표 status 고객사추천, 포지션 상태 목록, custom field 0개를 확인했다.
- npm registry 읽기 전용 확인 — 문서에 고정한 npm package가 모두 exact version으로 해석됐고 TypeScript 6.0.3은 현재 typescript-eslint의 `<6.1.0` peer 범위를 만족했다.
- 로컬 실행 기반 — Docker 29.4.0과 Docker Compose 5.1.2를 확인했다. PostgreSQL image digest는 Phase 2 구현 PR의 lockfile/compose evidence로 고정한다.
- 공식 기술 근거 — [Node release 상태](https://nodejs.org/en/about/previous-releases), [pnpm 11](https://pnpm.io/blog/releases/11.0), [Next.js 16 upgrade와 next lint 제거](https://nextjs.org/docs/app/guides/upgrading/version-16), [typescript-eslint 지원 범위](https://typescript-eslint.io/users/dependency-versions/), [Prisma system requirements](https://www.prisma.io/docs/orm/reference/system-requirements), [PostgreSQL 지원 버전](https://www.postgresql.org/support/versioning/).

이번 문서 작업 비범위:

- apps/admin 제품 코드와 dependency 설치
- 실제 Gmail·Calendar 자료 적재
- ClickUp task 생성·수정·이동
- 과거 후보 파일 실제 반출·적재
- 운영 화면 캡처 획득
- 운영 주소 변경, 배포, merge, 기존 서비스 삭제

## 24. 적대 검증 로그

### 24.1 Claude CLI 1차 — CLAUDE_NOT_RUN

첫 호출 원문:

~~~text
$ env -u ANTHROPIC_API_KEY claude -p < /Users/kangsangmo/Desktop/Valuehire_v6/worktrees/admin-weekly-dashboard-v6-goal-v2/docs/engineering/admin-weekly-dashboard-v6-replacement-review-request-2026-08-16.md
exit=1
API Error: Fable 5's safeguards flagged this message (https://www.anthropic.com/legal/aup). This sometimes happens with safe, normal conversations. Claude Code can't respond to this message with Fable 5.

Try rephrasing the request in a new session or change your model.

Learn more: https://support.claude.com/en/articles/15363606

Request ID: req_011Ce6WyBvvqz5E7uLM2whnw
Client.listTools() called but server does not advertise tools capability - returning empty list
~~~

→ 문서 결함 판정이 아니라 Claude 서비스 거절이다. VERDICT가 없으므로 PASS/FAIL 어느 쪽으로도 세지 않는다.

재시도 1 원문:

~~~text
$ env -u ANTHROPIC_API_KEY claude -p --model sonnet < /Users/kangsangmo/Desktop/Valuehire_v6/worktrees/admin-weekly-dashboard-v6-goal-v2/docs/engineering/admin-weekly-dashboard-v6-replacement-review-request-2026-08-16.md
output: Execution error
~~~

→ 출력 없이 대기하는 동안 대상 문서가 내부 보안 검토로 바뀌어, 오래된 파일을 판정하지 않도록 중단했다. 검증 판정이 아니다.

최종 재시도 원문:

~~~text
$ env -u ANTHROPIC_API_KEY claude -p --safe-mode --model sonnet --permission-mode dontAsk --tools "Read,Grep,Glob" --add-dir /Users/kangsangmo/Desktop/Valuehire_v6/worktrees/admin-weekly-dashboard-v6-goal-v2 --no-session-persistence < /Users/kangsangmo/Desktop/Valuehire_v6/worktrees/admin-weekly-dashboard-v6-goal-v2/docs/engineering/admin-weekly-dashboard-v6-replacement-review-request-2026-08-16.md
output after bounded wait and interrupt: Execution error
~~~

→ 사용자 설정·훅을 끄고 읽기 도구만 허용했지만 제한 시간 안에 본문이 한 글자도 오지 않았다. 따라서 외부 적대 검증 최종 상태는 `CLAUDE_NOT_RUN`이다.

### 24.2 Codex 2차 독립 재공격

Claude 판정 본문이 없어서 “Claude 결함 재현”은 NOT_RUN이다. 대신 서로 다른 네 검토면으로 최신 문서를 독립 재공격했다.

1. 요구사항 검토는 여섯 discovery source pair 미강제, Google 주차 FAIL 상태 누락, raw 제목과 NFKC 불일치를 찾았다. 여섯 coverage 행·PASS/FAIL/NOT_RUN·raw prefix fixture와 AC로 고쳤다.
2. 원장 검토는 approval-target 결속, payload 삭제, HMAC rotation, typed watermark, active body projection, run identity source 결속을 찾았다. DB procedure·erasable payload·key state·required source·composite FK·mutation AC로 고쳤고 최신 재검토 P0/P1은 0건이었다.
3. 보안 검토는 Gmail provider id 잔존, key lifecycle, Phase 권한 충돌, plaintext lease token, OIDC/CSRF 시험, admin artifact scan, tracked mailbox 주소 모순을 찾았다. 모두 schema/procedure/AC로 고쳤고 최신 재검토 P0/P1은 0건이었다.
4. 전체 계약 검토는 Phase 4/5 권한과 일반 PR 중지문 충돌을 찾았다. 별도 오너 지시와 Phase 진입조건만 예외 권한이 되도록 고쳤고 최신 재검토 P0/P1은 0건이었다.

→ 내부 검토는 모두 최신 파일을 다시 읽어 0건을 확인했다. 그러나 이는 다른 모델의 판정을 대신하지 않으므로 외부 검증 상태는 계속 CLAUDE_NOT_RUN이다.
