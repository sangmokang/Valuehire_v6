"""HS-03.02 3차 RED — Codex V1 2차가 낸 잔여·신규 결함을 닫는다.

판정 원문: V1 2차 (3061bd3, 2026-09-15).
  1 [high]   F0302-2 잔여 — DB 파일 자체의 symlink 로 키 경계를 우회한다
  2 [high]   신규 — 인수 스크립트가 CI 고정 목록·정본 명부에 배선돼 있지 않다
  3 [medium] F0302-4 잔여 — tests/test_hs_0302_acceptance_probe.py 로 분리해 다룬다
  4 [medium] 신규 — 유니코드 정규화 차이로 같은 후보가 두 행이 된다

시험 데이터는 전부 합성이다. 실명·이력서 원문·실제 키를 쓰지 않는다.
"""

from __future__ import annotations

import hmac
import importlib
import sqlite3
import unicodedata
from pathlib import Path
from types import ModuleType

import pytest

from humansearch.storage_schema import initialize_humansearch_storage

_MODULE_NAME = "humansearch.candidate_identity"
_REQUIRED_NAMES = (
    "CandidateIdentityInput",
    "CandidateIdentityError",
    "record_candidate_identity",
    "candidate_key_hmac",
)
_TEST_KEY = bytes(range(32))
_OBSERVED_AT = "2026-09-15T10:00:00Z"
_KEY_BASENAME = "hs-candidate.key"
_DB_BASENAME = "humansearch.sqlite3"
_ACCEPTANCE_RUN = "bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-0302.sh"

# 같은 후보다 — 결합형 é 와 분해형 e+U+0301. NFC 에서 같아진다.
_NFC_PAIR = ("café", "café")
# 서로 다른 후보다 — NFKC 에서만 같아지는 호환문자. 합치면 오병합이다.
_NFKC_ONLY_PAIRS = [("①", "1"), ("Ａ", "A")]


def _load_identity_module() -> ModuleType:
    module: ModuleType | None
    try:
        module = importlib.import_module(_MODULE_NAME)
    except ModuleNotFoundError:
        module = None
    if module is None:
        pytest.fail(f"record function missing: {_MODULE_NAME}")
    missing = [name for name in _REQUIRED_NAMES if not hasattr(module, name)]
    if missing:
        pytest.fail(f"record function missing: {_MODULE_NAME}.{'/'.join(missing)}")
    return module


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _assert_tmp_is_symlink_free(tmp_path: Path) -> None:
    assert tmp_path.resolve(strict=True) == tmp_path, (
        "pytest tmp_path 에 symlink 구성요소가 있다 — 경로 시험의 전제가 깨졌다"
    )


def _key_at(directory: Path, *, key: bytes = _TEST_KEY) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / _KEY_BASENAME
    path.write_bytes(key)
    path.chmod(0o600)
    directory.chmod(0o700)
    return path


def _record(
    identity: ModuleType,
    db_path: Path,
    key_path: Path,
    *,
    position_ref: str = "POS-1",
    channel: str = "saramin",
    candidate_ref: str = "cand-1",
    observed_at: str = _OBSERVED_AT,
) -> str:
    record = identity.CandidateIdentityInput(
        position_ref=position_ref,
        channel=channel,
        candidate_ref=candidate_ref,
        observed_at=observed_at,
    )
    return str(identity.record_candidate_identity(db_path, record, hmac_key_path=key_path))


def _independent_key_hmac(position_ref: str, channel: str, candidate_ref: str) -> str:
    """계약 문구만으로 다시 계산한다 — 길이 접두 정규 직렬화, 도메인 v2.

    정규화는 여기서 하지 않는다. 기록 경로가 strip + NFC 를 한 뒤 이 직렬화를 부르므로,
    저장값과 대조할 때는 호출하는 쪽이 정규화한 값을 넘긴다.
    """

    message = b"hs-candidate-key-v2"
    for field in (position_ref, channel, candidate_ref):
        raw = field.encode("utf-8")
        message += len(raw).to_bytes(4, "big") + raw
    return hmac.new(_TEST_KEY, message, "sha256").hexdigest()


def _nfc(value: str) -> str:
    return unicodedata.normalize("NFC", value)


def _count_rows(db_path: Path) -> int:
    with sqlite3.connect(db_path) as connection:
        row = connection.execute("select count(*) from hs_candidates").fetchone()
    return int(row[0])


def _has_key(db_path: Path, key: str) -> bool:
    with sqlite3.connect(db_path) as connection:
        row = connection.execute(
            "select 1 from hs_candidates where candidate_key_hmac = ?", (key,)
        ).fetchone()
    return row is not None


# ── 결함 1 [high] DB 경로 symlink 로 키 경계 우회 ────────────────────────────


def test_db_file_symlink_into_key_root_is_refused(tmp_path: Path) -> None:
    """DB 파일 마지막 구성요소가 symlink 면 비교한 경로와 실제로 여는 파일이 갈라진다.

    alias 디렉터리의 DB 링크가 키 디렉터리 안 실제 DB 를 가리키면, 경계 비교는 alias 를
    보고 통과하지만 쓰기는 키와 같은 루트에 도달한다. 한 번의 복사로 DB 와 키가 함께 샌다.
    """

    identity = _load_identity_module()
    _assert_tmp_is_symlink_free(tmp_path)
    key_root = tmp_path / "key-root"
    key_root.mkdir(mode=0o700)
    real = initialize_humansearch_storage(key_root / "realdb")
    key_path = key_root / _KEY_BASENAME
    key_path.write_bytes(_TEST_KEY)
    key_path.chmod(0o600)
    key_root.chmod(0o700)
    alias = tmp_path / "alias"
    alias.mkdir(mode=0o700)
    aliased_db = alias / _DB_BASENAME
    aliased_db.symlink_to(real.db_path)

    with pytest.raises(identity.CandidateIdentityError):
        _record(identity, aliased_db, key_path)

    assert _count_rows(real.db_path) == 0


def test_db_ancestor_symlink_is_refused(tmp_path: Path) -> None:
    """DB 경로 조상이 symlink 여도 거부한다 — 검사한 경로와 연 파일이 같아야 한다."""

    identity = _load_identity_module()
    _assert_tmp_is_symlink_free(tmp_path)
    real_root = tmp_path / "real-db-root"
    real_root.mkdir(mode=0o700)
    result = initialize_humansearch_storage(real_root / "protected-root")
    key_path = _key_at(tmp_path / "key-root")
    linked_root = tmp_path / "linked-db-root"
    linked_root.symlink_to(real_root, target_is_directory=True)

    with pytest.raises(identity.CandidateIdentityError):
        _record(identity, linked_root / "protected-root" / _DB_BASENAME, key_path)

    assert _count_rows(result.db_path) == 0


def test_plain_db_path_still_records(tmp_path: Path) -> None:
    """양성 대조군 — 링크 없는 평범한 DB 경로는 그대로 기록된다."""

    identity = _load_identity_module()
    _assert_tmp_is_symlink_free(tmp_path)
    db_path = initialize_humansearch_storage(tmp_path / "protected-root").db_path
    key_path = _key_at(tmp_path / "key-root")

    assert _record(identity, db_path, key_path) == "inserted"
    assert _count_rows(db_path) == 1


# ── 결함 4 [medium] 유니코드 정규화 ─────────────────────────────────────────


@pytest.mark.parametrize("field", ["position_ref", "candidate_ref"])
def test_nfc_equivalent_fields_collapse_into_one_row(tmp_path: Path, field: str) -> None:
    """결합형과 분해형은 같은 후보다 — 행이 하나만 남아야 한다."""

    identity = _load_identity_module()
    _assert_tmp_is_symlink_free(tmp_path)
    db_path = initialize_humansearch_storage(tmp_path / "protected-root").db_path
    key_path = _key_at(tmp_path / "key-root")

    composed = {"position_ref": "POS-1", "candidate_ref": "cand-1"}
    decomposed = dict(composed)
    composed[field] = _NFC_PAIR[0]
    decomposed[field] = _NFC_PAIR[1]

    first = _record(identity, db_path, key_path, **composed)
    second = _record(identity, db_path, key_path, **decomposed)

    assert (first, second) == ("inserted", "duplicate")
    assert _count_rows(db_path) == 1
    expected = _independent_key_hmac(
        _nfc(composed["position_ref"]), "saramin", _nfc(composed["candidate_ref"])
    )
    assert _has_key(db_path, expected), "저장된 키가 NFC 정규화 뒤 계약 계산과 다르다"


@pytest.mark.parametrize(("left", "right"), _NFKC_ONLY_PAIRS)
def test_nfkc_only_equivalents_stay_separate_rows(tmp_path: Path, left: str, right: str) -> None:
    """NFKC 에서만 같아지는 호환문자는 다른 후보다 — 합치면 오병합이다."""

    identity = _load_identity_module()
    _assert_tmp_is_symlink_free(tmp_path)
    db_path = initialize_humansearch_storage(tmp_path / "protected-root").db_path
    key_path = _key_at(tmp_path / "key-root")

    first = _record(identity, db_path, key_path, candidate_ref=f"cand-{left}")
    second = _record(identity, db_path, key_path, candidate_ref=f"cand-{right}")

    assert (first, second) == ("inserted", "inserted")
    assert _count_rows(db_path) == 2
    assert unicodedata.normalize("NFKC", left) == unicodedata.normalize("NFKC", right), (
        "이 쌍이 NFKC 에서 같지 않으면 오병합 시험이 성립하지 않는다"
    )


def test_surrounding_whitespace_is_stripped_before_normalisation(tmp_path: Path) -> None:
    """strip 뒤 NFC 라는 순서를 고정한다 — 앞뒤 공백이 다른 같은 후보는 한 행이다."""

    identity = _load_identity_module()
    _assert_tmp_is_symlink_free(tmp_path)
    db_path = initialize_humansearch_storage(tmp_path / "protected-root").db_path
    key_path = _key_at(tmp_path / "key-root")

    first = _record(identity, db_path, key_path, candidate_ref=_NFC_PAIR[0])
    second = _record(identity, db_path, key_path, candidate_ref=f"  {_NFC_PAIR[1]}  ")

    assert (first, second) == ("inserted", "duplicate")
    assert _count_rows(db_path) == 1


# ── 결함 2 [high] CI 배선 ───────────────────────────────────────────────────


def _workflow_text() -> str:
    return (_repo_root() / ".github/workflows/verify.yml").read_text(encoding="utf-8")


def test_acceptance_script_runs_as_its_own_ci_step() -> None:
    """정본 53행 — 새 acceptance-*.sh 는 verify.yml 에 자기 줄을 넣어야 한다.

    로컬 pre-push 는 글로브로 전량 실행하지만 CI 는 고정 목록이다. 여기 없으면
    '로컬에만 있는 검사'가 되고 P15③ 은 그것을 없는 것으로 친다.
    """

    assert _ACCEPTANCE_RUN in _workflow_text(), "CI 고정 목록에 이 인수 검사가 없다"


def test_acceptance_script_is_listed_in_the_verification_sot() -> None:
    """정본 53행 — 명부에도 같은 PR 에서 자기 줄이 들어가야 한다."""

    roster = (_repo_root() / "docs/sot/verification-commands.md").read_text(encoding="utf-8")

    assert "acceptance-hs-0302.sh" in roster, "검증 명부에 이 인수 검사가 없다"


def test_ci_step_is_not_conditional_or_error_suppressed() -> None:
    """스텝이 있어도 조건부거나 오류무시면 꺼진 것과 같다."""

    lines = _workflow_text().splitlines()
    run_at = [index for index, line in enumerate(lines) if _ACCEPTANCE_RUN in line]
    assert run_at, "CI 고정 목록에 이 인수 검사가 없다"

    start = run_at[0]
    while start > 0 and "- name:" not in lines[start]:
        start -= 1
    end = run_at[0] + 1
    while end < len(lines) and "- name:" not in lines[end]:
        end += 1
    block = "\n".join(lines[start:end])

    assert "if:" not in block, f"조건부 스텝이다:\n{block}"
    assert "continue-on-error" not in block, f"오류를 무시한다:\n{block}"
    assert "echo " not in block, f"실행을 echo 로 대체했다:\n{block}"
