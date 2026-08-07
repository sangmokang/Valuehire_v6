# History squash V2 — V1(codex) 판정 적대적 재검증

- 검증자: V2 (Claude, 무맥락 재공격). 구현자 추론 미제공 — 모든 주장은 V2가 직접 실행한 명령 출력으로만 인정했다.
- 대상: `task/history-squash` @ `2f4bf04` (V1 판정 이후 ③④ FAIL 반영본), 저장소 `/Users/kangsangmo/Desktop/Valuehire_v6`
- 실행 환경: `git version 2.39.5 (Apple Git-154)`, darwin 24.6.0
- 비밀값 취급: 실제 리터럴은 이 문서·명령 출력 어디에도 옮기지 않았다. 스캐너 공격 실험은 **합성 토큰**(`SYNTHSECRET42`, `PROBE_LEAK_TOKEN`)과 격리 임시 저장소에서 수행했다.
- 파괴 작업: squash·rewrite·push·main 수정 **미실행**. 커밋 0건.

---

## 판정 요약

| # | 항목 | V1 판정 | V2 판정 | 요지 |
| --- | --- | --- | --- | --- |
| ① | 스캐너 검출력 | PASS | **REFUTED (NEW-FINDING ×3)** | 공백/개행 포함 파일명, `-`로 시작하는 파일명은 리터럴이 **스테이징된 상태에서 exit 0 PASS**. `xargs` 분할 + 에러 무음화가 원인 |
| ② | 패턴 파일 fail-closed | PASS | **REFUTED (NEW-FINDING ×3)** | `SECRET_PATTERNS_FILE`이 **디렉터리**·**읽기 불가 파일**·**CRLF 패턴 파일**이면 스캔이 조용히 no-op → exit 0 PASS |
| ③ | acceptance 신호 원복 | FAIL | **수정 유효 (CONFIRMED-FIXED)** | TERM=143 / INT=130 / HUP=129, 스테이징·디스크 잔존 0. V1 공격 재현 불가 |
| ④ | 잔존 경로 완전성 | FAIL | **부분 CONFIRMED + NEW-FINDING ×3** | V1 목록은 유효. 추가로 ⑴ stale worktree admin dir(index/HEAD)가 gc를 뚫는 root, ⑵ per-worktree `ORIG_HEAD` 미점검, ⑶ acceptance의 `fsck --unreachable`이 `--no-reflogs` 누락으로 reflog 잔존을 못 봄 |
| ⑤ | 상관 블라인드스팟 | — | **NEW-FINDING (치명)** | G·V1 공통 가정 "오염 = 이 저장소 내부"가 거짓. 동일 리터럴이 **다른 저장소의 원격 브랜치 2개(GitHub)** 및 로컬 29개 파일에 평문 존재 |
| ⑥ | 예정 절차 커버리지 | — | 5개 게이트 중 **완전 커버 2 / 부분 2 / 미커버 1** | 아래 O/X 표 |

---

## ① 스캐너 검출력 재공격 — REFUTED (PASS 판정 뒤집힘)

**시도한 공격:** V1이 해보지 않은 우회 9종 — 서브디렉터리, 파일명 공백, 파일명 개행, 파일명 선행 하이픈, 심볼릭 링크, 바이너리(NUL) 파일, 긴 줄 중간 매몰, 줄 분할, 20만자 단일 라인.

**실행 명령:** 격리 저장소(`scratchpad/scan-test`)에 `verify.sh`를 그대로 복사하고 합성 패턴 `SYNTHSECRET42`로 `.secret-patterns` 구성 후, 각 케이스마다
```bash
printf 'SYNTHSECRET42\n' > <target>; git add -- <target>; bash verify.sh; echo "exit=$?"
```

**관측 출력 요지:**

| 케이스 | 관측 | 결과 |
| --- | --- | --- |
| A1 서브디렉터리 `sub/deep/a.txt` | `FAIL: ... - sub/deep/a.txt` / exit=1 | 검출 O |
| **A2 파일명에 공백 `my file.txt`** | `PASS: no secret-pattern match ...` / **exit=0** (`git ls-files`에는 존재) | **우회 성공** |
| **A3 파일명에 개행 `bad\nname.txt`** | `PASS ...` / **exit=0** (`ls-files`는 `"bad\nname.txt"`로 따옴표 출력) | **우회 성공** |
| **A4 파일명 선행 하이픈 `-dashfile.txt`** | `PASS ...` / **exit=0** | **우회 성공** |
| A5 심볼릭 링크(외부 파일 지시) | `FAIL: ... - linky` / exit=1 | 검출 O |
| A6 바이너리(NUL 포함) | `FAIL: ... - bin.dat` / exit=1 | 검출 O |
| A7 500자 패딩 사이 매몰 | `FAIL: ... - buried.txt` / exit=1 | 검출 O |
| A8 리터럴 줄 분할 | exit=0 | 계약 밖(단일행 ERE) — 정보성 |
| A9 20만자 단일 라인 | `FAIL: ... - long.txt` / exit=1 | 검출 O |

**원인(소스 근거):** `verify.sh:16`
```bash
LEAKS=$(git ls-files | xargs grep -lEf "$PATTERNS" 2>/dev/null || true)
```
`git ls-files`는 개행 포함 경로를 따옴표·이스케이프로 출력하고, `xargs`는 기본 구분자가 공백/개행이며, `grep`은 `-`로 시작하는 인자를 옵션으로 해석한다. 세 경우 모두 grep이 "그런 파일 없음"으로 실패하는데 `2>/dev/null || true`가 이를 완전히 삼켜 `LEAKS`가 비고 **FAIL=0 → exit 0**이 된다. 즉 실패가 통과로 둔갑한다.

**최소 수정 방향(참고):** `git ls-files -z | xargs -0 grep -lEf "$PATTERNS" --`, 그리고 grep 종료코드 2(오류)를 PASS로 흡수하지 말 것.

**판정: REFUTED / NEW-FINDING.** V1의 ① PASS는 "정상적인 파일명"이라는 무언의 전제 위에서만 성립한다. 공격자(또는 실수)가 만든 공백 포함 경로 하나로 스캐너 계약 전체가 무력화된다.

---

## ② fail-closed 경계 재공격 — REFUTED (PASS 판정 뒤집힘)

**시도한 공격:** V1은 "없는 경로"와 `/dev/null`만 봤다. V2는 리터럴을 **스테이징한 상태**(대조군에서 exit 1 확인)에서 패턴 입력의 경계 9종을 투입했다.

**실행 명령:**
```bash
printf 'SYNTHSECRET42\n' > planted.txt; git add planted.txt   # 모든 케이스 공통 전제
SECRET_PATTERNS_FILE=<변형> bash verify.sh; echo "exit=$?"
```

**관측 출력 요지:**

| 케이스 | 관측 | 결과 |
| --- | --- | --- |
| 대조군(정상 패턴 파일) | `FAIL: ... - planted.txt` / exit=1 | 정상 |
| **B1 디렉터리 지정** | `PASS: no secret-pattern match ...` / **exit=0** | **fail-OPEN** |
| B2 `/dev/null` | `FAIL: secret patterns file missing or empty` / exit=2 | fail-closed O |
| B3 없는 경로 | 동상 / exit=2 | fail-closed O |
| B4 빈 줄 1개 | 전 파일 매치 / exit=1 | 시끄러운 실패 O |
| **B5 주석형 한 줄(`# disabled for now`)** | `PASS ...` / **exit=0** | 조용한 no-op |
| **B6 퍼미션 000(읽기 불가)** | `PASS ...` / **exit=0** | **fail-OPEN** |
| **B8 CRLF 줄바꿈 패턴 파일** | `PASS ...` / **exit=0** | **fail-OPEN**(CI 주입 시 현실적) |
| B9 `SECRET_PATTERNS_FILE=`(빈 문자열) | `FAIL: ... - planted.txt` / exit=1 | 기본값 폴백 O |

**원인:** `verify.sh:7`의 게이트는 `[ ! -s "$PATTERNS" ]` 하나뿐이다. `-s`는 **크기>0**만 본다 — 디렉터리도, 읽을 수 없는 파일도 통과한다. 그 뒤 grep이 `Is a directory` / `Permission denied`로 실패해도 `2>/dev/null || true`가 삼킨다. CRLF는 패턴 끝에 `\r`이 붙어 어떤 것도 매치하지 않는 정상 실행이 된다.

**최소 수정 방향(참고):** `[ -f "$PATTERNS" ] && [ -r "$PATTERNS" ] && [ -s "$PATTERNS" ]`, 패턴 로드 후 `grep -c .` 로 유효 패턴 수 검증, grep 종료코드 2 검사, CRLF 정규화.

**판정: REFUTED / NEW-FINDING.** ②의 계약(조용한 스킵 금지)은 V1이 시험한 두 경계에서만 지켜진다. 실제 CI 주입 경로(디렉터리 마운트·퍼미션·CRLF)에서 전부 fail-open이며, 이때 **①의 검출력 계약도 동시에 무효**가 된다(①은 ②에 의존한다고 V1이 스스로 적었다).

---

## ③ V1의 TERM 공격 재현 — 수정 유효 (CONFIRMED-FIXED)

**시도한 공격:** 수정본 `scripts/acceptance-0-2.sh`에 대해 `ACCEPTANCE_TEST_SLEEP=3`으로 `git add` 직후 창을 열고 TERM/INT/HUP를 각각 주입. 대조군으로 KILL(무포착)도 실행.

**실행 명령:**
```bash
ACCEPTANCE_TEST_SLEEP=3 bash scripts/acceptance-0-2.sh > log 2>&1 &
pid=$!; /bin/sleep 1.5
ls -1 .acceptance-plant-*.tmp; git diff --cached --name-only     # 공격 창 실재 확인
kill -TERM $pid; wait $pid; echo "exit_code=$?"
git diff --cached --name-only; ls -1 .acceptance-plant-*.tmp     # 잔존 실측
```
INT은 zsh가 백그라운드 잡의 SIGINT를 SIG_IGN으로 물려주어 트랩 자체가 성립하지 않는 것을 확인한 뒤(1차 시도 exit=1, 신호 미도달), perl `fork`로 **기본 시그널 처분**을 복원해 재실행했다.

**관측 출력 요지:**

| 신호 | 공격 창 상태 | exit code | 스테이징 잔존 | 디스크 잔존 |
| --- | --- | --- | --- | --- |
| TERM | `.acceptance-plant-56542.tmp` 디스크+스테이징 확인 | **143** | 없음 | 없음 |
| INT (기본 처분 복원) | 동일 | **130** | 없음 | 없음 |
| HUP | 동일 | **129** | 없음 | 없음 |
| KILL(대조군) | 동일 | 137 | **`.acceptance-plant-72039.tmp` 잔존** | **잔존** |

KILL 잔존분은 즉시 회수했다(`removed .acceptance-plant-72039.tmp`, 이후 staged=[] / disk=[]).

**판정: 수정 유효 (CONFIRMED-FIXED).** V1의 공격(TERM 후 143 + 스테이징 잔존)은 재현되지 않는다. 공격 창이 실재함을 사전 관측으로 증명한 뒤 신호를 주었으므로 "창이 없어서 못 뚫린" 위양성이 아니다. `trap` 3종 + EXIT 트랩이 원래 종료 상태(143/130/129)까지 보존한다. 잔여 한계는 SIGKILL·전원 차단뿐이며 이는 trap으로 방어 불가 — 다만 acceptance는 **실제 비밀 리터럴을 저장소 루트에 평문으로 쓰는 절차**이므로, 이 잔여 위험을 없애려면 심는 값을 리터럴 대신 패턴에 매치하는 합성 값으로 바꾸는 편이 근본적이다(V2 권고, 이번 판정의 GO/NO-GO 조건은 아님).

---

## ④ 잔존 경로 목록 완전성 재공격 — 부분 CONFIRMED + NEW-FINDING ×3

### ④-a V1 목록의 재확인 (CONFIRMED)

실제 저장소 인벤토리 (`.git` 직접 점검):

```
absent : shallow / objects/info/alternates / rr-cache / modules / MERGE_HEAD /
         MERGE_MSG / SQUASH_MSG / CHERRY_PICK_HEAD / REVERT_HEAD / REBASE_HEAD /
         BISECT_LOG / rebase-merge / rebase-apply / info/refs / filter-repo
packs  : 없음 (.keep 팩·promisor 팩 없음).  loose object dirs: 62
refs   : refs/heads/main 6e52c77 / refs/heads/task/gptreview-verify-skills 4d53eac
         refs/heads/task/history-squash 2f4bf04 / refs/remotes/origin/main 9d0ffd9
stash  : 0건.  packed-refs: 헤더 한 줄뿐
logs   : .git/logs/HEAD, logs/refs/heads/{main,task/history-squash,task/gptreview-verify-skills}, logs/refs/remotes/origin/main
pseudo : .git/ORIG_HEAD -> 2f45b7b(오염 커밋)  ·  .git/FETCH_HEAD 없음
worktree admin: .git/worktrees/history-squash/{HEAD,index,ORIG_HEAD,COMMIT_EDITMSG,logs/HEAD}
         └ .git/worktrees/history-squash/ORIG_HEAD -> 6e52c77 (verify.sh 리터럴 보유 트리)
config : core.logallrefupdates true (gc.* 커스텀 없음)
```
V1이 든 경로(reflog·worktree HEAD reflog·ORIG_HEAD·FETCH_HEAD·stash·refs/original)는 실재하거나 실재 가능하며, 목록 자체는 **CONFIRMED**. 추가로 alternates/shallow/.keep 팩/서브모듈/rerere는 **이 저장소에 없음**을 실측으로 배제했다.

또한 V1이 제기한 "각 worktree reflog도 만료 대상"은 **`--all`이 이미 커버**함을 실측했다:
```
before: common logs/HEAD=5 | worktree logs/HEAD=4
git reflog expire --expire=now --expire-unreachable=now --all
after : common logs/HEAD=0 | worktree logs/HEAD=0
```
→ git 2.39.5에서 `--all`은 linked worktree의 HEAD reflog까지 비운다. (별도 명령 불필요 — 단, worktree admin dir가 **살아 있을 때만** 그렇다. ④-b 참조.)

`packed-refs` 텍스트 잔존도 반증했다: 팩된 브랜치를 `git branch -D` 하면 `packed-refs`가 재작성되고 `.git` 어디에도 삭제된 브랜치명 문자열이 남지 않았다(`grep -rl '<branch>' .git` → 0건).

### ④-b NEW-FINDING 1: stale worktree admin dir는 `gc --prune=now`를 뚫는 gc root

**공격:** 워크트리 디렉터리를 `git worktree remove` 대신 `rm -rf`로 지워 `.git/worktrees/<name>/` admin dir만 남긴 뒤, 계획된 정리(reflog expire --all → pseudoref 삭제 → gc --prune=now)를 완주.

**시나리오 A (worktree HEAD가 오염 커밋을 가리킴):**
```
after expire+gc --prune=now:
  BAD commit : EXISTS
  BAD blob   : EXISTS
  log --all -S hits: 1
  fsck --full --no-reflogs --unreachable : 0
  git worktree list -> .../wt  eca0ad6 (detached HEAD) prunable
```
→ 객체가 **완전히 살아남고**, `fsck`는 unreachable로 보고조차 하지 않는다(stale worktree HEAD가 정식 root로 취급됨). 이 경우는 acceptance check 1(`log --all -S`)이 1건으로 잡아낸다.

**시나리오 B (worktree HEAD는 깨끗하고, 그 index만 비밀 blob을 물고 있음):**
```
check1 git log --all -S hits      : 0
check5 cat-file -e BAD commit     : GONE
check6 for-each-ref extra refs    : []
check7 ORIG_HEAD/FETCH_HEAD       : NO
--- GROUND TRUTH ---
secret BLOB still in object db    : EXISTS
blob content recoverable          : PROBE_LEAK_TOKEN
pinned by                         : .../wt (detached HEAD) prunable
```
→ 커밋·refs·pseudoref 기준 모든 게이트가 음성인데 **평문 blob은 `git cat-file -p`로 그대로 복원**된다. 이 시나리오를 잡아낸 것은 오직 `fsck --full --unreachable`이 1을 반환한 것뿐이며(check 5), 그마저 "gc를 다시 돌리면 되겠지"로 오해하기 쉽다 — `gc --prune=now`는 이 객체를 **영원히 못 지운다**(worktree admin dir가 root이므로). 필요한 조치는 `git worktree prune` 또는 admin dir 제거다.

**계획서 대비:** 예정 절차의 "워크트리 제거"가 `git worktree remove`인지 `rm -rf`인지 명시되어 있지 않고, `git worktree prune` / `git worktree list`에 `prunable` 0건 확인 단계가 **없다**. acceptance에도 worktree 검사가 없다.

### ④-c NEW-FINDING 2: per-worktree `ORIG_HEAD`는 check 7의 사각지대

`scripts/acceptance-0-2.sh:82-85`는
```bash
GCD=$(git rev-parse --git-common-dir)
for p in ORIG_HEAD FETCH_HEAD; do [ -e "$GCD/$p" ] && FAIL; done
```
로 **common dir만** 본다. 실측한 실제 파일 `.git/worktrees/history-squash/ORIG_HEAD` = `6e52c77`(리터럴 보유 트리)는 이 검사에 걸리지 않는다. 예정 절차의 "ORIG_HEAD/FETCH_HEAD 삭제"도 대상이 common dir인지 per-worktree까지인지 불명확하다. worktree를 정상 제거하면 동반 삭제되지만, ④-b처럼 admin dir가 남으면 **삭제되지 않고 점검도 되지 않는다**.

### ④-d NEW-FINDING 3: acceptance의 `fsck`가 `--no-reflogs`를 빠뜨려 reflog 잔존을 못 본다

V1 보완 게이트 4는 `git fsck --full --no-reflogs --unreachable`을 명시했으나 구현된 `scripts/acceptance-0-2.sh:67`은
```bash
unreach=$(git fsck --full --unreachable 2>/dev/null | grep -c '^unreachable' || true)
```
로 `--no-reflogs`가 없다. 실측:
```
unreachable (default, reflogs count as roots): 0
unreachable (--no-reflogs):                    3
cat-file -e BAD after branch delete: EXISTS
```
→ **reflog로만 복구 가능한 오염 객체 3개가 존재하는 상태에서 check 5의 unreachable 카운트는 0**이다. 즉 reflog expire가 실패/부분 실패해도 이 게이트는 침묵한다.

이 사각지대는 check 5의 `cat-file -e` 화이트리스트가 **불완전**하기 때문에 더 커진다. `CONTAMINATED` 목록은 5개 SHA뿐인데 현재 `git log --all -S"$LIT"`는 **6건**을 반환한다(`965f084`가 목록에 없음). 더 근본적으로, 리터럴을 담은 **blob**은 `4d53eac`~`965f084` 구간의 모든 커밋 트리에 들어 있으므로(예: `6e52c77`, `45658ec`, `843cde3` 등) 5개 커밋 SHA만 검사하는 방식으로는 "객체 소멸"을 증명할 수 없다. 검증해야 할 것은 **blob SHA의 부재**다.

**판정: ④ 부분 CONFIRMED + NEW-FINDING ×3.** V1의 FAIL 판정과 경로 목록은 과장이 아니라 오히려 **불완전**했다. 다만 V1이 우려한 per-worktree reflog는 `--all`이 실제로 커버한다는 점에서 그 항목만은 완화된다.

---

## ⑤ 상관 블라인드스팟 — "오염 = 이 저장소 내부"라는 공유 가정 (NEW-FINDING, 치명)

**지목한 가정:** G(구현자)와 V1은 모두 오염의 경계를 `Valuehire_v6` 저장소 내부(커밋·refs·reflog·객체 DB)로 두고, goal 문서 ①의 "원격: `origin/main` = 9d0ffd9만. 오염 히스토리는 전량 미push → **유출 범위 로컬 국한**"을 검증 없이 승계했다. V1의 판정서 전체가 `.git` 내부 경로만 다룬다. 저장소 밖은 아무도 보지 않았다.

**실행 명령:**
```bash
LIT=$(head -1 .secret-patterns)
grep -rlF "$LIT" ~/.claude | wc -l
for g in $(find ~/Desktop -maxdepth 3 -name .git); do r=$(dirname $g); git -C "$r" grep -lF "$LIT" HEAD --; done
git -C ~/Desktop/Valueconnect-Ops for-each-ref refs/remotes ... + git grep -lF "$LIT" <remote-ref>
```

**관측 출력 요지:**

1. **다른 저장소의 원격 브랜치에 이미 push되어 있다.**
```
REPO: /Users/kangsangmo/Desktop/Valueconnect-Ops
    HEAD:docs/superpowers/specs/2026-05-18-weekly-growth-meeting-v2-design.md
origin  https://github.com/sangmokang/valueconnect-ops.git (fetch/push)

  refs/remotes/origin/fix/clickup-candidate-posting-qa477 -> matching files: 1
  refs/remotes/origin/fix/nudge-daily-dedup               -> matching files: 1
  (origin/main 및 나머지 7개 브랜치 -> 0)
commit afb5db06a87f 를 포함하는 원격 브랜치:
  origin/fix/clickup-candidate-posting-qa477
  origin/fix/nudge-daily-dedup
```
remote-tracking ref의 트리에 리터럴이 들어 있다는 것은 그 객체가 **원격에서 받아온 것**, 즉 GitHub에 이미 올라가 있다는 뜻이다.

2. **로컬 저장소 밖 평문 29개 파일** — Claude Code 세션 트랜스크립트(`~/.claude/projects/**/*.jsonl`, 서브에이전트 로그 포함), `~/.claude/history.jsonl`, `paste-cache/`, `file-history/`, 그리고 **다른 프로젝트의 memory 파일**(`projects/-Users-kangsangmo-Desktop-Valueconnect-Ops/memory/reference_gmail_app_password.md` 등).

3. `~/Desktop` 평문(.git·node_modules 제외) **64개 파일** — 대부분 `Valueconnect-Ops/reports/orchestrator/daily/*.html|md`.

4. 반면 `~/Desktop`는 iCloud Drive 동기화 대상이 **아님**(`FXICloudDriveDesktop = 0`, `CloudDocs/Desktop` 없음) — 이 경로로의 유출은 배제된다.

5. 이 저장소 자체는 계획대로 깨끗해질 수 있다: 저장소 트리 평문은 `REPO/verify.sh`(= main HEAD, 아직 미병합) 1건뿐이고 `docs/`는 양 트리 모두 clean, `task/history-squash` tip은 리터럴 0건이다.

**판정: NEW-FINDING (치명).** 0-2의 작업 자체는 유효하지만, **완료를 "유출 봉인"으로 보고해서는 안 된다.** goal 문서 ①의 "유출 범위 로컬 국한"은 실측으로 거짓이다. 0-2가 PASS해도 동일 비밀은 GitHub 원격 브랜치 2개와 로컬 90여 개 파일에 남는다. (사장님 2026-08-04 회전 거부 결정은 존중한다 — 여기서는 회전을 요구하지 않고, **사실관계가 그 결정의 전제와 다르다는 점만** 보고한다. 후속 조치 여부는 사장님 판단 사항.)

---

## ⑥ 예정 절차 vs V1 보완 게이트 — 항목별 O/X

예정 순서: 번들 백업 → .gitignore 훅 보존 → 병합 → 판정서 회수 → 워크트리 제거·브랜치 삭제 → `reset --soft 9d0ffd9` → 단일 커밋 → ORIG_HEAD/FETCH_HEAD 삭제 → `reflog expire --expire=now --expire-unreachable=now --all` → `gc --prune=now` → fsck·acceptance

| V1 보완 게이트 | 커버 | 근거 / 빠진 것 |
| --- | --- | --- |
| **1. 모든 worktree 포함 refs·pseudoref 위치를 번들과 함께 사전 기록** | **△** | 번들 백업은 O(계획 1단계, goal ⑧). 그러나 "refs·pseudoref 위치를 **열거·기록**"하는 단계가 순서에 없다. 사후 대조 기준선이 없으면 무엇이 사라졌는지 증명할 수 없다 |
| **2. rewrite 뒤 branch뿐 아니라 tag/remote/custom/refs\_original/replace/stash 열거·제거** | **△** | 절차에는 "브랜치 삭제"만 있다(현재 삭제 대상 `task/gptreview-verify-skills`=4d53eac, `task/history-squash`). tag·notes·replace·stash 열거 단계 없음. 다만 acceptance check 6의 화이트리스트(`main`·`origin/main` 외 전부 FAIL)가 **사후 검출**은 한다 → 절차 X, 검증 O |
| **3. 각 worktree reflog 포함 `reflog expire ... --all` + ORIG_HEAD/FETCH_HEAD 별도 처리** | **O(조건부)** | `--all`이 linked worktree HEAD reflog까지 비움을 실측 확인. 순서(pseudoref 삭제 → expire → gc)도 타당. **단 per-worktree `ORIG_HEAD`**는 worktree를 `git worktree remove`로 지웠을 때만 동반 삭제 — `rm -rf`면 남고 check 7도 못 본다(④-c) |
| **4. `gc --prune=now` 뒤 `fsck --full --no-reflogs --unreachable` + 옛 SHA `cat-file -e` 실패 확인** | **X** | 구현된 acceptance는 `--no-reflogs`가 **누락**되어 reflog 잔존을 0으로 보고한다(④-d 실측: 실제 3 vs 보고 0). `cat-file -e` 목록도 5개 SHA뿐이라 현재 `log --all -S` 6건과 불일치하고, 검사해야 할 **blob SHA**가 빠져 있다 |
| **5. ③ trap-safe 수정 + TERM/INT/HUP 테스트 PASS 후에만 rewrite 재개** | **O** | 143/130/129 + 잔존 0 실측(③). 이 게이트만 완전 충족 |
| *(V1 미제기, V2 추가)* **6. worktree admin dir / prunable 워크트리 제거·검증** | **X** | 절차·acceptance 모두 `git worktree prune`, `git worktree list`의 `prunable` 0건 확인이 없다. ④-b에서 이 경로가 `gc --prune=now`를 완전히 무력화함을 실증 |
| *(V1 미제기, V2 추가)* **7. 저장소 밖 잔존(원격·트랜스크립트) 처리** | **X** | 절차·AC 어디에도 없음. ⑤에서 GitHub 원격 브랜치 2개 + 로컬 90여 파일 실측 |

**요약: 완전 커버 1(게이트 5) / 조건부 1(게이트 3) / 부분 2(게이트 1·2) / 미커버 1(게이트 4) + V2 신규 미커버 2.**

---

## 실험 후 원복 확인 (실행 출력 그대로)

```
=== [RESTORE-1] worktree git status (history-squash) ===
?? docs/
(end)
=== [RESTORE-2] staged entries ===
(none above = clean index)
=== [RESTORE-3] plant/probe temp files on disk ===
none            # .acceptance-plant-*.tmp / .probe-index-write.tmp 전부 없음
=== [RESTORE-4] HEAD unchanged ===
2f4bf04
task/history-squash
=== [RESTORE-5] main repo status + refs unchanged ===
 M .gitignore
?? docs/
?? worktrees/
refs/heads/main 6e52c77
refs/heads/task/gptreview-verify-skills 4d53eac
refs/heads/task/history-squash 2f4bf04
refs/remotes/origin/main 9d0ffd9
=== [RESTORE-7] out-of-repo target of symlink test removed ===
removed
```
- SIGKILL 대조군이 남긴 `.acceptance-plant-72039.tmp`(실제 리터럴 평문)는 즉시 회수했다 — `removed .acceptance-plant-72039.tmp` → 이후 staged=[] / disk=[].
- 모든 스캐너·잔존경로 실험은 격리 임시 저장소(scratchpad)에서 **합성 토큰**으로만 수행했고, 실제 리터럴이 scratchpad에 유입되지 않았음을 확인했다(`grep -rlF "$LIT" <scratchpad>` → 0건).
- 커밋 0건, `git worktree`/refs/HEAD 변경 0건, main 무수정, squash·gc·reflog expire **실저장소 미실행**.

---

**VERDICT: NO-GO(① 공백·개행·하이픈 파일명으로 스캐너 우회 exit 0, ② 패턴 파일이 디렉터리·읽기불가·CRLF일 때 fail-open exit 0 — 이 둘이 살아 있으면 squash 후 "리터럴 0건 PASS"가 증거 능력을 갖지 못한다. 추가로 ④ stale worktree admin dir가 gc --prune=now를 무력화하고 acceptance의 fsck에 --no-reflogs가 빠져 reflog 잔존이 0으로 보고되며, ⑤ 동일 비밀이 이미 GitHub 원격 브랜치 2개에 push되어 있어 goal ①의 "유출 로컬 국한" 전제가 거짓이다. ③ trap 수정과 reflog expire --all은 유효 — 위 4건 보완 후 재판정하면 GO 가능.)**

---

# V2 재판정 (434039a)

- 대상: `task/history-squash` @ `434039a` ("fix: V2 적대검증 NO-GO 4건 보완")
- 방법: V2가 1차에서 성공시킨 공격을 **동일 절차·합성 토큰(`SYNTHSECRET42`, `PROBE_LEAK_TOKEN`)·격리 저장소**로 그대로 재현. 구현자 주장은 근거로 채택하지 않았고, 모든 판정은 아래 명령의 실제 출력에만 근거한다.
- 파괴 작업 미실행(squash·gc·reflog expire를 실저장소에서 돌리지 않음), 커밋 0건.

## (a) ①·② 공격 재현 — 전부 CLOSED

**실행 명령:** 격리 저장소에 새 `verify.sh`를 복사하고, 각 케이스마다 리터럴을 **스테이징한 상태**에서
```bash
git add -- <target>; bash verify.sh; echo "exit=$?"        # A 계열
SECRET_PATTERNS_FILE=<변형> bash verify.sh; echo "exit=$?"  # B 계열
```

| 공격 | 1차(2f4bf04) | 재현(434039a) 관측 | 판정 |
| --- | --- | --- | --- |
| 대조군 정상 파일명 | exit 1 | `FAIL: ... - plain.txt` / exit=1 | 검출 유지 |
| **A2 파일명 공백** | **exit 0 우회** | `FAIL: ... - my file.txt` / **exit=1** | **CLOSED** |
| **A3 파일명 개행** | **exit 0 우회** | `FAIL: ... - bad` `- name.txt` / **exit=1** | **CLOSED** |
| **A4 선행 하이픈** | **exit 0 우회** | `FAIL: ... - -dashfile.txt` / **exit=1** | **CLOSED** |
| **B1 디렉터리** | **exit 0 fail-open** | `FAIL: ... missing/not-a-file/unreadable/empty: patdir (exit 2)` / **exit=2** | **CLOSED** |
| **B5 주석뿐** | **exit 0 fail-open** | `FAIL: no effective secret patterns in pat-comment (주석/빈 줄뿐, exit 2)` / **exit=2** | **CLOSED** |
| **B6 퍼미션 000** | **exit 0 fail-open** | `FAIL: ... unreadable ... (exit 2)` / **exit=2** | **CLOSED** |
| **B8 CRLF** | **exit 0 fail-open** | `FAIL: ... - planted.txt` / **exit=1** (정규화 후 정상 검출) | **CLOSED** |
| B2 `/dev/null` · B3 없는 경로 · B4 빈 줄뿐 | 2·2·1 | exit=2 · exit=2 · **exit=2**(개선) | 유지/강화 |
| B9 빈 환경변수(기본값 폴백) | 1 | exit=1 | 유지 |

**V2가 이번에 새로 시도한 경계 5종(1차 미시도):**

| 신규 공격 | 관측 | 판정 |
| --- | --- | --- |
| N1 패턴 파일 = 디렉터리 심볼릭 링크 | `FAIL: ... not-a-file ... (exit 2)` | fail-closed O |
| N2 주석 + 유효 패턴 혼재 | `FAIL: ... - planted.txt` / exit=1 | 주석 제거가 검출력을 죽이지 않음 O |
| N3 잘못된 ERE(괄호 불균형) | `FAIL: scanner error — fail-closed (grep/xargs stderr): ! grep: parentheses not balanced` / exit=1 | fail-closed O |
| **A10 인덱스에만 리터럴, 워크트리 파일 삭제** | `FAIL: scanner error — fail-closed ... ! grep: ghost.txt: No such file or directory` / exit=1 | **구버전이면 무음 통과했을 경로가 새로 막힘** |
| A11 dangling 심볼릭 링크 추적 | 동일하게 fail-closed / exit=1 | O |
| A12 개행 파일명 + 정상 파일 혼재 | 리터럴 보유분만 FAIL / exit=1 | 오탐 없이 검출 O |

**판정: ①② 모두 CLOSED.** `ls-files -z | xargs -0 ... --`가 세 파일명 우회를 전부 닫았고, `-f`/`-r` 검사 + CRLF 정규화 + 유효 패턴 0개 exit 2 + **stderr 발생 시 fail-closed**가 fail-open 4종을 닫았다. 특히 stderr fail-closed는 1차에서 지적한 근본 원인(`2>/dev/null || true`의 은폐)을 제거해, 내가 이번에 새로 만든 A10·A11·N3까지 함께 막았다. 파일명 표시가 개행에서 두 줄로 쪼개지는 것은 **보고 형식의 흠**일 뿐 검출 자체는 성립한다(exit 1).

## (b) ④-b 시나리오 B 재현 — 새 check5/check8이 잡는다

**시도한 공격:** 1차와 동일하게 linked worktree의 **index만** 비밀 blob을 물게 한 뒤 `rm -rf`로 워크트리를 지워 admin dir만 남기고, 계획된 정리(reflog expire --all → pseudoref 삭제 → `gc --prune=now`)를 완주한 상태에서 새 acceptance를 실행.

**관측 출력 요지:**
```
GROUND TRUTH: secret blob EXISTS, BAD commit GONE
FAIL: unreachable 객체 1건 잔존 (reflog expire/gc --prune=now 미완)
FAIL: prunable 워크트리 1개 — stale admin dir가 오염 객체를 gc에서 살려둘 수 있음
  .../wt  9b7a02a (detached HEAD) prunable
FAIL: 워크트리 admin dir 잔존: .git/worktrees/ 아래 wt
acceptance exit=1
```
1차에서 "모든 게이트 음성인데 평문 blob 복원 가능"이던 상태가 이제 **3중으로 검출**된다(check5 unreachable + check8 prunable + check8 admin dir).

**대조군 1 — reflog에만 남은 오염 커밋(`--no-reflogs` 실효 검증):**
```
BAD2 reachable via reflog only: EXISTS
FAIL: unreachable 객체 3건 잔존 ...
  -> check5(--no-reflogs)가 reflog-잔존을 잡는가: YES
```
1차 실측(실제 3건 vs 보고 0건)의 사각지대가 닫혔다.

**대조군 2 — 정식 절차(`git worktree prune` 포함)로 정리 후:**
```
secret blob now: GONE / BAD2 commit now: GONE
```
객체가 실제로 소멸함을 확인했다.

**판정: ④-b·④-c·④-d 모두 CLOSED.** per-worktree `ORIG_HEAD` 검사(check7 루프)와 admin dir 검사(check8)도 소스·동작으로 확인했다.

## (c) NEW-FINDING (치명) — 새 acceptance는 **구조적으로 PASS할 수 없다**

**시도한 공격:** "보완된 게이트가 서로를 죽이지 않는가"를 물었다. 즉 **모든 다른 조건을 완벽히 충족한 squash 종료 상태**를 모사하고(단일 커밋, ref는 `refs/heads/main` 하나, 워크트리 0, pseudoref 0, unreachable 0, 실제 `.gitignore` 동일) 새 acceptance를 실행했다.

**실행 명령:**
```bash
git init -qb main repo && cp <verify.sh> <scripts/acceptance-0-2.sh> <.gitignore> .
printf 'SYNTHSECRET42\n' > .secret-patterns
git add -A && git commit -qm "단일 커밋(squash 종료 상태 모사)"
git reflog expire --expire=now --expire-unreachable=now --all && git gc --prune=now
bash scripts/acceptance-0-2.sh; echo "acceptance exit=$?"
```

**관측 출력 요지:**
```
종료 상태: refs=[refs/heads/main] commits=1 unreach=0 worktrees=1
PASS: no secret-pattern match in any tracked file, .env not tracked
NOTE: docs/ 없음(워크트리에서 실행 중) — 최종 판정은 main에서 재실행 필수
FAIL: unreachable 객체 1건 잔존 (reflog expire/gc --prune=now 미완)
acceptance exit=1

--- 실패 원인 객체 ---
unreachable blob c60398ae39ea8c4e9f6dccb6a5ec9fd09b62ce86
hash(plant literal) = c60398ae39ea8c4e9f6dccb6a5ec9fd09b62ce86      # 완전 일치

--- 멱등성 (매번 gc --prune=now 후 재실행) ---
run2 exit=1
run3 exit=1

--- 반증 대조군: check3(뮤테이션 블록 29~48행)만 제거하고 실행 ---
PASS: 0-2 완료 — 히스토리·객체·refs·pseudoref·docs 리터럴 0건, 스캐너 뮤테이션 검출 확인
no-mutation exit=0
```

**메커니즘:** check 3(뮤테이션)이 `echo "$LIT" > "$tmpf"` → `git add -- "$tmpf"`를 하는 순간 **리터럴 평문 blob이 object DB에 기록**된다. `cleanup_plant`의 `git rm --cached`는 **인덱스에서만** 떼어낼 뿐 객체는 남는다. 그 뒤 41행 아래 check 5(83행)의 `git fsck --full --no-reflogs --unreachable`이 바로 그 blob을 unreachable 1건으로 세어 `fail=1`을 만든다. 실행 순서(41행 add → 83행 fsck)상 **항상** 그렇다. 반증 대조군에서 check3만 빼면 같은 저장소가 exit 0으로 PASS하므로, 실패 원인이 check3의 자기 산출물임이 확정된다.

**두 가지 결과:**

1. **절차 11단계가 성립하지 않는다.** goal 문서 실행 절차 11은 "main에서 `bash scripts/acceptance-0-2.sh` → PASS(exit 0) 확인. **실패 시 2번 번들로 복구**"다. 이 AC는 어떤 상태에서도 exit 0을 낼 수 없으므로, **파괴적 squash를 마친 직후 반드시 롤백 조건이 발동**한다. 즉 계획대로 실행하면 되돌릴 수 없는 rewrite를 한 뒤 "실패" 판정을 받는다.

2. **AC 자신이 마지막으로 비밀을 object DB에 주입한다.** 계획 순서는 10) `gc --prune=now` → 11) acceptance다. 따라서 **정리가 끝난 뒤** acceptance가 평문 blob을 새로 써 넣고 그대로 종료한다. 실저장소에서 이미 관측된다(내 신호 테스트 실행분):
```
plant blob SHA = 6249997616fc734fa0f5d9f4008312c9dbd582be
실저장소 object db에 존재? EXISTS   (10 bytes, 어느 커밋도 참조하지 않음: 0건)
loose object 파일 실재: .git/objects/62/49997616fc734fa0f5d9f4008312c9dbd582be
현재 unreachable(--no-reflogs) 총계: 7 — 그중 리터럴 보유 blob 2개
    6249997616fc734fa0f5d9f4008312c9dbd582be (10 bytes)
    ef9bdfd83968ac9d89a25dd42dac612d9bc21135 (6561 bytes)
```
"object DB에 비밀이 없음"을 증명하는 스크립트가 실행 자체로 그 명제를 위반한다.

**부수 확인 — 오염 blob 하드코딩 목록의 정확도.** 실저장소 전 객체를 훑어 리터럴 보유 blob을 전수 열거한 결과 **8개**이며, acceptance에 하드코딩된 6개는 그 부분집합이다(`diff` 결과 6개는 정확히 일치, 누락 2개 = 위의 plant blob과 `ef9bdfd…`). 누락 2개는 모두 unreachable이므로 check5의 unreachable 게이트가 대신 커버한다 — 즉 목록 자체는 **틀리지 않았고**, 진짜 안전망은 unreachable 카운트다. 그런데 그 안전망이 (1)의 자기오염으로 상시 발화 상태가 되어 **신호 대 잡음이 0이 된다**: 진짜 잔존 1건과 자기 plant 1건을 구분할 방법이 스크립트 안에 없다.

**권고(최소 수정):** ⑴ check3의 심는 값을 실제 리터럴 대신 **패턴에 매치하는 합성 문자열**로 바꾼다(패턴이 리터럴 전체이므로, 패턴 파일에 테스트 전용 2행을 추가하거나 뮤테이션을 별도 임시 저장소에서 수행). ⑵ 그것이 어렵다면 check3을 check5 **이후**로 옮기고 종료 직전 `git gc --prune=now`로 자기 산출물을 회수한 뒤 재검한다. ⑶ 어느 쪽이든 "AC 실행이 object DB를 변경하지 않는다"를 별도 어서션으로 고정한다.

## ③ 회귀 재검 (편집된 acceptance)

새 코드에서도 신호 원복이 유지되는지 재측정했다.

| 신호 | 공격 창 관측 | exit | POST staged | POST disk |
| --- | --- | --- | --- | --- |
| TERM | `.acceptance-plant-16618.tmp` 디스크+스테이징 | **143** | [] | [] |
| HUP | `.acceptance-plant-18867.tmp` 디스크+스테이징 | **129** | [] | [] |
| INT(기본 처분 복원) | 동일 | **130** | [] | [] |

**판정: 회귀 없음(유효 유지).**

## (c) ⑥ 표 X 항목 해소 여부

| 1차 V2 지적 | 갱신된 절차/AC | 해소 |
| --- | --- | --- |
| 게이트1 △ — refs·pseudoref 사전 **기록** 단계 부재 | 절차 1 "사전 인벤토리 기록: `for-each-ref`, `worktree list --porcelain`, pseudoref 목록, 오염 blob/커밋 SHA" | **O** |
| 게이트2 △ — branch 외 ref 열거·제거 절차 부재 | 절차 6은 여전히 브랜치 2개만 명시. 다만 절차 1의 사전 인벤토리 + check6 화이트리스트가 전수를 커버 | **O(보완)** — 절차 문언은 여전히 브랜치만이나, 인벤토리+화이트리스트로 실질 커버 |
| 게이트3 O(조건부) — per-worktree ORIG_HEAD | 절차 5 `worktree remove`+`prune`, 절차 8 "per-worktree는 5단계에서 동반 삭제됨을 확인", check7 루프 | **O** |
| 게이트4 X — `--no-reflogs` 누락, blob 미검사 | check5에 `--no-reflogs` 추가 + 오염 blob 6개 `cat-file -e` (실측으로 목록 정확성 확인) | **O** |
| 게이트5 O — trap | 회귀 없음 재확인 | **O** |
| V2 추가6 X — worktree prune/prunable 검증 | 절차 5 + check8(prunable 0 + admin dir 0), 시나리오 B로 검출 실증 | **O** |
| V2 추가7 X — 저장소 밖 잔존 | goal "범위 밖으로 분리된 발견"에 사실만 기재, 별도 태스크로 분리. 회전 재요구 없음 | **O(범위 분리 타당)** |
| **(신규) AC 자기오염 → PASS 불가·object DB 재주입** | 없음 | **X** |

**7개 X/△ 중 7개 해소, 신규 X 1개 발생.**

## 실험 후 원복 확인 (실행 출력)

```
=== ③ 회귀 테스트 직후 실저장소 status ===
?? docs/
POST staged=[] disk=[]        (TERM/HUP/INT 3회 모두)
```
- 모든 ①②④ 공격은 격리 임시 저장소(`scratchpad/scan-test2`, `resid4`, `endstate2`)에서 **합성 토큰**으로만 수행했고, 각 케이스 종료 시 `git status --short` 공백·`git ls-files`가 `.gitignore`/`verify.sh`만 남음을 확인했다.
- 실저장소에서 실행한 것은 ③ 신호 회귀 3회뿐이며, 스테이징·디스크 잔존 0을 매회 확인했다.
- 커밋 0건, HEAD `434039a` 유지, refs 변경 0건, main 무수정, squash·gc·reflog expire **실저장소 미실행**.
- ⚠️ 회수 불가 잔여물 고지: ③ 테스트가 만드는 plant blob `6249997616…`(10 bytes, 리터럴 평문)가 실저장소 object DB에 unreachable 상태로 남아 있다. `git rm --cached`로는 지워지지 않으며 `gc --prune=now`로만 제거된다. 이는 위 (c) NEW-FINDING의 실물 증거이자, 예정 절차 10단계(gc) **이후**에 11단계(acceptance)를 두면 최종 상태에 동일한 blob이 남는다는 뜻이다. 나는 실저장소에서 gc를 실행하지 않았으므로(파괴 작업 금지) 이 blob은 squash 절차의 gc 단계에서 함께 제거되어야 한다.

VERDICT: NO-GO(①②④는 전부 CLOSED로 재현 실패 — 보완 유효. 그러나 새 acceptance는 check3이 심는 리터럴 blob을 check5의 `fsck --no-reflogs --unreachable`이 자기 자신의 잔존으로 세어 **어떤 상태에서도 exit 0이 불가능**하다(완벽한 종료 상태 모사에서 run1~3 모두 exit 1, check3만 제거하면 동일 저장소가 exit 0으로 PASS — 실측). 그 결과 절차 11단계가 파괴적 squash 직후 무조건 롤백 조건을 발동시키고, gc(10) 다음에 오는 acceptance(11)가 평문 비밀 blob을 object DB에 다시 써 넣어 0-2의 목적 명제 자체를 깬다. check3의 심는 값을 합성 문자열로 바꾸거나 check3을 check5 뒤로 옮기고 자기 산출물을 회수하도록 고치면 GO.)

---

# V2 3차 재판정 (236f657)

- 대상: `task/history-squash` @ `236f657` ("fix: 인수 스크립트가 스스로 비밀 blob을 심던 자기파괴 구조 제거")
- 방법: 구현자 주장은 근거로 채택하지 않고 전부 직접 재현·반증했다. 실저장소 변경 여부는 `.git` 전체 스냅샷 diff로, 나머지는 격리 저장소 + 합성 토큰(`SYNTHSECRET42`)으로 측정했다.
- 파괴 작업 미실행. 커밋 0건. 실저장소에 대한 쓰기 0건.

## (a) 실저장소 무접촉 검증 — CONFIRMED, 단 **NEW-FINDING 1건**

### a-1. 기준 측정: acceptance 실행 전후 `.git` 전체 스냅샷

`count-objects -v` 한 줄이 아니라 **object 파일 목록·refs·모든 reflog 파일 해시·index 해시·pseudoref 목록·status·worktree 목록**을 통째로 떠서 비교했다.

```
=== acceptance 실행 (실저장소) === exit=1   (squash 전이므로 FAIL 다수 — 정상)
=== BEFORE vs AFTER diff ===
IDENTICAL — 실저장소 무변경 (object db·refs·reflog·index·pseudoref·status 전부)

count-objects  before: count: 88 size: 352 in-pack: 0 packs: 0 ...
               after : count: 88 size: 352 in-pack: 0 packs: 0 ...
temp sandbox 잔존: 3 -> 3 / 카나리 보유 orphan sandbox: 0
```
조정자 보고(84→84)와 절대값은 다르지만(측정 시점 차이) **증감 0**이라는 결론은 동일하며, 나는 더 강한 기준(전체 스냅샷 동일)으로 확인했다. 2차 판정의 핵심 사유("check3이 실제 리터럴 blob을 object DB에 쓴다")는 **해소**되었다.

### a-2. 탈출 공격 매트릭스 (희생용 저장소에서 수행 — 실저장소 미사용)

| # | 공격 | 관측 | 판정 |
| --- | --- | --- | --- |
| A-1 | `TMPDIR`을 저장소 내부로 | exit=1, count 0, status 없음, 잔존물 없음 | 안전 |
| A-2 | `TMPDIR` 상대경로 + `CDPATH=/tmp` 오염 | exit=1, 오염 0 | 안전 |
| A-3 | `TMPDIR=/no/such/dir` | macOS `mktemp -d`는 무효 TMPDIR을 무시하고 기본 경로 사용 → 정상 동작 | 안전 |
| A-4 | `OLDPWD=/tmp/fake`(가짜 verify.sh 배치) 주입 | exit=1, 오염 0 — 서브셸의 `cd`가 OLDPWD를 재설정하므로 무효 | 안전 |
| A-5 | `PWD=/tmp` 오염 | exit=1, 오염 0 | 안전 |
| A-6 | PATH에 **실패하는 `mktemp` shim** | exit=1, cwd 잔존물 0 — 폴백으로 cwd를 쓰지 않고 `set -e`로 중단 | fail-closed |
| A-7 | `mktemp`가 **저장소 내부 경로**를 반환하도록 shim(침투형) | exit=1, count 0, `evil-sandbox` trap이 제거 | 안전 |
| A-8 | **서브셸(sandbox 구축) 도중 TERM** — 지연 0.05·0.1·0.15·0.2·0.3·0.5초 6회 | 전부 exit=143, tmp 디렉터리 증가 0, 카나리 보유 orphan 0, 저장소 오염 0 | trap 유효 |
| A-9 | 같은 지점 **SIGKILL**(무포착) | exit=137, **저장소 오염 0**(2차에서는 실제 리터럴이 스테이징·디스크에 잔존했음) | 구조적 개선 확인 |
| C-3 | 전역 `core.excludesFile`로 sandbox의 `git add planted.txt` 봉쇄 | exit=1, 저장소 오염 0 (위양성 PASS 아님) | fail-closed |

### a-3. **NEW-FINDING — git 환경변수 상속 시 sandbox가 실저장소로 샌다**

sandbox는 `cd`로만 격리되고 **git 환경변수를 차단하지 않는다.** 희생용 저장소에서 실측:

```
=== A-7: GIT_INDEX_FILE 이 설정된 채 실행 (pre-commit 훅 컨텍스트 모사) ===
  exit=1
  index 변화: CHANGED          ← sandbox의 git add가 실저장소 인덱스를 덮어씀
  status: [MM .gitignore]

=== A-7b: GIT_DIR 이 설정된 채 실행 ===
  exit=0                        ← ★ 위양성 PASS
  status: [ M .gitignore  AD planted.txt]
  count: 0 -> 4                 ← ★ 실저장소 object DB에 4개 객체 신규 기록

=== A-7c ===
  GIT_OBJECT_DIRECTORY 설정 → exit=1, count 0 -> 3   ← 객체 3개 유입
  GIT_WORK_TREE 설정        → exit=128, 오염 0        (fail-closed)
```

`GIT_DIR` 케이스는 **오염을 만들면서 동시에 exit 0 PASS**를 내므로 2차 NO-GO 사유와 동종의 결함이다. 다만 도달성을 실측했다:

```
ambient GIT_DIR=[unset] GIT_INDEX_FILE=[unset] GIT_WORK_TREE=[unset]
활성 훅(.sample 제외): (없음)
core.hooksPath: unset / init.templatedir: unset
```
계획된 실행 경로(절차 11 = 대화형 셸에서 `bash scripts/acceptance-0-2.sh`)에서는 이 변수들이 설정되지 않으므로 **이번 squash 실행 자체는 영향받지 않는다.** 그러나 이 AC는 0-5에서 CI/훅에 연결될 예정이고(goal ⑦), git 훅은 `GIT_DIR`·`GIT_INDEX_FILE`을 **항상** 설정한 채 스크립트를 부른다. 즉 지금은 잠복이고, 훅/CI에 붙이는 순간 발현한다.

**최소 수정:** 스크립트 상단에서 `unset GIT_DIR GIT_INDEX_FILE GIT_WORK_TREE GIT_OBJECT_DIRECTORY GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_COMMON_DIR`, 또는 sandbox 블록을 `env -u GIT_DIR -u GIT_INDEX_FILE ... bash -c '...'`로 감싼다. 한 줄이면 닫힌다.

## (b) 종료 상태 exit 0의 위양성 검증 — 위양성/위음성 모두 없음

**기준선(무결점 종료 상태 모사):** 단일 커밋, ref는 `refs/heads/main` 하나, 워크트리 1(주 워크트리만), `ORIG_HEAD` 없음, `reflog expire`+`gc --prune=now` 완료, unreachable 0.

```
PASS: no secret-pattern match in any tracked file, .env not tracked
PASS: 0-2 완료 — 히스토리·객체·refs·pseudoref·docs 리터럴 0건, 스캐너 뮤테이션 검출 확인
  exit=0 / count 0 -> 0 / status=[]
멱등성: run1 exit=0 count=0 / run2 exit=0 count=0 / run3 exit=0 count=0
```
2차 판정의 "어떤 상태에서도 exit 0 불가"는 **해소 확인**. 실행이 object DB를 늘리지도 않는다.

**개별 위반 매트릭스** — 각 check를 하나씩만 깨뜨리고 나머지는 완전한 상태로 두어 검출력을 확인했다.

| 위반 | 관측 exit | 발화한 FAIL |
| --- | --- | --- |
| check1 오염 커밋 1건 | 1 | `히스토리에 리터럴 커밋 1건 잔존` |
| check2 verify.sh 리터럴 하드코딩 | 1 | `verify.sh에 리터럴 하드코딩 잔존` |
| check2 `ls-files` 파이프라인에 `grep -v` 자기 면제 | 1 | `자기 면제/경로 제외(grep -v) 잔존` + 카나리 미검출 |
| check3 스캐너 무력화(verify.sh를 `exit 0`으로 치환) | 1 | `심은 카나리를 verify.sh가 못 잡음 — 스캐너가 조용히 무력화됨` |
| check4 `docs/` 비추적 파일에 리터럴 | 1 | `docs/ 실파일에 리터럴 잔존` |
| check5 unreachable 객체 1건 | 1 | `unreachable 객체 1건 잔존` |
| check6 잔존 브랜치 | 1 | `허용 외 ref 잔존` |
| check6 잔존 **태그** | 1 | `허용 외 ref 잔존` |
| check7 공통 `ORIG_HEAD` | 1 | `ORIG_HEAD 잔존` |
| check7 `FETCH_HEAD` | 1 | `FETCH_HEAD 잔존` |
| check8 stale worktree admin dir(`rm -rf`) | 1 | `per-worktree ORIG_HEAD 잔존` + `prunable 워크트리 1개` |
| check7c per-worktree `ORIG_HEAD` | 1 | `per-worktree ORIG_HEAD 잔존` |
| **대조군: 무결점** | **0** | (없음) |

12개 위반 전부 검출, 대조군만 통과. **exit 0은 위양성이 아니다.**

## (c) 합성 카나리 방식의 검출력 보증 — 유효, 단 **한계 1건 가시화**

### c-1. 실제 패턴이 실제 비밀을 매치하는지(디스크 기록 없이 메모리에서만 확인)
```
실패턴 → 실리터럴 매치: YES
카나리 패턴은 실리터럴을 매치하지 않음(정상 — 두 검증은 서로 독립)
실패턴에 ERE 메타문자 포함 개수: 0  (0이면 리터럴)
실패턴 파일 유효 패턴 줄 수: 1
```
카나리와 실패턴이 서로를 오염시키지 않음을 확인했고, **이번 실행에 쓰일 실제 패턴이 실제 리터럴을 매치한다**는 사실도 파일을 쓰지 않고 확인했다.

### c-2. 한계 — AC는 `.secret-patterns`가 "옳은 값"임을 보증하지 않는다
패턴 파일을 실제 비밀과 무관한 값으로 바꾸고, 비밀은 추적 파일에 그대로 둔 상태:
```
exit=0
  PASS: no secret-pattern match in any tracked file, .env not tracked
  PASS: 0-2 완료 — ...
실제로 추적 파일에 비밀 존재: HEAD:realsecret.txt
```
→ **비밀이 추적 파일에 버젓이 있는데 PASS.** 다만 이는 카나리 도입 때문이 아니다. 같은 시나리오를 구버전(`434039a`)으로 돌리면 exit 1이 나오지만 그 사유는 `unreachable 객체 1건`(= 구버전이 스스로 심은 blob)이지 **이 시나리오를 검출한 것이 아니다**. 즉 구버전은 상시 실패라 판별력이 아예 없었고, PASS가 도달 가능해진 지금에서야 이 한계가 관측 가능해진 것이다. 완화책은 c-1처럼 "패턴이 실비밀을 매치함"을 실행 직전 1회 확인하는 것이며, 나는 이번 실행분에 대해 그것을 확인했다.

### c-3. 한계 — 패턴이 ERE일 때 check1·2·4는 리터럴 검색이라 눈이 먼다
계약(goal ⑩)은 "한 줄당 ERE 1개"인데 acceptance의 check1은 `git log -S"$LIT"`(문자열), check2·4는 `grep -F`(고정 문자열)다. 메타문자 패턴 `SECRET[0-9]+X`로 실측:
```
exit=1   (verify.sh가 추적 파일에서 잡아 check2에서 실패)
check1 방식(-S literal) 히트: 0건
check4 방식(grep -F)   히트: 0건
```
추적 파일에 있으면 `verify.sh`(정규식 사용)가 잡아 주지만, **히스토리에만 있거나 `docs/`의 비추적 파일에만 있는 경우** check1·check4는 통과한다. 현재 실패턴은 메타문자 0개라 이번 실행에는 영향이 없다(c-1 실측). 향후 패턴을 정규식으로 바꾸면 이 두 검사가 조용히 무력해진다 — 기록해 둔다.

## (d) 절차 순서(gc 다음 acceptance) 안전성 — 안전

```
gc --prune=now 직후 acceptance: exit=0
  count 0 -> 0   size 0 -> 0   objects-listing IDENTICAL
  재fsck unreachable = 0
```
2차 판정의 두 번째 사유("gc(10) 다음의 acceptance(11)가 평문 blob을 다시 써 넣는다")는 **해소**. 실저장소에서도 전후 스냅샷이 동일했다(a-1).

부수 사항: 실저장소에는 **구버전 check3가 남긴 리터럴 blob 2개**가 unreachable 상태로 아직 있다.
```
unreachable: 6249997616fc734fa0f5d9f4008312c9dbd582be (10 bytes)
unreachable: ef9bdfd83968ac9d89a25dd42dac612d9bc21135 (6561 bytes)
```
둘 다 어떤 ref에서도 도달 불가이므로 절차 10단계 `gc --prune=now`에서 제거되고, 남으면 check5의 unreachable 게이트가 exit 1로 잡는다. 별도 조치 불필요 — 다만 **절차 10을 건너뛰면 안 된다**.

## 3차 판정 요약

| 항목 | 판정 |
| --- | --- |
| 2차 NO-GO 사유 ①(실리터럴 object DB 기록) | **해소** — 실저장소 스냅샷 전후 IDENTICAL |
| 2차 NO-GO 사유 ②(fsck 자기간섭으로 exit 0 불가) | **해소** — 종료 상태 exit 0, 3회 멱등 |
| 위양성 여부 | **없음** — 12개 개별 위반 전부 exit 1, 대조군만 exit 0 |
| 신호·sandbox 탈출(TMPDIR/CDPATH/OLDPWD/PWD/mktemp/TERM/KILL/excludesFile) | 전부 fail-closed 또는 무해 |
| **git 환경변수(GIT_DIR·GIT_INDEX_FILE·GIT_OBJECT_DIRECTORY) 상속 시 sandbox 탈출** | **NEW-FINDING** — 현 실행 경로에서는 미도달(ambient unset·훅 없음), CI/훅 연결 시 발현 |
| 카나리 방식의 검출력 | 유효. 단 패턴 오설정·ERE 패턴에 대한 보증은 없음(한계 명시) |
| 절차 순서(gc→acceptance) | 안전 |

## 실험 후 원복 확인 (실행 출력)

```
[R1] 워크트리 status: ?? docs/            (end)
[R2] staged: (empty=clean)
[R3] HEAD: 236f657 / task/history-squash
[R4] main repo refs:
  refs/heads/main 6e52c77
  refs/heads/task/gptreview-verify-skills 4d53eac
  refs/heads/task/history-squash 236f657
  refs/remotes/origin/main 9d0ffd9
[R5] main repo status:  M .gitignore / ?? docs/ / ?? worktrees/
[R6] count-objects: count: 88 size: 352 in-pack: 0 packs: 0 ...   (실행 전과 동일)
[R7] 임시파일: none
[R8] orphan sandbox(카나리 보유): 0
[R9] scratchpad 내 실제 리터럴: 0건
[R10] /tmp 실험 잔여물: none
```
- 모든 탈출·위반 실험은 격리된 희생용 저장소(`scratchpad/esc/victim`, `end3/repo*`)에서 **합성 토큰**으로만 수행했다. 실저장소에서 실행한 것은 acceptance 자체(무변경 확인용) 3회뿐이며, 매회 스냅샷 동일을 확인했다.
- 2차 판정 때와 달리 이번에는 **실저장소에 새로 유입된 리터럴 blob이 0건**이다(88 → 88).
- 커밋 0건, HEAD `236f657` 유지, refs·reflog·index 변경 0건, main 무수정, squash·gc·reflog expire 실저장소 미실행.

VERDICT: GO(2차 NO-GO 2건 모두 실측으로 해소 — 실저장소 스냅샷 전후 IDENTICAL(88→88, refs·reflog·index·pseudoref 전부), 무결점 종료 상태에서 exit 0 PASS 3회 멱등, 12개 개별 위반 전부 exit 1로 위양성 없음, TMPDIR·CDPATH·OLDPWD·PWD·mktemp 실패·서브셸 중 TERM/KILL·excludesFile 탈출 전부 fail-closed. 절차 순서(gc→acceptance)도 안전. 잔여 지적 2건은 이번 실행을 막지 않는다 — ⑴ `GIT_DIR`/`GIT_INDEX_FILE`/`GIT_OBJECT_DIRECTORY`가 환경에 있으면 sandbox가 실저장소로 새고 `GIT_DIR` 케이스는 위양성 PASS까지 내지만, 실측상 ambient 미설정·활성 훅 없음으로 계획된 실행 경로에서는 도달 불가이며 0-5에서 CI/훅에 붙이기 전 스크립트 상단 `unset` 한 줄로 닫아야 한다. ⑵ AC는 `.secret-patterns`가 실제 비밀과 일치함을 보증하지 않고 ERE 패턴에서는 check1·4가 눈이 머는데, 이번 실행분에 대해서는 "실패턴 → 실리터럴 매치 YES, 메타문자 0개"를 직접 확인했다. 단 절차 10 `gc --prune=now`는 생략 불가 — 구버전이 남긴 리터럴 blob 2개가 unreachable로 남아 있다.)
