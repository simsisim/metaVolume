"""
Ticker Card Generator
=====================

Generates individual ticker cards showing all HVE and HV1Y events
across all timeframes (daily, weekly, monthly).
"""

import pandas as pd
from pathlib import Path
from typing import Dict, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class TickerCardGenerator:
    """
    Generator for creating individual ticker cards with HVE/HV1Y event details.
    """

    def __init__(self, output_dir: str):
        """
        Initialize the ticker card generator.

        Args:
            output_dir: Base output directory for ticker cards
        """
        self.output_dir = Path(output_dir)
        self.ticker_cards_dir = self.output_dir / 'ticker_cards'
        self.ticker_cards_dir.mkdir(parents=True, exist_ok=True)

    def collect_ticker_data(self, all_results: Dict[str, pd.DataFrame]) -> Dict[str, Dict]:
        """
        Collect and organize data for all tickers across timeframes.

        Args:
            all_results: Dictionary mapping timeframe -> results DataFrame

        Returns:
            Dictionary mapping ticker -> {timeframe -> data}
        """
        ticker_data = {}

        for timeframe, results_df in all_results.items():
            if results_df is None or results_df.empty:
                continue

            for _, row in results_df.iterrows():
                ticker = row['ticker']

                if ticker not in ticker_data:
                    ticker_data[ticker] = {}

                ticker_data[ticker][timeframe] = row.to_dict()

        logger.info(f"Collected data for {len(ticker_data)} tickers across all timeframes")
        return ticker_data

    def format_volume(self, volume) -> str:
        """Format volume with commas."""
        if pd.isna(volume):
            return "N/A"
        return f"{int(volume):,}"

    def format_date(self, date) -> str:
        """Format date as YYYY-MM-DD."""
        if pd.isna(date):
            return "N/A"
        if isinstance(date, str):
            return date
        return date.strftime('%Y-%m-%d')

    def calculate_days_ago(self, event_date, latest_date) -> str:
        """Calculate and format days ago from an event."""
        if pd.isna(event_date) or pd.isna(latest_date):
            return ""

        if isinstance(event_date, str):
            event_date = pd.Timestamp(event_date)
        if isinstance(latest_date, str):
            latest_date = pd.Timestamp(latest_date)

        days = (latest_date - event_date).days
        return f"({days} days ago)"

    def generate_card_text(self, ticker: str, timeframe_data: Dict) -> str:
        """
        Generate text content for a ticker card.

        Args:
            ticker: Ticker symbol
            timeframe_data: Dictionary mapping timeframe -> data

        Returns:
            Formatted text content for the card
        """
        lines = []
        lines.append("=" * 80)
        lines.append(f"TICKER CARD: {ticker}")
        lines.append("=" * 80)
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")

        # Process each timeframe in order: daily, weekly, monthly
        for timeframe in ['daily', 'weekly', 'monthly']:
            if timeframe not in timeframe_data:
                continue

            data = timeframe_data[timeframe]
            lines.append("")
            lines.append(f"{timeframe.upper()} TIMEFRAME")
            lines.append("=" * len(f"{timeframe.upper()} TIMEFRAME"))

            # HVE Events section
            lines.append("")
            lines.append("HVE Events (Highest Volume Ever):")
            lines.append("-" * 40)

            all_hve_details = data.get('all_hve_details', [])
            if all_hve_details:
                latest_date = data.get('latest_date')
                for idx, event in enumerate(all_hve_details, 1):
                    date_str = self.format_date(event['date'])
                    volume_str = self.format_volume(event['volume'])
                    days_ago = self.calculate_days_ago(event['date'], latest_date)
                    lines.append(f"  {idx}. {date_str}  Volume: {volume_str}  {days_ago}")
            else:
                lines.append("  No HVE events found")

            # HV1Y Events section (if enabled)
            if 'all_hv1y_details' in data:
                lines.append("")
                lines.append("HV1Y Events (Highest Volume in 1 Year):")
                lines.append("-" * 40)

                all_hv1y_details = data.get('all_hv1y_details', [])
                if all_hv1y_details:
                    latest_date = data.get('latest_date')
                    hve_date = data.get('hve_date')

                    for idx, event in enumerate(all_hv1y_details, 1):
                        date_str = self.format_date(event['date'])
                        volume_str = self.format_volume(event['volume'])
                        days_ago = self.calculate_days_ago(event['date'], latest_date)

                        # Check if this HV1Y event is also an HVE
                        is_hve = (event['date'] == hve_date)
                        hve_flag = "  [Also HVE]" if is_hve else ""

                        lines.append(f"  {idx}. {date_str}  Volume: {volume_str}  {days_ago}{hve_flag}")
                else:
                    lines.append("  No HV1Y events found")

        # Summary section
        lines.append("")
        lines.append("Summary:")
        lines.append("-" * 40)

        total_hve_events = sum(len(data.get('all_hve_details', []))
                               for data in timeframe_data.values())
        lines.append(f"Total HVE events across all timeframes: {total_hve_events}")

        if any('all_hv1y_details' in data for data in timeframe_data.values()):
            total_hv1y_events = sum(len(data.get('all_hv1y_details', []))
                                    for data in timeframe_data.values())
            lines.append(f"Total HV1Y events across all timeframes: {total_hv1y_events}")

        # Find most recent activity
        most_recent = None
        most_recent_timeframe = None
        for timeframe, data in timeframe_data.items():
            days = data.get('days_since_hve')
            if days is not None:
                if most_recent is None or days < most_recent:
                    most_recent = days
                    most_recent_timeframe = timeframe

        if most_recent is not None:
            lines.append(f"Latest volume activity: {most_recent_timeframe.capitalize()} ({most_recent} days ago)")

        lines.append("")
        lines.append("=" * 80)

        return "\n".join(lines)

    def generate_card(self, ticker: str, timeframe_data: Dict) -> Path:
        """
        Generate a ticker card file.

        Args:
            ticker: Ticker symbol
            timeframe_data: Dictionary mapping timeframe -> data

        Returns:
            Path to the generated card file
        """
        try:
            card_text = self.generate_card_text(ticker, timeframe_data)
            card_file = self.ticker_cards_dir / f"{ticker}.txt"

            with open(card_file, 'w') as f:
                f.write(card_text)

            logger.info(f"Generated card for {ticker}: {card_file}")
            return card_file

        except Exception as e:
            logger.error(f"Error generating card for {ticker}: {e}")
            return None

    def generate_all_cards(self, all_results: Dict[str, pd.DataFrame]) -> int:
        """
        Generate ticker cards for all tickers in the results.

        Args:
            all_results: Dictionary mapping timeframe -> results DataFrame

        Returns:
            Number of cards generated
        """
        # Collect data for all tickers
        ticker_data = self.collect_ticker_data(all_results)

        # Generate a card for each ticker
        cards_generated = 0
        for ticker, timeframe_data in ticker_data.items():
            card_file = self.generate_card(ticker, timeframe_data)
            if card_file:
                cards_generated += 1

        logger.info(f"Generated {cards_generated} ticker cards in {self.ticker_cards_dir}")
        return cards_generated
