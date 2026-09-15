# 적대적 리뷰 재현 스크립트 (2026-09-15 01:37~01:39, 읽기 전용)
- repro_pr83.py      : F83-1(프레임 접두 은닉)·F83-3(매출 300억 오탐). 실행: cd worktrees/hs-13-stack-20260910/humansearch && uv run python <이 파일>
- repro_pr83_race.py : F83-2(save↔claim 순서 역전). 같은 위치에서 실행.
- repro_pr96.py      : F96-1(상위 symlink·0777·검사 후 교체)·F96-2(부분 쓰기 잔존·재시도 거부). 실행: cd worktrees/hs-0402a-runner-boundary-20260914/humansearch && uv run python <이 파일>
  hsrunner 계정 부재라 _runner_uid 만 현재 uid 로 대체함. RED 시험으로 옮길 때는 같은 대체를 fixture 로 둔다.
현재 기대 출력(수정 전) = PASSED_THROUGH / ACCEPTED / written. 수정 후에는 REJECTED / denied 로 뒤집혀야 GREEN.
