#!/usr/bin/env python3
"""
Newsletter Builder local server — port 8766
Serves files from this directory AND proxies images at /img?url=...
so html2canvas can capture cross-origin images without CORS errors.
"""

import http.server
import urllib.request
import urllib.parse
import os
import sys

PORT = 8766
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class Handler(http.server.SimpleHTTPRequestHandler):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)

        # ── Image proxy endpoint: /img?url=https://... ──────────────────────
        if parsed.path == "/img":
            params = urllib.parse.parse_qs(parsed.query)
            url = params.get("url", [None])[0]
            if not url:
                self.send_error(400, "Missing url parameter")
                return
            try:
                req = urllib.request.Request(url, headers={
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                                  "Chrome/120.0.0.0 Safari/537.36",
                    "Referer": "https://www.properhotel.com/"
                })
                with urllib.request.urlopen(req, timeout=15) as resp:
                    data        = resp.read()
                    content_type = resp.headers.get_content_type() or "image/jpeg"

                self.send_response(200)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(data)))
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Cache-Control", "public, max-age=3600")
                self.end_headers()
                self.wfile.write(data)

            except Exception as e:
                self.send_error(502, f"Proxy error: {e}")
            return

        # ── Everything else: serve files normally ───────────────────────────
        super().do_GET()

    def log_message(self, fmt, *args):
        # Suppress noisy request logs; only print errors
        if args[1] not in ("200", "304"):
            super().log_message(fmt, *args)


if __name__ == "__main__":
    os.chdir(DIRECTORY)
    print(f"Newsletter Builder server running at http://localhost:{PORT}")
    print(f"Serving files from: {DIRECTORY}")
    print(f"Image proxy at:     http://localhost:{PORT}/img?url=<image-url>")
    print("Press Ctrl+C to stop.\n")
    with http.server.HTTPServer(("", PORT), Handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")
            sys.exit(0)
