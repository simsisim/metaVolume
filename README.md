# Highest Volume Ever (HVE) Screener

A Python tool for identifying stocks that have experienced their highest volume ever within a specified time window. The screener analyzes multiple timeframes (daily, weekly, monthly) and generates comprehensive reports with visualizations.

## Features

- **Multi-Timeframe Analysis**: Analyze daily, weekly, and monthly data
- **HVE Detection**: Identify all instances of highest volume ever for each ticker
- **Scoring System**: Rank tickers based on recency, frequency, and volume characteristics
- **Visualizations**: Generate charts showing HVE events on price and volume data
- **Excel Reports**: Export detailed results with multiple sheets and formatting
- **Configurable**: Easy-to-use YAML configuration file

## Project Structure

```
metaVolume/
├── main.py                  # Main execution script
├── config.yaml              # Configuration file
├── requirements.txt         # Python dependencies
├── README.md               # This file
└── src/
    ├── data_loader.py      # Data loading from metaData_v1
    ├── hve_screener.py     # HVE detection logic
    ├── visualization.py    # Chart generation
    └── excel_exporter.py   # Excel export functionality
```

## Installation

1. Install required Python packages:
```bash
pip install -r requirements.txt
```

2. Update `config.yaml` with your paths:
   - Set `metadata_v1_path` to your metaData_v1 installation
   - Set `ticker_file` to your ticker list file

## Configuration

Edit `config.yaml` to customize the analysis:

```yaml
data_source:
  metadata_v1_path: "/path/to/metaData_v1"
  ticker_file: "combined_tickers_choice_0.csv"
  user_choice: 0

analysis:
  limit_hist_search_years: 4  # Limit to recent N years
  timeframes:
    - daily
    - weekly
    - monthly

output:
  results_dir: "results"
  create_timeframe_subdirs: true
```

## Usage

Run the screener:
```bash
python main.py
```

Or specify a custom config file:
```bash
python main.py --config my_config.yaml
```

## Output

The screener generates the following outputs in the `results/` directory:

### For Each Timeframe:
- `hve_results_{timeframe}.xlsx` - Detailed Excel report with:
  - HVE_Summary: Overview of all tickers with HVE events
  - HVE_Details: Detailed information for each HVE event
  - Statistics: Analysis statistics

- `hve_summary_{timeframe}.png` - Summary chart showing top tickers

- `charts_{timeframe}/` - Individual charts for each ticker showing:
  - Price history
  - Volume bars (HVE events highlighted in red)
  - Annotations for latest HVE

### Combined:
- `hve_results_combined.xlsx` - All timeframes in a single file

## HVE Screening Logic

1. **HVE Detection**: For each ticker, the screener identifies all dates where volume reached a new all-time high

2. **Metrics Calculated**:
   - HVE Count: Number of times HVE occurred
   - Latest HVE Date: Most recent HVE event
   - Days Since HVE: Days elapsed since latest HVE
   - Volume Ratio: Current volume as % of max volume

3. **Scoring System** (0-100 points):
   - **Recency Score (0-50 pts)**: Recent HVE events score higher
     - Within 30 days: 50 points
     - 30-90 days: 25-50 points (decay)
     - 90-365 days: 5-25 points (decay)
     - Beyond 365 days: 0-5 points (decay)

   - **Frequency Score (0-30 pts)**: More HVE events = higher score
     - 3 points per HVE event (capped at 30)

   - **Volume Score (0-20 pts)**: Current volume relative to max
     - Based on current volume as % of max volume

## Example Results

The screener will log progress and display top results:

```
Found 127 tickers with HVE events
Top 5 by score:
  1. AAPL: Score=85.23, Days Since HVE=15, HVE Count=8
  2. MSFT: Score=78.45, Days Since HVE=23, HVE Count=6
  3. NVDA: Score=72.11, Days Since HVE=8, HVE Count=12
  ...
```

## Troubleshooting

### No data loaded
- Verify `metadata_v1_path` is correct in config.yaml
- Ensure ticker file exists in metaData_v1/data/tickers/
- Check that market data exists for the specified timeframes

### Import errors
- Install all requirements: `pip install -r requirements.txt`
- Ensure metaData_v1 is properly installed

### Chart generation fails
- Check matplotlib installation
- Verify write permissions in output directory

## Reference

This tool is inspired by and integrates with the metaData_v1 project structure, particularly the pattern used in `pvb_screener.py`.

## Log File

All execution details are logged to `hve_screener.log` for debugging and audit purposes.
