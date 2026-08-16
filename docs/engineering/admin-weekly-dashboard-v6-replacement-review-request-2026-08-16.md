# 관리자 주간 대시보드 v6 전면교체 목표 문서 — 외부 적대 검증 요청

당신은 구현자가 아닌 독립 검증자다. 파일을 수정하지 말고 읽기 전용으로 검토하라.

검토 대상:

- `/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/admin-weekly-dashboard-v6-goal-v2/docs/engineering/admin-weekly-dashboard-v6-replacement-goal-2026-08-16.md`

저장소 정본:

- `/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/admin-weekly-dashboard-v6-goal-v2/docs/sot/coding-principles.md`
- `/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/admin-weekly-dashboard-v6-goal-v2/docs/sot/git-workflow.md`
- `/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/admin-weekly-dashboard-v6-goal-v2/docs/sot/verification-commands.md`
- `/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/admin-weekly-dashboard-v6-goal-v2/docs/sot/mechanism-registry.yaml`
- `/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/admin-weekly-dashboard-v6-goal-v2/README.md`

검증 목표:

1. 이 문서만 구현자에게 주었을 때 저장소 구조·검사 체계와 충돌하지 않고 Phase 0부터 순서대로 구현 가능한가.
2. v4/v5 코드·런타임·DB·정적 자산을 전혀 사용하지 않는 clean-room 교체가 기계적으로 강제되는가.
3. 월요일 회의가 전주 일요일 00:00부터 이번 주 일요일 00:00 직전까지를 세며, Google Calendar 표시 주차를 ISO라고 추측하지 않는가.
4. 네 mailbox의 보낸 메일 중 raw 제목 첫 글자부터 `[추천]` 또는 `[포지션]`이고 외부 수신자가 있는 메시지만 고르며 thread 전체가 아닌 당시 message body만 추출하는가.
5. 고객사 추천·포지션 ClickUp 대상, 분류, body-only description, 중복 방지, approval, lease/fencing, response loss/readback이 DB와 AC로 닫혀 있는가.
6. v4/v5/v6 × aisearch/humansearch 여섯 source pair의 원자료·실행·발견·고유·포지션 숫자를 빠짐없이 보존하고, 미제공 자료를 0으로 꾸미지 않는가.
7. 인증·권한·감사·암호화·key lifecycle·보관·실제 삭제가 서로 모순되지 않는가.
8. PASS/FAIL/NOT_RUN, target count, source completeness, snapshot watermark, mutation test가 가짜 합격을 막는가.
9. 고정 기술 버전과 실제 명령이 peer/runtime 관점에서 설치 가능한가.

P0 또는 P1 결함이 하나라도 있으면 FAIL이다. 각 결함은 반드시 최신 대상 파일의 정확한 `file:line`, 재현 논리, 그대로 구현했을 때 사업 영향, 최소 수정안을 포함하라. 과거 판정이나 문서의 자기주장을 근거로 삼지 말고 현재 파일을 직접 읽어 확인하라. 결함이 없으면 어떤 공격을 시도했고 왜 실패했는지 항목별로 남겨라. 실행하지 않은 시험은 NOT_RUN이라고 명시하라.

[출력 형식 — 반드시 지킬 것]
읽는 사람은 기술 배경이 없는 사업 책임자다. 판정 내용은 절대 축소하지 말고, 표현만 풀어 써라.
1) 문서 맨 앞에 "결론". 결정할 사항 1개당 1~2문장, 전체 분량 상한 없음. 전문용어는 풀어 쓰더라도 결론에서는 쓰지 마라.
2) 그다음 "판단 근거": 왜 그렇게 봤는지, 갈림길에서 왜 이 해석을 골랐는지, 버린 해석은 왜 버렸는지, 이 판정이 틀리면 무엇이 깨지는지.
3) 그다음부터 기술 상세·명령·출력·file:line 전문. 증거는 하나도 생략하지 마라.
- 전문용어는 첫 등장 문장 안에서 괄호로 풀어 써라. 뒤에 몰아 쓴 용어집은 무효다.
- 터미널 출력·코드 블록·표를 붙였으면 바로 아래에 "→ 뭘 시켰나 / 뭐가 나왔나 / 좋은 소식인가 나쁜 소식인가" 1~3줄을 달아라.
- 첫 줄에 `VERDICT: PASS|FAIL` 한 줄을 두어라. 그 한 줄은 결론의 일부가 아니라 기계가 읽는 표식이므로 결론 제목 앞에 온다.
- file:line 을 인용하면 그 줄이 무슨 일을 하는 줄인지 한 마디 덧붙여라.
- 결함마다 심각도 라벨을 붙이고, 그 옆에 그대로 두면 사업/운영에 무슨 일이 생기는지 한 문장으로 덧붙여라(라벨을 지우지 마라).
- 설계 결정을 지적할 때는 "무엇을 / 왜 / 버린 대안 / 대가 / 되돌리는 법" 5줄로 적어라.
- 이번에 건너뛴 것·확인하지 못한 것·중간에 실패해서 다시 한 것을 판정 앞부분에 명시해라.
- 추정과 확인된 사실을 구분 표시해라(확인 못 한 것은 ※).
- 한국어 존칭체. 초등학생용 비유는 쓰지 마라 — 성인 의사결정자 수준으로 써라.
