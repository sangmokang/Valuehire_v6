# 코덱스 전달 문서 — 검사 판정 권한 복구 (2026-08-25)

## 결론

넘길 일은 세 덩어리이고, 순서가 중요합니다.

**첫 덩어리를 안 고치면 나머지를 고쳐도 고쳤다는 걸 증명할 수 없습니다.** 지금 이 저장소는 검사 스크립트를 통째로 비우고 "합격했습니다"라는 문장 한 줄만 출력하게 만들면 그대로 통과시킵니다. 개인정보 유출을 막는 검사를 맨 앞에서 그냥 끝내버려도 그걸 잡으라고 만든 상위 검사 셋이 전부 초록불을 냅니다. 검사의 합격·불합격을 정하는 권한이 코드가 아니라 **출력 문자열**에 있기 때문입니다.

그래서 첫 덩어리(판정 권한 복구)만 먼저 코덱스에 넘겼습니다. 둘째·셋째는 첫째가 통과한 뒤에 넘깁니다. 셋을 한꺼번에 넘기면 검사 체계를 고치는 작업이 그 고장난 검사 체계로 검증되는 자기모순이 생깁니다.

작업 공간은 격리해 뒀습니다. 코덱스는 새로 판 별도 폴더에서만 손대고, 원격 전송·병합은 하지 않습니다.

---

## 넘기기 전에 실측한 환경 (추측 아님)

| 항목 | 실측 결과 |
|---|---|
| `npm run wt` (정본이 요구하는 워크트리 러너) | **없음** — `package.json` 자체가 없음 |
| `docs/sot/30-strict-mode-contract.md` | **없음** |
| `docs/sot/31-strict-recurrence-ledger.md` (재발 원장) | **없음** |
| 실재하는 SOT | `coding-principles.md`, `principles.yaml`, `mechanism-registry.yaml`, `hook-contracts.md`, `git-workflow.md`, `verification-commands.md`, `INDEX.md`, `humansearch-*` 2건 |
| `main` 브랜치 위치 | `c59bad7` (= `origin/main`) |
| `rescue/main-mixed-20260825T200952` | `3094eef` — main보다 1커밋 앞, 아직 main에 없음 |
| `strict/notion-bunjang-golden` | `a46c395` — 3094eef 위 1커밋, push 없음 |
| 코덱스 전달 경로 | `codex-companion.mjs task [--background] [--write]` — 사용 가능 |

→ 이 표는 "정본이 시키는 대로 할 수 있는가"를 먼저 확인한 것입니다. 워크트리 러너와 SOT 문서 두 개가 실제로 없어서, 정본이 지정한 명령 대신 `git worktree add`를 썼고 재발 원장 인용은 생략했습니다. 없는 것을 있는 것처럼 쓰지 않기 위해 그대로 적습니다.

**정정**: 앞선 보고에서 기준 브랜치를 `main (3094eef)`이라고 적었는데 틀렸습니다. `3094eef`는 아직 main에 없는 rescue 브랜치 커밋이고, main은 `c59bad7`입니다. 코덱스에는 `c59bad7`을 기준으로 지시했습니다.

## 격리 작업 공간

```
경로:   worktrees/gate-integrity-20260825
브랜치: task/gate-integrity-20260825
기준:   c59bad7 (main)
상태:   clean
```

→ 원본 작업 폴더와 문제 브랜치를 건드리지 않도록 별도 폴더를 새로 팠습니다. 코덱스가 실패하거나 엉뚱하게 고쳐도 폴더째 버리면 끝입니다.

---

## 프롬프트 1 — 판정 권한을 출력 문자열에서 걷어낸다 (전달 완료)

```text
$strict

작업 폴더: /Users/kangsangmo/Desktop/Valuehire_v6/worktrees/gate-integrity-20260825
브랜치: task/gate-integrity-20260825 (기준 c59bad7). 이 폴더 밖의 파일은 읽기만 하고 쓰지 마라.
위험등급 L3 — 개인정보 유출 방어선과 전체 인수 검사의 판정 권한을 다룬다.

## 해결할 문제 (둘 다 재현 완료)

문제 A. scripts/verify/run-acceptance.sh:47 이 `grep -c 'PASS'` 로 출력에 PASS 가 든 줄이
1개 이상이면 합격 처리한다. 즉 판정 권한이 출력 문자열에 있다.

  $ printf '#!/usr/bin/env bash\nexit 0\n' > exit-zero.sh
  $ bash scripts/verify/run-acceptance.sh exit-zero.sh          → EXIT=1 (막힘)
  $ printf '#!/usr/bin/env bash\necho "PASS: 검사했습니다"\nexit 0\n' > forged.sh
  $ bash scripts/verify/run-acceptance.sh forged.sh             → EXIT=0 (통과됨)

  .github/workflows/verify.yml 이 15개 넘는 인수 검사를 이 래퍼로 돌린다.
  CHECKED: 관례 분기(run-acceptance.sh:55-60)는 출력에 CHECKED: 문자열이 있을 때만
  동작하므로, CHECKED 를 아예 내놓지 않는 위조 검사기는 그 분기를 지나치지 못하고 통과한다.

문제 B. scripts/scan-data-exposure.sh 맨 앞줄에 위조 합격 문구와 exit 0 을 심으면
그 무력화를 잡아야 할 상위 방어선이 전부 통과한다. 격리 복제본 실측:

  [대조군]  데이터노출검사 EXIT=0 · 의미변조검사 EXIT=0 · 원칙검사 EXIT=0
  [무력화 후]
    PASS: 추적 파일 197개 검사, 위반 0건        무력화된 검사 EXIT=0
    scripts/acceptance-semantic-mutations.sh    EXIT=0
    scripts/acceptance-principles-check.sh      VERDICT: PASS
                                                MECHANISMS: PASS 34/34
                                                WIRING: PASS pre-push=1 ci=1
    hooks/pre-commit                            EXIT=0

  원인 후보: verify.yml:198 이 scan-data-exposure.sh 를 run-acceptance 래퍼 없이
  직접 실행한다. .check-weakening-patterns 에 조기 `exit 0` 과 위조 `PASS:` 가 없다.
  acceptance-semantic-mutations.sh 의 반례 목록에 "출력만 하고 아무 검사도 안 함"이 없다.

## 착수 전 필수

1. docs/sot/coding-principles.md, docs/sot/principles.yaml, docs/sot/mechanism-registry.yaml,
   docs/sot/hook-contracts.md, docs/sot/verification-commands.md 를 읽고 goal 문서에 경로를 적어라.
   docs/sot/30-strict-mode-contract.md 와 31-strict-recurrence-ledger.md 는 이 저장소에 없다.
   없는 문서를 읽었다고 쓰지 마라.
2. docs/engineering/gate-integrity-goal-2026-08-25.md 를 먼저 작성하라.
   상위 목표 1문장 · 현재 상태(file:line) · 근본 원인 · AC · 입력 영역 표 · 예외 표 ·
   롤백 절차 · 영향 반경 · 배포 후 관측 항목 · 비범위 · "## 적대 검증 로그"(후기록).
3. 대조군을 먼저 기록하라 — 손대지 않은 상태에서 위 5개 명령의 종료값을 그대로 남긴다.
   대조군 없이 "고쳤다"고 말하지 마라.

## 인수 기준 (AC — 각각 검증 명령 1개)

AC-1. When 인수 검사 본문을 (a) exit 0 (b) true (c) 빈 파일 (d) no-op (e) 일반 echo
      (f) `echo "PASS: ..."` 여섯 방식 중 어느 것으로 바꿔도, run-acceptance.sh 는
      비정상 종료해야 한다.
      검증: 여섯 사본 각각 실행 → 여섯 개 모두 종료값 0 이 아님.
      counter-AC: PASS 줄 개수만 세어 통과시킨다 / 파일 크기만 본다.

AC-2. When 정상 인수 검사를 돌리면 지금처럼 통과해야 한다.
      검증: verify.yml 이 부르는 인수 검사 전부를 실제로 실행 → 종료값 0.
      (차단만 증명하고 통과를 증명하지 않으면 불합격이다. 반드시 쌍으로 남겨라.)

AC-3. While 검사기가 검사 ID · 실제 검사 건수 · 입력 지문을 담은 구조화된 증거를
      내놓지 않으면, 단순 PASS 문자열은 판정 권한을 가져서는 안 된다.
      검증: 증거 없는 출력으로 통과 시도 → 차단됨.
      counter-AC: CHECKED: 를 안 쓰는 검사기는 예외로 빠져나간다.

AC-4. When verify.yml 이 직접 실행하는 검사(scan-data-exposure.sh 포함)를 AC-1 의
      여섯 방식으로 무력화하면, 독립된 검사가 실패해야 한다.
      검증: 무력화 후 semantic-mutations · principles-check · pre-commit 실행
            → 최소 하나가 비정상 종료. 대조군에서는 전부 종료값 0.
      counter-AC: pre-commit 의 문자열 패턴만 늘려서 막은 척한다 /
                  검사기와 변조 시험을 함께 약화한다.

## 절차

- 워크트리는 이미 만들어져 있다. 새로 만들지 마라.
- RED 먼저: 위 반례를 재현하는 시험을 먼저 커밋해 실패시켜라. 실패 이유가 문법 오류가
  아니라 기대 동작 결여여야 한다. 그 다음 최소 변경으로 통과시켜라.
- 반례 fixture 는 격리 임시 폴더에 만들어라. 원본 워크트리를 오염시키지 마라.
- 새 의존성 추가 금지. package.json 을 만들지 마라(이 저장소에는 없다).
- 테스트·검사를 지우거나 단언을 빼서 초록불을 만드는 것은 위반이다.
- mechanism-registry.yaml 과 hook-contracts.md 가 이번 변경으로 사실과 달라지면
  같은 커밋에 함께 고쳐라.

## 하지 말 것

- git push, PR 생성, 병합 — 전부 금지. 사용자가 직접 한다.
- 이 워크트리 밖 파일 수정 금지.
- 라이브 Notion / Supabase 호출 금지.
- 실제로 돌리지 않은 검증을 돌렸다고 쓰지 마라.

## 보고 형식

1) 한 줄 결론  2) 대조군 종료값 원문  3) AC별 판정과 재현 명령·출력 원문
4) 차단/통과 쌍 증거  5) 확인 못 한 것  6) 병합 전 판정
```

→ 뭘 시켰나: 검사의 합격·불합격을 정하는 권한을 출력 문자열에서 걷어내고, 직접 실행되는 검사도 무력화 시험 대상에 넣으라고 지시했습니다.
→ 왜 이게 먼저인가: 이걸 안 고치면 나머지 수정이 "검증됐다"는 말 자체가 성립하지 않습니다.
→ 무엇을 막아 뒀나: 차단만 증명하고 통과를 증명하지 않는 것, 패턴 목록만 늘려 막은 척하는 것, 검사기와 시험을 같이 약화하는 것을 counter-AC로 미리 금지했습니다.

---

## 프롬프트 2 — 저장물의 자기선언 제거 (프롬프트 1 통과 후 전달)

```text
$strict

작업 폴더는 프롬프트 1 이 통과한 뒤 새로 판 워크트리를 쓴다.
대상: tools/notion-golden/ (브랜치 strict/notion-bunjang-golden, a46c395 의 내용)
위험등급 L3 — 고객사 운영자료의 증거 계약.

## 해결할 문제 (전부 재현 완료)

F1. cli.mjs:86-91 — inspect 를 --supabase-env 없이 부르면 Supabase 비교를 건너뛴다.
    cli.mjs:131 의 `legacyComparison?.verdict !== "FAIL"` 이 undefined 에서 참이 되어
    최종 PASS 를 낸다. 실제 골든 파일 안에는 SUPABASE_RAW_ROW_BLOCKS_MISSING(severity high)
    이 저장돼 있는데도 읽지 않는다. 실측: verdict PASS, 종료값 0.

F2. lib.mjs:265 insertFindings 가 audit.findings 만 넣는다. 외부 비교의 high finding 은
    audit.externalComparisons.legacySupabase.findings 에 있어 테이블에 안 들어간다.
    실제 파일에서 SELECT COUNT(*) FROM audit_findings = 0.

F4. cli.mjs:145 readbackMatch 가 audit.captureHash 와 captures.capture_hash 컬럼을
    비교하는데 후자는 전자를 그대로 써넣은 값이다. 원본 JSON 에서 다시 계산하지 않는다.
    변조 실측: captures.raw_json 에서 blocks 를 통째로 비워도 8개 시험 전부 통과.
    별도 확인: captureHash="forged" 를 넣어도 저장·재조회 일치로 PASS.

## AC

AC-1. When SQLite 에 캡처를 쓰면 시스템은 원본 캡처에서 해시를 직접 계산하고,
      호출자가 준 해시가 다르면 거부해야 한다.
AC-2. When SQLite 를 읽으면 raw_json 에서 해시를 다시 계산해 저장 해시와 대조하고,
      다르면 FAIL 이어야 한다. 각 테이블 건수도 raw_json 안 배열 길이와 대조한다.
AC-3. When inspect 를 실행하면 저장된 audit 판정을 그대로 신뢰하지 말고 현재 코드로
      캡처를 재감사해야 한다. 저장된 high finding 은 종료값과 판정 문구에 나타나야 한다.
AC-4. While 필수 Supabase 비교가 실행되지 않았으면 전체 PASS 와 종료값 0 을 금지한다.
AC-5. 모든 출처(자체 감사 + 외부 비교)의 finding 이 source 컬럼과 함께
      audit_findings 에 적재돼야 한다.
AC-6. 현재 실제 SQLite 파일의 독립 해시 일치(893d7a...5116 / 44f0b2...dc91c)는 유지돼야 한다.

counter-AC: 저장 해시끼리만 비교 / audit JSON 의 PASS 를 그대로 출력 /
NOT_TESTED 를 FAIL 아닌 상태로 두면서 전체 PASS / 64자리처럼 보이는 문자열만 검증.

위조 해시, raw_json 변조, audit JSON 위조, 비교 미실행을 각각 RED fixture 로 추가하라.
기존 파일 덮어쓰기 금지와 0600 권한 시험은 유지하라.
push / PR / 병합 금지. 라이브 Notion·Supabase 호출 금지.
```

→ 이 덩어리는 "저장된 불합격이 다시 열면 합격으로 바뀌는" 문제를 닫습니다. 프롬프트 1이 끝나기 전에는 넘기지 않습니다.

---

## 프롬프트 3 — 라이브 증명·레이아웃 판정·배선·커밋 분리 (프롬프트 2 통과 후 전달)

```text
$strict

대상: tools/notion-golden/lib.mjs 의 원본 비교와 레이아웃 판정, 그리고 시험 배선.
위험등급 L3.

## 해결할 문제

F3. lib.mjs:57-58 — raw_page 가 있고 blocks 가 배열이기만 하면 빈 배열도 레이아웃
    보존으로 센다. tests/notion-golden-sample.test.mjs:234-260 이 blocks: [] 로
    layoutVerdict PASS 를 단언해 이 느슨한 규칙을 고정하고 있다.
    판정을 올바르게 강화하면 그 시험이 깨진다(실측 pass 7 / fail 1).

F3b. lib.mjs:9,13,25 — source.kind="notion-api" 와 상태 200 요청 한 건만 있으면
    원본 비교 완료로 보고 SOURCE_COMPARISON_NOT_RUN 을 제거한다. 원본 없는 루트
    페이지도 통과한다. 즉 자기가 만든 장부만으로 라이브 검증을 주장할 수 있다.

F5. notion-api.mjs 의 recordError → capture.errors → CAPTURE_ERRORS_PRESENT 사슬이
    시험으로 한 번도 실행되지 않는다. recordError 를 무음 처리해도, 재시도 소진 후
    throw 를 빈 값 반환으로 바꿔도 8개 시험 전부 통과했다.

F6. cli.mjs:24-25 — expectedDatabases / expectedRows 기본값이 undefined 이고
    lib.mjs:472 checkExpectedCount 는 undefined 면 즉시 통과한다. 인자를 빼면
    건수 검증이 통째로 사라진다.

F7. 저장소 전체에서 `node --test` 호출부가 0건이다. 새 시험 15건이 서버 자동검사에도
    커밋 전 훅에도 연결돼 있지 않다.

F8. a46c395 커밋에 tools/strict/finding-runner.mjs 외 6파일이 무언급으로 섞여 있고,
    task/wu4a-finding-runner-20260825T200952 브랜치에 바이트 동일하게 존재한다
    (sha256 2b770269a041b1e1… 일치). 둘 다 병합하면 충돌한다.

## AC

AC-1. 루트·하위 페이지·DB 행 중 raw page 가 하나라도 없으면 감사는 FAIL.
AC-2. 요청 장부는 캡처 결과와 대상별로 연결된 완료 증거여야 한다. 임의 자기선언 금지.
AC-3. 빈 blocks 배열만으로 수집 완료를 판정하지 않는다. 저장된 블록 수가 라이브 블록
      수와 일치할 때만 보존으로 센다. 개수 불일치는 별도 코드로 구분해 남긴다.
AC-4. 실제로 블록이 0개인 정상 페이지는 성공한 children 조회와 완료 표식이 있을 때만 PASS.
AC-5. 수집 실패 시나리오(500/404, 재시도 소진)에서 errors 가 기록되고 감사가 FAIL 이어야 한다.
AC-6. 건수 기대값을 선언하지 않으면 PASS 를 금지한다.
AC-7. node --test 를 서버 자동검사와 커밋 전 훅에 연결하고, 시험 하나를 일부러 깨뜨린
      상태에서 게이트가 비정상 종료하는 출력을 배선 증명으로 남긴다.
      continue-on-error, || true 금지.
AC-8. 노션 브랜치에서 finding-runner 6파일을 제거한다.
      `git diff --name-only <base>...HEAD` 에 finding-runner 0건.

기존 시험 :234-260 은 기대값을 FAIL 로 정정한다. 시험을 지우거나 단언을 빼는 것은 위반이다.
기존 18페이지·1,780블록 산출물은 읽기 전용 회귀 fixture 로 유지 확인하라.
push / PR / 병합 금지.
```

→ 이 덩어리는 "빈 것을 채워진 것으로 세는" 문제와 "시험이 아무 데도 연결 안 된" 문제를 닫습니다.

---

## 전달 상태

| 프롬프트 | 상태 | 근거 |
|---|---|---|
| 1 — 판정 권한 복구 | **전달 완료 · 실행 중** | 작업 `task-mt8nk58y-7l1dxj` · 실행 확인 17초 경과 · 작업 상태 폴더가 `gate-integrity-20260825` 로 잡힘 |
| 2 — 저장물 자기선언 제거 | 대기 | 1이 통과해야 검증이 성립 |
| 3 — 라이브 증명·배선·커밋 분리 | 대기 | 2가 통과해야 대상 코드가 안정 |

→ 이 표는 셋 중 무엇을 실제로 넘겼는지 구분한 것입니다. 1번만 돌고 있고 2·3번은 넘기지 않았습니다. 대기 중인 것을 넘겼다고 말하지 않기 위해 분리했습니다.

### 결정 카드 — 셋을 한꺼번에 넘기지 않은 이유

- **무엇을**: 세 프롬프트 중 1번만 코덱스에 전달하고 2·3번은 보류했습니다.
- **왜**: 2·3번이 고치는 코드의 합격 여부를 판정하는 것이 바로 1번이 고치는 검사 체계입니다. 순서를 바꾸면 고장난 저울로 저울을 고친 결과를 재게 됩니다.
- **버린 대안**: 셋을 병렬로 넘겨 시간을 줄이는 방법. 실제로 코덱스는 프롬프트 4개를 스스로 제안했고 병렬 실행이 가능합니다.
- **대가**: 전체 완료가 늦어집니다. 1번이 실패하면 2·3번은 시작조차 못 합니다.
- **되돌리는 법**: 1번 결과를 보고 판단해, 검사 체계가 이미 믿을 만하다고 확인되면 2·3번을 동시에 넘기면 됩니다. 워크트리가 분리돼 있어 서로 간섭하지 않습니다.

전달 명령(재현용):

```
node .../codex-companion.mjs task --background --write --fresh --effort high "<프롬프트 1 전문>"
→ Codex Task started in the background as task-mt8nk58y-7l1dxj

node .../codex-companion.mjs status task-mt8nk58y-7l1dxj
→ running | Phase: starting | Elapsed: 17s
  Log: .../state/gate-integrity-20260825-566a8010964a8597/jobs/task-mt8nk58y-7l1dxj.log
```

→ 뭘 시켰나: 프롬프트 1 전문을 코덱스에 새 세션(`--fresh`)으로, 격리 워크트리에 쓰기 권한을 주어 넘겼습니다.
→ 뭐가 나왔나: 작업 번호가 발급됐고 실제로 돌고 있음을 상태 조회로 확인했습니다. 작업 로그 경로가 그 워크트리 이름으로 잡혔습니다.
→ 좋은 소식인가: 좋은 소식입니다. 지난번처럼 "시작했습니다"만 찍히고 실제로는 안 도는 상태가 아니라는 뜻입니다.

→ 이 표는 셋 중 무엇을 실제로 넘겼는지 구분하는 것입니다. 대기 항목을 넘겼다고 말하지 않기 위해 분리했습니다. 사장님이 다른 창에서 직접 넘기실 경우 위 코드 블록 안의 내용만 그대로 복사하시면 됩니다 — 블록 밖 설명은 코덱스에 전달하지 않아도 됩니다.

## 남은 위험

- 코덱스에 **쓰기 권한**을 줍니다. 격리 워크트리로 범위를 좁혔지만, 코덱스가 그 경계를 스스로 지킨다는 보장은 코드가 아니라 지시문뿐입니다. 실행 후 다른 워크트리들의 상태를 직접 확인해야 합니다.
- 지난번 코덱스 실행은 중계 계층이 결과를 전달하지 않고 "시작했습니다"만 반복했습니다. 이번에도 같으면 작업 로그에서 직접 회수해야 합니다.
- 이 저장소에는 재발 원장이 없어, 이번에 찾은 반례를 영구 자산으로 남기는 R9 절차를 문서 기준으로만 지킬 수 있습니다. 원장 신설 자체가 별도 작업으로 남습니다.
