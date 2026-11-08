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

    try:
        with pyvirtualcam.Camera(
            width=args.width,
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
                rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
                virtual_camera.send(np.ascontiguousarray(rgb))
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
