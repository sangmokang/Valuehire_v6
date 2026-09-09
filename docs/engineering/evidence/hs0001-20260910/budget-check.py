import ast
import json
import sys
import tempfile
from pathlib import Path


def validate(files: list[Path]) -> bool:
    if not files:
        print("FAIL: 검사 대상 0개")
        return False
    valid = True
    for path in files:
        lines = path.read_text().splitlines()
        within = len(lines) <= 600
        print(f"{'PASS' if within else 'FAIL'}: {path}: {len(lines)} lines / hard600")
        valid = valid and within
        if path.suffix == ".py":
            for node in ast.walk(ast.parse(path.read_text())):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    size = (node.end_lineno or node.lineno) - node.lineno + 1
                    print(f"{'PASS' if size <= 100 else 'FAIL'}: {node.name}: {size} / hard100")
                    valid = valid and size <= 100
    return valid


if __name__ == "__main__":
    if sys.argv[1:] == ["--boundaries"]:
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "boundary.txt"
            path.write_text("x\n" * 600)
            assert validate([path])
            path.write_text("x\n" * 601)
            assert not validate([path])
            assert not validate([])
        print("PASS: same validator hard600 accepted / hard601 rejected / zero rejected")
    else:
        manifest = json.loads(Path(sys.argv[1]).read_text())
        paths = [Path(p) for p in manifest["files"] if Path(p).suffix in {".py", ".sh", ".yml"}]
        sys.exit(0 if validate(paths) else 1)
