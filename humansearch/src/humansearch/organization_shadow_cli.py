"""Local-only command line entrypoint for organization shadow review."""

from collections.abc import Sequence


def main(argv: Sequence[str] | None = None) -> int:
    del argv
    raise NotImplementedError("organization shadow CLI is not implemented")


if __name__ == "__main__":
    raise SystemExit(main())
