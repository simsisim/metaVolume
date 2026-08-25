"""
Cross-sectional staleness guard for screener results.

A per-ticker screener like HVE/HVD computes "days since event" relative to
that ticker's OWN last row (df.index[-1]) - not "today." If a ticker's data
silently stopped updating (a slow-pipeline gap, a delisting, a fetch that
started failing), its stale last row still produces a valid-looking
days-since count, anchored to whenever it actually stopped - which can sort
to the TOP of a "most recent event" ranking, indistinguishable from a
genuinely fresh signal. Same bug class found and fixed in yf-gics's
rs_percentile.py (downloadData_v1 session, 2026-08-24) - there it's fixed by
comparing against SPY's date since every industry is already measured
against SPY; here there's no equivalent single reference series, so this
uses the batch's own majority date instead - the same "majority wins,
anything else is a straggler" convention downloadData_v1's own
scripts/sync_stragglers.py already uses to detect stale tickers.
"""
import logging

import pandas as pd

logger = logging.getLogger(__name__)


def exclude_stale(results_df: pd.DataFrame, date_col: str = 'latest_date',
                   ticker_col: str = 'ticker') -> pd.DataFrame:
    """Drop rows whose `date_col` doesn't match the batch's majority date.

    Returns results_df unchanged if empty, if date_col is missing, or if
    there's no real majority to compare against.
    """
    if results_df.empty or date_col not in results_df.columns:
        return results_df

    majority = results_df[date_col].mode()
    if majority.empty:
        return results_df
    majority_date = majority.iloc[0]

    is_stale = results_df[date_col] != majority_date
    if is_stale.any():
        stale_tickers = results_df.loc[is_stale, ticker_col].tolist()
        logger.warning(
            f"Excluding {len(stale_tickers)} stale ticker(s) (latest data "
            f"date != batch majority {majority_date}): {stale_tickers}"
        )

    return results_df.loc[~is_stale].reset_index(drop=True)
