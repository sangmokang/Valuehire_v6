# Valuehire v6 개발 환경 이관 가이드

최종 갱신: 2026-09-22

이 문서는 새 PC, Cursor, 다른 AI 코딩 환경에서 현재 저장소를 이어받기 위한 최소 절차다. 모델별 기능이나 Grok 특정 버전 지원 여부는 이 저장소가 보장하지 않는다. 도구가 무엇이든 정본은 `docs/sot/`와 로컬 훅/CI다.

## 1. 저장소 받기

```bash
git clone --branch task/cross-pc-handoff-20260922 https://github.com/sangmokang/Valuehire_v6.git
cd Valuehire_v6
git remote -v
git branch --show-current
```

현재 원격은 `origin` 하나를 기준으로 한다. `docs/sot/git-workflow.md` 규칙상 `main` 직접 push는 금지이고, 작업은 짧은 `task/<name>` 브랜치나 worktree로 진행한다.

```bash
git worktree add worktrees/<name> -b task/<name>
```

worktree를 쓰지 않는 단순 문서 작업도 PR 단위는 작게 유지한다.

## 2. Python/uv 환경

HumanSearch 패키지는 `humansearch/` 하위 프로젝트다.

```bash
uv --version
uv sync --locked --project humansearch
```

- `humansearch/.python-version`: `3.14.1`
- `humansearch/pyproject.toml`: `requires-python >=3.14`
- `humansearch/uv.lock`: 의존성 잠금 파일
- CI HumanSearch 게이트: `uv 0.11.3`을 확인한 뒤 `uv sync --locked --project humansearch`를 실행

먼저 Git, Bash, Python 3, Ruby를 준비한다. uv가 없으면 `python3 -m pip install --user uv==0.11.3` 또는 `pipx install uv==0.11.3`으로 설치하고 실행 경로를 PATH에 추가한다. Windows에서는 심볼릭 링크와 POSIX 검사를 위해 WSL2의 Linux 파일시스템에서 clone한다. 전체 Invoice 게이트에는 PostgreSQL 서버 도구도 필요하다. 환경은 루트가 아니라 `humansearch/` 프로젝트 기준으로 맞춘다.

## 3. 로컬 훅 설치

```bash
bash scripts/install-hooks.sh
git config --get core.hooksPath
```

정상 값은 `hooks`다. 이 스크립트는 `hooks/*`와 `scripts/*.sh` 실행 권한을 보정하고, worktree에서 메인 작업트리의 `.secret-patterns`를 찾을 수 있으면 심볼릭 링크도 만든다.

## 4. 비밀/환경 파일

git에 올리지 않는 로컬 파일:

- `.env`, `.env.*`
- `.secret-patterns`
- 브라우저 로그인 세션, Aside 상태, MCP/커넥터 로그인
- `outputs/`, `artifacts/`, `data/`, SQLite DB류

`bash verify.sh`는 기본적으로 커밋된 `.secret-patterns.default`를 사용하고, 로컬 `.secret-patterns`가 있으면 함께 읽는다. 따라서 새 PC에서 기본 비밀 스캔과 pre-push가 곧바로 `.secret-patterns` 부재로 막히지는 않는다.

단, `bash scripts/acceptance-0-2.sh`를 직접 실행하는 경우에는 `.secret-patterns`가 없거나 비어 있으면 exit 2로 실패한다. 이 검사는 로컬 전용 실제 리터럴의 히스토리 잔존 여부를 확인하는 용도라 CI에서는 합성 fixture 기반 `scripts/acceptance-0-2-unreachable-content.sh`가 등가 회귀를 맡는다.

## 5. 기본 검증 명령

레포 루트:

```bash
bash verify.sh
bash scripts/session-status.sh
python3 -m unittest discover -s tests
```

HumanSearch:

```bash
bash scripts/acceptance-hs-gates.sh
```

`acceptance-hs-gates.sh`는 `uv sync --locked --project humansearch`, pytest 수집/실행, runtime import 증명, ruff, mypy strict를 한 번에 확인한다. CI의 전체 목록은 `docs/sot/verification-commands.md`가 정본이다.

## 6. Cursor에서 열 때

Cursor가 저장소를 열면 `.cursor/rules/repository.mdc`를 먼저 읽게 둔다. 새 작업을 시작하기 전 AI에게 다음 파일을 읽으라고 지시하면 된다.

```text
README.md
docs/sot/INDEX.md
docs/sot/verification-commands.md
docs/sot/git-workflow.md
.cursor/rules/repository.mdc
```

Cursor, Grok, Codex, Claude 같은 도구의 로컬 로그인/커넥터 상태는 git으로 이관되지 않는다. 브라우저 자동화, Aside, Notion/Gmail/Drive/MCP류는 새 PC에서 각 도구를 다시 연결해야 한다.

## 7. 커밋 전 체크

```bash
git status --short
bash verify.sh
bash scripts/session-status.sh
```

코드 변경이 `humansearch/`를 건드렸다면 `bash scripts/acceptance-hs-gates.sh`도 실행한다. 루트 `tests/` 하위 스크립트 테스트를 건드렸다면 `python3 -m unittest discover -s tests`를 실행한다.

커밋 메시지는 AGENTS.md의 Lore Commit Protocol을 따른다. 첫 줄은 “무엇을 바꿨는지”보다 “왜 이 변경이 필요한지”를 적고, 필요한 경우 `Constraint`, `Confidence`, `Scope-risk`, `Tested`, `Not-tested` trailer를 붙인다.

이 이관 브랜치는 PR 검토 전 상태다. 병합 후에는 기본 `main`을 clone해도 된다.

## 선택적 실서비스 연결

`cp .env.example .env`로 빈 예시를 복사한 뒤 필요한 값만 안전하게 채운다.
테스트에는 실서비스 키가 필요 없다. `.env`는 모든 명령이 자동으로 읽는
파일이 아니다. 아카이브 설정의 `env_files` 또는 해당 도구의 프로세스 환경을
통해 명시적으로 연결한다. 별도 아카이버 서버와 SQLite/원격 데이터는 이
저장소 clone만으로 설치·복원되지 않는다.

공개 GitHub에는 후보자 이력이 담긴 기존 로컬 RPS 커밋을 포함하지 않았다.
기존 `main`과 `backup/pre-cross-pc-handoff-20260922`는 원본을 로컬에 보존한다.
다른 worktree의 독립 작업은 자동 병합하지 않았다. 전체 로컬 인벤토리는
`artifacts/cross-pc-handoff/worktree-inventory.md`에 있으며 별도 비공개 이관 대상이다.
