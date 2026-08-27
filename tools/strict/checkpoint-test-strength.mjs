function maskIgnoredJavaScript(source) {
  const visible = [...source];
  let state = "code";
  let escaped = false;
  let inClass = false;
  let previous = "";
  const mask = (index) => {
    if (visible[index] !== "\n" && visible[index] !== "\r") visible[index] = " ";
  };
  for (let index = 0; index < source.length; index += 1) {
    const char = source[index];
    const next = source[index + 1];
    if (state === "code") {
      if (char === "/" && next === "/") state = "line-comment";
      else if (char === "/" && next === "*") state = "block-comment";
      else if (char === "\"" || char === "'" || char === "`") state = char;
      else if (char === "/" && (!previous || /[({[=,:;!&|?+\-*%^~<>]/.test(previous))) state = "regex";
      else if (!/\s/.test(char)) previous = char;
      if (state !== "code") mask(index);
      continue;
    }
    mask(index);
    if (state === "line-comment" && (char === "\n" || char === "\r")) state = "code";
    else if (state === "block-comment" && char === "*" && next === "/") {
      mask(++index);
      state = "code";
    } else if (escaped) escaped = false;
    else if (char === "\\") escaped = true;
    else if (state === "regex") {
      if (char === "[") inClass = true;
      else if (char === "]") inClass = false;
      else if (char === "/" && !inClass) state = "code";
    } else if (char === state) state = "code";
  }
  return visible.join("");
}

function hasDisabledContext(visible, position) {
  const disabled = [];
  for (let index = 0; index < position; index += 1) {
    if (visible[index] === "{") {
      const prefix = visible.slice(Math.max(0, index - 120), index).trimEnd();
      disabled.push(/(?:\btry|\bif\s*\(\s*(?:false|0|null|undefined)\s*\))\s*$/.test(prefix));
    } else if (visible[index] === "}") {
      disabled.pop();
    }
  }
  return disabled.includes(true);
}

function jsCalls(source, name) {
  const calls = [];
  const visible = maskIgnoredJavaScript(source);
  const pattern = new RegExp(`\\bassert\\.${name}\\s*\\(`, "g");
  for (const match of visible.matchAll(pattern)) {
    if (hasDisabledContext(visible, match.index)) continue;
    const start = match.index + match[0].length;
    let depth = 1;
    for (let index = start; index < visible.length; index += 1) {
      if (visible[index] === "(") depth += 1;
      else if (visible[index] === ")") depth -= 1;
      if (depth === 0) {
        calls.push(source.slice(start, index));
        break;
      }
    }
  }
  return calls;
}

function splitArguments(text) {
  const parts = [];
  let current = "";
  let depth = 0;
  let quote = "";
  let escaped = false;
  let regex = false;
  let inClass = false;
  for (const char of text) {
    if (escaped) {
      current += char;
      escaped = false;
      continue;
    }
    if (char === "\\") {
      current += char;
      escaped = true;
      continue;
    }
    if (quote) {
      current += char;
      if (char === quote) quote = "";
      continue;
    }
    if (regex) {
      current += char;
      if (char === "[") inClass = true;
      else if (char === "]") inClass = false;
      else if (char === "/" && !inClass) regex = false;
      continue;
    }
    if (char === "\"" || char === "'" || char === "`") {
      current += char;
      quote = char;
    } else if (char === "/" && /(^|[,(=\s])$/.test(current)) {
      current += char;
      regex = true;
      inClass = false;
    } else if (char === "(" || char === "[" || char === "{") {
      current += char;
      depth += 1;
    } else if (char === ")" || char === "]" || char === "}") {
      current += char;
      depth -= 1;
    } else if (char === "," && depth === 0) {
      parts.push(current.trim());
      current = "";
    } else {
      current += char;
    }
  }
  if (current.trim()) parts.push(current.trim());
  return parts;
}

function normalizeExpression(text) {
  return text.trim().replace(/\s+/g, " ");
}

function regexToken(text) {
  const match = text.trim().match(/^\/((?:\\.|[^/])*)\/([a-z]*)$/i);
  return match ? { body: match[1], flags: match[2].toLowerCase() } : null;
}

function anchoredRegex(token) {
  if (token === null || !token.body.startsWith("^") || !token.body.endsWith("$")) return null;
  const body = token.body.slice(1, -1);
  if (body === ".*" || body === "[\\s\\S]*") return null;
  const weakFlags = [...token.flags].filter((flag) => "ims".includes(flag)).sort().join("");
  return { body, weakFlags };
}

function jsStrongAtoms(source) {
  const atoms = [];
  for (const name of ["equal", "strictEqual", "deepEqual", "deepStrictEqual"]) {
    for (const call of jsCalls(source, name)) {
      const args = splitArguments(call);
      if (args.length < 2) continue;
      const subject = normalizeExpression(args[0]);
      const expected = normalizeExpression(args[1]);
      if (subject !== expected) atoms.push(`js:exact:${subject}:${expected}`);
    }
  }
  for (const call of jsCalls(source, "match")) {
    const args = splitArguments(call);
    const regex = anchoredRegex(regexToken(args[1] ?? ""));
    if (args.length >= 2 && regex) {
      atoms.push(`js:anchored:${normalizeExpression(args[0])}:${regex.body}\u001f${regex.weakFlags}`);
    }
  }
  return atoms;
}

function pythonStrongAtoms(source) {
  const atoms = [];
  for (const line of source.split(/\r?\n/)) {
    const stripped = line.replace(/#.*/, "").trim();
    const match = stripped.match(/^assert\s+(.+?)\s*==\s*(.+?)(?:\s*,.*)?$/);
    if (!match) continue;
    const subject = normalizeExpression(match[1]);
    const expected = normalizeExpression(match[2]);
    if (subject !== expected) atoms.push(`py:exact:${subject}:${expected}`);
  }
  return atoms;
}

function strongAtoms(path, source) {
  const lower = path.toLowerCase();
  if (/\.[cm]?[jt]sx?$/.test(lower)) return jsStrongAtoms(source);
  if (/\.py$/.test(lower)) return pythonStrongAtoms(source);
  return [];
}

function preservesAtom(before, after) {
  if (!before.startsWith("js:anchored:") || !after.startsWith("js:anchored:")) return before === after;
  const [beforeKey, beforeFlags = ""] = before.split("\u001f");
  const [afterKey, afterFlags = ""] = after.split("\u001f");
  return beforeKey === afterKey && [...afterFlags].every((flag) => beforeFlags.includes(flag));
}

export function strengthDetails(basePath, beforeContent, currentPath, currentContent) {
  const before = strongAtoms(basePath ?? currentPath, beforeContent);
  const after = strongAtoms(currentPath, currentContent);
  const used = new Set();
  const details = [];
  for (const atom of before) {
    const match = after.findIndex((candidate, index) => !used.has(index) && preservesAtom(atom, candidate));
    if (match === -1) details.push(`strong assertion weakened: ${atom.replace("\u001f", " flags=")}`);
    else used.add(match);
  }
  return details;
}
