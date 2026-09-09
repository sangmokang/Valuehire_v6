#!/usr/bin/env bash
# V1 final: show why mutant m04 (TOP_KEYS=()) let the two "top ..." tests pass for the wrong reason.
set -u; unset BASH_ENV ENV GIT_DIR GIT_WORK_TREE
D=$(mktemp -d -t v1final-0002); trap 'rm -rf "$D"' EXIT
cp "$V1_REPO/scripts/verify/list-workflow-steps.py" "$D/reader.py"
python3 - "$D/reader.py" <<'PY'
import sys,pathlib
p=pathlib.Path(sys.argv[1]); t=p.read_text(); old='TOP_KEYS = ("name", "on", "permissions", "jobs", "concurrency")'; assert t.count(old)==1
p.write_text(t.replace(old,'TOP_KEYS = ()'))
PY
echo "--- mutated reader on the untouched candidate verify.yml:"; python3 "$D/reader.py" "$V1_REPO/.github/workflows/verify.yml"; echo "rc=$?"
echo "--- test expectation for 'top defaults run shell is rejected': substring '워크플로를 정규 형식으로 읽지 못했다' (present above regardless of which top key tripped)"
