# Local DAV Alpinprogramm monitor

Checks https://www.alpenverein-muenchen-oberland.de/alpinprogramm every 120 seconds while running on your laptop. No login or hosted service required. Telegram push is optional and can reuse your existing bot.

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

The old GitHub workflow is changed to manual-only and performs a single check. Routine polling now happens locally. GitHub Telegram secrets are not available locally. Use the local Telegram configuration below. The old `page_hashes.json` is not used.

## Dashboard only / manual launch

`.venv/bin/python dashboard.py` starts both the local dashboard and monitor. The server binds only to 127.0.0.1. Date filtering matches the DAV date text; entering 2027 matches 27. Status colours are labelled as indicators rather than assuming bookability.

## Test winter programme

Click **Test winter programme** in the dashboard to scan https://www.alpenverein-muenchen-oberland.de/alpinprogramm/winter and its categories. The dashboard reports the number of extracted dates and offers a separate winter CSV download. Tests can take several minutes and show fetch/parse failures explicitly. A successful test proves the winter crawl and date extraction work with the current site; it does not claim the new season has launched. The test uses the same parser but never changes `state.json`, the main course list or launch detection. It also emits a test notification on macOS.

CLI alternative: `.venv/bin/python check_pages.py --test-winter`. Results: `output/winter_test.csv` and `output/winter_test.json`.

## Structured dates and costs

Exports include `start_date`, `end_date` (ISO dates), `days` (inclusive calendar span), `date_note`, `cost_eur` and `cost_note`. Multi-session and recurring programmes retain the original DAV date text. Days does not claim the number of attended sessions and includes school-holiday exclusions in the overall span. Cost is the first listed price, for DAV München & Oberland members; missing prices stay blank.

Select **Main programme** or **Winter test results** in the dashboard to display the relevant CSV. Old exports receive date parsing in the dashboard; rerun the winter test to retrieve prices. Updating to this schema triggers a fresh main export automatically. CSV edits become visible on refresh; Excel must save back to the CSV rather than a separate XLSX file.

## Automatic Telegram push with your existing bot

1. Copy the example: `cp telegram_config.example.json telegram_config.json`.
2. Open `telegram_config.json` in a text editor and replace the placeholders with your existing bot token and chat ID. Keep the quotes. This file is ignored by git.
3. Send `/start` to your bot in Telegram if you have not already done so.
4. Test: `.venv/bin/python check_pages.py --test-telegram`.
5. Start normally: `bash start.command`.

Environment variables `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` also work and override the file. Existing GitHub secret values cannot be downloaded; use your saved credentials or recover the bot token from BotFather. Never paste the token into GitHub code or screenshots.

Automatic scans queue a Telegram message when a programme refresh discovers new event URLs relative to the saved baseline. Messages include the programme link, new course count, and sample dates/prices. The first baseline and winter tests do not send publication alerts. Failed deliveries remain in a local outbox and retry on subsequent checks, including after restart. Confirmed deliveries are remembered; an ambiguous network timeout can cause a duplicate on retry. The monitor must remain running and online. Announcement/category-count detection limitations still apply; the message reports newly published dates rather than claiming an official launch signal.
