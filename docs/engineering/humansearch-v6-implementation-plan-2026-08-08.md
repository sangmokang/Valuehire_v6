# humansearch v6 구현 계획 (goal) — 타 저장소 의존 0

- **작성일**: 2026-08-08 · **개정 2판** (V1 적대검증 FAIL 판정 D-1~D-10 반영. 초판 334줄은 §11 판정서가 인용하는 판본이다)
- **위험 등급**: 이 문서 자체는 **L2**(문서 산출물, 소스 변경 0). 이 문서가 계획하는 **각 Phase는 L3**(인증·자격증명·외부 사이트 경로 접촉 → 풀하네스).
- **지시**: 2026-08-08 사장님 — *"이 구현 프롬프트를 다른 폴더 구현 코드를 절대 참조하지 말고 스스로 다시 짜 … 타 레파지토리 의존성 전혀 두지 말고 구현 계획 짜도록해"*
- **상위 스펙(SOT 아님, 창립 지시서)**: `docs/engineering/humansearch-v6-founding-spec-2026-08-07.md` (657줄, 커밋 `3d7930c`)
- **준수 대상 SOT**: `docs/sot/coding-principles.md`(P1~P22·웹자동화 5조·V-1~V-5) · `docs/sot/verification-commands.md` · `docs/sot/hook-contracts.md` · `docs/sot/git-workflow.md`
- **적대검증**: V1 판정서 `docs/engineering/humansearch-plan-v1-verdict-2026-08-08.md`(VERDICT: FAIL, 결함 10건) · V2 재현 결과는 §11
- **회수(C)**: `git ls-files`(46개 전량) · `docs/sot/*` 4종 · `hooks/pre-commit`·`hooks/pre-push`·`verify.sh`·`scripts/*.sh`·`.github/workflows/verify.yml`·`suppressions.yaml`(억제 4건 전문)·`.check-weakening-patterns` 정독 · 자동메모리 `MEMORY.md` 10항목

---

## §0. 결론 3줄

1. **타 저장소를 안 봐도 된다.** 셀렉터를 "코드 이식"이 아니라 **라이브 캡처로 v6 안에서 재획득**하는 루프(Phase B)를 먼저 만들면, 창립 스펙 §4가 남긴 유일한 잔여 작업("로컬 worktree를 push하거나 복사")이 사라진다. 다만 이 지시의 기계 장치(AC-B3)는 **경로 문자열 탐지라는 대리지표**이고, 코드를 복붙하고 경로만 지우면 잡히지 않는다 — 한계를 §10에 적었다.
2. **선행 Phase A가 필요한 이유는 "push가 막힌다"가 아니라 "CI가 안 본다"다.** `hooks/pre-push`는 글로브로 신규 인수 스크립트를 자동 포함하지만 `.github/workflows/verify.yml`은 **고정 스텝 목록**이다 — 신규 `scripts/acceptance-hs-*.sh`는 **CI에서 한 줄도 실행되지 않고** `bash -n`(문법 검사)만 걸린다. P15③("로컬에만 있는 검사는 없는 것으로 친다") 정면 위반이며, 이 상태로는 게이트 5의 "CI 초록"이 첫 Phase부터 위장 가능하다. (초판은 이 자리에 "라이브 인수가 CI에서 영구 FAIL이라 merge 불가"라고 적었다 — **거짓이었다.** CI는 애초에 그 스크립트를 실행하지 않으므로 빨간불도 나지 않는다. V1 D-2·D-3에서 뒤집혔다)
3. **런타임은 Python 3.14 + uv로 확정**한다(§3). 게이트 계약은 bash 인수 스크립트로 유지한다 — `pytest`는 인수 스크립트 안의 구현 수단일 뿐 게이트 계약이 아니다.

---

## §1. 현재 상태 (전부 2026-08-08 실행 확인, 추측 0)

| # | 사실 | 증거 |
|---|---|---|
| 1-1 | 이 저장소에 **제품 코드가 0줄**이다. 추적 파일 46개 전부 문서·훅·bash | `git ls-files \| wc -l` → 46 |
| 1-2 | `Makefile`·`package.json` 없음. `make -n red-ledger` → `No rule to make target` | 실행 확인 |
| 1-3 | **RED 원장의 실제 구현체는 bash 글로브다** — `find . -maxdepth 2 \( -name 'verify.sh' -o -name 'acceptance-*.sh' \)` 를 돌려 실패 개수를 센다 | `scripts/session-status.sh:44-70` |
| 1-4 | 현재 RED = **1/4**. 빨간 것은 `scripts/acceptance-0-2.sh`(rc=1) | 4개 직접 실행 |
| 1-5 | `pre-push`는 acceptance 글로브 전량을 실행하고 **0이 아닌 종료코드 전부**(1·2 모두)를 차단한다 | `hooks/pre-push:112,166` · V1 실측 |
| 1-6 | 실패하는 인수 스크립트 1개를 커밋 후 훅 실행 → `BLOCKED: … exit=1`, exit 1 | probe 커밋 `6538bac`(워크트리·브랜치는 제거했으나 **커밋 객체는 unreachable로 잔존** — E-2) |
| 1-7 | **글로브는 이름·깊이에 묶여 있다.** `scripts/live-x.sh`(이름 불일치)나 `host/live/acceptance-x.sh`(깊이 3)는 차단을 벗어난다 | V1 D-3 실측(exit 0으로 통과) |
| 1-8 | **CI는 고정 스텝 목록이다.** acceptance는 `0-6`·`0-7`·`0-5` 세 이름만 실행. 글로브 0건 | `.github/workflows/verify.yml:66,79,84` — 직접 grep 확인 |
| 1-9 | 런타임 실재: `python3` **3.14.1** · `uv` **0.11.3** · `node` v22.19.0 · `sqlite3` 3.51.1(stdlib) · `/usr/bin/security` | `python3 -VV` 등 |
| 1-10 | **지금 CDP 디버그 포트를 LISTEN하는 크롬이 0개다** | `lsof -nP -iTCP -sTCP:LISTEN \| grep -icE 'chrome\|922[0-9]'` → 0 |
| 1-11 | 억제 4건. 만료 `2026-08-21`(acceptance-0-2) · `2026-09-15` 2건 · `2026-09-30` 1건. 그중 **`ci-transfer-guarantee`는 "마커 검증 패턴이 4종 우회로 뚫렸다"는 원장**이다 | `suppressions.yaml:26-42` |

---

## §2. 근본 원인

### 2-A. 원인 ① — 신규 인수 스크립트가 **로컬에만 존재**한다 (P15③ 위반)

두 강제 장치의 탐색 방식이 다르다.

| | 탐색 방식 | 신규 `acceptance-hs-*.sh` |
|---|---|---|
| `hooks/pre-push` | **글로브**(`find … -name 'acceptance-*.sh'`) | 자동 포함 → 실패 시 차단 |
| `.github/workflows/verify.yml` | **고정 스텝 목록** | **한 줄도 실행 안 됨.** `bash -n`(문법 검사)만 걸린다 |

`hooks/pre-push:87-88`이 스스로 적어둔 문장이 그대로 적용된다 — *"`bash -n <script>`는 문법 검사일 뿐 실행하지 않는데, 워크플로 diff에서 정상 lint 스텝과 구분되지 않아 특히 위험하다."* 결과: **게이트 5의 "CI 초록"이 그 Phase의 인수 기준과 무관한 초록이 된다.** 이것이 Phase A의 첫째 근거다.

### 2-B. 원인 ② — 차단 범위가 **이름·깊이 규약**에 묶여 있다

`pre-push`의 글로브는 `scripts/acceptance-*.sh`(깊이 2)만 본다. 이름을 바꾸거나 한 단계 더 깊이 두면 실패하는 검사가 있어도 push가 통과한다(V1 D-3 실측). 이것은 결함이지만, **이 계획의 태도는 "탈출로가 있으니 쓴다"가 아니라 "탈출로를 쓰지 않기로 결정하고, 그 규약이 CI까지 도달하게 일반화한다"**다. 규약을 지키기로 한 순간 §2-A가 유일한 실제 문제로 남는다.

> 초판은 여기서 *"다단계 프로젝트는 전부 초록 전까지 push 불가"* 와 *"라이브 인수는 CI에서 영구 FAIL"* 두 문장을 근거로 삼았다. 앞의 것은 §4-3의 "1 Phase = 1 PR"이 스스로 해소하는 자작 문제였고, 뒤의 것은 §2-A와 모순되는 거짓이었다(CI가 실행하지 않으므로 FAIL도 없다). **둘 다 철회한다.**

### 2-C. 원인 ③ — 창립 스펙의 잔여 작업이 타 저장소 의존이었다

이식이 필요했던 것은 **셀렉터·필터리셋·스크롤 완료판정** 3종이고, 그중 **셀렉터만 "값"**이다. 나머지 둘은 알고리즘이며 조건이 스펙 §4-6·§4-7에 산문으로 전부 있다. 그리고 셀렉터는 **베끼면 안 되는 값**이다 — 스펙 §4-10이 스스로 적었듯 대소문자 불일치를 **합성 fixture가 못 잡고 라이브 캡처 HTML만 잡았다**. 어제 맞은 셀렉터가 오늘 틀린다(2026-07-31 nav DOM 변경으로 후보 20명 유실). 따라서 v6는 셀렉터를 **가설로 시작해 라이브 캡처로 승격**시킨다(Phase B).

### 2-D. 원인 ④ — 런타임 미확정으로 인수 기준을 쓸 수 없었다 → §3에서 확정

---

## §3. 런타임 결정 — Python 3.14 + uv

**결정: Python 3.14.1 + uv(락파일 커밋) + ruff + mypy --strict + pytest + Hypothesis.** 게이트 계약은 bash 유지.

| 판단 축 | 판정 |
|---|---|
| SQLite 단일 정본 + WAL + `flock` (스펙 §5) | **Python 우위** — stdlib `sqlite3`+`fcntl`, 네이티브 빌드 0. Node는 `better-sqlite3` 빌드 필요(P6: 실행 환경도 제품) |
| Keychain 단일 출처 (스펙 §3-6) | 무승부 — 양쪽 다 `/usr/bin/security` stdin |
| raw CDP 단일탭 WebSocket | 무승부 |
| P3 조용한 실패 금지 린트 | **Python 우위** — ruff `E722`/`BLE001`/`TRY`. TS는 `\|\|`·`??`가 관용구라 금지 시 오탐 폭증 |
| P5 속성 기반 테스트 | **Python 우위** — Hypothesis |
| P21 빌드 산출물 최소화 | **Python 우위** — `node_modules`·`dist` 없음 |
| 웹자동화 5조-5 "개입 이후 호출이 **타입상 불가능**" · 스펙 §2-6 "`close()` 미노출" | **mypy --strict로 충족된다** — V1이 반증을 시도해 실패했다(`"LiveDriver" has no attribute "close"` / `Argument 1 … incompatible type "LiveDriver \| Yielded"`). 초판이 이것을 "Python 열위"로 적은 것은 **과소평가였다** |

### 3-A. 타입만으로는 안 닫히는 구멍 — 원시 참조 에일리어싱 (V1 D-5)

원시 CDP 객체 참조가 같은 스코프에 살아 있으면 mypy도 런타임 계약 테스트도 못 잡는다. V1이 실증했다:

```python
d: LiveDriver = raw          # 래퍼로 좁혔지만
after = detect_intervention(d)
raw.close()                  # 원시 참조로 직접 호출 → mypy 오류 0건
raw.navigate("https://x")    # 개입 이후에도 타입상 합법
```

**이 구멍은 TypeScript로 바꿔도 닫히지 않는다.** 필요한 것은 타입이 아니라 **소유권 규칙**이다 — 계약에 넣는다:

- **원시 소켓 객체는 팩토리 밖으로 이름 바인딩되지 않는다.** 팩토리는 래퍼만 반환하고, 원시 타입은 모듈 private + `__all__` 미포함. 계약 테스트가 모듈 export에 원시 타입이 없음을 **런타임으로** 단언한다(P16).
- **재승격 전이 계약** (V1 D-10 — 초판은 `Yielded → LiveDriver` 복귀를 정의하지 않아 "5조-5 충족"과 "영구 중단 금지"가 서로를 막았다):
  ```python
  def resume(y: Yielded, proof: LiveAuthProof) -> LiveDriver: ...
  # LiveAuthProof 는 라이브 재검증 함수만 생성할 수 있다(모듈 private 생성자).
  # 조건 없는 재승격 = 5조-5 무력화 / 전이 미정의 = 영구 중단(SOT 위반). 둘 다 피한다.
  ```

**버전 고정**: `.python-version` = `3.14.1`(호스트 실측값), `uv.lock` 커밋. CI는 `uv python install`로 같은 버전을 받는다.

---

## §4. 인수 기준 채널 설계 — HOST-ONLY 마커를 폐기한다

### 4-1. 초판 설계를 버리는 이유 (V1 D-6·D-7)

초판은 `# HOST-ONLY` 마커를 만들고 세 규칙을 나란히 뒀다 — ① 영수증이 유효하면 통과 ② 영수증 없으면 차단 ③ **라이브 없이 초록이면 차단**. ③은 ①과 정면 충돌해 **세 규칙을 동시에 만족하는 종료코드가 존재하지 않았고**, ③은 애초에 기계가 판정할 수 없다(pre-push는 "라이브가 있었는데 통과"와 "없이 통과"를 구별할 수단이 없다). 게다가 마커가 라이브 부재 시 exit 2를 내면 `session-status.sh:63`이 그것을 RED로 세므로 **크롬이 안 떠 있는 모든 세션에서 RED 원장이 상시 빨간불**이 된다 — 원장을 없애는 것과 같다. "PUSH-PERFORMING과 동형"이라는 주장도 거짓이었다(그 마커는 *"독립 러너에 등록됐는가"*라는 검증 가능한 명제를 갖는데, HOST-ONLY에는 그 명제가 없다).

### 4-2. 대신: 라이브 **실행**과 라이브 **검증**을 다른 파일로 쪼갠다

| 파일 | 하는 일 | 어디서 도는가 | 글로브 |
|---|---|---|---|
| `tools/live_<n>.py` | 라이브를 실제로 실행하고 **영수증을 생성**한다 | 사장님 맥 전용 | **인수 스크립트 아님** — 걸리지 않는다 |
| `scripts/acceptance-hs-<n>.sh` | **커밋된 영수증을 검증**한다 | 로컬·CI **동일하게** | 걸린다. exit 0만 통과 |

이렇게 나누면 **특례가 사라진다.** 모든 인수 스크립트가 같은 규칙으로 판정되고(P15③ 충족: 같은 검사가 양쪽에 있다), RED 원장 오염도 없고(영수증이 커밋되면 초록), 마커도 필요 없다. 라이브 부재는 exit 2(NOT_RUN)가 아니라 **exit 1(FAIL — 라이브 증거 없음은 미완이다)**이다.

### 4-3. 영수증 검증 — 초판의 4개 장치는 뚫렸다. 무엇이 남고 무엇을 더하는가

**V1은 초판 문구를 그대로 코드화해 4개 장치 전부를 통과시켰다. 라이브 0회 · 크롬 0개 · 증거 파일 전부 0바이트.** 나(V2)도 독립 코드로 재현했다(§11).

| 초판 장치 | 실제 보장 | 판정 |
|---|---|---|
| ① 해시 체인 | **이미 후속 레코드가 있는 줄**의 사후 조작만 탐지. 꼬리 레코드 위조 후 정상 append하면 새 `prev`가 위조된 줄에서 계산돼 **체인이 다시 온전해진다**. 전량 재생성도 탐지 못 한다 | 초판의 *"한 줄 조작하면 이후 전부 깨진다"*는 **거짓** — 철회 |
| ② 코드 SHA 결박 | 유효. 단 실제 HEAD를 쓰면 공정하게 만족되므로 위조를 막지 못한다 | 유지(보조) |
| ③ "쓰기 주체 분리(P17)" | **이름만 빌렸다.** P17의 요구는 *"에이전트에게 그 경로의 쓰기 권한 자체를 주지 않는다"*(`coding-principles.md:32`)인데, 초판은 권한을 분리하지 않고 체인 내부 일관성으로 대체했다 | **제목 철회** |
| ④ 비밀 부재 + 크기 제한 | 유효 | 유지 |

**더하는 것 — 3겹**:

1. **증거의 실질성** (D-1 공격 1을 막는다): `bytes > 0` AND 최소 크기(스크린샷 ≥ 20KB, 텍스트 ≥ 2000자 — 스펙 §4-8의 상세 완료 임계와 동일) AND 파일 매직바이트 일치(PNG) AND **텍스트 증거 안에 그 채널의 인증 마커가 실제로 존재**(라이브 픽스처 교집합과 대조). 0바이트 파일은 SHA를 정직하게 기록해도 여기서 죽는다.
2. **외부 서버 시각 결박** (소급 위조를 막는다): 영수증은 라이브 실행 시점의 **3사 도메인 응답 헤더 `Date` + 응답 본문 해시**를 담고, 검증기는 그 시각이 영수증 시각과 ±120초 안인지 본다. 에이전트는 **과거 시각의 영수증을 지어낼 수 없다**(현재 시각의 것은 여전히 만들 수 있다 — §10 한계).
3. **1 라이브 = 1 PR**: 배송 게이트는 **그 PR의 HEAD SHA로 생성된 영수증만** 인정한다. 초판의 "30일 신선도"는 **삭제**한다 — 라이브 1건이 30일치 초록을 사는 것은 V-3(*"라이브 1건 없이 완료 없음"*)을 30일 단위로 면제하는 것이다. 신선도 값은 **1800초 하나만** 존재하며 그것은 *순회 진입 게이트*용이다(배송 게이트와 개념이 다르다 — 초판은 30일과 1800초를 같은 필드에 1440배 차이로 걸어뒀다).

**정직한 한계**: 러너를 실행할 수 있는 주체는 **지금 시각의 영수증을 위조할 수 있다.** 이 계획은 그것을 막지 못한다. P17 완전 충족에는 러너 전용 권한(별도 자격·디바이스·CI 러너)이 필요하고 그것은 별도 이슈다. `suppressions.yaml:39-42`(`ci-transfer-guarantee`)가 이미 같은 결론 — *"실행 증명으로 바꾼다"* — 에 도달해 있었고, **초판은 그 원장을 회수하지 못했다**(P12 위반). 이 문서가 그것을 회수한다.

---

## §5. 계약 스펙 (손대기 전에 박는 입출력)

### 5-1. 실행 입력

```jsonc
// RunRequest — CLI/API/큐 어느 진입이든 이 계약만 받는다. 포지션 하드코딩 금지.
{ "channel": "saramin|jobkorea|linkedin_rps",
  "position_ref": "string",
  "search_url": "https://…",   // ⚠️ 3사 인재풀 URL 형태 화이트리스트만 허용(사고유형 [14] 부분 대응)
  "target_id": "string",       // 기존 CDP target. 새 탭 생성 금지
  "jd_or_config": { } }
// 에러: 필드 누락·빈 문자열·비-http·화이트리스트 불일치 → ValidationError(exit 2). 기본값 채우기 금지(P3).
```

### 5-2. 로그인 영수증

```jsonc
// receipts/<channel>.json — tools/live_*.py 만 쓴다. 커밋된다(작아야 하는 이유: P21)
{ "schema_version": 1, "channel": "saramin", "host_id": "sha256(hostname+uuid)",
  "state": "AUTHENTICATED",                            // HUMAN_AUTH·AUTH_CONFLICT 거부
  "last_verified_at": "2026-08-08T12:00:00+09:00",     // 시간대 필수, 미래 거부, 1800초 만료(순회 진입용)
  "owner_activity_detected": false, "mutation_count": 0,
  "evidence": [ {"path":"artifacts/…/nav.png","sha256":"<64hex>","bytes":48231,"kind":"png"},
                {"path":"artifacts/…/body.txt","sha256":"<64hex>","bytes":8123,"kind":"text",
                 "auth_markers_found":["account","search"]} ],   // 3개, 실질성 검사 대상
  "external_anchor": { "origin":"https://www.saramin.co.kr", "server_date":"Sat, 08 Aug 2026 03:00:01 GMT",
                       "response_sha256":"<64hex>" },            // ±120초 대조
  "code_commit": "<git sha — 이 PR 의 HEAD>", "prev_receipt_sha256": "<64hex|null>" }
// validate(receipt) -> PASS | FAIL(reason[]) | NOT_RUN.  NOT_RUN 이 하나라도 있으면 전체 PASS 불가(P3).
// SHA 는 형식 검사가 아니라 파일에서 재계산해 대조한다 + 위 §4-3 의 실질성 3겹을 전부 통과해야 한다.
```

### 5-3. 셀렉터 계약 (타 저장소 의존 제거 지점)

```jsonc
// contracts/<channel>/selectors.json — 셀렉터는 코드가 아니라 데이터다(5조-1, P22)
{ "detail_link": { "candidates": ["a[data-test-…]", "…폴백…"],
    "status": "hypothesis|live_confirmed",
    "fixture_ref": "fixtures/live/linkedin_rps/list-2026-08-08.json",   // live_confirmed 필수
    "confirmed_at": "…", "matched_nodes": 25 } }
// 게이트: hypothesis 가 하나라도 있으면 그 채널 순회는 거부.
//        live_confirmed 인데 fixture_ref 부재 또는 그 픽스처에서 매칭 0건이면 FAIL.
```

```jsonc
// fixtures/live/<channel>/<surface>-<date>.json — 축약 캡처(원본 HTML·PNG 는 git 밖)
{ "surface":"list", "captured_at":"…", "url_shape":"https://…",   // query 제거(로그 위생)
  "attrs":["data-test-…"], "nodes":[{"selector_hit":"…","outer_html_excerpt":"…"}],
  "source_sha256":"<원본 HTML sha256>", "bytes":0 }                // 축약본 200KB 이하 강제
```

### 5-4. 인수 스크립트 출력 계약 (게이트 계약 — bash, 런타임 무관)

```
scripts/acceptance-hs-<id>.sh
  exit 0 = PASS  |  exit 1 = FAIL(라이브 증거 없음도 FAIL)  |  exit 2 = NOT_RUN(전제 자체를 읽을 수 없음)
  stdout: 검사 항목마다 "PASS: …" / "FAIL: …" / "NOT_RUN: …" 전부 출력(조용한 통과 금지)
  마지막 줄: "CHECKED: <검사 항목 수>" — 0 이면 스크립트 스스로 FAIL(P20)
  불변식: pre-push·CI 는 exit 0 만 통과시킨다. 특례·마커 없음(§4-1)
```

### 5-5. 판정 함수 계약 (P14 — 숫자는 코드만 만든다)

```
score(candidate, jd) -> { d1..d8:int, sub_reasons:{d1:str,…}, total:int,
                          tier:"strong|pass|reject", input_sha256:str, fn_version:str }
  · LLM 은 d1..d8 과 sub_reasons 만 낸다. total·tier 는 순수 함수가 계산한다.
  · LLM 출력에서 total 을 파싱하는 경로는 존재 자체가 금지(ruff 커스텀 룰 + 계약 테스트).
  · 폴백 금지: 평가 클라이언트 부재 시 fail-closed. 레거시 축으로 조용히 내려가지 않는다.
eligible(candidate) -> bool    # 유일한 경계 함수. total >= register_min AND profile_url 유효.
```

---

## §6. Phase 계획 — 1 Phase = 1 PR. **각 AC에 검증 명령과 기대 출력을 붙인다** (V1 D-8)

게이트는 `docs/sot/verification-commands.md`를 따른다: 0 `bash scripts/session-status.sh` → 2 `git worktree add worktrees/<name> -b task/<name>` → 4 `bash verify.sh` + 해당 인수 스크립트 → 5 push·PR·CI 초록 → 6 워크트리 제거.

**기대 출력 표기 규칙**: 각 인수 스크립트는 마지막 줄에 `CHECKED: n`을 낸다. 아래 표의 "기대 출력"은 그 n과 반드시 나와야 하는 PASS 라인이다.

### Phase A — 게이트 확장 (선행 1)

| AC | EARS 단언 | 검증 명령 | 기대 출력 |
|---|---|---|---|
| **A1** | *When 저장소에 `scripts/acceptance-*.sh` 가 존재하면, then `pre-push`는 그 각각이 CI 워크플로의 **실행 줄**에 등록돼 있는지 확인하고 없으면 차단해야 한다* | `bash scripts/acceptance-hs-a1.sh` | `PASS: acceptance 스크립트 N개 전부 CI 실행 줄에 등록` / `CHECKED: N+2` |
| **A2** | *When 파이썬 소스가 존재하면, then CI는 ruff·mypy·pytest를 실행하고 **검사 대상 수가 `git ls-files '*.py'` 개수와 일치**함을 단언하며, pytest 수집 케이스가 1건 미만이면 실패해야 한다* | `bash scripts/acceptance-hs-a2.sh` | `PASS: ruff 대상 K개 == ls-files K개` · `PASS: mypy 대상 K개` · `PASS: pytest 수집 T건 (>=1)` / `CHECKED: 3` |

- **A1의 구현**: `hooks/pre-push:93-97`의 `DEFERRED` 검증(“CI 실행 줄에 있는가”)을 **글로브 전량으로 일반화**한다. 이미 검증된 정규식(`RUNVERB` — `bash -n`·`bash -c`·`echo` 대체를 막는다)을 재사용한다.
- **A1의 알려진 한계(회수)**: 그 정규식은 `suppressions.yaml:26-42`(`ci-transfer-guarantee`, expiry 2026-09-15)에 **4종 우회가 남아 있다고 기록된 상태**다. A1은 그 억제를 해소하지 않는다 — 방어 심도로 채택하고, 억제 항목을 이 Phase에서 갱신한다.
- **counter-AC**: ① 새 인수 스크립트를 CI에 등록하지 않고 push 통과 ② CI에 `bash -n`으로만 등록 ③ ruff/mypy가 0개 파일을 검사하고 exit 0(P20 — v4 `next typegen` 사고)
- **산출물**: `hooks/pre-push` 확장 · `verify.yml` 스텝 추가 · `pyproject.toml`·`uv.lock`·`.python-version` · `scripts/acceptance-hs-a1.sh`·`-a2.sh` · `suppressions.yaml` 갱신 · **SOT diff 2건**(`verification-commands.md`·`hook-contracts.md`)
- **비범위**: humansearch 도메인 코드 0줄.

### Phase B — 라이브 캡처 → 픽스처 → 계약 루프 (선행 2)

| AC | EARS 단언 | 검증 명령 | 기대 출력 |
|---|---|---|---|
| **B1** | *Where `contracts/<channel>/selectors.json`에 `status=="hypothesis"` 항목이 하나라도 있으면, 시스템은 그 채널의 순회 진입을 거부해야 한다* | `bash scripts/acceptance-hs-b1.sh` | `PASS: hypothesis 잔존 시 순회 거부 확인` · `PASS: live_confirmed N개 전부 fixture 매칭 >=1` / `CHECKED: 2+N` |
| **B2** | *When 캡처 도구가 픽스처를 저장하면, then 축약 픽스처는 200KB 이하이고 원본 HTML·스크린샷은 `artifacts/`(git 밖)에 두고 SHA-256만 기록해야 한다* | `bash scripts/acceptance-hs-b2.sh` | `PASS: 픽스처 N개 전부 <=204800 바이트` · `PASS: 추적 파일에 1MB 초과 데이터 0건` / `CHECKED: 2` |
| **B3** | *If **추적 파일**이 타 저장소 경로 패턴을 포함하면(단 `docs/engineering/` 제외), then CI는 실패해야 한다* | `bash scripts/acceptance-hs-b3.sh` | `PASS: 실행 경로 0건` · `PASS: 패턴 파일에 실행 코드 없음` / `CHECKED: 2` |

- **B3의 자기매칭 해법** (V1 D-4 — 초판은 이 함정을 인식조차 하지 않았다): 검사 문자열을 스크립트에 리터럴로 두면 **검사기 자신이 매칭돼 상시 FAIL**한다. 이 저장소가 이미 승인한 두 해법 중 **①을 쓴다** — 패턴을 커밋된 외부 파일 `.foreign-repo-patterns`로 분리한다(선례: `.check-weakening-patterns:2` *"이 패턴들을 훅 소스에 literal로 두면 훅 자신이 자기 매칭에 걸리므로 분리한다"*). **파일명 자기 면제는 금지**(`acceptance-0-6.sh:17` — E1 사고 재현). 패턴 파일 자신은 스캔 대상에서 빠지는 대신 *"패턴·주석 줄만 있고 실행 코드가 없는가"*를 별도로 검사한다(`verify.yml`의 `.secret-patterns.default` 자기오염 스텝과 동형).
- **B3의 범위**: 초판의 열거식 허용목록(`src/`·`contracts/`·…)을 **폐기**한다 — 계획 자신이 §4에서 *"열거는 항상 샌다"*고 적고 AC-B3에서 그것을 위반했고, 실제로 `.claude/skills/verify/local-checks.sh`·`suppressions.yaml`·`verify.sh` 등이 범위 밖이었다. **추적 파일 전체 − `docs/engineering/`** 로 반전한다. 그 제외의 정당성은 실측으로 확인됐다 — 해당 문자열 13건이 **전부** `docs/engineering/`(사건 기록, 날짜 필수·불변)에 있고 실행 경로에 0건이다. 선례도 있다(`acceptance-0-6.sh:19`가 같은 제외를 쓴다).
- **HOST 인수**: 채널 1개(사람인 권장 — 좌석 제약이 가장 약함) 라이브 캡처 1건 → 영수증 1건(§4-3 3겹 통과).
- **산출물**: `tools/live_capture.py`(read-only: 새 탭 0·입력 0·클릭 0) · `contracts/*/selectors.json`(전부 `hypothesis`로 시작) · `.foreign-repo-patterns` · 인수 스크립트 3개
- **비범위**: 필터 입력·수집·채점.

### Phase 0 — 골격: 스키마 · 설정 · 경계 함수 (창립 스펙 §5·§6)

| AC | EARS 단언 | 검증 명령 | 기대 출력 |
|---|---|---|---|
| **0** | *If 증거 행(`evidence`)이 없는 후보를 `registrations`에 넣으려 하면, then **DB 제약**이 거부해야 한다* | `bash scripts/acceptance-hs-0.sh` | `PASS: 위반 INSERT 4종 전부 거부` · `PASS: 속성기반 3함수 통과` / `CHECKED: 7` |

- 함께 **테스트로** 고정(주석 아님): 경력 **회사 단위 groupby** 후 `job_changes = unique_companies - 1`(승진≠이직) · `profile_url`은 수확 JSON의 `url` 문자 그대로(손입력 차단 + 등록 직전 문자열 대조 1회) · 문턱은 `config/humansearch.json` **1곳**에서 읽고 **러너가 그 파일에서 읽었음을 단언**(v5는 설정에 70이 있는데 러너가 리터럴을 썼다) · `eligible()`은 **1개**
- **속성 기반 테스트(P5) 필수 3함수**: `score` 총점 계산 · `eligible` · `build_company_tenures`
- **counter-AC**: 앱 코드로만 막고 DB 제약이 없으면 가짜 — **DB에 직접 위반 INSERT를 시도**해 거부되는지로 검증한다
- **롤백**: forward-only 마이그레이션 + `schema_version`. N-1 릴리스가 현재 스키마를 읽을 수 있음을 검사(P7)

### Phase 1 — 로그인 (창립 스펙 §3, RC1~RC13)

| AC | EARS 단언 | 검증 명령 | 기대 출력 |
|---|---|---|---|
| **1** | *If 채널 영수증이 `AUTHENTICATED`가 아니거나 1800초를 넘었거나 **증거 SHA 재계산·실질성·외부 앵커 중 하나라도 실패**하면, then 시스템은 순회를 시작하지 않고 STOP하며 알림을 **1건만** 남겨야 한다* | `bash scripts/acceptance-hs-1.sh` | `PASS: 위조 영수증 6종 전부 거부(0바이트·임의hex·꼬리위조·전량재생성·미래시각·앵커불일치)` · `PASS: 라이브 영수증 1건 유효` / `CHECKED: 8` |
| **1-안전** | *If 보안 챌린지(캡차·2FA·인증번호·checkpoint·authwall)가 탐지되면, then 시스템은 같은 URL 재네비게이션을 **0회** 수행해야 한다* | 같은 스크립트 | `PASS: challenge 후 navigation 이벤트 0건(run_log)` |
| **1-단일창** ([4]) | *If `launch()`·`launch_persistent_context()`·새 탭/새 창 생성 호출이 소스에 존재하면, then CI는 실패해야 한다. 그리고 라이브 실행 전후 target 수가 동일해야 한다* | 같은 스크립트 | `PASS: launch 계열 grep 0건` · `PASS: target 수 전후 동일(N→N)` |
| **1-전면화** ([3]) | *When 사람이 봐야 하는 순간(로그인·캡차·2FA)이 오면, then `Page.bringToFront`로 실제 전면화하고 성공 여부를 `run_log`에 남겨야 한다* | 같은 스크립트 | `PASS: bringToFront 이벤트 기록됨` |
| **1-불살생** ([7]) | *While 작업이 종료되면, 시스템은 WebSocket만 해제하고 `context.close()`·`browser.close()`·`page.close()`·kill·restart를 **0회** 수행해야 한다* | 같은 스크립트 | `PASS: 드라이버 export에 원시 타입 없음` · `PASS: hasattr(driver,'close') is False` |
| **1-마커** ([8]) | *If 인증 마커 집합과 라이브 픽스처 속성의 **교집합이 비면**, then 판정은 FAIL이며 "미로그인"으로 단정해서는 안 된다* | 같은 스크립트 | `PASS: 교집합 공집합 시 FAIL 반환` |

- 함께: CDP 포트 **조회**(하드코딩 금지 — 실제로 9338이었던 사고) · 생존 판정 = target 존재 + `/json/version` 200 · 로그인 판정은 **URL 금지, header/nav의 보이는 컨트롤만** · 좌석 lease(atomic mkdir + heartbeat, own-token만 반납) · Keychain 단일 출처(`.env.local`은 import 전용) · **비밀번호 회전을 요구하지 않는다**(2026-08-04 사장님 결정)
- **counter-AC**: 빈 파일 3개 + 임의 64자 hex(v5 main의 실제 구멍 — 그리고 **초판 설계도 여기서 뚫렸다**) · 잡코리아 2FA FAQ 문구만 보고 `HUMAN_AUTH` 오판 · 검색 결과가 보이니 로그인됐다고 판정(로그아웃 상태에서도 카드 100장은 보인다)
- **영향 반경**: 3사 계정 잠금·좌석 충돌. 그래서 재시도 0회·terminal 처리·fail-closed가 데이터 안전 AC다.

### Phase 2 — 순회 + 증거 (창립 스펙 §4·§2-4)

| AC | EARS 단언 | 검증 명령 | 기대 출력 |
|---|---|---|---|
| **2-완주** ([1] **9회·최다**) | *While 순회가 시작되면, 시스템은 `min_pages`(20) 이상을 방문하거나, 그보다 적게 끝나면 `runs.abort_reason`에 사유를 기록해야 하며, **사유 없는 종료를 성공으로 기록해서는 안 된다**. 상세를 열지 않고 링크만 저장된 후보는 0건이어야 한다* | `bash scripts/acceptance-hs-2.sh` | `PASS: abort_reason NULL 이면서 status=completed 인 run 0건` · `PASS: evidence(page_type='detail') 없는 candidate 0건` |
| **2-필터** ([9]) | *While 순회 중, 요청 필터가 화면의 **활성 조건 칩으로** 전부 증명되지 않으면 수집을 중단해야 한다* | 같은 스크립트 | `PASS: 칩 미증명 시 수집 0건` |
| **2-영건** ([13]) | *If 결과 건수 표시가 N>0인데 수집 카드가 0개면, then 시스템은 STOP하고 `preflight_fail`을 기록해야 한다* | 같은 스크립트 | `PASS: 카드 0 + 건수>0 → preflight_fail 기록` |
| **2-페이싱** ([10]) | *While 순회 중, 요청 간격은 설정의 지터 범위에서 **결정론으로** 산출되며 같은 `run_id`는 같은 타이밍 열을 재현해야 한다. 고정 간격 리터럴은 금지한다* | 같은 스크립트 | `PASS: 같은 run_id 2회 실행 타이밍 열 동일` · `PASS: 간격 리터럴 grep 0건` |
| **2-양보재개** ([11]) | *While 크롬 활성 탭이 3사 도메인이고 사장님 조작이 감지되면, 시스템은 즉시 양보하고, OS idle이 60초를 넘으면 **작업 목록을 유지한 채** 재개해야 한다* | 같은 스크립트 | `PASS: 양보→재개 왕복 후 backlog 길이 보존` |
| **2-진행표시** ([12]) | *While 자동화가 화면을 쓰는 중이면, 배지를 주입한 뒤 **스크린샷 픽셀 색 + 히트테스트로 실제 렌더를 증명**하고 실패 시 fail-closed해야 한다* | 같은 스크립트 | `PASS: 렌더 증명 실패 시 fail-closed` |

- 함께: 새 검색 전 `reset_filters` · 수집 직전 `bringToFront`+focus emulation · 가상 스크롤 완료 증명(occluded 0 AND unique≥itemCount, 못 채우면 fail-closed) · `readyState`를 렌더 완료로 믿지 않는 유계 재시도(10회×1.5초) · 상세 완료 판정 4조건(2000자 AND 식별자 일치 AND 필수항목 AND 로딩 인디케이터 부재) · 같은 URL 연속 2회 금지 · **`min_pages`(하한)와 MAX_PAGES(절대 상한)의 이름 분리** · 열람 순서 triage 4단(컷은 Non-OTW & 현 회사 24개월 미만 → 버리지 않고 `triage_deferred`)
- **HOST 인수**: 라이브 1건 순회로 `candidates`+`evidence` N건.

### Phase 3 — 채점 + 게이트 (창립 스펙 §6)

| AC | EARS 단언 | 검증 명령 | 기대 출력 |
|---|---|---|---|
| **3** | *If LLM 출력에 총점이 포함되면, then 시스템은 그것을 무시하고 **순수 함수 계산값만** `scores.total`에 기록해야 한다* | `bash scripts/acceptance-hs-3.sh` | `PASS: LLM total 주입 시에도 DB total == 재계산값` |
| **3-폴백금지** | *If 평가 클라이언트를 사용할 수 없으면, then 시스템은 **실패해야 한다** — 레거시 축으로 폴백해서는 안 된다* | 같은 스크립트 | `PASS: 클라이언트 부재 시 exit 1, scores 행 0건` |
| **3-경계** | *While 등록 경로가 여러 개여도, `registrations`에 도달하는 모든 후보는 `eligible()` **한 함수**를 통과한 것이어야 한다* | 같은 스크립트 | `PASS: 합격선 미달 registrations 도달 0회(호출 카운트)` |

- 함께: D1~D8 가중치(27/10/14/9/7/10/14/9=100) 설정 1곳 · 합격선 70과 게이트 캡(필수요건 fail→최대 49, uncertain 2개+→최대 69) 한 세트 · 하드제외(프리랜서 · 12개월 미만 단기이직 2회+ · 전문대는 사람인·잡코리아만, **링크드인 학교 하드컷 없음**) · `sub_reasons` 없으면 등록 거부 · 문턱을 파이프라인 간에 섞지 않는다(humansearch 70 / 다른 파이프라인 60·85는 의도된 차이)

### Phase 4 — 등록 어댑터

| AC | EARS 단언 | 검증 명령 | 기대 출력 |
|---|---|---|---|
| **4** | *While 모든 등록 어댑터가 비활성이면, 시스템은 Phase 0~3을 그대로 완주해야 한다* | `bash scripts/acceptance-hs-4.sh` | `PASS: 어댑터 0개 상태에서 파이프라인 완주` · `PASS: Send 클릭 경로 grep 0건` / `CHECKED: 2` |

- **Phase 4는 선택 사항이 아니다.** 초판은 "(선택적)"으로 표시했는데, 완료 정의에 선택항이 있으면 "완료"가 협상 가능해진다(V1 D-8 부수). 어댑터의 *기능*은 선택이지만 **"어댑터를 다 꺼도 완주한다"는 인수 기준은 필수**다.
- **불변식**: 발송(제안·InMail·메일) **Send 클릭 0회**.

### 6-Z. 사고 14유형 → 전용 AC 전수 매핑

창립 스펙 §1은 *"v6는 이 14개 유형을 코드로 못 나게 막아야 완료다"*라고 못 박았다. **초판은 전용 AC를 2개 유형([2]·[9])에만 붙여놓고 "[12]·[14] 2건만 미매핑"이라 적었다 — 축소 보고였다.** V1이 실제 미매핑 8건을 열거했고(§3 전수표), 그중 [3]·[7]·[11]·[12]는 V1 보고 전 자체 반증에서, [1]·[4]·[10]·[8]·[13]은 V1 지적으로 AC를 신설했다.

| 유형 | 횟수 | 전용 AC | 상태 |
|---|---|---|---|
| [1] 중도 이탈·얕은 수집 | **9(최다)** | **AC-2-완주** | 덮음 |
| [2] 로그인 미수행 | 8 | AC-1 | 덮음 |
| [3] 창 전면화 안 함 | 5 | **AC-1-전면화** | 덮음 |
| [4] AI 창 ≠ 사장님 창 | 5 | **AC-1-단일창** | 덮음 |
| [5] 자격증명 취급 | 5 | AC-1(Keychain) + §8 PII AC | 덮음 |
| [6] 거짓 완료 보고 | 4 | AC-1(영수증 위조 6종 거부) — **초판 설계는 여기서 뚫렸고 §4-3으로 보강했으나 완전하지 않다(§10)** | 부분 |
| [7] 창·탭이 죽음 | 4 | **AC-1-불살생** + §3-A 소유권 규칙 | 덮음 |
| [8] 로그인 상태 오판 | 4 | **AC-1-마커** | 덮음 |
| [9] 필터·검색어 오사용 | 4 | AC-2-필터 (검색어 *생성/입력*은 창립 스펙 §0 scope out — aisearch의 일) | 덮음(경계 명시) |
| [10] 봇처럼 굴어 차단 | 3 | **AC-2-페이싱** | 덮음 |
| [11] 개입 시 양보·재개 안 됨 | 3 | **AC-2-양보재개** + §3-A 재승격 전이 계약 | 덮음 |
| [12] 진행 표시 부재 | 3 | **AC-2-진행표시** | 덮음 |
| [13] 결과 0건인데 진행 | 2 | **AC-2-영건** | 덮음 |
| [14] 서치 범위 축소 해석 | 1 | **없음** — `RunRequest.search_url` 화이트리스트(§5-1)로 **부분** 대응만 | **미해결** |

---

## §7. SOT 체크리스트 · 드리프트

| SOT | 이 계획이 하는 일 |
|---|---|
| `docs/sot/coding-principles.md` | 수정 없음. P1~P22를 **적용**한다 |
| `docs/sot/verification-commands.md` | **Phase A에서 수정** — 게이트 4 표에 `pytest`·`ruff`·`mypy`와 신설 인수 스크립트가 들어간다. 같은 PR에 SOT diff 동봉(P13) |
| `docs/sot/hook-contracts.md` | **Phase A에서 수정** — `pre-push`에 "글로브 전량의 CI 등록 검사"가 추가되므로 계약 갱신 |
| `docs/sot/git-workflow.md` | 수정 없음 |
| `suppressions.yaml` | **Phase A에서 갱신** — `ci-transfer-guarantee`(A1이 그 패턴을 재사용한다) · `acceptance-0-2`(2026-08-21 만료가 Phase 기간과 겹친다) |
| 창립 스펙(불변) | §9 Phase 순서와 이 문서 §6의 차이(선행 A·B 추가, 이식 경로 삭제)는 이 문서가 근거와 함께 덮어쓴다 |

---

## §8. 롤백 · 영향 반경

- **롤백 단위 = Phase = PR 1개.** `git revert <merge sha>` 한 번. Phase A만 게이트 자체를 건드리므로, revert 시 `scripts/acceptance-0-7.sh`(훅 위반 6종 시연)로 이전 상태 복귀를 확인한다.
- **DB**: forward-only + `schema_version`. 롤백 보장은 "N-1이 현재 스키마를 읽을 수 있음"(P7). 파괴적 마이그레이션 금지.
- **영향 반경**: ① 3사 계정(잠금 — AC-1-안전) ② 사장님 크롬 세션(닫지 않음 · 새 탭 0 · 즉시 양보 · **재개는 반드시 살린다**) ③ 후보자 PII(`candidates`·`evidence`).
- **PII 데이터 안전 AC**: *If 후보자 개인정보를 담은 파일이 git 추적 대상이 되려 하면, then `pre-commit`이 차단해야 한다.* (DB·`artifacts/`·`fixtures/` 원본은 gitignore + 1MB 초과 데이터 차단, P21) ⚠️ **얇다** — 파일 권한·디스크 암호화·백업 경로 요구가 없다(V1 E-3). L3 데이터 안전으로는 Phase 0에서 보강해야 하며, 이번 계획에서는 미결로 남긴다.

---

## §9. 재검증 시 반드시 통과해야 할 것 (V1 §6이 지정한 6개)

1. **D-1**: 0바이트 증거 3개 + 실제 HEAD SHA + 러너 재실행 5건 체인이 **거부**되는가. 거부 사유가 "체인"이 아니라 **"실질성 미달"** 또는 **"외부 앵커 부재/불일치"**여야 한다.
2. **D-2**: 신규 `scripts/acceptance-hs-*.sh`가 CI **실행 줄**(`bash -n` 아님)에 없으면 push가 차단되는가.
3. **D-6**: 인수 스크립트 종료코드 0·1·2 각각에 대해 pre-push·CI 판정이 §5-4대로 나오는가(특례 0건).
4. **D-7**: `bash scripts/session-status.sh`의 RED 카운트가 크롬 부재 상태에서 **오염되지 않는가**(라이브 실행 파일이 글로브에 없으므로 오염되지 않아야 한다).
5. **D-4**: `scripts/acceptance-hs-b3.sh`가 자기 리터럴에 매칭되지 않으면서 대상 검출력이 동일함을 증명하는가.
6. **§6-Z**: 14유형 중 [14]를 제외한 13개에 전용 AC가 붙었는가.

---

## §10. 비범위 / 한계 (정직하게)

- **이번 산출물은 문서 2개뿐이다**(이 계획 + V1 판정서). 코드 0줄, 인수 스크립트 0개.
- **영수증 위조를 완전히 막지 못한다.** §4-3의 3겹은 ① 0바이트·가짜 증거와 ② **과거 시각 소급 위조**를 막지만, **러너를 실행할 수 있는 주체가 지금 시각의 영수증을 만드는 것**은 막지 못한다. P17 완전 충족에는 러너 전용 권한 분리가 필요하고 별도 이슈다. **초판이 이것을 "P17 충족"이라 적은 것은 참칭이었다.**
- **AC-B3은 대리지표다.** 경로 문자열만 탐지하므로, v5 코드를 복붙하고 경로 문자열을 지우면 0건을 보고한다. "타 저장소 **의존성** 없음"의 본지표(코드 유래)는 기계로 잡을 방법을 찾지 못했다. 실질 방어는 **셀렉터를 라이브 캡처로만 승격시키는 Phase B 루프**이며, 그것이 이 지시의 진짜 이행 수단이다.
- **HOST 계층 인수는 오늘 실행할 수 없다** — 지금 CDP 디버그 포트를 LISTEN하는 크롬이 0개다. 라이브 인수는 **사장님이 디버그 프로필 크롬을 띄운 시점**에만 진행 가능하다. 일정은 이 외부 의존성을 분리해서 잡아야 한다.
- **사고 14유형 중 [14](서치 범위 축소 해석) 1건 미해결.** URL 화이트리스트로 부분만 덮인다.
- **PII 안전 AC가 얇다**(§8). Phase 0에서 보강 필요.
- **`suppressions.yaml`의 만료 3건**(2026-08-21 · 2026-09-15 ×2)이 Phase 기간과 겹친다. 특히 `ci-transfer-guarantee`는 **A1이 재사용하는 패턴이 이미 4종 우회로 뚫려 있다는 원장**이다 — A1은 그것을 해소하지 않는다.
- **작업량·세션 수 견적은 내지 않는다.** 창립 스펙의 15세션·32,850 LOC는 산식 없는 추정치로 이미 폐기됐다.
- **probe 커밋 `6538bac`는 unreachable 객체로 남아 있다**(워크트리·브랜치는 제거). 이것이 `acceptance-0-2`(unreachable==0)를 빨간불로 유지하는 조건 중 하나다 — "폐기 완료"가 객체 회수까지 뜻하지 않음을 명시한다(V1 E-2).

---

## §11. 적대 검증 로그

### V1 — codex 계열 별도 세션 (2026-08-08) · **VERDICT: FAIL** · 결함 10건

- **판정 원문**: `docs/engineering/humansearch-plan-v1-verdict-2026-08-08.md` (446줄, verbatim 사본. 원 산출 위치가 세션 임시폴더라 비영속이므로 저장소로 옮겨 커밋했다)
- **검증 대상**: 이 문서의 **초판(334줄)**. 실행 위생: 검증 시작·종료 모두 `HEAD=ec201dc`, 추적 파일 수정 0건, 임시 워크트리 폐기 확인
- **V1이 깨뜨리려 했으나 실패한 것(계획이 버틴 항목)**: §1 사실표 9개 전량 재현 → 과장 0건 / §2-A 재현 명령 그대로 실행 → pre-push 차단은 참 / **mypy --strict가 5조-5·스펙 §2-6을 실제로 잡음 → 런타임 결정은 SOT 위반 아님** / `docs/engineering/` 제외는 선례가 있는 정당한 범위 한정

### V2 — Claude 재현 (2026-08-08) · V1 증거를 **내가 새로 짠 코드로** 직접 돌렸다

| V1 결함 | 내 재현 결과 | 판정 |
|---|---|---|
| **D-1** 영수증 4장치가 라이브 0회·0바이트로 통과 | 독립 재현 성공. `0바이트 SHA = e3b0c442…b855` 를 정직하게 기록 → SHA 재계산 일치 → PASS / **꼬리 줄 위조 직후에도 PASS, 위조 후 정상 append하면 체인이 "다시" 온전해짐** / 크롬 LISTEN 0건 | **일치 — 수용.** §4-3 전면 재작성 |
| **D-2** 신규 인수 스크립트가 CI 미실행 | `verify.yml` grep → 고정 이름 3개(`0-6`·`0-7`·`0-5`)만, 글로브 0건 | **일치 — 수용.** §0-2·§2-A 재작성, AC-A1 신설 |
| **D-3** "라이브는 원리적으로 막힌다"는 과장 | 확인. 내 초판 문장은 **CI가 실행조차 않으므로 FAIL도 나지 않는다**는 점에서 자기모순이었다 | **일치 — 문장 철회** |
| **D-4** B3 검사기 자기매칭 | `.check-weakening-patterns:2`·`acceptance-0-6.sh:16-18` 두 선례 확인 | **일치 — 수용.** 외부 패턴 파일로 분리 |
| **D-5** 원시 참조 에일리어싱 | 논리 확인(래퍼가 아닌 원시 객체는 어떤 타입 검사도 안 지난다). TS로도 안 닫힘 | **일치 — 수용.** §3-A 소유권 규칙 신설 |
| **D-6** §4-3 세 규칙 모순 + 비동형 | 확인. HOST-ONLY 마커 **폐기**로 해소 | **일치 — 설계 교체** |
| **D-7** RED 원장 상시 오염 | 확인(`session-status.sh:63`이 0 아닌 종료코드 전부 RED). 마커 폐기로 소멸 | **일치 — 해소** |
| **D-8** AC 11개 중 검증 명령 1개·기대 출력 0개 | 확인 | **일치 — 수용.** §6 전 AC에 명령·기대 출력 부여 |
| **D-9** counter-AC 4건이 자기 AC로 안 잡힘 | 확인 | **일치 — 수용.** 전용 AC 신설로 해소 |
| **§3 전수표** 실제 미매핑 8건 | **부분 불일치**: V1이 읽은 판본은 **초판 334줄**이고, 그 시점 이후 내가 자체 반증으로 [3]·[7]·[11]·[12] 4건의 AC를 이미 신설했다(현 파일 350줄). 다만 [1]·[4]·[10]이 전용 AC 없이 산문/counter-AC로만 있었다는 지적은 **정확하며 더 무겁다** — 최다 유형 [1](9회)에 기계 장치가 없었다 | **대부분 일치 — 수용.** 판본 차이는 표기 |
| **E-2** "폐기 완료" 표현 부정확 | 확인 — probe 커밋은 unreachable 객체로 잔존 | **일치 — §10에 명시** |

**뒤집힌 것 (양방향 의심 결과)**: ① **V1이 내 과장을 잡은 것 3건** — "라이브 CI 영구 FAIL"(D-3), "P17 충족"(D-1), "PUSH-PERFORMING과 동형"(D-6). ② **내가 V1에서 잡은 것 1건** — V1의 §3 전수표는 내 수정 이전 판본을 대상으로 해 [3]·[7]·[11]·[12] 4건을 미매핑으로 셌으나 그 시점 이미 AC가 있었다(판본 차이). ③ **V1이 내 과소평가를 교정한 것 1건** — Python 런타임의 타입 강제력을 내가 낮게 봤고, mypy 실증으로 "SOT 위반 아님"이 확인됐다.

**최종 상태**: V1 결함 10건 전부 반영. **G·V1·V2가 T(계약·AC·SOT) 기준에서 갈리는 항목은 없다.** 단 §10의 한계 6건은 미해결로 남아 있고, 그중 **영수증 위조(현재 시각)** 와 **[14] 서치 범위 축소**는 다음 Phase에서도 닫히지 않는다.
