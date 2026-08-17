VERDICT: PARTIAL

- **PR #4 (task/secret-session-patterns)** — 핵심 기전은 진짜다. 결함 3건(중 3). 조건부 머지 가능.
- **PR #5 (task/size-and-ignore)** — 훅 쪽은 진짜다. 그러나 **선언한 PASS 문구 중 하나("CI 경로 패턴이 훅과 동치")가 가짜다**. 결함 5건(고 1 · 중 4). 머지 전 수정 권고.

검증 환경: 대상 저장소는 읽기 전용으로만 다뤘다. 모든 뮤테이션은 스크래치패드의 `--no-hardlinks` 클론에서 수행했다.
브리핑에 적힌 기대 출력(`CHECKED: 20` / `CHECKED: 22`)은 구버전이다. **실제 PR 본문은 `CHECKED: 21` / `CHECKED: 23`을 선언**하고, 실측도 21 / 23으로 일치한다. 이 항목은 결함이 아니다.

---

## 1. 반증 시도 기록

무효한 "PASS"를 배제하기 위해, 각 검사에 대해 **"이걸 이렇게 깨뜨리면 스크립트가 못 잡을 것"** 이라는 가설을 세우고 실제로 깨뜨렸다. 총 19종.

### 1-A. PR #4 / `acceptance-hs-a3.sh` — 8종 시도, 6종 반증 실패(= 검사 유효), 2종 성공(= 결함)

| # | 깨뜨린 방법 | 예상 | 실측 결과 | 판정 |
|---|---|---|---|---|
| M1 | `.secret-patterns.default`의 값-자리 패턴 `['\"]name['\"]…` 한 줄 삭제 | 격리 케이스만 빨개짐 | `FAIL: 통과됨(놓침) — CDP 직렬화(값 모양 미상)` **1건만** / exit 1 | 반증 실패 → 검사 유효 |
| M2 | 값-모양 패턴 `AQED[A-Za-z0-9_-]{30,}` 삭제 | 해당 항목만 | `FAIL — 값 모양만(키 이름 변조)` **1건만** / exit 1 | 반증 실패 |
| M3 | 세션 패턴 전량(27줄 이후) 삭제 | 다수 FAIL | 13건 미탐 + **종단 1건** FAIL / exit 1 | 반증 실패 |
| M4 | **`verify.sh`에서 `grep -i` 제거** (판정기 2벌 시나리오 — 패턴은 그대로 두고 스캐너만 무력화) | ①~④ 자체 파이프라인은 전부 초록이라 못 잡을 것 | `FAIL: 스캐너 종단 — 세션 쿠키 파일을 verify.sh 가 차단 (기대 exit=1, 실제 0)` / exit 1 | **반증 실패 → 종단 검사가 실제로 작동한다** |
| M5 | `verify.sh`를 `exit 0` 스텁으로 교체 (완전 fail-open) | — | 종단 FAIL / exit 1 | 반증 실패 |
| M6 | **`must_catch` 5줄 삭제** (검사 자체를 약화) | 하한이 있으면 잡을 것 | **`CHECKED: 16` / exit 0 / FAIL 0건** | **반증 성공 → 결함 D1** |
| M7 | 스크립트가 `README.md`를 건드리게 개조 | 오염 감지 작동? | `FAIL: 이 검사가 저장소를 오염시켰다` / exit 1 | 반증 실패 → 오염 감지 유효 |
| M8 | 패턴 파일을 `.`(전부 매칭)으로 교체 | 오탐 대조군이 잡나? | 오탐 5건 + 종단 통과 대조군 1건 FAIL / exit 1 | 반증 실패 → 차단/통과 한 쌍 유효 |

추가로 **RED 재현**: 현재 테스트셋을 `origin/main`의 패턴 파일로 실행 → `FAIL 14건 / exit 1`. RED는 진짜다.
(PR 본문의 "구현 전 FAIL x7"은 초판 테스트셋 기준이라 현재 스크립트와 맞지 않는다 — 판정에 영향 없음.)

**P13④ 자기 면제 없음 확인**: 스크립트는 카나리를 런타임에 `printf`로 조립하고 파일명 제외를 쓰지 않는다. 병합 트리에서 `bash verify.sh` → `PASS`(자기매칭 0건). 자기 면제 경로 없음.

**P20 0건 경로 확인**: 패턴 파일이 없거나 유효 패턴 0개면 `NOT_RUN` + `CHECKED: 0` + **exit 2**로 나간다(`acceptance-hs-a3.sh:40-54`). 0건이 조용히 통과하는 경로는 없다.

### 1-B. PR #5 / `acceptance-hs-a4.sh` — 11종 시도, 5종 반증 실패, 6종 성공(= 결함)

| # | 깨뜨린 방법 | 실측 결과 | 판정 |
|---|---|---|---|
| N1 | 훅 `hooks/pre-commit`에서 `*/artifacts/*` **만** 제거 | `FAIL: pre-commit 통과함 — 하위 경로 아티팩트` / exit 1 | 반증 실패 → 유효 |
| N2 | 훅 `--diff-filter=ACMR` → `ACM` | `FAIL: git mv 로 검사를 우회했다 (rc=0)` / exit 1 | 반증 실패 |
| N3 | 훅 크기 측정을 인덱스 → 작업트리(`wc -c`) | `FAIL: 작업트리 덮어쓰기로 크기 검사를 우회했다` / exit 1 | 반증 실패 |
| N7 | `.gitignore` 앵커 제거 (`/data/` → `data/`) | `FAIL: src/data/schema.json 이 조용히 무시된다` / exit 1 | 반증 실패 |
| — | 정상 파일 대조군(README.md) | PASS | 반증 실패 |
| **N4** | **CI 쪽에서만** `private-reviews/`·`*.sqlite*`·`*.ndjson`·`*.parquet` 패턴 제거 (훅은 그대로 = 실제로 훅과 CI가 갈라짐) | **exit 0 / `CHECKED: 23` / `PASS: CI 경로 패턴이 훅과 동치`** | **반증 성공 → D4** |
| **N5** | CI 스캔 스텝 + hs-a4 스텝 양쪽에 `if: false` 추가 | **exit 0 / `PASS: CI 경로 패턴이 훅과 동치`** | **반증 성공 → D4** |
| **N6** | CI 스캔 스텝을 **통째로 삭제**하고 패턴 문자열만 `echo` 미끼로 남김 | **exit 0 / `PASS: CI 에 크기 검사 본문 존재` + `PASS: CI 경로 패턴이 훅과 동치`** | **반증 성공 → D4** |
| **N8** | `run_hook_case` 4줄 삭제 | **`CHECKED: 19` / exit 0** | **반증 성공 → D6** |
| **N9** | `mktemp`를 항상 실패시키는 스텁을 PATH에 주입 | **실제 저장소의 `README.md`가 덮어써지고 스테이지됨 + `core.hooksPath`가 조용히 변경됨** | **반증 성공 → D5** |
| **N10** | 병합 트리에서 `verify.yml`의 hs-a3 / hs-a4 등록 줄만 삭제 | **모든 로컬 검사 exit 0** | **반증 성공 → D2·D8** |

---

## 2. 결함 목록

### D4 [HIGH · PR #5] "CI 경로 패턴이 훅과 동치"는 훅을 보지 않는다 — 문자열 4개 grep

`scripts/acceptance-hs-a4.sh:246-254`

```bash
  miss=""
  for pat in '\*/artifacts/\*' '\*/data/\*' '\*\.db-\*' '\*\.jsonl'; do
    if ! printf '%s\n' "$ACTIVE" | grep -q -- "$pat"; then miss="${miss} ${pat}"; fi
  done
  if [ -z "$miss" ]; then
    ok "CI 경로 패턴이 훅과 동치 (하위경로·사이드카·덤프 포함)"
```

`hooks/pre-commit:189-190`의 case 블록은 **14개 패턴**인데, 이 검사는 그중 **4개를 하드코딩해서 CI 파일 안에 문자열로 존재하는지만** 본다. 훅 쪽 소스는 한 번도 읽지 않는다. 따라서:

1. **CI가 훅보다 좁아져도 "동치" PASS** (N4) — `private-reviews/`·`*.sqlite`·`*.sqlite3`·`*/private-reviews/*`·`*.ndjson`·`*.parquet` 6개가 CI에서 사라져도 초록.
2. **CI 스텝이 `if: false`로 죽어도 PASS** (N5).
3. **CI 스텝이 통째로 삭제되고 `echo` 한 줄만 남아도 PASS** (N6) — `PASS: CI 에 크기 검사 본문 존재 (cat-file -s)`(`:239`)도 같이 뚫린다.

위반 원칙: **P16**(소스 텍스트가 아니라 런타임 동작을 검사한다 — 이 검사는 정확히 `readFileSync`+`toContain` 류다) · **P15③**(로컬에만 있는 검사는 없는 것으로 친다 — CI 등가물이 죽어도 못 잡는다) · **P13②**(검사 약화 탐지).

`hooks/pre-push:100-102`에 `if: false` 탐지가 있으나 **CI에는 없다**(`verify.yml` 전체에 해당 코드 0건 — 실측). P15③ 기준으로 로컬 전용이므로 N5의 방어선으로 셀 수 없다. N4·N6은 어디서도 안 잡힌다.

재현:
```bash
S=$(mktemp -d); git clone -q --no-hardlinks -b task/size-and-ignore /Users/kangsangmo/Desktop/Valuehire_v6 "$S/w"; cd "$S/w"
python3 - <<'EOF'
p='.github/workflows/verify.yml'; s=open(p).read()
i=s.index("      - name: 대용량 파일 · 산출물 경로 스캔"); j=s.index("      - name: 인수 검사 hs-a4")
open(p,'w').write(s[:i]+'      - name: 미끼\n        run: |\n          echo "cat-file -s */artifacts/* */data/* *.db-* *.jsonl"\n\n'+s[j:])
EOF
bash scripts/acceptance-hs-a4.sh | grep -E 'CI|CHECKED'; echo "exit=$?"
# → PASS: CI 에 크기 검사 본문 존재 / PASS: CI 경로 패턴이 훅과 동치 / CHECKED: 23 / exit=0
```

수정 방향: 훅의 case 블록과 CI의 case 블록을 **하나의 파일**(예: `contracts/artifact-paths.txt`)에서 읽게 하고, 인수 검사는 그 파일과 두 소비처를 대조하라. 또는 최소한 두 case 블록 본문을 추출해 문자열 동등 비교하라 — 지금은 "동치"라는 단어만 출력한다.

---

### D5 [MED · PR #5] 대조군 절(§4)에 mktemp 가드가 없어 실제 저장소를 오염시킨다

`scripts/acceptance-hs-a4.sh:208-226`

```bash
tmp=$(mktemp -d)          # ← :208  가드 없음
git init -q "$tmp"
mkdir -p "$tmp/hooks"
cp hooks/pre-commit hooks/pre-push "$tmp/hooks/"
...
(
  cd "$tmp" || exit 9     # ← tmp="" 이면 cd "" 는 rc=0, 현재 디렉터리(= 실제 저장소)에 머문다
  git config core.hooksPath hooks
  ...
  printf '# hello\n' > README.md
  git add README.md
```

같은 파일 `:80-82`가 이 사고를 이미 적어놨다("mktemp 실패를 통과로 처리하면 검증기가 오염원이 된다 … user.name·hooksPath 가 덮어써지고 1.2MB 파일이 스테이지됐다"). 그 교훈을 `run_hook_case`(:83-87) · 3-b(:144-145) · 3-c(:170-171)에는 적용했는데 **§4에만 빠졌다**.

실측 (클론에서 재현):
```
--- before: hooksPath=[] README md5=0b9a3c85… status=[]
--- after : hooksPath=[hooks] README md5=487deb05…
M  README.md
```
스크립트 자신의 오염 감지가 `README.md` 변경은 잡아 exit 1을 냈지만, **`core.hooksPath` 변경은 `git status`에 안 나오므로 감지되지 않고 영구히 남는다**.

재현:
```bash
S=$(mktemp -d); git clone -q --no-hardlinks -b task/size-and-ignore /Users/kangsangmo/Desktop/Valuehire_v6 "$S/w"
mkdir -p "$S/bin"; printf '#!/bin/sh\nexit 1\n' > "$S/bin/mktemp"; chmod +x "$S/bin/mktemp"
cd "$S/w"; git config --get core.hooksPath; PATH="$S/bin:$PATH" bash scripts/acceptance-hs-a4.sh >/dev/null 2>&1
git config --get core.hooksPath; git status --porcelain    # → hooks / M  README.md
```

수정: :208을 `run_hook_case`와 같은 3줄 가드로 맞춰라. 더 근본적으로는 임시 저장소 생성을 함수 하나로 합쳐 가드가 한 곳에만 있게 하라(지금은 같은 코드가 4벌이고, 그중 1벌만 틀렸다).

---

### D1 / D6 [MED · PR #4 · PR #5] `CHECKED` 하한이 없어 검사를 지우면 조용히 통과한다 (P20)

`scripts/acceptance-hs-a3.sh:173-177` · `scripts/acceptance-hs-a4.sh:257-261`

```bash
if [ "$checked" -eq 0 ]; then
  echo "FAIL: 검사 항목 0개 — 0건 처리로 통과는 금지한다 (P20)"
```

`checked`는 스크립트 안의 호출 횟수로 정해지므로 **0이 될 수 없다** — 이 가드는 구조적으로 도달 불가능한 죽은 코드다. 실제로 막아야 할 것은 "0건"이 아니라 **"어제보다 줄어든 건수"**다. 하한(`21` / `23`)을 어디서도 단언하지 않는다:

- A3: `must_catch` 5줄 삭제 → `CHECKED: 16` / **exit 0** / FAIL 0건
- A4: `run_hook_case` 4줄 삭제 → `CHECKED: 19` / **exit 0** / FAIL 0건

P13②의 약화 탐지도 못 잡는다. `.check-weakening-patterns`는 `|| true`·`continue-on-error`·`if: always()` 등 **추가된 줄**의 패턴만 보는데(`hooks/pre-commit:42-52` `scan_added`는 diff의 `+`만 읽는다), 이건 **순수 삭제**라 원리적으로 탐지 범위 밖이다.

재현:
```bash
cd <클론>
sed -i '' '/must_catch "Bearer 인증 헤더"/d' scripts/acceptance-hs-a3.sh
bash scripts/acceptance-hs-a3.sh | tail -1; echo "exit=$?"   # → CHECKED: 20 / exit=0
```

수정: 두 스크립트 끝에 `MIN_CHECKS`를 상수로 두고 `[ "$checked" -lt "$MIN_CHECKS" ] && FAIL` 하라. 상수 변경은 diff에 남아 리뷰 대상이 된다.

---

### D2 / D8 [MED · PR #4 · PR #5] 두 인수 검사의 CI 등록을 지키는 장치가 없다 (P15③)

`.github/workflows/verify.yml` (PR#4 +3줄 / PR#5 +31줄)

CI 등록 자체는 **진짜다** — 확인함: 두 PR이 추가한 것은 실제 `run:` 줄이고, `bash -n`(문법검사)도 아니고 주석·`if:` 조건부도 아니다.

```yaml
      - name: 인수 검사 hs-a3 (세션 계열 자격증명 탐지)
        run: bash scripts/acceptance-hs-a3.sh
      - name: 인수 검사 hs-a4 (대용량·산출물 차단이 실제로 도는가)
        run: bash scripts/acceptance-hs-a4.sh
```

문제는 **그 줄이 나중에 사라져도 아무도 못 잡는다**는 것이다. `hooks/pre-push:60`의 `DEFERRED`는 `acceptance-0-5`·`acceptance-0-7`만 담고 있고, `RUNVERB` 대조(:92-97)는 그 둘과 `# PUSH-PERFORMING` 선언 스크립트에만 적용된다. `hs-a3`·`hs-a4`는 pre-push 글로브(:112)로 **로컬에서만** 돌기 때문에, CI 등록 줄을 지워도 로컬은 전부 초록이다.

실측(병합 트리에서 등록 줄만 삭제):
```
scripts/acceptance-hs-a3.sh      exit=0
scripts/acceptance-hs-a4.sh      exit=0
scripts/acceptance-0-7.sh        exit=0
verify.sh                        exit=0
```

**이 결함은 D9(충돌)와 결합할 때 실제 위험이 된다** — 아래 참조.

수정: `hooks/pre-push`의 `RUNVERB` 대조를 `DEFERRED` 고정 목록이 아니라 **발견된 모든 `acceptance-*.sh`** 에 적용하라(이미 글로브가 있으니 루프를 재사용하면 된다).

---

### D9 [MED · 교차] `verify.yml` 충돌을 사람이 해소하며, 잘못 해소해도 감지되지 않는다

두 PR이 본문에 예고한 대로 실제 충돌한다. 실측:
```
$ git merge origin/task/secret-session-patterns   # OK
$ git merge origin/task/size-and-ignore
CONFLICT (content): Merge conflict in .github/workflows/verify.yml
```

- 해소 시 PR#5 쪽 스텝이 빠지면 → `acceptance-hs-a4.sh`의 §5가 FAIL을 낸다(자동 감지됨).
- **해소 시 PR#4 쪽 `hs-a3` 스텝이 빠지면 → 아무도 못 잡는다**(D2). CI는 초록, 로컬도 초록, 그런데 세션 자격증명 인수 검사가 CI에서 전혀 안 돈다.

양쪽을 다 채택해 해소한 상태는 검증했다 — 전부 초록이다:
```
verify.sh                    exit=0  PASS: no secret-pattern match in any tracked file
scripts/acceptance-hs-a3.sh  exit=0  CHECKED: 21
scripts/acceptance-hs-a4.sh  exit=0  CHECKED: 23
scripts/acceptance-0-6.sh    exit=0  PASS
scripts/acceptance-0-7.sh    exit=0  PASS
CI 히스토리 전량 blob 스캔 재현 : blob 97개, hit=0
CI 대용량·산출물 경로 스캔 재현 : 추적 파일 전량, fail=0
```
→ **병합 자체는 안전하다.** 단 충돌 해소 후 `verify.yml`에 CI 스텝 3개(`hs-a3` · 대용량 스캔 · `hs-a4`)가 전부 있는지 **사람이 눈으로 확인해야 한다**.

---

### D3 [MED · PR #4] 패턴 파일 주석의 커버리지 주장 2건이 실측으로 거짓

`.secret-patterns.default:42-43` · `:56`

```
#   · SESSION_ID / SESSIONID 키 — "sessionIdHeader" 같은 설정 '이름'과 구분이 안 된다.
#     실제 세션 값은 아래 (6) 값 모양으로 잡는다.        ← 거짓
...
# (8) Set-Cookie 응답 헤더 / cookies.txt 형태            ← cookies.txt 는 안 잡힌다
```

(6)은 `AQED…`(LinkedIn)와 `ajax:숫자`(LinkedIn JSESSIONID) **두 가지 형태뿐**이다. 사람인·잡코리아 등 다른 포털의 세션 값(16진·base64)은 값 모양으로 잡히지 않는다. (8)의 `SET-COOKIE[[:space:]]*:` 는 리터럴 `Set-Cookie:` 헤더를 요구하는데, Netscape `cookies.txt`는 헤더가 없는 **탭 구분 7필드** 포맷이라 매칭되지 않는다.

실측 (병합 트리의 패턴 파일 기준, 탭 구분 · 값은 전부 더미):
```
CAUGHT   Netscape cookies.txt (탭, li_at + AQED 값)      ← (6) 덕분이지 (8) 때문이 아니다
MISSED   Netscape cookies.txt (탭, PHPSESSID 16진 값)
MISSED   Netscape cookies.txt (탭, JSESSIONID 16진 값)
MISSED   storageState — 목록 외 쿠키 이름 + 16진 값
MISSED   storageState — 목록 외 쿠키 이름 + base64 값
MISSED   document.cookie = 'sessionid=' + '<16진>'
MISSED   curl -b 'sessionid=<16진>'
CAUGHT   storageState — li_at (목록 내)
CAUGHT   Set-Cookie: sessionid=… (대조군)
```

재현:
```bash
cd <병합 트리>
CLEAN=$(mktemp); tr -d '\r' < .secret-patterns.default | grep -vE '^[[:space:]]*(#|$)' > "$CLEAN"
TAB=$(printf '\t'); P=$(printf 'PHPSESS%s' 'ID')
printf 'www.saramin.co.kr%sTRUE%s/%sTRUE%s1799%s%s%sa1b2c3d4e5f60718293a4b5c6d7e8f90\n' "$TAB" "$TAB" "$TAB" "$TAB" "$TAB" "$P" "$TAB" \
  | grep -qEif "$CLEAN" && echo CAUGHT || echo MISSED     # → MISSED
```

이것은 "구멍이 있다"가 아니라 **"구멍의 위치를 문서가 틀리게 적었다"**가 요점이다. PR 본문은 이 두 키를 "의도적으로 뺀 것"으로 정직하게 선언했으나, 그 대체 방어선으로 지목한 (6)이 실제로는 LinkedIn 전용이다. v6의 주 대상이 사람인·잡코리아인 점을 감안하면 주석을 사실대로 고쳐야 한다(패턴 추가 여부는 오탐 트레이드오프이므로 별건).

---

### D7 [MED · PR #5] `*/data/*` 가 모든 깊이의 `data` 디렉터리를 영구 차단하고 억제 경로가 없다

`hooks/pre-commit:189-190`

훅은 `data/*|*/data/*`를 모든 깊이에서 막는다. `.gitignore`는 P3(조용한 실패)를 피하려고 `/data/`로 최상위 앵커만 걸었다 — 즉 **`src/data/schema.json`은 gitignore되지 않지만 훅이 영구히 차단**한다. `acceptance-hs-a4.sh:201-205`(3-d)는 "조용히 사라지지 않는다"만 단언하고, **커밋할 수 있는지는 단언하지 않는다**.

실측:
```
BLOCKED: 산출물·데이터 경로는 커밋하지 않는다 — docs/data/note.md (P21 · 후보자 PII)
BLOCKED: 산출물·데이터 경로는 커밋하지 않는다 — src/data/schema.json (P21 · 후보자 PII)
pre-commit exit=1
```

`hooks/pre-commit`의 `suppressions.yaml` 소비처는 §3(검사 약화)뿐이고 **§7 경로 차단에는 억제 경로가 전혀 없다**(grep으로 확인). 즉 정상 소스 파일 하나가 `data/` 아래 있으면 `--no-verify` 말고는 커밋 방법이 없다.

이는 PR #4가 명시적으로 피하겠다고 선언한 실패 양식과 같은 것이다 — *"평범한 코드가 막히면 훅 우회 습관이 생긴다"*(`acceptance-hs-a3.sh:98`). A3는 오탐 대조군 5종을 세웠는데, A4의 대조군은 **루트의 `README.md` 하나뿐**(`:207-231`)이라 이 비대칭을 잡지 못한다.

재현:
```bash
cd <병합 트리>; t=$(mktemp -d); git init -q "$t"; mkdir -p "$t/hooks"
cp hooks/pre-commit hooks/pre-push "$t/hooks/"; cp verify.sh .secret-patterns.default .check-weakening-patterns .gitignore suppressions.yaml "$t/"
chmod +x "$t/hooks/"*
( cd "$t" && git config core.hooksPath hooks && git config user.email a@b.c && git config user.name t \
  && mkdir -p src/data && printf '{"a":1}\n' > src/data/schema.json \
  && git add src/data/schema.json && bash hooks/pre-commit )   # → BLOCKED / exit 1
rm -rf "$t"
```

수정: `data/` 는 최상위 앵커(`data/*`)만 훅에서 막고 하위 경로는 확장자·크기 규칙에 맡기거나, §7에 `suppressions.yaml` 경유 억제(만료일 필수)를 열어라. 어느 쪽이든 A4의 오탐 대조군에 `src/data/*` 케이스를 추가해 결정을 검사로 고정해야 한다.

---

## 3. 정조준 항목별 답

| # | 항목 | 판정 |
|---|---|---|
| 1 | **뮤테이션** — 인수 스크립트가 실제로 위반을 잡는가 | **A3 통과** — 패턴 삭제 3종·스캐너 무력화 2종 전부 격리 탐지. 특히 `verify.sh`의 `grep -i` 제거를 종단 검사가 잡는다(판정기 2벌 방지가 진짜다). **A4 훅 쪽 통과** — 경로·rename·인덱스측정·앵커 4종 전부 격리 탐지. **A4 CI 쪽 실패** — D4 |
| 2 | **0건 공허 통과(P20)** | **부분 실패** — 0건 경로 자체는 막혀 있으나(A3는 `NOT_RUN`+exit 2), `CHECKED`에 **하한이 없어** 검사를 지우면 조용히 통과한다. D1·D6 |
| 3 | **자기 면제(P13④)** | **통과** — 두 스크립트 모두 파일명·자기 리터럴 제외를 쓰지 않는다. A3는 카나리를 런타임 `printf` 조립으로 만들어 자기매칭을 피한다(`:59-72`, 파일명 제외를 금지한다는 주석 `:21` 포함). `bash verify.sh` 병합 트리 실행 결과 자기매칭 0건 |
| 4 | **CI 등록의 실질(P15③)** | **통과(현재) + 결함(미래)** — 추가분은 진짜 `run:` 실행 줄이다. `bash -n`·주석·`if:` 조건부 아님. 그러나 그 줄이 사라져도 감지하는 장치가 없다. D2·D8·D9 |
| 5 | **훅과 CI 동치 주장** | **실패** — 문자열만 출력하는 수준은 아니지만, **훅을 읽지 않고** CI 파일에서 하드코딩 4개 문자열을 grep할 뿐이다. 3종 뮤테이션 전부 초록 통과. D4 |
| 6 | **오염** | **통과(정상 경로)** — 실행 전후 HEAD·`git status`·`core.hooksPath`·원격 전부 동일. GIT_DIR 계열 8종 `unset`(`hs-a3:30-31`, `hs-a4:27-28`)과 시작/종료 `git status` 대조가 실제로 작동함을 M7로 확인(일부러 오염시키니 `FAIL`). **단 `mktemp` 실패 시 A4가 실제 저장소를 오염시킨다** — D5 |

---

## 4. 검증 위생 (실행 전후 대조)

대상 저장소의 추적 파일·인덱스·config·원격을 **하나도 바꾸지 않았다.**

### 실행 전
```
Valuehire_v6             HEAD=ec201dc04222f908e3403083719f61867ac7cb25 status=[] hooksPath=[hooks] remote=https://github.com/sangmokang/Valuehire_v6.git
secret-session-patterns  HEAD=f5f16b1eaf69c4eb4e5f18ee07e38bb4c58ed8c8 status=[] hooksPath=[hooks] remote=(동일)
size-and-ignore          HEAD=ad9d1dfa6a3066d669ce883380b7ee41202513af status=[] hooksPath=[hooks] remote=(동일)
humansearch-plan         HEAD=06fa3a3bf3248b632dec2ab13acb0a573aaada7d status=[] hooksPath=[hooks]
```

### 실행 (두 인수 스크립트를 각자의 실제 워크트리에서 1회씩)
```
$ cd worktrees/secret-session-patterns && bash scripts/acceptance-hs-a3.sh
  PASS: 스캐너 종단 — 정상 파일은 verify.sh 가 통과 (verify.sh exit=0)
  PASS: 저장소 무오염 (시작/종료 상태 동일)
  CHECKED: 21
$ cd worktrees/size-and-ignore && bash scripts/acceptance-hs-a4.sh
  PASS: CI 경로 패턴이 훅과 동치 (하위경로·사이드카·덤프 포함)
  PASS: 저장소 무오염 (시작/종료 상태 동일)
  CHECKED: 23
```

### 실행 후 (전과 완전 동일)
```
Valuehire_v6             HEAD=ec201dc04222f908e3403083719f61867ac7cb25 status=[] hooksPath=[hooks]
secret-session-patterns  HEAD=f5f16b1eaf69c4eb4e5f18ee07e38bb4c58ed8c8 status=[] hooksPath=[hooks]
size-and-ignore          HEAD=ad9d1dfa6a3066d669ce883380b7ee41202513af status=[] hooksPath=[hooks]
humansearch-plan         HEAD=06fa3a3bf3248b632dec2ab13acb0a573aaada7d status=[] hooksPath=[hooks]
원격: origin https://github.com/sangmokang/Valuehire_v6.git (fetch/push) — 변경 없음
브랜치: main, task/humansearch-plan, task/secret-session-patterns, task/size-and-ignore + origin/* — 신규/삭제 없음
```

모든 뮤테이션(19종)은 `git clone --no-hardlinks`로 만든 스크래치패드 사본에서만 수행했다. 대상 저장소에는 `git rev-parse` · `git status` · `git diff` · `git log` · `git show` 등 읽기 명령과, 워크트리 안에서의 인수 스크립트 1회 실행만 있었다.

---

## 5. 머지 권고

| PR | 권고 | 조건 |
|---|---|---|
| **#4** | **머지 가능** | D1(`CHECKED` 하한)과 D3(주석 정정)은 후속 이슈로 분리해도 된다. 핵심 기전(패턴 + 종단 스캐너 검사)은 뮤테이션 5종으로 입증됐다 |
| **#5** | **D4 수정 후 머지** | D4는 PR이 선언한 4개 PASS 문구 중 하나가 **입증되지 않은 상태로 초록**이라는 뜻이다 — P16 그 자체이며 이 저장소가 명시적으로 금지한 패턴이다. D5는 같이 고치는 게 싸다(3줄) |
| **양쪽** | 병합 순서 무관, 단 `verify.yml` 충돌을 **양쪽 채택**으로 해소하고 스텝 3개 존재를 눈으로 확인 | D9. 양쪽 채택 상태는 검증 완료(전 검사 초록) |
