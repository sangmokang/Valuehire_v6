# Declared external effects

`external-effect-contract.json` records expected effect entries as a source path
and named function (`export` is the selected function name, not an ESM export
verification). The staged checker requires each declaration to reach a supported
network-call syntax through direct local function calls or static named imports.
Removing a declaration, removing the manifest, changing an entry to an unsupported
language, or losing the supported call path blocks the commit. Migration of an
existing declaration needs a separate reviewed contract change; no expiry or
filename exemption authorizes shrinking it.

This is a bounded syntactic check. It does not prove runtime execution, a live
network request, authentication, response handling, or delivery. Branch conditions
and mocked runtime globals are not evaluated. Undeclared expected effects cannot
be inferred from intent or filenames: new expected effects must be declared in
review. A type-only file under an `api` directory has no implicit effect claim.

Supported inputs are staged regular Python and JavaScript files. Python supports
module-level functions, static absolute imports, and direct calls; nested functions,
wildcard/relative imports, and dynamic evaluation are rejected in the analyzed
entry. JavaScript supports named function declarations, direct calls, and static
named imports. Binding identifiers, including destructured bindings, conservatively
shadow matching network primitive names. Default/namespace/dynamic imports, closures,
computed calls, optional calls, and templates inside a visited function are
rejected. Regex and ordinary strings are opaque; other module templates permit
only simple interpolations. Ambiguous slash syntax fails closed. TypeScript,
runtime-generated modules, and general interprocedural language semantics are
outside the supported subset. An unsupported declared entry needs a reviewed
checker extension, not a success assertion.

The workflow deletion checker separately preserves the HEAD multiset of `uses`
and shell command lines from jobs/steps across staged workflow files. Display
names and moves within `.github/workflows` may change. Deletion, relocation out
of that directory, non-regular replacements, or changing a command to a no-op
blocks. Only the exact repository acceptance wrapper normalizes to its underlying
`bash` command. This inventory is not a shell interpreter or CI execution proof;
acceptance marker verification supplies that separate evidence.
