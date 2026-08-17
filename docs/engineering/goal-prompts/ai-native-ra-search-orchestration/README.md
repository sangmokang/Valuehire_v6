# AI-native RA 구현 프롬프트 묶음

이 디렉터리는 통합 기획서를 28개의 독립 실행 프로젝트로 나눈 정본 후보입니다. 각 파일은 worktree 1개, 인수 기준 1개, 검토 요청 1개를 전제로 하며 앞 프로젝트가 요구 수준으로 실제 합격한 증거 없이는 후속 프로젝트를 시작하지 않습니다.

## 공통 경계

- 현재 v6에는 사업 실행 코드가 없으므로 과거 v4/v5 코드를 가져오지 않고 계약과 실패 사례만 새 시험으로 재작성합니다.
- LinkedIn 사이트 안 자동화는 범위 밖입니다. 어떤 채널이든 봇 탐지·보안문자·속도·기기·계정·네트워크 제한을 숨기거나 우회하는 구현은 금지합니다.
- 후보 원문은 공유 작업 큐에 넣지 않고, SQLite 파일은 여러 컴퓨터가 네트워크로 공동 쓰지 않습니다.
- ClickUp 쓰기, 메일/인메일 발송, 포털 쓰기, 운영 DB 변경, 배포는 각각 별도 승인 프로젝트입니다.

## 실행 순서

| 단계 | 프롬프트 | 병렬 가능 조건 |
|---|---|---|
| 계약 | P00A → P00B → P01/P02 → P03 → P04 | P01과 P02만 P00B 뒤 병렬 |
| 읽기·판단 | P05/P09/P10/P11 → P12 → P13 → P06/P07 → P08; P14는 P12 뒤 | P05와 세 후보 입력원, P13 뒤 P06/P07, P12 뒤 P14는 각각 병렬 가능 |
| 여러 컴퓨터 | P15 → P16 → P17 → P18 → P19 | 각 프로젝트의 선행조건 합격 뒤 순차 실행 |
| 브라우저·수동 | P20 → P21 → P22/P23, 별도로 P24 | P22와 P23은 채널별 승인 뒤 병렬 |
| 통합 | P25 → P26 | 병렬 금지 |

→ 번호는 구현 편의가 아니라 위험 경계에 맞춘 순서입니다. 실제 의존조건은 각 파일의 `선행조건`이 우선합니다.

## 프롬프트 목록

- [P00A — 정보 책임 장소 오너 결정](p00a-data-ownership-owner-decision.md)
- [P00B — 승인된 정보 책임 장소 SOT 강제](p00-data-ownership-sot.md)
- [P01 — 후보 개인정보 보관·삭제·접근 기본 거부](p01-candidate-data-governance.md)
- [P02 — 채널별 허용 정책 레지스트리](p02-channel-policy-registry.md)
- [P03 — 포지션 명세와 시작 가능 관문](p03-position-spec-readiness.md)
- [P04 — AI RA 기반 서버 검증 게이트](p04-ai-ra-foundation-gate.md)
- [P05 — ClickUp 읽기 전용 포지션 스냅샷](p05-clickup-read-snapshot.md)
- [P06 — 재현 가능한 포지션 우선순위](p06-position-priority.md)
- [P07 — 수량·구성별 서치 부족분 계산](p07-search-gap-engine.md)
- [P08 — 읽기 전용 서치 작업 제안 생성](p08-work-proposal-generator.md)
- [P09 — Supabase 후보 자료 목록화](p09-supabase-candidate-inventory.md)
- [P10 — 로컬 SQLite 후보 아카이브 목록화](p10-sqlite-candidate-inventory.md)
- [P11 — Gmail 이력서 첨부 메타데이터 목록](p11-gmail-attachment-catalog.md)
- [P12 — 후보 동일인 연결과 사람 검토](p12-candidate-identity-resolution.md)
- [P13 — 근거 분리형 내부 후보 매칭](p13-deterministic-internal-match.md)
- [P14 — 중복 접촉·접촉금지 보호 장부](p14-contact-dedupe-ledger.md)
- [P15 — 실행 머신 등록과 능력 계약](p15-machine-registry.md)
- [P16 — 머신 생존·준비 상태 판정](p16-machine-heartbeat.md)
- [P17 — Supabase 지속 작업 큐](p17-durable-work-queue.md)
- [P18 — 채널·계정 사용권과 account fencing token](p18-channel-account-lease.md)
- [P19 — 머신 스케줄러와 장애 승계](p19-fleet-scheduler-recovery.md)
- [P20 — Aside 로컬 진단과 목표 탭 발견](p20-aside-local-discovery.md)
- [P21 — 사람 개입 즉시 브라우저 권한 폐기](p21-human-intervention-guard.md)
- [P22 — 사람인 허용 범위 후보 1명 관찰](p22-saramin-one-candidate.md)
- [P23 — 잡코리아 허용 범위 후보 1명 관찰](p23-jobkorea-one-candidate.md)
- [P24 — LinkedIn 수동 작업표와 결과 영수증](p24-linkedin-manual-packet.md)
- [P25 — 운영자 후보 검토 큐와 판정 영수증](p25-operator-review-queue.md)
- [P26 — 읽기 전용 한 바퀴와 장애 복구 그림자 운영](p26-shadow-loop-chaos.md)

## 완료 정의

| 상태 | 후속 프로젝트에서의 의미 |
|---|---|
| `DECISION_APPROVED` | 오너 결정이 필요한 선행조건만 충족 |
| `CONTRACT_PASS` | 순수 계산·계약 프로젝트의 선행조건만 충족 |
| `LIVE_PASS` | 외부 의존 프로젝트와 통합의 선행조건 충족 |
| `BLOCKED_OWNER`, `BLOCKED_AUTH`, `BLOCKED_POLICY`, `NOT_RUN`, `FAIL` | 어떤 “합격” 선행조건도 충족하지 못함 |

→ 프롬프트에서 단순히 “합격”이라고 쓴 경우 최소 `CONTRACT_PASS`를 뜻합니다. `LIVE_PASS`가 필요한 곳은 선행조건에 직접 적습니다.

프롬프트 파일 존재는 구현 완료가 아닙니다. 각 프로젝트의 목표 문서, RED→GREEN 증거, 전체 저장소 검사, Claude 1차와 Codex 2차 적대검증, 요구된 수준의 실제 영수증이 모두 있어야 해당 프로젝트만 완료입니다. `NOT_RUN`을 준비 완료나 조건부 통과로 보고하지 않습니다.

각 프롬프트의 `원자적 인수 기준`에는 그 프로젝트만 판정하는 `scripts/acceptance-ai-ra-<번호>.sh` 명령, 기대 `PASS AI_RA_<번호>` 표식, 1 이상의 실제 핵심 건수, 고장 주입 시 0이 아닌 종료값이 적혀 있습니다. P04는 이 이름 규칙의 모든 스크립트를 자동 발견하고 0건·중복·누락 실행·핵심 건수 0을 거부하는 `scripts/acceptance-ai-ra-all.sh`와 서버 workflow를 단독 소유합니다. 후속 프로젝트는 자기 스크립트만 추가하고 공용 workflow를 직접 수정하지 않습니다.
