"""Load the AUSTLANG CSV file and clean it into Language objects.

Two layouts are read. The CSV exported from AustLang Online (version 3,
launched June 2026) has `austlang_code`, `primary_name`, `lat` and `lon`, puts
alternative spellings inside the primary name ("Name A / Name B") and has
separate ABS, Ethnologue and Tindale name columns. Older AUSTLANG files had a
`language_synonym` column instead. Column names are matched, not positions, so
the order of the columns does not matter.

Only the Python standard library is used, so every cleaning step is visible here.
"""
from __future__ import annotations

import csv
import io
import math
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse

from .geo import estimate_state, is_in_australia
from .models import STATE_NAMES, CleaningReport, Language

# Each field the app needs, and the column names it may appear under (lower case).
COLUMN_ALIASES = {
    "code": ("language_code", "code", "austlang_code"),
    "name": ("language_name", "primary_name", "name"),
    "alternative_names": ("language_synonym", "language_synonyms", "synonyms", "synonym"),
    "latitude": ("approximate_latitude_of_language_variety", "latitude", "lat"),
    "longitude": ("approximate_longitude_of_language_variety", "longitude", "lon", "lng"),
    "states": ("state_territory", "states", "state"),
    "uri": ("uri", "url", "language_uri"),
    "abs_name": ("abs_name",),
    "ethnologue_name": ("ethnologue_name",),
    "tindale_name": ("tindale_name",),
}
REQUIRED_FIELDS = ("code", "name")

# Other recorded names for each variety in AustLang v3 files: the names used by
# the Australian Bureau of Statistics, Ethnologue and Norman Tindale's catalogue.
# They become alternative names, so a search by any of them finds the variety.
OTHER_NAME_FIELDS = ("abs_name", "ethnologue_name", "tindale_name")

# Encodings to try, in order. AUSTLANG publishes UTF-8 with a byte-order mark;
# the others cover a file re-saved by a spreadsheet program.
ENCODINGS = ("utf-8-sig", "cp1252", "latin-1")

# Full state names and abbreviations, mapped to one standard abbreviation.
_STATE_LOOKUP = {name.casefold(): abbr for abbr, name in STATE_NAMES.items()}
_STATE_LOOKUP.update({abbr.casefold(): abbr for abbr in STATE_NAMES})

# Characters that make a spreadsheet treat a cell as a formula.
_FORMULA_STARTS = ("=", "+", "-", "@", "\t", "\r")


def clean_text(value: object) -> str:
    """Trim a value and squash runs of spaces. None becomes an empty string."""
    if value is None:
        return ""
    return " ".join(str(value).split())


def split_multi_value(value: object) -> list[str]:
    """Split a cell that holds several values into a list.

    AUSTLANG's documentation mentions both comma- and pipe-separated lists, so
    each cell is checked: if it contains a pipe we split on pipes (so commas
    inside a name survive), otherwise on semicolons, otherwise on commas.
    """
    text = clean_text(value)
    if not text:
        return []
    parts = [text]
    for delimiter in ("|", ";", ","):
        if delimiter in text:
            parts = text.split(delimiter)
            break
    cleaned = (clean_text(part) for part in parts)
    return [part for part in cleaned if part]


def split_name_variants(value: object) -> list[str]:
    """Split 'Name A / Name B' into ['Name A', 'Name B'].

    AustLang v3 lists a variety's spellings inside one name, separated by
    slashes. Only slashes split here: names such as 'Language Group, nfd'
    contain commas that belong to the name.
    """
    cleaned = (clean_text(part) for part in clean_text(value).split("/"))
    return [part for part in cleaned if part]


def parse_alternative_names(
    value: object, main_name: str, extra_names: Iterable[str] = ()
) -> tuple[str, ...]:
    """Alternative names without blanks, repeats or copies of the main name.

    `value` is a synonym cell (comma-, semicolon- or pipe-separated) and
    `extra_names` are names that are already split, such as the spellings inside
    a v3 primary name and its ABS, Ethnologue and Tindale names.
    """
    seen = {main_name.casefold()}
    names = []
    for name in [*split_multi_value(value), *extra_names]:
        name = clean_text(name)
        if name and name.casefold() not in seen:
            seen.add(name.casefold())
            names.append(name)
    return tuple(names)


def parse_states(value: object) -> tuple[str, ...]:
    """Turn 'Western Australia, NT' into ('WA', 'NT'). Unknown values are kept as written."""
    states = []
    for part in split_multi_value(value):
        abbreviation = _STATE_LOOKUP.get(part.casefold(), part)
        if abbreviation not in states:
            states.append(abbreviation)
    return tuple(states)


def parse_coordinate(value: object) -> float | None:
    """Read one coordinate. Returns None if it is blank or not a real number."""
    text = clean_text(value).replace("\u2212", "-")  # some files use the Unicode minus sign
    if not text:
        return None
    try:
        number = float(text)
    except ValueError:
        return None
    return number if math.isfinite(number) else None


def safe_link(value: object) -> str | None:
    """Keep a link only if it is an ordinary http or https web address."""
    text = clean_text(value)
    parsed = urlparse(text)
    if parsed.scheme in ("http", "https") and parsed.netloc:
        return text
    return None


def map_columns(header: list[str]) -> tuple[dict[str, str], list[str]]:
    """Match the file's column names to the fields the app needs.

    Returns the mapping (field -> column name in the file) and the columns the
    app does not use. Raises ValueError if a required column is missing.
    """
    by_simple_name: dict[str, str] = {}
    for column in header:
        simple = clean_text(column).casefold().replace(" ", "_")
        by_simple_name.setdefault(simple, column)

    mapping: dict[str, str] = {}
    for field_name, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            if alias in by_simple_name:
                mapping[field_name] = by_simple_name[alias]
                break

    missing = [COLUMN_ALIASES[name][0] for name in REQUIRED_FIELDS if name not in mapping]
    if missing:
        found = ", ".join(clean_text(column) for column in header) or "none"
        raise ValueError(
            f"missing required column(s): {', '.join(missing)}. Columns found: {found}."
        )

    used = set(mapping.values())
    ignored = [column for column in header if column not in used]
    return mapping, ignored


def read_csv_rows(path: Path) -> tuple[list[str], list[dict], str]:
    """Read every row of the CSV file. Returns (header, rows, encoding used)."""
    for encoding in ENCODINGS:
        try:
            with path.open(newline="", encoding=encoding) as file:
                reader = csv.DictReader(file)
                rows = list(reader)
                header = list(reader.fieldnames or [])
            return header, rows, encoding
        except UnicodeDecodeError:
            continue  # try the next encoding
        except csv.Error as error:
            raise ValueError(f"the file is not a valid CSV file ({error}).") from error
    raise ValueError("the file's text encoding could not be read.")


def _cell(row: dict, mapping: dict[str, str], field_name: str) -> str:
    """Cleaned text in one row for one field ('' if the file lacks that column)."""
    column = mapping.get(field_name)
    return clean_text(row.get(column)) if column else ""


def _read_location(row: dict, mapping: dict[str, str], report: CleaningReport):
    """Read and check one row's coordinates, updating the report's counters."""
    lat_text = _cell(row, mapping, "latitude")
    lon_text = _cell(row, mapping, "longitude")
    if not lat_text and not lon_text:
        report.no_coordinates += 1
        return None, None
    latitude, longitude = parse_coordinate(lat_text), parse_coordinate(lon_text)
    if latitude is None or longitude is None or not is_in_australia(latitude, longitude):
        report.invalid_coordinates += 1
        return None, None
    return latitude, longitude


def load_languages(path: str | Path) -> tuple[list[Language], CleaningReport]:
    """Read and clean an AUSTLANG CSV file.

    For each row:
      1. Trim spaces from every value.
      2. Skip rows with no code or no name.
      3. Skip repeated codes (the first copy is kept).
      4. Read the coordinates. Blanks, non-numbers and points outside
         Australia become "no location"; the variety is still kept.
      5. Collect the alternative names (from the synonym column in older files;
         in v3 files, the spellings inside the primary name plus the ABS,
         Ethnologue and Tindale names) and split the states into a list.
      6. Estimate the state from the coordinates.
      7. Keep the AUSTLANG link only if it is a normal web address.
    """
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Data file not found: {path}")

    header, rows, encoding = read_csv_rows(path)
    mapping, ignored = map_columns(header)
    report = CleaningReport(
        source=path.name,
        encoding=encoding,
        rows_read=len(rows),
        has_state_column="states" in mapping,
        columns_used=dict(mapping),
        columns_ignored=ignored,
    )

    languages: list[Language] = []
    seen_codes: set[str] = set()
    for row in rows:
        code = _cell(row, mapping, "code")
        name = _cell(row, mapping, "name")
        if not code or not name:
            report.missing_code_or_name += 1
            continue
        if code.casefold() in seen_codes:
            report.duplicate_codes += 1
            continue
        seen_codes.add(code.casefold())

        latitude, longitude = _read_location(row, mapping, report)
        extra_names = split_name_variants(name)
        if len(extra_names) == 1:
            extra_names = []  # a single spelling is just the main name
        for field_name in OTHER_NAME_FIELDS:
            extra_names.extend(split_name_variants(_cell(row, mapping, field_name)))
        alternative_names = parse_alternative_names(
            _cell(row, mapping, "alternative_names"), name, extra_names
        )
        report.alternative_names_found += len(alternative_names)

        raw_link = _cell(row, mapping, "uri")
        link = safe_link(raw_link)
        if raw_link and link is None:
            report.unsafe_links_removed += 1

        languages.append(
            Language(
                code=code,
                name=name,
                alternative_names=alternative_names,
                latitude=latitude,
                longitude=longitude,
                states=parse_states(_cell(row, mapping, "states")),
                estimated_state=estimate_state(latitude, longitude),
                uri=link,
            )
        )

    languages.sort(key=lambda language: (language.name.casefold(), language.code))
    report.rows_kept = len(languages)
    return languages, report


def csv_safe(text: str) -> str:
    """Stop spreadsheet programs from running a cell as a formula (CSV injection)."""
    return "'" + text if text.startswith(_FORMULA_STARTS) else text


def to_csv_text(languages: Iterable[Language]) -> str:
    """The cleaned data as CSV text, for the download button."""
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow([
        "language_code", "language_name", "alternative_names", "latitude", "longitude",
        "states_or_territories", "state_source", "austlang_uri",
    ])
    for language in languages:
        writer.writerow([
            csv_safe(language.code),
            csv_safe(language.name),
            csv_safe(" | ".join(language.alternative_names)),
            "" if language.latitude is None else language.latitude,
            "" if language.longitude is None else language.longitude,
            csv_safe(", ".join(language.regions)),
            language.region_source,
            csv_safe(language.uri or ""),
        ])
    return buffer.getvalue()
