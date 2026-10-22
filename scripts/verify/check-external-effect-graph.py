#!/usr/bin/env python3
"""Check declared effect entries against staged, statically reachable network calls.

Expected intent comes from a versioned declaration, never filenames. This bounded
analysis proves a syntactic call path, not execution, authentication, or delivery.
Python functions/static imports and JS function declarations/static named imports
are supported. Dynamic imports/evaluation, computed calls and closures in a visited
JS function are rejected; arbitrary JS/TS semantics are outside this checker.
"""
import ast
import json
from pathlib import PurePosixPath
import re
import subprocess


CONTRACT = "scripts/verify/external-effect-contract.json"
NETWORK = {"urllib.request.urlopen", "requests.request", "requests.get", "requests.post",
           "requests.put", "requests.patch", "requests.delete", "httpx.request",
           "httpx.get", "httpx.post", "node:https.request", "node:https.get",
           "node:http.request", "node:http.get", "https.request", "https.get",
           "http.request", "http.get"}


class Invalid(Exception):
    pass


def git(*args):
    result = subprocess.run(["git", *args], capture_output=True)
    if result.returncode:
        raise Invalid("Git 입력을 읽지 못함")
    return result.stdout


def files(ref=""):
    listing = git("ls-tree", "-rz", ref) if ref else git("ls-files", "--stage", "-z")
    result = {}
    for row in listing.split(b"\0"):
        if row:
            meta, path = row.split(b"\t", 1)
            parts = meta.split()
            if not ref and parts[2] != b"0":
                raise Invalid("해결되지 않은 인덱스 충돌")
            result[path.decode()] = parts[0].decode()
    return result


def read(path, ref="", mapping=None):
    mapping = files(ref) if mapping is None else mapping
    if mapping.get(path) not in ("100644", "100755"):
        raise Invalid("선언/소스가 없거나 일반 파일이 아님")
    return git("show", ref + ":" + path).decode()


def declaration(mapping, ref=""):
    if CONTRACT not in mapping:
        return set()
    data = json.loads(read(CONTRACT, ref, mapping))
    if not (type(data) is dict and set(data) == {"version", "entries"} and
            type(data["version"]) is int and data["version"] == 1 and type(data["entries"]) is list):
        raise Invalid("선언 스키마 오류")
    result = set()
    for item in data["entries"]:
        if not (type(item) is dict and set(item) == {"path", "export"} and
                type(item["path"]) is str and type(item["export"]) is str and
                re.fullmatch(r"[A-Za-z_$][A-Za-z0-9_$]*", item["export"])):
            raise Invalid("선언 entry 오류")
        path = PurePosixPath(item["path"])
        if path.is_absolute() or ".." in path.parts or str(path) != item["path"]:
            raise Invalid("선언 경로 오류")
        key = (str(path), item["export"])
        if key in result:
            raise Invalid("중복 선언")
        result.add(key)
    return result


def local_path(path, target, mapping, python=False):
    if python:
        parent = PurePosixPath(path).parent
        candidates = [str(parent / (target.replace(".", "/") + ".py"))]
    else:
        if not target.startswith("."):
            return None
        parts = list(PurePosixPath(path).parent.parts)
        for piece in target.split("/"):
            if piece == "..":
                if not parts:
                    raise Invalid("저장소 밖 import")
                parts.pop()
            elif piece not in ("", "."):
                parts.append(piece)
        base = "/".join(parts)
        candidates = [base, base + ".js", base + ".mjs"]
    found = [p for p in candidates if p in mapping]
    if len(found) != 1:
        raise Invalid("로컬 import 해석 불가")
    return found[0]


def dotted(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        root = dotted(node.value)
        return root + "." + node.attr if root else None
    return None


def python_function(path, name, mapping, seen):
    module = ast.parse(read(path, mapping=mapping))
    functions = {n.name: n for n in module.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    if name not in functions:
        raise Invalid("선언 함수 없음")
    imports = {}
    for node in module.body:
        if isinstance(node, ast.Import):
            for item in node.names:
                imports[item.asname or item.name.split(".")[0]] = (item.name if item.asname else item.name.split(".")[0], None)
        elif isinstance(node, ast.ImportFrom):
            if node.level or node.module is None or any(n.name == "*" for n in node.names):
                raise Invalid("지원하지 않는 Python import")
            for item in node.names:
                imports[item.asname or item.name] = (node.module + "." + item.name, (node.module, item.name))
    function = functions[name]
    nodes = [child for statement in function.body for child in ast.walk(statement)]
    if any(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)) for n in nodes):
        raise Invalid("중첩 함수 분석은 지원하지 않음")
    arguments = function.args.posonlyargs + function.args.args + function.args.kwonlyargs
    arguments += [arg for arg in (function.args.vararg, function.args.kwarg) if arg is not None]
    shadow = {arg.arg for arg in arguments}
    shadow |= {n.id for n in nodes if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store)}
    shadow |= {n.id for statement in module.body if isinstance(statement, (ast.Assign, ast.AnnAssign))
               for n in ast.walk(statement) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store)}
    calls = [dotted(n.func) for n in nodes if isinstance(n, ast.Call)]
    if any(c in ("eval", "exec", "__import__", "importlib.import_module", "getattr") for c in calls):
        raise Invalid("동적 Python 호출은 지원하지 않음")
    for call in calls:
        if call is None:
            continue
        root, _, suffix = call.partition(".")
        origin = imports[root][0] + ("." + suffix if suffix else "") if root in imports else call
        if origin in NETWORK and root not in shadow:
            return True
    for call in calls:
        if call in functions and call not in shadow and reachable(path, call, mapping, seen):
            return True
        if call in imports and imports[call][1] and call not in shadow:
            target, exported = imports[call][1]
            candidate = str(PurePosixPath(path).parent / (target.replace(".", "/") + ".py"))
            if candidate in mapping and reachable(candidate, exported, mapping, seen):
                return True
    return False


TOKEN = re.compile(r"\s+|//[^\n]*|/\*[\s\S]*?\*/|" +
                   r"'(?:\\.|[^'\\])*'|\"(?:\\.|[^\"\\])*\"|`(?:\\.|[^`\\])*`|" +
                   r"/(?:\\.|[^/\\\n\[]|\[(?:\\.|[^\]\\\n])*\])+/[dgimsuvy]*|" +
                   r"[A-Za-z_$][A-Za-z0-9_$]*|=>|\?\.|[^\s]", re.DOTALL)


def tokens(source):
    result = []
    for match in TOKEN.finditer(source):
        token = match.group()
        if token.isspace() or token.startswith(("//", "/*")):
            continue
        if token[0] in ("'", '"'):
            # Preserve static import strings, while hiding strings containing fake call text.
            result.append(("string", ast.literal_eval(token)))
        elif token[0] == "`":
            # Templates are opaque. Only simple interpolations are recognized;
            # a nested template/quoted expression must never expose fake code.
            content, offset = token[1:-1], 0
            while (start := content.find("${", offset)) != -1:
                end = content.find("}", start + 2)
                if end == -1 or any(c in content[start + 2:end] for c in "{'\"`\\"):
                    raise Invalid("복합 JS template 분석은 지원하지 않음")
                offset = end + 1
            result.append(("template", ""))
        elif token[0] == "/":
            if len(token) == 1:
                raise Invalid("모호한 JS slash 분석은 지원하지 않음")
            result.append(("regex", ""))
        else:
            result.append(("code", token))
    return result


def close(values, start, opening, closing):
    depth = 0
    for i in range(start, len(values)):
        if values[i] == opening:
            depth += 1
        elif values[i] == closing:
            depth -= 1
            if depth == 0:
                return i
    raise Invalid("JS 구문 경계 해석 불가")


def javascript_function(path, name, mapping, seen):
    text = read(path, mapping=mapping)
    syntax = subprocess.run(["node", "--input-type=module", "--check"],
                            input=text, capture_output=True, text=True)
    if syntax.returncode:
        raise Invalid("선언 JS 소스 구문 오류")
    source = tokens(text)
    values = [value if kind == "code" else "" for kind, value in source]
    functions, imports = {}, {}
    for i, value in enumerate(values):
        if value == "import" and values[i + 1:i + 2] != ["{"]:
            raise Invalid("정적 named import 외 JS import는 지원하지 않음")
        if value == "function" and i + 2 < len(values) and values[i + 1] and values[i + 2] == "(":
            end = close(values, i + 2, "(", ")")
            if end + 1 >= len(values) or values[end + 1] != "{":
                raise Invalid("지원하지 않는 JS 함수")
            body_end = close(values, end + 1, "{", "}")
            key = values[i + 1]
            if key in functions:
                raise Invalid("중복/중첩 함수명")
            functions[key] = (source[i + 3:end], source[end + 2:body_end])
        if value == "import" and i + 1 < len(values) and values[i + 1] == "{":
            end = close(values, i + 1, "{", "}")
            if values[end + 1:end + 2] != ["from"] or source[end + 2][0] != "string":
                raise Invalid("지원하지 않는 JS import")
            target = source[end + 2][1]
            for part in " ".join(values[i + 2:end]).split(","):
                names = part.split()
                if len(names) == 1:
                    imports[names[0]] = (target, names[0])
                elif len(names) == 3 and names[1] == "as":
                    imports[names[2]] = (target, names[0])
                else:
                    raise Invalid("지원하지 않는 JS import alias")
    if name not in functions:
        raise Invalid("선언 JS 함수 없음")
    params, body = functions[name]
    words = [v if k == "code" else "" for k, v in body]
    if any(k == "template" for k, _ in params + body) or any(v in ("=>", "function", "?.") for v in words):
        raise Invalid("지원하지 않는 JS closure/template/optional call")
    if any(words[i:i + 2] in (["import", "("], ["eval", "("], ["Function", "("])
           for i in range(len(words) - 1)):
        raise Invalid("동적 JS 호출은 지원하지 않음")
    if any(words[i] == "]" and words[i + 1] == "(" for i in range(len(words) - 1)):
        raise Invalid("계산된 JS 호출은 지원하지 않음")
    # Conservative binding check: any module assignment to a primitive name prevents proof.
    shadow = {v for k, v in params if k == "code" and re.fullmatch(r"[A-Za-z_$][\w$]*", v)}
    for i, value in enumerate(values):
        if value in ("const", "let", "var", "class") and i + 1 < len(values):
            binding = values[i + 1]
            if binding in ("{", "["):
                end = close(values, i + 1, binding, "}" if binding == "{" else "]")
                shadow.update(v for v in values[i + 2:end] if re.fullmatch(r"[A-Za-z_$][\w$]*", v))
            elif re.fullmatch(r"[A-Za-z_$][\w$]*", binding):
                shadow.add(binding)
            else:
                raise Invalid("JS 바인딩 해석 불가")
        if value == "catch" and values[i + 1:i + 2] == ["("]:
            shadow.update(values[i + 2:close(values, i + 1, "(", ")")])
        if i + 1 < len(values) and values[i + 1] == "=" and value:
            shadow.add(value)
    # The entry itself is a function declaration; other direct local function calls remain valid.
    call_names = [words[i] for i in range(len(words) - 1)
                  if words[i + 1] == "(" and words[i] and (i == 0 or words[i - 1] != ".")]
    if "fetch" in call_names and "fetch" not in shadow and "fetch" not in imports and "fetch" not in functions:
        return True
    for call in call_names:
        if call in functions and call not in shadow:
            if reachable(path, call, mapping, seen):
                return True
        elif call in imports:
            target, exported = imports[call]
            if target + "." + exported in NETWORK and call not in shadow:
                return True
            if target.startswith(".") and call not in shadow:
                if reachable(local_path(path, target, mapping), exported, mapping, seen):
                    return True
    return False


def reachable(path, name, mapping, seen):
    key = (path, name)
    if key in seen:
        return False
    seen = seen | {key}
    if path.endswith(".py"):
        return python_function(path, name, mapping, seen)
    if path.endswith((".js", ".mjs")):
        return javascript_function(path, name, mapping, seen)
    raise Invalid("선언 entry 언어는 Python/JS 정적 부분집합만 지원")


def main():
    current = files()
    head = subprocess.run(["git", "rev-parse", "--verify", "-q", "HEAD"], capture_output=True)
    if head.returncode not in (0, 1):
        raise Invalid("HEAD 조회 실패")
    previous_files = files("HEAD") if head.returncode == 0 else {}
    previous = declaration(previous_files, "HEAD")
    expected = declaration(current)
    if previous - expected or (CONTRACT in previous_files and CONTRACT not in current):
        raise Invalid("기존 외부 효과 선언 제거/축소")
    for path, name in sorted(expected):
        if not reachable(path, name, current, set()):
            raise Invalid("선언 entry에 정적 네트워크 호출 경로 없음")
    print("PASS: 외부 효과 선언", len(expected), "개 정적 호출 경로 확인; 실행/인증 증명은 별도")
    return 0


if __name__ == "__main__":
    try:
        status = main()
    except (Invalid, ValueError, SyntaxError, OSError, IndexError) as exc:
        reason = str(exc) if isinstance(exc, Invalid) else type(exc).__name__
        print("BLOCKED: 외부 효과 정적 검증 불가 (fail-closed):", reason)
        status = 2
    raise SystemExit(status)
