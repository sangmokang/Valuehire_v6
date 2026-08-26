# /strict 프롬프트 — 노션 골든 샘플 판정 경로 경화 (2026-08-25)

## 결론

번개장터 노션 자료를 다시 읽어 저장하는 일 자체는 잘 됐습니다. 숫자도 해시도 문서와 전부 맞습니다. 문제는 **그 저장물을 다시 열어 "합격이냐"를 정하는 부분**입니다. 파일 안에는 "불합격"이 적혀 있는데, 아무 옵션 없이 다시 열어보면 화면에는 "합격"이 뜨고 종료값도 정상으로 나옵니다.

그리고 이 도구를 지키는 방어 코드를 한 줄씩 일부러 망가뜨려 봤더니, 여섯 번 중 네 번은 망가뜨려도 테스트가 전부 초록불이었습니다. 지금 상태에서 초록불은 코드가 옳다는 증거가 되지 못합니다.

마지막으로, 이 커밋에는 노션과 무관한 다른 작업 파일 6개가 말없이 같이 실려 있고, 그 파일들은 다른 브랜치에도 똑같이 들어 있어 둘 다 합치면 부딪힙니다.

그런데 코덱스에 같은 대상을 39분간 적대적으로 검증시킨 결과, **이 저장소 전체에 걸친 더 심각한 문제 두 가지**가 나왔습니다. 제가 직접 재현해 사실로 확인했습니다.

첫째, 검사 스크립트 본문을 통째로 비우고 "합격했습니다"라는 문장 한 줄만 출력하게 만들면, 아무것도 검사하지 않고 합격 처리됩니다. 서버 자동검사가 열다섯 개 넘는 검사를 이 방식으로 돌리고 있습니다.

둘째, 개인정보와 대용량 파일 유출을 막는 검사를 맨 앞줄에서 그냥 끝내버려도, 그 무력화를 잡아야 할 상위 방어선 세 개가 전부 초록불을 냅니다. 원칙 34개 전항 합격까지 그대로 뜹니다.

**병합 전 판정: REQUEST_CHANGES.** 노션 작업보다 이 두 가지가 먼저입니다.

커버 트랙: A(계약 대조), B(반례 지목), C(변조 8종 실행 — 6종 자체 + 코덱스 발견 2종 재현) · 미커버: D(라이브 재수집)→승인 필요

---

## 붙여넣을 프롬프트 본문

> 아래 본문을 그대로 새 세션에 붙여넣어 /strict 로 실행한다.
> 근거: strict/notion-bunjang-golden HEAD a46c395 에 대한 codeaudit(A·B 트랙) + humanreview 기계 리뷰. 변조 생존 4건 실측.

/strict

번개장터 노션 골든 샘플 도구(`tools/notion-golden/`)의 **판정 경로**를 경화한다. 수집·저장·해시 증거는 이미 닫혀 있다. 문제는 그 증거를 읽어 합격/불합격을 정하는 부분이 스스로를 검증하지 않는다는 것이다.

기준 브랜치: `main` (`3094eef`)
문제 브랜치: `strict/notion-bunjang-golden` (`a46c395`, push·PR 없음)
등급: **L3** — 고객사 운영자료 · 외부 Notion/Supabase 경계 · 저장된 불합격이 합격으로 뒤집히는 오판 경로.

### 상위 목표

번개장터 고객사 정보 16행이 검색·추론에서 조용히 빠지는 것을 막는 것이 이 도구의 존재 이유다. 성공 신호: **저장된 골든 샘플을 아무 인자 없이 다시 조회했을 때, 그 안에 기록된 심각도 high 결함이 종료값과 판정 문구에 그대로 나타난다.**

### 착수 전 필수

1. `docs/sot/30-strict-mode-contract.md`, `docs/sot/31-strict-recurrence-ledger.md`를 읽고 관련 행을 goal에 인용한다 (R4).
2. `docs/engineering/notion-bunjang-golden-sample-goal-2026-08-25.md`의 AC-1~AC-6을 읽는다. 아래 결함은 전부 그 AC가 **막겠다고 선언한 것을 못 막는** 사례다.
3. 워크트리는 `npm run wt -- notion-golden-hardening`으로만 만든다. 문제 브랜치를 그대로 쓰지 말고 `main`에서 새로 판다 — 아래 WU-8이 그 커밋을 분해하기 때문이다.

### 결함 목록 — 전부 실측 재현됨

> **F0-A·F0-B는 노션 작업의 결함이 아니라 저장소 전체 검증 체계의 결함이다.** 이 둘을 먼저 닫지 않으면 아래 F1~F8을 고쳐도 그 수정이 검증됐다고 말할 수 없다. 별도 워크트리에서 먼저 처리한다.

#### F0-A (치명적) 합격 문구 한 줄로 모든 인수 검사를 위조할 수 있다

`scripts/verify/run-acceptance.sh:46`은 종료값 0이면서 출력에 `PASS:` 또는 `VERDICT: PASS` 줄이 하나라도 있으면 합격 처리한다. 즉 **판정 권한이 출력 문자열에 있다.** 검사 본문을 통째로 비우고 문장만 찍으면 통과한다.

```
$ printf '#!/usr/bin/env bash\nexit 0\n' > exit-zero.sh
$ bash scripts/verify/run-acceptance.sh exit-zero.sh
FAIL(run-acceptance): … 종료값 0 이지만 판정을 한 건도 내놓지 않았다.       EXIT=1

$ printf '#!/usr/bin/env bash\necho "PASS: 검사했습니다"\nexit 0\n' > forged-pass.sh
$ bash scripts/verify/run-acceptance.sh forged-pass.sh
PASS: 검사했습니다
OK(run-acceptance): … — 판정 1건                                          EXIT=0
```

→ 뭘 시켰나: 아무 검사도 하지 않는 빈 스크립트 두 개를 만들어, 하나는 그냥 끝내고 하나는 "합격했습니다"라는 문장만 찍게 한 뒤 인수 검사 껍데기에 통과시켜 봤습니다.
→ 뭐가 나왔나: 그냥 끝낸 쪽은 막혔지만, 문장만 찍은 쪽은 통과했습니다.
→ 좋은 소식인가: 나쁜 소식입니다. `.github/workflows/verify.yml`이 열다섯 개 넘는 검사를 이 껍데기로 돌리고 있어, 서버 자동검사 전체가 같은 방식으로 뚫립니다.

**요구**: 판정 권한을 출력 문자열에서 걷어낸다. 검사기는 **검사 ID · 실제 검사 건수 · 입력 지문**을 담은 구조화된 증거를 내야 하고, 껍데기는 그 증거의 건수가 0이면 통과시키지 않는다. `PASS:` 줄 개수만 세는 방식으로 고치는 것은 금지(counter-AC).

#### F0-B (치명적) 개인정보 유출 검사를 꺼도 상위 방어선 셋이 전부 초록불이다

`scripts/scan-data-exposure.sh` 맨 앞줄에 위조 합격 문구와 조기 종료를 심으면, 그 무력화를 잡아야 할 검사들이 전부 통과한다. 격리 복제본에서 재현:

```
[대조군 · 손대지 않음]  데이터노출검사 EXIT=0 · 의미변조검사 EXIT=0 · 원칙검사 EXIT=0

[검사기 무력화 후]
PASS: 추적 파일 197개 검사, 위반 0건       무력화된 검사 EXIT=0
의미변조검사 EXIT=0
VERDICT: PASS
MECHANISMS: PASS 34/34 strict-contract-bindings
WIRING: PASS pre-push=1 ci=1
pre-commit  EXIT=0
```

→ 뭘 시켰나: 저장소를 따로 복제해 개인정보·대용량 파일 유출 검사를 맨 앞에서 그냥 끝나게 만든 뒤, 그걸 잡으라고 만들어 둔 상위 검사 세 개와 커밋 직전 훅을 돌렸습니다.
→ 뭐가 나왔나: 네 개 전부 정상 통과였고, "원칙 34개 전항 합격"까지 그대로 떴습니다.
→ 좋은 소식인가: 나쁜 소식입니다. 고객사 자료가 실수로 커밋되는 것을 막는 마지막 방어선이 조용히 꺼져도 아무도 알 수 없다는 뜻입니다.

**요구**: `verify.yml:198`처럼 보호 래퍼 없이 직접 실행되는 검사도 무력화 시험 대상에 넣는다. `.check-weakening-patterns`에 조기 `exit 0`과 위조 `PASS:`를 금지 패턴으로 추가한다. 그리고 **차단과 통과를 한 쌍으로** 증명한다 — 무력화하면 실패하고 정상이면 통과하는 두 출력을 모두 남긴다.

#### F1 (치명적) 저장된 FAIL이 재조회에서 PASS로 뒤집힌다

`tools/notion-golden/cli.mjs:86-91`이 `--supabase-env` 없이 `inspect`를 부르면 Supabase 비교를 아예 건너뛰고, `cli.mjs:131`의 `legacyComparison?.verdict !== "FAIL"`이 `undefined !== "FAIL"` → 참이 되어 최종 PASS를 낸다. SQLite `captures.audit_json` 안에는 이미 `SUPABASE_RAW_ROW_BLOCKS_MISSING`(severity high)이 저장되어 있는데도 읽지 않는다.

```
$ node tools/notion-golden/cli.mjs inspect --sqlite data/notion-golden/bunjang-golden-v1-final-20260825.sqlite3
"verdict": "PASS", "supabaseGoldenVerdict": "NOT_TESTED"   exit=0

$ sqlite3 …bunjang-golden-v1-final-20260825.sqlite3 "SELECT json_extract(audit_json,'\$.externalComparisons.legacySupabase.verdict') FROM captures WHERE id=1"
FAIL
```

→ 뭘 시켰나: 저장된 골든 파일을 옵션 없이 다시 열어보고, 이어서 그 파일 안에 실제로 뭐라 적혀 있는지 직접 꺼내봤습니다.
→ 뭐가 나왔나: 화면은 "합격 · 미검사", 파일 속 기록은 "불합격"이었습니다.
→ 좋은 소식인가: 나쁜 소식입니다. 나중에 누가 이 골든 샘플을 확인하면 초록불만 보게 됩니다.

**요구**: `inspect`는 `record.audit.externalComparisons`에 저장된 판정과 finding을 최종 판정에 반드시 반영한다. 저장된 비교 결과가 있으면 그것을 쓰고, 없으면 `NOT_TESTED`가 아니라 **`SOURCE_COMPARISON_NOT_RUN`과 동급으로 PASS를 금지**한다. `--supabase-env`를 새로 주면 재비교하되, 재비교 결과가 저장본보다 관대해질 때는 두 판정을 모두 출력하고 나쁜 쪽을 채택한다.

#### F2 (높음) `audit_findings` 테이블이 항상 비어 있다

`lib.mjs:265`의 `insertFindings(database, audit.findings)`는 SQLite 자체 감사 finding만 넣는다. Supabase 비교의 high finding은 `audit.externalComparisons.legacySupabase.findings`에 있어 테이블에 들어가지 않는다. 실제 골든 파일에서 `SELECT COUNT(*) FROM audit_findings` = **0**. goal AC-4의 검증 명령이 "audit_findings readback을 대조한다"인데, 대조 대상이 빈 테이블이다.

**요구**: 모든 출처(자체 감사 + 외부 비교)의 finding을 `source` 컬럼과 함께 `audit_findings`에 적재한다. finding이 0건인데 어딘가의 JSON 블롭에는 high가 있는 상태를 **스키마 수준에서 불가능**하게 만든다.

#### F3 (높음) 빈 blocks 배열이 "레이아웃 보존"으로 통과하고, 테스트가 그 약한 규칙을 고정하고 있다

`lib.mjs:57-58`의 레이아웃 판정은 `(rawPage || raw_page || raw_json) && Array.isArray(row.blocks)`뿐이다. `blocks: []`(빈 배열)이면 재귀 블록이 하나도 없는데 보존으로 센다. 이것이 AC-2가 막겠다고 선언한 "가짜 골든 샘플" 그 자체다.

그리고 `tests/notion-golden-sample.test.mjs:234-260`이 `blocks: []` fixture로 `layoutVerdict === "PASS"`를 **단언**한다. 판정을 올바르게 강화하면 이 테스트가 깨진다:

```
### 레이아웃 판정을 강화 — 빈 blocks 배열은 보존으로 안 친다
# pass 7
# fail 1
```

→ 뭘 시켰나: 판정을 올바른 방향(빈 목록은 보존으로 안 침)으로 고친 뒤 테스트를 돌렸습니다.
→ 뭐가 나왔나: 테스트 하나가 깨졌습니다.
→ 좋은 소식인가: 나쁜 소식입니다. 고치면 깨진다는 건 테스트가 지금의 느슨한 규칙을 정답으로 못박아 뒀다는 뜻입니다.

**요구**: 저장된 행의 블록 수가 라이브 행의 블록 수와 일치할 때만 레이아웃 보존으로 판정한다. 개수 불일치는 `SUPABASE_RAW_ROW_BLOCKS_MISSING`이 아니라 별도 코드(`SUPABASE_RAW_ROW_BLOCKS_INCOMPLETE`)로 구분해 남긴다. 위 테스트는 **기대값을 FAIL로 정정**한다 — 테스트를 지우거나 단언을 빼는 방식은 금지(테스트 약화 = 위반).

#### F4 (높음) 해시 재조회가 동어반복이다

`readbackMatch`(`cli.mjs:145`)는 `audit.captureHash`와 `captures.capture_hash` 컬럼을 비교하는데, 후자는 전자를 그대로 써넣은 값이다. 저장된 `raw_json`을 다시 정규화해 해시를 계산하지 않으므로, 증거 블롭이 통째로 훼손돼도 검사를 통과한다. 실측:

```
### captures.raw_json 에서 blocks 를 통째로 비운다
# pass 8   # fail 0     ← 8개 테스트 전부 통과
```

→ 뭘 시켰나: 저장물의 핵심 증거 덩어리에서 블록 전체를 지운 뒤 테스트를 돌렸습니다.
→ 뭐가 나왔나: 8개 전부 통과했습니다.
→ 좋은 소식인가: 나쁜 소식입니다. 증거가 통째로 비어도 "해시 일치"가 뜨므로, 그 검사는 아무것도 지키지 못합니다.

**요구**: 재조회는 `captures.raw_json`을 파싱해 `canonicalHash()`를 다시 계산하고 저장된 `capture_hash`와 대조한다. 추가로 `pages`/`blocks`/`databases`/`database_rows` 각 테이블 건수가 `raw_json` 안의 배열 길이와 일치하는지 검사한다.

#### F5 (중간) 수집 실패 기록 경로가 무테스트다 — 부분 수집이 만점으로 보고될 수 있다

이 도구가 "부분 수집을 합격시키지 않는" 근거는 `notion-api.mjs`의 `recordError` → `capture.errors` → `CAPTURE_ERRORS_PRESENT`(high) 사슬 하나뿐인데, 그 사슬이 테스트로 한 번도 실행되지 않는다. 두 변조 모두 8/8 통과:

```
### recordError 를 무음 처리 — 수집 실패가 장부에 안 남는다      # pass 8  # fail 0
### 재시도 소진 후 throw 를 삼킨다 (실패를 성공처럼)              # pass 8  # fail 0
```

→ 뭘 시켰나: 수집이 실패해도 기록하지 않게, 그리고 실패 응답을 빈 값으로 삼키게 각각 바꾼 뒤 테스트를 돌렸습니다.
→ 뭐가 나왔나: 둘 다 8개 전부 통과했습니다.
→ 좋은 소식인가: 나쁜 소식입니다. "부분만 수집됐는데 만점으로 보고되는" 사고를 막는 장치가 한 번도 시험된 적이 없다는 뜻입니다.

**요구**: 목 fetch가 특정 경로에서 500/404를 내는 시나리오를 추가해 ① `capture.errors.length > 0` ② `audit.verdict === "FAIL"` ③ `CAPTURE_ERRORS_PRESENT` 존재를 단언한다. 재시도 소진 경로도 별도 케이스로 만든다.

#### F6 (중간) 건수 기대값이 기본으로 꺼져 있다

`cli.mjs:24-25`에서 `expectedDatabases`/`expectedRows` 기본값이 `undefined`이고, `lib.mjs:472`의 `checkExpectedCount`는 `undefined`면 즉시 통과한다. 즉 `--expect-databases`/`--expect-rows`를 빼고 부르면 AC-1이 요구한 건수 검증이 통째로 사라지고, 하드코딩된 `rootPages: 1`만 남는다.

**요구**: `capture` 명령에서 두 인자를 **필수**로 만들거나, 생략 시 `EXPECTED_COUNTS_NOT_DECLARED`(high)를 남겨 PASS를 금지한다. 어느 쪽을 택하든 goal의 결정 목록에 올려 오너 확정을 받는다(R1 ②).

#### F7 (높음) 새 테스트가 CI에도 pre-push에도 배선되지 않았다

저장소 전체에서 `node --test` 호출부가 **0건**이다(`.github/workflows/verify.yml`, `verify.sh`, `hooks/` 전수 확인). 새로 만든 테스트 2개(`notion-golden-sample.test.mjs` 8건, `finding-runner.test.mjs` 7건)는 사람이 손으로 돌려야만 도는 고아 상태다. 위 F1~F6을 다 고쳐도 배선이 없으면 다음 커밋에서 조용히 되돌아간다.

**요구**: `verify.yml`에 Node 테스트 단계를 추가하고, **배선 증명**을 남긴다 — 일부러 테스트 하나를 깨뜨린 상태에서 게이트가 비정상 종료하는 출력. `continue-on-error`, `|| true` 금지.

#### F8 (절차) 커밋 하나에 다른 작업이 무언급으로 섞였다

`a46c395`의 메시지는 노션 얘기만 하는데, `tools/strict/finding-runner.mjs` + 테스트 + fixture 3개 + goal 문서가 함께 실려 있다. 이 6개 파일은 `worktrees/wu4a-finding-runner-20260825T200952`(브랜치 `task/wu4a-finding-runner-20260825T200952`, RED→GREEN 2커밋)에 **바이트 동일**하게 존재한다:

```
notion 쪽 sha256: 2b770269a041b1e1…
wu4a  쪽 sha256: 2b770269a041b1e1…
공통 변경 파일 6개
```

→ 뭘 시켰나: 두 브랜치의 같은 이름 파일을 지문(해시)으로 대조하고, 겹치는 변경 파일을 세었습니다.
→ 뭐가 나왔나: 지문이 완전히 같고, 겹치는 파일이 6개였습니다.
→ 좋은 소식인가: 나쁜 소식입니다. 같은 작업이 두 브랜치에 복제돼 있어 둘 다 합치면 충돌합니다.

두 브랜치를 다 병합하면 같은 파일이 충돌한다. 한 워크트리 = 인수 기준 1개 규칙 위반.

**요구**: 노션 작업 브랜치에서 finding-runner 6파일을 제거하고, 그 작업은 `task/wu4a-…` 브랜치에만 남긴다.

### 작업 분해 (WU = AC 1개 = 검증 1개, 순차)

| WU | 내용 | 검증 명령 |
|---|---|---|
| **WU-0A** | **F0-A 판정 권한을 출력 문자열에서 걷어냄 (별도 워크트리·선행)** | 빈/위조 검사기 6종 전부 비정상 종료 + 정상 검사 통과 |
| **WU-0B** | **F0-B 직접 실행 검사도 무력화 시험 대상에 편입 (별도 워크트리·선행)** | 무력화 시 상위 검사 3종 비정상 종료 + 대조군 통과 |
| WU-1 | F3 레이아웃 판정 강화 + 기존 테스트 기대값 정정 | `node --test tests/notion-golden-sample.test.mjs` |
| WU-2 | F1 `inspect` 저장 판정 반영 | 동 위 + 실제 골든 파일 `inspect` exit 1 확인 |
| WU-3 | F2 `audit_findings` 전 출처 적재 | 동 위 + `SELECT COUNT(*) FROM audit_findings` ≥ 1 |
| WU-4 | F4 해시 재계산 대조 | 동 위 (F4 변조가 RED로 죽는지 확인) |
| WU-5 | F5 수집 실패 경로 회귀 | 동 위 (M4·M5 변조가 RED로 죽는지 확인) |
| WU-6 | F6 건수 기대값 필수화 (오너 확정 후) | 동 위 |
| WU-7 | F7 CI 배선 + 배선 증명 | `bash verify.sh` · 고의 파손 시 비정상 종료 출력 |
| WU-8 | F8 커밋 범위 분리 | `git diff --name-only main...HEAD`에 finding-runner 0건 |

→ 이 표는 작업을 8덩어리로 쪼갠 것입니다. 한 덩어리 = 합격 기준 1개 = 검증 명령 1개이고, 앞 덩어리가 닫히기 전에는 다음 덩어리를 시작하지 않습니다. WU-1~WU-5가 실제 결함 수정이고, WU-7은 그 수정이 되돌아가지 못하게 막는 배선, WU-8은 커밋 정리입니다.

WU-1~WU-5는 각각 **먼저 RED**(현재 코드에서 실패)를 커밋한 뒤 최소 구현으로 GREEN을 만든다. WU-4·WU-5의 RED는 위에 적은 변조가 아니라 **정상 코드에서 실패하는 테스트**여야 한다 — 변조는 커버리지 진단이지 회귀 자산이 아니다.

### 예외 표 (R1 ③ — 표에 없는 상황은 임의 판단 금지, 중단 후 표 갱신)

| 상황 | 처리 |
|---|---|
| 골든 SQLite 파일이 없다 | 명시적 중단 — 재수집은 이 작업 범위 밖(외부 호출) |
| Supabase 자격증명이 없다 | `inspect`는 저장 판정으로 진행, 재비교는 건너뛰되 그 사실을 판정에 남긴다 |
| 라이브 Notion 재수집이 필요해 보인다 | **중단 + 사장님 승인 요청** — 읽기 전용이어도 외부 호출은 이 작업 범위 밖 |
| 기존 테스트 기대값을 바꿔야 한다 | WU-1의 F3 정정만 허용. 그 외 기대값 완화·단언 제거·skip 추가는 전부 위반 |
| 그 외 전부 | 명시적 중단 + 표 갱신안 보고 |

→ 이 표는 작업 중 예상 밖 상황이 나왔을 때의 행동을 미리 못박은 것입니다. 표에 없는 상황에서 알아서 판단하는 것을 막는 게 목적이며, 특히 외부(노션·Supabase)에 다시 접속하는 일은 전부 중단 후 승인 대상입니다.

### 교차 검증 상태 (V1)

코덱스 `task-mt8ljbmp-xramu3`(세션 `01a038bb-a16e-7753-bd45-7bd721296f1e`, 39분 42초)이 같은 대상을 독립 적대 검증했고 판정은 동일하게 REQUEST_CHANGES였다. F1·F3·F4·F7은 양쪽이 독립적으로 같은 결론에 도달했다. F0-A·F0-B는 코덱스만 찾았고 이쪽에서 재현해 확인했다. 코덱스가 추가로 지목했으나 이 문서에 아직 반영하지 않은 항목:

- 위조된 요청 장부 1건 + 원본 없는 루트 페이지로 라이브 비교 PASS (`lib.mjs:9,13,25`)
- 정본 600줄과 실제 판정기 500줄 경계 불일치 (`coding-principles.md:26` vs `check-strict-principles-skills.sh:72`)
- goal 문서 165줄의 게이트 명령이 존재하지 않는 경로 → `MODULE_NOT_FOUND`

주의: 코덱스는 쓰기 권한(`--write`)으로 실행됐다. 실행 후 대상 워크트리는 `git status` 빈 줄, HEAD `a46c395` 그대로임을 확인했다.

### 이번 리뷰의 반례를 영구 자산으로 (R9)

M1·M2·M4·M5(변조 생존 4건)와 M3(테스트가 약한 규칙을 고정)는 같은 PR의 회귀 테스트로 편입한다. 편입 못 하는 항목은 `docs/sot/31-strict-recurrence-ledger.md`에 기한 있는 부채 행으로 남긴 뒤에만 READY TO MERGE를 선언한다.

### 하지 말 것

- 라이브 Notion·Supabase 재수집 (승인 없이 금지)
- Supabase 스키마 변경·쓰기 (원 goal의 비범위)
- 골든 SQLite를 git에 추가 (`.gitignore:36 /data/`가 막고 있음 — 유지)
- merge 실행 (`USER_MERGE_ONLY`)

---

## 이 프롬프트의 근거 실행 기록

| 검사 | 명령 | 결과 |
|---|---|---|
| **F0-A 합격 문구 위조** | `bash scripts/verify/run-acceptance.sh <빈 검사기>` | **EXIT=0 — 통과됨** |
| **F0-B 유출 검사 무력화** | 복제본에서 검사기 조기 종료 후 상위 검사 3종 | **전부 EXIT=0 — 통과됨** |
| 기준선 | `node --test tests/notion-golden-sample.test.mjs` | pass 8 / fail 0 |
| M1 `captures.raw_json`에서 blocks 제거 | 위와 같음 | **pass 8 / fail 0 — 생존** |
| M2 `insertFindings` 호출 제거 | 위와 같음 | **pass 8 / fail 0 — 생존** |
| M3 레이아웃 판정 강화(`blocks.length > 0`) | 위와 같음 | pass 7 / fail 1 — 테스트가 약한 규칙을 고정 중 |
| M4 `recordError` 무음화 | 위와 같음 | **pass 8 / fail 0 — 생존** |
| M5 재시도 소진 후 throw 삼킴 | 위와 같음 | **pass 8 / fail 0 — 생존** |
| M6 `SOURCE_COMPARISON_NOT_RUN` 방어 제거 | 위와 같음 | pass 7 / fail 1 — 방어 살아 있음 |
| 저장 판정 뒤집힘 | `node tools/notion-golden/cli.mjs inspect --sqlite …` | verdict PASS, exit 0 (저장본은 FAIL) |
| CI 배선 | `grep -rn 'node --test' --include=*.yml --include=*.sh .` | **0건** |
| 커밋 범위 | `comm -12` 두 브랜치 변경 파일 | 공통 6파일, 내용 바이트 동일 |

→ 뭘 시켰나: 정상 테스트를 먼저 돌린 뒤, 방어 코드를 한 줄씩 일부러 망가뜨려 테스트가 잡아내는지 봤습니다.
→ 뭐가 나왔나: 6번 중 4번은 망가뜨려도 전부 초록불이었습니다.
→ 좋은 소식인가: 나쁜 소식입니다. 초록불이 그 코드가 옳다는 증거가 되지 못한다는 뜻입니다. 반대로 M3·M6은 방어가 실제로 걸려 있음을 보여줍니다.

## 미확인으로 남긴 것

- 라이브 Notion·Supabase 재수집: 읽기 전용이어도 외부 호출이라 승인 없이 하지 않았습니다. 저장된 SQLite만 읽었습니다.
- 댓글 범위: 원 goal대로 HTTP 403 `restricted_resource`, `NOT_VERIFIED` 유지.
- 원격 CI 상태: 이 브랜치는 push 자체가 없어 판정 불가.
- `finding-runner` 자체의 품질: 별도 브랜치 `task/wu4a-…`의 리뷰 대상이며 여기서는 중복 사실만 확인했습니다.

## 적대 검증 로그

(후기록 — V1 `/codex:adversarial-review --fresh` 판정 본문과 V2 재검증 결과를 여기에 그대로 append)
