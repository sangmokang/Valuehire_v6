# GitHub Actions GITHUB_ENV / GITHUB_PATH official adjudication sources

Request type: Comprehensive research.

Version/date context: Retrieved 2026-09-10 KST. GitHub Docs are living docs. Runner source links are pinned to `actions/runner` commit `0e345bcaa292fea27a2f218c0edab3d3b93e1060` from `main` at retrieval time.

## Direct Answer

- `echo "BASH_ENV=..." >> "$GITHUB_ENV"` is supported for subsequent steps. It is not documented as prohibited, and runner source only blocks `NODE_OPTIONS` in the `GITHUB_ENV` file-command handler.
- The step that writes to `$GITHUB_ENV` does not see the new value. Later steps in the same job do.
- Because Bash reads `BASH_ENV` for non-interactive shells, a later GitHub Actions `run` step whose effective shell is non-interactive Bash can be affected by a prior step writing `BASH_ENV=...` to `$GITHUB_ENV`.
- `echo /some/dir >> "$GITHUB_PATH"` prepends that directory to `PATH` for subsequent steps, not the current step.
- Runner source supports two relevant `GITHUB_PATH` effects for later non-container `run` steps:
  - the runner uses the accumulated prepend path when resolving the shell command with `WhichUtil.Which(...)`;
  - the runner also injects the prepended path into the step process environment, so commands inside the script, such as `bash verify.sh`, use the updated `PATH`.
- Therefore p01/p13 are real GitHub-runner effects for subsequent steps. A local one-process shell simulation that only compares `run` strings or does not process GitHub environment files between steps will miss this.

## Official Docs Evidence

- GitHub Docs: Workflow commands, setting an environment variable
  - URL: https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-commands#setting-an-environment-variable
  - Supports writing `NAME=value` lines to `$GITHUB_ENV` to create/update an environment variable for subsequent workflow steps.
  - Boundary: the writing step cannot access the new value; subsequent steps can.
  - Prohibition documented here: `$GITHUB_ENV` cannot be used to set `NODE_OPTIONS`.

- GitHub Docs: Workflow commands, adding a system path
  - URL: https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-commands#adding-a-system-path
  - Supports writing a directory path to `$GITHUB_PATH`.
  - Exact effect: prepends that directory to system `PATH` and makes it available to all subsequent actions in the current job.
  - Boundary: the currently running action cannot access the updated path variable.

- GitHub Docs: Variables reference, default environment variables
  - URL: https://docs.github.com/en/actions/reference/workflows-and-actions/variables#default-environment-variables
  - Establishes that default `GITHUB_*` and `RUNNER_*` variables cannot be overwritten.
  - Boundary: `BASH_ENV` is not a GitHub default variable in this list and is not covered by that overwrite restriction.

- GitHub Docs: Workflow syntax, step shell
  - URL: https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#jobsjob_idstepsshell
  - Establishes that a `run` step is written to a temporary file and executed by the selected shell.
  - Establishes custom shell template syntax `command [options] {0} [more_options]`, with `{0}` replaced by the temporary script path.

- GNU Bash Reference Manual: Bash Startup Files
  - URL: https://www.gnu.org/software/bash/manual/html_node/Bash-Startup-Files.html
  - Establishes that non-interactive Bash checks `BASH_ENV` in the environment, expands its value, and reads/executes the named file.
  - Boundary: Bash does not use `PATH` to search for the `BASH_ENV` file.

## Source-Reference Evidence

Official docs do not enumerate the full internal runner file-command implementation, so runner source is used for the exact `GITHUB_ENV` blocklist and command lookup/PATH application.

- `actions/runner`: `FileCommandManager.cs`, `SetEnvFileCommand`
  - URL: https://github.com/actions/runner/blob/0e345bcaa292fea27a2f218c0edab3d3b93e1060/src/Runner.Worker/FileCommandManager.cs#L160-L218
  - Establishes runner parsing of `$GITHUB_ENV`: it iterates key/value pairs, checks `_setEnvBlockList`, and only the blocklist entry shown is `NODE_OPTIONS`.
  - Establishes non-blocked variables are written into global environment variables for later execution context.

- `actions/runner`: `FileCommandManager.cs`, `AddPathFileCommand`
  - URL: https://github.com/actions/runner/blob/0e345bcaa292fea27a2f218c0edab3d3b93e1060/src/Runner.Worker/FileCommandManager.cs#L127-L157
  - Establishes runner parsing of `$GITHUB_PATH`: non-empty lines are added to `context.Global.PrependPath` after removing duplicates.

- `actions/runner`: `Handler.cs`, `AddPrependPathToEnvironment`
  - URL: https://github.com/actions/runner/blob/0e345bcaa292fea27a2f218c0edab3d3b93e1060/src/Runner.Worker/Handlers/Handler.cs#L205-L233
  - Establishes the accumulated prepend paths are reversed, joined by the platform path separator, and prepended into the step `PATH` environment for non-container steps.

- `actions/runner`: `ScriptHandler.cs`, shell lookup and execution
  - URL: https://github.com/actions/runner/blob/0e345bcaa292fea27a2f218c0edab3d3b93e1060/src/Runner.Worker/Handlers/ScriptHandler.cs#L170-L288
  - Establishes `run` step shell resolution uses `ExecutionContext.Global.PrependPath` when locating default or parsed shell commands via `WhichUtil.Which(...)`.
  - Establishes the script is written to a temp file, `{0}` is formatted with that script path, and `AddPrependPathToEnvironment()` runs before executing the step process.

- `actions/runner`: `WhichUtil.cs`
  - URL: https://github.com/actions/runner/blob/0e345bcaa292fea27a2f218c0edab3d3b93e1060/src/Runner.Sdk/Util/WhichUtil.cs#L9-L129
  - Establishes `WhichUtil.Which(command, ..., prependPath)` prepends `prependPath` to the process `PATH` before searching directories for the command.

- `actions/runner`: `PathUtil.cs`
  - URL: https://github.com/actions/runner/blob/0e345bcaa292fea27a2f218c0edab3d3b93e1060/src/Runner.Sdk/Util/PathUtil.cs#L13-L33
  - Establishes `PrependPath(path, currentPath)` returns `path + separator + currentPath` unless it is already first.

## Supported / Inferred Boundaries

- Supported by official docs: `$GITHUB_ENV` changes apply to subsequent steps; `$GITHUB_PATH` prepends directories for subsequent actions/steps in the job; the current step cannot see its own just-written env/path updates.
- Supported by official docs and runner source: `NODE_OPTIONS` is prohibited via `$GITHUB_ENV`; `BASH_ENV` is not in the documented prohibition and is not in the runner blocklist at the pinned source revision.
- Supported by GNU Bash docs: if a later step is actually non-interactive Bash and has `BASH_ENV` in its environment, Bash reads that file before running the script.
- Supported by runner source: prior `$GITHUB_PATH` entries can affect runner-side shell command lookup for later non-container `run` steps and process-side command lookup inside the later script through updated `PATH`.
- Inferred for p01: an earlier unrelated step that writes `BASH_ENV=...` to `$GITHUB_ENV` can affect later Bash-backed `run` steps on GitHub Actions, even if a local shell simulation with the same `run` strings does not.
- Inferred for p13: an earlier unrelated step that writes a fakebin directory to `$GITHUB_PATH` can affect later `bash ...` command lookup on GitHub Actions. On non-container hosted Linux/macOS jobs, this can affect both runner shell resolution and commands executed inside the step script, depending on effective shell configuration and command names.

## Reusable Takeaway

For V1/V2 adjudication, treat `$GITHUB_ENV` and `$GITHUB_PATH` writes in earlier steps as part of the later step execution surface. A parser/checker that only compares later `run` strings is unsound: GitHub Actions processes environment files between steps, and the runner plus Bash startup rules can change later behavior without changing the later `run` body.
