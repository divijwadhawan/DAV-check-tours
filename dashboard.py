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
TEST_LOCK = threading.Lock()
TEST = {"status": "idle"}


def winter_test():
    try:
        result = subprocess.run([sys.executable, "-u", str(ROOT / "check_pages.py"), "--test-winter"], capture_output=True, text=True, timeout=1800)
        if result.returncode:
            update = {"status": "error", "message": (result.stdout + result.stderr)[-1200:]}
        else:
            with (ROOT / "output/winter_test.csv").open(encoding="utf-8-sig", newline="") as f:
                count = len(list(csv.DictReader(f)))
            update = {"status": "success", "count": count, "message": f"Winter test passed: {count} published course dates extracted. This is a test, not a new-programme alert."}
    except (OSError, ValueError, subprocess.TimeoutExpired) as e:
        update = {"status": "error", "message": f"Winter test failed: {e}"}
    with TEST_LOCK:
        TEST.clear()
        TEST.update(update)


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
        elif path == '/api/winter-test':
            with TEST_LOCK:
                payload = json.dumps(TEST).encode()
            self.reply(payload, 'application/json')
        elif path == '/winter_test.csv':
            file = ROOT / 'output/winter_test.csv'
            self.reply(file.read_bytes(), 'text/csv; charset=utf-8') if file.exists() else self.reply(b'No winter test export yet', 'text/plain', 404)
        elif path in ('/', '/index.html'):
            self.reply((ROOT / 'dashboard.html').read_bytes(), 'text/html; charset=utf-8')
        elif path == '/courses.csv':
            file = ROOT / 'output/courses.csv'
            self.reply(file.read_bytes(), 'text/csv; charset=utf-8') if file.exists() else self.reply(b'First scan is still running.', 'text/plain', 404)
        else:
            self.reply(b'Not found', 'text/plain', 404)

    def do_POST(self):
        if self.path != "/api/winter-test":
            return self.reply(b"Not found", "text/plain", 404)
        # Only the local dashboard may trigger a scan; no arbitrary target URL.
        expected = f"http://127.0.0.1:{self.server.server_port}"
        if self.headers.get("Origin") != expected:
            return self.reply(b"Invalid origin", "text/plain", 403)
        with TEST_LOCK:
            if TEST.get("status") != "running":
                TEST.clear()
                TEST.update(status="running", message="Reading winter categories and course dates. This can take several minutes.")
                threading.Thread(target=winter_test, daemon=True).start()
            payload = json.dumps(TEST).encode()
        self.reply(payload, "application/json", 202)

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
