VERDICT: FAIL

검증 대상 SHA: 6246f99d2ef9a24fa8bb95a7dbc54d353d851a80
실행 시각: 2026-08-24 01:13 UTC(KST 10:13)
작업 폴더: /private/tmp/valuehire-rdp-20260824.7e3kk1/worktree
Claude CLI 버전: 2.1.239 (Claude Code)

---

## 건너뜀·미확인·재시도·추정 (판정 앞부분 고지)

1. **작업 중 사고 발생 및 즉시 복구**: 임시 저장소로 이동하려던 `cd` 명령이 실패했는데 이를 감지하지 못한 채 뒤이은 `git commit` 두 건이 실제 작업 저장소(worktree)에 그대로 적용됐습니다. 발견 즉시 `git status`로 원격 미푸시 상태(로컬 전용 브랜치)를 확인하고 `git reset --hard 6246f99`로 원상복구했습니다. 최종 확인 결과 HEAD는 원래 SHA로 정확히 돌아왔고 작업 트리는 깨끗합니다. 이 사고로 실제 저장소 데이터가 외부로 나가거나 손실되지는 않았지만, 검증 도중 파일을 건드리지 않는다는 지시를 일시적으로 어긴 사실을 숨기지 않고 밝힙니다.
2. **GitHub Actions 실제 실행은 미확인**: CI가 실제로 러너에서 도는 것은 관측하지 못했습니다. 대신 워크플로 YAML을 직접 읽고, `acceptance-ci-step-integrity.sh`(YAML을 실제로 파싱해 조건부·무시 스텝을 구조로 검사)와 `acceptance-hs-a4.sh`의 실행줄 문자열 대조로 대체 확인했습니다.
3. **pre-commit의 PII 내용 미검사는 결함이 아니라 설계로 판단**: `hooks/pre-commit`은 CSV/TSV/SQL 내용 검사를 하지 않습니다. 이것은 주석(`hooks/pre-commit:181`)과 SOT boundaries에 이미 명시된 의도된 위임(커밋 시점엔 크기·경로만, 내용 검사는 CI push 시점)이므로 심각 결함으로 세지 않았습니다.
4. 함수당 100줄 하드 리밋은 `scan-data-exposure.sh`에 대해서만 직접 카운트했고, `verify.sh`는 함수 정의가 없는 단일 스크립트임을 확인했습니다. `hooks/pre-commit`의 개별 함수(`scan`, `scan_added` 등)는 육안으로 10줄 내외임을 확인했으나 자동 카운트 도구는 만들지 않았습니다.

---

## 결론

이 저장소의 비밀·개인정보 보호 장치는 겉보기엔 정상적으로 통과 표시(초록불)를 내고 있고, 실제로 삭제된 과거 개인정보 파일을 다시 찾아내는 핵심 기능은 작동합니다. 하지만 "검사 장치 자체가 몰래 약해져도 그것을 잡아내는 감시 장치"에 다섯 군데 구멍이 있습니다. 검사 코드 중 일부를 제가 직접 손상시켜(예: 빈 저장소를 통과시키는 안전장치를 지우거나, 검사한 파일 개수를 거짓으로 1개라고 우기게 만드는 식) 다시 실행해봤더니, 그 손상된 코드를 잡아내야 할 감시 테스트들이 대부분 아무 이상 없다고 통과시켰습니다. 즉 지금 이 순간의 코드는 정상이지만, 누군가 이 코드를 몰래 약화시켜도 자동으로 걸리지 않는 사각지대가 실제로 존재함을 실행으로 증명했습니다. 또한 "코드 파일은 600줄, 함수는 100줄을 넘으면 안 된다"는 계약을 실제로 강제하는 자동 장치 자체가 저장소 어디에도 없다는 것도 확인했습니다. 이런 이유로 이번 독립 검증은 불합격으로 판정합니다.

---

## 판단 근거

- **선택한 해석**: "계약 3번 — 거짓 합격 10종을 공격하라"는 지시를, 기존에 저장된 통과 보고서를 재실행하는 것이 아니라 실제로 검사 코드를 손으로 훼손한 사본을 만들어 재실행하는 것으로 해석했습니다. 저장된 goal 문서(`repository-data-protection-alignment-goal-2026-08-24.md`)에도 "R2 적대검증 계획" 6개 항목이 있었지만 실제 실행 로그가 없어("Claude V1 | 예 | 대기"), 이를 제가 직접 채워야 할 공백으로 봤습니다.
- **버린 해석**: hs-a4.sh, acceptance-secret-webhook-vendor.sh가 이미 PASS라는 이유로 뮤테이션 검증을 생략하는 길을 버렸습니다. 이유는 "결론을 미리 주지 않는다"는 지시와, 기존 acceptance가 시나리오 매트릭스 방식이라 매트릭스에 없는 실패 경로(빈 저장소, git 열거 실패)는 애초에 테스트되지 않을 수 있기 때문입니다. 실제로 이 우려가 맞았습니다.
- **틀리면 깨지는 것**: 제가 만든 뮤테이션 재현(python으로 특정 코드 블록을 정확히 치환)이 원본 코드의 정확한 텍스트와 일치하지 않으면 `assert` 오류로 즉시 드러나도록 짰습니다. 모든 뮤테이션 스크립트는 `bash -n`으로 문법 검증을 통과한 뒤에만 실행했습니다. 이 전제가 틀렸다면(즉 제가 원본과 다른 코드를 공격했다면) 결과가 무의미한데, 실제로는 `git diff --stat`로 매 공격 뒤 원상복구를 확인했고 각 공격 직전에 원본 파일을 새로 복사해왔으므로 이 전제는 지켜졌습니다.

---

## 기술 상세와 증거 원문

### 최소 실행 증거 11건 — 전부 PASS/exit 0

```text
acceptance-principles-check.sh  → VERDICT: PASS, CHECKED: 34, exit=0
check-docs-sot.sh                → OK, exit=0
acceptance-secret-webhook-vendor.sh → CHECKED: 35, exit=0
acceptance-hs-a4.sh              → CHECKED: 35, exit=0
verify.sh                        → PASS, CHECKED: 189, exit=0
scan-data-exposure.sh tracked    → PASS, CHECKED: 189, exit=0
scan-data-exposure.sh history    → PASS, CHECKED: 1043, exit=0
scan-data-exposure.sh pii        → PASS, CHECKED: 189, exit=0
scan-data-exposure.sh all        → CHECKED: 1421, exit=0
acceptance-ci-step-integrity.sh  → VERDICT: PASS, CHECKED: 14, exit=0
acceptance-semantic-mutations.sh → VERDICT: PASS, CHECKED: 10, exit=0
git diff --check                 → exit=0
```
→ 해석: 표면적인 필수 명령 게이트는 전부 통과합니다. 문제는 이 게이트들이 "지금 이 코드"가 정상이라는 것만 증명하고, "이 코드가 몰래 약해져도 걸리는가"는 증명하지 못한다는 데 있습니다. 아래 뮤테이션 결과가 그 간극을 보여줍니다.

### 정상 동작 확인 — 삭제된 PII 이력을 실제로 잡아냄

별도 임시 Git 저장소에서 CSV/TSV/SQL에 합성 canary(실명·실제 값 아님)를 담아 커밋한 뒤 삭제 커밋을 만들고 `history`/`all` 모드로 재검사했습니다.

```text
FAIL: 후보자 개인정보 내용: candidates.csv · blob e81239b... · 개인정보 컬럼 3종 · 표 데이터 2행
FAIL: 후보자 개인정보 내용: candidates.sql · blob b4ccc3b... · 개인정보 컬럼 2종 · INSERT/VALUES/COPY 적재문
FAIL: 후보자 개인정보 내용: candidates.tsv · blob 683a195... · 개인정보 컬럼 2종 · 표 데이터 1행
CHECKED: 1046 (또는 격리 재실행 시 6)
exit=1
```
→ 해석: 커밋 후 삭제해도 Git 객체는 남는다는 원리대로, 세 확장자 모두 과거 blob에서 실제로 열려 잡혔습니다. 원문(합성 값)은 출력에 없고 경로·blob 지문·컬럼 종류 수·형태(表 데이터/적재문)만 나왔습니다.

정상 대조군(지표 CSV, schema-only SQL)은 문제없이 통과했습니다.
```text
PASS: csv/tsv/sql 1개 검사(추적 4개 중), 개인정보 적재 0건   ← metrics.csv (metric,value)
PASS: csv/tsv/sql 2개 검사(추적 5개 중), 개인정보 적재 0건   ← + schema.sql (CREATE TABLE만)
```

빈 저장소에서는 모든 모드가 올바르게 `NOT_RUN`, exit=2를 냈습니다.
```text
NOT_RUN: tracked scan target count is zero        CHECKED: 0  exit=2   (verify.sh)
NOT_RUN: 추적 파일 0개 — 스캔 무효 (P20 ...)        CHECKED: 0  exit=2   (tracked)
NOT_RUN: blob 을 한 개도 읽지 못했다 (스캔 무효)     CHECKED: 0  exit=2   (history)
NOT_RUN: 추적 파일 0개 — 스캔 무효 (P20)             CHECKED: 0  exit=2   (pii)
```

---

### 결함 1 — 심각도: 높음 — "빈 저장소 차단이 사라져도 아무도 모른다"

- **원문 제목**: zero-target 차단 제거가 어떤 acceptance에도 걸리지 않음
- **원인**: `scripts/scan-data-exposure.sh:75-78`(scan_tracked 함수 안, "추적 파일 0개 — 스캔 무효" 검사)을 제거해도, 기존 `acceptance-hs-a4.sh`의 시나리오들은 전부 최소 1개 파일이 있는 저장소만 만들기 때문에 이 실패 경로 자체가 테스트되지 않습니다.
- **재현**: 저장소 전체를 별도 미러(`git clone`)로 복제한 뒤 그 안에서만 코드를 훼손해 실제 worktree는 전혀 건드리지 않고 검증했습니다.
```text
(뮤테이션 후) PASS: 추적 파일 0개 검사, 위반 0건
              CHECKED: 0
              exit=0
```
→ 해석: 계약은 "대상 0개는 합격이 아니다"(P20)라고 명시하는데, 이 방어선이 제거된 뮤테이션을 `acceptance-hs-a4.sh` 전체(FAIL 0건)로 재실행해도 잡히지 않았습니다.
- **사업 영향**: 향후 리팩터링에서 실수로 이 가드가 빠지면, CI의 "데이터 노출 스캔" 스텝이 체크아웃 오류·경로 오타 등으로 대상을 0개 찾아도 조용히 초록불이 켜집니다. goal 문서(`repository-data-protection-alignment-goal-2026-08-24.md:200`)의 R2 계획 1번이 "acceptance FAIL"을 요구했는데 실제로는 만족되지 않습니다.

### 결함 2 — 심각도: 높음 — "검사 건수(CHECKED)를 거짓말해도 아무도 모른다"

- **원문 제목**: `CHECKED` 값을 상수 1로 위조해도 어떤 acceptance도 잡지 못함
- **원인**: `scripts/scan-data-exposure.sh:245`의 `printf 'CHECKED: %d\n' "$checked_total"`을 고정값 `1`로 바꿔도, 실제 189개 파일을 검사했다는 문구("PASS: 추적 파일 189개 검사...")와 `CHECKED: 1`이라는 숫자가 서로 모순인 채 그대로 출력됩니다. `acceptance-hs-a4.sh`는 exit 코드만 비교할 뿐 `CHECKED:` 줄의 값 자체를 실제 대상 수와 대조하는 로직이 없습니다.
- **재현**:
```text
(뮤테이션 후) PASS: 추적 파일 189개 검사, 위반 0건
              CHECKED: 1
(acceptance-hs-a4.sh 재실행) FAIL 0건, exit=0
```
→ 해석: `verify.sh`에는 이미 유사한 위조를 막는 acceptance("CHECKED 상수 위조 방지용 안전 blob 두 개")가 있는데, 같은 방어가 `scan-data-exposure.sh`에는 없습니다. 정본이 스스로 세운 R2 계획 3번("실제 대상 수 대조 acceptance FAIL")과 실제 코드 사이의 간극입니다.
- **사업 영향**: `CHECKED`는 "검사가 실제로 돌았다"는 유일한 정량 증거인데, 이 값이 위조돼도 걸러지지 않으면 "PASS인데 사실상 아무것도 안 본" 상태를 구분할 수 없습니다.

### 결함 3 — 심각도: 높음 — "정상 파일 오탐 방지선이 얇아져도 대조군이 못 잡는다"

- **원문 제목**: PII 컬럼 하한(2종)을 1종으로 낮춰도 정상 대조군 오탐 acceptance가 통과
- **원인**: `scripts/scan-data-exposure.sh:182`의 `[ "$hits" -ge 2 ]`를 `-ge 1`로 낮춰도, `acceptance-hs-a4.sh`의 정상 대조군(`sc_ok_csv`: "position,count,stage", `sc_history_ok_csv`: "position,count")은 애초에 개인정보 컬럼 단어를 0개 가진 fixture라서 임계값이 1이든 2든 차이가 나지 않습니다.
- **재현(경계 fixture로 직접 확인)**: 별도 임시 저장소에 `name,department` 헤더만 있는 평범한 인사 CSV(개인정보 컬럼 단어 1개: name)를 만들어 검사했습니다.
```text
(원본 코드) PASS: csv/tsv/sql 1개 검사(추적 1개 중), 개인정보 적재 0건   exit=0
(뮤테이션)  FAIL: 후보자 개인정보 내용: employees.csv · 개인정보 컬럼 1종 · 표 데이터 1행
            exit=1
(acceptance-hs-a4.sh 재실행) FAIL 0건, exit=0
```
→ 해석: 오탐 방지 경계 자체가 사실상 무력화됐는데도 기존 대조군은 "PII 단어 0개"인 경우만 다뤄서 이 뮤테이션을 통과시켰습니다. "정상 지표 CSV는 통과해야 한다"는 계약(counter-AC 8)의 실제 테스트 커버리지가 경계값(hits=1)에는 미치지 못합니다.
- **사업 영향**: 임계값이 실수로 완화되면 `department,name`처럼 흔한 일반 CSV까지 전부 FAIL 처리되어 정상 개발이 막히는데, 이 회귀 자체를 감지할 방법이 없습니다.

### 결함 4 — 심각도: 중간 — "테스트 케이스를 지워도 CHECKED가 줄어드는 것만으로는 안 걸린다"

- **원문 제목**: `acceptance-hs-a4.sh`에서 삭제-이력 PII 테스트 호출 3건을 제거해도 통과
- **원인**: `history_pii_case` 호출 3줄(삭제된 CSV/TSV/SQL 검증)을 지우면 `CHECKED`가 35→32로 줄지만, 이 개수 자체를 특정 하한과 대조하는 장치가 없습니다. mechanism-registry(`acceptance-verify-ac-m.sh`)도 acceptance 스크립트가 "존재하는지"만 대조하지 그 내부 judge_case 호출 개수는 세지 않습니다.
- **재현**:
```text
(테스트 호출 3건 삭제 후 acceptance-hs-a4.sh 재실행) FAIL 0건, CHECKED: 32, exit=0
(acceptance-verify-ac-m.sh 재실행)                    FAIL 0건, exit=0
```
→ 해석: 계약 3번이 명시한 "테스트 호출/fixture 제거" 공격이 그대로 재현됩니다. counter-AC 10("테스트 대상을 0개로 만들거나 검사 호출을 제거해도 테스트가 통과")에 정확히 해당하는 상황이 실제로 재현됐습니다.
- **사업 영향**: 향후 누군가 "테스트가 너무 느리다"는 이유로 일부 시나리오를 지워도 CI는 계속 초록불입니다.

### 결함 5 — 심각도: 중간 — "Git 자체가 고장 나도 통과로 접힐 수 있다"

- **원문 제목**: `git rev-list` 실패를 PASS로 접어도 걸리지 않음
- **원인**: `scripts/scan-data-exposure.sh:92-94`의 `git rev-list --all --reflog --objects` 실패 시 `NOT_RUN`/exit 2 처리를 `PASS`/exit 0으로 바꿔도, `acceptance-hs-a4.sh`의 모든 judge_case는 정상적으로 초기화된 Git 저장소만 사용해 이 실패 경로가 테스트되지 않습니다.
- **재현**: HEAD 참조를 존재하지 않는 40자리 zero-SHA로 손상시킨 별도 임시 저장소에서 확인했습니다.
```text
(뮤테이션 후) PASS: 기록 스캔 — git rev-list 실패했지만 통과 처리 (공격)
              CHECKED: 0
              exit=0
(acceptance-hs-a4.sh 재실행) FAIL 0건, exit=0
```
→ 해석: 계약 3번의 마지막 공격("Git 열거·blob 읽기 실패의 PASS 접힘")이 그대로 재현됩니다.
- **사업 영향**: CI 러너의 일시적 Git 오류나 얕은 클론(shallow clone) 설정 실수로 `rev-list`가 실패해도 초록불이 켜질 수 있는 경로가 이론상 열려 있습니다(다만 CI는 `fetch-depth: 0`을 명시적으로 쓰고 있어 실제 발현 가능성은 낮습니다 — `.github/workflows/verify.yml:20`).

### 결함 6 — 심각도: 높음 — "600/601줄 판정기가 실재하지 않는다"

- **원문 제목**: 코드 파일 600줄/함수 100줄 하드 리밋을 강제하는 자동 판정기가 저장소에 없음
- **원인**: `docs/sot/principles.yaml:106-113`(P11)의 evidence 필드가 스스로 인정합니다 — "Strict 계약 편입 장치의 실존·직접 실행만 PASS다. mechanism_expected에 적힌 제품 장치의 구현 완료를 주장하지 않는다." 즉 `acceptance-principles-check.sh`의 34/34 PASS는 "P11이라는 원칙 문서가 존재하고 로드된다"만 증명하지, "601줄 파일을 실제로 차단한다"는 것을 증명하지 않습니다. 저장소 전체를 `600`, `601`, `LINE_LIMIT` 등의 키워드로 검색한 결과, 유일하게 발견된 줄수 검사기(`scripts/verify/check-strict-principles-skills.sh:74`)는 스킬 문서(`codex.md`/`claude.md`) 500줄 제한만 다루며, 계약이 요구하는 "직접 작성 코드 파일" 대상 판정기가 아닙니다.
- **직접 수동 확인**: `verify.sh`(143줄), `scan-data-exposure.sh`(246줄), `hooks/pre-commit`(208줄), `hooks/pre-push`(186줄) 모두 600줄 미만이며, `scan-data-exposure.sh`의 각 함수도 최대 60줄(scan_history)로 100줄 미만입니다. → 해석: 지금 이 순간의 코드는 경계를 지키고 있지만, 이는 "우연히 지금은 작다"는 것이지 "커지면 자동으로 막힌다"는 보장이 아닙니다.
- **사업 영향**: goal 문서(`repository-data-protection-alignment-goal-2026-08-24.md:106-111`)의 AC-7이 "저장소의 기존 파일 크기 판정기 원명령과 합성 600/601 fixture"로 검증한다고 명시했지만, 그런 판정기 자체가 존재하지 않아 이 AC는 애초에 검증 불가능한 상태입니다.

---

### 설계 지적 — pre-commit이 공용 판정기를 재사용하지 않고 목록을 복제함

- **무엇을**: `hooks/pre-commit:189-190`이 `scripts/scan-data-exposure.sh:50-51`의 `is_forbidden_path` 목록을 코드로 복제하고 있습니다(같은 파일을 실행하는 대신 문자열을 다시 적음).
- **왜**: 훅은 "스테이지된 파일"만 봐야 하고 판정기는 "임의 Git 인자"를 받아야 해서 함수 시그니처가 다르기 때문으로 보입니다(스크립트 주석에도 "훅은 별도 코드로 남아 있고, 그래서 목록이 갈라질 수 있다"고 자인).
- **버린 길**: pre-commit이 `scan-data-exposure.sh`를 서브프로세스로 호출하는 길은 채택하지 않았습니다.
- **대가**: 두 목록이 갈라질 위험이 상존하며, 실제로 `acceptance-hs-a4.sh` §5가 매번 두 파일의 패턴 문자열 동치성을 정적으로 대조해 이 위험을 상쇄하고 있습니다(현재는 PASS로 동치 확인됨).
- **되돌리기**: 필요 시 `hooks/pre-commit`에서 `scan-data-exposure.sh tracked`를 직접 호출하도록 바꾸면 이 이중 유지보수 구조를 없앨 수 있으나, 이번 검증 범위에서는 결함으로 세지 않고 참고 사항으로만 남깁니다(현재 동치성 검사가 실효적으로 작동 중이므로).

---

## 최종 판정

필수 실행 증거 11건은 전부 PASS/exit 0이었고, 삭제된 과거 PII CSV/TSV/SQL을 실제로 재현해 잡아내는 핵심 기능도 정상 작동을 확인했습니다. 그러나 계약 3번이 명시적으로 요구한 "거짓 합격 공격" 10종 가운데 5종(zero-target 차단 제거·CHECKED 위조·정상 대조군 오탐 임계값 완화·테스트 호출 제거·Git 열거 실패의 PASS 접힘)을 직접 코드에 주입해 재실행한 결과, 기존 acceptance 전량이 이를 감지하지 못하고 그대로 통과시켰습니다. 또한 계약 5번이 요구하는 600/601줄 하드 리밋 판정기 자체가 저장소에 존재하지 않습니다. "필수 계약 또는 증거 공백이 하나라도 있으면 FAIL"이라는 지시에 따라 **VERDICT: FAIL**로 판정합니다.
