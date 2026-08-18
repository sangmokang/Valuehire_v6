#!/usr/bin/env bash
# acceptance-principles-check.sh — docs/sot/principles.yaml 스키마 완전성 + status 회귀(ratchet) 검사 (AC1~AC3)
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

FILE="docs/sot/principles.yaml"
REQUIRED_COUNT=32
REQUIRED_FIELDS=(id principle mechanism_expected mechanism_found status evidence)
VALID_STATUSES=(완전 부분 없음 해당없음 미확인)
# codex(V1) D1 반증(2026-08-19): id 개수·중복만 보면 P1을 P999로 바꿔도 통과한다.
# 32개 항목의 정확한 id 집합을 고정해 대조한다(docs/sot/coding-principles.md §1·§1-B·검증체제 기준).
EXPECTED_IDS="P1 P2 P3 P4 P5 P6 P7 P8 P9 P10 P11 P12 P13 P14 P15 P16 P17 P18 P19 P20 P21 P22 §1-B-1 §1-B-2 §1-B-3 §1-B-4 §1-B-5 V-1 V-2 V-3 V-4 V-5"

if [ ! -f "$FILE" ]; then
  echo "FAIL: $FILE 없음"
  exit 1
fi

# 외부 라이브러리(pyyaml) 의존 금지 — docs/sot/mechanism-registry.yaml 파서(scripts/verify/
# check-mechanism-registry.sh) 관례를 따라 이 파일 전용 최소 파서를 표준 파이썬으로 직접 짠다.
# 계약: 항목은 `- id: 값`으로 시작, 그 뒤 2칸 들여쓴 `key: 값` 줄이 항목당 정확히 6개(자기 자신 포함).
# 값은 큰따옴표로 감싸거나 `null` 리터럴만 허용(그 외 형태 = 파싱 실패로 fail-closed).
result=$(python3 - "$FILE" "$REQUIRED_COUNT" "$EXPECTED_IDS" <<'PYEOF'
import re, sys

path, required_count, expected_ids_raw = sys.argv[1], int(sys.argv[2]), sys.argv[3]
expected_ids = set(expected_ids_raw.split())
required_fields = ["id", "principle", "mechanism_expected", "mechanism_found", "status", "evidence"]
valid_statuses = {"완전", "부분", "없음", "해당없음", "미확인"}

with open(path, encoding="utf-8") as f:
    lines = f.readlines()

item_start = re.compile(r'^- id:\s*(.+)$')
field_line = re.compile(r'^  ([a-z_]+):\s*(.*)$')

BARE_OK = re.compile(r'^[A-Za-z0-9._§-]+$')
# codex(V1) D2 반증(2026-08-19): 예전엔 "첫/끝 글자가 따옴표"만 보고 중간에 깨진 따옴표가
# 섞인 값도 통과시켰다(독립 YAML 해석기는 이를 문법 오류로 거부함). fullmatch로 중간에
# 따옴표가 하나도 더 없어야만 유효한 값으로 인정한다(fail-closed).
QUOTED_OK = re.compile(r'^"[^"]*"$')

def unquote(raw):
    raw = raw.rstrip("\n").strip()
    if raw == "null":
        return None
    if QUOTED_OK.match(raw):
        return raw[1:-1]
    if BARE_OK.match(raw):
        return raw
    print(f"FAIL: 값이 계약 밖 형태(온전한 큰따옴표 쌍/null/영숫자._§- 아님): {raw!r}")
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

missing_ids = expected_ids - ids_seen
extra_ids = ids_seen - expected_ids
if missing_ids or extra_ids:
    print(f"FAIL: id 집합 불일치 — 누락: {sorted(missing_ids)} / 예상 밖: {sorted(extra_ids)}")
    sys.exit(1)

print("PASS: 스키마 32/32 유효, id 집합 정확히 일치, 중복 0건")
PYEOF
) && rc=0 || rc=$?
echo "$result"
if [ "$rc" -ne 0 ] || ! echo "$result" | grep -q '^PASS:'; then
  exit 1
fi

# AC3 — status 회귀(ratchet): "직전 커밋(HEAD)"이 아니라 "서버에 이미 올라간 origin/main"과
# 대조한다. codex(V1) D3 반증(2026-08-19, 치명적): HEAD와 대조하면 실제 push 시점엔 이미
# 모든 변경이 커밋된 상태라 HEAD==작업파일이 되어 회귀를 항상 놓친다. origin/main에 이
# 파일이 아직 없으면(최초 추가) 회귀 비교를 건너뛴다 — 비교 대상 자체가 없음.
# HEAD로 조용히 대체하지 않는다 — 그 폴백 자체가 방금 고친 D3 취약점을 그대로 재도입하므로
# (P13 검사약화 탐지가 이 이유로 실제 커밋을 막아 잡아낸 결함, 2026-08-19). origin/main 참조
# 자체를 못 찾으면 사람이 볼 수 있게 실패한다(fail-closed) — 조용히 격하하지 않는다.
# codex(V1) D3 2차 반증(2026-08-19, 치명적): 로컬에 저장된 "origin/main"은 마지막으로 내려받은
# 시점의 사본일 뿐이다 — 서버는 이미 새 기준으로 앞서 있는데 이 컴퓨터가 그걸 안 내려받았으면,
# 오래된(파일이 아직 없던) 사본과 비교해 회귀 검사 자체가 통째로 생략된다. 매번 비교 직전
# 실제로 새로 내려받는다 — `|| true`로 실패를 삼키지 않는다(fail-closed. 기존 관례인
# acceptance-0-5.sh:85의 `git fetch ... || true`는 이 자리에서 그대로 베끼지 않는다).
if ! git fetch --quiet origin main; then
  echo "FAIL: git fetch origin main 실패 — 서버 최신 기준을 확인할 수 없어 안전하게 실패 처리(fail-closed). 네트워크·자격증명을 확인하라"
  exit 1
fi
BASE_REF="origin/main"
if ! git cat-file -e "$BASE_REF" 2>/dev/null; then
  echo "FAIL: $BASE_REF 참조를 찾을 수 없음 — 회귀 비교 기준이 없어 안전하게 실패 처리(fail-closed). 'git fetch origin'을 먼저 실행하라"
  exit 1
fi
if git cat-file -e "$BASE_REF:$FILE" 2>/dev/null; then
  regressed=$(python3 - "$FILE" "$BASE_REF" <<'PYEOF'
import re, subprocess, sys

path, base_ref = sys.argv[1], sys.argv[2]
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

old_raw = subprocess.run(["git", "show", f"{base_ref}:{path}"], capture_output=True, text=True, check=True).stdout
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
