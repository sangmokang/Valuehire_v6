# HS-03.02 사전검사기 — 검사 16개 분류표 (v4 1단계, 2026-09-20, 코드 수정 없음)

기준: ① 없으면 잘못된 코드·잘못된 실행환경의 결과가 PASS 되어 push·마감될 수 있는가 ② 실제 사고 때문에 생긴 검사인가 ③ 다른 기존 게이트가 같은 위험을 막는가. 규칙: ①예→KEEP · ①아니오·②없음→REMOVE · ①아니오·②있음·③없음→DECISION. 줄 번호는 scripts/verify/hs0302-closeout-preflight.sh(e36770d 기준). goal-prompts/ 아래에 둔 이유: git.prompt-tail 이 goal-prompts 밖 변경을 FAIL 로 세기 때문.

| 검사 | ① | ② 사고 근거 | ③ 대체 게이트 | 처분 |
|---|---|---|---|---|
| git.worktree :113 | 예 — 다른 저장소 경로면 엉뚱한 트리를 판정 | 없음(설계) | 없음 | KEEP |
| git.branch :118 | 예 — 다른 브랜치·detached 를 마감으로 오인 | 없음 | 없음 | KEEP |
| git.clean :124 | 예 — 미커밋 변경이 판정에 섞임 | 없음 | 없음 | KEEP |
| git.base-ancestor :129 | 예 — 기준 위에 쌓이지 않은 코드를 마감 | 없음 | 없음 | KEEP |
| git.prompt-tail :140 | 아니오 — 마감 프롬프트와 코드의 문서 동기화이지 코드 결함 방어가 아님. 코드 커밋마다 프롬프트도 건드려야 해 마찰이 큼 | 없음 | 검사 수·명부 일치는 acceptance-ci-step-integrity·mechanism-registry 가 검사(docs/sot/verification-commands.md) | REMOVE |
| proc.codex :156 | 아니오 — 판정과 SHA 의 귀속은 git.clean(전)·ac2 의 status 전후 대조(:251,:272)·v1.head(:354)가 지킴 | 있음 — 세션 동시 실행으로 작업 소실 1회·중복 1회(2026-09-05); 고아 Codex 트리가 마감을 BLOCKED(README 결론, pid 76616·84050); 2026-09-20 에도 09-18 Codex 리뷰 잔여 트리(38781)로 BLOCKED | 동시 세션 소실 자체를 막는 게이트 없음 | **DECISION** |
| proc.cwd :165 | 아니오 — 위와 같음 | 있음 — 표본기 sleep 고아가 워크트리를 점유(2026-09-17 실측) | 없음 | **DECISION** |
| shm.ledger :190 | 아니오 — 보고만 하며(삭제 없음) 판정을 바꾸지 않음(30개↑ 는 BLOCKED) | 있음 — 고아 공유메모리가 invoice 게이트를 shmget ENOSPC 로 죽임(검사기 :197 주석, 2026-09-09 메모리) | 없음(다른 invoice 검사는 System V 공유메모리를 보지 않음) | **DECISION** |
| shm.post :225 | 아니오 — 이 실행이 만든 신규 세그먼트의 소유권 6조건 증명(:211-224, 표본기 포함 ~40줄). V2 에서 6조건 전부 무시험으로 드러남 | 위와 같은 사고 | 없음 | **DECISION** (유지하면 "신규 세그먼트 1개↑ = BLOCKED" 한 조건으로 줄이는 안 권고) |
| ac2.copy :248 | 예 — 변이 사본이 원본 venv·파일을 공유하면 변이 시험이 원본을 오염해 거짓 판정(검증기가 대상을 바꾼 사고 2026-08-07; 복사 venv 가 다른 워크트리 실행 2026-09-16) | 있음 | 없음 | KEEP |
| ac3.clone :327 | 예 — 객체 공유 클론·복사 venv 면 V1 판정이 다른 트리 것(허위 FAIL 사고 2026-09-01, Codex 실증 2026-09-16) | 있음 | 없음 | KEEP |
| v1.sha :353 | 예 — 판정 대상 SHA 형식 | 없음 | 없음 | KEEP |
| v1.head :354 | 예 — 판정이 현재 HEAD 것인지 | 없음 | 없음 | KEEP |
| v1.rc :359 | 예 — codex exec 실제 반환값 없이는 판정 불채택(서브에이전트 본문 유실 사고) | 있음 | 없음 | KEEP |
| v1.verdict :365 | 예 — 첫 줄 VERDICT·본문 SHA | 없음 | 없음 | KEEP |
| v1.venv-same :373 | 예 — 판정 뒤 클론 환경 변조(링크 대상 교체, V1 r2 반례15) | 있음 | 없음 | KEEP(자기신고 한계는 그대로) |

집계: KEEP 11 · REMOVE 1(git.prompt-tail) · DECISION 4(proc.codex, proc.cwd, shm.ledger, shm.post).

→ 해석: 검사기 축소분은 크지 않다(사고 근거가 있는 검사가 대부분). 실질 축소는 2단계에서 인수 시험(반례 36종 → 남은 검사당 정상 1·잘못된 상태 1)에서 나온다. DECISION 4개는 사장님이 "삭제" 또는 "유지" 한 단어로 답한다. 삭제 = 그 사고 재발을 감수. 권고: proc.codex·proc.cwd 는 삭제(오늘처럼 검사기 자신이 남긴 잔여 프로세스에 막히는 마찰이 더 크고, 판정-SHA 귀속은 다른 검사가 지킴), shm.ledger 는 유지(ipcs 한 번, 보고만), shm.post 는 한 조건으로 축소 유지.
