# AI-native RA 비평 지적 수정 검증

다음은 독립 비평에서 나온 5개 지적과 수정 후 저장소 증거다. 제공된 증거만 검토하고, 각 지적이 실제로 닫혔는지 판정하라. 파일·외부 서비스·도구는 사용하지 마라. 이 검토는 전체 문서 전수검사가 아니라 5개 지적 수정 검증이라는 한계를 판정 앞부분에 반드시 밝혀라.

## 지적 1 — 실행할 수 없는 문서 인수 기준

- 수정 증거: `docs/engineering/ai-native-ra-search-orchestration-goal-2026-08-17.md:106-135`에 목표·계획·28개 프롬프트 수, 필수 절 10개, 목차 링크를 실제로 검사하는 전체 셸 명령이 들어 있다.
- 실행 증거: `PASS planning_packet goal=1 plan=1 prompts=28 required_sections=10 links=all-present`.
- 반대 시험: 프롬프트 27개, RED 절 삭제, 존재하지 않는 링크를 각각 거부했다.

## 지적 2 — NOT_RUN이 합격처럼 사용됨

- `docs/engineering/goal-prompts/ai-native-ra-search-orchestration/README.md:59-66`: `DECISION_APPROVED`, `CONTRACT_PASS`, `LIVE_PASS`를 분리하고 `BLOCKED_OWNER`, `BLOCKED_AUTH`, `BLOCKED_POLICY`, `NOT_RUN`, `FAIL`은 어떤 합격 선행조건도 충족하지 못한다고 명시한다.
- `p05-clickup-read-snapshot.md:11,41`, `p09-supabase-candidate-inventory.md:11,41`, `p10-sqlite-candidate-inventory.md:11,41`, `p11-gmail-attachment-catalog.md:11,41`: 계약 합격과 실제 합격을 분리하고 권한 부재는 차단으로 끝낸다.
- `p17-durable-work-queue.md:11,41`, `p18-channel-account-lease.md:11,41`, `p19-fleet-scheduler-recovery.md:11,41`, `p20-aside-local-discovery.md:11,41`: 운영 제어 장부와 실제 두 실행자 증거가 없으면 실제 합격이 아니다.
- `p26-shadow-loop-chaos.md:11,41`: ClickUp·세 내부 입력원·공유 큐·사용권·두 실행자·Aside의 실제 합격을 통합 선행조건으로 요구한다.

## 지적 3 — P00이 오너 결정과 강제를 한 프로젝트에 숨김

- `p00a-data-ownership-owner-decision.md:11,25-41`: 오너 답변 전 SOT 변경 금지, 서명·선택지·대가·되돌리기 누락 거부, 승인 전 `BLOCKED_OWNER`.
- `p00-data-ownership-sot.md:1,7,11,29`: P00B는 P00A의 `DECISION_APPROVED` 버전·지문·오너를 확인한 뒤 승인 내용을 임의 변경 없이 정본과 검사로 강제한다.
- `README.md:16,26-27`: P00A→P00B 순서와 두 독립 프로젝트를 목차에 반영했다.

## 지적 4 — 첨부 본문을 읽지 않으면서 내용 지문을 만든다는 모순

- `docs/engineering/ai-native-ra-search-orchestration-plan-2026-08-17.md:198-200`: 본문 승인 전에는 식별자·파일명·형식·크기로 만든 자료표 지문만 허용하고 첨부 본문 호출·내용 지문을 금지한다.
- `p11-gmail-attachment-catalog.md:7,29,41`: 내용 지문은 별도 원문 접근 프로젝트 전에는 존재하지 않으며, 권한·정책 부재는 실제 합격이 아니다.

## 지적 5 — 채용사이트 표시자와 실제 화면 시험 계약 누락

- `p22-saramin-one-candidate.md:11,15,25,29,37,41`과 `p23-jobkorea-one-candidate.md:11,15,25,29,37,41`: 채널별 `contracts/<channel>/markers.json`, 실제 화면에서 파생하고 개인정보 제거를 검증한 자료, 판정·배선·동작 분리, 가짜 브라우저 주 증거 금지, 실제 한 명과 외부 쓰기 0건, 정책·권한 부재 시 실제 합격 금지를 요구한다.

## 판정 요구

각 지적을 `RESOLVED`, `PARTIAL`, `UNRESOLVED` 중 하나로 판정하라. 하나라도 `PARTIAL` 또는 `UNRESOLVED`면 전체 `VERDICT: FAIL`이다. 새 결함을 추정하지 말고 제공 증거 안의 모순만 지적하라.

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
