"""Configuration for MuleHunter synthetic data generation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SyntheticDataConfig:
    """Top-level controls for the reproducible synthetic dataset."""

    merchants: int = 5000
    transactions: int = 150_000
    customers: int = 10_000
    devices: int = 10_000
    ips: int = 10_000
    settlement_accounts: int = 5_000
    mule_networks: int = 75
    seed: int = 42
    period_days: int = 90
    start_date: str = "2026-01-01"
    output_dir: Path = Path("data/synthetic_v2")

    def validate(self) -> None:
        if self.merchants < 3:
            raise ValueError("merchants must be at least 3")
        if self.transactions < self.merchants:
            raise ValueError("transactions should be at least the merchant count")
        if self.customers < 10:
            raise ValueError("customers must be at least 10")
        if self.devices < 10:
            raise ValueError("devices must be at least 10")
        if self.ips < 10:
            raise ValueError("ips must be at least 10")
        if self.settlement_accounts < 10:
            raise ValueError("settlement_accounts must be at least 10")
        if self.mule_networks < 1:
            raise ValueError("mule_networks must be at least 1")
        if self.mule_networks * 3 > self.merchants:
            raise ValueError("mule_networks requires at least 3 merchants per network")
        if self.period_days < 30:
            raise ValueError("period_days should be at least 30")


CATEGORIES = (
    "ecommerce",
    "electronics",
    "fashion",
    "grocery",
    "restaurant",
    "travel",
    "SaaS",
    "education",
    "healthcare",
    "services",
)

PAYMENT_METHODS = ("UPI", "card", "netbanking", "wallet")
STATUSES = ("SUCCESS", "FAILED", "REFUNDED")
MULE_SCENARIOS = (
    "TYPE_A_RAPID_FORMATION",
    "TYPE_B_GRADUAL_EXPANSION",
    "TYPE_C_INFRASTRUCTURE_CONVERGENCE",
    "TYPE_D_BEHAVIORAL_TRANSITION",
)
