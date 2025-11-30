"""
HVE (Highest Volume Ever) Historical Exporter
==============================================

Exports HVE results in historical format with configurable number of events.
Generates wide-format CSV with most recent N HVE events per ticker.

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
  2020-05-25: 7,000  → NOT HVE

HVE exports: [2020-04-20: 8,000, 2020-02-10: 5,000, 2020-01-05: 1,000]
HVD exports: [2020-04-20: 8,000, 2020-05-25: 7,000, 2020-02-10: 5,000, ...]

Configuration (user_data.csv):
------------------------------
HVE_historical_export,TRUE     # Enable/disable HVE export
HVE_historical_max_events,10   # Number of HVE events to export
"""

import pandas as pd
import logging
from typing import Dict, List
from pathlib import Path

logger = logging.getLogger(__name__)


def export_hve_historical(
    results_df: pd.DataFrame,
    output_path: Path,
    max_events: int = 10,
    timeframe: str = "daily"
) -> bool:
    """
    Export HVE results in historical format with N most recent events.

    Args:
        results_df: DataFrame with HVE screening results
        output_path: Path to save the CSV file
        max_events: Maximum number of HVE events to export per ticker
        timeframe: Timeframe being exported

    Returns:
        bool: True if export successful, False otherwise
    """
    try:
        if results_df.empty:
            logger.warning("No results to export")
            return False

        # Build the output data
        export_rows = []

        for _, row in results_df.iterrows():
            ticker = row['ticker']
            
            # Get all HVE details for this ticker
            all_hve_details = row.get('all_hve_details', [])
            
            if not all_hve_details:
                logger.warning(f"{ticker}: No HVE details found, skipping")
                continue

            # Build the export row
            export_row = {
                'Symbol': ticker,
                'timeframe': timeframe
            }

            # Extract the N most recent HVE events (they're already sorted by date, most recent first)
            # Limit to max_events
            events_to_export = all_hve_details[:max_events]

            # Add each event as HVE_date_1, HVE_vol_1, HVE_date_2, HVE_vol_2, etc.
            for i, event in enumerate(events_to_export, start=1):
                hve_date = event['date']
                hve_volume = event['volume']
                
                # Format date as YYYY-MM-DD
                date_str = pd.Timestamp(hve_date).strftime('%Y-%m-%d')
                
                export_row[f'HVE_date_{i}'] = date_str
                export_row[f'HVE_vol_{i}'] = int(hve_volume)

            # Pad remaining columns if fewer than max_events
            for i in range(len(events_to_export) + 1, max_events + 1):
                export_row[f'HVE_date_{i}'] = ""
                export_row[f'HVE_vol_{i}'] = ""

            export_rows.append(export_row)

        if not export_rows:
            logger.warning("No valid export rows generated")
            return False

        # Create DataFrame
        export_df = pd.DataFrame(export_rows)

        # Ensure proper column order: Symbol, timeframe, HVE_date_1, HVE_vol_1, ...
        columns = ['Symbol', 'timeframe']
        for i in range(1, max_events + 1):
            columns.append(f'HVE_date_{i}')
            columns.append(f'HVE_vol_{i}')

        export_df = export_df[columns]

        # Save to CSV
        output_path.parent.mkdir(parents=True, exist_ok=True)
        export_df.to_csv(output_path, index=False)

        logger.info(f"Exported {len(export_df)} tickers with {max_events} HVE events each to {output_path}")
        print(f"\n✅ Exported historical HVE results to: {output_path}")
        print(f"   {len(export_df)} tickers × {max_events} HVE events per ticker")

        return True

    except Exception as e:
        logger.error(f"Error exporting historical HVE: {e}")
        print(f"❌ Error exporting historical HVE: {e}")
        return False


def export_all_timeframes_historical(
    all_timeframe_results: Dict[str, pd.DataFrame],
    output_dir: Path,
    max_events: int = 10
) -> int:
    """
    Export historical HVE results for all timeframes.

    Args:
        all_timeframe_results: Dictionary mapping timeframe -> results DataFrame
        output_dir: Base output directory
        max_events: Maximum number of HVE events to export per ticker

    Returns:
        int: Number of files successfully exported
    """
    exported_count = 0

    for timeframe, results_df in all_timeframe_results.items():
        output_path = output_dir / f'sample_results_HVE_historical_{timeframe}.csv'
        
        if export_hve_historical(results_df, output_path, max_events, timeframe):
            exported_count += 1

    return exported_count
