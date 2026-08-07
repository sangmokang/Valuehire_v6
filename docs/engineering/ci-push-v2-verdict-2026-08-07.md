# CI/Push V2 독립 검증 판정서 — 2026-08-07

**단일 질문: 이 트리를 push하면 비밀이 유출되는가?**

| 항목 | 값 |
|---|---|
| 검증자 | 독립 검증 에이전트 (구현자 주장 무전제, 실측 only) |
| 저장소 | `/Users/kangsangmo/Desktop/Valuehire_v6` |
| 로컬 main | `23f65da5276eb0512434a520d861d1c7b47df824` |
| origin/main | `9d0ffd93580ce4ee523fe07f6e1315aa8dc40464` (`git ls-remote`로 원격 실측 확인) |
| 원격 | `https://github.com/sangmokang/Valuehire_v6.git` |
| push 대상 | 커밋 4건, 객체 32개, 추적 파일 12개 |
| 비밀 리터럴 | 본 문서에서 `$LIT`로만 참조 (길이 9자, `.secret-patterns` 1행) |

> **주의**: 배경 사실(어제까지 히스토리에 평문 비밀번호 존재, 2026-08-07 squash 청소)은 전제가 아니라 검증 대상으로 취급했다. 아래 항목 1·6이 그 검증에 해당한다.

---

## 0. 검증 도구 자체의 검출력 선행 확인 (모든 판정의 전제)

"0건"이라는 결과는 스캐너가 고장 났을 때도 나온다. 그래서 판정 전에 **내 스캐너가 실제로 검출하는지** 먼저 증명했다.

**[시도한 공격]** 내 스캔 루프가 조용한 no-op이라서 모든 판정이 위양성일 가능성.

**[실행 명령]**
```bash
# 격리 저장소에 $LIT을 심고, 본 검증에서 쓴 것과 동일한 루프로 검출되는지 확인
git init -q . && printf 'harmless\n%s\nmore\n' "$LIT" > poison.txt
git add poison.txt && git commit -qm "canary"
for obj in $(git rev-list --all --objects | awk '{print $1}'); do
  [ "$(git cat-file -t $obj)" = blob ] && git cat-file blob "$obj" | grep -q -F "$LIT" && echo "LOOP DETECTED $obj"
done
```

**[관측 출력]**
```
canary blob detected count=1  (expect 1 -> scanner WORKS)
LOOP DETECTED canary blob 1944e4e606fabc030c4aae8ccf51c8ba474aa917
```

또한 `.secret-patterns.default` 10개 패턴에 대해 9종 가짜 비밀(quoted / env / AKIA / ghp_ / sk- / xoxb- / AIza / BEGIN RSA PRIVATE KEY / user:pass@host)을 심어 검출력을 측정:
```
patterns that fired on canary: 9 / 10
```
(미발화 1건은 `ASIA[0-9A-Z]{16}` — 해당 형태의 샘플을 심지 않았기 때문이며 패턴 결함 아님.)

**[판정]** **PASS.** 이하 모든 "0건" 결과는 검출력이 실증된 도구로 얻은 것이다.

---

## 1. push 대상 객체 전수 스캔 (blob · 커밋 메시지 · 트리 이름 · 태그)

**[시도한 공격]**
- 파일 내용이 아닌 **커밋 메시지·author/committer 필드**에 비밀이 박혀 있을 가능성
- **경로/트리 이름** 자체가 비밀일 가능성
- **태그 객체**로 오염 조상이 살아남을 가능성
- 대소문자 변형으로 리터럴 스캔 회피
- live ref 밖(reflog 등)에 도달 가능 blob 잔존

**[실행 명령]**
```bash
# (a) push 대상 전 blob × 리터럴 (대소문자 구분 / 무시 양쪽)
for obj in $(git rev-list origin/main..main --objects | awk '{print $1}'); do
  [ "$(git cat-file -t $obj)" = blob ] && git cat-file blob "$obj" | grep -c -F  "$LIT"
  [ "$(git cat-file -t $obj)" = blob ] && git cat-file blob "$obj" | grep -ci -F "$LIT"
done

# (b) push 대상 전 blob × .secret-patterns.default 10개 패턴 (주석·빈 줄 제거 후, grep -E -i)
git show HEAD:.secret-patterns.default | grep -v '^[[:space:]]*#' | grep -v '^[[:space:]]*$' > pat.txt
# blob별 × 패턴별 이중 루프로 grep -E -i -q

# (c) 커밋 메타데이터
git log origin/main..main --format='%H%n%an%n%ae%n%cn%n%ce%n%s%n%b%n---' | grep -c -F "$LIT"

# (d) 경로/트리 이름
git rev-list origin/main..main --objects | awk '{print $2}' | grep -c -F "$LIT"

# (e) 태그
git tag -l

# (f) 저장소 전체(모든 ref) blob
for obj in $(git rev-list --all --objects | awk '{print $1}'); do ... done

# (g) 최종 원격 트리가 될 12개 파일 전수 (delta 밖 README.md 포함)
for f in $(git ls-files); do git show "HEAD:$f" | grep -c -F "$LIT"; done
```

**[관측 출력]**
```
=== rev-list origin/main..main --objects === 32 objects (커밋4 + 트리 + blob)
blob hits: 0
case-insensitive blob hits: 0
=== scanning each pushed blob against each pattern (grep -E -i) ===
=== scan complete ===          # PATTERN-HIT 줄 0개
0 (no match in commit metadata)
0 (no match in path names)
=== tags === (no tags above means none)
full-repo blob hits: 0
=== FULL HEAD tree scan (the exact 12 files the remote will hold) — literal ===
done (no HIT lines above = clean)
=== FULL HEAD tree scan — default patterns ===
done
```
`scripts/acceptance-0-2.sh`의 reflog 포함 전수 검사도 독립적으로 재실행:
```
PASS: 0-2 — 히스토리·객체·reflog·docs 리터럴 0건, 스캐너 뮤테이션 검출 확인
```

**[판정]** **PASS.** push 대상 32개 객체 어디에도 — blob 내용, 커밋 메시지, author/committer, 경로명 — 실제 리터럴도 default 패턴 매치도 **0건**. 태그 없음. reflog 포함 전 객체 0건. 배경 사실로 주어진 "squash 청소 완료"는 실측으로 **확인됨**.

---

## 2. `.secret-patterns`(실제 비밀 보유)가 push에 포함될 경로 — 전방위 공격

**[시도한 공격]** 6개 경로를 각각 두드렸다.

| # | 공격 벡터 | 결과 |
|---|---|---|
| A | gitignore 규칙이 실효 없음 | 차단됨 |
| B | 이미 추적 중(gitignore는 추적 파일에 무력) | 미추적 |
| C | `.gitattributes` 필터/변환으로 우회 | 파일 자체가 없음 |
| D | 워크플로우 artifact upload로 유출 | upload-artifact 스텝 없음 |
| E | 서브모듈/gitlink로 반입 | gitlink 0건, `.gitmodules` 없음 |
| F | 심볼릭 링크로 참조 | 심볼릭 링크(120000) 0건 |

**[실행 명령]**
```bash
git check-ignore -v .secret-patterns
git ls-files --error-unmatch .secret-patterns
ls -la .gitattributes .gitmodules
git ls-tree -r HEAD                     # 모드 확인 (160000 gitlink / 120000 symlink)
git show HEAD:.github/workflows/verify.yml | grep -nE 'upload-artifact|secrets\.|GITHUB_TOKEN'
# 결정적 실증: 실제로 클론해서 따라오는지 본다
git clone -q --no-local . "$SP/iso" && ls "$SP/iso/.secret-patterns"
```

**[관측 출력]**
```
.gitignore:21:.secret-patterns	.secret-patterns
error: pathspec '.secret-patterns' did not match any file(s) known to git
".gitattributes": No such file or directory (os error 2)
".gitmodules": No such file or directory (os error 2)
(no gitlinks)
=== symlinks? ===                       # 출력 없음
(none of upload-artifact/continue-on-error/if:/secrets./pull_request_target/GITHUB_TOKEN present)

=== does .secret-patterns follow the clone? ===
OK: .secret-patterns ABSENT in clone
=== clone file listing (working tree) ===   # 12개, .secret-patterns 없음
=== clone: literal anywhere in working tree? ===
OK: 0 hits in clone working tree
=== clone: literal in ANY object in clone object db? ===
clone object-db literal hits: 0
```
전 파일 모드는 `100644`/`100755`만 존재 (gitlink·symlink 0).

**[판정]** **PASS.** `.secret-patterns`가 원격에 도달할 경로가 **6개 벡터 모두에서 없음**. 격리 클론(= push가 전달하는 것과 동일한 도달 가능 객체 집합)에 작업 트리·object DB 양쪽 모두 리터럴 0건으로 실증됨.

---

## 3. `.secret-patterns.default`에 실제 비밀값이 있는가 / "모양"만 담았는가

**[시도한 공격]** 커밋되는 패턴 파일이 자기 오염되어, 비밀 스캐너가 곧 비밀 유출원이 되는 경우.

**[실행 명령]**
```bash
git show HEAD:.secret-patterns.default          # 전문 육안 검토
diff <(git show HEAD:.secret-patterns.default) .secret-patterns.default
# 실제 리터럴이 들어있는지 (acceptance-0-5 check3과 동일 로직)
grep -qF "$LIT" .secret-patterns.default
# CI의 자기오염 방지 스텝을 로컬에서 그대로 실행
grep -nE "^[^#]*=[A-Za-z0-9]{8,}[[:space:]]*$" .secret-patterns.default
```

**[관측 출력]**
```
SAME                                     # 커밋본 == 작업본
(항목 1의 전수 스캔에서 이 파일도 포함되어 리터럴 0건)
=== CI step 4 self-contamination check, run locally ===
PASS: 기본 패턴 파일에 실값 없음
```
파일 내용은 전부 정규식 형태다 — 자격증명 대입문 2종(따옴표형/env형), 클라우드 키 형식 6종(`AKIA`/`ASIA`/`gh[pousr]_`/`sk-`/`xox[baprs]-`/`AIza`), 개인키 블록 1종, 자격증명 박힌 URL 1종. 상수 문자열 값은 하나도 없다.

**[판정]** **PASS.** "모양"만 담았음이 확인됨. 항목 0에서 이 패턴들이 심은 가짜 비밀 9종을 실제로 잡는 것까지 확인했으므로, **값 없이 검출력만 있는 상태**라는 설계 의도가 실증됨.

---

## 4. `.github/workflows/verify.yml`이 실제로 검증을 강제하는가

**[시도한 공격]**
- 이름만 있고 아무것도 실행 안 하는 껍데기
- `continue-on-error`·조건부 `if:` skip으로 항상 초록
- 패턴 파일이 CI에 없어 스캔이 조용히 no-op
- `permissions` 과다(쓰기 권한 → 공급망 리스크)
- `pull_request_target` + secrets 조합(포크 PR 탈취)
- YAML 문법 오류로 워크플로우 자체가 미실행
- 액션 버전 노후/불명

**[실행 명령]**
```bash
ruby -ryaml -e 'd=YAML.safe_load(...); ...'      # 문법 + 구조 파싱
# 클린 클론(=.secret-patterns 없음, GitHub 러너와 동일 조건)에서 4개 스텝 전부 재현
git clone -q --no-local . ci && cd ci
bash verify.sh
bash scripts/acceptance-0-6.sh
while IFS= read -r -d '' f; do bash -n "$f"; done < <(git ls-files -z '*.sh')
grep -nE "^[^#]*=[A-Za-z0-9]{8,}[[:space:]]*$" .secret-patterns.default
```

**[관측 출력]**
```
YAML parses OK
keys: ["name", true, "permissions", "jobs"]
on: {"push"=>{"branches"=>["**"]}, "pull_request"=>nil, "workflow_dispatch"=>nil}
permissions: {"contents"=>"read"}
 step: actions/checkout@v4                        | coe=nil | if=nil
 step: 비밀 스캔 (verify.sh)                        | coe=nil | if=nil
 step: 인수 검사 0-6 (가짜 검증 스크립트 0건)         | coe=nil | if=nil
 step: 셸 스크립트 문법 검사                         | coe=nil | if=nil
 step: 패턴 파일 자체에 실제 비밀이 없는지            | coe=nil | if=nil

=== FULL CI SIMULATION (no .secret-patterns, exactly like GitHub runner) ===
--- step: 비밀 스캔 ---   PASS: no secret-pattern match in any tracked file, .env not tracked   rc=0
--- step: 인수 0-6 ---    PASS: 병합 완료, 가짜 검증 스크립트 0건                              rc=0
--- step: shell syntax ---                                                                    rc=0
--- step: self-contamination --- PASS
=== CI SIMULATION COMPLETE ===
```

**[판정]** **PASS (단, 문서 과대주장 1건 지적).**
- 껍데기 아님: 4개 스텝 전부 실제 명령을 실행하고 실패 시 non-zero로 잡 실패시킨다.
- no-op 경로 없음: `continue-on-error` 0건, 조건부 `if:` 0건. 패턴 부재 시 `verify.sh`가 **exit 2로 fail-closed**하도록 설계돼 있어 "패턴 없어서 조용히 통과"가 불가능하다.
- `permissions: contents: read` — 최소 권한. `secrets.*`·`GITHUB_TOKEN`·`pull_request_target` 미사용 → 포크 PR 탈취 벡터 없음.
- `actions/checkout@v4` — 현행 메이저, 유효.
- YAML 문법 정상 (Ruby `YAML.safe_load` 파싱 성공).

> **지적 (유출 아님, 문서 정확성 문제)**: `fetch-depth: 0` 주석이 *"히스토리 전량 — 비밀 스캔·인수 검사가 과거 커밋까지 본다"*고 적혀 있으나, `verify.sh`는 `git ls-files`(= 체크아웃된 커밋의 추적 파일)만 스캔하고 `acceptance-0-6.sh`도 히스토리를 보지 않는다. **CI는 히스토리를 스캔하지 않는다.** `fetch-depth: 0`은 비밀 스캔 측면에서 아무 효과가 없다. 주석을 사실에 맞게 고치거나, 히스토리 스캔 스텝을 실제로 추가해야 한다.

---

## 5. `scripts/acceptance-0-5.sh`의 위양성 PASS 경로

**[시도한 공격]**
- 스크립트가 지금 상태에서 그냥 PASS해버리는가 (= 판별력 0)
- 격리 클론 검사(check 4)가 실제로 클론을 만들고 검사하는가
- 카나리 검사가 실제 검출력을 가지는가
- **카나리의 `&&` 체인에서 `git add`가 실패해도 "검출 성공"으로 오독되는가** ← 핵심 반례

**[실행 명령]**
```bash
# (a) 현재 상태에서 실행 — push 미완료이므로 FAIL이 나와야 정상
bash scripts/acceptance-0-5.sh

# (b) 카나리 문자열이 default 패턴에 실제로 걸리는지
printf 'CHATGPT_%s=hunter2example\n' 'PASSWORD' > canarystr.txt   # 패턴 매치 개수 측정

# (c) 실제 클론에서 카나리가 "진짜로" 발동하는지 이유까지 분리
git clone -q --no-local . real && cd real
printf 'CHATGPT_%s=hunter2example\n' 'PASSWORD' > leak-canary.env.txt
git add leak-canary.env.txt; echo "git add rc=$?"
bash verify.sh; echo "exit=$?"

# (d) 반례: git add가 실패하는 조건(.gitignore에 *.txt)을 만들어 카나리를 무력화
printf '*.txt\n' > .gitignore
( printf 'CHATGPT_%s=hunter2example\n' 'PASSWORD' > leak-canary.env.txt \
    && git add leak-canary.env.txt && bash verify.sh >/dev/null 2>&1 ); echo "canary_rc=$?"
```

**[관측 출력]**
```
(a) FAIL: origin/main(9d0ffd9...) != main(23f65da...) — push 미완료
    0-5 exit=1
    → check 1·2·3·4는 통과, check 5(push 게이트)에서만 실패. 판별력 있음.

(b) default patterns matching the 0-5 canary string: 1   (>=1 => canary has real power)

(c) git add rc=0  (0 => add succeeded, canary really tracked)
    canary IS tracked
    FAIL: secret pattern matched in tracked files:
      - leak-canary.env.txt
    verify.sh on poisoned clone exit=1 (expect 1 = detection works)

(d) The following paths are ignored by one of your .gitignore files: leak-canary.env.txt
    canary_rc=1
    -> 0-5 records NO failure => SILENT FALSE-POSITIVE PASS (canary never actually ran)
```

**[판정]** **CONDITIONAL PASS — 오늘은 진짜로 동작하나, 잠복 위양성 1건 확인.**
- 현 상태에서 0-5는 **정확히 push 게이트에서만 실패**한다. 러버스탬프가 아님이 실증됨.
- 격리 클론 검사는 실제로 클론을 만들고(`clone rc=0`), 로컬 전용 패턴 파일이 따라오지 않음을 확인하며, 클린 환경에서 `verify.sh` exit 0을 요구한다 — 실판별력 있음.
- 카나리는 **오늘 실제로 발동한다**: `git add` 성공(rc=0) → 파일 추적 확인 → `verify.sh`가 잡아서 exit 1. 검출 사유까지 분리 확인함.
- **[결함 — 잠복]** check 4 카나리는 다음 형태다:
  ```bash
  ( cd "$sandbox/repo" && printf ... > leak-canary.env.txt \
      && git add leak-canary.env.txt && bash verify.sh >/dev/null 2>&1 )
  canary_rc=$?
  if [ "$canary_rc" -eq 0 ]; then echo "FAIL: ..."; fi
  ```
  `&&` 체인이라 **`printf`나 `git add`가 실패해도 `canary_rc != 0`이 되어 "스캐너가 잡았다"로 오독**된다. 즉 *"카나리가 검출됨"*과 *"카나리를 심는 데 실패함"*을 구분하지 못한다. 반례 (d)로 `canary_rc=1`이면서 스캐너가 한 번도 돌지 않는 상태를 재현했다.
  현재 `.gitignore`에는 이를 유발하는 규칙이 없어 **오늘의 판정에는 영향 없다**. 다만 향후 `.gitignore`에 `*.txt`/`*.env*` 계열 규칙이 추가되면 이 검사가 조용히 무의미해진다.
  **권고 수정**: `git add`까지를 별도로 검사하고 실패를 명시적 FAIL로 처리 —
  ```bash
  ( cd "$sandbox/repo" && printf ... > leak-canary.env.txt && git add -f leak-canary.env.txt ) \
      || { echo "FAIL: 카나리를 심지 못함 — 검사 무효"; fail=1; }
  ( cd "$sandbox/repo" && bash verify.sh >/dev/null 2>&1 ); canary_rc=$?
  ```

---

## 6. push 후 되돌릴 수 없는 위험 / 원격에 올라가면 안 되는 파일

**[시도한 공격]**
- `git push`가 main 외 브랜치까지 밀어 예상 밖 객체를 올릴 가능성
- `git ls-files` 12개 중 원격에 있으면 안 되는 파일
- 원격 저장소가 **public**이라 유출 반경이 무한대일 가능성
- 원격 baseline이 주장(`9d0ffd9`)과 다를 가능성

**[실행 명령]**
```bash
git for-each-ref --format='%(refname) %(objectname:short)'
git worktree list
git config --get push.default; git config --get remote.origin.push
git config --get branch.main.remote; git config --get branch.main.merge
git rev-list main..task/ci-push --objects | wc -l
git ls-files
gh repo view sangmokang/Valuehire_v6 --json name,visibility,isPrivate,pushedAt,defaultBranchRef
git ls-remote --heads origin
```

**[관측 출력]**
```
refs/heads/main            23f65da
refs/heads/task/ci-push    23f65da        # main과 동일 커밋
refs/remotes/origin/main   9d0ffd9

push.default: (unset -> 'simple')
remote.origin.push: (unset)
origin / refs/heads/main                   # `git push`는 main만 전송

objects unique to task/ci-push (NOT in main): count: 0

git ls-files (12):
  .claude/skills/gptreview/SKILL.md
  .claude/skills/verify/SKILL.md
  .claude/skills/verify/local-checks.sh
  .github/workflows/verify.yml
  .gitignore
  .secret-patterns.default
  README.md
  SKILLS_GUIDE.md
  scripts/acceptance-0-2.sh
  scripts/acceptance-0-5.sh
  scripts/acceptance-0-6.sh
  verify.sh

{"defaultBranchRef":{"name":"main"},"isPrivate":true,"name":"Valuehire_v6",
 "pushedAt":"2026-08-03T13:06:40Z","visibility":"PRIVATE"}

9d0ffd93580ce4ee523fe07f6e1315aa8dc40464	refs/heads/main
```

**[판정]** **PASS.**
- 원격 baseline이 주장과 **정확히 일치**(`git ls-remote` 실측 = `9d0ffd9`). fast-forward push이며 원격 히스토리 파괴 없음.
- `push.default=simple` + `branch.main.merge=refs/heads/main` → `git push`는 **main만** 전송. 설령 `--all`을 써도 `task/ci-push`는 main과 동일 커밋이고 고유 객체 **0개**라 추가 내용물이 없다.
- 추적 12개 파일 전부 항목 1에서 전수 스캔 통과. 원격에 있으면 안 되는 파일 **0건**(비밀 파일·`.env`·자격증명·개인키 없음). `verify.sh`의 `.env` 추적 검사도 통과.
- **저장소가 PRIVATE**이므로 설령 잔여물이 있었더라도 노출 반경이 조직 내부로 한정된다. 다만 본 판정은 private에 의존하지 않는다 — public이어도 유출될 내용이 없다.
- **되돌릴 수 없는 위험 없음**: 올라가는 4개 커밋에 비밀이 0건이므로 "GitHub가 객체를 영구 보존한다"는 성질이 리스크로 전환되지 않는다.

---

## 7. 구현자가 놓쳤을 법한 것 — 검증자 자체 지목

세 가지를 스스로 골라 검증했다.

### 7-a. **CI는 이 프로젝트 자신의 비밀 리터럴을 맨몸으로는 못 잡는다** (잔여 갭)

**[시도한 공격]** 설계상 `.secret-patterns`(실제 리터럴)는 CI에 없다. 그렇다면 **누군가 실수로 $LIT을 그냥 커밋했을 때 CI가 잡는가?**

**[실행 명령]**
```bash
printf 'some text\n%s\nmore text\n' "$LIT" > bare.txt        # 맨몸 리터럴
printf 'CHATGPT_PASSWORD=%s\n' "$LIT"      > bare2.txt        # KEY=값 형태
# 각각 .secret-patterns.default 10개 패턴으로 매치 개수 측정
```

**[관측 출력]**
```
default patterns matching a BARE literal line: 0   (0 => CI blind to this project's own literal)
default patterns matching KEY=<literal>:       1
(literal length = 9)
```

**[판정]** **경고 — 유출 아님, 잔여 리스크.** $LIT은 9자 일반 단어형이라 `AKIA`/`ghp_`/`sk-` 같은 형식 패턴에 걸리지 않는다. `KEY=값` 형태로 적히면 잡히지만, **문서 본문·주석·산문 안에 맨몸으로 적히면 CI는 통과시킨다.** 과거 사고(E1)가 정확히 `SKILLS_GUIDE.md`/`settings.json` 같은 **문서 안 평문**이었다는 점에서 이 갭은 실제 재발 시나리오와 겹친다.
→ CI를 로컬 `verify.sh`(=`.secret-patterns` 보유)의 **대체재로 믿으면 안 된다**. 로컬 pre-push 훅으로 `verify.sh`를 강제하거나, GitHub 저장소 시크릿 없이도 동작하도록 리터럴의 **해시**(예: salt+SHA256 목록)를 `.secret-patterns.default` 옆에 커밋하는 보강을 권고한다. 오늘의 push에는 영향 없음(리터럴 0건 확인).

### 7-b. **`.gitignore` 강화분이 커밋되지 않은 채 남아 있다** (다음 사고의 씨앗)

**[실행 명령]**
```bash
git diff .gitignore
git status --porcelain
```

**[관측 출력]**
```
 M .gitignore
+# 비공개 리뷰 결과 (원본 코드 재포함 가능 - 유출 방지)
+.claude/private-reviews/
+gptreview-*.md
+verify-*.json
```

**[판정]** **경고 — 이번 push에는 무해, 다음 push에 위험.** 이 3개 규칙은 **커밋되지 않았고 push 대상에도 없다.** 따라서 원격의 `.gitignore`는 이 보호막이 **없는** 상태로 올라간다. 이후 누구든(또는 새 클론에서) `git add -A`를 하면 `gptreview-*.md`(원본 코드·리뷰 전문 포함 가능)와 `verify-*.json`이 그대로 커밋된다. 현재 로컬 미추적 파일 12건(`docs/`, `worktrees/`)에는 $LIT이 0건임을 확인했으나(`grep -rlF` → 0 hits), 구조적 구멍은 남는다.
→ push 직전 또는 직후에 `.gitignore` 강화분을 별도 커밋할 것.

### 7-c. **`SKILLS_GUIDE.md`의 `.env` 템플릿에 값이 남았는가** (E1 재발 지점)

과거 사고에서 `SKILLS_GUIDE.md`가 평문 비밀번호 보유 파일 중 하나였으므로 직접 확인했다.

**[실행 명령]**
```bash
git show HEAD:SKILLS_GUIDE.md | grep -nE 'CHATGPT_(PASSWORD|EMAIL)=.+'
for f in $(git ls-files); do git show "HEAD:$f" | grep -nEo '[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}'; done
```

**[관측 출력]**
```
OK: all such lines have empty values (template only)
=== ITEM 7a: residual credential material (account IDs / emails / URLs) in the pushed tree ===
--- (above = email-shaped strings in pushed files) ---     # 결과 0건
```
해당 블록은 `CHATGPT_EMAIL=` / `CHATGPT_PASSWORD=` — 우변이 비어 있는 순수 템플릿이다.

**[판정]** **PASS.** 값도 없고, push 대상 12개 파일 전체에 이메일 형태 문자열조차 **0건**. 계정 식별자(비밀번호의 나머지 절반)도 유출되지 않는다.

---

## 8. 실험 후 원복 확인

본 검증에서 실저장소에 대한 쓰기는 하지 않았다. 모든 오염 실험은 scratchpad의 **별도 `git init` 저장소**와 **`git clone --no-local` 격리 클론**에서만 수행했다(실저장소 object DB 무접촉). push·커밋·히스토리 변경·main 수정 **일절 없음**.

**[실행 명령]**
```bash
git rev-parse HEAD; git rev-parse origin/main
git for-each-ref --format='%(refname) %(objectname)'
git status --porcelain
git fsck --full --no-reflogs --unreachable | grep -c '^unreachable'
git stash list | wc -l
git worktree list
bash verify.sh; bash scripts/acceptance-0-2.sh; bash scripts/acceptance-0-6.sh
git check-ignore -v .secret-patterns
```

**[관측 출력]**
```
HEAD:        23f65da5276eb0512434a520d861d1c7b47df824   (expect 23f65da... ✓)
origin/main: 9d0ffd93580ce4ee523fe07f6e1315aa8dc40464   (expect 9d0ffd9... ✓)
refs/heads/main            23f65da5276eb0512434a520d861d1c7b47df824
refs/heads/task/ci-push    23f65da5276eb0512434a520d861d1c7b47df824
refs/remotes/origin/main   9d0ffd93580ce4ee523fe07f6e1315aa8dc40464
--- status ---   M .gitignore / ?? docs/ / ?? worktrees/      # 검증 시작 시점과 동일
--- unreachable objects (fsck) --- 0
--- stash --- 0
--- worktrees --- 2 (main, worktrees/ci-push)                 # 검증 시작 시점과 동일

verify.sh=0
0-2=0
0-6=0
0-5: FAIL: origin/main != main — push 미완료 (push 게이트 외 전부 통과)

.secret-patterns: present, 10 bytes
.gitignore:21:.secret-patterns	.secret-patterns
untracked (good)
```
scratchpad에 심었던 카나리·오염 클론은 전부 삭제 완료(`iso`, `ci`, `real`, `fp`, `canaryrepo`, `*.txt` 임시파일).

**[판정]** **원복 확인.** HEAD·origin/main·refs·worktree·status 모두 검증 시작 시점과 동일. **unreachable 객체 0건** — 내 실험이 실저장소 object DB에 어떤 잔여물도 남기지 않았음을 실증. `.secret-patterns`는 10바이트 그대로, 여전히 미추적·ignore 상태.

---

## 종합

| 항목 | 판정 |
|---|---|
| 0. 검증 도구 검출력 선행 확인 | PASS (카나리 실증) |
| 1. push 대상 객체 전수 (blob/메시지/트리명/태그) | PASS — 0건 |
| 2. `.secret-patterns` 반입 경로 6종 | PASS — 전 경로 차단, 클론 실증 |
| 3. `.secret-patterns.default` 자기 오염 | PASS — 모양만, 값 0 |
| 4. `verify.yml` 강제력 | PASS (주석 과대주장 1건 지적) |
| 5. `acceptance-0-5.sh` 위양성 | CONDITIONAL PASS (잠복 결함 1건, 오늘 미발현) |
| 6. 되돌릴 수 없는 위험 / 파일 목록 | PASS — private, fast-forward, 12파일 전부 클린 |
| 7. 검증자 자체 지목 (3건) | 7-a 경고 / 7-b 경고 / 7-c PASS |
| 8. 원복 | 확인 — unreachable 0건 |

**결론**: `origin/main..main`의 커밋 4건·객체 32개·추적 파일 12개 전부를 실제 리터럴(대소문자 양쪽)과 `.secret-patterns.default` 10개 패턴으로 전수 스캔한 결과 매치 **0건**이며, 커밋 메시지·author/committer·경로명·태그에도 0건이다. 스캐너의 검출력은 카나리로 선행 실증했다. `.secret-patterns`가 원격에 도달할 경로는 gitignore/추적상태/gitattributes/artifact/서브모듈/심볼릭링크 6개 벡터 모두에서 존재하지 않으며, 격리 클론에서 파일 부재와 object DB 리터럴 0건으로 실증했다. 원격은 PRIVATE이고 baseline이 주장과 일치해 fast-forward이다.

발견된 결함 3건(4의 `fetch-depth` 주석 과대주장, 5의 카나리 `&&` 체인 잠복 위양성, 7-a의 CI 리터럴 맹점)과 경고 1건(7-b `.gitignore` 강화분 미커밋)은 **모두 "이번 push로 비밀이 유출되는가"에 대한 답을 바꾸지 않는다.** 전부 *향후* 유입을 놓칠 가능성에 관한 것이며, 현재 트리에 유출될 비밀이 0건이라는 실측을 무효화하지 않는다.

**후속 권고 (push를 막지는 않음)**
1. `acceptance-0-5.sh` check 4 카나리를 `git add` 실패와 검출 성공이 구분되도록 분리 (항목 5 권고 코드).
2. `verify.yml`의 `fetch-depth: 0` 주석을 사실에 맞게 수정하거나 히스토리 스캔 스텝을 실제 추가.
3. `.gitignore` 강화분(`.claude/private-reviews/`, `gptreview-*.md`, `verify-*.json`)을 커밋.
4. 프로젝트 고유 리터럴에 대한 CI 검출력 보강(해시 기반) 또는 로컬 pre-push 훅으로 `verify.sh` 강제.

VERDICT: SAFE-TO-PUSH
