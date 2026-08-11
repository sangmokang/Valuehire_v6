# 비밀 스캔 — 웹훅·벤더 키 패턴 (goal)

- **작성일**: 2026-08-12 · **위험 등급 L3** (비밀 스캔 = 보안 경로, 훅·CI 실동작 변경)
- **지시**: 2026-08-12 사장님 — *"지금 처리해"* (`git stash` 에 묶여 있던 패턴 수정을 정식 PR로 되살린다)
- **AC 식별자**: AC-S1
- **작업 폴더**: `worktrees/secret-webhook-vendor/` · 브랜치 `task/secret-webhook-vendor` (base: `main` 32ce698)

---

## ⑪ 사장님 브리핑

### 결론

지금 이 저장소의 비밀 검사기는 **Discord·Slack 알림 주소와 앤트로픽 API 키를 한 건도 못 잡습니다.** 제가 8가지 형태를 넣어 시험했더니 **7가지가 그냥 통과**했습니다.

이 패턴 수정은 원래 8월 11일에 만들어졌는데, 작업 폴더를 쓰지 않고 메인에 직접 손댄 실수를 되돌리면서 임시 서랍에 넣어뒀습니다. 그 서랍이 목록에 안 뜨는 상태로 하루가 지났고, 오늘 사장님 지시로 정식 절차를 태워 되살립니다.

**사장님이 결정하실 것은 하나입니다** — 다 만들어 검증까지 끝낸 뒤 올릴 PR을 머지할지 여부입니다. 그 전까지 저장소는 아무것도 안 바뀝니다.

### 판단 근거

**왜 지금 급한가.** Discord 알림 주소 하나면 그걸 아는 누구나 그 채널에 글을 쓸 수 있습니다. 앤트로픽 API 키는 곧바로 요금이 나가는 자격증명입니다. 이 저장소는 이미 **알림 주소가 실제로 새어나간 적**이 있고, 그때 기존 검사기가 못 잡았다는 것이 카나리(일부러 심어보는 미끼값)로 확인됐습니다.

**왜 검사기가 못 잡았나.** 기존 검사기는 `PASSWORD`, `TOKEN` 같은 **이름표가 붙은 것**만 찾습니다. 그런데 Discord 알림 주소는 비밀값이 **주소 경로 안에** 들어 있어서 이름표가 없습니다. 앤트로픽 키는 `sk-ant-`로 시작하는데, 기존의 `sk-` 패턴이 **하이픈 뒤로는 글자만** 오길 요구해서 빗나갑니다.

**갈림길 — 어디에 붙일 것인가.** 지금 PR #4가 같은 파일의 같은 자리를 고치고 있습니다. 두 선택지가 있었습니다.

- **택한 길: `main` 기준으로 독립 작업.** 이 PR은 혼자서도 읽고 판단할 수 있고, PR #4의 코덱스 판정 결과가 어떻게 나오든 영향을 안 받습니다.
- **버린 길: PR #4 위에 얹기.** 지금 당장은 부딪힘이 0이지만, **PR #4가 판정에서 바뀌면 이것도 같이 흔들립니다.** 지금 #4는 코덱스 검증 중이라 결과를 모릅니다.
- **대가:** 머지할 때 부딪힘 한 번을 손으로 풉니다. 다만 두 변경이 **파일 끝에 나란히 붙는 형태**라 위아래로 놓기만 하면 끝납니다(실측 확인).

**이 판단이 틀리면 무엇이 깨지나.** 패턴이 지나치게 넓으면 평범한 코드가 막혀 커밋이 안 됩니다. 비밀 검사에는 **예외 등록 경로가 없어서**, 헛경보 한 번이 곧 작업 중단입니다. 그래서 아래 AC에 "막히면 안 되는 것" 5종을 대조군으로 넣었습니다.

---

## ① 현재 상태 (2026-08-12 실행 확인, 추측 0)

| # | 사실 | 증거 |
|---|---|---|
| 1-1 | 유효 패턴 10개 (주석·빈 줄 제외) | `.secret-patterns.default` 정제 후 `wc -l` → 10 |
| 1-2 | Discord 웹훅 URL **MISSED** | 아래 실측 블록 |
| 1-3 | `discordapp.com` 변종 **MISSED** | 〃 |
| 1-4 | Slack 웹훅 URL **MISSED** | 〃 |
| 1-5 | Anthropic `sk-ant-…` **MISSED** — 기존 `sk-[A-Za-z0-9]{20,}`(`.secret-patterns.default:17`)이 `sk-` 직후 20자 이상 **영숫자만** 요구하는데 `sk-ant-`는 4번째가 하이픈이라 빗나간다 | 〃 |
| 1-6 | `WEBHOOK_URL=` (.env 형태) **MISSED** | 〃 |
| 1-7 | `CREDENTIAL=` **MISSED** / `PRIVATE_KEY=` 한 줄 형태 **MISSED** (블록 형태 `-----BEGIN … PRIVATE KEY`는 `:22`가 이미 잡는다) | 〃 |
| 1-8 | **`BOT_TOKEN=` 은 이미 CAUGHT** — `.secret-patterns.default:11`의 `(…\|TOKEN\|…)` 가 이미 덮는다. 서랍 패치가 `BOT_TOKEN`을 다시 넣은 것은 **중복**이다 | 〃 |
| 1-9 | 서랍 패치는 현재 `main`에 **깨끗이 붙는다** | `git apply --check` 무경고 |
| 1-10 | 서랍 패치와 PR #4는 `.secret-patterns.default` **파일 끝에서 1건 충돌**(둘 다 append) | `git merge-tree` 충돌마커 1개 |
| 1-11 | 서랍 실체: `refs/stash` → `149f6c5` (packed-refs 에 존재). `git stash list`가 빈 것은 **reflog 파일이 0바이트**이기 때문 | `.git/logs/refs/stash` 0바이트 |
| 1-12 | 검사기는 대소문자를 무시한다 | `verify.sh:63,72` — `grep -qEif` / `grep -lEif` |

```
$ (main 패턴 10개로 8종 시험 — 2026-08-12)
MISSED : Discord 웹훅 URL
MISSED : Discordapp 변종
MISSED : Slack 웹훅 URL
MISSED : Anthropic API 키
MISSED : WEBHOOK_URL= (.env)
CAUGHT : BOT_TOKEN= (.env)
MISSED : CREDENTIAL= (.env)
MISSED : PRIVATE_KEY= (.env 한줄)
--- 대조군(잡히면 안 되는 것) ---
MISSED : 일반 Discord 채널 URL
MISSED : 코드 대입
MISSED : 환경변수 참조
```
→ **뭘 했나:** 지금 저장소의 패턴 10개만으로 8가지 비밀 형태와 3가지 평범한 코드를 검사했습니다.
→ **결과:** 8개 중 **7개가 그냥 통과**했습니다(MISSED = 못 잡음). 대조군 3개는 정상적으로 안 걸렸습니다.
→ **의미:** 나쁜 소식입니다. 다만 `BOT_TOKEN`은 이미 잡히므로, 서랍 패치의 그 부분은 새로 얻는 게 없습니다.

## ② 근본 원인

기존 패턴이 **"비밀은 이름표가 붙은 값이다"**라는 전제 위에 서 있다. 세 종류가 그 전제를 벗어난다:

1. **경로에 실린 비밀** — Discord/Slack 웹훅은 URL 경로 자체가 자격증명이라 `키=값` 형태가 아니다.
2. **하이픈이 든 키 형식** — `sk-ant-`는 `sk-[A-Za-z0-9]{20,}`의 문자 클래스를 만족하지 못한다.
3. **키워드 목록의 누락** — `WEBHOOK`·`CREDENTIAL`·`PRIVATE_KEY`가 `.env` 대입문 키워드 목록에 없다.

## ③ 인수 기준 (AC-S1) — EARS

**AC-S1**
> *If 추적 파일에 Discord/Slack 웹훅 URL, `sk-ant-` 형식 벤더 키, 또는 `WEBHOOK|CREDENTIAL|BOT_TOKEN|PRIVATE_KEY` 계열 `.env` 대입문이 있으면, then 비밀 스캔이 실패(exit 1)해야 한다. 동시에 평범한 코드·문서·환경변수 참조는 막히지 않아야 한다.*

- **검증 명령**: `bash scripts/acceptance-secret-webhook-vendor.sh`
- **기대 출력**: `PASS × 17` / `CHECKED: 17` / `exit 0`
  - 탐지 8건(신규 7 + 회귀방지 1) · 오탐 대조군 5건 · 스캐너 종단 3건 · 무오염 1건
- **counter-AC (가짜 완료의 모습)**
  1. 시험 문자열을 패턴에서 그대로 베껴 와 자기충족으로 통과하면 가짜(tautology).
  2. 정규식만 맞추고 `verify.sh`를 실제로 태우지 않으면 가짜 — 판정기가 두 벌이 된다.
  3. 대조군 없이 탐지만 늘려 평범한 코드가 막히면 가짜. 헛경보는 훅 우회 습관을 만든다.
  4. `CHECKED: 0`이거나 하한 없이 통과하면 가짜(P20).
  5. 검사 스크립트가 저장소를 오염시킨 뒤 되돌려 통과하면 가짜 — 시작/종료 상태 대조로 잡는다.
  6. **패턴을 넣고도 `verify.sh`가 그 패턴 파일을 안 읽는 경로가 남아 있으면 가짜**(고아 패턴).

## ④ Harness 게이트 진행 계획

| 게이트 | 상태 | 내용 |
|---|---|---|
| 0 | ✅ | `bash scripts/session-status.sh` → `RED: 0/4`. 과거 회수(C) 수행 — 메모리 6개 파일 확인, `project_verify_unification_status.md`에 이 서랍 건이 기록돼 있음 |
| 1 | ✅ | 이 문서 (AC 1개 + 계약 스펙 ⑩) |
| 2 | 진행 | `worktrees/secret-webhook-vendor/`에서 RED 커밋 — 신규 7종이 **올바른 이유로**(패턴 부재로) 빨개지는지 확인 |
| 3 | — | 서랍 패치 적용 = 최소 GREEN |
| 3.5 | — | 배선 증명: `verify.sh` → `.secret-patterns.default` → `hooks/pre-commit`·`hooks/pre-push`·CI 경로 추적 |
| 4 | — | `bash scripts/acceptance-secret-webhook-vendor.sh` + `bash verify.sh` 실행 출력 그대로 첨부 |
| 5 | — | `git push -u origin task/secret-webhook-vendor` → `gh pr create` → **사장님 머지 결정** |
| 6 | — | merge 후 워크트리 제거 |

## ⑤ codex 적대검증 항목 (V1에서 정조준시킬 것)

1. tautology 여부 — 시험 문자열이 패턴을 거울처럼 베낀 것 아닌가.
2. **새 패턴이 뚫리는 변형을 3개 이상 찾아라** — 대소문자 혼용, 쿼리스트링, URL 인코딩, 줄바꿈 삽입 등.
3. 오탐 — 실제 오픈소스 코드에서 새 패턴이 평범한 줄을 막는 사례를 찾아라.
4. 종단 검사가 `verify.sh`를 실제로 태우는가, 규칙 복사 아닌가.
5. `BOT_TOKEN` 중복을 남긴 판단이 옳은가(방어 심도 vs 죽은 패턴).
6. 무오염 검사가 실제 오염을 잡는가.
7. PR #4와의 충돌 해소안이 어느 패턴도 잃지 않는가.

## ⑥ SOT 체크리스트

- `docs/sot/verification-commands.md` — **수정함(드리프트 차단)**. 처음에는 "수정 불필요"로 적었으나 배선 증명(게이트 3.5)에서 뒤집혔다: **로컬 `pre-push`는 글로브라 새 스크립트를 자동 수집하지만 CI는 고정 목록**이라 한 줄도 안 돈다(`.github/workflows/verify.yml`). 그대로 두면 이 검사가 "로컬에만 있는 검사"가 되어 P15③에 걸린다. `verify.yml`에 스텝을 등록했고, 그 결과 이 SOT 문서의 "CI가 실제로 돌리는 것" 목록이 낡았으므로 같은 PR에서 갱신했다. 다음 사람이 같은 함정에 빠지지 않도록 **"새 인수 스크립트는 양쪽에 등록"** 규칙 한 줄을 그 문서에 추가했다.
- `docs/sot/hook-contracts.md` — 훅 계약. **수정 불필요**(훅 로직 변경 0, 패턴 데이터만 추가)
- `docs/sot/coding-principles.md` — P13(검사 약화 금지)·P20(공허 통과 금지)·P22(패턴은 데이터) 준수. **수정 불필요**
- `docs/sot/git-workflow.md` — 작업 1개 = 워크트리 1개 = AC 1개 준수
- **결론: SOT 1건을 같은 PR에서 함께 고친다.** 패턴 데이터가 늘어나는 것 자체는 SOT를 안 바꾸지만, **CI 실행 목록을 바꾼 것**이 SOT 기술 내용을 바꾼다.

## ⑦ 비범위

- PR #4(세션 계열 자격증명)·PR #5(대용량·PII 경로) — 별도 트랙, 건드리지 않는다
- humansearch 계획서(PR #3)와 코덱스가 작업 중인 `task/humansearch-clean-room-plan` — 건드리지 않는다
- `.secret-patterns`(gitignore된 로컬 실값 파일) — 수정하지 않는다
- 서랍(`refs/stash`) 자체의 정리 — 이 PR 머지 후 별도 처리
- `.git/logs/refs/stash`가 0바이트가 된 원인 규명 — `git gc` 계열 추정이나 미확인, 사장님 확인 없이 손대지 않는다

## ⑧ 롤백 절차

1. `git revert <merge sha>` — 패턴 파일과 인수 스크립트가 함께 되돌아간다.
2. 되돌린 뒤 `bash verify.sh`로 스캔이 정상 동작하는지 확인(패턴 0개가 되면 `verify.sh`는 exit 2로 멈추므로 조용한 실패는 없다).
3. **되돌려도 멈추는 제품 기능이 없다** — 이 저장소에는 제품 코드가 0줄이고, 이 변경은 검사 장치에만 닿는다.

## ⑨ 영향 반경

| 반경 | 내용 |
|---|---|
| **커밋·push 차단** | 패턴이 넓으면 평범한 커밋이 막힌다. 비밀 스캔에는 억제 경로가 없어 **오탐 = 즉시 작업 중단**. 그래서 대조군 5종을 AC에 넣었다 |
| **CI** | `.github/workflows/verify.yml`이 push·PR마다 `verify.sh`를 돌린다. 오탐이면 CI도 빨개진다 |
| **다른 워크트리 5개** | 같은 패턴 파일을 쓰므로 전부 영향받는다. 특히 코덱스가 작업 중인 `humansearch-clean-room-plan`이 이 패턴에 걸릴 수 있다 |
| **데이터 안전 AC** | 이 변경 자체가 데이터 안전 장치다. 추가 AC 대신 counter-AC 5·6번이 그 역할을 한다 |

## ⑩ 계약 스펙

```
scripts/acceptance-secret-webhook-vendor.sh
  입력  : 없음 (저장소 루트에서 실행. .secret-patterns.default 를 읽는다)
  환경  : SECRET_PATTERNS_FILE 은 종단 검사에서 빈 값으로 고정한다(상속 차단)
  출력  : stdout 에 항목마다 PASS:/FAIL:/NOT_RUN: 전부. 마지막 줄 `CHECKED: <n>`
  종료  : 0 = PASS | 1 = FAIL | 2 = NOT_RUN(패턴 파일 부재·빈 파일·유효 패턴 0개·mktemp 실패)
  불변식: n == 0 이면 통과가 아니라 FAIL (P20)
          시작/종료 `git status --porcelain` 이 다르면 판정 무효 → FAIL
```

```
.secret-patterns.default  (추가되는 패턴 — ERE, 한 줄 1개)
  discord(app)?\.com/api/webhooks/[0-9]{15,}/[A-Za-z0-9_-]{20,}
  hooks\.slack\.com/services/T[A-Za-z0-9]+/B[A-Za-z0-9]+/[A-Za-z0-9]{20,}
  sk-ant-[A-Za-z0-9_-]{40,}
  ^[[:space:]]*(export[[:space:]]+)?[A-Za-z0-9_]*(WEBHOOK|CREDENTIAL|BOT_TOKEN|PRIVATE_KEY)[A-Za-z0-9_]*=[A-Za-z0-9][^[:space:]'"#$<>{}()]{5,}[[:space:]]*$
  ※ 실제 비밀값은 이 파일에 절대 넣지 않는다 — 여기 있는 것은 '모양'이지 '값'이 아니다
```

---

## 적대 검증 로그

*(V1 codex · V2 Claude 판정이 여기에 원문 그대로 append 된다 — 요약만 남기지 않는다)*

### V1 (codex · 2026-08-12 03:03) — VERDICT PR#6: FAIL, 결함 8건 (D1~D8)

- 원문 561줄은 카나리 유사 문자열이 들어 있어 저장소에 커밋하면 비밀 스캔에 걸린다(§8-1 민감정보 예외).
  보관: `~/Desktop/valuehire-verdicts-2026-08-12/codex-v1-verdict-pr6.md`
  내용 지문(SHA-256): `c9b197ec47fe27d6447802a0f7475263ad953d8fbe98266fcb7e78505aa94610`
- 요지: 높음 3건(D1 유효 주소 미탐 · D2 정상 설정 오탐 · D3 검사 개수 하한 부재),
  중간 4건(D4 무오염 사각지대 · D5 BOT_TOKEN 죽은 중복 · D6 정본 CI 목록 불일치 · D7 RED 뒤 시험 변경),
  낮음 1건(D8 보고 수치 불일치). 반증 실패 목록(= 진짜인 부분): CI 배선 · 핵심 4규칙 · RED 숫자 · M1~M4 · bash 3.2.

### V2 (Claude · 2026-08-12 04:1x) — V1 판정 8건 전부 격리 재현 성공, 과장 없음

격리 클론(`v2-sandbox/pr6`, aeea77d)에서 직접 재현한 결과 (실행: repro.sh):

| 결함 | 재현 결과 | 비고 |
|---|---|---|
| D1 미탐 3종 | 전부 MISSED 재현 | 외부 근거 독립 확인: GovSlack 공식 문서가 slack-gov.com 명시, Discord v10 버전 경로 유효 |
| D2 오탐 6종 | 전부 CAUGHT(오탐) 재현 | — |
| D3 검사 3개 삭제 | CHECKED: 14, exit 0 재현 | 하한 부재 확정 |
| D4 생성-삭제 오염 | "무오염 PASS" 재현 | 사각지대 확정 |
| D5 양방향 삭제 | 어느 쪽을 지워도 17건 통과 재현 | 죽은 중복 확정 |
| D6·D7·D8 | 문서·커밋 대조로 확인 (실행 없이 문서 대조로 낸 것) | D7: RED→GREEN 사이 시험 입력 변경 diff 확인 |

→ 판정: V1 FAIL 은 정당하다. G(구현자)·V1(codex)·V2(Claude) 일치.

### 결함 반영 (codex 구현 0e96bcc·4fb61d0 + Claude 보강 3커밋)

- codex: 머지(5b39816) → 새 RED(0e96bcc: 뚫린 형식 5종·오탐 4종) → GREEN(4fb61d0: 패턴 앵커·v10·GovSlack·인라인 주석·BOT_TOKEN 제거·CHECKED 27 하한·무오염 3축) — D7 절차(새 RED) 준수.
- Claude V2 재검증이 codex 수정본에서 추가로 잡은 것 3건 (전부 반영 완료):
  1. **잔여 오탐 2종** — 글자로 된 짧은 설정값(저장 방식 이름 keychain · 형식 이름 PKCS12)이 여전히 차단됨. 값 하한 12자로 해소 (RED → GREEN 커밋).
  2. **죽은 카나리** — 새 WEBHOOK 카나리 키에 SECRET 이 들어가 기존 규칙이 가림. 신규 규칙을 지워도 초록으로 남는 것을 뮤테이션으로 실증, 중립 이름으로 교체.
  3. **개수 강제 방식** — 하한(-lt)을 정확값(-ne)으로. V1 설계 결정("checked == 기대값")과 일치.
- 잔여 한계(반영 안 함, 문서화만):
  - 일반(3사 밖) 벤더의 웹훅 URL 값 미탐 — codex 가 오탐 트레이드오프로 명시 제외(패턴 파일 주석). 벤더 추가 시 규칙 추가.
  - D4 의 "고쳤다 되돌린 추적 파일"은 3축 감시로도 못 본다 — 권한 격리 실행(V1 권고안)은 채택 안 됨. 후속 AC 후보.
