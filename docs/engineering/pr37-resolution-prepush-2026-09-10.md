# 최신 main 통합 후 pre-push 원출력

명령: `bash hooks/pre-push`
작업 공간: `worktrees/pr37-resolution-codex-20260910`
검사 커밋: `594b595632dc7e9cdbaf2e0b104b35872c28a300`
세션: `01a0879f-b739-7bf0-b947-5ac4a184d87b`
시작: 2026-09-09T20:33:06.885Z
완료 확인: 2026-09-09T20:40:34.562Z
종료값: 0

```text
VERDICT: PASS
SOT_LOAD: PASS docs/sot/coding-principles.md
LEDGER_LOAD: PASS docs/sot/principles.yaml
MECHANISMS: PASS 34/34 strict-contract-bindings
WIRING: PASS pre-push=1 ci=1
CHECKED: 34
  skip ./scripts/acceptance-0-2.sh (DEFERRED · CI 담당)
  skip ./scripts/acceptance-0-5.sh (DEFERRED · CI 담당)
  skip ./scripts/acceptance-0-7.sh (PUSH-PERFORMING · CI 담당)
pre-push: 검사 29개 실행
  ok  ./scripts/acceptance-0-2-unreachable-content.sh
  ok  ./scripts/acceptance-0-6.sh
  ok  ./scripts/acceptance-ci-step-integrity.sh
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
  ok  ./scripts/acceptance-invoice.sh
  ok  ./scripts/acceptance-principles-check.sh
  ok  ./scripts/acceptance-principles-mutations.sh
  ok  ./scripts/acceptance-secret-webhook-vendor.sh
  ok  ./scripts/acceptance-semantic-mutations.sh
  ok  ./scripts/acceptance-silent-failure-lint-mutations.sh
  ok  ./scripts/acceptance-silent-failure-lint.sh
  ok  ./scripts/acceptance-verified-sha.sh
  ok  ./scripts/acceptance-verify-ac-m.sh
  ok  ./scripts/acceptance-work-unit-policy-mutations.sh
  ok  ./scripts/acceptance-work-unit-policy.sh
  ok  ./verify.sh
```

→ 기존 훅이 선택한 로컬 검사 29개가 모두 성공했습니다. 첫 세 skip은 기존 계약의 CI 이관이며 이번 작업이 새로 만든 예외가 아닙니다. 이 출력은 원명령이 내보낸 전체 출력이며 훅 내부에서 숨긴 하위 명령 로그를 복원한 것이 아닙니다. 원격 push는 실행하지 않았습니다.
