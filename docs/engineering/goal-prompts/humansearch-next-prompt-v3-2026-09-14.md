> [낡음 — 2026-09-14 11:00] 이 문서는 쓰지 마십시오. 사장님의 9/13 23:24 지시("RPS 프로젝트 생성은 필요해")를 반영하지 못했습니다.
> 최신 정본 지시서는 docs/engineering/goal-prompts/humansearch-next-prompt-v5-2026-09-14.md 이고, 진행 상태는 docs/engineering/humansearch-v5-execution-ledger-2026-09-14.md 입니다.

/strict HumanSearch 후속 v3.1 (2026-09-14 09:00) — HS-13 결함 수정을 끝내고, 브라우저 사용권(HS-05)을 세운 뒤, 잡코리아 1명 완주와 RPS 읽기 연동까지 간다. 사람인은 미결제라 라이브만 NOT_RUN 후보다. 나는 자리를 비운다. 파괴적 작업·외부 발송·후보 접촉·정본 되돌리기·merge 만 멈추고 나머지는 네가 판단한다. "CI 초록 = 안전"이 아니다.

## 결론 (1층)
결함 수정(A)과 브라우저 사용권(B)을 병렬로 끝낸 뒤에만 잡코리아 1명 완주와 RPS 읽기(C)로 간다. 결정 카드 4개는 사장님 몫이다.

## 0. 먼저 읽을 것 (전부 실존 경로. 없으면 git log --all -- <경로> 로 회수)
- ~/Desktop/hs13-followup-prompt.md — 9/12 결함 수정 지시(S1-1~S2-6, 불변식 I1~I3, D13, triage 규칙). 이 문서의 1절은 그 파일을 그대로 따른다.
- worktrees/hs-13-stack-20260910/docs/engineering/humansearch-hs13-position-brief-goal-2026-09-10.md — HS-13 정본(§2 채택표·§7 D1~D12·§9 카드·§12 비범위).
- worktrees/hs-0004-recovery-20260910/docs/engineering/humansearch-next-issues-wu-2026-09-10.md — HS-00~12 장부(상태 열은 전부 PLANNED, HS-00.01~03 만 RED/GREEN 커밋 있음).
- worktrees/hs-0004-recovery-20260910/docs/engineering/goal-prompts/humansearch-journey-kickoff-2026-09-07.md — 9/8 사장님 결정 ①~⑫(자동 재개·무조건 저장·1초 멈춤·Aside만·다중 브라우저·LinkedIn 상세 저장). 같은 파일 v7 이 ~/Downloads/ 에 있다.
- docs/sot/humansearch-browser-contract.md — D0 정본. §4 표: 잡코리아·LinkedIn 은 exact-origin 목록과 D1 증명 전 연결 금지.
- 메모리 project_hs13_brief_spec_state_20260910, project_humansearch_owner_decisions_20260908, reference_aside_browser_control, project_concurrent_sessions_same_repo.

## 1. 사장님 원문 (해석하지 말고 그대로)
- 9/10: 회사 조사 → JD 3버전(RPS 1,899자·사람인/잡코리아 2필드·Gmail) → 팀 메일 → LinkedIn 후보(1촌 Email·URL·점수·학력·경력) → DB → "RPS 에서 프로젝트를 검색하거나 생성하여 South Korea·Boolean AND/OR 로 멈추지 말고 찾는다" → 후보별 1,900자 메시지 준비.
- 9/8: 자동 재개 한다 · 본 프로필 무조건 저장(동의 절차 없음) · 멈춰 하면 1초 안에 멈춘다 · 브라우저는 Aside 만 · 사람인·잡코리아 다중 브라우저 가능 · LinkedIn 상세도 저장.
- 9/14: "잡코리아도 역시 해야 하는데 모두 Aside 브라우저. 사람인은 현재 결제를 하지 않아서 테스트가 가능할지 모르겠다. RPS 읽기 연동도 중요한데 그 작업도 되어야 한다."
이 세 원문은 취소된 것이 없다. 뒤 원문이 앞 원문의 우선순위를 바꿀 뿐이다.

## 2. 지금 상태 (2026-09-14 실측. 다시 재지 말고 착수 때 git rev-parse 로만 대조)
- PR #83(task/hs-13-stack-20260910, HEAD 767d027) CI 초록이지만 사장님 결정 B: S1 4건·S2 2건 고치기 전 merge 금지. 9/12 이후 아무 세션도 착수하지 않았다. 워크트리 미커밋 0.
- HS-00~12 장부: task/hs-0004-recovery-20260910 이 origin/main(fc6beed)+48커밋, 원격 0·PR 0. 시험 파일은 test_hs_0001~0003 뿐. HS-01 이후 전부 PLANNED.
- 로컬 main 은 f12ea33(origin 에 없음, Issue #84). 모든 워크트리에서 acceptance-0-5 가 이 탓에 FAIL 한다. 코드 결함 아님. 사유만 기록하고 고치지 마라.
- Aside 실측(09-14 08:45): Claude 확장 deviceId 0c136c08-05a7-4f58-b8e1-713e23d7a711(표시명 Browser 2, 표식 URL 대조로 확정), 확장 사이트 권한 전체 URL 허용, sangmokang 프로필. 사람인(Valueconnect 기업회원)·잡코리아(밸류커넥트 서치펌)·RPS(talent/home, Value Connect - RPS, 프로젝트 10개) 3사 모두 로그인돼 있다. 요령: 페이지 이동 직후 screenshot 은 타임아웃이 잦으니 wait 3~4초 뒤 재시도, 잡코리아 헤더는 find 에 안 잡혀 screenshot 으로, RPS 첫 진입 "Hiring Assistant" 모달은 Close 만. Aside CDP 45103 은 인증 잠김. Chrome 9223·9225 는 v4 가 띄운 것 — 쓰지 마라(9/8 결정 ⑩). 비밀번호·캡차 입력 0, 세션 만료면 사장님께 로그인 요청.

## 3. 순서 (트랙 A·B 는 파일이 안 겹치므로 병렬. C 는 A·B 뒤)
### 트랙 A — HS-13 결함 수정 (워크트리 hs-13-stack-20260910 에서만)
~/Desktop/hs13-followup-prompt.md 의 "고칠 것"·"완료 조건"·"순서" 를 글자 그대로 수행한다. 요약: I1 claim_send 가 잠금 안에서 현재 패킷 body_sha256·recipients_sha256 을 대조 / I2 verify_and_mark 하나만 VERIFIED 를 만든다 / I3 open_new_attempt 는 자기 digest 를 기록 / JD 블록 밖 조건 거부 / packet-id 접두 주입 거부 / 카드 13.10 "legacy artifact" 정정 + schema_version. 결함마다 RED 커밋 → GREEN 커밋. Codex 적대 검토 최대 2회, S1 은 라운드 무관 merge 차단. push 뒤 PR #83 본문에서 "합격" 표현 제거. merge 는 사장님만.

### 트랙 B — 브라우저 사용권 HS-05 (새 워크트리 task/hs-05-<카드>-20260914, 기준 task/hs-0004-recovery-20260910)
잡코리아·RPS·사람인 어느 채널도 이것 없이는 자동 접속이 금지다(D0 §4). 장부 HS-05.01~05.09 를 카드 순서대로, 카드 하나 = 워크트리 하나 = PR 하나.
- HS-05.01 정책 문서: 9/8 결정 ⑦⑨⑩⑪⑫ 를 D0 §9·§11·§14 대체표로 정본에 반영(L3 결정 기록·승인 출처 = kickoff 문서 줄 번호).
- HS-05.02~05.04: 포트·프로필 발견, 목표 탭 1개, SQLite 사용권(RPS 채널당 1행·나머지 인스턴스당). 포트·경로는 contracts/humansearch/browser-policy.json 에서만 읽는다(P22).
- HS-05.05~05.07: 회수 가능한 전송 핸들 + 경합 100회 sent_after_stop==0 + 실제 소켓 중단 ≤1000ms + 사람 입력 회수 + 새 관측 뒤 재개(명시 STOP 은 자동 해제 안 함).
- HS-05.08 Aside 실증은 합성 페이지에서만. 확장 경로는 이미 붙는다(위 실측). 별도 --user-data-dir 인스턴스·CDP 재시작은 사장님 몫이니 못 하면 그 항목만 NOT_RUN.
- HS-05.09 STOP 파일·로컬 멈춤 명령.
HS-05 가 끝나기 전에는 잡코리아·LinkedIn 실제 화면을 여는 코드·시험을 만들지 않는다. fixture 는 합성만.

### 트랙 C — 채널 (A·B 병합 또는 최소 LOCAL_COMMITTED+AUDITED 뒤)
- 첫 라이브 1명 완주 채널 = 잡코리아(HS-11.01·02·07~10). 사람인 카드(HS-07.04~07.07)는 미결제로 상세 열람이 막히면 그 카드만 NOT_RUN(사유: 결제) 으로 남기고, 잡코리아가 같은 공통 저장 경계(HS-02·03·07.05)를 대신 실증한다. 목록 화면만 쓰는 HS-07.01~03 은 결제와 무관하면 그대로 진행한다 — 실제로 막히는지는 첫 접속 때 readback 으로 확인하고 추정으로 쓰지 마라.
- RPS 읽기 연동 = HS-13.11 + HS-11.04~06·11.11~13: 사장님이 만들어 둔 프로젝트 id 확인 → South Korea·포지션 필터 적용 readback → Boolean 3종(HS-13.07 순수 함수 산출) 순회 → 후보 목록·상세 읽기 → 무조건 저장(LinkedIn 상세 포함, partial/complete 구분, 저장 실패 = 순회 정지) → 중복 방지 → 근거 기반 채점(HS-12.03, LLM 숫자 유입 거부) → HS-13 패킷 [초도 LinkedIn 후보자] 절·InMail 초안에 연결. 실프로필 재사용·카드 클릭 지터·동일 URL 연속 금지·캡차/2FA 즉시 STOP.
- RPS 프로젝트 "생성"은 HS-13 정본 §2 8행이 오너 승인 없는 비범위로 확정했고 9/14 원문은 "읽기 연동"이다. 구현하지 말고 아래 결정 카드 1 로 올린다.
- 잡코리아 exact-origin 목록·화면 계약(HS-11.01)은 D0 §4 규칙대로 실제 허용 origin 을 먼저 정본화한 뒤 연결한다.

## 4. 유지되는 제품 흐름 (장부에서 지우지 않는다)
ClickUp 포지션 선택(HS-08.01) · Discord 멤버 명령(HS-08.03~09) · 회사 조사·JD 3버전·팀 메일·후보 URL·매칭 이유·점수·학력·경력·출처 있는 Email Contact(HS-13, 구현됨) · SQLite 원본 + Supabase 파생(HS-03·HS-10) · 반복 검색·평가·재기동(HS-12). 팀 보고 메일 기능은 구현 대상이지만, 결함 수정이 끝나고 사장님이 승인하기 전에는 실제 발송·재발송 0. 후보 접촉은 항상 0.

## 5. 규칙
- L3. 후보 PII·실 URL·실 이메일은 git·PR·판정 파일·로그에 0. fixture 는 example-·holder@valueconnect.kr·@example.com 만. linkedin.com 은 HS-05 전 열람 금지.
- 워크트리 1개 = PR 1개 = 카드 1개. 결함·카드마다 RED 커밋 → GREEN 커밋. 시험 약화 금지(P13), CHECKED 불변식(P20), 운영 상수는 계약 파일(P22), 파일 300줄 soft(P11). main 직접 수정 금지.
- 검사기는 UTF-8 과 LC_ALL=C 양쪽으로. printf|grep -q 금지. 매 카드 cd humansearch && uv run --no-sync pytest -q / ruff check src tests / mypy --strict src tests + 해당 검사기.
- Codex 적대 검토는 넘기기 전에 커밋(미커밋 소실 사고 있음). 판정은 파일로 회수해 저장.
- 착수 전 다른 세션의 같은 저장소 작업 여부 확인: git worktree list, gh pr list, ps 로 codex 세션 수.
- 커밋 메시지 한국어. merge 는 사용자만.

## 6. 사장님 결정 카드 (네가 정하지 마라. 보고서 맨 위에 답 없이 놓아라)
1. RPS 프로젝트 자동 생성 — 무엇을: 정본은 "확인만". 왜: 사이트 변경은 되돌리기·중복 방지 계약 필요. 버린 대안: 9/10 원문대로 생성 구현. 대가: 사장님이 프로젝트를 먼저 만들어야 순회 시작. 되돌리는 법: 새 L3 결정 기록 + 승인이면 HS-13.11b 로 카드 추가.
2. 사람인 라이브 NOT_RUN — 무엇을: 첫 1명 완주를 잡코리아로. 왜: 미결제. 버린 대안: 결제 후 사람인 먼저. 대가: 사람인 상세 저장 경로는 미실증으로 남음. 되돌리는 법: 결제 뒤 HS-07.04~07 카드 실행.
3. f12ea33 처분 — 메모리 project_f12ea33_relocation 의 가지 143a79f 로 이관·main 복원·push 승인 여부. 승인 전까지 acceptance-0-5 FAIL 은 사유 기록.
4. (해결) Aside 확장 연결·3사 로그인은 09-14 완료. 남은 것은 Aside 전용 인스턴스(사람인·잡코리아용 별도 프로필) 기동 여부 — HS-05.08 에서 필요해지면 그때 묻는다.

## 7. 완료 조건과 보고
- 트랙 A: 9/12 프롬프트 완료 조건 전부 fresh 실행 증거. Codex 재검토 S1 0건. PR #83 push·pull_request 두 이벤트 초록.
- 트랙 B: HS-05.01~05.09 각 카드 RED→GREEN 커밋·검사기 PASS·독립 감사 1회. 라이브 0.
- 트랙 C: 잡코리아 1명 완주 영수증 1건(재실행 시 같은 후보 재열람 0) · RPS 프로젝트 확인·필터 readback·목록 1페이지 읽기·상세 저장 1건 · 발송 0·후보 접촉 0.
- 채널별 1건 실증 뒤에도 반복 검색·저장·재개가 남으면 전체 완료라 하지 않는다. 자동 merge 없음.
- 보고는 쉬운 한국어로 트랙별 무엇/왜/증거(숫자 그대로)/다음. 이름·URL·이메일 0. "해결 확인"은 fresh 실행이 있는 항목에만. NOT_RUN 은 이유·해제 조건과 함께.