# HS-03.02 마감 검증 — 다음 실행 프롬프트 v2 (2026-09-16, /clear 뒤 그대로 붙여넣기)

v1 의 결함(외부 검토 R3: `ps | grep -c` 자기 매칭·`lsof` 자기 세션 오탐, R4: 제외 근거 미인용, R5: V1 명령 메모 표기, R6: V2 재현 편중)을 고치고, 억제 만료로 인한 CI 빨간불을 0단계 차단 사유로 추가했다.

```text
$strict
대상: task/hs-0302-candidate-identity-20260914, 기준 범위 7473ec8..HEAD. HEAD 는 `git log -1 --format=%H -- docs/engineering/goal-prompts/hs-0302-closeout-next-prompt-2026-09-16.md` 와 같아야 한다. 다르면 0단계에서 멈추고 보고.
목표: HS-03.02 를 고치는 작업이 아니라 최종 마감 검증이다. 기존 PASS·V1·V2 판정은 주장일 뿐이며 현재 저장소와 실행 결과로 다시 판정한다. 이번 세션은 push·PR 수정·merge·이력 재작성·기능 추가를 하지 않는다.

0단계(착수 자격 — 하나라도 어긋나면 손대지 말고 SHA·PID/COMMAND·git status 만 보고):
  a. `git branch --show-current` = task/hs-0302-candidate-identity-20260914, `git status --porcelain` 빈 출력.
  b. 동시 편집: `pgrep -af '[c]odex app-server' || true` 와 `pgrep -af '[c]odex exec' || true` 가 빈 출력. `lsof -d cwd -Fpc 2>/dev/null | paste - - | grep hs-0302` 결과에서 PID·COMMAND 를 출력하고, 이 세션 자신(현재 셸·claude)과 그 부모를 뺀 나머지가 0 이어야 한다. 단순 줄 수로 판정하지 않는다.
  c. 억제 만료: `suppressions.yaml` 의 expiry 가 오늘보다 앞선 항목이 있으면(2026-09-16 기준 ci-transfer-guarantee·p13-deletion-blindspot 2건이 2026-09-15 만료) CI "억제 만료 스캔" 스텝이 이 브랜치와 main 양쪽에서 빨간불이다. 이 WU 범위 밖이므로 고치지 말고, 검증은 진행하되 최종 판정에 "push 해도 CI 는 억제 만료로 실패한다(별도 PR 필요)" 를 명시한다.

1단계(D1 — P5 이력 처리): `docs/sot/coding-principles.md` 의 P5 행을 직접 읽는다. 실측 기준(2026-09-16): P5① "RED 커밋 이후 테스트 파일 불변 — 구현 PR 의 테스트 파일 diff 검사" 에는 예외 조항이 없고, 그 검사기는 scripts/hooks/CI 어디에도 구현돼 있지 않다(정본 "시행 지점" 절이 "표에만 있고 CI 에 없는 것도 있다" 고 인정). 저장소의 유일한 공식 예외 장치는 P13③ `suppressions.yaml`(check·reason·owner·expiry·issue, 만료 시 CI 실패)이다. 따라서:
  - B(이력 유지)는 "규칙 준수 복구" 가 아니라 "위반 사실의 기록" 이다. B 로 가려면 goal 검증 장부에 위반 커밋(e25ac5e·2d4722a)·변경 내용(단언 삭제 0, 설명문·import 위치)·사장님 결정을 적고, 필요하면 suppressions.yaml 에 expiry 있는 항목으로 등록한다. 장부 기록만으로 위반이 해소됐다고 쓰지 않는다.
  - A(rebase)는 다른 세션 커밋까지 얽혀 있어 이번 세션에서는 실행하지 않는다. A 가 필요하다고 판단되면 사람에게 올린다.
  - 답: __D1__ (A 또는 B). 비어 있으면 1단계에서 멈춘다.

2단계(변경 범위): `git diff --numstat 7473ec8..HEAD` 전체를 기록하고 이번 목표와 무관한 변경을 지목한다. `docs/sot/strict-workflow.md` 브랜치 사본 제거는 `git diff main c5f5896~1 -- docs/sot/strict-workflow.md` 로 브랜치 판이 main 보다 오래된 문구(work-unit-policy 소유 문구)였음을 직접 확인한다.

3단계(과거 결함 4건 회귀 — 각각 규칙·구현 file:line·시험 file:line·실행 결과·반대 증거):
  R1 검사 사이 파일 이동 → 경로 없는 CandidateIdentityError (`_verify_db_boundary` 의 stat try/except; test_db_file_vanishing_between_checks_is_a_closed_error)
  R2 무관 fd 로 오거부 없음 (`_connect_approved_db` 의 "승인 inode 새 fd 부재" 만 거부; test_unrelated_open_files_in_other_threads_do_not_refuse_writes)
  R3 pragma database_list 경로 대조 제거 시 실패 (mutation_case '열린 연결 pragma database_list 경로 대조 제거'; test_opened_db_reported_outside_approved_path_is_refused)
  R4 sidecar hard link 대조 제거 시 실패 (mutation_case 'sidecar hard link 대조 제거'; test_hardlinked_sqlite_sidecar_is_refused[3])

4단계(로컬 검증, 최종 SHA 에서 새로 실행, 기대값 그대로):
  cd humansearch && uv run --frozen pytest -q -p no:cacheprovider   → failed 0, skip/xfail 개수 별도 보고
  uv run --frozen ruff check src tests / uv run --frozen mypy src tests → rc 0
  bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-0302.sh → rc 0, CHECKED ≥ 29, 약화 변이 6종 각각 "잡았다", 명부 127 == 수집
  bash scripts/acceptance-ci-step-integrity.sh → VERDICT: PASS / bash scripts/acceptance-principles-check.sh → CHECKED: 34
  git diff --numstat 7473ec8..HEAD | awk '{a+=$1;d+=$2} END{print a+d}' → 3000 이하 (계약 근거: coding-principles.md P11③ "3,000줄 초과 PR 절대 금지")
  git diff --check 7473ec8..HEAD → 빈 출력

5단계(applicable gate sweep — "전체" 라 부르지 않는다): verify.sh + scripts/acceptance-*.sh 에서 0-2/0-5/0-7 을 뺀 27개를 `bash scripts/verify/run-acceptance.sh <script>` 로 순차 실행, 모두 rc 0, 실행 전후 `git status --porcelain` 빈 출력. 제외 근거는 hooks/pre-push 53~70행(0-2 는 로컬 전용 .secret-patterns 의존, 0-5 는 push 전 논리 불성립, 0-7 은 훅 안 순환)이며 셋 다 CI 가 담당한다.

6단계(V1 — 최종 SHA, Codex, 격리 클론):
  S=<임시 폴더>; git clone -q --no-local "$PWD" "$S/v1-clone" && git -C "$S/v1-clone" checkout -q <최종 SHA>; cp -R humansearch/.venv "$S/v1-clone/humansearch/.venv"
  cd "$S/v1-clone" && TMPDIR="$S/v1-tmp" codex exec -s workspace-write -C "$S/v1-clone" "$(cat "$S/v1-prompt.md")" </dev/null > "$S/v1-stdout.log" 2>&1
  프롬프트에는 계약(goal AC-1~16, 저장 계약 §3·§7·§10, P5·P11·P13·P15·P20)·기준/최종 SHA·변경 범위·검토 파일·재현 명령만 넣고 성공 주장은 넣지 않는다. 어휘는 검토·회귀 시험으로만(정책 차단 어휘 금지). 결과는 private-reviews/hs-0302/ 에 sha256 과 함께 보존. V1 FAIL 은 finding 별로 file:line·조건·영향·재현·환경/제품 구분을 먼저 검증한다.

7단계(V2 — 새 맥락 에이전트, 판정은 파일로 받는다): V1 finding 재현/반증 + 인수 스크립트의 변이 목록을 쓰지 않고 소스의 방어 지점(`raise`·조건 분기)마다 새 변이를 만들어 전용 시험 전체에 돌린다(직전 회차는 18종 중 2종 생존). 생존마다 원본/변이 대조군으로 equivalent 를 가려내고, lint 가 잡으면 lint 를 통과하는 같은 의미의 변이로 재시도한다. 최소 대상: 경로 노출, 검사-사용 사이 이동, 무관 fd, 열린 연결 경로/inode 불일치, sidecar hard link, 필수 시험/인수 검사 삭제·개명, docstring 무해 변경 오탐. 전체 pytest 는 socket bind 가 되는 로컬에서 돌려 환경 실패를 분리한다. 생존 변이 1건이라도 있으면 PASS 금지.

8단계(판정): 작업트리 clean·pytest·ruff/mypy·인수·CI 원칙·applicable gate·V1 미해결 제품 finding 0·V2 재현 완료·V2 생존 0·D1 처리가 P5/P13③ 와 모순 없음 — 모두 만족할 때만 LOCAL_CLOSEOUT_PASS. 보고 형식: 1 코드 판단 2 아키텍처 판단 3 진행 판단 4 SHA 5 변경량 6 명령/rc/출력 7 V1 finding 8 V2 finding·변이 9 D1 근거 10 제외 검사와 근거 11 남은 위험(억제 만료 CI 빨간불 포함) 12 push 가능 후보 여부. "push 가능 후보" 는 승인이 아니며 사람의 지시를 기다린다.
```
