"""
Serveur API local rapide pour tester des endpoints.
Usage: python scripts/quick_api.py [--port 8000]
"""
import sys
import argparse
import json
from http.server import HTTPServer, BaseHTTPRequestHandler


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        response = {"status": "ok", "path": self.path, "message": "API locale fonctionnelle"}
        self.wfile.write(json.dumps(response).encode())

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode() if length else ""
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        response = {"status": "received", "body": body}
        self.wfile.write(json.dumps(response).encode())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", "-p", type=int, default=8000)
    args = parser.parse_args()
    server = HTTPServer(("0.0.0.0", args.port), Handler)
    print(f"🚀 API locale sur http://localhost:{args.port}")
    server.serve_forever()
