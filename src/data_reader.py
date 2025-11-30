"""
Data Reader for Post-Processing Financial Market Data
==================================================

This module handles reading historical market data from local CSV files
and provides utilities for batch processing and data validation.

Based on the original data_reader.py from the old model with enhancements
for ticker info reading and better error handling.
"""

import pandas as pd
import os
from pathlib import Path
from typing import List, Dict, Optional, Generator, Tuple
import logging

logger = logging.getLogger(__name__)


class DataReader:
    """
    Reads and processes market data from local CSV files.
    
    Supports multiple timeframes (daily, weekly, monthly) and provides
    batch processing capabilities for large datasets.
    """
    
    def __init__(self, config, timeframe='daily', batch_size=100):
        """
        Initialize DataReader with configuration and timeframe.
        
        Args:
            config: Configuration object with directory paths
            timeframe: Data timeframe ('daily', 'weekly', 'monthly', 'intraday')
            batch_size: Number of tickers to process in each batch
        """
        self.config = config
        self.timeframe = timeframe
        self.batch_size = batch_size
        
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
        file_path = self.market_data_dir / f"{ticker}.csv"
        
        if not file_path.exists():
            logger.debug(f"Data file not found for {ticker}: {file_path}")
            return None
        
        try:
            # Use the exact same approach as the working marketScanners_v1 version
            df = pd.read_csv(file_path, index_col='Date', parse_dates=False)
            df.index = df.index.str.split(' ').str[0]
            df.index = pd.to_datetime(df.index)
            
            # Ensure timezone-naive datetime index for consistency across all calculations
            if hasattr(df.index, 'tz') and df.index.tz is not None:
                df.index = df.index.tz_localize(None)
            
            # Remove rows with invalid dates (just in case)
            df = df[df.index.notna()]
            
            # Sort by date
            df = df.sort_index()

            # Filter to business days only (exclude weekends)
            # This removes Saturday (5) and Sunday (6) data points
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
    
    def read_batch_data(self, ticker_batch: List[str], 
                       validate: bool = True) -> Dict[str, pd.DataFrame]:
        """
        Read data for a batch of tickers.
        
        Args:
            ticker_batch: List of ticker symbols
            validate: Whether to validate data quality
            
        Returns:
            Dictionary mapping tickers to their DataFrames
        """
        batch_data = {}
        
        for ticker in ticker_batch:
            df = self.read_stock_data(ticker)
            
            if df is not None:
                if validate:
                    is_valid, reason = self.validate_stock_data(ticker, df)
                    if is_valid:
                        batch_data[ticker] = df
                    else:
                        logger.debug(f"Skipping {ticker}: {reason}")
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