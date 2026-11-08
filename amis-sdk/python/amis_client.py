#!/usr/bin/env python3
"""Python client for the local APOLO AMIS host-agent camera endpoints."""
import json
from urllib.request import Request, urlopen
BASE = "http://127.0.0.1:8765"
def request(path, method="GET", timeout=30):
    req = Request(BASE + path, data=b"" if method == "POST" else None,
                  headers={"Content-Length": "0"} if method == "POST" else {}, method=method)
    with urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))
def discover():
    return request("/v1/camera")
def capture():
    """Ask the host agent to capture one frame and run local OCR."""
    return request("/v1/camera/capture", "POST")
if __name__ == "__main__":
    print(json.dumps({"discovery": discover(), "capture": capture()}, ensure_ascii=False, indent=2))
