# Data

## The file

`austlang.csv` is the **AUSTLANG dataset** published by the Australian Institute of
Aboriginal and Torres Strait Islander Studies (AIATSIS).

| Item | Details |
| --- | --- |
| Download page | https://aiatsis.gov.au/austlang/dataResources (AustLang Online, version 3) |
| Dataset listing | https://data.gov.au/data/dataset/austlang-dataset-001 |
| Publisher | AIATSIS (data@aiatsis.gov.au) |
| Licence | Creative Commons Attribution 4.0 International (CC BY 4.0) |
| Format | CSV (comma separated) |
| Downloaded on | _fill in, or see `austlang_source.json` (written by the download script)_ |

AUSTLANG is a live dataset that AIATSIS updates regularly, so record the date you downloaded it.
AIATSIS launched AustLang Online (version 3) in June 2026, and the old direct CSV link
(`collection.aiatsis.gov.au/datasets/austlang/001.csv`) no longer works.

## Columns the app uses

| Column in the file | Used for |
| --- | --- |
| `austlang_code` | Unique code for each variety (required) |
| `primary_name` | Main name (required). Spellings are separated by slashes, as in "Name A / Name B", and each one becomes searchable |
| `lat`, `lon` | Approximate location |
| `state_territory` | State(s) or territory |
| `abs_name`, `ethnologue_name`, `tindale_name` | Other recorded names (Australian Bureau of Statistics, Ethnologue, Tindale), used as alternative names |

Any other columns (`overview`, `thes_lang_head`, `thes_peop_head`, `status`,
`iso_639_3_code`, `location_info`) are ignored. The app also reads the older AUSTLANG
layout (`language_code`, `language_name`, `language_synonym`,
`approximate_latitude_of_language_variety`, `approximate_longitude_of_language_variety`,
`uri`), which is what the synthetic test file uses.

## Attribution (required by the licence)

> AUSTLANG dataset, Australian Institute of Aboriginal and Torres Strait Islander
> Studies (AIATSIS), licensed under CC BY 4.0. Cleaned and reformatted for this app.

## Getting or updating the file

1. Open https://aiatsis.gov.au/austlang/dataResources in a browser.
2. Leave every field ticked and click **Download as a CSV**.
3. From the project folder, run the script on the downloaded file:

```bash
python scripts/download_data.py path/to/the/file.csv
```

The script copies the file here as `austlang.csv`, checks it and prints the count from
every cleaning step.
