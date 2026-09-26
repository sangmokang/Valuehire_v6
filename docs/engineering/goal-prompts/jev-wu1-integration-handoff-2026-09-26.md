# Jev 근거 평가 WU1 — main 반영(integration) 인수인계 (2026-09-26)

## 결론

WU1(Jev 근거 평가 + Vercel Gateway 경유 호출) 기능 개발은 끝났습니다. 더 만들 코드는 없고, 남은 일은 main에 올리는 일뿐입니다.
main 반영을 막는 것은 WU1 코드가 아니라 저장소 공통 문제 두 가지입니다. ① 검사 예외 2건이 9/15에 만료되어 모든 PR과 main의 자동 검사가 빨간불이고, ② main 병합에 "본인 외 승인 1건"이 필요한지 지금은 확인이 안 됩니다.
사장님이 정할 것: (1) 만료된 예외를 "체인 PR로 해제"할지 "기한 연장"할지, (2) GitHub 웹 설정에서 main 보호 규칙이 지금 켜져 있는지 확인.

판정: WU1 기능 개발 종료 → integration 정리 단계.

## A. 현재 상태 (2026-09-26 22:2x KST 이 세션 실측)

| 항목 | 값 | 기록 대비 |
|---|---|---|
| 작업 폴더 | `/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/jev-ea-wu1-split` | 일치 |
| branch | `task/jev-evidence-assessment-wu1-split` | 일치 |
| HEAD(이 문서 커밋 전) | `741f275` | 일치 |
| working tree | 깨끗함(추적 안 된 파일도 0) | 일치 |
| origin 대비 | ahead 21 / behind 0, origin 끝 `dbc7fd0` | 일치 |
| 미푸시 커밋 | 21개(`39a66bf`…`741f275`) + 이 문서 커밋 1개 = 22 | 일치(+1) |
| origin/main 대비 | 이 브랜치가 main보다 4커밋 뒤(main에 9/25 직접 push된 `f12ea33 605973f fdb9a20 f1f7a01`) | 새로 확인 |
| 다른 세션 | 이 폴더를 cwd로 쓰는 작업 세션 없음. 잡힌 프로세스는 전부 부모 PID 1인 Codex 플러그인 브로커(93937) 자손 | — |

관련 PR (`gh pr view`, 2026-09-26 실측)

| PR | 제목 요약 | base ← head | 상태 | CI |
|---|---|---|---|---|
| #109 | Jev 조직 shadow 기반 | `main` ← `task/jev-shadow-base-split@0d92a8a` | OPEN, UNSTABLE, MERGEABLE, 리뷰 없음 | verify 실패(push·pull_request 둘 다). 실패 단계는 "억제 만료 스캔" 하나 |
| #110 | Jev 근거 평가 WU1 | `task/jev-shadow-base-split` ← `wu1-split@dbc7fd0`(원격, 로컬 21개 미반영) | OPEN, UNSTABLE, MERGEABLE, 리뷰 없음 | 같은 단계 하나로 실패 |
| #74 | 억제 p13-deletion-blindspot 해제 | `main` ← `task/p13-deletion-guard@903051b` | OPEN, UNSTABLE, main보다 4커밋 뒤 | 실패 |
| #75 | Gate 0 fail-open 차단 | `task/p13-deletion-guard` ← `task/gate0-loop-proof@9fced45` | OPEN, **DIRTY(충돌)** — 현재 #74의 옛 버전 위에 있음(현재 #74 대비 19커밋 뒤) | — |
| #77 | 억제 ci-transfer-guarantee 해제 | `task/gate0-loop-proof` ← `task/ci-execution-proof@7dcba17` | OPEN, CLEAN | 기록 없음 |
| #78 | P13 약화 감시에 패턴 파일 추가 | `task/ci-execution-proof` ← `task/p13-patterns-scope` | OPEN, CLEAN | (참고, 억제 해제 없음) |

→ 기록의 "#109 UNKNOWN, #74 UNKNOWN"은 지금 둘 다 UNSTABLE(검사 실패)입니다. #110·#109의 빨간불은 WU1 코드 시험 실패가 아니라 억제 만료 한 단계 때문입니다.

억제(검사 예외) 장부 `suppressions.yaml` — main과 이 브랜치 내용 동일

| 억제 이름 | 만료 | 해제하는 PR | 상태 |
|---|---|---|---|
| `ci-transfer-guarantee` | 2026-09-15 | #77 (#75 위에 쌓임) | **만료됨** |
| `p13-deletion-blindspot` | 2026-09-15 | #74 | **만료됨** |
| `gate-scope-gaps` | 2026-09-30 | **없음** | 10/1부터 만료. 해제 PR이 열려 있지 않음 |

→ CI 검사는 `expiry < 오늘`이면 실패합니다. 지금 main 자체도 9/25 직접 push 이후 같은 단계로 빨갛습니다(run 36131725763).

main 병합 조건

- `gh api .../branches/main/protection`과 `.../rules/branches/main` 둘 다 **HTTP 403**("Upgrade to GitHub Pro or make this repository public"). → **확인 불가**.
- 이전 기록(2026-09-23 메모): 필수 검사 `verify` + 승인 리뷰 1건(마지막 push 승인, 관리자에게도 적용) + ruleset `acceptance-independent-gate`(배포 환경 `acceptance` 필수). 협업자는 sangmokang 1명뿐이라 본인 PR을 스스로 승인할 수 없음.
- 반대 방향 증거: 2026-09-25 11:51Z main에 PR 없이 직접 push(`fc6beed→f1f7a01`)가 성공했습니다. 관리자에게도 리뷰가 강제됐다면 거부됐어야 합니다.
- ※ 추정: 요금제가 바뀌어 보호 규칙이 지금 시행되지 않을 수 있습니다. 확인되지 않았으므로 **사장님이 GitHub 웹 Settings → Branches / Rules에서 직접 확인**해야 합니다.

## B. 실제 완료된 것 (커밋·코드 근거)

흐름: 최초 문제(후보 근거를 사람 판단 없이 등급으로 평가할 장치가 없음) → WU1 목표(등급표·계약 보호·전송 표기, Jev 판정) → Gateway 경유 호출 추가 → V1 적대검증에서 결함 발견 → RED→GREEN 수정 반복 → 마지막 키 노출 결함 수정.

| 무엇 | 위치 | 커밋 |
|---|---|---|
| 근거 평가 본체·CLI, 등급표 | `humansearch/src/humansearch/evidence_assessment.py`, `evidence_assessment_cli.py`, `tier_table.py`, `contracts/jev-evidence-assessment.json`, `contracts/{company,school}-tier.json` | 원격 `dbc7fd0`까지(#110) |
| 조직 shadow CLI가 저장소 라이브 스위치를 따름, 출력이 정책 파일을 덮지 못함 | `organization_shadow_cli.py` | `402c4cb`→`d4b3517`, `1f32f8a`→`f00de09` |
| 근거 평가 CLI가 Vercel AI Gateway(`https://ai-gateway.vercel.sh/typesafe`, 모델 `jev`)로 호출하고 호출 사실을 `jev_call`에 기록 | `evidence_assessment_cli.py`, `organization_shadow_jev.py`, `organization_shadow_validation.py` | `c648416`→`5330ad7` |
| V1 1차 결함 3건(재시도 과소 기록·키 되돌림 저장·조직 경로 완화) | 같은 파일 | `d409bfb`→`d983434` |
| V1 2차: 허용 목록 필드만 기록 | `evidence_assessment_cli.py` | `0ee7510`→`432a0d0`, `2788c66` |
| V1 3차: 키와 6글자 이상 겹치는 값 제거, 시도 기록 10개 상한 | 같은 파일 | `43098e3`→`9c76c38`, `479a592` |
| 마지막 S0: 응답의 모델 이름 필드로 키가 결과 파일에 들어갈 수 있던 문제 → 다른 기록 값과 같은 필터 적용 | `evidence_assessment_cli.py:91` (`response_model`을 `_text(..., key=key)`로 거름 — 결과 파일에 남는 모델 이름에서 키 조각을 지우는 줄) | `0f930fe`(RED)→`741f275`(GREEN) |
| 시험 | `humansearch/tests/test_evidence_assessment_{input,live,tiers,verdict}.py`, `test_organization_shadow_cli.py`, `ea_support.py`, `scripts/acceptance-evidence-assessment-mutations.sh` | 위 커밋들 |

계약 상태(실측): `contracts/jev-evidence-assessment.json` → `model_version "jev"`, `live_calls_allowed false`. 조직 shadow 계약은 `jev-1.13.0` 그대로(범위 밖).

## C. 검증 수준

이번 세션에서 직접 실행해 확인한 것
- git 상태·미푸시 21개·PR 6개 상태·CI 실패 단계(억제 만료 스캔 하나)·억제 3건·보호 규칙 403·main 직접 push 기록·main CI 실패 단계.
- Gateway 키 존재(`security find-generic-password ... >/dev/null` 종료값 0, 값 미출력).
- `uv run --frozen python -m pytest tests/test_evidence_assessment_live.py -q` → `40 passed in 0.41s`, 종료값 0 (마지막 S0 시험 포함 파일 하나만).
- `bash scripts/acceptance-principles-check.sh` → `MECHANISMS: PASS 34/34`, `WIRING: PASS pre-push=1 ci=1`, 종료값 0.

제공 기록·다른 검증자가 확인한 것 (이번 세션 미재현)
- hs-gates 전체(pytest 452 passed, ruff·mypy strict 58파일 0) — 커밋 메시지·문서에 452 기록 없음. 문서상 마지막 기록은 `9c76c38` 기준 pytest 450.
- 근거 평가 변이 86개 생존 0 — `9c76c38` 기준(문서 기록).
- V1 1~3차: Codex(다른 엔진) 세션, 세 번 모두 FAIL → 전부 수정. 판정 원문은 임시 폴더라 사라졌을 수 있음.
- 마지막 재검증: Codex 사용 한도 때문에 **별도 Claude 검증자**(구현 맥락 없음, 읽기 전용)가 수행. 같은 Claude 계열이므로 완전히 독립적인 검증이 아닙니다. 이 판정 원문은 저장소에 없습니다.
- 라이브 합성 1건: 2026-09-25T20:17:07Z, 코드 `72ec917` 시점, 제품 CLI, 결과 rc 0·키 0회. 이후 수정 뒤 라이브 재호출 없음. 실제 후보자 데이터 전송 0건.

미검증
- `741f275` 기준 hs-gates 전체, 변이 검사, 비밀 스캔(`bash verify.sh`).
- 억제 만료가 풀린 뒤 #110 CI가 초록인지.
- main 보호 규칙이 현재 시행 중인지.
- 수정 후 코드로 라이브 호출.

## D. 남은 위험

main 반영을 막는 것(blocker)
- S1 — 억제 2건 만료(9/15). 모든 PR·main CI 빨강. 그대로 두면 어떤 PR도 초록이 안 됨.
- S1 — 병합 조건 확인 불가(403). 기록대로 본인 외 승인이 강제되면 협업자 1명인 지금 어떤 PR도 병합 불가.
- S1 — 해제 체인 #75 충돌(옛 #74 위에 있음). #77은 #75 위에 쌓여 있어 같이 막힘.
- S2 — `gate-scope-gaps` 9/30 만료, 해제 PR 없음. 10/1부터 같은 빨간불이 다시 생김.
- S2 — #109·#110 기반이 main보다 4커밋 뒤. main 반영 전 갱신 필요(rebase는 force push가 필요하므로 금지 → merge 방식).

종료를 막지 않는 기존 사항 (기록상, 이번 세션 미재현)
- S2 — Gateway 공급자 미고정: 라우팅이 digitalocean(503) → typesafe-ai(200)로 기록됨. 그래서 실데이터를 보내지 않는 것이 현재 결정이며, 이 결정이 유지되는 한 main 반영과 무관.
- S2 — `organization_reference.py:118-125` 표본 2명(LIMITED)에서도 classification=high (기존, 미착수).
- S3 — 모델 이름 `jev`가 고정 버전이 아님(날짜별 결과 차이 가능). 키와 5글자 이하만 겹치는 조각은 안 걸러짐. 조직 shadow CLI의 SDK 기본 재시도(2회)로 요청 수 과소 기록 가능. 조직 shadow는 Gateway 미지원. `main(config=...)` 주입이 저장소 스위치보다 우선(제품 호출자 0건). not_run 결과 `error_reason None`.

확인된 열린 S0: 없음.

## E. 지금 하지 말 것

- WU1·Jev 기능 추가, 조직 shadow 경로의 Gateway 확장, 위 S2/S3 기존 사항 수정.
- 실제 후보자 데이터를 Jev/Gateway로 보내는 일(공급자 고정이 문서로 확인되지 않음).
- Gateway `/v1/evaluate` 전환·BYOK 조사 같은 공급자 경계 작업.
- V1/V2 재검증 추가 라운드(검증 계층 제한, 2026-09-18 사장님 지시).
- 새 추상화·새 시험 틀·새 문서 체계, 불필요한 리팩터링.
- `docs/engineering/goal-prompts/jev-gateway-provider-boundary-next-wu-2026-09-26.md`를 다음 작업 기준으로 쓰는 것. 이 문서는 "공급자 경계 결정(A/B/C) → V1 4회차 → 필요 시 새 HTTP 호출 코드"를 다음 단계로 잡고 있어 현재 결정(실데이터 전송 안 함·WU1 종료·다음은 integration)과 충돌합니다. **현재 다음 작업의 기준으로 사용하지 말 것.** 삭제·수정도 하지 않습니다(이력 보존).
- main 폴더의 untracked 파일 건드리기. 특히 `docs/engineering/goal-prompts/wu3-3-duration-experiment-2026-09-26.md`는 WU3 분석 실험(코드·Git 변경 없음)용이며, 거기 적힌 "WU1 be46261 마감"은 분할 전 옛 브랜치 `task/jev-evidence-assessment-wu1`의 9/23 끝 커밋입니다. 이 통합 작업과 의존 관계 없음 — 그대로 둡니다.
- 옛 브랜치 `task/jev-evidence-assessment-wu1`(다른 워크트리에 체크아웃됨) 삭제.

## F. 다음 작업 — main 반영 최소 순서 (실측 반영)

1. 0단계 재확인(아래 프롬프트 0단계).
2. **사장님 결정 1**: 만료 억제 2건 처리 — (가) 체인 정리: #75를 현재 #74 위로 다시 쌓고 충돌 해소 → #77 → #74부터 병합 / (나) 만료일 연장 커밋 1개(기록상 사장님 방침은 "유예를 기본 처리로 삼지 말 것"). 9/30 `gate-scope-gaps`도 같은 결정에 포함.
3. **사장님 확인 2**: GitHub 웹에서 main 보호 규칙·ruleset이 켜져 있는지. 켜져 있고 본인 외 승인이 필요하면 병합 경로가 없으므로 규칙 변경 여부가 사장님 결정 사항.
4. 억제가 풀려 main CI가 초록이 된 뒤 #109: main을 브랜치에 merge(force push 없이) → 승인 후 push → pull_request CI 초록 확인 → 병합 승인.
5. #110: 로컬 22개 커밋 push 전 게이트(hs-gates·비밀 스캔·원칙) → 승인 후 push → #109 병합 후 base를 main으로 바꾸는 것도 승인 대상 → pull_request CI 초록 확인 → 병합 승인.

※ 순서 2·3은 서로 독립이라 병행 확인 가능. 4·5는 2·3이 풀려야 의미가 있습니다.

## 결정 카드 — 이번 인수인계에서 내린 판단

> **무엇을** — WU1은 추가 수정 없이 종료하고 integration만 넘긴다.
> **왜** — CI 실패 원인이 WU1 코드가 아니라 억제 만료 한 단계뿐이고, 마지막 S0 시험 파일이 이번 세션에서 40건 통과. 남은 S2/S3는 main 반영을 막지 않는다.
> **버린 길** — provider-boundary 문서의 V1 4회차·공급자 고정 작업: 실데이터 전송을 안 하는 한 병합과 무관하고 검증 계층만 늘린다.
> **대가** — `741f275` 기준 전체 게이트와 라이브 재호출은 아직 없음 → push 직전 게이트에서 확인해야 함.
> **되돌리기** — 모든 변경이 로컬 커밋이라 push 전까지 비용 0. 문제가 나오면 해당 커밋만 RED→GREEN으로 추가.

---

## 다음 세션용 실행 프롬프트 (이 블록 전체를 복사해 새 세션에 붙여넣기)

```text
/strict

[VALUEHIRE-V6 — Jev 근거 평가 WU1 main 반영(integration)] L2. 새 기능 개발 금지. 검증된 변경을 main에 올리는 작업만 한다.

## 작업 위치 (반드시)
- 작업 폴더: /Users/kangsangmo/Desktop/Valuehire_v6/worktrees/jev-ea-wu1-split
  브랜치 task/jev-evidence-assessment-wu1-split. 모든 git 작업은 여기서만.
- /Users/kangsangmo/Desktop/Valuehire_v6 (main 폴더)는 다른 세션이 쓴다. checkout·수정·stash·commit 금지.
  그 폴더의 untracked 파일(.agents/, outputs/, docs/engineering/goal-prompts/wu3-3-duration-experiment-2026-09-26.md 등)은 다른 작업물이다. 손대지 않는다.
- 읽기 조회(gh pr view, gh pr checks, gh run view, gh api GET)는 자유. 쓰기(push, PR 수정·base 변경·병합, 브랜치 삭제)는 각 단계 직전에 사장님 승인 후에만.
- 금지: force push, --no-verify, rebase(원격 반영 브랜치), 브랜치 삭제, 새 기능, 리팩터링, 새 문서 체계, Jev 범위 확장,
  실제 후보자 데이터의 Jev/Gateway 전송, V1/V2 추가 라운드.
- 비밀값·후보자 데이터를 출력하지 않는다. 키는 `security find-generic-password -s valuehire-ai-gateway -a sangmokang >/dev/null` 로 존재만 확인.

## 2026-09-26 인수인계 시점 사실 (주장이다. 0단계에서 재확인하고 다르면 실제를 따른다)
- HEAD: 인수인계 문서 커밋(741f275 다음 1개). origin 끝 dbc7fd0, 미푸시 22개. working tree 깨끗.
- 이 브랜치와 #109 기반 브랜치는 origin/main 보다 4커밋 뒤(9/25 main 직접 push f12ea33 605973f fdb9a20 f1f7a01).
- 완료된 WU1: 근거 평가 CLI(evidence_assessment*.py, tier_table.py, contracts/jev-evidence-assessment.json)
  + Vercel AI Gateway 경유(모델 jev, jev_call 기록, 키 조각 필터, 시도 10개 상한, 재시도 0)
  + 마지막 S0(응답 모델 이름으로 키 유출) 0f930fe RED → 741f275 GREEN. live_calls_allowed=false.
- 기준 문서: docs/engineering/goal-prompts/jev-wu1-integration-handoff-2026-09-26.md (이 프롬프트의 원본).
  jev-gateway-provider-boundary-next-wu-2026-09-26.md 는 낡은 지시다. 따르지 않는다.
- PR: #109 main←task/jev-shadow-base-split (UNSTABLE) / #110 task/jev-shadow-base-split←wu1-split@dbc7fd0 (UNSTABLE)
  / #74 main←task/p13-deletion-guard (UNSTABLE, 억제 p13-deletion-blindspot 해제)
  / #75 task/p13-deletion-guard←task/gate0-loop-proof (DIRTY 충돌, 옛 #74 위에 있음)
  / #77 task/gate0-loop-proof←task/ci-execution-proof (CLEAN, CI 기록 없음, 억제 ci-transfer-guarantee 해제) / #78 #77 위(억제 무관).
- CI: #109·#110·#74·main 모두 verify 실패. 실패 단계는 "억제 만료 스캔 (suppressions.yaml)" 하나.
- suppressions.yaml: ci-transfer-guarantee 2026-09-15(만료), p13-deletion-blindspot 2026-09-15(만료), gate-scope-gaps 2026-09-30(해제 PR 없음 → 10/1부터 실패).
- main 보호 규칙: gh api 403(요금제) → 확인 불가. 9/23 기록은 필수 검사 verify + 본인 외 승인 1건 + ruleset acceptance 배포.
  그러나 9/25 main 직접 push가 성공함 → 지금 시행 여부 불명. 협업자는 sangmokang 1명.

## 0단계 — 재확인 (쓰기 없음)
a. 작업 폴더를 cwd로 쓰는 다른 세션: lsof -a -d cwd -Fpcn 을 awk로 p/c/n 필드 묶어 경로 대조.
   부모 PID 1인 Codex 브로커(app-server-broker)와 그 자손(codex app-server, oh-my-codex mcp)은 작업 세션이 아니다. 다른 작업 세션이 있으면 멈추고 보고.
b. git branch --show-current / git log -1 / git status --porcelain / git fetch 후
   git rev-list --left-right --count origin/task/jev-evidence-assessment-wu1-split...HEAD / git log --oneline origin/task/jev-evidence-assessment-wu1-split..HEAD
   / git rev-list --left-right --count origin/main...HEAD
c. PR 6개: gh pr view <n> --json state,baseRefName,headRefOid,mergeStateStatus,mergeable,reviewDecision (74 75 77 78 109 110)
   gh pr checks <n>, 실패면 gh run view <id> --json jobs 로 실패 단계 이름.
d. grep -nE '^- *check:|^ *expiry:' suppressions.yaml (main 과 이 브랜치 둘 다: git show origin/main:suppressions.yaml)
e. gh api repos/sangmokang/Valuehire_v6/branches/main/protection (GET). 403 이면 "확인 불가".
f. 결과를 "기록/실측/일치 여부" 표로. 불일치가 판단을 바꾸면 멈추고 보고.

## 1단계 — 사장님 결정 (코드 전, 두 가지만)
1) 만료 억제 처리: (가) 체인 정리 — #75를 현재 #74 위로 다시 쌓아 충돌 해소(새 커밋, force push 없이 가능한 방법으로) → #77 순으로 병합 준비
   / (나) 만료일 연장 커밋. gate-scope-gaps(9/30)도 함께 정한다. 사장님 방침: "유예를 기본 처리로 삼지 말 것".
2) main 보호 규칙: 사장님이 GitHub 웹 Settings → Branches·Rules 에서 현재 시행 여부 확인.
   본인 외 승인이 강제되면 병합 경로가 없다 → 규칙 변경은 사장님만 결정.
결정 없이는 2단계로 가지 않는다. 선택지를 2~3개로 좁혀 결정 카드(무엇을/왜/버린 길/대가/되돌리기)로 올린다.

## 2단계 — 결정된 범위만
- 억제 해제 체인을 먼저 처리하고 main CI 가 초록인지 확인(push 이벤트 + 이후 PR 은 pull_request 이벤트).
- #109: origin/main 을 task/jev-shadow-base-split 에 merge(rebase 금지) — 이 브랜치는 별도 워크트리가 필요하면 새로 만들고 main 폴더는 쓰지 않는다.
- #110: 이 작업 폴더에서 origin/main(또는 갱신된 shadow-base) 을 merge 한 뒤 push 준비.

push 직전 조건 (전부 PASS 아니면 push 금지, 사장님 승인 필수)
- 로컬 hs-gates: bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-gates.sh → 종료값 0, pytest·ruff·mypy 숫자 원문 기록.
- 근거 평가 변이: bash scripts/acceptance-evidence-assessment-mutations.sh → 종료값 0, 생존 0.
- 비밀 스캔: bash verify.sh → 종료값 0.
- 원칙: bash scripts/acceptance-principles-check.sh → 34/34.
- push 대상 커밋 목록을 git log --oneline origin/<branch>..HEAD 로 다시 뽑아 사장님께 보여 준다(예상: 22개 + merge 커밋). 목록 밖 커밋이 섞이면 멈춘다.
- pre-push 훅이 막으면 우회하지 않는다(--no-verify 금지). 원인을 보고한다.

merge 직전 조건 (전부 충족 + 사장님 승인)
- PR 최종 head SHA 가 로컬에서 검증한 SHA 와 같다.
- 그 SHA 의 verify 가 pull_request 이벤트 기준으로 success (push 이벤트 초록만으로 판단 금지).
- 보호 규칙이 요구하는 승인 리뷰가 충족됐다(또는 규칙이 없음이 확인됐다).
- #109 → #110 순서. #110 base 를 main 으로 바꾸는 것도 승인 대상.

## 중단 조건 (즉시 멈추고 보고)
- 다른 작업 세션이 같은 폴더를 쓰는 중.
- 미푸시 커밋 목록이 예상과 다름, 또는 working tree 에 모르는 변경.
- 게이트 하나라도 FAIL/NOT_RUN. 같은 방법으로 두 번 실패하면 세 번째 대신 보고.
- 충돌 해소에 WU1 코드 의미 변경이 필요해 보임.
- 보호 규칙상 병합 불가로 확인됨.
- 비밀값·후보자 데이터가 출력·커밋될 위험.

## 보고
§8: 결론 → 판단 근거 → 증거 원문. 각 단계 PASS/FAIL/NOT_RUN/BLOCKED, 배송 상태 LOCAL_ONLY 등.
끝나면 같은 폴더 docs/engineering/goal-prompts/ 에 결과 1개 파일만 추가하고 로컬 커밋(push 는 승인 후).
```
