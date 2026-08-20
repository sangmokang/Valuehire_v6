# Strict 원칙 계약 G 실행 증거 — 2026-08-20

## 결론

저장소 내부의 원칙 정본·장부·실행 배선과 적대 fixture는 합격이다. 이후 독립 대체검증에서 발견한 증거 해시 대조 결함도 수정·재공격을 마쳤다. 다른 모델 계열 검증의 미실행은 별도 최종 장부에서 실패로 유지한다.

### 판정 코드

VERDICT: PASS

## 실행 신원

- 주체: Codex G
- 세션 식별자: `codex-root-2026-08-20-strict-principles`
- 기준 commit: `7bd3298695c93e0e60bdabd2500840da47c4db05`
- 실행 시각: `2026-08-20T02:18:52+0900`
- 원칙 정본 SHA-256: `073d4bf646b069fae376ec268bf97ea835c5019386908535adc8b6ee71ffdc7a`
- 원칙 장부 SHA-256: `7efdb3093e9f7575f71940af323a664d96c2432370090dfe4db8b6f2097eff5a`
- 검사기 SHA-256: `5d83868961ad628a6d8f7ae42014f019895fa3069a53282dc58bc95f92f0731e`

## 원칙 검사·반례 전체 출력

명령:

```text
bash scripts/acceptance-principles-check.sh
bash scripts/acceptance-principles-mutations.sh
```

→ 두 원명령을 순서대로 실행해 정상 장부와 고장 사본을 함께 검증했다.

종료값: 0

```text
VERDICT: PASS
SOT_LOAD: PASS docs/sot/coding-principles.md
LEDGER_LOAD: PASS docs/sot/principles.yaml
MECHANISMS: PASS 32/32
WIRING: PASS pre-push=1 ci=1
CHECKED: 32
PASS: FIXTURE-NORMAL 정상 fixture — PASS (exit=0)
PASS: C1 principles.yaml 삭제 — FAIL (exit=1)
PASS: C2 coding-principles.md 삭제 — FAIL (exit=1)
PASS: C3 YAML 문법 오류 — FAIL (exit=1)
PASS: C4 원칙 ID 하나 삭제 — FAIL (exit=1)
PASS: C5 중복 ID 추가 — FAIL (exit=1)
PASS: C6 mechanism 경로 미존재 — FAIL (exit=1)
PASS: C7 CI 실행 줄 삭제 — FAIL (exit=1)
PASS: C8 검사기 파일 삭제 — FAIL (exit=127)
PASS: C9 검사 대상 0개가 되도록 글로브 변경 — FAIL (exit=1)
PASS: C10-A CI에 || true 삽입 — FAIL (exit=1)
PASS: C10-B CI에 continue-on-error 삽입 — FAIL (exit=1)
PASS: C11 거짓 최종 판정 차단 — FAIL (exit=1)
PASS: C12 거짓 최종 판정 차단 — FAIL (exit=1)
PASS: C13 Codex/Claude 공통 계약 불일치 — FAIL (exit=1)
PASS: C14-A 메모리 파일 없음, 현재 SOT 직접 로드 — PASS (exit=0)
PASS: C14-B 메모리 파일 잘림, 현재 SOT 직접 로드 — PASS (exit=0)
PASS: BOUNDARY-500 직접 작성 코드 500줄 — PASS
PASS: BOUNDARY-501 직접 작성 코드 501줄 — FAIL
PASS: SOURCE-TREE 원본 저장소 상태 불변
CHECKED: 20
VERDICT: PASS
```

→ 당시 최초 20개 fixture가 기대 상태와 일치했으며 이후 절에서 반례를 확장했다.

## registry 전체 출력

명령:

```text
bash scripts/verify/check-mechanism-registry.sh
bash scripts/acceptance-verify-ac-m.sh
```

→ registry 원명령과 전용 acceptance fixture를 함께 실행했다.

종료값: 0

```text
PASS: secrets-scan-precommit (pre-commit · 규칙 1·2·3)
PASS: acceptance-glob-prepush (pre-push · 규칙 1·2·3)
PASS: ci-secret-scan (ci · 규칙 1·2·4)
PASS: principles-local-check (manual · 규칙 1·2·5)
PASS: principles-explicit-prepush (pre-push · 규칙 1·2·3)
PASS: principles-explicit-ci (ci · 규칙 1·2·4)
PASS: 원칙 검사 원명령 실행 (local·pre-push·ci 배선 포함)
CHECKED: 6
PASS: 검사기 실존·실행가능 — scripts/verify/check-mechanism-registry.sh
PASS: fixture 정상 명부 → 통과 (exit=0)
PASS: fixture path 없는 항목 → 불합격 (exit=1)
PASS: fixture 죽은 target → 불합격 (exit=1)
PASS: id 중복 → 불합격 (exit=1)
PASS: 알 수 없는 stage → 불합격 (exit=1)
PASS: manual 인데 사유 없음 → 불합격 (exit=1)
PASS: manual 정상(사유+실행권한) → 통과 (exit=0)
PASS: manual 인데 실행권한 없음 → 불합격 (exit=1)
PASS: ci 인데 거짓 target → 불합격 (exit=1)
PASS: 절대경로 path → 불합격 (exit=1)
PASS: 상대경로 심볼릭 링크 → 불합격 (exit=1)
PASS: 필드 중복(path 2회, 마지막 값 유효) → 불합격 (exit=1)
PASS: id 뒤 인라인 주석 → 불합격 (exit=1)
PASS: 닫히지 않은 따옴표 → 불합격 (exit=1)
PASS: stage 불일치 필드(ci_mirror_job) → 불합격 (exit=1)
PASS: 문법 오류·항목 0개 → 위반(1) (exit=1)
PASS: 항목 0개 명부 → NOT_RUN (exit=2)
PASS: ci_mirror_job 불일치 → 불합격 (exit=1)
PASS: 필수 필드(stage) 누락 → 불합격 (exit=1)
PASS: 빈 문자열 path → 불합격 (exit=1)
PASS: CI 배선 — verify.yml 에 무조건 실행 스텝 정확히 1회
PASS: 실제 명부(docs/sot/mechanism-registry.yaml) → 통과 (exit=0)
PASS: 명부 항목 6개 = 검사기 보고 6개 (하한 3)
PASS: 저장소 무오염 (시작/종료 상태 동일)
CHECKED: 25
```

→ 실제 명부 6개와 registry 고장 fixture 25건이 기대 상태와 일치했다.

## Strict 대칭성·잠금 전체 출력

명령:

```text
bash scripts/verify/check-strict-principles-skills.sh
bash scripts/guard-global-skill-files.sh check
bash scripts/acceptance-guard-global-skill-files.sh
```

→ 두 전역 스킬의 공통 계약과 검증 중 잠금 수명주기를 확인했다.

종료값: 0

```text
VERDICT: PASS
COMMON_CONTRACT: PASS byte-identical
ENGINE_ORDER: PASS Codex/Claude platform-only difference
LINES: codex=306 claude=306
CHECKED: 2
PASS: 2개 파일 내용·lock 권한 일치
LIMIT: 동일 UID 적대자에 대한 불변성 증거가 아님
PASS: normal lock — exit=0, modes=444/444
PASS: check 전 unlock 거부 — exit=1
PASS: check 뒤 unlock + 원래 권한 복구 — check=0 unlock=0
PASS: 두 번째 파일 누락 preflight — exit=1, first-mode=640
PASS: 첫 chmod 뒤 중간 종료 rollback — exit=143
PASS: 비정상 종료 뒤 recover — exit=0, PASS로 세지 않는 표식
PASS: 동일 UID 내용+상태 위조 우회 재현 — check exit=0 (0이 문서화된 한계)
PASS: 원본 worktree 상태 기준선 보존 — before/after 동일
CHECKED: 8
```

→ 두 스킬의 공통 계약·엔진 순서·guard 한계를 확인했고, `quick_validate.py`도 각각 `Skill is valid!`를 반환했다.

## 실제 pre-push 전체 출력

명령: 추적 파일을 새 임시 Git 저장소에 복제·커밋한 뒤 `bash hooks/pre-push`

종료값: 0

```text
VERDICT: PASS
SOT_LOAD: PASS docs/sot/coding-principles.md
LEDGER_LOAD: PASS docs/sot/principles.yaml
MECHANISMS: PASS 32/32
WIRING: PASS pre-push=1 ci=1
CHECKED: 32
  skip ./scripts/acceptance-0-2.sh (DEFERRED · CI 담당)
  skip ./scripts/acceptance-0-5.sh (DEFERRED · CI 담당)
  skip ./scripts/acceptance-0-7.sh (PUSH-PERFORMING · CI 담당)
pre-push: 검사 21개 실행
  ok  ./scripts/acceptance-0-2-unreachable-content.sh
  ok  ./scripts/acceptance-0-6.sh
  ok  ./scripts/acceptance-guard-global-skill-files.sh
  ok  ./scripts/acceptance-hs-a3.sh
  ok  ./scripts/acceptance-hs-a4.sh
  ok  ./scripts/acceptance-hs-cleanroom-absolute-contexts.sh
  ok  ./scripts/acceptance-hs-cleanroom-absolute-paths.sh
  ok  ./scripts/acceptance-hs-cleanroom-colon-paths.sh
  ok  ./scripts/acceptance-hs-cleanroom-file-urls.sh
  ok  ./scripts/acceptance-hs-cleanroom-hook-env-mutations.sh
  ok  ./scripts/acceptance-hs-cleanroom-hook-env.sh
  ok  ./scripts/acceptance-hs-cleanroom-mutations.sh
  ok  ./scripts/acceptance-hs-cleanroom.sh
  ok  ./scripts/acceptance-hs-gates-antiforge.sh
  ok  ./scripts/acceptance-hs-gates-mutations.sh
  ok  ./scripts/acceptance-hs-gates.sh
  ok  ./scripts/acceptance-principles-check.sh
  ok  ./scripts/acceptance-principles-mutations.sh
  ok  ./scripts/acceptance-secret-webhook-vendor.sh
  ok  ./scripts/acceptance-verify-ac-m.sh
  ok  ./verify.sh
```

→ 깨끗한 snapshot의 pre-push가 원칙 검사 포함 21개 검사를 모두 실행했다.

## 기타 정적 증거

```text
bash verify.sh
PASS: no secret-pattern match in any tracked file, .env not tracked

WORKFLOW_YAML: PASS
git diff --check: exit 0
scripts/acceptance-principles-check.sh 294
scripts/acceptance-principles-mutations.sh 224
scripts/guard-global-skill-files.sh 249
scripts/acceptance-guard-global-skill-files.sh 181
scripts/verify/check-strict-principles-skills.sh 85
scripts/verify/check-strict-verdict-ledger.sh 96
```

→ 당시 정적 검사와 파일별 줄 수 기준이 모두 통과했다.

## goal continuation 최종 재실행

장부의 `mechanism_found`가 제품 기능 전체 구현이 아니라 Strict 계약 편입 장치임을 명시하고, 빈 파일·알 수 없는 ID·문구 불일치·빈 mechanism·잘못된 check/stages·자기 제외·CI 조건/다중 줄·pre-push 약화 반례를 추가한 뒤 같은 원명령을 다시 실행했다.

명령:

```text
bash scripts/acceptance-principles-check.sh
bash scripts/acceptance-principles-mutations.sh
```

→ 확장된 원칙 검사와 mutation suite를 같은 현재 작업트리에서 다시 실행했다.

종료값: 0

```text
VERDICT: PASS
SOT_LOAD: PASS docs/sot/coding-principles.md
LEDGER_LOAD: PASS docs/sot/principles.yaml
MECHANISMS: PASS 32/32 strict-contract-bindings
WIRING: PASS pre-push=1 ci=1
CHECKED: 32
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
PASS: C13 Codex/Claude 공통 계약 불일치 — FAIL (exit=1)
PASS: C14-A 메모리 파일 없음, 현재 SOT 직접 로드 — PASS (exit=0)
PASS: C14-B 메모리 파일 잘림, 현재 SOT 직접 로드 — PASS (exit=0)
PASS: BOUNDARY-500 직접 작성 코드 500줄 — PASS
PASS: BOUNDARY-501 직접 작성 코드 501줄 — FAIL
PASS: SOURCE-TREE 원본 저장소 상태 불변
CHECKED: 32
VERDICT: PASS
```

→ 두 정본의 32개 Strict 편입 장치와 명시적 pre-push/CI 배선이 정상이며, 요구된 구조·약화 반례 32개가 모두 기대 상태를 냈다. 이 PASS는 `mechanism_expected`에 적힌 제품 기능 전체가 구현됐다는 주장이 아니다.

## Codex 대체검증 후 artifact 증거 보강

독립 Codex 검증자가 판정 장부의 `artifact_hash`가 형식만 검사되고 실제 파일과 대조되지 않는 결함을 발견했다. 장부에 역할별 `artifact` 경로를 추가하고 검사기가 경로 안전성·파일 실존·비심볼릭 링크·실제 SHA-256 일치를 확인하도록 수정했다.

```text
bash scripts/verify/check-strict-verdict-ledger.sh scripts/verify/fixtures/strict-principles/valid-verdict.yaml
VERDICT: PASS
ROLES: PASS G/V1/V2/T
CHECKED: 4
exit=0

missing artifact fixture
VERDICT: FAIL
ARTIFACT_MISSING: g=missing/no-artifact
exit=1

hash mismatch fixture
VERDICT: FAIL
ARTIFACT_HASH_MISMATCH: g=scripts/verify/fixtures/strict-principles/artifact.txt
exit=1

bash scripts/acceptance-principles-mutations.sh
PASS: C11-ARTIFACT-MISSING 증거 파일 누락 차단 — FAIL (exit=1)
PASS: C11-ARTIFACT-HASH 증거 해시 불일치 차단 — FAIL (exit=1)
CHECKED: 34
VERDICT: PASS
exit=0
```

→ 최초 대체검증의 실제 finding을 수정하고 같은 독립 검증자가 재공격해 `CODEX_SUBSTITUTE_RECHECK: PASS`를 냈다. 이 단계 뒤 실제 Claude V1과 새 맥락 Codex V2를 별도로 실행했다.

## 최종 G 재검증 — runtime 지문 방어 포함

V1/V2가 발견한 주석·echo·죽은 코드·`if false`·고정 Git 신원·고정 임시경로 접두사 우회를 각각 RED fixture로 고정한 뒤 런타임 probe를 무작위화했다.

```text
bash scripts/verify/check-pre-push-runtime.sh hooks/pre-push
PASS: pre-push runtime probe discovered and executed
exit=0

bash scripts/acceptance-principles-check.sh
VERDICT: PASS
SOT_LOAD: PASS docs/sot/coding-principles.md
LEDGER_LOAD: PASS docs/sot/principles.yaml
MECHANISMS: PASS 32/32 strict-contract-bindings
WIRING: PASS pre-push=1 ci=1
CHECKED: 32
exit=0

bash scripts/acceptance-principles-mutations.sh
PASS: C9-COMMENT-DECOY ... FAIL (exit=1)
PASS: C9-ECHO-DECOY ... FAIL (exit=1)
PASS: C9-DEAD-CODE ... FAIL (exit=1)
PASS: C9-IF-FALSE ... FAIL (exit=1)
PASS: C9-RUNTIME-FINGERPRINT ... FAIL (exit=1)
PASS: C9-RUNTIME-PATH-FINGERPRINT ... FAIL (exit=1)
PASS: BOUNDARY-500 직접 작성 코드 500줄 — PASS
PASS: BOUNDARY-501 직접 작성 코드 501줄 — FAIL
CHECKED: 40
VERDICT: PASS
exit=0

bash scripts/verify/check-mechanism-registry.sh
CHECKED: 6
exit=0

bash scripts/acceptance-verify-ac-m.sh
CHECKED: 31
exit=0

bash scripts/verify/check-strict-principles-skills.sh
VERDICT: PASS
COMMON_CONTRACT: PASS byte-identical
ENGINE_ORDER: PASS Codex/Claude platform-only difference
LINES: codex=306 claude=306
CHECKED: 2
exit=0

bash scripts/acceptance-guard-global-skill-files.sh
CHECKED: 8
exit=0

bash verify.sh
PASS: no secret-pattern match in any tracked file, .env not tracked
exit=0
```

실제 Claude V1 최종 판정은 `PASS`, 새 맥락 Codex V2 `/root/strict_principles_v2_final_r2`도 `PASS`다. 전체 원문은 각각의 verdict 문서에 보존한다.

## 커밋 상태 pre-push 통합 검증

미추적 파일은 현재 저장소의 `verify.sh` 대상이 아니므로, 현재 tracked+untracked 구현을 임시 Git 저장소에 복제해 모두 커밋한 뒤 실제 `hooks/pre-push`를 실행했다. 첫 실행은 runtime helper의 `MARKER_TOKEN="..."` 변수가 기존 secret pattern의 자격증명 대입 형태와 충돌해 `acceptance-0-6.sh`와 `verify.sh`에서 exit 1이었다. 이를 PASS로 숨기지 않고 변수명을 비밀 키워드가 아닌 `MARKER_PROOF`로 바꿨다.

수정 후 같은 검증:

```text
pre-push: 검사 21개 실행
  ok  ./scripts/acceptance-0-6.sh
  ok  ./scripts/acceptance-principles-check.sh
  ok  ./scripts/acceptance-principles-mutations.sh
  ok  ./scripts/acceptance-verify-ac-m.sh
  ok  ./verify.sh
ISOLATED_HEAD=6571e0ac11b8ba8f24197ecfa079da7a8ddbd6e8
ISOLATED_PRE_PUSH_EXIT=0
```

격리 저장소는 원본 밖에서 만들었고 실행 뒤 macOS 휴지통으로 이동했다. 원본 작업트리는 검사 전후 동일했다.
