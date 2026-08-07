# History squash v1 — 0–2 사전 작업 적대 검증 판정

- 대상: `task/history-squash` @ `965f084`
- 범위: squash **실행 전** 0–2 작업의 검증 도구와 절차. 이 문서는 history rewrite나 push를 승인하거나 실행하지 않는다.
- 비밀값 취급: 패턴의 실제 문자열은 이 문서·명령 출력에 재기록하지 않는다. 아래의 “리터럴”은 로컬의 gitignore된 패턴 파일 첫 행을 뜻한다.
- 판정 기준: 단순 정상 경로가 아니라, 각 보장을 깨려 한 반증 시도와 그 결과로 판정한다.

## 판정 요약

| 항목 | 판정 | 깨려 한 보장 | 결과 / 결함 |
| --- | --- | --- | --- |
| ① 스캐너 검출력 | PASS | 리터럴 파일을 인덱스에 올려 스캐너를 우회 | 격리 인덱스에서 패턴 파일을 tracked로 보이게 한 뒤 `bash verify.sh`가 exit 1 및 해당 파일을 보고했다. 중단 전 실제 `git add` 실측도 exit 1이었다. |
| ② 패턴 파일 fail-closed | PASS | 패턴 파일을 누락·빈 입력으로 만들어 no-op화 | 존재하지 않는 경로와 `/dev/null` 각각 `verify.sh` exit 2. 조용한 PASS가 아니었다. |
| ③ acceptance의 자기오염·인터럽트 정리 | FAIL | `git add` 직후 TERM으로 cleanup을 건너뜀 | 이전 실측에서 TERM 후 exit 143 및 `.acceptance-plant-*.tmp`의 스테이징 잔존. 현재 소스에도 `trap`이 없어 재현 가능하다. |
| ④ squash 잔존 경로 | FAIL | `git log --all`이 0이면 과거 객체도 사라졌다고 가정 | 임시 클론 실측에서 refs 이외 reflog·pseudoref·linked-worktree HEAD reflog·FETCH_HEAD가 남았다. 현재 절차에 이들을 모두 제거·검증하는 단계가 없다. |

현재 대상 브랜치에서 `git log --all -S"$(head -1 .secret-patterns)" --oneline`은 **6건**이다. 따라서 이 브랜치는 squash 전이며 0–2의 최종 AC PASS 상태가 아니다.

## ① 스캐너가 staged 리터럴을 잡는가 — PASS

**반증 시도:** 리터럴을 담은 파일을 staged 상태로 만들고 `verify.sh`가 “추적 파일만 본다”는 이유로 놓치게 만들려 했다.

**방법과 관측:** 공유 인덱스를 오염시키지 않도록 `GIT_INDEX_FILE` 격리 인덱스에 gitignore된 `.secret-patterns`를 `git update-index --add --cacheinfo`로 staged entry로 넣고 실행했다. `bash verify.sh`는 exit **1**이었고 `.secret-patterns`를 매치 파일로 보고했다. 중단 직전 세션의 실제 임시 리터럴 파일 `git add` 실측도 같은 exit 1이었다.

**판정:** 우회에 실패했다. 스캐너는 `git ls-files`로 staged 파일을 포함해 검사하고 자기 면제도 두지 않으므로, 이 검출력 계약은 통과다. 이 판정은 패턴 파일 자체가 정상적으로 제공된다는 ②의 계약에 의존한다.

## ② 패턴 파일이 없거나 비면 조용히 통과하는가 — PASS

**반증 시도:** `SECRET_PATTERNS_FILE`을 존재하지 않는 경로 및 빈 입력(`/dev/null`)으로 바꿔 스캔을 no-op로 만들려 했다.

**관측:** 두 경우 모두 `bash verify.sh`가 `FAIL: secret patterns file missing or empty`를 출력하고 exit **2**로 끝났다.

**판정:** 우회에 실패했다. 패턴이 없을 때 PASS/exit 0이 되는 fail-open 경로는 확인되지 않았다.

## ③ acceptance 스크립트가 자기오염 없이 신호에도 원복되는가 — FAIL

**반증 시도 A (자기 리터럴):** 패턴 첫 행을 `scripts/acceptance-0-2.sh`에서 고정문자열 검색했다. 검색 exit는 **1**(미검출)이었다. 즉 실제 리터럴을 스크립트 몸체에 다시 쓰지는 않았다. `grep -v` 텍스트는 설명 주석에만 있고, 실행되는 파일 제외 로직은 없었다.

**반증 시도 B (신호 중단):** 뮤테이션 절차의 `git add "$tmpf"` 직후 TERM을 주입해 `git rm --cached`와 파일 삭제까지 도달하지 못하게 했다. 중단 전 세션의 실측은 exit **143**이었고, `.acceptance-plant-*.tmp`가 **staged로 잔존**했다. 공격은 성공했다.

소스 근거도 동일하다. cleanup은 정상 경로의 아래 두 줄뿐이며 `trap`이 없다.

```bash
git rm --cached -q "$tmpf"
rm -f "$tmpf"
```

이번 재측정에서는 같은 지점을 결정적으로 만들기 위한 test-only `git` shim을 사용했으나, 이 실행 환경이 linked-worktree의 `index.lock` 생성을 거부하여 `git add`가 exit **128**로 끝났다. TERM 재현은 이 환경에서 새로 확정하지 못했지만, shim과 plant 파일은 즉시 삭제했고 shared index에는 staged entry가 남지 않았다. 기존의 143 실측과 `trap` 부재는 반증 성공 판정을 뒤집지 않는다.

**판정:** FAIL. `set -e`는 TERM/SIGINT에 대한 cleanup을 보장하지 않는다. acceptance가 신호 후에도 작업트리를 보존한다는 보장이 없으므로, squash 실행 전 `trap` 기반 cleanup(원래 종료 상태 보존 포함)과 TERM/INT/HUP 적대 테스트가 필요하다.

## ④ `git log --all` 밖의 squash 잔존 경로 — FAIL

**반증 시도:** 임시 클론에서 오염을 나타내는 비밀값 대신 비민감 probe commit을 만든 뒤, 일반적인 “soft reset → 단일 commit → 보이는 branch 삭제” 절차를 수행했다. 이어 `git log --all`에서 probe가 사라진 것을 “완전 제거”로 오판할 수 있는지 확인했다.

**관측:** `git log --all`은 **live refs 아래의 commit만** 걷는다. 따라서 다음 경로는 별도로 제거·검증하지 않으면 probe/옛 객체 또는 그 SHA가 남는다.

| 경로 | `git log --all` 가시성 | 위험 / 필요 조치 |
| --- | --- | --- |
| 남은 branch, tag, remote-tracking, `refs/original/*`, `refs/replace/*`, notes, custom refs | 보임 | 보이는 모든 ref를 열거해 오염 조상을 가리키는 ref를 제거해야 한다. |
| `refs/stash`의 현재 tip | 보임 | `--all`에는 보이지만 branch 삭제만으로는 지워지지 않는다. `stash`를 별도로 점검·삭제해야 한다. |
| `logs/HEAD`, `logs/refs/**`, 오래된 stash reflog entry | **안 보임** | `git reflog expire --expire=now --expire-unreachable=now --all` 없이 커밋이 회복 가능하다. |
| linked worktree별 `worktrees/<name>/logs/HEAD` | **안 보임** | 각 linked worktree의 HEAD reflog도 만료 대상이다. 현재 대상의 실제 경로는 `.git/worktrees/history-squash/logs/HEAD`다. |
| `ORIG_HEAD` pseudoref | **안 보임** | reset/rebase 후 이전 tip SHA가 남을 수 있다. `show-ref` 열거에도 나오지 않으므로 별도 점검·삭제가 필요하다. |
| `FETCH_HEAD` | **안 보임** | ref가 아니므로 GC root를 보장하지는 않지만, 최근 fetch한 옛 SHA가 평문으로 남는 잔존/복구 단서다. 별도 점검·삭제 또는 다음 fetch로 갱신해야 한다. |

**판정:** FAIL. “`git log --all` 0건”은 live-ref 음성 판정일 뿐, object database와 모든 복구 경로의 음성 증명이 아니다. 특히 reflog와 linked-worktree HEAD reflog, `ORIG_HEAD`, `FETCH_HEAD`는 그 명령이 못 보는 경로다. 반면 `refs/stash`의 현재 tip은 `--all`에 보인다는 점을 구분해야 한다.

## squash 전 보완 게이트 (미실행)

1. 모든 worktree를 포함해 refs와 pseudoref 파일 위치를 먼저 보존용 bundle과 함께 기록한다.
2. rewrite 뒤 branch뿐 아니라 tag/remote/custom/ref-original/replace/stash를 열거해 오염 조상을 가리키는 ref를 제거한다.
3. 각 worktree의 reflog를 포함해 `git reflog expire --expire=now --expire-unreachable=now --all`을 실행하고, 검증한 `ORIG_HEAD` 및 `FETCH_HEAD`를 별도 처리한다.
4. `git gc --prune=now` 뒤 `git fsck --full --no-reflogs --unreachable` 및 알려진 옛 SHA에 대한 `git cat-file -e <old-sha>` 실패를 확인한다. 이 검증은 `git log --all -S...`와 함께 수행하되, 후자만으로 완료 판정을 내리지 않는다.
5. ③을 trap-safe하게 고치고 TERM/INT/HUP 도중에도 index와 untracked probe가 원복되는 테스트가 PASS한 뒤에만 history rewrite를 재개한다.

## 이번 작업의 원복 확인

- test-only signal shim, `.acceptance-plant-*.tmp`, shared index의 staged entry: 모두 제거/없음 확인.
- `.secret-patterns`는 이번 확인 뒤 삭제했다. 이 값은 gitignore된 로컬 검증 입력이었으나 비밀 평문을 보관하므로 작업트리에 남기지 않는다. 이후 검증은 보안 저장소가 `SECRET_PATTERNS_FILE`로 주입한 입력에서만 재개해야 한다.
- 이 판정 문서는 비추적 산출물이다. history rewrite는 이 문서 작성 중 실행하지 않았다.
