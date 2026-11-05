"""Downloads the latest official data, into data/raw unless another folder is given.

    python scripts/download_data.py [folder]

Exits with an error if any source failed, but keeps the last good copy of that file.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from taiwan_trade.sources import download_all  # noqa: E402

failures = download_all(sys.argv[1] if len(sys.argv) > 1 else ROOT / "data" / "raw")
if failures:
    print(f"\n{len(failures)} source(s) failed: {', '.join(failures)}")
    sys.exit(1)
print("\nAll sources downloaded.")
