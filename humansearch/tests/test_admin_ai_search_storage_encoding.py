"""PostgreSQL JSONB cannot hold NUL; retain a visible escape and original raw checksum."""

from humansearch.admin_ai_search.storage_encoding import postgres_document


def test_nested_nul_is_preserved_as_a_visible_escape_without_mutating_the_raw() -> None:
    raw = {"id": "message", "body": "before\x00after", "parts": [{"text": "\x00"}], "checksum": "raw-sha"}
    safe = postgres_document(raw)
    assert safe["body"] == "before\\u0000after"
    assert safe["parts"] == [{"text": "\\u0000"}]
    assert safe["checksum"] == "raw-sha"
    assert raw["body"] == "before\x00after"
