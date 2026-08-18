# Codex 서치 실행 프롬프트 — 뤼튼 5개 포지션 (2026-08-15)

너는 Valuehire v6 저장소(/Users/kangsangmo/Desktop/Valuehire_v6)에서 codex CLI로 라이브 인재 서치를 수행한다. 아래 5개 포지션을 사람인·잡코리아·링크드인 RPS에서 서치하고 후보를 채점·저장한다.

## 브라우저 접속 (이미 준비됨 — 새로 로그인/자격증명 입력 금지)
- 사장님 **Aside 브라우저**가 `127.0.0.1:45111` 원격 디버깅 포트로 떠 있고, 사람인·잡코리아·링크드인 RPS **로그인 세션이 살아 있다**(사장님이 직접 로그인함).
- 접속 도구: `/private/tmp/claude-501/-Users-kangsangmo-Desktop-Valuehire-v6/b413d459-c1c9-4e1d-9d13-228f782e5b22/scratchpad/cdp.py` (venv: 같은 폴더 `venv/bin/python`, websocket-client 설치됨). 사용법: `venv/bin/python cdp.py probe "<url부분문자열>" "<JS표현식>"` → 해당 탭에서 JS 평가. IIFE가 null 나면 객체 직접 반환식(`({...})`)으로 쓸 것.
- 탭 목록: `curl -s http://127.0.0.1:45111/json/list`. 개별 탭 `webSocketDebuggerUrl`에 raw WebSocket으로 붙어 `Runtime.evaluate`. `connectOverCDP` 전체 attach 금지(탭 과다 hang). suppress_origin=True 필수.
- **자격증명 자동 입력 금지.** 미로그인 화면이면 멈추고 사장님께 알림(자동 로그인 재시도는 계정 잠금 위험).

## 5개 포지션 (JD 요약 — 채점 기준)
1. **뤼튼 FP&A / Finance Data Analyst** (86eyhdzky): Finance/FP&A/IR 데이터관리·리포팅 5년+, SQL 쿼리 데이터추출, dbt/Airflow·BI·FinOps·IR 우대. 서울.
2. **뤼튼 Accounting Manager** (86eyhdzq1): IT업계 회계 3년+, 더존 iCUBE/아마란스10, K-IFRS 우대. 서울.
3. **뤼튼 일본법인 Accounting Manager** (z8nfn6merg): 회계·재무·세무 단독실무, 한국어+일본어 비즈니스급, **일본 현지 거주자**, IFRS·J-GAAP. 도쿄.
4. **뤼튼 Global Growth Marketer 북미** (86exbvqg6): 북미 크랙(AI캐릭터챗) 그로스. Reddit/TikTok/Discord 북미매체, creator/influencer/community 마케팅. **링크드인 RPS 중심** — 포지션 본문에 Boolean 6종(A~F)·Location 필터 3차·평가비중이 이미 적혀 있으니 그대로 사용. 서울근무+북미문화감각.
5. **뤼튼 Growth Marketer** (86eyhdzud): 그로스/퍼포먼스 마케팅 3년+, 모바일/웹 어트리뷰션, 서브컬처 이해, AI캐릭터챗. 서울.

전체 JD 원문은 ClickUp 태스크(위 id) 또는 `clickup_get_task`로 확보. 채널 매핑: 1·2·5는 사람인·잡코리아 국내 서치, 3은 일본거주라 링크드인 위주, 4는 링크드인 RPS 위주(국내 사람인·잡코리아는 보조).

## 서치 규칙 (창립 스펙 계승 — docs/engineering/humansearch-v6-founding-spec-2026-08-07.md)
- **서울권 대학 최우선**, 잦은이직 강한 감점(12개월 미만 2회+ 하드제외), 프리랜서 제외, 구조적으로 잘 쓴 프로필 가점, OTW 우선/Non-OTW는 현직 2년+.
- 새 검색 전 이전 검색 필터/키워드 **리셋 필수**(안 지우면 이전 71명 그대로 나옴).
- 백그라운드 탭은 카드 0 렌더 → 수집 직전 `Page.bringToFront`. 상세 열람은 숨김 iframe 우선, 목록 상태 깨지 말 것.
- 봇 회피: 카드 클릭 간격 지터, 같은 URL 연속 2회 열지 말 것, 캡차·2FA 감지 즉시 STOP.
- profile_url은 손으로 옮겨적지 말고 href 문자 그대로. 증거(스크린샷+본문+SHA) 없는 후보는 후보 아님.

## 산출
- 후보별 채점표(적합도·근거)를 `.claude/private-reviews/codex-5position-search-result-2026-08-15.md`에 저장.
- **발송(제안/InMail/메일) 절대 자동 클릭 0회.** 수집·채점·저장까지만.
- 각 포지션 최소 상위 5명. 채널별 로그인 상태·수집 건수를 표로.

## 안전선
- 발송 0, 자격증명 입력 0, 탭 닫기·창 종료 0, Aside 포트 45111 상태 유지.
- 2회 이상 같은 방식 막히면 멈추고 원인 기록 후 다음 포지션.
