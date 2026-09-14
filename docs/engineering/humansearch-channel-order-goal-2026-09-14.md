# HS-11 채널 순서 개정 goal — 2026-09-14

## 1층 — 결론

이 WU는 잡코리아를 사람인 실제 완주 뒤에만 시작할 수 있다는 과거 HS-11 의존성을 대체한다. 공통 안전 선행은 유지하고, 사람인 전용 선행은 잡코리아 필수 선행에서 분리한다.

제품 배송 상태: NOT_APPLICABLE. 이 WU는 문서 계약만 추가하며 포털 접속, origin 실측, 검색 입력, 후보 저장, 결제, 카드 삭제를 하지 않는다.

## 2층 — 판단 근거

2026-09-14 v5 지시는 잡코리아와 RPS를 이번 필수 대상으로 두고, 사람인 미결제가 다른 채널 작업을 막지 않게 하라고 한다. 동시에 실제 잡코리아 접속 전에는 기존 2026-09-14 실행 승인 범위 안에서 브라우저 접속·중단 증명과 채널별 정확한 origin 목록이 현재 계약으로 확정·검증돼 있어야 한다. 이 문구는 새 사용자 재승인 게이트가 아니다.

과거 장부의 HS-11은 선행을 HS-07과 HS-05.08로 두어 사람인 완주가 잡코리아 확장의 선행처럼 읽힌다. 이번 WU는 그 부분을 공통 선행과 사람인 전용 선행으로 나눈다.

## 소유 범위

이번 WU에서 쓰는 파일은 아래 두 개뿐이다.

- `docs/sot/humansearch-channel-order-contract.md`
- `docs/engineering/humansearch-channel-order-goal-2026-09-14.md`

수정하지 않는 파일:

- `docs/sot/humansearch-browser-contract.md`
- 기존 CI, acceptance script, shared SOT
- 제품 코드와 fixture

## 읽은 근거

- Desktop v5 원문 `/Users/kangsangmo/Desktop/hs-next-prompt-v5-20260914.md` §6: 기존 HS-11의 HS-07 사람인 완주 선행을 명시적으로 개정하고, 채널 공통 선행과 사람인 전용 구현·완주 증거를 분리하라는 최신 결정. SHA-256 `12d99b3f304100eedd587a956a5ffcc8c2340ffa3ce9e220624d74938dddfc6e`.
- Desktop v5 원문 §7: 잡코리아 HS-11.01→02→07→08→09→10 진행 순서.
- Desktop v5 원문 §7 사람인: 실제 막힌 카드만 보류하고 카드·회귀시험·장기 목표는 삭제하지 말라는 결정.
- handoff 기준: `task/hs-cross-pc-handoff-20260914` `fc6beedc78019862bc2f1b3bf4c4ad3bbd8e845b`. 현재 이 기준에는 v5 Desktop 원문 파일이 Git 추적 파일로 포함돼 있지 않아 Desktop 원문 hash를 함께 남긴다.
- 과거 장부 exact Git provenance: `task/hs-0004-recovery-20260910` `464220fb2d25193c626d3a8fb514661dab863d25:docs/engineering/humansearch-next-issues-wu-2026-09-10.md` HS-11. 기존 선행 `HS-07, HS-05.08`와 잡코리아 단계 목록.
- `docs/sot/humansearch-browser-contract.md`: 브라우저·프로필·사용권·STOP·NOT_RUN 경계.

## 인수 기준

### AC-1 과거 HS-07 선행 대체

When 잡코리아 HS-11 작업을 계획할 때 시스템은 사람인 HS-07 실제 완주를 필수 선행으로 요구하지 않아야 하며, 대신 공통 증거·저장·브라우저 권한·사용권·STOP·checkpoint·후보 잠금 선행과 잡코리아 전용 선행을 요구해야 한다.

검증 명령:

```bash
rg -n 'HS-07|공통 선행|사람인 전용|잡코리아.*HS-11.01|필수 선행' docs/sot/humansearch-channel-order-contract.md
```

→ 해석: 과거 HS-07 선행이 제거되고 공통 선행과 사람인 전용 선행이 분리됐는지 확인한다.

counter-AC: 잡코리아 시작 전 사람인 1명 완주를 다시 필수 조건으로 둔다.

### AC-2 잡코리아 six-step 계약

When 잡코리아를 실행할 때 시스템은 HS-11.01 화면 계약, HS-11.02 검색 조건, HS-11.07 상세 열람, HS-11.08 증거 저장, HS-11.09 목록 복귀, HS-11.10 1명 완주를 각각 독립 인수 기준·오류·fixture 출처·기존 실행 승인 범위 안의 라이브 조건으로 검증해야 한다.

검증 명령:

```bash
rg -n 'HS-11.01|HS-11.02|HS-11.07|HS-11.08|HS-11.09|HS-11.10|fixture 출처|라이브 조건' docs/sot/humansearch-channel-order-contract.md
```

→ 해석: 잡코리아 여섯 단계가 각자 인수 기준, 오류, fixture 출처, 라이브 조건을 갖는지 확인한다.

counter-AC: 잡코리아 한 단계 성공을 나머지 단계의 성공으로 확대한다.

### AC-3 origin 추측 금지

When 잡코리아 라이브 조건을 검토할 때 시스템은 실제 origin 값을 추측해 고정하지 않고, precise-origin 후속 계약이 공식 근거 또는 승인된 실제 관측으로 exact origin을 확정할 때까지 잡코리아 라이브를 `NOT_RUN`으로 둬야 한다.

검증 명령:

```bash
rg -n 'precise-origin|origin.*추측|exact origin|NOT_RUN' docs/sot/humansearch-channel-order-contract.md
```

→ 해석: 실제 origin 값이 추측으로 고정되지 않고 후속 계약의 미실행 상태로 남는지 확인한다.

counter-AC: 확인하지 않은 잡코리아 origin을 문서에 하드코딩한다.

### AC-4 사람인 제한 보류 경계

When 사람인 상태를 보고할 때 시스템은 목록·검색·상세 중 실제로 확인된 막힌 카드만 이유와 해제 조건을 붙여 보류해야 하며, 결제와 카드 삭제를 하지 않아야 한다.

검증 명령:

```bash
rg -n '사람인|실제 확인|막힌 카드|결제|카드 삭제|목록|검색|상세' docs/sot/humansearch-channel-order-contract.md
```

→ 해석: 사람인은 실제로 막힌 카드만 보류하고 결제·카드 삭제를 하지 않는 경계를 확인한다.

counter-AC: 미실측 제한을 결제 실패로 단정하거나 사람인 카드를 삭제한다.

### AC-5 중복 후보와 다른 후보 진행 분리

When 잡코리아 후보를 순회할 때 시스템은 같은 후보 key 재열람을 차단해야 하지만, 저장 실패·STOP·권한 회수·drift가 없는 경우에는 다른 후보 key의 새 잠금과 checkpoint 성공 뒤 다음 후보 진행을 허용할 수 있어야 한다.

검증 명령:

```bash
rg -n '중복 후보|다른 후보|candidate key|저장 실패 뒤|새 잠금|checkpoint' docs/sot/humansearch-channel-order-contract.md
```

→ 해석: 같은 후보 재열람 차단과 다른 후보 진행 허용 조건이 분리돼 있는지 확인한다.

counter-AC: 중복 후보 차단을 전체 채널 중단으로 오해하거나, 저장 실패 뒤 다른 후보로 계속 진행한다.

## 비범위

- 실제 잡코리아, 사람인, RPS 접속.
- 잡코리아 origin 확정.
- 화면 fixture 생성.
- 저장·증거·브라우저 shared SOT 수정.
- RPS 프로젝트 생성, 필터 업데이트, LinkedIn 상세 저장.
- 결제, 카드 삭제, 브라우저 조작.
- CI 또는 acceptance script 추가.

## 검증 계획

```bash
rg -n 'HS-07|공통 선행|사람인 전용|잡코리아.*HS-11.01|필수 선행' docs/sot/humansearch-channel-order-contract.md
rg -n 'HS-11.01|HS-11.02|HS-11.07|HS-11.08|HS-11.09|HS-11.10|fixture 출처|라이브 조건' docs/sot/humansearch-channel-order-contract.md
rg -n 'precise-origin|origin.*추측|exact origin|NOT_RUN' docs/sot/humansearch-channel-order-contract.md
rg -n '사람인|실제 확인|막힌 카드|결제|카드 삭제|목록|검색|상세' docs/sot/humansearch-channel-order-contract.md
rg -n '중복 후보|다른 후보|candidate key|저장 실패 뒤|새 잠금|checkpoint' docs/sot/humansearch-channel-order-contract.md
git diff --check
```

→ 해석: 이 계획은 문서 계약 존재와 diff hygiene만 확인한다. 라이브 권한 충족이나 제품 동작 성공을 증명하지 않는다.

## 현재 검증 제한

이 WU의 검증은 문서 AC 대조와 diff hygiene까지만 한다. 잡코리아 라이브, precise-origin 확인, 브라우저 권한 runtime 증명, 저장 구현 증명은 모두 `NOT_RUN`이다. 합성 fixture가 생겨도 계약 단위 시험일 뿐 실제 잡코리아 화면 관측으로 승격하지 않는다. 이 문서 검토는 라이브 권한 충족 증거가 아니다.
