# Local DAV Alpinprogramm monitor

Checks https://www.alpenverein-muenchen-oberland.de/alpinprogramm every 120 seconds while running on your laptop. No Telegram, login or hosted service required.

## macOS: start

Download/clone this branch, then in Terminal inside the project:

```bash
bash start.command
```

Requires Python 3 (`python3 --version`). The launcher creates a virtual environment, installs dependencies and uses macOS `caffeinate` to prevent idle sleep while running. Keep the laptop lid open and internet connected. The launcher opens a dashboard at http://127.0.0.1:8765 with search, course and date filters, DAV links, and CSV download. It refreshes the local list every 15 seconds. The dashboard starts immediately while the first scan runs. Stop with Ctrl+C. Run again after restarting your laptop; this does not install an automatic login service.

Alternatively:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python check_pages.py
```

One check: `.venv/bin/python check_pages.py --once`
Force course-list refresh: `.venv/bin/python check_pages.py --once --refresh`

## Results

- `output/courses.csv`: all currently published dated events, including tours and indoor events, with course name, dates, location, code, website status classes and booking link. Open in Excel. Dates preserve DAV's formatting, including multi-session dates.
- `output/courses.json`: same data in JSON.
- `output/new_courses.csv`: newly discovered dates from the most recent change that added dates.
- `output/state.json`: local baseline, preserved across restarts.

The initial scan traverses the programme's category pages and can take several minutes. Historical events under “Vergangene Veranstaltungen” are excluded. Published does not mean bookable or having free places; the status field preserves the site's text/classes, and the link lets you verify availability.

Subsequent lightweight checks compare the programme announcement and top-level category counts. On change, the monitor refreshes the complete course list and emits a terminal bell and macOS notification only if new event URLs are found. Native notification permissions may need enabling. No repeated alerts for identical data. Fetch/parse errors preserve the last baseline and retry on the next check.

This detects publication through announcement/count changes, not an official launch API. A change replacing events without changing those indicators can be missed; use `--refresh` to force a complete scan. The launch announcement alone is not treated as proof of availability. The DAV page currently announces 7 October 2026 for the 2026/2027 programme.

The old GitHub workflow is changed to manual-only and performs a single check. Routine polling now happens locally. Existing Telegram secrets and the old `page_hashes.json` are not used.

## Dashboard only / manual launch

`.venv/bin/python dashboard.py` starts both the local dashboard and monitor. The server binds only to 127.0.0.1. Date filtering matches the DAV date text; entering 2027 matches 27. Status colours are labelled as indicators rather than assuming bookability.

## Test winter programme

Click **Test winter programme** in the dashboard to scan https://www.alpenverein-muenchen-oberland.de/alpinprogramm/winter and its categories. The dashboard reports the number of extracted dates and offers a separate winter CSV download. Tests can take several minutes and show fetch/parse failures explicitly. A successful test proves the winter crawl and date extraction work with the current site; it does not claim the new season has launched. The test uses the same parser but never changes `state.json`, the main course list or launch detection. It also emits a test notification on macOS.

CLI alternative: `.venv/bin/python check_pages.py --test-winter`. Results: `output/winter_test.csv` and `output/winter_test.json`.
