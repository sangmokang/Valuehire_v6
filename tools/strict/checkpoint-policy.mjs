function flattenStrings(value) {
  if (typeof value === "string") return [value];
  if (Array.isArray(value)) return value.flatMap(flattenStrings);
  return [];
}

export function scopesFromWu(entry) {
  return [
    ...flattenStrings(entry?.scope),
    ...flattenStrings(entry?.scopes),
    ...flattenStrings(entry?.files),
    ...flattenStrings(entry?.paths),
  ];
}

function normalizedSet(values, label) {
  if (!Array.isArray(values) || values.some((value) => typeof value !== "string" || value.length === 0)) {
    throw new Error(`${label} must contain non-empty strings`);
  }
  const unique = [...new Set(values)].sort();
  if (unique.length !== values.length) throw new Error(`${label} contains duplicate entries`);
  return unique;
}

export function secureLedgerScopes({ runId, wuId, cliScopes, readIndex }) {
  if (!/^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$/.test(runId ?? "")) {
    throw new Error("run id contains unsupported characters");
  }
  if (!wuId || typeof wuId !== "string") throw new Error("--wu-id is required with --run-id");

  const path = `.strict/run-ledger/${runId}.json`;
  let text;
  try {
    text = readIndex(path);
  } catch {
    throw new Error(`${path} is not present in the Git index`);
  }

  let parsed;
  try {
    parsed = JSON.parse(text);
  } catch (error) {
    throw new Error(`${path}: invalid JSON (${error.message})`);
  }
  if (parsed?.run_id !== runId) {
    throw new Error(`${path}: run_id mismatch (expected ${runId})`);
  }
  if (!Array.isArray(parsed.wus)) throw new Error(`${path}: wus must be an array`);
  const matches = parsed.wus.filter((entry) => entry?.id === wuId);
  if (matches.length > 1) throw new Error(`${path}: duplicate WU id ${wuId}`);
  if (matches.length === 0) throw new Error(`${path}: WU id ${wuId} not found`);

  const ledgerScopes = normalizedSet(scopesFromWu(matches[0]), "ledger scope");
  if (ledgerScopes.length === 0) throw new Error(`${path}: WU ${wuId} has no declared scope`);
  if (cliScopes.length > 0) {
    const normalizedCli = normalizedSet(cliScopes, "CLI scope");
    if (JSON.stringify(normalizedCli) !== JSON.stringify(ledgerScopes)) {
      throw new Error(
        `CLI scope does not match indexed ledger scope (CLI=${normalizedCli.join(", ")} ledger=${ledgerScopes.join(", ")})`,
      );
    }
  }
  return { path, scopes: ledgerScopes };
}
