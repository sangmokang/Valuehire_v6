# HumanSearch 관측기 URL 파싱 크래시 — goal (2026-08-25)

등급: **L3** (개인정보 누출 경로 · SOT-30 §1)
워크트리: `worktrees/hs-observe-url-crash` · 브랜치 `task/hs-observe-url-crash` · base `c59bad7`

## 1층 — 결론

사람인 화면을 한 번 들여다보는 프로그램이, 브라우저에 열려 있던 **이상한 주소 하나** 때문에
통째로 멈추면서 그 주소의 일부를 오류 기록에 그대로 남기고 있었다. 실제로 돌려 재현했다.
고친 뒤에는 어떤 주소가 들어와도 정해진 한 줄만 남기고 정해진 값으로 끝난다.

처음 받은 지시는 한 곳을 고치는 일이었는데, 감사와 교차 검증이 **같은 종류의 구멍을 일곱 개 더**
찾아내 모두 같은 변경에 담았다. 늘어난 이유는 이 문서의 작업 분해표와 적대 검증 로그에 있다.

작업 중 내가 한 번 잘못 판단했다 — 시험이 닿지 않는 코드를 "닿을 수 없는 코드"로 읽고
안전장치를 걷어냈다가, 검증자가 곧바로 닿는 경로를 찾아냈다. 되돌리고 그 자리에 시험을 넣었다.

## 상위 목표 (1문장)

사람인 탭 하나를 관측할 때, 다른 탭이 만든 이상한 주소 하나 때문에 관측기가 통째로 죽으면서
주소 일부를 오류 메시지에 그대로 흘리는 일이 없게 한다 — 성공 신호: 어떤 문자열이 주소 자리에
들어와도 관측기는 계약된 한 줄만 찍고 계약된 종료값(0 또는 2)으로 끝난다.

## 읽은 SOT

- `docs/sot/humansearch-browser-contract.md` §5 (허용 origin — "경로·query에 계정·후보 식별자가
  있더라도 로그나 증거에 값을 남기지 않는다"), §7 (목표 탭 계약 — 0개·2개 이상이면 시작 금지),
  §12 (개인정보 경계 — "Git·로그·PR 본문에 원본 내용·후보 식별자를 남기지 않는다")
- `docs/sot/humansearch-l0-surface-contract.md` (출력 상태 5개 · `DRIFTED` 는 계약 불일치의 결과)
- `docs/sot/coding-principles.md` P3(조용한 실패 금지) · P5②(순수 판정 함수 = 속성 기반 시험 필수)
  · P11①(파일 soft 300 / hard 600) · P16(런타임 동작 검사) · P20(0건 처리 의심) · P22(상수 1곳)
- `docs/sot/verification-commands.md` (이 저장소의 실제 게이트 명령 — `npm` 스크립트 없음)

## 과거 회수 (R4)

- SOT-30이 요구하는 재발 원장 `docs/sot/31-strict-recurrence-ledger.md`는 **이 저장소에 존재하지
  않는다**(`ls docs/sot/` 실행 확인). 있는 척하지 않고, 이번 건의 재발 방지는 회귀 테스트로만
  담보한다.
- 회수한 자기 지침: "정규식·파서는 눈으로 읽지 말고 돌려라" — 그래서 이 문서의 입력 영역 표는
  전부 실제 `urlsplit` 실행 결과로 채웠고, 검증도 Hypothesis 속성 시험을 포함한다.

## 현재 상태 (추측 금지 · file:line)

`humansearch/src/humansearch/observe.py` 안에서 `urlsplit()`을 감싸지 않고 부르는 곳이 4군데다.

| # | 위치 | 입력 출처 | 도달 경로 |
|---|---|---|---|
| 1 | `observe.py:244` `_origin()` | CDP `/json/list`가 준 **다른 탭의 URL** | `observe_once` → `select_single_target:69` |
| 2 | `observe.py:299` `_privacy_reduced_url()` | 선택된 탭 URL | `observe_once:142`, 공개 API `format_observation_line:118` |
| 3 | `observe.py:253` `_valid_origin()` | `contracts/humansearch/saramin-markers.json` | `_load_contract:189` |
| 4 | `observe.py:163` `main()` | 이미 축약된 tab_url | `main` |
| 5 | `_cdp.py:32` `observe_markers()` | 선택된 탭의 websocket URL | `observe_once:134` — **이미 올바르게 막혀 있다**(`ValueError`→`CdpReadError`, 메시지에 URL 없음). 다만 시험이 0건이었다 |


→ 표가 말하는 것: 같은 결함이 5곳에 있었고 4곳은 무방비, 1곳(`_cdp`)은 이미 막혀 있었다. 즉 저자가 이 위험을 알고 있었는데 나머지 4곳에 적용하지 않은 것이다. 나쁜 소식이지만 고칠 방향은 분명하다.
`urlsplit()`은 `ValueError`를 던진다(실행 확인, Python 3.14.1):

```
'https://[::1'                → ValueError: Invalid IPv6 URL
'https://www.saramin.co.kr＃x' → ValueError: netloc 'www.saramin.co.kr＃x' contains
                                 invalid characters under NFKC normalization
```


→ 뭘 시켰나: 두 종류의 잘못된 주소를 `urlsplit()` 에 넣었다. 뭐가 나왔나: 예외가 났고, 두 번째 메시지에는 **주소의 호스트가 원문 그대로** 실렸다. 나쁜 소식 — 이 문자열이 오류 로그에 남는다.
`main()`은 `except (CdpReadError, ObservationError)`만 잡는다(`observe.py:157`). `ValueError`는
그 그물에 안 걸린다.

### 재현 (실행 확인 2026-08-25)

`_fetch_targets`가 `url = "https://www.saramin.co.kr＃x/candidates/HONG-GILDONG?token=SECRET"`인
page 타깃 1개를 돌려주게 하고 `observe.main(["--channel","saramin","--port","9225","--once"])` 실행:

```
ValueError: netloc 'www.saramin.co.kr＃x' contains invalid characters under NFKC normalization
EXIT=1
```


→ 뭘 시켰나: 후보 식별자와 토큰이 든 주소를 가진 탭 하나를 관측기에 먹였다. 뭐가 나왔나: 계약된 한 줄 대신 종료값 1. 나쁜 소식 — 관측기가 답을 못 주고 죽는다.
- stdout: **비어 있음** — 계약된 `STATE=... TAB=... ROLES=... CONTRACT_VALID=...` 한 줄이 안 나온다.
- 종료값: **1** — L0 계약이 정한 값은 0(authenticated) 또는 2뿐이다.
- stderr: traceback에 **netloc이 원문 그대로** 실린다 → 브라우저 계약 §5·§12 위반.

## 근본 원인

주소 파싱의 **입력 영역이 정의된 적이 없다**. 코드는 "urlsplit은 문자열을 받으면 결과를 준다"는
암묵 가정 위에 서 있고, 파싱 자체가 실패할 수 있다는 행이 어느 표에도 없다. 그래서 파싱 실패는
거부(deny)로 흡수되지 못하고 프로세스 밖으로 새어 나간다.

## ① 입력 영역 표 — 주소 문자열 (SOT-30 §3)

명시 입력: URL 문자열 1개, 허용 origin 집합, loggable 경로 집합.
암묵 입력: 없음(순수 함수 — 네트워크·파일·시계·난수 없음).

| # | 입력 부류 | 예 | `_origin` | `_valid_origin` | `_privacy_reduced_url` |
|---|---|---|---|---|---|
| 1 | 정상 https | `https://portal.invalid/home` | origin 반환 | True | 축약 URL |
| 2 | 스킴 위반 | `http://h/`, `ws://h`, `file:///x` | `""` 거부 | False | (도달 불가·거부) |
| 3 | netloc 없음 | `https:///p`, `/rel`, `""` | `""` 거부 | False | 빈 결과 |
| 4 | netloc에 userinfo(`사용자:암호@호스트`) | (리터럴은 비밀 스캔에 걸리므로 생략) | userinfo까지 포함한 문자열 반환 → 허용목록에 그런 값이 못 들어가므로 거부 | False | netloc 그대로(경로만 가림) |
| 5 | 경로·query에 식별자 | `…/candidates/X?token=S` | origin 반환 | False | 경로 `/...` 로 가림 |
| 6 | **IPv6 미종결** | `https://[::1` | **현재 크래시** → `""` | **현재 크래시** → False | **현재 크래시** → `""` |
| 7 | **NFKC 위반 netloc** | `https://exa℀mple.com` | **현재 크래시** → `""` | **현재 크래시** → False | **현재 크래시** → `""` |
| 8 | **그 외 전부 파싱 불가** | 임의 문자열 | `""` 거부 | False | `""` |


→ 표가 말하는 것: 6·7행이 지금 크래시하는 자리이고, 8행이 "앞으로 뭐가 오든"을 덮는 안전망이다. 6·7만 고치면 다음 파이썬 판올림에서 새 실패 사유가 생겼을 때 같은 사고가 반복된다.
catch-all(8행) 구현 = `ValueError`를 **명시적 거부로 변환**한다. 의미 추정·정상화·다른 파서로의
자동 전환은 하지 않는다(브라우저 계약 §"주 경로가 실패하면 다른 경로로 자동 전환하지 않고 중단").

## ② 결정 목록 (확정)

| 결정 | 확정값 | 근거 |
|---|---|---|
| 파싱 불가 URL은 목표 탭이 되는가 | **아니다** — 후보에서 제외 | 브라우저 계약 §7 "URL의 부분 일치로 추측하지 않는다" |
| 파싱 불가 URL이 유일 후보였다면 | 후보 0개 → `TargetSelectionError` → `DRIFTED`, exit 2 | §7 "0개면 시작하지 않는다" |
| 파싱 불가 URL을 화면에 뭐라고 찍나 | 빈 문자열 → `format_observation_line`이 기존대로 `TAB=-` | 새 어휘를 만들지 않는다. §5 "값을 남기지 않는다" |
| 계약 JSON에 파싱 불가 origin이 있으면 | `ObservationError("allowed origin contract is invalid")` | 기존 fail-closed 경로 재사용 |
| 오류 메시지에 URL을 넣나 | **아니다** — 어떤 예외 메시지에도 입력 URL을 넣지 않는다 | §12 |


→ 표가 말하는 것: 애매한 갈림길 5개를 코드 쓰기 전에 못 박았다. 특히 마지막 줄이 이 작업의 핵심이다 — 크래시를 막는 것만으로는 부족하고, 새로 만드는 거부 메시지에도 주소를 넣지 않아야 한다.
## ③ 표↔테스트 대응

표의 6·7행은 WU1 RED(`tests/test_observe_url_parse_failure.py`), 8행은 WU2 RED
(`tests/test_observe_url_parse_property.py`)다. 시험 파일을 WU별로 나누는 이유는 P5①(RED 커밋
이후 테스트 파일 불변)을 WU 단위로도 지키기 위해서다. 1~5행은 기존 시험이 이미 덮는다(`test_observe_boundary.py`,
`test_observe_adversarial_output.py`). 8행(catch-all)은 Hypothesis 속성 시험으로 덮는다 —
**임의 텍스트에 대해 세 함수가 절대 예외를 던지지 않는다**는 성질.

## 인수 기준 (EARS)

**AC-1 (WU1)** — 목표 탭 목록에 파싱 불가 URL을 가진 page 타깃이 있을 때, 관측기는 그 타깃을
후보에서 제외하고, 예외를 프로세스 밖으로 내보내지 않으며, stdout에 계약된 한 줄만 찍고 종료값
2로 끝난다. 어떤 출력에도 그 URL의 netloc·경로·query가 나타나지 않는다.

- 검증: `uv run pytest tests/test_observe_url_parse_failure.py -q` (exit 0)
- counter-AC: 수정 코드를 되돌리면(`_origin`의 예외 처리 제거) 이 시험이 반드시 실패한다.

**AC-2 (WU2)** — 계약 JSON의 `allowed_origins`에 파싱 불가 값이 있을 때 `_load_contract`는
`ObservationError`로 거부하고, `format_observation_line`에 파싱 불가 URL이 들어와도 예외 없이
`TAB=-`를 찍는다. 그리고 임의 텍스트 입력에 대해 `_origin`·`_valid_origin`·`_privacy_reduced_url`
셋 다 예외를 던지지 않는다(Hypothesis 속성).

- 검증: `uv run pytest tests/test_observe_url_parse_property.py -q` · `bash scripts/acceptance-hs-gates.sh` (exit 0, 수집 수 > 81)
- counter-AC: 속성 시험은 수정 전 코드에서 반드시 실패해야 한다(반례를 Hypothesis가 스스로 찾는다).

## 계약 (SDD — 입출력 모양 먼저)

```python
def _split(url: str) -> SplitResult | None:   # 신설. 파싱 실패 = None. 예외 없음. URL 미포함.
def _origin(url: str) -> str                  # 불변: 파싱 실패 → ""
def _valid_origin(value: object) -> bool      # 불변: 파싱 실패 → False
def _privacy_reduced_url(url, loggable) -> str  # 불변: 파싱 실패 → ""
```


→ 뭘 보여주나: 겉으로 드러나는 함수 모양은 하나도 바뀌지 않고, 파싱이 실패했을 때의 반환값만 정해진다. 좋은 소식 — 이 변경을 쓰는 쪽 코드는 손댈 것이 없다.
공개 API 시그니처는 바뀌지 않는다. `humansearch/__init__.py` 내보내기 목록도 바뀌지 않는다.

## R1 작업 분해표

| WU | AC | 파일 | focused 검증 |
|---|---|---|---|
| WU1 | AC-1 | `observe.py`(`_split`,`_origin`) + 신규 시험 | `pytest tests/test_observe_url_parse_failure.py` |
| WU2 | AC-2 | `observe.py`(`_valid_origin`,`_privacy_reduced_url`) + 신규 속성 시험 | `pytest tests/test_observe_url_parse_property.py` + `acceptance-hs-gates.sh` |
| WU3 | AC-3(R9로 추가) | 시험만 — `tests/test_cdp_websocket_parse_failure.py` | `pytest tests/test_cdp_websocket_parse_failure.py` + 변조 증명 |
| WU4 | AC-4(Codeaudit 반례, R9) | `observe.py`(`_privacy_reduced_url`) + `tests/test_observe_userinfo_redaction.py` | `pytest tests/test_observe_userinfo_redaction.py` + 변조 증명 |
| WU5 | AC-5(V1 1회차 반례, R9) | `observe.py`(`_load_contract`,`_fetch_targets`,`_valid_origin`,`_privacy_reduced_url`) + `tests/test_observe_adversarial_v1_findings.py` | 같은 파일 + 변조 8종 |
| WU6 | AC-6(V1 2회차 반례, R9) | `observe.py`(JSON 경계·`_valid_targets_path`·한 줄 가드) + `_cdp.py`(JSON 경계) + `tests/test_observe_adversarial_v1_round2.py` | 같은 파일 + 변조 6종 |
| WU7 | AC-7(V1 3회차 반례, R9) | `observe.py`(`_fetch_targets` 생성자 위치·`_is_loopback_address`) + `tests/test_observe_transport_construction.py` | 같은 파일 + 변조 |
| WU8 | AC-8(V1 4회차 반례, R9) | `observe.py`(`_is_loopback_address` ASCII·전송 `except`) + 같은 시험 파일 | 같은 파일 + 변조 3종 |


→ 표가 말하는 것: 사장님 지시 범위는 WU1~WU2이고 WU3 이후는 전부 감사·적대검증이 찾아낸 반례를 같은 PR에 넣은 것이다. 범위가 늘어난 이유가 여기 다 적혀 있다.
WU1 GREEN 커밋 전 WU2 착수 금지(R5). WU3는 작업 중 발견한 반례의 영구 편입이며(R9) 코드 변경
0줄 · 시험만 추가한다. 이미 올바른 코드의 특성화 시험이므로 RED 대신 **변조 증명**으로
공허하지 않음을 보인다.

**AC-3** — `_cdp.observe_markers`에 파싱 불가 websocket 주소가 들어오면 `CdpReadError`로
거부하고 그 메시지에 주소 조각이 없다. counter-AC: 그 가드를 제거하면 시험이 반드시 실패한다.

## R1 예외 케이스 표 (작업 진행 중 만날 수 있는 상황)

| 상황 | 처리 |
|---|---|
| `uv sync` 실패 / 네트워크 없음 | 명시적 중단 + 사유 보고. 시험 건너뛰기 금지 |
| ruff/mypy가 새 코드에 불합격 | 자동 처리(코드 수정 후 재실행) |
| 파일이 P11 hard 600줄 초과 | 명시적 중단 + 분할안 제시 |
| 기존 시험 81건 중 하나라도 깨짐 | 명시적 중단 — 회귀이므로 원인 회수 |
| 적대검증이 새 반례 발견 | 같은 PR 회귀 시험으로 편입(R9). 불가하면 중단 보고 |
| GitHub push·PR 생성 실패 | 명시적 중단 + 사유 보고. merge 시도 금지 |
| 그 외 전부 | 명시적 중단 + 이 표 갱신안 제시 |


→ 표가 말하는 것: 작업 중 만날 수 있는 상황을 미리 세어 두고, 표에 없는 일이 생기면 임의로 판단하지 않고 멈춘다. 마지막 줄이 그 약속이다.
## 게이트 계획

RED 커밋(시험만) → GREEN 커밋(구현만) → `bash scripts/acceptance-hs-gates.sh` →
`bash scripts/acceptance-hs-gates-mutations.sh` → `bash scripts/acceptance-hs-gates-antiforge.sh` →
`bash verify.sh` → Codeaudit(읽기 전용) → 적대검증 V1/V2 → push → PR → CI. **merge 안 함.**

## 적대검증 정조준

1. `_split`이 `None`을 돌려줄 때 호출부가 그걸 정말 거부로 쓰는가, 아니면 빈 origin `""`이
   `allowed_origins`에 우연히 들어 있으면 통과해 버리는가? (계약 JSON에 `""`가 못 들어가는지 확인)
2. 파싱 실패를 삼키면서 **정상 URL의 거부까지 조용해지지** 않는가 (P3 조용한 실패)
3. 새 예외 메시지에 URL 조각이 들어가지 않는가
4. Hypothesis 속성이 실제로 6·7행 같은 반례를 만들 수 있는가 — 아니면 통과가 공허한가
5. 표 밖의 현실 입력이 남아 있는가 (`urlsplit`이 던질 수 있는 다른 `ValueError` 사유)

## 롤백 절차 (L3)

`git revert <GREEN SHA>` 1개로 되돌아간다. 시험 커밋(RED)은 남겨도 무해하지 않다 — 되돌리면
시험이 빨개지므로 RED·GREEN 두 커밋을 함께 revert한다. 공개 API·계약 JSON·SOT를 바꾸지 않으므로
데이터 마이그레이션이나 하위 호환 문제는 없다.

## 영향 반경 (L3)

`humansearch/src/humansearch/observe.py` 1개 파일. 호출자는 CLI(`python -m humansearch.observe`)
뿐이고, 아직 운영 자동화에 배선되지 않았다(브라우저 계약 §"실제 자동화 코드는 여전히 NOT_RUN").
따라서 라이브 영향은 CLI 1개 명령의 실패 모드에 한정된다.

## 배포 후 관측 항목 (L3)

- 관측기 종료값이 **1로 끝나는 실행이 0건**이어야 한다(0/2만 정상). 1이 관측되면 이 표에 없는
  예외가 또 새고 있다는 뜻이다.
- 관측기 stderr가 **비어 있어야** 한다. 한 줄이라도 있으면 즉시 조사.
- **단, 출력을 받는 쪽이 파이프를 먼저 닫으면 종료값 120 + stderr 2줄이 난다**(아래 참조).
  이것은 입력 결함이 아니라 소비자 조건이므로 위 두 항목은 "정상 소비자로 실행했을 때"를
  전제한다. 종료값 120 이 보이면 관측기가 아니라 그 실행을 감싼 파이프라인을 먼저 본다.

## 비범위

- CDP 연결·브라우저 기동·포트 발견(D1 소유, `NOT_RUN`)
- `_cdp.py`의 websocket URL 검증
- observe.py의 P11 soft 300줄 초과(현재 312줄) 해소 — 이번 변경으로 ~25줄 늘어난다. hard 600은
  넘지 않는다. 분할은 별도 요청으로 남긴다(이 PR에서 파일을 쪼개면 diff가 결함 수정을 가린다).
- 재발 원장 파일 신설

## 적대 검증 로그

### G(생성자) 자기 공격 — goal §"적대검증 정조준" 5개 항목 실행

**정조준 4번이 실제로 터졌다.** WU2의 Hypothesis 속성 시험을 `st.text()` 만으로 쓴 첫 판은
**수정 전 코드에서도 통과했다**(실측: `2 failed, 2 passed` — 실패한 2건은 속성이 아닌 예시 시험).
평범한 텍스트 전략은 `https://` 접두사와 NFKC 파괴 문자를 동시에 만들 확률이 사실상 0이라
결함 영역에 닿지 못한다. 주소 모양을 직접 조립하는 전략(`_ADDRESSES`)과 알려진 반례 2개의
`@example` 고정으로 교체한 뒤 `4 failed` 로 진짜 RED가 됐다. → **회귀 자산으로 편입됨**(R9).

**정조준 5번(표 밖 입력)에서 5번째 파싱 지점 발견.** `_cdp.py:32` 도 같은 `urlsplit` 을 쓴다.
그쪽 가드는 이미 올바르지만 **시험이 0건**이었다. → WU3로 편입, 변조 증명까지 완료(R9).

**부수 발견 — `.port` 함정.** `urlsplit()` 이 성공한 뒤에도 `SplitResult.port` 는 숫자가 아닌
포트에서 별도로 `ValueError` 를 던진다(실측: `.port` 만 그렇고 `.scheme/.netloc/.path/.query/`
`.fragment/.username/.password` 는 아니다). `observe.py` 는 `.port` 를 읽지 않고 `_cdp.py` 는
읽으면서 이미 막고 있다. WU3 시험이 이 갈래를 함께 고정한다.

**정조준 1번(빈 origin 통과 가능성) 반증.** `_origin` 이 거부 시 돌려주는 `""` 가
`allowed_origins` 에 우연히 들어 있으면 파싱 실패가 통과가 된다. 확인: `_load_contract` 는
`_string_list()` 로 빈 문자열 원소를 거부하고(`bool(item)`), `_valid_origin("")` 도 False다
(실측). 따라서 `""` 는 허용목록에 들어갈 수 없다.

**정조준 2번(정상 URL의 거부까지 조용해지는가) 반증.** 기존 시험 81건이 그대로 통과하고
(85→89건), `test_unparseable_target_url_does_not_hide_the_approved_tab` 이 파싱 불가 탭과
정상 탭이 섞여 있을 때 정상 탭이 선택됨을 고정한다.

**정조준 3번(새 메시지의 URL 조각) 반증.** 새로 만든 예외 메시지는 없다. 기존
`TargetSelectionError("expected exactly one matching tab, found N")` 로 흡수되며, 시험이
`＃drift`·`CANDIDATE-9`·`private`·`[::1` 4개 표식의 부재를 단언한다.

### 변조 증명 (L3)

| 변조 | 대상 | 결과 |
|---|---|---|
| `_split` 의 `except ValueError: return None` 제거 | `test_observe_url_parse_failure.py` | **4 failed** (exit 1) |
| 〃 | `test_observe_url_parse_property.py` | **4 failed** (exit 1) |
| `_cdp` 의 `try/except ValueError` 가드 제거 | `test_cdp_websocket_parse_failure.py` | **2 failed** (exit 1) |


→ 뭘 시켰나: 고친 코드를 일부러 되돌려서 시험이 빨개지는지 봤다. 뭐가 나왔나: 세 경우 모두 시험이 죽었다. 좋은 소식 — 이 시험들은 통과 도장이 아니라 실제로 뭔가를 지키고 있다.
변조는 전부 격리 복제본(`scratchpad/mut*`)에 적용했고 작업트리 원본은 건드리지 않았다.

### 라이브 실증 (몽키패치 0건, 실제 CLI 엔트리포인트)

실제 `python -m humansearch.observe --channel saramin --port <p> --once` 를 진짜 TCP 소켓 상대로
실행했다. 사장님의 실제 크롬(127.0.0.1:9225, Chrome/151.0.7922.170)에는 읽기 전용 확인만 하고
건드리지 않았으며, 파싱 불가 입력 실증은 원본을 오염시키지 않는 복제 트리 + 별도 포트에서 했다.

| | 수정 전 (`c59bad7`) | 수정 후 (HEAD) |
|---|---|---|
| stdout | (빈 문자열) | `STATE=drifted TAB=- ROLES=0 CONTRACT_VALID=false` |
| 종료값 | **1** (L0 계약 밖) | **2** (계약 안) |
| stderr | Traceback + `netloc 'hiring.saramin.co.kr＃drift'` | (빈 문자열) |
| 누출 표식 | `＃drift`, `Traceback` **검출됨** | 4종 전부 미검출 |


→ 표가 말하는 것: 같은 입력에서 수정 전에는 호스트 이름이 오류 출력에 남았고, 수정 후에는 네 가지 표식 어느 것도 나오지 않는다. 좋은 소식 — 사장님이 지목하신 누출이 실제로 닫혔다.
사장님 실제 크롬(9225) 상대 실행에서도 정상 동작했다: `STATE=drifted TAB=- ROLES=0
CONTRACT_VALID=false`, exit 2, stderr 없음(해당 프로필에 승인 origin 탭이 0개였다).

### 배선 증명 (런타임 추적 — grep 아님)

`sys.settrace` 로 실제 CLI 실행 중 호출을 기록:

```
main:148 -> observe_once:128 -> _valid_origin:269 -> _split:246
         -> select_single_target:59 -> _origin:262 -> _split:246
         -> format_observation_line:110
```


→ 뭘 보여주나: 실제 명령을 돌리는 동안 어떤 함수가 순서대로 불렸는지 기록한 것이다. 새로 만든 `_split` 이 두 갈래로 실제 도달한다. 좋은 소식 — 아무도 안 부르는 죽은 코드가 아니다.
새 함수 `_split` 이 엔트리포인트에서 두 경로로 실제 도달한다. 고아 아님.

### Full Strict 기준선 대비 (BASELINE_DIFFERENTIAL_PASS)

base SHA `c59bad7b160c473cda5545e76e6fa6bcc711a7ea` 의 격리 복제본에서 같은 명령을 실행해 대조.

| 명령 | 브랜치 | 기준선(c59bad7) |
|---|---|---|
| `scripts/acceptance-0-2.sh` | exit 2 (`.secret-patterns` 없음 = NOT_RUN) | exit 2 (동일) |
| `scripts/acceptance-0-5.sh` | exit 1 (origin/main != main) | exit 1 (동일) |
| 나머지 인수 검사 23종 | 전부 exit 0 | — |


→ 표가 말하는 것: 실패한 2건은 이 브랜치를 만들기 전 상태에서도 똑같이 실패한다. 즉 내 변경이 만든 실패가 아니다. 다만 "원래 실패하던 것"이므로 통과로 세지 않고 그대로 실패로 적는다.
브랜치 실패 집합 ⊆ 기준선 실패 집합 · **새 실패 0건** · 삭제된 테스트 0건 · 테스트 약화 0건.
두 실패는 모두 환경 사유이며(로컬 전용 패턴 파일 부재 / main 브랜치 push 상태) 이 변경과 무관하다.
`acceptance-0-7.sh` 는 세션 시작 원장이 "CI 담당"으로 표시한 항목이라 로컬에서 제외했다.

### Codeaudit (읽기 전용, 트랙 A·B)

대상 SHA `6eff539` 이전(`3df21fd`). 커버 트랙 A(계약 대조)·B(반례 지목). C(검사기 무력화)는
Adversarial, D(실제 실행)는 위 라이브 절이 담당한다.

**A 트랙 — 위장 origin 전수 대조(실측).** 승인 origin 만 통과하고 나머지는 전부 `found 0` 으로
거부됨을 확인했다.

| 입력 | 결과 |
|---|---|
| `https://hiring.saramin.co.kr/home` | 선택됨 |
| netloc 에 `사용자:암호@` 를 붙인 위장 | 거부 (found 0) |
| 대문자 호스트 `HIRING.SARAMIN.CO.KR` | 거부 |
| 명시 포트 `:443` | 거부 |
| 합자 문자 호스트(`ﬀ`) | 거부 |
| 서브도메인 덧붙임 `…co.kr.evil.com` | 거부 |
| NFKC 파괴 / IPv6 미종결 | 거부 |

→ exact-origin 문자열 동등 비교라서 정규화 틈이 없다. 전부 fail-closed 방향이다.

**B 트랙 — 유효 반례 1건 발견(→ WU4로 편입).**

- 입력: `_privacy_reduced_url(...)` 에 netloc 앞에 `사용자:암호` 접속 자격이 붙은 https 주소
- 기대: 접속 자격이 출력에 없어야 한다(브라우저 계약 §12)
- 당시 실제 동작: 경로는 `/...` 로 가렸지만 **접속 자격이 붙은 netloc 을 통째로 출력**했다
- 도달성: CLI 경로로는 도달 불가(그런 탭은 허용 origin 과 절대 일치하지 않는다). 그러나
  `format_observation_line` 은 패키지가 내보내는 공개 함수이고, 이 함수의 직무 자체가
  개인정보 축약이다
- 처분: **같은 PR 에 편입 완료**(R9) — `tests/test_observe_userinfo_redaction.py`,
  구현은 `parsed.netloc.rpartition("@")[2]`. 변조(되돌림) 시 3건 실패로 공허하지 않음을 확인

**A 트랙 — 문서 과장 1건 정정.** `_split` 독스트링이 "모든 호출자가 잘못된 scheme 과 같은
거부로 바꾼다"고 썼는데, `_privacy_reduced_url` 은 잘못된 scheme 을 거부하지 않는다(실측: `http://h/x` → `'http://h/...'`). "각자의 명시적 거부"로 정정했다.

**잔여 위험(중간) — 실패 원인이 한 표기로 뭉개진다.** `main()` 은 계약 파일 손상·브라우저
불통·탭 0개·탭 2개를 전부 `STATE=drifted` 로 낸다. 이번 변경으로 "계약 origin 파싱 실패"가
크래시(시끄러움)에서 `drifted`(조용함)로 옮겨왔다. 다만 크래시도 원인을 알려주지 않았고
(종료값 1 + netloc 누출), `_load_contract` 는 이미 다른 8종의 계약 오류를 같은 곳으로 보낸다.
즉 기존 설계와 일관되며 이번 변경이 만든 구멍은 아니다. 원인 구분은 별도 요청이 소유한다 —
그래서 이 문서의 "배포 후 관측 항목"에 종료값 1 감시를 뒀다.

### V1 (1차 적대검증) — `codex exec --sandbox read-only`, fresh 세션

**도구 정정 (실행하지 않은 것을 실행했다고 하지 않는다).** SOT-30 §6이 지정한
`/codex:adversarial-review --fresh` 는 **이 환경에 존재하지 않는다**(`~/.claude/skills/` 목록과
codex 플러그인 커맨드 전수 확인). 대신 실제 설치된 `codex-cli 0.148.0` 을 fresh·read-only
샌드박스로 직접 실행했다. 산출물(diff·AC·테스트)만 전달하고 구현 추론 과정은 전달하지 않았다.

**1차 시도는 무효.** 첫 프롬프트는 제공자 측 필터에 걸려
`ERROR: This content was flagged for possible cybersecurity risk`, exit 1, 판정 본문 0줄로
끝났다. "Done만/빈 결과는 무효" 규칙에 따라 V1으로 세지 않고, 방어적 견고성 검토 문구로
1회 재작성해 재실행했다.

**2차 시도 판정: `VERDICT: FAIL` · Merge recommendation: REQUEST_CHANGES** (transcript:
`scratchpad/v1_out2.txt`, 121,898 tokens, HEAD `5f8f8c7` 기준). 네 건 중 세 건을 **독립
재현**했다 — 액면으로 받지 않았다.

| V1 지적 | 재현 결과 | 처분 |
|---|---|---|
| ①[HIGH] `json.loads` 가 4,300자리 초과 정수에서 `JSONDecodeError` 가 아닌 맨 `ValueError` 를 던져 두 JSON 경계를 샌다 | **재현됨** — `ValueError: Exceeds the limit (4300 digits)` | WU5에서 `except ValueError` 로 수정 |
| ②A[HIGH] 고립 서로게이트(`\ud800`)가 `print()` 에서 `UnicodeEncodeError` 로 죽는다(try 밖) | **재현됨** | WU5에서 축약 단계가 인코딩 불가를 빈 문자열로 흡수 |
| ②B[HIGH] U+2028 이 netloc 에 살아남아 출력이 `splitlines()` 기준 **2줄** | **재현됨** — `"\n" in line = False` 인데 `splitlines()==2` | WU5에서 한 줄 계약 가드 추가 |
| ③[HIGH] `_valid_origin` 이 `.port` 를 검증하지 않아 `:notaport`·`:99999` 를 통과 | **재현됨** | WU5에서 `_readable_port` 추가 |
| ④[LOW] argparse 오류는 상태줄 계약 밖 | 재현됨 — 단, **traceback 없이** usage 3줄 + exit 2 | 결함 아님으로 판정. CLI 인자 오류는 관측 결과가 아니다 |
| ⑧ `rpartition("@")` → `partition("@")` 변조가 지정한 4개 파일에서 살아남음 | **재현됨** | WU5에서 `@` 두 개짜리 픽스처로 잡음 |


→ 표가 말하는 것: 검증자가 낸 지적 6개 중 5개가 사실이었고 1개(argparse)는 결함이 아니었다. 액면으로 받지 않고 전부 직접 돌려 본 결과다.
②B는 G(생성자)가 자체 공격에서 탭·개행으로 독립 발견한 것과 같은 결함이며, V1이 더 강한
반례(U+2028은 `urlsplit` 이 지우지 않는다)를 냈다.

### 변조 증명 — 최종 (대조군 포함)

첫 시도의 하네스는 복제본에 `contracts/` 가 없어 대조군이 16건 실패하는 잡음 하네스였다.
경로를 바로잡고(`mroot/{humansearch,contracts}`) 대상 시험 9개 파일로 좁혀 다시 쟀다.

| 변조 | 결과 |
|---|---|
| (대조군) 무변조 | **34 passed, exit 0** |
| ① 계약 JSON `ValueError`→`JSONDecodeError` | 1 failed |
| ② 타깃 JSON `ValueError`→`JSONDecodeError` | 2 failed |
| ③ `_readable_port` 검증 제거 | 4 failed |
| ④ 한 줄 계약 가드 제거 | 1 failed |
| ⑤ 인코딩 가드 제거 | 1 failed |
| ⑥ `rpartition`→`partition` | 7 failed |
| ⑦ `_split` 의 `ValueError` 흡수 제거 | 8 failed |
| ⑧ 축약 단계 통째로 건너뜀 | 5 failed |


→ 표가 말하는 것: 고친 자리를 하나씩 일부러 되돌렸더니 전부 시험이 빨개졌다. 좋은 소식 — 살아남은 변조가 없다는 건 이 시험들이 구현을 실제로 붙잡고 있다는 뜻이다.
**살아남은 변조 0건.**

### 남은 위험 — 고치지 않기로 한 것과 그 이유

**`format_observation_line` 의 TAB 필드에 임의 문자열을 심을 수 있다.** 승인 origin 뒤에
공백과 함께 `STATE=authenticated` 를 붙인 주소를 넣으면 출력 한 줄 안에 그 문자열이 들어간다
(실측 5건 중 3건 성공). 다만 그런 netloc 은 허용 origin 과 절대 일치하지 않아 **CLI 경로로는
도달할 수 없다**(선택 단계에서 `found 0`). 고치려면 "netloc 이 어떤 모양이어야 하는가"라는
확정되지 않은 결정을 코드에 넣어야 하므로(SOT-30 §3② 위반) 이번 PR에서는 고치지 않고 기록만
한다. 오너 결정이 필요한 항목이다.

**`_valid_origin` 이 포트 `0` 을 허용한다.** `.port` 가 0 을 정상 반환하므로 "읽을 수 있는가"
규칙으로는 통과한다. "포트 0 은 실주소가 아니다"는 별도 결정이라 넣지 않았다.

**실패 원인이 `STATE=drifted` 한 표기로 뭉개진다.** V1의 지적 (e)와 Codeaudit의 잔여 위험이
같은 것을 가리킨다. 기존 설계와 일관되며 이번 변경이 만든 구멍은 아니다.

**출력을 받는 쪽이 파이프를 먼저 닫으면 종료값이 120 이 된다.** G 자체 공격에서 찾았다.

```
$ python -m humansearch.observe --channel saramin --port 9327 --once > >(exec true)
관측기 종료값: 120
STDERR:
Exception ignored while flushing sys.stdout:
BrokenPipeError: [Errno 32] Broken pipe
```

→ 뭘 시켰나: 출력을 받자마자 닫아 버리는 소비자에게 관측기를 연결했다. 뭐가 나왔나: 종료값 120
과 stderr 두 줄. 좋은 소식 절반 — 개인정보도 우리 코드의 traceback 도 없고, 이건 파이썬이
종료하며 stdout 을 비우다 실패한 것이지 `main()` 을 뚫은 예외가 아니다. 나쁜 소식 절반 —
그래도 계약된 종료값(0·2)이 아니다. 같은 조건에서 `cat` 으로 받으면 정상이다(한 줄, stderr 0줄).

**고치지 않는 이유**: 이 결함은 *입력*이 아니라 *소비자*가 만든다 — 이번 작업의 인수 기준
(AC-1: "주소 자리에 무엇이 들어와도")이 다루는 축이 아니다. 그리고 고치려면 "읽을 사람이
사라졌을 때 무엇으로 끝낼 것인가"를 정해야 하는데, 그건 확정되지 않은 결정이다(§3②).
파이썬 CLI 의 표준 동작이기도 하다. 오너 결정 항목으로 남긴다.

### V1 2회차 — `VERDICT: FAIL` (HEAD `abb1ed7`, transcript `scratchpad/v1_out3.txt`)

WU5 를 얹은 상태를 다시 공격해 네 갈래를 더 냈다. **넷 다 독립 재현했다** — 특히 ①은 내 첫
재현 시도(깊이 2,000)에서 실패했고, 깊이를 300,000 까지 올려서야 재현됐다. V1 말을 못 믿어서가
아니라 못 믿는 게 규칙이라 판 것이고, 결과적으로 V1 이 옳았다.

| V1 지적 | 재현 | 처분 |
|---|---|---|
| ①[HIGH] 깊게 중첩된 JSON 은 `RecursionError` — `ValueError` 가 **아니다** | **재현됨**: 깊이 300,000 = 600KB(1MiB 한계 안) | WU6 — `observe.py` 두 경계 + `_cdp.py` 한 경계에 `RecursionError` 추가 |
| ②[HIGH] `_valid_targets_path` 가 고립 서로게이트 경로를 허용 → HTTP 요청 인코딩(latin-1)에서 `UnicodeEncodeError` | **재현됨** | WU6 — 계약 경로에 `isascii()` 요구 |
| ③[HIGH] 축약 주소 **끝**의 U+2028 은 `splitlines()` 로 1이지만 완성된 줄은 **2줄** | **재현됨**: `'…/home\u2028 ROLES=0…'` → `splitlines()==2` | WU6 — 판정을 개수에서 `"".join(splitlines()) != s` 로 교체 |
| ④ 아홉 번째 변조: `parsed.netloc` → `parsed.hostname` 이 살아남는다(포트 탈락 → `:444` 가 포트 없는 origin 과 일치) | **재현됨** | WU6 — 포트가 origin 비교의 일부임을 고정하는 시험 4건 추가 |

→ 표가 말하는 것: 2회차 지적 네 건이 전부 사실이었다. ③은 내가 1회차 대응으로 넣은 안전장치가 **한 칸 이르게 판정**하고 있었다는 뜻이다 — 안전장치를 넣었다는 사실이 그것이 옳다는 증거가 아니다.

③은 내가 WU5에서 넣은 가드가 **한 칸 이르게 판정**하고 있었다는 뜻이다 — 가드를 넣었다는 사실이
가드가 옳다는 증거가 아니라는 실례다.

### 변조 증명 — WU6 추가분 (대조군 47 passed, exit 0)

| 변조 | 결과 |
|---|---|
| ⑨ 계약 JSON `RecursionError` 제거 | 1 failed |
| ⑩ 타깃 JSON `RecursionError` 제거 | 1 failed |
| ⑪ CDP JSON `RecursionError` 제거 | 1 failed |
| ⑫ 계약 경로 `isascii()` 요구 제거 | 3 failed |
| ⑬ 한 줄 판정을 개수 세기로 되돌림 | 1 failed |
| ⑭ `netloc`→`hostname` (V1 이 지목한 아홉 번째) | 3 failed |

→ 표가 말하는 것: 2회차 대응으로 고친 여섯 자리를 하나씩 되돌렸더니 전부 시험이 빨개졌다. 특히 ⑭는 검증자가 "이 변조는 살아남는다"고 지목한 바로 그 자리다 — 이제 잡힌다.

**누적 변조 14종 · 살아남은 변조 0건.**

### G 자체 퍼징 (1,512 입력)

실제 `main()` 에 적대적 타깃 목록 1,512개를 먹였다 — 제어문자·유니코드 줄분리자·고립
서로게이트·전각문자·합자·널바이트를 섞은 무작위 주소 1,500개 + 깊이 300,000 JSON·자릿수 초과
정수·비UTF8·빈 목록 등 12개.

```
total=1512 crash=0 bad_exit=0 multiline=0
```

→ 크래시 0건, 계약 밖 종료값(0·2 외) 0건, 여러 줄 출력 0건.

### V1 3·4회차 — 판정 줄 없이 잘렸으나 반례는 유효

3·4회차는 **제공자 측 필터에 최종 요약 단계에서 잘려 `VERDICT` 줄이 없다**(둘 다
`ERROR: flagged for possible cybersecurity risk`). 형식상 판정은 미완이므로 "V1 PASS"로 세지
않는다. 다만 잘리기 전 작업 로그에 남은 반례는 각각 독립 재현했고 유효했다.

| 회차 | 반례 | 재현 | 처분 |
|---|---|---|---|
| 3회차 | `HTTPConnection(...)` 생성자가 `try` **밖**(`observe.py:225`)이라, 제어문자가 든 호스트(`::1%\n`)에서 나는 `http.client.InvalidURL` 이 `main()` 을 뚫는다. `ip_address("::1%\n")` 이 루프백으로 판정되기 때문에 계약을 통과한다 | **재현됨** (생성자 단독 호출로 확인) | WU7 — 생성자를 try 안으로, `_is_loopback_address` 에 `isprintable()` 요구 |
| 4회차 | scope id 에 **비ASCII** 문자가 오면(`::1%<히브리문자>`) `isprintable()` 은 True, `ip_address()` 도 루프백 → 통과 후 호스트 IDNA 인코딩에서 `UnicodeEncodeError`(=`ValueError`) | **재현됨** | WU8 — `isascii()` 도 요구 + 전송 `except` 에 `ValueError` 복원 |

→ 표가 말하는 것: 3·4회차는 형식상 판정이 없지만(제공자 필터에 잘림) 잘리기 전에 낸 반례 두 건은 각각 재현됐고 고쳤다. 판정이 없다는 이유로 반례를 버리지 않는다.

### 이 run 에서 내가 틀렸던 판단 (기록)

WU7 직후 변조 시험 ⑯("전송 `except` 에서 `ValueError` 제거")이 **살아남았다**. 나는 이를
"계약 검증이 이미 그 입력을 막으므로 도달 불가한 추측 방어"로 읽고 `ValueError` 를 걷어냈다.
V1 4회차가 곧바로 **도달 경로**(비ASCII scope id)를 찾아냈다.

- **무엇이 틀렸나**: "어떤 시험도 이 가지에 닿지 않는다"를 "이 가지에 닿을 수 없다"로 읽었다.
- **왜 위험한가**: 변조 생존은 *커버리지 부족*의 신호이지 *도달 불가*의 증명이 아니다. 전자의
  올바른 처방은 시험 추가, 후자는 코드 제거인데 정반대를 골랐다.
- **어떻게 고쳤나**: 가드를 복원하고 그 가지에 **실제로 닿는 시험**을 함께 넣었다
  (`test_transport_encoding_failure_is_a_closed_observation_failure`). 이제 변조 ⑱이 죽는다.

### 변조 증명 — 최종 전량 (대조군 56 passed, exit 0)

누적 20종을 최종 코드에 다시 걸었다. ⑮는 대상 문구가 ⑲·⑳으로 대체돼 SKIP 되었고, 나머지
**19종 전부 죽었다. 살아남은 변조 0건.**

| # | 변조 | # | 변조 |
|---|---|---|---|
| ① 계약JSON→JSONDecodeError | 죽음 | ⑪ CDP RecursionError 제거 | 죽음 |
| ② 타깃JSON→JSONDecodeError | 죽음 | ⑫ 계약경로 isascii 제거 | 죽음 |
| ③ `_readable_port` 제거 | 죽음 | ⑬ 한 줄 판정→개수세기 | 죽음 |
| ④ 한 줄 가드 제거 | 죽음 | ⑭ netloc→hostname | 죽음 |
| ⑤ 인코딩 가드 제거 | 죽음 | ⑯ 생성자를 try 밖으로 | 죽음 |
| ⑥ rpartition→partition | 죽음 | ⑰ CDP websocket 가드 제거 | 죽음 |
| ⑦ `_split` 흡수 제거 | 죽음 | ⑱ 전송 except ValueError 제거 | 죽음 |
| ⑧ 축약 단계 건너뜀 | 죽음 | ⑲ 호스트 isascii 제거 | 죽음 |
| ⑨ 계약JSON RecursionError 제거 | 죽음 | ⑳ 호스트 isprintable 제거 | 죽음 |
| ⑩ 타깃JSON RecursionError 제거 | 죽음 | | |

→ 표가 말하는 것: 이번 작업에서 고친 자리 전부를 하나씩 되돌려 봤고, 되돌릴 때마다 시험이 빨개졌다. 좋은 소식 — 통과가 우연이 아니다.

### 실계약 회귀 확인

좁힌 검증이 **실제 운영 계약을 막지 않는지** 확인했다:
`_load_contract('saramin')` → host `127.0.0.1` · origin `https://hiring.saramin.co.kr` ·
loggable `/home` 로 정상 로드된다.

### V2 (2차 적대검증)

(후기록)
