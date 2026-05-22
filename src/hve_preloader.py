"""
HVE/HVD Preload Module
======================

Handles loading and converting preload data from CSV files to accelerate HVE analysis.

This module enables the HVE pipeline to skip computation for tickers with existing
historical data by loading pre-computed HVE/HVD results from CSV files.

Functions:
- load_hve_preload_data(): Load HVE preload data from CSV
- load_hvd_preload_data(): Load HVD preload data from CSV
- convert_hve_wide_to_results_format(): Convert wide CSV format to results format
- convert_hvd_wide_to_results_format(): Convert wide CSV format to results format
- get_tickers_to_process(): Determine which tickers need computation
"""

import pandas as pd
import numpy as np
import logging
from pathlib import Path
from typing import List, Tuple, Dict
from datetime import datetime

logger = logging.getLogger(__name__)


def load_hve_preload_data(file_path: str, timeframe: str = "daily") -> pd.DataFrame:
    """
    Load HVE preload data from CSV file and convert to results format.
    Replaces * wildcard in file_path with timeframe.
    
    Args:
        file_path: Path to HVE preload CSV file (use * as placeholder for timeframe)
                   Example: /path/to/HVE_historical_*.csv
        timeframe: Timeframe to load ('daily', 'weekly', 'monthly')
    
    Returns:
        DataFrame in HVEScreener results format, or empty DataFrame if load fails
    """
    try:
        # Replace * wildcard with actual timeframe
        actual_file_path = file_path.replace('*', timeframe)
        file_path_obj = Path(actual_file_path)
        
        if not file_path_obj.exists():
            logger.warning(f"HVE preload file not found: {actual_file_path}")
            return pd.DataFrame()
        
        logger.info(f"Loading HVE preload data from {actual_file_path}")
        
        # Load the wide-format CSV
        df = pd.read_csv(file_path_obj)
        
        # Filter by timeframe if column exists
        if 'timeframe' in df.columns:
            df = df[df['timeframe'] == timeframe].copy()
        
        if df.empty:
            logger.warning(f"No HVE preload data found for timeframe: {timeframe}")
            return pd.DataFrame()
        
        # Convert from wide format to results format
        results_df = convert_hve_wide_to_results_format(df)
        
        logger.info(f"Loaded {len(results_df)} HVE preload records for {timeframe}")
        return results_df
        
    except Exception as e:
        logger.error(f"Error loading HVE preload data: {e}")
        return pd.DataFrame()


def load_hvd_preload_data(file_path: str, timeframe: str = "daily") -> pd.DataFrame:
    """
    Load HVD preload data from CSV file and convert to results format.
    Replaces * wildcard in file_path with timeframe.
    
    Args:
        file_path: Path to HVD preload CSV file (use * as placeholder for timeframe)
                   Example: /path/to/HVD_historical_*.csv
        timeframe: Timeframe to load ('daily', 'weekly', 'monthly')
    
    Returns:
        DataFrame in HVDScreener results format, or empty DataFrame if load fails
    """
    try:
        # Replace * wildcard with actual timeframe
        actual_file_path = file_path.replace('*', timeframe)
        file_path_obj = Path(actual_file_path)
        
        if not file_path_obj.exists():
            logger.warning(f"HVD preload file not found: {actual_file_path}")
            return pd.DataFrame()
        
        logger.info(f"Loading HVD preload data from {actual_file_path}")
        
        # Load the wide-format CSV
        df = pd.read_csv(file_path_obj)
        
        # Filter by timeframe if column exists
        if 'timeframe' in df.columns:
            df = df[df['timeframe'] == timeframe].copy()
        
        if df.empty:
            logger.warning(f"No HVD preload data found for timeframe: {timeframe}")
            return pd.DataFrame()
        
        # Convert from wide format to results format
        results_df = convert_hvd_wide_to_results_format(df)
        
        logger.info(f"Loaded {len(results_df)} HVD preload records for {timeframe}")
        return results_df
        
    except Exception as e:
        logger.error(f"Error loading HVD preload data: {e}")
        return pd.DataFrame()


def convert_hve_wide_to_results_format(wide_df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert HVE wide CSV format to HVEScreener results format.
    
    Input format (wide):
        Symbol, timeframe, HVE_date_1, HVE_vol_1, HVE_date_2, HVE_vol_2, ...
    
    Output format (results):
        ticker, timeframe, hve_date, hve_volume, days_since_hve, total_hve_count,
        all_hve_details (list of dicts), etc.
    
    Args:
        wide_df: DataFrame in wide format from CSV
    
    Returns:
        DataFrame in HVEScreener results format
    """
    try:
        results = []
        
        for _, row in wide_df.iterrows():
            ticker = row['Symbol']
            timeframe = row.get('timeframe', 'daily')
            
            # Extract all HVE events from wide format
            hve_events = []
            for i in range(1, 100):  # Support up to 99 events (should be more than enough)
                date_col = f'HVE_date_{i}'
                vol_col = f'HVE_vol_{i}'
                
                if date_col not in row or pd.isna(row[date_col]) or row[date_col] == '':
                    break
                
                hve_date = pd.to_datetime(row[date_col])
                hve_volume = int(row[vol_col]) if not pd.isna(row[vol_col]) else 0
                
                hve_events.append({
                    'date': hve_date,
                    'volume': hve_volume
                })
            
            if not hve_events:
                continue
            
            # Sort by date (most recent first)
            hve_events = sorted(hve_events, key=lambda x: x['date'], reverse=True)
            
            # Most recent HVE event
            latest_hve = hve_events[0]
            hve_date = latest_hve['date']
            hve_volume = latest_hve['volume']
            
            # Calculate days since HVE
            days_since_hve = (pd.Timestamp.now() - hve_date).days
            
            # Count HVE events in past year
            one_year_ago = pd.Timestamp.now() - pd.Timedelta(days=365)
            hve_occ_1y = sum(1 for event in hve_events if event['date'] >= one_year_ago)
            
            # Build result row matching HVEScreener output format
            result_row = {
                'ticker': ticker,
                'timeframe': timeframe,
                'hve_date': hve_date,
                'hve_volume': hve_volume,
                'days_since_hve': days_since_hve,
                'total_hve_count': len(hve_events),
                'hve_occ_1y': hve_occ_1y,
                'all_hve_details': hve_events,
                'data_source': 'preload'  # Mark as preloaded for tracking
            }
            
            results.append(result_row)
        
        if not results:
            return pd.DataFrame()
        
        results_df = pd.DataFrame(results)
        return results_df
        
    except Exception as e:
        logger.error(f"Error converting HVE wide format to results: {e}")
        return pd.DataFrame()


def convert_hvd_wide_to_results_format(wide_df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert HVD wide CSV format to HVDScreener results format.
    
    Input format (wide):
        Symbol, timeframe, HVD_date_1, HVD_vol_1, HVD_date_2, HVD_vol_2, ...
    
    Output format (results):
        ticker, timeframe, hvd_date, hvd_volume, days_since_hvd, hvd_count,
        all_hvd_details (list of dicts), etc.
    
    Args:
        wide_df: DataFrame in wide format from CSV
    
    Returns:
        DataFrame in HVDScreener results format
    """
    try:
        results = []
        
        for _, row in wide_df.iterrows():
            ticker = row['Symbol']
            timeframe = row.get('timeframe', 'daily')
            
            # Extract all HVD events from wide format
            hvd_events = []
            for i in range(1, 100):  # Support up to 99 days
                date_col = f'HVD_date_{i}'
                vol_col = f'HVD_vol_{i}'
                
                if date_col not in row or pd.isna(row[date_col]) or row[date_col] == '':
                    break
                
                hvd_date = pd.to_datetime(row[date_col])
                hvd_volume = int(row[vol_col]) if not pd.isna(row[vol_col]) else 0
                
                hvd_events.append({
                    'date': hvd_date,
                    'volume': hvd_volume
                })
            
            if not hvd_events:
                continue
            
            # Sort by volume (highest first) - HVD is magnitude-based
            hvd_events = sorted(hvd_events, key=lambda x: x['volume'], reverse=True)
            
            # Most recent high-volume day
            latest_hvd = hvd_events[0]
            hvd_date = latest_hvd['date']
            hvd_volume = latest_hvd['volume']
            
            # Calculate days since most recent HVD
            days_since_hvd = (pd.Timestamp.now() - hvd_date).days
            
            # Build result row matching HVDScreener output format
            result_row = {
                'ticker': ticker,
                'timeframe': timeframe,
                'hvd_date': hvd_date,
                'hvd_volume': hvd_volume,
                'days_since_hvd': days_since_hvd,
                'hvd_count': len(hvd_events),
                'all_hvd_details': hvd_events,
                'data_source': 'preload'  # Mark as preloaded for tracking
            }
            
            results.append(result_row)
        
        if not results:
            return pd.DataFrame()
        
        results_df = pd.DataFrame(results)
        return results_df
        
    except Exception as e:
        logger.error(f"Error converting HVD wide format to results: {e}")
        return pd.DataFrame()


def get_tickers_to_process(
    all_tickers: List[str],
    preload_df: pd.DataFrame
) -> Tuple[List[str], List[str]]:
    """
    Determine which tickers need computation vs. which are in preload.
    
    Args:
        all_tickers: Complete list of tickers to analyze
        preload_df: DataFrame with preloaded results (must have 'ticker' column)
    
    Returns:
        Tuple of (tickers_with_preload, tickers_to_compute)
    """
    try:
        if preload_df.empty or 'ticker' not in preload_df.columns:
            return ([], all_tickers)
        
        preload_tickers = set(preload_df['ticker'].unique())
        all_tickers_set = set(all_tickers)
        
        tickers_with_preload = sorted(list(preload_tickers & all_tickers_set))
        tickers_to_compute = sorted(list(all_tickers_set - preload_tickers))
        
        return (tickers_with_preload, tickers_to_compute)
        
    except Exception as e:
        logger.error(f"Error determining tickers to process: {e}")
        return ([], all_tickers)


def get_preload_max_volumes(preload_df: pd.DataFrame) -> Dict[str, float]:
    """
    Extract the maximum historical volume for each ticker from preload data.
    
    This provides the baseline threshold to determine if new data points are HVE events.
    Only volumes exceeding this baseline will be recorded as new HVE events.
    
    Args:
        preload_df: Preload DataFrame with all_hve_details column
    
    Returns:
        Dict mapping ticker -> max_volume
        Example: {'AAPL': 100000000.0, 'MSFT': 85000000.0, ...}
    """
    try:
        max_volumes = {}
        
        if preload_df.empty or 'ticker' not in preload_df.columns:
            return max_volumes
        
        for _, row in preload_df.iterrows():
            ticker = row['ticker']
            all_hve_details = row.get('all_hve_details', [])
            
            if all_hve_details and isinstance(all_hve_details, list):
                # Get the maximum volume from all historical HVE events
                max_vol = max(event['volume'] for event in all_hve_details if 'volume' in event)
                max_volumes[ticker] = float(max_vol)
                logger.debug(f"{ticker}: Baseline max volume = {max_vol:,.0f}")
        
        logger.info(f"Extracted baseline max volumes for {len(max_volumes)} tickers")
        return max_volumes
        
    except Exception as e:
        logger.error(f"Error extracting max volumes from preload: {e}")
        return {}

