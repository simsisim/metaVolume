"""
HVD (Highest Volume Days) Historical Exporter
=============================================

Exports HVD results - the top N volume days regardless of when they occurred.
Unlike HVE (temporal milestones), HVD finds the highest magnitude volume days.

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
  2020-05-25: 7,000  → NOT HVE (below record, but still high!)

HVE exports (temporal): [2020-04-20: 8,000, 2020-02-10: 5,000, 2020-01-05: 1,000]
HVD exports (magnitude): [2020-04-20: 8,000, 2020-05-25: 7,000, 2020-02-10: 5,000, ...]
                         ↑ Same          ↑ INCLUDED (high volume, not HVE)

Real-World Use Case:
-------------------
- HVE: "When did this stock reach new volume records?" → Momentum tracking
- HVD: "What were the most liquid trading days?" → Liquidity/volatility analysis

Configuration (user_data.csv):
------------------------------
HVD_historical_export,TRUE     # Enable/disable HVD export
HVD_historical_max_days,10     # Number of top volume days to export
"""

import pandas as pd
import logging
from typing import Dict, List
from pathlib import Path

logger = logging.getLogger(__name__)


def export_hvd_historical(
    results_df: pd.DataFrame,
    output_path: Path,
    max_days: int = 10,
    timeframe: str = "daily"
) -> bool:
    """
    Export HVD results - top N volume days by magnitude.

    Args:
        results_df: DataFrame with HVE screening results (contains all_hve_details)
        output_path: Path to save the CSV file
        max_days: Maximum number of top volume days to export per ticker
        timeframe: Timeframe being exported

    Returns:
        bool: True if export successful, False otherwise
    """
    try:
        if results_df.empty:
            logger.warning("No results to export for HVD")
            return False

        # Build the output data
        export_rows = []

        for _, row in results_df.iterrows():
            ticker = row['ticker']
            
            # Get all HVE details for this ticker
            # NOTE: all_hve_details contains ALL volume data, not just HVEs
            # We need to extract the raw volume history to find top days
            all_hve_details = row.get('all_hve_details', [])
            
            if not all_hve_details:
                logger.warning(f"{ticker}: No volume data found, skipping HVD export")
                continue

            # Sort by volume (descending) to get top days
            top_days = sorted(all_hve_details, key=lambda x: x['volume'], reverse=True)
            
            # Limit to max_days
            top_days = top_days[:max_days]

            # Build the export row
            export_row = {
                'Symbol': ticker,
                'timeframe': timeframe
            }

            # Add each top volume day as HVD_date_1, HVD_vol_1, etc.
            for i, day in enumerate(top_days, start=1):
                hvd_date = day['date']
                hvd_volume = day['volume']
                
                # Format date as YYYY-MM-DD
                date_str = pd.Timestamp(hvd_date).strftime('%Y-%m-%d')
                
                export_row[f'HVD_date_{i}'] = date_str
                export_row[f'HVD_vol_{i}'] = int(hvd_volume)

            # Pad remaining columns if fewer than max_days
            for i in range(len(top_days) + 1, max_days + 1):
                export_row[f'HVD_date_{i}'] = ""
                export_row[f'HVD_vol_{i}'] = ""

            export_rows.append(export_row)

        if not export_rows:
            logger.warning("No valid HVD export rows generated")
            return False

        # Create DataFrame
        export_df = pd.DataFrame(export_rows)

        # Ensure proper column order: Symbol, timeframe, HVD_date_1, HVD_vol_1, ...
        columns = ['Symbol', 'timeframe']
        for i in range(1, max_days + 1):
            columns.append(f'HVD_date_{i}')
            columns.append(f'HVD_vol_{i}')

        export_df = export_df[columns]

        # Save to CSV
        output_path.parent.mkdir(parents=True, exist_ok=True)
        export_df.to_csv(output_path, index=False)

        logger.info(f"Exported {len(export_df)} tickers with top {max_days} volume days each to {output_path}")
        print(f"\n✅ Exported HVD (Top Volume Days) results to: {output_path}")
        print(f"   {len(export_df)} tickers × {max_days} top volume days per ticker")

        return True

    except Exception as e:
        logger.error(f"Error exporting HVD historical: {e}")
        print(f"❌ Error exporting HVD historical: {e}")
        return False


def export_all_timeframes_hvd(
    all_timeframe_results: Dict[str, pd.DataFrame],
    output_dir: Path,
    max_days: int = 10
) -> int:
    """
    Export HVD historical results for all timeframes.

    Args:
        all_timeframe_results: Dictionary mapping timeframe -> results DataFrame
        output_dir: Base output directory
        max_days: Maximum number of top volume days to export per ticker

    Returns:
        int: Number of files successfully exported
    """
    exported_count = 0

    for timeframe, results_df in all_timeframe_results.items():
        output_path = output_dir / f'sample_results_HVD_historical_{timeframe}.csv'
        
        if export_hvd_historical(results_df, output_path, max_days, timeframe):
            exported_count += 1

    return exported_count
