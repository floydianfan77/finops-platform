"""FastAPI application: JSON cost endpoints, budget alerts, and a dashboard."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse

from api_service import __version__, budgets, queries
from api_service.config import Settings
from api_service.db import read_conn, table_exists
from api_service.queries import GoldNotReady

_STATIC = Path(__file__).parent / "static"


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    app = FastAPI(title="FinOps API", version=__version__,
                  description="Query cost rollups and budget alerts.")

    def _read(fn):
        """Run a query function against a fresh read-only connection."""
        try:
            with read_conn(settings.db_path) as conn:
                return fn(conn)
        except GoldNotReady as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except Exception as exc:  # e.g. DB file missing
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @app.get("/", response_class=HTMLResponse, include_in_schema=False)
    def dashboard() -> str:
        return (_STATIC / "index.html").read_text(encoding="utf-8")

    @app.get("/health")
    def health() -> dict:
        gold_ready = False
        try:
            with read_conn(settings.db_path) as conn:
                gold_ready = table_exists(conn, "agg_cost_by_provider")
        except Exception:
            gold_ready = False
        return {"status": "ok", "version": __version__,
                "db_path": settings.db_path, "gold_ready": gold_ready}

    @app.get("/api/summary")
    def api_summary() -> dict:
        return _read(queries.summary)

    @app.get("/api/costs/by-service")
    def api_by_service(limit: int = Query(10, ge=1, le=100)) -> list[dict]:
        return _read(lambda c: queries.by_service(c, limit))

    @app.get("/api/costs/by-provider")
    def api_by_provider() -> list[dict]:
        return _read(queries.by_provider)

    @app.get("/api/costs/by-account")
    def api_by_account(limit: int = Query(10, ge=1, le=100)) -> list[dict]:
        return _read(lambda c: queries.by_account(c, limit))

    @app.get("/api/costs/by-tag")
    def api_by_tag(key: str = Query("team")) -> list[dict]:
        return _read(lambda c: queries.by_tag(c, key))

    @app.get("/api/costs/timeseries")
    def api_timeseries() -> list[dict]:
        return _read(queries.timeseries)

    @app.get("/api/budgets")
    def api_budgets() -> dict:
        def _eval(conn):
            return budgets.evaluate(
                queries.total_billed(conn),
                queries.provider_totals(conn),
                budget_total=settings.budget_total,
                budget_by_provider=settings.budget_by_provider,
                warn_ratio=settings.warn_ratio,
            )
        return _read(_eval)

    return app


app = create_app()
