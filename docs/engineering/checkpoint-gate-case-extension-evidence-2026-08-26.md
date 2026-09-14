# WU-3a 대소문자 확장자 우회 검증 증거 — 2026-08-26

## 판정

- WU-3a logic: `PASS`
- checkpoint readiness: `NOT_RUN`
- overall T: `NOT_RUN`
- 기준 HEAD: `3094eefa646b102074dfb6401777afe450223e6c`
- 후보 staged tree: `2124a615104a06a1f1ae43cc19e8252879a6945b`
- 후보 cached diff SHA-256: `88c08534bd13e7e6e051daa8d8c545f81549effb9f9889fc58c9d92db9d3172f`
- 후보 staged 파일 수: `5`

최종 V1/V2 결과를 goal 문서에 다시 넣으면 검증 대상 해시가 바뀌는 순환이 생긴다. 따라서 goal 문서에는 계약, RED 기록, 최초 실패 해시의 판정과 보완 내용을 두고, 최종 후보 해시를 대상으로 한 V1/V2 판정은 이 별도 증거 파일에 둔다. 이 파일은 위 후보 staged tree의 구성원이 아니며 실제 index에도 올리지 않았다.

## 결함과 수정

### 대문자 코드 확장자 크기 우회

- 원인: `tools/strict/checkpoint-gate.mjs`의 `isSizeCheckedCode`가 확장자를 대소문자 그대로 비교했다.
- 입력: index P11 hard 600, worktree P11 hard 99999 미끼, staged `src/oversized.JS` 또는 `src/oversized.TSX` 601 LOC.
- 수정: 마지막 확장자만 소문자로 만드는 공통 `normalizeExtension`을 경로 판정 전에 호출한다.
- 결과: staged count 1, exit 1, `size-limit`, `file has 601 LOC, hard limit is 600`.
- 정상쌍: 같은 파일 600 LOC, staged count 1, exit 0, `{"pass":true,"violations":[]}`.

### 대문자 테스트 확장자 약화 우회

- 원인: `isTestFile`과 `countWeakeningMarkersForFile`이 `.JS`와 `.TSX`를 테스트/JavaScript 파일로 인식하지 않았다.
- 입력: staged `tests/unit.JS` 또는 `tests/unit.TSX`, assertion 2개에서 1개로 감소.
- 수정: 두 판정 함수 첫 줄에서 같은 `normalizeExtension`을 적용한다. 위반 JSON은 정규화 전 `change.path`를 사용한다.
- 결과: staged count 1, exit 1, `test-weakening`, `assertions decreased 2 -> 1`.
- 정상쌍: assertion 2개에서 3개로 증가, staged count 1, exit 0, `{"pass":true,"violations":[]}`.

### 정상 fixture의 staged 0 오증거

- 최초 후보의 assertion 정상쌍은 원래 내용을 복원해 staged count 0이 됐다.
- 수정 후 정상쌍은 assertion 2개에서 3개로 바꾸고, cached diff 대상이 정확히 해당 파일 하나인지 테스트가 단언한다.
- staged 0 PASS는 최종 후보 증거로 사용하지 않았다.

### P11 worktree 미끼

- 최초 후보는 hard limit을 worktree `docs/sot/coding-principles.md`에서 읽어 index hard 600을 worktree hard 99999로 우회할 수 있었다.
- 수정 후 P11은 index blob에서 읽고, index에 파일이 없을 때만 hard 500 fallback을 쓴다.
- index 600/worktree 99999에서 601 LOC는 exit 1과 hard 600을 보고했다.
- index 99999/worktree 600 역방향 미끼에서 601 LOC는 exit 0이어서 index 값이 실제 입력임을 확인했다.
- index SOT 없음/worktree 99999에서 501 LOC는 exit 1과 hard 500을 보고했다.

## RED와 GREEN

정규화 수정 전 `--test-name-pattern=uppercase` 실행은 네 회귀 모두 기대 exit 1, 실제 gate exit 0으로 실패했다. 수정 후 같은 네 회귀가 모두 통과했다. 최종 전체 결과는 다음과 같다.

```text
node --test tests/checkpoint-gate.test.mjs
tests 66 / pass 66 / fail 0 / exit 0

node --test tests/checkpoint-gate-mutation.test.mjs
tests 6 / pass 6 / fail 0 / exit 0

node --check tools/strict/checkpoint-gate.mjs
exit 0

node --check tools/strict/checkpoint-js-scan.mjs
exit 0

bash scripts/acceptance-principles-check.sh
VERDICT PASS / MECHANISMS 34/34 / exit 0

bash ~/.claude/skills/strict/brief-lint.sh docs/engineering/checkpoint-gate-goal-2026-08-24.md
exit 0

git diff --check
exit 0
```

P11 줄 수:

```text
tools/strict/checkpoint-gate.mjs                510
tools/strict/checkpoint-js-scan.mjs             572
tests/checkpoint-gate.test.mjs                  600
tests/checkpoint-gate-mutation.test.mjs         183
```

기존 62개와 대문자 신규 4개를 합친 66개가 실행됐다. 최초 62개 실행도 수정 전에 62/62로 기록했고, 최종 스위트는 66/66이다. 기존 테스트를 삭제하지 않았다.

## 독립 mutation validator

정상 bundle은 내부 exit 0이었다. 다음 다섯 no-op 고장 bundle은 validator가 각각 독립 exit 1로 거부했다.

```text
verify-exit-zero      1
scanner-always-zero   1
gate-exit-zero        1
gate-fixed-pass       1
gate-empty            1
```

추가 `gate-fixed-fail` 공격도 정상 fixture가 PASS여야 하는 구간에서 exit 1로 거부됐다.

## 후보 5파일 격리 stage

격리 저장소에서 다음 파일을 실제 stage했다.

```text
docs/engineering/checkpoint-gate-goal-2026-08-24.md
tests/checkpoint-gate-mutation.test.mjs
tests/checkpoint-gate.test.mjs
tools/strict/checkpoint-gate.mjs
tools/strict/checkpoint-js-scan.mjs
```

```text
HEAD          3094eefa646b102074dfb6401777afe450223e6c
staged count  5
tree          2124a615104a06a1f1ae43cc19e8252879a6945b
diff SHA-256  88c08534bd13e7e6e051daa8d8c545f81549effb9f9889fc58c9d92db9d3172f
gate exit     0
gate output   {"pass":true,"violations":[]}
```

검증 전후 HEAD, staged count, tree, diff SHA-256가 같았고 snapshot의 worktree-vs-index 변경과 untracked 파일은 0이었다. hook, CI, `docs/sot/INDEX.md`, P11 SOT, `verify.sh`는 후보 staged diff에 없었다.

## 실제 V1

- 실행기: Claude CLI `2.1.245`, model `claude-fable-5`
- session ID: `1f12994f-06d0-4be3-b3a1-5aac2b04b114`
- raw JSONL: `/Users/kangsangmo/.claude/projects/-private-tmp-wu3a-final-v1-OVYFlY-repo/1f12994f-06d0-4be3-b3a1-5aac2b04b114.jsonl`
- 판정: `VERDICT PASS`, `WU3A_LOGIC PASS`, `CHECKPOINT_READINESS NOT_RUN`, `OVERALL_T NOT_RUN`
- 후보 해시: tree `2124a615104a06a1f1ae43cc19e8252879a6945b`, diff `88c08534bd13e7e6e051daa8d8c545f81549effb9f9889fc58c9d92db9d3172f`

V1은 대문자 4개 결함/정상쌍, P11 양방향 미끼, fallback 500, 정규화 no-op, 정상 66개, mutation 6개와 고장 bundle 5종, 후보 staged 5개를 독립 실행했다. V1 본문은 harness가 session ID를 노출하지 않았다고 잘못 적었지만 CLI 최종 JSON과 raw JSONL 파일명에서 위 실제 session ID를 확인했다. 이 보고 오류는 로직 판정을 바꾸지 않는다.

V1의 비차단 관찰:

- 최초 62개 파일 사본과의 직접 tree diff는 그 객체가 격리 저장소에 없어 실행하지 못했다. 시작 시 62/62, 최종 66/66과 테스트 구성 집계를 근거로 보완했다.
- 중위 `.TEST.`/`TEST_`의 대소문자 무시는 이번 마지막 확장자 계약 밖의 알려진 한계다.
- validator 자체와 비밀 패턴 입력의 신뢰 기준점은 WU-3b가 맡는다.

## 새 Codex V2

- V2 ID: `/root/wu3a_v2_final`
- 판정: V1 핵심 주장 재현 `PASS`, `WU3A_LOGIC PASS`, `CHECKPOINT_READINESS NOT_RUN`, `OVERALL_T NOT_RUN`
- 후보 해시: tree `2124a615104a06a1f1ae43cc19e8252879a6945b`, diff `88c08534bd13e7e6e051daa8d8c545f81549effb9f9889fc58c9d92db9d3172f`

V2는 대문자 크기/약화 결함과 staged count 1 정상쌍, index P11 우선과 fallback 500, 66개/6개 스위트, 고장 bundle 5종의 각 exit 1, 후보 staged 5 gate exit 0, P11 600 이하, 비범위 staged diff 0을 다시 확인했다. 새 차단 결함이나 V1의 핵심 과장은 없었다. V1의 session ID 미노출 주장만 보고 오류로 반박했다.

## 아키텍처 판정과 WU-3b 잔여 책임

마지막 확장자를 공통 함수 한 곳에서 정규화하고, 원래 경로는 진단 출력에 보존하며, staged blob과 P11 정책 입력을 index에서 읽는 WU-3a 경계는 맞다. 세 판정 함수마다 대소문자 정규식을 복제하거나 전체 경로를 소문자로 바꾸는 대안보다 판정 드리프트와 경로 의미 변경이 작다.

그러나 이 순수 판정기는 아직 checkpoint가 아니다. WU-3b가 다음을 완료하고 실행하기 전까지 readiness와 overall T는 `NOT_RUN`이다.

- 승인된 후보 해시를 변경 대상 밖의 신뢰 영역에 고정한다.
- mutation validator를 gate보다 먼저 실행하고 정상 0, 고장 5종 각 1, 검사 대상 0개 아님을 강제한다.
- gate, scanner, validator, `verify.sh`, P11 SOT, `.secret-patterns.default`, `.secret-patterns`를 승인 SHA/index blob 또는 읽기 전용 배포 산출물로 보호한다.
- 보호 집합의 HEAD/index/worktree 불일치, 해시 불일치, runner 무출력을 fail-closed한다.
- 실제 hook/CI/checkpoint 경로에 연결하고 그 진입점을 검증한다.

중위 `.TEST.`/`TEST_`의 case-insensitive 확대는 WU-3b 신뢰 배선과 별개의 후속 판정 범위다. 현재 T에는 포함하지 않았으므로 WU-3a PASS를 막지 않지만, 정책상 필요하면 별도 WU로 계약과 회귀를 추가해야 한다.
