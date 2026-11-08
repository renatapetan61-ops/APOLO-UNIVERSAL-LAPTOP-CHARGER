#!/usr/bin/env python3
"""One-time, loopback-only Android approval gate for the Windows AMIS installer."""
from __future__ import annotations

import argparse
import hmac
import json
import secrets
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer


class ApprovalServer(HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8766)
    parser.add_argument("--timeout", type=int, default=300)
    args = parser.parse_args()
    token = f"{secrets.randbelow(1_000_000):06d}"
    approved = threading.Event()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            return

        def _reply(self, status: int, message: str) -> None:
            body = json.dumps({"approved": status == 200, "message": message}).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self):
            if self.path != "/v1/install/approve":
                return self._reply(404, "Endpoint não encontrado.")
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if length < 2 or length > 1024:
                    return self._reply(400, "Requisição inválida.")
                payload = json.loads(self.rfile.read(length))
                supplied = str(payload.get("code", ""))
            except (ValueError, json.JSONDecodeError, AttributeError):
                return self._reply(400, "Código inválido.")
            if not hmac.compare_digest(supplied, token):
                return self._reply(403, "Código de pareamento incorreto.")
            approved.set()
            return self._reply(200, "Autorização recebida do aplicativo APOLO.")

    server = ApprovalServer(("127.0.0.1", args.port), Handler)
    print(f"AMIS_APPROVAL_CODE={token}", flush=True)
    print(f"Aguardando confirmação no aplicativo por até {args.timeout} segundos...", flush=True)
    try:
        if not approved.wait(args.timeout):
            print("Tempo esgotado. Nenhum agente foi instalado.", file=sys.stderr)
            return 2
        print("APROVADO PELO APLICATIVO APOLO.", flush=True)
        return 0
    finally:
        server.server_close()


if __name__ == "__main__":
    raise SystemExit(main())
