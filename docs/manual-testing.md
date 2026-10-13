# Manual workflow testing

The automated tests (`pytest`) cover the core logic. These checks cover the main
user workflows in the running app. Run them locally and again on the deployed app,
fill in the Result column, and fix anything that fails.

| # | Workflow | Steps | Expected | Result (local) | Result (deployed) |
| --- | --- | --- | --- | --- | --- |
| 1 | App opens | Open the app | Home shows the map and figures; no error |PASS |PASS |
| 2 | Navigation | Click each menu item | All five screens open |PASS |PASS |
| 3 | Exact search | Find a language → type a name you can see on the map | It is the first result, match "Exact" |PASS |PASS |
| 4 | Alternative spelling | Search an alternative name shown in a record's details | The right variety appears, marked "(alternative name)" |PASS |PASS |
| 5 | Typo | Search a name with one letter wrong | Found as "Similar spelling" |PASS|PASS |
| 6 | Empty / junk search | Search `!!!` | Warning: type at least one letter or number |PASS |PASS |
| 7 | No match | Search `qqqqqq` | Message suggesting fewer letters or Relaxed |PASS |PASS |
| 8 | State filter | Search a common letter pair with Western Australia selected | Only WA varieties listed |PASS|PASS |
| 9 | Details | Pick a result in "Choose a result" | Details, link button, nearby table and map |PASS (no link button: the v3 file has no links) |PASS |
| 10 | Nearby, default | Languages near a place, default coordinates | Table and map around Perth |PASS|PASS |
| 11 | Nearby, invalid | Type `hello` in coordinates | Red error explaining the format |PASS|PASS |
| 12 | Nearby, outside Australia | Type `51.5, -0.12` | Warning plus "choose a larger distance" |PASS|PASS |
| 13 | Insights | Open Insights; change grid square size | Map, charts and tables update |PASS| |
| 14 | About the data | Open About the data; click Download | Cleaning numbers shown; CSV downloads |PASS|PASS |
| 15 | Phone layout | Open the deployed app on a phone | Readable; menu opens from the top-left |PASS|PASS|
