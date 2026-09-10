"""Generate the pinned confusable subset used by HS kickoff checks."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

VERSION = "17.0.0"
DATE = "2025-07-22, 05:49:37 GMT"
SOURCE_URL = "https://www.unicode.org/Public/17.0.0/security/confusables.txt"
SOURCE_SHA256 = "091c7f82fc39ef208faf8f94d29c244de99254675e09de163160c810d13ef22a"
LICENSE_URL = "https://www.unicode.org/license.txt"
EXPECTED_MAPPING_COUNT = 628
PROTECTED_TOKENS = (
    "hs-kickoff",
    "hs-kickoff-mutations",
    "PR #13",
    "PR #54",
    "PR #15",
    "task/hs-d1-permit",
    "task/hs-l1-malformed-url-fix",
    "task/hs-observe-url-crash",
)
LINE_RE = re.compile(r"^([0-9A-F ]+)\s*;\s*([0-9A-F ]+)\s*;\s*MA\s*#")


def protected_ascii() -> str:
    return "".join(sorted({char for token in PROTECTED_TOKENS for char in token if char != " "}))


def parse_codepoints(raw: str) -> list[int]:
    return [int(part, 16) for part in raw.split()]


def validate_source(path: Path) -> str:
    body = path.read_bytes()
    digest = hashlib.sha256(body).hexdigest()
    if digest != SOURCE_SHA256:
        raise SystemExit(f"source sha256 mismatch: expected {SOURCE_SHA256} actual {digest}")
    text = body.decode("utf-8")
    if f"# Version: {VERSION}" not in text or f"# Date: {DATE}" not in text:
        raise SystemExit("source header does not match pinned Unicode 17.0.0 metadata")
    return text


def build_groups(text: str) -> dict[str, list[str]]:
    protected = set(protected_ascii())
    groups: dict[str, set[str]] = {char: set() for char in protected}
    for line in text.splitlines():
        match = LINE_RE.match(line)
        if not match:
            continue
        source = parse_codepoints(match.group(1))
        target = parse_codepoints(match.group(2))
        if len(source) != 1 or len(target) != 1:
            continue
        source_cp = source[0]
        target_char = chr(target[0])
        if source_cp > 0x7F and not 0xFF01 <= source_cp <= 0xFF5E and target_char in protected:
            groups[target_char].add(f"{source_cp:04X}")
    return {
        target: sorted(groups[target])
        for target in sorted(groups)
        if groups[target]
    }


def dump_document(document: dict[str, dict[str, object]]) -> str:
    lines = ["{"]
    sections = list(document.items())
    for section_index, (section, values) in enumerate(sections):
        section_comma = "," if section_index < len(sections) - 1 else ""
        lines.append(f"  {json.dumps(section)}: {{")
        items = list(values.items())
        for index, (key, value) in enumerate(items):
            comma = "," if index < len(items) - 1 else ""
            encoded = json.dumps(value, ensure_ascii=False, sort_keys=True)
            lines.append(f"    {json.dumps(key)}: {encoded}{comma}")
        lines.append(f"  }}{section_comma}")
    lines.append("}")
    return "\n".join(lines) + "\n"


def build_document(text: str) -> dict[str, dict[str, object]]:
    groups = build_groups(text)
    mapping_count = sum(len(codepoints) for codepoints in groups.values())
    if mapping_count != EXPECTED_MAPPING_COUNT:
        raise SystemExit(
            f"mapping count mismatch: expected {EXPECTED_MAPPING_COUNT} actual {mapping_count}"
        )
    return {
        "metadata": {
            "source_url": SOURCE_URL,
            "source_version": VERSION,
            "source_date": DATE,
            "source_sha256": SOURCE_SHA256,
            "license": "Unicode License v3",
            "license_url": LICENSE_URL,
            "selection_rule": (
                "single non-ASCII source code point to a single protected ASCII target; "
                "ASCII sources, U+FF01..U+FF5E, and multi-character targets are excluded"
            ),
        },
        "selection": {
            "protected_tokens": list(PROTECTED_TOKENS),
            "protected_ascii": protected_ascii(),
            "mapping_count": mapping_count,
        },
        "confusables": groups,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    args = parser.parse_args()
    print(dump_document(build_document(validate_source(args.source))), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
