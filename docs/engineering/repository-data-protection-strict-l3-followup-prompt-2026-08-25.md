# Repository Data Protection — Strict L3 후속 구현 프롬프트 + 공격감사 델타

아래 첫 블록은 최초 Strict L3 프롬프트를 그대로 보존한다. 두 번째 블록은 첫 블록의 어떤 요구도 삭제하거나 대체하지 않고 뒤에 추가한다.

## 최초 Strict L3 프롬프트 — 보존본

```text
$strict

ValueHire_v6의 repository-data-protection 후속 보완 작업을 Strict L3로 수행하라.

기준 HEAD fdac401be104bc5d9454401edf0477fb478636dc에서 새 격리 worktree/후속 브랜치를 만들고, 원본 dirty worktree는 수정하지 않는다. push, PR, merge, deploy는 금지한다.

Human Review에서 다음 세 결함이 현재 HEAD에 재현됐다.
HR-1: INSERT/INTO/VALUES 사이에 줄바꿈·탭이 있는 개인정보 적재 SQL을 커밋 후 삭제하면 history와 all이 PASS/0이다.
HR-2: git ls-files -z가 경로 하나를 출력한 뒤 exit 1이면 tracked, pii, all이 PASS/0이다.
HR-3: 이름·이메일이 포함된 PII 파일 경로는 history 위반 로그에 원문이 노출된다. printf %q는 개인정보 비식별화가 아니다.

허용 변경은 scripts/scan-data-exposure.sh, scripts/acceptance-hs-a4.sh, repository-data-protection SOT/verification 문서, 새 후속 goal/V1/V2 기록으로 제한한다. verify.sh/workflow/hooks는 실제 회귀가 없으면 변경하지 않는다. 새 의존성·PII 판정 함수 복제·기존 판정 기록 수정은 금지한다.

합격 조건:
1) 다중 행/탭 SQL 적재문을 현재 pii, 삭제 history, all 모두 exit 1로 차단한다.
2) schema-only/비적재 SQL은 통과한다.
3) git ls-files가 일부 NUL 경로를 출력한 뒤 실패하면 tracked/pii/all은 PASS 없이 NOT_RUN/2이고 CHECKED는 실제 완전 처리 수다.
4) 이름·이메일·전화번호가 경로에 있어도 stdout/stderr에 원문이 없다. PII 위반 로그에는 원본 경로 대신 비가역 path fingerprint, 형식, blob fingerprint, 컬럼 수, 데이터 형태만 출력한다.
5) 현재/history는 scan_pii_content 한 함수를 공유한다.
6) 기존 단일행 CSV/TSV/SQL, 삭제 기록, alias, 특수문자 경로, 정상 controls, zero-target/CHECKED, 600/601 및 100/101은 회귀하지 않는다.

테스트 우선:
- current/history/all 다중행 SQL
- tracked/pii/all partial git ls-files failure
- current/history PII-in-path non-disclosure
- schema-only control
을 acceptance에 추가해 RED를 기록한 뒤 GREEN으로 만든다.

Mutation:
- SQL multiline 판정 제거
- ls-files exit 확인 제거
- raw/%q path 출력 복원
- 새 acceptance 호출 제거
- CHECKED 고정
- history shared PII 호출 제거
각각 acceptance가 실패해야 한다.

구현 제약:
- git 추적 목록은 상태 확인 가능한 임시 NUL 목록으로 먼저 수집하고 성공한 목록만 tracked/pii가 재사용한다.
- SQL whitespace는 줄바꿈/탭을 허용한다.
- 실제 SQL/PII 원문은 출력하지 않는다.
- 파일 600줄/함수100줄, 새 의존성 없음.

필수 검증:
principles, docs SOT, secret acceptance, data acceptance, verify, tracked/history/pii/all, CI integrity, semantic mutations, git diff --check, shellcheck, 모든 새 targeted 반례, 원본 dirty 상태/SOT hash 대조. 명령별 시각/PWD/exit/CHECKED/전체 출력을 goal에 기록한다.

Claude V1과 새 맥락 Codex V2가 새 최종 구현 SHA를 독립 공격한다. G/V1/V2가 갈리거나 FAIL이 남으면 PASS 금지. Lore 로컬 커밋까지만. GitHub-hosted Actions 미실행과 P23 원격 UNVERIFIED/NOT_RUN을 공개한다. 최종 humanreview APPROVE 전 완료 선언 금지.
```

## 추가 공격감사 델타 — 기존 Strict L3 요구를 삭제·대체하지 않음

현재 `fdac401be104bc5d9454401edf0477fb478636dc`에는 다음 결함이 재현됐다.

1. `scan-data-exposure.sh`의 tracked/pii가 `git ls-files` 부분 출력 후 실패를 감지하지 못한다. 부분 목록은 검사 성립으로 인정하지 말고 `NOT_RUN`, `CHECKED: 0`, PASS 0줄, exit 2로 처리한다.
2. all은 세 하위 출력을 버퍼링한다. 하나라도 `NOT_RUN`이면 최종 PASS는 0줄이고 exit 2다. 이미 발견된 FAIL은 숨기지 않는다. `CHECKED`는 정상적으로 완료된 하위 검사의 실제 처리 수만 합산하며, `NOT_RUN` 하위는 0으로 센다. 정확한 exit, PASS/FAIL/NOT_RUN 개수와 `CHECKED`를 acceptance에서 검증한다.
3. SQL 판정은 판정용 사본에서 주석과 작은따옴표 문자열 내용을 제거한 후 `INSERT`/`INTO`/`VALUES`/`COPY`를 줄바꿈을 포함한 공백 단위로 판정한다. 현재/history는 기존 `scan_pii_content` 한 함수를 계속 공유한다.
4. 반드시 다음 사례를 RED로 먼저 재현한다: `INSERT`, `INTO`, `VALUES`가 서로 다른 줄에 있는 현재·삭제 history SQL; 주석과 개행이 함께 있는 INSERT 적재문; 주석 안에만 INSERT가 있는 정상 SQL; 문자열 안에만 INSERT/VALUES가 있는 정상 SQL; 부분 `git ls-files` 실패 후 tracked/pii/all의 거짓 PASS. all의 부분 목록 RED는 history가 잡아버리지 않도록 미커밋 또는 staged PII로 만든다.
5. stdout/stderr 어디에도 원문 경로를 출력하지 않는다. 금지경로, 크기초과, PII FAIL, 경로 포함 NOT_RUN 모두 동일하다. 경로는 명세가 고정된 결정론적 가명 fingerprint로 출력하고, 삭제된 history 경로까지 로컬에서 역조회할 수 있는 절차와 충돌 처리를 SOT에 기록한다.
6. `acceptance-hs-a4.sh`와 `acceptance-semantic-mutations.sh` 자신의 Git 대상 수집도 부분 출력 후 실패를 감지해야 한다. 실제 Git 대상 수와 acceptance가 센 대상 수를 정확히 비교하며 하한 비교만 사용하지 않는다.
7. 새 repository-data-protection acceptance를 추가하면 같은 커밋에서 다음을 모두 수행한다: `verify.yml`에서 `run-acceptance.sh` 경유로 정확히 한 번 호출; `verification-commands.md` CI 표 등록; 기존 CI 연결 독립 검사기가 호출 삭제 mutation 차단; `acceptance-hs-a4.sh` 코드 예산 대상에 신규 파일 추가.
8. 현재 브랜치의 `check-docs-sot.sh`가 실제로 하지 않는 catalog와 `surface_coverage` 검사를 `verification-commands.md`에서 주장하지 않는다. 원본 dirty worktree의 미커밋 검사기를 격리 브랜치 실행 증거로 사용하지 않는다. 이 전역 검증 체계 결함을 이번 범위에서 고치지 않으면 명시적 잔여 `REQUEST_CHANGES`로 기록하고 PASS 근거에서 제외한다.
9. 기존 프롬프트의 EARS AC, counter-AC, RED→GREEN, R2 mutation, 원명령 전체 출력, 시각/PWD/exit/CHECKED 기록, 600/601·100/101 경계, 원본 dirty 보존, Claude V1/Codex V2/humanreview, Lore 로컬 커밋 조건은 모두 유지한다.

완료 조건:

- 위 mutation을 제거하면 acceptance가 반드시 실패한다.
- 개인정보 원문 및 원문 경로 출력 0건이다.
- 현재/history/all의 SQL·Git 오류 계약이 일치한다.
- `check-docs-sot` 허위 PASS를 완료 근거로 사용하지 않는다.
- fresh humanreview가 `APPROVE`다.
- 원격 CI가 없으면 P23은 `NOT_RUN`으로 공개한다.
- FAIL/NOT_RUN이 남으면 완료라고 보고하지 않는다.

검증 기록은 기존 hs-a4 exit 0/CHECKED 48, CI integrity exit 0/CHECKED 14, semantic mutations exit 0/CHECKED 10, verify/tracked/pii exit 0, 적대 harness의 우회·오탐 재현, all 수동 중단 exit 130을 출발점으로만 사용한다. fresh 전체 검증을 대신하지 않는다. 격리 브랜치는 clean `fdac401…`, 원본은 dirty `3094eef…` 41건이고, 공통 조상 `c59bad7…` 이후 갈라졌으므로 현재 상태를 병합 준비 완료로 주장하지 않는다. 같은 범주 요청은 현재 세션에서 다섯 번째다.

결정: 최초 두 결함을 고친 커밋은 보존하고, 이 델타를 적용한 뒤 다시 감사한다. 현재 상태는 병합 불가다.
