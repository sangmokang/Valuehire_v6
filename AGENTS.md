# Project Agent Operating Rule

## Autonomous hurdle removal

- The agent owns ordinary development hurdles end to end. Resolve tool installation,
  environment setup, dependency problems, test failures, Git/GitHub operations,
  browser recovery, and CI investigation without asking the user to drive them.
- Before requesting user input, exhaust safe read-only diagnosis and every reversible,
  in-scope remediation available in the current environment.
- Do not ask the user to run commands, copy values, navigate routine screens, retry
  ordinary operations, or choose an implementation detail that the repository and
  evidence can determine.
- When an operating-system or provider security boundary requires a human-only action,
  open the exact screen when possible, reduce the request to one explicit action, and
  resume automatically as soon as the boundary clears.
- Never interpret autonomy as permission to bypass verification, weaken tests, evade
  authentication or safety controls, expose secrets or personal data, perform an
  irreversible external action, or expand beyond the user's requested outcome.
- Report blockers only after concrete attempts and evidence. Keep unrelated user work
  intact, and prefer the smallest fix that restores real implementation testing.
