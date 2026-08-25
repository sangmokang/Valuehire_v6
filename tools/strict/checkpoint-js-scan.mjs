import { staticTemplateExpression, tokenizeJavaScript } from "./checkpoint-js-lexer.mjs";

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
    return { marker: MARKERS.has(value) ? value : null, end: cursor };
  }
  return { marker: null, end: index };
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
  return /^(?:node:)?assert(?:\/strict)?$/.test(moduleName) || /^(?:expect|chai)$/.test(moduleName);
}

function isDestructuredAssignment(tokens, index) {
  let depth = 0;
  for (let cursor = index + 1; cursor < tokens.length; cursor += 1) {
    const value = tokens[cursor].value;
    if (value === ";" || value === "=>") return false;
    if (depth === 0 && ["const", "let", "var", "function", "class"].includes(value)) return false;
    if (["{", "["].includes(value)) {
      depth += 1;
      continue;
    }
    if (["}", "]"].includes(value)) {
      if (depth > 0) depth -= 1;
      if (depth === 0 && tokens[cursor + 1]?.value === "=") return true;
    }
  }
  return false;
}

function collectAssertionShadows(tokens) {
  const shadows = new Set();
  for (let index = 0; index < tokens.length; index += 1) {
    const token = tokens[index];
    if (["const", "let", "var"].includes(token.value) && ASSERTION_NAMES.has(tokens[index + 1]?.value)) {
      if (!isTrustedAssertionRequire(tokens, index + 1)) shadows.add(tokens[index + 1].value);
    }
    if (["function", "class"].includes(token.value) && ASSERTION_NAMES.has(tokens[index + 1]?.value)) {
      shadows.add(tokens[index + 1].value);
    }
    if (ASSERTION_NAMES.has(token.value) && token.type === "identifier") {
      if (isDestructuredAssignment(tokens, index)) shadows.add(token.value);
      if (tokens[index + 1]?.value === "=" && !["const", "let", "var"].includes(tokens[index - 1]?.value)) {
        shadows.add(token.value);
      }
      if ([".", "?."].includes(tokens[index + 1]?.value) && tokens[index + 3]?.value === "=") {
        shadows.add(token.value);
      }
    }
  }
  return shadows;
}

export function countJavaScriptWeakening(source) {
  const counts = { skip: 0, only: 0, todo: 0, assertions: 0 };
  const tokens = tokenizeJavaScript(source);
  const aliases = collectAliases(tokens);
  const assertionShadows = collectAssertionShadows(tokens);
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
    if (
      token.type === "identifier" &&
      token.value === "assert" &&
      !assertionShadows.has("assert") &&
      next?.value === "("
    ) {
      counts.assertions += 1;
    }
    if (
      token.type === "identifier" &&
      token.value === "assert" &&
      !assertionShadows.has("assert") &&
      next?.value === "." &&
      tokens[index + 2]?.type === "identifier" &&
      tokens[index + 3]?.value === "("
    ) {
      counts.assertions += 1;
    }
    if (
      token.type === "identifier" &&
      token.value === "expect" &&
      !assertionShadows.has("expect") &&
      next?.value === "("
    ) {
      counts.assertions += 1;
    }
  }
  return counts;
}
