"""Fast local HTTP decision server for Codex and local scripts.

Runs model once in memory on Apple Neural Engine.
All subsequent requests take ~20-30 ms.
Automatically escalates to JEV Cloud API when needed.
"""

import json
import time
import os
import sys
import signal
from http.server import HTTPServer, BaseHTTPRequestHandler

# Ignore SIGHUP so server survives terminal exit
if hasattr(signal, "SIGHUP"):
    signal.signal(signal.SIGHUP, signal.SIG_IGN)

# Ensure current directory is on python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hybrid import triage_hybrid
from agent import get_agent


class DecisionHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/decide":
            self.send_response(404)
            self.end_headers()
            return

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8")

        try:
            data = json.loads(body)
            ticket_text = data.get("ticket", "")
            if not ticket_text:
                raise ValueError("Missing 'ticket' field in JSON body")

            threshold = float(data.get("threshold", 0.70))
            res = triage_hybrid(ticket_text, confidence_threshold=threshold)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(res, indent=2).encode("utf-8"))

        except Exception as e:
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))

    def log_message(self, format, *args):
        print(f"[HTTP Server] {args[0]} - {args[1]} ({args[2]})")


def run_server(port=8080):
    print("\nWarmup: Loading Laya CoreML Agent into Apple Silicon Neural Engine...")
    t0 = time.perf_counter()
    get_agent()
    print(f"Model ready on Neural Engine in {(time.perf_counter() - t0):.1f}s!")
    print(f"Server listening on http://127.0.0.1:{port}/decide")
    print("Test with: curl -s -X POST http://127.0.0.1:8080/decide -d '{\"ticket\":\"server crash\"}'\n")

    httpd = HTTPServer(("127.0.0.1", port), DecisionHandler)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server.")
        httpd.server_close()


if __name__ == "__main__":
    run_server()
