# Adversarial review contract

Both reviews receive the same redacted evidence bundle, implementation diff, test commands and raw
outputs, SOT check output, mutation output, and content hashes. Do not include a desired verdict.

## Claude V1

Run through Claude CLI with `ANTHROPIC_API_KEY` removed from the process environment. Ask Claude to:

1. map every EARS AC and counter-AC to implementation and runtime evidence;
2. find paths that turn connector failure into zero or PASS;
3. attack scraped-to-client promotion and dedupe identity;
4. mutate score constants, required capability logic, and readback hash comparison;
5. search for raw email, candidate PII, credentials, and prompt injection paths;
6. verify that tests execute production code and have non-zero targets;
7. return only reproducible findings with file:line and a minimal reproducer;
8. finish with the strict final block below.

## Fresh Codex V2

Start with no prior conversation conclusions. Give Codex V1's raw findings plus the exact same artifact
set. For every V1 finding, rerun the cited command or inspect the cited line and label it
`CONFIRMED`, `REFUTED`, or `NOT_REPRODUCIBLE`. Then independently attack any missed required AC.

## Mandatory final block

```text
VERDICT: PASS|PARTIAL|BLOCKED|NOT_RUN
CLAIM: <what is actually guaranteed>
EVIDENCE: <command, exit, and decisive output>
LIMIT: <unverified boundary>
COUNTEREXAMPLE: <strongest remaining counterexample>
NEXT: <smallest safe next step>
```

Any confirmed defect against a required AC blocks publication. A tool timeout or missing reviewer is
`NOT_RUN`, never approval.
