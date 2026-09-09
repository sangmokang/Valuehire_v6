VERDICT: FAIL

# Codex V2 최종 판정 — HS-00.01 로컬 착수문서/검사 회수

## 결론

HS-00.01은 20:31:56Z에 지문 고정한 옛 로컬 후보 기준으로 최종 완료/PASS를 선언할 수 없다. 로컬 착수 문서와 baseline acceptance는 대부분 성립하지만, V1의 high 결함인 workflow 실행환경 우회가 독립 재현됐고, 현재 index에는 fixed worktree가 아니라 old 116-line `main()` staged blob이 남아 있었다.

이 판정은 HS-00.01 로컬 kickoff 문서/검사 게이트만 다룬다. 제품 검색, 포털 운영, remote CI, merge, HS-00.02~HS-00.04 부채 완료를 승인하지 않는다. ROOT가 이후 제품 수정과 브랜치 복구를 시작했으므로, 이 문서는 20:31:56Z 이전 후보에 대한 V2 판정으로만 읽어야 한다.

## 판단 근거

Codeaudit의 기존 PASS 문서는 제품 PASS가 아니라 HS-00.01 로컬 문서·검사 범위 PASS로 해석할 때만 타당하다. 해당 문서는 product delivery, portal, remote CI, HS-00.02~HS-00.04를 명시적으로 제외한다. 따라서 Codeaudit PASS를 제품/운영 완료로 확장하면 오판이다.

V1 최종 판정은 `VERDICT: FAIL`이고, V2는 V1 F1~F4를 독립 재현했다. F1은 HS-00.01의 CI wiring integrity 주장 자체를 깨므로 완료 차단 결함이다. F2는 V1 표현보다 범위를 줄여야 한다. worktree의 `scripts/verify/list-workflow-steps.py`는 함수 분리 상태였지만, staged blob은 여전히 `main()` 116줄이었다. 따라서 F2는 fixed worktree 결함이 아니라 현재 index를 그대로 commit하면 발생하는 pending-staging 위험이다.

600/601 hard-boundary 주장은 완료 증거가 부족하다. V2는 현재 파일/함수 크기가 hard limit 아래임을 재계산했지만, repository-owned reusable command가 실제로 600/601 경계값을 강제한다는 보존된 증거를 찾지 못했다. 기존 `hs0001-final-budget.log`에는 `PASS hard601 rejected` 주장이 있으나, 그 검사를 재실행 가능한 source-gated command로 확인하지 못했으므로 상태는 `UNRESOLVED`다.

회수 commit 전략은 `c6a94c7`에 기존 19커밋 회수 기준이 이미 있으면 별도 recovery commit을 만들지 않는 쪽이 낫다. 현재 패치와 prompt 파일을 artifact로 보존한 뒤 merge abort, `c6a94c7` 기준 새 branch, 필요한 untracked prompt input 복구, tests-only RED, 그 다음 함수분리와 F1 fix GREEN 순서가 더 작고 검토 가능하다. recovery commit을 만들 경우에도 GREEN이 아니라 unfinished/FAIL baseline checkpoint로만 명명해야 한다.

V1이 제안한 새 `acceptance-b` shell은 필수로 보지 않는다. 사용자의 제약상 기존 pytest 수집으로 충분하면 새 framework/surface를 만들 필요가 없다. 다만 pytest는 실제 parser/checker behavior를 호출해야 하고, 기존 CI/WU verification path에 수집되어야 하며, fix 전 RED 증거가 있어야 한다. standalone pytest 또는 실제 `list-workflow-steps.py` 동작을 실행하지 않는 test는 충분하지 않다.

## 기술 증거

- `artifacts/hs-next-20260910/v2-verdict.md` — 원본 V2 판정 보존본. SHA256 `6fe40b66c1de8780edee27f3759e3365684874c7bf32a6f439a3495e21c89f69`.
- `artifacts/hs-next-20260910/v2-evidence.log` — V2 baseline, 정상대조, always-allow, always-reject, verdict-section omission, weak-key omission, scope, budget-current 재현 로그. Source HEAD `06110d9355ae352da58e4ee7e4e2551962cda7d4`; SHA256 `c5a2545be136b49ca78cb12fd1b702f5a85cd698fb6ec39aa771621c8bb63f34`.
- `artifacts/hs-next-20260910/v2-f1-f4-evidence.log` — V1 F1~F4 집중 재현 로그. V1 artifact hash, source status before/after, mutation diff, command output, direct exit code를 보존했다. SHA256 `cd331ab4d0d108150d6f8372763b6bcbeb0f9013b70545c87da24119bda67f1b`.
- `artifacts/hs-next-20260910/v1-verdict.md` — V1 최종 원문. 첫 판정 `VERDICT: FAIL`; SHA256 `e894ba0a942c0a5f2161801fbc39e570d0cddca5ba6e4b7c25dd1060bbba5eeb`.
- `artifacts/hs-next-20260910/v1-cli.log` — V1 CLI stream. SHA256 `635e6d669cd142b0b180cb20629c382e98815d054889bae7b9bb7aa41a78c6f5`.
- `artifacts/hs-next-20260910/v2-reproduction.sh` — V2 재현 스크립트. Git 환경변수를 제거하고 fresh `mktemp` `v2-*` 경로를 사용했다. SHA256 `cb7f76a08475d3b500e1ed6d09185ef9c8dd08456737f0a890cc746379e5b026`.
- `artifacts/hs-next-20260910/v2-f1-f4.sh` — F1~F4 집중 재현 스크립트. Git 환경변수를 제거하고 fresh `mktemp` `v2-*` 경로를 사용했다. SHA256 `9a1ff99040311ef2dbb41e22dc039e4041bdc810e87c308ef11d834d12541642`.

## 발견 상태

- Codeaudit local-scope PASS 의미 — `REPRODUCED`. Codeaudit 문서는 HS-00.01 local docs/checks만 PASS로 보고, product delivery, portal, remote CI, HS-00.02~HS-00.04를 제외한다.
- Baseline acceptance and normal controls — `REPRODUCED`. V2는 source acceptance exit 0과 `CHECKED: 12`를 확인했다. PASS verdict fixture와 FAIL verdict fixture가 모두 exit 0인 것도 재현됐다. 이는 review content 보존이지 `VERDICT: FAIL`을 product PASS로 변환한 것이 아니다.
- Always-allow mutation — `REPRODUCED`. `failc`를 PASS 출력/무실패로 바꾸면 main acceptance가 verdict document 없이 통과하고, mutation suite는 여러 “변조가 통과했다” 실패와 함께 exit 1을 반환했다.
- Always-reject mutation — `REPRODUCED`. `pass`를 FAIL 출력/실패 설정으로 바꾸면 main acceptance가 exit 1이 되고 harmless positive controls도 실패했다.
- Verdict-section omission — `REPRODUCED`. verdict check를 unconditional `pass`로 대체하면 main acceptance가 verdict document 없이 exit 0이 되고, mutation 음성6이 이를 잡았다.
- Weak-key omission — `REPRODUCED`. `WEAK_KEYS = ()`로 비우면 mutation 음성2의 CI `continue-on-error` 변조가 통과하고 mutation suite가 exit 1을 반환했다.
- F1 high workflow execution environment bypass — `REPRODUCED`. `shell: bash -c "true" {0}`, top-level `defaults.run.shell: cat`, step `env.BASH_ENV` 삽입 모두에서 `acceptance-hs-kickoff.sh`와 `check-ci-step-integrity.sh`가 exit 0이었다. `shell`과 `BASH_ENV`의 local semantic probe는 intended acceptance script 없이 `step-exit=0`이 가능함을 보였다. 이는 HS-00.01 CI wiring integrity 완료를 차단한다.
- F2 high staged 116-line function — `REPRODUCED` with narrowed scope. V2 staged AST는 `STAGED [('fail', 3), ('main', 116)]`, worktree AST는 `WORKTREE [('fail', 3), ('main', 38), ('list_steps', 81)]`였다. 즉 현재 index commit 위험이지 fixed worktree 자체 결함으로 과장하면 안 된다.
- F3 low `PR #131` partial match — `REPRODUCED`. `PR #13`을 `PR #131`로 바꿔도 acceptance가 `PASS: 처분 PR #13`을 출력했다.
- F4 low verdict prefix and first-file selection — `REPRODUCED`. `VERDICT: PASSED`가 prefix regex 때문에 exit 0이었다. verdict file 두 개가 있으면 alphabetically first fixture가 선택되어 exit 0이었다. Empty verdict fixture는 direct run에서 exit 1로 올바르게 실패했다.
- V1 E6 grep-pipeline exit-code risk — `REPRODUCED` as reporting gap. grep으로 감싼 명령은 underlying acceptance 실패를 rc0처럼 보이게 할 수 있다. V2는 F4 empty verdict를 direct run으로 확인해 `RC[f4-empty-verdict-direct-acceptance]=1`을 기록했다.
- 600/601 hard-boundary proof — `UNRESOLVED`. 현재 크기 재계산은 했지만, repo-owned reusable checker가 hard 600/601 경계를 실제 강제한다는 재실행 가능한 증거가 없다.

## 미검증/잔여 공백

- Remote CI는 이 로컬 후보에 대해 실행하거나 검증하지 않았다.
- HS-00.03 homoglyph handling은 이 V2 범위에서 테스트하지 않았다.
- GitHub hosted runner에서 `defaults.run.shell: cat`이 실제로 어떤 런타임 효과를 내는지는 직접 증명하지 않았다. V2는 local parser/checker blind spot과 V1의 runner-behavior inference를 보존했다.
- latest main/origin은 PR70 이후 top-level `concurrency`, job `timeout-minutes`를 포함한다. V1 prototype allowlist는 최신 main schema를 수용해야 하며, old-base 성공은 latest-main compatibility proof가 아니다.

## 위험 및 다음 조건

- V2 시작 당시 worktree는 dirty 상태였다. V2는 source status와 hash를 보존했지만, 깨끗한 committed SHA 후보가 아니었다.
- `acceptance-hs-kickoff-mutations.sh`는 이미 593줄이므로 F1 mutation 세 개를 같은 파일에 추가하면 hard 600 초과 위험이 높다. 기존 pytest가 CI에 실제 수집된다면 그 경로를 쓰거나, shell mutation 파일을 분리해 `verification-commands.md`와 `verify.yml`에 명시적으로 wire해야 한다.
- GREEN proof에는 staged-blob AST 길이, baseline acceptance, mutation suite, 그리고 PR70 이후 최신 main 호환성이 포함되어야 한다.
