"""
Highest Volume Days (HVD) Screener
===================================

This module identifies the top N volume days for stocks by magnitude,
regardless of when they occurred.

HVE vs HVD - Key Differences:
------------------------------
HVE (Highest Volume Ever):
  - Temporal milestones: Progressive all-time volume highs
  - Only includes days when volume set a NEW record
  - Chronological significance: Tracks momentum progression
  - Use case: Breakout detection, trend analysis

HVD (Highest Volume Days):
  - Magnitude ranking: Top N volume days, period
  - Includes ANY high-volume day regardless of timing
  - No temporal constraint: Pure volume sorting
  - Use case: Liquidity analysis, volatility assessment

Example:
--------
Stock X volume history:
  2020-01-05: 1,000  → HVE #1 (first data point)
  2020-02-10: 5,000  → HVE #2 (new record!)
  2020-03-15: 4,000  → NOT HVE (below previous record)
  2020-04-20: 8,000  → HVE #3 (new record!)
  2020-05-25: 7,000  → NOT HVE (below record)

HVE exports (temporal): [2020-04-20: 8,000, 2020-02-10: 5,000, 2020-01-05: 1,000]
HVD exports (magnitude): [2020-04-20: 8,000, 2020-05-25: 7,000, 2020-02-10: 5,000, 2020-03-15: 4,000, ...]
                         ↑ Same          ↑ INCLUDED (high volume, not HVE)
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class HVDScreener:
    """
    Screener for finding Highest Volume Days (HVD) - top N volume days
    by magnitude, regardless of temporal sequence.
    """

    def __init__(
        self,
        limit_hist_years: int = 0,
        min_price: float = 0.0,
        min_volume: int = 0,
        max_events: int = 10,
        date_range_mode: str = "rolling",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ):
        """
        Initialize HVD Screener for finding top volume days.

        Args:
            limit_hist_years: Limit search to most recent N years (0 = no limit)
            min_price: Minimum price filter (0 = no filter)
            min_volume: Minimum volume filter (0 = no filter)
            max_events: Maximum number of top volume events to return per ticker
            date_range_mode: 'rolling' (from now) or 'fixed' (specific dates)
            start_date: Start date for fixed range mode (YYYY-MM-DD)
            end_date: End date for fixed range mode (YYYY-MM-DD)
        """
        self.limit_hist_years = limit_hist_years
        self.min_price = min_price
        self.min_volume = min_volume
        self.max_events = max_events
        self.date_range_mode = date_range_mode
        def _parse_date(v):
            return pd.Timestamp(v) if v and str(v).strip().lower() not in ('', 'nan', 'none', 'nat') else None
        self.start_date = _parse_date(start_date)
        self.end_date = _parse_date(end_date)

    def find_hvd_events(self, df: pd.DataFrame) -> Dict:
        """
        Find top N volume days in the DataFrame by magnitude.

        Args:
            df: DataFrame with OHLCV data (must have 'Volume' column)

        Returns:
            Dictionary with HVD analysis results:
            - hvd_count: Number of top volume days found
            - hvd_dates: List of dates with highest volumes
            - latest_hvd_date: Most recent high volume day
            - days_since_latest_hvd: Days since most recent high volume day
            - current_volume: Most recent volume
            - max_volume_ever: Maximum volume in the dataset
            - hvd_details: List of dictionaries with detailed HVD info
            - all_hvd_details: Same as hvd_details (for exporter compatibility)
        """
        try:
            if df is None or df.empty or 'Volume' not in df.columns:
                return self._empty_result()

            # Sort by date to ensure chronological order
            df = df.sort_index()

            # Sort by volume to find top N days
            df_sorted = df.sort_values('Volume', ascending=False)

            # Take top N days (limited by max_days)
            top_days = df_sorted.head(self.max_events)

            if len(top_days) == 0:
                return self._empty_result()

            # Get all HVD dates (sorted by volume, highest first)
            hvd_dates = top_days.index.tolist()
            hvd_count = len(hvd_dates)

            # Find the most recent high volume day (by date, not volume)
            latest_hvd_date = max(hvd_dates)
            days_since_latest_hvd = (df.index[-1] - latest_hvd_date).days

            # Get current and max volumes
            current_volume = df['Volume'].iloc[-1]
            max_volume_ever = df['Volume'].max()

            # Build detailed HVD information (sorted by date, most recent first)
            hvd_details = []
            for hvd_date in sorted(hvd_dates, reverse=True):
                hvd_row = df.loc[hvd_date]

                detail = {
                    'date': hvd_date,
                    'volume': hvd_row['Volume'],
                    'close': hvd_row['Close'],
                    'open': hvd_row['Open'] if 'Open' in hvd_row else None,
                    'high': hvd_row['High'] if 'High' in hvd_row else None,
                    'low': hvd_row['Low'] if 'Low' in hvd_row else None,
                    'price_change_pct': ((hvd_row['Close'] - hvd_row['Open']) / hvd_row['Open'] * 100)
                                       if 'Open' in hvd_row and hvd_row['Open'] > 0 else None
                }
                hvd_details.append(detail)

            result = {
                'hvd_count': hvd_count,
                'hvd_dates': hvd_dates,
                'latest_hvd_date': latest_hvd_date,
                'days_since_latest_hvd': days_since_latest_hvd,
                'current_volume': current_volume,
                'max_volume_ever': max_volume_ever,
                'hvd_details': hvd_details,
                'all_hvd_details': hvd_details,  # Alias for exporter
                'current_price': df['Close'].iloc[-1],
                'data_start_date': df.index[0],
                'data_end_date': df.index[-1],
                'data_points': len(df)
            }

            return result

        except Exception as e:
            logger.error(f"Error finding HVD events: {e}")
            return self._empty_result()

    def _empty_result(self) -> Dict:
        """Return empty result structure."""
        return {
            'hvd_count': 0,
            'hvd_dates': [],
            'latest_hvd_date': None,
            'days_since_latest_hvd': None,
            'current_volume': None,
            'max_volume_ever': None,
            'hvd_details': [],
            'all_hvd_details': [],
            'current_price': None,
            'data_start_date': None,
            'data_end_date': None,
            'data_points': 0
        }

    def screen_batch(self, batch_data: Dict[str, pd.DataFrame],
                     timeframe: str) -> pd.DataFrame:
        """
        Screen a batch of tickers for HVD events.

        Args:
            batch_data: Dictionary mapping ticker -> DataFrame
            timeframe: Timeframe being analyzed ('daily', 'weekly', 'monthly')

        Returns:
            DataFrame with HVD screening results
        """
        results = []

        for ticker, df in batch_data.items():
            try:
                # Ensure required columns exist
                if 'Volume' not in df.columns:
                    logger.warning(f"{ticker}: No Volume column, skipping")
                    continue

                # Apply minimum price filter
                if self.min_price > 0:
                    if 'Close' in df.columns:
                        latest_price = df['Close'].iloc[-1]
                        if latest_price < self.min_price:
                            continue

                # Apply minimum volume filter
                if self.min_volume > 0:
                    latest_volume = df['Volume'].iloc[-1]
                    if latest_volume < self.min_volume:
                        continue

                # Apply date range filter based on mode
                if self.date_range_mode == "fixed" and self.start_date:
                    if self.end_date:
                        df = df[(df.index >= self.start_date) & (df.index <= self.end_date)]
                    else:
                        df = df[df.index >= self.start_date]
                elif self.limit_hist_years > 0:
                    # Rolling mode: filter from now backwards by N years
                    cutoff_date = pd.Timestamp.now() - pd.DateOffset(years=self.limit_hist_years)
                    df = df[df.index >= cutoff_date]

                # Ensure we have enough data
                if len(df) < 1:
                    continue

                # Ensure data is sorted by date
                df = df.sort_index()

                # Sort by volume to find top N days
                df_sorted_by_volume = df.sort_values('Volume', ascending=False)

                # Take top N days
                top_days = df_sorted_by_volume.head(self.max_events)

                if len(top_days) == 0:
                    continue

                # Get the absolute highest volume day
                max_volume = df['Volume'].max()
                max_volume_date = df[df['Volume'] == max_volume].index[0]

                # Calculate days since highest volume day
                days_since_hvd = (df.index[-1] - max_volume_date).days

                # Build detailed list of all HVD events with dates and volumes
                all_hvd_details = []
                for hvd_date in top_days.index:
                    all_hvd_details.append({
                        'date': hvd_date,
                        'volume': df.loc[hvd_date, 'Volume']
                    })

                # Sort by date (most recent first) for consistent output
                all_hvd_details = sorted(all_hvd_details, key=lambda x: x['date'], reverse=True)

                # Get recent data
                latest_date = df.index[-1]
                latest_volume = df['Volume'].iloc[-1]
                latest_close = df['Close'].iloc[-1] if 'Close' in df.columns else None

                # Calculate volume ratio (latest vs max)
                volume_ratio = latest_volume / max_volume if max_volume > 0 else 0

                # Build result dictionary
                result_dict = {
                    'ticker': ticker,
                    'timeframe': timeframe,
                    'hvd_date': max_volume_date,
                    'hvd_volume': max_volume,
                    'days_since_hvd': days_since_hvd,
                    'hvd_count': len(all_hvd_details),
                    'all_hvd_details': all_hvd_details,
                    'latest_date': latest_date,
                    'latest_volume': latest_volume,
                    'latest_close': latest_close,
                    'volume_ratio': volume_ratio,
                    'data_points': len(df)
                }

                results.append(result_dict)

            except Exception as e:
                logger.warning(f"Error screening {ticker}: {e}")
                continue

        if results:
            results_df = pd.DataFrame(results)
            # Sort by days since HVD (most recent first)
            results_df = results_df.sort_values('days_since_hvd')
            logger.info(f"Found {len(results_df)} tickers with HVD data")
            return results_df
        else:
            logger.info("No HVD events found")
            return pd.DataFrame()
