> **고정 메타데이터** (2026-08-08)
> - **역할**: /strict §5 V1(1차 적대검증) 판정서. 검증 대상은 `docs/engineering/humansearch-v6-implementation-plan-2026-08-08.md` 의 **초판(334줄)**이다.
> - **검증자**: codex 계열 별도 세션(에이전트명 `V1-codex`), 구현 컨텍스트와 격리. 산출물 + 채점 기준표(SOT·창립 스펙)만 전달.
> - **본문**: 아래는 검증자가 파일로 쓴 판정 원문의 verbatim 사본이다(원 산출 위치는 세션 임시폴더라 비영속이므로 여기로 옮겨 커밋한다 — 요지 요약만 남기고 본문을 버리지 않는다).
> - **저장소 상태**: 검증 시작·종료 모두 HEAD `ec201dc`, 추적 파일 수정 0건.
> - **V2(Claude 재현) 결과**: 계획 문서 §11 에 표로 있다. 판정이 뒤집힌 항목도 거기에 공개했다.

---

# V1 적대검증 판정 — humansearch v6 구현 계획 (2026-08-08)

**VERDICT: FAIL**

- 검증 대상: `docs/engineering/humansearch-v6-implementation-plan-2026-08-08.md` (334줄, 미추적)
- 저장소 HEAD: `ec201dc` (검증 시작·종료 동일, 추적 파일 무수정)
- 판정자: V1 (Claude Opus 5, 별도 컨텍스트)
- 산출 위치: `private-reviews/` 는 `.gitignore` 대상이 **아니다**(`.gitignore:22` 는 `.claude/private-reviews/` 만 무시). 그래서 저장소에 만들지 않고 scratchpad 에 썼다.

**FAIL 근거 요약**: 계획의 핵심 방어선인 §4-2 영수증 4개 장치를 **계획 문구 그대로 구현한 뒤, 라이브 실행 0회·크롬 0개·증거 파일 전부 0바이트로 4개 장치 전부를 통과시켰다**(D-1). 이것은 계획이 막겠다고 명시한 바로 그 시나리오(§6 AC-1 counter-AC ①)다. 추가로 Phase A 의 첫 인수 스크립트가 CI 에 등록되지 않아 P15③("로컬에만 있는 검사는 없는 것으로 친다")을 위반하는 구조를 확인했다(D-2).

---

## §0. 반증 시도 기록 — 깨뜨리려 했으나 실패한 것 (PASS 판정 근거)

단순 동의는 무효이므로, 먼저 **내가 공격했으나 계획이 버틴 항목**을 적는다.

### R-1. §1 사실표 9개 전량 재현 → 전부 참. 과장 0건

| 계획 주장 | 내 재실행 결과 | 판정 |
|---|---|---|
| §1-1 추적 파일 46개 | `git ls-files \| wc -l` → 46 | 참 |
| §1-2 `make -n red-ledger` 실패 | `make: *** No rule to make target 'red-ledger'` | 참 |
| §1-3 RED 원장은 bash 글로브 | `scripts/session-status.sh:46-48` 확인 | 참 |
| §1-4 RED = 1/4 | `bash scripts/session-status.sh` → `RED: 1/4 (acceptance-0-7.sh 제외 — CI 담당)` | 참 |
| §1-5·1-6 pre-push 차단 | 아래 R-2 | 참 |
| §1-7 런타임 | `Python 3.14.1` · `uv 0.11.3` · `node v22.19.0` | 참 |
| §1-8 CDP LISTEN 0건 | `lsof -nP -iTCP -sTCP:LISTEN \| grep -icE 'chrome\|922[0-9]'` → 0 | 참 |
| §1-9 억제 4건, 최단 만료 2026-08-21 | `suppressions.yaml:19,37,49,61` | 참 |

**§1 은 "실행 확인, 추측 0" 이라는 자기선언을 실제로 지켰다.** 이 저장소의 이전 사고 유형(문서가 실측을 참칭)이 여기서는 재현되지 않았다.

### R-2. §2-A 재현 명령을 그대로 돌려 깨뜨리려 했으나 실패 — 주장은 참이다

계획 §2-A 의 재현 명령(§46-54줄)을 내 워크트리에서 독립 실행했다.

```
$ git worktree add …/wt-v1probe -b probe/v1-red-push
$ printf '#!/usr/bin/env bash\nexit 1\n' > scripts/acceptance-v1probe.sh && chmod +x …
$ git add -A && git -c core.hooksPath=/dev/null commit --no-verify -m probe   # db426d5
$ bash hooks/pre-push origin https://example.invalid </dev/null; echo "exit=$?"
  skip ./scripts/acceptance-0-2.sh (DEFERRED · CI 담당)
  skip ./scripts/acceptance-0-5.sh (DEFERRED · CI 담당)
  skip ./scripts/acceptance-0-7.sh (PUSH-PERFORMING · CI 담당)
pre-push: 검사 3개 실행
  ok  ./scripts/acceptance-0-6.sh
BLOCKED: ./scripts/acceptance-v1probe.sh exit=1
  ok  ./verify.sh
exit=1
```

**§1-5·§1-6 은 참이다.** 글로브가 신규 스크립트를 자동 포함하고, 하나라도 실패하면 exit 1 이다(`hooks/pre-push:112-113, 165-171`).

추가로 계획이 언급하지 않은 사실을 **계획에 유리한 방향으로** 확인했다 — `exit 2`(계획 §5-4 의 NOT_RUN)도 push 를 막는다:

```
$ printf '#!/usr/bin/env bash\n# HOST-ONLY\nexit 2\n' > scripts/acceptance-v1probe.sh   (커밋 후)
$ bash hooks/pre-push origin https://example.invalid </dev/null
BLOCKED: ./scripts/acceptance-v1probe.sh exit=2
pre-push exit=1
```

`hooks/pre-push:166` 이 `[ "$rc" -ne 0 ]` 이므로 2도 차단이다. 즉 **HOST-ONLY 스크립트가 라이브 부재 시 NOT_RUN 을 내면 push 가 영구 차단된다** — Phase A 가 필요하다는 계획의 결론 자체는 강화된다.

### R-3. §3 런타임 결정을 깨뜨리려 했으나 실패 — mypy --strict 로 SOT 충족 가능

정조준 항목 3은 "mypy 로 5조-5·창립 스펙 §2-6 을 충족 못 하면 SOT 위반"이었다. 실제로 mypy 를 돌려 반증을 시도했고 **실패했다** — mypy 가 두 조항을 모두 잡는다.

```python
# drv.py (요약)
class LiveDriver(Protocol):            # close() 를 아예 노출하지 않는다 (창립 스펙 §2-6)
    def navigate(self, url: str) -> None: ...
    def screenshot(self) -> bytes: ...
class Yielded: __slots__ = ()          # 개입 이후: 조작 메서드 0개
def detect_intervention(d: LiveDriver) -> "LiveDriver | Yielded": ...
def collect(d: LiveDriver) -> bytes: return d.screenshot()
def run(raw: RawCdp) -> None:
    d: LiveDriver = raw
    d.close()                          # ①
    collect(detect_intervention(d))    # ②
```
```
$ uv run --python 3.14 --with mypy mypy --strict drv.py
drv.py:31: error: "LiveDriver" has no attribute "close"  [attr-defined]        ← ① 잡힘
drv.py:33: error: Argument 1 to "collect" has incompatible type
           "LiveDriver | Yielded"; expected "LiveDriver"  [arg-type]           ← ② 잡힘
Found 3 errors in 1 file
```

**정조준 항목 3에 대한 판정: 계획 §3 은 SOT 위반이 아니다.** 계획이 스스로 "Python 열위"라고 적은 것은 오히려 과소평가다. 단, 아래 D-5 의 에일리어싱 구멍은 계획이 놓쳤고 그것은 TS 로 바꿔도 안 닫힌다.

### R-4. AC-B3 의 `docs/engineering/` 제외를 P13④ 위반으로 몰려 했으나 실패

정조준 항목 4를 P13④("검사기는 자기 자신을 검사 대상에서 제외할 수 없다") 위반으로 판정하려 했으나, **이 저장소에 동일 제외의 선례가 이미 승인돼 있다**:

```
scripts/acceptance-0-6.sh:19
  if git ls-files | xargs grep -lE "rating:[[:space:]]8\.5|…" 2>/dev/null | grep -v "docs/engineering/"; then
```

또한 그 제외가 **없으면 안 되는** 이유도 실측으로 확인됐다 — 검사 문자열이 실제로 사건 기록에만 있다:

```
$ git grep -nIE 'Valuehire_v5|aisearch-live-portal-wire|/Desktop/Valuehire_v' | awk -F: '{print $1}' | sort | uniq -c
   6 docs/engineering/humansearch-v6-founding-spec-2026-08-07.md
   3 docs/engineering/history-squash-goal-2026-08-07.md
   2 docs/engineering/history-squash-inventory-2026-08-07.txt
   1 docs/engineering/history-squash-v2-verdict-2026-08-07.md
   1 docs/engineering/ci-push-v2-verdict-2026-08-07.md
```

13건 전부 `docs/engineering/`. 실행 경로 0건. **제외는 정당한 범위 한정이고 P13④ 위반이 아니다.** (P13④ 의 실제 위반 위험은 다른 곳에 있다 → D-4)

### R-5. §10 의 "코드 0줄" 자기고백을 결함으로 몰려 했으나 실패

L2 문서 산출물로 자기 등급을 정확히 매기고(§4줄), 게이트 미이행을 §10 첫 줄에 스스로 적었다. `git status --porcelain` 은 이 문서 1개만 미추적으로 보고한다 — 추적 파일 무단 수정 0건. 정직하다.

---

## §1. 결함 — 재현된 것

### D-1 [치명] §4-2 영수증 4개 장치를 전부 통과시켰다. 라이브 0회 · 증거 0바이트

**대상**: `docs/engineering/humansearch-v6-implementation-plan-2026-08-08.md:107-110`(4개 장치), `:239`(AC-1), `:242`(counter-AC ①), `:291`(계획자 자신의 정조준 항목 2)

계획 문구를 그대로 코드화했다(러너 = §4-2③ "러너 코드만 쓴다", 검증기 = §5-2 계약 + §4-2 장치 1·2·4). 그리고 세 가지 공격을 했다.

**공격 1 — 빈 파일 3개를 증거로 등록** (계획 §6 AC-1 counter-AC ① 그대로: *"빈 파일 3개 + 임의 64자 hex 로 영수증 검증 통과(v5 main 의 실제 구멍)"*)

```
$ : > artifacts/nav.png; : > artifacts/header.png; : > artifacts/body.html   # 전부 0바이트
$ python3 runner.py saramin artifacts/{nav.png,header.png,body.html} <sha> <now>
$ python3 validator.py
PASS: 영수증 1건 · 체인 온전 · SHA 재계산 일치
validator exit=0
```

계획은 이 counter-AC 의 **절반만** 막았다. `임의 64자 hex` 는 §5-2 의 "SHA 를 파일에서 실제로 재계산해 대조"(`:152`)로 막힌다. 그런데 **`빈 파일 3개` 는 안 막힌다** — 0바이트 파일의 SHA(`e3b0c44298fc…b855`)를 정직하게 기록하면 재계산이 정확히 일치한다. §5-2 는 `"bytes":12345` 필드를 두었지만 **`bytes > 0` 도, PNG 매직바이트도, 화면 내용 단언도 어떤 AC 에도 없다.**

**공격 2 — 체인 마지막 줄을 손으로 고친 뒤 정상 append** (계획 §4-2① *"한 줄을 사후 조작하면 이후 전부가 깨진다"*)

```
$ python3 -c "…마지막 줄의 mutation_count 를 0→99 로 변경…"
$ python3 runner.py saramin …            # 러너로 정상 append (prev 를 현재 파일에서 재계산)
$ python3 validator.py
PASS: 영수증 2건 · 체인 온전 · SHA 재계산 일치
exit=0    ← 기대는 1 이었다
```

**§4-2① 의 주장은 거짓이다.** append-only 해시체인은 **후속 레코드가 이미 존재하는 줄**만 보호한다. 꼬리 레코드는 항상 위조 가능하고, 위조 후 append 하면 새 `prev` 가 위조된 줄로부터 계산되어 체인이 다시 온전해진다. "이후 전부가 깨진다"는 append 를 하지 않는 경우에만 성립한다.

**공격 3 — 러너로 체인 전량 재생성** (계획자 자신이 §9-2 에 적은 공격: *"러너가 곧 에이전트가 실행하는 코드라면, 체인 전체를 다시 만들면 되지 않는가"*)

```
$ rm -f receipts/index.jsonl
$ # 라이브 크롬 0개, 로그인 0회. 5일치 '라이브 로그' 를 러너 API 로 생성.
$ REAL=$(git rev-parse HEAD)   # ec201dc… — 실제 도달 가능 커밋을 쓴다(장치 2 를 공정하게 만족)
$ for d in 5 4 3 2 1: python3 runner.py saramin <0바이트 3개> $REAL <now - d days>
영수증 5건 생성 (라이브 실행 0회)

$ # 장치 2: code_commit 도달성
장치2(코드 SHA 도달성): PASS
$ # 장치 1·3·4
PASS: 영수증 5건 · 체인 온전 · SHA 재계산 일치
장치1·3·4 exit=0

$ lsof -nP -iTCP -sTCP:LISTEN | grep -icE 'chrome|922[0-9]'
LISTEN 프로세스: 0건
```

**4개 장치 전부 통과. 라이브 로그인 0회. 증거 파일 전부 0바이트. 크롬 프로세스 0개.**

**판정 — 정조준 항목 2에 대한 답**: §4-2③ 의 제목 "쓰기 주체 분리(P17)" 는 **이름만 빌린 것**이다. P17 의 요구는 *"에이전트에게 그 경로의 쓰기 권한 자체를 주지 않는다"*(`docs/sot/coding-principles.md:32`)인데, 계획은 권한을 분리하지 않고 **해시체인 내부 일관성**으로 대체했다. 해시체인이 증명하는 것은 "이 파일이 러너 함수를 거쳐 만들어졌다"이고, 증명하지 못하는 것은 "라이브 사건이 실제로 일어났다"다. 에이전트가 러너를 실행할 수 있는 한 둘은 동치가 아니다.

§4-2 의 헤더 문구 *"위조를 **어렵게** 하는 4개 장치"* 는 정직하다. 그 아래 ③ 의 제목이 P17 충족을 참칭한 것이 결함이다. §10 에 "영수증 체인은 사후 단일 조작만 막고 러너 재실행 위조는 막지 못한다"가 없다.

**최소 수정 방향**(참고): 신선도 판정의 시각 근거를 에이전트가 못 만드는 것으로 바꿔야 한다 — 예: 영수증에 **외부 타임스탬프**(GitHub check-run id, TLS 서버 시각, 또는 러너가 CI 에 남긴 job-summary 마커)를 결박하고 CI 가 그 외부 객체를 조회한다. 이는 `suppressions.yaml:39-42`(`ci-transfer-guarantee`)가 이미 같은 결론에 도달한 방향("실행 증명으로 바꾼다")과 동일하다. 계획은 그 원장 항목을 회수하지 못했다.

### D-2 [치명] Phase A 의 인수 스크립트가 CI 에 등록되지 않는다 — P15③ 위반

**대상**: 계획 `:201`(게이트 표), `:206`(`bash scripts/acceptance-hs-a1.sh`), `:210`(Phase A 산출물 목록)

`hooks/pre-push:112` 는 **글로브**로 인수 스크립트를 찾지만, `.github/workflows/verify.yml` 은 **고정 스텝 목록**이다:

```
verify.yml 이 실행하는 것 (전량):
  :26  bash verify.sh
  :31  히스토리 전량 blob 스캔 (인라인)
  :66  bash scripts/acceptance-0-6.sh
  :79  bash scripts/acceptance-0-7.sh
  :84  bash scripts/acceptance-0-5.sh   (main 한정)
  :90  억제 만료 스캔 (인라인)
  :112 훅 존재 검사 (인라인)
  :123 셸 문법 검사 — git ls-files '*.sh' 에 bash -n. 실행이 아니다
  :131 패턴 파일 자기오염 (인라인)
```

즉 **신규 `scripts/acceptance-hs-*.sh` 는 CI 에서 한 줄도 실행되지 않는다.** `bash -n`(`:126`)만 걸리는데, `hooks/pre-push:87-88` 이 스스로 *"`bash -n <script>` 는 문법 검사일 뿐 실행하지 않는데 워크플로 diff 에서 정상 lint 스텝과 구분되지 않아 특히 위험하다"* 라고 적어둔 그 경로다.

Phase A 산출물 목록(`:210`)은 `.github/workflows/verify.yml` 에 **"스텝 3개 추가"** 라고만 적었고, 그 3개는 AC-A2 의 `ruff`·`mypy`·`pytest` 다. **`acceptance-hs-a1.sh` 를 CI 에 등록하라는 요구가 어느 AC 에도 없다.**

결과: P15③(`coding-principles.md:30`) *"같은 검사가 양쪽에 있어야 하며, **로컬에만 있는 검사는 없는 것으로 친다**"* 를 Phase A 가 자기 인수 기준에서 위반한다. 그리고 계획 `:201` 의 게이트 5("push·PR·CI 초록")를 통과해도 **CI 초록은 AC-A1 과 무관한 초록**이다 — 계획의 완료 정의가 첫 Phase 부터 위장 가능하다.

이 결함은 이후 모든 Phase 에 자동 전파된다(AC-A2·AC-B1~B3·AC-0~AC-4).

### D-3 [중대] §2-A 의 "라이브 인수는 영구히 막힌다"는 구조적 필연이 아니라 명명 규약이다 — 과장

**대상**: 계획 `:43-44`

계획은 두 주장을 한 문단에 섞었다. 정조준 항목 1이 요구한 대로 분리 판정한다.

| 계획 주장 | 판정 |
|---|---|
| `:42` "단일 PR 안에서는 문제가 없다" | **참** |
| `:43` "다단계 프로젝트에서는 막힌다 — 인수 스크립트를 미리 써 두면 전부 초록 전까지 push 불가" | **참이지만 자작 문제다.** 계획 스스로 §4-4(`:122`)에서 "1 Phase = 1 PR = 1 인수 스크립트"를 채택해 이 문제를 소멸시킨다. 즉 이 주장은 Phase A 의 필요 근거가 **아니다** |
| `:44` "라이브가 필요한 인수는 CI 에서 원리적으로 통과할 수 없다 → 영구 FAIL → merge 불가" | **과장.** 아래 실측 |

pre-push 의 차단 범위는 `find . -maxdepth 2 \( -name 'verify.sh' -o -name 'acceptance-*.sh' \)`(`hooks/pre-push:112`)다. 이름과 깊이를 벗어나면 차단되지 않는다:

```
$ mkdir -p host/live && printf '#!/usr/bin/env bash\nexit 1\n' > host/live/acceptance-live.sh   # depth 3
$ printf '#!/usr/bin/env bash\nexit 1\n' > scripts/live-login-check.sh                          # 이름 불일치
$ git add -A && git -c core.hooksPath=/dev/null commit --no-verify -m "probe: glob escape"
$ bash hooks/pre-push origin https://example.invalid </dev/null
pre-push: 검사 2개 실행
  ok  ./scripts/acceptance-0-6.sh
  ok  ./verify.sh
pre-push exit=0        ← 실패하는 스크립트 2개가 있는데 push 통과
```

**즉 §2-A 의 "원리적으로 막힌다"는 거짓이고, 실제로는 "`scripts/acceptance-*.sh` 라는 이름을 쓰기로 선택하면 막힌다"다.**

이 구분이 중요한 이유: 계획 §0-2(`:15`)는 이 과장 위에 **"선행 Phase A 가 Phase 0 보다 먼저다"** 라는 우선순위 결론을 세웠고, 그 결론이 창립 스펙 §9 의 Phase 순서를 덮어쓴다(`:275`). 근거가 "구조적 불가능"에서 "명명 규약"으로 약해지면, Phase A 를 선행할지 Phase 0 과 병합할지는 **다시 열린 판단**이 된다(정조준 항목 5의 답).

Phase A 를 선행할 실제 근거는 §2-A 가 쓴 것이 아니라 **"글로브 탈출 자체가 P15③ 위반이므로 탈출로를 쓰지 않겠다는 결정"** 이다. 계획은 그 문장을 쓰지 않았다.

### D-4 [중대] AC-B3 검사기가 자기 자신을 매칭한다 — 여기서 P13④ 가 실제로 위험하다

**대상**: 계획 `:217-218`

AC-B3 의 검사 문자열은 `Valuehire_v5` · `aisearch-live-portal-wire` · `/Desktop/Valuehire_v` 다(`:218`). 이 검사기는 `scripts/`(= AC-B3 의 검사 대상 범위 안)에 놓인다. **그러면 검사기 자신이 자기 리터럴에 매칭돼 상시 FAIL 한다.**

이 저장소는 이 함정을 이미 두 번 밟고 두 개의 해법을 승인했다:

1. `.check-weakening-patterns:2` — *"이 패턴들을 훅 소스에 literal 로 두면 훅 자신이 자기 매칭에 걸리므로 분리한다"* (외부 패턴 파일)
2. `scripts/acceptance-0-6.sh:16-18` — *"`[[:space:]]` 는 자기 매칭 방지용 … **파일명 자기 면제는 E1 사고 재현이라 금지**"* (패턴 조립)

**계획은 둘 중 어느 것도 언급하지 않았다.** 계획을 그대로 구현하면 구현자가 마주치는 가장 쉬운 탈출은 "검사기 파일을 제외 목록에 넣기"이고, 그것이 P13④ 정면 위반이자 `acceptance-0-6.sh:17` 이 명시적으로 금지한 "E1 사고 재현"이다.

**정조준 항목 4의 최종 판정**: `docs/engineering/` 제외는 정당하다(R-4). **P13④ 위반 위험은 검사기 자기매칭의 미해결에 있고, 계획은 그 위험을 인식조차 하지 않았다.**

부수 결함 두 개:

- **범위가 열거식 허용목록이다.** `src/`·`contracts/`·`config/`·`scripts/`·`hooks/`·`.github/`(`:217`). 계획 스스로 §4-2③(`:109`)에서 *"열거식 금지는 채택하지 않는다 — 열거는 항상 샌다"* 라고 원칙을 세웠는데 AC-B3 에서 그 원칙을 자기가 위반한다. 실제로 현재 저장소의 실행 경로 중 `.claude/skills/verify/local-checks.sh` · `.claude/settings.json` · `.check-weakening-patterns` · `.secret-patterns.default` · `suppressions.yaml` · `verify.sh`(루트) 가 전부 범위 밖이다. 그리고 **`suppressions.yaml:56-57` 이 이미 같은 경로 누락을 다른 게이트의 알려진 결함으로 기록해 두었다** — 계획이 회수(P12)하지 못한 원장 항목이다.
- **AC-B3 은 경로 문자열만 탐지한다.** 사장님 지시는 "타 레파지토리 **의존성**을 두지 말라"인데, v5 코드를 복붙하고 경로 문자열만 지우면 AC-B3 은 0건을 보고한다. `:217` 이 이 AC 를 **"사장님 지시의 기계 장치"** 로 명명한 것은 대리지표를 본지표로 참칭한 것이다. 계획 §10 에 이 한계가 없다.

### D-5 [중대] §3 typestate 의 에일리어싱 구멍 — 계획의 보완 2겹이 둘 다 못 잡는다

**대상**: 계획 `:86`(보완 2겹), `:84`

R-3 에서 mypy 가 두 SOT 조항을 잡는 것을 확인했다. 그런데 **원시 CDP 객체 참조가 같은 스코프에 살아 있으면 둘 다 무력하다**:

```python
# alias.py
def run(raw: RawCdp) -> None:
    d: LiveDriver = raw
    after = detect_intervention(d)   # 개입 신호 탐지됨
    del after
    raw.close()                      # 원시 참조로 직접 호출
    raw.navigate("https://x")        # 개입 이후에도 타입상 합법
```
```
$ uv run --python 3.14 --with mypy mypy --strict alias.py
drv.py:31,33: (drv.py 자신의 기존 오류 3건만)
alias.py: 오류 0건        ← raw.close() · raw.navigate() 통과
```

계획 §3 의 보완 ①(`mypy --strict`)도 ②(`hasattr(driver,'close')` 런타임 계약 테스트)도 이 경로를 못 잡는다 — ② 는 래퍼(`LiveDriver`)를 검사하고, 뚫리는 것은 래핑되지 않은 원시 객체다. **그리고 이 구멍은 TS 로 바꿔도 닫히지 않는다**(branded type 도 이전 변수 참조를 막지 않는다). 계획 `:84` 의 "TS 우위" 서술은 그 자체가 부정확하지만, 결정을 더 안전한 쪽으로 틀리게 했으므로 결정 자체는 유지 가능하다.

**빠진 요구**: 원시 CDP 객체가 **어디서도 이름에 바인딩되지 않아야 한다** — 팩토리가 원시 타입을 반환하지 않고, 소켓 소유권이 래퍼 안에만 있어야 한다. 계획 §3·§5 에 이 요구가 없다. 유형 [7](창·탭 죽음, 4회)과 [11](양보·재개, 3회)이 이 한 줄에 달려 있다.

### D-6 [중대] §4-3 의 세 규칙이 서로 모순이고, "PUSH-PERFORMING 과 동형"은 거짓이다

**대상**: 계획 `:114-118`

§4-3 은 세 규칙을 나란히 둔다:

| # | 계획 문구 | 문제 |
|---|---|---|
| ① `:116` | HOST-ONLY 스크립트는 "skip 되는 대신" 영수증이 존재·신선·온전하면 **통과** | 스크립트 종료코드와 무관 |
| ② `:117` | 마커만 있고 영수증 없으면 **차단** | ①과 일관 |
| ③ `:118` | HOST-ONLY 인데 "**초록으로 바뀌면** 차단한다 — 라이브 없이 통과하는 라이브 인수는 시뮬레이션이라는 증명(P4)" | ①과 정면 충돌 |

①은 통과 판정을 영수증에 위임하고, ③은 스크립트가 exit 0 이면 차단하라고 한다. 그러면 **HOST-ONLY 스크립트는 exit 0 을 낼 수 없고**, exit 1/2 는 R-2 에서 실측한 대로 `hooks/pre-push:166` 이 무조건 차단한다. 세 규칙을 동시에 만족시키는 종료코드가 존재하지 않는다 — 즉 §4-3 을 그대로 구현하면 pre-push 는 HOST-ONLY 스크립트의 종료코드를 **양방향 모두 무시**해야 하고, 그러면 그 인수 스크립트는 장식이 되고 유일한 게이트는 D-1 에서 뚫린 영수증뿐이다.

게다가 ③은 **기계가 판정할 수 없다**. pre-push 는 "라이브가 있었는데 통과"와 "라이브 없이 통과"를 구별할 수단이 없다. P4 의 기계 장치는 *"네트워크 차단 CI 레인에서 반드시 실패"*(`coding-principles.md:19`)인데, HOST 계층은 정의상 그 레인이 존재하지 않는 계층이다.

**"PUSH-PERFORMING 과 동형"(`:114`)은 거짓이다.** `hooks/pre-push:123-141` 의 검증 구조를 읽고 대조했다:

| | PUSH-PERFORMING (실재) | HOST-ONLY (계획) |
|---|---|---|
| 마커가 뜻하는 것 | "**다른 러너**(CI)로 옮겼다" | "**어떤 러너도** 돌릴 수 없다" |
| 검증하는 대상 | CI 워크플로의 **실행 줄에 그 경로가 있는가** (`:137`) | 에이전트가 만든 **영수증 파일이 있는가** |
| 검증의 독립성 | CI = 에이전트가 아닌 판정자(P15③) | 영수증 = 에이전트가 실행한 러너의 산출물 |
| 실패 방향 | 옮기지 않았으면 차단 — 성립 | 영수증 없으면 차단 — 성립하지만 영수증을 만드는 비용이 D-1 처럼 0 |

**두 마커는 구조가 아니라 수사만 같다.** `hooks/pre-push:132-136` 이 basename 대조·정규식 이스케이프까지 파고든 것은 "**독립 러너에 실제로 등록됐는가**"라는 검증 가능한 명제가 있었기 때문이다. HOST-ONLY 에는 그 명제가 없다.

부수: 신선도가 두 값으로 갈린다 — §4-3 은 **30일**(`:116`), §5-2·AC-1 은 **1800초**(`:147`, `:239`). 같은 `receipts/<channel>.json` 의 `last_verified_at` 을 두 소비자가 1440배 차이로 읽는다. 어느 것이 배송 게이트인지 계획에 없다. 30일이 배송 게이트라면 **라이브 1건이 30일치 초록을 산다** — V-3(`coding-principles.md:57` *"라이브 1건 없이 완료 없음"*)을 30일 단위로 면제하는 셈이다.

### D-7 [중대] HOST-ONLY 스크립트가 RED 원장을 영구 오염시킨다 — §4-4 의 전제가 깨진다

**대상**: 계획 `:120-122`(§4-4 "RED 원장은 새로 만들지 않는다"), `:183`(§5-4 "exit 2 는 session-status.sh 에서 RED 로 세어진다")

계획의 §5-4 주장은 참이다 — `scripts/session-status.sh:63` 이 `|| red=$((red + 1))` 로 **0 이 아닌 모든 종료코드**를 RED 로 센다. 그런데 HOST-ONLY 스크립트는 라이브 부재 시 정의상 exit 0 을 낼 수 없다(D-6). 그러면:

- 게이트 0(`bash scripts/session-status.sh`)의 `RED: N/M` 이 **크롬이 안 떠 있는 모든 세션에서 상시 N≥1** 이 된다.
- 계획 §10(`:303`)이 "지금 CDP LISTEN 크롬 0개"라고 적었듯 그것이 기본 상태다.
- 결과: RED 카운트가 "이 세션에 미해결 작업이 있다"는 신호를 잃는다. §4-4 는 "새 원장을 안 만드는 쪽이 P1·P12 에 맞다"고 했지만, **기존 원장을 상시 빨간불로 만드는 것은 원장을 없애는 것과 같다.**

계획에 이 상호작용이 없다. `session-status.sh` 가 `EXCLUDED=acceptance-0-7.sh` 를 출력에 명시하며 제외하는 선례(`:44-45,66` — *"조용히 빼지 않고 출력에 명시한다"*)가 있으므로 해법은 있으나, 계획이 그것을 요구하지 않는다.

---

## §2. 결함 — P2("인수 기준은 실행 가능한 명령") 관점

### D-8 [중대] EARS AC 10개 중 검증 명령이 붙은 것은 1개다

**대상**: 계획 `:205-263`

| AC | 검증 명령 | 기대 출력 |
|---|---|---|
| AC-A1 `:205` | `bash scripts/acceptance-hs-a1.sh` (`:206`) | 없음 |
| AC-A2 `:208` | 없음 | 없음 — 게다가 "**사전 최소치**"의 숫자가 문서 어디에도 없다 |
| AC-B1 `:215` | 없음 | 없음 |
| AC-B2 `:216` | 없음 | 200KB 만 있음 |
| AC-B3 `:217` | 없음 | 없음 |
| AC-0 `:227` | 없음 (검증 방법은 산문 — "DB 에 직접 위반 INSERT 를 시도", `:233`) | 없음 |
| AC-1 `:239` | 없음 | 없음 |
| AC-1-데이터안전 `:240` | 없음 (`run_log` 네비게이션 이벤트 수) | "0회" |
| AC-2 `:248` | 없음 | 없음 |
| AC-3 `:255` | 없음 | 없음 |
| AC-4 `:262` | 없음 | 없음 |

P2(`coding-principles.md:17`)는 *"PR 본문에 검증 명령 + **기대 출력**이 없으면 CI 실패. 산문 단언만 있으면 실패"* 다. §5-4(`:178-184`)가 명명 규약(`scripts/acceptance-hs-<id>.sh`)과 출력 형식을 정의하므로 명령은 **유추 가능**하지만, 기대 출력은 유추도 안 된다. 특히 AC-A2 의 "사전 최소치"가 미정인 채로는 그 AC 자체가 P20 함정("0건 처리로 통과")을 자기 인수 기준에서 못 막는다 — 계획이 `:209` 에서 인용한 `next typegen` 사고 그 자체다.

부수: AC-4 가 "**(선택적)**" Phase 로 표시돼 있다(`:260`). 완료 정의에 선택항이 있으면 "완료"가 협상 가능해진다. 계획 §10 이 이것을 한계로 적지 않았다.

### D-9 [중대] counter-AC 가 자기 AC 로 잡히지 않는다 — 4건 확인

정조준 항목 5의 답. counter-AC 는 Phase 별 평문 목록으로 놓였을 뿐, 해당 Phase 의 단일 EARS AC 가 그것을 탐지하는지 검사되지 않았다.

| counter-AC | 그 Phase 의 AC | 잡히는가 |
|---|---|---|
| AC-1 ① "빈 파일 3개 + 임의 64자 hex" (`:242`) | AC-1(`:239`) = SHA 재계산 | **절반만.** 0바이트+정직한 SHA 는 통과 — D-1 공격 1로 **재현** |
| AC-A1 ③ "HOST-ONLY 가 라이브 없이 초록이면 가짜" (`:207`) | AC-A1(`:205`) = 영수증 존재·신선·체인 | **아니다.** AC-A1 은 종료코드를 보지 않는다. 게다가 판정 불가 — D-6 |
| AC-2 ① "카드 0개인데 '0명 수집 완료'로 보고" (`:250`) | AC-2(`:248`) = 필터 활성 칩 증명 | **아니다.** 백그라운드 탭의 카드 0 렌더는 필터와 무관. 유형 [13] 전용 AC 가 없다 |
| AC-3 ① "평가 클라이언트 부재 시 조용한 폴백" (`:257`) | AC-3(`:255`) = LLM 총점 무시 | **아니다.** 폴백 금지는 §5-5(`:193`)의 계약 문구로만 존재하고 AC 가 아니다 |
| AC-B3 "문서에서 손으로 베껴 `live_confirmed`" (`:220`) | AC-B3 + `fixture_ref` 실존·매칭건수 | **잡힌다** — 유일하게 정합 |
| AC-0 "앱 코드로만 막고 DB 제약 없음" (`:233`) | AC-0 = DB 제약 거부 | **잡힌다** |

**"1 Phase = 1 EARS AC"(`:199`)라는 구조 자체가 원인이다.** 한 Phase 가 여러 사고 유형을 담는데 AC 는 하나이므로, 나머지 유형은 counter-AC 나 "함께 넣을 것" 목록으로 밀려나고 **기계 장치를 얻지 못한다**(P1: *"기계 장치 없는 원칙은 삭제한다"*).

---

## §3. 정조준 항목 6 — 사고 14유형 전수 매핑 (계획 §10 은 정직하지 않다)

계획 `:304` 는 [12]·[14] 두 개만 미매핑으로 인정했다. 창립 스펙 §1 표(14유형)를 계획 §6 전체에 대조한 결과:

| # | 유형 (횟수) | 계획에서의 위치 | 전용 EARS AC | 판정 |
|---|---|---|---|---|
| 1 | 중도 이탈·얕은 수집 (**9회 — 최다**) | Phase 2 "함께 넣을 것" 산문(`:249`) + counter-AC(`:250`) | **없음** | ⚠️ **미인정 결함** |
| 2 | 로그인 미수행 (**8회**) | AC-1(`:239`) | 있음 | ✅ |
| 3 | 창을 앞으로 안 띄움 (5회) | Phase 2 산문 `bringToFront`+focus emulation(`:249`) | **없음** | ⚠️ **미인정** |
| 4 | AI 창 ≠ 사장님 창 (5회) | §5-1 `target_id`(`:135`) + Phase 1 산문(`:241`) + Phase B 산출물 주석 "새 탭 0"(`:222`) | **없음** | ⚠️ **미인정** |
| 5 | 자격증명 취급 (5회) | §8 PII AC(`:284`) + §4-2④(`:110`) + Phase 1 Keychain(`:241`) | 부분(PII AC) | 🟡 |
| 6 | 거짓 완료 보고 (4회) | §4 전체 | 있음(간접) — 단 **D-1 로 뚫림** | ⚠️ |
| 7 | 창·탭이 닫히거나 죽음 (4회) | §3 `close()` 미노출(`:86`) + Phase 1 생존 판정 산문(`:241`) + §8(`:283`) | **없음** — 게다가 **D-5 로 뚫림** | ⚠️ **미인정** |
| 8 | 로그인 상태 오판 (4회) | Phase 1 산문(`:241`) + counter-AC(`:242`) | **없음** | 🟡 counter-AC 만 |
| 9 | 필터·검색어 오사용 (4회) | AC-2(`:248`) | 있음 | ✅ |
| 10 | 봇처럼 굴어 차단 (3회) | Phase 2 산문 "결정론 지터"(`:249`) | **없음**, counter-AC 도 없음 | ⚠️ **미인정 — 표현 최약** |
| 11 | 개입 시 양보·재개 안 됨 (3회) | §3 5조-5(`:86`) + §8 "재개는 반드시 살린다"(`:283`) | **없음** | ⚠️ **미인정 + 설계 모순(아래)** |
| 12 | 진행 표시 부재 (3회) | 없음 | 없음 | ✅ §10 이 인정 |
| 13 | 결과 0건인데 진행·보고 (2회) | Phase 2 counter-AC(`:250`) + §5-4 `CHECKED: 0`→FAIL(`:182`) | **없음** | 🟡 counter-AC 만 |
| 14 | 서치 범위 축소 해석 (1회) | 없음 | 없음 | ✅ §10 이 인정 |

**전용 EARS AC 를 가진 유형은 14개 중 2개다 — [2]와 [9].** 계획 §10 이 인정한 미매핑은 2건([12][14])이고, **실제 미매핑은 [1][3][4][7][10][11] 6건이 추가된다**(전용 AC 없음 + counter-AC 없음).

가장 무거운 문제: **창립 스펙 §1 이 스스로 "v6 설계 1순위"로 지목한 [1](9회)·[2](8회)** 중 [1]이 산문으로 밀렸고, 그 자리에 [9](4회)가 유일한 Phase 2 AC 로 들어갔다(`:248`). **최다 사고 유형과 유일한 기계 장치가 어긋나 있다** — 계획 §10 은 이 우선순위 역전을 적지 않았다.

### D-10 [중대] 유형 [11] 은 미매핑을 넘어 계획 내부에서 모순된다

- §3(`:86`)의 typestate 설계: 개입 신호 → `Yielded` 타입(조작 메서드 0개). 그래서 개입 후 호출이 타입상 불가능해진다(5조-5 충족, R-3 에서 실증).
- §8(`:283`): *"개입 시 즉시 양보하고 **재개는 반드시 살린다** — 영구 중단 코드는 SOT 위반"*.

**`Yielded` → `LiveDriver` 로 돌아오는 전이가 §3·§5 어디에도 정의되지 않았다.** 정의하지 않으면 §8 위반(영구 중단)이고, 아무 조건 없이 정의하면 5조-5 무력화다. 필요한 것은 "재승격 함수는 라이브 재검증 통과를 인자로만 받는다" 같은 전이 계약인데 계획에 없다. 유형 [11]은 3회 발생 이력이 있고, 계획은 그것을 "AC 없음"이 아니라 "설계가 서로 막는다" 상태로 두었다.

---

## §4. 경미

- **E-1** `:307` 은 `acceptance-0-2` 만료(2026-08-21)를 적었으나 `suppressions.yaml:37,49`(둘 다 2026-09-15) 도 Phase 기간과 겹칠 가능성이 높다. 특히 `ci-transfer-guarantee`(`:26-42`)는 **계획이 §4-3 에서 재사용하겠다고 한 마커 검증 패턴 자체가 4종 우회로 뚫려 있다는 원장**이다. 계획이 그 패턴을 "동형으로 그대로 쓴다"(`:114`)고 하면서 **그 패턴이 현재 억제 상태라는 사실을 회수하지 않았다**(P12).
- **E-2** `:29` 는 probe 커밋 `6538bac` 을 "워크트리·브랜치 폐기 완료"라고 적었다. `git cat-file -t 6538bac` → `commit`, `git branch -a --contains 6538bac` → 0건. 즉 unreachable 객체로 남아 있고, 이는 `acceptance-0-2`(unreachable==0)를 계속 빨간불로 유지하는 조건이다. 내 probe(`db426d5`·`af6167f`)도 같은 것을 남겼으므로 이것은 계획의 결함이라기보다 0-2 가 억제된 이유의 재확인이다. "폐기 완료"라는 표현이 objects 까지 포함한다고 읽히면 부정확하다.
- **E-3** `:283` 이 PII 를 "로컬 SQLite 1개 파일이 정본"으로 두는데, §8 PII AC(`:284`)는 `pre-commit` 차단만 요구한다. 파일 권한·디스크 암호화·백업 경로에 대한 요구가 없다. L3 데이터 안전 AC 로는 얇다.

---

## §5. 정조준 항목별 최종 판정

| # | 항목 | 판정 |
|---|---|---|
| 1 | §2-A "pre-push 가 다단계·라이브를 막는다" | 차단 사실은 **참**(R-2 실측). "다단계에서 막힌다"는 §4-4 가 스스로 해소하는 자작 문제. "라이브는 원리적으로 막힌다"는 **과장** — 명명·깊이 규약일 뿐(D-3 실측). Phase A 선행의 근거를 다시 써야 한다 |
| 2 | §4 영수증 체인이 P17 을 충족하는가 | **이름만 빌렸다.** 4개 장치 전부를 라이브 0회·0바이트 증거로 통과시켰다(D-1). §4-2① "한 줄 조작하면 이후 전부 깨진다"는 **거짓**(꼬리 위조 후 append 로 무력화). PUSH-PERFORMING 과 **동형이 아니다**(D-6) |
| 3 | §3 런타임이 5조-5·§2-6 을 충족하는가 | **충족한다. SOT 위반 아님** — mypy --strict 로 실증(R-3). 단 에일리어싱 구멍은 계획의 보완 2겹이 둘 다 못 잡고 TS 로도 안 닫힌다(D-5) |
| 4 | AC-B3 범위 제외가 P13④ 위반인가 | `docs/engineering/` 제외는 **정당**(선례 `acceptance-0-6.sh:19`, 실측 13건 전부 문서). **P13④ 위험은 검사기 자기매칭 미해결에 있다**(D-4). 열거식 허용목록도 계획 자신의 §4-2③ 원칙 위반 |
| 5 | EARS AC 가 실행 가능한 명령인가 / counter-AC 가 잡히는가 | **아니다.** AC 11개 중 검증 명령 1개, 기대 출력 0개(D-8). counter-AC 6건 중 4건이 자기 AC 로 안 잡히고 그중 1건은 기계로 재현했다(D-9) |
| 6 | §10 한계 목록이 정직한가 | **불완전하다.** 인정 2건([12][14]), 실제 미매핑 **8건** — [1](9회·최다)·[3]·[4]·[7]·[10]·[11] 추가(§3 전수표). 최다 유형과 유일한 Phase 2 AC 의 우선순위 역전도 미기재 |

---

## §6. 재검증 시 반드시 다시 통과해야 할 것 (D-1~D-10 수정 후)

1. **D-1 재시험**: 0바이트 증거 3개 + 실제 HEAD sha + 러너 재실행으로 만든 5건 체인이 **거부**되는가. 거부 사유가 "체인"이 아니라 "에이전트가 만들 수 없는 외부 객체 부재"여야 한다.
2. **D-2 재시험**: 신규 `scripts/acceptance-hs-*.sh` 가 `.github/workflows/verify.yml` 의 **실행 줄**(`bash -n` 아님)에 등록되지 않으면 push 가 차단되는가. 현재 `hooks/pre-push:93-97` 의 `DEFERRED` 검증 로직을 글로브 전량으로 일반화하면 얻어진다.
3. **D-6 재시험**: HOST-ONLY 스크립트의 종료코드 0·1·2 세 경우 각각에 대해 pre-push 판정이 문서화된 대로 나오는가.
4. **D-7 재시험**: `bash scripts/session-status.sh` 가 크롬 부재 상태에서 HOST-ONLY 를 어떻게 세는지 **출력에 명시**하는가(조용한 제외 금지).
5. **D-4 재시험**: AC-B3 검사기가 자기 리터럴에 매칭되지 않으면서 대상 검출력이 동일함을 `acceptance-0-6.sh:16-18` 방식으로 증명하는가.
6. **§3 전수표**: [1][3][4][7][10][11] 각각에 EARS AC 를 붙이거나, §10 에 미매핑으로 **열거**하는가.

---

## §7. 검증 위생

- 저장소 추적 파일 **수정 0건**. 검증 시작·종료 모두 `HEAD=ec201dc`, `git status --porcelain` = 미추적 `docs/engineering/humansearch-v6-implementation-plan-2026-08-08.md` 1건뿐(검증 시작 시점과 동일).
- 임시 워크트리 `wt-v1probe` 와 브랜치 `probe/v1-red-push` **폐기 완료**(`git worktree remove --force`, `git branch -D` → `Deleted branch probe/v1-red-push (was af6167f)`). `git worktree list` = 메인 1개.
- D-1·D-5 의 실험 코드(`runner.py`·`validator.py`·`drv.py`·`alias.py`)는 scratchpad 에만 있고 저장소에 없다.
- V-1 준수: 이 판정의 결함 D-1·D-2·D-3·D-5·D-6·D-7 은 실행 산출물로 뒷받침된다. 실행 없이 문서 대조만으로 낸 것은 D-4(부분)·D-8·D-9·§3 전수표이며, 그 사실을 여기 명시한다.
