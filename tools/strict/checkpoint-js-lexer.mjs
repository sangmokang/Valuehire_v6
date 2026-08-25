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
  ">>>=",
  "===",
  "!==",
  ">>>",
  "**=",
  "&&=",
  "||=",
  "??=",
  "=>",
  "==",
  "!=",
  "<=",
  ">=",
  "++",
  "--",
  "&&",
  "||",
  "??",
  "?.",
  "**",
  "+=",
  "-=",
  "*=",
  "/=",
  "%=",
  "&=",
  "|=",
  "^=",
  "<<",
  ">>",
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

export function staticTemplateExpression(tokens) {
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

class JavaScriptLexer {
  constructor(source) {
    this.source = source;
    this.tokens = [];
    this.index = 0;
    this.regexAllowed = true;
  }

  push(type, value) {
    this.tokens.push({ type, value });
    if (["identifier", "number", "string", "regex", "template"].includes(type)) {
      this.regexAllowed = type === "identifier" && PREFIX_KEYWORDS.has(value);
    } else {
      this.regexAllowed = !VALUE_ENDING_PUNCTUATORS.has(value);
    }
  }

  scanString(quote) {
    let value = "";
    this.index += 1;
    while (this.index < this.source.length) {
      const char = this.source[this.index++];
      if (char === quote) {
        this.push("string", value);
        return;
      }
      if (char === "\n" || char === "\r") throw new Error("unterminated JavaScript string literal");
      if (char !== "\\") {
        value += char;
        continue;
      }
      if (this.index >= this.source.length) break;
      const escapeStart = this.index - 1;
      const decoded = decodeStaticEscape(this.source, escapeStart);
      if (decoded) {
        value += decoded.value;
        this.index = escapeStart + decoded.length;
        continue;
      }
      const escaped = this.source[this.index++];
      if (escaped === "\n") continue;
      if (escaped === "\r") {
        if (this.source[this.index] === "\n") this.index += 1;
        continue;
      }
      value += escaped;
    }
    throw new Error("unterminated JavaScript string literal");
  }

  scanRegex() {
    let inClass = false;
    this.index += 1;
    while (this.index < this.source.length) {
      const char = this.source[this.index++];
      if (char === "\n" || char === "\r") throw new Error("unterminated JavaScript regex literal");
      if (char === "\\") {
        if (this.index < this.source.length) this.index += 1;
      } else if (char === "[") {
        inClass = true;
      } else if (char === "]") {
        inClass = false;
      } else if (char === "/" && !inClass) {
        while (/[A-Za-z]/.test(this.source[this.index] ?? "")) this.index += 1;
        this.push("regex", "");
        return;
      }
    }
    throw new Error("unterminated JavaScript regex literal");
  }

  scanTemplate() {
    let staticValue = "";
    let isStatic = true;
    this.index += 1;
    while (this.index < this.source.length) {
      const char = this.source[this.index++];
      if (char === "\\") {
        const escapeStart = this.index - 1;
        const decoded = decodeStaticEscape(this.source, escapeStart);
        if (decoded) {
          staticValue += decoded.value;
          this.index = escapeStart + decoded.length;
        } else if (this.index < this.source.length) staticValue += this.source[this.index++];
      } else if (char === "`") {
        this.push("template", isStatic ? staticValue : "");
        return;
      } else if (char === "$" && this.source[this.index] === "{") {
        this.index += 1;
        this.regexAllowed = true;
        const tokenStart = this.tokens.length;
        this.scanCode(true);
        const interpolation = staticTemplateExpression(this.tokens.slice(tokenStart));
        if (interpolation === null) isStatic = false;
        else {
          this.tokens.splice(tokenStart);
          staticValue += interpolation;
        }
      } else staticValue += char;
    }
    throw new Error("unterminated JavaScript template literal");
  }

  scanJsxString(quote) {
    this.index += 1;
    while (this.index < this.source.length) {
      const char = this.source[this.index++];
      if (char === "\\" && this.index < this.source.length) this.index += 1;
      else if (char === quote) return;
    }
    throw new Error("unterminated JSX attribute string");
  }

  scanJsxOpeningTag() {
    this.index += 1;
    while (this.index < this.source.length) {
      const char = this.source[this.index];
      if (char === '"' || char === "'") this.scanJsxString(char);
      else if (char === "{") {
        this.index += 1;
        this.regexAllowed = true;
        this.scanCode(true);
      } else if (char === "/" && this.source[this.index + 1] === ">") {
        this.index += 2;
        return true;
      } else if (char === ">") {
        this.index += 1;
        return false;
      } else this.index += 1;
    }
    throw new Error("unterminated JSX opening tag");
  }

  scanJsx() {
    let depth = 0;
    while (this.index < this.source.length) {
      if (this.source.startsWith("</", this.index)) {
        const end = this.source.indexOf(">", this.index + 2);
        if (end < 0) throw new Error("unterminated JSX closing tag");
        this.index = end + 1;
        depth -= 1;
        if (depth === 0) {
          this.push("jsx", "");
          return;
        }
      } else if (this.source[this.index] === "<") {
        const selfClosing = this.scanJsxOpeningTag();
        if (!selfClosing) depth += 1;
        else if (depth === 0) {
          this.push("jsx", "");
          return;
        }
      } else if (this.source[this.index] === "{") {
        this.index += 1;
        this.regexAllowed = true;
        this.scanCode(true);
      } else this.index += 1;
    }
    throw new Error("unterminated JSX element");
  }

  scanNumber() {
    const rest = this.source.slice(this.index);
    const match = rest.match(/^(?:0[xX][0-9A-Fa-f]+|0[bB][01]+|0[oO][0-7]+|(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?)/);
    if (!match) return false;
    this.index += match[0].length;
    this.push("number", match[0]);
    return true;
  }

  scanIdentifier() {
    let value = "";
    let first = true;
    while (this.index < this.source.length) {
      const char = this.source[this.index];
      if ((first && isIdentifierStart(char)) || (!first && isIdentifierPart(char))) {
        value += char;
        this.index += 1;
      } else {
        const decoded = decodeUnicodeEscape(this.source, this.index);
        const valid = decoded && (first ? isIdentifierStart(decoded.value) : isIdentifierPart(decoded.value));
        if (!valid) break;
        value += decoded.value;
        this.index += decoded.length;
      }
      first = false;
    }
    this.push("identifier", value);
  }

  scanCode(stopAtTemplateBrace = false) {
    let braceDepth = 0;
    while (this.index < this.source.length) {
      const char = this.source[this.index];
      const next = this.source[this.index + 1];
      if (/\s/.test(char)) {
        this.index += 1;
        continue;
      }
      if (char === "/" && next === "/") {
        this.index += 2;
        while (this.index < this.source.length && !/[\r\n]/.test(this.source[this.index])) this.index += 1;
        continue;
      }
      if (char === "/" && next === "*") {
        const end = this.source.indexOf("*/", this.index + 2);
        if (end < 0) throw new Error("unterminated JavaScript block comment");
        this.index = end + 2;
        continue;
      }
      if (stopAtTemplateBrace && char === "}" && braceDepth === 0) {
        this.index += 1;
        return;
      }
      if (char === '"' || char === "'") {
        this.scanString(char);
        continue;
      }
      if (char === "`") {
        this.scanTemplate();
        continue;
      }
      if (
        char === "<" &&
        this.regexAllowed &&
        (isIdentifierStart(next) || next === ">") &&
        !startsTsxGenericArrow(this.source, this.index)
      ) {
        this.scanJsx();
        continue;
      }
      if (char === "/" && this.regexAllowed) {
        this.scanRegex();
        continue;
      }
      const escapedIdentifier = decodeUnicodeEscape(this.source, this.index);
      if (isIdentifierStart(char) || (escapedIdentifier && isIdentifierStart(escapedIdentifier.value))) {
        this.scanIdentifier();
        continue;
      }
      if ((/\d/.test(char) || (char === "." && /\d/.test(next ?? ""))) && this.scanNumber()) continue;
      const punctuator = MULTI_PUNCTUATORS.find((value) => this.source.startsWith(value, this.index)) ?? char;
      this.index += punctuator.length;
      if (stopAtTemplateBrace) {
        if (punctuator === "{") braceDepth += 1;
        if (punctuator === "}") braceDepth -= 1;
      }
      this.push("punctuator", punctuator);
    }
    if (stopAtTemplateBrace) throw new Error("unterminated JavaScript template interpolation");
  }

  tokenize() {
    this.scanCode();
    return this.tokens;
  }
}

export function tokenizeJavaScript(source) {
  return new JavaScriptLexer(source).tokenize();
}
