VERDICT: FAIL

# HS-00.01 최종 Codeaudit — 2026-09-10

## 결론

현재 9개 후보 파일의 동작 검증은 통과로 볼 수 있습니다. 하지만 지금 커밋 대기열 전체는 비밀 검사와 공백 검사를 통과하지 못하므로 로컬 커밋 승인으로 넘기면 안 됩니다.

확인하지 않은 것은 원격 검사, 병합, 실제 채용 포털 실행, 운영 저장, 별도 운영체제 계정 격리입니다. 이번 감사는 같은 사용자 계정의 로컬 읽기 전용 검토입니다.

## 판단 근거

HS-00.01의 목표는 빠진 착수 판정 증거를 실제 검토 원문으로 채우고, V1/V2가 잡은 실행 우회와 잘못된 대상 판정을 새 회귀로 닫는 것입니다. 제품 검색이나 포털 운영 성공을 증명하는 작업이 아닙니다.

9개 후보 파일은 `artifacts/hs-next-20260910/final-candidate-files.json`의 SHA256 지문과 현재 worktree·index가 모두 일치했습니다. 신규 pytest 8개, 기존 hs-kickoff 변이 37개, 본 acceptance 12개, G2 family(정적 검사·전체 pytest·G2 변이·antiforge), 파일/함수 예산 600/601/0 경계는 통과했습니다.

그러나 staging 후 증거 로그까지 포함한 커밋 후보는 `bash verify.sh`에서 `docs/engineering/evidence/hs0001-20260910/v1-cli.log` 비밀 패턴 매치로 실패했습니다. 값은 출력하지 않았습니다. 같은 staged 상태에서 `git diff --cached --check`도 여러 증거 원문 파일의 trailing whitespace로 실패했습니다.

## 요구사항·주장 대조표

| ID | 사용자 요구/주장 | 판정 | 근거 | 반증/공백 | 심각도 |
|---|---|---|---|---|---|
| R1 | 기존 19커밋 보존, RED 기대값 유지 | 구현 확인 | `git show --stat e2404d3`, `git show --stat 16e5d64`, `sha256sum` 재확인 | 원격 main 통합 아님 | 낮음 — 로컬 이력 판단에 한정 |
| R2 | 9개 후보 파일 index=worktree 일치 | 구현 확인 | `final-candidate-files.json` 9개 모두 worktree/index SHA 일치 | 증거 문서 31개는 별도 staged로 추가됨 | 낮음 — 후보 소스 지문은 맞음 |
| R3 | V1/V2 FAIL의 F1~F4를 실제 코드에 연결해 닫음 | 구현 확인 | `humansearch/tests/test_hs_0001.py:98`부터 `shell`, `defaults`, `BASH_ENV`, `PR #131`, `PASSED` 반례가 있음. 현재 `uv run --no-sync pytest -q tests/test_hs_0001.py tests/test_hs_0001_main_compat.py`는 8 passed | trigger와 homoglyph는 HS-00.03/04 부채로 남김 | 중간 — 범위 밖 부채는 승인으로 오해하면 안 됨 |
| R4 | G2 mutations/antiforge가 사본 검증으로 정상 통과와 의도한 실패를 확인 | 구현 확인 | `hs0001-final-g2.json` 종료값 0, `hs0001-final-g2.log` ruff43/mypy43/pytest219/mutations6/antiforge3 PASS. 독립 재실행도 종료값 0 | 원격 runner가 아님 | 중간 — 로컬 G2 증거로 충분, 원격 CI는 별도 |
| R5 | 예산 600/601/0 경계 증명 | 구현 확인 | `hs0001-final-budget-real.log`, `hs0001-final-budget-boundaries.log`, `budget-check.py:8` 같은 validator가 실제 파일과 경계를 검사 | 공용 CI 예산 장치 존재 주장은 아님이라고 README가 제한 | 낮음 — 로컬 증거로만 인정 |
| R6 | staged 전체가 커밋 가능해야 함 | 불일치 | `git diff --cached --check` 종료값 2. `codeaudit-reconsideration.md:58`, `v1-evidence.log:39`, `v1-verdict.md:62`, `v2-evidence.log:71` 등 trailing whitespace | 원문 보존 의도일 수 있으나 커밋 전 검사와 충돌 | 중간 — 커밋 흐름을 막음 |
| R7 | 비밀/민감 로그가 staged되지 않아야 함 | 불일치 | `bash verify.sh` 종료값 1: `docs/engineering/evidence/hs0001-20260910/v1-cli.log` 매치. `VERIFY_SCAN_SOURCE=index bash verify.sh`도 fail-closed | 정확한 라인은 비밀 노출 방지를 위해 공개하지 않음 | 높음 — 그대로 두면 비밀 스캔/훅이 차단하고 실제 유출 위험도 배제 불가 |

→ 좋은 소식은 핵심 9개 후보 소스와 새 회귀의 동작은 현재 증거와 맞는다는 점입니다. 나쁜 소식은 staged 전체가 커밋 전 기본 안전 검사를 통과하지 못한다는 점입니다.

## 핵심 해설

실제 입력은 `scripts/acceptance-hs-kickoff.sh`가 읽는 처분표, workflow, verification 문서, 판정 문서입니다. 처리 경로는 `scripts/verify/list-workflow-steps.py`가 workflow 정규 형식을 읽고, `acceptance-hs-kickoff.sh`가 보호 run 단계의 이름·명령·약화 키를 판정하는 구조입니다. 출력은 `PASS/FAIL` 12건과 `CHECKED: 12`입니다.

V1/V2가 깨뜨린 핵심은 “run 문자열은 그대로인데 실행 환경이 바뀌어 명령이 안 도는 경우”였습니다. 현재 후보는 최상위 `defaults/env`를 거부하고, 보호 run 스텝에서는 `name/run/id/timeout-minutes`만 허용하며, `shell/env/working-directory` 같은 실행 의미 변경 키를 약화로 판정합니다. 신규 pytest는 이 반례를 임시 저장소에서 실제로 주입하고 본 acceptance가 실패하는지 확인합니다.

G2 family도 같은 후보 상태에서 통과했습니다. `acceptance-hs-gates-mutations.sh`와 `acceptance-hs-gates-antiforge.sh`는 임시 부모에 `.github`, `docs`, `scripts`, `humansearch/src`를 복사해 원본 worktree를 직접 읽는 위조 통과를 피합니다.

## 놓친 더 나은 답

최종 보고 전에 staged 전체 기준으로 `git diff --cached --check`와 `VERIFY_SCAN_SOURCE=index bash verify.sh`를 다시 실행했어야 합니다. 이전 정적 PASS는 증거 로그가 staging되기 전 후보 기준이어서, 새로 staged된 `v1-cli.log`와 원문 로그 공백 문제를 증명하지 못했습니다.

더 나은 마감 조건은 두 가지입니다. 첫째, raw `v1-cli.log`는 git에 올리지 말고 외부 artifact 경로와 SHA256만 tracked 문서에 남기거나, 값·패턴 문자열을 라인 보존 방식으로 redaction한 사본만 stage합니다. 둘째, 원문 로그를 tracked evidence로 보존할 경우 trailing whitespace를 정리하거나, raw 원본은 git 밖에 두고 해시만 남깁니다.

## 적대 반박

강한 반론은 “비밀 스캔 매치는 실제 비밀이 아니라 Claude 로그 안의 패턴 문자열일 수 있고, trailing whitespace는 원문 증거 보존을 위해 필요하다”입니다. 이 반론은 일부 타당합니다. 실제 값인지 패턴 텍스트인지는 공개하지 않았고, raw 증거 보존 요구도 있습니다.

그래도 결론은 바뀌지 않습니다. 현재 저장소의 `verify.sh`와 pre-commit 계약은 비밀 패턴 매치가 있으면 fail-closed로 닫습니다. `git diff --cached --check`도 커밋 전 검사로 쓰였고 지금 실패합니다. 원문 보존이 필요하면 raw 파일을 git 밖에 두고 SHA256·경로·접근 권한을 남기는 방식으로 계약을 바꿔야 합니다.

## 근거 장부

| 주장 | 판정 | 1차 근거 | 근거 강도 | 미확인 사항 |
|---|---|---|---|---|
| 새 pytest 8개 통과 | 확인 | `uv run --no-sync pytest -q tests/test_hs_0001.py tests/test_hs_0001_main_compat.py` 종료값 0, 8 passed | 직접 재실행 | GitHub runner |
| 기존 hs-kickoff 변이 37개 통과 | 확인 | `bash scripts/acceptance-hs-kickoff-mutations.sh` 종료값 0, CHECKED 37 | 직접 재실행 | 없음 |
| G2 family 통과 | 확인 | `hs0001-final-g2.json` 종료값 0, 독립 재실행 종료값 0 | artifact 대조 + 직접 재실행 | 원격 CI |
| staged 소스 지문 일치 | 확인 | 9개 파일 worktree/index SHA 모두 manifest와 일치 | 직접 계산 | final commit SHA |
| staged 전체 diff check 실패 | 확인 | `git diff --cached --check` 종료값 2 | 직접 재실행 | 수정 후 재실행 |
| staged 전체 비밀 스캔 실패 | 확인 | `bash verify.sh` 종료값 1, `v1-cli.log` file-level match | 직접 재실행 | 매치 라인/값은 미공개 |

→ 이 표는 사실과 추론을 분리합니다. PASS 근거는 후보 9개와 검증 명령에 대해 강하고, FAIL 근거는 현재 staged 전체의 커밋 가능성에 대해 강합니다.

## 반복 질문 조사

대화 전체 반복 횟수 조사는 요청 범위가 아니며 현재 보관 세션 검색을 수행하지 않았습니다. 이번 감사에서 반복으로 본 것은 V1/V2가 이미 지적한 F1~F4가 현재 후보에서 다시 닫혔는지뿐입니다.

## 검증 신뢰도와 우선순위

실행한 주요 명령은 다음과 같습니다. `uv run --no-sync pytest -q tests/test_hs_0001.py tests/test_hs_0001_main_compat.py`는 8 passed, `bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-kickoff.sh`는 CHECKED 12, `bash scripts/acceptance-hs-kickoff-mutations.sh`는 CHECKED 37, G2 family 직접 재실행은 mutations 6/6과 antiforge 3/3까지 종료값 0이었습니다. `git diff --cached --check`와 `bash verify.sh`는 실패했습니다.

우선순위는 높음 1건, 중간 1건입니다.

1. 높음 — `v1-cli.log`를 staged 상태에서 제거하거나 redaction한 뒤 `VERIFY_SCAN_SOURCE=index bash verify.sh`와 `bash verify.sh`를 모두 통과시켜야 합니다. 그대로 두면 커밋 전 비밀 검사와 실제 보안 판단이 막힙니다.
2. 중간 — staged 증거 원문의 trailing whitespace를 정리하거나 raw 원문을 git 밖으로 옮긴 뒤 `git diff --cached --check`를 통과시켜야 합니다. 그대로 두면 커밋 전 위생 검사가 실패합니다.

이 두 문제가 해결되면, 현재 확인 범위에서는 HS-00.01 로컬 후보 9개 파일의 계약·처리·출력·검증 연결은 PASS로 바꿀 수 있습니다. 단 그때도 원격 CI, 병합, 실제 제품/포털 완료, HS-00.02~04 부채 완료는 별도입니다.
