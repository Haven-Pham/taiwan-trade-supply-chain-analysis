"""Calculations behind the analysis: like-for-like periods, concentration, value density and exposure."""
import numpy as np
import pandas as pd


def same_months(frame, year, last_month):
    """Rows of a monthly table for January to last_month of one year, so partial years compare fairly."""
    index = frame.index
    return frame[(index.year == year) & (index.month <= last_month)]


def hhi(values, total=None):
    """Herfindahl-Hirschman index on the 0-10,000 scale. Pass the published total as the denominator
    when some value is unallocated, so that missing detail does not inflate the shares."""
    values = pd.Series(values, dtype=float).fillna(0)
    denominator = values.sum() if total is None else total
    if denominator <= 0:
        raise ValueError("HHI needs a positive total")
    return float(((values / denominator) ** 2).sum() * 10_000)


def rolling_sum(series, months=12):
    return series.rolling(months).sum().dropna()


def first_lasting_crossover(leader, follower, months=12):
    """First month from which leader's rolling total stays above follower's through the end of the data."""
    gap = (rolling_sum(leader, months) - rolling_sum(follower, months)).dropna()
    below = gap[gap <= 0]
    after = gap.index[gap.index > below.index.max()] if len(below) else gap.index
    return after.min() if len(after) else None


def growth_multiple(index_series, base_year, year, last_month):
    """Ratio of an index's mean between two years, over the same calendar months."""
    return float(same_months(index_series.to_frame(), year, last_month).mean().iloc[0]
                 / same_months(index_series.to_frame(), base_year, last_month).mean().iloc[0])


def value_density(trade_usd_million, teu):
    """Annual trade value per TEU handled, in US$. Combines air and sea trade, so it is an indicator of
    how value has separated from container volume, not the value of the goods inside a container."""
    frame = pd.DataFrame({"trade": trade_usd_million, "teu": teu}).dropna()
    annual = frame.groupby(frame.index.year).sum()
    annual["usd_per_teu"] = annual["trade"] * 1e6 / annual["teu"]
    annual["months"] = frame.groupby(frame.index.year).size()
    return annual


def yoy_of_rolling(series, months=12):
    """Year-on-year growth of a rolling 12-month total, which removes seasonality."""
    return rolling_sum(series, months).pct_change(12).dropna()


def coupling(teu, series_by_name, start=None, end=None):
    """Correlation between year-on-year TEU growth and the growth of each value series."""
    base = yoy_of_rolling(teu)
    rows = {}
    for name, series in series_by_name.items():
        joined = pd.concat([base.rename("teu"), yoy_of_rolling(series).rename("value")], axis=1).dropna().loc[start:end]
        rows[name] = {"correlation": joined["teu"].corr(joined["value"]), "months": len(joined)}
    return pd.DataFrame(rows).T


def lead_lag(leading, following, max_lag=6, start="2015"):
    """Correlation of following's growth with leading's growth k months earlier, using 3-month totals."""
    a = leading.rolling(3).sum().pct_change(12)
    b = following.rolling(3).sum().pct_change(12)
    joined = pd.concat([a.rename("lead"), b.rename("follow")], axis=1).dropna().loc[start:]
    return pd.Series({k: joined["follow"].corr(joined["lead"].shift(k)) for k in range(max_lag + 1)}, name="correlation")


def stress_test(lanes, total_exports, shocks=(0.10, 0.20, 0.30)):
    """First-order exposure of total exports to a fall in one lane's value.

    lanes: {lane name: exports in US$ million over the period}. Assumes no diversion to other markets
    and no change in the rest of trade, so it sizes exposure and is not a forecast.
    """
    rows = []
    for name, value in lanes.items():
        row = {"lane": name, "exports_usd_m": value, "share_of_exports_pct": value / total_exports * 100}
        for shock in shocks:
            row[f"impact_at_{int(shock * 100)}pct_fall_usd_m"] = value * shock
            row[f"export_loss_at_{int(shock * 100)}pct_fall_pct"] = value * shock / total_exports * 100
        rows.append(row)
    return pd.DataFrame(rows).sort_values("exports_usd_m", ascending=False, ignore_index=True)


def reconciliation_gap(parts, published_total):
    """Published total minus the sum of the published parts; returns the monthly gap and its share."""
    gap = published_total - parts.sum(axis=1)
    return pd.DataFrame({"gap": gap, "gap_pct": gap / published_total * 100})


def round_trip(values, decimals=1):
    """Round floats for JSON output; NaN becomes None."""
    return [None if pd.isna(v) or np.isinf(v) else round(float(v), decimals) for v in values]
