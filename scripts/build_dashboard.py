"""Builds dashboard/data.json from the raw files. The dashboard always shows the latest month.

    python scripts/build_dashboard.py
"""
import json
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from taiwan_trade import data as d  # noqa: E402
from taiwan_trade import metrics as m  # noqa: E402

BASE_YEAR = 2021
START_YEAR = 2011
TOP_COUNTRIES = 15
MACHINERY = d.SECTIONS[d.ELECTRONICS]
MARKET_ZH = {"china_hk": "中國大陸及香港", "usa": "美國", "asean": "東協", "japan": "日本", "korea": "南韓", "germany": "德國"}
PORT_ZH = {english: zh for zh, english in d.PORTS.items()}


def rounded(series, decimals=1):
    return m.round_trip(series.tolist(), decimals)


def section_names_zh():
    """Traditional Chinese section names, taken from the official column headers."""
    header = d.read_csv("x_usa").columns[2:]
    names = {}
    for column in header:
        match = re.match(r"(\d{1,2})\.(.+?)\(千美元\)", column)
        if match:
            names[d.SECTIONS[int(match.group(1))]] = match.group(2)
    return names


def main():
    trade = d.load_trade_total()
    hs = d.load_trade_by_hs()
    indices = d.load_indices()
    ports, all_ports = d.load_ports()
    # Sources publish on different days. Stop at the last month they all cover, so that a partial
    # update never compares nine months of trade with eight months of containers.
    latest = min(trade.index.max(), hs["month"].max(), indices.dropna().index.max(), all_ports.index.max(),
                 d.load_market_sections("x", "usa").index.max(), d.load_countries("imports").index.max())
    last_month = latest.month
    year = latest.year
    months = trade.index

    sections = {flow: hs[hs["flow"] == flow].pivot(index="month", columns="section", values="value").reindex(months)
                for flow in ("exports", "imports")}
    period = lambda frame, y: m.same_months(frame, y, last_month)  # noqa: E731
    years = list(range(START_YEAR, year + 1))

    by_year = {}
    for flow, table in sections.items():
        machinery = [float(period(table, y)[MACHINERY].sum()) for y in years]
        rest = [float(period(table, y).drop(columns=MACHINERY).sum().sum()) for y in years]
        by_year[flow] = {"machinery": m.round_trip(machinery, 0), "rest": m.round_trip(rest, 0)}

    section_table = {}
    for flow, table in sections.items():
        latest_values = period(table, year).sum().sort_values(ascending=False)
        base_values = period(table, BASE_YEAR).sum()
        section_table[flow] = [{"name": name, "value": round(float(v), 0), "base": round(float(base_values[name]), 0)}
                               for name, v in latest_values.items()]

    goods = d.load_major_goods().rolling(12).sum().dropna().loc["2012":]

    markets = {}
    for flow in ("x", "m"):
        total = trade["exports" if flow == "x" else "imports"]
        markets[flow] = {}
        for key in d.MARKETS:
            table = d.load_market_sections(flow, key).reindex(months)
            share = table["total"].rolling(12).sum() / total.rolling(12).sum() * 100
            markets[flow][key] = {
                "share": rounded(share.loc["2012":], 1),
                "machinery_ytd": round(float(period(table, year)[MACHINERY].sum()), 0),
                "machinery_base": round(float(period(table, BASE_YEAR)[MACHINERY].sum()), 0),
                "total_ytd": round(float(period(table, year)["total"].sum()), 0),
                "total_base": round(float(period(table, BASE_YEAR)["total"].sum()), 0),
            }
    share_months = months[months >= pd.Timestamp("2012-01-01")]

    countries = {}
    for flow in ("exports", "imports"):
        table = d.load_countries(flow)
        countries[flow] = {}
        for y in years:
            published = float(period(trade[[flow]], y).sum().iloc[0])
            top = period(table, y).sum().sort_values(ascending=False).head(TOP_COUNTRIES)
            countries[flow][str(y)] = [{"zh": name, "en": d.COUNTRY_EN.get(name, name), "share": round(float(v) / published * 100, 1)}
                                       for name, v in top.items()]
        unallocated = m.reconciliation_gap(table, trade[flow])
        countries[f"{flow}_unallocated_pct"] = round(
            float(period(unallocated, year)["gap"].sum()) / float(period(trade[[flow]], year).sum().iloc[0]) * 100, 1)

    index_columns = ["export_value", "export_quantity", "export_unit_value", "machinery_quantity"]
    smooth = indices[index_columns].rolling(12).mean().loc["2015":]
    quantity = period(d.load_quantity_by_section(), year).mean().sort_values(ascending=False)

    teu_by_year = [float(period(all_ports, y)["total"].sum()) for y in years]
    value_by_year = [float(period(trade, y)["trade"].sum()) for y in years]
    main_ports = ["Kaohsiung", "Keelung", "Taichung", "Taipei"]
    port_year = ports.pivot_table(index=ports["month"].dt.year, columns="port", values="total", aggfunc="sum")[main_ports]
    port_period = ports[ports["month"].dt.month <= last_month].pivot_table(
        index=ports["month"].dt.year, columns="port", values="total", aggfunc="sum")[main_ports].loc[START_YEAR:]

    x_total = float(period(trade, year)["exports"].sum())
    x_prev = float(period(trade, year - 1)["exports"].sum())
    usa = d.load_market_sections("x", "usa")
    china_hk = d.load_market_sections("x", "china_hk")
    teu_base = float(period(all_ports, BASE_YEAR)["total"].sum())
    teu_now = float(period(all_ports, year)["total"].sum())
    trade_base = float(period(trade, BASE_YEAR)["trade"].sum())
    trade_now = float(period(trade, year)["trade"].sum())
    machinery_now = float(period(sections["exports"], year)[MACHINERY].sum())
    machinery_base = float(period(sections["exports"], BASE_YEAR)[MACHINERY].sum())
    x_base = float(period(trade, BASE_YEAR)["exports"].sum())
    rest_now = float(period(sections["exports"], year).drop(columns=MACHINERY).sum().sum())
    rest_base = float(period(sections["exports"], BASE_YEAR).drop(columns=MACHINERY).sum().sum())
    imports_now = float(period(trade, year)["imports"].sum())
    imports_base = float(period(trade, BASE_YEAR)["imports"].sum())
    crossover = m.first_lasting_crossover(usa["total"], china_hk["total"])

    kpis = {
        "exports": x_total,
        "exports_yoy": (x_total / x_prev - 1) * 100,
        "machinery_share": machinery_now / x_total * 100,
        "machinery_share_base": machinery_base / x_base * 100,
        "machinery_growth_contribution": (machinery_now - machinery_base) / (x_total - x_base) * 100,
        "rest_now": rest_now,
        "rest_change": (rest_now / rest_base - 1) * 100,
        "import_machinery_share": float(period(sections["imports"], year)[MACHINERY].sum()) / imports_now * 100,
        "import_machinery_share_base": float(period(sections["imports"], BASE_YEAR)[MACHINERY].sum()) / imports_base * 100,
        "us_basket_machinery": float(period(usa, year)[MACHINERY].sum()) / float(period(usa, year)["total"].sum()) * 100,
        "us_machinery_share_base": float(period(usa, BASE_YEAR)[MACHINERY].sum()) / x_base * 100,
        "us_share": float(period(usa, year)["total"].sum()) / x_total * 100,
        "us_share_base": float(period(usa, BASE_YEAR)["total"].sum()) / x_base * 100,
        "china_hk_share": float(period(china_hk, year)["total"].sum()) / x_total * 100,
        "china_hk_share_base": float(period(china_hk, BASE_YEAR)["total"].sum()) / x_base * 100,
        "us_machinery_share": float(period(usa, year)[MACHINERY].sum()) / x_total * 100,
        "teu": teu_now,
        "teu_change": (teu_now / teu_base - 1) * 100,
        "usd_per_teu": trade_now * 1e6 / teu_now,
        "usd_per_teu_base": trade_base * 1e6 / teu_base,
        "trade_multiple": trade_now / trade_base,
        "quantity_multiple": m.growth_multiple(indices["export_quantity"], BASE_YEAR, year, last_month),
        "price_multiple": m.growth_multiple(indices["export_unit_value"], BASE_YEAR, year, last_month),
    }

    payload = {
        "asOf": latest.strftime("%Y-%m"),
        "lastMonth": last_month,
        "year": year,
        "baseYear": BASE_YEAR,
        "machinery": MACHINERY,
        "years": years,
        "crossover": crossover.strftime("%Y-%m") if crossover is not None else None,
        "kpis": {k: round(v, 2) for k, v in kpis.items()},
        "byYear": by_year,
        "sections": section_table,
        "sectionZh": section_names_zh(),
        "goods": {"months": goods.index.strftime("%Y-%m").tolist(), **{c: rounded(goods[c], 0) for c in goods.columns}},
        "marketNames": {k: {"en": d.MARKETS[k], "zh": MARKET_ZH[k]} for k in d.MARKETS},
        "markets": markets,
        "shareMonths": share_months.strftime("%Y-%m").tolist(),
        "countries": countries,
        "indices": {"months": smooth.index.strftime("%Y-%m").tolist(), **{c: rounded(smooth[c], 1) for c in smooth.columns}},
        "quantity": [{"name": n, "value": round(float(v), 1)} for n, v in quantity.items()],
        "quantityBelow": int((quantity < 100).sum()),
        "ports": {"years": years, "teu": m.round_trip(teu_by_year, 0), "trade": m.round_trip(value_by_year, 0),
                  "names": {p: {"en": p, "zh": PORT_ZH[p]} for p in main_ports},
                  "byPort": {p: m.round_trip(port_period[p].tolist(), 0) for p in main_ports},
                  "shareYears": [int(y) for y in port_year.index],
                  "share": {p: rounded(port_year[p] / port_year.sum(axis=1) * 100, 1) for p in main_ports}},
    }
    target = ROOT / "dashboard" / "data.json"
    target.parent.mkdir(exist_ok=True)
    if target.exists() and json.loads(target.read_text(encoding="utf-8"))["asOf"] > payload["asOf"]:
        print(f"Kept the existing dashboard data: a source only reaches {payload['asOf']} in this run")
        return
    target.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Wrote {target.relative_to(ROOT)}: data through {payload['asOf']}, {target.stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    main()
