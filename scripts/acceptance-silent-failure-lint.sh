#!/usr/bin/env bash
# P3 "조용한 실패 금지"의 문법 판정 절반. 계약:
#   사용법 : bash scripts/acceptance-silent-failure-lint.sh [파일...]
#            인자가 없으면 추적 중인 Python/JavaScript 계열 파일을 확장자 대소문자와 무관하게 검사한다.
#   출력   : 위반마다 FAIL: <file>:<line>: <패턴이름> — <해당 줄> 을 stdout에 출력
#   종료   : 0 = 위반 없음 | 1 = 위반 발견 | 2 = NOT_RUN(스캔 성립 불가)
#   불변식 : 검사 대상 0건, 파일 읽기 실패, 문법 토큰화 실패는 통과가 아니다(P20).
# `const x = new Map(); x.get(k) || []`는 미존재를 빈 컬렉션으로 모델링한 예외다.
set -uo pipefail
if ! command -v python3 >/dev/null 2>&1; then
  echo "NOT_RUN: python3 없음 — 문법 판정기를 실행할 수 없음"
  exit 2
fi
python3 - "$@" <<'PY'
from __future__ import annotations
import ast
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
TARGET_SUFFIXES = {".py", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".mts", ".cts"}
@dataclass(frozen=True)
class Token:
    value: str
    line: int
class ScanError(Exception):
    def __init__(self, line: int, message: str) -> None:
        super().__init__(message)
        self.line = line
        self.message = message
class JSLexer:
    REGEX_PREFIXES = {
        None, "(", "[", "{", ",", ";", ":", "=", "==", "===", "!=", "!==",
        "!", "?", "??", "||", "&&", "+", "-", "*", "%", "&", "|", "^", "~",
        "=>", "return", "throw", "case", "delete", "void", "typeof", "instanceof",
        "in", "of", "yield", "await",
    }
    MULTI = (
        "??=", "||=", "&&=", "===", "!==", ">>>", "**=", "=>", "??", "||", "&&",
        "==", "!=", "<=", ">=", "++", "--", "?.", "**", "<<", ">>", "+=", "-=",
        "*=", "/=", "%=", "&=", "|=", "^=", "...",
    )
    JSX_PREFIXES = {None, "=", "(", "[", "{", ",", ":", ";", "return", "=>", "?", "||", "&&"}
    def __init__(self, source: str, jsx_enabled: bool = False) -> None:
        self.source = source
        self.length = len(source)
        self.index = 0
        self.line = 1
        self.tokens: list[Token] = []
        self.jsx_enabled = jsx_enabled
    def peek(self, offset: int = 0) -> str:
        pos = self.index + offset
        return self.source[pos] if pos < self.length else ""
    def advance(self, count: int = 1) -> None:
        for _ in range(count):
            if self.index >= self.length:
                return
            if self.source[self.index] == "\n":
                self.line += 1
            self.index += 1
    def emit(self, value: str, line: int | None = None) -> None:
        self.tokens.append(Token(value, self.line if line is None else line))
    def skip_quoted(self, quote: str) -> None:
        start = self.line
        self.advance()
        while self.index < self.length:
            ch = self.peek()
            if ch == "\\":
                self.advance()
                if self.index >= self.length:
                    raise ScanError(start, "문자열 끝의 고립된 이스케이프")
                self.advance()
            elif ch == quote:
                self.advance()
                self.emit("<literal>", start)
                return
            elif ch in "\r\n":
                raise ScanError(start, "닫히지 않은 문자열")
            else:
                self.advance()
        raise ScanError(start, "닫히지 않은 문자열")
    def skip_line_comment(self) -> None:
        self.advance(2)
        while self.index < self.length and self.peek() not in "\r\n":
            self.advance()
    def skip_block_comment(self) -> None:
        start = self.line
        self.advance(2)
        while self.index < self.length:
            if self.peek() == "*" and self.peek(1) == "/":
                self.advance(2)
                return
            self.advance()
        raise ScanError(start, "닫히지 않은 블록 주석")
    def skip_regex(self) -> None:
        start = self.line
        self.advance()
        in_class = False
        while self.index < self.length:
            ch = self.peek()
            if ch == "\\":
                self.advance(2)
            elif ch in "\r\n":
                raise ScanError(start, "닫히지 않은 정규식 리터럴")
            elif ch == "[":
                in_class = True
                self.advance()
            elif ch == "]" and in_class:
                in_class = False
                self.advance()
            elif ch == "/" and not in_class:
                self.advance()
                while self.peek().isalpha():
                    self.advance()
                self.emit("<literal>", start)
                return
            else:
                self.advance()
        raise ScanError(start, "닫히지 않은 정규식 리터럴")
    def scan_template(self) -> None:
        start = self.line
        self.advance()
        while self.index < self.length:
            ch = self.peek()
            if ch == "\\":
                self.advance()
                if self.index >= self.length:
                    raise ScanError(start, "템플릿 문자열 끝의 고립된 이스케이프")
                self.advance()
            elif ch == "`":
                self.advance()
                self.emit("<literal>", start)
                return
            elif ch == "$" and self.peek(1) == "{":
                self.advance(2)
                self.scan_code(stop_at_template_brace=True)
            else:
                self.advance()
        raise ScanError(start, "닫히지 않은 템플릿 문자열")
    def looks_like_jsx_start(self) -> bool:
        if not self.jsx_enabled or self.peek() != "<":
            return False
        next_char = self.peek(1)
        if not (next_char.isalpha() or next_char in "_>/"):
            return False
        previous = self.tokens[-1].value if self.tokens else None
        if previous not in self.JSX_PREFIXES:
            return False
        # TSX의 제네릭 화살표 함수 `=<T>(...) =>`를 JSX 태그로 오인하지 않는다.
        tag_end = self.source.find(">", self.index + 1)
        if tag_end != -1:
            after = tag_end + 1
            while after < self.length and self.source[after].isspace():
                after += 1
            if after < self.length and self.source[after] == "(":
                return False
        return True
    def skip_jsx_quoted(self, quote: str) -> None:
        start = self.line
        self.advance()
        while self.index < self.length:
            ch = self.peek()
            if ch == "\\":
                self.advance(2)
            elif ch == quote:
                self.advance()
                return
            else:
                self.advance()
        raise ScanError(start, "닫히지 않은 JSX 속성 문자열")
    def scan_jsx_element(self) -> None:
        start = self.line
        depth = 0
        while self.index < self.length:
            if self.peek() != "<":
                raise ScanError(self.line, "JSX 태그 시작을 잃음")
            self.advance()
            closing = self.peek() == "/"
            if closing:
                self.advance()
            self_closing = False
            while self.index < self.length:
                ch = self.peek()
                if ch in "'\"":
                    self.skip_jsx_quoted(ch)
                elif ch == "{":
                    self.advance()
                    self.scan_code(stop_at_template_brace=True)
                elif ch == "/" and self.peek(1) == ">":
                    self_closing = True
                    self.advance(2)
                    break
                elif ch == ">":
                    self.advance()
                    break
                else:
                    self.advance()
            else:
                raise ScanError(start, "닫히지 않은 JSX 태그")
            if closing:
                depth -= 1
                if depth < 0:
                    raise ScanError(start, "대응하는 시작이 없는 JSX 닫기 태그")
            elif not self_closing:
                depth += 1
            if depth == 0:
                self.emit("<literal>", start)
                return
            while self.index < self.length and self.peek() != "<":
                if self.peek() == "{":
                    self.advance()
                    self.scan_code(stop_at_template_brace=True)
                else:
                    self.advance()
        raise ScanError(start, "닫히지 않은 JSX 요소")
    def scan_identifier(self) -> None:
        start = self.index
        line = self.line
        self.advance()
        while self.peek().isalnum() or self.peek() in "_$":
            self.advance()
        self.emit(self.source[start:self.index], line)
    def scan_number(self) -> None:
        line = self.line
        self.advance()
        while self.peek().isalnum() or self.peek() in "._":
            self.advance()
        self.emit("<literal>", line)
    def scan_code(self, stop_at_template_brace: bool = False) -> None:
        brace_depth = 0
        while self.index < self.length:
            ch = self.peek()
            if ch.isspace():
                self.advance()
                continue
            if ch == "/" and self.peek(1) == "/":
                self.skip_line_comment()
                continue
            if ch == "/" and self.peek(1) == "*":
                self.skip_block_comment()
                continue
            if ch in "'\"":
                self.skip_quoted(ch)
                continue
            if ch == "`":
                self.scan_template()
                continue
            if ch == "<" and self.looks_like_jsx_start():
                self.scan_jsx_element()
                continue
            if ch == "}" and stop_at_template_brace and brace_depth == 0:
                self.advance()
                return
            if ch == "{":
                self.emit(ch)
                brace_depth += 1
                self.advance()
                continue
            if ch == "}":
                self.emit(ch)
                if brace_depth > 0:
                    brace_depth -= 1
                self.advance()
                continue
            previous = self.tokens[-1].value if self.tokens else None
            if ch == "/" and previous in self.REGEX_PREFIXES:
                self.skip_regex()
                continue
            if ch.isalpha() or ch in "_$":
                self.scan_identifier()
                continue
            if ch.isdigit():
                self.scan_number()
                continue
            matched = next((item for item in self.MULTI if self.source.startswith(item, self.index)), None)
            if matched:
                self.emit(matched)
                self.advance(len(matched))
            else:
                self.emit(ch)
                self.advance()
        if stop_at_template_brace:
            raise ScanError(self.line, "닫히지 않은 템플릿 보간식")
    def run(self) -> list[Token]:
        self.scan_code()
        stack: list[Token] = []
        pairs = {")": "(", "]": "[", "}": "{"}
        for token in self.tokens:
            if token.value in "([{":
                stack.append(token)
            elif token.value in pairs:
                if not stack or stack[-1].value != pairs[token.value]:
                    raise ScanError(token.line, f"짝이 맞지 않는 {token.value}")
                stack.pop()
        if stack:
            raise ScanError(stack[-1].line, f"닫히지 않은 {stack[-1].value}")
        return self.tokens
def source_line(lines: list[str], line: int) -> str:
    if 1 <= line <= len(lines):
        return lines[line - 1].strip()
    return ""
def matching(tokens: list[Token], start: int, opening: str, closing: str, step: int = 1) -> int | None:
    depth = 0
    first, second = (opening, closing) if step > 0 else (closing, opening)
    for index in range(start, len(tokens) if step > 0 else -1, step):
        value = tokens[index].value
        if value == first:
            depth += 1
        elif value == second:
            depth -= 1
            if depth == 0:
                return index
    return None

def unwrap_parentheses(values: list[str]) -> list[str]:
    current = values
    while len(current) >= 2 and current[0] == "(" and current[-1] == ")":
        depth = 0
        wraps_all = True
        for index, value in enumerate(current):
            if value == "(":
                depth += 1
            elif value == ")":
                depth -= 1
                if depth == 0 and index != len(current) - 1:
                    wraps_all = False
                    break
        if not wraps_all:
            break
        current = current[1:-1]
    return current

def is_identifier(value: str) -> bool:
    return bool(value) and (value[0].isalpha() or value[0] in "_$") and all(
        character.isalnum() or character in "_$" for character in value[1:]
    )

def names_in_parameters(tokens: list[Token], opening: int, closing: int) -> set[str]:
    names: set[str] = set()
    nested = 0
    expect_name = True
    for token in tokens[opening + 1:closing]:
        value = token.value
        if value in "[{(":
            nested += 1
        elif value in "]})":
            nested -= 1
        elif nested == 0 and value == ",":
            expect_name = True
        elif nested == 0 and value in {":", "="}:
            expect_name = False
        elif expect_name and is_identifier(value):
            names.add(value)
            expect_name = False
    return names

def parameter_names(tokens: list[Token], opening_brace: int) -> set[str]:
    before = opening_brace - 1
    if before < 0:
        return set()
    if tokens[before].value == "=>":
        before -= 1
        if before >= 0 and is_identifier(tokens[before].value):
            return {tokens[before].value}
    if before < 0 or tokens[before].value != ")":
        return set()
    opening = matching(tokens, before, "(", ")", -1)
    if opening is None:
        return set()
    marker = tokens[opening - 1].value if opening else ""
    preceding = tokens[opening - 2].value if opening >= 2 else ""
    is_signature = marker in {"catch", "function"} or preceding == "function"
    is_signature = is_signature or (is_identifier(marker) and marker not in {"if", "for", "while", "switch", "with"})
    if not is_signature:
        return set()
    return names_in_parameters(tokens, opening, before)

def scope_model(tokens: list[Token]) -> tuple[list[dict[str, bool]], list[int]]:
    bindings: list[dict[str, bool]] = [{}]
    token_scopes = [0] * len(tokens)
    stack = [0]
    for index, token in enumerate(tokens):
        if token.value == "{":
            bindings.append({name: False for name in parameter_names(tokens, index)})
            stack.append(len(bindings) - 1)
        token_scopes[index] = stack[-1]
        if token.value in {"const", "let", "var"}:
            cursor, depth, expects_name = index + 1, 0, True
            while cursor < len(tokens):
                value = tokens[cursor].value
                if depth == 0 and value in {";", "}"}:
                    break
                if expects_name and depth == 0 and is_identifier(value):
                    following = [item.value for item in tokens[cursor + 1:cursor + 4]]
                    bindings[stack[-1]][value] = token.value == "const" and following == ["=", "new", "Map"]
                    expects_name = False
                if value in "([{":
                    depth += 1
                elif value in ")]}" and depth > 0:
                    depth -= 1
                elif value == "," and depth == 0:
                    expects_name = True
                cursor += 1
        if token.value == "}" and len(stack) > 1:
            stack.pop()
    return bindings, token_scopes

def inside_expression_arrow(tokens: list[Token], operator: int) -> bool:
    pairs = {")": "(", "]": "[", "}": "{"}
    for arrow in range(operator):
        if tokens[arrow].value != "=>" or arrow + 1 >= len(tokens) or tokens[arrow + 1].value == "{":
            continue
        depths = {"(": 0, "[": 0, "{": 0}
        contains_operator = True
        for item in tokens[arrow + 1:operator]:
            value = item.value
            if value in depths:
                depths[value] += 1
            elif value in pairs:
                if depths[pairs[value]] == 0:
                    contains_operator = False
                    break
                depths[pairs[value]] -= 1
            elif value in {",", ";"} and not any(depths.values()):
                contains_operator = False
                break
        if contains_operator:
            return True
    return False

def is_declared_map_get(tokens: list[Token], operator: int,
                        bindings: list[dict[str, bool]], token_scopes: list[int]) -> bool:
    if operator < 5 or tokens[operator - 1].value != ")":
        return False
    depth = 0
    for cursor in range(operator - 1, -1, -1):
        depth += tokens[cursor].value == ")"
        depth -= tokens[cursor].value == "("
        if depth == 0:
            if cursor < 3 or [item.value for item in tokens[cursor - 2:cursor]] != [".", "get"]:
                return False
            name = tokens[cursor - 3].value
            if inside_expression_arrow(tokens, operator):
                return False
            return bindings[token_scopes[operator]].get(name, False)
    return False

def contains_return_null(body: list[Token]) -> bool:
    for index, token in enumerate(body):
        if token.value != "return":
            continue
        values: list[str] = []
        depths = {"(": 0, "[": 0, "{": 0}
        for item in body[index + 1:]:
            value = item.value
            if value == ";" and not any(depths.values()):
                break
            if value == "}" and not any(depths.values()):
                break
            if value in depths:
                depths[value] += 1
            elif value in {")": "(", "]": "[", "}": "{"}:
                opening = {")": "(", "]": "[", "}": "{"}[value]
                depths[opening] -= 1
            values.append(value)
        if unwrap_parentheses(values) == ["null"]:
            return True
    return False

def js_findings(tokens: list[Token]) -> list[tuple[int, str]]:
    findings: list[tuple[int, str]] = []
    bindings, token_scopes = scope_model(tokens)
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if token.value in {"??", "??="}:
            findings.append((token.line, "nullish-coalescing-fallback"))
        elif token.value in {"||", "||="}:
            cursor = index + 1
            while cursor < len(tokens) and tokens[cursor].value == "(":
                cursor += 1
            if cursor + 1 < len(tokens) and tokens[cursor].value == "[" and tokens[cursor + 1].value == "]" and not is_declared_map_get(tokens, index, bindings, token_scopes):
                findings.append((token.line, "or-empty-array-fallback"))
        elif token.value == "catch":
            cursor = index + 1
            if cursor < len(tokens) and tokens[cursor].value == "(":
                end_parameters = matching(tokens, cursor, "(", ")")
                if end_parameters is None:
                    raise ScanError(token.line, "닫히지 않은 catch 매개변수")
                cursor = end_parameters + 1
            if cursor < len(tokens) and tokens[cursor].value == "{":
                end_body = matching(tokens, cursor, "{", "}")
                if end_body is None:
                    raise ScanError(token.line, "닫히지 않은 catch 블록")
                body = tokens[cursor + 1:end_body]
                meaningful = [item.value for item in body if item.value != ";"]
                if not meaningful:
                    findings.append((token.line, "bare-catch"))
                elif contains_return_null(body):
                    findings.append((token.line, "catch-return-null"))
        index += 1
    return findings

def collect_files(arguments: list[str]) -> list[str]:
    if arguments:
        return arguments
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise ScanError(0, "git ls-files 실패")
    return [os.fsdecode(item) for item in result.stdout.split(b"\0") if item]

def main() -> int:
    try:
        candidates = collect_files(sys.argv[1:])
    except ScanError as error:
        print(f"NOT_RUN: {error.message} — 검사 대상 목록을 만들 수 없음")
        return 2
    files = [path for path in candidates if Path(path).suffix.lower() in TARGET_SUFFIXES]
    missing = next((path for path in files if not Path(path).is_file()), None)
    if missing:
        print(f"NOT_RUN: {missing}: 지정된 검사 대상이 존재하지 않음")
        return 2
    if not files:
        print("CHECKED_FILES: 0")
        print("NOT_RUN: 지정된 파일 중 실존하는 대상 0건(스캔 무효, P20 fail-closed)")
        return 2
    violations = 0
    invalid = 0
    for filename in files:
        path = Path(filename)
        try:
            source = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            print(f"NOT_RUN: {filename}: 파일 읽기 실패 — {error.__class__.__name__}")
            invalid += 1
            continue
        lines = source.splitlines()
        findings: list[tuple[int, str]] = []
        try:
            if path.suffix.lower() == ".py":
                tree = ast.parse(source, filename=filename)
                findings = [
                    (node.lineno, "bare-except")
                    for node in ast.walk(tree)
                    if isinstance(node, ast.ExceptHandler) and node.type is None
                ]
            else:
                findings = js_findings(
                    JSLexer(source, jsx_enabled=path.suffix.lower() in {".jsx", ".tsx"}).run()
                )
        except SyntaxError as error:
            print(f"NOT_RUN: {filename}:{error.lineno or 0}: Python 문법 판정 실패 — {error.msg}")
            invalid += 1
            continue
        except ScanError as error:
            print(f"NOT_RUN: {filename}:{error.line}: JavaScript/TypeScript 토큰 판정 실패 — {error.message}")
            invalid += 1
            continue
        for line, marker in findings:
            print(f"FAIL: {filename}:{line}: {marker} — {source_line(lines, line)}")
            violations += 1
    print(f"CHECKED_FILES: {len(files)}")
    if invalid:
        print(f"NOT_RUN: 문법 판정 실패 파일 {invalid}건(스캔 무효, P20 fail-closed)")
        return 2
    if violations:
        print("FAIL: P3 조용한 실패 패턴 발견 — 명시적 assertX() 관문으로 대체할 것")
        return 1
    print("PASS: 조용한 실패 패턴 0건 (선언된 Map.get 컬렉션 기본값은 허용)")
    return 0
raise SystemExit(main())
PY
