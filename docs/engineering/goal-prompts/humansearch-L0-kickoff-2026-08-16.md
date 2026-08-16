# 폐기됨 — HumanSearch L0 초기 착공 프롬프트 (2026-08-16)

## 결론

이 문서는 실행하지 마십시오. 빈 화면의 결과를 두 가지 중 하나로 허용하고, 추적되지 않은 다른
작업 폴더를 정본으로 가리키며, 검증자 순서를 잘못 적었습니다.

대체 실행 문서:
`docs/engineering/goal-prompts/codex-humansearch-l0-surface-classifier-v2-2026-08-16.md`

정본 계약:
`docs/sot/humansearch-l0-surface-contract.md`

기존 본문은 이 파일의 교정 전 Git 이력에만 남습니다. branch 정리나 squash merge 뒤 특정 commit이
회수될 수 있으므로 보존을 약속하지 않습니다. 새 실행자는 과거 판본을 복원하지 말고 대체 문서가
요구하는 선행 병합 확인과 중단 조건을 먼저 통과해야 합니다.

## 판단 근거

- L0는 현재 화면을 다섯 결과 중 하나로 분류하는 계층으로 확정됐습니다.
- 빈 유효 관측은 `UNKNOWN`, 상충 관측은 `DRIFTED`로 각각 하나의 결과만 가집니다.
- 1차 검증자는 Claude, 2차 검증자는 Claude의 판정을 직접 재현하는 Codex입니다.

## 증거

교정의 전체 근거와 검증 기록은
`docs/engineering/humansearch-l0-autonomous-harness-repair-goal-2026-08-16.md`에 있습니다.
