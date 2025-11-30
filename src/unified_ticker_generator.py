"""
Unified Ticker File Generator
============================

Simple, clean system that generates all required ticker files for any user choice format.
Replaces complex legacy preprocessing workflow and combine_tickers systems.

Core Requirements:
- Always generate universe files (choice 0) regardless of user choice
- Handle semicolon-separated choices (1;2) with dash filenames (1-2) 
- Generate 3 file types: combined_tickers_*.csv, combined_info_tickers_*.csv, combined_info_tickers_clean_*.csv
"""

import pandas as pd
from pathlib import Path
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class UnifiedTickerGenerator:
    """Generates all ticker files for any user choice format."""
    
    def __init__(self, config):
        """Initialize with config object containing directories."""
        self.config = config
        self.tickers_dir = Path(config.directories['TICKERS_DIR'])
        self.tickers_dir.mkdir(parents=True, exist_ok=True)
        
        # Choice mapping: choice -> list of boolean column filters
        self.choice_filters = {
            0: [],                          # Full universe (no filtering)
            1: ['SP500'],                   # S&P 500 only
            2: ['NASDAQ100'],               # NASDAQ 100 only  
            3: ['NASDAQComposite'],         # All NASDAQ
            4: ['Russell1000'],             # Russell 1000
            5: ['SP500', 'NASDAQ100'],      # S&P 500 + NASDAQ 100
            6: ['SP500', 'NASDAQComposite'], # S&P 500 + All NASDAQ
            7: ['SP500', 'Russell1000'],    # S&P 500 + Russell 1000
            8: ['NASDAQ100', 'NASDAQComposite'], # NASDAQ 100 + All NASDAQ
            9: ['NASDAQ100', 'Russell1000'], # NASDAQ 100 + Russell 1000
            10: ['NASDAQComposite', 'Russell1000'], # All NASDAQ + Russell 1000
            11: ['SP500', 'NASDAQ100', 'NASDAQComposite'], # Major indexes
            12: ['SP500', 'NASDAQ100', 'Russell1000'], # Major indexes
            13: ['SP500', 'NASDAQComposite', 'Russell1000'], # Major indexes
            14: ['NASDAQ100', 'NASDAQComposite', 'Russell1000'], # Tech heavy
            15: ['SP500', 'NASDAQ100', 'Russell1000', 'NASDAQComposite'], # All major
        }
    
    def clean_ticker_name(self, ticker: str) -> Optional[str]:
        """
        Clean ticker name according to rules:
        - Exclude tickers containing '/' (preferred shares, depositary shares)
        - Transform '.' to '-' (class shares like BRK.A -> BRK-A)
        
        Args:
            ticker: Raw ticker symbol from TradingView
            
        Returns:
            Cleaned ticker name or None if ticker should be excluded
        """
        if pd.isna(ticker) or not isinstance(ticker, str):
            return None
            
        ticker = ticker.strip()
        
        # Exclude tickers with '/' (preferred shares, depositary shares)
        if '/' in ticker:
            return None
            
        # Transform '.' to '-' for class shares
        cleaned_ticker = ticker.replace('.', '-')
        
        return cleaned_ticker
    
    def generate_all_ticker_files(self, user_choice):
        """
        Generate all ticker files for any user choice format.
        
        Args:
            user_choice (int, str): User choice (0, 1, "1;2", etc.)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            print(f"\n{'='*60}")
            print("UNIFIED TICKER FILE GENERATION")
            print(f"{'='*60}")
            print(f"User choice: {user_choice}")
            
            # Step 1: Ensure universe data exists
            if not self._ensure_universe_data():
                return False
            
            # Step 2: Always generate universe files (choice 0)
            print(f"\n📊 STEP 1: Generating universe files (choice 0)...")
            if not self._generate_files_for_choice(0):
                print(f"❌ Failed to generate universe files")
                return False
            
            # Step 3: Parse user choice and generate individual/combined files
            choices = self._parse_user_choice(user_choice)
            if not choices:
                print(f"✅ Only universe files needed for choice {user_choice}")
                return True
            
            print(f"\n📊 STEP 2: Generating files for user choices: {choices}")
            
            # Generate individual choice files
            for choice in choices:
                if choice != 0:  # Skip 0 since we already generated it
                    if not self._generate_files_for_choice(choice):
                        print(f"❌ Failed to generate files for choice {choice}")
                        return False
            
            # Generate combined multi-choice files if needed
            if len(choices) > 1 or (len(choices) == 1 and choices[0] != 0):
                combined_choice = str(user_choice)
                if combined_choice != str(choices[0]):  # Only if different from single choice
                    print(f"\n📊 STEP 3: Generating combined files for {combined_choice}...")
                    if not self._generate_combined_files(choices, combined_choice):
                        print(f"❌ Failed to generate combined files")
                        return False
            
            print(f"\n✅ All ticker files generated successfully!")
            self._print_summary(user_choice, choices)
            return True
            
        except Exception as e:
            print(f"❌ Error generating ticker files: {e}")
            logger.error(f"Error generating ticker files: {e}")
            return False
    
    def _ensure_universe_data(self):
        """Force regeneration of TradingView universe data with boolean columns."""
        universe_bool_file = self.tickers_dir / 'tradingview_universe_bool.csv'
        
        # Always regenerate - remove existing file if present
        if universe_bool_file.exists():
            universe_bool_file.unlink()
            print(f"🔄 Removed existing universe data for regeneration")
        
        # Create universe data from root tradingview_universe.csv
        root_universe = Path('tradingview_universe.csv')
        if not root_universe.exists():
            print(f"❌ Missing root TradingView universe file: {root_universe}")
            return False
        
        print(f"🔄 Creating boolean-enhanced universe data...")
        try:
            # Read root universe
            df = pd.read_csv(root_universe)
            print(f"📊 Loaded {len(df)} tickers from root universe")
            
            # Standardize to 'ticker' column name
            if 'Symbol' in df.columns:
                df = df.rename(columns={'Symbol': 'ticker'})
            
            # Clean ticker names (filter '/' and transform '.' to '-')
            print("🧹 Cleaning ticker names...")
            original_count = len(df)
            
            # Apply ticker cleaning
            df['cleaned_ticker'] = df['ticker'].apply(self.clean_ticker_name)
            # Remove rows where ticker should be excluded (None values)
            df = df.dropna(subset=['cleaned_ticker'])
            df['ticker'] = df['cleaned_ticker']
            df.drop('cleaned_ticker', axis=1, inplace=True)
            
            filtered_count = original_count - len(df)
            print(f"📊 Original tickers: {original_count}")
            print(f"🚫 Filtered out: {filtered_count} tickers with '/' characters")
            print(f"✅ Clean tickers: {len(df)}")
            
            # Standardize all column names to lowercase (convention)
            df.columns = df.columns.str.lower()
            
            # Handle special cases after lowercase conversion
            column_renames = {
                'market capitalization - currency': 'market_cap_currency',
                'market capitalization': 'market_cap'  # Standard name for market cap
            }
            
            for old_col, new_col in column_renames.items():
                if old_col in df.columns:
                    df = df.rename(columns={old_col: new_col})
            
            # Create boolean columns from index column (now lowercase)
            if 'index' in df.columns:
                df_bool = self._create_boolean_columns(df)
                df_bool.to_csv(universe_bool_file, index=False)
                print(f"✅ Created boolean-enhanced universe: {len(df_bool)} tickers, {len(df_bool.columns)} columns")
                return True
            else:
                print(f"⚠️  No index column found, using basic universe data")
                df.to_csv(universe_bool_file, index=False)
                return True
                
        except Exception as e:
            print(f"❌ Error creating universe data: {e}")
            return False
    
    def _create_boolean_columns(self, df):
        """Create boolean columns from Index data."""
        # Copy original dataframe
        df_enhanced = df.copy()
        
        # Parse indexes and create boolean columns
        index_counts = {}
        
        for idx, row in df.iterrows():
            if pd.notna(row.get('index')):
                # Split by comma (not semicolon) since the data uses comma-separated values
                indexes = str(row['index']).split(',')
                for index_name in indexes:
                    index_name = index_name.strip()
                    if index_name:
                        # Clean index name for column - more comprehensive cleaning
                        col_name = (index_name
                                   .replace(' ', '')
                                   .replace('&', '')
                                   .replace('-', '')
                                   .replace('.', '')
                                   .replace('/', '')
                                   .replace('(', '')
                                   .replace(')', ''))
                        
                        # Initialize column if not exists
                        if col_name not in df_enhanced.columns:
                            df_enhanced[col_name] = False
                            index_counts[col_name] = 0
                        
                        # Set boolean value
                        df_enhanced.at[idx, col_name] = True
                        index_counts[col_name] += 1
        
        print(f"🏗️  Created {len(index_counts)} boolean index columns")
        if index_counts:
            top_indexes = sorted(index_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            print(f"🎯 Top indexes: {', '.join([f'{name}({count})' for name, count in top_indexes])}")

        # Add boolean columns for exchange categories
        exchange_counts = {}
        if 'exchange' in df_enhanced.columns:
            exchanges = df_enhanced['exchange'].dropna().unique()
            for exchange in exchanges:
                if pd.notna(exchange) and exchange != '':
                    col_name = f'exchange_{exchange}'
                    df_enhanced[col_name] = (df_enhanced['exchange'] == exchange)
                    exchange_counts[col_name] = df_enhanced[col_name].sum()

            print(f"🏗️  Created {len(exchange_counts)} boolean exchange columns")
            if exchange_counts:
                print(f"🎯 Exchanges: {', '.join([f'{name}({count})' for name, count in exchange_counts.items()])}")

        # Add boolean columns for analyst rating categories
        rating_counts = {}
        if 'analyst rating' in df_enhanced.columns:
            ratings = df_enhanced['analyst rating'].dropna().unique()
            for rating in ratings:
                if pd.notna(rating) and rating != '':
                    # Clean rating name for column (handle spaces and special chars)
                    clean_rating = rating.replace(' ', '_').replace('-', '_')
                    col_name = f'rating_{clean_rating}'
                    df_enhanced[col_name] = (df_enhanced['analyst rating'] == rating)
                    rating_counts[col_name] = df_enhanced[col_name].sum()

            print(f"🏗️  Created {len(rating_counts)} boolean rating columns")
            if rating_counts:
                print(f"🎯 Ratings: {', '.join([f'{name}({count})' for name, count in rating_counts.items()])}")

        return df_enhanced
    
    def _parse_user_choice(self, user_choice):
        """Parse user choice into list of individual choices."""
        if user_choice == 0 or user_choice == '0':
            return [0]
        
        # Handle string with dashes
        if isinstance(user_choice, str) and '-' in user_choice:
            try:
                choices = [int(c.strip()) for c in user_choice.split('-') if c.strip().isdigit()]
                return choices
            except ValueError:
                print(f"❌ Invalid choice format: {user_choice}")
                return []
        
        # Handle single choice
        try:
            choice = int(user_choice)
            return [choice] if choice != 0 else [0]
        except ValueError:
            print(f"❌ Invalid choice format: {user_choice}")
            return []
    
    def _generate_files_for_choice(self, choice):
        """Force regenerate all 3 file types for a specific choice."""
        try:
            # Check if this is a special choice that requires individual ticker files
            if choice in [5, 6, 7, 8]:
                return self._generate_files_individual_mode(choice)
            
            # Standard TradingView filtering mode
            # Load universe data
            universe_file = self.tickers_dir / 'tradingview_universe_bool.csv'
            if not universe_file.exists():
                print(f"❌ Universe boolean file not found: {universe_file}")
                return False
            
            df = pd.read_csv(universe_file)
            
            # Apply filtering
            filtered_df = self._filter_by_choice(df, choice)
            if filtered_df is None:
                return False
            
            # Generate 3 file types - force regeneration by removing existing files
            choice_str = str(choice)
            
            # Remove existing files if they exist
            files_to_regenerate = [
                self.tickers_dir / f'combined_tickers_{choice_str}.csv',
                self.tickers_dir / f'combined_info_tickers_{choice_str}.csv',
                self.tickers_dir / f'combined_info_tickers_clean_{choice_str}.csv'
            ]
            
            for file_path in files_to_regenerate:
                if file_path.exists():
                    file_path.unlink()
            
            # 1. combined_tickers_{choice}.csv (ticker column only)
            tickers_only = pd.DataFrame({'ticker': filtered_df['ticker'].tolist()})
            ticker_file = self.tickers_dir / f'combined_tickers_{choice_str}.csv'
            tickers_only.to_csv(ticker_file, index=False)
            
            # 2. combined_info_tickers_{choice}.csv (all columns)
            info_file = self.tickers_dir / f'combined_info_tickers_{choice_str}.csv'
            filtered_df.to_csv(info_file, index=False)
            
            # 3. combined_info_tickers_clean_{choice}.csv (same as info)
            clean_file = self.tickers_dir / f'combined_info_tickers_clean_{choice_str}.csv'
            filtered_df.to_csv(clean_file, index=False)
            
            print(f"✅ Force-generated files for choice {choice}: {len(filtered_df)} tickers")
            return True
            
        except Exception as e:
            print(f"❌ Error generating files for choice {choice}: {e}")
            return False
    
    def _generate_combined_files(self, choices, combined_choice_str):
        """Force regenerate combined files for multi-choice selections."""
        try:
            # Combine tickers from all individual choice files
            all_tickers = []
            all_info_data = []
            
            print(f"  • Combining tickers from individual choice files...")
            
            for choice in choices:
                # Load tickers from each individual choice file
                choice_file = self.tickers_dir / f'combined_tickers_{choice}.csv'
                info_file = self.tickers_dir / f'combined_info_tickers_{choice}.csv'
                
                if choice_file.exists():
                    choice_df = pd.read_csv(choice_file)
                    choice_tickers = choice_df['ticker'].tolist()
                    all_tickers.extend(choice_tickers)
                    print(f"    - Choice {choice}: {len(choice_tickers)} tickers")
                    
                    # Also load info data if available
                    if info_file.exists():
                        info_df = pd.read_csv(info_file)
                        all_info_data.append(info_df)
                else:
                    print(f"    ⚠️  Choice file not found: {choice_file}")
            
            if not all_tickers:
                print(f"❌ No tickers found from any choice files")
                return False
            
            # Remove duplicates while preserving order
            unique_tickers = list(dict.fromkeys(all_tickers))
            print(f"  • Combined {len(all_tickers)} total tickers -> {len(unique_tickers)} unique tickers")
            
            # Combine info data
            if all_info_data:
                # Concatenate all info dataframes and remove duplicates based on ticker
                combined_info_df = pd.concat(all_info_data, ignore_index=True)
                combined_info_df = combined_info_df.drop_duplicates(subset=['ticker'], keep='first')
                
                # Ensure all unique tickers are represented
                missing_tickers = set(unique_tickers) - set(combined_info_df['ticker'])
                if missing_tickers:
                    print(f"  • Adding {len(missing_tickers)} missing tickers with minimal data")
                    for ticker in missing_tickers:
                        minimal_row = {'ticker': ticker}
                        # Fill other columns with default values
                        for col in combined_info_df.columns:
                            if col != 'ticker':
                                minimal_row[col] = False if col.isupper() else ''
                        combined_info_df = pd.concat([combined_info_df, pd.DataFrame([minimal_row])], ignore_index=True)
                
                # Sort by the order of unique_tickers
                ticker_order = {ticker: i for i, ticker in enumerate(unique_tickers)}
                combined_info_df['_sort_order'] = combined_info_df['ticker'].map(ticker_order)
                combined_info_df = combined_info_df.sort_values('_sort_order').drop('_sort_order', axis=1)
                
            else:
                # Create minimal info dataframe
                combined_info_df = pd.DataFrame({'ticker': unique_tickers})
            
            # Force regeneration by removing existing files
            files_to_regenerate = [
                self.tickers_dir / f'combined_tickers_{combined_choice_str}.csv',
                self.tickers_dir / f'combined_info_tickers_{combined_choice_str}.csv',
                self.tickers_dir / f'combined_info_tickers_clean_{combined_choice_str}.csv'
            ]
            
            for file_path in files_to_regenerate:
                if file_path.exists():
                    file_path.unlink()
            
            # Generate 3 file types with combined choice name
            # 1. combined_tickers_{choice}.csv (ticker column only)
            tickers_only = pd.DataFrame({'ticker': unique_tickers})
            ticker_file = self.tickers_dir / f'combined_tickers_{combined_choice_str}.csv'
            tickers_only.to_csv(ticker_file, index=False)
            
            # 2. combined_info_tickers_{choice}.csv (all columns)
            info_file = self.tickers_dir / f'combined_info_tickers_{combined_choice_str}.csv'
            combined_info_df.to_csv(info_file, index=False)
            
            # 3. combined_info_tickers_clean_{choice}.csv (same as info)
            clean_file = self.tickers_dir / f'combined_info_tickers_clean_{combined_choice_str}.csv'
            combined_info_df.to_csv(clean_file, index=False)
            
            print(f"✅ Force-generated combined files for {combined_choice_str}: {len(unique_tickers)} tickers")
            return True
            
        except Exception as e:
            print(f"❌ Error generating combined files: {e}")
            return False
    
    def _generate_files_individual_mode(self, choice):
        """Generate files using individual ticker files for special choices 5,6,7,8."""
        try:
            from .config import get_ticker_files, find_ticker_file
            
            print(f"  🎯 Using individual file mode for choice {choice}")
            
            # Get ticker filename for this choice
            ticker_files = get_ticker_files(self.config)
            filename = ticker_files.get(choice)
            
            if not filename:
                print(f"❌ No ticker filename configured for choice {choice}")
                return False
            
            # Find the ticker file (with root directory fallback)
            ticker_file_path = find_ticker_file(filename, self.config)
            
            if not ticker_file_path or not ticker_file_path.exists():
                print(f"❌ Ticker file not found: {filename}")
                return False
            
            print(f"  📂 Loading individual file: {ticker_file_path}")
            
            # Load ticker file
            df_tickers = pd.read_csv(ticker_file_path)
            
            # Ensure 'ticker' column exists
            if 'ticker' not in df_tickers.columns:
                # Try common column names
                for col in ['Symbol', 'symbol', 'Ticker', 'TICKER']:
                    if col in df_tickers.columns:
                        df_tickers = df_tickers.rename(columns={col: 'ticker'})
                        break
                else:
                    print(f"❌ No ticker column found in {filename}")
                    return False
            
            # Get unique tickers
            tickers = df_tickers['ticker'].dropna().unique().tolist()
            print(f"  📊 Loaded {len(tickers)} tickers from individual file")
            
            # Load universe data for enrichment
            universe_file = self.tickers_dir / 'tradingview_universe_bool.csv'
            if universe_file.exists():
                universe_df = pd.read_csv(universe_file)
                
                # Create enriched dataframe by matching tickers
                enriched_data = []
                matched_count = 0
                
                for ticker in tickers:
                    # Find matching row in universe
                    universe_match = universe_df[universe_df['ticker'] == ticker]
                    
                    if not universe_match.empty:
                        enriched_data.append(universe_match.iloc[0])
                        matched_count += 1
                    else:
                        # Create minimal row for ticker not in universe
                        minimal_row = pd.Series({'ticker': ticker})
                        # Fill missing columns with default values
                        for col in universe_df.columns:
                            if col not in minimal_row.index:
                                minimal_row[col] = False if col.isupper() else ''
                        enriched_data.append(minimal_row)
                
                if enriched_data:
                    filtered_df = pd.DataFrame(enriched_data).reset_index(drop=True)
                    print(f"  ✅ Enriched {matched_count}/{len(tickers)} tickers with universe data")
                else:
                    # Fallback to basic ticker dataframe
                    filtered_df = df_tickers[['ticker']].drop_duplicates()
                    
            else:
                print(f"  ⚠️  Universe file not found, using basic ticker data")
                filtered_df = df_tickers[['ticker']].drop_duplicates()
            
            # Force regeneration by removing existing files
            choice_str = str(choice)
            files_to_regenerate = [
                self.tickers_dir / f'combined_tickers_{choice_str}.csv',
                self.tickers_dir / f'combined_info_tickers_{choice_str}.csv',
                self.tickers_dir / f'combined_info_tickers_clean_{choice_str}.csv'
            ]
            
            for file_path in files_to_regenerate:
                if file_path.exists():
                    file_path.unlink()
            
            # Generate 3 file types
            # 1. combined_tickers_{choice}.csv (ticker column only)
            tickers_only = pd.DataFrame({'ticker': filtered_df['ticker'].tolist()})
            ticker_file = self.tickers_dir / f'combined_tickers_{choice_str}.csv'
            tickers_only.to_csv(ticker_file, index=False)
            
            # 2. combined_info_tickers_{choice}.csv (all columns)
            info_file = self.tickers_dir / f'combined_info_tickers_{choice_str}.csv'
            filtered_df.to_csv(info_file, index=False)
            
            # 3. combined_info_tickers_clean_{choice}.csv (same as info)
            clean_file = self.tickers_dir / f'combined_info_tickers_clean_{choice_str}.csv'
            filtered_df.to_csv(clean_file, index=False)
            
            print(f"✅ Generated individual mode files for choice {choice}: {len(filtered_df)} tickers")
            return True
            
        except Exception as e:
            print(f"❌ Error generating individual mode files for choice {choice}: {e}")
            return False
    
    def _filter_by_choice(self, df, choice):
        """Filter dataframe by choice using boolean columns."""
        filters = self.choice_filters.get(choice)
        if filters is None:
            print(f"❌ No filter definition for choice {choice}")
            return None
        
        # Handle choice 0 (no filtering)
        if choice == 0 or not filters:
            print(f"  • No filtering applied - using full universe ({len(df)} tickers)")
            return df
        
        # Apply OR filtering for multiple indexes
        mask = pd.Series([False] * len(df))
        found_filters = []
        
        for filter_col in filters:
            if filter_col in df.columns:
                mask = mask | df[filter_col]
                count = df[filter_col].sum()
                found_filters.append(f"{filter_col}({count})")
            else:
                print(f"  ⚠️  Column {filter_col} not found in universe file")
        
        filtered_df = df[mask]
        print(f"  • Applied filters: {', '.join(found_filters)}")
        print(f"  • Choice {choice}: {len(filtered_df)} tickers after filtering")
        
        return filtered_df
    
    def _print_summary(self, user_choice, choices):
        """Print summary of generated files."""
        print(f"\n📋 FILE GENERATION SUMMARY")
        print(f"{'='*40}")
        print(f"User choice: {user_choice}")
        print(f"Individual choices processed: {choices}")
        
        # Count generated files
        total_files = 0
        for choice in [0] + [c for c in choices if c != 0]:
            choice_files = list(self.tickers_dir.glob(f'*_{choice}.csv'))
            total_files += len(choice_files)
            print(f"  Choice {choice}: {len(choice_files)} files")
        
        # Combined files
        if len(choices) > 1 or (len(choices) == 1 and choices[0] != 0):
            combined_name = str(user_choice)
            if combined_name not in [str(c) for c in choices]:
                combined_files = list(self.tickers_dir.glob(f'*_{combined_name}.csv'))
                total_files += len(combined_files)
                print(f"  Combined {combined_name}: {len(combined_files)} files")
        
        print(f"Total files generated: {total_files}")


def generate_all_ticker_files(config, user_choice):
    """
    Main entry point for unified ticker file generation.
    
    Args:
        config: Config object with directories
        user_choice: User choice (int, str) - any format
        
    Returns:
        bool: True if successful, False otherwise
    """
    generator = UnifiedTickerGenerator(config)
    return generator.generate_all_ticker_files(user_choice)