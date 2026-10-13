# AI-LOG

This log records significant use of AI tools in this project, as the unit requires.
**Fill in the blank columns honestly.** Markers look for evidence that you checked,
tested and changed AI output, and the Q&A can ask about any part of the code.

## Summary

- **Tool:** Claude (Anthropic), model Claude Opus 5.5, used through claude.ai.
- **Not used for cultural content:** AI did not write or generate any cultural, language
  or historical content. Every language name, code, alternative name and location in the
  app comes from the AUSTLANG dataset (AIATSIS, CC BY 4.0). The test data uses invented
  names such as "Alphaword" and codes such as "TEST01".

## Log

| Date | Tool | What I asked for | What the AI produced | How I checked it | What I changed or rejected |
   | --- | --- | --- | --- | --- | --- |
| 2026-10-07 | Claude Opus 5.5 | Build the whole project from the brief, with a guidebook explaining it | Project structure; `explorer/` modules (cleaning, search, geography, analysis); Streamlit screens; 148 pytest cases with a synthetic fixture; download script; README, data README, architecture and manual-testing docs; this log's template; a draft technical report; a guidebook | Ran `pytest`; ran the data script on the real AUSTLANG file, which exposed the broken download link and the new file format (see the 13 Oct row); ran the app locally and completed `docs/manual-testing.md` (15 of 15 passed); deployed it to Streamlit Community Cloud and repeated the tests on the live app | Added UWA's Acknowledgement of Country (copied from UWA) to `ui_common.py`; added the download date to `data/README.md`; kept the default search tolerance, since the search tests passed with it; replaced the broken download step and old column names (see the 13 Oct row) |
| 2026-10-13 | Claude Opus 5.5 | Fix loading the data: the script's download link was dead and the file from AustLang Online (version 3, launched June 2026) failed with "missing required column(s): language_name" | `data_loader.py` reads the v3 columns (`primary_name`, `lat`, `lon`, `abs_name`, `ethnologue_name`, `tindale_name`) and treats the spellings inside a primary name as alternative names; the download script now explains the browser download; About screen and docs updated; 9 new test cases (157 in total) | Applied the patch; ran pytest (157 passed); re-ran the script on the AustLang v3 file: 1,183 varieties kept, 342 without coordinates, 1,115 alternative names | Applied as given; added the download date to data/README.md |
| 2026-10-13 | Claude Opus 5.5 | Update the technical report for the AustLang v3 data and fill in the real figures | Updated sections 1–11 and the References: the v3 data source and format change, the cleaning counts, the Insights figures (computed with the app's own functions from `data/austlang.csv`), 157 tests, the live link and the diagram labels | Compared the figures with the About and Insights screens in the running app |Added our names and student numbers, the three screenshots, the deployed test results and the team contribution statement  |

## Verification checklist

- [x] Ran `pytest` locally. Result: 157 passed
- [x] Downloaded the real AUSTLANG file and ran `scripts/download_data.py`. Rows kept: 1,183
- [x] Ran the app locally and completed `docs/manual-testing.md`.
- [x] Checked the AUSTLANG licence and attribution myself on data.gov.au.
- [x] Read every file with the guidebook and can explain each algorithm without notes.
- [x] Deployed the app and repeated the manual tests on the live version.

## Problems found in AI output and how I fixed them

The download script's link no longer worked, because AIATSIS moved AustLang to version 3 in June 2026, and the new file's column names didn't match the code, so loading failed with "missing required column(s): language_name". I downloaded the file from AustLang Online's data page and had Claude update the loader. I checked the fix with pytest (157 passed) and by re-running the script (1,183 varieties kept).
