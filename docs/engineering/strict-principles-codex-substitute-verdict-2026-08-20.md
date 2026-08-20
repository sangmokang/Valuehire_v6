# Strict 원칙 Codex 대체 적대검증 — 2026-08-20

## 결론

Codex 대체 적대검증은 저장소 내부 계약에 대해 합격이다. 첫 독립 검증에서 판정 증거 해시를 실제 파일과 대조하지 않는 결함을 발견했고, 이를 고친 뒤 같은 검증자가 재공격해 합격했다. 다만 다른 모델 계열이 검증해야 한다는 원래 계약은 충족되지 않았다.

### 판정 코드

CODEX_SUBSTITUTE_VERDICT: PASS  
ORIGINAL_CROSS_MODEL_CONTRACT: NOT_SATISFIED  
독립 검증자: `/root/strict_principles_codex_substitute`

## 기준과 범위

- 기준 commit: `7bd3298695c93e0e60bdabd2500840da47c4db05`
- 현재 미커밋 작업트리의 SOT·장부·검사기·pre-push·CI·registry·두 전역 Strict를 직접 읽었다.
- 대체검증은 Claude 실행 사실을 사칭하지 않는다. 저장소 구현과 거짓 PASS 방어를 Codex가 대신 공격한 결과만 기록한다.

## 직접 SOT와 장부 대조

`bash scripts/acceptance-principles-check.sh` → exit `0`:

```text
VERDICT: PASS
SOT_LOAD: PASS docs/sot/coding-principles.md
LEDGER_LOAD: PASS docs/sot/principles.yaml
MECHANISMS: PASS 32/32 strict-contract-bindings
WIRING: PASS pre-push=1 ci=1
CHECKED: 32
```

→ 현재 저장소의 두 파일을 직접 읽었고 32개 ID·문구·Strict 배선을 확인했다.

별도 Ruby 대조 → exit `0`:

```text
INDEPENDENT_LEDGER_ENTRIES=32
INDEPENDENT_SOURCE_TITLES=32
INDEPENDENT_ERRORS=0
```

→ 주 검사기의 결과를 그대로 신뢰하지 않고 ID 집합·중복·문구·필드·path/check/stages를 독립 구현으로 다시 대조했다.

## 적대 fixture 전체 출력

`bash scripts/acceptance-principles-mutations.sh` → exit `0`:

```text
PASS: FIXTURE-NORMAL 정상 fixture — PASS (exit=0)
PASS: C1 principles.yaml 삭제 — FAIL (exit=1)
PASS: C2 coding-principles.md 삭제 — FAIL (exit=1)
PASS: C3 YAML 문법 오류 — FAIL (exit=1)
PASS: C3-EMPTY-LEDGER principles.yaml 빈 파일 — FAIL (exit=1)
PASS: C3-EMPTY-SOT coding-principles.md 빈 파일 — FAIL (exit=1)
PASS: C4 원칙 ID 하나 삭제 — FAIL (exit=1)
PASS: C5 중복 ID 추가 — FAIL (exit=1)
PASS: C5-UNKNOWN 알 수 없는 ID — FAIL (exit=1)
PASS: C5-PRINCIPLE 정본과 원칙 문구 불일치 — FAIL (exit=1)
PASS: C5-EMPTY-EXPECTED 빈 mechanism_expected — FAIL (exit=1)
PASS: C5-EMPTY-FOUND 빈 mechanism_found — FAIL (exit=1)
PASS: C6 mechanism 경로 미존재 — FAIL (exit=1)
PASS: C6-CHECK mechanism 검사기 미존재 — FAIL (exit=1)
PASS: C6-STAGES 잘못된 stages 구조 — FAIL (exit=1)
PASS: C6-SELF 검사기 자기 대상에서 제외 — FAIL (exit=1)
PASS: C7 CI 실행 줄 삭제 — FAIL (exit=1)
PASS: C8 검사기 파일 삭제 — FAIL (exit=127)
PASS: C9 검사 대상 0개가 되도록 글로브 변경 — FAIL (exit=1)
PASS: C10-A CI에 || true 삽입 — FAIL (exit=1)
PASS: C10-B CI에 continue-on-error 삽입 — FAIL (exit=1)
PASS: C10-C CI에 if exists 조건 삽입 — FAIL (exit=1)
PASS: C10-D CI 다중 줄 exit 0 우회 — FAIL (exit=1)
PASS: C10-E pre-push에 || true 삽입 — FAIL (exit=1)
PASS: C11 거짓 최종 판정 차단 — FAIL (exit=1)
PASS: C12 거짓 최종 판정 차단 — FAIL (exit=1)
PASS: C11-ARTIFACT-MISSING 증거 파일 누락 차단 — FAIL (exit=1)
PASS: C11-ARTIFACT-HASH 증거 해시 불일치 차단 — FAIL (exit=1)
PASS: C13 Codex/Claude 공통 계약 불일치 — FAIL (exit=1)
PASS: C14-A 메모리 파일 없음, 현재 SOT 직접 로드 — PASS (exit=0)
PASS: C14-B 메모리 파일 잘림, 현재 SOT 직접 로드 — PASS (exit=0)
PASS: BOUNDARY-500 직접 작성 코드 500줄 — PASS
PASS: BOUNDARY-501 직접 작성 코드 501줄 — FAIL
PASS: SOURCE-TREE 원본 저장소 상태 불변
CHECKED: 34
VERDICT: PASS
```

→ 필수 반례와 추가 공격 34건이 모두 기대 상태를 냈고 원본 작업트리를 오염시키지 않았다.

## 독립 검증이 찾은 결함과 수정

최초 독립 검증은 `scripts/verify/check-strict-verdict-ledger.sh`가 `artifact_hash`의 64자리 형식만 검사하고 실제 파일과 SHA를 대조하지 않는 결함을 발견했다.

수정 뒤 재검증:

```text
CODEX_SUBSTITUTE_RECHECK: PASS
ORIGINAL_CROSS_MODEL_CONTRACT: NOT_SATISFIED
missing artifact fixture: exit 1, ARTIFACT_MISSING
hash mismatch fixture: exit 1, ARTIFACT_HASH_MISMATCH
absolute artifact path fixture: exit 1, ARTIFACT_PATH_INVALID
valid verdict fixture: exit 0
full mutation suite: exit 0, CHECKED: 34, VERDICT: PASS
```

→ 장부는 이제 안전한 저장소 상대경로, 파일 실존·비심볼릭 링크, 실제 SHA-256 일치를 기계적으로 확인한다.

## 실행 배선

격리된 깨끗한 임시 저장소에서 `bash hooks/pre-push` → exit `0`:

```text
VERDICT: PASS
MECHANISMS: PASS 32/32 strict-contract-bindings
WIRING: PASS pre-push=1 ci=1
pre-push: 검사 21개 실행
ok ./scripts/acceptance-principles-check.sh
ok ./scripts/acceptance-principles-mutations.sh
ok ./scripts/acceptance-verify-ac-m.sh
ok ./verify.sh
ISOLATED_PRE_PUSH_EXIT=0
```

→ 현재 변경을 커밋한 것과 같은 깨끗한 snapshot에서 명시적 원칙 검사와 acceptance 글로브가 모두 실제 실행됐다. 임시 저장소는 검증 후 휴지통으로 이동했다.

추가 결과:

- mechanism registry: exit `0`, `CHECKED: 6`
- registry acceptance: exit `0`, `CHECKED: 25`
- Codex/Claude 공통 계약: exit `0`, byte-identical
- 500/501 경계: 500 PASS, 501 FAIL
- `verify.sh`: exit `0`
- `git diff --check`: exit `0`

## 최종 판정 경계

Codex 대체검증으로 저장소 구현의 GREEN과 적대 fixture의 방어력은 확인됐다. 그러나 `V-2`의 “V1은 다른 모델 계열” 계약을 바꾸지 않는 한 Claude V1의 `NOT_RUN`은 그대로다. 따라서 이 문서는 로컬 구현 합격증이지 원래 G/V1/V2 전체 PASS를 위조하는 문서가 아니다.
