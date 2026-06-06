"""CLI entry point: run the FinOps API + dashboard with uvicorn.

Examples:
    api-service --db-path ../ingestion-service/data/finops.db
    api-service --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

import argparse

import uvicorn

from api_service import __version__
from api_service.app import create_app
from api_service.config import Settings


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="api-service",
        description="Serve the FinOps cost API + dashboard.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--db-path", dest="db_path", help="SQLite database to read.")
    parser.add_argument("--host", help="Bind host (default 127.0.0.1).")
    parser.add_argument("--port", type=int, help="Bind port (default 8000).")
    return parser


def main() -> None:
    args = _build_parser().parse_args()
    settings = Settings()
    if args.db_path is not None:
        settings.db_path = args.db_path
    if args.host is not None:
        settings.host = args.host
    if args.port is not None:
        settings.port = args.port

    app = create_app(settings)
    print(f"[api-service] serving on http://{settings.host}:{settings.port} "
          f"(db: {settings.db_path})")
    uvicorn.run(app, host=settings.host, port=settings.port, log_level="info")


if __name__ == "__main__":
    main()
