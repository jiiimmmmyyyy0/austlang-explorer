# Manual workflow testing

The automated tests (`pytest`) cover the core logic. These checks cover the main
user workflows in the running app. Run them locally and again on the deployed app,
fill in the Result column, and fix anything that fails.

| # | Workflow | Steps | Expected | Result (local) | Result (deployed) |
| --- | --- | --- | --- | --- | --- |
| 1 | App opens | Open the app | Home shows the map and figures; no error | | |
| 2 | Navigation | Click each menu item | All five screens open | | |
| 3 | Exact search | Find a language → type a name you can see on the map | It is the first result, match "Exact" | | |
| 4 | Alternative spelling | Search an alternative name shown in a record's details | The right variety appears, marked "(alternative name)" | | |
| 5 | Typo | Search a name with one letter wrong | Found as "Similar spelling" | | |
| 6 | Empty / junk search | Search `!!!` | Warning: type at least one letter or number | | |
| 7 | No match | Search `qqqqqq` | Message suggesting fewer letters or Relaxed | | |
| 8 | State filter | Search a common letter pair with Western Australia selected | Only WA varieties listed | | |
| 9 | Details | Pick a result in "Choose a result" | Details, link button, nearby table and map | | |
| 10 | Nearby, default | Languages near a place, default coordinates | Table and map around Perth | | |
| 11 | Nearby, invalid | Type `hello` in coordinates | Red error explaining the format | | |
| 12 | Nearby, outside Australia | Type `51.5, -0.12` | Warning plus "choose a larger distance" | | |
| 13 | Insights | Open Insights; change grid square size | Map, charts and tables update | | |
| 14 | About the data | Open About the data; click Download | Cleaning numbers shown; CSV downloads | | |
| 15 | Phone layout | Open the deployed app on a phone | Readable; menu opens from the top-left | | |
