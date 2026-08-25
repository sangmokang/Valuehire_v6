# Repository Data Protection 후속 전체 검증 로그 — 2026-08-25

## 결론

구현 SHA `8945496f957a62d8d17a8bceafc3616fc5e38d22`의 로컬 기능·CI 등가·mutation 검사는 아래 원출력대로 통과했다. 그러나 Claude V1은 무출력/크레딧 문제로 `NOT_RUN`, P23은 원격 브랜치 부재로 `NOT_RUN`, 원본 dirty 기준은 외부 변경으로 불일치하므로 전체 완료와 병합 판정은 `REQUEST_CHANGES`다.

이 문서는 명령 출력을 재구성하거나 줄이지 않고 보존한다. 합성 fixture의 실제 개인정보 값과 역조회 원문 경로는 기록하지 않는다. `check-docs-sot.sh` 출력은 10개 정적 항목만 증명하며 repository-data-protection 완료 근거에서 제외한다.

## 원명령 전체 출력

### Strict principles

```text
TIMESTAMP_KST: 2026-08-25 23:44:12 KST
PWD: /private/tmp/valuehire-rdp-20260824.7e3kk1/worktree
HEAD: 8945496f957a62d8d17a8bceafc3616fc5e38d22
COMMAND: bash scripts/acceptance-principles-check.sh
VERDICT: PASS
SOT_LOAD: PASS docs/sot/coding-principles.md
LEDGER_LOAD: PASS docs/sot/principles.yaml
MECHANISMS: PASS 34/34 strict-contract-bindings
WIRING: PASS pre-push=1 ci=1
CHECKED: 34
EXIT: 0
```

→ 원명령 종료값은 0; 위 stdout/stderr 전체가 해당 판정의 직접 증거다.

### Limited docs SOT check

```text
TIMESTAMP_KST: 2026-08-25 23:44:13 KST
PWD: /private/tmp/valuehire-rdp-20260824.7e3kk1/worktree
HEAD: 8945496f957a62d8d17a8bceafc3616fc5e38d22
COMMAND: bash scripts/check-docs-sot.sh
PASS: docs/sot/INDEX.md 존재, 1366바이트 (<=20000)
PASS: docs/sot/coding-principles.md 존재, 19184바이트 (<=20000)
PASS: docs/sot/hook-contracts.md 존재, 4455바이트 (<=20000)
PASS: docs/sot/git-workflow.md 존재, 2225바이트 (<=20000)
PASS: docs/sot/verification-commands.md 존재, 11699바이트 (<=20000)
PASS: hooks/pre-commit 가 docs/sot/hook-contracts.md 를 계약으로 참조
PASS: hooks/pre-push 가 docs/sot/hook-contracts.md 를 계약으로 참조
PASS: scripts/install-hooks.sh 가 docs/sot/hook-contracts.md 를 계약으로 참조
PASS: scripts/session-status.sh 가 docs/sot/hook-contracts.md 를 계약으로 참조
PASS: scripts/acceptance-0-7.sh 가 docs/sot/hook-contracts.md 를 계약으로 참조
OK: docs/sot 재구성 AC 전부 충족
EXIT: 0
```

→ 이 PASS는 필수 SOT 파일 5개와 훅 계약 참조 5개만 증명한다. catalog·surface coverage 또는 본 기능 완료 근거가 아니다.

### Principles mutations via CI wrapper

```text
TIMESTAMP_KST: 2026-08-25 23:44:13 KST
PWD: /private/tmp/valuehire-rdp-20260824.7e3kk1/worktree
HEAD: 8945496f957a62d8d17a8bceafc3616fc5e38d22
COMMAND: bash scripts/verify/run-acceptance.sh scripts/acceptance-principles-mutations.sh
PASS: FIXTURE-NORMAL 정상 fixture — PASS (exit=0)
PASS: C1 principles.yaml 삭제 — FAIL (exit=1)
PASS: C2 coding-principles.md 삭제 — FAIL (exit=1)
PASS: C3 YAML 문법 오류 — FAIL (exit=1)
PASS: C3-EMPTY-LEDGER principles.yaml 빈 파일 — FAIL (exit=1)
PASS: C3-EMPTY-SOT coding-principles.md 빈 파일 — FAIL (exit=1)
PASS: C4 원칙 ID 하나 삭제 — FAIL (exit=1)
PASS: C5 중복 ID 추가 — FAIL (exit=1)
PASS: C5-UNKNOWN 알 수 없는 ID — FAIL (exit=1)
PASS: C5-PRINCIPLE 정본과 원칙 문구 불일치 — FAIL (exit=1)
PASS: C5-EMPTY-EXPECTED 빈 mechanism_expected — FAIL (exit=1)
PASS: C5-EMPTY-FOUND 빈 mechanism_found — FAIL (exit=1)
PASS: C6 mechanism 경로 미존재 — FAIL (exit=1)
PASS: C6-CHECK mechanism 검사기 미존재 — FAIL (exit=1)
PASS: C6-STAGES 잘못된 stages 구조 — FAIL (exit=1)
PASS: C6-SELF 검사기 자기 대상에서 제외 — FAIL (exit=1)
PASS: C7 CI 실행 줄 삭제 — FAIL (exit=1)
PASS: C8 검사기 파일 삭제 — FAIL (exit=127)
PASS: C9 검사 대상 0개가 되도록 글로브 변경 — FAIL (exit=1)
PASS: C9-COMMENT-DECOY 죽은 주석으로 깨진 pre-push 글로브 위장 — FAIL (exit=1)
PASS: C9-ECHO-DECOY echo 문자열로 깨진 pre-push 글로브 위장 — FAIL (exit=1)
PASS: C9-DEAD-CODE 최상위 exit 뒤 죽은 find 줄로 글로브 위장 — FAIL (exit=1)
PASS: C9-IF-FALSE if false 분기의 죽은 find 줄로 글로브 위장 — FAIL (exit=1)
PASS: C9-RUNTIME-FINGERPRINT 고정 sandbox 지문일 때만 정상 글로브 실행 — FAIL (exit=1)
PASS: C9-RUNTIME-PATH-FINGERPRINT 고정 임시경로 접두사일 때만 정상 글로브 실행 — FAIL (exit=1)
PASS: C10-A CI에 실패무시(or-true) 삽입 — FAIL (exit=1)
PASS: C10-B CI에 continue-on-error 삽입 — FAIL (exit=1)
PASS: C10-C CI에 if exists 조건 삽입 — FAIL (exit=1)
PASS: C10-D CI 다중 줄 exit 0 우회 — FAIL (exit=1)
PASS: C10-E pre-push에 실패무시(or-true) 삽입 — FAIL (exit=1)
PASS: C11 거짓 최종 판정 차단 — FAIL (exit=1)
PASS: C12 거짓 최종 판정 차단 — FAIL (exit=1)
PASS: C11-ARTIFACT-MISSING 증거 파일 누락 차단 — FAIL (exit=1)
PASS: C11-ARTIFACT-HASH 증거 해시 불일치 차단 — FAIL (exit=1)
PASS: C15 검사 스크립트가 저장소 밖 절대경로를 참조하지 않는다
PASS: C13 Codex/Claude 공통 계약 불일치 — FAIL (exit=1)
PASS: C14-A 메모리 파일 없음, 현재 SOT 직접 로드 — PASS (exit=0)
PASS: C14-B 메모리 파일 잘림, 현재 SOT 직접 로드 — PASS (exit=0)
PASS: BOUNDARY-500 직접 작성 코드 500줄 — PASS
PASS: BOUNDARY-501 직접 작성 코드 501줄 — FAIL
PASS: SOURCE-TREE 원본 저장소 상태 불변
CHECKED: 41
VERDICT: PASS
OK(run-acceptance): path c8836ae13207 — 판정 42건, CHECKED 41
EXIT: 0
```

→ 원명령 종료값은 0; 위 stdout/stderr 전체가 해당 판정의 직접 증거다.

### HS-A3 via CI wrapper

```text
TIMESTAMP_KST: 2026-08-25 23:44:33 KST
PWD: /private/tmp/valuehire-rdp-20260824.7e3kk1/worktree
HEAD: 8945496f957a62d8d17a8bceafc3616fc5e38d22
COMMAND: bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-a3.sh
PASS: 탐지됨 — CDP getAllCookies 직렬화
PASS: 탐지됨 — Playwright storageState
PASS: 탐지됨 — CDP 디버거 WebSocket URL
PASS: 탐지됨 — CDP 직렬화(값 모양 미상)
PASS: 탐지됨 — 값 모양만(키 이름 변조)
PASS: 탐지됨 — 세션 값 모양(ajax 형식)
PASS: 탐지됨 — 세션 쿠키 키(따옴표 값)
PASS: 탐지됨 — 세션 쿠키 키(무따옴표 YAML)
PASS: 탐지됨 — 세션 쿠키 키(.env 형태)
PASS: 탐지됨 — Set-Cookie 응답 헤더
PASS: 탐지됨 — Cookie 요청 헤더
PASS: 탐지됨 — 무따옴표 Cookie 헤더(Copy as cURL)
PASS: 탐지됨 — Bearer 인증 헤더
PASS: 탐지됨 — 쿠키 이름 앵커 — LIDC
PASS: 탐지됨 — 쿠키 이름 앵커 — PHPSESSID
PASS: 탐지됨 — 쿠키 이름 앵커 — BCOOKIE
PASS: 탐지됨 — 쿠키 이름 앵커 — BSCOOKIE
PASS: 오탐 없음 — 빌드 경로 값
PASS: 오탐 없음 — 상태 상수
PASS: 오탐 없음 — 헤더 '이름' 설정
PASS: 오탐 없음 — i18n 안내 문구
PASS: 오탐 없음 — 산문 속 키 이름 언급
PASS: 스캐너 종단 — 세션 쿠키 파일을 verify.sh 가 차단 (verify.sh exit=1)
PASS: 스캐너 종단 — 정상 파일은 verify.sh 가 통과 (verify.sh exit=0)
PASS: 작업트리 무오염 (git status 기준 — git 설정·내부 객체·참조는 범위 밖)
CHECKED: 25
OK(run-acceptance): path d394b96957cb — 판정 25건, CHECKED 25
EXIT: 0
```

→ 원명령 종료값은 0; 위 stdout/stderr 전체가 해당 판정의 직접 증거다.

### Secret acceptance via CI wrapper

```text
TIMESTAMP_KST: 2026-08-25 23:44:34 KST
PWD: /private/tmp/valuehire-rdp-20260824.7e3kk1/worktree
HEAD: 8945496f957a62d8d17a8bceafc3616fc5e38d22
COMMAND: bash scripts/verify/run-acceptance.sh scripts/acceptance-secret-webhook-vendor.sh
PASS: 탐지됨 — discord 웹훅 URL
PASS: 탐지됨 — discordapp.com 변종(구 도메인)
PASS: 탐지됨 — Slack 웹훅 URL
PASS: 탐지됨 — Anthropic 벤더 키(하이픈 접두 · 중립 변수명)
PASS: 탐지됨 — WEBHOOK 계열 .env 대입(불투명 토큰)
PASS: 탐지됨 — CREDENTIAL 계열 .env 대입
PASS: 탐지됨 — PRIVATE_KEY 한 줄 형태
PASS: 탐지됨 — BOT_TOKEN (기존 TOKEN 규칙 회귀 앵커 · 신규 규칙에는 없음)
PASS: 탐지됨 — discord 버전 경로 /api/v10/ (공식 권장 형식)
PASS: 탐지됨 — discord 하위 도메인(canary)
PASS: 탐지됨 — Slack 공공기관용 GovSlack 도메인
PASS: 탐지됨 — Slack services 없는 형태(OAuth 응답 예시)
PASS: 탐지됨 — 벤더 키 39자 본문(길이 경계)
PASS: 탐지됨 — 인라인 주석이 붙은 .env 값
PASS: 오탐 없음 — 일반 discord 채널 URL(비밀 아님)
PASS: 오탐 없음 — 코드 대입(값이 아니라 호출)
PASS: 오탐 없음 — 환경변수 참조(값이 없다)
PASS: 오탐 없음 — 산문 속 키 형식 언급
PASS: 오탐 없음 — 일반 Slack 워크스페이스 URL
PASS: 오탐 없음 — .env.example 의 예시 주소
PASS: 오탐 없음 — 숫자만 있는 설정값(재시도 간격)
PASS: 오탐 없음 — 접미사 위장 도메인(notdiscord.com)
PASS: 오탐 없음 — 접미사 위장 도메인(not-hooks.slack.com)
PASS: 오탐 없음 — CREDENTIAL 저장 방식 이름(글자 설정값)
PASS: 오탐 없음 — PRIVATE_KEY 형식 이름(짧은 글자+숫자 설정값)
PASS: 오탐 없음 — sk-ant 조각을 품은 평범한 식별자(왼쪽 경계)
PASS: 오탐 없음 — 밑줄 접두 위장 discord 도메인
PASS: 오탐 없음 — 밑줄 접두 위장 slack 도메인
PASS: 스캐너 종단 — 벤더 키 파일을 verify.sh 가 차단 (verify.sh exit=1)
PASS: 스캐너 종단 — 대문자 표기 웹훅도 차단(-i 손실 감지) (verify.sh exit=1)
PASS: 스캐너 종단 — 정상 파일은 verify.sh 가 통과 (verify.sh exit=0)
PASS: verify 계약 — 빈 Git 인덱스는 합격이 아니다 (NOT_RUN, CHECKED: 0, exit=2)
PASS: verify 계약 — 안전한 Git 인덱스 blob 한 개 (PASS, CHECKED: 1, exit=0)
PASS: verify 계약 — CHECKED 상수 위조 방지용 안전 blob 두 개 (PASS, CHECKED: 2, exit=0)
PASS: 3축 종료 상태 동일 (파일 상태[무시 포함] · HEAD · 객체 수 — 중간에 바꿨다 되돌린 변경·같은 개수 객체 교체는 못 본다, REV2-D1)
CHECKED: 35
OK(run-acceptance): path 4e096fdca893 — 판정 35건, CHECKED 35
EXIT: 0
```

→ 원명령 종료값은 0; 위 stdout/stderr 전체가 해당 판정의 직접 증거다.

### HS-A4 via CI wrapper

```text
TIMESTAMP_KST: 2026-08-25 23:44:35 KST
PWD: /private/tmp/valuehire-rdp-20260824.7e3kk1/worktree
HEAD: 8945496f957a62d8d17a8bceafc3616fc5e38d22
COMMAND: bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-a4.sh
PASS: gitignore 적용 — artifacts/x.png
PASS: gitignore 적용 — data/humansearch.sqlite3
PASS: gitignore 적용 — humansearch.db
PASS: gitignore 적용 — run.sqlite
PASS: gitignore 적용 — private-reviews/x.md
PASS: 추적 파일 198개 중 1048576 바이트 초과 0건
PASS: pre-commit 차단 확인 — 1MB 초과 파일 (exit=1 · 사유 일치)
PASS: pre-commit 차단 확인 — SQLite 파일 (exit=1 · 사유 일치)
PASS: pre-commit 차단 확인 — 아티팩트 스크린샷 (exit=1 · 사유 일치)
PASS: pre-commit 차단 확인 — 하위 경로 아티팩트 (exit=1 · 사유 일치)
PASS: pre-commit 차단 확인 — 하위 경로 데이터 (exit=1 · 사유 일치)
PASS: pre-commit 차단 확인 — SQLite WAL 사이드카 (exit=1 · 사유 일치)
PASS: pre-commit 차단 확인 — JSONL 덤프 (exit=1 · 사유 일치)
PASS: pre-commit 차단 확인 — 대문자 확장자 (exit=1 · 사유 일치)
PASS: pre-commit 차단 확인 — 디렉터리 규칙(확장자 무해) (exit=1 · 사유 일치)
PASS: pre-commit 차단 확인 — 비공개 리뷰 경로 (exit=1 · 사유 일치)
PASS: 인덱스 blob 기준 측정 확인 (작업트리 덮어쓰기로 우회 불가)
PASS: rename 도 검사 대상 (git mv 로 우회 불가)
PASS: 하위 경로 정상 소스는 조용히 사라지지 않는다 (앵커 확인)
PASS: 정상 파일은 통과 (차단과 통과가 한 쌍)
PASS: 훅과 공용 판정기의 금지 경로 패턴이 동치 (하위경로·사이드카·덤프·비공개리뷰 포함)
PASS: 판정기 실행 — 기록에만 남은 1MB 초과 파일을 잡는다 (D1) (exit=1)
PASS: 판정기 실행 — 깨끗한 기록은 통과시킨다 (차단과 통과가 한 쌍) (exit=0)
PASS: 현재 PII 차단·원문 비출력 — 후보자 컬럼 CSV 를 잡는다 (D2) (exit=1)
PASS: 현재 PII 차단·원문 비출력 — 후보자 컬럼 TSV 를 잡는다 (D2) (exit=1)
PASS: 현재 PII 차단·원문 비출력 — 후보자 컬럼 SQL 을 잡는다 (D2) (exit=1)
PASS: 판정기 실행 — 정상 지표 CSV 는 통과시킨다 (오탐 대조군) (exit=0)
PASS: 판정기 실행 — PII 컬럼 1종뿐인 정상 CSV 통과 (임계값 경계) (exit=0 · CHECKED=1)
PASS: 판정기 실행 — 정상 마이그레이션 SQL 은 통과시킨다 (오탐 대조군) (exit=0)
PASS: 판정기 실행 — 빈 tracked는 합격이 아니다 (exit=2 · CHECKED=0)
PASS: 판정기 실행 — 빈 history는 합격이 아니다 (exit=2 · CHECKED=0)
PASS: 판정기 실행 — tracked CHECKED는 실제 blob 두 개와 일치 (exit=0 · CHECKED=2)
PASS: 판정기 실행 — Git rev-list 실패는 NOT_RUN으로 전파 (exit=2 · CHECKED=0)
PASS: 과거 PII 차단·원문 비출력 — 삭제된 CSV blob (exit=1)
PASS: 과거 PII 차단·원문 비출력 — 삭제된 TSV blob (exit=1)
PASS: 과거 PII 차단·원문 비출력 — 삭제된 SQL blob을 all에서도 탐지 (exit=1)
PASS: 과거 PII 차단·원문 비출력 — 동일 blob의 안전 확장자 alias가 있어도 삭제 CSV 탐지 (exit=1)
PASS: 과거 PII 차단·원문 비출력 — 동일 blob의 안전 확장자 alias가 있어도 all에서 탐지 (exit=1)
PASS: 과거 PII 차단·원문 비출력 — 탭·따옴표·줄바꿈 포함 CSV 경로도 history에서 안전하게 탐지 (exit=1)
PASS: 과거 PII 차단·원문 비출력 — 탭·따옴표·줄바꿈 포함 CSV 경로도 all에서 안전하게 탐지 (exit=1)
PASS: 판정기 실행 — 삭제된 정상 지표 CSV history 통과 (exit=0)
PASS: 판정기 실행 — 삭제된 PII 컬럼 1종 CSV history 통과 (exit=0)
PASS: 판정기 실행 — 삭제된 schema-only SQL history 통과 (exit=0)
PASS: 현재/history PII 판정 함수 1개 직접 공유 (정의 1 · 각 호출 1)
PASS: P11 코드 예산 — 현재 파일≤600·함수≤100, 600/100 통과·601/101 차단
PASS: CI 가 공용 판정기를 실행 줄에서 호출한다
PASS: 판정기 스텝에 비활성화 조건 없음
PASS: repository-data-protection acceptance가 CI와 검증 SOT에 정확히 한 번 연결됨
PASS: 작업트리 무오염 (git status 기준 — git 설정·내부 객체·참조는 범위 밖)
CHECKED: 49
OK(run-acceptance): path 9a8deea619d8 — 판정 49건, CHECKED 49
EXIT: 0
```

→ 원명령 종료값은 0; 위 stdout/stderr 전체가 해당 판정의 직접 증거다.

### Repository data protection via CI wrapper

```text
TIMESTAMP_KST: 2026-08-25 23:44:53 KST
PWD: /private/tmp/valuehire-rdp-20260824.7e3kk1/worktree
HEAD: 8945496f957a62d8d17a8bceafc3616fc5e38d22
COMMAND: bash scripts/verify/run-acceptance.sh scripts/acceptance-repository-data-protection.sh
PASS: current multiline SQL
PASS: deleted history multiline SQL
PASS: all staged multiline SQL
PASS: comment newline SQL load
PASS: comment-only SQL control
PASS: string-only SQL control
PASS: multiline COPY FROM SQL load
PASS: deleted history multiline COPY FROM SQL load
PASS: all staged multiline COPY FROM SQL load
PASS: COPY identifier schema control
PASS: tracked partial ls-files
PASS: pii partial ls-files
PASS: all partial ls-files no false PASS
PASS: all tracked NOT_RUN plus completed history only
PASS: all history FAIL plus pii NOT_RUN
PASS: all normal checked sum
PASS: forbidden path fingerprint only
PASS: oversize path fingerprint only
PASS: PII fail path fingerprint only
PASS: path NOT_RUN raw suppression
PASS: path fingerprint 역조회 결정론·삭제 history·충돌
PASS: acceptance-hs-a4 부분 git 대상 수집 정확 계약
PASS: acceptance-semantic-mutations 부분 git 대상 수집 정확 계약
PASS: hs-a4 크기초과 진단 원문 경로 제거
PASS: scanner unknown-mode NOT_RUN 원문 입력 제거
PASS: verify secret FAIL 원문 경로·값 제거
PASS: verify path NOT_RUN 원문 경로 제거
PASS: run-acceptance 오류 원문 대상 경로 제거
PASS: current/history scan_pii_content 공유
PASS: verify.yml 신규 acceptance 정확히 1회 호출
PASS: verification-commands.md 신규 acceptance 등록
PASS: CI 호출 삭제 mutation 방어 등록
PASS: hs-a4 코드 예산 대상에 신규 acceptance 포함
CHECKED: 33
VERDICT: PASS
OK(run-acceptance): path 75787d607b73 — 판정 34건, CHECKED 33
EXIT: 0
```

→ 원명령 종료값은 0; 위 stdout/stderr 전체가 해당 판정의 직접 증거다.

### Secret scanner

```text
TIMESTAMP_KST: 2026-08-25 23:45:07 KST
PWD: /private/tmp/valuehire-rdp-20260824.7e3kk1/worktree
HEAD: 8945496f957a62d8d17a8bceafc3616fc5e38d22
COMMAND: bash verify.sh
PASS: no secret-pattern match in any tracked file, .env not tracked
CHECKED: 198
EXIT: 0
```

→ 원명령 종료값은 0; 위 stdout/stderr 전체가 해당 판정의 직접 증거다.

### Tracked scanner

```text
TIMESTAMP_KST: 2026-08-25 23:45:10 KST
PWD: /private/tmp/valuehire-rdp-20260824.7e3kk1/worktree
HEAD: 8945496f957a62d8d17a8bceafc3616fc5e38d22
COMMAND: bash scripts/scan-data-exposure.sh tracked
PASS: 추적 파일 198개 검사, 위반 0건
CHECKED: 198
EXIT: 0
```

→ 원명령 종료값은 0; 위 stdout/stderr 전체가 해당 판정의 직접 증거다.

### History scanner

```text
TIMESTAMP_KST: 2026-08-25 23:45:15 KST
PWD: /private/tmp/valuehire-rdp-20260824.7e3kk1/worktree
HEAD: 8945496f957a62d8d17a8bceafc3616fc5e38d22
COMMAND: bash scripts/scan-data-exposure.sh history
PASS: 기록 전량 blob 1319개 검사, 크기·경로·개인정보 위반 0건
CHECKED: 1319
EXIT: 0
```

→ 원명령 종료값은 0; 위 stdout/stderr 전체가 해당 판정의 직접 증거다.

### PII scanner

```text
TIMESTAMP_KST: 2026-08-25 23:46:08 KST
PWD: /private/tmp/valuehire-rdp-20260824.7e3kk1/worktree
HEAD: 8945496f957a62d8d17a8bceafc3616fc5e38d22
COMMAND: bash scripts/scan-data-exposure.sh pii
PASS: csv/tsv/sql 0개 검사(추적 198개 중), 개인정보 적재 0건
CHECKED: 198
EXIT: 0
```

→ 원명령 종료값은 0; 위 stdout/stderr 전체가 해당 판정의 직접 증거다.

### All scanner

```text
TIMESTAMP_KST: 2026-08-25 23:46:09 KST
PWD: /private/tmp/valuehire-rdp-20260824.7e3kk1/worktree
HEAD: 8945496f957a62d8d17a8bceafc3616fc5e38d22
COMMAND: bash scripts/scan-data-exposure.sh all
PASS: 추적 파일 198개 검사, 위반 0건
PASS: 기록 전량 blob 1319개 검사, 크기·경로·개인정보 위반 0건
PASS: csv/tsv/sql 0개 검사(추적 198개 중), 개인정보 적재 0건
CHECKED: 1715
EXIT: 0
```

→ 원명령 종료값은 0; 위 stdout/stderr 전체가 해당 판정의 직접 증거다.

### CI step integrity checker

```text
TIMESTAMP_KST: 2026-08-25 23:47:04 KST
PWD: /private/tmp/valuehire-rdp-20260824.7e3kk1/worktree
HEAD: 8945496f957a62d8d17a8bceafc3616fc5e38d22
COMMAND: bash scripts/verify/check-ci-step-integrity.sh
ALLOWED: 인수 검사 0-5 (push · CI 연결) — if 허용 (origin/main==main 을 보는 검사라 main push 에서만 의미가 있다. PR 실행에서 요구하면 상시 실패한다.)
PASS: 조건부·오류무시 스텝 없음 (job·step 27개 검사)
CHECKED: 27
EXIT: 0
```

→ 원명령 종료값은 0; 위 stdout/stderr 전체가 해당 판정의 직접 증거다.

### CI integrity acceptance via wrapper

```text
TIMESTAMP_KST: 2026-08-25 23:47:04 KST
PWD: /private/tmp/valuehire-rdp-20260824.7e3kk1/worktree
HEAD: 8945496f957a62d8d17a8bceafc3616fc5e38d22
COMMAND: bash scripts/verify/run-acceptance.sh scripts/acceptance-ci-step-integrity.sh
PASS: 실제 워크플로 → 통과 — exit=0
PASS: 스텝에 if: ${{ false }} 주입 → 불합격 — exit=1
PASS: 스텝에 항상-거짓 조건 주입 → 불합격 — exit=1
PASS: 스텝에 항상-참 조건(always) 주입 → 불합격 — exit=1
PASS: 스텝에 continue-on-error 주입 → 불합격 — exit=1
PASS: job 에 if 주입 → 불합격 — exit=1
PASS: 실행 대신 echo → 불합격 — exit=1
PASS: 실행 대신 bash -n → 불합격 — exit=1
PASS: repository-data-protection 호출 삭제 → 불합격 — exit=1
PASS: job 의 스텝 전량 삭제 → 불합격 — exit=1
PASS: 워크플로 파일 없음 → NOT_RUN — exit=2
PASS: 파싱 불가 워크플로 → NOT_RUN — exit=2
PASS: job 0개 → NOT_RUN — exit=2
PASS: 이유가 적힌 예외는 통과 — 0-5 의 main 전용 조건
PASS: 원본 저장소 상태 불변 — before/after 동일
CHECKED: 15
VERDICT: PASS
OK(run-acceptance): path e710376e5fb9 — 판정 16건, CHECKED 15
EXIT: 0
```

→ 원명령 종료값은 0; 위 stdout/stderr 전체가 해당 판정의 직접 증거다.

### Semantic mutations via wrapper

```text
TIMESTAMP_KST: 2026-08-25 23:47:06 KST
PWD: /private/tmp/valuehire-rdp-20260824.7e3kk1/worktree
HEAD: 8945496f957a62d8d17a8bceafc3616fc5e38d22
COMMAND: bash scripts/verify/run-acceptance.sh scripts/acceptance-semantic-mutations.sh
PASS: 대상 수집 — 인수 검사 27개 = Git 완전 목록 27개
PASS: 무력화 차단: exit-zero — 27/27 전부 불합격 처리
PASS: 무력화 차단: true-only — 27/27 전부 불합격 처리
PASS: 무력화 차단: noop — 27/27 전부 불합격 처리
PASS: 무력화 차단: empty — 27/27 전부 불합격 처리
PASS: 무력화 차단: echo-only — 27/27 전부 불합격 처리
PASS: 정상 인수 검사 통과 — acceptance-guard-global-skill-files.sh exit=0 (과잉 차단 없음)
PASS: 래퍼 인자 없음 거부 — exit=2
PASS: 래퍼 대상 없음 거부 — exit=2
PASS: 원본 저장소 상태 불변 — before/after 동일
CHECKED: 10
VERDICT: PASS
OK(run-acceptance): path b9c6a4253925 — 판정 11건, CHECKED 10
EXIT: 0
```

→ 원명령 종료값은 0; 위 stdout/stderr 전체가 해당 판정의 직접 증거다.

### Mechanism registry via wrapper

```text
TIMESTAMP_KST: 2026-08-25 23:47:14 KST
PWD: /private/tmp/valuehire-rdp-20260824.7e3kk1/worktree
HEAD: 8945496f957a62d8d17a8bceafc3616fc5e38d22
COMMAND: bash scripts/verify/run-acceptance.sh scripts/acceptance-verify-ac-m.sh
PASS: 검사기 실존·실행가능 — scripts/verify/check-mechanism-registry.sh
PASS: fixture 정상 명부 → 통과 (exit=0)
PASS: fixture path 없는 항목 → 불합격 (exit=1)
PASS: fixture 죽은 target → 불합격 (exit=1)
PASS: 주석에만 있는 target → 불합격 (exit=1)
PASS: echo에만 있는 target → 불합격 (exit=1)
PASS: 최상위 exit 뒤 target → 불합격 (exit=1)
PASS: if false 분기 안 target → 불합격 (exit=1)
PASS: 고정 sandbox 지문에서만 실행되는 target → 불합격 (exit=1)
PASS: 고정 임시경로 접두사에서만 실행되는 target → 불합격 (exit=1)
PASS: id 중복 → 불합격 (exit=1)
PASS: 알 수 없는 stage → 불합격 (exit=1)
PASS: manual 인데 사유 없음 → 불합격 (exit=1)
PASS: manual 정상(사유+실행권한) → 통과 (exit=0)
PASS: manual 인데 실행권한 없음 → 불합격 (exit=1)
PASS: ci 인데 거짓 target → 불합격 (exit=1)
PASS: 절대경로 path → 불합격 (exit=1)
PASS: 상대경로 심볼릭 링크 → 불합격 (exit=1)
PASS: 필드 중복(path 2회, 마지막 값 유효) → 불합격 (exit=1)
PASS: id 뒤 인라인 주석 → 불합격 (exit=1)
PASS: 닫히지 않은 따옴표 → 불합격 (exit=1)
PASS: stage 불일치 필드(ci_mirror_job) → 불합격 (exit=1)
PASS: 문법 오류·항목 0개 → 위반(1) (exit=1)
PASS: 항목 0개 명부 → NOT_RUN (exit=2)
PASS: ci_mirror_job 불일치 → 불합격 (exit=1)
PASS: 필수 필드(stage) 누락 → 불합격 (exit=1)
PASS: 빈 문자열 path → 불합격 (exit=1)
PASS: CI 배선 — verify.yml 에 무조건 실행 스텝 정확히 1회
PASS: 실제 명부(docs/sot/mechanism-registry.yaml) → 통과 (exit=0)
PASS: 명부 항목 13개 = 검사기 보고 13개 (하한 3)
PASS: 저장소 무오염 (시작/종료 상태 동일)
CHECKED: 31
OK(run-acceptance): path 5c71f52b2c9d — 판정 31건, CHECKED 31
EXIT: 0
```

→ 원명령 종료값은 0; 위 stdout/stderr 전체가 해당 판정의 직접 증거다.

### Repository attack mutations

```text
TIMESTAMP_KST: 2026-08-25 23:47:23 KST
PWD: /private/tmp/valuehire-rdp-20260824.7e3kk1/worktree
HEAD: 8945496f957a62d8d17a8bceafc3616fc5e38d22
COMMAND: bash .omx/artifacts/rdp-attack-mutations.sh
MUTATION: sql-detection-deleted
COMMAND: bash scripts/acceptance-repository-data-protection.sh
FAIL: current multiline SQL — got exit=0 PASS=1 FAIL=0 NOT_RUN=0 CHECKED=1
FAIL: deleted history multiline SQL — got exit=0 PASS=1 FAIL=0 NOT_RUN=0 CHECKED=2
FAIL: all staged multiline SQL — got exit=0 PASS=3 FAIL=0 NOT_RUN=0 CHECKED=5
FAIL: comment newline SQL load — got exit=0 PASS=1 FAIL=0 NOT_RUN=0 CHECKED=1
PASS: comment-only SQL control
PASS: string-only SQL control
FAIL: multiline COPY FROM SQL load — got exit=0 PASS=1 FAIL=0 NOT_RUN=0 CHECKED=1
FAIL: deleted history multiline COPY FROM SQL load — got exit=0 PASS=1 FAIL=0 NOT_RUN=0 CHECKED=2
FAIL: all staged multiline COPY FROM SQL load — got exit=0 PASS=3 FAIL=0 NOT_RUN=0 CHECKED=5
PASS: COPY identifier schema control
PASS: tracked partial ls-files
PASS: pii partial ls-files
PASS: all partial ls-files no false PASS
PASS: all tracked NOT_RUN plus completed history only
PASS: all history FAIL plus pii NOT_RUN
PASS: all normal checked sum
PASS: forbidden path fingerprint only
PASS: oversize path fingerprint only
PASS: PII fail path fingerprint only
PASS: path NOT_RUN raw suppression
PASS: path fingerprint 역조회 결정론·삭제 history·충돌
PASS: acceptance-hs-a4 부분 git 대상 수집 정확 계약
PASS: acceptance-semantic-mutations 부분 git 대상 수집 정확 계약
PASS: hs-a4 크기초과 진단 원문 경로 제거
PASS: scanner unknown-mode NOT_RUN 원문 입력 제거
PASS: verify secret FAIL 원문 경로·값 제거
PASS: verify path NOT_RUN 원문 경로 제거
PASS: run-acceptance 오류 원문 대상 경로 제거
PASS: current/history scan_pii_content 공유
PASS: verify.yml 신규 acceptance 정확히 1회 호출
PASS: verification-commands.md 신규 acceptance 등록
PASS: CI 호출 삭제 mutation 방어 등록
PASS: hs-a4 코드 예산 대상에 신규 acceptance 포함
CHECKED: 33
VERDICT: FAIL
EXIT: 1
MUTANT_KILLED: sql-detection-deleted
MUTATION: copy-from-contract-loosened
COMMAND: bash scripts/acceptance-repository-data-protection.sh
PASS: current multiline SQL
PASS: deleted history multiline SQL
PASS: all staged multiline SQL
PASS: comment newline SQL load
PASS: comment-only SQL control
PASS: string-only SQL control
PASS: multiline COPY FROM SQL load
PASS: deleted history multiline COPY FROM SQL load
PASS: all staged multiline COPY FROM SQL load
FAIL: COPY identifier schema control — got exit=1 PASS=0 FAIL=1 NOT_RUN=0 CHECKED=1
PASS: tracked partial ls-files
PASS: pii partial ls-files
PASS: all partial ls-files no false PASS
PASS: all tracked NOT_RUN plus completed history only
PASS: all history FAIL plus pii NOT_RUN
PASS: all normal checked sum
PASS: forbidden path fingerprint only
PASS: oversize path fingerprint only
PASS: PII fail path fingerprint only
PASS: path NOT_RUN raw suppression
PASS: path fingerprint 역조회 결정론·삭제 history·충돌
PASS: acceptance-hs-a4 부분 git 대상 수집 정확 계약
PASS: acceptance-semantic-mutations 부분 git 대상 수집 정확 계약
PASS: hs-a4 크기초과 진단 원문 경로 제거
PASS: scanner unknown-mode NOT_RUN 원문 입력 제거
PASS: verify secret FAIL 원문 경로·값 제거
PASS: verify path NOT_RUN 원문 경로 제거
PASS: run-acceptance 오류 원문 대상 경로 제거
PASS: current/history scan_pii_content 공유
PASS: verify.yml 신규 acceptance 정확히 1회 호출
PASS: verification-commands.md 신규 acceptance 등록
PASS: CI 호출 삭제 mutation 방어 등록
PASS: hs-a4 코드 예산 대상에 신규 acceptance 포함
CHECKED: 33
VERDICT: FAIL
EXIT: 1
MUTANT_KILLED: copy-from-contract-loosened
MUTATION: partial-git-fail-open
COMMAND: bash scripts/acceptance-repository-data-protection.sh
PASS: current multiline SQL
PASS: deleted history multiline SQL
PASS: all staged multiline SQL
PASS: comment newline SQL load
PASS: comment-only SQL control
PASS: string-only SQL control
PASS: multiline COPY FROM SQL load
PASS: deleted history multiline COPY FROM SQL load
PASS: all staged multiline COPY FROM SQL load
PASS: COPY identifier schema control
FAIL: tracked partial ls-files — got exit=0 PASS=1 FAIL=0 NOT_RUN=0 CHECKED=1
FAIL: pii partial ls-files — got exit=0 PASS=1 FAIL=0 NOT_RUN=0 CHECKED=1
FAIL: all partial ls-files no false PASS — got exit=0 PASS=3 FAIL=0 NOT_RUN=0 CHECKED=3
FAIL: all tracked NOT_RUN plus completed history only — got exit=0 PASS=3 FAIL=0 NOT_RUN=0 CHECKED=3
PASS: all history FAIL plus pii NOT_RUN
PASS: all normal checked sum
PASS: forbidden path fingerprint only
PASS: oversize path fingerprint only
PASS: PII fail path fingerprint only
PASS: path NOT_RUN raw suppression
PASS: path fingerprint 역조회 결정론·삭제 history·충돌
PASS: acceptance-hs-a4 부분 git 대상 수집 정확 계약
PASS: acceptance-semantic-mutations 부분 git 대상 수집 정확 계약
PASS: hs-a4 크기초과 진단 원문 경로 제거
PASS: scanner unknown-mode NOT_RUN 원문 입력 제거
PASS: verify secret FAIL 원문 경로·값 제거
PASS: verify path NOT_RUN 원문 경로 제거
PASS: run-acceptance 오류 원문 대상 경로 제거
PASS: current/history scan_pii_content 공유
PASS: verify.yml 신규 acceptance 정확히 1회 호출
PASS: verification-commands.md 신규 acceptance 등록
PASS: CI 호출 삭제 mutation 방어 등록
PASS: hs-a4 코드 예산 대상에 신규 acceptance 포함
CHECKED: 33
VERDICT: FAIL
EXIT: 1
MUTANT_KILLED: partial-git-fail-open
MUTATION: raw-forbidden-path
COMMAND: bash scripts/acceptance-repository-data-protection.sh
PASS: current multiline SQL
PASS: deleted history multiline SQL
PASS: all staged multiline SQL
PASS: comment newline SQL load
PASS: comment-only SQL control
PASS: string-only SQL control
PASS: multiline COPY FROM SQL load
PASS: deleted history multiline COPY FROM SQL load
PASS: all staged multiline COPY FROM SQL load
PASS: COPY identifier schema control
PASS: tracked partial ls-files
PASS: pii partial ls-files
PASS: all partial ls-files no false PASS
PASS: all tracked NOT_RUN plus completed history only
PASS: all history FAIL plus pii NOT_RUN
PASS: all normal checked sum
FAIL: forbidden path fingerprint only — 원문 경로/값 출력
PASS: oversize path fingerprint only
PASS: PII fail path fingerprint only
PASS: path NOT_RUN raw suppression
PASS: path fingerprint 역조회 결정론·삭제 history·충돌
PASS: acceptance-hs-a4 부분 git 대상 수집 정확 계약
PASS: acceptance-semantic-mutations 부분 git 대상 수집 정확 계약
PASS: hs-a4 크기초과 진단 원문 경로 제거
PASS: scanner unknown-mode NOT_RUN 원문 입력 제거
PASS: verify secret FAIL 원문 경로·값 제거
PASS: verify path NOT_RUN 원문 경로 제거
PASS: run-acceptance 오류 원문 대상 경로 제거
PASS: current/history scan_pii_content 공유
PASS: verify.yml 신규 acceptance 정확히 1회 호출
PASS: verification-commands.md 신규 acceptance 등록
PASS: CI 호출 삭제 mutation 방어 등록
PASS: hs-a4 코드 예산 대상에 신규 acceptance 포함
CHECKED: 33
VERDICT: FAIL
EXIT: 1
MUTANT_KILLED: raw-forbidden-path
MUTATION: checked-total-forged
COMMAND: bash scripts/acceptance-repository-data-protection.sh
PASS: current multiline SQL
FAIL: deleted history multiline SQL — got exit=1 PASS=0 FAIL=1 NOT_RUN=0 CHECKED=1
FAIL: all staged multiline SQL — got exit=1 PASS=2 FAIL=1 NOT_RUN=0 CHECKED=1
PASS: comment newline SQL load
PASS: comment-only SQL control
PASS: string-only SQL control
PASS: multiline COPY FROM SQL load
FAIL: deleted history multiline COPY FROM SQL load — got exit=1 PASS=0 FAIL=1 NOT_RUN=0 CHECKED=1
FAIL: all staged multiline COPY FROM SQL load — got exit=1 PASS=2 FAIL=1 NOT_RUN=0 CHECKED=1
PASS: COPY identifier schema control
FAIL: tracked partial ls-files — got exit=2 PASS=0 FAIL=0 NOT_RUN=1 CHECKED=1
FAIL: pii partial ls-files — got exit=2 PASS=0 FAIL=0 NOT_RUN=1 CHECKED=1
PASS: all partial ls-files no false PASS
PASS: all tracked NOT_RUN plus completed history only
FAIL: all history FAIL plus pii NOT_RUN — got exit=2 PASS=0 FAIL=1 NOT_RUN=1 CHECKED=1
FAIL: all normal checked sum — got exit=0 PASS=3 FAIL=0 NOT_RUN=0 CHECKED=1
PASS: forbidden path fingerprint only
PASS: oversize path fingerprint only
PASS: PII fail path fingerprint only
PASS: path NOT_RUN raw suppression
PASS: path fingerprint 역조회 결정론·삭제 history·충돌
PASS: acceptance-hs-a4 부분 git 대상 수집 정확 계약
PASS: acceptance-semantic-mutations 부분 git 대상 수집 정확 계약
PASS: hs-a4 크기초과 진단 원문 경로 제거
PASS: scanner unknown-mode NOT_RUN 원문 입력 제거
PASS: verify secret FAIL 원문 경로·값 제거
PASS: verify path NOT_RUN 원문 경로 제거
PASS: run-acceptance 오류 원문 대상 경로 제거
PASS: current/history scan_pii_content 공유
PASS: verify.yml 신규 acceptance 정확히 1회 호출
PASS: verification-commands.md 신규 acceptance 등록
PASS: CI 호출 삭제 mutation 방어 등록
PASS: hs-a4 코드 예산 대상에 신규 acceptance 포함
CHECKED: 33
VERDICT: FAIL
EXIT: 1
MUTANT_KILLED: checked-total-forged
MUTATION: history-pii-call-deleted
COMMAND: bash scripts/acceptance-repository-data-protection.sh
PASS: current multiline SQL
FAIL: deleted history multiline SQL — got exit=0 PASS=1 FAIL=0 NOT_RUN=0 CHECKED=2
PASS: all staged multiline SQL
PASS: comment newline SQL load
PASS: comment-only SQL control
PASS: string-only SQL control
PASS: multiline COPY FROM SQL load
FAIL: deleted history multiline COPY FROM SQL load — got exit=0 PASS=1 FAIL=0 NOT_RUN=0 CHECKED=2
PASS: all staged multiline COPY FROM SQL load
PASS: COPY identifier schema control
PASS: tracked partial ls-files
PASS: pii partial ls-files
PASS: all partial ls-files no false PASS
PASS: all tracked NOT_RUN plus completed history only
FAIL: all history FAIL plus pii NOT_RUN — got exit=2 PASS=0 FAIL=0 NOT_RUN=1 CHECKED=5
PASS: all normal checked sum
PASS: forbidden path fingerprint only
PASS: oversize path fingerprint only
PASS: PII fail path fingerprint only
PASS: path NOT_RUN raw suppression
PASS: path fingerprint 역조회 결정론·삭제 history·충돌
PASS: acceptance-hs-a4 부분 git 대상 수집 정확 계약
PASS: acceptance-semantic-mutations 부분 git 대상 수집 정확 계약
PASS: hs-a4 크기초과 진단 원문 경로 제거
PASS: scanner unknown-mode NOT_RUN 원문 입력 제거
PASS: verify secret FAIL 원문 경로·값 제거
PASS: verify path NOT_RUN 원문 경로 제거
PASS: run-acceptance 오류 원문 대상 경로 제거
FAIL: scan_pii_content 공유 위반 defs/history/current=1/0/1
PASS: verify.yml 신규 acceptance 정확히 1회 호출
PASS: verification-commands.md 신규 acceptance 등록
PASS: CI 호출 삭제 mutation 방어 등록
PASS: hs-a4 코드 예산 대상에 신규 acceptance 포함
CHECKED: 33
VERDICT: FAIL
EXIT: 1
MUTANT_KILLED: history-pii-call-deleted
MUTATION: acceptance-case-deleted
COMMAND: bash scripts/acceptance-repository-data-protection.sh
PASS: deleted history multiline SQL
PASS: all staged multiline SQL
PASS: comment newline SQL load
PASS: comment-only SQL control
PASS: string-only SQL control
PASS: multiline COPY FROM SQL load
PASS: deleted history multiline COPY FROM SQL load
PASS: all staged multiline COPY FROM SQL load
PASS: COPY identifier schema control
PASS: tracked partial ls-files
PASS: pii partial ls-files
PASS: all partial ls-files no false PASS
PASS: all tracked NOT_RUN plus completed history only
PASS: all history FAIL plus pii NOT_RUN
PASS: all normal checked sum
PASS: forbidden path fingerprint only
PASS: oversize path fingerprint only
PASS: PII fail path fingerprint only
PASS: path NOT_RUN raw suppression
PASS: path fingerprint 역조회 결정론·삭제 history·충돌
PASS: acceptance-hs-a4 부분 git 대상 수집 정확 계약
PASS: acceptance-semantic-mutations 부분 git 대상 수집 정확 계약
PASS: hs-a4 크기초과 진단 원문 경로 제거
PASS: scanner unknown-mode NOT_RUN 원문 입력 제거
PASS: verify secret FAIL 원문 경로·값 제거
PASS: verify path NOT_RUN 원문 경로 제거
PASS: run-acceptance 오류 원문 대상 경로 제거
PASS: current/history scan_pii_content 공유
PASS: verify.yml 신규 acceptance 정확히 1회 호출
PASS: verification-commands.md 신규 acceptance 등록
PASS: CI 호출 삭제 mutation 방어 등록
PASS: hs-a4 코드 예산 대상에 신규 acceptance 포함
FAIL: 검사 항목 32개 ≠ 계약값 33개
CHECKED: 32
EXIT: 1
MUTANT_KILLED: acceptance-case-deleted
MUTATION: ci-call-deleted
COMMAND: bash scripts/acceptance-ci-step-integrity.sh
FAIL: 실제 워크플로 → 통과 — expected exit=0 actual=1
PASS: 스텝에 if: ${{ false }} 주입 → 불합격 — exit=1
PASS: 스텝에 항상-거짓 조건 주입 → 불합격 — exit=1
PASS: 스텝에 항상-참 조건(always) 주입 → 불합격 — exit=1
PASS: 스텝에 continue-on-error 주입 → 불합격 — exit=1
PASS: job 에 if 주입 → 불합격 — exit=1
PASS: 실행 대신 echo → 불합격 — exit=1
PASS: 실행 대신 bash -n → 불합격 — exit=1
PASS: repository-data-protection 호출 삭제 → 불합격 — exit=1
PASS: job 의 스텝 전량 삭제 → 불합격 — exit=1
PASS: 워크플로 파일 없음 → NOT_RUN — exit=2
PASS: 파싱 불가 워크플로 → NOT_RUN — exit=2
PASS: job 0개 → NOT_RUN — exit=2
FAIL: 이유가 적힌 예외는 통과 — ALLOWED 출력 없음 — 예외 목록이 죽었다
PASS: 원본 저장소 상태 불변 — before/after 동일
CHECKED: 15
VERDICT: FAIL
EXIT: 1
MUTANT_KILLED: ci-call-deleted
MUTATIONS_CHECKED: 8
VERDICT: PASS
EXIT: 0
```

→ 원명령 종료값은 0; 위 stdout/stderr 전체가 해당 판정의 직접 증거다.

### Diff whitespace

```text
TIMESTAMP_KST: 2026-08-25 23:48:59 KST
PWD: /private/tmp/valuehire-rdp-20260824.7e3kk1/worktree
HEAD: 8945496f957a62d8d17a8bceafc3616fc5e38d22
COMMAND: git diff --check fdac401be104bc5d9454401edf0477fb478636dc..HEAD
EXIT: 0
```

→ 원명령 종료값은 0; 위 stdout/stderr 전체가 해당 판정의 직접 증거다.

### Scanner and dedicated acceptance ShellCheck

```text
TIMESTAMP_KST: 2026-08-25 23:49:00 KST
PWD: /private/tmp/valuehire-rdp-20260824.7e3kk1/worktree
HEAD: 8945496f957a62d8d17a8bceafc3616fc5e38d22
COMMAND: shellcheck scripts/scan-data-exposure.sh scripts/acceptance-repository-data-protection.sh
EXIT: 0
```

→ 원명령 종료값은 0; 위 stdout/stderr 전체가 해당 판정의 직접 증거다.

### Changed shell warning-level ShellCheck

```text
TIMESTAMP_KST: 2026-08-25 23:49:01 KST
PWD: /private/tmp/valuehire-rdp-20260824.7e3kk1/worktree
HEAD: 8945496f957a62d8d17a8bceafc3616fc5e38d22
COMMAND: shellcheck -S warning verify.sh scripts/scan-data-exposure.sh scripts/resolve-data-path-fingerprint.sh scripts/acceptance-repository-data-protection.sh scripts/acceptance-hs-a4.sh scripts/acceptance-semantic-mutations.sh scripts/acceptance-ci-step-integrity.sh scripts/verify/check-ci-step-integrity.sh scripts/verify/run-acceptance.sh
EXIT: 0
```

→ 원명령 종료값은 0; 위 stdout/stderr 전체가 해당 판정의 직접 증거다.

### Changed shell syntax

```text
TIMESTAMP_KST: 2026-08-25 23:49:02 KST
PWD: /private/tmp/valuehire-rdp-20260824.7e3kk1/worktree
HEAD: 8945496f957a62d8d17a8bceafc3616fc5e38d22
COMMAND: bash -n verify.sh scripts/scan-data-exposure.sh scripts/resolve-data-path-fingerprint.sh scripts/acceptance-repository-data-protection.sh scripts/acceptance-hs-a4.sh scripts/acceptance-semantic-mutations.sh scripts/acceptance-ci-step-integrity.sh scripts/verify/check-ci-step-integrity.sh scripts/verify/run-acceptance.sh
EXIT: 0
```

→ 원명령 종료값은 0; 위 stdout/stderr 전체가 해당 판정의 직접 증거다.

### P23 verified SHA

```text
TIMESTAMP_KST: 2026-08-25 23:49:02 KST
PWD: /private/tmp/valuehire-rdp-20260824.7e3kk1/worktree
HEAD: 8945496f957a62d8d17a8bceafc3616fc5e38d22
COMMAND: bash scripts/verify/check-verified-sha.sh
NOT_RUN: 원격에 task/repository-data-protection-followup-20260825 가 없다 — 아직 push 되지 않았다면 검증된 SHA 자체가 없다
EXIT: 2
```

→ 원격 브랜치와 그 SHA의 GitHub check-run이 없어 P23은 `NOT_RUN`이다. 로컬 PASS로 대체하지 않는다.

### Final isolated state

```text
TIMESTAMP_KST: 2026-08-25 23:49:03 KST
PWD: /private/tmp/valuehire-rdp-20260824.7e3kk1/worktree
HEAD: 8945496f957a62d8d17a8bceafc3616fc5e38d22
COMMAND: git status --porcelain=v1 && git rev-parse HEAD && wc -l scripts/scan-data-exposure.sh scripts/acceptance-repository-data-protection.sh scripts/acceptance-hs-a4.sh
8945496f957a62d8d17a8bceafc3616fc5e38d22
     401 scripts/scan-data-exposure.sh
     451 scripts/acceptance-repository-data-protection.sh
     600 scripts/acceptance-hs-a4.sh
    1452 total
EXIT: 0
```

→ 원명령 종료값은 0; 위 stdout/stderr 전체가 해당 판정의 직접 증거다.

## Claude V1 복구 기록

```text
TIMESTAMP_KST: 2026-08-25 23:25:05 KST
COMMAND: omx ask claude '<8945496 이전 SHA 3136354 read-only V1 prompt>'
EXIT: 1
OUTPUT: Credit balance is too low
STATUS: NOT_RUN
ARTIFACT: .omx/artifacts/claude-you-are-claude-v1-an-independent-adversarial-reviewer-work-r-2026-08-25T14-25-05-039Z.md

TIMESTAMP_KST: 2026-08-25 23:31~23:36 KST
COMMAND: env -u ANTHROPIC_API_KEY omx ask claude '<8945496 exact-SHA read-only V1 prompt>'
ELAPSED: 5 minutes
STDOUT_BYTES: 0
STDERR_BYTES: 0
ACTION: interrupt after bounded recovery window
EXIT: 1
STATUS: NOT_RUN
```

→ 직접 크레딧 경로와 환경변수를 제거한 로그인 경로를 각각 시도했지만 검토 본문을 얻지 못했다. 다른 Codex 검증을 Claude V1 PASS로 바꾸지 않는다.

## 원본 dirty worktree 종료 대조

```text
TIMESTAMP_KST: 2026-08-25 23:49:03 KST
PWD: /Users/kangsangmo/Desktop/valuehire_v6
HEAD: 3094eefa646b102074dfb6401777afe450223e6c
BRANCH: rescue/main-mixed-20260825T200952
DIRTY_COUNT: 43
STATUS_SHA256: 64c1b6218c9079bfb0447b6fb1625a1a8a44db394ca56b92b23f5367cc38894b
d226898f717649c2c0be5790e09e7f716af118dcbb4ccc0eaee9f13632f99911  docs/sot/verification-commands.md
5f7de4bfa2805608d8e548905fd4483566f76211281a9e047b16bd0e1870d978  scripts/check-docs-sot.sh
EXIT: 0
```

→ 시작 기준 HEAD·branch·두 SOT 해시는 유지됐지만 dirty count/status 지문은 41·`804384...`에서 43·현재 지문으로 바뀌었다. 원본을 수정하거나 되돌리지 않았으며, 보존 AC는 불일치로 남는다.

## 판정

- 로컬 구현·targeted acceptance·CI 등가·mutation: PASS
- check-docs-sot catalog/surface coverage: 완료 근거 제외, 잔여 REQUEST_CHANGES
- Claude V1: NOT_RUN
- P23: NOT_RUN
- 원본 dirty 보존: FAIL(외부 드리프트)
- 전체: REQUEST_CHANGES
