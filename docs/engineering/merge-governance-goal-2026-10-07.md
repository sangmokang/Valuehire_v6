# PR 적체 정상화·병합 규칙 정리 — goal (2026-10-07)

위험등급 L3(CI·저장소 규칙 변경). 배송 상태 `NOT_APPLICABLE`(제품 동작 변경 없음 — 저장소 운영 규칙과 관제 스크립트).
증거 원문: `docs/engineering/evidence/merge-governance-20261007/` (수정 전 baseline, 실험 원문, 적용 전후 ruleset, PR 상태표, 리뷰 판정서).

## 1층 결론

- **main 병합을 막던 것은 `acceptance` 배포 요구 하나였고, 그 배포를 만드는 경로는 저장소 어디에도 없었다.** 9-17 이후 열린 PR 은 코드가 멀쩡해도 영원히 병합될 수 없었다(10-02 22:26 부터 실측 확인, 오늘 재현).
- 같은 규칙은 **명령 두 줄짜리 가짜 배포 기록으로 통과**됐다(오늘 임시 브랜치에서 재현). 막아야 할 것은 못 막고 막지 말아야 할 것만 막는 장치였다.
- 그 규칙을 **"PR 필수 + `verify` 검사 통과 + main 최신 기준"** 으로 바꿨다. 실패 PR·뒤처진 PR·PR 없는 직접 push 는 여전히 막히고, 정상 PR 만 풀린다(임시 브랜치와 실제 main 에서 실측).
- 열린 PR 55개 분류: 병합 가능 1(#122) · 수정 필요 12 · 대체/중복 5 · 사람 결정 37.
- 매일 09:00 KST 에 "지금 봐야 할 PR" 을 🔴/🟡/🟢 로 이슈 댓글 하나에 남기는 관제를 추가했다(이 PR 병합 후 동작).
- **가장 급한 일: 10-13 에 억제 3건이 만료되면 모든 PR 의 CI 가 다시 빨개진다.** 그 전에 연장하거나 해제 체인(#74→#75→#77→#78)을 정리해야 한다.

사장님 결정:
1. 이 PR 병합(규칙 문서화·관제 배선).
2. 10-13 억제 만료 대응 — 기한 재연장(1줄 PR) 또는 해제 체인 정리.
3. 쓰이지 않는 `acceptance` 환경 삭제 여부(남겨도 지금은 아무것도 막지 않는다).

## 2층 판단 근거

### 수정 전 baseline (2026-10-06T16:16Z, 원문 `baseline-gate.txt`)

| 항목 | 값 |
|---|---|
| origin/main | 55240f7 (10-02, #111) |
| 열린 PR | 55개 |
| 고전 branch protection | 없음(404) |
| ruleset | `acceptance-independent-gate`(23568184, 09-17 생성, 버전 1개) — `required_deployments: [acceptance]`, 우회자 없음 |
| `acceptance` 환경 | 지정 승인자 sangmokang·자기승인 금지·보호 브랜치에서만 배포 |
| 배포 기록 | 0건(전체) |
| `environment:` 를 쓰는 workflow | 모든 원격 브랜치 이력에서 0건 |
| main 대상 PR 상태 | 전부 `BLOCKED` (base 가 main 이 아닌 스택 PR 만 `CLEAN`) |

→ 규칙은 "acceptance 에 배포 성공한 커밋만 main 에 들어온다"인데, 그 배포를 만드는 workflow 가 한 번도 커밋된 적이 없다. 2026-09-18 goal(`verification-trust-core-hardening-goal-2026-09-14.md`, 미병합 브랜치)이 workflow 쪽 `environment: acceptance` 배선을 삭제했고 ruleset 만 남았다.

### 근본 원인 분리

| 범주 | 해당 | 근거 |
|---|---|---|
| 존재하지 않는 deployment 요구 | **main 대상 PR 전부** | 위 baseline, 실험 A-2 |
| 테스트 실패(시간 부패) | 17개 | 실패 단계가 `억제 만료 스캔` — 9-15 만료 후 10-02 연장 전에 돈 CI(`baseline-pr-fail-steps.tsv`) |
| 테스트 실패(실제 검사) | #83(G2 테스트 게이트), #44·#45(P3 조용한 실패 lint), #120(히스토리 스캔) | 같은 파일 |
| merge conflict | #14 #15 #37 #43 #48 #68 #74 #75 #110 | `mergeable: CONFLICTING` |
| 스택(base≠main) | 12개 | `baseRefName` |
| 초안 | 14개 | `isDraft` |
| 리뷰 결함 | #123(재현), #109(외부 리뷰 S2×3, 미재현) | 아래 분류 |
| 중복·폐기 경로 | #118 #120 #121 | 트리 대조 |
| 아직 검토 안 됨 | 거의 전부 — 리뷰·승인 기록 0 | `reviews` 0건 |
| CI 자체 장애 | 없음 | main 마지막 verify 10-02 success |

### 반례 A~E 판정

| 반례 | 지켜야 할 규칙 | 실제 설정·코드 | 예상 | 실제 확인 | 반대 증거 | 판정 |
|---|---|---|---|---|---|---|
| A 정상 PR 이 없는 배포 때문에 영구 차단 | 정상 PR 은 실재하는 검사만 통과하면 병합 가능 | ruleset `required_deployments[acceptance]`, 배포 경로 0 | 차단 | 실험 A-1/A-2 405 `Missing successful active acceptance deployment`, rule-suite 10-02 22:26 cursor[bot] push fail | #111(10-02 01:36Z)·09-25/09-28 직접 push 는 통과 — 판정 기록 자체가 없음(평가 안 됨, 원인 UNRESOLVED) | **REPRODUCED**(현재 시점) |
| B 실제 배포 없이 이름만 같은 기록으로 우회 | 검증은 위조 불가해야 | 환경 보호 규칙은 Actions job 에만 적용 | 우회 가능 ※ | 실험 B-2/B-3: API 배포 + success 상태 → 병합 성공 | 없음 | **REPRODUCED** |
| C 게이트 제거로 꼭 필요한 production 검증이 사라짐 | 운영 배포 검증은 유지 | 운영 배포 workflow 0, `acceptance` 배포 0건, 운영 배포를 병합 전 필수로 요구하는 SOT 없음(`git-workflow.md` 는 PR·CI·태그 릴리스) | 사라질 것 없음 | 배포 기록 0, 환경 1개(acceptance)뿐 | 9-17 의도는 "자기승인 불가 독립 검토"였으나 9-18 goal 이 일반 개발에서 제외 결정 | **NOT_REPRODUCIBLE**(잃는 검증 없음) |
| D 규칙·workflow 의 검사 이름 불일치로 교착 | 요구 이름 = 실제 발행 이름 | 요구 `verify`(Actions 앱 15368) ↔ `verify.yml` job id `verify` | 일치 | 실험 POS-1 `CLEAN`, 실제 #122/#123 `CLEAN` | review-status 브랜치(미병합)가 새 workflow 를 추가하나 job 이름이 다름 | **NOT_REPRODUCIBLE** |
| E fork·bot·Dependabot 만 영구 대기 | 출처와 무관하게 같은 조건 | `verify.yml` 은 `pull_request` 전체에 반응. Dependabot 설정 없음. cursor[bot] PR(#117~#121)도 verify 결과 있음 | 대기 없음 | cursor[bot] PR 5건 모두 verify 실행 기록 있음 | 첫 외부 기여자 fork PR 은 공개 저장소 기본값으로 workflow 실행에 사람 승인이 필요 — 승인하면 풀림(교착 아님) ※미실험 | **NOT_REPRODUCIBLE**(fork 첫 기여 승인 대기는 정상 동작) |

### 결정 카드

> **무엇을** — ruleset 23568184 의 규칙을 `required_deployments[acceptance]` → `pull_request(승인 0)` + `required_status_checks[verify @ GitHub Actions]` + `strict` 로 바꾸고 이름을 `main-pr-verify-gate` 로 고쳤다.
> **왜** — 실재하고 위조가 어려운 검사(Actions 가 발행한 `verify`)에 병합을 묶는다. `pull_request` 는 지금 우연히 막히던 main 직접 push 를 정식으로 막는다(정본 `git-workflow.md:20` "직접 push 금지, 오너 본인도 예외 없음"). `strict` 는 9월의 옛 초록불로 병합하지 못하게 한다.
> **버린 길** — ① 규칙 삭제: 실패 PR·직접 push 가 무방비가 된다. ② 승인 1명 이상: 작성자는 자기 PR 을 승인할 수 없어 1인 저장소는 다시 교착. ③ `acceptance` 배포 workflow 신설: 운영 배포 대상이 없고 9-18 결정과 충돌하며 위조 가능성은 그대로. ④ strict 끔: 뒤처진 옛 초록 PR 이 현재 main 과 합쳐 본 적 없이 병합된다(main 대상·초안 아님·BEHIND 26개, `after-rule-pr-state.tsv`).
> **대가** — main 이 바뀔 때마다 다른 PR 은 "Update branch" 후 CI(약 4~6분)를 다시 기다려야 한다. PR 이 자기 `verify.yml` 을 약화하면 그 PR 의 검사도 약화된 채 초록일 수 있다(사람 diff 검토가 방어선).
> **되돌리기** — `gh api -X PUT repos/sangmokang/Valuehire_v6/rulesets/23568184 --input docs/engineering/evidence/merge-governance-20261007/ruleset-main-before.json` 한 줄(1분).

> **무엇을** — 관제는 GitHub 상태만 읽는 69줄 스크립트 + 매일 1회 이슈 댓글.
> **왜** — GitHub 기본 알림 메일을 그대로 쓰므로 새 서버·DB·메일 경로가 없다. 어디서 돌려도 같은 답이 나온다.
> **버린 길** — `task/review-status`(1,789줄, 미푸시): LLM 리뷰 장부·메일·댓글 갱신까지 묶여 있어 "관제 자체가 관리 대상"이 된다. 장부가 Mac 에만 있어 Actions 에서 못 읽는다.
> **대가** — 리뷰 결함은 GitHub 이 모르므로 사람이 `needs-fix` 라벨을 달아야 🔴 로 뜬다.
> **되돌리기** — `pr-triage.yml` 삭제(스크립트는 수동 실행용으로 남겨도 무해).

## 인수 기준 (EARS) · 검증 명령 · counter-AC

| ID | EARS 단언 | 검증 명령 → 기대 | counter-AC(가짜 완료) |
|---|---|---|---|
| AC-1 | When main 대상 PR 의 최신 head 에 Actions `verify` 가 성공이고 충돌 없고 main 최신이면, 시스템은 병합을 허용해야 한다 | `gh pr view <n> --json mergeStateStatus` → `CLEAN` (실측 #122/#123, 실험 #126/#128) | 규칙을 지워서 CLEAN 이 된 것 |
| AC-2 | If `verify` 가 실패하면, 시스템은 병합을 거부해야 한다 | 실험 NEG-1 405 `is failing`; 실제 #116 405 | 실패 PR 이 BEHIND 라서만 막힌 것(→ NEG-1 은 base 최신 상태에서 실패로 거부) |
| AC-3 | If PR 없이 main 에 push 하면, 시스템은 거부해야 한다 | 실험 NEG-2a/2b 422 `Changes must be made through a pull request` | 검사 미완료라서만 거부된 것(→ 2b 는 검사 완료 후) |
| AC-4 | While PR 이 main 보다 뒤처져 있으면, 시스템은 옛 초록으로 병합을 허용하지 않아야 한다 | 실험 STRICT-NEG 405 → update 후 STRICT-POS 성공; 실제 #85 405 | strict 없이 옛 초록 통과 |
| AC-5 | When 관제를 실행하면, 시스템은 CI 실패·충돌·needs-fix 를 🔴, CLEAN+CI 성공만 🟢, 나머지를 🟡 로 출력하고 조회·형식 실패는 종료값 2 여야 한다 | `bash scripts/verify/run-acceptance.sh scripts/acceptance-pr-triage.sh` → `VERDICT: PASS`, `CHECKED: 25` | CLEAN 만 보고 CI 없음·초안을 🟢 로 |
| AC-6 | 규칙 변경 후 우회 권한자는 0 이어야 한다 | `gh api .../rulesets/23568184 --jq .bypass_actors` → `[]` | 관리자 우회를 열어 둔 채 "막힌다" 주장 |

## 테스트 실행 기록

| 검사 | 결과 |
|---|---|
| `bash scripts/acceptance-principles-check.sh` (Strict 시작) | PASS, CHECKED 34, rc 0 |
| `acceptance-pr-triage.sh` RED(구현 없음) | FAIL rc 1 — 8f3d5a9 |
| 같은 시험 RED(needs-fix 규칙 없음) | FAIL `#13 이 '🔴' 칸에 없다` — 48bc61a |
| 같은 시험 GREEN | PASS 26판정/CHECKED 25 — f2652b9 |
| 뮤테이션 10종(충돌·CI 요구·스택·잘림·뒤처짐·형식실패·ERROR·초안·라벨·미변경 기준) | 10/10 KILLED, 무변경 대조군 SURVIVED |
| `check-mechanism-registry.sh` | PASS CHECKED 21 (pr-triage-ci 포함) |
| `check-ci-step-integrity.sh verify.yml` | PASS 32 |
| `pr-triage.sh` 실제 실행(읽기 전용) | rc 0, 55개 → 🔴21 🟢1 🟡33 (`triage-after-rule-change.md`) |
| 병합 규칙 실험 매트릭스 | `probe-matrix.md` — A·B REPRODUCED, POS/NEG/STRICT 전부 기대대로 |
| `pr-triage.yml` 실제 예약 실행·이슈 댓글 | **NOT_RUN** — 기본 브랜치에 있어야 예약·수동 실행이 가능. 병합 후 `gh workflow run pr-triage` 1회로 확인 |
| `check-ci-step-integrity.sh pr-triage.yml` | 해당 없음 — 검사기의 동시성·30분 계약은 verify job 전용(`check-ci-step-integrity.sh:19` 기본 대상 verify.yml). 일반 규칙(조건부·오류무시 스텝)은 새 workflow 에 없음 |

## PR 55개 분류 (2026-10-07 01:4x KST, 새 규칙 적용 후 상태 `after-rule-pr-state.tsv`)

### A — MERGE_READY (1)
- **#122** herdr 런처 — `CLEAN`, CI 초록(10-04, 현재 main 기준), 리뷰 PASS(S0/S1 0). 후속 S2 2건: 사용자 지정 PowerShell 명령 실패를 성공으로 보고 가능(`vh-herdr.ps1:177`), 분리 HEAD 커밋 손실 가능(`:262-272`). Windows 실측 미확인. herdr 도입 자체를 원하시는지는 확인 필요.

### B — FIX_REQUIRED (12)
| PR | 심각도 | 결함 | 증거 상태 |
|---|---|---|---|
| #123 | S1 | 통합·재감사 단계 검사기가 확인할 경계가 전부 미확인이어도 `COVERAGE_OK`(`check_wu.py:43-67`), 검토 파일 0개 WU 도 합격 | REPRODUCED(직접 실행) · `needs-fix` 라벨 부착 |
| #123 | S1 | 첨부 생성 실패 시 빈 첨부 + "0줄까지 봄" 통과(`gpt_bundle.py`) 외 S2 5건 | NOT_TESTED(리뷰어 재현, 본인 미재현) |
| #74 #75 #77 #78 | S1(시한) | 억제 3건 10-13 만료 → 모든 PR 의 `verify` 실패. 이 체인이 2건을 해제하는데 #74·#75 충돌 | REPRODUCED(`suppressions.yaml` expiry 2026-10-13, 만료 스캔 코드) |
| #109 | S2 | 브랜치 쪽 CI(push) 실패(브랜치의 억제 파일이 옛 기한) + 외부 리뷰 S2×3(`validation.py:96`, `cli.py:109-122`, `antiforge.sh:38-42`) + 3,905줄(P11③ 3,000줄 초과) | CI REPRODUCED / 리뷰 결함 NOT_TESTED |
| #110 | S2 | `DIRTY` 충돌 + #109 위 스택 + 3,922줄 | REPRODUCED |
| #83 | S2 | CI `HumanSearch G2 테스트 게이트` 실패(시간 부패 아님) + 15,677줄(P11③ 5배) | REPRODUCED |
| #44 #45 | S2 | CI `P3 조용한 실패 문법·오탐 회귀` 실패(실제 lint 위반) · 40일 미변경 | REPRODUCED |
| #104 | S2 | 7,703줄(P11③ 초과), `outputs/` 실행 산출물 49개 커밋(P21 데이터는 git 밖) — 후보자 개인정보는 검색 0건(채용공고 문구만) | REPRODUCED |
| #105 | S2 | 7,557줄(P11③ 초과) 스냅샷 | REPRODUCED |

### C — SUPERSEDED_OR_DUPLICATE (5)
| PR | 대체 근거 |
|---|---|
| #120 | #121 과 트리 완전 동일(`git diff` 0줄), head 브랜치 삭제됨 |
| #118 | #121 의 조상 커밋(`merge-base --is-ancestor` 참), 10개 파일 동일 blob |
| #121 | GitHub Actions + XAI API 리뷰 경로는 2026-10-06 사장님 결정으로 폐기 — 대체: #123 llmcodereview(Aside × Cursor 웹) |
| #119 | 10-02 시점 "열린 PR 병합 판정" 스냅샷 — 이 문서의 10-07 baseline·분류와 `pr-triage.sh` 가 대체 |
| #108 | 핵심 파일 `docs/sot/strict-workflow.md` 는 f12ea33 으로 이미 main 에 있음(차이 2줄). 남은 고유분은 판정 문서 2개·goal 문서 증분 — 보존 여부만 결정 |

### D — STALE_NEEDS_DECISION (37)
| 묶음 | PR | 사람 결정이 필요한 이유 |
|---|---|---|
| 갱신만 하면 판정 가능(작고 최근) | #116 #115 #112 #102 #107 #103 | 실패 원인이 억제 만료(시간 부패)뿐. "Update branch" 1회로 현재 main 기준 CI 가 판정. 브랜치에 커밋이 추가되므로 다른 세션 작업 여부 확인 후 실행 |
| HumanSearch 계열 | #85 #86 #88 #91 #92 (main) · #87 #89 #90 #93 #94 #96 #97 #100 (스택) · #95 (초안) | 9-14 작성, 이후 HS v5 정본으로 바뀜. 스택 순서대로 갱신·병합할지, v5 기준으로 다시 짤지 |
| 오래된 충돌 | #14 #15 #37 #43 #48 #68 | 19~73커밋 뒤처진 채 충돌. 되살리려면 충돌 해소(재작성 수준). #37 의 work-unit 정본은 9-18 goal 이 삭제 대상으로 지정 |
| 오래된 문서·인프라(옛 초록) | #47 #54 #61 #63 #65 #66 #67 #79 | 19~42커밋 뒤처짐. 여전히 필요한지 |
| 초안 | #106 #114 #117 | 작성자가 완료 표시 전 |

## 잔여 위험·미확인

- **R-1** PR 이 `verify.yml` 을 약화하면 그 PR 의 `verify` 도 약화된 채 초록 — 필수 검사는 PR 쪽 workflow 로 돈다. 방어선은 사람 diff 검토(자동 병합 금지). NOT_TESTED.
- **R-2** 10-02 이전 직접 push·#111 병합이 규칙 평가 없이 통과한 원인 UNRESOLVED.
- **R-3** 같은 SHA 에 push·pull_request 두 `verify` 가 있고 결과가 갈릴 때(#109) GitHub 이 어느 쪽을 보는지 NOT_TESTED. 어느 쪽이든 PR 결과(병합 결과물 검사)가 실패면 막힌다.
- **R-4** `pr-triage.yml` 예약 실행·이슈 생성·댓글 알림 NOT_RUN(병합 후 확인).

## 적대 검증 로그

(아래에 V1·V2 원문 경로와 판정을 덧붙인다.)
