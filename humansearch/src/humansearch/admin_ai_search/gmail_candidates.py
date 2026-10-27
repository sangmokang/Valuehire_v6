"""Candidate extraction from normalized AI Search Gmail body text."""

from __future__ import annotations

import hashlib
import html
import re
from collections.abc import Sequence
from urllib.parse import parse_qs, parse_qsl, unquote, urlencode, urlsplit, urlunsplit

from .evidence import CandidateEvidence, EvidenceContract
from .scoring import ScoreComponents, calculate_candidate_score, score_input_hash

_URL_PATTERN = re.compile(r"https?://[^\s<>\"']+", re.IGNORECASE)
_CANDIDATE_HEADING = re.compile(
    r"(?im)^\s*(?:(?:\[\[VH_HEADING\]\]|[#>*•-]+)\s*)?(?:"
    r"(?:후보|후보자|candidate)\s*(?:#|no\.?|번호)?\s*\d+|"
    r"\d+\s*(?:번|번째)?\s*(?:후보|후보자|candidate))\b|"
    r"^\s*(?:\[\[VH_HEADING\]\]|#{1,6})\s*\d+[.)]?\s+\S+"
)
_NAMED_CANDIDATE_HEADING = re.compile(
    r"(?im)^\s*\[\[VH_HEADING\]\]\s*(?:후보|후보자|candidate)\s+"
    r"(?!(?:검색\s*결과|결과|목록|추천|검색|없음|요약|현황|분석)\b)\S+"
)
_EXCLUDED_HEADING = re.compile(
    r"(?im)^\s*(?:(?:\[\[VH_HEADING\]\]|[#>*•-]+)\s*)?"
    r"(?:제외(?:된)?\s*후보|excluded\s+candidate)\b"
)
_EXPLICIT_NO_CANDIDATES = re.compile(
    r"후보\s*(?:결과\s*)?(?:없음|없습니다)|"
    r"적합한\s*후보.{0,20}(?:없음|찾지|발견하지)|"
    r"no\s+(?:suitable\s+)?candidates?",
    re.IGNORECASE,
)
_SCORE_LABELS = {
    "education": (r"학력\s*점수", r"education\s*score"),
    "job_fit": (r"직무\s*적합성\s*점수", r"job\s*fit\s*score"),
    "difficult_work": (r"고난도\s*업무\s*점수", r"difficult\s*work\s*score"),
    "job_description_logic": (
        r"직무\s*기술\s*논리성\s*점수",
        r"job\s*description\s*logic\s*score",
    ),
}


def candidate_records(
    body_text: str,
    links: Sequence[tuple[str, str]],
    contract: EvidenceContract,
) -> tuple[tuple[CandidateEvidence, ...], int, int, bool]:
    lines = [line.strip() for line in body_text.splitlines() if line.strip()]
    boundaries: list[tuple[int, bool]] = []
    for index, line in enumerate(lines):
        if _EXCLUDED_HEADING.match(line):
            boundaries.append((index, True))
        elif _CANDIDATE_HEADING.match(line):
            boundaries.append((index, False))
    if boundaries:
        known_indexes = {index for index, _ in boundaries}
        boundaries.extend(
            (index, False)
            for index, line in enumerate(lines)
            if index not in known_indexes and _NAMED_CANDIDATE_HEADING.match(line)
        )
        boundaries.sort()
        candidates: list[CandidateEvidence] = []
        unparsed = 0
        excluded = 0
        for boundary_index, (start, is_excluded) in enumerate(boundaries):
            end = (
                boundaries[boundary_index + 1][0]
                if boundary_index + 1 < len(boundaries)
                else len(lines)
            )
            context = lines[start:end]
            if is_excluded:
                excluded += 1
                continue
            occurrences = _candidate_occurrences("\n".join(context), links)
            identities = list(dict.fromkeys(url for url, _, _ in occurrences))
            if len(identities) != 1:
                unparsed += 1
                continue
            url = identities[0]
            label = next(label for item_url, label, _ in occurrences if item_url == url)
            candidates.append(_candidate_from_context(url, label, context, contract))
        return tuple(candidates), unparsed, excluded, True

    occurrences = _candidate_occurrences(body_text, links)
    if occurrences:
        if len(occurrences) == 1:
            url, label, line_index = occurrences[0]
            named_boundaries = [
                index for index, line in enumerate(lines) if _NAMED_CANDIDATE_HEADING.match(line)
            ]
            if named_boundaries:
                owner = next(
                    (index for index in reversed(named_boundaries) if index <= line_index), None
                )
                end = next(
                    (index for index in named_boundaries if index > line_index), len(lines)
                )
                start = line_index if owner is None else owner
                unparsed = len(named_boundaries) - (owner is not None)
                candidate = _candidate_from_context(url, label, lines[start:end], contract)
                return (candidate,), unparsed, 0, True
        candidates = []
        for url, label, line_index in occurrences:
            context_end = len(lines) if len(occurrences) == 1 else line_index + 1
            candidates.append(
                _candidate_from_context(url, label, lines[line_index:context_end], contract)
            )
        return tuple(candidates), 0, 0, True
    if _EXPLICIT_NO_CANDIDATES.search(body_text):
        return (), 0, 0, True
    return (), 0, 0, False


def channels(body_text: str, candidates: Sequence[CandidateEvidence]) -> tuple[str, ...]:
    found = {candidate.source_channel for candidate in candidates}
    lowered = body_text.lower()
    for marker, channel in (
        ("linkedin", "LINKEDIN"),
        ("링크드인", "LINKEDIN"),
        ("saramin", "SARAMIN"),
        ("사람인", "SARAMIN"),
        ("jobkorea", "JOBKOREA"),
        ("잡코리아", "JOBKOREA"),
    ):
        if marker in lowered:
            found.add(channel)
    return tuple(sorted(found)) or ("OTHER",)


def _candidate_occurrences(
    text: str, links: Sequence[tuple[str, str]]
) -> list[tuple[str, str, int]]:
    labels: dict[str, list[str]] = {}
    for raw_url, label in links:
        normalized = _candidate_url(raw_url)
        if normalized is not None:
            labels.setdefault(normalized, []).append(label)
    label_offsets: dict[str, int] = {}
    occurrences: list[tuple[str, str, int]] = []
    for line_index, line in enumerate(line.strip() for line in text.splitlines() if line.strip()):
        for match in _URL_PATTERN.finditer(line):
            normalized = _candidate_url(match.group(0))
            if normalized is None:
                continue
            offset = label_offsets.get(normalized, 0)
            choices = labels.get(normalized, ())
            label = choices[offset] if offset < len(choices) else normalized
            label_offsets[normalized] = offset + 1
            occurrences.append((normalized, label, line_index))
    return occurrences


def _candidate_from_context(
    url: str, label: str, context: Sequence[str], contract: EvidenceContract
) -> CandidateEvidence:
    score, score_reason, components, input_hash = _score_evidence(context, contract)
    requirements = _label_values(context, (r"필수\s*요건(?:별)?\s*근거", r"필수\s*요건"))
    contact_opinion = _first_label_value(context, (r"컨택\s*의견(?:\s*근거)?", r"추천\s*근거"))
    better_exists, better_position, better_reason = _better_position(context)
    return CandidateEvidence(
        canonical_key=hashlib.sha256(url.encode("utf-8")).hexdigest(),
        display_name=_candidate_label(label, url),
        source_channel=_channel_for_url(url),
        profile_url=url,
        education=_first_label_value(context, (r"학력", r"education")),
        experience=_first_label_value(
            context,
            (r"총\s*경력", r"전체\s*경력", r"경력", r"experience", r"career\s*summary"),
        ),
        key_experience=_first_label_value(
            context, (r"핵심\s*경력", r"주요\s*경력", r"핵심\s*업무")
        ),
        score=score,
        score_reason=score_reason,
        score_contract_version=(contract.score_contract_version if score is not None else None),
        score_components=components,
        score_input_hash=input_hash,
        why_fit=tuple(_label_values(context, (r"적합\s*근거", r"추천\s*이유", r"why\s*fit"))),
        requirements_evidence=tuple(requirements),
        reverse_match_position=None,
        reverse_match_score=None,
        reverse_match_reason="NOT_RUN:reverse_match_contract_evidence_missing",
        contact_recommendation="NOT_RUN",
        contact_opinion_evidence=contact_opinion,
        better_position_exists=better_exists,
        better_position=better_position,
        better_position_reason=better_reason,
    )


def _score_evidence(
    context: Sequence[str], contract: EvidenceContract
) -> tuple[int | None, str | None, ScoreComponents | None, str | None]:
    matched_values = {
        key: _label_values(context, labels) for key, labels in _SCORE_LABELS.items()
    }
    if any(not values for values in matched_values.values()):
        return None, "score_contract_evidence_missing", None, None
    if any(len(values) != 1 for values in matched_values.values()):
        return None, "score_contract_evidence_conflict", None, None
    raw_values = {key: values[0] for key, values in matched_values.items()}
    if any(re.fullmatch(r"\d{1,3}", value or "") is None for value in raw_values.values()):
        return None, "score_contract_evidence_invalid", None, None
    components: ScoreComponents = {key: int(value or "") for key, value in raw_values.items()}
    try:
        score = calculate_candidate_score(components, contract.score_weights)
    except ValueError:
        return None, "score_contract_evidence_invalid", None, None
    return score, None, components, score_input_hash(contract.score_contract_version, components)


def _candidate_url(raw_url: str) -> str | None:
    cleaned = html.unescape(raw_url).rstrip(".,);]}")
    parsed = urlsplit(cleaned)
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
        return None
    if parsed.username or parsed.password or parsed.port:
        return None
    host = parsed.hostname.lower().removeprefix("www.")
    if host in {"google.com", "google.co.kr"} and parsed.path == "/url":
        target = parse_qs(parsed.query).get("q", [None])[0]
        return None if target is None else _candidate_url(unquote(target))
    path = re.sub(r"/{2,}", "/", parsed.path).rstrip("/")
    if _host_is(host, "linkedin.com") and (path.startswith("/in/") or "/talent/profile/" in path):
        return urlunsplit((parsed.scheme.lower(), host, path, "", ""))
    if _host_is(host, "saramin.co.kr") and "/applicant-view/position/resume" in path:
        return urlunsplit((parsed.scheme.lower(), host, path, _identity_query(parsed.query), ""))
    if _host_is(host, "jobkorea.co.kr") and "/resume/" in path.lower():
        return urlunsplit((parsed.scheme.lower(), host, path, _identity_query(parsed.query), ""))
    return None


def _identity_query(query: str) -> str:
    return urlencode(sorted(parse_qsl(query, keep_blank_values=True)), doseq=True)


def _host_is(host: str, domain: str) -> bool:
    return host == domain or host.endswith(f".{domain}")


def _candidate_label(label: str, url: str) -> str:
    normalized = " ".join(label.split())
    return (
        url
        if normalized.lower() in {"", "링크", "프로필", "바로가기", "duplicate link"}
        else normalized
    )


def _label_values(lines: Sequence[str], labels: Sequence[str]) -> list[str]:
    values: list[str] = []
    for line in lines:
        for label in labels:
            match = re.match(rf"^\s*(?:{label})\s*[:：]\s*(.+?)\s*$", line, re.IGNORECASE)
            if match and match.group(1).strip():
                values.append(match.group(1).strip())
                break
    return list(dict.fromkeys(values))


def _first_label_value(lines: Sequence[str], labels: Sequence[str]) -> str | None:
    values = _label_values(lines, labels)
    return values[0] if values else None


def _better_position(lines: Sequence[str]) -> tuple[bool | None, str | None, str | None]:
    value = _first_label_value(
        lines, (r"더\s*적합한\s*포지션", r"더\s*적합한\s*직무", r"better\s*position")
    )
    if value is None:
        return None, None, "better_position_evidence_missing"
    if value.lower() in {"없음", "no", "none", "해당 없음"}:
        return False, None, value
    return True, value, value


def _channel_for_url(url: str) -> str:
    host = urlsplit(url).netloc
    if _host_is(host, "linkedin.com"):
        return "LINKEDIN"
    if _host_is(host, "saramin.co.kr"):
        return "SARAMIN"
    if _host_is(host, "jobkorea.co.kr"):
        return "JOBKOREA"
    return "OTHER"
