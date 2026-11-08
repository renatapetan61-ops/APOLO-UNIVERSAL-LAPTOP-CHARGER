#!/usr/bin/env python3
"""Optional USB/UVC camera discovery and explicit local capture for APOLO AMIS."""
from __future__ import annotations
import platform
import subprocess
from pathlib import Path

def discover_cameras() -> dict:
    system = platform.system()
    devices = []
    if system == "Linux":
        for node in sorted(Path("/dev").glob("video[0-9]*")):
            name = None
            try:
                name = (Path("/sys/class/video4linux") / node.name / "name").read_text().strip()
            except OSError:
                pass
            devices.append({"id": node.name, "path": str(node), "name": name,
                            "transport": "video4linux", "capture_supported": True})
    elif system == "Windows":
        command = ["powershell", "-NoProfile", "-NonInteractive", "-Command",
                   "Get-PnpDevice -PresentOnly -Class Camera,Image | Select-Object FriendlyName,InstanceId,Status | ConvertTo-Json -Compress"]
        try:
            p = subprocess.run(command, capture_output=True, text=True, timeout=8)
            if p.returncode == 0 and p.stdout.strip():
                import json
                data = json.loads(p.stdout)
                if isinstance(data, dict): data = [data]
                for item in data:
                    devices.append({"id": item.get("InstanceId"), "name": item.get("FriendlyName"),
                                    "status": item.get("Status"), "transport": "windows-pnp",
                                    "capture_supported": False})
        except (OSError, subprocess.TimeoutExpired, ValueError):
            pass
    elif system == "Darwin":
        try:
            p = subprocess.run(["system_profiler", "SPCameraDataType", "-json"],
                               capture_output=True, text=True, timeout=12)
            if p.returncode == 0:
                import json
                data = json.loads(p.stdout)
                for item in data.get("SPCameraDataType", []):
                    devices.append({"id": item.get("_name"), "name": item.get("_name"),
                                    "transport": "system-profiler", "capture_supported": False})
        except (OSError, subprocess.TimeoutExpired, ValueError):
            pass
    return {"status": "CAMERA_FOUND" if devices else "CAMERA_NOT_FOUND",
            "platform": system, "devices": devices,
            "note": "USB enumeration does not prove macro optics, focus distance, illumination control, or safe internal mounting."}

def capture_and_inspect(electronic_evidence: dict, catalogue_path: Path,
                        device_index: int = 0) -> dict:
    try:
        import cv2
    except ImportError:
        return {"status": "CAPTURE_UNAVAILABLE", "reason": "OpenCV is not installed on the host"}
    cap = cv2.VideoCapture(device_index, cv2.CAP_ANY)
    try:
        if not cap.isOpened():
            return {"status": "CAMERA_OPEN_FAILED", "reason": "Camera could not be opened"}
        ok, frame = cap.read()
        if not ok or frame is None:
            return {"status": "CAPTURE_FAILED", "reason": "Camera returned no frame"}
        height, width = frame.shape[:2]
        if width < 320 or height < 240:
            return {"status": "IMAGE_TOO_SMALL", "width": width, "height": height}
        ok, encoded = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 92])
        if not ok:
            return {"status": "ENCODE_FAILED"}
        from board_ocr import inspect_image
        result = inspect_image(encoded.tobytes(), electronic_evidence, catalogue_path)
        return {"status": "CAPTURED", "camera_index": device_index,
                "image_dimensions": {"width": width, "height": height},
                "capture_transport": "local UVC/OpenCV",
                "macro_capability_verified": False,
                "illumination_control": "NOT_AVAILABLE_UNLESS_HARDWARE_SUPPORTS_IT",
                "inspection": result}
    finally:
        cap.release()


def capture_frame(device_index: int = 0) -> tuple[bytes | None, dict]:
    """Capture one JPEG frame from a local UVC camera without running OCR here."""
    try:
        import cv2
    except ImportError:
        return None, {"status": "CAPTURE_UNAVAILABLE", "reason": "OpenCV is not installed on the host"}
    cap = cv2.VideoCapture(device_index, cv2.CAP_ANY)
    try:
        if not cap.isOpened():
            return None, {"status": "CAMERA_OPEN_FAILED", "reason": "Camera could not be opened"}
        ok, frame = cap.read()
        if not ok or frame is None:
            return None, {"status": "CAPTURE_FAILED", "reason": "Camera returned no frame"}
        height, width = frame.shape[:2]
        if width < 320 or height < 240:
            return None, {"status": "IMAGE_TOO_SMALL", "width": width, "height": height}
        ok, encoded = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 92])
        if not ok:
            return None, {"status": "ENCODE_FAILED"}
        return encoded.tobytes(), {"status": "CAPTURED", "camera_index": device_index, "image_dimensions": {"width": width, "height": height}, "capture_transport": "local UVC/OpenCV", "macro_capability_verified": False, "illumination_control": "NOT_AVAILABLE_UNLESS_HARDWARE_SUPPORTS_IT"}
    finally:
        cap.release()
