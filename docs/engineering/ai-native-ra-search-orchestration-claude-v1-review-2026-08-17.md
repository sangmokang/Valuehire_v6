# AI-native RA 서치 오케스트레이션 Claude V1 검토 기록 — 2026-08-17

## 결론

최신 기획서와 28개 구현 프롬프트를 위험 경계별로 나눠 Claude CLI에 읽기 전용 적대검토를 반복한 최종 합성 판정은 통과다. 이는 한 번의 전체 파일 호출이 아니라 입력 한도를 지키며 겹치는 범위로 수행한 합성 판정이다. 각 범위에서 중대 결함이 나오면 Codex가 저장소 문구를 직접 재현하고 수정한 뒤 같은 범위를 처음부터 다시 검토했다.

검토 통과는 문서 계약의 통과다. 실제 ClickUp·Supabase·SQLite·Gmail·Aside·채용사이트 실행이나 권한을 증명하지 않으며, 각 프롬프트가 요구하는 실제 경계 통과를 대신하지 않는다.

## 실행 격리와 판정 뒤집힘

일반 Claude Code 플러그인·훅 경로에서는 안전 필터 응답 또는 장시간 무출력이 발생했다. 당시 `NOT_RUN` 판정은 맞았지만 도구 전체가 불가능한 것은 아니었다. 플러그인·훅을 격리하는 `--safe-mode` 경로에서 동일한 읽기 전용 검토가 정상 응답해 이후 V1을 실제 수행했다.

사용한 명령 형태:

```bash
{ printf '%s\n' '<검토 지시>'; sed -n '<필요 범위>' <검토 파일>; } |
  env -u ANTHROPIC_API_KEY claude -p \
    --safe-mode \
    --model sonnet \
    --effort medium \
    --tools '' \
    --no-chrome \
    --no-session-persistence
```

→ 후보 원문·자격증명·실서비스 데이터는 입력하지 않았고, 저장소의 기획 문서만 전달했다.

## 적대검토 라운드

| 범위 | 최초 판정과 결함 | Codex 재현·수정 | 최신 판정 |
|---|---|---|---|
| P03, P09~P17 | `FAIL`: P14 고객사 차원/선행조건, P16→P17 적격성 증명, P12 정식 후보 ID·별칭·연결 해제 보호가 불완전 | 정식 고객사·포지션 ID, `canonical_candidate_id`, alias closure, 연결 해제 뒤 양쪽 `DO_NOT_CONTACT`, P15/P16 사람 상태와 P17 claim 증명을 추가 | `PASS` |
| P15~P26 | `FAIL`: 큐·계정·로컬 예약 세대 혼합, 사람 pause가 장애 예산을 소진, 장애 회수 상한과 P21 capability 만료가 불완전 | `queue_lease_epoch`, `account_fencing_token`, `local_reservation_epoch`, `machine_recovery_attempts`, `delivery_attempt`를 분리하고 pause/release/reacquire, 로컬 단조 마감, `MACHINE_RECOVERY_LIMIT`을 추가 | `PASS` |
| 통합 기획서 | `FAIL`: 자동 회수 카운터, 정식 ID 생성, 묶음 병렬성, 목표 후보 수 이름이 프롬프트와 불일치 | 정식 ID 규칙, 프로젝트별 선행조건 우선, `target_eligible_candidate_count`/`target_pre_interview_count` 분리와 동일 필드 소비를 고정 | `PASS` |
| P03/P06/P07 READY | `FAIL`: P03이 미래 P06/P07 런타임을 선행 검증, P06 교환 시험 누락, READY 필수 필드가 P03·계획서에서 불일치 | P03은 필드 계약만, P06/P07은 자기 소비 검증을 소유. READY 필드 전체·선택값·누락 표 시험을 일치시킴 | `PASS` |
| 내부 후보 우선 경로 | `FAIL`: P08이 P13보다 먼저 외부 작업을 제안할 수 있고 P07↔P25 공유 영수증 소유자가 없음 | P12가 동일인 포트와 공용 적격 영수증 스키마를 소유. P13 내부 결정→P06/P07 병렬→P08 결합, P25 외부 사람 판정→P07 재계산으로 변경 | `PASS` |
| 병렬 판단 세대 | `FAIL`: P08에 P06 결정 지문이 없고 P06/P07 후보 집합 해시 산출 계약이 없음 | `position_priority_decision_hash`와 P12 단일 `candidate_eligibility_receipt_set_hash` 구현·정렬·정규 JSON·SHA-256 계약을 추가 | `PASS` |

→ 표는 최초 결함을 숨기지 않고 수정 뒤 같은 범위를 다시 검토해 통과한 이력을 요약한다.

## 최신 정확 판정 원문

### P03/P05/P06/P07과 실행 카운터 범위

```text
VERDICT: PASS

P03/P05/P06/P07 선행조건·소비·검증 책임은 순환 없이 분리됐고,
delivery_attempt, queue_lease_epoch, machine_recovery_attempts,
account_fencing_token, local_reservation_epoch의 소유·증가 주체와
DELIVERY_RETRY_LIMIT / MACHINE_RECOVERY_LIMIT가 분리 유지됐다.
```

→ 목표 필드와 실행 카운터 범위에서 최신 문서 사이의 차단급 모순이 없다는 판정이다.

### 내부 매칭 선행·공유 영수증 범위

```text
VERDICT: PASS

공유 적격 영수증은 P12가 스키마를 소유하고 P13·P25가 결정을 생성하며
P07이 canonical_candidate_id 합집합으로 계수한다. 외부 신규 후보는 P25에서
P12 동일인 경계를 먼저 통과하고, P13 내부 매칭 뒤 P06/P07을 병렬 계산해
P08에서 결합하는 순서에 BLOCKER/HIGH가 없다.
```

→ 내부 후보를 먼저 계산하고 외부 후보는 사람 판정 뒤 다시 세는 의존성이 통과했다는 판정이다.

### 최종 후보 집합 지문 회귀 검토

```text
VERDICT: PASS

이전 BLOCKER였던 candidate_eligibility_receipt_set_hash의 공용 산출 규칙·소유자
문제는 해결되었다. P12가 eligibility_receipts.py를 유일한 구현 소유자로 명시하고,
별칭 폐쇄, 현재 유효 결정 선택, 고정 키 추출, UTF-8 바이트 정렬, 정규 JSON,
SHA-256 규칙을 완결적으로 규정했다. P06·P07은 공용 함수를 호출하고 P08은
두 지문의 일치를 검사한다. 새 BLOCKER/HIGH는 발견되지 않았다.
```

→ 병렬 계산의 후보 집합 지문을 P12 공용 함수 하나로 재현할 수 있다는 최종 회귀 판정이다.

## V1 최종 상태

- 기획서: `PASS`
- 28개 구현 프롬프트 합성 검토: `PASS`
- 최신 변경 범위 회귀 검토: `PASS`
- 실제 외부 경계 실행: `NOT_RUN` — 이번 기획 작업의 비범위이며 후속 프로젝트별 `LIVE_PASS`가 필요
- 저장소 출하 상태: 별도 Harness 판정에 따름
