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

## 재검토 2026-09-15 — PR #96 1차 GREEN(5c71817) Codex V1 + Claude V2

V1 실행: `codex-companion.mjs adversarial-review --wait --scope branch --base origin/main` @ worktree hs-0402a HEAD 5c71817, 10:48:04~10:59:43, rc=0, verdict needs-attention. 원문 로그는 세션 스크래치 `codex-v1-96.log`, 판정 본문은 아래에 전문 보존.

| ID | Codex 판정 | Claude V2 재현(11:00:50, 제어 호출 `v2_pr96_codex.py`) | 처분 |
|---|---|---|---|
| F96-1 | 부분 해결(high) — 조상 lstat 검사와 루트 open 사이 교체 틈 | 코드 구조로 확인(`runner_boundary.py:96-115` 문자열 순회 → `:126` 전체 경로 open). 악용은 조상을 바꿀 권한(러너·root)이 필요 | 2차 GREEN 지시: `/` 부터 dir_fd 사슬로 열기 |
| F96-2 | 미해결(high) — 게시 뒤 unlink 실패·정리 unlink 실패·close 실패 | (A) `written` 인데 임시+final 잔존 (B) `denied write_failed` 인데 임시 잔존 (C) OSError 5 예외 유출 — 셋 다 REPRODUCED | 2차 GREEN 지시: cleanup_failed/recovery_required 상태, close try 안으로 |
| 추가 | medium — 자식 fstat 실패 시 FD 누수·예외 | (D) opened [3,4] closed [3] leaked [4], OSError 5 — REPRODUCED | 2차 GREEN 지시 |

V2 출력 원문:
```
=== V2 11:00:50 HEAD 5c71817
(A) post-link unlink fail : written written | names: ['.f73c31bddbfe8939.tmp', 'final']
(B) discard unlink fail   : denied write_failed | names: ['.8b40bcee8599a6e3.tmp']
(C) close fail            : EXCEPTION OSError 5 | names: ['.428524d353765102.tmp']
(D) child fstat fail      : EXCEPTION OSError 5 | opened: [3, 4] closed: [3] leaked: [4]
```
→ Codex 의 제어 호출 재현 4건을 독립 스크립트로 재현했다. V1 과장 0건, V2 가 잡은 V1 누락 0건. 2차 GREEN 뒤 V1 을 다시 돌린다.

### Codex V1 판정 전문(5c71817)

```text
# Codex Adversarial Review

Target: branch diff against origin/main
Verdict: needs-attention

VERDICT: FAIL

결론
이 변경은 아직 내보내면 안 됩니다. 검사한 장소 밖에 기록될 가능성과 실패 뒤 찌꺼기가 남는 경로가 모두 닫히지 않았습니다.

건너뜀·미확인·재시도·추정
- 실제 `hsrunner` 계정은 없어 별도 사용자 시험은 `NOT_RUN`입니다.
- 실제 OS 임시 디렉터리 시험은 읽기 전용 sandbox 때문에 실행하지 못했습니다. `uv pytest`는 캐시 권한 오류로 exit 2, 직접 pytest는 사용 가능한 임시 디렉터리 부재로 exit 1이었습니다. collect-only는 22개 시험 수집, exit 0이었습니다.
- mypy는 캐시 DB 생성 실패로 exit 2, ruff는 exit 0이었습니다.
- F96 판정 장부는 현재 branch와 origin/main에 없습니다. 별도 branch의 commit `6981035`에서 원문을 회수했으며, 이 commit은 HEAD와 origin/main 어느 쪽의 조상도 아닙니다.
- 경쟁 공격은 실제 파일시스템 재현이 아니라 운영체제 호출을 제어한 실행입니다. 실제 악용에는 검사된 조상을 교체할 권한이 있는 주체가 필요합니다.

| ID | 판정 | 이유 |
|---|---|---|
| F96-1 | 부분 해결 | 상위 symlink·sticky 없는 0777·루트 개방 뒤 교체는 방어하지만, 조상 검사와 루트 개방 사이 교체는 남았습니다. |
| F96-2 | 미해결 | 일반 쓰기 실패는 정리하지만 unlink·close 실패에서 임시 파일이 남고 성공으로도 보고됩니다. |
→ 해석: 하나라도 미해결이면 ‘검증된 경계 밖 write 0’과 ‘부분 쓰기 잔존 0’을 보장할 수 없습니다.

판단 근거
- 선택: `needs-attention`입니다. 통제 실행에서 경계 밖 게시와 임시 파일 잔존을 각각 재현했습니다.
- 버린 해석: 추가된 회귀 시험과 commit 설명만으로 해결됐다는 해석은 버렸습니다. 시험은 정확한 검사-개방 틈과 정리 실패를 때리지 않습니다.
- 틀리면 깨지는 것: 후보 원문이 승인되지 않은 위치나 숨은 임시 이름에 남고, 성공 영수증이 실제 저장 상태와 달라지며, 반복 장애에서 열린 파일 손잡이가 고갈될 수 있습니다.

반증 기록
- sticky 예외 공격: `ATTACK_STICKY None`; sticky 없는 0777 대조군은 `denied protected_root_ancestor_invalid`였습니다. 소유자 검사와 sticky 규칙 자체를 깨지는 못했습니다.
- 임시 이름 충돌: `denied write_failed`로 닫혀 경계 밖 쓰기는 없었습니다. 다만 새 이름 재시도는 하지 않습니다.
- dir_fd 제거: `not_run platform_lacks_dir_fd`로 멈춰 조용한 경로 기반 폴백은 없었습니다.
- uid 대체 코드는 두 시험 파일에만 있고 제품 코드는 실제 `pwd.getpwnam("hsrunner")`를 사용합니다.

Findings:
- [high] F96-1 원문 — 루트 검사(lstat·0700): 검사 후 교체 미방어가 남아 있습니다 (humansearch/src/humansearch/runner_boundary.py:71-126)
  원인: TOCTOU(time-of-check to time-of-use, 검사 시점과 사용 시점 사이의 교체 경쟁)가 남았습니다. `runner_boundary.py:71`—조상 검사 호출이 경로 문자열로 끝난 뒤, `runner_boundary.py:126`—루트 개방이 전체 경로를 다시 해석합니다. `O_NOFOLLOW`는 마지막 요소만 보호하므로 중간 조상의 교체를 고정하지 않습니다. 기존 `test_runner_boundary_hardening.py:126`—교체 시험은 `_ensure_parent` 반환 뒤, 즉 루트가 이미 열린 뒤에만 교체합니다.

증거 원문:
`ATTACK_ROOT_CHECK_OPEN_GAP written published_dir_fd= 20 (20=post-swap outside)`
→ 해석: 조상 검사 직후 경로 해석을 바꾸자 현재 코드가 교체 뒤 디렉터리에 최종 이름을 게시하고 `written`을 반환했습니다. 실제 OS 재현이 아닌 제어 호출 재현이며, 공격자가 해당 조상을 바꿀 권한이 있다는 전제가 필요합니다.

사업 영향: 절대 불변조건으로 내건 보호 경계 밖 write 0을 입증하지 못합니다. 또한 개방 뒤 루트가 이동하면 `runner_boundary.py:140`의 반환 경로는 실제 FD가 가리킨 파일과 달라져 후속 readback이 다른 위치를 읽을 수 있습니다.
  Recommendation: 무엇을 — `/` 또는 신뢰한 bootstrap FD부터 각 경로 요소를 `openat` 계열로 열고 즉시 `fstat`하여 다음 요소를 같은 FD 사슬에서 여십시오.
왜 — 검사한 객체와 실제 사용하는 객체를 동일하게 고정해야 합니다.
버린 길 — 현재처럼 모든 조상을 `lstat`한 뒤 전체 경로를 한 번에 여는 방식은 마지막 요소 보호만으로 충분하지 않습니다.
대가 — FD 생명주기와 플랫폼별 지원 처리가 늘어납니다.
되돌리기 — 새 FD 순회 구현을 별도 함수로 두고 실패 시 기존 구현으로 폴백하지 말고 `NOT_RUN`으로 되돌리십시오.
- [high] F96-2 원문 — `_write_new_file` except 분기: 부분 쓰기 잔존·재시도 거부가 정리 실패에서 재발합니다 (humansearch/src/humansearch/runner_boundary.py:219-285)
  원인: hard link(동일 파일을 가리키는 두 이름) 게시 뒤 `runner_boundary.py:237`에서 임시 이름 삭제 결과를 확인하지 않고, `runner_boundary.py:281-285`는 모든 unlink 오류를 삼킵니다. 실패 정리에서도 `_discard`가 같은 무시 함수를 사용합니다. `runner_boundary.py:219`의 close 오류는 보호된 예외 처리 밖에서 발생합니다.

증거 원문:
`ATTACK_POST_LINK_UNLINK_FAILURE written names= ['.3132333435363738.tmp', 'final']`
→ 해석: 최종 파일과 임시 파일이 함께 남았지만 성공으로 보고됐습니다.

`ATTACK_FAILURE_UNLINK_FAILURE denied names= ['.3132333435363738.tmp']`
→ 해석: 쓰기 실패를 반환했지만 부분 임시 파일이 남았습니다.

`ATTACK_CLOSE_FAILURE OSError 5 names= ['.3132333435363738.tmp']`
→ 해석: close 실패에서는 영수증도 반환하지 못하고 임시 파일도 정리하지 않았습니다.

사업 영향: 후보 원문이 숨은 임시 파일로 중복 잔존하고, 삭제·readback·재시도 장부가 이를 알지 못합니다. 현재의 ENOSPC 단일 시험 통과만으로 F96-2를 닫을 수 없습니다.
  Recommendation: 무엇을 — unlink·close 실패를 별도 실패 상태로 올리고, close는 `finally` 안에서 처리하며 정리 결과를 반드시 검사하십시오.
왜 — 정리에 실패했는데 `WRITTEN` 또는 일반 `DENIED`로 접으면 잔존 파일을 복구할 수 없습니다.
버린 길 — `_remove`에서 모든 `OSError`를 무시하는 방식은 폐기하십시오.
대가 — `cleanup_failed`/`recovery_required` 상태와 임시 참조를 PII 없이 기록하는 계약이 필요합니다.
되돌리기 — 새 상태를 소비자가 처리하지 못하면 배포를 중단하고 기존 성공 상태로 폴백하지 마십시오. unlink·close·게시 후 정리 실패 회귀 시험도 추가하십시오.
- [medium] 추가 결함 — 디렉터리 검증 오류에서 FD가 누수되고 경계가 영수증 없이 예외를 던집니다 (humansearch/src/humansearch/runner_boundary.py:174-187)
  원인: FD(file descriptor, 열린 파일이나 디렉터리를 가리키는 운영체제 손잡이)를 연 뒤 `runner_boundary.py:182`의 `fstat`이 실패하면 `next_fd`를 닫는 `finally`가 없습니다. 바깥 `finally`는 루트 FD만 닫습니다. 같은 구조의 close 호출도 실패를 안전한 상태로 변환하지 않습니다.

증거 원문:
`ATTACK_FSTAT_FD_LEAK OSError 5 opened= [10, 11] closed= [10] leaked= [11]`
→ 해석: 두 디렉터리를 연 뒤 두 번째 검증을 실패시키자 루트만 닫히고 자식 FD가 남았습니다.

사업 영향: 손상되거나 불안정한 파일시스템에서 요청이 반복되면 프로세스 FD 한도에 도달해 이후 저장 전체가 중단될 수 있으며, 호출자는 `BoundaryReceipt` 대신 예외를 받습니다.
  Recommendation: 각 `os.open` 직후 소유권을 명확히 하고 `try/finally` 또는 `ExitStack`으로 모든 반환·예외 경로에서 정확히 한 번 닫으십시오. `fstat`, 중간 close, 최종 close 실패를 주입해 열린 FD 수가 전후 동일하고 항상 명시적 실패 영수증이 반환되는지 시험하십시오.

Next steps:
- F96-1의 정확한 조상 검사→루트 open 틈을 실제 OS 디렉터리에서 교체하는 회귀 시험을 추가하고, 구성요소별 FD 순회로 닫으십시오.
- F96-2에 unlink 실패, 게시 뒤 정리 실패, close 실패, 고정된 임시 이름 충돌 시험을 추가하십시오.
- 실제 `hsrunner`/구현자 UID 두 개로 sticky 경계와 EACCES를 검증하고 전체 pytest·mypy를 쓰기 가능한 검증 환경에서 재실행하십시오.
- 판정 장부 commit을 대상 branch 역사에 포함하거나 현재 HEAD를 명시한 새 판정 장부를 만들어 증거 사슬을 닫으십시오.
```

## 재검토 2026-09-15 — HS-03.02 1차 GREEN(9ac10f9) Codex V1 + Claude V2

V1 실행: `codex-companion.mjs adversarial-review --wait --scope branch --base 7473ec8` @ worktree hs-0302 HEAD 9ac10f9, 10:54:01~11:01:55, rc=0, verdict needs-attention. 원문 로그 세션 스크래치 `codex-v1-0302.log`, 판정 본문은 아래 전문.

| ID | Codex 판정 | Claude V2 재현(11:03:19, 실제 임시 DB `v2_0302_codex.py`) | 처분 |
|---|---|---|---|
| F0302-1 | high AC-2 — 필드 안 `` 로 다른 후보가 같은 HMAC | `separator collision: True`, DB 기록 `inserted duplicate` rows 1 — REPRODUCED. goal 계약(구분자 결합)의 구멍 | 2차 GREEN: 제어문자 거부 + 길이 접두 직렬화 |
| F0302-2 | high — 키 파일이 DB 루트 하위면 통과 | `dbroot/keys/k` → `ACCEPTED inserted` — REPRODUCED | 2차 GREEN: 양방향 포함 거부 |
| F0302-3 | medium — RFC3339 정규식이 달력 범위 미검증 | `2026-99-99T99:99:99+99:99` → `ACCEPTED inserted` — REPRODUCED | 2차 GREEN: fromisoformat 의미 검증 |
| F0302-4 | medium — 인수 스크립트 skip_item 이 CHECKED 만 늘려 fail-open | `acceptance-hs-0302.sh:68` `skip_item(){ echo NOT_RUN; checked+=1 }` 코드로 확인 — REPRODUCED(정적) | 2차 GREEN: exit 2 |

→ V1 과장 0건, V2 가 잡은 V1 누락 0건. 기준선 정정: v8 §4-4 의 241 은 틀린 값이고 #97 워크트리·0302 베이스 모두 229 수집(28 추가 → 257).

### Codex V1 판정 전문(9ac10f9)

```text
# Codex Adversarial Review

Target: branch diff against 7473ec8
Verdict: needs-attention

VERDICT: FAIL
건너뜀·미확인·재시도: 쓰기 금지 환경 때문에 전체 pytest와 인수 스크립트는 임시 디렉터리 생성 단계에서 각각 종료값 1·2로 막혔습니다. uv 캐시 경로와 기존 가상환경 경로로 두 번 재시도했습니다. 원격 CI·push·PR은 미확인입니다. 읽기 전용 단일 시험은 `1 passed in 0.47s`, ruff와 mypy는 모두 종료값 0이었습니다.
결론: 서로 다른 후보가 한 후보로 합쳐질 수 있고, 비밀키가 데이터와 함께 놓일 수 있으므로 아직 내보내시면 안 됩니다.
판단 근거: 계약 문구의 구분자 존재만으로 경계가 안전하다는 해석은 버렸습니다. 입력 안에 같은 문자가 들어가는 실제 반례가 있기 때문입니다. 또한 ‘DB 루트와 다른 디렉터리’를 단순 동일 경로 금지로 해석하지 않았습니다. 목표 문서가 DB 루트 내부를 거부 대상으로 명시하기 때문입니다. 이 판단이 틀리면 후보 누락, 키와 데이터의 동시 유출, 잘못된 관측 입력의 조용한 수용이 발생합니다.

| 계약 | 판정 | 근거 |
|---|---|---|
| AC-1 | NOT_REPRODUCIBLE | 동일 키·동일 세 값의 계산 문제는 찾지 못했습니다. 다만 전체 DB 시험은 NOT_RUN입니다. |
| AC-2 | REPRODUCED | 허용된 두 채널과 `\x1f`가 든 두 입력 조합이 같은 HMAC를 만들었습니다. |
| AC-3 | NOT_REPRODUCIBLE | 코드는 호출마다 새 연결과 단일 INSERT를 사용하며 기본키 오류만 접습니다. 실제 경쟁 재실행은 NOT_RUN입니다. |
| AC-4 | NOT_REPRODUCIBLE | 빈 세 값·허용 밖 채널 거부 코드에는 반례가 없었습니다. 별도 입력 계약인 RFC3339 검사는 깨졌습니다. |
→ 해석: AC-2와 경계·입력 계약 결함만으로도 병합 차단입니다.

정조준 반증 기록: IntegrityError 전체 삼킴, 직접·즉시 부모 symlink 허용, 개인정보·키 값·경로가 포함된 자체 오류, 실제 파일 0개 성공, 구현 함수를 그대로 호출해 기대값을 만드는 시험, `storage_schema.py` 변경은 재현되지 않았습니다. 경쟁 시험은 두 워커가 각각 `sqlite3.connect`를 호출하는 구조지만, 쓰기 금지 때문에 연결 ID 실측은 재검증하지 못했습니다. 시험의 독립 HMAC 계산은 구현 호출을 재사용하지 않아 단순 tautology는 아니지만 구분자 주입 경우를 빠뜨렸습니다. `storage_schema.py`는 기준 SHA 대비 diff 0줄입니다.

observed_at 설계 잔여 위험(계약상 선택이므로 별도 결함에는 포함하지 않았습니다):
무엇을 — 형식만 검사하고 후보 행에는 저장하지 않습니다.
왜 — 현 스키마에 열이 없고 HS-03.04가 증거 시각을 맡기 때문입니다.
버린 길 — 버전 2 마이그레이션으로 후보 행에 시각을 추가하는 길입니다.
대가 — 후보 기록 뒤 증거 기록 전 실패하면 실제 관측 시각은 DB에서 복구할 수 없고 생성 시각만 남습니다.
되돌리기 — 후속 단계와 원자적으로 묶거나 복구 가능한 intent에 observed_at을 보존해야 합니다.

Findings:
- [high] [AC-2] 필드 안의 구분자로 서로 다른 후보 키가 충돌합니다 (humansearch/src/humansearch/candidate_identity.py:65-72)
  상태: REPRODUCED.
원문 제목: HMAC 구분자 우회로 다른 입력이 같은 기본키가 됩니다.
파일 역할: `candidate_identity.py:65-72`는 세 필드를 구분자로 이어 HMAC 입력을 만드는 부분입니다.
원인: `position_ref`와 `candidate_ref`에서 `\x1f`를 금지하거나 길이로 구획하지 않습니다. 따라서 `(a, saramin, x\x1fjobkorea\x1fy)`와 `(a\x1fsaramin\x1fx, jobkorea, y)`가 같은 바이트열이 됩니다.
사업 영향: 뒤 입력은 `duplicate`로 처리되어 서로 다른 포지션·채널·후보 중 하나가 조용히 사라집니다.
증거 원문:
`a_validated=('a','saramin','x\x1fjobkorea\x1fy')`
`b_validated=('a\x1fsaramin\x1fx','jobkorea','y')`
`hmac_a=7bf7ed72e1cc36e9bd5d146950bd1bf5084377d344395ea071cfbe0972b71e98`
`hmac_b=7bf7ed72e1cc36e9bd5d146950bd1bf5084377d344395ea071cfbe0972b71e98`
`collision=True`
→ 해석: 두 입력 모두 현재 검증을 통과하지만 AC-2가 요구한 별도 행을 만들 수 없습니다. 기존 시험 `test_hs_0302_candidate_identity.py:172-182`는 필드 안에 구분자가 없는 경우만 다뤄 이 결함을 놓칩니다.
  Recommendation: 각 필드를 길이 접두어가 있는 정규 직렬화로 인코딩하거나 모든 가변 필드에서 U+001F를 명시적으로 거부하십시오. 제시한 두 조합을 실제 DB에 연속 기록해 둘 다 `inserted`이고 행이 2개인지 확인하는 회귀 시험도 추가하십시오.
- [high] [키 경계] DB 보호 루트의 하위 디렉터리에 키를 둘 수 있습니다 (humansearch/src/humansearch/candidate_identity.py:137-144)
  상태: REPRODUCED(경로 포함 판정 분리 실행).
원문 제목: DB 루트 내부 검사가 경로 동일성만 비교합니다.
파일 역할: `candidate_identity.py:137-144`는 키 부모를 검사하고 DB 보호 루트와 분리하는 부분입니다.
원인: `key_dir.resolve() == db_path.parent.resolve()`만 거부합니다. 하위 디렉터리는 같은 보호 루트 안이어도 같지 않으므로 통과합니다. 시험 `test_hs_0302_candidate_identity.py:325-337`도 키를 DB의 즉시 부모에 둘 때만 검사합니다.
사업 영향: DB 루트 전체의 백업·복사·유출 한 번으로 데이터와 HMAC 키를 함께 가져갈 수 있어 분리 보관 목적이 무너집니다.
증거 원문:
`key_parent_inside_db_root=True`
`guard_equality=False`
`load_accepted=True bytes=22262`
→ 해석: 모드 검사 부분을 격리하고 현재 포함관계 조건만 실행했을 때, DB 루트 내부 하위 경로가 거부되지 않았습니다. 실제 0600/0700 fixture 생성은 쓰기 금지 때문에 NOT_RUN입니다.
  Recommendation: 해결된 키 경로가 DB 보호 루트와 같거나 그 하위이면 모두 거부하십시오(`is_relative_to` 포함). 즉시 부모뿐 아니라 symlink가 포함된 상위 경로도 검증하고, 직접 루트·중첩 하위·부모 symlink 반례를 추가하십시오.
- [medium] [입력 계약] 존재하지 않는 날짜와 시각을 RFC3339로 인정합니다 (humansearch/src/humansearch/candidate_identity.py:39-41)
  상태: REPRODUCED.
원문 제목: 정규식이 달력과 시간 범위를 검증하지 않습니다.
파일 역할: `candidate_identity.py:39-41`은 RFC3339 모양을 정의하고, `117-120`은 그 결과만으로 입력을 승인하는 부분입니다.
원인: 숫자의 자리수만 확인하므로 월 99, 일 99, 시·분·초 99, 오프셋 99:99도 통과합니다.
사업 영향: 잘못된 관측 시각을 가진 요청이 후보 행을 만들며, observed_at 자체는 저장되지 않아 잘못된 상류 데이터를 나중에 추적하기도 어렵습니다.
증거 원문:
`CandidateIdentityInput(... observed_at='2026-99-99T99:99:99+99:99')`
`invalid_calendar_accepted=('POS-1','saramin','cand-1')`
→ 해석: 입력 계약상 거부해야 하는 값이 `_validated_fields`에서 정상 반환됐습니다.
  Recommendation: 문자열 모양 검사 뒤 실제 날짜·시간·UTC 오프셋을 파싱해 범위를 검증하십시오. 존재하지 않는 월·일, 24시 이상, 60분·초 이상, ±24시간 이상 오프셋을 포함한 음성 시험을 추가하십시오.
- [medium] [인수 검사] 필수 검사가 NOT_RUN이어도 전체 스크립트가 성공할 수 있습니다 (scripts/acceptance-hs-0302.sh:168-170)
  상태: REPRODUCED(종료 조건 분리 실행).
원문 제목: 기준 SHA 부재와 스캔 오류가 실패 상태에 반영되지 않습니다.
파일 역할: `acceptance-hs-0302.sh:168-170`은 기준 커밋이 없을 때 스키마 동일성 검사를 건너뛰는 분기입니다. 같은 문제가 `176-178`의 create-table 스캔 오류에도 있습니다.
원인: `skip_item`은 checked만 늘리고 fail을 설정하지 않습니다. 마지막 `209-215`는 checked가 1 이상이고 fail이 0이면 종료값 0을 냅니다.
사업 영향: 얕은 checkout이나 grep 오류 환경에서 스키마 무변경·우회 테이블 검사를 하지 않고도 인수 게이트가 초록이 될 수 있습니다.
증거 원문:
`not_run_checked=1 final_rc=0`
→ 해석: NOT_RUN 한 건이 검사 건수로 계산되고 최종 성공 조건을 만족했습니다. 현재 저장소에는 기준 SHA가 있어 이 분기 전체 실행은 재현하지 않았지만, 종료 논리는 확정적으로 fail-open입니다. 반면 필수 파일 0개와 최종 checked 0은 각각 exit 2·1이므로 ‘완전한 0건 성공’은 NOT_REPRODUCIBLE입니다.
  Recommendation: 필수 비교나 스캔이 불가능하면 즉시 exit 2로 종료하고 CHECKED 성공 건수에 포함하지 마십시오. 기준 SHA 없는 얕은 저장소와 grep 오류를 주입해 래퍼까지 비정상 종료하는 회귀 시험을 추가하십시오.

Next steps:
- 구분자 주입과 DB 루트 중첩 키 경로 결함을 먼저 수정하고 각각 DB 수준 회귀 시험을 추가하십시오.
- RFC3339를 의미론적으로 검증하고 observed_at 유실 구간을 후속 intent/manifest 설계에서 복구 가능하게 하십시오.
- 인수 스크립트의 모든 필수 NOT_RUN 분기를 fail-closed로 바꾸십시오.
- 쓰기 가능한 환경에서 전체 pytest, 20회 독립 연결 경쟁, 인수 스크립트와 새 반례 변이를 다시 실행한 뒤에만 병합 판단을 갱신하십시오.
```

## 재검토 2026-09-15 — PR #96 2차 GREEN(471a936) Codex V1

실행 11:18:22~11:28:18, `--base origin/main`, verdict needs-attention. F96-1 **해결**, F96-2 부분(불일치 되돌리기에서 임시 파일 미정리·디렉터리 close 실패가 WRITTEN 뒤에 숨음), 추가 medium 부분(자식 fstat 시험의 고장 지점이 구현 변경으로 조상 검사로 이동). 새 high: 게시 경로 동일성 검사 직후 교체 시 영수증 경로가 낡음 → 영수증에 (device, inode) 안정 식별값 요구. 3차 GREEN 지시(11:31).

```text
# Codex Adversarial Review

Target: branch diff against origin/main
Verdict: needs-attention

VERDICT: FAIL

결론
지금은 내보내시면 안 됩니다. 실패했을 때 민감한 파일이 남고도 사람의 확인이 필요하다고 알리지 않으며, 성공했다고 돌려준 위치에서 파일을 찾지 못할 수도 있습니다.

건너뜀·미확인·재시도
- 현재 HEAD는 `471a9368a0f231d991959e34a0940edfe51ba655`, 기준은 `origin/main`의 `fc6beedc78019862bc2f1b3bf4c4ad3bbd8e845b`이며 작업트리 변경은 없었습니다.
- 새 시험 6건 실행은 `uv run`이 캐시 생성 권한으로 exit 2, `.venv/bin/pytest` 재시도도 쓸 수 있는 임시 디렉터리가 없어 exit 1이었습니다. 따라서 현재 HEAD의 pytest 결과는 `NOT_RUN`입니다.
- 실제 `hsrunner` 계정, 별도 사용자 권한, 실제 동시 프로세스 경주는 미확인입니다. Ruff, 구문 분석, `git diff --check`는 exit 0이었습니다.

판단 근거

| ID | 판정 | 근거 |
|---|---|---|
| F96-1 | 해결 | `/`만 이름으로 연 뒤 각 경로 요소를 앞서 연 디렉터리 기준으로 열고 검사합니다. 5c71817의 조상 검사와 루트 재개방 사이 틈은 제거됐습니다. |
| F96-2 | 부분 해결 | 게시·쓰기 실패 뒤 삭제 실패와 임시 파일 닫기 실패는 이유로 반환하지만, 경로 불일치 때 임시 파일을 남기며 디렉터리 닫기 실패도 성공 뒤에 숨습니다. |
| 추가 medium | 부분 해결 | 자식 디렉터리 검사 실패의 구현상 누수와 예외는 고쳤지만, 새 시험의 ‘두 번째 검사 실패’는 현재 코드에서 자식이 아니라 루트 조상에 걸립니다. |
| 변이 A2 | 5c71817 재현 확인 | 5c71817은 조상 검사 후 `_relative_parts`, 그 뒤 전체 루트 경로를 다시 열었습니다. 시험은 정확히 `_relative_parts` 반환 때 조상을 바꿉니다. 다만 현재 시험은 더 늦은 교체와 남은 임시 파일을 검사하지 않습니다. |

→ 해석: 최초 세 지적은 모두 완전히 닫히지 않았고, 게시·영수증 경계에서 새 차단 결함도 재현됐습니다.

선택: `FAIL`입니다. 버린 해석은 “시험 여섯 개가 추가됐으니 해결됐다”와 “경로를 한 번 비교했으니 성공 영수증이 계속 유효하다”입니다. 이 판단이 틀리면 깨지는 것은 독립 재조회, 삭제 장부, 재시도, 민감 자료의 잔여물 추적입니다.

반증 기록: 조상 교체가 다시 보호 밖 쓰기로 이어지는지 코드 순서를 공격했으나 실제 쓰기에는 전체 경로 재해석이 남지 않아 F96-1 반증에는 실패했습니다. 반면 게시 경로 확인 직후 교체, 불일치 후 정리, 디렉터리 닫기 실패는 각각 거짓 성공·고아 파일·숨은 실패를 만들었습니다.

Findings:
- [high] 게시 경로 확인이 늦은 교체를 막지 못하고 불일치 때 임시 파일도 남깁니다 (humansearch/src/humansearch/runner_boundary.py:303-331)
  원문 제목: `published_path_mismatch` 검증이 성공 영수증과 정리를 끝까지 묶지 못합니다.

원인: `runner_boundary.py:303-304`(게시 이름과 영수증 경로 비교)는 파일의 장치·inode, 즉 파일시스템 객체 식별값을 한 순간만 비교합니다. 그 직후 `runner_boundary.py:305-309`(임시 이름 삭제와 성공 반환) 사이에 같은 runner 사용자 프로세스가 루트 이름을 옮기면 `WRITTEN` 경로가 더 이상 게시 파일을 가리키지 않습니다. 반대로 비교가 실패하면 `runner_boundary.py:326-331`(되돌림)은 최종 이름만 지우고 임시 이름은 전혀 지우지 않습니다.

증거 원문:
```
MISMATCH_RECEIPT denied published_path_mismatch
MISMATCH_REMOVED_NAMES ['final.jsonl']
MISMATCH_TEMP_REMOVED False
POSTCHECK_RECEIPT written written /protected/final.jsonl
POSTCHECK_NAMESPACE_MATCHES False
```
→ 해석: 불일치 결과는 사람 확인 필요 상태가 아닌 일반 거부로 돌아가면서 임시 payload를 남기고, 비교 직후 교체에서는 실제 연결이 끊긴 경로로 성공을 반환합니다.

기존 `test_runner_boundary_failures.py:102-132`(루트 교체 시험)는 비교 전에만 루트를 바꾸고, 옮겨진 `holder/moved` 내부의 임시 파일을 검사하지 않습니다.

사업 영향: 독립 재조회와 삭제가 엉뚱한 위치를 보며, 후보 자료가 장부에 없는 고아 파일로 남을 수 있습니다.

무엇을: 성공 영수증과 게시 파일의 관계를 반환 시점까지 안정된 참조로 유지해야 합니다.
왜: 변경 가능한 경로 문자열은 한 번의 동일성 검사만으로 이후 동일성을 보장하지 못합니다.
버린 길: 현재의 단발성 절대경로 검사만으로 충분하다는 해석은 버렸습니다.
대가: 영수증에 안정 식별값을 넣고, 재조회까지 디렉터리 기준 접근을 유지하거나 이름공간을 직렬화해야 합니다.
되돌리기: 안정 참조가 불가능하면 `path`를 성공 증거로 반환하지 말고 후속 readback 성공 전까지 완료로 승격하지 않아야 합니다.
  Recommendation: 불일치 시 최종 이름과 임시 이름을 모두 제거하고 하나라도 실패하면 `recovery_required`를 반환하십시오. 동일성 검사 직후 루트를 교체하는 OS 시험과 `holder/moved`가 완전히 비었음을 확인하는 시험을 추가하고, 성공 영수증은 장치·inode 같은 안정 식별값 및 디렉터리 기준 readback에 결합하십시오.
- [medium] 디렉터리 FD close 실패는 여전히 WRITTEN 영수증 뒤에 숨습니다 (humansearch/src/humansearch/runner_boundary.py:113-117)
  원문 제목: 디렉터리 파일 디스크립터(FD, 운영체제가 열린 파일이나 디렉터리를 가리키는 번호) 닫기 실패가 관측되지 않습니다.

원인: `_close_fd()`는 모든 `OSError`를 `False`로 바꾸지만 `runner_boundary.py:113-117`(부모와 루트 정리), `144-150`(루트 사슬 정리), `205-217`(자식·오류 경로 정리)은 반환값을 버립니다. POSIX는 `close()`가 EIO를 반환하면 FD 상태가 명확하지 않다고 규정하므로 “오류여도 항상 해제된다”는 `runner_boundary.py:220-228`의 전제는 일반적으로 성립하지 않습니다. [POSIX close 규정](https://pubs.opengroup.org/onlinepubs/009604499/functions/close.html)

증거 원문:
```
DIR_CLOSE_RECEIPT written written
DIR_CLOSE_FAILURES_IGNORED [11, 10]
```
→ 해석: 부모와 루트 닫기가 모두 실패했다고 보고돼도 성공 영수증이 그대로 반환됩니다.

`test_runner_boundary_failures.py:193-197`(close 고장 주입)은 먼저 실제 `close`를 성공시킨 뒤 예외를 던지며 임시 파일 FD만 대상으로 합니다. 따라서 열린 채 남는 경우와 디렉터리 FD 실패를 검사하지 않습니다.

사업 영향: 장기 실행에서 FD가 누적돼 `EMFILE`로 후속 저장 전체가 중단될 수 있고, 운영자는 성공 영수증만 보고 원인을 추적할 수 없습니다.

무엇을: 디렉터리 닫기 실패도 반환 결과나 비민감 진단에 반영해야 합니다.
왜: 현재 boolean 반환은 모든 호출부에서 버려져 존재 이유가 없습니다.
버린 길: 예외를 무조건 다시 던져 원래 실패를 가리는 길도 적절하지 않습니다.
대가: 반환할 영수증을 먼저 보관한 뒤 정리 결과와 합성하는 구조가 필요합니다.
되돌리기: 성공을 유지해야 한다면 최소한 카운터와 경고를 남기고 반복 실패 시 실행기를 중단해야 합니다.
  Recommendation: `return` 값을 먼저 저장한 뒤 부모·루트 정리 결과를 합성하고, 성공 경로의 close 실패는 `recovery_required` 또는 별도 구조화 사유로 승격하십시오. 실제 close 전에 실패시키는 부모 FD·루트 FD 시험을 각각 추가해 성공 은폐와 누적 누수를 검증하십시오.
- [medium] 자식 fstat 실패 회귀 시험이 현재는 루트 조상 실패만 검사합니다 (humansearch/tests/test_runner_boundary_failures.py:232-243)
  원문 제목: ‘자식 디렉터리 fstat 실패’ 시험의 고장 위치가 구현 변경으로 이동했습니다.

원인: `test_runner_boundary_failures.py:232-243`(두 번째 `os.fstat` 실패)은 5c71817에서는 루트 검사 다음의 자식 디렉터리 검사에 걸렸습니다. 471a936은 `runner_boundary.py:131-148`에서 루트 경로의 모든 요소마다 `fstat`을 호출하므로, 현재 두 번째 호출은 `/` 다음 조상이며 `_ensure_parent()`의 자식 검사에는 도달하지 않습니다. 구현 자체는 `runner_boundary.py:202-209`에서 이전 FD와 새 FD를 닫도록 고쳐졌지만 그 정확한 경로의 회귀 증거는 사라졌습니다.

증거 원문:
```
if calls['n'] == 2:
    raise OSError(errno.EIO, 'Input/output error')
```
→ 해석: 호출 번호는 코드 구조가 바뀌면 의미가 달라져, 시험 이름과 실제 공격 지점이 일치하지 않습니다.

사업 영향: 이후 자식 디렉터리 검사 경로가 다시 예외를 흘리거나 FD를 남겨도 이 시험은 계속 통과할 수 있습니다.
  Recommendation: 호출 횟수 대신 `reason == 'parent_directory_invalid'`인 `_check_open_directory` 호출이나 `sub`를 연 직후 받은 FD를 식별해 그 `fstat`만 실패시키십시오. 반환 사유, 예외 부재, 각 FD 개방 수와 닫기 수가 정확히 일치하는지도 단언하십시오.

Next steps:
- 게시 경로 불일치 시 임시·최종 이름을 함께 정리하고 실패 하나라도 `recovery_required`로 승격합니다.
- 성공 반환을 디렉터리 close 결과와 합성하고 부모·루트 close 실패 시험을 추가합니다.
- 자식 fstat 시험의 고장 지점을 호출 횟수가 아닌 의미상 위치로 고정합니다.
- 쓰기 가능한 격리 환경에서 5c71817+8668d9e는 6 RED, 471a936 수정본은 6 GREEN인지 다시 실행하고 실제 별도 `hsrunner` 계정 시험은 별도로 `NOT_RUN` 해제합니다.
```

## 재검토 2026-09-15 — PR #83 1차 GREEN(3ebb38c) Codex V1

실행 11:07:32~11:28:22, `--base origin/main`, verdict needs-attention. 세 ID 전부 **부분 해결**: F83-1 조건 문구를 `linkedin_frame_lines` 에 선언하면 통과(Codex 실행 재현 4/4), F83-2 잠금 정체성이 호출자 디렉터리+packet_id 라 다른 디렉터리·cli 의 별도 packet_path 로 갈라짐(코드 경로 추정, 샌드박스로 미실행), F83-3 `CompanyBrief.revenue=Claim('경력 5년 이상')` 이 허용 집합에 들어감(실행 재현). 2차 GREEN 지시(11:33). Claude V2 재현은 아래 절.

```text
# Codex Adversarial Review

Target: branch diff against origin/main
Verdict: needs-attention

VERDICT: FAIL

건너뜀·미확인·실패 후 재시도·추정:
- 지정 판정 장부는 현재 체크아웃에 없습니다. 사용자 제공 정의와 git 이력의 6981035 판본에서 F83 행을 대조했습니다.
- 쓰기가 필요한 잠금 시험은 읽기 전용 환경 때문에 실행하지 못했습니다. pytest 최초 실행은 “No usable temporary directory”로 실패했고, 쓰기 없는 범위로 재시도해 17건 통과했습니다. F83-2의 새 우회는 코드 순서에 근거한 추정입니다.
- note 기록도 읽기 전용 제한으로 저장하지 못했습니다. 작업 트리는 깨끗합니다.
- 무음 실패 검사: 관련 경로에 skip 값, 포괄 예외 처리, 기본값 대체로 성공시키는 판정기는 없어 세 항목 모두 해당 없음입니다.

결론:
이 변경은 아직 보내시면 안 됩니다. 세 항목 모두 일부만 막혔고, 원문에 없는 채용 조건이 여전히 통과할 수 있으며, 저장 장소가 갈리면 한 번만 보내야 한다는 약속도 깨질 수 있습니다.

| ID | 판정 | 가장 강한 반증 |
|---|---|---|
| F83-1 (high) | 부분 해결 | 조건 문구 자체를 선언 목록에 넣으면 원문 검사와 JSON 왕복을 통과합니다. |
| F83-2 (high) | 부분 해결 | 같은 디렉터리 경합은 막았지만, 잠금과 청구가 호출자가 준 디렉터리별로 따로 생깁니다. |
| F83-3 (medium) | 부분 해결 | 정상 매출 오탐은 없어졌지만 조건 문구를 CompanyBrief 필드로 넣으면 허용됩니다. |
→ 해석: 세 ID 모두 ‘해결’로 닫을 수 없습니다.

판단 근거:
- 선택: 직접 재현된 F83-1·F83-3 우회와 저장 장소별로 분리되는 F83-2 보증을 출하 차단 근거로 선택했습니다.
- 버린 해석: GREEN 커밋과 기존 시험 통과만으로 닫혔다고 보는 해석은 버렸습니다. 기존 시험이 공격 입력을 선언하거나 구조화 필드에 넣은 경우를 검사하지 않습니다.
- 틀리면 깨지는 것: 승인하지 않은 자격 조건이 팀 메일에 들어가 후보 탐색이 왜곡되거나, 같은 패킷이 둘 이상의 발송 허가를 얻고 감사 기록과 저장본이 갈라집니다.

기술 상세와 증거 원문:
- 대상은 HEAD 3ebb38c, origin/main fc6beed, diff 67파일·14,079추가·7삭제입니다.
- F83-1 실행 원문: “F83-1-BYPASS [('문의: 대졸 필수', 'PASS'), ('문의: 재택근무 가능', 'PASS'), ('문의: 야간 근무 가능', 'PASS'), ('제목: 대졸 필수', 'PASS')]”.
→ 해석: 원래 정조준한 네 문구 모두 선언만 추가하면 패킷 생성과 JSON 왕복에 남습니다.
- F83-3 실행 원문: “F83-3-BYPASS True True”.
→ 해석: “- 매출: 경력 5년 이상 [I1]”이 메일에 남고 본문 해시도 일치한 채 왕복했습니다.
- 회귀 실행 원문: “17 passed in 13.94s”.
→ 해석: 정상 경로와 기존 음성 사례는 통과하지만 위 우회를 반박하지 못합니다.
- 기존 시험 3파일 대조: test_hs_1303은 선언 helper와 미선언 음성을 추가했고, test_hs_1304b는 선언 필드를 명시했으며, test_hs_1309e는 공유 잠금 import로 교체했습니다. 삭제된 판정 assertion은 없어 직접적인 약화는 확인되지 않았습니다. 다만 새 전용 시험이 각각 ‘선언된 미탐 조건’, ‘CompanyBrief 자체의 조건’, ‘서로 다른 디렉터리·프로세스’를 빠뜨렸습니다.
→ 해석: 기존 시험을 약화한 문제보다 새 방어선의 공격 범위가 부족한 문제입니다.

Findings:
- [high] F83-1 (high) linkedin_limit.py 프레임 줄 면제로 `문의: 대졸 필수` 같은 조건이 충실도 검사에서 빠짐 — 선언 기반 우회 잔존 (humansearch/src/humansearch/brief/linkedin_limit.py:307-313)
  심각도: high
원문 제목: linkedin_limit.py 프레임 줄 면제로 `문의: 대졸 필수` 같은 조건이 충실도 검사에서 빠짐.
원인: humansearch/src/humansearch/brief/linkedin_limit.py:307-313 — 선언 프레임 제외 역할에서 본문 줄이 `linkedin_frame_lines`와 정규화 후 일치하고 제한된 조건 정규식에만 걸리지 않으면 payload 검사 전에 제거합니다. 선언 필드는 호출자가 자유 문자열로 채우며 신뢰할 수 있는 렌더러와 결합되지 않았습니다. NFKC·마크다운·글머리표 정규화 때문에 선언과 본문이 원문 그대로 같지 않아도 면제 범위에 들어갑니다.
사업 영향: JD에 없는 학력·근무 형태·지원 조건이 LinkedIn 문안과 팀 메일에 승인된 내용처럼 남을 수 있습니다.
증거 원문: “F83-1-BYPASS [('문의: 대졸 필수', 'PASS'), ('문의: 재택근무 가능', 'PASS'), ('문의: 야간 근무 가능', 'PASS'), ('제목: 대졸 필수', 'PASS')]”.
→ 해석: 네 원래 공격 문구 모두 해당 문구를 선언 필드에도 넣자 패킷 생성과 JSON 왕복을 통과했습니다.
반증 기록: 선언 필드를 JSON에서 삭제하면 복원이 거부되고, 선언하지 않은 문구와 선언했더라도 ‘경력 10년 이상’처럼 현재 정규식이 아는 조건은 거부됩니다. 따라서 왕복 탈락과 알려진 조건은 닫혔지만, 정규식이 모르는 선언 조건은 닫히지 않았습니다.
  Recommendation: 자유 문자열 `linkedin_frame_lines`를 면제권으로 사용하지 마십시오. 제목·문의 줄을 PositionSpec과 계약된 담당자 필드에서 렌더러가 직접 도출하는 타입으로 바꾸고, 공격자가 선언값을 공급할 수 없게 하십시오. HIDDEN_CONDITIONS 네 문구를 각각 선언한 경우와 마크다운·전각·공백 정규화 변형이 모두 거부되는 시험을 추가하십시오.
- [high] F83-2 (high) PacketStore.save 잠금 없음 → 승인 digest와 저장 패킷 분리 — 잠금 디렉터리별 새 우회 (humansearch/src/humansearch/brief/packet.py:303-327)
  심각도: high
원문 제목: PacketStore.save 잠금 없음 → save(B) 확인 → record_intent(A)+claim_send(A) → save(B) 교체로 승인 digest와 저장 패킷이 갈라짐.
원인: 같은 디렉터리에서는 humansearch/src/humansearch/brief/packet.py:342-386 — 패킷→채널 순서의 파일 잠금과 확인 전후 attempt 집합 대조가 원래 경합을 막습니다. 그러나 packet.py:303-304의 잠금 경로는 호출자가 준 디렉터리에 종속되고, PacketStore·claim_send·verify_and_mark는 같은 정규 경로를 강제하지 않습니다. cli.py:162-180은 `dir`을 잠근 뒤 별도 `packet_path`를 읽습니다. 서로 다른 디렉터리에는 같은 packet_id라도 별도 잠금·intent·claim 마커가 생기므로 상호 배타가 없고, 잠금 안에서 읽은 별도 패킷도 이후 교체될 수 있습니다.
사업 영향: 같은 패킷이 디렉터리마다 한 번씩 발송 허가를 얻어 중복 메일이 나가거나, VERIFIED 기록이 사용자가 지정한 현재 패킷 파일과 달라질 수 있습니다.
반증 기록: 같은 디렉터리의 잠금 순서는 패킷→채널 하나로 통일됐고 코드 내부 잠금 삭제 함수도 없습니다. 기존 시험은 스레드·같은 디렉터리만 사용합니다. 실제 두 디렉터리·두 프로세스 재현은 읽기 전용 샌드박스 때문에 실행하지 못했으므로 이 finding은 코드 경로 추정입니다.
무엇을: 패킷과 장부 루트를 하나의 정규 Store 객체로 묶고 모든 API가 그 객체만 받게 하십시오.
왜: 현재 잠금의 정체성이 packet_id가 아니라 ‘호출자 디렉터리+packet_id’이기 때문입니다.
버린 길: 운영자가 항상 같은 경로를 넣는다는 규율과 마지막 해시 재검사만 믿는 길은 코드 불변식이 아니므로 버렸습니다.
대가: Path 기반 공개 함수 시그니처 이전과 기존 호출부·fixture 수정이 필요합니다.
되돌리기: Store 전환을 되돌리려면 보증을 ‘디렉터리별 1회’로 명시적으로 낮추고 교차 디렉터리 verify를 거부해야 합니다.
  Recommendation: 모든 경로를 `resolve()`한 단일 저장 루트에 결합하고 `verify_and_mark`에서 `packet_path == root/<id>.packet.json`을 강제하십시오. 서로 다른 두 디렉터리에 같은 패킷을 둔 뒤 두 claim 중 정확히 하나만 성공하는 시험, packet 재읽기 직후 다른 프로세스가 교체하는 시험, 실제 multiprocessing 기반 배타·교착 시험을 추가하십시오.
- [medium] F83-3 (medium) 회사 리서치 절의 `- 매출: 300억 원 [I1]` 오탐 — CompanyBrief 조건 주입 우회 (humansearch/src/humansearch/brief/types_packet.py:345-353)
  심각도: medium
원문 제목: 회사 리서치 절의 `- 매출: 300억 원 [I1]`이 채용 조건으로 오탐.
원인: humansearch/src/humansearch/brief/types_packet.py:345-353 — 회사 절의 줄이 `render_company_research` 결과와 일치하면 조건 검사 전체를 건너뜁니다. Claim은 types.py:113-126에서 비어 있지 않은 값과 출처 ID 형식만 확인하므로, `CompanyBrief.revenue=Claim('경력 5년 이상', ('I1',))`처럼 조건을 구조화 필드에 넣으면 그 줄 자체가 허용 집합에 들어갑니다.
사업 영향: 회사 사실로 위장한 자격 조건이 내부 브리프에 남아 후보 선별 기준으로 오용될 수 있습니다.
증거 원문: “F83-3-BYPASS True True”.
→ 해석: “- 매출: 경력 5년 이상 [I1]”이 패킷과 JSON 왕복을 통과했고 본문 해시도 정상입니다.
반증 기록: 정상 `300억 원` 줄은 통과하고, CompanyBrief가 렌더링하지 않은 조건 줄과 변조한 `999억 원` 줄은 기존 시험에서 거부됩니다. 조건을 메일 본문에 직접 넣는 공격은 실패하지만 같은 값을 CompanyBrief에 먼저 넣는 공격은 성공합니다.
  Recommendation: ‘렌더러가 만들었음’을 조건 검사 면제로 쓰지 마십시오. 회사 줄에도 채용 조건 검사를 계속 적용하되 revenue·funding_total 같은 필드에서 허용할 회사 금액 형식만 필드별로 좁게 제외하십시오. CompanyBrief의 모든 단일·목록 필드에 경력·학력·연봉·근무 조건을 넣어 패킷과 JSON 왕복이 거부되는 시험을 추가하십시오.

Next steps:
- F83-1의 선언 문자열 우회와 F83-3의 CompanyBrief 주입 우회를 먼저 RED 시험으로 고정하십시오.
- 저장 루트를 단일 객체로 결합하고 서로 다른 디렉터리·실제 프로세스 경합을 F83-2 시험에 추가하십시오.
- 세 반례가 실패하고 관련 전체 pytest·ruff·mypy가 쓰기 가능한 환경에서 새로 통과하기 전에는 병합하지 마십시오.
```

### Claude V2 재현 — PR #83 3ebb38c (11:30:24, `v2_pr83_codex.py`)

```
F83-1 declared [문의: 대졸 필수]: PASSED_THROUGH in body=True
F83-1 declared [문의: 재택근무 가능]: PASSED_THROUGH in body=True
F83-1 declared [문의: 야간 근무 가능]: PASSED_THROUGH in body=True
F83-1 declared [제목: 대졸 필수]: PASSED_THROUGH in body=True
F83-3 revenue='경력 5년 이상': PASSED_THROUGH | line in body: True
```
→ Codex 의 F83-1 선언 우회 4건과 F83-3 CompanyBrief 주입 1건을 독립 스크립트로 재현했다(REPRODUCED). F83-2 디렉터리 분리는 코드 경로(`packet.py:303` 잠금 경로가 호출자 dir 종속, `cli.py:162-180` 별도 packet_path)로 확인. V1 과장 0건.

## 재검토 2026-09-15 — PR #96 3차 GREEN(be20d9b) Codex V1

실행 11:41:34~11:52:02, verdict needs-attention. **F96-2 해결**, 디렉터리 close 은폐 해결, 자식 fstat 시험 해결. 남은 high 1건: 게시 확인 직후 최종 이름 교체 시 영수증이 원문 A 해시 + 교체 파일 B 식별값이 됨(임시 FD fstat 값을 _publish 에 안 넘김) + "식별값으로 재조회" 주장에 소비자 없음. 4차 지시(11:54).

```text
# Codex Adversarial Review

Target: branch diff against origin/main
Verdict: needs-attention

VERDICT: FAIL

결론
이 변경은 아직 합치면 안 됩니다. 저장했다고 돌려준 결과가 실제로 저장한 내용이 아닌 교체된 파일을 가리킬 수 있고, 나중에 그 파일을 다시 찾는 방법도 제공하지 않습니다.

판정 전 제한
- 건너뜀: 실제 `hsrunner` 계정 실증과 원격 CI는 범위·환경상 실행하지 못했습니다.
- 미확인: `origin/main=fc6beed`는 로컬 추적 참조이며 원격 최신성은 네트워크 제한으로 확인하지 못했습니다.
- 실패 후 재시도: 표적 pytest는 쓰기 가능한 임시 디렉터리가 없어 수집 전에 exit 1이었습니다. 같은 제한에서 무의미한 재시도 대신 `--collect-only`, ruff, mypy, diff 검사와 메모리 기반 반례로 전환했습니다.
- 추정: 최종 이름 교체 경쟁은 실제 파일시스템으로 실행하지 못했지만, 해당 시점의 메서드 반환값을 교체해 같은 제어 흐름을 재현했습니다.

판단 근거
- 선택: `REQUEST_CHANGES`에 해당합니다. 페이로드(payload, 저장 요청의 원문 바이트)의 식별값을 버린 뒤 변경 가능한 최종 이름에서 식별값을 다시 읽어 성공 처리합니다.
- 버린 해석: 디바이스(device, 파일시스템 장치 번호)와 아이노드(inode, 파일시스템 내부 객체 번호) 쌍만 있으면 경로 없이 파일을 다시 열 수 있다는 해석을 버렸습니다. 현재 플랫폼에는 그 쌍을 받아 여는 API가 없고 저장소에도 소비자가 없습니다.
- 틀리면 깨지는 것: 영수증의 해시는 원문 A, 경로와 식별값은 교체 파일 B가 되어 독립 재조회·감사·삭제가 잘못된 파일을 대상으로 할 수 있습니다.

2차 잔여 3건 최종 상태
| 항목 | 상태 | 근거 |
|---|---|---|
| high: 불일치 되돌리기·낡은 영수증 경로 | 부분 | 최종·임시 이름 정리와 실패 승격은 해결됐으나, 식별값이 작성 원문에 묶이지 않고 경로 없는 재조회 소비자가 없습니다. |
| medium: 디렉터리 FD close 실패가 WRITTEN 뒤에 숨음 | 해결 | 파일 디스크립터(FD, 열린 파일·디렉터리를 가리키는 운영체제 손잡이)인 부모·루트 닫기 실패를 `DENIED/recovery_required`로 바꾸고 path·device·inode를 보존합니다. |
| medium: 자식 fstat 시험이 호출 횟수 기반 | 해결 | fstat(열린 손잡이의 파일 정보를 읽는 호출) 실패 대상이 `sub`를 열어 받은 FD 집합으로 고정됐습니다. |
→ 해석: 첫 항목의 두 하위 문제 중 정리만 닫혔으므로 전체 판정은 부분 해결입니다.

원래 ID 최종 상태
| ID | 상태 | 근거 |
|---|---|---|
| F96-1 | 부분 | 루트·조상 치환에 따른 보호 밖 쓰기는 FD 사슬로 막았지만, 게시 뒤 이동된 파일을 영수증만으로 다시 찾는 계약은 닫히지 않았습니다. |
| F96-2 | 해결 | 중단 쓰기와 정리 실패는 최종 성공으로 접히지 않으며, 삭제 실패는 `recovery_required`가 됩니다. |
→ 해석: F96-1의 쓰기 경계는 좋아졌지만 재조회까지 포함한 증거 사슬은 미완성입니다.

새 시험 6건 평가
| 시험 | 평가 |
|---|---|
| 불일치 시 두 이름 제거 | 코드와 단언이 최종·임시 잔여 0건을 확인합니다. |
| 불일치 정리 실패 | 임시 이름 삭제 실패를 주입해 `recovery_required`를 확인합니다. 최종 삭제 실패는 시험하지 않지만 코드가 두 삭제를 모두 호출함을 별도 반례로 확인했습니다. |
| 성공 영수증 device/inode | 정상 시점 일치만 확인하며 게시 이름 교체 경쟁은 잡지 못합니다. |
| 늦은 루트 이동 뒤 식별값 탐색 | fixture가 알고 있는 `holder/moved`를 직접 순회합니다. 제품 소비자가 영수증만으로 같은 탐색을 할 수 있다는 증거가 아닙니다. |
| 부모 FD close 실패 | `os.close`를 부르기 전에 EIO를 발생시킵니다. 올바른 고장 주입입니다. |
| 루트 FD close 실패 | `os.close`를 부르기 전에 EIO를 발생시킵니다. 올바른 고장 주입입니다. |
→ 해석: close 관련 두 시험은 실제 close 이전 고장을 검증하지만, 식별값 관련 두 시험은 핵심 재조회·교체 경쟁을 증명하지 못합니다.

`_open_root_chain`과 `_ensure_parent` 중간 close 실패는 별도 신규 시험이 없습니다. 다만 메모리 주입에서 각각 `denied/protected_root_ancestor_invalid`, `denied/parent_directory_invalid`로 성공 전에 차단됐습니다.

크기 한도
| 대상 | 실측 | 판정 |
|---|---:|---|
| `runner_boundary.py` | 445줄 | soft 300 초과, hard 600 이내 |
| 최장 함수 `_ensure_parent` | 37줄 | hard 100 이내 |
| origin/main 대비 전체 diff | +2536/-3, 합계 2539줄 | PR hard 3000 이내 |
→ 해석: 크기 hard 한도 위반은 없습니다.

증거 원문
- 표적 pytest: `FileNotFoundError: No usable temporary directory found ...`, exit 1.
→ 해석: 코드 실패가 아니라 실행 환경 제한이므로 런타임 PASS로 인정하지 않았습니다.
- 대체 검증: `12 tests collected`, `All checks passed!`, `Success: no issues found in 3 source files`, diff-check 출력 없음, exit 0.
→ 해석: 시험 수집·ruff·mypy·공백 검사는 통과했지만 파일 동작 시험을 대신하지 않습니다.
- 반증 성공: `UNDO_ONE_FAIL denied recovery_required ['final', '.abc.tmp']`.
→ 해석: 최종 삭제가 실패해도 임시 삭제를 시도하고 복구 필요 상태로 반환합니다.
- 반증 성공: `OPEN_CHAIN_CLOSE_FAIL denied protected_root_ancestor_invalid`, `ENSURE_PARENT_CLOSE_FAIL denied parent_directory_invalid`.
→ 해석: 중간 디렉터리 close 실패는 쓰기 성공으로 진행되지 않습니다.
- 결함 재현: `IDENTITY_SWAP written sha-of-payload-A 99 123`.
→ 해석: 작성 원문의 식별값을 대조하지 않아 임의의 최종 이름 식별값과 원문 A의 해시를 함께 성공 영수증으로 만들 수 있습니다.
- 검토 전후 HEAD `be20d9b108e7c3463f78d9705d31b6ee50adaaa2`, 추적 작업트리 변경 0건입니다.

Findings:
- [high] [원문 high — 부분 해결] 성공 영수증이 작성한 원문이 아닌 교체 파일을 가리킬 수 있으며 식별값만으로 재조회할 수 없습니다 (humansearch/src/humansearch/runner_boundary.py:291-356)
  원인: `runner_boundary.py:291-299 — 임시 파일 검증 역할`에서 `_fill_temp_file`이 얻은 원문 파일의 stat 결과를 검사한 뒤 `_publish`에 전달하지 않습니다. `runner_boundary.py:346-356 — 게시 확인과 영수증 생성 역할`은 변경 가능한 최종 이름을 다시 stat하여 그 식별값을 원문 해시와 결합합니다. 같은 runner UID의 동시 실행이 `_published_path_matches` 직후 최종 이름을 교체하면, 영수증은 원문 A의 sha256과 교체 파일 B의 device/inode를 `WRITTEN`으로 반환할 수 있습니다. 이는 코드 흐름과 메모리 주입 결과에 기반한 추론입니다.

또한 `BoundaryReceipt`의 설명은 식별값이 경로를 대신한다고 주장하지만, 저장소 검색상 이를 소비하는 재조회 함수는 없고 시험은 fixture가 미리 아는 이동 경로를 순회합니다. device/inode는 후보 경로를 연 뒤 동일성을 확인하는 값이지, 현재 지원 플랫폼에서 그 자체로 파일을 여는 위치 정보가 아닙니다.

사업 영향: 독립 재조회가 다른 파일을 정상 원문으로 승인하거나, 감사·복구·삭제가 잘못된 파일을 대상으로 삼을 수 있습니다. 저장 성공 장부와 실제 후보 원문이 분리되는 데이터 무결성 결함입니다.

무엇을 — 영수증 식별값을 작성한 임시 파일의 열린 FD에서 얻은 식별값에 직접 묶고 실제 재조회 소비 경계를 추가해야 합니다.
왜 — 변경 가능한 최종 이름을 다시 읽는 것만으로는 원문과 영수증의 동일성을 증명하지 못합니다.
버린 길 — device/inode만 저장하고 소비자가 전체 디렉터리를 탐색하게 하는 길은 이동 위치를 알아야 하며 inode 재사용도 막지 못해 버립니다.
대가 — 임시 FD를 게시·검증까지 유지하거나, 경로를 locator로 사용하되 device/inode와 sha256을 검증값으로 쓰는 별도 readback API가 필요합니다.
되돌리기 — 소비 계약이 준비되지 않으면 ‘경로 대신 식별값’ 주장을 되돌리고 늦은 이동 상황을 성공으로 보고하지 않아야 합니다.
  Recommendation: `stored`의 `(st_dev, st_ino)`를 `_publish`에 전달하고 게시된 최종 항목이 그 값과 일치하는지 비교하십시오. `_published_path_matches` 반환 직후 최종 이름을 다른 0600 일반 파일로 교체하는 시험을 추가해 `WRITTEN`을 금지하십시오. 이어서 pinned root/parent FD로 경로를 열고 device/inode와 sha256을 함께 검증하는 실제 readback API를 제공하거나, 이동 후 경로 없이 찾을 수 있다는 계약을 제거하십시오.

Next steps:
- 이 finding이 닫히기 전에는 병합하지 마십시오.
- 쓰기 가능한 임시 디렉터리 환경에서 표적 pytest 전체를 다시 실행하고 종료값 0을 확보하십시오.
- `_open_root_chain`과 `_ensure_parent`의 중간 FD close-before-close 고장을 각각 직접 고정하는 회귀 시험을 추가하십시오.
- 원격 origin/main 최신성, PR CI, 실제 hsrunner UID 경계는 별도 증거로 확인하십시오.
```

### Claude V2 재현 — PR #83 2차 GREEN 5576b02 (12:11:38, `v2_pr83_r2.py`)

```
[codex] 문의: 대졸 필수 + contact.name='대졸 필수': REJECTED
[codex] 문의: 재택근무 가능 + contact.name='재택근무 가능': REJECTED
[codex] 문의: 야간 근무 가능 + contact.name='야간 근무 가능': REJECTED
[codex] 제목: 대졸 필수 + contact.name='대졸 필수': REJECTED
[ok] 문의: 홍길동 (x@example.kr): PASSED_THROUGH
[residual1] 문의: 대졸 필수 (x@example.kr) + contact.name='대졸 필수': PASSED_THROUGH
[residual2] 제목: 대졸 필수 + position.title='대졸 필수': REJECTED (구현자 probe 는 PASS — 구성 차이, V1 2차가 판정)
[F83-3] revenue/funding_total/headcount/ceo='경력 5년 이상': 전부 REJECTED
```
→ Codex 1차 우회 4건과 CompanyBrief 주입은 닫혔다. 구현자가 스스로 보고한 잔여 구멍(담당자 이름 칸에 정규식이 모르는 조건 문구 + 본문을 렌더 형식으로; 완전히 다른 두 디렉터리)은 신뢰 경계(Contact·position.title 이 운영자 설정값인지 LLM 산출물인지) 결정 사항으로 §7-5 카드에 올린다.

### Claude V2 재현 — HS-03.02 2차 GREEN 3061bd3 (12:08, `v2_0302_codex_after_green.py`)

지시 모순 정정: 제어문자 거부(b)와 "Codex 충돌 쌍 둘 다 inserted"(a)는 양립 불가(쌍 자체가  를 담음). 구현자가 (b) 거부를 택하고 합법 경계쌍 ab/c vs a/bc 가 별도 2행인 DB 회귀 시험을 추가했다. 팀리드가 이 해석을 승인.
```
(1a) separator collision : False | (1b) A·B 둘 다 REJECTED control characters | (1c) rows 0
(1d) legal pair ab/c, a/bc 둘 다 inserted | (1e) rows 2
(2) key under db root : REJECTED | (3) 2026-99-99T99:99:99 : REJECTED
```
→ 4건 전부 뒤집혔다. 인수 스크립트 실행 2.99초, CHECKED 11(구현자 보고: 변이 M5 에서 인수 스크립트의 pytest 단계가 자기 호출 시험을 돌려 프로세스 1,493개 폭증·612초 타임아웃 2회 → deselect 로 순환 제거·깊이 차단을 변이 대상과 분리·subprocess timeout 300초).

## 재검토 2026-09-15 — PR #96 4차 GREEN(b3cbb08) Codex V1

실행 12:07:23~12:14:53, verdict needs-attention. 3차 잔여 high(IDENTITY_SWAP·재조회 주장) **둘 다 해결**. 새 high 1건: 게시 대조 실패 시 `_undo_publication`/`_roll_back` 이 최종 이름을 무조건 unlink 해 같은 UID 다른 실행의 파일 B 를 삭제 가능(데이터 안전, WU 계약 범위 안). 5차 지시(12:17): 소유 증명 없는 최종 이름 삭제 금지·A 되돌리기 폐지.

```text
# Codex Adversarial Review

Target: branch diff against origin/main
Verdict: needs-attention

VERDICT: FAIL
결론: 기존 두 문제는 해결됐습니다. 그러나 불일치를 되돌리는 과정에서 다른 실행이 만든 파일을 지울 수 있어 아직 배포하면 안 됩니다.

미확인·재시도: pytest는 uv 캐시 쓰기 거부 후 직접 실행도 사용 가능한 임시 디렉터리가 없어 수집 전에 실패했습니다. mypy는 내부 오류로 실패했습니다. ruff와 `git diff --check origin/main...HEAD`는 통과했습니다. 실제 별도 UID 시험은 이 WU 밖이며 계속 NOT_RUN입니다. 따라서 실행 성공은 주장하지 않고 코드·커밋별 경로 대조로 판정했습니다.

판단 근거: F96-1은 임시 파일 디스크립터의 `fstat` 결과와 게시 항목의 장치·아이노드(device/inode, 파일시스템 객체 식별 쌍)를 비교하고, 영수증도 그 디스크립터 값으로 만들므로 해결입니다. F96-2는 식별값을 위치 탐색값이 아닌 대조값이라고 바로잡아 해결입니다. ‘교체 파일 B는 공격 산물이므로 삭제해도 된다’는 해석은 버렸습니다. 시험 자체가 B를 같은 UID의 다른 실행이 만든 파일이자 ‘우리가 만든 것이 아님’으로 규정하기 때문입니다. 이 판단이 틀리면 동시 실행이 보존한 후보 원문이나 영수증이 복구 과정에서 사라집니다.

| ID | 최종 상태 |
|---|---|
| F96-1 IDENTITY_SWAP | 해결 |
| F96-2 식별값으로 재조회 주장 | 해결 |
→ 해석: 3차의 잔여 HIGH 자체는 닫혔지만, 4차에서 같은 경쟁 경로의 별도 데이터 삭제 결함이 남았습니다.

기술 증거: `runner_boundary.py:316-323 — 페이로드 FD를 fsync한 뒤 fstat하는 역할`, `:358-376 — 게시 이름과 그 식별값을 대조하는 역할`, `:362-365 — 최종 이름을 다시 읽지 않고 FD 값으로 영수증을 만드는 역할`입니다. 대조 뒤 영수증 생성 전 최종 이름 stat은 없고 임시 이름 제거만 있습니다. `:378-387 — 불일치 정리 역할`은 최종·임시 제거 중 하나라도 실패하면 recovery_required로 승격합니다. `:177-182 — 루트 사슬 중간 close 실패를 조상 오류로 귀속하는 역할`, `:239-246 — 부모 사슬 중간 close 실패를 부모 오류로 귀속하는 역할`도 맞습니다.

신규 시험 5건을 모두 과거 RED라고 볼 수는 없습니다. c864d1f의 커밋 원문은 ‘현재 HEAD에서 2개가 실패하고 계약·회귀 시험 2개는 통과’라고 명시하고, b3cbb08도 ‘be20d9b 구현에서도 통과한다. RED가 아니라 변이를 잡기 위한 계약 시험’이라고 명시합니다. 실제 파일 교체는 `test_final_name_taken_over_after_check...`와 `test_receipt_identity_is_not_re_read...` 두 건이며, 전자만 be20d9b를 RED로 만듭니다. 후자는 늦은 재읽기 변이를 막습니다. 나머지는 정상 출처 확인 1건과 close 실패 2건이고, close 중 조상 이유 귀속 1건만 be20d9b에서 RED입니다.
→ 해석: 시험 이력의 표현은 정직하지만, 교체본 B가 보존되는지는 시험하지 않습니다.

범위: 아래 HIGH는 `runner_boundary.py`의 게시·되돌리기 동작이므로 HS-04.02a 러너 쓰기 경계 안입니다. 실제 hsrunner 계정 생성, 구현자 EACCES와 runner 성공 실증은 계약대로 이 WU 밖입니다.

Findings:
- [high] 게시 불일치 복구가 다른 실행의 교체 파일 B를 삭제합니다 (humansearch/src/humansearch/runner_boundary.py:356-409)
  원문 제목: 게시 불일치 복구가 교체 파일 B를 삭제합니다.

원인: `_published_entry_is()`가 최종 이름이 원문 A가 아님을 확인한 직후 `_undo_publication()`은 그 이름이 누구 것인지 구분하지 않고 삭제합니다. 시험은 B를 같은 UID의 다른 실행이 만든 파일이라고 규정하면서도 B의 생존을 단언하지 않아 이 삭제를 통과시킵니다. 임시 이름 정리 실패 뒤 `_roll_back()`도 같은 방식으로 현재 최종 이름을 무조건 삭제합니다.

증거 원문:
`if not self._published_entry_is(parent_fd, name, written): return self._undo_publication(...)`
`removed_final = self._remove(parent_fd, name)`
→ 해석: 불일치가 바로 ‘현재 이름은 우리 파일이 아닐 수 있다’는 증거인데도 그 파일을 삭제합니다.

사업 영향: 같은 러너 계정으로 겹쳐 실행된 저장 작업의 후보 원문·영수증을 되돌릴 수 없게 삭제할 수 있습니다. 실패를 안전하게 보고하는 수준을 넘어 보호 저장소의 타 작업 데이터를 훼손합니다.

무엇을 — 불일치나 정리 실패 시 현재 최종 이름을 무조건 unlink하지 않도록 바꾸셔야 합니다.
왜 — 대조 실패 뒤 최종 이름은 이미 다른 작성자의 파일일 수 있습니다.
버린 길 — unlink 직전 stat만 한 번 더 하는 방식은 검사 시점과 삭제 시점 사이 경쟁 창을 그대로 남겨 버립니다.
대가 — 게시 구간을 같은 디렉터리의 협력적 잠금으로 직렬화하거나, 소유를 증명할 수 없으면 파일을 남기고 recovery_required로 넘겨야 합니다.
되돌리기 — 최종 이름의 무조건 삭제를 제거하고, B의 내용·식별값이 보존됨을 실제 파일 교체 시험으로 고정하면 됩니다.
  Recommendation: `_undo_publication`과 `_roll_back`이 소유가 불확실한 최종 이름을 삭제하지 않게 하십시오. 게시 구간을 잠금으로 직렬화하거나, 확실한 소유 증명이 없으면 임시 파일만 안전하게 처리하고 `recovery_required`를 반환하십시오. 교체 파일 B가 그대로 남고 원문 A의 임시 이름 처리 결과가 명시되는 실제 파일시스템 시험을 추가하십시오.

Next steps:
- 최종 이름 무조건 삭제를 제거하거나 게시 구간에 협력적 잠금을 도입합니다.
- 교체 파일 B의 내용과 식별값이 보존되는지, 정리 실패가 recovery_required인지 시험합니다.
- goal 문서의 ‘반환값은 path/status/reason/sha256/byte count만’ 문구를 실제 device/inode 계약과 맞춥니다.
- 쓰기 가능한 검증 환경에서 전체 pytest와 과거 커밋 RED 행렬을 다시 실행합니다.
```

## 재검토 2026-09-15 — HS-03.02 2차 GREEN(3061bd3) Codex V1

실행 12:08:43~12:15:57, `--base 7473ec8`, verdict needs-attention. F0302-1 해결·F0302-3 해결·F0302-2 부분(DB 파일 마지막 구성요소 symlink 미검사)·F0302-4 부분(자기 호출 시험 2건 deselect, 통과 하한을 함수 수로). 신규 high: 인수 스크립트가 verify.yml·verification-commands.md 미배선(정본 53행). 신규 medium: NFC 미정규화로 같은 후보 2행. 3차 지시(12:20).

```text
# Codex Adversarial Review

Target: branch diff against 7473ec8
Verdict: needs-attention

지금은 내보내시면 안 됩니다. 1차 4건 판정은 F0302-1 해결, F0302-2 부분 해결, F0302-3 해결, F0302-4 부분 해결입니다. 건너뜀·미확인: 전체 pytest와 인수·변이 검증은 읽기 전용 환경 때문에 실행하지 못했습니다. `uv run pytest`는 캐시 쓰기 거부(rc=2), `.venv/bin/pytest` 재시도는 `No usable temporary directory`(rc=1)였습니다. 대신 현재 HEAD 3061bd3·깨끗한 작업트리·7473ec8 대비 5파일/1592줄 추가, ruff 성공, 셸 문법 성공, `storage_schema.py` SHA 동일을 확인했습니다. 직접 실행 결과 제어문자는 strip 전에 거부됐고, HMAC은 독립 계산한 4바이트 big-endian 길이 접두값과 일치했으며 구분자·합법 경계쌍 충돌도 없었습니다. 버린 해석은 과거 검증 장부만으로 현재 합격을 인정하는 것, 호출자가 언제나 안전한 DB 경로만 준다고 가정하는 것, 글자가 같아 보이면 바이트 차이를 무시해도 된다는 것입니다.

Findings:
- [high] F0302-2 [high] 키 파일이 DB 루트 하위면 통과 — DB 파일 심볼릭 링크로 경계를 우회할 수 있습니다 (humansearch/src/humansearch/candidate_identity.py:188-194)
  원인: 키 쪽은 해석된 디렉터리를 쓰지만 DB 쪽은 `db_path.parent.resolve()`만 검사하고 마지막 DB 파일 자체는 해석하거나 심볼릭 링크인지 확인하지 않습니다. 이후 `sqlite3.connect(db_path)`는 마지막 링크를 따라갑니다.

증거 원문:
`key_root = key_dir.resolve(strict=True)`
`db_root = db_path.parent.resolve(strict=True)`
`sqlite3.connect(db_path, isolation_level=None)`
또한 로컬 확인에서 `/dev/stdin`은 `parent.resolve()=/dev`, 파일 전체 `resolve()=/dev/fd/0`으로 달랐습니다.
→ 해석: 별도 디렉터리의 `alias/humansearch.sqlite3`를 키 디렉터리 안 실제 DB로 연결하면 비교 대상은 alias 디렉터리지만 쓰기는 키와 같은 실제 루트의 DB에 도달합니다. 파일 생성이 금지된 환경이라 전체 DB 재현은 미확인이고, 코드·경로 의미론에 따른 추론입니다.

사업 영향: DB와 HMAC 키를 한 번에 복사·유출할 수 있어 보호 루트 분리 목적이 무너지고, 유출된 후보 식별값의 대입 검증이 가능해집니다.

무엇을: DB 파일과 상위 경로도 링크 없이 검증하고 실제 DB 위치를 기준으로 비교해야 합니다.
왜: 검사한 경로와 실제로 연 파일이 같아야 경계 검사가 성립합니다.
버린 길: 호출자가 초기화 함수 반환값만 전달한다고 가정하는 방식은 공개 함수 경계를 보호하지 못합니다.
대가: 기존에 링크된 DB를 사용하던 호출은 거부됩니다.
되돌리기: DB 경로 검증을 별도 보조 함수로 격리하면 정책 변경 시 그 경계만 되돌릴 수 있습니다.
  Recommendation: `db_path`의 모든 구성요소와 마지막 파일의 symlink를 거부하고, `db_path.resolve(strict=True).parent`를 키 루트와 양방향 비교하십시오. 가능하면 검증한 파일 descriptor를 사용해 검사 후 교체 경쟁도 막고, DB 최종 구성요소 symlink·조상 symlink·hard-link 경계를 회귀 시험으로 추가하십시오.
- [high] 신규 [high] 새 인수 검사가 CI의 고정 실행 목록에 연결되지 않았습니다 (.github/workflows/verify.yml:227-231)
  원인: `scripts/acceptance-hs-0302.sh`를 추가했지만 `.github/workflows/verify.yml`과 `docs/sot/verification-commands.md`에는 실행 항목이 없습니다.

증거 원문:
`rg -n "acceptance-hs-0302" .github/workflows/verify.yml docs/sot/verification-commands.md` → 0건
정본 53행: `새 scripts/acceptance-*.sh를 추가하는 PR은 verify.yml과 이 표 양쪽에 자기 줄을 함께 넣어야 한다.`
→ 해석: 로컬 pre-push 글로브에서는 실행되지만, 우회 가능한 로컬 훅과 달리 최종 판정권을 가진 CI는 이 인수 검사를 직접 실행하지 않습니다.

사업 영향: HMAC 의미 검사, 스키마 무변경 검사, 우회 테이블 검사와 fail-closed 자기 검사가 CI에서 빠진 채 병합될 수 있습니다. 저장소의 P15 배송 규칙을 직접 위반합니다.
  Recommendation: `verify.yml`에 `bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-0302.sh` 전용 단계를 추가하고 `docs/sot/verification-commands.md` 명부도 함께 갱신하십시오. CI 배선 제거·echo 대체 변이가 실패하는지도 확인하십시오.
- [medium] F0302-4 [medium] 인수 스크립트 skip_item fail-open — 필수 fail-closed 시험을 제외하고도 PASS가 가능합니다 (scripts/acceptance-hs-0302.sh:293-301)
  원인: pytest 단계가 `-k "not acceptance_aborts"`로 기준 SHA 실패와 create-table 스캔 실패 시험을 모두 제외합니다. 성공 하한은 실제 수집·선택된 시험 수가 아니라 함수 정의 26개이며, 매개변수 확장으로 실행 건수가 부풀어 일부 필수 시험이 빠져도 `passed >= total_tests`가 성립합니다. 아래 자기 검사는 기준 SHA 실패만 대체하고 create-table 스캔 실패는 대체하지 않습니다.

증거 원문:
`-k "not acceptance_aborts"`
`if ... "${passed:-0}" -ge "$total_tests" ...`
함수 계수: 1차 13개 + 2차 13개. 제외 대상에는 `test_acceptance_aborts_when_create_table_scan_fails`가 포함됩니다.
→ 해석: 자기 호출 순환은 제거됐지만, F0302-4의 필수 음성 대조군 하나가 인수 실행 안에서는 실제로 돌지 않습니다. 필터가 더 넓어지는 회귀도 부풀려진 통과 수가 가릴 수 있습니다.

사업 영향: 스캔 오류가 다시 성공으로 처리되어도 인수 명령이 성공할 수 있고, 필수 검사를 실제로 돌렸다는 보고가 거짓이 됩니다.
  Recommendation: 자기 호출 시험을 별도 비재귀 시험 모듈이나 직접 probe로 분리해 모두 실행하십시오. `pytest --collect-only`의 선택 건수와 실제 passed 건수를 정확히 대조하고, deselected·skipped·xfail이 하나라도 있으면 실패하도록 하십시오.
- [medium] 신규 [medium] 유니코드 정규화 차이로 같은 후보가 두 행이 됩니다 (humansearch/src/humansearch/candidate_identity.py:115-125)
  원인: 입력 처리는 제어문자 검사와 `strip()`만 수행하고, HMAC은 원래 UTF-8 바이트를 그대로 사용합니다. 유니코드 정규화는 같은 글자를 여러 코드열로 표현할 수 있게 하는 규칙인데, NFC 등 대표형을 정하지 않았습니다.

증거 원문:
`café`와 `cafe\u0301`은 NFC 정규화 후 같고 원문은 다릅니다.
직접 실행: `nfc_equal=True`, `hmac_a=e2aa...`, `hmac_b=8474...`, `hmac_equal=False`.
→ 해석: 두 입력은 모두 현재 검증을 통과하고 서로 다른 기본키가 되므로, 동일한 포털 후보 식별자가 수집 경로의 정규화 차이만으로 중복 저장됩니다. 두 행 생성은 기본키 정의로부터의 추론이며 쓰기 금지 환경 때문에 DB 실행은 미확인입니다.

사업 영향: 후보 수 과대계상, 중복 접촉, 후속 증거·상태가 두 후보 행으로 갈라지는 문제가 발생합니다.

무엇을: 후보 식별 문자열의 정규화 계약을 명시해야 합니다.
왜: 중복 제거는 동일 후보가 항상 동일 바이트열이 된다는 전제에 의존합니다.
버린 길: NFKC를 무조건 적용하면 호환문자까지 합쳐 서로 다른 포털 ID를 오병합할 수 있습니다.
대가: NFC 강제 또는 비정규 입력 거부에 따라 일부 기존 입력의 키가 바뀌거나 거부됩니다.
되돌리기: 도메인 버전을 올리고 전환 규칙을 분리하면 기존 키 형식을 보존할 수 있습니다.
  Recommendation: 포털 식별자가 유니코드 의미 문자열인지 불투명 ID인지 먼저 계약으로 고정하십시오. 의미 문자열이면 strip 후 NFC로 정규화하거나 비-NFC 입력을 거부하고, 불투명 ID이면 허용 문자 집합을 좁히십시오. NFC 조합형/분해형과 NFKC에서만 같아지는 문자를 각각 별도 회귀 시험으로 두어 중복과 오병합을 모두 막으십시오.

Next steps:
- DB 최종 파일 링크 우회, 유니코드 동등쌍, create-table 스캔 fail-open 변이를 회귀 시험으로 고정하십시오.
- 새 인수 스크립트를 CI와 검증 명부에 직접 연결하십시오.
- 쓰기 가능한 검증 환경에서 전체 pytest, ruff, mypy, 인수 스크립트, 새 변이 시험을 다시 실행하고 현재 HEAD에 귀속된 원문 출력을 남기십시오.
```

## 재검토 2026-09-15 — PR #83 2차 GREEN(5576b02) Codex V1

실행 12:12:00~12:21:29, verdict needs-attention. 세 ID 전부 **부분 해결**. Codex 재현: Contact.name 미등록 조건+실제 렌더 형식 통과, 영폭 문자·마크다운 분할 변형 통과, 잘못된 이메일(a@b..com, a@-b.com) 통과, position.title 조건 문구 통과, 완전히 다른 두 루트 독립 청구, 금액 모양 `1,,,원` 통과. 팀리드 처분(12:24): 값싼 방어 4건(이메일 형식·영폭/마크다운/NFKC 정규화 후 판정·금액 형식 엄격화·실제 렌더 줄 시험 strict xfail)은 3차로, 구조 변경 3건(단일 Store 객체·CompanyBrief 금액 타입화·담당자 운영자 설정 조회/제목 면제 폐지)은 R5 에 따라 반복하지 않고 §7-5 사장님 결정 카드로. 결정 전까지 #83 은 병합 후보에서 제외.

```text
# Codex Adversarial Review

Target: branch diff against origin/main
Verdict: needs-attention

VERDICT: FAIL
건너뜀·미확인: 읽기 전용 환경이라 note 기록과 임시 디렉터리가 필요한 프로세스 경합 시험은 실행하지 못했습니다. uv 시험은 캐시 권한 오류(exit 2), pytest 첫 재시도는 임시 디렉터리 부재(exit 1)였습니다. 캡처를 끈 재시도로 F83-1 관련 38건과 F83-3 관련 34건은 통과했습니다. ruff도 통과했습니다. git diff --check는 mechanism-registry.yaml 끝의 빈 줄 때문에 실패했으나 병합 차단 결함으로 세지 않았습니다. 작업트리는 깨끗했습니다.

결론: 이 변경은 아직 내보내시면 안 됩니다. 원문에 없는 채용 조건이 후보자용 문구에 들어갈 수 있고, 저장 위치를 달리하면 같은 메일을 두 번 보낼 수 있습니다.

판단 근거: Contact·position.title을 운영자가 보증한 값으로 보는 해석은 버렸습니다. 시험 자체가 본문과 선언이 같은 LLM·실행 세션에서 온다고 명시하며, 코드에는 별도 승인·출처 표시가 없습니다. 서로 다른 저장 위치를 범위 밖으로 보는 해석도 버렸습니다. 공개 함수가 매번 경로를 받으면서 ‘한 패킷·한 채널 최대 한 번’을 약속하기 때문입니다. 이 판단이 틀리면 후보자에게 허위 지원 조건이 전달되거나 중복 메일이 발송되고, 장부는 이를 한 사건으로 추적하지 못합니다.

| ID | 판정 | 이유 |
|---|---|---|
| F83-1 선언 우회 | 부분 해결 | 자유 문자열 목록은 폐지됐지만 같은 신뢰 경계의 Contact와 position.title이 새 면제권이 됐습니다. |
| F83-2 잠금 정체성 | 부분 해결 | 같은 실제 디렉터리의 별칭과 verify packet_path는 묶였지만 서로 다른 두 루트는 독립 청구됩니다. |
| F83-3 CompanyBrief 주입 | 부분 해결 | 정형 조건과 금액 뒤 덧붙이기는 막았지만 미등록·영폭 문자·마크다운 변형은 통과합니다. |
→ 해석: 세 건 모두 원래 반례 일부는 막았지만 사업상 약속까지 닫지는 못했습니다. 기존 시험 5파일의 수정은 전반적 약화로 보지 않았습니다. 다만 새 F83-1 시험은 실제 Contact 렌더 결과 대신 이메일이 빠진 다른 문자열을 검사해 핵심 우회를 놓칩니다. flock은 운영체제 파일 잠금이며, 추가된 시험은 같은 루트의 프로세스 배타를 확인하는 데는 의미가 있지만 서로 다른 루트 문제에는 효력이 없습니다.

Findings:
- [high] F83-1 선언 우회(linkedin_frame_lines에 조건 문구 선언) — 타입 필드 면제권으로 우회가 남았습니다 (humansearch/src/humansearch/brief/types_packet.py:325-350)
  types_packet.py:325-350은 타입 필드 렌더 줄을 LinkedIn 충실도 검사에서 제외하는 역할입니다. Contact.name은 제한된 조건 정규식만 검사하고 position.title은 공백 여부만 검사합니다. 따라서 같은 LLM·러너 입력을 구조화했다는 사실만으로 신뢰할 수 있는 값이 되지 않습니다.

증거 원문:
CONTACT_UNKNOWN_RENDERED=PASS:문의: 대졸 필수 (x@example.kr)
CONTACT_ZWSP_VISIBLE_KNOWN=PASS:문의: 경​력 5년 이​상 (x@example.kr)
TITLE_UNKNOWN_RENDERED=PASS:제목: 대졸 필수
EMAIL_DOUBLE_DOT_RENDERED=PASS:문의: 홍길동 (a@b..com)
EMAIL_LEADING_HYPHEN_DOMAIN=PASS:a@-b.com
→ 해석: 미등록 조건, 화면에는 거의 동일하게 보이는 영폭 문자 변형, 잘못된 이메일이 실제 렌더 형식으로 패킷 경계를 통과했습니다.

시험의 원인도 구체적입니다. test_hs_1302c_frame_typed_render.py:112-123은 Contact를 ‘대졸 필수 + 이메일’로 선언하면서 본문에는 이메일 없는 ‘문의: 대졸 필수’를 넣습니다. 거부 원인은 조건 판정이 아니라 문자열 불일치입니다. 이 시험을 포함한 관련 시험 38건은 통과했지만 정확한 렌더 반례도 통과했습니다.

사업 영향: 후보자에게 원문에 없는 학력·경력 조건이나 회신 불가능한 주소가 전달될 수 있습니다.

설계 지적
무엇을: JD 본문과 프레임 메타데이터를 같은 패킷 안에서 서로 면제시키고 있습니다.
왜: 두 값 모두 같은 생성 주체에서 오므로 독립된 신뢰 근거가 아닙니다.
버린 길: 조건 단어를 정규식에 계속 추가하는 방식은 새 표현과 문자 변형마다 다시 열립니다.
대가: 프레임 조립 API와 저장 스키마를 변경해야 합니다.
되돌리기: 기존 linkedin_contact를 읽기 전용 호환 필드로 잠시 유지하되 면제 계산에서는 제외할 수 있습니다.
  Recommendation: JdPacket.linkedin_body에는 JD에서 검증된 내용만 저장하고 제목·연락처는 검증 후 별도 렌더 단계에서 붙이십시오. 연락처는 패킷 자유 입력이 아니라 운영자 소유 설정의 식별자로 조회하고, position.title도 신뢰 출처를 코드로 증명하지 못하면 면제하지 마십시오. 실제 rendered_line을 사용한 ‘대졸 필수’·영폭 문자 반례와 a@b..com·a@-b.com 거부 시험을 추가하십시오.
- [high] F83-2 잠금 정체성이 호출자 디렉터리에 종속 — 서로 다른 루트에서 중복 청구가 가능합니다 (humansearch/src/humansearch/brief/packet.py:222-257)
  packet.py:222-257은 호출자가 준 각 경로를 resolve하여 같은 실제 디렉터리의 별칭만 합칩니다. packet.py:5는 저장 위치가 호출자 주입임을 명시하고, record_intent·claim_send도 매 호출마다 별도 dir을 받습니다. 전역 저장소 정체성이나 허용된 단일 루트는 없습니다. 따라서 A와 B가 완전히 다른 디렉터리이면 각각 독립적인 packet·sent·claim 파일과 잠금을 가지며 둘 다 True를 받을 수 있습니다. verify_and_mark의 root/<id>.packet.json 검사는 각 루트 안의 일관성만 보장합니다.

제공된 구현자 재현 ‘완전히 다른 두 디렉터리는 청구 둘 다 성공’은 이 코드 구조와 일치합니다. 쓰기 금지 환경이라 재실행하지 못했으므로 실행 결과는 제공 증거, 결론은 코드에서 도출한 추론입니다. 새 test_hs_1309f_store_root_binding.py:112-125는 같은 실제 디렉터리와 심볼릭 링크 별칭만 시험합니다. 프로세스 경합 시험도 모든 프로세스가 같은 directory를 사용합니다.

→ 해석: resolve와 flock은 같은 저장 루트 안에서는 유효하지만, 호출자가 루트를 바꾸면 서로의 묘비와 잠금을 전혀 볼 수 없습니다.

사업 영향: 동일 패킷·수신자·본문이 두 번 발송될 수 있고, 각 장부는 자신이 유일한 발송이라고 기록합니다. 이미 발송된 이메일은 되돌릴 수 없습니다.

설계 지적
무엇을: 저장 루트가 함수 인자이면서 발송 정체성의 일부가 되었습니다.
왜: 동일 패킷의 유일성은 호출자 선택이 아닌 시스템 소유 값이어야 합니다.
버린 길: resolve만 적용하는 방식은 별칭만 합치며 독립 디렉터리는 합칠 수 없습니다.
대가: 공개 함수 인자와 CLI 조립부의 이전이 필요합니다.
되돌리기: 기존 Path API를 단일 Store 생성기로 위임하는 호환 래퍼를 둘 수 있습니다.
  Recommendation: 운영 계약에서 단 하나의 저장 루트를 해석해 생성하는 Store 객체를 도입하고 PacketStore·record_intent·claim_send·mark·verify_and_mark가 그 객체만 받도록 묶으십시오. 임의 Path 입력은 경계에서 거부하십시오. 서로 다른 두 실제 디렉터리에 동일 packet_id를 준비했을 때 두 번째 청구가 절대 True가 되지 않는 프로세스 시험을 추가하십시오.
- [high] F83-3 CompanyBrief 필드 조건 주입 — 금지 표현 목록 밖과 문자 변형이 통과합니다 (humansearch/src/humansearch/brief/types_packet.py:403-440)
  types_packet.py:403-418은 JD 블록 밖 줄을 제한된 정규식으로만 검사합니다. Claim.value는 types.py:120-126에서 공백과 출처 형식만 확인하므로 WebSearch 결과를 옮기는 LLM·러너의 자유 문구가 그대로 들어옵니다. 새 시험도 test_hs_1305b_company_amount_shape.py:36-38에서 ‘대졸 필수·재택근무 가능은 잡히지 않는다’고 명시하고 canonical 조건 두 개만 거부합니다.

증거 원문:
COMPANY_UNKNOWN_CONDITION=PASS:- 매출: 대졸 필수 [I1]
COMPANY_ZWSP_VISIBLE_KNOWN=PASS:- 매출: 경​력 5년 이​상 [I1]
COMPANY_MARKDOWN_VISIBLE_KNOWN=PASS:- 매출: 경**력** 5년 이**상** [I1]
MALFORMED_AMOUNT_SHAPE=PASS:- 매출: 1,,,원 [I1]
→ 해석: 알려지지 않은 표현뿐 아니라 사람이 같은 조건으로 읽는 영폭 문자·마크다운 분할도 통과하며, 금액 모양 검사도 잘못된 쉼표를 허용합니다.

반증 기록: 전각 숫자의 ‘경력 ５년 이상’, ‘경력 5년 **이상**’, ‘300억 원 경력 5년 이상’은 거부됐습니다. NFKC는 호환 문자를 표준형으로 바꾸는 유니코드 정규화이며, 일부 경로에서는 효과가 있었습니다. 그러나 금지어 양쪽을 나눈 변형은 통과하므로 전체 계약을 증명하지 못합니다. 관련 정상 시험 34건은 통과했습니다.

사업 영향: 회사 소개나 재무 정보로 표시된 줄에 허위 학력·경력 조건이 섞여 후보자에게 전달될 수 있으며, 잘못된 회사 금액도 정상 사실처럼 보일 수 있습니다.

설계 지적
무엇을: 자유 서술 회사 사실의 의미를 유한한 금지 정규식으로 판정합니다.
왜: 조건 표현과 유니코드·마크다운 변형은 닫힌 목록이 아닙니다.
버린 길: 패턴 몇 개 추가와 금액 줄 면제만으로는 같은 종류의 새 우회를 막지 못합니다.
대가: 회사 필드별 타입과 자유 서술의 승인 절차가 늘어납니다.
되돌리기: 기존 Claim JSON을 읽되 후보자용 렌더 전에 새 타입으로 변환·검증하는 경계를 둘 수 있습니다.
  Recommendation: 매출·영업이익·투자금은 Decimal·통화·단위로 분리한 타입과 엄격한 천 단위 형식으로 바꾸십시오. 자유 서술 CompanyBrief 값은 후보자용 본문에 자동 포함하지 말고 별도 승인된 필드만 렌더하십시오. 보조 방어로 모든 검사 입력에 NFKC·마크다운 제거·유니코드 format 문자 제거를 동일 적용하되, 이를 완전한 의미 검증으로 간주하지 마십시오. 성공한 세 반례와 1,,,원 거부 시험을 추가하십시오.

Next steps:
- F83-1의 실제 Contact.rendered_line 및 position.title 반례를 먼저 RED 시험으로 고정하십시오.
- 발송 API를 단일 Store 정체성에 결합하고 서로 다른 두 실제 루트 경합을 프로세스 시험으로 고정하십시오.
- CompanyBrief 금액을 구조화하고 자유 서술의 자동 면제를 제거하십시오.
- 쓰기 가능한 환경에서 전체 pytest·mypy와 test_hs_1309f_store_root_binding.py의 프로세스 경합 시험을 다시 실행하십시오.
- git diff --check의 mechanism-registry.yaml 끝 빈 줄도 정리한 뒤 재검토하십시오.
```

## 재검토 2026-09-15 — PR #96 5차 GREEN(cc74f1a) Codex V1

실행 12:24:05~12:34:15, verdict needs-attention. **F96-1 해결·F96-2 해결·4차 신규 high 해결**(`_remove` 는 temp_name 만, B 보존). 신규 high: 대조 성공 뒤 임시 unlink 실패 사이 최종 이름 교체 시 cleanup_failed 의 path 가 B 자리(A 임시 경로 없음), 불일치+정리 실패의 recovery_required 에 path·식별값 None. 신규 medium: 임시 FD close-before-close 실패가 write_failed 로 접힘. 6차(마지막) 지시(12:36): temp_path 후보 경로·recovery_required+러너 중단 계약. 종료 기준: 이후 잔여가 같은 UID 동시 실행 봉투 안이면 HS-05.04 사용권 선행으로 이관.

```text
# Codex Adversarial Review

Target: branch diff against origin/main
Verdict: needs-attention

VERDICT: FAIL

결론
다른 실행의 파일을 지우던 문제 자체는 해결됐습니다. 그러나 작업이 겹치면 실패 보고가 보존된 파일을 찾지 못하고, 반복 장애가 실행기를 멈출 수 있어 아직 내보내시면 안 됩니다.

판정 전 제한
- 실제 `hsrunner` 계정·별도 UID·원격 CI는 미확인입니다.
- 표적 pytest는 `uv` 캐시 쓰기 거부로 종료값 2, 직접 실행은 사용 가능한 임시 디렉터리 부재로 종료값 1이었습니다. 재시도 후 42건 수집, ruff·mypy는 종료값 0이었습니다.
- 경쟁 재현은 실제 파일시스템 실행이 아니라 메서드 순서를 고정한 제어 호출입니다. 같은 UID 실행이 최종 이름을 바꿀 수 있다는 조건에 기반한 추론입니다.
- HEAD는 `cc74f1a4e9e6da5b38fa96a9496fde4f78b44029`, 로컬 `origin/main`은 `fc6beedc78019862bc2f1b3bf4c4ad3bbd8e845b`이며 검토 전후 작업트리는 깨끗했습니다.

판단 근거
- 선택: `needs-attention`입니다. 이전 삭제 결함은 닫혔지만 실패 후 복구 계약을 깨는 새 순서를 재현했습니다.
- 버린 해석: 새 시험 세 건이 모든 동시 실행을 포괄한다는 해석은 버렸습니다. 시험은 최종 이름 교체와 임시 삭제 실패를 같은 구간에 배치하지 않습니다.
- 틀리면 깨지는 것: 후보 원문 A가 임시 이름으로 남으면서 영수증 경로는 B를 가리키고, 반복 close 장애는 열린 파일을 누적시킵니다.

원래 ID 최종 상태
- F96-1: 해결. 루트·조상은 FD 사슬로 고정됩니다.
- F96-2: 원래 결함은 해결. 중단 쓰기가 최종 이름을 선점해 재시도를 막는 경로는 사라졌습니다.
- 4차 신규 high: 해결. `_undo_publication`·`_roll_back`은 삭제됐고 `_remove` 호출 세 곳 모두 `temp_name`만 받습니다.
- 5차 최종 상태: 아래 신규 high·medium 때문에 전체 WU는 미완료입니다.

반증 기록
- 최종 이름 삭제를 다시 찾으려 했으나 `REMOVE_CALL 365 temp_name`, `415 temp_name`, `470 temp_name`만 확인됐습니다.
→ 해석: B를 이 구현이 직접 삭제하던 4차 결함은 닫혔습니다.
- 불일치 시험은 B의 내용과 `(device, inode)`를 보존하고, 동시 정리 실패도 `recovery_required`와 B 생존을 단언합니다.
→ 해석: 신규 시험은 삭제 방지 방향의 반대 요구이며 약화가 아닙니다.
- 기존 시험 두 건은 ‘최종 파일 없음’에서 ‘A 보존’, ‘두 이름 없음’에서 ‘A와 식별값 보존’으로 바뀌었습니다.
→ 해석: 계약 변경에 따른 의도적인 반대 방향 요구입니다.
- goal 문서와 `BoundaryReceipt` 필드는 `status, reason, path, sha256, byte_count, device, inode`로 일치합니다.
→ 해석: cc74f1a의 반환값 문서 정합 공격은 실패했습니다.
- 파일은 정확히 491줄, 최장 함수 `_publish`는 47줄, 전체 diff는 2,879줄입니다.
→ 해석: 파일 hard 600, 함수 hard 100, PR hard 3,000 한도는 통과합니다. 파일 soft 300은 초과합니다.

Findings:
- [high] 정리 실패 영수증이 보존된 파일 A의 위치를 보장하지 못합니다 (humansearch/src/humansearch/runner_boundary.py:356-416)
  원문 제목: 정리 실패 영수증이 보존된 파일 A의 위치를 보장하지 못합니다.

원인: `runner_boundary.py:356-358 — 게시된 항목이 A인지 확인하는 역할`과 `:365-368 — 임시 이름 삭제 실패 영수증을 만드는 역할` 사이에 최종 이름이 다시 바뀔 수 있습니다. 같은 UID 실행이 이때 B를 설치하고 임시 삭제가 실패하면 A는 임시 이름에 남지만, `cleanup_failed`의 `path`는 B가 있는 최종 경로이고 식별값은 A입니다. 또한 `:415-416 — 불일치 후 임시 정리 실패를 반환하는 역할`은 기존 영수증을 버리고 path·hash·device·inode가 모두 없는 `recovery_required`를 만듭니다.

증거 원문:
`ATTACK_CLEANUP_RACE denied cleanup_failed receipt_path=/protected/final.jsonl receipt_id=(7,101) path_now_id=(7,202) A_temp_id=(7,101) remove_calls=['.a.tmp']`
→ 해석: 최종 이름은 B인데 영수증은 그 경로와 A의 식별값을 결합했습니다. A를 여는 경로는 반환되지 않았습니다.

`ATTACK_MISMATCH_PLUS_CLEANUP_FAIL denied recovery_required final_B_id=(7,202) remove_calls=['.a.tmp'] receipt_path=None receipt_id=(None,None)`
→ 해석: B는 보존됐지만 남은 A 임시 파일을 어느 영수증과 연결해야 하는지 알 수 없습니다.

시험 공백: `test_runner_boundary_receipt.py:476-505 — cleanup_failed 영수증 시험 역할`은 최종 이름 교체 없이 정리 실패만 만듭니다. `:508-534 — 불일치와 정리 실패 동시 시험 역할`은 B만 검증하고 남은 A의 위치·식별값은 검증하지 않습니다.

사업 영향: 후보 원문이 임의 임시 이름으로 장기 잔존하지만 복구·readback·purge가 어느 파일인지 결정할 수 없습니다. 이는 보호 자료의 추적 불가능한 잔존과 수동 오삭제 위험으로 이어집니다.

무엇을 — 실패 영수증이 A를 열 수 있는 후보 경로와 A의 hash·device·inode를 함께 보존하게 하십시오.
왜 — device/inode는 위치 탐색값이 아니므로 경로 없이 A를 복구할 수 없습니다.
버린 길 — 최종 경로를 계속 A의 경로라고 쓰는 방식은 같은 경쟁 창 때문에 버려야 합니다.
대가 — receipt에 검증 대상인 `temp_path` 또는 복수 후보 경로를 추가하고 소비자가 식별값·hash를 확인해야 합니다.
되돌리기 — 이 계약을 제공할 수 없으면 해당 순서를 `recovery_required`로 중단하고 자동 복구 가능 주장을 제거하십시오.
  Recommendation: 최종 경로와 임시 경로를 신뢰도와 함께 구분해 반환하고, 동일 구간에 B 교체와 임시 unlink 실패를 주입하여 반환된 후보 경로 중 하나가 A의 device/inode와 hash를 실제로 만족하는지 시험하십시오.
- [medium] 임시 파일 close 실패가 열린 FD를 남겨도 일반 write_failed로 접힙니다 (humansearch/src/humansearch/runner_boundary.py:304-313)
  원문 제목: 임시 파일 close 실패가 열린 FD를 남겨도 일반 write_failed로 접힙니다.

원인: `runner_boundary.py:263-268 — close 실패 시 FD 상태가 불확실하다고 정의하는 역할`과 달리 `:312-313 — 임시 FD close 실패 처리 역할`은 이름만 unlink하고 일반 `write_failed`를 반환합니다. close가 실제 호출 전에 실패하면 FD는 열린 채인데 이후 실행을 중단하거나 복구 필요 상태로 올리는 장치가 없습니다.

증거 원문:
`ATTACK_TEMP_CLOSE_BEFORE_CLOSE denied write_failed fd_still_open=True name_removed=True receipt_id=(None,None)`
→ 해석: 이름은 없어졌지만 열린 객체가 프로세스에 남았고, 영수증은 이를 복구 필요 상태로 구분하지 못했습니다.

시험 공백: `test_runner_boundary_failures.py:197-201 — 임시 close 고장 주입 역할`은 `real_close(fd)`를 먼저 실행한 뒤 예외를 던집니다. 따라서 ‘실패했지만 실제로 닫히지 않은’ 경우를 시험하지 않습니다. 디렉터리 FD용 `CloseTrap`은 반대로 실제 close 전에 실패시키므로 시험 방식도 일관되지 않습니다.

사업 영향: 장시간 실행되는 러너에서 같은 장애가 반복되면 열린 FD와 unlink된 원문 객체가 누적되어 이후 모든 저장이 실패할 수 있습니다.

무엇을 — 실제 close 전 실패를 모델링하고 이 경우 프로세스를 계속 정상 사용하지 않도록 하십시오.
왜 — close 오류 뒤 FD 소유 상태를 휴리스틱으로 정상 처리할 수 없다고 코드 자체가 선언합니다.
버린 길 — 실제 close 후 예외만 던지는 시험은 핵심 실패를 제거하므로 버려야 합니다.
대가 — `recovery_required`와 러너 중단·재시작 정책이 필요합니다.
되돌리기 — 안전한 회수 계약이 없으면 close 실패 후 같은 프로세스에서 추가 저장을 허용하지 마십시오.
  Recommendation: 임시 FD의 close를 실제로 수행하기 전에 오류를 주입하는 회귀 시험을 추가하고, 실패 시 `recovery_required`로 반환한 뒤 호출자가 순회를 중단하고 해당 러너 프로세스를 폐기하도록 계약하십시오.

Next steps:
- cleanup_failed/recovery_required 영수증에 A를 열 수 있는 검증 가능한 경로와 hash·device·inode를 보존하십시오.
- 임시 FD close-before-close 실패 시험과 러너 중단·재시작 계약을 추가하십시오.
- 쓰기 가능한 환경에서 표적 42건과 전체 pytest를 실행하고, 실제 별도 UID 실증은 기존 계약대로 NOT_RUN 상태를 유지하십시오.
```

## 재검토 2026-09-15 — PR #83 3차 GREEN(c57dde1) Codex V1

실행 12:36:36~12:46:43, verdict needs-attention. 2차 증거 9줄 중 6줄 거부로 해소, 3줄(COMPANY_UNKNOWN_CONDITION·CONTACT_UNKNOWN_RENDERED·TITLE_UNKNOWN_RENDERED)은 범위 밖(구조 변경 결정 대기, strict xfail). 범위 안 새 결함: high — 마크다운 링크 문법·U+FE0F·키릴 동형문자로 조건 문구를 쪼개면 통과(정규화 사본이 Cf·강조만 제거), medium — 이메일 로컬파트 점 배치(a..b@, .a@, a.@) 통과. F83-2 범위 안 PASS. 처분(12:48): 두 건을 5차(마지막)로 닫고 이후 잔여는 결정 카드 ⑤(금지→허용 목록)로. 별도: push 가 PII 게이트(합성 이메일 리터럴 14곳)에 막혀 4차로 정정 중.

```text
# Codex Adversarial Review

Target: branch diff against origin/main
Verdict: needs-attention

VERDICT: FAIL

결론
이번 HEAD는 아직 내보내시면 안 됩니다. 앞서 잡힌 여섯 입력은 막혔지만, 같은 화면 결과를 만드는 새 우회 두 종류와 실제로 배달할 수 없는 주소 우회가 확인됐습니다. 범위 밖으로 합의하신 세 가지 구조 변경은 새 결함으로 세지 않았습니다.

건너뜀·실패·재시도
- 전체 시험은 읽기 전용 환경에서 임시 디렉터리를 만들 수 없어 미확인입니다.
- 첫 실행은 uv 캐시 권한 문제로 exit 2, 두 번째는 pytest 임시 파일 문제로 exit 1이었습니다. 캡처를 끈 세 번째 실행은 106 passed, 2 xfailed, exit 0이었습니다. strict xfail은 현재 실패를 예상하되 갑자기 통과하면 시험 전체를 실패시키는 고정 시험입니다.
- 관련 파일 ruff와 mypy는 각각 exit 0, git diff --check도 exit 0이었습니다.
- note 스킬의 체크포인트 저장은 읽기 전용 정책 때문에 거부됐습니다.

판단 근거
- 선택: 범위 안의 새 우회가 실제 패킷 생성까지 통과했으므로 출고 중단입니다.
- 버린 해석: 기존 여섯 증거가 거부되므로 방어가 충분하다는 해석은 버렸습니다. 강조 표시 외의 링크 문법과 보이지 않는 다른 문자로 같은 검사를 다시 통과시켰기 때문입니다.
- 틀리면 깨지는 것: 원문에 없는 채용 조건이 회사 소개나 문의 줄로 발송되고, 잘못된 회신 주소가 정상 연락처로 표시됩니다.

9개 증거 실측
| 증거 | HEAD 결과 | 범위/상태 |
|---|---|---|
| EMAIL_DOUBLE_DOT_RENDERED | 거부 | 범위 안, 해소 |
| EMAIL_LEADING_HYPHEN_DOMAIN | 거부 | 범위 안, 해소 |
| CONTACT_ZWSP_VISIBLE_KNOWN | 거부 | 범위 안, 해소 |
| COMPANY_ZWSP_VISIBLE_KNOWN | 거부 | 범위 안, 해소 |
| COMPANY_MARKDOWN_VISIBLE_KNOWN | 거부 | 범위 안, 해소 |
| MALFORMED_AMOUNT_SHAPE | 거부 | 범위 안, 해소 |
| COMPANY_UNKNOWN_CONDITION | 통과: `• 대졸 필수 [C1]` | 구조 변경 범위 밖, 미해결·새 결함 미산정 |
| CONTACT_UNKNOWN_RENDERED | 통과: `문의: 대졸 필수 (x@example.kr)` | 범위 밖, strict xfail 미해결·새 결함 미산정 |
| TITLE_UNKNOWN_RENDERED | 통과: `제목: 대졸 필수` | 범위 밖, strict xfail 미해결·새 결함 미산정 |
→ 해석: 약속된 여섯 회귀는 닫혔지만, 세 구조적 구멍은 선언대로 남아 있습니다.

F83 최종 상태
| 항목 | 범위 안 | 범위 밖 | 최종 상태 |
|---|---|---|---|
| F83-1 | 기존 영폭·강조 변형은 거부하지만 링크 문법·U+FE0F 변형이 통과 | 운영자 담당자 조회·제목 면제 폐지 보류 | FAIL |
| F83-2 | 정규 저장 루트·공통 잠금·발송 직전 해시 재검사는 코드상 결합됨 | 단일 Store 객체 결정 보류 | 범위 안 PASS, 전체 보류 |
| F83-3 | 엉터리 금액은 거부하지만 회사 자유 서술에서 새 정규화 우회가 통과 | 금액 타입화·자유 서술 자동 렌더 금지 보류 | FAIL |
→ 해석: F83-2의 값싼 방어에서는 새 우회를 찾지 못했지만, F83-1과 F83-3은 이번 범위 안에서도 다시 뚫렸습니다.

기술 상세와 증거 원문
- NFKC는 호환 문자를 표준 모양으로 접는 유니코드 정규화이고, Cf는 영폭 문자 등이 속한 유니코드 형식 문자 범주입니다. 현재 판정 사본은 Cf와 일부 강조 기호만 제거합니다.
- U+FE0F는 Cf가 아닌 결합 표시 문자여서 남습니다. `경️력 5년 이️상`은 Contact와 실제 회사 리서치 줄 모두 통과했습니다.
- 마크다운 링크 `경[력]() 5년 이[상]()`도 링크의 표시 글자만 보면 `경력 5년 이상`이지만 Contact와 회사 리서치 패킷을 통과했습니다. HTML 태그 변형은 전체 메일 조립에서 거부됐습니다.
- 키릴 문자 а를 삽입한 `경а력 5년 이а상`도 통과했습니다. NFKC는 서로 다른 문자 체계의 닮은 글자를 같은 글자로 바꾸지 않습니다.
- 원문·해시는 보존됐습니다. 영폭 문자가 든 정상 JD의 JSON 왕복에서 원문 바이트가 유지됐고 packet_id도 원문 SHA-256에서 계산됐습니다.
- 정상 대조군 `300억 원`과 `홍길동 (x@example.kr)`은 통과했습니다. `999원`·`1,000원`은 통과하고 `1000원`은 거부됩니다.
- 국제화 도메인 `x@한글.kr`은 거부되고 ASCII 변환 주소 `x@xn--bj0bj06e.kr`은 통과합니다. `"x"@example.kr`은 통과하지만 공백을 포함한 `"x y"@example.kr`은 거부돼 따옴표 로컬파트 지원은 일관된 계약이 아닙니다.
- c57dde1은 회사 자유 서술 필드 시험을 추가했으므로 기존 시험 약화는 아닙니다. 다만 새 링크·U+FE0F·로컬파트 점 배치 반례는 시험에 없습니다.

원문:
`106 passed, 2 xfailed in 0.43s`
`CONTACT 경️력 5년 이️상 = ACCEPTED`
`COMPANY • 경️력 5년 이️상 [C1] = ACCEPTED`
`CONTACT 문의: 경[력]() 5년 이[상]() (x@example.kr) = ACCEPTED`
`COMPANY • 경[력]() 5년 이[상]() [C1] = ACCEPTED`
`문의: 홍길동 (a..b@example.kr) = ACCEPTED_PACKET`
`문의: 홍길동 (.a@example.kr) = ACCEPTED_PACKET`
`문의: 홍길동 (a.@example.kr) = ACCEPTED_PACKET`
→ 해석: 실패 판정은 추정이 아니라 HEAD의 생성·검증 경계를 직접 통과한 결과입니다.

Findings:
- [high] 판정용 정규화가 링크 문법과 Cf 밖의 보이지 않는 문자를 놓칩니다 (humansearch/src/humansearch/brief/jd_fidelity.py:55-70)
  원인: `judgement_form()`은 NFKC 적용 뒤 Cf 문자와 `*`, `_`, 백틱 등만 제거합니다. 마크다운 링크의 괄호·대괄호와 U+FE0F 같은 Cf 밖의 기본적으로 보이지 않는 문자는 남아 조건 정규식의 연속 문자열을 끊습니다. `types_packet.py:94`와 `types_packet.py:236-254`가 이 사본을 신뢰하고, 회사 줄은 `types_packet.py:417-430`에서 해당 검사만 통과하면 발송 본문에 남습니다.
사업 영향: 원문에 없는 경력·학력 조건이 회사 소개나 문의 줄로 패킷과 발송 본문에 들어갈 수 있습니다.

원문:
`문의: 경️력 5년 이️상 (x@example.kr) = ACCEPTED`
`• 경️력 5년 이️상 [C1] = ACCEPTED`
`문의: 경[력]() 5년 이[상]() (x@example.kr) = ACCEPTED`
`• 경[력]() 5년 이[상]() [C1] = ACCEPTED`
→ 해석: 강조 표시만 제거하는 현재 규칙을 벗어나면 같은 채용 조건이 실제 렌더 줄에서 허용됩니다.

설계 지적
무엇을: 판정 사본을 사람이 보게 되는 글자로 환원해야 합니다.
왜: 현재 문자 삭제 목록과 화면 표시 규칙이 다릅니다.
버린 길: 조건 단어와 강조 기호만 계속 추가하는 방식은 다음 문법에서 다시 뚫립니다.
대가: 링크 해석, 보이지 않는 문자 정책, 혼합 문자 체계 정책을 명시해야 합니다.
되돌리기: 새 정규화를 독립 함수와 회귀 시험으로 격리하면 문제가 생길 때 이전 판정기로 되돌릴 수 있습니다.
  Recommendation: 마크다운 링크·이미지는 표시 문자열로 환원하고, Cf뿐 아니라 기본적으로 보이지 않는 유니코드 문자 전체를 제거하거나 입력 단계에서 거부하십시오. 한글 중심 필드의 혼합 문자 체계도 거부하고, Contact와 CompanyBrief의 실제 전체 메일 조립 경로에 링크·U+FE0F·키릴 문자 회귀 시험을 추가하십시오.
- [medium] 이메일 검사가 로컬파트의 잘못된 점 배치를 정상 주소로 허용합니다 (humansearch/src/humansearch/brief/types.py:26-31)
  원인: 주소의 @ 앞부분인 로컬파트를 `[^@\s]+`로 받아 연속 점, 선행 점, 후행 점을 모두 허용합니다. 도메인 라벨만 강화돼 이전 결함과 같은 회신 불가 위험이 로컬파트에 남았습니다.
사업 영향: 발송 문서에 정상 연락처처럼 표시되지만 실제 회신이 실패할 수 있어 후보 접촉과 출처 검증이 끊깁니다.

원문:
`문의: 홍길동 (a..b@example.kr) = ACCEPTED_PACKET`
`문의: 홍길동 (.a@example.kr) = ACCEPTED_PACKET`
`문의: 홍길동 (a.@example.kr) = ACCEPTED_PACKET`
→ 해석: 타입 생성만이 아니라 실제 LinkedIn 렌더 줄과 SearchPacket 경계까지 통과했습니다.
  Recommendation: 지원 범위를 명시적으로 정하십시오. 단순 주소만 지원한다면 로컬파트를 허용 문자로 구성된 점 구분 조각으로 제한해 빈 조각·선행·후행 점을 거부하고 따옴표도 전부 거부하십시오. 따옴표 주소나 국제화 도메인을 지원한다면 부분 정규식 대신 그 계약을 완전히 검증하는 파서를 사용하고 각각 회귀 시험을 추가하십시오.

Next steps:
- 두 범위 안 결함을 수정한 뒤 링크 문법·U+FE0F·혼합 문자·로컬파트 점 배치를 실제 패킷 생성 시험으로 고정하십시오.
- 읽기 가능한 임시 디렉터리가 있는 환경에서 전체 pytest를 재실행하고 기존 범위 밖 strict xfail 두 건만 남는지 확인하십시오.
- `1000원` 거부와 국제화·따옴표 이메일 미지원이 의도된 제품 계약인지 문서에 명시하십시오.
- 범위 밖 세 구조 변경은 이번 결함 수에 합치지 말고 별도 사장님 결정 항목으로 유지하십시오.
```

## 재검토 2026-09-15 — PR #96 6차 GREEN(60c4fb8) Codex V1

실행 12:42:45~12:49:02, verdict needs-attention. 5차 잔여 2건 중 안정 부모 경로에서의 정리 실패·단독 close 실패는 보강 확인. 남은 것: (a) 루트 디렉터리 자체 이동 시 temp_path 낡음 — 같은 UID 동시 실행 봉투, HS-05.04 이관(Codex 도 새 결함으로 세지 않음, 단 goal 문서 이관 문구 미확인), (b) in-scope: `_discard` 가 권한검증 실패+unlink 실패에서 영수증 필드 전부 None, (c) in-scope: 쓰기 실패+close 실패 결합이 write_failed. 7차(최종) 지시(12:51): (b)(c)+goal 이관 문구.

```text
# Codex Adversarial Review

Target: branch diff against origin/main
Verdict: needs-attention

VERDICT: FAIL. 지금 상태로는 내보내시면 안 됩니다. 미확인: 읽기 전용 환경 때문에 전체 pytest·verify.sh·실제 hsrunner/EACCES·CI는 실행하지 못했습니다. uv 재시도 전에는 캐시 권한 오류(exit 2), 직접 pytest는 사용 가능한 임시 디렉터리 부재(exit 1)였습니다. F96-1은 부분 해결, F96-2도 부분 해결입니다. 안정된 부모 경로에서의 정상 정리 실패와 단독 close 실패는 보강됐지만, 결합 실패 반례 두 건이 현재 HEAD에서 재현됩니다. 선택한 해석은 ‘남은 임시 파일에 실제로 닿아야 하고, 임시 FD를 닫지 못한 모든 경로가 러너 폐기를 요구한다’입니다. 정상 사례만 충족하면 된다는 해석은 버렸습니다. 이 판단이 틀리면 복구해야 할 원문을 찾지 못하거나, 열린 손잡이를 가진 러너가 다음 후보를 계속 처리합니다. 같은 러너 UID가 최종 이름만 바꾸는 창은 사용자 선언에 따라 HS-05.04 선행조건으로 보고 새 결함으로 세지 않았습니다. 다만 현재 checkout의 goal 문서에서는 HS-05.04 이관 문구를 찾지 못해 그 문서화 상태는 미확인입니다. 반증 기록: ruff는 “All checks passed!”, mypy는 “Success: no issues found in 46 source files”, AST 파싱은 “AST_OK 46 files”, git diff --check는 exit 0이었습니다. 열린 FD를 정리하면서 다시 FD 자체를 조작하는 경로는 찾지 못했고, 파일 526줄·최장 함수 54줄은 P11의 hard 600/100 안이라 결함으로 세지 않았습니다.

Findings:
- [high] [F96-1] 정리 실패 영수증이 A의 위치를 보장하지 못함 (humansearch/src/humansearch/runner_boundary.py:383-398)
  원인: humansearch/src/humansearch/runner_boundary.py:383-398은 잔류 임시 경로를 고정된 `final_path.parent` 문자열로 만듭니다. 보호 루트가 열린 디렉터리 파일 디스크립터(FD, 열린 디렉터리를 가리키는 운영체제 손잡이)로 고정된 뒤 이름이 이동하면 실제 파일은 이동한 디렉터리에 남지만 `temp_path`는 옛 경로를 가리킵니다. 기존 결합 시험도 tests/test_runner_boundary_receipt.py:107-129에서 루트 이동과 unlink 실패를 만들면서 상태와 이유만 확인해 이 불일치를 놓칩니다. 또한 runner_boundary.py:500-507의 일반 `_discard`는 완성 파일의 권한 검증 실패 뒤 unlink까지 실패해도 sha256/device/inode/temp_path를 모두 버립니다.
사업 영향: 복구가 필요하다는 영수증은 남지만 소비자가 원문 A를 열 수 없어 감사 자료나 후보 원문을 사실상 잃을 수 있습니다.
증거 원문:
root-move+cleanup-failure receipt: BoundaryReceipt(status=<BoundaryStatus.DENIED: 'denied'>, reason='recovery_required', path=PosixPath('/holder/root/final'), sha256='digest', byte_count=7, device=11, inode=22, temp_path=PosixPath('/holder/root/.3132333435363738.tmp'))
receipt candidate: /holder/root/.3132333435363738.tmp
actual pinned-directory location after /holder/root -> /holder/moved rename: /holder/moved/.3132333435363738.tmp
→ 해석: 영수증의 두 후보 경로 모두 실제 잔류 파일에 닿지 않습니다.
추가 반례 원문:
F96-1 counterexample: BoundaryReceipt(status=<BoundaryStatus.DENIED: 'denied'>, reason='recovery_required', path=None, sha256=None, byte_count=0, device=None, inode=None, temp_path=None)
→ 해석: 완성된 payload의 권한 검증과 삭제가 연속 실패하면 ‘항상 보존’해야 할 값도 사라집니다.
  Recommendation: 무엇을: 모든 정리 실패를 하나의 영수증 생성 경로로 모으고, 알려진 digest·fstat 값과 실제로 다시 열 수 있는 복구 위치를 보존하십시오.
왜: device/inode는 위치를 찾는 값이 아니므로 유효한 후보 경로가 반드시 필요합니다.
버린 길: `final_path.parent / temp_name` 문자열만 반환하는 방식과 `_discard`의 빈 영수증은 버리십시오.
대가: 보호 루트의 직접 부모를 러너가 이동할 수 없게 하는 bootstrap 계약 또는 고정된 recovery 위치에 hard-link하는 절차가 추가됩니다.
되돌리기: 새 복구 위치와 영수증 필드를 함께 제거하고 이전 API로 되돌릴 수 있게 변경을 한 커밋에 묶으십시오. 루트 이동+unlink 실패 및 완성 파일 검증 실패+unlink 실패 시험에서 경로·sha256·device·inode를 모두 검증하십시오.
- [medium] [F96-2] 쓰기 실패와 겹친 임시 FD close 실패가 write_failed로 접힘 (humansearch/src/humansearch/runner_boundary.py:303-307)
  원인: humansearch/src/humansearch/runner_boundary.py:303-307은 `_fill_temp_file` 오류 뒤 `_close_fd(fd)`의 False 결과를 버리고 곧바로 `_discard(..., "write_failed")`를 반환합니다. 성공적으로 채운 뒤의 close 실패만 308-311에서 `recovery_required`로 승격됐습니다.
사업 영향: 실제로 열린 임시 FD가 남았는데 호출자는 단순 쓰기 실패로 오인해 러너를 재사용할 수 있습니다. 그 결과 FD 누적, 삭제된 파일의 저장공간 유지, 다음 후보 처리의 신뢰 경계 붕괴가 생길 수 있습니다.
증거 원문:
F96-2 counterexample: BoundaryReceipt(status=<BoundaryStatus.DENIED: 'denied'>, reason='write_failed', path=None, sha256=None, byte_count=0, device=None, inode=None, temp_path=None)
F96-2 close attempts: 1
→ 해석: ENOSPC 쓰기 실패와 실제 close 전 EIO를 함께 주입했으며 close 실패가 있었음에도 러너 폐기 신호가 반환되지 않았습니다. 현재 시험 tests/test_runner_boundary_failures.py:180-229은 쓰기가 먼저 성공한 단독 close 실패만 다룹니다.
  Recommendation: `except OSError`에서 close 결과를 보존하고, False이면 정리 성공 여부와 무관하게 `recovery_required`를 반환하십시오. ENOSPC 또는 fsync/fstat 오류와 close-before-close 오류를 동시에 주입해 열린 FD를 확인한 뒤, 영수증이 `recovery_required`인지 검증하는 회귀 시험을 추가하십시오.

Next steps:
- F96-1의 안정적인 복구 위치와 모든 cleanup 경로의 식별값 보존을 구현하십시오.
- F96-2의 쓰기 실패+close 실패 결합 경로를 `recovery_required`로 승격하십시오.
- 쓰기 가능한 환경에서 대상 pytest, 전체 pytest, ruff, mypy, verify.sh를 다시 실행하고 실제 hsrunner 분리 실증은 계속 NOT_RUN으로 명시하십시오.
```
