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

# 외부 라이브러리(pyyaml) 의존 금지 — docs/sot/mechanism-registry.yaml 파서(scripts/verify/
# check-mechanism-registry.sh) 관례를 따라 이 파일 전용 최소 파서를 표준 파이썬으로 직접 짠다.
# 계약: 항목은 `- id: 값`으로 시작, 그 뒤 2칸 들여쓴 `key: 값` 줄이 항목당 정확히 6개(자기 자신 포함).
# 값은 큰따옴표로 감싸거나 `null` 리터럴만 허용(그 외 형태 = 파싱 실패로 fail-closed).
result=$(python3 - "$FILE" "$REQUIRED_COUNT" <<'PYEOF'
import re, sys

path, required_count = sys.argv[1], int(sys.argv[2])
required_fields = ["id", "principle", "mechanism_expected", "mechanism_found", "status", "evidence"]
valid_statuses = {"완전", "부분", "없음", "해당없음", "미확인"}

with open(path, encoding="utf-8") as f:
    lines = f.readlines()

item_start = re.compile(r'^- id:\s*(.+)$')
field_line = re.compile(r'^  ([a-z_]+):\s*(.*)$')

BARE_OK = re.compile(r'^[A-Za-z0-9._-]+$')

def unquote(raw):
    raw = raw.rstrip("\n").strip()
    if raw == "null":
        return None
    if len(raw) >= 2 and raw[0] == '"' and raw[-1] == '"':
        return raw[1:-1]
    if BARE_OK.match(raw):
        return raw
    print(f"FAIL: 값이 계약 밖 형태(따옴표 없음/null 아님/영숫자._- 아님): {raw!r}")
    sys.exit(1)

items = []
current = None
for lineno, line in enumerate(lines, 1):
    if not line.strip() or line.lstrip().startswith("#"):
        continue
    m = item_start.match(line)
    if m:
        if current is not None:
            items.append(current)
        current = {"id": unquote(m.group(1))}
        continue
    m = field_line.match(line)
    if m and current is not None:
        key, val = m.group(1), m.group(2)
        if key in current:
            print(f"FAIL: {lineno}행 — 같은 항목에 필드 '{key}' 중복")
            sys.exit(1)
        current[key] = unquote(val)
        continue
    print(f"FAIL: {lineno}행 — 계약 밖 형태: {line.rstrip()!r}")
    sys.exit(1)
if current is not None:
    items.append(current)

if len(items) != required_count:
    print(f"FAIL: 항목 수 {len(items)} != {required_count}")
    sys.exit(1)

ids_seen = set()
for item in items:
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

print("PASS: 스키마 32/32 유효, id 중복 0건")
PYEOF
) && rc=0 || rc=$?
echo "$result"
if [ "$rc" -ne 0 ] || ! echo "$result" | grep -q '^PASS:'; then
  exit 1
fi

# AC3 — status 회귀(ratchet): 직전 커밋(HEAD)의 principles.yaml과 대조해 등급이 나빠진 항목이 있으면 실패.
# HEAD에 이 파일이 아직 없으면(최초 추가 커밋) 회귀 비교를 건너뛴다 — 비교 대상 자체가 없음.
if git cat-file -e "HEAD:$FILE" 2>/dev/null; then
  regressed=$(python3 - "$FILE" <<'PYEOF'
import re, subprocess, sys

path = sys.argv[1]
order = {"완전": 4, "부분": 3, "미확인": 2, "해당없음": 2, "없음": 1}
item_start = re.compile(r'^- id:\s*(.+)$')
field_line = re.compile(r'^  ([a-z_]+):\s*(.*)$')

def unquote(raw):
    raw = raw.rstrip("\n").strip()
    if raw == "null":
        return None
    if len(raw) >= 2 and raw[0] == '"' and raw[-1] == '"':
        return raw[1:-1]
    return raw  # 회귀검사는 status 값(항상 bare 한글 단어)만 쓰므로 관용적으로 허용

def parse_id_status(text):
    result = {}
    current_id = None
    for line in text.splitlines():
        m = item_start.match(line)
        if m:
            current_id = unquote(m.group(1))
            continue
        m = field_line.match(line)
        if m and current_id is not None and m.group(1) == "status":
            result[current_id] = unquote(m.group(2))
    return result

old_raw = subprocess.run(["git", "show", f"HEAD:{path}"], capture_output=True, text=True, check=True).stdout
old = parse_id_status(old_raw)

with open(path, encoding="utf-8") as f:
    new = parse_id_status(f.read())

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
