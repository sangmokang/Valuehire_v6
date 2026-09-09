import ast, json, sys
files = json.load(open("artifacts/hs-next-20260910/final-candidate-files.json"))["files"]
for f in files:
    lines = open(f, encoding="utf-8").read().splitlines()
    print(f"{f}: {len(lines)} lines -> {'OK' if len(lines) <= 600 else 'OVER600'}{' (soft300 exceeded)' if len(lines) > 300 else ''}")
    if f.endswith(".py"):
        for n in ast.walk(ast.parse(open(f, encoding="utf-8").read())):
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                s = (n.end_lineno or n.lineno) - n.lineno + 1
                print(f"   def {n.name}: {s} lines -> {'OK' if s <= 100 else 'OVER100'}{' (soft60 exceeded)' if s > 60 else ''}")
# staged blob check for the python reader
import subprocess
blob = subprocess.run(["git", "show", ":scripts/verify/list-workflow-steps.py"], capture_output=True, text=True).stdout
print("INDEX blob functions:", [(n.name, (n.end_lineno or n.lineno) - n.lineno + 1) for n in ast.walk(ast.parse(blob)) if isinstance(n, ast.FunctionDef)])
head = subprocess.run(["git", "show", "HEAD:scripts/verify/list-workflow-steps.py"], capture_output=True, text=True).stdout
print("HEAD blob functions:", [(n.name, (n.end_lineno or n.lineno) - n.lineno + 1) for n in ast.walk(ast.parse(head)) if isinstance(n, ast.FunctionDef)])
