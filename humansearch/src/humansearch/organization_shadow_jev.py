"""Official TypeSafe SDK adapter for the organization shadow boundary."""

import json
import logging
from collections.abc import Mapping
from typing import Any, cast

from typesafe_sdk import JSONContent, Question, RetryPolicy, TypeSafeClient


class TypeSafeJevJudge:
    """Translate the local judge protocol to the official TypeSafe client."""

    def __init__(self, client: TypeSafeClient | None = None, *, api_key: str | None = None,
                 base_url: str | None = None, retry: RetryPolicy | None = None) -> None:
        sdk_logger = logging.getLogger("typesafe_sdk")
        if sdk_logger.level < logging.WARNING:
            sdk_logger.setLevel(logging.WARNING)
        self._client = client or TypeSafeClient(api_key=api_key, base_url=base_url, retry=retry)
        self._owns_client = client is None

    def evaluate(
        self,
        *,
        state: Mapping[str, object],
        questions: Mapping[str, Mapping[str, Any]],
        model: str,
        timeout_seconds: float,
    ) -> Mapping[str, object]:
        response = self._client.system_one(
            cast(JSONContent, state),
            cast(Mapping[str, Question], questions),
            model=model,
            timeout=timeout_seconds,
        )
        raw = json.loads(response.raw_http_response.content)
        if not isinstance(raw, dict):
            raise TypeError("Jev response must be a JSON object")
        return cast(Mapping[str, object], raw)

    def close(self) -> None:
        if self._owns_client:
            self._client.close()
