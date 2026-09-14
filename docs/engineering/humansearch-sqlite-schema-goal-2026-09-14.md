# HS-03.01 SQLite schema/migration goal

## Scope

Install only the empty local SQLite source schema for HumanSearch storage under an explicitly supplied Git-outside protected root. This WU owns migration mechanics, root/file permission checks, symlink/root-escape refusal, schema idempotency, and transaction atomicity.

It does not write actual candidates, choose encryption algorithms or keys, implement storage intents/outbox, implement readback, or compute evidence coverage completeness. HS-02.03 owns coverage calculation. HS-03.03 owns encryption/key contracts. HS-03.04 owns intent/file/readback wiring.

## Owned files

- `humansearch/src/humansearch/storage_schema.py`
- `humansearch/tests/test_hs_0301.py`
- `docs/engineering/humansearch-sqlite-schema-goal-2026-09-14.md`

## Contract

- Given an explicit protected root outside the Git worktree, initialize a single SQLite DB at `humansearch.sqlite3`.
- Create root with mode `0700` and DB file with mode `0600`; reject wider modes, owner mismatch, symlink root, symlink DB, and DB filename path escape.
- Keep SQLite journal sidecars inside the same protected root and set temp storage to memory for initializer-owned SQLite connections. SQLite `temp_store` is connection-local, so tests assert the durable sidecar boundary rather than expecting a new connection to remember that PRAGMA.
- Apply forward migrations idempotently. Supported migration input range is N-1 because the first runtime version migrates empty version `0` to current version `1`.
- Migration failure is atomic: a failing migration must not leave partially created HS tables recorded as usable schema.
- Store only non-sensitive refs, hashes, HMAC-shaped keys, and encrypted payload reference pointers. Do not add raw candidate body, raw contact, raw URL, plaintext key, token, cookie, or session columns.
- Use stdlib `sqlite3` only. Do not copy invoice storage semantics; invoice DB is Supabase-origin/mirror, while HS DB is the local source of truth.

## EARS

- When the protected root does not exist, the schema initializer creates it as `0700` and creates the DB as `0600`.
- When the root or DB path is a symlink, the initializer rejects before opening SQLite.
- When a caller attempts path escape through the DB filename, the initializer rejects before file creation.
- When the initializer runs twice, the second run applies no duplicate migration and leaves the same tables.
- When a migration statement fails, the initializer rolls back the migration transaction and reports a closed `StorageSchemaError`.
- When tests inspect DB columns, no raw candidate/contact/URL/key plaintext columns exist.

## Counter-AC

1. Root under the Git worktree is accepted.
2. Root mode `0755` is accepted.
3. Symlink root or DB is followed.
4. `../escape.sqlite3` creates a DB outside the root.
5. Failed migration leaves `hs_partial` table behind.
6. Re-run inserts duplicate migration rows.
7. Candidate or evidence tables contain raw/contact/email/phone/plaintext/token columns.
8. Bad HMAC or bad SHA-256 shapes insert successfully.
9. SQLite temp files are allowed outside the protected root.
10. Goal claims OS-level isolation; this WU only checks same-UID owner/mode/symlink boundaries and does not prove independent OS execution.

## Verification

```bash
cd humansearch && uv run pytest tests/test_hs_0301.py
```

```bash
cd humansearch && uv run pytest
```

```bash
cd humansearch && uv run ruff check src tests
```

```bash
cd humansearch && uv run mypy src tests
```

## Isolation mutation evidence

Mutation runs were performed against a temporary copy of `humansearch/src/humansearch/storage_schema.py` and restored immediately after each run.

- `mode_check_disabled`: changed `if actual_mode != expected_mode:` to `if False and ...`. `test_rejects_broad_modes_and_path_escape` failed because root mode `0755` was accepted. Mutant killed.
- `no_git_guard`: disabled the Git-worktree root check. `test_rejects_root_inside_git_worktree` failed because `data/hs-db` under the repo was accepted. Mutant killed.
- `allow_bad_hmac`: removed the `candidate_key_hmac` HMAC shape check. `test_schema_constraints_reject_plain_shapes_and_bad_hmac` failed because bad HMAC inserted. Mutant killed.

A weaker mutation that changed root creation from `0700` to `0755` survived because the implementation wraps creation in restrictive `umask(077)`, so the actual created mode remained `0700`. That survival is not a contract gap; the stronger mode-check-disabled mutation above verifies the enforced invariant.


## Sonnet V1 journal umask follow-up

External V1 requested a defense for SQLite rollback journal files created during `_apply_schema`. A new runtime test watches `humansearch.sqlite3-journal` during a long synthetic migration while the process umask is temporarily widened to `000`; every observed journal mode must be `0600`. On this platform the pre-fix implementation already produced `0600`, apparently because SQLite derived the journal mode from the DB file, but `_apply_schema` is now also wrapped in `umask(077)` so sidecar creation does not depend on that SQLite behavior.
