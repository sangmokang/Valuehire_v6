"""HS-13.10c — readback 검증과 VERIFIED 장부 전이를 한 경계에서 수행한다."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from test_hs_1310b import (
    _JP,
    _PACKET_ID,
    _claim,
    _intent,
    _ledger,
    _mail_body,
    _moment,
    _write_packet_and_sent,
)

from humansearch.brief import BriefInputError, SendState, load_intent, mark, record_intent
from humansearch.brief import cli as cli_module


def test_verify_and_mark_rejects_packet_recipients_changed_after_send_claim(tmp_path: Path) -> None:
    body = "정상 본문"
    directory = _ledger(tmp_path)
    record_intent(directory, _intent(_mail_body(_JP, body)))
    _claim(directory, _mail_body(_JP, body))
    mark(directory, _PACKET_ID, "gmail", 1, SendState.SENT_UNVERIFIED, "msg-1", _moment(5), "발송함 id")
    packet_path, sent_path = _write_packet_and_sent(
        tmp_path, body, f"{body}\npacket-id: {_PACKET_ID}"
    )
    payload = json.loads(packet_path.read_text(encoding="utf-8"))
    payload["mail"]["to"] = ["other@example.org"]
    packet_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    with pytest.raises(BriefInputError):
        cli_module.verify_and_mark(directory, packet_path, sent_path, "msg-1", _moment(6))


def test_main_verify_mark_writes_verified_transition(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    body = "정상 본문"
    directory = _ledger(tmp_path)
    record_intent(directory, _intent(_mail_body(_JP, body)))
    _claim(directory, _mail_body(_JP, body))
    mark(directory, _PACKET_ID, "gmail", 1, SendState.SENT_UNVERIFIED, "msg-1", _moment(5), "발송함 id")
    packet_path, sent_path = _write_packet_and_sent(
        tmp_path, body, f"{body}\npacket-id: {_PACKET_ID}"
    )

    from humansearch.brief.__main__ import main

    code = main([
        "verify",
        "--packet",
        str(packet_path),
        "--sent",
        str(sent_path),
        "--mark-dir",
        str(directory),
        "--message-id",
        "msg-1",
        "--at",
        _moment(6).isoformat(),
    ])

    assert code == 0
    assert "VERIFIED" in capsys.readouterr().out
    verified = load_intent(directory, _PACKET_ID, "gmail")
    assert verified is not None
    assert verified.state is SendState.VERIFIED
