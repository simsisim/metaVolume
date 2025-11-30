"""
Configuration management for the financial data post-processing system.
Handles directory structure, file paths, and ticker selection logic.
"""

import os
import logging
from pathlib import Path
from datetime import datetime
from src.user_defined_data import read_user_data_legacy, read_user_data, _get_default_ticker_filenames

logger = logging.getLogger(__name__)


class Config:
    """Main configuration class for post-processing financial data."""
    
    def __init__(self):
        self.base_dir = Path(__file__).resolve().parent.parent
        self.current_date = datetime.now().strftime('%Y%m%d')

        # Read user preferences first (needed for environment detection)
        self.user_choice, self.write_file_info = read_user_data_legacy()
        user_config = read_user_data()
        self.ticker_filenames = user_config.ticker_filenames

        # Detect environment before setting up directories
        self.environment = self._detect_environment(user_config)

        # Initialize configuration components
        self._setup_directories()
        self._setup_paths()

    def _detect_environment(self, user_config):
        """
        Detect whether running in local environment or Google Colab.

        Args:
            user_config: User configuration object

        Returns:
            str: 'local' or 'colab'
        """
        # Check user's manual override first
        try:
            manual_override = getattr(user_config, 'manual_environment_override', None)
            if manual_override and str(manual_override).strip() and str(manual_override).lower() != 'nan':
                override_value = str(manual_override).strip().lower()
                if override_value in ['local', 'colab']:
                    logger.info(f"Using manual environment override: {override_value}")
                    return override_value
        except Exception as e:
            logger.warning(f"Error reading manual environment override: {e}")
            pass  # Continue with auto-detection

        # Auto-detect environment
        # Method 1: Check for Colab-specific environment variables
        if 'COLAB_GPU' in os.environ:
            return 'colab'

        # Method 2: Check for typical Colab paths
        if os.path.exists('/content'):
            return 'colab'

        # Method 3: Check if current working directory is in Colab structure
        cwd = str(Path.cwd())
        if '/content/drive/MyDrive' in cwd:
            return 'colab'

        # Method 4: Check if base directory is in Colab structure
        if '/content/drive/MyDrive' in str(self.base_dir):
            return 'colab'

        # Default to local environment
        return 'local'

    def _setup_directories(self):
        """Define all directory paths using user-configurable settings."""
        user_config = read_user_data()

        self.directories = {
            # Data directories
            "DATA_DIR": self.base_dir / "data",
            "TICKERS_DIR": self.base_dir / "data" / "tickers",

            # Market data directories - use environment-specific paths from user config
            "MARKET_DATA_DIR": Path(self._get_environment_specific_path('daily') or "data/market_data").parent,
            "DAILY_DATA_DIR": Path(self._get_environment_specific_path('daily') or "data/market_data/daily"),
            "WEEKLY_DATA_DIR": Path(self._get_environment_specific_path('weekly') or "data/market_data/weekly"),
            "MONTHLY_DATA_DIR": Path(self._get_environment_specific_path('monthly') or "data/market_data/monthly"),
            "INTRADAY_DATA_DIR": Path(self._get_environment_specific_path('intraday') or "data/intraday"),

            # Base output directories
            "RESULTS_DIR": self.base_dir / "results",
            "OVERVIEW_DIR": self.base_dir / "results" / "overview",
            "CALCULATIONS_DIR": self.base_dir / "results" / "calculations",
            "MODELS_DIR": self.base_dir / "results" / "models",

            # User-configurable calculation output directories
            "BASIC_CALCULATION_DIR": self._resolve_user_directory(user_config.basic_calculation_output_dir),
            "STAGE_ANALYSIS_DIR": self._resolve_user_directory(user_config.stage_analysis_output_dir),
            "RS_DIR": self._resolve_user_directory(user_config.rs_output_dir),
            "PER_DIR": self._resolve_user_directory(user_config.per_output_dir),
            "SR_output_dir": self._resolve_user_directory(user_config.sr_output_dir),

            # User-configurable screener output directories
            "PVB_SCREENER_DIR": self._resolve_user_directory(user_config.pvb_TWmodel_output_dir),
            "ATR1_SCREENER_DIR": self._resolve_user_directory(user_config.atr1_output_dir),
            "DRWISH_SCREENER_DIR": self._resolve_user_directory(user_config.drwish_output_dir),
            "GIUSTI_SCREENER_DIR": self._resolve_user_directory(user_config.giusti_output_dir),
            "MINERVINI_SCREENER_DIR": self._resolve_user_directory(user_config.minervini_output_dir),
            "STOCKBEE_SCREENER_DIR": self._resolve_user_directory(user_config.stockbee_output_dir),
            "QULLAMAGGIE_SCREENER_DIR": self._resolve_user_directory(user_config.qullamaggie_output_dir),
            "ADL_SCREENER_DIR": self._resolve_user_directory(user_config.adl_screener_output_dir),
            "GUPPY_SCREENER_DIR": self._resolve_user_directory(user_config.guppy_screener_output_dir),
            "GOLD_LAUNCH_PAD_SCREENER_DIR": self._resolve_user_directory(user_config.gold_launch_pad_output_dir),
            "RTI_SCREENER_DIR": self._resolve_user_directory(user_config.rti_output_dir),

            # Legacy screeners directory for backwards compatibility
            "SCREENERS_DIR": self.base_dir / "results" / "screeners",

            # RS sub-directories (based on user RS directory)
            "RS_VALUES_DIR": self._resolve_user_directory(user_config.rs_output_dir) / "rs_values",
            "RS_PERCENTILES_DIR": self._resolve_user_directory(user_config.per_output_dir),  # PER gets its own directory now
        }

    def _resolve_user_directory(self, user_path):
        """
        Resolve user-configured directory path.
        Supports both relative and absolute paths.

        Args:
            user_path (str): User-configured directory path

        Returns:
            Path: Resolved directory path
        """
        if not user_path:
            # Fallback to default if path is empty
            return self.base_dir / "results"

        user_path_str = str(user_path).strip()
        if os.path.isabs(user_path_str):
            # Absolute path - use as is
            return Path(user_path_str)
        else:
            # Relative path - resolve relative to base directory
            return self.base_dir / user_path_str
    
    def _setup_paths(self):
        """Define specific file paths."""
        self.paths = {
            # Configuration files
            "USER_DATA_CONFIG": self.base_dir / "user_data.csv",
            
            # Output files (will be updated based on user choice)
            "OVERVIEW_FILE": self.directories["OVERVIEW_DIR"] / "indexes_overview.csv",
            "CALCULATIONS_FILE": self.directories["CALCULATIONS_DIR"] / "basic_calculations.csv",
            "SCREENER_RESULTS": self.directories["SCREENERS_DIR"] / "screener_results.csv",
            "MODEL_RESULTS": self.directories["MODELS_DIR"] / "model_results.csv"
        }
    
    
    def create_directories(self):
        """Create all required directories."""
        for dir_path in self.directories.values():
            os.makedirs(dir_path, exist_ok=True)
    
    def get_ticker_files(self, user_choice=None):
        """
        Get ticker files based on user choice.
        Supports both single numbers and dash-separated combinations (e.g., "1-2-3").
        
        Args:
            user_choice (str/int, optional): Override the default user choice
            
        Returns:
            list: List of ticker filenames to process
        """
        # Read current user configuration to get both choice and filenames
        config = read_user_data()
        current_user_choice = user_choice if user_choice is not None else config.ticker_choice

        # Get ticker group filenames from user configuration (with fallback to defaults)
        ticker_filenames = config.ticker_filenames or _get_default_ticker_filenames()
        
        # Convert to the expected format (group_id -> list of files)
        group_files = {group_id: [filename] for group_id, filename in ticker_filenames.items()}
        
        # Parse ticker choice (handle both string and int)
        ticker_choice_str = str(current_user_choice).strip()
        
        # Split by dash to get individual group IDs
        try:
            group_ids = [int(id_str.strip()) for id_str in ticker_choice_str.split('-')]
        except ValueError:
            raise ValueError(f"Invalid ticker_choice format: '{ticker_choice_str}'. Use single numbers or dash-separated (e.g., '1-2-3').")

        # Validate all group IDs
        for group_id in group_ids:
            if group_id not in group_files:
                raise ValueError(f"Invalid group ID: {group_id}. Valid groups are 0-8.")

        # Combine files from all selected groups (remove duplicates)
        combined_files = []
        for group_id in group_ids:
            for file in group_files[group_id]:
                if file not in combined_files:
                    combined_files.append(file)

        return combined_files
    
    def find_ticker_file(self, filename):
        """
        Find ticker file with root directory priority.
        First checks root directory, then fallback to data/tickers/.
        
        Args:
            filename (str): Ticker filename to find
            
        Returns:
            Path or None: Path to the file if found, None otherwise
        """
        # First check root directory (PRIORITY)
        root_path = Path(filename)
        if root_path.exists():
            return root_path
        
        # Fallback to data/tickers/ directory
        tickers_path = Path(self.directories['TICKERS_DIR']) / filename
        if tickers_path.exists():
            return tickers_path
        
        return None
    
    def get_market_data_dir(self, timeframe='daily'):
        """
        Get the appropriate market data directory for the given timeframe.
        Uses environment-specific paths when available, falls back to hardcoded paths.

        Args:
            timeframe (str): 'daily', 'weekly', 'monthly', or 'intraday'

        Returns:
            Path: Directory path for the specified timeframe
        """
        # Try to get environment-specific path first
        env_path = self._get_environment_specific_path(timeframe)
        if env_path:
            return Path(env_path)

        # Fallback to hardcoded directory structure
        timeframe_mapping = {
            'daily': 'DAILY_DATA_DIR',
            'weekly': 'WEEKLY_DATA_DIR',
            'monthly': 'MONTHLY_DATA_DIR',
            'intraday': 'INTRADAY_DATA_DIR'
        }

        if timeframe not in timeframe_mapping:
            raise ValueError(f"Invalid timeframe '{timeframe}'. Choose from: daily, weekly, monthly, intraday")

        return self.directories[timeframe_mapping[timeframe]]

    def _get_environment_specific_path(self, timeframe):
        """
        Get environment-specific market data path from user configuration.

        Args:
            timeframe (str): 'daily', 'weekly', 'monthly', or 'intraday'

        Returns:
            str or None: Path string if found, None otherwise
        """
        try:
            user_config = read_user_data()

            # Map timeframes to config keys based on detected environment
            config_key_mapping = {
                'daily': f'yf_daily_data_files_{self.environment}',
                'weekly': f'yf_weekly_data_files_{self.environment}',
                'monthly': f'yf_monthly_data_files_{self.environment}',
                'intraday': f'tw_intraday_folder_{self.environment}'
            }

            if timeframe not in config_key_mapping:
                return None

            config_key = config_key_mapping[timeframe]
            path = getattr(user_config, config_key, None)

            # Check if path is valid (not None, not empty, not 'nan')
            if path and str(path).strip() and str(path).lower() != 'nan':
                path_str = str(path).strip()

                # Convert relative paths to absolute paths
                if not os.path.isabs(path_str):
                    path_str = os.path.join(str(self.base_dir), path_str)

                return path_str

        except Exception as e:
            # If environment-specific path reading fails, return None for fallback
            logger.warning(f"Failed to read environment-specific path for {timeframe}: {e}")

        return None
    
    def get_output_filename(self, file_type, user_choice=None):
        """
        Generate timestamped output filename based on file type and user choice.
        
        Args:
            file_type (str): Type of output file ('overview', 'calculations', 'screener', 'model')
            user_choice (str/int, optional): Override the default user choice
            
        Returns:
            Path: Full path to the output file
        """
        choice = user_choice if user_choice is not None else self.user_choice
        # Use centralized naming function to preserve hyphens
        safe_choice = get_file_safe_user_choice(choice, preserve_hyphens=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        filename_templates = {
            'overview': f'overview_{safe_choice}_{timestamp}.csv',
            'calculations': f'calculations_{safe_choice}_{timestamp}.csv', 
            'screener': f'screener_{safe_choice}_{timestamp}.csv',
            'model': f'model_{safe_choice}_{timestamp}.csv'
        }
        
        if file_type not in filename_templates:
            raise ValueError(f"Invalid file_type '{file_type}'. Choose from: {list(filename_templates.keys())}")
        
        directory_mapping = {
            'overview': 'OVERVIEW_DIR',
            'calculations': 'CALCULATIONS_DIR',
            'screener': 'SCREENERS_DIR', 
            'model': 'MODELS_DIR'
        }
        
        return self.directories[directory_mapping[file_type]] / filename_templates[file_type]
    
    def __str__(self):
        """String representation of configuration."""
        return f"Config(user_choice={self.user_choice}, base_dir={self.base_dir})"


# Centralized file naming functions
def get_file_safe_user_choice(user_choice, preserve_hyphens=True):
    """
    Central function to handle user_choice formatting for filenames.
    
    Args:
        user_choice: User ticker choice (e.g., '0-5')
        preserve_hyphens: If True, keep hyphen format (0-5). If False, use underscore format (0_5)
        
    Returns:
        str: Formatted user choice for filenames
    """
    if preserve_hyphens:
        return str(user_choice)  # Keep 0-5 format
    else:
        return str(user_choice).replace('-', '_')  # Legacy 0_5 format


# Legacy support functions for backwards compatibility
def setup_directories():
    """Legacy function - use Config().create_directories() instead."""
    config = Config()
    config.create_directories()

def get_ticker_files(config=None):
    """Get ticker files configuration from user data."""
    if config is None:
        # Legacy function - use Config() instance
        config = Config()
        return config.get_ticker_files()
    else:
        # New function - use provided config object
        return config.ticker_filenames or _get_default_ticker_filenames()


def find_ticker_file(filename, config):
    """Find ticker file with root directory priority."""
    from pathlib import Path
    
    # First try root directory (PRIORITY)
    root_path = Path(filename)
    if root_path.exists():
        return root_path
    
    # Fallback to tickers directory
    tickers_dir = Path(config.directories['TICKERS_DIR'])
    ticker_path = tickers_dir / filename
    
    if ticker_path.exists():
        return ticker_path
    
    return None


# Legacy directory constants for backwards compatibility  
PARAMS_DIR = {
    "DATA_DIR": "data",
    "TICKERS_DIR": os.path.join("data", "tickers"),
    "MARKET_DATA_DIR_1d": os.path.join("data", "market_data", "daily"),
    "MARKET_DATA_DIR_1wk": os.path.join("data", "market_data", "weekly"),
    "MARKET_DATA_DIR_1mo": os.path.join("data", "market_data", "monthly")
}