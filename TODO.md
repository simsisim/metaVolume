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

- [ ] Update `DataReader.read_stock_data()` to support two read modes:
      mode='tw_only'  → read only market_data_tw/ (fast; enough for volume top-10 check
                        because the baseline is already stored — only today's bar needed)
      mode='stitched' → read YF full history + TW rows newer than last YF date,
                        concat + sort in memory → single gapless DataFrame
                        (required for HVE, HV1Y, moving averages, RS, or any
                        calculation that needs continuous multi-year history)
      Rule: no third folder, no disk write, both source files stay pure.
      Screener picks the mode based on what it computes, not a global config.

## Pipeline (new)

- [ ] Write `daily_run.py` orchestration script that chains:
      1. downloadData_v1 TW update
      2. metaVolume incremental run (data_source=tw, preload_HVE=TRUE)
      3. Copy updated HVD_historical_daily.csv → HVE_data_for_preload/

- [ ] Write `bootstrap.py` one-time setup script:
      1. downloadData_v1 YF full download (5k tickers, 5 years)
      2. metaVolume full run (data_source=yf, preload_HVE=FALSE) to build initial baseline
