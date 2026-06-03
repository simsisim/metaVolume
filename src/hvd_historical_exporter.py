"""
HVD (Highest Volume Days) Historical Exporter
=============================================

Exports HVD results from HVDScreener - the top N volume days by magnitude,
regardless of when they occurred.

Unlike HVE (temporal milestones), HVD finds the highest volume days without
temporal constraints. This exporter receives data from HVDScreener, not HVEScreener.

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

import json
import pandas as pd
import logging
from datetime import datetime
from typing import Dict, List
from pathlib import Path

logger = logging.getLogger(__name__)


def write_baseline_metadata(
    output_dir: Path,
    all_timeframe_results: Dict[str, pd.DataFrame],
) -> None:
    """
    Write baseline_metadata.json alongside the HVD historical CSVs.

    Records the maximum date found across all tickers/timeframes so that
    VolDailyChecker (Yahoo mode) knows exactly where the baseline ends and
    can refuse to re-process already-covered data.
    """
    try:
        all_dates = []
        ticker_set = set()

        for results_df in all_timeframe_results.values():
            if results_df.empty:
                continue
            ticker_set.update(results_df['ticker'].tolist())
            for details in results_df.get('all_hvd_details', pd.Series(dtype=object)):
                if isinstance(details, list):
                    for ev in details:
                        try:
                            all_dates.append(
                                pd.Timestamp(ev['date']).date()
                            )
                        except Exception:
                            pass

        baseline_as_of = max(all_dates).strftime('%Y-%m-%d') if all_dates else ''

        metadata = {
            'baseline_as_of_date': baseline_as_of,
            'generated_at': datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
            'ticker_count': len(ticker_set),
            'source': 'yahoo',
        }

        output_dir.mkdir(parents=True, exist_ok=True)
        meta_path = output_dir / 'baseline_metadata.json'
        meta_path.write_text(json.dumps(metadata, indent=2))
        print(f"   Baseline metadata written: {meta_path}")
        print(f"   baseline_as_of_date: {baseline_as_of}")

    except Exception as e:
        logger.warning(f"Could not write baseline_metadata.json: {e}")


def export_hvd_historical(
    results_df: pd.DataFrame,
    output_path: Path,
    max_events: int = 10,
    timeframe: str = "daily"
) -> bool:
    """
    Export HVD results - top N volume days by magnitude.

    Args:
        results_df: DataFrame with HVD screening results from HVDScreener
                   (contains all_hvd_details with top volume days)
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

            # Get all HVD details for this ticker
            # NOTE: all_hvd_details comes from HVDScreener and contains
            # the top N volume days already sorted by magnitude
            all_hvd_details = row.get('all_hvd_details', [])

            if not all_hvd_details:
                logger.warning(f"{ticker}: No HVD data found, skipping HVD export")
                continue

            # Sort by volume (descending) to get top days
            # (already sorted by HVDScreener, but ensure consistency)
            top_days = sorted(all_hvd_details, key=lambda x: x['volume'], reverse=True)
            
            # Limit to max_events
            events_to_export = all_hvd_details[:max_events]

            # Build the export row
            export_row = {
                'Symbol': ticker,
                'timeframe': timeframe
            }

            # Add each event as HVD_date_1, HVD_vol_1, HVD_date_2, HVD_vol_2, etc.
            for i, day_event in enumerate(events_to_export, start=1):
                hvd_date = day_event['date']
                hvd_volume = day_event['volume']
                
                # Format date as YYYY-MM-DD
                date_str = pd.Timestamp(hvd_date).strftime('%Y-%m-%d')
                
                export_row[f'HVD_date_{i}'] = date_str
                export_row[f'HVD_vol_{i}'] = int(hvd_volume)

            # Pad remaining columns if fewer than max_events
            for i in range(len(events_to_export) + 1, max_events + 1):
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
        for i in range(1, max_events + 1):
            columns.append(f'HVD_date_{i}')
            columns.append(f'HVD_vol_{i}')

        export_df = export_df[columns]

        # Save to CSV
        output_path.parent.mkdir(parents=True, exist_ok=True)
        export_df.to_csv(output_path, index=False)

        logger.info(f"Exported {len(export_df)} tickers with {max_events} HVD events each to {output_path}")
        print(f"\n✅ Exported historical HVD results to: {output_path}")
        print(f"   {len(export_df)} tickers × {max_events} HVD events per ticker")

        return True

    except Exception as e:
        logger.error(f"Error exporting HVD historical: {e}")
        print(f"❌ Error exporting HVD historical: {e}")
        return False


def export_all_timeframes_hvd(
    all_timeframe_results: Dict[str, pd.DataFrame],
    output_dir: Path,
    max_events: int = 10
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
        output_path = output_dir / f'HVD_historical_{timeframe}.csv'

        if export_hvd_historical(results_df, output_path, max_events, timeframe):
            exported_count += 1

    if exported_count > 0:
        write_baseline_metadata(output_dir, all_timeframe_results)

    return exported_count
