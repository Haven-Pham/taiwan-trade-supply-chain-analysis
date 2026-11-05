# Data

`raw/` holds the official files exactly as downloaded, through September 2026. The notebook and the README figures use this
snapshot, so they can be reproduced even after the sources are revised. To replace it with the current files, run
`python scripts/download_data.py`.

The dashboard refresh downloads into `data/latest/` instead, which is not committed, so it never changes the snapshot.

| File(s) | Content | Publisher | data.gov.tw dataset |
|---|---|---|---|
| `trade_total.csv` | Monthly exports, imports and balance | Ministry of Finance | 8378 |
| `exports_major_goods.csv` | Exports of major goods, including ICT and electronic components | Ministry of Finance | 8380 |
| `trade_by_hs.csv` | Exports and imports by HS section | Ministry of Finance | 8383 |
| `country_exports.csv`, `country_imports.csv` | Monthly trade by country | Ministry of Finance | 15392 |
| `index_total.csv`, `index_export_quantity.csv`, `index_export_unit_value.csv` | Chain indices, 2021 = 100 | Ministry of Finance | 8385, 8387, 8386 |
| `port_containers.csv` | Container throughput (TEU) by port | Taiwan International Ports Corporation | 8368 |
| `x_*.csv` | Exports to six markets by HS section | Ministry of Finance | 28536 to 28541 |
| `m_*.csv` | Imports from six markets by HS section | Ministry of Finance | 28543, 28544, 28554, 28555, 28557, 28558 |

The six markets are China & Hong Kong, the United States, Japan, South Korea, ASEAN and Germany.

## Things to know when reading the files

- Ministry of Finance files use Republic of China years in most tables: `115年 9月` is September 2026. The country files use
  Gregorian dates.
- Annual subtotal rows are mixed in with monthly rows, and the country files include regional subtotal columns. Both are
  removed when the files are loaded.
- Encoding differs by file (UTF-8 with BOM or Big5). `src/taiwan_trade/data.py` handles this.
- In `port_containers.csv` the row `國際商港` is the total for all international commercial ports.

## License

Published under the [Open Government Data License, version 1.0](https://data.gov.tw/license). Attribution belongs to the
publishers named above.
