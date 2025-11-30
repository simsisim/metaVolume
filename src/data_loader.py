"""
Data Loader for metaVolume HVE Screener
=======================================

This module handles loading data from the metaData_v1 project
and ticker selection from downloadData_v1.
"""

import sys
import logging
from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd
import importlib.util

logger = logging.getLogger(__name__)


class DataLoader:
    """
    Loads market data from metaData_v1 project for HVE analysis.
    """

    def __init__(self, metadata_v1_path: str, user_choice: int = 0):
        """
        Initialize DataLoader with metaData_v1 configuration.

        Args:
            metadata_v1_path: Path to metaData_v1 project directory
            user_choice: User choice for ticker selection (default: 0)
        """
        self.metadata_v1_path = Path(metadata_v1_path)
        self.user_choice = user_choice

        # Import metaData_v1 modules using importlib to avoid module name conflicts
        try:
            # Save current sys.path and metaVolume's 'src' module
            old_syspath = sys.path.copy()
            metavolume_src_modules = {}

            # Temporarily remove metaVolume's 'src' modules from sys.modules
            # to allow metaData_v1's 'src' imports to work
            for key in list(sys.modules.keys()):
                if key == 'src' or key.startswith('src.'):
                    metavolume_src_modules[key] = sys.modules.pop(key)

            try:
                # Add metaData_v1 to sys.path for imports
                sys.path.insert(0, str(self.metadata_v1_path))

                # Load config module
                config_path = self.metadata_v1_path / "src" / "config.py"
                spec = importlib.util.spec_from_file_location("metadata_v1_config", config_path)
                metadata_config = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(metadata_config)

                # Load data_reader module
                data_reader_path = self.metadata_v1_path / "src" / "data_reader.py"
                spec = importlib.util.spec_from_file_location("metadata_v1_data_reader", data_reader_path)
                metadata_data_reader = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(metadata_data_reader)

                self.Config = metadata_config.Config
                self.DataReader = metadata_data_reader.DataReader
                logger.info(f"Successfully loaded metaData_v1 modules from {metadata_v1_path}")

            finally:
                # Restore sys.path and metaVolume's 'src' modules
                sys.path = old_syspath

                # Remove metaData_v1's 'src' modules and restore metaVolume's
                for key in list(sys.modules.keys()):
                    if key == 'src' or key.startswith('src.'):
                        if key not in metavolume_src_modules:
                            del sys.modules[key]

                for key, module in metavolume_src_modules.items():
                    sys.modules[key] = module

        except Exception as e:
            logger.error(f"Failed to import metaData_v1 modules: {e}")
            raise

        # Initialize config
        self.config = None
        self.reader = None

    def load_tickers(self, ticker_file: Optional[str] = None) -> List[str]:
        """
        Load ticker list from file.

        Args:
            ticker_file: Path to ticker file. Can be:
                        - Absolute path (e.g., "/path/to/tickers.csv")
                        - Relative path (e.g., "test_tickers.csv")
                        - File name in metaData_v1/data/tickers directory
                        - If None, uses combined_tickers_choice_{user_choice}.csv

        Returns:
            List of ticker symbols
        """
        try:
            ticker_file_path = None

            # Case 1: ticker_file is provided and is an absolute path or relative path that exists
            if ticker_file is not None:
                # Check if it's an absolute path
                if Path(ticker_file).is_absolute():
                    if Path(ticker_file).exists():
                        ticker_file_path = Path(ticker_file)
                        logger.info(f"Using absolute path ticker file: {ticker_file_path}")
                else:
                    # Check if it's a relative path that exists (in current directory)
                    current_dir_path = Path.cwd() / ticker_file
                    if current_dir_path.exists():
                        ticker_file_path = current_dir_path
                        logger.info(f"Using relative path ticker file: {ticker_file_path}")

            # Case 2: File not found yet, try metaData_v1 ticker directory
            if ticker_file_path is None:
                # Initialize config if not already done
                if self.config is None:
                    self.config = self.Config()

                # Determine ticker file path in metaData_v1
                tickers_dir = self.config.directories['TICKERS_DIR']

                if ticker_file is None:
                    ticker_file = f"combined_tickers_choice_{self.user_choice}.csv"

                ticker_file_path = tickers_dir / ticker_file

                if not ticker_file_path.exists():
                    # Try alternative naming patterns in metaData_v1
                    alternatives = [
                        f"combined_info_tickers_clean_{self.user_choice}.csv",
                        f"combined_info_tickers_{self.user_choice}.csv",
                        "tradingview_universe_bool.csv"
                    ]

                    for alt_file in alternatives:
                        alt_path = tickers_dir / alt_file
                        if alt_path.exists():
                            ticker_file_path = alt_path
                            logger.info(f"Using alternative ticker file: {alt_file}")
                            break

            # Verify file exists
            if ticker_file_path is None or not ticker_file_path.exists():
                raise FileNotFoundError(f"Ticker file not found: {ticker_file}")

            # Load tickers from CSV
            df = pd.read_csv(ticker_file_path)

            # Find ticker column (support various common column names)
            ticker_column = None
            for col in ['ticker', 'symbol', 'Ticker', 'Symbol']:
                if col in df.columns:
                    ticker_column = col
                    break

            # If no standard column found and CSV has only one column, use it
            if ticker_column is None and len(df.columns) == 1:
                ticker_column = df.columns[0]
                logger.info(f"Using single column '{ticker_column}' as ticker column")

            if ticker_column is None:
                raise ValueError(f"No ticker column found in {ticker_file_path}")

            tickers = df[ticker_column].dropna().unique().tolist()
            # Clean up tickers (strip whitespace)
            tickers = [str(t).strip() for t in tickers]
            logger.info(f"Loaded {len(tickers)} tickers from {ticker_file_path.name}")

            return tickers

        except Exception as e:
            logger.error(f"Error loading tickers: {e}")
            raise

    def load_data(self, timeframe: str, tickers: List[str],
                  limit_years: Optional[int] = None) -> Dict[str, pd.DataFrame]:
        """
        Load historical data for specified timeframe and tickers.

        Args:
            timeframe: Data timeframe ('daily', 'weekly', 'monthly')
            tickers: List of ticker symbols
            limit_years: Limit data to most recent N years (None = all data)

        Returns:
            Dictionary mapping ticker -> DataFrame with OHLCV data
        """
        try:
            # Initialize config if not already done
            if self.config is None:
                self.config = self.Config()

            # Create DataReader for the specified timeframe
            self.reader = self.DataReader(self.config, timeframe=timeframe)
            self.reader.tickers = tickers

            # Load data for all tickers
            batch_data = {}

            for ticker in tickers:
                df = self.reader.read_stock_data(ticker)

                if df is not None and not df.empty:
                    # Validate data
                    is_valid, reason = self.reader.validate_stock_data(ticker, df)

                    if is_valid:
                        # Limit to recent years if specified
                        if limit_years is not None:
                            cutoff_date = pd.Timestamp.now() - pd.DateOffset(years=limit_years)
                            df = df[df.index >= cutoff_date]

                        if not df.empty:
                            batch_data[ticker] = df
                    else:
                        logger.debug(f"Skipping {ticker}: {reason}")

            logger.info(f"Loaded data for {len(batch_data)}/{len(tickers)} tickers ({timeframe})")

            return batch_data

        except Exception as e:
            logger.error(f"Error loading data for {timeframe}: {e}")
            raise

    def get_ticker_info(self) -> Optional[pd.DataFrame]:
        """
        Load ticker information (exchange, industry, etc.) if available.

        Returns:
            DataFrame with ticker info or None
        """
        try:
            if self.reader is None:
                return None

            ticker_info = self.reader.load_ticker_info(user_choice=self.user_choice)
            return ticker_info

        except Exception as e:
            logger.warning(f"Could not load ticker info: {e}")
            return None
