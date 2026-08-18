# 결론

현재의 경고 표시는 사람이 임의로 바꿀 수 있고, 실제로 변경을 합치지 못하게 막지도 않습니다.
이번 작업은 현재 변경 묶음의 지문과 위험 신호를 별도 자동 검사에 남기되, 경고 표시와 합치기 권한은 건드리지 않습니다.

# 판단 근거

현재 서버에는 `verify`(= 저장소가 정한 검사를 실행해 성공·실패를 보여 주는 자동 검사) 하나만 있고,
라벨(= 변경 화면에 붙이는 분류 표시)을 읽거나 쓰는 코드가 없습니다. 그런데 정본은 `weakens-check`
(= 검사나 계약을 건드렸음을 알리는 표시)가 없으면 합칠 수 없다고 적어 실제 강제 수준을 과장합니다.

그래서 첫 단계는 check-run(= GitHub 변경 화면에 남는 자동 검사 결과) 자체를 현재 head SHA
(= 검토 대상 마지막 기록의 고유 지문)에 묶는 것입니다. 이 판정은 base SHA(= 비교 기준 기록의 지문)부터
head SHA까지의 전체 변경을 다시 읽어 커밋 수·파일 수·파일 명부·위험 신호를 계산합니다. 라벨은 입력으로
읽지 않고 출력도 바꾸지 않습니다. 지금은 advisory(= 참고용이며 합치기를 강제로 막지 않는 상태)로만 둡니다.

## 결정 카드

**무엇을** — 현재 기록 지문과 전체 변경 명부에 묶인 참고용 검토 판정을 별도 자동 검사로 만듭니다.
**왜** — 사람이 바꿀 수 있는 경고 표시를 승인 권한으로 믿으면 표시와 실제 코드가 갈라져도 합격할 수 있기 때문입니다.
**버린 길** — 경고 표시가 붙었는지를 합격 조건으로 읽는 방식과, 권한이 큰 사건에서 외부 변경 코드를 실행하는 방식은 조작·권한 오용 위험 때문에 버립니다.
**대가** — 아직 합치기를 막지 않으므로 오탐을 관찰할 수 있지만, 보호 설정 전까지 우회도 가능합니다.
**되돌리기** — 새 자동 검사 파일·판정기·인수 검사를 한 변경으로 되돌리면 기존 `verify`만 남습니다. 데이터나 운영 상태는 바뀌지 않습니다.

# 증거 원문

## 1. 현재 상태

- `.github/workflows/verify.yml:1-16` — 현재 서버 자동 검사는 `verify` 하나이며 읽기 권한만 사용합니다.
- `.github/workflows/verify.yml:5-9` — 현재 검사는 모든 업로드와 변경 요청에서 실행되지만, 검토 상태를 따로 계산하지 않습니다.
- `docs/sot/coding-principles.md:28` — 정본은 검사·계약 변경이 `weakens-check` 없이 합쳐질 수 없다고 적습니다.
- `docs/sot/verification-commands.md:18-44` — 실제 서버 검사는 `verify.yml`의 17단계뿐이고, 새 인수 검사는 서버에 직접 연결해야 한다고 적습니다.
- `docs/sot/git-workflow.md:19-28` — 정본은 기준 브랜치 보호를 요구하지만 실제 기계 강제 여부는 미확인이라고 동시에 적습니다.
- `worktrees/position-map-prompt-audit/docs/engineering/verdicts/codeaudit-pr23-label-system-2026-08-18.md:175-186` — 라벨 자동 판정·승인·재검토·필수 검사가 모두 없다는 감사 결과입니다.
- 같은 감사 문서 `:192-247` — 현재 기록에 묶인 판정이 정본이고 라벨은 화면 표시만 맡아야 하며, 외부 변경 코드에 큰 권한을 주지 말라고 정합니다.

```text
$ bash scripts/session-status.sh
HEAD: ab851a2 (synced)
ORIGIN: ab851a2
RED: 0/20 (acceptance-0-7.sh 제외 — CI 담당)
exit=0
```

→ 무엇을 시켰나: 새 작업 시작 전에 기준 브랜치와 원격 기록, 기존 인수 검사 20개를 다시 확인했습니다.
→ 무엇이 나왔나: 두 기록이 같고 실패한 검사는 0개이며 프로그램 성적도 0이었습니다.
→ 좋은 소식인가: 새 결함 수리를 시작할 자격이 있습니다. 제외된 1개는 정본이 서버 담당으로 명시한 검사입니다.

```text
$ gh issue create ...
https://github.com/sangmokang/Valuehire_v6/issues/30
```

→ 무엇을 시켰나: 합격 조건 하나만 가진 이슈를 만들었습니다.
→ 무엇이 나왔나: 이슈 #30이 생성됐습니다.
→ 좋은 소식인가: 이번 작업공간은 조언형 판정 하나만 다루며 라벨 변경·보호 설정을 섞지 않습니다.

## 2. 근본 원인

1. 현재 자동 검사는 코드 시험의 성공·실패만 보여 주며, 어떤 기록과 파일 명부를 검토했는지 별도 판정으로 고정하지 않습니다.
2. 현재 라벨을 읽는 실행 경로가 없으므로 정본의 “라벨 없이는 합칠 수 없다”는 문장은 실제 시스템보다 강합니다.
3. 사람 표시를 판정 입력으로 쓰면 표시를 붙이거나 떼는 행위가 코드 위험도 자체를 바꾸는 권한이 됩니다.
4. 과거 판정을 현재 기록 지문과 묶지 않으면 새 커밋 뒤에도 예전 승인이 살아남을 수 있습니다.
5. 보호 설정이 꺼져 있어 참고용 검사와 실제 합치기 차단을 분리해서 보고해야 합니다.

## 3. 단일 인수 기준 AC-30

`pull_request`(= GitHub에서 변경을 합치기 전에 여는 검토 요청)의 `opened`, `synchronize`, `reopened`
(= 처음 열림, 새 커밋 추가, 다시 열림) 사건에서만 별도 `review-gate` 검사가 실행되어야 합니다.
판정기는 입력 base/head 기록이 실제 커밋인지 확인한 뒤 다음을 하나의 JSON(= 기계가 읽을 수 있는 구조화 문서)으로 출력해야 합니다.

- 형식 버전과 상태 `advisory`
- base/head 전체 지문
- base 이후 head까지의 커밋 수
- 전체 변경 파일 수와 정렬된 파일 명부
- 변경 종류, 위험도, 특수 위험 신호
- 위험 신호로부터 계산한 권장 검사 목록
- 위 필드를 정렬해 계산한 판정 지문

기계 합격 조건은 다음과 같습니다.

- 합성 저장소의 문서 전용 변경은 낮은 위험으로 분류됩니다.
- 일반 코드 변경은 중간 위험 이상으로 분류됩니다.
- 검사·계약·보안·데이터·외부 의존 경계는 높은 위험 이상과 각 특수 신호를 냅니다.
- 검사 약화 문구 또는 검사 파일 삭제는 가장 높은 위험으로 분류됩니다.
- 같은 입력은 같은 판정 지문을 내고, head에 새 커밋이 생기면 지문이 달라집니다.
- 잘못된 기록, 같은 base/head, 변경 파일 0개는 성공하지 않습니다.
- 판정기와 workflow(= 서버가 자동 검사를 실행하는 설정)는 라벨 API를 읽거나 쓰지 않습니다.
- workflow는 `pull_request_target`을 쓰지 않고 `contents: read`만 가집니다.
- `bash scripts/acceptance-review-gate.sh`는 계약한 사례 수와 실제 실행 수가 일치하고 성적 0을 냅니다.
- 새 인수 검사는 기존 `verify.yml`에도 무조건 실행 단계로 연결됩니다.

## 4. Harness 게이트 진행

- Gate 0 시작 자격: `RED: 0/20`, 기준·원격 기록 일치, 성적 0으로 통과했습니다.
- Gate 1 스펙: GitHub 이슈 #30과 이 문서의 AC-30 하나로 고정했습니다.
- Gate 2 격리: `worktrees/review-gate-advisory`, `task/review-gate-advisory`를 만들었습니다.
- Gate 3 RED: 이 문서를 먼저 커밋한 뒤 실제 판정기가 없어 실패하는 인수 검사를 별도 커밋으로 고정합니다.
- Gate 3 GREEN: RED 기대를 바꾸지 않고 판정기·workflow·정본 연결만 최소 수정합니다.
- Gate 4 검증: 대상 인수 검사, 변조, 문법, `session-status`, `verify`, pre-push 원명령을 순서대로 실행합니다.
- Gate 4.5 적대 검증: Claude가 1차 공격하고 Codex가 판정 근거를 전부 재현·반박합니다.
- Gate 5 배송: 작업 브랜치 업로드와 한국어 PR, 같은 최종 기록의 서버 검사까지만 수행합니다.
- Gate 6 종료: 병합·브랜치 삭제·보호 설정 변경은 오너 승인 전 실행하지 않습니다.

## 5. 적대 검증 항목

1. 파일 명부가 일부만 집계되거나 이름에 공백·탭이 있으면 수치가 틀리는가.
2. base/head 입력이 없거나 가짜여도 0건 합격하는가.
3. 새 커밋 뒤 과거 판정 지문이 그대로 남는가.
4. 검사 파일 변경을 문서 변경으로 오분류하는가.
5. 삭제된 검사 파일이나 약화 문구를 높은 위험보다 낮게 분류하는가.
6. 라벨이 위험도·상태를 바꾸거나 workflow가 라벨을 쓰는가.
7. 외부 변경 요청에서 큰 권한을 가진 사건으로 코드를 실행하는가.
8. 참고용 판정을 실제 병합 차단처럼 과장하는가.
9. 새 인수 검사가 로컬에만 있고 서버의 기존 자동 검사에서는 실행되지 않는가.
10. 현재 head가 아닌 checkout 상태를 읽어 수치가 갈리는가.

## 6. SOT 체크리스트

- [x] `docs/sot/INDEX.md` — 사건 기록은 이 문서에, 다음 세션이 참조할 실행 계약만 SOT에 둡니다.
- [x] `docs/sot/coding-principles.md` — P2 실행 가능한 합격 조건, P3 조용한 실패 금지, P13 검사 약화, P15 서버 연결, P20 0건 금지를 적용합니다.
- [x] `docs/sot/git-workflow.md` — 작업 하나·작업공간 하나·브랜치 하나·인수 기준 하나를 지킵니다.
- [x] `docs/sot/hook-contracts.md` — 새 인수 스크립트가 pre-push 이름 규칙으로 자동 실행되는 계약을 확인했습니다.
- [x] `docs/sot/verification-commands.md` — make/npm 대신 이 저장소의 실제 명령과 서버 고정 목록 갱신 규칙을 사용합니다.
- [x] `docs/sot/mechanism-registry.yaml` — 새 서버 판정 실행 줄을 명부에 등록하고 실제 workflow 문구와 대조되게 합니다.

## 7. 비범위

- GitHub 라벨 생성·수정·삭제와 라벨을 판정 입력으로 읽는 기능
- `main` 보호, 필수 검사 설정, 관리자 우회 차단
- 오너 승인 저장과 G1·G3~G6 전체 검토 루프 자동화
- Claude/Codex 외부 모델 호출 자동화
- 후보자·포지션·고객사 데이터와 제품 실행 경로
- 새 외부 패키지나 GitHub Action 추가
- merge, auto-merge, 배포, main 직접 push

## 8. 적대 검증 로그

구현과 원검증이 끝난 뒤 `claude -p` 전체 명령·판정 원문과 Codex 재현 명령·일치 표를 이 절에 그대로 추가합니다.

## 9. RED → GREEN 실행 로그

### 9-1. RED — 판정기·서버 배선이 없어서 실패

```text
$ bash scripts/acceptance-review-gate.sh
FAIL: 판정기 없음 — scripts/review_gate.py
FAIL: 문서 변경 판정 불일치 (exit=2)
FAIL: 같은 입력의 판정 지문이 달라짐
FAIL: 새 커밋이 과거 판정을 무효화하지 못함
FAIL: 일반 코드 변경 위험도 불일치
FAIL: 검사·계약 변경 신호 불일치
FAIL: 보안 경계 신호 불일치
FAIL: 데이터 경계 신호 불일치
FAIL: 외부 의존 경계 신호 불일치
FAIL: 검사 약화 문구를 가장 높은 위험으로 올리지 못함
FAIL: 검사 파일 삭제를 가장 높은 위험으로 올리지 못함
PASS: 없는 base 기록 → NOT_RUN (exit=2)
PASS: 없는 head 기록 → NOT_RUN (exit=2)
PASS: base와 head가 같아 변경 0건 → NOT_RUN (exit=2)
FAIL: workflow 사건·권한·동시성 계약 위반
FAIL: workflow 실제 판정기 배선 없음
FAIL: 라벨/API 쓰기 경로가 있거나 파일이 없음
FAIL: 기존 verify workflow 인수 검사 배선 불일치 (실행 줄 0회)
FAIL: 실제 작업 브랜치 명부 불일치 (exit=2, git=1, manifest=)
PASS: 검사 전후 저장소 상태 동일
CHECKED: 20
RED_RC=1
```

→ 무엇을 시켰나: 실제 판정기나 서버 설정을 만들기 전에 합격 조건 20개를 먼저 실행했습니다.
→ 무엇이 나왔나: 잘못된 기록·0건·무오염 4개만 기존 셸 실패 특성으로 예정대로 통과했고, 구현이 필요한 16개는 실패했습니다.
→ 좋은 소식인가: 판정기·권한 제한·서버 연결이 실제로 없으면 전체 성적 1이므로, 이후 구현이 무엇을 증명해야 하는지 빨간불로 고정됐습니다.

### 9-2. GREEN — 판정기·권한·서버 배선 20개 통과

```text
$ bash scripts/acceptance-review-gate.sh
PASS: 판정기 실존 — scripts/review_gate.py
PASS: 공백 경로를 포함한 문서 변경 1개 → 낮은 위험과 현재 head 명부
PASS: 같은 입력 → 같은 판정 지문
PASS: 새 커밋 → 과거 판정과 다른 head·판정 지문
PASS: 일반 코드 변경 → 중간 위험
PASS: 검사·계약 변경 → 높은 위험과 weakens_check
PASS: 보안 경계 변경 → 높은 위험과 touches_security
PASS: 데이터 경계 변경 → 높은 위험과 touches_data
PASS: 외부 의존 경계 변경 → 높은 위험과 touches_external
PASS: 검사 약화 문구 → 가장 높은 위험
PASS: 검사 파일 삭제 → 가장 높은 위험
PASS: 없는 base 기록 → NOT_RUN (exit=2)
PASS: 없는 head 기록 → NOT_RUN (exit=2)
PASS: base와 head가 같아 변경 0건 → NOT_RUN (exit=2)
PASS: workflow는 세 사건·읽기 권한·현재 요청 단위 동시성만 사용
PASS: workflow가 현재 base/head로 실제 판정기를 실행하고 화면 요약을 남김
PASS: 판정기와 workflow에 라벨/API 쓰기 권한 없음
PASS: 기존 verify workflow에 인수 검사 무조건 1회 배선
PASS: 실제 작업 브랜치의 현재 head·파일 수와 판정 명부 일치
PASS: 검사 전후 저장소 상태 동일
CHECKED: 20
GREEN_RC=0
```

→ 무엇을 시켰나: RED 시험을 바꾸지 않고 판정기·별도 workflow·기존 서버 검사 연결을 추가한 뒤 같은 20개를 다시 실행했습니다.
→ 무엇이 나왔나: 정상 분류·변조·잘못된 입력·권한·배선·무오염 20개가 모두 예정대로 통과했고 성적은 0이었습니다.
→ 좋은 소식인가: 로컬 합성 경로와 실제 작업 브랜치 호출 경로는 현재 합격입니다. 실제 GitHub 서버 실행은 push 뒤 별도로 확인해야 합니다.

### 9-3. 필수 장치 명부 검사 실패와 복구

최초 실패 실행은 시작·종료 시각을 별도 줄로 기록하지 못했습니다. 이 기록 누락을 숨기지 않으며,
도구가 보고한 경과 시간과 전체 출력, 실패 커밋, 복구 뒤 원명령 재실행을 아래에 보존합니다.

```text
$ bash scripts/verify/check-mechanism-registry.sh docs/sot/mechanism-registry.yaml
PASS: secrets-scan-precommit (pre-commit · 규칙 1·2·3)
PASS: acceptance-glob-prepush (pre-push · 규칙 1·2·3)
PASS: ci-secret-scan (ci · 규칙 1·2·4)
FAIL: ci-review-gate-advisory — ci_mirror_job 'review-gate' 이(가) .github/workflows/verify.yml 의 jobs: 키에 없다
CHECKED: 4
RC=1
```

→ 무엇을 시켰나: 새 `review-gate.yml` 실행 줄을 장치 명부에 등록하고 실제 파일·작업 이름과 맞는지 검사했습니다.
→ 무엇이 나왔나: 기존 검사기가 모든 서버 항목의 작업 이름을 `verify.yml` 한 파일에서만 찾아 성적 1을 냈습니다.
→ 나쁜 소식인가: 필수 검사가 실패했으므로 완료할 수 없었습니다. 명부를 거짓으로 바꾸지 않고 검사기 복구로 전환했습니다.

검사기 수정 전 커밋 `bdb0ce0`에 두 번째 workflow 자기 대조 사례를 RED로 고정했습니다.

```text
$ bash scripts/acceptance-verify-ac-m.sh
PASS: 검사기 실존·실행가능 — scripts/verify/check-mechanism-registry.sh
PASS: fixture 정상 명부 → 통과 (exit=0)
PASS: fixture path 없는 항목 → 불합격 (exit=1)
PASS: fixture 죽은 target → 불합격 (exit=1)
PASS: id 중복 → 불합격 (exit=1)
PASS: 알 수 없는 stage → 불합격 (exit=1)
PASS: manual 인데 사유 없음 → 불합격 (exit=1)
PASS: manual 정상(사유+실행권한) → 통과 (exit=0)
PASS: manual 인데 실행권한 없음 → 불합격 (exit=1)
PASS: ci 인데 거짓 target → 불합격 (exit=1)
FAIL: ci 항목은 자기 path workflow의 job·target을 대조 → 통과 (기대 exit=0, 실제 1)
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
PASS: 명부 항목 3개 = 검사기 보고 3개 (하한 3)
PASS: 저장소 무오염 (시작/종료 상태 동일)
CHECKED: 26
AC_M_RED_RC=1
```

→ 무엇을 시켰나: 기존 25개 경계에 “각 서버 항목이 자기 설정 파일의 작업 이름을 읽는가” 한 사례를 더했습니다.
→ 무엇이 나왔나: 새 사례 하나만 기대와 달랐고 전체 성적 1이었습니다. 기존 경계는 모두 유지됐습니다.
→ 좋은 소식인가: 검사기 결함을 다른 실패에 묻지 않고 한 사례로 고정했습니다.

검사기가 각 명부 항목의 `path`에서 작업 이름과 실행 줄을 함께 읽도록 최소 수정한 뒤 원명령을 다시 실행했습니다.

```text
$ bash scripts/acceptance-verify-ac-m.sh
PASS: 검사기 실존·실행가능 — scripts/verify/check-mechanism-registry.sh
PASS: fixture 정상 명부 → 통과 (exit=0)
PASS: fixture path 없는 항목 → 불합격 (exit=1)
PASS: fixture 죽은 target → 불합격 (exit=1)
PASS: id 중복 → 불합격 (exit=1)
PASS: 알 수 없는 stage → 불합격 (exit=1)
PASS: manual 인데 사유 없음 → 불합격 (exit=1)
PASS: manual 정상(사유+실행권한) → 통과 (exit=0)
PASS: manual 인데 실행권한 없음 → 불합격 (exit=1)
PASS: ci 인데 거짓 target → 불합격 (exit=1)
PASS: ci 항목은 자기 path workflow의 job·target을 대조 → 통과 (exit=0)
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
PASS: 명부 항목 4개 = 검사기 보고 4개 (하한 3)
PASS: 저장소 무오염 (시작/종료 상태 동일)
CHECKED: 26
FINAL_RC=0
```

→ 무엇을 시켰나: 실패했던 원명령을 검사기 수정 뒤 그대로 다시 실행했습니다.
→ 무엇이 나왔나: 기존 25개와 새 자기-workflow 사례까지 26개 모두 통과했고 성적은 0이었습니다.
→ 좋은 소식인가: 필수 게이트의 임시 실패는 PASS로 승격됐고, 장치 명부도 실제 별도 workflow를 정직하게 가리킵니다.
