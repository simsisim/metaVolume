#!/usr/bin/env python3
"""
event_study.py — forward-return / money-flow evaluation of volume-anomaly events.

For every HVD (top-N highest-volume day) event in the frozen baseline plus the
post-processor incremental ledger, this joins the raw per-ticker OHLCV history and
measures what happened next:

  * same-day return           Close / prev_Close - 1
  * opening gap               Open  / prev_Close - 1
  * forward return  +1w       Close(+5 td)  / Close(0) - 1
  * forward return  +1m       Close(+21 td) / Close(0) - 1
  * forward return  +3m       Close(+63 td) / Close(0) - 1
  * dollar volume ("money flow")  Close * Volume on the event day

Results are aggregated by TradingView sector, market-cap tier and volume rank.

Usage:
    python scripts/event_study.py
    python scripts/event_study.py --timeframe daily --min-price 2 --start 2021-01-01
Outputs land in results/analysis/.
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / ".." / "downloadData_v1" / "data" / "market_data"
UNIVERSE = ROOT / "user_input" / "tradingview_universe.csv"
OUT_DIR = ROOT / "results" / "analysis"

HORIZONS = {"1w": 5, "1m": 21, "3m": 63}


def load_universe() -> pd.DataFrame:
    u = pd.read_csv(UNIVERSE)
    u = u.rename(columns={
        "Symbol": "ticker",
        "Sector": "sector",
        "Industry": "industry",
        "Market capitalization": "universe_mktcap",
    })
    return u[["ticker", "sector", "industry", "universe_mktcap"]]


def cap_tier(mktcap: float) -> str:
    if not np.isfinite(mktcap) or mktcap <= 0:
        return "unknown"
    if mktcap >= 10e9:
        return "large (>$10B)"
    if mktcap >= 2e9:
        return "mid ($2-10B)"
    if mktcap >= 300e6:
        return "small ($300M-2B)"
    return "micro (<$300M)"


def rank_bucket(r) -> str:
    try:
        r = int(r)
    except (TypeError, ValueError):
        return "unranked"
    if r == 1:
        return "1 (all-time high)"
    if r <= 3:
        return "2-3"
    if r <= 10:
        return "4-10"
    return "11-20"


def load_events(timeframe: str) -> pd.DataFrame:
    """Long-format event list: ticker, date, event_vol, rank (rank only for baseline)."""
    hist_path = ROOT / "results" / "pre" / "historical" / f"HVD_historical_{timeframe}.csv"
    hist = pd.read_csv(hist_path)
    date_cols = [c for c in hist.columns if c.startswith("HVD_date_")]
    rows = []
    for _, r in hist.iterrows():
        for i, dc in enumerate(date_cols, start=1):
            d = r[dc]
            v = r.get(f"HVD_vol_{i}")
            if pd.isna(d):
                continue
            rows.append((r["Symbol"], str(d)[:10], v, i))
    ev = pd.DataFrame(rows, columns=["ticker", "date", "event_vol", "rank"])

    inc_path = ROOT / "results" / "post" / timeframe / "HVD_incremental.csv"
    if inc_path.exists():
        inc = pd.read_csv(inc_path)
        inc = inc.rename(columns={"volume": "event_vol"})
        inc["date"] = inc["date"].astype(str).str[:10]
        inc["rank"] = np.nan
        ev = pd.concat([ev, inc[["ticker", "date", "event_vol", "rank"]]], ignore_index=True)

    ev["date"] = pd.to_datetime(ev["date"], errors="coerce")
    ev = ev.dropna(subset=["date"]).drop_duplicates(["ticker", "date"])
    return ev


def read_prices(ticker: str, timeframe: str) -> pd.DataFrame | None:
    frames = []
    for sub in ("archive", "current"):
        p = DATA_DIR / timeframe / sub / f"{ticker}.csv"
        if p.exists():
            try:
                f = pd.read_csv(p, usecols=["Date", "Open", "Close", "Volume"])
                frames.append(f)
            except (ValueError, pd.errors.EmptyDataError):
                pass
    if not frames:
        p = DATA_DIR / timeframe / f"{ticker}.csv"
        if p.exists():
            try:
                frames.append(pd.read_csv(p, usecols=["Date", "Open", "Close", "Volume"]))
            except (ValueError, pd.errors.EmptyDataError):
                return None
    if not frames:
        return None
    df = pd.concat(frames, ignore_index=True)
    df["Date"] = pd.to_datetime(df["Date"].astype(str).str[:10], errors="coerce")
    df = df.dropna(subset=["Date"]).drop_duplicates("Date").sort_values("Date").reset_index(drop=True)
    return df


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--timeframe", default="daily", choices=["daily", "weekly", "monthly"])
    ap.add_argument("--min-price", type=float, default=2.0)
    ap.add_argument("--start", default="2021-01-01", help="ignore events before this date")
    args = ap.parse_args()

    uni = load_universe()
    events = load_events(args.timeframe)
    events = events[events["date"] >= pd.Timestamp(args.start)]
    print(f"{len(events):,} raw events ({events['ticker'].nunique():,} tickers) since {args.start}")

    last_data_date = None
    out_rows = []
    for ticker, grp in events.groupby("ticker"):
        px = read_prices(ticker, args.timeframe)
        if px is None or len(px) < 70:
            continue
        px = px.set_index("Date")
        if last_data_date is None or px.index.max() > last_data_date:
            last_data_date = px.index.max()
        idx_pos = {d: i for i, d in enumerate(px.index)}
        closes = px["Close"].to_numpy(dtype=float)
        opens = px["Open"].to_numpy(dtype=float)
        vols = px["Volume"].to_numpy(dtype=float)
        n = len(px)
        for _, e in grp.iterrows():
            i = idx_pos.get(e["date"])
            if i is None or i == 0:
                continue
            c0, o0, pc = closes[i], opens[i], closes[i - 1]
            if not (np.isfinite(c0) and np.isfinite(pc) and pc > 0) or c0 < args.min_price:
                continue
            rec = {
                "ticker": ticker,
                "date": e["date"].date().isoformat(),
                "rank": e["rank"],
                "event_vol": e["event_vol"],
                "close": c0,
                "dollar_vol": c0 * vols[i] if np.isfinite(vols[i]) else np.nan,
                "same_day_ret": c0 / pc - 1,
                "gap": (o0 / pc - 1) if np.isfinite(o0) and o0 > 0 else np.nan,
            }
            for name, h in HORIZONS.items():
                j = i + h
                rec[f"fwd_{name}"] = (closes[j] / c0 - 1) if j < n and np.isfinite(closes[j]) else np.nan
            out_rows.append(rec)

    df = pd.DataFrame(out_rows)
    if df.empty:
        print("no events matched", file=sys.stderr)
        return 1
    df = df.merge(uni, on="ticker", how="left")
    df["sector"] = df["sector"].fillna("Unknown")
    df["cap_tier"] = df["universe_mktcap"].apply(cap_tier)
    df["rank_bucket"] = df["rank"].apply(rank_bucket)
    df["date"] = pd.to_datetime(df["date"])

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_DIR / f"event_study_{args.timeframe}.csv", index=False)
    print(f"{len(df):,} scored events -> results/analysis/event_study_{args.timeframe}.csv")
    print(f"price data through {last_data_date.date() if last_data_date is not None else '?'}\n")

    fwd_cols = [f"fwd_{k}" for k in HORIZONS]

    def summarise(g: pd.DataFrame) -> pd.Series:
        out = {"events": len(g), "tickers": g["ticker"].nunique(),
               "dollar_vol_bn": g["dollar_vol"].sum() / 1e9,
               "median_gap_%": 100 * g["gap"].median()}
        for c in fwd_cols:
            v = g[c].dropna()
            out[f"{c}_med_%"] = 100 * v.median() if len(v) else np.nan
            out[f"{c}_hit_%"] = 100 * (v > 0).mean() if len(v) else np.nan
            out[f"{c}_n"] = len(v)
        return pd.Series(out)

    pd.set_option("display.width", 200)
    pd.set_option("display.max_columns", 30)
    pd.set_option("display.float_format", lambda x: f"{x:,.1f}")

    print("=" * 100)
    print("OVERALL — what happened after a top-20 volume day")
    print("=" * 100)
    print(summarise(df).to_frame("all").T.to_string())

    for dim in ["sector", "cap_tier", "rank_bucket"]:
        print("\n" + "=" * 100)
        print(f"BY {dim.upper()}")
        print("=" * 100)
        tbl = df.groupby(dim).apply(summarise).sort_values("dollar_vol_bn", ascending=False)
        print(tbl.to_string())
        tbl.to_csv(OUT_DIR / f"event_study_{args.timeframe}_by_{dim}.csv")

    print("\n" + "=" * 100)
    print("SECTOR MONEY FLOW ranked (total $ traded on volume-anomaly days, since %s)" % args.start)
    print("=" * 100)
    mf = (df.groupby("sector")
            .agg(events=("ticker", "size"),
                 dollar_vol_bn=("dollar_vol", lambda s: s.sum() / 1e9),
                 median_gap_pct=("gap", lambda s: 100 * s.median()),
                 fwd_1m_med_pct=("fwd_1m", lambda s: 100 * s.median()),
                 fwd_1m_hit_pct=("fwd_1m", lambda s: 100 * (s.dropna() > 0).mean()))
            .sort_values("dollar_vol_bn", ascending=False))
    print(mf.to_string())

    # recency-aware note
    cut_1m = last_data_date - pd.Timedelta(days=35)
    cut_3m = last_data_date - pd.Timedelta(days=95)
    print(f"\nNote: fwd_1m excludes {int((df['date'] > cut_1m).sum())} events after {cut_1m.date()}; "
          f"fwd_3m excludes {int((df['date'] > cut_3m).sum())} after {cut_3m.date()} (window not complete).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
