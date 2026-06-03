"""
Volume Daily Checker
====================

Compares each day's volume against the stored HVD top-N baseline
(HVD_historical_daily.csv) and flags tickers that enter the top positions.

Supports two data sources:
  tradingview  — TradingView bulk CSV files (one file per trading day)
  yahoo        — Per-ticker Yahoo Finance CSVs (from downloadData_v1)

Inputs:
  - results/hve_results/HVD_historical_daily.csv  (baseline, READ-ONLY)
  - results/hve_results/baseline_metadata.json    (cutoff date, READ-ONLY)

  For TradingView source:
  - tw_files/daily/*.csv  (one bulk file per trading day)

  For Yahoo source:
  - downloadData_v1/data/market_data/daily/<TICKER>.csv  (per-ticker files)

Outputs:
  - results/vol_top20/vol_check_results.csv  (appended each run)
  - results/vol_top20/last_processed.txt     (state: last processed date)
  - results/vol_top20/HVD_incremental.csv    (new events since baseline)
  - results/vol_top20/daily/<date>.csv       (per-day snapshots)
  - results/vol_top20/daily_log.csv          (full daily log)

  The baseline is never modified during daily runs.
  Delete HVD_incremental.csv and re-run to safely reprocess any date range.

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


class VolDailyChecker:

    def __init__(self, config, user_config):
        self.base_dir = Path(__file__).resolve().parent.parent
        self.ticker_choice = getattr(user_config, 'ticker_choice', None)

        # Baseline file (produced by pre-processor HVD export, read-only during daily runs)
        self.baseline_path = (
            self.base_dir / 'results' / 'hve_results' / 'HVD_historical_daily.csv'
        )
        self.baseline_dir = self.baseline_path.parent

        # ------------------------------------------------------------------
        # Data source selection
        # ------------------------------------------------------------------
        self.data_source = getattr(user_config, 'vol_checker_data_source', 'tradingview').strip().lower()
        if self.data_source not in ('tradingview', 'yahoo'):
            print(f"   WARNING: unknown vol_checker_data_source '{self.data_source}' — falling back to tradingview")
            self.data_source = 'tradingview'

        # ------------------------------------------------------------------
        # TradingView bulk files directory
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
        # Yahoo per-ticker data directory (resolved by user_defined_data)
        # ------------------------------------------------------------------
        yahoo_dir_resolved = getattr(user_config, 'vol_checker_yahoo_data_dir', None)
        if yahoo_dir_resolved:
            self.yahoo_data_dir = Path(yahoo_dir_resolved)
        else:
            # Fallback default
            self.yahoo_data_dir = (
                self.base_dir / '../downloadData_v1/data/market_data/daily/'
            ).resolve()

        # ------------------------------------------------------------------
        # Output
        # ------------------------------------------------------------------
        self.output_dir = self.base_dir / 'results' / 'vol_top20'
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results_path     = self.output_dir / 'vol_check_results.csv'
        self.state_path       = self.output_dir / 'last_processed.txt'
        self.incremental_path = self.output_dir / 'HVD_incremental.csv'
        self.daily_log_path   = self.output_dir / 'daily_log.csv'

        # How many top positions to flag (default 6)
        self.top_n_flag = int(getattr(user_config, 'vol_checker_top_n_flag', 6))

        # State filled by load_baseline() / load_incremental()
        self.baseline_dict:    Dict[str, List[Dict]] = {}
        self.incremental_dict: Dict[str, List[Dict]] = {}
        self.top_n_hist: int = 0

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

    # ------------------------------------------------------------------
    # Results output
    # ------------------------------------------------------------------

    def save_daily_snapshot(self, hits: List[Dict], file_date: date):
        """Save hits for a single trading day to its own file. Always overwrites."""
        snapshot_dir = self.output_dir / 'daily'
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

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    def run(self, since_date_override: Optional[str] = None):
        print(f"\n{'='*60}")
        print(f"VOL DAILY CHECKER  [source: {self.data_source.upper()}]")
        print(f"{'='*60}")

        # ------------------------------------------------------------------
        # Load baseline (read-only) and incremental (read/write)
        # ------------------------------------------------------------------
        print(f"\n Loading baseline...")
        if not self.load_baseline():
            return
        print(f"\n Loading incremental...")
        self.load_incremental()

        # ------------------------------------------------------------------
        # Determine baseline cutoff date (hard floor — never go before this)
        # ------------------------------------------------------------------
        from src.yahoo_daily_adapter import get_baseline_cutoff_date
        baseline_cutoff = get_baseline_cutoff_date(self.baseline_dir)

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

        self._finalize(all_hits, last_processed)

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

        self._finalize(all_hits, last_processed)

    # ------------------------------------------------------------------
    # Shared finalization
    # ------------------------------------------------------------------

    def _finalize(self, all_hits: List[Dict], last_processed: Optional[date]):
        print(f"\n Saving...")
        self.save_incremental()
        self.save_results(all_hits)
        if last_processed:
            self.save_last_processed_date(last_processed)

        top_n_hits = [h for h in all_hits if h['entered_top_n']]
        print(f"\n{'='*60}")
        print(f" SUMMARY")
        print(f"{'='*60}")
        print(f"   Source          : {self.data_source.upper()}")
        print(f"   Beat threshold  : {len(all_hits)}")
        print(f"   Entered top-{self.top_n_flag:2d}  : {len(top_n_hits)}")

        if top_n_hits:
            print(f"\n   Top-{self.top_n_flag} hits (sorted by rank):")
            for h in sorted(top_n_hits, key=lambda x: (x['check_date'], x['rank']))[:20]:
                print(
                    f"   {h['check_date']} | Rank {h['rank']:2d} | "
                    f"{h['ticker']:<8s} | vol={h['new_volume']:>15,.0f} | "
                    f"close={h['new_close']:>8.2f}"
                )
