"""
Highest Volume Ever (HVE) Screener
===================================

This module identifies stocks that have experienced their highest volume
ever within a specified historical time window.
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class HVEScreener:
    """
    Screener for finding Highest Volume Ever (HVE) events in stock data.
    """

    def __init__(
        self,
        limit_hist_years: int = 0,
        min_price: float = 0.0,
        min_volume: int = 0,
        hv1y_enabled: bool = False,
        hv1y_window_days: int = 365,
        date_range_mode: str = "rolling",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ):
        """
        Initialize HVE Screener.

        Args:
            limit_hist_years: Limit search to most recent N years (0 = no limit, use date_range_mode)
            min_price: Minimum price filter (0 = no filter)
            min_volume: Minimum volume filter (0 = no filter)
            hv1y_enabled: Enable HV1Y (Highest Volume in 1 Year) calculation
            hv1y_window_days: Rolling window for HV1Y in calendar days
            date_range_mode: 'rolling' (from now) or 'fixed' (specific dates)
            start_date: Start date for fixed range mode (YYYY-MM-DD)
            end_date: End date for fixed range mode (YYYY-MM-DD)
        """
        self.limit_hist_years = limit_hist_years
        self.min_price = min_price
        self.min_volume = min_volume
        self.hv1y_enabled = hv1y_enabled
        self.hv1y_window_days = hv1y_window_days
        self.date_range_mode = date_range_mode
        self.start_date = pd.Timestamp(start_date) if start_date else None
        self.end_date = pd.Timestamp(end_date) if end_date else None

    def find_hve_events(self, df: pd.DataFrame) -> Dict:
        """
        Find all Highest Volume Ever events in the DataFrame.

        Args:
            df: DataFrame with OHLCV data (must have 'Volume' column)

        Returns:
            Dictionary with HVE analysis results:
            - hve_count: Number of times HVE occurred
            - hve_dates: List of dates when HVE occurred
            - latest_hve_date: Most recent HVE date
            - days_since_latest_hve: Days since most recent HVE
            - current_volume: Most recent volume
            - max_volume_ever: Maximum volume in the dataset
            - hve_details: List of dictionaries with detailed HVE info
        """
        try:
            if df is None or df.empty or 'Volume' not in df.columns:
                return self._empty_result()

            # Sort by date to ensure chronological order
            df = df.sort_index()

            # Calculate rolling maximum volume
            df['Volume_Max'] = df['Volume'].expanding().max()

            # Identify HVE events: Volume equals rolling max AND is different from previous max
            # This ensures we only count new HVE events, not repeated max values
            df['Volume_Max_Shifted'] = df['Volume_Max'].shift(1)
            df['Is_HVE'] = (df['Volume'] == df['Volume_Max']) & (df['Volume'] > df['Volume_Max_Shifted'])

            # Get all HVE dates
            hve_dates = df[df['Is_HVE']].index.tolist()
            hve_count = len(hve_dates)

            if hve_count == 0:
                return self._empty_result()

            # Get latest HVE date
            latest_hve_date = hve_dates[-1]
            days_since_latest_hve = (df.index[-1] - latest_hve_date).days

            # Get current and max volumes
            current_volume = df['Volume'].iloc[-1]
            max_volume_ever = df['Volume'].max()

            # Build detailed HVE information
            hve_details = []
            for hve_date in hve_dates:
                hve_row = df.loc[hve_date]

                detail = {
                    'date': hve_date,
                    'volume': hve_row['Volume'],
                    'close': hve_row['Close'],
                    'open': hve_row['Open'] if 'Open' in hve_row else None,
                    'high': hve_row['High'] if 'High' in hve_row else None,
                    'low': hve_row['Low'] if 'Low' in hve_row else None,
                    'price_change_pct': ((hve_row['Close'] - hve_row['Open']) / hve_row['Open'] * 100)
                                       if 'Open' in hve_row and hve_row['Open'] > 0 else None
                }
                hve_details.append(detail)

            result = {
                'hve_count': hve_count,
                'hve_dates': hve_dates,
                'latest_hve_date': latest_hve_date,
                'days_since_latest_hve': days_since_latest_hve,
                'current_volume': current_volume,
                'max_volume_ever': max_volume_ever,
                'hve_details': hve_details,
                'current_price': df['Close'].iloc[-1],
                'data_start_date': df.index[0],
                'data_end_date': df.index[-1],
                'data_points': len(df)
            }

            return result

        except Exception as e:
            logger.error(f"Error finding HVE events: {e}")
            return self._empty_result()

    def _empty_result(self) -> Dict:
        """Return empty result structure."""
        return {
            'hve_count': 0,
            'hve_dates': [],
            'latest_hve_date': None,
            'days_since_latest_hve': None,
            'current_volume': None,
            'max_volume_ever': None,
            'hve_details': [],
            'current_price': None,
            'data_start_date': None,
            'data_end_date': None,
            'data_points': 0
        }

    def _calculate_hv1y_metrics(self, df: pd.DataFrame, hve_date, hve_volume) -> Dict:
        """
        Calculate HV1Y (Highest Volume in 1 Year) metrics.

        Args:
            df: DataFrame with OHLCV data (must have 'Volume' column)
            hve_date: Date of HVE event (for comparison)
            hve_volume: Volume of HVE event (for ratio calculation)

        Returns:
            Dictionary with HV1Y metrics:
            - hv1y_date: Date of highest volume in last year
            - hv1y_volume: Highest volume in last year
            - days_since_hv1y: Days since HV1Y event
            - hv1y_occ_1y: Number of HV1Y events in last year
            - total_hv1y_count: Total number of HV1Y events in dataset
            - is_hv1y_also_hve: Boolean flag if HV1Y date matches HVE date
            - hv1y_to_hve_ratio: Ratio of HV1Y volume to HVE volume
        """
        try:
            if df is None or df.empty or 'Volume' not in df.columns:
                return self._empty_hv1y_result()

            # Sort by date to ensure chronological order
            df = df.sort_index()

            # Get the latest date in the dataset
            latest_date = df.index[-1]

            # Define the 1-year window using calendar days
            one_year_ago = latest_date - pd.DateOffset(days=self.hv1y_window_days)

            # Filter data to last year
            df_1y = df[df.index >= one_year_ago].copy()

            if len(df_1y) < 2:
                return self._empty_hv1y_result()

            # Calculate cumulative maximum volume within 1-year window
            df_1y['cummax_volume_1y'] = df_1y['Volume'].cummax()

            # Identify HV1Y events (similar to HVE logic)
            df_1y['is_hv1y'] = df_1y['Volume'] == df_1y['cummax_volume_1y']
            df_1y['is_new_hv1y'] = (df_1y['is_hv1y']) & (df_1y['Volume'] > df_1y['cummax_volume_1y'].shift(1).fillna(0))

            # Get all HV1Y event dates
            hv1y_events = df_1y[df_1y['is_new_hv1y']]

            # Get the absolute highest volume in 1 year
            max_volume_1y = df_1y['Volume'].max()
            max_volume_1y_date = df_1y[df_1y['Volume'] == max_volume_1y].index[0]

            # Calculate days since latest HV1Y
            days_since_hv1y = (latest_date - max_volume_1y_date).days

            # Count HV1Y occurrences in last 1 year (all events are by definition in last year)
            hv1y_occ_1y = len(hv1y_events)

            # Total HV1Y count (same as hv1y_occ_1y since we're looking at 1-year window)
            total_hv1y_count = len(hv1y_events)

            # Build detailed list of all HV1Y events with dates and volumes
            all_hv1y_details = []
            for hv1y_date_item in hv1y_events.index:
                all_hv1y_details.append({
                    'date': hv1y_date_item,
                    'volume': df_1y.loc[hv1y_date_item, 'Volume']
                })
            # Sort by date (most recent first)
            all_hv1y_details = sorted(all_hv1y_details, key=lambda x: x['date'], reverse=True)

            # Check if HV1Y is also HVE
            is_hv1y_also_hve = (max_volume_1y_date == hve_date)

            # Calculate HV1Y to HVE ratio
            hv1y_to_hve_ratio = max_volume_1y / hve_volume if hve_volume > 0 else 0

            return {
                'hv1y_date': max_volume_1y_date,
                'hv1y_volume': max_volume_1y,
                'days_since_hv1y': days_since_hv1y,
                'hv1y_occ_1y': hv1y_occ_1y,
                'total_hv1y_count': total_hv1y_count,
                'is_hv1y_also_hve': is_hv1y_also_hve,
                'hv1y_to_hve_ratio': hv1y_to_hve_ratio,
                'all_hv1y_details': all_hv1y_details
            }

        except Exception as e:
            logger.error(f"Error calculating HV1Y metrics: {e}")
            return self._empty_hv1y_result()

    def _empty_hv1y_result(self) -> Dict:
        """Return empty HV1Y result structure."""
        return {
            'hv1y_date': None,
            'hv1y_volume': None,
            'days_since_hv1y': None,
            'hv1y_occ_1y': 0,
            'total_hv1y_count': 0,
            'is_hv1y_also_hve': False,
            'hv1y_to_hve_ratio': 0.0,
            'all_hv1y_details': []
        }

    def screen_batch(self, batch_data: Dict[str, pd.DataFrame],
                     timeframe: str) -> pd.DataFrame:
        """
        Screen a batch of tickers for HVE events.

        Args:
            batch_data: Dictionary mapping ticker -> DataFrame
            timeframe: Timeframe being analyzed ('daily', 'weekly', 'monthly')

        Returns:
            DataFrame with HVE screening results
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
                if self.date_range_mode == "fixed" and self.start_date and self.end_date:
                    # Fixed date range mode: filter to specific start and end dates
                    df = df[(df.index >= self.start_date) & (df.index <= self.end_date)]
                elif self.limit_hist_years > 0:
                    # Rolling mode: filter from now backwards by N years
                    cutoff_date = pd.Timestamp.now() - pd.DateOffset(years=self.limit_hist_years)
                    df = df[df.index >= cutoff_date]

                # Find HVE events
                if len(df) < 2:
                    continue

                # Ensure data is sorted by date
                df = df.sort_index()

                # Calculate cumulative maximum volume (rolling HVE)
                df['cummax_volume'] = df['Volume'].cummax()

                # Identify all HVE events (when volume equals cumulative max at that point)
                # An HVE event is when volume reaches a new all-time high
                df['is_hve'] = df['Volume'] == df['cummax_volume']

                # Also need to filter out consecutive duplicates (same volume stays as max)
                # Only count it as HVE when it's a NEW maximum
                df['is_new_hve'] = (df['is_hve']) & (df['Volume'] > df['cummax_volume'].shift(1).fillna(0))

                # Get all HVE event dates
                hve_events = df[df['is_new_hve']]

                # Get the absolute highest volume ever (most recent HVE)
                max_volume = df['Volume'].max()
                max_volume_date = df[df['Volume'] == max_volume].index[0]

                # Calculate days since latest HVE
                days_since_hve = (df.index[-1] - max_volume_date).days

                # Count HVE occurrences in last 1 year
                one_year_ago = df.index[-1] - pd.DateOffset(years=1)
                hve_last_year = hve_events[hve_events.index >= one_year_ago]
                hve_occ_1y = len(hve_last_year)

                # Get all HVE dates for reference
                all_hve_dates = hve_events.index.tolist()
                total_hve_count = len(all_hve_dates)

                # Build detailed list of all HVE events with dates and volumes
                all_hve_details = []
                for hve_date in hve_events.index:
                    all_hve_details.append({
                        'date': hve_date,
                        'volume': df.loc[hve_date, 'Volume']
                    })
                # Sort by date (most recent first)
                all_hve_details = sorted(all_hve_details, key=lambda x: x['date'], reverse=True)

                # Get recent data
                latest_date = df.index[-1]
                latest_volume = df['Volume'].iloc[-1]
                latest_close = df['Close'].iloc[-1] if 'Close' in df.columns else None

                # Calculate volume ratio (latest vs max)
                volume_ratio = latest_volume / max_volume if max_volume > 0 else 0

                # Calculate HV1Y metrics if enabled
                if self.hv1y_enabled:
                    hv1y_metrics = self._calculate_hv1y_metrics(df, max_volume_date, max_volume)
                else:
                    hv1y_metrics = self._empty_hv1y_result()

                # Build result dictionary
                result_dict = {
                    'ticker': ticker,
                    'timeframe': timeframe,
                    'hve_date': max_volume_date,
                    'hve_volume': max_volume,
                    'days_since_hve': days_since_hve,
                    'hve_occ_1y': hve_occ_1y,
                    'total_hve_count': total_hve_count,
                    'all_hve_details': all_hve_details,
                }

                # Add HV1Y metrics if enabled
                if self.hv1y_enabled:
                    result_dict.update({
                        'hv1y_date': hv1y_metrics['hv1y_date'],
                        'hv1y_volume': hv1y_metrics['hv1y_volume'],
                        'days_since_hv1y': hv1y_metrics['days_since_hv1y'],
                        'hv1y_occ_1y': hv1y_metrics['hv1y_occ_1y'],
                        'total_hv1y_count': hv1y_metrics['total_hv1y_count'],
                        'is_hv1y_also_hve': hv1y_metrics['is_hv1y_also_hve'],
                        'hv1y_to_hve_ratio': hv1y_metrics['hv1y_to_hve_ratio'],
                        'all_hv1y_details': hv1y_metrics['all_hv1y_details'],
                    })

                # Add current data
                result_dict.update({
                    'latest_date': latest_date,
                    'latest_volume': latest_volume,
                    'latest_close': latest_close,
                    'volume_ratio': volume_ratio,
                    'data_points': len(df)
                })

                results.append(result_dict)

            except Exception as e:
                logger.warning(f"Error screening {ticker}: {e}")
                continue

        if results:
            results_df = pd.DataFrame(results)
            # Sort by days since HVE (most recent first)
            results_df = results_df.sort_values('days_since_hve')
            logger.info(f"Found {len(results_df)} tickers with HVE data")
            return results_df
        else:
            logger.info("No HVE events found")
            return pd.DataFrame()

    def calculate_score(self, result: Dict) -> float:
        """
        Calculate a screening score for ranking HVE candidates.

        Score is based on:
        - Recency of latest HVE (more recent = higher score)
        - Frequency of HVE events (more events = higher score)
        - Current volume relative to max (closer to max = higher score)

        Args:
            result: HVE screening result dictionary

        Returns:
            Numeric score (higher = better candidate)
        """
        try:
            score = 0.0

            # Recency score (0-50 points)
            # Recent HVE within 30 days gets max points, decays over time
            days_since = result.get('days_since_latest_hve', 9999)
            if days_since <= 30:
                recency_score = 50
            elif days_since <= 90:
                recency_score = 50 * (1 - (days_since - 30) / 60 * 0.5)  # Decay to 25
            elif days_since <= 365:
                recency_score = 25 * (1 - (days_since - 90) / 275 * 0.8)  # Decay to 5
            else:
                recency_score = 5 * max(0, (1 - (days_since - 365) / 365))  # Decay to 0

            score += recency_score

            # Frequency score (0-30 points)
            # More HVE events indicates consistent high volume activity
            hve_count = result.get('hve_count', 0)
            frequency_score = min(30, hve_count * 3)
            score += frequency_score

            # Volume ratio score (0-20 points)
            # Current volume relative to max volume
            volume_ratio = result.get('volume_ratio_to_max', 0)
            volume_score = min(20, volume_ratio / 5)  # 100% ratio = 20 points
            score += volume_score

            return round(score, 2)

        except Exception as e:
            logger.error(f"Error calculating score: {e}")
            return 0.0

    def enrich_results_with_scores(self, results: List[Dict]) -> List[Dict]:
        """
        Add screening scores to results and re-sort by score.

        Args:
            results: List of HVE screening results

        Returns:
            Enriched results sorted by score (descending)
        """
        for result in results:
            result['score'] = self.calculate_score(result)

        # Sort by score (highest first)
        results.sort(key=lambda x: x['score'], reverse=True)

        return results
