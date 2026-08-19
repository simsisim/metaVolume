"""
Data Reader for Post-Processing Financial Market Data
==================================================

This module handles reading historical market data from local CSV files
and provides utilities for batch processing and data validation.

Based on the original data_reader.py from the old model with enhancements
for ticker info reading and better error handling.

BatchDataSupplementer / read_ticker_ohlcv_raw below are a trimmed port of
marketHealth/src/data_reader.py (itself ported from metaData_v1): they
supplement downloadData_v1's per-ticker market_data/ files -- which are only
refreshed by the slow --hist-data pipeline and can go stale for weeks --
with newer rows from market_data_batch/{timeframe}/prices_*.csv, the
fast/gap-fill pipeline (see downloadData_v1/batchJob_calc). Batch data is
never written to disk here; it's overlaid in memory only, so market_data/
stays the untouched source of truth.
"""

import pandas as pd
import os
from pathlib import Path
from typing import List, Dict, Optional, Generator, Tuple
import logging

logger = logging.getLogger(__name__)


class BatchDataSupplementer:
    """
    Loads downloadData_v1's fast-batch price files
    (market_data_batch/{timeframe}/prices_{interval}_YYYY-MM-DD.csv) and
    supplies rows newer than a given cutoff to append onto a ticker's
    per-ticker DataFrame in read_ticker_ohlcv_raw().

    Usage:
        sup = BatchDataSupplementer(batch_dir)
        sup.load()                          # once
        rows = sup.get_rows('AAPL', after)  # per ticker, per call
    """

    def __init__(self, batch_dir: Path):
        self.batch_dir = Path(batch_dir)
        self._data: Dict[str, list] = {}  # {SYMBOL: [{date, Open, High, Low, Close, Volume}]}
        self._loaded = False

    def load(self) -> int:
        """Load every prices_*.csv in batch_dir. Returns number of symbols loaded."""
        if not self.batch_dir.exists():
            self._loaded = True
            return 0

        files_loaded = 0
        for f in sorted(self.batch_dir.glob('prices_*.csv')):
            try:
                df = pd.read_csv(f)
                required = {'Date', 'Symbol', 'Open', 'High', 'Low', 'Close', 'Volume'}
                if not required.issubset(df.columns):
                    logger.warning(f"Batch file {f.name} missing columns, skipping")
                    continue
                for _, row in df.iterrows():
                    sym = str(row['Symbol']).upper()
                    self._data.setdefault(sym, []).append({
                        'date':   str(row['Date']),
                        'Open':   float(row['Open'])   if pd.notna(row['Open'])   else None,
                        'High':   float(row['High'])   if pd.notna(row['High'])   else None,
                        'Low':    float(row['Low'])    if pd.notna(row['Low'])    else None,
                        'Close':  float(row['Close'])  if pd.notna(row['Close'])  else None,
                        'Volume': float(row['Volume']) if pd.notna(row['Volume']) else 0.0,
                    })
                files_loaded += 1
            except Exception as e:
                logger.warning(f"Could not load batch file {f.name}: {e}")

        for sym in self._data:
            self._data[sym].sort(key=lambda r: r['date'])

        self._loaded = True
        total_syms = len(self._data)
        if files_loaded:
            logger.info(
                f"BatchDataSupplementer: {files_loaded} file(s) loaded, "
                f"{total_syms} symbols, dir={self.batch_dir}"
            )
        return total_syms

    def get_rows(self, ticker: str, after_date: str) -> Optional[pd.DataFrame]:
        """
        Rows with date strictly after after_date, both compared as plain
        strings -- market_data/'s raw dates are tz-suffixed ("2026-07-14
        00:00:00-04:00") and batch dates are plain ("2026-07-14"), but both
        are ISO-prefixed so lexicographic string comparison sorts them
        correctly without parsing. A batch row for a date already covered by
        market_data/ compares as NOT newer (a plain "2026-07-31" sorts
        before the longer "2026-07-31 00:00:00-04:00" as a string prefix),
        so it's excluded rather than duplicating/overwriting an
        already-authoritative row.
        """
        if not self._loaded or not self._data:
            return None
        sym = ticker.upper()
        rows = (
            self._data.get(sym)
            or self._data.get(sym.replace('.', '-'))  # BRK.B -> BRK-B (yf format)
            or self._data.get(sym.replace('-', '.'))  # BRK-B -> BRK.B (tv format)
        )
        if not rows:
            return None
        filtered = [r for r in rows if r['date'] > after_date]
        if not filtered:
            return None
        df = pd.DataFrame(filtered).set_index('date')
        df.index.name = 'Date'
        return df


_batch_supplementer_cache: Dict[str, BatchDataSupplementer] = {}


def _batch_dir_for(market_data_dir: Path) -> Path:
    """market_data/{timeframe} -> market_data_batch/{timeframe}, sibling-directory convention."""
    return market_data_dir.parent.parent / 'market_data_batch' / market_data_dir.name


def _get_batch_supplementer(market_data_dir: Path) -> BatchDataSupplementer:
    """Lazily load and cache one BatchDataSupplementer per batch dir for the life of the process."""
    batch_dir = _batch_dir_for(market_data_dir)
    key = str(batch_dir)
    sup = _batch_supplementer_cache.get(key)
    if sup is None:
        sup = BatchDataSupplementer(batch_dir)
        sup.load()
        _batch_supplementer_cache[key] = sup
    return sup


def _supplement_with_batch(df: pd.DataFrame, ticker: str, market_data_dir: Path) -> pd.DataFrame:
    """
    Append any market_data_batch/ rows newer than df's last date (df indexed
    by raw, unparsed 'Date' string). No-op if the batch dir doesn't exist,
    has nothing newer for this ticker, or df is empty.
    """
    if df.empty:
        return df

    sup = _get_batch_supplementer(market_data_dir)
    after_date_str = str(df.index.max())

    batch_rows = sup.get_rows(ticker, after_date_str)
    if batch_rows is None:
        return df

    if len(after_date_str) > 10:
        # Match market_data/'s tz-suffixed string shape (e.g. "2026-07-31
        # 00:00:00-04:00") instead of leaving batch rows as bare "YYYY-MM-DD",
        # so the later `df.index.str.split(' ').str[0]` in read_stock_data()
        # handles both uniformly. Only the string *shape* needs to match, not
        # the literal DST offset value, so reusing the last real row's suffix
        # verbatim is safe.
        suffix = after_date_str[10:]
        batch_rows.index = batch_rows.index.astype(str) + suffix

    batch_rows.index.name = df.index.name
    return pd.concat([df, batch_rows]).sort_index()


def read_ticker_ohlcv_raw(
    market_data_dir: Path,
    ticker: str,
    include_batch_overlay: bool = True,
) -> Optional[pd.DataFrame]:
    """
    Raw per-ticker OHLCV rows (index='Date', unparsed). Falls back through
    archive/+current/ (if present) to the flat {ticker}.csv legacy cache.

    include_batch_overlay: when True (default), supplements with any newer
    market_data_batch/ rows -- the fast/gap-fill pipeline, appropriate for
    the daily incremental checker which wants the freshest possible data.
    Set False for the pre-process baseline rebuild, which should be sourced
    only from the slow/authoritative pipeline (archive/current) so its
    cutoff date is deterministic and reproducible, not dependent on
    whatever the fast pipeline happened to have at run time.
    """
    frames = []
    for sub in ('archive', 'current'):
        p = market_data_dir / sub / f"{ticker}.csv"
        if p.exists():
            frame = pd.read_csv(p, index_col='Date', parse_dates=False)
            if not frame.empty:
                frames.append(frame)
    if frames:
        df = pd.concat(frames) if len(frames) > 1 else frames[0]
        df = df[~df.index.duplicated(keep='last')]
        return _supplement_with_batch(df, ticker, market_data_dir) if include_batch_overlay else df

    flat_path = market_data_dir / f"{ticker}.csv"
    if flat_path.exists():
        df = pd.read_csv(flat_path, index_col='Date', parse_dates=False)
        return _supplement_with_batch(df, ticker, market_data_dir) if include_batch_overlay else df
    return None


class DataReader:
    """
    Reads and processes market data from local CSV files.
    
    Supports multiple timeframes (daily, weekly, monthly) and provides
    batch processing capabilities for large datasets.
    """
    
    def __init__(self, config, timeframe='daily', batch_size=100, include_batch_overlay=True):
        """
        Initialize DataReader with configuration and timeframe.

        Args:
            config: Configuration object with directory paths
            timeframe: Data timeframe ('daily', 'weekly', 'monthly', 'intraday')
            batch_size: Number of tickers to process in each batch
            include_batch_overlay: Supplement archive/current with the fast
                market_data_batch/ pipeline (default True). Set False for
                pre-process baseline rebuilds, which should be sourced only
                from the slow/authoritative pipeline for a deterministic
                cutoff date -- see read_ticker_ohlcv_raw().
        """
        self.config = config
        self.timeframe = timeframe
        self.batch_size = batch_size
        self.include_batch_overlay = include_batch_overlay

        # Get market data directory for specified timeframe
        self.market_data_dir = config.get_market_data_dir(timeframe)
        self.tickers_dir = config.directories['TICKERS_DIR']

        # Initialize tickers list
        self.tickers = []
        self.ticker_info = None

        logger.info(f"DataReader initialized for {timeframe} data from {self.market_data_dir}")
    
    def load_tickers_from_file(self, combined_ticker_file: str) -> List[str]:
        """
        Load tickers from combined ticker file.
        
        Args:
            combined_ticker_file: Path to combined ticker CSV file
            
        Returns:
            List of ticker symbols
        """
        try:
            df = pd.read_csv(combined_ticker_file)
            
            # Handle different possible column names (prioritize 'ticker' as standardized column)
            ticker_column = None
            for col in ['ticker', 'symbol', 'Ticker', 'Symbol']:
                if col in df.columns:
                    ticker_column = col
                    break
            
            if ticker_column is None:
                raise ValueError(f"No ticker column found in {combined_ticker_file}")
            
            self.tickers = df[ticker_column].dropna().unique().tolist()
            logger.info(f"Loaded {len(self.tickers)} tickers from {combined_ticker_file}")
            
            return self.tickers
            
        except Exception as e:
            logger.error(f"Error loading tickers from {combined_ticker_file}: {e}")
            raise
    
    def load_ticker_info(self, ticker_info_file: Optional[str] = None, user_choice: Optional[str] = None) -> Optional[pd.DataFrame]:
        """
        Load additional ticker information if available.
        
        Args:
            ticker_info_file: Path to ticker info file (optional)
            user_choice: User ticker choice to find choice-specific files (optional)
            
        Returns:
            DataFrame with ticker info or None if not available
        """
        if not ticker_info_file:
            # Try to find choice-specific ticker info files first
            possible_files = []
            
            # Add choice-specific files if user_choice provided
            if user_choice is not None:
                possible_files.extend([
                    f'combined_info_tickers_clean_{user_choice}.csv',
                    f'combined_info_tickers_{user_choice}.csv'
                ])
            
            # Add generic fallback files
            possible_files.extend([
                'combined_info_tickers_clean_0.csv',  # Universe file fallback
                'combined_info_tickers_0.csv',
                'tradingview_universe_bool.csv',      # Boolean universe file
                'tradingview_universe_info.csv'
            ])
            
            for filename in possible_files:
                file_path = self.tickers_dir / filename
                if file_path.exists():
                    ticker_info_file = str(file_path)
                    logger.info(f"Found ticker info file: {filename}")
                    break
        
        if ticker_info_file and Path(ticker_info_file).exists():
            try:
                self.ticker_info = pd.read_csv(ticker_info_file)
                logger.info(f"Loaded ticker info from {ticker_info_file}")
                return self.ticker_info
            except Exception as e:
                logger.warning(f"Could not load ticker info from {ticker_info_file}: {e}")
        
        logger.info("No ticker info file available")
        return None
    
    def read_stock_data(self, ticker: str) -> Optional[pd.DataFrame]:
        """
        Read historical data for a single ticker.
        
        Args:
            ticker: Ticker symbol
            
        Returns:
            DataFrame with OHLCV data or None if file not found
        """
        df = read_ticker_ohlcv_raw(self.market_data_dir, ticker, self.include_batch_overlay)

        if df is None:
            logger.debug(f"Data file not found for {ticker}: {self.market_data_dir}")
            return None

        try:
            df.index = df.index.str.split(' ').str[0]
            df.index = pd.to_datetime(df.index)
            
            # Ensure timezone-naive datetime index for consistency across all calculations
            if hasattr(df.index, 'tz') and df.index.tz is not None:
                df.index = df.index.tz_localize(None)
            
            # Remove rows with invalid dates (just in case)
            df = df[df.index.notna()]
            
            # Sort by date
            df = df.sort_index()

            # Filter to business days only for daily data (weekly/monthly bars land on weekends)
            if self.timeframe == 'daily':
                df = df[df.index.weekday < 5]

            # Return standard OHLCV columns
            standard_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            available_columns = [col for col in standard_columns if col in df.columns]
            
            if not available_columns:
                logger.warning(f"No standard OHLCV columns found for {ticker}")
                return df  # Return as-is
            
            return df[available_columns]
            
        except Exception as e:
            logger.error(f"Error reading data for {ticker}: {e}")
            return None
    
    def validate_stock_data(self, ticker: str, df: pd.DataFrame, 
                          min_data_points: Optional[int] = None) -> Tuple[bool, str]:
        """
        Validate stock data quality.
        
        Args:
            ticker: Ticker symbol
            df: DataFrame with stock data
            min_data_points: Minimum number of data points required (auto-calculated if None)
            
        Returns:
            Tuple of (is_valid, reason)
        """
        if df is None or df.empty:
            return False, "No data available"
        
        # Set minimum data points based on timeframe if not provided
        if min_data_points is None:
            timeframe_minimums = {
                'daily': 252,    # 1 year of trading days
                'weekly': 52,    # 1 year of weeks  
                'monthly': 12,   # 1 year of months
                'intraday': 100  # Minimum for intraday
            }
            min_data_points = timeframe_minimums.get(self.timeframe, 50)  # Default 50
        
        # Check for minimum data points
        if len(df) < min_data_points:
            return False, f"Insufficient data: {len(df)} < {min_data_points} ({self.timeframe})"
        
        # Check for required columns
        if 'Close' not in df.columns:
            return False, "Missing Close price column"
        
        # Check for excessive missing values
        if df['Close'].isnull().sum() > len(df) * 0.1:  # More than 10% missing
            return False, f"Too many missing Close prices: {df['Close'].isnull().sum()}"
        
        # Check for unrealistic price values
        close_prices = df['Close'].dropna()
        if (close_prices <= 0).any():
            return False, "Invalid price values (≤ 0)"
        
        # Check for extreme price movements (potential data errors)
        price_changes = close_prices.pct_change().dropna()
        extreme_moves = (abs(price_changes) > 0.5).sum()  # More than 50% change
        if extreme_moves > len(price_changes) * 0.01:  # More than 1% of days
            return False, f"Too many extreme price movements: {extreme_moves}"
        
        return True, "Valid data"
    
    def get_batches(self, tickers: Optional[List[str]] = None) -> Generator[List[str], None, None]:
        """
        Generate batches of tickers for processing.
        
        Args:
            tickers: List of tickers (uses self.tickers if None)
            
        Yields:
            Lists of ticker symbols for batch processing
        """
        if tickers is None:
            tickers = self.tickers
            
        for i in range(0, len(tickers), self.batch_size):
            yield tickers[i:i + self.batch_size]
    
    def read_batch_data(
        self,
        ticker_batch: List[str],
        validate: bool = True,
        aggregate_to: str = 'daily'  # NEW: 'daily', 'weekly', 'monthly'
    ) -> Dict[str, pd.DataFrame]:
        """
        Read data for a batch of tickers.
        
        Args:
            ticker_batch: List of ticker symbols
            validate: Whether to validate data quality
            aggregate_to: Timeframe to aggregate to ('daily', 'weekly', 'monthly')
        
        Returns:
            Dictionary mapping tickers to their DataFrames
        """
        batch_data = {}
        
        for ticker in ticker_batch:
            df = self.read_stock_data(ticker)
            
            if df is not None:
                # Only aggregate when read_stock_data() returned daily-granularity
                # rows (self.timeframe == 'daily'). When self.timeframe is already
                # 'weekly'/'monthly', read_stock_data() read straight from that
                # pre-aggregated directory -- resampling it again here would
                # double-aggregate (mislabels dates to calendar period-end and
                # sums volumes across stray same-period rows).
                if self.timeframe == 'daily' and aggregate_to == 'weekly':
                    from src.data_aggregator import aggregate_to_weekly
                    df = aggregate_to_weekly(df)
                elif self.timeframe == 'daily' and aggregate_to == 'monthly':
                    from src.data_aggregator import aggregate_to_monthly
                    df = aggregate_to_monthly(df)
                # else: already at the target granularity - no aggregation needed
                
                if validate:
                    is_valid, reason = self.validate_stock_data(ticker, df)
                    if is_valid:
                        batch_data[ticker] = df
                    else:
                        logger.debug(f"{ticker}: {reason}")
                else:
                    batch_data[ticker] = df
        
        logger.info(f"Successfully read {len(batch_data)}/{len(ticker_batch)} tickers from batch")
        return batch_data
    
    def create_combined_dataframe(self, column='Close', 
                                exclude_patterns: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Create a combined DataFrame with specified column for all tickers.
        
        Args:
            column: Column to extract ('Close', 'Volume', etc.)
            exclude_patterns: List of ticker patterns to exclude
            
        Returns:
            DataFrame with tickers as columns and dates as index
        """
        combined_df = pd.DataFrame()
        
        # Default exclusions for problematic index tickers
        if exclude_patterns is None:
            exclude_patterns = ['^BUK100P', '^FTSE', '^GDAXI', '^FCHI', 
                              '^STOXX50E', '^N100', '^BFX', '^HSI', '^STI']
        
        processed_count = 0
        skipped_count = 0
        
        for ticker in self.tickers:
            # Check exclusion patterns
            if any(pattern in ticker for pattern in exclude_patterns):
                logger.debug(f"Excluding ticker {ticker} due to exclusion pattern")
                skipped_count += 1
                continue
            
            df = self.read_stock_data(ticker)
            
            if df is not None and column in df.columns:
                is_valid, reason = self.validate_stock_data(ticker, df)
                
                if is_valid:
                    # Rename column to ticker name
                    ticker_series = df[column].rename(ticker)
                    combined_df = pd.concat([combined_df, ticker_series], axis=1)
                    processed_count += 1
                else:
                    logger.debug(f"Skipping {ticker}: {reason}")
                    skipped_count += 1
            else:
                skipped_count += 1
        
        logger.info(f"Combined DataFrame created: {processed_count} tickers, "
                   f"{skipped_count} skipped, shape: {combined_df.shape}")
        
        return combined_df
    
    def get_data_summary(self) -> Dict:
        """
        Get summary statistics of available data.
        
        Returns:
            Dictionary with data summary statistics
        """
        summary = {
            'timeframe': self.timeframe,
            'total_tickers': len(self.tickers),
            'available_files': 0,
            'valid_files': 0,
            'date_range': {'start': None, 'end': None},
            'avg_data_points': 0
        }
        
        # Count available files
        if self.market_data_dir.exists():
            csv_files = list(self.market_data_dir.glob('*.csv'))
            summary['available_files'] = len(csv_files)
        
        # Sample some files to get date range and validation info
        sample_size = min(10, len(self.tickers))
        if sample_size > 0:
            valid_count = 0
            total_points = 0
            min_date = None
            max_date = None
            
            for ticker in self.tickers[:sample_size]:
                df = self.read_stock_data(ticker)
                if df is not None and not df.empty:
                    is_valid, _ = self.validate_stock_data(ticker, df)
                    if is_valid:
                        valid_count += 1
                        total_points += len(df)
                        
                        # Update date range
                        if min_date is None or df.index.min() < min_date:
                            min_date = df.index.min()
                        if max_date is None or df.index.max() > max_date:
                            max_date = df.index.max()
            
            summary['valid_files'] = valid_count
            if valid_count > 0:
                summary['avg_data_points'] = total_points // valid_count
                summary['date_range']['start'] = min_date.strftime('%Y-%m-%d') if min_date else None
                summary['date_range']['end'] = max_date.strftime('%Y-%m-%d') if max_date else None
        
        return summary
    
    def __str__(self) -> str:
        """String representation of DataReader."""
        return (f"DataReader(timeframe={self.timeframe}, "
                f"tickers={len(self.tickers)}, "
                f"batch_size={self.batch_size})")