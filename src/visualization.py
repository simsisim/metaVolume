"""
Visualization Module for HVE Screener
======================================

Creates charts to visualize Highest Volume Ever events.
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import numpy as np
import logging
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class HVEVisualizer:
    """
    Creates visualizations for Highest Volume Ever analysis.
    """

    def __init__(self, chart_width: int = 14, chart_height: int = 7):
        """
        Initialize visualizer with chart dimensions.

        Args:
            chart_width: Width of charts in inches
            chart_height: Height of charts in inches
        """
        self.chart_width = chart_width
        self.chart_height = chart_height

        # Set style
        plt.style.use('seaborn-v0_8-darkgrid')

    def create_hve_chart(self, ticker: str, df: pd.DataFrame,
                        hve_dates: List[pd.Timestamp],
                        output_path: Path,
                        timeframe: str = 'daily') -> bool:
        """
        Create a chart showing price and volume with HVE events highlighted.

        Args:
            ticker: Ticker symbol
            df: DataFrame with OHLCV data
            hve_dates: List of dates when HVE occurred
            output_path: Path to save the chart
            timeframe: Timeframe being analyzed

        Returns:
            True if chart created successfully, False otherwise
        """
        try:
            # Create figure with 2 subplots (price and volume)
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(self.chart_width, self.chart_height),
                                          gridspec_kw={'height_ratios': [2, 1]})

            # Plot price
            ax1.plot(df.index, df['Close'], label='Close Price', color='blue', linewidth=1.5)
            ax1.set_ylabel('Price ($)', fontsize=12, fontweight='bold')
            ax1.set_title(f'{ticker} - Highest Volume Ever Analysis ({timeframe.capitalize()})',
                         fontsize=14, fontweight='bold')
            ax1.grid(True, alpha=0.3)
            ax1.legend(loc='upper left')

            # Plot volume bars
            colors = ['red' if date in hve_dates else 'gray' for date in df.index]
            ax2.bar(df.index, df['Volume'], color=colors, alpha=0.6, width=0.8)
            ax2.set_ylabel('Volume', fontsize=12, fontweight='bold')
            ax2.set_xlabel('Date', fontsize=12, fontweight='bold')
            ax2.grid(True, alpha=0.3, axis='y')

            # Mark HVE events on both subplots
            for hve_date in hve_dates:
                if hve_date in df.index:
                    hve_price = df.loc[hve_date, 'Close']
                    hve_volume = df.loc[hve_date, 'Volume']

                    # Mark on price chart
                    ax1.axvline(x=hve_date, color='red', linestyle='--', alpha=0.5, linewidth=1)
                    ax1.scatter([hve_date], [hve_price], color='red', s=100,
                               zorder=5, marker='v', label='HVE' if hve_date == hve_dates[0] else '')

                    # Annotate latest HVE
                    if hve_date == hve_dates[-1]:
                        ax1.annotate('Latest HVE', xy=(hve_date, hve_price),
                                   xytext=(10, 10), textcoords='offset points',
                                   bbox=dict(boxstyle='round,pad=0.5', fc='yellow', alpha=0.7),
                                   arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))

                    # Mark on volume chart
                    ax2.axvline(x=hve_date, color='red', linestyle='--', alpha=0.5, linewidth=1)

            # Format x-axis dates
            ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            ax2.xaxis.set_major_locator(mdates.AutoDateLocator())
            plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha='right')

            # Add legend for HVE markers on price chart
            if hve_dates:
                handles, labels = ax1.get_legend_handles_labels()
                if 'HVE' in labels:
                    ax1.legend(loc='upper left')

            # Add text box with HVE statistics
            hve_count = len(hve_dates)
            latest_hve = hve_dates[-1] if hve_dates else None
            days_since = (df.index[-1] - latest_hve).days if latest_hve else None

            stats_text = f'HVE Events: {hve_count}\n'
            if latest_hve:
                stats_text += f'Latest: {latest_hve.strftime("%Y-%m-%d")}\n'
                stats_text += f'Days Since: {days_since}'

            ax1.text(0.02, 0.98, stats_text, transform=ax1.transAxes,
                    fontsize=10, verticalalignment='top',
                    bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

            # Tight layout and save
            plt.tight_layout()
            output_path.parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(output_path, dpi=100, bbox_inches='tight')
            plt.close(fig)

            logger.info(f"Created chart for {ticker}: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Error creating chart for {ticker}: {e}")
            plt.close('all')
            return False

    def create_summary_chart(self, results: List[Dict],
                           output_path: Path,
                           timeframe: str = 'daily',
                           top_n: int = 20) -> bool:
        """
        Create a summary chart showing top tickers by HVE recency.

        Args:
            results: List of HVE screening results
            output_path: Path to save the chart
            timeframe: Timeframe being analyzed
            top_n: Number of top tickers to show

        Returns:
            True if chart created successfully, False otherwise
        """
        try:
            if not results:
                logger.warning("No results to visualize")
                return False

            # Take top N results
            top_results = results[:top_n]

            # Prepare data
            tickers = [r['ticker'] for r in top_results]
            days_since_hve = [r['days_since_latest_hve'] for r in top_results]
            hve_counts = [r['hve_count'] for r in top_results]

            # Create figure
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(self.chart_width, self.chart_height))

            # Chart 1: Days since latest HVE (horizontal bar)
            colors1 = plt.cm.RdYlGn_r(np.array(days_since_hve) / max(days_since_hve))
            ax1.barh(range(len(tickers)), days_since_hve, color=colors1)
            ax1.set_yticks(range(len(tickers)))
            ax1.set_yticklabels(tickers, fontsize=9)
            ax1.set_xlabel('Days Since Latest HVE', fontsize=12, fontweight='bold')
            ax1.set_title(f'Most Recent HVE Events\n({timeframe.capitalize()})',
                         fontsize=12, fontweight='bold')
            ax1.invert_yaxis()
            ax1.grid(True, alpha=0.3, axis='x')

            # Add value labels
            for i, v in enumerate(days_since_hve):
                ax1.text(v + max(days_since_hve) * 0.02, i, str(v),
                        va='center', fontsize=8)

            # Chart 2: HVE event counts (horizontal bar)
            colors2 = plt.cm.Blues(np.array(hve_counts) / max(hve_counts) * 0.7 + 0.3)
            ax2.barh(range(len(tickers)), hve_counts, color=colors2)
            ax2.set_yticks(range(len(tickers)))
            ax2.set_yticklabels(tickers, fontsize=9)
            ax2.set_xlabel('Number of HVE Events', fontsize=12, fontweight='bold')
            ax2.set_title(f'HVE Frequency\n({timeframe.capitalize()})',
                         fontsize=12, fontweight='bold')
            ax2.invert_yaxis()
            ax2.grid(True, alpha=0.3, axis='x')

            # Add value labels
            for i, v in enumerate(hve_counts):
                ax2.text(v + max(hve_counts) * 0.02, i, str(v),
                        va='center', fontsize=8)

            # Overall title
            fig.suptitle(f'Highest Volume Ever (HVE) Analysis - Top {len(top_results)} Tickers',
                        fontsize=14, fontweight='bold')

            # Tight layout and save
            plt.tight_layout()
            output_path.parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(output_path, dpi=100, bbox_inches='tight')
            plt.close(fig)

            logger.info(f"Created summary chart: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Error creating summary chart: {e}")
            plt.close('all')
            return False

    def create_charts_for_results(self, results: List[Dict],
                                 batch_data: Dict[str, pd.DataFrame],
                                 output_dir: Path,
                                 timeframe: str = 'daily',
                                 max_charts: int = 50) -> int:
        """
        Create individual HVE charts for screening results.

        Args:
            results: List of HVE screening results
            batch_data: Dictionary mapping ticker -> DataFrame
            output_dir: Directory to save charts
            timeframe: Timeframe being analyzed
            max_charts: Maximum number of individual charts to create

        Returns:
            Number of charts created successfully
        """
        charts_created = 0

        # Create charts directory
        charts_dir = output_dir / f'charts_{timeframe}'
        charts_dir.mkdir(parents=True, exist_ok=True)

        # Create charts for top results
        for i, result in enumerate(results[:max_charts]):
            ticker = result['ticker']
            hve_dates = result['hve_details']
            hve_dates_list = [detail['date'] for detail in hve_dates]

            if ticker in batch_data:
                output_path = charts_dir / f'{ticker}_{timeframe}.png'

                if self.create_hve_chart(ticker, batch_data[ticker],
                                        hve_dates_list, output_path, timeframe):
                    charts_created += 1

        logger.info(f"Created {charts_created} individual charts for {timeframe}")

        return charts_created
