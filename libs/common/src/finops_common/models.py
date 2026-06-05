"""Typed model for a FOCUS-aligned billing record.

Mirrors ``schemas/billing/focus_billing_record.schema.json``. This is the shared,
authoritative contract imported by every service that produces or consumes billing
records (the billing generator, the ingestion service, etc.).
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class FocusBillingRecord(BaseModel):
    """A single cost & usage line item, aligned to the FOCUS specification."""

    RecordId: str
    ProviderName: str
    PublisherName: str | None = None

    BillingAccountId: str
    BillingAccountName: str | None = None
    SubAccountId: str | None = None

    BillingPeriodStart: datetime
    BillingPeriodEnd: datetime
    ChargePeriodStart: datetime
    ChargePeriodEnd: datetime

    ServiceName: str
    ServiceCategory: str
    ChargeCategory: str
    ChargeDescription: str | None = None

    RegionId: str
    ResourceId: str
    ResourceType: str | None = None

    PricingQuantity: float = Field(ge=0)
    PricingUnit: str
    ListUnitPrice: float = Field(ge=0)
    ListCost: float
    EffectiveCost: float
    BilledCost: float
    BillingCurrency: str

    Tags: dict[str, str] = Field(default_factory=dict)

    def to_json(self) -> str:
        """Serialize to a single-line JSON string (datetimes as ISO-8601)."""
        return self.model_dump_json()
