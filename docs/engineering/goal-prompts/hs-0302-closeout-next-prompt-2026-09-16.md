# HS-03.02 마감 — 다음 실행 프롬프트 (2026-09-16, /clear 뒤 그대로 붙여넣기)

```text
$strict
대상: task/hs-0302-candidate-identity-20260914 의 7473ec8..HEAD (HEAD 는 `git log -1 --format=%H -- docs/engineering/goal-prompts/hs-0302-closeout-next-prompt-2026-09-16.md` 와 같아야 한다. 다르면 0단계에서 멈추고 보고).
0단계(착수 자격): `git -C worktrees/hs-0302-candidate-identity-20260914 status --porcelain` 이 비어 있고, `ps -eo command | grep -c "codex app-server"` 가 0 이며, 이 워크트리를 cwd 로 가진 다른 셸이 없어야 한다(`lsof -d cwd | grep hs-0302`). 하나라도 어긋나면 손대지 말고 보고한다.
1단계(사장님 결정 반영, 아래 __D1__ 에 답이 채워져 있어야 진행):
  D1 P5 이력 위반(e25ac5e·2d4722a 가 RED 뒤 시험 파일 수정, 단언 삭제는 없음) = [A 이력 재구성(rebase, 위험·다른 세션 커밋 포함) | B goal 검증 장부에 예외로 명시하고 이력 유지(권장)]. 답: __D1__
  D1=A 면 rebase 는 별도 워크트리에서 하고 원 브랜치를 태그로 먼저 보존한다. 접두 해시 기준선 검사기는 17차에서 이미 제거됐으므로 별도 결정이 없다.
2단계(검증, 최종 SHA 에서 전부 새로 실행, 기대값 그대로):
  cd humansearch && uv run --frozen pytest -q            → "N passed" 만, failed 0
  uv run --frozen ruff check src tests / uv run --frozen mypy src tests → rc 0
  bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-0302.sh → "CHECKED: 29" 이상, 약화 변이 6종 전부 "잡았다"
  bash scripts/acceptance-ci-step-integrity.sh → VERDICT: PASS / bash scripts/acceptance-principles-check.sh → CHECKED: 34
  git diff --numstat 7473ec8..HEAD | awk '{a+=$1;d+=$2} END{print a+d}' → 3000 이하
  전체 게이트: verify.sh + scripts/acceptance-*.sh 전량(0-2/0-5/0-7 제외) rc 0, 작업트리 전후 clean
  V1: `codex exec -s workspace-write -C <--no-local 클론>` — 프롬프트에 공격·우회·깨뜨·무력화·뚫 어휘 금지(정책 차단), 검토·회귀시험 어휘로. 판정 원문은 private-reviews/hs-0302/ 에 sha256 과 함께 보존.
  V2: 새 맥락 에이전트가 V1 의 file:line·명령을 재실행. 전체 pytest 는 socket bind 가 되는 환경(로컬)에서 돌려 V1 의 환경 실패 16건을 판정에서 분리.
3단계(SHIP, 사장님 직전 승인 뒤에만): push → PR #100 본문을 §8-8 순서(결론/사장님이 볼 부분/확인한 것/못 한 것/증거)로 갱신 → `gh pr view 100 --json title,body,url` 재확인 → CI 를 최종 SHA 로 귀속 확인(scripts/verify/check-verified-sha.sh). merge 는 하지 않는다.
중단 조건: FAIL·NOT_RUN·변이 생존·다른 세션 동시 편집 감지 중 하나라도 있으면 멈추고 명령·종료값·출력·SHA 만 보고.
```

근거: 이 세션 장부 `docs/engineering/humansearch-hs-0302-candidate-identity-goal-2026-09-15.md` 검증 장부, V1 7~9회차 원문 `private-reviews/hs-0302/`.
