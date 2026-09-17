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
    assert result.candidate.profile_url_normalized == "https://linkedin.com/in/abc"
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
        return real_connect(  # type: ignore[call-overload, no-any-return]
            *args, **{**kwargs, "factory": _FailingCommitConnection}
        )

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


# --- a URL-shaped candidate_ref must dedup like a URL, not split on tracking params ---
# (reproduced 2026-09-17 via adversarial check against an owner-side review: two
# observations of the same LinkedIn profile URL, differing only by ?trk=..., were
# silently creating two separate candidate rows before this fix.)


def test_url_shaped_candidate_ref_dedups_ignoring_tracking_params(tmp_path: Path) -> None:
    db_path = _db(tmp_path)
    first = record_candidate_observation(
        db_path,
        _input(
            channel="linkedin_rps",
            candidate_ref="https://www.linkedin.com/in/abc/?trk=test",
            ingestion_id="run-1",
        ),
    )
    second = record_candidate_observation(
        db_path,
        _input(
            channel="linkedin_rps",
            candidate_ref="https://www.linkedin.com/in/abc/?trk=other",
            ingestion_id="run-2",
        ),
    )
    assert first.candidate.candidate_id == second.candidate.candidate_id
    # raw evidence for each distinct URL variant must still be preserved verbatim
    assert first.candidate.candidate_ref_raw == "https://www.linkedin.com/in/abc/?trk=test"
    connection = sqlite3.connect(db_path)
    try:
        candidate_count = connection.execute("select count(*) from hs_candidates").fetchone()[0]
    finally:
        connection.close()
    assert candidate_count == 1


# --- LinkedIn profile URLs are case-insensitive and www-optional (Codex V1 finding F-2,
# 2026-09-17): the fix for tracking-param dedup did not also fold case or strip www. ---


def test_linkedin_url_dedups_across_case_and_www_prefix(tmp_path: Path) -> None:
    db_path = _db(tmp_path)
    variants = [
        "https://www.linkedin.com/in/JohnDoe/?trk=x",
        "https://www.linkedin.com/in/johndoe",
        "https://linkedin.com/in/johndoe",
    ]
    candidate_ids = {
        record_candidate_observation(
            db_path,
            _input(channel="linkedin_rps", candidate_ref=url, ingestion_id=f"run-{i}"),
        ).candidate.candidate_id
        for i, url in enumerate(variants)
    }
    assert len(candidate_ids) == 1


# --- a burst of concurrent writers for the same candidate must all succeed, not
# just avoid data corruption (Codex V1 finding F-1, 2026-09-17): the old retry
# budget (5 tries, ~0.75s total) let normal contention exhaust retries and lose
# observations outright, even though no row was ever corrupted or duplicated. ---


def test_forty_concurrent_writes_of_the_same_candidate_all_succeed(tmp_path: Path) -> None:
    db_path = _db(tmp_path)
    errors: list[BaseException] = []

    def _write(i: int) -> None:
        try:
            record_candidate_observation(db_path, _input(ingestion_id=f"burst-{i}"))
        except BaseException as exc:  # noqa: BLE001 -- collected for the assertion below
            errors.append(exc)

    threads = [threading.Thread(target=_write, args=(i,)) for i in range(40)]
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
    assert observation_count == 40


# --- a query-string identifier (e.g. saramin/jobkorea resume view links) must NOT be
# stripped like a tracking param (Codex V1 re-verification finding, 2026-09-17): the
# fix for F-2 normalized URLs by dropping the whole query string, which silently
# merged two different real candidates into one row and discarded the second
# person's identifying URL. ---


def test_query_string_identifier_is_preserved_not_treated_as_tracking(tmp_path: Path) -> None:
    db_path = _db(tmp_path)
    first = record_candidate_observation(
        db_path,
        _input(
            channel="saramin",
            candidate_ref="https://www.saramin.co.kr/zf_user/resume/view?rec_idx=39825930",
            ingestion_id="run-1",
        ),
    )
    second = record_candidate_observation(
        db_path,
        _input(
            channel="saramin",
            candidate_ref="https://www.saramin.co.kr/zf_user/resume/view?rec_idx=51002211",
            ingestion_id="run-2",
        ),
    )
    assert first.candidate.candidate_id != second.candidate.candidate_id
    assert second.outcome == "candidate_created"
    assert (
        second.candidate.candidate_ref_raw
        == "https://www.saramin.co.kr/zf_user/resume/view?rec_idx=51002211"
    )


def test_known_tracking_params_are_still_stripped_alongside_a_real_identifier(
    tmp_path: Path,
) -> None:
    """Tracking-param stripping only applies to an approved host (linkedin.com) —
    see the unapproved-host tests below for why saramin/jobkorea must NOT get this."""
    db_path = _db(tmp_path)
    first = record_candidate_observation(
        db_path,
        _input(
            channel="linkedin_rps",
            candidate_ref="https://www.linkedin.com/in/abc/?trk=email",
            ingestion_id="run-1",
        ),
    )
    second = record_candidate_observation(
        db_path,
        _input(
            channel="linkedin_rps",
            candidate_ref="https://www.linkedin.com/in/abc/?trk=push",
            ingestion_id="run-2",
        ),
    )
    assert first.candidate.candidate_id == second.candidate.candidate_id


def test_non_tracking_param_order_does_not_affect_dedup(tmp_path: Path) -> None:
    """Codex V1 3rd-round finding: the previous tracking-param test left only one
    non-tracking key after filtering, so a broken `sorted()` in `_normalize_query`
    would not have failed it. This uses two non-tracking keys in reversed order, on
    the one approved host where query normalization applies at all."""
    db_path = _db(tmp_path)
    first = record_candidate_observation(
        db_path,
        _input(
            channel="linkedin_rps",
            candidate_ref="https://www.linkedin.com/in/abc/?a=1&b=seoul&trk=a",
            ingestion_id="run-1",
        ),
    )
    second = record_candidate_observation(
        db_path,
        _input(
            channel="linkedin_rps",
            candidate_ref="https://www.linkedin.com/in/abc/?b=seoul&trk=b&a=1",
            ingestion_id="run-2",
        ),
    )
    assert first.candidate.candidate_id == second.candidate.candidate_id


# --- owner-directed scope narrowing (2026-09-17): a host with no verified
# equivalence rule must get NO query canonicalization at all, so an assumed
# "tracking" param can never cause a false merge on that host. ---


def test_unapproved_host_query_is_untouched_so_tracking_looking_params_still_split(
    tmp_path: Path,
) -> None:
    db_path = _db(tmp_path)
    first = record_candidate_observation(
        db_path,
        _input(
            channel="saramin",
            candidate_ref="https://www.saramin.co.kr/zf_user/resume/view?rec_idx=1&trk=email",
            ingestion_id="run-1",
        ),
    )
    second = record_candidate_observation(
        db_path,
        _input(
            channel="saramin",
            candidate_ref="https://www.saramin.co.kr/zf_user/resume/view?trk=push&rec_idx=1",
            ingestion_id="run-2",
        ),
    )
    # Not merged: on an unapproved host we cannot tell "trk" is noise, and the two
    # query strings differ verbatim (order and value both differ). A recoverable
    # duplicate is accepted here — the alternative (guessing wrong) is not.
    assert first.candidate.candidate_id != second.candidate.candidate_id


def test_unapproved_host_never_treats_a_tracking_style_name_as_a_real_identifier(
    tmp_path: Path,
) -> None:
    """A channel could legitimately use a name like "ref" as its own real per-
    candidate identifier. Because saramin is not an approved host, that value must
    survive untouched even though "ref" is on the LinkedIn tracking-param list."""
    db_path = _db(tmp_path)
    first = record_candidate_observation(
        db_path,
        _input(
            channel="saramin",
            candidate_ref="https://www.saramin.co.kr/zf_user/resume/view?ref=applicant-001",
            ingestion_id="run-1",
        ),
    )
    second = record_candidate_observation(
        db_path,
        _input(
            channel="saramin",
            candidate_ref="https://www.saramin.co.kr/zf_user/resume/view?ref=applicant-002",
            ingestion_id="run-2",
        ),
    )
    assert first.candidate.candidate_id != second.candidate.candidate_id
    assert second.candidate.candidate_ref_raw == (
        "https://www.saramin.co.kr/zf_user/resume/view?ref=applicant-002"
    )


def test_unapproved_host_fragment_is_preserved_not_dropped_like_a_tracking_param(
    tmp_path: Path,
) -> None:
    """Codex V1 4th-round finding, 2026-09-17: `_normalize_url` never referenced
    ``parts.fragment`` at all, so it was silently dropped for every host — the same
    class of bug as the query-string merge (F-1), just in the URL fragment (#...)
    instead. A site using fragment-based routing to identify a candidate would have
    two different real people merge on an unapproved host."""
    db_path = _db(tmp_path)
    first = record_candidate_observation(
        db_path,
        _input(
            channel="saramin",
            candidate_ref="https://www.saramin.co.kr/zf_user/resume/view#applicant-39825930",
            ingestion_id="run-1",
        ),
    )
    second = record_candidate_observation(
        db_path,
        _input(
            channel="saramin",
            candidate_ref="https://www.saramin.co.kr/zf_user/resume/view#applicant-51002211",
            ingestion_id="run-2",
        ),
    )
    assert first.candidate.candidate_id != second.candidate.candidate_id
    assert second.candidate.candidate_ref_raw == (
        "https://www.saramin.co.kr/zf_user/resume/view#applicant-51002211"
    )


def test_unapproved_host_trailing_slash_is_preserved_not_stripped(tmp_path: Path) -> None:
    """Codex V1 4th-round finding, 2026-09-17: the trailing-slash strip ran before
    the approval check, so an unapproved host still lost a path difference that
    could be a real identifier boundary."""
    db_path = _db(tmp_path)
    first = record_candidate_observation(
        db_path,
        _input(
            channel="saramin",
            candidate_ref="https://www.saramin.co.kr/zf_user/resume/view/applicant-1",
            ingestion_id="run-1",
        ),
    )
    second = record_candidate_observation(
        db_path,
        _input(
            channel="saramin",
            candidate_ref="https://www.saramin.co.kr/zf_user/resume/view/applicant-1/",
            ingestion_id="run-2",
        ),
    )
    assert first.candidate.candidate_id != second.candidate.candidate_id


def test_unapproved_host_userinfo_case_is_preserved(tmp_path: Path) -> None:
    """Codex V1 4th-round finding, 2026-09-17: lowercasing the whole netloc also
    lowercased URL userinfo (before the @), which is not a DNS-aliasing fact and
    could be a real identifier on a host we have not verified."""
    db_path = _db(tmp_path)
    first = record_candidate_observation(
        db_path,
        _input(
            channel="saramin",
            candidate_ref="https://Applicant-A@saramin.co.kr/x",
            ingestion_id="run-1",
        ),
    )
    second = record_candidate_observation(
        db_path,
        _input(
            channel="saramin",
            candidate_ref="https://applicant-a@saramin.co.kr/x",
            ingestion_id="run-2",
        ),
    )
    assert first.candidate.candidate_id != second.candidate.candidate_id


def test_unapproved_host_non_numeric_port_position_case_is_preserved(tmp_path: Path) -> None:
    """Codex V1 5th-round finding, 2026-09-17: `_normalized_netloc` lowercased the
    entire host:port tail, including whatever follows a ':' — even non-numeric text
    (urlsplit does not validate that a "port" is actually numeric). A malformed URL
    using that position to carry an identifier must not have it case-folded."""
    db_path = _db(tmp_path)
    first = record_candidate_observation(
        db_path,
        _input(
            channel="saramin",
            candidate_ref="https://unapproved.invalid:Applicant-A/candidate",
            ingestion_id="run-1",
        ),
    )
    second = record_candidate_observation(
        db_path,
        _input(
            channel="saramin",
            candidate_ref="https://unapproved.invalid:applicant-a/candidate",
            ingestion_id="run-2",
        ),
    )
    assert first.candidate.candidate_id != second.candidate.candidate_id


def test_unapproved_host_www_prefix_is_not_assumed_equivalent_to_apex(tmp_path: Path) -> None:
    """Owner-directed narrowing, round 6 (2026-09-17, via external review): scheme
    and host case-folding are RFC 3986 syntax facts (the spec defines them as
    case-insensitive), but "www.X and X are the same host" is a DNS/CNAME
    convention, not a URI-syntax fact — treating them as equivalent for a channel
    nobody has verified is a business identity call this codebase must not make
    unilaterally. Only the approved host (linkedin.com) gets that assumption."""
    db_path = _db(tmp_path)
    first = record_candidate_observation(
        db_path,
        _input(
            channel="saramin",
            candidate_ref="https://www.unapproved.invalid/candidate/42",
            ingestion_id="run-1",
        ),
    )
    second = record_candidate_observation(
        db_path,
        _input(
            channel="saramin",
            candidate_ref="https://unapproved.invalid/candidate/42",
            ingestion_id="run-2",
        ),
    )
    assert first.candidate.candidate_id != second.candidate.candidate_id


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
