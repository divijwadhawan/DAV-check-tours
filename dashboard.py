"""Serve the course dashboard on localhost and run the monitor alongside it."""
import csv
import json
import subprocess
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def read_courses():
    path = ROOT / 'output/courses.csv'
    if not path.exists():
        return [], None
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f)), path.stat().st_mtime


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split('?')[0]
        if path == '/api/courses':
            try:
                rows, updated = read_courses()
                payload = {'courses': rows, 'updated': updated}
                self.reply(json.dumps(payload, ensure_ascii=False).encode(), 'application/json; charset=utf-8')
            except (OSError, ValueError) as e:
                self.reply(json.dumps({'error': str(e)}).encode(), 'application/json', 503)
        elif path in ('/', '/index.html'):
            self.reply((ROOT / 'dashboard.html').read_bytes(), 'text/html; charset=utf-8')
        elif path == '/courses.csv':
            file = ROOT / 'output/courses.csv'
            self.reply(file.read_bytes(), 'text/csv; charset=utf-8') if file.exists() else self.reply(b'First scan is still running.', 'text/plain', 404)
        else:
            self.reply(b'Not found', 'text/plain', 404)

    def reply(self, body, content_type, status=200):
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


def main():
    server = ThreadingHTTPServer(('127.0.0.1', 8765), Handler)
    monitor = subprocess.Popen([sys.executable, '-u', str(ROOT / 'check_pages.py')])
    threading.Thread(target=server.serve_forever, daemon=True).start()
    print('Dashboard: http://127.0.0.1:8765 — stop with Ctrl+C', flush=True)
    webbrowser.open('http://127.0.0.1:8765')
    try:
        monitor.wait()
    except KeyboardInterrupt:
        monitor.terminate()
        try:
            monitor.wait(timeout=5)
        except subprocess.TimeoutExpired:
            monitor.kill()
            monitor.wait()
    finally:
        server.shutdown()
        server.server_close()


if __name__ == '__main__':
    main()
