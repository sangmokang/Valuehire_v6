---
name: llmcodereview
description: 큰 GitHub PR 을 이미 결제 중인 웹 구독 모델(Cursor Grok·ChatGPT·Gemini)로 추가 비용 없이 분할 리뷰한다. Aside 브라우저를 오케스트레이터로 써서 Planner → Coverage 독립 대조 → WU(리뷰 단위)별 새 세션 리뷰 → 고위험 WU 감사 → Cross-WU 통합 리뷰 → Final Review Map 을 만들고, 장부로 중단·재개하며, 첨부를 끝까지 읽었는지 기계로 검사한다. 엔진 간 같은 지시문 비교도 한다. 트리거 — "llmcodereview", "LLM 코드리뷰", "Grok 리뷰", "Cursor로 PR 리뷰", "ChatGPT로도 리뷰", "Gemini로도 리뷰", "PR 분할 리뷰", "WU 리뷰", "Review Map", "엔진 비교 리뷰".
---

# llmcodereview — 웹 구독 LLM 으로 큰 PR 분할 리뷰

완료 = 변경 파일 전부가 어느 WU 에서 검토됐는지 추적되고, 고위험 연결 코드와 WU 사이 경계까지 검증된 상태. "모델이 다 봤다"는 말은 증거가 아니다. 대조는 스크립트가 한다.

## 0. 절대 규칙
- 추가 비용 0: xAI/OpenAI/Anthropic 등 종량 API·XAI_API_KEY 호출 금지. Cursor On-Demand·크레딧 구매·업그레이드 금지. 한도·결제 화면이 뜨면 `BLOCKED_INCLUDED_USAGE` 로 멈춘다.
- 리뷰 전용: merge·push·PR 승인·코멘트·코드 수정 금지. 모델 지시문에도 읽기 전용·외부 SDK import 금지·같은 실험 2회 초과 반복 금지를 넣는다(이미 템플릿에 있음).
- 로그인·CAPTCHA·권한 승인(OAuth)·사용자 비밀값 입력이 필요하면 멈추고 보고. 봇 탐지 우회 금지.
- 브라우저는 Aside 만. 사장님 활성 탭을 빼앗지 않는다. 엔진마다 전용 탭 1개를 정해 그 탭만 주소를 바꿔 쓴다.
- 결과·원문은 gitignore 된 `private-reviews/cursor-pr-review/` 에만. 저장소에는 절차·스크립트만.

## 0.5 기본 경로 — 셸 교차검증 (Claude ↔ Codex 구독, 브라우저 불필요)
모든 PR 의 기본은 이 경로다. 아래 1~3절의 브라우저 분할 리뷰(Grok·ChatGPT·Gemini)는 **선택** — 수천 줄 PR 이거나 Codex 가 BLOCKED 일 때만. 같은 headRefOid 로 이미 끝난 리뷰는 다시 돌리지 않는다(새 커밋이 생긴 SHA 만).
1. **상태 복원**: `gh pr view <N> --json headRefOid,files,state,mergeable`, PR 워크트리 HEAD 일치·`git status` 깨끗, `gh pr checks <N>` 를 push/pull_request 이벤트로 나눠 본다. 기존 판정·장부(`private-reviews/cursor-pr-review/pr<N>/`)와 사장님 결정(ADR·goal)을 먼저 읽는다.
2. **Claude 요구사항 대조**: 정본 goal 의 AC·counter-AC 와 변경 파일 전체를 대조한다. 결정된 사항(예: 2026-09-23 개인정보·Jev 전송 허용)과 충돌하는 지적은 결함으로 세지 않는다.
3. **Codex 적대검증**(`codex login status` 로 구독 인증 확인 후, PR 워크트리에서 백그라운드):
   `node ~/.claude/plugins/cache/openai-codex/codex/<ver>/scripts/codex-companion.mjs adversarial-review --base origin/main "<중립 문구: 무엇을 의심할지·결정된 허용 범위·재현 명령 요구>" > private-reviews/cursor-pr-review/pr<N>/codex-adversarial-<날짜>-<sha>.raw.txt 2>&1`
   - `--base origin/main` 필수(로컬 main 은 뒤처질 수 있다). `--help` 는 사용법이 아니라 **리뷰 주제로 실행된다** — 쓰지 말 것.
   - "깨뜨려라·우회" 같은 공격 문구는 정책 차단을 부른다. 실패·인증 불가면 `BLOCKED` 로 기록, 성공으로 적지 않는다.
   - companion 샌드박스는 읽기 전용이라 pytest·mktemp 가 안 돈다 → 시험 실행은 4단계에서 Claude 가 한다.
4. **Claude 독립 재현**: 지적마다 코드 경로·정본·반대 증거를 확인하고, 재현되면 **실패 시험(RED) 먼저 커밋** → 최소 수정(GREEN) → 수정 줄 고장 사본(뮤테이션)으로 시험 민감도 확인 → 저장소 게이트 원명령 재실행. 의견 일치는 증거가 아니다.
   - 시험의 합성 비밀값은 `SECRET = "..."` 처럼 키워드-값 형태로 쓰면 pre-commit 비밀 스캔에 걸린다. 의미대로 `MARKER` 같은 이름과 접두어 없는 고유 문자열을 쓴다(스캐너 회피용 문자열 쪼개기 금지).
5. **파일별 전수 장부**: `pr<N>/FILE-REVIEW-LEDGER-<날짜>.md` — 파일·줄·변경 목적·요구사항·호출 경로·검토 상태(REVIEWED 는 파일 전체를 실제로 읽은 경우만 / PARTIAL 은 읽은 범위 명시 / GENERATED 는 정합성 명령)·결함·시험 결과·미검증. 검토 범위와 시험 범위를 섞지 않는다.
6. **판정**: 코드/아키텍처/진행 판단 + 병합 가능 여부. merge·push 는 사장님 승인 전 하지 않는다.
실례: PR #109 (2026-10-10) — Codex 지적 3건 전부 Claude 재현·수정, 장부 `pr109/FILE-REVIEW-LEDGER-2026-10-10.md`.

## 1. 준비 (매 실행)
```bash
SK=.claude/skills/llmcodereview/scripts
export LCR_PR=<번호> LCR_SHA=<headRefOid> LCR_BASE=<baseRefOid> ASIDE_WIN=<창id> CURSOR_TAB=<탭id> GPT_TAB=<탭id> GEM_TAB=<탭id>
# 선택: LCR_EXTRA_FILES='{"WU07":["scripts/a.sh"],"INTEG":["scripts/a.sh"]}'  (PR 밖이지만 묶음에 넣을 파일)
```
1. `gh pr view $LCR_PR --json headRefOid,baseRefOid,changedFiles,additions,deletions` 로 값 확인. 장부(`$LCR_ROOT/ledger.jsonl`)에 같은 SHA 의 `FINAL_DONE` 이 있으면 `SKIP_SAME_SHA`.
2. Aside 창·탭 id: AppleScript 로 탭 목록(id·URL)을 읽어 Cursor·ChatGPT·Gemini 탭을 고른다(없으면 탭 1개만 `make new tab` 후 활성 탭 원복). id 는 재시작 시 바뀐다.
3. 인벤토리: `gh pr diff $LCR_PR > $P/pr.diff`, 파일별 +/− 를 `$P/inventory.tsv`(경로\t추가\t삭제)로. 합계를 GitHub 메타와 대조.
4. Cursor 사용량: `bash $SK/aside/usage.sh` → `N od_disabled=true`. 90% 이상이거나 On-Demand 가 켜져 있으면 중단.

## 2. 흐름
| 단계 | 명령 | 통과 조건 |
|---|---|---|
| Planner | `python3 $SK/make_wu_prompt.py planner > $P/planner-prompt.txt` → `bash $SK/aside/launch.sh` → `poll2.sh <세션> PLANNER_JSON $P/planner-raw.txt` | `check_coverage.py raw inventory out` = PASS (파일 N/N, 파일별 줄 수 일치, 파일당 Primary WU 1개) |
| WU 리뷰·감사 | `make_wu_prompt.py wu $P/planner.json WUxx > $P/WUxx-prompt.txt` 후 `bash $SK/aside/driver.sh WU05 WU04 …` (위험 높은 순) | `check_wu.py` = COVERAGE_OK (SHA 일치, WU 파일 전부·변경 줄 이상 읽음). 감사는 외부 전송·권한·삭제·개인정보 WU 와 S0/S1·낮은 확신일 때만 |
| 통합 | `driver.sh INTEG` | 경계마다 VERIFIED/ISSUE/NOT_CHECKED, NOT_CHECKED 가 남으면 `HOLD — REVIEW COVERAGE GAP` |
| 최종 | `$P/FINAL-REVIEW-MAP.md` + 장부 `FINAL_DONE` | S2 이상은 오케스트레이터가 해당 줄을 직접 읽거나 로컬 재현해 확인한 뒤에만 보고 |

- 드라이버는 실패 시 즉시 멈추고 장부에 사유를 남긴다. 재실행하면 결과 파일이 있는 WU 는 건너뛴다(중단·재개).
- Claude Code 백그라운드는 2시간 제한 → 드라이버를 3~4 WU 씩 나눠 실행.
- 실행 중인 셸 스크립트 파일을 수정하지 말 것(bash 가 읽는 도중이라 깨진다). 새 이름으로 만들고 다음 단계부터 쓴다.

## 3. 다른 엔진으로 같은 리뷰 (비교)
- 1:1 비교는 **같은 WU 분할·같은 지시문**으로 한다. 엔진별 Planner 는 분할 비교용으로 따로 돌린다.
- 저장소를 못 읽는 엔진은 `gpt_bundle.py` 로 "줄번호 붙은 HEAD 원문 묶음"을 붙인다: `python3 $SK/gpt_bundle.py planner|wu WUxx|audit WUxx <rev.json>|integ <summary.json> <out>`. 각 파일 끝 `END FILE (last line N)` 표식 + 응답 JSON 의 `bundle_files_seen` 을 `check_seen.py <prompt> <result.json>` 으로 대조해 **첨부를 끝까지 읽었는지** 증명한다.
- ChatGPT: `glaunch.sh <prompt> <짧은지시>` → `gpoll2.sh` / 순차는 `gdriver.sh`. Gemini: `gem_js.sh`·`mpoll.sh`. GitHub 연결이 꺼져 있으면 켜지 말고(권한 승인 필요) 묶음만 붙인다. 화면 조작 세부는 [references/engines.md](references/engines.md).

## 4. 판정·보고
- Finding 필드: id·severity(S0~S3)·evidence(REPRODUCED/NOT_TESTED/…)·file:line+역할·조건·영향·반대 증거·최소 수정·검증법. 반대 증거로 막히면 철회.
- 최종: 코드/아키텍처/진행 판단 3개, Coverage(files N/N, 고위험 경로 N/N, 경계 N/N), 실행·미실행 시험, Review Debt, 비용(유료 API 0, 세션 수, 사용률 전후).
- 엔진 비교표: 분할(WU 수·경계 수), WU별 판정·S 등급·같은 결함 발견 여부, 소요, 끝까지 읽음 여부, 엔진 고유 발견(예: CI 상태 확인).
- 보고는 한국어 존댓말, 상태 한 줄 + 결정 1~2개. 증거는 파일에.
