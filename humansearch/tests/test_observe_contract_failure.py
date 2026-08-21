from pathlib import Path

import pytest

from humansearch import observe


def test_non_utf8_contract_is_a_closed_observation_failure(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    contract_path = tmp_path / "saramin-markers.json"
    contract_path.write_bytes(bytes((255,)))
    monkeypatch.setattr(observe, "_CONTRACT_PATH", contract_path)

    with pytest.raises(observe.ObservationError, match="marker contract"):
        observe._load_contract("saramin")
