# Admin Weekly Dashboard v6 Phase 0 계획 검사기 — `\Z` 정규식 거짓 실패 수정 goal — 2026-08-19

## 사장님 브리핑 (결론 + 판단 근거)

**결론**: `admin-phase0-plan-structural-contract.mjs` 파일 218번째 줄에 있는 `\Z`라는 표시는 자바스크립트에서는 "문서 끝까지"라는 뜻이 아니라 그냥 알파벳 "Z" 한 글자로 읽힙니다. 그래서 지금 이 검사기가 참조하는 정본 문서(`docs/sot/verification-commands.md`)의 "CI가 실제로 돌리는 것" 표 구간에 나중에 누군가 대문자 Z가 들어간 정상적인 문장을 추가하면, 그 순간부터 이 검사기가 표 안의 실제 행 개수를 잘못 세게 됩니다. 지금 당장 이 표 구간에는 대문자 Z가 없어서 아직 사고가 난 적은 없지만, 미래에 정상적인 문서 수정이 이 검사기 때문에 잘못 막힐 수 있는 잠재 결함입니다.

**판단 근거**: 이 결함은 사장님이 2026-08-18에 전달해 주신 판정문(R9)과 제가 코드를 직접 읽어 확인한 결과, 그리고 방금 Codex가 독립적으로 코드를 실행해 재현한 결과까지 세 번 교차 확인됐습니다. 고치는 방법도 이미 확정돼 있습니다 — 자바스크립트에서 진짜로 "문자열 끝"을 뜻하는 `(?![\s\S])`로 바꾸면 됩니다. 다른 방법(예: 정규식 전체를 다시 설계)은 검토하지 않았습니다 — 이미 원인·해법이 명확한 한 줄 수정이라 과잉 설계가 됩니다.

**대가**: 이 정규식이 다른 곳에서도 쓰이지는 않는지 확인이 필요합니다(검토 결과 이 함수 안에서만 1곳 사용 — 아래 3층 증거 참고). 회귀 검사를 추가하려면 기존 뮤테이션(고장 시험) 프레임워크가 "정상 변형이 거짓으로 실패하지 않는지"를 확인하는 용도로는 아직 없어서, 이 케이스만을 위한 별도 확인 함수를 추가해야 합니다.

## ① 현재 상태 (증거)

- `scripts/verify/admin-phase0-plan-structural-contract.mjs:218` — `const section = text.match(/^### CI\([^\n]*\)[^\n]*\n([\s\S]*?)(?=^### |^## |\Z)/m)?.[1] ?? "";`
- 이 함수(`parseSotCiRowCount`)는 파일 556번째 줄 한 곳에서만 호출됩니다.
- `docs/sot/verification-commands.md`의 `### CI(...)` 구간을 `awk`로 잘라 대문자 Z 개수를 세어보니 현재 0건입니다 — 지금은 잠재 결함이며 실제 오탐은 아직 없습니다.

## ② 근본 원인

자바스크립트 정규식 엔진에는 Perl/Python류에 있는 `\Z`(문자열 끝, 마지막 개행 앞) 문법이 없습니다. 자바스크립트는 이를 리터럴 문자 "Z"로 해석합니다. 작성자가 다른 언어의 정규식 습관을 그대로 가져와 쓴 것으로 보입니다.

## ③ 인수 기준(AC)

**AC-1**: When `docs/sot/verification-commands.md`의 `### CI(...)` 구간에 정상적인 문장 중 대문자 Z가 포함되면, Then `parseSotCiRowCount`는 그 Z를 구간의 끝으로 오인하지 않고 실제 표 행 개수를 정확히 세어야 한다.
- 검증 명령: `node scripts/verify/check-admin-phase0-plan.mjs --self-test`(회귀 케이스 통과) + 새 회귀 테스트 단독 실행
- counter-AC: Z가 포함된 순간 구간을 잘라내 표 행 개수를 실제보다 적게(또는 0으로) 세면 가짜 통과다.

**AC-2**: When 32개 기존 고장 시험(mutation)을 그대로 실행하면, Then 전부 그대로 지정된 오류 문구로 실패해야 한다(이번 수정이 기존 검출 능력을 약화시키지 않았음을 증명).
- 검증 명령: `node scripts/verify/check-admin-phase0-plan.mjs --self-test`
- counter-AC: mutationsCaught이 32 미만으로 떨어지면 이번 수정이 기존 방어를 깬 것이다.

## ④ Harness 게이트 계획

이미 이 작업 전용 워크트리(`worktrees/admin-weekly-dashboard-v6-phase0-plan-checker-hardening-a1`, 브랜치 `task/admin-weekly-dashboard-v6-phase0-plan-checker-hardening-a1`)가 있고 PR #28이 열려 있으므로 새 워크트리를 파지 않고 이 브랜치에 이어서 커밋합니다. RED(회귀 테스트가 수정 전에는 실패)를 먼저 커밋하고, 그다음 GREEN(정규식 수정)을 별도 커밋으로 남깁니다.

## ⑤ codex 적대검증 항목

- `(?![\s\S])`로 바꾼 뒤에도 원래 `\Z`가 의도했던 "문서 끝 또는 다음 `###`/`##` 헤딩 앞"이라는 원래 의미를 그대로 보존하는지
- 32개 기존 mutation이 전부 그대로 잡히는지
- 새 회귀 테스트가 진짜로 수정 전 코드에서는 실패하는지(RED가 올바른 이유로 빨간지)

## ⑥ SOT 체크리스트

`docs/sot/verification-commands.md`를 읽었습니다. 이 수정은 검사기 내부 버그 수정이며 SOT가 기술하는 게이트·명령 자체는 바뀌지 않으므로 SOT diff는 필요 없습니다.

## ⑦ 비범위

관리자 제품 코드, P0-01 이후 micro, `package.json`/`.node-version`/`pnpm-workspace.yaml`, 과거 감사 문서 수정, main 변경, merge·deploy는 이번 범위가 아닙니다.

## ⑩ 계약 스펙

- 입력: `docs/sot/verification-commands.md`의 텍스트 문자열 (CI 구간 포함)
- 출력: 그 구간 안의 표 행 개수(정수)
- 변경 전: 구간 안에 대문자 Z가 있으면 그 앞에서 잘림 → 행 개수 과소 집계
- 변경 후: 구간 끝은 오직 다음 `###`/`##` 헤딩 또는 실제 문자열 끝에서만 결정 → Z 유무와 무관하게 정확한 행 개수
