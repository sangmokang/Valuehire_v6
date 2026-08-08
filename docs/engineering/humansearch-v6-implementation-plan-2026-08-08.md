# humansearch v6 구현 계획 (goal) — 타 저장소 의존 0

- **작성일**: 2026-08-08 · **3판**. 개정 이력은 §12.
- **위험 등급**: 이 문서는 **L2**(문서, 소스 변경 0). 계획하는 **각 Phase는 L3**(인증·자격증명·외부 사이트).
- **지시**: 2026-08-08 사장님 — *"다른 폴더 구현 코드를 절대 참조하지 말고 스스로 다시 짜 … 타 레파지토리 의존성 전혀 두지 말고"*
- **상위 스펙(불변)**: `docs/engineering/humansearch-v6-founding-spec-2026-08-07.md` (657줄, `3d7930c`)
- **준수 SOT**: `docs/sot/coding-principles.md` · `verification-commands.md` · `hook-contracts.md` · `git-workflow.md`
- **적대검증**: V1 판정서 `humansearch-plan-v1-verdict-2026-08-08.md`(FAIL, D-1~D-10) · 2판에 대한 품질 리뷰(FAIL, 치명4·중대11) · 보안 리뷰(Critical2·High4) — 반영 결과는 §11

---

## §0. 3판이 바꾼 것 — 전제 하나가 틀렸다

초판과 2판이 **같은 자리에서 두 번 무너졌다.** 뿌리는 설계가 아니라 전제였다:

> ❌ **틀린 전제**: "라이브가 실제로 있었는지를 CI가 판정할 수 있다."

초판은 해시체인으로, 2판은 "커밋된 영수증"으로 그걸 하려다 각각 뚫렸고, 2판은 그 위에 **딜레마**까지 만들었다 — 증거 파일을 커밋하면 후보자 개인정보·세션 쿠키가 저장소에 박히고(P21·보안 Critical), 커밋하지 않으면 CI가 해시를 재계산할 수 없어 인수 스크립트가 영구 실패한다. **제3의 길이 없었다.**

> ✅ **3판의 전제**: "CI는 라이브를 판정할 수 없다. 기계가 할 수 있는 것만 기계에 맡기고, 못 하는 것은 **사람이 판정한다고 명시**한다."

이 전제 교체 하나로 치명 4건이 함께 풀린다(§4). 그리고 **"기계가 못 한다"를 적는 것이 기계가 하는 척하는 것보다 안전하다** — 후자는 초록불이 거짓말을 하고, 전자는 거짓말할 초록불이 없다.

---

## §1. 현재 상태 (2026-08-08 실행 확인, 추측 0)

| # | 사실 | 증거 |
|---|---|---|
| 1-1 | 제품 코드 **0줄**. 추적 파일 46개 전부 문서·훅·bash | `git ls-files \| wc -l` → 46 |
| 1-2 | `Makefile`·`package.json` 없음 | `make -n red-ledger` 실패 |
| 1-3 | RED 원장 = bash 글로브(`acceptance-*.sh` 실패 개수) | `scripts/session-status.sh:44-70` |
| 1-4 | 현재 **RED 1/4** (`acceptance-0-2`가 빨강) — 창립 스펙 §7 게이트 0("RED 0에서 시작")을 **지금은 통과할 수 없다** | 4개 직접 실행 |
| 1-5 | `pre-push`는 글로브 전량 실행, **0이 아닌 종료코드 전부 차단** | `hooks/pre-push:112,166` |
| 1-6 | **CI는 고정 스텝 목록**. acceptance는 `0-6`·`0-7`·`0-5` 셋만. 신규 스크립트는 **CI에서 한 줄도 안 돈다** | `verify.yml:66,79,84` |
| 1-7 | **`acceptance-0-2`의 CI 미등록은 사고가 아니라 문서화된 결정** | `verify.yml:72-76` · `verification-commands.md:14` · `pre-push:104-107` |
| 1-8 | 비밀 스캔이 **세션 계열 자격증명을 하나도 못 잡는다** — `li_at`·`cookie`·`JSESSIONID`·`set-cookie`·`pw`·`session_id`·`Bearer eyJ…` 전부 MISSED (대조군 `password`·`access_token`은 CAUGHT) | `.secret-patterns.default:9,11` · 직접 실측 |
| 1-9 | **파일 크기 차단이 없다.** `hooks/pre-commit`에 크기 검사 0건 | grep 0건 |
| 1-10 | `artifacts/`·`receipts/`·`fixtures/`·`*.db`·`*.sqlite*`·`private-reviews/` 전부 **gitignore 안 됨(TRACKABLE)** | `git check-ignore` 실측 |
| 1-11 | P4(시뮬레이션 탐지)의 파일명 범위가 `tools/live_capture.py`·`src/humansearch/driver.py`를 **안 덮는다** | `pre-commit:152` case 대조 |
| 1-12 | 런타임: `python3` **3.14.1** · `uv` 0.11.3 · `sqlite3` 3.51.1(stdlib) · `/usr/bin/security` | 실행 확인 |
| 1-13 | **CDP 디버그 포트를 LISTEN하는 크롬 0개** | `lsof` → 0 |
| 1-14 | 억제 4건(만료 08-21 / 09-15 ×2 / 09-30). `session-status.sh`는 억제 원장을 **읽지 않는다** | `suppressions.yaml` · `session-status.sh:46-64` |

---

## §2. 근본 원인

- **원인 ①** 신규 인수 스크립트가 **로컬에만 존재**한다(1-5 vs 1-6). P15③("로컬에만 있는 검사는 없는 것으로 친다") 위반이며, 게이트 5의 "CI 초록"이 그 Phase의 인수 기준과 **무관한 초록**이 된다.
- **원인 ②** **라이브 증거는 개인정보다.** 커밋할 수 없고(P21·PII), 커밋하지 않으면 CI가 검사할 수 없다. §0의 전제 교체로만 풀린다.
- **원인 ③** 창립 스펙 §4의 잔여 작업이 타 저장소 의존이었다 → 셀렉터를 **이식하지 않고 라이브 캡처로 재획득**한다(Phase B). 셀렉터는 베끼면 안 되는 값이다 — 스펙 §4-10이 스스로 적었듯 대소문자 불일치를 합성 fixture는 못 잡고 라이브 캡처만 잡았고, 2026-07-31엔 nav DOM 변경으로 후보 20명이 유실됐다.
- **원인 ④** **게이트 0을 지금 통과할 수 없다**(1-4). Phase A가 이것부터 해소해야 한다.

---

## §3. 런타임 — Python 3.14.1 + uv

`ruff` + `mypy --strict` + `pytest` + `Hypothesis`. **게이트 계약은 bash 인수 스크립트**이며 pytest는 그 안의 수단일 뿐이다.

| 축 | 판정 |
|---|---|
| SQLite + WAL + `flock` | **Python 우위** — stdlib, 네이티브 빌드 0(P6) |
| P3 조용한 실패 린트 | **Python 우위** — ruff `E722`/`BLE001`/`TRY`. TS는 `\|\|`·`??`가 관용구라 오탐 폭증 |
| P5 속성 기반 테스트 | **Python 우위** — Hypothesis |
| 5조-5 "개입 후 호출이 타입상 불가능" · 스펙 §2-6 "`close()` 미노출" | **mypy --strict로 충족**. V1이 반증 시도 후 실패로 확인 |

### 3-A. 타입으로 못 막는 것 — 원시 참조를 **클로저에 가둔다**

`d: LiveDriver = raw` 로 좁혀도 `raw.close()`는 타입상 합법이고, 2판이 쓴 `__all__` 미포함·`hasattr(driver,'close')`도 **`driver._raw.close()`를 못 잡는다**(래퍼가 소켓을 속성으로 들고 있어야 동작하므로).

**해법은 속성이 아니라 클로저다.** 팩토리가 소켓을 지역변수로 붙잡고 함수만 반환한다:

```python
def make_driver(ws: _RawSocket) -> LiveDriver:      # _RawSocket 은 이 모듈 밖으로 안 나간다
    def navigate(u: Url) -> None: ws.send(...)      # ws 는 클로저에만 산다
    return LiveDriver(navigate=navigate, screenshot=..., read_marker=...)
# 계약 테스트(런타임): vars(driver) 안에 소켓 타입 객체가 0개 — `driver._raw` 가 존재하지 않는다
```

**재승격 전이 계약**(개입 후 영구 중단 금지와 5조-5를 동시에 만족):
```python
def resume(y: Yielded, proof: LiveAuthProof) -> LiveDriver: ...
# LiveAuthProof 는 라이브 재관찰 함수만 생성한다(모듈 private 생성자)
```

---

## §4. 라이브 증거 설계 — **기계가 못 하는 것을 적는다**

### 4-1. 세 질문을 분리한다

| 질문 | 누가 판정하나 | 어떻게 |
|---|---|---|
| **Q1** 영수증이 형식·불변식을 지키는가 | **CI + 로컬(동일)** | 커밋된 JSON만으로 판정 가능 |
| **Q2** 증거 파일이 실질적인가(0바이트·매직·마커) | **러너가 캡처 직후, 호스트에서** | 실패하면 **영수증을 아예 쓰지 않는다**(write-time fail-closed) |
| **Q3** 라이브가 실제로 있었는가 | **사람(오너)** | 기계는 판정 불가. 머지 승인이 그 게이트다 |

**Q3을 기계에 맡기지 않는 것이 이 판의 핵심 결정이다.** 러너를 실행할 수 있는 주체는 어떤 기계 검사도 통과하는 영수증을 만들 수 있다(초판·2판이 각각 실증당했다). 그러니 **"라이브 1건"의 최종 판정자는 오너**이고, `git-workflow.md:23`의 *"자동 병합 금지 — 오너가 diff를 실제로 읽는다"*가 이미 그 자리를 만들어 뒀다. 기계는 오너의 판정을 **싸게** 만들어 준다(§4-3).

### 4-2. 증거 파일은 git에 들어가지 않는다 — 딜레마 해소

- **git 안(커밋)**: `receipts/<channel>.json`(작다, 해시·개수·마커 **이름**만) · `fixtures/live/**`(축약 캡처, **텍스트 노드 0건**)
- **git 밖(gitignore)**: `artifacts/**`(스크린샷·원문) · `*.db`·`*.sqlite*`(후보자 PII) · `data/`
- **CI는 `artifacts/`를 재계산하지 않는다.** 없는 파일을 검사하라고 요구하지 않으므로 2판의 영구 실패가 사라진다.
- 대신 영수증은 Q2의 **검사 결과**를 필드로 담고, **그것이 러너의 자기신고임을 문서와 필드 이름에 명시**한다(`self_reported: true`). 자기신고를 자기신고라 부르면 아무도 속지 않는다.

### 4-3. 오너 판정을 싸게 만드는 3가지

1. **눈으로 대조 가능한 요약**: 영수증에 `human_summary`(채널·시각·방문 페이지 수·수집 건수·발견한 마커 **이름**)를 넣는다. **값(계정명·후보자 이름)은 넣지 않는다.**
2. **모순 자동 탐지**: 기계가 판정 못 하는 건 "라이브였나"이지 "앞뒤가 맞나"가 아니다. CI가 잡는 것 — 미래 시각 · 시각 역행 · 같은 시각 중복 · 페이지 수 0인데 수집 N건 · 마커 이름이 `contracts/`에 없는 것 · 비밀 키 존재 · 스키마 위반.
3. **1 라이브 = 1 PR**: 영수증 재사용 금지. `code_commit`이 이 브랜치의 조상이 아니면 FAIL(§5-2).

### 4-4. CI에 못 올리는 검사는 **원장에 등록**한다 (F-2 딜레마 해소)

2판의 AC-A1은 *"인수 스크립트 **전량**이 CI 실행 줄에 있어야 한다"*였는데, `acceptance-0-2`는 **CI에 못 올리는 것이 문서화된 결정**이라(1-7) 그대로 두면 push가 영구 차단되고, 예외 목록을 만들면 이 저장소가 이미 한 번 막은 "마커=자기선언 탈출구"가 부활한다.

**해소**: 새 장치를 만들지 않고 **`suppressions.yaml`을 재사용**한다.
- 규칙: *CI 실행 줄에 없는 인수 스크립트는 `suppressions.yaml`에 `check`·`reason`·`owner`·**`expiry`**·`issue`와 함께 있어야 한다. 없으면 차단.*
- **자기선언 탈출구가 아닌 이유**: ① 원장 항목에 **만료가 강제**된다(`pre-commit`·CI가 이미 검사) ② 원장에 없는 미등록 스크립트는 **차단**(실패 방향이 뒤집혀 있다) ③ 원장은 커밋되어 오너가 읽는다.
- `acceptance-0-2`는 **이미 그 원장에 있다** — 새로 만들 것이 없다.

---

## §5. 계약 스펙

### 5-1. 실행 입력
```jsonc
{ "channel":"saramin|jobkorea|linkedin_rps", "position_ref":"str",
  "search_url":"https://…",   // 3사 인재풀 URL 화이트리스트만(불일치=exit 2). 사고유형 [14] 부분 대응
  "target_id":"str",          // 기존 CDP target. 새 탭 금지
  "jd_or_config":{} }
// 누락·빈 값·비-http·화이트리스트 불일치 → ValidationError(exit 2). 기본값 채우기 금지(P3)
```

### 5-2. 영수증 (커밋된다 · 작다 · 비밀·PII 없음)
```jsonc
{ "schema_version":2, "channel":"saramin", "host_id":"sha256(hostname+uuid)",
  "state":"AUTHENTICATED",
  "last_verified_at":"2026-08-08T12:00:00+09:00",   // 시간대 필수·미래 거부·역행 거부
  "code_commit":"<라이브 실행 시점 HEAD>",           // ⚠️ 자기참조 금지(2판 결함): 영수증을 담은 커밋이 아니라 그 부모
  "evidence_check": {                                // Q2 결과. 러너 자기신고임을 이름으로 못박는다
     "self_reported": true, "files": 3, "all_nonempty": true, "magic_ok": true,
     "min_bytes": 48231, "markers_found": ["account","search"] },   // 마커 '이름'만. 값 금지
  "human_summary": { "pages_visited": 21, "profiles_opened": 63, "duration_s": 1840 },
  "prev_receipt_sha256":"<64hex|null>" }
```
**검증기 계약** `validate(receipt, mode)` → `PASS | FAIL(reason[])`:
- `mode="branch"`(PR): 위 전부 + `git merge-base --is-ancestor code_commit HEAD`
- `mode="main"`(squash merge 후 SHA가 바뀌므로): 조상 검사 **제외**, 나머지 전부
- **키 화이트리스트**: 위 11개 필드 외의 키가 하나라도 있으면 FAIL(열거식 denylist 금지 — P17)
- `artifacts/` 재계산은 **하지 않는다**(§4-2)

### 5-3. 셀렉터 · 픽스처
```jsonc
// contracts/<channel>/selectors.json — 셀렉터는 코드가 아니라 데이터다(5조-1)
{ "detail_link": { "candidates":["…"], "status":"hypothesis|live_confirmed",
                   "fixture_ref":"fixtures/live/…json", "confirmed_at":"…", "matched_nodes":25 } }
// hypothesis 가 하나라도 있으면 그 채널 순회 거부. live_confirmed 인데 fixture_ref 부재·매칭 0 → FAIL

// fixtures/live/<channel>/<surface>-<date>.json — 커밋된다. 그래서 PII 를 담으면 안 된다
{ "surface":"list", "captured_at":"…", "url_shape":"https://…",     // query 제거
  "attrs":["data-test-…"],                                          // 속성 이름만
  "nodes":[{"tag":"a","attrs":{"data-test-…":""},"selector_hit":"…"}],  // ⚠️ 텍스트 노드 0건 · outer_html 금지
  "account_control_present": true,                                  // 계정명 '값' 대신 존재 여부
  "source_sha256":"<원본 HTML sha256>", "bytes":0 }                  // 축약본 ≤200KB
```

### 5-4. 인수 스크립트 출력 계약
```
scripts/acceptance-hs-<id>.sh
  exit 0=PASS | 1=FAIL(라이브 증거 없음도 FAIL) | 2=NOT_RUN(전제를 읽을 수 없음)
  stdout: 항목마다 PASS:/FAIL:/NOT_RUN: 전부 출력. 마지막 줄 `CHECKED: n`, n=0 이면 스스로 FAIL(P20)
  pre-push·CI 는 exit 0 만 통과. 특례 없음. CI 에 못 올리면 suppressions.yaml 등록(§4-4)
```

### 5-5. 판정 함수 — **LLM은 숫자를 만들지 않는다** (SOT P14 우선)
```
extract(candidate_text) -> { tenures:[{company,months}], schools:[str], evidence_spans:{d1:[str],…} }
        # LLM 은 여기까지. 사실 추출만. 숫자 판정 없음
score(facts, jd) -> { d1..d8:int, total:int, tier:str, input_sha256:str, fn_version:str }
        # d1..d8 을 포함해 모든 숫자는 순수 함수가 계산한다
eligible(candidate) -> bool     # 유일한 경계 함수
```
> ⚠️ **SOT 드리프트 명시**: 창립 스펙 §6은 *"LLM은 소점수 + 근거만"*이라 d1~d8을 LLM이 만들게 했다. 그런데 `coding-principles.md:29` **P14①**은 *"점수·확률·적합도·평점은 순수 함수의 반환값만 DB에 기록"*을 요구하고, `scores` 테이블의 `d1..d8`은 판정 필드다. **SOT가 상위이므로 P14를 따르고 창립 스펙과 갈라진다.** 이 차이를 여기 적어 드리프트를 숨기지 않는다.

---

## §6. Phase 계획 — **PR = AC 1개** (Phase는 마일스톤일 뿐)

`git-workflow.md:15,20,21`이 *"작업 1개 = 브랜치 1개 = 인수 기준 1개, 수명 24~48시간, PR = 인수 기준 1개"*를 요구한다. 2판은 "1 Phase = 1 PR"이라 적어 Phase 1·2에 AC를 6개씩 넣었다 — **48시간 상한도 P11③(3,000줄 금지)도 지킬 수 없다.** 3판은 **AC 1개 = PR 1개**로 되돌린다(총 PR 약 25개).

**기대 출력 규칙**: 모든 인수 스크립트는 마지막 줄에 `CHECKED: n`을 낸다. **하한이 있는 검사는 `>= 1`을 명시**한다(N=0 공허 통과 차단).

### Phase A — 게이트 확장 (선행 · 6 PR)

| AC | EARS | 검증 명령 | 기대 출력 |
|---|---|---|---|
| **A1** | *When 인수 스크립트가 CI 실행 줄에 없으면, then `suppressions.yaml`에 만료와 함께 등록돼 있어야 하고 없으면 차단해야 한다* | `bash scripts/acceptance-hs-a1.sh` | `PASS: 인수 스크립트 N개 (CI등록 M · 원장등록 K, M+K==N)` · `PASS: 원장 항목 전부 만료 이내` / `CHECKED: 3` |
| **A2** | *When 파이썬 소스가 존재하면, then ruff·mypy 검사 대상 수가 `git ls-files '*.py'` 개수와 **일치**하고 pytest 수집 케이스가 **1건 이상**이어야 한다* | `bash scripts/acceptance-hs-a2.sh` | `PASS: ruff K == ls-files K` · `PASS: mypy K` · `PASS: pytest 수집 T >= 1` / `CHECKED: 3` |
| **A3** | *If 세션 계열 자격증명이 추적 파일에 있으면, then 스캔이 실패해야 한다* | `bash scripts/acceptance-hs-a3.sh` | `PASS: 실형식 4 + 값모양 2 + 키=값 6 전부 탐지` · `PASS: 스캐너 종단 2건(verify.sh 실제 실행)` · `PASS: 오탐 대조군 5종 전부 통과` / `CHECKED: 20` |
| **A4** | *If 1MB를 넘는 파일 또는 DB·아티팩트 경로가(하위 디렉터리 포함) 커밋되려 하면, then `pre-commit`과 CI가 **양쪽 다** 차단해야 한다* | `bash scripts/acceptance-hs-a4.sh` | `PASS: 차단 10종(사유 일치)` · `PASS: 인덱스 측정·rename·앵커 3건` · `PASS: gitignore 5경로` · `PASS: CI 경로 패턴이 훅과 동치` / `CHECKED: 22` |
| **A5** | *When P4 시뮬레이션 검사가 돌면, then 외부 효과 모듈 판별이 **파일명이 아니라 선언된 목록**(`contracts/external-effect-modules.txt`)을 근거로 해야 한다* | `bash scripts/acceptance-hs-a5.sh` | `PASS: tools/live_*.py 전부 커버` · `PASS: 네트워크 0건 모듈 차단 시연` / `CHECKED: 2` |
| **A6** | *When `session-status.sh`가 RED를 세면, then 억제된 RED를 **출력에 명시하며** 분리 계상해야 한다* | `bash scripts/acceptance-hs-a6.sh` | `PASS: RED 0/4 (1건 억제: acceptance-0-2 expiry 2026-08-21)` / `CHECKED: 2` |

- **A3~A5는 보안 리뷰 Critical 2 + Medium 1을 선행으로 당긴 것이다.** 셋 다 소스 0줄로 끝난다.
- **A3의 의도적 구멍(근거를 패턴 파일에 남긴다)**: `pw`/`pwd` 짧은 키와 `SESSION_ID`/`SESSIONID` 키는 **잡지 않는다.** 실측에서 오탐 4종(빌드 경로 `"pwd":"/Users/…"` · 상태 상수 `'PW':'PENDING_WRITE'` · 헤더 이름 설정 · i18n 문구)이 여기서 났고, **비밀 스캔에는 억제 경로가 없어 오탐이 곧 작업 중단**이다. 진짜는 놓치고 더미는 막는 비대칭이 훅 우회 습관을 만든다. 자격증명은 Keychain 단일 출처라 파일에 남을 경로가 정책상 없다(창립 스펙 §3-6). 세션 값은 키 이름이 아니라 **값 모양**으로 잡는다.
- **A4의 의도적 허용**: `*.sql`(마이그레이션은 정상 산출물) · `*.csv`(소형 픽스처와 구분 불가). 크기 검사와 내용 검사에 맡긴다.
- **1MB 문턱의 한계**: 크기로는 **1MB 미만 PII를 못 막는다.** `receipts/`·`fixtures/live/`는 계획상 커밋 대상이라 차단 목록 밖이며, 그 방어선은 A3의 내용 검사와 **AC-B2(픽스처 텍스트 노드 0건)**뿐이다. B2가 붙기 전까지 그 두 경로는 사실상 무방비다 — §10에 한계로 적었다.
- **A6은 게이트 0 통과 조건을 만든다**(1-4·1-14). 조용한 제외 금지 — `session-status.sh:45`의 `EXCLUDED` 명시 선례를 따른다.
- **산출물**: `hooks/pre-commit`(+크기·+P4 목록) · `hooks/pre-push`(+A1) · `verify.yml`(+스텝 5) · `.gitignore` · `.secret-patterns.default` · `contracts/external-effect-modules.txt` · `pyproject.toml`·`uv.lock`·`.python-version` · 인수 스크립트 6개 · **SOT diff 2건**(`verification-commands.md`·`hook-contracts.md`)
- **LOC 예산**: 훅 2개 각 +80줄 이내(현재 pre-commit 164·pre-push 174 → hard 600 여유), 인수 스크립트 각 100줄 이내
- **비범위**: humansearch 도메인 코드 0줄

### Phase B — 라이브 캡처 → 픽스처 → 계약 (선행 · 4 PR)

| AC | EARS | 검증 명령 | 기대 출력 |
|---|---|---|---|
| **B1** | *Where `selectors.json`에 `hypothesis` 항목이 하나라도 있으면, 시스템은 그 채널 순회를 거부해야 한다* | `bash scripts/acceptance-hs-b1.sh` | `PASS: hypothesis 잔존 시 거부` / `CHECKED: 2` |
| **B2** | *When 픽스처를 저장하면, then ≤200KB이고 **텍스트 노드가 0건**이며 원본은 `artifacts/`(git 밖)에 두고 SHA만 기록해야 한다* | `bash scripts/acceptance-hs-b2.sh` | `PASS: 픽스처 텍스트 노드 0건` · `PASS: 전부 <=204800` / `CHECKED: 3` |
| **B3** | *If 추적 파일이 타 저장소 경로 패턴을 포함하면(단 `docs/engineering/` 제외), then CI가 실패해야 한다* | `bash scripts/acceptance-hs-b3.sh` | `PASS: 실행 경로 0건` · `PASS: 패턴 파일에 실행 코드 없음` / `CHECKED: 2` |
| **B4** 🆕 | *When Phase B가 완료되면, then **최소 1개 채널**의 `selectors.json` 전 항목이 `live_confirmed`이고 각 `fixture_ref`가 실존하며 매칭이 **1건 이상**이어야 한다* | `bash scripts/acceptance-hs-b4.sh` | `PASS: live_confirmed 채널 >= 1` · `PASS: 항목 N개 전부 매칭 >= 1 (N >= 1)` / `CHECKED: 2+N` |

- **B4가 2판의 치명 결함을 막는다**: 2판은 셀렉터가 "전부 hypothesis로 시작"하는데 기대 출력이 *"live_confirmed N개 전부 매칭"*이라, **크롬 0회·픽스처 0건으로 Phase B 전체가 초록**이었다(P20 함정 그 자체). 하한 `>= 1`로 닫는다.
- **B는 영수증을 요구하지 않는다.** 영수증 개념은 Phase 1부터다 — 2판은 B의 인수를 "영수증 1건"으로 걸어놓고 그 검증기를 Phase 1 산출물로 뒀다(순환).
- **채널 확장**: B는 **사람인 1채널**만 승격한다. 잡코리아·LinkedIn RPS는 **B-2·B-3(별도 PR)**로 Phase 2 이후 각각 진행한다. 그 전까지 두 채널은 B1에 의해 순회 거부 상태이며, 이는 **의도된 fail-closed**다(창립 스펙 §0의 3사 범위는 B-2·B-3 완료 시 충족).
- **산출물**: `tools/live_capture.py`(read-only: 새 탭 0·입력 0·클릭 0, ≤300줄) · `contracts/saramin/selectors.json` · `.foreign-repo-patterns` · 인수 스크립트 4개
- **B3 자기매칭 해법**: 검사 문자열을 스크립트에 리터럴로 두면 검사기가 자기 매칭한다. 커밋된 외부 파일 `.foreign-repo-patterns`로 분리(선례 `.check-weakening-patterns:2`). **파일명 자기 면제는 금지**(`acceptance-0-6.sh:17`).
- **B3 한계**: 경로 문자열 탐지는 **대리지표**다. 코드를 복붙하고 경로만 지우면 0건이 된다. 실질 방어는 B4의 라이브 승격 강제다.

### Phase 0 — 골격 (4 PR)

| AC | EARS | 기대 출력 |
|---|---|---|
| **0-1** | *If 증거 행이 없는 후보를 `registrations`에 넣으려 하면, then **DB 제약**이 거부해야 한다* | `PASS: 위반 INSERT 4종 전부 거부` / `CHECKED: 4` |
| **0-2** | *When 경력을 계산하면, then **회사 단위 groupby** 후 `job_changes = unique_companies - 1`이어야 한다(승진≠이직)* | `PASS: 속성기반 100케이스 통과` / `CHECKED: 2` |
| **0-3** | *If `profile_url`이 수확 JSON의 `url`과 문자열 불일치하면, then 등록을 중단해야 한다* | `PASS: 손입력·재구성 4종 차단` / `CHECKED: 4` |
| **0-4** | *When 러너가 문턱을 읽으면, then `config/humansearch.json` **한 곳**에서 읽어야 하고 코드 리터럴 재정의는 거부돼야 한다* | `PASS: 리터럴 재정의 grep 0건` · `PASS: 러너가 설정 파일에서 읽음` / `CHECKED: 2` |

- **속성 기반 테스트(P5) 필수 3함수**: `score` · `eligible` · `build_company_tenures`
- **PII 보존·파기(보안 M-6)**: 스키마에 `purge_after` 컬럼 + **단일 함수** `purge_candidate(profile_url)`(DB행 + `artifacts/` + 픽스처 일괄). 디렉터리 0700 / 파일 0600 계약 테스트. AC: *파기 후 DB 0건 AND 디스크 잔존 0건*
- **산출물**: `src/humansearch/{schema.sql,db.py,config.py,scoring.py,gate.py,purge.py}` 각 ≤300줄 · 마이그레이션 forward-only + `schema_version`(P7)

### Phase 1 — 로그인 (6 PR · 창립 스펙 §3)

| AC | EARS | 기대 출력 |
|---|---|---|
| **1-1** | *If 영수증이 `AUTHENTICATED`가 아니거나 1800초 초과이거나 스키마·키 화이트리스트를 위반하면, then 순회를 시작하지 않고 STOP하며 알림을 **1건만** 남겨야 한다* | `PASS: 위조 6종 거부(빈영수증·미래시각·시각역행·키추가·비밀키·조상아님)` / `CHECKED: 8` |
| **1-2** 안전 | *If 보안 챌린지(캡차·2FA·인증번호·checkpoint·authwall)가 탐지되면, then 같은 URL 재네비게이션을 **0회** 해야 한다* | `PASS: challenge 후 navigation 0건` / `CHECKED: 2` |
| **1-3** [4] | *If `launch()`·`launch_persistent_context()`·새 탭 생성 호출이 소스에 있으면 CI가 실패해야 하고, 라이브 전후 target 수가 같아야 한다* | `PASS: launch grep 0건` · `PASS: target N→N` / `CHECKED: 2` |
| **1-4** [3] | *When 로그인·캡차·2FA 순간이 오면, then `Page.bringToFront`로 전면화하고 성공 여부를 `run_log`에 남겨야 한다* | `PASS: bringToFront 이벤트 기록` / `CHECKED: 2` |
| **1-5** [7] | *While 작업이 끝나면, WebSocket만 해제하고 `close()`·kill·restart를 **0회** 해야 한다* | `PASS: vars(driver)에 소켓 객체 0개` · `PASS: close 속성 부재` / `CHECKED: 3` |
| **1-6** [8] | *When 인증을 판정하면, then **요구 마커 전부**가 매칭되고 그 집합이 라이브 픽스처 속성과 교집합을 가져야 하며, **URL과 검색결과 가시성은 인증 증거로 쓰지 않아야** 한다* | `PASS: 2FA FAQ 문구만으론 미판정` · `PASS: 로그아웃 상태 카드 100장 → 미인증` · `PASS: URL 휴리스틱 경로 0건` / `CHECKED: 5` |

- **1-6이 2판의 미포착 counter-AC 2건을 닫는다**(교집합 공집합만 보면 *잘못된 마커가 매칭되는* 경우를 놓친다).
- 함께: CDP 포트 **조회**(하드코딩 금지 — 실제로 9338이었던 사고) · 생존 판정 = target 존재 + `/json/version` 200 · Keychain 단일 출처(`.env.local` import 전용, 반환 타입은 `Secret` 래퍼 — `str`이면 CI 실패) · **비밀번호 회전 요구 금지**(2026-08-04 결정)
- **좌석 lease(P8)**: SOT는 *"TTL 있는 DB lease + fencing token"*을 요구한다. 창립 스펙의 atomic mkdir + heartbeat는 **다른 기법**이므로, **SOT를 따라 DB lease + fencing token**으로 하고 CDP 호출 직전 토큰 재확인. AC: `PASS: stale 소유자 상태에서 획득 거부` (2판은 이 드리프트를 기재하지 않았다)
- **보안 H-1**: CDP 포트는 사장님 주 프로필 **전체**에 대한 무인증 채널이다(3사가 아니라 메일·은행 쿠키까지). AC 추가 — *`--remote-debugging-address=127.0.0.1`이 아니면 순회 거부* (`lsof`로 확인)
- **보안 H-2**: attach 직후 `Target.getTargetInfo().url`의 origin이 화이트리스트에 없으면 **즉시 detach, 캡처 0건**
- **보안 H-3**: 런타임 프리플라이트는 **영수증을 읽지 않는다.** 순회 직전 **라이브 DOM 마커 재관찰**(navigate·click 0회)로 판정한다. 영수증은 **배송 게이트 전용**이다. → 영수증 위조의 피해 범위가 "계정 접근"에서 "보고 무결성"으로 줄어든다

### Phase 2 — 순회 + 증거 (6 PR · 창립 스펙 §4)

| AC | EARS | 기대 출력 |
|---|---|---|
| **2-1** [1] 9회 | *While 순회가 시작되면, `min_pages`(20) 이상을 방문하거나 그보다 적게 끝나면 `abort_reason`을 기록해야 하며, **사유 없는 종료를 성공으로 기록해서는 안 된다**. 상세를 열지 않은 후보는 0건이어야 한다* | `PASS: abort_reason NULL & completed 인 run 0건` · `PASS: detail 증거 없는 candidate 0건` / `CHECKED: 3` |
| **2-2** [9] | *While 순회 중, 요청 필터가 화면의 **활성 조건 칩**으로 전부 증명되지 않으면 수집을 중단해야 한다* | `PASS: 칩 미증명 시 수집 0건` / `CHECKED: 2` |
| **2-3** [13] | *If 결과 건수 표시가 N>0인데 수집 카드가 0개면, then STOP하고 `preflight_fail`을 기록해야 한다* | `PASS: 카드0 & 건수>0 → preflight_fail` / `CHECKED: 2` |
| **2-4** [10] | *While 순회 중, 간격은 **결정론 지터**로 산출되어 같은 `run_id`가 같은 타이밍 열을 재현해야 하고, **일일 총량 상한**을 넘으면 중단해야 한다* | `PASS: 같은 run_id 타이밍 동일` · `PASS: 고정 간격 리터럴 0건` · `PASS: 일일 상한 초과 시 중단` / `CHECKED: 3` |
| **2-5** [11] | *While 활성 탭이 3사 도메인이고 조작이 감지되면 즉시 양보하고, OS idle 60초 초과 시 **작업 목록을 유지한 채** 재개해야 한다* | `PASS: 양보→재개 후 backlog 길이 보존` / `CHECKED: 2` |
| **2-6** [12] | *While 자동화가 화면을 쓰는 중이면, 배지 주입 후 **픽셀 색 + 히트테스트로 렌더를 증명**하고 실패 시 fail-closed해야 한다* | `PASS: 렌더 증명 실패 시 fail-closed` / `CHECKED: 2` |

- 함께(각 PR에 분산): `reset_filters` · 수집 직전 `bringToFront`+focus emulation · 가상 스크롤 완료 증명(occluded 0 AND unique≥itemCount) · `readyState`를 믿지 않는 유계 재시도(10회×1.5초) · 상세 완료 4조건(2000자 AND 식별자 일치 AND 필수항목 AND 인디케이터 부재) · 같은 URL 연속 2회 금지 · triage 4단(컷은 Non-OTW & 현 회사 24개월 미만 → `triage_deferred`)
- **일일 총량 상한(보안 L-2)**: 2판은 키워드당 20페이지만 상한이고 `continue_with_new_keywords:true`라 무제한이었다. 제재 단위가 계정 잠금이 아니라 **기업회원 계약 해지**일 수 있어 상한을 넣는다.
- **산출물**: `src/humansearch/{driver.py,traverse.py,evidence.py,pacing.py,yielding.py,badge.py}` 각 ≤300줄

### Phase 3 — 채점 + 게이트 (3 PR)

| AC | EARS | 기대 출력 |
|---|---|---|
| **3-1** | *If LLM 출력에 숫자가 포함되면, then 시스템은 그것을 **판정 필드에 넣지 않고** 순수 함수 계산값만 기록해야 한다(P14)* | `PASS: LLM 숫자 주입 시에도 DB 값 == 재계산값` · `PASS: LLM→판정필드 파싱 경로 lint 0건` / `CHECKED: 3` |
| **3-2** | *If 평가 클라이언트를 쓸 수 없으면, then **실패해야 한다** — 레거시 축 폴백 금지* | `PASS: 클라이언트 부재 시 exit 1, scores 0건` / `CHECKED: 2` |
| **3-3** | *While 등록 경로가 여럿이어도, `registrations`에 도달하는 후보는 전부 `eligible()` **한 함수**를 통과해야 한다* | `PASS: 미달 후보 registrations 도달 0회` / `CHECKED: 2` |

- 가중치 27/10/14/9/7/10/14/9=100 · 합격선 70과 게이트 캡(필수요건 fail→49, uncertain 2개+→69) 한 세트 · 하드제외(프리랜서 · 12개월 미만 2회+ · 전문대는 사람인·잡코리아만, **LinkedIn 학교 하드컷 없음**) · 문턱을 파이프라인 간에 섞지 않는다

### Phase 4 — 등록 어댑터 (2 PR)

| AC | EARS | 기대 출력 |
|---|---|---|
| **4-1** | *While 모든 어댑터가 비활성이면, Phase 0~3을 그대로 완주해야 한다* | `PASS: 어댑터 0개로 파이프라인 완주(후보 >= 1)` / `CHECKED: 2` |
| **4-2** (P9) | *When 등록하면, then `(position, candidate, channel)`에 **DB unique**가 걸리고 실행 **전** intent를 기록하며 실행 **후** 화면 재확인(readback)해야 한다* | `PASS: 중복 등록 거부` · `PASS: intent→readback 쌍 누락 0건` / `CHECKED: 3` |

- **불변식**: 발송(제안·InMail·메일) **Send 클릭 0회**. AC-4-1의 `PASS: Send 경로 grep 0건`은 어댑터 0개일 때 자동 참이므로 **4-2(어댑터 활성 상태)에서 검사**한다.
- 2판은 Phase 4를 "선택적"으로 뒀다가 철회했다 — 완료 정의에 선택항이 있으면 완료가 협상 가능해진다.

---

## §7. 원칙 → 기계 장치 전수표 (P1~P22)

2판은 사고 14유형엔 전수표를 만들고 P번호엔 만들지 않아, **P4·P8·P9·P10·P12·P16·P2가 "적용한다"로만 선언**돼 있었다. P1은 *"기계 장치 없는 원칙은 삭제한다"*이므로 전수로 적는다.

| P | 이 계획의 기계 장치 |
|---|---|
| P1 | 이 표 자체 + A1(원장 강제) |
| P2 | §6 전 AC에 검증 명령·기대 출력·`CHECKED: n` |
| P3 | ruff `E722`/`BLE001` (A2) · 3상태 종료코드(§5-4) |
| **P4** | **A5** — 외부 효과 모듈을 파일명이 아니라 `contracts/external-effect-modules.txt` 선언 목록으로 판별 + 네트워크 0건 시 차단 |
| P5 | 속성 기반 3함수(Phase 0) + 표본 뮤테이션 |
| P6 | uv 락파일 + `.python-version` 고정(A2) |
| P7 | forward-only 마이그레이션 + `schema_version`(Phase 0) |
| **P8** | **1-좌석 PR** — DB lease + TTL + fencing token (창립 스펙의 mkdir 방식과 갈라짐, §6 Phase 1에 명시) |
| **P9** | **4-2** — DB unique + write-ahead intent + readback |
| **P10** | Phase 4에 일일 접촉 건수 외부 전송 1건 (감시자는 별도 실패 영역) — **미배정, §10 한계** |
| P11 | §6 각 Phase 산출물의 LOC 예산 · PR = AC 1개 |
| **P12** | A1이 `suppressions.yaml` 재사용(새 장치 안 만듦) · 이 표가 회수 결과 |
| P13 | `.check-weakening-patterns`(기존) + B3 외부 패턴 파일 |
| P14 | **3-1** + §5-5(LLM은 사실만, 숫자는 순수 함수) |
| P15 | A1(로컬-CI 동치) · pre-push 작업트리 청결(기존) |
| **P16** | 계약 테스트를 **런타임 import·호출**로(1-5의 `vars(driver)`가 그 예) · 텍스트 단언 파일은 `.contract.test.py` 접미사 — **부분, §10** |
| P17 | §4-1 Q3을 사람에게 이관(기계인 척 안 함) · 키 화이트리스트(§5-2) |
| P18 | 클로저 소유권(§3-A) — 금지가 아니라 능력 제거 |
| P19 | 외부 의존 경로 PR은 라이브 1건 필수(§4-1 Q3) |
| P20 | 모든 `CHECKED: n`의 하한 · B4의 `>= 1` · A2의 "대상 수 == 파일 수" |
| P21 | **A4** — 1MB 차단(로컬·CI 양쪽) + `artifacts/`·`*.db`·`data/` gitignore |
| P22 | 셀렉터·문턱은 `contracts/`·`config/` 데이터(§5-3·Phase 0) · **A3** 세션 계열 패턴 |

---

## §8. 롤백 · 영향 반경

- **롤백 단위 = PR 1개.** `git revert <merge sha>`. Phase A만 게이트 자체를 건드리므로 revert 후 `scripts/acceptance-0-7.sh`(훅 위반 6종 시연)로 복귀 확인.
- **DB**: forward-only + `schema_version`. N-1이 현재 스키마를 읽을 수 있음을 검사(P7).
- **영향 반경 4가지**:
  ① 3사 계정(잠금·**계약 해지** — 1-2·2-4)
  ② 사장님 크롬 세션(닫지 않음·새 탭 0·즉시 양보·재개 보장 — 1-5·2-5)
  ③ **사장님 주 프로필 전체**(CDP 포트는 무인증 전권 채널 — 메일·은행 쿠키까지. 1-3의 127.0.0.1 바인딩 + H-2 origin 검증) ← 2판이 빠뜨린 가장 넓은 반경
  ④ 후보자 PII(A4 + Phase 0의 `purge_candidate` + 0700/0600)

---

## §9. 재검증 시 통과해야 할 것

1. **D-1**(V1 원문 기준): 0바이트 증거 + 실제 HEAD SHA + 러너 재실행 체인이 **거부**되는가 — 거부 사유가 *"에이전트가 만들 수 없는 외부 객체 부재"*여야 한다. ⚠️ **3판은 이 조건을 충족하지 않는다. 대신 그 판정을 기계에서 사람으로 이관했다(§4-1 Q3)** — 기준을 낮춘 것이 아니라 **기계가 못 한다고 명시**한 것이며, 그 차이를 §10에 적었다.
2. 신규 인수 스크립트가 CI 실행 줄 또는 원장 어디에도 없으면 push가 차단되는가(A1).
3. 종료코드 0·1·2 각각에 대해 pre-push·CI 판정이 §5-4대로인가(특례 0건).
4. `session-status.sh`가 억제된 RED를 **출력에 명시하며** 분리 계상하는가(A6).
5. B3 검사기가 자기 리터럴에 매칭되지 않으면서 검출력이 동일한가.
6. **N=0 공허 통과가 남아 있는 AC가 있는가** — 모든 `CHECKED: n`과 개수 단언에 하한이 있는가.

---

## §10. 비범위 / 한계 (정직하게)

- **이번 산출물은 문서뿐이다.** 코드 0줄, 인수 스크립트 0개. Phase A부터가 실제 작업이다.
- **라이브 실재는 기계가 판정하지 않는다.** §4-1 Q3을 오너 판정으로 이관했다. 이것은 D-1을 **닫은 것이 아니라 담당자를 바꾼 것**이다. 러너를 실행할 수 있는 주체는 여전히 형식상 완전한 영수증을 만들 수 있고, 기계는 그것을 구별하지 못한다. **완전 충족에는 러너 전용 권한 분리(별도 자격·디바이스)가 필요하며 별도 이슈다.**
- **HOST 계층은 오늘 실행 불가** — CDP 디버그 포트를 LISTEN하는 크롬이 0개다(1-13). 라이브 인수는 **사장님이 디버그 프로필 크롬을 띄운 시점**에만 진행된다. 일정은 이 외부 의존을 분리해서 잡아야 한다.
- **P10(외부 감시자)은 어느 Phase에도 배정하지 못했다.** SOT는 *"감시자는 감시 대상과 다른 실패 영역"*을 요구하는데 이 계획에 그 채널이 없다.
- **P16은 부분**이다. 텍스트 단언 접미사 규칙은 넣었으나 "테스트/구현 비율과 결함률 상관계수 주기 계산"은 없다.
- **사고유형 [14](서치 범위 축소)** 1건 미해결. `search_url` 화이트리스트로 부분만 덮인다.
- **유형 [5](자격증명)는 "덮음"이 아니라 "부분"**이다 — 2판은 §8의 PII AC를 근거로 "덮음"이라 셌는데 같은 문서가 그 AC를 "얇다"고 적었고(이중장부), 보안 리뷰는 그 방어의 두 다리가 **실재하지 않는다**고 확인했다. A4·Phase 0으로 실체를 만든 뒤에야 "덮음"이 된다.
- **잡코리아·LinkedIn은 B-2·B-3 전까지 순회 불가**(의도된 fail-closed). 3사 전체 범위는 그 두 PR 완료 시 충족된다.
- **1MB 미만 PII는 크기 문턱으로 못 막는다.** 특히 `receipts/`·`fixtures/live/`는 계획상 **커밋 대상**이라 A4의 경로 차단 밖에 있다. 그 두 경로의 유일한 방어선은 A3의 내용 검사와 AC-B2(픽스처 텍스트 노드 0건)이며, **B2 병합 전까지는 방어가 한 겹뿐**이다.
- **A3는 세션 값 '모양'에 의존한다.** LinkedIn이 쿠키 값 형식을 바꾸면 값-모양 패턴이 무력해지고 키 이름 패턴만 남는다. 형식 변경은 예고 없이 일어난다 — 정기 재확인이 필요하며 이 계획에 그 주기가 없다.
- **`suppressions.yaml` 만료 3건**(08-21 · 09-15 ×2)이 작업 기간과 겹친다. `ci-transfer-guarantee`는 **A1이 재사용하는 마커 검증 패턴이 4종 우회로 뚫려 있다는 원장**이다 — A1은 그것을 해소하지 않는다(방어 심도).
- **작업량·세션 수 견적은 내지 않는다.**
- probe 커밋 `6538bac`는 unreachable 객체로 잔존(워크트리·브랜치는 제거). `acceptance-0-2`를 빨간불로 유지하는 조건 중 하나다.

---

## §11. 적대 검증 로그

### V1 — codex 별도 세션 (2026-08-08) · **VERDICT: FAIL** · D-1~D-10
판정 원문: `docs/engineering/humansearch-plan-v1-verdict-2026-08-08.md`(446줄, verbatim). V1이 깨려다 실패한 것: §1 사실표 9개 전량 재현(과장 0건) · mypy가 5조-5를 실제로 잡음(런타임 결정은 SOT 위반 아님) · `docs/engineering/` 제외는 선례 있는 정당한 범위.

### V2 — Claude 재현 (2026-08-08)
V1 결함 10건을 독립 코드로 재현. **뒤집힌 것**: V1이 내 과장 3건을 잡았고(라이브 CI 영구 FAIL / P17 충족 / PUSH-PERFORMING 동형), 내가 V1의 판본 차이 1건을 잡았고, V1이 내 과소평가 1건을 교정했다(Python 타입 강제력).

### V3 — 2판에 대한 품질·보안 리뷰 (2026-08-08) · **양쪽 FAIL**
- **품질**: 치명 4(증거 전달 경로 · A1 vs `acceptance-0-2` 딜레마 · `code_commit` 자기참조 · Phase B 공허 통과) · 중대 11 · 경미 4
- **보안**: Critical 2(세션 계열 비밀 미탐지 · 크기 차단·gitignore 부재) · High 4 · Medium 5 · Low 4
- **가장 무거운 지적**: 2판이 **V1의 재검증 기준 자체를 낮췄다**(에이전트가 만들 수 없는 외부 객체 → `curl` 한 번이면 만들어지는 앵커). 판정 기준에 P13(검사 약화 금지)을 적용한 형태다. 3판은 기준을 원문으로 되돌리고, 충족 대신 **담당자 이관을 명시**했다(§9-1).
- 리뷰어들이 깨려다 실패한 것: B3 외부 패턴 분리는 P13④ 위반 아님 · `search_url` 화이트리스트는 fail-closed라 "열거는 샌다"에 안 걸림 · **상수·가중치 인용에서 왜곡 0건** · §1 사실표 재확인 · HOST-ONLY 폐기 결정 자체는 옳음.

**현재 상태**: V1 D-1은 §4-1 Q3 이관으로 **성격이 바뀌었을 뿐 기계적으로는 미해결**이다(§10 첫 항목). V3 치명 4건은 §4-2(증거 경로)·§4-4(원장 재사용)·§5-2(`code_commit` 조상 검사)·B4(하한)로 각각 닫았다. **닫혔다고 주장하는 것과 실제로 닫힌 것을 다음 검증이 다시 갈라야 한다.**

---

## §12. 개정 이력

| 판 | 무엇이 바뀌었나 |
|---|---|
| 초판 (334줄) | 최초 작성. V1에서 FAIL — 영수증 4장치가 라이브 0회·0바이트로 통과 |
| 2판 (403줄) | V1 10건 반영 시도. **두 곳에서 자기 판정을 낮춤**(재검증 기준 치환 · "10건 전부 반영" 거짓) → `2766435`로 정정 |
| **3판** | **전제 교체**: "CI가 라이브를 판정할 수 있다" → "못 한다고 명시하고 사람에게 이관". 증거 파일 git 밖 확정(딜레마 해소) · A1을 원장 재사용으로 · `code_commit` 조상 검사 2모드 · B4 하한 신설 · PR=AC 1개로 복원 · P1~P22 전수표 · 보안 Critical 2건을 Phase A로 이관 · LLM은 숫자를 만들지 않음(P14 우선, 창립 스펙과 드리프트 명시) |
