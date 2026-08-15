# 파일 500줄 게이트 — goal 문서 (2026-08-15)

> 위험 등급 L3 (SOT 수정 + 공유 검사 장치 신설 — 자동 승격 트리거 해당) / 마스터플랜 `docs/engineering/humansearch-journey-master-plan-2026-08-14.md` §4·§11의 "강제 장치가 먼저다" 이행

## 사장님 브리핑 (§1⑪ — 1·2층)

**결론.** 사장님이 정하신 "코드 한 파일 500줄 초과 금지" 규칙을 사람이 세지 않아도 자동으로 검사하는 장치를 만듭니다. 지금 만들어 두면 앞으로 서치·등록·보고 코드가 늘어날 때마다 기계가 위반을 실패로 표시합니다. 현재 합치기 차단은 사람 검토가 맡으며, 결정하실 사항은 없습니다.

**왜 지금인가.** 마스터플랜의 파일 분할표(부품 20여 개)는 약속일 뿐이고, 약속은 코드가 커지는 순간부터 어겨집니다. 코드가 아직 작을 때(현재 제품 파일 1개) 장치를 먼저 깔아야 규칙이 처음부터 지켜집니다. 이 저장소의 확정 원칙("원칙은 문서가 아니라 CI에 둔다")과 같은 방향입니다.

**틀리면 뭐가 깨지나.** 이 검사가 헐거우면(예: 검사할 파일이 하나도 안 걸리는데 합격 처리) 500줄 규칙은 있으나 마나가 됩니다. 그래서 "0개 검사 = 불합격" 장치를 함께 박습니다.

---

## 3층 — 기술 본문

### ① 현재 상태 (증거)

- 제품 코드 디렉토리 중 존재하는 것: `humansearch/src` (파이썬 파일 1개 — `humansearch/src/humansearch/__init__.py`). `extension/src`, `bot/src`는 아직 없음 (2026-08-15 실측).
- `humansearch/.venv/`(외부 라이브러리 설치 폴더)가 `humansearch/` 밑에 있으므로, 검사 범위를 `src` 밑으로 한정하지 않으면 남의 코드를 세는 오탐이 난다.
- 500줄 규칙을 강제하는 검사는 현재 저장소에 없다 (`scripts/` 목록 실측 — `acceptance-file-size.sh` 부재).

### ② 근본 원인

규칙이 문서(마스터플랜 §4)에만 있고 집행 장치가 없다.

**V2 후속 보수(2026-08-15).** 소스 확장자 선택이 소문자 패턴만 받고, 줄 수 계산이 LF만 구분자로 취급한다. 그 결과 대문자·혼합 확장자와 CR 전용 개행은 원격 검사에서도 빠진다(`.claude/private-reviews/claude-file-size-v2-2026-08-15.md` A-1·A-2).

### ③ 인수 기준 (EARS + 검증 명령 + counter-AC)

**AC-FS1.** When 제품 코드 디렉토리(`humansearch/src`, `extension/src`, `bot/src` 중 존재하는 것)의 소스 파일(`*.py`, `*.ts`, `*.tsx`, `*.js`, `*.sh`) 중 하나라도 500줄을 초과하면, `scripts/acceptance-file-size.sh`는 초과 파일 목록을 출력하고 exit 1로 끝나야 한다.
- 검증: 501줄짜리 임시 파일을 `humansearch/src` 밑에 두고 실행 → exit 1 확인 후 제거.
- counter-AC: 500줄 초과 파일이 있는데 exit 0이면 가짜. `.venv`·`tests`·문서 파일을 세서 오탐해도 가짜.

**AC-FS2.** If 검사 대상 파일이 0개이면, then exit 1로 끝나야 한다 (0개 통과 함정 차단 — 게이트 설계 3원칙).
- 검증: 대상 글로브를 임시로 존재하지 않는 확장자로 바꾼 사본 실행 → exit 1.
- counter-AC: 대상 디렉토리가 전부 사라져도 "검사할 게 없어 합격"이면 가짜.

**AC-FS3.** 배선 — pre-push 글로브(`acceptance-*.sh` 자동 수집)에 걸리고, CI(`.github/workflows/verify.yml`)의 실제 실행 단계(run 칸)에 등록되고, 검사 장치 명부(`docs/sot/mechanism-registry.yaml`)와 `docs/sot/verification-commands.md` 표에 같은 PR로 등재되어야 한다.
- 검증: `bash scripts/verify/check-mechanism-registry.sh` exit 0 + 명부 diff 존재.
- counter-AC: CI에 문자열만 있고 실행 단계에 없으면 가짜(G3 F1과 같은 함정). 명부 미등재면 AC-M 대조기가 빨간불이어야 한다.

**AC-FS4.** 소스 확장자 5종(`.py`, `.ts`, `.tsx`, `.js`, `.sh`)은 대소문자를 구분하지 않아야 한다. 그러므로 `.PY`·`.TsX`·`.Sh` 등의 501줄 파일도 exit 1로 차단한다.
- 검증: 대문자·혼합 확장자 5종의 501줄 임시 파일을 추적하고 실행 → 5개 전부 초과 목록 + exit 1.
- counter-AC: 같은 내용의 `.py`는 막히지만 `.PY`는 검사 대상에서 빠지면 가짜.

**AC-FS5.** 파일 내용에 LF가 바로 뒤따르지 않는 CR(bare CR)이 하나라도 있으면 줄 수를 신뢰할 수 없으므로 검사 불능 문구를 출력하고 exit 2로 끝나야 한다. bare CR이 없으면 LF를 줄 구분자로 신뢰하며, 순수 LF·순수 CRLF·두 형식의 혼합 모두 기존 경계값 판정이 바뀌지 않아야 한다.
- 검증: CR만으로 구분한 501줄 임시 파일과 `499 CRLF + 1 bare CR + 1 CRLF` 혼합 501줄 임시 파일 → exit 2. LF·CRLF 각각 500줄 → exit 0, 501줄 → exit 1.
- counter-AC: bare CR이 든 파일을 LF 개수만으로 세어 exit 0이면 가짜. bare CR이 없는 정상 LF·CRLF 및 두 형식의 혼합 파일까지 검사 불능으로 막으면 오탐.

### ④ Harness 게이트 계획

워크트리 `worktrees/file-size-gate`(브랜치 `task/file-size-gate`)에서 RED(위 counter-AC를 재현하는 실패 시험) 커밋 → GREEN(검사기 구현) → verify → PR. 구현은 codex에 위임(G=codex), V1=별도 codex 세션, V2=Claude.

### ⑤ codex 적대검증 정조준

⑴ 0개 통과 함정 ⑵ `.venv`·심볼릭 링크 경유 오탐/미탐 ⑶ CI 문자열-실행 불일치(G3 F1 유형) ⑷ 글로브가 새 확장자·새 디렉토리를 놓치는 미래 구멍.

### ⑥ SOT 체크리스트

- `docs/sot/verification-commands.md` — 검사 표에 행 추가 (같은 PR).
- `docs/sot/mechanism-registry.yaml` — 항목 추가 (같은 PR).
- `docs/sot/coding-principles.md` — 500줄 원칙이 이미 있는지 확인, 없으면 이 게이트를 근거로 추가 여부는 별도 판단(이번 비범위).

### ⑦ 비범위

- 파일 분할 자체(기존 파일 쪼개기) — 현재 초과 파일 0개라 해당 없음.
- 함수 길이·복잡도 검사 — 별도 AC.

### ⑧ 롤백 절차 (L3)

스크립트 삭제 + CI 단계 제거 + 명부 항목 제거를 한 커밋으로 되돌리면 끝. 다른 검사와 상태를 공유하지 않는다.

### ⑨ 영향 반경 (L3)

이 게이트가 오탐하면 훅을 우회하지 않는 모든 push 시도가 검사 실패로 멈춘다(pre-push 글로브에 걸리므로). `git push --no-verify` 우회는 가능하며, 현재 원격도 합치기를 기계적으로 막지 못한다. 완화: 오탐 시 해당 파일을 명시적 예외 목록(만료일 필수)에 올리는 절차를 스크립트 주석에 기재. PII·인증·과금 경로 접촉 없음 — 데이터 안전 AC 불필요.

### ⑩ 계약 스펙 (입출력)

- 입력: 기본은 저장소 상태이며 검사 루트는 `humansearch/src`, `extension/src`, `bot/src`, 한도는 500줄이다. 소스 확장자 `.py`, `.ts`, `.tsx`, `.js`, `.sh` 비교는 ASCII 대소문자를 구분하지 않으며, 파일 내용에 LF가 바로 뒤따르지 않는 CR(bare CR)이 하나라도 있으면 줄 수를 신뢰할 수 없는 입력으로 판정한다. bare CR이 없으면 LF를 줄 구분자로 신뢰하므로 순수 LF·순수 CRLF·두 형식의 혼합을 같은 기준으로 센다. 검사 루트의 존재 여부는 작업 폴더가 아니라 Git 색인(`git ls-files`)의 루트 자체 또는 하위 항목으로 판정한다. 격리 자기시험에서 `FILE_SIZE_TEST=1`을 함께 설정한 경우에만 `FILE_SIZE_LIMIT`(시험 한도)과 `FILE_SIZE_ROOTS`(공백으로 구분한 시험 루트)를 오버라이드로 인정한다. `FILE_SIZE_TEST=1` 없이 두 값 중 하나라도 들어오면 둘 다 무시하고 기본 루트·기본 한도로 검사하며, 무시 사실을 출력한다. `pre-push`는 인수 스크립트 실행 전에 시험 오버라이드 3종(`FILE_SIZE_TEST`, `FILE_SIZE_ROOTS`, `FILE_SIZE_LIMIT`)과 자식 셸 시작 파일 환경값 2종(`BASH_ENV`, `ENV`)을 모두 제거한다. JSON 입·출력, 함수·API 시그니처, 외부 상태 전이는 없다.
- 출력: exit 0 = 전 파일 한도 이하. exit 1 = 초과 파일 존재(각 줄 `초과: <path> <줄수>줄`) 또는 검사 파일 0개(`FAIL: 검사 대상 0개`). exit 2 = 읽기·줄 수 계산 불가, bare CR이 하나라도 있는 파일, 추적 연결 항목 등으로 검사 불능.
- 경계값: 정확히 500줄 = 합격, 501줄 = 불합격.
- 연결 항목: 대상 루트 자체 또는 그 아래에서 Git 모드 `120000`(심볼릭 링크)이나 `160000`(하위 저장소 연결)을 발견하면 작업 폴더에 보이는지와 무관하게 파일 이름·확장자·제외 경로를 판정하기 전에 즉시 exit 2로 끝낸다.

## 적대 검증 로그

### fix6 후속 보수

- 다른 엔진 1차 시도: `env -u ANTHROPIC_API_KEY claude -p '<읽기 전용 적대 검증 지시 + strict §8-7 출력 형식 전문>'` → exit 1. 실제 전체 프롬프트와 출력은 `.claude/private-reviews/codex-file-size-fix6-2026-08-15.md` §3-7에 보존한다.

```text
Not logged in · Please run /login
SessionEnd hook [node "${CLAUDE_PLUGIN_ROOT}/scripts/session-lifecycle-hook.mjs" SessionEnd] failed: EPERM: operation not permitted, unlink '/Users/kangsangmo/.claude/plugins/data/codex-openai-codex/state/file-size-gate-06c3787ab657e36e/broker.json'
CLAUDE_ADVERSARIAL_EXIT=1
```

→ 접속 자격이 없어 판정 본문이 생성되지 않았다. 따라서 다른 엔진 합격으로 세지 않았고, 발주 절차의 로컬 실행 증거와 codex 직접 재공격만 최종 근거로 삼았다.

- codex 2차 재공격: 대소문자 처리 한 줄을 임시로 무력화하자 자기시험이 14/15·exit 1로 실패했고, 원복 후 본체 내용 지문이 일치하며 15/15·exit 0으로 복귀했다. 본체·명부·문법·기본 검사는 최종 재실행에서 전부 exit 0이었다. 명령·출력 전문은 위 fix6 보고서 §3-5·§3-6·§3-8에 보존한다.

### 최종 검증 사슬 (2026-08-15) — G·V1·V2 수렴

이 게이트는 만든 뒤 일곱 라운드의 적대검증을 거쳤다. 각 라운드는 다른 세션(V1=codex, V2=Claude 격리)이 산출물만 받아 새 우회를 찾고, 그 우회를 재현하는 실패 시험(RED)을 먼저 커밋한 뒤 최소 수정(GREEN)으로 닫는 순서로 진행됐다. 당시 판정 원문은 Git 추적에서 제외된 각 작업 공간의 `.claude/private-reviews/`에 로컬 보존돼 있어 작업 공간 회수 전에 별도 보존 여부를 결정해야 한다. 추적 문서에는 경로와 당시 내용 지문만 남는다.

| 라운드 | 검증자 | 판정 | 찾은 결함(닫은 우회) | 판정서·지문 |
|---|---|---|---|---|
| 1 | V1(codex) | FAIL | tests/·.venv 세그먼트 하 추적 파일 오탐(정상 변경 차단) | codex-file-size-verdict-2026-08-15.md `ff899487` |
| 2 | V1(codex) | FAIL | 일반 이름 디렉터리 링크로 tests의 501줄 모듈 은닉 | verdict2 `c95cac4a` |
| 3 | V1(codex) | FAIL | FILE_SIZE_ROOTS 단독 범위 축소 / gitlink(160000) 은닉 | verdict3 `58b2cfae` |
| 4 | V1(codex) | FAIL | BASH_ENV 재주입 / 루트 자체 은닉 | verdict4 `3b67577c` |
| 5 | V1(codex) | **PASS** | (모델 안 치명·높음 0) | verdict5 `15a21896` |
| 5 | V2(Claude 격리) | **CONFIRM** | 신규: .PY 대문자 미탐 / CR 전용 개행 과소집계(중간) | claude-file-size-v2-2026-08-15.md |
| 6 | V1(codex) | FAIL | 개행 혼합(bare CR) 파일 줄수 과소집계 | verdict6 `6814fa6a` |
| 7 | V1(codex) | **PASS(병합 가능)** | (개행 공간 완결: LF/CRLF=집계, bare CR=exit 2) | verdict7 `4bc4ac37` |

→ **이 표가 말하는 것:** 처음 만든 검사기는 "정직한 개발자의 실수를 잡는다"는 목적에는 맞았지만, 검사 범위를 몰래 좁히거나 파일을 다른 경로로 연결해 숨기는 우회에 7겹으로 취약했다. 일곱 라운드로 그 우회를 하나씩 닫아, 마지막에 G(구현)·V1(codex)·V2(Claude)가 계약(AC-FS1·2·3) 기준에서 일치(PASS)했다. V2가 V1이 놓친 결함 2건을 잡았고(대문자 확장자·CR 개행), 그 2건도 후속 라운드에서 닫혔다 — 두 검증이 실제로 교차했다는 증거다.

**정직한 잔여 한계 (병합해도 남는 것, V1·V2 공통 기재):**
- 서버 검사는 현재 합치기 차단선이 아니다. 2026-08-15 원격 조회에서 main은 보호되지 않았고(`protected=false`), 현재 개인 계정의 비공개 저장소 요금제에서는 보호 규칙과 저장소 규칙 조회가 모두 403으로 거부됐다. 로컬 pre-push 훅도 `git push --no-verify`로 우회할 수 있다. 따라서 지금의 강제력은 사람 규율과 실패 표시까지이며, 합치기를 기계적으로 막으려면 GitHub Pro로 올리거나 저장소를 공개한 뒤 `verify` 성공을 필수 상태 검사로 지정해야 한다.
- "미래에 추가될 새 파일 확장자"는 유한한 규칙이 선제 차단할 수 없다 — 새 언어를 제품에 도입하면 대상 확장자 목록에 추가하는 절차가 필요하다.
