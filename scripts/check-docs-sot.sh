#!/usr/bin/env bash
# check-docs-sot.sh — docs/sot/ 재구성 인수 기준(AC) 검사.
#
# 계약:
#   - docs/engineering/docs-sot-restructure-goal-2026-08-08.md
#   - docs/engineering/feature-sot-catalog-goal-2026-08-21.md
#   출력  : exit 0 (AC 전부 충족) | exit 1 (하나라도 위반, 위반 내용을 stderr에 출력)
#   불변식: 조용한 통과 금지 — 각 검사 항목의 PASS/FAIL을 전부 stdout에 출력한다.
#
# 비범위: CI(verify.yml) 상시 연결은 이번 작업 범위 밖이다(문서 재구성이지 신규
# 상시 게이트 신설이 아님). 필요해지면 별도 이슈로 연결한다.
set -uo pipefail

fail=0
pass() { printf 'PASS: %s\n' "$1"; }
bad()  { printf 'FAIL: %s\n' "$1" >&2; fail=1; }

# AC-1: 기존 docs/sot/ 필수 파일 5개와 기능 진입점 2개가 존재하고 각각
#       20,000바이트를 넘지 않는다.
#   (수정 이력: 최초 구현은 wc -l<=300 로 쟀으나, coding-principles.md 처럼 원칙
#    표의 각 행이 개행 없이 한 줄에 긴 문장을 담는 경우 줄 수가 실제 분량을
#    반영하지 못함을 실행 중 발견(70줄인데 15,424바이트). 바이트 크기로 교정.)
REQUIRED_FILES=(
  "docs/sot/INDEX.md"
  "docs/sot/coding-principles.md"
  "docs/sot/hook-contracts.md"
  "docs/sot/git-workflow.md"
  "docs/sot/verification-commands.md"
  "docs/sot/features/INDEX.md"
  "docs/sot/features/catalog.yaml"
)
MAX_BYTES=20000
for f in "${REQUIRED_FILES[@]}"; do
  if [ ! -f "$f" ]; then
    bad "필수 SOT 파일 없음: $f"
    continue
  fi
  bytes=$(wc -c < "$f" | tr -d ' ')
  if [ "$bytes" -gt "$MAX_BYTES" ]; then
    bad "$f 가 ${MAX_BYTES}바이트 초과 (${bytes}바이트) — 계약과 서술이 다시 섞였을 가능성"
  else
    pass "$f 존재, ${bytes}바이트 (<=${MAX_BYTES})"
  fi
done

# AC-2: 주요 기능 정본은 YAML 1.2와 JSON 양쪽에서 읽히는 제한 형식이며, 카탈로그와
#       기능 문서가 1:1로 대응하고 모든 근거 경로가 현재 저장소에 존재한다.
#       JSON 호환 부분집합을 쓰므로 외부 YAML 패키지 없이 Python 표준 라이브러리로 검사한다.
if python3 - <<'PY'
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path.cwd()
FEATURE_ROOT = ROOT / "docs/sot/features"
CATALOG_PATH = FEATURE_ROOT / "catalog.yaml"
REQUIRED_FEATURE_KEYS = {
    "id",
    "name",
    "category",
    "maturity",
    "availability",
    "purpose",
    "authority",
    "surface_coverage",
    "entrypoints",
    "inputs",
    "outputs",
    "errors",
    "invariants",
    "boundaries",
    "non_goals",
    "verification",
    "evidence",
    "change_protocol",
}
ID_PATTERN = re.compile(r"^[a-z][a-z0-9-]*$")
SURFACE_KEYS = {
    "tracked_product_files",
    "ci_steps",
    "ci_command_paths",
    "hooks",
    "contract_surfaces",
}


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate key: {key}")
        result[key] = value
    return result


def load_document(path: Path) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicate_keys)
    if not isinstance(raw, dict):
        raise ValueError(f"document root must be an object: {path.relative_to(ROOT)}")
    return raw


def repo_path(value: str) -> Path:
    if value.startswith(("http://", "https://")):
        raise ValueError(f"external URL is not permitted as repository evidence: {value}")
    clean = value.split("#", 1)[0]
    path = Path(clean)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"path must be repository-relative: {value}")
    return ROOT / path


def markdown_anchors(path: Path) -> set[str]:
    anchors: set[str] = set()
    counts: dict[str, int] = {}
    fence_char = ""
    fence_length = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        fence = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line)
        if not fence_char and fence is not None:
            marker = fence.group(1)
            if marker[0] != "`" or "`" not in fence.group(2):
                fence_char = marker[0]
                fence_length = len(marker)
                continue
        if fence_char:
            closing = re.match(
                rf"^ {{0,3}}{re.escape(fence_char)}{{{fence_length},}}\s*$",
                line,
            )
            if closing is not None:
                fence_char = ""
                fence_length = 0
            continue
        match = re.match(r"^#{1,6}\s+(.+?)\s*#*\s*$", line)
        if match is None:
            continue
        heading = re.sub(r"[`*~]", "", match.group(1)).lower().strip()
        spaced = re.sub(r"\s", "-", heading)
        base = re.sub(r"[^\w\-]", "", spaced, flags=re.UNICODE)
        if not base:
            continue
        count = counts.get(base, 0)
        counts[base] = count + 1
        anchors.add(base if count == 0 else f"{base}-{count}")
    return anchors


def require_existing(value: object, context: str) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{context} must be a non-empty string")
    path = repo_path(value)
    if not path.exists():
        raise ValueError(f"{context} does not exist: {value}")
    if "#" in value:
        _, fragment = value.split("#", 1)
        if not fragment:
            raise ValueError(f"{context} has an empty fragment: {value}")
        if path.suffix.lower() != ".md":
            raise ValueError(f"{context} fragment requires a Markdown document: {value}")
        if fragment not in markdown_anchors(path):
            raise ValueError(f"{context} Markdown anchor does not exist: {value}")


def parse_ci_step_names(workflow_path: Path) -> list[str]:
    ruby_program = r'''
require "psych"
require "json"
require "date"

begin
  doc = Psych.safe_load(File.read(ARGV[0]), aliases: true, permitted_classes: [Date, Time])
  jobs = doc.is_a?(Hash) ? doc["jobs"] : nil
  raise "jobs must be a non-empty mapping" unless jobs.is_a?(Hash) && !jobs.empty?
  names = []
  jobs.each_value do |job|
    next unless job.is_a?(Hash)
    steps = job["steps"]
    raise "job steps must be a non-empty array" unless steps.is_a?(Array) && !steps.empty?
    steps.each do |step|
      next unless step.is_a?(Hash) && step.key?("name")
      name = step["name"]
      raise "CI step name must be a non-empty string" unless name.is_a?(String) && !name.empty?
      names << name
    end
  end
  puts JSON.generate(names)
rescue StandardError, Psych::Exception => error
  warn error.message
  exit 2
end
'''
    parsed = subprocess.run(
        ["ruby", "-e", ruby_program, str(workflow_path)],
        cwd=ROOT,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if parsed.returncode != 0:
        raise ValueError(f"CI workflow parse failed: {parsed.stderr.decode(errors='replace').strip()}")
    names = json.loads(parsed.stdout.decode("utf-8"))
    if not isinstance(names, list) or not all(isinstance(name, str) for name in names):
        raise ValueError("CI workflow parser returned an invalid step-name list")
    return names


try:
    if not CATALOG_PATH.is_file() or not CATALOG_PATH.stat().st_size:
        raise ValueError("feature catalog missing or empty")
    catalog = load_document(CATALOG_PATH)
    if catalog.get("schema_version") != "valuehire.feature-catalog/v1":
        raise ValueError("unsupported catalog schema_version")

    categories = catalog.get("categories")
    features = catalog.get("features")
    vocabulary = catalog.get("status_vocabulary")
    if not isinstance(categories, list) or not categories:
        raise ValueError("catalog categories must be non-empty")
    if not isinstance(features, list) or not features:
        raise ValueError("catalog features must be non-empty")
    if not isinstance(vocabulary, dict):
        raise ValueError("catalog status_vocabulary must be an object")

    category_ids = [item.get("id") for item in categories if isinstance(item, dict)]
    if len(category_ids) != len(categories) or len(category_ids) != len(set(category_ids)):
        raise ValueError("catalog category ids must be present and unique")
    for category in categories:
        if not category.get("label") or not category.get("definition"):
            raise ValueError(f"category label or definition missing: {category.get('id')}")
    maturity_values = set(vocabulary.get("maturity", {}))
    availability_values = set(vocabulary.get("availability", {}))

    catalog_by_id: dict[str, dict[str, Any]] = {}
    catalog_documents: set[str] = set()
    for item in features:
        if not isinstance(item, dict):
            raise ValueError("each catalog feature must be an object")
        feature_id = item.get("id")
        document = item.get("document")
        if not isinstance(feature_id, str) or ID_PATTERN.fullmatch(feature_id) is None:
            raise ValueError(f"invalid feature id: {feature_id!r}")
        if feature_id in catalog_by_id:
            raise ValueError(f"duplicate feature id: {feature_id}")
        if item.get("category") not in category_ids:
            raise ValueError(f"unknown category for {feature_id}")
        if item.get("maturity") not in maturity_values:
            raise ValueError(f"unknown maturity for {feature_id}")
        if item.get("availability") not in availability_values:
            raise ValueError(f"unknown availability for {feature_id}")
        require_existing(document, f"catalog document for {feature_id}")
        if not isinstance(document, str) or document in catalog_documents:
            raise ValueError(f"duplicate or invalid feature document: {document!r}")
        catalog_documents.add(document)
        catalog_by_id[feature_id] = item

    coverage = catalog.get("coverage")
    if not isinstance(coverage, dict):
        raise ValueError("catalog coverage must be an object")
    for key in ("product_roots", "control_roots"):
        paths = coverage.get(key)
        if not isinstance(paths, list) or not paths:
            raise ValueError(f"catalog coverage.{key} must be non-empty")
        for path in paths:
            require_existing(path, f"catalog coverage.{key}")

    actual_documents = {
        str(path.relative_to(ROOT))
        for path in FEATURE_ROOT.rglob("*.yaml")
        if path != CATALOG_PATH
    }
    if actual_documents != catalog_documents:
        missing = sorted(catalog_documents - actual_documents)
        extra = sorted(actual_documents - catalog_documents)
        raise ValueError(f"catalog/document mismatch missing={missing} extra={extra}")

    invariant_ids: set[str] = set()
    surface_owners: dict[str, dict[str, str]] = {key: {} for key in SURFACE_KEYS}

    def claim_surface(kind: str, value: object, feature_id: str, category: str) -> None:
        if not isinstance(value, str) or not value:
            raise ValueError(f"{feature_id}.surface_coverage.{kind} contains an invalid value")
        if kind in {"tracked_product_files", "ci_command_paths", "contract_surfaces"}:
            require_existing(value, f"{kind} surface for {feature_id}")
        if kind == "hooks":
            require_existing(value, f"hook surface for {feature_id}")
        if kind in {"ci_steps", "ci_command_paths", "hooks"} and category != "engineering_assurance":
            raise ValueError(f"repository control surface assigned outside engineering_assurance: {feature_id}")
        if kind == "tracked_product_files" and category == "engineering_assurance":
            raise ValueError(f"product file assigned to engineering_assurance: {feature_id}")
        owner = surface_owners[kind].get(value)
        if owner is not None:
            raise ValueError(f"duplicate {kind} surface: {value} ({owner}, {feature_id})")
        surface_owners[kind][value] = feature_id

    for document in sorted(catalog_documents):
        data = load_document(ROOT / document)
        if data.get("schema_version") != "valuehire.feature-sot/v1":
            raise ValueError(f"unsupported feature schema_version: {document}")
        feature = data.get("feature")
        if not isinstance(feature, dict):
            raise ValueError(f"feature object missing: {document}")
        missing_keys = sorted(REQUIRED_FEATURE_KEYS - set(feature))
        if missing_keys:
            raise ValueError(f"required keys missing in {document}: {missing_keys}")
        feature_id = feature["id"]
        catalog_item = catalog_by_id.get(feature_id)
        if catalog_item is None:
            raise ValueError(f"feature id absent from catalog: {feature_id}")
        if not isinstance(feature.get("purpose"), str) or not feature["purpose"]:
            raise ValueError(f"feature purpose missing: {feature_id}")
        for key in ("name", "category", "maturity", "availability"):
            if feature.get(key) != catalog_item.get(key):
                raise ValueError(f"catalog mismatch for {feature_id}.{key}")
        if not isinstance(feature["entrypoints"], list):
            raise ValueError(f"{feature_id}.entrypoints must be an array")
        for key in ("inputs", "outputs", "errors", "invariants", "boundaries", "non_goals", "verification", "evidence"):
            value = feature.get(key)
            if not isinstance(value, list) or not value:
                raise ValueError(f"{feature_id}.{key} must be a non-empty array")
        if feature["maturity"] == "implemented" and not feature["entrypoints"]:
            raise ValueError(f"implemented feature has no entrypoints: {feature_id}")

        surfaces = feature["surface_coverage"]
        if not isinstance(surfaces, dict) or set(surfaces) != SURFACE_KEYS:
            raise ValueError(f"surface_coverage must contain exactly {sorted(SURFACE_KEYS)}: {feature_id}")
        surface_count = 0
        for kind in sorted(SURFACE_KEYS):
            values = surfaces[kind]
            if not isinstance(values, list):
                raise ValueError(f"{feature_id}.surface_coverage.{kind} must be an array")
            for value in values:
                claim_surface(kind, value, feature_id, feature["category"])
                surface_count += 1
        if surface_count == 0:
            raise ValueError(f"feature owns no derived repository surface: {feature_id}")

        authority = feature["authority"]
        if not isinstance(authority, dict) or not authority.get("owns"):
            raise ValueError(f"authority.owns missing: {feature_id}")
        for delegated in authority.get("delegates", []):
            if not isinstance(delegated, dict):
                raise ValueError(f"invalid authority delegate: {feature_id}")
            require_existing(delegated.get("document"), f"delegate for {feature_id}")
        for path in authority.get("historical_context_only", []):
            require_existing(path, f"historical context for {feature_id}")
        for entrypoint in feature["entrypoints"]:
            if not isinstance(entrypoint, dict):
                raise ValueError(f"invalid entrypoint: {feature_id}")
            require_existing(entrypoint.get("path"), f"entrypoint for {feature_id}")
        for evidence in feature["evidence"]:
            require_existing(evidence, f"evidence for {feature_id}")
        for invariant in feature["invariants"]:
            if not isinstance(invariant, dict) or not invariant.get("id") or not invariant.get("rule"):
                raise ValueError(f"invalid invariant: {feature_id}")
            invariant_id = invariant["id"]
            if invariant_id in invariant_ids:
                raise ValueError(f"duplicate invariant id: {invariant_id}")
            invariant_ids.add(invariant_id)
            require_existing(invariant.get("evidence"), f"invariant evidence for {invariant_id}")
        for verification in feature["verification"]:
            if not isinstance(verification, dict) or not verification.get("id") or not verification.get("command") or not verification.get("expected"):
                raise ValueError(f"invalid verification contract: {feature_id}")
        protocol = feature["change_protocol"]
        if not isinstance(protocol, dict) or not protocol.get("required_updates") or not protocol.get("rollback"):
            raise ValueError(f"invalid change protocol: {feature_id}")

    product_roots = coverage["product_roots"]
    tracked = subprocess.run(
        ["git", "ls-files", "-z", "--", *product_roots],
        cwd=ROOT,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if tracked.returncode != 0:
        raise ValueError(f"git ls-files failed for product roots: {tracked.stderr.decode(errors='replace')}")
    actual_product_files = {
        value for value in tracked.stdout.decode("utf-8").split("\0") if value
    }

    workflow_path = ROOT / ".github/workflows/verify.yml"
    actual_workflow_files = {
        path for pattern in ("*.yml", "*.yaml") for path in (ROOT / ".github/workflows").glob(pattern)
    }
    if actual_workflow_files != {workflow_path}:
        relative = sorted(str(path.relative_to(ROOT)) for path in actual_workflow_files)
        raise ValueError(f"CI workflow coverage changed; explicitly classify workflow files: {relative}")
    workflow_text = workflow_path.read_text(encoding="utf-8")
    ci_step_list = parse_ci_step_names(workflow_path)
    if len(ci_step_list) != len(set(ci_step_list)):
        raise ValueError("CI named steps must be unique for feature ownership")
    actual_ci_steps = set(ci_step_list)
    actual_ci_command_paths = set(
        re.findall(
            r"(?<![A-Za-z0-9_.-])(verify\.sh|scripts/[A-Za-z0-9_./-]+\.sh)",
            workflow_text,
        )
    )

    hook_root = ROOT / "hooks"
    actual_hooks = {
        str(path.relative_to(ROOT)) for path in hook_root.iterdir() if path.is_file()
    }
    actual_contract_surfaces = {
        str(path.relative_to(ROOT)) for path in (ROOT / "docs/sot").glob("humansearch-*-contract.md")
    }
    actual_surfaces = {
        "tracked_product_files": actual_product_files,
        "ci_steps": actual_ci_steps,
        "ci_command_paths": actual_ci_command_paths,
        "hooks": actual_hooks,
        "contract_surfaces": actual_contract_surfaces,
    }
    for kind, actual in actual_surfaces.items():
        assigned = set(surface_owners[kind])
        if assigned != actual:
            missing = sorted(actual - assigned)
            extra = sorted(assigned - actual)
            raise ValueError(f"{kind} ownership mismatch missing={missing} extra={extra}")

    print(
        "PASS: feature SOT structure "
        f"catalog=1 features={len(catalog_by_id)} categories={len(category_ids)} "
        f"invariants={len(invariant_ids)} product_files={len(actual_product_files)} "
        f"ci_steps={len(actual_ci_steps)} ci_commands={len(actual_ci_command_paths)} "
        f"hooks={len(actual_hooks)} "
        f"contract_surfaces={len(actual_contract_surfaces)} paths=validated"
    )
except (OSError, UnicodeError, json.JSONDecodeError, TypeError, ValueError) as error:
    print(f"FAIL: feature SOT structure — {error}", file=sys.stderr)
    raise SystemExit(1)
PY
then
  pass "주요 기능 카탈로그·기능 문서 구조와 근거 경로 일치"
else
  bad "주요 기능 카탈로그·기능 문서 구조 또는 근거 경로 불일치"
fi

# AC-3: 훅 강제 장치를 참조하는 5개 실행 파일이 전부 새 SOT 경로(docs/sot/hook-contracts.md)를
#       계약으로 가리킨다 — 옛 goal 문서 경로가 더 이상 "계약"으로 남아있으면 안 된다.
CONTRACT_CONSUMERS=(
  "hooks/pre-commit"
  "hooks/pre-push"
  "scripts/install-hooks.sh"
  "scripts/session-status.sh"
  "scripts/acceptance-0-7.sh"
)
for f in "${CONTRACT_CONSUMERS[@]}"; do
  if [ ! -f "$f" ]; then
    bad "계약 참조 대상 파일 없음: $f"
    continue
  fi
  if grep -q '계약: docs/sot/hook-contracts\.md' "$f"; then
    pass "$f 가 docs/sot/hook-contracts.md 를 계약으로 참조"
  else
    bad "$f 가 여전히 옛 경로(goal 문서)를 계약으로 참조하거나 참조가 없음"
  fi
  if grep -q '계약: docs/engineering/hook-enforcement-goal-2026-08-07\.md' "$f"; then
    bad "$f 에 옛 계약 경로가 남아있음(제거되어야 함)"
  fi
done

if [ "$fail" -eq 0 ]; then
  echo "OK: docs/sot 재구성 AC 전부 충족"
  exit 0
else
  echo "NOT_RUN이 아니라 FAIL — 위 FAIL 라인을 고친다"
  exit 1
fi
