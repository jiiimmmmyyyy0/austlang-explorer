"""Shared pytest fixtures. All test data is synthetic (see tests/fixtures/README.md)."""
from pathlib import Path

import pytest

from explorer.data_loader import load_languages
from explorer.text_search import build_search_index

SAMPLE_CSV = Path(__file__).parent / "fixtures" / "sample_austlang.csv"


@pytest.fixture
def loaded():
    """(languages, report) from the synthetic sample file."""
    return load_languages(SAMPLE_CSV)


@pytest.fixture
def languages(loaded):
    return loaded[0]


@pytest.fixture
def report(loaded):
    return loaded[1]


@pytest.fixture
def by_code(languages):
    return {language.code: language for language in languages}


@pytest.fixture
def index(languages):
    return build_search_index(languages)
