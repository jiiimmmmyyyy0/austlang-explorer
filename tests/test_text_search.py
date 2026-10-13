"""Tests for the spelling-tolerant search (explorer/text_search.py)."""
import pytest

from explorer.text_search import (
    CONTAINS,
    EXACT,
    MAX_QUERY_LENGTH,
    SIMILAR,
    STARTS_WITH,
    classify_match,
    levenshtein,
    normalise,
    search_languages,
    similarity,
)


# ---- The algorithm's building blocks ----------------------------------------------

@pytest.mark.parametrize("a, b, expected", [
    ("kitten", "sitting", 3),
    ("flaw", "lawn", 2),
    ("", "abc", 3),
    ("abc", "", 3),
    ("same", "same", 0),
    ("a", "b", 1),
])
def test_levenshtein_known_values(a, b, expected):
    assert levenshtein(a, b) == expected


def test_levenshtein_is_symmetric():
    assert levenshtein("alphaword", "alfawurd") == levenshtein("alfawurd", "alphaword")


def test_similarity_range():
    assert similarity("abc", "abc") == 1.0
    assert similarity("", "") == 1.0
    assert similarity("abc", "xyz") == 0.0
    assert similarity("alphawrd", "alphaword") == pytest.approx(1 - 1 / 9)


@pytest.mark.parametrize("text, expected", [
    ("Caf\u00e9-Noir 2", "cafenoir2"),
    ("  A b C ", "abc"),
    ("\u00d1and\u00fa", "nandu"),
    ("!!!", ""),
])
def test_normalise(text, expected):
    assert normalise(text) == expected


def test_classify_match_types():
    assert classify_match("alpha", "alpha", 0.7) == (EXACT, 1.0)
    assert classify_match("alp", "alpha", 0.7)[0] == STARTS_WITH
    assert classify_match("pha", "alpha", 0.7)[0] == CONTAINS
    assert classify_match("alpho", "alpha", 0.7)[0] == SIMILAR
    assert classify_match("zzzzz", "alpha", 0.7) is None


# ---- Searching the sample data -------------------------------------------------------

def test_exact_main_name_ranks_first(index, by_code):
    results = search_languages("Alphaword", index, by_code)
    assert results[0].language.code == "TEST01"
    assert results[0].match_type == EXACT
    assert results[0].matched_main_name is True


def test_alternative_spelling_is_found_and_reported(index, by_code):
    results = search_languages("alfaword", index, by_code)
    assert results[0].language.code == "TEST01"
    assert results[0].matched_spelling == "Alfaword"
    assert results[0].matched_main_name is False


def test_a_typo_is_tolerated(index, by_code):
    results = search_languages("Alphawrd", index, by_code)
    assert results[0].language.code == "TEST01"
    assert results[0].match_type == SIMILAR


def test_part_of_a_name_matches_by_prefix(index, by_code):
    results = search_languages("gamma", index, by_code)
    assert [result.language.code for result in results] == ["TEST03"]
    assert results[0].match_type == STARTS_WITH


def test_contains_matches_rank_closer_names_first(index, by_code):
    results = search_languages("speech", index, by_code)
    assert [result.language.name for result in results] == ["Muspeech", "Betaspeech", "Thetaspeech"]


def test_state_filter(index, by_code):
    results = search_languages("speech", index, by_code, state="WA")
    assert {result.language.code for result in results} == {"TEST02", "TEST15"}


def test_no_match_returns_an_empty_list(index, by_code):
    assert search_languages("qqqqqq", index, by_code) == []


def test_max_results_limits_the_output(index, by_code):
    assert len(search_languages("speech", index, by_code, max_results=1)) == 1


def test_stricter_tolerance_finds_fewer_similar_spellings(index, by_code):
    relaxed = search_languages("Etawrod", index, by_code, min_similarity=0.55)
    strict = search_languages("Etawrod", index, by_code, min_similarity=0.95)
    assert [result.language.code for result in relaxed] == ["TEST07"]
    assert strict == []


# ---- Invalid input -------------------------------------------------------------------

@pytest.mark.parametrize("bad_query", ["", "   ", "!!!", "x" * (MAX_QUERY_LENGTH + 1), None, 42])
def test_invalid_queries_raise_value_error(index, by_code, bad_query):
    with pytest.raises(ValueError):
        search_languages(bad_query, index, by_code)


@pytest.mark.parametrize("settings", [
    {"max_results": 0},
    {"max_results": 2.5},
    {"min_similarity": 0},
    {"min_similarity": 1.5},
])
def test_invalid_settings_raise_value_error(index, by_code, settings):
    with pytest.raises(ValueError):
        search_languages("alpha", index, by_code, **settings)
