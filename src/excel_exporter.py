"""
Excel Export Module for HVE Screener
=====================================

Exports HVE screening results to Excel with formatting and charts.
"""

import pandas as pd
import logging
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class HVEExcelExporter:
    """
    Exports HVE screening results to formatted Excel files.
    """

    def __init__(self):
        """Initialize Excel exporter."""
        pass

    def export_results(self, results: List[Dict],
                      output_path: Path,
                      timeframe: str,
                      include_details: bool = True) -> bool:
        """
        Export HVE screening results to Excel file.

        Args:
            results: List of HVE screening results
            output_path: Path to save Excel file
            timeframe: Timeframe being analyzed
            include_details: Include detailed HVE events in separate sheet

        Returns:
            True if export successful, False otherwise
        """
        try:
            if not results:
                logger.warning("No results to export")
                return False

            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Create Excel writer
            with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
                # Create main results DataFrame
                main_df = self._create_main_dataframe(results)

                # Write main results
                main_df.to_excel(writer, sheet_name='HVE_Summary', index=False)

                # Get workbook and worksheet objects
                workbook = writer.book
                worksheet = writer.sheets['HVE_Summary']

                # Format worksheet
                self._format_summary_sheet(worksheet, workbook, len(main_df))

                # Create detailed events sheet if requested
                if include_details:
                    details_df = self._create_details_dataframe(results)
                    details_df.to_excel(writer, sheet_name='HVE_Details', index=False)

                    details_worksheet = writer.sheets['HVE_Details']
                    self._format_details_sheet(details_worksheet, workbook, len(details_df))

                # Create statistics sheet
                stats_df = self._create_statistics_dataframe(results, timeframe)
                stats_df.to_excel(writer, sheet_name='Statistics', index=False)

                stats_worksheet = writer.sheets['Statistics']
                self._format_stats_sheet(stats_worksheet, workbook, len(stats_df))

            logger.info(f"Exported {len(results)} results to {output_path}")
            return True

        except Exception as e:
            logger.error(f"Error exporting to Excel: {e}")
            return False

    def _create_main_dataframe(self, results: List[Dict]) -> pd.DataFrame:
        """Create main summary DataFrame from results."""
        data = []

        for result in results:
            row = {
                'Ticker': result['ticker'],
                'Timeframe': result['timeframe'],
                'Score': result.get('score', 0),
                'HVE Count': result['hve_count'],
                'Latest HVE Date': result['latest_hve_date'],
                'Days Since HVE': result['days_since_latest_hve'],
                'Max Volume': result['max_volume_ever'],
                'Current Volume': result['current_volume'],
                'Volume % of Max': result['volume_ratio_to_max'],
                'Current Price': result['current_price'],
                'Data Start': result['data_start_date'],
                'Data End': result['data_end_date'],
                'Data Points': result['data_points']
            }
            data.append(row)

        df = pd.DataFrame(data)
        return df

    def _create_details_dataframe(self, results: List[Dict]) -> pd.DataFrame:
        """Create detailed events DataFrame from results."""
        data = []

        for result in results:
            ticker = result['ticker']
            timeframe = result['timeframe']

            for detail in result['hve_details']:
                row = {
                    'Ticker': ticker,
                    'Timeframe': timeframe,
                    'HVE Date': detail['date'],
                    'Volume': detail['volume'],
                    'Close Price': detail['close'],
                    'Open Price': detail.get('open'),
                    'High Price': detail.get('high'),
                    'Low Price': detail.get('low'),
                    'Price Change %': detail.get('price_change_pct')
                }
                data.append(row)

        df = pd.DataFrame(data)
        return df

    def _create_statistics_dataframe(self, results: List[Dict],
                                    timeframe: str) -> pd.DataFrame:
        """Create statistics DataFrame."""
        if not results:
            return pd.DataFrame()

        # Calculate statistics
        hve_counts = [r['hve_count'] for r in results]
        days_since = [r['days_since_latest_hve'] for r in results]
        scores = [r.get('score', 0) for r in results]
        volume_ratios = [r['volume_ratio_to_max'] for r in results]

        stats = {
            'Metric': [
                'Total Tickers Analyzed',
                'Tickers with HVE',
                'Timeframe',
                'Analysis Date',
                '',
                'Average HVE Count',
                'Max HVE Count',
                'Min HVE Count',
                '',
                'Average Days Since HVE',
                'Min Days Since HVE',
                'Max Days Since HVE',
                '',
                'Average Score',
                'Max Score',
                '',
                'Average Volume % of Max',
                'HVE in Last 30 Days',
                'HVE in Last 90 Days',
                'HVE in Last 365 Days'
            ],
            'Value': [
                len(results),
                len(results),
                timeframe,
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                '',
                round(sum(hve_counts) / len(hve_counts), 2),
                max(hve_counts),
                min(hve_counts),
                '',
                round(sum(days_since) / len(days_since), 2),
                min(days_since),
                max(days_since),
                '',
                round(sum(scores) / len(scores), 2),
                max(scores),
                '',
                round(sum(volume_ratios) / len(volume_ratios), 2),
                len([d for d in days_since if d <= 30]),
                len([d for d in days_since if d <= 90]),
                len([d for d in days_since if d <= 365])
            ]
        }

        df = pd.DataFrame(stats)
        return df

    def _format_summary_sheet(self, worksheet, workbook, num_rows: int):
        """Apply formatting to summary sheet."""
        # Define formats
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#4472C4',
            'font_color': 'white',
            'border': 1,
            'align': 'center',
            'valign': 'vcenter'
        })

        number_format = workbook.add_format({'num_format': '#,##0'})
        decimal_format = workbook.add_format({'num_format': '#,##0.00'})
        percent_format = workbook.add_format({'num_format': '0.00'})
        date_format = workbook.add_format({'num_format': 'yyyy-mm-dd'})

        # Set column widths
        worksheet.set_column('A:A', 10)  # Ticker
        worksheet.set_column('B:B', 12)  # Timeframe
        worksheet.set_column('C:C', 10)  # Score
        worksheet.set_column('D:D', 12)  # HVE Count
        worksheet.set_column('E:E', 15)  # Latest HVE Date
        worksheet.set_column('F:F', 15)  # Days Since HVE
        worksheet.set_column('G:H', 15)  # Volumes
        worksheet.set_column('I:I', 15)  # Volume %
        worksheet.set_column('J:J', 12)  # Current Price
        worksheet.set_column('K:L', 12)  # Dates
        worksheet.set_column('M:M', 12)  # Data Points

        # Apply formats to data columns
        worksheet.set_column('C:C', 10, decimal_format)  # Score
        worksheet.set_column('D:D', 12, number_format)  # HVE Count
        worksheet.set_column('E:E', 15, date_format)  # Latest HVE Date
        worksheet.set_column('F:F', 15, number_format)  # Days Since
        worksheet.set_column('G:H', 15, number_format)  # Volumes
        worksheet.set_column('I:I', 15, percent_format)  # Volume %
        worksheet.set_column('J:J', 12, decimal_format)  # Price
        worksheet.set_column('K:L', 12, date_format)  # Dates
        worksheet.set_column('M:M', 12, number_format)  # Data Points

        # Freeze first row
        worksheet.freeze_panes(1, 0)

    def _format_details_sheet(self, worksheet, workbook, num_rows: int):
        """Apply formatting to details sheet."""
        number_format = workbook.add_format({'num_format': '#,##0'})
        decimal_format = workbook.add_format({'num_format': '#,##0.00'})
        percent_format = workbook.add_format({'num_format': '0.00'})
        date_format = workbook.add_format({'num_format': 'yyyy-mm-dd'})

        # Set column widths and formats
        worksheet.set_column('A:A', 10)  # Ticker
        worksheet.set_column('B:B', 12)  # Timeframe
        worksheet.set_column('C:C', 15, date_format)  # HVE Date
        worksheet.set_column('D:D', 15, number_format)  # Volume
        worksheet.set_column('E:H', 12, decimal_format)  # Prices
        worksheet.set_column('I:I', 12, percent_format)  # Price Change %

        # Freeze first row
        worksheet.freeze_panes(1, 0)

    def _format_stats_sheet(self, worksheet, workbook, num_rows: int):
        """Apply formatting to statistics sheet."""
        # Set column widths
        worksheet.set_column('A:A', 30)  # Metric
        worksheet.set_column('B:B', 20)  # Value

        # Freeze first row
        worksheet.freeze_panes(1, 0)

    def export_combined_results(self, all_results: Dict[str, List[Dict]],
                               output_path: Path) -> bool:
        """
        Export combined results from all timeframes to single Excel file.

        Args:
            all_results: Dictionary mapping timeframe -> results list
            output_path: Path to save Excel file

        Returns:
            True if export successful, False otherwise
        """
        try:
            if not all_results:
                logger.warning("No results to export")
                return False

            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Create Excel writer
            with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
                workbook = writer.book

                # Create a sheet for each timeframe
                for timeframe, results in all_results.items():
                    if results:
                        # Create DataFrame
                        df = self._create_main_dataframe(results)

                        # Write to sheet
                        sheet_name = f'HVE_{timeframe.capitalize()}'
                        df.to_excel(writer, sheet_name=sheet_name, index=False)

                        # Format sheet
                        worksheet = writer.sheets[sheet_name]
                        self._format_summary_sheet(worksheet, workbook, len(df))

                # Create combined summary sheet
                combined_df = pd.concat([
                    self._create_main_dataframe(results)
                    for results in all_results.values()
                    if results
                ], ignore_index=True)

                # Sort by score
                combined_df = combined_df.sort_values('Score', ascending=False)

                combined_df.to_excel(writer, sheet_name='All_Combined', index=False)
                worksheet = writer.sheets['All_Combined']
                self._format_summary_sheet(worksheet, workbook, len(combined_df))

            logger.info(f"Exported combined results to {output_path}")
            return True

        except Exception as e:
            logger.error(f"Error exporting combined results: {e}")
            return False
