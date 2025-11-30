import pandas as pd
from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class UserConfiguration:
    """
    Data class to hold all user configuration settings.
    """
    # Ticker data sources
    web_tickers_down: bool = False
    tw_tickers_down: bool = True  
    tw_universe_file: str = "tradingview_universe.csv"
    
    # Historical data collection (downloading - now disabled for post-processing)
    yf_hist_data: bool = False
    yf_daily_data: bool = False
    yf_weekly_data: bool = False  
    yf_monthly_data: bool = False
    tw_intraday_data: bool = False
    tw_intraday_file: str = "intraday_data.csv"
    
    # Financial data enrichment (downloading - now disabled for post-processing)
    fin_data_enrich: bool = False
    yf_fin_data: bool = False
    tw_fin_data: bool = False
    zacks_fin_data: bool = False
    
    # GLOBAL EXECUTION PHASE CONTROL
    PRE_PROCESS: bool = True  # Execute pre-processing of TradingView data phase
    BASIC: bool = True        # Execute data processing and core calculations phase
    SCREENERS: bool = True    # Execute screening and analysis phase
    POST_PROCESS: bool = True # Execute post-processing and report generation phase
    BACKTESTING: bool = False # Execute backtesting analysis of screener strategies

    # PRE_PROCESS configuration
    PRE_PROCESS_file: str = "user_data_pre_process.csv"

    # General settings
    write_info_file: bool = True
    ticker_info_TW: bool = False
    ticker_info_TW_file: str = "tradingview_universe_info.csv"
    ticker_info_YF: bool = True
    ticker_choice: str = "2"
    batch_size: int = 100
    
    # Ticker group filenames
    ticker_filenames: dict = None
    
    # POST-PROCESSING CONFIGURATION
    # Input historical data sources (local data loading)
    yf_daily_data_files: str = "data/market_data/daily/"
    yf_weekly_data_files: str = "data/market_data/weekly/"
    yf_monthly_data_files: str = "data/market_data/monthly/"
    tw_intraday_folder: str = "data/intraday/"

    # Environment detection and paths
    auto_detect_environment: bool = True
    manual_environment_override: Optional[str] = None

    # Local environment paths
    yf_daily_data_files_local: Optional[str] = None
    yf_weekly_data_files_local: Optional[str] = None
    yf_monthly_data_files_local: Optional[str] = None
    tw_intraday_folder_local: Optional[str] = None

    # Colab environment paths
    yf_daily_data_files_colab: Optional[str] = None
    yf_weekly_data_files_colab: Optional[str] = None
    yf_monthly_data_files_colab: Optional[str] = None
    tw_intraday_folder_colab: Optional[str] = None

    # Overview files
    indexes_overview_file: str = "indexes_overview.csv"
    
    # INDEX OVERVIEW CONFIGURATION
    sp500_overview: bool = True
    nasdaq100_overview: bool = True
    djia_overview: bool = True
    
    # Index Overview Period Configurations
    # Daily Period Percent Change Configuration        
    index_daily_daily_periods: str = "2;3;5"    # Daily data: daily percent change periods (semicolon separated - 2d;3d;5d)
    index_daily_weekly_periods: str = "7"    # Daily data: weekly percent change periods (days back)
    index_daily_monthly_periods: str = "22;44"    # Daily data: monthly percent change periods (semicolon separated - 1m;2m)
    index_daily_quarterly_periods: str = "66;132"    # Daily data: quarterly percent change periods (semicolon separated - 1q;2q)
    index_daily_yearly_periods: str = "252"    # Daily data: yearly percent change periods (days back)
    # Weekly Period Percent Change Configuration        
    index_weekly_weekly_periods: str = "2;4"    # Weekly data: weekly percent change periods (weeks back)
    index_weekly_monthly_periods: str = "4;8"    # Weekly data: monthly percent change periods (semicolon separated - 1m;2m)
    # Monthly Period Percent Change Configuration        
    index_monthly_monthly_periods: str = "2;3;6"    # Monthly data: monthly percent change periods (months back)
    
    # Index Overview RS Period Configurations
    # Daily RS Configuration
    index_daily_rs_periods: str = "10;20;50;100"    # Daily RS periods (days)
    index_daily_rs_short_periods: str = "5;10"    # Short-term RS periods
    index_daily_rs_long_periods: str = "100;200"    # Long-term RS periods
    # Weekly RS Configuration  
    index_weekly_rs_periods: str = "4;13;26;52"    # Weekly RS periods (weeks)
    index_weekly_rs_short_periods: str = "2;4"    # Short-term weekly RS
    index_weekly_rs_long_periods: str = "26;52"    # Long-term weekly RS
    # Monthly RS Configuration
    index_monthly_rs_periods: str = "3;6;12"    # Monthly RS periods (months)
    
    # Output directory configuration
    basic_calculation_output_dir: str = "results/basic_calculation"
    stage_analysis_output_dir: str = "results/stage_analysis"
    rs_output_dir: str = "results/rs"
    per_output_dir: str = "results/per"
    # Screener output directories
    pvb_TWmodel_output_dir: str = "results/screeners/pvb"
    atr1_output_dir: str = "results/screeners/atr1"
    drwish_output_dir: str = "results/screeners/drwish"
    giusti_output_dir: str = "results/screeners/giusti"
    minervini_output_dir: str = "results/screeners/minervini"
    stockbee_output_dir: str = "results/screeners/stockbee"
    qullamaggie_output_dir: str = "results/screeners/qullamaggie"
    adl_screener_output_dir: str = "results/screeners/adl"
    guppy_screener_output_dir: str = "results/screeners/guppy"
    gold_launch_pad_output_dir: str = "results/screeners/gold_launch_pad"
    rti_output_dir: str = "results/screeners/rti"

    # Basic calculations (legacy)
    basic_calculation_file: str = "basic_calculations.csv"
    # Basic calculations timeframe enable flags
    basic_calc_daily_enable: bool = True
    basic_calc_weekly_enable: bool = True
    basic_calc_monthly_enable: bool = True
    # Daily period percent change configuration
    daily_daily_periods: str = "2;3;5"
    daily_weekly_periods: str = "7"
    daily_monthly_periods: str = "22;44"  
    daily_quarterly_periods: str = "66;132"
    daily_yearly_periods: str = "252"
    # Weekly period percent change configuration
    weekly_weekly_periods: str = "2;4"
    weekly_monthly_periods: str = "4;8"
    # Monthly period percent change configuration
    monthly_monthly_periods: str = "2;3;6"
    # Monthly RS periods
    RS_monthly_periods: str = "1;3;6"

    # SUSTAINABILITY RATIOS (SR) CONFIGURATION
    sr_enable: bool = False
    sr_output_dir: str = "results/sustainability_ratios"
    sr_panel_config_file: str = "user_data_sr_panel.csv"
    sr_timeframes: str = "daily"  # Legacy setting - use sr_timeframe_* settings instead
    # New granular timeframe controls
    sr_timeframe_daily: bool = True
    sr_timeframe_weekly: bool = False
    sr_timeframe_monthly: bool = False
    # Chart display range control
    sr_chart_display: int = 66  # Number of historical data points to show on charts
    sr_chart_generation: bool = True
    sr_intermarket_ratios: bool = True
    sr_market_breadth: bool = True
    sr_save_detailed_results: bool = True
    sr_dashboard_style: str = "multi_panel"
    sr_lookback_days: int = 252

    # SUBMODULE CONTROL FLAGS
    sr_panels_enable: bool = True
    sr_overview_enable: bool = True
    sr_intermarket_enable: bool = True
    sr_breadth_enable: bool = True

    # OVERVIEW SUBMODULE CONFIGURATION
    sr_overview_values_enable: bool = True
    sr_overview_charts_enable: bool = True
    sr_overview_values_history: int = 10
    sr_overview_values_indexes: str = "SPY;IWM"
    sr_overview_values_sectors: str = "XLY;XLC"
    sr_overview_values_industries: str = "NVDA"
    sr_overview_values_timeframe: str = "latest;5;latest_Wednesday"
    sr_overview_output_dir: str = "results/sustainability_ratios/overview"
    sr_overview_filename_prefix: str = "sr_overview"
    sr_overview_charts_tickers: str = "SPY;IWM"
    sr_overview_charts_display_panel: str = "user_data_sr_overview.csv"
    sr_overview_charts_display_history: int = 30

    # MMM SUBMODULE CONFIGURATION
    sr_mmm_enable: bool = False
    sr_mmm_daily_enable: bool = True
    sr_mmm_weekly_enable: bool = False
    sr_mmm_monthly_enable: bool = False
    sr_mmm_gaps_values: bool = True
    sr_mmm_gaps_tickers: str = "XLY;XLC"
    sr_mmm_gaps_values_input_folder_daily: str = "../downloadData_v1/data/market_data/daily/"
    sr_mmm_gaps_values_input_folder_weekly: str = "../downloadData_v1/data/market_data/weekly/"
    sr_mmm_gaps_values_input_folder_monthly: str = "../downloadData_v1/data/market_data/monthly/"
    sr_mmm_gaps_values_output_folder_daily: str = "../downloadData_v1/data/market_data/daily/"
    sr_mmm_gaps_values_output_folder_weekly: str = "../downloadData_v1/data/market_data/weekly/"
    sr_mmm_gaps_values_output_folder_monthly: str = "../downloadData_v1/data/market_data/monthly/"
    sr_mmm_gaps_values_filename_suffix: str = "_gap"
    sr_mmm_gaps_chart_enable: bool = True
    sr_mmm_gaps_charts_display_panel: str = "user_data_sr_mmm.csv"
    sr_mmm_gaps_charts_display_history: int = 30
    sr_mmm_output_dir: str = "results/sustainability_ratios/mmm"

    # Screeners
    screener_output_file: str = "screener_results.csv"
    screener_criteria_file: str = "screener_criteria.csv"
    
    # Models
    models_output_file: str = "model_results.csv"
    models_config_file: str = "model_configuration.csv"
    
    # Database functionality completely removed
    
    # PDF report configuration
    pdf_reports_enable: bool = True
    pdf_reports_output_dir: str = "results/reports"
    pdf_reports_include_charts: bool = True
    
    # REPORT GENERATION CONFIGURATION
    report_enable: bool = False
    report_template_type: str = "indexes_overview"
    report_page_size: str = "A4_landscape"
    report_output_dir: str = "results/reports"
    report_include_charts: bool = True
    report_file_dates_auto: bool = True
    report_file_dates_manual: str = ""
    report_sections_basic_stats: bool = True
    report_sections_percentage_analysis: bool = True
    report_sections_rs_analysis: bool = True
    report_sections_tornado_charts: bool = True
    report_sections_summary: bool = True
    report_max_tickers_display: int = 20
    report_format: str = "PDF"
    report_include_metadata: bool = True
    
    # INDEX OVERVIEW CONFIGURATION
    sp500_overview: bool = True
    nasdaq100_overview: bool = True
    djia_overview: bool = True
    
    # TECHNICAL INDICATORS CONFIGURATION
    # Daily timeframe indicators
    daily_ema_periods: str = "10;20"
    daily_sma_periods: str = "20;50;200;250;350"
    # Weekly timeframe indicators  
    weekly_ema_periods: str = "10"
    weekly_sma_periods: str = "20;50"
    # Monthly timeframe indicators
    monthly_ema_periods: str = "10"
    monthly_sma_periods: str = "12;24"
    
    # PERCENTAGE MOVERS CONFIGURATION
    enable_movers_analysis: bool = True
    daily_pct_threshold: float = 4.0
    weekly_pct_threshold: float = 20.0
    movers_output_dir: str = "results/movers/"
    movers_min_volume: int = 10000
    movers_top_n: int = 50
    
    # BASIC SCREENERS CONFIGURATION
    basic_momentum_enable: bool = False
    basic_breakout_enable: bool = False
    basic_value_momentum_enable: bool = False
    
    # ATR (AVERAGE TRUE RANGE) CONFIGURATION
    enable_atr_calculation: bool = True
    atr_period: int = 14
    atr_sma_period: int = 50
    enable_atr_percentile: bool = True
    atr_percentile_period: int = 100
    
    # ATR SCREENER CONFIGURATION
    # ATR1 Screener (TradingView-validated with RMA smoothing)
    atr1_enable: bool = True
    # Daily ATR1 parameters
    atr1_daily_length: int = 20
    atr1_daily_factor: float = 3.0
    atr1_daily_length2: int = 20
    atr1_daily_factor2: float = 1.5
    # Weekly ATR1 parameters
    atr1_weekly_length: int = 4
    atr1_weekly_factor: float = 3.0
    atr1_weekly_length2: int = 4
    atr1_weekly_factor2: float = 1.5
    # Monthly ATR1 parameters
    atr1_monthly_length: int = 2
    atr1_monthly_factor: float = 3.0
    atr1_monthly_length2: int = 2
    atr1_monthly_factor2: float = 1.5
    
    # ATR2 Screener (Volatility analysis with Wilder smoothing)
    atr2_enable: bool = True
    # Daily ATR2 parameters
    atr2_daily_atr_period: int = 14
    atr2_daily_sma_period: int = 50
    atr2_daily_percentile_period: int = 100
    # Weekly ATR2 parameters
    atr2_weekly_atr_period: int = 14
    atr2_weekly_sma_period: int = 10
    atr2_weekly_percentile_period: int = 20
    # Monthly ATR2 parameters
    atr2_monthly_atr_period: int = 14
    atr2_monthly_sma_period: int = 4
    atr2_monthly_percentile_period: int = 6
    
    # STAGE ANALYSIS CONFIGURATION - Global
    enable_stage_analysis: bool = False

    # STAGE ANALYSIS CONFIGURATION - Daily
    stage_analysis_daily_enabled: bool = True
    stage_daily_ema_fast_period: int = 10
    stage_daily_sma_medium_period: int = 20
    stage_daily_sma_slow_period: int = 50
    stage_daily_atr_period: int = 14
    stage_daily_atr_threshold_low: float = 4.0
    stage_daily_atr_threshold_high: float = 7.0
    stage_daily_ma_convergence_threshold: float = 1.0
    
    # STAGE ANALYSIS CONFIGURATION - Weekly
    stage_analysis_weekly_enabled: bool = True
    stage_weekly_ema_fast_period: int = 10
    stage_weekly_sma_medium_period: int = 20
    stage_weekly_sma_slow_period: int = 50
    stage_weekly_atr_period: int = 14
    stage_weekly_atr_threshold_low: float = 4.0
    stage_weekly_atr_threshold_high: float = 7.0
    stage_weekly_ma_convergence_threshold: float = 1.0
    
    # STAGE ANALYSIS CONFIGURATION - Monthly
    stage_analysis_monthly_enabled: bool = True
    stage_monthly_ema_fast_period: int = 10
    stage_monthly_sma_medium_period: int = 20
    stage_monthly_sma_slow_period: int = 50
    stage_monthly_atr_period: int = 14
    stage_monthly_atr_threshold_low: float = 4.0
    stage_monthly_atr_threshold_high: float = 7.0
    stage_monthly_ma_convergence_threshold: float = 1.0
    
    # STAGE ANALYSIS CONFIGURATION - Legacy (deprecated)
    stage_analysis_enabled: bool = True
    stage_analysis_min_price: float = 5.0
    stage_analysis_min_vol: int = 100000
    stage_analysis_report_enable: bool = True
    stage_ema_fast_period: int = 10
    stage_sma_medium_period: int = 20
    stage_sma_slow_period: int = 50
    stage_atr_period: int = 14
    stage_atr_threshold_low: float = 4.0
    stage_atr_threshold_high: float = 7.0
    stage_ma_convergence_threshold: float = 1.0
    
    # RELATIVE STRENGTH (RS) CONFIGURATION - MULTI-BENCHMARK
    rs_enable_stocks: bool = True
    rs_enable_sectors: bool = True
    rs_enable_industries: bool = True
    # Multi-benchmark configuration
    rs_benchmark_tickers: str = "SPY;QQQ"
    # Legacy single benchmark (backward compatibility)
    rs_benchmark_ticker: str = "SPY"
    rs_composite_method: str = "equal_weighted"
    rs_output_dir: str = "results/RS/"
    rs_min_group_size: int = 3
    # Percentile universe configurations
    rs_percentile_universe_stocks: str = "ticker_choice"
    rs_percentile_universe_sectors: str = "all"
    rs_percentile_universe_industries: str = "all"

    # New mapping-based percentile configuration (preferred)
    rs_percentile_mapping_stocks: str = ""
    rs_percentile_mapping_sectors: str = ""
    rs_percentile_mapping_industries: str = ""
    # Daily timeframe parameters
    rs_daily_enable: bool = True
    # Weekly timeframe parameters  
    rs_weekly_enable: bool = True
    # Monthly timeframe parameters
    rs_monthly_enable: bool = True

    # MOVING AVERAGE RS CONFIGURATION
    rs_ma_enable: bool = False
    rs_ma_method: str = "20;50"
    rs_method_for_per: str = "IBD"

    # TECHNICAL INDICATORS CONFIGURATION
    indicators_enable: bool = True
    indicators_config_file: str = "data/indicators/ticker_indicators_config.csv"
    indicators_output_dir: str = "results/indicators/"
    indicators_charts_dir: str = "results/charts/"
    
    # Default Indicator Parameters
    indicators_kurutoga_enable: bool = True
    indicators_kurutoga_length: int = 14
    indicators_kurutoga_source: str = "Close"
    
    indicators_tsi_enable: bool = True
    indicators_tsi_fast: int = 13
    indicators_tsi_slow: int = 25
    indicators_tsi_signal: int = 13
    
    indicators_macd_enable: bool = True
    indicators_macd_fast: int = 12
    indicators_macd_slow: int = 26
    indicators_macd_signal: int = 9
    
    indicators_mfi_enable: bool = True
    indicators_mfi_length: int = 14
    indicators_mfi_signal_enable: bool = True
    indicators_mfi_signal_period: int = 9
    
    indicators_cog_enable: bool = True
    indicators_cog_length: int = 9
    indicators_cog_source: str = "Close"
    
    indicators_momentum_enable: bool = True
    indicators_momentum_length: int = 20
    
    indicators_rsi_enable: bool = True
    indicators_rsi_length: int = 14
    
    indicators_ma_crosses_enable: bool = True
    indicators_ma_fast_period: int = 50
    indicators_ma_slow_period: int = 200
    
    indicators_easy_trade_enable: bool = True
    indicators_easy_trade_fast: int = 12
    indicators_easy_trade_slow: int = 26
    indicators_easy_trade_signal: int = 9
    
    # PVB (Price Volume Breakout) screener settings
    pvb_TWmodel_enable: bool = True
    pvb_TWmodel_daily_enable: bool = True
    pvb_TWmodel_weekly_enable: bool = True
    pvb_TWmodel_monthly_enable: bool = True
    # Daily timeframe PVB parameters
    pvb_TWmodel_daily_price_breakout_period: int = 60
    pvb_TWmodel_daily_volume_breakout_period: int = 60
    pvb_TWmodel_daily_trendline_length: int = 50
    pvb_TWmodel_daily_close_threshold: int = 5
    pvb_TWmodel_daily_signal_max_age: int = 100
    # Weekly timeframe PVB parameters
    pvb_TWmodel_weekly_price_breakout_period: int = 12
    pvb_TWmodel_weekly_volume_breakout_period: int = 12
    pvb_TWmodel_weekly_trendline_length: int = 10
    pvb_TWmodel_weekly_close_threshold: int = 2
    pvb_TWmodel_weekly_signal_max_age: int = 20
    # Monthly timeframe PVB parameters
    pvb_TWmodel_monthly_price_breakout_period: int = 6
    pvb_TWmodel_monthly_volume_breakout_period: int = 6
    pvb_TWmodel_monthly_trendline_length: int = 4
    pvb_TWmodel_monthly_close_threshold: int = 1
    pvb_TWmodel_monthly_signal_max_age: int = 6
    # Common PVB parameters
    pvb_TWmodel_order_direction: str = "Long and Short"
    pvb_TWmodel_min_volume: int = 10000
    pvb_TWmodel_min_price: float = 1.0
    # TradingView Watchlist Export Configuration
    pvb_TWmodel_export_tradingview: bool = True
    pvb_TWmodel_watchlist_max_symbols: int = 1000
    pvb_TWmodel_watchlist_include_buy: bool = True
    pvb_TWmodel_watchlist_include_sell: bool = True

    # MINERVINI TEMPLATE SCREENER CONFIGURATION
    minervini_enable: bool = True
    minervini_rs_min_rating: float = 70.0
    minervini_min_volume: int = 100000
    minervini_min_price: float = 5.0
    minervini_show_all_stocks: bool = False
    
    # GIUSTI MOMENTUM SCREENER CONFIGURATION
    giusti_enable: bool = True
    giusti_min_price: float = 5.0
    giusti_min_volume: int = 100000
    giusti_rolling_12m: int = 12
    giusti_rolling_6m: int = 6
    giusti_rolling_3m: int = 3
    giusti_top_12m_count: int = 50
    giusti_top_6m_count: int = 30
    giusti_top_3m_count: int = 10
    giusti_min_history_months: int = 12
    giusti_show_all_stocks: bool = False
    
    # DR. WISH SUITE SCREENER CONFIGURATION
    drwish_enable: bool = True
    drwish_min_price: float = 5.0
    drwish_min_volume: int = 100000
    drwish_pivot_strength: int = 10
    drwish_lookback_period: str = "3m"
    drwish_calculate_historical_GLB: str = "1y"
    drwish_confirmation_period: str = "2w"
    drwish_require_confirmation: bool = True
    drwish_enable_glb: bool = True
    drwish_enable_blue_dot: bool = True
    drwish_enable_black_dot: bool = True
    drwish_blue_dot_stoch_period: int = 10
    drwish_blue_dot_stoch_threshold: float = 20.0
    drwish_blue_dot_sma_period: int = 50
    drwish_black_dot_stoch_period: int = 10
    drwish_black_dot_stoch_threshold: float = 25.0
    drwish_black_dot_lookback: int = 3
    drwish_black_dot_sma_period: int = 30
    drwish_black_dot_ema_period: int = 21
    drwish_show_all_stocks: bool = False
    drwish_enable_charts: bool = True
    drwish_chart_output_dir: str = "results/screeners/drwish/charts"
    drwish_show_historical_glb: bool = True
    drwish_show_breakout_labels: bool = True
    drwish_generate_individual_files: bool = True
    
    # Volume Suite Configuration
    volume_suite_enable: bool = True
    volume_suite_daily_enable: bool = True
    volume_suite_weekly_enable: bool = True
    volume_suite_monthly_enable: bool = True
    volume_suite_hv_absolute: bool = True
    volume_suite_hv_stdv: bool = True
    volume_suite_enhanced_anomaly: bool = True
    volume_suite_volume_indicators: bool = True
    volume_suite_pvb_clmodel_integration: bool = True
    
    # HV Absolute parameters
    volume_suite_hv_month_cutoff: int = 15
    volume_suite_hv_day_cutoff: int = 3
    volume_suite_hv_std_cutoff: int = 10
    volume_suite_hv_min_volume: int = 100000
    volume_suite_hv_min_price: float = 20.0
    
    # HV StdDev parameters
    volume_suite_stdv_cutoff: int = 12
    volume_suite_stdv_min_volume: int = 10000
    
    # Volume Indicators parameters
    volume_suite_vroc_threshold: float = 50.0
    volume_suite_rvol_threshold: float = 2.0
    volume_suite_rvol_extreme_threshold: float = 5.0
    volume_suite_mfi_overbought: int = 80
    volume_suite_mfi_oversold: int = 20
    volume_suite_vpt_threshold: float = 0.05
    volume_suite_adtv_3m_threshold: float = 2.0
    volume_suite_adtv_6m_threshold: float = 2.0
    volume_suite_adtv_1y_threshold: float = 2.0
    volume_suite_adtv_min_volume: int = 100000
    volume_suite_output_dir: str = "results/screeners/volume_suite"
    volume_suite_save_individual_files: bool = True

    # PVB ClModel Integration parameters (separate from PVB TW)
    volume_suite_pvb_clmodel_price_period: int = 15
    volume_suite_pvb_clmodel_volume_period: int = 15
    volume_suite_pvb_clmodel_trend_length: int = 50
    volume_suite_pvb_clmodel_volume_multiplier: float = 1.5
    volume_suite_pvb_clmodel_direction: str = "Long"

    # Stockbee Suite Configuration
    stockbee_suite_enable: bool = True
    stockbee_suite_daily_enable: bool = True
    stockbee_suite_weekly_enable: bool = False
    stockbee_suite_monthly_enable: bool = False
    stockbee_suite_9m_movers: bool = True
    stockbee_suite_weekly_movers: bool = True
    stockbee_suite_daily_gainers: bool = True
    stockbee_suite_industry_leaders: bool = True
    
    # Stockbee Suite parameters
    stockbee_suite_min_market_cap: int = 1000000000  # $1B
    stockbee_suite_min_price: float = 5.0
    stockbee_suite_exclude_funds: bool = True
    
    # 9M Movers parameters
    stockbee_suite_9m_volume_threshold: int = 9000000  # 9M shares
    stockbee_suite_9m_rel_vol_threshold: float = 1.25
    
    # Weekly Movers parameters
    stockbee_suite_weekly_gain_threshold: float = 20.0  # 20%
    stockbee_suite_weekly_rel_vol_threshold: float = 1.25
    stockbee_suite_weekly_min_avg_volume: int = 100000
    
    # Daily Gainers parameters
    stockbee_suite_daily_gain_threshold: float = 4.0  # 4%
    stockbee_suite_daily_rel_vol_threshold: float = 1.5
    stockbee_suite_daily_min_volume: int = 100000
    
    # Industry Leaders parameters
    stockbee_suite_industry_top_pct: float = 20.0  # Top 20% (stored as percentage)
    stockbee_suite_industry_top_stocks: int = 4  # Top 4 per industry
    stockbee_suite_industry_min_size: int = 3  # Minimum stocks per industry
    stockbee_suite_save_individual_files: bool = True  # Save individual screener files

    # Qullamaggie Suite Configuration
    qullamaggie_suite_enable: bool = True
    qullamaggie_suite_rs_threshold: float = 97.0  # Top 3% RS requirement
    qullamaggie_suite_atr_rs_threshold: float = 50.0  # Top 50% ATR requirement
    qullamaggie_suite_range_position_threshold: float = 0.5  # 50% of 20-day range
    qullamaggie_suite_min_market_cap: int = 1000000000  # $1B
    qullamaggie_suite_min_price: float = 5.0
    qullamaggie_suite_extension_warning: float = 7.0  # 7x ATR extension warning
    qullamaggie_suite_extension_danger: float = 11.0  # 11x ATR extension danger
    qullamaggie_suite_min_data_length: int = 250  # Minimum data for full analysis
    volume_suite_adtv_min_volume: int = 1000000
    
    # ADL Screener Configuration
    adl_screener_enable: bool = True
    adl_screener_daily_enable: bool = False
    adl_screener_weekly_enable: bool = False
    adl_screener_monthly_enable: bool = False

    # Base ADL calculation parameters (existing functionality)
    adl_screener_lookback_period: int = 50  # Period for ADL calculation and analysis
    adl_screener_divergence_period: int = 20  # Period to analyze for divergence patterns
    adl_screener_breakout_period: int = 30  # Period to check for ADL breakouts/breakdowns
    adl_screener_min_divergence_strength: float = 0.7  # Minimum divergence strength threshold
    adl_screener_min_breakout_strength: float = 1.2  # Minimum breakout strength threshold
    adl_screener_min_volume_avg: int = 100000  # Minimum average volume requirement
    adl_screener_min_price: float = 5.0  # Minimum stock price requirement
    adl_screener_save_individual_files: bool = True  # Save individual component files

    # Month-over-Month Accumulation Analysis (Step 2)
    adl_screener_mom_analysis_enable: bool = True
    adl_screener_mom_period: int = 22  # Trading days per month
    adl_screener_mom_min_threshold_pct: float = 15.0  # Minimum monthly growth percentage
    adl_screener_mom_max_threshold_pct: float = 30.0  # Maximum monthly growth percentage
    adl_screener_mom_consecutive_months: int = 3  # Minimum consecutive months meeting criteria
    adl_screener_mom_lookback_months: int = 6  # Total historical months to analyze
    adl_screener_mom_min_consistency_score: float = 60.0  # Minimum consistency score (0-100)

    # Short-term Momentum Analysis (Step 3)
    adl_screener_short_term_enable: bool = True
    adl_screener_short_term_periods: str = "5;10;20"  # Periods for percentage change calculation
    adl_screener_short_term_momentum_threshold: float = 5.0  # Minimum % change for momentum shift
    adl_screener_short_term_acceleration_detect: bool = True  # Enable acceleration detection
    adl_screener_short_term_min_score: float = 50.0  # Minimum momentum score (0-100)

    # Moving Average Analysis (Step 4)
    adl_screener_ma_enable: bool = True
    adl_screener_ma_periods: str = "20;50;100"  # MA periods (semicolon separated)
    adl_screener_ma_type: str = "SMA"  # Type: SMA or EMA
    adl_screener_ma_bullish_alignment_required: bool = True  # Require 20 > 50 > 100
    adl_screener_ma_crossover_detection: bool = True  # Detect MA crossovers
    adl_screener_ma_crossover_lookback: int = 10  # Periods to look back for crossovers
    adl_screener_ma_min_slope_threshold: float = 0.01  # Minimum positive slope
    adl_screener_ma_min_alignment_score: float = 70.0  # Minimum alignment score (0-100)

    # Composite Scoring and Ranking (Step 5)
    adl_screener_composite_scoring_enable: bool = True
    adl_screener_composite_weight_longterm: float = 0.4  # Weight for long-term accumulation
    adl_screener_composite_weight_shortterm: float = 0.3  # Weight for short-term momentum
    adl_screener_composite_weight_ma_align: float = 0.3  # Weight for MA alignment
    adl_screener_composite_min_score: float = 70.0  # Minimum composite score (0-100)
    adl_screener_ranking_method: str = "composite"  # Ranking method
    adl_screener_output_ranking_file: bool = True  # Generate ranked output file
    adl_screener_top_candidates_count: int = 50  # Number of top candidates to highlight

    # Output Configuration
    adl_screener_output_separate_signals: bool = True  # Separate files per signal type
    adl_screener_output_include_charts: bool = False  # Generate charts (future feature)
    adl_screener_output_summary_stats: bool = True  # Include summary statistics
    
    # Guppy GMMA Screener Configuration
    guppy_screener_enable: bool = True
    guppy_screener_daily_enable: bool = True
    guppy_screener_weekly_enable: bool = False
    guppy_screener_monthly_enable: bool = False
    guppy_screener_ma_type: str = "EMA"  # Moving average type: EMA or SMA
    guppy_screener_short_term_emas: List[int] = field(default_factory=lambda: [3, 5, 8, 10, 12, 15])  # Trader behavior EMAs
    guppy_screener_long_term_emas: List[int] = field(default_factory=lambda: [30, 35, 40, 45, 50, 60])  # Investor behavior EMAs
    guppy_screener_min_compression_ratio: float = 0.02  # 2% compression threshold
    guppy_screener_min_expansion_ratio: float = 0.05  # 5% expansion threshold
    guppy_screener_crossover_confirmation_days: int = 3  # Days to confirm crossover
    guppy_screener_volume_confirmation_threshold: float = 1.2  # Volume confirmation multiplier
    guppy_screener_min_price: float = 5.0  # Minimum stock price requirement
    guppy_screener_min_volume_avg: int = 100000  # Minimum average volume requirement
    guppy_screener_min_data_length: int = 65  # Minimum data length for analysis
    guppy_screener_save_individual_files: bool = True  # Save individual component files
    
    # GOLD LAUNCH PAD SCREENER CONFIGURATION
    gold_launch_pad_enable: bool = True
    gold_launch_pad_daily_enable: bool = True
    gold_launch_pad_weekly_enable: bool = True
    gold_launch_pad_monthly_enable: bool = True
    gold_launch_pad_ma_periods: List[int] = field(default_factory=lambda: [10, 20, 50])
    gold_launch_pad_ma_type: str = "EMA"  # EMA, SMA, WMA
    gold_launch_pad_zscore_window: int = 50
    gold_launch_pad_max_spread_threshold: float = 1.0
    gold_launch_pad_slope_lookback_pct: float = 0.3
    gold_launch_pad_min_slope_threshold: float = 0.0001
    gold_launch_pad_price_proximity_stdv: float = 2.0
    gold_launch_pad_proximity_window: int = 20
    gold_launch_pad_min_price: float = 5.0
    gold_launch_pad_min_volume: int = 100000
    gold_launch_pad_save_individual_files: bool = True
    
    # RANGE TIGHTENING INDICATOR (RTI) SCREENER CONFIGURATION
    rti_enable: bool = True
    rti_daily_enable: bool = True
    rti_weekly_enable: bool = False
    rti_monthly_enable: bool = False
    rti_period: int = 50
    rti_short_period: int = 5
    rti_swing_period: int = 15
    rti_zone1_threshold: float = 5.0
    rti_zone2_threshold: float = 10.0
    rti_zone3_threshold: float = 15.0
    rti_low_volatility_threshold: float = 20.0
    rti_expansion_multiplier: float = 2.0
    rti_consecutive_low_vol_bars: int = 2
    rti_min_consolidation_period: int = 3
    rti_breakout_confirmation_period: int = 2
    rti_min_price: float = 5.0
    rti_min_volume: int = 100000
    rti_save_individual_files: bool = True
    
    # PVB Integration parameters
    volume_suite_pvb_TWmodel_price_period: int = 30
    volume_suite_pvb_TWmodel_volume_period: int = 30
    volume_suite_pvb_TWmodel_trend_length: int = 50
    volume_suite_pvb_TWmodel_volume_multiplier: float = 1.5
    volume_suite_pvb_TWmodel_direction: str = "Long"
    
    # Output settings
    volume_suite_output_dir: str = "results/screeners/volume_suite"
    volume_suite_save_individual_files: bool = True
    
    # Performance optimization
    cap_history_data: int = 2
    
    # MARKET PULSE CONFIGURATION
    market_pulse_enable: bool = True
    market_pulse_gmi_index1: str = "SPY"  # Index1 for R3 (SPY daily analysis)
    market_pulse_gmi_index2: str = "QQQ"  # Index2 for R4 and R5 (QQQ daily analysis)
    
    # GMI Configuration
    market_pulse_gmi_enable: bool = True
    market_pulse_gmi_threshold: int = 3
    market_pulse_gmi_confirmation_days: int = 2
    market_pulse_gmi_short_term_sma: int = 50
    market_pulse_gmi_long_term_sma: int = 150
    market_pulse_gmi_mf_index: str = "SPY"
    market_pulse_gmi_mf_ma_period: int = 50
    market_pulse_gmi_breath_file_suffix: str = "latest"  # "latest" or specific date "YYYY-MM-DD"

    # GMI2 Configuration (Multi-SMA Requirements Model)
    market_pulse_gmi2_enable: bool = False
    market_pulse_gmi2_index: str = "SPY;QQQ"  # Multiple indexes separated by semicolon
    market_pulse_gmi2_sma: str = "10;20;50;150"  # Exactly 4 SMA values separated by semicolon
    market_pulse_gmi2_index_stochastic_threshold: int = 20
    market_pulse_gmi2_threshold: int = 5  # Out of 9 possible points
    market_pulse_gmi2_confirmation_days: int = 2
    
    # FTD & DD Configuration
    market_pulse_ftd_dd_enable: bool = True
    market_pulse_dd_threshold: float = 0.2  # 0.2% minimum decline for Distribution Day
    market_pulse_ftd_threshold: float = 1.5  # 1.5% minimum gain for Follow-Through Day
    market_pulse_ftd_optimal_days_min: int = 4
    market_pulse_ftd_optimal_days_max: int = 7
    market_pulse_dd_lookback_period: int = 25
    
    # Net New Highs/Lows Configuration
    market_pulse_net_highs_lows_enable: bool = True
    market_pulse_net_highs_lows_timeframes: List[str] = field(default_factory=lambda: ['52week', '3month', '1month'])
    market_pulse_breadth_threshold_healthy: float = 2.0  # >2% net new highs = healthy
    market_pulse_breadth_threshold_unhealthy: float = -2.0  # >2% net new lows = unhealthy
    
    # Chillax Moving Averages Configuration
    market_pulse_chillax_ma_enable: bool = True
    market_pulse_chillax_ma_fast_period: int = 10
    market_pulse_chillax_ma_slow_period: int = 20
    market_pulse_chillax_trend_days: int = 5  # Days to check for trend confirmation

    # Chillax MAs Enhanced Configuration
    market_pulse_chillax_mas_indexes: str = "SPY;QQQ;IWM"  # Chillax MA analysis indexes (semicolon separated)
    market_pulse_chillax_mas_sma: str = "10;20"  # Chillax MA SMA periods (semicolon separated)
    market_pulse_chillax_mas_charts: str = "SPY;QQQ"  # Indexes to create charts for (if empty creates for all chillax_mas_indexes)
    market_pulse_chillax_mas_charts_timeframe: int = 150  # Chart timeframe in trading days (150 daily = ~30 weeks)
    market_pulse_chillax_display_sma: str = "50;150;200"  # Additional moving averages to be displayed on chart
    
    # Moving Average Cycles Enhanced Configuration
    market_pulse_ma_cycles_enable: bool = True
    market_pulse_ma_cycles_indexes: str = "SPY;QQQ;IWM"  # MA Cycles analysis indexes (semicolon separated)
    market_pulse_ma_cycles_ma_period: str = "20;50"  # MA periods for cycle analysis (semicolon separated)
    market_pulse_ma_cycles_charts: str = "SPY;QQQ"  # Indexes to create charts for (if empty creates for all ma_cycles_indexes)
    market_pulse_ma_cycles_charts_timeframe: int = 200  # Chart timeframe in trading days
    market_pulse_ma_cycles_cycle_mode: str = "Sharp"  # Cycle detection mode (Sharp, Smooth, etc.)
    market_pulse_ma_cycles_smoothed_candles: int = 3  # Number of candles for smoothing

    # Legacy MA Cycles Configuration (for backward compatibility)
    market_pulse_ma_cycles_reference_period: int = 50
    market_pulse_ma_cycles_min_cycle_length: int = 5
    
    # Output Configuration
    market_pulse_output_dir: str = "results/market_pulse"
    market_pulse_save_detailed_results: bool = True
    market_pulse_generate_alerts: bool = True

    # Report Generation Configuration
    market_pulse_ftd_dd_report_enable: bool = False
    market_pulse_comprehensive_report_enable: bool = True
    
    # Market Breadth Analysis Configuration
    market_breadth_enable: bool = True
    market_breadth_daily_enable: bool = True
    market_breadth_weekly_enable: bool = False
    market_breadth_monthly_enable: bool = False
    market_breadth_universe: dict = field(default_factory=lambda: {
        'type': 'single',
        'universes': ['all'],
        'display_name': 'all',
        'file_count': 1,
        'raw_config': 'all'
    })
    market_breadth_lookback_days: int = 252
    market_breadth_ma_periods: List[int] = field(default_factory=lambda: [20, 50, 200])
    # 252-day threshold configuration
    market_breadth_daily_252day_new_highs_threshold: int = 100
    market_breadth_ten_day_success_threshold: int = 5
    # 20-day threshold configuration
    market_breadth_daily_20day_new_highs_threshold: int = 100
    market_breadth_twenty_day_success_threshold: int = 10
    # 63-day threshold configuration
    market_breadth_daily_63day_new_highs_threshold: int = 100
    market_breadth_sixty_three_day_success_threshold: int = 30
    # Advance/decline thresholds
    market_breadth_strong_ad_ratio_threshold: float = 2.0
    market_breadth_weak_ad_ratio_threshold: float = 0.5
    market_breadth_strong_advance_threshold: float = 70.0
    market_breadth_weak_advance_threshold: float = 30.0
    # Moving average breadth thresholds
    market_breadth_strong_ma_breadth_threshold: float = 80.0
    market_breadth_weak_ma_breadth_threshold: float = 20.0
    # Chart history display configuration (all represent 1 year in respective timeframes)
    market_breadth_chart_history_days: int = 252      # Daily charts: 252 days (1 year)
    market_breadth_chart_history_weeks: int = 52      # Weekly charts: 52 weeks (1 year)
    market_breadth_chart_history_months: int = 12     # Monthly charts: 12 months (1 year)
    # Output configuration
    market_breadth_save_detailed_results: bool = True
    market_breadth_output_dir: str = "results/market_breadth"
    
    # Dashboard Configuration
    dashboard_enable: bool = True
    dashboard_output_dir: str = "results/dashboards"
    dashboard_auto_refresh: bool = True
    dashboard_include_charts: bool = True
    dashboard_max_opportunities: int = 15
    dashboard_max_alerts: int = 10
    dashboard_save_historical: bool = True

    # HVE (Highest Volume Ever) Configuration
    hve_enable: bool = True
    hve_output_dir: str = "results/hve_results"
    hve_limit_years: int = 4
    hve_min_volume: int = 0
    hve_min_price: float = 0.0
    hve_date_range_mode: str = "fixed"  # 'rolling' or 'fixed'
    hve_start_date: str = "2020-01-01"  # Start date for fixed range mode
    hve_end_date: str = "2023-12-31"  # End date for fixed range mode
    hve_historical_max_events: int = 10  # Number of HVE events to export
    hve_historical_export: bool = True  # Enable HVE historical export
    hvd_historical_export: bool = True  # Enable HVD (Top Volume Days) historical export
    hvd_historical_max_days: int = 10  # Number of top volume days to export

    # HV1Y (Highest Volume in 1 Year) Configuration
    hv1y_enable: bool = True
    hv1y_window_days: int = 365


def _get_default_ticker_filenames() -> dict:
    """Get the default ticker filenames mapping."""
    return {
        0: 'tradingview_universe.csv',
        1: 'sp500_tickers.csv',
        2: 'nasdaq100_tickers.csv',
        3: 'nasdaq_all_tickers.csv',
        4: 'iwm1000_tickers.csv',
        5: 'indexes_tickers.csv',
        6: 'portofolio_tickers.csv',
        7: 'etf_tickers.csv',
        8: 'test_tickers.csv'
    }


def _read_ticker_filenames(file_path: str) -> dict:
    """
    Parse ticker group filenames from comment lines in the CSV file.
    
    Looks for lines in format: # N: Description,filename,
    where N is the group ID (0-8) and filename is the CSV filename.
    
    Returns dict mapping group_id -> filename
    """
    ticker_filenames = {}
    
    try:
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith('#') and ':' in line:
                    # Parse lines like: # 5: Index tickers only,indexes_tickers.csv,
                    parts = line.split(',')
                    if len(parts) >= 2:
                        # Extract the group ID from "# N: Description"
                        prefix_part = parts[0]  # "# 5: Index tickers only"
                        if ':' in prefix_part:
                            try:
                                # Split on ':' and get the part before it
                                before_colon = prefix_part.split(':')[0]  # "# 5"
                                # Extract the number
                                group_id = int(before_colon.replace('#', '').strip())
                                # Get the filename (second column)
                                filename = parts[1].strip()
                                if filename and 0 <= group_id <= 8:
                                    ticker_filenames[group_id] = filename
                            except (ValueError, IndexError):
                                continue  # Skip invalid lines
        
        # If no filenames found, use defaults
        if not ticker_filenames:
            ticker_filenames = _get_default_ticker_filenames()
            
    except FileNotFoundError:
        # Use defaults if file not found
        ticker_filenames = _get_default_ticker_filenames()
    
    return ticker_filenames


def parse_boolean(value: str) -> bool:
    """
    Parse string value to boolean.
    Accepts: TRUE, FALSE, true, false, 1, 0, yes, no
    """
    if isinstance(value, bool):
        return value

    value_str = str(value).strip().lower()
    return value_str in ['true', '1', 'yes', 'on']


def parse_comma_separated_ints(value: str) -> List[int]:
    """
    Parse comma-separated integer string to List[int].

    Examples:
        "3,5,8,10,12,25" → [3, 5, 8, 10, 12, 25]
        "30,35, 40, 45, 50, 60" → [30, 35, 40, 45, 50, 60] (handles spaces)

    Args:
        value: String with comma-separated integers

    Returns:
        List of integers, empty list if parsing fails
    """
    if not value or not isinstance(value, str):
        return []
    try:
        # Remove quotes if present, strip whitespace, split by comma
        cleaned = value.strip().strip('"\'')
        return [int(x.strip()) for x in cleaned.split(',') if x.strip()]
    except (ValueError, AttributeError) as e:
        logger.warning(f"Failed to parse comma-separated integers '{value}': {e}")
        return []


def read_user_data(file_path: str = 'user_data.csv') -> UserConfiguration:
    """
    Reads user configuration from the restructured CSV file.
    
    The new format uses key-value pairs with format:
    variable_name,value,description
    
    Returns UserConfiguration object with all settings.
    """
    try:
        # First, read ticker group filenames from comment lines
        ticker_filenames = _read_ticker_filenames(file_path)
        
        # Read CSV file, skipping comment lines that start with #
        df = pd.read_csv(file_path, comment='#', header=None, 
                        names=['variable', 'value', 'description'])
        
        # Remove rows where variable is NaN (empty lines, etc.)
        df = df.dropna(subset=['variable'])
        df['variable'] = df['variable'].str.strip()
        df['value'] = df['value'].str.strip()
        
        # Create configuration object with defaults
        config = UserConfiguration()
        config.ticker_filenames = ticker_filenames
        
        # Parse each configuration variable
        config_map = {
            # Original data collection settings (now mostly disabled)
            'WEB_tickers_down': ('web_tickers_down', parse_boolean),
            'TW_tickers_down': ('tw_tickers_down', parse_boolean),
            'TW_universe_file': ('tw_universe_file', str),
            'YF_hist_data': ('yf_hist_data', parse_boolean),
            'YF_daily_data': ('yf_daily_data', parse_boolean),
            'YF_weekly_data': ('yf_weekly_data', parse_boolean),
            'YF_monthly_data': ('yf_monthly_data', parse_boolean),
            'TW_intraday_data': ('tw_intraday_data', parse_boolean),
            'TW_intraday_file': ('tw_intraday_file', str),
            'fin_data_enrich': ('fin_data_enrich', parse_boolean),
            'YF_fin_data': ('yf_fin_data', parse_boolean),
            'TW_fin_data': ('tw_fin_data', parse_boolean),
            'Zacks_fin_data': ('zacks_fin_data', parse_boolean),
            'write_info_file': ('write_info_file', parse_boolean),
            'ticker_info_TW': ('ticker_info_TW', parse_boolean),
            'ticker_info_TW_file': ('ticker_info_TW_file', str),
            'ticker_info_YF': ('ticker_info_YF', parse_boolean),
            'ticker_choice': ('ticker_choice', str),
            'batch_size': ('batch_size', int),

            # Global execution phase flags
            'PRE_PROCESS': ('PRE_PROCESS', parse_boolean),
            'PRE_PROCESS_file': ('PRE_PROCESS_file', str),
            'BASIC': ('BASIC', parse_boolean),
            'SCREENERS': ('SCREENERS', parse_boolean),
            'POST_PROCESS': ('POST_PROCESS', parse_boolean),
            'BACKTESTING': ('BACKTESTING', parse_boolean),

            # POST-PROCESSING CONFIGURATION
            # Input historical data sources (local data loading)
            'YF_daily_data_files': ('yf_daily_data_files', str),
            'YF_weekly_data_files': ('yf_weekly_data_files', str),
            'YF_monthly_data_files': ('yf_monthly_data_files', str),
            'TW_intraday_folder': ('tw_intraday_folder', str),

            # Environment detection and paths
            'auto_detect_environment': ('auto_detect_environment', parse_boolean),
            'manual_environment_override': ('manual_environment_override', str),

            # Local environment paths
            'YF_daily_data_files_local': ('yf_daily_data_files_local', str),
            'YF_weekly_data_files_local': ('yf_weekly_data_files_local', str),
            'YF_monthly_data_files_local': ('yf_monthly_data_files_local', str),
            'TW_intraday_folder_local': ('tw_intraday_folder_local', str),

            # Colab environment paths
            'YF_daily_data_files_colab': ('yf_daily_data_files_colab', str),
            'YF_weekly_data_files_colab': ('yf_weekly_data_files_colab', str),
            'YF_monthly_data_files_colab': ('yf_monthly_data_files_colab', str),
            'TW_intraday_folder_colab': ('tw_intraday_folder_colab', str),
            
            # Overview files
            'indexes_overview_file': ('indexes_overview_file', str),
            
            # Index Overview Configuration
            'SP500_overview': ('sp500_overview', parse_boolean),
            'NASDAQ100_overview': ('nasdaq100_overview', parse_boolean),
            'DJIA_overview': ('djia_overview', parse_boolean),
            
            # Index Period Configurations
            'index_daily_daily_periods': ('index_daily_daily_periods', str),
            'index_daily_weekly_periods': ('index_daily_weekly_periods', str),
            'index_daily_monthly_periods': ('index_daily_monthly_periods', str),
            'index_daily_quarterly_periods': ('index_daily_quarterly_periods', str),
            'index_daily_yearly_periods': ('index_daily_yearly_periods', str),
            
            # Output directory configuration
            'BASIC_CALCULATION_output_dir': ('basic_calculation_output_dir', str),
            'STAGE_ANALYSIS_output_dir': ('stage_analysis_output_dir', str),
            'RS_output_dir': ('rs_output_dir', str),
            'PER_output_dir': ('per_output_dir', str),
            # Screener output directories
            'PVB_TWmodel_output_dir': ('pvb_TWmodel_output_dir', str),
            'ATR1_output_dir': ('atr1_output_dir', str),
            'DRWISH_output_dir': ('drwish_output_dir', str),
            'GIUSTI_output_dir': ('giusti_output_dir', str),
            'MINERVINI_output_dir': ('minervini_output_dir', str),
            'STOCKBEE_output_dir': ('stockbee_output_dir', str),
            'QULLAMAGGIE_output_dir': ('qullamaggie_output_dir', str),
            'ADL_SCREENER_output_dir': ('adl_screener_output_dir', str),
            'GUPPY_SCREENER_output_dir': ('guppy_screener_output_dir', str),
            'GOLD_LAUNCH_PAD_output_dir': ('gold_launch_pad_output_dir', str),
            'RTI_output_dir': ('rti_output_dir', str),

            # Basic calculations (legacy)
            'Basic_calculation_file': ('basic_calculation_file', str),
            'Basic_calc_daily_enable': ('basic_calc_daily_enable', parse_boolean),
            'Basic_calc_weekly_enable': ('basic_calc_weekly_enable', parse_boolean),
            'Basic_calc_monthly_enable': ('basic_calc_monthly_enable', parse_boolean),
            # Daily period percent change configuration
            'daily_daily_periods': ('daily_daily_periods', str),
            'daily_weekly_periods': ('daily_weekly_periods', str),
            'daily_monthly_periods': ('daily_monthly_periods', str),
            'daily_quarterly_periods': ('daily_quarterly_periods', str),
            'daily_yearly_periods': ('daily_yearly_periods', str),
            # Weekly period percent change configuration
            'weekly_weekly_periods': ('weekly_weekly_periods', str),
            'weekly_monthly_periods': ('weekly_monthly_periods', str),
            # Monthly period percent change configuration
            'monthly_monthly_periods': ('monthly_monthly_periods', str),
            # Monthly RS periods
            'RS_monthly_periods': ('RS_monthly_periods', str),

            # SUSTAINABILITY RATIOS (SR) CONFIGURATION
            'SR_enable': ('sr_enable', parse_boolean),
            'SR_output_dir': ('sr_output_dir', str),
            # SUBMODULE CONTROL FLAGS
            'SR_panels_enable': ('sr_panels_enable', parse_boolean),
            'SR_overview_enable': ('sr_overview_enable', parse_boolean),
            'SR_intermarket_enable': ('sr_intermarket_enable', parse_boolean),
            'SR_breadth_enable': ('sr_breadth_enable', parse_boolean),
            # PANEL SUBMODULE CONFIGURATION
            'SR_panel_config_file': ('sr_panel_config_file', str),
            'SR_timeframes': ('sr_timeframes', str),
            # New granular timeframe controls
            'SR_timeframe_daily': ('sr_timeframe_daily', parse_boolean),
            'SR_timeframe_weekly': ('sr_timeframe_weekly', parse_boolean),
            'SR_timeframe_monthly': ('sr_timeframe_monthly', parse_boolean),
            # OVERVIEW SUBMODULE CONFIGURATION
            'SR_overview_values_enable': ('sr_overview_values_enable', parse_boolean),
            'SR_overview_charts_enable': ('sr_overview_charts_enable', parse_boolean),
            'SR_overview_values_history': ('sr_overview_values_history', int),
            'SR_overview_values_indexes': ('sr_overview_values_indexes', str),
            'SR_overview_values_sectors': ('sr_overview_values_sectors', str),
            'SR_overview_values_industries': ('sr_overview_values_industries', str),
            'SR_overview_values_timeframe': ('sr_overview_values_timeframe', str),
            'SR_overview_output_dir': ('sr_overview_output_dir', str),
            'SR_overview_filename_prefix': ('sr_overview_filename_prefix', str),
            'SR_overview_charts_tickers': ('sr_overview_charts_tickers', str),
            'SR_overview_charts_display_panel': ('sr_overview_charts_display_panel', str),
            'SR_overview_charts_display_history': ('sr_overview_charts_display_history', int),
            # Chart display range control
            'SR_chart_display': ('sr_chart_display', int),
            'SR_chart_generation': ('sr_chart_generation', parse_boolean),
            'SR_intermarket_ratios': ('sr_intermarket_ratios', parse_boolean),
            'SR_market_breadth': ('sr_market_breadth', parse_boolean),
            'SR_save_detailed_results': ('sr_save_detailed_results', parse_boolean),
            'SR_dashboard_style': ('sr_dashboard_style', str),
            'SR_lookback_days': ('sr_lookback_days', int),

            # MMM SUBMODULE CONFIGURATION
            'SR_mmm_enable': ('sr_mmm_enable', parse_boolean),
            'SR_mmm_daily_enable': ('sr_mmm_daily_enable', parse_boolean),
            'SR_mmm_weekly_enable': ('sr_mmm_weekly_enable', parse_boolean),
            'SR_mmm_monthly_enable': ('sr_mmm_monthly_enable', parse_boolean),
            'SR_mmm_gaps_values': ('sr_mmm_gaps_values', parse_boolean),
            'SR_mmm_gaps_tickers': ('sr_mmm_gaps_tickers', str),
            'SR_mmm_gaps_values_input_folder_daily': ('sr_mmm_gaps_values_input_folder_daily', str),
            'SR_mmm_gaps_values_input_folder_weekly': ('sr_mmm_gaps_values_input_folder_weekly', str),
            'SR_mmm_gaps_values_input_folder_monthly': ('sr_mmm_gaps_values_input_folder_monthly', str),
            'SR_mmm_gaps_values_output_folder_daily': ('sr_mmm_gaps_values_output_folder_daily', str),
            'SR_mmm_gaps_values_output_folder_weekly': ('sr_mmm_gaps_values_output_folder_weekly', str),
            'SR_mmm_gaps_values_output_folder_monthly': ('sr_mmm_gaps_values_output_folder_monthly', str),
            'SR_mmm_gaps_values_filename_suffix': ('sr_mmm_gaps_values_filename_suffix', str),
            'SR_mmm_gaps_chart_enable': ('sr_mmm_gaps_chart_enable', parse_boolean),
            'SR_mmm_gaps_charts_display_panel': ('sr_mmm_gaps_charts_display_panel', str),
            'SR_mmm_gaps_charts_display_history': ('sr_mmm_gaps_charts_display_history', int),
            'SR_mmm_output_dir': ('sr_mmm_output_dir', str),

            # Screeners
            'screener_output_file': ('screener_output_file', str),
            'screener_criteria_file': ('screener_criteria_file', str),
            
            # Models
            'models_output_file': ('models_output_file', str),
            'models_config_file': ('models_config_file', str),
            
            # Database configuration removed
            
            # PDF reports configuration
            'pdf_reports_enable': ('pdf_reports_enable', parse_boolean),
            'pdf_reports_output_dir': ('pdf_reports_output_dir', str),
            'pdf_reports_include_charts': ('pdf_reports_include_charts', parse_boolean),
            
            # Report generation configuration
            'REPORT_enable': ('report_enable', parse_boolean),
            'REPORT_template_type': ('report_template_type', str),
            'REPORT_page_size': ('report_page_size', str),
            'REPORT_output_dir': ('report_output_dir', str),
            'REPORT_include_charts': ('report_include_charts', parse_boolean),
            'REPORT_file_dates_auto': ('report_file_dates_auto', parse_boolean),
            'REPORT_file_dates_manual': ('report_file_dates_manual', str),
            'REPORT_sections_basic_stats': ('report_sections_basic_stats', parse_boolean),
            'REPORT_sections_percentage_analysis': ('report_sections_percentage_analysis', parse_boolean),
            'REPORT_sections_rs_analysis': ('report_sections_rs_analysis', parse_boolean),
            'REPORT_sections_tornado_charts': ('report_sections_tornado_charts', parse_boolean),
            'REPORT_sections_summary': ('report_sections_summary', parse_boolean),
            'REPORT_max_tickers_display': ('report_max_tickers_display', int),
            'REPORT_format': ('report_format', str),
            'REPORT_include_metadata': ('report_include_metadata', parse_boolean),

            # Market Breadth Report Configuration (Independent of global REPORT_ settings)
            'MARKET_BREADTH_REPORT_enable': ('market_breadth_report_enable', parse_boolean),
            'MARKET_BREADTH_REPORT_template_type': ('market_breadth_report_template_type', str),
            'MARKET_BREADTH_force_file': ('market_breadth_force_file', parse_boolean),

            # Market Pulse GMI/GMI2 Report Configuration
            'MARKET_PULSE_GMIGMI2_REPORT_enable': ('market_pulse_gmigmi2_report_enable', parse_boolean),

            # Technical Indicators Configuration
            'daily_ema_periods': ('daily_ema_periods', str),
            'daily_sma_periods': ('daily_sma_periods', str),
            'weekly_ema_periods': ('weekly_ema_periods', str),
            'weekly_sma_periods': ('weekly_sma_periods', str),
            'monthly_ema_periods': ('monthly_ema_periods', str),
            'monthly_sma_periods': ('monthly_sma_periods', str),
            
            # Percentage Movers Configuration
            'enable_movers_analysis': ('enable_movers_analysis', parse_boolean),
            'daily_pct_threshold': ('daily_pct_threshold', float),
            'weekly_pct_threshold': ('weekly_pct_threshold', float),
            'movers_output_dir': ('movers_output_dir', str),
            'movers_min_volume': ('movers_min_volume', int),
            'movers_top_n': ('movers_top_n', int),
            
            # ATR Configuration
            'enable_atr_calculation': ('enable_atr_calculation', parse_boolean),
            'atr_period': ('atr_period', int),
            'atr_sma_period': ('atr_sma_period', int),
            'enable_atr_percentile': ('enable_atr_percentile', parse_boolean),
            'atr_percentile_period': ('atr_percentile_period', int),
            
            # ATR Screener Configuration
            # ATR1 (TradingView-validated)
            'ATR1_enable': ('atr1_enable', parse_boolean),
            'ATR1_daily_length': ('atr1_daily_length', int),
            'ATR1_daily_factor': ('atr1_daily_factor', float),
            'ATR1_daily_length2': ('atr1_daily_length2', int),
            'ATR1_daily_factor2': ('atr1_daily_factor2', float),
            'ATR1_weekly_length': ('atr1_weekly_length', int),
            'ATR1_weekly_factor': ('atr1_weekly_factor', float),
            'ATR1_weekly_length2': ('atr1_weekly_length2', int),
            'ATR1_weekly_factor2': ('atr1_weekly_factor2', float),
            'ATR1_monthly_length': ('atr1_monthly_length', int),
            'ATR1_monthly_factor': ('atr1_monthly_factor', float),
            'ATR1_monthly_length2': ('atr1_monthly_length2', int),
            'ATR1_monthly_factor2': ('atr1_monthly_factor2', float),
            
            # ATR2 (Volatility analysis)
            'ATR2_enable': ('atr2_enable', parse_boolean),
            'ATR2_daily_atr_period': ('atr2_daily_atr_period', int),
            'ATR2_daily_sma_period': ('atr2_daily_sma_period', int),
            'ATR2_daily_percentile_period': ('atr2_daily_percentile_period', int),
            'ATR2_weekly_atr_period': ('atr2_weekly_atr_period', int),
            'ATR2_weekly_sma_period': ('atr2_weekly_sma_period', int),
            'ATR2_weekly_percentile_period': ('atr2_weekly_percentile_period', int),
            'ATR2_monthly_atr_period': ('atr2_monthly_atr_period', int),
            'ATR2_monthly_sma_period': ('atr2_monthly_sma_period', int),
            'ATR2_monthly_percentile_period': ('atr2_monthly_percentile_period', int),
            
            # Stage Analysis Configuration - Global
            'enable_stage_analysis': ('enable_stage_analysis', parse_boolean),

            # Stage Analysis Configuration - Daily
            'stage_analysis_daily_enabled': ('stage_analysis_daily_enabled', parse_boolean),
            'stage_daily_ema_fast_period': ('stage_daily_ema_fast_period', int),
            'stage_daily_sma_medium_period': ('stage_daily_sma_medium_period', int),
            'stage_daily_sma_slow_period': ('stage_daily_sma_slow_period', int),
            'stage_daily_atr_period': ('stage_daily_atr_period', int),
            'stage_daily_atr_threshold_low': ('stage_daily_atr_threshold_low', float),
            'stage_daily_atr_threshold_high': ('stage_daily_atr_threshold_high', float),
            'stage_daily_ma_convergence_threshold': ('stage_daily_ma_convergence_threshold', float),
            
            # Stage Analysis Configuration - Weekly
            'stage_analysis_weekly_enabled': ('stage_analysis_weekly_enabled', parse_boolean),
            'stage_weekly_ema_fast_period': ('stage_weekly_ema_fast_period', int),
            'stage_weekly_sma_medium_period': ('stage_weekly_sma_medium_period', int),
            'stage_weekly_sma_slow_period': ('stage_weekly_sma_slow_period', int),
            'stage_weekly_atr_period': ('stage_weekly_atr_period', int),
            'stage_weekly_atr_threshold_low': ('stage_weekly_atr_threshold_low', float),
            'stage_weekly_atr_threshold_high': ('stage_weekly_atr_threshold_high', float),
            'stage_weekly_ma_convergence_threshold': ('stage_weekly_ma_convergence_threshold', float),
            
            # Stage Analysis Configuration - Monthly
            'stage_analysis_monthly_enabled': ('stage_analysis_monthly_enabled', parse_boolean),
            'stage_monthly_ema_fast_period': ('stage_monthly_ema_fast_period', int),
            'stage_monthly_sma_medium_period': ('stage_monthly_sma_medium_period', int),
            'stage_monthly_sma_slow_period': ('stage_monthly_sma_slow_period', int),
            'stage_monthly_atr_period': ('stage_monthly_atr_period', int),
            'stage_monthly_atr_threshold_low': ('stage_monthly_atr_threshold_low', float),
            'stage_monthly_atr_threshold_high': ('stage_monthly_atr_threshold_high', float),
            'stage_monthly_ma_convergence_threshold': ('stage_monthly_ma_convergence_threshold', float),
            
            # Legacy Stage Analysis Configuration (deprecated)
            'stage_analysis_enabled': ('stage_analysis_enabled', parse_boolean),
            'stage_analysis_min_price': ('stage_analysis_min_price', float),
            'stage_analysis_min_vol': ('stage_analysis_min_vol', int),
            'stage_analysis_report_enable': ('stage_analysis_report_enable', parse_boolean),
            'stage_ema_fast_period': ('stage_ema_fast_period', int),
            'stage_sma_medium_period': ('stage_sma_medium_period', int),
            'stage_sma_slow_period': ('stage_sma_slow_period', int),
            'stage_atr_period': ('stage_atr_period', int),
            'stage_atr_threshold_low': ('stage_atr_threshold_low', float),
            'stage_atr_threshold_high': ('stage_atr_threshold_high', float),
            'stage_ma_convergence_threshold': ('stage_ma_convergence_threshold', float),
            
            # Relative Strength Configuration
            'RS_enable_stocks': ('rs_enable_stocks', parse_boolean),
            'RS_enable_sectors': ('rs_enable_sectors', parse_boolean),
            'RS_enable_industries': ('rs_enable_industries', parse_boolean),
            # Multi-benchmark configuration
            'RS_benchmark_tickers': ('rs_benchmark_tickers', str),
            # Legacy single benchmark
            'RS_benchmark_ticker': ('rs_benchmark_ticker', str),
            'RS_composite_method': ('rs_composite_method', str),
            'RS_output_dir': ('rs_output_dir', str),
            'RS_min_group_size': ('rs_min_group_size', int),
            # Percentile universe configurations
            'RS_percentile_universe_stocks': ('rs_percentile_universe_stocks', str),
            'RS_percentile_universe_sectors': ('rs_percentile_universe_sectors', str),
            'RS_percentile_universe_industries': ('rs_percentile_universe_industries', str),

            # New mapping-based percentile configuration
            'RS_percentile_mapping_stocks': ('rs_percentile_mapping_stocks', str),
            'RS_percentile_mapping_sectors': ('rs_percentile_mapping_sectors', str),
            'RS_percentile_mapping_industries': ('rs_percentile_mapping_industries', str),
            # Daily timeframe parameters
            'RS_daily_enable': ('rs_daily_enable', parse_boolean),
            # Weekly timeframe parameters
            'RS_weekly_enable': ('rs_weekly_enable', parse_boolean),
            # Monthly timeframe parameters
            'RS_monthly_enable': ('rs_monthly_enable', parse_boolean),

            # Moving Average RS Configuration
            'RS_ma_enable': ('rs_ma_enable', parse_boolean),
            'RS_ma_method': ('rs_ma_method', str),
            'RS_method_for_PER': ('rs_method_for_per', str),

            # Technical Indicators Configuration
            'INDICATORS_enable': ('indicators_enable', parse_boolean),
            'INDICATORS_config_file': ('indicators_config_file', str),
            'INDICATORS_output_dir': ('indicators_output_dir', str),
            'INDICATORS_charts_dir': ('indicators_charts_dir', str),
            
            # Default Indicator Parameters
            'INDICATORS_kurutoga_enable': ('indicators_kurutoga_enable', parse_boolean),
            'INDICATORS_kurutoga_length': ('indicators_kurutoga_length', int),
            'INDICATORS_kurutoga_source': ('indicators_kurutoga_source', str),
            
            'INDICATORS_tsi_enable': ('indicators_tsi_enable', parse_boolean),
            'INDICATORS_tsi_fast': ('indicators_tsi_fast', int),
            'INDICATORS_tsi_slow': ('indicators_tsi_slow', int),
            'INDICATORS_tsi_signal': ('indicators_tsi_signal', int),
            
            'INDICATORS_macd_enable': ('indicators_macd_enable', parse_boolean),
            'INDICATORS_macd_fast': ('indicators_macd_fast', int),
            'INDICATORS_macd_slow': ('indicators_macd_slow', int),
            'INDICATORS_macd_signal': ('indicators_macd_signal', int),
            
            'INDICATORS_mfi_enable': ('indicators_mfi_enable', parse_boolean),
            'INDICATORS_mfi_length': ('indicators_mfi_length', int),
            'INDICATORS_mfi_signal_enable': ('indicators_mfi_signal_enable', parse_boolean),
            'INDICATORS_mfi_signal_period': ('indicators_mfi_signal_period', int),
            
            'INDICATORS_cog_enable': ('indicators_cog_enable', parse_boolean),
            'INDICATORS_cog_length': ('indicators_cog_length', int),
            'INDICATORS_cog_source': ('indicators_cog_source', str),
            
            'INDICATORS_momentum_enable': ('indicators_momentum_enable', parse_boolean),
            'INDICATORS_momentum_length': ('indicators_momentum_length', int),
            
            'INDICATORS_rsi_enable': ('indicators_rsi_enable', parse_boolean),
            'INDICATORS_rsi_length': ('indicators_rsi_length', int),
            
            'INDICATORS_ma_crosses_enable': ('indicators_ma_crosses_enable', parse_boolean),
            'INDICATORS_ma_fast_period': ('indicators_ma_fast_period', int),
            'INDICATORS_ma_slow_period': ('indicators_ma_slow_period', int),
            
            'INDICATORS_easy_trade_enable': ('indicators_easy_trade_enable', parse_boolean),
            'INDICATORS_easy_trade_fast': ('indicators_easy_trade_fast', int),
            'INDICATORS_easy_trade_slow': ('indicators_easy_trade_slow', int),
            'INDICATORS_easy_trade_signal': ('indicators_easy_trade_signal', int),
            
            # Basic Screeners Configuration
            'BASIC_momentum_enable': ('basic_momentum_enable', parse_boolean),
            'BASIC_breakout_enable': ('basic_breakout_enable', parse_boolean),
            'BASIC_value_momentum_enable': ('basic_value_momentum_enable', parse_boolean),
            
            # PVB (Price Volume Breakout) Configuration
            'PVB_TWmodel_enable': ('pvb_TWmodel_enable', parse_boolean),
            'PVB_TWmodel_daily_enable': ('pvb_TWmodel_daily_enable', parse_boolean),
            'PVB_TWmodel_weekly_enable': ('pvb_TWmodel_weekly_enable', parse_boolean),
            'PVB_TWmodel_monthly_enable': ('pvb_TWmodel_monthly_enable', parse_boolean),
            # Daily timeframe PVB parameters
            'PVB_TWmodel_daily_price_breakout_period': ('pvb_TWmodel_daily_price_breakout_period', int),
            'PVB_TWmodel_daily_volume_breakout_period': ('pvb_TWmodel_daily_volume_breakout_period', int),
            'PVB_TWmodel_daily_trendline_length': ('pvb_TWmodel_daily_trendline_length', int),
            'PVB_TWmodel_daily_close_threshold': ('pvb_TWmodel_daily_close_threshold', int),
            'PVB_TWmodel_daily_signal_max_age': ('pvb_TWmodel_daily_signal_max_age', int),
            # Weekly timeframe PVB parameters
            'PVB_TWmodel_weekly_price_breakout_period': ('pvb_TWmodel_weekly_price_breakout_period', int),
            'PVB_TWmodel_weekly_volume_breakout_period': ('pvb_TWmodel_weekly_volume_breakout_period', int),
            'PVB_TWmodel_weekly_trendline_length': ('pvb_TWmodel_weekly_trendline_length', int),
            'PVB_TWmodel_weekly_close_threshold': ('pvb_TWmodel_weekly_close_threshold', int),
            'PVB_TWmodel_weekly_signal_max_age': ('pvb_TWmodel_weekly_signal_max_age', int),
            # Monthly timeframe PVB parameters
            'PVB_TWmodel_monthly_price_breakout_period': ('pvb_TWmodel_monthly_price_breakout_period', int),
            'PVB_TWmodel_monthly_volume_breakout_period': ('pvb_TWmodel_monthly_volume_breakout_period', int),
            'PVB_TWmodel_monthly_trendline_length': ('pvb_TWmodel_monthly_trendline_length', int),
            'PVB_TWmodel_monthly_close_threshold': ('pvb_TWmodel_monthly_close_threshold', int),
            'PVB_TWmodel_monthly_signal_max_age': ('pvb_TWmodel_monthly_signal_max_age', int),
            # Common PVB parameters
            'PVB_TWmodel_order_direction': ('pvb_TWmodel_order_direction', str),
            'PVB_TWmodel_min_volume': ('pvb_TWmodel_min_volume', int),
            'PVB_TWmodel_min_price': ('pvb_TWmodel_min_price', float),
            # TradingView Watchlist Export Configuration
            'PVB_TWmodel_export_tradingview': ('pvb_TWmodel_export_tradingview', parse_boolean),
            'PVB_TWmodel_watchlist_max_symbols': ('pvb_TWmodel_watchlist_max_symbols', int),
            'PVB_TWmodel_watchlist_include_buy': ('pvb_TWmodel_watchlist_include_buy', parse_boolean),
            'PVB_TWmodel_watchlist_include_sell': ('pvb_TWmodel_watchlist_include_sell', parse_boolean),

            # Minervini Template Screener Configuration
            'MINERVINI_enable': ('minervini_enable', parse_boolean),
            'MINERVINI_rs_min_rating': ('minervini_rs_min_rating', float),
            'MINERVINI_min_volume': ('minervini_min_volume', int),
            'MINERVINI_min_price': ('minervini_min_price', float),
            'MINERVINI_show_all_stocks': ('minervini_show_all_stocks', parse_boolean),
            
            # Giusti Momentum Screener Configuration
            'GIUSTI_enable': ('giusti_enable', parse_boolean),
            'GIUSTI_min_price': ('giusti_min_price', float),
            'GIUSTI_min_volume': ('giusti_min_volume', int),
            'GIUSTI_rolling_12m': ('giusti_rolling_12m', int),
            'GIUSTI_rolling_6m': ('giusti_rolling_6m', int),
            'GIUSTI_rolling_3m': ('giusti_rolling_3m', int),
            'GIUSTI_top_12m_count': ('giusti_top_12m_count', int),
            'GIUSTI_top_6m_count': ('giusti_top_6m_count', int),
            'GIUSTI_top_3m_count': ('giusti_top_3m_count', int),
            'GIUSTI_min_history_months': ('giusti_min_history_months', int),
            'GIUSTI_show_all_stocks': ('giusti_show_all_stocks', parse_boolean),
            
            # Dr. Wish Suite Screener Configuration
            'DRWISH_enable': ('drwish_enable', parse_boolean),
            'DRWISH_min_price': ('drwish_min_price', float),
            'DRWISH_min_volume': ('drwish_min_volume', int),
            'DRWISH_pivot_strength': ('drwish_pivot_strength', int),
            'DRWISH_lookback_period': ('drwish_lookback_period', str),
            'DRWISH_confirmation_period': ('drwish_confirmation_period', str),
            'DRWISH_require_confirmation': ('drwish_require_confirmation', parse_boolean),
            'DRWISH_enable_glb': ('drwish_enable_glb', parse_boolean),
            'DRWISH_enable_blue_dot': ('drwish_enable_blue_dot', parse_boolean),
            'DRWISH_enable_black_dot': ('drwish_enable_black_dot', parse_boolean),
            'DRWISH_blue_dot_stoch_period': ('drwish_blue_dot_stoch_period', int),
            'DRWISH_blue_dot_stoch_threshold': ('drwish_blue_dot_stoch_threshold', float),
            'DRWISH_blue_dot_sma_period': ('drwish_blue_dot_sma_period', int),
            'DRWISH_black_dot_stoch_period': ('drwish_black_dot_stoch_period', int),
            'DRWISH_black_dot_stoch_threshold': ('drwish_black_dot_stoch_threshold', float),
            'DRWISH_black_dot_lookback': ('drwish_black_dot_lookback', int),
            'DRWISH_black_dot_sma_period': ('drwish_black_dot_sma_period', int),
            'DRWISH_black_dot_ema_period': ('drwish_black_dot_ema_period', int),
            'DRWISH_show_all_stocks': ('drwish_show_all_stocks', parse_boolean),
            'DRWISH_enable_charts': ('drwish_enable_charts', parse_boolean),
            'DRWISH_chart_output_dir': ('drwish_chart_output_dir', str),
            
            # Volume Suite Configuration
            'VOLUME_SUITE_enable': ('volume_suite_enable', parse_boolean),
            'VOLUME_SUITE_daily_enable': ('volume_suite_daily_enable', parse_boolean),
            'VOLUME_SUITE_weekly_enable': ('volume_suite_weekly_enable', parse_boolean),
            'VOLUME_SUITE_monthly_enable': ('volume_suite_monthly_enable', parse_boolean),
            'VOLUME_SUITE_hv_absolute': ('volume_suite_hv_absolute', parse_boolean),
            'VOLUME_SUITE_hv_stdv': ('volume_suite_hv_stdv', parse_boolean),
            'VOLUME_SUITE_enhanced_anomaly': ('volume_suite_enhanced_anomaly', parse_boolean),
            'VOLUME_SUITE_volume_indicators': ('volume_suite_volume_indicators', parse_boolean),
            'VOLUME_SUITE_pvb_Clmodel_integration': ('volume_suite_pvb_clmodel_integration', parse_boolean),
            'VOLUME_SUITE_hv_month_cutoff': ('volume_suite_hv_month_cutoff', int),
            'VOLUME_SUITE_hv_day_cutoff': ('volume_suite_hv_day_cutoff', int),
            'VOLUME_SUITE_hv_std_cutoff': ('volume_suite_hv_std_cutoff', int),
            'VOLUME_SUITE_hv_min_volume': ('volume_suite_hv_min_volume', int),
            'VOLUME_SUITE_hv_min_price': ('volume_suite_hv_min_price', float),
            'VOLUME_SUITE_stdv_cutoff': ('volume_suite_stdv_cutoff', int),
            'VOLUME_SUITE_stdv_min_volume': ('volume_suite_stdv_min_volume', int),
            'VOLUME_SUITE_vroc_threshold': ('volume_suite_vroc_threshold', int),
            'VOLUME_SUITE_rvol_threshold': ('volume_suite_rvol_threshold', float),
            'VOLUME_SUITE_rvol_extreme_threshold': ('volume_suite_rvol_extreme_threshold', float),
            'VOLUME_SUITE_mfi_overbought': ('volume_suite_mfi_overbought', int),
            'VOLUME_SUITE_mfi_oversold': ('volume_suite_mfi_oversold', int),
            'VOLUME_SUITE_vpt_threshold': ('volume_suite_vpt_threshold', float),
            'VOLUME_SUITE_adtv_3m_threshold': ('volume_suite_adtv_3m_threshold', float),
            'VOLUME_SUITE_adtv_6m_threshold': ('volume_suite_adtv_6m_threshold', float),
            'VOLUME_SUITE_adtv_1y_threshold': ('volume_suite_adtv_1y_threshold', float),
            'VOLUME_SUITE_adtv_min_volume': ('volume_suite_adtv_min_volume', int),
            'VOLUME_SUITE_output_dir': ('volume_suite_output_dir', str),
            'VOLUME_SUITE_save_individual_files': ('volume_suite_save_individual_files', parse_boolean),
            'VOLUME_SUITE_pvb_Clmodel_price_period': ('volume_suite_pvb_clmodel_price_period', int),
            'VOLUME_SUITE_pvb_Clmodel_volume_period': ('volume_suite_pvb_clmodel_volume_period', int),
            'VOLUME_SUITE_pvb_Clmodel_trend_length': ('volume_suite_pvb_clmodel_trend_length', int),
            'VOLUME_SUITE_pvb_Clmodel_volume_multiplier': ('volume_suite_pvb_clmodel_volume_multiplier', float),
            'VOLUME_SUITE_pvb_Clmodel_direction': ('volume_suite_pvb_clmodel_direction', str),
            
            # Stockbee Suite Configuration
            'STOCKBEE_SUITE_enable': ('stockbee_suite_enable', parse_boolean),
            'STOCKBEE_SUITE_daily_enable': ('stockbee_suite_daily_enable', parse_boolean),
            'STOCKBEE_SUITE_weekly_enable': ('stockbee_suite_weekly_enable', parse_boolean),
            'STOCKBEE_SUITE_monthly_enable': ('stockbee_suite_monthly_enable', parse_boolean),
            'STOCKBEE_SUITE_9m_movers': ('stockbee_suite_9m_movers', parse_boolean),
            'STOCKBEE_SUITE_weekly_movers': ('stockbee_suite_weekly_movers', parse_boolean),
            'STOCKBEE_SUITE_daily_gainers': ('stockbee_suite_daily_gainers', parse_boolean),
            'STOCKBEE_SUITE_industry_leaders': ('stockbee_suite_industry_leaders', parse_boolean),
            'STOCKBEE_SUITE_min_market_cap': ('stockbee_suite_min_market_cap', int),
            'STOCKBEE_SUITE_min_price': ('stockbee_suite_min_price', float),
            'STOCKBEE_SUITE_exclude_funds': ('stockbee_suite_exclude_funds', parse_boolean),
            'STOCKBEE_SUITE_9m_volume_threshold': ('stockbee_suite_9m_volume_threshold', int),
            'STOCKBEE_SUITE_9m_rel_vol_threshold': ('stockbee_suite_9m_rel_vol_threshold', float),
            'STOCKBEE_SUITE_weekly_gain_threshold': ('stockbee_suite_weekly_gain_threshold', float),
            'STOCKBEE_SUITE_weekly_rel_vol_threshold': ('stockbee_suite_weekly_rel_vol_threshold', float),
            'STOCKBEE_SUITE_weekly_min_avg_volume': ('stockbee_suite_weekly_min_avg_volume', int),
            'STOCKBEE_SUITE_daily_gain_threshold': ('stockbee_suite_daily_gain_threshold', float),
            'STOCKBEE_SUITE_daily_rel_vol_threshold': ('stockbee_suite_daily_rel_vol_threshold', float),
            'STOCKBEE_SUITE_daily_min_volume': ('stockbee_suite_daily_min_volume', int),
            'STOCKBEE_SUITE_industry_top_pct': ('stockbee_suite_industry_top_pct', float),
            'STOCKBEE_SUITE_industry_top_stocks': ('stockbee_suite_industry_top_stocks', int),
            'STOCKBEE_SUITE_industry_min_size': ('stockbee_suite_industry_min_size', int),
            'STOCKBEE_SUITE_9m_relative_volume': ('stockbee_suite_9m_relative_volume', float),
            'STOCKBEE_SUITE_weekly_min_volume': ('stockbee_suite_weekly_min_volume', int),
            'STOCKBEE_SUITE_save_individual_files': ('stockbee_suite_save_individual_files', parse_boolean),

            # Qullamaggie Suite Configuration
            'QULLAMAGGIE_SUITE_enable': ('qullamaggie_suite_enable', parse_boolean),
            'QULLAMAGGIE_SUITE_rs_threshold': ('qullamaggie_suite_rs_threshold', float),
            'QULLAMAGGIE_SUITE_atr_rs_threshold': ('qullamaggie_suite_atr_rs_threshold', float),
            'QULLAMAGGIE_SUITE_range_position_threshold': ('qullamaggie_suite_range_position_threshold', float),
            'QULLAMAGGIE_SUITE_min_market_cap': ('qullamaggie_suite_min_market_cap', int),
            'QULLAMAGGIE_SUITE_min_price': ('qullamaggie_suite_min_price', float),
            'QULLAMAGGIE_SUITE_extension_warning': ('qullamaggie_suite_extension_warning', float),
            'QULLAMAGGIE_SUITE_extension_danger': ('qullamaggie_suite_extension_danger', float),
            'QULLAMAGGIE_SUITE_min_data_length': ('qullamaggie_suite_min_data_length', int),
            
            # ADL Screener Configuration
            'ADL_SCREENER_enable': ('adl_screener_enable', parse_boolean),
            'ADL_SCREENER_daily_enable': ('adl_screener_daily_enable', parse_boolean),
            'ADL_SCREENER_weekly_enable': ('adl_screener_weekly_enable', parse_boolean),
            'ADL_SCREENER_monthly_enable': ('adl_screener_monthly_enable', parse_boolean),

            # Base ADL calculation parameters
            'ADL_SCREENER_lookback_period': ('adl_screener_lookback_period', int),
            'ADL_SCREENER_divergence_period': ('adl_screener_divergence_period', int),
            'ADL_SCREENER_breakout_period': ('adl_screener_breakout_period', int),
            'ADL_SCREENER_min_divergence_strength': ('adl_screener_min_divergence_strength', float),
            'ADL_SCREENER_min_breakout_strength': ('adl_screener_min_breakout_strength', float),
            'ADL_SCREENER_min_volume_avg': ('adl_screener_min_volume_avg', int),
            'ADL_SCREENER_min_price': ('adl_screener_min_price', float),
            'ADL_SCREENER_save_individual_files': ('adl_screener_save_individual_files', parse_boolean),

            # Month-over-Month Analysis
            'ADL_SCREENER_mom_analysis_enable': ('adl_screener_mom_analysis_enable', parse_boolean),
            'ADL_SCREENER_mom_period': ('adl_screener_mom_period', int),
            'ADL_SCREENER_mom_min_threshold_pct': ('adl_screener_mom_min_threshold_pct', float),
            'ADL_SCREENER_mom_max_threshold_pct': ('adl_screener_mom_max_threshold_pct', float),
            'ADL_SCREENER_mom_consecutive_months': ('adl_screener_mom_consecutive_months', int),
            'ADL_SCREENER_mom_lookback_months': ('adl_screener_mom_lookback_months', int),
            'ADL_SCREENER_mom_min_consistency_score': ('adl_screener_mom_min_consistency_score', float),

            # Short-term Momentum Analysis
            'ADL_SCREENER_short_term_enable': ('adl_screener_short_term_enable', parse_boolean),
            'ADL_SCREENER_short_term_periods': ('adl_screener_short_term_periods', str),
            'ADL_SCREENER_short_term_momentum_threshold': ('adl_screener_short_term_momentum_threshold', float),
            'ADL_SCREENER_short_term_acceleration_detect': ('adl_screener_short_term_acceleration_detect', parse_boolean),
            'ADL_SCREENER_short_term_min_score': ('adl_screener_short_term_min_score', float),

            # Moving Average Analysis
            'ADL_SCREENER_ma_enable': ('adl_screener_ma_enable', parse_boolean),
            'ADL_SCREENER_ma_periods': ('adl_screener_ma_periods', str),
            'ADL_SCREENER_ma_type': ('adl_screener_ma_type', str),
            'ADL_SCREENER_ma_bullish_alignment_required': ('adl_screener_ma_bullish_alignment_required', parse_boolean),
            'ADL_SCREENER_ma_crossover_detection': ('adl_screener_ma_crossover_detection', parse_boolean),
            'ADL_SCREENER_ma_crossover_lookback': ('adl_screener_ma_crossover_lookback', int),
            'ADL_SCREENER_ma_min_slope_threshold': ('adl_screener_ma_min_slope_threshold', float),
            'ADL_SCREENER_ma_min_alignment_score': ('adl_screener_ma_min_alignment_score', float),

            # Composite Scoring and Ranking
            'ADL_SCREENER_composite_scoring_enable': ('adl_screener_composite_scoring_enable', parse_boolean),
            'ADL_SCREENER_composite_weight_longterm': ('adl_screener_composite_weight_longterm', float),
            'ADL_SCREENER_composite_weight_shortterm': ('adl_screener_composite_weight_shortterm', float),
            'ADL_SCREENER_composite_weight_ma_align': ('adl_screener_composite_weight_ma_align', float),
            'ADL_SCREENER_composite_min_score': ('adl_screener_composite_min_score', float),
            'ADL_SCREENER_ranking_method': ('adl_screener_ranking_method', str),
            'ADL_SCREENER_output_ranking_file': ('adl_screener_output_ranking_file', parse_boolean),
            'ADL_SCREENER_top_candidates_count': ('adl_screener_top_candidates_count', int),

            # Output Configuration
            'ADL_SCREENER_output_separate_signals': ('adl_screener_output_separate_signals', parse_boolean),
            'ADL_SCREENER_output_include_charts': ('adl_screener_output_include_charts', parse_boolean),
            'ADL_SCREENER_output_summary_stats': ('adl_screener_output_summary_stats', parse_boolean),
            
            # Guppy GMMA Screener Configuration
            'GUPPY_SCREENER_enable': ('guppy_screener_enable', parse_boolean),
            'GUPPY_SCREENER_daily_enable': ('guppy_screener_daily_enable', parse_boolean),
            'GUPPY_SCREENER_weekly_enable': ('guppy_screener_weekly_enable', parse_boolean),
            'GUPPY_SCREENER_monthly_enable': ('guppy_screener_monthly_enable', parse_boolean),
            'GUPPY_SCREENER_ma_type': ('guppy_screener_ma_type', str),
            'GUPPY_SCREENER_short_term_group_daily': ('guppy_screener_short_term_emas', parse_comma_separated_ints),
            'GUPPY_SCREENER_long_term_group_daily': ('guppy_screener_long_term_emas', parse_comma_separated_ints),
            'GUPPY_SCREENER_min_compression_ratio': ('guppy_screener_min_compression_ratio', float),
            'GUPPY_SCREENER_min_expansion_ratio': ('guppy_screener_min_expansion_ratio', float),
            'GUPPY_SCREENER_crossover_confirmation_days': ('guppy_screener_crossover_confirmation_days', int),
            'GUPPY_SCREENER_volume_confirmation_threshold': ('guppy_screener_volume_confirmation_threshold', float),
            'GUPPY_SCREENER_min_price': ('guppy_screener_min_price', float),
            'GUPPY_SCREENER_min_volume_avg': ('guppy_screener_min_volume_avg', int),
            'GUPPY_SCREENER_min_data_length': ('guppy_screener_min_data_length', int),
            'GUPPY_SCREENER_save_individual_files': ('guppy_screener_save_individual_files', parse_boolean),
            
            # Gold Launch Pad CSV mappings
            'GOLD_LAUNCH_PAD_enable': ('gold_launch_pad_enable', parse_boolean),
            'GOLD_LAUNCH_PAD_daily_enable': ('gold_launch_pad_daily_enable', parse_boolean),
            'GOLD_LAUNCH_PAD_weekly_enable': ('gold_launch_pad_weekly_enable', parse_boolean),
            'GOLD_LAUNCH_PAD_monthly_enable': ('gold_launch_pad_monthly_enable', parse_boolean),
            'GOLD_LAUNCH_PAD_ma_periods': ('gold_launch_pad_ma_periods', _parse_period_string),
            'GOLD_LAUNCH_PAD_ma_type': ('gold_launch_pad_ma_type', str),
            'GOLD_LAUNCH_PAD_zscore_window': ('gold_launch_pad_zscore_window', int),
            'GOLD_LAUNCH_PAD_max_spread_threshold': ('gold_launch_pad_max_spread_threshold', float),
            'GOLD_LAUNCH_PAD_slope_lookback_pct': ('gold_launch_pad_slope_lookback_pct', float),
            'GOLD_LAUNCH_PAD_min_slope_threshold': ('gold_launch_pad_min_slope_threshold', float),
            'GOLD_LAUNCH_PAD_price_proximity_stdv': ('gold_launch_pad_price_proximity_stdv', float),
            'GOLD_LAUNCH_PAD_proximity_window': ('gold_launch_pad_proximity_window', int),
            'GOLD_LAUNCH_PAD_min_price': ('gold_launch_pad_min_price', float),
            'GOLD_LAUNCH_PAD_min_volume': ('gold_launch_pad_min_volume', int),
            'GOLD_LAUNCH_PAD_save_individual_files': ('gold_launch_pad_save_individual_files', parse_boolean),
            
            # RTI CSV mappings
            'RTI_enable': ('rti_enable', parse_boolean),
            'RTI_daily_enable': ('rti_daily_enable', parse_boolean),
            'RTI_weekly_enable': ('rti_weekly_enable', parse_boolean),
            'RTI_monthly_enable': ('rti_monthly_enable', parse_boolean),
            'RTI_period': ('rti_period', int),
            'RTI_short_period': ('rti_short_period', int),
            'RTI_swing_period': ('rti_swing_period', int),
            'RTI_zone1_threshold': ('rti_zone1_threshold', float),
            'RTI_zone2_threshold': ('rti_zone2_threshold', float),
            'RTI_zone3_threshold': ('rti_zone3_threshold', float),
            'RTI_low_volatility_threshold': ('rti_low_volatility_threshold', float),
            'RTI_expansion_multiplier': ('rti_expansion_multiplier', float),
            'RTI_consecutive_low_vol_bars': ('rti_consecutive_low_vol_bars', int),
            'RTI_min_consolidation_period': ('rti_min_consolidation_period', int),
            'RTI_breakout_confirmation_period': ('rti_breakout_confirmation_period', int),
            'RTI_min_price': ('rti_min_price', float),
            'RTI_min_volume': ('rti_min_volume', int),
            'RTI_save_individual_files': ('rti_save_individual_files', parse_boolean),

            'VOLUME_SUITE_pvb_TWmodel_integration': ('volume_suite_pvb_clmodel_integration', parse_boolean),
            'VOLUME_SUITE_hv_month_cutoff': ('volume_suite_hv_month_cutoff', int),
            'VOLUME_SUITE_hv_day_cutoff': ('volume_suite_hv_day_cutoff', int),
            'VOLUME_SUITE_hv_std_cutoff': ('volume_suite_hv_std_cutoff', int),
            'VOLUME_SUITE_hv_min_volume': ('volume_suite_hv_min_volume', int),
            'VOLUME_SUITE_hv_min_price': ('volume_suite_hv_min_price', float),
            'VOLUME_SUITE_stdv_cutoff': ('volume_suite_stdv_cutoff', int),
            'VOLUME_SUITE_stdv_min_volume': ('volume_suite_stdv_min_volume', int),
            'VOLUME_SUITE_vroc_threshold': ('volume_suite_vroc_threshold', float),
            'VOLUME_SUITE_rvol_threshold': ('volume_suite_rvol_threshold', float),
            'VOLUME_SUITE_rvol_extreme_threshold': ('volume_suite_rvol_extreme_threshold', float),
            'VOLUME_SUITE_mfi_overbought': ('volume_suite_mfi_overbought', int),
            'VOLUME_SUITE_mfi_oversold': ('volume_suite_mfi_oversold', int),
            'VOLUME_SUITE_vpt_threshold': ('volume_suite_vpt_threshold', float),
            'VOLUME_SUITE_output_dir': ('volume_suite_output_dir', str),
            
            # Performance optimization
            'cap_history_data': ('cap_history_data', int),
            
            # Market Pulse Configuration
            'MARKET_PULSE_enable': ('market_pulse_enable', parse_boolean),
            'MARKET_PULSE_gmi_enable': ('market_pulse_gmi_enable', parse_boolean),
            'MARKET_PULSE_gmi_threshold': ('market_pulse_gmi_threshold', int),
            'MARKET_PULSE_gmi_confirmation_days': ('market_pulse_gmi_confirmation_days', int),
            'MARKET_PULSE_gmi_short_term_sma': ('market_pulse_gmi_short_term_sma', int),
            'MARKET_PULSE_gmi_long_term_sma': ('market_pulse_gmi_long_term_sma', int),
            'MARKET_PULSE_gmi_MF_index': ('market_pulse_gmi_mf_index', str),
            'MARKET_PULSE_gmi_index1': ('market_pulse_gmi_index1', str),
            'MARKET_PULSE_gmi_index2': ('market_pulse_gmi_index2', str),
            'MARKET_PULSE_gmi_MF_ma_period': ('market_pulse_gmi_mf_ma_period', int),
            'MARKET_PULSE_gmi_breath_file_suffix': ('market_pulse_gmi_breath_file_suffix', str),

            # GMI2 Configuration mappings
            'MARKET_PULSE_gmi2_enable': ('market_pulse_gmi2_enable', parse_boolean),
            'MARKET_PULSE_gmi2_index': ('market_pulse_gmi2_index', str),
            'MARKET_PULSE_gmi2_sma': ('market_pulse_gmi2_sma', str),
            'MARKET_PULSE_gmi2_index_stochastic_threshold': ('market_pulse_gmi2_index_stochastic_threshold', int),
            'MARKET_PULSE_gmi2_threshold': ('market_pulse_gmi2_threshold', int),
            'MARKET_PULSE_gmi2_confirmation_days': ('market_pulse_gmi2_confirmation_days', int),
            
            'MARKET_PULSE_ftd_dd_enable': ('market_pulse_ftd_dd_enable', parse_boolean),
            'MARKET_PULSE_ftd_dd_report_enable': ('market_pulse_ftd_dd_report_enable', parse_boolean),
            'MARKET_PULSE_comprehensive_report_enable': ('market_pulse_comprehensive_report_enable', parse_boolean),
            'MARKET_PULSE_dd_threshold': ('market_pulse_dd_threshold', float),
            'MARKET_PULSE_ftd_threshold': ('market_pulse_ftd_threshold', float),
            'MARKET_PULSE_ftd_optimal_days_min': ('market_pulse_ftd_optimal_days_min', int),
            'MARKET_PULSE_ftd_optimal_days_max': ('market_pulse_ftd_optimal_days_max', int),
            'MARKET_PULSE_dd_lookback_period': ('market_pulse_dd_lookback_period', int),
            'MARKET_PULSE_net_highs_lows_enable': ('market_pulse_net_highs_lows_enable', parse_boolean),
            'MARKET_PULSE_breadth_threshold_healthy': ('market_pulse_breadth_threshold_healthy', float),
            'MARKET_PULSE_breadth_threshold_unhealthy': ('market_pulse_breadth_threshold_unhealthy', float),
            'MARKET_PULSE_chillax_ma_enable': ('market_pulse_chillax_ma_enable', parse_boolean),
            'MARKET_PULSE_chillax_ma_fast_period': ('market_pulse_chillax_ma_fast_period', int),
            'MARKET_PULSE_chillax_ma_slow_period': ('market_pulse_chillax_ma_slow_period', int),
            'MARKET_PULSE_chillax_trend_days': ('market_pulse_chillax_trend_days', int),

            # Chillax MAs Enhanced Configuration
            'MARKET_PULSE_chillax_mas_indexes': ('market_pulse_chillax_mas_indexes', str),
            'MARKET_PULSE_chillax_mas_sma': ('market_pulse_chillax_mas_sma', str),
            'MARKET_PULSE_chillax_mas_charts': ('market_pulse_chillax_mas_charts', str),
            'MARKET_PULSE_chillax_mas_charts_timeframe': ('market_pulse_chillax_mas_charts_timeframe', int),
            'MARKET_PULSE_chillax_display_sma': ('market_pulse_chillax_display_sma', str),
            'MARKET_PULSE_ma_cycles_enable': ('market_pulse_ma_cycles_enable', parse_boolean),

            # MA Cycles Enhanced Configuration
            'MARKET_PULSE_ma_cycles_indexes': ('market_pulse_ma_cycles_indexes', str),
            'MARKET_PULSE_ma_cycles_ma_period': ('market_pulse_ma_cycles_ma_period', str),
            'MARKET_PULSE_ma_cycles_charts': ('market_pulse_ma_cycles_charts', str),
            'MARKET_PULSE_ma_cycles_charts_timeframe': ('market_pulse_ma_cycles_charts_timeframe', int),
            'MARKET_PULSE_ma_cycles_cycle_mode': ('market_pulse_ma_cycles_cycle_mode', str),
            'MARKET_PULSE_ma_cycles_smoothed_candles': ('market_pulse_ma_cycles_smoothed_candles', int),

            # Legacy MA Cycles Configuration
            'MARKET_PULSE_ma_cycles_reference_period': ('market_pulse_ma_cycles_reference_period', int),
            'MARKET_PULSE_ma_cycles_min_cycle_length': ('market_pulse_ma_cycles_min_cycle_length', int),
            'MARKET_PULSE_output_dir': ('market_pulse_output_dir', str),
            'MARKET_PULSE_save_detailed_results': ('market_pulse_save_detailed_results', parse_boolean),
            'MARKET_PULSE_generate_alerts': ('market_pulse_generate_alerts', parse_boolean),
            
            # Market Breadth Analysis Configuration
            'MARKET_BREADTH_enable': ('market_breadth_enable', parse_boolean),
            'MARKET_BREADTH_daily_enable': ('market_breadth_daily_enable', parse_boolean),
            'MARKET_BREADTH_weekly_enable': ('market_breadth_weekly_enable', parse_boolean),
            'MARKET_BREADTH_monthly_enable': ('market_breadth_monthly_enable', parse_boolean),
            # Timeframe configuration
            'MARKET_BREADTH_daily_ma_periods': ('market_breadth_daily_ma_periods', _parse_period_string),
            'MARKET_BREADTH_daily_new_high_lows_periods': ('market_breadth_daily_new_high_lows_periods', _parse_period_string),
            'MARKET_BREADTH_weekly_ma_periods': ('market_breadth_weekly_ma_periods', _parse_period_string),
            'MARKET_BREADTH_weekly_new_high_lows_periods': ('market_breadth_weekly_new_high_lows_periods', _parse_period_string),
            'MARKET_BREADTH_monthly_ma_periods': ('market_breadth_monthly_ma_periods', _parse_period_string),
            'MARKET_BREADTH_monthly_new_high_lows_periods': ('market_breadth_monthly_new_high_lows_periods', _parse_period_string),
            'MARKET_BREADTH_universe': ('market_breadth_universe', _parse_market_breadth_universe),
            # Generic threshold configuration
            'MARKET_BREADTH_new_highs_threshold_long': ('market_breadth_new_highs_threshold_long', int),
            'MARKET_BREADTH_new_highs_threshold_medium': ('market_breadth_new_highs_threshold_medium', int),
            'MARKET_BREADTH_new_highs_threshold_short': ('market_breadth_new_highs_threshold_short', int),
            'MARKET_BREADTH_success_window_pct_long': ('market_breadth_success_window_pct_long', int),
            'MARKET_BREADTH_success_window_pct_medium': ('market_breadth_success_window_pct_medium', int),
            'MARKET_BREADTH_success_window_pct_short': ('market_breadth_success_window_pct_short', int),
            'MARKET_BREADTH_success_threshold_pct_long': ('market_breadth_success_threshold_pct_long', int),
            'MARKET_BREADTH_success_threshold_pct_medium': ('market_breadth_success_threshold_pct_medium', int),
            'MARKET_BREADTH_success_threshold_pct_short': ('market_breadth_success_threshold_pct_short', int),
            # Legacy configuration (deprecated)
            'MARKET_BREADTH_lookback_days': ('market_breadth_lookback_days', int),
            'MARKET_BREADTH_ma_periods': ('market_breadth_ma_periods', _parse_period_string),
            # 252-day threshold configuration
            'MARKET_BREADTH_daily_252day_new_highs_threshold': ('market_breadth_daily_252day_new_highs_threshold', int),
            'MARKET_BREADTH_ten_day_success_threshold': ('market_breadth_ten_day_success_threshold', int),
            # 20-day threshold configuration
            'MARKET_BREADTH_daily_20day_new_highs_threshold': ('market_breadth_daily_20day_new_highs_threshold', int),
            'MARKET_BREADTH_twenty_day_success_threshold': ('market_breadth_twenty_day_success_threshold', int),
            # 63-day threshold configuration
            'MARKET_BREADTH_daily_63day_new_highs_threshold': ('market_breadth_daily_63day_new_highs_threshold', int),
            'MARKET_BREADTH_sixty_three_day_success_threshold': ('market_breadth_sixty_three_day_success_threshold', int),
            # Advance/decline thresholds
            'MARKET_BREADTH_strong_ad_ratio_threshold': ('market_breadth_strong_ad_ratio_threshold', float),
            'MARKET_BREADTH_weak_ad_ratio_threshold': ('market_breadth_weak_ad_ratio_threshold', float),
            'MARKET_BREADTH_strong_advance_threshold': ('market_breadth_strong_advance_threshold', float),
            'MARKET_BREADTH_weak_advance_threshold': ('market_breadth_weak_advance_threshold', float),
            # Moving average breadth thresholds
            'MARKET_BREADTH_strong_ma_breadth_threshold': ('market_breadth_strong_ma_breadth_threshold', float),
            'MARKET_BREADTH_weak_ma_breadth_threshold': ('market_breadth_weak_ma_breadth_threshold', float),
            # Chart history display configuration
            'MARKET_BREADTH_chart_history_days': ('market_breadth_chart_history_days', int),
            'MARKET_BREADTH_chart_history_weeks': ('market_breadth_chart_history_weeks', int),
            'MARKET_BREADTH_chart_history_months': ('market_breadth_chart_history_months', int),
            # Output configuration
            'MARKET_BREADTH_save_detailed_results': ('market_breadth_save_detailed_results', parse_boolean),
            'MARKET_BREADTH_output_dir': ('market_breadth_output_dir', str),
            'MARKET_BREADTH_tornado_chart': ('market_breadth_tornado_chart', parse_boolean),
            'MARKET_BREADTH_tornado_chart_display_units_time': ('market_breadth_tornado_chart_display_units_time', int),
            
            # Dashboard Configuration
            'DASHBOARD_enable': ('dashboard_enable', parse_boolean),
            'DASHBOARD_output_dir': ('dashboard_output_dir', str),
            'DASHBOARD_auto_refresh': ('dashboard_auto_refresh', parse_boolean),
            'DASHBOARD_include_charts': ('dashboard_include_charts', parse_boolean),
            'DASHBOARD_max_opportunities': ('dashboard_max_opportunities', int),
            'DASHBOARD_max_alerts': ('dashboard_max_alerts', int),
            'DASHBOARD_save_historical': ('dashboard_save_historical', parse_boolean),

            # HVE (Highest Volume Ever) Configuration
            'HVE_enable': ('hve_enable', parse_boolean),
            'HVE_output_dir': ('hve_output_dir', str),
            'HVE_limit_years': ('hve_limit_years', int),
            'HVE_min_volume': ('hve_min_volume', int),
            'HVE_min_price': ('hve_min_price', float),
            'HVE_date_range_mode': ('hve_date_range_mode', str),
            'HVE_start_date': ('hve_start_date', str),
            'HVE_end_date': ('hve_end_date', str),
            'HVE_historical_max_events': ('hve_historical_max_events', int),
            'HVE_historical_export': ('hve_historical_export', parse_boolean),
            'HVD_historical_export': ('hvd_historical_export', parse_boolean),
            'HVD_historical_max_days': ('hvd_historical_max_days', int),

            # HV1Y (Highest Volume in 1 Year) Configuration
            'HV1Y_enable': ('hv1y_enable', parse_boolean),
            'HV1Y_window_days': ('hv1y_window_days', int)
        }
        
        # Process each row in the dataframe
        for _, row in df.iterrows():
            variable = row['variable']
            value = row['value']
            
            if variable in config_map:
                attr_name, converter = config_map[variable]
                try:
                    converted_value = converter(value)
                    setattr(config, attr_name, converted_value)
                except (ValueError, TypeError) as e:
                    print(f"Warning: Invalid value '{value}' for {variable}. Using default. Error: {e}")
        
        # Validation for ticker_choice
        try:
            # Parse ticker choice to validate format - handle dash separator
            choice_str = str(config.ticker_choice)
            group_ids = [int(id_str.strip()) for id_str in choice_str.split('-')]
            
            # Validate all group IDs are in range 0-8
            for group_id in group_ids:
                if not (0 <= group_id <= 8):
                    raise ValueError(f"Group ID {group_id} not in valid range 0-8")
                    
        except (ValueError, AttributeError):
            print(f"Warning: ticker_choice '{config.ticker_choice}' is invalid. Using default ('2').")
            config.ticker_choice = "2"
        
        # Parse RS period strings into lists of integers
        # Parse RS periods based on the new configuration structure
        # Note: RS periods now use the same period configuration as basic calculations
        # This ensures consistency between RS and basic calculation period definitions
            
        return config

    except FileNotFoundError:
        print(f"Error: {file_path} not found. Using default configuration.")
        return UserConfiguration()

    except Exception as e:
        print(f"Error reading user data: {e}. Using default configuration.")
        return UserConfiguration()


def read_user_data_legacy() -> tuple:
    """
    Legacy function for backward compatibility.
    Returns (ticker_choice, write_info_file) tuple as expected by existing code.
    """
    config = read_user_data()
    return config.ticker_choice, config.write_info_file



def _parse_market_breadth_universe(value: str) -> dict:
    """
    Parse market breadth universe configuration supporting all three syntax types.
    
    Examples:
        'SP500' -> single universe
        'SP500;NASDAQ100' -> separate processing (2 files per timeframe)  
        'SP500+NASDAQ100' -> combined processing (1 file per timeframe)
        
    Returns:
        dict: Configuration object with type and universe information
    """
    value = value.strip()
    
    if ';' in value:
        # Separate universe processing: SP500;NASDAQ100;Russell1000
        universes = [u.strip() for u in value.split(';') if u.strip()]
        return {
            'type': 'separate',
            'universes': universes,
            'display_name': None,  # Individual names used
            'file_count': len(universes),  # Multiple files
            'raw_config': value
        }
        
    elif '+' in value:
        # Combined universe processing: SP500+NASDAQ100+Russell1000
        universes = [u.strip() for u in value.split('+') if u.strip()]
        return {
            'type': 'combined',
            'universes': universes,
            'display_name': value,  # Full combined name
            'file_count': 1,  # Single file
            'raw_config': value
        }
        
    else:
        # Single universe (backwards compatible): SP500
        return {
            'type': 'single',
            'universes': [value],
            'display_name': value,
            'file_count': 1,  # Single file
            'raw_config': value
        }


def _parse_period_string(period_str: str) -> list:
    """
    Parse semicolon-separated period string into list of integers.
    
    Args:
        period_str: String like "1;3;5;10;15"
        
    Returns:
        List of integers [1, 3, 5, 10, 15]
    """
    try:
        return [int(p.strip()) for p in period_str.split(';') if p.strip()]
    except (ValueError, AttributeError):
        return [1, 3, 5]  # Default fallback


def get_atr1_params_for_timeframe(config: UserConfiguration, timeframe: str) -> dict:
    """
    Get timeframe-specific ATR1 parameters.
    
    Args:
        config: UserConfiguration object
        timeframe: 'daily', 'weekly', or 'monthly'
        
    Returns:
        Dictionary with ATR1 parameters for the specified timeframe
    """
    base_params = {
        'src': 'Close',
        'src2': 'Close',
        'min_volume': 10000,
        'min_price': 1.0,
        'ticker_choice': config.ticker_choice,
        'timeframe': timeframe,
        'cap_history_data': config.cap_history_data
    }
    
    if timeframe == 'daily':
        base_params.update({
            'length': config.atr1_daily_length,
            'factor': config.atr1_daily_factor,
            'length2': config.atr1_daily_length2,
            'factor2': config.atr1_daily_factor2
        })
    elif timeframe == 'weekly':
        base_params.update({
            'length': config.atr1_weekly_length,
            'factor': config.atr1_weekly_factor,
            'length2': config.atr1_weekly_length2,
            'factor2': config.atr1_weekly_factor2
        })
    elif timeframe == 'monthly':
        base_params.update({
            'length': config.atr1_monthly_length,
            'factor': config.atr1_monthly_factor,
            'length2': config.atr1_monthly_length2,
            'factor2': config.atr1_monthly_factor2
        })
    else:
        raise ValueError(f"Unsupported timeframe for ATR1: {timeframe}")
    
    return base_params


def get_atr2_params_for_timeframe(config: UserConfiguration, timeframe: str) -> dict:
    """
    Get timeframe-specific ATR2 parameters.
    
    Args:
        config: UserConfiguration object
        timeframe: 'daily', 'weekly', or 'monthly'
        
    Returns:
        Dictionary with ATR2 parameters for the specified timeframe
    """
    base_params = {
        'min_volume': 10000,
        'min_price': 1.0,
        'high_volatility_threshold': 0.8,
        'low_volatility_threshold': 0.2,
        'extended_threshold': 2.0,
        'optimal_range': 1.0,
        'ticker_choice': config.ticker_choice,
        'timeframe': timeframe,
        'cap_history_data': config.cap_history_data
    }
    
    if timeframe == 'daily':
        base_params.update({
            'atr_period': config.atr2_daily_atr_period,
            'sma_period': config.atr2_daily_sma_period,
            'enable_percentile': True,
            'percentile_period': config.atr2_daily_percentile_period
        })
    elif timeframe == 'weekly':
        base_params.update({
            'atr_period': config.atr2_weekly_atr_period,
            'sma_period': config.atr2_weekly_sma_period,
            'enable_percentile': True,
            'percentile_period': config.atr2_weekly_percentile_period
        })
    elif timeframe == 'monthly':
        base_params.update({
            'atr_period': config.atr2_monthly_atr_period,
            'sma_period': config.atr2_monthly_sma_period,
            'enable_percentile': True,
            'percentile_period': config.atr2_monthly_percentile_period
        })
    else:
        raise ValueError(f"Unsupported timeframe for ATR2: {timeframe}")
    
    return base_params


def get_pvb_TWmodel_params_for_timeframe(config: UserConfiguration, timeframe: str) -> dict:
    """
    Get timeframe-specific PVB TWmodel parameters.
    
    Args:
        config: UserConfiguration object
        timeframe: 'daily', 'weekly', or 'monthly'
        
    Returns:
        Dictionary with PVB TWmodel parameters for the specified timeframe
    """
    if timeframe == 'daily':
        return {
            'price_breakout_period': config.pvb_TWmodel_daily_price_breakout_period,
            'volume_breakout_period': config.pvb_TWmodel_daily_volume_breakout_period,
            'trendline_length': config.pvb_TWmodel_daily_trendline_length,
            'close_threshold': config.pvb_TWmodel_daily_close_threshold,
            'signal_max_age': config.pvb_TWmodel_daily_signal_max_age,
            'order_direction': config.pvb_TWmodel_order_direction,
            'min_volume': config.pvb_TWmodel_min_volume,
            'min_price': config.pvb_TWmodel_min_price,
            'ticker_choice': config.ticker_choice,
            'timeframe': timeframe
        }
    elif timeframe == 'weekly':
        return {
            'price_breakout_period': config.pvb_TWmodel_weekly_price_breakout_period,
            'volume_breakout_period': config.pvb_TWmodel_weekly_volume_breakout_period,
            'trendline_length': config.pvb_TWmodel_weekly_trendline_length,
            'close_threshold': config.pvb_TWmodel_weekly_close_threshold,
            'signal_max_age': config.pvb_TWmodel_weekly_signal_max_age,
            'order_direction': config.pvb_TWmodel_order_direction,
            'min_volume': config.pvb_TWmodel_min_volume,
            'min_price': config.pvb_TWmodel_min_price,
            'ticker_choice': config.ticker_choice,
            'timeframe': timeframe
        }
    elif timeframe == 'monthly':
        return {
            'price_breakout_period': config.pvb_TWmodel_monthly_price_breakout_period,
            'volume_breakout_period': config.pvb_TWmodel_monthly_volume_breakout_period,
            'trendline_length': config.pvb_TWmodel_monthly_trendline_length,
            'close_threshold': config.pvb_TWmodel_monthly_close_threshold,
            'signal_max_age': config.pvb_TWmodel_monthly_signal_max_age,
            'order_direction': config.pvb_TWmodel_order_direction,
            'min_volume': config.pvb_TWmodel_min_volume,
            'min_price': config.pvb_TWmodel_min_price,
            'ticker_choice': config.ticker_choice,
            'timeframe': timeframe
        }
    else:
        raise ValueError(f"Unsupported timeframe: {timeframe}")


# Legacy function for backward compatibility
def get_pvb_params_for_timeframe(config: UserConfiguration, timeframe: str) -> dict:
    """Legacy function - redirects to TWmodel version."""
    return get_pvb_TWmodel_params_for_timeframe(config, timeframe)


def get_minervini_params_for_timeframe(config: UserConfiguration, timeframe: str) -> dict:
    """
    Get timeframe-specific Minervini parameters.
    
    Args:
        config: UserConfiguration object
        timeframe: 'daily', 'weekly', or 'monthly'
        
    Returns:
        Dictionary with Minervini parameters for the specified timeframe
    """
    return {
        'rs_min_rating': config.minervini_rs_min_rating,
        'min_volume': config.minervini_min_volume,
        'min_price': config.minervini_min_price,
        'show_all_stocks': config.minervini_show_all_stocks,
        'ticker_choice': config.ticker_choice,
        'timeframe': timeframe
    }


def get_giusti_params_for_timeframe(config, timeframe):
    """
    Get Giusti screener parameters for specific timeframe.
    
    Args:
        config: User configuration object
        timeframe: String timeframe ('daily', 'weekly', 'monthly')
        
    Returns:
        dict: Giusti parameters for the timeframe
    """
    return {
        'min_price': config.giusti_min_price,
        'min_volume': config.giusti_min_volume,
        'rolling_12m': config.giusti_rolling_12m,
        'rolling_6m': config.giusti_rolling_6m,
        'rolling_3m': config.giusti_rolling_3m,
        'top_12m_count': config.giusti_top_12m_count,
        'top_6m_count': config.giusti_top_6m_count,
        'top_3m_count': config.giusti_top_3m_count,
        'min_history_months': config.giusti_min_history_months,
        'show_all_stocks': config.giusti_show_all_stocks,
        'ticker_choice': config.ticker_choice,
        'timeframe': timeframe
    }


def get_drwish_params_for_timeframe(config: UserConfiguration, timeframe: str) -> list:
    """
    Get Dr. Wish suite screener parameters for specific timeframe.
    Now supports multiple parameter sets via semicolon-separated configuration.

    Args:
        config: UserConfiguration object
        timeframe: 'daily', 'weekly', or 'monthly'

    Returns:
        List of dictionaries with Dr. Wish parameters for each parameter set
    """
    # Parse semicolon-separated values
    lookback_periods = [p.strip() for p in config.drwish_lookback_period.split(';') if p.strip()]
    historical_glb_periods = [p.strip() for p in config.drwish_calculate_historical_GLB.split(';') if p.strip()]
    confirmation_periods = [p.strip() for p in config.drwish_confirmation_period.split(';') if p.strip()]

    # Ensure all lists have the same length by padding with the first value
    max_sets = max(len(lookback_periods), len(historical_glb_periods), len(confirmation_periods))

    if len(lookback_periods) < max_sets:
        lookback_periods.extend([lookback_periods[0]] * (max_sets - len(lookback_periods)))
    if len(historical_glb_periods) < max_sets:
        historical_glb_periods.extend([historical_glb_periods[0]] * (max_sets - len(historical_glb_periods)))
    if len(confirmation_periods) < max_sets:
        confirmation_periods.extend([confirmation_periods[0]] * (max_sets - len(confirmation_periods)))

    # Create parameter sets
    param_sets = []
    for i in range(max_sets):
        param_set = {
            'timeframe': timeframe,
            'parameter_set_index': i,
            'parameter_set_name': f"set{i+1}",
            'min_price': config.drwish_min_price,
            'min_volume': config.drwish_min_volume,
            'pivot_strength': config.drwish_pivot_strength,
            'lookback_period': lookback_periods[i],
            'calculate_historical_GLB': historical_glb_periods[i],
            'confirmation_period': confirmation_periods[i],
            'require_confirmation': config.drwish_require_confirmation,
            'enable_glb': config.drwish_enable_glb,
            'enable_blue_dot': config.drwish_enable_blue_dot,
            'enable_black_dot': config.drwish_enable_black_dot,
            'blue_dot_stoch_period': config.drwish_blue_dot_stoch_period,
            'blue_dot_stoch_threshold': config.drwish_blue_dot_stoch_threshold,
            'blue_dot_sma_period': config.drwish_blue_dot_sma_period,
            'black_dot_stoch_period': config.drwish_black_dot_stoch_period,
            'black_dot_stoch_threshold': config.drwish_black_dot_stoch_threshold,
            'black_dot_lookback': config.drwish_black_dot_lookback,
            'black_dot_sma_period': config.drwish_black_dot_sma_period,
            'black_dot_ema_period': config.drwish_black_dot_ema_period,
            'show_all_stocks': config.drwish_show_all_stocks,
            'enable_charts': config.drwish_enable_charts,
            'chart_output_dir': config.drwish_chart_output_dir,
            'show_historical_glb': config.drwish_show_historical_glb,
            'show_breakout_labels': config.drwish_show_breakout_labels,
            'generate_individual_files': config.drwish_generate_individual_files,
            'ticker_choice': config.ticker_choice
        }
        param_sets.append(param_set)

    return param_sets


def get_volume_suite_params_for_timeframe(config: UserConfiguration, timeframe: str) -> dict:
    """
    Get Volume Suite screener parameters for specific timeframe.
    Automatically scales periods based on timeframe.
    
    Args:
        config: UserConfiguration object
        timeframe: 'daily', 'weekly', or 'monthly'
        
    Returns:
        Dictionary with Volume Suite parameters for the timeframe
    """
    # Timeframe scaling factors for periods
    timeframe_scaling = {
        'daily': 1.0,
        'weekly': 0.2,  # 5 weeks = 1 month daily
        'monthly': 0.05  # 12 months = 1 year daily 
    }
    
    scale = timeframe_scaling.get(timeframe, 1.0)
    
    return {
        'enable_volume_suite': config.volume_suite_enable,
        'timeframe': timeframe,
        'timeframe_scale': scale,
        'volume_suite': {
            'enable_hv_absolute': config.volume_suite_hv_absolute,
            'enable_hv_stdv': config.volume_suite_hv_stdv,
            'enable_enhanced_anomaly': config.volume_suite_enhanced_anomaly,
            'enable_volume_indicators': config.volume_suite_volume_indicators,
            'enable_pvb_clmodel_integration': config.volume_suite_pvb_clmodel_integration,
            'save_individual_files': config.volume_suite_save_individual_files,
            
            # HV Absolute parameters (timeframe-scaled)
            'hv_month_cutoff': max(1, int(config.volume_suite_hv_month_cutoff * scale)),
            'hv_day_cutoff': max(1, int(config.volume_suite_hv_day_cutoff * scale)),
            'hv_std_cutoff': config.volume_suite_hv_std_cutoff,
            'hv_min_volume': config.volume_suite_hv_min_volume,
            'hv_min_price': config.volume_suite_hv_min_price,
            
            # HV StdDev parameters (timeframe-scaled)
            'stdv_cutoff': config.volume_suite_stdv_cutoff,
            'stdv_min_volume': config.volume_suite_stdv_min_volume,
            
            # Volume Indicators parameters (timeframe-scaled periods)
            'vroc_threshold': config.volume_suite_vroc_threshold,
            'vroc_period': max(1, int(25 * scale)),  # 25 daily -> 5 weekly -> 1 monthly
            'rvol_threshold': config.volume_suite_rvol_threshold,
            'rvol_period': max(1, int(20 * scale)),  # 20 daily -> 4 weekly -> 1 monthly
            'rvol_extreme_threshold': config.volume_suite_rvol_extreme_threshold,
            'mfi_period': max(1, int(14 * scale)),   # 14 daily -> 3 weekly -> 1 monthly
            'mfi_overbought': config.volume_suite_mfi_overbought,
            'mfi_oversold': config.volume_suite_mfi_oversold,
            'vpt_threshold': config.volume_suite_vpt_threshold,
            'vpt_ma_period': max(1, int(20 * scale)), # 20 daily -> 4 weekly -> 1 monthly
            'adtv_ma_period': max(1, int(50 * scale)), # 50 daily -> 10 weekly -> 3 monthly
            'adtv_3m_threshold': config.volume_suite_adtv_3m_threshold,
            'adtv_6m_threshold': config.volume_suite_adtv_6m_threshold,
            'adtv_1y_threshold': config.volume_suite_adtv_1y_threshold,
            'adtv_min_volume': config.volume_suite_adtv_min_volume,
            
            # PVB ClModel Integration parameters (separate from PVB TW)
            'pvb_clmodel_price_period': config.volume_suite_pvb_clmodel_price_period,
            'pvb_clmodel_volume_period': config.volume_suite_pvb_clmodel_volume_period,
            'pvb_clmodel_trend_length': config.volume_suite_pvb_clmodel_trend_length,
            'pvb_clmodel_volume_multiplier': config.volume_suite_pvb_clmodel_volume_multiplier,
            'pvb_clmodel_direction': config.volume_suite_pvb_clmodel_direction
        },
        'volume_output_dir': config.volume_suite_output_dir,
        'timeframe': timeframe
    }


def get_stockbee_suite_params_for_timeframe(config: UserConfiguration, timeframe: str) -> Optional[dict]:
    """
    Get Stockbee Suite screener parameters for specific timeframe with hierarchical flag checking.
    Automatically scales periods based on timeframe.

    Args:
        config: UserConfiguration object
        timeframe: 'daily', 'weekly', or 'monthly'

    Returns:
        Dictionary with Stockbee Suite parameters for the timeframe, or None if disabled
    """
    # Check master flag
    if not getattr(config, "stockbee_suite_enable", False):
        return None

    # Check timeframe flag
    timeframe_flag = f"stockbee_suite_{timeframe}_enable"
    if not getattr(config, timeframe_flag, True):
        return None

    # Timeframe scaling factors for periods
    timeframe_scaling = {
        'daily': 1.0,
        'weekly': 0.2,  # 5 weeks = 1 month daily
        'monthly': 0.05  # 12 months = 1 year daily
    }

    scale = timeframe_scaling.get(timeframe, 1.0)

    return {
        'enable_stockbee_suite': config.stockbee_suite_enable,
        'timeframe': timeframe,
        'timeframe_scale': scale,
        'stockbee_suite': {
            'enable_9m_movers': config.stockbee_suite_9m_movers,
            'enable_weekly_movers': config.stockbee_suite_weekly_movers,
            'enable_daily_gainers': config.stockbee_suite_daily_gainers,
            'enable_industry_leaders': config.stockbee_suite_industry_leaders,
            
            # Base filtering parameters
            'min_market_cap': config.stockbee_suite_min_market_cap,
            'min_price': config.stockbee_suite_min_price,
            'exclude_funds': config.stockbee_suite_exclude_funds,
            
            # 9M Movers parameters
            '9m_volume_threshold': config.stockbee_suite_9m_volume_threshold,
            '9m_rel_vol_threshold': config.stockbee_suite_9m_rel_vol_threshold,
            '9m_rel_vol_period': max(1, int(20 * scale)),  # 20 daily -> 4 weekly
            
            # Weekly Movers parameters (timeframe-scaled)
            'weekly_gain_threshold': config.stockbee_suite_weekly_gain_threshold,
            'weekly_rel_vol_threshold': config.stockbee_suite_weekly_rel_vol_threshold,
            'weekly_min_avg_volume': config.stockbee_suite_weekly_min_avg_volume,
            'weekly_lookback_days': max(3, int(5 * scale)),  # 5 daily -> 1 weekly
            'weekly_avg_period': max(1, int(20 * scale)),   # 20 daily -> 4 weekly
            
            # Daily Gainers parameters (timeframe-scaled)
            'daily_gain_threshold': config.stockbee_suite_daily_gain_threshold,
            'daily_rel_vol_threshold': config.stockbee_suite_daily_rel_vol_threshold,
            'daily_min_volume': config.stockbee_suite_daily_min_volume,
            'daily_rel_vol_period': max(1, int(20 * scale)),  # 20 daily -> 4 weekly
            'daily_sma_50_period': max(1, int(50 * scale)),   # 50 daily -> 10 weekly
            'daily_sma_200_period': max(1, int(200 * scale)), # 200 daily -> 40 weekly
            
            # Industry Leaders parameters
            'industry_top_pct': config.stockbee_suite_industry_top_pct,
            'industry_top_stocks': config.stockbee_suite_industry_top_stocks,
            'industry_min_stocks': 3,  # Minimum stocks per industry
            'industry_history_period': max(10, int(50 * scale)),  # History needed
        },
        'stockbee_output_dir': f'results/screeners/stockbee_suite',
        'timeframe': timeframe
    }


def get_qullamaggie_suite_params_for_timeframe(config: UserConfiguration, timeframe: str) -> dict:
    """
    Get Qullamaggie Suite screener parameters for specific timeframe.
    
    Args:
        config: UserConfiguration object
        timeframe: 'daily', 'weekly', or 'monthly'
        
    Returns:
        Dictionary with Qullamaggie Suite parameters for the timeframe
    """
    return {
        'enable_qullamaggie_suite': config.qullamaggie_suite_enable,
        'timeframe': timeframe,
        'qullamaggie_suite': {
            # Core filtering criteria
            'rs_threshold': config.qullamaggie_suite_rs_threshold,
            'atr_rs_threshold': config.qullamaggie_suite_atr_rs_threshold,
            'range_position_threshold': config.qullamaggie_suite_range_position_threshold,
            'min_market_cap': config.qullamaggie_suite_min_market_cap,
            'min_price': config.qullamaggie_suite_min_price,
            'min_data_length': config.qullamaggie_suite_min_data_length,
            
            # Extension formatting thresholds
            'extension_warning': config.qullamaggie_suite_extension_warning,
            'extension_danger': config.qullamaggie_suite_extension_danger,
            
            # Moving averages periods (fixed for Qullamaggie methodology)
            'ema10_period': 10,
            'sma20_period': 20,
            'sma50_period': 50,
            'sma100_period': 100,
            'sma200_period': 200,
            'atr_period': 14,
            'range_period': 20,
            
            # RS timeframes to check (mapped to periods)
            'rs_timeframes': {
                '1w': ('daily', 5),    # 1 week
                '1m': ('daily', 20),   # 1 month  
                '3m': ('daily', 60),   # 3 months
                '6m': ('daily', 120)   # 6 months
            },
            
            'save_individual_files': True
        },
        'qullamaggie_output_dir': f'results/screeners/qullamaggie_suite',
        'timeframe': timeframe
    }


def get_adl_screener_params_for_timeframe(config: UserConfiguration, timeframe: str) -> dict:
    """
    Get ADL screener parameters for specific timeframe.
    
    Args:
        config: UserConfiguration object
        timeframe: 'daily', 'weekly', or 'monthly'
        
    Returns:
        Dictionary with ADL screener parameters
    """
    return {
        'enable_adl_screener': config.adl_screener_enable,
        'timeframe': timeframe,
        'adl_screener': {
            # Core ADL parameters
            'adl_lookback_period': config.adl_screener_lookback_period,
            'divergence_period': config.adl_screener_divergence_period,
            'breakout_period': config.adl_screener_breakout_period,
            
            # Signal thresholds
            'min_divergence_strength': config.adl_screener_min_divergence_strength,
            'min_breakout_strength': config.adl_screener_min_breakout_strength,
            'min_volume_avg': config.adl_screener_min_volume_avg,
            'min_price': config.adl_screener_min_price,
            
            # Output settings
            'save_individual_files': config.adl_screener_save_individual_files
        },
        'adl_output_dir': f'results/screeners/adl',
        'timeframe': timeframe
    }


def get_guppy_screener_params_for_timeframe(config: UserConfiguration, timeframe: str) -> dict:
    """
    Get Guppy GMMA screener parameters for specific timeframe with hierarchical flag checking.

    Args:
        config: UserConfiguration object
        timeframe: 'daily', 'weekly', or 'monthly'

    Returns:
        Dictionary with Guppy GMMA screener parameters, empty dict if disabled
    """
    # Check master enable flag first
    master_enabled = getattr(config, 'guppy_screener_enable', False)
    if not master_enabled:
        return {}  # Skip entirely if master disabled

    # Check timeframe-specific enable flag
    timeframe_attr = f'guppy_screener_{timeframe}_enable'
    timeframe_enabled = getattr(config, timeframe_attr, True)  # Default True for compatibility

    if not timeframe_enabled:
        return {}  # Skip if timeframe disabled

    # Both master AND timeframe flags are enabled - return full parameter set
    return {
        'enable_guppy_screener': True,  # Both flags are enabled
        'timeframe': timeframe,
        'guppy_screener': {
            # Moving average type (NEW - from user configuration)
            'ma_type': config.guppy_screener_ma_type,

            # EMA periods (NOW from user configuration, not hardcoded)
            'short_term_emas': config.guppy_screener_short_term_emas,
            'long_term_emas': config.guppy_screener_long_term_emas,
            
            # Signal detection thresholds
            'min_compression_ratio': config.guppy_screener_min_compression_ratio,
            'min_expansion_ratio': config.guppy_screener_min_expansion_ratio,
            'crossover_confirmation_days': config.guppy_screener_crossover_confirmation_days,
            'volume_confirmation_threshold': config.guppy_screener_volume_confirmation_threshold,
            
            # Base filtering criteria
            'min_price': config.guppy_screener_min_price,
            'min_volume_avg': config.guppy_screener_min_volume_avg,
            'min_data_length': config.guppy_screener_min_data_length,
            
            # Output settings
            'save_individual_files': config.guppy_screener_save_individual_files
        },
        'guppy_output_dir': f'results/screeners/guppy',
        'timeframe': timeframe
    }


def get_gold_launch_pad_params_for_timeframe(config: UserConfiguration, timeframe: str) -> Optional[dict]:
    """
    Get Gold Launch Pad screener parameters for specific timeframe with hierarchical flag checking.

    Args:
        config: UserConfiguration object
        timeframe: 'daily', 'weekly', or 'monthly'

    Returns:
        Dictionary with Gold Launch Pad screener parameters or None if disabled
    """
    # Check master flag first
    if not getattr(config, "gold_launch_pad_enable", False):
        return None

    # Check timeframe flag
    timeframe_flag = f"gold_launch_pad_{timeframe}_enable"
    if not getattr(config, timeframe_flag, True):
        return None

    return {
        'enable_gold_launch_pad': True,
        'timeframe': timeframe,
        'gold_launch_pad': {
            # Moving Average Configuration
            'ma_periods': config.gold_launch_pad_ma_periods,
            'ma_type': config.gold_launch_pad_ma_type,
            
            # Z-score Analysis Configuration
            'zscore_window': config.gold_launch_pad_zscore_window,
            'max_spread_threshold': config.gold_launch_pad_max_spread_threshold,
            
            # Slope Analysis Configuration
            'slope_lookback_pct': config.gold_launch_pad_slope_lookback_pct,
            'min_slope_threshold': config.gold_launch_pad_min_slope_threshold,
            
            # Price Proximity Configuration
            'price_proximity_stdv': config.gold_launch_pad_price_proximity_stdv,
            'proximity_window': config.gold_launch_pad_proximity_window,
            
            # Base Filters
            'min_price': config.gold_launch_pad_min_price,
            'min_volume': config.gold_launch_pad_min_volume,
            
            # Output settings
            'save_individual_files': config.gold_launch_pad_save_individual_files
        },
        'gold_launch_pad_output_dir': f'results/screeners/gold_launch_pad',
        'timeframe': timeframe
    }


def get_rti_screener_params_for_timeframe(config: UserConfiguration, timeframe: str) -> dict:
    """
    Get RTI screener parameters for specific timeframe.
    
    Args:
        config: UserConfiguration object
        timeframe: 'daily', 'weekly', or 'monthly'
        
    Returns:
        Dictionary with RTI screener parameters
    """
    # Timeframe scaling for RTI periods
    timeframe_scaling = {
        'daily': 1.0,
        'weekly': 0.2,  # 5 weeks = 1 month daily
        'monthly': 0.05  # 12 months = 1 year daily
    }
    
    scale = timeframe_scaling.get(timeframe, 1.0)
    
    return {
        'enable_rti': config.rti_enable,
        'timeframe': timeframe,
        'rti_screener': {
            # RTI Calculation Parameters (timeframe-scaled)
            'rti_period': max(5, int(config.rti_period * scale)),
            'rti_short_period': max(2, int(config.rti_short_period * scale)),
            'rti_swing_period': max(3, int(config.rti_swing_period * scale)),
            
            # Volatility Zone Thresholds
            'zone1_threshold': config.rti_zone1_threshold,
            'zone2_threshold': config.rti_zone2_threshold,
            'zone3_threshold': config.rti_zone3_threshold,
            'low_volatility_threshold': config.rti_low_volatility_threshold,
            
            # Range Expansion Parameters
            'expansion_multiplier': config.rti_expansion_multiplier,
            'consecutive_low_vol_bars': max(1, int(config.rti_consecutive_low_vol_bars * scale)),
            
            # Signal Detection Parameters (timeframe-scaled)
            'min_consolidation_period': max(1, int(config.rti_min_consolidation_period * scale)),
            'breakout_confirmation_period': max(1, int(config.rti_breakout_confirmation_period * scale)),
            
            # Base Filters
            'min_price': config.rti_min_price,
            'min_volume': config.rti_min_volume,
            
            # Output settings
            'save_individual_files': config.rti_save_individual_files
        },
        'rti_output_dir': f'results/screeners/rti',
        'timeframe': timeframe
    }


# get_market_pulse_params_for_timeframe function removed - obsolete after market pulse migration
