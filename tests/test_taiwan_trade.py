"""Unit tests for parsing and metrics, plus integrity checks on the committed data snapshot."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from taiwan_trade import data as d  # noqa: E402
from taiwan_trade import metrics as m  # noqa: E402


@pytest.mark.parametrize("label,expected", [
    ("115年 9月", pd.Timestamp("2026-09-01")),
    ("90年 1月", pd.Timestamp("2001-01-01")),
    ("100年12月", pd.Timestamp("2011-12-01")),
])
def test_roc_months_convert_to_gregorian(label, expected):
    assert d.parse_roc_period(label) == expected


@pytest.mark.parametrize("label", ["115年", "90年", "總計", "", None])
def test_annual_and_other_rows_are_not_months(label):
    assert d.parse_roc_period(label) is None


def test_gregorian_months():
    assert d.parse_gregorian_period("2026年9月") == pd.Timestamp("2026-09-01")
    assert d.parse_gregorian_period("2026年") is None


def test_numbers_with_separators_and_blanks():
    result = d.to_number(pd.Series(["128,239.00", "106", "", "-"]))
    assert result.iloc[0] == 128239.0 and result.iloc[1] == 106.0
    assert result.iloc[2:].isna().all()


def test_same_months_selects_like_for_like():
    frame = pd.DataFrame({"v": range(24)}, index=pd.date_range("2024-01-01", periods=24, freq="MS"))
    selected = m.same_months(frame, 2025, 3)
    assert list(selected["v"]) == [12, 13, 14]


def test_hhi_bounds_and_denominator():
    assert m.hhi([100]) == pytest.approx(10_000)
    assert m.hhi([50, 50]) == pytest.approx(5_000)
    assert m.hhi([50], total=100) == pytest.approx(2_500)  # unallocated value must not inflate the share
    with pytest.raises(ValueError):
        m.hhi([0, 0])


def test_crossover_requires_the_lead_to_last():
    months = pd.date_range("2020-01-01", periods=48, freq="MS")
    leader = pd.Series(np.r_[np.ones(24), np.full(24, 3.0)], index=months)
    follower = pd.Series(np.full(48, 2.0), index=months)
    crossed = m.first_lasting_crossover(leader, follower)
    assert crossed == months[30]  # the rolling sums tie at index 29; the leader is strictly ahead from index 30
    assert m.first_lasting_crossover(follower, leader) is None


def test_stress_test_arithmetic():
    table = m.stress_test({"A": 200.0, "B": 100.0}, total_exports=1000.0, shocks=(0.10,))
    assert list(table["lane"]) == ["A", "B"]
    assert table.loc[0, "impact_at_10pct_fall_usd_m"] == pytest.approx(20)
    assert table.loc[0, "export_loss_at_10pct_fall_pct"] == pytest.approx(2)


def test_value_density():
    months = pd.date_range("2025-01-01", periods=2, freq="MS")
    table = m.value_density(pd.Series([10.0, 10.0], index=months), pd.Series([1000.0, 1000.0], index=months))
    assert table.loc[2025, "usd_per_teu"] == pytest.approx(10_000)


# ---- integrity of the data snapshot ----

@pytest.fixture(scope="module")
def total():
    return d.load_trade_total()


def test_trade_series_has_no_missing_months(total):
    assert len(pd.date_range(total.index.min(), total.index.max(), freq="MS")) == len(total)
    assert total.index.is_unique


def test_balance_equals_exports_minus_imports(total):
    assert (total["exports"] - total["imports"] - total["balance"]).abs().max() < 0.01


def test_hs_sections_reconcile_with_total(total):
    hs = d.load_trade_by_hs()
    for flow, limit in [("exports", 1.0), ("imports", 9.0)]:
        parts = hs[hs["flow"] == flow].groupby("month")["value"].sum()
        gap = (total[flow] - parts).abs() / total[flow] * 100
        assert gap.max() < limit, f"{flow} HS sections differ from the total by {gap.max():.2f}%"


def test_market_sections_add_up_to_market_total():
    for flow in ["x", "m"]:
        for market in d.MARKETS:
            table = d.load_market_sections(flow, market)
            assert (table.drop(columns="total").sum(axis=1) - table["total"]).abs().max() < 0.05


def test_country_tables_have_unique_names_and_no_subtotals():
    for flow in ["exports", "imports"]:
        table = d.load_countries(flow)
        assert not table.columns.duplicated().any()
        assert not set(table.columns) & d.REGION_COLUMNS
        assert "美國" in table.columns


def test_country_parts_never_exceed_the_published_total(total):
    for flow in ["exports", "imports"]:
        gap = m.reconciliation_gap(d.load_countries(flow), total[flow])
        assert gap["gap"].min() > -1, f"{flow}: countries exceed the total"


def test_port_table_matches_the_all_port_row():
    ports, all_ports = d.load_ports()
    assert (ports.groupby("month")["total"].sum() - all_ports["total"]).abs().max() < 1
    assert set(ports["port"]) <= set(d.PORTS.values())
    assert (ports["total"] >= 0).all()
    assert all_ports["total"].notna().all()


def test_indices_are_based_on_2021():
    indices = d.load_indices()
    assert indices.loc["2021", "export_value"].mean() == pytest.approx(100, abs=1)
    assert indices.notna().all().all()


def test_major_goods_cover_the_three_machinery_groups():
    goods = d.load_major_goods()
    assert set(goods.columns) == {"Electronic components", "ICT & audio-visual products", "Machinery"}
    assert (goods >= 0).all().all()
