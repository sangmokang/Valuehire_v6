#!/usr/bin/env bash
# acceptance-hs-portal-constants.sh — G3: 운영 상수·portal locator(URL·포트·도메인·CSS
# selector·XPath)는 저장소 루트의 정확한 contracts/ 밖에 존재할 수 없다 (P22 · 웹 자동화 5조 1번).
#
# 계약: docs/engineering/humansearch-g3-portal-constants-goal-2026-08-12.md §1⑩
#   exit 0 = 깨끗한 트리 | 1 = 위반 발견(금지값·contracts 구역 위반·배선 훼손)
#   exit 2 = 검사 불능(패턴 계약 부재/깨짐, 열거·읽기 실패, 제품 루트 부재, 하한 미달)
#
# 경계 규칙 (사전감사 벡터 8):
#   허용 구역은 git ls-files 상대 경로의 정확한 `contracts/` 접두뿐이다. 부분 문자열
#   (a/contracts/, contracts-evil/) 은 전부 검사 대상이다. contracts/ 값에는 금지 패턴을
#   적용하지 않는 대신 구역 자체를 검사한다(정규 파일·비실행·허용 확장자만).
#   docs/ 디렉터리 전체를 면제하지 않는다. 그 안에서도 문서 확장자(md·yaml·yml·txt·html)이고
#   Git 추적 모드가 100644인 정규 비실행 파일만 면제하며 CHECKED 에 세지 않는다. 그 조건을
#   벗어난 docs 파일(실행 코드·실행 권한 문서)은 전역 검사 대상이다(V1 결함 D5·F3).
#   그 밖의 모든 추적 파일 — 이 검사기 자신·scripts/·hooks/·.github/ 포함 — 은 전역
#   패턴으로 검사한다. 자기면제 없음(P13④). 제품 루트는 전역 + 제품 전용 패턴 둘 다.
set -euo pipefail

unset GIT_DIR GIT_INDEX_FILE GIT_OBJECT_DIRECTORY GIT_WORK_TREE GIT_COMMON_DIR
unset GIT_ALTERNATE_OBJECT_DIRECTORIES

REPO=$(git rev-parse --show-toplevel) || {
  echo "FAIL: repository root unavailable"
  exit 2
}
cd "$REPO"

GLOBAL_PATTERNS=contracts/portal-constants-deny-patterns.txt
PRODUCT_PATTERNS=contracts/portal-constants-deny-patterns-product.txt
# 제품 루트는 코드가 아니라 데이터다. 코드에 고정하면 새 제품 폴더가 생겼을 때 검사가
# 적용되지 않는다(codex V1 D3). 목록 밖 제품 폴더를 발견하면 통과가 아니라 exit 2 다.
PRODUCT_ROOTS_CONTRACT=contracts/portal-constants-product-roots.txt
NONOP_ADDRESSES=contracts/portal-constants-nonoperational-addresses.txt
NONOP_SUFFIXES=contracts/portal-constants-nonoperational-suffixes.txt
# 제품 코드로 볼 확장자. 루트 발견에만 쓴다(계층 배정은 경로 접두로 한다).
# 대소문자를 무시해 대조한다 — 2026-08-25 V1(codex) F3 실측: `main.PY`·`main.Js` 가
# 미등재 제품 폴더 탐지를 피해 전역 계층만 받았다.
PRODUCT_EXT_RE='\.(py|js|mjs|cjs|ts|tsx|jsx|html|css)$'
# 검사기 자신의 구역 정의 — 이 접두는 제품 루트 발견 대상이 아니다.
INFRA_PREFIX_RE='^(contracts|docs|scripts|hooks|\.github)/'
WF=.github/workflows/verify.yml
HOOK=hooks/pre-push

# 임시 작업공간 생성 실패는 위반(1)이 아니라 검사 불능(2)이다 — set -e 에 맡기면
# mktemp 의 1 이 그대로 새어 나가 규칙 위반과 환경 고장이 구분되지 않는다 (V1 결함 D4).
GCLEAN=$(mktemp) || { echo "FAIL: temp workspace unavailable"; exit 2; }
PCLEAN=$(mktemp) || { echo "FAIL: temp workspace unavailable"; exit 2; }
FILES=$(mktemp) || { echo "FAIL: temp workspace unavailable"; exit 2; }
ERRS=$(mktemp) || { echo "FAIL: temp workspace unavailable"; exit 2; }
PLIST=$(mktemp) || { echo "FAIL: temp workspace unavailable"; exit 2; }
cleanup() { rm -f -- "$GCLEAN" "$PCLEAN" "$FILES" "$ERRS" "$PLIST"; }
trap cleanup EXIT
trap 'cleanup; trap - EXIT; exit 143' TERM
trap 'cleanup; trap - EXIT; exit 130' INT
trap 'cleanup; trap - EXIT; exit 129' HUP

# 패턴 계약 검증 (G1 acceptance-hs-cleanroom.sh:14-43 방어 재사용):
# 부재/빈 파일/유효 패턴 0개/깨진 표현식/빈 문자열 매치 전부 exit 2 — "검사가 안 돌았는데
# 위반 없음"을 원리적으로 금지한다.
load_patterns() {
  local src="$1" dst="$2" rc=0
  if [ ! -f "$src" ] || [ ! -r "$src" ] || [ ! -s "$src" ]; then
    echo "FAIL: portal pattern contract missing, unreadable, or empty: $src"
    exit 2
  fi
  sed -e 's/\r$//' -e '/^[[:space:]]*#/d' -e '/^[[:space:]]*$/d' "$src" > "$dst"
  if [ ! -s "$dst" ]; then
    echo "FAIL: portal pattern contract has zero effective patterns: $src"
    exit 2
  fi
  printf '\n' | LC_ALL=C grep -aEiqf "$dst" > /dev/null 2> "$ERRS" || rc=$?
  if [ "$rc" -gt 1 ]; then
    echo "FAIL: portal pattern contract contains an invalid expression: $src"
    exit 2
  fi
  if [ "$rc" -eq 0 ]; then
    echo "FAIL: portal pattern contract contains an empty-matching expression: $src"
    exit 2
  fi
}

load_patterns "$GLOBAL_PATTERNS" "$GCLEAN"
load_patterns "$PRODUCT_PATTERNS" "$PCLEAN"

# 제품 루트 계약 적재. 부재·빈 파일·유효 항목 0개는 전부 검사 불능이다.
if [ ! -f "$PRODUCT_ROOTS_CONTRACT" ] || [ ! -r "$PRODUCT_ROOTS_CONTRACT" ] || [ ! -s "$PRODUCT_ROOTS_CONTRACT" ]; then
  echo "FAIL: product root contract missing, unreadable, or empty: $PRODUCT_ROOTS_CONTRACT"
  exit 2
fi
PRODUCT_ROOTS=$(sed -e 's/\r$//' -e '/^[[:space:]]*#/d' -e '/^[[:space:]]*$/d' "$PRODUCT_ROOTS_CONTRACT")
if [ -z "$PRODUCT_ROOTS" ]; then
  echo "FAIL: product root contract has zero effective roots: $PRODUCT_ROOTS_CONTRACT"
  exit 2
fi
for required in "$NONOP_ADDRESSES" "$NONOP_SUFFIXES"; do
  if [ ! -f "$required" ] || [ ! -r "$required" ] || [ ! -s "$required" ]; then
    echo "FAIL: portal judgment contract missing, unreadable, or empty: $required"
    exit 2
  fi
done

# 등재한 루트가 실재하지 않으면 조용한 skip 이 아니라 검사 불능이다 (사전감사 벡터 5).
# 계약이 현실과 어긋난 채로 초록이 되는 것을 금지한다 — 루트를 지웠으면 계약에서도 지워야
# 하고, 그러면 아래 미등재 발견이 그 폴더를 다시 잡는다. 어느 방향으로도 조용히 빠져나갈 수 없다.
for root in $PRODUCT_ROOTS; do
  if [ ! -d "$root" ]; then
    echo "FAIL: product root missing: $root"
    exit 2
  fi
done

if ! git ls-files -z > "$FILES"; then
  echo "FAIL: tracked-file enumeration failed"
  exit 2
fi

is_product_path() {
  local candidate="$1" root
  for root in $PRODUCT_ROOTS; do
    case "$candidate" in "$root"/*) return 0 ;; esac
  done
  return 1
}

# 제품 코드 확장자를 가진 추적 파일이 계약 밖에 있으면 검사 불능이다 (D3).
# "등재를 잊는 것"이 통과가 아니라 실패가 되게 하는 장치다.
# grep 의 "일치 없음"(1)은 정상이고 도구 오류(2 이상)는 검사 불능이다. 종료값을 참으로
# 덮어쓰면 열거 실패가 "미등재 0건"으로 둔갑한다 — 그래서 구분해서 받는다 (P13).
undeclared_rc=0
undeclared=$(git ls-files | LC_ALL=C grep -Ei "$PRODUCT_EXT_RE") || undeclared_rc=$?
if [ "$undeclared_rc" -gt 1 ]; then
  echo "FAIL: product-code enumeration failed (rc=$undeclared_rc)"
  exit 2
fi
undeclared_rc=0
undeclared=$(printf '%s\n' "$undeclared" | LC_ALL=C grep -vE "$INFRA_PREFIX_RE") || undeclared_rc=$?
if [ "$undeclared_rc" -gt 1 ]; then
  echo "FAIL: product-code enumeration failed (rc=$undeclared_rc)"
  exit 2
fi
undeclared_roots=""
while IFS= read -r candidate; do
  if [ -z "$candidate" ]; then continue; fi
  if is_product_path "$candidate"; then continue; fi
  undeclared_roots="${undeclared_roots}$(dirname "$candidate")
"
done <<UNDECLARED
$undeclared
UNDECLARED
undeclared_roots=$(printf '%s' "$undeclared_roots" | LC_ALL=C sort -u | sed '/^$/d')
if [ -n "$undeclared_roots" ]; then
  echo "FAIL: product code outside the product-root contract — 등재하지 않으면 검사가 적용되지 않는다"
  printf '  undeclared-root: %s\n' $undeclared_roots
  echo "  계약: $PRODUCT_ROOTS_CONTRACT"
  exit 2
fi

checked=0
product_files=0
contract_files=0
forbidden=0
zone_violations=0
errors=0

scan_with() {
  local path="$1" pats="$2" tier="$3" rc=0
  LC_ALL=C grep -aEiqf "$pats" -- "./$path" 2>> "$ERRS" || rc=$?
  if [ "$rc" -eq 0 ]; then
    forbidden=$((forbidden + 1))
    printf '  forbidden(%s): %q\n' "$tier" "$path"
  elif [ "$rc" -gt 1 ]; then
    errors=$((errors + 1))
    printf '  unreadable: %q\n' "$path"
  fi
}

while IFS= read -r -d '' path; do
  case "$path" in
    contracts/*)
      contract_files=$((contract_files + 1))
      mode=$(git ls-files -s -- "$path" | awk '{print $1}')
      case "$mode" in
        100644) ;;
        *)
          zone_violations=$((zone_violations + 1))
          printf '  contracts-zone: %q (mode %s — 데이터 구역엔 정규 비실행 파일만)\n' "$path" "${mode:-?}"
          ;;
      esac
      lower=$(printf '%s' "$path" | tr '[:upper:]' '[:lower:]')
      case "$lower" in
        *.txt|*.json|*.yaml|*.yml|*.md) ;;
        *)
          zone_violations=$((zone_violations + 1))
          printf '  contracts-zone: %q (허용 확장자 밖)\n' "$path"
          ;;
      esac
      continue
      ;;
    docs/*)
      # 문서 면제는 디렉터리 전체가 아니라 "문서 확장자 + 정규 비실행 파일"에만 준다.
      # 통 면제는 docs/run-portal.py 같은 실행 코드의 은닉 경로가 된다 (V1 결함 D5).
      lower=$(printf '%s' "$path" | tr '[:upper:]' '[:lower:]')
      mode=$(git ls-files -s -- "$path" | awk '{print $1}')
      case "$lower" in
        *.md|*.yaml|*.yml|*.txt|*.html)
          if [ "$mode" = "100644" ]; then continue; fi
          ;;
      esac
      # 문서 형식이 아니거나 실행 가능한 docs 파일 → 전역 검사로 계속 진행
      ;;
  esac
  checked=$((checked + 1))
  if is_product_path "$path"; then
    product_files=$((product_files + 1))
    scan_with "$path" "$GCLEAN" global
    printf '%s\n' "$path" >> "$PLIST"
  else
    scan_with "$path" "$GCLEAN" global
  fi
done < "$FILES"

# ── 제품 계층 판정 (3단) ─────────────────────────────────────────────────────
# 1단 비운영 주소 제거: RFC 2606 예약 도메인·루프백은 원리적으로 운영 주소가 될 수 없다.
#      제거 후에도 금지 패턴이 남으면 그 줄은 여전히 위반이다 — 면제가 아니라 정밀화다.
# 2단 금지 패턴: contracts/portal-constants-deny-patterns-product.txt (셀렉터·포트 등).
# 3단 점 토큰 fail-closed: 따옴표 안이 통째로 `이름.이름` 또는 `.이름` 형태인데 마지막
#      라벨이 비운영 접미사 계약에 **없으면** 거부한다. 예전 TLD 열거는 모르는 값을
#      통과시키는 방향으로 실패했다(codex V2 D4). 이 단계가 그 방향을 뒤집는다.
# 판정기는 하나다(P16) — 이 검사기 안에서만 판정하고 결과를 여기서 센다.
if [ -s "$PLIST" ]; then
  SBOX=$(mktemp -d) || { echo "FAIL: temp workspace unavailable"; exit 2; }
  # 1·3단은 Ruby 가 맡는다(비운영 주소 제거 · 점 토큰 fail-closed). 2단 금지 패턴은
  # 계약 파일의 POSIX ERE 를 그대로 해석하는 grep 에 맡긴다 — 표현식을 두 문법으로
  # 옮겨 적으면 판정이 두 벌이 되고 반드시 갈라진다(P16).
  product_rc=0
  dotted_hits=$(ruby -e '
    address_path, suffix_path, list_path, sandbox = ARGV
    rules = lambda do |path|
      File.readlines(path, chomp: true).reject { |line| line.strip.empty? || line.strip.start_with?("#") }
    end
    addresses = rules.call(address_path).map { |raw| Regexp.new(raw, Regexp::IGNORECASE) }
    suffixes = {}
    rules.call(suffix_path).each { |raw| suffixes[raw.strip] = true }
    exit 2 if addresses.empty? || suffixes.empty?

    # 2026-08-25 V1(codex) F2 반영. 소문자 ASCII 만 보던 판정을 두 방향으로 넓혔다:
    #   ① 호스트·CSS 클래스는 대문자를 쓸 수 있다("HIRE-PORTAL.ZZUNKNOWN", ".Login-Button")
    #   ② 전각 마침표(U+FF0E 등)는 IDNA 정규화에서 보통 마침표가 된다
    dotted = /(["\x27`])(\.?[A-Za-z0-9][A-Za-z0-9_-]*(?:\.[A-Za-z0-9][A-Za-z0-9_-]*)*)\1/
    ipv4 = /\A[0-9]{1,3}(?:\.[0-9]{1,3}){3}\z/
    fullwidth_dots = /[\uFF0E\u3002\uFF61\u02D9]/

    File.readlines(list_path, chomp: true).reject(&:empty?).each_with_index do |path, index|
      reason = nil
      stripped = +""
      begin
        File.foreach(path) do |line|
          clean = line.dup
          clean = clean.gsub(fullwidth_dots, ".") if clean.match?(fullwidth_dots)
          addresses.each { |rule| clean = clean.gsub(rule, "") }
          stripped << clean
          next if reason
          clean.scan(dotted) do |_quote, token|
            next unless token.include?(".")
            labels = token.split(".", -1)
            last = labels.last.to_s
            next if suffixes.key?(last.downcase)
            # 버전 문자열(1.2.3)은 주소가 아니다. 4옥텟 IPv4 만 주소로 본다.
            next if labels.all? { |label| label.match?(/\A[0-9]+\z/) } && !token.match?(ipv4)
            reason = "unknown-suffix:#{last.downcase}"
            break
          end
        end
        File.binwrite(File.join(sandbox, index.to_s), stripped)
      rescue SystemCallError, ArgumentError
        puts "#{index}\tunreadable\t#{path}"
        next
      end
      puts "#{index}\t#{reason || "-"}\t#{path}"
    end
  ' "$NONOP_ADDRESSES" "$NONOP_SUFFIXES" "$PLIST" "$SBOX" 2>> "$ERRS") || product_rc=$?
  if [ "$product_rc" -ne 0 ]; then
    rm -rf -- "$SBOX"
    echo "FAIL: product-tier evaluator unavailable (rc=$product_rc)"
    exit 2
  fi
  while IFS=$(printf '\t') read -r pidx preason ppath; do
    if [ -z "$ppath" ]; then continue; fi
    if [ "$preason" = unreadable ]; then
      errors=$((errors + 1))
      printf '  unreadable: %q\n' "$ppath"
      continue
    fi
    prc=0
    LC_ALL=C grep -aEiqf "$PCLEAN" -- "$SBOX/$pidx" 2>> "$ERRS" || prc=$?
    if [ "$prc" -eq 0 ]; then
      forbidden=$((forbidden + 1))
      printf '  forbidden(product/deny-pattern): %q\n' "$ppath"
    elif [ "$prc" -gt 1 ]; then
      errors=$((errors + 1))
      printf '  unreadable: %q\n' "$ppath"
    elif [ "$preason" != "-" ]; then
      forbidden=$((forbidden + 1))
      printf '  forbidden(product/%s): %q\n' "$preason" "$ppath"
    fi
  done <<PRODUCT_HITS
$dotted_hits
PRODUCT_HITS
  rm -rf -- "$SBOX"
fi

# ── 배선 자기 검사 (사전감사 벡터 1·2, V1 결함 D2·D3, V1 2차 결함 N2·N3) ──────
# CI 는 수동 열거(verify.yml)라 여기 등록되지 않으면 "로컬에만 있는 검사"가 되고,
# P15③ 은 그것을 없는 것으로 친다. 이 검사기 자신이 양쪽 배선을 확인한다.
wiring_fail=0
wire_bad() { wiring_fail=$((wiring_fail + 1)); printf '  wiring: %s\n' "$1"; }

# 존재하는 G3 검사 파일 전부가 각자 CI 실행 줄을 가져야 한다. 요구 목록을 파일
# 존재에서 만들므로 새 G3 검사를 추가하면 CI 줄도 자동으로 요구된다 (V1 2차 N3).
# 잔여 한계: 검사 파일 자체를 지우면 요구도 사라진다 — 그 삭제는 diff·P13 라벨·
# RED 원장 분모 감소로 드러난다 (goal 문서 한계 절).
G3_FILES=$(find . -maxdepth 2 -name 'acceptance-hs-portal-constants*.sh' \
  -not -path './worktrees/*' -not -path './.git/*' | sed 's|^\./||' | LC_ALL=C sort)
# awk -v 는 개행을 못 받으므로(BSD awk) 세미콜론으로 잇는다 — 경로에 ; 는 없다.
ALLOWED_CMDS=""
while IFS= read -r g3f; do
  if [ -z "$g3f" ]; then continue; fi
  ALLOWED_CMDS="${ALLOWED_CMDS}bash ${g3f};"
done <<G3EOF
$G3_FILES
G3EOF

# 워크플로를 YAML 구조로 읽고 jobs.*.steps[*].run 문자열만 실행 칸으로 인정한다. 파일
# 어딘가에 명령 글자가 있다는 이유만으로 통과시키면 env.NOTE 같은 실행되지 않는 값 안의
# 가짜 단계도 배선으로 오인한다(V1 3차 F1). Ruby 표준 YAML 해석기를 쓰므로 새 의존성은 없다.
#
# target 명령이 있는 run 문자열은 주석·빈 줄·현재 G3 실행 줄만 담아야 하고, 그 스텝에 if 또는
# continue-on-error 키가 있으면 인정하지 않는다. 이로써 기존 셸 감싸기·오류 무시 방어도 유지한다.
ci_line_ok() {
  local tgt="$1"
  ruby -ryaml -e '
    workflow_path, target, allowed_text = ARGV
    begin
      workflow = YAML.safe_load(
        File.read(workflow_path),
        permitted_classes: [],
        permitted_symbols: [],
        aliases: true
      )
    rescue Psych::Exception, SystemCallError
      exit 2
    end

    jobs = workflow.is_a?(Hash) ? workflow["jobs"] : nil
    exit 2 unless jobs.is_a?(Hash)
    trigger = workflow.key?("on") ? workflow["on"] : workflow[true]
    automatic_event = case trigger
                      when String
                        ["push", "pull_request"].include?(trigger)
                      when Array
                        trigger.map(&:to_s).any? { |event| ["push", "pull_request"].include?(event) }
                      when Hash
                        trigger.any? do |event, config|
                          next false unless ["push", "pull_request"].include?(event.to_s)
                          next true if config.nil? || (config.is_a?(Hash) && config.empty?)
                          next false unless config.is_a?(Hash)

                          keys = config.keys.map(&:to_s)
                          keys == ["branches"] && Array(config["branches"]).map(&:to_s) == ["**"]
                        end
                      else
                        false
                      end
    exit 1 unless automatic_event
    allowed = allowed_text.split(";").reject(&:empty?).each_with_object({}) do |command, set|
      set[command] = true
    end
    workflow_defaults = workflow["defaults"]
    workflow_run = workflow_defaults.is_a?(Hash) ? workflow_defaults["run"] : nil
    workflow_shell = workflow_run.is_a?(Hash) && workflow_run.key?("shell")
    workflow_working_directory = workflow_run.is_a?(Hash) && workflow_run.key?("working-directory")
    forbidden_env_keys = ["BASH_ENV", "ENV", "SHELLOPTS", "PATH"]
    unsafe_env = lambda do |owner|
      owner.is_a?(Hash) && owner["env"].is_a?(Hash) &&
        owner["env"].keys.map(&:to_s).any? { |key| forbidden_env_keys.include?(key) }
    end
    workflow_unsafe_env = unsafe_env.call(workflow)

    unsafe_g3_execution = false
    good = jobs.values.map do |job|
      next false unless job.is_a?(Hash) && job["steps"].is_a?(Array)
      job_defaults = job["defaults"]
      job_run = job_defaults.is_a?(Hash) ? job_defaults["run"] : nil
      job_shell = job_run.is_a?(Hash) && job_run.key?("shell")
      job_working_directory = job_run.is_a?(Hash) && job_run.key?("working-directory")
      job_unsafe_env = unsafe_env.call(job)
      runs_on = job["runs-on"]
      runs_on_valid = case runs_on
                      when String
                        !runs_on.strip.empty?
                      when Array
                        !runs_on.empty? && runs_on.all? { |label| label.is_a?(String) && !label.strip.empty? }
                      else
                        false
                      end
      strategy = job["strategy"]
      matrix_valid = if !strategy.is_a?(Hash) || !strategy.key?("matrix")
                       true
                     elsif strategy["matrix"].is_a?(Hash)
                       matrix = strategy["matrix"]
                       static_axes = matrix.reject { |axis, _| ["include", "exclude"].include?(axis.to_s) }
                       includes = matrix.key?("include") ? matrix["include"] : []
                       excludes = matrix.key?("exclude") ? matrix["exclude"] : []
                       expression = lambda do |value|
                         case value
                         when String then value.include?("${{")
                         when Array then value.any? { |item| expression.call(item) }
                         when Hash then value.any? { |key, item| expression.call(key) || expression.call(item) }
                         else false
                         end
                       end
                       controls_valid = includes.is_a?(Array) && includes.all? { |entry| entry.is_a?(Hash) } &&
                         excludes.is_a?(Array) && excludes.all? { |entry| entry.is_a?(Hash) }
                       if !controls_valid || expression.call(matrix)
                         false
                       elsif static_axes.empty?
                         matrix.keys.all? { |axis| axis.to_s == "include" } && !includes.empty?
                       elsif !static_axes.values.all? { |values| values.is_a?(Array) && !values.empty? }
                         false
                       else
                         combinations = static_axes.reduce([{}]) do |product, (axis, values)|
                           product.flat_map { |combination| values.map { |value| combination.merge(axis => value) } }
                         end
                         combinations.reject! do |combination|
                           excludes.any? do |entry|
                             entry.all? { |axis, value| combination.key?(axis) && combination[axis] == value }
                           end
                         end
                         include_additions = includes.count do |entry|
                           combinations.none? do |combination|
                             entry.all? { |axis, value| !static_axes.key?(axis) || combination[axis] == value }
                           end
                         end
                         combinations.length + include_additions >= 1
                       end
                     else
                       false
                     end
      job_disqualified = job.key?("if") || job.key?("needs") || (job.key?("continue-on-error") && job["continue-on-error"] != false)
      job["steps"].map do |step|
        next false unless step.is_a?(Hash)
        run = step["run"]
        next false unless run.is_a?(String)

        lines = run.each_line.map(&:strip).reject { |line| line.empty? || line.start_with?("#") }
        unsafe_g3_execution = true if lines.include?(target) && (
          !runs_on_valid || !matrix_valid || workflow_shell || workflow_working_directory || workflow_unsafe_env ||
          job_shell || job_working_directory || job_unsafe_env ||
          step.key?("shell") || step.key?("working-directory") || unsafe_env.call(step)
        )
        next false if job_disqualified || step.key?("if") || step.key?("continue-on-error")
        lines.include?(target) && lines.all? { |line| allowed.key?(line) }
      end.any?
    end.any?
    exit 1 if unsafe_g3_execution
    exit(good ? 0 : 1)
  ' "$WF" "$tgt" "$ALLOWED_CMDS"
}

if [ ! -f "$WF" ]; then
  wire_bad "CI 워크플로($WF) 부재 — 판정 권한이 있는 쪽이 비어 있다"
elif ! command -v ruby >/dev/null 2>&1; then
  echo "FAIL: YAML parser unavailable: ruby"
  exit 2
else
  while IFS= read -r g3f; do
    if [ -z "$g3f" ]; then continue; fi
    ci_rc=0
    ci_line_ok "bash $g3f" || ci_rc=$?
    case "$ci_rc" in
      0) ;;
      1) wire_bad "CI 실행 줄이 없거나 블록이 오염됨: bash $g3f" ;;
      *)
        errors=$((errors + 1))
        printf 'CI workflow YAML parse failed: %s\n' "$WF" >> "$ERRS"
        break
        ;;
    esac
  done <<G3EOF2
$G3_FILES
G3EOF2
fi

if [ ! -f "$HOOK" ] || [ ! -x "$HOOK" ]; then
  wire_bad "pre-push 훅 부재 또는 실행 불가 — 로컬 1차 차단이 없다"
else
  if ! grep -qF -- "-o -name 'acceptance-*.sh'" "$HOOK"; then
    wire_bad "pre-push 의 acceptance 글로브 수집식이 사라졌다"
  fi
  # 훅 상단의 무조건 exit 0 은 수집 이전에 훅 전체를 무력화한다 (V1 2차 N3 절반).
  # 순정 pre-push 에는 순수 `exit 0` 줄이 없다(실측: exit 1 두 곳과 exit "$fail" 뿐).
  if sed -e 's/[[:space:]]*#.*//' "$HOOK" | grep -qE '^[[:space:]]*exit[[:space:]]+0[[:space:]]*$'; then
    wire_bad "pre-push 에 무조건 exit 0 줄이 있다 — 훅이 검사 전에 통과한다"
  fi
  found_self=$(printf '%s\n' "$G3_FILES" | grep -cF 'acceptance-hs-portal-constants')
  if [ "$found_self" -lt 2 ]; then
    wire_bad "글로브 수집 재현에서 검사기·mutation 이 다 잡히지 않는다 (found=$found_self)"
  fi
  # pre-push 는 파일 첫 20줄의 건너뛰기 표식을 보고 검사를 CI 로 넘긴다. G3 파일에 그
  # 표식이 붙으면 로컬 절반이 조용히 사라지므로 여기서 차단한다 (V1 결함 D3).
  G3_MARK=$(printf '# PUSH-%s' 'PERFORMING')
  while IFS= read -r g3f; do
    if [ -z "$g3f" ]; then continue; fi
    if head -20 "$g3f" | grep -qF "$G3_MARK"; then
      wire_bad "G3 검사 파일이 pre-push 건너뛰기 표식을 달고 있다: $g3f"
    fi
  done <<G3EOF3
$G3_FILES
G3EOF3
fi

# ── 판정 ─────────────────────────────────────────────────────────────────────
if [ "$forbidden" -eq 0 ]; then
  echo "PASS: portal constants outside contracts 0"
else
  echo "FAIL: portal constants outside contracts $forbidden"
fi
if [ "$zone_violations" -eq 0 ]; then
  echo "PASS: contracts zone violations 0"
else
  echo "FAIL: contracts zone violations $zone_violations"
fi
if [ "$wiring_fail" -eq 0 ]; then
  echo "PASS: ci/pre-push wiring intact"
else
  echo "FAIL: ci/pre-push wiring broken $wiring_fail"
fi
echo "PRODUCT_FILES: $product_files"
echo "CHECKED: $checked"
echo "CONTRACT_FILES: $contract_files"

# 검사 불능(2)이 위반(1)보다 우선한다 — 일부만 읽은 스캔의 "위반 n건"은 믿을 수 없다.
if [ "$errors" -ne 0 ] || [ -s "$ERRS" ]; then
  echo "FAIL: scanner errors $errors"
  exit 2
fi
if [ "$product_files" -lt 2 ]; then
  echo "FAIL: product files $product_files (<2) — 검사 대상이 없어서 통과는 금지 (P20)"
  exit 2
fi
if [ "$checked" -lt 10 ]; then
  echo "FAIL: checked files $checked (<10)"
  exit 2
fi
if [ "$contract_files" -lt 2 ]; then
  echo "FAIL: contract files $contract_files (<2) — 패턴 계약 2벌이 추적되고 있지 않다"
  exit 2
fi
if [ "$forbidden" -ne 0 ] || [ "$zone_violations" -ne 0 ] || [ "$wiring_fail" -ne 0 ]; then
  exit 1
fi
