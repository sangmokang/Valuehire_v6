# LOCAL-VH-WU3B-20260827 — Strict 변경 전달 사슬 완결

## 문제 정의

현재 checkpoint 판정은 작업 폴더의 최신 run ledger와 secret pattern을 입력으로 삼을 수 있어, 검사 대상과 정책을 함께 완화하면 거짓 합격을 만들 수 있다. Issue, 격리 branch/worktree, WU 커밋, 검증 결과, 원격 PR/CI, merge 이후 deploy/live verify를 한 대상 해시에 연결하는 검증 가능한 장부도 없다.

GitHub Issue 생성은 외부 쓰기이므로 승인 전에는 실행하지 않는다. 이 로컬 계약의 ID를 추적 키로 사용하고, 실제 GitHub Issue가 생기면 별도 원격 ID를 추가하되 이 ID를 바꾸지 않는다.

## EARS 인수 기준

- AC-1 — When checkpoint가 scope를 판정할 때, 시스템은 명시적 `run_id`와 `wu_id`가 가리키는 Git index blob 한 개만 읽고 다른 작업 폴더 ledger를 자동 선택하지 않아야 한다.
- AC-2 — If CLI scope와 ledger scope가 동시에 주어지면, 시스템은 두 집합이 정확히 같을 때만 계속하고 불일치하면 종료값 1을 반환해야 한다.
- AC-3 — When checkpoint가 비밀 검사를 수행할 때, 시스템은 index blob, 승인 SHA가 일치하는 로컬 입력, 또는 읽기 전용 산출물에서 읽은 pattern만 사용해야 한다.
- AC-4 — When 추적 장부를 검증할 때, 시스템은 Issue, branch, worktree, WU ID, RED/구현 commit, 대상 SHA, 명령·시각·종료값·전체 출력 지문을 한 사슬로 검증해야 한다.
- AC-5 — If ledger 삭제·복제·재정렬·timestamp 역행·WU/commit 불일치·stale branch/worktree·검사 대상 0개·무출력·부분 출력 중 하나가 있으면, 시스템은 종료값 1을 반환해야 한다.
- AC-6 — While 사용자 merge 증거가 없으면, 시스템은 `checkpoint readiness`와 `overall T`를 `NOT_RUN`보다 높게 승격하지 않아야 한다.
- AC-7 — When merge 이후 deploy 또는 live verify 증거를 기록할 때, 시스템은 merge 증거와 분리된 단계로 저장하고 merge가 없으면 이를 합격으로 인정하지 않아야 한다.
- AC-8 — When 보호 집합이 실행될 때, 시스템은 `verify.sh`, gate, scanner, mutation validator, P11 정본, run ledger, 두 secret pattern 경로, runner와 실행 설정의 승인 지문을 확인해야 한다.

## counter-AC

- unstaged ledger scope를 `["**"]`로 바꾼 뒤 staged 범위 검사가 통과한다.
- unstaged secret pattern을 완화한 뒤 staged secret 검사가 통과한다.
- 이름이 다른 최신 ledger나 과거 timestamp를 자동 선택한다.
- 장부 내부 hash만 다시 계산해 승인 대상 SHA 없이 과거 결과를 바꾼다.
- WU ID가 없는 commit이나 다른 WU trailer를 가진 commit을 연결한다.
- stdout이 비었거나 일부만 저장됐는데 command를 PASS로 센다.
- 로컬 GREEN을 GitHub CI GREEN으로 기록한다.
- merge 전 readiness 또는 overall T를 PASS로 기록한다.
- merge 전 deploy/live verify를 PASS로 기록한다.

## 입출력·오류·경계 계약

입력은 명시적 run ID, WU ID, 기준 commit, 승인 authority SHA, Git index, 선택적 로컬 pattern SHA, 추적 장부 commit SHA와 blob SHA다. 출력은 구조화된 단일 JSON 판정과 종료값 `0=PASS`, `1=FAIL`이다. 입력 누락, 해석 실패, 대상 0개, 무출력, hash 불일치, 모호한 선택은 모두 종료값 1이다. 비밀 원문은 출력하거나 장부에 저장하지 않는다.

동시 실행은 공유 임시 파일을 사용하지 않고 실행별 `mktemp` 디렉터리만 사용한다. 재시도는 새 evidence record로 남기며 이전 실패를 삭제하거나 PASS로 덮어쓰지 않는다. full 40자리 commit SHA만 승인 기준으로 허용하고 branch name을 authority로 허용하지 않는다.

## WU와 영향 반경

| WU | 책임 | 주 영향 파일 |
|---|---|---|
| WU-3b-1 | run-ledger 단일 권한 출처 | checkpoint gate, ledger policy, 회귀 테스트 |
| WU-3b-2 | secret-pattern 신뢰 경계 | trusted secret runner, `verify.sh`, 회귀 테스트 |
| WU-3b-3 | Issue→commit→evidence 추적 장부 | trace validator, schema, 회귀 테스트 |
| WU-3b-4 | 최신 SHA V1/V2 준비·보존 | adversarial evidence 계약과 회귀 테스트 |
| WU-3b-5 | PR/CI/merge/deploy/live 상태 | delivery state, acceptance, hook/CI/SOT 배선 |

## 데이터 안전 조건

- 비밀 pattern 원문과 검출 원문을 문서·장부·stdout에 저장하지 않는다.
- 사용자 기존 dirty 파일과 원본 index는 시작·종료 지문이 같아야 한다.
- 파괴 반례는 `mktemp` 아래 격리 저장소에서만 실행한다.
- 원격 push, PR 생성·수정, merge, deploy, 메일·포털·운영 쓰기는 승인 전 실행하지 않는다.

## 롤백

작업 브랜치를 병합하지 않고 worktree를 제거하면 원본은 변하지 않는다. 병합 뒤 되돌릴 때는 WU 커밋을 역순으로 revert하고, checkpoint acceptance와 기존 전체 strict 명령을 재실행한다. 추적 장부의 실패 기록은 삭제하지 않고 새 rollback evidence로 연결한다.

## 비범위

- GitHub Issue/PR 생성 또는 수정
- push, merge, deploy, live 운영 호출
- 기존 unrelated dirty 변경의 수정·stage·stash·삭제
- secret 원문의 저장
