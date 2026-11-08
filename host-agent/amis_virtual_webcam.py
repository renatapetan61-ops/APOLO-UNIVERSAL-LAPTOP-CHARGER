#!/usr/bin/env python3
"""Relay a REAL UVC camera to a Windows virtual webcam.

This is an OS-level virtual webcam output, not a synthetic motherboard camera.
The physical UVC camera must have optical access to the subject. The Android
CameraX -> AMIS HTTP pipeline remains the authoritative OCR input path.
"""
from __future__ import annotations

import argparse
import sys
import time
import json
import urllib.error
import urllib.request

import cv2
import numpy as np
import pyvirtualcam


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", type=int, default=0, help="OpenCV camera index")
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=720)
    parser.add_argument("--fps", type=float, default=30.0)
    parser.add_argument("--backend", choices=("obs", "unitycapture"), default=None)
    parser.add_argument("--amis-url", default=None, help="Optional AMIS frame endpoint, e.g. http://127.0.0.1:8765/v1/virtual-camera/frames")
    parser.add_argument("--inspect-interval", type=float, default=2.0, help="Seconds between OCR submissions when --amis-url is set")
    parser.add_argument("--hardware-map-url", default=None, help="AMIS logical hardware map JSON endpoint")
    args = parser.parse_args()

    if args.width < 320 or args.height < 240 or not (1 <= args.fps <= 60):
        parser.error("Use dimensions >= 320x240 and FPS between 1 and 60")

    capture = cv2.VideoCapture(args.device, cv2.CAP_DSHOW)
    if not capture.isOpened():
        print("ERROR: physical UVC camera could not be opened.", file=sys.stderr)
        return 2

    capture.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
    capture.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)
    capture.set(cv2.CAP_PROP_FPS, args.fps)

    last_inspection = 0.0
    hardware_map = {"nodes": [], "node_count": 0}
    if args.hardware_map_url:
        try:
            with urllib.request.urlopen(args.hardware_map_url, timeout=8) as response:
                hardware_map = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, ValueError) as exc:
            print(f"AMIS hardware map unavailable: {exc}", file=sys.stderr)
    output_width = args.width + (360 if args.hardware_map_url else 0)
    try:
        with pyvirtualcam.Camera(
            width=output_width,
            height=args.height,
            fps=args.fps,
            fmt=pyvirtualcam.PixelFormat.RGB,
            backend=args.backend,
            print_fps=True,
        ) as virtual_camera:
            print(f"Virtual webcam: {virtual_camera.device}")
            print("Streaming real UVC frames. Press Ctrl+C to stop.")
            while True:
                ok, bgr = capture.read()
                if not ok or bgr is None:
                    print("WARN: no frame received; waiting for camera.", file=sys.stderr)
                    time.sleep(0.1)
                    continue
                if bgr.shape[1] != args.width or bgr.shape[0] != args.height:
                    bgr = cv2.resize(bgr, (args.width, args.height), interpolation=cv2.INTER_AREA)
                if args.hardware_map_url:
                    panel = np.zeros((args.height, 360, 3), dtype=np.uint8)
                    panel[:] = (24, 36, 48)
                    cv2.putText(panel, "AMIS HARDWARE MAP", (18, 34), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (230, 245, 255), 2)
                    cv2.putText(panel, "Components: " + str(hardware_map.get("node_count", 0)), (18, 68), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (160, 220, 210), 1)
                    y = 108
                    for node in hardware_map.get("nodes", [])[:16]:
                        category = str(node.get("category", "part")).upper()
                        label = str(node.get("label", "Unknown"))
                        cv2.putText(panel, (category + ": " + label)[:42], (18, y), cv2.FONT_HERSHEY_SIMPLEX, 0.40, (235, 240, 245), 1)
                        y += 34
                    cv2.putText(panel, "LOGICAL INVENTORY — NOT X-RAY", (18, args.height - 24), cv2.FONT_HERSHEY_SIMPLEX, 0.36, (120, 190, 255), 1)
                    bgr = np.concatenate((bgr, panel), axis=1)
                rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
                virtual_camera.send(np.ascontiguousarray(rgb))
                if args.amis_url and time.monotonic() - last_inspection >= max(0.5, args.inspect_interval):
                    encoded_ok, encoded = cv2.imencode(".jpg", bgr, [int(cv2.IMWRITE_JPEG_QUALITY), 92])
                    if encoded_ok:
                        request = urllib.request.Request(
                            args.amis_url,
                            data=encoded.tobytes(),
                            headers={"Content-Type": "image/jpeg", "X-AMIS-Source": "windows-uvc-virtualcam"},
                            method="POST",
                        )
                        try:
                            with urllib.request.urlopen(request, timeout=25) as response:
                                result = json.loads(response.read().decode("utf-8"))
                            print("AMIS:", result.get("result", "UNKNOWN"),
                                  "| OCR candidates:", len(result.get("ocr_candidates", [])),
                                  "| exact code:", result.get("exact_board_code"))
                        except (urllib.error.URLError, TimeoutError, ValueError) as exc:
                            print(f"AMIS submission failed: {exc}", file=sys.stderr)
                    last_inspection = time.monotonic()
                virtual_camera.sleep_until_next_frame()
    except KeyboardInterrupt:
        print("\nStopped.")
        return 0
    except (RuntimeError, OSError) as exc:
        print(f"Virtual webcam unavailable: {exc}", file=sys.stderr)
        print("Install and enable OBS Virtual Camera or Unity Capture driver.", file=sys.stderr)
        return 3
    finally:
        capture.release()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
