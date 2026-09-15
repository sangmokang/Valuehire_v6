"""F83-2 결정적 재현: save(B) 의 intent 확인 직후에 record_intent(A)+claim_send(A) 를 끼워 넣는다."""
import sys, tempfile
from dataclasses import replace
from pathlib import Path
sys.path.insert(0, "tests")
import test_hs_1309e as t
from humansearch.brief import PacketStore, TeamMail, from_json, record_intent, claim_send, recipients_digest
from humansearch.brief.send_claim import _check_current_packet_digest
from humansearch.brief.packet import read_store_file
from humansearch.brief import BriefInputError

with tempfile.TemporaryDirectory() as td:
    d = Path(td) / "ledger"; d.mkdir(mode=0o700)
    A = t._current_packet()
    body_b = A.mail.body + "추가 줄\n"
    B = replace(A, mail=replace(A.mail, body=body_b, body_sha256=t._sha256(body_b)))
    store = PacketStore(d); store.save(A)
    claimed = {}
    orig = PacketStore._has_send_intent
    def hooked(self, pid):
        r = orig(self, pid)                      # save(B) 가 본 값: intent 없음
        rec, created = record_intent(d, t._intent())
        intent, got = claim_send(d, t._PACKET_ID, "gmail", 1, at=t._CLAIM_AT, evidence="청구",
                                 recipients_sha256=recipients_digest(A.mail.to, A.mail.cc), body_sha256=A.mail.body_sha256)
        claimed.update(created=created, got=got, saw_intent=r)
        return r
    PacketStore._has_send_intent = hooked
    try:
        path = store.save(B)
        outcome = f"save(B) ACCEPTED -> {path.name}"
    except BriefInputError as e:
        outcome = f"save(B) REJECTED -> {e}"
    PacketStore._has_send_intent = orig
    stored = from_json(read_store_file(d / f"{t._PACKET_ID}.packet.json"))
    print("claim_send(A) got send right:", claimed)
    print(outcome)
    print("stored body_sha256 == claimed A digest:", stored.mail.body_sha256 == A.mail.body_sha256)
    try:
        _check_current_packet_digest(d, t._PACKET_ID, intent if False else claim_send.__globals__['_latest'](d, t._PACKET_ID, "gmail"))
        print("post-hoc digest check: PASSES (would send B under A's claim)")
    except BriefInputError as e:
        print("post-hoc digest check: REJECTS ->", str(e)[:80])
