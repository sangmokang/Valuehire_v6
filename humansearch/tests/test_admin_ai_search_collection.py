"""Read-only collection must be exhaustive, restartable and idempotent."""

import sqlite3
from pathlib import Path
from typing import cast

import pytest

from humansearch.admin_ai_search.collection import CollectionStore, collect_mailbox


class Mailbox:
    def __init__(self) -> None:
        self.fail = False
        self.requests: list[tuple[str, str | None]] = []

    def request(self, operation: str, args: dict[str, object]) -> object:
        if operation == "labels":
            return {"labels": [{"id": "label-live", "name": "02aisearch"}]}
        if operation == "list":
            scope = str(args["label_id"])
            token = cast(str | None, args.get("page_token"))
            self.requests.append((scope, str(token) if token else None))
            if self.fail and token:
                raise RuntimeError("temporary read failure")
            ids, next_token = {
                ("label-live", None): (["a", "b"], None),
                ("INBOX", None): (["b", "c"], "page-2"),
                ("INBOX", "page-2"): (["d"], None),
            }[(scope, token)]
            return {"messages": [{"id": i} for i in ids], "nextPageToken": next_token}
        if operation == "messages":
            return [
                {"id": i, "threadId": i, "internalDate": "1793156400000",
                 "labelIds": [], "snippet": "ordinary mail",
                 "payload": {"mimeType": "text/plain", "headers": [],
                             "body": {"data": "aGVsbG8="}}}
                for i in cast(list[str], args["ids"])
            ]
        raise AssertionError(operation)


def test_union_ends_both_paginations_and_upserts_without_duplicates(tmp_path: Path) -> None:
    store = CollectionStore(tmp_path / "private.sqlite")
    mailbox = Mailbox()
    first = collect_mailbox(store, mailbox)
    second = collect_mailbox(store, mailbox)
    assert first["status"] == second["status"] == "SUCCEEDED"
    assert first["scopes"]["INBOX"]["pages"] == 2
    assert first["scopes"]["02aisearch"]["pages"] == 1
    assert first["union_count"] == 4
    assert first["overlap_count"] == 1
    assert all(s["exhausted"] for s in first["scopes"].values())
    assert second["new"] == 0
    assert second["unchanged"] == 4
    with sqlite3.connect(store.path) as db:
        assert db.execute("SELECT count(*) FROM source_messages").fetchone() == (4,)


def test_failed_page_resumes_checkpoint_instead_of_claiming_success(tmp_path: Path) -> None:
    store = CollectionStore(tmp_path / "private.sqlite")
    mailbox = Mailbox()
    mailbox.fail = True
    with pytest.raises(RuntimeError, match="temporary read failure"):
        collect_mailbox(store, mailbox, run_id="resume-me")
    mailbox.fail = False
    mailbox.requests.clear()
    resumed = collect_mailbox(store, mailbox, run_id="resume-me")
    assert resumed["status"] == "SUCCEEDED"
    assert mailbox.requests == [("INBOX", "page-2")]
    assert resumed["union_count"] == 4
    assert resumed["errors"][0]["message"] == "temporary read failure"
    assert resumed["attempt_count"] == 2


def test_missing_live_label_fails_closed(tmp_path: Path) -> None:
    class Missing(Mailbox):
        def request(self, operation: str, args: dict[str, object]) -> object:
            if operation == "labels":
                return {"labels": []}
            return super().request(operation, args)

    with pytest.raises(ValueError, match="02aisearch"):
        collect_mailbox(CollectionStore(tmp_path / "private.sqlite"), Missing())


def test_resume_retains_the_listed_page_when_body_download_is_interrupted(tmp_path: Path) -> None:
    class Interrupted(Mailbox):
        body_failure = True

        def request(self, operation: str, args: dict[str, object]) -> object:
            if operation == "messages" and self.body_failure:
                raise RuntimeError("body download interrupted")
            return super().request(operation, args)

    store = CollectionStore(tmp_path / "private.sqlite")
    mailbox = Interrupted()
    with pytest.raises(RuntimeError, match="body download interrupted"):
        collect_mailbox(store, mailbox, run_id="body-resume")
    mailbox.body_failure = False
    mailbox.requests.clear()
    result = collect_mailbox(store, mailbox, run_id="body-resume")
    assert ("label-live", None) not in mailbox.requests
    assert result["union_count"] == 4
