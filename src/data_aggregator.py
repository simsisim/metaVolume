"""
Data Aggregation Module
========================

Provides functions to aggregate daily OHLCV data to weekly and monthly timeframes.

Functions:
- aggregate_to_weekly(): Aggregate daily data to weekly bars
- aggregate_to_monthly(): Aggregate daily data to monthly bars
"""

import pandas as pd
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def aggregate_to_weekly(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate daily OHLCV data to weekly bars.
    
    Aggregation rules:
    - Open: First day's open of the week
    - High: Maximum high of the week
    - Low: Minimum low of the week
    - Close: Last day's close of the week
    - Volume: Sum of week's volumes
    - Week boundary: Monday to Sunday
    
    Args:
        df: DataFrame with OHLCV data indexed by date
    
    Returns:
        DataFrame with weekly aggregated data
    """
    try:
        if df.empty:
            return df
        
        # Ensure index is datetime
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)
        
        # Resample to weekly (W-SUN = week ending on Sunday)
        weekly = df.resample('W-SUN').agg({
            'Open': 'first',
            'High': 'max',
            'Low': 'min',
            'Close': 'last',
            'Volume': 'sum'
        })
        
        # Drop rows with NaN (incomplete weeks)
        weekly = weekly.dropna()
        
        logger.debug(f"Aggregated {len(df)} daily bars to {len(weekly)} weekly bars")
        return weekly
        
    except Exception as e:
        logger.error(f"Error aggregating to weekly: {e}")
        return pd.DataFrame()


def aggregate_to_monthly(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate daily OHLCV data to monthly bars.
    
    Aggregation rules:
    - Open: First day's open of the month
    - High: Maximum high of the month
    - Low: Minimum low of the month
    - Close: Last day's close of the month
    - Volume: Sum of month's volumes
    - Month boundary: Calendar month
    
    Args:
        df: DataFrame with OHLCV data indexed by date
    
    Returns:
        DataFrame with monthly aggregated data
    """
    try:
        if df.empty:
            return df
        
        # Ensure index is datetime
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)
        
        # Resample to monthly (ME = month end)
        monthly = df.resample('ME').agg({
            'Open': 'first',
            'High': 'max',
            'Low': 'min',
            'Close': 'last',
            'Volume': 'sum'
        })
        
        # Drop rows with NaN (incomplete months)
        monthly = monthly.dropna()
        
        logger.debug(f"Aggregated {len(df)} daily bars to {len(monthly)} monthly bars")
        return monthly
        
    except Exception as e:
        logger.error(f"Error aggregating to monthly: {e}")
        return pd.DataFrame()
