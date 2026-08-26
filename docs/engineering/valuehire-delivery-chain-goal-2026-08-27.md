# ValueHire v6 기본 개발 흐름 완결 goal — 2026-08-27

## 결론

현재 후보는 아직 전달할 수 없다. 검사 입력을 작업 폴더에서 바꿀 수 있고, 변경과 검증·원격 결과를 같은 대상으로 묶는 장부가 없기 때문이다.

이번 로컬 작업은 이 두 허점을 닫고 검증 가능한 커밋까지 만든다. 실제 원격 전달, 병합, 배포는 승인 전 실행하지 않으며 미실행 상태를 합격으로 바꾸지 않는다.

## 판단 근거

- `tools/strict/checkpoint-gate.mjs`는 `.strict/run-ledger/*.json`을 작업 폴더에서 전부 읽고 `updated_at`이 가장 큰 파일을 자동 선택한다.
- `verify.sh`는 기본 실행에서 작업 폴더의 `.secret-patterns.default`와 `.secret-patterns`를 합친다.
- 과거 WU-3a V1/V2 증거의 대상 tree는 현재 HEAD `472c276f8c18584719319f1665c73bed61257c1a`가 아니므로 현재 후보 합격증이 아니다.
- `docs/sot/coding-principles.md` P11 hard limit은 직접 작성 코드 파일 600 LOC다. 새 코드 파일과 수정 후 기존 파일 모두 이를 넘지 않는다.
- 저장소에는 `AGENTS.md`와 `CLAUDE.md`가 없었다. 사용자 메시지로 제공된 AGENTS 계약은 적용하되 저장소 직접 로드는 `NOT_RUN`으로 기록한다.

## 정본과 위험등급

- L3: 보안 검사, SOT, hook/CI, branch/worktree, 외부 PR/CI와 배포 상태를 함께 다룬다.
- 직접 읽은 정본: `docs/sot/coding-principles.md`, `docs/sot/principles.yaml`, `docs/sot/git-workflow.md`, `docs/sot/hook-contracts.md`, `docs/sot/verification-commands.md`, 두 engineering feature SOT.
- 기존 goal/evidence: `checkpoint-gate-goal-2026-08-24.md`, `checkpoint-gate-case-extension-evidence-2026-08-26.md`, `work-unit-process-adoption-2026-08-21.md`, `gate-integrity-codex-handoff-2026-08-25.md`.

## Issue 계약

- Issue ID: `LOCAL-VH-WU3B-20260827`
- 계약: `docs/engineering/valuehire-delivery-chain-issue-2026-08-27.md`
- branch: `task/wu3b-delivery-chain-20260827`
- worktree: `/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/wu3b-delivery-chain-20260827`
- base SHA: `472c276f8c18584719319f1665c73bed61257c1a`
- run ID: `strict-wu3b-20260827-472c276`

## T 계약

T는 Issue의 AC-1~AC-8, counter-AC, 저장소 P1~P24와 V-1~V-5, 이 문서의 WU 경계다. G는 구현 Codex, V1은 `env -u ANTHROPIC_API_KEY claude -p`, V2는 새 맥락 Codex다. 셋이 같은 대상 SHA에서 일치하지 않으면 PASS가 아니다.

### 보호 집합

- `verify.sh`
- `tools/strict/checkpoint-js-scan.mjs`
- `tools/strict/checkpoint-gate.mjs`
- `tests/checkpoint-gate-mutation.test.mjs` checkpoint mutation validator
- `docs/sot/coding-principles.md` P11 정본
- `.strict/run-ledger/<run-id>.json`
- `.secret-patterns.default`
- 선택적 `.secret-patterns`
- `scripts/verify/run-acceptance.sh`, `hooks/pre-push`, `.github/workflows/verify.yml`의 관련 runner와 실행 설정

보호 집합은 명시적 full commit SHA 또는 Git index blob에서 읽는다. 로컬 `.secret-patterns`가 존재하면 한 번 읽은 bytes의 승인 SHA-256이 일치해야 하며 원문은 보존하지 않는다.

## Harness 게이트

1. Gate 0~1: 현재 Git 기준선, 정본, Issue, WU scope를 고정한다.
2. Gate 2: 각 WU의 누락 동작을 별도 RED 테스트 커밋으로 남긴다.
3. Gate 3: 테스트를 바꾸지 않고 최소 구현으로 GREEN을 만든다.
4. Gate 3.5: CLI→trusted policy/secret/ledger/state validator의 실제 호출 경로를 실행한다.
5. Gate 4: 원명령, 정상/고장 fixture, hard 600/601, 대문자 경계, mutation, staged count를 기록한다.
6. Gate 5: 최신 candidate SHA에 V1/V2와 codeaudit를 연결하되 원격은 미실행으로 남긴다.
7. Gate 6: 사용자 merge 뒤에만 deploy/live evidence를 별도 기록한다. 이번 실행에서는 도달하지 않는다.

## WU 실행 계약

각 WU는 RED 테스트 커밋 → 최소 구현 → 정상/고장 fixture → 독립 반증 → 전체 출력 지문 기록 → WU 구현 커밋 순서를 지킨다. 테스트 기대를 구현 커밋에서 약화하지 않는다. WU 구현 커밋에는 `WU: <id>` trailer를 둔다.

## 검증 원명령

```text
node --test tests/checkpoint-gate.test.mjs
node --test tests/checkpoint-gate-mutation.test.mjs
node --check tools/strict/checkpoint-gate.mjs
node --check tools/strict/checkpoint-js-scan.mjs
bash scripts/acceptance-principles-check.sh
bash ~/.claude/skills/strict/brief-lint.sh docs/engineering/checkpoint-gate-goal-2026-08-24.md
git diff --check
```

→ 위 명령은 기존 gate·mutation·구문·원칙·문서·diff 계약의 원래 진입점이다. 모두 실제 실행하고 하나라도 비정상 종료하면 전체 후보를 합격으로 기록하지 않는다.

추가 acceptance와 새 테스트는 WU-3b-5에서 pre-push glob과 CI 고정 목록에 함께 연결한다. 실행 대상 0개와 무출력은 실패다.

WU-3b-6은 PR 본문과 변경 요약을 로컬에서 준비하되, `origin/main`과 후보 기반의 분기 상태 및 사용자 승인 경계를 문서와 테스트로 고정한다. base가 정리되지 않은 동안 PR 생성 명령은 `BLOCKED`다.

Codeaudit에서 secure `--run-id` 경로 밖의 legacy fallback이 작업 폴더 ledger를 계속 자동 선택하는 결함을 재현했다. WU-3b-1a는 이 fallback을 삭제해 `--run-id`가 없으면 명시적 `--scope`만 사용하고, 둘 다 없으면 staged 파일별 scope 위반으로 닫는다.

같은 감사에서 no-run-id secret 경로가 작업 폴더 `verify.sh`와 pattern을 직접 실행하는 우회도 재현했다. WU-3b-2a는 호출 모드와 무관하게 index의 `verify.sh`와 `.secret-patterns.default`, 승인 SHA가 일치하는 선택적 로컬 pattern만 사용한다.

실제 pre-push와 CI도 하위 `verify.sh`를 작업 폴더에서 직접 호출하고 있었으므로 WU-3b-2b에서 `tools/strict/trusted-secret-scan.mjs`를 공통 진입점으로 추가했다. pre-push는 clean-tree 확인 뒤 이 runner를 직접 실행하고, CI checkout은 event commit의 index blob만 scanner/default pattern 권한으로 사용한다.

WU-3b-2b 뒤 full strict에서 기존 격리 fixture가 새 policy/secret 모듈을 복사하지 않아 2건 실패했다. WU-3b-2c는 protected bundle을 실제 의존 집합과 맞추고, scanner 준비 실패를 빈 경로가 아니라 staged 대상에 귀속하며, 직접 작성 gate 테스트 정본을 hard 600 LOC에 맞췄다.

## 설계 결정

> **무엇을** — scope ledger는 명시적 run/WU ID와 index blob으로 고정한다.
> **왜** — 작업 폴더 최신 파일 자동 선택은 공격자가 검사 범위를 바꾸게 한다.
> **버린 길** — 최신 timestamp 자동 선택과 파일명 정렬 선택은 둘 다 decoy에 취약해 기각한다.
> **대가** — 호출자가 run/WU ID를 반드시 알아야 한다.
> **되돌리기** — gate와 ledger policy 커밋을 revert하면 과거 fallback 동작으로 돌아간다.

> **무엇을** — secret policy는 index blob과 승인 SHA가 일치하는 선택 입력만 합친다.
> **왜** — 작업 폴더 pattern 완화가 staged secret을 숨길 수 있다.
> **버린 길** — worktree와 index가 같다는 비교만 하는 방식은 둘을 함께 바꿀 수 있어 기각한다.
> **대가** — 로컬 전용 pattern을 쓰려면 SHA 승인 입력이 추가된다.
> **되돌리기** — trusted secret runner 변경을 revert하고 기존 `verify.sh` 호출로 복귀한다.

> **무엇을** — 과거 evidence는 full commit SHA와 blob SHA로 읽는 추적 장부에 연결한다.
> **왜** — 내부 hash chain만으로는 같은 작성자가 전체를 다시 계산할 수 있다.
> **버린 길** — 작업 폴더 JSON만 검증하는 방식을 기각한다.
> **대가** — 새 evidence를 인정하려면 새 승인 SHA가 필요하다.
> **되돌리기** — 추적 validator와 schema를 제거하되 기존 evidence commit은 삭제하지 않는다.

> **무엇을** — merge 전 readiness/overall T를 `NOT_RUN`으로 고정하고 deploy/live를 후속 단계로 분리한다.
> **왜** — 로컬 합격이 원격 CI, 사람 merge, 운영 결과를 대신할 수 없다.
> **버린 길** — 로컬 테스트 성공을 SHIP GREEN으로 승격하는 방식을 기각한다.
> **대가** — 로컬 작업을 모두 끝내도 최종 판정은 `REQUEST_CHANGES`다.
> **되돌리기** — 상태 validator를 revert하면 기존 수동 문서 판정으로 돌아가지만 오승격 방어도 사라진다.

## 롤백·영향 반경·데이터 안전

롤백과 데이터 안전 조건은 Issue 계약을 따른다. 영향은 repository assurance CLI, acceptance, hook/CI 설정과 문서뿐이며 제품 후보자 데이터나 운영 서비스에 쓰지 않는다.

## 적대 검증 로그

최신 candidate SHA가 확정된 뒤 V1 원문·session ID·명령·전체 출력 SHA와 V2 재현 표를 작업 branch 밖의 pinned evidence commit에 보존한다. 후보 SHA를 바꾸는 문서 후기록으로 순환시키지 않는다.

## 시작 장부

```text
TIME: 2026-08-26T17:45:29Z
SESSION: strict-wu3b-20260827
HEAD: 472c276f8c18584719319f1665c73bed61257c1a
BRANCH: rescue/main-mixed-20260825T200952
COMMAND: bash scripts/acceptance-principles-check.sh
EXIT: 0
VERDICT: PASS
MECHANISMS: PASS 34/34 strict-contract-bindings
WIRING: PASS pre-push=1 ci=1
CHECKED: 34
```

→ 원칙 정본과 기계 장부 자체는 통과했다. 다만 이 명령은 원본 작업폴더의 unstaged 수정 상태에서 실행됐으므로, 구현 후보의 최종 증거로 재사용하지 않고 격리 worktree에서 다시 실행한다.

## 현재 원격 상태

- PR: `NOT_RUN`
- CI: `NOT_RUN`
- Merge: `NOT_RUN`
- Deploy: `NOT_RUN`
- Live Verify: `NOT_RUN`
- checkpoint readiness: `NOT_RUN`
- overall T: `NOT_RUN`
