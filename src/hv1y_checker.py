"""
HV1Y Checker (post-process)
============================

Computes HV1Y (Highest Volume in 1 Year) fresh, every run, per timeframe --
decoupled from the expensive HVE/HVD pre-process pipeline it used to ride
along with as a side effect of HVEScreener.screen_batch().

Why this needs its own module instead of reusing VolChecker:
HV1Y is a rolling window, not a record or a ranking, so it doesn't fit the
"frozen baseline + incremental delta" pattern HVD/HVE use -- a value can
age OUT of a rolling window as time passes (something that was the year's
highest-volume day eventually falls outside the trailing 365 days), which
an ever-accumulating incremental ledger has no way to represent. There is
no baseline file, no incremental file, and no comparison-against-prior-max
here: every run recomputes the whole window from scratch, so expiry is
handled automatically by construction.

That also means the read pattern is different from VolChecker's (which
only reads *new* rows since a cutoff): a rolling window needs the *whole*
window's data in memory every time, so this always reads archive/+current/
via the same DataReader pre-process already uses -- just with the fast
market_data_batch/ overlay included (unlike pre's HVE/HVD baseline build,
which deliberately excludes it for a deterministic cutoff; HV1Y has no
cutoff to keep deterministic, so freshness wins here, matching post's
philosophy for HVD/HVE).

What makes this still much cheaper than the old ride-along path: it skips
HVEScreener's expensive full-history cummax and all_hve_details/all_hvd_details
Python dict-list building entirely -- just a slice + max() per ticker.

Output (per timeframe):
  results/post/{timeframe}/HV1Y_{timeframe}.csv
    ticker, timeframe, hv1y_date, hv1y_volume, days_since_hv1y
"""

import logging
import pandas as pd
from datetime import date
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)


class HV1YChecker:

    def __init__(self, config, user_config, timeframe: str = 'daily'):
        self.config = config
        self.timeframe = timeframe
        self.base_dir = Path(__file__).resolve().parent.parent
        self.ticker_choice = getattr(user_config, 'ticker_choice', None)
        self.window_days = int(getattr(user_config, 'hv1y_window_days', 365))
        self.batch_size = int(getattr(user_config, 'batch_size', 100))

        self.output_dir = self.base_dir / 'results' / 'post' / timeframe
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.output_path = self.output_dir / f'HV1Y_{timeframe}.csv'

    def _window_periods(self) -> int:
        """Same conversion HVEScreener._get_hv1y_window_periods() uses."""
        if self.timeframe == 'weekly':
            return self.window_days // 7
        elif self.timeframe == 'monthly':
            return self.window_days // 30
        return self.window_days

    def _load_ticker_list(self) -> List[str]:
        """Tickers for the configured ticker_choice (same file VolChecker filters against)."""
        if self.ticker_choice is None:
            print("   WARNING: no ticker_choice configured — nothing to check")
            return []
        ticker_file = self.base_dir / 'data' / 'tickers' / f'combined_tickers_{self.ticker_choice}.csv'
        if not ticker_file.exists():
            print(f"   ERROR: ticker file not found: {ticker_file}")
            return []
        try:
            tf = pd.read_csv(ticker_file)
            col = 'ticker' if 'ticker' in tf.columns else tf.columns[0]
            return sorted(set(tf[col].dropna().astype(str).str.strip()))
        except Exception as e:
            print(f"   WARNING: could not load ticker list: {e}")
            return []

    def run(self) -> None:
        from src.data_reader import DataReader

        print(f"\n{'='*60}")
        print(f"HV1Y CHECKER — {self.timeframe.upper()}")
        print(f"{'='*60}")

        tickers = self._load_ticker_list()
        if not tickers:
            return
        print(f" Checking {len(tickers)} tickers, {self.window_days}-day window "
              f"({self._window_periods()} {self.timeframe} periods)")

        # Freshest data available -- unlike pre's HVE/HVD baseline build,
        # there's no cutoff to keep deterministic here, so batch overlay
        # (the fast pipeline) is included for maximum currency.
        data_reader = DataReader(self.config, self.timeframe,
                                  batch_size=self.batch_size, include_batch_overlay=True)

        window_periods = self._window_periods()
        today = date.today()
        rows = []
        skipped = 0

        for ticker in tickers:
            df = data_reader.read_stock_data(ticker)
            if df is None or df.empty or 'Volume' not in df.columns:
                skipped += 1
                continue

            df = df.sort_index()
            if self.timeframe == 'daily':
                latest_date = df.index[-1]
                lookback_date = latest_date - pd.DateOffset(days=window_periods)
                window = df[df.index >= lookback_date]
            else:
                window = df.tail(window_periods)

            if window.empty or window['Volume'].isna().all():
                skipped += 1
                continue

            hv1y_volume = window['Volume'].max()
            hv1y_date = window['Volume'].idxmax()

            rows.append({
                'ticker':         ticker,
                'timeframe':      self.timeframe,
                'hv1y_date':      hv1y_date.strftime('%Y-%m-%d'),
                'hv1y_volume':    int(hv1y_volume),
                'days_since_hv1y': (today - hv1y_date.date()).days,
            })

        cols = ['ticker', 'timeframe', 'hv1y_date', 'hv1y_volume', 'days_since_hv1y']
        df_out = pd.DataFrame(rows)[cols].sort_values('days_since_hv1y') if rows else pd.DataFrame(columns=cols)
        df_out.to_csv(self.output_path, index=False)

        print(f" Checked: {len(rows)} tickers | Skipped (no data): {skipped}")
        print(f" HV1Y summary written: {self.output_path}")
