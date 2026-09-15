# 착수 프롬프트 v2 — HS-03.02 최종 마감: 남은 일만 (2026-09-15 14:55)

## 결론

v1 프롬프트(11:13 작성)는 현실보다 낡았다. 13:39 착수 시도에서 0단계 불일치(다른 세션 실행 중)로 멈췄고, Codex 적대 리뷰(14:00~14:50)가 v1의 남은 일 목록을 다시 갈랐다. **끝난 일**: 계약 문서 개정(WU-B), CI 배선 자체(WU-A 대부분), PR #100 Draft 생성. **남은 일**: 검증 정본 머리글 숫자 1건, DB 저장 경계 결함(높음, 재현 대기) 1건, 현재 최종 커밋에 대한 독립 검토(WU-C), 승인 뒤 기존 PR #100 갱신. 아래를 새 세션에 그대로 붙여넣는다.

## v1 대비 정정 (Codex 초안에서 두 곳을 바꿨다)

| 항목 | Codex 초안 | v2 |
|---|---|---|
| 0단계 "원격보다 5커밋 앞" | 고정 기대값 `0 5` | 다른 세션이 그 사이 push 했을 수 있으므로 실측 후 기록. 로컬이 원격보다 뒤면 중단 |
| 1단계 반례 재현 주체 | 명시 없음 | Claude 세션이 쓰기 가능한 격리 폴더(mktemp)에서 수행. Codex 상자는 임시 파일·네트워크가 막혀 재현 불가 |

→ 나머지는 Codex 초안 그대로다. 3라운드 파일 도입 커밋은 3996dd8(12:22)이고 3bcfdad(13:05)는 그 파일을 고친 커밋이다.

```text
$strict

역할: 너는 HS-03.02(후보 동일성·중복 방지) 최종 마감 담당이다. 완료된 CI 배선과 계약 문서 개정은 다시 구현하지 않는다. 남은 결함만 재현·수정하고, 마지막 독립 검토는 작성자와 다른 세션이 한다. "통과했다" 대신 명령·종료값·출력 원문만 기록한다. push·PR 갱신은 사장님이 이 세션에서 명시적으로 승인할 때만 한다.

저장소: /Users/kangsangmo/Desktop/Valuehire_v6
작업 위치: /Users/kangsangmo/Desktop/Valuehire_v6/worktrees/hs-0302-candidate-identity-20260914 (브랜치 task/hs-0302-candidate-identity-20260914, 스택 베이스 task/hs-0301-sqlite-schema-20260914 @7473ec8 = PR #97)
메인 작업트리·다른 워크트리 수정 금지. 파괴적 실증은 mktemp 아래에서만.

0. 착수 조건 (값을 전부 기록한다. 중단 조건에 걸리면 착수하지 않고 §8 형식으로 보고한다)
pwd; git branch --show-current                     → task/hs-0302-candidate-identity-20260914
git status --short                                 → 출력 없음. 하나라도 있으면 중단
git log --format='%h %ci %s' -3                    → 기대 HEAD c14638d(13:28 "필수 시험 명부 건수를 … 정확한 기대값으로 본다"). 다르면 새 HEAD 를 기록하고 1~3단계의 모든 실측을 새 HEAD 기준으로 다시 한다
stat -f '%Sm' -t '%F %T' "$(git rev-parse --git-dir)/index"  → 참고 신호. 10분 이내면 lsof +D "$PWD" 와 ps 로 살아 있는 셸의 PID·시작시각·명령을 원문으로 기록하고, 다른 쓰기 세션이 입증될 때만 중단
git fetch origin 2>&1 | tail -1; git rev-list --left-right --count HEAD...origin/task/hs-0302-candidate-identity-20260914  → 실측값 기록(13:41 실측은 "5 0" = 로컬이 5커밋 앞). 오른쪽 숫자가 0 이 아니면(원격이 앞서면) 중단
gh pr view 100 --json number,state,isDraft,baseRefName,headRefName,headRefOid,url  → OPEN·Draft·base task/hs-0301-sqlite-schema-20260914·head 브랜치 일치. 조회 실패면 PR 상태는 NOT_RUN 으로 적고 추정하지 않는다
git config core.hooksPath                          → hooks
cd humansearch && uv run --frozen pytest -q 2>&1 | tail -1   → "N passed", failed 0 (13:28 장부 기준 311 passed)
uv run --frozen ruff check src tests && uv run --frozen mypy src tests → 종료값 0
cd .. && bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-0302.sh 2>&1 | tail -3  → CHECKED: 22, 종료값 0
이력 기록: 3라운드 시험 파일 test_hs_0302_r3_hardening.py 는 3996dd8 에서 추가, 3bcfdad 에서 소문자 시각 시험 보강.

1. 프롬프트 회수 커밋
이 파일은 worktrees/hs-prompts-20260915/docs/engineering/goal-prompts/humansearch-hs-0302-closeout-prompt-v2-2026-09-15.md 에 있다. 같은 경로로 복사하고 커밋: "HS03.02 최종 마감 착수 프롬프트 v2 를 저장소에 둔다". git show --stat HEAD 에 파일 1개만.

2. WU-D — DB 저장 경계 반례 재현 → 수정 (Codex 14:50 높음 결함, 재현 대기)
주장: humansearch/src/humansearch/candidate_identity.py 의 _verify_db_location 은 링크·존재만 보고, _insert_once 가 DB 부모 0700·DB 0600·현재 UID·일반 파일·Git 밖 승인 루트·SQLite sidecar 경계를 확인하지 않은 채 연결을 연다. 저장 정본 docs/sot/humansearch-storage-contract.md 80~83행(쓰기 직전 보호 규칙)과 충돌.
RED 먼저(격리 폴더, git 환경변수 unset):
  (a) 정상 DB 초기화 후 DB 를 0644, 부모를 0755 로 완화 → record_candidate_identity 호출
  (b) 호환 스키마 DB 를 Git 작업 폴더 아래(예: mktemp 안에 git init 한 폴더)에 두고 호출
  (c) 대조군: 정상 권한·Git 밖 경로 → 기록 1행
현재 함수가 (a)·(b)에서 기록하면 RED 증거(명령·출력 원문). 재현되지 않으면 코드를 고치지 않고 원인을 보고하고 3단계로 간다.
재현되면: 각 반례가 CandidateIdentityError 를 내고 행 0 이 되는 시험을 tests/test_hs_0302_r4_db_boundary.py 로 먼저 추가(RED 커밋) → 쓰기 직전 검증을 최소 수정으로 추가(GREEN 커밋). 오류 메시지에 경로 원문·키 바이트·HMAC·position_ref·candidate_ref 를 넣지 않는다. 필수 시험 명부 scripts/verify/fixtures/hs-0302-required-tests.txt 와 EXPECTED_REQUIRED_IDS 를 함께 올린다(명부와 상수 동반 갱신 없이는 인수 검사가 FAIL 이어야 한다 — 그 FAIL 을 먼저 기록한다).
AC-D1: 격리 사본에서 새 검증 한 줄을 지우면 r4 시험이 실패한다(변이 생존 0).
AC-D2: 대조군 (c)는 수정 전후 모두 1행 기록.
커밋: "HS03.02 DB 저장 경계 반례를 시험으로 먼저 고정한다" / "HS03.02 쓰기 직전에 DB 권한·위치를 검증한다"

3. WU-A' — 검증 정본 머리글 숫자만 정합
CI 스텝과 표 27행은 이미 있다(55602f1·9d9e2c7). 재배선 금지.
docs/sot/verification-commands.md 20행 "워크플로 스텝 26개" 를 실측 27 로 고친다.
AC-A2': /usr/bin/grep -c '^      - name:' .github/workflows/verify.yml (=28) − 표에서 각주로 제외한 checkout 1 = 표 번호행 수 (awk '/^\| *[0-9]+ *\|/{c++} END{print c}' docs/sot/verification-commands.md =27) = 머리글 숫자 27. 세 값을 원문으로 붙인다. v1 의 "세 값 직접 동등" 조건은 쓰지 않는다.
AC-A3: bash scripts/acceptance-ci-step-integrity.sh → VERDICT: PASS, CHECKED: 24.
AC-A4: bash scripts/acceptance-principles-check.sh → CHECKED: 34, rc 0.
WU-B(계약 문서 개정)는 완료 상태다. 내용 변경 금지.
커밋: "HS03.02 검증 정본 머리글 스텝 수를 실측에 맞춘다"

4. 최종 검증 (현재 HEAD 에 귀속, 과거 결과로 대체 금지)
cd humansearch && uv run --frozen pytest -q | tail -1 ; uv run --frozen ruff check src tests ; uv run --frozen mypy src tests
cd .. && bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-0302.sh | tail -3
bash scripts/acceptance-hs-gates-mutations.sh ; bash scripts/acceptance-hs-gates.sh 2>&1 | tail -2 ; bash scripts/acceptance-hs-gates-antiforge.sh 2>&1 | tail -2
bash scripts/acceptance-ci-step-integrity.sh | tail -2 ; git diff --check 7473ec8..HEAD ; echo rc=$?
각 명령의 종료값·마지막 출력·실행 SHA 를 goal 문서 docs/engineering/humansearch-hs-0302-candidate-identity-goal-2026-09-15.md 의 검증 장부에 "7차" 행으로 적는다. 임시 폴더·네트워크가 막히면 NOT_RUN.

5. WU-C — 최종 독립 검토 (작성자와 다른 쪽이 한다)
/humanreview 로 7473ec8..최종 HEAD 를 읽기 전용 리뷰. 최소 공격:
- DB 권한·Git 밖 경계 검증 제거 변이 / 키 폴더가 DB 보호 루트 하위일 때 거부 제거 변이
- 필수 시험 명부와 EXPECTED_REQUIRED_IDS 동반 약화(시험 1개 + 명부 1줄 + 상수 −1)
- verify.yml 의 HS-03.02 스텝 run 줄에 실패 삼키는 꼬리(`|| true`, `; echo`) 주입 → check-hs-0302-ci-wiring.rb 가 FAIL 인가
- 인수 스크립트 "true" 치환 / CHECKED 위조 / pytest 호출 제거
- AC-3 경쟁 시험이 실제로 서로 다른 연결 2개를 쓰는가
- 예외 메시지 전수 grep: position_ref·candidate_ref·키 바이트·HMAC·절대 경로 노출 0건
판정 APPROVE / REQUEST_CHANGES / NOT_RUN. 결함은 파일:줄·재현 입력·영향·최소 수정 방향. REQUEST_CHANGES 면 멈추고 보고한다 — 고치지 않는다. 장부 "V1 (5차)" 행을 이 결과로 갱신하고 커밋: "HS03.02 장부에 최종 독립 검토를 남긴다".

6. push·PR #100 갱신 (APPROVE 이고 사장님이 이 세션에서 명시 승인한 경우에만)
새 PR 을 만들지 않는다. git push origin task/hs-0302-candidate-identity-20260914 → gh pr view 100 --json headRefOid,isDraft,baseRefName,state 로 head SHA 가 최종 HEAD 와 같은지 다시 읽는다. PR 본문은 §8-8 순서(결론 / 사장님이 반드시 볼 부분 / 확인한 부분 / 확인 못 한 부분 / 근거·결정 카드·롤백·증거)로 gh pr edit 100 --body-file. "#97 병합 전까지 Draft" 유지. 승인이 없으면 NOT_RUN 으로 기록하고 끝낸다. 자격증명·후보 원문·키 값은 본문에 넣지 않는다.

중단 조건: 0단계 불일치 / 작업 중 git status 에 내가 만들지 않은 변경(다른 세션) / 검사기 FAIL / 변이 생존 / 리뷰 REQUEST_CHANGES. 어느 하나면 §8 형식으로 보고하고 멈춘다.

비범위: 계약 문서 내용 변경, CI 재배선, storage_schema.py, 마이그레이션, HS-03.03 암호화, HS-03.04 readback, #96 연동, merge.

완료 보고(§8): 결론(전문용어 0) → 판단 근거 → 증거 원문. 첫 줄에 최종 HEAD SHA, push 여부, 리뷰 판정, WU-D 재현 여부(REPRODUCED / NOT_REPRODUCIBLE). 다음 프롬프트(HS-03.03 암호화 저장)는 docs/engineering/goal-prompts/ 에 파일로 남긴다.
```

→ 이 프롬프트는 끝난 일을 다시 만들지 않고, 남은 네 가지(DB 경계 결함 재현·수정, 머리글 숫자, 최종 독립 검토, 승인 뒤 PR #100 갱신)만 한다. 0단계는 고정값 대신 실측 기록으로 바꿔 다른 세션이 그 사이 push 했어도 오판하지 않는다.

## 2026-09-15 14:51 실측 상태 (이 프롬프트를 쓴 시점)

| 항목 | 값 |
|---|---|
| HEAD | c14638d 13:28 "필수 시험 명부 건수를 하한이 아니라 정확한 기대값으로 본다" |
| efaefab..HEAD | 21 커밋 (2라운드 GREEN·3라운드·5~6차 장부 포함) |
| 원격 | origin 69648d4, 로컬이 5커밋 앞 (13:41 실측) |
| PR | #100 OPEN Draft, base task/hs-0301-sqlite-schema-20260914, head 69648d4 (13:41 gh 실측) |
| 다른 세션 | 13:37:12 시작 셸(PID 3797)이 인수·G2 변이·pytest·ruff·mypy 실행. 14:51 재확인 시 종료됨. index 13:36:22 이후 변경 없음 |
| 장부 | 6차 재검증 PASS(인수 CHECKED 22·G2 6/6·311 passed), "V1 (5차) NOT_RUN", "push·Draft PR NOT_RUN" |
| 정본 머리글 | "스텝 26개" vs 표 27행 vs name 28개 |
| Codex 높음 결함 | DB 쓰기 직전 권한·위치 미검증 (Codex 읽기 전용 확인, 실제 기록은 NOT_RUN) |

→ 이 표가 0단계의 비교 기준이다. 값이 달라져 있으면 다른 세션이 그 사이 일한 것이므로 새 값을 기록하고 그 기준으로 다시 잰다.
