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
| 2026-10-07 | Claude Opus 5.5 | Build the whole project from the brief, with a guidebook explaining it | Project structure; `explorer/` modules (cleaning, search, geography, analysis); Streamlit screens; 148 pytest cases with a synthetic fixture; download script; README, data README, architecture and manual-testing docs; this log's template; a draft technical report; a guidebook | _e.g. ran `pytest` (result?), ran the app with the real AUSTLANG file, completed `docs/manual-testing.md`, read each file alongside the guidebook_ | _e.g. added UWA's Acknowledgement of Country, adjusted the tolerance values after testing with real names, fixed …_ |
| 2026-10-13 | Claude Opus 5.5 | Fix loading the data: the script's download link was dead and the file from AustLang Online (version 3, launched June 2026) failed with "missing required column(s): language_name" | `data_loader.py` reads the v3 columns (`primary_name`, `lat`, `lon`, `abs_name`, `ethnologue_name`, `tindale_name`) and treats the spellings inside a primary name as alternative names; the download script now explains the browser download; About screen and docs updated; 9 new test cases (157 in total) | _e.g. ran `pytest` (result?), re-ran the script on the v3 file (rows kept?), searched a few names in the app_ | _…_ |
| | | | | | |

## Verification checklist

- [ ] Ran `pytest` locally. Result:
- [ ] Downloaded the real AUSTLANG file and ran `scripts/download_data.py`. Rows kept:
- [ ] Ran the app locally and completed `docs/manual-testing.md`.
- [ ] Checked the AUSTLANG licence and attribution myself on data.gov.au.
- [ ] Read every file with the guidebook and can explain each algorithm without notes.
- [ ] Deployed the app and repeated the manual tests on the live version.

## Problems found in AI output and how I fixed them

_Record anything that was wrong, unclear or didn't suit the real data, and what you did about it._
