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

function jsCalls(source, name) {
  const calls = [];
  const visible = maskIgnoredJavaScript(source);
  const pattern = new RegExp(`\\bassert\\.${name}\\s*\\(`, "g");
  for (const match of visible.matchAll(pattern)) {
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
  const match = text.trim().match(/^\/((?:\\.|[^/])*)\/[a-z]*$/i);
  return match ? match[1] : null;
}

function anchoredRegexBody(token) {
  if (token === null || !token.startsWith("^") || !token.endsWith("$")) return null;
  const body = token.slice(1, -1);
  if (body === ".*" || body === "[\\s\\S]*") return null;
  return body;
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
    const body = anchoredRegexBody(regexToken(args[1] ?? ""));
    if (args.length >= 2 && body) atoms.push(`js:anchored:${normalizeExpression(args[0])}:${body}`);
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

function multiset(values) {
  const counts = new Map();
  for (const value of values) counts.set(value, (counts.get(value) ?? 0) + 1);
  return counts;
}

export function strengthDetails(basePath, beforeContent, currentPath, currentContent) {
  const before = multiset(strongAtoms(basePath ?? currentPath, beforeContent));
  const after = multiset(strongAtoms(currentPath, currentContent));
  const details = [];
  for (const [atom, count] of before) {
    const actual = after.get(atom) ?? 0;
    if (actual < count) details.push(`strong assertion weakened: ${atom} ${count} -> ${actual}`);
  }
  return details;
}
