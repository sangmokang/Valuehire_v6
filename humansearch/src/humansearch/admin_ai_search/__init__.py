"""Contract-first AI Search evidence view for the v6 admin surface."""

from .evidence import (
    AiSearchPayload,
    AiSearchRun,
    CandidateEvidence,
    ContactEvidence,
    EvidenceContract,
    VerificationCheck,
    build_ai_search_batch,
    build_ai_search_payload,
    load_evidence_contract,
    stable_batch_id,
)
from .scoring import ScoreComponents, calculate_candidate_score, score_input_hash
from .weekly_view import (
    WeeklyAiSearchIndexPayload,
    WeeklyAiSearchViewPayload,
    WeeklyAiSearchWeekPayload,
    build_weekly_ai_search_index,
    build_weekly_ai_search_view,
)

__all__ = [
    "AiSearchPayload",
    "AiSearchRun",
    "CandidateEvidence",
    "ContactEvidence",
    "EvidenceContract",
    "ScoreComponents",
    "VerificationCheck",
    "WeeklyAiSearchIndexPayload",
    "WeeklyAiSearchViewPayload",
    "WeeklyAiSearchWeekPayload",
    "build_ai_search_batch",
    "build_ai_search_payload",
    "build_weekly_ai_search_index",
    "build_weekly_ai_search_view",
    "calculate_candidate_score",
    "load_evidence_contract",
    "score_input_hash",
    "stable_batch_id",
]
