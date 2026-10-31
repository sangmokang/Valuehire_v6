"""Lossless visible escaping for characters unsupported by PostgreSQL JSONB."""

from typing import Any


def postgres_document(value: Any) -> Any:
    if isinstance(value, str):
        return value.replace("\x00", "\\u0000")
    if isinstance(value, list):
        return [postgres_document(item) for item in value]
    if isinstance(value, dict):
        return {postgres_document(key): postgres_document(item) for key, item in value.items()}
    return value
