"""Local DAV programme monitor; no accounts or Telegram required."""
import argparse
import csv
import hashlib
import json
import platform
import subprocess
import time
from collections import deque
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, urlsplit, parse_qs

import requests
from bs4 import BeautifulSoup

URL = 'https://www.alpenverein-muenchen-oberland.de/alpinprogramm'
HOME = Path(__file__).resolve().parent
OUT = HOME / 'output'
STATE = OUT / 'state.json'


def text(node):
    return node.get_text(' ', strip=True) if node else ''


def fetch(session, url):
    response = session.get(url, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, 'html.parser')
    if not soup.select_one('.namespace_WOdavTourList'):
        raise ValueError(f'Expected DAV programme markup missing: {url}')
    return soup


def signature(soup):
    # Ignore navigation, changing free-place recommendations and other unrelated content.
    notices = [text(n) for n in soup.select('.article_infobox') if 'alpinprogramm' in text(n).lower()]
    counts = [text(n) for n in soup.select('#tour-list-container .tour-list-count')]
    if not counts:
        raise ValueError('Programme category counts missing; keeping previous state')
    return hashlib.sha256(json.dumps([notices, counts], ensure_ascii=False).encode()).hexdigest()


def parse_page(soup, url):
    scope = soup.select_one('.namespace_WOdavTourList')
    children = []
    for a in scope.select('li.linked > a[href]'):
        link = urljoin(url, a['href'])
        if urlsplit(link).netloc == urlsplit(URL).netloc and not parse_qs(urlsplit(link).query).get('tour'):
            children.append(link)
    rows = []
    heading = text(soup.select_one('#tour-list-crumbtrail-current')) or text(soup.select_one('h1'))
    for entry in scope.select('.tour-entries .tour-entry-container'):
        if entry.find_parent(class_='oldeventsAccordion'):
            continue
        a = entry.find_parent('a', href=True)
        dates = text(entry.select_one('.tour-dates__datum'))
        if not a or not dates:
            raise ValueError(f'Course row missing date/link: {url}')
        link = urljoin(url, a['href'])
        code = text(entry.select_one('.tour-postcode'))
        title = text(entry.select_one('.tour-subtitle'))
        if code:
            title = title.replace(code, '').strip()
        status = entry.select_one('.tour-status')
        rows.append({'course': title or heading, 'dates': dates,
                     'location': text(entry.select_one('.tour-title__headline')),
                     'code': code, 'status': text(status) or (' '.join(status.get('class', [])) if status else 'unknown'),
                     'url': link})
    return children, rows


def collect(session, root):
    queue = deque([(URL, root)])
    visited, courses = set(), {}
    while queue:
        url, soup = queue.popleft()
        if url in visited:
            continue
        visited.add(url)
        if len(visited) > 2000:
            raise ValueError('Unexpectedly large crawl; no partial export saved')
        if soup is None:
            time.sleep(0.3)
            soup = fetch(session, url)
        children, rows = parse_page(soup, url)
        for row in rows:
            courses[row['url']] = row
        queue.extend((child, None) for child in children if child not in visited)
        print(f'\rReading programme: {len(visited)} pages, {len(courses)} dates', end='', flush=True)
    print()
    if not courses:
        raise ValueError('No current dated events found; no state saved')
    return sorted(courses.values(), key=lambda r: (r['course'], r['dates'], r['code']))


def save(rows):
    OUT.mkdir(exist_ok=True)
    path = OUT / 'courses.csv'
    temp = path.with_suffix('.tmp')
    with temp.open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    temp.replace(path)
    (OUT / 'courses.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding='utf-8')
    return path


def notify(message):
    print('\a' + message, flush=True)
    if platform.system() == 'Darwin':
        # Pass message as argv; never interpolate website content into AppleScript.
        script = 'on run argv\ndisplay notification (item 1 of argv) with title "DAV Alpinprogramm"\nend run'
        subprocess.run(['osascript', '-e', script, message], check=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--once', action='store_true', help='Check once and exit')
    parser.add_argument('--refresh', action='store_true', help='Force a full course export on the first check')
    args = parser.parse_args()
    session = requests.Session()
    session.headers['User-Agent'] = 'DAV-local-programme-monitor/1.0'
    print('Checking DAV every 120 seconds. Stop with Ctrl+C. Keep laptop awake and online.')
    force = args.refresh
    try:
        while True:
            started = time.monotonic()
            try:
                state = json.loads(STATE.read_text()) if STATE.exists() else {}
                soup = fetch(session, URL)
                current = signature(soup)
                if force or state.get('signature') != current:
                    baseline = not state
                    print('Creating initial course list.' if baseline else 'Programme announcement or category counts changed. Refreshing courses.')
                    rows = collect(session, soup)
                    path = save(rows)
                    old = set(state.get('course_urls', []))
                    added = [r for r in rows if r['url'] not in old]
                    if not baseline and added:
                        save_new = OUT / 'new_courses.csv'
                        with save_new.open('w', encoding='utf-8-sig', newline='') as f:
                            writer = csv.DictWriter(f, fieldnames=list(rows[0]))
                            writer.writeheader()
                            writer.writerows(added)
                        notify(f'{len(added)} newly listed dates. Course list: {path}')
                        for row in added:
                            print(f"{row['course']} | {row['dates']} | {row['url']}")
                    elif baseline:
                        print(f'Initial list: {len(rows)} dated events saved to {path}. These are the currently published events, not a new-launch alert.')
                    else:
                        print(f'List refreshed: {len(rows)} dated events. No newly listed dates.')
                    temp = STATE.with_suffix('.tmp')
                    temp.write_text(json.dumps({'signature': current, 'course_urls': [r['url'] for r in rows], 'checked': datetime.now().isoformat()}))
                    temp.replace(STATE)
                    force = False
                else:
                    print(f'{datetime.now():%Y-%m-%d %H:%M:%S}: programme unchanged.', flush=True)
            except (requests.RequestException, ValueError, OSError) as e:
                print(f'Check failed; will retry without replacing previous state: {e}', flush=True)
            if args.once:
                break
            time.sleep(max(0, 120 - (time.monotonic() - started)))
    except KeyboardInterrupt:
        print('\nMonitor stopped.')


if __name__ == '__main__':
    main()
