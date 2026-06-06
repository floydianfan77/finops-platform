"""Budget evaluation: compare spend against limits and emit alert statuses.

Pure functions (no DB), so they're trivial to unit-test.

Status thresholds:
    spend / budget  <  warn_ratio   -> "OK"
    warn_ratio <= ratio < 1.0       -> "WARN"
    ratio >= 1.0                    -> "OVER"
"""

from __future__ import annotations


def status_for(spend: float, budget: float, warn_ratio: float = 0.8) -> dict:
    ratio = (spend / budget) if budget > 0 else 0.0
    if ratio >= 1.0:
        state = "OVER"
    elif ratio >= warn_ratio:
        state = "WARN"
    else:
        state = "OK"
    return {
        "spend": round(spend, 2),
        "budget": round(budget, 2),
        "ratio": round(ratio, 4),
        "status": state,
    }


def evaluate(
    total_spend: float,
    provider_spend: dict[str, float],
    *,
    budget_total: float,
    budget_by_provider: dict[str, float],
    warn_ratio: float = 0.8,
) -> dict:
    """Return overall + per-provider budget statuses and the list of active alerts."""
    overall = {"scope": "total", "name": "All providers",
               **status_for(total_spend, budget_total, warn_ratio)}

    providers = []
    for name, budget in budget_by_provider.items():
        spend = provider_spend.get(name, 0.0)
        providers.append({"scope": "provider", "name": name,
                          **status_for(spend, budget, warn_ratio)})

    rows = [overall, *providers]
    alerts = [r for r in rows if r["status"] in ("WARN", "OVER")]
    return {
        "warn_ratio": warn_ratio,
        "overall": overall,
        "providers": providers,
        "alerts": alerts,
        "alert_count": len(alerts),
    }
