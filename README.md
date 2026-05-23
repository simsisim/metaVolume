# metaVolume — Volume Anomaly Screener

## What It Does

metaVolume identifies stocks that trade exceptionally high volume — days that stand out historically. It runs in two independent stages:

1. **Pre-processor** — reads years of OHLCV history (from `downloadData_v1`) and computes, for every ticker, its top volume days and volume milestones. Results are saved as baseline files.
2. **Post-processor (daily checker)** — every trading day, compares a new TradingView bulk export against the baseline and flags tickers whose volume enters their historical top positions.

The key design principle: the baseline is **computed once and never modified during daily runs**. New events accumulate in a separate incremental file that is safe to delete and replay.

---

## Data Flow

```
downloadData_v1/
  market_data/daily/*.csv          ← one CSV per ticker (OHLCV history)
          │
          ▼
  [PRE-PROCESSOR]  (run once, ticker_choice=0 recommended)
          │
          ▼
  results/hve_results/
    HVD_historical_daily.csv       ← read-only baseline (VOL checker reads this)
    HVE_historical_daily.csv
    HVE_historical_weekly.csv
    HVE_historical_monthly.csv
          │
          │    TW bulk file (daily export from TradingView)
          │    tw_files/daily/all_stocks_LOHP_YYYY-MM-DD.csv
          │            │
          ▼            ▼
  [POST-PROCESSOR / VOL DAILY CHECKER]  (run every trading day)
          │
          ▼
  results/vol_top20/
    HVD_incremental.csv            ← new events since baseline (safe to delete)
    daily_log.csv                  ← every monitored ticker, hit=0/1 per day
    vol_check_results.csv          ← cumulative hits log
    daily/vol_check_YYYY-MM-DD.csv ← per-day snapshot
```

---

## Project Structure

```
metaVolume/
├── main.py                          ← single entry point
├── user_input/                      ← ALL user-editable files live here
│   ├── user_data.csv                ← main configuration
│   ├── tradingview_universe.csv     ← full ticker universe (~6348 tickers)
│   ├── test_tickers.csv             ← choice 8: test tickers (AMD TXN NVDA)
│   ├── indexes_tickers.csv          ← choice 5: QQQ SPY IWM + sectors
│   ├── portofolio_tickers.csv       ← choice 6: personal holdings
│   └── etf_tickers.csv              ← choice 7: major ETFs
├── src/
│   ├── config.py                    ← path resolution, environment detection
│   ├── user_defined_data.py         ← user_data.csv parser → UserConfiguration
│   ├── data_reader.py               ← loads OHLCV CSV files per timeframe
│   ├── unified_ticker_generator.py  ← builds combined_tickers_*.csv files
│   ├── hve_screener.py              ← HVE calculation (expanding cummax)
│   ├── hvd_screener.py              ← HVD calculation (top-N by magnitude)
│   ├── hve_historical_exporter.py   ← exports HVE_historical_*.csv
│   ├── hvd_historical_exporter.py   ← exports HVD_historical_daily.csv
│   ├── vol_daily_checker.py         ← daily TW file vs HVD baseline
│   └── ticker_card_generator.py     ← text summary cards per ticker
├── results/
│   ├── hve_results/                 ← pre-processor output (baseline lives here)
│   └── vol_top20/                   ← post-processor output
├── data/
│   └── tickers/                     ← generated combined_tickers_*.csv files
└── HVE_data_for_preload/            ← legacy preload files (not used by checker)
```

---

## Core Concepts: HVE vs HVD

### HVE — Highest Volume Ever (milestone tracker)

Answers: *"On which days did this stock set a new all-time volume record?"*

- Volume must be higher than **all previous days** (expanding maximum / cummax)
- HVE events form an **ascending sequence** — each event is larger than the one before
- Tells you the history of volume milestones: when did volume really break out?

Example (NVDA):
- 2020-03-18: 200M → new record ✅
- 2021-11-19: 350M → new record ✅
- 2023-05-25: 1.54B → new record ✅
- 2024-06-10: 900M → NOT a record (lower than 1.54B) ❌

### HVD — Highest Volume Days (top-N ranking)

Answers: *"What are the top 20 highest volume days ever for this stock, ranked by size?"*

- Ranks **all days by volume**, keeps the biggest N (e.g. top 20)
- Includes high-volume days that were **not** new records at the time
- Used by the daily checker: *"Is today's volume big enough to enter the top 20?"*

Example (NVDA top 5):
1. 2023-05-25: 1.54B
2. 2024-03-08: 950M  ← high volume day, NOT an HVE event
3. 2024-06-10: 900M  ← high volume day, NOT an HVE event
4. 2022-08-15: 800M
5. 2021-11-19: 350M

### Key difference

| | HVE | HVD |
|---|---|---|
| Question | Was this a new record **at the time**? | Is this one of the **biggest days ever**? |
| Sequence | Ascending (each beats the last) | Ranked by magnitude |
| Contains each other? | Partially | HVD contains the largest HVE events, but old small HVE events may be displaced; HVD also contains non-HVE high-volume days |

For the **daily checker**, HVD is the right tool — you want to know if today is one of the biggest days ever by size, not just whether it's a new record.

---

## Run Modes — user_data.csv settings

### Mode 1: Generate historical baseline files (pre-processor only)

Run this **once** (ideally with `ticker_choice=0` for the full universe) to build the HVD/HVE baseline.
The baseline covers all tickers, so the daily checker can filter to any subset without missing history.

| Setting | Value |
|---|---|
| `HVE_enable` | TRUE |
| `HVD_historical_export` | TRUE |
| `HVE_historical_export` | TRUE |
| `VOL_checker_enable` | FALSE |
| `ticker_choice` | **0** (full universe — do this once and save the file) |

Output (authoritative baseline, read-only after this):
```
results/hve_results/HVD_historical_daily.csv   ← VOL checker reads THIS file
results/hve_results/HVE_historical_daily.csv
results/hve_results/HVE_historical_weekly.csv
results/hve_results/HVE_historical_monthly.csv
```

> **Note:** `HVE_data_for_preload/` contains older copies — the VOL checker does NOT read from there.

---

### Mode 2: Daily checker only (post-processor only)

Run every trading day after dropping a new TradingView bulk export file.
Set `ticker_choice` to any subset — the full-universe baseline covers all tickers.

| Setting | Value |
|---|---|
| `HVE_enable` | FALSE |
| `HVD_historical_export` | FALSE |
| `HVE_historical_export` | FALSE |
| `VOL_checker_enable` | TRUE |
| `ticker_choice` | any (2 = NASDAQ-100, 1 = S&P500, 0 = full universe, etc.) |

Output:
```
results/vol_top20/HVD_incremental.csv    ← new events only, safe to delete and replay
results/vol_top20/daily_log.csv          ← all monitored tickers, hit=0/1 per day
results/vol_top20/vol_check_results.csv  ← cumulative hits log
results/vol_top20/daily/                 ← one snapshot file per trading day
```

To force reprocess a date: set `VOL_checker_tw_since_date,YYYY-MM-DD` (one day before the target).
Reset to blank after a successful run.

---

## Ticker Choice Values

| Choice | Tickers | Source | Count |
|---|---|---|---|
| 0 | TradingView Universe | `tradingview_universe.csv` | ~6348 |
| 1 | S&P 500 | boolean column in universe | ~503 |
| 2 | NASDAQ 100 | boolean column in universe | ~100 |
| 3 | All NASDAQ | boolean column in universe | ~3300 |
| 4 | Russell 1000 | boolean column in universe | ~1008 |
| 5 | Indexes | `indexes_tickers.csv` | 16 |
| 6 | Portfolio | `portofolio_tickers.csv` | custom |
| 7 | ETFs | `etf_tickers.csv` | 23 |
| 8 | Test | `test_tickers.csv` | 3 (AMD TXN NVDA) |

Combinations: `ticker_choice = 1-2` processes S&P 500 + NASDAQ 100 together.

---

## Commands

### Local (terminal)

```bash
# Generate full historical baseline (run once — takes time for choice=0)
python main.py --preset preprocess_full

# Generate baseline for a specific ticker group
python main.py --preset preprocess --ticker-choice 2

# Run daily checker for NASDAQ-100
python main.py --preset postprocess --ticker-choice 2

# Force reprocess a date (e.g. to fix a bad run)
python main.py --preset postprocess --ticker-choice 2 --since-date 2026-05-21

# Show all options
python main.py --help
```

### Colab — shell cells (`!`)

```python
# Cell 1: setup
!git clone https://github.com/simsisim/metaVolume.git
%cd /content/drive/MyDrive/_invest2024_py_run/run_python/metaVolume

# Cell 2: generate baseline
!python main.py --preset preprocess_full

# Cell 3: daily checker
!python main.py --preset postprocess --ticker-choice 2
```

### Colab — Python cells (no `!`, more flexible)

```python
from main import main

# Generate baseline for NASDAQ-100
main(preset='preprocess', config_override={'ticker_choice': '2'})

# Daily checker for NASDAQ-100
main(preset='postprocess', config_override={'ticker_choice': '2'})

# Daily checker and force reprocess a specific date
main(preset='postprocess', config_override={
    'ticker_choice': '2',
    'vol_checker_tw_since_date': '2026-05-21'
})
```

### Priority order for settings

```
CLI args  >  --preset  >  config_override dict  >  user_data.csv
```

---

## Colab Quick Start (copy-paste notebook)

```python
# ── CELL 1: Mount Drive and navigate ──────────────────────────────────────────
from google.colab import drive
drive.mount('/content/drive')
%cd /content/drive/MyDrive/_invest2024_py_run/run_python/metaVolume

# ── CELL 2: Install dependencies ──────────────────────────────────────────────
!pip install -q pandas numpy yfinance mplfinance

# ── CELL 3A: FIRST TIME — generate full baseline (slow, run once) ─────────────
!python main.py --preset preprocess_full

# ── CELL 3B: EVERY TRADING DAY — run daily checker ────────────────────────────
# Drop your TradingView export in:
#   downloadData_v1/data/tw_files/daily/all_stocks_LOHP_YYYY-MM-DD.csv
# Then run:
!python main.py --preset postprocess --ticker-choice 2

# ── CELL 4: View results ───────────────────────────────────────────────────────
import pandas as pd

# Today's hits
hits = pd.read_csv('results/vol_top20/vol_check_results.csv')
print(hits[hits['entered_top_n'] == True].tail(20).to_string())

# Full daily log (all monitored tickers, hit=0/1)
log = pd.read_csv('results/vol_top20/daily_log.csv')
print(log[log['hit'] == 1].tail(20).to_string())
```

---

## TradingView Export File

The daily checker reads TradingView bulk export CSV files. Place them in:
```
../downloadData_v1/data/tw_files/daily/
```

Required filename format: `*YYYY-MM-DD*.csv` (date anywhere in filename)

Required columns: `Symbol`, `Open 1 day`, `High 1 day`, `Low 1 day`, `Price`, `Volume 1 day`

Multiple files for the same date are merged (e.g. one for stocks, one for ETFs).

---

## Output Files Reference

| File | Updated by | Purpose |
|---|---|---|
| `results/hve_results/HVD_historical_daily.csv` | Pre-processor | HVD baseline — top-N volume days per ticker. **Read-only** during daily runs |
| `results/hve_results/HVE_historical_*.csv` | Pre-processor | HVE milestones per ticker per timeframe |
| `results/vol_top20/HVD_incremental.csv` | Daily checker | New events since baseline. Safe to delete |
| `results/vol_top20/daily_log.csv` | Daily checker | All monitored tickers per day, `hit` column |
| `results/vol_top20/vol_check_results.csv` | Daily checker | Cumulative hits (beat threshold) |
| `results/vol_top20/daily/vol_check_YYYY-MM-DD.csv` | Daily checker | Hits for a single day |
| `results/vol_top20/last_processed.txt` | Daily checker | State: last processed TW date |

---

## Recovering from a Bad Run

If the daily checker produced wrong results (wrong ticker_choice, bug, etc.):

1. Delete the incremental file (baseline is untouched):
   ```bash
   rm results/vol_top20/HVD_incremental.csv
   rm results/vol_top20/vol_check_results.csv
   rm results/vol_top20/daily_log.csv
   ```

2. Force reprocess by setting `VOL_checker_tw_since_date` one day before the target date in `user_data.csv`, then re-run.

3. Alternatively use `--since-date`:
   ```bash
   python main.py --preset postprocess --ticker-choice 2 --since-date 2026-05-21
   ```

The HVD baseline (`results/hve_results/HVD_historical_daily.csv`) is **never modified** by the daily checker — it is always safe.

---

## HVE Screening Logic

1. **HVE Detection**: For each ticker, identifies all dates where volume reached a new all-time high (expanding cummax from `HVE_start_date`)

2. **Metrics Calculated**:
   - HVE Count: Number of times a new volume record was set
   - Latest HVE Date: Most recent milestone
   - Days Since HVE: Days elapsed since latest milestone
   - HVE_1Y: Whether an HVE event occurred in the last 365 days

3. **HV1Y**: Highest volume within a rolling 365-day window — separate from HVE, tracks recent volume peaks even if not all-time records

---

## Requirements

```
pandas
numpy
yfinance
pathlib (stdlib)
```

Install:
```bash
pip install pandas numpy yfinance
```
