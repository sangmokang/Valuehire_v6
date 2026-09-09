# GitHub Actions shell/env/concurrency official sources

Request type: Comprehensive research.

Version/date context: Retrieved 2026-09-10 KST. GitHub Actions docs are living docs. GNU Bash manual is Edition 5.3, last updated 2025-05-18, for Bash 5.3.

## Direct answer

- `run` string equality alone does not prove the actual invocation. GitHub writes a `run` step to a temporary script and invokes it through the selected shell command template.
- For built-in bash, explicit `shell: bash` is documented as `bash --noprofile --norc -eo pipefail {0}`. On Linux/macOS with no shell specified, GitHub documents `bash -e {0}` if bash is found, falling back to `sh -e {0}` if not.
- A custom step shell can be a template string such as `command [options] {0} [more_options]`; GitHub treats the first whitespace-delimited word as the command and inserts the temporary script path at `{0}`. Therefore `shell: bash {0}` or another template changes the real invocation while leaving the `run` body text unchanged.
- `defaults.run.shell` can be set at workflow or job level for all `run` steps. The most specific default wins: job defaults override workflow defaults, and a step-level `shell` overrides defaults.
- `env` can be set at workflow, job, or step level; the most specific env wins. If `BASH_ENV` is present in the environment of a non-interactive Bash process, Bash expands its value and reads/executes that file before running the script, without using `PATH` to find it. Thus workflow/job/step `env.BASH_ENV` can affect Bash startup if the actual shell invocation is Bash and it is non-interactive.
- GitHub workflow/job `concurrency` allows at most one running and one pending workflow run or job in the same concurrency group. A newly queued run/job in the same group cancels the existing pending one. `cancel-in-progress: true` also cancels the currently running run/job in that group. Group names are case-insensitive and ordering is not guaranteed.
- `jobs.<job_id>.timeout-minutes` is the maximum minutes before GitHub automatically cancels the job; default is 360. If runner execution limits are lower, those limits win. Step `timeout-minutes` kills the step process, max 360, positive integers only.

## Official docs evidence

- GitHub Docs, Workflow syntax for GitHub Actions: `defaults.run` / `defaults.run.shell`
  - URL: https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#defaultsrun
  - URL: https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#defaultsrunshell
  - Establishes workflow-level default `shell` and `working-directory` for all `run` steps; job-level defaults can also set these; more-specific settings override less-specific settings.
  - Establishes built-in shell invocations, including unspecified Linux/macOS shell as `bash -e {0}` or fallback `sh -e {0}`, and explicit `bash` as `bash --noprofile --norc -eo pipefail {0}`.

- GitHub Docs, Workflow syntax for GitHub Actions: `jobs.<job_id>.steps[*].shell`
  - URL: https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#jobsjob_idstepsshell
  - Establishes step-level shell selection and custom shell templates. Custom shell syntax is `command [options] {0} [more_options]`; GitHub inserts the temporary script filename at `{0}`.

- GitHub Docs, Workflow syntax for GitHub Actions: `env`, `jobs.<job_id>.env`, `jobs.<job_id>.steps[*].env`
  - URL: https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#env
  - URL: https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#jobsjob_idenv
  - URL: https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#jobsjob_idstepsenv
  - Establishes workflow/job/step env scope and precedence: step env overrides job/workflow env while the step executes; job env overrides workflow env while the job executes.

- GNU Bash Reference Manual, Bash Startup Files
  - URL: https://www.gnu.org/software/bash/manual/html_node/Bash-Startup-Files.html
  - Establishes that Bash 5.3 non-interactive startup checks `BASH_ENV`, expands it, and reads/executes the named file as if `. "$BASH_ENV"` had run; it does not search `PATH` for that filename. Also establishes that `--noprofile` inhibits login startup files and `--norc` inhibits interactive `~/.bashrc`, but those flags are separate from `BASH_ENV` non-interactive behavior.

- GitHub Docs, Workflow syntax for GitHub Actions: `concurrency`, `jobs.<job_id>.concurrency`
  - URL: https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#concurrency
  - URL: https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#jobsjob_idconcurrency
  - Establishes workflow-level and job-level concurrency groups, one-running/one-pending semantics, pending replacement, optional `cancel-in-progress`, case-insensitive group names, and arbitrary ordering.

- GitHub Docs, Workflow syntax for GitHub Actions: `jobs.<job_id>.timeout-minutes`, `jobs.<job_id>.steps[*].timeout-minutes`
  - URL: https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#jobsjob_idtimeout-minutes
  - URL: https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#jobsjob_idstepsstep_idtimeout-minutes
  - Establishes job timeout default 360 minutes and automatic cancellation; step timeout kills the process, max 360, positive integer only.

## Source-reference evidence

None used. Official GitHub Actions and GNU Bash documentation were sufficient.

## Caveats / ambiguity flags

- GitHub docs are living docs; pin findings to retrieval date if using them in an audit report.
- `BASH_ENV` impact depends on actual invocation being Bash and non-interactive. A checker must resolve effective shell from step `shell`, job `defaults.run.shell`, workflow `defaults.run.shell`, and platform default before claiming whether `BASH_ENV` can affect startup.
- `bash --noprofile --norc` does not disable `BASH_ENV` for non-interactive Bash per GNU Bash startup-file rules.

## Reusable takeaway

To prove a GitHub Actions step's real command surface, inspect the effective shell template and env scope, not just `run`. The meaningful invocation is `effective_shell_template` plus the temporary script path at `{0}` plus effective env such as `BASH_ENV`; concurrency and timeout semantics are separate workflow/job controls that can change execution/cancellation without changing the `run` string.
