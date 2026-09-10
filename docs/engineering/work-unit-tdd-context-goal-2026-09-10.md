# Work Unit TDD·맥락 계약 연결 goal — 2026-09-10

## 결론

현재 정본은 작업 단위의 순서를 설명하지만, 작업마다 합격 조건·실패 시험·사용한 파일 증거가 없을 때 자동으로 멈추지 않습니다. 이 작업은 그 세 가지가 빠지거나 오래되거나 조작되면 로컬과 서버 검사에서 실패하도록 만듭니다.

건너뛴 것은 없습니다. 첫 병렬 저장소 조회 세 건은 빠른 조회 모델의 사용 한도로 실행되지 않아 일반 검토 역할과 직접 조사로 전환했습니다. 운영·DB·외부 서비스는 변경하지 않으며 제품 배송 상태는 `NOT_APPLICABLE`입니다.

## 판단 근거

`docs/sot/strict-workflow.md`는 Work Unit(WU, 하나의 반증 가능한 작업 주장)의 필드 정본으로 `work-unit-policy.yaml`을 지목하지만 현재 `main`에는 파일이 없습니다. 기존 원칙 검사는 34건을 통과해도 그 누락을 잡지 못했습니다. 따라서 테스트의 존재가 아니라 RED(빠진 동작 때문에 먼저 실패하는 시험)의 원인, 기대값 불변, 선언한 저장소 맥락의 현재성까지 별도 검사해야 합니다.

> **무엇을** — 기계 판독 정책 한 벌과 WU manifest 검사기·정상/고장 fixture·서버 배선을 추가합니다.
> **왜** — 문서 절차만으로는 누락된 AC, 가짜 RED, 오래된 맥락, 검사기 무력화를 차단하지 못합니다.
> **버린 길** — 기존 `principles.yaml`에 새 P 원칙을 추가하는 길은 사용자가 금지했고 Type을 별도 권위로 만들기 때문에 제외했습니다.
> **대가** — WU 시작 전에 계약과 맥락 지문을 기록하고, RED·GREEN 커밋을 재실행할 수 있어야 합니다.
> **되돌리기** — 이 브랜치의 WU별 완료 커밋을 역적용하면 정책·검사·배선을 순서대로 제거할 수 있습니다. DB와 운영 데이터 복구는 없습니다.

## 현재 상태와 회수

- 시작 `main`: `f12ea335a0fd323bb3eec3ca0e300ae1ca9b0717`, 원본 변경 0건.
- 격리 작업공간: `/tmp/valuehire-wu-tdd-context-20260910`, 브랜치 `task/wu-tdd-context-contract-20260910`.
- 직접 읽은 정본: `coding-principles.md`, `principles.yaml`, `strict-workflow.md`, `hook-contracts.md`, `verification-commands.md`.
- 기존 구현 회수: `d07f613` 계열의 구조화 WU 정책과 Ruby 검사기는 재사용 후보이나, 현재 `main`에 없고 TDD/context 계약을 다루지 않아 그대로 합치지 않습니다.
- 기준 검사: `bash scripts/acceptance-principles-check.sh` → 종료값 0, `CHECKED: 34`.
- 코드 한도: P11의 직접 작성 파일 hard 600줄, 함수 hard 100줄. fixture는 면제지만 가능한 작게 유지합니다.

## T 계약: 입력·출력·오류·경계

### DB/API와 Type 선행 경계

- 이 작업은 저장소 내부 정책 검사이므로 다섯 WU 모두 DB와 외부 API 변경이 `NOT_APPLICABLE`입니다. 사유는 “데이터 저장, migration, 네트워크 호출, 외부 부작용이 없다”이며 빈 사유는 허용하지 않습니다.
- Type은 `docs/sot/work-unit-policy.yaml`의 기계 판독 manifest 형식입니다. DB/API보다 높은 별도 권위나 새 P 원칙이 아닙니다.
- 정책 형식과 아래 CLI 계약을 이 커밋에 먼저 고정한 뒤 RED를 만듭니다.

### 검사기 계약

- 입력: 저장소 안 일반 YAML 파일 1개. 정확히 1개 이상의 WU를 포함합니다.
- 출력: 성공은 `VERDICT: PASS`, 양수 `CHECKED`; 계약 위반은 `VERDICT: FAIL`, 구체 코드, 종료값 1; 실행 불능은 `VERDICT: NOT_RUN`, `CHECKED: 0`, 종료값 2입니다.
- 오류: 누락·빈 파일·링크·YAML 문법·중복 키·알 수 없는 필드·0개 WU는 닫힌 실패로 처리합니다.
- 경계: ID는 manifest 안에서 유일해야 하고, WU 하나는 주장과 EARS 형식 AC 각각 1개, counter-AC 1개 이상을 가집니다. DB/API/Type 및 입력·출력·오류·경계 계약은 RED보다 앞선 커밋에 있어야 합니다.
- RED: 명령 1개 이상, 실제 시험 1건 이상, 비정상 종료, `missing_behavior` 증거가 필요합니다. 문법/import/수집 오류나 0건은 RED가 아닙니다.
- GREEN: RED 이후 시험 파일은 고정합니다. 바꾸려면 별도 승인 커밋을 선언하고 그 커밋이 시험 파일만 바꾸며 승인 trailer를 가져야 합니다.
- 맥락: 선언한 저장소 상대경로마다 commit SHA, SHA-256, 읽기 증거를 요구하고, 선언 목록과 관측된 읽기 영수증 목록이 정확히 같아야 합니다. 현재 예상 HEAD·작업공간과 다르거나 전체 저장소를 근거로 선언하면 실패합니다. 해시는 바이트 접근을 증명하지만 사람이 의미를 이해했다는 사실까지 증명하지 않습니다.
- 저장소 적용: `docs/engineering/work-units/*.yaml`에 실제 WU manifest가 1개 이상 없거나 CI가 이 manifest를 실행하지 않으면 실패합니다. fixture 통과는 실제 WU 계약의 대체 증거가 아닙니다.
- NOT_APPLICABLE: 일반 단위 시험이 부적합한 UI·문서·설정·migration 변경만 사유와 대체 검증 명령 1개 이상으로 사용할 수 있습니다.

## Work Unit 장부

| ID | 하나의 AC | counter-AC | 검증 명령 | 선행 | 상태 |
|---|---|---|---|---|---|
| WU-1 | When manifest를 검사하면 필수 필드·유일 ID·AC 1개·counter-AC 1개 이상만 통과해야 합니다. | 파일 존재만으로 통과, 중복 ID, AC/counter-AC 누락 | `bash scripts/acceptance-work-unit-contract.sh schema` | 이 계약 | PASS · RED `14604d5` · GREEN `18e7535` |
| WU-2 | When RED→GREEN 이력을 검사하면 빠진 동작 RED와 시험 불변 이력만 통과해야 합니다. | 0건, 문법/import 오류, 기대값 동시 변경 | `bash scripts/acceptance-work-unit-contract.sh tdd` | WU-1 완료 | PASS · RED `f72c029` · 승인 시험 보정 `95110bd` · GREEN `f2c6099` |
| WU-3 | When 맥락 manifest를 검사하면 현재 HEAD·작업공간·파일 hash가 모두 맞아야 합니다. | filename-only, 전체 저장소, 오래된 HEAD, 다른 작업공간 | `bash scripts/acceptance-work-unit-contract.sh context` | WU-2 완료 | PASS · RED `bc5c4d0` · GREEN `2c25879` |
| WU-4 | If 단위 시험이 부적합하면 허용 종류·구체 사유·대체 검증 명령이 있어야 합니다. | 빈 사유, 임의 생략, 실행 명령 0개 | `bash scripts/acceptance-work-unit-contract.sh not-applicable` | WU-3 완료 | PASS · RED `3c418f5` · GREEN `597e5a1` |
| WU-5 | If 검사기나 서버 실행 줄을 무력화하면 독립 공격 검사가 실패를 관측해야 합니다. | exit 0, no-op, echo-only, 항상 거짓 조건 | `bash scripts/acceptance-work-unit-contract-mutations.sh` | WU-4 완료 | PASS · RED `672283c` · 시험 보정 `c78f930` · GREEN `faa8b6f` |
| WU-2R | When DB/API/Type 선행 근거를 검사하면 각 근거 파일이 contract commit에 이미 존재해야 합니다. | RED에서 뒤늦게 만든 계약 파일 경로를 manifest에 적어 통과 | `bash scripts/acceptance-work-unit-contract.sh tdd` | WU-1~WU-5 완료 뒤 감사 보정 | PASS · 계약 `3c1ad8c` · RED `aa87570` · GREEN `1bdb504` |
| WU-2R2 | When RED 이후 시험 불변을 검사하면 첫 GREEN 뒤 현재 HEAD까지의 무승인 변경도 거부해야 합니다. | GREEN 다음 커밋에서 기대값 변경 | `bash scripts/acceptance-work-unit-contract.sh tdd` | V1 감사 재현 | PASS · RED `14dad68` · GREEN `0cd7731` |
| WU-5R | When 저장소 WU gate를 실행하면 실제 WU manifest 1개 이상과 CI 실행 배선이 없을 때 실패해야 합니다. | fixture만 통과하고 실제 WU manifest가 0개인 저장소 | `bash scripts/acceptance-work-unit-repository.sh` | WU-2R2 완료 후 V1 감사 재현 | CONTRACT |

각 WU는 계약 커밋 → RED 커밋 → 최소 GREEN 커밋 → 회귀·적대검증 → 완료 커밋 순서로 닫습니다. 앞 WU의 완료 커밋 전에는 다음 WU 파일을 시작하지 않습니다.

## Harness·검증·중단 조건

- Gate 0/1: 이 문서와 정책 Type, 시작 상태, 원칙 34건을 고정합니다.
- Gate 2/3: 격리 작업공간에서 각 WU의 올바른 RED를 보존한 뒤 최소 구현으로 GREEN을 만듭니다.
- Gate 3.5/4: fixture → acceptance → mutation → pre-push 글로브 → CI의 실제 호출을 추적합니다.
- V1은 구현과 분리된 검토자가 검사기를 깨고, V2는 새 맥락에서 V1의 명령·위치·판정을 재현하고 반대로 과장을 공격합니다.
- 필수 명령이 FAIL/NOT_RUN/BLOCKED면 완료하지 않습니다. push, PR, merge, deploy는 실행하지 않습니다.
- 원본 작업공간의 HEAD와 `git status --porcelain=v1 -uall`이 시작값과 다르면 중단하고 복구합니다.

## 적대 검증 로그

WU-1~WU-5 원문과 종료값은 [실행 증거 장부](work-unit-tdd-context-evidence-2026-09-10.md)에 보존합니다. 필수 로컬 WU 범위는 모두 실행했습니다.
