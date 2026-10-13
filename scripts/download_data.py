"""Download the AUSTLANG dataset and check that the app can read it.

Run from the project folder:
    python scripts/download_data.py                 download from AIATSIS
    python scripts/download_data.py path/to/file.csv  use a file you downloaded in a browser

The file is saved as data/austlang.csv, and the download date is recorded in
data/austlang_source.json so the About screen can show it.
"""
from __future__ import annotations

import json
import shutil
import sys
import urllib.request
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from explorer.data_loader import load_languages  # noqa: E402  (needs the path above)

SOURCE_URL = "https://collection.aiatsis.gov.au/datasets/austlang/001.csv"
DATASET_PAGE = "https://data.gov.au/data/dataset/austlang-dataset-001"
TARGET = PROJECT_ROOT / "data" / "austlang.csv"
INFO_FILE = PROJECT_ROOT / "data" / "austlang_source.json"


def download(url: str, target: Path) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": "AUSTLANG-Explorer (UWA CITS1501 student project)"})
    with urllib.request.urlopen(request, timeout=120) as response, open(target, "wb") as out:
        shutil.copyfileobj(response, out)


def main(argv: list[str]) -> int:
    TARGET.parent.mkdir(exist_ok=True)
    if len(argv) > 1:
        source = Path(argv[1]).expanduser()
        if not source.is_file():
            print(f"Can't find {source}. Check the path and try again.")
            return 1
        if source.resolve() != TARGET.resolve():
            shutil.copyfile(source, TARGET)
        origin = f"browser download ({source.name})"
    else:
        print(f"Downloading {SOURCE_URL}\n(the file is generated live, so this can take a minute)...")
        try:
            download(SOURCE_URL, TARGET)
        except OSError as error:  # no internet, blocked request, HTTP error, timeout
            print(f"\nThe download didn't work: {error}")
            print(f"Download the CSV in your browser from {DATASET_PAGE}, then run:")
            print("    python scripts/download_data.py path/to/the/file.csv")
            return 1
        origin = SOURCE_URL

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
