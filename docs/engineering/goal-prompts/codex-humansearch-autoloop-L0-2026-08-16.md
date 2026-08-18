# CODEX 자율 하네스 프롬프트 — HumanSearch L0 로그인 상태 뼈대 (2026-08-16)

> **대상 실행자: Codex (GPT-5.6, SOL, reasoning=xhigh).** 이 문서를 통째로 codex에 붙여넣고 자율 실행시킨다.
> **성격: 구현 프롬프트 = 계약 + 게이트 + 정본 전이표.** 아래 전이표는 **이미 확정됐다.** 너는 표를 바꾸지 말고 구현만 한다.
> 정본 계약: `worktrees/humansearch-clean-room-plan/docs/engineering/humansearch-v6-clean-room-rebuild-goal-2026-08-12.md`(이하 "계약").

---

## 0. 실행자에게 (Codex — 반드시 먼저 읽어라)

너는 **구현자(G)**다. 아래 규칙을 어기면 이 작업은 실패다.

**A. 자율 루프 규칙.** 아래 마이크로 단계 M1→M5를 **순서대로 자동 진행**한다. 각 단계는 `RED(실패 시험 먼저) → GREEN(최소 구현) → 검증 → 커밋`을 밟는다. 한 단계의 종료 조건을 만족하기 전에는 다음 단계로 넘어가지 않는다.

**B. 절대 금지 (GPT 계열 자율 실행에서 자주 나오는 사고 — 하나라도 하면 실패):**
- **테스트를 구현에 맞추지 마라. 구현을 계약(§2 전이표)에 맞춰라.** 시험이 빨간불이면 시험이 아니라 구현을 고친다.
- **전이표(§2)를 임의로 바꾸지 마라.** 표에 없는 전이가 필요해 보이면 **그 자리에서 STOP**하고 `## 실행자 질문` 파일에 "어느 (상태,신호) 쌍이 표에 없는데 필요하다고 판단했는지 + 계약 근거 줄"을 적고 멈춘다. 추측으로 채우지 마라.
- **"완료했다"를 먼저 선언하지 마라.** 완료의 정의는 이 문서 §5의 종료 조건(verify exit 0 + 커밋 SHA + push 성공)이다. 그 증거 없이 완료라 쓰지 마라.
- **DOM 셀렉터·URL 문자열·특정 사이트 이름(saramin/jobkorea/linkedin)을 상태기계 코드에 넣지 마라.** L0는 의미 역할(role)만 소비한다(계약 :259 "코드에는 DOM 지식이 없다").
- **시계·난수·네트워크·파일 I/O를 상태 판정에 쓰지 마라.** 같은 입력 → 항상 같은 출력(결정론).

**C. 커밋/푸시.** 각 마이크로 단계 끝에 **로컬 커밋**한다(메시지 형식 §4). L0 전체(M1~M5) + verify 통과 후 **한 번 push**하고 PR을 연다(§5). `git commit`이 `index.lock` 권한 오류(exit 128)로 막히면 커밋하지 말고 변경을 남긴 뒤 `## 실행자 질문`에 "커밋 권한 없음, 사람이 커밋 필요"라고 적고 그 단계까지의 작업을 보존한다. `git push`는 pre-push 훅을 반드시 통과해야 한다(우회 `--no-verify` 금지).

**D. 멈춤 게이트(사람 호출).** L0는 순수 로직이라 끝까지 자율로 간다. 그러나 **L0 다음 단계(C1 = 실제 사람인 화면 캡처)는 라이브·개인정보 접촉이라 자율 금지**다. L0 PR을 연 뒤에는 **STOP**하고 §6 브리핑만 남긴다. C1을 시작하지 마라.

**E. 언어.** 모든 산출 보고·PR 본문·질문은 한국어 존칭체. 문서 맨 앞은 전문용어 없는 "결론". (상세 형식 §7)

---

## 1. 게이트 0 — 시작 자격 (레포 규칙 회수)

1. 작업 폴더: 새 워크트리 `worktrees/humansearch-L0`, 브랜치 `task/humansearch-L0`, base = 현재 `origin/main`. (`git worktree add worktrees/humansearch-L0 -b task/humansearch-L0 origin/main`)
2. 검증 명령 정본은 `docs/sot/verification-commands.md`를 읽어 확정한다(추측 금지). 게이트 0 = `bash scripts/session-status.sh`, 게이트 4 = `bash verify.sh`로 기재돼 있음을 확인하고 그대로 쓴다.
3. 과거 회수: `git log --oneline --all | grep -i "L0\|state.*machine\|상태기계"` — 이미 만든 L0가 있으면 이어서, 없으면 신설(현재 없음).
4. 제품 패키지 위치 = `humansearch/src/humansearch/`. 파이썬. 테스트는 `humansearch/tests/`(계약이 정한 위치를 따른다).

---

## 2. L0 계약 (정본 — 이대로 구현. 표를 바꾸지 마라)

### 2-1. 상태 집합 (7개) — 계약 근거 명시

계약 :241-243 전이 다이어그램 + :247 + :274 + :397에서 확정. **각 상태 정의 옆 괄호가 계약 근거 줄이다.**

| 상태 | 뜻 | 계약 근거 |
|---|---|---|
| `UNKNOWN` | 화면 판정 전/모름 (초기 상태) | :241 |
| `HUMAN_AUTH` | 미로그인 감지 → 사람 로그인 대기(park) | :242, :247 |
| `RECHECK` | 사람 로그인 후 인증 재확인 중 | :242, :397 |
| `AUTHENTICATED` | 인증 확인됨 (L0의 성공 종점) | :241 |
| `CHALLENGE` | 캡차·2단계 인증 감지 (terminal) | :243 |
| `AUTH_CONFLICT` | 세션 충돌 감지 (terminal) | :243 |
| `DRIFTED` | 화면 구조가 계약과 어긋남, 텍스트 저장 안 함 (terminal) | :274 |

**범위 밖(구현 금지):** `RUNNING`(실제 순회 = L2 이후 :241), `STOP`(상태가 아니라 terminal 상태들의 공통 종료 표식 — `is_terminal()` 함수로 표현). 이 둘을 State enum에 넣지 마라.

### 2-2. 신호(Signal) — 화면에서 읽은 의미 역할 집합 (구체 셀렉터 아님)

```python
# 의미 역할 이름. 구체 DOM/CSS/URL 아님. 화면 관측을 이 role 집합으로 추상화한다.
Role = Literal[
    "login_required",    # 미로그인 표식이 보임
    "auth_confirmed",    # 인증됨 표식이 보임
    "challenge_present", # 캡차·2FA 표식이 보임
    "session_conflict",  # 세션 충돌 표식이 보임
    "structure_drift",   # 계약이 기대한 구조가 깨짐
    "human_login_done",  # 사람이 로그인을 마쳤다는 표식 (RECHECK 트리거)
]
Signal = frozenset[Role]   # 한 화면에서 동시에 여러 role이 관측될 수 있음. 빈 집합 = 아무것도 못 읽음.
```

### 2-3. 전이표 (current, signal_role) → next — 정본

**규칙:** 한 화면의 Signal(role 집합)에서 **우선순위가 가장 높은 role 하나**로 전이를 결정한다. 우선순위(위험한 것 먼저): `structure_drift > session_conflict > challenge_present > login_required > human_login_done > auth_confirmed`. 이 우선순위는 fail-closed(위험·미확정을 안전한 쪽으로) 원칙이다 — 인증(auth_confirmed)이 가장 낮아, 다른 위험 신호가 하나라도 있으면 인증으로 안 넘어간다.

| current | 결정된 role | next | 근거/의미 |
|---|---|---|---|
| `UNKNOWN` | `login_required` | `HUMAN_AUTH` | :247 미로그인 park |
| `UNKNOWN` | `auth_confirmed` | `AUTHENTICATED` | :241 |
| `UNKNOWN` | `challenge_present` | `CHALLENGE` | :243 |
| `UNKNOWN` | `session_conflict` | `AUTH_CONFLICT` | :243 |
| `UNKNOWN` | `structure_drift` | `DRIFTED` | :274 |
| `UNKNOWN` | (빈 집합) | `UNKNOWN` | 아직 모름 — 유지(무한 방지는 상위 러너 책임, L0 밖) |
| `HUMAN_AUTH` | `human_login_done` | `RECHECK` | :242, :397 |
| `HUMAN_AUTH` | `login_required` | `HUMAN_AUTH` | 아직 미로그인 — 유지 |
| `HUMAN_AUTH` | `challenge_present` | `CHALLENGE` | 로그인 중 캡차 |
| `HUMAN_AUTH` | `session_conflict` | `AUTH_CONFLICT` | |
| `HUMAN_AUTH` | `structure_drift` | `DRIFTED` | |
| `RECHECK` | `auth_confirmed` | `AUTHENTICATED` | :397 |
| `RECHECK` | `login_required` | `HUMAN_AUTH` | 로그인 실패 → 다시 대기 |
| `RECHECK` | `challenge_present` | `CHALLENGE` | |
| `RECHECK` | `session_conflict` | `AUTH_CONFLICT` | |
| `RECHECK` | `structure_drift` | `DRIFTED` | |

**Terminal 상태 (전이 없음):** `AUTHENTICATED`(L0 종점), `CHALLENGE`, `AUTH_CONFLICT`, `DRIFTED`. terminal 상태에서 어떤 신호가 와도 자동 전이하지 않는다(계약 L3 :398 "캡차·2FA·세션충돌은 terminal, 자동 제출·재시도 없음"). `is_terminal(state) -> bool`로 표현.

**Illegal transition:** 위 표에 없는 (current, 결정된 role) 쌍 → `raise IllegalTransition(current, role)`. 절대 조용히 아무 상태나 반환하지 마라(이게 v5의 "미로그인을 인증으로 착각" 사고 경로다).

### 2-4. 함수 시그니처 (이대로 구현)

```python
class IllegalTransition(Exception): ...

def decide_role(signal: Signal) -> Role | None:
    """우선순위(2-3)로 signal에서 role 하나 선택. 빈 집합이면 None."""

def transition(current: State, signal: Signal) -> State:
    """빈 집합이면 규칙표의 (current, 빈) 행을 따른다.
       terminal 상태면 IllegalTransition (또는 current 유지 — 아래 counter-AC 참조).
       표에 없는 쌍이면 raise IllegalTransition."""

def classify(signal: Signal) -> State:
    """UNKNOWN에서 시작한 1스텝 판정. 빈 집합이면 절대 AUTHENTICATED 아님(fail-closed)."""

def is_terminal(state: State) -> bool: ...
```

---

## 3. 마이크로 단계 M1~M5 (순서대로 자율 진행)

각 단계: **RED 커밋 → GREEN 커밋** (또는 계약 정의 단계는 단일 커밋). RED은 "기대 동작이 없어서" 실패해야 한다(문법 오류로 빨간 건 무효).

- **M1 (계약 타입).** `humansearch/src/humansearch/login_state.py`에 State enum(7개)·Role·Signal 타입·`IllegalTransition`·`is_terminal()` 정의. 로직 없음. 단일 커밋 `L0 M1: 상태·역할 타입 계약 고정`.
- **M2 (전이표 + illegal).** RED: `test_transition_illegal` — 표에 없는 (상태,신호) 쌍이 `IllegalTransition`을 내야 한다는 시험(현재 미구현이라 실패). GREEN: 전이표(2-3) + `transition()` 구현. 표는 **데이터(dict)로** 두고 코드 분기로 흩지 마라(계약 대조 가능하게). 커밋 `L0 M2 RED/GREEN`.
- **M3 (classify + 빈화면 fail-closed).** RED: `test_classify_empty_not_authenticated` — 빈 Signal → 결과가 AUTHENTICATED가 **아님**(현재 실패). RED: `test_priority_drift_beats_auth` — {structure_drift, auth_confirmed} 동시 관측 시 DRIFTED(위험 우선). GREEN: `decide_role()`·`classify()` 구현. 커밋.
- **M4 (property test).** `test_transition_property` — 무작위로 (State, Signal) 다수(예: 1000건) 생성해 "정의된 쌍은 표와 일치, 정의 안 된 쌍은 전부 IllegalTransition, terminal은 자동전이 없음"을 검증. hypothesis 등 성질 시험 라이브러리가 저장소에 있으면 쓰고, 없으면 시드 고정한 순수 파이썬 무작위(단 상태 판정 자체엔 난수 금지 — 시험 입력 생성에만). 커밋 `L0 M4: property test`.
- **M5 (셀렉터 금지 + 배선).** `login_state.py`에 DOM 셀렉터·URL·사이트명 리터럴 0건임을 확인하는 시험(grep 기반) 추가. `humansearch/src/humansearch/__init__.py`에서 공개 API export. 커밋 `L0 M5: 셀렉터 0건 게이트 + export`.

---

## 4. 커밋 메시지 형식

```
L0 <단계>: <한 줄 요약>

<RED이면 "왜 지금 실패하는가", GREEN이면 "어느 AC를 통과시키나">

Co-Authored-By: Codex GPT-5.6 <noreply@openai.com>
```

---

## 5. L0 페이즈 종료 조건 (전부 만족해야 "완료")

1. `cd worktrees/humansearch-L0 && bash verify.sh` → **exit 0**. 출력 숫자를 그대로 기록.
2. M1~M5 커밋이 전부 존재(각 SHA 기록).
3. 뮤테이션 자가 점검: `transition()`의 전이표 한 줄을 임시로 틀리게 바꿔 관련 시험이 빨개지는지 확인 후 원복(시험이 진짜 잡는지 증명).
4. **적대적 자기검증 (계약 위반 입력 탐색):** 다음을 각각 시도해 시험이 막는지 확인하고 결과를 `## 적대 검증 로그`에 기록 — ⑴ 빈 Signal이 AUTHENTICATED로 새는 경로 ⑵ terminal 상태에서 자동 전이하는 경로 ⑶ 우선순위 무시(auth가 drift를 이기는) 경로 ⑷ 표에 없는 쌍이 조용히 통과하는 경로. (이건 "우회 탐색"이 아니라 "계약 위반 입력에 대한 방어 확인"이다.)
5. `git push origin task/humansearch-L0` → pre-push 훅 통과. PR 생성(base main). PR 본문은 §7 형식.
6. **여기서 STOP.** C1(사람인 캡처) 시작 금지. §6 브리핑만 남긴다.

---

## 6. L0 완료 후 브리핑 (사장님용 — codex가 작성)

`## 브리핑` 파일 또는 PR 본문에 §7 형식으로:
1. L0(상태 뼈대)가 병합 준비됐는지, verify exit 0·PR 번호·커밋 SHA.
2. 다음 = C1(사람인 화면 첫 접촉, 라이브·개인정보라 위험 오름). 착수 전 필요조건: 사장님 로그인 세션 + 계약 :576 [BLOCKING](마스킹 fixture vs role/name 매칭 모순) 해소.
3. **결정 카드**: 다음을 ⑴ C1으로 갈지 ⑵ 계약 :576 blocker부터 풀지 ⑶ 다른 순수 단계(S1 점수 순수함수)를 먼저 할지. 각 대가·되돌리기.
4. 정직 표기: L0는 순수 로직이라 "실제 후보 찾기"까지 아직 여러 단계 남음(로드맵 위 현위치 한 줄).

---

## 7. 출력 형식 (모든 보고·PR·질문에 적용)

[출력 형식 — 반드시 지킬 것]
읽는 사람은 기술 배경이 없는 사업 책임자다. 내용은 축소하지 말고 표현만 풀어 써라.
1) 맨 앞 "결론"(전문용어 0개, 결정할 사항 명시). 2) "판단 근거"(왜 이 길, 버린 길, 틀리면 뭐가 깨지나). 3) 기술 상세·명령·출력·file:line 전문.
- 전문용어는 첫 등장 문장에서 괄호로 풀어 써라. 터미널 출력·코드 블록 아래에 "→ 뭘 시켰나/뭐가 나왔나/좋은·나쁜 소식" 1~3줄. file:line 인용엔 그 줄이 하는 일 한 마디. 결함마다 사업 영향 한 문장. 건너뛴 것·확인 못 한 것·실패 후 재시도한 것을 앞부분에 명시. 추정은 ※. 한국어 존칭체. 초등학생 비유 금지.

---

## 8. ⚠️ 계약 불확정 경고 (실행 전 반드시 인지)

이 전이표(§2)는 **클린룸 계약을 근거로 확정했으나, 계약 자체가 문서 안에서 상태 집합을 두 곳에서 다르게 적었다** — :377은 5개 상태(UNKNOWN/HUMAN_AUTH/AUTHENTICATED/CHALLENGE/DRIFTED), :241 다이어그램은 RECHECK·AUTH_CONFLICT·RUNNING·STOP까지 더 나온다. 이 프롬프트는 그 불일치를 "다이어그램(:241)을 정본으로, RUNNING/STOP은 L0 범위 밖"으로 **해석해 확정**했다(§2-1 근거표). **이 해석이 사장님 의도와 다르면, 구현 전에 §2-1 상태 집합부터 정정해야 한다.** codex는 이 표를 정본으로 삼되, 구현 중 표로 설명 안 되는 계약 문장을 만나면 STOP하고 질문한다.
