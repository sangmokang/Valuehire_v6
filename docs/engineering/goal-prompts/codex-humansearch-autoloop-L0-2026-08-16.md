# 폐기됨 — HumanSearch L0 7-state 자율 프롬프트 (2026-08-16)

## 결론

이 문서는 실행하지 마십시오. L0와 후속 실행 단계를 섞어 상태를 잘못 늘렸고, 선행 작업의 병합을
확인하지 않은 채 코드를 시작하게 만들었습니다.

대체 실행 문서:
`docs/engineering/goal-prompts/codex-humansearch-l0-surface-classifier-v2-2026-08-16.md`

정본 계약:
`docs/sot/humansearch-l0-surface-contract.md`

기존 본문은 이 파일의 교정 전 Git 이력에만 남습니다. branch 정리나 squash merge 뒤 특정 commit이
회수될 수 있으므로 보존을 약속하지 않습니다. 새 실행자는 과거 판본을 복원·부분 재사용하지 말고
대체 문서를 처음부터 끝까지 사용해야 합니다.

## 판단 근거

- 기존 판본은 L0의 다섯 화면 결과에 후속 단계의 재확인과 세션 충돌 상태를 섞었습니다.
- 계획에 없는 role 이름과 위험 우선순위를 새로 만들었습니다.
- 아직 `main`에 없는 PR #13과 #14를 확인하지 않고 현재 `main`에서 시작하게 했습니다.
- Claude 1차 검증, Codex 재현 검증, 서버 검사 완료가 종료 조건에 없었습니다.
- 저장소의 Lore 커밋 계약과 RED/GREEN 분리 규칙을 지키지 않았습니다.

## 증거

교정의 전체 근거와 검증 기록은
`docs/engineering/humansearch-l0-autonomous-harness-repair-goal-2026-08-16.md`에 있습니다.
