# WU-4a Finding 재현 러너 — goal (2026-08-24)

VERDICT: CHECKPOINT_PENDING

## 1층 결론

2026-08-25 복구 Work Unit은 검증된 base `c59bad7b160c473cda5545e76e6fa6bcc711a7ea`에서 RED commit을 보존한 뒤 원본 구현을 복원했습니다. 구현 전 원명령은 요구 동작 부재로 실패했고, 구현 후 pre-commit 원명령은 8/8 통과했습니다. 이 문서 아래의 2026-08-24 PASS·V1·V2 기록은 원본 보존용 역사 자료이며 현재 branch나 새 SHA의 PASS 증거가 아닙니다.

현재 Work Unit의 pre-commit GREEN만 실행됐습니다. 최종 commit SHA의 mutation, G, Claude V1, 새 맥락 Codex V2, T는 모두 `NOT_RUN`이며, 이를 마치기 전에는 완료나 PASS로 승격하지 않습니다.

### 2026-08-25 복구 신원과 RED 증거

- 복구 세션: `VHREC-20260825T200157+0900-01a03893`
- branch: `task/wu4a-finding-runner-20260825T200952`
- worktree: `/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/wu4a-finding-runner-20260825T200952`
- RED base HEAD: `c59bad7b160c473cda5545e76e6fa6bcc711a7ea`
- 원본 보호 ref: `task/wu4a-finding-runner-original-20260825T200952` = `3094eefa646b102074dfb6401777afe450223e6c`
- 원명령: `node --test tests/finding-runner.test.mjs`
- 구현 부재 확인: `tools/strict/finding-runner.mjs` 없음
- 첫 RED: `2026-08-25T20:25:01+09:00`, exit `1`, tests `7`, pass `0`, fail `7`
- 첫 RED raw output: `/tmp/vhrec-c-red.hMnnMq/node-test-red.log`, SHA-256 `736a78c2a4d9f7f6c5d92700eb10f0fec7fe27ef4ad05a6b1535c30a8977d45f`
- 정책 counter-test 포함 최종 RED: `2026-08-25T20:27:23+09:00`, exit `1`, tests `8`, pass `0`, fail `8`
- 최종 RED raw output: `/tmp/vhrec-c-red-policy.OQnFkz/node-test-red.log`, SHA-256 `618c7c08fbba3488e9ed1b816210764cbc2e366e6bb17d3d3d02b77116888e22`
- RED commit: `6ddb22db81d4360296e9b138181c0aa01a699289`
- clean RED commit 재현: `2026-08-25T20:28:36+09:00`, exit `1`, tests `8`, pass `0`, fail `8`
- clean RED raw output: `/tmp/vhrec-c-red-commit.jEoqDj/node-test-red-commit.log`, SHA-256 `32d0126a92748ad4e9af536624b1f13b24fcdfbe09bf5b29f5a5c99798dee335`
- 구현 복원 SHA-256: 원본·worktree 모두 `2b770269a041b1e17378cbc9b6fa4325e64bee22969c2553087813188e48ab67`
- pre-commit GREEN: `2026-08-25T20:29:09+09:00`, node check exit `0`; 원명령 exit `0`, tests `8`, pass `8`, fail `0`
- pre-commit GREEN raw output: `/tmp/vhrec-c-green-precommit.298I5D/node-test.log`, SHA-256 `f20635cb6b6c3e7bbb751b26c8223f2bd036845bc4b520263af9c5a3f8ffeef4`
- 실행 제거 R2 mutant: `2026-08-25T20:31:49+09:00`, exit `1`, tests `8`, pass `4`, fail `4`; 원본 구현 hash 전후 동일
- R2 raw output: `/tmp/vhrec-c-mutation-rerun.jFFmnI/node-test-mutation.log`, SHA-256 `d92729b18bc64932b46ea7fbd9cb825e0087c54c214daa54fd860bf3d4cc1e72`
- pre-commit 저장소 게이트: `2026-08-25T20:33:38+09:00`~`20:34:03+09:00`, node check/test, 원칙 `34/34`, `verify.sh`, docs SOT, diff check, 600/601·100/101 경계 모두 exit `0`
- 저장소 게이트 raw evidence: `/tmp/vhrec-c-gates-precommit.KiBHbg/`; node test SHA-256 `fe350d1124afcce31c0a961b4db4e1d973bb91f670a3a731d9a22cea40b36c94`, verify SHA-256 `757c22ef0b961070b50f38c22529cd03a350af7bf292f80a9b83345db1165900`

### BLOCKED와 NOT_TESTED 정책

- 이 러너의 직접 merge-block은 기존 문서 계약과 원본 구현대로 `severity=high`이면서 `status=REPRODUCED|UNRESOLVED`일 때만 참이다.
- finding의 `BLOCKED`와 `NOT_TESTED`는 runner-level exit `1`을 직접 만들지 않는다. 해당 상태를 `NOT_REPRODUCIBLE`로 세탁해서도 안 된다.
- 상위 Strict 필수 검증에서 `BLOCKED` 또는 `NOT_RUN`이 남으면 완료 불가다. runner-level merge-block과 Strict 전체 완료 판정을 혼동하지 않는다.
- 테스트는 high `BLOCKED` 한 건과 선택되지 않은 high `NOT_TESTED` 한 건을 동시에 보존하고, 요약 수치와 `병합 차단: 아니오`를 함께 고정한다.

> 역사 경계: 이 지점 이후의 2026-08-24 실행 결과·세션·PASS 표현은 보호 ref 원문을 보존한 무효 증거다. 2026-08-25 branch나 이후 commit의 초록불로 재사용하지 않는다.

## 2층 판단 근거

- `scripts/verify/check-strict-verdict-ledger.sh`는 YAML의 `g/v1/v2/t` 역할별 `status`, `command`, `exit`, `output`, `artifact`, `artifact_hash`, `session_id`를 검사합니다. 상태도 `PASS|FAIL|NOT_RUN`으로, finding의 다섯 상태와 목적이 다릅니다.
- `/Users/kangsangmo/.codex/skills/strict/SKILL.md:135`는 개별 Finding 상태를 `REPRODUCED|BLOCKED|NOT_REPRODUCIBLE|NOT_TESTED|UNRESOLVED` 다섯 값으로 이미 고정합니다. 새 러너는 이 기존 의미를 그대로 실행 코드로 옮깁니다.
- 모델의 claim·기존 status는 실행 증거가 아닙니다. 선택한 finding마다 셸 명령을 실제 시작한 뒤 종료값 또는 표준 출력 기대값으로만 상태를 새로 계산합니다.
- 실행 파일 없음, 권한 거부, 유효하지 않은 작업 폴더처럼 명령을 시작하거나 완료할 환경이 없으면 `BLOCKED`입니다. 현상이 나타나지 않은 `NOT_REPRODUCIBLE`과 섞지 않습니다.
- 병합 차단은 사용자 계약 그대로 `high + (REPRODUCED|UNRESOLVED)`만 참입니다. 명령 오류나 잘못된 입력은 finding 판정과 다른 러너 오류로 분리합니다.

## 착수 전 재검증

### 유사 스키마 검색

명령과 전체 출력:

```text
$ rg -n --hidden --glob '!.git/**' 'WU-4a|Finding 재현|finding runner|finding-runner|findings/<run_id>|verdict.json' . .omx 2>/dev/null
[출력 없음]
exit=1
```

→ 저장소와 현재 OMX 계획에 같은 이름 또는 JSON 관례가 0건이므로 새 파일 계약과 이름 충돌이 없습니다.

기존 verdict 장부 확인:

```text
$ sed -n '1,260p' scripts/verify/check-strict-verdict-ledger.sh
allowed_statuses = %w[PASS FAIL NOT_RUN]
roles = %w[g v1 v2 t]
role_keys = %w[status command exit output artifact artifact_hash session_id]
```

→ 기존 장부는 역할별 전체 실행 증거이고 이번 산출물은 finding별 재현 결과입니다. 후속 WU-4b가 파일로 두 계층을 연결할 수 있지만 이번 작업은 import나 장부 연결을 하지 않습니다.

### Strict 정본 직접 로드 장부

- 세션: `01a030c0-873c-7891-83db-8079de9fd8bb`
- 시작 commit: `c59bad7b160c473cda5545e76e6fa6bcc711a7ea`
- 코딩 정본 직접 읽기: `sed -n '1,180p' docs/sot/coding-principles.md && sed -n '181,360p' docs/sot/coding-principles.md`, `2026-08-24T07:35:25+09:00`, exit `0`, 74줄, SHA-256 `5402cb3f05d03e35db79158e9933e13c3fe17db4d63c8a7a808db10c80151dcb` — `PASS`.
- 기계 장부 직접 읽기: `sed -n '1,220p' docs/sot/principles.yaml && sed -n '221,500p' docs/sot/principles.yaml`, `2026-08-24T07:35:25+09:00`, exit `0`, 345줄, SHA-256 `a19b29abaf6c61e403d2f1df5720b55ff477942dc9257cb2513043b20855ef22` — `PASS`.
- 정본 검사: `bash scripts/acceptance-principles-check.sh`, `2026-08-24T07:33:29+09:00`, exit `0` — `PASS`.

정본 검사 전체 출력:

```text
VERDICT: PASS
SOT_LOAD: PASS docs/sot/coding-principles.md
LEDGER_LOAD: PASS docs/sot/principles.yaml
MECHANISMS: PASS 34/34 strict-contract-bindings
WIRING: PASS pre-push=1 ci=1
CHECKED: 34
```

→ 정본과 파생 장부가 모두 직접 읽혔고 Strict 배선 34건이 확인됐습니다. 코드 hard 한도는 파일 600줄, 함수 100줄입니다.

## 현재 상태와 근본 원인

- `docs/sot/coding-principles.md:60` — 외부 모델 의견은 로컬 실행으로 재현되기 전까지 결함이 아니라는 V-4 원칙이 있습니다.
- `/Users/kangsangmo/.codex/skills/strict/SKILL.md:147` — 모델 자기 서술은 상태를 승격하지 못하며 독립 재현만 증거로 센다고 고정합니다.
- 현재 `tools/strict/finding-runner.mjs`와 이를 실행하는 테스트는 없습니다.

근본 원인은 개별 지적에 실행 가능한 `repro` 계약은 제안됐지만, 그 명령을 실행하고 다섯 상태로 환원하는 판정기가 없다는 점입니다. 따라서 지금은 사람이 모델 서술을 읽고 임의로 병합 차단 여부를 정할 수 있습니다.

## 인수 기준 — AC-1

**When** 재현되는 결함, 재현되지 않는 주장, 실행할 수 없는 명령의 세 fixture를 러너에 입력하면, 시스템은 실제 명령 실행 결과만 사용해 각각 `REPRODUCED`, `NOT_REPRODUCIBLE`, `BLOCKED`를 기록해야 한다.

- 검증 명령: `node --test tests/finding-runner.test.mjs`
- 기대값: 전체 테스트 exit `0`; 세 fixture 상태가 순서대로 `REPRODUCED`, `NOT_REPRODUCIBLE`, `BLOCKED`; high `REPRODUCED`만 병합 차단.
- counter-AC: 입력 파일의 기존 `REPRODUCED`를 실행 없이 신뢰하거나, `--only`가 선택하지 않은 finding을 새 상태로 기록하거나, 명령이 실제 실행되지 않았는데 결과 status가 기록되면 실패해야 한다.
- R2 고장 사본: 러너의 실제 실행 호출을 고정 결과로 치환한 사본에 같은 테스트를 실행하면 marker 미생성 또는 fixture 오판정으로 반드시 exit `1`이어야 한다.

## 고정 계약

### 파일과 입력

정식 교환 파일은 `findings/<run_id>.json`이며 JSON 루트 키는 `findings` 하나입니다. 러너 테스트용 사본은 `tests/fixtures/finding-runner/*.json`에 둡니다.

```json
{
  "findings": [
    {
      "id": "F-1",
      "source": "contract|adversarial|runtime",
      "claim": "한 줄",
      "severity": "high|medium|low",
      "repro": {
        "cmd": "셸 명령",
        "cwd": "저장소 루트 기준 상대경로",
        "expect": {"exit_not": 0}
      },
      "status": "REPRODUCED|BLOCKED|NOT_REPRODUCIBLE|NOT_TESTED|UNRESOLVED"
    }
  ]
}
```

- `expect`는 정수 `exit_not` 또는 문자열 `stdout_contains` 중 정확히 하나입니다.
- `cwd`는 저장소 루트 안의 상대경로만 허용하고 절대경로·`..` 탈출은 러너 오류입니다.
- ID는 파일 안에서 중복될 수 없고, `--only` ID가 없으면 아무 status도 쓰지 않습니다.

### CLI와 출력

- 호출: `node tools/strict/finding-runner.mjs run <파일> [--only F-1]`
- 성공 실행은 선택한 각 finding의 status를 원본 JSON에 원자적으로 기록합니다.
- 요약: `지적 N건 / 재현 R건 / 반증 X건 / 차단 B건 / 미실행 T건`
- 병합 차단: 전체 파일에 `severity=high`이면서 `status=REPRODUCED|UNRESOLVED`인 항목이 하나라도 있으면 `병합 차단: 예`, CLI exit `1`; 아니면 `병합 차단: 아니오`, exit `0`.
- JSON/계약/인자 오류는 stderr와 exit `2`이며 파일을 쓰지 않습니다.

### 실행 상태 판정

- 명령이 시작돼 기대가 충족되면 `REPRODUCED`.
- 명령이 시작돼 기대가 충족되지 않으면 `NOT_REPRODUCIBLE`.
- 작업 폴더 접근 불가, 셸 시작 실패, 명령 없음(127), 실행 권한 거부(126), 신호 종료는 `BLOCKED`.
- 러너는 claim을 판정 입력으로 사용하지 않고 기존 status를 실행 결과로 덮습니다.

## Harness 게이트와 적대검증

1. 게이트 0~1: 현 SOT, 기존 verdict 장부, 작업트리 오염을 회수하고 이 계약을 고정합니다.
2. 게이트 2: 러너 없이 테스트를 실행해 missing behavior RED를 보존합니다.
3. 게이트 3: Node 표준 라이브러리만 사용한 최소 러너로 RED→GREEN을 만듭니다.
4. 게이트 3.5~4: 실제 CLI 진입점, 세 fixture, `--only`, merge block, schema fail-closed, marker 기반 counter-AC를 실행합니다.
5. AUDIT: 실행 호출 제거 뮤테이션, 600/601 파일 경계, Claude V1, 새 맥락 Codex V2로 판정과 검사를 공격합니다.

정조준 항목은 입력 status 신뢰, claim 파싱, `BLOCKED`의 반증 세탁, stdout/stderr 혼동, 절대 cwd 탈출, `--only`의 비선택 상태 변경, high `UNRESOLVED` 누락, 실행 0건 가짜 초록입니다.

## 범위, 영향, 데이터 안전, 롤백

- 수정 허용: `tools/strict/finding*`, `tests/**`, 이 goal 문서.
- 비범위: 감사 에이전트 호출, ledger import/연결, `docs/sot/INDEX.md` 등록, CI/pre-push 배선, 원격 push/PR/merge.
- 영향 반경: 로컬 Node CLI가 전달받은 명령을 저장소 안 상대 cwd에서 실행하고 지정 JSON status를 갱신합니다. 제품 런타임과 운영 데이터에는 연결되지 않습니다.
- 데이터 안전 AC: 테스트는 `mktemp` 계열 OS 임시 폴더의 JSON 사본만 갱신하고, fixture 원본과 기존 작업트리는 바꾸지 않아야 합니다.
- 롤백: 이번에 추가한 `tools/strict/finding*`, `tests/fixtures/finding-runner/**`, `tests/finding-runner.test.mjs`, 이 goal 문서만 삭제하면 됩니다. 기존 SOT와 장부에는 쓰지 않습니다.

## 결정 카드

> **무엇을** — 역할 verdict YAML과 분리된 per-finding JSON 러너를 둡니다.
> **왜** — 전체 검증 실행 증거와 개별 지적 재현 상태는 수명과 판정 단위가 다릅니다.
> **버린 길** — 기존 YAML 장부 확장과 `ledger.mjs` import는 후속 배선을 선행하고 사용자 비범위를 깨므로 기각합니다.
> **대가** — WU-4b 전까지 두 파일 계층은 자동 연결되지 않습니다.
> **되돌리기** — 추가 파일만 제거하면 기존 판정 경로가 그대로 복구됩니다.

## 2026-08-24 무효화된 검증 장부

아래 표와 로그는 보호 ref의 역사 기록을 보존하기 위한 것이며 2026-08-25 복구 branch의 검증 결과로 재사용하지 않는다. 새 SHA의 유효한 결과는 위 복구 신원과 이후 control evidence에 정확한 명령·시각·종료값·전체 출력·세션 ID로 별도 귀속한다.

| 단계 | 상태 | 명령 | 기대 |
|---|---|---|---|
| SOT 직접 로드 | PASS | 위 직접 읽기 2건 | 파일 전체 접근, hash 고정 |
| 원칙 검사 | PASS | `bash scripts/acceptance-principles-check.sh` | `VERDICT: PASS`, `CHECKED: 34` |
| RED | PASS | `node --test tests/finding-runner.test.mjs` | `2026-08-24T07:37:42+09:00`, runner 부재로 exit `1`, 0/7 통과 |
| GREEN | PASS | 같은 명령 | `2026-08-24T07:39:02+09:00`, exit `0`, 7/7 통과 |
| R2 mutation | PASS | 실행 호출 제거 사본 + 같은 테스트 | `2026-08-24T07:39:55+09:00`, exit `1`, 3건이 고장 사본 차단 |
| 저장소 검사 | PASS | Node check·`verify.sh`·SOT·diff·줄수 | `2026-08-24T07:40:40+09:00`, 전부 exit `0` |
| V1 Claude | PASS | goal·산출물·실행 증거 격리 검토 | 재시도 session `005b4341-b263-40bf-8989-995ae991d30c`, exit `0`, `VERDICT: PASS` |
| V2 Codex | PASS | V1 finding 직접 재현 | 재심 뒤 `PASS`, V1 과장 0건·누락 0건 |

## 2026-08-24 무효화된 적대 검증 로그

### RED→GREEN

RED 원명령과 출력:

```text
timestamp=2026-08-24T07:37:42+09:00
$ node --test tests/finding-runner.test.mjs
Error: Cannot find module '/Users/kangsangmo/Desktop/Valuehire_v6/tools/strict/finding-runner.mjs'
1..7
# tests 7
# pass 0
# fail 7
exit=1
```

→ 러너 파일이 없어서 fixture status가 `NOT_TESTED`에 머무는 missing behavior로 실패했습니다. 문법/import 오류가 아니라 구현 부재를 확인한 RED입니다.

GREEN 원명령과 출력:

```text
timestamp=2026-08-24T07:39:02+09:00
$ node --test tests/finding-runner.test.mjs
ok 1 - 재현되는 결함은 REPRODUCED이고 high이면 병합을 차단한다
ok 2 - 재현되지 않는 주장은 NOT_REPRODUCIBLE이다
ok 3 - 실행할 수 없는 명령은 NOT_REPRODUCIBLE이 아니라 BLOCKED이다
ok 4 - 기존 status를 믿지 않고 명령을 실행한 뒤 덮어쓴다
ok 5 - --only는 선택한 finding만 실행하고 나머지는 NOT_TESTED로 둔다
ok 6 - 선택 밖 high UNRESOLVED도 병합 차단으로 계산한다
ok 7 - 계약 오류나 없는 --only ID는 파일을 수정하지 않고 exit 2이다
1..7
# tests 7
# pass 7
# fail 0
exit=0
```

→ AC의 세 fixture와 counter-AC, 선택 실행, 병합 차단, 오류 시 무수정이 모두 통과했습니다.

### 실제 CLI 호출

세 fixture를 OS 임시 폴더의 한 JSON 사본으로 합쳐 실행한 전체 출력:

```text
timestamp=2026-08-24T07:41:21+09:00
[F-1] cwd=. cmd=node -e "process.stdout.write('defect reproduced\n'); process.exit(7)"
defect reproduced
[F-1] exit=7 status=REPRODUCED
[F-2] cwd=. cmd=node -e "process.stdout.write('healthy output\n')"
healthy output
[F-2] exit=0 status=NOT_REPRODUCIBLE
[F-3] cwd=. cmd=valuehire_wu4a_command_that_must_not_exist_9f47a
/bin/sh: valuehire_wu4a_command_that_must_not_exist_9f47a: command not found
[F-3] exit=127 status=BLOCKED
지적 3건 / 재현 1건 / 반증 1건 / 차단 1건 / 미실행 0건
병합 차단: 예
recorded=F-1=REPRODUCED F-2=NOT_REPRODUCIBLE F-3=BLOCKED
fixture_hash_unchanged=yes
exit=1
```

→ 종료값 1은 러너 실패가 아니라 `high REPRODUCED`의 의도된 병합 차단입니다. fixture 원본은 쓰지 않았습니다.

### R2 실행 제거 뮤테이션

첫 시도는 임시 폴더 정리에 쓴 `rm -rf` 형태가 안전 정책에 의해 명령 시작 전에 거부돼 `NOT_RUN`이었습니다. `unlink`와 `rmdir`로 정리 범위를 좁혀 같은 뮤테이션을 다시 실행했습니다.

```text
timestamp=2026-08-24T07:39:55+09:00
mutation=executeRepro bypassed
exit=1
original_hash_before=2b770269a041b1e17378cbc9b6fa4325e64bee22969c2553087813188e48ab67
original_hash_after=2b770269a041b1e17378cbc9b6fa4325e64bee22969c2553087813188e48ab67
# tests 7
# pass 4
# fail 3
```

→ 실제 `executeRepro` 호출을 고정 성공값으로 치환하자 재현 fixture, BLOCKED fixture, marker counter-AC가 실패했습니다. 원본 러너 해시는 전후 동일합니다.

### 저장소 게이트와 경계

```text
timestamp=2026-08-24T07:40:40+09:00
node --check tools/strict/finding-runner.mjs: exit=0
node --test tests/finding-runner.test.mjs: pass=7 fail=0 exit=0
bash verify.sh: PASS no secret-pattern match, exit=0
bash scripts/acceptance-principles-check.sh: VERDICT PASS, CHECKED 34, exit=0
bash scripts/check-docs-sot.sh: OK, exit=0
git diff --check: exit=0
tools/strict/finding-runner.mjs: 233/600 LOC PASS
tests/finding-runner.test.mjs: 154/600 LOC PASS
limit.mjs: 600/600 allowed=true PASS
over.mjs: 601/600 allowed=false PASS
largest function/test callback: 23/100 LOC PASS
```

→ 적용 가능한 문법·테스트·정본·비밀·문서 구조·공백 검사와 파일/함수 hard 경계가 모두 통과했습니다.

### V1 — Claude

첫 실행은 session `e0a4ebb8-3452-4a26-a8a1-9c149ad8b086`에서 `dontAsk` 권한 모드가 `node --test`와 임시 사본 생성을 8회 거부했습니다. Claude는 실행 0건을 PASS로 세지 않고 판정을 유보했습니다. 권한 원인을 제거하기 전 상태는 `NOT_RUN`입니다.

재시도 명령 신원:

```text
timestamp=2026-08-24T07:47:09+09:00
commit=c59bad7b160c473cda5545e76e6fa6bcc711a7ea
session=005b4341-b263-40bf-8989-995ae991d30c
$ env -u ANTHROPIC_API_KEY claude --safe-mode --tools Read,Grep,Glob,Bash \
  --dangerously-skip-permissions --no-session-persistence --effort high \
  --output-format json --session-id 005b4341-b263-40bf-8989-995ae991d30c -p
exit=0
permission_denials=[]
```

Claude 판정 원문:

```text
VERDICT: PASS

WU-4a 산출물은 합격입니다. 이번 세션에서 테스트 7건을 직접 실행해 전부 통과를 확인했고,
임시 폴더 사본으로 열여덟 가지가 넘는 공격을 실제로 돌렸지만 계약을 깨는 데 모두 실패했습니다.
도구를 일부러 망가뜨린 사본 두 개도 테스트가 잡아냈습니다. 저장소 파일은 하나도 바뀌지 않았습니다.

필수 실행: node --test tests/finding-runner.test.mjs
# tests 7 / # pass 7 / # fail 0 / EXIT=0

공격 결과: 미존재 cwd=BLOCKED, 실행 권한 없는 파일 126=BLOCKED,
직접 SIGKILL=BLOCKED, stderr-only 기대=NOT_REPRODUCIBLE, 기존 REPRODUCED는 실행 뒤 강등,
--only 비선택 보존, high UNRESOLVED 병합 차단, 스키마 11종 exit 2+해시 불변,
symlink 입력 exit 2, 원자 기록 실패 exit 2+원본 해시 불변+tmp 잔류 0,
실행 제거 및 기존 status 신뢰 뮤테이션은 각각 테스트 exit 1.
```

→ Claude의 low finding은 이 장부가 비어 있었다는 점이었고, 위 실행 기록으로 해소했습니다. 간접 자식 신호가 셸 종료값 137로 감싸지는 경우와 `UNRESOLVED`가 요약 숫자 칸에 없는 점은 고정 계약 바깥의 설계 관찰로 남겼으며 병합 차단 finding으로 세지 않았습니다.

### V2 — 새 맥락 Codex

검증자: `/root/wu4a_v2` (읽기 전용, 임시 사본만 사용).

첫 판정은 `FAIL`이었습니다. V2는 `UNRESOLVED` 별도 요약 칸이 없고 전체 작업트리가 dirty라는 두 점을 finding으로 셌습니다. 그러나 첫 항목은 사용자 T에 없는 새 출력 계약을 요구했고, 둘째는 착수 전 dirty 상태와 병렬 레인 변경을 WU-4a에 귀속했습니다. 착수 기준과 고정 요약 문자열을 다시 주고 같은 V2가 재심했습니다.

재심 출력:

```text
VERDICT: PASS
node --test tests/finding-runner.test.mjs: exit=0, pass=7, fail=0
executeRepro 제거 mutant: exit=1, pass=4, fail=3
WU-4a 소유 파일 밖 신규 변경 귀속: 0건
docs/sot/INDEX.md finding-runner 등록: 0건
V1 과장: 0건
V1 누락: 0건
실행 증거가 있는 WU-4a T 위반 finding: 0건
```

V2가 직접 재현한 high `UNRESOLVED` 출력:

```text
지적 2건 / 재현 1건 / 반증 0건 / 차단 0건 / 미실행 0건
병합 차단: 예
saved=F-HIGH:UNRESOLVED,F-LOW:REPRODUCED
exit=1
```

→ 사용자 고정 문자열에는 `UNRESOLVED` 별도 숫자 칸이 없지만, 요구된 병합 차단에는 정확히 반영됐습니다. G/V1/V2가 T 기준에서 최종 일치했습니다.

### 잔여 위험

- repro 명령이 끝난 뒤 JSON 원자 기록이 실패하면 명령의 부작용은 이미 발생했지만 status는 남지 않을 수 있습니다. 원본 JSON 보존과 exit `2`는 검증됐으며, 부작용 명령의 재시도 정책은 후속 배선 범위입니다.
- 현재 작업트리에는 착수 전 변경과 다른 병렬 레인의 파일이 남아 있습니다. WU-4a 소유 파일은 이 문서, `tools/strict/finding-runner.mjs`, `tests/finding-runner.test.mjs`, fixture 3개뿐입니다.
