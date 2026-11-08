#!/usr/bin/env python3
"""APOLO read-only laptop identity agent.

This agent reports OS-provided identity metadata only. It does NOT measure the
DC jack, infer its polarity, control power hardware, or authorize charging.
Bind to loopback and expose it to Android only through an explicitly configured
ADB reverse tunnel (USB debugging must be enabled by the owner).
"""
from __future__ import annotations

import json
import platform
import socket
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HOST = "127.0.0.1"
PORT = 8765
PROTOCOL = "apolo-host-agent/1"


def snapshot() -> dict:
    return {
        "protocol": PROTOCOL,
        "manufacturer": "unknown",
        "model": platform.node() or "unknown",
        "system": platform.system(),
        "system_release": platform.release(),
        "machine": platform.machine(),
        "hostname": socket.gethostname(),
        "identity_source": "host-operating-system",
        "dc_jack_voltage_v": None,
        "dc_jack_polarity": "UNMEASURED",
        "dc_measurement_available": False,
        "charging_authorized": False,
        "limitations": [
            "OS identity is not proof of physical laptop identity",
            "USB metadata cannot reveal DC jack voltage or polarity",
            "A physical isolated measurement circuit is required",
        ],
    }


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path != "/v1/identity":
            self.send_error(404)
            return
        body = json.dumps(snapshot(), separators=(",", ":")).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_):
        pass


if __name__ == "__main__":
    print(f"APOLO read-only host agent: http://{HOST}:{PORT}/v1/identity")
    print("USB bridge setup (owner-enabled ADB): adb reverse tcp:8765 tcp:8765")
    print("DC voltage/polarity: NOT MEASURED. Charging remains unauthorized.")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
