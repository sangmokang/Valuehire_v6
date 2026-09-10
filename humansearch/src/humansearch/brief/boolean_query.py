"""HS-13.07 — LinkedIn Recruiter Boolean 검색식 3종(좁게·표준·넓게)을 결정적으로 만든다.

순수 함수. 시계·파일·네트워크 접근 0. §5 계약(HS-13 브리프 스펙 문서)을 생성 시점에 강제한다.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from . import BriefInputError

__all__ = ["BooleanQuerySet", "build_boolean_queries", "check_balanced"]


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
    synonyms: Mapping[str, tuple[str, ...]] = {},  # noqa: B006 - 읽기 전용 결정적 순수 함수
    exclude: tuple[str, ...] = (),
) -> BooleanQuerySet:
    """required/optional/synonyms/exclude 로 좁게·표준·넓게 3종 검색식을 만든다.

    (RED 골격) 아직 구현되지 않았다.
    """
    raise NotImplementedError


def check_balanced(query: str) -> bool:
    """큰따옴표 짝·괄호 깊이·AND/OR/NOT 이 식 시작/끝에 오지 않는지 검사한다.

    (RED 골격) 아직 구현되지 않았다.
    """
    raise NotImplementedError
