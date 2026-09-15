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
