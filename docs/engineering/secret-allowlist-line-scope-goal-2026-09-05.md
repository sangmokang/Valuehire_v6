Base SHA: 8bb31ed912869275b17579b8b2d8042f47098cea (unmerged task/secret-short-value-additive)

# 비밀 스캔 줄 단위 허용 목록 goal (2026-09-05)

## 1층 — 결론

현재 비밀 검사는 파일 하나에서 한 줄만 오탐이어도 파일 전체를 실패시키며, 안전하게 한 줄만
제외할 방법이 없습니다. 이번 변경은 정확한 파일 경로와 정확한 줄 내용에 허용 횟수 한 번을
묶어 이 문제만 해결합니다. 탐지 규칙은 늘리지 않으며 형식 구멍 자체를 닫았다고 판정하지 않습니다.

작업은 지정된 격리 작업공간과 브랜치에서만 수행하고 로컬 안전 커밋까지 보존합니다. 원격 전송,
변경 요청 생성, 합치기는 하지 않습니다. 배포와 제품 데이터 변경이 없는 내부 보안 검사 작업이므로
제품 배송 상태는 해당 없음입니다.

## 2층 — 판단 근거

파일 이름만 허용하면 같은 파일에 새 비밀이 생겨도 모두 통과하므로 금지합니다. 줄번호를 저장하면
설명 한 줄을 위에 추가한 것만으로 허용이 깨지므로 금지합니다. 대신 `path`와 줄 내용의 Git blob
지문을 저장하고, 같은 조합이 한 번 나타날 때 허용 항목 하나를 소비합니다. 따라서 줄이 이동해도
통과하지만 같은 줄을 한 번 더 복제하면 남은 한 줄이 실패합니다.

작업공간 파일과 커밋 직전 파일은 내용을 가져오는 경계만 다르고, 정규식 판정·허용 소비·오류 판정은
한 함수가 담당합니다. 심볼릭 링크는 두 경로 모두 Git에 실제로 저장되는 링크 대상 문자열을 읽어,
작업공간에서만 링크 바깥 파일을 따라가던 기존 차이를 제거합니다.

### 결정 카드

> **무엇을** — `.secret-allowlist.yaml`에 정확한 상대 경로, 줄 내용 지문, 사유, 책임자, 만료일을 기록하고 같은 경로·지문당 허용 항목 수만큼만 매치를 소비합니다.
> **왜** — 줄 이동은 허용하면서 같은 내용의 추가 줄은 차단해야 하기 때문입니다.
> **버린 길** — 파일·디렉터리·이름 규칙 전체 면제는 새 비밀까지 숨기고, 줄번호 고정은 무해한 편집에 깨지며, 원문 저장은 허용 목록 자체가 비밀 규칙에 잡히므로 버립니다.
> **대가** — 허용할 줄이 바뀌면 지문을 다시 계산해야 하고, 같은 내용을 여러 번 허용하려면 항목도 그 횟수만큼 명시해야 합니다.
> **되돌리기** — 이 작업의 로컬 커밋들을 역순으로 되돌리면 기존 파일 단위 실패 판정으로 돌아갑니다. 비밀 데이터나 운영 데이터 복구는 없습니다.

## 3층 — 계약과 증거

### 1. 범위와 시작 상태

- 위험등급: L3. 보안 검사, 억제 장치, 훅, 서버 자동 검사, 정본을 함께 변경합니다.
- 저장소: `/Users/kangsangmo/Desktop/Valuehire_v6`
- 작업공간: `/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/secret-allowlist`
- 브랜치: `task/secret-allowlist-line-scope`
- 기준 선택: `git fetch origin main` 뒤 `8bb31ed`가 `origin/main`의 조상이 아님을 확인했으므로,
  아직 합쳐지지 않은 선행 브랜치의 `8bb31ed`에서 파생했습니다.
- 시작 HEAD: `8bb31ed912869275b17579b8b2d8042f47098cea`
- 원래 `main` 작업공간에는 사용자 변경이 있으므로 읽기 전용 상태 확인 외에는 손대지 않습니다.
- 현재 작업공간의 무시 파일은 `.omc/`, `.secret-patterns`이며 내용을 출력하거나 수정하지 않습니다.
- `private-reviews/`, `artifacts/`, `.harness/`, `.omx/`는 이 작업공간에 없습니다.
- 저장소 내부 `AGENTS.md`, `CLAUDE.md`는 추적 파일 목록에 없습니다. 사용자 메시지로 제공된
  `AGENTS.md`와 `/Users/kangsangmo/.codex/skills/strict/SKILL.md`를 적용합니다.

현재 `verify.sh:59-72`는 커밋 직전 파일은 파일별 `grep -q`, 작업공간 파일은 `grep -l`로
갈라집니다. 특히 `verify.sh:72`는 매치한 파일 이름만 내므로 어느 줄이 오탐인지 판정할 수 없습니다.

현재 `suppressions.yaml:46-79`의 `secret-format-gap`은 인용형·camelCase·등호 공백·여러 줄·
base64·하이픈 키·docker-compose 시퀀스 형식이 탐지되지 않으며, 줄 단위 허용 목록이 선행조건이라고
기록합니다. 이번 작업은 이 선행조건만 닫고 항목을 삭제하지 않습니다.

현재 실제 오탐 후보는 다음 두 줄입니다.

- `docs/engineering/humansearch-v6-founding-spec-2026-08-07.md:515` — 자격증명 값이 아니라 저장 위치를 나타내는 `credential_source` 필드입니다.
- `scripts/acceptance-secret-webhook-vendor.sh:128` — 런타임에 조립하는 Slack 시험값을 담는 배열 원소입니다.

### 2. 근본 원인

스캐너 출력의 정보 단위가 줄이 아니라 파일입니다. 따라서 허용 목록이 참조할 수 있는 최소 단위도
파일 전체뿐이고, 오탐 한 줄과 같은 파일의 새 비밀 한 줄을 구분할 수 없습니다. 작업공간 경로와
커밋 직전 경로가 서로 다른 명령으로 매치를 판정해 심볼릭 링크에서도 결과가 갈립니다.

### 3. 단일 인수 기준

#### AC-ALLOWLIST-1

**EARS**: When 격리 임시 Git 저장소에서 동일한 `verify.sh`, 동일한 패턴, 동일한 줄 허용 목록을
작업공간 모드와 커밋 직전 모드로 각각 실행하면, 시스템은 아래 판정을 두 모드에서 동일하게 내야
합니다. And 허용 목록에 없는 기존 검출 표본 가운데 변경 전에 잡혔다가 변경 후 놓치는 항목은 정확히
0개여야 합니다.

1. 허용 항목의 경로와 줄 내용이 한 번 나타나면 종료값 0이어야 합니다.
2. 같은 파일에 같은 줄 내용을 한 번 더 추가하면 허용 횟수를 초과한 줄 때문에 종료값 1이어야 합니다.
3. 허용한 줄 내용이 한 글자라도 바뀌면 종료값 1이어야 합니다.
4. 허용한 줄이 다른 줄번호로 이동하되 내용과 경로가 같으면 종료값 0이어야 합니다.
5. 허용 항목에 만료일이 없거나 오늘보다 과거면 각각 종료값 2여야 합니다.
6. 허용 목록 파일이 없거나 계약 문법을 위반하면 각각 종료값 2여야 합니다.
7. 추적 심볼릭 링크는 작업공간 모드와 커밋 직전 모드가 모두 Git에 저장된 링크 대상 문자열만
   판정해야 하며, 링크가 가리키는 바깥 파일 내용 때문에 결과가 갈리면 안 됩니다.
8. 정규식 판정 전에는 런타임에 조립한 양성 대조군을 `/usr/bin/grep`으로 확인하고 두 모드의
   `verify.sh`가 모두 그 대조군을 종료값 1로 잡아야 합니다.

검증 명령과 기대값:

```text
bash scripts/verify/run-acceptance.sh scripts/acceptance-secret-allowlist.sh
```

→ 이 한 명령이 모든 격리 fixture와 두 스캔 모드의 판정을 끝까지 실행하며, 판정 수와 종료값을 함께
검증합니다.

최초 RED 기대 출력은 `CHECKED: 22`, 합성 표본의 `ALLOWED_LINES_COUNT=1`, `UNEXPECTED_MISSED_COUNT=0`, 마지막 `PASS:`
한 줄과 종료값 0입니다. RED 커밋에서는 같은 명령이 문법 오류가 아니라 허용 목록 미지원과 두 모드
심볼릭 링크 판정 차이 때문에 종료값 1이어야 합니다.

#### counter-AC — 가짜 합격 시나리오

- 파일 경로만 맞으면 파일 전체를 통과시켜 2번이 초록인 경우
- 줄번호를 저장해 한 줄 위에 무해한 내용을 넣었을 때 4번이 실패하는 경우
- 같은 경로·내용의 허용 항목 하나가 무제한 매치를 숨겨 2번이 통과하는 경우
- 허용 원문을 목록에 저장해 허용 목록 자신을 검사 대상에서 빼는 경우
- 허용 목록의 `reason` 줄에 탐지값을 넣고 자기 파일의 그 줄 지문으로 스스로 억제하는 경우
- 같은 허용 목록을 `./` 경로 별칭으로 선택해 자기 파일 문자열 비교를 우회하는 경우
- 추적 일반 파일이던 허용 목록의 worktree 사본을 저장소 밖 심볼릭 링크로 바꿔 외부 정책을 읽는 경우
- 매치 줄에 NUL 바이트를 추가했는데 Bash 변수가 그 바이트를 버려 기존 지문과 같아지는 경우
- 허용 목록 파싱 실패, 항목 0개, 필수 필드 누락, 잘못된 날짜, 만료를 값 없음처럼 통과시키는 경우
- 작업공간과 커밋 직전 모드가 서로 다른 허용 판정 함수를 쓰는 경우
- 작업공간 모드가 추적 심볼릭 링크를 따라 저장되지 않는 바깥 내용을 검사하는 경우
- 양성 대조군이 실제로 잡히지 않는데 `MISSED` 결과를 허용 증거로 세는 경우
- `.secret-patterns.default`를 변경하거나 새 탐지 정규식을 추가해 범위를 형식 구멍 본체까지 넓히는 경우
- 새 인수 검사가 로컬 문서에만 있고 서버 자동 검사에 연결되지 않는 경우
- 허용 목록 파일이 P13 검사 약화 감시와 억제 만료 스캔 중 하나에만 연결되는 경우
- 명부의 `target`을 되돌려 죽은 명령이 됐는데 명부 대조가 통과하는 경우

### 4. 입출력·오류·경계 계약

#### 파일 계약

```text
.secret-allowlist.yaml := comment-or-blank* entry+
entry :=
  - path: "<repository-relative literal path>"
    line_hash: "<40 lowercase hexadecimal git-blob digest of exact line bytes without newline>"
    reason: "<non-empty single-line text>"
    owner: "<non-empty single-line text>"
    expiry: "<YYYY-MM-DD>"
```

→ 허용 항목은 정확한 파일·줄 지문과 사유·책임자·기한을 한 묶음으로 요구하며, 일부 필드만 있는
항목은 유효한 억제가 아닙니다.

- `path`는 정확한 저장소 상대 경로 문자열이며 절대경로, `.`, `..`, 이중·후행 슬래시,
  빈 값, 글로브 문자를 거부합니다.
  대상 파일이 현재 없으면 항목은 어떤 매치에도 적용되지 않는 비활성 상태로 남고, expiry 의무는
  그대로 적용됩니다. 이 성질로 부분 fixture에서도 운영 목록 원본을 복사해 같은 파서를 검증합니다.
- 허용 목록 파일 자체는 추적된 일반 파일이어야 하며, worktree 모드는 작업공간 사본을, index 모드는
  스테이지된 blob을 읽습니다. 외부·미추적 목록을 환경변수로 주입해 검사를 우회할 수 없습니다.
- 값은 큰따옴표 한 쌍 안의 단일 행이며 큰따옴표·역슬래시·개행을 값에 허용하지 않습니다.
- 필드 순서와 들여쓰기는 위 계약 그대로입니다. 알 수 없는 줄·필드, 중복 필드, 항목 0개는 문법 오류입니다.
- `line_hash`는 줄 끝 개행을 제외한 정확한 바이트를 `git hash-object --stdin`에 넣은 값입니다.
- 같은 `path`와 `line_hash` 항목 수가 허용 가능한 동일 줄 수입니다. 항목 하나는 매치 하나만 소비합니다.

#### 실행 계약

```text
input:
  VERIFY_SCAN_SOURCE = "worktree" | "index"        # 그 밖의 값은 exit 2
  SECRET_PATTERNS_FILE = optional readable file     # 기존 계약 유지
  SECRET_ALLOWLIST_FILE = optional path             # 기본 .secret-allowlist.yaml
output:
  exit 0 = 탐지되지 않은 줄만 있거나 모든 탐지 줄이 유효 허용 항목을 각각 하나씩 소비
  exit 1 = 허용되지 않은 비밀 매치 또는 추적 .env 또는 기존 스캐너 실행 오류
  exit 2 = 패턴/허용 목록 없음·읽기 불가·빈 항목·문법 오류·필수 필드 오류·날짜 오류·만료
  stdout = 실제 매치 값은 출력하지 않고 경로와 판정 요약만 출력
```

→ 종료값 0은 정상 또는 정확한 한 줄 억제, 1은 실제 탐지, 2는 정책 자체가 신뢰 불가능한 상태로
서로 섞지 않습니다.

- 빈 파일과 항목 0개는 exit 2입니다. 허용할 것이 없더라도 주석만 둔 목록은 허용하지 않습니다.
- 최소 한 항목이 필요하며 최대 항목 수는 별도 제한하지 않습니다.
- 병렬 실행은 각 프로세스의 임시 파일과 메모리 안에서 독립적으로 허용 횟수를 소비합니다.
- 재시도는 상태를 저장하지 않으며 같은 입력은 같은 결과를 냅니다.
- 작업공간 파일 읽기와 커밋 직전 blob 읽기만 경계 함수에서 갈리고, 줄 매치·허용 소비 판정은 한 함수입니다.
- 추적 심볼릭 링크는 두 모드 모두 링크가 가리키는 파일이 아니라 Git blob의 링크 대상 문자열을 읽습니다.
- worktree 허용 목록 소스가 심볼릭 링크이면 외부 내용을 따라가지 않고 exit 2로 닫습니다.
- 정규식에 매치한 줄에 NUL이 있으면 Bash 문자열로 지문을 축약하지 않고 해당 경로를 exit 1로 차단합니다.

### 5. Harness 게이트와 작업 단위

- Gate 0 / PLAN: 기준 SHA, 과거 goal·이력·정본, 현재 분기와 형식 구멍 유예를 회수합니다.
- Gate 1 / PLAN: 사용자 요청을 이 단일 인수 기준과 counter-AC, 파일·실행 계약으로 고정합니다.
- Gate 2 / BUILD-RED: `scripts/acceptance-secret-allowlist.sh`를 먼저 만들고 `EXPECTED_CHECKS=22`를
  고정한 뒤 기능 부재 RED를 로컬 커밋으로 보존합니다.
- Gate 3 / BUILD-GREEN: RED 파일의 기대값·표본을 바꾸지 않고 스캐너 한 벌, 허용 목록, 만료 검사,
  기존 시험의 필수 복사 배선만 최소 변경합니다.
- Gate 3.5 / BUILD: `verify.sh` → 두 내용 공급 경계 → 공통 줄 판정 함수 → 허용 소비의 실제 호출을 추적합니다.
- Gate 4 / AUDIT: 원 명령, 두 모드, 실제 오탐 2건, 종단 스캔, P13 차단/통과, 명부 죽은 target,
  계약값 44/17/0, 파일·함수 한도 경계, 네 가지 뮤테이션을 실행합니다.
- Gate 5 / CHECKPOINT: 로컬 안전 커밋과 되돌림 절차를 보존하고 V1·V2·codeaudit 판정을 대조합니다.
- Gate 6 / SHIP: 사용자 금지에 따라 push·PR·merge는 수행하지 않습니다.

### 6. R2~R5와 적대검증 정조준

- R2: RED 파일의 기대값·표본을 Git diff로 고정하고, 허용 조회 제거·파일 단위 교체·만료 제거·한 모드
  우회를 저장소 밖 사본에 주입해 각각 지정 시험이 실패하는지 확인합니다.
- R3: 형식 구멍을 닫았다는 주장을 금지하고, 새 인용형 규칙을 저장소 밖에서만 조립해 현재 오탐
  개수만 측정합니다.
- R4: pre-commit의 index 호출과 CI의 worktree 호출이 같은 `verify.sh` 판정기를 거치는지 실행으로 확인합니다.
- R5: `omx explore`는 Rust 실행 파일 부재로 종료값 1이었으므로 반복하지 않고 일반 읽기 전용 조회로 전환했습니다.

정조준 항목은 허용 무제한 소비, 해시 대상 개행 차이, CRLF, 빈 마지막 줄, 파일명 공백·개행·선행하이픈,
심볼릭 링크, 추적 파일 삭제, grep 오류, 날짜 경계(오늘은 유효), 잘못된 달·일, 목록 자기매칭,
작업공간/index 부분 배선, CI 스텝 누락, P13 사유 대조 없는 위양성, 명부의 죽은 target입니다.

### 7. SOT와 비범위

직접 읽은 정본과 관련 문서:

- `docs/sot/coding-principles.md` — P3, P5, P11, P13, P15, P20, P22, V-1~V-5
- `docs/sot/principles.yaml` — 34개 strict/pre-push/CI 직접 로드 배선
- `docs/sot/hook-contracts.md` — pre-commit과 acceptance-0-7 입출력 계약
- `docs/sot/verification-commands.md` — 실제 CI 명령 표
- `docs/sot/mechanism-registry.yaml` — 장치 명부와 실제 target 대조 계약
- `docs/engineering/secret-short-value-goal-2026-09-03.md` — 선행 RED/GREEN 및 계약값 44/17/0
- `docs/engineering/secret-webhook-vendor-goal-2026-08-12.md` — 카나리 조립·무오염·자가 대조 계약
- `docs/engineering/gate0-unreachable-secret-scan-goal-2026-08-17.md` — 임시 저장소 Git 환경 격리 계약

비범위:

- `.secret-patterns.default` 또는 gitignored `.secret-patterns` 변경
- JSON/YAML 인용형, camelCase, 등호 공백, 여러 줄, base64, 하이픈 키, docker-compose 형식 탐지 추가
- `secret-format-gap` 억제 삭제
- 실제 비밀, 후보자 개인정보, 운영 데이터의 생성·출력·수정
- `main` reset/rebase, push, PR 생성, merge, 배포
- 대기열 2~5번 구현

### 8. 영향 반경·데이터 안전·롤백

영향 반경은 `verify.sh`를 부르는 수동 검사, pre-commit index 검사, pre-push 인수 묶음, CI verify job,
그리고 이를 검증하는 문서·장치 명부입니다. 제품 런타임과 데이터베이스에는 호출 경로가 없습니다.

데이터 안전 AC: When 인수·뮤테이션 시험이 파괴적 Git 조작과 가짜 값을 필요로 하면, 시스템은 저장소
밖 `mktemp -d` 아래의 독립 저장소에서 Git 환경변수를 제거한 뒤 실행하고, 시작과 끝의 원본 HEAD와
상태 지문이 같아야 합니다. 실제 비밀값은 생성·출력·저장하지 않습니다.

롤백은 이 작업의 로컬 커밋을 역순으로 `git revert <sha>` 하는 것입니다. 허용 목록 도입 커밋을
되돌리면 새 목록 파일과 모든 배선을 함께 되돌려, 필수 파일만 남거나 판정기만 남는 부분 적용을 막습니다.

### 9. 원칙 직접 로드 검증 장부

세션 식별자: `strict-secret-allowlist-20260905-30748`

| 시각 | 명령 | HEAD | 종료값 | 상태 |
|---|---|---|---:|---|
| 2026-09-05T00:07:01+09:00 | `sed -n '1,260p' docs/sot/coding-principles.md` | `8bb31ed` | 0 | PASS |
| 2026-09-05T00:07:07+09:00, 00:07:11+09:00 | `sed -n '1,320p'`와 `sed -n '321,380p' docs/sot/principles.yaml` | `8bb31ed` | 0, 0 | PASS |
| 2026-09-05T00:07:18+09:00 | `bash scripts/acceptance-principles-check.sh` | `8bb31ed` | 0 | PASS |

→ 원칙 정본과 기계 장부를 구현 전에 직접 읽었고, 같은 기준 SHA에서 배선 검사까지 통과했습니다.

직접 읽은 원문은 같은 HEAD의 추적 파일 전체이며, 재현 지문은 각각 Git blob
`b8122deae7192b714d9a35c5e2c6f96cadffde42`, `5e416a64bcb795c8668392f3d34f5c5dc402be84`입니다.

```text
VERDICT: PASS
SOT_LOAD: PASS docs/sot/coding-principles.md
LEDGER_LOAD: PASS docs/sot/principles.yaml
MECHANISMS: PASS 34/34 strict-contract-bindings
WIRING: PASS pre-push=1 ci=1
CHECKED: 34
EXIT_CODE=0
```

→ 무엇을 시켰나: 현재 기준 SHA에서 원칙 정본, 기계 장부, 실제 배선을 순서대로 직접 읽고 검사했습니다.
→ 뭐가 나왔나: 34개가 모두 존재하고 pre-push와 CI에 각각 한 번 연결됐으며 종료값 0이었습니다.
→ 좋은 소식인가 나쁜 소식인가: L3 작업을 시작할 자격은 통과했지만 새 기능의 합격 증거는 아직 아닙니다.

### 10. 검증 로그

#### 10-1. RED — 허용 목록 기능 부재와 기존 모드 갈림

시각 `2026-09-05T00:14:50+09:00`, HEAD `8bb31ed912869275b17579b8b2d8042f47098cea`에서
`bash scripts/verify/run-acceptance.sh scripts/acceptance-secret-allowlist.sh`를 실행했고 종료값은 1이었습니다.

```text
[1/22] 양성 대조군 탐지 (worktree) -> PASS (exit=1)
[2/22] 양성 대조군 탐지 (index) -> PASS (exit=1)
[3/22] 등재된 정확한 한 줄 (worktree) -> FAIL (expected=0 actual=1 scanner_error=0)
       FAIL: secret pattern matched in tracked files:
         - payload.txt
[4/22] 등재된 정확한 한 줄 (index) -> FAIL (expected=0 actual=1 scanner_error=0)
       FAIL: secret pattern matched in tracked files:
         - payload.txt
[5/22] 같은 파일의 같은 값 두 번째 줄 (worktree) -> PASS (exit=1)
[6/22] 같은 파일의 같은 값 두 번째 줄 (index) -> PASS (exit=1)
[7/22] 등재된 줄 한 글자 변경 (worktree) -> PASS (exit=1)
[8/22] 등재된 줄 한 글자 변경 (index) -> PASS (exit=1)
[9/22] 등재된 줄의 줄번호 이동 (worktree) -> FAIL (expected=0 actual=1 scanner_error=0)
       FAIL: secret pattern matched in tracked files:
         - payload.txt
[10/22] 등재된 줄의 줄번호 이동 (index) -> FAIL (expected=0 actual=1 scanner_error=0)
       FAIL: secret pattern matched in tracked files:
         - payload.txt
[11/22] expiry 누락 (worktree) -> FAIL (expected=2 actual=1 scanner_error=0)
       FAIL: secret pattern matched in tracked files:
         - payload.txt
[12/22] expiry 누락 (index) -> FAIL (expected=2 actual=1 scanner_error=0)
       FAIL: secret pattern matched in tracked files:
         - payload.txt
[13/22] expiry 만료 (worktree) -> FAIL (expected=2 actual=1 scanner_error=0)
       FAIL: secret pattern matched in tracked files:
         - payload.txt
[14/22] expiry 만료 (index) -> FAIL (expected=2 actual=1 scanner_error=0)
       FAIL: secret pattern matched in tracked files:
         - payload.txt
[15/22] 허용 목록 파일 없음 (worktree) -> FAIL (expected=2 actual=1 scanner_error=0)
       FAIL: secret pattern matched in tracked files:
         - payload.txt
[16/22] 허용 목록 파일 없음 (index) -> FAIL (expected=2 actual=1 scanner_error=0)
       FAIL: secret pattern matched in tracked files:
         - payload.txt
[17/22] 허용 목록 문법 위반 (worktree) -> FAIL (expected=2 actual=1 scanner_error=0)
       FAIL: secret pattern matched in tracked files:
         - payload.txt
[18/22] 허용 목록 문법 위반 (index) -> FAIL (expected=2 actual=1 scanner_error=0)
       FAIL: secret pattern matched in tracked files:
         - payload.txt
[19/22] 추적 심볼릭 링크의 바깥 내용은 비범위 (worktree) -> FAIL (expected=0 actual=1 scanner_error=0)
       FAIL: secret pattern matched in tracked files:
         - link.txt
[20/22] 추적 심볼릭 링크의 바깥 내용은 비범위 (index) -> PASS (exit=0)
MODE_MISMATCH: 추적 심볼릭 링크의 바깥 내용은 비범위 worktree=1 index=0
[21/22] 추적 심볼릭 링크의 저장 문자열은 탐지 (worktree) -> FAIL (expected=1 actual=1 scanner_error=1)
       FAIL: scanner error — fail-closed (grep/xargs stderr):
         ! grep: link.txt: No such file or directory
[22/22] 추적 심볼릭 링크의 저장 문자열은 탐지 (index) -> PASS (exit=1)
ALLOWED_LINES_COUNT=1
MODE_MISMATCH_COUNT=1
UNEXPECTED_MISSED_COUNT=0
CHECKED: 22
FAIL: AC-ALLOWLIST-1을 만족하지 못했다
FAIL(run-acceptance): scripts/acceptance-secret-allowlist.sh 종료값 1
RED_EXIT_CODE=1
```

→ 무엇을 시켰나: 새 기대 동작만 담은 인수 검사를 기존 판정기에 실행했습니다.
→ 뭐가 나왔나: 22회가 모두 실행됐고, 허용이 필요한 항목은 기존 판정 그대로 실패했으며 모드 갈림도 1건 재현됐습니다.
→ 좋은 소식인가 나쁜 소식인가: 구현 전 RED가 문법 문제가 아니라 요구한 동작 부재로 실패했으므로 시험 자격은 좋은 소식입니다.

#### 10-2. GREEN — 단일 줄 소비와 모드 동일성

시각 `2026-09-05T00:36:53+09:00`부터 `00:37:04+09:00`, HEAD `1b0439d` 위의 스테이지된
GREEN 후보에서 RED와 같은 원명령을 다시 실행했고 종료값은 0이었습니다. RED 커밋
`1b0439d` 이후 `scripts/acceptance-secret-allowlist.sh`의 기대값과 표본은 바꾸지 않았습니다.

```text
[1/22] 양성 대조군 탐지 (worktree) -> PASS (exit=1)
[2/22] 양성 대조군 탐지 (index) -> PASS (exit=1)
[3/22] 등재된 정확한 한 줄 (worktree) -> PASS (exit=0)
[4/22] 등재된 정확한 한 줄 (index) -> PASS (exit=0)
[5/22] 같은 파일의 같은 값 두 번째 줄 (worktree) -> PASS (exit=1)
[6/22] 같은 파일의 같은 값 두 번째 줄 (index) -> PASS (exit=1)
[7/22] 등재된 줄 한 글자 변경 (worktree) -> PASS (exit=1)
[8/22] 등재된 줄 한 글자 변경 (index) -> PASS (exit=1)
[9/22] 등재된 줄의 줄번호 이동 (worktree) -> PASS (exit=0)
[10/22] 등재된 줄의 줄번호 이동 (index) -> PASS (exit=0)
[11/22] expiry 누락 (worktree) -> PASS (exit=2)
[12/22] expiry 누락 (index) -> PASS (exit=2)
[13/22] expiry 만료 (worktree) -> PASS (exit=2)
[14/22] expiry 만료 (index) -> PASS (exit=2)
[15/22] 허용 목록 파일 없음 (worktree) -> PASS (exit=2)
[16/22] 허용 목록 파일 없음 (index) -> PASS (exit=2)
[17/22] 허용 목록 문법 위반 (worktree) -> PASS (exit=2)
[18/22] 허용 목록 문법 위반 (index) -> PASS (exit=2)
[19/22] 추적 심볼릭 링크의 바깥 내용은 비범위 (worktree) -> PASS (exit=0)
[20/22] 추적 심볼릭 링크의 바깥 내용은 비범위 (index) -> PASS (exit=0)
[21/22] 추적 심볼릭 링크의 저장 문자열은 탐지 (worktree) -> PASS (exit=1)
[22/22] 추적 심볼릭 링크의 저장 문자열은 탐지 (index) -> PASS (exit=1)
ALLOWED_LINES_COUNT=1
MODE_MISMATCH_COUNT=0
UNEXPECTED_MISSED_COUNT=0
CHECKED: 22
PASS: 줄 내용 허용 목록과 두 스캔 모드가 AC-ALLOWLIST-1을 만족한다
OK(run-acceptance): scripts/acceptance-secret-allowlist.sh — 판정 23건, CHECKED 22
EXIT_CODE=0
```

→ 무엇을 시켰나: RED에서 고정한 6항목×2모드와 심볼릭 링크 회귀를 구현 후 같은 래퍼로 실행했습니다.
→ 뭐가 나왔나: 허용 항목 하나가 한 매치만 소비했고, 내용 변경은 잡고 줄 이동은 허용했으며,
잘못된 억제는 exit 2로 닫혔고 모드 불일치는 0이었습니다.
→ 좋은 소식인가 나쁜 소식인가: AC-ALLOWLIST-1의 핵심인 파일 전체 면제 금지와 모드 동일성을
실행으로 만족했으므로 좋은 소식입니다.

#### 10-2a. 독립 검토 반례 추가 RED — 허용 목록 자기 억제

독립 구조 검토가 `0e98de3`에서 허용 목록이 자기 파일의 탐지 줄을 자기 지문으로 소비할 수 있는
반례를 재현했습니다. 기존 22개 기대값·표본은 한 줄도 바꾸지 않고, 런타임 조립 탐지값을
`reason`에 둔 자기 target 거부 시험만 두 모드에 추가했습니다. 따라서 `EXPECTED_CHECKS`는
22에서 24로 늘었으며 이는 추가만·기준 안 낮춤입니다.

시각 `2026-09-05T00:49:46+09:00`부터 `00:49:51+09:00`, HEAD `0e98de3`의 구현에 추가 시험을
실행한 결과입니다.

```text
[19/24] 허용 목록 자기 파일 target 거부 (worktree) -> FAIL (expected=2 actual=0 scanner_error=0)
       ALLOWED_LINES_COUNT=1
       ALLOWED_MATCHES_CONSUMED=1
[20/24] 허용 목록 자기 파일 target 거부 (index) -> FAIL (expected=2 actual=0 scanner_error=0)
       ALLOWED_LINES_COUNT=1
       ALLOWED_MATCHES_CONSUMED=1
MODE_MISMATCH_COUNT=0
UNEXPECTED_MISSED_COUNT=0
CHECKED: 24
FAIL: AC-ALLOWLIST-1을 만족하지 못했다
ADVERSARIAL_RED_EXIT=1
```

→ 무엇을 시켰나: 목록 자신을 target으로 삼아 목록 안의 탐지 줄을 소비하려는 반례를 양 모드에
추가했습니다.
→ 뭐가 나왔나: 두 모드 모두 자기 매치 한 건을 소비해 exit 0으로 통과했고, 시험 전체는 기대 exit 2와
달라 RED가 됐습니다.
→ 좋은 소식인가 나쁜 소식인가: 구현에는 자기제외 구멍이 있어 나쁜 소식이지만, 독립 검토가 이를
커밋 전에 재현 가능한 RED로 고정한 것은 좋은 소식입니다.

같은 검토자가 `8dadafd`에서 `SECRET_ALLOWLIST_FILE=./.secret-allowlist.yaml` 별칭으로 위 거부를
우회하는 두 번째 반례를 재현했습니다. 기존 24개는 그대로 두고 별칭의 두 모드만 추가해
`EXPECTED_CHECKS`를 26으로 올렸습니다. 이 역시 추가만·기준 안 낮춤입니다.

```text
START=2026-09-05T00:54:49+09:00
[21/26] 허용 목록 자기 파일 경로 별칭 거부 (worktree) -> FAIL (expected=2 actual=0 scanner_error=0)
[22/26] 허용 목록 자기 파일 경로 별칭 거부 (index) -> FAIL (expected=2 actual=0 scanner_error=0)
       ALLOWED_MATCHES_CONSUMED=1
CHECKED: 26
ALIAS_RED_EXIT=1
END=2026-09-05T00:55:01+09:00
```

→ 무엇을 시켰나: 선택 파일과 실제 파일은 같지만 원시 경로 문자열만 다른 별칭으로 자기 target을
다시 시도했습니다.
→ 뭐가 나왔나: 두 모드 모두 자기 매치를 한 건 소비하고 exit 0으로 통과해 새 기대 exit 2와 달랐습니다.
→ 좋은 소식인가 나쁜 소식인가: 첫 수정이 문자열 동치만 막은 불완전한 방어였으므로 나쁜 소식이며,
동치 경로 반례가 재현 가능한 RED로 추가된 것은 좋은 소식입니다.

#### 10-2b. V2 반례 추가 RED/GREEN — 외부 허용 정책 심볼릭 링크

읽기 전용 V2가 `96e80a9`에서 추적 일반 허용 목록의 worktree 사본만 저장소 밖 파일을 가리키는
심볼릭 링크로 바꾸면 `-f/-r/-s`와 `cat`이 외부 정책을 신뢰한다는 BLOCK을 찾았습니다. 기존
26개는 바꾸지 않고 두 스캔 소스의 허용 목록 심볼릭 링크 거부 2개만 더해 `EXPECTED_CHECKS=28`로
올렸습니다. 커밋 `366a259`의 메시지에 `추가만·기준 안 낮춤`과 기존 표본 불변을 기록했습니다.

```text
[23/28] worktree 허용 목록 외부 심볼릭 링크 거부 (worktree) -> FAIL (expected=2 actual=0 scanner_error=0)
[24/28] index 허용 목록 심볼릭 링크 거부 (index) -> PASS (exit=2)
ALLOWED_LINES_COUNT=1
MODE_MISMATCH_COUNT=0
UNEXPECTED_MISSED_COUNT=0
CHECKED: 28
SYMLINK_SOURCE_RED_EXIT=1
```

→ 무엇을 시켰나: 인덱스에는 일반 파일이지만 worktree에서는 외부 파일을 가리키는 허용 목록과,
index 자체에 심볼릭 링크가 저장된 경우를 각각 실행했습니다.
→ 뭐가 나왔나: index는 이미 닫혔지만 worktree는 외부 정책을 읽고 exit 0으로 통과해 RED였습니다.
→ 좋은 소식인가 나쁜 소식인가: 외부 정책 주입 가능성은 나쁜 소식이며, `-L` 거부 뒤 같은 28개가
전부 GREEN이 되어 우회를 닫은 것은 좋은 소식입니다.

#### 10-2c. V1·codeaudit 반례 추가 RED/GREEN — NUL 바이트 지문 축약

V1과 codeaudit는 `96e80a9`에서 `/usr/bin/grep -a`가 반환한 매치 줄을 Bash 변수로 읽을 때 NUL이
보존되지 않아 다른 바이트열이 기존 허용 지문을 소비할 수 있다는 BLOCK을 각각 독립 보고했습니다.
외부 정책 링크 수정 뒤의 기존 28개는 그대로 두고, 허용된 텍스트 끝에 NUL 한 바이트를 더한 양 모드
2개만 추가해 `EXPECTED_CHECKS=30`으로 올렸습니다. 커밋 `d08a454`도
`추가만·기준 안 낮춤`을 명시합니다.

```text
[25/30] 등재된 줄 끝 NUL 한 바이트 추가 (worktree) -> FAIL (expected=1 actual=0 scanner_error=0)
[26/30] 등재된 줄 끝 NUL 한 바이트 추가 (index) -> FAIL (expected=1 actual=0 scanner_error=0)
ALLOWED_LINES_COUNT=1
MODE_MISMATCH_COUNT=0
UNEXPECTED_MISSED_COUNT=2
CHECKED: 30
NUL_BYTE_RED_EXIT=1
```

→ 무엇을 시켰나: 완성 카나리를 저장소 밖 fixture에서만 조립하고 끝에 NUL 한 바이트를 추가해,
원래 텍스트 지문이 소비되는지 두 모드로 확인했습니다.
→ 뭐가 나왔나: 두 모드 모두 기존 지문을 소비해 exit 0으로 놓쳤으므로 정확한 바이트 결속이 RED였습니다.
→ 좋은 소식인가 나쁜 소식인가: 보안 계약 위반은 나쁜 소식이며, 매치 결과에 NUL이 있으면 지문 판정
전에 경로를 exit 1로 차단한 뒤 30개가 전부 GREEN이 된 것은 좋은 소식입니다.

#### 10-2d. 최종 V1 반례 추가 RED/GREEN — 대체 경로 상위 링크

최종 V1은 `dd9d032`의 구현을 PASS로 판정하면서도, 환경변수로 선택한 중첩 허용 목록의 상위
디렉터리가 외부 심볼릭 링크일 때 마지막 파일의 `-L` 검사만으로는 외부 정책을 구분하지 못한다는
LOW 잔여 위험을 남겼습니다. 이는 목표 문서의 외부 정책 주입 금지 계약과 충돌하므로 기존 30개를
바꾸지 않고 worktree 반례 한 개만 더해 `EXPECTED_CHECKS=31`로 올렸습니다. 커밋 `e5fa5af`는
`추가만·기준 안 낮춤`을 명시합니다.

```text
[25/31] worktree 허용 목록 상위 외부 심볼릭 링크 거부 (worktree) -> FAIL (expected=2 actual=0 scanner_error=0)
ALLOWED_LINES_COUNT=1
MODE_MISMATCH_COUNT=0
UNEXPECTED_MISSED_COUNT=0
CHECKED: 31
PARENT_SYMLINK_RED_EXIT=1
```

→ 무엇을 시켰나: 추적된 중첩 허용 목록을 커밋한 뒤 상위 디렉터리만 저장소 밖 경로를 가리키는
링크로 교체해 worktree 모드를 실행했습니다.
→ 뭐가 나왔나: 외부 정책을 읽어 exit 0으로 통과했으므로 기대 exit 2와 달라 RED였습니다.
→ 좋은 소식인가 나쁜 소식인가: 기본 루트 경로에는 없던 낮은 위험이지만 명시 계약 위반은 나쁜
소식이며, 모든 경로 구성요소의 링크를 거부한 `999f46f` 뒤 31개가 GREEN이 된 것은 좋은 소식입니다.

최종 기능 HEAD `999f46f`에서 원명령의 전체 결론은 다음과 같습니다.

```text
[1/31] 양성 대조군 탐지 (worktree) -> PASS (exit=1)
[2/31] 양성 대조군 탐지 (index) -> PASS (exit=1)
[3/31] 등재된 정확한 한 줄 (worktree) -> PASS (exit=0)
[4/31] 등재된 정확한 한 줄 (index) -> PASS (exit=0)
[5/31] 같은 파일의 같은 값 두 번째 줄 (worktree) -> PASS (exit=1)
[6/31] 같은 파일의 같은 값 두 번째 줄 (index) -> PASS (exit=1)
[7/31] 등재된 줄 한 글자 변경 (worktree) -> PASS (exit=1)
[8/31] 등재된 줄 한 글자 변경 (index) -> PASS (exit=1)
[9/31] 등재된 줄의 줄번호 이동 (worktree) -> PASS (exit=0)
[10/31] 등재된 줄의 줄번호 이동 (index) -> PASS (exit=0)
[11/31] expiry 누락 (worktree) -> PASS (exit=2)
[12/31] expiry 누락 (index) -> PASS (exit=2)
[13/31] expiry 만료 (worktree) -> PASS (exit=2)
[14/31] expiry 만료 (index) -> PASS (exit=2)
[15/31] 허용 목록 파일 없음 (worktree) -> PASS (exit=2)
[16/31] 허용 목록 파일 없음 (index) -> PASS (exit=2)
[17/31] 허용 목록 문법 위반 (worktree) -> PASS (exit=2)
[18/31] 허용 목록 문법 위반 (index) -> PASS (exit=2)
[19/31] 허용 목록 자기 파일 target 거부 (worktree) -> PASS (exit=2)
[20/31] 허용 목록 자기 파일 target 거부 (index) -> PASS (exit=2)
[21/31] 허용 목록 자기 파일 경로 별칭 거부 (worktree) -> PASS (exit=2)
[22/31] 허용 목록 자기 파일 경로 별칭 거부 (index) -> PASS (exit=2)
[23/31] worktree 허용 목록 외부 심볼릭 링크 거부 (worktree) -> PASS (exit=2)
[24/31] index 허용 목록 심볼릭 링크 거부 (index) -> PASS (exit=2)
[25/31] worktree 허용 목록 상위 외부 심볼릭 링크 거부 (worktree) -> PASS (exit=2)
[26/31] 등재된 줄 끝 NUL 한 바이트 추가 (worktree) -> PASS (exit=1)
[27/31] 등재된 줄 끝 NUL 한 바이트 추가 (index) -> PASS (exit=1)
[28/31] 추적 심볼릭 링크의 바깥 내용은 비범위 (worktree) -> PASS (exit=0)
[29/31] 추적 심볼릭 링크의 바깥 내용은 비범위 (index) -> PASS (exit=0)
[30/31] 추적 심볼릭 링크의 저장 문자열은 탐지 (worktree) -> PASS (exit=1)
[31/31] 추적 심볼릭 링크의 저장 문자열은 탐지 (index) -> PASS (exit=1)
ALLOWED_LINES_COUNT=1
MODE_MISMATCH_COUNT=0
UNEXPECTED_MISSED_COUNT=0
CHECKED: 31
PASS: 줄 내용 허용 목록과 두 스캔 모드가 AC-ALLOWLIST-1을 만족한다
```

→ 무엇을 시켰나: 최초 22개, 자기 target 2개, 경로 별칭 2개, 허용 목록 소스 링크 2개,
상위 링크 1개, NUL 경계 2개를 한 원명령에서 실행했습니다.
→ 뭐가 나왔나: 31개 모두 기대 종료값과 일치했고 두 모드 불일치와 예상 밖 누락이 0이었습니다.
→ 좋은 소식인가 나쁜 소식인가: AC-ALLOWLIST-1과 독립 검토에서 새로 드러난 두 BLOCK 및 한 LOW를 함께 닫았으므로
좋은 소식입니다.

#### 10-3. 실제 항목·규칙 비변경·현재 오탐 실측

- `.secret-allowlist.yaml`에 요청된 두 경로의 현재 정확한 줄 지문을 등재했고, 각 지문을 원문에서
  다시 계산한 결과 모두 일치했습니다. 원문 값은 로그에 출력하지 않았습니다.
- `.secret-patterns.default`의 HEAD blob과 작업공간 blob은 모두
  `5541a33a6b96ba0e16d8680dfe4154779968ecab`로 같아 탐지 규칙 변경은 0줄입니다.
- 저장소 밖 임시 규칙에서 먼저 조립한 양성 대조군이 `/usr/bin/grep`에 CAUGHT됨을 확인한 뒤,
  인용형 규칙의 키워드 집합만 세 이름으로 확장해 index blob 229개를 측정했습니다.

```text
POSITIVE_CONTROL=CAUGHT
MATCH_PATH=docs/engineering/humansearch-v6-founding-spec-2026-08-07.md MATCH_LINES=1
MATCH_PATH=scripts/acceptance-secret-webhook-vendor.sh MATCH_LINES=1
QUOTED_RULE_CURRENT_MATCHES=2
SCANNER_ERRORS=0
```

→ 이 결과는 규칙을 켰다는 뜻이 아닙니다. 이번 작업은 두 오탐을 정확한 줄 내용에 묶는 예외 경로만
만들었고, 인용형·camelCase·docker-compose 형식 구멍 본체는 `secret-format-gap`에 그대로 남습니다.

#### 10-4. 영향 회귀 중간 증거

- 실제 저장소 종단: worktree/index 각각 `ALLOWED_LINES_COUNT=2`, `ALLOWED_MATCHES_CONSUMED=0`,
  추적 파일 매치 0, 스캐너 오류 0, exit 0.
- `acceptance-0-2-unreachable-content.sh`: `CHECKED: 13`, exit 0.
- `acceptance-hs-a3.sh`: `CHECKED: 25`, exit 0.
- `acceptance-hs-a4.sh`: `CHECKED: 30`, exit 0.
- `acceptance-secret-webhook-vendor.sh`: `CHECKED: 44`, `UNCOVERED_BASELINE_RULES=17`,
  `OLD_CAUGHT_AND_NEW_MISSED_COUNT=0`, exit 0.
- `acceptance-verify-ac-m.sh`: 새 target 되돌림이 죽은 target으로 실패했고, 실제 명부 18건이
  일치했으며 `CHECKED: 32`, exit 0.

최종 로컬 재실행에서도 다음 계약값이 유지됐습니다.

```text
acceptance-0-7.sh: BLOCKED 8/8, 정확 사유 일치 8/8, 정상 통과쌍 2/2, exit 0
acceptance-0-2-unreachable-content.sh: CHECKED 13, exit 0
acceptance-principles-check.sh: CHECKED 34, MECHANISMS 34/34, exit 0
acceptance-secret-webhook-vendor.sh: CHECKED 44, UNCOVERED_BASELINE_RULES=17,
  OLD_CAUGHT_AND_NEW_MISSED_COUNT=0, exit 0
acceptance-verify-ac-m.sh: CHECKED 32, 명부 18/18, 죽은 target mutation RED, exit 0
```

→ 무엇을 시켰나: 새 억제 파일이 훅·원칙·명부·기존 비밀 탐지 계약을 약화하지 않았는지 각 원명령을
다시 실행했습니다.
→ 뭐가 나왔나: P13은 새 파일 약화를 정확한 사유로 막고 정상 변경은 통과시켰으며, 요구된 44·17·0과
명부 mutation 계약이 그대로였습니다.
→ 좋은 소식인가 나쁜 소식인가: 기존 방어가 새 예외 경로 때문에 약해지지 않았으므로 좋은 소식입니다.

기존 `acceptance-0-2.sh` 직접 실행은 이 저장소에 이미 존재하던 장시간 히스토리 검사에서 약 3분 동안
끝나지 않아 종료값 130으로 중단했습니다. 같은 범위의 CI 계약인 AC-19
`acceptance-0-2-unreachable-content.sh`는 13/13으로 통과했고, no-local CI의 데이터 노출 기록 스캔도
통과했습니다. 이 실패한 첫 시도를 숨기지 않으며, 레거시 스크립트 자체의 성능 원인은 이번 변경의
비범위로 남깁니다.

#### 10-5. 외부 사본 뮤테이션 감사

시각 `2026-09-05T01:18+09:00`, HEAD `f84a4ac4ea83c19edc9846e2db19d57a2640b11b`를
네 번 `git clone --no-local --single-branch`한 저장소 밖 경로
`/var/folders/4h/jphmynjn2jl54cqy8d_ddhkh0000gn/T/tmp.PADpY6pGVN`에서 판정기를 한 축씩 망가뜨렸습니다.

```text
MUTATION_A_RC=1
[3/30] 등재된 정확한 한 줄 (worktree) -> FAIL (expected=0 actual=1 scanner_error=0)
[4/30] 등재된 정확한 한 줄 (index) -> FAIL (expected=0 actual=1 scanner_error=0)

MUTATION_B_RC=1
[5/30] 같은 파일의 같은 값 두 번째 줄 (worktree) -> FAIL (expected=1 actual=0 scanner_error=0)
[6/30] 같은 파일의 같은 값 두 번째 줄 (index) -> FAIL (expected=1 actual=0 scanner_error=0)

MUTATION_C_RC=1
[13/30] expiry 만료 (worktree) -> FAIL (expected=2 actual=0 scanner_error=0)
[14/30] expiry 만료 (index) -> FAIL (expected=2 actual=0 scanner_error=0)

MUTATION_D_RC=1
[4/30] 등재된 정확한 한 줄 (index) -> FAIL (expected=0 actual=1 scanner_error=0)
MODE_MISMATCH: 등재된 정확한 한 줄 worktree=0 index=1

ALLOWED_LINES_COUNT=1
UNEXPECTED_MISSED_COUNT=0  # A·C·D; B는 의도한 파일 면제로 8건 누락되어 suite가 RED
CHECKED: 30
```

→ 무엇을 시켰나: (a) 허용 조회 제거, (b) 줄 내용 고정을 파일명 고정으로 교체, (c) expiry 검사를
제거, (d) index 모드에서만 허용 소비를 끄는 네 뮤테이션을 각각 독립 사본에 주입했습니다.
→ 뭐가 나왔나: A는 정확 허용, B는 핵심 ② 중복 줄, C는 만료, D는 모드 동일성에서 모두 exit 1 RED였습니다.
→ 좋은 소식인가 나쁜 소식인가: 각 검사가 요구한 잘못된 구현을 실제로 구별했으므로 좋은 소식입니다.
운영 GREEN 원명령의 `UNEXPECTED_MISSED_COUNT`는 0이며, B의 8은 의도적으로 파일 면제를 넣은 사본이
놓친 대조군 수라서 뮤테이션 판별 증거입니다.

#### 10-6. no-local CI 재현

시각 `2026-09-05T01:20+09:00`, HEAD `f84a4ac4ea83c19edc9846e2db19d57a2640b11b`를
`git clone --no-local --single-branch --branch task/secret-allowlist-line-scope`로 저장소 밖
`/var/folders/4h/jphmynjn2jl54cqy8d_ddhkh0000gn/T/tmp.tg0CPGbOow/ci-clone`에 복제했습니다.
로컬 객체 저장소 공유는 사용하지 않았습니다.

```text
CI_REPRO_HEAD=f84a4ac4ea83c19edc9846e2db19d57a2640b11b
CI_REPRO[01] PASS secret-scan
CI_REPRO[02] PASS principles-check
CI_REPRO[03] PASS principles-mutations
CI_REPRO[04] PASS unreachable-content
CI_REPRO[05] PASS hook-0-7
CI_REPRO[06] PASS hs-a3
CI_REPRO[07] PASS data-exposure
CI_REPRO[08] PASS hs-a4
CI_REPRO[09] PASS webhook-vendor
CI_REPRO[10] PASS secret-allowlist
CI_REPRO[11] PASS ci-step-integrity
CI_REPRO[12] PASS semantic-mutations
CI_REPRO[13] PASS mechanism-registry
CI_REPRO[14] PASS shell-syntax
CI_REPRO[15] PASS suppression-expiry
CI_REPRO_CHECKED=15
CI_REPRO_FAIL=0
```

→ 무엇을 시켰나: 변경이 영향을 주는 CI 명령 15개를 객체를 공유하지 않는 단일 브랜치 복제본에서
순서대로 실행했습니다.
→ 뭐가 나왔나: 15개 모두 exit 0이고 실패는 0이었습니다. 로그는 위 scratch의 `ci-logs/`에 있습니다.
→ 좋은 소식인가 나쁜 소식인가: 다른 worktree의 폐기 객체 때문에 생기는 허위 실패 없이 현재 SHA의
로컬 CI 경로가 모두 통과했으므로 좋은 소식입니다. 실제 GitHub 원격 CI는 push 금지 때문에 실행하지
않았습니다.

#### 10-7. 종단·규칙·크기 경계

```text
worktree: ALLOWED_LINES_COUNT=2, ALLOWED_MATCHES_CONSUMED=0, exit 0
index:    ALLOWED_LINES_COUNT=2, ALLOWED_MATCHES_CONSUMED=0, exit 0
PATTERN_RULE_DIFF_LINES=0
PATTERN_BASE_BLOB=5541a33a6b96ba0e16d8680dfe4154779968ecab
PATTERN_HEAD_BLOB=5541a33a6b96ba0e16d8680dfe4154779968ecab
ALLOWLIST_ENTRY founding-spec hash_matches=1
ALLOWLIST_ENTRY webhook-vendor hash_matches=1
SHELL_SYNTAX=PASS
FILE_LIMIT=PASS max=581 hard=600
FUNCTION_LIMIT=PASS max=51 hard=100
DIFF_LIMIT=PASS changed_lines=1626 hard=3000
```

→ 무엇을 시켰나: 실제 저장소 양 모드 종단, 규칙 blob, 두 운영 지문, 셸 문법, P11 코드 경계를
직접 대조했습니다.
→ 뭐가 나왔나: 추적 파일 매치와 스캐너 오류는 0, 허용 항목은 2개지만 소비는 0, 규칙 변경은 0줄,
두 지문은 각각 정확히 한 줄과 일치했습니다. 코드 파일·함수·전체 diff도 hard 한도 이내였습니다.
→ 좋은 소식인가 나쁜 소식인가: 탐지 규칙을 늘리지 않고 예외 경로만 추가했다는 범위와 안전 경계가
일치하므로 좋은 소식입니다. goal 증거 문서 추가 뒤 diff 수치는 최종 재계산합니다.

#### 10-8. 독립 판정 이력과 재시도

첫 V1/V2/codeaudit는 기능 HEAD `96e80a9`를 읽고 실행했으며, 읽기 전용 sandbox가 `mktemp`를
막아 실행형 검사는 `NOT_RUN`으로 분리했습니다. 최초 백그라운드 V1 시도는 터미널 HUP로 본문을
남기지 못해, 사용자 지정 명령에 `< /dev/null`을 붙인 지속 세션으로 재시도했습니다.

세 판정은 다음 두 BLOCK을 실제로 찾았습니다.

1. worktree 허용 목록의 외부 심볼릭 링크 정책 주입 — V2와 codeaudit가 보고, `366a259` RED 뒤
   `cb57655`에서 수정했습니다.
2. 매치 줄 NUL 바이트의 Bash 변수 축약 — V1과 codeaudit가 보고, `d08a454` RED 뒤
   `4822440`에서 수정했습니다.

초기 판정 본문은 저장소 밖 scratch에 보존했습니다.

- V1: `/var/folders/4h/jphmynjn2jl54cqy8d_ddhkh0000gn/T/tmp.IhUV0vGgTN/v1-codex-verdict.txt`
- V2: `/var/folders/4h/jphmynjn2jl54cqy8d_ddhkh0000gn/T/tmp.IhUV0vGgTN/v2-codex-verdict.txt`
- codeaudit: `/var/folders/4h/jphmynjn2jl54cqy8d_ddhkh0000gn/T/tmp.IhUV0vGgTN/codeaudit-verdict.txt`

→ 무엇을 시켰나: 서로 다른 새 Codex 맥락에 구조·바이트·증거 사슬을 공격하게 하고 codeaudit에는
요구사항과 전체 diff를 별도로 대조하게 했습니다.
→ 뭐가 나왔나: 세 판정 모두 당시에는 FAIL이었고, 겹치는 두 BLOCK은 추가 RED와 GREEN 커밋으로
재현·수정됐습니다. 증거 미기록 지적은 §10-5~§10-7에 채웠습니다.
→ 좋은 소식인가 나쁜 소식인가: 첫 판정 실패 자체는 나쁜 소식이지만 결함을 숨기지 않고 시험과 코드로
닫았으므로 유효한 적대검증이었습니다.

증거 커밋 `dd9d032`에서 다시 실행한 V1과 codeaudit는 모두 PASS였고 BLOCK/HIGH를 CLEAR로
판정했습니다. 본문은 다음 저장소 밖 파일에 있습니다.

- V1 PASS: `/var/folders/4h/jphmynjn2jl54cqy8d_ddhkh0000gn/T/tmp.IhUV0vGgTN/final-v1-codex-verdict.txt`
- codeaudit PASS: `/var/folders/4h/jphmynjn2jl54cqy8d_ddhkh0000gn/T/tmp.IhUV0vGgTN/final-codeaudit-verdict.txt`

V1의 유일한 구현 잔여 위험은 대체 중첩 경로의 상위 디렉터리 링크였습니다. PASS 안의 LOW였지만
문서 계약보다 약한 상태를 남기지 않고 `e5fa5af` RED와 `999f46f` GREEN으로 닫았습니다. 이 마지막
코드 변경 뒤의 V1·V2·codeaudit를 다시 실행해 최종 본문 경로와 판정 대조를 이어서 기록합니다.

### 11. 제출 직전 사람 감사

| 질문 | 판정 | 근거 |
|---|---|---|
| 결론에 전문용어가 있나? | 아니오 | 1층 결론은 한 줄 예외와 파일 전체 면제의 차이를 일상어로 설명합니다. |
| `→` 해석 없는 출력·코드·표가 있나? | 아니오 | 실행 출력과 핵심 표 뒤에 무엇·결과·좋고 나쁨을 붙였습니다. |
| 결론에 결정할 사항이 빠졌나? | 아니오 | 로컬 완료, 형식 규칙 비범위, 원격 작업 금지를 명시했습니다. |
| 결정에 버린 길·대가가 빠졌나? | 아니오 | 결정 카드에 파일 면제·줄번호·원문 저장 기각과 지문 갱신 비용을 기록했습니다. |
| `file:line`의 역할 설명이 빠졌나? | 아니오 | 위치를 쓴 곳마다 오탐 줄·기존 파일명 출력·suppression 역할을 함께 적었습니다. |
| 쉽게 쓰며 증거·수치·한계를 뺐나? | 아니오 | 31개, 44·17·0, 15개 CI, 두 BLOCK과 한 LOW, 비범위를 수치로 남겼습니다. |
| 초등학생 비유로 내용을 깎았나? | 아니오 | 비유 없이 계약과 실행 결과를 그대로 설명했습니다. |
| 건너뜀·미확인·실패 후 재시도가 앞부분에서 빠졌나? | 아니오 | 레거시 0-2 중단, V1 HUP 재시도, 원격 CI 미실행을 명시했습니다. |
| 추정을 확인된 사실처럼 썼나? | 아니오 | 실행 증거, 코드 기반 판단, 원격 미확인을 분리했습니다. |

→ 무엇을 시켰나: strict §8-6b의 아홉 문항을 제출 직전 사람 눈으로 다시 판정했습니다.
→ 뭐가 나왔나: 아홉 항목 모두 `아니오`이며 각 판단 근거를 표에 남겼습니다.
→ 좋은 소식인가 나쁜 소식인가: 문서 누락을 기계 검사와 별개로 다시 확인했으므로 좋은 소식입니다.
