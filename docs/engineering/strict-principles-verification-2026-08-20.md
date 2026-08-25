# Strict 원칙 계약 최종 검증 — 2026-08-20

## 1. 결론

**연결됨.** 현재 작업트리에서 코딩 원칙 정본·기계 장부·Strict 직접 로드·원칙 검사기·pre-push·CI·mechanism registry가 하나의 fail-closed 실행 계약으로 연결됐다. 실제 Claude CLI V1과 새 맥락 Codex V2도 최종 PASS했다.

이 결론은 “32개 제품 원칙의 모든 제품 기능이 구현됐다”가 아니라 “32개 원칙의 현재 정본과 Strict 실행 배선이 빠짐없이 직접 로드·기계 검증된다”는 뜻이다.

## 2. 변경 파일

정본·장부:

- `docs/sot/coding-principles.md`
- `docs/sot/principles.yaml`
- `docs/sot/mechanism-registry.yaml`
- `docs/sot/verification-commands.md`

검사·배선:

- `scripts/acceptance-principles-check.sh`
- `scripts/acceptance-principles-mutations.sh`
- `scripts/verify/check-pre-push-runtime.sh`
- `scripts/verify/check-mechanism-registry.sh`
- `scripts/acceptance-verify-ac-m.sh`
- `scripts/verify/check-strict-principles-skills.sh`
- `scripts/verify/check-strict-verdict-ledger.sh`
- `scripts/guard-global-skill-files.sh`
- `scripts/acceptance-guard-global-skill-files.sh`
- `scripts/verify/fixtures/mechanism-registry/{comment-only,echo-only,dead-code,if-false,fingerprint,path-fingerprint}-hook.sh`
- `scripts/verify/fixtures/strict-principles/*`
- `hooks/pre-push`
- `.github/workflows/verify.yml`

Strict 계약:

- `/Users/kangsangmo/.codex/skills/strict/SKILL.md`
- `/Users/kangsangmo/.claude/skills/strict/SKILL.md`

goal·검증:

- `docs/engineering/strict-principles-contract-goal-2026-08-20.md`
- `docs/engineering/strict-principles-g-evidence-2026-08-20.md`
- `docs/engineering/strict-principles-v1-{prompt,recheck-prompt,verdict}-2026-08-20.md`
- `docs/engineering/strict-principles-v2-{prompt,verdict}-2026-08-20.md`
- `docs/engineering/strict-principles-verdict-2026-08-20.yaml`
- 이 문서

## 3. 실제 실행 흐름

```text
현재 저장소 입력
  → Strict가 coding-principles.md + principles.yaml 직접 로드
  → acceptance-principles-check.sh가 32개 ID·문구·mechanism·배선 검증
  → hooks/pre-push가 검사기를 정확한 명령으로 직접 호출
  → GitHub Actions verify job이 같은 명령을 무조건 실행
  → G Codex 구현·40개 mutation
  → 실제 Claude CLI V1 적대검증
  → 새 맥락 Codex V2 재현·재공격
  → verdict ledger가 G/V1/V2/T 모두 PASS일 때만 최종 PASS
```

## 4. 단계별 file:line

- 원칙 22개: `docs/sot/coding-principles.md:16`
- §1-B 5개: `docs/sot/coding-principles.md:45`
- V 5개: `docs/sot/coding-principles.md:55`
- Strict 직접 로드 계약: `docs/sot/coding-principles.md:63`
- 32개 장부 시작·필드 구조: `docs/sot/principles.yaml:4`
- 원칙 검사기 입력·runtime checker: `scripts/acceptance-principles-check.sh:33`
- 무작위 runtime probe: `scripts/verify/check-pre-push-runtime.sh:28`
- runtime marker·종료값·출력 3중 증명: `scripts/verify/check-pre-push-runtime.sh:72`
- pre-push 명시 호출: `hooks/pre-push:47`
- CI 무조건 실행: `.github/workflows/verify.yml:28`
- registry local/pre-push/CI: `docs/sot/mechanism-registry.yaml:25`
- registry의 실제 runtime 검증: `scripts/verify/check-mechanism-registry.sh:133`
- registry 필수 3항목 강제: `scripts/verify/check-mechanism-registry.sh:254`
- mutation의 Git·경로 지문 공격: `scripts/acceptance-principles-mutations.sh:149`
- registry fixture 수 하한: `scripts/acceptance-verify-ac-m.sh:27`
- Codex/Claude 공통 블록 대칭성: `scripts/verify/check-strict-principles-skills.sh:23`
- Codex 공통 계약: `/Users/kangsangmo/.codex/skills/strict/SKILL.md:12`
- Claude 공통 계약: `/Users/kangsangmo/.claude/skills/strict/SKILL.md:12`

## 5. 실행 명령과 결과

```text
bash scripts/acceptance-principles-check.sh
exit 0
VERDICT: PASS
SOT_LOAD: PASS docs/sot/coding-principles.md
LEDGER_LOAD: PASS docs/sot/principles.yaml
MECHANISMS: PASS 32/32 strict-contract-bindings
WIRING: PASS pre-push=1 ci=1
CHECKED: 32
```

```text
bash scripts/acceptance-principles-mutations.sh
exit 0
CHECKED: 40
VERDICT: PASS
```

```text
bash scripts/verify/check-mechanism-registry.sh
exit 0
CHECKED: 6

bash scripts/acceptance-verify-ac-m.sh
exit 0
CHECKED: 31
```

```text
bash scripts/verify/check-strict-principles-skills.sh
exit 0
VERDICT: PASS
COMMON_CONTRACT: PASS byte-identical
ENGINE_ORDER: PASS Codex/Claude platform-only difference
LINES: codex=306 claude=306
CHECKED: 2
```

```text
bash scripts/acceptance-guard-global-skill-files.sh
exit 0
CHECKED: 8

bash verify.sh
exit 0
PASS: no secret-pattern match in any tracked file, .env not tracked
```

현재 구현 전체를 임시 Git 저장소에 커밋한 뒤 실제 pre-push를 실행한 결과:

```text
pre-push: 검사 21개 실행
21개 모두 ok
ISOLATED_HEAD=6571e0ac11b8ba8f24197ecfa079da7a8ddbd6e8
ISOLATED_PRE_PUSH_EXIT=0
```

V1 실제 호출:

```text
env -u ANTHROPIC_API_KEY claude -p --resume fc479ae5-4368-47d5-91d1-65c0e75fde6e --output-format json --effort high --permission-mode dontAsk --allowedTools Read,Grep,Glob,Bash < docs/engineering/strict-principles-v1-recheck-prompt-2026-08-20.md
CLI exit 0
api_error_status null
final VERDICT: PASS
session fc479ae5-4368-47d5-91d1-65c0e75fde6e
```

V2:

```text
native verifier /root/strict_principles_v2_final_r2
V2_VERDICT: PASS
OVERALL_STRICT: PASS, with ledger finalization pending
V2_RECHECK after tracked secret-scan integration fix: PASS
```

V1 여섯 라운드의 전체 판정 출력과 호출 메타데이터는 `strict-principles-v1-verdict-2026-08-20.md`, V2 전체 출력은 `strict-principles-v2-verdict-2026-08-20.md`에 보존한다.

## 6. 반례별 결과

| # | 반례 | 기대 | 실제 |
|---:|---|---|---|
| 1 | `principles.yaml` 삭제 | FAIL | exit 1 |
| 2 | `coding-principles.md` 삭제 | FAIL | exit 1 |
| 3 | YAML 문법 오류 | FAIL | exit 1 |
| 4 | 원칙 ID 삭제 | FAIL | exit 1 |
| 5 | 중복 ID | FAIL | exit 1 |
| 6 | mechanism 경로 미존재 | FAIL | exit 1 |
| 7 | CI 실행 줄 삭제 | FAIL | exit 1 |
| 8 | 검사기 파일 삭제 | FAIL/NOT_RUN | 호출 127, suite FAIL |
| 9 | 검사 대상 0개 | FAIL | exit 1 |
| 10 | `|| true`·`continue-on-error` | FAIL | exit 1 |
| 11 | V1 FAIL을 최종 PASS | FAIL | exit 1 |
| 12 | V1 FAIL 뒤 V2 NOT_RUN | FAIL | exit 1 |
| 13 | Codex/Claude 계약 불일치 | FAIL | exit 1 |
| 14 | memory 없음·잘림 | 현재 SOT 직접 로드 PASS | exit 0 |
| 15 | 주석·echo·죽은 collector·`if false` | FAIL | 모두 exit 1 |
| 16 | 고정 Git 신원/커밋 지문 | FAIL | exit 1 |
| 17 | 고정 `pre-push-runtime.` 경로 지문 | FAIL | exit 1 |
| 18 | marker/output/exit 위조·실패 삼킴 | FAIL | V2 모두 exit 1 |
| 19 | 직접 작성 500/501줄 | PASS/FAIL | 경계 일치 |

전체 mutation: `CHECKED: 40`, registry fixture: `CHECKED: 31`.

## 7. Codex/Claude 대칭성

- 공통 `STRICT_PRINCIPLES_CONTRACT` 블록은 byte-identical이다.
- 두 판 모두 현재 저장소의 두 SOT를 직접 읽고 검사기를 실행하며 T와 goal 장부에 기록한다.
- 누락·FAIL·NOT_RUN이면 전체 PASS를 금지한다.
- memory는 보조 정보일 뿐 정본이 아니다.
- Codex: `G=Codex → V1=Claude → V2=Codex`
- Claude: `G=Claude → V1=Codex → V2=Claude`

결과: `COMMON_CONTRACT: PASS`, `ENGINE_ORDER: PASS`.

## 8. memory 의존성과 직접 SOT 로드

- `.omx/project-memory.json` 삭제 fixture: PASS.
- 잘린 memory fixture: PASS.
- 두 경우 모두 현재 저장소의 `coding-principles.md`와 `principles.yaml`을 직접 읽었다.
- memory 로드 성공을 SOT 로드 성공으로 계산하지 않는다.
- SOT 파일 자체가 삭제되거나 비면 FAIL한다.

## 9. 남은 FAIL/NOT_RUN

없음. 최종 기계 ledger 검사가 `ROLES: PASS G/V1/V2/T`와 exit 0을 재현해야 이 상태가 확정된다.

## 10. 롤백

1. 신규 장부·검사·fixture·검증 문서를 제거한다.
2. `hooks/pre-push`, `.github/workflows/verify.yml`, mechanism registry의 이번 호출·항목만 역패치한다.
3. 두 Strict에서 `STRICT_PRINCIPLES_CONTRACT` 블록을 제거한다.
4. 검사기를 제거하기 전에 pre-push와 CI 참조를 먼저 제거해 고아 호출을 남기지 않는다.
5. Git 이력에 아직 커밋하지 않았으므로 관련 diff만 역패치하면 된다. 다른 작업트리 변경은 건드리지 않는다.
