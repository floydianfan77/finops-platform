"""Builds a stable catalog of fake tenants, services, regions, and resources.

The catalog is generated once (deterministically if a seed is given) so that billing
records reference a consistent population of accounts/resources over time -- just like
a real cloud bill references the same account ids month over month.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from faker import Faker

# (ServiceName, ServiceCategory, ResourceType, PricingUnit) tuples per provider flavour.
_SERVICE_CATALOG: list[tuple[str, str, str, str]] = [
    ("Amazon EC2", "Compute", "t3.medium", "Hours"),
    ("Amazon S3", "Storage", "gp3-bucket", "GB-Month"),
    ("Amazon RDS", "Databases", "db.r6g.large", "Hours"),
    ("AWS Lambda", "Compute", "function", "Requests"),
    ("Amazon CloudFront", "Networking", "distribution", "GB"),
    ("Google BigQuery", "Analytics", "on-demand-slot", "TB-Scanned"),
    ("Google Compute Engine", "Compute", "n2-standard-4", "Hours"),
    ("Azure Blob Storage", "Storage", "hot-tier", "GB-Month"),
    ("Azure SQL Database", "Databases", "S3-tier", "Hours"),
    ("Amazon SageMaker", "AI and Machine Learning", "ml.m5.xlarge", "Hours"),
]

_REGIONS: list[str] = [
    "us-east-1",
    "us-west-2",
    "eu-west-1",
    "eu-central-1",
    "sa-east-1",
    "ap-southeast-1",
]

_PROVIDER_BY_PREFIX = {
    "Amazon": "AWS",
    "AWS": "AWS",
    "Google": "GCP",
    "Azure": "Azure",
}

_ENVIRONMENTS = ["prod", "staging", "dev", "qa"]
_TEAMS = ["platform", "data", "payments", "growth", "ml", "security"]


@dataclass
class ServiceOffering:
    name: str
    category: str
    resource_type: str
    pricing_unit: str
    provider: str
    list_unit_price: float


@dataclass
class Account:
    account_id: str
    account_name: str
    sub_account_id: str


@dataclass
class AccountCatalog:
    """A fixed population of accounts + service offerings to bill against."""

    num_accounts: int = 8
    seed: int | None = None

    accounts: list[Account] = field(default_factory=list)
    services: list[ServiceOffering] = field(default_factory=list)
    regions: list[str] = field(default_factory=lambda: list(_REGIONS))

    def __post_init__(self) -> None:
        self._rng = random.Random(self.seed)
        self._faker = Faker()
        if self.seed is not None:
            Faker.seed(self.seed)
        self._build()

    def _build(self) -> None:
        self.accounts = [
            Account(
                account_id=f"acct-{self._rng.randint(10**9, 10**10 - 1)}",
                account_name=self._faker.company(),
                sub_account_id=f"sub-{self._rng.randint(1000, 9999)}",
            )
            for _ in range(self.num_accounts)
        ]

        self.services = []
        for name, category, resource_type, unit in _SERVICE_CATALOG:
            prefix = name.split(" ", 1)[0]
            provider = _PROVIDER_BY_PREFIX.get(prefix, "AWS")
            self.services.append(
                ServiceOffering(
                    name=name,
                    category=category,
                    resource_type=resource_type,
                    pricing_unit=unit,
                    provider=provider,
                    # Stable-ish list price per service, with cents.
                    list_unit_price=round(self._rng.uniform(0.0005, 4.5), 4),
                )
            )

    # --- random pickers -----------------------------------------------------
    def pick_account(self) -> Account:
        return self._rng.choice(self.accounts)

    def pick_service(self) -> ServiceOffering:
        return self._rng.choice(self.services)

    def pick_region(self) -> str:
        return self._rng.choice(self.regions)

    def random_tags(self) -> dict[str, str]:
        return {
            "environment": self._rng.choice(_ENVIRONMENTS),
            "team": self._rng.choice(_TEAMS),
            "cost_center": f"cc-{self._rng.randint(100, 999)}",
        }

    @property
    def rng(self) -> random.Random:
        return self._rng
