# Data

## The file

`austlang.csv` is the **AUSTLANG dataset** published by the Australian Institute of
Aboriginal and Torres Strait Islander Studies (AIATSIS).

| Item | Details |
| --- | --- |
| Dataset page | https://data.gov.au/data/dataset/austlang-dataset-001 |
| Direct CSV link | https://collection.aiatsis.gov.au/datasets/austlang/001.csv |
| Publisher | AIATSIS (data@aiatsis.gov.au) |
| Licence | Creative Commons Attribution 4.0 International (CC BY 4.0) |
| Format | CSV, comma separated, quoted, UTF-8 with a byte-order mark |
| Downloaded on | _fill in, or see `austlang_source.json` (written by the download script)_ |

AUSTLANG is a live dataset that AIATSIS updates regularly, so record the date you downloaded it.

## Columns the app uses

| Column in the file | Used for |
| --- | --- |
| `language_code` | Unique code for each variety (required) |
| `language_name` | Main name (required) |
| `language_synonym` | Alternative names and spellings (comma- or pipe-separated) |
| `approximate_latitude_of_language_variety` | Approximate location |
| `approximate_longitude_of_language_variety` | Approximate location |
| `state_territory` | State(s) or territory (only in some versions of the file) |
| `uri` | Link to the record on the AUSTLANG website |

Any other columns (such as `thesaurus_heading_language`) are ignored.

## Attribution (required by the licence)

> AUSTLANG dataset, Australian Institute of Aboriginal and Torres Strait Islander
> Studies (AIATSIS), licensed under CC BY 4.0. Cleaned and reformatted for this app.

## Getting or updating the file

```bash
python scripts/download_data.py                  # downloads from AIATSIS
python scripts/download_data.py ~/Downloads/x.csv  # or use a file you downloaded in a browser
```
