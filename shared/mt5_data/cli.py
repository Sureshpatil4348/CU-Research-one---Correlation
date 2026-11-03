"""Command-line entry for creating a majors D1 snapshot."""

from __future__ import annotations

import argparse
import sys

from .connection import MT5ConnectionError
from .snapshot import create_snapshot


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Create an immutable MT5 snapshot of the eight major pairs."
    )
    parser.add_argument("--timeframe", default="D1", help="Bar timeframe (default: D1)")
    parser.add_argument(
        "--years",
        type=int,
        default=5,
        help="Years of history ending today (default: 5; ignored with --full-history)",
    )
    parser.add_argument(
        "--full-history",
        action="store_true",
        help="Pull every available daily bar in year chunks (ignores --years)",
    )
    parser.add_argument(
        "--label",
        default="majors",
        help="Label segment in the folder name (default: majors)",
    )
    args = parser.parse_args(argv)

    try:
        path = create_snapshot(
            timeframe=args.timeframe,
            years=None if args.full_history else args.years,
            label=args.label,
            full_history=args.full_history,
        )
    except FileExistsError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    except MT5ConnectionError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001 — surface unexpected pull failures
        print(f"ERROR: snapshot failed: {exc}", file=sys.stderr)
        return 1

    print(f"Snapshot written: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
