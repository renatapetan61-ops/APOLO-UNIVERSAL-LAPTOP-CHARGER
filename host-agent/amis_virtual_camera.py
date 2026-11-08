"""AMIS Virtual Camera Core: source-agnostic, in-memory image frame intake.

This is a software camera abstraction, not a physical sensor. Frames must come
from a real camera (for example the Android CameraX client) or an explicit
image source. Frames are validated and never persisted by this module.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import uuid

MAX_FRAME_BYTES = 8 * 1024 * 1024


def image_format(data: bytes) -> str | None:
    if data.startswith(b"\xff\xd8\xff"):
        return "jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return "webp"
    return None


@dataclass(frozen=True)
class VirtualCameraFrame:
    frame_id: str
    source_id: str
    captured_at: str
    media_type: str
    byte_length: int
    sha256: str
    data: bytes


class AMISVirtualCameraCore:
    """Validates and normalizes frames from pluggable external image sources."""

    PROTOCOL = "amis-virtual-camera/1"

    def __init__(self) -> None:
        self._last_frame: dict | None = None
        self._sources: dict[str, dict] = {}
        self._accepted_frames = 0
        self._rejected_frames = 0

    def ingest(self, data: bytes, source_id: str = "android-camerax",
               captured_at: str | None = None) -> VirtualCameraFrame:
        if not isinstance(data, bytes) or not data or len(data) > MAX_FRAME_BYTES:
            self._rejected_frames += 1
            raise ValueError("Frame must contain 1 byte to 8 MiB")
        kind = image_format(data)
        if kind is None:
            self._rejected_frames += 1
            raise ValueError("Unsupported frame; JPEG, PNG or WebP required")
        if not isinstance(source_id, str) or not source_id.strip() or len(source_id) > 80:
            self._rejected_frames += 1
            raise ValueError("Invalid image source identifier")
        timestamp = captured_at or datetime.now(timezone.utc).isoformat()
        frame = VirtualCameraFrame(
            frame_id=str(uuid.uuid4()), source_id=source_id.strip(),
            captured_at=timestamp, media_type="image/" + kind,
            byte_length=len(data), sha256=hashlib.sha256(data).hexdigest(),
            data=data,
        )
        self._accepted_frames += 1
        self._last_frame = {
            "frame_id": frame.frame_id, "source_id": frame.source_id,
            "captured_at": frame.captured_at, "media_type": frame.media_type,
            "byte_length": frame.byte_length, "sha256": frame.sha256,
        }
        source = self._sources.setdefault(frame.source_id, {"source_id": frame.source_id, "accepted_frames": 0, "last_frame": None})
        source["accepted_frames"] += 1
        source["last_frame"] = self._last_frame
        return frame

    def status(self) -> dict:
        return {
            "protocol": self.PROTOCOL,
            "component": "AMIS Virtual Camera Core",
            "mode": "software-image-source-abstraction",
            "physical_camera_embedded": False,
            "requires_image_source": True,
            "accepted_frames": self._accepted_frames,
            "rejected_frames": self._rejected_frames,
            "last_frame": self._last_frame,
            "image_sources_seen": list(self._sources.values()),
            "sources_seen_count": len(self._sources),
            "retention": "in-memory metadata only; frame bytes discarded after processing",
        }
