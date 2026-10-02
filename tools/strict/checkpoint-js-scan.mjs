const PREFIX_KEYWORDS = new Set([
  "await",
  "case",
  "delete",
  "do",
  "else",
  "in",
  "instanceof",
  "new",
  "return",
  "throw",
  "typeof",
  "void",
  "yield",
]);
const VALUE_ENDING_PUNCTUATORS = new Set([")", "]", "}", "++", "--"]);
const MULTI_PUNCTUATORS = [
  ">>>=", "===", "!==", ">>>", "...", "**=", "&&=", "||=", "??=", "=>",
  "==", "!=", "<=", ">=", "++", "--", "&&", "||", "??", "?.", "**",
  "+=", "-=", "*=", "/=", "%=", "&=", "|=", "^=", "<<", ">>",
];
function isIdentifierStart(char) {
  return /[A-Za-z_$]/.test(char ?? "");
}
function isIdentifierPart(char) {
  return /[A-Za-z0-9_$]/.test(char ?? "");
}
function decodeUnicodeEscape(source, index) {
  const match = source.slice(index).match(/^\\u(?:\{([0-9A-Fa-f]{1,6})\}|([0-9A-Fa-f]{4}))/);
  if (!match) return null;
  const codePoint = Number.parseInt(match[1] ?? match[2], 16);
  if (codePoint > 0x10ffff) return null;
  return { value: String.fromCodePoint(codePoint), length: match[0].length };
}
function decodeStaticEscape(source, index) {
  const unicode = decodeUnicodeEscape(source, index);
  if (unicode) return unicode;
  const hex = source.slice(index).match(/^\\x([0-9A-Fa-f]{2})/);
  if (!hex) return null;
  return { value: String.fromCodePoint(Number.parseInt(hex[1], 16)), length: hex[0].length };
}
function startsTsxGenericArrow(source, index) {
  let angleDepth = 0;
  for (let cursor = index + 1; cursor < source.length; cursor += 1) {
    if (source[cursor] === "<") angleDepth += 1;
    if (source[cursor] !== ">") continue;
    if (angleDepth > 0) {
      angleDepth -= 1;
      continue;
    }
    const parameters = source.slice(index + 1, cursor).trim();
    const distinguishable = parameters.includes(",") || /\bextends\b/.test(parameters);
    return /^[A-Za-z_$]/.test(parameters) && distinguishable && /^\s*\(/.test(source.slice(cursor + 1));
  }
  return false;
}
function staticTemplateExpression(tokens) {
  let expression = tokens;
  while (expression[0]?.value === "(" && expression.at(-1)?.value === ")") {
    expression = expression.slice(1, -1);
  }
  let value = "";
  for (let index = 0; index < expression.length; index += 2) {
    const token = expression[index];
    if (!token || (index > 0 && expression[index - 1]?.value !== "+")) return null;
    if (["string", "template", "number"].includes(token.type)) value += token.value;
    else if (["true", "false", "null"].includes(token.value)) value += token.value;
    else return null;
  }
  return value;
}
function tokenizeJavaScript(source) {
  const tokens = [];
  let index = 0;
  let regexAllowed = true;
  function push(type, value) {
    tokens.push({ type, value });
    if (["identifier", "number", "string", "regex", "template"].includes(type)) {
      regexAllowed = type === "identifier" && PREFIX_KEYWORDS.has(value);
    } else {
      regexAllowed = !VALUE_ENDING_PUNCTUATORS.has(value);
    }
  }
  function scanString(quote) {
    let value = "";
    index += 1;
    while (index < source.length) {
      const char = source[index++];
      if (char === quote) {
        push("string", value);
        return;
      }
      if (char === "\n" || char === "\r") throw new Error("unterminated JavaScript string literal");
      if (char !== "\\") {
        value += char;
        continue;
      }
      if (index >= source.length) break;
      const escapeStart = index - 1;
      const decoded = decodeStaticEscape(source, escapeStart);
      if (decoded) {
        value += decoded.value;
        index = escapeStart + decoded.length;
        continue;
      }
      const escaped = source[index++];
      if (escaped === "\n") continue;
      if (escaped === "\r") {
        if (source[index] === "\n") index += 1;
        continue;
      }
      value += escaped;
    }
    throw new Error("unterminated JavaScript string literal");
  }
  function scanRegex() {
    let inClass = false;
    index += 1;
    while (index < source.length) {
      const char = source[index++];
      if (char === "\n" || char === "\r") throw new Error("unterminated JavaScript regex literal");
      if (char === "\\") {
        if (index < source.length) index += 1;
      } else if (char === "[") {
        inClass = true;
      } else if (char === "]") {
        inClass = false;
      } else if (char === "/" && !inClass) {
        while (/[A-Za-z]/.test(source[index] ?? "")) index += 1;
        push("regex", "");
        return;
      }
    }
    throw new Error("unterminated JavaScript regex literal");
  }
  function scanTemplate() {
    let staticValue = "";
    let isStatic = true;
    index += 1;
    while (index < source.length) {
      const char = source[index++];
      if (char === "\\") {
        const escapeStart = index - 1;
        const decoded = decodeStaticEscape(source, escapeStart);
        if (decoded) {
          staticValue += decoded.value;
          index = escapeStart + decoded.length;
        } else if (index < source.length) {
          staticValue += source[index++];
        }
      } else if (char === "`") {
        push("template", isStatic ? staticValue : "");
        return;
      } else if (char === "$" && source[index] === "{") {
        index += 1;
        regexAllowed = true;
        const tokenStart = tokens.length;
        scanCode(true);
        const interpolation = staticTemplateExpression(tokens.slice(tokenStart));
        if (interpolation === null) isStatic = false;
        else {
          tokens.splice(tokenStart);
          staticValue += interpolation;
        }
      } else {
        staticValue += char;
      }
    }
    throw new Error("unterminated JavaScript template literal");
  }
  function scanJsxString(quote) {
    index += 1;
    while (index < source.length) {
      const char = source[index++];
      if (char === "\\" && index < source.length) index += 1;
      else if (char === quote) return;
    }
    throw new Error("unterminated JSX attribute string");
  }
  function scanJsxOpeningTag() {
    index += 1;
    while (index < source.length) {
      const char = source[index];
      if (char === '"' || char === "'") {
        scanJsxString(char);
      } else if (char === "{") {
        index += 1;
        regexAllowed = true;
        scanCode(true);
      } else if (char === "/" && source[index + 1] === ">") {
        index += 2;
        return true;
      } else if (char === ">") {
        index += 1;
        return false;
      } else {
        index += 1;
      }
    }
    throw new Error("unterminated JSX opening tag");
  }
  function scanJsx() {
    let depth = 0;
    while (index < source.length) {
      if (source.startsWith("</", index)) {
        const end = source.indexOf(">", index + 2);
        if (end < 0) throw new Error("unterminated JSX closing tag");
        index = end + 1;
        depth -= 1;
        if (depth === 0) {
          push("jsx", "");
          return;
        }
      } else if (source[index] === "<") {
        const selfClosing = scanJsxOpeningTag();
        if (!selfClosing) depth += 1;
        else if (depth === 0) {
          push("jsx", "");
          return;
        }
      } else if (source[index] === "{") {
        index += 1;
        regexAllowed = true;
        scanCode(true);
      } else {
        index += 1;
      }
    }
    throw new Error("unterminated JSX element");
  }
  function scanNumber() {
    const rest = source.slice(index);
    const match = rest.match(/^(?:0[xX][0-9A-Fa-f]+|0[bB][01]+|0[oO][0-7]+|(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?)/);
    if (!match) return false;
    index += match[0].length;
    push("number", match[0]);
    return true;
  }
  function scanIdentifier() {
    let value = "";
    let first = true;
    while (index < source.length) {
      const char = source[index];
      if ((first && isIdentifierStart(char)) || (!first && isIdentifierPart(char))) {
        value += char;
        index += 1;
      } else {
        const decoded = decodeUnicodeEscape(source, index);
        const valid = decoded && (first ? isIdentifierStart(decoded.value) : isIdentifierPart(decoded.value));
        if (!valid) break;
        value += decoded.value;
        index += decoded.length;
      }
      first = false;
    }
    push("identifier", value);
  }
  function scanCode(stopAtTemplateBrace = false) {
    let braceDepth = 0;
    while (index < source.length) {
      const char = source[index];
      const next = source[index + 1];
      if (/\s/.test(char)) {
        index += 1;
        continue;
      }
      if (char === "/" && next === "/") {
        index += 2;
        while (index < source.length && !/[\r\n]/.test(source[index])) index += 1;
        continue;
      }
      if (char === "/" && next === "*") {
        const end = source.indexOf("*/", index + 2);
        if (end < 0) throw new Error("unterminated JavaScript block comment");
        index = end + 2;
        continue;
      }
      if (stopAtTemplateBrace && char === "}" && braceDepth === 0) {
        index += 1;
        return;
      }
      if (char === '"' || char === "'") {
        scanString(char);
        continue;
      }
      if (char === "`") {
        scanTemplate();
        continue;
      }
      if (
        char === "<" &&
        regexAllowed &&
        (isIdentifierStart(next) || next === ">") &&
        !startsTsxGenericArrow(source, index)
      ) {
        scanJsx();
        continue;
      }
      if (char === "/" && regexAllowed) {
        scanRegex();
        continue;
      }
      const escapedIdentifier = decodeUnicodeEscape(source, index);
      if (isIdentifierStart(char) || (escapedIdentifier && isIdentifierStart(escapedIdentifier.value))) {
        scanIdentifier();
        continue;
      }
      if (/\d/.test(char) || (char === "." && /\d/.test(next ?? ""))) {
        if (scanNumber()) continue;
      }
      const punctuator = MULTI_PUNCTUATORS.find((value) => source.startsWith(value, index)) ?? char;
      index += punctuator.length;
      if (stopAtTemplateBrace) {
        if (punctuator === "{") braceDepth += 1;
        if (punctuator === "}") braceDepth -= 1;
      }
      push("punctuator", punctuator);
    }
    if (stopAtTemplateBrace) throw new Error("unterminated JavaScript template interpolation");
  }
  scanCode();
  return tokens;
}
const MARKERS = new Set(["skip", "only", "todo"]);
const DISABLED_ALIASES = new Set(["xit", "xdescribe", "xtest"]);
const FOCUSED_ALIASES = new Set(["fit", "fdescribe"]);
const TEST_OBJECTS = new Set(["test", "it", "describe"]);
const ASSERTION_NAMES = new Set(["assert", "expect"]);
function markerAt(tokens, index) {
  const token = tokens[index];
  return token && MARKERS.has(token.value) ? token.value : null;
}
function computedMarkerAt(tokens, index) {
  let depth = 0;
  for (let cursor = index + 1; cursor < tokens.length; cursor += 1) {
    if (tokens[cursor].value === "[") depth += 1;
    if (tokens[cursor].value !== "]") continue;
    if (depth > 0) {
      depth -= 1;
      continue;
    }
    const value = staticTemplateExpression(tokens.slice(index + 1, cursor));
    return { marker: MARKERS.has(value) ? value : null, value, end: cursor };
  }
  return { marker: null, value: null, end: index };
}
function staticTruthiness(tokens, index) {
  let inverted = false;
  while (tokens[index]?.value === "!") {
    inverted = !inverted;
    index += 1;
  }
  while (["+", "-"].includes(tokens[index]?.value)) index += 1;
  const token = tokens[index];
  let value;
  if (token?.type === "number") value = Number(token.value) !== 0;
  else if (["string", "template"].includes(token?.type)) value = token.value.length > 0;
  else if (token?.type === "regex" || ["{", "["].includes(token?.value)) value = true;
  else if (token?.value === "true") value = true;
  else if (["false", "null", "undefined", "NaN"].includes(token?.value)) value = false;
  else value = true;
  value = inverted ? !value : value;
  if (!value && ![",", "}"].includes(tokens[index + 1]?.value)) return true;
  return value;
}
function isInlineTestOptions(tokens, keyIndex) {
  let braceDepth = 0;
  let objectStart = -1;
  for (let cursor = keyIndex - 1; cursor >= 0; cursor -= 1) {
    if (tokens[cursor].value === "}") {
      braceDepth += 1;
    } else if (tokens[cursor].value === "{") {
      if (braceDepth === 0) {
        objectStart = cursor;
        break;
      }
      braceDepth -= 1;
    }
  }
  if (objectStart < 0 || !["(", ","].includes(tokens[objectStart - 1]?.value)) return false;
  let parenDepth = 0;
  for (let cursor = objectStart - 1; cursor >= 0; cursor -= 1) {
    if (tokens[cursor].value === ")") {
      parenDepth += 1;
    } else if (tokens[cursor].value === "(") {
      if (parenDepth === 0) return TEST_OBJECTS.has(tokens[cursor - 1]?.value);
      parenDepth -= 1;
    }
  }
  return false;
}
function assignedMarker(tokens, index, aliases) {
  if (tokens[index]?.type === "identifier" && aliases.has(tokens[index].value)) {
    return aliases.get(tokens[index].value);
  }
  if ([".", "?."].includes(tokens[index + 1]?.value)) return markerAt(tokens, index + 2);
  if (tokens[index + 1]?.value === "[") {
    return computedMarkerAt(tokens, index + 1).marker;
  }
  return null;
}
function collectAliases(tokens) {
  const aliases = new Map();
  for (let index = 0; index < tokens.length; index += 1) {
    if (tokens[index]?.type === "identifier" && tokens[index + 1]?.value === "=") {
      const marker = assignedMarker(tokens, index + 2, aliases);
      if (marker) aliases.set(tokens[index].value, marker);
    }
    if (tokens[index]?.value !== "{") continue;
    const close = tokens.findIndex((token, cursor) => cursor > index && token.value === "}");
    if (close < 0 || tokens[close + 1]?.value !== "=" || !TEST_OBJECTS.has(tokens[close + 2]?.value)) continue;
    for (let cursor = index + 1; cursor < close; cursor += 1) {
      const marker = markerAt(tokens, cursor);
      if (!marker) continue;
      const alias = tokens[cursor + 1]?.value === ":" ? tokens[cursor + 2]?.value : marker;
      if (alias) aliases.set(alias, marker);
    }
  }
  return aliases;
}
function isTrustedAssertionModule(moduleName) { return /^(?:node:)?assert(?:\/strict)?$/.test(moduleName) || /^(?:expect|chai|vitest|@jest\/globals|bun:test)$/.test(moduleName); }
function isTrustedAssertionRequire(tokens, bindingIndex) {
  if (
    tokens[bindingIndex + 1]?.value !== "=" ||
    tokens[bindingIndex + 2]?.value !== "require" ||
    tokens[bindingIndex + 3]?.value !== "(" ||
    tokens[bindingIndex + 4]?.type !== "string"
  ) {
    return false;
  }
  const moduleName = tokens[bindingIndex + 4].value;
  return isTrustedAssertionModule(moduleName);
}
function staticImportSourceIndex(tokens, index) {
  if (["(", "."].includes(tokens[index + 1]?.value)) return -1;
  return tokens.findIndex((token, cursor) => cursor > index && token.type === "string");
}
function collectAssertionBindings(tokens) {
  const bindings = new Set(ASSERTION_NAMES);
  for (let index = 0; index < tokens.length; index += 1) {
    if (tokens[index].value === "import") {
      const sourceIndex = staticImportSourceIndex(tokens, index);
      if (sourceIndex > index && isTrustedAssertionModule(tokens[sourceIndex].value)) {
        for (let cursor = index + 1; cursor < sourceIndex; cursor += 1) {
          const token = tokens[cursor];
          if (token.type === "identifier" && !["as", "from", "type"].includes(token.value) && tokens[cursor + 1]?.value !== "as") bindings.add(token.value);
        }
      }
    }
    if (["const", "let", "var"].includes(tokens[index].value) && tokens[index + 1]?.value === "{") {
      const close = tokens.findIndex((token, cursor) => cursor > index + 1 && token.value === "}");
      if (close > index && isTrustedAssertionRequire(tokens, close)) {
        for (let cursor = index + 2; cursor < close; cursor += 1) {
          const local = tokens[cursor + 1]?.value === ":" ? tokens[cursor + 2] : tokens[cursor];
          if (local?.type === "identifier") bindings.add(local.value);
          if (tokens[cursor + 1]?.value === ":") cursor += 2;
        }
      }
    }
    if (["const", "let", "var"].includes(tokens[index].value) && tokens[index + 1]?.type === "identifier" && isTrustedAssertionRequire(tokens, index + 1)) bindings.add(tokens[index + 1].value);
  }
  return bindings;
}
function isTrustedDestructuredRequire(tokens, index) {
  const open = tokens.findLastIndex((token, cursor) => cursor < index && token.value === "{");
  if (open < 1 || !["const", "let", "var"].includes(tokens[open - 1]?.value)) return false;
  const close = tokens.findIndex((token, cursor) => cursor > index && token.value === "}");
  return close > index && isTrustedAssertionRequire(tokens, close);
}
function isTrustedImportBinding(tokens, index) {
  const start = tokens.findLastIndex((token, cursor) => cursor < index && token.value === "import");
  const source = start < 0 ? -1 : staticImportSourceIndex(tokens, start);
  return source > index && isTrustedAssertionModule(tokens[source].value);
}
function closesBeforeBlock(tokens, open) {
  let depth = 1;
  for (let cursor = open + 1; cursor < tokens.length; cursor += 1) {
    if (tokens[cursor].value === "(") depth += 1;
    if (tokens[cursor].value !== ")") continue;
    depth -= 1;
    if (depth === 0) return tokens[cursor + 1]?.value === "{";
  }
  return true;
}
function isAssertionCall(tokens, index) {
  const next = tokens[index + 1]?.value;
  if (next === "(") return !closesBeforeBlock(tokens, index + 1);
  if (next === "?." && tokens[index + 2]?.value === "(") return !closesBeforeBlock(tokens, index + 2);
  return [".", "?."].includes(next) && tokens[index + 2]?.type === "identifier" &&
    tokens[index + 3]?.value === "(" && !closesBeforeBlock(tokens, index + 3);
}
function collectAssertionShadows(tokens, bindings) {
  const shadows = new Set();
  for (let index = 0; index < tokens.length; index += 1) {
    const token = tokens[index];
    if (["globalThis", "global", "window"].includes(token.value) && tokens[index + 1]?.value === "[") {
      const computed = computedMarkerAt(tokens, index + 1);
      if (bindings.has(computed.value) && tokens[computed.end + 1]?.value === "=") shadows.add(computed.value);
    }
    const globalObject = ["globalThis", "global", "window"].includes(tokens[index - 2]?.value);
    const globalDotWrite = token.type === "identifier" && bindings.has(token.value) &&
      tokens[index - 1]?.value === "." && globalObject && tokens[index + 1]?.value === "=";
    const globalComputedWrite = ["string", "template"].includes(token.type) && bindings.has(token.value) &&
      tokens[index - 1]?.value === "[" && globalObject && tokens[index + 1]?.value === "]" && tokens[index + 2]?.value === "=";
    if (globalDotWrite || globalComputedWrite) {
      shadows.add(token.value);
      continue;
    }
    if (token.type !== "identifier" || !bindings.has(token.value)) continue;
    if ([".", "?."].includes(tokens[index - 1]?.value) || tokens[index + 1]?.value === ":") continue;
    if (isTrustedImportBinding(tokens, index) || isTrustedAssertionRequire(tokens, index) ||
      isTrustedDestructuredRequire(tokens, index) || isAssertionCall(tokens, index)) continue;
    shadows.add(token.value);
  }
  return shadows;
}
export function countJavaScriptWeakening(source) {
  const counts = { skip: 0, only: 0, todo: 0, assertions: 0 };
  const tokens = tokenizeJavaScript(source);
  const aliases = collectAliases(tokens);
  const assertionBindings = collectAssertionBindings(tokens);
  const assertionShadows = collectAssertionShadows(tokens, assertionBindings);
  for (let index = 0; index < tokens.length; index += 1) {
    const token = tokens[index];
    const next = tokens[index + 1];
    if (token.type === "identifier" && DISABLED_ALIASES.has(token.value) && next?.value === "(") {
      counts.skip += 1;
    }
    if (token.type === "identifier" && FOCUSED_ALIASES.has(token.value) && next?.value === "(") {
      counts.only += 1;
    }
    if (
      token.type === "identifier" &&
      aliases.has(token.value) &&
      (next?.value === "(" || (next?.value === "?." && tokens[index + 2]?.value === "("))
    ) {
      counts[aliases.get(token.value)] += 1;
    }
    if ([".", "?."].includes(token.value)) {
      const marker = markerAt(tokens, index + 1);
      if (marker && ["(", ".", "?.", "["].includes(tokens[index + 2]?.value)) counts[marker] += 1;
    }
    if (token.value === "[") {
      const computed = computedMarkerAt(tokens, index);
      const marker = computed.marker;
      const continuation = tokens[computed.end + 1];
      if (
        marker &&
        (["(", ".", "?.", "["].includes(continuation?.value) ||
          (continuation?.value === ":" &&
            isInlineTestOptions(tokens, index) &&
            staticTruthiness(tokens, computed.end + 2)))
      ) {
        counts[marker] += 1;
      }
    }
    const marker = markerAt(tokens, index);
    if (
      marker &&
      next?.value === ":" &&
      isInlineTestOptions(tokens, index) &&
      staticTruthiness(tokens, index + 2)
    ) {
      counts[marker] += 1;
    }
    if (token.type === "identifier" && assertionBindings.has(token.value) &&
      !assertionShadows.has(token.value) && isAssertionCall(tokens, index)) {
      counts.assertions += 1;
    }
  }
  return counts;
}
