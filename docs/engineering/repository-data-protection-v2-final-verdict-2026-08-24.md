# Repository data protection — Codex V2 final verdict

- Verdict: `PASS`
- Target: `6bb1865c703331f2560efb9110f4f94eb2a314ae`
- Captured: `2026-08-24 12:21:31 KST`
- Independent workdir: `/tmp/valuehire-rdp-v2-final.LJizVt`
- Start/end: same HEAD, clean status; no tracked file, ref, or remote changed
- Privacy: synthetic fixture literals are omitted; only safe counts and exit states follow

## Required commands

| Command | Exit | Result |
| --- | ---: | --- |
| `bash scripts/acceptance-principles-check.sh` | 0 | `PASS`, `CHECKED: 34` |
| `bash scripts/check-docs-sot.sh` | 0 | `OK` |
| `bash scripts/acceptance-secret-webhook-vendor.sh` | 0 | `PASS`, `CHECKED: 35` |
| `bash scripts/acceptance-hs-a4.sh` | 0 | `PASS`, `CHECKED: 48` |
| `bash verify.sh` | 0 | `PASS`, `CHECKED: 193` |
| `bash scripts/scan-data-exposure.sh tracked` | 0 | `PASS`, `CHECKED: 193` |
| `bash scripts/scan-data-exposure.sh history` | 0 | `PASS`, `CHECKED: 1004` |
| `bash scripts/scan-data-exposure.sh pii` | 0 | `PASS`, `CHECKED: 193` |
| `bash scripts/scan-data-exposure.sh all` | 0 | `PASS`, `CHECKED: 1390` |
| `bash scripts/acceptance-ci-step-integrity.sh` | 0 | `PASS`, `CHECKED: 14` |
| `bash scripts/acceptance-semantic-mutations.sh` | 0 | `PASS`, `CHECKED: 10` |
| `git diff --check` | 0 | no output |

## Independent attacks

- Empty `verify` and empty data targets returned `NOT_RUN`, `CHECKED: 0`, exit 2.
- Safe one- and two-target fixtures returned their actual positive `CHECKED` values.
- Deleted CSV, TSV, and SQL PII fixtures made `history`/`all` exit 1.
- Metrics CSV, one-column CSV, and schema-only SQL controls exited 0.
- Same-content safe-extension aliases did not hide a deleted PII blob.
- A CSV path containing tab, quote, and newline was detected; the diagnostic gained no structural line and contained no raw tab.
- Fixture names, email addresses, and phone numbers were absent from stdout and stderr.
- NUL removal, raw/display path swapping, PII-function splitting, zero-target guard removal, forged `CHECKED`, plaintext injection, acceptance count/call removal, 600/601 and 100/101 weakening, CI disablement, and semantic no-op mutations all made their guards fail.

## Contract verdict

AC-1 through AC-8 and counter-AC 1 through 14 passed. No executable zero-target, history-content, alias-path, nonstandard-path, non-disclosure, shared-logic, or test-integrity violation remained at the target SHA.

The live GitHub-hosted runner was not executed. Local workflow wiring, integrity mutations, and the exact commands were executed instead. Full-history inspection took several minutes; this is a performance risk, not a correctness exception.
