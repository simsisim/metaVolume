#!/usr/bin/env python3
"""
Highest Volume Ever (HVE) Screener - Main Pipeline
===================================================

Main entry point for HVE analysis following metaData_v1 patterns.

This tool:
1. Generates ticker files based on ticker_choice
2. Loads market data using DataReader
3. Screens for Highest Volume Ever (HVE) and Highest Volume Days (HVD) events
4. Exports historical baseline CSVs and per-ticker text cards

Usage:
    python main.py
"""

import argparse
import copy
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
from src.vol_daily_checker import VolChecker
from src.hv1y_checker import HV1YChecker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def _display_end_date(end_date) -> str:
    """
    hve_end_date is blank='use latest available date', but a blank CSV cell
    parses through pandas as NaN and gets stringified to the literal text
    'nan' by the str() config converter -- normalize that (and other blank
    spellings) to a readable label instead of printing "to nan".
    """
    if end_date and str(end_date).strip().lower() not in ('', 'nan', 'none', 'nat'):
        return str(end_date)
    return 'latest available'


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


def run_post_process(config: Config, user_config: UserConfiguration) -> None:
    """
    Run VolChecker (the daily incremental checker) once per configured
    timeframe -- reuses the same 'timeframes' setting the pre-processor
    iterates over (TIMEFRAMES in user_data.csv), so there's no separate
    post-process timeframe list to keep in sync. Each timeframe tracks its
    own baseline, cutoff, and output independently (results/post/{timeframe}/).
    """
    timeframes = user_config.timeframes if hasattr(user_config, 'timeframes') and user_config.timeframes else ['daily']
    for timeframe in timeframes:
        checker = VolChecker(config, user_config, timeframe=timeframe)
        checker.run(since_date_override=user_config.vol_checker_tw_since_date)


def run_hv1y_check(config: Config, user_config: UserConfiguration) -> None:
    """
    Run HV1YChecker once per configured timeframe. Independent of
    hve_pre_process/hve_post_process -- gated only by hv1y_enable, since a
    rolling-window recompute doesn't depend on either the baseline rebuild
    or the incremental checker having run.
    """
    timeframes = user_config.timeframes if hasattr(user_config, 'timeframes') and user_config.timeframes else ['daily']
    for timeframe in timeframes:
        checker = HV1YChecker(config, user_config, timeframe=timeframe)
        checker.run()


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

        # Initialize HVE Screener with user configuration.
        # date_range_mode is always 'fixed': start_date/end_date (end blank =
        # latest available date) fully describe the scan window -- there's no
        # separate rolling-N-years mode exposed in config anymore.
        hve_screener = HVEScreener(
            min_price=user_config.hve_min_price,
            min_volume=user_config.hve_min_volume,
            hv1y_enabled=user_config.hv1y_enable,
            hv1y_window_days=user_config.hv1y_window_days,
            date_range_mode='fixed',
            start_date=user_config.hve_start_date,
            end_date=user_config.hve_end_date
        )

        # Initialize HVD Screener with user configuration (same date window as HVE)
        hvd_screener = HVDScreener(
            min_price=user_config.hve_min_price,
            min_volume=user_config.hve_min_volume,
            max_events=user_config.hvd_historical_max_events,
            date_range_mode='fixed',
            start_date=user_config.hve_start_date,
            end_date=user_config.hve_end_date
        )

        # Initialize DataReader
        print(f"\n📖 Initializing DataReader for {timeframe}...")
        # Pre-process is the authoritative baseline rebuild -- source only
        # from the slow/vetted pipeline (archive/current), not the fast
        # market_data_batch/ overlay, so its cutoff date is deterministic.
        data_reader = DataReader(config, timeframe, batch_size=user_config.batch_size,
                                  include_batch_overlay=False)

        # Print data summary
        print_data_summary(data_reader, timeframe)


        # Always full-scan mode: the on-disk preload feature was retired in
        # favor of results/pre/historical/ + VolChecker's incremental
        # checker, so this dict stays empty and hve_screener always
        # detects HVE events from scratch here.
        baseline_hve_volumes = {}  # Dict of ticker -> max_volume

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
                if user_config.hve_pre_process:
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
                if user_config.hve_pre_process:
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
            hve_results_file = output_base / f'HVE_{timeframe}.csv'
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
            hvd_results_file = output_base / f'HVD_{timeframe}.csv'
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
            hv1y_results_file = output_base / f'HV1Y_{timeframe}.csv'
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


# ============================================================================
# PRESETS
# ============================================================================
CONFIG_PRESETS = {
    'preprocess': {
        'hve_pre_process':  True,
        'hve_post_process': False,
    },
    'preprocess_full': {           # same but forces full universe
        'hve_pre_process':  True,
        'hve_post_process': False,
        'ticker_choice':    '0',
    },
    'postprocess': {
        'hve_pre_process':  False,
        'hve_post_process': True,
    },
}


# ============================================================================
# COMMAND-LINE ARGUMENT PARSER
# ============================================================================
def parse_arguments():
    """Parse command-line arguments. Only explicitly provided args override the CSV."""
    parser = argparse.ArgumentParser(
        description='metaVolume — HVE/HVD screener and daily volume checker',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Modes (presets):
  preprocess       Generate HVE/HVD historical baseline files (run once)
  preprocess_full  Same as preprocess but forces ticker_choice=0 (full universe)
  postprocess      Run VOL daily checker only (run every trading day)

Examples:
  python main.py --preset preprocess_full
  python main.py --preset postprocess --ticker-choice 2
  python main.py --preset postprocess --ticker-choice 2 --since-date 2026-05-21
  python main.py --ticker-choice 2 --no-post-process

Ticker choice values:
  0: TradingView Universe (~6348 tickers)
  1: S&P 500
  2: NASDAQ 100
  3: All NASDAQ stocks
  4: Russell 1000
  5: Index tickers (QQQ SPY IWM …)
  6: Portfolio tickers
  7: ETF tickers
  8: Test tickers (AMD TXN NVDA)
        '''
    )

    parser.add_argument('--preset', type=str, choices=CONFIG_PRESETS.keys(),
                        help='Use a predefined mode configuration')

    parser.add_argument('--ticker-choice', type=str, dest='ticker_choice',
                        help='Ticker group (e.g. "2" for NASDAQ 100, "1-2" for S&P500+NASDAQ100)')

    parser.add_argument('--pre-process', dest='hve_pre_process', action='store_true',
                        help='Enable HVE/HVD pre-processor (full scan + historical export)')
    parser.add_argument('--no-pre-process', dest='hve_pre_process', action='store_false',
                        help='Disable HVE/HVD pre-processor')

    parser.add_argument('--post-process', dest='hve_post_process', action='store_true',
                        help='Enable incremental checker (VolChecker, one per configured timeframe)')
    parser.add_argument('--no-post-process', dest='hve_post_process', action='store_false',
                        help='Disable daily incremental checker')

    parser.add_argument('--since-date', type=str, dest='vol_checker_tw_since_date',
                        help='Force VOL checker to reprocess TW files since YYYY-MM-DD')

    args = parser.parse_args()

    # Only include args that were explicitly provided on the command line
    flag_to_dest = {
        '--ticker-choice':     'ticker_choice',
        '--pre-process':       'hve_pre_process',
        '--no-pre-process':    'hve_pre_process',
        '--post-process':      'hve_post_process',
        '--no-post-process':   'hve_post_process',
        '--since-date':        'vol_checker_tw_since_date',
    }
    provided = {flag_to_dest[a] for a in sys.argv[1:] if a in flag_to_dest}
    cli_dict = {k: v for k, v in vars(args).items() if k != 'preset' and k in provided}

    return args.preset, cli_dict


# ============================================================================
# CONFIGURATION MERGING
# ============================================================================
def merge_configs(base_config, config_override=None, preset=None, cli_args=None):
    """
    Merge settings with priority: CLI args > preset > config_override > CSV base.
    config_override is a plain dict — used for Colab calls like main(config_override={...}).
    """
    merged = copy.deepcopy(base_config)

    # Priority 1: preset
    if preset:
        if preset not in CONFIG_PRESETS:
            print(f"⚠️  Unknown preset '{preset}'. Available: {', '.join(CONFIG_PRESETS)}")
        else:
            print(f"   Using preset: {preset}")
            for key, value in CONFIG_PRESETS[preset].items():
                if hasattr(merged, key):
                    setattr(merged, key, value)

    # Priority 2: config_override dict (Colab)
    if config_override:
        print(f"   Applying overrides: {list(config_override.keys())}")
        for key, value in config_override.items():
            if hasattr(merged, key):
                setattr(merged, key, value)
            else:
                print(f"⚠️  Unknown override key '{key}' — ignored")

    # Priority 3: CLI args (highest priority)
    if cli_args:
        print(f"   Applying CLI args: {list(cli_args.keys())}")
        for key, value in cli_args.items():
            if hasattr(merged, key):
                setattr(merged, key, value)
            else:
                print(f"⚠️  Unknown CLI arg '{key}' — ignored")

    return merged


def main(config_override=None, preset=None):
    """Main entry point.

    Args:
        config_override (dict): Key/value overrides for Colab usage, e.g.
            main(config_override={'ticker_choice': '2', 'hve_post_process': True})
        preset (str): Named preset — 'preprocess', 'preprocess_full', 'postprocess'.
    """
    print("="*60)
    print("HIGHEST VOLUME EVER (HVE) SCREENER")
    print("="*60)

    try:
        # Setup logging
        setup_logging()

        # Load configuration
        print("\n1. Loading configuration...")
        base_config = read_user_data()
        config = Config()

        # Parse CLI args (ignored when called from Colab with config_override)
        cli_preset, cli_args = None, {}
        if len(sys.argv) > 1:
            cli_preset, cli_args = parse_arguments()

        # Merge: CLI > preset (CLI or Colab arg) > config_override > CSV base
        final_preset = cli_preset or preset
        user_config = merge_configs(base_config, config_override, final_preset, cli_args)

        print("   ✓ Configuration loaded")
        print(f"   ✓ Ticker choice: {user_config.ticker_choice}")
        print(f"   ✓ Batch size: {user_config.batch_size}")
        print(f"   ✓ HVE date range: {user_config.hve_start_date} to {_display_end_date(user_config.hve_end_date)}")
        print(f"   ✓ HVE min price: ${user_config.hve_min_price}")
        print(f"   ✓ HV1Y enabled: {user_config.hv1y_enable}")
        if user_config.hv1y_enable:
            print(f"   ✓ HV1Y window: {user_config.hv1y_window_days} days")

        # Check if pre-processing is enabled
        if not user_config.hve_pre_process:
            print("\n⚠️  HVE pre-processing is disabled — skipping to VOL checker")
            if user_config.hve_post_process:
                run_post_process(config, user_config)
            else:
                print("⏭️  Post-process also disabled (HVE_post_process=FALSE)")
            if user_config.hv1y_enable:
                run_hv1y_check(config, user_config)
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

            # ticker_cards/ is a sibling of pre/ and post/, not nested under either
            card_generator = TickerCardGenerator(str(Path(user_config.hve_output_dir).parent))
            cards_generated = card_generator.generate_all_cards(all_hve_results)

            print(f"\n✅ Generated {cards_generated} ticker cards")
            print(f"   Location: {card_generator.ticker_cards_dir}")

            # ================================================================
            # HISTORICAL VOLUME EXPORT - HVE AND HVD
            # ================================================================
            # Both HVE (temporal milestones) and HVD (magnitude ranking) are
            # exported together whenever hve_pre_process is TRUE -- there's
            # no separate per-metric toggle.
            # ================================================================

            # Accumulated multi-run baselines (HVD/HVE_historical_*.csv,
            # baseline_metadata.json) live in their own subfolder, separate
            # from the per-run daily/weekly/monthly outputs and ticker cards.
            output_dir = Path(user_config.hve_output_dir) / 'historical'

            # ----------------------------------------------------------
            # HVE Historical Export (temporal milestones)
            # ----------------------------------------------------------
            if user_config.hve_pre_process and all_hve_results:
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
                print(f"   Date range: {user_config.hve_start_date} to {_display_end_date(user_config.hve_end_date)}")
            elif user_config.hve_pre_process:
                print("\n⚠️  HVE pre-process enabled but no HVE results found")

            # ----------------------------------------------------------
            # HVD Historical Export (top volume days by magnitude)
            # ----------------------------------------------------------
            if user_config.hve_pre_process and all_hvd_results:
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
                print(f"   Date range: {user_config.hve_start_date} to {_display_end_date(user_config.hve_end_date)}")
            elif user_config.hve_pre_process:
                print("\n⚠️  HVD pre-process enabled but no HVD results found")
        else:
            print("\n⚠️  No results to generate ticker cards")

        # ================================================================
        # VOL CHECKER (post-process)
        # ================================================================
        # Reads the frozen HVE/HVD baseline from results/pre/historical/
        # + only new data since each timeframe's own cutoff. Runs
        # independently from the pre-process pipeline above -- no
        # full-history rescan, no data download required.
        # ================================================================
        if user_config.hve_post_process:
            run_post_process(config, user_config)
        else:
            print("\n⏭️  Post-process disabled (HVE_post_process=FALSE)")

        # ================================================================
        # HV1Y CHECKER (independent of pre/post -- see run_hv1y_check())
        # ================================================================
        if user_config.hv1y_enable:
            run_hv1y_check(config, user_config)

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
