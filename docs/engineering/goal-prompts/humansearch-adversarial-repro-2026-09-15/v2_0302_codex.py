"""V2: Codex V1 HS-03.02 결함 재현 (실제 임시 DB, 저장소 무변경)."""
import os, sqlite3, tempfile
from pathlib import Path
from humansearch.storage_schema import initialize_humansearch_storage
from humansearch.candidate_identity import (CandidateIdentityInput, CandidateIdentityError,
    record_candidate_identity, candidate_key_hmac)
key = os.urandom(32)
# (1) 구분자 주입 충돌
a = candidate_key_hmac(key, "a", "saramin", "x\x1fjobkorea\x1fy")
b = candidate_key_hmac(key, "a\x1fsaramin\x1fx", "jobkorea", "y")
print("(1) separator collision  :", a == b)
with tempfile.TemporaryDirectory() as td:
    base = Path(td).resolve(); os.chmod(base, 0o700)
    res = initialize_humansearch_storage(base / "dbroot")
    kd = base / "keys"; kd.mkdir(mode=0o700); kp = kd / "k"; kp.write_bytes(key); kp.chmod(0o600)
    r1 = record_candidate_identity(res.db_path, CandidateIdentityInput("a", "saramin", "x\x1fjobkorea\x1fy", "2026-09-15T00:00:00Z"), hmac_key_path=kp)
    r2 = record_candidate_identity(res.db_path, CandidateIdentityInput("a\x1fsaramin\x1fx", "jobkorea", "y", "2026-09-15T00:00:00Z"), hmac_key_path=kp)
    rows = sqlite3.connect(res.db_path).execute("select count(*) from hs_candidates").fetchone()[0]
    print("(1) db outcome           :", r1, r2, "| rows:", rows, "(기대 inserted inserted 2)")
    # (2) DB 루트 하위 디렉터리 키
    sub = res.db_path.parent / "keys"; sub.mkdir(mode=0o700); kp2 = sub / "k"; kp2.write_bytes(key); kp2.chmod(0o600)
    try:
        r = record_candidate_identity(res.db_path, CandidateIdentityInput("p", "saramin", "c", "2026-09-15T00:00:00Z"), hmac_key_path=kp2); out = f"ACCEPTED {r}"
    except CandidateIdentityError as e: out = f"REJECTED {e}"
    print("(2) key under db root    :", out, "(기대 REJECTED)")
    # (3) 달력 밖 시각
    try:
        r = record_candidate_identity(res.db_path, CandidateIdentityInput("p2", "saramin", "c", "2026-99-99T99:99:99+99:99"), hmac_key_path=kp); out = f"ACCEPTED {r}"
    except CandidateIdentityError as e: out = f"REJECTED {e}"
    print("(3) 2026-99-99T99:99:99  :", out, "(기대 REJECTED)")
