# herdr 도입 — 설치·사용법·Valuehire 적용 아키텍처·운영 원칙

작성: 2026-10-04 · 대상 버전: herdr 0.9.3 (stable, Windows native) · 라이선스: Apache-2.0
출처: https://github.com/herdrdev/herdr (구 `ogulcancelik/herdr`, 이전 글에 남은 AGPL 표기는 옛 정보) · https://herdr.dev/docs

## 1. herdr가 무엇인가

코딩 에이전트용 터미널 멀티플렉서(tmux 계열)다. Rust 단일 바이너리이고 Electron 없이 기존 터미널 안에서 돈다.

- **백그라운드 서버 + 클라이언트**: 창을 닫거나(`ctrl+b q`) SSH가 끊겨도 pane은 계속 돈다. `herdr`로 다시 붙는다.
- **에이전트 상태 인식**: pane마다 `working / blocked / done / idle / unknown`을 표시한다. 승인 대기(blocked)인 에이전트를 찾으러 다닐 필요가 없다.
- **에이전트가 herdr를 조종**: CLI·소켓 API로 pane 생성, 명령 실행, 출력 읽기, 다른 에이전트에게 prompt 보내기, 상태가 바뀔 때까지 대기를 할 수 있다. Claude가 Codex 세션을 부릴 수 있다.
- **worktree 1급 지원**: `herdr worktree create`가 git worktree를 만들고 그 자리를 워크스페이스로 연다.

사용자가 붙여준 그림의 구조 그대로다.

```
                    HERDR (백그라운드 서버, 세션 1개)
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
   Workspace A    Workspace B   Workspace C        ← 작업 1개 = worktree 1개 = task/<name> 브랜치
   (작업 X)       (aisearch)    (버그 수정)
        │
   ┌────┼──────┐
   ▼    ▼      ▼
 coder review  test                                ← pane 라벨
 Claude Codex  셸(verify.sh)
   │    │      │
 working blocked idle                              ← herdr가 감지하는 상태
```

## 2. 설치 (2026-10-04 이 PC에서 실제 수행)

| 단계 | 명령 | 결과·위치 |
|---|---|---|
| 본체 | `powershell -ExecutionPolicy Bypass -c "irm https://herdr.dev/install.ps1 \| iex"` (설치기는 SHA-256 검증, 사용자 PATH만 수정) | `%LOCALAPPDATA%\Programs\Herdr\bin\herdr.exe` (실제 릴리스는 `%USERPROFILE%\.herdr\packages\standalone\releases`) |
| Claude 연동 | `herdr integration install claude` | `~/.claude/hooks/herdr-agent-state.ps1` + `~/.claude/settings.json`에 `SessionStart` 훅 1개 |
| Codex 연동 | `herdr integration install codex` | `~/.codex/herdr-agent-state.ps1`, `~/.codex/hooks.json`, `config.toml`의 `[features] hooks = true` |
| 에이전트 스킬 | `herdr --skill > ~/.claude/skills/herdr/SKILL.md` | Claude가 herdr pane 안에서 herdr CLI를 쓰는 법 (`HERDR_ENV=1`일 때만 동작) |
| 설정 | `tools/herdr/config.example.toml` → `%APPDATA%\herdr\config.toml` | 한글 IME 대응, 세션 복원 |

- 설치 전 원본 백업: `%USERPROFILE%\.herdr-backup-20261004\` (claude-settings.json, codex-config.toml).
- Claude 훅은 `HERDR_ENV=1`이 아니면 즉시 `exit 0` 한다 → **herdr 밖의 일반 Claude 세션에는 영향 없음**.
- Codex는 새 훅을 처음 볼 때 "Hooks need review" 화면을 띄운다. 우리가 설치한 herdr 훅 1개이므로 `Trust all and continue`를 고른다(최초 1회).
- macOS 다른 PC: `brew install herdr` 후 위 연동·스킬·설정 단계를 같게 반복한다 (설정 경로만 `~/.config/herdr/config.toml`).

### 되돌리기

```powershell
herdr integration uninstall claude; herdr integration uninstall codex
Remove-Item -Recurse $env:USERPROFILE\.claude\skills\herdr, $env:APPDATA\herdr
# 본체: %USERPROFILE%\.herdr 와 %LOCALAPPDATA%\Programs\Herdr 삭제, 사용자 PATH에서 해당 항목 제거
```

## 3. 사용법

### 3.1 사람이 쓰는 TUI

Windows Terminal에서 저장소 루트로 가서 `herdr`. 기본 prefix는 `ctrl+b`.

| 동작 | 키 |
|---|---|
| 새 워크스페이스 / 워크스페이스 전환 | `ctrl+b` `shift+n` / `ctrl+b` `w` |
| 새 탭 | `ctrl+b` `c` |
| 오른쪽 / 아래 분할 | `ctrl+b` `v` / `ctrl+b` `-` |
| 새 worktree 워크스페이스 | `ctrl+b` `shift+g` |
| 알림 대상(멈춘 에이전트)으로 이동 | `ctrl+b` `o` |
| 복사 모드 / 분리(detach) / 단축키 전체 | `ctrl+b` `[` / `ctrl+b` `q` / `ctrl+b` `?` |

붙여넣기는 `ctrl+shift+v`. 마우스로 클릭·드래그·분할 조절도 된다. 끝낼 때(모든 pane 종료)만 `herdr server stop`.

### 3.2 스크립트·에이전트가 쓰는 CLI (요지)

```bash
herdr workspace create --cwd <dir> --label <name> --no-focus   # JSON 응답의 .result.root_pane.pane_id 사용
herdr pane split <pane> --direction right --no-focus
herdr pane run <pane> "<command>"
herdr pane wait-output <pane> --regex '^DONE$' --timeout 60000
herdr agent start reviewer --kind codex --pane <pane> -- --no-daemon --sandbox read-only
herdr agent prompt reviewer "<text>" --wait --timeout 600000
herdr agent read reviewer --source recent-unwrapped --lines 400
herdr agent wait reviewer --until blocked
herdr agent list
```

ID는 예측하지 말고 생성 명령의 JSON 응답에서 꺼낸다. 전체 목록: `herdr --help`, https://herdr.dev/docs/cli-reference/

## 4. Valuehire 적용 아키텍처

### 4.1 매핑 원칙

| herdr 개념 | Valuehire 규칙 | 근거 |
|---|---|---|
| 세션 | PC당 기본 세션 1개 (`herdr`) | 세션을 쪼개면 `status`가 전체를 못 본다 |
| 워크스페이스 | 작업 1개 = worktree 1개 = 브랜치 `task/<name>` = 인수 기준 1개 | `docs/sot/git-workflow.md` |
| worktree 위치 | `worktrees/<name>/` (gitignore됨) — `herdr worktree create --path`로 강제 | 같은 문서. herdr 기본값 `~/.herdr/worktrees` 쓰지 않음 |
| pane `coder` | Claude Code. strict 흐름(goal → RED → GREEN → verify)으로 구현 | strict 스킬 §5 |
| pane `review` | Codex, **매번 새 pane·새 세션·`--sandbox read-only`** | strict §6 V1: "fresh 세션 + read-only" |
| pane `test` | 셸. `verify.sh`·인수 스크립트 실행, 종료 코드를 회수 | `docs/sot/verification-commands.md` |
| 상태 | `blocked` = 사람(사장님) 판단 필요, `idle/done` = 다음 지시 가능 | herdr 상태 모델 |

리뷰어를 같은 워크스페이스에 두되 세션을 매번 새로 띄우는 이유: 구현 추론이 리뷰어에게 새지 않게 하면서(V1 독립성), 사람은 한 화면에서 구현과 판정을 나란히 본다.

### 4.2 런처 — `tools/herdr/vh-herdr.ps1`

위 규칙을 손으로 반복하지 않도록 한 파일로 고정했다.

```powershell
.\tools\herdr\vh-herdr.ps1 up                                   # 서버를 창 없이 기동
.\tools\herdr\vh-herdr.ps1 task aisearch-fix -Prompt "goal 문서 docs/engineering/x-goal.md 대로 /strict 수행"
.\tools\herdr\vh-herdr.ps1 test aisearch-fix                    # test pane에서 bash verify.sh → 종료 코드 반환
.\tools\herdr\vh-herdr.ps1 review aisearch-fix -Goal docs/engineering/x-goal.md
.\tools\herdr\vh-herdr.ps1 status                               # 전체 에이전트, blocked 먼저
.\tools\herdr\vh-herdr.ps1 done aisearch-fix                    # 미커밋 변경 있으면 거부, 브랜치는 남김
```

- `task`: `git fetch` → `herdr worktree create --branch task/<name> --base origin/main --path worktrees/<name>` → pane 3개(coder/review/test) → coder에 Claude 기동 → `-Prompt`가 있으면 지시서 파일을 만들어 전달.
- `review`: 기존 review pane을 닫고 새로 만든 뒤 Codex를 read-only로 띄워 **검토 의뢰서 파일**을 읽힌다. 의뢰서는 diff 범위·goal·출력 형식을 담고, 마지막 줄 `VH_VERDICT: PASS|FAIL`을 요구한다. 판정 줄이 없으면 무효(exit 1). 원문은 `%LOCALAPPDATA%\vh-herdr\<name>\review-*.md`에 남는다.
- `test`: 무작위 마커로 `<marker>=<exit code>` 줄을 찍게 하고 그 줄 전체가 일치할 때만 인정한다. 화면 기록은 `test-*.log`.
- 종료 코드: 0 성공 / 1 실패·FAIL·판정 누락 / 2 사용법 오류. 실패를 조용히 넘기지 않는다.

### 4.3 strict 흐름과의 연결

```
Issue → task <name> (worktree+브랜치+pane 3개)
      → coder: goal 문서 → RED 커밋 → GREEN → 커밋
      → test <name>                         (게이트 4: verify.sh exit 0)
      → review <name> -Goal <goal>          (V1: fresh·read-only Codex, VH_VERDICT)
      → V2·codeaudit (기존 절차 그대로)
      → push → PR → CI 초록 → 사장님 merge
      → done <name>
```

herdr는 **실행 위치와 관찰**을 맡고, 판정 규칙은 기존 SOT(strict·verification-commands)가 그대로 소유한다. 런처는 그 규칙을 복제하지 않고 명령만 부른다.

### 4.4 운영 형태

- **낮(자리)**: Windows Terminal 하나에 `herdr`. 작업마다 워크스페이스, 사이드바에서 blocked만 보고 개입.
- **여러 작업 병렬**: 워크스페이스 A(작업), B(aisearch), C(버그 수정)를 동시에 띄우고 `status`로 한 번에 본다.
- **자리 비움**: `ctrl+b q`로 분리. 에이전트는 계속 돈다. 돌아와 `herdr`.
- **다른 PC에서 원격(선택)**: 작업 PC에 OpenSSH 서버를 켜면 `herdr --remote <host>` 또는 `herdr machine add <host> --label office`로 한 창에서 본다. 이 PC에는 아직 SSH 서버를 켜지 않았다 (보안 결정이 필요하므로 별도 작업).

## 5. 운영 원칙 (best practice)

1. **ID는 응답에서 꺼낸다.** `w1:p2` 같은 값을 추측하지 않는다. pane을 옮기면 ID가 바뀐다.
2. **에이전트에는 `agent` 명령, 일반 프로세스에는 `pane` 명령.** 테스트·서버는 `pane run` + `pane wait-output`, 에이전트는 `agent prompt --wait` / `agent wait`.
3. **wait에는 항상 `--timeout`.** 기본은 무한 대기다.
4. **timeout ≠ 미전송.** `agent prompt`가 timeout 나도 입력은 들어갔을 수 있다. 재전송 전에 `agent read`로 확인한다(이중 지시 방지).
5. **긴 지시·리뷰 결과는 파일로.** 화면 읽기는 잘릴 수 있다. 지시는 파일 경로로 넘기고, 길어질 결과는 에이전트에게 파일로 쓰게 하거나 `--lines`를 크게 준다.
6. **리뷰어는 매번 fresh + read-only.** 같은 Codex 세션을 재사용하면 V1 독립성이 깨진다.
7. **Codex는 `--no-daemon`.** 공유 데몬이면 훅 보고가 엉뚱한 pane으로 간다(공식 문서).
8. **blocked는 사람에게.** 스크립트가 승인 다이얼로그에 자동으로 "예"를 누르지 않는다. 런처는 blocked면 멈추고 보고한다.
9. **워크스페이스 수명은 24~48시간.** 끝나면 `done`. 방치 worktree가 쌓이는 것은 git-workflow SOT가 금지한 실패 사례다.
10. **herdr 밖에서 herdr를 조종하지 않는다.** 스킬은 `HERDR_ENV=1`이 없으면 멈추게 되어 있다. 런처는 사람이 바깥 터미널에서 돌리는 도구다.

## 6. 실측으로 확인한 주의사항 (2026-10-04, Windows 11 + PowerShell 5.1)

| 현상 | 영향 | 대응 |
|---|---|---|
| `pane wait-output --match X`가 **입력한 명령줄 에코**에도 매칭 | 명령이 끝나기 전에 "완료"로 오판 | 줄 전체 정규식 `^marker=\d+$` 사용 (런처 반영) |
| `-Cmd`에 `exit N`을 쓰면 pane 셸 자체가 종료 | pane 소멸, 대기 실패 | `cmd /c exit N` 형태로. 런처는 `pane_not_found`로 즉시 실패 보고 |
| Claude 첫 실행 다이얼로그(Chrome 도구 사용 여부 등)를 herdr가 `idle`로 분류 | 다이얼로그 위에 prompt를 보내면 선택지가 눌릴 수 있음 | 새 PC·새 설정 후 첫 기동은 TUI로 붙어서 직접 답한다 |
| Codex 새 훅 신뢰 화면은 `unknown`/`working`으로 표시 | 자동 대기가 안 끝남 | 연동 설치 직후 1회 수동 신뢰 |
| PS 5.1은 네이티브 인자 안의 큰따옴표를 깨뜨림 | prompt 내용 손상 | 지시는 파일로 전달, `-Cmd`는 큰따옴표 거부 |
| PowerShell PATH에 `bash` 없음 (Git Bash는 `usr\bin`/`bin`에만) | `bash verify.sh` 실패 | 런처가 `git.exe` 위치로 Git Bash 경로를 계산 |
| 한글 IME 조합창 위치 | 기본 `host_cursor=auto`에서 어긋남 | 설정에서 `native` + prefix IME 전환 실험 기능 켬 |
| Windows에서 플러그인은 preview, `herdr terminal attach`·live handoff 미지원 | 해당 기능 사용 불가 | 쓰지 않는다 |

## 7. 검증 기록

- 설치: `herdr --version` → `herdr 0.9.3`, `herdr integration status` → `claude: current (v10)`, `codex: current (v8)`.
- 별도 세션 `HERDR_SESSION=vhtest`에서 실측: workspace/pane/split/run/wait-output/read, Codex `agent start → prompt --wait → read` 왕복 19초, `worktree create --path worktrees/<name>` → `worktree remove`.
- 런처: `status`, `task`(중복 생성 거부 포함), `test`(verify.sh PASS → exit 0 / `cmd /c exit 3` → exit 1), `review`(본 작업 브랜치에 실제 수행 — 결과는 PR 본문).
