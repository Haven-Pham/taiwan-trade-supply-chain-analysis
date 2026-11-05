"""Loads the raw government CSVs into tidy, English-labelled monthly tables.

The sources mix Republic of China (ROC) years with Gregorian years, UTF-8 with Big5,
and plain numbers with thousands separators. Everything is normalised here, and all
values are returned in US$ million unless a function says otherwise.
"""
import io
import os
import re
from pathlib import Path

import pandas as pd

# The frozen snapshot by default; the dashboard refresh points this at a freshly downloaded copy.
RAW_DIR = Path(os.environ.get("TAIWAN_TRADE_RAW_DIR", Path(__file__).resolve().parents[2] / "data" / "raw"))

SECTIONS = {
    1: "Live animals & animal products", 2: "Vegetable products", 3: "Fats & oils", 4: "Prepared foods, beverages, tobacco",
    5: "Mineral products", 6: "Chemicals", 7: "Plastics & rubber", 8: "Hides & leather", 9: "Wood products",
    10: "Pulp & paper", 11: "Textiles", 12: "Footwear & headgear", 13: "Stone, ceramics, glass",
    14: "Jewellery & precious metals", 15: "Base metals", 16: "Machinery & electrical equipment",
    17: "Transport equipment", 18: "Optical & precision instruments", 19: "Other",
}
ELECTRONICS = 16

MARKETS = {"china_hk": "China & Hong Kong", "usa": "United States", "asean": "ASEAN", "japan": "Japan",
           "korea": "South Korea", "germany": "Germany"}

PORTS = {"基隆港": "Keelung", "臺北港": "Taipei", "臺中港": "Taichung", "高雄港": "Kaohsiung",
         "花蓮港": "Hualien", "蘇澳港": "Suao", "安平港": "Anping", "布袋港": "Budai"}

# Regional subtotals in the country files; everything else is a single country.
REGION_COLUMNS = {"總計", "亞洲", "中東", "歐洲", "北美洲", "中美洲", "南美洲", "大洋洲", "非洲"}

COUNTRY_EN = {
    "中國大陸": "China", "香港": "Hong Kong", "美國": "United States", "日本": "Japan", "韓國": "South Korea",
    "新加坡": "Singapore", "馬來西亞": "Malaysia", "越南": "Vietnam", "泰國": "Thailand", "菲律賓": "Philippines",
    "印尼": "Indonesia", "印度": "India", "德國": "Germany", "荷蘭": "Netherlands", "英國": "United Kingdom",
    "澳大利亞": "Australia", "沙烏地阿拉伯": "Saudi Arabia", "卡達": "Qatar", "墨西哥": "Mexico", "加拿大": "Canada",
    "土耳其": "Turkey", "科威特": "Kuwait", "阿拉伯聯合大公國": "United Arab Emirates", "俄羅斯": "Russia",
    "義大利": "Italy", "法國": "France", "巴西": "Brazil", "瑞士": "Switzerland",
    "愛爾蘭": "Ireland", "安哥拉": "Angola", "阿曼": "Oman",
}


def parse_roc_period(label):
    """'115年 9月' -> Timestamp('2026-09-01'). Returns None for annual rows such as '115年'."""
    match = re.fullmatch(r"\s*(\d{2,3})年\s*(\d{1,2})月\s*", str(label))
    if not match:
        return None
    return pd.Timestamp(year=int(match.group(1)) + 1911, month=int(match.group(2)), day=1)


def parse_gregorian_period(label):
    """'2026年9月' -> Timestamp('2026-09-01'). Returns None for annual rows such as '2026年'."""
    match = re.fullmatch(r"\s*(\d{4})年\s*(\d{1,2})月\s*", str(label))
    if not match:
        return None
    return pd.Timestamp(year=int(match.group(1)), month=int(match.group(2)), day=1)


def to_number(series):
    """Convert a column that may hold '128,239.00', blanks or '-' to floats."""
    cleaned = series.astype(str).str.replace(",", "", regex=False).str.strip()
    return pd.to_numeric(cleaned.replace({"": None, "-": None, "nan": None}), errors="coerce")


def read_csv(name, raw_dir=RAW_DIR, **kwargs):
    raw = (Path(raw_dir) / f"{name}.csv").read_bytes()
    for encoding in ("utf-8-sig", "cp950"):
        try:
            text = raw.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise ValueError(f"{name}: unknown encoding")
    return pd.read_csv(io.StringIO(text), dtype=str, **kwargs)


def _monthly(frame, parser=parse_roc_period):
    """Index a table by month, dropping the annual subtotal rows mixed into the files."""
    periods = frame.iloc[:, 0].map(parser)
    out = frame.loc[periods.notna()].copy()
    out.index = pd.DatetimeIndex(periods[periods.notna()], name="month")
    return out.iloc[:, 1:].apply(to_number).sort_index()


def load_trade_total(raw_dir=RAW_DIR):
    """Monthly exports, imports and balance, US$ million."""
    table = _monthly(read_csv("trade_total", raw_dir))
    table.columns = ["trade", "exports", "imports", "balance"]
    return table


def _section_number(label):
    match = re.search(r"(\d{1,2})\.", label)
    return int(match.group(1)) if match else None


def load_market_sections(flow, market, raw_dir=RAW_DIR):
    """Monthly trade with one market by HS section, US$ million. flow is 'x' (exports) or 'm' (imports)."""
    table = _monthly(read_csv(f"{flow}_{market}", raw_dir)) / 1_000
    columns = {}
    for column in table.columns:
        if column.startswith("總計"):
            columns[column] = "total"
        else:
            number = _section_number(column)
            columns[column] = SECTIONS[number] if number in SECTIONS else column
    return table.rename(columns=columns)


def load_trade_by_hs(raw_dir=RAW_DIR):
    """Monthly exports and imports by HS section, US$ million, in long form."""
    table = _monthly(read_csv("trade_by_hs", raw_dir)) / 1_000
    numerals = ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十", "十一", "十二", "十三", "十四", "十五",
                "十六", "十七", "十八", "十九", "二十", "二十一"]
    rows = []
    for column in table.columns:
        parts = column.split("/")
        if len(parts) < 3:
            continue
        flow = "exports" if "出口" in parts[1] else "imports"
        match = re.search(r"第(.+?)類", parts[2])
        if not match or match.group(1) not in numerals:
            continue
        number = numerals.index(match.group(1)) + 1
        section = SECTIONS.get(number, SECTIONS[19])
        rows.append(table[column].rename("value").to_frame().assign(flow=flow, section=section))
    long = pd.concat(rows).reset_index()
    return long.groupby(["month", "flow", "section"], as_index=False)["value"].sum()


def load_major_goods(raw_dir=RAW_DIR):
    """Monthly exports of the machinery sub-groups, US$ million: electronic parts, machinery, ICT & AV products."""
    table = _monthly(read_csv("exports_major_goods", raw_dir))
    labels = {"電子零組件": "Electronic components", "資通與視聽產品": "ICT & audio-visual products", "機械": "Machinery"}
    out = {}
    for column in table.columns:
        tail = column.split("/")[-1].strip()
        for key, english in labels.items():
            if re.fullmatch(rf"\(\d\){key}", tail):
                out[english] = table[column]
    return pd.DataFrame(out)


def load_countries(flow, raw_dir=RAW_DIR):
    """Monthly trade by single country, US$ million (regional subtotals removed). flow: 'exports' or 'imports'."""
    table = _monthly(read_csv(f"country_{flow}", raw_dir), parse_gregorian_period) / 1_000
    table.columns = [c.replace("(千元)", "").strip() for c in table.columns]
    return table[[c for c in table.columns if c not in REGION_COLUMNS]]


def load_indices(raw_dir=RAW_DIR):
    """Monthly chain indices (2021 = 100): value, quantity and unit value for all goods and section 16."""
    total = _monthly(read_csv("index_total", raw_dir))
    out = pd.DataFrame({
        "export_value": total["價值指數－出口"],
        "export_quantity": total["數量指數－出口"],
        "export_unit_value": total["單位價值指數－出口"],
        "terms_of_trade": total["純貿易條件"],
    })
    machinery = "第十六類　機械及電機設備"
    out["machinery_quantity"] = _monthly(read_csv("index_export_quantity", raw_dir))[machinery]
    out["machinery_unit_value"] = _monthly(read_csv("index_export_unit_value", raw_dir))[machinery]
    return out


def load_ports(raw_dir=RAW_DIR):
    """Monthly container throughput by port in TEU, long form. The all-port total row is excluded."""
    table = read_csv("port_containers", raw_dir)
    table = table.iloc[:, :5]
    table.columns = ["period", "port_zh", "total", "inbound", "outbound"]
    table = table[table["period"].astype(str).str.fullmatch(r"\d{6}")]
    table["month"] = pd.to_datetime(table["period"], format="%Y%m")
    for column in ["total", "inbound", "outbound"]:
        table[column] = to_number(table[column])
    all_ports = table[table["port_zh"] == "國際商港"]
    table = table[table["port_zh"].isin(PORTS)].assign(port=lambda d: d["port_zh"].map(PORTS))
    return table[["month", "port", "total", "inbound", "outbound"]].reset_index(drop=True), \
        all_ports.set_index("month")[["total", "inbound", "outbound"]].sort_index()


def load_quantity_by_section(raw_dir=RAW_DIR):
    """Monthly export quantity index (2021 = 100) by HS section, with English section names."""
    table = _monthly(read_csv("index_export_quantity", raw_dir)).drop(columns="總計")
    numerals = ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十", "十一", "十二", "十三", "十四", "十五",
                "十六", "十七", "十八"]
    names = {c: SECTIONS[numerals.index(re.match(r"第(.+?)類", c).group(1)) + 1] for c in table.columns}
    return table.rename(columns=names)
