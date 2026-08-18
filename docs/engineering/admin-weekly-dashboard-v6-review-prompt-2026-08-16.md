# Claude 1차 적대검증 요청 — 관리자 주간 대시보드 전면교체 목표

당신은 구현자가 아닌 적대적 검증자다. 저장소를 수정하지 말고 읽기 전용으로만 검증하라.

검증은 저장소 훅이 개입하지 않는 중립 폴더에서 실행된다. 아래 상대경로는 모두 `/Users/kangsangmo/Desktop/Valuehire_v6/`를 기준으로 절대경로로 해석하라.

검증 대상 문서를 처음부터 끝까지 읽어라.

- `docs/engineering/admin-weekly-dashboard-v6-replacement-goal-2026-08-16.md`

그 문서가 인용한 다음 정본과 실제 코드도 필요한 범위에서 직접 읽고, 문서 주장과 다르면 지적하라.

- `AGENTS.md`가 저장소 파일로 없다면 이번 검증에서는 사용자 제공 계약이 존재한다고 가정하되, 파일 증거 없음은 한계로 적어라.
- `README.md`
- `docs/sot/INDEX.md`
- `docs/sot/coding-principles.md`
- `docs/sot/verification-commands.md`
- `docs/sot/git-workflow.md`
- `docs/sot/hook-contracts.md`
- `/Users/kangsangmo/Desktop/Valuehire_v4/app/(admin)/admin/dashboard/page.tsx`
- `/Users/kangsangmo/Desktop/Valuehire_v4/tools/gmail-recommendation-clickup-sync/run.mjs`
- `/Users/kangsangmo/Desktop/Valuehire_v4/tools/gmail-recommendation-clickup-sync/lib/gmail-body.mjs`
- `/Users/kangsangmo/Desktop/Valuehire_v4/tools/gmail-recommendation-clickup-sync/lib/parse-subject.mjs`
- `/Users/kangsangmo/Desktop/Valuehire_v4/supabase/migrations/20260725090000_weekly_brief_snapshot.sql`
- `/Users/kangsangmo/Desktop/Valuehire_v4/supabase/migrations/20260516120002_sourcing_results.sql`
- `/Users/kangsangmo/Desktop/Valuehire_v5/tools/multi_position_sourcing/humansearch_supabase_sync.py`
- `/Users/kangsangmo/Desktop/Valuehire_v5/scripts/humansearch_supabase_backfill.py`

목표는 코드를 평가하는 것이 아니라, 이 목표·구현 프롬프트가 실제 구현자를 잘못된 완료로 유도할 구멍이 있는지 평가하는 것이다. 아래 항목을 반드시 하나씩 판정하라.

1. “4세대 의존성 완전 배제”와 4·5·6세대 AI/Human Search 원자료 보존이 동시에 가능한 경계인지. 중립 반출 계약이 숨은 실행 의존성을 만들지 않는지.
2. Gmail thread 전체가 아니라 개별 message의 그 당시 업무 본문만 가져오는 규칙이 MIME 구조, HTML 인용, plain fallback, 자동 서명, 첨부파일, 전달/답장 제목에서 기계적으로 검증 가능한지.
3. 제목이 태그로 시작하고 외부 수신자가 있는 조건에서 To/Cc/Bcc, 주소 정규화, alias, 내부 도메인, Gmail 검색 과포함을 잘 막는지.
4. 중복 판정이 같은 메시지 재처리와 같은 업무 대상 재등록을 구분하는지. 동시 실행, timeout 뒤 unknown outcome, 기존 v4 ClickUp task와의 연결에서 두 개 생성될 경로가 남는지.
5. ClickUp 현재 상태명과 포지션 분류 규칙이 사용자 예시를 충족하는지. 일반 Engineer, 복합 직무, `etc`, `scraped`, 상태명 변경에서 잘못된 자동 쓰기를 막는지.
6. 월요일 회의 주차와 직전 일요일~토요일 사건 창이 수학적으로 맞는지. 자정 경계, KST, 회의 이동·휴일, 늦게 도착한 사건, snapshot revision에서 조용한 덮어쓰기가 없는지.
7. AI Search/Human Search의 4·5·6세대 숫자를 나중에 세부 분석할 만큼 원자료로 보존하는지. 원시 행, 고유 후보, run, position, channel, source generation, event time, 거부 행이 충분한지.
8. 메일·후보 개인정보가 git·로그·ClickUp·새 데이터베이스에서 과다 보존되거나 노출될 경로가 있는지. 사용자 요구를 지키면서 더 적게 보존할 수 있는지.
9. v6 저장소에 관리자 제품 기술 기반이 없는 상황에서 프롬프트가 실행 가능할 만큼 구체적인지, 아니면 구현자가 임의로 큰 선택을 하게 되는지.
10. 인증된 기존 화면 캡처와 구글 캘린더 일정 고유값이 없는 상태를 정직하게 NOT_RUN으로 다루고, 완료로 위장하지 않는지.
11. 각 인수 기준과 반대 시험이 실제 실행 가능한지. 정적 문자열 검사만으로 가짜 합격하거나 시험 0건으로 통과할 구멍이 있는지.
12. 문서 안의 서로 모순되는 규칙, 잘못된 수치, 근거 없는 확정, 빠진 운영 중지점이 있는지.

각 결함은 반드시 대상 문서의 정확한 `file:line`과 함께 적고, 가능하면 정본 또는 기존 코드의 반대 증거 `file:line`도 붙여라. 추측만으로 FAIL을 만들지 마라. 실행하지 않은 검사는 NOT_RUN이라고 적어라.

PASS는 “제품 구현 완료”가 아니라 “이 프롬프트가 다음 구현 단계로 넘길 수 있을 만큼 모순·치명적 누락이 없다”는 뜻이다. 치명·높음 결함이 하나라도 있으면 FAIL이다. 중간·낮음만 있더라도 기계 인수 기준이 깨지면 FAIL이다.

[출력 형식 — 반드시 지킬 것]
읽는 사람은 기술 배경이 없는 사업 책임자다. 판정 내용은 절대 축소하지 말고, 표현만 풀어 써라.
1) 문서 맨 앞에 "결론". 결정할 사항 1개당 1~2문장, 전체 분량 상한 없음. 전문용어는 풀어 쓰더라도 결론에서는 쓰지 마라.
2) 그다음 "판단 근거": 왜 그렇게 봤는지, 갈림길에서 왜 이 해석을 골랐는지, 버린 해석은 왜 버렸는지, 이 판정이 틀리면 무엇이 깨지는지.
3) 그다음부터 기술 상세·명령·출력·file:line 전문. 증거는 하나도 생략하지 마라.
- 전문용어는 첫 등장 문장 안에서 괄호로 풀어 써라. 뒤에 몰아 쓴 용어집은 무효다.
- 터미널 출력·코드 블록·**표**를 붙였으면 바로 아래에 "→ 뭘 시켰나 / 뭐가 나왔나 / 좋은 소식인가 나쁜 소식인가" 1~3줄을 달아라.
- 첫 줄에 `VERDICT: PASS|FAIL` 한 줄을 두어라. 그 한 줄은 결론의 일부가 아니라 기계가 읽는 표식이므로 결론 제목 앞에 온다.
- file:line 을 인용하면 그 줄이 무슨 일을 하는 줄인지 한 마디 덧붙여라.
- 결함마다 심각도 라벨을 붙이고, 그 옆에 그대로 두면 사업/운영에 무슨 일이 생기는지 한 문장으로 덧붙여라(라벨을 지우지 마라).
- 설계 결정을 지적할 때는 "무엇을 / 왜 / 버린 대안 / 대가 / 되돌리는 법" 5줄로 적어라.
- 이번에 건너뛴 것·확인하지 못한 것·중간에 실패해서 다시 한 것을 판정 앞부분에 명시해라.
- 추정과 확인된 사실을 구분 표시해라(확인 못 한 것은 ※).
- 한국어 존칭체. 초등학생용 비유는 쓰지 마라 — 성인 의사결정자 수준으로 써라.
