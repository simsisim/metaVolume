# metaVolume + downloadData_v1 — Project Analysis & Integration Plan

## 1. metaVolume (current project)

**Purpose**: Stock volume analysis screener identifying three event types:
- **HVE** — new all-time volume record for a ticker (temporal milestone)
- **HVD** — top N highest-volume days by magnitude (ranking, any time)
- **HV1Y** — highest volume within the trailing 365-day window

**Input**: Per-ticker OHLCV CSVs at `data/market_data/{daily|weekly|monthly}/TICKER.csv`

**Key feature**: Incremental detection via preload baselines — stores the top-10 historical volume events per ticker in `HVE_data_for_preload/HVD_historical_*.csv`. Future runs only check whether new data beats a stored threshold. This is the `top10_hist_data` concept.

### Entry point
`main.py` → reads `user_data.csv` → processes tickers in batches of 100 → runs HVE/HVD/HV1Y screeners → exports CSVs and ticker cards

### Output files
| File | Description |
|---|---|
| `results/hve_results/{tf}/hve_results_{tf}.csv` | HVE results, long format |
| `results/hve_results/{tf}/hvd_results_{tf}.csv` | HVD results, long format |
| `results/hve_results/{tf}/hv1y_results_{tf}.csv` | HV1Y results, long format |
| `results/hve_results/HVE_historical_{tf}.csv` | Wide format, preload-compatible |
| `results/hve_results/HVD_historical_{tf}.csv` | Wide format, preload-compatible |

### Key configuration parameters (`user_data.csv`)
```
HVE_enable, HVD_historical_export, HV1Y_enable
HVE_limit_years, HVE_min_price, HVE_min_volume
HVE_date_range_mode (rolling / fixed), HVE_start_date, HVE_end_date
HVD_historical_max_events (default 10)
preload_HVE (TRUE = incremental mode)
```

---

## 2. downloadData_v1

**Purpose**: Data acquisition pipeline — downloads and maintains OHLCV and financial data for downstream analysis tools such as metaVolume.

### Data sources
| Source | Speed | Coverage | Purpose |
|---|---|---|---|
| TradingView bulk CSV | ~30 sec | Latest bar only | Daily fast update |
| Yahoo Finance (yfinance) | ~3 hrs for 5k tickers | Full 5-year OHLCV history | Baseline + gap fill |
| NASDAQ FTP | minutes | Ticker lists | Universe construction |
| Wikipedia | seconds | S&P 500, NASDAQ 100, Russell 1000 | Ticker lists |

### Storage layout
```
data/
├── market_data/          # Yahoo Finance full history (primary DB)
│   ├── daily/            # Per-ticker CSVs, 5 years
│   ├── weekly/
│   └── monthly/
├── market_data_tw/       # TradingView latest-bar snapshot (temporary DB)
│   ├── daily/            # ~6438 tickers
│   ├── weekly/
│   └── monthly/
├── tickers/              # Generated ticker lists
│   ├── combined_info_tickers_clean_*.csv
│   ├── financial_data_*.csv
│   └── problematic_tickers_*.csv
└── tw_files/             # Input TradingView bulk CSV exports
```

### Supported ticker universes
| Choice | Universe |
|---|---|
| 0 | TradingView custom (all_stocks_LOHP — up to 6k tickers) |
| 1 | S&P 500 |
| 2 | NASDAQ 100 |
| 3 | All NASDAQ (~5000+) |
| 4 | Russell 1000 |
| 5–8 | Index / Portfolio / ETF / Test tickers |

Choices can be combined: `ticker_choice=1-2` = S&P 500 + NASDAQ 100.

### Rate limiting
- Yahoo Finance: 0.2 s per ticker, 30 s pause every 100 tickers
- Financial data: 1.5 s per ticker, 10 s pause every 50 tickers
- TradingView: no delay (local CSV parsing)
- Smart sampling: samples 5 random tickers before a TradingView update; skips if already current

---

## 3. How They Fit Together

These two projects are the two halves of the proposed workflow. The architecture is already partially implemented — the missing piece is a daily merge step and an orchestration layer.

```
downloadData_v1                          metaVolume
─────────────────                        ──────────────────────────────
TradingView bulk CSV ──(30 sec)──┐
                                 ├──► data/market_data/ ──► HVD screener
Yahoo Finance history ──(3 hr)──┘    (primary DB)           (compares new bar
                                                              vs stored top10)
data/market_data_tw/ ──(daily)──► [MISSING: merge step]
  (temporary DB)
```

---

## 4. What Already Exists vs. What Needs Building

| Component | Status |
|---|---|
| Universe from TradingView all_stocks_LOHP | **Exists** — `ticker_choice=0` in downloadData_v1 |
| 5-year Yahoo Finance historical download | **Exists** — `YF_hist_data=TRUE` |
| top10_hist_data (10 highest-volume days per ticker) | **Exists** — `HVD_historical_daily.csv` preload in metaVolume |
| Primary DB (full history, per-ticker CSVs) | **Exists** — `data/market_data/daily/` |
| Temporary DB (latest bar only) | **Exists** — `data/market_data_tw/daily/` |
| Daily TradingView fast update (~30 sec) | **Exists** — `TW_hist_data=TRUE` |
| **Merge: TW daily bar → primary DB** | **MISSING** |
| **Daily orchestration script** | **MISSING** |
| **Incremental screener wiring** | **Partially exists** — metaVolume preload mode does this but needs connecting |

---

## 5. Implementation Plan

### Step 1 — One-time bootstrap (`bootstrap.py`)
Run Yahoo Finance full 5-year download for all ~5k tickers, then run metaVolume once without preload to build the initial `HVD_historical_daily.csv` baseline.

- Runtime: ~3–4 hours (one-time only)
- Output: `data/market_data/daily/TICKER.csv` for all tickers + initial `HVE_data_for_preload/HVD_historical_daily.csv`

### Step 2 — Merge script (`merge_tw_to_primary.py`)
After TradingView updates `market_data_tw/daily/`, append each ticker's new bar to `market_data/daily/TICKER.csv`. Deduplicate by date. ~50–80 lines of Python.

### Step 3 — Daily orchestration (`daily_run.py`)
```
1. downloadData_v1: TW_hist_data=TRUE          (~30 sec)
      └─► data/market_data_tw/daily/TICKER.csv
2. merge_tw_to_primary.py                      (~2 min for 5k tickers)
      └─► data/market_data/daily/TICKER.csv  (append today's bar)
3. metaVolume: preload_HVE=TRUE                (~5–10 min)
      reads:  HVE_data_for_preload/HVD_historical_daily.csv
      checks: did today's volume beat any top-10?
      writes: results/hve_results/daily/hvd_results_daily.csv
4. copy updated HVD_historical_daily.csv → HVE_data_for_preload/
      (update baseline for tomorrow)
```

---

## 6. Full Data Flow

```
ONE-TIME SETUP (~3–4 hours, run once)
──────────────────────────────────────────────────────────────────
downloadData_v1: YF_hist_data=TRUE, ticker_choice=0
    └─► data/market_data/daily/TICKER.csv  (5 years, ~5k tickers)
metaVolume: preload_HVE=FALSE
    └─► HVE_data_for_preload/HVD_historical_daily.csv  (initial top10 baseline)

DAILY RUN (~10–15 min total)
──────────────────────────────────────────────────────────────────
1. TradingView update       30 sec  → data/market_data_tw/daily/
2. merge_tw_to_primary       2 min  → data/market_data/daily/  (today's bar appended)
3. metaVolume (preload)     5-10 min→ results/hve_results/daily/hvd_results_daily.csv
4. copy new baseline         <1 sec → HVE_data_for_preload/

WEEKLY REFRESH (optional — catches gaps from missed days)
──────────────────────────────────────────────────────────────────
downloadData_v1: YF_hist_data=TRUE (incremental, new bars only)
    └─► fills any gaps left by missed TradingView updates
```

---

## 7. Why This Solves the TradingView 1,000-Ticker Limit

TradingView Pine Screener watchlists are capped at 1,000 symbols. The proposed pipeline removes that constraint entirely:

- The universe (~5k–6k US stocks) is managed in Python, not in TradingView watchlists
- TradingView is used only as a fast data feed (bulk CSV export, ~30 sec)
- The screening logic (HVD top-10 comparison) runs locally in metaVolume
- Results are a daily CSV of all tickers that hit a new top-10 volume event

---

## 8. Open Questions

1. Is the TradingView `all_stocks_LOHP` bulk CSV already being exported and placed in `downloadData_v1/data/tw_files/daily/`?
2. Where should the new scripts (`merge_tw_to_primary.py`, `daily_run.py`) live — in metaVolume, in downloadData_v1, or in a new `pipeline/` project?
3. Should the weekly Yahoo Finance gap-fill refresh be scheduled (cron) or run manually?
