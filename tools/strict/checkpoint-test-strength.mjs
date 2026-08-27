import { startsJavaScriptRegex } from "./checkpoint-js-lex.mjs";

function maskIgnoredJavaScript(source) {
  const visible = [...source];
  let state = "code";
  let escaped = false;
  let inClass = false;
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
      else if (char === "/" && startsJavaScriptRegex(source, index)) state = "regex";
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

function namedFunctionDisabled(prefix, visible) {
  const declaration = prefix.match(/\bfunction\s*(\*)?\s+([A-Za-z_$][\w$]*)\s*\([^)]*\)\s*$/);
  const arrow = prefix.match(/\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s+)?(?:\([^)]*\)|[A-Za-z_$][\w$]*)\s*=>\s*$/);
  const expression = prefix.match(/\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*function(?:\s+[A-Za-z_$][\w$]*)?\s*\([^)]*\)\s*$/);
  const method = prefix.match(/\b(?:static\s+)?(?:async\s+)?([A-Za-z_$][\w$]*)\s*\([^)]*\)\s*$/);
  const methodName = method?.[1] === "function" ? undefined : method?.[1];
  const name = declaration?.[2] ?? arrow?.[1] ?? expression?.[1] ?? methodName;
  if (!name) return false;
  if (declaration?.[1]) return true;
  const calls = [...visible.matchAll(new RegExp(`\\b${name}\\s*\\(`, "g"))].length;
  return declaration || method ? calls <= 1 : calls === 0;
}

function runnerCallback(prefix) {
  return /\b(?:test|it|specify|describe|suite|context)\s*\([^;]*,\s*(?:async\s*)?function(?:\s+[A-Za-z_$][\w$]*)?\s*\([^)]*\)\s*$/s.test(prefix);
}

function runnerArrowCallback(prefix) {
  return /\b(?:test|it|specify|describe|suite|context)\s*\([^;]*,\s*(?:async\s*)?(?:\([^)]*\)|[A-Za-z_$][\w$]*)\s*=>\s*$/s.test(prefix);
}

function anonymousFunctionDisabled(prefix) {
  const anonymous = /\bfunction\s*\*?\s*\([^)]*\)\s*$/.test(prefix);
  return anonymous && !runnerCallback(prefix);
}

function blockDisabled(prefix, visible) {
  if (runnerCallback(prefix) || runnerArrowCallback(prefix)) return false;
  const control = /(?:^|[;{}])\s*(?:if|else|while|for|switch|try|catch|finally|do|with)\b[^{}]*$/s;
  const deferred = /\b(?:setTimeout|setInterval|queueMicrotask)\s*\([^{};]*=>\s*$/s;
  const promise = /\.(?:then|catch|finally)\s*\([^{};]*=>\s*$/s;
  const namedArrow = /\b(?:const|let|var)\s+[A-Za-z_$][\w$]*\s*=\s*(?:async\s+)?(?:\([^)]*\)|[A-Za-z_$][\w$]*)\s*=>\s*$/s;
  if (namedArrow.test(prefix)) return namedFunctionDisabled(prefix, visible);
  const callbackArrow = /(?:\([^)]*\)|[A-Za-z_$][\w$]*)\s*=>\s*$/.test(prefix);
  return control.test(prefix) || deferred.test(prefix) || promise.test(prefix)
    || callbackArrow || namedFunctionDisabled(prefix, visible) || anonymousFunctionDisabled(prefix);
}

function arrowExpressionDisabled(statement, visible, position) {
  const assigned = statement.match(/\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?(?:\([^)]*\)|[A-Za-z_$][\w$]*)\s*=>\s*$/s);
  if (assigned) {
    const calls = [...visible.matchAll(new RegExp(`\\b${assigned[1]}\\s*\\(`, "g"))].length;
    return calls === 0;
  }
  const testCallback = /\b(?:test|it|specify)\s*\((?:[^;]*,\s*)?(?:async\s*)?(?:\([^)]*\)|[A-Za-z_$][\w$]*)\s*=>\s*$/s;
  if (testCallback.test(statement)) return false;
  if (/\[\s*\]\s*\.\s*(?:forEach|map|filter|some|every|find)\s*\([^;]*=>\s*$/s.test(statement)) return true;
  if (/\b(?:setTimeout|setInterval)\s*\([^;]*=>\s*$/s.test(statement)) return true;
  const immediate = /^\s*\(+\s*(?:async\s*)?(?:\([^)]*\)|[A-Za-z_$][\w$]*)\s*=>\s*$/s.test(statement);
  const tail = visible.slice(position).match(/^assert\.[A-Za-z_$][\w$]*\s*\((?:[^()]|\([^()]*\))*\)([\s\S]{0,16})/)?.[1] ?? "";
  if (immediate && /^\s*\)\s*\(/.test(tail)) return false;
  return /=>\s*$/.test(statement);
}

function expressionDisabled(visible, position) {
  const statement = visible.slice(Math.max(0, visible.lastIndexOf(";", position - 1) + 1), position);
  const bracelessControl = /(?:^|[;}])\s*(?:(?:if|while|for|with)\s*\([^;{}]*\)|else)\s*$/s;
  return /&&|\|\||\?/.test(statement) || bracelessControl.test(statement) || arrowExpressionDisabled(statement, visible, position);
}

function hasDisabledContext(visible, position) {
  const blocks = [];
  for (let index = 0; index < position; index += 1) {
    if (visible[index] === "{") {
      const prefix = visible.slice(Math.max(0, index - 120), index).trimEnd();
      blocks.push({ disabled: blockDisabled(prefix, visible), start: index + 1 });
    } else if (visible[index] === "}") {
      blocks.pop();
    }
  }
  const afterReturn = blocks.some(({ start }) => /\breturn\b(?:[^\r\n;]*;|[^\r\n]*\r?\n)/.test(visible.slice(start, position)));
  const regionStart = blocks.at(-1)?.start ?? Math.max(0, visible.lastIndexOf("}", position - 1) + 1);
  const terminated = /\b(?:process|Deno|Bun)\s*\.\s*exit\s*\([^)]*\)\s*;/s.test(visible.slice(regionStart, position));
  return blocks.some(({ disabled }) => disabled) || afterReturn || terminated || expressionDisabled(visible, position);
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
  const lines = source.split(/\r?\n/);
  for (const [index, line] of lines.entries()) {
    const stripped = line.replace(/#.*/, "").trim();
    const match = stripped.match(/^assert\s+(.+?)\s*==\s*(.+?)(?:\s*,.*)?$/);
    if (!match || pythonDisabledContext(lines, index)) continue;
    const subject = normalizeExpression(match[1]);
    const expected = normalizeExpression(match[2]);
    if (subject !== expected) atoms.push(`py:exact:${subject}:${expected}`);
  }
  return atoms;
}

function pythonDisabledContext(lines, position) {
  const indentation = (line) => line.match(/^[ \t]*/)[0].replace(/\t/g, "        ").length;
  let ceiling = indentation(lines[position]);
  const source = lines.join("\n");
  for (let index = position - 1; index >= 0 && ceiling > 0; index -= 1) {
    const code = lines[index].replace(/#.*/, "").trim();
    const indent = indentation(lines[index]);
    if (!code || indent >= ceiling || !code.endsWith(":")) continue;
    if (/^(?:if|elif|else|while|for|try|except|finally|with|match|case)\b/.test(code)) return true;
    const definition = code.match(/^(?:async\s+)?def\s+([A-Za-z_]\w*)\s*\(/);
    if (definition && !/^test(?:_|$)/.test(definition[1])
      && [...source.matchAll(new RegExp(`\\b${definition[1]}\\s*\\(`, "g"))].length <= 1) return true;
    ceiling = indent;
  }
  const targetIndent = indentation(lines[position]);
  for (let index = position - 1; index >= 0; index -= 1) {
    const code = lines[index].replace(/#.*/, "").trim();
    const indent = indentation(lines[index]);
    if (code && indent < targetIndent) break;
    if (indent === targetIndent && /^(?:return\b|(?:sys\.exit|os\._exit|exit|quit)\s*\(|raise\s+SystemExit\b)/.test(code)) return true;
  }
  return false;
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
