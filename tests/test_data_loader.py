"""Tests for loading and cleaning the data file (explorer/data_loader.py)."""
import pytest

from explorer.data_loader import (
    csv_safe,
    load_languages,
    map_columns,
    parse_alternative_names,
    parse_coordinate,
    parse_states,
    safe_link,
    split_multi_value,
    to_csv_text,
)
from explorer.models import MIN_RECORDS


# ---- The whole cleaning pipeline on the sample file -------------------------

def test_report_counts_every_cleaning_step(report):
    assert report.rows_read == 15
    assert report.rows_kept == 12
    assert report.rows_removed == 3
    assert report.missing_code_or_name == 2
    assert report.duplicate_codes == 1
    assert report.no_coordinates == 1
    assert report.invalid_coordinates == 2
    assert report.alternative_names_found == 11
    assert report.unsafe_links_removed == 1


def test_columns_are_matched_and_unused_ones_listed(report):
    assert report.columns_used["code"] == "language_code"
    assert report.columns_used["latitude"] == "approximate_latitude_of_language_variety"
    assert report.has_state_column is True
    assert report.columns_ignored == ["thesaurus_heading_language"]


def test_duplicate_code_keeps_the_first_copy(by_code, languages):
    assert by_code["TEST01"].name == "Alphaword"
    assert "Alphaword copy" not in [language.name for language in languages]


def test_extra_spaces_are_trimmed(by_code):
    assert by_code["TEST15"].name == "Muspeech"


def test_bad_coordinates_become_no_location(by_code):
    assert not by_code["TEST09"].has_location   # blank
    assert not by_code["TEST10"].has_location   # 0, 0 is outside Australia
    assert not by_code["TEST14"].has_location   # 'abc' is not a number
    assert by_code["TEST01"].latitude == -31.95
    assert by_code["TEST01"].longitude == 115.86


def test_alternative_names_skip_copies_of_the_main_name(by_code):
    assert by_code["TEST01"].alternative_names == ("Alfaword", "Alphawurd", "Alpha Word")
    assert by_code["TEST04"].alternative_names == ("Deltavoyce", "Delta-Voice")


def test_states_are_standardised_and_fall_back_to_the_estimate(by_code):
    assert by_code["TEST05"].states == ("QLD", "NSW")
    assert by_code["TEST06"].states == ("NSW",)        # 'New South Wales' became NSW
    assert by_code["TEST15"].states == ()              # blank in the file...
    assert by_code["TEST15"].regions == ("WA",)        # ...so the estimate is used
    assert by_code["TEST15"].region_source == "estimated"
    assert by_code["TEST10"].regions == ()             # no state and no location


def test_unsafe_link_is_removed(by_code):
    assert by_code["TEST05"].uri is None               # was javascript:...
    assert by_code["TEST01"].uri == "https://example.org/TEST01"


def test_languages_are_sorted_by_name(languages):
    names = [language.name.casefold() for language in languages]
    assert names == sorted(names)


# ---- Problem files -----------------------------------------------------------

def test_missing_file_raises_file_not_found(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_languages(tmp_path / "does_not_exist.csv")


def test_missing_required_column_gives_a_clear_error(tmp_path):
    path = tmp_path / "bad.csv"
    path.write_text("language_code,latitude\nTEST1,-30\n", encoding="utf-8")
    with pytest.raises(ValueError, match="language_name"):
        load_languages(path)


def test_empty_file_is_rejected(tmp_path):
    path = tmp_path / "empty.csv"
    path.write_text("", encoding="utf-8")
    with pytest.raises(ValueError, match="missing required column"):
        load_languages(path)


def test_pipe_separated_file_without_a_state_column(tmp_path):
    path = tmp_path / "pipes.csv"
    path.write_text(
        "language_code,language_name,language_synonym,"
        "approximate_latitude_of_language_variety,approximate_longitude_of_language_variety,uri\n"
        'TEST1,Omegaword,"Omega word|Omegawurd, northern",-31.95,115.86,https://example.org/1\n',
        encoding="utf-8-sig",
    )
    languages, report = load_languages(path)
    assert report.has_state_column is False
    assert languages[0].alternative_names == ("Omega word", "Omegawurd, northern")
    assert languages[0].regions == ("WA",)


def test_file_saved_by_a_spreadsheet_program_is_still_read(tmp_path):
    path = tmp_path / "cp1252.csv"
    path.write_bytes("language_code,language_name\nTEST1,Caf\u00e9word\n".encode("cp1252"))
    languages, report = load_languages(path)
    assert languages[0].name == "Caf\u00e9word"
    assert report.encoding == "cp1252"


@pytest.mark.parametrize("rows, expected", [(MIN_RECORDS - 1, False), (MIN_RECORDS, True)])
def test_minimum_record_check_boundary(tmp_path, rows, expected):
    path = tmp_path / "many.csv"
    lines = ["language_code,language_name"] + [f"TEST{i},Name{i}" for i in range(rows)]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    _, report = load_languages(path)
    assert report.rows_kept == rows
    assert report.meets_minimum is expected


# ---- Helper functions ------------------------------------------------------------

@pytest.mark.parametrize("text, expected", [
    ("a, b,  c", ["a", "b", "c"]),
    ("a|b, c", ["a", "b, c"]),       # a pipe wins, so the comma stays inside the name
    ("a; b", ["a", "b"]),
    ("single", ["single"]),
    ("", []),
    (None, []),
    (" , ,", []),
])
def test_split_multi_value(text, expected):
    assert split_multi_value(text) == expected


def test_parse_alternative_names_removes_blanks_repeats_and_main_name():
    assert parse_alternative_names("Bee, bee, , Main, Cee", "main") == ("Bee", "Cee")


def test_parse_states_handles_full_names_case_and_repeats():
    assert parse_states("western australia, NT, nt, Somewhere") == ("WA", "NT", "Somewhere")


@pytest.mark.parametrize("text, expected", [
    (" -31.5 ", -31.5),
    ("\u221231.5", -31.5),   # Unicode minus sign
    ("", None),
    ("abc", None),
    ("inf", None),
    ("nan", None),
])
def test_parse_coordinate(text, expected):
    assert parse_coordinate(text) == expected


@pytest.mark.parametrize("link, expected", [
    ("https://example.org/a", "https://example.org/a"),
    ("http://example.org", "http://example.org"),
    ("javascript:alert(1)", None),
    ("ftp://example.org/file", None),
    ("not a link", None),
    ("", None),
])
def test_safe_link(link, expected):
    assert safe_link(link) == expected


def test_map_columns_ignores_case_and_spaces():
    mapping, ignored = map_columns(["Language Code", "LANGUAGE_NAME", "Extra"])
    assert mapping == {"code": "Language Code", "name": "LANGUAGE_NAME"}
    assert ignored == ["Extra"]


@pytest.mark.parametrize("text, expected", [
    ("=SUM(A1)", "'=SUM(A1)"),
    ("@cmd", "'@cmd"),
    ("Plain", "Plain"),
])
def test_csv_safe_blocks_spreadsheet_formulas(text, expected):
    assert csv_safe(text) == expected


def test_csv_export_has_a_header_and_every_language(languages):
    lines = to_csv_text(languages).strip().splitlines()
    assert lines[0].startswith("language_code,language_name")
    assert len(lines) == len(languages) + 1
