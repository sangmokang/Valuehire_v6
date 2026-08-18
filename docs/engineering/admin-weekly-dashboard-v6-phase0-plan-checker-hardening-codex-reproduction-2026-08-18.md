# Admin Weekly Dashboard v6 Phase 0 계획 검사기 Codex 독립 재현 — 2026-08-18

## 1층 — 결론

Claude의 유효 판정은 통과였지만 그대로는 틀렸습니다. Codex가 큰 결함 6개를 재현했고 모두 별도 실패 시험과 수정 커밋으로 막은 뒤 최종 32/32를 통과시켰습니다.

checker hardening 검증만 완료됐습니다. P0-01 실행, P0-02, 관리자 제품 구현은 허가되지 않았습니다.

## 2층 — Claude 대조

- 유효 Claude 판정: PASS
- Claude가 주장한 P0/P1: 0/0
- Codex가 재현한 Claude 누락: 6
- Claude 과장: 2
  - “13개 공격을 전부 실행했다”는 주장
  - “CI 우회 벡터가 전부 차단됐다”는 주장
- Claude P2 주장 재현: 1 (`\Z`가 false-fail을 만들 수 있음)
- 유효 본문 위치: `docs/engineering/admin-weekly-dashboard-v6-phase0-plan-checker-hardening-claude-audit-2026-08-18.md`

유효 Claude 이전에 무효 호출은 5회였습니다. safeguard 1회, 빈 출력·timeout 3회, 첫 줄 형식 위반 1회였습니다. health 호출 2회는 각각 `HEALTH_OK`, `HEALTH_SAFE_OK`였으며 감사 완료로 세지 않았습니다.

## 실제 false PASS 6건

| 번호 | 반례 | 수정 전 | RED | GREEN | 최종 지정 사유 |
| --- | --- | --- | --- | --- | --- |
| 1 | 이름 없는 마지막 step 뒤 job-level 인용 `'if'` | 26/26 PASS | `61bb92a` | `199d8eb` | `CI verify job must not contain if` |
| 2 | 후행 주석이 붙은 decoy job 경계 | direct validator PASS | `b4cb6b1` | `fbe6067` | `CI verify job must contain steps` |
| 3 | `BASH_ENV`에서 acceptance 전에 `exit 0` | 28/28 PASS, 실제 command 미실행 | `6d390ea` | `82ed4e6` | `CI workflow must not define BASH_ENV` |
| 4 | `pull_request` trigger 삭제 | 29/29 PASS | `786c153` | `8ce7bfb` | `CI workflow SHA-256 does not match the pinned checker workflow` |
| 5 | skip된 decoy를 `needs`로 연결 | 29/29 PASS | `786c153` | `8ce7bfb` | 같은 workflow SHA 사유 |
| 6 | custom shell이 즉시 `exit 0` | 29/29 PASS | `786c153` | `8ce7bfb` | 같은 workflow SHA 사유 |

→ 뭘 대조했나: Claude가 놓친 실행 우회 6개를 수정 전·RED·GREEN·최종 실패 사유로 연결했습니다.

→ 뭐가 나왔나: 여섯 반례 모두 수정 전에는 통과했고 최종에는 지정 사유로 실패합니다.

→ 좋은 소식인가 나쁜 소식인가: Claude 원판정에는 나쁜 소식이지만 최종 checker에는 좋은 소식입니다.

세 번째 공격의 로컬 실행 증거는 다음과 같습니다.

~~~text
BASH_ENV=scripts/short-circuit.sh bash -c 'echo SHOULD_NOT_RUN; bash scripts/acceptance-admin-phase0-plan.sh'
exit=0
stdout=0 bytes
~~~

→ 뭘 시켰나: Bash가 선언된 acceptance 명령을 실행하는지 확인했습니다.

→ 뭐가 나왔나: 시작 파일의 `exit 0` 때문에 본문과 sentinel이 전혀 실행되지 않았습니다.

→ 좋은 소식인가 나쁜 소식인가: 수정 전에는 CI 초록이 실제 검사 실행을 뜻하지 않아 나쁜 소식이었습니다. 최종 코드는 workflow 단독 변경 전체를 hash로 막습니다.

## 사용자 지정 독립 mutation 6개

| mutation | 최종 결과 | 핵심 증거 |
| --- | --- | --- |
| consumer와 dependency를 함께 다른 ID로 변경 | FAIL | missing 원 ID, unexpected 새 ID |
| blocker 목록과 사용 edge를 함께 제거 | FAIL | required blocker missing |
| CI command를 다른 job으로 옮기고 verify steps 제거 | FAIL | verify job must contain steps |
| 인용된 `if`를 첫 step key로 삽입 | FAIL | Phase 0 step must not contain if |
| baseline을 먼저 깨고 `|| true` 추가 | FAIL | mutationsCaught=0, mutationsRequired=0, structural FAIL |
| plan·graph·contract·contract hash를 함께 변경 | PASS | structural PASS, semanticAuditRequired=true, executionPermission=false |

→ 뭘 시켰나: 사용자께서 지정한 서로 다른 독립 mutation 6개를 기존 self-test와 별도로 실행했습니다.

→ 뭐가 나왔나: 다섯 개는 실패했고 동일 작성자 공격 하나만 구조 통과했으며, 의미 감사 필요와 실행 불허는 유지됐습니다.

→ 좋은 소식인가 나쁜 소식인가: 구조 검사의 fail-closed 범위는 확인됐지만 독립 승인 권한이 없다는 한계도 재확인됐습니다.

동일 작성자 공격은 최종 HEAD에서도 다시 실행했습니다. 새 contract hash `e792f4bf...`를 evaluator에 함께 넣으면 exit 0이었고 두 보수 flag는 그대로였습니다. 이것은 검사기 결함을 숨긴 것이 아니라 문서화한 권한 경계입니다.

## 3층 — 최종 수치와 이력

- 시작 HEAD: `4c75940e3d1f68d1a1e826d649e287142231cf3e`
- 기존 RED: `ed7c11e85f4c6703502ca1259686b9d6043f36b7`
- 기존 candidate: `276af11c30173412ea7f9b68e578224237a6e2aa`
- final code HEAD: `8ce7bfbc327be2790790ee335a5185725b25e9e4`
- base 이후 commit: 17개 = 기존 9개 + 신규 8개
- 신규 RED/GREEN: 4쌍
- 기존 mutation 보존: 26/26
- 신규 mutation: 6
- 최종 mutation: 32/32, 이름 중복 0
- phase0Rows: 26
- active: 135
- consumers: 135
- duplicateConsumers: 0
- unknownDependencies: 0
- dependencyCycles: 0
- blockersUnknown: 0
- structuralContract: PASS
- semanticAuditRequired: true
- executionPermission: false

변경한 code/contract 파일은 다음 3개입니다.

- `scripts/verify/check-admin-phase0-plan.mjs`
- `scripts/verify/admin-phase0-plan-structural-contract.mjs`
- `scripts/verify/fixtures/admin-phase0-plan-structural-contract.json`

금지 파일·관리자 제품 코드 변경은 0개입니다. 기존 커밋 amend/rebase/squash/reset은 0회입니다.

## 최종 검증

- Node syntax 2개: PASS
- Bash syntax 1개: PASS
- Phase 0 acceptance: PASS 32/32
- 독립 parser: 26/135/135, 중복·unknown·cycle·unknown blocker 0
- acceptance-verify-ac-m: PASS, CHECKED 25
- mechanism registry: PASS, CHECKED 4
- pre-push: PASS, 실행 18, 계약상 CI 담당 skip 3
- verify.sh: PASS
- data exposure: tracked 125, history blob 705, csv/tsv/sql 0, 위반 0
- 신규 diff-check: 0
- historical full-chain diff-check: 기존 trailing whitespace 7
- final code HEAD worktree: clean

## 남은 blocker

P0-01은 다음 3개가 따로 해결될 때까지 BLOCKED입니다.

1. runner-only audit evidence authority
2. historical full-chain diff-check blocker 7건
3. fresh semantic plan audit PASS

이 보고서는 3번을 대신하지 않습니다. 본 fresh codeaudit는 checker hardening 구현 감사이지 Phase 0 계획 의미 승인 문서가 아닙니다.
