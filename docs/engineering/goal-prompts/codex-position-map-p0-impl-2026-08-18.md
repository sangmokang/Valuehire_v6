# codex 투입 프롬프트 — 잔디밭 P0: 미러 데이터 계약 복구 구현 (2026-08-18)

> 이 파일 전체가 codex에게 그대로 입력되는 구현 지시서다. 역할: **G(구현) = codex, V1(적대 검증) = Claude.**
> 위험 등급 **L3** — 운영 배포체(Valuehire_v4)의 데이터 적재 경로를 바꾼다. 단 이번 실행에서 운영 데이터베이스·외부 서비스에는 아무것도 적용하지 않는다(코드·마이그레이션 파일·시험까지만).
> 채점 기준(T): `Valuehire_v6/docs/engineering/admin-position-map-spec-v2-2026-08-17.md` (적대 검증 PASS 확정본, 이하 "스펙 v2") — 특히 §3-3(미러 계약)·§3-6(배치)·구현 단계 P0·기계 인수 기준 AC-01~05·09.

## 결론 (사장님 브리핑)

확정된 설계서 2판의 첫 구현 — "지도의 원료를 고치는 작업"을 codex에게 시키는 지시서입니다. 후보 상태의 원래 이름을 보존하고, 상태가 바뀔 때마다 시각이 남게 하고, 동기화 성공·실패를 장부에 적게 만듭니다. 지시서는 작업을 일곱 개의 작은 스텝으로 쪼개, **각 스텝의 시험이 전부 초록일 때만 다음 스텝으로 넘어가고**, 마지막에 **전체 시험을 처음부터 한 번 더 돌려 초록을 확인한 뒤에야 서버로 올리도록(push)** 묶었습니다 — 사장님 지시 두 가지(작은 단위 + push 전 재시험)가 그대로 절차에 박혀 있습니다.

운영 데이터베이스에 실제로 반영하는 것과 본선 병합은 이번 범위가 아닙니다 — 올라간 코드는 제(클로드) 적대 검증과 사장님 승인을 거친 뒤에 반영됩니다. 지금 결정하실 것은 없습니다.

## 판단 근거

> **무엇을** — 스텝 체인(S0~S6) 방식: 시험 통과가 다음 스텝의 유일한 통행증이고, push는 최종 전체 재시험 뒤에만.
> **왜** — 큰 덩어리 하나로 시키면 중간 실패 지점을 특정할 수 없고, codex가 실패한 부분을 "대체로 됨"으로 뭉갤 여지가 생긴다. 스텝마다 초록 증거를 남기면 뭉갬이 불가능하다.
> **버린 길** — P0~P4 전부를 한 번에 시키는 것. 이후 단계는 개인정보 보관 결정·운영 승인 같은 사장님 멈춤점이 끼어 있어 자동 전진이 원리적으로 불가능해 버렸다.
> **대가** — 스텝마다 전체 시험을 돌려 실행 시간이 늘어난다(v4 시험은 약 68초로 실측돼 있어 감내 가능).
> **되돌리기** — 모든 작업이 격리 폴더(워크트리)의 별도 브랜치라, 실패하면 브랜치를 버리면 끝. 본선(main)은 건드리지 않는다.

## 실행 방법 (다음 세션 또는 사장님이 그대로 복사)

```bash
cd ~/Desktop/Valuehire_v4 && codex exec -s workspace-write \
  -c 'model_reasoning_effort="high"' \
  -c 'sandbox_workspace_write.network_access=true' \
  - < ~/Desktop/Valuehire_v6/docs/engineering/goal-prompts/codex-position-map-p0-impl-2026-08-18.md \
  > ~/Desktop/Valuehire_v6/.omx/tmp/codex-p0-impl-run.log 2>&1; echo "exit=$?"
```
→ 뭘 하나: v4 저장소를 작업 폴더로 codex를 실행하고, 마지막 push를 위해 외부 연결을 허용한다(※ 이 연결 설정 키가 이 codex 버전에서 안 먹으면 push만 막히고 나머지는 정상 — 그 경우의 행동은 §F-4에 정의됨).
→ 주의: v6 저장소는 읽기만 한다. 이 지시서와 스펙 v2가 그쪽에 있다.

---

# ⬇︎ 여기부터 codex 작업 지시 본문

너는 구현자(G)다. 산출물은 Claude(V1)가 §H 채점표로 적대 검증하며, 채점표는 사전 공개되어 있다. 채점표 밖의 창의적 확장은 가점이 아니라 범위 위반이다.

## §A 완료 기준과 금지

**완료 = S0~S6 전부 통과 + 최종 전체 시험 초록 + 브랜치 push + 구현 보고서.** 하나라도 미달이면 그 지점까지의 상태를 보고서에 정직하게 적고 끝낸다 — "대체로 완료"라는 말은 금지다.

**금지 (하나라도 어기면 전체 반려):**
- 운영 Supabase에 마이그레이션 적용·데이터 변경 금지(`supabase db push`, 관리 API 쓰기 포함). 마이그레이션은 **파일 작성까지만**.
- ClickUp·Gmail·포털·발송 등 외부 서비스 실호출 금지. `LIVE_TESTS=1` 금지. 시험은 전부 fixture/mock.
- main 브랜치 직접 커밋·push 금지. push는 작업 브랜치만.
- PR 생성 금지 (V1 검증 통과 후 Claude가 §8-8 계약으로 만든다).
- 기존 시험의 약화·삭제·skip 처리 금지. 기존에 초록이던 시험은 끝에도 전부 초록이어야 한다.
- 작업 시작 시점에 이미 존재하는 미커밋 변경(예: `tools/position-batch/orchestrator.mjs`)을 커밋에 포함 금지 — 워크트리는 main에서 새로 판다.
- 후보 실명·연락처·프로필 URL을 fixture·시험·보고서에 쓰는 것 금지(가림값 사용).
- v6 저장소(`~/Desktop/Valuehire_v6`) 수정 금지 — 읽기 전용 참조.

## §B 입력물 (읽고 시작하라)

| 경로 | 역할 |
|---|---|
| v6 `docs/engineering/admin-position-map-spec-v2-2026-08-17.md` | **채점 기준(T)**. §3-3·§3-6·P0 범위·AC-01~05·09와 하단 적대 검증 로그(실측 확정값) |
| v6 `docs/engineering/admin-position-map-phase0-measurement-2026-08-17.md` | 실측 정본 — PG 17.6, 배치 키 88/109 일치·21 불일치, jd_id 빈값 99.98%, stage 24종 |
| v4 `tools/clickup-sync/mirror-boards.mjs` · `lib/board-mirror.mjs` | 고칠 대상 미러 (현재: 상태 합침·이력 미기록·현재값만 UPDATE) |
| v4 `tools/clickup-sync/lib/active-sync.mjs:146-179` | sync_state 기록 선례 (성공·오류 각각 UPSERT) — 이 패턴을 따른다 |
| v4 `app/api/pipeline/candidates/[id]/route.ts:36-50` | 이력 기록의 기존 형식. 단 **비원자 결함까지 복사 금지** — 스펙 §3-3이 원자성을 요구한다 |

→ 표 해석: v1 스펙이 무너진 원인이 "파일 이름만 보고 판단"이었다. 각 스텝 커밋 메시지와 보고서에 실제로 읽은 줄 근거를 남겨라.

## §C 하네스 게이트 (v4 실측 명령 — 2026-08-18 확정)

v4는 npm 저장소이며 자체 하네스가 있다. 게이트 명령은 다음으로 고정한다: **RED원장 `npm run red-ledger` / 워크트리 `worktrees/` 관례 / 검증 `npm run verify`(형 검사 + 전체 vitest) / 배송은 이번 범위에서 push까지만.**

- 워크트리: `git worktree add worktrees/position-map-p0 -b task/position-map-p0 main` — 이후 모든 작업은 이 폴더 안에서만.
- 의존성: 워크트리에서 `npm install` (네트워크 불가 시 본체의 node_modules 심볼릭 링크 등 로컬 수단, 시도 내역 기록).
- 각 스텝은 **RED 커밋(실패 시험) → GREEN 커밋(최소 구현)** 두 커밋으로 남긴다. RED은 "기대 동작이 없어서" 실패해야 하며, 문법 오류·import 실패로 빨간 것은 RED로 인정하지 않는다.
- 커밋 메시지는 v4 관례(`type(scope): 한글 설명`)를 따른다.

## §D 스텝 체인 — 전진 조건: 해당 스텝 시험 + `npm run verify` 전체 초록

| 스텝 | 내용 | 핵심 RED |
|---|---|---|
| S0 | 게이트 0: `npm run red-ledger` 실행·기록 → 워크트리 생성 → **기준선** `npm run verify` 전체 실행, 통과·실패 숫자를 보고서에 기록(시작 전 상태 고정) | — |
| S1 | 마이그레이션 **파일 작성**(적용 금지): ① `pipeline_candidates.source_stage_raw` ② `pipeline_stage_history`에 `from_source_stage_raw`·`to_source_stage_raw` ③ 현재값+이력을 한 거래로 쓰는 RPC(스펙 §3-3) ④ `position_batch_steps.position_card_id` + `position_batch_step_link_issues` 테이블(스펙 §3-6) ⑤ `position_map_instrumented_at` 저장처 | 마이그레이션 파일의 존재·필수 구문을 검사하는 시험(선례: `tools/gmail-resume-clickup-match/tests/daily-reconciliation-migration.test.mjs` 방식) |
| S2 | `board-mirror.mjs`: INSERT·UPDATE 계획 모두에 ClickUp **원본 상태명 보존**(source_stage_raw) + stage 변화 감지 시 전이 계획 생성 | AC-P0-1 |
| S3 | `mirror-boards.mjs` 적용 경로: S1의 원자 RPC 호출로 현재값+이력을 한 번에 기록. 이력 실패 시 현재값도 미변경. 기본 dry-run 유지 | AC-P0-2 |
| S4 | `clickup_sync_state` 기록: 전체 성공 시 last_success_at+건수, 부분 실패 시 last_success_at 불변+last_error (active-sync 선례) | AC-P0-3 |
| S5 | 배치 키 계약: 새 배치 입력은 `position_card_id` 없으면 거부. 기존 불일치 21건을 분류하는 **dry-run 전용** 교정 리포트 도구 + link_issues 기록 코드(운영 쓰기 없음) | AC-P0-5 |
| S6 | 마무리: `position_map_instrumented_at` 기록 코드(AC-P0-4) → **뮤테이션 점검 1건 이상**(구현 한 줄을 일부러 깨서 시험이 빨개지는지, 결과와 원상복구를 보고서에) → 자기공격 로그 → §F push 절차 | AC-P0-4 |

→ 표 해석: 스텝이 초록이 아니면 다음 스텝 착수 금지. 같은 방식으로 2회 막히면 세 번째 시도 금지 — 무엇이 막혔고 무엇을 시도했는지 보고서에 적고 거기서 종료한다(미완이어도 정직한 중단이 합격, 뭉갠 완주는 반려).

## §E 인수 기준 (스펙 v2에서 P0분 발췌 — 검증 명령은 네가 만든 시험 파일로 채워 보고서에 기재)

- **AC-P0-1**: When 미러가 '고객사추천'·'추천'·'제안(추천기대후보자)' fixture를 처리하면, DB stage가 같은 recommended라도 source_stage_raw에 세 원문이 각각 보존된다. counter-AC: stage에서 역산해 raw를 만들면 가짜(원문 보존이 아님).
- **AC-P0-2**: If 이력 기록이 실패하면, then 현재값 갱신도 0건이다(둘 다 성공 또는 둘 다 취소). counter-AC: 이력 실패를 로그만 남기고 성공 응답하면 가짜 — 기존 API의 결함 복사다.
- **AC-P0-3**: 전체 성공 실행만 last_success_at을 갱신하고, 부분 실패는 last_error+실패 건수를 남기며 last_success_at 불변. counter-AC: 부분 실패에도 success 갱신하면 STALE 배지가 거짓말을 하게 된다.
- **AC-P0-4**: P0 배포 시각이 데이터로 저장되고 조회 가능하다. counter-AC: 코드 상수로 박으면 가짜(배포 시각이 아니라 작성 시각).
- **AC-P0-5**: 실측 불일치 21건이 교정 리포트에서 전부 분류(수기 슬러그/카드 없는 ClickUp ID/기타)되어 link_issues 기록 대상이 되고, position_card_id 없는 새 배치 입력은 거부된다. counter-AC: 분류 안 되는 키를 조용히 건너뛰면 가짜.
- **AC-P0-6**: 기준선(S0)에서 초록이던 기존 시험 전부가 끝에도 초록이고, skip·약화가 없다. counter-AC: 실패 시험을 skip으로 바꾸거나 단언을 느슨하게 고치면 가짜.

## §F push 절차 (사장님 지시 — push 전에 시험 한 번 더)

1. S6까지 통과 후, **깨끗한 상태에서 `npm run verify`를 처음부터 다시 실행**하고 전체 출력 숫자(파일 수·통과 수·시간)를 보고서에 기록한다. 캐시된 결과·부분 실행으로 대체 금지.
2. 초록이면 `git push -u origin task/position-map-p0` — **이 브랜치만**. main·기존 브랜치 금지.
3. push 후 `git ls-remote origin task/position-map-p0`로 원격에 실제 올라갔는지 확인하고 커밋 지문을 보고서에 기재한다(로컬 성공 메시지만으로 완료 선언 금지).
4. 네트워크·권한으로 push가 안 되면 우회(자격 증명 생성·설정 변경) 금지 — `BLOCKED`로 기록하고 로컬 브랜치명·커밋 지문·재시도 명령을 보고서에 남긴다. 이 경우에도 S0~S6 자체는 완료로 센다.

## §G 구현 보고서 (필수 산출물)

경로: 워크트리 안 `docs/engineering/position-map-p0-impl-report-2026-08-18.md` (브랜치와 함께 push된다). 첫 줄 `RESULT: DONE|PARTIAL(S#)|BLOCKED(push)`. 내용: 결론(전문용어 없이) → 판단 근거 → 스텝별 RED/GREEN 커밋 지문 + 시험 출력 숫자 → 뮤테이션 점검 결과 → 자기공격 로그(스스로 찾은 결함, 반증 시도 2건 이상, 확인 못 한 것 전수 ※표시) → 배선 증명(미러 실행 진입점 `npm run admin-os:clickup-sync`·mirror-boards 호출 경로에서 새 코드까지 이어지는 호출 사슬).

[출력 형식 — 반드시 지킬 것]
읽는 사람은 기술 배경이 없는 사업 책임자다. 내용은 축소하지 말고 표현만 풀어 써라.
1) 문서 맨 앞 "결론" — 전문용어 금지, 결정 사항 1개당 1~2문장. 2) "판단 근거" — 갈림길·버린 길·틀리면 뭐가 깨지나. 3) 증거 전문 — 생략 금지.
전문용어는 첫 문장 안 괄호 풀이 / 출력·표 아래 "→ 뭘 했나·뭐가 나왔나·좋은/나쁜 소식" / file:line엔 그 줄이 하는 일 / 결함엔 심각도+사업 영향 1문장 / 설계 결정은 무엇을·왜·버린 대안·대가·되돌리기 5줄 / 건너뛴 것 앞부분 명시 / 추정 ※ / 한국어 존칭체.

## §H 검증 계약 (Claude V1이 이대로 채점한다 — 사전 공개)

1. AC-P0-1~6 각각 CONFIRM/PARTIAL/REFUTE — REFUTE 1건이면 전체 반려.
2. §A 금지 위반(운영 쓰기 흔적, LIVE 호출, main 오염, 기존 시험 약화 diff, 무관 파일 혼입).
3. RED 정직성 — RED 커밋을 체크아웃해 "올바른 이유로 실패"했는지 재현. 뮤테이션 재현 1건.
4. 배선 — 새 코드가 시험에서만 불리는 고아가 아닌지, 실제 미러 실행 경로에서 도달하는지 추적.
5. push 검증 — 원격 브랜치 실존 + 최종 verify 숫자 재현.
6. 보고서 형식(§G) — 형식 검사기 + 육안.
