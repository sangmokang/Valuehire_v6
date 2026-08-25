import { extname } from "node:path";

const JAVASCRIPT_EXTENSIONS = new Set([".js", ".mjs", ".cjs", ".jsx", ".ts", ".tsx"]);
const SHELL_EXTENSIONS = new Set([".sh", ".bash", ".zsh"]);
const CONTROL_WORDS = new Set(["if", "for", "while", "switch", "catch", "with"]);

function maskBraceLanguage(source, language) {
  const output = [...source];
  let index = 0;
  let state = "code";
  let quote = "";
  let inClass = false;
  let previousSignificant = "";
  const mask = (position) => {
    if (output[position] !== "\n" && output[position] !== "\r") output[position] = " ";
  };
  const startsRegex = () =>
    language === "javascript" &&
    (previousSignificant === "" || /[([{=:;,!?&|+*%^~<>-]/.test(previousSignificant));

  while (index < source.length) {
    const char = source[index];
    const next = source[index + 1] ?? "";
    if (state === "line-comment") {
      mask(index);
      if (char === "\n") state = "code";
      index += 1;
      continue;
    }
    if (state === "block-comment") {
      mask(index);
      if (char === "*" && next === "/") {
        mask(index + 1);
        index += 2;
        state = "code";
      } else index += 1;
      continue;
    }
    if (state === "quote" || state === "template") {
      mask(index);
      if (char === "\\") {
        mask(index + 1);
        index += 2;
      } else if (char === quote) {
        index += 1;
        state = "code";
      } else index += 1;
      continue;
    }
    if (state === "regex") {
      mask(index);
      if (char === "\\") {
        mask(index + 1);
        index += 2;
      } else if (char === "[") {
        inClass = true;
        index += 1;
      } else if (char === "]") {
        inClass = false;
        index += 1;
      } else if (char === "/" && !inClass) {
        index += 1;
        while (/[A-Za-z]/.test(source[index] ?? "")) mask(index++);
        state = "code";
        previousSignificant = "/";
      } else index += 1;
      continue;
    }
    if (language === "javascript" && char === "/" && next === "/") {
      mask(index);
      mask(index + 1);
      index += 2;
      state = "line-comment";
    } else if (language === "javascript" && char === "/" && next === "*") {
      mask(index);
      mask(index + 1);
      index += 2;
      state = "block-comment";
    } else if (language === "shell" && char === "#" && /\s|^/.test(source[index - 1] ?? "")) {
      mask(index++);
      state = "line-comment";
    } else if (char === '"' || char === "'") {
      quote = char;
      mask(index++);
      state = "quote";
    } else if (language === "javascript" && char === "`") {
      quote = char;
      mask(index++);
      state = "template";
    } else if (char === "/" && startsRegex()) {
      mask(index++);
      inClass = false;
      state = "regex";
    } else {
      if (!/\s/.test(char)) previousSignificant = char;
      index += 1;
    }
  }
  return output.join("");
}

function matchingBrace(source, open) {
  let depth = 0;
  for (let index = open; index < source.length; index += 1) {
    if (source[index] === "{") depth += 1;
    if (source[index] === "}") depth -= 1;
    if (depth === 0) return index;
  }
  throw new Error("function budget parser found an unmatched opening brace");
}

function lineNumber(source, index) {
  return source.slice(0, index).split("\n").length;
}

function spansFromPatterns(source, masked, patterns) {
  const spans = [];
  const seen = new Set();
  for (const { pattern, nameIndex } of patterns) {
    for (const match of masked.matchAll(pattern)) {
      const open = masked.indexOf("{", match.index);
      if (open < 0 || seen.has(open)) continue;
      seen.add(open);
      const close = matchingBrace(masked, open);
      const startLine = lineNumber(source, match.index);
      const endLine = lineNumber(source, close);
      spans.push({ name: match[nameIndex] || "<anonymous>", startLine, endLine, loc: endLine - startLine + 1 });
    }
  }
  return spans;
}

function javascriptFunctionSpans(source) {
  const masked = maskBraceLanguage(source, "javascript");
  const spans = spansFromPatterns(source, masked, [
    { pattern: /\b(?:async\s+)?function(?:\s*\*)?\s*([A-Za-z_$][\w$]*)?\s*\([^)]*\)\s*\{/g, nameIndex: 1 },
    { pattern: /([A-Za-z_$][\w$]*|\([^()\n]*\))\s*=>\s*\{/g, nameIndex: 1 },
    {
      pattern: /^[ \t]*(?:async[ \t]+)?(?:get[ \t]+|set[ \t]+)?([A-Za-z_$][\w$]*)[ \t]*\([^()\n]*\)[ \t]*\{/gm,
      nameIndex: 1,
    },
  ]);
  return spans.filter((span) => !CONTROL_WORDS.has(span.name));
}

function maskPython(source) {
  const output = [...source];
  let index = 0;
  let quote = "";
  let triple = false;
  const mask = (position) => {
    if (output[position] !== "\n" && output[position] !== "\r") output[position] = " ";
  };
  while (index < source.length) {
    const char = source[index];
    if (!quote && char === "#") {
      while (index < source.length && source[index] !== "\n") mask(index++);
      continue;
    }
    if (!quote && (source.startsWith("'''", index) || source.startsWith('\"\"\"', index))) {
      quote = source.slice(index, index + 3);
      triple = true;
      mask(index++);
      mask(index++);
      mask(index++);
      continue;
    }
    if (!quote && (char === "'" || char === '"')) {
      quote = char;
      triple = false;
      mask(index++);
      continue;
    }
    if (quote) {
      mask(index);
      if (char === "\\") {
        mask(index + 1);
        index += 2;
      } else if (triple && source.startsWith(quote, index)) {
        mask(index + 1);
        mask(index + 2);
        index += 3;
        quote = "";
      } else if (!triple && char === quote) {
        index += 1;
        quote = "";
      } else index += 1;
    } else index += 1;
  }
  return output.join("");
}

function indentation(line) {
  let width = 0;
  for (const char of line.match(/^[ \t]*/)?.[0] ?? "") width += char === "\t" ? 8 - (width % 8) : 1;
  return width;
}

function pythonFunctionSpans(source) {
  const lines = maskPython(source).split("\n");
  const spans = [];
  for (let start = 0; start < lines.length; start += 1) {
    const match = lines[start].match(/^([ \t]*)(?:async[ \t]+)?def[ \t]+([A-Za-z_]\w*)[ \t]*\(/);
    if (!match) continue;
    const baseIndent = indentation(match[1]);
    let end = start;
    for (let index = start + 1; index < lines.length; index += 1) {
      if (/^[ \t]*$/.test(lines[index])) {
        let next = index + 1;
        while (next < lines.length && /^[ \t]*$/.test(lines[next])) next += 1;
        if (next >= lines.length || indentation(lines[next]) <= baseIndent) break;
        end = index;
        continue;
      }
      if (indentation(lines[index]) <= baseIndent) break;
      end = index;
    }
    spans.push({ name: match[2], startLine: start + 1, endLine: end + 1, loc: end - start + 1 });
  }
  return spans;
}

function shellFunctionSpans(source) {
  const masked = maskBraceLanguage(source, "shell");
  return spansFromPatterns(source, masked, [
    {
      pattern: /(?:^|\n)[ \t]*(?:function[ \t]+)?([A-Za-z_][A-Za-z0-9_]*)[ \t]*(?:\(\))?[ \t]*\{/g,
      nameIndex: 1,
    },
  ]);
}

export function functionSpans(path, source) {
  const extension = extname(path).toLowerCase();
  if (JAVASCRIPT_EXTENSIONS.has(extension)) return javascriptFunctionSpans(source);
  if (extension === ".py") return pythonFunctionSpans(source);
  if (SHELL_EXTENSIONS.has(extension)) return shellFunctionSpans(source);
  throw new Error(`unsupported function budget language: ${extension || "<none>"}`);
}
