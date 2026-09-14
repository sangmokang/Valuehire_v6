"""HS-13.09g — 발송 digest·저장 패킷 불변성 보강."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from test_hs_1309 import _PACKET_ID, _intent, _packet

from humansearch.brief import (
    BriefInputError,
    PacketStore,
    from_json,
    recipients_digest,
    record_intent,
    to_json,
)


def test_packet_json_requires_schema_version_one() -> None:
    payload = json.loads(to_json(_packet()))
    assert payload["schema_version"] == 1
    del payload["schema_version"]
    with pytest.raises(BriefInputError):
        from_json(json.dumps(payload, ensure_ascii=False))
    payload["schema_version"] = 2
    with pytest.raises(BriefInputError):
        from_json(json.dumps(payload, ensure_ascii=False))


def test_save_rejects_changed_packet_after_send_intent_exists(tmp_path: Path) -> None:
    directory = tmp_path / "packets"
    store = PacketStore(directory)
    original = _packet("첫 문구")
    store.save(original)
    record_intent(directory, _intent())

    with pytest.raises(BriefInputError):
        store.save(_packet("두 번째 문구"))

    assert store.load(_PACKET_ID) == original


def test_recipients_digest_sorts_within_to_cc_but_keeps_roles_distinct() -> None:
    assert recipients_digest(
        ("z@example.org", "a@example.org"), ("c@example.org",)
    ) == recipients_digest(("a@example.org", "z@example.org"), ("c@example.org",))
    assert recipients_digest(("a@example.org",), ("c@example.org",)) != recipients_digest(
        ("a@example.org", "c@example.org"), ()
    )
    with pytest.raises(BriefInputError):
        recipients_digest(("a@example.org",), ("a@example.org",))
