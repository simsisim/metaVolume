#!/usr/bin/env python3
"""
Add a market_cap column (from downloadData_v1's tradingview_universe.csv) to
every results CSV under results/hve_results/, then split each into 3
market-cap-tier sibling files (small/mid/large) so tier filtering doesn't
require opening a spreadsheet.

Market cap source: ../downloadData_v1/user_input/tradingview_universe.csv
('Symbol' -> 'Market capitalization'), the same file metaVolume's own
ticker universe is synced from. It's a snapshot (not historical-at-event-date)
but adequate for excluding micro-caps.

Tiers (chosen 2026-08-16, standard buckets excluding micro/nano-cap):
    small:  $300M  - $2B
    mid:    $2B    - $10B
    large:  $10B+
    (below $300M, or unmatched/unknown market cap, excluded from all 3)

Rerun this after every baseline rebuild (preprocess/preprocess_full) -- it
overwrites market_cap and all tier files in place. Safe to rerun: only
*_small_cap.csv/_mid_cap.csv/_large_cap.csv are written as derived output,
and those are excluded from the source-file scan so reruns don't cascade.

Usage:
    python scripts/add_market_cap.py
"""
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).parent.parent
RESULTS_DIR = ROOT / 'results' / 'hve_results'
UNIVERSE_FILE = ROOT / '..' / 'downloadData_v1' / 'user_input' / 'tradingview_universe.csv'

SMALL_MIN = 300_000_000
MID_MIN = 2_000_000_000
LARGE_MIN = 10_000_000_000
TIERS = [
    ('small_cap', SMALL_MIN, MID_MIN),
    ('mid_cap', MID_MIN, LARGE_MIN),
    ('large_cap', LARGE_MIN, float('inf')),
]
TIER_SUFFIXES = tuple(f'_{name}.csv' for name, _, _ in TIERS)


def load_market_cap_map() -> dict:
    df = pd.read_csv(UNIVERSE_FILE, usecols=['Symbol', 'Market capitalization'])
    df = df.dropna(subset=['Symbol'])
    return dict(zip(df['Symbol'], df['Market capitalization']))


def add_market_cap_and_split(path: Path, mcap_map: dict) -> None:
    df = pd.read_csv(path)
    ticker_col = 'Symbol' if 'Symbol' in df.columns else 'ticker' if 'ticker' in df.columns else None
    if ticker_col is None:
        print(f"  SKIP {path.relative_to(ROOT)}: no ticker/Symbol column")
        return

    df['market_cap'] = df[ticker_col].map(mcap_map)
    # Put market_cap right after the ticker column for readability
    cols = list(df.columns)
    cols.remove('market_cap')
    insert_at = cols.index(ticker_col) + 1
    cols.insert(insert_at, 'market_cap')
    df = df[cols]

    df.to_csv(path, index=False)
    matched = df['market_cap'].notna().sum()
    print(f"  {path.relative_to(ROOT)}: {matched}/{len(df)} tickers matched")

    for tier_name, lo, hi in TIERS:
        tier_df = df[(df['market_cap'] >= lo) & (df['market_cap'] < hi)]
        tier_path = path.with_name(f"{path.stem}_{tier_name}.csv")
        tier_df.to_csv(tier_path, index=False)
        print(f"    -> {tier_path.name}: {len(tier_df)} rows")


def main():
    if not UNIVERSE_FILE.exists():
        print(f"ERROR: universe file not found: {UNIVERSE_FILE}", file=sys.stderr)
        sys.exit(1)

    mcap_map = load_market_cap_map()
    print(f"Loaded market cap for {len(mcap_map)} tickers from {UNIVERSE_FILE}\n")

    csv_files = sorted(
        p for p in RESULTS_DIR.rglob('*.csv')
        if not p.name.endswith(TIER_SUFFIXES)
    )
    if not csv_files:
        print(f"No CSV files found under {RESULTS_DIR}")
        return

    for path in csv_files:
        add_market_cap_and_split(path, mcap_map)


if __name__ == '__main__':
    main()
