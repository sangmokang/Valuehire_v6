# 시작 검사 임시 객체 판정 수리 goal (2026-08-17)

## 1층 — 결론

현재 새 기능을 시작할 수 없습니다. 비밀값 검사는 정상이지만, 이미 지워진 무해한 작업 흔적 27개를
전부 위험으로 잘못 세어 시작 검사가 멈춥니다.

이번 작업은 흔적의 개수가 아니라 그 안에 실제 금지값이 있는지를 검사하도록 바꿉니다. 실제 금지값이
남으면 계속 막고, 저장소 정리를 끝낸 직후에는 흔적이 하나도 없어야 한다는 기존 기준도 유지합니다.

사장님이 지금 추가로 정하실 것은 없습니다. 실제 기록 삭제, HumanSearch 기능 구현, 실제 사이트 접근,
합치기와 배포는 하지 않고 변경 요청 검토 직전에 멈춥니다.

첫 외부 검토에서 큰 기록 조각과 읽기 오류를 놓치는 두 결함이 추가로 드러났고, 실패 시험부터 다시
만들어 둘 다 수리했습니다. 현재도 사용 중인 기록의 설명문·파일 이름을 검사하지 않는 기존 구멍은
이번 수리가 만든 문제가 아니어서 별도 이슈 #22로 분리했습니다. 서버 검사 결과와 책임자 승인은 아직
남았고, 전용 자동화 설정 검사 도구는 이 환경에 없어 실행하지 못했습니다.

첫 일반 push는 새 합성 시험이 훅의 저장소 위치를 물려받아 실제 작업 브랜치에 가짜 커밋을 만드는
문제까지 찾아 차단됐습니다. 원격에는 아무것도 올라가지 않았고, 가짜 커밋은 역사에서 제거했습니다.
같은 훅 환경을 합성 바깥 저장소로 재현하는 여섯 번째 실패 시험과 환경 격리 수리를 추가했습니다.

## 2층 — 판단 근거

시작 검사 19개 중 실패한 것은 하나뿐입니다. 추적 파일과 현재 기록에서 금지값을 찾는 검사는
통과했지만, 내용과 무관하게 임시 기록 조각이 하나라도 있으면 실패시키는 조건이 27개를 세었습니다.

임시 기록 조각은 실패한 커밋 시도나 작업 중 되돌림만으로도 생깁니다. 이를 매번 0개로 만들려면
복구 가능한 작업 흔적을 강제로 지워야 하므로 일반적인 작업 시작 조건으로 부적절합니다. 반면 지운
비밀값이 그 조각 안에 남아 있으면 복원될 수 있으므로 내용 검사는 계속 필요합니다.

따라서 일반 실행에서는 모든 임시 기록 조각의 파일 내용을 열어 로컬 금지값이 있는지만 검사하고,
저장소 정리 완료를 확인하는 별도 실행에서만 조각 수 0개를 요구합니다. 이 구분은 기존 스크립트의
정리 완료 전용 구간과 같은 경계를 따릅니다.

### 결정 카드

**무엇을** — 일반 시작 검사에서는 임시 기록의 개수 대신 그 안의 실제 금지값을 검사합니다.

**왜** — 무해한 개발 흔적은 허용하면서, 지운 뒤 남은 비밀값은 계속 차단해야 하기 때문입니다.

**버린 길** — 모든 임시 기록을 강제로 삭제하는 방법은 다른 작업의 복구 가능성을 없애므로 버렸습니다.
검사 목록에서 해당 검사를 통째로 빼는 방법도 실제 비밀값을 놓치므로 버렸습니다.

**대가** — 일반 시작 검사가 임시 파일 조각의 내용을 추가로 열기 때문에 실행 시간이 조금 늘어납니다.

**되돌리기** — 변경 커밋을 되돌리면 기존 개수 판정으로 돌아갑니다. 비용은 다시 모든 임시 기록을
삭제해야 시작할 수 있다는 운영 중단입니다.

## 3층 — 계약과 증거

### 1. 현재 상태

실행 위치는 기준 브랜치와 같은 `task/gate0-unreachable-secret-scan` 작업 공간이며, GitHub 이슈는
[#19](https://github.com/sangmokang/Valuehire_v6/issues/19)입니다.

```text
$ bash scripts/session-status.sh
HEAD: 4fdef31 (synced)
ORIGIN: 4fdef31
RED: 1/19 (acceptance-0-7.sh 제외 — CI 담당)
```

→ 무엇을 시켰나: 현재 저장소에서 시작 자격 검사 전체를 실행했습니다.
→ 뭐가 나왔나: 기준 브랜치와 원격은 같지만 19개 중 1개가 실패했습니다.
→ 좋은 소식인가 나쁜 소식인가: 새 기능 착수는 막아야 하므로 현재는 나쁜 소식입니다.

```text
$ SECRET_PATTERNS_FILE= bash scripts/acceptance-0-2.sh
PASS: no secret-pattern match in any tracked file, .env not tracked
FAIL: unreachable 객체 27건 잔존 (reflog expire/gc --prune=now 미완)
```

→ 무엇을 시켰나: 실패한 검사 하나를 분리해 원문 출력을 확인했습니다.
→ 뭐가 나왔나: 현재 파일의 금지값 검사는 통과했고, 내용이 아닌 임시 객체 27개 때문에 실패했습니다.
→ 좋은 소식인가 나쁜 소식인가: 비밀 노출 증거는 없지만 일상 작업이 영구 차단되는 잘못된 판정입니다.

`scripts/acceptance-0-2.sh:101-106`은 모든 unreachable 객체(= 현재 브랜치나 기록에서 더는 가리키지
않지만 저장소 내부에 남아 복구 가능한 객체)의 개수가 0인지 검사합니다. 이 줄이 현재 실패의 직접
원인입니다.

`scripts/acceptance-0-2.sh:108-117`은 현재 브랜치와 되돌림 기록이 가리키는 모든 파일 내용을 실제
로컬 금지값과 대조합니다. 현재 상시 내용 검사의 기존 경계입니다.

`scripts/acceptance-0-2.sh:119-153`은 저장소 정리 직후에만 요구되는 검사들을
`ACCEPTANCE_ENDSTATE=1`일 때로 제한합니다. 임시 객체 0개 조건도 이 경계와 같은 성질입니다.

`scripts/session-status.sh:42-64`는 작업 시작 때 `acceptance-0-2.sh`를 포함한 인수 검사를 전부
실행합니다. 따라서 일회성 정리 조건이 상시 실패하면 모든 후속 작업이 멈춥니다.

### 2. 근본 원인

한 스크립트가 두 목적을 섞었습니다.

- 상시 목적: 현재 파일, 현재 기록, 복구 가능한 임시 파일 조각 어디에도 실제 로컬 금지값이 없어야 함.
- 일회성 목적: 비밀 이력 정리를 끝낸 바로 그 시점에는 임시 객체 자체가 0개여야 함.

상시 실행 경로가 일회성 목적의 `unreachable 객체 수 == 0` 단언까지 실행해, 이후 정상 개발이 만든
무해한 객체도 모두 보안 실패로 오판합니다.

### 3. 단일 인수 기준

**AC-19.** 합성 저장소에 무해한 unreachable blob(= 현재 브랜치에서 가리키지 않는 파일 조각)만 있을
때 `scripts/acceptance-0-2.sh` 일반 실행은 종료 성적 0이어야 합니다. 같은 blob에 로컬 금지값이 있거나
unreachable 객체 읽기 자체가 실패하거나, 50MiB 큰 blob의 앞쪽에 금지값이 있으면 일반 실행은 0이
아닌 성적이어야 합니다. 무해한 blob이라도 `ACCEPTANCE_ENDSTATE=1` 실행은 0이 아닌 성적이어야 합니다.
Git 훅 환경에서도 합성 시험이 바깥 저장소의 HEAD·파일 상태를 바꾸지 않아야 합니다. 이 여섯 경우를
검사하는 인수 스크립트는 로컬 push 검사와 서버 자동 검사에서 모두 실행되어야 합니다.

#### 가짜 합격을 막는 반대 사례

- 모든 unreachable 객체를 허용해 지운 비밀값까지 놓치면 실패입니다.
- 객체를 읽거나 내용을 대조하는 도구가 실패했는데 통과하면 실패입니다.
- 큰 binary 객체의 앞쪽에서 값을 찾은 뒤 파이프가 먼저 닫혀 통과하면 실패입니다.
- 무해한 unreachable 객체 하나만 있어도 일반 시작 검사가 실패하면 실패입니다.
- 정리 완료 실행이 unreachable 객체 0개를 요구하지 않으면 실패입니다.
- 새 인수 스크립트가 로컬에서만 돌고 서버 자동 검사에 연결되지 않으면 실패입니다.
- 합성 시험이 실제 대상 스크립트를 복사해 실행하지 않고 문자열만 검사하면 실패입니다.

### 4. Harness 게이트

- Gate 0: `RED: 1/19`; 이 작업이 닫아야 할 선행 실패로 확인했습니다.
- Gate 1: GitHub 이슈 #19, 단일 인수 기준 AC-19를 만들었습니다.
- Gate 2: `worktrees/gate0-unreachable-secret-scan`, `task/gate0-unreachable-secret-scan`으로 격리했습니다.
- Gate 3 RED: 최초 세 사례와 적대검증 추가 두 사례, 훅 환경 무오염 한 사례를 각각 코드보다 먼저 실패로 고정합니다.
- Gate 3 GREEN: RED 시험을 바꾸지 않고 대상 판정기와 필요한 서버 연결만 최소 수정합니다.
- Gate 4: 대상 시험, 시작 검사, 비밀 스캔, 문서·장치 대조, 셸 문법, 변조 시험을 실행합니다.
- Gate 4.5: Claude가 1차로 공격하고 Codex가 모든 증거를 직접 재현합니다.
- Gate 5: 일반 push와 한국어 PR까지만 수행하고 서버 결과를 같은 커밋인지 확인합니다.
- Gate 6: merge, branch 삭제, 배포는 사장님 승인 전 실행하지 않습니다.

### 5. 적대검증 항목

1. 관련 없는 unreachable 객체를 허용한다는 명목으로 실제 비밀값까지 놓치는가.
2. blob 외 commit·tree·tag 안의 금지값을 놓치는가.
3. 알려진 과거 오염 객체의 고정 SHA 검사가 그대로 유지되는가.
4. refs와 reflog가 가리키는 현재 내용 전수 검사가 그대로 유지되는가.
5. `ACCEPTANCE_ENDSTATE=1`에서 unreachable 객체 0개 요구가 실제로 남는가.
6. RED 시험이 GREEN 단계에서 약해지거나 기대값이 바뀌는가.
7. 새 인수 검사가 로컬 push와 서버 자동 검사 중 한쪽에만 연결되는가.
8. 시험이 원본 저장소 객체를 만들거나 지우는가.
9. 출력에 실제 로컬 금지값이 노출되는가.
10. `session-status.sh`가 최종적으로 `RED: 0/N`을 만드는가.
11. `git cat-file` 또는 `grep` 실패가 값 없음과 같은 통과로 처리되는가.
12. 큰 binary 객체 앞부분의 값이 `grep -q` 조기 종료와 `pipefail` 조합 때문에 누락되는가.

### 6. SOT 체크리스트

- [x] `docs/sot/INDEX.md` — 영구 규칙과 사건 기록의 경계를 읽었습니다.
- [x] `docs/sot/coding-principles.md` — P2, P3, P12, P13, P15, P20, P22와 V-1~V-5를 읽었습니다.
- [x] `docs/sot/git-workflow.md` — 한 작업=한 worktree=한 branch=한 인수 기준, 자동 merge 금지를 읽었습니다.
- [x] `docs/sot/hook-contracts.md` — 시작 검사와 push 검사의 입력·출력 계약을 읽었습니다.
- [x] `docs/sot/verification-commands.md` — 이 저장소가 make/npm 저장소가 아니며 실제 명령이 bash임을 읽었습니다.
- [x] 사용자 제공 `AGENTS.md` — Lore commit, 증거 우선, 자동 merge 금지를 적용합니다.

### 7. 비범위

- `git gc`, `reflog expire` 또는 다른 작업의 객체 삭제
- `.secret-patterns` 실제 내용 변경·출력·추적
- HumanSearch 인증 화면 분류기 구현
- PR #13, #14, #15 merge
- 실제 포털, 브라우저, 로그인, 세션, 자격증명, 후보자 개인정보
- main 직접 push, 자동 merge, 배포, 메일·후보 발송

### 8. 실행·검증 로그

#### 8-1. RED — 구현 전 실패 고정

```text
$ bash scripts/acceptance-0-2-unreachable-content.sh
[1/3] 일반 실행은 무해한 unreachable blob을 허용 -> UNEXPECTED (exit=1, expected=pass)
PASS: no secret-pattern match in any tracked file, .env not tracked
FAIL: unreachable 객체 1건 잔존 (reflog expire/gc --prune=now 미완)
[2/3] 일반 실행은 금지값이 든 unreachable blob을 차단 -> BLOCKED (exit=1)
[3/3] 종료상태 실행은 무해한 unreachable blob도 차단 -> BLOCKED (exit=1)
CHECKED: 3
FAIL: AC-19 예상과 다른 사례 1건
red_rc=1
```

→ 무엇을 시켰나: 실제 대상 스크립트를 합성 저장소 세 개에서 실행하는 시험만 먼저 만들었습니다.
→ 뭐가 나왔나: 기존 코드는 무해한 객체도 차단해 첫 사례가 실패했습니다.
→ 좋은 소식인가 나쁜 소식인가: 구현 전에는 의도대로 RED이며, 시험이 기존 동작과 새 계약을 구분합니다.

첫 커밋 시도는 시험 변수 이름에 비밀처럼 보이는 단어가 들어가 pre-commit에서 차단됐습니다. 실제 값은
아니었지만 이름을 `CANARY`와 `tainted`로 바꾼 뒤 다시 같은 RED를 확인해 시험 커밋
`c7f2dcf`로 고정했습니다.

```text
$ git diff --exit-code c7f2dcf -- scripts/acceptance-0-2-unreachable-content.sh
red_test_unchanged_rc=0
```

→ 무엇을 시켰나: GREEN 뒤 시험 파일이 RED 커밋과 같은지 Git으로 대조했습니다.
→ 뭐가 나왔나: 차이가 0건입니다.
→ 좋은 소식인가 나쁜 소식인가: 기대값을 바꿔 가짜 GREEN을 만들지 않았으므로 좋은 소식입니다.

#### 8-2. GREEN — 최소 구현

```text
$ bash scripts/acceptance-0-2-unreachable-content.sh
[1/3] 일반 실행은 무해한 unreachable blob을 허용 -> PASS (exit=0)
[2/3] 일반 실행은 금지값이 든 unreachable blob을 차단 -> BLOCKED (exit=1)
[3/3] 종료상태 실행은 무해한 unreachable blob도 차단 -> BLOCKED (exit=1)
CHECKED: 3
PASS: AC-19 일반 내용 검사와 종료상태 0건 조건 분리
targeted_rc=0
```

→ 무엇을 시켰나: RED 시험을 바꾸지 않고 수정한 판정기를 다시 실행했습니다.
→ 뭐가 나왔나: 일반 실행의 무해한 객체만 허용되고 나머지 두 위험·종료상태 사례는 차단됐습니다.
→ 좋은 소식인가 나쁜 소식인가: AC-19의 세 문장을 각각 실행으로 증명했으므로 좋은 소식입니다.

```text
$ SECRET_PATTERNS_FILE= bash scripts/acceptance-0-2.sh
PASS: no secret-pattern match in any tracked file, .env not tracked
PASS: 0-2 — 히스토리·객체·reflog·docs 리터럴 0건, 스캐너 뮤테이션 검출 확인
acceptance_rc=0
```

→ 무엇을 시켰나: 합성 값이 아니라 현재 저장소의 로컬 패턴 파일을 사용해 0-2 전체를 실행했습니다.
→ 뭐가 나왔나: 실제 패턴은 출력하지 않은 채 현재 파일·기록·객체 검사가 통과했습니다.
→ 좋은 소식인가 나쁜 소식인가: 기존 27개 무해한 객체 때문에 막히던 시작 조건이 내용 검사로 통과해 좋은 소식입니다.

#### 8-3. 전체 Gate 0와 관련 검사

GREEN 직후 첫 묶음 실행은 아래처럼 1건을 보고했습니다.

```text
$ bash scripts/session-status.sh
HEAD: 8402572 (ahead 3 / behind 0)
ORIGIN: 4fdef31
RED: 1/20 (acceptance-0-7.sh 제외 — CI 담당)
```

→ 무엇을 시켰나: 새 인수 시험을 포함한 시작 검사 전체를 묶음으로 실행했습니다.
→ 뭐가 나왔나: 대상 이름을 숨기는 요약에서 20개 중 1개가 실패했습니다.
→ 좋은 소식인가 나쁜 소식인가: 한 번이라도 흔들린 것은 나쁜 소식이라 성공으로 세지 않고 전부 분리했습니다.

```text
$ for each Gate-0 check; do SECRET_PATTERNS_FILE= bash "$check"; done
PASS ./scripts/acceptance-0-2-unreachable-content.sh
PASS ./scripts/acceptance-0-2.sh
PASS ./scripts/acceptance-0-5.sh
PASS ./scripts/acceptance-0-6.sh
PASS ./scripts/acceptance-hs-a3.sh
PASS ./scripts/acceptance-hs-a4.sh
PASS ./scripts/acceptance-hs-cleanroom-absolute-contexts.sh
PASS ./scripts/acceptance-hs-cleanroom-absolute-paths.sh
PASS ./scripts/acceptance-hs-cleanroom-colon-paths.sh
PASS ./scripts/acceptance-hs-cleanroom-file-urls.sh
PASS ./scripts/acceptance-hs-cleanroom-hook-env-mutations.sh
PASS ./scripts/acceptance-hs-cleanroom-hook-env.sh
PASS ./scripts/acceptance-hs-cleanroom-mutations.sh
PASS ./scripts/acceptance-hs-cleanroom.sh
PASS ./scripts/acceptance-hs-gates-antiforge.sh
PASS ./scripts/acceptance-hs-gates-mutations.sh
PASS ./scripts/acceptance-hs-gates.sh
PASS ./scripts/acceptance-secret-webhook-vendor.sh
PASS ./scripts/acceptance-verify-ac-m.sh
PASS ./verify.sh
```

→ 무엇을 시켰나: 묶음과 같은 20개를 같은 순서·환경으로 하나씩 실행하고 각 이름을 드러냈습니다.
→ 뭐가 나왔나: 20개가 모두 통과해 첫 실패는 재현되지 않았습니다.
→ 좋은 소식인가 나쁜 소식인가: 현재 실패 검사는 없지만 첫 흔들림은 PR의 잔여 위험으로 공개해야 합니다.

```text
$ bash scripts/session-status.sh
HEAD: 8402572 (ahead 3 / behind 0)
ORIGIN: 4fdef31
RED: 0/20 (acceptance-0-7.sh 제외 — CI 담당)
```

→ 무엇을 시켰나: 분리 실행 뒤 동일한 묶음 검사를 다시 실행했습니다.
→ 뭐가 나왔나: 시작 검사가 0/20으로 통과했습니다.
→ 좋은 소식인가 나쁜 소식인가: 현재 Gate 0는 GREEN이지만, 서버 CI와 추가 반복 전까지 완료 판정은 보류합니다.

```text
$ bash verify.sh
PASS: no secret-pattern match in any tracked file, .env not tracked
$ bash scripts/check-docs-sot.sh
OK: docs/sot 재구성 AC 전부 충족
$ bash scripts/verify/check-mechanism-registry.sh
CHECKED: 3
$ bash scripts/acceptance-verify-ac-m.sh
CHECKED: 25
$ git ls-files '*.sh' | while read f; do bash -n "$f"; done
exit=0
$ actionlint .github/workflows/verify.yml
NOT_RUN: actionlint unavailable
```

→ 무엇을 시켰나: 비밀 스캔, SOT 참조, 검사 장치 명부, 명부 변조 25종, 모든 셸 문법과 워크플로 정적 검사를 확인했습니다.
→ 뭐가 나왔나: 설치된 검사들은 모두 통과했고 `actionlint`만 환경에 없어 실행하지 못했습니다.
→ 좋은 소식인가 나쁜 소식인가: 저장소 자체 검사 결과는 좋지만 워크플로 전용 정적 도구 미실행은 공개할 검증 공백입니다.

```text
$ bash scripts/acceptance-0-7.sh
[1/6] 검사기 자기 제외 → BLOCKED (훅ON=1 · 훅OFF=0) ✓ 훅이 원인
[2/6] 검사 약화(실패 무시) → BLOCKED (훅ON=1 · 훅OFF=0) ✓ 훅이 원인
[3/6] 만료일 없는 억제 → BLOCKED (훅ON=1 · 훅OFF=0) ✓ 훅이 원인
[4/6] LLM 출력→판정 필드 → BLOCKED (훅ON=1 · 훅OFF=0) ✓ 훅이 원인
[5/6] 미커밋 상태로 push → BLOCKED (훅ON=1 · 훅OFF=0) ✓ 훅이 원인
[6/6] 가짜 외부효과 모듈 → BLOCKED (훅ON=1 · 훅OFF=0) ✓ 훅이 원인
OK: 원본 저장소 무변경 확인 (da39a3ee5e6b4b0d3255bfef95601890afd80709)
PASS: 위반 6 종이 전부 차단됨 (각 건 훅 OFF 대조 통과)
```

→ 무엇을 시켰나: 시작 검사에서 비용 때문에 제외하는 CI 전용 훅 시연도 별도로 실행했습니다.
→ 뭐가 나왔나: 위반 6종은 훅이 켜졌을 때만 전부 차단됐고 원본 저장소는 변하지 않았습니다.
→ 좋은 소식인가 나쁜 소식인가: 로컬에서 CI 전용 방어까지 통과했으므로 좋은 소식입니다.

#### 8-4. 뮤테이션 — 시험이 구현 약화를 잡는지 확인

대상 코드의 내용 비교만 임시 문자열로 바꿔 실제 금지값을 놓치도록 만든 뒤 시험했습니다.

```text
$ bash scripts/acceptance-0-2-unreachable-content.sh
[1/3] 일반 실행은 무해한 unreachable blob을 허용 -> PASS (exit=0)
[2/3] 일반 실행은 금지값이 든 unreachable blob을 차단 -> UNEXPECTED (exit=0, expected=blocked)
PASS: no secret-pattern match in any tracked file, .env not tracked
PASS: 0-2 — 히스토리·객체·reflog·docs 리터럴 0건, 스캐너 뮤테이션 검출 확인
[3/3] 종료상태 실행은 무해한 unreachable blob도 차단 -> BLOCKED (exit=1)
CHECKED: 3
FAIL: AC-19 예상과 다른 사례 1건
mutation_rc=1
```

→ 무엇을 시켰나: 구현의 핵심 비교를 고의로 무력화하고 RED 시험을 그대로 실행했습니다.
→ 뭐가 나왔나: 위험 객체를 놓친 두 번째 사례가 `UNEXPECTED`로 실패했습니다.
→ 좋은 소식인가 나쁜 소식인가: 시험이 실제 구현 약화를 잡으므로 좋은 소식입니다.

```text
$ git diff --exit-code HEAD -- scripts/acceptance-0-2.sh
implementation_restored=YES
$ git diff --exit-code c7f2dcf -- scripts/acceptance-0-2-unreachable-content.sh
red_test_unchanged=YES
$ bash scripts/acceptance-0-2-unreachable-content.sh
PASS: AC-19 일반 내용 검사와 종료상태 0건 조건 분리
```

→ 무엇을 시켰나: 임시 약화를 정확히 복구하고 구현은 HEAD, 시험은 RED 커밋과 대조한 뒤 재실행했습니다.
→ 뭐가 나왔나: 구현·시험 모두 원래 바이트와 같고 세 사례가 다시 통과했습니다.
→ 좋은 소식인가 나쁜 소식인가: 뮤테이션 흔적이 남지 않았으므로 좋은 소식입니다.

#### 8-5. V1/V2가 찾은 추가 RED와 GREEN

첫 Claude V1은 새 코드의 객체 읽기 실패를 조용히 통과시키는 중간 결함을 찾았습니다. Codex V2는 이를
재현했고, Claude가 안전하다고 본 큰 객체 파이프는 반대로 5회 모두 값을 놓치는 것도 재현했습니다.

```text
$ bash /tmp/codex-v2-gate0-probe.sh <worktree>
CASE reachable_commit_message rc=0 result=MISSED
CASE unreachable_commit_message rc=1 result=BLOCKED
CASE cat_file_failure rc=0 result=SILENT_PASS
CASE large_blob_run_1 rc=0 result=MISSED
CASE large_blob_run_2 rc=0 result=MISSED
CASE large_blob_run_3 rc=0 result=MISSED
CASE large_blob_run_4 rc=0 result=MISSED
CASE large_blob_run_5 rc=0 result=MISSED
```

→ 무엇을 시켰나: 합성 저장소에서 현재 커밋 설명문, 지운 커밋 설명문, 강제 객체 읽기 실패, 50MiB 객체 앞쪽 값을 각각 실행했습니다.
→ 뭐가 나왔나: 범위 안 읽기 실패와 큰 객체가 통과했고, 범위 밖 현재 커밋 설명문 누락도 재현됐습니다.
→ 좋은 소식인가 나쁜 소식인가: 첫 GREEN이 불완전했다는 나쁜 소식이어서, 별도 RED 없이는 수정하지 않았습니다.

현재 커밋 설명문·tree 경로·tag를 놓치는 문제는 `origin/main`에도 있던 기존 reachable 경계이며 AC-19가
수리하는 unreachable 개수/내용 경계와 다릅니다. 이를 숨기거나 범위를 조용히 넓히지 않고 GitHub
[#22](https://github.com/sangmokang/Valuehire_v6/issues/22)로 분리했습니다.

```text
$ bash scripts/acceptance-0-2-unreachable-content.sh  # d409c34 RED
[1/5] 일반 실행은 무해한 unreachable blob을 허용 -> PASS (exit=0)
[2/5] 일반 실행은 금지값이 든 unreachable blob을 차단 -> BLOCKED (exit=1)
[3/5] unreachable 객체 읽기 실패는 조용히 통과하지 않음 -> UNEXPECTED (exit=0, expected=blocked)
[4/5] 큰 unreachable blob 앞쪽의 금지값도 차단 -> UNEXPECTED (exit=0, expected=blocked)
[5/5] 종료상태 실행은 무해한 unreachable blob도 차단 -> BLOCKED (exit=1)
CHECKED: 5
FAIL: AC-19 예상과 다른 사례 2건
adversarial_red_rc=1
```

→ 무엇을 시켰나: V1/V2가 찾은 범위 안 두 결함을 기존 세 사례에 추가한 시험만 먼저 실행했습니다.
→ 뭐가 나왔나: 읽기 실패와 큰 객체 두 사례가 정확히 RED였습니다.
→ 좋은 소식인가 나쁜 소식인가: 결함이 실행으로 고정됐으므로 이후 코드만 바꿔야 하는 올바른 RED입니다.

```text
$ bash scripts/acceptance-0-2-unreachable-content.sh  # 4e4dac1 GREEN
[1/5] 일반 실행은 무해한 unreachable blob을 허용 -> PASS (exit=0)
[2/5] 일반 실행은 금지값이 든 unreachable blob을 차단 -> BLOCKED (exit=1)
[3/5] unreachable 객체 읽기 실패는 조용히 통과하지 않음 -> BLOCKED (exit=1)
[4/5] 큰 unreachable blob 앞쪽의 금지값도 차단 -> BLOCKED (exit=1)
[5/5] 종료상태 실행은 무해한 unreachable blob도 차단 -> BLOCKED (exit=1)
CHECKED: 5
PASS: AC-19 일반 내용 검사와 종료상태 0건 조건 분리
$ git diff --exit-code d409c34 4e4dac1 -- scripts/acceptance-0-2-unreachable-content.sh
exit=0
$ git diff --name-status d409c34 4e4dac1
M scripts/acceptance-0-2.sh
```

→ 무엇을 시켰나: 같은 RED 시험을 수정 뒤 실행하고 두 커밋 사이 시험 불변과 변경 파일을 대조했습니다.
→ 뭐가 나왔나: 5/5 통과했고 GREEN 커밋은 대상 코드만 바꿨습니다.
→ 좋은 소식인가 나쁜 소식인가: 시험 기대값을 낮추지 않은 진짜 GREEN이라 좋은 소식입니다.

#### 8-6. 최종 뮤테이션

```text
$ 대상의 실제 값 비교를 임시 문자열로 교체
$ bash scripts/acceptance-0-2-unreachable-content.sh
[1/5] 일반 실행은 무해한 unreachable blob을 허용 -> PASS (exit=0)
[2/5] 일반 실행은 금지값이 든 unreachable blob을 차단 -> UNEXPECTED (exit=0, expected=blocked)
[3/5] unreachable 객체 읽기 실패는 조용히 통과하지 않음 -> BLOCKED (exit=1)
[4/5] 큰 unreachable blob 앞쪽의 금지값도 차단 -> UNEXPECTED (exit=0, expected=blocked)
[5/5] 종료상태 실행은 무해한 unreachable blob도 차단 -> BLOCKED (exit=1)
CHECKED: 5
FAIL: AC-19 예상과 다른 사례 2건
final_mutation_rc=1
$ git diff --exit-code HEAD -- scripts/acceptance-0-2.sh
implementation_restored=YES
```

→ 무엇을 시켰나: 최종 코드의 값 비교를 다시 고의로 무력화하고 시험한 뒤 정확히 원복했습니다.
→ 뭐가 나왔나: 작은 값과 큰 값 두 사례가 모두 실패했고 원복 뒤 HEAD와 차이가 0건입니다.
→ 좋은 소식인가 나쁜 소식인가: 새 두 방어를 포함한 최종 시험이 실제 약화를 잡고 흔적도 남지 않아 좋은 소식입니다.

#### 8-7. 첫 일반 push가 찾은 Git 훅 환경 오염과 수리

```text
$ git push -u origin task/gate0-unreachable-secret-scan
pre-push: 검사 18개 실행
BLOCKED: ./scripts/acceptance-0-2-unreachable-content.sh exit=1
BLOCKED: ./scripts/acceptance-0-6.sh exit=1
BLOCKED: ./scripts/acceptance-hs-cleanroom.sh exit=2
BLOCKED: ./verify.sh exit=1
error: failed to push some refs
$ git log -1 --oneline
e794579 fixture
$ git status --short
 M .gitignore
 D docs/README.md
```

→ 무엇을 시켰나: 모든 로컬 검증 뒤 훅을 우회하지 않는 첫 일반 push를 실행하고 HEAD·파일 상태를 확인했습니다.
→ 뭐가 나왔나: push는 차단됐지만 새 합성 시험이 훅의 저장소 위치를 상속해 원본 브랜치에 fixture 커밋을 만들었습니다.
→ 좋은 소식인가 나쁜 소식인가: 원격 유출은 막혔지만 로컬 원본 오염은 심각한 나쁜 소식이어서 PR 진행을 중단했습니다.

직접 실행 때는 Git 저장소 위치 환경값이 없었지만 pre-push 자식은 연결 worktree의 절대 `GIT_DIR`을
상속했습니다. 합성 저장소의 `git -C`보다 이 환경값이 우선해 원본 index·branch를 사용한 것이
직접 원인입니다. 작업 파일 상태가 push 전 `a066daa`와 완전히 같음을 먼저 증명하고 임시 역변경
커밋으로 복구한 뒤, 원인 커밋과 복구 커밋은 최종 rebase에서 함께 제거했습니다.

```text
$ 합성 바깥 저장소에서 절대 GIT_DIR만 상속하고 기존 시험 실행  # 322d523 RED
[1/6] 일반 실행은 무해한 unreachable blob을 허용 -> PASS (exit=0)
[2/6] 일반 실행은 금지값이 든 unreachable blob을 차단 -> BLOCKED (exit=1)
[3/6] unreachable 객체 읽기 실패는 조용히 통과하지 않음 -> BLOCKED (exit=1)
[4/6] 큰 unreachable blob 앞쪽의 금지값도 차단 -> BLOCKED (exit=1)
[5/6] 종료상태 실행은 무해한 unreachable blob도 차단 -> BLOCKED (exit=1)
[6/6] Git hook 환경에서도 바깥 저장소 무오염 -> UNEXPECTED (exit=1, head_same=NO, status_same=NO)
CHECKED: 6
FAIL: AC-19 예상과 다른 사례 1건
hook_env_red_rc=1
real_worktree_unchanged=YES
```

→ 무엇을 시켰나: 실제 훅과 같은 절대 저장소 위치를 합성 바깥 저장소에만 주고 시험 자체의 오염을 관찰했습니다.
→ 뭐가 나왔나: 합성 바깥 저장소 HEAD와 파일 상태가 둘 다 바뀌어 여섯 번째 사례가 RED였고 실제 worktree는 그대로였습니다.
→ 좋은 소식인가 나쁜 소식인가: 위험을 원본이 아닌 합성 저장소에서 재현해 수리 기준을 고정한 올바른 RED입니다.

```text
$ ROOT 고정 직후 Git 로컬 환경값 7종 unset  # 56cc258 GREEN
$ bash scripts/acceptance-0-2-unreachable-content.sh
[1/6] 일반 실행은 무해한 unreachable blob을 허용 -> PASS (exit=0)
[2/6] 일반 실행은 금지값이 든 unreachable blob을 차단 -> BLOCKED (exit=1)
[3/6] unreachable 객체 읽기 실패는 조용히 통과하지 않음 -> BLOCKED (exit=1)
[4/6] 큰 unreachable blob 앞쪽의 금지값도 차단 -> BLOCKED (exit=1)
[5/6] 종료상태 실행은 무해한 unreachable blob도 차단 -> BLOCKED (exit=1)
[6/6] Git hook 환경에서도 바깥 저장소 무오염 -> PASS (exit=0)
CHECKED: 6
PASS: AC-19 일반 내용 검사와 종료상태 0건 조건 분리
hook_env_green_rc=0
real_repository_unchanged=YES
$ git rebase --onto a066daa 4f65be1 task/gate0-unreachable-secret-scan
Successfully rebased and updated refs/heads/task/gate0-unreachable-secret-scan.
```

→ 무엇을 시켰나: 실제 ROOT만 먼저 고정하고 Git 로컬 환경을 지운 뒤 같은 여섯 사례를 실행하고 무효 두 커밋을 역사에서 제거했습니다.
→ 뭐가 나왔나: 6/6 통과, 실제 HEAD·상태 불변, 최종 역사에는 Lore를 지키지 않은 fixture와 임시 복구 커밋이 없습니다.
→ 좋은 소식인가 나쁜 소식인가: 실제 pre-push가 찾은 원본 오염 경로를 회귀 시험으로 닫아 좋은 소식입니다.

### 9. 적대 검증 로그

#### 9-1. Claude V1 호출 이력

첫 `env -u ANTHROPIC_API_KEY claude -p` 호출은 코드 판정이 아니라 제공사 안전장치 오탐으로 응답 없이
끝났습니다. 엄격 스킬이 허용한 한 번의 재시도에서 모델과 합성 값 범위를 좁혀 실제 판정을 받았습니다.

```text
API Error: Fable 5's safeguards flagged this message.
Try rephrasing the request in a new session or change your model.
Request ID: req_011Ce7VZ1pwCDT1X6UN1QYh6
```

→ 무엇을 시켰나: 실제 값을 읽지 않는 읽기 전용 적대검증을 Claude에 요청했습니다.
→ 뭐가 나왔나: 첫 호출은 내용 판정 없이 제공사 안전장치가 거부했습니다.
→ 좋은 소식인가 나쁜 소식인가: 검증 증거가 아니므로 실패로 기록하고 한 번만 다시 실행했습니다.

재시도 명령은 `env -u ANTHROPIC_API_KEY claude -p --model sonnet`이며, 프롬프트 끝에는 strict §8-7
출력 형식 블록을 원문 그대로 붙였습니다. 검증자는 `VERDICT: FAIL`을 냈습니다.

```text
VERDICT: FAIL

1) AC-19의 원래 세 사례는 직접 재현해 모두 확인했습니다.
2) [HIGH] 현재 reachable commit 메시지의 금지값을 기존 전체 검사가 놓칩니다.
3) [MEDIUM] 신규 cat-file 조회 실패가 값 없음과 같은 통과로 처리됩니다.
4) 큰 50MiB 객체는 5회 모두 탐지됐다고 판정했습니다.
5) RED 시험 불변, 로컬·CI 배선, CI 17단계 일치를 확인했습니다.
6) actionlint는 설치되지 않아 실행하지 못했습니다.
```

→ 무엇을 시켰나: diff·goal·합성 저장소를 읽고 가짜 완료, 객체형, 오류 처리, 큰 객체, 배선을 공격하게 했습니다.
→ 뭐가 나왔나: 범위 안 중간 결함 1건, 기존 높은 결함 1건을 보고했고 큰 객체는 안전하다고 봤습니다.
→ 좋은 소식인가 나쁜 소식인가: PASS가 아니므로 구현을 멈추고 Codex V2로 모든 주장을 다시 재현했습니다.

#### 9-2. Codex V2 1차 재공격

| V1 주장 | Codex 재현 | 일치 여부 | 처리 |
|---|---|---|---|
| 기존 reachable commit 설명문 누락 | `rc=0`, MISSED | 일치 | 기존 결함 #22로 분리 |
| 신규 `cat-file` 실패 조용한 통과 | `rc=0`, SILENT_PASS | 일치 | d409c34 RED → 4e4dac1 GREEN |
| 50MiB 큰 객체 5회 탐지 | `rc=0`, MISSED 5/5 | **불일치** | V1 판정을 무효화하고 RED 추가 |
| RED 시험 불변 | diff exit 0 | 일치 | 유지 |
| 로컬·CI 배선과 17단계 | 각 1회·17개 | 일치 | 유지 |

→ 무엇을 시켰나: V1의 각 사실 주장을 독립 합성 저장소와 Git diff로 재실행했습니다.
→ 뭐가 나왔나: 두 주장은 일치했고, 큰 객체 안전 주장은 5/5 반대로 재현돼 틀렸습니다.
→ 좋은 소식인가 나쁜 소식인가: 다른 엔진의 PASS성 주장도 그대로 믿지 않고 실제 결함 하나를 더 찾았습니다.

Claude의 `pipefail` 설명은 “가장 오른쪽 명령의 결과가 이긴다”였지만 Bash의 `pipefail`은 가장 오른쪽의
**0이 아닌** 결과를 돌려줍니다. `grep -q`가 값을 찾고 먼저 닫히면 앞단 `git cat-file`이 SIGPIPE로
끝나 전체 조건이 거짓이 될 수 있으며, Codex 실측 5/5 누락이 그 결과입니다.

#### 9-3. 수정 후 Claude V1 재검토

수정 후 같은 출력 형식으로 `env -u ANTHROPIC_API_KEY claude -p --model sonnet --effort medium`을 실행했습니다.

```text
VERDICT: PASS

- d409c34에서 읽기 실패·50MiB 앞쪽 값 두 사례가 RED였음을 재현했습니다.
- 4e4dac1에서 시험 파일은 불변이고 대상 스크립트만 바뀌었음을 확인했습니다.
- 현재 5개 사례를 3회 실행해 매번 5/5 통과를 확인했습니다.
- 로컬 pre-push와 GitHub CI 배선을 확인했습니다.
- #22 reachable 경계는 기존 별도 위험으로 남겼습니다.
- actionlint는 설치되지 않아 실행하지 못했습니다.
- SOT가 아직 3개 사례라고 적은 낮은 문서 결함을 찾았습니다.
```

→ 무엇을 시켰나: 두 추가 커밋의 RED→GREEN, 5개 사례 반복, 종료값 분리, 배선을 재검토하게 했습니다.
→ 뭐가 나왔나: 범위 안 중간 이상 결함 0건으로 PASS했고 문서 숫자 1건을 찾았습니다.
→ 좋은 소식인가 나쁜 소식인가: 코드 판정은 PASS이며 문서 숫자는 `cb1a78c`에서 즉시 5개로 고쳤습니다.

#### 9-4. Codex V2 최종 재현

```text
$ for n in 1 2 3; do bash scripts/acceptance-0-2-unreachable-content.sh; done
run 1: CHECKED: 5 / PASS
run 2: CHECKED: 5 / PASS
run 3: CHECKED: 5 / PASS
$ bash /tmp/codex-v2-object-types.sh <worktree>
BLOCKED type=blob exit=1 literal_not_echoed=YES
BLOCKED type=commit exit=1 literal_not_echoed=YES
BLOCKED type=tree exit=1 literal_not_echoed=YES
BLOCKED type=tag exit=1 literal_not_echoed=YES
BLOCKED fsck_failure exit=1
PASS: all unreachable object types and fsck failure are fail-closed
$ rg -c '^      - name:' .github/workflows/verify.yml
17
$ gh issue view 22
OPEN — 현재 커밋 설명문·파일 경로의 로컬 금지값도 차단한다
```

→ 무엇을 시켰나: V1 PASS의 반복성, 모든 Git 객체형, `fsck` 실패, 문서·CI 단계 수, 잔여 이슈를 직접 재현했습니다.
→ 뭐가 나왔나: 5개 사례 3회 동일, 네 객체형과 검사 실패 전부 차단, 실제 값 미출력, 17단계·#22가 확인됐습니다.
→ 좋은 소식인가 나쁜 소식인가: V1 PASS와 Codex V2가 일치해 AC-19 범위의 적대검증은 통과했습니다.

#### 9-5. 훅 환경 수리 후 Claude V1

`env -u ANTHROPIC_API_KEY claude -p --model sonnet --effort medium`으로 322d523·56cc258·0235b9b를
읽기 전용 재검토했습니다. 프롬프트 끝에는 strict §8-7 출력 형식 원문을 다시 붙였습니다.

```text
VERDICT: PASS

- 별도 임시 clone에서 322d523의 6번째 사례가 head_same=NO, status_same=NO로 RED임을 재현했습니다.
- 56cc258은 ROOT 다음 Git 환경 unset 두 줄만 추가했고 같은 사례가 6/6 GREEN임을 재현했습니다.
- 실제 worktree는 시작/종료 모두 HEAD=0235b9b, status 없음으로 불변이었습니다.
- 별도 연결 worktree의 실제 pre-push에서 GIT_DIR 절대경로·GIT_WORK_TREE unset을 관찰했습니다.
- 수정 전에는 가짜 폴더 명령이 실제 branch HEAD를 바꾸고, 수정 후에는 HEAD/status가 불변임을 재현했습니다.
- e794579·4f65be1는 refs 역사에 없고 최종 diff에 .gitignore·docs/README가 없음을 확인했습니다.
- 실제 훅을 설치한 별도 clone의 로컬 bare push에서 18개 검사가 전부 통과했습니다.
- 범위 안 중간 이상 결함은 0건입니다.
```

→ 무엇을 시켰나: 시험 자기판정이 아니라 실제 연결 worktree의 push 환경과 수정 전후 바깥 저장소 변화를 독립 재현하게 했습니다.
→ 뭐가 나왔나: RED·두 줄 GREEN·역사 정리·6개 SOT·실제 훅 push가 모두 확인돼 PASS였습니다.
→ 좋은 소식인가 나쁜 소식인가: 첫 실제 push에서 찾은 새 범위 안 결함도 다른 엔진 검증을 통과해 좋은 소식입니다.

#### 9-6. 훅 환경 수리 Codex V2

```text
$ bash scripts/acceptance-0-2-unreachable-content.sh
[1/6] 일반 실행은 무해한 unreachable blob을 허용 -> PASS (exit=0)
[2/6] 일반 실행은 금지값이 든 unreachable blob을 차단 -> BLOCKED (exit=1)
[3/6] unreachable 객체 읽기 실패는 조용히 통과하지 않음 -> BLOCKED (exit=1)
[4/6] 큰 unreachable blob 앞쪽의 금지값도 차단 -> BLOCKED (exit=1)
[5/6] 종료상태 실행은 무해한 unreachable blob도 차단 -> BLOCKED (exit=1)
[6/6] Git hook 환경에서도 바깥 저장소 무오염 -> PASS (exit=0)
CHECKED: 6
PASS: AC-19 일반 내용 검사와 종료상태 0건 조건 분리
$ git diff --unified=0 322d523 56cc258 -- scripts/acceptance-0-2-unreachable-content.sh
+unset GIT_DIR GIT_INDEX_FILE GIT_OBJECT_DIRECTORY GIT_WORK_TREE GIT_COMMON_DIR \
+  GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_PREFIX
$ git log --all --format='%H' | grep '<e794579-or-4f65be1>'
출력 없음
$ git diff --name-status origin/main..HEAD
M .github/workflows/verify.yml
A docs/engineering/gate0-unreachable-secret-scan-goal-2026-08-17.md
M docs/sot/verification-commands.md
A scripts/acceptance-0-2-unreachable-content.sh
M scripts/acceptance-0-2.sh
PASS HEAD/status unchanged
```

→ 무엇을 시켰나: V1의 여섯 사례, 두 줄 최소 변경, 무효 역사 부재, 최종 파일 목록과 실제 worktree 불변을 다시 확인했습니다.
→ 뭐가 나왔나: V1과 전부 일치했고 사고 파일·커밋은 refs와 최종 diff에 없습니다.
→ 좋은 소식인가 나쁜 소식인가: 훅 환경 수리에 대한 V1/V2 교차검증도 일치해 좋은 소식입니다.

#### 9-7. 제출 직전 사람 셀프 감사 (§8-6b)

- 아니오 — 1층 결론에 풀이 없는 전문용어가 없습니다.
- 아니오 — 해석이 없는 출력 블록·표가 없습니다.
- 아니오 — 1층에 결정할 사항과 승인 전 정지 상태가 빠지지 않았습니다.
- 아니오 — 결정 카드에 버린 길과 대가가 있습니다.
- 아니오 — 줄 위치를 들 때 그 줄의 역할을 함께 설명했습니다.
- 아니오 — 쉽게 쓰기 위해 실패·수치·검증 공백을 빼지 않았습니다.
- 아니오 — 초등학생용 비유로 내용을 축소하지 않았습니다.
- 아니오 — 건너뛴 `actionlint`, 첫 Gate 흔들림, 첫 Claude 거부·첫 push 오염과 재시도를 숨기지 않았습니다.
- 아니오 — 확인하지 못한 서버 CI와 #22를 확인된 완료처럼 쓰지 않았습니다.

### 10. 도구 제약

대화의 goal 상태 기록 도구는 제공되지 않아 호출이 `TypeError`로 실패했습니다. 이를 성공으로 세지
않았고, 이 추적 가능한 goal 문서를 정본 기록으로 사용합니다.

### 11. 중복 수리 정리 계획 — 임시 예외 종료

#### 11-1. 결론

검사 동작은 수리됐지만, 이 가지에는 아직 “검사가 실행되지 않는다”는 과거 임시 예외가 남아 있습니다.
그대로 합치면 실제 검사와 예외 원장이 서로 반대말을 하며, 2026-08-21 기한이 지난 뒤 새 서버 검사를
막을 수 있습니다. 제품 분류기를 시작하기 전에 이 한 항목을 종료합니다.

#### 11-2. 판단 근거

PR #21은 `acceptance-0-2` 임시 예외를 삭제하고 `weakens-check` 검토 표시를 붙였지만, 객체형 전체,
읽기 실패, 50MiB 객체, 실제 훅 환경 오염을 이 가지와 같은 여섯 사례로 고정하지 않았습니다. 반대로
PR #23은 더 강한 여섯 사례와 실패 닫힘을 보존하지만 임시 예외 종료와 검토 표시가 빠졌습니다.

따라서 PR #21 전체를 섞지 않고, 이 가지의 구현과 시험은 그대로 둔 채 해결된 예외 한 항목만 제거하고
검사 판정 범위 변경 표시를 붙입니다. 현재도 참조되는 기록의 설명문·파일 경로·태그 검사 구멍은 별도
이슈 #22에 남기며 이번 수정에 섞지 않습니다.

#### 11-3. 실행 가능한 인수 기준

**AC-19-R1.** `suppressions.yaml`에서 `check: acceptance-0-2` 항목은 정확히 0건이고 다른 억제 항목은
기준 커밋 `f28511e`와 같아야 합니다. 기존 여섯 사례, 시작 검사 전체, 업로드 전 검사, 저장소 전체
검사가 모두 합격해야 하며 PR #23에는 `weakens-check` 표시가 있어야 합니다.

가짜 합격은 다음과 같습니다.

- PR #21 구현 전체를 가져와 더 강한 객체형·오류·대용량·훅 환경 시험을 잃습니다.
- `acceptance-0-2` 이외의 억제 항목을 함께 바꿉니다.
- 예외 항목만 지우고 실제 여섯 사례나 서버 연결이 깨진 상태를 통과로 보고합니다.
- 이슈 #22를 이번 인수 기준에 섞어 변경 범위를 넓힙니다.

#### 11-4. Harness 진행

- PLAN: 이 절을 코드 변경보다 먼저 별도 커밋으로 고정합니다.
- GREEN: `suppressions.yaml`의 해결된 한 항목만 제거합니다.
- VERIFY: 여섯 사례 → 시작 검사 → 업로드 전 검사 → 저장소 전체 검사 순서로 실행합니다.
- REVIEW: Claude가 #21 장점 손실·#23 시험 약화·다른 억제 변경을 공격하고 Codex가 전부 재현합니다.
- SHIP: 일반 push와 동일 코드 지문의 서버 검사까지만 진행하고 합치기 전에 멈춥니다.

#### 11-5. 결정 카드

**무엇을** — PR #23을 정본 수리로 유지하면서 해결된 임시 예외와 빠진 검토 표시만 보완합니다.

**왜** — #23의 강한 실행 증거와 #21의 예외 종료를 둘 다 보존해야 하기 때문입니다.

**버린 길** — #21 전체를 가져오는 길은 더 강한 여섯 사례를 잃고, #23을 그대로 합치는 길은 해결된
검사를 계속 예외로 남기므로 버렸습니다. 두 요청을 모두 합치는 길도 충돌과 중복 역사를 만듭니다.

**대가** — 두 요청 중 하나를 정본으로 고르는 교정 커밋과 서버 재검사가 추가됩니다.

**되돌리기** — 이 교정 커밋을 되돌리면 코드 동작은 그대로지만 임시 예외가 다시 살아나므로,
2026-08-21 이후 새 서버 검사가 막히는 상태로 돌아갑니다.

#### 11-6. 비범위

- PR #21 닫기 또는 두 PR 합치기
- 이슈 #22 구현
- HumanSearch 제품 분류기, 실제 포털, 로그인, 후보자 자료
- main 수정, 자동 합치기, 배포

#### 11-7. 교정 실행·적대검증 로그

이 절 아래에 임시 예외 제거, 대상 시험, 전체 검사, Claude V1, Codex V2, 원격 서버 결과를 순서대로
추가합니다. 과거 1~10절의 증거는 고치거나 삭제하지 않습니다.

### 12. Attempt 2 — PR #23 단일 정본 강화

#### 12-1. 결론

PR #23의 검사 본체는 PR #21보다 더 많은 실패를 막지만, 시험 프로그램이 호출자의 패턴 파일 설정을
그대로 물려받는 한 가지 약점이 남아 있습니다. 이 약점을 먼저 실패 시험으로 고정하고, 파일 조각뿐
아니라 기록 설명문·파일 이름·주석 태그까지 실제 시험으로 증명한 뒤 PR #23 하나만 남깁니다.

PR #21의 코드는 합치거나 복사하지 않습니다. 그 요청에서 유효한 환경 격리 한 줄의 의도만 PR #23의
더 강한 시험에 흡수하고, 로컬·서버 검사와 두 검토자가 모두 동의한 뒤 PR #21을 중복으로 닫습니다.

#### 12-2. 판단 근거와 현재 상태

현재 작업 폴더는 깨끗하지만 사용자가 예상한 `f28511e`보다 로컬 커밋 두 개가 앞서 있습니다. 두 커밋은
이 문서에 정리 계획을 더하고 `acceptance-0-2` 임시 억제 한 항목을 삭제했으며, reset·stash·checkout
없이 현재 `e8e402d`를 새 감사 기준으로 삼습니다.

PR #21의 유효한 추가 보호는 합성 시험 시작부의 `unset SECRET_PATTERNS_FILE`입니다. PR #23의
`scripts/acceptance-0-2-unreachable-content.sh:5-7`은 Git 저장소 위치 환경은 비우지만 이 값은 비우지
않습니다. 실제 판정기 `scripts/acceptance-0-2.sh:12-14`는 이 값이 있으면 fixture의 합성 패턴 대신
호출자 경로를 우선하므로 동일 시험이 실행 환경에 따라 달라집니다.

```text
$ SECRET_PATTERNS_FILE=/dev/null bash scripts/acceptance-0-2-unreachable-content.sh
[1/6] 일반 실행은 무해한 unreachable blob을 허용 -> UNEXPECTED (exit=2, expected=pass)
FAIL: /dev/null 없음/빈 파일 — AC 판정 불가
[2/6] 일반 실행은 금지값이 든 unreachable blob을 차단 -> BLOCKED (exit=2)
[3/6] unreachable 객체 읽기 실패는 조용히 통과하지 않음 -> BLOCKED (exit=2)
[4/6] 큰 unreachable blob 앞쪽의 금지값도 차단 -> BLOCKED (exit=2)
[5/6] 종료상태 실행은 무해한 unreachable blob도 차단 -> BLOCKED (exit=2)
[6/6] Git hook 환경에서도 바깥 저장소 무오염 -> UNEXPECTED (exit=1, head_same=YES, status_same=YES)
[1/5] 일반 실행은 무해한 unreachable blob을 허용 -> UNEXPECTED (exit=2, expected=pass)
FAIL: /dev/null 없음/빈 파일 — AC 판정 불가
[2/5] 일반 실행은 금지값이 든 unreachable blob을 차단 -> BLOCKED (exit=2)
[3/5] unreachable 객체 읽기 실패는 조용히 통과하지 않음 -> BLOCKED (exit=2)
[4/5] 큰 unreachable blob 앞쪽의 금지값도 차단 -> BLOCKED (exit=2)
[5/5] 종료상태 실행은 무해한 unreachable blob도 차단 -> BLOCKED (exit=2)
CHECKED: 5
FAIL: AC-19 예상과 다른 사례 1건
CHECKED: 6
FAIL: AC-19 예상과 다른 사례 2건
rc_null=1
$ SECRET_PATTERNS_FILE=.secret-patterns.default bash scripts/acceptance-0-2-unreachable-content.sh
[1/6] 일반 실행은 무해한 unreachable blob을 허용 -> UNEXPECTED (exit=2, expected=pass)
FAIL: .secret-patterns.default 없음/빈 파일 — AC 판정 불가
[2/6] 일반 실행은 금지값이 든 unreachable blob을 차단 -> BLOCKED (exit=2)
[3/6] unreachable 객체 읽기 실패는 조용히 통과하지 않음 -> BLOCKED (exit=2)
[4/6] 큰 unreachable blob 앞쪽의 금지값도 차단 -> BLOCKED (exit=2)
[5/6] 종료상태 실행은 무해한 unreachable blob도 차단 -> BLOCKED (exit=2)
[6/6] Git hook 환경에서도 바깥 저장소 무오염 -> UNEXPECTED (exit=1, head_same=YES, status_same=YES)
[1/5] 일반 실행은 무해한 unreachable blob을 허용 -> UNEXPECTED (exit=2, expected=pass)
FAIL: .secret-patterns.default 없음/빈 파일 — AC 판정 불가
[2/5] 일반 실행은 금지값이 든 unreachable blob을 차단 -> BLOCKED (exit=2)
[3/5] unreachable 객체 읽기 실패는 조용히 통과하지 않음 -> BLOCKED (exit=2)
[4/5] 큰 unreachable blob 앞쪽의 금지값도 차단 -> BLOCKED (exit=2)
[5/5] 종료상태 실행은 무해한 unreachable blob도 차단 -> BLOCKED (exit=2)
CHECKED: 5
FAIL: AC-19 예상과 다른 사례 1건
CHECKED: 6
FAIL: AC-19 예상과 다른 사례 2건
rc_default=1
```

→ 무엇을 시켰나: 호출자가 빈 파일과 저장소 기본 패턴 경로를 각각 넘긴 상태에서 현재 합성 시험을 실행했습니다.
→ 뭐가 나왔나: 두 실행 모두 무해한 사례가 시험 환경 때문에 실패했고, 바깥 저장소의 기록 위치와 파일 상태는 그대로였습니다.
→ 의미: 검사 본체의 보안 차단이 아니라 시험 격리가 실패한 올바른 RED이며, PR #21의 환경 격리 의도를 흡수해야 합니다.

#### 12-3. 계약 스펙과 인수 기준

입력은 `SECRET_PATTERNS_FILE`, `GIT_DIR`, `GIT_WORK_TREE` 등 호출자 환경과 합성 객체 종류입니다. 출력은
사례별 `PASS` 또는 `BLOCKED`, 전체 검사 수, 전체 종료 성적입니다. 실제 로컬 값은 읽거나 출력하지 않고
고정된 합성 카나리만 사용합니다.

**AC-19-R2.** 일반 실행은 무해한 미도달 객체를 허용하고, 합성 금지값이 든 blob·commit message·tree
path·annotated tag message를 모두 차단해야 합니다. 50MiB 이상 객체 앞부분의 값, `git fsck` 실패,
`git cat-file` 실패, 알 수 없는 객체형도 통과시켜서는 안 됩니다. `ACCEPTANCE_ENDSTATE=1`이면 내용과
무관하게 미도달 객체 한 개도 차단해야 합니다.

**AC-19-R3.** 합성 시험은 호출자가 `/dev/null`, `.secret-patterns.default`, Git 훅 저장소 위치 환경을
넘겨도 같은 판정을 내고, 바깥 저장소와 현재 작업 폴더의 HEAD·파일 상태를 바꾸지 않아야 합니다.

가짜 합격은 다음과 같습니다.

- 파일 조각만 검사하고 commit·tree·tag를 건너뜁니다.
- 큰 객체에서 값을 찾은 뒤 읽기 프로그램의 파이프 종료를 값 없음으로 오판합니다.
- `git fsck` 또는 `git cat-file` 실패를 검사 대상 없음으로 바꿉니다.
- 환경 상속 실행이 실패하는데 기본 실행만 통과했다고 보고합니다.
- RED 시험의 기대 결과를 GREEN에서 바꾸거나 새 사례를 삭제합니다.
- 실제 로컬 금지값을 시험 입력이나 출력에 사용합니다.

#### 12-4. Harness·적대검증 계획

- RED: 환경 상속 두 경우, 네 객체형, 큰 객체, 두 Git 명령 실패, 종료상태, 훅 환경 무오염을 시험에 고정합니다.
- RED 뮤테이션: 비blob 처리 한 줄을 임시로 끄면 commit·tree·tag 사례가 실제로 실패하는지 확인하고 즉시 원복합니다.
- GREEN: 합성 시험 진입부에서 `SECRET_PATTERNS_FILE`만 비우며 객체 판정 본체는 유지합니다.
- VERIFY: 사용자 지정 명령 전부, 셸 문법, 서버 단계·정본 목록, RED 불변, 비blob·파이프 판정 뮤테이션을 실행합니다.
- REVIEW: Claude V1이 원본 차이와 실행 원문을 공격하고, Codex V2가 환경·큰 객체·객체형·도구 실패·오염·억제·서버 배선을 재현합니다.
- SHIP: 중간 이상 결함 0건일 때만 일반 push, PR #23 갱신, 같은 기록 위치의 서버 성공 확인, PR #21 중복 종료까지 수행합니다.

#### 12-5. SOT·영향·비범위

읽은 정본은 `docs/sot/INDEX.md`, `coding-principles.md`, `git-workflow.md`, `hook-contracts.md`,
`verification-commands.md`입니다. P3의 검사 실패 차단, P13의 검사 약화 표시, P15의 로컬·서버 동시 배선,
P20의 0건 가짜 합격 금지를 적용합니다. 검사 동작과 실행 표가 달라지면 같은 변경에서 함께 고칩니다.

영향 범위는 시작 검사, 합성 회귀시험, 로컬 push 문지기, GitHub 서버 검사, 억제 원장과 PR 설명입니다.
틀리면 무해한 작업을 다시 막거나 복구 가능한 금지값을 놓칩니다. 되돌릴 때는 Attempt 2의 RED와 GREEN
커밋을 역순으로 되돌리되, 과거 억제를 되살리면 해당 사유가 다시 사실인지 별도 확인해야 합니다.

비범위는 main 수정·병합·배포, PR #13/#14/#15, 이슈 #22의 도달 가능한 commit message·tree path·tag
확장, HumanSearch L0 제품 코드, 실제 포털·브라우저·로그인·세션·후보자 자료, 실제 비밀값입니다.

#### 12-6. Attempt 2 실행·적대검증 로그

이 절 아래에 RED 커밋, GREEN 커밋, 전체 실행 원문, Claude V1 원문, Codex V2 재현 표, 원격 결과와
PR #21 중복 종료 근거를 순서대로 덧붙입니다. 기존 1~11절의 과거 증거는 고치거나 삭제하지 않습니다.

#### 12-7. RED 시험과 비blob 변형 증거

```text
$ bash -n scripts/acceptance-0-2-unreachable-content.sh
syntax_rc=0
$ bash scripts/acceptance-0-2-unreachable-content.sh
[1/13] SECRET_PATTERNS_FILE=/dev/null 상속을 격리 -> UNEXPECTED (exit=1, expected=pass)
[1/1] 일반 실행은 무해한 unreachable blob을 허용 -> UNEXPECTED (exit=2, expected=pass)
FAIL: /dev/null 없음/빈 파일 — AC 판정 불가
CHECKED: 1
FAIL: AC-19 예상과 다른 사례 1건
[2/13] SECRET_PATTERNS_FILE=.secret-patterns.default 상속을 격리 -> UNEXPECTED (exit=1, expected=pass)
[1/1] 일반 실행은 무해한 unreachable blob을 허용 -> UNEXPECTED (exit=2, expected=pass)
FAIL: .secret-patterns.default 없음/빈 파일 — AC 판정 불가
CHECKED: 1
FAIL: AC-19 예상과 다른 사례 1건
[3/13] 일반 실행은 무해한 unreachable blob을 허용 -> PASS (exit=0)
[4/13] 일반 실행은 금지값이 든 unreachable blob을 차단 -> BLOCKED (exit=1)
[5/13] unreachable commit message의 금지값을 차단 -> BLOCKED (exit=1)
[6/13] unreachable tree path의 금지값을 차단 -> BLOCKED (exit=1)
[7/13] unreachable annotated tag message의 금지값을 차단 -> BLOCKED (exit=1)
[8/13] git fsck 실패는 검사 대상 없음으로 통과하지 않음 -> BLOCKED (exit=1)
[9/13] unreachable 객체 읽기 실패는 조용히 통과하지 않음 -> BLOCKED (exit=1)
[10/13] 알 수 없는 unreachable 객체형은 읽기 실패로 차단 -> BLOCKED (exit=1)
[11/13] 큰 unreachable blob 앞쪽의 금지값도 차단 -> BLOCKED (exit=1)
[12/13] 종료상태 실행은 무해한 unreachable blob도 차단 -> BLOCKED (exit=1)
[13/13] Git hook 환경에서도 바깥 저장소 무오염 -> PASS (exit=0)
CHECKED: 13
FAIL: AC-19 예상과 다른 사례 2건
red_rc=1
```

→ 무엇을 시켰나: 구현을 바꾸기 전에 13개 회귀 사례의 문법과 실제 판정을 실행했습니다.
→ 뭐가 나왔나: 문법은 정상이었고 환경 상속 두 사례만 예상대로 실패했으며, 새 객체형·도구 실패 사례는 기존 강한 판정이 막았습니다.
→ 의미: RED는 환경 격리 누락을 정확히 가리키며, 이미 동작하는 보안 분기를 약화하지 않고 GREEN 한 줄을 요구합니다.

`scripts/acceptance-0-2.sh`의 객체 반복문에 blob이 아닌 형식을 건너뛰는 한 줄을 임시로 넣고 같은 시험을
실행한 뒤 즉시 제거했습니다. 아래 변형은 작업 상태에 남지 않았고 커밋 대상에도 포함하지 않습니다.

```text
$ bash scripts/acceptance-0-2-unreachable-content.sh  # 임시 비blob 건너뛰기 변형 상태
[1/13] SECRET_PATTERNS_FILE=/dev/null 상속을 격리 -> UNEXPECTED (exit=1, expected=pass)
[1/1] 일반 실행은 무해한 unreachable blob을 허용 -> UNEXPECTED (exit=2, expected=pass)
FAIL: /dev/null 없음/빈 파일 — AC 판정 불가
CHECKED: 1
FAIL: AC-19 예상과 다른 사례 1건
[2/13] SECRET_PATTERNS_FILE=.secret-patterns.default 상속을 격리 -> UNEXPECTED (exit=1, expected=pass)
[1/1] 일반 실행은 무해한 unreachable blob을 허용 -> UNEXPECTED (exit=2, expected=pass)
FAIL: .secret-patterns.default 없음/빈 파일 — AC 판정 불가
CHECKED: 1
FAIL: AC-19 예상과 다른 사례 1건
[3/13] 일반 실행은 무해한 unreachable blob을 허용 -> PASS (exit=0)
[4/13] 일반 실행은 금지값이 든 unreachable blob을 차단 -> BLOCKED (exit=1)
[5/13] unreachable commit message의 금지값을 차단 -> UNEXPECTED (exit=0, expected=blocked)
PASS: no secret-pattern match in any tracked file, .env not tracked
PASS: 0-2 — 히스토리·객체·reflog·docs 리터럴 0건, 스캐너 뮤테이션 검출 확인
[6/13] unreachable tree path의 금지값을 차단 -> UNEXPECTED (exit=0, expected=blocked)
PASS: no secret-pattern match in any tracked file, .env not tracked
PASS: 0-2 — 히스토리·객체·reflog·docs 리터럴 0건, 스캐너 뮤테이션 검출 확인
[7/13] unreachable annotated tag message의 금지값을 차단 -> UNEXPECTED (exit=0, expected=blocked)
PASS: no secret-pattern match in any tracked file, .env not tracked
PASS: 0-2 — 히스토리·객체·reflog·docs 리터럴 0건, 스캐너 뮤테이션 검출 확인
[8/13] git fsck 실패는 검사 대상 없음으로 통과하지 않음 -> BLOCKED (exit=1)
[9/13] unreachable 객체 읽기 실패는 조용히 통과하지 않음 -> BLOCKED (exit=1)
[10/13] 알 수 없는 unreachable 객체형은 읽기 실패로 차단 -> UNEXPECTED (exit=0, expected=blocked)
PASS: no secret-pattern match in any tracked file, .env not tracked
PASS: 0-2 — 히스토리·객체·reflog·docs 리터럴 0건, 스캐너 뮤테이션 검출 확인
[11/13] 큰 unreachable blob 앞쪽의 금지값도 차단 -> BLOCKED (exit=1)
[12/13] 종료상태 실행은 무해한 unreachable blob도 차단 -> BLOCKED (exit=1)
[13/13] Git hook 환경에서도 바깥 저장소 무오염 -> UNEXPECTED (exit=1, head_same=YES, status_same=YES)
[1/10] 일반 실행은 무해한 unreachable blob을 허용 -> PASS (exit=0)
[2/10] 일반 실행은 금지값이 든 unreachable blob을 차단 -> BLOCKED (exit=1)
[3/10] unreachable commit message의 금지값을 차단 -> UNEXPECTED (exit=0, expected=blocked)
PASS: no secret-pattern match in any tracked file, .env not tracked
PASS: 0-2 — 히스토리·객체·reflog·docs 리터럴 0건, 스캐너 뮤테이션 검출 확인
[4/10] unreachable tree path의 금지값을 차단 -> UNEXPECTED (exit=0, expected=blocked)
PASS: no secret-pattern match in any tracked file, .env not tracked
PASS: 0-2 — 히스토리·객체·reflog·docs 리터럴 0건, 스캐너 뮤테이션 검출 확인
[5/10] unreachable annotated tag message의 금지값을 차단 -> UNEXPECTED (exit=0, expected=blocked)
PASS: no secret-pattern match in any tracked file, .env not tracked
PASS: 0-2 — 히스토리·객체·reflog·docs 리터럴 0건, 스캐너 뮤테이션 검출 확인
[6/10] git fsck 실패는 검사 대상 없음으로 통과하지 않음 -> BLOCKED (exit=1)
[7/10] unreachable 객체 읽기 실패는 조용히 통과하지 않음 -> BLOCKED (exit=1)
[8/10] 알 수 없는 unreachable 객체형은 읽기 실패로 차단 -> UNEXPECTED (exit=0, expected=blocked)
PASS: no secret-pattern match in any tracked file, .env not tracked
PASS: 0-2 — 히스토리·객체·reflog·docs 리터럴 0건, 스캐너 뮤테이션 검출 확인
[9/10] 큰 unreachable blob 앞쪽의 금지값도 차단 -> BLOCKED (exit=1)
[10/10] 종료상태 실행은 무해한 unreachable blob도 차단 -> BLOCKED (exit=1)
CHECKED: 10
FAIL: AC-19 예상과 다른 사례 4건
CHECKED: 13
FAIL: AC-19 예상과 다른 사례 7건
mutation_rc=1
```

→ 무엇을 시켰나: 실제 판정기에서 비blob 객체를 의도적으로 건너뛰게 만든 뒤 새 시험을 다시 실행했습니다.
→ 뭐가 나왔나: commit·tree·tag와 알 수 없는 형식이 모두 가짜 합격으로 뒤집혔고, 바깥 훅 재현도 그 실패를 전파했습니다.
→ 의미: 새 객체형 시험은 구현을 따라 쓴 장식이 아니라 해당 보호 분기가 사라지면 즉시 실패하는 유효한 회귀 장치입니다.

#### 12-8. GREEN 최소 수정과 환경 독립 실행

GREEN은 `scripts/acceptance-0-2-unreachable-content.sh` 진입부에서 `SECRET_PATTERNS_FILE`을 비우는 한 줄과
그 이유를 적은 주석만 추가했습니다. `scripts/acceptance-0-2.sh`의 실제 객체 판정 코드는 바꾸지 않았고,
RED 커밋의 13개 기대 결과도 그대로 유지했습니다.

```text
$ bash scripts/acceptance-0-2-unreachable-content.sh
[1/13] SECRET_PATTERNS_FILE=/dev/null 상속을 격리 -> PASS (exit=0)
[2/13] SECRET_PATTERNS_FILE=.secret-patterns.default 상속을 격리 -> PASS (exit=0)
[3/13] 일반 실행은 무해한 unreachable blob을 허용 -> PASS (exit=0)
[4/13] 일반 실행은 금지값이 든 unreachable blob을 차단 -> BLOCKED (exit=1)
[5/13] unreachable commit message의 금지값을 차단 -> BLOCKED (exit=1)
[6/13] unreachable tree path의 금지값을 차단 -> BLOCKED (exit=1)
[7/13] unreachable annotated tag message의 금지값을 차단 -> BLOCKED (exit=1)
[8/13] git fsck 실패는 검사 대상 없음으로 통과하지 않음 -> BLOCKED (exit=1)
[9/13] unreachable 객체 읽기 실패는 조용히 통과하지 않음 -> BLOCKED (exit=1)
[10/13] 알 수 없는 unreachable 객체형은 읽기 실패로 차단 -> BLOCKED (exit=1)
[11/13] 큰 unreachable blob 앞쪽의 금지값도 차단 -> BLOCKED (exit=1)
[12/13] 종료상태 실행은 무해한 unreachable blob도 차단 -> BLOCKED (exit=1)
[13/13] Git hook 환경에서도 바깥 저장소 무오염 -> PASS (exit=0)
CHECKED: 13
PASS: AC-19 일반 내용 검사와 종료상태 0건 조건 분리
green_rc=0
```

→ 무엇을 시켰나: 호출 환경을 따로 주지 않은 기본 실행으로 13개 사례를 다시 돌렸습니다.
→ 뭐가 나왔나: 허용해야 할 4개 실행은 통과했고 차단해야 할 9개 실행은 모두 차단됐으며 전체 성적은 합격입니다.
→ 의미: 환경 격리 한 줄이 RED 두 건을 닫았고 기존 객체형·대용량·실패 차단은 그대로 남았습니다.

```text
$ SECRET_PATTERNS_FILE=/dev/null bash scripts/acceptance-0-2-unreachable-content.sh
[1/13] SECRET_PATTERNS_FILE=/dev/null 상속을 격리 -> PASS (exit=0)
[2/13] SECRET_PATTERNS_FILE=.secret-patterns.default 상속을 격리 -> PASS (exit=0)
[3/13] 일반 실행은 무해한 unreachable blob을 허용 -> PASS (exit=0)
[4/13] 일반 실행은 금지값이 든 unreachable blob을 차단 -> BLOCKED (exit=1)
[5/13] unreachable commit message의 금지값을 차단 -> BLOCKED (exit=1)
[6/13] unreachable tree path의 금지값을 차단 -> BLOCKED (exit=1)
[7/13] unreachable annotated tag message의 금지값을 차단 -> BLOCKED (exit=1)
[8/13] git fsck 실패는 검사 대상 없음으로 통과하지 않음 -> BLOCKED (exit=1)
[9/13] unreachable 객체 읽기 실패는 조용히 통과하지 않음 -> BLOCKED (exit=1)
[10/13] 알 수 없는 unreachable 객체형은 읽기 실패로 차단 -> BLOCKED (exit=1)
[11/13] 큰 unreachable blob 앞쪽의 금지값도 차단 -> BLOCKED (exit=1)
[12/13] 종료상태 실행은 무해한 unreachable blob도 차단 -> BLOCKED (exit=1)
[13/13] Git hook 환경에서도 바깥 저장소 무오염 -> PASS (exit=0)
CHECKED: 13
PASS: AC-19 일반 내용 검사와 종료상태 0건 조건 분리
```

→ 무엇을 시켰나: 호출자가 빈 패턴 파일을 강제로 넘긴 환경에서 같은 13개 사례를 실행했습니다.
→ 뭐가 나왔나: 기본 실행과 같은 13개 판정과 전체 합격이 나왔습니다.
→ 의미: 외부의 빈 경로가 합성 시험을 무력화하거나 거짓 실패로 바꾸지 못합니다.

```text
$ SECRET_PATTERNS_FILE=.secret-patterns.default bash scripts/acceptance-0-2-unreachable-content.sh
[1/13] SECRET_PATTERNS_FILE=/dev/null 상속을 격리 -> PASS (exit=0)
[2/13] SECRET_PATTERNS_FILE=.secret-patterns.default 상속을 격리 -> PASS (exit=0)
[3/13] 일반 실행은 무해한 unreachable blob을 허용 -> PASS (exit=0)
[4/13] 일반 실행은 금지값이 든 unreachable blob을 차단 -> BLOCKED (exit=1)
[5/13] unreachable commit message의 금지값을 차단 -> BLOCKED (exit=1)
[6/13] unreachable tree path의 금지값을 차단 -> BLOCKED (exit=1)
[7/13] unreachable annotated tag message의 금지값을 차단 -> BLOCKED (exit=1)
[8/13] git fsck 실패는 검사 대상 없음으로 통과하지 않음 -> BLOCKED (exit=1)
[9/13] unreachable 객체 읽기 실패는 조용히 통과하지 않음 -> BLOCKED (exit=1)
[10/13] 알 수 없는 unreachable 객체형은 읽기 실패로 차단 -> BLOCKED (exit=1)
[11/13] 큰 unreachable blob 앞쪽의 금지값도 차단 -> BLOCKED (exit=1)
[12/13] 종료상태 실행은 무해한 unreachable blob도 차단 -> BLOCKED (exit=1)
[13/13] Git hook 환경에서도 바깥 저장소 무오염 -> PASS (exit=0)
CHECKED: 13
PASS: AC-19 일반 내용 검사와 종료상태 0건 조건 분리
```

→ 무엇을 시켰나: 호출자가 저장소 기본 패턴 파일을 넘긴 환경에서도 같은 시험을 실행했습니다.
→ 뭐가 나왔나: 합성 fixture 내부의 카나리만 사용해 기본 실행과 동일한 결과가 나왔습니다.
→ 의미: PR #21의 유효한 환경 격리 의도가 PR #23의 더 강한 13개 시험에 흡수됐습니다.

#### 12-9. 억제 원장과 실행 게이트 일치성

| 질문 | 실제 실행 주체와 범위 | 근거 |
|---|---|---|
| 실제 로컬 저장소 검사를 누가 실행하는가 | 세션 시작의 `scripts/session-status.sh`가 실제 `scripts/acceptance-0-2.sh`를 포함한 검사를 실행합니다. `hooks/pre-push`는 실제 로컬 값이 필요한 이 파일 하나는 의도적으로 건너뜁니다. | `scripts/session-status.sh:46-64`, `hooks/pre-push:143-147` |
| 합성 AC-19 시험을 로컬 push에서 누가 실행하는가 | `hooks/pre-push`가 이름 규칙으로 인수 스크립트를 모으고, 정확히 `acceptance-0-2.sh`와 `acceptance-0-5.sh`만 제외하므로 `acceptance-0-2-unreachable-content.sh`를 실행합니다. | `hooks/pre-push:110-171` |
| 같은 합성 시험을 서버에서 누가 실행하는가 | GitHub 서버 검사 5번째 단계가 같은 파일을 직접 실행합니다. | `.github/workflows/verify.yml:85-88`, `docs/sot/verification-commands.md:20-40` |
| 도달 가능한 객체는 어디서 다루는가 | 실제 로컬 검사의 5-c와 서버의 히스토리 전량 검사가 refs·되돌림 기록이 가리키는 blob 내용을 검사합니다. 현재 추적 파일은 `verify.sh`가 별도로 검사합니다. | `scripts/acceptance-0-2.sh:137-146`, `.github/workflows/verify.yml:48-83`, `verify.sh:49-73` |
| 도달 불가능한 객체는 어디서 다루는가 | 실제 로컬 검사의 5-b가 blob·commit·tree·tag를 객체형 그대로 열고, 합성 AC-19가 네 형식과 실패 분기를 로컬 push·서버에서 동일하게 재현합니다. | `scripts/acceptance-0-2.sh:102-135`, `scripts/acceptance-0-2-unreachable-content.sh` |
| PR #23 뒤에도 남는 범위는 무엇인가 | 현재 refs나 되돌림 기록이 가리키는 commit message·tree path·annotated tag message는 blob 전용 경로에서 빠져 있으며 이슈 #22가 담당합니다. HumanSearch L0 제품 코드는 시작하지 않습니다. | GitHub 이슈 #22, `scripts/acceptance-0-2.sh:137-146` |

→ 무엇을 대조했나: 로컬 세션 검사, push 직전 문지기, GitHub 서버 단계, 실제 객체 판정기와 정본 표를 한 행씩 연결했습니다.
→ 뭐가 나왔나: 실제 로컬 값 검사는 세션 시작에, 합성 AC-19는 로컬 push와 서버 양쪽에 배선돼 있으며 17개 서버 단계와 정본 표도 같습니다.
→ 의미: 억제 사유의 “어느 게이트도 실행하지 않는다”는 현재 사실이 아니지만, 별도 이슈 #22의 도달 가능한 비blob 범위는 정직하게 남습니다.

```text
$ git show origin/task/humansearch-g0-unreachable-secret-scan:suppressions.yaml | rg -n 'acceptance-0-2'
출력 없음
pr21_match_rc=1
$ rg -n 'acceptance-0-2' suppressions.yaml
출력 없음
pr23_match_rc=1
$ git diff --unified=0 f28511e8df4793bf33f6fbaf6cb473c1de9a951f..HEAD -- suppressions.yaml
@@ -10,16 +9,0 @@
-- check: acceptance-0-2
-  reason: >-
-    히스토리 정리 완결성 검사. pre-push 에서 CI 로 이관하려 했으나 CI 에서도 돌지 못해
-    현재 어느 게이트도 실행하지 않는 상태다. 두 가지 이유가 겹쳤다.
-    (1) unreachable==0 조건이 git add·reset·amend 만으로 깨져 개발 중 상시 실패한다.
-    (2) 로컬 전용 .secret-patterns 를 요구하는데 CI 에는 없고, .secret-patterns.default 로
-    대체하면 패턴 파일 자신이 자기매칭한다(CI run 31176518944, blob 09b233e).
-    로컬에서 현재 exit 1(unreachable 잔존)이다.
-  owner: sangmokang
-  expiry: 2026-08-21
-  issue: >-
-    분할 이관한다. 0-2 의 뮤테이션 테스트는 합성 카나리(ACCEPTANCE-MUTATION-CANARY-42)만
-    쓰므로 로컬 패턴 파일이 필요 없다 — CI 로 그대로 옮길 수 있다. 이것이 스캐너 무력화를
-    탐지하는 핵심이므로 최우선이다. unreachable 검사는 커밋 시점 검사가 아니라 주기 점검으로
-    옮기고, 히스토리 리터럴 검사는 CI 의 '히스토리 전량 스캔' 스텝이 이미 등가로 수행한다.
```

→ 무엇을 시켰나: PR #21, 현재 PR #23 작업본, 원격 PR #23 기준점의 억제 원장 차이를 직접 비교했습니다.
→ 뭐가 나왔나: PR #21과 현재 작업본 모두 해당 억제가 0건이고, 현재 작업본은 원격 PR #23에서 그 한 항목만 삭제했습니다.
→ 의미: 일반 실행의 개수 오판과 서버 미실행이라는 기존 사유가 모두 해소돼 삭제가 맞으며, 다른 억제 항목은 건드리지 않았습니다.
