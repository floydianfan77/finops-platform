"""CLI entry point for the billing generator.

Examples:
    billing-generator --sink stdout --interval 2 --batch-size 5
    billing-generator --sink file --file-path ./data/billing.ndjson
    billing-generator --sink stdout --max-batches 3 --seed 42
"""

from __future__ import annotations

import argparse

from billing_generator import __version__
from billing_generator.config import Settings
from billing_generator.scheduler import build_scheduler
from billing_generator.sinks import build_sink


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="billing-generator",
        description="Generate synthetic, FOCUS-aligned cloud billing records.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument(
        "--sink",
        choices=["stdout", "file", "broker"],
        help="Output destination (default from env BILLING_SINK or 'stdout').",
    )
    parser.add_argument("--batch-size", type=int, help="Records per batch.")
    parser.add_argument(
        "--interval", type=float, dest="interval_seconds",
        help="Seconds between batches (0 = as fast as possible).",
    )
    parser.add_argument("--num-accounts", type=int, help="Number of fake accounts.")
    parser.add_argument("--seed", type=int, help="Seed for reproducible output.")
    parser.add_argument("--file-path", help="Output path when --sink file.")
    parser.add_argument(
        "--max-batches", type=int, default=None,
        help="Stop after N batches (default: run until interrupted).",
    )
    return parser


def _merge_settings(args: argparse.Namespace) -> Settings:
    """Env-based settings, overridden by any explicitly provided CLI flags."""
    settings = Settings()
    overrides = {
        "sink": args.sink,
        "batch_size": args.batch_size,
        "interval_seconds": args.interval_seconds,
        "num_accounts": args.num_accounts,
        "seed": args.seed,
        "file_path": args.file_path,
    }
    for key, value in overrides.items():
        if value is not None:
            setattr(settings, key, value)
    return settings


def main() -> None:
    args = _build_parser().parse_args()
    settings = _merge_settings(args)

    sink = build_sink(settings)
    scheduler = build_scheduler(
        num_accounts=settings.num_accounts,
        seed=settings.seed,
        sink=sink,
        batch_size=settings.batch_size,
        interval_seconds=settings.interval_seconds,
        max_batches=args.max_batches,
    )
    scheduler.run()


if __name__ == "__main__":
    main()
