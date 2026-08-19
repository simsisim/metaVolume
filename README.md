# metaVolume — Volume Anomaly Screener

## What It Does

metaVolume identifies stocks that trade exceptionally high volume — days that stand out historically. It runs in two independent stages:

1. **Pre-processor** — reads years of OHLCV history (from `downloadData_v1`) and computes, for every ticker, its top volume days and volume milestones. Results are saved as baseline files.
2. **Post-processor (daily checker)** — every trading day, compares new volume data against the baseline and flags tickers whose volume enters their historical top positions.

The key design principle: the baseline is **computed once and never modified during daily runs**. New events accumulate in a separate incremental file that is safe to delete and replay.

---

## Data Flow

```
downloadData_v1/
  market_data/daily/*.csv          ← one CSV per ticker (OHLCV + marketCap)
          │
          ▼
  [PRE-PROCESSOR]  (run once, ticker_choice=0 recommended)
          │
          ▼
  results/pre/
    HVD_historical_daily.csv       ← read-only baseline (VOL checker reads this)
    HVE_historical_daily.csv
    HVE_historical_weekly.csv
    HVE_historical_monthly.csv
    baseline_metadata.json         ← cutoff date written after every HVD export
          │
          │    Data source (choose one):
          │      A) TradingView bulk file: tw_files/daily/all_stocks_LOHP_YYYY-MM-DD.csv
          │      B) Yahoo per-ticker CSVs: downloadData_v1/data/market_data/daily/
          │            │
          ▼            ▼
  [POST-PROCESSOR / VOL DAILY CHECKER]  (run every trading day)
          │
          ▼
  results/post/
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
│   ├── hvd_historical_exporter.py   ← exports HVD_historical_daily.csv + baseline_metadata.json
│   ├── yahoo_daily_adapter.py       ← Yahoo per-ticker CSV adapter for daily checker
│   ├── vol_daily_checker.py         ← daily volume checker (TradingView or Yahoo source)
│   └── ticker_card_generator.py     ← text summary cards per ticker
├── results/
│   ├── pre/                         ← pre-processor output (HVE+HVD together)
│   │   └── historical/              ← frozen HVE/HVD baseline (read by vol_daily_checker.py)
│   ├── post/                        ← post-processor (daily checker) output
│   └── ticker_cards/                ← per-ticker text summary cards
└── data/
    └── tickers/                     ← generated combined_tickers_*.csv files
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
| `HVE_pre_process` | TRUE |
| `HVE_post_process` | FALSE |
| `ticker_choice` | **0** (full universe — do this once and save the file) |

Equivalent shortcut: `python main.py --preset preprocess_full`

Output (authoritative baseline, read-only after this):
```
results/pre/historical/HVD_historical_daily.csv   ← VOL checker reads THIS file
results/pre/historical/HVE_historical_daily.csv
results/pre/historical/HVE_historical_weekly.csv
results/pre/historical/HVE_historical_monthly.csv
results/pre/historical/baseline_metadata.json     ← written automatically, records cutoff date
```

> **Note:** `results/pre/historical/` is the baseline `vol_daily_checker.py` reads directly — no copying elsewhere needed. Rebuild it (rerun `preprocess_full`) once a year after the new year's data rolls in.

---

### Mode 2: Incremental checker only (post-processor only)

Run every day. Runs once per entry in `TIMEFRAMES` (default `daily,weekly,monthly`)
— each timeframe tracks its own baseline, its own cutoff date, and its own
`current/` data source independently (see "Why per-timeframe cutoffs matter"
below). Daily can use TradingView or Yahoo; weekly/monthly always use Yahoo
(there's no weekly/monthly TradingView bulk-file concept in this codebase).

| Setting | Value |
|---|---|
| `HVE_pre_process` | FALSE |
| `HVE_post_process` | TRUE |
| `VOL_checker_data_source` | `tradingview` or `yahoo` (daily only) |
| `ticker_choice` | any (2 = NASDAQ-100, 1 = S&P500, 0 = full universe, etc.) |

Equivalent shortcut: `python main.py --preset postprocess`

Output (per timeframe, under `results/post/{daily,weekly,monthly}/`):
```
results/post/daily/HVD_incremental.csv    ← new events only, safe to delete and replay
results/post/daily/daily_log.csv          ← all monitored tickers, hit=0/1 per period
results/post/daily/vol_check_results.csv  ← cumulative hits log
results/post/daily/snapshots/             ← one snapshot file per period
results/post/weekly/  (same files)
results/post/monthly/ (same files)
```

To force reprocess a date: set `VOL_checker_tw_since_date,YYYY-MM-DD` (one day before the target).
Reset to blank after a successful run.

#### Why per-timeframe cutoffs matter

`baseline_metadata.json`'s `baseline_as_of_date` is a dict keyed by
timeframe, not one shared date. A monthly bar for the currently-open month
naturally carries the latest trading day within that month — so monthly's
true cutoff is often weeks ahead of daily's. Pooling them into a single
cutoff would let monthly's more-current date mask real gaps in daily's
coverage (daily days would look "already covered" when they weren't).
Each `VolChecker` instance only ever reads its own timeframe's cutoff.

#### How pre and post compare and evolve (important)

`pre` and `post` are read fresh from disk **every single post run** — `pre`'s
baseline is never "seeded once" into post and then forgotten about; it's
re-read every time, it just doesn't change between reads.

At the start of every `VolChecker.run()`:
1. `load_hve_baseline()` re-reads `results/pre/historical/HVE_historical_{timeframe}.csv`
   — `pre`'s output, **read-only**, never written to by post.
2. `load_hve_incremental()` re-reads `results/post/{timeframe}/HVE_incremental.csv`
   — post's own ledger, growing across every previous post run.

For each new day's volume, the comparison is:
```
combined_max = max(pre's stored record, everything post has found since the last pre rebuild)
new_vol > combined_max  →  new HVE hit
```
A hit gets appended in memory to `hve_incremental_dict`, and at the end of
the run `save_hve_incremental()` writes the whole updated set back to
`HVE_incremental.csv` (a full overwrite each time, not an on-disk append —
but since the file is loaded back in at the start of the next run, it
behaves as an accumulating ledger).

**Concretely, across runs:**
- **Run 1** (right after a `pre` rebuild): `HVE_incremental.csv` is empty,
  so the comparison is effectively "new data vs. `pre`'s baseline alone."
- **Run 2**: loads `pre`'s baseline again (unchanged) **and** Run 1's
  discoveries → a ticker that set a new record in Run 1 must now beat
  *that* record, not fall back to `pre`'s older one.
- **Run N**: same pattern — `pre` stays frozen, `HVE_incremental.csv` keeps
  growing, the effective threshold per ticker is always the max of both.

**`pre` never absorbs what `post` finds.** They only reconverge when you
manually rerun `preprocess_full` — a completely independent full rescan of
the underlying market data (not a merge of `pre` + `HVE_incremental.csv`)
that overwrites `HVE_historical_{timeframe}.csv` from scratch. At that
point `HVE_incremental.csv` is redundant (its discoveries are already
baked into the fresh baseline), so **after every `preprocess_full` rebuild,
clear each timeframe's `results/post/{timeframe}/HVD_incremental.csv`,
`HVE_incremental.csv`, and `last_processed.txt`** — otherwise stale entries
linger uselessly (harmless, since they'd never win a `max()` comparison
against the fresh baseline, but they bloat the incremental files for no
reason). This is still a manual step, not automated.

`HVE_{timeframe}.csv` (the per-ticker summary — see "Output Files
Reference") follows the identical logic for display: per ticker, whichever
is more current, `pre`'s stored record or the newest `HVE_incremental.csv`
entry.

---

## Daily Checker Data Sources

### Source A: TradingView bulk export

The original source. One CSV file per trading day covering all tickers.

**Directory:** `../downloadData_v1/data/tw_files/daily/`  
**Filename format:** `*YYYY-MM-DD*.csv` (date anywhere in filename)

**Required columns:** `Symbol`, `Open 1 day`, `High 1 day`, `Low 1 day`, `Price`, `Volume 1 day`

**Optional column:** `Mkt cap` — add it to your TradingView export template to enable market-cap output. When present, the value is captured at the export date (= detection date), which is the most accurate market cap for each event.

Multiple files for the same date are merged (e.g. one for stocks, one for ETFs).

**Config keys:**
```
VOL_checker_data_source,tradingview
VOL_checker_tw_files_dir,../downloadData_v1/data/tw_files/daily/
VOL_checker_tw_since_date,                     ← blank = auto from state file
```

---

### Source B: Yahoo Finance per-ticker CSVs

Uses the same per-ticker OHLCV files that generated the baseline — no extra export needed.
One file per ticker (`AAPL.csv`, `MSFT.csv`, …) with one row per trading day.

**Key design:** all ticker files are opened once and all pending dates are extracted in a single pass — efficient even on Colab/Google Drive.

**Cutoff protection:** the checker reads `baseline_metadata.json` (written automatically after every HVD export) to determine the last date already covered by *that timeframe's* baseline. It refuses to process any date on or before that cutoff, preventing double-counting of historical data. If metadata is missing it falls back to scanning `HVD_historical_{timeframe}.csv` for the maximum date.

**Market cap:** the `marketCap` column in Yahoo per-ticker files is a snapshot taken at download time, replicated across all rows. It reflects the current cap rather than the historical cap at the event date — adequate for large-company filtering, labeled `market_cap` in output.

**Directory:** resolved via the same `YF_daily_data_files_local` / `YF_weekly_data_files_local` / `YF_monthly_data_files_local` (and `_colab`) settings the pre-processor already uses — no separate vol-checker path setting.

**Config keys:**
```
VOL_checker_data_source,yahoo
```

---

## Output Columns (hits files)

| Column | Description | Source |
|---|---|---|
| `ticker` | Stock symbol | both |
| `check_date` | Date of the volume event | both |
| `new_volume` | Volume on that date | both |
| `price_at_event` | Closing price on that date (exact) | both |
| `market_cap` | Market cap at detection (TW: exact; Yahoo: latest snapshot) | optional |
| `entered_top_n` | TRUE if volume rank ≤ `VOL_checker_top_n_flag` | both |
| `rank` | Position in the all-time top-N list (1 = all-time high) | both |
| `displaced_vol` | Volume of the record being pushed out of top-N | both |
| `displaced_date` | Date of the displaced record | both |
| `days_since_top1` | Days since the all-time rank-1 event | both |

> Tip: sort the output Excel by `market_cap` descending to focus on large companies, then by `rank` ascending to find the most significant volume events.

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

# Run daily checker (TradingView source, NASDAQ-100)
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

# Cell 3A: daily checker — TradingView source
!python main.py --preset postprocess --ticker-choice 2

# Cell 3B: daily checker — Yahoo source (set VOL_checker_data_source=yahoo in user_data.csv)
!python main.py --preset postprocess --ticker-choice 2
```

### Colab — Python cells (no `!`, more flexible)

```python
from main import main

# Generate baseline for NASDAQ-100
main(preset='preprocess', config_override={'ticker_choice': '2'})

# Daily checker — TradingView source
main(preset='postprocess', config_override={'ticker_choice': '2'})

# Daily checker — Yahoo source
main(preset='postprocess', config_override={
    'ticker_choice': '2',
    'vol_checker_data_source': 'yahoo'
})

# Force reprocess a specific date
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

# ── CELL 3B: EVERY TRADING DAY — TradingView source ───────────────────────────
# Drop your TradingView export in:
#   downloadData_v1/data/tw_files/daily/all_stocks_LOHP_YYYY-MM-DD.csv
# Then run:
!python main.py --preset postprocess --ticker-choice 2

# ── CELL 3C: EVERY TRADING DAY — Yahoo source (no TradingView export needed) ──
# Set VOL_checker_data_source=yahoo in user_data.csv, then run:
!python main.py --preset postprocess --ticker-choice 2

# ── CELL 4: View results ───────────────────────────────────────────────────────
import pandas as pd

# Today's hits — filter large caps and sort by rank
hits = pd.read_csv('results/post/daily/vol_check_results.csv')
big = hits[hits['entered_top_n'] == True].copy()
if 'market_cap' in big.columns:
    big = big.sort_values(['market_cap', 'rank'], ascending=[False, True])
print(big.tail(20).to_string())

# Full daily log (all monitored tickers, hit=0/1)
log = pd.read_csv('results/post/daily/daily_log.csv')
print(log[log['hit'] == 1].tail(20).to_string())
```

---

## Output Files Reference

Paths below are shown for `daily`; the identical set exists under
`results/post/weekly/` and `results/post/monthly/` for those timeframes.

| File | Updated by | Purpose |
|---|---|---|
| `results/pre/historical/HVD_historical_{timeframe}.csv` | Pre-processor | HVD baseline — top-N volume days per ticker. **Read-only** during checker runs |
| `results/pre/historical/HVE_historical_*.csv` | Pre-processor | HVE milestones per ticker per timeframe |
| `results/pre/historical/baseline_metadata.json` | Pre-processor | Per-timeframe cutoff dates for cutoff protection |
| `results/post/daily/HVD_incremental.csv` | Checker | New events since baseline. Safe to delete |
| `results/post/daily/daily_log.csv` | Checker | All monitored tickers per period, `hit` column |
| `results/post/daily/vol_check_results.csv` | Checker | Cumulative hits (beat threshold) |
| `results/post/daily/snapshots/vol_check_YYYY-MM-DD.csv` | Checker | Hits for a single period |
| `results/post/daily/last_processed.txt` | Checker | State: last processed date |

---

## Recovering from a Bad Run

If the checker produced wrong results (wrong ticker_choice, bug, etc.), for
whichever timeframe was affected:

1. Delete the incremental file (baseline is untouched):
   ```bash
   rm results/post/daily/HVD_incremental.csv
   rm results/post/daily/vol_check_results.csv
   rm results/post/daily/daily_log.csv
   ```

2. Force reprocess by setting `VOL_checker_tw_since_date` one day before the target date in `user_data.csv`, then re-run.

3. Alternatively use `--since-date`:
   ```bash
   python main.py --preset postprocess --ticker-choice 2 --since-date 2026-05-21
   ```

The HVD baseline (`results/pre/historical/HVD_historical_{timeframe}.csv`) is **never modified** by the checker — it is always safe.

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
