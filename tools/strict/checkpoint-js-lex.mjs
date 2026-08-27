const REGEX_PREFIX_KEYWORDS = new Set([
  "await",
  "case",
  "delete",
  "in",
  "instanceof",
  "of",
  "return",
  "throw",
  "typeof",
  "void",
  "yield",
]);

function previousWord(source, cursor) {
  let start = cursor;
  while (start >= 0 && /[A-Za-z0-9_$]/.test(source[start])) start -= 1;
  return source.slice(start + 1, cursor + 1);
}

export function startsJavaScriptRegex(source, slashIndex) {
  let cursor = slashIndex - 1;
  while (cursor >= 0 && /\s/.test(source[cursor])) cursor -= 1;
  if (cursor < 0) return true;
  const previous = source[cursor];
  if (/[A-Za-z_$]/.test(previous)) return REGEX_PREFIX_KEYWORDS.has(previousWord(source, cursor));
  if (/[0-9'"`\])}]/.test(previous)) return false;
  if ((previous === "+" || previous === "-") && source[cursor - 1] === previous) return false;
  return /[([{=:;,!?&|+*%^~<>-]/.test(previous);
}
