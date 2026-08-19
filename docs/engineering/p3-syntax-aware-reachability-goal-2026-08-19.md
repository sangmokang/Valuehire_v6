# P3 문법 판정·서버 도달성 보강 — goal (2026-08-19)

## 결론

현재 보호 검사는 실제 프로그램 구조가 아니라 줄마다 글자 모양만 찾아서, 여러 줄로 쓴 위반을 놓치고 설명문·주석·문자열을 잘못 막는다. 서버에서도 앞선 총괄 검사가 의도대로 실패하면 이 보호 검사는 실행되지 않는다.

이번 작업은 이미 확인된 두 구멍만 닫는다. 실제 프로그램 구조를 읽어 위반과 무해한 글을 구분하고, 앞선 검사의 성적과 관계없이 서버가 이 보호 검사를 실행하게 만든다. 다른 31개 원칙과 모든 예외 처리 결과의 데이터베이스 기록은 건드리지 않는다.

## 판단 근거

이전 작업은 같은 변경 안에서 검사기 자체를 약하게 만드는 공격을 막았지만, 검사 방식 자체는 줄 단위 문자열 검색으로 남았다. `scripts/acceptance-silent-failure-lint.sh:44-73`은 Python과 JavaScript 계열 파일을 `grep`으로 직접 읽고, 같은 파일 `16-17`은 문자열·주석 오탐과 여러 줄 누락을 한계로 인정한다.

서버 설정은 `.github/workflows/verify.yml:34-40`에서 32개 원칙 총괄 검사를 먼저 실행하고 P3 검사를 그 뒤에 둔다. 현재 총괄 검사는 미충족 원칙 31개 때문에 의도적으로 불합격이므로, 기본 순차 실행에서는 P3 단계가 시작되지 않는다. 이는 “로컬 훅은 우회 가능하므로 서버가 같은 검사를 맡는다”는 `docs/sot/coding-principles.md` P15의 취지와 맞지 않는다.

틀리면 두 종류의 문제가 남는다. 실제 위반을 여러 줄로 나눠 숨길 수 있고, 반대로 설명문에 금지 기호를 적었다는 이유만으로 정상 변경이 막힌다. 서버 검사가 실행되지 않으면 로컬 검사를 건너뛴 변경을 원격에서 다시 판정하지 못한다.

## 결정 카드

**무엇을** — Python은 표준 문법 나무로, JavaScript·TypeScript 계열은 문자열·주석과 중첩 블록을 구분하는 토큰 판정으로 바꾼다. 서버 P3 단계에는 앞 단계 실패와 무관하게 실행되는 조건을 둔다.

**왜** — 새 외부 꾸러미 없이 현재 macOS와 GitHub Ubuntu 실행기에서 같은 결과를 내면서, 이미 재현된 여러 줄 누락과 문자열·주석 오탐을 직접 닫을 수 있다.

**버린 길** — 정규식을 더 길게 만드는 길은 줄바꿈·주석·문자열·중첩 블록 조합마다 새 구멍이 생겨 폐기한다. JavaScript 전체 문법 분석 꾸러미를 새로 추가하는 길은 이 저장소에 꾸러미 관리 정본이 없고 이번 한 조건보다 변경 범위가 커서 채택하지 않는다.

**대가** — JavaScript·TypeScript 쪽은 전체 언어 변환기가 아니라 이 네 위반만 읽는 제한된 토큰 판정기다. 지원하지 못하는 문법이나 깨진 파일을 만나면 합격시키지 않고 검사 불가로 종료해야 한다.

**되돌리기** — 이 커밋만 되돌리면 이전 줄 단위 검사로 복귀한다. 다만 그러면 이 문서의 실패·통과 대조군이 다시 빨간불이 되어 되돌림의 안전 저하가 드러난다.

## 1. 현재 상태와 직접 확인 근거

- `scripts/acceptance-silent-failure-lint.sh:44-73`: 네 금지 형태를 모두 줄 단위 `grep`으로 찾는다. 프로그램 문법을 읽는 호출은 없다.
- `scripts/acceptance-silent-failure-lint.sh:16-17`: 문자열·주석 오탐과 여러 줄 `catch` 누락을 현재 한계로 명시한다.
- `scripts/acceptance-silent-failure-lint-mutations.sh:38-124`: 기존 1~8번 시험은 한 줄 위반과 정상 Python 한 건만 다뤄, 알려진 반례를 회귀 시험으로 잠그지 못한다.
- `.github/workflows/verify.yml:34-40`: 현재 실패하는 P1 전체 검사 다음에 P3 단계가 있어, 현재 원격 실행에서 P3가 건너뛰어진다.
- `private-reviews/p3-silent-failure-verdict-2026-08-19.md`: 이전 Codex 판정 원문은 여러 줄 누락 6건과 문자열·주석 오탐 3건을 격리 실행으로 기록한다. 이 경로는 회사 정책상 git에는 올리지 않지만 이번 착수 때 실제 존재를 재확인했다.
- 착수 HEAD `7bfaf7a`, `git status --porcelain` 빈 출력. 작업은 기존 PR #31 워크트리와 브랜치에서만 계속한다.

## 2. 근본 원인

1. 검사기가 문법 단위가 아니라 물리적 한 줄을 입력 단위로 삼는다.
2. 주석과 문자열을 실행 코드에서 분리하지 않는다.
3. 기존 시험이 구현자가 처음 생각한 한 줄 예시만 되풀이해, 검증자가 찾은 반례를 고정하지 않았다.
4. 서버 단계가 순차 실행 기본값에 기대면서, 의도적으로 실패하는 총괄 검사 뒤에 배치됐다.

## 3. 단일 인수 기준

**AC-P3-REACH:** `bash scripts/acceptance-silent-failure-lint-mutations.sh`가 다음 계약 전체를 한 번에 증명하고 프로그램 성적 0으로 끝나야 한다.

- 막아야 할 것: Python bare `except`의 줄연결 변형, JavaScript·TypeScript의 한 줄·여러 줄·주석만 든 빈 `catch`, 여러 줄 `catch { return null }`, 공백·주석을 낀 `|| []`와 `??` 실행식.
- 막지 말아야 할 것: Python 주석·일반 문자열·독스트링, JavaScript·TypeScript 주석·문자열·템플릿 문자열·정규식 안의 같은 글자, 타입이 명시된 Python `except`, 실제 처리가 있는 `catch`.
- 검사할 파일이 0개거나 문법 판정 자체가 성립하지 않으면 합격이 아니라 검사 불가 성적 2로 끝난다.
- 같은 시험이 `.github/workflows/verify.yml`에서 P3 단계에 연결되어 있고, 앞의 P1 전체 검사가 실패해도 P3 단계가 실행되도록 정적 배선 대조가 통과한다.
- 검사기 본문 또는 이 시험을 같은 변경에서 약하게 만들면 실제 `hooks/pre-commit`이 막고, 무해한 자기개선은 통과한다.
- 시험 종료 후 원본 작업공간의 `git status --porcelain`이 시작 기준선과 같다.

## 4. 반대 조건

- 여러 줄 위반 중 하나라도 프로그램 성적 0으로 통과하면 실패다.
- 주석·문자열·독스트링·템플릿 문자열·정규식 대조군 중 하나라도 차단되면 실패다.
- 서버 설정에서 P3 단계가 P1 실패 뒤 기본 순차 실행에만 의존하면 실패다.
- 새 외부 꾸러미나 원격 다운로드가 있어야만 검사할 수 있으면 실패다.
- 시험이 실제 검사기를 부르지 않고 판정을 다시 구현하면 실패다.

## 5. Harness 게이트 진행

- 게이트 0 시작 자격: 이 저장소에는 Makefile과 package.json이 없다. 정본 명령 `bash scripts/session-status.sh`를 사용한다. 기존 PR #31 자체가 미해결 빨간불이므로 새 작업공간을 만들지 않고 같은 빨간불을 닫는다.
- 게이트 1 스펙: 이 문서의 AC-P3-REACH 한 개와 GitHub 이슈 [#33](https://github.com/sangmokang/Valuehire_v6/issues/33) 한 개로 고정한다.
- 게이트 2 실패 먼저: 위 AC의 반례를 기존 뮤테이션 시험에 먼저 추가하고 현재 검사기에서 실패를 확인한다.
- 게이트 3 최소 수정: P3 검사기, 그 시험, 실제 훅 자기보호, 서버 실행 순서, 관련 정본만 수정한다.
- 게이트 4 검증: 원래 명령인 `bash scripts/session-status.sh`, P3 시험, 실제 훅, 관련 회귀 검사, 서버와 같은 셸 실행을 다시 돌린다.
- 게이트 5 배송: PR #31 브랜치에만 push하고 원격 본문을 한국어 검토 계약으로 고친 뒤 실제 서버 로그에서 P3 단계 실행을 확인한다.
- 게이트 6 종료: 병합·배포·메일 발송은 하지 않는다. 오너 승인 대기로 끝낸다.

## 6. 새 게이트 설계 3원칙

- [ ] 자기 선언 검증: “문법을 읽는다”는 주석을 믿지 않고, 기존에 놓친 변형과 기존에 잘못 막은 대조군을 같은 시험이 실제 검사기에 넣는다.
- [ ] 실패 방향 반전: 서버 실행 조건은 P1 실패가 있어도 P3를 실행하게 해야 하며, P3 자체 실패는 전체 서버 판정을 계속 불합격으로 남겨야 한다.
- [ ] 차단·통과 한 쌍: 막아야 할 사례와 막지 말아야 할 사례를 같은 수치 장부에 넣고 둘 중 어느 쪽이 깨져도 시험 전체가 실패한다.

## 7. 적대검증 항목

- 여러 줄·줄연결·주석 삽입으로 네 위반을 숨길 수 있는가.
- 문자열·독스트링·주석·템플릿 문자열·정규식 안의 글자가 오탐되는가.
- 중첩 블록과 중첩 괄호가 `catch` 끝을 잘못 자르게 만드는가.
- 깨진 문법이나 읽을 수 없는 파일이 조용히 합격하는가.
- 검사기·시험·서버 설정을 같은 커밋에서 약화하면서 위반을 통과시킬 수 있는가.
- P1 실패가 있어도 원격 로그에 P3 단계의 실제 출력이 남는가.
- 정상 Python/JavaScript/TypeScript 파일과 무해한 검사기 개선이 막히는가.

## 8. SOT 체크리스트

- [x] `docs/sot/INDEX.md` — 이 저장소의 정본 위치와 문서 분류 확인.
- [x] `docs/sot/coding-principles.md` — P3, P13, P15, P20과 V-1~V-5 확인.
- [x] `docs/sot/hook-contracts.md` — 스테이지 확정본 검사와 서버 동일 검사 계약 확인.
- [x] `docs/sot/verification-commands.md` — Make/npm이 아닌 실제 게이트 명령과 CI 고정 목록 확인.
- [x] `docs/sot/principles.yaml` — P3가 현재 “부분”이며 정규식 한계를 증거에 명시한 상태 확인.
- [x] `docs/sot/mechanism-registry.yaml` — 현재 P3 장치는 이 별도 명부의 관리 대상이 아님을 확인.
- [x] 사용자 제공 최상위 `AGENTS.md` — 단일 워크트리·증거 우선·검증 후 완료 계약 확인.
- [x] 루트 `CLAUDE.md`, 로컬 `AGENTS.md`, `docs/sot/00-sot-vs-wiki.md`, `docs/sot/04-coding-rules.md`는 이 저장소에 존재하지 않음을 파일 목록으로 확인. 없는 경로를 정본으로 꾸며내지 않는다.

## 9. 비범위

- P3의 “모든 핸들러가 상태와 함께 데이터베이스에 기록” 요건.
- P1을 제외한 나머지 원칙 구현과 P1 총괄 불합격 자체의 해소.
- 전체 JavaScript·TypeScript 언어 검사기 도입 또는 새 외부 꾸러미 추가.
- PR #31 병합, main 직접 push, 운영 반영, 배포, 메일 발송.
- 다른 워크트리와 전역 Claude/Codex 스킬 파일 수정.

## 10. 적대 검증 로그

구현 후 `env -u ANTHROPIC_API_KEY claude -p` 판정 원문과 실행 명령을 이 아래에 그대로 붙인다. 이어서 Codex가 Claude의 모든 증거를 독립 재현하고, 일치·불일치·Claude 누락을 표로 남긴다.

## 11. RED 증거 — 구현 전 실패 고정

실행 명령:

```bash
bash scripts/acceptance-silent-failure-lint-mutations.sh
```

원문 출력:

```text
PASS: 정상 Python 파일 — 위반 없음 — exit=0
PASS: bare except 주입 — exit=1 + bare-except 마커 — exit=1
PASS: bare/empty catch 주입 — exit=1 + bare-catch 마커 — exit=1
PASS: catch{return null} 주입 — exit=1 + catch-return-null 마커 — exit=1
PASS: || [] 주입 — exit=1 + or-empty-array-fallback 마커 — exit=1
PASS: ?? 주입 — exit=1 + nullish-coalescing-fallback 마커 — exit=1
PASS: 존재하지 않는 파일 지정 — 0건 스캔은 통과가 아니라 NOT_RUN(exit 2) — exit=2
PASS: 정상 fixture 재확인(회귀 없음) — exit=0
FAIL: Python 한 줄 handler bare except → BLOCKED — exit=0
FAIL: Python 줄연결 bare except → BLOCKED — exit=0
FAIL: Python 독스트링 안 except:는 실행 코드가 아니므로 통과 — exit=1
FAIL: JavaScript 여러 줄 빈 catch → BLOCKED — exit=0
FAIL: JavaScript 주석만 든 catch → BLOCKED — exit=0
FAIL: JavaScript catch·매개변수·블록 줄분리 → BLOCKED — exit=0
FAIL: TypeScript 여러 줄 catch return null → BLOCKED — exit=0
FAIL: JavaScript 괄호로 감싼 catch return null → BLOCKED — exit=0
FAIL: JavaScript 줄바꿈·내부공백·주석 || [] 3종 → 모두 BLOCKED — exit=0, hits=0/3
FAIL: JavaScript 문자열·템플릿·주석·정규식과 실제 처리 catch는 통과 — exit=1
FAIL: CI P3 단계는 앞 단계 실패와 무관하게 본체+회귀시험을 실행 — always+두 명령 정적 배선
PASS: 실제 hooks/pre-commit 배선(위반 스테이지 → BLOCKED) — exit=1
PASS: 실제 hooks/pre-commit 배선(정상 파일 → 통과) — exit=0
PASS: 검사기 자체 무력화 공격(같은 커밋에서 정규식 무력화+위반) → BLOCKED — exit=1
FAIL: 검사기 무해한 자기개선 커밋은 통과(벽이 아니라 게이트) — exit=1
PASS: 원본 worktree 상태 기준선 보존 — before/after 동일 여부=0
CHECKED: 24
```

→ 뭘 시켰나: 구현 전 검사기에 이전 적대검증 반례와 서버 실행 조건을 넣었다. / 뭐가 나왔나: 전체 24개 중 12개가 실패했고 명령은 성적 1로 끝났다. / 좋은 소식인가 나쁜 소식인가: 현재 결함 재현에는 좋은 소식이지만 제품 보호 상태에는 나쁜 소식이다. 이 출력이 구현 후 모두 통과해야 한다.

RED 커밋에서는 `hooks/pre-commit`이 검사 시험의 의도된 실패도 “검사기 약화”로 보아 막는다. 따라서 실패 시험을 보존하는 로컬 RED 커밋에만 `git commit --no-verify`를 쓰고 원격에는 보내지 않는다. GREEN 구현 커밋은 실제 훅을 생략하지 않고 통과시켜 이 예외가 배송 우회로 남지 않게 한다.
