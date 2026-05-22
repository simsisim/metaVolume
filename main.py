#!/usr/bin/env python3
"""
Highest Volume Ever (HVE) Screener - Main Pipeline
===================================================

Main entry point for HVE analysis following metaData_v1 patterns.

This tool:
1. Generates ticker files based on ticker_choice
2. Loads market data using DataReader
3. Screens for Highest Volume Ever (HVE) events
4. Creates Excel reports and visualizations

Usage:
    python main.py
"""

import pandas as pd
import sys
import logging
import math
from pathlib import Path
from typing import List, Dict

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import Config
from src.user_defined_data import read_user_data, UserConfiguration
from src.data_reader import DataReader
from src.unified_ticker_generator import generate_all_ticker_files
from src.hve_screener import HVEScreener
from src.hvd_screener import HVDScreener
from src.ticker_card_generator import TickerCardGenerator
from src.hve_historical_exporter import export_all_timeframes_historical
from src.hvd_historical_exporter import export_all_timeframes_hvd
from src.vol_daily_checker import VolDailyChecker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def setup_logging() -> None:
    """Configure logging for the main pipeline."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logging.getLogger().setLevel(logging.WARNING)  # Reduce noise


def setup_output_directories(config: Config, timeframe: str) -> Path:
    """
    Create output directories for a specific timeframe.

    Args:
        config: Config object with directory paths
        timeframe: Timeframe name ('daily', 'weekly', 'monthly')

    Returns:
        Path: Output base directory for the timeframe
    """
    try:
        # Get HVE output directory from user config
        user_config = read_user_data()
        output_base = Path(user_config.hve_output_dir) / timeframe
        output_base.mkdir(parents=True, exist_ok=True)

        # Create subdirectories
        (output_base / 'details').mkdir(exist_ok=True)
        (output_base / 'charts').mkdir(exist_ok=True)

        print(f"📁 Output directory: {output_base}")
        logger.info(f"Output directory for {timeframe}: {output_base}")
        return output_base

    except Exception as e:
        logger.error(f"Error setting up directories for {timeframe}: {e}")
        raise


def print_data_summary(data_reader: DataReader, timeframe: str) -> None:
    """
    Print data summary for a timeframe.

    Args:
        data_reader: DataReader instance
        timeframe: Timeframe name
    """
    try:
        summary = data_reader.get_data_summary()
        print(f"📊 Data summary: {summary['available_files']} files, "
              f"{summary['valid_files']} valid, "
              f"avg {summary['avg_data_points']} points per ticker")

        if summary['date_range']['start']:
            print(f"📅 Date range: {summary['date_range']['start']} to {summary['date_range']['end']}")

        logger.info(f"{timeframe} data summary: {summary}")

    except Exception as e:
        print(f"⚠️  Could not generate data summary: {e}")
        logger.warning(f"Could not generate data summary for {timeframe}: {e}")


def process_timeframe(
    config: Config,
    user_config: UserConfiguration,
    timeframe: str,
    ticker_list: List[str]
) -> pd.DataFrame:
    """
    Process a single timeframe.

    Args:
        config: System configuration
        user_config: User configuration
        timeframe: Timeframe to process ('daily', 'weekly', 'monthly')
        ticker_list: List of ticker symbols

    Returns:
        Dictionary with 'hve' and 'hvd' DataFrames for this timeframe
    """
    print(f"\n{'='*60}")
    print(f"PROCESSING {timeframe.upper()} TIMEFRAME")
    print(f"{'='*60}")

    try:
        # Setup output directories
        output_base = setup_output_directories(config, timeframe)

        # Initialize HVE Screener with user configuration
        hve_screener = HVEScreener(
            limit_hist_years=user_config.hve_limit_years,
            min_price=user_config.hve_min_price,
            min_volume=user_config.hve_min_volume,
            hv1y_enabled=user_config.hv1y_enable,
            hv1y_window_days=user_config.hv1y_window_days,
            date_range_mode=user_config.hve_date_range_mode,
            start_date=user_config.hve_start_date,
            end_date=user_config.hve_end_date
        )

        # Initialize HVD Screener with user configuration
        hvd_screener = HVDScreener(
            limit_hist_years=user_config.hve_limit_years,  # Use same date filters as HVE for consistency
            min_price=user_config.hve_min_price,
            min_volume=user_config.hve_min_volume,
            max_events=user_config.hvd_historical_max_events,
            date_range_mode=user_config.hve_date_range_mode,
            start_date=user_config.hve_start_date,
            end_date=user_config.hve_end_date
        )

        # Initialize DataReader
        print(f"\n📖 Initializing DataReader for {timeframe}...")
        data_reader = DataReader(config, timeframe, batch_size=user_config.batch_size)

        # Print data summary
        print_data_summary(data_reader, timeframe)


        # ================================================================
        # PRELOAD BASELINE LOADING
        # ================================================================
        # Load pre-computed HVE/HVD max volumes as baselines
        # This enables incremental detection: only volumes EXCEEDING
        # historical maxes will be recorded as new HVE events
        # ================================================================
        baseline_hve_volumes = {}  # Dict of ticker -> max_volume
        baseline_hvd_volumes = {}  # Dict of ticker -> max_volume
        
        if user_config.preload_hve:
            print(f"\n📥 Loading preload baselines for {timeframe}...")
            
            # Load HVE preload and extract baselines
            if user_config.hve_enable and user_config.preload_hve_file:
                try:
                    from src.hve_preloader import load_hve_preload_data, get_preload_max_volumes
                    preload_hve_df = load_hve_preload_data(user_config.preload_hve_file, timeframe)
                    
                    if not preload_hve_df.empty:
                        baseline_hve_volumes = get_preload_max_volumes(preload_hve_df)
                        print(f"   ✓ Loaded baselines for {len(baseline_hve_volumes)} tickers")
                        print(f"   ℹ️  Will detect only NEW HVE events exceeding historical maxes")
                    else:
                        print(f"   ⚠️  No HVE preload baselines found for {timeframe}")
                        
                except FileNotFoundError:
                    print(f"   ⚠️  HVE preload file not found: {user_config.preload_hve_file}")
                except Exception as e:
                    print(f"   ⚠️  Failed to load HVE preload baselines: {e}")
                    logger.error(f"HVE preload error: {e}", exc_info=True)
                    
            # Load HVD preload and extract baselines (for future use)
            if user_config.hvd_historical_export and user_config.preload_hvd_file:
                try:
                    from src.hve_preloader import load_hvd_preload_data, get_preload_max_volumes
                    preload_hvd_df = load_hvd_preload_data(user_config.preload_hvd_file, timeframe)
                    
                    if not preload_hvd_df.empty:
                        baseline_hvd_volumes = get_preload_max_volumes(preload_hvd_df)
                        print(f"   ✓ Loaded HVD baselines for {len(baseline_hvd_volumes)} tickers")
                    else:
                        print(f"   ⚠️  No HVD preload baselines found for {timeframe}")
                        
                except FileNotFoundError:
                    print(f"   ⚠️  HVD preload file not found: {user_config.preload_hvd_file}")
                except Exception as e:
                    print(f"   ⚠️  Failed to load HVD preload baselines: {e}")
                    logger.error(f"HVD preload error: {e}", exc_info=True)

        # Process ALL tickers (don't skip any - we use baselines to filter instead)
        total_tickers = len(ticker_list)
        batch_size = user_config.batch_size
        total_batches = math.ceil(total_tickers / batch_size) if total_tickers > 0 else 0

        if total_tickers > 0:
            print(f"\n📦 Processing {total_tickers} tickers in {total_batches} batches of {batch_size}")

        all_hve_results = []
        all_hvd_results = []
        all_hv1y_results = []  # NEW: Separate HV1Y results collection

        for batch_num in range(total_batches):
            start_idx = batch_num * batch_size
            end_idx = min(start_idx + batch_size, total_tickers)
            batch_tickers = ticker_list[start_idx:end_idx]
            batch_count = batch_num + 1


            print(f"\n🔄 Processing batch {batch_count}/{total_batches} ({len(batch_tickers)} tickers)")

            try:
                # Read batch data with appropriate aggregation
                batch_data = data_reader.read_batch_data(
                    batch_tickers,
                    validate=True,
                    aggregate_to=timeframe  # Pass timeframe for aggregation
                )

                if not batch_data:
                    print(f"⚠️  No valid data in batch {batch_count}, skipping...")
                    continue

                print(f"✅ Loaded {len(batch_data)} valid tickers from batch {batch_count}")

                # Screen for HVE events (with baseline filtering for incremental detection)
                if user_config.hve_enable:
                    print(f"\n🔍 Screening for HVE events...")
                    
                    # Pass baseline volumes to filter for only NEW events exceeding historical maxes
                    hve_batch_results = hve_screener.screen_batch(
                        batch_data,
                        timeframe,
                        baseline_volumes=baseline_hve_volumes if baseline_hve_volumes else None
                    )

                    if not hve_batch_results.empty:
                        # Extract HV1Y data if HV1Y is enabled
                        if user_config.hv1y_enable:
                            hv1y_columns = [
                                'ticker', 'timeframe',
                                'hv1y_date', 'hv1y_volume', 'days_since_hv1y',
                                'hv1y_occ_1y', 'total_hv1y_count',
                                'is_hv1y_also_hve', 'hv1y_to_hve_ratio',
                                'all_hv1y_details'
                            ]
                            # Check which HV1Y columns actually exist
                            available_hv1y_cols = [col for col in hv1y_columns if col in hve_batch_results.columns]
                           
                            if available_hv1y_cols:
                                hv1y_batch_results = hve_batch_results[available_hv1y_cols].copy()
                                all_hv1y_results.append(hv1y_batch_results)
                            
                            # Remove HV1Y columns from HVE results
                            hve_columns = [col for col in hve_batch_results.columns if col not in hv1y_columns or col in ['ticker', 'timeframe']]
                            hve_batch_results = hve_batch_results[hve_columns]
                        
                        if baseline_hve_volumes:
                            print(f"✅ Found {len(hve_batch_results)} tickers with NEW HVE events (exceeding preload baselines)")
                        else:
                            print(f"✅ Found {len(hve_batch_results)} tickers with HVE data")
                        all_hve_results.append(hve_batch_results)
                    else:
                        if baseline_hve_volumes:
                            print(f"ℹ️  No new HVE events in batch {batch_count} (all volumes within baselines)")
                        else:
                            print(f"⚠️  No HVE events found in batch {batch_count}")

                # Screen for HVD events (top volume days by magnitude)
                if user_config.hvd_historical_export:  # Only run if HVD export is enabled
                    print(f"\n🔍 Screening for HVD events (top volume days)...")
                    hvd_batch_results = hvd_screener.screen_batch(batch_data, timeframe)

                    if not hvd_batch_results.empty:
                        print(f"✅ Found {len(hvd_batch_results)} tickers with HVD data")
                        all_hvd_results.append(hvd_batch_results)
                    else:
                        print(f"⚠️  No HVD events found in batch {batch_count}")

            except Exception as e:
                logger.error(f"Error processing batch {batch_count}: {e}")
                print(f"❌ Error processing batch {batch_count}: {e}")
                continue

        # Combine and save results
        result_dict = {'hve': pd.DataFrame(), 'hvd': pd.DataFrame()}

        # ================================================================
        # SAVE NEW HVE RESULTS (NO MERGING)
        # ================================================================
        # Output only NEW HVE events detected (those exceeding baselines)
        # Do not re-write old preload data
        # ================================================================
        
        # Process HVE results - save only NEW events
        if all_hve_results:
            combined_hve_results = pd.concat(all_hve_results, ignore_index=True)
            combined_hve_results = combined_hve_results.sort_values('days_since_hve')

            # Save HVE results
            hve_results_file = output_base / f'hve_results_{timeframe}.csv'
            combined_hve_results.to_csv(hve_results_file, index=False)
            
            print(f"\n✅ Saved {len(combined_hve_results)} NEW HVE results to {hve_results_file}")
            if baseline_hve_volumes:
                print(f"   (Detected by exceeding preload baselines for {len(baseline_hve_volumes)} tickers)")

            # Print HVE summary
            print(f"\n📊 {timeframe.upper()} NEW HVE EVENTS SUMMARY:")
            print(f"   Total tickers with NEW HVE events: {len(combined_hve_results)}")
            print(f"\n   Top 10 by recent HVE:")
            for i, row in combined_hve_results.head(10).iterrows():
                print(f"   {i+1}. {row['ticker']}: {row['days_since_hve']} days ago "
                      f"({row['hve_date'].strftime('%Y-%m-%d')}, vol={row['hve_volume']:,.0f}, "
                      f"HVE_1Y={row['hve_occ_1y']}, Total={row['total_hve_count']})")

            result_dict['hve'] = combined_hve_results
        else:
            if baseline_hve_volumes:
                print(f"\n✅ No new HVE events detected (all volumes within historical baselines)")
            else:
                print(f"\n⚠️  No HVE results for {timeframe} timeframe")

        # Process HVD results - save only NEW events  
        if all_hvd_results:
            combined_hvd_results = pd.concat(all_hvd_results, ignore_index=True)
            combined_hvd_results = combined_hvd_results.sort_values('days_since_hvd')

            # Save HVD results
            hvd_results_file = output_base / f'hvd_results_{timeframe}.csv'
            combined_hvd_results.to_csv(hvd_results_file, index=False)
            
            print(f"\n✅ Saved {len(combined_hvd_results)} HVD results to {hvd_results_file}")

            # Print HVD summary
            print(f"\n📊 {timeframe.upper()} HVD RESULTS SUMMARY:")
            print(f"   Total tickers with HVD data: {len(combined_hvd_results)}")
            print(f"\n   Top 10 by recent HVD:")
            for i, row in combined_hvd_results.head(10).iterrows():
                print(f"   {i+1}. {row['ticker']}: {row['days_since_hvd']} days ago "
                      f"({row['hvd_date'].strftime('%Y-%m-%d')}, vol={row['hvd_volume']:,.0f}, "
                      f"Count={row['hvd_count']})")

            result_dict['hvd'] = combined_hvd_results
        else:
            print(f"\n⚠️  No HVD results for {timeframe} timeframe")

        # Save HV1Y results separately
        if all_hv1y_results and user_config.hv1y_enable:
            combined_hv1y_results = pd.concat(all_hv1y_results, ignore_index=True)
            combined_hv1y_results = combined_hv1y_results.sort_values('days_since_hv1y')

            # Limit to max events per ticker if configured
            if user_config.hv1y_max_events > 0:
                print(f"\n🔧 Limiting to {user_config.hv1y_max_events} most recent HV1Y events per ticker...")
                limited_results = []
                for ticker in combined_hv1y_results['ticker'].unique():
                    ticker_data = combined_hv1y_results[
                        combined_hv1y_results['ticker'] == ticker
                    ].head(user_config.hv1y_max_events)
                    limited_results.append(ticker_data)
                combined_hv1y_results = pd.concat(limited_results, ignore_index=True)
                combined_hv1y_results = combined_hv1y_results.sort_values('days_since_hv1y')

            # Save to separate HV1Y file
            hv1y_results_file = output_base / f'hv1y_results_{timeframe}.csv'
            combined_hv1y_results.to_csv(hv1y_results_file, index=False)
            
            print(f"\n✅ Saved {len(combined_hv1y_results)} HV1Y results to {hv1y_results_file}")
            if user_config.hv1y_max_events > 0:
                print(f"   (Limited to {user_config.hv1y_max_events} events per ticker)")

            # Print HV1Y summary
            print(f"\n📊 {timeframe.upper()} HV1Y  RESULTS SUMMARY:")
            print(f"   Total HV1Y records: {len(combined_hv1y_results)}")
            print(f"\n   Top 10 by recent HV1Y:")
            for i, row in combined_hv1y_results.head(10).iterrows():
                is_hve = "✓" if row.get('is_hv1y_also_hve', False) else "✗"
                print(f"   {i+1}. {row['ticker']}: {row['days_since_hv1y']} days ago "
                      f"({row['hv1y_date'].strftime('%Y-%m-%d')}, vol={row['hv1y_volume']:,.0f}, "
                      f"Count={row['total_hv1y_count']}, Is_HVE={is_hve})")

            result_dict['hv1y'] = combined_hv1y_results
        else:
            if user_config.hv1y_enable:
                print(f"\n⚠️  No HV1Y results for {timeframe} timeframe")


        return result_dict

    except Exception as e:
        logger.error(f"Error processing {timeframe}: {e}")
        print(f"❌ Error processing {timeframe}: {e}")
        return {'hve': pd.DataFrame(), 'hvd': pd.DataFrame()}


def main():
    """Main entry point."""
    print("="*60)
    print("HIGHEST VOLUME EVER (HVE) SCREENER")
    print("="*60)

    try:
        # Setup logging
        setup_logging()

        # Load configuration
        print("\n1. Loading configuration...")
        user_config = read_user_data()
        config = Config()
        print("   ✓ Configuration loaded")
        print(f"   ✓ Ticker choice: {user_config.ticker_choice}")
        print(f"   ✓ Batch size: {user_config.batch_size}")
        print(f"   ✓ HVE limit years: {user_config.hve_limit_years}")
        print(f"   ✓ HVE min price: ${user_config.hve_min_price}")
        print(f"   ✓ HV1Y enabled: {user_config.hv1y_enable}")
        if user_config.hv1y_enable:
            print(f"   ✓ HV1Y window: {user_config.hv1y_window_days} days")

        # Check if HVE is enabled
        if not user_config.hve_enable:
            print("\n⚠️  HVE processing is disabled in user_data.csv")
            print("   Set HVE_enable to TRUE to enable")
            return

        # Generate ticker files
        print("\n2. Generating ticker files...")
        success = generate_all_ticker_files(config, user_config.ticker_choice)

        if not success:
            print("❌ Failed to generate ticker files")
            sys.exit(1)

        # Load ticker list
        print("\n3. Loading ticker list...")
        tickers_dir = Path(config.directories['TICKERS_DIR'])
        ticker_choice = user_config.ticker_choice

        # Use the clean file (this is the one used for processing)
        ticker_file = tickers_dir / f'combined_info_tickers_clean_{ticker_choice}.csv'

        if not ticker_file.exists():
            print(f"❌ Ticker file not found: {ticker_file}")
            sys.exit(1)

        df_tickers = pd.read_csv(ticker_file)
        ticker_list = df_tickers['ticker'].tolist()
        print(f"   ✓ Loaded {len(ticker_list)} tickers from choice {ticker_choice}")

        # Determine which timeframes to process from configuration
        timeframes = user_config.timeframes if hasattr(user_config, 'timeframes') and user_config.timeframes else ['daily']
        
        if not timeframes: # This check is technically redundant if default is ['daily'] but good for robustness
            print("\n⚠️  No timeframes enabled in user_data.csv")
            print("   Please ensure 'timeframes' is configured or YF_daily_data, YF_weekly_data, or YF_monthly_data are TRUE")
            return

        print(f"   ✓ Timeframes to process: {', '.join(timeframes)}")

        # Process each timeframe and collect results
        all_hve_results = {}
        all_hvd_results = {}
        for timeframe in timeframes:
            results = process_timeframe(config, user_config, timeframe, ticker_list)
            if not results['hve'].empty:
                all_hve_results[timeframe] = results['hve']
            if not results['hvd'].empty:
                all_hvd_results[timeframe] = results['hvd']

        # Generate ticker cards (using HVE results)
        if all_hve_results:
            print("\n" + "="*60)
            print("GENERATING TICKER CARDS")
            print("="*60)

            card_generator = TickerCardGenerator(user_config.hve_output_dir)
            cards_generated = card_generator.generate_all_cards(all_hve_results)

            print(f"\n✅ Generated {cards_generated} ticker cards")
            print(f"   Location: {card_generator.ticker_cards_dir}")

            # ================================================================
            # HISTORICAL VOLUME EXPORT - HVE AND HVD
            # ================================================================
            # Two distinct export methods, independently configurable:
            #
            # 1. HVE (Highest Volume Ever) - Temporal milestones
            #    - Progressive all-time volume highs
            #    - Tracks when new records were set
            #    - Use: Breakout detection, momentum analysis
            #    - Config: HVE_historical_export (TRUE/FALSE)
            #
            # 2. HVD (Highest Volume Days) - Magnitude ranking
            #    - Top N volume days, any time period
            #    - Pure volume sorting, no temporal constraint
            #    - Use: Liquidity analysis, volatility assessment
            #    - Config: HVD_historical_export (TRUE/FALSE)
            #
            # Both exports can run simultaneously or independently
            # ================================================================
            
            output_dir = Path(user_config.hve_output_dir)
            
            # ----------------------------------------------------------
            # HVE Historical Export (temporal milestones)
            # ----------------------------------------------------------
            if user_config.hve_historical_export and all_hve_results:
                print("\n" + "="*60)
                print("EXPORTING HISTORICAL HVE FORMAT")
                print("="*60)

                hve_exported = export_all_timeframes_historical(
                    all_hve_results,  # Use HVE results
                    output_dir,
                    max_events=user_config.hve_historical_max_events
                )

                print(f"\n✅ Exported {hve_exported} HVE (Highest Volume Ever) files")
                print(f"   Events per ticker: {user_config.hve_historical_max_events}")
                print(f"   Date range: {user_config.hve_start_date} to {user_config.hve_end_date}")
            elif user_config.hve_historical_export:
                print("\n⚠️  HVE historical export enabled but no HVE results found")
            else:
                print("\n⏭️  HVE historical export disabled (HVE_historical_export=FALSE)")

            # ----------------------------------------------------------
            # HVD Historical Export (top volume days by magnitude)
            # ----------------------------------------------------------
            if user_config.hvd_historical_export and all_hvd_results:
                print("\n" + "="*60)
                print("EXPORTING HISTORICAL HVD FORMAT")
                print("="*60)

                hvd_exported = export_all_timeframes_hvd(
                    all_hvd_results,  # Use HVD results (DIFFERENT from HVE!)
                    output_dir,
                    max_events=user_config.hvd_historical_max_events
                )

                print(f"\n✅ Exported {hvd_exported} HVD (Highest Volume Days) files")
                print(f"   Top events per ticker: {user_config.hvd_historical_max_events}")
                print(f"   Date range: {user_config.hve_start_date} to {user_config.hve_end_date}")
            elif user_config.hvd_historical_export:
                print("\n⚠️  HVD historical export enabled but no HVD results found")
            else:
                print("\n⏭️  HVD historical export disabled (HVD_historical_export=FALSE)")
        else:
            print("\n⚠️  No results to generate ticker cards")

        # ================================================================
        # VOL DAILY CHECKER
        # ================================================================
        # Reads HVD_historical_daily.csv baseline + TW bulk files.
        # Flags tickers whose new volume enters the top-N positions.
        # Runs independently from the HVD pipeline above — no data
        # download required, no data merging on disk.
        # ================================================================
        if user_config.vol_checker_enable:
            checker = VolDailyChecker(config, user_config)
            checker.run(since_date_override=user_config.vol_checker_tw_since_date)
        else:
            print("\n⏭️  Vol daily checker disabled (VOL_checker_enable=FALSE)")

        # Final summary
        print("\n" + "="*60)
        print("✅ HVE ANALYSIS COMPLETE")
        print("="*60)
        print(f"Results saved to: {user_config.hve_output_dir}")

    except KeyboardInterrupt:
        print("\n\n⚠️  Analysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
