# codex 코드 리뷰 판정 원문 — v4 환경 복구 개입 (2026-08-18)

> 대상: main 재배치·충돌 해소 2파일·기준선 커밋 (Claude 개입분). 검증자: codex CLI(읽기 전용). 원문 보존 — 무수정. 후속 조치: 잡코리아 파일 보관본 복원·저장 대상 16건 원복·워크트리 청소(같은 날, Claude).

VERDICT: FAIL

최고 심각도: 높음 — 잡코리아 포지션 등록이 제출 직전에 확정적으로 중단됩니다.

## 결론

- 인터넷 연결 실패로 GitHub 서버의 지금 상태는 확인하지 못했습니다. 다만 이 컴퓨터에 기록된 본선과 원격 기준점은 모두 `8a20289e`로 정확히 일치합니다.

- 본선 이력 정리 과정에서 두 작업이 사라지지는 않았습니다. 두 작업 모두 원격에 내용이 똑같이 존재하며, 원래 기록도 다른 가지에서 그대로 찾을 수 있습니다.

- 잡코리아 충돌 해결은 실패했습니다. 원격판과 보관판을 잘못 결합해, 등록 버튼을 누르기 직전에 존재하지 않는 값을 읽으면서 모든 정상 등록이 중단됩니다.

- 충돌 복원 과정에서 원래 “아직 저장 대상으로 고르지 않았던” 16개 파일이 저장 대상으로 바뀌었습니다. 이 상태에서 저장하면 운영 도구와 실행 결과 파일까지 의도치 않게 함께 들어갈 수 있습니다.

- 설정 목록 병합 자체는 정확한 합집합이며 문법 오류와 중복은 없습니다. 그러나 현재 160개 항목 중 153개가 이미 사라진 임시 시험 폴더를 가리키고 있어 관리 상태는 좋지 않습니다.

- `12602238`의 “실패 파일 17개·실패 검사 22개” 기록은 원문 로그와 정확히 일치합니다. 다만 해당 별도 작업 폴더는 자동 생성 파일 2개가 다시 바뀐 채 남아 있어 착수 준비가 끝난 깨끗한 상태는 아닙니다.

## 판단 근거

리베이스(rebase, 기존 작업을 최신 본선 위에 다시 배치하는 절차), 스태시(stash, 미완성 변경을 임시 보관하는 공간), 스테이징(staging, 다음 저장에 넣겠다고 표시하는 상태), 워크트리(worktree, 같은 저장소를 별도 폴더에서 작업하는 기능)를 아래처럼 분리해 판정했습니다.

| ID | 대상 | 판정 | 심각도·사업 영향 |
|---|---|---|---|
| R1 | 본선 재배치와 두 작업의 유실 여부 | 통과 | 유실 증거 없음 |
| R2 | 잡코리아 충돌 해결 | 실패 | **높음 — 잡코리아 등록이 제출 전에 전부 중단됨** |
| R3 | `tsconfig.json` 합집합 | 부분 통과 | **낮음 — 즉시 파손 증거는 없지만 임시 경로 153개가 정식 설정에 잔존** |
| R4 | 기준선 커밋 `12602238` 내용 | 통과 | 실패 파일·검사 수가 로그와 일치 |
| R5 | 기준선 워크트리 청결성 | 실패 | **중간 — 후속 P0 저장에 자동 생성 찌꺼기가 섞일 수 있음** |
| R6 | 본선 작업 상태 보존 | 실패 | **중간 — 16개 파일의 저장 대상 여부가 바뀌어 accidental commit 위험** |
| R7 | 스태시 보존 | 통과 | `stash@{0}`가 그대로 남아 있고 삭제·복원되지 않음 |

→ 무엇을 판정했나: 코드 내용, 저장 이력, 임시 보관본, 별도 작업 폴더를 서로 독립적으로 확인했습니다.  
→ 좋은 소식: 본선 커밋과 기준선 실패 목록은 맞습니다. 나쁜 소식: 실제 등록 코드와 저장 대상 경계가 훼손됐습니다.

### 주요 갈림길과 버린 해석

1. 커밋 제목이 같다는 이유만으로 “중복”이라고 인정하지 않았습니다. 변경 내용의 지문까지 비교해 동일함을 확인했습니다. 이 판단이 틀리면 8월 10일 위클리 문서 일부가 사라진 것이 됩니다.

2. 잡코리아 오류가 원격판부터 있던 문제라는 해석을 버렸습니다. 원격판에는 문제의 값이 아예 없고, 보관판에는 정의와 사용이 모두 있지만, 현재판에는 사용만 남았습니다. 즉 충돌 결합 과정에서 만들어진 새 오류입니다.

3. 존재하지 않는 설정 경로가 곧바로 형 검사를 깨뜨린다는 해석도 버렸습니다. 깨끗한 별도 작업 폴더에서는 같은 종류의 경로를 둔 채 형 검사가 통과했습니다.

4. `22건`을 전체 오류 수라고 확대하지 않았습니다. 원문은 “실패한 개별 검사 22개”와 “검사 시작 전 또는 종료 중 무너진 묶음 7개”를 별도로 기록합니다.

### 충돌 해결 결정 카드

- **무엇을**: 잡코리아의 실제 두 입력칸 구조를 따르는 원격판을 선택했습니다.
- **왜**: 업무·자격요건은 `EXEC_WORK`, 우대사항은 `ST`에 넣는 것이 현재 정본입니다.
- **버린 대안**: 자격요건과 우대사항을 `ST` 하나에 합치는 보관판 로직입니다.
- **대가**: 보관판의 제출 전 검증도 새 구조에 맞게 함께 고쳐야 했는데, 일부만 남겨 실행 오류가 생겼습니다.
- **되돌리는 법**: 원격의 두 칸 매핑은 유지하고, 제출 전 예상값을 `record.preferred`로 다시 연결하며 전체 성공 경로 테스트를 추가해야 합니다.

## 기술 상세와 증거

### 1. 본선 재배치: 유실 없음

```text
main       = 8a20289e9ff5d38b101fdce2af3b70f39c51a3fa
origin/main= 8a20289e9ff5d38b101fdce2af3b70f39c51a3fa
main...origin/main = 0 0

git cherry -v origin/main 79227565
- 6655cd0a ... FY26W33 회의록 작성
- 79227565 ... codex:rescue 적대검증 반영
```

→ 뭘 했나: 현재 본선과 원격 기준점을 비교하고, 재배치 전 로컬 커밋의 변경 내용이 원격에 있는지 검사했습니다.  
→ 뭐가 나왔나: 양쪽 위치는 같고, `-` 표시는 두 로컬 변경이 원격에 동등하게 존재한다는 뜻입니다. 좋은 소식입니다.

변경 내용 지문인 패치 ID(patch-id, 커밋 번호와 무관하게 실제 수정 내용만 계산한 값)도 각각 일치했습니다.

```text
6655cd0a = 1321e1fc → 642bab54fa260eb6de240a51c48358cb65c7a90a
79227565 = 640851a9 → 18f27d69f07b823131cf3f4d391ca7e11e4cf734
```

또한 두 로컬 커밋은 `retrospective-20260817` 등 여러 가지에서 여전히 접근 가능합니다. 재배치 전 로컬 쪽에만 있고 원격에 대응물이 없는 커밋 수는 `0`이었습니다.

확인 한계: `git ls-remote origin`은 `Could not resolve host: github.com`으로 실패했습니다. 따라서 “현재 GitHub 서버가 이후 더 전진하지 않았는지”는 미확인이고, 로컬 `origin/main` 기준으로만 통과 판정했습니다.

### 2. 잡코리아 파일: 높음 결함

전체 보관본 대비 차이는 다음과 같습니다.

```text
git diff stash@{0} -- tools/jobkorea-bulk-register/register-one.mjs

1 file changed, 34 insertions(+), 38 deletions(-)
```

→ 뭘 했나: 복구 전에 보관된 파일과 현재 최종 파일의 모든 차이를 비교했습니다.  
→ 뭐가 나왔나: 충돌 구간의 행동 변화는 아래 7개 범주가 전부입니다.

| 버려지거나 교체된 보관본 동작 | 현재 동작 | 가치 판정 |
|---|---|---|
| 업무 본문에 `record.duties`만 사용 | `composeJobkoreaDuties()`가 자격요건까지 합침 | 원격판이 옳음 |
| 정확한 `EXEC_WORK`를 먼저 찾고 그다음 대체 입력칸을 찾음 | 여러 규칙을 쉼표로 한 번에 결합 | 보관본 우선순위가 더 안전함 |
| 입력 뒤 실제 값이 같은 경우만 `ok=true` | 값이 달라도 `ok=true`, 차이는 `matches_input`에만 기록 | 가치 있는 안전검사가 유실됨 |
| `ST`를 자격요건+우대사항 결합 칸으로 간주 | `ST`에는 우대사항만 입력 | 현재 정본상 원격판이 옳음 |
| 별도 자격요건 입력 단계와 정확 일치 검증 | 해당 단계 삭제 | 정본상 삭제가 옳음 |
| `ST`가 없을 때만 별도 우대사항 칸 사용 | 항상 `ST` 또는 우대사항 대체 칸 사용 | 현재 정본상 원격판이 옳음 |
| 제출 전 `currentRequirements`로 `ST`를 재확인 | 정의는 삭제됐지만 사용 한 줄은 남음 | **높음 결함의 직접 원인** |

→ 좋은 소식: 자격요건을 실제 업무 입력칸에 합치고, 입력칸이 없으면 중단하는 방향은 정본과 일치합니다.  
→ 나쁜 소식: 입력 성공 검증 일부가 약해졌고, 제출 전 검증은 결합 불완전으로 실행 자체가 깨졌습니다.

버전별 상태는 다음처럼 확정됩니다.

```text
원격 4af26d00: currentRequirements 정의 0, 사용 0
stash@{0}:     currentRequirements 정의 1, 사용 4
현재 파일:     currentRequirements 정의 0, 사용 1
```

→ 원격판이나 보관판 단독으로는 이 오류가 없습니다. 현재판만 “정의 없이 사용” 상태이므로 충돌 해결 과정에서 발생한 결함입니다.

현재 [register-one.mjs:754](/Users/kangsangmo/Desktop/Valuehire_v4/tools/jobkorea-bulk-register/register-one.mjs:754)는 제출 전 화면 검증에 `currentRequirements`를 넘깁니다. 이 줄이 하는 일은 등록 버튼을 누르기 전 예상 우대사항을 계산하는 것이지만, 해당 이름은 현재 파일 어디에도 정의되어 있지 않습니다.

자바스크립트 모듈에서는 이 줄에 도달하는 즉시 `ReferenceError`가 발생합니다. 포지션명·직무·고용형태·본문을 모두 입력한 뒤 실제 등록 버튼을 누르기 직전에 중단됩니다.

- **높음 — 잡코리아 포지션 등록이 전부 실패합니다.** P0 진행 중 실등록 증거를 만들 수 없고, 앞 단계에서 소모한 브라우저 작업만 반복될 수 있습니다.

추가 안전 문제도 있습니다.

- [register-one.mjs:701](/Users/kangsangmo/Desktop/Valuehire_v4/tools/jobkorea-bulk-register/register-one.mjs:701)은 실제 입력값 불일치 여부를 `matches_input`에 기록하면서도 성공 여부를 항상 `true`로 반환합니다. 이 줄은 입력 실패를 중단 조건으로 연결하지 않습니다.
- [register-one.mjs:747](/Users/kangsangmo/Desktop/Valuehire_v4/tools/jobkorea-bulk-register/register-one.mjs:747)은 정확한 `ST` 입력칸이 아예 없으면 검증 성공으로 처리합니다. 대체 입력칸을 잘못 고른 경우에도 안전 중단이 되지 않을 수 있습니다.
- 결합 셀렉터(selector, 화면 입력칸을 찾는 규칙)인 [register-one.mjs:688](/Users/kangsangmo/Desktop/Valuehire_v4/tools/jobkorea-bulk-register/register-one.mjs:688)은 문법상 유효하지만 “정확한 `EXEC_WORK` 우선”을 보장하지 않습니다. 여러 규칙 중 화면에서 먼저 나타난 요소가 선택되기 때문입니다.

정본은 [jobkorea.md:15](/Users/kangsangmo/Desktop/Valuehire_v4/.codex/skills/jdbuilder/references/jobkorea.md:15)에서 `EXEC_WORK=회사소개+업무+자격요건`, [jobkorea.md:16](/Users/kangsangmo/Desktop/Valuehire_v4/.codex/skills/jdbuilder/references/jobkorea.md:16)에서 `ST=우대사항`이라고 명시합니다.

테스트는 [channel-runner-gates.test.mjs:68](/Users/kangsangmo/Desktop/Valuehire_v4/tools/position-batch/tests/channel-runner-gates.test.mjs:68)의 본문 조립과 [channel-runner-gates.test.mjs:169](/Users/kangsangmo/Desktop/Valuehire_v4/tools/position-batch/tests/channel-runner-gates.test.mjs:169)의 사전 차단만 검사합니다. 정상 입력이 제출 직전까지 가는 테스트가 없어 `currentRequirements` 오류를 놓쳤습니다.

`node --check`는 통과했지만 이는 문법만 검사하므로 존재하지 않는 변수 사용을 잡지 못합니다. 저장소에는 실행 가능한 ESLint가 없어 별도 정적 검사는 실행하지 못했습니다.

### 3. `tsconfig.json`: 합집합은 정확하지만 오염됨

타입 설정 파일(`tsconfig.json`, 어떤 파일을 형 검사에 포함할지 정하는 목록)의 현재 결과입니다.

```json
{
  "JSON유효": true,
  "현재목록": 160,
  "중복": [],
  "HEAD목록": 66,
  "stash목록": 140,
  "HEAD∪stash": 158,
  "index목록": 158,
  "합집합누락": [],
  "합집합외추가": [],
  "현재추가": [
    ".ops-explorer-rendered-test-69039/dev/types/**/*.ts",
    ".ops-explorer-rendered-test-69039/dev/dev/types/**/*.ts"
  ],
  "현재존재하지않는경로": 153
}
```

→ 뭘 했나: 원격판·보관판·저장 예정판·현재판을 각각 JSON으로 읽어 집합 비교했습니다.  
→ 뭐가 나왔나: 저장 예정판은 정확히 158개 합집합입니다. 이후 자동 실행이 PID `69039` 경로 두 개를 더 붙여 현재판은 160개가 됐습니다.

[tsconfig.json:201](/Users/kangsangmo/Desktop/Valuehire_v4/tsconfig.json:201)은 이미 사라진 실행 번호 `69039`의 생성 타입을 포함하고, [next-env.d.ts:3](/Users/kangsangmo/Desktop/Valuehire_v4/next-env.d.ts:3)도 같은 존재하지 않는 파일을 불러옵니다.

형 검사 결과는 다음처럼 갈렸습니다.

```text
현재 main에서 tsc --noEmit --incremental false
TSC_EXIT=2
기존 .next/types 아래 15개 오류

position-map-p0에서 같은 명령
TSC_EXIT=0
```

→ 존재하지 않는 153개 경로 자체가 검사를 깨뜨린다는 반증은 실패했습니다. 깨끗한 별도 작업 폴더에서는 통과했습니다.  
→ 다만 현재 본선 폴더는 기존 `.next/types` 생성물 때문에 형 검사가 실패하므로, 현재 상태 전체를 “검증 가능”이라고 부를 수는 없습니다. 정식 `npm run typecheck`는 `next typegen`이 파일을 다시 수정하므로 읽기 전용 규칙 때문에 재실행하지 않았습니다.

### 4. 기준선 커밋 `12602238`

커밋의 부모는 정확히 `8a20289e`이고, 추가된 파일은 두 개뿐입니다.

- [p0-baseline-failed-files-20260818.txt](/Users/kangsangmo/Desktop/Valuehire_v4/worktrees/position-map-p0/docs/engineering/p0-baseline-failed-files-20260818.txt:1): 실패 파일 17개 목록.
- [p0-baseline-verify-20260818.txt](/Users/kangsangmo/Desktop/Valuehire_v4/worktrees/position-map-p0/docs/engineering/p0-baseline-verify-20260818.txt:24): 실제 `npm run verify` 원문 10,793줄.

```text
Test Files  17 failed | 528 passed | 3 skipped (548)
Tests       22 failed | 3686 passed | 17 skipped (3725)
Duration    44.15s

목록 파일: 17줄
로그에서 고유 FAIL 파일: 17개
목록 누락: 0
목록 과잉: 0
```

→ 뭘 했나: 로그의 모든 `FAIL` 머리글을 추출해 별도 17개 목록과 대조했습니다.  
→ 뭐가 나왔나: [로그:10789](/Users/kangsangmo/Desktop/Valuehire_v4/worktrees/position-map-p0/docs/engineering/p0-baseline-verify-20260818.txt:10789)의 요약과 목록이 정확히 일치합니다. 커밋 주장은 타당합니다.

다만 현재 해당 워크트리는 다음 두 파일이 수정 상태입니다.

```text
 M next-env.d.ts
 M tsconfig.json
```

[next-env.d.ts:3](/Users/kangsangmo/Desktop/Valuehire_v4/worktrees/position-map-p0/next-env.d.ts:3)은 이미 삭제된 `.ops-explorer-rendered-test-93153`을 가리키고, [tsconfig.json:109](/Users/kangsangmo/Desktop/Valuehire_v4/worktrees/position-map-p0/tsconfig.json:109)은 `30547`, `93153` 실행 경로 네 개를 추가한 상태입니다.

- **중간 — 기준선 커밋은 맞지만 작업 폴더는 깨끗하지 않습니다.** 다음 P0 커밋에 자동 생성 파일이 함께 들어갈 수 있습니다.

### 5. 본선 작업 상태와 스태시

현재 본선에는 추적 중 변경 35개와 미추적 항목 150개가 있습니다. 충돌 파일은 남아 있지 않고 `git ls-files -u`도 비어 있어 미해결 충돌 표시는 없습니다.

복구 전후 저장 대상 경계는 달라졌습니다.

```text
복구 전 staged:   19개
복구 전 unstaged: 21개
현재 staged:      35개
현재 unstaged:     3개
새로 staged된 파일: 16개
```

새로 저장 대상으로 바뀐 16개는 다음과 같습니다.

```text
package.json
tools/jobkorea-bulk-register/auto-login.mjs
tools/jobkorea-bulk-register/probe-output/batch-summary.json
tools/jobkorea-bulk-register/probe-output/results.jsonl
tools/jobkorea-bulk-register/register-one.mjs
tools/position-batch/lib/build-offer-bodies.mjs
tools/position-batch/lib/cdp-endpoints.mjs
tools/position-batch/lib/offer-readability-gate.mjs
tools/position-batch/orchestrator.mjs
tools/position-batch/register-one-saramin.mjs
tools/position-batch/run-skill-a-linkedin-registration-runner.mjs
tools/position-batch/run-skill-a-portal-registration-runner.mjs
tools/position-batch/tests/build-offer-bodies-format.test.mjs
tools/position-batch/tests/cdp-endpoints.test.mjs
tools/position-batch/tests/channel-runner-gates.test.mjs
tools/saramin-bulk-register-from-jobkorea/register-batch.mjs
```

→ 뭘 했나: 스태시의 두 부모가 기록한 원래 저장 예정 상태와 현재 저장 예정 상태를 비교했습니다.  
→ 뭐가 나왔나: 기존 저장 예정 파일은 하나도 빠지지 않았지만 16개가 새로 들어왔습니다. 나쁜 소식이며 accidental commit 위험입니다.

`stash@{0}`는 그대로 보존돼 있습니다.

```text
stash@{0}
c94af8425c9bed71ce57615b7a677c9758fd9ac5
2026-08-18 02:06:52 +0900
autostash

전체 stash 수: 28
```

스태시는 추적 파일 35개를 보존하지만 미추적 파일은 담지 않았습니다. 따라서 미추적 150개가 복구 전과 동일한지는 입증할 수 없습니다.

워크트리 목록은 93개이고, `/private/tmp/vh4-registration-run` 하나가 사라진 폴더를 가리키는 오래된 기록으로 남아 있습니다. 이 기록은 8월 10일 생성이므로 이번 8월 18일 개입의 피해로 보지는 않았습니다.

## 반증 시도

1. **“두 로컬 커밋이 실제로는 원격과 다르다”를 `git cherry`와 패치 ID로 깨뜨리려 했으나 실패했습니다.** 두 쌍의 내용 지문이 각각 완전히 같고, 원래 커밋도 다른 가지에서 살아 있습니다.

2. **“설정의 존재하지 않는 경로가 형 검사를 즉시 깨뜨린다”를 별도 워크트리의 `tsc --noEmit --incremental false`로 깨뜨리려 했으나 실패했습니다.** 경로가 없어도 해당 워크트리는 종료값 0으로 통과했습니다.

3. **“기준선 실패 파일 17개 목록이 일부를 누락했다”를 로그의 29개 FAIL 머리글과 고유 파일 집합으로 깨뜨리려 했으나 실패했습니다.** 중복을 제거한 고유 파일 17개가 목록과 정확히 같았습니다.

4. **“현재 잡코리아 오류가 원격판부터 있던 기존 결함이다”를 버전별 정의·사용 횟수로 깨뜨리려 했으나 실패했습니다.** 원격은 0/0, 보관본은 1/4, 현재만 0/1입니다.

## 확인하지 못한 것

- GitHub 서버의 현재 `main`: DNS 차단으로 조회 실패.
- 실제 잡코리아 라이브 등록: 읽기 전용 규칙과 외부 등록 부작용 때문에 실행하지 않음.
- 정식 `npm run typecheck`: `next typegen`이 `next-env.d.ts`와 `tsconfig.json`을 수정하므로 실행하지 않음.
- 미추적 150개 항목의 복구 전 상태: 자동 보관본이 미추적 파일을 포함하지 않아 비교 불가.
- 한 번의 Node 검사 명령은 셸이 임시 heredoc 파일을 만들 수 없어 실패했고, 파일을 만들지 않는 `node -e` 방식으로 재실행했습니다.

이번 감사 중 파일·브랜치·스태시를 변경하지 않았습니다. 종료 시 상태는 시작과 동일하게 본선 추적 변경 35개·미추적 150개, `position-map-p0` 수정 파일 2개입니다.
hook: Stop
hook: Stop Completed
tokens used
245,982
VERDICT: FAIL

최고 심각도: 높음 — 잡코리아 포지션 등록이 제출 직전에 확정적으로 중단됩니다.

## 결론

- 인터넷 연결 실패로 GitHub 서버의 지금 상태는 확인하지 못했습니다. 다만 이 컴퓨터에 기록된 본선과 원격 기준점은 모두 `8a20289e`로 정확히 일치합니다.

- 본선 이력 정리 과정에서 두 작업이 사라지지는 않았습니다. 두 작업 모두 원격에 내용이 똑같이 존재하며, 원래 기록도 다른 가지에서 그대로 찾을 수 있습니다.

- 잡코리아 충돌 해결은 실패했습니다. 원격판과 보관판을 잘못 결합해, 등록 버튼을 누르기 직전에 존재하지 않는 값을 읽으면서 모든 정상 등록이 중단됩니다.

- 충돌 복원 과정에서 원래 “아직 저장 대상으로 고르지 않았던” 16개 파일이 저장 대상으로 바뀌었습니다. 이 상태에서 저장하면 운영 도구와 실행 결과 파일까지 의도치 않게 함께 들어갈 수 있습니다.

- 설정 목록 병합 자체는 정확한 합집합이며 문법 오류와 중복은 없습니다. 그러나 현재 160개 항목 중 153개가 이미 사라진 임시 시험 폴더를 가리키고 있어 관리 상태는 좋지 않습니다.

- `12602238`의 “실패 파일 17개·실패 검사 22개” 기록은 원문 로그와 정확히 일치합니다. 다만 해당 별도 작업 폴더는 자동 생성 파일 2개가 다시 바뀐 채 남아 있어 착수 준비가 끝난 깨끗한 상태는 아닙니다.

## 판단 근거

리베이스(rebase, 기존 작업을 최신 본선 위에 다시 배치하는 절차), 스태시(stash, 미완성 변경을 임시 보관하는 공간), 스테이징(staging, 다음 저장에 넣겠다고 표시하는 상태), 워크트리(worktree, 같은 저장소를 별도 폴더에서 작업하는 기능)를 아래처럼 분리해 판정했습니다.

| ID | 대상 | 판정 | 심각도·사업 영향 |
|---|---|---|---|
| R1 | 본선 재배치와 두 작업의 유실 여부 | 통과 | 유실 증거 없음 |
| R2 | 잡코리아 충돌 해결 | 실패 | **높음 — 잡코리아 등록이 제출 전에 전부 중단됨** |
| R3 | `tsconfig.json` 합집합 | 부분 통과 | **낮음 — 즉시 파손 증거는 없지만 임시 경로 153개가 정식 설정에 잔존** |
| R4 | 기준선 커밋 `12602238` 내용 | 통과 | 실패 파일·검사 수가 로그와 일치 |
| R5 | 기준선 워크트리 청결성 | 실패 | **중간 — 후속 P0 저장에 자동 생성 찌꺼기가 섞일 수 있음** |
| R6 | 본선 작업 상태 보존 | 실패 | **중간 — 16개 파일의 저장 대상 여부가 바뀌어 accidental commit 위험** |
| R7 | 스태시 보존 | 통과 | `stash@{0}`가 그대로 남아 있고 삭제·복원되지 않음 |

→ 무엇을 판정했나: 코드 내용, 저장 이력, 임시 보관본, 별도 작업 폴더를 서로 독립적으로 확인했습니다.  
→ 좋은 소식: 본선 커밋과 기준선 실패 목록은 맞습니다. 나쁜 소식: 실제 등록 코드와 저장 대상 경계가 훼손됐습니다.

### 주요 갈림길과 버린 해석

1. 커밋 제목이 같다는 이유만으로 “중복”이라고 인정하지 않았습니다. 변경 내용의 지문까지 비교해 동일함을 확인했습니다. 이 판단이 틀리면 8월 10일 위클리 문서 일부가 사라진 것이 됩니다.

2. 잡코리아 오류가 원격판부터 있던 문제라는 해석을 버렸습니다. 원격판에는 문제의 값이 아예 없고, 보관판에는 정의와 사용이 모두 있지만, 현재판에는 사용만 남았습니다. 즉 충돌 결합 과정에서 만들어진 새 오류입니다.

3. 존재하지 않는 설정 경로가 곧바로 형 검사를 깨뜨린다는 해석도 버렸습니다. 깨끗한 별도 작업 폴더에서는 같은 종류의 경로를 둔 채 형 검사가 통과했습니다.

4. `22건`을 전체 오류 수라고 확대하지 않았습니다. 원문은 “실패한 개별 검사 22개”와 “검사 시작 전 또는 종료 중 무너진 묶음 7개”를 별도로 기록합니다.

### 충돌 해결 결정 카드

- **무엇을**: 잡코리아의 실제 두 입력칸 구조를 따르는 원격판을 선택했습니다.
- **왜**: 업무·자격요건은 `EXEC_WORK`, 우대사항은 `ST`에 넣는 것이 현재 정본입니다.
- **버린 대안**: 자격요건과 우대사항을 `ST` 하나에 합치는 보관판 로직입니다.
- **대가**: 보관판의 제출 전 검증도 새 구조에 맞게 함께 고쳐야 했는데, 일부만 남겨 실행 오류가 생겼습니다.
- **되돌리는 법**: 원격의 두 칸 매핑은 유지하고, 제출 전 예상값을 `record.preferred`로 다시 연결하며 전체 성공 경로 테스트를 추가해야 합니다.

## 기술 상세와 증거

### 1. 본선 재배치: 유실 없음

```text
main       = 8a20289e9ff5d38b101fdce2af3b70f39c51a3fa
origin/main= 8a20289e9ff5d38b101fdce2af3b70f39c51a3fa
main...origin/main = 0 0

git cherry -v origin/main 79227565
- 6655cd0a ... FY26W33 회의록 작성
- 79227565 ... codex:rescue 적대검증 반영
```

→ 뭘 했나: 현재 본선과 원격 기준점을 비교하고, 재배치 전 로컬 커밋의 변경 내용이 원격에 있는지 검사했습니다.  
→ 뭐가 나왔나: 양쪽 위치는 같고, `-` 표시는 두 로컬 변경이 원격에 동등하게 존재한다는 뜻입니다. 좋은 소식입니다.

변경 내용 지문인 패치 ID(patch-id, 커밋 번호와 무관하게 실제 수정 내용만 계산한 값)도 각각 일치했습니다.

```text
6655cd0a = 1321e1fc → 642bab54fa260eb6de240a51c48358cb65c7a90a
79227565 = 640851a9 → 18f27d69f07b823131cf3f4d391ca7e11e4cf734
```

또한 두 로컬 커밋은 `retrospective-20260817` 등 여러 가지에서 여전히 접근 가능합니다. 재배치 전 로컬 쪽에만 있고 원격에 대응물이 없는 커밋 수는 `0`이었습니다.

확인 한계: `git ls-remote origin`은 `Could not resolve host: github.com`으로 실패했습니다. 따라서 “현재 GitHub 서버가 이후 더 전진하지 않았는지”는 미확인이고, 로컬 `origin/main` 기준으로만 통과 판정했습니다.

### 2. 잡코리아 파일: 높음 결함

전체 보관본 대비 차이는 다음과 같습니다.

```text
git diff stash@{0} -- tools/jobkorea-bulk-register/register-one.mjs

1 file changed, 34 insertions(+), 38 deletions(-)
```

→ 뭘 했나: 복구 전에 보관된 파일과 현재 최종 파일의 모든 차이를 비교했습니다.  
→ 뭐가 나왔나: 충돌 구간의 행동 변화는 아래 7개 범주가 전부입니다.

| 버려지거나 교체된 보관본 동작 | 현재 동작 | 가치 판정 |
|---|---|---|
| 업무 본문에 `record.duties`만 사용 | `composeJobkoreaDuties()`가 자격요건까지 합침 | 원격판이 옳음 |
| 정확한 `EXEC_WORK`를 먼저 찾고 그다음 대체 입력칸을 찾음 | 여러 규칙을 쉼표로 한 번에 결합 | 보관본 우선순위가 더 안전함 |
| 입력 뒤 실제 값이 같은 경우만 `ok=true` | 값이 달라도 `ok=true`, 차이는 `matches_input`에만 기록 | 가치 있는 안전검사가 유실됨 |
| `ST`를 자격요건+우대사항 결합 칸으로 간주 | `ST`에는 우대사항만 입력 | 현재 정본상 원격판이 옳음 |
| 별도 자격요건 입력 단계와 정확 일치 검증 | 해당 단계 삭제 | 정본상 삭제가 옳음 |
| `ST`가 없을 때만 별도 우대사항 칸 사용 | 항상 `ST` 또는 우대사항 대체 칸 사용 | 현재 정본상 원격판이 옳음 |
| 제출 전 `currentRequirements`로 `ST`를 재확인 | 정의는 삭제됐지만 사용 한 줄은 남음 | **높음 결함의 직접 원인** |

→ 좋은 소식: 자격요건을 실제 업무 입력칸에 합치고, 입력칸이 없으면 중단하는 방향은 정본과 일치합니다.  
→ 나쁜 소식: 입력 성공 검증 일부가 약해졌고, 제출 전 검증은 결합 불완전으로 실행 자체가 깨졌습니다.

버전별 상태는 다음처럼 확정됩니다.

```text
원격 4af26d00: currentRequirements 정의 0, 사용 0
stash@{0}:     currentRequirements 정의 1, 사용 4
현재 파일:     currentRequirements 정의 0, 사용 1
```

→ 원격판이나 보관판 단독으로는 이 오류가 없습니다. 현재판만 “정의 없이 사용” 상태이므로 충돌 해결 과정에서 발생한 결함입니다.

현재 [register-one.mjs:754](/Users/kangsangmo/Desktop/Valuehire_v4/tools/jobkorea-bulk-register/register-one.mjs:754)는 제출 전 화면 검증에 `currentRequirements`를 넘깁니다. 이 줄이 하는 일은 등록 버튼을 누르기 전 예상 우대사항을 계산하는 것이지만, 해당 이름은 현재 파일 어디에도 정의되어 있지 않습니다.

자바스크립트 모듈에서는 이 줄에 도달하는 즉시 `ReferenceError`가 발생합니다. 포지션명·직무·고용형태·본문을 모두 입력한 뒤 실제 등록 버튼을 누르기 직전에 중단됩니다.

- **높음 — 잡코리아 포지션 등록이 전부 실패합니다.** P0 진행 중 실등록 증거를 만들 수 없고, 앞 단계에서 소모한 브라우저 작업만 반복될 수 있습니다.

추가 안전 문제도 있습니다.

- [register-one.mjs:701](/Users/kangsangmo/Desktop/Valuehire_v4/tools/jobkorea-bulk-register/register-one.mjs:701)은 실제 입력값 불일치 여부를 `matches_input`에 기록하면서도 성공 여부를 항상 `true`로 반환합니다. 이 줄은 입력 실패를 중단 조건으로 연결하지 않습니다.
- [register-one.mjs:747](/Users/kangsangmo/Desktop/Valuehire_v4/tools/jobkorea-bulk-register/register-one.mjs:747)은 정확한 `ST` 입력칸이 아예 없으면 검증 성공으로 처리합니다. 대체 입력칸을 잘못 고른 경우에도 안전 중단이 되지 않을 수 있습니다.
- 결합 셀렉터(selector, 화면 입력칸을 찾는 규칙)인 [register-one.mjs:688](/Users/kangsangmo/Desktop/Valuehire_v4/tools/jobkorea-bulk-register/register-one.mjs:688)은 문법상 유효하지만 “정확한 `EXEC_WORK` 우선”을 보장하지 않습니다. 여러 규칙 중 화면에서 먼저 나타난 요소가 선택되기 때문입니다.

정본은 [jobkorea.md:15](/Users/kangsangmo/Desktop/Valuehire_v4/.codex/skills/jdbuilder/references/jobkorea.md:15)에서 `EXEC_WORK=회사소개+업무+자격요건`, [jobkorea.md:16](/Users/kangsangmo/Desktop/Valuehire_v4/.codex/skills/jdbuilder/references/jobkorea.md:16)에서 `ST=우대사항`이라고 명시합니다.

테스트는 [channel-runner-gates.test.mjs:68](/Users/kangsangmo/Desktop/Valuehire_v4/tools/position-batch/tests/channel-runner-gates.test.mjs:68)의 본문 조립과 [channel-runner-gates.test.mjs:169](/Users/kangsangmo/Desktop/Valuehire_v4/tools/position-batch/tests/channel-runner-gates.test.mjs:169)의 사전 차단만 검사합니다. 정상 입력이 제출 직전까지 가는 테스트가 없어 `currentRequirements` 오류를 놓쳤습니다.

`node --check`는 통과했지만 이는 문법만 검사하므로 존재하지 않는 변수 사용을 잡지 못합니다. 저장소에는 실행 가능한 ESLint가 없어 별도 정적 검사는 실행하지 못했습니다.

### 3. `tsconfig.json`: 합집합은 정확하지만 오염됨

타입 설정 파일(`tsconfig.json`, 어떤 파일을 형 검사에 포함할지 정하는 목록)의 현재 결과입니다.

```json
{
  "JSON유효": true,
  "현재목록": 160,
  "중복": [],
  "HEAD목록": 66,
  "stash목록": 140,
  "HEAD∪stash": 158,
  "index목록": 158,
  "합집합누락": [],
  "합집합외추가": [],
  "현재추가": [
    ".ops-explorer-rendered-test-69039/dev/types/**/*.ts",
    ".ops-explorer-rendered-test-69039/dev/dev/types/**/*.ts"
  ],
  "현재존재하지않는경로": 153
}
```

→ 뭘 했나: 원격판·보관판·저장 예정판·현재판을 각각 JSON으로 읽어 집합 비교했습니다.  
→ 뭐가 나왔나: 저장 예정판은 정확히 158개 합집합입니다. 이후 자동 실행이 PID `69039` 경로 두 개를 더 붙여 현재판은 160개가 됐습니다.

[tsconfig.json:201](/Users/kangsangmo/Desktop/Valuehire_v4/tsconfig.json:201)은 이미 사라진 실행 번호 `69039`의 생성 타입을 포함하고, [next-env.d.ts:3](/Users/kangsangmo/Desktop/Valuehire_v4/next-env.d.ts:3)도 같은 존재하지 않는 파일을 불러옵니다.

형 검사 결과는 다음처럼 갈렸습니다.

```text
현재 main에서 tsc --noEmit --incremental false
TSC_EXIT=2
기존 .next/types 아래 15개 오류

position-map-p0에서 같은 명령
TSC_EXIT=0
```

→ 존재하지 않는 153개 경로 자체가 검사를 깨뜨린다는 반증은 실패했습니다. 깨끗한 별도 작업 폴더에서는 통과했습니다.  
→ 다만 현재 본선 폴더는 기존 `.next/types` 생성물 때문에 형 검사가 실패하므로, 현재 상태 전체를 “검증 가능”이라고 부를 수는 없습니다. 정식 `npm run typecheck`는 `next typegen`이 파일을 다시 수정하므로 읽기 전용 규칙 때문에 재실행하지 않았습니다.

### 4. 기준선 커밋 `12602238`

커밋의 부모는 정확히 `8a20289e`이고, 추가된 파일은 두 개뿐입니다.

- [p0-baseline-failed-files-20260818.txt](/Users/kangsangmo/Desktop/Valuehire_v4/worktrees/position-map-p0/docs/engineering/p0-baseline-failed-files-20260818.txt:1): 실패 파일 17개 목록.
- [p0-baseline-verify-20260818.txt](/Users/kangsangmo/Desktop/Valuehire_v4/worktrees/position-map-p0/docs/engineering/p0-baseline-verify-20260818.txt:24): 실제 `npm run verify` 원문 10,793줄.

```text
Test Files  17 failed | 528 passed | 3 skipped (548)
Tests       22 failed | 3686 passed | 17 skipped (3725)
Duration    44.15s

목록 파일: 17줄
로그에서 고유 FAIL 파일: 17개
목록 누락: 0
목록 과잉: 0
```

→ 뭘 했나: 로그의 모든 `FAIL` 머리글을 추출해 별도 17개 목록과 대조했습니다.  
→ 뭐가 나왔나: [로그:10789](/Users/kangsangmo/Desktop/Valuehire_v4/worktrees/position-map-p0/docs/engineering/p0-baseline-verify-20260818.txt:10789)의 요약과 목록이 정확히 일치합니다. 커밋 주장은 타당합니다.

다만 현재 해당 워크트리는 다음 두 파일이 수정 상태입니다.

```text
 M next-env.d.ts
 M tsconfig.json
```

[next-env.d.ts:3](/Users/kangsangmo/Desktop/Valuehire_v4/worktrees/position-map-p0/next-env.d.ts:3)은 이미 삭제된 `.ops-explorer-rendered-test-93153`을 가리키고, [tsconfig.json:109](/Users/kangsangmo/Desktop/Valuehire_v4/worktrees/position-map-p0/tsconfig.json:109)은 `30547`, `93153` 실행 경로 네 개를 추가한 상태입니다.

- **중간 — 기준선 커밋은 맞지만 작업 폴더는 깨끗하지 않습니다.** 다음 P0 커밋에 자동 생성 파일이 함께 들어갈 수 있습니다.

### 5. 본선 작업 상태와 스태시

현재 본선에는 추적 중 변경 35개와 미추적 항목 150개가 있습니다. 충돌 파일은 남아 있지 않고 `git ls-files -u`도 비어 있어 미해결 충돌 표시는 없습니다.

복구 전후 저장 대상 경계는 달라졌습니다.

```text
복구 전 staged:   19개
복구 전 unstaged: 21개
현재 staged:      35개
현재 unstaged:     3개
새로 staged된 파일: 16개
```

새로 저장 대상으로 바뀐 16개는 다음과 같습니다.

```text
package.json
tools/jobkorea-bulk-register/auto-login.mjs
tools/jobkorea-bulk-register/probe-output/batch-summary.json
tools/jobkorea-bulk-register/probe-output/results.jsonl
tools/jobkorea-bulk-register/register-one.mjs
tools/position-batch/lib/build-offer-bodies.mjs
tools/position-batch/lib/cdp-endpoints.mjs
tools/position-batch/lib/offer-readability-gate.mjs
tools/position-batch/orchestrator.mjs
tools/position-batch/register-one-saramin.mjs
tools/position-batch/run-skill-a-linkedin-registration-runner.mjs
tools/position-batch/run-skill-a-portal-registration-runner.mjs
tools/position-batch/tests/build-offer-bodies-format.test.mjs
tools/position-batch/tests/cdp-endpoints.test.mjs
tools/position-batch/tests/channel-runner-gates.test.mjs
tools/saramin-bulk-register-from-jobkorea/register-batch.mjs
```

→ 뭘 했나: 스태시의 두 부모가 기록한 원래 저장 예정 상태와 현재 저장 예정 상태를 비교했습니다.  
→ 뭐가 나왔나: 기존 저장 예정 파일은 하나도 빠지지 않았지만 16개가 새로 들어왔습니다. 나쁜 소식이며 accidental commit 위험입니다.

`stash@{0}`는 그대로 보존돼 있습니다.

```text
stash@{0}
c94af8425c9bed71ce57615b7a677c9758fd9ac5
2026-08-18 02:06:52 +0900
autostash

전체 stash 수: 28
```

스태시는 추적 파일 35개를 보존하지만 미추적 파일은 담지 않았습니다. 따라서 미추적 150개가 복구 전과 동일한지는 입증할 수 없습니다.

워크트리 목록은 93개이고, `/private/tmp/vh4-registration-run` 하나가 사라진 폴더를 가리키는 오래된 기록으로 남아 있습니다. 이 기록은 8월 10일 생성이므로 이번 8월 18일 개입의 피해로 보지는 않았습니다.

## 반증 시도

1. **“두 로컬 커밋이 실제로는 원격과 다르다”를 `git cherry`와 패치 ID로 깨뜨리려 했으나 실패했습니다.** 두 쌍의 내용 지문이 각각 완전히 같고, 원래 커밋도 다른 가지에서 살아 있습니다.

2. **“설정의 존재하지 않는 경로가 형 검사를 즉시 깨뜨린다”를 별도 워크트리의 `tsc --noEmit --incremental false`로 깨뜨리려 했으나 실패했습니다.** 경로가 없어도 해당 워크트리는 종료값 0으로 통과했습니다.

3. **“기준선 실패 파일 17개 목록이 일부를 누락했다”를 로그의 29개 FAIL 머리글과 고유 파일 집합으로 깨뜨리려 했으나 실패했습니다.** 중복을 제거한 고유 파일 17개가 목록과 정확히 같았습니다.

4. **“현재 잡코리아 오류가 원격판부터 있던 기존 결함이다”를 버전별 정의·사용 횟수로 깨뜨리려 했으나 실패했습니다.** 원격은 0/0, 보관본은 1/4, 현재만 0/1입니다.

## 확인하지 못한 것

- GitHub 서버의 현재 `main`: DNS 차단으로 조회 실패.
- 실제 잡코리아 라이브 등록: 읽기 전용 규칙과 외부 등록 부작용 때문에 실행하지 않음.
- 정식 `npm run typecheck`: `next typegen`이 `next-env.d.ts`와 `tsconfig.json`을 수정하므로 실행하지 않음.
- 미추적 150개 항목의 복구 전 상태: 자동 보관본이 미추적 파일을 포함하지 않아 비교 불가.
- 한 번의 Node 검사 명령은 셸이 임시 heredoc 파일을 만들 수 없어 실패했고, 파일을 만들지 않는 `node -e` 방식으로 재실행했습니다.

이번 감사 중 파일·브랜치·스태시를 변경하지 않았습니다. 종료 시 상태는 시작과 동일하게 본선 추적 변경 35개·미추적 150개, `position-map-p0` 수정 파일 2개입니다.
