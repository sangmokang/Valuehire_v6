"""Recognize a literal kickoff failure reason on its own canonical FAIL line."""

import re
import sys
from pathlib import Path

TARGET = r"(?:PR #[0-9]+|task/[A-Za-z0-9_./-]+)"
LEGACY_REASONS = {
    "행 없음": rf"처분표에 {TARGET} 행 없음",
    "대상 칸에 다른 대상": (
        rf"{TARGET} 행의 대상 칸에 다른 대상 [1-9][0-9]*개가 함께 적혀 있다"
        r" — 대상마다 자기 행이 있어야 한다"
    ),
    "처분이 둘 이상": (
        rf"{TARGET} 행이 (?:[2-9]|[1-9][0-9]+)개"
        r" — 같은 대상에 처분이 둘 이상이면 결론이 무엇인지 정해지지 않는다"
    ),
}


def has_failure(output: str, expected: str) -> bool:
    if not expected.strip() or "\n" in expected or "\r" in expected:
        return False
    for line in output.split("\n"):
        if not line.startswith("FAIL: "):
            continue
        message = line.removeprefix("FAIL: ").removesuffix("\r")
        if expected in LEGACY_REASONS:
            if re.fullmatch(LEGACY_REASONS[expected], message):
                return True
        elif message.startswith(expected):
            suffix = message[len(expected):]
            if not suffix or suffix[0] in " \t/":
                return True
    return False


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: has-kickoff-failure.py LOG EXPECTED", file=sys.stderr)
        return 2
    try:
        output = Path(sys.argv[1]).read_bytes().decode("utf-8")
    except (OSError, UnicodeError) as error:
        print(f"cannot read kickoff output: {error}", file=sys.stderr)
        return 2
    return 0 if has_failure(output, sys.argv[2]) else 1


if __name__ == "__main__":
    sys.exit(main())
