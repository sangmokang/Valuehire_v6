"""HS-03.02 v2 — raw+normalized candidate storage, transactional writes, observation history.

Design contract: docs/engineering/humansearch-hs-0302-storage-v2-goal-2026-09-17.md
Owner-directed rewrite (2026-09-17): raw values are evidence and must never be
discarded; HMAC is optional secondary identity only; filesystem-attack hardening
(decoy fd / VFS interception) is explicitly out of scope for this unit.
"""

from __future__ import annotations

import sqlite3
import threading
from pathlib import Path

import pytest

from humansearch.candidate_storage import (
    CandidateObservationInput,
    CandidateStorageError,
    CandidateStorageRetryExhausted,
    record_candidate_observation,
)
from humansearch.candidate_storage_schema import initialize_candidate_storage


def _db(tmp_path: Path) -> Path:
    result = initialize_candidate_storage(tmp_path / "approved")
    return result.db_path


def _input(**overrides: object) -> CandidateObservationInput:
    fields: dict[str, object] = {
        "position_ref": "pos-1",
        "channel": "linkedin_rps",
        "candidate_ref": "li-profile-abc",
        "observed_at": "2026-09-17T08:21:00Z",
        "ingestion_id": "crawl-20260917-00001",
        "email": None,
        "profile_url": None,
    }
    fields.update(overrides)
    return CandidateObservationInput(**fields)  # type: ignore[arg-type]


# --- AC-1/AC-9: raw values survive, first write creates a candidate, readback matches ---


def test_first_write_stores_raw_and_normalized_email_and_url(tmp_path: Path) -> None:
    db_path = _db(tmp_path)
    result = record_candidate_observation(
        db_path,
        _input(
            email="John.Kim@Example.com",
            profile_url="https://www.linkedin.com/in/abc/?trk=test",
        ),
    )
    assert result.outcome == "candidate_created"
    assert result.candidate.email_raw == "John.Kim@Example.com"
    assert result.candidate.email_normalized == "john.kim@example.com"
    assert result.candidate.profile_url_raw == "https://www.linkedin.com/in/abc/?trk=test"
    assert result.candidate.profile_url_normalized == "https://www.linkedin.com/in/abc"
    # counter-AC: a "success" that only proves an INSERT ran, not a committed+readable row, is fake.
    connection = sqlite3.connect(db_path)
    try:
        row = connection.execute(
            "select email_raw, profile_url_raw from hs_candidates where candidate_id = ?",
            (result.candidate.candidate_id,),
        ).fetchone()
    finally:
        connection.close()
    assert row == ("John.Kim@Example.com", "https://www.linkedin.com/in/abc/?trk=test")


# --- AC-2: required field missing must reject before any row is written ---


def test_missing_candidate_ref_is_rejected_with_no_write(tmp_path: Path) -> None:
    db_path = _db(tmp_path)
    with pytest.raises(CandidateStorageError):
        record_candidate_observation(db_path, _input(candidate_ref="   "))
    connection = sqlite3.connect(db_path)
    try:
        count = connection.execute("select count(*) from hs_candidates").fetchone()[0]
    finally:
        connection.close()
    assert count == 0


# --- email/url omission must not corrupt data (nullable, not a silent lie) ---


def test_missing_email_and_url_are_stored_as_null_not_fabricated(tmp_path: Path) -> None:
    db_path = _db(tmp_path)
    result = record_candidate_observation(db_path, _input())
    assert result.candidate.email_raw is None
    assert result.candidate.email_normalized is None
    assert result.candidate.profile_url_raw is None
    assert result.candidate.profile_url_normalized is None


# --- AC-3/AC-4: format validation rejects garbage before writing ---


def test_invalid_email_format_is_rejected(tmp_path: Path) -> None:
    db_path = _db(tmp_path)
    with pytest.raises(CandidateStorageError):
        record_candidate_observation(db_path, _input(email="not-an-email"))
    connection = sqlite3.connect(db_path)
    try:
        count = connection.execute("select count(*) from hs_candidates").fetchone()[0]
    finally:
        connection.close()
    assert count == 0


def test_invalid_url_format_is_rejected(tmp_path: Path) -> None:
    db_path = _db(tmp_path)
    with pytest.raises(CandidateStorageError):
        record_candidate_observation(db_path, _input(profile_url="not a url"))
    connection = sqlite3.connect(db_path)
    try:
        count = connection.execute("select count(*) from hs_candidates").fetchone()[0]
    finally:
        connection.close()
    assert count == 0


# --- AC-5: re-observation of the same candidate must append history, not duplicate/overwrite ---


def test_reobservation_reuses_candidate_and_appends_observation(tmp_path: Path) -> None:
    db_path = _db(tmp_path)
    first = record_candidate_observation(
        db_path, _input(ingestion_id="run-1", observed_at="2026-09-01T00:00:00Z")
    )
    second = record_candidate_observation(
        db_path, _input(ingestion_id="run-2", observed_at="2026-09-17T00:00:00Z")
    )
    assert first.candidate.candidate_id == second.candidate.candidate_id
    assert second.outcome == "observation_added"
    connection = sqlite3.connect(db_path)
    try:
        candidate_count = connection.execute("select count(*) from hs_candidates").fetchone()[0]
        observation_count = connection.execute(
            "select count(*) from hs_candidate_observations"
        ).fetchone()[0]
    finally:
        connection.close()
    assert candidate_count == 1
    assert observation_count == 2  # history accumulates, nothing is overwritten


def test_reobservation_backfills_missing_email_without_overwriting_existing(
    tmp_path: Path,
) -> None:
    db_path = _db(tmp_path)
    record_candidate_observation(db_path, _input(ingestion_id="run-1"))
    filled = record_candidate_observation(
        db_path, _input(ingestion_id="run-2", email="found@example.com")
    )
    assert filled.candidate.email_raw == "found@example.com"
    # a later, different email must never clobber recorded evidence
    kept = record_candidate_observation(
        db_path, _input(ingestion_id="run-3", email="different@example.com")
    )
    assert kept.candidate.email_raw == "found@example.com"


# --- AC-6: retrying the same ingestion must be idempotent, not a duplicate row ---


def test_retry_of_same_ingestion_id_is_idempotent(tmp_path: Path) -> None:
    db_path = _db(tmp_path)
    record_candidate_observation(db_path, _input(ingestion_id="crawl-retry"))
    replay = record_candidate_observation(db_path, _input(ingestion_id="crawl-retry"))
    assert replay.outcome == "duplicate_observation"
    connection = sqlite3.connect(db_path)
    try:
        observation_count = connection.execute(
            "select count(*) from hs_candidate_observations"
        ).fetchone()[0]
    finally:
        connection.close()
    assert observation_count == 1


# --- AC-7: a mid-transaction failure must roll back everything, not leave a partial row ---


def test_mid_transaction_failure_rolls_back_candidate_and_observation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db_path = _db(tmp_path)
    real_connect = sqlite3.connect

    class _FailingCommitConnection(sqlite3.Connection):
        def commit(self) -> None:
            raise sqlite3.OperationalError("simulated mid-transaction failure")

    def _connect_with_failing_commit(*args: object, **kwargs: object) -> sqlite3.Connection:
        return real_connect(*args, **{**kwargs, "factory": _FailingCommitConnection})  # type: ignore[arg-type]

    monkeypatch.setattr(sqlite3, "connect", _connect_with_failing_commit)
    with pytest.raises(sqlite3.OperationalError):
        record_candidate_observation(db_path, _input())
    monkeypatch.undo()
    connection = sqlite3.connect(db_path)
    try:
        candidate_count = connection.execute("select count(*) from hs_candidates").fetchone()[0]
        observation_count = connection.execute(
            "select count(*) from hs_candidate_observations"
        ).fetchone()[0]
    finally:
        connection.close()
    assert candidate_count == 0  # counter-AC: partial visibility of only one table is data loss
    assert observation_count == 0


# --- AC-8: concurrent identical writes must converge to exactly one candidate row ---


def test_ten_concurrent_writes_of_the_same_candidate_yield_one_candidate_row(
    tmp_path: Path,
) -> None:
    db_path = _db(tmp_path)
    errors: list[BaseException] = []

    def _write(i: int) -> None:
        try:
            record_candidate_observation(db_path, _input(ingestion_id=f"concurrent-{i}"))
        except BaseException as exc:  # noqa: BLE001 -- collected for the assertion below
            errors.append(exc)

    threads = [threading.Thread(target=_write, args=(i,)) for i in range(10)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert errors == []
    connection = sqlite3.connect(db_path)
    try:
        candidate_count = connection.execute("select count(*) from hs_candidates").fetchone()[0]
        observation_count = connection.execute(
            "select count(*) from hs_candidate_observations"
        ).fetchone()[0]
    finally:
        connection.close()
    assert candidate_count == 1
    assert observation_count == 10


# --- distinct candidates must never be merged into one row ---


def test_different_candidate_ref_creates_a_separate_candidate(tmp_path: Path) -> None:
    db_path = _db(tmp_path)
    first = record_candidate_observation(db_path, _input(candidate_ref="li-profile-abc"))
    second = record_candidate_observation(db_path, _input(candidate_ref="li-profile-xyz"))
    assert first.candidate.candidate_id != second.candidate.candidate_id


# --- SQLITE_BUSY must retry with a hard cap, never hang or silently report success ---


def test_persistent_lock_raises_after_retry_cap_instead_of_hanging(tmp_path: Path) -> None:
    db_path = _db(tmp_path)
    blocker = sqlite3.connect(db_path, timeout=0.1)
    blocker.execute("begin exclusive")
    try:
        with pytest.raises(CandidateStorageRetryExhausted):
            record_candidate_observation(db_path, _input())
    finally:
        blocker.rollback()
        blocker.close()
