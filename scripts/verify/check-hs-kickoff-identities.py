"""Reject Unicode disguises of protected HumanSearch kickoff identifiers."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DATA = Path(__file__).with_name("hs-kickoff-confusables-17.0.0.json")
EXPECTED_DATA_SHA256 = "687cd7d5f774002d92a2f994599d614fd08d7d85287ce3a3030c4ef84cd0cdfd"
EXPECTED_SOURCE_SHA256 = "091c7f82fc39ef208faf8f94d29c244de99254675e09de163160c810d13ef22a"
EXPECTED_MAPPING_COUNT = 628
EXPECTED_PROTECTED_ASCII = "#-/1345PRabcdefhiklmnoprstuvx"
EXPECTED_TOKENS = (
    "hs-kickoff",
    "hs-kickoff-mutations",
    "PR #13",
    "PR #54",
    "PR #15",
    "task/hs-d1-permit",
    "task/hs-l1-malformed-url-fix",
    "task/hs-observe-url-crash",
)
EXPECTED_METADATA = {
    "source_url": "https://www.unicode.org/Public/17.0.0/security/confusables.txt",
    "source_version": "17.0.0",
    "source_date": "2025-07-22, 05:49:37 GMT",
    "source_sha256": EXPECTED_SOURCE_SHA256,
    "license": "Unicode License v3",
    "license_url": "https://www.unicode.org/license.txt",
    "selection_rule": (
        "single non-ASCII source code point to a single protected ASCII target; "
        "ASCII sources, U+FF01..U+FF5E, and multi-character targets are excluded"
    ),
}
BOUNDARY = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_./-")
CODEPOINT_RE = re.compile(r"[0-9A-F]{4,6}")


@dataclass(frozen=True)
class Shadow:
    text: str
    changed: tuple[bool, ...]


def data_error(message: str) -> int:
    print(f"ERROR: Unicode 매핑 데이터 {message}", file=sys.stderr)
    return 2


def input_error(message: str) -> int:
    print(f"ERROR: 입력 {message}", file=sys.stderr)
    return 2


def read_document() -> Any:
    try:
        body = DATA.read_bytes()
    except OSError as exc:
        raise ValueError(f"읽기 실패: {exc}") from exc
    digest = hashlib.sha256(body).hexdigest()
    if digest != EXPECTED_DATA_SHA256:
        raise ValueError(f"파일 sha256 불일치: {digest}")
    try:
        return json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"JSON 파싱 실패: {exc}") from exc


def validate_header(document: Any) -> dict[str, list[str]]:
    if not isinstance(document, dict):
        raise TypeError("최상위 객체 아님")
    metadata = document.get("metadata")
    selection = document.get("selection")
    groups = document.get("confusables")
    if metadata != EXPECTED_METADATA:
        raise ValueError("metadata 계약 불일치")
    if not isinstance(selection, dict) or not isinstance(groups, dict):
        raise TypeError("selection/confusables 객체 없음")
    if selection.get("protected_tokens") != list(EXPECTED_TOKENS):
        raise ValueError("protected_tokens 불일치")
    if selection.get("protected_ascii") != EXPECTED_PROTECTED_ASCII:
        raise ValueError("protected_ascii 불일치")
    if selection.get("mapping_count") != EXPECTED_MAPPING_COUNT:
        raise ValueError("mapping_count 불일치")
    return groups


def build_mapping(groups: dict[str, list[str]]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for target, codepoints in groups.items():
        if len(target) != 1 or target not in EXPECTED_PROTECTED_ASCII:
            raise ValueError("target 계약 위반")
        if not isinstance(codepoints, list) or not codepoints:
            raise ValueError("codepoint 목록 비어 있음")
        for raw_codepoint in codepoints:
            if not isinstance(raw_codepoint, str) or CODEPOINT_RE.fullmatch(raw_codepoint) is None:
                raise ValueError("codepoint 형식 오류")
            try:
                source = chr(int(raw_codepoint, 16))
            except ValueError as exc:
                raise ValueError("codepoint 범위 오류") from exc
            if ord(source) <= 0x7F or source in mapping:
                raise ValueError("source 계약 위반")
            mapping[source] = target
    if len(mapping) != EXPECTED_MAPPING_COUNT:
        raise ValueError("실제 매핑 수 불일치")
    return mapping


def load_confusables() -> dict[str, str]:
    return build_mapping(validate_header(read_document()))


def make_shadow(value: str, mapping: dict[str, str]) -> Shadow:
    chars: list[str] = []
    changed: list[bool] = []
    for char in value:
        codepoint = ord(char)
        if 0xFF01 <= codepoint <= 0xFF5E:
            chars.append(chr(codepoint - 0xFEE0))
            changed.append(True)
        elif char in mapping:
            chars.append(mapping[char])
            changed.append(True)
        else:
            chars.append(char)
            changed.append(False)
    return Shadow("".join(chars), tuple(changed))


def has_token_boundary(text: str, start: int, end: int) -> bool:
    before = text[start - 1] if start else ""
    after = text[end] if end < len(text) else ""
    return (not before or before not in BOUNDARY) and (not after or after not in BOUNDARY)


def has_confusable_boundary(shadow: Shadow, start: int, end: int) -> bool:
    before = start > 0 and shadow.changed[start - 1] and shadow.text[start - 1] in BOUNDARY
    after = end < len(shadow.text) and shadow.changed[end] and shadow.text[end] in BOUNDARY
    return before or after


def spoofed_tokens(value: str, tokens: list[str], mapping: dict[str, str]) -> list[str]:
    shadow = make_shadow(value, mapping)
    hits: list[str] = []
    for token in tokens:
        start = shadow.text.find(token)
        while start != -1:
            end = start + len(token)
            changed_token = has_token_boundary(shadow.text, start, end) and any(
                shadow.changed[start:end]
            )
            if changed_token or has_confusable_boundary(shadow, start, end):
                hits.append(token)
                break
            start = shadow.text.find(token, start + 1)
    return hits


def validate_tokens(tokens: list[str]) -> None:
    for token in tokens:
        if token not in EXPECTED_TOKENS:
            raise ValueError(f"지원하지 않는 보호 토큰: {token!r}")
        if any(char != " " and char not in EXPECTED_PROTECTED_ASCII for char in token):
            raise ValueError(f"보호 ASCII 집합 밖 토큰: {token!r}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--kind",
        required=True,
        choices=("workflow-step", "sot-step", "disposition-target"),
    )
    parser.add_argument("--token", action="append", required=True)
    return parser.parse_args()


def read_input_lines() -> list[str]:
    try:
        body = sys.stdin.buffer.read()
    except OSError as exc:
        raise ValueError(f"읽기 실패: {exc}") from exc
    try:
        text = body.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"UTF-8 해독 실패: {exc}") from exc
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    if not lines or not any(line.strip() for line in lines):
        raise ValueError("이름 줄 없음")
    return lines


def main() -> int:
    args = parse_args()
    try:
        validate_tokens(args.token)
        mapping = load_confusables()
    except (TypeError, ValueError) as exc:
        return data_error(str(exc))
    try:
        lines = read_input_lines()
    except ValueError as exc:
        return input_error(str(exc))
    failed = False
    for line_number, line in enumerate(lines, 1):
        for token in spoofed_tokens(line, args.token, mapping):
            print(f"SPOOF: {args.kind} line={line_number} token={token}")
            failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
