# HumanSearch G3 Product Contracts Goal — 2026-09-14

## Scope

Recover the two product literals that remained after PR13 without merging the old
57-commit branch:

- CDP read method name for the HumanSearch read-only transport.
- Non-loopback bind host samples for the local admin shadow dashboard.

## Acceptance

- The CDP transport consumes `contracts/humansearch/cdp-protocol.json`.
- The admin shadow server tests consume
  `contracts/admin-weekly-dashboard/non-loopback-host-samples.json`.
- No browser, operating data, CI wiring, or wider portal-detection behavior is changed.
- Re-running this work unit does not recreate duplicate contract files.
- The isolated mutation harness may run copied sources without the repository-level
  contract tree. The runtime fallback still reads JSON data from a packaged mirror of the
  same CDP contract so unrelated fake-CDP tests do not fail for file-copy reasons.

## Integration Note

PR54 already changes `humansearch/src/humansearch/_cdp.py` for handshake protection and is
not merged into `origin/main` at this work unit's base. This work intentionally keeps only the
G3 product-contract extraction on `origin/main`; a later integration must verify both the PR54
handshake protection and this CDP method contract after the branches are combined.
