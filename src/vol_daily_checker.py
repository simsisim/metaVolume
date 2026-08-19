"""
Volume Checker (post-process)
==============================

Compares each new period's volume against two stored baselines and flags
tickers that qualify:
  HVD — enters the top-N volume days (HVD_historical_{timeframe}.csv)
  HVE — sets a new all-time-high volume (HVE_historical_{timeframe}.csv)

Runs independently per timeframe (daily, weekly, monthly) -- each instance
is constructed with its own `timeframe` and tracks its own baseline, its
own cutoff date, and its own current-data source. Timeframes never share
or influence each other's cutoff (see write_baseline_metadata() in
hvd_historical_exporter.py for why that matters: pooling cutoffs across
timeframes let a more-current one mask real gaps in a less-current one).

Both HVD/HVE checks read the same per-period ticker data and never modify
their baseline file — new discoveries accumulate in a separate incremental
ledger (baseline ∪ incremental is recomputed in memory each run) until the
next full preprocess_full baseline rebuild folds them in.

Supports two data sources:
  tradingview  — TradingView bulk CSV files (one file per trading day).
                 Daily only -- there's no weekly/monthly bulk-file concept
                 in this codebase, so weekly/monthly always use 'yahoo'
                 regardless of this setting.
  yahoo        — Per-ticker Yahoo Finance CSVs (from downloadData_v1),
                 read from current/ (this year's rows only) rather than
                 the full multi-year per-ticker file, so checks don't
                 re-parse years of already-covered history. Directory is
                 resolved via Config.get_market_data_dir(timeframe) -- the
                 same YF_{timeframe}_data_files_local/colab config DataReader
                 already uses, so there's no separate vol-checker-specific
                 path setting to keep in sync.

Inputs (per timeframe):
  - results/pre/historical/HVD_historical_{timeframe}.csv  (HVD baseline, READ-ONLY)
  - results/pre/historical/HVE_historical_{timeframe}.csv  (HVE baseline, READ-ONLY)
  - results/pre/historical/baseline_metadata.json          (per-timeframe cutoff dates, READ-ONLY)

  For TradingView source (daily only):
  - tw_files/daily/*.csv  (one bulk file per trading day)

  For Yahoo source:
  - downloadData_v1/data/market_data/{timeframe}/current/<TICKER>.csv (this year only)

Outputs (per timeframe, under results/post/{timeframe}/):
  - vol_check_results.csv   (HVD hits, appended each run)
  - HVE_check_results.csv   (HVE hits, appended each run)
  - last_processed.txt      (state: last processed date)
  - HVD_incremental.csv     (new HVD events since baseline)
  - HVE_incremental.csv     (new HVE events since baseline)
  - snapshots/vol_check_<date>.csv  (per-period HVD snapshots)
  - snapshots/HVE_check_<date>.csv  (per-period HVE snapshots)
  - daily_log.csv           (full log, HVD only)

  Baselines are never modified during checker runs.
  Delete HVD_incremental.csv / HVE_incremental.csv and re-run to safely
  reprocess any date range.

TW bulk file format (columns that matter):
  Symbol, Open 1 day, High 1 day, Low 1 day, Price (=Close), Volume 1 day
  Date is NOT in the file — extracted from filename (*_YYYY-MM-DD.csv)

Yahoo file format (per-ticker):
  Date,Open,High,Low,Close,Volume,...
  Date is IN the file with timezone offset (2020-01-02 00:00:00-05:00)
"""

import re
import logging
import pandas as pd
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class VolChecker:

    def __init__(self, config, user_config, timeframe: str = 'daily'):
        self.config = config
        self.timeframe = timeframe
        self.base_dir = Path(__file__).resolve().parent.parent
        self.ticker_choice = getattr(user_config, 'ticker_choice', None)

        # Baseline files (produced by pre-processor HVD/HVE export, read-only during checker runs)
        self.baseline_path = (
            self.base_dir / 'results' / 'pre' / 'historical' / f'HVD_historical_{timeframe}.csv'
        )
        self.baseline_dir = self.baseline_path.parent
        self.hve_baseline_path = self.baseline_dir / f'HVE_historical_{timeframe}.csv'

        # ------------------------------------------------------------------
        # Data source selection
        # ------------------------------------------------------------------
        self.data_source = getattr(user_config, 'vol_checker_data_source', 'tradingview').strip().lower()
        if self.data_source not in ('tradingview', 'yahoo'):
            print(f"   WARNING: unknown vol_checker_data_source '{self.data_source}' — falling back to tradingview")
            self.data_source = 'tradingview'
        if timeframe != 'daily' and self.data_source == 'tradingview':
            print(f"   NOTE: TradingView source is daily-only (no weekly/monthly bulk files) — "
                  f"using yahoo source for {timeframe}")
            self.data_source = 'yahoo'

        # ------------------------------------------------------------------
        # TradingView bulk files directory (daily only)
        # ------------------------------------------------------------------
        tw_dir_str = getattr(
            user_config,
            'vol_checker_tw_files_dir',
            '../downloadData_v1/data/tw_files/daily/'
        )
        tw_dir = Path(tw_dir_str)
        if not tw_dir.is_absolute():
            tw_dir = (self.base_dir / tw_dir).resolve()
        self.tw_files_dir = tw_dir

        # ------------------------------------------------------------------
        # Yahoo per-ticker data directory -- same resolution DataReader uses
        # (Config.get_market_data_dir), so there's no separate vol-checker
        # path setting that could drift out of sync per timeframe.
        # ------------------------------------------------------------------
        self.yahoo_data_dir = Path(config.get_market_data_dir(timeframe))

        # ------------------------------------------------------------------
        # Output
        # ------------------------------------------------------------------
        self.output_dir = self.base_dir / 'results' / 'post' / timeframe
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results_path     = self.output_dir / 'vol_check_results.csv'
        self.state_path       = self.output_dir / 'last_processed.txt'
        self.incremental_path = self.output_dir / 'HVD_incremental.csv'
        self.daily_log_path   = self.output_dir / 'daily_log.csv'
        self.hve_results_path     = self.output_dir / 'HVE_check_results.csv'
        self.hve_incremental_path = self.output_dir / 'HVE_incremental.csv'
        self.hve_summary_path     = self.output_dir / f'HVE_{timeframe}.csv'

        # How many top positions to flag (default 6)
        self.top_n_flag = int(getattr(user_config, 'vol_checker_top_n_flag', 6))

        # State filled by load_baseline() / load_incremental()
        self.baseline_dict:    Dict[str, List[Dict]] = {}
        self.incremental_dict: Dict[str, List[Dict]] = {}
        self.top_n_hist: int = 0

        # State filled by load_hve_baseline() / load_hve_incremental()
        self.hve_baseline_dict:    Dict[str, Dict] = {}  # ticker -> {'date': ..., 'volume': ...}
        self.hve_incremental_dict: Dict[str, List[Dict]] = {}
        self.hve_check_enabled: bool = False

    # ------------------------------------------------------------------
    # Baseline I/O
    # ------------------------------------------------------------------

    def load_baseline(self) -> bool:
        if not self.baseline_path.exists():
            print(f"   ERROR: Baseline not found: {self.baseline_path}")
            print(f"   Run main.py with HVD_historical_export=TRUE first.")
            return False

        df = pd.read_csv(self.baseline_path)

        date_cols = [c for c in df.columns if c.startswith('HVD_date_')]
        self.top_n_hist = len(date_cols)

        print(f"   Loaded baseline: {len(df)} tickers, top-{self.top_n_hist} positions")

        for _, row in df.iterrows():
            ticker = str(row['Symbol'])
            events = []
            for i in range(1, self.top_n_hist + 1):
                dc = f'HVD_date_{i}'
                vc = f'HVD_vol_{i}'
                if pd.isna(row.get(dc, float('nan'))) or str(row.get(dc, '')) == '':
                    break
                try:
                    events.append({
                        'date':   str(row[dc]),
                        'volume': int(row[vc])
                    })
                except (ValueError, TypeError):
                    break
            self.baseline_dict[ticker] = events  # already sorted vol desc by exporter

        return True

    def load_incremental(self):
        """Load new events accumulated since the baseline was built."""
        self.incremental_dict = {}
        if not self.incremental_path.exists():
            print(f"   No incremental file yet — starting fresh")
            return
        try:
            df = pd.read_csv(self.incremental_path)
            for _, row in df.iterrows():
                ticker = str(row['ticker']).strip()
                try:
                    ev = {'date': str(row['date']), 'volume': int(row['volume'])}
                    self.incremental_dict.setdefault(ticker, []).append(ev)
                except (ValueError, TypeError):
                    continue
            total = sum(len(v) for v in self.incremental_dict.values())
            print(f"   Loaded incremental: {len(self.incremental_dict)} tickers, {total} events")
        except Exception as e:
            print(f"   WARNING: Could not load incremental file: {e}")

    def save_incremental(self):
        """Save incremental_dict to HVD_incremental.csv (long format, baseline untouched)."""
        rows = []
        for ticker, events in self.incremental_dict.items():
            for ev in events:
                rows.append({'ticker': ticker, 'date': ev['date'], 'volume': ev['volume']})

        cols = ['ticker', 'date', 'volume']
        if rows:
            pd.DataFrame(rows)[cols].sort_values(['ticker', 'date']).to_csv(
                self.incremental_path, index=False
            )
        else:
            pd.DataFrame(columns=cols).to_csv(self.incremental_path, index=False)

        print(f"   Incremental file updated: {len(rows)} events — {self.incremental_path}")

    def load_hve_baseline(self) -> bool:
        """
        Load the HVE (all-time record) baseline: ticker -> {date, volume} of
        the highest volume ever recorded as of the last preprocess_full run.

        Unlike the HVD baseline (a top-N list), HVE only needs the single
        highest event -- reduced from the same wide HVE_date_i/HVE_vol_i
        columns the exporter writes. The date is kept (not just the volume)
        so save_hve_summary() can report each ticker's current record
        without needing to re-scan full history.
        """
        if not self.hve_baseline_path.exists():
            print(f"   WARNING: HVE baseline not found: {self.hve_baseline_path}")
            print(f"   Run main.py with HVE_historical_export=TRUE first — HVE checking disabled this run.")
            return False

        df = pd.read_csv(self.hve_baseline_path)
        vol_cols = [c for c in df.columns if c.startswith('HVE_vol_')]

        print(f"   Loaded HVE baseline: {len(df)} tickers")

        for _, row in df.iterrows():
            ticker = str(row['Symbol'])
            best_date, best_vol = None, None
            for vc in vol_cols:
                idx = vc.rsplit('_', 1)[-1]
                dc = f'HVE_date_{idx}'
                val = row.get(vc, '')
                if pd.isna(val) or str(val) == '':
                    continue
                try:
                    vol = int(val)
                except (ValueError, TypeError):
                    continue
                if best_vol is None or vol > best_vol:
                    best_vol = vol
                    best_date = str(row.get(dc, '')).strip()
            if best_vol is not None:
                self.hve_baseline_dict[ticker] = {'date': best_date, 'volume': best_vol}

        return True

    def load_hve_incremental(self):
        """Load new all-time-high events accumulated since the HVE baseline was built."""
        self.hve_incremental_dict = {}
        if not self.hve_incremental_path.exists():
            print(f"   No HVE incremental file yet — starting fresh")
            return
        try:
            df = pd.read_csv(self.hve_incremental_path)
            for _, row in df.iterrows():
                ticker = str(row['ticker']).strip()
                try:
                    ev = {'date': str(row['date']), 'volume': int(row['volume'])}
                    self.hve_incremental_dict.setdefault(ticker, []).append(ev)
                except (ValueError, TypeError):
                    continue
            total = sum(len(v) for v in self.hve_incremental_dict.values())
            print(f"   Loaded HVE incremental: {len(self.hve_incremental_dict)} tickers, {total} events")
        except Exception as e:
            print(f"   WARNING: Could not load HVE incremental file: {e}")

    def save_hve_incremental(self):
        """Save hve_incremental_dict to HVE_incremental.csv (long format, baseline untouched)."""
        rows = []
        for ticker, events in self.hve_incremental_dict.items():
            for ev in events:
                rows.append({'ticker': ticker, 'date': ev['date'], 'volume': ev['volume']})

        cols = ['ticker', 'date', 'volume']
        if rows:
            pd.DataFrame(rows)[cols].sort_values(['ticker', 'date']).to_csv(
                self.hve_incremental_path, index=False
            )
        else:
            pd.DataFrame(columns=cols).to_csv(self.hve_incremental_path, index=False)

        print(f"   HVE incremental file updated: {len(rows)} events — {self.hve_incremental_path}")

    # ------------------------------------------------------------------
    # State file (tracks last processed date)
    # ------------------------------------------------------------------

    def get_last_processed_date(self) -> Optional[date]:
        if self.state_path.exists():
            try:
                return datetime.strptime(self.state_path.read_text().strip(), '%Y-%m-%d').date()
            except Exception:
                pass
        return None

    def save_last_processed_date(self, d: date):
        self.state_path.write_text(d.strftime('%Y-%m-%d'))

    # ------------------------------------------------------------------
    # Ticker filter
    # ------------------------------------------------------------------

    def _load_allowed_tickers(self) -> Optional[set]:
        """Return set of allowed tickers for current ticker_choice, or None if no filter."""
        if self.ticker_choice is None:
            return None
        ticker_file = self.base_dir / 'data' / 'tickers' / f'combined_tickers_{self.ticker_choice}.csv'
        if not ticker_file.exists():
            print(f"   WARNING: ticker file not found: {ticker_file} — no filter applied")
            return None
        try:
            tf = pd.read_csv(ticker_file)
            col = 'ticker' if 'ticker' in tf.columns else tf.columns[0]
            tickers = set(tf[col].dropna().astype(str).str.strip())
            print(f"   Ticker filter: {len(tickers)} tickers (choice={self.ticker_choice})")
            return tickers
        except Exception as e:
            print(f"   WARNING: could not load ticker filter: {e}")
            return None

    # ------------------------------------------------------------------
    # TW file discovery and parsing
    # ------------------------------------------------------------------

    def find_tw_files_since(self, since_date: Optional[date]) -> List[Tuple[date, List[Path]]]:
        """Return [(file_date, [path, ...]), ...] sorted chronologically, newer than since_date."""
        if not self.tw_files_dir.exists():
            print(f"   ERROR: TW files directory not found: {self.tw_files_dir}")
            return []

        pattern = re.compile(r'(\d{4}-\d{2}-\d{2})')
        date_files: Dict[date, List[Path]] = {}

        for f in self.tw_files_dir.iterdir():
            if f.suffix.lower() != '.csv':
                continue
            m = pattern.search(f.name)
            if not m:
                continue
            file_date = datetime.strptime(m.group(1), '%Y-%m-%d').date()
            if since_date and file_date <= since_date:
                continue
            date_files.setdefault(file_date, []).append(f)

        return sorted(date_files.items())

    def parse_tw_file(self, file_path: Path, file_date: date) -> Dict:
        """Parse one TW bulk CSV. Returns {ticker: {date, open, high, low, close, volume, market_cap}}.

        'Mkt cap' is optional — add it to your TradingView export to enable market-cap filtering.
        When present it reflects the market cap at the export date (= detection date).
        """
        ticker_data: Dict = {}
        try:
            df = pd.read_csv(file_path)
            df.columns = df.columns.str.strip()

            required = ['Symbol', 'Open 1 day', 'High 1 day', 'Low 1 day', 'Price', 'Volume 1 day']
            missing = [c for c in required if c not in df.columns]
            if missing:
                print(f"   WARNING {file_path.name}: missing columns {missing} — skipping")
                return {}

            has_mkt_cap = 'Mkt cap' in df.columns
            date_str = file_date.strftime('%Y-%m-%d')

            for _, row in df.iterrows():
                raw_ticker = row.get('Symbol')
                if pd.isna(raw_ticker):
                    continue
                ticker = str(raw_ticker).strip().replace('.', '-')
                if '/' in ticker:
                    continue

                try:
                    volume = row['Volume 1 day']
                    close  = row['Price']
                    if pd.isna(volume) or pd.isna(close):
                        continue
                    volume = int(float(volume))
                    if volume <= 0:
                        continue

                    mkt_cap = None
                    if has_mkt_cap:
                        raw_mc = row['Mkt cap']
                        if not pd.isna(raw_mc):
                            mkt_cap = float(raw_mc)

                    ticker_data[ticker] = {
                        'date':       date_str,
                        'open':       float(row['Open 1 day']) if not pd.isna(row['Open 1 day']) else None,
                        'high':       float(row['High 1 day']) if not pd.isna(row['High 1 day']) else None,
                        'low':        float(row['Low 1 day'])  if not pd.isna(row['Low 1 day'])  else None,
                        'close':      float(close),
                        'volume':     volume,
                        'market_cap': mkt_cap,
                    }
                except (ValueError, TypeError):
                    continue

        except Exception as e:
            print(f"   ERROR parsing {file_path.name}: {e}")

        return ticker_data

    # ------------------------------------------------------------------
    # Core comparison logic
    # ------------------------------------------------------------------

    def check_and_update(self, ticker_data: Dict, file_date: date,
                         allowed_tickers: Optional[set] = None) -> List[Dict]:
        """
        Compare today's volumes against the combined top-N (baseline + incremental).
        Baseline is never modified — new events go to incremental_dict only.
        Re-run safe: if today's date is already in combined, the ticker is skipped.
        """
        hits = []
        today_str = file_date.strftime('%Y-%m-%d')

        for ticker, data in ticker_data.items():
            if allowed_tickers is not None and ticker not in allowed_tickers:
                continue

            new_vol = data['volume']

            # Merge baseline + incremental, deduplicate by date, sort vol desc
            all_events = self.baseline_dict.get(ticker, []) + self.incremental_dict.get(ticker, [])
            seen: Dict[str, int] = {}
            for ev in all_events:
                d = ev['date']
                if d not in seen or ev['volume'] > seen[d]:
                    seen[d] = ev['volume']
            combined = sorted(
                [{'date': d, 'volume': v} for d, v in seen.items()],
                key=lambda x: x['volume'], reverse=True
            )[:self.top_n_hist]

            # Re-run safety: skip if today already recorded
            if any(ev['date'] == today_str for ev in combined):
                continue

            # Threshold: lowest volume in current top-N (0 if list not yet full)
            threshold = combined[-1]['volume'] if len(combined) >= self.top_n_hist else 0

            if new_vol <= threshold:
                continue

            # Find 1-based rank in combined
            rank = 1
            for ev in combined:
                if new_vol >= ev['volume']:
                    break
                rank += 1

            # What gets displaced when new entry is inserted
            new_combined = (
                combined[:rank - 1]
                + [{'date': today_str, 'volume': new_vol}]
                + combined[rank - 1:]
            )
            displaced = new_combined[self.top_n_hist] if len(new_combined) > self.top_n_hist else None

            # Record in incremental only — baseline stays read-only
            self.incremental_dict.setdefault(ticker, []).append(
                {'date': today_str, 'volume': new_vol}
            )

            # Days since all-time rank-1
            try:
                top1_date = datetime.strptime(new_combined[0]['date'], '%Y-%m-%d').date()
                days_since_top1 = (file_date - top1_date).days
            except Exception:
                days_since_top1 = None

            hits.append({
                'ticker':          ticker,
                'check_date':      today_str,
                'new_volume':      new_vol,
                'price_at_event':  data['close'],
                'market_cap':      data.get('market_cap'),
                'entered_top_n':   rank <= self.top_n_flag,
                'rank':            rank,
                'displaced_vol':   displaced['volume'] if displaced else '',
                'displaced_date':  displaced['date']   if displaced else '',
                'days_since_top1': days_since_top1
            })

        return hits

    def check_and_update_hve(self, ticker_data: Dict, file_date: date,
                              allowed_tickers: Optional[set] = None) -> List[Dict]:
        """
        Compare today's volumes against the combined all-time max (baseline + incremental).
        Simplified sibling of check_and_update(): no top-N/rank bookkeeping, just
        "did this ticker set a new all-time volume record today?"
        Baseline is never modified — new records go to hve_incremental_dict only.
        Re-run safe: if today's date is already recorded for this ticker, it's skipped.
        """
        hits = []
        today_str = file_date.strftime('%Y-%m-%d')

        for ticker, data in ticker_data.items():
            if allowed_tickers is not None and ticker not in allowed_tickers:
                continue

            new_vol = data['volume']

            prior_events = self.hve_incremental_dict.get(ticker, [])
            if any(ev['date'] == today_str for ev in prior_events):
                continue  # already recorded today (re-run safety)

            baseline_entry = self.hve_baseline_dict.get(ticker)
            baseline_max = baseline_entry['volume'] if baseline_entry else 0
            combined_max = max([baseline_max] + [ev['volume'] for ev in prior_events])

            if new_vol <= combined_max:
                continue

            self.hve_incremental_dict.setdefault(ticker, []).append(
                {'date': today_str, 'volume': new_vol}
            )

            hits.append({
                'ticker':         ticker,
                'check_date':     today_str,
                'new_volume':     new_vol,
                'price_at_event': data['close'],
                'market_cap':     data.get('market_cap'),
                'prior_max':      combined_max,
            })

        return hits

    # ------------------------------------------------------------------
    # Results output
    # ------------------------------------------------------------------

    def save_daily_snapshot(self, hits: List[Dict], file_date: date):
        """Save hits for a single trading day to its own file. Always overwrites."""
        snapshot_dir = self.output_dir / 'snapshots'
        snapshot_dir.mkdir(exist_ok=True)
        snapshot_path = snapshot_dir / f"vol_check_{file_date.strftime('%Y-%m-%d')}.csv"

        if hits:
            pd.DataFrame(hits).to_csv(snapshot_path, index=False)
        else:
            pd.DataFrame(columns=[
                'ticker', 'check_date', 'new_volume', 'price_at_event', 'market_cap',
                'entered_top_n', 'rank', 'displaced_vol', 'displaced_date', 'days_since_top1'
            ]).to_csv(snapshot_path, index=False)

        print(f"   Snapshot: {snapshot_path.name} ({len(hits)} hit(s))")

    def save_daily_log(self, ticker_data: Dict, hits: List[Dict],
                       file_date: date, allowed_tickers: Optional[set]):
        """
        Append one row per monitored ticker to daily_log.csv.
        hit=1 means the ticker beat its historical threshold today, hit=0 otherwise.
        Re-run safe: existing rows for this date are replaced.
        """
        hit_set = {h['ticker'] for h in hits}
        date_str = file_date.strftime('%Y-%m-%d')

        rows = []
        for ticker, data in ticker_data.items():
            if allowed_tickers is not None and ticker not in allowed_tickers:
                continue
            rows.append({
                'ticker': ticker,
                'date':   date_str,
                'volume': data['volume'],
                'close':  data['close'],
                'hit':    1 if ticker in hit_set else 0
            })

        if not rows:
            return

        new_df = pd.DataFrame(rows)[['ticker', 'date', 'volume', 'close', 'hit']]

        if self.daily_log_path.exists():
            existing = pd.read_csv(self.daily_log_path)
            existing = existing[existing['date'] != date_str]
            new_df = pd.concat([existing, new_df], ignore_index=True)

        new_df.sort_values(['date', 'ticker']).to_csv(self.daily_log_path, index=False)
        hits_today = sum(1 for r in rows if r['hit'])
        print(f"   Daily log: {len(rows)} tickers logged ({hits_today} hits) — {self.daily_log_path}")

    def save_results(self, hits: List[Dict]):
        """Append all hits from this run to the cumulative history file."""
        if not hits:
            print("   No volume events beat the threshold")
            return

        new_df = pd.DataFrame(hits)

        if self.results_path.exists():
            existing = pd.read_csv(self.results_path)
            new_df = pd.concat([existing, new_df], ignore_index=True)

        new_df.to_csv(self.results_path, index=False)
        entered = sum(1 for h in hits if h['entered_top_n'])
        print(f"   Cumulative log: {len(hits)} new rows | {entered} entered top-{self.top_n_flag} | {self.results_path}")

    def save_hve_daily_snapshot(self, hits: List[Dict], file_date: date):
        """Save HVE (new all-time-high) hits for a single trading day. Always overwrites."""
        snapshot_dir = self.output_dir / 'snapshots'
        snapshot_dir.mkdir(exist_ok=True)
        snapshot_path = snapshot_dir / f"HVE_check_{file_date.strftime('%Y-%m-%d')}.csv"

        if hits:
            pd.DataFrame(hits).to_csv(snapshot_path, index=False)
        else:
            pd.DataFrame(columns=[
                'ticker', 'check_date', 'new_volume', 'price_at_event', 'market_cap', 'prior_max'
            ]).to_csv(snapshot_path, index=False)

        print(f"   HVE snapshot: {snapshot_path.name} ({len(hits)} hit(s))")

    def save_hve_results(self, hits: List[Dict]):
        """Append all HVE (new all-time-high) hits from this run to the cumulative history file."""
        if not hits:
            print("   No new all-time-high volume events")
            return

        new_df = pd.DataFrame(hits)

        if self.hve_results_path.exists():
            existing = pd.read_csv(self.hve_results_path)
            new_df = pd.concat([existing, new_df], ignore_index=True)

        new_df.to_csv(self.hve_results_path, index=False)
        print(f"   HVE cumulative log: {len(hits)} new rows — {self.hve_results_path}")

    def save_hve_summary(self):
        """
        Write HVE_{timeframe}.csv: one row per ticker, current known HVE
        record (ticker, timeframe, hve_date, hve_volume, days_since_hve) --
        same shape as the pre-process HVE_{timeframe}.csv, but cheap: no
        history re-scan, just baseline ∪ incremental merged in memory.

        For each ticker, the current record is whichever is more recent:
        the newest hve_incremental_dict entry (if any -- by HVE definition
        each new entry exceeds every prior one, so the newest by date is
        also the highest by volume) or, failing that, the baseline's
        stored (date, volume).
        """
        if not self.hve_check_enabled:
            return

        today = date.today()
        rows = []
        tickers = set(self.hve_baseline_dict) | set(self.hve_incremental_dict)

        for ticker in tickers:
            incremental = self.hve_incremental_dict.get(ticker, [])
            if incremental:
                latest = max(incremental, key=lambda ev: ev['date'])
                hve_date_str, hve_volume = latest['date'], latest['volume']
            else:
                baseline_entry = self.hve_baseline_dict.get(ticker)
                if not baseline_entry or not baseline_entry.get('date'):
                    continue
                hve_date_str, hve_volume = baseline_entry['date'], baseline_entry['volume']

            try:
                hve_date_obj = datetime.strptime(hve_date_str, '%Y-%m-%d').date()
                days_since = (today - hve_date_obj).days
            except (ValueError, TypeError):
                days_since = ''

            rows.append({
                'ticker':         ticker,
                'timeframe':      self.timeframe,
                'hve_date':       hve_date_str,
                'hve_volume':     hve_volume,
                'days_since_hve': days_since,
            })

        cols = ['ticker', 'timeframe', 'hve_date', 'hve_volume', 'days_since_hve']
        if rows:
            df = pd.DataFrame(rows)[cols].sort_values('days_since_hve')
        else:
            df = pd.DataFrame(columns=cols)
        df.to_csv(self.hve_summary_path, index=False)
        print(f"   HVE summary: {len(rows)} tickers — {self.hve_summary_path}")

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    def run(self, since_date_override: Optional[str] = None):
        print(f"\n{'='*60}")
        print(f"VOL CHECKER — {self.timeframe.upper()}  [source: {self.data_source.upper()}]")
        print(f"{'='*60}")

        # ------------------------------------------------------------------
        # Load baseline (read-only) and incremental (read/write)
        # ------------------------------------------------------------------
        print(f"\n Loading baseline...")
        if not self.load_baseline():
            return
        print(f"\n Loading incremental...")
        self.load_incremental()

        # HVE (all-time record) baseline is optional -- if missing, HVE
        # checking is skipped for this run but HVD checking still proceeds.
        print(f"\n Loading HVE baseline...")
        self.hve_check_enabled = self.load_hve_baseline()
        if self.hve_check_enabled:
            print(f"\n Loading HVE incremental...")
            self.load_hve_incremental()

        # ------------------------------------------------------------------
        # Determine baseline cutoff date (hard floor — never go before this)
        # ------------------------------------------------------------------
        from src.yahoo_daily_adapter import get_baseline_cutoff_date
        baseline_cutoff = get_baseline_cutoff_date(self.baseline_dir, self.timeframe)

        # ------------------------------------------------------------------
        # Determine since_date from override or state file
        # ------------------------------------------------------------------
        override_clean = (since_date_override or '').strip().lower()
        if override_clean and override_clean != 'nan':
            user_since = datetime.strptime(override_clean, '%Y-%m-%d').date()
            print(f" Requested since: {user_since} (from config override)")
        else:
            user_since = self.get_last_processed_date()
            if user_since:
                print(f" Requested since: {user_since} (from state file)")
            else:
                user_since = None
                print(f" No state file — processing all available dates")

        # ------------------------------------------------------------------
        # Compute effective start: max(user_since, baseline_cutoff)
        # Print clear status so the user knows exactly what's happening
        # ------------------------------------------------------------------
        print(f"\n{'─'*50}")
        if baseline_cutoff:
            print(f" Baseline cutoff  : {baseline_cutoff}  (from baseline_metadata / HVD CSV)")
        else:
            print(f" Baseline cutoff  : unknown (no metadata / HVD CSV found)")

        print(f" Last processed   : {user_since or 'none'}")

        if baseline_cutoff and user_since and user_since < baseline_cutoff:
            print(f" WARNING: requested since-date ({user_since}) predates the baseline "
                  f"({baseline_cutoff}). Clamping to baseline cutoff to avoid re-processing.")
            effective_since = baseline_cutoff
        elif baseline_cutoff and user_since is None:
            effective_since = baseline_cutoff
        else:
            effective_since = user_since

        print(f" Effective start  : {effective_since or 'beginning of available data'}")
        print(f"{'─'*50}")

        # ------------------------------------------------------------------
        # Find dates to process — branching on data source
        # ------------------------------------------------------------------
        if self.data_source == 'tradingview':
            self._run_tradingview(effective_since)
        else:
            self._run_yahoo(effective_since)

        # Refresh the per-ticker HVE summary regardless of whether new
        # dates were found this run, so days_since_hve stays current.
        self.save_hve_summary()

    # ------------------------------------------------------------------
    # TradingView source path
    # ------------------------------------------------------------------

    def _run_tradingview(self, effective_since: Optional[date]):
        print(f"\n Scanning TW files: {self.tw_files_dir}")
        files_to_process = self.find_tw_files_since(effective_since)

        if not files_to_process:
            print(f" No new TW files found")
            return

        print(f" Found {len(files_to_process)} date(s) to process:")
        for d, paths in files_to_process:
            print(f"   {d}: {[p.name for p in sorted(paths)]}")

        allowed_tickers = self._load_allowed_tickers()
        all_hits: List[Dict] = []
        all_hve_hits: List[Dict] = []
        last_processed: Optional[date] = None

        for file_date, file_paths in files_to_process:
            print(f"\n --- {file_date} ---")
            ticker_data: Dict = {}
            for fp in sorted(file_paths):
                parsed = self.parse_tw_file(fp, file_date)
                ticker_data.update(parsed)
                print(f"   Parsed {fp.name}: {len(parsed)} tickers")

            hits = self.check_and_update(ticker_data, file_date, allowed_tickers)
            self.save_daily_snapshot(hits, file_date)
            self.save_daily_log(ticker_data, hits, file_date, allowed_tickers)
            all_hits.extend(hits)
            last_processed = file_date

            top_n_hits = [h for h in hits if h['entered_top_n']]
            print(f"   Beat threshold: {len(hits)} | Entered top-{self.top_n_flag}: {len(top_n_hits)}")

            if self.hve_check_enabled:
                hve_hits = self.check_and_update_hve(ticker_data, file_date, allowed_tickers)
                self.save_hve_daily_snapshot(hve_hits, file_date)
                all_hve_hits.extend(hve_hits)
                print(f"   New all-time highs (HVE): {len(hve_hits)}")

        self._finalize(all_hits, last_processed, all_hve_hits)

    # ------------------------------------------------------------------
    # Yahoo source path
    # ------------------------------------------------------------------

    def _run_yahoo(self, effective_since: Optional[date]):
        from src.yahoo_daily_adapter import find_trading_dates_since, load_days

        if not self.yahoo_data_dir.exists():
            print(f"   ERROR: Yahoo data directory not found: {self.yahoo_data_dir}")
            return

        print(f"\n Scanning Yahoo data: {self.yahoo_data_dir}")
        dates_to_process = find_trading_dates_since(effective_since, self.yahoo_data_dir)

        if not dates_to_process:
            print(f" No new Yahoo dates found")
            return

        print(f" Found {len(dates_to_process)} trading date(s) to process "
              f"({dates_to_process[0]} → {dates_to_process[-1]})")

        # Determine tickers to load
        allowed_tickers = self._load_allowed_tickers()
        if allowed_tickers is not None:
            tickers_to_load = list(allowed_tickers)
        else:
            # Fall back to all tickers in the baseline
            tickers_to_load = list(self.baseline_dict.keys())
            print(f"   No ticker filter — using {len(tickers_to_load)} baseline tickers")

        # Batch-load all dates in a single pass through ticker files (Colab-friendly)
        print(f"\n Loading Yahoo data for {len(dates_to_process)} date(s) "
              f"× {len(tickers_to_load)} tickers...")
        all_day_data = load_days(dates_to_process, tickers_to_load, self.yahoo_data_dir)

        all_hits: List[Dict] = []
        all_hve_hits: List[Dict] = []
        last_processed: Optional[date] = None

        for file_date in sorted(dates_to_process):
            ticker_data = all_day_data.get(file_date, {})
            print(f"\n --- {file_date} --- ({len(ticker_data)} tickers with data)")

            hits = self.check_and_update(ticker_data, file_date, allowed_tickers)
            self.save_daily_snapshot(hits, file_date)
            self.save_daily_log(ticker_data, hits, file_date, allowed_tickers)
            all_hits.extend(hits)
            last_processed = file_date

            top_n_hits = [h for h in hits if h['entered_top_n']]
            print(f"   Beat threshold: {len(hits)} | Entered top-{self.top_n_flag}: {len(top_n_hits)}")

            if self.hve_check_enabled:
                hve_hits = self.check_and_update_hve(ticker_data, file_date, allowed_tickers)
                self.save_hve_daily_snapshot(hve_hits, file_date)
                all_hve_hits.extend(hve_hits)
                print(f"   New all-time highs (HVE): {len(hve_hits)}")

        self._finalize(all_hits, last_processed, all_hve_hits)

    # ------------------------------------------------------------------
    # Shared finalization
    # ------------------------------------------------------------------

    def _finalize(self, all_hits: List[Dict], last_processed: Optional[date],
                  all_hve_hits: Optional[List[Dict]] = None):
        all_hve_hits = all_hve_hits or []

        print(f"\n Saving...")
        self.save_incremental()
        self.save_results(all_hits)
        if self.hve_check_enabled:
            self.save_hve_incremental()
            self.save_hve_results(all_hve_hits)
        if last_processed:
            self.save_last_processed_date(last_processed)

        top_n_hits = [h for h in all_hits if h['entered_top_n']]
        print(f"\n{'='*60}")
        print(f" SUMMARY")
        print(f"{'='*60}")
        print(f"   Source          : {self.data_source.upper()}")
        print(f"   Beat threshold  : {len(all_hits)}")
        print(f"   Entered top-{self.top_n_flag:2d}  : {len(top_n_hits)}")
        if self.hve_check_enabled:
            print(f"   New all-time highs (HVE) : {len(all_hve_hits)}")

        if top_n_hits:
            print(f"\n   Top-{self.top_n_flag} hits (sorted by rank):")
            for h in sorted(top_n_hits, key=lambda x: (x['check_date'], x['rank']))[:20]:
                print(
                    f"   {h['check_date']} | Rank {h['rank']:2d} | "
                    f"{h['ticker']:<8s} | vol={h['new_volume']:>15,.0f} | "
                    f"close={h['price_at_event']:>8.2f}"
                )
