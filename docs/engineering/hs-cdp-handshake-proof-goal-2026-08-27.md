# CDP 핸드셰이크 증명이 무방비다 — goal (2026-08-27)

등급: **L3** (관측기가 "누구와 이야기하는가"를 확정하는 경계 · 무력화 시 위조된 인증 관측 수용)
워크트리: `worktrees/hs-cdp-handshake-proof` · 브랜치 `task/hs-cdp-handshake-proof` · base `3276712`

## 1층 — 결론

관측기가 CDP WebSocket으로 붙을 때, 상대 응답이 우리가 보낸 키에 대한 RFC 6455 upgrade 증명인지
확인하는 절차가 코드에는 있는데 **그 절차를 지키는 시험이 하나도 없다.** 그 한 줄을 지워도 시험 118건이 전부 통과한다.

지우면 무슨 일이 나느냐 — 틀린 WebSocket upgrade 응답도 통과해 이후 CDP 메시지 읽기 단계로 넘어갈 수 있다.
단, 이 검사는 브라우저 프로세스 신원, Aside 프로필, PID, 로그인 상태를 증명하지 않는다.

원인이 하필 **내가 지난 변경에서 쓴 시험들**에 있다. 세 시험 파일이 전부 그 확인 절차를 가짜로
바꿔치기하고 지나갔다 — 지켜야 할 것을 시험이 치워 버린 것이다.

## 상위 목표 (1문장)

관측기가 CDP WebSocket upgrade 무결성 검사를 제품 진입 경로에서 지키게 한다 — 성공 신호:
핸드셰이크 accept 검사를 지우면 시험이 반드시 빨개진다.

## 읽은 SOT

- `docs/sot/humansearch-browser-contract.md` §6(진단 포트·프로토콜 확인) · §7(목표 탭 계약) ·
  §12(개인정보 경계) — "포트 응답 하나만으로 프로필·채널·탭·로그인 일치를 증명하지 못한다"
- `docs/sot/humansearch-l0-surface-contract.md` — `AUTHENTICATED` 는 화면 분류 결과일 뿐
- `docs/sot/coding-principles.md` P13(검사는 약화될 수 없다) · P16(런타임 동작 검사) ·
  P20(0건 처리 의심)

## 과거 회수 (R4)

- 재발 원장 `docs/sot/31-strict-recurrence-ledger.md` 는 이 저장소에 **없다**(실행 확인).
- 회수한 자기 지침: "변조 생존은 커버리지 부족이지 도달 불가가 아니다" — PR #42 에서 세 번
  걸린 함정이다. 이번 건도 같은 뿌리다: 내 변조 24종 목록이 **내가 손댄 곳만** 보고 있었고,
  Codex 가 목록 밖을 찔러 찾았다.

## 현재 상태 (실행 확인)

`humansearch/src/humansearch/_cdp.py:136`

```python
    expected = base64.b64encode(
        hashlib.sha1(f"{key}{_WEBSOCKET_GUID}".encode("ascii")).digest()
    ).decode("ascii")
    if headers.get("sec-websocket-accept") != expected:
        raise CdpReadError("DevTools websocket handshake proof was invalid")
```

→ 이 줄이 하는 일: 서버가 우리가 보낸 임의 키로 RFC 6455 accept 값을 계산했는지 본다.
이것은 WebSocket upgrade 응답 무결성 검사이지 브라우저·프로필·로그인 신원 증명이 아니다.

### 변조 실측

`if headers.get(...) != expected:` → `if False:`

```
exit=0 | 118 passed in 4.93s
```

→ 뭘 시켰나: 위조된 증명을 수락하게 만들었다. 뭐가 나왔나: 시험이 하나도 안 죽었다.
나쁜 소식 — 이 프로토콜 무결성 경계는 지금 아무 시험도 지키지 않는다.

### 왜 무방비였나

```
humansearch/tests/test_observe_adversarial_v1_round2.py:106
humansearch/tests/test_observe_adversarial_v2_findings.py:187
humansearch/tests/test_observe_closed_failure_branches.py:192
  → 셋 다 monkeypatch.setattr(_cdp, "_handshake", lambda *args: None)
```

→ PR #42 에서 내가 쓴 시험들이다. 읽기 루프를 시험하려고 핸드셰이크를 치웠는데, 그 결과
핸드셰이크 자체를 보는 시험이 저장소에 0건이 됐다.

## 근본 원인

변조 목록을 **내가 바꾼 코드 기준**으로 만들었다. `_handshake` 는 PR #42 가 건드리지 않은
base 코드라 목록에 없었고, 그래서 "살아남은 변조 0건"이 이 함수에 대해서는 아무 말도 하지
않았다.

## ① 입력 영역 표 — 핸드셰이크 응답

명시 입력: 서버가 돌려준 응답 헤더 뭉치. 암묵 입력: 우리가 방금 보낸 임의 키(`Sec-WebSocket-Key`).

| # | 입력 | 처리 |
|---|---|---|
| 1 | 정상 101 + 올바른 증명 | 통과 |
| 2 | 101 인데 증명이 틀림 | `CdpReadError("handshake proof was invalid")` |
| 3 | 101 인데 증명 헤더가 아예 없음 | 같음(`headers.get` → None ≠ expected) |
| 4 | 상태줄이 101 이 아님 | `CdpReadError("handshake was rejected")` |
| 5 | 헤더 뭉치가 16KB 초과 | `CdpReadError("handshake was too large")` |
| 6 | 헤더 뒤에 데이터가 붙어 옴 | `CdpReadError("unexpected data followed")` |
| 7 | 연결이 헤더 도중 끊김 | `CdpReadError("handshake ended early")` |
| 8 | 그 외 전부 | 명시적 거부 — 열린 채로 두지 않는다 |

→ 표가 말하는 것: 코드는 여덟 행을 이미 다 처리한다. 없는 것은 **2·3행을 지키는 시험**이다.

## ② 결정 목록

| 결정 | 확정값 | 근거 |
|---|---|---|
| 증명이 틀리면 재시도하나 | **아니다** — 즉시 `CdpReadError` | 브라우저 계약 "주 경로 실패 시 자동 전환하지 않고 중단" |
| 오류 메시지에 증명값·키를 넣나 | **아니다** | §12 — 세션 자격에 준하는 값이다 |
| 코드를 바꾸나 | **아니다 — 시험만 추가** | 코드는 이미 옳다. 없던 것은 그 옳음을 지키는 것 |

→ 표가 말하는 것: 이번 작업은 제품 코드를 한 줄도 건드리지 않는다. 고칠 것이 없어서가 아니라,
고칠 것이 **시험 쪽**에 있기 때문이다.

## 인수 기준 (EARS)

**AC-1** — 서버가 `Sec-WebSocket-Accept` 를 틀리게 주거나 아예 주지 않으면 `_handshake` 는
`CdpReadError` 로 거부하고, 그 메시지에 증명값이나 우리 키가 들어가지 않는다.

- 검증: `uv run pytest tests/test_cdp_handshake_proof.py -q` (exit 0)
- counter-AC: `if headers.get(...) != expected:` 를 `if False:` 로 바꾸면 반드시 실패한다.

**AC-2** — 정상 증명은 그대로 통과한다(거부 방향으로만 좁힌다).

## R1 작업 분해표

| WU | AC | 파일 | focused 검증 |
|---|---|---|---|
| WU1 | AC-1·AC-2 | `tests/test_cdp_handshake_proof.py` (신규, 시험만) | 같은 파일 + 변조 |

→ 표가 말하는 것: 작업 단위가 하나뿐이다. 범위를 좁게 유지해 지난번처럼 16개로 불어나지 않게 한다.

코드 변경 0줄이므로 RED 대신 **변조 증명**으로 공허하지 않음을 보인다.

## R1 예외 케이스 표

| 상황 | 처리 |
|---|---|
| 소켓 없이 `_handshake` 를 시험할 수 없음 | 가짜 소켓으로 `sendall`/`recv` 를 주입(자동 처리) |
| 실제 브라우저가 필요해짐 | 명시적 중단 — 사장님 크롬(9225) 접속 금지 |
| 기존 시험 211건 중 하나라도 깨짐 | 명시적 중단, 원인 회수 |
| 그 외 전부 | 명시적 중단 + 이 표 갱신안 |

→ 표가 말하는 것: 표에 없는 상황을 만나면 임의로 판단하지 않고 멈춘다. 특히 사장님 크롬은
읽기조차 하지 않는다 — 지난 작업에서 그 약속을 한 번 어겼다.

## 게이트 계획

시험 추가 → focused test → 변조 증명 → 전체 시험 → 인수 검사 전량 → `verify.sh` →
Codeaudit → 적대검증 → push → PR → CI. **merge 안 함.**

## 적대검증 정조준

1. 가짜 소켓이 실제 `_handshake` 를 태우는가, 아니면 또 몽키패치로 치우는가
2. 새 시험이 제품 `_WEBSOCKET_GUID` 를 재사용해 제품 상수 오류와 함께 틀어지지 않는가 — RFC 6455 고정 GUID와 공식 벡터로 따로 고정하는가
3. `if False:` 말고 **다른 방향의 변조**(예: `expected` 계산을 상수로)도 잡는가
4. 기존 세 시험의 `_handshake` 몽키패치를 그대로 둬도 되는가 — 그것이 이 구멍의 원인이었다

## 롤백 절차 (L3)

`git revert <GREEN SHA>` 하나. 시험만 추가하므로 제품 동작에 영향이 없다.

## 영향 반경 (L3)

`humansearch/tests/` 신규 1파일. 제품 코드 0줄.

## 배포 후 관측 항목 (L3)

- `CdpReadError("DevTools websocket handshake proof was invalid")` 가 로그에 뜨면 그 포트에
  브라우저가 아닌 것이 앉아 있다는 뜻이다 — 즉시 조사.

## 비범위

- 기존 세 시험의 `_handshake` 몽키패치 제거(그 시험들은 읽기 루프를 보는 것이 목적이다)
- CDP 연결·브라우저 기동(D1 소유, `NOT_RUN`)

## 적대 검증 로그

### 변조 증명 (대조군 124 passed, exit 0)

정조준 3번대로 `if False:` 하나가 아니라 **방향이 다른 네 갈래**로 걸었다.

| 변조 | 무엇을 흉내 내나 | 결과 |
|---|---|---|
| M1 증명 검사 무력화 (`if False:`) | Codex 가 지목한 그 한 줄 | **3 failed** |
| M2 존재만 확인(값은 무시) | 헤더는 있는데 값이 틀린 서버 | **2 failed** |
| M3 우리 키를 빼고 계산(고정 상수화) | 누구나 미리 알 수 있는 증명 | **2 failed** |
| M4 상태줄 101 검사 제거 | 웹소켓으로 승격하지 않은 응답 | **1 failed** |

→ 표가 말하는 것: 넷 다 죽는다. 특히 M3 는 "정답을 픽스처에 심지 않았는가"를 보는 시험이
잡는다 — 매번 새로 생기는 키로 증명이 계산되는지 확인하기 때문이다.

### 이번 run 에서 내가 저지른 것 (숨기지 않고 적는다)

워크트리를 만들며 `humansearch/.venv` **심볼릭 링크**를 걸었는데, `.gitignore` 에는
`.venv/`(슬래시 포함)만 있어 링크는 걸리지 않았고 `git add -A` 가 그대로 커밋했다(`e34e7a9`).

```
$ bash verify.sh
FAIL: scanner error — fail-closed (grep/xargs stderr):
  ! grep: humansearch/.venv: Is a directory
종료값=1
```

→ 뭘 시켰나: 비밀 스캔을 돌렸다. 뭐가 나왔나: 스캐너가 링크를 디렉터리로 만나 오류를 냈고,
검사기가 fail-closed 로 실패했다. 좋은 소식 — 검사기가 제 할 일을 했다. 나쁜 소식 — 내가
추적하면 안 되는 것을 커밋했다.

처분: 추적에서 빼고(`git rm --cached`), `.gitignore` 에 슬래시 없는 `.venv`·`node_modules` 를
더해 같은 함정을 막았다. 링크를 실제로 만들어 `git status` 에 안 뜨는 것까지 확인했다.
`main` 에는 추적된 심볼릭 링크가 0건이라 내 워크트리만의 문제였다.

**왜 기록하나**: 이 저장소의 규약이 "워크트리 생성 직후 node_modules·env 링크"인데, 그 규약을
따르면 누구나 같은 곳을 밟는다. 문서가 아니라 `.gitignore` 로 막는 것이 옳다.

### 남은 위험

- 기존 시험 셋(`test_observe_adversarial_v1_round2.py` 등)은 여전히 `_handshake` 를 몽키패치로
  치운다. 그 시험들의 목적은 읽기 루프라 그대로 두되, **이제는 핸드셰이크를 보는 시험이 따로
  있다.** 같은 함정이 다시 생기지 않으려면 "몽키패치로 치운 함수는 어딘가에서 실제로 태워야
  한다"는 규칙이 필요한데, 그것을 기계로 만드는 것은 이 작업의 범위 밖이다.

### 2026-09-14 회수 보강 — 실제 localhost 소켓 경로

9월 14일 v5 실행 지시 회수 뒤 확인한 결론: 기존 WU1 시험은 `_handshake` 를 몽키패치하지 않는
가짜 소켓 단위 시험으로는 충분했지만, `observe_markers()` 가 `socket.create_connection()` 으로
로컬 소켓을 열고 CDP 응답을 받는 관통 경로는 비어 있었다. 그래서 같은 파일에 localhost 합성
서버를 추가했다.

추가한 경계:

- 정상 서버: 실제 로컬 포트에서 올바른 `Sec-WebSocket-Accept` 를 계산하고 CDP 결과 프레임을
  돌려주면 `observe_markers()` 가 값을 반환한다.
- 잘못된 WebSocket upgrade 응답: 틀린 증명 또는 증명 헤더 없음 뒤에 정상처럼 CDP 결과를 돌려줘도 클라이언트는
  `handshake proof was invalid` 로 거부한다.
- 중간 종료 서버: 헤더 전에 연결이 끊기면 값 반환 없이 `CdpReadError` 로 닫힌 실패가 된다.

변조 재실행:

```
_cdp.py 의 검증 조건을 `if False and headers.get("sec-websocket-accept") != expected:` 로 바꿈
$ uv run pytest tests/test_cdp_handshake_proof.py -q
5 failed, 6 passed in 0.41s
```

→ 무엇을 시켰나: 증명 검사를 일부러 무력화했다. 무엇이 나왔나: 기존 가짜 소켓 거부 3개와 새
localhost 관통 거부 2개가 실패했다. 좋은 소식: accept 검증 생략은 단위 함수와 실제 로컬 소켓 진입 경로
양쪽에서 빨간불이 된다.

검증:

```
$ uv run pytest tests/test_cdp_handshake_proof.py tests/test_cdp_websocket_parse_failure.py -q
13 passed in 1.04s

$ uv run pytest -q
222 passed in 12.90s

$ uv run ruff check .
All checks passed!

$ uv run mypy src tests
Success: no issues found in 42 source files

$ bash verify.sh
PASS: no secret-pattern match in any tracked file, .env not tracked

$ bash scripts/acceptance-hs-gates.sh
PASS: ruff clean in 42 python files
PASS: mypy strict clean in 42 source files
PASS: pytest collected 221 and passed
PASS: runtime import proof /Users/kangsangmo/Desktop/Valuehire_v6/worktrees/hs-cdp-handshake-proof/humansearch/src/humansearch/__init__.py
COLLECTED: 221
```

→ 무엇을 시켰나: 변경 파일 중심 시험, HumanSearch 전체 시험·정적 검사, 저장소 비밀 스캔과
HumanSearch 게이트를 돌렸다. 무엇이 나왔나: 변경 범위 검사는 모두 통과했다.

원격 CI 재현:

```
$ gh run view 33030699472 --log-failed
FAIL: 만료된 억제 (expiry 2026-08-26 < 오늘 2026-08-27)

$ bash -lc '<CI 억제 만료 스캔과 같은 비교식>'
FAIL: 만료된 억제 (expiry 2026-08-26 < 오늘 2026-09-14)
```

→ 무엇을 시켰나: PR54의 원격 실패 로그를 다시 읽고 같은 억제 만료 판정을 현재 날짜로 재현했다.
무엇이 나왔나: PR54의 원격 실패 원인은 `suppressions.yaml` 의 공유 검증정책 만료 항목이다.
이 항목은 HS-01.02 테스트 보강과 별개라 이 작업에서는 수정하지 않는다.
