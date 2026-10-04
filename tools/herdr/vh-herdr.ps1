<#
vh-herdr.ps1 — Valuehire 작업을 herdr 워크스페이스로 띄우는 런처.

작업 1개 = 워크스페이스 1개 = worktree 1개 = 브랜치 1개 (docs/sot/git-workflow.md).
워크스페이스 안의 pane 3개:
  coder  : Claude Code — 구현 (strict 흐름)
  review : Codex — 적대 검증. review 명령마다 새 pane·새 세션·read-only로 다시 띄운다.
  test   : 셸 — verify.sh 등 검증 명령

사용법 (PowerShell):
  .\tools\herdr\vh-herdr.ps1 up                        # herdr 서버를 창 없이 기동
  .\tools\herdr\vh-herdr.ps1 task <name> [-Prompt <지시>] [-NoCoder]
  .\tools\herdr\vh-herdr.ps1 test <name> [-Cmd <명령>] # 기본: bash verify.sh
  .\tools\herdr\vh-herdr.ps1 review <name> [-Goal <goal 문서 경로>]
  .\tools\herdr\vh-herdr.ps1 status                    # 모든 에이전트 상태 (blocked 먼저)
  .\tools\herdr\vh-herdr.ps1 done <name>               # worktree 제거 (브랜치는 남긴다)

종료 코드: 0 성공 | 1 실패(명령 실패·검증 FAIL·판정 누락) | 2 사용법 오류.
조용한 실패 금지: herdr 호출이 실패하면 즉시 throw 한다.
#>
param(
    [Parameter(Position = 0)][string]$Command = "",
    [Parameter(Position = 1)][string]$Name = "",
    [string]$Base = "origin/main",
    [string]$Prompt = "",
    [string]$Cmd = "",
    [string]$Goal = "",
    [string]$CoderArgs = "",
    [int]$TimeoutSec = 1800,
    [switch]$NoCoder
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version 2.0

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
# worktree 안에서 실행해도 주 저장소 루트를 쓴다 (worktrees/<name> 규칙은 주 저장소 기준).
$commonDir = (& git -C $RepoRoot rev-parse --path-format=absolute --git-common-dir).Trim()
if ($LASTEXITCODE -ne 0) { throw "git 저장소가 아님: $RepoRoot" }
$RepoRoot = (Split-Path -Parent $commonDir) -replace '/', '\'

$StateRoot = Join-Path $env:LOCALAPPDATA "vh-herdr"

function Find-Herdr {
    $cmd = Get-Command herdr -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    $alias = Join-Path $env:LOCALAPPDATA "Programs\Herdr\bin\herdr.exe"
    if (Test-Path $alias) { return $alias }
    throw "herdr 미설치 — docs/engineering/herdr-adoption-2026-10-04.md 의 설치 절차를 먼저 실행"
}
$Herdr = Find-Herdr

function Invoke-Herdr {
    # herdr CLI는 성공 시 stdout에 JSON, 실패 시 stderr에 JSON + exit 1.
    $out = & $Herdr @args
    if ($LASTEXITCODE -ne 0) { throw "herdr $($args -join ' ') 실패 (exit $LASTEXITCODE)" }
    $text = ($out | Out-String).Trim()
    if ($text.StartsWith("{")) { return ($text | ConvertFrom-Json).result }
    return $text
}

function Get-Slug([string]$raw) {
    if ($raw -notmatch '^[a-z][a-z0-9-]{0,23}$') {
        throw "작업 이름은 ^[a-z][a-z0-9-]{0,23}$ (예: codeit-minfix). 받은 값: '$raw'"
    }
    return $raw
}

function Find-Workspace([string]$slug) {
    $list = Invoke-Herdr workspace list
    $hits = @($list.workspaces | Where-Object { $_.label -eq $slug })
    if ($hits.Count -gt 1) { throw "라벨 '$slug' 워크스페이스가 $($hits.Count)개 — herdr에서 정리 필요" }
    if ($hits.Count -eq 0) { return $null }
    return $hits[0]
}

function Require-Workspace([string]$slug) {
    $ws = Find-Workspace $slug
    if (-not $ws) { throw "워크스페이스 '$slug' 없음 — 먼저 task $slug 실행" }
    return $ws
}

function Find-Pane([string]$workspaceId, [string]$label) {
    $panes = (Invoke-Herdr pane list --workspace $workspaceId).panes
    $hits = @($panes | Where-Object { $_.PSObject.Properties.Name -contains "label" -and $_.label -eq $label })
    if ($hits.Count -eq 0) { return $null }
    return $hits[0]
}

function New-LabeledPane([string]$fromPane, [string]$direction, [string]$label) {
    $pane = (Invoke-Herdr pane split $fromPane --direction $direction --no-focus).pane
    Invoke-Herdr pane rename $pane.pane_id $label | Out-Null
    return $pane.pane_id
}

function Get-GitBash {
    $git = (Get-Command git -ErrorAction Stop).Source        # ...\Git\cmd\git.exe
    $bash = Join-Path (Split-Path -Parent (Split-Path -Parent $git)) "bin\bash.exe"
    if (-not (Test-Path $bash)) { throw "Git Bash 없음: $bash" }
    return $bash
}

function Get-StateDir([string]$slug) {
    $dir = Join-Path $StateRoot $slug
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
    return $dir
}

function Cmd-Up {
    $status = & $Herdr status server | Out-String
    if ($status -match 'status:\s+running') { Write-Output "herdr 서버 이미 실행 중"; return }
    # memory 규칙: cmdlet 자체의 -WindowStyle Hidden 으로 띄워야 창이 번쩍이지 않는다.
    Start-Process -FilePath $Herdr -ArgumentList "server" -WindowStyle Hidden -WorkingDirectory $RepoRoot
    for ($i = 0; $i -lt 20; $i++) {
        Start-Sleep -Milliseconds 500
        if ((& $Herdr status server | Out-String) -match 'status:\s+running') { Write-Output "herdr 서버 기동"; return }
    }
    throw "herdr 서버가 10초 안에 뜨지 않음 — 'herdr status' 확인"
}

function Cmd-Task([string]$slug) {
    Cmd-Up
    if (Find-Workspace $slug) { throw "워크스페이스 '$slug' 이미 있음 — status 로 확인" }
    $path = Join-Path $RepoRoot "worktrees\$slug"
    $branch = "task/$slug"

    & git -C $RepoRoot fetch origin --quiet
    if ($LASTEXITCODE -ne 0) { throw "git fetch 실패" }
    & git -C $RepoRoot show-ref --verify --quiet "refs/heads/$branch"
    $branchExists = ($LASTEXITCODE -eq 0)

    if (Test-Path $path) {
        # 기존 경로는 그 체크아웃이 정확히 task/<slug> 일 때만 연다 (다른 브랜치 오염 방지).
        $head = (& git -C $path rev-parse --abbrev-ref HEAD | Out-String).Trim()
        if ($LASTEXITCODE -ne 0) { throw "$path 는 git worktree 가 아님 — 직접 확인 후 정리" }
        if ($head -ne $branch) { throw "$path 의 브랜치가 '$head' (기대: $branch) — 경로 충돌, 직접 정리 필요" }
        $created = Invoke-Herdr worktree open --cwd $RepoRoot --path $path --label $slug --no-focus
    } elseif ($branchExists) {
        $created = Invoke-Herdr worktree create --cwd $RepoRoot --branch $branch --path $path --label $slug --no-focus
    } else {
        $created = Invoke-Herdr worktree create --cwd $RepoRoot --branch $branch --base $Base --path $path --label $slug --no-focus
    }
    $coderPane = $created.root_pane.pane_id
    Invoke-Herdr pane rename $coderPane coder | Out-Null
    $reviewPane = New-LabeledPane $coderPane right review
    $testPane = New-LabeledPane $coderPane down test
    Write-Output "워크스페이스 $slug — coder=$coderPane review=$reviewPane test=$testPane ($path)"

    if ($NoCoder) { return }
    $startArgs = @("agent", "start", "$slug-coder", "--kind", "claude", "--pane", $coderPane, "--timeout", "90000")
    if ($CoderArgs) { $startArgs += @("--") + ($CoderArgs -split '\s+') }
    $out = & $Herdr @startArgs
    if ($LASTEXITCODE -ne 0) {
        # agent_not_ready = 최초 실행 다이얼로그(신뢰·브라우저 도구 등). 사람이 답해야 한다.
        throw "Claude 기동 실패/대기 — herdr 로 붙어서($Herdr) coder pane의 다이얼로그에 답한 뒤 다시 지시"
    }
    if ($Prompt) {
        $brief = Join-Path (Get-StateDir $slug) "coder-task.md"
        Set-Content -Path $brief -Value $Prompt -Encoding UTF8
        # PS 5.1은 네이티브 인자 안의 큰따옴표를 깨뜨리므로, 지시문은 파일로 넘긴다.
        Invoke-Herdr agent prompt "$slug-coder" "작업 지시서 $brief 를 읽고 그대로 수행하라. 작업 위치는 $path 이다." | Out-Null
        Write-Output "coder 에 지시 전달: $brief"
    }
}

function Cmd-Test([string]$slug) {
    $ws = Require-Workspace $slug
    $pane = Find-Pane $ws.workspace_id test
    if (-not $pane) { throw "test pane 없음 (워크스페이스 $slug)" }
    $run = $Cmd
    if (-not $run) { $run = "& '$(Get-GitBash)' verify.sh" }
    if ($run.Contains('"')) { throw "-Cmd 에 큰따옴표 금지 (PS 5.1 인자 전달 결함) — 작은따옴표를 쓴다" }
    $marker = "VHX" + [Guid]::NewGuid().ToString("N").Substring(0, 8)
    # 명령줄 에코에도 마커 글자가 보이므로, 출력 줄 전체가 '<marker>=<숫자>' 인 경우만 매칭한다.
    Invoke-Herdr pane run $pane.pane_id "$run; Write-Output ('$marker=' + `$LASTEXITCODE)" | Out-Null
    $hit = Invoke-Herdr pane wait-output $pane.pane_id --regex "^$marker=(-?\d+)$" --timeout ($TimeoutSec * 1000)
    $code = [int](($hit.matched_line -split '=')[1])
    $log = Join-Path (Get-StateDir $slug) ("test-" + (Get-Date -Format "yyyyMMdd-HHmmss") + ".log")
    Set-Content -Path $log -Value $hit.read.text -Encoding UTF8
    Write-Output "test exit=$code (화면 기록: $log)"
    if ($code -ne 0) { exit 1 }
}

function Cmd-Review([string]$slug) {
    $ws = Require-Workspace $slug
    $path = $ws.worktree.checkout_path
    $old = Find-Pane $ws.workspace_id review
    $coder = Find-Pane $ws.workspace_id coder
    if (-not $coder) { throw "coder pane 없음 (워크스페이스 $slug)" }
    # strict V1: 매번 fresh 세션. 이전 reviewer pane을 닫고 새로 만든다.
    if ($old) { Invoke-Herdr pane close $old.pane_id | Out-Null }
    $pane = New-LabeledPane $coder.pane_id right review

    $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $dir = Get-StateDir $slug
    $brief = Join-Path $dir "review-$stamp-brief.md"
    $goalLine = "goal 문서 없음 — 커밋 메시지와 diff 로 의도를 추정하지 말고, 의도가 불명확하면 그 자체를 MAJOR 로 보고하라."
    if ($Goal) { $goalLine = "인수 기준(goal): $Goal — 이 문서의 AC 와 counter-AC 를 기준으로 판정하라." }
    @"
# 적대 검증 의뢰 (V1, fresh·read-only)

너는 이 변경을 승인하지 않을 이유를 찾는 리뷰어다. 구현자의 설명은 받지 않는다. 산출물만 본다.

- 저장소(worktree): $path
- 대상: git diff $Base...HEAD (브랜치 task/$slug)
- $goalLine
- 검증 명령 정본: docs/sot/verification-commands.md

절차:
1. git -C '$path' log --oneline $Base..HEAD 와 git -C '$path' diff $Base...HEAD 를 읽는다.
2. 각 변경에 대해 반증을 시도한다: 조용한 실패, 미배선(호출 경로 없음), 테스트 약화, 경계값, 되돌리기 어려운 부작용, 비밀·개인정보 노출.
3. 파일을 수정하지 않는다 (read-only).

출력 형식 (한국어):
- 발견 목록: [BLOCKER|MAJOR|MINOR] 파일:줄 — 결함 — 재현 시나리오
- 반증 시도 내역: 시도했지만 결함이 아니었던 것
- 마지막 줄은 정확히 VH_VERDICT: PASS 또는 VH_VERDICT: FAIL (BLOCKER/MAJOR 가 하나라도 있으면 FAIL)
"@ | Set-Content -Path $brief -Encoding UTF8

    $name = "$slug-review"
    Invoke-Herdr agent start $name --kind codex --pane $pane --timeout 90000 '--' --no-daemon --sandbox read-only | Out-Null
    Write-Output "reviewer 기동 ($pane). 검토 중… (최대 $TimeoutSec 초)"
    Invoke-Herdr agent prompt $name "검토 의뢰서 $brief 를 읽고 그 지시대로 검토하라." --wait --until idle --until done --until blocked --timeout ($TimeoutSec * 1000) | Out-Null
    $agent = (Invoke-Herdr agent get $name).agent
    if ($agent.agent_status -eq "blocked") { throw "reviewer 가 승인 대기(blocked) — herdr 로 붙어서 확인" }

    $text = (& $Herdr agent read $name --source recent-unwrapped --lines 3000 | Out-String)
    if ($LASTEXITCODE -ne 0) { throw "reviewer 출력 읽기 실패 (exit $LASTEXITCODE)" }
    $out = Join-Path $dir "review-$stamp.md"
    Set-Content -Path $out -Value $text -Encoding UTF8
    $verdicts = @([regex]::Matches($text, '(?m)^\W*VH_VERDICT:\s*(PASS|FAIL)\s*$') | ForEach-Object { $_.Groups[1].Value })
    if ($verdicts.Count -eq 0) { Write-Output "판정 줄 없음 — 무효 처리 (원문: $out)"; exit 1 }
    $verdict = $verdicts[-1]
    Write-Output "VH_VERDICT: $verdict (원문: $out)"
    if ($verdict -ne "PASS") { exit 1 }
}

function Cmd-Status {
    $agents = @((Invoke-Herdr agent list).agents)
    if ($agents.Count -eq 0) { Write-Output "실행 중인 에이전트 없음"; return }
    $labels = @{}
    foreach ($w in (Invoke-Herdr workspace list).workspaces) { $labels[$w.workspace_id] = $w.label }
    $order = @{ blocked = 0; working = 1; done = 2; idle = 3; unknown = 4 }
    $agents | Sort-Object { if ($order.ContainsKey($_.agent_status)) { $order[$_.agent_status] } else { 9 } } | ForEach-Object {
        $n = ""
        if ($_.PSObject.Properties.Name -contains "name") { $n = $_.name }
        [pscustomobject]@{ workspace = $labels[$_.workspace_id]; pane = $_.pane_id; agent = $_.agent; name = $n; status = $_.agent_status }
    } | Format-Table -AutoSize | Out-String | Write-Output
}

function Cmd-Done([string]$slug) {
    $ws = Require-Workspace $slug
    # 일하는 중이거나 상태를 모르는 에이전트가 있으면 지우지 않는다 (아직 디스크에 안 쓴 작업 보호).
    $busy = @((Invoke-Herdr agent list).agents | Where-Object {
        $_.workspace_id -eq $ws.workspace_id -and @("idle", "done") -notcontains $_.agent_status })
    if ($busy.Count -gt 0) {
        $desc = ($busy | ForEach-Object { "$($_.pane_id)=$($_.agent_status)" }) -join ", "
        throw "작업 중/미확인 에이전트 있음 ($desc) — 멈추거나 종료한 뒤 다시 실행"
    }
    $dirty = & git -C $ws.worktree.checkout_path status --porcelain
    if ($LASTEXITCODE -ne 0) { throw "git status 실패" }
    if ($dirty) { throw "미커밋 변경 있음 — 커밋하거나 직접 정리 후 다시 실행 (강제 삭제 안 함)" }
    Invoke-Herdr worktree remove --workspace $ws.workspace_id | Out-Null
    Write-Output "worktree 제거: $($ws.worktree.checkout_path) (브랜치 task/$slug 는 남김)"
}

switch ($Command) {
    "up"     { Cmd-Up }
    "task"   { Cmd-Task (Get-Slug $Name) }
    "test"   { Cmd-Test (Get-Slug $Name) }
    "review" { Cmd-Review (Get-Slug $Name) }
    "status" { Cmd-Status }
    "done"   { Cmd-Done (Get-Slug $Name) }
    default  { Get-Content $PSCommandPath -TotalCount 21 | Select-Object -Skip 1 | Write-Output; exit 2 }
}
