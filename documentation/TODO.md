# TODO

## downloadData_v1

- [ ] Fix `find_all_tw_files_for_latest_date()` in `src/get_tradingview_data.py`
      Current behaviour: only processes the newest TW file date, silently skips older dates.
      Required behaviour: detect the last date already stored in `market_data_tw/`,
      then find ALL TW bulk files newer than that date and process them in
      chronological order (backfill support).
      Impact: without this fix, any day where TW update was not run immediately
      results in a permanent gap in `market_data_tw/`.

## metaVolume

- [x] Fast read mode for the daily checker — superseded by a different (better)
      mechanism than originally planned here: `downloadData_v1` already splits
      each ticker's file into `archive/` (frozen, through last Dec 31) and
      `current/` (this year only). `vol_daily_checker.py`'s Yahoo path now
      reads only `current/` via `yahoo_daily_adapter._ticker_csv_path()`
      instead of the full multi-year per-ticker file. HVE/HV1Y/multi-year
      calculations still go through `DataReader`, which reads archive+current
      combined — unchanged, no third folder, no disk write.

## Pipeline (new)

- [x] Daily incremental run — implemented directly in `vol_daily_checker.py`
      rather than a separate orchestration script: `VolDailyChecker` now
      checks both HVD (top-N) and HVE (all-time record) against the frozen
      baseline in `results/hve_results/historical/`, reading only `current/`.
      Run via `python main.py --preset postprocess`. The old plan (a
      `preload_HVE` flag + a `HVE_data_for_preload/` folder manually kept in
      sync) was removed — the baseline is read straight from
      `results/hve_results/historical/`, no copy step.

- [ ] Yearly maintenance runbook (still manual): after `downloadData_v1`'s
      own archive/current rollover for Dec 31 data, rerun
      `python main.py --preset preprocess_full` to rebuild
      `HVE_historical_{timeframe}.csv` / `HVD_historical_{timeframe}.csv`
      for all timeframes, then clear each
      `results/post/{timeframe}/HVE_incremental.csv` /
      `HVD_incremental.csv` / `last_processed.txt` since their discoveries
      are now baked into the fresh baseline. See README.md's "How pre and
      post compare and evolve" section for why this matters.

- [ ] Extend the same current/-only incremental pattern to weekly/monthly
      (currently daily-only).
