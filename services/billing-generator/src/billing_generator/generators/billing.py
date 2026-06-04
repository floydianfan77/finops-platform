"""Factory that turns the account catalog into FOCUS billing records."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from billing_generator.generators.accounts import AccountCatalog
from billing_generator.models import FocusBillingRecord

# Distribution of charge categories (mostly usage, with occasional credits/taxes).
_CHARGE_CATEGORIES = (
    ["Usage"] * 88 + ["Purchase"] * 5 + ["Tax"] * 4 + ["Credit"] * 3
)


class BillingGenerator:
    """Produces individual or batched :class:`FocusBillingRecord` instances."""

    def __init__(self, catalog: AccountCatalog) -> None:
        self._catalog = catalog
        self._rng = catalog.rng

    def _month_bounds(self, now: datetime) -> tuple[datetime, datetime]:
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        # First day of next month.
        if start.month == 12:
            end = start.replace(year=start.year + 1, month=1)
        else:
            end = start.replace(month=start.month + 1)
        return start, end

    def generate_one(self, now: datetime | None = None) -> FocusBillingRecord:
        now = now or datetime.now(timezone.utc)
        account = self._catalog.pick_account()
        service = self._catalog.pick_service()
        region = self._catalog.pick_region()

        billing_start, billing_end = self._month_bounds(now)

        # Charge window: a 1-hour slice ending "now".
        charge_end = now
        charge_start = charge_end - timedelta(hours=1)

        quantity = round(self._rng.uniform(0.1, 1000.0), 4)
        list_unit_price = service.list_unit_price
        list_cost = round(quantity * list_unit_price, 6)

        charge_category = self._rng.choice(_CHARGE_CATEGORIES)

        # Discounts: effective cost is usually below list (commitments/negotiated).
        discount_factor = self._rng.uniform(0.6, 1.0)
        effective_cost = round(list_cost * discount_factor, 6)
        billed_cost = effective_cost

        # Credits are negative; taxes add on top.
        if charge_category == "Credit":
            effective_cost = -abs(effective_cost)
            billed_cost = effective_cost
            list_cost = 0.0
        elif charge_category == "Tax":
            list_cost = 0.0
            list_unit_price = 0.0
            quantity = 0.0

        resource_id = (
            f"{service.resource_type}/"
            f"{uuid.uuid4().hex[:12]}"
        )

        return FocusBillingRecord(
            RecordId=str(uuid.uuid4()),
            ProviderName=service.provider,
            PublisherName=service.provider,
            BillingAccountId=account.account_id,
            BillingAccountName=account.account_name,
            SubAccountId=account.sub_account_id,
            BillingPeriodStart=billing_start,
            BillingPeriodEnd=billing_end,
            ChargePeriodStart=charge_start,
            ChargePeriodEnd=charge_end,
            ServiceName=service.name,
            ServiceCategory=service.category,
            ChargeCategory=charge_category,
            ChargeDescription=f"{service.name} {charge_category.lower()} in {region}",
            RegionId=region,
            ResourceId=resource_id,
            ResourceType=service.resource_type,
            PricingQuantity=quantity,
            PricingUnit=service.pricing_unit,
            ListUnitPrice=list_unit_price,
            ListCost=list_cost,
            EffectiveCost=effective_cost,
            BilledCost=billed_cost,
            BillingCurrency="USD",
            Tags=self._catalog.random_tags(),
        )

    def generate_batch(self, size: int) -> list[FocusBillingRecord]:
        now = datetime.now(timezone.utc)
        return [self.generate_one(now) for _ in range(size)]
