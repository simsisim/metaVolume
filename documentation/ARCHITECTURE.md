# System Architecture

## Overview

Two separate projects with a clean division of responsibility:

- **downloadData_v1** — data acquisition only, zero calculations
- **metaVolume**       — calculations and screening only, never downloads data

---

## Full Data Flow

```
╔══════════════════════════════════════════════════════════════════╗
║                        DATA SOURCES                              ║
╠══════════════════════════╦═══════════════════════════════════════╣
║  TradingView bulk CSV    ║  Yahoo Finance API (yfinance)         ║
║  (exported manually      ║  (automated download)                 ║
║   from TradingView UI)   ║                                       ║
║  ~30 seconds             ║  ~3 hours for 5,000 tickers           ║
║  latest bar only         ║  full OHLCV history (5 years)         ║
╚══════════════╤═══════════╩══════════════════╤════════════════════╝
               │                              │
               ▼                              ▼
╔══════════════════════════════════════════════════════════════════╗
║           downloadData_v1   (DATA ACQUISITION ONLY)             ║
║                                                                  ║
║  get_tradingview_data.py        get_marketData.py                ║
║  ─────────────────────          ──────────────────               ║
║  • parse bulk CSV               • call yfinance API              ║
║  • split rows per ticker        • incremental updates            ║
║  • append new bar to file       • full 5-year history            ║
║                │                          │                      ║
║                ▼                          ▼                      ║
║  data/market_data_tw/daily/   data/market_data/daily/           ║
║  ├── AAPL.csv  (TW rows)      ├── AAPL.csv  (YF rows)           ║
║  ├── MSFT.csv                 ├── MSFT.csv                       ║
║  └── ...~5,000 tickers        └── ...~5,000 tickers             ║
║                                                                  ║
║  grows by 1 row/day           full history, refreshed weekly     ║
╚══════════════╤═══════════════════════════╤══════════════════════╝
               │                           │
               │   DataReader picks mode   │
               │   per screener (below)    │
               └───────────┬───────────────┘
                           │
                           ▼
╔══════════════════════════════════════════════════════════════════╗
║             metaVolume   (CALCULATIONS + SCREENING)              ║
║                                                                  ║
║  DataReader (two read modes)                                     ║
║  ├─ mode='tw_only'  → market_data_tw/ only (fast)               ║
║  │  today's bar vs stored baseline; no history needed            ║
║  └─ mode='stitched' → YF history + TW gap joined in memory      ║
║     continuous multi-year series; no third folder on disk        ║
║           │                                                      ║
║           ▼                                                      ║
║  ┌────────────────────────────────────────────────┐             ║
║  │  HVE Screener      HVD Screener   HV1Y         │             ║
║  │  (stitched)        (tw_only)      (stitched)   │             ║
║  │  volume record  by magnitude   in last 1 year  │             ║
║  └────────────────────┬───────────────────────────┘             ║
║                       │                                          ║
║           ┌───────────┴───────────┐                             ║
║           ▼                       ▼                             ║
║  results/hve_results/daily/    HVE_data_for_preload/            ║
║  ├── hve_results_daily.csv     └── HVD_historical_daily.csv     ║
║  ├── hvd_results_daily.csv         (top-10 baseline — input     ║
║  └── hv1y_results_daily.csv         for next day's run)         ║
╚══════════════════════════════════════════════════════════════════╝
```

---

## Three Run Modes

### Mode 1 — Bootstrap (run once, ~4 hours)

```
downloadData_v1
  YF full download → data/market_data/daily/   (5 years, 5k tickers)

metaVolume
  data_source = yf
  preload_HVE = FALSE  (no baseline yet, scan full history)
  → builds HVE_data_for_preload/HVD_historical_daily.csv  (initial top-10)
```

### Mode 2 — Daily fast path (~10 min total)

```
downloadData_v1
  TW update → data/market_data_tw/daily/       (~30 sec, today's bar)

metaVolume
  data_source = tw
  preload_HVE = TRUE   (compare today's bar vs stored top-10)
  → updates HVD_historical_daily.csv if today beat the top-10
  → outputs only tickers with a new top-10 volume event
```

### Mode 3 — Gap fill (after missed days / vacation)

```
Precondition: TW bulk CSV files saved for each missed day (Mon, Tue, Wed...)

downloadData_v1
  TW backfill → processes Mon, Tue, Wed files in order  [TODO: fix needed]
  → data/market_data_tw/daily/ is now gapless

metaVolume
  data_source = tw
  preload_HVE = TRUE
  → scans all missing days against baseline
```

---

## Key Design Rules

| Rule | Reason |
|---|---|
| `market_data/` and `market_data_tw/` never merge on disk | Prevents data corruption from mixing two sources |
| metaVolume never downloads data | Clean separation of concerns |
| downloadData_v1 never calculates anything | Clean separation of concerns |
| Only ONE data source folder per metaVolume run | Controlled by `data_source` config param |
| TW bulk CSV files must be saved even if not processed immediately | Enables gap-fill backfill later |
| Baseline (`HVD_historical_daily.csv`) is the bridge between runs | metaVolume only needs today's bar + baseline, not full history |



  ┌───────────────────────────────────┬────────────────────────────────┬──────────────────┐
  │         Calculation type          │          Data needed           │    Read mode     │
  ├───────────────────────────────────┼────────────────────────────────┼──────────────────┤
  │ Volume top-10 check (HVD)         │ Today's bar vs stored baseline │ TW only          │
  ├───────────────────────────────────┼────────────────────────────────┼──────────────────┤
  │ Moving average, RS, any indicator │ Continuous gapless history     │ YF + TW stitched │
  └───────────────────────────────────┴────────────────────────────────┴──────────────────┘

