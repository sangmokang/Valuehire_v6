# Valuehire v6 agent handoff

Read `README.md`, `docs/engineering/development-setup.md`, and
`docs/sot/INDEX.md` before working. Repository SOT owns domain behavior and
verification commands; do not invent missing integrations or claim unrun checks.

- Work on a short `task/<name>` branch; preserve other worktrees and local edits.
- Use the existing hooks and CI. Do not bypass failed checks.
- Browser operations use Aside by default. Reconnect tools on each machine.
- Shared JD/search skills live under `.agents/skills/`. The `.codex/skills/`
  and `.claude/skills/` JD entrypoints use relative symlinks to that source.
- Never commit credentials, candidate records, browser sessions, or local DBs.
- No external messages or production writes without task authorization.
- Report the verified commit SHA and any remaining setup or verification gaps.

## Commit messages

Use a concise intent line explaining why, followed by relevant git trailers:
`Constraint:`, `Rejected:`, `Confidence:`, `Scope-risk:`, `Directive:`,
`Tested:`, and `Not-tested:`. Include only trailers that add decision context.
