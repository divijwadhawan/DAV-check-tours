# Setup

Install Python and the dependencies from `requirements.txt`. URLs and the target message are configured in `check_pages.py`.

## Telegram

Create your own Telegram bot and obtain its token and destination chat ID. Store `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` as repository Actions secrets, or environment variables locally. Do not commit their values.

## Schedule

`.github/workflows/check.yml` declares `*/5 * * * *` and a manual `workflow_dispatch` trigger. Scheduled execution is requested, not an exact-time guarantee. The hash-file commit step is retained from earlier work; the script does not modify that file.
