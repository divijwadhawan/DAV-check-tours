"""Telegram delivery with a persistent local outbox; credentials never logged."""
import hashlib
import json
import os
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parent
CONFIG = ROOT / 'telegram_config.json'
OUTBOX = ROOT / 'output/telegram_outbox.json'


def credentials():
    config = json.loads(CONFIG.read_text()) if CONFIG.exists() else {}
    token = os.getenv('TELEGRAM_BOT_TOKEN') or config.get('bot_token')
    chat = os.getenv('TELEGRAM_CHAT_ID') or config.get('chat_id')
    if not token or not chat or token == 'YOUR_EXISTING_BOT_TOKEN':
        raise ValueError('Telegram not configured. Fill telegram_config.json with bot_token and chat_id.')
    return token, chat


def send(message):
    token, chat = credentials()
    try:
        response = requests.post(f'https://api.telegram.org/bot{token}/sendMessage',
                                 json={'chat_id': chat, 'text': message[:4000]}, timeout=20)
        result = response.json()
        if response.status_code != 200 or not result.get('ok'):
            raise ValueError(f'Telegram rejected the message (HTTP {response.status_code}). Check bot token, chat ID and whether you started the bot.')
    except requests.RequestException:
        # Request exception strings can contain the token-bearing URL.
        raise ValueError('Telegram network error; message was not confirmed.') from None
    return True


def read_outbox():
    return json.loads(OUTBOX.read_text()) if OUTBOX.exists() else {'pending': [], 'sent': []}


def persist(data):
    OUTBOX.parent.mkdir(exist_ok=True)
    temp = OUTBOX.with_suffix('.tmp')
    temp.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
    temp.replace(OUTBOX)


def queue(message):
    data = read_outbox()
    key = hashlib.sha256(message.encode()).hexdigest()
    if key not in data['sent'] and not any(m['id'] == key for m in data['pending']):
        data['pending'].append({'id': key, 'text': message})
        persist(data)


def deliver_pending():
    data = read_outbox()
    while data['pending']:
        item = data['pending'][0]
        try:
            send(item['text'])
        except (ValueError, OSError) as e:
            print(f'{e} Alert stays queued and will retry on the next check.', flush=True)
            return
        data['pending'].pop(0)
        data['sent'].append(item['id'])
        persist(data)
        print('Telegram alert delivered.', flush=True)


def programme_message(rows):
    lines = [f'DAV Alpinprogramm update: {len(rows)} newly published course dates detected.',
             'https://www.alpenverein-muenchen-oberland.de/alpinprogramm', '']
    for row in rows[:6]:
        price = f" | €{row['cost_eur']} (members)" if row.get('cost_eur') else ''
        lines.append(f"{row['course'][:120]} | {row['dates'][:90]}{price}\n{row['url']}")
    if len(rows) > 6:
        lines.append(f'Plus {len(rows)-6} more dates. Full list in your local dashboard / CSV.')
    return '\n'.join(lines)[:4000]
