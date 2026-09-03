#!/usr/bin/env python3
"""
earnings_gap_study.py — do leader moves start with a high-volume gap?

Defines a "shock bar" as a day where BOTH:
    * Volume >= VOL_MULT x the trailing 50-day average volume   (default 4.0x = "400%")
    * |Open / prev_Close - 1| >= GAP_MIN                         (default 5%)
This is a proxy for an earnings / guidance / M&A gap (Wall Street caught off guard).

For every shock bar it measures the forward path (1w/1m/3m/6m/12m), the maximum
run-up and drawdown over the next 6 months, and two "leader continuation" tests:
    * held        — never closed below the shock-bar CLOSE over the next month
                    (consolidated instead of round-tripping)
    * continued   — after that month, price is >= +15% above the shock-bar close
                    at the 6-month mark

Aggregates by direction, sector, cap tier, gap size and volume multiple, and
prints the full shock-bar history for a set of named leaders.

Usage:
    python scripts/earnings_gap_study.py
    python scripts/earnings_gap_study.py --vol-mult 4 --gap-min 0.05 --start 2023-01-01
    python scripts/earnings_gap_study.py --leaders SNDK,MU,DELL,AMD,NVDA,PLTR,ANET,VST
Output: results/analysis/earnings_gap_events.csv
"""
from __future__ import annotations
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / ".." / "downloadData_v1" / "data" / "market_data" / "daily"
UNIVERSE = ROOT / "user_input" / "tradingview_universe.csv"
OUT_DIR = ROOT / "results" / "analysis"

FWD = {"1w": 5, "1m": 21, "3m": 63, "6m": 126, "12m": 252}
DEF_LEADERS = "SNDK,MU,DELL,AMD,NVDA,PLTR,ANET,AVGO,VRT,VST,CVNA,APP,COIN,MSTR,SMCI"


def load_universe() -> pd.DataFrame:
    u = pd.read_csv(UNIVERSE).rename(columns={
        "Symbol": "ticker", "Sector": "sector", "Industry": "industry",
        "Market capitalization": "mktcap"})
    return u[["ticker", "sector", "industry", "mktcap"]]


def cap_tier(m: float) -> str:
    if not np.isfinite(m) or m <= 0:
        return "unknown"
    return ("large (>$10B)" if m >= 10e9 else "mid ($2-10B)" if m >= 2e9
            else "small ($300M-2B)" if m >= 300e6 else "micro (<$300M)")


def read_prices(ticker: str) -> pd.DataFrame | None:
    frames = []
    for sub in ("archive", "current"):
        p = DATA_DIR / sub / f"{ticker}.csv"
        if p.exists():
            try:
                frames.append(pd.read_csv(p, usecols=["Date", "Open", "High", "Low", "Close", "Volume"]))
            except (ValueError, pd.errors.EmptyDataError):
                pass
    if not frames:
        return None
    df = pd.concat(frames, ignore_index=True)
    df["Date"] = pd.to_datetime(df["Date"].astype(str).str[:10], errors="coerce")
    df = (df.dropna(subset=["Date"]).drop_duplicates("Date")
            .sort_values("Date").reset_index(drop=True))
    return df


def scan_ticker(ticker: str, vol_mult: float, gap_min: float, start: pd.Timestamp) -> list[dict]:
    px = read_prices(ticker)
    if px is None or len(px) < 120:
        return []
    o = px["Open"].to_numpy(float)
    h = px["High"].to_numpy(float)
    l = px["Low"].to_numpy(float)
    c = px["Close"].to_numpy(float)
    v = px["Volume"].to_numpy(float)
    d = px["Date"].to_numpy()
    n = len(px)
    avg50 = pd.Series(v).rolling(50).mean().shift(1).to_numpy()  # excludes event day
    out = []
    for i in range(50, n):
        if px["Date"].iloc[i] < start:
            continue
        pc = c[i - 1]
        if not (np.isfinite(pc) and pc > 0 and np.isfinite(avg50[i]) and avg50[i] > 0):
            continue
        gap = o[i] / pc - 1
        volx = v[i] / avg50[i]
        if volx < vol_mult or abs(gap) < gap_min or c[i] < 3:
            continue
        direction = "gap-up" if gap > 0 else "gap-down"
        c0 = c[i]
        rec = {"ticker": ticker, "date": pd.Timestamp(d[i]).date().isoformat(),
               "direction": direction, "gap": gap, "vol_x": volx,
               "close": c0, "day_ret": c0 / pc - 1, "dollar_vol": c0 * v[i]}
        for name, k in FWD.items():
            j = i + k
            rec[f"fwd_{name}"] = (c[j] / c0 - 1) if j < n and np.isfinite(c[j]) else np.nan
        # 6-month path stats
        end = min(i + 126, n)
        seg_c = c[i + 1:end]
        seg_l = l[i + 1:end]
        seg_h = h[i + 1:end]
        if len(seg_c):
            rec["max_runup_6m"] = np.nanmax(seg_h) / c0 - 1
            rec["max_drawdown_6m"] = np.nanmin(seg_l) / c0 - 1
        else:
            rec["max_runup_6m"] = rec["max_drawdown_6m"] = np.nan
        # continuation tests
        m_end = min(i + 21, n)
        month_c = c[i + 1:m_end]
        rec["held_1m"] = bool(len(month_c)) and bool(np.all(month_c >= c0 * 0.90))
        j6 = i + 126
        rec["continued_6m"] = (j6 < n and np.isfinite(c[j6]) and c[j6] >= c0 * 1.15)
        rec["leader_12m"] = np.nan
        j12 = i + 252
        if j12 < n and np.isfinite(c[j12]):
            rec["leader_12m"] = c[j12] / c0 - 1
        out.append(rec)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--vol-mult", type=float, default=4.0)
    ap.add_argument("--gap-min", type=float, default=0.05)
    ap.add_argument("--start", default="2022-01-01")
    ap.add_argument("--leaders", default=DEF_LEADERS)
    args = ap.parse_args()
    start = pd.Timestamp(args.start)

    uni = load_universe()
    tickers = sorted(set(uni["ticker"]) | set(args.leaders.split(",")))

    rows = []
    for t in tickers:
        rows.extend(scan_ticker(t, args.vol_mult, args.gap_min, start))
    df = pd.DataFrame(rows)
    if df.empty:
        print("no shock bars found")
        return 1
    df = df.merge(uni, on="ticker", how="left")
    df["sector"] = df["sector"].fillna("Unknown")
    df["cap_tier"] = df["mktcap"].apply(cap_tier)
    df["date"] = pd.to_datetime(df["date"])
    df["gap_bucket"] = pd.cut(df["gap"].abs(), [0.05, 0.10, 0.20, 0.40, 10],
                              labels=["5-10%", "10-20%", "20-40%", ">40%"])
    df["volx_bucket"] = pd.cut(df["vol_x"], [4, 6, 10, 20, 1e9],
                               labels=["4-6x", "6-10x", "10-20x", ">20x"])
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_DIR / "earnings_gap_events.csv", index=False)

    pd.set_option("display.width", 220); pd.set_option("display.max_columns", 40)
    pd.set_option("display.float_format", lambda x: f"{x:,.1f}")
    last = df["date"].max()
    print(f"{len(df):,} shock bars ({df.ticker.nunique():,} tickers), "
          f"vol>={args.vol_mult}x avg50 & |gap|>={args.gap_min:.0%}, since {args.start}")
    print(f"data through ~{last.date()}\n")

    fcols = [f"fwd_{k}" for k in FWD]

    def summ(g):
        r = {"n": len(g), "median_gap_%": 100 * g["gap"].median(),
             "median_volx": g["vol_x"].median(),
             "held_1m_%": 100 * g["held_1m"].mean(),
             "continued_6m_%": 100 * g["continued_6m"].mean()}
        for cc in fcols:
            s = g[cc].dropna()
            r[f"{cc}_med%"] = 100 * s.median() if len(s) else np.nan
            r[f"{cc}_hit%"] = 100 * (s > 0).mean() if len(s) else np.nan
        r["runup6m_med%"] = 100 * g["max_runup_6m"].median()
        r["drawdn6m_med%"] = 100 * g["max_drawdown_6m"].median()
        return pd.Series(r)

    for dim in ["direction", "cap_tier", "gap_bucket", "volx_bucket"]:
        print("=" * 110)
        print(f"BY {dim.upper()}")
        print("=" * 110)
        print(df.groupby(dim, observed=True).apply(summ, include_groups=False).to_string())
        print()

    print("=" * 110)
    print("GAP-UP ONLY — by sector (min 25 events), sorted by 6-month continuation rate")
    print("=" * 110)
    gu = df[df.direction == "gap-up"]
    t = gu.groupby("sector").apply(summ, include_groups=False)
    print(t[t.n >= 25].sort_values("continued_6m_%", ascending=False).to_string())
    t.to_csv(OUT_DIR / "earnings_gap_by_sector.csv")

    print("\n" + "=" * 110)
    print("LARGE + MID CAP GAP-UPS — the 'leader' cohort")
    print("=" * 110)
    lc = gu[gu.cap_tier.str.startswith(("large", "mid"))]
    print(summ(lc).to_frame("large+mid gap-up").T.to_string())
    ld = lc["leader_12m"].dropna()
    if len(ld):
        print(f"\n12-month outcome of large/mid-cap gap-ups (n={len(ld)} with full year):")
        for thr in (0.0, 0.20, 0.50, 1.0):
            print(f"   > {thr:+.0%} 12m later: {100*(ld > thr).mean():.1f}%")
        print(f"   median 12m: {100*ld.median():+.1f}%   mean 12m: {100*ld.mean():+.1f}%")

    print("\n" + "=" * 110)
    print("NAMED LEADERS — every shock bar (vol>=%gx, |gap|>=%d%%)" % (args.vol_mult, args.gap_min * 100))
    print("=" * 110)
    for t in args.leaders.split(","):
        g = df[df.ticker == t].sort_values("date")
        if g.empty:
            print(f"\n{t}: no qualifying shock bar in window")
            continue
        print(f"\n{t}  ({g.sector.iloc[0]})")
        show = g[["date", "direction", "gap", "vol_x", "close", "day_ret",
                  "fwd_1m", "fwd_3m", "fwd_6m", "fwd_12m", "max_drawdown_6m", "held_1m"]].copy()
        for cc in ["gap", "day_ret", "fwd_1m", "fwd_3m", "fwd_6m", "fwd_12m", "max_drawdown_6m"]:
            show[cc] = (show[cc] * 100).round(1)
        show["vol_x"] = show["vol_x"].round(1)
        show["date"] = show["date"].dt.date
        print(show.to_string(index=False))

    cut = {"12m": last - pd.Timedelta(days=380), "6m": last - pd.Timedelta(days=195),
           "3m": last - pd.Timedelta(days=100)}
    print("\nWindow completeness: fwd_12m needs event before %s; fwd_6m before %s; fwd_3m before %s."
          % (cut["12m"].date(), cut["6m"].date(), cut["3m"].date()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
