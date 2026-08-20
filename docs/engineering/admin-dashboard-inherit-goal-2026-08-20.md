# Admin Weekly Dashboard — 16개 로컬 전용 브랜치 승계 조사 (2026-08-20, 정정판)

> 위험 등급: L3 — 관리자 인증, 고객 메일, 후보자 자료, ClickUp 운영 쓰기와 서비스 전환이 함께 걸린 기능의 이어받기 판단이다.
> 성격: 이 문서는 새 코드를 만들지 않는다. "이어받아야 할 것이 무엇인가"를 확정하는 L1 조사 문서다. 최초 작성본(G)은 Codex 적대 검증(V1)에서 6개 주장이 REFUTED됐고, 그중 하나는 다른 저장소(Valuehire_v4)의 살아있는 병행 작업 세션 확인으로 최종 정정됐다. 이 문서는 그 정정을 반영한 최종판이다.

## 1. 결론 (1층)

- **16개 로컬 전용 브랜치 중 "새로 이어받아야 할 미지의 코드"는 실질적으로 없다.** 대부분 이미 열려 있는 PR #16→#20(대시보드 실제 코드)과 PR #28(계획·CI 하네스) 두 갈래에 흡수됐다. 다만 실패한 재시도 7개 브랜치에 PR에는 없는 감사 기록·스크립트 15개 파일이 남아 있다 — 코드 자산이 아니라 "왜 실패했는지"를 보여주는 기록이므로, 브랜치를 지우기 전 보존 여부만 사장님이 정하면 된다.
- **"잔디밭"(고객사×포지션 맵)은 v6의 16개 브랜치 어디에도 없다.** 정본은 이미 main에 병합 확정된 설계 문서(`admin-position-map-spec-v2-2026-08-17.md`)이고, **구현 대상은 처음부터 이 저장소(Valuehire_v6)가 아니라 Valuehire_v4**다. 방금 Valuehire_v4에서 실행 중인 다른 세션에 직접 확인한 결과, **`task/position-map-p0` 작업이 지금 진행 중**이며 테스트 72건 통과·Claude V1 file:line 재검증 완료·`npm run verify` 기준선 대비 신규 실패 0건 상태다. 남은 건 Codex V2(현재 백그라운드 실행 중) 하나뿐이고, 그게 끝나야 push/PR을 연다(사장님 승인 전 병합 안 함).
- PR **#16**(shadow-ui, MERGEABLE)과 **#28**(phase0-plan-checker-hardening, main과 병합 충돌)은 서로 완전히 다른 두 트랙이다 — 아래 3절 참고.
- 사장님이 기억한 4요소 중 **지표는 v6 코드(metric-contract-v1.json)로 실재**하지만 sourcing/mail 카운트 계열이다. **잔디밭·고객·포지션 매트릭스는 v6이 아니라 v4에서 지금 만들어지는 중**이다 — v6에서 "이어받을" 게 아니라 v4 세션과 합류해야 하는 작업이다.

## 2. 판단 근거 (2층) — 무엇이 왜 뒤집혔는가

이 조사는 3단계를 거쳤다: **G**(내가 직접 16개 브랜치 diff --stat 대조) → **V1**(Codex `exec --ephemeral --json --sandbox read-only`, 별도 프롬프트로 G의 결론을 모른 채 반증 시도) → **v4 세션 실측**(다른 Claude 세션이 Valuehire_v4에서 보낸 실시간 상태). G→V1에서 뒤집힌 것 6건, V1→v4실측에서 확정된 것 1건이다.

### 2.1 G가 놓친 것: "잔디밭"의 진짜 정체 (가장 중요한 정정)

G는 `apps/admin/app.js`의 `renderHeatmap` 함수를 "잔디밭 구현됨"으로 판정했다. **V1이 코드 내용을 직접 읽어 반증했다**: 이 함수는 12주 각각을 `PASS`(수집됨)/`미집계`로만 표시하는 "12주 집계 상태" 화면이지, 참여도나 고객사×포지션을 표시하지 않는다(`app.js:39` `heatmapLabel`, `styles.css:161`, 테스트 `test_admin_weekly_snapshot.py:114`가 `total_engagement` 필드가 없음을 확인한다). 이름이 heatmap이라서 같은 기능으로 착각한 것이다.

V1은 이어서 main 브랜치 커밋 이력(`git log main`)에서 진짜 정본을 찾아냈다: `73fbbc5 고객사×포지션 맵(잔디밭) 확정 스펙`, `e2efc53 잔디밭 스펙 v1 감사 원문 보존`, `0eb3d61 잔디밭 스펙 v2 확정`. 이 커밋들이 만든 문서 `docs/engineering/admin-position-map-spec-v2-2026-08-17.md` 65행이 이렇게 적어 놓았다:

> "구현 대상은 Valuehire_v4의 **/admin/position-map**이며, 문서 정본은 Valuehire_v6의 이 파일입니다."

→ 해석: v6 저장소는 스펙만 보관하는 정본 저장소이고, 실제 화면 코드는 처음부터 v4에 짓도록 설계돼 있었다. "v6의 16개 브랜치를 뒤져서 잔디밭을 찾는다"는 접근 자체가 잘못된 저장소를 보고 있었던 것이다.

### 2.2 v4 세션 실측으로 최종 확정

이 문서 작성 도중 Valuehire_v4에서 실행 중이던 다른 세션(`valuehire-v4-d4`)에 직접 상태를 물었다. 답변 원문(2026-08-20):

> "task/position-map-p0(worktrees/position-map-p0) 작업 중입니다. 다만 이건 화면(/admin/position-map) 자체가 아니라 그 밑에 깔릴 데이터 배관(ClickUp 원본 상태 보존 + 원자적 상태 전이 + 카드 연결 무결성) P0 단계이고, 화면·색 계산·주간 집계는 명시적으로 다음 단계 범위입니다. 진행 상태: 관련 테스트 72건 통과, 6개 커밋 코드를 file:line 단위로 직접 재검증(Claude V1) 완료, npm run verify 기준선 대비 신규 실패 0건, strict:gate/exit-gate/git diff --check 전부 PASS. 남은 건 Codex 2차 재검증(V2, 지금 백그라운드 실행 중) 하나뿐이고, 그게 끝나야 push/PR을 열 수 있습니다."

→ 해석: 이건 자기 신고(자기 세션이 스스로 한 말)이므로 이 문서 안에서는 **미확인·참고 정보**로만 다룬다(V2가 통과했는지, 실제 diff 내용이 무엇인지는 이 세션에서 직접 확인하지 않았다). 다만 "잔디밭/고객×포지션은 v6이 아니라 v4에서, 그것도 화면 이전 단계(P0)까지만 진행 중"이라는 큰 그림은 V1이 main 문서에서 확인한 사실(2.1절)과 정확히 들어맞는다.

### 2.3 나머지 뒤집힘 (V1 REFUTED 5건 요약)

| G의 원래 주장 | V1 판정 | 정정 내용 |
|---|---|---|
| 16개 브랜치 전부 PR에 완전 흡수 | REFUTED | 실패 재시도 7개 브랜치에 PR 밖 고유 파일 15개(감사 문서 14개 + 스크립트 1개) 존재. 코드 자산 아님, 기록성 파일 |
| goal-v2 등 14개 브랜치 나열 | REFUTED(숫자) | 실제 15개. PR #28의 직접 조상은 6개뿐이고 나머지는 버려진 실패 재시도 |
| gh mergeable=CONFLICTING | 혼합 | codex 샌드박스는 네트워크 차단이라 `gh` 원문 재현 실패. 로컬 read-only 병합 시뮬레이션으로 충돌 15건은 별도 확인 — 결론(충돌 있음)은 유지 |
| #16 선병합 없인 #20 병합 불가 | REFUTED(과장) | #20은 #16 위에 곧게 쌓인 구조(rev-list 0:6)라 #16 브랜치로는 바로 합칠 수 있다. "main 반영"과 "병합 가능 여부"를 혼동했다 |
| foundation ⊂ shadow-ui (부분집합) | **CONFIRMED** | 유일하게 살아남은 원 주장. shadow-ui는 foundation 대비 삭제 0줄·추가 92줄 |

→ 표 해석: 5줄 중 4줄이 G의 과장·오류였다는 뜻이다. G 혼자 낸 결론을 그대로 믿었다면 "16개 브랜치 다 흡수됐다"·"#16 없인 #20 못 합친다"는 두 가지 잘못된 전제로 다음 작업을 계획했을 것이다.

## 3. PR #16, #28이 각각 무엇인가

| | PR #16 | PR #28 |
|---|---|---|
| 제목 | Build a truthful local shadow admin weekly dashboard | Admin Weekly Dashboard v6 Phase 0 계획 검사기 외부 적대 감사 및 CI 우회 보강 |
| base | main | main |
| 성격 | **실제 제품 코드.** `apps/admin/{app.js,index.html,styles.css}`(로컬 전용 화면) + Python 계약/스냅샷/shadow_server. Synthetic 데이터만, 실제 Gmail/ClickUp/Supabase 연결 없음 | **순수 거버넌스/CI 코드.** Phase 0 "계획 문서 자체가 구조적으로 올바른지" 검사하는 스크립트(`check-admin-phase0-plan.mjs`)와 CI 우회 방지 강화. 대시보드 기능과 무관 — PR 본문 스스로 "관리자 제품 구현을 시작하지 않았다"고 명시 |
| 상태 | `mergeable: MERGEABLE`, CI green | CI green이나 `mergeable: CONFLICTING`(main과 충돌), PR 본문이 스스로 "P0-01 해결 전까지 BLOCKED" 선언, 워크트리에 미커밋 파일 1개(`...regex-eof-fix-goal-2026-08-19.md`) 잔존 |
| 병합 순서 | #16 먼저 → #20(source_policy, #16 위에 쌓임)을 그 위로 | 트랙 1(#16/#20)과 독립적이라 순서 제약 없음. 단, 충돌 해소·BLOCKED 사유 해결이 선행돼야 병합 가능 |

→ 표 해석: #16은 지금 바로 병합 검토가 가능한 완성품이고, #28은 코드는 다 됐지만 main과 충돌·자기선언 BLOCKED 두 가지 때문에 지금 병합하면 안 된다. 둘을 "둘 다 CI초록이니 비슷한 상태"로 묶어 보면 안 되는 이유가 여기 있다.

## 4. 다른 세션(다른 쉘)의 진행 상황 — 미실행/진행 중 항목

이 조사 도중 `ListAgents`로 확인한 활성 세션과, 상태를 직접 물어 받은 응답:

| 세션 | 저장소 | 상태(자기 신고, 미확인) |
|---|---|---|
| `valuehire-v6-e3` | v6 | HumanSearch 5개 브랜치(g3/d0/clean-room-plan/g0-secret-scan/plan) 정리 방향을 `/strict`로 브리핑 중. `codex:rescue`+`codeaudit` 병렬 실행해 g3 구현 재검증 중(2026-08-18 codex FAIL→같은 세션이 자체 뒤집기한 판정을 재의심). 미완료 |
| `valuehire-v6-29` | v6 | 읽기 전용 조사 완료. admin 대시보드(로컬 15개 브랜치, 실제 화면 코드 없음 — **본 문서 트랙 2와 정합**)와 HumanSearch(PR#13 정상)를 감사했고, "진짜 고객사×포지션 매트릭스는 Valuehire_v4의 task/position-map-p0"라는 것도 독립적으로 찾아냈다(**본 문서 2.1/2.2절과 교차 확인됨**). 정식 적대검증 실행 여부·PR#28 정규식 버그 커밋 여부는 사용자 결정 대기 |
| `valuehire-v6-35` | v6 | 7시간째 busy. `worktrees/verification-authority`에 미커밋 변경 다수(merge-group/principles-recovery 관련) — **이 세션은 손대지 않았다.** 응답 없음(질의만 보냄) |
| `valuehire-v4-d4` | v4 | `task/position-map-p0` P0(데이터 배관) 단계 작업 중. 위 2.2절 원문 참고. Codex V2 대기 중이라 push/PR 전 |

→ 해석: "다른 쉘에서 아직 못한 것"은 admin-dashboard 트랙에서는 **v4의 Codex V2 하나**이고, v6에서는 **PR #28 충돌 해소 + P0-01 BLOCKED 해소**다. HumanSearch/verification-authority는 이 조사 범위 밖의 별개 작업이라 손대지 않았다.

## 5. 권장 다음 행동 (사장님 결정 필요 — 실행 안 함)

1. PR #16 → #20 순서로 병합 검토(코드 충돌 없음, synthetic 전용, 실제 계정 연결 없음).
2. PR #28은 main과의 충돌 해소 + 미커밋 파일 1개 정리 + P0-01 BLOCKED 사유 해결이 선행돼야 함. 트랙 1과 무관하므로 트랙 1 병합을 막을 이유는 없음.
3. **잔디밭/고객×포지션 매트릭스는 v6이 아니라 v4의 `task/position-map-p0` 세션과 합류할 것.** v6에서 새로 설계·구현을 시작하면 이미 진행 중인 v4 작업과 중복된다.
4. 실패 재시도 7개 브랜치(15개 파일)는 삭제 전에 보존 여부만 결정하면 됨 — 되살릴 코드 자산은 없음.

## 6. 적대 검증 로그

### V1 — Codex (`codex exec --ephemeral --json --sandbox read-only`, 2026-08-20)

실행 로그: `/private/tmp/claude-501/-Users-kangsangmo-Desktop-Valuehire-v6/be6f5eee-cc7f-45fb-93bb-6ec8a74a8411/scratchpad/v1_codex_output.jsonl` (75줄, exit 0)

**VERDICT: FAIL** — 검증 대상 7개 주장 중 1개(foundation⊂shadow-ui)만 CONFIRMED, 6개 REFUTED/혼합. 전체 판정·근거·기술 상세는 위 2·3절에 반영했다. 원문에는 위 표에 담지 못한 세부 diff·명령 출력이 더 있으며, 필요하면 로그 파일을 직접 연다.

### 남은 한계

- **V2(Claude 2차 재공격)는 아직 실행하지 않았다** — 이 문서는 V1 채택 상태다. L3 완료 체크리스트의 V2 항목이 비어 있다.
- v4 세션의 "테스트 72건 통과·Codex V2 실행 중" 발언은 **자기 신고이며 이 세션이 직접 재현하지 않았다** — 별도 세션이 이미 실행 중인 작업에 개입하지 않기 위해 의도적으로 확인을 생략했다.
- V1도 GitHub 실시간 `gh` 응답(codex 샌드박스 네트워크 차단)은 확인하지 못했다. 로컬 read-only 병합 시뮬레이션으로 충돌 자체는 별도 확인했다.
