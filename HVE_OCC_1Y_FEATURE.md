# HVE_OCC_1Y Feature - Complete Documentation ✅

**Date**: 2025-11-18
**Status**: Fully Implemented and Tested

---

## 📋 Overview

The `HVE_OCC_1Y` feature tracks **how many times** a stock achieved a Highest Volume Ever (HVE) event in the last 1 year.

### What is an HVE Event?

An **HVE event** occurs when the trading volume on a specific day reaches a new all-time high for that stock. This means the volume on that day is higher than any previous day in the stock's trading history.

### Example Scenario

```
March 2025: Volume = 10M  → HVE Event #1 (new high!)
April 2025: Volume = 12M  → HVE Event #2 (new high!)
May 2025:   Volume = 8M   → Not HVE (below previous high)
June 2025:  Volume = 15M  → HVE Event #3 (new high!)

Result: HVE_OCC_1Y = 3 (three HVE events in last year)
```

---

## 🎯 New CSV Columns

Two new columns have been added to the HVE results CSV:

### 1. `hve_occ_1y`
**Count of HVE events in the last 365 days**

- Counts only HVE events within the last 1 year from the latest date
- Events older than 1 year are excluded
- Helps identify stocks with recent volume acceleration

### 2. `total_hve_count`
**Total count of HVE events across all history**

- Counts all HVE events in the entire data history
- Limited by `HVE_limit_years` setting in user_data.csv
- Helps understand overall volume volatility

---

## 📊 Real Data Examples

From test run with 6 tickers (2025-09-05):

| Ticker | Days Since HVE | HVE Volume | hve_occ_1y | total_hve_count |
|--------|----------------|------------|------------|-----------------|
| HOOD | 66 days | 121.2M | **4** | 10 |
| GOOG | 121 days | 78.7M | **1** | 7 |
| STX | 155 days | 12.9M | **2** | 10 |
| WDC | 400 days | 35.6M | **0** | 5 |
| GEV | 521 days | 18.2M | **0** | 2 |
| NVDA | 546 days | 1.14B | **0** | 6 |

### Interpretation:

**HOOD (Robinhood)**:
- Latest HVE: 66 days ago (July 1, 2025)
- **4 HVE events in last year** ← High volume activity!
- 10 total HVE events across all history
- **Signal**: Recent volume acceleration, multiple new highs

**GOOG (Google)**:
- Latest HVE: 121 days ago (May 7, 2025)
- **1 HVE event in last year** ← Moderate activity
- 7 total HVE events across all history
- **Signal**: One recent volume spike

**WDC, GEV, NVDA**:
- Latest HVE: 400-546 days ago (over 1 year ago)
- **0 HVE events in last year** ← No recent volume highs
- **Signal**: Volume declining or stable

---

## 🔧 Implementation Details

### Algorithm

Located in `main.py` → `screen_hve_events()` function (lines 149-207):

```python
# 1. Sort data by date
df = df.sort_index()

# 2. Calculate cumulative maximum volume
df['cummax_volume'] = df['Volume'].cummax()

# 3. Identify HVE events (new volume highs)
df['is_hve'] = df['Volume'] == df['cummax_volume']
df['is_new_hve'] = (df['is_hve']) & (df['Volume'] > df['cummax_volume'].shift(1).fillna(0))

# 4. Get all HVE events
hve_events = df[df['is_new_hve']]

# 5. Count HVE events in last 1 year
one_year_ago = df.index[-1] - pd.DateOffset(years=1)
hve_last_year = hve_events[hve_events.index >= one_year_ago]
hve_occ_1y = len(hve_last_year)

# 6. Count total HVE events
total_hve_count = len(hve_events)
```

### Key Logic Points

1. **Cumulative Maximum**: `cummax()` tracks the highest volume seen up to each point
2. **New High Detection**: Compare current volume with previous cumulative max
3. **Time Window**: Use `pd.DateOffset(years=1)` for exactly 365 days
4. **First Data Point**: Counted as HVE (it's the first volume seen)

---

## ✅ Testing

### test_05_hve_occurrence.py - ALL TESTS PASSED ✅

**Test Scenario:**
- Created synthetic data with 5 HVE events over 15 months
- Event #1: 14 months ago (outside 1Y window)
- Events #2-5: 11, 8, 5, 2 months ago (inside 1Y window)

**Results:**
```
✅ HVE_OCC_1Y count correct: 4
✅ Total HVE count correct: 6 (including baseline)
✅ Latest HVE volume correct: 3,500
✅ Days since HVE reasonable: 62
```

**Explanation:**
- Baseline (first day): Outside 1Y → Not counted in `hve_occ_1y`
- Event #1 (14 months): Outside 1Y → Not counted in `hve_occ_1y`
- Events #2-5 (11,8,5,2 months): Inside 1Y → **4 events counted** ✓

---

## 📈 Use Cases

### 1. Volume Breakout Detection
**Filter**: `hve_occ_1y >= 3`
- Identifies stocks with multiple recent volume spikes
- Signals increasing interest and volatility
- Example: HOOD with 4 HVE events

### 2. Momentum Confirmation
**Filter**: `hve_occ_1y >= 1 AND days_since_hve < 90`
- Recent volume high within 90 days
- Confirms ongoing momentum
- Example: HOOD, GOOG

### 3. Volume Decline Detection
**Filter**: `hve_occ_1y == 0 AND days_since_hve > 365`
- No recent volume highs in over a year
- May indicate declining interest
- Example: WDC, GEV, NVDA

### 4. Screening Strategy
```csv
ticker_choice,2,NASDAQ 100
HVE_min_price,10,Minimum price $10
```

Then filter results:
- High activity: `hve_occ_1y >= 2`
- Recent spike: `hve_occ_1y >= 1 AND days_since_hve < 60`
- Historical volatility: `total_hve_count >= 5`

---

## 📁 Output Files

### CSV Format

**File**: `results/hve_results/{timeframe}/hve_results_{timeframe}.csv`

**Columns** (in order):
1. `ticker` - Stock symbol
2. `timeframe` - daily/weekly/monthly
3. `hve_date` - Date of latest HVE
4. `hve_volume` - Volume of latest HVE
5. `days_since_hve` - Days since latest HVE
6. **`hve_occ_1y`** ← NEW: HVE count in last year
7. **`total_hve_count`** ← NEW: Total HVE count
8. `latest_date` - Most recent date in data
9. `latest_volume` - Most recent volume
10. `latest_close` - Most recent close price
11. `volume_ratio` - Latest vol / HVE vol
12. `data_points` - Number of data points

### Example Output

```csv
ticker,timeframe,hve_date,hve_volume,days_since_hve,hve_occ_1y,total_hve_count,latest_date,latest_volume,latest_close,volume_ratio,data_points
HOOD,daily,2025-07-01,121171500,66,4,10,2025-09-05,60862400,101.25,0.50,421
GOOG,daily,2025-05-07,78729800,121,1,7,2025-09-05,26106200,235.17,0.33,421
```

---

## 🔧 Configuration

No additional configuration needed! The feature uses existing settings:

**user_data.csv:**
```csv
HVE_limit_years,4,Limit historical search to N years
HVE_min_volume,0,Minimum volume threshold
HVE_min_price,2,Minimum price threshold
```

These settings affect which data is analyzed, but `hve_occ_1y` always counts events in the last 365 days from the latest date.

---

## 📊 Console Output

Updated to show new columns:

```
📊 DAILY RESULTS SUMMARY:
   Total tickers with HVE data: 6

   Top 10 by recent HVE:
   1. HOOD: 66 days ago (2025-07-01, vol=121,171,500, HVE_1Y=4, Total=10)
   2. GOOG: 121 days ago (2025-05-07, vol=78,729,800, HVE_1Y=1, Total=7)
   3. STX: 155 days ago (2025-04-03, vol=12,915,600, HVE_1Y=2, Total=10)
```

---

## 🎓 Interpretation Guide

### `hve_occ_1y` Values

| Value | Meaning | Trading Signal |
|-------|---------|---------------|
| **0** | No recent HVE events | Declining or stable interest |
| **1** | One recent spike | Single event, monitor for continuation |
| **2-3** | Multiple recent spikes | Increasing volatility/interest |
| **4+** | Frequent new highs | High activity, potential breakout |

### `total_hve_count` Values

| Value | Meaning | Volatility Signal |
|-------|---------|------------------|
| **1-2** | Few historical spikes | Low historical volatility |
| **3-5** | Moderate spikes | Moderate volatility |
| **6-10** | Many spikes | High historical volatility |
| **10+** | Very frequent spikes | Extremely volatile |

### Combined Analysis

**Example: HOOD**
- `hve_occ_1y = 4` → Recent surge in activity ⚡
- `total_hve_count = 10` → Historically volatile
- `days_since_hve = 66` → Recent HVE (2 months ago)
- **Conclusion**: Active stock with recent volume acceleration

**Example: NVDA**
- `hve_occ_1y = 0` → No recent HVE events
- `total_hve_count = 6` → Moderate historical volatility
- `days_since_hve = 546` → Last HVE was 1.5 years ago
- **Conclusion**: Volume cooling down after previous activity

---

## ✅ Completion Checklist

- [x] Implemented cumulative maximum volume tracking
- [x] Added HVE event detection logic
- [x] Count HVE events in last 1 year (`hve_occ_1y`)
- [x] Count total HVE events (`total_hve_count`)
- [x] Updated CSV output with new columns
- [x] Updated console output to display new metrics
- [x] Created comprehensive test (test_05_hve_occurrence.py)
- [x] Tested with real data (6 test tickers)
- [x] Verified CSV format and column order
- [x] Documentation complete

---

## 🚀 Usage

### Run HVE Analysis

```bash
# Test with 6 tickers
python main.py

# Check results
cat results/hve_results/daily/hve_results_daily.csv

# Filter high activity stocks
cat results/hve_results/daily/hve_results_daily.csv | awk -F',' '$6 >= 2 {print $1,$6,$7}'
```

### Analyze Results

```python
import pandas as pd

df = pd.read_csv('results/hve_results/daily/hve_results_daily.csv')

# High recent activity (2+ HVE events in last year)
high_activity = df[df['hve_occ_1y'] >= 2]
print(high_activity[['ticker', 'hve_occ_1y', 'total_hve_count']])

# Recent spikes (HVE within 90 days)
recent_spikes = df[(df['hve_occ_1y'] >= 1) & (df['days_since_hve'] <= 90)]
```

---

**Status**: ✅ **FEATURE COMPLETE AND TESTED**
**Date**: 2025-11-18
**Ready for**: Production use with any ticker_choice value
