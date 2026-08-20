# V2 판정 — 원칙 게이트 복구

V2_VERDICT: FAIL

## 결론

새 맥락 Codex 검증자는 복구된 원칙 게이트와 기존 일반 변경 요청 검증을 직접 재실행해 새 결함을 찾지 못했다. 로컬 구현은 합격이지만 독립 V1이 미실행이므로 전체 Strict 판정은 실패다.

## 직접 재현

```text
bash scripts/acceptance-principles-check.sh
→ PASS, CHECKED: 32

bash scripts/acceptance-principles-mutations.sh
→ PASS, CHECKED: 34

bash scripts/verify/check-mechanism-registry.sh
→ PASS, CHECKED: 6

bash scripts/acceptance-verify-ac-m.sh
→ PASS, CHECKED: 25

bash scripts/acceptance-verification-authority.sh
→ PASS, MUTATIONS: total=32 blocked=31 survived=0 controls=1

bash verify.sh
→ PASS

git diff --check
→ PASS
```

→ 두 정본, 명시적 pre-push/CI 배선, 적대 fixture, mechanism registry, 기존 일반 PR 검증과 기본 저장소 검사가 모두 현재 파일에서 재현됐다.

## 적대 판정

- 활성 CI에는 merge_group 트리거, 관련 토큰 또는 환경변수가 없다.
- 남은 merge_group 문자열은 재도입을 실패시키는 방어 mutation과 보존된 기존 사용자 자산이다.
- 워크플로 문서의 명명된 검사·증거 단계는 실제 파일과 같은 21개다.
- 기존 42개 미추적 사용자 자산의 결합 SHA-256은 시작값과 같은 `1e008fb0728c104acd241e884f43b78abaedc9e177b7c2cd87e6aecb91799ab7`이다.

## 전체 Strict 판정

V1은 비용 잔액 부족으로 토큰 0건, 검증 본문 0건이었다. V2의 로컬 PASS는 다른 모델 계열 V1을 대체하지 않으므로 전체 판정은 FAIL을 유지한다.
