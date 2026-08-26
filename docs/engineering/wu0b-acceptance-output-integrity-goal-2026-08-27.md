# WU0-B — acceptance 출력 위조와 no-op 거짓 PASS 차단

## 결론

현재 canonical runner는 출력 문자열을 성공 권한으로 취급해 가짜 `PASS`, `CHECKED`, 정상 출력 재생을 승인한다. WU0-B는 runner가 실행 전에 승인된 repo 상대경로와 내용 지문을 독립 JSON 계약에 대조하게 만들어 script 단독 변조를 차단한다.

이 작업은 WU0-B만 다룬다. trigger·checkout·선행 step·workspace는 WU0-C, runner·validator·contract·workflow 동시 약화는 WU0-D, permissions·environment approval은 WU0-E다. 전체 안전성은 `CONDITIONAL`, 원격 상태는 `UNVERIFIED`, SHIP은 `NO`다.

## 판단 근거

- 위험등급은 L3다. runner, 구조화 정본, CI/pre-push wiring, acceptance를 함께 바꾸는 공유 안전장치다.
- 출력은 표시 자료일 뿐 진위의 독립 근거가 아니다. 승인된 content identity가 맞으면 target의 종료값을 보존하고, 다르면 실행 전에 거부한다.
- JSON registry 원문 SHA-256을 validator에 pin한다. registry의 정상 변경은 registry와 validator pin을 함께 갱신해야 하며, 그 동시 변경을 악의적으로 승인하는 공격은 WU0-D다.
- 새 dependency를 추가하지 않는다. 저장소의 Ruby 2.6.10 stdlib `json`, `digest`, `pathname`과 기존 duplicate-key scanner 패턴을 사용한다.

## 기준선과 격리

- session ID: `5441961A-F3E7-4539-B0A1-AAB86EDE277F`
- branch creation base: `d782079c3ede8effd09016b15ff48e2afbe5cf97`
- WU0-B implementation base after the required A2 evidence-only correction: `169fad3`
- branch: `task/wu0b-acceptance-output-integrity`
- worktree: `worktrees/wu0b-acceptance-output-integrity`
- 원본 작업공간 시작 HEAD: `3094eefa646b102074dfb6401777afe450223e6c`
- 원본 작업공간 시작 staged SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- 원본 작업공간 시작 status SHA-256: `8dc8bce42ac3a77fd3050e8a694b4d94abc01ae9fafe99483bf837f8b7876efb`
- 신규 worktree 시작 HEAD: `d782079c3ede8effd09016b15ff48e2afbe5cf97`
- 신규 worktree 시작 staged SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- 신규 worktree 시작 status SHA-256: `d42e30b6ca619e5b36dea169773c78de64bfbc13b022caf3ccc521cd59a4346b`
- 원본 main, WU0-A2 worktree와 다른 worktree를 수정하지 않는다.
- push, PR, merge, 원격 변경, SHIP·merge-ready 주장을 금지한다.

## 직접 로드 장부

### 코딩 원칙 정본

- 명령: `sed -n '1,9999p' docs/sot/coding-principles.md`
- UTC: `2026-08-26T16:26:03Z`
- HEAD: `d782079c3ede8effd09016b15ff48e2afbe5cf97`
- 종료값: `0`, 상태: `PASS`
- 확인한 hard 한도: 파일 600줄, 함수 100줄, 전체 diff 3,000줄.

### 기계 장부

- 명령: `sed -n '1,9999p' docs/sot/principles.yaml`
- UTC: `2026-08-26T16:26:04Z`
- HEAD: `d782079c3ede8effd09016b15ff48e2afbe5cf97`
- 종료값: `0`, 상태: `PASS`
- P1~P24, §1-B-1~5, V-1~5의 34개 항목을 직접 읽었다.

### 원칙 acceptance

- 명령: `bash scripts/acceptance-principles-check.sh`
- UTC: `2026-08-26T16:26:04Z` ~ `2026-08-26T16:26:05Z`
- HEAD: `d782079c3ede8effd09016b15ff48e2afbe5cf97`
- 종료값: `0`, 상태: `PASS`

```text
VERDICT: PASS
SOT_LOAD: PASS docs/sot/coding-principles.md
LEDGER_LOAD: PASS docs/sot/principles.yaml
MECHANISMS: PASS 34/34 strict-contract-bindings
WIRING: PASS pre-push=1 ci=1
CHECKED: 34
```

→ Strict 시작 자격과 원칙 배선 34건만 증명한다. WU0-B 합격 증거는 아니다.

## 현재 상태와 근본 원인

- `scripts/verify/run-acceptance.sh`는 target이 exit 0이면 통합 stdout/stderr에서 `PASS`를 grep하고 마지막 `CHECKED:` 뒤의 숫자만 남긴다.
- runner는 target의 repo 상대경로, 추적 상태, symlink/hardlink, content digest를 검사하지 않는다.
- 따라서 출력 위조자가 정상 출력 전체를 literal로 재생하면 target이 실제 검사를 한 것과 구분할 수 없다.
- 기존 `acceptance-semantic-mutations.sh`는 tracked acceptance 26개를 수집하지만 하한 5만 요구해 inventory 감소를 고정값과 대조하지 않는다.

근본 원인은 parser가 약해서가 아니라 성공 권한이 공격자가 쓸 수 있는 출력에 있다는 것이다.

## 보호 inventory와 호출 경로

### 구현 전 exact count

- 추적된 `scripts/acceptance-*.sh`: 26개.
- CI workflow의 canonical runner invocation: 25개.
- `ci-required-steps.json`: 보호 step 23개 안 canonical runner invocation 25개.
- pre-push 수집: `verify.sh` + acceptance 26개 = 27개.
- pre-push skip: `acceptance-0-2.sh`, `acceptance-0-5.sh`, PUSH-PERFORMING `acceptance-0-7.sh` = 3개.
- pre-push runner 실행: 24개.
- CI와 pre-push runner target 합집합: acceptance 25개 + `verify.sh` = 26개.
- runner 호출 경로가 없는 `acceptance-0-2.sh`는 WU0-B registry 비범위다.

WU0-B 전용 acceptance를 CI에 추가하면 승인된 runner target 합집합과 contract inventory는 27개가 되어야 한다. 감소, 빈 목록, 중복 path는 거부한다.

### R4 실제 배선

```text
.github/workflows/verify.yml
  -> scripts/verify/run-acceptance.sh <canonical target>
hooks/pre-push
  -> glob inventory
  -> scripts/verify/run-acceptance.sh <canonical target>
scripts/verify/run-acceptance.sh
  -> scripts/verify/check-acceptance-integrity.rb <canonical target>
  -> docs/sot/acceptance-integrity-contract.json
  -> integrity PASS 뒤에만 bash <canonical target> [args...]
```

→ CI와 pre-push가 같은 runner와 같은 identity contract를 사용한다. workflow provenance와 동시 contract 약화는 각각 WU0-C/D다.

## T 계약 — 입력·출력·오류·경계

### Runner CLI

```text
bash scripts/verify/run-acceptance.sh <repo-relative-target> [target-args...]
```

- target은 contract에 정확히 한 번 존재하는 canonical repo 상대경로여야 한다.
- 절대경로, `.`, `..`, cleanpath 불일치, basename-only, repo 밖 경로, untracked path, symlink, hardlink는 거부한다.
- 현재 pre-push `find .`가 만드는 `./scripts/...` 입력은 hook이 runner 호출 전에 `${c#./}`로 canonicalize한다. runner는 non-canonical 입력을 승인하지 않는다.
- target 인자는 integrity 판정 뒤 원 target에 바꾸지 않고 전달한다. 정상 acceptance의 mktemp fixture 인자를 제한하지 않는다.

### Integrity contract schema

```json
{
  "schema_version": 1,
  "algorithm": "sha256",
  "inventory": [
    {"path": "scripts/acceptance-example.sh", "sha256": "64 lowercase hex"}
  ]
}
```

- root와 entry는 폐쇄 schema다. unknown/missing field를 거부한다.
- duplicate JSON object key는 의미 Hash 생성 전 독립 scanner로 거부한다.
- inventory는 고정 contract digest와 일치해야 하며 0개·감소·중복 path를 거부한다.
- path는 정렬된 고유 canonical 문자열이어야 하고 실제 Git tracked regular file과 정확히 일치해야 한다.
- contract와 target 모두 `File.lstat(path).symlink? == false`, `File.stat(path).file? == true`, `File.stat(path).nlink == 1`, `git ls-files --error-unmatch -- path`를 만족해야 한다.
- contract 자체는 고정 repo 상대경로의 tracked regular non-symlink·non-hardlink 파일이어야 한다.

### 종료값과 출력

- integrity 정상 + target 정상 성공: target stdout/stderr 의미를 보존하고 exit `0`.
- integrity 정상 + target 정상 실패: target 실패를 성공으로 바꾸지 않고 원 exit 값을 보존한다.
- target content mismatch: 실행 전 `VERDICT: FAIL`, `CHECKED: 0`, exit `1`.
- contract/target/registry identity 또는 증거 missing·malformed·duplicate-key·symlink·hardlink·untracked·repo 밖·inventory 0/감소: `VERDICT: NOT_RUN`, `CHECKED: 0`, exit `2`.
- `PASS`, `CHECKED`, `VERDICT` 출력 문자열은 target 성공 권한이 아니다.
- runner의 stderr/ANSI/CR/marker 순서/숫자 파싱은 성공 판정에 사용하지 않는다.

### 경계

- 정상 target arguments와 target 내부 mktemp fixture 실행은 허용한다.
- target의 승인된 bytes가 같더라도 untracked copy, symlink, hardlink, basename-only path는 거부한다.
- registry 갱신은 script 변경과 함께 digest를 다시 만들고 validator pin을 갱신하는 명시 절차다.
- runner·validator·contract·workflow를 함께 약화하는 공격은 WU0-D라서 WU0-B PASS로 숨기지 않는다.

## EARS 인수 기준

1. WHEN 승인된 보호 acceptance가 canonical runner로 실행되면 시스템은 기존 성공/실패 의미와 종료값을 보존해야 한다.
2. WHEN 보호 script가 `exit 0`, `true`, `:`, empty로 치환되면 시스템은 실행 전에 non-zero로 차단해야 한다.
3. WHEN script가 정확한 가짜 `PASS`, `CHECKED`, `VERDICT: PASS`를 출력하면 시스템은 성공 권한을 부여하지 않아야 한다.
4. WHEN 실제 정상 출력 전체를 literal로 복사한 위조 script가 실행되면 시스템은 non-zero로 차단해야 한다.
5. WHEN 정상 검사 한 건 뒤 나머지 출력을 위조하면 시스템은 non-zero로 차단해야 한다.
6. WHEN stderr, ANSI, CR, 중복 marker, 선두/후행 숫자, 음수, overflow, 순서 변경으로 parser를 공격하면 시스템은 성공 권한을 부여하지 않아야 한다.
7. WHEN target content가 승인 contract와 다르면 시스템은 target 실행 전에 FAIL 또는 NOT_RUN으로 거부해야 한다.
8. WHEN contract, target, registry가 missing·malformed·duplicate-key·symlink·hardlink·untracked·repo 밖이면 시스템은 exit 2와 CHECKED 0을 출력해야 한다.
9. WHEN target 자체가 정상 실패하면 시스템은 원 실패를 성공으로 바꾸지 않아야 한다.
10. WHEN 보호 inventory가 비거나 감소하거나 중복되면 시스템은 vacuous PASS를 거부해야 한다.
11. WHILE mutation이 mktemp clone에서 실행될 때 시스템은 원본 worktree의 HEAD, staged, status hash를 바꾸지 않아야 한다.
12. WHEN rollback을 수행하면 신규 contract·validator·acceptance·wiring commit을 폐기해 base runner 동작으로 되돌릴 수 있어야 한다.

## Counter-AC

- PASS line 수나 CHECKED parser만 강화한 구현은 불합격이다.
- 정상 출력 literal replay가 통과하면 불합격이다.
- basename, repo 밖 copy, symlink, hardlink, untracked temp copy가 통과하면 불합격이다.
- `tail -1`, 숫자 추출, ANSI/CR, duplicate marker first/last 선택에 판정 권한이 남으면 불합격이다.
- inventory path 한 개 삭제나 중복 후 전체 검사가 PASS하면 불합격이다.
- 정상 acceptance의 intended fixture args를 막으면 불합격이다.
- contract digest만 스스로 다시 계산해 같은 actor가 승인할 수 있음을 전체 안전성 해결로 표현하면 불합격이다.
- WU0-C/D/E나 WU0-A3 입력 identity를 해결했다고 주장하면 불합격이다.

## RED 원장

제품 코드 전에 WU0-B 전용 acceptance만 추가해 다음을 현재 runner에 실행한다.

1. `exit 0`
2. `true`, no-op, empty
3. fake PASS
4. fake PASS + CHECKED 99
5. fake PASS + CHECKED + VERDICT PASS
6. 실제 정상 출력 literal replay
7. 정상 검사 한 건만 실행하고 나머지 출력 replay
8. stderr/ANSI/CR/duplicate marker·숫자 변형
9. symlink/outside-repo/untracked/hardlink target
10. contract missing/malformed/duplicate/reduced/empty inventory

RED는 미래 validator를 직접 호출하지 않는다. 현재 runner에 mktemp fake/replay target을 넘겼을 때 exit 0으로 승인되는 현상과 현재 contract 부재를 전용 acceptance가 명시적으로 실패로 기록한다. 문법 오류가 아니라 빠진 identity 권한 때문에 exit 1이 되며, RED commit에는 fixture/test만 넣는다.

## PLAN 검토 기준

- JSON pinned registry와 기존 CI contract 확장안을 비교한다.
- 기존 `ci-required-steps.json`은 workflow 선언 정본이라 script content identity를 섞지 않는다.
- Git blob ID만 사용하는 대안은 working tree 실행 bytes와 직접 대조가 복잡하고 SHA-1 저장소 의존을 늘려 기각한다.
- 출력 parser 강화는 위조자가 같은 출력 채널을 소유하므로 기각한다.
- plan reviewer는 inventory 정의, exit 1/2 구분, hardlink, fixture args, update 절차, WU0-D 경계를 counter-AC로 공격한다.

## Harness와 R2~R5

- Gate 0~1: 시작 SHA, SOT, T, inventory, RED 원장을 이 문서로 고정한다.
- Gate 2: 전용 worktree와 RED fixture/test-only commit.
- Gate 3: JSON contract, validator, runner, CI/pre-push/SOT wiring 최소 변경으로 GREEN.
- Gate 3.5/R4: workflow·pre-push → runner → validator → contract → target 호출을 정적·실행으로 증명한다.
- Gate 4/R2: validator·runner·contract 각각을 mktemp에서 일부러 고장 내 전용 acceptance가 실패하는지 확인한다.
- R3: CRLF, locale, whitespace, duplicate registry entry, malformed JSON, empty inventory, 비표준 path를 공격한다.
- R4/V1: 실제 diff, 원검증, mutation 원문을 다른 엔진 Claude가 대조한다.
- R5/V2: 구현 맥락을 상속하지 않은 Codex가 V1 근거와 핵심 위조를 직접 재실행한다.
- 구현 종료 후 `humanreview`를 읽기 전용으로 실행해 T와 diff·현재 증거를 공격한다.

## 정상 검증 G

- 변경 shell 전부 `bash -n`.
- WU0-B 전용 acceptance.
- `scripts/acceptance-semantic-mutations.sh`.
- 보호 inventory의 모든 canonical runner 실행.
- `scripts/acceptance-ci-step-integrity.sh`.
- `scripts/verify/check-mechanism-registry.sh`.
- `scripts/acceptance-verify-ac-m.sh`.
- `scripts/acceptance-principles-check.sh`.
- `scripts/check-docs-sot.sh`.
- `verify.sh`.
- `git diff --check`.
- 0 targets, skipped targets, unexpected exit가 없어야 한다.
- 모든 원명령의 START/END UTC, exit, CHECKED/VERDICT를 원문으로 보존한다.

사용자 표기의 `scripts/acceptance-mechanism-registry.sh`, `scripts/acceptance-ac-m-registry.sh`, `scripts/verify/check-docs-sot.sh`, `scripts/verify.sh`는 base에 존재하지 않는다. PLAN 3·6의 “현재 배선 분석·기존 패턴 우선”에 따라 현재 SOT가 지정한 실제 명령인 `scripts/verify/check-mechanism-registry.sh`, `scripts/acceptance-verify-ac-m.sh`, `scripts/check-docs-sot.sh`, `verify.sh`로 검증 명령명을 정정한다. 없는 경로를 위한 wrapper·symlink·우회 호환 계층은 만들지 않는다. 이 정정을 인정하지 않으면 네 원문 경로는 `NOT_RUN`이고 최종 WU0-B PASS도 불가하다는 한계를 최종 보고에 그대로 남긴다.

## 갱신 절차와 WU0-D 경계

1. 승인할 target bytes와 canonical path를 확정한다.
2. target SHA-256을 계산해 정렬된 JSON inventory entry를 갱신한다.
3. JSON duplicate/schema/target count 검사를 실행한다.
4. contract 원문 SHA-256을 계산해 validator의 pinned digest를 갱신한다.
5. WU0-B acceptance, 전 canonical runner, CI/pre-push wiring 검사를 실행한다.
6. registry와 validator pin 동시 변경을 reviewer가 별도 검토한다.

이 절차는 정상 유지보수다. 같은 actor가 target, contract, validator, runner, workflow를 모두 악의적으로 약화해도 막는 외부 trust root는 WU0-D가 맡는다.

## 영향 반경·데이터 안전·롤백

- 영향 반경: 로컬/CI acceptance runner와 그 target identity contract, 전용 acceptance, CI/SOT wiring.
- 후보자·고객·운영 데이터와 외부 API를 읽거나 쓰지 않는다.
- mutation은 git 환경변수를 해제한 `mktemp` clone에서만 수행한다.
- 원본 main과 다른 worktree는 읽기 비교 외 수정하지 않는다.
- 롤백은 WU0-B RED/GREEN/evidence commit을 역순 폐기해 implementation base `169fad3`로 복귀한다. branch creation base `d782079`와 그 뒤의 A2 evidence correction은 구분하며 원격 rollback은 수행하지 않는다.

## 결정 카드

> **무엇을** — validator에 원문 digest를 pin한 JSON content registry로 canonical runner target을 실행 전 검증한다.
> **왜** — 출력은 공격자가 쓸 수 있지만 고정 validator와 독립 contract가 승인한 bytes는 script 단독 변조자가 위조할 수 없다.
> **버린 길** — PASS/CHECKED parser 강화, 기존 CI step contract에 content identity 혼합, Git blob ID 단독 비교를 기각한다.
> **대가** — 승인된 script 변경마다 digest와 pin 갱신이 필요하고, 동시 trust-root 약화는 WU0-D가 남는다.
> **되돌리기** — WU0-B commit을 폐기하면 기존 runner와 wiring으로 돌아간다.

## 적대 검증 로그

### 구현 전 PLAN reviewer

- 최초 판정: `REJECT`. pre-push의 `./scripts/...` 입력, 네 부재 명령의 상태, implementation base, hardlink 판정, RED의 미래 validator 의존이 불명확했다.
- 보정: hook-side `${c#./}`, actual SOT command name correction, implementation base `169fad3`, `lstat`/`nlink`/tracked 계약, future validator 미호출 RED를 명시했다.
- 재판정: `VERDICT: PASS`, blocking finding 0개.

RED→GREEN, G, R2/R3, V1/V2, humanreview 원문 경로와 SHA는 구현 진행 중 이 절에 추가한다.
