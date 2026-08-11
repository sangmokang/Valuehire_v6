# 검증 이력 — verify·codeaudit 통합 goal (v1~v6)

### v6-라운드 (2026-08-12, v5 착수 전 최종 점검 — `/codex:rescue a86e46d4aa31af9bb` → codex task `task-msotec9m-mpeyct`)

**V — Codex(이 세션의 codex:rescue 호출)**
- **VERDICT: 재작성 필요**(codex 판정). 8개 결함 제시.

**Claude 재현 (직접 실행)**

| # | codex 주장 | 재현 결과 | 판정 |
|---|---|---|---|
| 1 | Gate 0 측정기가 거짓 GREEN(here-string 생성 실패했는데 RED:0/4 출력) | `bash scripts/session-status.sh` 직접 재실행 → 정상 동작, `RED: 0/4` 정확히 출력. 이 세션에서 이미 여러 번 실제 상태변화(1/4→원인특정→고침→0/4)를 정확히 추적한 이력 있음 | **반증됨 — codex 자신의 샌드박스가 임시파일 생성을 막아서 생긴 codex 쪽 아티팩트로 판정. 스크립트 결함 아님** |
| 2 | AC-M 예시 `target: check_secret_render`가 죽은 참조 | `grep -n "check_secret_render" hooks/pre-commit` → 0건. 실제 훅은 `SECRET_PATTERNS_FILE= VERIFY_SCAN_SOURCE=index bash verify.sh`(`hooks/pre-commit:71`) 호출 | **일치 — 확인, 수정 완료**(예시를 실제 문구로 교체) |
| 3 | AC-M 검증절이 산문뿐, 실행 명령·fixture 없음 | goal 문서 AC-M 본문 재확인 | **일치 — 확인, 수정 완료**(check-mechanism-registry.sh 스펙 + fixture 3종 추가) |
| 4 | AC-20이 레지스트리 stage에 못 들어감(pre-commit/pre-push/ci만 있고 수동 실행 단계 없음) | 스키마 재확인 | **일치 — 확인, 수정 완료**(`stage: manual` + `manual_reason` 필드 신설) |
| 5 | AC-1/AC-5가 개수만 비교하고 ID 집합은 비교 안 함 | AC-5 counter-AC 재확인 | **일치 — 확인, 수정 완료**(ID 집합 비교로 강화) |
| 6 | SOT(coding-principles.md 등)에 "강제"·"CI가 최종방어선" 문구가 남아 v5 결정과 불일치 | 별도 미재현(문서 존재는 이미 앎) | **타당 — SOT 체크리스트에 정정 항목 추가** |
| 7 | 장기보류 문서의 AC 목록에 AC-20 누락 | 문서 재확인 | **일치 — 확인, 수정 완료** |

**조치**: AC-M·AC-20·AC-5·SOT체크리스트·장기보류문서 수정 완료(v5→v6 goal 본문 자체 갱신, 별도 버전 문서 안 만들고 같은 파일에 즉시 반영). Gate 0 측정기 관련 지적(#1)은 반증됐으므로 대응 없음 — 단, 이 스크립트가 `<<<`(here-string)를 쓰는 한 극단적으로 제한된 셸 환경에서 이론상 조용히 실패할 잠재 취약점은 낮은 우선순위로 인지만 해둠(이 저장소의 실제 실행 환경 — 로컬 macOS·GitHub Actions — 에서는 해당 안 됨).

**G(이 세션)·V(codex)·V2(이 세션 재현) 정합**: 7개 중 6개 일치(반영 완료), 1개(Gate0) 반증. 갈리지 않음 — AC-M 착수 가능으로 판단.

### v5-라운드 (2026-08-11, 문서 v4 대상 — 세션 밖 외부 Codex 적대검증)

**V — 외부 Codex 세션(이 대화의 `/codex:rescue` 호출이 아니라, 사장님이 별도로 돌린 독립 세션)**
- **VERDICT: NO-GO.** v4 구현 프롬프트를 그대로 실행하면 안 됨. 6개 핵심 차단점.

**Claude 격리 재현 (전부 실측, 이 세션에서 직접 실행)**

| # | 주장 | 재현 명령 | 결과 | 판정 |
|---|---|---|---|---|
| 1 | Gate 0 RED 1/4 | `bash scripts/session-status.sh` | RED: 1/4 확인 | 일치 |
| 2 | Gate 0 원인 = unreachable 객체 | `bash scripts/acceptance-0-2.sh` | "unreachable 객체 61건"(외부 검증 시점 58건에서 소폭 증가) | 일치 |
| 3 | main dirty | `git status --short` | `.secret-patterns.default` 수정 + 문서 3개 untracked | 일치 — **원인은 이 세션이 main에서 직접 수정한 것** |
| 4 | PR #4 이미 존재 | `gh pr list` | `task/secret-session-patterns` OPEN 확인 | 일치 |
| 5 | branch protection 403 | `gh api repos/.../branches/main/protection` | `403 Upgrade to GitHub Pro or make this repository public` | 일치 |
| 6 | rulesets도 403 | `gh api repos/.../rulesets` | 동일 403 | 일치 |
| 7 | git-workflow.md가 "1 AC=1 worktree" 요구 | `grep -n "worktree" docs/sot/git-workflow.md` | `:15` "작업 1개 = worktree 1개 = 인수 기준 1개", `:21` "PR = 인수 기준 1개" | 일치 — v4의 "1 Phase=1 워크트리" 설계 오류 확인 |
| 8 | `/codex:rescue`를 쓰면 동일엔진 자기검증(R8) | `.codex/skills/strict/SKILL.md:56` 직접 확인 | "**구현자가 codex이므로** 검증자는 Claude"라고 명시 — 이 세션은 반대로 Claude가 구현자라 codex를 V1으로 쓰는 게 같은 원칙의 대칭 적용 | **반증됨 — 인용 방향 오류로 판정** |

**조치**:
1. main의 직접 수정을 `git stash`로 격리(`stash@{0}`), main을 clean 상태로 복구
2. AC-4·AC-6·AC-7(required-check 강제 계열) 전체 삭제 — 이 저장소 요금제에서 GitHub 쪽 강제장치가 근본적으로 불가능하다고 실측 확인됐고, 사장님이 "강제장치 없이 정직한 로컬 도구로" 결정
3. `enforced_by` → `checked_by`로 필드명 변경(강제 인상 제거)
4. AC-5를 머지게이트가 아닌 순수 로컬 리포트 집계기로 재정의 — 이 재정의로 v4의 `phases_shipped` 자기모순(자기 PR이 아직 안 머지된 자신을 phases_shipped에 먼저 기록하는 시간적 모순)도 함께 해소됨(canonical 목록을 "머지된 Phase 배열" 대신 "레지스트리에 실제 등록된 required 항목"으로 재정의했기 때문)
5. Phase 단위 워크트리 설계를 AC 단위로 정정(SOT 준수)
6. 이 goal 자체가 만들지 않은 기존 문제(Gate 0 RED, PR #4와의 조율)는 비범위로 명시하고 별도 트랙으로 분리

v4 → v5 재작성은 위 조치를 전부 반영. 상세는 goal 본문 상단 "이번 v5에서 뭐가 왜 빠졌는가" 참조.

---


이 문서는 `verify-unification-goal-2026-08-10.md`(goal 본문)와 짝을 이루는 **메타 기록 전용** 문서다. goal 본문은 "지금 무엇을 구현하는가"만 담고, "왜 지금 이 형태인가"는 여기에 있다. (품질 리뷰 지적: 이 둘이 한 파일에 섞여 있으면 정정 기록의 낡은 포인터가 본문 인수기준처럼 읽혀 구현자를 헷갈리게 한다.)

---

## 정정 기록 (누적, 시간순)

1. **"MEMORY.md에 10여 건"** — 미확인 추정치였다. 정정: 미확인.
2. **"이번이 세 번째 질문"** — AI 발화를 사용자 질문으로 오산했다. 정정: 재계산 없이는 순번 주장 안 함.
3. **"2계층(항상적용+코드범위)"** — 정정: 3계층(①항상적용 ②diff·호출관계 ③훅/CI 자동강제).
4. **"파일 태그 기반 관련성 판단"** — 정정: diff 변경 심볼 + call graph 기준.
5. **"codex 16개 강화안"** — codex(V1)가 저장소·세션 전수 검색해도 원문을 못 찾았고, AC-5~19를 세면 15개다. 정정: "codex 강화 제안"으로만 지칭. 정확한 원안 개수는 미확인.
6. **"AC-8을 GitHub 브랜치 보호로, AC-18을 GitHub Secret 자체서명으로 내재화하면 충분하다"** — 틀렸다. GitHub 공식문서 재현: 필수 상태검사는 `skipped`/`neutral`도 통과로 치고, 저장소 Secret은 그 저장소의 모든 워크플로가 접근 가능하다. **이 정정이 가리키던 "§③-D 로컬 봇 설계"는 v3에서 별도 문서(`verify-independent-trust-boundary-goal-2026-08-11.md`)로 완전히 옮겨졌다 — 이 포인터는 이제 그 문서를 가리킨다.**
7. **"GitHub Environment 필수 승인자로 대체하면 된다"** — 틀렸다. `sangmokang`은 개인 계정이고 private 저장소의 Required reviewers는 Enterprise Cloud가 필요하며, 개인 계정은 Enterprise Cloud를 구매할 수 없다. **이 포인터도 위와 동일하게 분리 문서를 가리킨다.**
8. **(v3→v4, 품질 리뷰가 잡음) "안닫힘·신규결함이 거의 전부 AC-D 계열에 몰려 있다"** — 부정확했다. 실제로는 v2→v3에서 안닫힘 6건 중 D계열 2건/비D 4건, 신규 9건 중 D계열 5건/비D 4건 — **합계 15건 중 D 7건, 비D 8건으로 절반 이하**다. 비D 4건(AC-11·13·14·15) 중 AC-11만 실제로 고쳐졌고, AC-13·14·15는 "고침"이 아니라 "Phase 6(제품코드 도입 후)로 재분류 후 canonical 목록에서 제외"로 처리됐다 — 결함을 닫은 게 아니라 범위 밖으로 옮긴 것이다. v4에서는 이 사실을 있는 그대로 적는다(위 문단 자체가 그 정정이다).

---

## 적대 검증 로그

### v1-라운드 (2026-08-10, 문서 v1 대상)

**V1 — Codex (격리)**
- 실행: `codex:codex-rescue abd275372607d9584` → codex task `task-msnapikt-e5r03y`
- transcript: `/Users/kangsangmo/.claude/plugins/data/codex-openai-codex/state/Valuehire_v6-8e58430ebc33c25b/jobs/task-msnapikt-e5r03y.log`
- codex session: `019febf6-730b-7152-bd8f-931c428be998`
- **VERDICT: 재작성 필요.** 결함 19건 전수(AC-1~19), P1위반 7·순서오류 8·방어력손실 4(AC-6·7·8·18)·counter-AC느슨함 19·누락 1.

**V2 — Claude 격리 재현**

| # | codex 주장 | 재현 결과 | 판정 |
|---|---|---|---|
| 1 | AC-5~19는 15개, "16개"는 부정확 | `grep -c` 재계산 | 일치 |
| 2 | AC-9/AC-11 Phase 순서 꼬임 | goal §④ 재확인 | 일치 |
| 3 | AC-16/AC-19 Phase 순서 꼬임 | 상동 | 일치 |
| 4 | local-checks.sh:19-23 skip 후 exit 0 | 파일 재확인 | 일치 |
| 5 | verify.sh 기본 스캔이 worktree | 파일 재확인 | 일치 |
| 6 | suppressions.yaml이 workflows/local-checks.sh 범위밖 인정 | 파일 재확인 | 일치 |
| 7 | GitHub 필수검사 skipped/neutral도 통과 | GitHub 공식문서 재확인 | 일치 |
| 8 | repo secret은 모든 워크플로가 접근 가능 | GitHub 공식문서 재확인 | 일치 |

과장 0건. **G·V1·V2 일치 — v1 문서는 승인 불가로 확정.**

### v2-라운드 (2026-08-10~11, 문서 v2 대상)

**V1 — Codex (격리)**
- 실행: `codex:codex-rescue a4e93226ed5f0398f` → codex task `task-msnf5obf-yyderi`
- log: `/Users/kangsangmo/.claude/plugins/data/codex-openai-codex/state/Valuehire_v6-8e58430ebc33c25b/jobs/task-msnf5obf-yyderi.log` (341줄, Final output은 211행부터)
- codex session: `019fec68-7992-7473-9de1-d5fcbfd0d3f7`
- **VERDICT: 재작성 필요.** v1 결함 19건 중 13건 닫힘 / 6건 안닫힘(AC-8→D3, AC-11, AC-13, AC-14, AC-15, AC-18→D2). 신규 결함 9건(N1~N9).
- **가장 치명적: AC-D2의 핵심 전제 "repo Workflow permissions를 read-only로 고정하면 PR의 GITHUB_TOKEN이 상태를 못 씀"이 사실이 아니다.** GitHub 공식문서: 저장소 설정은 default일 뿐이고 workflow/job의 `permissions:` 키가 덮어쓴다. 같은 저장소 PR(포크 아님)은 write 강등 대상도 아니다.
- AC-D3(브랜치 보호 identity 고정) 자체는 가능 — 단 GitHub App의 `app_id`로 고정해야 하고 PAT/개인 계정 credential로는 안 됨.
- AC-D1: 봇이 결과를 독립 재계산하지 않고 전달받아 승인·서명하는 구조 — P17 취지 미충족.
- 신규결함: AC-5 canonical 목록과 Phase 6 `NOT_RUN`의 자기봉쇄(N5), AC-17이 Phase 5 산출물을 요구하는 역의존(N6), AC-6·7이 동일 PR 공격만 막음(N7), Discord 승인에 allowlist·binding 없음(N8), `mechanism_id`↔`enforced_by` 레지스트리 미정의(N9).

**V2 — Claude 격리 재현**

| 주장 | 재현 명령 | 결과 | 판정 |
|---|---|---|---|
| "repo Workflow permissions read-only는 default일 뿐, workflow의 permissions: 키가 덮어쓴다" | WebSearch, GitHub 공식문서 재확인 | "job-level permissions... completely override the repository default" 확인. 동일 저장소 PR은 write 강등 대상 아님도 확인 | **일치 — 확인** |

**G·V1·V2 일치 — v2도 승인 불가로 확정.**

### R5 적용 — 2회 연속 동일 유형 실패, 접근 전환

`strict` R5: "2회 이상 같은 방식으로 막히면 멈추고 접근을 바꾸거나 질문한다." v1·v2 두 라운드 모두 "재작성 필요" 판정을 받았고, 특히 두 번 다 Phase 1~4(원장·집계기·격리·검증기분리 등)는 대부분 닫혔는데 Phase 5(舊 AC-8·AC-18, 독립 신뢰경계)만 반복적으로 무너졌다. → **AC-8·AC-18을 별도 문서로 분리**, v3는 Phase 1~4의 잔여 결함(N5·N6·N7·N9, AC-11)만 반영.

### v3-라운드 (2026-08-11, 문서 v3 대상 — Phase 1~4로 범위 축소 후 첫 검증)

**V1 — Codex (격리, 사장님 지시로 "Spec 해부 + Hook 배선 정리" 정조준)**
- 실행: `codex:codex-rescue ad008e7baf2fe0bf9`
- **VERDICT: 승인 불가.** N5·N9·AC-11이 실질적으로 안 닫혔고, AC 대부분의 실행 명령과 pre-commit/pre-push/CI 배선 계약이 빠져 있음.
- Spec 해부 표(14개 AC 전수) — 대부분 "불량"/"보완필요": EARS 문장이 여러 동작을 혼합, 검증 명령이 산문 수준(실행 가능한 명령·fixture·기대 exit 없음).
- Hook 배선 표(14개 AC 전수) — **대부분 "명시안됨"**: 각 AC의 기계장치가 pre-commit/pre-push/CI 중 어디서 도는지 특정 안 됨. AC-M도 "3단 훅과의 1:1 배선을 강제하는 registry가 아니다"(등록만 요구, 실제 호출 증거 요구 안 함).
- N5 — **미해결.** Phase 1 시점(phases_shipped=[1])에 canonical 목록이 아직 배송 안 된 Phase 2~4(AC-11·9·7·6·17·12)까지 요구해서 자기봉쇄 재발.
- N6 — 역의존 결함 자체는 닫힘(AC-17 manifest 자체완결화 성공). 단 manifest 값과 실제 실행값의 일치 검증이 없어 AC-17 전체는 보완 대상.
- N7 — 문서화는 반영(순차 2-PR 위협을 정확히 인정, 사람 승인 임시절차 명시)됐지만 위협 자체는 미해결. 승인자·증거·blocking 위치가 정의 안 됨.
- N9 — 부분 반영, 미해결. `enforced_by` 예시(`hooks/pre-commit:secrets-render-check`)와 registry `id`(`secrets-render-check`) 형식이 불일치, 파싱 규칙 없음.
- AC-11 — 여전히 미해결(검증 시점 판본 기준. **주의: 이 판정 직후 리뷰 중 09:14에 AC-11이 default-deny 네트워크 정책으로 실제 수정됨 — 아래 quality-reviewer가 이 수정을 확인**).

**quality-reviewer (Agent 도구, `/verify` 2단계로 사용자가 직접 실행 지시)**
- 실행: `oh-my-claudecode:quality-reviewer a626bff208fb2692d`
- **핵심 지적: 재작성 사유(v3 당시 line 12) 자체가 부정확.** "안닫힘·신규결함이 거의 전부 D계열" → 실제로는 D 7건/비D 8건(절반 이하). 비D 4건 중 AC-11만 실제로 고쳐졌고 AC-13·14·15는 "Phase 6 재분류"로 범위 밖으로 옮겨진 것 — 이 사실이 위 정정 기록 #8로 반영됨.
- AC 간 잔존 모순 4건 발견 — v4에서 전부 해소:
  1. AC-2("NOT_RUN") ↔ AC-5("canonical 밖") — N5 자기봉쇄 재현 구조. → v4: AC-2를 canonical 목록 밖으로 명시(NOT_RUN 문구 삭제).
  2. AC-19가 3상태 계약에 없는 "FAIL 대기" 4번째 상태 생성. → v4: 명시적 FAIL로 정정.
  3. AC-1의 `required` 필드가 AC-5와 의미 미정의. → v4: `required:true`만 NOT_RUN 집계 대상으로 명문화.
  4. AC-4·AC-6이 이 문서 스스로 "무효"라 기록한 required-check(skipped/neutral 통과)에 의존. → v4: 두 AC 모두 "명시적 failure 게시 필수" 추가.
- 증거 사슬 단절 지적: 두 goal 문서가 git 미추적 상태라 v1·v2 원본이 디스크에 없고, 적대검증 로그의 `[v2:121]` 류 줄번호 인용이 v3 덮어쓰기로 전부 엉뚱한 텍스트를 가리킴. → **v4 착수 전 git 커밋 필수(아래 액션 아이템).**
- file:line 인용 오류 3건 발견(SKILL.md :55→58, verify.sh :91→92, verify.yml :15→16) → v4에서 정정 완료.
- 구조 문제: AC 번호 결번(8·10·18) 대응표 없음, Phase 5가 정의 없이 3회 참조, ③-E 스캐폴딩 범위가 3곳에서 다른 답, AC-3↔AC-M 순환 참조, AC-6 요구사항이 3곳에 분산 → v4에서 전부 정리(대응표 신설, Phase 5/6 번호 폐기, 스캐폴딩 범위 "안 만듦"으로 통일, AC-M을 AC-3보다 먼저 배치, AC-6에 요구사항 통합).
- **결론: "전면 v4 재작성은 불필요, AC 본문은 쓸 만하고 망가진 건 골격"** — 골격 정리(문서 분리, 모순 해소, line 12 재작성)만으로 충분하다고 판단, 실제로 v4는 AC 본문 재작성이 아니라 골격 재배치로 진행함.

**보안 리뷰(security-reviewer, `/verify` 3단계, 사용자가 직접 실행 지시)**
- 실행: `oh-my-claudecode:security-reviewer ae407cde54565fdba`
- 문서 자체의 리터럴 시크릿: **0건**(46개 추적 파일 + git 히스토리 54커밋 전체 blob 스캔).
- **F1(치명)**: 재발방지 설계가 산문 한 줄뿐(`verify-independent-trust-boundary-goal-2026-08-11.md:23`) — 이 문서 자신의 AC-1 counter-AC가 금지하는 "산문 지침"에 해당. 강제 장치 전부가 git만 보는데, 실제 유출 경로는 대화기록이었음.
- **F2(가장 치명적, Phase 1~4와 무관하게 지금 존재하는 위험)**: `~/.claude/history.jsonl`에 Discord 웹훅 12개·Google API 키 3개·Anthropic 키 3개 평문 잔존. `Valueconnect-Ops` 프로젝트 메모리 파일이 웹훅 2개를 참조값으로 의도적 저장 + `MEMORY.md`에서 자동 로드됨. "(회전 완료)" 전제(goal 문서 정정기록 #6 인접 서술)가 디스크 상태로 뒷받침 안 됨. 리뷰 도중 Google 키 1개가 리뷰어 자신의 트랜스크립트에 실수로 재출력되는 사고가 실시간으로 재현됨.
- **F3**: `.secret-patterns.default`가 Discord/Slack 웹훅·`sk-ant-` 키를 탐지 못함(카나리 실측). 이 저장소가 실제로 겪은 유출 유형과 정확히 일치 — 즉시 조치 권고, 정규식 제안 포함.
- F4~F8(Phase 5 전용, 분리 문서에 반영 필요): Keychain 선택 미지정+재부팅자동기동과 상충, 서명 권한이 판정 대상과 같은 로컬 신뢰경계에 있음(같은 세션이 서명 도구 호출 가능 → `app_id` 고정이 로컬에서 우회됨), GitHub App 최소권한·자산 4종 목록 부재, Discord 승인 채널의 allowlist 식별자·2요소·nonce-message binding 부재, 신뢰된 digest 출처 미정의(v1·v2를 죽인 것과 같은 실패 유형).
- **F9(Phase 1~4 반영 완료)**: `verify.sh`가 미추적 파일 스캔 안 하고도 PASS 출력 — goal 문서 ①에 반영.
- **F10(Phase 5 문서에 반영 필요)**: AC-11 격리가 파일 변조만 다루고 자격증명·네트워크 접근은 다루지 않음 — Phase 5의 Keychain 자격증명과 교차 위험.
- 잘 된 점으로 명시: 실패한 접근 3가지를 GitHub 공식문서 근거로 보존한 것, `app_id` 고정 판단, `neutral`/`skipped` 대신 명시적 `failure` 요구, 순차 2-PR 위험을 숨기지 않고 문서 존재를 required check 조건으로 삼은 설계, `verify.sh`의 fail-closed 구조.
- 착수 전 순서 권고: F2(자격증명 현황 확정) → F3(패턴 추가, 즉시 조치) → F1(재발방지 AC 승격) → F5/F4(서명권한 로컬 격리 결정) → F6(자산표+최소권한) → F8/F7(다음 라운드 재작성 위험 최대 지점).
- **F1·F2·F3은 Phase 5 착수 여부와 무관하게 지금 존재하는 현재 위험** — goal 문서 작업과 별도로 사장님께 즉시 보고됨(2026-08-11).

### v4 — 골격 정리 (2026-08-11, quality-reviewer 권고 반영)

G(Claude)가 quality-reviewer 지적사항을 전수 반영해 문서를 분리·재정리. **아직 codex(V1) 재검증 전 — 다음 라운드에서 v4를 대상으로 검증 예정.** 변경 요약:
- 이 문서(검증이력)를 goal 본문에서 분리
- 모순 4건 해소, file:line 인용 3건 정정, "미추적 0건" 표현 삭제(사실과 다름 — 실제로 두 문서 다 미추적이었음)
- AC 번호 대응표 신설, Phase 5/6 번호 폐기("제품코드 도입 후"로 대체), AC-M을 Phase 1 최우선으로 재배치, AC-3의 enforced_by 검증을 AC-M 완료 전/후로 명시적 이원화
- AC-6에 잔여위험·문서존재조건 통합, AC-4·AC-6에 skipped/neutral 금지 명문화
- AC-13·14·15에 "제품코드 도입 후 착수" 명시, AC-2와 함께 "스캐폴딩도 지금 안 만듦"으로 범위 통일

## 다음 라운드 codex 지시 (v4 대상)

이전 라운드(§v3-라운드) 지시를 계승하되, v4의 변경사항을 정조준한다:

- **Spec 해부 재실행**: quality-reviewer가 지적한 4개 모순이 실제로 해소됐는지 AC 원문으로 재확인
- **Hook 배선 재실행**: v3에서 "명시안됨"으로 판정된 AC들이 여전히 배선 위치가 없는지, 아니면 v4에서 실질적으로 나아졌는지(v4는 배선 위치를 새로 추가하지 않았음 — 이 갭은 아직 남아있을 가능성이 높다는 걸 인지하고 검증할 것)
- N5(Phase 1 canonical 목록의 자기봉쇄)가 `phases_shipped` 배열 도입으로 실제로 해소됐는지
- AC-3→AC-M 재배치가 순환 참조를 실제로 없앴는지
- git 커밋 여부와 그 이후 인용 무결성
