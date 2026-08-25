# Makefile — harness 게이트 6(종료)의 정본 명령.
#
# 계약: docs/sot/verification-commands.md
#
# 이 파일은 얇은 위임만 한다. 검사 로직은 전부 scripts/ 아래 셸 스크립트에 둔다.
#   · Makefile 은 탭 문법과 셸 이스케이프가 까다로워 판정 로직을 담기에 부적합하다.
#   · 인수 검사가 로직을 직접 호출하고 무력화 사본을 만들려면 파일 하나로 떨어져 있어야 한다.
#
# 이 저장소는 여전히 npm 레포가 아니고, make 도 게이트 6 하나에만 쓴다.
# `make task` / `make verify` / `make ship` 은 아직 없다 — verification-commands.md 표가 정본이다.

.PHONY: task-done

## task-done — 워크트리를 폐기한다. 무시된 산출물이 남아 있으면 차단하고 목록을 낸다.
##   사용법: make task-done NAME=<worktree-name>
##   종료값: 0 폐기함 · 1 회수 대상 있음(BLOCK) · 2 미분류 있음(REVIEW) 또는 판정 불능(REFUSED)
task-done:
	@bash scripts/task-done.sh "$(NAME)"
