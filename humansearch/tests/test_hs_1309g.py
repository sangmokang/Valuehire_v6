"""HS-13.09g — 발송 digest·저장 패킷 불변성 보강."""

from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from pathlib import Path

import pytest
from test_hs_1309 import _AT, _PACKET_ID, _intent, _packet

from humansearch.brief import (
    BriefInputError,
    PacketStore,
    SendIntent,
    SendState,
    claim_send,
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


def test_claim_send_rejects_stale_hashes_after_packet_file_body_changes(tmp_path: Path) -> None:
    directory = tmp_path / "packets"
    store = PacketStore(directory)
    original = _packet("첫 문구")
    store.save(original)
    recipients_sha256 = recipients_digest(original.mail.to, original.mail.cc)
    record_intent(
        directory,
        SendIntent(
            packet_id=_PACKET_ID,
            channel="gmail",
            attempt=1,
            recipients_sha256=recipients_sha256,
            body_sha256=original.mail.body_sha256,
            recorded_at=_AT,
            state=SendState.INTENT,
        ),
    )
    changed_body = f"{original.mail.body}\n추가 설명입니다."
    changed = replace(
        original,
        mail=replace(
            original.mail,
            body=changed_body,
            body_sha256=hashlib.sha256(changed_body.encode("utf-8")).hexdigest(),
        ),
    )
    store.path_for(_PACKET_ID).write_text(to_json(changed), encoding="utf-8")

    with pytest.raises(BriefInputError):
        claim_send(
            directory,
            _PACKET_ID,
            "gmail",
            1,
            at=_AT,
            evidence="러너가 발송 직전 청구",
            recipients_sha256=recipients_sha256,
            body_sha256=original.mail.body_sha256,
        )


def test_claim_send_rejects_packet_file_named_for_another_internal_packet_id(tmp_path: Path) -> None:
    directory = tmp_path / "packets"
    store = PacketStore(directory)
    original = _packet("첫 문구")
    store.save(original)
    recipients_sha256 = recipients_digest(original.mail.to, original.mail.cc)
    record_intent(
        directory,
        SendIntent(
            packet_id=_PACKET_ID,
            channel="gmail",
            attempt=1,
            recipients_sha256=recipients_sha256,
            body_sha256=original.mail.body_sha256,
            recorded_at=_AT,
            state=SendState.INTENT,
        ),
    )
    other_clickup = "86e1abce"
    other_packet_id = f"{other_clickup}-{original.jd.raw_sha256[:8]}"
    other = replace(
        original,
        packet_id=other_packet_id,
        position=replace(original.position, clickup_task_id=other_clickup),
    )
    store.path_for(_PACKET_ID).write_text(to_json(other), encoding="utf-8")

    with pytest.raises(BriefInputError):
        claim_send(
            directory,
            _PACKET_ID,
            "gmail",
            1,
            at=_AT,
            evidence="러너가 발송 직전 청구",
            recipients_sha256=recipients_sha256,
            body_sha256=original.mail.body_sha256,
        )
