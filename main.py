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
from src.ticker_card_generator import TickerCardGenerator
from src.hve_historical_exporter import export_all_timeframes_historical
from src.hvd_historical_exporter import export_all_timeframes_hvd

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
        DataFrame with combined results for this timeframe, or empty DataFrame
    """
    print(f"\n{'='*60}")
    print(f"PROCESSING {timeframe.upper()} TIMEFRAME")
    print(f"{'='*60}")

    try:
        # Setup output directories
        output_base = setup_output_directories(config, timeframe)

        # Initialize HVE Screener with user configuration
        screener = HVEScreener(
            limit_hist_years=user_config.hve_limit_years,
            min_price=user_config.hve_min_price,
            min_volume=user_config.hve_min_volume,
            hv1y_enabled=user_config.hv1y_enable,
            hv1y_window_days=user_config.hv1y_window_days,
            date_range_mode=user_config.hve_date_range_mode,
            start_date=user_config.hve_start_date,
            end_date=user_config.hve_end_date
        )

        # Initialize DataReader
        print(f"\n📖 Initializing DataReader for {timeframe}...")
        data_reader = DataReader(config, timeframe, batch_size=user_config.batch_size)

        # Print data summary
        print_data_summary(data_reader, timeframe)

        # Process in batches
        total_tickers = len(ticker_list)
        batch_size = user_config.batch_size
        total_batches = math.ceil(total_tickers / batch_size)

        print(f"\n📦 Processing {total_tickers} tickers in {total_batches} batches of {batch_size}")

        all_results = []

        for batch_num in range(total_batches):
            start_idx = batch_num * batch_size
            end_idx = min(start_idx + batch_size, total_tickers)
            batch_tickers = ticker_list[start_idx:end_idx]
            batch_count = batch_num + 1

            print(f"\n🔄 Processing batch {batch_count}/{total_batches} ({len(batch_tickers)} tickers)")

            try:
                # Read batch data
                batch_data = data_reader.read_batch_data(batch_tickers, validate=True)

                if not batch_data:
                    print(f"⚠️  No valid data in batch {batch_count}, skipping...")
                    continue

                print(f"✅ Loaded {len(batch_data)} valid tickers from batch {batch_count}")

                # Screen for HVE events
                print(f"\n🔍 Screening for HVE events...")
                batch_results = screener.screen_batch(batch_data, timeframe)

                if not batch_results.empty:
                    print(f"✅ Found {len(batch_results)} tickers with HVE data")
                    all_results.append(batch_results)
                else:
                    print(f"⚠️  No HVE events found in batch {batch_count}")

            except Exception as e:
                logger.error(f"Error processing batch {batch_count}: {e}")
                print(f"❌ Error processing batch {batch_count}: {e}")
                continue

        # Combine and save results
        if all_results:
            combined_results = pd.concat(all_results, ignore_index=True)
            combined_results = combined_results.sort_values('days_since_hve')

            # Save results
            results_file = output_base / f'hve_results_{timeframe}.csv'
            combined_results.to_csv(results_file, index=False)
            print(f"\n✅ Saved {len(combined_results)} results to {results_file}")

            # Print summary
            print(f"\n📊 {timeframe.upper()} RESULTS SUMMARY:")
            print(f"   Total tickers with HVE data: {len(combined_results)}")
            print(f"\n   Top 10 by recent HVE:")
            for i, row in combined_results.head(10).iterrows():
                print(f"   {i+1}. {row['ticker']}: {row['days_since_hve']} days ago "
                      f"({row['hve_date'].strftime('%Y-%m-%d')}, vol={row['hve_volume']:,.0f}, "
                      f"HVE_1Y={row['hve_occ_1y']}, Total={row['total_hve_count']})")

            return combined_results
        else:
            print(f"\n⚠️  No results for {timeframe} timeframe")
            return pd.DataFrame()

    except Exception as e:
        logger.error(f"Error processing {timeframe}: {e}")
        print(f"❌ Error processing {timeframe}: {e}")
        return pd.DataFrame()


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

        # Determine which timeframes to process
        timeframes = []
        if user_config.yf_daily_data:
            timeframes.append('daily')
        if user_config.yf_weekly_data:
            timeframes.append('weekly')
        if user_config.yf_monthly_data:
            timeframes.append('monthly')

        if not timeframes:
            print("\n⚠️  No timeframes enabled in user_data.csv")
            print("   Set YF_daily_data, YF_weekly_data, or YF_monthly_data to TRUE")
            return

        print(f"   ✓ Timeframes to process: {', '.join(timeframes)}")

        # Process each timeframe and collect results
        all_timeframe_results = {}
        for timeframe in timeframes:
            results = process_timeframe(config, user_config, timeframe, ticker_list)
            if not results.empty:
                all_timeframe_results[timeframe] = results

        # Generate ticker cards
        if all_timeframe_results:
            print("\n" + "="*60)
            print("GENERATING TICKER CARDS")
            print("="*60)

            card_generator = TickerCardGenerator(user_config.hve_output_dir)
            cards_generated = card_generator.generate_all_cards(all_timeframe_results)

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
            if user_config.hve_historical_export:
                print("\n" + "="*60)
                print("EXPORTING HISTORICAL HVE FORMAT")
                print("="*60)
                
                hve_exported = export_all_timeframes_historical(
                    all_timeframe_results,
                    output_dir,
                    max_events=user_config.hve_historical_max_events
                )
                
                print(f"\n✅ Exported {hve_exported} HVE (Highest Volume Ever) files")
                print(f"   Events per ticker: {user_config.hve_historical_max_events}")
                print(f"   Date range: {user_config.hve_start_date} to {user_config.hve_end_date}")
            else:
                print("\n⏭️  HVE historical export disabled (HVE_historical_export=FALSE)")
            
            # ----------------------------------------------------------
            # HVD Historical Export (top volume days by magnitude)
            # ----------------------------------------------------------
            if user_config.hvd_historical_export:
                print("\n" + "="*60)
                print("EXPORTING HISTORICAL HVD FORMAT")
                print("="*60)
                
                hvd_exported = export_all_timeframes_hvd(
                    all_timeframe_results,
                    output_dir,
                    max_days=user_config.hvd_historical_max_days
                )
                
                print(f"\n✅ Exported {hvd_exported} HVD (Highest Volume Days) files")
                print(f"   Top days per ticker: {user_config.hvd_historical_max_days}")
                print(f"   Date range: {user_config.hve_start_date} to {user_config.hve_end_date}")
            else:
                print("\n⏭️  HVD historical export disabled (HVD_historical_export=FALSE)")
        else:
            print("\n⚠️  No results to generate ticker cards")

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
