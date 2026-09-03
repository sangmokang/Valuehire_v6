# 짧은 값(6~11자) 자격증명 탐지를 되살린다 — 삭제 없이 한 줄 추가로

작성: 2026-09-03 · 등급 L3(보안 검사 변경) · 브랜치 `task/secret-short-value-additive` · 워크트리 `worktrees/secret-short-value/`

## ① 상위 목표 (1문장)

`CREDENTIAL=` · `WEBHOOK_URL=` · `PRIVATE_KEY=` 처럼 **이름이 곧 자격증명인 환경변수**에 6~11자짜리 실제 비밀이 들어가도 지금은 커밋·push·CI 어디서도 걸리지 않는데, 기존 12자 규칙의 오탐 내성을 하나도 잃지 않으면서 그 구간만 다시 막는다.

**성공 신호(사업)**: 억제 원장에서 `keyword-env-value-floor-12` 가 사라지고, 그 억제가 만료되어 멈춰 있던 CI 스텝 11개(16~26번)가 다시 판정을 낸다. 즉 "기능이 들어갔다"가 아니라 **막혀 있던 검사 라인이 다시 돈다**가 성공 신호다.

## ② 현재 상태 (실행으로 확인한 것만)

| 사실 | 근거 |
|---|---|
| 키워드 대입 규칙의 값 하한이 12자 | `.secret-patterns.default:99` (마지막 줄, `{11,}`) |
| 6~11자 구간이 비어 있음 | 실측 — `.secret-patterns.default` 만으로 `CREDEN`+`TIAL=abc123xy` 를 grep 하면 `MISSED` (2026-09-03, `/usr/bin/grep -qEif`) |
| 그 손실이 억제 원장에 기록돼 있고 **만료됨** | `suppressions.yaml:50-66` — `keyword-env-value-floor-12`, `expiry: 2026-08-26` < 오늘 |
| 만료 억제 때문에 CI 가 15번 스텝에서 죽어 16~26번 11개가 skipped | `.github/workflows/verify.yml:139-159` (억제 만료 스캔) 이 `exit 1` → 이후 스텝 미실행 |
| `.secret-patterns.default` 가 훅의 P13 검사 약화 감시 범위 밖 | `hooks/pre-commit:103-104` — `case` 가 `*.sh\|*.yml\|*.yaml\|hooks/*` 뿐 |
| 비밀 스캐너에 줄 단위 허용 목록이 없음 | `verify.sh:72` — `grep -lEif` 는 **파일명**만 낸다. 예외를 걸 단위가 파일뿐이다 |

## ③ 근본 원인

2026-08-12 재검증에서 오탐 2건(`CREDENTIAL_PROVIDER=keychain`, `PRIVATE_KEY_FORMAT=PKCS12`)이 나왔고, POSIX ERE 에 부정 표현(negative lookahead)이 없다는 이유로 **값 하한을 6→12자로 올려** 오탐을 눌렀다. 즉 문제를 "값의 길이"로 풀었는데, 실제 차이는 값이 아니라 **키 이름의 접미사**에 있었다 — `_PROVIDER`·`_FORMAT` 은 비밀을 담지 않고 그 비밀의 *메타데이터*를 담는다.

부정 표현이 없어도 **긍정 열거**는 가능하다. "비밀 자체를 담는 접미사만 허용"하는 규칙을 12자 규칙과 **나란히 한 줄 더** 두면, 12자 규칙의 넓은 커버리지를 하나도 잃지 않으면서 열거된 이름에 한해 하한을 6자로 내릴 수 있다.

## ④ 계약 (SDD — 입출력 모양 먼저)

```
입력  : 텍스트 한 줄 (추적 파일의 임의의 줄)
출력  : CAUGHT(비밀 패턴 매치) | MISSED(매치 없음)
판정기: verify.sh — .secret-patterns.default 의 모든 줄을 grep -Eif 로 OR 결합
불변식: 규칙 집합은 단조 증가만 한다. 이번 변경은 줄 1개 추가이며
        기존 줄의 수정·삭제·교체가 0건이다 (git diff 로 증명한다)
```

신규 줄(허용-접미 열거형):

| 요소 | 값 | 왜 |
|---|---|---|
| 키워드 | `WEBHOOK` \| `CREDENTIAL` \| `PRIVATE_KEY` | 기존 12자 줄과 동일 — 범위를 넓히지 않는다 |
| 접두 | `[A-Za-z0-9_]*` 자유 | `SERVICE_` 같은 네임스페이스는 의미를 바꾸지 않는다 |
| 접미 | `(_URL)?` **열거만** | 열거 원칙 = "이 이름이 가리키는 것이 비밀 **자체**인가". `_PROVIDER`·`_FORMAT`·`_TYPE`·`_RETRY_INTERVAL_MS` 는 비밀의 메타데이터라 제외. **2026-09-03 적대검증 후 확정본** — 초판은 `_URI`·`_ENDPOINT`·`_VALUE` 도 넣었으나 인수 기준 밖인데 오탐 표면만 넓혀 전부 뺐다(V1 F2 · V2 ②) |
| 값 | **영숫자만** 총 6자 이상 + **숫자 1개 이상**, 문자집합 `[A-Za-z0-9]` | `:`·`/` 가 없어 URL 값은 계속 제외(2026-08-12 D2 결정 유지). 숫자 요구는 단어형 센티널 오탐(V1 F2), 영숫자 한정은 IP·날짜·버전·서비스명 오탐(V2 ②)을 막는다 — 둘 다 실측 반례가 인수 검사에 박혀 있다 |
| 앵커 | 줄 전체 `^…$`, 끝 인라인 주석 허용 | 기존 12자 줄과 동일 |

**catch-all**: 열거 밖 접미사는 이 규칙이 **판정하지 않는다**. 그 입력은 기존 12자 규칙으로 떨어지며, 12자 미만이면 놓친다 — 이것이 이번 변경이 남기는 알려진 대가다(⑧ 비범위).

## ⑤ 인수 기준 — AC-SECRET-SHORT-1 (딱 하나)

**EARS**: When 격리된 단일 파일에 아래 6줄 중 하나만 담아 `verify.sh` 전체 스캐너(`VERIFY_SCAN_SOURCE=index`)에 넣으면, the system shall 각 줄에 대해 아래 종료값을 낸다. And 2026-09-03 이전 규칙 집합이 CAUGHT 하던 표본 중 변경 후 MISSED 가 되는 것은 **0개**여야 한다.

| # | 입력 한 줄 | 기대 | 판별력 |
|---|---|---|---|
| 1 | `CREDENTIAL=abc123xy` | CAUGHT (exit 1) | ✅ 신규 줄만 잡는다 |
| 2 | `WEBHOOK_URL=abc123xy` | CAUGHT (exit 1) | ✅ 신규 줄만 잡는다 |
| 3 | `PRIVATE_KEY=abc123xy` | CAUGHT (exit 1) | ✅ 신규 줄만 잡는다 |
| 4 | `CREDENTIAL_TOKEN=abc123xy` | CAUGHT (exit 1) | ❌ 기존 `TOKEN` 규칙이 이미 덮는다 — **검출력 증거로 세지 않는다** (회귀 앵커 전용) |
| 5 | `CREDENTIAL_PROVIDER=keychain` | MISSED (exit 0) | ✅ 열거 밖 접미사 |
| 6 | `PRIVATE_KEY_FORMAT=PKCS12` | MISSED (exit 0) | ✅ 열거 밖 접미사 |

**검증 명령**: `bash scripts/verify/run-acceptance.sh scripts/acceptance-secret-webhook-vendor.sh`

**counter-AC (이게 안 깨지면 위 초록은 가짜다)**
- CA-1 신규 줄을 삭제하면 #1·#2·#3 이 **RED** 여야 한다. (#4 는 RED 가 되지 않는다 — 그게 정상이며 그래서 증거가 아니다)
- CA-2 기존 12자 줄을 신규 줄로 **교체**하면 장문·열거 밖 접미사(`CREDENTIAL_PROVIDER=<12자 이상>`)가 MISSED 로 바뀌어 **RED** 여야 한다.
- CA-3 모든 MISSED 판정 앞에 대조군 `PASSWORD=abc123xy` → CAUGHT 가 먼저 통과해야 한다. 대조군 없는 MISSED 는 "패턴이 죽었다"와 구별되지 않는다.

## ⑥ 결정성 규율 — 입력 영역 표 (SOT §1-11 ①)

명시 입력: 검사 대상 한 줄. 암묵 입력: `.secret-patterns.default` 내용 · `grep -i` 여부 · 로케일 · `git ls-files` 목록.

| 축 | 입력 예 | 처리 |
|---|---|---|
| 정상 | 열거 접미 + 6자 이상 불투명 값 | **CAUGHT** |
| 정상 | 열거 접미 + 12자 이상 값 | CAUGHT (신규·기존 둘 다) |
| 경계 | 값 5자 (`abc12`) | MISSED — 하한 미만. 의도된 경계 |
| 경계 | 값 6자 (`PKCS12` 모양) + **열거 밖** 접미 | MISSED — 이름으로 배제 |
| 빈값 | `CREDENTIAL=` | MISSED — 값이 없다 |
| 숫자만 | `WEBHOOK_RETRY_INTERVAL_MS=300000` | MISSED — **열거 밖 접미**. (초판은 사유를 "글자 0개"라 적었는데, 확정 규칙은 글자가 아니라 숫자를 요구하므로 사유가 낡았다. 판정은 그대로 MISSED) |
| 형식위반 | `WEBHOOK_URL=https://example.com/x` | MISSED — 값 문자집합에 `:`·`/` 없음(D2 결정 유지) |
| 형식위반 | `WEBHOOK_URL=${DISCORD_WEBHOOK}` | MISSED — `$`·`{`·`}` 없음 |
| 대소문자 | `credential=abc123xy` | CAUGHT — `verify.sh` 가 `grep -i` |
| 인라인 주석 | `CREDENTIAL=abc123xy # placeholder` | CAUGHT |
| 형식 밖 | JSON/YAML 인용형 · camelCase · `=` 주변 공백 · 다중 라인 · base64 · 하이픈 키 | **MISSED — 명시적 미처리**. 이번 범위 밖이며 `suppressions.yaml` 의 `secret-format-gap` 에 기록한다 |
| 그 외 전부 | — | **명시적 미판정** → 기존 규칙으로 떨어진다. 이 줄이 단독으로 무언가를 "정상화"하거나 조용히 통과시키는 경로는 없다 |

## ⑦ 결정 목록 (오너 확정 필요했던 것)

| 결정 | 선택 | 근거 |
|---|---|---|
| 12자 줄을 고칠까, 줄을 더할까 | **더한다** | 원명령 명시("삭제도 교체도 하지 않고"). 단조 증가는 회귀 위험이 0 |
| 허용 접미 목록 범위 | **`_URL` 1개** (확정본) | 인수 기준이 요구하는 것은 `_URL` 하나뿐이다. 초판은 같은 슬롯이라는 이유로 `_URI`·`_ENDPOINT`·`_VALUE` 를 더했으나, V1·V2 가 그 셋에서만 오탐을 뽑아냈고 검출 이득은 인수 기준에 근거가 없었다. `_SECRET`·`_TOKEN`·`_PASSWORD` 는 처음부터 제외 — 기존 (1)(2) 규칙이 덮는 죽은 중복이고 죽은 중복은 서로의 삭제를 가린다(2026-08-12 D5) |
| 억제 항목 제거 시점 | AC GREEN 이후 | 원명령 명시. 억제를 먼저 지우면 구멍이 열린 채로 CI 만 초록이 된다 |

## ⑧ 게이트 계획 (WU 분해 · R1/R5 — 앞 단위가 닫히기 전 다음 착수 금지)

| WU | 인수 기준 1개 | 검증 명령 |
|---|---|---|
| WU1 (RED) | 6벡터 + old∖new 회귀 검사가 인수 스크립트에 있고, 짧은 값 누락 때문에 실패한다 | `bash scripts/verify/run-acceptance.sh scripts/acceptance-secret-webhook-vendor.sh` → exit 1 |
| WU2 (GREEN) | 신규 줄 1개 추가로 같은 명령이 exit 0 | 같은 명령 + `bash verify.sh` |
| WU3 | `hooks/pre-commit` P13 §3 감시 대상에 `.secret-patterns.default` 포함, 차단/통과 한 쌍 시연 | `bash scripts/verify/run-acceptance.sh scripts/acceptance-0-7.sh` |
| WU4 | 억제 원장에서 `keyword-env-value-floor-12` 제거 + `secret-format-gap` 추가, 만료 스캔 통과 | 워크플로 15번 스텝 로직 재실행 |
| WU5 | AUDIT 뮤테이션 (a)(b) 가 저장소 밖 사본에서 RED, `OLD_CAUGHT_AND_NEW_MISSED_COUNT=0` | 저장소 밖 임시 사본 |

## ⑨ 예외 케이스 표 (R1 ③ — 표에 없는 상황은 임의 판단 금지, 중단+표 갱신)

| 상황 | 처리 |
|---|---|
| 신규 줄이 추적 파일에서 오탐을 낸다 | **명시적 중단** — 접미 열거를 줄이고 goal 을 고친 뒤 재개 |
| `grep` 이 `ugrep` 등으로 가려져 있다 | 자동 처리 — `/usr/bin/grep` 절대경로 + 자기검사 + rc 3갈래 (2026-08-25 회수) |
| bash 3.2 에서 `${VAR^^}` 류가 죽는다 | 자동 처리 — `tr` 로만 변환 (스크립트 주석 61-64행 기존 규칙) |
| 억제 제거 후 16~26번 스텝 중 새로 빨개지는 것이 있다 | **명시적 중단 + 그것부터 보고** (원명령 C) |
| 가짜 값을 저장소 안에 만들어야 할 것 같다 | **금지** — 저장소 밖 `mktemp` 에서만, 값은 AC 표본 이상 출력하지 않는다 |
| 그 외 전부 | **명시적 중단** + 이 표 갱신안 제시 |

## ⑩ 적대검증 정조준 (V1/V2 가 여기를 때려야 한다)

1. 신규 줄이 **판별력 0**은 아닌가 — #1~#3 이 기존 규칙에도 걸리고 있지는 않은가(#4 가 그 사례다).
2. 허용 접미 열거가 **자의적**이지 않은가 — `_VALUE` 를 넣은 근거가 `_PROVIDER` 를 뺀 근거와 같은 원리인가. (→ 자의적이었다. V1·V2 가 뚫었고 확정본은 `_URL` 하나만 남겼다)
3. old∖new 회귀 검사가 **동어반복**이 아닌가 — 줄을 더하기만 하면 검출력은 구조적으로 줄 수 없으므로, 기준선을 "현재 파일 − 신규 줄"로 잡으면 항상 0이 나온다. 그래서 기준선을 **동결 fixture**로 잡았다(⑤ CA-2 가 여기서 살아난다).
4. `EXPECTED_CHECKS` 를 늘리면서 기존 검사를 조용히 지우지 않았는가.
5. P13 감시 범위 확대가 실제로 **막는 것**이 있는가 — "범위에 넣었다"와 "약화를 탐지한다"는 다르다(⑪ 한계).

## ⑪ 비범위 / 알려진 한계 (여기 적힌 것을 "닫았다"고 쓰지 않는다)

- **이번에 닫는 것은 환경변수 형식(`KEY=value`)의 6~11자 구간뿐이다.** JSON/YAML/JS 인용 형식 · camelCase · `=` 주변 공백 · 다중 라인 · base64 · 하이픈 키는 길이와 무관하게 **전부 계속 놓친다** → `suppressions.yaml:secret-format-gap` (expiry 2026-09-30).
- 열거 밖 접미사 + 6~11자 값은 계속 놓친다(설계상 대가, ④ catch-all).
- **숫자가 없는 영문자만의 6~11자 값**, 그리고 **`.`·`-`·`_` 가 섞인 6~11자 값**도 놓친다 (2026-09-03 V1 F2 · V2 ② 대응의 대가). 센티널 오탐 8종을 막으려 숫자를 요구했고, 그러자 IP·날짜·버전·서비스명 오탐 계열이 들어와 값 문자집합을 영숫자로 좁혔다.
- **남는 오탐**: 영숫자만으로 된 짧은 설정 낱말(`ed25519`·`SHA256` 같은 알고리즘·형식 이름)과 순수 숫자 값은 실제 비밀과 값 모양이 같아 정규식으로 못 가른다. 추적 파일 전수·히스토리 blob 전량에서 발생 0건이라 열어 뒀고 억제 원장에 적었다. **별개로, `WEBHOOK_ENDPOINT=api-v2.example.com` 같은 12자 이상 호스트명은 origin/main 의 12자 규칙이 이미 잡는 기존 오탐이다** — 이 PR 이 만든 것이 아니며 이 PR 이 고치지도 않는다.
- **`- KEY=value` (docker-compose `environment:` 시퀀스 표기)는 길이와 무관하게 전부 미탐이다** (2026-09-03 V2 ④). 신규 줄·기존 12자 줄·기존 env 줄 셋 다 접두를 `[A-Za-z0-9_]*` 로 잡아 줄 앞 `- ` 를 흡수하지 못한다. `PASSWORD` 같은 최강 키워드까지 샌다. **PR 이전부터 있던 구멍이라 회귀는 아니지만, "6~11자를 되살린다"는 프레이밍이 가리는 지점이다 — 형식 축은 모든 길이에서 새는데 이번 작업은 길이 축만 좁혔다.**
- **`verify.sh` 의 index 모드와 worktree 모드가 추적된 심볼릭 링크에서 판정이 갈린다** (2026-09-03 V2 ③). worktree 모드는 링크를 따라가 저장소 밖 내용을 스캔하고, index 모드는 blob(= 대상 경로 문자열)만 본다. 비밀이 커밋되는 경로는 아니지만 pre-commit 은 통과시키고 CI 는 빨개지는 **로컬 재현 불가 CI 적신호**가 된다. `verify.sh` 소관이라 이 PR 범위 밖이며, V1 도 나도 두 모드 차이를 시험하지 않았다.
- P13 §3 범위 확대는 `.check-weakening-patterns` 에 적힌 **리터럴 추가**만 탐지한다. "정규식을 더 느슨하게 고쳤다"·"규칙 줄을 지웠다"는 여전히 미탐이며, 후자는 기존 억제 `p13-deletion-blindspot` 이 이미 기록하고 있다. 그 층의 실제 방어는 P13 이 아니라 **해시로 못박은 동결 기준선 + 24건 회귀 코퍼스**다(2026-09-03 V1 F4).
- `acceptance-0-7.sh` 의 `demo()` 사유 대조는 **출력 문자열 위조에 무력**하다 — 훅 본문을 고쳐 검사를 지우면서 기대 문구만 찍으면 통과한다(2026-09-03 V1 F5). 문자열 위조 차단은 `scripts/verify/run-acceptance.sh` 계약이 자기 소관이 아니라고 명시한 영역이며, 이 PR 은 그 층을 닫지 않는다.
- 3사(Discord/Slack/Anthropic) 밖 벤더 웹훅 URL 미탐(2026-08-12 D2 결정) 유지.

## ⑫ L3 추가 항목

**영향 반경**: `.secret-patterns.default`(스캔 규칙) → `verify.sh`(로컬·CI) · `hooks/pre-commit`(커밋) · `hooks/pre-push`(push) · `.github/workflows/verify.yml` 25개 스텝 중 비밀 관련 4개 · 모든 브랜치의 CI. 규칙이 과하면 **모든 커밋이 멈춘다**(비밀 스캔에는 줄 단위 억제 경로가 없다 — `verify.sh:72`).

**롤백 절차**: 이 PR 은 (a) 패턴 1줄 추가 (b) 훅 case 1줄 (c) 인수 스크립트 (d) 억제 원장 뿐이다. 되돌리기는 `git revert <merge SHA>` 한 번이며 데이터 마이그레이션·상태 변경이 없다. 긴급 시 (a) 한 줄만 지워도 2026-09-03 이전 동작으로 정확히 복귀한다(단조 증가의 대가 없는 이점).

**배포 후 관측 항목** (무엇을 보면 실패를 아는가)
1. 병합 후 첫 3개 브랜치의 CI 에서 "비밀 스캔 (verify.sh)" 스텝이 초록인가 — 빨개지면 오탐이 실제로 났다는 뜻이고, 그 파일명이 로그에 그대로 찍힌다.
2. `hooks/pre-commit` 이 정상 커밋을 막기 시작하는가 — 로컬에서 `BLOCKED: 비밀 스캔 실패` 가 정상 작업 중 1회라도 나오면 즉시 롤백 판단.
3. CI 16~26번 스텝이 skipped 가 아니라 실제 판정을 내는가(억제 제거의 성공 신호).

## ⑬ 읽은 SOT · 회수

- `docs/sot/INDEX.md` · `coding-principles.md` · `hook-contracts.md` · `verification-commands.md` · `git-workflow.md` · `mechanism-registry.yaml`
- ⚠️ `docs/sot/30-strict-mode-contract.md` 와 `docs/sot/31-strict-recurrence-ledger.md` 는 **이 저장소에 존재하지 않는다**(2026-09-03 `ls docs/sot/` 실측). strict 스킬이 "유일 SOT"로 지목하는 파일이 없다 — 과거 회수 "스킬이 참조하는 SOT 실존 확인"(SOT-30 팬텀 참조 사고)의 재발이며, 이번 PR 범위 밖이므로 여기 사실로만 남긴다.
- 과거 회수 인용:
  - "정규식은 눈으로 읽지 말고 돌려라" → ②·⑤ 의 모든 판정을 `/usr/bin/grep` 실행으로 만들었다.
  - "grep 이 ugrep 으로 가려져 있다" → 절대경로 + 자기검사 + rc 3갈래.
  - "검증기가 오염원이 되는 함정" → 가짜 값은 저장소 밖 `mktemp` 에서만.
  - "변조 생존은 커버리지 부족이지 도달 불가가 아니다" → CA-1 에서 #4 를 증거로 세지 않는 이유.
  - "유예를 기본 처리로 삼지 마라" → 억제는 1건 제거·1건 추가이며, 추가분은 "지금 닫으면 CI 가 멈춘다"는 실측 근거를 동반한다.

## 적대 검증 로그

### AUDIT — 뮤테이션 (저장소 밖 격리 사본, 2026-09-03)

사본: 워크트리를 `git clone` 한 3벌. 저장소 안에서는 아무것도 바꾸지 않았다.

**기준(뮤테이션 없음)** — `bash scripts/acceptance-secret-webhook-vendor.sh` exit 0
```
OLD_CAUGHT_AND_NEW_MISSED_COUNT=0
CHECKED: 41
```

**(a) 신규 줄 삭제** — 패턴 파일 114 → 113줄(삭제 1줄, 기존 12자 줄은 잔존 확인). exit 1
```
FAIL: 스캐너 종단 — 짧은 값 — CREDENTIAL (접미 없음) (기대 exit=1, 실제 0)
FAIL: 스캐너 종단 — 짧은 값 — WEBHOOK_URL (열거된 접미) (기대 exit=1, 실제 0)
FAIL: 스캐너 종단 — 짧은 값 — PRIVATE_KEY (접미 없음) (기대 exit=1, 실제 0)
OLD_CAUGHT_AND_NEW_MISSED_COUNT=0
```
판별 표본 3건이 정확히 RED 다. `CREDENTIAL_TOKEN` 은 **RED 가 되지 않았다** — 기존 TOKEN
규칙이 덮기 때문이며, 그래서 §⑤ 에서 검출력 증거로 세지 않았다(변조 생존 ≠ 도달 불가).

**(b) 기존 12자 줄을 신규 줄로 교체** — 12자 줄만 삭제(후보 1건 확인), 신규 줄 잔존. exit 1
```
FAIL: 통과됨(놓침) — WEBHOOK 계열 .env 대입(불투명 토큰)
FAIL: 회귀 — 기준선은 잡던 것을 지금은 놓친다 (코퍼스 1)
FAIL: 회귀 — 기준선은 잡던 것을 지금은 놓친다 (코퍼스 2)
FAIL: 회귀 — 기준선은 잡던 것을 지금은 놓친다 (코퍼스 3)
FAIL: 회귀 — 기준선은 잡던 것을 지금은 놓친다 (코퍼스 4)
OLD_CAUGHT_AND_NEW_MISSED_COUNT=4
```
장문·열거 밖 접미 회귀가 잡힌다(§⑤ CA-2 충족). 동결 fixture 를 기준선으로 잡은 설계가
여기서 값을 한다 — '현재 파일 − 신규 줄'을 기준선으로 삼았다면 이 뮤테이션도 0이 나온다.

**(c) 훅 case 에서 `.secret-patterns.default` 제거** — `hooks/pre-commit` 한 줄 되돌림. exit 1
```
[7/7] 비밀 패턴 파일 약화 → 사유 불일치 ← 차단은 됐지만 겨냥한 게이트가 아니다
      (기대 사유: 검사 약화 패턴 추가 — .secret-patterns.default)
```
사유 대조가 없으면 이 뮤테이션은 **생존한다** — verify.sh 가 대신 막아 종료값이 1이기
때문이다. 실제로 WU3 RED 실행에서 그 장면을 그대로 관측했다.

### 정규식 실측 (저장소 밖, `/usr/bin/grep` 절대경로 · rc 3갈래)

대조군 `PASSWORD=abc123xy` → old=CAUGHT / new=CAUGHT (판정기 생존 확인) 이후:

| 입력 | old | new |
|---|---|---|
| `CREDENTIAL=abc123xy` | MISSED | CAUGHT |
| `WEBHOOK_URL=abc123xy` | MISSED | CAUGHT |
| `PRIVATE_KEY=abc123xy` | MISSED | CAUGHT |
| `CREDENTIAL_TOKEN=abc123xy` | CAUGHT | CAUGHT |
| `CREDENTIAL_PROVIDER=keychain` | MISSED | MISSED |
| `PRIVATE_KEY_FORMAT=PKCS12` | MISSED | MISSED |

신규 줄 **단독**으로 추적 파일 전수 스캔: rc=1(매치 0건), stderr 0바이트, 합성 카나리로
패턴 생존 확인. 즉 "0건"이 "패턴이 죽었다"의 결과가 아님을 같은 실행에서 증명했다.

### Full Strict · 억제 제거로 열린 CI 스텝 재검 (2026-09-03)

**로컬 전량 원장** — 워크트리에서 `verify.sh` + `acceptance-*.sh` 28개:
```
FULL_STRICT: TOTAL=28 RED=0
```
(`acceptance-0-7.sh` 는 원장 제외 대상이라 따로 실행 — exit 0, 위반 7종 차단 + 통과쌍 1건)

착수 시 `RED: 1/28` 이 나왔는데 원인은 이번 변경이 아니라 **새 워크트리에 gitignore 된
로컬 `.secret-patterns` 가 없다**는 환경 문제였다(`acceptance-0-2.sh` 가 그 파일을 요구).
메인 트리에서 심볼릭 링크한 뒤 0/28. 워크트리 생성 직후 로컬 env 파일을 잇는 규칙에
`.secret-patterns` 도 포함된다는 사실을 여기 남긴다.

**CI 16~26번(억제 만료로 그동안 skipped 였던 11개) 재현** — GitHub 체크아웃과 같은 객체
집합을 만들기 위해 `git clone --no-local --single-branch` 로 뜬 사본에서 실행:

| CI # | 스텝 | 결과 |
|---|---|---|
| 16 | 강제 장치 존재 검사 | EXIT=0 |
| 17 | 셸 스크립트 문법 검사 (50개) | EXIT=0 |
| 18 | 패턴 파일 자체 실값 | EXIT=0 |
| 19 | hs-a3 (CHECKED 25) | EXIT=0 |
| 20 | 데이터 노출 스캔 (추적 226 · blob 365) | EXIT=0 |
| 21 | hs-a4 (CHECKED 30) | EXIT=0 |
| 22 | secret-webhook-vendor (CHECKED 41) | EXIT=0 |
| 23 | verified-sha (CHECKED 12) | EXIT=0 |
| 24 | ci-step-integrity (CHECKED 14) | EXIT=0 |
| 25 | semantic-mutations (CHECKED 10) | EXIT=0 |
| 26 | verify-ac-m (CHECKED 31) | EXIT=0 |

**새로 빨개진 것 0건.** 중간에 20번이 로컬에서 한 번 FAIL 로 보였는데
(`docs/decisions/finding-events.jsonl`, blob d8148f1), 추적하니 **origin/main 에서 도달
불가능한 객체**였고 기준 커밋 b724093 에서도 같은 FAIL 이 재현됐다. 로컬 `git clone` 이
객체 저장소를 하드링크로 공유해 다른 워크트리의 폐기 객체까지 끌고 온 허상이며,
전송 프로토콜을 강제한 `--no-local` 사본에서는 위 표대로 PASS 다. 이번 변경과 무관하다.

**히스토리 전량 스캔(CI 8번)** — 신규 패턴을 도달 가능한 모든 blob 에 적용:
`PASS: 히스토리 전량 blob 스캔 0건 (blob 2136개 검사)`, 객체 6184개.

### V1 (외부 적대검증) — codex CLI, read-only 샌드박스, 2026-09-03

실행: `codex exec --sandbox read-only -c model_reasoning_effort=high` (토큰 138,685).
리뷰 전후 HEAD 동일(`9dfb108`), 작업트리·스테이지 diff 0바이트.

**`V1 VERDICT: FAIL` · 병합 전 판정 `REQUEST_CHANGES`** — 발견 6건. 전부 내가 직접
재현했고(대조군 `PASSWORD=abc123xy` → CAUGHT 선통과), 6건 모두 재현됐다.

| # | 심각도 | 발견 | 내 재현 결과 | 대응 |
|---|---|---|---|---|
| F1 | 높음 | 열거 밖 접미(`_DATA`)·base64 값·YAML 인용형·다중 `#` 주석은 계속 미탐 | 4건 전부 MISSED 재현 | **인정.** 원명령이 정한 범위(환경변수 형식 6~11자) 밖이지만, 잔여 손실이 억제 원장에 없던 것은 결함 → F6 과 함께 원장에 이관 |
| F2 | 높음 | `WEBHOOK_VALUE=disabled` 오탐 | 재현 + **더 넓음** — `WEBHOOK_URL=disabled`·`CREDENTIAL=disabled`·`keychain`·`changeme`·`placeholder`·`default` 8종 전부 CAUGHT | **수정.** 값에 숫자 1개 이상 요구 + 접미에서 `_VALUE` 제거. 8종 전부 MISSED 로 바뀜, AC 6벡터는 전부 그대로 |
| F3 | 높음 | 동결 fixture 의 무결성을 실행 중 검증하지 않아 `.` 한 줄로 무력화 가능 | 재현 | **수정.** `BASELINE_SHA256` 상수로 못박고 불일치는 fail-closed. 뮤테이션 재실행: `FAIL: 기준선이 변조됐다` exit 1 |
| F4 | 높음 | P13 범위 확대는 실제 정규식 완화(`{16}`→`{99}`)를 못 막는다 | 재현 (P13 추가줄 검사에서 미탐) | **인정 + 보완.** P13 은 원리적으로 못 막는다(훅 주석·SOT 에 명시). 대신 회귀 코퍼스를 24건으로 넓혀 규칙 계열마다 표본을 박았다. 같은 뮤테이션 재실행: `OLD_CAUGHT_AND_NEW_MISSED_COUNT=1` exit 1 |
| F5 | 중간 | `demo()` 사유 대조는 출력 문자열 위조로 우회 가능 | 코드 분기상 성립 | **인정, 미수정.** 문자열 위조 차단은 `run-acceptance.sh` 계약이 명시적으로 자기 소관이 아니라고 적은 영역이다. 훅 본문을 고쳐 가짜 문구를 찍는 공격에는 사유 대조가 무력하며, 그 층의 독립 방어는 위 fixture 고정 회귀 검사다. §⑪ 에 한계로 적는다 |
| F6 | 중간 | `keyword-env-value-floor-12` 를 지우면서 잔여 6~11자 손실을 원장에 이관하지 않음 | 정당한 지적 | **수정.** `secret-format-gap` 에 잔여 손실 3종(열거 밖 접미 · 숫자 없는 영문자 값 · 반대 방향 순수 숫자 오탐)을 명시 |

**V1 이 깨보고 못 깬 것**(판정서 「반증 시도 내역」에서): AC 6표본 재현 일치 · fixture
payload SHA-256 이 `b724093:.secret-patterns.default` 와 동일 · `EXPECTED_CHECKS` 41 =
호출 38 + 수동 증가 3 으로 산술 정합 · RED 커밋 `ae84381` 이후 기존 검사 호출 삭제 흔적
없음 · 대소문자 무시·정상 따옴표·단일 인라인 주석 조합은 안 깨짐.

**V1 대응 후 재측정** (전부 `/usr/bin/grep` 절대경로, 대조군 선통과)

| 항목 | 결과 |
|---|---|
| AC 6벡터 | 6/6 그대로 (표본·기대값 한 글자도 변경 없음) |
| V1 오탐 8종 | 8/8 MISSED |
| 숫자 위치 경계 1~7번째 · 6자 하한 | 9/9 CAUGHT |
| 5자·순수 영문자 값 | MISSED (의도된 대가) |
| 신규 줄 단독 추적 파일 전수 | rc=1 (오탐 0건), stderr 0바이트, 합성 카나리로 생존 확인 |
| 인수 검사 | `CHECKED: 43`, 43건 전건 PASS |
| 뮤테이션 (a) 신규 줄 삭제 | 판별 표본 3건 RED |
| 뮤테이션 (b) 12자 줄 교체 | `OLD_CAUGHT_AND_NEW_MISSED_COUNT=4` RED |
| 뮤테이션 fixture 무력화 | `FAIL: 기준선이 변조됐다` RED |
| 뮤테이션 AKIA `{16}`→`{99}` | `OLD_CAUGHT_AND_NEW_MISSED_COUNT=1` RED |

작업 중 발견한 자체 결함 2건도 함께 남긴다 — ① 회귀 코퍼스 24건 중 `Set-Cookie` 표본이
실제 헤더 형식이 아니어서 기준선에 안 잡혔다(규칙이 아니라 **표본**이 틀린 경우).
② 자격증명 URL·`Authorization` 카나리를 리터럴로 두어 이 스크립트 자신이 스캔에 걸렸다
(`verify.sh` exit 1 로 즉시 관측). 둘 다 조립·형식 교정으로 닫고 주석에 근거를 남겼다.

### Codeaudit (읽기 전용 요구·구현 대조) — 2026-09-03, 기준 `9dfb108` + 재감사 `3962bf1`

**`CODEAUDIT VERDICT: PASS`** (요구사항 25행 + 재감사 15행 + 병합 전 위험 5건 + 지시 이탈 1건).
확인된 것: RED 커밋 이후 AC 표본·기대값 diff 매칭 0줄 · 12자 줄 누적 삭제 0 · "닫았다" 과장
서술 0건(전수 검색) · 억제 4건 전부 기한 내 · push/PR 0건(`ls-remote` 0).

고쳐서 반영한 지적 2건:
- **억제 본문이 스스로 3번째 오탐이 됐다.** `secret-format-gap` 의 issue 에 문제의 JSON 한
  조각을 리터럴로 옮겨 적어, 형식 구멍을 닫을 때 처리할 오탐이 2건이 아니라 3건이 됐다.
  형태를 끊어 다시 적어 3파일 → 2파일(= origin/main 과 동일)로 되돌렸다.
  "검증기가 오염원이 되는 함정"의 문서판이다.
- **CI 스텝 이름이 "위반 6종"으로 남아 있었다.** SOT·스크립트는 7종+통과쌍으로 갱신됐는데
  `.github/workflows/verify.yml:131` 라벨만 옛 숫자였다.

기록만 하고 고치지 않은 지적: `acceptance-0-7.sh` 샌드박스가 `git clone`(=HEAD 커밋)이라
미커밋 훅 변조를 구조적으로 못 본다(기존 설계, 이번 변경이 만든 결함 아님).

### V2 (리셋 컨텍스트 재검증) — 2026-09-03, 기준 `b575d5d`

**`V2 VERDICT: DISPUTE`.** V1 발견 6건은 전부 재현 또는 "고쳐짐"으로 확인됐고, 숫자 대조
9항목은 전건 일치했다. 그러나 **F4 대응 주장이 실측으로 거짓**임을 잡았고 새 고아 4건을 냈다.

| # | 심각도 | 발견 | 내 재현 | 대응 |
|---|---|---|---|---|
| F4-보완 | ★핵심 | "회귀 코퍼스를 24건으로 넓혀 규칙 계열마다 표본을 박았다"가 거짓 — 기준선 25개 규칙 전수 삭제 스윕에서 **9개가 통째로 지워져도 전 게이트 초록**. 그중 1번은 이 저장소에서 가장 넓은 인용형 자격증명 규칙이다. 코퍼스 표본이 "잡히는가"만 보고 "그 규칙만 잡는가"를 안 봤다(내가 `_TOKEN` 열거 제외 근거로 인용한 2026-08-12 D5 죽은 중복 함정을, 정작 코퍼스에는 적용하지 않았다) | 재현 | **수정.** 주장 대신 **검사**를 뒀다 — ⑥-d 판별력 스윕이 기준선의 각 규칙을 현행에서 하나만 빼고 코퍼스가 반응하는지 본다. 판별 표본 없는 규칙 **집합**을 정확값으로 못박아, 늘어도 줄어도 빨간불이다. 코퍼스 24→32 로 빈자리 8개를 채웠고 남은 것은 `UNCOVERED_BASELINE_RULES=17` 하나 |
| ② | 높음 | V1 F2 대응(숫자 요구)이 **새 오탐 계열**을 만들었다 — `192.168.0.10`(IP) · `2026-09-03`(날짜) · `v2.1.0-rc1`(버전) · `n8n-prod-01`(서비스명) 등. 저장소 밖 클론에 내부 IP 한 줄을 커밋하니 실제로 `verify.sh` exit 1 | 재현 | **수정.** 값 문자집합에서 `.`·`-`·`_` 를 빼 영숫자만 남겼다. 해당 계열이 전부 MISSED 로 바뀌었고 9종을 FP 코퍼스에 편입(8→17). **귀속 정정**: V2 가 든 13건 중 `api-v2.example.com`·`svc-01.internal` 2건은 origin/main 의 12자 규칙이 이미 잡던 **기존 오탐**이다(기준선 단독 측정으로 확인) |
| ② -파생 | 높음 | `_URL`·`_ENDPOINT` 를 "비밀 자체를 담는 이름"이라 열거해 놓고, 정작 그 이름의 가장 전형적인 값(URL)은 D2 결정 때문에 못 잡고 비밀 아닌 호스트명은 잡는다 — 열거 근거가 스스로와 어긋난다 | 인정 | **수정.** 인수 기준이 명시한 `_URL` 하나만 남기고 `_URI`·`_ENDPOINT` 제거 |
| ③ | 중간 | 추적된 심볼릭 링크에서 `verify.sh` index/worktree 모드 판정이 갈린다 | 재현(V2 실측) | **기록만.** `verify.sh` 소관이라 범위 밖. §⑪ 에 적었다 |
| ④ | 중간 | docker-compose `- KEY=value` 시퀀스는 `PASSWORD` 까지 길이 무관 미탐 | 재현(V2 실측) | **기록만.** PR 이전부터 있던 구멍. 억제 원장 ④ + §⑪ |
| ⑤ | 낮음 | F2 수정이 goal §④·§⑥·§⑦ 계약 본문에 역류하지 않아 정본이 둘이 됐다(접미 4개 vs 3개 등) | 재현 | **수정.** 세 곳을 확정 규칙에 맞춰 갱신 |
| ① | — | 6갈래 합집합 등가성 — 64,734건 전수로 공격했으나 **과탐 0·미탐 0으로 안 깨짐** | — | 없음 |

**V2 대응 후 재측정**: AC 6벡터 6/6 유지 · 센티널·설정값 오탐 17종 전건 MISSED ·
회귀 코퍼스 32/32 · `UNCOVERED_BASELINE_RULES=17`(계약값 일치) ·
`OLD_CAUGHT_AND_NEW_MISSED_COUNT=0` · `CHECKED: 44` · `verify.sh` worktree/index 양쪽 exit 0 ·
신규 줄 단독 추적 파일 전수 rc=1(오탐 0). 기존 12자 줄 누적 삭제 **0줄**(44 추가 / 0 삭제).

작업 중 자체 발견 1건: 새 카나리를 설명하는 **주석**에 CDP 엔드포인트 예시를 적었더니 그
주석이 규칙 #16 에 걸려 `verify.sh` 가 이 스크립트를 매치했다. 이번 PR 에서만 같은 유형
(카나리·문서 문구의 자기매칭)이 4번 나왔다 — 리터럴은 말로 바꾸고 값은 조립한다.
