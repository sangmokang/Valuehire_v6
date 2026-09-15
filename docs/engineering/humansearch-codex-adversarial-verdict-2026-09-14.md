# HumanSearch 적대적 리뷰 판정 장부 — Codex 2회(2026-09-14 21시) + Claude 독립 재현(2026-09-15 01:36~01:39)

실행: `codex-companion.mjs adversarial-review` (codex-cli 0.154.0), 읽기 전용. 두 대상 모두 verdict = needs-attention.
Finding ID는 이 장부에서 부여한다(Codex 원문에는 ID가 없다). 재검토 때 이 ID로 해결/부분/미해결을 적는다.

## 심각도 정합 (2026-09-15 정정)

Codex 원문 라벨 기준: **high 3건, medium 2건**. 이전 v6 §2의 "S1 4건"은 Claude가 F96-2(medium)를 근거 명시 없이 S1로 올린 것이며, 누락된 네 번째 원문 finding은 **없다**. 정본 수치는 아래 표의 Codex 라벨이다. F96-2를 S1로 다룰지는 §3 결정 카드로 분리했다.

| ID | PR | Codex 라벨 | 파일:줄 | 무엇이 잘못되나 | Claude 독립 재현(Finding 상태) |
|---|---|---|---|---|---|
| F83-1 | #83 | high | `humansearch/src/humansearch/brief/linkedin_limit.py:285-289` — 프레임 줄 면제 필터 | `문의: 대졸 필수`, `문의: 재택근무 가능`이 프레임 접두 + 조건 정규식 미매치라 충실도 검사에서 통째로 제거됨 | **REPRODUCED** 01:37:58 — 두 줄 모두 패킷 생성·JSON 왕복 통과, 본문에 잔존. 대조군 `문의: 경력 10년 이상만`은 거부(정규식이 잡는 경우만 막힘) |
| F83-2 | #83 | high | `humansearch/src/humansearch/brief/packet.py:292-300` — `PacketStore.save`, 잠금 없음 | save(B)의 intent 부재 확인 → record_intent(A) → claim_send(A) True → save(B) 교체. 승인 digest와 저장 패킷이 갈라짐 | **REPRODUCED** 01:39:12 — 훅으로 순서 고정: claim_send(A) `got=True`, save(B) ACCEPTED, 저장 digest ≠ 청구 digest. 사후 `_check_current_packet_digest`는 거부하므로 발송 직전 재검사를 거치면 B 발송은 막히나, 승인된 A 본문은 이미 소실(재검증 자료 손실) |
| F83-3 | #83 | medium | `humansearch/src/humansearch/brief/types_packet.py:324-330` — 회사 절 조건 검사 | 정상 fixture `- 매출: 300억 원 [I1]`이 회사 리서치 절에서 채용 조건으로 거부 | **REPRODUCED** 01:37:58 — test_hs_1305 `_draft` → `compose_brief_mail` → `SearchPacket` 이 `TeamMail.body 의 JD 블록 밖에 채용 조건이 끼었다: '- 매출: 300억 원 [I1]'` 로 거부 |
| F96-1 | #96 | high | `humansearch/src/humansearch/runner_boundary.py:55-66` — 루트 검사(lstat·0700) | 상위 디렉터리 소유권·심볼릭 링크·검사 후 교체 미방어 | **REPRODUCED** 01:38:32 — (b) 상위 컴포넌트 symlink: WRITTEN, 파일이 링크 대상에 생성. (b2) 상위 0777: WRITTEN. (c) 검사 직후 루트를 symlink로 교체: WRITTEN, **보호 밖 디렉터리에 파일 생성** |
| F96-2 | #96 | medium | `humansearch/src/humansearch/runner_boundary.py:140-146` — `_write_new_file` except 분기 | write/close OSError 뒤 생성 파일 미정리 → O_EXCL로 재시도 영구 거부 | **REPRODUCED** 01:38:32 — (d) 0바이트 파일 잔존, (e) 재시도 `target_already_exists`. 대조군 정상 쓰기 WRITTEN |

추가 관측(초안 a): 보호 루트 **자체**가 symlink인 경우는 현재 코드가 이미 `protected_root_invalid`로 거부한다. 이건 RED가 될 수 없고 회귀 보호 시험으로만 둔다.

재현 조건: hsrunner 계정이 이 Mac에 없어 `_runner_uid`만 현재 uid로 대체했다(경계 로직은 원본). 재현 스크립트 `docs/engineering/goal-prompts/humansearch-adversarial-repro-2026-09-15/` 3개. 세 워크트리 `git status --short` 전후 0줄.

## HS 밖 2건 (main 작업트리, 다른 세션 소유 — 보고만)

| ID | 파일:줄 | 내용 | 상태 |
|---|---|---|---|
| FV-1 | `scripts/verify/check-strict-verdict-ledger.sh:103-109` | 옛 fixture에 WU·현재 SHA 문자열만 붙이면 PASS. 영수증이 그 SHA에서 나왔는지 대조 없음 | Codex 메모리 실행 재현. Claude NOT_TESTED |
| FV-2 | `scripts/verify/run-acceptance.sh:64-74` | Ruby 검사기·계약 digest·mutation이 같은 변경 권한 안 → 독립 승인 경계 아님 | 코드 경로 분석. Claude NOT_TESTED |

## 결정 카드 — F96-2 심각도

> **무엇을** — F96-2는 Codex 라벨 medium을 정본으로 두되, 수정 순서는 F96-1과 같은 커밋 묶음에서 처리한다.
> **왜** — 같은 함수(`_write_new_file`)를 고치며 원자적 게시로 바꾸면 두 건이 한 설계로 닫힌다.
> **버린 길** — F96-2를 S1로 격상: 근거 없이 숫자를 바꾸는 일이라 기각. 별도 PR로 분리: 같은 함수 두 번 수정이라 기각.
> **대가** — F96-1 설계(dir_fd 고정)가 늦어지면 F96-2도 같이 늦어진다.
> **되돌리기** — 사장님이 S1 격상을 원하면 이 표의 라벨 열에 "owner: S1" 을 덧붙이면 된다. 코드 영향 없음.

## 한계

- Codex 대상 1은 HS 전용 diff가 아니다(다른 세션 미커밋 17파일 포함).
- HS PR 16개 중 #83·#96만 이번 리뷰 대상. 나머지는 각 PR의 외부 V1·독립 V2 이력 참조.
- Codex는 쓰기 필요한 장부 통합시험을 실행하지 않았다(읽기 전용 샌드박스).
- F83-2의 "다른 본문을 실제 발송" 부분은 러너가 발송 직전 재검사를 생략할 때만 성립한다(추론 ※). 승인 본문 소실은 재현된 사실이다.


## v8 프롬프트 리뷰 — Codex adversarial-review 3회(2026-09-15 10:05, thread 01a0a269-370e-7af0-8f7c-3f25f91d2599) + Claude 자기 검증(09:55~10:05)

대상: `docs/engineering/goal-prompts/humansearch-next-prompt-v8-2026-09-15.md` 초판(sha256 앞 16자 18246c82e8dbe76c) + Claude 의 Codex 현황 보고 검증 판정. verdict = needs-attention. 원문은 세션 스크래치 `codex-adversarial-v8.log` (Codex 출력 전문은 이 절 아래 표로 요약, 재현 명령은 원문 그대로).

| ID | Codex 라벨 | v8 줄 | 무엇이 잘못됐나 | 처분(10:10) |
|---|---|---|---|---|
| F-V8-01 | high | 80 | channel `linkedin` 허용 → #97 `storage_schema.py:55,70` CHECK 는 `linkedin_rps` 만. 메모리 SQLite 삽입 실행으로 재현(CHECK constraint failed) | **해결** — Claude 자기 검증이 09:58 같은 불일치를 잡아 10:05 패치(허용값 3개·HMAC 입력 정의)로 먼저 반영. Codex 는 초판을 봤음 |
| F-V8-02 | high | 95 | "마이그레이션 지우면 비용 0" → 적용된 DB 는 `_current_version` 201~211행이 unsupported version 으로 거부. 실행 재현 | **해결** — 되돌리기 줄을 DB 재초기화 절차 + 버전 2 없는 설계 우선으로 교체 |
| F-V8-03 | high | 103~104 | HS-05.02 EARS 에서 장부 201행 "예상 engine/**profile** 1개만 선택"의 profile 조건 누락. 같은 engine 다른 profile 반례 통과 | **해결** — profile 일치·유일성 복원, 필수 반례 추가, HS-05.03 도 profile 범위 명시 |
| F-V8-04 | medium | 54 | 로컬 전용 작업을 0303a 하나로 정리 → hs-0004-recovery(WU 장부 소재지)·hs-d1-permit 누락 | **해결** — Claude 자기 검증 10:00 실측(로컬 hs 브랜치 × 원격 × PR 전수 대조 → 4개)으로 먼저 반영. detached 워크트리 3개는 ⑤ 로 추가 |

Codex 한계(원문): 원격 조회 네트워크 차단, 임시 디렉터리 생성 제한으로 원칙 검사 불가, 기존 5개 결함 재현 미재실행, Image #5 미수신(LinkedIn Hiring Assistant 는 Claude 가 메모리 `reference_linkedin_hiring_assistant.md` 에 저장).

Claude 자기 검증에서만 잡힌 것: 워크트리 수 "43" 은 재지 않고 적은 숫자(실측 45) → 정정. 스택 베이스를 두 개 지정한 행 2개(HS-05.02·05.04) → 단일 베이스 + 두 사슬 합류 조건으로 교체.
