# HumanSearch G2 테스트 게이트 goal

## 결론 (사장님 브리핑 §1⑪)

이번 작업은 후보자 검색 기능(휴먼서치)의 "검사가 실제로 돌았는지"를 기계가 증명하게 만드는 것입니다. 지금은 그 기능의 코드가 한 줄도 없고, 따라서 "검사를 돌렸다"고 주장해도 확인할 방법이 없습니다. 이번에 만들 장치는 ① 검사가 진짜 부품을 메모리에 올려 실행했다는 증거를 남기고 ② 시험이 0개 수집되면 합격이 아니라 불합격을 내며 ③ 누가 검사 명령을 지우거나 무력화하면 자동으로 들통나게 합니다. 결정하실 사항: 없습니다 — 서버 정본 반영은 위임 조건(자동 검사 초록 + 두 검증 엔진 통과 + 공격 감사 통과)대로 진행합니다.

## 왜 이렇게 판단했나 (2층)

**결정 카드 (§8-4)**

> **무엇을** — "검사가 실제로 돌았는가"를 문자열 검사가 아니라 **행동 검증**(일부러 고장 낸 사본을 진짜 게이트에 먹여 불합격이 나오는지 확인)으로 증명하는 구조를 골랐다.
> **왜** — 검사 명령의 존재가 아니라 검사의 효과를 재는 유일한 방법이라서. 명령이 지워지든 무력화되든, 심어둔 고장을 못 잡으면 반드시 들통난다.
> **버린 길** — ① 명령을 문서에만 적기: 지워도 아무 검사가 빨개지지 않아 버림. ② 게이트가 자기 소스에 명령 문자열이 있는지 확인하기: 실행 없이 문자열만 남겨도 통과라 버림(P16 위반).
> **대가** — 문지기·서버 검사가 파이썬 도구를 받아 도는 시간(수십 초~수 분)이 추가되고, 뮤테이션 사본 실행만큼 검사가 길어진다.
> **되돌리기** — 병합 커밋 1개를 revert하면 전체 원복(추가 전용 변경). 비용은 revert PR 1건.

---

## 0. 메타

- 작성일: 2026-08-12 (착수 05:0x)
- 구현 계약: `worktrees/humansearch-clean-room-plan/docs/engineering/humansearch-v6-clean-room-rebuild-goal-2026-08-12.md` (SHA-256 `04c03a11bf0b88ad3f84efbf37a3b237d735d471941f8fe5c23f39ce57273faf`) — Phase G / G2
- GitHub issue: #10 / 선행 G1: #7 → PR #9 병합(main `b384e47`)
- branch/worktree: `task/humansearch-g2-gates` / `worktrees/humansearch-g2-gates`
- 구현자(G): Fable 5 (이 세션) / V1: Codex CLI / V2: Fable 격리 재현 + codeaudit
- 중단선: G2 PR과 CI, 위임 조건 충족 시 병합까지. G3는 별도 worktree로. B1 착수 금지.

## 1. 현재 상태 (file:line 증거)

| 사실 | 증거 |
|---|---|
| HumanSearch 파이썬 패키지·테스트가 0개다 | `git ls-files '*.py'` → 0건 (b384e47) |
| G2 게이트 스크립트가 없다 | `test -e scripts/acceptance-hs-gates.sh` → 부재 |
| CI에는 파이썬 도구 셋업이 없다 | `.github/workflows/verify.yml:16-27` — checkout과 bash 스텝뿐 |
| pre-push는 `scripts/acceptance-*.sh` 글로브 자동 수집 + 0개면 차단 | `docs/sot/hook-contracts.md:22-24` |
| CI는 명시 열거라 새 스크립트는 verify.yml에 직접 배선해야 한다 | `docs/sot/verification-commands.md:33` (P15③ 경고 문단) |
| 환경은 계약 C-8과 일치 | `python3 --version`→3.14.1, `uv --version`→0.11.3 (05:00 실측) |
| 허용 개발 도구 | 계약 291-293행: Python 3.14 + stdlib, dev는 ruff·mypy strict·pytest·Hypothesis, 관리자 uv |

→ **의미:** 검증할 대상도 배관도 0에서 시작하지만, 도구 환경은 계약과 정확히 일치하므로 "환경이 없어서 못 한다"는 변명은 성립하지 않는다. CI에만 파이썬 셋업을 새로 배선하면 된다.

## 2. 근본 원인

검증 대상(모듈)과 검증 배관(게이트)이 둘 다 없어서, "정적·단위 테스트 통과"라는 말이 실행 증거 없이 성립해 버린다. 특히 ① 테스트 러너는 0건 수집도 조용히 지나갈 수 있고 ② 소스 문자열 검사로는 실제 import를 증명할 수 없으며(P16) ③ CI와 pre-push가 다른 명령을 돌면 한쪽만 통과하는 위장이 가능하다(P15③).

## 3. AC — G2 단언 1개 (EARS)

**When CI 또는 pre-push가 돌 때, the system은 HumanSearch 정적·단위 테스트를 실제 모듈 import와 함께 실행해야 하며, If 수집된 테스트가 0건이거나 검사가 실행되지 못하면 then exit 0이 아니어야 한다.**

- 검증 명령: `bash scripts/acceptance-hs-gates.sh` → `PASS` 4종(정적 2·수집·import) + `COLLECTED: N`(N≥1) + exit 0
- 뮤테이션 명령: `bash scripts/acceptance-hs-gates-mutations.sh` → `PASS: gates mutations blocked M/M` + exit 0
- counter-AC (가짜 완료 시나리오 — 이 목록에 국한하지 않음):
  1. 테스트 명령이 CI에만 있거나 pre-push에만 있음 → 뮤테이션이 verify.yml 열거를 검사, pre-push는 글로브+0개 차단이 기존 계약
  2. 두 경로가 서로 다른 명령 실행 → 단일 진입점(`acceptance-hs-gates.sh`) 하나만 존재, 뮤테이션이 열거 문자열 대조
  3. 모듈 미import 문자열 검사만 → 수입 확인 장치(spy)가 런타임 `sys.modules`의 실제 파일 경로를 기록해야 통과
  4. 수집 0건인데 exit 0 → COLLECTED 파싱 N≥1 강제 + pytest의 0건 수집 종료값도 불합격 처리
  5. 명령 삭제·주석·`|| true` 무력화 → 행동 뮤테이션(실패 시험 심기)이 잡는다: 게이트가 실패를 못 보면 뮤테이션 suite가 exit 1
  6. 없는 경로 조건부 skip → 패키지 부재 사본에서 게이트가 exit 0이면 뮤테이션 suite가 exit 1
  7. 러너 실패를 성공으로 덮음 → 5와 동일 원리로 검출

## 4. 계약 스펙 (§1⑩ — 입출력)

`scripts/acceptance-hs-gates.sh`
```
입력  : 없음(기본: 저장소의 humansearch/). 검증용 재지정: HS_GATES_PROJECT=<dir>
출력  : stdout —
        PASS: ruff clean (files >= 2)
        PASS: mypy strict clean in <N> source files   # N >= 1
        PASS: pytest collected <N> and passed          # N >= 1
        PASS: runtime import proof <src 경로>
        COLLECTED: <N>
exit  : 0(전부 합격) | 1(검사 불합격) | 2(검사 자체를 실행 못 함 — fail-closed)
불변식: set -euo pipefail. 어떤 검사도 조건부 skip 금지. 검사 수·수집 수 하한 미달은 exit 1.
        spy 파일의 module_file이 프로젝트 src 밖이면 exit 1.
```

→ **의미:** 이 스크립트 하나가 CI와 문지기 양쪽의 단일 진입점이다. 성적 0=합격, 1=검사 불합격, 2=검사 자체를 못 돌림 — 2도 불합격으로 취급해 "못 돌렸으니 통과"를 막는다.

`scripts/acceptance-hs-gates-mutations.sh`
```
입력  : 없음. mktemp 샌드박스에 humansearch/ 사본을 만들어 진짜 게이트 스크립트를 실행
출력  : PASS: gates mutations blocked <M>/<M> | FAIL: mutation passed: <라벨>
exit  : 0 | 1 | 2(전제 부재)
뮤테이션 최소 목록: 실패 시험 주입 / 타입 오류 주입 / lint 오류 주입 / 테스트 전부 삭제(0건 수집) /
        모듈 import 파손 / 패키지 디렉터리 부재 / verify.yml 배선 문자열 부재 검사 / 깨끗한 사본 baseline 통과
```

→ **의미:** 진짜 게이트 스크립트를 고장 사본에 먹여 "불합격을 낼 줄 아는지"를 재는 검사다. 게이트의 검사 명령이 지워지거나 무력화되면 여기서 반드시 빨간불이 켜진다.

`humansearch/` 패키지 (사업 동작 없음 — G2 배관 성립용 최소 경계)
```
humansearch/pyproject.toml     # name=humansearch, requires-python>=3.14, dev: ruff·mypy·pytest·hypothesis 핀 고정
humansearch/uv.lock            # 재현 가능한 도구 버전 잠금
humansearch/.python-version    # 3.14.1 (C-8)
humansearch/src/humansearch/__init__.py  # 상수/버전만. 로직 0
humansearch/tests/test_package_boundary.py  # 실제 import 단언 ≥ 1개
scripts/hs_import_spy.py       # pytest 플러그인: 세션 종료 시 sys.modules['humansearch'].__file__과 수집 수를 JSON으로 기록
```

→ **의미:** 사업 로직은 0줄이다. 이 최소 골격은 "검증 배관이 실제 모듈을 물고 도는가"를 성립시키기 위한 경계일 뿐이며, HumanSearch 기능은 이후 Phase에서 이 배관 위에 얹는다.

## 5. Harness 게이트 계획

| Gate | 계획 | 상태 |
|---|---|---|
| 0 | G1 병합(b384e47) + RED 0/14 + 과거 회수(G1 goal의 worktree 함정 재사용) | PASS |
| 1 | issue #10 + 이 문서 | PASS |
| 2 | RED: 뮤테이션 suite가 현 배관에서 실패(구현 부재)를 실행으로 증명 후 커밋 | NOT_RUN |
| 3 | GREEN: §4 산출물 최소 구현. RED 파일 불변 | NOT_RUN |
| 3.5 | 배선: pre-push 글로브 자동 수집 실측 + verify.yml 명시 열거 + SOT 표 갱신(명령 실재 후) | NOT_RUN |
| 4 | 검증: 두 명령 + 기존 acceptance 전량 + 실제 pre-push + RED 0 | NOT_RUN |
| 5 | 배송: push → PR(#10 연결) → CI 초록 → 위임 조건 확인 후 병합 | NOT_RUN |
| 6 | 병합 후 worktree 정리, G3 착수 | NOT_RUN |

→ **의미:** 표의 상태값은 3상태(PASS/FAIL/NOT_RUN)로만 적으며, NOT_RUN이 하나라도 남아 있으면 전체를 완료라 부르지 않는다(P3).

## 6. 적대검증 조준점 (V1 Codex에 전달)

- 게이트가 자기(스크립트·플러그인)를 검사 대상에서 빼는가
- HS_GATES_PROJECT 재지정이 실전 경로(기본값)를 약화시키는가
- spy 파일 위조: 플러그인 없이 JSON만 미리 써두면 통과하는가 (신선도·경로 검증)
- COLLECTED 파싱을 속이는 출력 주입(테스트 이름에 "collected N items" 문자열 등)
- 뮤테이션 suite가 "잘못된 이유의 실패"를 성공으로 세는가
- uv 캐시 부재·네트워크 차단에서 exit 0이 나오는가 (fail-closed)
- CI 열거 검사 문자열을 주석으로 넣어도 통과하는가

## 7. SOT 체크리스트

- [x] `docs/sot/INDEX.md` `docs/sot/coding-principles.md`(P2·P3·P5·P13·P15·P16·P20) `docs/sot/verification-commands.md` `docs/sot/hook-contracts.md` `docs/sot/git-workflow.md` — 04:0x 이 세션에서 전부 읽음
- [x] 저장소 AGENTS.md/CLAUDE.md 부재 확인 (`ls` 04:56)
- [ ] `docs/sot/verification-commands.md`에 G2 두 명령 추가 — **GREEN에서 명령이 실재·실행된 뒤에만** (계약 357-358행)

## 8. 비범위

G3(portal locator·운영 상수 검사), B1~B5, L0, C, 사업 로직·브라우저·native host, v1~v5 열람/복사/import/실행, 외부 포털·PII 접근, main 직접 수정.

## 9. 롤백 (L3)

`git revert <squash 커밋>` 한 번으로 전체 원복(추가 전용 변경). CI의 G2 스텝도 같은 revert에 포함되므로 별도 조치 불요.

## 10. 영향 반경 (L3)

이 변경이 깨지면: pre-push·CI가 불합격을 내 배송이 멈춘다(안전한 방향). 라이브 제품·PII·과금 경로 접촉 없음 — 검증 인프라 전용. 데이터 안전 AC: 게이트·테스트는 네트워크와 PII에 접근하지 않는다(테스트에서 외부 호출 0 — V1 조준점에 포함).

## 검증 출력

NOT_RUN — RED/GREEN 이후 실측 출력을 그대로 append한다.

## 적대 검증 로그

NOT_RUN — V1(Codex) 판정 원문과 V2 재현을 명령·출력 그대로 append한다.
