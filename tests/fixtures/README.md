# Test fixtures

`sample_austlang.csv` is **synthetic test data**, not real AUSTLANG records.
The language names (Alphaword, Betaspeech, …) and codes (TEST01, …) are invented
so the tests can check the cleaning and search code without using cultural
material. The file deliberately includes problems the cleaner must handle:
a duplicate code, a missing code, a missing name, blank and impossible
coordinates, a coordinate that is not a number, an unsafe link, extra spaces,
full state names, and an alternative name that repeats the main name.

It uses the same column names and UTF-8 byte-order mark as the real AUSTLANG file.
