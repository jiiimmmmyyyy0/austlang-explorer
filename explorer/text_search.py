"""Spelling-tolerant search over language names and their alternative names."""
from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from typing import Iterable, Mapping

from .models import Language

MAX_QUERY_LENGTH = 60  # longer input is rejected (keeps every search fast)

# Match types, best first. Results are ranked by type, then by similarity.
EXACT = "Exact"
STARTS_WITH = "Starts with"
CONTAINS = "Contains"
SIMILAR = "Similar spelling"
_TYPE_RANK = {EXACT: 0, STARTS_WITH: 1, CONTAINS: 2, SIMILAR: 3}


def normalise(text: str) -> str:
    """Make text easy to compare: remove accents, case, spaces and punctuation.

    For example 'Café-Noir 2' becomes 'cafenoir2'.
    """
    decomposed = unicodedata.normalize("NFKD", text)
    without_accents = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return "".join(ch for ch in without_accents.casefold() if ch.isalnum())


def levenshtein(a: str, b: str) -> int:
    """Edit distance: the fewest one-letter insertions, deletions or substitutions
    that turn `a` into `b`.

    Dynamic programming: row j of the table holds the distance from the first i
    letters of `a` to the first j letters of `b`. Only two rows are kept in
    memory at a time.
    """
    if a == b:
        return 0
    if len(a) < len(b):
        a, b = b, a  # make `b` the shorter string so the rows stay short
    if not b:
        return len(a)

    previous = list(range(len(b) + 1))
    for i, char_a in enumerate(a, start=1):
        current = [i]
        for j, char_b in enumerate(b, start=1):
            cost = 0 if char_a == char_b else 1
            current.append(min(
                previous[j] + 1,         # delete char_a
                current[j - 1] + 1,      # insert char_b
                previous[j - 1] + cost,  # substitute (free when the letters match)
            ))
        previous = current
    return previous[-1]


def similarity(a: str, b: str) -> float:
    """1.0 for identical strings, down to 0.0 for completely different ones."""
    longest = max(len(a), len(b))
    if longest == 0:
        return 1.0
    return 1 - levenshtein(a, b) / longest


@dataclass(frozen=True)
class IndexEntry:
    """One spelling of one language, already normalised for comparison."""

    code: str
    spelling: str        # the name exactly as written in the data
    normalised: str
    is_main_name: bool


@dataclass(frozen=True)
class SearchResult:
    """A language that matched, and the spelling that matched best."""

    language: Language
    matched_spelling: str
    matched_main_name: bool
    match_type: str
    similarity: float


def build_search_index(languages: Iterable[Language]) -> list[IndexEntry]:
    """List every spelling (main name and alternatives) once, normalised in advance,
    so a search doesn't have to normalise thousands of names every time."""
    index = []
    for language in languages:
        spellings = [(language.name, True)]
        spellings += [(alternative, False) for alternative in language.alternative_names]
        for spelling, is_main in spellings:
            normalised = normalise(spelling)
            if normalised:
                index.append(IndexEntry(language.code, spelling, normalised, is_main))
    return index


def validate_query(query: object) -> str:
    """Return the normalised query, or raise ValueError explaining what is wrong."""
    if not isinstance(query, str):
        raise ValueError("The search must be text.")
    if len(query) > MAX_QUERY_LENGTH:
        raise ValueError(f"Search text can be at most {MAX_QUERY_LENGTH} characters long.")
    normalised = normalise(query)
    if not normalised:
        raise ValueError("Type at least one letter or number to search.")
    return normalised


def classify_match(query: str, candidate: str, min_similarity: float) -> tuple[str, float] | None:
    """How well one normalised spelling matches the normalised query.

    Returns (match type, score) or None when it does not match. For the
    'starts with' and 'contains' types, the score is the share of the spelling
    covered by the query, so shorter, closer spellings rank higher.
    """
    if candidate == query:
        return EXACT, 1.0
    if candidate.startswith(query):
        return STARTS_WITH, len(query) / len(candidate)
    if query in candidate:
        return CONTAINS, len(query) / len(candidate)
    # Shortcut before the slower edit distance: the distance is at least the
    # difference in length, so if that alone is too big, skip this spelling.
    longest = max(len(query), len(candidate))
    if abs(len(query) - len(candidate)) > (1 - min_similarity) * longest:
        return None
    score = similarity(query, candidate)
    if score >= min_similarity:
        return SIMILAR, score
    return None


def search_languages(
    query: str,
    index: Iterable[IndexEntry],
    languages_by_code: Mapping[str, Language],
    min_similarity: float = 0.7,
    max_results: int = 25,
    state: str | None = None,
) -> list[SearchResult]:
    """Find languages whose name or alternative names match the query.

    1. Normalise the query (and reject empty or overly long input).
    2. Compare it with every spelling in the index: exact, starts with,
       contains, or similar spelling (edit distance).
    3. Keep each language's best-matching spelling.
    4. Optionally keep only languages in one state or territory.
    5. Rank by match type, then score, then name, and return the top results.
    """
    if isinstance(min_similarity, bool) or not isinstance(min_similarity, (int, float)) \
            or not 0 < min_similarity <= 1:
        raise ValueError("min_similarity must be greater than 0 and at most 1.")
    if isinstance(max_results, bool) or not isinstance(max_results, int) or max_results < 1:
        raise ValueError("max_results must be a whole number of at least 1.")
    query_normalised = validate_query(query)

    best: dict[str, tuple[tuple, SearchResult]] = {}
    for entry in index:
        match = classify_match(query_normalised, entry.normalised, min_similarity)
        if match is None:
            continue
        language = languages_by_code.get(entry.code)
        if language is None:
            continue
        if state is not None and state not in language.regions:
            continue
        match_type, score = match
        # Lower tuples are better: best type, highest score, main name before alternatives.
        rank = (_TYPE_RANK[match_type], -score, not entry.is_main_name)
        if entry.code not in best or rank < best[entry.code][0]:
            result = SearchResult(language, entry.spelling, entry.is_main_name, match_type, score)
            best[entry.code] = (rank, result)

    ranked = sorted(
        best.values(),
        key=lambda item: (item[0][0], item[0][1], item[1].language.name.casefold()),
    )
    return [result for _, result in ranked[:max_results]]
