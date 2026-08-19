# docs/sot/ 인덱스

이 디렉토리는 "다음 세션이 이 문서 없이도 이 저장소가 왜 이런 규칙으로 도는지 알아야 하는" 것만 담는다. 세션/사건 기록은 `docs/engineering/`(날짜 필수, 불변)에 남긴다. 분류 기준과 파일 크기 예산은 `docs/engineering/docs-sot-restructure-goal-2026-08-08.md` 참고.

- [coding-principles.md](coding-principles.md) — P1~P22 확정 원칙 표 + 웹 자동화 5조 + 검증 체제(V-1~V-5)
- [hook-contracts.md](hook-contracts.md) — 로컬 git hook 5개(pre-commit·pre-push·session-status·acceptance-0-7·install-hooks)의 입출력 계약
- [git-workflow.md](git-workflow.md) — trunk-based + worktree + 태그 릴리스 규약
- [verification-commands.md](verification-commands.md) — 이 저장소의 실제 게이트 명령(make 레포 아님, 실행 확인됨)
- [verification-authority.md](verification-authority.md) — 검증 권한, SHA 귀속, 상태 모델, 보호 영역과 외부 강제/내부 탐지 경계
- [verification-requirements.yaml](verification-requirements.yaml) — 새 검증 권한 요구사항의 실행 계약과 mutation 고정 목록
- [verification-protected-surface.yaml](verification-protected-surface.yaml) — 보호 대상 파일과 외부 보호 가용성의 정직한 상태
- [humansearch-l0-surface-contract.md](humansearch-l0-surface-contract.md) — HumanSearch L0 인증 화면 분류의 입력·출력·경계

새 SOT 파일을 추가하는 유일한 트리거: 스크립트/훅/CI/다음 세션이 이 문서를 **답으로 참조**해야 하는가? 아니면 `docs/engineering/`에 남긴다.
