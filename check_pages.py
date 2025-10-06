import requests
import os
from datetime import datetime

# --- CONFIGURATION ---

URLS = [
    "https://www.alpenverein-muenchen-oberland.de/alpinprogramm/sommer/hochtouren/grundkurs-hochtouren",
    "https://www.alpenverein-muenchen-oberland.de/alpinprogramm/winter/wasserfalleisklettern/grundkurs-wasserfalleisklettern",
    "https://www.alpenverein-muenchen-oberland.de/alpinprogramm/winter/skischule/nordic-classic/nordic-classic-fuer-einsteiger",
    "https://www.alpenverein-muenchen-oberland.de/alpinprogramm/sommer/klettern-alpin/grundkurs-klettern-alpin",
    "https://www.alpenverein-muenchen-oberland.de/alpinprogramm/sommer/wildwasserkajak/schnupperkurs-kajak-wildwasser",
    "https://www.alpenverein-muenchen-oberland.de/alpinprogramm/sommer/klettern-alpin/keile-friends-co"
]

# Text to check for
TARGET_TEXT = "Leider haben wir momentan keine Veranstaltungen dieser Art im Angebot"

# Telegram bot setup
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


# --- FUNCTIONS ---

def check_page_for_text(url, target_text):
    """Return True if target_text is present, False if not."""
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        return target_text in response.text
    except Exception as e:
        print(f"❌ Error fetching {url}: {e}")
        return None  # None means failed


def send_telegram_message(message):
    """Send Telegram notification."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Missing Telegram credentials.")
        return
    try:
        api_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        params = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
        requests.get(api_url, params=params, timeout=10)
    except Exception as e:
        print(f"⚠️ Error sending Telegram message: {e}")


# --- MAIN ---

def main():
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    pages_missing_text = []
    pages_checked = []
    failed_pages = []

    for url in URLS:
        result = check_page_for_text(url, TARGET_TEXT)
        if result is None:
            failed_pages.append(url)
        elif not result:  # target text not found
            pages_missing_text.append(url)
        pages_checked.append(url)

    # Build Telegram message
    if pages_missing_text:
        msg = f"⚠️ Target text removed from the following pages ({timestamp}):\n"
        msg += "\n".join([f"• {url}" for url in pages_missing_text])
    else:
        msg = f"✅ Target text still present on all pages ({timestamp})."

    if failed_pages:
        msg += "\n\n⚠️ Failed to fetch:\n" + "\n".join([f"• {url}" for url in failed_pages])

    print(msg)
    send_telegram_message(msg)


if __name__ == "__main__":
    main()
