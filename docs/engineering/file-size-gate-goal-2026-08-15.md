# 파일 500줄 게이트 — goal 문서 (2026-08-15)

> 위험 등급 L3 (SOT 수정 + 공유 검사 장치 신설 — 자동 승격 트리거 해당) / 마스터플랜 `docs/engineering/humansearch-journey-master-plan-2026-08-14.md` §4·§11의 "강제 장치가 먼저다" 이행

## 사장님 브리핑 (§1⑪ — 1·2층)

**결론.** 사장님이 정하신 "코드 한 파일 500줄 초과 금지" 규칙을 말이 아니라 자동 검사로 강제하는 장치를 만듭니다. 지금 만들어 두면 앞으로 서치·등록·보고 코드가 늘어날 때마다 사람이 세지 않아도 기계가 막습니다. 결정하실 사항은 없습니다 — 이미 확정하신 규칙의 집행 장치입니다.

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

이 게이트가 오탐하면 모든 push가 막힌다(pre-push 글로브에 걸리므로). 완화: 오탐 시 해당 파일을 명시적 예외 목록(만료일 필수)에 올리는 절차를 스크립트 주석에 기재. PII·인증·과금 경로 접촉 없음 — 데이터 안전 AC 불필요.

### ⑩ 계약 스펙 (입출력)

- 입력: 기본은 저장소 상태이며 검사 루트는 `humansearch/src`, `extension/src`, `bot/src`, 한도는 500줄이다. 검사 루트의 존재 여부는 작업 폴더가 아니라 Git 색인(`git ls-files`)의 루트 자체 또는 하위 항목으로 판정한다. 격리 자기시험에서 `FILE_SIZE_TEST=1`을 함께 설정한 경우에만 `FILE_SIZE_LIMIT`(시험 한도)과 `FILE_SIZE_ROOTS`(공백으로 구분한 시험 루트)를 오버라이드로 인정한다. `FILE_SIZE_TEST=1` 없이 두 값 중 하나라도 들어오면 둘 다 무시하고 기본 루트·기본 한도로 검사하며, 무시 사실을 출력한다. `pre-push`는 인수 스크립트 실행 전에 시험 오버라이드 3종(`FILE_SIZE_TEST`, `FILE_SIZE_ROOTS`, `FILE_SIZE_LIMIT`)과 자식 셸 시작 파일 환경값 2종(`BASH_ENV`, `ENV`)을 모두 제거한다.
- 출력: exit 0 = 전 파일 한도 이하. exit 1 = 초과 파일 존재(각 줄 `초과: <path> <줄수>줄`) 또는 검사 파일 0개(`FAIL: 검사 대상 0개`). exit 2 = 검사 불능.
- 경계값: 정확히 500줄 = 합격, 501줄 = 불합격.
- 연결 항목: 대상 루트 자체 또는 그 아래에서 Git 모드 `120000`(심볼릭 링크)이나 `160000`(하위 저장소 연결)을 발견하면 작업 폴더에 보이는지와 무관하게 파일 이름·확장자·제외 경로를 판정하기 전에 즉시 exit 2로 끝낸다.

## 적대 검증 로그

(V1·V2 판정을 여기 append)
