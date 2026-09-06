"""Fail closed when Weekly Ops SOT and its execution surfaces drift."""
from __future__ import annotations
import hashlib, json
import re, sys, unicodedata
from pathlib import Path
from typing import Any, Mapping
REQUIRED_PATHS = {
    "sot": "docs/sot/weekly-ops-contract.md",
    "index": "docs/sot/INDEX.md",
    "skill": ".agents/skills/weekly-ops/SKILL.md",
    "prompt_contract": ".agents/skills/weekly-ops/references/prompt-contract.md",
    "briefing_style": ".agents/skills/weekly-ops/references/briefing-style.md",
    "data_contract": ".agents/skills/weekly-ops/references/data-contract.md", "adversarial_review": ".agents/skills/weekly-ops/references/adversarial-review.md", "brief_renderer": ".agents/skills/weekly-ops/scripts/brief_renderer.py",
    "golden_reference": ".agents/skills/weekly-ops/references/notion-golden-sample.md",
    "verification": "docs/sot/verification-commands.md",
    "mechanism_registry": "docs/sot/mechanism-registry.yaml",
    "ci_workflow": ".github/workflows/verify.yml",
    "runtime_contract": "contracts/weekly-ops/runtime-contract-v1.json",
    "legacy_contract": "contracts/weekly-ops/notion-golden-sample-v1.json",
    "db_contract": "contracts/weekly-ops/db-contract-v1.sql",
}
REPOSITORY_REQUIREMENTS = {
    "sot": ("## DB와 source snapshot", "immutable run identity/window, legal status transition, source snapshot"),
    "mechanism_registry": ("weekly-ops-sot-ci", "acceptance-weekly-ops-skill.sh --full"), "ci_workflow": ("run: bash scripts/verify/run-acceptance.sh scripts/acceptance-weekly-ops-skill.sh --full",),
    "skill": ("emit exactly one diagnostic for each fixed channel on every run", "A caller assertion or unverified alternate path never satisfies the Golden v2 gate."), "prompt_contract": ("Candidate display names may be resolved only at write time", "six exact tracked v2 paths", "A caller assertion or alternate path"), "golden_reference": ("Do not write from this legacy block.", "v1 performs no write or readback.", "A caller assertion never satisfies that gate."),
}
REQUIRED_HEADINGS = (
    "## 권한과 정본 우선순위",
    "## 현재 구현 상태",
    "## 보고 주차와 4주 데이터",
    "## 실제 고객 포지션과 Scraped 경계",
    "## Task identity와 중복 제거",
    "## Pipeline 정의",
    "## 후보자 소싱",
    "## LinkedIn 시장 접근성",
    "## 소싱 커버리지 위험지수",
    "## Notion Golden Sample 형식",
    "## 외부 발행과 개인정보",
    "## 검증과 완료 조건",
    "## 롤백과 영향 반경",
)
REQUIRED_TOKENS = (
    "valuehire-report-calendar-v1",
    "SCRAPED_STAGING",
    "CLIENT_REQUESTED",
    "CLIENT_SHARED",
    "(candidate_key_hmac, position_id, hiring_cycle_id)",
    "`run_id`가 있는 증거 행은 같은 run의 source snapshot만 참조한다.",
    "위 네 terminal stage 어디에서든 active stage로 돌아가는 event type은 `REACTIVATED`만 허용한다.",
    "Saramin",
    "JobKorea",
    "LinkedIn Recruiter",
    "0/20",
    "HARD 0",
    "UNRANKED",
    "A=70..100 B=40..69 C=0..39",
    "P0/P1",
    "즉시 실행",
    "해야 한다",
    "MODE_FORBIDS_PUBLICATION",
    "CONTRACT_ONLY_NOT_EXECUTABLE", "두 section의 row 수를 합산하지 않는다.", "`YELLOW_ELIGIBLE`", "어느 쪽도 우선하지 않고 영향 셀은", "tuple의 lexicographic maximum", "`post_cutoff_alerts`", "`market-accessibility-v2`", "`sourcing-coverage-risk-v1`", "`market_formula_version`", "`coverage_risk_formula_version`", "다섯 source 모두 talent pool/general opening을 active requisition에서 제외한다.", "값 충돌은 machine contract의 우선권이", "넓히거나 배제를 줄이거나", "`REQUESTED→CLIENT_REQUESTED`", "`REFERENCE_ONLY|NONE`도 origin을 승격하지 않는다.", "metric_window_end_exclusive", "새 current-run source snapshot을 먼저 캡처한다.",
)
IDENTITY = ("candidate_key_hmac", "position_id", "hiring_cycle_id")
ACTIVE_STAGES = (
    "RECOMMENDATION_PENDING", "CLIENT_REVIEW", "ASSIGNMENT", "INTERVIEW_1",
    "INTERVIEW_2", "FINAL_INTERVIEW", "OFFER", "FINAL_ACCEPTED",
)
INTERVIEW_STAGES = (
    "ASSIGNMENT", "INTERVIEW_1", "INTERVIEW_2", "FINAL_INTERVIEW", "OFFER", "FINAL_ACCEPTED",
)
PRE_INTERVIEW_STAGES = ("RECOMMENDATION_PENDING", "CLIENT_REVIEW")
CLOSED_STAGES = ("JOINED", "REJECTED", "WITHDRAWN", "CLOSED")
PIPELINE_STAGES = ACTIVE_STAGES + CLOSED_STAGES
MARKET_FORMULA = "market_accessibility = (pool_points * precision_points * 100) // 2500"
POOL_POINTS = ((0, 0), (9, 10), (24, 20), (49, 30), (99, 40), (None, 50))
PRECISION_POINTS = ((0.2, 0), (0.4, 15), (0.6, 30), (0.8, 40), (None, 50))
MARKET_SAMPLE_SCHEMA = {
    "exact_fields": ["candidate_key_hmac", "rank", "predicate_results"],
    "candidate_key_hmac_min_length": 32,
    "rank_sequence": [1, 20],
    "predicate_keys_equal_must_have_predicates": True,
    "predicate_values": ["TRUE", "FALSE", "UNKNOWN"],
    "qualified_count_recomputed_from_predicates": True,
}
GOLDEN_SECTIONS = (
    "four_week_kpis", "recent_client_positions", "market_accessibility", "position_changes",
    "candidate_sourcing", "new_tasks", "reactivated_tasks", "pipeline_movements",
    "active_pipeline", "pre_interview_pipeline", "data_coverage",
)
GOLDEN_TITLES = (
    "4주 KPI", "최근 인입 포지션", "시장 접근성 / 소싱 커버리지 위험지수", "포지션 변동 사항",
    "후보자 소싱", "지난주 신규 Task", "지난주 재활성 Task", "지난주 이동 후보자",
    "활성 Pipeline", "면접 직전 Pipeline", "데이터 커버리지",
)
GOLDEN_COLLAPSED = GOLDEN_SECTIONS[5:]
REQUIRED_METRICS = (
    "live_client_position_count", "new_task_count", "reactivated_task_count",
    "active_pipeline_count", "interview_pipeline_count", "pre_interview_pipeline_count",
    "channel_outreach",
)
EXPECTED_HOOKS = (
    "preflight_sources", "freeze_four_week_cutoffs", "capture_source_snapshots",
    "normalize_positions_and_tasks", "dedupe_candidate_position_records", "compute_weekly_metrics",
    "compute_market_accessibility", "compute_sourcing_coverage_risk", "render_golden_sample",
    "record_write_ahead_intent", "publish_private_notion", "readback_verify",
)
LEGACY_TOP_LEVEL = {
    "contract_version", "runtime_status", "template", "authority", "four_week_series", "metrics",
    "recent_client_positions", "market_accessibility", "sourcing_coverage_risk",
    "pipeline", "privacy", "hooks", "fail_closed", "section_schemas",
}
LEGACY_NESTED_KEYS = {
    "runtime_status": "state publication_allowed replacement_required",
    "template": "title_pattern view section_order detail_sections_collapsed",
    "authority": "recent_client_positions_order managerial_directives_forbidden llm_may_not_choose_work risk_name risk_is_formula_output_not_management_decision legacy_priority_score_fields_forbidden",
    "four_week_series": "length contiguous_iso_weeks timezone missing_value missing_display missing_is_never_zero trend_requires_verified_points",
    "metrics": " ".join(REQUIRED_METRICS),
    "metrics.live_client_position_count": "kind unit allowed_origins allowed_lifecycles excluded_origins excluded_statuses headcount_is_separate",
    "metrics.new_task_count": "kind unit dedupe_key external_task_id_is_lineage_not_identity reactivation_is_separate_metric",
    "metrics.reactivated_task_count": "kind unit dedupe_key requires_prior_closed_same_cycle new_task_is_false",
    "metrics.active_pipeline_count": "kind unit latest_state_only stages",
    "metrics.interview_pipeline_count": "kind unit latest_state_only stages",
    "metrics.pre_interview_pipeline_count": "kind unit latest_state_only stages",
    "metrics.channel_outreach": "kind channels unit dedupe_key status_fields unsupported_status_value",
    "recent_client_positions": "window allowed_origins excluded_origins required_fields no_priority_or_action_language",
    "market_accessibility": "source source_system filter_dimensions_require_nonempty_string_arrays ordered_result_snapshot_hash_equals_source_raw_hash formula_version required_fields evaluated_sample_size sample_selection underfilled_unique_sample sample_evaluation_schema pool_points precision_points pool_points_input result_count_source precision_rate_formula precision_points_input score_formula zero_qualified_override score_bounds bands missing_or_partial_result",
    "sourcing_coverage_risk": "formula_version position_age_source active_candidate_source inputs_recomputed_by_db eligible_lifecycles ineligible_lifecycle_result recency_points pipeline_gap_points scarcity_points score_formula bands explain_components unverified_market_result",
    "pipeline": "dedupe_key latest_event_at_cutoff_wins closed_stages movement_count_is_distinct_transition",
    "privacy": "canonical_snapshot_uses_candidate_key_hmac candidate_display_name_allowed_only_in_user_authorized_private_notion resolve_display_name_at_write_time forbidden_targets_for_candidate_display_name private_page_access_readback_required",
    "fail_closed": "unknown_is_not_zero missing_linkedin_search_is_unranked missing_four_week_history_is_visible duplicate_or_ambiguous_identity_blocks_affected_count publication_without_readback_is_partial",
}
EXPECTED_URLS = {
    "jobkorea_operator_url": "https://www.jobkorea.co.kr/corp/person/position",
    "saramin_operator_url": "https://billing.saramin.co.kr/manage/7791926?svcAypdTgtNos=31463970",
    "clickup_list_url": "https://app.clickup.com/9018789656/v/li/901814621569",
    "notion_parent_url": "https://app.notion.com/p/valueconnect/1975f52f80964fb1996eed3b0226e633?v=c5aa2180f3b24feda8408f20547aed54",
}
STABLE_VERIFICATION = "단위 테스트 0건 거부·mutation 생존 0건·CHECKED 양수"
LEGACY_CANONICAL_SHA256 = "43ff362c6c2f2fead5fd6d1b1c6090d17870a366d0bcb5d9d05c8cf8cf78b009"
SOT_CONTRACT_SHA256 = "5e64be67a5a1a26633ebdf45d59033d95268b16b3211c6dee32c72113c4e7054"; DB_CONTRACT_SHA256 = "f461ae60fd4e3a8c995bb8710508d075340b35566e515dd38c87a931c0252b6a"; SKILL_SHA256 = "7b1dcfd1958663d19575d301cb8db21be1cad7394fe33702a92000d52a09ec7e"; DATA_CONTRACT_SHA256 = "c432a1975374f8b8d419d717c6a91a8d9e494e462767c8225232ff3302d8f8e1"; ADVERSARIAL_REVIEW_SHA256 = "81a889a6518f2165198dece20a0799a4f4cd6310e59c142adffa123ace6257b7"; RUNTIME_CONTRACT_SHA256 = "2f407e749f0464773b08b0af9f98abf394d02259015064d2cd3d831a6e198cc5"
GOLDEN_REFERENCE_SHA256 = "0380e58e91a85ef02602712ce42c3f7d222325f155c3b6a76db5e4592cf636a2"; PROMPT_CONTRACT_SHA256 = "67bb96486ec102c364bcef88dfc70165e901b38d653c96490beead8d5612c7d9"; BRIEFING_STYLE_SHA256 = "1cfb7d761c1aa5c6406b82e90ed313f58ec9c474c15278dbd30f36803b20633b"; BRIEF_RENDERER_SHA256 = "e3ab9aa1c3f38b842edeb57b828cd0d74d427b3f2a8464df30003d86136c53bc"
def _normal(text: str) -> str:
    return " ".join(text.split())
def _visible_markdown(text: str) -> str:
    return "".join(character for character in unicodedata.normalize("NFKC", re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)) if unicodedata.category(character) != "Cf")
def _section(text: str, heading: str) -> str:
    match = re.search(rf"^{re.escape(heading)}\s*$", text, re.MULTILINE)
    if not match:
        return ""
    tail = text[match.end():]
    end = re.search(r"^## ", tail, re.MULTILINE)
    return tail[:end.start()] if end else tail
def _bullet_values(section: str, label: str) -> tuple[str, ...]:
    matches = re.findall(
        rf"^{re.escape(label)}\s*\n\s*\n((?:- `[^`]+`\s*\n?)+)",
        section,
        re.MULTILINE,
    )
    return tuple(re.findall(r"^- `([^`]+)`", matches[0], re.MULTILINE)) if len(matches) == 1 else ()
def _json_object(raw: str, error: str) -> tuple[dict[str, Any] | None, list[str]]:
    try:
        value = json.loads(raw)
    except (json.JSONDecodeError, TypeError, ValueError, RecursionError):
        return None, [error]
    return (value, []) if isinstance(value, dict) else (None, [error])
def _point_rows(value: Any, threshold_key: str) -> tuple[tuple[Any, Any], ...]:
    expected = {threshold_key, "points"}
    if not isinstance(value, list) or any(not isinstance(row, dict) or set(row) != expected for row in value):
        return ()
    return tuple((row.get(threshold_key), row.get("points")) for row in value)
def _nested_mapping(root: Mapping[str, Any], path: str) -> Mapping[str, Any] | None:
    value: Any = root
    for part in path.split("."):
        if not isinstance(value, Mapping):
            return None
        value = value.get(part)
    return value if isinstance(value, Mapping) else None
def _legacy_shape_errors(contract: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    for path, raw_keys in LEGACY_NESTED_KEYS.items():
        node = _nested_mapping(contract, path)
        if node is None:
            errors.append("LEGACY_STRUCTURE_INVALID")
        elif set(node) != set(raw_keys.split()):
            errors.append(f"LEGACY_NESTED_SHAPE_DRIFT:{path}")
    return errors
def _sot_semantic_errors(sot: str) -> list[str]:
    sot = _visible_markdown(sot)
    errors: list[str] = []
    authority = _normal(_section(sot, "## 권한과 정본 우선순위"))
    weekly = _normal(_section(sot, "## 보고 주차와 4주 데이터"))
    positions = _normal(_section(sot, "## 실제 고객 포지션과 Scraped 경계"))
    identity = _section(sot, "## Task identity와 중복 제거")
    linkedin = _section(sot, "## LinkedIn 시장 접근성")
    linkedin_normal = _normal(linkedin)
    publication = _normal(_section(sot, "## 외부 발행과 개인정보"))
    authority_rule = "LLM이 포지션 실행 여부, 경영 우선순위, 점수, 상태, 중복 identity를 결정할 수 없다."
    contract_rule = "두 표면이 같은 숫자 weight, enum 또는 schema 값을 모두 명시하면 반드시 동일해야 한다. 값 충돌은 machine contract의 우선권이 아니라 drift이며 위 순서대로 이 문서가 우선한다."
    if authority.count(authority_rule) != 1 or authority.count(contract_rule) != 1 or "중복 identity를 결정할 수 있다." in authority:
        errors.append("SOT_AUTHORITY_MEANING_DRIFT")
    unknown_rule = "미확인 주차는 0이 아니라 `—`, `PARTIAL`, `NOT_RUN`으로 표시한다."
    if weekly.count(unknown_rule) != 1 or "미확인 주차는 0으로 표시한다." in weekly:
        errors.append("SOT_UNKNOWN_ZERO_MEANING_DRIFT")
    history_rule = "과거 주는 같은 형식의 raw history 또는 immutable VERIFIED snapshot만 사용한다."
    if weekly.count(history_rule) != 1 or "과거 주는 현재 상태를 네 주에 복사해 사용한다." in weekly:
        errors.append("SOT_FOUR_WEEK_SOURCE_DRIFT")
    required_position_rule = "position만 포함한다. `SCRAPED_STAGING`, `INTERNAL_CREATED`, canonical lifecycle `CLOSED`, ClickUp의 외부 terminal status `closedpositions|complete`는 제외한다."
    customer_rule = (
        "고객 Gmail의 `REQUESTED|POSITION_SHARED` evidence와 canonical position이 연결돼야 "
        "고객 origin으로 승격할 수 있다."
    )
    if (
        positions.count(required_position_rule) != 1
        or positions.count(customer_rule) != 1
        or "position과 `SCRAPED_STAGING`을 모두 포함한다." in positions
        or "고객 evidence 없이도 고객 origin으로 승격한다." in positions
    ):
        errors.append("SOT_SCRAPED_BOUNDARY_DRIFT")
    matches = re.findall(r"Candidate Task identity:\s*`([^`]+)`", identity)
    identity_override = "실제 중복 제거는 외부 ClickUp task ID만 사용한다."
    if len(matches) != 1 or matches[0] != "(" + ", ".join(IDENTITY) + ")" or identity_override in identity:
        errors.append("SOT_CANDIDATE_IDENTITY_DRIFT")
    formulas = re.findall(r"market_accessibility\s*=\s*[^\n]+", linkedin)
    if len(formulas) != 1 or _normal(formulas[0]) != MARKET_FORMULA:
        errors.append("SOT_MARKET_FORMULA_MEANING_DRIFT")
    pool_rule = "Pool points는 `result_count_lower_bound`를 versioned 구간값에 매핑한다."
    if linkedin_normal.count(pool_rule) != 1:
        errors.append("SOT_MARKET_POOL_INPUT_DRIFT")
    sample_rule = (
        "각 evaluation row의 필드는 정확히 `candidate_key_hmac`, `rank`, `predicate_results`이고 "
        "`rank`는 캡처 순서와 같은 1..20이다. Predicate key 집합은 frozen "
        "`must_have_predicates`와 정확히 같아야 한다."
    )
    if linkedin_normal.count(sample_rule) != 1 or "각 값은 JSON null이 아닌 `TRUE|FALSE|UNKNOWN` 중 하나다." not in linkedin_normal or "`result_count_lower_bound`는 검증한 20명보다 작을 수 없다." not in linkedin_normal:
        errors.append("SOT_MARKET_SAMPLE_SCHEMA_DRIFT")
    errors.extend(_pipeline_errors(_section(sot, "## Pipeline 정의")))
    layout = _section(sot, "## Notion Golden Sample 형식")
    titles = tuple(re.findall(r"^\d+\. `([^`]+)`", layout, re.MULTILINE))
    if titles != GOLDEN_TITLES:
        errors.append("SOT_GOLDEN_LAYOUT_DRIFT")
    if layout.count("금지 표현:") != 1 or "필수 표현:" in layout:
        errors.append("SOT_GOLDEN_BANNED_LANGUAGE_DRIFT")
    pre_write = "외부 호출 전에는 exact target, private visibility, write-ahead intent, idempotency key, current schema readback이 필요하다."; post_write = "External object ID는 외부 쓰기 결과로 받은 뒤 readback receipt에 기록한다."
    current_rule = "전체 revision 중 가장 높은 현재 revision만 발행 후보가 될 수 있고, 그 snapshot과 weekly run이 모두 `READY`여야 한다."
    complete_rule = "Weekly run의 `PUBLISHED` 전이는 다섯 target 모두의 `READBACK_VERIFIED` intent와 verified receipt가 같은 current report snapshot에 연결된 뒤에만 허용한다."
    if publication.count(pre_write) != 1 or publication.count(post_write) != 1 or publication.count(current_rule) != 1 or publication.count(complete_rule) != 1:
        errors.append("SOT_PUBLICATION_SEQUENCE_DRIFT")
    return errors
def _pipeline_errors(section: str) -> list[str]:
    expected = {
        "Active Pipeline stages:": ACTIVE_STAGES,
        "Interview Pipeline stages:": INTERVIEW_STAGES,
        "Pre-interview Pipeline, 즉 `면접 직전 Pipeline` stages:": PRE_INTERVIEW_STAGES,
        "Current Pipeline에서 제외하는 stages:": CLOSED_STAGES,
    }
    return [
        f"SOT_PIPELINE_SET_DRIFT:{label}"
        for label, stages in expected.items()
        if _bullet_values(section, label) != stages
    ]
def _runtime_errors(raw: str) -> list[str]:
    contract, errors = _json_object(raw, "RUNTIME_CONTRACT_INVALID")
    if errors:
        return errors
    outreach_rows = contract.get("outreach_sources")
    career_rows = contract.get("career_sources")
    clickup = contract.get("clickup")
    publication = contract.get("publication"); zero_result = contract.get("zero_result_contract", {})
    if (
        not isinstance(outreach_rows, list)
        or not isinstance(career_rows, list)
        or any(not isinstance(row, dict) for row in outreach_rows)
        or not isinstance(clickup, dict)
        or not isinstance(publication, dict)
    ):
        return ["RUNTIME_STRUCTURE_INVALID"]
    outreach = {row.get("channel"): row for row in outreach_rows}
    careers = {row.get("company"): row for row in career_rows if isinstance(row, dict)}
    actual = {
        "jobkorea_operator_url": outreach.get("jobkorea", {}).get("operator_url"),
        "saramin_operator_url": outreach.get("saramin", {}).get("operator_url"),
        "clickup_list_url": clickup.get("list_url"),
        "notion_parent_url": publication.get("notion_parent_url"),
    }
    errors = [f"RUNTIME_URL_MISMATCH:{key}" for key, value in actual.items() if value != EXPECTED_URLS[key]]
    if len(outreach) != len(outreach_rows) or set(outreach) != {"jobkorea", "saramin", "linkedin_rps"} or len(careers) != len(career_rows) or set(careers) != {"SpoonLabs", "Codeit", "여기어때", "Wrtn Technologies", "FastView"} or careers.get("여기어때", {}).get("legal_operator") != "GC Company": errors.append("RUNTIME_DUPLICATE_OR_UNKNOWN_SOURCE_DRIFT")
    guards = {"default_mode": "dry_run", "require_write_ahead": True, "require_idempotency_key": True, "require_readback": True, "data_and_publication_verdicts_separate": True, "publication_report_outside_content_hash": True, "canonical_brief_warns_not_publication_complete": True, "publication_report_names_contract_errors": True}
    if any(publication.get(key) != value for key, value in guards.items()):
        errors.append("RUNTIME_PUBLICATION_GUARD_DRIFT")
    projection = contract.get("golden_projection_policy", {})
    if projection.get("legacy_priority_score_excluded") is not True or projection.get("required_output_collection_section") != "candidate_sourcing" or projection.get("post_cutoff_projection_section") != "data_coverage": errors.append("RUNTIME_GOLDEN_PROJECTION_DRIFT")
    if outreach.get("linkedin_rps", {}).get("navigation_boundary") != "existing_authenticated_aside_tab_only" or outreach.get("jobkorea", {}).get("navigation") != "operator_url > sent_history > position_offer_history" or careers.get("Codeit", {}).get("empty_allowlist_behavior") != "NOT_RUN" or any(row.get("talent_pool_behavior") != "exclude_from_active_requisition" for row in careers.values()): errors.append("RUNTIME_BROWSER_BOUNDARY_DRIFT")
    if not {"target_name", "target_id"}.issubset(publication.get("receipt_required_fields", [])): errors.append("RUNTIME_PUBLICATION_RECEIPT_TARGET_DRIFT")
    if contract.get("intent_origin_mapping") != {"REQUESTED": "CLIENT_REQUESTED", "POSITION_SHARED": "CLIENT_SHARED", "REQUIREMENT_CHANGED": "EXISTING_CLIENT_POSITION_ONLY_NO_PROMOTION", "PIPELINE_FEEDBACK": "EXISTING_CLIENT_POSITION_ONLY_NO_PROMOTION", "REFERENCE_ONLY": "NO_PROMOTION", "NONE": "NO_PROMOTION"}: errors.append("RUNTIME_INTENT_ORIGIN_MAPPING_DRIFT")
    if zero_result.get("collections") != ["positions", "position_state", "outreach_events", "pipeline_events", "pipeline_state"] or contract.get("outreach_diagnostic_contract", {}).get("require_all_channels_on_every_run") is not True: errors.append("RUNTIME_ZERO_RESULT_DRIFT" if zero_result.get("collections") != ["positions", "position_state", "outreach_events", "pipeline_events", "pipeline_state"] else "RUNTIME_OUTREACH_DIAGNOSTIC_DRIFT")
    return errors
def _legacy_errors(raw: str, semantic: bool = False) -> list[str]:
    contract, errors = _json_object(raw, "LEGACY_CONTRACT_INVALID")
    if errors:
        return errors
    expected_status = {
        "state": "CONTRACT_ONLY_NOT_EXECUTABLE",
        "publication_allowed": False,
        "replacement_required": "notion-weekly-golden-v2",
    }
    if contract.get("runtime_status") != expected_status:
        errors.append("LEGACY_PUBLICATION_NOT_BLOCKED")
    if not semantic:
        return errors
    canonical = json.dumps(contract, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    if hashlib.sha256(canonical).hexdigest() != LEGACY_CANONICAL_SHA256:
        errors.append("LEGACY_CANONICAL_DIGEST_DRIFT")
    if set(contract) != LEGACY_TOP_LEVEL:
        errors.append("LEGACY_TOP_LEVEL_SHAPE_DRIFT")
    errors.extend(_legacy_shape_errors(contract))
    if "LEGACY_STRUCTURE_INVALID" in errors:
        return errors
    template = contract.get("template", {})
    authority = contract.get("authority", {})
    four_week = contract.get("four_week_series", {})
    metrics = contract.get("metrics", {})
    market = contract.get("market_accessibility", {})
    risk = contract.get("sourcing_coverage_risk", {})
    pipeline = contract.get("pipeline", {}); privacy = contract.get("privacy", {})
    sections = contract.get("section_schemas", {})
    if set(sections) != set(GOLDEN_SECTIONS) or sections.get("candidate_sourcing", {}).get("required_collections") != ["channel_coverage", "consultant_focus", "excluded_rows"] or sections.get("data_coverage", {}).get("required_collections") != ["requirement_status", "post_cutoff_alerts"] or not {"market_formula_version", "coverage_risk_formula_version"}.issubset(sections.get("market_accessibility", {}).get("row_required_fields", [])) or not {"week_label", "metric_iso_week"}.issubset(sections.get("four_week_kpis", {}).get("row_required_fields", [])): errors.append("LEGACY_SECTION_SCHEMA_DRIFT")
    if tuple(template.get("section_order", ())) != GOLDEN_SECTIONS:
        errors.append("LEGACY_GOLDEN_LAYOUT_DRIFT")
    if tuple(template.get("detail_sections_collapsed", ())) != GOLDEN_COLLAPSED:
        errors.append("LEGACY_GOLDEN_COLLAPSE_DRIFT")
    if tuple(metrics.get("new_task_count", {}).get("dedupe_key", ())) != IDENTITY:
        errors.append("LEGACY_NEW_TASK_IDENTITY_DRIFT")
    if tuple(pipeline.get("dedupe_key", ())) != IDENTITY:
        errors.append("LEGACY_PIPELINE_IDENTITY_DRIFT")
    if market.get("evaluated_sample_size") != 20 or market.get("underfilled_unique_sample") != "UNRANKED":
        errors.append("LEGACY_MARKET_SAMPLE_DRIFT")
    if market.get("sample_selection") != "ordered_first_20_hmac_unique":
        errors.append("LEGACY_MARKET_SAMPLE_DRIFT")
    if market.get("sample_evaluation_schema") != MARKET_SAMPLE_SCHEMA:
        errors.append("LEGACY_MARKET_SAMPLE_SCHEMA_DRIFT")
    pool = _point_rows(market.get("pool_points"), "max")
    precision = _point_rows(market.get("precision_points"), "max_rate_exclusive")
    if pool != POOL_POINTS or precision != PRECISION_POINTS:
        errors.append("LEGACY_MARKET_POINT_MAPPING_DRIFT")
    if market.get("score_formula") != MARKET_FORMULA.split(" = ", 1)[1]:
        errors.append("LEGACY_MARKET_FORMULA_DRIFT")
    if (market.get("formula_version"), market.get("pool_points_input"), market.get("result_count_source"), market.get("precision_rate_formula"), market.get("precision_points_input"), market.get("source_system"), market.get("filter_dimensions_require_nonempty_string_arrays"), market.get("ordered_result_snapshot_hash_equals_source_raw_hash")) != ("market-accessibility-v2", "result_count_lower_bound", "immutable_pass_bound_provider_receipt", "qualified_sample_matches / evaluated_sample_size", "precision_rate", "linkedin_rps", True, True) or "provider_result_receipt_ref" not in market.get("required_fields", []): errors.append("LEGACY_MARKET_INPUT_DRIFT")
    if market.get("zero_qualified_override") != {"score": 0, "band": "HARD"}:
        errors.append("LEGACY_MARKET_ZERO_OVERRIDE_DRIFT")
    if "sourcing_coverage_risk" not in contract or "sourcing_coverage_priority" in contract:
        errors.append("LEGACY_COVERAGE_RISK_NAME_DRIFT")
    if risk.get("score_formula") != "recency_points + pipeline_gap_points + scarcity_points" or risk.get("formula_version") != "sourcing-coverage-risk-v1" or risk.get("ineligible_lifecycle_result") != {"score": None, "band": "UNRANKED", "reason": "INELIGIBLE_LIFECYCLE"} or (risk.get("position_age_source"), risk.get("active_candidate_source"), risk.get("inputs_recomputed_by_db")) != ("latest_pass_customer_intent_before_cutoff", "latest_pass_pipeline_event_per_task_at_cutoff", True):
        errors.append("LEGACY_COVERAGE_RISK_FORMULA_DRIFT")
    if risk.get("pipeline_gap_points") != [{"active_candidates": 0, "points": 30}, {"active_candidates": 1, "points": 20}, {"active_candidates": 2, "points": 10}, {"active_candidates_min": 3, "points": 0}]: errors.append("LEGACY_COVERAGE_RISK_BUCKET_DRIFT")
    if tuple(metrics.get("active_pipeline_count", {}).get("stages", ())) != ACTIVE_STAGES:
        errors.append("LEGACY_ACTIVE_PIPELINE_DRIFT")
    if tuple(metrics.get("interview_pipeline_count", {}).get("stages", ())) != INTERVIEW_STAGES:
        errors.append("LEGACY_INTERVIEW_PIPELINE_DRIFT")
    if tuple(metrics.get("pre_interview_pipeline_count", {}).get("stages", ())) != PRE_INTERVIEW_STAGES:
        errors.append("LEGACY_PRE_INTERVIEW_PIPELINE_DRIFT")
    if tuple(metrics) != REQUIRED_METRICS:
        errors.append("LEGACY_METRIC_SET_DRIFT")
    live = metrics.get("live_client_position_count", {})
    channel = metrics.get("channel_outreach", {})
    if not isinstance(live, dict) or live.get("allowed_origins") != ["CLIENT_REQUESTED", "CLIENT_SHARED"] or live.get("excluded_origins") != ["SCRAPED_STAGING", "INTERNAL_CREATED"]:
        errors.append("LEGACY_LIVE_POSITION_ORIGIN_DRIFT")
    if not isinstance(channel, dict) or channel.get("channels") != ["saramin", "jobkorea", "linkedin_rps"]:
        errors.append("LEGACY_OUTREACH_CHANNEL_DRIFT")
    if privacy.get("forbidden_targets_for_candidate_display_name") != ["canonical_input", "git", "email", "admin_web", "logs", "hashes", "receipts", "exceptions", "review_bundle"]: errors.append("LEGACY_PRIVACY_TARGET_DRIFT")
    if (
        four_week.get("length") != 4
        or four_week.get("contiguous_iso_weeks") is not True
        or four_week.get("missing_is_never_zero") is not True
    ):
        errors.append("LEGACY_FOUR_WEEK_SERIES_DRIFT")
    if authority.get("managerial_directives_forbidden") is not True or authority.get("llm_may_not_choose_work") is not True or authority.get("legacy_priority_score_fields_forbidden") is not True:
        errors.append("LEGACY_MANAGERIAL_AUTHORITY_DRIFT")
    if contract.get("recent_client_positions", {}).get("allowed_origins") != ["CLIENT_REQUESTED", "CLIENT_SHARED"] or contract.get("recent_client_positions", {}).get("excluded_origins") != ["SCRAPED_STAGING", "INTERNAL_CREATED"]:
        errors.append("LEGACY_RECENT_POSITION_ORIGIN_DRIFT")
    if pipeline.get("latest_event_at_cutoff_wins") is not True:
        errors.append("LEGACY_PIPELINE_LATEST_STATE_DRIFT")
    expected_fail_closed = {
        "unknown_is_not_zero": True,
        "missing_linkedin_search_is_unranked": True,
        "missing_four_week_history_is_visible": True,
        "duplicate_or_ambiguous_identity_blocks_affected_count": True,
        "publication_without_readback_is_partial": True,
    }
    if contract.get("fail_closed") != expected_fail_closed:
        errors.append("LEGACY_FAIL_CLOSED_DRIFT")
    if tuple(contract.get("hooks", ())) != EXPECTED_HOOKS:
        errors.append("LEGACY_HOOK_SET_DRIFT")
    return errors
def _reference_errors(reference: str) -> list[str]:
    digest = hashlib.sha256(reference.encode()).hexdigest()
    reference = _visible_markdown(reference)
    errors: list[str] = []
    if digest != GOLDEN_REFERENCE_SHA256:
        errors.append("GOLDEN_REFERENCE_DIGEST_DRIFT")
    source = _normal(_section(reference, "## Required source input"))
    linkedin = _section(reference, "## LinkedIn market measurement")
    linkedin_normal = _normal(linkedin)
    formula = re.search(r"market_accessibility\s*=\s*[^\n]+", linkedin)
    required_source = ("candidate_key_hmac, position_id, hiring_cycle_id", "first 20 HMAC-unique", "week_label, metric_iso_week", "provider_result_receipt_ref")
    if any(value not in source for value in required_source):
        errors.append("GOLDEN_REFERENCE_SEMANTIC_DRIFT")
    corrections = _normal(_section(reference, "## Semantic corrections"))
    recent_rule = "`최근 인입 포지션` is a chronological fact list. It has no P0/P1 and no action verbs."
    if corrections.count(recent_rule) != 1 or "must have P0/P1 and imperative action verbs" in corrections:
        errors.append("GOLDEN_REFERENCE_AUTHORITY_DRIFT")
    if not formula or _normal(formula.group(0)) != MARKET_FORMULA or "sourcing_coverage_risk" not in linkedin or "immutable PASS-bound provider result receipt" not in linkedin_normal:
        errors.append("GOLDEN_REFERENCE_SEMANTIC_DRIFT")
    sample_rules = (
        "Each row has exactly `candidate_key_hmac`, `rank`, and `predicate_results`",
        "predicate keys equal the frozen must-have set",
        "values are `TRUE|FALSE|UNKNOWN`",
    )
    if any(rule not in linkedin_normal for rule in sample_rules):
        errors.append("GOLDEN_REFERENCE_SAMPLE_SCHEMA_DRIFT")
    titles = tuple(re.findall(r"^\d+\. `([^`]+)`", _section(reference, "## Fixed Notion layout"), re.MULTILINE))
    if titles != GOLDEN_TITLES:
        errors.append("GOLDEN_REFERENCE_LAYOUT_DRIFT")
    return errors
def _sql_block(db: str, declaration: str) -> str:
    start = db.find(declaration)
    if start < 0:
        return ""
    tail = db[start + len(declaration):]
    next_object = re.search(r"\ncreate (?:table|function|unique index) ", tail)
    return db[start:start + len(declaration) + next_object.start()] if next_object else db[start:]
def _sql_semantic_block(db: str, declaration: str) -> str:
    block = _sql_block(db, declaration)
    without_comments = re.sub(r"/\*.*?\*/|--[^\n]*", "", block, flags=re.DOTALL)
    return _normal(without_comments)
def _sql_function_body(block: str) -> str:
    match = re.search(r"\bas\s+(\$[A-Za-z_][A-Za-z0-9_]*\$|\$\$)(.*?)\1\s*;", block, re.DOTALL)
    return match.group(2) if match else ""
def _executable_sql(raw: str, function_body: bool = False) -> str:
    code = _sql_function_body(raw) if function_body else raw
    code = re.sub(r"/\*.*?\*/|--[^\n]*", "", code, flags=re.DOTALL)
    code = re.sub(r"\bas\s+(\$[A-Za-z_][A-Za-z0-9_]*\$|\$\$)(.*?)\1", lambda match: "as " + match.group(2), code, flags=re.DOTALL); code = re.sub(r"(\$[A-Za-z_][A-Za-z0-9_]*\$|\$\$).*?\1", "", code, flags=re.DOTALL)
    protected = {
        "evaluation->>'candidate_key_hmac'": "__HMAC_EXPR__", "jsonb_typeof(evaluation->'candidate_key_hmac') = 'string'": "__HMAC_TYPE__",
        "(evaluation->>'rank')::integer": "__RANK_EXPR__", "jsonb_typeof(evaluation->'rank') = 'number'": "__RANK_TYPE__",
        "array['candidate_key_hmac', 'predicate_results', 'rank']::text[]": "__EXACT_FIELDS__", "from jsonb_object_keys(evaluation->'predicate_results') as result_keys(key)\n                ) is not distinct from (": "__PREDICATE_KEY_SET__",
        "where value is null or value not in ('TRUE', 'FALSE', 'UNKNOWN')": "__VALID_VALUES__",
        "where evaluation->'predicate_results'->>predicate_key = 'TRUE'": "__QUALIFIED_TRUE__",
    }
    for expression, marker in protected.items():
        code = code.replace(expression, marker)
    code = re.sub(r"'(?:''|[^'])*'", "''", code)
    return _normal(code)
def _db_market_errors(db: str) -> list[str]:
    table_raw = _sql_block(db, "create table linkedin_market_search_snapshots (")
    validator_raw = _sql_block(db, "create function weekly_market_sample_is_valid(")
    counter_raw = _sql_block(db, "create function weekly_market_qualified_count("); filter_raw = _sql_block(db, "create function weekly_market_filter_set_is_valid(filter_set jsonb)")
    table = _executable_sql(table_raw)
    validator = _executable_sql(validator_raw, function_body=True)
    counter = _executable_sql(counter_raw, function_body=True); filter_validator = _executable_sql(filter_raw, function_body=True)
    errors: list[str] = []
    sample_rules = (
        "jsonb_array_length(sample_evaluations) = 20",
        "weekly_market_sample_is_valid(sample_evaluations, must_have_predicates)",
        "count(distinct __HMAC_EXPR__) = 20", "__HMAC_TYPE__", "__RANK_TYPE__",
        "__RANK_EXPR__ = ordinal::integer",
        "__EXACT_FIELDS__",
        "jsonb_array_elements(must_have_predicates)", "__PREDICATE_KEY_SET__",
        "__VALID_VALUES__",
    )
    if any(rule not in table + " " + validator for rule in sample_rules):
        errors.append("DB_MARKET_SAMPLE_DRIFT")
    if "weekly_market_qualified_count(sample_evaluations, must_have_predicates)" not in table or not counter:
        errors.append("DB_MARKET_QUALIFIED_COUNT_DRIFT")
    counter_rules = (
        "when weekly_market_sample_is_valid(sample_evaluations, must_have_predicates) is not true then null",
        "select count(*)::integer", "__QUALIFIED_TRUE__",
    )
    if any(rule not in counter for rule in counter_rules):
        errors.append("DB_MARKET_QUALIFIED_COUNT_DRIFT")
    point_rules = (
        "pool_points = case", "precision_points = case", "weekly_market_filter_set_is_valid(filter_set) is true", "market_formula_version text not null", "coverage_risk_formula_version text not null", "coverage_risk_score = recency_points + pipeline_gap_points + scarcity_points",
        "accessibility_score = (pool_points * precision_points * 100) / 2500",
    )
    if any(rule not in table + " " + filter_validator for rule in point_rules + ("jsonb_typeof(value) <> ''", "jsonb_array_length(value) = 0", "btrim(entry #>> '') = ''")):
        errors.append("DB_MARKET_FORMULA_DRIFT")
    return errors
def _db_errors(db: str) -> list[str]:
    start = db.find("create table candidate_position_tasks (")
    end = db.find("\ncreate table ", start + 1) if start >= 0 else -1
    table = db[start:end if end >= 0 else len(db)] if start >= 0 else ""; source_table = _sql_semantic_block(db, "create table source_snapshots ("); proposal = _sql_semantic_block(db, "create table proposal_send_attempts ("); send_guard = _sql_function_body(_sql_block(db, "create function weekly_proposal_send_transition_is_valid()")); coverage = _sql_semantic_block(db, "create table outreach_channel_coverage ("); pipeline = _sql_semantic_block(db, "create table candidate_pipeline_events ("); pipeline_guard = _sql_function_body(_sql_block(db, "create function weekly_pipeline_event_is_valid()")); report = _sql_semantic_block(db, "create table report_snapshots ("); run_table = _sql_semantic_block(db, "create table weekly_runs ("); metric_zero_guard = _sql_function_body(_sql_block(db, "create function weekly_metric_snapshot_zero_is_verified()")); metric_expected = _sql_function_body(_sql_block(db, "create function weekly_metric_expected_value(")); live_branch = metric_expected.split("if target_metric_name = 'live_client_position_count' then", 1)[-1].split("elsif target_metric_name = 'new_task_count' then", 1)[0] if "if target_metric_name = 'live_client_position_count' then" in metric_expected else ""; new_task_branch = metric_expected.split("elsif target_metric_name = 'new_task_count' then", 1)[-1].split("elsif target_metric_name = 'reactivated_task_count' then", 1)[0] if "elsif target_metric_name = 'new_task_count' then" in metric_expected else ""; zero_map = _sql_function_body(_sql_block(db, "create function weekly_zero_collection_for_metric(target_metric_name text)")); report_insert = _sql_function_body(_sql_block(db, "create function weekly_report_snapshot_insert_is_valid()")); intent_guard = _sql_function_body(_sql_block(db, "create function weekly_publication_intent_snapshot_is_ready()")); receipt_guard = _sql_function_body(_sql_block(db, "create function weekly_publication_receipt_matches_intent()")); publication_complete = _sql_function_body(_sql_block(db, "create function weekly_run_publication_is_complete(target_run_id text)")); focus_guard = _sql_function_body(_sql_block(db, "create function weekly_consultant_position_focus_is_valid()")); market_lineage_raw = _sql_block(db, "create function weekly_market_snapshot_lineage_is_valid()"); canonical_guard = _sql_function_body(_sql_block(db, "create function weekly_canonical_position_transition_is_valid()")); state_guard = _sql_function_body(_sql_block(db, "create function weekly_position_state_event_is_valid()")); customer_guard = _sql_function_body(_sql_block(db, "create function weekly_customer_intent_is_valid()")); zero_guard = _sql_function_body(_sql_block(db, "create function weekly_zero_result_assertion_is_valid()")); market_receipt_guard = _sql_function_body(_sql_block(db, "create function weekly_market_result_receipt_is_valid()")); publication_intent_table = _sql_semantic_block(db, "create table publication_intents ("); publication_receipt_table = _sql_semantic_block(db, "create table publication_receipts (")
    field = re.search(r"^\s*hiring_cycle_id text not null,\s*$", table, re.MULTILINE)
    unique = re.search(r"^\s*unique \(candidate_key_hmac, position_id, hiring_cycle_id\)\s*$", table, re.MULTILINE)
    errors = [] if field and unique else ["DB_CANDIDATE_IDENTITY_DRIFT"]
    if hashlib.sha256(db.encode()).hexdigest() != DB_CONTRACT_SHA256:
        errors.append("DB_CONTRACT_DIGEST_DRIFT")
    if "evidence_refs jsonb not null check (weekly_evidence_refs_are_valid(evidence_refs))" not in source_table or "source.evidence_refs ? new.provider_receipt_ref" not in send_guard: errors.append("DB_PROPOSAL_RECEIPT_LINEAGE_DRIFT")
    if any(rule not in pipeline_guard for rule in ("select source_snapshot_id, first_created_at", "into strict task_source_snapshot_id, task_first_created_at", "new.source_snapshot_id <> task_source_snapshot_id", "new.event_at <> task_first_created_at")) or any(rule not in new_task_branch for rule in ("count(distinct event.candidate_task_id)", "event.event_type = 'CREATED'", "event.event_at = task.first_created_at", "event.source_snapshot_id = task.source_snapshot_id", "event.recorded_at <= target_meeting")): errors.append("DB_NEW_TASK_DERIVATION_DRIFT")
    if "where current_state.origin in ('CLIENT_REQUESTED', 'CLIENT_SHARED')" not in live_branch or any(origin in live_branch for origin in ("SCRAPED_STAGING", "INTERNAL_CREATED")): errors.append("DB_LIVE_CLIENT_POSITION_DERIVATION_DRIFT")
    if any(rule not in guard for guard in (canonical_guard, state_guard) for rule in ("(new.origin = 'CLIENT_REQUESTED' and intent.intent_type = 'REQUESTED')", "(new.origin = 'CLIENT_SHARED' and intent.intent_type = 'POSITION_SHARED')")) or any(value in canonical_guard + state_guard for value in ("REFERENCE_ONLY", "NONE")): errors.append("DB_CLIENT_INTENT_PROMOTION_DRIFT")
    if any(token not in guard for guard, token in ((customer_guard, "source.evidence_refs ? new.evidence_ref"), (state_guard, "source.evidence_refs ? new.evidence_ref"), (pipeline_guard, "source.evidence_refs ? new.evidence_ref"), (zero_guard, "source.evidence_refs ? new.provider_receipt_ref"), (market_receipt_guard, "source.evidence_refs ? new.protected_provider_receipt_ref"))): errors.append("DB_NORMALIZED_EVIDENCE_LINEAGE_DRIFT")
    if any("target_name text not null check ( target_name in ('database', 'clickup', 'notion', 'admin_web', 'email') )" not in table_block for table_block in (publication_intent_table, publication_receipt_table)) or "select count(*) = 5" not in publication_complete or "count(distinct intent.target_name) = 5" not in publication_complete: errors.append("DB_PUBLICATION_TARGET_SET_DRIFT")
    metric_table = _sql_semantic_block(db, "create table weekly_metric_snapshots ("); zero_table = _sql_semantic_block(db, "create table zero_result_assertions (")
    for metric in REQUIRED_METRICS:
        if f"'{metric}'" not in metric_table:
            errors.append(f"DB_WEEKLY_METRIC_MISSING:{metric}")
    executable = _executable_sql(db)
    invariants = ("create function weekly_run_transition_is_valid()", "create trigger weekly_run_transition_guard", "create function weekly_reject_truncate()", "create trigger weekly_runs_no_truncate", "create trigger source_snapshots_immutable", "unique (run_id, snapshot_id)", "foreign key (run_id, source_snapshot_id)", "references source_snapshots(run_id, snapshot_id)", "create trigger canonical_position_transition_guard", "create trigger customer_intent_insert_guard", "create table canonical_position_state_events (", "create trigger canonical_position_state_event_insert_guard", "create trigger canonical_position_state_events_immutable", "create trigger zero_result_assertions_immutable", "primary key (run_id, collection_name, dimension_key, week_index, source_snapshot_id)", "create function weekly_zero_collection_for_metric(target_metric_name text)", "create function weekly_metric_expected_value(", "create function weekly_metric_snapshot_zero_is_verified()", "create trigger weekly_metric_snapshot_zero_guard", "week_index smallint not null", "metric_iso_week text not null", "metric_window_start timestamptz not null", "create function weekly_proposal_send_transition_is_valid()", "create trigger proposal_send_attempts_transition_guard", "create function weekly_channel_mix_is_valid(channel_mix jsonb, expected_total integer)", "create function weekly_consultant_position_focus_is_valid()", "create trigger consultants_immutable", "create trigger consultant_provider_accounts_immutable", "create trigger consultants_no_truncate", "create trigger consultant_provider_accounts_no_truncate", "consultant_id text not null references consultants(consultant_id)", "create function weekly_candidate_task_source_is_valid()", "create trigger candidate_position_task_insert_guard", "create function weekly_pipeline_event_is_valid()", "where snapshot_id = new.source_snapshot_id and status = ''", "new.to_stage is distinct from previous_stage", "next_to_stage is distinct from new.to_stage", "create trigger candidate_pipeline_event_transition_guard", "create trigger candidate_pipeline_events_immutable", "create view candidate_task_current_state as", "order by event_at desc, recorded_at desc, pipeline_event_id desc", "create function weekly_evidence_refs_are_valid(evidence_refs jsonb)", "check (weekly_evidence_refs_are_valid(evidence_refs))", "create table linkedin_market_result_receipts (", "create trigger linkedin_market_result_receipt_insert_guard", "create trigger linkedin_market_result_receipts_immutable", "position_observed_at", "expected_active_candidate_count", "new.active_candidate_count is distinct from expected_active_candidate_count", "new.ordered_result_snapshot_hash is distinct from source_raw_hash", "new.result_count_lower_bound is distinct from receipt_result_count", "new.count_is_exact is distinct from receipt_count_is_exact", "new.captured_at is distinct from receipt_captured_at", "create trigger linkedin_market_search_snapshot_insert_guard", "revision integer not null check (revision > 0)", "unique (run_id, revision)", "create trigger report_snapshot_insert_guard", "create function weekly_report_snapshot_is_current(target_report_snapshot_id text)", "create function weekly_report_snapshot_is_publishable(target_report_snapshot_id text)", "create trigger publication_intent_snapshot_guard", "unique (report_snapshot_id, target_name)", "unique (publication_intent_id, target_name, target_id)", "foreign key (report_snapshot_id, expected_content_hash)", "publication_eligible boolean not null", "unique (readback_report_snapshot_id, target_name, external_object_id)", "readback_report_snapshot_id text not null references report_snapshots(report_snapshot_id)", "create function weekly_publication_intent_transition_is_valid()", "create trigger publication_intent_transition_guard", "create trigger publication_receipt_lineage_guard", "create function weekly_run_publication_is_complete(target_run_id text)")
    if any(rule not in executable for rule in invariants) or "check (window_end_exclusive = window_start + interval '7 days')" not in run_table or "date_trunc('week', meeting_at at time zone 'Asia/Seoul')" not in run_table or "week_index smallint not null check (week_index between 0 and 3)" not in zero_table or "week_index smallint not null check (week_index between 0 and 3)" not in metric_table or "current_stage text not null" in table or "provider_receipt_ref text check ( provider_receipt_ref is null or btrim(provider_receipt_ref) <> '' )" not in proposal or "check (coverage_status <> 'COVERED' or access_state = 'AUTHENTICATED')" not in coverage or "evidence_ref text not null check (btrim(evidence_ref) <> '')" not in pipeline or "check (status = 'VERIFIED' or value is null)" not in metric_table or "raise exception 'WEEKLY_METRIC_ZERO_RECEIPT_MISSING'" not in metric_zero_guard or "raise exception 'WEEKLY_METRIC_DERIVATION_INVALID'" not in metric_zero_guard or all(rule in zero_map for rule in ("then 'position_state'", "then 'outreach_events'", "then 'pipeline_events'", "then 'pipeline_state'")) is not True or "then 'pipeline_events'" in zero_map.split("'active_pipeline_count'", 1)[-1] or "revision integer not null check (revision > 0)" not in report or "unique (run_id, revision)" not in report or "for update" not in report_insert or "new.revision <> expected_revision" not in report_insert or "weekly_report_snapshot_is_publishable(new.report_snapshot_id)" not in intent_guard or "for update" not in intent_guard or "weekly_report_snapshot_is_publishable(intent_snapshot_id)" not in receipt_guard or "for update" not in receipt_guard or "weekly_report_snapshot_is_current(report.report_snapshot_id)" not in publication_complete or "weekly_run_publication_is_complete(new.run_id)" not in _sql_function_body(_sql_block(db, "create function weekly_run_transition_is_valid()")) or "PUBLICATION_INTENT_RECEIPT_MISSING" not in _sql_function_body(_sql_block(db, "create function weekly_publication_intent_transition_is_valid()")) or "PUBLICATION_RECEIPT_INTENT_STATE_INVALID" not in receipt_guard or "target_run.run_id = new.run_id" not in focus_guard or "source.fetched_at <= target_run.meeting_at" not in focus_guard or "send.run_id = new.run_id" in focus_guard or "new.position_lifecycle = 'ACTIVE' and (" not in market_lineage_raw:
        errors.append("DB_LEDGER_OR_LINEAGE_DRIFT")
    return errors + _db_market_errors(db)
def _briefing_errors(briefing: str) -> list[str]:
    briefing = _visible_markdown(briefing)
    safe_rule = "Do not issue management priorities or action directives."
    conflicts = ("이번 주 고객 액션 — ordered by deterministic priority.", "이번 주 선행 소싱 대상이다.")
    directive = re.search(r"(?:즉시 실행|우선 착수|해야 한다|오늘 연락한다|우선 연락|선행 소싱)", briefing)
    if briefing.count(safe_rule) != 1 or any(value in briefing for value in conflicts) or directive:
        return ["BRIEFING_STYLE_AUTHORITY_DRIFT"]
    return []
def _repository_semantic_errors(files: Mapping[str, str]) -> list[str]:
    errors = _sot_semantic_errors(files["sot"])
    errors.extend(error for key, expected, error in (("prompt_contract", PROMPT_CONTRACT_SHA256, "PROMPT_CONTRACT_DIGEST_DRIFT"), ("briefing_style", BRIEFING_STYLE_SHA256, "BRIEFING_STYLE_DIGEST_DRIFT"), ("brief_renderer", BRIEF_RENDERER_SHA256, "BRIEF_RENDERER_DIGEST_DRIFT"), ("runtime_contract", RUNTIME_CONTRACT_SHA256, "RUNTIME_CONTRACT_DIGEST_DRIFT"), ("skill", SKILL_SHA256, "SKILL_DIGEST_DRIFT"), ("data_contract", DATA_CONTRACT_SHA256, "DATA_CONTRACT_DIGEST_DRIFT"), ("adversarial_review", ADVERSARIAL_REVIEW_SHA256, "ADVERSARIAL_REVIEW_DIGEST_DRIFT")) if hashlib.sha256(files[key].encode()).hexdigest() != expected)
    skill_rule = "return `NOT_RUN`; do not route a Golden request through the general v1 renderer."
    skill_visible = _visible_markdown(files["skill"]); required_reads = _normal(_section(skill_visible, "## Required reads"))
    publication_override = re.search(r"publish\s+v1\s+without\s+readback", skill_visible, re.IGNORECASE)
    if required_reads.count(skill_rule) != 1 or publication_override:
        errors.append("SKILL_GOLDEN_FAIL_CLOSED_DRIFT")
    errors.extend(_runtime_errors(files["runtime_contract"]))
    errors.extend(_reference_errors(files["golden_reference"]))
    errors.extend(_briefing_errors(files["briefing_style"]))
    errors.extend(_db_errors(files["db_contract"]))
    return errors
def audit_bundle(files: Mapping[str, str]) -> list[str]:
    errors: list[str] = []
    sot = _visible_markdown(files.get("sot", ""))
    for heading in REQUIRED_HEADINGS:
        count = sot.count(heading)
        if count == 0:
            errors.append(f"SOT_HEADING_MISSING:{heading}")
        elif count > 1:
            errors.append(f"SOT_HEADING_DUPLICATE:{heading}")
    for token in REQUIRED_TOKENS:
        if token not in sot:
            errors.append(f"SOT_TOKEN_MISSING:{token}")
    for stage in PIPELINE_STAGES:
        if stage not in sot:
            errors.append(f"SOT_PIPELINE_STAGE_MISSING:{stage}")
    if MARKET_FORMULA not in sot:
        errors.append("SOT_MARKET_FORMULA_MISSING")
    for key in ("index", "skill", "prompt_contract", "golden_reference"):
        link = "weekly-ops-contract.md" if key == "index" else "docs/sot/weekly-ops-contract.md"
        if link not in files.get(key, ""):
            errors.append(f"SOT_LINK_MISSING:{key}")
    verification = files.get("verification", "")
    if STABLE_VERIFICATION not in verification or re.search(r"mutation\s+\d+종", verification):
        errors.append("VERIFICATION_COUNT_DRIFT_RISK")
    full_bundle = set(REQUIRED_PATHS).issubset(files)
    if full_bundle: errors.extend(f"REPOSITORY_LINK_MISSING:{key}:{token}" for key, tokens in REPOSITORY_REQUIREMENTS.items() for token in tokens if token not in files.get(key, ""))
    if full_bundle and hashlib.sha256(files["sot"].encode()).hexdigest() != SOT_CONTRACT_SHA256: errors.append("SOT_CONTRACT_DIGEST_DRIFT")
    errors.extend(_legacy_errors(files.get("legacy_contract", ""), full_bundle))
    if full_bundle:
        errors.extend(_repository_semantic_errors(files))
    return sorted(set(errors))
def audit_paths(repo: Path) -> list[str]:
    files: dict[str, str] = {}
    errors: list[str] = []
    for key, relative in REQUIRED_PATHS.items():
        path = repo / relative
        if not path.is_file() or path.is_symlink() or path.stat().st_size == 0:
            errors.append(f"FILE_MISSING:{relative}")
            continue
        files[key] = path.read_text(encoding="utf-8")
    for key, tokens in REPOSITORY_REQUIREMENTS.items():
        for token in tokens:
            if token not in files.get(key, ""):
                errors.append(f"REPOSITORY_LINK_MISSING:{key}:{token}")
    return sorted(set(errors + audit_bundle(files)))
def main(argv: list[str]) -> int:
    if len(argv) != 2 or argv[0] != "--repo":
        print("NOT_RUN: usage: sot_gate.py --repo <repository-root>")
        print("CHECKED: 0")
        return 2
    repo = Path(argv[1]).resolve()
    if not repo.is_dir():
        print(f"NOT_RUN: repository unavailable: {repo}")
        print("CHECKED: 0")
        return 2
    errors = audit_paths(repo)
    repository_checks = sum(map(len, REPOSITORY_REQUIREMENTS.values()))
    checked = len(REQUIRED_HEADINGS) + len(REQUIRED_TOKENS) + len(PIPELINE_STAGES) + repository_checks + 16
    for error in errors:
        print(f"FAIL: {error}")
    if errors:
        print(f"CHECKED: {checked}")
        return 1
    print("PASS: Weekly Ops SOT semantics and execution links")
    print(f"CHECKED: {checked}")
    return 0
if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
