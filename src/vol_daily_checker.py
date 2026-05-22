"""
Volume Daily Checker
====================

Compares each day's volume from TradingView bulk CSV files against the stored
HVD top-N baseline (HVD_historical_daily.csv) and flags tickers that enter
the top positions.

Inputs:
  - HVE_data_for_preload/HVD_historical_daily.csv  (baseline, wide format)
  - tw_files/daily/*.csv  (TradingView bulk exports, one file per trading day)

Outputs:
  - results/vol_top20/vol_check_results.csv  (appended each run)
  - results/vol_top20/last_processed.txt     (state: last processed TW date)
  - HVE_data_for_preload/HVD_historical_daily.csv  (updated in place)

TW bulk file format (columns that matter):
  Symbol, Open 1 day, High 1 day, Low 1 day, Price (=Close), Volume 1 day
  Date is NOT in the file — extracted from filename (*_YYYY-MM-DD.csv)
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

        # Baseline file (produced by HVD historical export, updated here)
        self.baseline_path = (
            self.base_dir / 'HVE_data_for_preload' / 'HVD_historical_daily.csv'
        )

        # TW bulk files directory — may be relative to base_dir or absolute
        tw_dir_str = getattr(
            user_config,
            'vol_checker_tw_files_dir',
            '../downloadData_v1/data/tw_files/daily/'
        )
        tw_dir = Path(tw_dir_str)
        if not tw_dir.is_absolute():
            tw_dir = (self.base_dir / tw_dir).resolve()
        self.tw_files_dir = tw_dir

        # Output
        self.output_dir = self.base_dir / 'results' / 'vol_top20'
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results_path = self.output_dir / 'vol_check_results.csv'
        self.state_path  = self.output_dir / 'last_processed.txt'

        # How many top positions to flag (default 6)
        self.top_n_flag = int(getattr(user_config, 'vol_checker_top_n_flag', 6))

        # State filled by load_baseline()
        self.baseline_dict: Dict[str, List[Dict]] = {}
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

    def save_baseline(self):
        rows = []
        for ticker, events in self.baseline_dict.items():
            row = {'Symbol': ticker, 'timeframe': 'daily'}
            for i, ev in enumerate(events, 1):
                row[f'HVD_date_{i}'] = ev['date']
                row[f'HVD_vol_{i}']  = ev['volume']
            for i in range(len(events) + 1, self.top_n_hist + 1):
                row[f'HVD_date_{i}'] = ''
                row[f'HVD_vol_{i}']  = ''
            rows.append(row)

        cols = ['Symbol', 'timeframe']
        for i in range(1, self.top_n_hist + 1):
            cols += [f'HVD_date_{i}', f'HVD_vol_{i}']

        pd.DataFrame(rows)[cols].to_csv(self.baseline_path, index=False)
        print(f"   Baseline updated: {self.baseline_path}")

    # ------------------------------------------------------------------
    # State file (tracks last processed TW date)
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
    # TW file discovery
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

    # ------------------------------------------------------------------
    # TW bulk file parser (ported from downloadData_v1, no modifications there)
    # ------------------------------------------------------------------

    def parse_tw_file(self, file_path: Path, file_date: date) -> Dict:
        """Parse one TW bulk CSV. Returns {ticker: {date, open, high, low, close, volume}}."""
        ticker_data: Dict = {}
        try:
            df = pd.read_csv(file_path)
            df.columns = df.columns.str.strip()

            required = ['Symbol', 'Open 1 day', 'High 1 day', 'Low 1 day', 'Price', 'Volume 1 day']
            missing = [c for c in required if c not in df.columns]
            if missing:
                print(f"   WARNING {file_path.name}: missing columns {missing} — skipping")
                return {}

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
                    ticker_data[ticker] = {
                        'date':   date_str,
                        'open':   float(row['Open 1 day'])  if not pd.isna(row['Open 1 day'])  else None,
                        'high':   float(row['High 1 day'])  if not pd.isna(row['High 1 day'])  else None,
                        'low':    float(row['Low 1 day'])   if not pd.isna(row['Low 1 day'])   else None,
                        'close':  float(close),
                        'volume': volume
                    }
                except (ValueError, TypeError):
                    continue

        except Exception as e:
            print(f"   ERROR parsing {file_path.name}: {e}")

        return ticker_data

    # ------------------------------------------------------------------
    # Core comparison logic
    # ------------------------------------------------------------------

    def check_and_update(self, ticker_data: Dict, file_date: date) -> List[Dict]:
        """
        For each ticker in ticker_data, compare volume against baseline.
        Update baseline in memory. Return list of hit dicts.
        Baseline is updated regardless of top_n_flag so it stays accurate.
        """
        hits = []
        today_str = file_date.strftime('%Y-%m-%d')

        for ticker, data in ticker_data.items():
            if ticker not in self.baseline_dict:
                continue

            events  = self.baseline_dict[ticker]
            new_vol = data['volume']

            if not events:
                continue

            # Threshold: lowest volume currently in the top-N list
            threshold = events[-1]['volume'] if len(events) >= self.top_n_hist else 0

            if new_vol <= threshold:
                continue

            # Find 1-based rank
            rank = 1
            for ev in events:
                if new_vol >= ev['volume']:
                    break
                rank += 1

            # What gets displaced (pushed out of top-N)
            displaced = events[-1] if len(events) >= self.top_n_hist else None

            # Insert and trim
            events.insert(rank - 1, {'date': today_str, 'volume': new_vol})
            self.baseline_dict[ticker] = events[:self.top_n_hist]

            # Days since all-time rank-1
            try:
                top1_date = datetime.strptime(self.baseline_dict[ticker][0]['date'], '%Y-%m-%d').date()
                days_since_top1 = (file_date - top1_date).days
            except Exception:
                days_since_top1 = None

            hits.append({
                'ticker':          ticker,
                'check_date':      today_str,
                'new_volume':      new_vol,
                'new_close':       data['close'],
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
            # Write empty file with headers so the date is still recorded
            pd.DataFrame(columns=[
                'ticker', 'check_date', 'new_volume', 'new_close',
                'entered_top_n', 'rank', 'displaced_vol', 'displaced_date', 'days_since_top1'
            ]).to_csv(snapshot_path, index=False)

        print(f"   Snapshot: {snapshot_path.name} ({len(hits)} hit(s))")

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
        print(f"VOL DAILY CHECKER")
        print(f"{'='*60}")

        # Load baseline
        print(f"\n Loading baseline...")
        if not self.load_baseline():
            return

        # Determine since_date
        # Treat blank, whitespace, or 'nan' (pandas NaN-as-string) as "no override"
        override_clean = (since_date_override or '').strip().lower()
        if override_clean and override_clean != 'nan':
            since_date = datetime.strptime(override_clean, '%Y-%m-%d').date()
            print(f" Processing TW files since: {since_date} (from config override)")
        else:
            since_date = self.get_last_processed_date()
            if since_date:
                print(f" Processing TW files since: {since_date} (from state file)")
            else:
                print(f" No state file — processing ALL TW files in directory")

        # Find TW files
        print(f"\n Scanning: {self.tw_files_dir}")
        files_to_process = self.find_tw_files_since(since_date)

        if not files_to_process:
            print(f" No new TW files found")
            return

        print(f" Found {len(files_to_process)} date(s) to process:")
        for d, paths in files_to_process:
            print(f"   {d}: {[p.name for p in sorted(paths)]}")

        # Process each date chronologically
        all_hits: List[Dict] = []
        last_processed: Optional[date] = None

        for file_date, file_paths in files_to_process:
            print(f"\n --- {file_date} ---")

            # Merge stocks + ETFs files for this date
            ticker_data: Dict = {}
            for fp in sorted(file_paths):
                parsed = self.parse_tw_file(fp, file_date)
                ticker_data.update(parsed)
                print(f"   Parsed {fp.name}: {len(parsed)} tickers")

            # Compare against baseline (baseline updated in memory after each date)
            hits = self.check_and_update(ticker_data, file_date)
            self.save_daily_snapshot(hits, file_date)
            all_hits.extend(hits)
            last_processed = file_date

            top_n_hits = [h for h in hits if h['entered_top_n']]
            print(f"   Beat threshold: {len(hits)} | Entered top-{self.top_n_flag}: {len(top_n_hits)}")

        # Persist
        print(f"\n Saving...")
        self.save_baseline()
        self.save_results(all_hits)
        if last_processed:
            self.save_last_processed_date(last_processed)

        # Summary
        top_n_hits = [h for h in all_hits if h['entered_top_n']]
        print(f"\n{'='*60}")
        print(f" SUMMARY")
        print(f"{'='*60}")
        print(f"   Dates processed : {len(files_to_process)}")
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
