# P1 장부 검증과 전체 완료 진단 분리 — goal (2026-08-19)

## 결론

오너는 원칙 장부의 실제 미충족 상태를 그대로 두면서, 장부가 올바른 형식과 연결을 갖췄는지 확인하는 필수 검사와 32개 전체 완료 여부를 알리는 진단을 분리하는 정책을 승인했다. 이번 작업은 그 승인 범위만 구현하며, PR #31을 병합하거나 원칙 상태를 좋게 바꾸지 않는다.

현재 전체 완료 판정은 32개 중 31개 미충족을 정확히 알리지만 같은 작업의 뒤쪽 검사를 시작하지 못하게 한다. 분리 뒤에도 이 미충족 원문은 남고, 구조 검사·P3·기존 회귀 검사는 독립적으로 끝까지 실행돼야 한다.

## 판단 근거

`.github/workflows/verify.yml:33-46`은 필수 파일·뮤테이션·전역 파일 보호 검사 뒤에 인자 없는 전체 완료 명령을 실행하고, `.github/workflows/verify.yml:48-213`의 기존 회귀 검사를 같은 `verify` 작업 안에 둔다. GitHub Actions의 한 작업은 앞 단계가 실패하면 기본적으로 뒤 단계를 실행하지 않으므로, 현재 `P1_UNMET: 31/32`가 원칙 검사가 아닌 다른 회귀 검사의 실행 증거까지 없앤다.

`scripts/acceptance-principles-check.sh:346-348`의 `--schema-only`는 장부 구조·경로·정적 연결만 검사하고, `scripts/acceptance-principles-check.sh:399-416`의 기본 전체 모드는 32개 완료 여부를 따로 계산한다. 새 판정기를 만들 필요 없이 기존 두 의미를 작업 경계로 분리할 수 있다.

버린 해석은 “31개 미충족을 완전으로 바꾸거나 전체 명령을 삭제해 서버 검사를 초록으로 만든다”이다. 이는 오너 정책, `docs/sot/principles.yaml:2`, 기존 P1 계약을 모두 거스르므로 선택하지 않는다.

※ 저장소 루트에는 `AGENTS.md`가 없었다. 이번 대화에 제공된 AGENTS 계약을 적용했고, PR #31 실제 파일은 `worktrees/strict-principles-yaml`에서 읽었다. 착수 시 이 작업트리는 깨끗했으며 원격보다 기존 조사 커밋 `95329e2` 하나 앞서 있었다. 그 커밋과 원칙 상태는 사용자 소유 선행 작업으로 보존한다.

## 결정 카드

**무엇을** — `principles-structure` 필수 작업, `p1-completion-diagnostic` 진단 작업, 기존 `verify` 회귀 작업을 서로 독립시킨다.

**왜** — 장부 자체가 깨졌는지, 아직 원칙이 덜 끝났는지, 다른 회귀가 깨졌는지를 각각 따로 판정해야 한 실패가 다른 증거를 지우지 않는다.

**버린 길** — 전체 명령 삭제·상태 상향·같은 작업 안의 실패 무시만 추가하는 길은 미충족 사실을 숨기거나 뒤 단계 실행 경계를 다시 섞으므로 버린다.

**대가** — 서버 화면에 필수 검사와 진단 결과가 따로 표시되고, 초록인 필수 검사만 보고 32개가 끝났다고 오해할 수 있다. 문서와 PR 본문에 이 차이를 반복해 명시해야 한다.

**되돌리기** — workflow의 세 작업 경계를 이전 단일 `verify` 작업으로 되돌릴 수 있다. 다만 그러면 31/32 미충족이 뒤 검사를 다시 가리므로, 되돌릴 때는 오너가 그 증거 손실을 다시 승인해야 한다.

## 1. 현재 상태와 근본 원인

- `.github/workflows/verify.yml:15-24` — P3는 이미 별도 `p3` 작업에서 P1과 독립 실행된다.
- `.github/workflows/verify.yml:26-47` — 구조 검사와 전체 완료 판정이 `verify` 작업 앞부분에 섞여 있다.
- `.github/workflows/verify.yml:48-213` — 비밀 검사, HumanSearch 검사, 기록 전량 검사, 훅·셸·데이터 노출 회귀가 전체 완료 판정 뒤에 있어 현재 서버에서 실행되지 않는다.
- `scripts/acceptance-principles-check.sh:14-21` — `--schema-only`, `--pre-push`, `--full` 세 실행 방식이 이미 존재한다.
- `scripts/acceptance-principles-check.sh:331-348` — 구조가 맞으면 `SCHEMA_OK`를 내고 구조 전용 실행은 성공으로 끝난다.
- `scripts/acceptance-principles-check.sh:399-416` — 인자 없는 기존 전체 명령은 31개 미충족을 `P1_UNMET`으로 출력하고 실패한다.
- 착수 기준선 직접 실행 — 전체 명령은 `P1_UNMET: 31/32`, 구조·연결은 `SCHEMA_OK: 32/32`; 현재 상태 집계는 `완전=1 부분=12 없음=7 해당없음=9 미확인=3`이다.
- 근본 원인은 판정 로직이 아니라 작업 경계다. 서로 다른 의미의 결과를 한 순차 작업에 넣어 첫 의도된 실패가 뒤쪽 독립 검사를 취소한다.

## 2. 원자적 인수 기준

### AC1 — 필수 구조 작업

`principles-structure` 작업은 필수 파일 존재, `acceptance-principles-mutations.sh`, 전역 skill guard, `acceptance-principles-check.sh --schema-only`를 실행한다. 어느 하나라도 실패하면 이 작업은 실패한다.

검증 명령: `bash scripts/acceptance-principles-mutations.sh`와 workflow 정적 배선 뮤테이션.

반대 조건: 작업 이름 변경, `--schema-only` 제거, 전체 모드 대체, `continue-on-error` 추가, 명령 삭제 중 하나라도 정적 시험을 통과하면 가짜다.

### AC2 — 별도 전체 완료 진단

`p1-completion-diagnostic` 작업은 기존 명령 `bash scripts/acceptance-principles-check.sh`를 인자 없이 실행해 31/32 미충족 원문과 실패 결과를 그대로 만든다. 이 결과는 진단으로 명시되며 다른 필수 작업의 실행을 막지 않는다.

검증 명령: 전체 명령 직접 실행에서 종료값 1과 `P1_UNMET: 31/32`를 함께 확인하고, workflow 정적 배선에서 정확한 작업 이름·기본 전체 모드·독립성·진단 처리 방식을 확인한다.

반대 조건: `--schema-only` 또는 `--pre-push`로 바뀌거나, `|| true`로 원문 실패가 지워지거나, 진단 작업이 `verify`/`p3`의 선행 조건이 되면 가짜다.

### AC3 — 후속 회귀 독립 실행

기존 `verify` 작업의 비밀 검사부터 마지막 mechanism 명부 대조까지는 P1 전체 완료 진단과 선후 의존성이 없어야 한다. P1이 실패해도 `verify`와 `p3`가 서버에서 각각 끝까지 실행돼야 한다.

검증 명령: workflow 정적 배선 뮤테이션과 실제 GitHub Actions 작업별 로그.

반대 조건: `verify` 또는 `p3`에 `needs: p1-completion-diagnostic`가 생기거나, 전체 명령이 다시 `verify` 안에 들어가면 실패다.

### AC4 — 원칙 상태와 P3 방어 보존

`docs/sot/principles.yaml`의 상태값은 이번 변경에서 수정하지 않는다. P3의 검사 범위, 실제 훅 자기무력화 공격 차단, 정상 커밋과 무해한 자기개선 통과 대조군을 그대로 유지한다.

검증 명령: `git diff -- docs/sot/principles.yaml`, `bash scripts/acceptance-silent-failure-lint-mutations.sh`.

반대 조건: 원칙 상태가 더 좋아지거나, 35개 P3 공격/대조군 중 하나라도 빠지거나 기대값이 완화되면 중지한다.

### AC5 — 문서와 PR의 의미 일치

`docs/sot/verification-commands.md`와 기존 P1/P3 goal 문서는 필수 검사, 진단 검사, 실패 의미, 병합 판단을 같은 말로 설명한다. PR 본문은 필수 검사가 초록이어도 32개 완료를 뜻하지 않으며 현재 진단은 31/32 미충족이라고 명시한다.

검증 명령: 문서 대조, `git diff --check`, 실제 `gh pr view 31 --json title,body,url` 재조회.

반대 조건: “CI 초록 = 32개 완료” 또는 branch protection을 확인 없이 required check로 표현하면 실패다.

### AC6 — 원격 실행 증거

PR #31의 새 커밋에서 `principles-structure`, `p3`, `verify`, `p1-completion-diagnostic`의 실제 결과와 로그를 확인한다. 전체 완료 진단의 `P1_UNMET` 원문을 저장소 안 이 문서의 적대 검증 로그에 보존한다.

검증 명령: `gh pr checks 31`, `gh run view <run> --job <job> --log`, branch protection API 조회.

반대 조건: 로컬 결과를 서버 결과로 부르거나, 진단 원문 없이 “의도된 실패”라고만 요약하거나, 보호 설정 조회 실패를 보호 활성으로 단정하면 실패다.

## 3. RED → GREEN 계획

1. `scripts/acceptance-principles-mutations.sh`에 현재 workflow가 실패하도록 먼저 시험을 추가한다.
2. RED는 정확한 작업 이름, 구조 작업의 `--schema-only`, 진단 작업의 인자 없는 전체 명령, 독립 작업 경계, 필수 작업의 실패 무시 금지를 동시에 요구한다.
3. workflow만 최소 변경해 세 작업을 분리한다.
4. 기존 장부 판정기, P3 판정기, 훅과 기대값은 수정하지 않는다.
5. 문서 세 곳과 PR 본문을 실제 구현과 같은 의미로 갱신한다.

## 4. Harness 게이트 진행

- 게이트 0: PR #31 작업트리와 원격 상태, 기존 RED 두 종류를 분리 확인했다. 전체 P1은 의도된 실패, 구조·P3는 통과 기준이다.
- 게이트 1: 이 문서의 AC1~AC6을 각각 독립 단언으로 고정한다.
- 게이트 2: 기존 PR #31 전용 worktree에서 RED 커밋을 먼저 만든다. `main`은 읽기 전용이다.
- 게이트 3: workflow·문서 최소 변경으로 GREEN을 만든다.
- 게이트 4: 사용자가 지정한 로컬 명령 전부와 원본 작업트리 무변경 공격 시험을 실행한다.
- 게이트 5: 작은 Lore 커밋을 PR #31 브랜치에만 push하고 실제 서버 로그와 원격 PR 본문을 다시 읽는다.
- 게이트 6: 병합·배포·메일·외부 운영 변경 없이 오너 검토 대기로 끝낸다.

## 5. 새 게이트 설계 3원칙

- [x] 자기 선언 검증자 — workflow의 작업 이름·명령·실행 방식은 `acceptance-principles-mutations.sh`가 YAML 구조로 확인한다. workflow 주석이나 작업 자체의 이름만 믿지 않는다.
- [x] 실패 방향 반전 — 진단 명령의 실제 실패는 원문으로 보존하되 다른 필수 작업 실행을 막지 않는다. 필수 구조 작업에 실패 무시가 생기면 시험이 실패한다.
- [x] 차단/통과 쌍 — 차단: 작업 이름·모드·독립성 변경, 상태 상향, P3 자기무력화 공격. 통과: 정상 구조, 31/32 진단, 정상 커밋, 검사기 주석만 바꾼 무해한 자기개선.

## 6. SOT 체크리스트

- [x] 대화에 제공된 `AGENTS.md` 계약.
- [x] `docs/sot/principles.yaml` — 상태와 31/32 미충족 불변식.
- [x] `docs/sot/verification-commands.md` — 실제 로컬·서버 명령 목록.
- [x] `docs/sot/coding-principles.md` — P1, P3, P13, P15, P20.
- [x] `docs/sot/hook-contracts.md` — pre-commit/pre-push와 CI의 책임 경계.
- [x] `docs/engineering/strict-principles-yaml-goal-2026-08-19.md` — P1 장부 설계와 과거 원격 실패.
- [x] `docs/engineering/p3-syntax-aware-reachability-goal-2026-08-19.md` — P3 독립 작업과 35/35 공격 증거.
- [x] `.github/workflows/verify.yml`, `scripts/acceptance-principles-check.sh`, `scripts/acceptance-principles-mutations.sh`, `scripts/acceptance-silent-failure-lint.sh`, `scripts/acceptance-silent-failure-lint-mutations.sh`, `hooks/pre-commit`, `hooks/pre-push`.

## 7. 비범위와 중지 조건

- 원칙 32개의 실제 구현 확대, 상태 상향·은폐, P3 범위 변경, 기존 기대값 완화는 비범위다.
- `main` 직접 push, PR 병합, 배포, 메일, 외부 운영 변경은 하지 않는다.
- branch protection은 API 응답이 확인된 범위만 보고한다.
- 기존 P3·원칙 상태·회귀 검사 중 하나라도 악화되면 고치지 않은 채 진행했다고 보고하지 않고 중지한다.
- 필수 로컬 검사나 원격 검사가 `NOT_RUN`으로 남으면 완료가 아니라 진행 중이다.

## 8. 적대 검증 로그

Claude 1차 전체 원문은 `docs/engineering/p1-validation-separation-claude-raw-2026-08-19.txt`,
실행 명령과 Codex 2차 재현·반박 표는
`docs/engineering/p1-validation-separation-adversarial-evidence-2026-08-19.md`에 보존했다.
로컬 1차·2차 검증은 통과했지만 원격 `P1_UNMET` 로그 원문은 아직 없다. push 뒤 이 절과 증거 문서에 원격 실행 ID·job 결과·원문을 추가하기 전에는 AC6을 완료로 판정하지 않는다.
