/strict HS-13 PR #83 후속 — 사장님 결정 B: 발송 무결성 결함을 전부 고친 뒤에만 merge 가능 상태로 만든다. 나는 자리를 비우니 웬만한 판단은 네가 하고, 파괴적 작업·외부 발송·후보 접촉만 멈춰라. "CI 초록 = 안전"이 아니다 — 이 PR은 CI 초록 상태에서 적대 검토가 S1 2건을 찾은 반례다. 이전 기록의 "코드 자체는 합격" 표현은 뒤집혔으니 PR·Issue 갱신 때 지워라.

## 대상·상태
- 워크트리 /Users/kangsangmo/Desktop/Valuehire_v6/worktrees/hs-13-stack-20260910 (브랜치 task/hs-13-stack-20260910, HEAD 767d027 = 원격 = PR #83). 이 워크트리에서만. main 직접 수정 금지.
- 정본 스펙 docs/engineering/humansearch-hs13-position-brief-goal-2026-09-10.md, 검사기 scripts/acceptance-hs-1300.sh(+-mutations.sh), 코드 humansearch/src/humansearch/brief/, 시험 humansearch/tests/test_hs_13*.py, 계약 contracts/humansearch/*.json. Issue #82. 메모리 project_hs13_brief_spec_state_20260910.md 를 먼저 읽어라.

## 이번 작업이 지켜야 할 불변식 3개 (코드 + 시험으로 박는다)
I1. 승인된 digest ≠ 현재 digest 이면 발송할 수 없다 — claim_send 는 잠금 안에서 현재 패킷의 body_sha256·recipients_sha256 을 SendIntent 와 대조한다.
I2. 검증에 성공하지 않은 발송은 어떤 공개 API 로도 VERIFIED 가 될 수 없다 — verify 와 상태 전이는 같은 잠금 구간의 한 함수다.
I3. 한 attempt 안에서 body·recipients·packet identity 가 바뀌면 기존 승인은 무효다 — 새 attempt 는 자기 digest 를 기록한다.

## 고칠 것 (심각도순. S1 은 전부 merge 차단)
S1-1) claim_send: 현재 패킷(또는 body/recipients digest)을 인자로 받아 잠금 안에서 SendIntent.body_sha256·recipients_sha256 과 대조, 불일치 시 거부. PacketStore.save 도 같은 packet_id 에 intent 파일이 있으면 변경 저장을 거부하되, 저장 경로 우회를 가정하고 claim 경계 대조를 주 방어선으로 둔다. 회귀 test_hs_1309d.py: ① 본문만 변경 ② 수신자만 변경(1→4명) ③ 둘 다 변경 → 각각 claim 거부.
S1-2) 일반 mark 로 VERIFIED 생성 금지. verify_and_mark(dir, packet_path, readback_path, message_id, at) 하나만 VERIFIED 를 만든다: cli.verify 의 해시·꼬리 검증 → 통과 시 같은 잠금 구간에서 전이 → 전이 기록에 packet_id + attempt + body_sha256 + recipients_sha256 + message_id 를 함께 남긴다(검증한 digest 자체를 장부에 기록). cli.py 에 --mark 로 노출. 회귀 test_hs_1310b.py·test_hs_1309.py: ④ verify 실패 뒤 mark(VERIFIED) 거부 ⑤ verify 성공 직후 패킷을 바꾸면 verify_and_mark 거부(TOCTOU) ⑥ 다른 attempt 의 message_id·readback 으로 이 attempt 를 VERIFIED 못 만듦.
S1-3) open_new_attempt: body_sha256·recipients_sha256 을 필수 인자로 받아 a2 에 기록(a1 복사 금지). a1 과 같으면 approval.reason 에 "정정 없음" 명시를 요구. 회귀 test_hs_1309b.py.
S1-4) SearchPacket._check_mail_embeds_jd: JD 3블록 밖 본문에도 EXTRA_CONDITION_PATTERNS 매치 0 강제(JD·allowed_extra 밖). 회귀 test_hs_1304b.py: 경력·연봉·학력 조건 3종 + 블록 밖 위치 2곳 이상.
S2-5) compose_brief_mail: 본문 모든 줄에서 packet-id: 접두 거부(대소문자·앞 공백·개행 주입 포함), 한 줄 필드(key_line·sender_name 등) 개행 거부. 회귀 test_hs_1305.py. 자동 재발송은 존재하지 않으므로 S2 — "영구 미검증" 같은 표현은 쓰지 마라(승인 재시도 경로가 있다).
S2-6) 카드 13.10 VERIFIED·PR 본문 "PRODUCTION_VERIFIED" → "legacy artifact — 현행 코드로 재검증 불가" 로 정정. 구 패킷 호환 로더는 만들지 않는다(PII 파일을 읽는 코드를 늘리지 않는다). 앞으로 만드는 패킷 JSON 에만 schema_version 필드를 넣고 from_json 은 버전 없음·다른 버전을 거부한다.
결정 D13(스펙 §7 에 추가): recipients_sha256 은 to·cc 를 각각 정렬한 뒤 계산한다(순서 무관, 중복 불가). 지금 계약이 없어 구현 간 digest 불일치가 날 수 있다 — 시험 ② 의 [a,b]/[b,a] 로 고정.
낮음(같은 PR, 시간이 남으면): 검사기 글자 수 wc -m·${#var} 를 perl -CS 로 통일 + LC_ALL=C 변이 · LINKEDIN_FRAME_LINES 를 "제목:"·"문의:" 만 접두, 나머지는 완전 일치 · 한계②·카드 13.09 "(정적 검사)" 문구 정정 · 카드 13.05 "절 누락 거부" 시험 · §5 시그니처 6곳 갱신 · 카드 수 "18"→22 · registry 에 hs-1305-pii-mutations 추가 · scripts/verify/check-mechanism-registry.sh 를 CI 스텝으로 배선(+verification-commands·registry 동기화) · may_send 가 장부를 쓰는 사실 문서화 · git diff --check 빈 줄.

## 규칙
- L3. 후보 PII·실 URL·실 이메일은 git·PR·판정 파일·로그에 0(fixture 는 example-·holder@valueconnect.kr·@example.com 만). 후보 발송 절대 금지. 라이브·재발송은 사장님 지시 없이는 하지 않는다. linkedin.com 직접 열람 금지.
- 워크트리 1개=PR 1개. 결함마다 RED 시험 커밋 → GREEN 커밋(이 저장소 하네스 게이트 2 규칙 — 실패 증거를 이력에 남긴다). 시험 약화 금지(P13), CHECKED 불변식(P20), 운영 상수는 계약 파일(P22), 파일 300줄 soft(P11).
- 검사기는 커밋 전에 UTF-8 과 LC_ALL=C LANG=C 양쪽으로 돌려라. printf|grep -q 금지.
- 커밋 메시지 한국어, 끝에 Co-Authored-By: Claude 줄. merge 는 사용자만(USER_MERGE_ONLY).
- Codex 적대 검토: 프롬프트에 백틱 금지. node /Users/kangsangmo/.claude/plugins/cache/openai-codex/codex/1.0.2/scripts/codex-companion.mjs adversarial-review --background --base fc6beed --scope branch '<프롬프트>' ; 결과는 같은 디렉터리에서 codex-companion.mjs result. 명시된 한계 4종(승인 재발송 at-least-once·같은 UID 파일 삭제/위조·산문 의미 적합성·core_tokens 형태소 경계)은 차단 아님. **triage 규칙: 최대 2회 검토 뒤 남은 지적은 하나씩 등급을 매긴다. S1(발송 권한·PII·검증 무결성)은 라운드 수와 무관하게 merge 차단으로 유지하고 고친다. S2 이하만, 사유를 적고 Issue #82 부채로 넘긴다.**

## 완료 조건 (전부 fresh 실행 증거)
- I1: 본문/수신자/둘 다 변경 시 claim 거부 RED→GREEN.
- I2: verify 실패 뒤 어떤 공개 API 로도 VERIFIED 불가. 성공 readback 과 장부 전이가 같은 attempt·digest 에 묶임. 다른 attempt 의 message_id 재사용 거부.
- I3: attempt 2 는 attempt 2 의 digest 를 기록.
- packet-id 주입(대소문자·공백·개행) 거부. JD 블록 밖 조건 3종 이상 거부.
- 전체 pytest·ruff·mypy --strict·검사기 6종(hs-1300·mutations·1301b·1305·1308·1309)·Full Strict(bash verify.sh + verify.yml acceptance 전부 + hs-gates) 통과. acceptance-0-5 가 다른 세션의 로컬 main 미push 커밋으로 FAIL 이면 사유만 기록.
- Codex 재검토에서 발송 권한/PII/VERIFIED 관련 S1 0건.
- 시험 중 실 이메일·실 후보·실 LinkedIn 접근 0.

## 순서
1. 메모리·스펙 §5·§7·§9·§10·적대 검증 로그 읽기 → 위 항목을 WU 카드(HS-13.09g·13.10c·13.04c·13.05b 등)로 §9 에 추가, D13 을 §7 에 추가, 검사기 WU_IDS·EXPECTED_CHECKED·mutations sed(카드 수)·verification-commands 행 동기화.
2. S1-1 → S1-2 → S1-3 → S1-4 → S2-5 → S2-6 → 낮음 순으로 RED→GREEN. 매번 cd humansearch && uv run --no-sync pytest -q / ruff check src tests / mypy --strict src tests + 검사기 6종.
3. Full Strict(로그를 스크래치에 저장).
4. Codex 적대 검토 최대 2회 → triage 규칙대로 처분.
5. push origin task/hs-13-stack-20260910(pre-push 훅 통과) → PR #83 본문·코멘트 갱신("합격" 표현 제거, 판정 첨부, 남은 S2 부채 목록) → CI push·pull_request 두 이벤트 초록 확인 → Issue #82 코멘트.
6. 보고: 쉬운 한국어로 무엇/왜/증거(숫자 그대로)/다음. 이름·URL·이메일 0. "해결 확인"은 fresh 실행 결과가 있는 항목에만 쓰고, 재발송 여부는 사장님 결정 사항으로 남겨라.
