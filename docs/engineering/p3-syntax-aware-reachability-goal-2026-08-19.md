# P3 문법 판정·서버 도달성 보강 — goal (2026-08-19)

## 결론

여러 줄로 숨긴 위반은 막고 설명문·주석·문자열은 통과시키는 수정이 로컬 시험 35개를 모두 통과했다. 앞선 총괄 검사가 실패해도 서버가 이 검사를 따로 실행하도록 분리했다.

Claude 1차 공격이 처리 코드가 있는 바깥 예외 블록 안의 위반을 전부 놓치는 결함을 찾아 실제 커밋까지 통과시켰다. 같은 반례를 회귀시험으로 고정하고 내부 코드도 끝까지 검사하도록 수정해 로컬에서는 다시 막았다. 아직 수정 후 재공격과 실제 서버 실행이 남았으며, 둘 중 하나라도 실패하면 다시 고친다. 다른 31개 원칙과 모든 예외 처리 결과의 데이터베이스 기록은 이번에 건드리지 않는다.

## 판단 근거

이전 작업은 같은 변경 안에서 검사기 자체를 약하게 만드는 공격을 막았지만, 검사 방식 자체는 줄 단위 문자열 검색으로 남았다. `scripts/acceptance-silent-failure-lint.sh:44-73`은 Python과 JavaScript 계열 파일을 `grep`으로 직접 읽고, 같은 파일 `16-17`은 문자열·주석 오탐과 여러 줄 누락을 한계로 인정한다.

서버 설정은 `.github/workflows/verify.yml:34-40`에서 32개 원칙 총괄 검사를 먼저 실행하고 P3 검사를 그 뒤에 둔다. 현재 총괄 검사는 미충족 원칙 31개 때문에 의도적으로 불합격이므로, 기본 순차 실행에서는 P3 단계가 시작되지 않는다. 이는 “로컬 훅은 우회 가능하므로 서버가 같은 검사를 맡는다”는 `docs/sot/coding-principles.md` P15의 취지와 맞지 않는다.

틀리면 두 종류의 문제가 남는다. 실제 위반을 여러 줄로 나눠 숨길 수 있고, 반대로 설명문에 금지 기호를 적었다는 이유만으로 정상 변경이 막힌다. 서버 검사가 실행되지 않으면 로컬 검사를 건너뛴 변경을 원격에서 다시 판정하지 못한다.

## 결정 카드

**무엇을** — Python은 표준 문법 나무로, JavaScript·TypeScript 계열은 문자열·주석과 중첩 블록을 구분하는 토큰 판정으로 바꾼다. 서버 P3 검사는 P1과 선후 관계가 없는 별도 작업으로 분리한다.

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

### Claude(V1) 실행 복구 기록

첫 실행은 저장소 폴더에서 같은 명령을 6분 넘게 기다렸지만 출력이 없어서 중단했다. 저장소 SessionStart 훅이 장시간 선행되는 환경 차이였고, 이 실행은 판정으로 세지 않는다(`NOT_RUN`). 전역 키를 제거한 인증 상태와 `/private/tmp` 한 줄 응답 시험(`READY`, exit 0)을 확인한 뒤, 저장소 절대경로를 명시한 같은 읽기 전용 프롬프트를 `/private/tmp`에서 다시 실행했다. 두 번째 실행은 exit 0과 아래 판정 전문을 냈다.

→ 뭘 시켰나: 첫 무응답의 원인이 모델 판정인지 시작 훅인지 분리하고 같은 검증을 깨끗한 시작 폴더에서 재실행했다. / 뭐가 나왔나: 첫 실행은 판정 없음, 복구 후 실행은 `VERDICT: FAIL`과 재현 가능한 결함 한 건을 냈다. / 좋은 소식인가 나쁜 소식인가: 검증 누락을 합격으로 세지 않고 실제 판정을 확보한 점은 좋지만, 수정본이 실제로 뚫린 것은 나쁜 소식이다.

### Claude(V1) 실행 명령의 전체 프롬프트

```text
적대적으로 부숴봐. 당신은 다른 엔진의 1차 검증자다. 검증 대상 저장소는 /Users/kangsangmo/Desktop/Valuehire_v6/worktrees/strict-principles-yaml 이고 현재 HEAD는 12a3c6b다. 현재 셸 시작 폴더가 /private/tmp인 것은 저장소의 SessionStart 검사가 장시간 선행되어 claude -p 출력이 막히는 환경 차이를 피하기 위한 것이다. 모든 저장소 명령은 위 절대경로를 명시해 실행하라.

검증 대상은 35d76a4..12a3c6b의 GREEN 구현이며, 사용자 요구는 docs/engineering/p3-syntax-aware-reachability-goal-2026-08-19.md의 단일 AC-P3-REACH다. 기존 실패 원문은 private-reviews/p3-silent-failure-verdict-2026-08-19.md다.

반드시 읽고 실행으로 공격할 파일:
- scripts/acceptance-silent-failure-lint.sh
- scripts/acceptance-silent-failure-lint-mutations.sh
- hooks/pre-commit
- .github/workflows/verify.yml
- docs/sot/coding-principles.md
- docs/sot/hook-contracts.md
- docs/sot/verification-commands.md
- docs/sot/principles.yaml
- 새 goal 문서

정조준 질문:
1) Python bare except의 줄연결/한 줄 handler 및 정상 문자열·주석·독스트링 구분이 진짜 AST로 되는가.
2) JS/JSX/TS/TSX 토큰 판정이 여러 줄 empty catch, comment-only catch, catch{return (null)}, || [] 변형, ??를 실제 코드에서 잡고 문자열·주석·template 본문·regex·JSX text에서는 오탐하지 않는가. 구현자가 안 넣은 반례도 직접 만들어라. 특히 regex/division 모호성, template interpolation, JSX/TSX generic, 중첩 괄호·블록, CRLF, Unicode, 파일명 공백을 공격하라.
3) 깨진 문법·읽기 실패·대상 0건이 조용히 PASS하는가.
4) hooks/pre-commit이 index 확정본을 보고, 검사기/뮤테이션을 같은 커밋에서 약화하는 공격을 막으며 정상 변경은 통과하는가. 훅·검사기·시험을 동시에 바꾸는 공격이 남는다면 과장 없이 구분하라.
5) GitHub workflow의 p3 job이 verify/P1과 실제 선행 의존성이 없고 checkout+본체+회귀시험을 실행하는가. 공격자가 같은 PR에서 workflow도 지우는 신뢰경계 한계와 이번 AC의 도달성 결함을 구분하라.
6) docs/sot 문구, 29/29 수치, step count 24, P3 status 부분이 실제와 일치하는가.
7) 원본 worktree를 훼손하지 않는가. 파괴적 fixture는 mktemp 격리에서만 만들고 GIT_DIR/GIT_WORK_TREE 등은 unset하라. 시작/종료 git status를 대조하라.

VERDICT: PASS는 위 AC가 실행 증거로 모두 성립하고 중대 누락/오탐이 없을 때만 가능하다. 결함마다 정확한 file:line, 재현 명령, 전체 출력, 사업 영향을 남겨라. 저장소와 전역 ~/.claude 및 ~/.codex 파일은 수정하지 마라. 검증 중 임시 파일은 mktemp 아래만 허용한다. 확인하지 못한 것은 PASS로 세지 마라.

[출력 형식 — 반드시 지킬 것]
읽는 사람은 기술 배경이 없는 사업 책임자다. 판정 내용은 절대 축소하지 말고, 표현만 풀어 써라.
1) 문서 맨 앞에 "결론". 결정할 사항 1개당 1~2문장, 전체 분량 상한 없음. 전문용어는 풀어 쓰더라도 결론에서는 쓰지 마라.
2) 그다음 "판단 근거": 왜 그렇게 봤는지, 갈림길에서 왜 이 해석을 골랐는지, 버린 해석은 왜 버렸는지, 이 판정이 틀리면 무엇이 깨지는지.
3) 그다음부터 기술 상세·명령·출력·file:line 전문. 증거는 하나도 생략하지 마라.
- 전문용어는 첫 등장 문장 안에서 괄호로 풀어 써라. 뒤에 몰아 쓴 용어집은 무효다.
- 터미널 출력·코드 블록·표를 붙였으면 바로 아래에 "→ 뭘 시켰나 / 뭐가 나왔나 / 좋은 소식인가 나쁜 소식인가" 1~3줄을 달아라.
- 첫 줄에 VERDICT: PASS|FAIL 한 줄을 두어라. 그 한 줄은 결론의 일부가 아니라 기계가 읽는 표식이므로 결론 제목 앞에 온다.
- file:line 을 인용하면 그 줄이 무슨 일을 하는 줄인지 한 마디 덧붙여라.
- 결함마다 심각도 라벨을 붙이고, 그 옆에 그대로 두면 사업/운영에 무슨 일이 생기는지 한 문장으로 덧붙여라(라벨을 지우지 마라).
- 설계 결정을 지적할 때는 "무엇을 / 왜 / 버린 대안 / 대가 / 되돌리는 법" 5줄로 적어라.
- 이번에 건너뛴 것·확인하지 못한 것·중간에 실패해서 다시 한 것을 판정 앞부분에 명시해라.
- 추정과 확인된 사실을 구분 표시해라(확인 못 한 것은 ※).
- 한국어 존칭체. 초등학생용 비유는 쓰지 마라 — 성인 의사결정자 수준으로 써라.
```

실제 호출은 `env -u ANTHROPIC_API_KEY -u CLAUDE_CODE_SSE_PORT claude -p <위 프롬프트>`였고, 저장소·전역 파일 수정 없이 임시 폴더에서만 공격하도록 제한했다.

### Claude(V1) 판정 원문

```text
# 검증 결과

VERDICT: FAIL

# 결론

이번 수정은 통과시켜서는 안 됩니다. 겉보기로는 "조용한 실패"(오류가 나도 알아채지 못하게 값만 살짝 바꿔서 넘어가는 코드 작성 방식, 예: 예외를 잡고도 아무 처리 없이 넘어가거나 기본값으로 슬쩍 때우는 것)를 막는 검사기가 29개 자체 시험을 전부 통과했다고 주장하고, 실제로 그 29개는 제가 다시 돌려봐도 그대로 통과합니다. 하지만 그 29개 시험이 다루지 않은 아주 흔한 코드 형태 하나를 제가 직접 만들어 넣어보니, 금지하려던 네 가지 위반(빈 예외 처리, 예외를 잡고 그냥 null만 돌려주기, `|| []` 로 오류를 숨기는 기본값, `??` 로 오류를 숨기는 기본값) 전부를 한꺼번에 완전히 무력화할 수 있었습니다. 이 결함은 특별한 해킹 기법이 아니라, "이미 뭔가 처리하는 예외 처리 블록 안에 원하는 나쁜 코드를 한 번 더 넣기"라는 지극히 평범한 코드 배치만으로 발동합니다. 저는 이 공격을 검사 스크립트뿐 아니라 실제로 커밋을 막아야 할 `hooks/pre-commit`(사람이 코드를 저장소에 올리기 직전 자동으로 실행되는 검사 장치)에도 그대로 적용해 실제 git 커밋을 성공시켰습니다. 즉 이번 구현은 "여러 줄로 숨긴 위반을 막는다"는 이번 작업의 핵심 목표를 정면으로 못 지킵니다.

반면 사용자 요구 문서(`docs/engineering/p3-syntax-aware-reachability-goal-2026-08-19.md`)의 나머지 항목들 — 파이썬 쪽 문법 분석의 견고함, 문자열·주석·독스트링·템플릿 문자열·정규식·JSX 텍스트에서의 오탐 방지, 깨진 문법이나 검사 대상 0건일 때 조용히 통과시키지 않는 안전장치, 검사기 자체를 같은 커밋에서 약화시키는 공격에 대한 방어, GitHub 서버 쪽 검사가 실제로 앞 단계 실패와 무관하게 독립 실행되도록 배선된 부분, 문서에 적힌 "29/29", "전체 24단계" 같은 숫자들 — 은 제가 독립적으로 재현·검증한 결과 모두 사실과 일치했고 결함이 없었습니다. 이 부분들은 칭찬할 만한 수준으로 잘 만들어졌습니다. 다만 제품 전체의 판정은 가장 취약한 지점에 좌우되므로, 위에서 말씀드린 치명적 결함 하나 때문에 전체 판정은 실패입니다.

그대로 배포하면 생기는 사업 위험은 이렇습니다: 개발자가 (의도적이든 실수든) 오류를 조용히 숨기는 코드를, 이미 뭔가 로그를 남기거나 처리를 하는 것처럼 보이는 예외 처리 블록 안에 한 번 더 겹쳐 넣기만 하면, 로컬 검사도 서버 검사도 이를 전혀 잡아내지 못한 채 그대로 저장소에 들어갑니다. 후보자 데이터 수집·처리 파이프라인에서 이런 코드가 조용히 실패하면, 실패 사실 자체가 기록에 남지 않아 사업 운영진이 "정상적으로 처리됐다"고 착각하게 되는, 이번 작업이 원래 막으려던 바로 그 상황이 재발합니다.

# 판단 근거

## 어디서 갈렸고 왜 이 해석을 택했는가

가장 중요한 갈림길은 "구현자가 이미 만든 29개 시험을 전부 통과했다는 사실을, 검증이 끝났다는 증거로 볼 것인가, 아니면 검증자가 독립적으로 새 반례를 만들어 그 시험들이 놓친 지점을 직접 찾아야 하는가"였습니다. 저는 후자를 택했습니다. 이유는 이 작업의 목표 문서 자체가 "다른 검증자의 공격과 실제 서버 실행이 남아 있다"고 스스로 명시했고(목표 문서 결론 문단), 제 임무 지시문도 "구현자가 안 넣은 반례도 직접 만들어라"라고 못박았기 때문입니다. 만약 제가 전자를 택해 29/29 통과만으로 합격 처리했다면, 이번 검증은 구현자가 이미 확인한 것을 다시 확인하는 것에 불과해 아무 가치가 없었을 것이고, 실제로 존재하는 심각한 우회로를 놓쳤을 것입니다.

두 번째 갈림길은 "제가 찾은 중첩 catch 우회가 정말로 이번 인수 기준(AC-P3-REACH) 범위 안의 결함인가, 아니면 범위 밖의 별개 문제인가"였습니다. 저는 범위 안이라고 판단했습니다. 목표 문서의 반대 조건 1번이 "여러 줄 위반 중 하나라도 프로그램 성적 0으로 통과하면 실패다"라고 명시했고, 같은 문서 §7 적대검증 항목에 "중첩 블록과 중첩 괄호가 catch 끝을 잘못 자르게 만드는가"가 이미 검증자가 확인해야 할 항목으로 못박혀 있습니다. 제가 찾은 결함은 정확히 이 항목이 우려한 그 시나리오이고, 실제로 exit 0(통과)으로 끝났습니다. 버린 해석은 "네 가지 금지 패턴을 감지하는 개별 로직 자체는 맞으니 부분 성공으로 봐야 한다"는 것인데, 이 해석을 택했다면 반대 조건에 명시된 "하나라도 통과하면 전체 실패"라는 문서 자체의 규칙과 정면으로 어긋나 무효한 해석이 됩니다.

세 번째 갈림길은 "이 결함을 스크립트 실행만으로 확인할 것인가, 실제 커밋까지 재현할 것인가"였습니다. 저는 실제 `git commit`까지 재현하는 쪽을 택했습니다. 스크립트 실행만으로는 "이론적으로 검사기가 놓친다"는 정도만 보이지만, 실제 훅과 실제 커밋까지 성공시켜야 "실제 운영에서 이 위반이 저장소에 들어갈 수 있다"는 사업적 결론을 뒷받침할 수 있기 때문입니다. 실제로 격리된 임시 저장소에서 커밋이 성공했습니다(아래 §3 증거).

이 판정이 틀렸다면 무엇이 깨지는가: 만약 제가 이 결함을 과대평가한 것이라면(예: 중첩 catch 안에 진짜 위반을 넣는 코드 패턴이 실무에서 절대 나오지 않는다면), 이번 FAIL 판정 때문에 실제로는 안전한 릴리스가 한 번 더 지연되는 비용이 생깁니다. 하지만 이 결함은 "정상적으로 로그를 남기는 예외 처리 안에 또 다른 함수를 정의하거나 다른 try/catch를 넣는" 매우 흔한 코드 스타일만으로 발동하므로, 실무에서 나오지 않을 패턴이라고 보기 어렵습니다.

## 확인하지 못한 것 · 건너뛴 것 · 재시도한 것

- ※ 실제 GitHub Actions 원격 서버에서 이번 브랜치를 새로 실행해보지는 않았습니다. `.github/workflows/verify.yml` 파일 내용과 `p3` 작업(job)의 정적 배선(파일에 적힌 구조)만 확인했고, 이 부분은 회귀 시험(`scripts/acceptance-silent-failure-lint-mutations.sh`)이 이미 같은 정적 대조를 수행하며, 저도 파일을 직접 읽어 `needs:`(선행 작업 의존성 지정 키워드) 항목이 `p3` 작업에 없음을 확인했습니다. 이는 "P1이 실패해도 실행된다"는 것에 대한 구조적 증거이지 실제 서버 로그 증거는 아닙니다.
- ※ `??=`, `||=` 같은 "복합 대입 연산자"(예: `cfg.value ??= 3`처럼 값이 없을 때만 조용히 대입하는 문법)가 검사기에서 감지되지 않는 것을 확인했으나, 이는 인수 기준 원문이 "`??` 실행식"과 "`|| []`"만 명시했지 이 변형까지 요구하지 않았으므로 AC 위반으로 세지 않고 낮은 심각도의 별도 참고 사항으로만 기록합니다.
- 재시도한 것은 없습니다. 모든 명령은 첫 실행에서 의도한 출력을 얻었습니다.
- 임시 실습은 전부 `mktemp`로 만든 격리 디렉터리(`/tmp/p3-attack.*`, 별도 임시 git 저장소)에서만 진행했고, 저장소 원본이나 `~/.claude`, `~/.codex` 파일은 전혀 건드리지 않았습니다. 작업 종료 후 이 임시 파일들은 모두 삭제했습니다.

---

# 기술 상세 — 명령·출력·file:line 전문

## 0. 시작 기준선 확인

명령:
```bash
cd /Users/kangsangmo/Desktop/Valuehire_v6/worktrees/strict-principles-yaml
git status --porcelain=v2 --branch
git log -1 --format='%H %ci'
```
출력 요약: `HEAD=12a3c6b79c82bcb90e4767ca2e5279d77812a840`, 브랜치 `task/strict-principles-yaml`, `git status`는 깨끗함(추적 대상 변경 없음, ahead +2).
→ 뭘 시켰나: 검증 시작 전 원본 상태를 기록했습니다. / 뭐가 나왔나: 지시받은 HEAD `12a3c6b`와 일치했습니다. / 좋은 소식인가 나쁜 소식인가: 중립(기준점 확보).

## 1. 원본 회귀 시험 재실행 — 구현자 주장 재현

명령:
```bash
bash scripts/acceptance-silent-failure-lint-mutations.sh
```
출력: `CHECKED: 29`, 전부 `PASS`, `EXIT=0` (전문은 위 대화에 그대로 인용됨).
→ 뭘 시켰나: 구현자가 GREEN 증거로 제출한 원문 그대로 재현했습니다. / 뭐가 나왔나: 문서 §12의 주장과 완전히 일치했습니다. / 좋은 소식인가 나쁜 소식인가: 좋은 소식입니다 — 이 부분에서는 문서 위조나 과장이 없습니다.

## 2. 핵심 결함 — 중첩 `catch` 내부 스캔 누락 (CRITICAL)

**결함 위치**: `scripts/acceptance-silent-failure-lint.sh:407` — `index = end_body` 줄입니다. 이 줄은 `catch` 블록 하나를 처리한 뒤, 그 블록의 시작 중괄호부터 끝 중괄호까지 사이의 모든 토큰(글자 단위가 아니라 의미 단위로 쪼갠 코드 조각)을 건너뛰고 바로 끝 중괄호 위치로 커서를 이동시키는 역할을 합니다. 바로 다음 줄 `scripts/acceptance-silent-failure-lint.sh:408`(`index += 1`)이 그 끝 중괄호마저 지나쳐 버립니다.

**왜 문제인가**: 이 검사기는 전체 코드를 토큰(의미 단위 조각) 리스트로 한 번 쪼갠 뒤, 처음부터 끝까지 하나씩 훑으면서 `??`, `||`, `catch` 키워드를 만날 때마다 검사합니다(`scripts/acceptance-silent-failure-lint.sh:378` `while index < len(tokens):` 부터 시작하는 반복문). 그런데 `catch` 블록을 하나 처리하고 나면, 그 블록 **내부에 있던 모든 토큰을 다시 검사하지 않고 통째로 건너뜁니다**. 그 `catch` 블록 자체는 안에 `log(...)` 같은 실제 처리 코드가 있어 "정상 처리하는 catch"로 판정되어 통과하지만, 문제는 그 안에 또 다른 `catch`, `??`, `|| []`가 숨어 있어도 전혀 검사되지 않는다는 것입니다.

### 2-1. 스크립트 단독 실행으로 1차 확인

명령(격리된 `/tmp/p3-attack.*` 디렉터리에 파일 생성 후 실행):
```bash
bash "$LINT" "$MYTMP/nested_nullish_in_handled_catch.js"
```
대상 파일 내용:
```javascript
function load(cfg) {
  try {
    return risky();
  } catch (e) {
    log(e);
    return cfg.value ?? 3;
  }
}
```
출력:
```
CHECKED_FILES: 1
PASS: bare except/catch, catch{return null}, ||[], ?? 실행 패턴 0건
EXIT=0
```
→ 뭘 시켰나: "실제 처리(log)는 있지만 그 처리 안에 `??` 조용한 실패 폴백이 함께 있는" catch를 넣었습니다. / 뭐가 나왔나: 검사기는 이 파일을 완전 정상(EXIT=0)으로 판정했습니다. / 좋은 소식인가 나쁜 소식인가: 나쁜 소식입니다 — 인수 기준이 명시적으로 요구하는 "`??` 실행식 차단"이 이 catch 안에서는 작동하지 않습니다.

같은 방식으로 만든 나머지 두 공격도 동일하게 통과(EXIT=0)했습니다.

- `nested_bare_catch.js`(바깥 catch 안에 진짜 빈 `catch(e2){}`를 중첩) → `EXIT=0`
- `nested_or_empty_in_handled_catch.js`(바깥 catch 안에서 `|| []`로 폴백) → `EXIT=0`

### 2-2. 궁극 공격 — 4대 금지 패턴 전부를 한 파일에 은닉

명령:
```bash
bash "$LINT" "$MYTMP/ultimate_hide.js"
```
대상 파일 내용(요약: 바깥 `catch(wrapError)`가 `log(wrapError)`로 "정상 처리"를 하는 것처럼 보이게 한 뒤, 그 블록 안에 4개 함수를 정의해 각각 ①`catch(e){return null}`, ②`catch(e){}`, ③`list.items || []`, ④`cfg.retries ?? 3`을 그대로 심었습니다):
```javascript
function wrapper() {
  try {
    setup();
  } catch (wrapError) {
    log(wrapError);
    function realLoad(path) {
      try { return fs.readFileSync(path); } catch (e) { return null; }
    }
    function realFallback(list) { return list.items || []; }
    function realNullish(cfg) { return cfg.retries ?? 3; }
    function realBareCatch() {
      try { risky(); } catch (e) {}
    }
  }
}
```
출력:
```
CHECKED_FILES: 1
PASS: bare except/catch, catch{return null}, ||[], ?? 실행 패턴 0건
EXIT=0
```
→ 뭘 시켰나: 검사기가 막으려는 네 가지 위반 전부를 한 파일 안에, 각각 문자 그대로(글자 하나도 안 바꾸고) 넣되 바깥 껍데기 catch 하나로만 감쌌습니다. / 뭐가 나왔나: 네 가지가 전부 검출되지 않고 완전 통과했습니다. / 좋은 소식인가 나쁜 소식인가: 매우 나쁜 소식입니다 — 이것은 우회가 아니라 사실상 검사기 무효화입니다.

### 2-3. 실제 `hooks/pre-commit`으로 진짜 커밋까지 성공 재현

이 부분은 원본 저장소를 전혀 건드리지 않기 위해, `mktemp -d`로 새로 만든 완전히 별도의 임시 git 저장소 안에서 원본의 `hooks/pre-commit`, `scripts/acceptance-silent-failure-lint.sh`, `verify.sh` 등을 그대로 복사해 진짜로 초기화하고 실행했습니다.

명령(핵심 부분만 발췌):
```bash
cd "$HOOKTMP"
cat > scripts/hidden_violation.js <<'EOF'
function wrapper() {
  try { setup(); } catch (wrapError) {
    log(wrapError);
    function realLoad(path) {
      try { return fs.readFileSync(path); } catch (e) { return null; }
    }
    function realBareCatch() { try { risky(); } catch (e) {} }
    function realFallback(list) { return list.items || []; }
    function realNullish(cfg) { return cfg.retries ?? 3; }
  }
}
EOF
git add scripts/hidden_violation.js
bash hooks/pre-commit
git commit --quiet -m "hidden violation via nested catch"
```
출력:
```
HOOK2_EXIT=0
COMMIT2_EXIT=0
commit 19673fb74107b8c7a6c15314d67a83ab37a41729
 scripts/hidden_violation.js | 23 +++++++++++++++++++++++
```
→ 뭘 시켰나: 검사기가 아니라 실제 커밋을 막는 문지기인 `hooks/pre-commit`(§8 "조용한 실패 패턴" 검사 구간, `hooks/pre-commit:222-272`)에 같은 파일을 실제로 스테이지하고 훅을 실행한 뒤, 훅이 통과하면 실제로 커밋까지 시도했습니다. / 뭐가 나왔나: 훅도 통과(exit 0)했고, 실제 git 커밋도 성공했습니다. 4개 금지 패턴이 담긴 파일이 커밋 이력에 그대로 들어갔습니다. / 좋은 소식인가 나쁜 소식인가: 매우 나쁜 소식입니다. 이 결함은 스크립트 수준의 이론적 결함이 아니라, 실제 저장소에 이런 코드가 들어가는 것을 막지 못한다는 실증입니다.

대조군으로 같은 임시 저장소에서 진짜 정상 파일 커밋 시도(`scripts/normal.js`)는 `HOOK1_EXIT=0`으로 정상 통과해, 훅 자체가 무작정 다 막는 고장이 아니라 이 특정 결함만 뚫려 있음을 확인했습니다.

### 2-4. 대조 실험 — `try` 블록(캐치가 아닌) 안의 중첩 위반은 정상 검출됨

명령:
```bash
bash "$LINT" "$MYTMP/js_nested_in_try.js"
```
대상 파일(중첩 위반이 `catch`가 아니라 `try` 블록 안에 있음):
```javascript
function outer() {
  try {
    function inner() {
      try { return 1; } catch (e) {}
    }
    return inner();
  } catch (e) {
    return -1;
  }
}
```
출력:
```
FAIL: /tmp/.../js_nested_in_try.js:4: bare-catch — try { return 1; } catch (e) {}
CHECKED_FILES: 1
FAIL: P3 조용한 실패 패턴 발견 — 명시적 assertX() 관문으로 대체할 것
EXIT=1
```
→ 뭘 시켰나: 같은 중첩 구조이지만 바깥 껍데기를 `catch`가 아니라 `try`로 바꿔봤습니다. / 뭐가 나왔나: 이번엔 정상적으로 검출(EXIT=1)됐습니다. / 좋은 소식인가 나쁜 소식인가: 이 결과는 결함의 원인을 정확히 특정하는 좋은 소식입니다 — 문제는 "중첩" 자체가 아니라, `js_findings` 함수(`scripts/acceptance-silent-failure-lint.sh:375-409`)가 오직 `catch` 블록을 처리한 직후에만 `index = end_body`로 건너뛰기 때문임을 확정했습니다.

### 2-5. Python 쪽은 같은 유형의 결함이 없음을 확인 (대조군)

명령:
```bash
bash "$LINT" "$MYTMP/py_nested_bare_except.py"
```
대상 파일(정상 처리하는 `except ValueError` 안에 중첩된 진짜 bare except):
```python
def outer():
    try:
        return risky()
    except ValueError as e:
        log(e)
        def inner():
            try:
                return 1
            except:
                return None
        return inner()
```
출력:
```
FAIL: .../py_nested_bare_except.py:9: bare-except — except:
EXIT=1
```
→ 뭘 시켰나: 파이썬 쪽에서 같은 유형의 은닉을 시도했습니다. / 뭐가 나왔나: 정상적으로 검출됐습니다. / 좋은 소식인가 나쁜 소식인가: 좋은 소식입니다 — 파이썬은 `ast.walk`(파이썬 표준 라이브러리의 구문 나무 전체 순회 기능, `scripts/acceptance-silent-failure-lint.sh:453-458`)를 쓰기 때문에 중첩 깊이와 무관하게 모든 노드를 훑습니다. 이번 결함은 JavaScript/TypeScript 쪽 손수 작성한 토큰 판정기에만 있는 결함이며, 파이썬 쪽 설계(표준 문법 나무 사용)가 왜 더 안전한지를 보여주는 대조 증거이기도 합니다.

**심각도: 치명적(CRITICAL)** — 그대로 두면 개발자가 "이미 뭔가 처리하는 예외 블록 안에 새 함수나 새 try/catch를 추가로 정의"하는, 실무에서 매우 흔한 코드 구조만으로 검사기를 완전히 무력화할 수 있습니다. 이는 우연한 실수뿐 아니라 검사를 피하고 싶은 의도적 시도에도 그대로 열려 있는 통로입니다.
- 무엇을: `js_findings`가 `catch` 블록을 판정한 뒤 그 내부 토큰 전체를 재검사하지 않고 건너뜁니다.
- 왜: 처리 로직(빈 catch인지, `return null`인지)을 판정하고 나면 "이 catch는 끝났다"고 보고 다음 토큰으로 넘어가려 했던 것으로 보입니다. ※ 의도는 코드 주석에 명시되지 않아 추정입니다.
- 버린 대안: catch 처리 여부를 판정한 뒤에도 본문 내부 토큰들을 `index+1`부터 하나씩 계속 순회하며 중첩된 `??`/`||`/`catch`를 재귀적으로 다시 검사하는 방식(실제로 `try` 블록에서는 이런 재귀적 전체 순회가 이미 일어나고 있어 `try` 쪽은 안전합니다).
- 대가: catch 블록 내부에 숨긴 모든 위반이 영원히 검출되지 않습니다.
- 되돌리는 법: `catch` 처리 판정 후 `index = end_body`로 건너뛰지 말고, catch 본문 내부 토큰들도 재귀적으로(또는 스택 기반으로) 계속 스캔하도록 바꿔야 합니다. 이 결함은 §22 "검사기 자체 무력화 공격" 뮤테이션 시험처럼 새로운 회귀 시험으로 반드시 고정해야 재발을 막을 수 있습니다.

## 3. 나머지 공격 항목 — 전부 정상 방어 확인 (구조적으로 견고함)

아래 항목들은 모두 제가 별도로 만든 반례이며, 전부 검사기가 의도대로 동작했습니다.

| 공격 | 명령/파일 | 결과 | 판정 |
|---|---|---|---|
| `)` 뒤 나눗셈/정규식 모호성 | `if (check(x)) /pattern/.test(x); return x \|\| [];` | `FAIL: or-empty-array-fallback`, `EXIT=1` | 정상 검출, 렉서 손상 없음 |
| CRLF 여러 줄 빈 catch | `\r\n` 줄바꿈의 `catch(e){\r\n}` | `FAIL: bare-catch`, `EXIT=1` | 정상 검출 |
| 한글 주석·문자열 vs 실제 위반 혼재 | 한글 주석/문자열 안 `catch (e) {}` 문구 + 실제 bare-catch | 실제 것만 `FAIL`, `EXIT=1` | 오탐 없음, 실제 검출 정상 |
| 공백 포함 파일명 | `file with space.js` | `FAIL: bare-catch`, `EXIT=1` | 정상 처리 |
| git 저장소 아닌 곳, 인자 없음(대상 0건) | 빈 mktemp 디렉터리에서 실행 | `NOT_RUN`, `EXIT=2` | P20(0건 처리는 합격 아님) 준수 |
| `except*`(예외 그룹, 항상 타입 필요) | 문법만 성립 확인 | `EXIT=0`(정상, 반례 아님) | 문법 성립 확인용, 위반 아님이 맞음 |

→ 뭘 시켰나: 지시받은 정조준 질문 1·2·3(파이썬 AST 견고성, 정규식/나눗셈 모호성, 템플릿·JSX, CRLF, 유니코드, 공백 파일명, 대상 0건·깨진 문법)을 모두 직접 반례로 만들어 실행했습니다. / 뭐가 나왔나: 위 표의 결과와 같이 전부 의도대로 동작했습니다. / 좋은 소식인가 나쁜 소식인가: 좋은 소식입니다 — §2의 치명적 결함을 제외하면 이 검사기의 문법 판정 골격 자체는 상당히 견고합니다.

## 4. hooks/pre-commit — 인덱스 확정본 대조·같은 커밋 약화 방어 (정조준 질문 4)

- `hooks/pre-commit:39` — 커밋될 파일 목록을 `git diff --cached`로 읽는 줄(작업 화면이 아니라 실제 저장될 내용을 봄).
- `hooks/pre-commit:248-260` — 검사 대상 파일과 검사기 자신을 모두 `git show ":$f"`로 인덱스(다음 커밋에 확정될 임시 저장 공간)에서 떠서 별도 임시 폴더에 복사한 뒤 그 사본으로 검사하는 줄. 작업 화면만 덮어써 우회하는 공격을 막습니다.
- `hooks/pre-commit:274-319`(§9) — 검사기 자신이나 뮤테이션 시험 파일이 같은 커밋에 포함되면, "이번 커밋이 확정할 버전 그대로"의 검사기로 뮤테이션 시험을 재실행해 여전히 알려진 위반을 잡아내는지 재확인하는 방어입니다.

이 부분은 원본 시험(§1)에서 이미 "검사기 자체 무력화 공격(같은 커밋에서 정규식 무력화+위반) → BLOCKED — exit=1"과 "검사기 무해한 자기개선 커밋은 통과 — exit=0" 두 항목으로 실제 실행 검증되어 있고, 제가 재실행해도 동일하게 통과했습니다. 다만 이 §9 방어는 **알려진 단순 위반(정규식을 못 맞는 문자열로 바꾸는 식의 명시적 약화)만 잡을 뿐**, §2에서 발견한 "애초에 검사기 로직 자체에 내재된 구조적 결함"은 약화 공격이 아니라 이미 존재하는 버그이므로 §9가 잡을 수 있는 종류가 아닙니다. 즉 훅·검사기·시험을 동시에 바꾸는 공격은 이 저장소가 방어하고 있지만, "애초에 검사기가 원래부터 놓치는 경우"는 훅·시험 동시 변경 없이도(정상적인 단일 커밋만으로) 뚫립니다 — 이는 제가 지시받은 대로 정확히 구분해서 보고드리는 부분입니다.

## 5. GitHub workflow p3 작업의 독립성 (정조준 질문 5)

`.github/workflows/verify.yml:14-24`:
```yaml
jobs:
  p3:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: P3 조용한 실패 패턴 검사 (bare except/catch, ??, ||[])
        run: |
          bash scripts/acceptance-silent-failure-lint.sh
          bash scripts/acceptance-silent-failure-lint-mutations.sh

  verify:
    runs-on: ubuntu-latest
    steps: ...
```
→ 뭘 시켰나: `p3` 작업(job)에 `needs:`(다른 작업이 끝나야 시작한다는 선행 조건 키워드)가 있는지 파일을 직접 읽어 확인했습니다. / 뭐가 나왔나: `p3` 작업에는 `needs:`가 없고, `verify` 작업과 완전히 별도로 나열되어 있습니다. GitHub Actions에서 `needs:` 없는 작업은 다른 작업의 성공/실패와 무관하게 병렬로 즉시 실행됩니다. / 좋은 소식인가 나쁜 소식인가: 좋은 소식입니다. 앞선 검증자(원문 `private-reviews/p3-silent-failure-verdict-2026-08-19.md`)가 지적한 "P1 실패 뒤에 순차 배치되어 P3가 실행되지 않는다"는 결함은 이번 수정에서 구조적으로 해소됐습니다. 다만 이것은 파일 안의 정적 배선 확인이며, 실제 GitHub 서버 로그로 이번 브랜치의 P3 실행을 재확인하지는 않았습니다(※ 앞서 명시한 미확인 항목). 같은 PR에서 이 workflow 파일 자체를 지워버리는 공격은 GitHub 저장소 신뢰 경계 밖의 문제(브랜치 보호 규칙 등 저장소 설정에 달린 문제)이며, 이번 AC의 "도달성 결함"과는 다른 범주임을 구분해 드립니다 — 이번 검증에서는 그런 시나리오는 다루지 않았습니다.

## 6. docs/sot 수치·문구 일치 (정조준 질문 6)

- `docs/sot/principles.yaml:25-36`: P3 항목의 `status: "부분"`과 근거 문구가 "회귀 시험 29/29"라고 명시. → 제가 §1에서 재실행한 결과(`CHECKED: 29`, 전부 PASS)와 정확히 일치합니다.
- `docs/sot/verification-commands.md:20`: "워크플로 스텝은 checkout 2개와 이름 있는 검증 22개, 총 24개다." → 실제 파일을 세어보니 `p3` 작업 1개 checkout + 1개 이름있는 단계, `verify` 작업 1개 checkout(`fetch-depth: 0` 옵션 포함) + 21개 이름있는 단계로, 합계 checkout 2개 + 이름있는 단계 22개 = 24개. 정확히 일치합니다.
- `docs/sot/hook-contracts.md:40-42`: "P3의 CI 검사는 P1과 선후 관계가 없는 별도 `p3` 작업에서 실행한다"는 문구도 §5에서 확인한 실제 파일 구조와 일치합니다.

→ 좋은 소식인가 나쁜 소식인가: 문서 수치·문구 자체는 전부 정확했습니다. 다만 `docs/sot/principles.yaml:36`의 "여러 줄·주석 삽입·괄호·배열 공백 변형을 잡으면서"라는 표현은, 제가 §2에서 입증한 catch-내부-중첩 변형까지는 잡지 못하므로 실제 방어 범위보다 넓게 들리는 표현입니다. 문서가 거짓말을 한 것은 아니지만("모든 중첩"이라고 명시하지는 않았음), 실제 결함이 존재하는 상태에서 "변형을 잡는다"는 일반적 표현만 남아 있으면 향후 이 문서만 보고 안전하다고 오판할 위험이 있습니다.

## 7. 원본 worktree 무손상 확인 (정조준 질문 7)

명령:
```bash
git status --porcelain=v2 --branch  # 시작 시
... (모든 공격은 /tmp/p3-attack.* 및 별도 mktemp git 저장소에서만 수행) ...
git status --porcelain=v2 --branch  # 종료 시
diff /tmp/pre_status.txt /tmp/post_status.txt
git rev-parse HEAD
```
출력: `diff` 결과 `IDENTICAL`, `HEAD`는 시작·종료 모두 `12a3c6b79c82bcb90e4767ca2e5279d77812a840`로 동일.
→ 뭘 시켰나: 검증 시작 직후와 모든 공격이 끝난 직후 원본 저장소의 상태를 대조했습니다. / 뭐가 나왔나: 완전히 동일했습니다. / 좋은 소식인가 나쁜 소식인가: 좋은 소식입니다 — 이번 검증 과정에서 원본 워크트리에는 어떤 흔적도 남지 않았습니다. 파괴적 실험은 전부 `mktemp` 격리 공간에서만 수행했고 `GIT_DIR`/`GIT_WORK_TREE` 등은 사용하지 않았습니다(뮤테이션 스크립트 자체도 `scripts/acceptance-silent-failure-lint-mutations.sh:7-8`에서 이 환경변수들을 `unset`하도록 이미 되어 있고, 제 추가 공격도 별도 `mktemp -d` 안에서만 `git init`했습니다). 모든 임시 파일과 임시 저장소는 작업 종료 후 삭제했습니다.
```

→ 뭘 시켰나: 기존 29개 시험을 반복하는 데서 멈추지 말고 구현자가 넣지 않은 중첩·문법·파일명·서버 배선 반례를 만들게 했다. / 뭐가 나왔나: 처리 코드가 있는 바깥 `catch` 뒤에서 내부 전체를 건너뛰어 네 위반과 실제 커밋이 모두 통과하는 치명적 결함을 찾았다. / 좋은 소식인가 나쁜 소식인가: 나쁜 소식이며 AC의 반대조건에 해당하므로 즉시 RED로 고정했다.

## 11. RED 증거 — 구현 전 실패 고정

실행 명령:

```bash
bash scripts/acceptance-silent-failure-lint-mutations.sh
```

→ 뭘 시켰나: 새 구현을 넣기 전에 이전 검증자가 찾은 반례와 서버 실행 조건을 기존 검사기에 적용했다. / 뭐가 나왔나: 아래 원문처럼 절반이 실패했다. / 좋은 소식인가 나쁜 소식인가: 실패를 재현해 시험으로 잠갔다는 점은 좋은 소식이다.

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

## 12. GREEN 증거 — 최소 구현 후 로컬 합격

실행 명령:

```bash
bash scripts/acceptance-silent-failure-lint-mutations.sh
```

→ 뭘 시켰나: 문법 판정과 서버 독립 작업 배선을 반영한 뒤, 실패·통과 대조군과 실제 커밋 문지기를 전부 다시 실행했다. / 뭐가 나왔나: 아래 29개가 모두 PASS이고 프로그램 성적은 0이었다. / 좋은 소식인가 나쁜 소식인가: 로컬 인수 기준에는 좋은 소식이며, 다른 엔진과 실제 서버 검증 전에는 최종 합격이 아니다.

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
PASS: Python 한 줄 handler bare except → BLOCKED — exit=1
PASS: Python 줄연결 bare except → BLOCKED — exit=1
PASS: Python 독스트링 안 except:는 실행 코드가 아니므로 통과 — exit=0
PASS: JavaScript 여러 줄 빈 catch → BLOCKED — exit=1
PASS: JavaScript 주석만 든 catch → BLOCKED — exit=1
PASS: JavaScript catch·매개변수·블록 줄분리 → BLOCKED — exit=1
PASS: TypeScript 여러 줄 catch return null → BLOCKED — exit=1
PASS: JavaScript 괄호로 감싼 catch return null → BLOCKED — exit=1
PASS: JavaScript 줄바꿈·내부공백·주석 || [] 3종 → 모두 BLOCKED — exit=1, hits=3/3
PASS: JavaScript 문자열·템플릿·주석·정규식과 실제 처리 catch는 통과 — exit=0
PASS: 템플릿 본문은 무시하고 보간식 안 ??만 BLOCKED — exit=1, hits=1/1
PASS: JSX 본문은 무시하고 중괄호 실행식 안 ??만 BLOCKED — exit=1, nullish=1/1, other=0/0
PASS: 중첩 블록에서 실제 처리하는 catch는 통과 — exit=0
PASS: 깨진 Python 문법은 합격이 아니라 NOT_RUN — exit=2
PASS: 닫히지 않은 TypeScript 블록은 합격이 아니라 NOT_RUN — exit=2
PASS: CI P3 독립 작업은 P1 성적과 무관하게 본체+회귀시험을 실행 — 독립 job+두 명령 정적 배선
PASS: 실제 hooks/pre-commit 배선(위반 스테이지 → BLOCKED) — exit=1
PASS: 실제 hooks/pre-commit 배선(정상 파일 → 통과) — exit=0
PASS: 검사기 자체 무력화 공격(같은 커밋에서 정규식 무력화+위반) → BLOCKED — exit=1
PASS: 검사기 무해한 자기개선 커밋은 통과(벽이 아니라 게이트) — exit=0
PASS: 원본 worktree 상태 기준선 보존 — before/after 동일 여부=0
CHECKED: 29
```

→ 뭘 시켰나: 구현 전 12개가 실패했던 같은 원명령을 수정 후 다시 실행했다. / 뭐가 나왔나: 29개 전부 통과했고, 위반 fixture 내부의 exit 1·검사 불가 fixture의 exit 2는 시험이 기대한 차단 성적이다. / 좋은 소식인가 나쁜 소식인가: 원래 검증 명령의 성공 계약을 충족했으므로 좋은 소식이다.

## 13. Codex(V2) 독립 재공격과 수정 후 증거

Claude의 핵심 결함을 코드 설명만 믿지 않고 먼저 새 fixture로 재현했다. 수정 전 확정본에서 처리 코드가 있는 바깥 `catch` 안에 `catch{return null}`, 빈 `catch`, `|| []`, `??` 네 가지를 동시에 넣자 검사기는 exit 0, 각 위반 마커는 모두 0건이었다. 이 RED를 커밋 `79c3ee9`로 고정한 뒤 `js_findings`가 바깥 catch 끝으로 건너뛰던 한 줄을 제거했다.

Claude가 별도 참고로 남긴 `??=`도 다시 공격했다. 같은 의미의 `||= []`와 함께 넣자 수정 전 exit 0, 두 마커 모두 0건이어서 실제 빈틈으로 확인했다. 이를 각각 `??`, `|| []`와 같은 판정으로 묶었다. Claude가 합격시킨 정규식/나눗셈 구분, CRLF, 유니코드, 공백 파일명에 더해 TSX 제네릭 화살표도 별도 회귀로 추가했다.

| Claude 주장 | Codex 독립 결과 | 조치 |
|---|---|---|
| 처리 중인 바깥 catch 내부를 전부 건너뜀 | 일치 — 네 위반 모두 exit 0·마커 0건 재현 | 내부 토큰 끝까지 순회 + 직접 검사·실제 훅 시험 추가 |
| Python AST·문자/주석/템플릿/JSX 대조군은 정상 | 일치 — 기존 대조군과 추가 TSX/정규식/CRLF 대조군 통과 | 회귀 유지 |
| 0건·깨진 문법은 NOT_RUN | 일치 — exit 2 재확인 | 변경 없음 |
| P3 서버 작업은 P1과 독립 | 정적 배선 일치, 원격 실제 로그는 아직 미확인 | push 후 원격 로그로 최종 확인 |
| `??=`는 AC 밖 참고 결함 | 기술 사실은 일치하나 P3의 '?? 기본값 금지' 취지에는 포함된다고 재판정 | `??=`와 `||= []`도 차단 |
| 훅·시험·workflow 자체를 모두 바꾸는 공격은 저장소 신뢰경계 | 일치 — 저장소 내부 코드만으로 악의적 변경 권한 자체를 없앨 수 없음 | 브랜치 보호 실측 후 PR 위험으로 명시 |

수정 후 원명령과 전체 출력:

```bash
bash scripts/acceptance-silent-failure-lint-mutations.sh
```

```text
PASS: 정상 Python 파일 — 위반 없음 — exit=0
PASS: bare except 주입 — exit=1 + bare-except 마커 — exit=1
PASS: bare/empty catch 주입 — exit=1 + bare-catch 마커 — exit=1
PASS: catch{return null} 주입 — exit=1 + catch-return-null 마커 — exit=1
PASS: || [] 주입 — exit=1 + or-empty-array-fallback 마커 — exit=1
PASS: ?? 주입 — exit=1 + nullish-coalescing-fallback 마커 — exit=1
PASS: 존재하지 않는 파일 지정 — 0건 스캔은 통과가 아니라 NOT_RUN(exit 2) — exit=2
PASS: 정상 fixture 재확인(회귀 없음) — exit=0
PASS: Python 한 줄 handler bare except → BLOCKED — exit=1
PASS: Python 줄연결 bare except → BLOCKED — exit=1
PASS: Python 독스트링 안 except:는 실행 코드가 아니므로 통과 — exit=0
PASS: JavaScript 여러 줄 빈 catch → BLOCKED — exit=1
PASS: JavaScript 주석만 든 catch → BLOCKED — exit=1
PASS: JavaScript catch·매개변수·블록 줄분리 → BLOCKED — exit=1
PASS: TypeScript 여러 줄 catch return null → BLOCKED — exit=1
PASS: JavaScript 괄호로 감싼 catch return null → BLOCKED — exit=1
PASS: JavaScript 줄바꿈·내부공백·주석 || [] 3종 → 모두 BLOCKED — exit=1, hits=3/3
PASS: JavaScript 문자열·템플릿·주석·정규식과 실제 처리 catch는 통과 — exit=0
PASS: 템플릿 본문은 무시하고 보간식 안 ??만 BLOCKED — exit=1, hits=1/1
PASS: JSX 본문은 무시하고 중괄호 실행식 안 ??만 BLOCKED — exit=1, nullish=1/1, other=0/0
PASS: TSX 제네릭 화살표 뒤 실제 ??는 BLOCKED — exit=1, nullish=1/1
PASS: 정규식·나눗셈은 보존하고 실제 || []만 BLOCKED — exit=1, array=1/1, other=0/0
PASS: CRLF·유니코드·공백 파일명은 실제 빈 catch만 BLOCKED — exit=1, bare-catch=1/1, other=0/0
PASS: ??= 기본값·||= [] 복합 대입도 BLOCKED — exit=1, nullish=1/1, array=1/1
PASS: 중첩 블록에서 실제 처리하는 catch는 통과 — exit=0
PASS: 처리 중인 바깥 catch 안의 네 위반도 모두 BLOCKED — exit=1, catch-null=1/1, bare-catch=1/1, array=1/1, nullish=1/1
PASS: 깨진 Python 문법은 합격이 아니라 NOT_RUN — exit=2
PASS: 닫히지 않은 TypeScript 블록은 합격이 아니라 NOT_RUN — exit=2
PASS: CI P3 독립 작업은 P1 성적과 무관하게 본체+회귀시험을 실행 — 독립 job+두 명령 정적 배선
PASS: 실제 hooks/pre-commit 배선(위반 스테이지 → BLOCKED) — exit=1
PASS: 실제 hooks/pre-commit 배선(정상 파일 → 통과) — exit=0
PASS: 실제 hooks/pre-commit 배선(바깥 catch 안 네 위반 → BLOCKED) — exit=1
PASS: 검사기 자체 무력화 공격(같은 커밋에서 정규식 무력화+위반) → BLOCKED — exit=1
PASS: 검사기 무해한 자기개선 커밋은 통과(벽이 아니라 게이트) — exit=0
PASS: 원본 worktree 상태 기준선 보존 — before/after 동일 여부=0
CHECKED: 35
```

→ 뭘 시켰나: Claude가 뚫은 중첩 경로를 직접 검사와 실제 pre-commit 두 곳에서 다시 공격하고, 추가 문법 반례·정상 대조군·자기무력화·작업공간 보존까지 한 명령으로 실행했다. / 뭐가 나왔나: 35개 모두 PASS, 전체 명령 exit 0이며 중첩 네 위반은 각 1건, 실제 훅은 exit 1로 차단했다. / 좋은 소식인가 나쁜 소식인가: 로컬 수정에는 좋은 소식이지만 원격 서버 로그와 전체 저장소 게이트가 남아 있어 아직 최종 완료는 아니다.
