#!/usr/bin/env bash
# acceptance-principles-check.sh — docs/sot/principles.yaml 스키마 완전성 + status 회귀(ratchet) 검사 (AC1~AC3)
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

FILE="docs/sot/principles.yaml"
REQUIRED_COUNT=32
REQUIRED_FIELDS=(id principle mechanism_expected mechanism_found status evidence)
VALID_STATUSES=(완전 부분 없음 해당없음 미확인)
RATCHET_ORDER_JSON='{"완전": 4, "부분": 3, "미확인": 2, "없음": 1, "해당없음": 2}'

if [ ! -f "$FILE" ]; then
  echo "FAIL: $FILE 없음"
  exit 1
fi

result=$(python3 - "$FILE" "$REQUIRED_COUNT" <<'PYEOF'
import sys, json
try:
    import yaml
except ImportError:
    print("FAIL: pyyaml 미설치 — python3 -m pip install pyyaml 필요")
    sys.exit(1)

path, required_count = sys.argv[1], int(sys.argv[2])
required_fields = ["id", "principle", "mechanism_expected", "mechanism_found", "status", "evidence"]
valid_statuses = {"완전", "부분", "없음", "해당없음", "미확인"}

with open(path, encoding="utf-8") as f:
    data = yaml.safe_load(f)

if not isinstance(data, list):
    print("FAIL: 최상위가 배열이 아님")
    sys.exit(1)

if len(data) != required_count:
    print(f"FAIL: 항목 수 {len(data)} != {required_count}")
    sys.exit(1)

ids_seen = set()
for item in data:
    if not isinstance(item, dict):
        print(f"FAIL: 배열 원소가 dict 아님: {item!r}")
        sys.exit(1)
    missing = [k for k in required_fields if k not in item]
    if missing:
        print(f"FAIL: {item.get('id', '?')} 필드 누락: {missing}")
        sys.exit(1)
    if item["status"] not in valid_statuses:
        print(f"FAIL: {item['id']} status 값 불허: {item['status']}")
        sys.exit(1)
    if item["id"] in ids_seen:
        print(f"FAIL: id 중복: {item['id']}")
        sys.exit(1)
    ids_seen.add(item["id"])

print(f"PASS: 스키마 32/32 유효, id 중복 0건")
PYEOF
)
rc=$?
echo "$result"
if [ "$rc" -ne 0 ] || ! echo "$result" | grep -q '^PASS:'; then
  exit 1
fi

# AC3 — status 회귀(ratchet): 직전 커밋(HEAD)의 principles.yaml과 대조해 등급이 나빠진 항목이 있으면 실패.
# HEAD에 이 파일이 아직 없으면(최초 추가 커밋) 회귀 비교를 건너뛴다 — 비교 대상 자체가 없음.
if git cat-file -e "HEAD:$FILE" 2>/dev/null; then
  regressed=$(python3 - "$FILE" <<'PYEOF'
import sys, subprocess
import yaml

path = sys.argv[1]
order = {"완전": 4, "부분": 3, "미확인": 2, "해당없음": 2, "없음": 1}

old_raw = subprocess.run(["git", "show", f"HEAD:{path}"], capture_output=True, text=True, check=True).stdout
old = {x["id"]: x["status"] for x in yaml.safe_load(old_raw)}

with open(path, encoding="utf-8") as f:
    new = {x["id"]: x["status"] for x in yaml.safe_load(f)}

bad = []
for pid, new_status in new.items():
    old_status = old.get(pid)
    if old_status is None:
        continue
    if order.get(new_status, 0) < order.get(old_status, 0):
        bad.append(f"{pid}: {old_status} -> {new_status}")

if bad:
    print("REGRESSED:" + ";".join(bad))
else:
    print("NO_REGRESSION")
PYEOF
)
  if echo "$regressed" | grep -q '^REGRESSED:'; then
    echo "FAIL: status 회귀 발견 — $regressed"
    exit 1
  fi
  echo "PASS: 회귀 0건 ($regressed)"
fi

echo "PASS: principles.yaml 32/32 스키마 유효, 회귀 0건"
exit 0
