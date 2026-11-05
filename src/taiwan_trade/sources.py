"""Official Taiwanese open datasets used by this project and how to download them."""
import json
import time
import urllib.request
from pathlib import Path

USER_AGENT = "Mozilla/5.0 (taiwan-trade-supply-chain-analysis)"
_MOF = "https://web02.mof.gov.tw/njswww/webMain.aspx?sys=220&type=4&kind=21&cycle=41&outmode=12&compmode=00&utf=1"
_MARKET = _MOF + "&ym=9000&outkind=12&codspc0=0,20,"

# name -> (data.gov.tw dataset id, publisher, download URL)
SOURCES = {
    "trade_total": (8378, "Ministry of Finance", _MOF + "&ym=9000&funid=i8101&outkind=1&fld0=1&codlst0=11001001"),
    "exports_major_goods": (8380, "Ministry of Finance", None),
    "trade_by_hs": (8383, "Ministry of Finance", None),
    "country_exports": (15392, "Ministry of Finance", "https://service.mof.gov.tw/public/data/statistic/trade/u2010ex.csv"),
    "country_imports": (15392, "Ministry of Finance", "https://service.mof.gov.tw/public/data/statistic/trade/u2010im.csv"),
    "index_total": (8385, "Ministry of Finance", None),
    "index_export_unit_value": (8386, "Ministry of Finance", None),
    "index_export_quantity": (8387, "Ministry of Finance", None),
    "port_containers": (8368, "Taiwan International Ports Corporation", "https://www.twport.com.tw/fapi/opendata?id=13878"),
    "x_china_hk": (28536, "Ministry of Finance", _MARKET + "&funid=op8201&fld1=1"),
    "x_usa": (28537, "Ministry of Finance", _MARKET + "&funid=op8201&fld2=1"),
    "x_japan": (28538, "Ministry of Finance", _MARKET + "&funid=op8201&fld3=1"),
    "x_korea": (28539, "Ministry of Finance", _MARKET + "&funid=op8201&fld4=1"),
    "x_asean": (28540, "Ministry of Finance", _MARKET + "&funid=op8201&fld6=1"),
    "x_germany": (28541, "Ministry of Finance", _MARKET + "&funid=op8201&fld5=1"),
    "m_china_hk": (28543, "Ministry of Finance", _MARKET + "&funid=op8202&fld1=1"),
    "m_usa": (28544, "Ministry of Finance", _MARKET + "&funid=op8202&fld2=1"),
    "m_japan": (28554, "Ministry of Finance", _MARKET + "&funid=op8202&fld3=1"),
    "m_korea": (28555, "Ministry of Finance", _MARKET + "&funid=op8202&fld4=1"),
    "m_asean": (28557, "Ministry of Finance", _MARKET + "&funid=op8202&fld6=1"),
    "m_germany": (28558, "Ministry of Finance", _MARKET + "&funid=op8202&fld5=1"),
}


def _get(url, retries=3):
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                return response.read()
        except OSError:
            if attempt == retries - 1:
                raise
            time.sleep(5 * (attempt + 1))
    raise RuntimeError("unreachable")


def resolve_url(dataset_id):
    """Ask the national open data portal for a dataset's current CSV link."""
    meta = json.loads(_get(f"https://data.gov.tw/api/v2/rest/dataset/{dataset_id}"))["result"]
    return next(r["resourceDownloadUrl"] for r in meta["distribution"] if r.get("resourceFormat") == "CSV")


def download_all(raw_dir):
    """Download every source. A file is replaced only if the new copy has content, so a failed
    or empty response never destroys the last good snapshot. Returns {name: error} for failures."""
    raw_dir = Path(raw_dir)
    raw_dir.mkdir(parents=True, exist_ok=True)
    failures = {}
    for name, (dataset_id, _, url) in SOURCES.items():
        try:
            payload = _get(url or resolve_url(dataset_id))
            if len(payload) < 500:
                raise ValueError(f"suspiciously small response ({len(payload)} bytes)")
            (raw_dir / f"{name}.csv").write_bytes(payload)
            print(f"{name:<28} {len(payload):>9,} bytes")
        except Exception as exc:  # keep going: one source being down should not stop the rest
            failures[name] = f"{type(exc).__name__}: {exc}"
            print(f"{name:<28} FAILED {failures[name]}")
    return failures
