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
| 접미 | `(_URL\|_URI\|_ENDPOINT\|_VALUE)?` **열거만** | 열거 원칙 = "이 이름이 가리키는 것이 비밀 **자체**인가". `_PROVIDER`·`_FORMAT`·`_TYPE`·`_RETRY_INTERVAL_MS` 는 비밀의 메타데이터라 제외 |
| 값 | 글자 1개 이상 + 총 6자 이상, 문자집합 `[A-Za-z0-9._-]` | `:`·`/` 를 넣지 않아 URL 값은 계속 제외(2026-08-12 D2 결정 유지) |
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
| 숫자만 | `WEBHOOK_RETRY_INTERVAL_MS=300000` | MISSED — 글자 0개 + 열거 밖 접미 |
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
| 허용 접미 목록 범위 | `_URL`·`_URI`·`_ENDPOINT`·`_VALUE` 4개 | AC 가 요구하는 것은 `_URL` 하나. 나머지 3개는 같은 판정 근거("비밀 자체")를 만족하고 값 문자집합·길이 하한이 오탐을 이미 좁힌다. `_SECRET`·`_TOKEN`·`_PASSWORD` 는 **넣지 않는다** — 기존 (1)(2) 규칙이 이미 덮는 죽은 중복이고, 죽은 중복은 서로의 삭제를 가린다(2026-08-12 D5) |
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
2. 허용 접미 열거가 **자의적**이지 않은가 — `_VALUE` 를 넣은 근거가 `_PROVIDER` 를 뺀 근거와 같은 원리인가.
3. old∖new 회귀 검사가 **동어반복**이 아닌가 — 줄을 더하기만 하면 검출력은 구조적으로 줄 수 없으므로, 기준선을 "현재 파일 − 신규 줄"로 잡으면 항상 0이 나온다. 그래서 기준선을 **동결 fixture**로 잡았다(⑤ CA-2 가 여기서 살아난다).
4. `EXPECTED_CHECKS` 를 늘리면서 기존 검사를 조용히 지우지 않았는가.
5. P13 감시 범위 확대가 실제로 **막는 것**이 있는가 — "범위에 넣었다"와 "약화를 탐지한다"는 다르다(⑪ 한계).

## ⑪ 비범위 / 알려진 한계 (여기 적힌 것을 "닫았다"고 쓰지 않는다)

- **이번에 닫는 것은 환경변수 형식(`KEY=value`)의 6~11자 구간뿐이다.** JSON/YAML/JS 인용 형식 · camelCase · `=` 주변 공백 · 다중 라인 · base64 · 하이픈 키는 길이와 무관하게 **전부 계속 놓친다** → `suppressions.yaml:secret-format-gap` (expiry 2026-09-30).
- 열거 밖 접미사 + 6~11자 값은 계속 놓친다(설계상 대가, ④ catch-all).
- P13 §3 범위 확대는 `.check-weakening-patterns` 에 적힌 **리터럴 추가**만 탐지한다. "정규식을 더 느슨하게 고쳤다"·"규칙 줄을 지웠다"는 여전히 미탐이며, 후자는 기존 억제 `p13-deletion-blindspot` 이 이미 기록하고 있다.
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

(후기록 — V1/V2 판정 본문을 그대로 append 한다)
