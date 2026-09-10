"""HS-13.10 — `python -m humansearch.brief verify` 가 readback 본문 해시로 발송을 검증하는가.

계약: docs/engineering/humansearch-hs13-position-brief-goal-2026-09-10.md
      §5 __main__.py(HS-13.10 소유 — 유일한 CLI) · §9 HS-13.10 카드 · §10 러너 절차 5단계.
발송·네트워크·시계 접근은 이 모듈에 없다 — 두 파일(패킷 JSON·readback 평문)을 비교하는
순수 판정만 시험한다. 합성 `SearchPacket` 은 `test_hs_1309.py` 의 빌더 구조를 그대로 복제한다
(다른 시험 파일을 import 해 결합을 만들지 않는다).
"""

from __future__ import annotations

import hashlib
import os
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

from humansearch.brief import (
    CandidateEvidence,
    CandidateLead,
    Claim,
    CompanyBrief,
    ConnectionDegree,
    EmailContact,
    JdPacket,
    JdSource,
    PositionSpec,
    ScoreBreakdown,
    SearchPacket,
    SourceRef,
    TeamMail,
    to_json,
)
from humansearch.brief.cli import verify

# --- 합성 패킷 (test_hs_1309.py 의 빌더 구조를 복제) --------------------------

_JD_TEXT = "직무: 백엔드 엔지니어\n요구: 분산 시스템 경험 3년"
_RAW_SHA = hashlib.sha256(_JD_TEXT.encode("utf-8")).hexdigest()
_CLICKUP = "77a2bcde"
_TODAY = date(2026, 9, 10)
_PACKET_ID = f"{_CLICKUP}-{_RAW_SHA[:8]}"
_LEAD_URL = "https://www.linkedin.com/in/example-lead"

_VERIFIED_RE = re.compile(r"^VERIFIED packet_id=(\S+) body_sha256=([0-9a-f]{64})$")
_UNVERIFIED_RE = re.compile(
    r"^SENT_UNVERIFIED packet_id=(\S+) expected=([0-9a-f]{64}) actual=([0-9a-f]{64})$"
)

_SRC_DIR = Path(__file__).resolve().parent.parent / "src"


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _packet(body: str) -> SearchPacket:
    return SearchPacket(
        packet_id=_PACKET_ID,
        created_on=_TODAY,
        position=PositionSpec(
            _CLICKUP, "예시 고객사", "백엔드 엔지니어", None, "정규직", "서울", None
        ),
        jd=JdSource(_JD_TEXT, _RAW_SHA, "U1"),
        company=CompanyBrief(
            legal_name=Claim("예시 주식회사", ("C1",)),
            sources=(SourceRef("C1", "https://example.com/about", "회사 소개", _TODAY),),
        ),
        jd_packet=JdPacket("gmail 본문", "링크드인 본문", "회사 소개 필드", "JD 본문 필드"),
        candidates=(
            CandidateLead(
                display_name="예시 후보",
                headline="백엔드 엔지니어",
                linkedin_url=_LEAD_URL,
                education="예시대학원 석사",
                career="예시사 3년",
                match_reasons=("분산 시스템 경험",),
                check_points=("도메인 적합성",),
                evidence=CandidateEvidence(
                    ("분산시스템",), 1, 2, "석사", 2, (24, 18), 2, 8, 10
                ),
                score=ScoreBreakdown(30, 15, 15, 15),
                email=EmailContact(
                    "lead@example.org", "https://example.org/lab", "연구실 페이지"
                ),
                degree=ConnectionDegree.SECOND,
                source_note="공개 프로필 URL 일치",
            ),
        ),
        mail=TeamMail(
            subject="[포지션]예시 고객사, 백엔드 엔지니어",
            to=("sangmokang@valueconnect.kr",),
            cc=(),
            body=body,
            body_sha256=_sha256(body),
        ),
        boolean_queries=('("Backend Engineer" OR 백엔드) AND 분산시스템',),
        inmails=((_LEAD_URL, "안녕하세요, 포지션을 제안드립니다."),),
    )


_BODY = "고객사 백엔드 엔지니어 | 밸류커넥트 내부 공유\n본문 둘째 줄\n본문 셋째 줄"


def _write_packet(tmp_path: Path, body: str = _BODY) -> Path:
    path = tmp_path / "packet.json"
    path.write_text(to_json(_packet(body)), encoding="utf-8")
    return path


def _write_sent(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "sent.txt"
    path.write_bytes(text.encode("utf-8"))
    return path


# --- 1. 양성 — 본문 그대로 ----------------------------------------------------


def test_verify_positive_exact_body_matches(tmp_path: Path) -> None:
    packet_path = _write_packet(tmp_path)
    sent_path = _write_sent(tmp_path, _BODY)
    code, message = verify(packet_path, sent_path)
    assert code == 0
    match = _VERIFIED_RE.fullmatch(message)
    assert match is not None
    assert match.group(1) == _PACKET_ID
    assert match.group(2) == _sha256(_BODY)


# --- 2. 양성 — CRLF 정규화 후에도 일치 ----------------------------------------


def test_verify_positive_survives_crlf_normalization(tmp_path: Path) -> None:
    packet_path = _write_packet(tmp_path)
    sent_path = _write_sent(tmp_path, _BODY.replace("\n", "\r\n"))
    code, message = verify(packet_path, sent_path)
    assert code == 0
    assert _VERIFIED_RE.fullmatch(message) is not None


# --- 3. 양성 — 줄 끝 후행 공백이 있어도 일치 ----------------------------------


def test_verify_positive_survives_trailing_whitespace(tmp_path: Path) -> None:
    packet_path = _write_packet(tmp_path)
    padded = "\n".join(f"{line}   " for line in _BODY.split("\n")) + "  \n\n"
    sent_path = _write_sent(tmp_path, padded)
    code, message = verify(packet_path, sent_path)
    assert code == 0
    assert _VERIFIED_RE.fullmatch(message) is not None


# --- 4. 양성 — §10 ③ packet-id 꼬리 줄이 있어도 일치 --------------------------


def test_verify_positive_survives_packet_id_trailer_line(tmp_path: Path) -> None:
    packet_path = _write_packet(tmp_path)
    sent_path = _write_sent(tmp_path, f"{_BODY}\npacket-id: {_PACKET_ID}")
    code, message = verify(packet_path, sent_path)
    assert code == 0
    assert _VERIFIED_RE.fullmatch(message) is not None


# --- 5. 음성 — 한 글자 변경 → 불일치 ------------------------------------------


def test_verify_negative_single_char_change_reports_both_hashes(tmp_path: Path) -> None:
    packet_path = _write_packet(tmp_path)
    tampered = _BODY.replace("둘째", "넷째")
    sent_path = _write_sent(tmp_path, tampered)
    code, message = verify(packet_path, sent_path)
    assert code == 1
    match = _UNVERIFIED_RE.fullmatch(message)
    assert match is not None
    assert match.group(1) == _PACKET_ID
    expected, actual = match.group(2), match.group(3)
    assert expected == _sha256(_BODY)
    assert actual == _sha256(tampered)
    assert expected != actual


# --- 6. 음성 — 패킷 파일 없음/손상 → exit 2 -----------------------------------


def test_verify_missing_packet_file_exits_2(tmp_path: Path) -> None:
    sent_path = _write_sent(tmp_path, _BODY)
    code, message = verify(tmp_path / "no-such-packet.json", sent_path)
    assert code == 2
    assert message.strip() != ""


def test_verify_corrupted_packet_file_exits_2(tmp_path: Path) -> None:
    packet_path = tmp_path / "packet.json"
    packet_path.write_text("{이건 JSON 이 아니다", encoding="utf-8")
    sent_path = _write_sent(tmp_path, _BODY)
    code, message = verify(packet_path, sent_path)
    assert code == 2
    assert message.strip() != ""


# --- 7. 음성 — readback 파일 없음 → exit 2 ------------------------------------


def test_verify_missing_sent_file_exits_2(tmp_path: Path) -> None:
    packet_path = _write_packet(tmp_path)
    code, message = verify(packet_path, tmp_path / "no-such-sent.txt")
    assert code == 2
    assert message.strip() != ""


# --- 8. 실제 진입점 — 양성 subprocess ----------------------------------------


def _run_module(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    existing = env.get("PYTHONPATH")
    env["PYTHONPATH"] = str(_SRC_DIR) if not existing else f"{_SRC_DIR}{os.pathsep}{existing}"
    return subprocess.run(
        [sys.executable, "-m", "humansearch.brief", *args],
        cwd=str(cwd),
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )


def test_cli_entrypoint_positive(tmp_path: Path) -> None:
    packet_path = _write_packet(tmp_path)
    sent_path = _write_sent(tmp_path, _BODY)
    result = _run_module(
        ["verify", "--packet", str(packet_path), "--sent", str(sent_path)], tmp_path
    )
    assert result.returncode == 0, result.stderr
    assert _VERIFIED_RE.fullmatch(result.stdout.strip()) is not None
    assert result.stderr == ""


# --- 9. 실제 진입점 — 잘못된 하위 명령 → exit 2 -------------------------------


def test_cli_entrypoint_invalid_subcommand_exits_2(tmp_path: Path) -> None:
    result = _run_module(["bogus"], tmp_path)
    assert result.returncode == 2
    assert result.stdout == ""


# --- 10. 정적 — 발송·네트워크·시계 API 0건 ------------------------------------


def test_cli_modules_have_no_send_network_or_clock_access() -> None:
    brief_dir = Path(__file__).resolve().parent.parent / "src" / "humansearch" / "brief"
    forbidden = ("smtplib", "requests", "datetime.now(")
    for name in ("__main__.py", "cli.py"):
        text = (brief_dir / name).read_text(encoding="utf-8")
        for token in forbidden:
            assert token not in text, f"{name} 에 금지된 토큰이 있다: {token}"
