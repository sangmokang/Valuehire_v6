# P00A 소유권 계약 수리 목표 — 2026-08-18

## 결론

P00A가 만들라고 요구하는 세 산출물을 모두 자기 작업 범위에 넣고, 하나라도 빠지면 기획 묶음 검사가 합격하지 못하게 고친다. 실제 책임자 선택이나 제품 구현은 시작하지 않는다.

다른 실행문에서도 같은 누락 후보가 발견되면 이번 작업에 섞어 고치지 않고 목록과 근거만 남긴다. 수정한 문서와 검사만 다시 준비 영역에 올린 뒤, 그 준비 영역을 기준으로 모든 필수 검사를 통과할 때 멈춘다.

## 판단 근거

현재 P00A는 결정 기록 한 파일만 소유한다고 제한하면서, 아래에서는 별도 목표 문서와 자기 검사 파일을 만들라고 요구한다. 기존 기획 묶음 검사는 제목·파일 수·명령 문자열만 확인하고, 요구 산출물이 소유 범위 안에 있는지는 확인하지 않아 이 모순을 합격으로 처리한다.

이번 수리는 P00A의 소유 범위에 세 산출물의 정확한 경로를 쓰고, 기획 묶음 검사에서 그 세 경로가 반드시 `작업 소유 범위` 절 안에 있는지 확인하는 최소 변경으로 제한한다. 다른 프롬프트는 읽기 전용으로만 대조한다. 이 판단이 틀리면 다음 작업자가 소유하지 않은 파일을 만들거나, 만들지 못한 채 검사가 합격하는 문제가 다시 생긴다.

**무엇을** — P00A 소유 범위와 기획 묶음 검사 사이에 같은 세 산출물 목록을 둔다.

**왜** — 요구 목록과 소유 목록을 기계가 직접 대조해야 기존 가짜 합격을 막을 수 있기 때문이다.

**버린 길** — 28개 프롬프트를 한꺼번에 고치는 방법은 버린다. 이번에 확정된 결함은 P00A 하나이고, 나머지는 별도 판단과 작업 분리가 필요하다.

**대가** — 검사 안에 P00A 산출물 경로가 명시되어 경로를 바꾸면 계약과 검사를 함께 갱신해야 한다.

**되돌리기** — 이번 두 계약 변경과 이 목표 문서를 준비 영역에서 제외하면 원상 복구된다. 단, 그러면 소유권 누락을 잡지 못하는 기존 가짜 합격도 되살아난다.

## 현재 상태와 근본 원인

- `docs/engineering/goal-prompts/ai-native-ra-search-orchestration/p00a-data-ownership-owner-decision.md:15`는 결정 기록 한 파일만 소유한다고 제한한다. 이 줄이 별도 목표 문서와 자기 검사 파일 요구를 소유 범위 밖으로 밀어낸다.
- 같은 파일의 `원자적 인수 기준`은 `scripts/acceptance-ai-ra-p00a.sh` 생성을 요구하고, `공통 strict 실행 지시` 2번은 이번 프로젝트 목표 문서 생성을 요구한다.
- `docs/engineering/ai-native-ra-search-orchestration-goal-2026-08-17.md`의 `AC-PLAN-1`은 28개 파일·11개 절·자기 명령 문자열을 확인하지만, `작업 소유 범위` 절 안의 산출물 목록은 확인하지 않는다.
- 작업은 이미 `task/ai-ra-orchestration-plan` 별도 작업공간에 격리되어 있고, 기본 작업공간의 `main`은 수정하지 않는다.

→ 문서 대조로 확정한 원인은 “요구 산출물과 소유 산출물을 같은 검사에서 비교하지 않음”이다. 제품 코드나 실제 오너 결정은 원인이 아니며 이번 작업 대상도 아니다.

## 원자적 인수 기준

### AC-P00A-OWNERSHIP-1

P00A의 `작업 소유 범위` 절이 아래 세 산출물을 모두 소유하고, `AC-PLAN-1`이 세 산출물 중 하나라도 그 절에서 빠진 임시 사본을 불합격시켜야 한다.

1. `docs/engineering/ai-ra-data-ownership-decision-<date>.md` — 오너 결정 기록
2. `docs/engineering/ai-ra-data-ownership-owner-decision-goal-<date>.md` — 이번 프로젝트 목표 문서
3. `scripts/acceptance-ai-ra-p00a.sh` — P00A 자기 인수 검사

→ 합격은 정상 P00A에서 `AC-PLAN-1`이 0을 남기고, 세 번째 소유권 줄을 제거한 반대 사본에서 같은 검사가 0이 아닌 값을 남기는 두 결과가 함께 있어야 한다.

## RED 먼저

수정 전 `AC-PLAN-1`을 현재 준비 내용에 실행해 `PASS planning_packet ...`이 나오는지 확인한다. 이 합격은 문서에 모순이 남아 있는데도 나온 것이므로 기존 검사의 가짜 합격 증거다.

그다음 자기 검사 파일 소유권 문구가 없는 P00A 임시 사본을 같은 판정 함수에 넣어도 통과하는지 확인한다. 수리 후에는 이 반대 사본만 실패하고 원본은 통과해야 한다.

## 검증 계약

필수 검사는 아래 순서로 실행한다.

1. `git diff --cached --check`
2. 최신 준비 내용에서 `AC-PLAN-1`
3. P00A 자기 검사 파일 소유권을 제거한 임시 사본 반대 시험
4. `VERIFY_SCAN_SOURCE=index bash verify.sh`
5. `bash scripts/acceptance-hs-gates.sh`
6. `env -u ANTHROPIC_API_KEY claude -p` 읽기 전용 1차 적대검토
7. Claude가 든 모든 근거를 Codex가 같은 명령으로 재현하고, 빠진 반례를 다시 공격하는 2차 검토

→ 모든 필수 검사는 프로그램이 남기는 성적 0이어야 한다. 반대 시험만은 누락을 거부했음을 뜻하는 0이 아닌 값이 기대 결과다.

## 28개 프롬프트 읽기 전용 감사 범위

대상은 `docs/engineering/goal-prompts/ai-native-ra-search-orchestration/p*.md` 정확히 28개다. 각 파일에서 `작업 소유 범위`, `원자적 인수 기준`, `공통 strict 실행 지시`를 대조해 다음 두 유형을 센다.

1. 자기 번호 인수 검사 파일을 만들라고 요구하지만 소유 범위에 정확한 경로나 명백한 전용 검사 소유 문구가 없는 경우
2. 이번 프로젝트 목표 문서를 만들라고 요구하지만 소유 범위에 목표 문서가 없는 경우

→ P00A 외 사례는 이번 변경에 포함하지 않는다. 파일명, 요구 근거, 소유 범위 근거, 확정 또는 해석 필요 여부만 이 문서의 감사 결과에 기록한다.

## Harness 진행

- 게이트 0: 이 작업은 새 제품 작업이 아니라 현재 기획 묶음의 확정 차단 결함을 닫는 작업이다. `scripts/session-status.sh`의 전체 검사는 실행 시간이 길어 진행 중 상태가 발생했으므로 원인을 분해하고 원명령을 다시 실행한다.
- 게이트 1: 인수 기준은 `AC-P00A-OWNERSHIP-1` 하나다.
- 게이트 2: 기존 `task/ai-ra-orchestration-plan` 별도 작업공간만 사용한다.
- 게이트 3: 기존 가짜 합격과 소유권 누락 반대 시험을 먼저 고정한 뒤 최소 변경한다.
- 게이트 4: 위 검증 계약의 모든 로컬 명령을 최신 준비 내용에서 실행한다.
- 게이트 5·6: 사용자가 커밋·업로드·검토 요청·병합을 명시적으로 금지했으므로 이번 목표 시작 전에 비범위로 확정한다.

## 정본 체크리스트

- [x] `docs/sot/INDEX.md` — 정본과 사건 기록의 경계를 확인했다.
- [x] `docs/sot/coding-principles.md` — 실행 가능한 인수 기준, 조용한 합격 금지, 검사 약화 금지, 검사 0건 합격 금지를 확인했다.
- [x] `docs/sot/git-workflow.md` — 기본 작업공간 보호와 작업 1개당 별도 작업공간 원칙을 확인했다.
- [x] `docs/sot/verification-commands.md` — 이 저장소는 make/npm 기반이 아니며 실제 검증 명령이 `bash verify.sh`와 인수 스크립트임을 확인했다.
- [x] 사용자 제공 `AGENTS.md` — 최소 변경, 증거 우선, 최신 준비 내용 검증, 커밋 금지를 확인했다.

## 적대 검증 항목

- 소유권 경로가 P00A의 다른 절에만 있어도 검사가 잘못 통과하지 않는가.
- `작업 소유 범위` 절 제목만 있고 세 파일 중 하나가 빠지면 실제로 실패하는가.
- 준비 영역이 아닌 오래된 작업 파일을 검증해 가짜 합격하지 않는가.
- 28개 감사가 파일 0개 또는 일부만 읽고 전수감사라고 과장하지 않는가.
- Claude 판정이 인용한 줄과 명령 출력이 최신 준비 내용에서 재현되는가.

## 비범위

- P00A 실제 오너 결정과 선택지 확정
- `humansearch/` 제품 코드, 데이터베이스, 후보 자료, 외부 서비스 변경
- 다른 27개 프롬프트의 소유권 계약 수정
- 기본 작업공간 `main` 수정
- 커밋, 업로드, 이력 재작성, 병합, 파일 삭제
- 공용 서버 검사 연결과 실제 라이브 실행

→ 이번 작업은 문서 계약과 그 계약을 검사하는 로컬 인수 기준만 다룬다. 제품 배선과 라이브 증거는 사용자 금지 범위이므로 시작 전에 제외되었고, 이 제외를 제품 완료 주장으로 바꾸지 않는다.

## 증거 원문

### 수정 전 가짜 합격

실행 명령:

```bash
sed -n '111,138p' docs/engineering/ai-native-ra-search-orchestration-goal-2026-08-17.md | bash
printf 'ac_plan_1_rc=%s\n' "$?"
```

→ 수정 전 문서에 들어 있던 기획 묶음 검사를 그대로 실행하고 프로그램 성적을 함께 출력하는 명령이다.

실행 출력:

```text
PASS planning_packet goal=1 plan=1 prompts=28 required_sections=11 atomic_commands=28 links=all-present
ac_plan_1_rc=0
```

→ 수정 전 P00A가 결정 기록 한 파일만 소유한다고 제한한 상태에서도 기획 묶음 검사가 합격했다. 이것이 이번 작업이 막아야 하는 기존 가짜 합격이다.

### 반대 시험 1차 실패와 복구

첫 시도 출력:

```text
PASS planning_packet goal=1 plan=1 prompts=28 required_sections=11 atomic_commands=28 p00a_owned_artifacts=3 links=all-present
normal_rc=0
COUNTER_P00A_SCRIPT_OWNERSHIP_REMOVED
counter_rc=0 expected_nonzero=yes
```

→ 임시 파일 경로가 하위 셸까지 안정적으로 전달되지 않아 반대 입력 대신 실제 문서를 읽었다. 반대 시험이 합격해 전체 묶음 명령은 성적 1로 끝났고, 이 시점에는 수리를 완료로 보지 않았다.

두 번째 시도 출력:

```text
COUNTER_P00A_SCRIPT_OWNERSHIP_REMOVED
counter_rc=1 expected_nonzero=yes
NORMAL_AC_PLAN_1
PASS planning_packet goal=1 plan=1 prompts=28 required_sections=11 atomic_commands=28 p00a_owned_artifacts=3 links=all-present
normal_rc=0
```

→ 소유 범위 본문을 메모리 안 임시 사본으로 전달하자 누락 입력은 성적 1, 정상 입력은 0이 나왔다. 다만 환경값으로 검사 입력을 바꾸는 입구 자체가 우회가 될 수 있어 최종안에서는 제거했고, 최신 준비 내용 전체를 임시 폴더로 복제하는 시험으로 다시 증명한다.

### 28개 프롬프트 읽기 전용 감사 결과

[높음] P00A를 제외한 27개 프롬프트는 모두 “이번 프로젝트 목표 문서를 작성”하라고 요구하지만, `작업 소유 범위` 절에는 그 목표 문서의 소유권을 명시하지 않는다. 대상은 `p00`, `p01`부터 `p26`까지이며 `p00a`만 이번 수리로 명시됐다.

[높음] `p01`과 `p03`부터 `p26`까지 25개는 자기 번호 인수 검사 파일의 정확한 경로를 요구하지만, 소유 범위에는 정확한 경로도 전용 검사 소유 표현도 없다. 특히 `p04`는 공용 검사와 `acceptance-ai-ra-foundation.sh`를 소유한다고 쓰면서 정작 자기가 요구하는 `acceptance-ai-ra-p04.sh`는 소유하지 않는다.

[해석 필요] `p00`과 `p02`는 각각 “전용 문서 인수 스크립트”, “전용 인수 검사”를 소유한다고 써 자기 번호 파일까지 포함한다고 읽을 여지가 있다. 그러나 요구 절의 정확한 파일 경로와 소유 절의 표현이 일치하지 않아 별도 계약 수리가 필요한 후보로 남긴다.

이번 작업에서는 위 27개 파일을 수정하지 않았다.

실행 명령:

```bash
bash -s <<'BASH'
set -euo pipefail
prompt_dir=docs/engineering/goal-prompts/ai-native-ra-search-orchestration
prompt_count=0
goal_missing_count=0
script_exact_missing_count=0
script_generic_count=0
printf 'file\tgoal_required\tgoal_owned\tscript_required\tscript_exact_owned\tscript_generic_owned\n'
for prompt_file in "$prompt_dir"/p*.md; do
  prompt_count=$((prompt_count + 1))
  prompt_id=$(basename "$prompt_file" | sed 's/-.*//')
  script_path="scripts/acceptance-ai-ra-${prompt_id}.sh"
  ownership_section=$(awk '
    /^## 작업 소유 범위$/ { in_scope=1; next }
    /^## / && in_scope { exit }
    in_scope { print }
  ' "$prompt_file")
  goal_required=no; goal_owned=no; script_required=no
  script_exact_owned=no; script_generic_owned=no
  if rg -F '코드보다 먼저 이 프로젝트 목표 문서를 작성' "$prompt_file" >/dev/null; then goal_required=yes; fi
  if printf '%s\n' "$ownership_section" | rg -e '소유.*목표 문서|목표 문서.*소유|ai-ra-.*-goal-<date>\.md' >/dev/null; then goal_owned=yes; fi
  if rg -F "bash $script_path" "$prompt_file" >/dev/null; then script_required=yes; fi
  if printf '%s\n' "$ownership_section" | rg -F "$script_path" >/dev/null; then script_exact_owned=yes; fi
  if printf '%s\n' "$ownership_section" | rg -e '전용.*인수 (스크립트|검사)' >/dev/null; then script_generic_owned=yes; fi
  if [ "$goal_required" = yes ] && [ "$goal_owned" = no ]; then goal_missing_count=$((goal_missing_count + 1)); fi
  if [ "$script_required" = yes ] && [ "$script_exact_owned" = no ]; then script_exact_missing_count=$((script_exact_missing_count + 1)); fi
  if [ "$script_exact_owned" = no ] && [ "$script_generic_owned" = yes ]; then script_generic_count=$((script_generic_count + 1)); fi
  printf '%s\t%s\t%s\t%s\t%s\t%s\n' "$(basename "$prompt_file")" "$goal_required" "$goal_owned" "$script_required" "$script_exact_owned" "$script_generic_owned"
done
printf 'SUMMARY prompts=%s goal_required_but_not_owned=%s script_exact_required_but_not_owned=%s script_generic_wording_requires_interpretation=%s\n' "$prompt_count" "$goal_missing_count" "$script_exact_missing_count" "$script_generic_count"
[ "$prompt_count" -eq 28 ]
BASH
```

→ 28개 프롬프트의 요구 절과 소유 절을 같은 규칙으로 읽어 파일별 결과와 합계 네 개를 출력하는 전수 대조 명령이다.

실행 출력:

```text
file	goal_required	goal_owned	script_required	script_exact_owned	script_generic_owned
p00-data-ownership-sot.md	yes	no	yes	no	yes
p00a-data-ownership-owner-decision.md	yes	yes	yes	yes	no
p01-candidate-data-governance.md	yes	no	yes	no	no
p02-channel-policy-registry.md	yes	no	yes	no	yes
p03-position-spec-readiness.md	yes	no	yes	no	no
p04-ai-ra-foundation-gate.md	yes	no	yes	no	no
p05-clickup-read-snapshot.md	yes	no	yes	no	no
p06-position-priority.md	yes	no	yes	no	no
p07-search-gap-engine.md	yes	no	yes	no	no
p08-work-proposal-generator.md	yes	no	yes	no	no
p09-supabase-candidate-inventory.md	yes	no	yes	no	no
p10-sqlite-candidate-inventory.md	yes	no	yes	no	no
p11-gmail-attachment-catalog.md	yes	no	yes	no	no
p12-candidate-identity-resolution.md	yes	no	yes	no	no
p13-deterministic-internal-match.md	yes	no	yes	no	no
p14-contact-dedupe-ledger.md	yes	no	yes	no	no
p15-machine-registry.md	yes	no	yes	no	no
p16-machine-heartbeat.md	yes	no	yes	no	no
p17-durable-work-queue.md	yes	no	yes	no	no
p18-channel-account-lease.md	yes	no	yes	no	no
p19-fleet-scheduler-recovery.md	yes	no	yes	no	no
p20-aside-local-discovery.md	yes	no	yes	no	no
p21-human-intervention-guard.md	yes	no	yes	no	no
p22-saramin-one-candidate.md	yes	no	yes	no	no
p23-jobkorea-one-candidate.md	yes	no	yes	no	no
p24-linkedin-manual-packet.md	yes	no	yes	no	no
p25-operator-review-queue.md	yes	no	yes	no	no
p26-shadow-loop-chaos.md	yes	no	yes	no	no
SUMMARY prompts=28 goal_required_but_not_owned=27 script_exact_required_but_not_owned=27 script_generic_wording_requires_interpretation=2
```

→ 28개를 모두 읽었고 검사 자체 성적은 0이다. 추가 누락 후보는 이번 P00A 수리에 섞지 않고 위 목록으로만 고정했다.

최신 준비 내용 검증, 최종 반대 시험, 저장소 검사, Claude 원문과 Codex 재현은 아래 적대 검증 로그까지 작업 중 계속 덧붙인다.

## 적대 검증 로그

### Claude safe-mode V1

실행자: Claude Code `sonnet`, `--safe-mode`, 쓰기 도구 없음, 2026-08-18.

판정 원문과 네 차례 실행·복구 장부는 `docs/engineering/ai-native-ra-p00a-ownership-contract-repair-claude-v1-2026-08-18.md`에 100% 보존했다.

고정값:

- `VERDICT: PASS`
- 결함 총 개수: 0
- 심각도 있는 결함: 0
- 직접 실행하지 못했다고 밝힌 항목: 정상·반대 시험, 저장소 검사, 28개 전수 대조 명령

→ 첫 요청은 안전 필터 오탐, 두 번째는 무출력 대기, 세 번째는 형식 위반이 있었고 네 번째 판정에서 결함 0개를 다시 받았다. 형식 재요청도 첫 줄 앞 안내문을 붙인 위반이 남아 원문은 그대로 보존하고 이 문서에서 쉬운 말로 해석한다.

### Codex V2 — Claude 판정 직접 재현

실행 명령:

```bash
git show :docs/engineering/goal-prompts/ai-native-ra-search-orchestration/p00a-data-ownership-owner-decision.md | awk '
  /^## 작업 소유 범위$/ { in_scope=1; next }
  /^## / && in_scope { exit }
  in_scope { print }
'

set +e
git show :docs/engineering/ai-native-ra-search-orchestration-goal-2026-08-17.md | rg 'P00A_OWNERSHIP_(FILE|TEXT)'
override_rg_rc=$?
set -e

awk '
  /^### AC-PLAN-1/ { in_ac=1 }
  in_ac && /^```bash$/ { capture=1; next }
  capture && /^```$/ { exit }
  capture { print }
' docs/engineering/ai-native-ra-search-orchestration-goal-2026-08-17.md | bash

set +e
git diff --no-index -- \
  docs/engineering/goal-prompts/ai-native-ra-search-orchestration/p00a-data-ownership-owner-decision.md \
  /private/tmp/valuehire-p00a-index.Z3RgjX/docs/engineering/goal-prompts/ai-native-ra-search-orchestration/p00a-data-ownership-owner-decision.md
counter_diff_rc=$?
(
  cd /private/tmp/valuehire-p00a-index.Z3RgjX
  awk '
    /^### AC-PLAN-1/ { in_ac=1 }
    in_ac && /^```bash$/ { capture=1; next }
    capture && /^```$/ { exit }
    capture { print }
  ' docs/engineering/ai-native-ra-search-orchestration-goal-2026-08-17.md | bash
)
counter_ac_rc=$?
set -e
```

→ 최신 준비 내용의 세 산출물·우회 입구·정상 검사와, 한 줄만 제거한 반대 사본의 정확한 차이·실패를 한 번에 재현하는 명령이다.

실행 출력:

```text
V2_THREE_OWNED_ARTIFACTS

P00A는 아래 세 산출물만 소유한다.

1. `docs/engineering/ai-ra-data-ownership-decision-<date>.md` — 선택지·근거·오너 결정 기록
2. `docs/engineering/ai-ra-data-ownership-owner-decision-goal-<date>.md` — 이번 프로젝트 목표 문서
3. `scripts/acceptance-ai-ra-p00a.sh` — P00A 자기 인수 검사

경로가 현재 SOT와 충돌하면 임의로 다른 영역까지 고치지 말고 목표 문서에 충돌을 증거와 함께 기록해 이 프로젝트를 중단한다.

V2_NO_OWNERSHIP_OVERRIDE_SEAM
override_rg_rc=1 expected_no_match_1=yes
V2_NORMAL_AC_FROM_CURRENT_INDEX_CONTENT
PASS planning_packet goal=1 plan=1 prompts=28 required_sections=11 atomic_commands=28 p00a_owned_artifacts=3 links=all-present
normal_ac_rc=0
V2_COUNTER_DIFF_ONLY_ONE_OWNERSHIP_LINE
diff --git a/docs/engineering/goal-prompts/ai-native-ra-search-orchestration/p00a-data-ownership-owner-decision.md b/private/tmp/valuehire-p00a-index.Z3RgjX/docs/engineering/goal-prompts/ai-native-ra-search-orchestration/p00a-data-ownership-owner-decision.md
index 508c8cc..567a348 100644
--- a/docs/engineering/goal-prompts/ai-native-ra-search-orchestration/p00a-data-ownership-owner-decision.md
+++ b/private/tmp/valuehire-p00a-index.Z3RgjX/docs/engineering/goal-prompts/ai-native-ra-search-orchestration/p00a-data-ownership-owner-decision.md
@@ -16,7 +16,6 @@ P00A는 아래 세 산출물만 소유한다.

 1. `docs/engineering/ai-ra-data-ownership-decision-<date>.md` — 선택지·근거·오너 결정 기록
 2. `docs/engineering/ai-ra-data-ownership-owner-decision-goal-<date>.md` — 이번 프로젝트 목표 문서
-3. `scripts/acceptance-ai-ra-p00a.sh` — P00A 자기 인수 검사

 경로가 현재 SOT와 충돌하면 임의로 다른 영역까지 고치지 말고 목표 문서에 충돌을 증거와 함께 기록해 이 프로젝트를 중단한다.

counter_diff_rc=1 expected_difference_1=yes
V2_COUNTER_AC
counter_ac_rc=1 expected_nonzero=yes
V2_SCOPE_STATUS
task/ai-ra-orchestration-plan
v2_core_reproduction=PASS
```

→ 세 산출물은 최신 준비 내용에 모두 있고, 시험용 우회 문구 검색은 일치 0건을 뜻하는 성적 1이었다. 정상 검사는 0, 정확히 한 소유권 줄만 뺀 반대 사본은 1이므로 Claude의 핵심 PASS 근거를 직접 재현했다.

### Codex V2 — Claude 메모 재공격

Claude는 “작업 소유 범위 제목에 오타가 나면 검사가 조용히 무력화될 수 있다”고 낮은 위험 메모를 남겼다. 최신 준비 내용 전체를 새 임시 폴더에 복제하고 그 제목만 바꿔 같은 검사를 실행했다.

실행 출력:

```text
diff --git a/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/ai-ra-orchestration-plan/docs/engineering/goal-prompts/ai-native-ra-search-orchestration/p00a-data-ownership-owner-decision.md b/docs/engineering/goal-prompts/ai-native-ra-search-orchestration/p00a-data-ownership-owner-decision.md
index 508c8cc..a89c6b1 100644
--- a/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/ai-ra-orchestration-plan/docs/engineering/goal-prompts/ai-native-ra-search-orchestration/p00a-data-ownership-owner-decision.md
+++ b/docs/engineering/goal-prompts/ai-native-ra-search-orchestration/p00a-data-ownership-owner-decision.md
@@ -10,7 +10,7 @@ ClickUp·승인된 `position_policy`·공유 제어 장부·후보 보호 장부

 없음. 다만 오너 답변 없이 선택을 추정하거나 SOT를 바꾸지 않는다.

-## 작업 소유 범위
+## 작업 소유 범위 오타

 P00A는 아래 세 산출물만 소유한다.

heading_diff_rc=1 expected_difference_1=yes
heading_ac_rc=1 expected_nonzero=yes
```

→ 제목 한 줄만 달라졌고 같은 검사는 성적 1로 거부했다. 따라서 “조용히 무력화된다”는 Claude 메모는 틀렸고, 실제 동작은 안전하게 불합격시키는 쪽이다.

### V1 ↔ V2 대조표

| Claude 주장 | Codex 직접 재현 | 최종 판단 |
|---|---|---|
| 세 산출물이 소유 범위 안에 있다 | 준비 내용에서 세 경로 전부 출력 | 일치 |
| 소유 범위 밖 문자열로 통과하지 않는다 | 해당 절만 자른 뒤 검사하고 한 줄 삭제 사본은 성적 1 | 일치 |
| 시험용 우회 입구가 없다 | 우회 변수 이름 일치 0건 | 일치 |
| 28개 감사 수치는 맞다 | 별도 읽기 전용 전수 명령에서 28·27·27·2 재현 | 일치 |
| 제목 오타가 검사를 조용히 무력화할 수 있다 | 제목만 바꾼 사본이 성적 1 | 불일치, Claude 메모 기각 |
| 28개 감사 결과 자체가 절 경계를 증명한다 | 두 검사는 별도이며 절 경계는 AC 원문과 반대 시험이 증명 | 근거 연결 과장, 결론 영향 없음 |

→ 표는 Claude의 핵심 합격 근거 4개가 직접 재현됐고, Claude의 과장·오류 2개는 최종 근거에서 제외됐음을 보여준다.

정정 수치:

- Claude가 잡아준 Codex 과장: 0건
- Codex가 Claude 판정에서 잡은 과장·오류: 2건
- 두 엔진이 합의한 실행 차단 결함: 0건
