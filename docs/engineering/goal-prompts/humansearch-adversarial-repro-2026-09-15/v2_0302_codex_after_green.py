"""V2 재현기 사본 (원본 v2_0302_codex.py 는 그대로 둔다).

원본 (1) 은 GREEN 후 도달 불가다 — 같은 지시서가 요구한 제어문자 거부가 그 입력을
먼저 막기 때문이다. 거부를 잡아 출력하도록만 고치고 (2)(3) 까지 측정한다.
"""
import os, sqlite3, tempfile
from pathlib import Path
from humansearch.storage_schema import initialize_humansearch_storage
from humansearch.candidate_identity import (CandidateIdentityInput, CandidateIdentityError,
    record_candidate_identity, candidate_key_hmac)

key = os.urandom(32)
A = ("a", "saramin", "x\x1fjobkorea\x1fy")
B = ("a\x1fsaramin\x1fx", "jobkorea", "y")

print("(1a) separator collision :", candidate_key_hmac(key, *A) == candidate_key_hmac(key, *B),
      "(기대 False)")
with tempfile.TemporaryDirectory() as td:
    base = Path(td).resolve(); os.chmod(base, 0o700)
    res = initialize_humansearch_storage(base / "dbroot")
    kd = base / "keys"; kd.mkdir(mode=0o700); kp = kd / "k"; kp.write_bytes(key); kp.chmod(0o600)

    def attempt(triple, observed="2026-09-15T00:00:00Z", key_path=None):
        try:
            return "ACCEPTED " + record_candidate_identity(
                res.db_path, CandidateIdentityInput(*triple, observed),
                hmac_key_path=key_path or kp)
        except CandidateIdentityError as exc:
            return f"REJECTED {exc}"

    print("(1b) db outcome A       :", attempt(A), "(기대 REJECTED)")
    print("(1b) db outcome B       :", attempt(B), "(기대 REJECTED)")
    rows = sqlite3.connect(res.db_path).execute("select count(*) from hs_candidates").fetchone()[0]
    print("(1c) rows after both    :", rows, "(기대 0)")
    # 합법 경계쌍은 여전히 별도 행으로 남아야 한다 — 전부 거부하는 구현 방지 대조군
    print("(1d) legal pair ab/c    :", attempt(("ab", "saramin", "c")), "(기대 ACCEPTED inserted)")
    print("(1d) legal pair a/bc    :", attempt(("a", "saramin", "bc")), "(기대 ACCEPTED inserted)")
    rows = sqlite3.connect(res.db_path).execute("select count(*) from hs_candidates").fetchone()[0]
    print("(1e) rows legal pair    :", rows, "(기대 2)")

    sub = res.db_path.parent / "keys"; sub.mkdir(mode=0o700)
    kp2 = sub / "k"; kp2.write_bytes(key); kp2.chmod(0o600)
    print("(2) key under db root   :", attempt(("p", "saramin", "c"), key_path=kp2), "(기대 REJECTED)")
    print("(3) 2026-99-99T99:99:99 :", attempt(("p2", "saramin", "c"), "2026-99-99T99:99:99+99:99"),
          "(기대 REJECTED)")
