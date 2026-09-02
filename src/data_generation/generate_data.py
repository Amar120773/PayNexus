"""CLI entrypoint for generating MuleHunter synthetic CSVs."""

from __future__ import annotations

import argparse
from pathlib import Path

from src.data_generation.config import SyntheticDataConfig
from src.data_generation.generators import generate_dataset, write_dataset


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate MuleHunter synthetic research data.")
    parser.add_argument("--merchants", type=int, default=500)
    parser.add_argument("--transactions", type=int, default=10_000)
    parser.add_argument("--customers", type=int, default=1_500)
    parser.add_argument("--devices", type=int, default=750)
    parser.add_argument("--ips", type=int, default=750)
    parser.add_argument("--settlement-accounts", type=int, default=750)
    parser.add_argument("--mule-networks", type=int, default=10)
    parser.add_argument("--period-days", type=int, default=90)
    parser.add_argument("--start-date", type=str, default="2026-01-01")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output-dir", type=Path, default=Path("data/synthetic"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = SyntheticDataConfig(
        merchants=args.merchants,
        transactions=args.transactions,
        customers=args.customers,
        devices=args.devices,
        ips=args.ips,
        settlement_accounts=args.settlement_accounts,
        mule_networks=args.mule_networks,
        period_days=args.period_days,
        start_date=args.start_date,
        seed=args.seed,
        output_dir=args.output_dir,
    )
    dataset = generate_dataset(config)
    write_dataset(dataset, config.output_dir)
    print(f"Wrote {len(dataset)} CSV files to {config.output_dir}")
    print(
        "Counts: "
        f"merchants={len(dataset['merchants'])}, "
        f"transactions={len(dataset['transactions'])}, "
        f"customers={len(dataset['customers'])}, "
        f"mule_merchants={int(dataset['merchant_labels']['is_mule'].sum())}, "
        f"mule_networks={len(dataset['mule_networks'])}"
    )


if __name__ == "__main__":
    main()
