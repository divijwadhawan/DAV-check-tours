# DAV Course Monitor

A small Python automation that checks selected DAV course pages and sends a Telegram alert when the standard “no events available” text is absent.

**Status:** implemented script with a scheduled GitHub Actions workflow. Absence of the message is a signal to inspect the page, not proof of a bookable course.

## Demo
Use GitHub Actions → Web Monitor → Run workflow after configuring Telegram secrets. See [demo](docs/demo.md).

## Implemented features
- Checks six configured outdoor-course URLs with HTTP timeouts.
- Detects whether a configured German unavailable-course message is present.
- Sends a Telegram message for pages where that message is absent.
- Workflow cron expression requests a run every five minutes; actual scheduling may vary.

## Architecture and stack
GitHub Actions → Python `requests` → DAV pages → text check → Telegram Bot API.

## Quick start
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python check_pages.py
```
Provide `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` as environment variables locally, or repository Actions secrets for scheduled runs. See [setup](docs/setup.md).

## Project scope and attribution
A personal outdoor-course monitoring use case combining HTTP checks, automation and messaging. DAV owns the monitored website; this repository is not an official DAV service.

## Validation and limitations
No live notification was sent during documentation restructuring. The script does not deduplicate alerts: it can notify on every run while the message is absent. Page layout changes can cause false positives. Telegram response status is not currently checked. Failed fetches are not always reflected accurately in the final console message.

`page_hashes.json` exists and the workflow attempts to commit it, but the current script does not read or update it. Hash-based change detection is not implemented.

## Documentation and license
[Setup](docs/setup.md) · [Architecture](docs/architecture.md) · [Demo](docs/demo.md)

No root licence file is currently provided.
