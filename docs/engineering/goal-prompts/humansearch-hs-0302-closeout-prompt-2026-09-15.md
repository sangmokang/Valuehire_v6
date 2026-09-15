# 착수 프롬프트 — HS-03.02 마감: CI 배선·계약 정합·독립 리뷰·PR 준비 (2026-09-15)

## 결론

HS-03.02(후보 동일성·중복 방지)는 검증자(Codex)가 계약·시험·구현을 한 워크트리에서 진행 중이다. 1라운드는 커밋됐고, 2라운드(Codex V1 결함 4건) RED가 11:11에 커밋된 뒤 GREEN이 진행 중이다. Claude 세션은 그 작업이 끝난 뒤에만 들어가며, 남은 일 세 가지를 맡는다. (1) 새 인수 스크립트의 CI 배선, (2) 계약 문서와 구현의 정합, (3) 작성자와 다른 쪽이 하는 독립 리뷰. push와 PR은 리뷰 판정과 사장님 승인 뒤에만 한다.

아래를 새 세션에 그대로 붙여넣는다.

```text
$strict

역할: 너는 HS-03.02의 마감 담당이다. 후보 식별키 모듈·시험·계약은 검증자(Codex)가 작성했다. 그 코드의 동작을 바꾸지 않는다. 네가 만드는 것은 CI 배선과 문서 정합뿐이고, 마지막에 작성자와 다른 눈으로 독립 리뷰를 한다. "통과했다"는 문장 대신 명령·종료값·출력 원문만 기록한다.

저장소: /Users/kangsangmo/Desktop/Valuehire_v6
작업 위치: /Users/kangsangmo/Desktop/Valuehire_v6/worktrees/hs-0302-candidate-identity-20260914 (브랜치 task/hs-0302-candidate-identity-20260914, 스택 베이스 task/hs-0301-sqlite-schema-20260914 @7473ec8 = PR #97)
메인 작업트리·다른 워크트리 수정 금지.

0. 착수 조건 (하나라도 어긋나면 착수하지 않고 그대로 보고한다 — 검증자 세션이 아직 작업 중이라는 뜻이다)
pwd; git branch --show-current                    → task/hs-0302-candidate-identity-20260914
git status --short                                → 출력 없음 (미커밋·스테이지 파일이 하나라도 있으면 중단)
git log --format='%h %ci %s' -8                   → efaefab(11:11 "Codex V1 결함 4건을 시험으로 먼저 고정한다") 뒤에 GREEN 커밋이 하나 이상 있어야 한다. HEAD가 efaefab 그대로면 2라운드가 끝나지 않은 것이므로 중단.
stat -f '%Sm' -t '%F %T' "$(git rev-parse --git-dir)/index"   → 현재 시각보다 10분 이상 이전이어야 한다(그보다 최근이면 다른 세션이 살아 있다고 보고 중단).
cd humansearch && uv run --frozen pytest -q 2>&1 | tail -1   → "N passed", failed 0. (2026-09-15 11:13 실측은 2라운드 RED 상태라 32 failed 262 passed였다. GREEN 뒤 값을 기록한다)
uv run --frozen ruff check src tests && uv run --frozen mypy src tests → 통과
cd .. && bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-0302.sh → "OK(run-acceptance)… CHECKED N", 종료값 0
git config core.hooksPath                         → hooks
위 값을 전부 기록한 뒤에만 1단계로 간다.

1. 프롬프트 회수 커밋
이 파일은 worktrees/hs-prompts-20260915/docs/engineering/goal-prompts/ 에 있다. 같은 경로로 복사하고 커밋한다: "HS03.02 마감 착수 프롬프트를 저장소에 둔다". git show --stat HEAD 에 파일 1개만.

2. WU-A — 인수 스크립트 CI 배선 (P15③: 로컬에만 있는 검사는 없는 것으로 친다)
현재 scripts/acceptance-hs-0302.sh 는 verify.yml 에도 docs/sot/verification-commands.md 표에도 없다(2026-09-15 11:13 grep 0건). 정본 55행 규칙대로 양쪽에 넣는다.
- .github/workflows/verify.yml 의 "HumanSearch G2 테스트 게이트" 스텝 바로 뒤에 이름 있는 스텝 "HumanSearch HS-03.02 후보 식별키 계약" 추가. 본문 한 줄: bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-0302.sh. if·continue-on-error·echo 대체 금지. uv 는 G2 스텝이 이미 설치·고정하므로 다시 설치하지 않는다.
- docs/sot/verification-commands.md 표에 같은 순서로 한 행 추가. 문서 머리의 "이름 있는 스텝 N개" 를 실측으로 고친다.
RED 먼저: 배선 전에 아래 AC-A1 명령을 돌려 "없음"을 기록한다(음성 대조군).
AC-A1: /usr/bin/grep -c 'acceptance-hs-0302.sh' .github/workflows/verify.yml → 1 ; 같은 grep 을 docs/sot/verification-commands.md → 1 이상.
AC-A2: /usr/bin/grep -c '^      - name:' .github/workflows/verify.yml 값 = 표 행 수 = 문서 머리 숫자. 세 값을 원문으로 붙인다.
AC-A3: bash scripts/acceptance-ci-step-integrity.sh → VERDICT: PASS, CHECKED: 24.
AC-A4: bash scripts/acceptance-principles-check.sh → CHECKED: 34, rc 0.
커밋: "HS03.02 인수 검사를 CI 와 검증 정본에 배선한다"

3. WU-B — 계약 문서와 구현의 정합
2라운드 시험(test_hs_0302_r2_hardening.py)은 HMAC 메시지를 길이 접두(length prefix) 방식으로, 제어문자 거부, 키 폴더와 DB 루트의 상호 중첩 거부, observed_at 달력·오프셋 범위 검사를 요구한다. 계약 문서 docs/engineering/humansearch-hs-0302-candidate-identity-goal-2026-09-15.md 51행은 아직 "\x1f 구분자" 정의다. 문서를 구현에 맞추되, 계약을 바꾸는 것이므로 "2026-09-15 2라운드 개정" 소제목 아래에 무엇이 왜 바뀌었는지 5줄 카드(무엇을/왜/버린 대안/대가/되돌리기)로 적는다. 기존 문장은 지우지 않고 취소선 없이 "개정 전" 표기로 남긴다.
AC-B1: 계약 문서의 HMAC 정의 문장과 humansearch/src/humansearch/candidate_identity.py 의 candidate_key_hmac 본문이 같은 방식이다. 확인 명령: 시험 파일의 독립 계산 함수(_independent_key_hmac 계열)가 참조하는 방식과 문서 문장을 나란히 붙이고, uv run --frozen pytest tests/test_hs_0302_candidate_identity.py tests/test_hs_0302_r2_hardening.py -q → 전부 passed.
AC-B2: 계약 문서 31행 기준 시험 수(241)를 지우지 말고 "2026-09-15 실측: <N> passed" 를 옆에 적는다.
AC-B3: bash ~/.claude/skills/strict/brief-lint.sh <계약 문서> → 위반 0 (홈 폴더 검사라 회사 차원 근거 아님).
커밋: "HS03.02 계약 문서를 2라운드 구현에 맞춘다"

4. WU-C — 독립 리뷰 (작성자와 다른 쪽이 한다)
/humanreview 로 7473ec8..HEAD 를 읽기 전용 리뷰한다. 최소 공격 목록:
- 키 폴더가 DB 보호 루트의 하위 폴더일 때 거부되는가 (1라운드 모듈은 "같은 폴더"만 막았고 하위 폴더는 허용했다 — 2026-09-15 11:12 탐침 실측). r2 시험이 이를 고정했는지, 격리 사본에서 그 검사를 지우면 시험이 실패하는지.
- HMAC 길이 접두 제거 변이·제어문자 검사 제거 변이·IntegrityError 전부 duplicate 변이·기본키 제약 제거 변이 — 각각 격리 사본에서 실패해야 한다.
- 인수 스크립트를 "true" 로 치환 / CHECKED 위조 / pytest 호출 제거 — run-acceptance 또는 스크립트 자체가 FAIL 인가.
- 오류 메시지에 position_ref·candidate_ref·키 바이트·HMAC 값이 섞이지 않는가 (예외 메시지 전수 grep).
- AC-3 경쟁 시험이 실제로 서로 다른 연결 2개를 쓰는가.
판정은 APPROVE / REQUEST_CHANGES / NOT_RUN 중 하나. 결함은 파일:줄·재현 입력·영향·최소 수정 방향과 함께 적고, 유효 반례는 회귀 시험 편입 후보로 남긴다. REQUEST_CHANGES 면 여기서 멈추고 보고한다 — 고치지 않는다(수정은 작성자 몫).

5. push·Draft PR (APPROVE 이고 사장님이 이 세션에서 명시적으로 승인한 경우에만)
git push -u origin task/hs-0302-candidate-identity-20260914
gh pr create --draft --base task/hs-0301-sqlite-schema-20260914 --title "HS03.02 후보 식별키 중복 없는 기록" --body-file <본문 파일>
본문에 base/head SHA, diff 줄 수, 검증 명령 원문과 종료값, "#97 병합 전까지 Draft", 리뷰 판정을 넣는다. 승인이 없으면 이 단계는 NOT_RUN 으로 기록하고 끝낸다. 자격증명·후보 원문·키 값은 본문에 넣지 않는다.

중단 조건: 0단계 불일치 / 작업 중 git status 에 내가 만들지 않은 변경이 생김(다른 세션) / 검사기 FAIL / 변이 생존 / 리뷰 REQUEST_CHANGES. 어느 하나면 §8 형식으로 보고하고 멈춘다.

비범위: candidate_identity.py·시험 파일·인수 스크립트 본문 수정, storage_schema.py, 마이그레이션, HS-03.03 암호화, HS-03.04 readback, #96 연동, merge.

완료 보고(§8): 결론(전문용어 0) → 판단 근거 → 증거 원문. 첫 줄에 HEAD SHA, push 여부, 리뷰 판정. 다음 프롬프트(HS-03.03 암호화 저장, 같은 역할 분리 방식)는 docs/engineering/goal-prompts/ 에 파일로 남긴다.
```

→ 이 프롬프트는 검증자가 만든 코드에 손대지 않고 빠진 배선과 문서 정합만 채운 뒤, 작성자와 다른 쪽이 리뷰하고, push·PR은 승인 뒤로 미룬다. 착수 조건이 어긋나면 다른 세션이 아직 작업 중이라는 뜻이므로 들어가지 않는다.

## 2026-09-15 11:13 실측 상태 (이 프롬프트를 쓴 시점)

| 항목 | 값 |
|---|---|
| HEAD | efaefab 11:11 "Codex V1 결함 4건을 시험으로 먼저 고정한다" (2라운드 RED) |
| 커밋 사슬 | 7473ec8(#97) → 23a4890 goal → 838577b RED → 4f51ca6 GREEN → 9ac10f9 장부 → efaefab r2 RED |
| pytest 전체 | 32 failed, 262 passed (r2 RED 상태) |
| 1라운드 GREEN(9ac10f9) 재실행 | 0302 시험 28 passed, 전체 257 passed, ruff·mypy 통과 |
| 인수 스크립트 | 1라운드 기준 CHECKED 11 PASS. r2 RED 상태에서는 pytest 구간 FAIL(정상) |
| CI 배선 | verify.yml·정본 표에 acceptance-hs-0302.sh 없음 |
| 원격 | 미푸시, PR 없음 (#97 Draft만 열림) |
| 탐침 | 키 폴더가 DB 루트 하위(protected-root/keys)일 때 1라운드 모듈이 허용 → r2 시험 test_key_directory_nested_under_db_protected_root_is_refused 가 고정 |

→ 이 표는 프롬프트를 쓴 시점의 실측이다. 2라운드가 진행 중이라 pytest 실패는 정상이고, 착수 조건은 이 값들이 GREEN 커밋으로 바뀐 뒤에만 충족된다. HMAC 은 r2 에서 v2(길이 접두)로 바뀌었으므로 계약 문서 51행 개정이 필요하다.
