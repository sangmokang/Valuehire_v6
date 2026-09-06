# docs/sot/ 인덱스

이 디렉토리는 "다음 세션이 이 문서 없이도 이 저장소가 왜 이런 규칙으로 도는지 알아야 하는" 것만 담는다. 세션/사건 기록은 `docs/engineering/`(날짜 필수, 불변)에 남긴다. 분류 기준과 파일 크기 예산은 `docs/engineering/docs-sot-restructure-goal-2026-08-08.md` 참고.

- [coding-principles.md](coding-principles.md) — P1~P24 확정 원칙 표 + 웹 자동화 5조 + 검증 체제(V-1~V-5)
- [hook-contracts.md](hook-contracts.md) — 로컬 git hook 5개(pre-commit·pre-push·session-status·acceptance-0-7·install-hooks)의 입출력 계약
- [git-workflow.md](git-workflow.md) — trunk-based + worktree + 태그 릴리스 규약
- [verification-commands.md](verification-commands.md) — 이 저장소의 실제 게이트 명령(make 레포 아님, 실행 확인됨)
- [humansearch-l0-surface-contract.md](humansearch-l0-surface-contract.md) — HumanSearch L0 인증 화면 분류의 입력·출력·경계
- [humansearch-browser-contract.md](humansearch-browser-contract.md) — HumanSearch 상주 브라우저 진단 접속·단일 탭·사용권·사람 개입·채널별 경계
- [weekly-ops-contract.md](weekly-ops-contract.md) — Weekly 4주 KPI·고객 포지션·Task/Pipeline·채널 소싱·Golden 문체·발행 경계와 현재 구현 상태

새 SOT 파일을 추가하는 유일한 트리거: 스크립트/훅/CI/다음 세션이 이 문서를 **답으로 참조**해야 하는가? 아니면 `docs/engineering/`에 남긴다.
