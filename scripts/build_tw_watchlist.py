#!/usr/bin/env python3
"""
Build a TradingView watchlist (.txt import format) from HVE results: every
ticker that had an HVE (all-time volume record) in the last N days, grouped
into ###Large Cap / ###Mid Cap / ###Small Cap sections.

Source: results/hve_results/daily/hve_results_daily.csv (must already have
a market_cap column -- run scripts/add_market_cap.py first if missing).

Cap tiers match add_market_cap.py's:
    large:  $10B+
    mid:    $2B - $10B
    small:  $300M - $2B
    (below $300M, or unmatched market cap, excluded)

Exchange prefix (required by TradingView's SYMBOL format) comes from
downloadData_v1's tradingview_universe.csv 'Exchange' column, which is
itself sourced from TradingView -- NASDAQ/NYSE map straight through.
NYSE Arca is mapped to AMEX: (TradingView's common prefix for Arca-listed
tickers); this dataset has ~108 of those and 1 CBOE ticker, so double-check
those specific symbols resolve correctly on import.

TradingView watchlist format: one "###Section Name" header line, followed
by a single comma-separated "EXCHANGE:SYMBOL,EXCHANGE:SYMBOL,..." line.

Usage:
    python scripts/build_tw_watchlist.py [--days 50]
"""
import argparse
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).parent.parent
HVE_DAILY_FILE = ROOT / 'results' / 'hve_results' / 'daily' / 'hve_results_daily.csv'
UNIVERSE_FILE = ROOT / '..' / 'downloadData_v1' / 'user_input' / 'tradingview_universe.csv'
OUTPUT_DIR = ROOT / 'results' / 'hve_results'

LARGE_MIN = 10_000_000_000
MID_MIN = 2_000_000_000
SMALL_MIN = 300_000_000

EXCHANGE_MAP = {
    'NASDAQ': 'NASDAQ',
    'NYSE': 'NYSE',
    'NYSE Arca': 'AMEX',
    'CBOE': 'CBOE',
}


def tier_for(market_cap: float) -> str:
    if pd.isna(market_cap) or market_cap < SMALL_MIN:
        return None
    if market_cap >= LARGE_MIN:
        return 'Large Cap'
    if market_cap >= MID_MIN:
        return 'Mid Cap'
    return 'Small Cap'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--days', type=int, default=50,
                         help='Include HVE events from the last N days (default: 50)')
    args = parser.parse_args()

    hve = pd.read_csv(HVE_DAILY_FILE)
    if 'market_cap' not in hve.columns:
        raise SystemExit(f"ERROR: {HVE_DAILY_FILE} has no market_cap column -- "
                          f"run scripts/add_market_cap.py first")

    recent = hve[hve['days_since_hve'] <= args.days].copy()
    recent = recent.sort_values('days_since_hve')

    universe = pd.read_csv(UNIVERSE_FILE, usecols=['Symbol', 'Exchange'])
    exchange_map = dict(zip(universe['Symbol'], universe['Exchange']))

    recent['tier'] = recent['market_cap'].apply(tier_for)
    recent = recent.dropna(subset=['tier'])

    sections = {'Large Cap': [], 'Mid Cap': [], 'Small Cap': []}
    skipped_no_exchange = []

    for _, row in recent.iterrows():
        ticker = row['ticker']
        exch_raw = exchange_map.get(ticker)
        exch = EXCHANGE_MAP.get(exch_raw)
        if not exch:
            skipped_no_exchange.append(ticker)
            continue
        sections[row['tier']].append(f"{exch}:{ticker}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / f'tw_watchlist_hve_{args.days}d.txt'
    with open(out_path, 'w') as f:
        for section in ('Large Cap', 'Mid Cap', 'Small Cap'):
            symbols = sections[section]
            f.write(f"###{section}\n")
            f.write(','.join(symbols) + '\n')

    print(f"HVE events in the last {args.days} days: {len(recent) + len(skipped_no_exchange)}")
    for section in ('Large Cap', 'Mid Cap', 'Small Cap'):
        print(f"  {section}: {len(sections[section])}")
    if skipped_no_exchange:
        print(f"  Skipped (no exchange match): {len(skipped_no_exchange)} -> {skipped_no_exchange}")
    print(f"\nWritten to: {out_path}")


if __name__ == '__main__':
    main()
