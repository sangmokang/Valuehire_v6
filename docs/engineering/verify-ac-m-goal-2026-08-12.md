# AC-M — 검사 장치 명부(mechanism registry) 신설 goal (2026-08-12)

## 결론 (⑪ 사장님 브리핑)

이 작업은 **"이 저장소에 어떤 자동 검사가 어디서 도는지"를 한 장의 명부로 만들고, 그 명부가 거짓말을 못 하게 하는 검사기**를 새로 만드는 것입니다.

지금은 검사 장치(커밋 직전 문지기, 서버 자동 검사 등)가 여러 파일에 흩어져 있어서, 문서에는 "이 검사가 돈다"고 적혀 있는데 실제로는 아무도 안 부르는 죽은 검사가 생겨도 알아챌 방법이 없습니다. 이 명부와 검사기가 생기면 — 명부에 적힌 검사가 실제 파일에 존재하는지, 그 파일 안에 정말 그 명령이 있는지를 기계가 매번 대조합니다. 명부가 실제와 어긋나는 순간 검사가 불합격을 냅니다.

**판단이 틀리면 깨지는 것**: 이 명부 자체가 또 하나의 "문서와 실제의 불일치"가 될 수 있습니다(PR #6 결함 D6과 같은 유형). 그래서 명부를 사람이 읽는 문서가 아니라 **기계가 매번 대조하는 데이터**로 만들고, 대조 검사 자체를 서버 자동 검사에도 등록합니다.

**결정하실 것**: 없습니다 — 정본 goal 문서(verify-unification-goal-2026-08-10.md, 커밋 32ce698에서 확정)가 이미 스펙을 고정했고, 이 문서는 그 첫 인수 기준(AC-M)의 실행 계획입니다. PR을 올려두면 머지 여부만 판단하시면 됩니다.

---

## ① 현재 상태 (파일:줄 증거)

- 정본 스펙: `docs/engineering/verify-unification-goal-2026-08-10.md:78-81` (AC-M 절) — 레지스트리 스키마는 같은 문서 196~207행.
- `docs/sot/mechanism-registry.yaml` — **없음** (신설 대상).
- `scripts/verify/` 디렉토리 — **없음** (2026-08-12 `ls` 실측: "No such file or directory").
- 실제 검사 장치(명부에 등록할 대상, 전부 `grep -n` 실측):
  - `hooks/pre-commit:73` — `SECRET_PATTERNS_FILE= VERIFY_SCAN_SOURCE=index bash verify.sh` (커밋 직전 비밀 스캔)
  - `hooks/pre-push:112` — `-name 'verify.sh' -o -name 'acceptance-*.sh'` (push 직전 인수 검사 전량 자동 수집 줄)
  - `.github/workflows/verify.yml:15` — `jobs:` 아래 유일한 job 키는 `verify` (CI 미러 job 이름)
- `scripts/memory-recall-check.sh` — **없음** (AC-20의 산출물, 아직 미착수). 따라서 실제 명부에 `stage: manual` 항목은 **넣지 않는다** — manual 처리 로직은 fixture로만 검증한다.

## ② 근본 원인

검사 장치가 훅 2개·CI 워크플로 1개·SOT 문서에 흩어져 있고, 이들을 잇는 기계 대조가 없다. "문서에 적힌 검사 ≠ 실제 도는 검사" 불일치(P15③ 위반 유형)는 이 저장소에서 반복 실측됐다 — PR #4·#5가 CI 등록을 빠뜨렸고 V1도 못 잡았으며(인수인계 문서 2-7절), PR #6 결함 D6이 같은 유형이다. 이후 AC-1(규칙별 mechanism_id)·AC-3(원장 checked_by)·AC-5(3상태 집계)가 전부 이 명부를 참조하므로, 명부가 먼저 있어야 한다.

## ③ 인수 기준 (EARS + 검증 명령 + counter-AC)

**AC-M**: When AC-1의 규칙이 `mechanism_id`를 선언하거나 AC-3 원장 항목이 `checked_by`를 선언하면, then 그 값은 `docs/sot/mechanism-registry.yaml`의 `id`와 정확히 문자열 일치해야 한다. 이번 PR의 범위는 그 전제가 되는 **명부 파일 + 대조 검사기 + 인수 검사**다.

검증 명령: `bash scripts/acceptance-verify-ac-m.sh` (exit 0 = 전부 통과, 마지막 줄 `CHECKED: 15`)

검사기(`scripts/verify/check-mechanism-registry.sh`)가 하는 일 5가지 (정본 80행 그대로):
1. YAML 파싱 후 `id` 유일성 — 중복이면 exit 1
2. 각 항목 `path` 실존(`[ -f ]`) — 없으면 exit 1
3. `stage`가 `pre-commit|pre-push`면 `grep -qF -- "$target" "$path"` — 없으면 exit 1 (죽은 target)
4. `stage: ci`면 `ci_mirror_job`이 `.github/workflows/verify.yml`의 `jobs:` 키와 일치 — 아니면 exit 1
5. `stage: manual`이면 `path`가 실행권한(`-x`) 있는 파일인지만 확인

추가 fail-closed 규칙 (이 저장소 반복 함정의 회수 — P12):
- 항목 0개면 exit 2 (0건 통과 금지 — P20, PR #6 결함 D3의 교훈)
- 알 수 없는 `stage` 값·필수 필드 누락·`manual`인데 `manual_reason` 없음 — 전부 exit 1 (조용한 skip 금지)

counter-AC (이런 모습이면 가짜 합격):
- 명부에 없는 임의 문자열 ID가 통과하면 가짜
- 아무도 안 부르는 죽은 `target`이 통과하면 가짜
- `stage: manual`을 아무 항목에나 붙여 호출 검사를 회피하면 가짜 (`manual_reason` 필수 + 이번 명부에는 manual 항목 자체가 없음)
- 검사 항목이 줄어도 초록이면 가짜 (CHECKED 정확값 강제 — `checked -ne 15`이면 exit 1)
- 인수 검사가 저장소에 파일을 남기거나 상태를 바꾸면 판정 무효

## ④ Harness 게이트 진행 계획

0. `session-status.sh` — RED 1/6이나, 그 1은 `acceptance-0-2`(전역 상태 결합, suppressions.yaml 만료 8/21 유예)로 이 작업과 무관 (2026-08-12 04:2x 실측)
1. 이 문서 (스펙 = 정본 78~81행)
2. RED: fixture 3종 + `acceptance-verify-ac-m.sh` 커밋 → 검사기·명부가 없어서 빨감 (올바른 이유)
3. GREEN: `check-mechanism-registry.sh` + `mechanism-registry.yaml` 최소 구현
3.5 배선 증명: pre-push 글로브(`hooks/pre-push:112`)가 `acceptance-verify-ac-m.sh`를 자동 수집함을 실행 로그로 증명 + CI 스텝 추가
4. `bash verify.sh` + 인수 검사 전량 + 뮤테이션(구현 한 줄씩 파괴 → 해당 항목만 빨간지)
5. CI 등록(verify.yml) + SOT 등록(verification-commands.md) → push → PR (머지는 사장님)

## ⑤ codex 적대검증 정조준 항목

1. YAML 파서가 bash 3.2에서 실제로 도는가 (`${VAR^^}` 계열 함정)
2. fixture 3종이 서로 다른 실패 경로를 실제로 짚는가 (하나의 원인으로 셋 다 빨간 것 아닌가)
3. 검사기 뮤테이션: 규칙 1~5 중 하나를 지웠을 때 해당 fixture/항목만 빨개지는가
4. CHECKED 정확값이 진짜 강제되는가 (검사 삭제 시 빨간가 — D3 재발 방지)
5. 인수 검사가 저장소를 오염시키지 않는가 (임시 폴더에서만 쓰기)
6. 명부의 `target` 문자열이 실제 훅 줄과 문자 그대로 일치하는가 (지어낸 함수명 아닌가)

## ⑥ SOT 체크리스트

- 읽음: `docs/engineering/verify-unification-goal-2026-08-10.md` (정본, 78~81·196~207행), `docs/sot/verification-commands.md`, `docs/sot/coding-principles.md`
- 수정 필요: `docs/sot/verification-commands.md` — CI 목록에 `bash scripts/acceptance-verify-ac-m.sh` 추가 (같은 PR에 포함, P15③)
- 신설: `docs/sot/mechanism-registry.yaml` (이 자체가 새 SOT)

## ⑦ 비범위

- AC-1(always-apply-rules.yaml)·AC-3(지시 원장)·AC-5(집계기)·AC-20(memory-recall-check.sh) — 별도 AC, 별도 워크트리
- `stage: manual` 실항목 등록 (AC-20 완료 시점에 등록)
- verify.sh 본문 변경 없음 (기존 검사 약화 금지 — P13)

## ⑧ 롤백 절차 (L3)

명부·검사기·인수 검사·CI 스텝·SOT 줄은 전부 **신규 추가**라 삭제 = 롤백이다:
`git revert <머지커밋>` 한 번으로 원상복구되며, 기존 검사는 어느 것도 이 작업에 의존하지 않는다.

## ⑨ 영향 반경 (L3)

- 이 검사가 깨지면: pre-push와 CI가 빨개져 push/머지 판단이 지연된다. 기존 검사 동작에는 영향 없음(신규 파일만 추가).
- 오탐 위험: 훅 파일의 해당 줄을 리팩터링하면 `target` 불일치로 빨개진다 — **의도된 동작**이다(명부를 함께 갱신하라는 신호). PII·인증·과금 경로는 건드리지 않는다.

## ⑩ 계약 스펙 (Spec-Driven)

`scripts/verify/check-mechanism-registry.sh`:
- 입력: `$1` = 명부 경로 (기본 `docs/sot/mechanism-registry.yaml`), 환경변수 `WORKFLOW_FILE` = CI 워크플로 경로 (기본 `.github/workflows/verify.yml`, fixture 시험용)
- 출력(stdout): 항목·규칙마다 `PASS:`/`FAIL:` 줄, 마지막 줄 `CHECKED: <항목 수>`
- exit: 0 = 전부 통과 / 1 = 하나라도 위반 / 2 = NOT_RUN(명부 없음·빈 명부·항목 0개)
- 명부 YAML 계약(파서가 받아들이는 유일한 형태 — 이 밖은 exit 1):
  ```yaml
  - id: "문자열(유일)"
    path: "저장소 루트 기준 상대경로"
    target: "path 파일 안에 문자 그대로 존재하는 명령 문자열"
    stage: "pre-commit|pre-push|ci|manual"
    required: true|false
    ci_mirror_job: "jobs: 키"     # stage: ci 일 때만 필수
    manual_reason: "사유"          # stage: manual 일 때만 필수
  ```
  → 명부 한 항목의 생김새입니다. 검사기는 이 모양 밖의 줄을 만나면 통과시키지 않고 불합격을 냅니다(모르는 형식을 조용히 넘기지 않는 안전한 기본값).
- 경계값: 값의 앞뒤 따옴표("·')는 벗겨서 비교, 빈 문자열 값 = 필드 누락으로 취급(exit 1)

fixture 3종 (`scripts/verify/fixtures/mechanism-registry/`):
- `normal.yaml` — 실존 path·실존 target(pre-commit)·유효 ci 항목 → exit 0
- `missing-path.yaml` — 존재하지 않는 path → exit 1
- `dead-target.yaml` — path는 실존하나 그 파일에 없는 target 문자열 → exit 1

## 회수 (규칙 C)

- `grep -rliE "mechanism|registry|checked_by|AC-M" ~/.claude/.../memory/` → `project_verify_unification_status.md`, `MEMORY.md` (2026-08-12 실행). 요지: goal v6 확정(32ce698), AC 1개=워크트리 1개, AC-M부터 착수, AC-M 검증 스펙은 codex 최종점검에서 보강됨. 본문까지 읽고 반영함.
- `git log --oneline --all -- scripts/verify docs/sot/mechanism-registry.yaml` → 0건 (과거 착수 이력 없음).
- 같은 유형 함정 회수: PR #6 D3(하한 없음)→CHECKED 정확값 강제 / D4(오염 사각지대)→쓰기는 mktemp에서만 / bash 3.2 함정→tr 사용, `${VAR^^}` 금지.

## 적대 검증 로그

(V1·V2 판정을 이 절에 append 한다)

### 게이트 2~4 검증 증거 (2026-08-12 04:2x~04:3x, 구현 세션)

RED (커밋 6d90ded → 보강 cc12b96):
```
acceptance_rc=1 / FAIL 14건 / CHECKED: 15
FAIL: 검사기 없음/실행불가 — scripts/verify/check-mechanism-registry.sh (기대 동작이 아직 없다)
FAIL: fixture 정상 명부 → 통과 (기대 exit=0, 실제 127)
```
→ 뭘 시켰나: 검사기·명부를 만들기 전에 인수 검사를 먼저 실행했습니다.
→ 뭐가 나왔나: 15건 중 14건이 "검사기가 없다"(127 = 셸이 파일을 못 찾음)로 실패했습니다.
→ 의미: 좋은 소식 — 문법 오류가 아니라 기대 동작 부재로 빨간, 올바른 RED입니다.

GREEN (검사기+명부 커밋 후):
```
PASS 15건 / FAIL 0건 / CHECKED: 15 / acceptance_rc=0
검사기 단독(실제 명부): PASS 3건 / CHECKED: 3 / rc=0
```
→ 뭘 시켰나: 검사기와 명부 3항목을 구현한 뒤 같은 인수 검사를 재실행했습니다.
→ 뭐가 나왔나: 15건 전부 통과, 실제 명부 3항목도 전부 통과했습니다.
→ 의미: RED→GREEN 전환이 계약값(CHECKED 15) 그대로 이뤄졌습니다.

뮤테이션 점검 (격리 클론에서 구현을 한 줄씩 파괴):
```
M1 rule2_path_check_removed   rc=1 fail=1  ← fixture 격리(ci 전환) 후. 격리 전엔 rc=0 생존
M2 rule3_dead_target_removed  rc=1 fail=1 (죽은 target fixture 만 빨감)
M3 rule1_dup_check_removed    rc=1 fail=1 (id 중복 항목만 빨감)
M4 rule4_ci_job_removed       rc=1 fail=2 (ci 포함 fixture·실제 명부 빨감)
M5 registry_fake_target       rc=1 fail=1 (실제 명부 항목만 빨감)
M6 acceptance_one_check_deleted rc=1 fail=1 (CHECKED 14≠15 — D3 방어 작동)
```
→ 뭘 시켰나: 검사기 규칙 4개·명부 target·인수 검사 항목 수를 각각 일부러 깨봤습니다.
→ 뭐가 나왔나: 6종 전부 빨간불. 단 M1은 처음에 살아남아 fixture 를 ci 로 격리해 잡았습니다(커밋 메시지에 기록).
→ 의미: 검사가 장식이 아니라 실제로 각 규칙의 삭제를 감지합니다. M1 생존은 "실패 경로 중복이 삭제를 가린다"는 PR #6 D5 와 같은 유형을 제 fixture 에서 잡아 고친 것입니다.

배선 증명 (R4 · 런타임):
```
$ bash hooks/pre-push origin https://example.invalid </dev/null
  ok  ./scripts/acceptance-verify-ac-m.sh
pre-push: 검사 5개 실행
pre-push_rc=0
```
→ 뭘 시켰나: 코드 올리기 직전 문지기(pre-push)를 실제로 통째로 돌렸습니다.
→ 뭐가 나왔나: 글로브(이름 규칙 자동 수집)가 새 인수 검사를 스스로 찾아 실행했고 전체 합격했습니다.
→ 의미: 새 검사는 고아가 아닙니다 — 로컬 문지기(자동 수집)와 CI(명시 등록) 양쪽에 배선됐습니다.
