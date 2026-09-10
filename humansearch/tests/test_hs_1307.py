"""HS-13.07 — LinkedIn Recruiter Boolean 검색식 3종을 결정적으로 만드는지 확인한다."""

from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st

from humansearch.brief import (
    BooleanQuerySet,
    BriefInputError,
    build_boolean_queries,
    check_balanced,
)

# --- 1. 정상 3식 생성 — 정확한 문자열 단언 ------------------------------------

_REQUIRED = ("Product Manager", "실험")
_OPTIONAL = ("정산", "검색")
_SYNONYMS = {"Product Manager": ("PM", "프로덕트 매니저")}
_EXCLUDE = ("인턴",)

_EXPECTED_NARROW = (
    '("Product Manager" OR PM OR "프로덕트 매니저") AND 실험 AND 정산 AND 검색 NOT 인턴'
)
_EXPECTED_STANDARD = (
    '("Product Manager" OR PM OR "프로덕트 매니저") AND 실험 AND (정산 OR 검색) NOT 인턴'
)
_EXPECTED_BROAD = '("Product Manager" OR PM OR "프로덕트 매니저") AND 실험 NOT 인턴'


def test_build_boolean_queries_produces_exact_three_strings() -> None:
    result = build_boolean_queries(
        required=_REQUIRED, optional=_OPTIONAL, synonyms=_SYNONYMS, exclude=_EXCLUDE
    )
    assert result.narrow == _EXPECTED_NARROW
    assert result.standard == _EXPECTED_STANDARD
    assert result.broad == _EXPECTED_BROAD


def test_build_boolean_queries_as_tuple_matches_fields() -> None:
    result = build_boolean_queries(
        required=_REQUIRED, optional=_OPTIONAL, synonyms=_SYNONYMS, exclude=_EXCLUDE
    )
    assert result.as_tuple() == (_EXPECTED_NARROW, _EXPECTED_STANDARD, _EXPECTED_BROAD)
    assert isinstance(result, BooleanQuerySet)


def test_build_boolean_queries_all_three_are_balanced() -> None:
    result = build_boolean_queries(
        required=_REQUIRED, optional=_OPTIONAL, synonyms=_SYNONYMS, exclude=_EXCLUDE
    )
    for query in result.as_tuple():
        assert check_balanced(query)


def test_build_boolean_queries_without_optional_or_exclude() -> None:
    result = build_boolean_queries(required=("Python", "백엔드"))
    assert result.narrow == "Python AND 백엔드"
    assert result.standard == "Python AND 백엔드"
    assert result.broad == "Python AND 백엔드"


# --- 2. 거부 사례(BriefInputError) --------------------------------------------


def test_build_boolean_queries_rejects_empty_required() -> None:
    with pytest.raises(BriefInputError):
        build_boolean_queries(required=())


@pytest.mark.parametrize("bad_required", [("   ",), ("",)])
def test_build_boolean_queries_rejects_blank_term(bad_required: tuple[str, ...]) -> None:
    with pytest.raises(BriefInputError):
        build_boolean_queries(required=bad_required)


@pytest.mark.parametrize("bad_term", ['a"b', "a(b", "a)b", '"a"'])
def test_build_boolean_queries_rejects_term_with_quote_or_paren(bad_term: str) -> None:
    with pytest.raises(BriefInputError):
        build_boolean_queries(required=(bad_term,))


def test_build_boolean_queries_rejects_required_optional_overlap() -> None:
    with pytest.raises(BriefInputError):
        build_boolean_queries(required=("A",), optional=("A",))


def test_build_boolean_queries_rejects_exclude_in_required() -> None:
    with pytest.raises(BriefInputError):
        build_boolean_queries(required=("A",), exclude=("A",))


def test_build_boolean_queries_rejects_exclude_in_optional() -> None:
    with pytest.raises(BriefInputError):
        build_boolean_queries(required=("A",), optional=("B",), exclude=("B",))


def test_build_boolean_queries_rejects_unknown_synonym_key() -> None:
    with pytest.raises(BriefInputError):
        build_boolean_queries(required=("A",), synonyms={"B": ("C",)})


def test_build_boolean_queries_rejects_over_length_result() -> None:
    huge_required = tuple(f"keyword{index:04d}" for index in range(400))
    with pytest.raises(BriefInputError):
        build_boolean_queries(required=huge_required)


# --- 3. check_balanced 단위 시험 ------------------------------------------------


@pytest.mark.parametrize(
    "query",
    [
        "(a OR b",
        '"a OR b',
        "AND a",
        "a OR b)",
        "a AND",
        "NOT a",
        ")(a)",
    ],
)
def test_check_balanced_rejects_malformed_queries(query: str) -> None:
    assert check_balanced(query) is False


@pytest.mark.parametrize(
    "query",
    [
        "python",
        '("Product Manager" OR PM) AND 실험',
        "Python AND 백엔드",
        _EXPECTED_STANDARD,
    ],
)
def test_check_balanced_accepts_well_formed_queries(query: str) -> None:
    assert check_balanced(query) is True


# --- 4. 속성 기반 — 임의 정상 입력에서 균형·필수어 포함 -------------------------

_WORD_ALPHABET = (
    "가나다라마바사아자차카타파하실험정산검색인턴백엔드프론트"
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
)

_word = st.text(alphabet=_WORD_ALPHABET, min_size=1, max_size=6)


def _term_strategy() -> st.SearchStrategy[str]:
    return (
        st.lists(_word, min_size=1, max_size=2)
        .map(lambda words: " ".join(words))
        .filter(lambda term: term.strip().upper() not in {"AND", "OR", "NOT"})
    )


@given(data=st.data())
def test_build_boolean_queries_property_balanced_and_contains_required(
    data: st.DataObject,
) -> None:
    required = data.draw(
        st.lists(_term_strategy(), min_size=1, max_size=3, unique=True), label="required"
    )
    optional = data.draw(
        st.lists(_term_strategy(), max_size=3, unique=True).filter(
            lambda terms: not (set(terms) & set(required))
        ),
        label="optional",
    )
    exclude = data.draw(
        st.lists(_term_strategy(), max_size=2, unique=True).filter(
            lambda terms: not (set(terms) & (set(required) | set(optional)))
        ),
        label="exclude",
    )
    keys_pool = required + optional
    raw_synonyms = data.draw(
        st.dictionaries(
            keys=st.sampled_from(keys_pool),
            values=st.lists(_term_strategy(), max_size=2, unique=True),
            max_size=len(keys_pool),
        ),
        label="synonyms",
    )
    synonyms: dict[str, tuple[str, ...]] = {
        key: tuple(values) for key, values in raw_synonyms.items()
    }

    result = build_boolean_queries(
        required=tuple(required),
        optional=tuple(optional),
        synonyms=synonyms,
        exclude=tuple(exclude),
    )

    for query in result.as_tuple():
        assert check_balanced(query) is True
        for term in required:
            assert term in query
