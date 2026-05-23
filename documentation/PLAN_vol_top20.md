# Implementation Plan — Volume Top-20 Check

## Overview

Two independently runnable steps:

| Step | Name | Input | Output | New code? |
|---|---|---|---|---|
| 1 | **Historical generator** | YF per-ticker CSVs | `HVD_historical_daily.csv` (baseline) | **None — already built** |
| 2 | **Daily checker** | baseline + TW bulk files | `vol_check_results.csv` | **One new module** |

---

## What Is Already Built (Do Not Rewrite)

### Step 1 is the existing HVD pipeline

The following chain already exists and produces the exact baseline format needed:

```
DataReader.read_batch_data()          src/data_reader.py
    ↓  reads YF per-ticker CSVs in batches of 100
HVDScreener.screen_batch()            src/hvd_screener.py
    ↓  finds top-N volume days per ticker, sorted by volume descending
export_hvd_historical()               src/hvd_historical_exporter.py
    ↓  writes wide-format CSV
HVE_data_for_preload/HVD_historical_daily.csv
    Symbol, timeframe, HVD_date_1, HVD_vol_1, HVD_date_2, HVD_vol_2, ..., HVD_date_N, HVD_vol_N
```

**Only change needed**: set `HVD_historical_max_events = 20` in `user_data.csv` (currently defaults to 10).
This is already a config parameter in `HVDScreener.__init__(max_events=...)`.
No new files, no new functions.

### Step 2 reuses these for baseline loading

```
load_hvd_preload_data()               src/hve_preloader.py
convert_hvd_wide_to_results_format()  src/hve_preloader.py
```

These already read `HVD_historical_daily.csv` and return a dict of events per ticker.

---

## File Structure Reference

### TW bulk file (input to Step 2)
One file per trading day, exported manually from TradingView UI.
Location: `downloadData_v1/data/tw_files/daily/all_stocks_OHLCV_2025-09-30.csv`

```
Symbol, Description, ..., High 1 day, Low 1 day, Open 1 day, Price, Volume 1 day
UPC,    ...,              4.605,      4.20,       4.58,       4.20,  23002
BRK.A,  ...,              755323.99,  744000,     746377.67,  754200, 338
```

Key differences from YF files:
- Date is **not in the file** — extracted from filename (`*_2025-09-30.csv`)
- Close = column `Price` (not `Close`)
- Volume = column `Volume 1 day` (not `Volume`)
- One row per ticker (not one row per date)
- `BRK.A` → convert dot to dash → `BRK-A`
- Tickers with `/` → skip (preferred shares)
- Multiple files per date possible (stocks + ETFs — merge before checking)
- ~6,700 stocks + ~4,800 ETFs per file

`parse_tw_bulk_file()` in `downloadData_v1/src/get_tradingview_data.py` already handles
all of the above. Port it into metaVolume (copy, do not import across projects).

### Baseline file (output of Step 1, input of Step 2)
`HVE_data_for_preload/HVD_historical_daily.csv` — already exists, produced by HVD pipeline.

```
Symbol, timeframe, HVD_date_1, HVD_vol_1, HVD_date_2, HVD_vol_2, ..., HVD_date_20, HVD_vol_20
AAPL,   daily,     2024-08-05, 337150800,  2024-11-15, 185000000, ..., 2020-03-20,   89000000
```

- Rank 1 (`HVD_vol_1`) = highest volume ever (all-time high)
- Rank 20 (`HVD_vol_20`) = threshold — new bar must beat this to enter top-20
- Sorted descending by volume within each row (not by date)

### Daily checker output
`results/vol_top20/vol_check_results.csv`

```
ticker, check_date,  new_volume,  new_close, entered_top_n, rank, displaced_vol, displaced_date, days_since_top1
AAPL,   2025-09-30,  195000000,  227.50,    True,          2,    89000000,      2020-03-20,     399
NVDA,   2025-09-30,  320000000,  125.40,    True,          1,    337150800,     2024-08-05,     0
MSFT,   2025-09-30,   45000000,  415.20,    False,         -,    -,             -,              -
```

Column meanings:
- `entered_top_n`: True if new volume qualifies within top `top_n_flag` positions (e.g., top 6)
- `rank`: where in the top-20 the new volume lands (1 = all-time high)
- `displaced_vol / displaced_date`: the entry dropped out of top-20 (rank 21 after insert)
- `days_since_top1`: days since all-time volume high (HVD_date_1) was set

---

## What Needs to Be Written

### One new module: `src/vol_daily_checker.py`

```
class VolDailyChecker:

    __init__(config, top_n_flag=6)
        baseline_path  → HVE_data_for_preload/HVD_historical_daily.csv
        tw_files_dir   → path to tw_files/daily/ (from config)
        output_path    → results/vol_top20/vol_check_results.csv
        top_n_flag     → flag if new volume enters this many positions (default 6)

    load_baseline()
        calls load_hvd_preload_data()               ← REUSE hve_preloader.py
        calls convert_hvd_wide_to_results_format()  ← REUSE hve_preloader.py
        builds: baseline_dict = { ticker: [(vol, date), ...] }  ranked vol desc
        builds: threshold_dict = { ticker: vol_at_rank_20 }     last position

    find_tw_files_since(last_processed_date)        ← NEW ~20 lines
        scan tw_files_dir for *_YYYY-MM-DD.csv
        group by date (stocks file + ETFs file share same date)
        filter to dates > last_processed_date
        return sorted list: [(date, [file_path, ...]), ...]  chronological

    parse_tw_file(file_path, file_date)             ← PORT from downloadData_v1
        read CSV                                       get_tradingview_data.py
        extract: Symbol → clean (dot→dash, skip slash)  parse_tw_bulk_file()
        extract: Volume 1 day, Price, Open 1 day, High 1 day, Low 1 day
        return: { ticker: {date, open, high, low, close, volume} }

    check_and_update(ticker_data, file_date)        ← NEW ~40 lines
        for each ticker in ticker_data:
            new_vol = ticker_data[ticker]['volume']
            if new_vol > threshold_dict[ticker]:        # beats rank-20
                insert new entry into baseline_dict[ticker]
                re-sort by volume desc
                keep only top 20, drop rank 21+
                find rank of new entry
                record hit if rank <= top_n_flag

    run(since_date=None)                            ← NEW ~30 lines
        load_baseline()
        files = find_tw_files_since(since_date or last_processed_date)
        all_hits = []
        for date, file_paths in files:              # chronological order
            ticker_data = {}
            for fp in file_paths:                   # merge stocks + ETFs
                ticker_data.update(parse_tw_file(fp, date))
            hits = check_and_update(ticker_data, date)
            all_hits.extend(hits)
            # baseline_dict updated in memory — next day checks updated baseline
        save updated baseline → HVD_historical_daily.csv
        save_results(all_hits) → vol_check_results.csv
        save last_processed_date → state file
```

Estimated size: ~150 lines total.

---

## Config Additions (`user_data.csv`)

```
# Existing — just change the value:
HVD_historical_max_events, 20        # was 10 → store top-20 (not top-10)

# New:
vol_checker_enable,        TRUE       # run the daily checker (Step 2)
vol_checker_top_n_flag,    6          # flag if new volume enters top-6
vol_checker_tw_since_date,            # blank = auto from state file
                                      # YYYY-MM-DD = process only files after this date
```

---

## New Files

```
metaVolume/
├── src/
│   └── vol_daily_checker.py          ← NEW (Step 2 only, ~150 lines)
│
└── results/
    └── vol_top20/
        ├── vol_check_results.csv     ← NEW output
        └── last_processed.txt        ← NEW state file (tracks last TW date processed)
```

The baseline file (`HVE_data_for_preload/HVD_historical_daily.csv`) already exists —
Step 1 is just the existing HVD pipeline run with `max_events=20`.

---

## Execution Flow

### First time (bootstrap) — Step 1
```
user_data.csv:
  HVD_historical_export     = TRUE
  HVD_historical_max_events = 20

python main.py  (existing flow, no changes)
→ reads market_data/daily/ for all tickers
→ computes top-20 per ticker via HVDScreener
→ writes HVE_data_for_preload/HVD_historical_daily.csv
→ done (~5-10 min for 5k tickers)
```

### Daily run — Step 2
```
user_data.csv:
  vol_checker_enable     = TRUE
  vol_checker_top_n_flag = 6
  vol_checker_tw_since_date =   (blank = auto)

python main.py  (or python -m src.vol_daily_checker)
→ loads HVD_historical_daily.csv baseline
→ finds unprocessed TW files since last_processed.txt date
→ processes them in date order (Mon → Tue → Wed if gap exists)
→ saves updated baseline + vol_check_results.csv
→ done (~1-2 min)
```

### Gap fill (missed days — Mon+Tue+Wed TW files saved)
```
Same as daily run — no special config needed.
find_tw_files_since() automatically picks up Mon, Tue, Wed in order.
Baseline updates in memory between each day.
```

---

## Key Reuse Summary

| Component | Source | Action |
|---|---|---|
| Read YF CSVs | `src/data_reader.py` | No change |
| Compute top-20 | `src/hvd_screener.py` | No change — just set `max_events=20` |
| Write baseline CSV | `src/hvd_historical_exporter.py` | No change |
| Load baseline | `src/hve_preloader.py` | No change |
| Parse TW bulk file | `downloadData_v1/src/get_tradingview_data.py` | Port into metaVolume |
| Compare + rank logic | — | New in `vol_daily_checker.py` |
| Multi-file ordering | — | New in `vol_daily_checker.py` |
