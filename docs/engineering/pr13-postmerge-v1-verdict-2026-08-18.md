VERDICT: FAIL

# 결론

지금 상태로는 올리거나 합치면 안 됩니다. 안내 문구와 그 문구를 검사하는 시험은 요구대로 동작했지만, 전체 28개 검사 중 2개를 이 격리 환경에서 끝까지 통과시키지 못했습니다.

확인된 코드 결함은 없습니다. 다만 “모든 검사가 통과했다”는 핵심 조건을 제가 직접 재현하지 못했으므로, 안전하다고 승인할 근거가 부족합니다.

## 이번 판정에서 건너뛴 것·확인하지 못한 것·다시 한 것

- 확인하지 못함: GitHub PR #13의 현재 서버 검사 상태와 실제 합치기 가능 상태는 외부 조회를 하지 않았습니다. ※ 이 문서는 로컬 커밋과 로컬 실행 결과만 판정합니다.
- 확인하지 못함: `acceptance-hs-gates-mutations.sh`의 여섯 고장 표본은 격리 환경이 사용자 홈의 `uv` 저장 공간을 열지 못했고, 새 임시 저장 공간에서는 외부 주소 조회가 막혀 끝까지 실행되지 않았습니다.
- 건너뜀: 실제 push와 PR 병합은 검증 역할과 안전 제한상 실행하지 않았습니다.
- 다시 한 것: 첫 `session-status.sh` 출력 포착은 장기 실행 회수 방식 때문에 두 차례 3번째 줄 전에 끊겼습니다. 장기 세션으로 다시 실행해 처음에는 `RED: 3/28`, 모든 다른 검사가 끝난 뒤 단독으로 다시 실행해 최종 `RED: 2/28`을 얻었습니다.
- 다시 한 것: 병합 파일 안의 훅 관련 문구 검색은 첫 명령에서 여러 파일명을 한 인자로 넘겨 실패했습니다. 파일명을 0바이트 구분으로 넘기는 방식으로 즉시 재실행했습니다.
- 다시 한 것: 기존 가상환경을 임시 폴더로 복사해 변조 검사를 실행하려던 보조 명령은 안전 장치가 임시 폴더 삭제 명령을 거부해 시작되지 않았습니다. 저장소 내용은 바뀌지 않았습니다.
- 범위 제한: 커밋 `7406c633…`의 비실행 증거 문서 추가분 1,146줄은 실행 계약이 아니므로 줄별 내용 판정에는 쓰지 않았습니다. 전체 커밋의 변경 파일과 줄 수는 확인했고, 훅과 회귀 시험의 실제 diff는 전문을 다시 읽었습니다.

# 판단 근거

## 왜 FAIL인가

요청의 가장 중요한 갈림길은 “코드에서 결함을 찾지 못했으니 승인할 것인가”와 “필수 전체 검사를 직접 통과시키지 못했으니 승인을 보류할 것인가”였습니다. 저는 후자를 골랐습니다. 사용자가 `RED: 0/28`의 직접 재현을 명시했고, 제 최종 단독 실행은 `RED: 2/28`이었기 때문입니다.

버린 해석은 “두 실패가 격리 환경 탓으로 설명되므로 전체 통과로 간주한다”입니다. 두 실패가 `uv` 캐시(파이썬 도구가 받은 파일을 보관하는 공간) 접근 제한에서 시작됐다는 사실은 확인했지만, 원래 명령의 실제 결과가 통과로 바뀌지는 않습니다. 기본 G3 검사는 허용된 임시 저장 공간을 썼을 때 통과했으나, 고장 표본 검사는 외부 주소 조회 실패로 여전히 끝까지 실행되지 않았습니다.

이 판정이 틀려 실제 코드가 안전하다면 생기는 손해는 push와 병합이 늦어지는 것입니다. 반대로 검증 공백을 통과로 잘못 인정하면, 고장 난 시험을 잡아야 하는 검사가 실제로 작동하는지 확인하지 않은 채 변경을 합치게 되어 이후 HumanSearch 검사 결과를 믿을 근거가 약해집니다.

## 요구사항별 판정

| ID | 요구 | 판정 | 직접 근거 | 남은 공백 | 영향 |
|---|---|---|---|---|---|
| AC1 | 0-2, 0-5, 0-7을 서로 다른 문구로 표시하고 각 건너뛰기 동작을 유지 | PASS | 직접 `pre-push` 실행에서 세 문구 전문 출력, `hooks/pre-push:140-150`의 각 `continue` 확인 | 없음 | 결함을 그대로 두면 운영자가 검사 책임자를 잘못 이해합니다. 현재는 바로잡혔습니다. |
| AC2 | 회귀 시험이 실제 훅을 실행하고 세 문구를 엄격히 확인하며 실패를 성공으로 흘리지 않음 | PASS | `acceptance-0-7.sh` 종료 0, `scripts/acceptance-0-7.sh:126` 실제 실행, `:134-150` 세 고정 문자열 검사와 최종 종료 1 경로 확인 | 수정 전 훅을 실제로 주입한 별도 RED 재현은 이번 감사에서 새로 만들지 않음 | 결함을 그대로 두면 댓글이나 죽은 문자열만 있어도 합격할 수 있습니다. 현재 코드에서는 그 우회가 확인되지 않았습니다. |
| AC3 | 병합된 4개 커밋이 훅·계약·설치·전체 검증 경로를 손상하지 않음 | 코드·문서 직접 변경은 PASS, 전체 실행 재현은 불충분 | 병합 전후 보호 파일 6개의 저장 객체 번호가 동일, 병합 파일 10개 목록 확인, 새 SOT 전문 확인 | 전체 합계가 `2/28`; 고장 표본 검사 미완료 | 이 공백을 무시하면 새 HumanSearch 의존성과 기존 검사 흐름의 결합 문제를 놓칠 수 있습니다. |
| V1 최종 | 커밋을 push하고 PR #13을 병합해도 안전한가 | FAIL | 최종 `session-status.sh`: `RED: 2/28`; 직접 `pre-push`: 종료 1 | 두 실패의 코드 결함 여부는 환경 제한 때문에 확정하지 못함 | 승인하면 필수 독립 검증을 마치지 않은 변경이 합쳐질 수 있습니다. |

→ 무엇을 비교했나: AC1~AC3의 코드·실행 증거와 최종 승인 조건을 나란히 비교했습니다. / 무엇이 나왔나: AC1·AC2는 통과했고 AC3의 직접 변경도 안전했지만, 전체 실행 재현 공백 때문에 최종 승인은 실패입니다.

## 버린 해석과 선택 이유

1. “`session-status.sh` 종료값이 0이므로 전체 합격”은 버렸습니다. 이 스크립트는 하위 실패 수를 3번째 줄로 보고하면서도 Git 조회가 정상이면 종료 0을 낼 수 있고, 실제 출력은 `RED: 2/28`이었습니다.
2. “직접 `pre-push` 종료 1이 훅 수정 결함”은 버렸습니다. 세 라벨과 24개 검사는 정상 출력됐고, 막힌 두 스크립트의 직접 출력은 모두 동일한 홈 저장 공간 권한 오류였습니다.
3. “새 HumanSearch 계약 문서가 훅 계약을 바꿨다”는 해석은 버렸습니다. `docs/sot/INDEX.md`는 새 링크 한 줄만 추가했고, `docs/sot/hook-contracts.md`의 저장 객체 번호는 병합 전후 같았습니다.
4. “코드 결함을 찾지 못했으니 최종 PASS”는 버렸습니다. 이 감사의 성공 조건에는 코드 검토뿐 아니라 전체 28개 직접 통과 재현이 포함됐습니다.

# 적대 반증 시도

## AC1 반증 시도

`continue`가 빠져 건너뛴 검사가 실행 목록에 다시 들어가거나, 기존 `PUSH-PERFORMING` 표시가 훼손됐는지 직접 훅 실행과 줄 단위 대조로 깨뜨리려 시도했으나 실패했습니다. 세 문구가 요구한 그대로 먼저 출력됐고, 0-2·0-5·0-7을 뺀 26개만 실행됐으며 세 분기 모두 `continue`를 유지했습니다.

## AC2 반증 시도

회귀 시험이 댓글만 읽거나 항상 참인 검색을 쓰거나 실패 뒤에도 종료 0으로 새는지 실제 실행과 제어 흐름 대조로 깨뜨리려 시도했으나 실패했습니다. 시험은 `bash hooks/pre-push`를 실행한 파일을 읽고, 세 개의 정확한 고정 문자열 중 하나라도 없으면 `fail=1`을 세운 뒤 종료 1을 냅니다.

## AC3 반증 시도

병합 4건이 `pre-push`, `acceptance-0-7`, 훅 계약, 설치 스크립트, 전체 검증 스크립트, 서버 검증 설정을 몰래 바꿨는지 변경 파일 목록과 병합 전후 저장 객체 번호로 깨뜨리려 시도했으나 실패했습니다. 여섯 파일은 모두 동일했습니다.

추가로 새 HumanSearch 코드와 의존성이 기존 G3 검사에 간접 영향을 주는지 실행으로 깨뜨리려 시도했습니다. 기본 G3 검사는 임시 저장 공간을 지정하자 25개 시험까지 통과했지만, 고장 표본 검사는 격리 환경의 주소 조회 제한으로 끝까지 실행되지 않아 이 추가 반증은 미완료입니다.

# 기술 상세와 증거 원문

## 1. 대상 커밋과 브랜치

```text
$ git rev-parse HEAD
$ git branch --show-current
$ git status --short --branch
$ git show --stat --oneline 7406c633395d943d28a6c24822f48d32160c1cfd
$ git diff --check 7406c633395d943d28a6c24822f48d32160c1cfd^ 7406c633395d943d28a6c24822f48d32160c1cfd
7406c633395d943d28a6c24822f48d32160c1cfd
task/humansearch-g3-portal-constants
## task/humansearch-g3-portal-constants...origin/task/humansearch-g3-portal-constants [ahead 6]
7406c63 fix(hooks): pre-push 안내 문구를 LOCAL-MANUAL/POST-PUSH로 분리하고 acceptance-0-7.sh에 실행 기반 회귀 시험 추가
 .../codeaudit-g3-followup-goal-2026-08-15.md       | 1146 ++++++++++++++++++++
 hooks/pre-push                                     |    8 +-
 scripts/acceptance-0-7.sh                          |   59 +
 3 files changed, 1211 insertions(+), 2 deletions(-)
COMMIT_DIFF_CHECK_EXIT=0
```

→ 뭘 시켰나: 현재 위치·브랜치·변경 통계와 diff 형식 오류를 확인했습니다. / 뭐가 나왔나: 요청한 커밋과 브랜치가 맞고, 원격 작업 브랜치보다 6커밋 앞서며 diff 형식 오류는 없습니다. / 좋은 소식인가 나쁜 소식인가: 대상 고정과 diff 형식에는 좋은 소식입니다.

## 2. 커밋 `7406c633…`의 실행 파일 실제 diff 전문

```diff
commit 7406c633395d943d28a6c24822f48d32160c1cfd
Author:     acceptance <acceptance@local>
AuthorDate: Tue Aug 18 21:54:57 2026 +0900
Commit:     acceptance <acceptance@local>
CommitDate: Tue Aug 18 21:54:57 2026 +0900

    fix(hooks): pre-push 안내 문구를 LOCAL-MANUAL/POST-PUSH로 분리하고 acceptance-0-7.sh에 실행 기반 회귀 시험 추가
    
    외부 P0 작업의 로컬 main 미동기화로 acceptance-0-5가 3회 연속 BLOCKED됐던 상태 해소.
    origin/main(b6aee6a) 병합 후 28/28 RED 재확인, 지문(unstaged diff) 병합 전후 동일 확인.
    
    Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>

diff --git a/hooks/pre-push b/hooks/pre-push
index 33ebb61..636d15b 100755
--- a/hooks/pre-push
+++ b/hooks/pre-push
@@ -141,8 +141,12 @@ while IFS= read -r c; do
     continue
   fi
   case "$(basename "$c")" in
-    acceptance-0-2.sh|acceptance-0-5.sh)
-      printf '  skip %s (DEFERRED · CI 담당)\n' "$c" >&2
+    acceptance-0-2.sh)
+      printf '  skip %s (LOCAL-MANUAL · push 시점 제외)\n' "$c" >&2
+      continue
+      ;;
+    acceptance-0-5.sh)
+      printf '  skip %s (POST-PUSH · CI 담당)\n' "$c" >&2
       continue
       ;;
   esac
diff --git a/scripts/acceptance-0-7.sh b/scripts/acceptance-0-7.sh
index b14195e..f8a1f0f 100755
--- a/scripts/acceptance-0-7.sh
+++ b/scripts/acceptance-0-7.sh
@@ -86,6 +86,15 @@ cd "$sandbox/repo"
 git remote add sandbox "$sandbox/remote.git"
 git config user.email "acceptance@local"
 git config user.name "acceptance"
+# 커밋 전 RED→GREEN도 시험할 수 있도록 clone의 옛 훅 대신 원본 작업트리의 현재 훅을 쓴다.
+# 변형 시험이 옛 훅을 넣은 별도 원본 clone에서 이 스크립트를 실행하면 그 옛 훅이 복사되므로
+# 같은 경로로 수정 전/후를 양방향 대조할 수 있다.
+cp "$REPO_ROOT/hooks/pre-push" hooks/pre-push
+git config core.hooksPath /dev/null
+git add hooks/pre-push
+if ! git diff --cached --quiet; then
+  git commit -qm "fixture: current pre-push under test"
+fi
 bash scripts/install-hooks.sh >/dev/null 2>&1 || { echo "FAIL: install-hooks.sh 실패"; exit 1; }
 
 hp=$(git config --get core.hooksPath) || hp=""
@@ -93,6 +102,56 @@ hp=$(git config --get core.hooksPath) || hp=""
 [ -x hooks/pre-commit ] || { echo "FAIL: clone 에서 pre-commit 실행 권한 없음"; exit 1; }
 
 BASE=$(git rev-parse HEAD)
+
+# pre-push가 직접 실행하지 않는 두 검사의 소유자를 같은 말로 뭉개면 안 된다.
+# 주석·죽은 문자열로 가짜 합격하지 않도록 훅을 실제 실행한다. 다른 인수 스크립트는
+# 이 문구 시험의 잡음이 되지 않게 샌드박스 안에서만 성공 스텁으로 바꾼다.
+echo "=== pre-push 예외 안내 실실행 ==="
+git config core.hooksPath /dev/null
+for f in scripts/acceptance-*.sh; do
+  case "$(basename "$f")" in
+    acceptance-0-7.sh)
+      printf '#!/usr/bin/env bash\n# PUSH-PERFORMING\nexit 0\n' > "$f"
+      ;;
+    *)
+      printf '#!/usr/bin/env bash\nexit 0\n' > "$f"
+      ;;
+  esac
+done
+printf '#!/usr/bin/env bash\nexit 0\n' > verify.sh
+chmod +x verify.sh scripts/acceptance-*.sh
+git add verify.sh scripts/acceptance-*.sh
+git commit -qm "fixture: pre-push skip labels"
+set +e
+bash hooks/pre-push </dev/null >"$outdir/prepush-labels" 2>&1
+labels_rc=$?
+set -e
+if [ "$labels_rc" -ne 0 ]; then
+  echo "FAIL: pre-push 안내 실실행 실패(exit=$labels_rc)"
+  sed 's/^/       /' "$outdir/prepush-labels" | head -10
+  fail=1
+fi
+if ! grep -qF 'skip ./scripts/acceptance-0-2.sh (LOCAL-MANUAL · push 시점 제외)' "$outdir/prepush-labels"; then
+  echo "FAIL: pre-push가 acceptance-0-2.sh를 로컬 수동 검사로 안내하지 않는다"
+  fail=1
+fi
+if ! grep -qF 'skip ./scripts/acceptance-0-5.sh (POST-PUSH · CI 담당)' "$outdir/prepush-labels"; then
+  echo "FAIL: pre-push가 acceptance-0-5.sh를 push 뒤 CI 검사로 안내하지 않는다"
+  fail=1
+fi
+if ! grep -qF 'skip ./scripts/acceptance-0-7.sh (PUSH-PERFORMING · CI 담당)' "$outdir/prepush-labels"; then
+  echo "FAIL: pre-push가 PUSH-PERFORMING 검사를 CI 담당으로 안내하지 않는다"
+  fail=1
+fi
+git reset -q --hard "$BASE"
+git config core.hooksPath hooks
+if [ "$fail" -ne 0 ]; then
+  echo; echo "RESULT: pre-push 예외 안내 계약 불일치 — 시연을 진행하지 않는다. exit 1"
+  exit 1
+fi
+echo "OK: 실제 pre-push 출력이 로컬 수동/사후 CI/PUSH-PERFORMING을 구분함"
+echo
+
 echo "=== 시연 (샌드박스: $sandbox/repo · 각 시연마다 훅 ON/OFF 대조) ==="
 
 reset_tree() {
```

→ 뭘 시켰나: 1,211줄짜리 전체 커밋 중 동작을 바꾸는 두 실행 파일만 경로로 좁혀 `git show`를 다시 실행했습니다. / 뭐가 나왔나: 훅 8줄과 회귀 시험 59줄의 전체 diff가 나왔습니다. / 좋은 소식인가 나쁜 소식인가: AC1·AC2에는 좋은 소식입니다. 전체 무제한 출력은 1,263줄이라 도구 화면에서 잘렸으므로 비실행 증거 문서는 판정 근거로 쓰지 않았습니다.

## 3. 요청한 범위 로그와 실제 병합 4건

```text
$ git log --oneline --decorate b6aee6a..7406c633395d943d28a6c24822f48d32160c1cfd
7406c63 (HEAD -> task/humansearch-g3-portal-constants) fix(hooks): pre-push 안내 문구를 LOCAL-MANUAL/POST-PUSH로 분리하고 acceptance-0-7.sh에 실행 기반 회귀 시험 추가
7c648b9 merge origin/main(b6aee6a) — PR#13 재개: 외부 P0 차단 해소 확인 후 최신 기본선 반영
f27af82 (origin/task/humansearch-g3-portal-constants) 최신 기본선의 비밀 검사 보호와 G3를 하나의 검증 흐름으로 보존한다
918f0b6 원격 검증 증거로 G3 배송 게이트를 닫는다
a3cd568 적대 검증의 실패와 최종 반증을 함께 고정한다
852ea28 실행되지 않는 명령을 명부 증거에서 끝까지 제외한다
0b2fd04 꺼진 실행 단계를 명부 근거로 믿는 허점을 재현한다
d1d17a9 명부 검사의 자기배선 주석 옆문을 재현한다
42c4503 명부가 실제 실행과 현재 강제력만 증명하게 한다
6e7e5c8 주석을 실행 증거로 믿는 명부 허점을 재현한다
3c7fd38 fix(G3): YAML.safe_load 위치인자→키워드 인자 — CI Ruby 3.2(Psych 4) 호환
6b95417 docs(G3): 최종 검증 사슬 로그 — 실행 무력화 부류 봉쇄(V2 PASS)·잔여 한계 6종 기재
610f179 G3 GREEN11: matrix 최종 조합 수 계산(곱집합-exclude, include 보수적)해 0이면 거부 — matrix 0회실행 부류 봉쇄
22a147f G3 RED11: hardening6 — exclude로 유일 조합 제거 등 최종 조합 0개 우회 미탐 재현 (V2 8차)
02b8fc4 G3 GREEN10: G3 작업의 strategy.matrix 빈 축·정적판정불가 형태 거부 (fail-closed)
2b33b83 G3 RED10: hardening6 — 빈 strategy.matrix로 작업 0회 실행되는 우회 미탐 재현 (V2 발견)
0a25f73 G3 GREEN9: working-directory 3위치 거부 + env의 BASH_ENV·ENV·SHELLOPTS·PATH 거부 + runs-on 값 계약(비어있지 않은 문자열/목록)
002bccd G3 RED9: hardening6 — working-directory 3위치·BASH_ENV 3위치·runs-on 빈값 3종 미탐 재현 (V1 6차 G6-1~3)
d06a88a G3 GREEN8: G3 단계 shell 키·작업/파일 defaults.run.shell 거부 + runs-on 필수화
1dc458d G3 표본 조정: 정상 표본에 runs-on 추가 — 공격 내용·기대 exit code 불변 (동결 예외 원칙 동일)
cbef7d3 G3 RED8: hardening6 — shell 바꿔치기 3위치·runs-on 누락을 검사기가 승인하는 미탐 재현 (V1 5차 판정)
201baa5 G3 GREEN7: 작업 수준 if/continue-on-error 거부 + on: push·pull_request 필수화 + hardening6 CI 등록
dc91fa3 G3 동결 예외: N3 규칙 성립 위해 정상 표본 생성 줄에 on: push·pull_request 추가 — 공격 내용 불변
f4115e0 G3 RED7: hardening6 — 작업 수준 if·continue-on-error·수동 전용 트리거를 검사기가 승인하는 미탐 재현 (V1 4차 N1~N3)
912aa79 G3 GREEN6: CI 배선 판정을 YAML 구조 해석으로 교체 — jobs.*.steps[*].run만 실행 칸으로 인정
ae5d501 G3 RED6: hardening5 — 실행 칸 밖 YAML 값·의미상 동일 탐색 명령을 검사기가 승인하는 미탐 재현
9655afb docs(G3): PR #13 적대검증 판정 보존 — V1(codex FAIL 11건)·V2·V3 교차 + Claude 자기정정
f10c8c4 G3 docs: record codeaudit A2 finding and round-5 literal-scalar closure
f3d4be3 G3 GREEN5 docs: register hardening3/4 in the SOT CI step table
3f9ee88 G3 GREEN5: exclude every non-run literal scalar block from the exec lane
f4b4bae G3 RED5: codeaudit exposes literal-scalar CI bypass beyond env
11d6989 G3 docs: preserve round-3 verdict verbatim plus round-4 remediation and residual-limit card
30270fd G3 GREEN4: parse the CI run block by indentation and exclude env subtrees
09c19b4 G3 RED4: third adversarial round exposes env-carrier CI bypass and semantic locators
bcf804a G3 docs: preserve round-2 verdict verbatim plus round-3 remediation ledger
918b882 G3 GREEN3: allowlist the CI step block and widen pattern categories
8e00bff G3 RED3: second adversarial round exposes ten expressions and a shell-wrap CI bypass
fb512e1 G3 docs: record codeaudit cross-check and the product-tier boundary limit
4119413 G3 docs: preserve V1 verdict verbatim plus V2 reproduction ledger
dfccaa7 G3 GREEN2: close all five V1-confirmed gaps in the portal-constants gate
37d2fa7 G3 RED2: hardening contract exposes five confirmed V1 defects
e80a50a G3 docs: satisfy briefing-contract lint (0 violations)
7f589d6 G3 docs: record Gate 4 verification outputs in goal document
b3a3db0 G3 GREEN: portal constants and locators are contracts-only data
9bab751 G3 RED: portal-constants mutation contract fails on missing gate
```

→ 뭘 시켰나: 사용자가 지정한 범위를 그대로 조회했습니다. / 뭐가 나왔나: 이 범위는 병합 4건만이 아니라 기준 커밋의 다른 계보에 있던 PR #13 기존 커밋들도 함께 보여 줬습니다. / 좋은 소식인가 나쁜 소식인가: 명령은 정상이나, 이 출력만으로 “병합 4건”을 고르면 잘못이므로 병합 부모를 추가로 분리했습니다.

```text
$ git show -s --format='MERGE=%H%nPARENTS=%P%nSUBJECT=%s' 7c648b9
$ git log --oneline 7c648b9^1..7c648b9^2
MERGE=7c648b9321002ddbd641fdb3dabe2ccaf9a5ee9c
PARENTS=f27af8237b5f30a07f3619f2a69c7d01f3fc15eb b6aee6a352309cfd721cd3b3d63d31ff7c0787f9
SUBJECT=merge origin/main(b6aee6a) — PR#13 재개: 외부 P0 차단 해소 확인 후 최신 기본선 반영
b6aee6a 다음 화면 판독이 인증 상태를 과장하지 않도록 L0 계약을 고정한다
ab851a2 docs(engineering): P0 구현 V1 적대 검증 PASS — 판정·재현 증거 장부 append Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
1e0f805 docs(engineering): P0 보완판 — 샌드박스 면제 범위 4파일 전체로 확대(밖 검증 실측 근거) + 재개 지점 S4 Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
8cd1e9e docs(engineering): P0 보완판 — 재개 지점을 실커밋 기준으로 갱신 Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
```

→ 뭘 시켰나: 병합 커밋의 두 부모를 확인하고 첫 부모에는 없고 둘째 부모에만 있는 커밋을 열거했습니다. / 뭐가 나왔나: 요청에 적힌 병합 유입 4건이 정확히 분리됐습니다. / 좋은 소식인가 나쁜 소식인가: AC3 범위를 정확히 고정한 좋은 소식입니다.

## 4. 병합 유입 4건의 `git show --stat` 전문

```text
b6aee6a 다음 화면 판독이 인증 상태를 과장하지 않도록 L0 계약을 고정한다
 .../humansearch-l0-auth-surface-goal-2026-08-18.md | 1003 ++++++++++++++++++++
 docs/sot/INDEX.md                                  |    1 +
 docs/sot/humansearch-l0-surface-contract.md        |  142 +++
 humansearch/pyproject.toml                         |    9 +-
 humansearch/src/humansearch/__init__.py            |   19 +-
 humansearch/src/humansearch/auth_surface.py        |   73 ++
 humansearch/tests/test_auth_surface.py             |  141 +++
 humansearch/uv.lock                                |   69 ++
 8 files changed, 1450 insertions(+), 7 deletions(-)
ab851a2 docs(engineering): P0 구현 V1 적대 검증 PASS — 판정·재현 증거 장부 append Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
 .../admin-position-map-spec-v2-2026-08-17.md       | 23 ++++++++++++++++++++++
 1 file changed, 23 insertions(+)
1e0f805 docs(engineering): P0 보완판 — 샌드박스 면제 범위 4파일 전체로 확대(밖 검증 실측 근거) + 재개 지점 S4 Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
 .../goal-prompts/codex-position-map-p0-impl-addendum-2026-08-18.md    | 4 ++--
 1 file changed, 2 insertions(+), 2 deletions(-)
8cd1e9e docs(engineering): P0 보완판 — 재개 지점을 실커밋 기준으로 갱신 Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
 .../goal-prompts/codex-position-map-p0-impl-addendum-2026-08-18.md   | 5 +++--
 1 file changed, 3 insertions(+), 2 deletions(-)
```

→ 뭘 시켰나: 병합 유입 4건 각각의 변경 파일과 줄 수를 확인했습니다. / 뭐가 나왔나: 세 커밋은 문서만, 한 커밋은 HumanSearch 코드·시험·의존성과 새 SOT를 바꿨습니다. 훅·훅 계약·설치·검증 설정 파일은 목록에 없습니다. / 좋은 소식인가 나쁜 소식인가: 직접 충돌 가능성에는 좋은 소식이지만 HumanSearch 코드가 기존 G3 검사 입력이 되므로 실행 확인은 별도로 필요했습니다.

## 5. 새 SOT와 INDEX 변경 전문

```diff
diff --git a/docs/sot/INDEX.md b/docs/sot/INDEX.md
index e330b4e..28421f1 100644
--- a/docs/sot/INDEX.md
+++ b/docs/sot/INDEX.md
@@ -6,5 +6,6 @@
 - [hook-contracts.md](hook-contracts.md) — 로컬 git hook 5개(pre-commit·pre-push·session-status·acceptance-0-7·install-hooks)의 입출력 계약
 - [git-workflow.md](git-workflow.md) — trunk-based + worktree + 태그 릴리스 규약
 - [verification-commands.md](verification-commands.md) — 이 저장소의 실제 게이트 명령(make 레포 아님, 실행 확인됨)
+- [humansearch-l0-surface-contract.md](humansearch-l0-surface-contract.md) — HumanSearch L0 인증 화면 분류의 입력·출력·경계
 
 새 SOT 파일을 추가하는 유일한 트리거: 스크립트/훅/CI/다음 세션이 이 문서를 **답으로 참조**해야 하는가? 아니면 `docs/engineering/`에 남긴다.
```

→ 뭘 시켰나: `INDEX.md`의 실제 diff를 읽었습니다. / 뭐가 나왔나: 기존 훅 계약 행은 문맥으로 보일 뿐 변경되지 않았고, HumanSearch 계약 링크 한 줄만 추가됐습니다. / 좋은 소식인가 나쁜 소식인가: 훅 계약 독립성에는 좋은 소식입니다.

새 `docs/sot/humansearch-l0-surface-contract.md` 142줄의 확인 결과는 다음과 같습니다.

- 입력은 `SurfaceObservation`, 세 화면 역할, `contract_valid`로 제한합니다.
- 출력은 `UNKNOWN`, `HUMAN_AUTH`, `AUTHENTICATED`, `CHALLENGE`, `DRIFTED` 다섯 값입니다.
- 실제 브라우저·로그인·검색·합치기·배포는 비범위로 명시합니다.
- 공개 구현은 `humansearch/src/humansearch/auth_surface.py`로 지정합니다.
- `pre-push`, `hook-contracts`, `install-hooks`, `acceptance-0-2`, `acceptance-0-5`, `acceptance-0-7`, `PUSH-PERFORMING`의 동작을 정하거나 바꾸는 문장은 없습니다.

→ 뭘 시켰나: 새 계약 전문을 읽고 훅 책임·실행 책임·비범위를 분리했습니다. / 뭐가 나왔나: 인증 화면 분류 계약이며 훅 계약을 재정의하지 않습니다. / 좋은 소식인가 나쁜 소식인가: AC3의 문서 충돌 우려에는 좋은 소식입니다.

## 6. 병합 전후 보호 파일 동일성

```text
$ git diff --name-status 7c648b9^1 7c648b9
M	docs/engineering/admin-position-map-spec-v2-2026-08-17.md
M	docs/engineering/goal-prompts/codex-position-map-p0-impl-addendum-2026-08-18.md
A	docs/engineering/humansearch-l0-auth-surface-goal-2026-08-18.md
M	docs/sot/INDEX.md
A	docs/sot/humansearch-l0-surface-contract.md
M	humansearch/pyproject.toml
M	humansearch/src/humansearch/__init__.py
A	humansearch/src/humansearch/auth_surface.py
A	humansearch/tests/test_auth_surface.py
M	humansearch/uv.lock
--- protected-path object IDs: before vs after merge ---
hooks/pre-push BEFORE=33ebb613f88b70fed8c8bced0ebd5076381fadd7 AFTER=33ebb613f88b70fed8c8bced0ebd5076381fadd7 UNCHANGED
scripts/acceptance-0-7.sh BEFORE=b14195e9c4664a1aa4bb92a525e101d52de2a3b1 AFTER=b14195e9c4664a1aa4bb92a525e101d52de2a3b1 UNCHANGED
docs/sot/hook-contracts.md BEFORE=f680a35e8816885f2651ad8118c176054e453b91 AFTER=f680a35e8816885f2651ad8118c176054e453b91 UNCHANGED
verify.sh BEFORE=00018158cd019de0a78f4d22685af6a3056446ed AFTER=00018158cd019de0a78f4d22685af6a3056446ed UNCHANGED
scripts/install-hooks.sh BEFORE=bd40f73cea2a79d86ef2b4e35d56bce60d3830a3 AFTER=bd40f73cea2a79d86ef2b4e35d56bce60d3830a3 UNCHANGED
.github/workflows/verify.yml BEFORE=6a6abfab46fdfdc77113a188a71435157a8e95d2 AFTER=6a6abfab46fdfdc77113a188a71435157a8e95d2 UNCHANGED
```

→ 뭘 시켰나: 병합 직전 첫 부모와 병합 결과의 파일 목록·내용 식별자를 대조했습니다. / 뭐가 나왔나: 병합 파일은 10개이고, 보호 파일 6개는 내용 식별자가 전부 같았습니다. / 좋은 소식인가 나쁜 소식인가: 직접 변경·충돌 우려에는 좋은 소식입니다.

훅 관련 문구 검색의 첫 시도는 파일 목록을 한 인자로 넘겨 다음처럼 실패했습니다.

```text
rg: docs/engineering/admin-position-map-spec-v2-2026-08-17.md
docs/engineering/goal-prompts/codex-position-map-p0-impl-addendum-2026-08-18.md
docs/engineering/humansearch-l0-auth-surface-goal-2026-08-18.md
docs/sot/INDEX.md
docs/sot/humansearch-l0-surface-contract.md
humansearch/pyproject.toml
humansearch/src/humansearch/__init__.py
humansearch/src/humansearch/auth_surface.py
humansearch/tests/test_auth_surface.py
humansearch/uv.lock: IO error ... No such file or directory
```

→ 뭘 시켰나: 병합 파일 안에서 훅 관련 단어를 찾으려 했습니다. / 뭐가 나왔나: 파일명 전달 방식이 틀려 검색이 실행되지 않았습니다. / 좋은 소식인가 나쁜 소식인가: 증거로 쓸 수 없는 실패이며, 바로 아래처럼 다시 했습니다.

```text
docs/sot/INDEX.md:6:- [hook-contracts.md](hook-contracts.md) — 로컬 git hook 5개(pre-commit·pre-push·session-status·acceptance-0-7·install-hooks)의 입출력 계약
docs/engineering/humansearch-l0-auth-surface-goal-2026-08-18.md:86:RED: 2/19 (acceptance-0-7.sh 제외 — CI 담당)
docs/engineering/humansearch-l0-auth-surface-goal-2026-08-18.md:100:RED: 1/19 (acceptance-0-7.sh 제외 — CI 담당)
docs/engineering/humansearch-l0-auth-surface-goal-2026-08-18.md:111:RED: 0/19 (acceptance-0-7.sh 제외 — CI 담당)
docs/engineering/humansearch-l0-auth-surface-goal-2026-08-18.md:131:RED: 0/20 (acceptance-0-7.sh 제외 — CI 담당)
docs/engineering/humansearch-l0-auth-surface-goal-2026-08-18.md:161:- `docs/sot/hook-contracts.md`
docs/engineering/humansearch-l0-auth-surface-goal-2026-08-18.md:223:- bash verify.sh
docs/engineering/humansearch-l0-auth-surface-goal-2026-08-18.md:330:**8. `bash verify.sh`** — exit 0
docs/engineering/humansearch-l0-auth-surface-goal-2026-08-18.md:334:(verify.sh 본문을 직접 읽어 비밀 패턴 스캔 전용 스크립트임을 확인 — fail-closed 설계, 자기 면제 없음)
docs/engineering/humansearch-l0-auth-surface-goal-2026-08-18.md:949:| 비밀 없음 | `bash verify.sh` | 추적 파일 비밀 패턴 0, `.env` 미추적 | 없음 |
```

→ 뭘 시켰나: 파일명을 각각 넘겨 같은 검색을 다시 했습니다. / 뭐가 나왔나: `INDEX.md:6`은 수정되지 않은 기존 문맥이고, 나머지는 실행 지시가 아닌 과거 검증 장부의 기록입니다. / 좋은 소식인가 나쁜 소식인가: 실제 훅 동작 변경 증거가 아니라는 점에서 좋은 소식입니다.

## 7. `session-status.sh` 직접 실행

첫 장기 세션 완주 결과:

```text
HEAD: 7406c63 (ahead 45 / behind 0)
ORIGIN: b6aee6a
RED: 3/28 (acceptance-0-7.sh 제외 — CI 담당)
SESSION_STATUS_EXIT=0
```

→ 뭘 시켰나: 정확히 `bash scripts/session-status.sh`를 실행했습니다. / 뭐가 나왔나: 28개 중 3개 실패로 보고됐지만 스크립트 자체 종료값은 0이었습니다. / 좋은 소식인가 나쁜 소식인가: 요구한 `0/28`이 아니므로 나쁜 소식입니다. 이때 앞선 포착 시도가 겹쳤을 가능성을 배제하기 위해 개별 진단과 최종 단독 재실행을 했습니다.

모든 다른 검사가 끝난 뒤 최종 단독 실행 결과:

```text
HEAD: 7406c63 (ahead 45 / behind 0)
ORIGIN: b6aee6a
RED: 2/28 (acceptance-0-7.sh 제외 — CI 담당)
SESSION_STATUS_FINAL_EXIT=0
```

→ 뭘 시켰나: 같은 명령을 다른 검사와 겹치지 않게 다시 실행했습니다. / 뭐가 나왔나: 최종 현재값은 2/28입니다. / 좋은 소식인가 나쁜 소식인가: 0/28 재현 실패이므로 최종 판정에는 나쁜 소식입니다.

개별 28개 진단 전문:

```text
PASS ./scripts/acceptance-0-2-unreachable-content.sh exit=0
PASS ./scripts/acceptance-0-2.sh exit=0
PASS ./scripts/acceptance-0-5.sh exit=0
PASS ./scripts/acceptance-0-6.sh exit=0
PASS ./scripts/acceptance-hs-a3.sh exit=0
PASS ./scripts/acceptance-hs-a4.sh exit=0
PASS ./scripts/acceptance-hs-cleanroom-absolute-contexts.sh exit=0
PASS ./scripts/acceptance-hs-cleanroom-absolute-paths.sh exit=0
PASS ./scripts/acceptance-hs-cleanroom-colon-paths.sh exit=0
PASS ./scripts/acceptance-hs-cleanroom-file-urls.sh exit=0
PASS ./scripts/acceptance-hs-cleanroom-hook-env-mutations.sh exit=0
PASS ./scripts/acceptance-hs-cleanroom-hook-env.sh exit=0
PASS ./scripts/acceptance-hs-cleanroom-mutations.sh exit=0
PASS ./scripts/acceptance-hs-cleanroom.sh exit=0
PASS ./scripts/acceptance-hs-gates-antiforge.sh exit=0
FAIL ./scripts/acceptance-hs-gates-mutations.sh exit=1
FAIL ./scripts/acceptance-hs-gates.sh exit=2
PASS ./scripts/acceptance-hs-portal-constants-hardening.sh exit=0
PASS ./scripts/acceptance-hs-portal-constants-hardening2.sh exit=0
PASS ./scripts/acceptance-hs-portal-constants-hardening3.sh exit=0
PASS ./scripts/acceptance-hs-portal-constants-hardening4.sh exit=0
PASS ./scripts/acceptance-hs-portal-constants-hardening5.sh exit=0
PASS ./scripts/acceptance-hs-portal-constants-hardening6.sh exit=0
PASS ./scripts/acceptance-hs-portal-constants-mutations.sh exit=0
PASS ./scripts/acceptance-hs-portal-constants.sh exit=0
PASS ./scripts/acceptance-secret-webhook-vendor.sh exit=0
PASS ./scripts/acceptance-verify-ac-m.sh exit=0
PASS ./verify.sh exit=0
DIAGNOSTIC_RED=2/28
```

→ 뭘 시켰나: `session-status.sh`와 같은 목록·환경값으로 각 검사의 이름과 종료값을 노출했습니다. / 뭐가 나왔나: 실패는 G3 기본 검사와 그 변조 검사 두 개뿐이었습니다. / 좋은 소식인가 나쁜 소식인가: 원인이 좁혀진 것은 좋지만 필수 전체 통과에는 나쁜 소식입니다.

두 실패의 직접 출력:

```text
error: Failed to initialize cache at `/Users/kangsangmo/.cache/uv`
  Caused by: failed to open file `/Users/kangsangmo/.cache/uv/sdists-v9/.git`: Operation not permitted (os error 1)
FAIL: environment sync
ACCEPTANCE_HS_GATES_EXIT=2

FAIL: mutation failed for the wrong reason: planted failing test (exit=2)
error: Failed to initialize cache at `/Users/kangsangmo/.cache/uv`
  Caused by: failed to open file `/Users/kangsangmo/.cache/uv/sdists-v9/.git`: Operation not permitted (os error 1)
FAIL: environment sync
ACCEPTANCE_HS_GATES_MUTATIONS_EXIT=1
```

→ 뭘 시켰나: 실패한 두 스크립트를 상세 출력을 숨기지 않고 각각 실행했습니다. / 뭐가 나왔나: 둘 다 실제 시험보다 먼저 사용자 홈 저장 공간의 `.git` 표식 파일을 열지 못해 중단됐습니다. / 좋은 소식인가 나쁜 소식인가: 코드 실패로 단정할 수 없다는 점은 좋지만, 검사가 실행되지 않았다는 점은 나쁩니다.

허용된 임시 저장 공간을 쓴 기본 G3 보조 실행:

```text
PASS: ruff clean in 4 python files
PASS: mypy strict clean in 4 source files
PASS: pytest collected 25 and passed
PASS: runtime import proof /Users/kangsangmo/Desktop/Valuehire_v6/worktrees/humansearch-g3-portal-constants/humansearch/src/humansearch/__init__.py
COLLECTED: 25
ACCEPTANCE_HS_GATES_ISOLATED_EXIT=0
```

→ 뭘 시켰나: `UV_CACHE_DIR`를 허용된 임시 경로로 바꾸고 기본 G3 검사를 실행했습니다. / 뭐가 나왔나: 형식·타입·25개 시험·실제 패키지 불러오기가 모두 통과했습니다. / 좋은 소식인가 나쁜 소식인가: 기본 HumanSearch 코드에는 좋은 소식입니다.

같은 방식의 변조 검사:

```text
FAIL: mutation failed for the wrong reason: planted failing test (exit=2)
  ├─▶ dns error
  ╰─▶ failed to lookup address information: nodename nor servname provided, or
      not known
  help: `pytest` (v9.1.1) was included because `humansearch:dev` (v0.1.0)
        depends on `pytest`
FAIL: environment sync
ACCEPTANCE_HS_GATES_MUTATIONS_ISOLATED_EXIT=1
```

→ 뭘 시켰나: 고장 사본 검사도 새 임시 저장 공간으로 실행했습니다. / 뭐가 나왔나: 고장 표본 실행 전에 필요한 도구를 외부에서 가져오려다 주소 조회가 막혔습니다. / 좋은 소식인가 나쁜 소식인가: 고장 탐지 능력을 끝까지 증명하지 못했으므로 나쁜 소식입니다.

## 8. `acceptance-0-7.sh` 직접 실행 전문

```text
$ SECRET_PATTERNS_FILE= bash scripts/acceptance-0-7.sh
=== 전제 검사: 훅 인프라 ===
OK: 훅 파일 4종 + settings.json 존재

=== pre-push 예외 안내 실실행 ===
OK: 실제 pre-push 출력이 로컬 수동/사후 CI/PUSH-PERFORMING을 구분함

=== 시연 (샌드박스: /var/folders/4h/jphmynjn2jl54cqy8d_ddhkh0000gn/T/tmp.JtTzXFj8Vm/repo · 각 시연마다 훅 ON/OFF 대조) ===
[1/6] 검사기 자기 제외 → BLOCKED (훅ON=1 · 훅OFF=0) ✓ 훅이 원인
         BLOCKED: 검사기 자기 제외 — scripts/acceptance-0-6.sh 가 자기 자신을 검사 대상에서 뺀다 (P13)
[2/6] 검사 약화(실패 무시) → BLOCKED (훅ON=1 · 훅OFF=0) ✓ 훅이 원인
         BLOCKED: 검사 약화 패턴 추가 — scripts/acceptance-0-2.sh (P13). 정당하면 suppressions.yaml 에 expiry 와 함께 등록하라
[3/6] 만료일 없는 억제 → BLOCKED (훅ON=1 · 훅OFF=0) ✓ 훅이 원인
         BLOCKED: 억제 항목 1건 중 expiry 가 0건뿐 — 만료일 없는 억제는 영구화된다 (P13)
[4/6] LLM 출력→판정 필드 → BLOCKED (훅ON=1 · 훅OFF=0) ✓ 훅이 원인
         BLOCKED: LLM 출력을 판정 수치로 변환 — src/scoring.js. 판정 수치는 순수 함수가 만든다 (P14)
[5/6] 미커밋 상태로 push → BLOCKED (훅ON=1 · 훅OFF=0) ✓ 훅이 원인
         BLOCKED: 작업트리가 깨끗하지 않다 — 미커밋/미추적 변경이 있는 상태의 push (P15)
[6/6] 가짜 외부효과 모듈 → BLOCKED (훅ON=1 · 훅OFF=0) ✓ 훅이 원인
         BLOCKED: 외부 효과를 표방하는데 네트워크 호출이 0건 — src/portal-login.js. 시뮬레이션 의심 (P4)

OK: 원본 저장소 무변경 확인 (da39a3ee5e6b4b0d3255bfef95601890afd80709)

PASS: 위반 6 종이 전부 차단됨 (각 건 훅 OFF 대조 통과)
ACCEPTANCE_0_7_EXIT=0
```

→ 뭘 시켰나: 사용자가 지정한 환경값으로 회귀 시험을 직접 실행했습니다. / 뭐가 나왔나: 실제 훅 라벨 확인과 기존 위반 6종의 훅 켬/끔 대조가 모두 통과했습니다. / 좋은 소식인가 나쁜 소식인가: AC2에는 좋은 소식입니다.

## 9. 직접 `pre-push` 실행 전문

```text
$ bash hooks/pre-push </dev/null
  skip ./scripts/acceptance-0-2.sh (LOCAL-MANUAL · push 시점 제외)
  skip ./scripts/acceptance-0-5.sh (POST-PUSH · CI 담당)
  skip ./scripts/acceptance-0-7.sh (PUSH-PERFORMING · CI 담당)
pre-push: 검사 26개 실행
  ok  ./scripts/acceptance-0-2-unreachable-content.sh
  ok  ./scripts/acceptance-0-6.sh
  ok  ./scripts/acceptance-hs-a3.sh
  ok  ./scripts/acceptance-hs-a4.sh
  ok  ./scripts/acceptance-hs-cleanroom-absolute-contexts.sh
  ok  ./scripts/acceptance-hs-cleanroom-absolute-paths.sh
  ok  ./scripts/acceptance-hs-cleanroom-colon-paths.sh
  ok  ./scripts/acceptance-hs-cleanroom-file-urls.sh
  ok  ./scripts/acceptance-hs-cleanroom-hook-env-mutations.sh
  ok  ./scripts/acceptance-hs-cleanroom-hook-env.sh
  ok  ./scripts/acceptance-hs-cleanroom-mutations.sh
  ok  ./scripts/acceptance-hs-cleanroom.sh
  ok  ./scripts/acceptance-hs-gates-antiforge.sh
BLOCKED: ./scripts/acceptance-hs-gates-mutations.sh exit=1
BLOCKED: ./scripts/acceptance-hs-gates.sh exit=2
  ok  ./scripts/acceptance-hs-portal-constants-hardening.sh
  ok  ./scripts/acceptance-hs-portal-constants-hardening2.sh
  ok  ./scripts/acceptance-hs-portal-constants-hardening3.sh
  ok  ./scripts/acceptance-hs-portal-constants-hardening4.sh
  ok  ./scripts/acceptance-hs-portal-constants-hardening5.sh
  ok  ./scripts/acceptance-hs-portal-constants-hardening6.sh
  ok  ./scripts/acceptance-hs-portal-constants-mutations.sh
  ok  ./scripts/acceptance-hs-portal-constants.sh
  ok  ./scripts/acceptance-secret-webhook-vendor.sh
  ok  ./scripts/acceptance-verify-ac-m.sh
  ok  ./verify.sh
PRE_PUSH_DIRECT_EXIT=1
```

→ 뭘 시켰나: 훅 자체를 원본 작업트리에서 직접 실행했습니다. / 뭐가 나왔나: 세 라벨은 정확했고 26개만 실행됐으며, 환경 제한의 두 검사 때문에 전체 종료값은 1이었습니다. / 좋은 소식인가 나쁜 소식인가: AC1 문구·건너뛰기에는 좋은 소식, 현재 push 가능 여부에는 나쁜 소식입니다.

## 10. 소스 줄 단위 증거

- `hooks/pre-push:140-141` — `PUSH-PERFORMING` 문구를 출력하고 즉시 다음 검사로 넘어갑니다.
- `hooks/pre-push:144-146` — `acceptance-0-2.sh`에 `LOCAL-MANUAL · push 시점 제외`를 출력하고 즉시 다음 검사로 넘어갑니다.
- `hooks/pre-push:148-150` — `acceptance-0-5.sh`에 `POST-PUSH · CI 담당`을 출력하고 즉시 다음 검사로 넘어갑니다.
- `hooks/pre-push:153-161` — 앞에서 건너뛰지 않은 검사만 목록에 넣고 실제 실행 개수를 출력합니다.
- `scripts/acceptance-0-7.sh:92-98` — 원본 작업트리의 현재 훅을 샌드박스 복제본에 복사하고 설치합니다.
- `scripts/acceptance-0-7.sh:126-128` — `bash hooks/pre-push`를 실제 실행하고 그 종료값을 저장합니다.
- `scripts/acceptance-0-7.sh:134-145` — 세 라벨을 정확한 고정 문자열로 각각 찾고, 없으면 실패 표식을 세웁니다.
- `scripts/acceptance-0-7.sh:148-150` — 실패 표식이 하나라도 있으면 종료 1로 후속 시연을 중단합니다.

```text
BASH_SYNTAX_EXIT=0
```

→ 뭘 시켰나: `bash -n hooks/pre-push scripts/acceptance-0-7.sh`로 두 셸 파일의 문법을 검사했습니다. / 뭐가 나왔나: 종료 0이었습니다. / 좋은 소식인가 나쁜 소식인가: 문법에는 좋은 소식입니다.

## 11. 사후 검사 `acceptance-0-5.sh`

```text
$ SECRET_PATTERNS_FILE= bash scripts/acceptance-0-5.sh
PASS: 0-5 완료 — CI 비밀스캔 강제 + push 완료 + 원격 트리 비밀 0건
ACCEPTANCE_0_5_EXIT=0
```

→ 뭘 시켰나: 배경에서 핵심 차단 해소 조건으로 제시된 사후 검사를 별도로 재실행했습니다. / 뭐가 나왔나: 원격 반영과 비밀 0건을 확인하며 통과했습니다. / 좋은 소식인가 나쁜 소식인가: 이전 외부 차단이 해소됐다는 직접 증거로 좋은 소식입니다.

# 결함·공백 요약

| 구분 | 심각도 | 확인 결과 | 그대로 두면 사업·운영에 생기는 일 |
|---|---|---|---|
| AC1 코드 | 결함 없음 | 세 문구와 각 건너뛰기 유지 확인 | 없음 |
| AC2 코드·시험 | 결함 없음 | 실제 훅 실행, 정확한 세 검색, 실패 종료 경로 확인 | 없음 |
| 병합 직접 충돌 | 결함 없음 | 보호 파일 6개 동일 | 없음 |
| 전체 검증 재현 | 높음(검증 공백) | `RED: 2/28`, 직접 훅 종료 1 | 안전하다고 승인한 뒤 고장 탐지 검사의 실제 작동이 확인되지 않은 상태가 남습니다. |
| 원격 PR 상태 | 범위 밖/미확인 | 이번 감사에서 조회 안 함 | 서버 상태가 달라졌다면 이 로컬 판정만으로 실제 병합 가능 여부를 알 수 없습니다. |

→ 무엇을 비교했나: 확인된 코드 결함과 실행·외부 상태의 공백을 분리했습니다. / 무엇이 나왔나: 코드 결함은 없지만 전체 검증 공백은 승인 차단 수준이며, 원격 상태는 이번 로컬 감사 범위 밖입니다.

## 문서 자체 검증

브리핑 형식 검사 결과는 코드블록 19개, 표 2개, 표·출력 해석 누락 0개, 위반 0건, 종료 0입니다. `git diff --check`도 종료 0이었습니다. 이 수치는 문서 형식과 공백 오류만 증명하며, 회사 차원의 코드 합격이나 PR 승인을 증명하지 않습니다.

# 최종 중단 조건

다음 두 조건이 모두 새 실행으로 확인되기 전까지 push와 PR #13 병합 승인을 보류합니다.

1. 동일 커밋 `7406c633395d943d28a6c24822f48d32160c1cfd`에서 정확히 `bash scripts/session-status.sh`가 `RED: 0/28`을 출력할 것.
2. 그 실행에서 `acceptance-hs-gates-mutations.sh`가 환경 준비가 아니라 의도한 여섯 고장 표본 판정까지 완료할 것.

이 두 조건이 닫히면 AC1~AC3의 코드 판정에는 현재 확인된 중간 이상 결함이 없으므로, 그 새 증거를 기준으로 최종 PASS를 다시 내릴 수 있습니다.
