# V1 적대 검증 판정서 — 하네스 감사 goal 문서 (PR #144, 2026-10-31)

대상: `docs/engineering/harness-audit-goal-2026-10-31.md` + `anthropic-engineering-to-v6-methodology-2026-10-31.md`
검증자: V1 (읽기 전용, 저장소 무변경). 측정 시각 2026-10-31 23:30~2026-11-01 00:20 KST. 작업 경로 `/Volumes/SSD/Valuehire_v6/worktrees/harness-audit-2026-10-31`, HEAD d5a6d30.
원자료: `scratchpad/runs200.json`(verify.yml 최근 200회), `fail_steps.tsv`(실패 95회의 실패 스텝), `succ_steps.tsv`(성공 96회의 skipped 스텝·소요시간), `open_prs.json`.

---

## (A) 수치 재측정 표

| # | 항목 | 주장값 | 재측정값 | 판정 | 재측정 명령 |
|---|---|---|---|---|---|
| A1 | 열린 PR | 63 | 64 (#144 자신 포함; 제외 시 63) | MATCH | `gh pr list --state open --limit 300 --json number` → len |
| A2 | 제품 코드(humansearch/src·apps·tools·supabase) 건드린 PR | 19 (30%) | 19 (63 중) | MATCH | open_prs.json 경로 접두사 분류(python) |
| A3 | 문서·검증·테스트만, SOT 없음 | 14 (22%) | 12 엄격 + 2 경계(#123 `.claude/skills/**`만, #54 `.gitignore`+docs+tests) = 14 | MATCH(경계 2건 포함 시) | 동일 분류. 단 **docs/sot 를 건드린 비제품 PR이 30건** 더 있음(아래 B7) |
| A4 | 병합 PR 누적 / 8-27 이후 | 33 / 12 | 33 / 12 (`mergedAt >= 2026-08-27`) | MATCH | `gh pr list --state merged --limit 300 --json number,mergedAt` |
| A5 | goal 문서 / verdict 문서 | 40 / 16 | 40(`-goal-` 포함) / 16(`verdict` 포함) | MATCH | `ls docs/engineering \| grep -c -- '-goal-'` 등 |
| A6 | 제품 LOC | 2,685 | humansearch/src `*.py` 2,525 + apps 462 = **2,987**; tools(4,687)·supabase(953) 포함 시 **8,627** | MISMATCH | `find … -print0 \| xargs -0 cat \| wc -l` |
| A7 | 검증 인프라 LOC | 15,764 | scripts 8,239 + hooks 443 + .github 283 + contracts 401 + humansearch/tests 3,190 + .claude 406 + verify.sh 96 + suppressions 48 = **13,106** | MISMATCH(정의 불명) | 동일 |
| A8 | 문서 LOC | 29,165 | docs `*.md` 전체 30,957 − 이 PR 신규 1,792 = **29,165**(origin/main 시점 `*.md`) / 현 HEAD 전체 파일 32,347 | MATCH(조건부: origin/main 시점·md만) | `find docs -name '*.md' … wc -l`, `git diff --stat origin/main...HEAD` |
| A9 | session-status.sh 소요 | **399초** | **189.26초**(real), user 62 sys 35 | MISMATCH(2.1배 차) | `/usr/bin/time -p bash scripts/session-status.sh` |
| A10 | RED | 0/29 | **1/29** (`acceptance-0-2.sh` — 이 워크트리에 gitignored `.secret-patterns` 부재; 메인 체크아웃에는 존재) | MISMATCH(환경 의존) | 동일 + 개별 재실행 |
| A11 | 워크트리 / task 브랜치 | 3 / 2 | 워크트리 4(main 포함 → 작업용 3) / 로컬 task 브랜치 **3**(harness-audit 포함) / **원격 task 브랜치 160** | MISMATCH(경미, 정의 불명) | `git worktree list`, `git branch --list 'task/*'`, `git branch -r` |
| A12 | 8/27 기준선 69 / 91 | 69 / 91 | 진단 문서 49~50행에 69 / 91 기재 확인 | MATCH(인용) | `grep -n 69 docs/engineering/throughput-architecture-diagnosis-goal-2026-08-27.md` |
| A13 | main 룰셋 | pull_request + required_status_checks(verify) | pull_request(approving 0) + required_status_checks(context `verify`, strict=true) | MATCH | `gh api repos/sangmokang/Valuehire_v6/rules/branches/main` |
| A14 | verify.yml 최근 200회 실패 | 95 | 95 (성공 96, **취소 9**) | MATCH | `gh run list --workflow verify.yml --limit 200 --json conclusion` |
| A15 | 실패 스텝: 억제 만료 | 85 | 85 | MATCH | 95회 각 `gh api …/runs/<id>/jobs` |
| A16 | 히스토리 전량 스캔 / 문법 / 비밀 / hs-1305 / P3 | 4 / 2 / 2 / 1 / 1 | 4 / 2 / 2 / 1 / 1 | MATCH | 동일 |
| A17 | "성공 run 105회에서는 전부 실행·전부 통과" | 105 | 성공은 **96**. 나머지 9는 취소(cancelled)라 "전부 통과" 아님. 성공 96회 중 **94회에서 `인수 검사 0-5` 스텝이 skipped**(`if: github.ref == 'refs/heads/main'`) | MISMATCH | succ_steps.tsv |
| A18 | 억제 만료 = 13번째 스텝 | 13 | 현 main yml에서 13번째(`- name:` 기준). 단 성공 run의 실제 스텝 수는 31/32/35로 브랜치마다 다름 | MATCH(main 한정) | `grep -n '^\s*- name:' .github/workflows/verify.yml \| nl` |
| A19 | CI 소요 "4~6분" | 4~6분 | 성공 96회: min 242초, 중앙값 313초, max 363초 | MATCH | succ_steps.tsv started_at/completed_at |
| A20 | 속성 테스트 4파일 | 4 | hypothesis 사용 테스트 4파일 | MATCH | `grep -rl hypothesis humansearch/tests` |
| A21 | 인수 스크립트 29개 | 29 | `scripts/acceptance-*.sh` 29개 | MATCH | `ls scripts/acceptance-*.sh \| wc -l` |
| A22 | strict 스킬 참조 경로 11개 중 v6 존재 1개(`.claude/skills/verify/local-checks.sh`) | 11 / 1 | 추출된 경로형 참조 **14개**(파일 9: docs/sot/30, docs/sot/31, .claude/hooks/stop-evidence-gate.py, .claude/strict-active.json, .claude/skills/strict, .claude/commands/st.md, .codex/skills/st, tools/install-strict-skill.sh, guards/runner-lease.py + npm run 5: wt, wt:done, red-ledger, strict:gate, check). v6 존재 **0개**. `local-checks.sh`는 strict SKILL.md에 **언급 자체가 없음** | MISMATCH(방향은 더 나쁨) | `grep -oE '…' ~/.claude/skills/strict/SKILL.md`, `ls` 각 경로 |
| A23 | harness 스킬 `make red-ledger/task/ship` v6 부재 | 부재 | Makefile 없음, `verification-commands.md:10`이 대체표 명시 | MATCH | `ls Makefile`, `grep -n make docs/sot/verification-commands.md` |
| A24 | principles.yaml 머리말 면제 단서 | 존재 | 3행 "mechanism_expected에 적힌 제품 장치의 실제 구현 여부는 이 장부의 PASS 범위가 아니다" 확인 | MATCH | `head -4 docs/sot/principles.yaml` |
| A25 | (방법론 문서) "인수 스크립트 29개·억제 **2건**" | 2 | suppressions.yaml 항목 **3건** | MISMATCH | `grep -c '^- check:' suppressions.yaml` |
| A26 | (방법론 문서 A-3) "humansearch 592줄·apps/admin 458줄" | 592 / 458 | 2,525 / 462 (8-27 진단 수치 2,156과도 불일치) | MISMATCH | A6 명령 |
| A27 | (방법론 문서) "원칙 24개" vs principles.yaml 머리말 "32개 원칙" | 24 | yaml 항목 24개(P1~P24), 머리말 문구만 32 | MATCH(yaml 머리말 자체가 오기) | `grep -c '^- id: "P' docs/sot/principles.yaml` |

---

## (B) 해석 공격

### B1. "메타 게이트 적중 0" — 가림 효과 반론에 대한 저자의 방어("2~12번은 200회 전부 실행")
**판정: WEAKENED.**
- 스텝 12(`인수 검사 0-5`)는 `if: github.ref == 'refs/heads/main'`이라 **main push 외 전부 skipped**(성공 96회 중 94회). "2~12번 200회 전부 실행"은 거짓이다.
- 실패 run은 첫 실패 스텝에서 멈춘다. 스텝 1(비밀 스캔) 실패 2회, 스텝 5(P3) 1회, 스텝 8(히스토리) 4회에서 그 뒤의 2~12번도 실행되지 않았다. 취소 9회도 어디까지 돌았는지 미확인.
- 성공 run의 실제 스텝 수가 31/32/35로 브랜치마다 다르다(일부 브랜치는 "CI 실행 증명 우회·동일 실행 검수 회귀", "P13 검사 삭제·자기제외·외부효과 경계 회귀" 스텝을 더 가짐). "메타 게이트 17개"라는 분모는 main yml 하나의 스냅샷이며 문서에 산출 근거가 없다.
- 다만 핵심 방향(메타 게이트가 200회 중 실패를 낸 적이 없다)은 성공 96회 + 억제 전 단계 통과 85회 모두에서 2~11번이 초록이었으므로 유지된다. 결론은 살아 있고 근거 문장이 틀렸다.

### B2. "85회(89%) = 2026-10-13 억제 3건 만료 사건, 11일간 모든 브랜치 CI 실패"(R-6)
**판정: REFUTED(인과 서술) / WEAKENED(수치).**
- 85회 중 **44회는 2026-10-20 이전**(9/30 2, 10/1 10, 10/6 1, 10/12 1, 10/13 24, 10/14 4, 10/15 2)이다. 이는 #111(10-02, 기한 10-13 연장)·#130(10-13, 기한 10-20 연장)이 main에 들어간 뒤에도 **rebase하지 않은 브랜치**가 옛 기한으로 실패한 것이다. 즉 단일 사건이 아니라 "기한 연장 → 미반영 브랜치 연쇄 실패"가 3회 반복된 구조 문제다. "2026-10-13 억제 3건 만료"라는 표현은 사건 날짜도 틀렸다(만료 10-20, 실패 시작 10-21).
- "저장소의 어떤 PR도 verify를 통과할 수 없다"(문서 108행)는 **반증됨**: `task/mail-governance-20261021`(PR #139)은 10-22 커밋 8d8b8bc에서 suppressions.yaml을 비우고(3건을 실제 방어로 해소했다고 기재) verify 전 스텝 **success**. 억제 기한 결정이 아니라 억제 해소로 통과가 가능하며, 그 PR이 **10-20부터 열려 있다**. "PR #130이 확보한 7일 판단 시간 안에 결정이 없었다"도 이 PR의 존재로 약화된다(결정 미병합일 뿐 부재가 아님).
- 중복 계산: 85회는 **고유 SHA 59개**(push 59 + pull_request 26, 40개 브랜치). 같은 SHA의 push/PR 이벤트가 쌍으로 잡힌다. "실제 결함 적중 10회"도 **고유 SHA 6개**(비밀 d3f45ae, 히스토리 1722d7f·f6ac2e1, 문법 09cc35b, hs-1305 b9e5d3b, P3 2a20823). 문서가 run 단위와 사건 단위를 구분하지 않아 비율(89%)이 과장되진 않지만 분모·분자 모두 2배 가까이 부풀어 있다.

### B3. LOC 비율(제품 2,685 / 검증 15,764 / 문서 29,165 ≈ 1 : 5.9 : 10.9)
**판정: WEAKENED.**
- 세 수치 중 재현된 것은 문서 LOC 하나뿐이고, 그것도 "origin/main 시점·`*.md`만"이라는 암묵 조건에서만 맞는다. 제품 LOC는 어떤 조합으로도 2,685가 나오지 않는다(2,987 또는 8,627).
- **같은 문서 안에서 "제품 코드" 정의가 두 개다.** PR 분류(A2)에서는 humansearch/src·apps·tools·supabase를 제품으로 쳤는데, LOC에서는 tools(4,687줄)·supabase(953줄)를 빼야 2천대가 나온다. tools/invoice는 Supabase 마이그레이션·런타임 코드까지 가진 제품이다. 둘 중 하나로 통일하면 비율은 1 : 1.5 : 3.5(tools 포함) 또는 1 : 4.4 : 9.8(제외)로 크게 달라진다.
- 검증 인프라 LOC에 humansearch/tests(3,190줄)가 들어간다면 그중 hypothesis 속성 테스트·observe 단위 테스트는 제품 품질 테스트이지 "하네스"가 아니다. 반대로 15,764가 tools를 포함한 값이라면(13,106+… 어떤 조합도 정확히 나오지 않음) 제품을 인프라로 센 것이다. 문서에 산출 명령이 `find+wc`로만 적혀 있어 재현 불가.

### B4. 세션 시작 399초 → "29개 전수 실행 구조 자체가 원인"(반대 가설 C 기각)
**판정: WEAKENED.**
- 같은 스크립트가 같은 머신에서 189초. 2.1배 차이는 "구조" 밖의 변수(동시 실행 중인 다른 세션·디스크 캐시·`acceptance-0-7` 제외 여부)가 절반 이상을 설명한다는 뜻이다. user+sys 97초로 wall 189초의 절반이므로 I/O·대기가 크다. "오너 PC 성능 문제"를 기각하려면 1회 측정이 아니라 조건을 적은 반복 측정이 필요하다.
- D1의 목표 "<30초"와 AC-D1은 유효하지만, 기준선 399는 상한값 1회 관측이다. 문서는 측정 조건(동시 세션 수·캐시 상태)을 적지 않았다.

### B5. "진입점 드리프트: 11개 중 1개 존재(`local-checks.sh`)"
**판정: WEAKENED(방향은 HOLDS, 수치·예시 오류).**
- strict SKILL.md에는 `local-checks.sh`가 등장하지 않는다. 저자가 "존재하는 1개"로 든 예시는 strict 스킬의 참조가 아니라 저장소에 있는 파일을 역으로 끼워 넣은 것이다. 참조 14개(파일 9 + npm 스크립트 5) 중 v6 존재는 0. 문서 주장보다 상태가 더 나쁘다.
- `check-strict-principles-skills.sh`가 "원칙 블록 동치만 보고 경로 실존은 안 본다"는 서술은 소스(마커 블록 추출·비교)로 확인됨 — HOLDS.

### B6. "원칙 ↔ 기계 장치 실존 대조"에서 ✗로 표기한 9행
**판정: HOLDS(9행 전부), 단 ○행 1건 근거 보강 필요.**
- P11(파일 크기 예산): scripts/hooks/.github/humansearch/tests에서 LOC 상한 검사 없음. ✗ 유지.
- P12(capabilities.yaml·미참조 export·고아): 파일 없음, 스캔 없음. ✗ 유지. 단 P12 문면에는 "SessionStart hook → session-status.sh"가 기계 장치로 적혀 있고 **그것은 존재**한다. 표가 P12를 통째로 ✗로 묶은 것은 과장 — P12는 "일부 ○".
- P16 `.contract.test` 접미사: 어떤 파일·스크립트에도 없음. ✗ 유지(단 "런타임 import 증명"은 `scripts/hs_import_spy.py`로 존재 — 표가 이미 ○로 분리 기재).
- P19 라이브 스모크·V-3 `make ship`: Makefile 없음, smoke 스크립트 없음. ✗ 유지.
- SOT diff 동봉: `check-docs-sot.sh`는 자기 자신만 참조, CI·hooks 어디에도 호출 없음. ✗ 유지.
- P5 RED 후 테스트 불변 / P15④ 기대값 단독 커밋: hooks/scripts에 테스트 파일 diff 검사 없음. ✗ 유지.
- P8 lease / P9 멱등키·readback / P10 외부 감시자: humansearch/src·tools에 lease·readback 구현 없음(grep으로 `lease` 0건; `멱등|idempot`은 tools/invoice의 DB 제약에만 등장 — invoice 한정이지 제안 발송 P9①이 아님). ✗ 유지.
- 삭제 대칭: 없음. ✗ 유지.
- mechanism-registry.yaml 20항목은 전부 CI 배선·비밀·P3·invoice 계열이라 위 9행과 겹치지 않음을 확인.
- 머리말 면제 단서와 P1 충돌 지적: HOLDS.

### B7. D4 "병합 티어링 보류 — 수혜 14건(22%)으로 효과 제한"
**판정: WEAKENED.**
- 14건은 "SOT도 안 건드린 순수 문서·검증·테스트"만 센 값이다. 제품 코드를 안 건드리고 docs/sot를 건드린 PR이 **30건** 더 있다. 방법론 문서 C-1이 제안한 티어 정의는 `docs-only / evidence-fixture / product-or-contract`이고, SOT 문서를 자동 병합 티어에 넣을지는 설계 선택이다. SOT를 포함하면 수혜 44건(70%)이 된다. 즉 "효과 제한"은 티어 정의를 가장 좁게 잡았을 때만 성립하며, 문서는 그 선택을 명시하지 않았다.

### B8. "실제 결함 적중은 전부 비밀·PII·문법 계열"
**판정: HOLDS.** 고유 사건 6건: 비밀 1, 히스토리 blob 2, 문법 1, PII 1, P3 lint 1. P3 lint는 "조용한 실패" 계열이지 비밀·PII·문법은 아니므로 표현은 부정확하나 "메타 게이트 아님"이라는 요지는 유지.

### B9. 재발 원장 R-6의 "이 PR의 7d4739d·fe8a296 포함, P23 UNVERIFIED"
**판정: HOLDS.** 이 브랜치 3커밋(7d4739d, fe8a296, d5a6d30) × push/PR 6 run 전부 failure, 실패 스텝 억제 만료. 확인.

---

## (C) PR 자체 검사

| 항목 | 결과 |
|---|---|
| 문서 전용 여부 | `git diff --stat origin/main...HEAD` → 9 files, +1,792, 전부 `docs/engineering/**`. **HOLDS** |
| counter-AC(제품·SOT·CI 경로 변경 0줄) | `git diff --stat origin/main...HEAD -- humansearch/src apps tools supabase docs/sot contracts scripts hooks .github \| wc -l` → **0**. PASS |
| AC `grep -c '^\| D[1-7] \|'` → 7 | **7**. PASS. 단 D7 행이 D1~D6 표와 **빈 줄로 분리된 별도 표**(85행)라 마크다운 렌더에서 1행짜리 두 번째 표로 보인다. 이슈 #143의 "결정 카드 표에 D1~D7 7행"을 문자 그대로 읽으면 한 표가 아니다 — grep은 통과하나 표 구조는 결함 |
| 이슈 #143 ↔ PR 본문 정합 | PR 본문은 "결정 카드 D1~D7", 문서 본문 상위 목표(5·7행)는 "D1~D6"로 남아 있음. 문서 내부 불일치 |
| CI 상태 | 6 run 전부 failure(억제 만료). PR 본문 "pre-push: verify.sh + acceptance 전량 통과"는 로컬 훅 결과이며 CI 초록 아님. 룰셋상 **병합 불가** |
| PII·비밀 | 이메일 2건은 anthropic.com 공개 주소(performance-recruiting@, feedback@). 전화번호 패턴 10건은 전부 뉴스 URL의 기사 ID 오탐(예: `v.daum.net/v/20260113115410967`). 토큰 패턴 0건. 인명은 공개 임원·연구원(ABB코리아 대표, 산업연구원 연구위원) — 후보자 PII 없음. **PASS** |
| 방법론 문서 "출처" 절 | `scratchpad/eng_articles_A.md, _B.md, _C.md`를 인용하나 저장소에는 `evidence/harness-audit-20261031/anthropic-articles-01-08.md` 등으로 이름이 바뀌어 들어옴. 출처 경로 불일치(R-1 취지와 상충) |

---

## (D) 검증 불가 목록

1. **"메타 게이트 17개"** — 어떤 스텝/스크립트가 메타 게이트인지 목록이 없다. 29 인수 스크립트 또는 27 CI 스텝 중 무엇에서 5를 뺀 값인지 산출 불가.
2. **검증 인프라 LOC 15,764·제품 LOC 2,685의 디렉터리 집합** — 어떤 조합으로도 재현되지 않음(A6·A7).
3. **399초의 측정 조건** — 동시 세션·캐시·`acceptance-0-7` 제외 여부 미기재. 재측정 189초와의 차이 원인 판정 불가.
4. **"8/27 진단 12 → 5배"의 기준 시점 비교 타당성** — 8-27의 12건 중 몇 건이 현재 63건에 남아 있는지(적체 vs 신규) 문서에 없음. 측정은 가능하나 문서가 주장하지 않아 보류.
5. **취소된 run 9회의 진행 범위** — 어느 스텝까지 실행됐는지 jobs API로 확인 가능하나 문서가 이를 "성공 105회"에 뭉뚱그려 분석 대상에서 빠짐.
6. **re발 원장 R-2·R-3·R-4·R-5** — 세션 내 관측 사건이라 외부 재현 불가. R-4의 재검증 결과 파일(`abb_recheck.md`)은 존재 확인만 함, 내용 검증은 범위 밖.
7. **방법론 문서 PART A(포멀 검증 글 사실검증 14항목)** — 외부 URL 실페치가 필요하며 이번 검증 범위(수치표·게이트·장치·진입점)에서 제외. 미검증.
8. **"PR #129·#130 예고"** — #130은 10-13 병합 확인. #129는 OPEN(병합 안 됨)이라 "예고"가 어떤 문장을 가리키는지 본문 대조 못 함.

---

## (E) 총평

문서의 골격 수치(열린 PR 63·병합 33/12·goal 40/verdict 16·실패 95/억제 85·룰셋·장치 부재 9행·Makefile/npm 부재)는 재현되며, 원칙↔장치 대조표와 진입점 드리프트의 **방향**은 전부 맞다. 그러나 "실측"이라 이름 붙인 표 가운데 LOC 3종은 하나만 조건부 재현되고 제품/인프라 정의가 문서 안에서 두 번 바뀌며, 세션 시작 399초는 같은 머신에서 189초로 재측정돼 1회 관측치를 구조 원인으로 단정한 반대가설 C 기각이 흔들린다. 게이트 적중 절에서는 "2~12번 200회 전부 실행"(0-5는 main 외 전부 skip), "성공 105회"(96+취소 9), "85회 = 10-13 만료 단일 사건"(44회는 10-20 이전, 기한 연장 미반영 브랜치의 연쇄), "어떤 PR도 통과 불가"(PR #139는 10-22 억제 해소로 초록)가 각각 틀렸고, run 단위와 SHA 단위를 섞어 85→59, 10→6으로 사건 수가 과장됐다. strict 스킬 "11개 중 1개 존재"는 실제로 14개 중 0개이고 존재한다던 파일은 스킬이 참조하지도 않는다. 결정 카드 D1·D5·D6은 이 오류들과 무관하게 성립하지만, D3(메타 게이트 17개 회수 검토)은 분모가 산출 불가하고, D4(티어링 보류)는 가장 좁은 티어 정의에서만 "효과 제한"이며, R-6의 원인 서술은 다시 써야 한다. PR은 문서 전용·AC 통과·PII 없음으로 형식 요건은 충족하나 CI 빨간불이라 룰셋상 병합 불가이고, 문서 자체가 "실측"으로 내세운 숫자 중 5개가 재현되지 않으므로 **현 상태로는 PASS 불가 — 수치 산출 명령·조건 명기와 B1·B2·B5 정정 후 재판정** 을 권고합니다.
