# Valuehire v6

Valuehire v6는 ValueConnect 채용 운영 자동화와 검증 장치를 모아 둔 저장소다. 현재 핵심 Python 패키지는 `humansearch/` 아래에 있고, 레포 루트에는 SOT 문서, 훅, 검증 스크립트, 채용/JD 보조 스크립트가 함께 있다.

처음 받는 PC에서는 아래 순서로 시작한다.

```bash
git clone --branch task/cross-pc-handoff-20260922 https://github.com/sangmokang/Valuehire_v6.git
cd Valuehire_v6
uv sync --locked --project humansearch
bash scripts/install-hooks.sh
bash scripts/session-status.sh
```

`humansearch/.python-version`은 Python `3.14.1`을 요구하고, CI의 HumanSearch 게이트는 `uv 0.11.3` 계약을 확인한다. `uv sync --locked --project humansearch`는 `humansearch/uv.lock` 기준으로 환경을 재현한다.

## 중요한 문서

- `docs/sot/INDEX.md` — 다음 세션이 먼저 읽어야 할 정본 목록
- `docs/sot/verification-commands.md` — 이 저장소에서 실제로 도는 검증 명령
- `docs/sot/git-workflow.md` — trunk-based, 짧은 `task/<name>` 브랜치, 직접 main push 금지
- `docs/engineering/development-setup.md` — 새 PC/Cursor 온보딩 체크리스트

## 자주 쓰는 검증

```bash
bash verify.sh
bash scripts/session-status.sh
bash scripts/acceptance-hs-gates.sh
python3 -m unittest discover -s tests
```

`bash verify.sh`는 커밋된 `.secret-patterns.default`와 로컬 `.secret-patterns`가 있으면 둘 다 사용한다. 로컬 `.secret-patterns`는 gitignore 대상이고, `scripts/acceptance-0-2.sh`를 직접 실행할 때 필요하다.

## 로컬에만 남는 것

`.env`, `.secret-patterns`, 브라우저 로그인 세션, Aside 상태, MCP/커넥터 로그인, 실행 산출물(`outputs/`, `artifacts/`, `data/`)은 git에 올리지 않는다. 새 PC에서는 저장소를 받은 뒤 각 도구에서 다시 로그인하거나 로컬 파일을 별도로 준비해야 한다.

AI 도구(Cursor, Codex, Claude 등)는 모델명보다 저장소의 SOT와 훅을 먼저 따라야 한다. Cursor용 기본 규칙은 `.cursor/rules/repository.mdc`에 있다.

이 이관 브랜치는 PR 검토 전 상태다. 병합 후에는 기본 `main`을 clone해도 된다.
