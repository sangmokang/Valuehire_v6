# V1 실행 재검토 프롬프트 — Work Unit 방법론

현재 저장소를 읽기 전용으로 독립 검토한다. 파일을 수정하거나 커밋하지 않는다. 첫 줄은 `VERDICT: PASS`, `VERDICT: FAIL`, `VERDICT: NOT_RUN` 중 하나다.

## 검토 대상

- `docs/engineering/work-unit-methodology-goal-2026-08-21.md`
- `docs/sot/git-workflow.md`
- `docs/sot/verification-commands.md`
- `scripts/acceptance-principles-check.sh`
- `scripts/acceptance-principles-mutations.sh`
- 기준 범위: `dcc71dd022cba9656cb1a4b6a0f825d8d99655a5..HEAD`

## 반드시 직접 실행할 명령

```bash
bash scripts/acceptance-principles-check.sh
bash scripts/acceptance-principles-mutations.sh
bash scripts/check-docs-sot.sh
bash -n scripts/acceptance-principles-check.sh scripts/acceptance-principles-mutations.sh
git diff --check dcc71dd022cba9656cb1a4b6a0f825d8d99655a5..HEAD
```

명령별 종료값과 핵심 출력을 판정문에 기록한다. 하나라도 실행하지 못하면 실행 검토는 `NOT_RUN`이다. 전달받은 로그나 문구 검색만으로 PASS를 만들지 않는다.

## 공격할 계약

1. Work Unit이 파일 묶음이 아니라 반증 가능한 주장 하나인가.
2. RED 계약 커밋과 WU 완료 커밋이 P5를 보존하며, 검토 보정 커밋의 다중 WU 귀속이 거짓 “WU 하나=커밋 하나”를 만들지 않는가.
3. PR 1개당 goal 1개·WU 1~5개 상한과 브랜치 24~48시간 상한이 충돌할 때 시간 상한이 우선하는가.
4. WU별 표적 검증·작은 적대검증이 최종 strict·codeaudit·결합 적대검증·CI를 대체하지 않는가.
5. pre-push PASS가 최종 세 관문을 대신한다고 의미 반전할 수 있는가.
6. 고위험 경로 목록 일부 삭제, 문서 REVIEW만으로 PASS, 최종 적대검증 생략을 기존 원칙 게이트가 실패시키는가.
7. 외부 모델·유료 GitHub 기능·새 CI 실행 줄 없이 기본 절차가 작동하는가.
8. WU 상태와 커밋 해시·검증 로그가 실제 현재 상태와 일치하는가.

PASS는 위 직접 실행과 공격에서 중대·높음 결함이 없을 때만 가능하다. 결함이 있으면 심각도, 원인, 사업 영향, `file:line`, 재현 명령을 적는다.
