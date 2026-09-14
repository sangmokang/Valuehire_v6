# 위클리 준비 작업 브리핑 — 2026-09-14 (검증 대상 주장)

> 이 문서는 Claude가 2026-09-14 07:58~08:20 KST에 사장님께 보고한 브리핑 원문이다.
> 아래 모든 문장은 "검증 대상 주장"이며, 저장소·워크트리·git 이력·Notion·Supabase 실측과 대조해야 한다.

## 1층 — 결론

위클리 준비 작업은 세 갈래로 흩어져 있고, 어느 하나도 main에 병합되지 않았다. 코드는 충분히 있고 부족한 것은 배송과 결정이다.

| 갈래 | 상태 | 막힌 이유 |
|---|---|---|
| weekly-ops 스킬 (브리프 자동 생산) | worktrees/weekly-ops-skill(task/weekly-ops-skill, HEAD ad91d53)에 main 대비 67커밋·38파일·11,813줄 추가, 9/6 이후 정지 | origin/task/weekly-ops-skill 대비 55커밋 미푸시, PR 0개 |
| admin 대시보드 (웹 화면) | main에 Phase B~D(humansearch/src/humansearch/admin_weekly_dashboard/), Phase E는 PR #66 OPEN | 9/6부터 rebase·병합 안 됨. e1 브랜치는 main 대비 13커밋 뒤, 6커밋 앞 |
| Supabase 데이터 파이프 | 테이블 253개 있으나 적재가 전부 멈춤(9/9 실측) | 9/9 결정 3건에 답이 없음 |

오늘(9/14 월) 11:20 위클리용 FY26W38 노션 페이지는 아직 없다. Notion `Weekly Growth Meeting` DB 최신은 FY26W37(Duration 2026-08-31~09-06, 생성 2026-09-06 17:02Z)이다.

## 2층 — 판단 근거

가장 최근 프롬프팅은 9/8의 "codex:rescue로 검증하고, 가상 리포트를 노션과 웹에 보여주고, 위클리 데이터와 대시보드 데이터를 코드로 공유하라"였다. 그 결과 9/9 새벽에 착수 프롬프트 v3(WU-0~8, "죽은 Supabase 파이프를 되살려 위클리를 DB에서 낸다")가 작성됐고, 사장님께 결정 3건을 물은 채 세션이 끝났다.

- anon 키 재발급 여부. 지금은 service_role 키만 살아 있어 프런트엔드에 못 쓴다.
- 적재 코드 위치. ClickUp→Supabase 동기화 스크립트가 Valuehire_v4/scripts/import-clickup-to-position-boards.py에만 있고 v6에는 0건이다.
- FY25 보드의 Live 포지션 185건을 트렌드에서 뺄지.

9/9 Supabase 실측 주장: pipeline_position_cards 최신 8/31 23:05(1,136행), gmail_messages 7/25(803행), pipeline_stage_history 5/20(56행), weekly_growth_metrics 2026-W21(18행), gmail_position_requests 0행. RPC `weekly_brief_snapshot`은 v4 마이그레이션(Valuehire_v4/supabase/migrations/20260725090000_weekly_brief_snapshot.sql)에만 있고 v6 supabase/migrations(3개)에는 없다.

병합 전에 정리할 방향 충돌이 하나 있다. weekly-ops 워크트리는 9/4~9/5에 개인정보(PII) 차단 게이트를 10라운드 강화했는데(커밋 3d3f045→1a39d95→1522be1→cfee50b→6f5766b→97eba8d 등), 9/6 split/p1-weekly-evidence-infra(3fc86cc)는 "내부 전용 도구"라는 9/5 결정으로 이메일·전화 정규식 차단(find_sensitive_values, EMAIL_PATTERN/PHONE_PATTERN)과 후보자 필드 차단을 제거했다. 어느 쪽을 정본으로 할지 정해야 스택 PR을 열 수 있다.

병합용 스택은 9/6에 이미 잘려 있다: task/weekly-ops-skill-stack-1(d594e36, main 대비 13커밋), stack-2(cd8d47d, 14), stack-3(5be9f38, 15). 각 커밋 메시지가 "3,000줄 미만" 제약을 명시한다. 실제 생산 실행은 FY26W36 1회(docs/weekly-ops-2026-08-31-receipt.md, 스냅샷 rpt_6b0bfab9f7bbed136f50bf9e). W37(9/7)은 MCP 수동 집계.

ChatGPT 사이트(valuehire-weekly-operations.sangmokang.chatgpt.site)와 v6 설계 차이:

| 항목 | ChatGPT 사이트 | v6 weekly-ops 정본 |
|---|---|---|
| 데이터 출처 | ClickUp, Gmail | Supabase RPC + ClickUp + Gmail + 채용사이트 + 포털 발송 이력 |
| 주차 정의 | 일 00:00~토 23:59, "FY26W37 = 9/13~19" | 월 00:00~월 00:00, Notion FY26W37 = 8/31~9/6 |
| 포털 발송 집계 | 없음 | 채널별 4주, provider 영수증 ID 있는 건만 SENT로 계수 (docs/sot/weekly-ops-contract.md, contracts/weekly-ops/runtime-contract-v1.json outreach_sources) |
| 4주 트렌드 | 있음(ClickUp 기준) | DB 이력이 5/20에 멈춰 현재 불가, NOT_COLLECTED 표기 |

사이트 주차 라벨이 노션과 1주 어긋난다.

ChatGPT로 부족한 두 가지를 채우는 방법:
- Supabase 연결: ChatGPT Developer mode 커스텀 MCP 서버 + Supabase 공식 MCP/Edge Function MCP. 읽기 전용 키로 RPC와 파이프라인 테이블 노출. 단 파이프가 죽어 있어 붙여도 8/31 값. 연결보다 적재 재가동(v3 WU-1~4)이 먼저.
- 잡코리아·사람인·링크드인 발송 이력: 세 포털 모두 공개 API 없음. Gmail 영수증 메일은 응답이고 발송 총량이 아님. 로그인 브라우저에서 발송 이력 화면을 읽어 Supabase에 적재한 뒤 ChatGPT가 DB를 읽는 경로가 맞다. runtime-contract에 세 포털 발송 이력 화면 경로·영수증 규칙이 이미 정의돼 있다.

## 3층 — 마무리 순서 제안

1. 오늘 오전: FY26W38 브리프는 MCP 수동 집계. 파이프라인 두께 전주 대비 표 필수.
2. 결정 3건에 답(v3 WU-0, 코드 0줄).
3. PII 정본 확정 후 weekly-ops 스택 1→2→3 PR.
4. PR #66 rebase·병합, shadow_server에 position_cards 배선.
5. v3 WU-1~8 실행으로 위클리·대시보드·ChatGPT 사이트가 같은 Supabase 스냅샷을 읽게 한다.
