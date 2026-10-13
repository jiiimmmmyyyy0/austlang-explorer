"""Check a downloaded AUSTLANG file and save it where the app reads it.

AIATSIS launched AustLang Online (version 3) in June 2026, and the old direct
CSV link stopped working, so the file is now downloaded in a browser:

    1. Open https://aiatsis.gov.au/austlang/dataResources
    2. Leave every field ticked and click "Download as a CSV".
    3. From the project folder, run:
           python scripts/download_data.py path/to/the/file.csv

The file is copied to data/austlang.csv, and the download date is recorded in
data/austlang_source.json so the About screen can show it.
"""
from __future__ import annotations

import json
import shutil
import sys
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from explorer.data_loader import load_languages  # noqa: E402  (needs the path above)

DOWNLOAD_PAGE = "https://aiatsis.gov.au/austlang/dataResources"
DATASET_PAGE = "https://data.gov.au/data/dataset/austlang-dataset-001"
TARGET = PROJECT_ROOT / "data" / "austlang.csv"
INFO_FILE = PROJECT_ROOT / "data" / "austlang_source.json"

HOW_TO_DOWNLOAD = f"""Download the AUSTLANG file in your browser first:
  1. Open {DOWNLOAD_PAGE}
  2. Leave every field ticked and click "Download as a CSV".
  3. Run:  python scripts/download_data.py path/to/the/file.csv"""


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(HOW_TO_DOWNLOAD)
        return 1
    TARGET.parent.mkdir(exist_ok=True)
    source = Path(argv[1]).expanduser()
    if not source.is_file():
        print(f"Can't find {source}. Check the path and try again.")
        return 1
    if source.resolve() != TARGET.resolve():
        shutil.copyfile(source, TARGET)
    origin = f"browser download from {DOWNLOAD_PAGE} ({source.name})"

    try:
        languages, report = load_languages(TARGET)
    except ValueError as error:
        print(f"\nThe file was saved but can't be used: {error}")
        return 1

    print(f"\nSaved {TARGET.relative_to(PROJECT_ROOT)}")
    print(f"  rows read:              {report.rows_read}")
    print(f"  language varieties kept: {report.rows_kept}  (minimum needed: 200)")
    print(f"  removed (no code/name): {report.missing_code_or_name}")
    print(f"  removed (repeated code): {report.duplicate_codes}")
    print(f"  no coordinates:         {report.no_coordinates}")
    print(f"  invalid coordinates:    {report.invalid_coordinates}")
    print(f"  alternative names:      {report.alternative_names_found}")
    print(f"  state column present:   {report.has_state_column}")
    print(f"  columns used:           {', '.join(report.columns_used.values())}")
    print(f"  columns not used:       {', '.join(report.columns_ignored) or 'none'}")

    INFO_FILE.write_text(json.dumps({
        "source": origin,
        "dataset_page": DATASET_PAGE,
        "licence": "CC BY 4.0",
        "downloaded": date.today().isoformat(),
        "rows_read": report.rows_read,
        "rows_kept": report.rows_kept,
    }, indent=2) + "\n", encoding="utf-8")
    print(f"Recorded the download details in {INFO_FILE.relative_to(PROJECT_ROOT)}")

    if not report.meets_minimum:
        print("\nWARNING: fewer than 200 records survived cleaning. Check you downloaded the full file.")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
