"""Builds the Excel results workbook from the CSV tables in reports/tables.

    python scripts/build_excel_report.py

Run scripts/run_notebook.py first so the tables are current.
"""
from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from openpyxl.drawing.image import Image
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).resolve().parent.parent
TABLES = ROOT / "reports" / "tables"
FIGURES = ROOT / "reports" / "figures"

CONFIG = {
    "file": "Taiwan_Trade_Supply_Chain_Results.xlsx",
    "title": "Taiwan's Export Boom Through a Supply Chain Lens",
    "subtitle": "What is growing, where it goes, what the ports see, and how exposed it is. January to September of each year unless stated.",
    "findings": [
        "Exports reached US$661.5B in Jan-Sep 2026, up 46.2% on a year earlier. Imports were US$500.9B.",
        "Machinery & electrical equipment is 84.5% of exports (61.9% in 2021) and supplied 106% of the increase since 2021. All other exports fell 17%.",
        "The US went from 14.5% to 31.4% of exports and China & Hong Kong from 42.7% to 24.2%. Machinery is 91.6% of what the US buys.",
        "Export value multiplied by 2.31: quantity by 1.73 and unit value by 1.33. 16 of 17 indexed product groups ship less than in 2021.",
        "Containers fell 13.1% while trade value multiplied by 1.93. Trade value per TEU went from US$51,840 to US$115,298.",
        "Machinery to the US alone is 28.8% of exports, so a 20% fall in that lane would remove about 5.8% of exports. This is exposure, not a forecast.",
    ],
    "sheets": {
        "Data reconciliation": ("data_reconciliation.csv", "values with no product or country, against the published totals"),
        "Product concentration": ("product_concentration.csv", "machinery share and product HHI by year"),
        "Concentration compare": ("concentration_comparison.csv", "product HHI against market HHI"),
        "Machinery subgroups": ("machinery_subgroups.csv", "official export sub-groups inside machinery"),
        "Market summary": ("market_summary.csv", "share of exports and machinery share of each market's basket"),
        "Market share rolling 12": ("market_share_rolling12.csv", "share of exports by market, monthly"),
        "Volume and price": ("volume_price_multiples.csv", "value, quantity and unit value multiples, 2021 to 2026"),
        "Quantity by section": ("quantity_by_section.csv", "export quantity index by product group, 2021 = 100"),
        "Value vs containers": ("value_vs_containers.csv", "TEU, trade value and value per TEU"),
        "TEU coupling": ("teu_coupling.csv", "correlation of year-on-year TEU with trade series, by period"),
        "Port share": ("port_share.csv", "share of container throughput by port and year"),
        "Machinery import sources": ("machinery_import_sources.csv", "where machinery imports come from"),
        "Imports lead exports": ("imports_lead_exports.csv", "lead-lag correlation of machinery imports and exports"),
        "Stress test": ("stress_test.csv", "first-order effect of a fall in each trade lane"),
    },
    "figure": "01_what_is_growing.png",
    "source": "Ministry of Finance and Taiwan International Ports Corporation, via data.gov.tw. Snapshot through September 2026.",
}

HEADER_FILL = PatternFill("solid", fgColor="1F4E79")
HEADER_FONT = Font(bold=True, color="FFFFFF")
TITLE_FONT = Font(bold=True, size=16, color="1F4E79")


def number_format(column, series):
    name = column.lower()
    if not pd.api.types.is_numeric_dtype(series):
        return None
    if "pct" in name or "(%)" in name:
        return '0.0"%"'
    if "usd" in name or "$m" in name:
        return '"$"#,##0'
    if name == "teu":
        return "#,##0"
    if "year" == name or "months" in name:
        return "0"
    if series.abs().max() >= 1000:
        return "#,##0"
    return "0.00"


def add_table_sheet(wb, title, frame):
    ws = wb.create_sheet(title[:31])
    ws.append(list(frame.columns))
    for row in frame.itertuples(index=False):
        ws.append([None if pd.isna(v) else (v.item() if hasattr(v, "item") else v) for v in row])
    for cell in ws[1]:
        cell.fill, cell.font = HEADER_FILL, HEADER_FONT
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws.row_dimensions[1].height = 45
    for idx, column in enumerate(frame.columns, start=1):
        fmt = number_format(column, frame[column])
        letter = get_column_letter(idx)
        if fmt:
            for cell in ws[letter][1:]:
                cell.number_format = fmt
        longest = max((len(str(v)) for v in frame[column].head(200)), default=8)
        ws.column_dimensions[letter].width = min(max(longest + 2, 14), 44)
    ws.freeze_panes = "B2"
    ws.auto_filter.ref = ws.dimensions


def main():
    wb = Workbook()
    ws = wb.active
    ws.title = "Summary"
    ws["A1"] = CONFIG["title"]
    ws["A1"].font = TITLE_FONT
    ws["A2"] = CONFIG["subtitle"]
    ws["A2"].font = Font(italic=True, color="555555")
    row = 4
    ws.cell(row, 1, "Key findings").font = Font(bold=True, size=12)
    for finding in CONFIG["findings"]:
        row += 1
        ws.cell(row, 1, f"• {finding}").alignment = Alignment(wrap_text=True, vertical="top")
        ws.row_dimensions[row].height = 32
    row += 2
    ws.cell(row, 1, "Sheets in this workbook").font = Font(bold=True, size=12)
    for sheet, (_, description) in CONFIG["sheets"].items():
        row += 1
        ws.cell(row, 1, f"{sheet}: {description}")
    row += 2
    ws.cell(row, 1, "Source: " + CONFIG["source"]).font = Font(color="555555")
    ws.column_dimensions["A"].width = 120
    if (FIGURES / CONFIG["figure"]).exists():
        image = Image(str(FIGURES / CONFIG["figure"]))
        scale = 620 / image.width
        image.width, image.height = image.width * scale, image.height * scale
        ws.add_image(image, f"A{row + 2}")

    for sheet, (csv_name, _) in CONFIG["sheets"].items():
        add_table_sheet(wb, sheet, pd.read_csv(TABLES / csv_name))

    out = ROOT / "reports" / CONFIG["file"]
    wb.save(out)
    print(f"Wrote {out.relative_to(ROOT)} with {len(wb.sheetnames)} sheets")


if __name__ == "__main__":
    main()
