# HumanSearch 여정 착수 프롬프트 v7 — 2026-09-08

> 이력: v1 Codex FAIL(10건) → v2 → v3(사장님 결정 ⑦⑧⑨) → v4(결정 ⑩⑪) → **v4 에 humanreview REQUEST_CHANGES(5건) + Codex FAIL(높음 6건·중간 6건)** → v5 → v6(결정 ⑪⑫·카드 기본값) → **v6 Codex FAIL(해소 10·부분 6·미해소 1 + 신규)** → v7. 판정 원문: `.claude/private-reviews/codex-hs-kickoff-verdict-2026-09-07.md`(v1), `humanreview-hs-kickoff-v4-2026-09-08.md`, `codex-hs-kickoff-v4-verdict-2026-09-08.md`, `codex-hs-kickoff-v6-verdict-2026-09-08.md`. 고친 것은 §9 에 표로.

**용어 풀이(이 문서에서 쓰는 말)**
- **WU(작업 단위)** = PR 하나로 끝나는 작업 한 덩어리. 인수 기준(무엇이 참이면 끝인가) 1개.
- **워크트리** = 작업 단위마다 따로 파는 작업 폴더(`worktrees/<이름>/`). 서로 안 섞이게.
- **리스(lease, 사용권)** = "이 채널 브라우저를 지금 누가 쓰는지" 적어 두는 표. 장부(SQLite)에 산다. **RPS 계정은 1석**이라 계정 보호용이고, **사람인은 여러 브라우저 동시 사용 가능**(사장님 확인)이라 "같은 후보를 두 곳에서 동시에 보지 않기" 용이다. **잡코리아도 여러 브라우저 동시 사용 가능**(사장님 확인 09-08). 1석은 RPS 뿐.
- **D1** = 브라우저에 붙는 부품(포트 찾기, 탭 1개 고르기, 사용권, 사람 개입 감지, 멈춤). **C1** = 실제 화면을 저장하는 규칙(암호화·보존·개인정보). **G3** = 포털 주소·셀렉터 같은 상수를 코드 밖 계약 파일에만 두게 하는 검사.
- **RED/GREEN** = 실패하는 시험을 먼저 커밋(RED), 통과시키는 최소 구현을 다음에 커밋(GREEN).
- **readback** = "썼다"고 믿지 않고 다시 읽어서 확인하는 것. **영수증** = 실행기가 남긴 실행 흔적 파일.
- **정본 개정 PR** = `docs/sot/`·`contracts/` 를 고치는 PR. 이 저장소는 그런 PR 에 라벨 `weakens-check` 와 결정 기록(L3 goal)을 요구한다(P13①, 브라우저 정본 §16).

/strict 로 진행한다. **작업 단위 1개 = 워크트리 1개 = 인수 기준 1개 = PR 1개.** 한 번에 하나만 하고, PR 을 열면 병합을 기다리지 않고 다음 작업 단위를 새 워크트리에서 바로 시작한다(앞 PR 이 필요하면 그 브랜치를 base 로 잡고 PR 본문에 적는다). merge 는 사장님이 한다. 이 문서는 첫 워크트리 안에서 `docs/engineering/goal-prompts/humansearch-journey-kickoff-2026-09-07.md` 로 커밋한다. §0 은 2026-09-07/08 실측이며, 착수 시 HEAD·origin 동기·포트 listener 만 다시 확인한다(P12).

## §0. 현재 사실 (실측 · Codex 두 차례 재현)

**저장소 (`main` = `01495b3` = origin/main, 2026-09-08 재확인)**
- 인재 서치 코드는 `humansearch/src/humansearch/` 최상위 4파일: `__init__.py`(44) · `auth_surface.py`(73, L0 순수 분류기) · `observe.py`(398) + `_cdp.py`(208) = L1. L1 은 `--channel saramin --once` 만 받아 사람인 탭 **하나**를 읽기 전용 CDP 로 1회 관측하고 한 줄 출력하고 끝난다. `admin_weekly_dashboard/` 는 별개 트랙.
- 시험: `cd humansearch && uv run pytest -q` → **211 passed**(2026-09-07 이 세션 실측).
- 완료: G1(PR #9 `b384e47`) · G2(PR #11 `f3a517f`) · L0(`b6aee6a`, PR #26 MERGED) · D0(PR #34 `f7bd9da`) · L1(PR #38 `c59bad7`, #42 `eadab45`).
- **0줄**: 검색어 입력, 결과 순회, 후보 상세 열기, 후보 저장(SQLite 스키마 없음), 채점, 중복 판정, 잡코리아·LinkedIn 계약, Discord 봇·큐·러너, Supabase 내보내기, ClickUp 어댑터, 브라우저 기동·포트 탐지·사용권·멈춤 스위치. `ledger/ bot/ daemon/ adapters/` 없음. 이 문서가 이름 붙인 `scripts/acceptance-hs-<wu>.sh`·`tests/test_*` 는 **전부 아직 없다**(만들 대상).
- 계약 파일은 `contracts/humansearch/saramin-markers.json` 하나(포트 9225, origin `https://hiring.saramin.co.kr`).
- 미병합(2026-09-08 `gh pr list` 실측): **PR #13 OPEN** G3(로컬 57 / origin 56커밋), **PR #54 OPEN** CDP 핸드셰이크 증명(5커밋), **PR #15 OPEN** = head `task/docs-snapshot`, 제목 "docs: HumanSearch 정본·자율 하네스와 기획 산출물 보존" — 문서 스냅샷 PR 이며 그 안에 D0 가 기각한 Active Tab Bridge 계획서가 들어 있다(정본 §13 "OPEN·CONFLICTING 후보 기록"). 브랜치 `task/hs-d1-permit`(2커밋, PR 없음), `task/hs-l1-malformed-url-fix`(3커밋, PR 없음), `task/hs-observe-url-crash`(54커밋, 워크트리 없음).
- **untracked 3건** (`worktrees/resume-evidence-supabase-prompt`): 설계서 2건(`docs/engineering/resume-evidence-supabase-{archive-goal,implementation-prompt}-2026-08-17.md`) + `scripts/experiments/profile-archiver-long-page-benchmark.mjs`. 설계서는 "기존 ValueHire v4 프로필 아카이버를 재사용" 전제(archive-goal:5,13,15) — v6 설계서로 그대로 채택 불가. `.mjs` 는 v4 경로 참조라 비문서 경로에 커밋하면 G1 이 거부.
- 인수 검사 실행기 규약(실측): `scripts/verify/run-acceptance.sh` 는 종료값 0 이어도 출력에 `PASS` 문자열 줄이 1개 이상 없으면 FAIL, `CHECKED:` 줄이 있으면 그 숫자가 1 미만일 때 FAIL. `scripts/acceptance-semantic-mutations.sh` 의 무력화는 **5종: exit-zero · true-only · noop · empty · echo-only**.

**정본 (`docs/sot/`) — 이 프롬프트보다 상위**
- `humansearch-browser-contract.md`: 사람인·잡코리아 = 채널별 비기본 전용 프로필 + 상주 브라우저 + 로컬 진단 포트 + 목표 탭 정확히 1개(§2·§4). LinkedIn Recruiter = 사장님 실제 로그인 프로필을 CDP 로 재사용 + 페이싱(§2-1·§4). **§4 LinkedIn: "후보 상세 저장, 메시지 작성·발송은 이 문서로 허용하지 않는다."** §6 포트·프로필 하드코딩 금지, 매 작업 재발견. §9-5·§11·§14 "자동 재개하지 않는다"(별도 승인 전 NOT_RUN). §12 C1 선행 조건 9개(그중 3 = 실행별 오너 승인, 7 = 채널별 보존기간·삭제·영수증). §15 D1 불변식 8개. **§16 개정 절차 6단계**(새 L3 goal + 결정 카드 / 권한·PII 영향·되돌리기 공개 / 금지 능력 부재·잔여 명령 0 변조 시험 / 대체·역사 문서 갱신 / Claude V1·Codex V2 가 자격증명·전체 프로필·탭 추측·사람 개입·세션 지속성·LinkedIn 범위 6축 공격 / 오너 승인 전 범위 확장 금지). 발송 자동화 금지.
- `humansearch-l0-surface-contract.md`: L0 는 순수 함수, `AUTHENTICATED` 는 실행 종료가 아니다.
- `coding-principles.md` P1~P24 + §1-B 5조. 직접 쓰는 것: P2(인수 기준 = 실행 명령+기대 출력), P4(외부 효과 모듈은 네트워크 차단 레인에서 반드시 FAIL), P5/P15(RED 후 시험 파일 불변), **P8("3사 계정 = 사이트당 1석" — ⑪ 로 개정 대상)**, P9(멱등키+write-ahead+readback), P11(파일 soft 300/hard 600, 함수 soft 60/hard 100, PR 3,000줄 금지, 생성물·마이그레이션·fixture 면제, 예외는 owner·reason·expiry), **P13①(계약·검사 파일 diff 는 라벨 `weakens-check` 없이 머지 불가)**, P17(증거는 만든 자가 못 쓴다), P19(외부 경계 라이브 1건), P20(0건 = FAIL), P22(상수는 `contracts/` 만), **§1-B 5조(개입 신호 이후 호출이 타입상 불가능해야 한다)**.
- `verification-commands.md`: `make` 없음. 게이트 0 = `bash scripts/session-status.sh`(3번째 줄 `RED: N/M` + 뒤 오류 줄까지), 워크트리 = `git worktree add worktrees/<name> -b task/<name>`, 검증 = `bash verify.sh` + CI, 배송 = `git push -u origin task/<name>` + `gh pr create`. **CI 스텝 30개**(2026-09-09 실측; 이름 없는 checkout 스텝 포함. 정본 표도 30 으로 갱신됨). 새 `scripts/acceptance-*.sh` 는 `verify.yml` + 이 표 양쪽.
- 마스터플랜 §2: **D2(Discord) 선행 = G3**, D3 선행 = D1 + L1, D1 = 자동 기동·생존 감시·포트 자동 탐지.

**브라우저 실측 (2026-09-08 재확인, `lsof`)**
- Chrome 전용 프로필 2개 listener: `9223`(잡코리아), `9225`(사람인) — v4 도구가 띄운 것. **v6 는 쓰지 않는다**(되돌리기도 새 프로필). 이 프로세스가 떠 있어도 v6 의 포트 발견은 `browser-policy.json` 의 `expected_engine_marker`(Aside) 로 걸러 Chrome 을 고르지 않는다.
- Aside 실행 중, 진단 포트 없음(`45103` 내장 잠김, `45111` 없음). 2026-08-14 `--remote-debugging-port=45111` 재시작 성공 기록(nightshift:8)은 **과거**. **미실측 ※ 3건**: (a) Aside 를 별도 `--user-data-dir` 로 두 번째 인스턴스 기동, (b) Aside 업데이트 뒤에도 실프로필 진단 포트가 열리는지(Chrome 은 136+ 에서 기본 프로필 포트를 막는다 — Aside 가 같은 정책을 따르는 날 RPS 자동화가 막힌다), (c) Aside·Chrome RPS 동시 접속(사장님 관찰). → 전부 WU-2 의 실증 항목. **재시작·기동은 사장님만 한다.**

**외부 식별자 (착수 시 재확인)** ClickUp workspace `9018789656`, 포지션 리스트 `901814621569`, AI Search 리스트 `901818680208`(후보 = 하위 작업, 커스텀 필드 0), 후보자 보드 `901814621142`. Supabase `profile_archives`(1,386행, 08-17), `sourcing_results`, `pipeline_position_cards`, `pipeline_candidates`; `profile_archives` live RLS NOT_RUN. Discord: v4/v5 는 Hermes(`~/.hermes`)·웹훅 5채널 — v6 미참조, 봇 신설.

**사장님 결정** (08-14) ① 정상 상황 클릭 0회 ② SQLite 정본 → Supabase 파생, 역방향 금지 ③ 자동 발송은 사람인·잡코리아 3단계 실험 전 금지 ④ v1~v5 의존 0 ⑤ 서치 기준 5종 ⑥ RPS 프로젝트+필터 준비 선행. (09-08) ⑦ **자동 재개 한다** ⑧ **본 프로필 무조건 저장, 동의 절차 없음, 똑바로(빠짐없이·암호화·readback)** ⑨ **"멈춰" 하면 1초 안에 멈추는 장치** ⑩ **브라우저는 Aside 만**(3채널) ⑪ **사람인·잡코리아는 여러 브라우저 동시 사용 가능**(잡코리아는 09-08 추가 확인) ⑫ **LinkedIn 후보 상세도 무조건 저장**(정본 §4 개정, WU-11). ⑦⑧⑪⑫ 는 정본 개정이 필요하고, 그 절차는 §2-10 에 고정.

## §1. 사장님 요구 6개 → WU 대응

| # | 요구 | 담당 WU | 덮지 못하는 것(정직 표기) |
|---|---|---|---|
| 1 | 현황 파악 | §0 | 외부 서비스 현재값은 착수 시 재확인 |
| 2 | Aside 로 3채널 | WU-1, WU-3, WU-2(미실측 ※3건 실증 포함), WU-C1a/b, WU-7/10/11 | Aside 인스턴스 기동·재부팅 자동 기동은 사장님 손 → WU-2c(launchd, P6) 로 별도 |
| 3 | ClickUp 포지션 | WU-4 목록·검색·선택 | 포지션 등록(U 트랙) 범위 밖 |
| 4 | Discord 멤버 명령 | WU-5 | G3 선행. 봇 계정 생성은 사장님만 가능(카드 2) |
| 5 | 이어지는 상태·자동 재개 | WU-3 checkpoint, WU-2 재개, WU-8 러너, WU-12 재순회 | 재개는 새 관측+새 번호 뒤에만, 스위치 켜지면 없음 |
| 6 | 레쥬메 SQLite+Supabase | WU-0B 계약, WU-7 무조건 저장, WU-9 내보내기 | 구간 무누락 manifest·원격 해시 대조는 WU-0B 가 AC 로 옮김 |
| — | 서치 기준 5종·채점 | **WU-14 S1**(이 문서 §3 에 정의) | 채점은 후보 증거 수집(WU-7) 뒤 |

## §2. 아키텍처 — 고정하는 것

1. **브라우저는 데이터다.** `contracts/humansearch/browser-policy.json`: 채널별 `{engine, profile_kind, allowed_origins, expected_engine_marker}`. 포트 없음(§6). 런타임이 `DevToolsActivePort`·`/json/version` 으로 매 작업 발견하고 발견 결과를 lease 행에 증거로 남긴다. 드라이버는 `engine` 으로 분기하지 않는다.
2. **배치 = 전부 Aside(⑩)**: 사람인·잡코리아 = Aside 채널별 별도 `--user-data-dir` 전용 인스턴스(§4 충족), RPS = 지금 쓰시는 Aside 실프로필(§2-1). 세 인스턴스 모두 진단 포트, 기동은 사장님. `engine=chrome` 은 되돌리기(WU-7b).
3. **저장 정본** = `humansearch/src/humansearch/ledger/` SQLite. 표: `positions`, `run_queue`, `runs`, `checkpoints`, `leases`(RPS 는 채널당 1행 = 계정 1석; 사람인·잡코리아는 (채널, 브라우저 인스턴스)당 1행 — 여러 인스턴스 동시 허용, TTL, fencing 번호), `candidate_locks`(후보 URL 당 1행 — 같은 후보를 두 인스턴스가 동시에 열지 않기), `candidates`, `evidence`, `contacts`, `export_outbox`, `imported_history`(Supabase 이력 1회 반입 — 중복 판정은 여기서만), `stop_switch`(§2-9). 마이그레이션 코드, N-1 읽기 시험(P7).
4. **지휘** = `bot/` Discord. `/hs search|status|cancel|stop|resume|purge`. 허용 = `contracts/humansearch/discord-allowlist.json` 에 적힌 **밸류커넥트 서버 id + 역할(role) id 1개**. 그 서버의 그 역할을 가진 멤버만 명령 가능, 그 밖은 거부(fail-closed). 사람별 id 목록은 두지 않는다(멤버가 바뀌면 디스코드에서 역할만 주면 됨). 결과는 **명령이 올라온 채널에 답글**로, 정지·오류 알림도 같은 채널. **답글 내용은 후보 수·채널·포지션·후보 프로필 URL 만** — 이름·연락처·이력 본문 0(검사 `acceptance-hs-bot-pii.sh`, WU-5 에 포함). 봇 토큰은 `~/.humansearch/env`(0600) 에만, 저장소·대화에 0회. 봇은 장부 행만 쓴다. 선행 = G3 결정.
5. **러너** = `daemon/`. 큐 → D-SAFE 프리플라이트 → 순회. **자동 재개(⑦)**: 정지 원인 해소를 주기적 **새 관측**(L0 `AUTHENTICATED` + 사람 입력 없음 N초 + 같은 탭 origin)으로 확인 → 새 증가 번호로 사용권 재획득 → 마지막 checkpoint 부터. 비밀번호·캡차는 재개 경로에도 없음.
6. **내보내기** = `adapters/supabase_export.py`. 화이트리스트 밖 exit 1. outbox → upsert → **별도 클라이언트 readback**. 중복 판정 함수의 import 그래프에 supabase 없음(정적 시험).
7. **파일 예산** = P11 전체.
8. **LLM 0.** 채점(WU-14)도 순수 함수(P14).
9. **멈춤 스위치(⑨) — 구조**: `stop_flag` 를 명령 전에 읽는 방식은 **읽기와 전송 사이에 멈춤이 끼어들면 1건이 새어 나간다**(Codex 실측 `sent_after_stop=1`). 그래서 플래그가 아니라 **회수 가능한 전송 핸들**로 만든다. Codex 가 v6 문구로도 새는 스케줄(신호 뒤·close 전 선점, `sent_after_stop=100`)을 만들었으므로 v7 은 직렬화 지점을 못 박는다: ⓐ `send()` 와 `revoke()` 는 **같은 잠금 하나** 안에서만 실행된다(잠금 밖에서 소켓을 만질 수 있는 코드 경로 0 — 소켓 필드는 잠금 객체 안에만 존재) ⓑ `revoke()` 는 잠금 안에서 `shutdown(SHUT_RDWR)` → `close()` → 핸들 `None` 순서로 끝내고 **그 뒤에야** 반환한다 ⓒ `send()` 는 잠금 안에서 핸들이 `None` 이면 `Stopped`, 아니면 그 자리에서 전송한다. 잠금 때문에 "신호는 봤는데 소켓은 아직 열려 있는" 창이 없다 ⓓ 드라이버 상위 계층은 `Transport` 가 아니라 `Grant`(사용권 번호가 박힌 1회용 능력 객체)를 받으며, `Grant.send()` 만 존재하고 `Grant` 는 revoke 시 폐기된다 — 개입 이후 호출할 수 있는 이름 자체가 없어진다(§1-B 5조). 세 경로(ⓐ `/hs stop`, ⓑ `~/.humansearch/STOP` 파일 — 경로는 `contracts/humansearch/runtime-paths.json`, ⓒ 사람 입력 감지) 전부 같은 `revoke()` 하나를 부른다. 멈춤은 사용권을 지우고 checkpoint 를 남긴다. 스위치가 켜져 있으면 자동 재개 없음. **첫 라이브(WU-C1b)부터 라이브 멈춤 1회가 인수 조건.**
10. **정본 개정 PR 규칙(⑦⑧⑪ 공통)**: 같은 PR 에 ⓐ `docs/engineering/humansearch-l3-decision-<주제>-2026-09-08.md`(결정 카드 5줄 + 사장님 지시 날짜) ⓑ 권한·PII 영향·되돌리기 절 ⓒ 금지 능력 부재·잔여 명령 0 변조 시험 ⓓ 대체/역사 문서 표 갱신 ⓔ Claude V1·Codex V2 판정 파일(§16 의 6축 명시) ⓕ PR 라벨 `weakens-check` ⓖ `bash scripts/acceptance-principles-check.sh` 통과. 이 7개 중 하나라도 없으면 그 WU 는 FAIL. 대상: ⑦ → 브라우저 정본 §9-5·§11·§14 (WU-2), ⑧ → §12 조건 3·7 (WU-C1a), ⑪ → `coding-principles.md` P8 문구("RPS 만 1석, 사람인·잡코리아는 작업 중복 방지 lease") + `principles.yaml` (WU-3), ⑫ → §4 LinkedIn "후보 상세 저장 불허" 조항 (WU-11).
11. **증거(P17)**: 이 저장소에는 아직 러너 전용 쓰기 권한 분리가 없다. 그래서 라이브 영수증은 두 겹으로 만든다 — ⓐ 실행기 `scripts/verify/live-receipt.sh` 가 CDP `/json/version` 응답 + 관측 결과 + 시각을 `tee` 로 기록 ⓑ **Codex V2 가 같은 대상을 독립 재관측**(탭 수·origin·상태)해 ⓐ 와 대조. 대조가 없으면 영수증은 `NOT_RUN`. 완전한 권한 분리는 **WU-15 P17 러너 격리**로 만들고, **첫 라이브(C1b) 전에 병합**한다(Codex v6 지적: 라이브가 격리보다 먼저면 P17 위반). WU-15 = 별도 macOS 계정 `hsrunner` + 영수증 디렉터리 그 계정 소유 0755·타 계정 쓰기 불가 + `live-receipt.sh` 는 `sudo -u hsrunner` 로만 실행(구현 에이전트 셸에는 sudo 없음) + 구현 프로세스의 쓰기 시도 → EACCES 시험. 계정 생성은 사장님 1회(절차 5줄, WU-15 착수 시).

## §3. WU 순서와 인수 기준

왜 이 순서인가(쉬운 말): 장부가 있어야 사용권 표를 적을 수 있고, 사용권·탭 고르기·멈춤이 증명돼야 실제 화면에 붙을 수 있고, 저장 규칙이 **병합돼** 있어야 붙은 화면을 저장할 수 있다. 그래서 장부 → 사용권·멈춤 → 저장 규칙(병합) → 첫 라이브 → 후보 1명.

```text
WU-0A 사실·브랜치 처분·정본 표 갱신
 → WU-0B 클린룸 레쥬메 증거 계약
 → G3 병합 또는 대체 결정 (사장님)
 → WU-1 browser-policy + 선택기 (라이브 없음)
 → WU-3 SQLite 정본 + lease + stop_switch  [정본 개정 ⑪]
 → WU-2 D1 중립 증명 + 멈춤 회수 핸들 + 자동 재개  [정본 개정 ⑦]  + Aside ※3건 실증
 → WU-C1a 저장 규칙 계약(코드+시험, 라이브 없음)  [정본 개정 ⑧]  → 병합
 → WU-15 P17 러너 격리 (첫 라이브 전에 — 영수증 위조 불가 상태를 먼저)
 → WU-C1b 첫 라이브: 사람인 탭 1개 읽기 + 라이브 멈춤 1회
 → WU-4 ClickUp (G3 뒤 병행 가능) → WU-5 Discord (G3+WU-3+WU-4 뒤)
 → WU-6 사람인 화면 계약 → WU-7 후보 1명 → WU-8 러너 → WU-9 Supabase
 → WU-7b Chrome 되돌리기 → WU-10 잡코리아 → WU-11 LinkedIn [정본 개정 §4] → WU-12 재순회 → WU-13 ClickUp 보고
 → WU-14 채점 S1 → WU-2c 재부팅 자동 기동(launchd, P6)
```

### 인수 기준 표

**출력 규약(실측한 실행기에 맞춤)**: 모든 `scripts/acceptance-hs-<wu>.sh` 는 판정마다 `PASS: <항목>` 또는 `FAIL: <항목>` 한 줄, 마지막에 `CHECKED: <n>` 한 줄. 종료값 `0/1/2(NOT_RUN)`. `CHECKED` 가 표의 최소치 미만이면 스크립트 스스로 exit 1. 각 스크립트는 `acceptance-semantic-mutations.sh` 의 **5종**(exit-zero·true-only·noop·empty·echo-only)에 걸려야 하고, 그에 더해 각 WU 는 **자기 변이 스크립트 `scripts/acceptance-hs-<wu>-mutations.sh`** 를 가진다 — 제품 구현을 ⓐ 항상-거부 ⓑ 항상-허용 ⓒ 저장 생략 으로 바꾼 세 변이에서 본 검사가 반드시 FAIL 이어야 한다(`CHECKED:` 3 이상). 아래 표의 `CHECKED` 는 **양성+음성 실행 건수**다(변이 수 아님). **명령 형식(표에서 생략한 공통 꼬리)**: 표의 인수 명령 뒤에 항상 ① `bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-<wu>-mutations.sh`(자기 변이 3종, `CHECKED: 3`) ② 정본 개정이 있는 WU 는 `bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-sot-amendment.sh <wu>` 를 실행한다. `acceptance-hs-sot-amendment.sh` 는 7요소를 기계로 센다: L3 goal 파일 존재·결정 카드 5줄 제목, "영향·되돌리기" 절, 변조 스크립트 존재+실행 결과 FAIL, 역사표 diff 1건 이상, 판정 파일 2개(첫 줄 `VERDICT:` + §16 6축 키워드), `gh pr view --json labels` 에 `weakens-check`(오프라인이면 exit 2 NOT_RUN), `bash scripts/acceptance-principles-check.sh` exit 0 → `CHECKED: 7`. `run-acceptance.sh` 는 `PASS` 줄과 `CHECKED:≥1` 만 보므로 **WU 별 최소치는 각 스크립트가 스스로 exit 1 로 지킨다**(래퍼에 기대지 않는다). 모든 pytest 는 `humansearch/` 에서 돈다(루트에 `pyproject.toml` 없음).

| WU | 워크트리 | 인수 명령 (전부 실행 가능해야 한다) | 최소 | 양성·음성 |
|---|---|---|---|---|
| **0A** | `hs-kickoff-ledger` | `bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-kickoff.sh` — 처분표 `docs/engineering/humansearch-branch-disposition-2026-09-07.md` 파싱: 대상 6건(PR #13·#54·#15, 브랜치 3) 각각 `결론=(병합요청\|재작성\|폐기)` + `근거=<file:line 또는 커밋>`; `verification-commands.md` 의 CI 스텝 **수·이름·순서**가 `.github/workflows/verify.yml` 의 `- name:` 과 1:1(이름이 빈 표 행 0); 08-17 설계서 2건이 `docs/engineering/history/` 에 "v4 전제 역사 기록" 머리말과 함께 존재; 이 프롬프트가 `docs/engineering/goal-prompts/` 에 존재; `verify.yml` 의 해당 스텝에 **주석이 아닌** `run:` 줄로 이 스크립트와 자기 변이 스크립트가 있고 그 스텝에 조건·오류무시 지시가 없음; `docs/engineering/humansearch-kickoff-ledger-verdict-*.md` 존재·크기>0·첫 줄 `VERDICT:` (**정정 2026-09-09**: `.claude/private-reviews/` 는 `.gitignore:24` 로 무시되어 CI 러너에 존재하지 않는다 — 거기 두면 이 검사는 CI 에서 영원히 FAIL 이다. 워크트리 청결은 이 스크립트가 검사하지 않는다 — CI 러너에서는 언제나 깨끗해 증거가 되지 못한다) | `CHECKED: 12` | 처분 6 + 스텝 1 + 문서 3 + 배선 1 + 판정 1. (main 의 기존 untracked `admin-weekly-dashboard-…-2026-09-01.md` 는 다른 트랙 — 처분표에 한 줄 기록만, 건드리지 않음) |
| **0B** | `hs-resume-evidence-contract` | `bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-resume-contract.sh` — `docs/sot/humansearch-evidence-contract.md` 의 counter-AC 8개(구간 무누락 manifest·마지막 화면·NULL 구분·회사별 duty·검색 조건 보존·원격 경로 금지·readback·회사 별칭) 각각에 "검사 명령:" 줄; 문서 내 `v4\|Valuehire_v4\|profile-archiver` 0회 | `CHECKED: 9` | 8 + 금지어 1 |
| **1** | `hs-browser-policy` | `cd humansearch && uv run pytest tests/test_browser_policy.py -q` + `bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-policy-literals.sh`(제품 코드 `127.0.0.1`·포트·origin 리터럴 grep) | `>= 12 passed`, `CHECKED: 3`(리터럴 3종 0) | 정상 탭 1개 → 선택 성공 **1**; 0개·2개·origin 밖·engine 미지·필드 누락 → 거부 5; fixture 교체로 로더가 json 을 읽음 증명 |
| **3** | `hs-ledger-lease` | `cd humansearch && uv run pytest tests/test_ledger*.py tests/test_lease*.py tests/test_stop_switch.py -q` + `bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-ledger-migration.sh`(빈 DB → up → 스키마 덤프 diff; N-1 DB 를 현 코드로 열기) + `acceptance-hs-sot-amendment.sh 3`(⑪ P8 개정 7요소) | `>= 24 passed`, `CHECKED: 4` | 큐 삽입 1(양성)·멱등키 2회→1행·만료→expired; lease 동시 2→1성공 1정상종료·낮은 번호 거부·TTL 재획득; checkpoint 저장→재시작 복원; stop_switch set/clear; 실제 `sqlite3` 파일 경로 단언 |
| **2** | `hs-d1-neutral` | `cd humansearch && uv run pytest tests/test_d1_*.py -q` + `bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-d1-neutral.sh`(로컬 정적 서버 + 테스트 전용 임시 Chromium 프로필로 실제 CDP 왕복) + `bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-d1-mutations.sh` + `acceptance-hs-sot-amendment.sh 2`(⑦ §9-5·§11·§14 개정 7요소) + `bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-aside-probe.sh`(사장님이 띄운 Aside 인스턴스 3개의 `/json/version` 응답·profile 구분·RPS 탭 존재 — 못 띄우면 exit 2) | `>= 30 passed`, `CHECKED: 22`(불변식 8×양성1·음성1 = 16 + 멈춤 3 + 재개 2 + Aside 1), 변조 `CHECKED: 12`(불변식 8 + 멈춤 3 + 재개 1) | §15 8개 각 양성·음성; 포트 자동 발견·0.0.0.0 거부·프로토콜 범위; **경쟁 시험**(Codex 반례 스케줄 그대로 포함): 두 스레드, `revoke()` 를 ⓐ 검사 직전 ⓑ 검사와 전송 사이(barrier 로 강제 선점) ⓒ 전송 도중 세 지점에 각 100회 주입 → `sent_after_stop == 0` 300/300, `revoke()` 반환 시점에 소켓 `fileno() == -1`, 회수 지연 `<= 1000ms`(`time.monotonic`); 재개: 해소 fixture → 새 번호 재획득 → checkpoint 이어감 1, 스위치 켜짐 → 재개 0. 재부팅 기동·세션 장기 유지는 `NOT_RUN` 표기(WU-2c) |
| **C1a** | `hs-c1-storage-contract` | `bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-c1.sh`(§12 조건 중 3 제외 8개: 계약 문서 존재, 저장 경로 0700/0600, `.gitignore`+`scan-data-exposure.sh` raw 경로 차단, 보존·삭제 시험) + `cd humansearch && uv run pytest tests/test_mandatory_save.py tests/test_retention.py -q` + `acceptance-hs-sot-amendment.sh c1a`(⑧ §12 조건 3 → "2026-09-08 포괄 승인", 조건 7 → "보존 = 무기한, 삭제는 `/hs purge` + PII 없는 영수증") | `CHECKED: 8`, `>= 10 passed` | 가짜 데이터: 열람 3 → 저장 3; 저장 실패 → 순회 즉시 STOP; readback SHA 일치; purge 1건 → 영수증 PII 0; 만료 자동 삭제 함수 **부재**(정적). **라이브 0.** 이 PR 이 main 에 병합돼야 C1b 시작(순환 제거) |
| **C1b** | `hs-c1-first-live` | `bash scripts/verify/live-receipt.sh saramin observe` + `bash scripts/verify/live-receipt.sh saramin stop` | `CHECKED: 2` | 사람인 Aside 탭 1개 읽기 1(§12 최소 접속) + **라이브 멈춤 1**(STOP 파일 생성 → 1초 안 전송 차단 실측). Codex 독립 재관측: `node /Users/kangsangmo/.claude/plugins/cache/openai-codex/codex/1.0.2/scripts/codex-companion.mjs task --wait "읽기 전용: 127.0.0.1:<발견된 포트>/json/list 를 curl 로 읽어 page 탭 수·origin 목록을 출력하고 <영수증 경로> 와 대조, 첫 줄 MATCH|MISMATCH"` → `result` 로 회수, `MATCH` 아니면 `NOT_RUN`(§2-11) |
| **4** | `hs-clickup-read` | `cd humansearch && uv run pytest tests/test_clickup_read.py -q` + `bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-netblock.sh clickup`(`env -i PATH=$PATH HTTPS_PROXY=http://127.0.0.1:9 HTTP_PROXY=http://127.0.0.1:9 uv run python -m humansearch.adapters.clickup_read --live-probe` → exit≠0 이고 stderr 에 `network`) + `bash scripts/verify/live-receipt.sh clickup list` | `>= 8 passed`, netblock `CHECKED: 1`, 라이브 1 | 목록 fixture 20 → PositionSpec 20; 이름 검색; id 1건(양성); 미실존 id 거부; 필드 누락 거부; fixture 지문 = 실제 응답 SHA(PII 0) |
| **5** | `hs-discord-queue` | `cd humansearch && uv run pytest tests/test_bot_*.py -q` + `bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-bot-pii.sh`(답글 payload 에 이름·전화·이메일 패턴 0) + `bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-bot-boundary.sh`(봇 패키지 import 그래프에 `_cdp`·`observe`·`daemon` 0, `subprocess`·`importlib.import_module` 0) + `bash scripts/verify/live-receipt.sh discord command` | `>= 10 passed`, `CHECKED: 5` | 파서 경유 정상 1 → 행 1(시험의 DB 직접 삽입 금지); 허용목록 밖·만료 없음·미실존 ref 거부 3; 동일 명령 2→1; 라이브: 테스트 서버 1건 → 행 → expired |
| **6** | `hs-c1-saramin-surface` | `cd humansearch && uv run pytest tests/test_saramin_surface.py -q` + `bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-fixture-provenance.sh`(fixture 지문이 `scripts/verify/live-receipt.sh saramin capture` 가 남긴 영수증의 SHA 와 일치 — 손제작 fixture 차단) | `>= 9 passed`, `CHECKED: 1` | 목록·상세·복귀 정상 3 + 드리프트 3 |
| **7** | `hs-v1-saramin-one` | `bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-v1.sh saramin aside` — 후보 1명: 목록→상세→`evidence` 행(SHA-256, manifest `doc_height`·viewport 좌표)→복귀; CDP 로그에 `Target.createTarget|closeTarget|activateTarget` 0, 클릭 재시도 0; 재실행 → 같은 후보 재열람 0 **+** 다른 후보 열람 1 | `CHECKED: 6` | 라이브 1명 |
| **7b** | `hs-v1-chrome-fallback` | `bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-v1.sh saramin chrome`(정책 json 을 `engine=chrome` 으로 바꾼 사본 사용) | `CHECKED: 6` | **사장님이 새로 띄운** Chrome 전용 프로필(v4 의 `~/.vh-profiles` 아님) 사람인 1명 |
| **8** | `hs-d3-runner` | `cd humansearch && uv run pytest tests/test_runner*.py -q` + `bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-runner-live.sh` | `>= 14 passed`, `CHECKED: 5`(정상 3 + 멈춤 1 + 재개 1) | 프리플라이트 양성 1·음성 5; 미로그인 → 순회 0 + Discord 알림 실제 1(readback); `/hs stop` → 잔여 0·1초; 재개 1 |
| **9** | `hs-e1-supabase-export` | `cd humansearch && uv run pytest tests/test_export*.py -q` + `bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-netblock.sh supabase` + `bash scripts/verify/live-receipt.sh supabase readback` | `>= 10 passed`, `CHECKED: 3` | RLS 실 정책 덤프(비면 FAIL); 화이트리스트 밖 exit 1; outbox 1 → upsert → 별도 클라이언트 select 지문 일치; 꺼짐 → 로컬 완료 유지; 정적: 중복 판정 import 에 supabase 0 |
| 10 | `hs-x1-jobkorea` | `bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-v1.sh jobkorea aside` + `cd humansearch && uv run pytest tests/test_jobkorea_surface.py -q`(`contracts/humansearch/jobkorea-markers.json`, fixture 지문 = `live-receipt.sh jobkorea capture`) | `CHECKED: 6`, `>= 9 passed` | 라이브 1명 |
| 11 | `hs-x2-linkedin-rps` | `cd humansearch && uv run pytest tests/test_pacing.py -q`(실제 `time.monotonic`, 표본 ≥ 30, 간격 2.0~9.0초, 인접 동일값 0, 평균 ≥ 4초) + `bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-v1.sh linkedin_rps aside` + `acceptance-hs-sot-amendment.sh 11`(⑫ §4·§5 LinkedIn 상세 저장 조항 개정 7요소) | `>= 6 passed`, `CHECKED: 6` | 프로젝트·필터 준비 확인 관문(없으면 exit 2); 캡차 fixture → 즉시 STOP; 라이브 1명 |
| 12 | `hs-recurrence` | `cd humansearch && uv run pytest tests/test_recurrence.py -q` | `>= 8 passed` | 스케줄러 함수가 큐 행 생성(직접 삽입 금지); 창 안 재열람 0·창 밖 1; 경계 ±1초 |
| 13 | `hs-e2-clickup-report` | `cd humansearch && uv run pytest tests/test_clickup_report.py -q` + `bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-netblock.sh clickup_report` + `bash scripts/verify/live-receipt.sh clickup subtask` | `>= 8 passed`, `CHECKED: 2` | write-ahead → 생성 → readback; 멱등키 중복 → 기존 readback; 발송 0 |
| 14 | `hs-s1-scoring` | `cd humansearch && uv run pytest tests/test_scoring.py -q`(Hypothesis 속성 시험 포함) | `>= 20 passed` | 순수 함수 D1~D8 + 하드 제외(프리랜서·12개월 미만 2회) + 기준 5종 대응표(마스터플랜 §3-1); 같은 입력 100회 SHA 1종; 서울 소재 대학 목록은 `contracts/humansearch/schools-seoul.json` |
| **15** | `hs-p17-runner-isolation`(**C1b 전**) | `bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-p17.sh` | `CHECKED: 4` | 영수증 디렉터리 `hsrunner` 소유·타 계정 쓰기 불가; 현재 셸(구현 에이전트)이 쓰기 시도 → EACCES; `sudo -u hsrunner` 실행기만 성공; `live-receipt.sh` 가 자기 실행 계정을 영수증에 기록 |
| 2c | `hs-d1-autostart` | `bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-launchd.sh` | `CHECKED: 3` | plist 가 저장소·워크트리·Desktop 경로 미참조(P6); 재부팅 실증 1(사장님 재부팅 후 3 인스턴스 `/json/version`); `doctor/status` 명령 존재 |

**진행 방식**: WU-0A 부터 순서대로 한 번에 하나. PR 을 열면 병합을 기다리지 말고 다음 워크트리를 판다. 착수 전 `gh pr list` 와 codex 세션 수 확인. 두 세션이 같은 WU 를 잡지 않는다.

## §4. 모든 WU 공통 절차

1. 게이트 0: `bash scripts/session-status.sh` → `RED: 0/…` 과 뒤 오류 줄 없음, HEAD == origin. (이 스크립트와 변이 검사기는 내부에서 `mktemp` 를 쓴다 — 정상 세션에서는 문제없고, codex 샌드박스에서만 못 돈다.) `git worktree add worktrees/<name> -b task/<name>`. 메인 작업트리 소스 수정 금지.
2. RED 커밋 먼저(시험·fixture·의존성·lock 만; 수집 0건·문법 오류는 RED 아님). GREEN 은 제품 코드만, 시험 파일 불변(P5·P15).
3. 외부 효과 모듈은 `acceptance-hs-netblock.sh <모듈>` 동봉(P4). 라이브 영수증은 `scripts/verify/live-receipt.sh` 만 쓴다(§2-11). 구현 에이전트가 영수증 경로에 쓴 흔적 → FAIL.
4. 판정 `PASS:/FAIL:/CHECKED:` 규약, 최소치 미만 = exit 1(P20). 자기 변이 3종 + 공통 5종.
5. 새 `scripts/acceptance-*.sh` 는 `verify.yml` + `docs/sot/verification-commands.md` 같은 PR. `bash verify.sh` 출력 숫자 PR 본문에.
6. 정본·계약 파일을 건드리면 §2-10 의 7요소. 라벨 `weakens-check` 없는 정본 diff 는 머지 불가.
7. 적대 검증: Claude V1 → Codex V2 재현. 판정 파일 `.claude/private-reviews/<wu>-verdict-<date>.md` 첫 줄 `VERDICT:`. **단, CI 인수 검사가 판정 파일을 세는 WU(0A 등)는 저장소 안 `docs/engineering/` 에 둔다** — `.claude/private-reviews/` 는 `.gitignore:24` 로 무시되어 CI 러너에 존재하지 않는다(2026-09-09 정정). **codex 샌드박스의 `mktemp`·파일 쓰기 차단은 실행 시점에 따라 다르다** — 2026-09-09 5회차에서는 둘 다 성공했다. 막히면 그때 미확인으로 적는다. **codex 샌드박스는 파일 쓰기·`mktemp`·네트워크·`uv` 캐시를 막는다** — 판정은 `node /Users/kangsangmo/.claude/plugins/cache/openai-codex/codex/1.0.2/scripts/codex-companion.mjs result <job>` 로 회수해 Claude 가 파일로 저장하고, 시험 실행은 Claude 가, codex 는 읽기·대조·독립 재관측.
8. PII: URL 경로 축약, 이름·연락처 암호화, 캡처 원본 git 밖(P21). 브리핑 3층, 용어 즉시 풀이, 결정 5줄 카드. 완료 선언은 CI 초록 + `check-verified-sha.sh` VERIFIED 뒤에만.

## §5. 절대 안전선

- 자동 로그인·자격증명 입력·저장 코드 0줄. 미로그인·캡차·2FA·세션 충돌 → 재시도 0, 정지 + Discord 알림 1건. 재개는 새 관측 뒤에만(⑦).
- **멈춤 스위치는 항상 이긴다.** 세 경로 중 하나라도 켜지면 전송 핸들이 닫히고(§2-9), 켜진 동안 재개 없음. 라이브 멈춤이 증명되지 않은 WU 는 라이브 권한 없음.
- 열람한 프로필은 **무조건 저장**(⑧). 저장 실패 = 순회 정지. 삭제는 `/hs purge` 만.
- 제안·InMail·메일 발송 자동 클릭 0회. 브라우저 kill·재시작·프로필 생성·포트 개방 0회(테스트 전용 임시 Chromium 은 WU-2 안에서만). 새 탭 0·닫기 0·활성화 0. 목표 탭 ≠ 1 → 정지.
- v1~v5·`~/.hermes`·`Valuehire_v4/tools` 참조 0(G1). **작업 중 전역 스킬 `search`·`ai-search-position-pipeline`·`saramin-talent-sourcing`·`jobkorea-talent-sourcing`·`chatgpt-*`·`position*`·`linkedin-rps-jd-set-builder`·`talent-search` 발동 금지** — 전부 `cd Valuehire_v4` 를 하드코딩해 v4 코드를 실행한다("서치해줘" 같은 말에 자동 발동되므로 이 프롬프트 안에서는 그 키워드로 스킬을 부르지 않는다). v4 가 띄운 Chrome 9223/9225 프로필은 되돌리기(WU-7b)에서도 쓰지 않고, 되돌릴 때는 사장님이 새 전용 프로필로 Chrome 을 띄운다. 억제(`suppressions.yaml`) 기본 처리 금지.

## §6. 사장님 결정 카드

- **카드 1 Aside 역할 → 결정됨(⑩).** 잡코리아 다중 사용도 확인됨(⑪).
- **카드 2 Discord 봇 → 사장님이 할 일 1개.** 디스코드 개발자 포털에서 봇 계정을 하나 만들고 밸류커넥트 서버에 초대한 뒤, 봇 토큰(비밀 문자열)을 `~/.humansearch/env` 에 `DISCORD_BOT_TOKEN=` 으로 저장. 절차서는 WU-5 착수 세션이 5줄로 만들어 드림. 허용 멤버는 id 목록 대신 **서버 역할 하나**(예: `humansearch`)로 — 역할을 주면 명령 가능.
- **카드 3 미병합 6건 처분 → 기본값으로 진행.** 예전에 만들다 만 작업 6개(PR 3 + 브랜치 3)가 남아 있음. WU-0A 가 "병합 / 폐기" 추천표를 만들어 올리면 사장님은 GitHub 에서 병합 버튼만 누르거나 "폐기 OK" 한 마디. 기본 추천: PR #13 G3 병합, #54 병합, #15 폐기(문서만이라 WU-0A 가 필요한 것만 회수), `hs-d1-permit` 은 WU-2 가 흡수, 나머지 2개 폐기.
- **카드 4 Supabase → 기본값으로 진행.** v4/v5 가 클라우드에 쌓아 둔 후보 데이터(1,386건)를 v6 도 같은 표에 이어서 씀(새 표 안 만듦). 그 표에 접근 규칙(RLS)이 안 걸려 있어 열쇠만 있으면 누구나 읽을 수 있는 상태 — WU-9 가 규칙을 걸어 줌. 사장님 결정 필요 없음, 반대 없으면 진행.
- **카드 5 멤버 범위 → 기본값으로 진행.** 명령 허용 = 카드 2 의 역할을 가진 멤버 전원. 결과 = 명령 올린 채널에 답글. 별도 채널을 원하시면 채널 이름 하나.
- **카드 6 자동 재개 → 결정됨(⑦).** WU-2 가 정본 개정 7요소로 처리.
- **카드 7 저장 동의 → 결정됨(⑧).** 보존 = 무기한, 삭제는 명령. 보존 일수를 두고 싶으시면 숫자 하나.
- **카드 8 LinkedIn 후보 상세 저장 → 결정됨(⑫, "당연히 저장").** WU-11 이 §4 개정 7요소로 처리.

## §7. 첫 작업(WU-0A) 종료 조건 — 끝나면 곧바로 WU-0B

- 워크트리 `hs-kickoff-ledger` 에 ① 이 프롬프트 ② 처분표(6건 결론+근거) ③ `verification-commands.md` CI 스텝 30 갱신(실측) ④ `scripts/acceptance-hs-kickoff.sh` + `verify.yml` 배선 ⑤ 08-17 설계서 2건 `docs/engineering/history/` 보존 — 커밋 + PR 열림. `bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-kickoff.sh` → `CHECKED: 12`, exit 0. 자기 변이 `bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-kickoff-mutations.sh` → `CHECKED: 33`(양성 6 + 음성 27), exit 0. `bash verify.sh` 숫자 PR 본문에.
- Codex V2 판정을 `result` 로 회수해 파일 저장(크기 > 0, 첫 줄 `VERDICT:`).
- 사장님께 남는 것은 **카드 2(봇 계정 만들기) 하나**와 카드 3 의 병합 버튼. 나머지는 기본값. merge 0. 막히면 원인 기록 후 다음 항목, 2회 막히면 질문으로.

## §9. v5 가 v4 판정에서 고친 것

| 출처 | 지적 | v5 처리 |
|---|---|---|
| HR-1 / CX-B1 | ⑦⑧⑪ 정본 개정에 §16·P13 절차 없음 | §2-10 7요소 고정, 해당 WU 인수 조건에 포함 |
| HR-1(높음) / 카드 8 | LinkedIn 상세 저장이 §4 와 충돌 | WU-11 에 §4 개정 7요소, 카드 8 신설 |
| CX-B2 | WU-C1 순환(계약 병합이 자기 합격조건) | C1a(계약·시험, 라이브 0, 병합) / C1b(첫 라이브) 로 분리; 보존 = 무기한 명시 |
| CX-B3 | ⑪ 과 용어 풀이 "사람인 1석" 자기모순 | 용어 풀이 수정: RPS 1석, 사람인 다중, 잡코리아 미확인=1석 |
| CX-B4 | 멈춤 플래그 TOCTOU(`sent_after_stop=1`) | 회수 가능한 전송 핸들(§2-9), 경쟁 시험 100회 `sent_after_stop==0`, 첫 라이브(C1b)에 라이브 멈춤 |
| CX-B5 / 이 세션 실측 | `checked=` 소문자 → 실행기는 `CHECKED:` 만; 변이 5종 중 `if false` 없음; 7b·10·9·11·13 명령 부재 | 출력 규약 `PASS:/CHECKED:`; 공통 5종 + 자기 변이 3종; 모든 WU 에 실행 명령 |
| CX-B6 / v1-8 | P17 위조 가능 | §2-11 두 겹 영수증 + Codex 독립 재관측, WU-15 격리 정의 |
| CX-C | fixture SHA 손제작, WU-0A 인수≠종료조건, WU-8 최소치, WU-2 CHECKED 의미, 지터 수치 | provenance 검사, 0A `CHECKED: 11` 로 종료조건 포함, WU-8 5, CHECKED = 실행 건수 명시, 지터 표본 ≥30·2~9초·평균 ≥4 |
| v1-3 / v1-10 | D1 자동 기동 미정의, 채점 미정의 | WU-2c launchd, WU-14 S1 정의 |
| HR-4 / HR-5 | PR #15 설명 오류, STOP 경로 하드코딩 | §0 정정(docs 스냅샷 PR), `runtime-paths.json` |
| CX6-C | 회수 핸들도 신호→close 사이 선점으로 누출(`sent_after_stop=100`) | 잠금 하나로 send/revoke 직렬화 + shutdown→close→None 뒤 반환 + `Grant` 능력 객체, 경쟁 시험 3지점×100 |
| CX6-H6 | 라이브가 P17 격리보다 먼저 | WU-15 를 C1b 앞으로, `hsrunner` 계정 설계 |
| CX6-A3 | 다중 브라우저인데 lease 가 채널당 1행 | RPS 만 채널당 1행, 사람인·잡코리아는 인스턴스당 + `candidate_locks` |
| CX6-D | 명령이 `run-acceptance.sh` 우회, pytest cwd 오류, 7요소·자기 변이·재관측이 산문 | 전 명령 래퍼 경유, `cd humansearch &&`, `acceptance-hs-sot-amendment.sh`, 공통 꼬리 명령, codex 재관측 명령 |
| CX6-B 카드 5 | Discord 답글 PII 미정의 | 답글 = 수·채널·포지션·URL 만, `acceptance-hs-bot-pii.sh` |
| 사장님 09-08 | v4/v5 의존 검수 | 전역 스킬 발동 금지 목록, v4 Chrome 프로필 불사용, 되돌리기도 새 프로필 |
