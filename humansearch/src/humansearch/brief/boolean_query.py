"""HS-13.07 — LinkedIn Recruiter Boolean 검색식 3종(좁게·표준·넓게)을 결정적으로 만든다.

순수 함수. 시계·파일·네트워크 접근 0. §5 계약(HS-13 브리프 스펙 문서)을 생성 시점에 강제한다.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass

from .types import BriefInputError

__all__ = ["BooleanQuerySet", "build_boolean_queries", "check_balanced"]

_OPERATORS = frozenset({"AND", "OR", "NOT"})
_QUOTE_TRIGGER_CHARS = (" ", "/", "-")
_MAX_QUERY_LENGTH = 3000
# 균형 검사용 토큰화: 따옴표로 감싼 구절은 한 토큰으로 보존해 그 내부의 단어가
# 우연히 AND/OR/NOT 과 같아도 연산자로 오인하지 않는다.
_TOKEN_RE = re.compile(r'"[^"]*"|[()]|[^\s()"]+')


def _needs_quotes(term: str) -> bool:
    return any(char in term for char in _QUOTE_TRIGGER_CHARS)


def _quote(term: str) -> str:
    return f'"{term}"' if _needs_quotes(term) else term


def _require_clean_term(term: str, field: str) -> None:
    if not term.strip():
        raise BriefInputError(f"{field} 는 공백만일 수 없다: {term!r}")
    if '"' in term or "(" in term or ")" in term:
        raise BriefInputError(f"{field} 는 큰따옴표·괄호를 포함할 수 없다: {term!r}")


def _dedup_with_synonyms(term: str, synonyms: Mapping[str, tuple[str, ...]]) -> tuple[str, ...]:
    seen: list[str] = []
    for candidate in (term, *synonyms.get(term, ())):
        if candidate not in seen:
            seen.append(candidate)
    return tuple(seen)


def _format_group(elements: tuple[str, ...]) -> str:
    quoted = tuple(_quote(element) for element in elements)
    if len(quoted) == 1:
        return quoted[0]
    return "(" + " OR ".join(quoted) + ")"


@dataclass(frozen=True)
class BooleanQuerySet:
    """narrow(좁게)·standard(표준)·broad(넓게) Boolean 검색식 3종."""

    narrow: str
    standard: str
    broad: str

    def as_tuple(self) -> tuple[str, str, str]:
        return (self.narrow, self.standard, self.broad)


def build_boolean_queries(
    required: tuple[str, ...],
    optional: tuple[str, ...] = (),
    synonyms: Mapping[str, tuple[str, ...]] = {},
    exclude: tuple[str, ...] = (),
) -> BooleanQuerySet:
    """required/optional/synonyms/exclude 로 좁게·표준·넓게 3종 검색식을 만든다.

    narrow = required 그룹 전부 AND + optional 그룹 전부 AND
    standard = required 전부 AND + (optional 그룹들 OR로 합친 하나의 그룹)
    broad = required 그룹 전부 AND
    세 식 모두 exclude 가 있으면 끝에 ` NOT (e1 OR e2 ...)` (1개면 ` NOT e1`)를 덧붙인다.
    """
    if not required:
        raise BriefInputError("required 는 비어 있을 수 없다")

    for term in required:
        _require_clean_term(term, "required")
    for term in optional:
        _require_clean_term(term, "optional")
    for term in exclude:
        _require_clean_term(term, "exclude")
    for alternatives in synonyms.values():
        for alternative in alternatives:
            _require_clean_term(alternative, "synonyms")

    required_set = set(required)
    optional_set = set(optional)
    overlap = required_set & optional_set
    if overlap:
        raise BriefInputError(f"required 와 optional 이 겹친다: {sorted(overlap)}")

    known_terms = required_set | optional_set
    exclude_overlap = set(exclude) & known_terms
    if exclude_overlap:
        raise BriefInputError(f"exclude 가 required/optional 과 겹친다: {sorted(exclude_overlap)}")

    unknown_synonym_keys = set(synonyms.keys()) - known_terms
    if unknown_synonym_keys:
        raise BriefInputError(
            f"synonyms 키가 required/optional 밖에 있다: {sorted(unknown_synonym_keys)}"
        )

    required_groups = tuple(
        _format_group(_dedup_with_synonyms(term, synonyms)) for term in required
    )
    optional_groups = tuple(
        _format_group(_dedup_with_synonyms(term, synonyms)) for term in optional
    )

    exclude_clause = f" NOT {_format_group(tuple(exclude))}" if exclude else ""

    narrow = " AND ".join((*required_groups, *optional_groups)) + exclude_clause

    if optional_groups:
        optional_combined = (
            optional_groups[0]
            if len(optional_groups) == 1
            else "(" + " OR ".join(optional_groups) + ")"
        )
        standard = " AND ".join((*required_groups, optional_combined)) + exclude_clause
    else:
        standard = " AND ".join(required_groups) + exclude_clause

    broad = " AND ".join(required_groups) + exclude_clause

    for label, query in (("narrow", narrow), ("standard", standard), ("broad", broad)):
        if len(query) > _MAX_QUERY_LENGTH:
            raise BriefInputError(
                f"{label} 검색식이 {_MAX_QUERY_LENGTH}자를 초과한다: {len(query)}자"
            )

    return BooleanQuerySet(narrow=narrow, standard=standard, broad=broad)


def check_balanced(query: str) -> bool:
    """큰따옴표 짝·괄호 깊이·AND/OR/NOT 이 식 시작/끝에 오지 않는지 검사한다."""
    if query.count('"') % 2 != 0:
        return False

    depth = 0
    for char in query:
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth < 0:
                return False
    if depth != 0:
        return False

    tokens = _TOKEN_RE.findall(query)
    if not tokens:
        return True

    start = 0
    while start < len(tokens) and tokens[start] == "(":
        start += 1
    end = len(tokens) - 1
    while end >= 0 and tokens[end] == ")":
        end -= 1
    if start > end:
        return True

    return not (tokens[start] in _OPERATORS or tokens[end] in _OPERATORS)
