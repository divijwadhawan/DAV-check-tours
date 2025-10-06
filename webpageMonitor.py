import hashlib
import requests
import os

# --- CONFIGURATION ---

URLS = [
    "https://www.alpenverein-muenchen-oberland.de/alpinprogramm/sommer/hochtouren/grundkurs-hochtouren",
    "https://www.alpenverein-muenchen-oberland.de/alpinprogramm/winter/wasserfalleisklettern/grundkurs-wasserfalleisklettern",
    "https://www.alpenverein-muenchen-oberland.de/alpinprogramm/winter/skischule/nordic-classic/nordic-classic-fuer-einsteiger",
    "https://www.alpenverein-muenchen-oberland.de/alpinprogramm/sommer/klettern-alpin/grundkurs-klettern-alpin",
    "https://www.alpenverein-muenchen-oberland.de/alpinprogramm/sommer/wildwasserkajak/schnupperkurs-kajak-wildwasser",
    "https://www.alpenverein-muenchen-oberland.de/alpinprogramm/sommer/klettern-alpin/keile-friends-co"
]

# Telegram bot setup
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Persistent hash file (Render mounts /data for persistent storage)
HASH_FILE = "/data/page_hashes.txt"


# --- FUNCTIONS ---

def get_page_hash(url):
    """Fetch page and return SHA256 hash."""
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        return hashlib.sha256(response.text.encode("utf-8")).hexdigest()
    except Exception as e:
        print(f"❌ Error fetching {url}: {e}")
        return None


def load_hashes():
    """Load previous hashes if available."""
    if not os.path.exists(HASH_FILE):
        return {}
    hashes = {}
    with open(HASH_FILE, "r") as f:
        for line in f:
            url, page_hash = line.strip().split(" ", 1)
            hashes[url] = page_hash
    return hashes


def save_hashes(hashes):
    """Save updated hashes."""
    os.makedirs(os.path.dirname(HASH_FILE), exist_ok=True)
    with open(HASH_FILE, "w") as f:
        for url, h in hashes.items():
            f.write(f"{url} {h}\n")


def send_telegram_message(message):
    """Send a Telegram message."""
    try:
        api_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        params = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
        requests.get(api_url, params=params, timeout=10)
    except Exception as e:
        print(f"⚠️ Error sending Telegram message: {e}")


# --- MAIN SCRIPT ---

def main():
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID env vars")
        return

    old_hashes = load_hashes()
    new_hashes = {}
    changed_urls = []

    for url in URLS:
        h = get_page_hash(url)
        if not h:
            continue
        old_hash = old_hashes.get(url)
        new_hashes[url] = h

        if old_hash and old_hash != h:
            changed_urls.append(url)

    if changed_urls:
        for url in changed_urls:
            msg = f"⚠️ Change detected on {url}"
            print(msg)
            send_telegram_message(msg)
    else:
        print("✅ No changes detected.")

    save_hashes(new_hashes)


if __name__ == "__main__":
    main()
