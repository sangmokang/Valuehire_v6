# Verification-authority 원칙 게이트 복구 goal — 2026-08-20

## 결론

중요한 원칙 검증 문서는 삭제된 것이 아니다. 별도 작업에서 처음 만들어진 뒤 현재 작업에 합쳐지지 않았고, 더 나은 보강본도 다른 작업공간에만 남아 있어 이 작업공간에서 보이지 않았다.

이번 변경은 루트 워크트리의 검증된 최신 원칙 게이트 중 최소 완결 묶음을 이 작업트리에 복구한다. 기존 verification-authority 변경·미추적 파일은 사용자 자산으로 보존하며 commit, push, PR, merge, deploy는 수행하지 않는다.

## 결정 카드

- 무엇을: 원칙 장부·검사·적대검증·로컬/CI 배선을 최소 완결 묶음으로 복구한다.
- 왜: 파일 두 개만 복사하면 실행되지 않는 장식 문서가 되기 때문이다.
- 버린 대안: 정상 상태도 실패시키는 오래된 작업 브랜치 초안을 그대로 가져오지 않는다.
- 대가: SOT와 실행 배선을 함께 바꾸므로 변경 파일 수와 검증 비용이 늘어난다.
- 되돌리기: 배선부터 역패치한 뒤 신규 검사 묶음과 시행점 문구를 제거한다.

## 위험등급과 범위

- 등급: L3 — SOT, pre-push, CI, 기계 장부와 적대검사가 함께 바뀐다.
- 포함: 원칙 파생 장부, 검사기, mutation과 그 fixture/helper, 정본 시행점, mechanism registry, pre-push/CI 배선, 명령 SOT.
- 제외: 전역 Strict 스킬 잠금 수명주기, 전역 파일 수정, 기존 verification-authority 기능 재설계.
- 시작 HEAD: `858b96d510cf9e4da393b85446871448b4c1dfa6`.
- 시작 상태 지문: `93ca7e12930b61dec403d896e7636631261e33df9a4ad04a9dbcbf79f9f1d5a3`.
- 기존 42개 미추적 자산 합성 지문: `1e008fb0728c104acd241e884f43b78abaedc9e177b7c2cd87e6aecb91799ab7`.

## 추적 근거

- `scripts/acceptance-principles-check.sh` 최초 추가: `03ad76f42d08bdf668083ff49a308caecb5d2fce`.
- `docs/sot/principles.yaml` 최초 추가: `804a39c72cf96cbd1c88eb836a18f31245bdd564`.
- mutation 최초 추가: `5d5c9700f35ace94bb625c453b1f001f7fad5078`.
- 위 파일은 현재 `main`과 대상 HEAD에 없다.
- 대상 워크트리에 복구한 보강본 SHA-256:
  - `principles.yaml`: `b7734fae038d9e3d856a6d805861c390a29754450c1c564f2769bd6819657260`
  - `acceptance-principles-check.sh`: `d87d589303409df2b4ed2c7c31483ecd7a20a7bb73e3537179bb99fa12830912`
  - `acceptance-principles-mutations.sh`: `a8703c48dbd558eca9271a45b7f078b110cf4aad799d6b455b1a43d303a625a5`
- 루트 워크트리는 별도 미추적 자산이 계속 변할 수 있으므로 복구 결과는 위 대상 워크트리 해시와 아래 명령 출력으로 고정한다.

## T 계약

### 입력

- `docs/sot/coding-principles.md`
- `docs/sot/principles.yaml`
- `hooks/pre-push`
- `.github/workflows/verify.yml`
- `docs/sot/mechanism-registry.yaml`

### 출력과 오류

- 정상 입력은 `VERDICT: PASS`, `CHECKED: 32`, exit 0을 낸다.
- 계약 위반은 `FAIL`, exit 1을 낸다.
- 환경 문제로 판정할 수 없으면 `NOT_RUN`, exit 2를 낸다.
- 파일 누락·빈 파일·파싱 오류·ID 누락/중복/미지 ID·원칙 문구 불일치·빈 mechanism·미존재 경로·잘못된 stage는 FAIL이다.
- pre-push와 CI의 명시적 실행 줄이 없거나 `|| true`, `continue-on-error`, 조건부 실행으로 약화되면 FAIL이다.
- 검사 대상 0개는 PASS가 아니다.

## EARS 인수 기준

### AC-1 직접 SOT 로드

When 원칙 검사를 실행하면 시스템은 현재 작업트리의 두 SOT를 직접 읽고 32개 ID와 원칙 문구를 대조해야 한다.

### AC-2 장치 실존

When 장부 항목을 검사하면 시스템은 모든 항목의 `mechanism_expected`와 `mechanism_found`가 비어 있지 않고 path/check/stages가 실제 파일과 허용 계약을 가리키는지 확인해야 한다.

### AC-3 강제 배선

When pre-push 또는 CI 구성을 읽으면 시스템은 `bash scripts/acceptance-principles-check.sh`의 무조건 직접 실행이 정확히 한 번 존재함을 확인해야 한다.

### AC-4 적대검증

When mutation suite를 실행하면 시스템은 정상 fixture와 누락·위조·약화·500/501 경계를 포함한 34개 사례를 기대 상태로 판정해야 한다.

### AC-5 기존 기능 보존

When 복구가 끝나면 일반 PR verification-authority acceptance와 저장소 전체 검사가 그대로 통과해야 한다.

### AC-6 사용자 자산 보존

When 복구 전후 상태를 비교하면 기존 42개 미추적 파일의 경로·내용 합성 지문이 같고 루트 워크트리 상태도 같아야 한다.

## Counter-AC

1. 문서만 복사하고 pre-push/CI를 배선하지 않아도 PASS한다.
2. 오래된 브랜치 초안을 그대로 복사해 정상 저장소가 영구 FAIL한다.
3. 원칙 파일·검사기·CI 줄 중 하나를 삭제해도 PASS한다.
4. `|| true`, `continue-on-error`, 조건부 실행으로 실패를 삼킨다.
5. 31개·33개·중복 ID 또는 원칙 문구 변조를 통과시킨다.
6. 기존 verification-authority workflow 환경변수 배선을 덮어쓴다.
7. 루트 워크트리 또는 기존 미추적 사용자 파일을 수정한다.

## RED → GREEN

- RED: `docs/sot/principles.yaml` 직접 읽기 exit 1, `bash scripts/acceptance-principles-check.sh` exit 127.
- GREEN: 동일 검사기 원명령 exit 0, `CHECKED: 32`.
- 회귀: mutation 34건, mechanism registry, verification-authority acceptance, `verify.sh`, shell syntax, `git diff --check`.

## 롤백

1. CI와 pre-push의 원칙 검사 호출을 먼저 역패치한다.
2. mechanism registry와 명령 SOT의 이번 항목을 역패치한다.
3. 신규 장부·검사기·mutation·helper·fixture를 제거한다.
4. `coding-principles.md`의 이번 시행점 두 줄과 날짜를 복원한다.
5. 기존 사용자 자산 합성 지문과 전체 검사를 다시 확인한다.

## 검증 로그

- `bash scripts/acceptance-principles-check.sh` → exit 0, `VERDICT: PASS`, `CHECKED: 32`, `WIRING: PASS pre-push=1 ci=1`.
- `bash scripts/acceptance-principles-mutations.sh` → exit 0, `CHECKED: 34`, `VERDICT: PASS`; 500줄 정상·501줄 실패 경계 포함.
- `bash scripts/verify/check-strict-principles-skills.sh` → exit 0, `COMMON_CONTRACT: PASS byte-identical`, `ENGINE_ORDER: PASS`.
- `bash scripts/verify/check-strict-verdict-ledger.sh scripts/verify/fixtures/strict-principles/valid-verdict.yaml` → exit 0, `ROLES: PASS G/V1/V2/T`.
- `bash scripts/verify/check-mechanism-registry.sh` → exit 0, `CHECKED: 6`.
- `bash scripts/acceptance-verify-ac-m.sh` → exit 0, `CHECKED: 25`.
- `bash scripts/acceptance-verification-authority.sh` → exit 0, `MUTATIONS: total=32 blocked=31 survived=0 controls=1`, `SHA_FIXTURES: total=9 scope=pr_head`, `LINE_LIMIT: files=5 limit=500 boundary_500=PASS boundary_501=FAIL zero_targets=FAIL`.
- `bash verify.sh` → exit 0, `PASS: no secret-pattern match in any tracked file, .env not tracked`.
- `git diff --check` → exit 0, no output.
- `bash -n` on changed shell scripts and pre-push → exit 0, no output.
- `.github/workflows/verify.yml` executable name rows: 21; `docs/sot/verification-commands.md` table rows: 21.
- Existing 42 user untracked assets: count 42; combined `sha256sum` manifest hash `1e008fb0728c104acd241e884f43b78abaedc9e177b7c2cd87e6aecb91799ab7`.
- V1: `docs/engineering/verification-authority-principles-recovery-v1-verdict-2026-08-20.md` records `V1_VERDICT: NOT_RUN` because Claude returned `Credit balance is too low`; therefore overall Strict verdict is not PASS even though local implementation verification passes.
