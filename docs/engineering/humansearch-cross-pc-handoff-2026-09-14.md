# HumanSearch — 다른 PC에서 이어가기 (2026-09-14)

## 결론

현재 제품 작업은 진행 중이다. GitHub 인계 준비와 제품 운영 완료는 별개다. 이 문서는 GitHub에서 코드·요구·작업 기록을 복원하는 안내이며,
잡코리아/RPS 운영 완료나 발송 허가를 뜻하지 않는다. 기본 설정은 현재 검증 환경과 같은 macOS다.

## 1. 새 PC 준비

Git, GitHub CLI(`gh`), Python 패키지 관리자 `uv`, Bash, Ruby, Perl, Node.js가 필요하다.
HumanSearch의 `pyproject.toml`은 Python >=3.14를 요구한다. 전체 저장소 검사는 Python 시험 외에도
Ruby/Perl/Node 기반 검사기를 실행하므로 Python만 설치하면 모든 게이트가 준비된 것은 아니다.
현재 PC 관측: Codex CLI 0.154.0, uv 0.11.3. Codex 버전은 관측값이다.
현재 GitHub CI의 C-8 계약은 uv 0.11.3을 고정하고 `humansearch/.python-version`은 3.14.1이다.
재개할 때 해당 브랜치의 두 파일을 다시 읽어 버전 계약이 바뀌었는지 확인한다.

macOS에서는 [Homebrew 설치 안내](https://brew.sh/)를 따른 뒤 `brew install git gh uv node`로
필요 도구를 준비한다. `ruby --version`, `perl -v`, `bash --version`도 확인한다.
uv의 다른 설치 방법은 [uv 공식 설치 문서](https://docs.astral.sh/uv/getting-started/installation/)를 따른다.
현재 CI 환경과 맞추려면 공식 uv 설치 안내의 버전 지정 URL `https://astral.sh/uv/0.11.3/install.sh`를
사용하고 `uv --version`을 재조회한다. 이미 설치된 다른 버전을 무조건 덮어쓰지 않는다.
`uv python install 3.14.1`로 현재 `humansearch/.python-version`이 지정한 Python을 준비한다. uv는 기본적으로 누락된 Python을 자동 설치하지만,
이 명령으로 설치 단계를 먼저 확인할 수 있다. 다운로드 제한 환경에서는 조직의 승인된 Python 설치를 사용한다.
[Python 설치 동작의 공식 근거](https://docs.astral.sh/uv/guides/install-python/)를 참고한다.

GitHub 접근 권한이 있는 본인 계정으로 로그인하고 새 폴더에 복제한다.
이미 복제한 폴더라면 다시 clone하지 말고 `git status` 확인 후 `git fetch origin`으로 갱신한다.

```bash
gh auth login
gh repo clone sangmokang/Valuehire_v6
cd Valuehire_v6
git fetch origin
git ls-remote --heads origin task/hs-cross-pc-handoff-20260914
git switch --track origin/task/hs-cross-pc-handoff-20260914
bash scripts/install-hooks.sh
git config --get core.hooksPath
```

→ 마지막 결과는 `hooks`여야 한다. 이 안내 브랜치는 제품 변경을 모두 합친 브랜치가 아니다.
과거 HS00 장부와 9월 8일 kickoff 원문도 이 브랜치에 보존했다(출처 464220f).
이 원문 보존은 HS00 코드 전체 감사·병합을 뜻하지 않는다. 아래 표에서 이어갈 작업 하나를 선택해 별도 worktree를 만든다. 이미 존재하는 worktree는 재생성하지 않는다.

```bash
git worktree add -b task/hs-13-stack-20260910 worktrees/hs-13-stack-20260910 origin/task/hs-13-stack-20260910
cd worktrees/hs-13-stack-20260910
bash scripts/install-hooks.sh
cd humansearch
uv sync --locked
uv run pytest -q
uv run ruff check .
uv run mypy src tests
cd ..
git diff --check
bash verify.sh
```

→ 위 예시는 기존 PR83 작업을 이어받는다. 새 기능은 `origin/main` 또는 승인된 선행 작업 SHA에서
새 `task/<name>` 브랜치와 worktree를 만든다. 서로 다른 PC에서 같은 브랜치를 동시에 편집하지 않는다.
인계 전 현재 PC에서 커밋·push를 마치고, 새 PC에서는 원격 SHA와 상태를 재조회한다.

```bash
git status --short --branch
git rev-parse HEAD
gh pr view 83 --json headRefOid,statusCheckRollup,mergeStateStatus
```

→ 로컬 HEAD와 PR headRefOid가 같아야 같은 버전의 검증 결과를 읽은 것이다.
`main` 직접 push, 자동 merge, force push, 훅 우회는 금지한다. 기존 로컬 main 문제(Issue84)를
새 PC 작업에 끌어와 reset하거나 복원하지 않는다. PR 병합은 사용자가 diff를 검토한 뒤 수행한다.

## 2. Codex와 외부 연결

Codex를 설치한 뒤 해당 worktree에서 `codex`를 실행하고 본인 ChatGPT 계정으로 로그인한다.
설치 경로와 OS별 안내는 [공식 Codex CLI 문서](https://learn.chatgpt.com/docs/codex/cli)를 따른다.
Codex App을 쓰는 경우에도 작업 폴더는 같은 Git worktree를 연다. Git은 코드와 문서를 옮기며,
현재 대화 세션·플러그인 로그인·OS 자동화 권한을 자동 이관하지 않는다.

이 안내 브랜치의 `.codex/skills/strict/SKILL.md`와 `.codex/skills/codeaudit/SKILL.md`에는 현재
사용한 지침의 원문을 보존했다. 실제 작업 worktree에서 실행할 때도 이 두 파일을 읽도록 아래 재개
프롬프트가 지시한다. 도구가 프로젝트 스킬을 자동 발견하지 않으면 파일을 직접 읽고 적용한다.
전역 설정 전체나 인증 파일을 복사하지 않는다. 저장소에 필수 정본이 없는 상태를 승인·검증 완료로
바꾸지 않는다. 외부 V1 검토에는 별도로 인증한 Claude Code가 필요하다.
[Claude Code 공식 시작 안내](https://code.claude.com/docs/en/quickstart)에 따라 설치·로그인하고 계정·모델 가용성을 확인한다.
홈 폴더 전용 `brief-lint.sh`는 선택 형식 검사다. 없으면 미실행 사유와 사람 검토를 기록하고 통과를 꾸미지 않는다.
OMX를 사용하는 환경은 설치된 OMX의 공식 설치 절차로 준비하고 `omx doctor`로 상태를 확인한다.
Codex App에서 OMX 런타임 상태가 없으면 실행 중인 OMX 팀이 이어졌다고 가정하지 않는다.

ClickUp·Gmail 커넥터는 새 PC 세션에서 연결 상태를 확인한다. 실제 대상 포지션은 사용자에게
이미 받은 ClickUp 카드다. 본인에게 보낸 인계 메일의 대상 카드 링크를 사용하며,
카드 링크 자체가 이 Git 문서에 없다는 이유로 프로젝트 생성 승인을 다시 묻지 않는다. 카드 원문과 JD는
인증된 ClickUp 조회로 다시 확보한다. 운영 입력값은 아래 보호 데이터와 같은 경계로 취급한다.

Aside는 [공식 다운로드](https://aside.com/download)에서 받아 Applications에 설치한다.
현재 PC에서 확인한 앱 식별자는 `at.studio.AsideBrowser`, 버전은 1.0.813.1이다. 이 버전을
새 PC에 강제로 고정하지 말고 실제 설치된 앱을 확인한다. 설치 뒤 공식 제어 경로로 앱 식별·무변경 읽기부터 다시 확인한다.
이 PC의 PID·포트·탭 수·확장 device ID를 복사해 고정하지 않는다. RPS는 기존 실프로필,
잡코리아·사람인은 전용 프로필이라는 계약을 유지한다. 인증·로그인·OS 자동화 허가는 새 환경에서
실제 필요할 때 본인이 완료한다. Chrome의 창·탭·입력·설정·프로필은 제어하지 않는다.
Windows/Linux의 Aside 및 OS 격리 지원은 이 작업에서 검증하지 않았다. 해당 OS의 코드 시험과
브라우저 운영 가능 여부를 별도로 확인하며 Chrome 대체 자동화로 우회하지 않는다.

## 3. GitHub로 옮기지 않는 것

`.env`, `.secret-patterns`, 키, 토큰, 쿠키, 브라우저 프로필, 후보 원문/캡처/연락처,
JD·운영 프로젝트 입력 원문, SQLite DB, 보호 감사 원출력은 Git·PR·이메일에 넣지 않는다.
예외로 본인이 제공한 실행 대상 ClickUp 카드 링크는 본인 인계 메일에만 넣어 새 세션에서 대상을 회수한다.
그 링크를 후보 원문·인증 정보·RPS 프로젝트 매핑 원문을 전달할 권한으로 확대하지 않는다.
`.secret-patterns.default`는 저장소의 기본 검사 기준이고 로컬 `.secret-patterns`의 실제 리터럴을
대신하지 않는다. 실제 로컬 비밀 패턴이 필요한 검사는 보호 경로로 재설정한 뒤 실행한다.
빈 파일을 만들어 준비 완료로 처리하거나 실패한 검사를 우회하지 않는다.

원본 SQLite·암호화 파일·키가 필요한 운영 재개는 별도 보호 전송과 권한/독립 readback 확인이 필요하다.
원본을 두 PC에서 동시에 쓰지 않는다. 같은 UID의 다른 Codex 세션은 OS 쓰기 권한 격리가 아니다.
이메일에는 코드 링크, 설정 절차와 본인이 제공한 실행 대상 카드 링크를 전달한다.

## 4. 작업 상태와 다음 순서

아래는 9월 14일 인계 준비 중 확인한 상태다. 전달 시점의 원격 상태는 PR에서 다시 조회한다. `AUDITED`, `LOCAL_COMMITTED`, CI 성공,
main 병합, 실제 사이트 실증은 각각 다른 상태다. 미병합 선행이 있으면 라이브는 `NOT_RUN`이다.

| 작업 | 브랜치 / PR | 현재 확인 범위 | 다음 작업 |
|---|---|---|---|
| HS13 결함 6건 | `task/hs-13-stack-20260910` / [#83](https://github.com/sangmokang/Valuehire_v6/pull/83) | 2acc828, 독립 반례 4개 차단·격리 변이 2개 검출·새 clone 805 tests | CI 동시 시험 실패·낮은 명시 부채 2건 수정 및 외부 감사 중 |
| HS01.02 handshake | `task/hs-cdp-handshake-proof` / [#54](https://github.com/sangmokang/Valuehire_v6/pull/54) | c308eb0, 222 tests·외부 문서 감사·CI 2개 성공 | 사용자 diff 검토·병합; 실제 Aside 신원 증명은 별도 |
| HS02.01 증거 | `task/hs-resume-evidence-contract` / [#85](https://github.com/sangmokang/Valuehire_v6/pull/85) | 443631e, 외부 V1·독립 V2 문서 승인·CI 2개 성공 | 사용자 검토·병합 |
| HS02.02 증거 입력 검증 | `task/hs-0202-evidence-validation-20260914` | e02f544, 잘못된 배열·객체/개인정보 경로 반례와 null 변이 수정 | 재감사·변이 시험·원격 전달 진행 |
| HS05.01 Aside 정책 | `task/hs-0501-aside-policy-20260914` / [#86](https://github.com/sangmokang/Valuehire_v6/pull/86) | 18fc1b4 CI 2개 성공; 10e9eec 외부 V1·독립 V2 정정 확인 | 10e9eec 원격 전달 중; runtime 권한 증명은 별도 |
| HS11.04a RPS 계약 | `task/hs-1104a-rps-project-contract-20260914` / [#88](https://github.com/sangmokang/Valuehire_v6/pull/88) | 15534a1, 외부 V1·독립 V2 문서 승인·CI 2개 성공 | 사용자 검토·병합 |
| HS11.04b 로컬 확보 판정 | `task/hs-1104b-rps-resolution-20260914` / [#87](https://github.com/sangmokang/Valuehire_v6/pull/87) | e041e8f, 신원·매핑 반례 수정·232 tests | 훅 우회 사용 사실 확인; 실패 원인 재검증·외부 감사·현재 CI |
| HS04.01 저장 정책 | `hs-0401-storage-policy-contract-20260914` / [#89](https://github.com/sangmokang/Valuehire_v6/pull/89) | 16d2f07 CI 2개 성공; 5228555 외부 Sonnet V1 지적 수정 | 5228555 원격 전달·현재 CI 확인 중; Draft |
| HS11.03 LinkedIn 저장 개정 | `task/hs-1103-linkedin-storage-contract-20260914` / [#90](https://github.com/sangmokang/Valuehire_v6/pull/90) | e9e91e4, 외부 V1·독립 V2·CI 2개 성공 | §16 runtime 시험 NOT_RUN이므로 Draft |
| HS11 채널 순서 | `task/hs-11-channel-order-20260914` | 잡코리아 공통 선행/사람인 전용 선행 분리 초안 | 검토 지적 수정·검증·원격 전달 진행 |

→ 표의 각 행은 별도 작업이다. PR이 열렸다는 이유만으로 병합·운영 완료가 되지 않는다.
PR89의 원격 브랜치는 실제로 `task/` 접두가 없다. 위 표는 그 실제 이름을 쓴다.
선행 PR 위에 쌓인 변경은 #85 다음 #89·증거 입력 검증, #86 다음 #90, #88 다음 #87 순서로
검토한다. 사용자 병합 후 자식 PR의 base·diff·현재 SHA 검사를 다시 확인하며 자동 병합하지 않는다.
HS02.03 전체/부분 계산은 `task/hs-0203-evidence-coverage-20260914`의 로컬 후보 작업으로 착수했다.
원격 PR이 없는 동안 다른 PC에서 복원 완료로 간주하지 않는다.
후속은 HS02.02 입력 검증 마무리·HS02.03 전체/부분 계산 → HS03 단일 SQLite/암호화/의도·재조회 → HS04 독립 실행기 →
HS05 사용권/STOP·HS06 checkpoint/후보 잠금 → 채널별 로컬 구현·필수 병합 확인 → 잡코리아/RPS 실증이다.
RPS 프로젝트 생성·필터 업데이트는 명시적 쓰기 경계에서 재조회·중복 방지를 검증한다.
사람인 미결제는 사용자 정보이며 목록/검색/상세 제한은 아직 실측하지 않았다.
Discord, Supabase/ClickUp 결과 연동, 회사 조사, JD 3버전, 팀메일·InMail 초안, 반복 운영 목표는 유지한다.

## 5. 새 세션에 붙여 넣기

```text
docs/engineering/humansearch-cross-pc-handoff-2026-09-14.md와
docs/engineering/humansearch-execution-prompt-v5-2026-09-14.md를 끝까지 읽고 이어서 실행하라.
docs/engineering/humansearch-hs13-followup-source-2026-09-12.md는 과거 원문이다.
9월 14일 최신 사용자 결정과 후속 지시가 충돌하는 과거 제한·작성자·절대경로·SHA보다 우선한다.
과거 /Users/kangsangmo/Desktop/Valuehire_v6 경로는 현재 clone 루트로 치환하라.
Desktop의 두 프롬프트는 위 저장소 문서로 회수하라.
HS00~12 장부와 kickoff는 이 안내 브랜치의 docs/engineering/ 경로에서 회수하라.
나머지 goal/SOT는 담당 원격 브랜치에서 확인하라.
RPS 프로젝트 생성·기존 필터 업데이트 승인을 다시 묻지 말고 Aside만 제어하라.
Chrome 업무에 간섭하지 말고 후보 접촉·팀메일 발송·자동 merge는 실행하지 마라.
이 안내 브랜치의 .codex/skills/strict/SKILL.md와 .codex/skills/codeaudit/SKILL.md도 읽고 적용하라.
다른 worktree라면 clone 루트의 안내 브랜치 경로에서 위 지침을 회수하라.
경로가 없으면 git show origin/task/hs-cross-pc-handoff-20260914:.codex/skills/strict/SKILL.md
형식으로 Git 원문을 읽고 codeaudit도 같은 방식으로 회수하라.
실행 대상은 인계 메일에 보존된 사용자 제공 ClickUp 카드 링크로 회수하라.
현재 원격 SHA·작업 소유권·검증·필수 병합 상태를 조회하고, 실패 기록을 보존하며
독립적으로 가능한 구현·검증·커밋·PR을 계속하라. 미검증 항목은 완료로 보고하지 마라.
```

→ 위 프롬프트는 현재 작업 소유권과 원격 상태를 다시 확인한 뒤 이어가도록 지시한다.

## 6. 인계 복원 시험

같은 macOS에서 기존 작업 폴더와 별개로 GitHub를 새로 clone했다. 인계 브랜치 0d53074의 문서/지침
8개를 열어 원격 SHA와 로컬 내용 일치를 확인하고 hooks 설치·설정 readback을 통과했다.
그 clone에서 PR83의 2acc828을 새 worktree로 복원하여 `uv sync --locked`, pytest 805개, Ruff,
mypy 85파일, `git diff --check`, `verify.sh`를 통과했다. 이는 실제 다른 PC·새 계정·Aside
운영 시험이 아니다. PR83에서는 별도 CI 동시 실행 시험 실패도 관측되어 수정 중이므로 이 성공
1회로 그 실패를 지우지 않는다. 보호 데이터·인증·브라우저 프로필은 복사하지 않았다.
