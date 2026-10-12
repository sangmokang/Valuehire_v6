# goal — 토큰 절약 전략 실증: 상세 스펙 → 저비용 구현 → 이중 검증

작성: 2026-08-10 · 등급: **L2** (코드 변경, 실험 워크트리 격리, 프로덕션 배선 없음)
워크트리: `worktrees/token-strategy-bench/` · 브랜치: `task/token-strategy-bench`
사장님 지시 원문: "Fable로 아주 상세한 .md를 만들고 → 이걸 코덱스에서 구현 → 이중 검증. 토큰 아끼는 방안으로 어떤가? 일단 Fable로 동일하게 테스트 한 번 해보자. v5 aisearch 로직을 그대로 가져와 여기서 구현하고, 동일한 프롬프트를 코덱스로 구현한 것과 품질 테스트."

---

## ① 현재 상태 (전부 실행으로 확인, 추측 없음)

| 사실 | 근거 |
|---|---|
| v6는 앱 코드 0줄 — git 추적 46파일이 전부 문서·훅·검증 스크립트 | `git ls-files \| wc -l` → 46 |
| v6에 `Makefile`·`package.json` 없음 | `make -n red-ledger` → `No rule to make target` |
| v6 게이트 명령은 셸 스크립트 정본 | `docs/sot/verification-commands.md` |
| 게이트 0 통과 상태 | `bash scripts/session-status.sh` → `HEAD: ec201dc (synced)` / `RED: 1/4 (acceptance-0-7.sh 제외 — CI 담당)` |
| v5 aisearch 규모 = 소스 3,605줄 + 테스트 5,674줄 | `wc -l apps/aisearch/**/*.py`, `wc -l tests/test_aisearch_*.py` |
| 벤치 대상 `apps/aisearch/core/boolean_builder.py` = 200줄 | `wc -l` |
| 그 정답지 `tests/test_aisearch_ac1_boolean.py` = 381줄 / **48 tests** | `wc -l` + pytest |
| 정답지가 v5에서 실제로 초록 | `env PYTHONDONTWRITEBYTECODE=1 .venv-playwright/bin/python -m pytest -p no:cacheprovider tests/test_aisearch_ac1_boolean.py -q` → **`48 passed in 0.04s`** |
| 대상 모듈 외부 의존 = **pytest 하나뿐** | `grep -n "^import\|^from"` → `copy` `re` `dataclasses` `typing`(표준) + `seoul_universities`(import 0줄, 순수 데이터) |

### 모델 단가 (2026-08-10 `claude-api` 스킬 회수값, 100만 토큰당 입력/출력)

| 모델 | 입력 | 출력 |
|---|---|---|
| Claude Fable 5 | $10 | $50 |
| Claude Opus 5 | $5 | $25 |
| Claude Sonnet 5 | $3 ($2 인트로) | $15 ($10 인트로) |
| Claude Haiku 4.5 | $1 | $5 |

**Fable은 Opus의 2배 단가다.** 사장님 가설("Fable로 스펙 → 값싼 도구로 구현")이 성립하려면, 스펙 단계의 토큰량이 구현 단계보다 충분히 작아야 한다. 이 실험이 그 비율을 실측한다.

※ 확인 안 된 사항: 사장님은 Max 정액제 + Codex 구독을 쓰신다. 위 단가표는 API 종량 기준이므로 **실제 지출과 직결되지 않는다.** 절약 대상이 "달러"가 아니라 "Max 사용량 한도"라면 환산식이 달라진다 — 이번 범위에서 결론 내지 않는다(§⑦ 비범위).

---

## ② 근본 원인 (무엇을 모르는가)

"비싼 모델로 스펙을 쓰고 값싼 도구로 구현하면 이득"이라는 명제는 **두 개의 미검증 가정** 위에 서 있다.

1. **품질 가정** — 충분히 상세한 스펙이 있으면 값싼 구현자도 비싼 구현자와 동등한 품질을 낸다.
2. **경제 가정** — 스펙 작성 토큰 + 값싼 구현 토큰 < 비싼 구현 토큰.

증상(막연히 아낄 것 같다)이 아니라 원인(두 가정이 참인가)을 재야 한다. 이 실험은 **가정 1을 직접 측정**하고, 가정 2는 실측 토큰량을 기록만 한다.

---

## ③ 인수 기준 (EARS · 각 1개 단위)

### AC-1 — 스펙 산출물이 구현 가능한 계약을 담는다
**EARS:** `When Fable에게 v5 boolean_builder 소스와 테스트를 주고 이식 스펙 작성을 요청하면, then 시스템은 구현자가 원본 코드를 보지 않고도 구현할 수 있는 입출력 계약이 담긴 .md 1개를 산출해야 한다.`
- 검증: 산출된 `SPEC-boolean-builder.md`가 §⑩ 계약 스펙의 필수 5항목(공개 함수 시그니처 / 입력 스키마 / 출력 스키마 / 에러 형태 / 경계값)을 모두 포함하는지 사람이 체크리스트로 확인
- **counter-AC(가짜 완료):** 스펙에 v5 원본 코드가 그대로 붙여넣어져 있으면 가짜다 — 그건 스펙이 아니라 복사다. 스펙에 테스트 코드가 인용돼 있어도 가짜다(정답 유출).

### AC-2 — 두 구현자가 동일 입력을 받는다
**EARS:** `While A/B 비교가 진행되는 동안, 시스템은 Fable 구현자와 Codex 구현자에게 바이트 단위로 동일한 스펙 파일만 제공해야 한다.`
- 검증: 양쪽에 전달한 프롬프트 파일의 `shasum -a 256` 이 일치
- **counter-AC:** 한쪽에만 "v5 원본을 참고하라"거나 "테스트를 통과시켜라" 같은 힌트가 붙으면 비교 무효.

### AC-3 — 구현자가 정답지를 보지 못한다
**EARS:** `If 구현 세션이 시작되면, then 시스템은 v5 원본 소스와 v5 테스트 파일 양쪽 모두를 구현자의 접근 범위 밖에 두어야 한다.`
- 검증: 구현은 워크트리 내 격리 디렉터리에서 수행하고, 그 안에 v5 경로가 존재하지 않음을 `find` 로 확인
- **counter-AC:** 구현자가 v5 테스트를 읽으면 테스트에 맞춰 짜게 되어(teaching to the test) 채점이 무의미해진다. **이 실험의 유효성을 결정하는 단일 최대 위험.**

### AC-4 — 동일 채점표로 양쪽을 채점한다
**EARS:** `When 두 구현이 산출되면, then 시스템은 v5 기존 테스트 48개를 양쪽에 그대로 적용하고 통과 수를 숫자로 기록해야 한다.`
- 검증: `python -m pytest <각 구현> -q` 출력의 `N passed / M failed` 원문 첨부 (양쪽)
- **counter-AC:** 어느 한쪽을 통과시키려 테스트를 수정하면 가짜다. 테스트 파일은 **읽기 전용**으로 취급하고, 실행 전후 `shasum` 이 동일해야 한다.

### AC-5 — 토큰 실측이 기록된다
**EARS:** `While 각 단계가 수행되는 동안, 시스템은 스펙 작성·Fable 구현·Codex 구현 각각의 소비 토큰을 기록해야 한다.`
- 검증: 단계별 토큰 수치를 결과 문서 표에 기재. 측정 불가한 항목은 "측정 불가"로 정직히 표기
- **counter-AC:** 추정치를 실측인 양 쓰면 가짜다. Codex 측 토큰이 회수 불가하면 그렇게 적는다.

> counter-AC는 알려진 실패 패턴의 최소 목록이다. 검증자는 이 목록에 국한하지 않는다.

---

## ④ Harness 게이트 진행 계획

| 게이트 | 이번 작업에서 |
|---|---|
| 0 | ✅ `bash scripts/session-status.sh` → synced / 미해결 RED 없음 |
| 1 | ✅ 이 문서 (AC 5개 + 계약 스펙 §⑩) |
| 2 | ✅ `git worktree add worktrees/token-strategy-bench -b task/token-strategy-bench` |
| 3 | 스펙 생성 → 두 구현 산출 |
| 3.5 | **배선 증명 비대상** — 실험 산출물이며 프로덕션 호출 경로에 배선하지 않는다(§⑦ 비범위에 명시) |
| 4 | `bash verify.sh` (비밀 스캔) + 채점 pytest 출력 원문 |
| 5 | PR — **코드 병합 아님.** 결과 문서만 main 후보 |
| 6 | 워크트리 회수 |

---

## ⑤ codex 적대검증 항목 (V1 정조준 지점)

1. 200줄 단일 모듈로 두 모델의 품질 차이를 판정한다는 주장이 **표본 부족으로 무의미**한 것 아닌가
2. 스펙 상세도가 실험 결과를 결정해버려서, 측정하는 것이 "모델 품질"이 아니라 "스펙 작성자의 친절함"인 것 아닌가
3. 정답지 격리가 실제로 되는가 — 구현자가 우회 경로로 v5에 접근할 수 있지 않은가
4. v6에 Python 스택이 없는데 채점을 어디서 돌릴 것인가 (환경 문제가 품질 차이로 오인될 위험)
5. 이 실험이 참이어도 "토큰 절약"이라는 원래 질문에 답하지 못하는 것 아닌가 (Max 정액제 이슈)

---

## ⑥ SOT 체크리스트

| SOT 파일 | 이 변경과의 관계 |
|---|---|
| `docs/sot/verification-commands.md` | **읽음.** 게이트 0/4 명령을 여기서 회수(`session-status.sh`, `verify.sh`). 변경 없음 |
| `docs/sot/git-workflow.md` | **읽음.** 워크트리·브랜치 명명 준수 |
| `docs/sot/coding-principles.md` | **읽음.** P1~P12 적용 대상 |
| `docs/sot/hook-contracts.md` | **읽음.** 커밋·push 훅이 워크트리에도 자동 적용됨 |

이 변경은 **SOT를 수정하지 않는다.** 실험 산출물이며 라이브 동작을 바꾸지 않는다. 실험 결과가 v6의 검증 절차를 바꿔야 한다고 판명되면, 그때 별도 PR에서 SOT diff를 동봉한다.

---

## ⑦ 비범위 (이번에 하지 않는 것)

- v5 aisearch **전체 이식** — 9,279줄. 이번 대상은 `boolean_builder` 1개 모듈뿐
- v6에 Python 스택(`pyproject.toml`/pytest/CI 확장) **정식 도입** — 사장님 지시 "실험 워크트리에서만 해"
- 산출 코드의 **v6 main 병합** — 승자 코드도 이번엔 병합하지 않는다
- 프로덕션 **배선**(R4 배선 증명 비대상) — 호출되지 않는 실험 코드임을 명시적으로 인정한다
- **Max 정액제 하의 실제 비용 환산** — 단가표는 API 종량 기준이며, 정액 한도 소모량과의 환산식은 이번 범위 밖
- 모델 **일반화 주장** — 단일 모듈 1회 실행 결과로 "Fable이 낫다/Codex가 낫다"는 일반 결론을 내지 않는다

---

## ⑩ 계약 스펙 (Spec-Driven — 손대기 전에 입출력을 박는다)

이 실험의 계약은 **두 층**이다.

### 층 1 — 실험 파이프라인 자체의 계약

```
STAGE A (스펙 작성)
  실행자: Claude Fable 5
  입력:  v5 apps/aisearch/core/boolean_builder.py (200줄)
         v5 tests/test_aisearch_ac1_boolean.py    (381줄, 48 tests)
         v5 apps/aisearch/core/data/seoul_universities.py (51줄)
  출력:  SPEC-boolean-builder.md   ← 원본 코드·테스트 코드 인용 금지
  기록:  입력 토큰 / 출력 토큰

STAGE B1 (구현 — 비싼 쪽)          STAGE B2 (구현 — 값싼 쪽)
  실행자: Claude Fable 5              실행자: Codex
  입력:  SPEC-boolean-builder.md      입력:  SPEC-boolean-builder.md  ← 동일 sha256
  출력:  impl-fable/boolean_builder.py 출력: impl-codex/boolean_builder.py
  금지:  v5 원본·테스트 접근          금지:  v5 원본·테스트 접근
  기록:  입력/출력 토큰               기록:  입력/출력 토큰 (회수 불가 시 그렇게 기재)

STAGE C (채점)
  입력:  두 구현 + v5 테스트 48개(읽기 전용, sha256 고정)
  출력:  각각 "N passed, M failed" 원문
```

### 층 2 — 구현 대상 모듈의 계약 (스펙 .md가 반드시 담아야 할 것)

`boolean_builder` 는 공개 함수 2개를 가진다. 스펙은 아래를 **코드 인용 없이 자연어+스키마로** 기술해야 한다.

| 항목 | 필수 내용 |
|---|---|
| `build_rps_boolean(jd)` | 입력 JD 객체의 필드 스키마 / 출력 문자열의 형태(`("A" OR "B") AND ("C" OR "D")`) / 한·영 혼합 키워드 그룹 처리 규칙 |
| `build_search_plan(jd, location)` | 단계(stage) 열거값 2종 · 기본 location 값 · 단계 전환 사유 열거값 · JD 필수요건이 **모든 단계에서 게이트로 유지**된다는 불변식 |
| 에러 형태 | 허용되지 않는 전환 사유는 fail-fast로 거부(catch-all 금지) — 예외 종류와 조건 |
| 경계값 | 빈 키워드 그룹 / location 미지정 / 20페이지 cap 도달 시 변형 전환 |
| 데이터 의존 | 서울 소재 4년제 대학 목록 상수의 이름과 용도 (목록 내용 자체는 별도 제공) |

**계약이 불명확하면 코드를 짜지 않고 먼저 질문한다.**

---

## 적대 검증 로그

### V1 — Codex 1차 적대검증 · **VERDICT: PARTIAL**

- 실행: `/codex:rescue` (agentId `aebea703fed9a3406`, Codex thread `019feb5b-fd91-7463-9a90-b07f291fbcda`)
- 1차 출력(명령 로그 172줄, 판정 본문 없음): `/private/tmp/claude-501/-Users-kangsangmo-Desktop-Valuehire-v6/a8b57c6f-b988-48f7-b4d1-fa3a8cbf4903/tasks/bakaaxowp.output`
- **판정 본문 전문(126줄)**: `/private/tmp/claude-501/-Users-kangsangmo-Desktop-Valuehire-v6/52b22ea0-c800-4f34-8e12-aed8a150a022/scratchpad/codex-verdict-1번안.md`
- 항목별: (a) PASS · (b) PARTIAL · (c) PARTIAL · **(d) FAIL** · **(e) FAIL**

Codex 총평 인용: *"1개 모듈·1개 공개 테스트 파일의 단발 결과로 일반적인 '코드 품질 차이'를 판정할 수 없습니다."* / *"1번 안은 저비용 파일럿이나 harness 점검에는 쓸 수 있습니다. 그러나 현재 형태는 환경 오염, 정답·계약 누출, 약한 변이 검출력, 단일 표본 때문에 Fable과 Codex의 '코드 품질 차이'를 판정하는 최적 벤치마크가 아닙니다."*

### V2 — Claude 2차 적대검증 (Codex 판정 재공격, 격리 재현)

재현 환경: `scratchpad/mut/` 에 v5 **격리 복사본** 구성(v5 원본 무수정 — 검증기가 오염원이 되지 않도록). import 경로 실측으로 오염 없음 확인:

```
loaded from: .../scratchpad/mut/apps/aisearch/core/boolean_builder.py
```

기준선: `48 passed in 0.04s`

**뮤테이션 실측 (R2 — 구현을 일부러 깨뜨려 테스트가 정말 빨개지는지 확인)**

| 뮤턴트 | 주입 내용 | 결과 | Codex 주장 | 재현? |
|---|---|---|---|---|
| A | `is_exhausted()` → `return True` (항상 소진) | **48 passed** (결함 못 잡음) | 48 passed | ✅ 재현 |
| B | `gates()`의 `copy.deepcopy(requirements)` → `requirements` (단계 간 dict 공유) | **1 failed, 47 passed** | 48 passed | ❌ **재현 실패** |

뮤턴트 B에서 빨개진 테스트: `TestCounterAcRequiredGates::test_mutating_stage_universities_does_not_touch_requirements`
→ **Codex의 "두 결함 모두 48 passed" 주장 중 절반은 성립하지 않는다.** 이 파일에는 단계 간 별칭(aliasing) 결함을 잡는 counter-AC 테스트가 실재한다. 해당 근거는 무효 처리한다.

복원 확인: `diff` 결과 v5 원본과 동일 — 격리 복사본에만 뮤테이션을 가했고 되돌렸다.

**Codex 지적 중 내가 직접 재현해 인정하는 것**

| 지적 | 재현 명령 | 결과 |
|---|---|---|
| `SearchPlan`은 상태를 가진다(`_index`, `advance()`가 변경) → "순수 모듈" 아님 | `sed -n '124,153p'` | 사실 — 내 (c) 표현은 과장 |
| 전용 테스트가 유일하지 않음 | `rg -l '(from\|import) .*boolean_builder' tests/` | `test_aisearch_ac1_boolean.py`, **`test_aisearch_orchestrator.py`** 2개 |
| v6에 pytest 없음 | `python3 -m pytest --version` | `No module named pytest` |
| `PYTHONPATH=v5` 로 통과시키면 v5 정답을 import → 채점 오염 | (설계상 자명) | 사실 — **격리 하네스로 해결됨**(위 import 경로 실측) |

**양방향 의심 결과**

- Codex의 `FAIL` → 과장인가? 뮤턴트 B 근거 1건이 재현 실패했고, "테스트가 약하다"는 결론의 강도가 그만큼 낮아진다. 다만 뮤턴트 A는 재현되어 **핵심 결론(48개 만점 ≠ 올바른 구현)은 살아남는다.**
- 내 `PASS` → 놓친 것은? (d) "v5 테스트가 **그대로** 채점 기준표"는 틀렸다. 패키지 골격·데이터 fixture·pytest 환경·import 격리를 먼저 만들어야 쓸 수 있다. 그 하네스를 이번에 만들었고 작동을 실측했다.
- 상관 블라인드스팟: 나와 Codex 둘 다 처음에 "테스트 개수 = 변별력"으로 셌다. 뮤테이션 실측이 그 가정을 깼다 — **48개 중 어느 것도 `is_exhausted` 결함을 잡지 못한다.**

### G/V1/V2 일치 여부 표

| 항목 | G(Claude) | V1(Codex) | V2(Claude 재현) | 일치 |
|---|---|---|---|---|
| (a) v6 앱 코드 0줄·46파일 | 참 | PASS(제품코드 한정) | 확인 | ✅ 일치 |
| (b) v5 aisearch 3,605+5,674줄 | 참 | PARTIAL(글롭 명시 필요) | 확인 | ✅ 일치(표현 보정) |
| (c) boolean_builder 순수 로직 | 참 | PARTIAL(`_index` 상태 있음) | **Codex 옳음** | ✅ 일치 — 내 과장 인정 |
| (d) v5 테스트가 **그대로** 채점표 | 참 | **FAIL** | **Codex 옳음**(하네스 필요) | ✅ 일치 — 내 과장 인정 |
| (d-근거) 뮤턴트 2종 모두 미검출 | — | 주장 | **1건 재현 실패** | ❌ **불일치 — Codex 과장** |
| (e) 1번 안이 A/B 비교에 "가장 적합" | 주장 | **FAIL** | **Codex 옳음**(표본 1) | ✅ 일치 — 내 과장 인정 |

**정정 집계: Codex가 잡은 내 과장 3건 (c)(d)(e) / 내가 잡은 Codex 과장 1건 (뮤턴트 B).**

### 설계 변경 (V1+V2 결과 반영) — 사장님 결정 대기

1. **채점표를 48개 그대로 쓰지 않는다.** 뮤턴트 A를 죽이는 숨은 테스트를 추가하고, 채점을 `공개 통과율`이 아니라 `숨은 테스트 통과율 + 변이 사살률`로 분리한다.
2. **격리 채점 하네스를 정본화한다.** 후보 구현만 import되도록 `module.__file__`을 매 실행 검증한다(이번에 실측 완료).
3. **결론 문장을 좁힌다.** "Fable이 낫다/Codex가 낫다"가 아니라 "이 과제·이 실행에서 어느 쪽이 몇 점"까지만 말한다 — 이미 §⑦ 비범위에 명시했고 이를 유지한다.
4. 과제를 5개로 늘린다 — **사장님 결정(2026-08-10): 5개 확대 채택.**
5. 숨은 테스트는 **Claude가 작성하고 Codex가 검증** — 사장님 결정(2026-08-10). 구현자 중 한쪽(Codex)이 채점표를 만들면 상대를 불리하게 만들 유인이 구조적으로 생기므로 배제.

---

## 확정 실험 설계 (V1+V2 + 사장님 결정 반영, 2026-08-10)

### 대상 5과제 — 의존성 실측 완료 (전부 제3자 패키지 의존 0)

| 모듈 | 줄 | import (실측) | 전용 테스트 | 기준선 |
|---|---|---|---|---|
| `boolean_builder.py` | 200 | `copy` `re` `dataclasses` `typing` + `seoul_universities`(로컬 데이터) | `test_aisearch_ac1_boolean.py` | **48 passed** |
| `intervention.py` | 201 | `enum` `typing.Protocol` | `test_aisearch_ac7_intervention.py` | **27 passed** |
| `pagination_store.py` | 194 | `uuid` `dataclasses` `datetime` `typing.Protocol` | `test_aisearch_ac3_pagination.py` | **25 passed** |
| `portal_search.py` | 233 | `typing` **뿐** | `test_aisearch_ac2_portal_search.py` | **31 passed** |
| `recorders.py` | 344 | `hashlib` `dataclasses` `typing.Protocol` | `test_aisearch_ac5_dual_record.py` | **20 passed** |
| **합계** | **1,172** | 제3자 패키지 **0** | 5파일 | **151 passed** |

측정 명령: `env PYTHONDONTWRITEBYTECODE=1 .venv-playwright/bin/python -m pytest -p no:cacheprovider tests/test_aisearch_<X>.py -q`

과제 성격이 서로 다르다 — 문자열 변환(boolean_builder) / 상태 전이(intervention) / 페이지 정책(pagination_store) / 요청 조립(portal_search) / 기록 경계(recorders). Codex가 지적한 "한 과제 편향"이 줄어든다.

**주의 (pagination_store):** `uuid`·`datetime`을 쓰므로 비결정성 위험이 있다. 채점 전에 주입 구조(`Callable`/`Protocol`)인지 확인하고, 아니라면 스펙에 시드/클록 주입을 명시한다.

### 반복 횟수 — 1회 선행, 신호 약하면 추가 (Codex 권고 3회에서 의도적으로 벗어남)

Codex는 모델당 3회 반복(총 30회 구현)을 권고했다. **1회씩(5과제 × 2구현자 = 10회) 먼저 돌린다.** 이유: ① 이 실험의 목적 자체가 토큰 절약이므로 30회 구현은 목적과 충돌한다 ② 1회차에서 점수가 크게 갈리면 반복 없이도 방향이 보인다 ③ 동률이거나 신호가 약하면 그때 반복을 추가한다. 이 선택으로 **통계적 일반화는 포기**하며, 결론은 §⑦ 비범위대로 "이 과제·이 실행에서 몇 점"까지만 말한다.

### 채점 3분리 (공개 통과율만으로는 변별 불가 — 뮤턴트 A 실측 근거)

| 축 | 내용 | 산출 |
|---|---|---|
| 1. 공개 통과율 | v5 기존 테스트 151개 | `N passed / M failed` |
| 2. 숨은 테스트 | Claude 작성 · 구현자 비공개 · Codex가 편향 검증 | 통과 수 |
| 3. 변이 사살률 | 각 모듈에 결함 주입 후 테스트가 잡는 비율 | 사살/전체 |

축 3이 축 1·2의 **감별력 자체를 검증**한다. 뮤턴트 A(`is_exhausted()` → 항상 `True`)가 공개 48개를 전부 통과한 실측이 이 축의 존재 이유다.

### 격리 규약 (Codex 지적 4 반영)

- 구현자는 v5 원본 소스·v5 테스트·git 이력에 접근 금지
- 후보별 새 격리 디렉터리에서 실행하고, 매 실행 `module.__file__`이 후보 경로인지 검증 (이번에 실측 완료)
- `PYTHONPATH`에 v5를 절대 넣지 않는다 — 넣는 순간 v5 정답을 import한다
- 양쪽 프롬프트 파일 `shasum -a 256` 일치 확인

---

## 실측 결과 1 — 채점 하네스 (2026-08-10, 게이트 3 진행분)

산출물: `bench/setup-harness.sh` · `bench/score.sh` · `bench/mutate.py` · `bench/hidden/test_hidden_survivors.py`

**reference 채점 (v5 원본 사본)**
```
== import 경로 검증 (채점 오염 차단) ==
   [OK]      boolean_builder -> apps/aisearch/core/boolean_builder.py
   [OK]      intervention -> apps/aisearch/core/intervention.py
   [OK]      pagination_store -> apps/aisearch/core/pagination_store.py
   [OK]      portal_search -> apps/aisearch/core/portal_search.py
   [OK]      recorders -> apps/aisearch/core/recorders.py
== 축 1: 공개 테스트 (147개 대상 / 문서·SQL 검사 4개 제외) ==
147 passed, 4 deselected in 0.15s
```

**채점 제외 4건** — 코드가 아니라 외부 산출물의 존재·내용을 검사하므로 구현 품질을 측정하지 못한다. 그 문서를 구현자에게 주면 정답 계약(실제 URL·셀렉터)이 유출되고, 안 주면 무조건 실패한다. 양쪽 후보에 동일 적용.

| 제외 테스트 | 검사 대상 |
|---|---|
| `ac2::test_doc_contract_still_contains_urls_and_selectors` | `docs/search-access.md` 본문 |
| `ac2::test_doc_contract_and_not_fields_are_indistinguishable` | 같은 문서의 169·175행 |
| `ac3::TestSchemaDraftLocation::test_not_in_supabase_migrations` | `supabase/migrations/*.sql` 부재 |
| `ac3::TestSchemaDraftLocation::test_draft_exists_with_guard_and_idempotency_unique` | `apps/aisearch/schema/*.draft.sql` 존재 |

## 실측 결과 2 — 축 3 변이 사살률 (핵심 발견)

측정: `bench/mutate.py` — 표준 뮤테이션 연산자 10종을 코드에 심고 테스트가 잡는지 센다. 문법이 깨지거나 **문자열 리터럴 내용만 바뀐** 뮤턴트는 AST 구조 비교로 제외한다(초기 측정에서 독스트링의 `live=False` 문구 변경 등 가짜 6건이 섞였고, 이를 걸러 수치를 정정했다).

| 과제 | 공개만 | 공개 + 숨은 | 개선 |
|---|---|---|---|
| `boolean_builder` | 85.0% (생존 3) | **95.0%** (생존 1) | +10.0 |
| `intervention` | 70.0% (생존 3) | **90.0%** (생존 1) | +20.0 |
| `pagination_store` | 100.0% (생존 0) | 100.0% (생존 0) | — |
| `portal_search` | 73.3% (생존 4) | **100.0%** (생존 0) | +26.7 |
| `recorders` | 91.3% (생존 2) | **95.7%** (생존 1) | +4.4 |
| **합계** | **84.4%** (65/77) | **96.1%** (74/77) | **+11.7** |

**v5 공개 테스트 147개를 전부 통과해도 심어놓은 결함 12개가 그대로 빠져나간다.** 가장 심한 곳은 `intervention.py:89·91` — 사람 개입 이벤트인지 차단 신호인지 가르는 `==` 를 `!=` 로 뒤집어도 공개 27개가 전부 초록이다. 사람이 개입했는데 "차단당했다"로 분류하는 코드가 만점을 받는다.

이 수치가 §③ AC-4의 근거다. **"테스트 N개 통과"를 완료 증거로 쓸 수 없다** — 축 2·3이 필요한 이유이며, 동시에 v6 검증 철학의 실물 반례다.

### 숨은 테스트 (축 2) — 28 tests, `bench/hidden/test_hidden_survivors.py`

작성 원칙: v5 코드를 베끼지 않고 **관찰 가능한 계약만** 단언한다. private 이름·내부 필드에 의존하지 않으며, 어떤 구조로 구현하든 계약만 지키면 통과한다. reference에서 `28 passed` (거짓 실패 0).

조준점 예시 — 경계값 포함성(`career 0·20`, `score 0·100`), 문장형 표지 단독 검출, `bool`을 정수로 오인하지 않기, 한쪽 키워드만으로 동작, 이벤트 분기 보존, 차단 상태의 종단성.

**남은 생존 3건 (정직 기재)**

| 위치 | 뮤턴트 | 상태 |
|---|---|---|
| `boolean_builder.py:130` | `repr=False` → `True` | 표시 옵션 — 계약 아님. 잡으려면 구현 스타일을 강요하게 되어 의도적으로 두었다 |
| `intervention.py:125` | `via_human_reset=False` → `True` | 테스트를 썼으나 여전히 생존 — 등가 뮤턴트 여부 Codex 판정 대기 |
| `recorders.py:251` | `resume_from is not None` → `is None` | 미작성 — 실패 주입 fixture 필요 |

### V1 2차 — 숨은 테스트 편향 검증 · **VERDICT: FAIL** (수정 완료)

판정 본문(313줄): `/private/tmp/claude-501/-Users-kangsangmo-Desktop-Valuehire-v6/52b22ea0-c800-4f34-8e12-aed8a150a022/scratchpad/codex-verdict-hidden-tests.md`

Codex 결론 인용: *"공개 계약을 통과하는 대안이 숨은 문구 정답 때문에 4점 손실하는 직접 반례가 있습니다. … 고의성 입증은 필요하지 않습니다. A/B 채점표는 결과에 영향을 주는 비대칭만 있어도 무효입니다."*

**V2 격리 재현 — Codex 지적이 사실로 확인됨 (내 잘못)**

recorders의 오류 문구만 한국어→영어로 바꾼 대안(상태·부작용·오류 의미는 동일):

```
--- 공개 테스트 ---   20 passed
--- 숨은 테스트 ---   4 failed, 24 passed
FAILED test_score_outside_contract_is_rejected[-1 / 101 / True / 3.5]
```

계약(실패 상태·외부 쓰기 0건·오류 정보 존재)을 전부 지킨 구현이 **v5의 한국어 문구를 재현하지 않았다는 이유만으로** 4점을 잃었다. 구현자 한쪽 계열이 만든 채점표가 자기 계열 문구를 정답으로 삼은 것 — 이해충돌 통제 실패다.

`intervention.py:125` 등가 뮤턴트 주장도 코드 경로로 확인: `poll()` 은 `PAUSED_HUMAN` 에서만 `_transition` 을 호출하고(`intervention.py:183-188`), `human_reset()` 은 `via_human_reset=True` 를 명시한다(`:191-200`). 그 기본값을 읽는 공개 경로가 없으므로 **계약 테스트로는 잡을 수 없다.** 내 테스트의 "이 뮤턴트를 잡는다"는 설명이 틀렸다.

**수정 6건 (Codex 우선순위 그대로 이행)**

| # | 수정 | 검증 |
|---|---|---|
| 1 | `test_score_outside_contract_is_rejected` — 문구 매칭 삭제 → 상태(`STATUS_FAILED`)·외부 쓰기 0건·오류 존재로 판정 | 문구 대안 **29 passed**(전 4 failed) |
| 2 | `test_failure_before_any_write_is_failed_not_partial` 신규 — 첫 단계가 쓰기 전 실패하면 `partial` 아닌 `failed` | `recorders` 87.5%→**100%** |
| 3 | `test_blocked_state_survives_repeated_polling` — 잘못된 조준 설명 삭제, 등가 뮤턴트임을 명시하고 이중 방어로 유지 | — |
| 4 | 숨은 테스트에서 **변이 좌표·연산자 전량 제거**(9곳) — 파일이 새도 정답 역산 불가 | `grep -c '\.py:[0-9]'` → 0 |
| 5 | `mutate.py` — 한 줄의 같은 연산자를 **발생마다 독립 뮤턴트**로 생성(`count=1` 제거) | 뮤턴트 77→**85**개 |
| 6 | `mutate.py` — pytest exit 2~5(수집·사용·내부 오류)를 사살로 세지 않고 예외로 중단 | 인프라 오류 오인 차단 |

**수정 후 재측정**

| 과제 | 공개만 | 공개 + 숨은 |
|---|---|---|
| `boolean_builder` | 85.7% | 95.2% |
| `intervention` | 70.0% | 90.0% |
| `pagination_store` | 100.0% | 100.0% |
| `portal_search` | 70.0% | **100.0%** |
| `recorders` | 87.5% | **100.0%** |
| **합계** | **82.4%** (70/85) | **97.6%** (83/85) |

남은 생존 2건은 **둘 다 계약-등가 뮤턴트**(`repr=False`, `via_human_reset`)로, Codex가 "기능 계약 기준 등가/무관"이라 판정한 것들이다. 잡으려면 private 구현을 강요해야 하므로 의도적으로 두었다. **관찰 가능한 결함은 전량 검출된다.**

숨은 테스트: 29 tests, reference에서 `29 passed` (거짓 실패 0).

**정정 집계 (V1 2차 기준): Codex가 잡은 내 결함 4건(문구 편향·잘못된 조준 설명·recorders 공백·좌표 유출) + 도구 결함 2건. 내가 잡은 Codex 과장 0건 — 이번 판정은 전면 수용.**

> 구현자 한쪽(Codex)이 채점표를 만들면 상대를 불리하게 만들 유인이 생기므로 **작성은 Claude, 검증은 Codex**로 분리했다(사장님 결정). 이번 검증은 그 분리가 실제로 작동했음을 보여준다 — 작성자(Claude) 혼자였다면 자기 계열 문구 편향을 발견하지 못했을 것이다.

---

## codeaudit 감사 (2026-08-13, 사장님 지시) — 하네스 구조 결함 5건

읽기 전용 감사 + 실행 대조. **본 실험을 시작하기 전에 발견해 전부 수정했다.**

| ID | 결함 | 근거 (감사 시점 실측) | 심각도 |
|---|---|---|---|
| A | `mutate.py:105` 가 `work = BENCH / "reference"` 로 **고정** — 축 3을 후보 구현에 적용할 방법이 없었다 | 해당 줄이 변이 대상 폴더를 정하는 곳 | **치명적** |
| B | `score.sh` 가 `tests/` 디렉터리를 통째로 지정해 **축 1에 축 2가 혼입** — 주석은 "147개 대상"인데 실제 `176 passed` | 숨은 테스트 29개가 같은 폴더에 있었다 | **치명적** |
| C | `setup-harness.sh` 가 숨은 테스트를 후보에 배치하지 않음 (`grep -c hidden` → 0) | 후보 축 2 측정 불가 | 높음 |
| D | 숨은 테스트 1파일에 5모듈이 섞여, 모든 모듈 변이에 전부 실행 | V1 2차에서 Codex가 지적했으나 미이행 | 높음 |
| E | 죽은 `import shutil` | 사용 0회 | 낮음 |

**결함 B·D가 실험 결과를 뒤집는 이유**

- B: 두 후보의 점수 차이가 어느 축에서 났는지 분간할 수 없다. 3축 분리 설계가 무의미해진다.
- D: 후보가 A모듈을 잘못 짜면 B모듈 변이 측정에서도 숨은 테스트가 실패해 **전부 사살로 집계**된다. **못 짠 구현일수록 사살률이 높아지는** 거꾸로 된 결과가 나온다.

**수정 5건 + 검증**

| 수정 | 검증 결과 |
|---|---|
| `mutate.py` — 변이 대상을 `TARGET` 환경변수로 (기본 `reference`) | `TARGET=candidate-fable` 실행 시 `[변이 대상] .../candidate-fable` 출력 확인 |
| `score.sh` — 축 1은 공개 5개 파일 **명시 나열**, 축 2를 별도 단계로 분리 | 숨은 테스트 배치 후에도 **축1 `147 passed` / 축2 `29 passed`** 로 분리 유지 |
| 숨은 테스트를 모듈별 4파일로 분할 (`test_hidden_{boolean_builder,intervention,portal_search,recorders}.py`) | 교차 오염 경로 제거. `pagination_store` 는 공개 사살률 100%라 숨은 테스트 없음 |
| `place-hidden.sh` 신규 — 숨은 테스트를 **채점 시점에만** 배치 | 4개 배치 확인. 구현 단계에서는 호출하지 않는다 |
| 죽은 `import shutil` 제거 | — |

**수정 후 축 3 재측정 (수치 불변 — 회귀 없음)**

| 과제 | 공개만 | 공개 + 해당 모듈 숨은 |
|---|---|---|
| `boolean_builder` | 85.7% | 95.2% |
| `intervention` | 70.0% | 90.0% |
| `pagination_store` | 100.0% | 100.0% |
| `portal_search` | 70.0% | 100.0% |
| `recorders` | 87.5% | 100.0% |
| **합계** | **82.4%** (70/85) | **97.6%** (83/85) |

후보 미구현 상태에서 채점하면 `[MISSING]` 5건 + `VERDICT: 채점 중단` 으로 안전 정지한다(빈 후보를 만점 처리하지 않는다).

**⚠️ 이 절의 "전부 수정했다"는 과장이었다.** 같은 날 Codex 적대 재검증(아래)이 치명 결함 4건을 추가로 찾았다. codeaudit(자체 감사)은 구조 결함은 잡았으나 **공격 시나리오를 실행하지 않아** 격리 우회·거짓 성공·기준선 미검증을 놓쳤다.

**감사가 놓쳤을 수 있는 것 (정직 기재)**

- 숨은 테스트 29개에 **아직 남아 있을지 모를 구현 스타일 강요**는 이 감사에서 반례 구현을 만들어 전수 검증하지 못했다. Codex 적대 검증에 위임했다(`codex-verdict-harness-v2.md`, 검증 중).
- 결함 B의 원인은 내가 숨은 테스트를 검증용으로 `reference/tests/` 에 복사한 뒤 **치우지 않은 것**이다. 그 뒤 `score.sh` 를 다시 돌려본 적이 없어 176이라는 숫자를 보지 못했다. goal 문서의 "147 passed" 는 복사 전 측정값이라 거짓은 아니지만, 감사 시점에 재현하면 다른 숫자가 나오는 상태였다.

---

## 마무리 체크 (현재 상태)

- [x] §0.5 레포 규칙 회수 + C(과거 회수) — `docs/sot/*` 4종, `git log`, MEMORY.md 확인
- [x] 위험 등급 판정 — L2
- [x] goal 문서 + 계약 스펙 (이 파일)
- [x] 게이트 0 통과 · 게이트 2 워크트리 생성
- [ ] STAGE A/B/C 실행
- [ ] 게이트 4 검증 (`bash verify.sh` + 채점 출력)
- [ ] §5 V1 판정 본문 확보 ← **현재 대기 중**
- [ ] §6 V2 재공격

---

## V1 3차 — Codex 하네스 적대 재검증 · **VERDICT: FAIL** → P0 4건 수정 완료

판정 본문(529줄): `scratchpad/codex-verdict-harness-v2.md`

Codex 결론 인용: *"이 상태에서 나온 Fable/Codex 승패는 모델 품질 증거가 아니다. P0 네 건을 고치고 동일 공격을 다시 통과하기 전까지 A/B 실행을 중단해야 한다."*

**Codex가 확인해준 것 (편향 혐의는 반증됨)**

- 내 재측정 수치 4종(70/85, 83/85, 숨은 29 passed, 영어 대안 20+29 passed) **전부 재현됨**
- 숨은 테스트의 Fable 계열 편향은 **실제 반례 구현으로 재현되지 않음** — private 이름(`_index`→`_cursor`), 자료구조(tuple→list), 오류 언어(한→영)를 모두 바꾼 대안이 공개 147 + 숨은 29 전부 통과
- v5 원본 무변경 확인(SHA 대조)

**그러나 하네스 자체가 뚫렸다 — 치명 결함 4건**

| ID | 공격 | Codex 실측 | 왜 치명적인가 |
|---|---|---|---|
| F-1 | 공개 9건 실패하는 후보에 변이 측정 | **21/21, 100% 사살** | 변이 전 기준선을 확인하지 않아, 이미 깨진 구현은 모든 뮤턴트에서도 실패 → 전부 "잡았다"로 집계. **못 짤수록 만점** |
| F-3a | 실패 후보를 `score.sh` 로 채점 | `9 failed` 출력 후 **exit 0** | `\|\| true` 로 종료 상태를 버려, 자동 채점기가 성공으로 읽는다 |
| F-3b | 후보 5개 모듈을 reference 정답으로 심볼릭 링크 | 전부 `[OK]`, **147 passed** | `__file__` 문자열의 lexical prefix만 봐서 링크를 못 걸러낸다. **정답 복사가 만점** |
| F-2 | `if A or B` → `if any((A, B))` (동작 등가) | 분모 **21→20**, 95.2%→95.0% | 구문 선택이 뮤턴트 분모를 바꾼다. 후보별 변이율은 **A/B 비교 불가능한 자** |
| F-4 | 숨은 4파일 중 1개만 배치 | 축2 `9 passed`, exit 0 | 배치 실수가 점수 차이로 읽힌다 |
| F-5 | pytest exit 5 강제 | 변이된 소스 **미복원** | `finally` 부재 — 인프라 오류 1회가 이후 전 측정을 오염 |
| F-6 | 절대경로 `TARGET` | 코드경로상 BENCH 밖 덮어쓰기 가능 | 변이는 파일을 실제로 쓰므로 탈출 = 원본 훼손 |

**수정 + 공격 재현 검증 (전부 실측)**

| 수정 | 대상 | 재현 결과 |
|---|---|---|
| 변이 전 **기준선 검증** — 초록이 아니면 중단 | `mutate.py` | 깨진 후보 → `FATAL: boolean_builder 기준선 실패 — 변이 측정 불가` (전: 21/21 100%) |
| 종료 상태 **누적** (`\|\| true` 제거, 인프라 오류는 코드 전달) | `score.sh` | 실패 후보 → **exit=1** (전: exit 0) |
| **심볼릭 링크 거부** + `realpath` 비교 | `score.sh` | 링크 5개 → `[링크거부]` 5건, **exit=2** (전: 147 passed) |
| 숨은 파일 **완전성 강제** (4/4 아니면 중단) | `score.sh`·`place-hidden.sh` | 1/4 배치 → `FATAL: 숨은 테스트 불완전 (1/4)`, **exit=3** (전: exit 0) |
| `finally` 복원 | `mutate.py` | 예외 경로에서도 원본 복원 보장 |
| TARGET **허용목록 + 실경로 봉쇄** | 3개 스크립트 | BENCH 밖 경로 거부 |
| **축 3을 후보 승패 점수에서 제외** | 설계 변경 | 아래 카드 참조 |

**회귀 없음**: reference 채점 `exit=0` · 축1 `147 passed` · 축2 `29 passed` · 축3 생존 2건(불변).

### 설계 결정 — 축 3의 용도 축소

- **무엇을**: 변이 사살률(축 3)을 후보 A/B 승패 점수에서 빼고, **고정 reference 에 대한 채점표 감별력 감사**로만 쓴다. 후보 채점은 축 1(공개 147) + 축 2(숨은 29)로 한다.
- **왜**: 동작이 같은 구현도 구문 선택만으로 뮤턴트 분모가 달라진다(F-2 실측: 21→20). 분모가 다른 백분율을 비교하면 **모델 실력이 아니라 코딩 스타일**을 재게 된다.
- **버린 대안**: ① 고정된 계약 위반 시나리오를 후보마다 동일하게 심어 통과/실패를 센다 — 정확하지만 시나리오 설계에 다시 편향이 들어갈 여지가 크고 작업량이 배로 든다. ② 분모가 다르면 "비교 불가"로 중단 — 그러면 대부분의 실행에서 축 3이 그냥 죽는다.
- **대가**: 후보 구현의 "견고함"을 직접 수치화하지 못한다. 그 역할은 숨은 테스트(축 2)가 대신한다 — 숨은 테스트가 곧 결함 시나리오이기 때문이다.
- **되돌리는 법**: `score.sh` 축 3 안내문과 `mutate.py` 헤더 경고를 지우고, 후보별 `TARGET=candidate-*` 변이율을 점수표에 넣으면 원복된다. 단 F-2 반례가 그대로 살아나므로 권하지 않는다.

### 남은 미이행 (정직 기재)

| 항목 | 상태 | 영향 |
|---|---|---|
| 숨은 테스트 독스트링의 변이 힌트 (`portal_search:22-24` 등 "조건이 결합으로 바뀌면") | **미이행** | 파일이 구현자에게 노출되는 사고 시 조준점 역산 가능. 점수 편향은 재현되지 않음 |
| `setup-harness.sh` 의 SHA manifest·삭제 sentinel | **미이행** | 두 후보를 서로 다른 setup 실행으로 만들면 v5 drift 가 모델 차이로 섞일 수 있음 |
| goal 문서 내부 수치 불일치(raw 151 / 실채점 147, 폐기된 단일 hidden 파일 기록) | **부분 정정** | 이 절에서 "전부 수정" 과장을 정정. 나머지 표기는 다음 갱신에서 통일 |

**정정 집계 (V1 3차): Codex가 잡은 치명 결함 4건 + 높음 3건. 내가 잡은 Codex 과장 0건 — 전면 수용.**
