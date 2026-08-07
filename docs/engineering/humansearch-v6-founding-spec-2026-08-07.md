> **고정 메타데이터** (2026-08-08)
> - **출처**: 강상모 사장님이 2026-08-07 `/strict` 명령어 인자(ARGUMENTS)로 이 Claude Code 세션에 직접 붙여넣은 원문. 이 세션이 1차 수신자이므로 "전달 경로"는 이 세션 자신이 직접 증인이다(외부 파일시스템 감사로는 확인 불가한 사실이며, 그 한계는 정당하다).
> - **본문**: 아래는 원문을 한 글자도 고치지 않은 verbatim 사본이다.
> - **배치 근거**: `docs/sot/INDEX.md`(2026-08-08 `d574fb7`로 확정)의 트리거 — "스크립트/훅/CI/다음 세션이 이 문서를 답으로 참조해야 하는가?" — 이 스펙은 아직 아무 코드도 참조하지 않는 계획 문서이므로 `docs/sot/`가 아니라 `docs/engineering/`(날짜 필수·불변)에 둔다. `docs/sot/`에 넣으면 20,000바이트 상한(이 저장소가 오늘 자신이 막은 안티패턴, `docs-sot-restructure-goal-2026-08-08.md` counter-AC②)을 이 문서(약 45KB)가 그대로 위반한다.
> - **§4 이식 원본 회수 가능성 재확인** (2026-08-08, Claude 직접 실측): `/Users/kangsangmo/Desktop/Valuehire_v5-aisearch-live-portal-wire`(원 저장소 `Valuehire_v5`의 git worktree)에서 `git log`·`git worktree list`·`git cat-file`로 확인:
>   - 로컬 HEAD = `cce9280`, `apps/aisearch/core/cdp_driver.py` = 정확히 **2,305줄** (본문 §4 주장과 일치)
>   - `git fetch origin` 후 `origin/task/aisearch-live-portal-wire` = `f02c537`(838줄, 본문 §4 주장과 일치)
>   - `git merge-base --is-ancestor cce9280 origin/task/aisearch-live-portal-wire` → NO. `git status`: `ahead 93` — **로컬이 원격보다 93개 커밋 앞서 있고 미push 상태를 직접 재확인**.
>   - 결론: 원본은 "회수 불가능"이 아니라 **"이 컴퓨터에 실재하며 이미 읽기 가능"**. v6로 이식하려면 (a) 그 worktree에서 파일을 직접 복사하거나 (b) `git push`로 원격에 반영한 뒤 받아오는 두 경로 중 선택하면 된다 — 별도 저장소 접근 문제가 아니라 이 컴퓨터 안의 작업이다.
> - **작업량 견적(15세션·32,850 LOC 등)에 대한 경고**: 이 수치들은 codex 1차 조사가 산식 없이 낸 추정치이며, codex 자신의 2차(감사) 패스에서 "근거 없음/재현 불가"로 판정받아 **폐기됐다**. 이 문서를 읽는 다음 세션은 저 숫자를 사실로 취급하지 말 것 — 정성적 결론("빈 저장소에서 시작 + 라이브 로그인 사람개입 의존 + 이식 원본은 로컬에만 있음 → 한 세션 전체 구현 불가, 단계별 착수 필요")만 신뢰할 것.

---

# humansearch v6 창립 지시서 — 로그인·브라우저 시행착오를 코드로 박제한다

> **이 문서의 목적** (2026-08-07 사장님 지시): 타 저장소(v6)에서 humansearch를 **처음부터**
> 다시 만든다. 핵심은 **로그인 시행착오와 브라우저 시행착오를 반드시 포함**하는 것이다 —
> *"그렇지 않으면 컴퓨터에서 실제로 쓸 수가 없기 때문이다."* 채점 로직만 이식하고 로그인·
> 브라우저를 빼면, v5에서 3개월간 **수백 건 실패**한 그 자리로 다시 떨어진다.
>
> **작성 원칙**: 지어내지 않는다. 모든 규칙 옆에 근거(파일:줄 · 커밋 SHA · 사장님 발화 날짜)가
> 붙는다. 근거 없는 문장은 없다. 부가 설명·중복 서술은 도려냈다.
>
> **근거 3계통** (전수 조사):
> - **로그인 코드 역사**: `skills/login/SKILL.md`, `docs/sot/26-portal-login-spec.json`
>   (`root_cause_catalog` RC1~RC13), `tools/multi_position_sourcing/` 로그인 15개 모듈,
>   `git log --all` 로그인 커밋.
> - **브라우저 코드 역사**: `apps/aisearch/core/cdp_driver.py`(브랜치 2,305줄), `harvest_policy.py`,
>   `humansearch_cdp_run.py`, `docs/sot/22·27`, PR #278.
> - **사장님 발화 원본**: Codex 세션 4,166건 + Claude 기록 3,840건 = **총 8,006건**을 훑고,
>   기계 프롬프트를 제거한 **사람 발화 2,006건**을 사고 근거 코퍼스로 삼았다(두 숫자는 다른
>   단계값이다 — 8,006 = 전체 훑은 양, 2,006 = 사람 발화만). **영속 원본**은
>   `.harness/humansearch-history/codex_user_msgs_human_only.jsonl`(4,166줄, 저장소에 커밋됨)이다.
>   Claude 3,840건과 중간 산출물(`scratchpad/mine/`)은 **세션 임시폴더라 비영속** — v6로 넘기기
>   전 `.harness/`로 옮겨 커밋해야 재현 가능하다(§10).
>
> **v5 최대 병리 (문서 첫 줄에 박는다)**: 로그인 하드닝 코드 **5,800줄이 stacked PR 7단으로
> 3개월째 미병합**이고(§7), 8월 4~5일 브라우저 수정도 미공유다.
> `.harness/red-ledger.tsv:115-127`은 이들을 GREEN으로 적지만 그 커밋은 **main의 조상이 아니다**
> (`git merge-base --is-ancestor ef6696c main` → NO, `7e917b3 main` → NO, 2026-08-07 확인).
> **더 심각한 것**(2026-08-07 적대검증에서 확인): 8월 라이브 브라우저 수정 2,305줄은 **PR #278에
> 올라간 것도 아니다.** PR #278의 head는 원격 `f02c537`=**838줄**이고, 라이브 수정 2,305줄은 **로컬
> worktree `cce9280`에만 있고 push조차 안 됐다**(`git show origin/task/aisearch-live-portal-wire:
> apps/aisearch/core/cdp_driver.py | wc -l`=838 vs 로컬 2305). **즉 §4의 이식 근거는 지금 이 컴퓨터의
> 로컬 worktree에만 존재한다 — v6가 참조하려면 먼저 push/병합해야 한다**(§4-말미·§8-7).
> **v6 규칙: "고쳤다"는 merge된 SHA를 댈 때만 참이다. PR을 여는 것도, 로컬에서 도는 것도 완료가 아니다.**

---

## §0. 범위 — humansearch는 로그인부터 시작한다

**scope in**: ① 3사(사람인·잡코리아·LinkedIn RPS) **로그인 준비/재로그인** → ② 사람이 걸어둔
검색 결과 순회 → ③ 프로필 1건씩 열람 → ④ 증거(스크린샷+본문) 저장 → ⑤ 하드제외 → ⑥ D1~D8
채점 → ⑦ 게이트 → ⑧ 합격자 등록/보고.

**과거 문서(`humansearch-sqlite-standalone-goal-prompt-2026-08-06.md`)와의 차이**: 그 문서는
로그인을 *"별도 모듈 전제 — 이 문서는 로그인된 탭 하나를 받는다는 인터페이스만 가정"*(그 문서 §0)
으로 **범위 밖**에 뒀다. **이번엔 정반대다.** 사장님 발화 집계에서 **로그인 미수행이 8회, 창
소유권/전면화 문제가 10회** 나왔고 마지막 주까지 재발했다(§1). **v6에서 로그인은 1급 시민이다.**
(해석 — 인과 단정 아님: 로그인을 범위 밖에 둔 것이 재발의 유일한 원인이라 단정하지는 않는다.
현 v5 러너는 이미 로그인 프리플라이트를 부른다 — `humansearch_cdp_run.py:41-56·868`이
`humansearch_preflight`·`session_guard`·`assert_live_or_abort`를 호출한다. 그럼에도 사장님이
매번 손으로 로그인을 시켜야 했다는 사실(§1 유형 [2] 8회)이, 로그인을 문서·설계의 1급 관심사로
끌어올릴 충분한 근거다.)

**실행 입력 계약 (v6가 반드시 넣을 것 — 현 러너의 최대 병리)**: 현 v5 러너는 포지션을 **상수로
하드코딩**한다 — `humansearch_cdp_run.py:15 POSITION = Position(position_id="86ey2cdfj", …뤼튼
AX Sales…)`, `SEARCH_URL_BASE`도 상수. CLI는 `<max_profiles> <start> <exact_target_id>`만 받는다
(`:937-947`). 즉 다른 포지션을 돌리려면 소스를 고쳐야 한다. **v6는 실행 파라미터를 입력 계약으로
받는다**:
```
RunRequest = { channel: 'saramin'|'jobkorea'|'linkedin_rps',
               position_ref: str, search_url: str, target_id: str,   # 기존 CDP target
               jd_or_config: {...} }   # 채점 계약(§6)에 넘길 JD
```
CLI/API/큐 어느 진입이든 이 계약을 받고, 채널별 로그인 프리플라이트(§3-5)를 통과한 뒤에만 순회한다.

**scope out**: 검색어·필터 **생성/입력**(그건 aisearch의 일 — humansearch는 사람이 이미 걸어둔
검색을 순회한다) · 제안/InMail **발송(Send) 클릭**(사람 손, §2-1) · Discord/ClickUp 연동의
**필수화**(선택적 어댑터, §6).

---

## §1. 사장님이 수십 번 반복한 서치 에러 — 전수 채굴 결과 (문서의 심장)

> 근거: 8,006건을 훑어 추린 사람 발화 2,006건(§ 서두). 각 행의 원문·날짜·파일:줄은 영속본
> `.harness/humansearch-history/`(커밋됨)와 세션 산출물 `scratchpad/mine/`(비영속)에 있다.
> **v6는 이 14개 유형을 코드로 못 나게 막아야 완료다** — 문서로 "하지 마라"만 적으면 v5처럼 재발한다.

> ⚠️ 아래 표의 인용은 **집계표용 요약 발췌**다(축약·조사 정리 있음). 원문 그대로의 전문과
> 파일:줄은 §10 재현 경로의 상세 목록에 있다. 유형 [13]의 "후보자 저장: 0건"은 사장님 직접
> 발화가 아니라 **사장님이 붙여넣은 Discord 실행 결과**다(구분해 표기).

| # | 사고 유형 | 횟수 | 최초→최종 | 대표 발화 (요약 발췌) |
|---|---|---|---|---|
| 1 | **중도 이탈·얕은 수집** (링크만 긁고 상세 안 엶, 페이지 중간 정지) | **9** | 06-02→08-07 | "링크만 떡하니 남겨뒀냐? 세부 내용 스크래핑하긴 했어?? 이거 내가 몇번이야기해"(06-03) |
| 2 | **로그인을 안 하고/못 하고 진행** | **8** | 06-08→08-06 | "로그인 세션을 강조해서 코딩해놨는데 지금 로그인을 안하도록 로직이 되어 있는건 뭐때문에"(06-08) |
| 3 | **사람이 봐야 할 창을 앞으로 안 띄움** | 5 | 08-04→08-06 | "병신아 크롬창 새거를 열어서 내가볼수있게해"(08-04) |
| 4 | **AI가 쓰는 창 ≠ 사장님 창** (새 인스턴스로 세션 유실) | 5 | 06-25→08-04 | "사용자가 보는 창과 AI가 제어하는 창이 서로 다른 창임 … 수백 건의 서치 실패 누적"(07-19) |
| 5 | **자격증명 취급 다툼** (비번 안 바꿈, .env로) | 5 | 08-04→08-06 | "비번 안바꿀거고 비번은 제거후 .env에 저장해"(08-04) |
| 6 | **거짓 완료 보고** | 4 | 06-05→08-06 | "맨날 넌 거짓말하잖아"(06-14) |
| 7 | **창·탭이 닫히거나 죽음** | 4 | 06-18→08-06 | "왜 꺼 씨발러마"(08-06) |
| 8 | **로그인 상태 오판** (멀쩡한데 실패 처리) | 4 | 07-16→08-05 | "사람인 로그인되어있고 링띤도 멀쩡한데?"(08-04) |
| 9 | **필터·검색어를 제대로 못 씀** | 4 | 06-09→08-06 | "'Target'과 '입점' 'MD'를 AND 조건으로 섞어야"(08-06) |
| 10 | **봇처럼 굴어 차단·인식됨** | 3 | 05-26→06-23 | "너무 빨라 봇으로 인식한다"(06-02) |
| 11 | **사람 개입 시 양보·재개 안 됨** | 3 | 06-05→06-08 | "내가 개입하면 스크롤 멈추고, 손 떼면 다시 되나?"(06-05) |
| 12 | **진행 표시 부재/익스텐션 역매칭 실패** | 3 | 06-24→08-05 | "지금 뭐 페이지 저장중인거냐?"(08-05) |
| 13 | **결과 0건인데 그대로 진행·보고** | 2 | 05-29→06-09 | "후보자 저장: 0건 … Issue 해결해야 한다"(06-09) |
| 14 | **서치 범위 멋대로 축소 해석** | 1 | 06-22 | "Search를 일반 웹 검색으로 잘못 축소 … 스킬에 명기해"(06-22) |

**두 가지가 3개월 내내, 마지막 주까지 끊이지 않았다: [1] 중도 이탈(9회), [2] 로그인 미수행(8회).**
v6 설계 1순위다.

### 1-A. 가장 무거운 단일 근거 — 2026-07-19 사장님 지시서 (1,995자)

사장님이 직접 원인 가설과 목표 아키텍처를 써 내려간 문서(Claude `df03264d…:14`). **v6 로그인
장(章)의 근간이다.** 요지:

- **증상**: *"Hermes가 aisearch 수행할 때 매번 로그인에서 실수가 많은데 … 로그인 세션 실패
  (수백 건 누적) … 사용자가 보는 브라우저 창과 AI가 제어하는 창이 서로 다른 창임 … 이미
  로그인된 세션이 존재하는데도 AI가 그 세션에 도달하지 못함."*
- **사장님이 짚은 원인**: ① `playwright.chromium.launch()`로 **빈 프로필 새 인스턴스** 생성
  (쿠키 없음) ② `connect_over_cdp`와 `launch` **혼재** ③ 일상용 Chrome 프로필 잠금 충돌.
- **사장님이 지정한 목표 아키텍처**: *"브라우저 식별자는 창이 아니라 **CDP 포트로 통일**"*,
  머신별 전용 Chrome 상시 실행, ***"launch 계열 호출은 전부 제거"***, 프리플라이트 게이트
  (`/json/version` 생존 → 로그인 확인 → 미로그인 시 **잡 큐 전체 일시정지 + Discord 알림 1건**),
  ***"절대 미로그인 상태로 서치를 반복 시도하지 말 것."***

이 지시가 6월에 이미 나온 것과 이어진다 — 06-25: *"CDP 방식을 최우선"*(`rollout-2026-06-25…:283`).
**07-19 사고는 이 6월 지시가 안 지켜진 결과다.**

### 1-B. 자동화 자신이 남긴 자백 (사장님 불만이 아니라 어시스턴트 응답에서 확보 — 설계 근거로 값이 높다)

1. **전면화 기능 부재**: 08-04 08:26 직후 *"claude-in-chrome 도구셋에는 '창을 화면 맨 앞으로
   가져오기' 전용 기능이 따로 없습니다 … window.focus()는 OS 레벨에서 100% 보장되지 않습니다."*
   → 유형 [3]의 단일 원인. **v6는 `Page.bringToFront`(CDP 레벨 전면화)를 계약에 넣는다.**
2. **창 없는 좀비 프로세스**: 08-06 14:19 직전 *"사람인은 브라우저 프로세스만 남아 실제 창이
   없는 상태입니다."* → 유형 [7]의 원인. **생존 판정을 "프로세스 있냐"가 아니라 "target 있냐 +
   `/json/version` 200이냐"로 한다.**
3. **로그인 코드 부재(v5 시점)**: 06-08 14:48 직전 *"사람인/잡코리아 = 자격증명 존재 여부만 확인,
   LinkedIn RPS = 자동 로그인 구현 없음."* → 유형 [2]의 뿌리. (이후 2026-07-26 `a31081f`로 구현됨.)

### 1-C. 근거 위생 — 코드엔 있으나 발화엔 없는 것 (정직하게 구분)

- **"이전 검색 필터 잔재"**(§4에서 다룸)는 **코드·커밋 근거는 확실**하나(PR #278 주석
  *"2026-08-04 잡코리아 라이브 실행에서 발견 — 이전(무관한) 검색의 필터 칩"*), **사장님 발화
  코퍼스(2,006건)에는 없다.** → 규칙은 코드 근거로 싣되, "사장님이 지시했다"고는 쓰지 않는다.
- **7월 Codex 세션이 11개뿐**(6월의 2%)이다. 7월이 조용한 게 아니라 **로그가 없는 것**이다 —
  7월 항목이 얇은 것을 "사고 없음"으로 읽으면 안 된다.

---

## §2. 절대 불변식 (약화 금지)

1. **발송(제안·InMail·메일)은 절대 자동으로 누르지 않는다.** humansearch는 후보 브리핑
   저장/전달까지만. Send 클릭 = 0회. (SOT26 INV4 / `docs/sot/28-auto-send-policy.json`)
2. **사람이 브라우저를 쓰는 동안 즉시 양보, 손 떼면 자동 재개.** 개입 판정은 **크롬 활성 탭이
   3사 도메인일 때만**(유튜브 등은 개입 아님, 2026-07-20 지시). OS idle 60초 기준
   (`owner_activity.py:37 DEFAULT_OWNER_IDLE_THRESHOLD_SECONDS = 60.0`). **로그인만은 예외** —
   3사 **로그인 화면 자체**를 만질 때만 양보한다(SOT26 INV9, `owner_activity.py:412-431`).
   - **양보가 "영구 중단"이 되면 안 된다.** v5는 사장님이 크롬을 만지면 **작업 목록을 통째로
     버리고 영원히 멈추는** 상태였다(2026-07-15 `d3888f8`: `PAUSE_COOLDOWN 600`→`OWNER_YIELD_
     RESUME 180`, backlog 전량 폐기 제거). **재개를 영구 차단하는 코드는 SOT 위반 — 발견 즉시 삭제.**
3. **보안 챌린지(캡차·2FA·checkpoint·봇차단) 감지 시 즉시 STOP, 재시도 금지.** 같은 URL 재
   네비게이션 루프는 계정 잠금 위험(SOT26 INV2). LinkedIn 세션충돌은 **terminal**(§3-4).
4. **증거 없는 후보는 존재하지 않는다.** 스크린샷+본문+manifest+SHA-256이 저장된 후보만
   채점·등록 대상. `evidence` 테이블 FK로 기계 강제(§5).
   - **이 불변식의 기원**: 06-03 *"링크만 떡하니 남겨뒀냐? 세부 내용 스크래핑하긴 했어??"* —
     수집을 "링크 목록"으로 끝낸 사고. URL만 있는 행은 후보가 아니다.
5. **profile_url은 손으로 옮겨 적지 않는다.** 수확 JSON의 `url`을 문자 그대로. 등록 직전 원본과
   문자열 대조 1회 — 불일치면 게시 중단(`git a4ce8a2`, 규칙 #42 / `humansearch_register.py:3`).
6. **사람이 로그인한 창·탭은 어떤 경우에도 닫지 않는다.** WebSocket 해제와 브라우저 종료를
   구분한다 — 작업 종료 시 **WebSocket만** 끊고 `context.close()`/`browser.close()`/`page.close()`
   /kill/restart는 0회(SKILL.md §0-5). **구조로 막는다**: 순회 드라이버 타입에 `close()`를 아예
   노출하지 않는다. 근거: 08-06 14:19 *"왜 꺼 씨발러마"*, 06-18 *"왜 화면 열었다가 닫아"*(유형 [7]).
7. **사람이 봐야 할 순간엔 창을 실제로 전면화한다.** 배지는 "쓰는 중"을 알릴 뿐. 로그인·캡차·2FA엔
   `Page.bringToFront`로 그 창을 앞으로(SOT26 INV6). 근거: 유형 [3] 5회, §1-B-1.
8. **내 코드는 내가 먼저 깨고 다른 도구가 한 번 더 깬다.** 자기 적대검증 → 독립 2차 검증(codex).
   둘 다 못 깨야 완료(CLAUDE.md 5번). 근거: 06-18 *"strict로 실행하고 codex·claude 동시 적대
   검증했는데 이런 일이"* — **2패스 통과도 충분조건이 아니다. 라이브 1건 실증을 함께 요구**(§7).
9. **완료 보고는 코드(러너)만 쓴다.** 로그인 여부·저장 건수·페이지 수를 모델이 텍스트로
   자기신고하는 경로를 만들지 않는다. 근거: 06-14 *"맨날 넌 거짓말하잖아"*, 08-04 *"200ok
   나한테 보고해"*(유형 [6], HTTP 상태코드로 실증 요구). 강제 장치 = LOGIN_BARRIER(§3-5).

---

## §3. 로그인 아키텍처 — v5가 수백 번 실패하고서야 도달한 것

> 이 절은 새 설계가 아니라 **RC1~RC13(SOT26 근본원인 목록)과 라이브 커밋을 이식**한 것이다.
> v6는 이 13개 함정을 처음부터 피해서 짠다.

### 3-1. 브라우저 접속 — CDP 포트로 통일, launch 전면 금지

- **사람이 이미 로그인해 둔 크롬에 raw CDP 단일탭으로 붙는다. `launch()`/`launch_persistent_
  context()` 계열은 전면 금지.** 근거: 2026-07-19 사장님 지시(§1-A) — launch로 빈 프로필을 띄워
  쿠키가 없어 수백 건 실패. **"launch 계열 호출은 전부 제거."**
- **`connectOverCDP` 전체 attach 금지** — 사장님 크롬 탭이 **161개 실측**(2026-06-25)이면 전체
  enumerate가 hang(ws는 붙는데 `evaluate`에서 멈춤). 목표 탭 1개의 `webSocketDebuggerUrl`에만
  raw WebSocket으로(SOT26 INV5, `cdp_driver.py:9-11`). ws 핸드셰이크는 `suppress_origin=True`
  (Chrome이 Origin 헤더를 403 거부, `raw_cdp.py:470-477`).
- **CDP 포트를 하드코딩하지 않는다.** 2026-07-08 실사고: LinkedIn이 표준 9225가 아니라 **9338**로
  떠 있어 죽은 포트에 붙어 "브라우저 사망" 오진(`06cc0a9`). 살아있는 크롬의 실제 포트를 조회
  (`portal_browsers.sh cdp <채널>`). 명령행 후보가 복수면 `lsof`로 IPv4 LISTEN PID 1개 선택
  (RC10: 9225를 두 PID가 선언한 사고). 라이브 실증: saramin→9223 / jobkorea→9224 / linkedin→9338.
- **CDP 무응답 ≠ 브라우저 사망.** 같은 영속 프로필 크롬이 살아 있으면 재-launch 금지, 기다렸다
  재확인(RC / issue #71 — 재-launch가 탭 무한 증식을 냈다).
- **생존 판정 = target 존재 + `/json/version` 200.** 프로세스만 있고 창 없는 좀비를 살아있다고
  보면 안 된다(§1-B-2, 08-06 사고).
- **창 생성 주체를 구분한다 — 사람은 열어도 되고, 자동화는 0개.** 08-04 08:02 *"같은 포트에서
  창 하나 더 여는건 내가 해왔었던 방식이다."* 는 **사장님이 손으로** 같은 CDP 포트에 창을 하나 더
  여는 것을 말한다(허용 — 세션이 갈리지 않는다). **자동화(§4-1)는 새 탭·새 창을 만들지 않는다** —
  별도 인스턴스로 창을 만들면 세션이 갈린다(§3-2 좌석 충돌). 두 규칙은 주어가 달라 모순이 아니다.

### 3-2. LinkedIn Recruiter = 좌석 1개 = 세션 1개 (v6는 이걸 자료구조에 내장한다)

2026-07-18 실측 정본(`docs/prompts/linkedin-rps-login-session-fix-2026-07-18.md`) — 세 가지가
동시에 얽힌다:

1. **좌석 1개만 허용.** 자동화가 새 탭/새 크롬으로 열면 사장님 세션과 충돌 → *"multiple
   sign-ins. Only one session is allowed."*
2. **메인 크롬(사장님 로그인)은 CDP 디버그 포트가 없다** → 정본 드라이버로 못 붙는다. 확장으로는
   붙지만 **새 탭 = 새 세션** → 1번 충돌 재발.
3. **디버그 크롬(별도 프로필)은 LinkedIn이 Cloudflare로 봇차단**(*"Attention Required"*) —
   **자동화 전용 프로필이 플래그**돼 있어서다.

**유일한 해결 구조**(:20-39, v6 필수 이식): 사장님이 평소 쓰는 **실제 크롬 프로필**을
`--remote-debugging-port=<p> --user-data-dir=<그 프로필>`로 띄운다 → 사람 세션 그대로 CDP 노출 →
Cloudflare(전용 프로필 플래그)와 좌석 1개를 **동시에** 푼다. 별도 빈 프로필로는 둘 다 못 푼다.

**v6 설계**: 함대 전체에서 RPS 세션 보유 호스트를 세어 **0개면 지정 호스트 1곳만 로그인,
1개면 재사용, 2개+면 fail-closed**(미완 PR #238 `linkedin-single-seat-guardian`이 하려던 것).
좌석 락은 atomic mkdir + heartbeat로 **크로스 프로세스/디바이스** 보호(`941c2f1`, `3433584` —
threading.RLock은 같은 프로세스만 보호해 부족했다). 사후에 락을 덧대면 v5처럼 분열한다
(2026-07-15 `8b91d2c`: 좌석 락 분열·stale flag 잔존).

### 3-3. "로그인됐다"를 어떻게 판정하는가 — URL 금지, DOM 마커만

정본: `session_guard.read_auth_observation` (`session_guard.py:611-725`). JS 1회 평가, 판정은
파이썬, 네비게이션·클릭 0회.

- **URL만으로 로그인 단정 금지.** 사람인 함정: `candidate-manage` 직행 시 로딩 미완 순간
  `/tutorial`로 보이고 password input이 뜬다(RC4). 5초 대기 후 GNB 계정명으로 재판정.
- **body 전체가 아니라 header/nav의 "보이는" 컨트롤만** 본다(`:622-633`).
  - 사람인: `account AND (search OR profile_detail) AND 공식URL`. search = `input.search_input`
    +`#career_min`+`#career_max`.
  - 잡코리아: `logout AND account AND (search OR profile_detail) AND 공식URL`.
  - LinkedIn: `공식 /talent/ surface AND recruiter account 컨트롤`.
- **인증 마커는 라이브 DOM fixture로 박제 + 교집합 회귀 테스트.** 2026-07-31 사고: nav DOM이
  바뀌자 **로그인 멀쩡한데 `authenticated=False`**가 되어 **후보 20명 수집 후 전량 중단**
  (`b165f91`). mock 주입 테스트는 드리프트를 못 잡는다. `tests/fixtures/...nav_attrs_2026-07-31.json`
  라이브 속성과 **교집합이 비면 실패**.
- **challenge 판정엔 "살아있는 인증 컨트롤" 동반 요구.** 문구만으로 판정 금지 — 잡코리아 로그인된
  홈은 항상 2FA FAQ 링크를 달아서, 그 문구만 보면 이미 인증된 세션이 `HUMAN_AUTH`로 넘어가
  자동로그인이 정지했다(`b04bb96`, #280).
- **화면별 인증 증거 다형성.** 상세 화면엔 기업 GNB가 없다 → 그 화면의 회원 전용 컨트롤을 증거로
  (`e6fc4f8`: 잡코리아 이력서 상세의 '포지션 제안'·'스크랩' 버튼). **본문 글자만으로는 인정 안 함.**
- **로그아웃 상태에서도 검색·카드 100장은 정상으로 보인다**(잡코리아, 상세만 마스킹) —
  **검색 성공을 로그인 증거로 착각 금지**(2026-07-04 실측). URL 휴리스틱 health 체크도 못 믿는다.

### 3-4. 상태기계 (핵심만) + 셀렉터 드리프트 · 세션충돌

- 상태: `DISCOVER → HUMAN_ACTIVE / AI_ATTACHED → (HUMAN_AUTH | AUTH_CONFLICT | AUTHENTICATED)
  → KEEPALIVE → AUTH_LOST → HANDOFF` (SKILL.md §1).
- **HUMAN_AUTH 중 금지 10개**: navigate/reload/back/click/type/submit/popup_close/close/focus/
  new_page. 허용 3개: read_auth_marker / read_owner_idle / wait. 폴링 최소 5초, **timeout 없음**,
  성공 = fresh 마커 AND owner idle ≥ 15초(SOT26 `human_auth_control`). ⚠️ 이 규칙을 상태기계
  JSON·SKILL·SOT·코드 4곳에 복제하지 말 것(RC와 A-1의 병리) — **코드 한 곳에 두고 문서는 참조만.**
- **셀렉터 드리프트 = 명시 실패, 추측 채움 금지.** 3역할(id/pw/submit) 중 하나라도 못 찾으면
  `drifted=True` 반환 — 안 그러면 조용히 실패한다(`portal_autologin.py:113-117`).
- **기존 로그인 폼 보존.** login-cap에 username/password가 다 있으면 `/uas/login`으로 강제 이동
  금지(RC11: 강제 이동 시 inputs=0, forms=0, buttons=['새로고침'] 연결 오류로 종료).
- **LinkedIn 세션충돌 = terminal `AUTH_CONFLICT`.** 자동로그인·Continue/Confirm 클릭·재시도 0회.
  같은 실행에서 재발해도 2차 인계 없음(`8f299b1`, #156). 단 사장님이 이 기기에서 명시 지시하면
  `--owner-takeover`로 세션충돌은 통과(다른 기기 세션은 LinkedIn 단일좌석이 자동 무효화) — **진짜
  캡차·2FA는 이 플래그와 무관하게 항상 STOP**(SOT26 INV8).
- **보안챌린지 재시도 금지, 네트워크 오류에만 지수 백오프**(최대 3회, base 1.0초). 주석 그대로:
  *"hammering a security challenge is the fastest way to get the account locked"*
  (`portal_recovery.py:118-124`).

### 3-5. LOGIN_BARRIER — 검색 전 문 (모델 자기신고 금지)

**설계 원칙**(`login_barrier.py:5`): 모델이 출력한 "LOGIN_BARRIER=PASS" 문자열은 **신뢰하지
않는다. 디스크의 JSON 영수증만 검증.** 근거: 2026-07-21 진단(`hermes-login-gate-before-search-
skills-2026-07-21.md`) — *"F16: 잡 시작 전에 로그인 검증을 무엇도 부르지 않는다. F17: 사후
검증은 자기신고라 위조 가능하고 검색이 다 끝난 뒤에야 걸린다."* 진짜 구멍은 "login 스킬 미로드"가
아니라 **검색 경로에 로그인을 코드로 강제하는 지점이 없다**는 것이었다.

영수증 검증 항목(`validate_channel_receipt:111-169`): schema_version / 비밀값 키 없음 / `state==
AUTHENTICATED`(HUMAN_AUTH·AUTH_CONFLICT 거부) / channel·**host 일치**(다른 기기 영수증 거부) /
`last_verified_at` 시간대 필수 / 미래 거부 / **1800초 만료** / `owner_activity_detected==False` /
`mutation_count==0` / 증거 3파일 **디스크 실존** / SHA-256 형식.

⚠️ **v6 강화 (미완 PR #240이 하려던 것)**: 현재 main은 증거 파일의 **존재만** 보고 **SHA를 실제로
재계산하지 않는다**(`login_barrier.py:164-168` — `isfile` + 형식검사뿐, `hashlib` 호출 없음,
2026-08-07 확인). 지금은 아무 64자 hex + 빈 파일 3개면 통과한다. **v6는 SHA를 실제 파일에서
재계산해 대조하고, worker가 executor 호출 직전에 디스크를 다시 읽는다(TOCTOU 방지).**

### 3-6. 자격증명 — Keychain 단일 출처

- **런타임 정본 = macOS Keychain `valuehire.portal_credentials`. `.env.local`은 초기 import
  전용**(RC9: 두 소스가 다르면 원인 파악 불가한 silent 실패). `session_guard`가 Keychain을 직접
  읽고 `--agent`만 바꾼다 — env 주입은 에이전트마다 명령이 갈리고 shell 노출 위험(RC12).
- **비밀값은 프로세스 밖으로 안 나간다**: `add_generic_password`는 stdin 전달(`-w` 인자 금지,
  ps 노출 방지, `portal_keychain.py:6-23`). 영수증에 `password|cookie|token|li_at` 키가 있으면
  거부(`login_barrier._contains_secret_key`). 로그 URL에서 query/fragment 제거(`portal_safety`).
- **자격증명 방침은 사장님 지시**: 08-04 *"비번 안바꿀거고 비번은 제거후 .env에 저장해"*(유형 [5]).
  비밀번호 회전을 요구하지 말 것.

---

## §4. 브라우저 드라이버 계약 — 라이브에서 검증된 규칙 (aisearch에서 이식)

> 근거: `apps/aisearch/core/cdp_driver.py`(브랜치 2,305줄), 2026-08-04~05 라이브 실행 커밋.
> **⚠️ 이 수정 전부가 PR #278로 미병합**이고 main cdp_driver(689줄)는 **깨진 셀렉터를 그대로**
> 갖고 있다(§4 말미). v6는 브랜치 코드를 근간으로 삼는다.

**접속·입력**
1. 기존 target 1개의 `webSocketDebuggerUrl`에만 붙는다. 새 탭·새 창 0개(§3-1과 동일 계약).
2. **텍스트 입력은 `Input.insertText`** — JS `value` 대입·문자별 키이벤트·clipboard는 라이브에서
   입력 미반영, clipboard 권한 프롬프트로 `Runtime.evaluate` 행(`live_collect.py:3-8`).
3. **입력 시퀀스를 자동 표식(`__vh_auto_active`)으로 감싼다** — CDP Input은 `isTrusted=true`라
   자동화가 **자기 입력을 사람 입력으로 오인**해 스스로 정지(`cdp_driver.py:26-29`). 유형 [11] 관련.
4. **키워드 검색은 실좌표 CDP 입력.** JS `.click()`·jQuery trigger는 안 먹지만 `Input.
   dispatchMouseEvent`(mousePressed/Released)는 먹는다(2026-07-04 RPS 실측). **Enter 구성은
   요소마다 다르다** — 일반 포털은 char("\r") 포함 3종, **LinkedIn textarea엔 char 제외 2종**
   (char는 개행만 삽입, `cdp_driver.py:756-763`). insertText 직후 Enter는 React 미갱신 → 1.5초
   정착 후 재전송.

**렌더·대기·스크롤**
5. **`readyState=='complete'`를 렌더 완료로 믿지 않는다.** SPA(잡코리아·LinkedIn)가 facet·건수·
   페이지네이션을 나중에 그린다 → 대상 요소가 실제로 보일 때까지 유계 재시도(10회×1.5초). 무한
   대기 금지(`cdp_driver.py:194-204`).
6. **백그라운드 탭 = 카드 0 렌더.** 수집 직전 `Page.bringToFront` + `Emulation.setFocusEmulation
   Enabled` 필수 — 안 하면 "결과 1.8K+인데 카드 0개" 오진(2026-08-05 `0b80e15`, 2026-07-02 재확인).
7. **가상 스크롤 목록**(RPS 한 페이지 25명): `bringToFront` → 최상단 복원 → occluded 좌표에
   `Input.synthesizeScrollGesture`(±700) 반복(최대 40스텝×1초), **occluded 0 + unique≥itemCount
   일 때만 완료**, 못 채우면 fail-closed(`cdp_driver.py:1841-1925`). 짧은 grab과 스크롤을 교차 —
   수십 회 scroll을 JS 한 호출에 몰면 렌더러 프리즈.
8. **상세 완료 판정은 길이만으로 하지 않는다.** 내비 뼈대 1040자를 완료로 오판 → 임계 2000자 +
   식별자 일치 + 필수항목 + 로딩 인디케이터 부재 전부 요구(`cdp_driver.py:207-313`).
9. **상세 열람이 목록 상태를 깨지 않게** — 숨김 iframe(`left:-10000px`) 우선, 이탈했으면
   `history.back()` 후 URL 일치 증명(Recruiter SPA 히스토리 손실로 페이지네이션 붕괴,
   `cdp_driver.py:928-975`).

**셀렉터·필터**
10. **CSS 속성 셀렉터 `[attr*=value]`는 대소문자 구분.** 잡코리아 코드가 `'View'`(대문자)인데
    실제 href는 소문자 `resume/view` → **상세링크 항상 0건**. **합성 fixture 테스트는 이걸 못 잡았다**
    → 라이브 캡처 HTML로 검증(`cdp_driver.py:134-145`). 셀렉터는 `data-test-*` 우선 + 복수 폴백.
11. **새 검색 전에 이전 검색의 필터 칩을 반드시 지운다**(`reset_filters`를 입력 전에). 칩이 남으면
    새 키워드를 넣어도 **같은 71명이 그대로**(PR #278, 2026-08-04). ⚠️ **코드 근거는 확실하나
    사장님 발화 근거는 없다**(§1-C) — 규칙으로 싣되 출처를 코드로 명시.
12. **입력값은 필터 적용의 증거가 아니다.** 화면의 **활성 조건 칩만** 증거로 인정하고, 요청 필터
    전부를 증명 못 하면 수집 차단(잡코리아 미적용 후보 유입, `cdp_driver.py:589-624`).
13. **typeahead 필터는 Enter로 끝내지 않는다** — 제안 렌더 대기 → 정확 일치 옵션 클릭 → 활성 칩
    존재로 증명(LinkedIn 지역: 1.8K+ → 87건, `cdp_driver.py:1607-1667`). 좌표 클릭 무시 시 DOM
    `.click()` 폴백.

**봇 회피·안전**
14. **간격은 고정하지 않고 결정론 지터로 흩는다. 값은 SOT 한 곳에서만 읽는다.** 고정 간격이 봇
    신호(`harvest_policy.py:82-100`, docstring: *"재현성을 위해 결정론으로 만든다"*). 근거: 유형
    [10] 봇 인식 3회, 06-02 *"너무 빨라"*, 06-23 *"봇이 아닌 것처럼."* ⚠️ **진짜 랜덤으로 바꾸면
    재현성(같은 run_id → 같은 타이밍 → 사고 재현)을 잃는다** — 바꾸려면 그 대가를 문서에 명시.
15. **같은 URL을 연속 두 번 열지 않는다**(후보 1명이 앵커 2개로 중복 노출 → 71명을 142번 열람한
    사고, `cdp_driver.py:1926-1937`). 실패 후 같은 네비게이션 반복 금지(SOT27 `no_bot_retry`).
16. **순회 시작 전 라이브 프리플라이트 fail-closed** — 로그인·세션충돌·캡차·결과렌더 4개 규칙
    전부 참일 때만 수집 코드를 **실행조차 한다**. 실패 시 즉시 STOP, 같은 URL 재네비게이션 금지
    (`docs/sot/27-humansearch-browsing-preflight.json`). 기원: 2026-06-30 뤼튼 순회에서 세션
    만료로 0건이 렌더됐는데 "0명"을 조용히 뱉고 반복(유형 [13]). **raw CDP와 확장을 같은 탭에
    동시 attach 금지**(렌더 손상).
17. **배지는 주입만으로 끝내지 말고 실제 렌더를 증명한다** — `z-index:2147483647` + 전 속성
    `!important` + `pointer-events:none`(클릭 방해 안 함) + **스크린샷 픽셀 색 + 히트테스트**로
    증명, 실패 시 fail-closed(컴포지터·조상 숨김으로 안 보이던 사고, `raw_cdp.py:313-355`).
18. **긴 순회는 체크포인트 저널로 재개.** JSONL 파싱은 **LF 바이트로만** 자른다 — `splitlines()`가
    U+2028/U+2029 든 Recruiter HTML을 잘라 정상 파일을 손상으로 오판(`live_portal_run.py:265-268`).

**⚠️ main과 브랜치 셀렉터 차이 (v6가 베끼면 안 되는 것)**

| 항목 | main (깨짐) | 브랜치 (라이브 검증) |
|---|---|---|
| jobkorea 상세링크 | `[href*='/Corp/Person/'][href*='View']` — 대소문자 불일치로 **항상 0건** | `a[href*='resume/view']` |
| linkedin 다음페이지 | `button[aria-label='Next']` — **엉뚱한 캐러셀** | `a[data-test-pagination-next]` |
| jobkorea 다음페이지 | `div.tplPagination a.next` — **첫 100건만** | `button.btn--next.btnNext:not(...)` |
| RPS 결과건수 | 3종 모두 **현재 화면에 없음** | `[data-test-profile-list-num-custom]` |

main엔 `reset_filters`·`bringToFront`·가상스크롤이 **하나도 없다**(grep 0건). **humansearch 러너
자체도** 필터 리셋·bringToFront가 없고 가상 스크롤이 `scrollBy(0,900)` 8회 고정이라 aisearch보다
뒤떨어진다(`humansearch_cdp_run.py:273-284`). v6는 이 격차를 처음부터 없앤 단일 드라이버로 짠다.

> ⚠️ **이식 근거의 소재 (2026-08-07 적대검증에서 확정)**: 위 "브랜치 검증" 값 2,305줄은 로컬
> worktree `cce9280`에만 있다. **원격 `origin/task/aisearch-live-portal-wire`(=PR #278 head
> `f02c537`)는 838줄뿐이라 이 라이브 수정을 담고 있지 않다.** v6가 셀렉터·필터리셋·스크롤 로직을
> 이식하려면, 먼저 이 컴퓨터의 로컬 worktree를 push하거나 코드를 v6로 직접 복사해야 한다 —
> 문서만 보고 `origin`에서 받으면 깨진 838줄을 가져온다. **이 사실 자체가 v5 병리의 극단 사례다:
> 라이브에서 실증된 코드가 3일간 로컬에만 있고 push조차 안 됐다.**

---

## §5. SQLite 스키마 — 유일한 저장 정본

> v5는 저장이 3벌(로컬 sqlite + results.json + Supabase)로 흩어져 동기화 누락이 "저장했는데
> 안 보인다" 사고를 냈다. **v6는 로컬 SQLite 1개 파일이 유일한 정본.** 클라우드가 필요하면
> SQLite를 읽어 내보내는 읽기 전용 파생 작업으로(반대 방향 금지). Supabase 스키마·동기화 코드는
> 버린다(`humansearch_supabase_sync.py`·`humansearch_supabase_backfill.py`는 서로 다른 폴더에 있음).

WAL 모드 + `fcntl.flock(LOCK_EX)` 단일 쓰기자. 멱등 upsert(`INSERT ... ON CONFLICT DO UPDATE`)만
쓰고 손으로 "있으면 skip" 분기를 흩지 않는다(v5 aisearch 락 결함 7회 재발 교훈).

```sql
PRAGMA journal_mode = WAL;  PRAGMA foreign_keys = ON;

CREATE TABLE runs (
  id TEXT PRIMARY KEY, channel TEXT NOT NULL, position_ref TEXT NOT NULL,
  search_url TEXT NOT NULL, started_at TEXT NOT NULL, finished_at TEXT,
  status TEXT NOT NULL,          -- running|completed|aborted|preflight_failed
  abort_reason TEXT,             -- 중도 정지 시 사유 필수(§2-2, 조용한 종료 금지)
  pages_visited INTEGER NOT NULL DEFAULT 0);

CREATE TABLE candidates (
  id INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT NOT NULL REFERENCES runs(id),
  channel TEXT NOT NULL, position_ref TEXT NOT NULL,
  profile_url TEXT NOT NULL,     -- canonical (query 제거)
  navigation_url TEXT,           -- query 포함 원본 href, 재방문 전용(LinkedIn bare url ≠ 이동용)
  name TEXT, education_json TEXT, employment_history_json TEXT, skills_json TEXT,
  summary TEXT, hard_exclude_reason TEXT, captured_at TEXT NOT NULL,
  UNIQUE(channel, position_ref, profile_url));   -- 후보 1명 = 1행, 3조각

CREATE TABLE evidence (
  id INTEGER PRIMARY KEY AUTOINCREMENT, candidate_id INTEGER NOT NULL REFERENCES candidates(id),
  page_type TEXT NOT NULL,       -- 'list' | 'detail'
  screenshot_path TEXT NOT NULL, text_path TEXT NOT NULL, manifest_path TEXT NOT NULL,
  screenshot_sha256 TEXT NOT NULL, text_sha256 TEXT NOT NULL, captured_at TEXT NOT NULL,
  UNIQUE(candidate_id, page_type));   -- 목록 캡처가 상세 캡처를 덮어쓰지 않게 4번째 조각

CREATE TABLE scores (
  id INTEGER PRIMARY KEY AUTOINCREMENT, candidate_id INTEGER NOT NULL REFERENCES candidates(id),
  d1 INTEGER,d2 INTEGER,d3 INTEGER,d4 INTEGER,d5 INTEGER,d6 INTEGER,d7 INTEGER,d8 INTEGER,
  sub_reasons_json TEXT NOT NULL,     -- LLM 근거(없으면 등록 거부, §6)
  total INTEGER NOT NULL,             -- 코드 계산, LLM 산출 금지
  tier TEXT NOT NULL, scored_at TEXT NOT NULL);   -- strong(85+)|pass(70-84)|reject(<70)

CREATE TABLE registrations (
  id INTEGER PRIMARY KEY AUTOINCREMENT, candidate_id INTEGER NOT NULL REFERENCES candidates(id),
  channel_target TEXT NOT NULL,       -- 'discord'|'clickup' 선택적 어댑터
  external_ref TEXT, registered_at TEXT NOT NULL,
  UNIQUE(candidate_id, channel_target));

CREATE TABLE run_log (   -- 완료 영수증은 코드만 쓴다(§2-9)
  id INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT NOT NULL REFERENCES runs(id),
  ts TEXT NOT NULL, event TEXT NOT NULL,   -- preflight_fail|hard_exclude|evidence_saved|
                                            -- scored|eligible|registered|human_intervention|
                                            -- captcha_stop|session_conflict_stop
  payload_json TEXT);
```

- **"전부 저장" 원칙**: 열람한 프로필은 점수·통과와 무관하게 전부 `candidates`에.
  `registrations`에만 게이트 통과분.
- **멱등키 4조각** = 채널 + 포지션 + 프로필URL + 화면종류. 후보 테이블은 앞 3조각(1명=1행),
  `evidence`는 `page_type`을 더한 4조각 — v6 부검이 *"조각 누락이 두 번 별도 사고로 터졌다"*
  (`~/Desktop/v6-clean-rebuild-goal-prompt-2026-08-04.md:231`).
- **등록은 선택적 어댑터**(`RegistrationAdapter.register(candidate)->external_ref`). 어댑터를 전부
  꺼도 파이프라인이 완결돼야 한다 — v5는 등록을 필수 단계로 하드코딩해 외부 SaaS 장애가 곧 서치
  실패였다.

---

## §6. 채점·게이트·설정 (압축)

**D1~D8 채점** (가중치 `docs/sot/24-position-jd-sot.json` `stage_4_deterministic_total.weights`):
D1 직무핵심역량 27 · D3 레벨정합 14 · D7 성사현실성 14 · D2 도메인 10 · D6 티어델타 10 ·
D4 재직안정성 9 · D8 학벌 9 · D5 성과구체성 7 (합 100).

- **LLM은 소점수 + 근거만. 총점·등급은 코드가 계산**(`matching_score_contract` 계승). LLM이 총점을
  내거나 문장력으로 채점하면 무효.
- **채점 경로는 하나만.** v5는 `evaluation_client` 있으면 D1~D8, 없으면 **레거시 4축으로 조용히
  폴백**했다(`humansearch_cdp_run.py:770-783`). **v6는 폴백하지 말고 실패**(fail-closed) — 조용한
  폴백은 "왜 점수가 다르지?"의 영구 원인.
- **합격선 70** — 게이트 캡과 한 세트: 필수요건 `fail`→최대 49(자동 탈락), `uncertain` 2개+→최대
  69. **즉 70점은 "필수요건이 전부 확인된 사람만 넘는 선."** 리터럴로 흩지 말고 설정 1곳에서 읽고,
  **러너가 그 파일에서 읽었다를 테스트로 단언**(v5는 설정에 70이 있는데 러너가 안 읽고 리터럴로
  썼다, `humansearch.config.json:57` vs `humansearch_cdp_run.py:677`).
  - ⚠️ 문턱은 파이프라인마다 다르다(의도된 차이): humansearch 70 / aisearch 등록 60
    (`recorders.py:31`) / 자동발송 85(`28-auto-send-policy.json`). 섞지 말 것.

**하드제외**(`hard_exclude_reason`): 프리랜서, 12개월 미만 단기이직 2회+, 전문대(사람인·잡코리아만
학교 컷 — **링크드인은 학교 하드컷 없음**). 세계 명문대는 학력 만점(2026-06-26). 경력은 **회사
단위 groupby** 후 `job_changes = unique_companies - 1`(승진을 이직으로 세지 않는다 — 최우수
후보가 단기이직 규칙에 걸려 잘린 라이브 사고, `build_company_tenures`).

**열람 순서** (2026-08-07 사장님 확정, 점수와 별개 층 — 여기서 밀려도 버리지 않는다):
인서울+OTW → 인서울+Non-OTW(현 회사 2년+) → 그 외 학교+OTW → 그 외+Non-OTW(2년+).
**유일한 컷 = Non-OTW & 현 회사 24개월 미만**(버리지 않고 `triage_deferred` 표시, 재열람 가능).
근거: 08-07 *"인서울 대학교 위주로 보고 나중에 나머지 … open to work 위주. Non Open to work
후보자는 현 회사 재직 2년 이상."* "인서울"은 계약 데이터로(코드 하드코딩 금지).

**단일 게이트 함수** `eligible(candidate)` 하나만: 점수 ≥ 합격선 AND profile_url 유효(빈 값·
내부 공백·상대경로·`javascript:void`·비-http 거부). v5는 이 경계가 매처·등록기·러너 3곳에 따로
있어 각각 뚫렸다 — v6는 **경계 함수 1개**, 등록 경로가 늘어도 전부 이걸 통과한 결과만 받는다.

**설정** (`config/humansearch.json`, 값 변경은 이 파일 1곳, 코드 리터럴 재정의는 테스트가 거부):

```jsonc
{ "score_gate": {"register_min":70,"strong_min":85},          // gate_caps(fail=49/uncertain2+=69)와 한 세트
  "traversal": {"min_pages":20,"max_pages_per_keyword":20,      // 한 키워드당 하한=상한 20(봇 회피·무한순회 방지). 더 보려면 키워드 교체
                "stop_early":false,                            // 멈추면 abort_reason 필수(조용한 종료 금지)
                "click_order_within_page":"random",            // 페이지 안 카드 순서만 무작위(봇 회피)
                "page_order":"sequential","continue_with_new_keywords":true},
  "triage_order":[{"school":"in_seoul","otw":true},{"school":"in_seoul","otw":false,"min_current_tenure_months":24},
                  {"school":"other","otw":true},{"school":"other","otw":false,"min_current_tenure_months":24}],
  "pacing": {"linkedin_keyword_seconds":[20,60],"linkedin_profile_seconds":[2,5],
             "saramin_jobkorea_card_seconds":[3,8]},           // 결정론 지터로 흩음(§4-14)
  "hard_exclude": {"short_tenure_months":12,"short_tenure_count":2,"school_cut_channels":["saramin","jobkorea"]},
  "registration_adapters": ["clickup","discord"],
  "adversarial_verification": {"second_pass":"always"},
  "login": {"connect":"cdp_existing_profile_only","launch_forbidden":true,   // §3-1
            "credential_source":"macos_keychain","env_local":"import_only"} }
```

**순회량 (2026-08-07 사장님 확정)**: *"20 페이지까지는 해야하고, 20페이지 안에서는 랜덤으로
클릭"* — 20은 **하한**(결과 있으면 채운다), 다 본 뒤 키워드 바꿔 계속, 랜덤은 **같은 열람 순위
그룹 안 카드 클릭 순서**만. 중도 이탈 금지(유형 [1] 9회, 08-04 *"페이지네이션 중간에서 멈추는
일은 절대 금물"*). v5 aisearch는 순차 루프에 결정론 지터라 이 지시가 아직 배선 안 됨 —
v6에서 배선하고 `min_pages`로 이름 지어 MAX_PAGES(절대 상한)와 의미를 구분한다.

---

## §7. 하니스 — v6도 게이트를 건너뛰지 않는다

| 게이트 | 내용 |
|---|---|
| 0 | 미해결 RED 없음 + 깨끗한 컨텍스트 (v6는 RED 0에서 시작) |
| 0.5 | **과거 지시 회수** — 이 문서·SKILL.md·lessons-learned부터 (지금 이 문서가 그 결과) |
| 1 | 이슈 + EARS 인수 기준 1개 + 계약 스펙(입출력 JSON) |
| 2 | worktree에서 **RED 먼저**, main 직접 수정 금지 |
| 3 | RED→GREEN 최소 변경 |
| 4a | `verify.sh`(pytest 전체) exit 0 |
| 4b | **2패스 적대검증**: 자기 반증(빈 값·경계·중복·동시성·막힌 사이트) + 독립 2차(codex). 둘 다 못 깨야 통과 |
| 5 | push → PR → **CI 초록 + merge 전까지 "완료" 아님** |
| 6 | merge 후 worktree 정리 |

- **마커/셀렉터 테스트에 mock 주입 금지** — 라이브 DOM fixture 교집합만(§3-3, 2026-07-31 후보 20명
  유실). 대소문자 불일치도 합성 fixture는 못 잡았다(§4-10).
- **라이브 1건 실증 없이 완료 없음.** "테스트 N개 통과"는 완료 근거가 아니다 — 06-18 *"strict로
  codex·claude 동시 적대검증했는데 이런 일이"*(§2-8). 각 기능은 실채널 1건의 `run_log` 영수증 필수.
- **완료 = merge된 SHA.** PR 열기는 완료가 아니다(문서 첫 줄, §7-말미 v5 병리).

---

## §8. v6가 처음부터 넣어야 할 것 — 미완 PR이 하려던 것 (요약)

v5는 아래를 사후에 덧대다 분열하거나(§3-2 좌석 락), stacked PR로 쌓고 미병합했다. **v6는 처음부터
자료구조·계약에 넣는다.**

1. **좌석(seat)을 자료구조에 내장** — LinkedIn RPS = 계정당 세션 1개, "어느 호스트가 갖고 있나"
   조회 가능(미완 PR #238).
2. **로그인 에피소드를 1급 객체로** — 에피소드당 제출 1회·표면화 1회·알림 1회(중복 알림은 SOT2
   "봇처럼 굴지 않는다" 위배, 미완 PR #234·#236).
3. **영수증 무결성 = 형식이 아니라 내용** — SHA 재계산 + 실행 직전 재읽기(§3-5, 미완 PR #240).
4. **lease는 own-token만 반납, 재개는 DISCOVER부터**(미완 PR #244) — 남의 토큰 반납이 락 분열 재발.
5. **cross-agent mutation guard를 처음에**(미완 PR #228) — Claude·Codex·Hermes 동시 조작 방지.
6. **한 정책 = 한 판정 함수.** 자동로그인 금지 정책이 6계층(DB CHECK·이벤트 가드·DoD 감사·
   프리플라이트·복구·자격증명 키)에 복제돼 **되돌릴 수 없게** 됐다(2026-06-09 사고, 해제에 13곳
   필요). 정책은 한 곳에서 판정하고 나머지는 호출.
7. **필터 리셋 + bringToFront + 가상 스크롤 완료 증명을 humansearch 러너에 처음부터** — v5는
   aisearch에만 있고 humansearch엔 없다(§4 말미).

---

## §9. 구현 순서 (각 Phase는 라이브 인수 포함)

- **Phase 0 · 골격**: SQLite 스키마(§5) + 설정(§6) + 하니스 배선. **§1 사고 14유형과 §3~§4 규칙을
  코드 주석이 아니라 테스트 케이스로 고정**(회사단위 groupby 회귀, profile_url 손입력 차단, 증거
  없는 후보 등록 차단, 대소문자 셀렉터 라이브 fixture). 인수: 무결성 제약 위반 시도가 전부 거부됨.
- **Phase 1 · 로그인**: §3 전체. CDP 단일탭 접속 + 포트 자동탐지 + DOM 마커 판정 + LOGIN_BARRIER +
  Keychain. 인수: 실채널 1개 라이브 로그인 후 영수증(SHA 재계산 포함) 검증 통과, 미로그인 시 큐
  정지 + 알림 1건, 세션충돌 terminal 처리.
- **Phase 2 · 순회+증거**: §4 + §2-4. fail-closed 프리플라이트 → 순회 → 증거 저장. 인수: 라이브
  1건 순회로 `candidates`+`evidence` N건, 증거 없는 행이 다음 단계로 못 넘어감을 강제 테스트.
- **Phase 3 · 채점+게이트**: §6. 인수: 합격선 미달이 `registrations`에 도달 안 함(호출 카운트),
  합격자 `total`이 코드 계산과 일치, 레거시 폴백이 실패로 처리됨.
- **Phase 4 · 어댑터+InMail 문구**: 인수: 어댑터 전부 끈 상태에서 Phase 0~3 그대로 동작. InMail
  precheck(이름 일치·글자수·금지워딩)는 불일치 입력에 STOP.

---

## §10. 근거 부록 — 상수·URL·재현

```
# 로그인/인재풀 URL (portal_login.py:28-30)
사람인   pool: /zf_user/memcom/talent-pool/main/search   login: /zf_user/auth?ut=c (기업회원)
잡코리아 pool: /Corp/Person/Find (대문자 필수)            login: 기업회원 탭 먼저
LinkedIn pool: /talent/hire/<id>/discover/recruiterSearch (검색) — /talent/search는 다른 제품(§4)

# 셀렉터 정답 (브랜치 검증) — main은 깨져 있으니 베끼지 말 것(§4 표)
상세링크: linkedin a[data-test-link-to-profile-link] / saramin div.talent_list_item .summary_info a / jobkorea a[href*='resume/view']
다음페이지: linkedin a[data-test-pagination-next] / jobkorea button.btn--next.btnNext:not([disabled])

# 시간 상수
owner idle 양보 60초 / HUMAN_AUTH 성공 후 정숙 15초, 폴링 최소 5초, timeout 없음
영수증 유효 1800초 / keepalive 900/900/1800초 / 재로그인 최대 3회 base 1.0초
SPA 렌더 대기 10회×1.5초 / 상세 임계 2000자 / 가상스크롤 최대 40스텝

# 디버그 포트 (조회하고 쓸 것 — 하드코딩 금지. 실제로 9338이었던 적 있음)
사람인 9223 · 잡코리아 9224 · 링크드인 9225(실사고 9338) · 사장님 메인 9222(디버그 포트 없음)

# 락·영수증·자격증명
lease: ~/.valuehire/browser_locks/login-<site>.lock (atomic mkdir)
receipt: ~/.valuehire/login_receipts/<channel>.json (VH_LOGIN_RECEIPT_DIR 우선)
keychain: service=valuehire.portal_credentials (.env.local은 import 전용)

# 차단 신호 (portal_login.py:116-128)
보안문자·2단계·인증번호·checkpoint·authwall·captcha = 항상 STOP
"multiple sign-ins"·"only one session"·enterprise-authentication = 세션충돌(owner_takeover로만 통과)

# 재현 (전수 조사 원본)
사장님 발화: 영속본 .harness/humansearch-history/codex_user_msgs_human_only.jsonl (4,166줄, 커밋됨)
             비영속 scratchpad/mine/ (Claude 3,840건 — v6 넘기기 전 .harness로 옮겨 커밋할 것)
로그인 코드 역사: docs/sot/26-portal-login-spec.json root_cause_catalog(RC1~13)
브라우저 코드 역사: 로컬 worktree cce9280:apps/aisearch/core/cdp_driver.py (2,305줄 — 원격엔 없음)
미병합/미push 확인:
  git merge-base --is-ancestor ef6696c main → NO ; 7e917b3 main → NO   (로그인 하드닝)
  git show origin/task/aisearch-live-portal-wire:apps/aisearch/core/cdp_driver.py | wc -l → 838
  git show cce9280:apps/aisearch/core/cdp_driver.py | wc -l → 2305   (라이브 수정, 로컬 전용)
  gh pr view 278 --json headRefOid → f02c537 (=838줄, OPEN)
```

**v6로 옮길 때**: §2 불변식 → v6 CLAUDE.md + 계약 테스트. §5 스키마 → 마이그레이션 1개.
§6 설정 → `config/humansearch.json`(리터럴 재정의는 테스트가 거부). **§1·§3·§4의 사고들 →
테스트 케이스로 번역**(문서에만 있으면 또 잊는다). 이 문서의 근거 방법(§10 재현)은 v5에 남긴다.

---

## §11. 적대 검증 로그 (2026-08-07) — 이 문서는 두 번 깨졌다

> CLAUDE.md 5번 규칙. 이 문서도 자기 반증(V2 자기공격) + 독립 2차 검증(codex, V1)을 거쳤고,
> **codex가 FAIL 판정과 함께 결함 6건을 냈다. 6건 전부 재현해 수용하고 본문을 고쳤다.**
> 판정 원본: `scratchpad/codex-verdict.md`. 아래는 재현 명령과 반영 결과다.

| # | codex 결함 | 내 재현 | 반영 |
|---|---|---|---|
| 1 (major) | 발화 8,006 vs 2,006 모수가 문서 안에서 어긋남 + `scratchpad/mine/`이 재현 불가 | 두 숫자는 다른 단계값(8,006=전체 훑음 / 2,006=사람 발화)인데 구분 없이 인용. `scratchpad/mine/`은 세션 임시폴더라 저장소에서 안 보임(`test -d` 실패 재현). 영속본은 `.harness/…codex_user_msgs_human_only.jsonl`(4,166줄) | 서두·§10에 두 숫자 구분 + 영속/비영속 경로 명시, 비영속본 커밋 권고 |
| 2 (major) | "원문 그대로"인데 축약·조사 변경(유형 9·11·13) | 정확일치 grep 0건 재현. §1 표는 집계 요약본이었음. 유형 13 "0건"은 사장님이 붙여넣은 Discord 출력(직접 발화 아님) | 표 헤더 "원문 그대로"→"요약 발췌", 유형 13 출처를 Discord 붙여넣기로 표기 |
| 3 (major) | 이식 근거 2,305줄이 고정 참조 없음 | **재현으로 더 심각한 사실 확인**: 원격/PR #278 head `f02c537`=838줄, 라이브 수정 2,305줄은 로컬 `cce9280`에만 있고 push 안 됨 | 서두·§4말미·§8-7에 "로컬 전용, push/복사 필요" 명시 — 병리 사례로 강화 |
| 4 (major) | 실행 입력 계약 누락, 현 러너는 포지션 상수 하드코딩 | `humansearch_cdp_run.py:15 POSITION=뤼튼 하드코딩`, CLI `<max_profiles> <start> <target_id>`만 재현 | §0에 `RunRequest(channel,position_ref,search_url,target_id,jd)` 입력 계약 추가 |
| 5 (minor) | 창 생성 규칙 내부 충돌(167 "창 하나 더" vs 274 "0개") | 주어가 다름(사람 수동 vs 자동화) — 문서가 구분 안 함 | §3-1에 "사람은 허용, 자동화 0개" 명시 |
| 6 (minor) | "scope-out이 재발의 구조적 원인" 인과 단정 과함 | 현 러너가 이미 로그인 프리플라이트 호출(`:41-56·868`) 재현 | §0에서 "해석 — 인과 단정 아님"으로 낮춤 |

**codex가 놓치거나 과장한 것(양방향 의심)**: ① 결함 1에서 codex는 데이터를 "재현 불가"라 했으나,
데이터 자체는 세션 임시폴더에 **실재**한다(내가 열람) — 문제는 "없음"이 아니라 "경로 비영속"이다.
② PR #278을 codex는 네트워크 실패로 확인 못 했으나, 나는 `gh pr view 278`로 OPEN + head
`f02c537`을 확인해 오히려 결함 3을 더 강하게 뒷받침했다. **두 검증자가 서로 다른 접근으로 봐서
합쳐야 전체가 나왔다** — codex는 git 로컬/원격 불일치를, 나는 GitHub PR 상태를 각각 잡았다.

**최종 상태**: 6건 전부 반영 완료. 이 문서는 "완성"이되, §4 이식 근거가 **로컬 전용**이라는
한계가 남아 있다 — v6 착수 전 그 코드를 push하거나 복사하는 것이 유일한 잔여 작업이다(§8-7).

---
