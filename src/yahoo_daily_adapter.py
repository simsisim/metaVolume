"""
Yahoo Daily Adapter
===================

Adapts per-ticker Yahoo Finance CSV files (from downloadData_v1) to the same
dict format that VolDailyChecker.check_and_update() consumes.

Also provides the cutoff-date helper so the checker never re-processes data
already baked into the HVD baseline.

Yahoo CSV format (per-ticker files, one file per ticker):
  Date,Open,High,Low,Close,Volume,...
  2020-01-02 00:00:00-05:00,71.40,...
  Date column contains a timezone offset — stripped during parsing.
  Filename == ticker symbol (e.g. AAPL.csv).

Key design: load_days() opens each ticker file only once and extracts all
requested dates in a single pass — O(n_tickers) file opens regardless of how
many dates are requested.  This matters on slow mounts (Colab/Google Drive).
"""

import json
import logging
import re
import pandas as pd
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from src.data_reader import BatchDataSupplementer, _batch_dir_for

logger = logging.getLogger(__name__)

_REFERENCE_TICKERS = ['SPY', 'AAPL', 'MSFT', 'QQQ']
_BATCH_DATE_RE = re.compile(r'prices_1d_(\d{4}-\d{2}-\d{2})\.csv$')


# ---------------------------------------------------------------------------
# Baseline cutoff helper
# ---------------------------------------------------------------------------

def get_baseline_cutoff_date(baseline_dir: Path) -> Optional[date]:
    """
    Return the last date covered by the HVD baseline.

    Checks baseline_metadata.json first (written by hvd_historical_exporter).
    Falls back to scanning HVD_historical_daily.csv for the maximum date
    across all HVD_date_* columns.  Returns None if neither source is found.
    """
    metadata_path = baseline_dir / 'baseline_metadata.json'
    if metadata_path.exists():
        try:
            data = json.loads(metadata_path.read_text())
            cutoff_str = data.get('baseline_as_of_date', '')
            if cutoff_str:
                return datetime.strptime(cutoff_str, '%Y-%m-%d').date()
        except Exception as e:
            logger.warning(f"Could not read baseline_metadata.json: {e}")

    # Fallback: derive from HVD CSV
    hvd_csv = baseline_dir / 'HVD_historical_daily.csv'
    if hvd_csv.exists():
        try:
            df = pd.read_csv(hvd_csv)
            date_cols = [c for c in df.columns if c.startswith('HVD_date_')]
            all_dates = []
            for col in date_cols:
                parsed = pd.to_datetime(df[col], errors='coerce').dropna()
                all_dates.extend(parsed.dt.date.tolist())
            if all_dates:
                cutoff = max(all_dates)
                logger.info(f"Derived baseline cutoff from HVD CSV: {cutoff}")
                return cutoff
        except Exception as e:
            logger.warning(f"Could not derive cutoff from HVD CSV: {e}")

    return None


# ---------------------------------------------------------------------------
# Trading-date discovery
# ---------------------------------------------------------------------------

# A comprehensive batch daily file covers thousands of tickers (hundreds of
# KB+). Stray near-empty files (e.g. a handful of bytes for a single ticker)
# turn up for non-trading days (weekends/holidays) or partial test runs --
# treating those as real trading dates would surface a checker cycle with
# "0 tickers with data" for every real ticker set. 20KB comfortably clears a
# single-row file while staying well under any real multi-ticker snapshot.
_MIN_BATCH_FILE_BYTES = 20_000


def _batch_dates_since(since_date: Optional[date], yahoo_data_dir: Path) -> List[date]:
    """
    Trading dates available in market_data_batch/{timeframe}/prices_1d_*.csv
    after since_date -- one file per trading day, so the filename date *is*
    the trading date (no need to parse the file, just check it's not a stray).
    """
    batch_dir = _batch_dir_for(yahoo_data_dir)
    if not batch_dir.exists():
        return []
    dates = []
    for f in batch_dir.glob('prices_1d_*.csv'):
        m = _BATCH_DATE_RE.search(f.name)
        if not m:
            continue
        if f.stat().st_size < _MIN_BATCH_FILE_BYTES:
            logger.debug(f"Skipping stray/near-empty batch file: {f.name}")
            continue
        d = datetime.strptime(m.group(1), '%Y-%m-%d').date()
        if not since_date or d > since_date:
            dates.append(d)
    return sorted(dates)


def find_trading_dates_since(
    since_date: Optional[date],
    yahoo_data_dir: Path,
    reference_tickers: Optional[List[str]] = None,
) -> List[date]:
    """
    Return sorted list of trading dates available after since_date, unioning
    two sources: the flat per-ticker Yahoo files (reference tickers) and
    market_data_batch/ (fast pipeline, usually more current -- see
    downloadData_v1/batchJob_calc). Either source alone may be stale/absent;
    the union is what's actually available to check.
    """
    if reference_tickers is None:
        reference_tickers = _REFERENCE_TICKERS

    flat_dates: List[date] = []
    found_reference_file = False
    for ticker in reference_tickers:
        ref_file = yahoo_data_dir / f'{ticker}.csv'
        if not ref_file.exists():
            continue
        try:
            df = pd.read_csv(ref_file, usecols=[0], header=0)
            df.columns = ['date_raw']
            # Strip timezone offset (e.g. "2020-01-02 00:00:00-05:00" → "2020-01-02")
            df['date_parsed'] = pd.to_datetime(
                df['date_raw'].astype(str).str.split(' ').str[0],
                errors='coerce',
            ).dt.date
            df = df.dropna(subset=['date_parsed'])
            dates = sorted(df['date_parsed'].tolist())
            if since_date:
                dates = [d for d in dates if d > since_date]
            logger.info(
                f"Found {len(dates)} trading dates after {since_date} "
                f"(reference ticker: {ticker})"
            )
            flat_dates = dates
            found_reference_file = True
            break
        except Exception as e:
            logger.warning(f"Could not read reference ticker {ticker}: {e}")

    if not found_reference_file:
        logger.warning(f"No usable reference ticker file found in {yahoo_data_dir}")

    batch_dates = _batch_dates_since(since_date, yahoo_data_dir)
    if batch_dates:
        logger.info(f"Found {len(batch_dates)} trading date(s) after {since_date} "
                     f"in market_data_batch/")

    return sorted(set(flat_dates) | set(batch_dates))


# ---------------------------------------------------------------------------
# Bulk loader — one file open per ticker regardless of date count
# ---------------------------------------------------------------------------

def load_days(
    target_dates: List[date],
    tickers: List[str],
    yahoo_data_dir: Path,
) -> Dict[date, Dict]:
    """
    Load OHLCV data for multiple dates across all tickers in a single pass.

    Opens each ticker file once and extracts rows for all requested dates.

    Returns:
        {target_date: {ticker: {date, open, high, low, close, volume}}}
        matching the dict format of VolDailyChecker.parse_tw_file().

    Tickers with no file or no matching rows are silently omitted.
    """
    if not target_dates or not tickers:
        return {}

    target_strs = {d.strftime('%Y-%m-%d') for d in target_dates}
    result: Dict[date, Dict] = {d: {} for d in target_dates}
    date_index = {d.strftime('%Y-%m-%d'): d for d in target_dates}

    loaded = 0
    for ticker in tickers:
        # Yahoo stores class-share tickers with '.' (e.g. BRK.A).
        # Internally we use '-' (e.g. BRK-A).  Try both.
        candidates = [ticker, ticker.replace('-', '.')]
        file_path = None
        for name in candidates:
            p = yahoo_data_dir / f'{name}.csv'
            if p.exists():
                file_path = p
                break

        if file_path is None:
            continue

        try:
            df = pd.read_csv(
                file_path,
                usecols=lambda c: c in ('Date', 'Open', 'High', 'Low', 'Close', 'Volume', 'marketCap'),
            )
            # Normalize date column
            df['Date'] = df['Date'].astype(str).str.split(' ').str[0]
            # Filter to requested dates only
            df = df[df['Date'].isin(target_strs)]
            if df.empty:
                continue

            has_mkt_cap = 'marketCap' in df.columns

            for _, row in df.iterrows():
                date_str = row['Date']
                if date_str not in date_index:
                    continue
                target_date = date_index[date_str]

                volume = row.get('Volume', None)
                close = row.get('Close', None)
                if pd.isna(volume) or pd.isna(close):
                    continue
                volume = int(float(volume))
                if volume <= 0:
                    continue

                mkt_cap = None
                if has_mkt_cap:
                    raw_mc = row.get('marketCap', None)
                    if raw_mc is not None and not pd.isna(raw_mc):
                        mkt_cap = float(raw_mc)

                result[target_date][ticker] = {
                    'date':       date_str,
                    'open':       float(row['Open']) if 'Open' in row.index and not pd.isna(row['Open']) else None,
                    'high':       float(row['High']) if 'High' in row.index and not pd.isna(row['High']) else None,
                    'low':        float(row['Low'])  if 'Low'  in row.index and not pd.isna(row['Low'])  else None,
                    'close':      float(close),
                    'volume':     volume,
                    'market_cap': mkt_cap,
                }
            loaded += 1

        except Exception as e:
            logger.debug(f"Skipping {ticker}: {e}")

    logger.info(f"Loaded Yahoo data: {loaded}/{len(tickers)} ticker files, "
                f"{len(target_dates)} date(s)")

    # Fill any (date, ticker) still missing (flat file stale/absent for that
    # date) from market_data_batch/ -- the fast pipeline usually has today's
    # bar when the slow per-ticker files don't yet.
    missing_tickers = [t for t in tickers if any(t not in result[d] for d in target_dates)]
    if missing_tickers:
        sup = BatchDataSupplementer(_batch_dir_for(yahoo_data_dir))
        sup.load()
        before = (min(target_dates) - timedelta(days=1)).strftime('%Y-%m-%d')
        batch_filled = 0
        for ticker in missing_tickers:
            batch_rows = sup.get_rows(ticker, before)
            if batch_rows is None:
                continue
            for date_str, row in batch_rows.iterrows():
                if date_str not in date_index:
                    continue
                target_date = date_index[date_str]
                if ticker in result[target_date]:
                    continue  # flat file already covered this date
                volume = row.get('Volume')
                close = row.get('Close')
                if pd.isna(volume) or pd.isna(close) or float(volume) <= 0:
                    continue
                result[target_date][ticker] = {
                    'date':       date_str,
                    'open':       float(row['Open']) if not pd.isna(row['Open']) else None,
                    'high':       float(row['High']) if not pd.isna(row['High']) else None,
                    'low':        float(row['Low'])  if not pd.isna(row['Low'])  else None,
                    'close':      float(close),
                    'volume':     int(float(volume)),
                    'market_cap': None,
                }
                batch_filled += 1
        if batch_filled:
            logger.info(f"Filled {batch_filled} ticker-date(s) from market_data_batch/")

    return result
