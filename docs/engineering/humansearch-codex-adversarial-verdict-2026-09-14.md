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
