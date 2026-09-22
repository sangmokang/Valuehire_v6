"""Official TypeSafe SDK adapter for the organization shadow boundary."""

from collections.abc import Mapping
from typing import Any


class TypeSafeJevJudge:
    """Translate the local judge protocol to the official TypeSafe client."""

    def evaluate(
        self,
        *,
        state: Mapping[str, object],
        questions: Mapping[str, Mapping[str, Any]],
        model: str,
        timeout_seconds: float,
    ) -> Mapping[str, object]:
        raise NotImplementedError("official Jev adapter is not implemented")
