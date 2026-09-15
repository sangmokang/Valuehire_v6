# HS-03.02 최종 독립 검토(V1) 판정 원문 — 2026-09-15

검토 엔진: Codex CLI 0.154.0 (`codex exec -s workspace-write`, `--no-local` 클론 @d84dc41, 17:12:46~18:15:15, 167,796 토큰). 검토 범위 7473ec8..d84dc41. 원문 100% 보존, 아래는 판정 파일 그대로다. 단계별 실행 기록은 세션 scratchpad `review-scratch/steps/step-1..6.md`(경유지)에 남았고 요약은 본문에 있다.

---

VERDICT: APPROVE

## 결론

현재 상태를 다음 단계로 넘겨도 됩니다. 같은 대상을 두 번 남기지 않고, 위험한 저장 위치와 권한을 막으며, 동시에 두 요청이 와도 한 건만 남는 동작을 확인했습니다. 다만 한 확인 묶음만 따로 돌리면 중요한 안전 규칙 하나를 놓칩니다. 전체 확인에서는 잡히므로 지금 동작이 잘못되지는 않지만 보강할 가치가 있습니다.

## 판단 근거

### 먼저 밝힐 제한

- 요청자가 5단계 수용 스크립트 음성 대조군을 별도 측정했다고 하여 재실행하지 않았습니다. 원격 CI, 보호 규칙, 실제 운영 UID 분리는 확인하지 않았습니다.
- 전체 pytest는 socket 생성이 금지된 샌드박스에서 `tests/test_admin_shadow_server.py` 16건이 모두 `Operation not permitted`로 실패했습니다. 요청 지침에 따라 HS-03.02 전용 102개 결과를 판정 근거로 사용했습니다.
- 실패 후 재시도는 네 종류였습니다. step 2 import 로그 집계에서 zsh 특수 변수 `path` 사용, step 4 workflow marker 표기 오인, step 7 최초 journal 프로브의 겹치는 key/DB root, step 8 최초 `.git` 프로브의 준비 순서 오류였습니다. 각 원인을 제거해 재실행했고 원래 테스트 결과를 덮어쓰지 않았습니다.
- journal 소멸까지 `CandidateIdentityError`여야 한다는 요청 문장은 목표 문서 249행 및 `continue`→`raise` 변이 결과와 충돌합니다. 두 키 소멸은 닫힌 오류, rollback journal 소멸은 정상 계속이라는 문서화된 해석을 채택했습니다.

### 선택과 버린 해석

- 선택: 공식 수용 경로인 102개 명부 전체와 CI 연결 검사를 판정 단위로 삼았습니다. R4 파일 하나만으로 전체 안전성을 대표한다는 해석은 버렸습니다. 실제로 보호 root 공유 거부 변이는 R4 20개를 통과했지만 전체 102개에서는 3개가 실패했습니다.
- 선택: AC-3은 응용 코드의 선조회가 아니라 SQLite 기본키 충돌과 서로 다른 두 연결로 증명해야 한다고 보았습니다. 20회 반복이 모두 `{inserted, duplicate}`와 1행을 유지했습니다. 이 선택이 틀리면 동시에 들어온 같은 후보가 두 행으로 남을 수 있습니다.
- 선택: disappearing journal은 검사 순간 이미 사라졌다면 없는 파일로 취급해야 합니다. 모든 소멸을 오류로 보는 해석은 버렸습니다. 그 해석을 적용한 변이는 R4 테스트 8개를 깨뜨리고 과거 간헐 실패를 되살립니다.
- 선택: R4 단독 누락은 낮은 심각도로 보았습니다. 공식 전용 모음과 수용 명부가 독립적으로 이를 잡기 때문입니다. 향후 R2 항목이 명부에서 빠지면 이 판단은 만료되고 안전 경계 약화가 거짓 정상으로 보일 수 있습니다.
- 선택: 명부·테스트·기대 개수를 함께 낮추는 공격은 저장소 내부 자기검사의 알려진 한계로 보았습니다. 이를 현재 제품 결함으로 해석하는 길은 버렸습니다. 이 판단이 틀리면 검토자가 세 파일의 동시 약화를 놓쳐 필수 검사가 조용히 사라질 수 있습니다.

## 기술 상세와 증거 원문

변이 테스트(mutation testing)는 보호 코드를 한 군데씩 제거해 검사가 회귀를 잡는지 보는 시험입니다. 음성 대조군(negative control)은 실패해야 정상인 입력이고, 회귀(regression)는 고친 문제가 다시 나타나는 현상이며, lint는 코드·구성 규칙을 자동 검사하는 절차입니다.

### 발견 1 — LOW

**원문 제목:** “키 폴더가 DB 보호 루트 하위일 때 거부 제거 변이”

- 심각도: LOW.
- 위치: `humansearch/src/humansearch/candidate_identity.py:245` — key/DB 보호 root 공유 거부; `humansearch/tests/test_hs_0302_r4_db_boundary.py:118` — R4 경계 반례 시작; `humansearch/tests/test_hs_0302_r2_hardening.py:214` — 실제 독립 방어 테스트.
- 원인: 보호 root 양방향 중첩 반례가 R2 hardening 파일에만 있고 R4 경계 파일에는 없습니다.
- 사업 영향: R4 파일만 빠르게 돌리는 검토자는 해당 안전 규칙 제거를 놓칠 수 있습니다. 공식 102개 모음은 현재 이를 잡으므로 실제 저장 경계 우회가 배포되는 직접 경로는 확인되지 않았습니다.
- 재현 입력: `_load_hmac_key`의 보호 root 공유 거부(원본 245–246행)만 제거하고 R4 20개 실행 → exit 0, `20 passed`; 전체 `test_hs_0302*.py` 실행 → exit 1, `3 failed, 99 passed`.
- 최소 수정 방향: R2의 양방향 root 중첩 반례를 R4 분류에도 포함하거나, 문서와 변이 절차의 판정 단위를 R4 단독이 아닌 필수 102개 명부로 명확히 고정하십시오. 새 테스트를 추가한다면 roster와 `EXPECTED_REQUIRED_IDS`를 함께 올려야 합니다.

→ 해석: 테스트 분류의 국소 공백이며 현재 공식 수용 경로의 거짓 정상은 아닙니다.

### 설계 지적 — 명부의 동시 약화 한계

- 무엇을: 테스트 함수, roster ID, `EXPECTED_REQUIRED_IDS`를 함께 1개 줄이면 수용 검사가 통과합니다.
- 왜: 검사 기준과 검사 대상이 같은 변경 묶음 안에 있어 내부 일관성만 확인할 수 있습니다.
- 버린 길: 현재 shell 검사만으로 저장소 밖의 불변 기준까지 증명할 수 있다는 해석은 버렸습니다.
- 대가: 세 파일을 함께 약화한 변경은 사람 검토나 외부 기준이 없으면 조용히 통과합니다.
- 되돌리기: 필요하면 보호된 외부 manifest/hash 또는 별도 정책 저장소를 기준으로 대조하십시오. 현재 goal 문서는 이 한계를 이미 기록합니다.

### 요구사항별 판정

- AC-1 PASS — 같은 `(position_ref, channel, candidate_ref)` 두 번 기록 시 1행과 HMAC 일치를 필수 모음이 확인했습니다. `docs/engineering/humansearch-hs-0302-candidate-identity-goal-2026-09-15.md:39` — 중복 방지 요구; `candidate_identity.py:78` — 식별 HMAC 계산; `candidate_identity.py:98` — 기록 진입점.
- AC-2 PASS — position 또는 channel 차이를 별도 행으로 유지하고 세 필드가 HMAC 입력에 포함됩니다. goal 문서 40행 — 구분 요구.
- AC-3 PASS — `test_hs_0302_candidate_identity.py:218` — 두 작업자·Barrier(2)·별도 connect 경쟁; 20회 반복 failure `0/20`. `candidate_identity.py:295` — 쓰기 함수; SQLite 기본키 충돌만 duplicate로 변환합니다.
- AC-4 PASS — 빈 필드와 허용 밖 channel을 닫힌 오류로 거부합니다. `candidate_identity.py:124` — 필수 필드 검증; goal 문서 42행 — 입력 거부 요구.
- 저장 경계 PASS — `candidate_identity.py:227` — HMAC key 검사; `:256` — 쓰기 직전 DB 경계; `:273` — sidecar 1회 stat 검사; `:305` — 연결 전 경계 호출. `docs/sot/humansearch-storage-contract.md:80` — 0700/0600·owner·symlink·root 계약; `:85` — WAL/SHM/journal 범위.
- 검증 연결 PASS — `.github/workflows/verify.yml:227` — HS-03.02 단계; `:234` — 정확한 수용 명령. `scripts/verify/check-hs-0302-ci-wiring.rb:17` — 기대 단일 명령; `scripts/acceptance-hs-0302.sh:88` — R4 하한 7; `:93` — 필수 ID 102. `docs/sot/verification-commands.md:20` — 27개 단계 목록 역할.

### 변경 범위와 위험 분류

- 제품 코드: `humansearch/src/humansearch/candidate_identity.py` — DB 쓰기, 중복, key/DB/sidecar 경계로 최고 위험.
- 테스트: `humansearch/tests/test_hs_0302_acceptance_probe.py`, `test_hs_0302_candidate_identity.py`, `test_hs_0302_r2_hardening.py`, `test_hs_0302_r3_hardening.py`, `test_hs_0302_r4_db_boundary.py` — 경쟁·입력·경계·검사기 증거.
- 검사기/fixture: `scripts/acceptance-hs-0302.sh`, `scripts/verify/check-hs-0302-ci-wiring.rb`, `scripts/verify/fixtures/hs-0302-required-tests.txt` — fail-closed와 명부 강도.
- CI/문서: `.github/workflows/verify.yml`, `docs/sot/verification-commands.md`, goal 문서, closeout prompt — 실행 연결과 요구사항 장부.

### 기준선 원문

- HS 전용 pytest exit 0: `102 passed in 10.94s`.
- Ruff exit 0: `All checks passed!`.
- mypy exit 0: `Success: no issues found in 48 source files`.
- HS 수용 exit 0: `CHECKED: 22`; `OK(run-acceptance): scripts/acceptance-hs-0302.sh — 판정 22건, CHECKED 22`.
- CI 단계 무결성 exit 0: `CHECKED: 24`; `VERDICT: PASS`.
- 의미 변이 exit 0: `CHECKED: 16`; `VERDICT: PASS`.

→ 해석: 현재 HEAD의 필수 전용 실행과 정적·수용·검사기 기준선은 모두 정상입니다. 세부 명령은 `steps/step-1.md`에 있습니다.

### 가드 변이 원문

- 부모 0700 제거 → exit 1, 2 failed; DB 0600 제거 → exit 1, 1 failed; DB 일반 파일 제거 → exit 1, 1 failed.
- Git 밖 검사 제거 → exit 1, 2 failed; sidecar 호출 제거 → exit 1, 9 failed.
- sidecar symlink 제거 → exit 1, 3 failed; mode 제거 → exit 1, 3 failed; 일반 파일 제거 → exit 1, 3 failed.
- sidecar FileNotFound `continue`를 `raise`로 변경 → exit 1, 8 failed.
- key-dir resolve 예외 변환 제거 → exit 1, 1 failed; key read 예외 변환 제거 → exit 1, 1 failed.
- key/DB 보호 root 공유 거부 제거 → **exit 0, 20 passed**; 전체 전용 모음은 exit 1, 3 failed.
- `_insert_once`의 DB 경계 호출 제거 → exit 1, 16 failed.
- 13/13 import probe가 각 `$REVIEW_SCRATCH/copies/<name>/src` 모듈을 불러왔습니다.

→ 해석: 지정 R4 모음은 13개 중 12개 변이를 잡았습니다. 유일한 생존 변이는 전체 필수 모음의 R2 테스트가 잡습니다. 상세는 `steps/step-2.md`에 있습니다.

### 검사기 음성 대조군 원문

- roster clone에서 R4 함수 1개+ID 1개+기대값 102→101 동시 약화 → 수용 exit 0; `CHECKED: 22`; 알려진 한계 재현.
- CI run에 `|| true` 주입 → checker exit 1; `WIRING_BAD: run 에 셸 제어 연산자 || 가 있다`.
- CI run에 `; echo ok` 주입 → checker exit 1; `WIRING_BAD: run 에 셸 제어 연산자 ; 가 있다`.
- 요청자 지정 step 5는 NOT_RUN; 별도 측정 주장만 있고 본 리뷰의 독립 증거는 없습니다.

→ 해석: CI 성공 강제 두 종류는 모두 차단됐습니다. 내부 명부의 동시 축소만 알려진 한계로 남습니다. 상세는 `steps/step-3.md`~`step-5.md`에 있습니다.

### 경쟁·경계 원문

- 두 연결 경쟁 20회 → failure `0/20`; 마지막 세 회 모두 exit 0.
- key file 소멸 → `CandidateIdentityError`, `hmac key is unreadable`, path 노출 False.
- key directory 소멸 → `CandidateIdentityError`, `hmac key directory is missing`, path 노출 False.
- journal commit 소멸 → `race_triggered=True`, `journal_disappeared=True`, `result=success`, `outcome=inserted`.
- DB file/ancestor symlink, `.git` FILE, DB directory, symlink sidecar 묶음 → exit 0, `7 passed in 3.87s`.
- 세 단계 위 `.git` marker → `CandidateIdentityError`, path 노출 False. 실제 journal → mode 0600, regular True, symlink False. macOS symlink lstat → mode 0755, islink True.

→ 해석: 과거 journal 소멸 간헐 실패는 재현되지 않았고 파일 경계는 fail-closed였습니다. 상세는 `steps/step-6.md`~`step-8.md`에 있습니다.

### 오류 메시지 전수 결과

직접 `CandidateIdentityError` raise 20곳의 runtime 문구는 다음 집합입니다: `{position_ref|channel|candidate_ref|observed_at} must not contain control characters`, 같은 label의 `must not be blank`와 `is too long`, `channel is not an allowed portal channel`, `observed_at must be an RFC3339 timestamp`, `observed_at is not a real instant`, `observed_at must carry a UTC offset`, `{db path|hmac key path} must not contain a symlink`, `db file is missing`, `hmac key must be a regular file`, `hmac key directory is missing`, `hmac key must not share the db protected root`, `hmac key is unreadable`, `hmac key must be at least 32 bytes`, `db file must be a regular file`, `db file must be outside the git worktree`, `sqlite sidecar must not be a symlink`, `sqlite sidecar mode must be 0600`, `sqlite sidecar must be a regular file`.

직접 `StorageSchemaError` raise는 candidate_identity.py에 0곳입니다. `_verify`가 재포장하는 네 문구는 `{hmac key directory|hmac key|db directory|db file} is missing`, `must not contain a symlink`, `owner mismatch`, `mode must be {0700|0600}`입니다. 구문 트리상 메시지 인수의 path·position_ref·candidate_ref·key bytes·HMAC hex 참조는 0개였습니다.

→ 해석: 지정된 민감값이 오류 문자열에 들어가는 경로를 찾지 못했습니다.

### 전체 suite와 Git 상태

- 전체 pytest exit 1: `16 failed, 315 passed in 14.83s`. 실패 16건 전부 `tests/test_admin_shadow_server.py`, `Operation not permitted` 16건.
- 시작 `git status --short`: 출력 0줄. 종료 `git status --short`: 출력 0줄.
- HEAD 시작/종료 동일: `d84dc41ce2f00bd22c58ed43d4ffa6790fc19e5b`; 기준 `7473ec8c343cb906b3f510c2d50f72dc8004cedd`.
- 원본 clone의 tracked file 편집, commit, push, stash는 없었습니다. 모든 변이는 `$REVIEW_SCRATCH/copies/`에 있습니다.

→ 해석: 전체 suite의 비관련 환경 실패는 남았지만, 검토 범위의 전용 증거는 닫혔고 원본 작업공간은 시작과 끝 모두 깨끗합니다. `APPROVE`는 자동 병합 권한이 아니며 HEAD가 바뀌면 만료됩니다.
