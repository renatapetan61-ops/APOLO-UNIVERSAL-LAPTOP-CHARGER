"""AMIS Motherboard Vision Engine: local visual metadata + OCR pipeline."""
from __future__ import annotations

from pathlib import Path
import struct
from board_ocr import inspect_image


def _dimensions(data: bytes, media_type: str) -> tuple[int | None, int | None]:
    # Read PNG dimensions without decoding or allocating a full image.
    if media_type == "image/png" and len(data) >= 24:
        return struct.unpack(">II", data[16:24])
    # JPEG/WebP dimensions are intentionally unknown unless an optional decoder
    # is installed; OCR remains available and no dimensions are fabricated.
    return None, None


class AMISMotherboardVisionEngine:
    PROTOCOL = "amis-motherboard-vision/1"

    def inspect(self, frame, electronic_evidence: dict,
                catalogue_path: Path) -> dict:
        width, height = _dimensions(frame.data, frame.media_type)
        result = inspect_image(frame.data, electronic_evidence, catalogue_path)
        result.update({
            "vision_protocol": self.PROTOCOL,
            "capture": {
                "frame_id": frame.frame_id,
                "source_id": frame.source_id,
                "captured_at": frame.captured_at,
                "media_type": frame.media_type,
                "byte_length": frame.byte_length,
                "sha256": frame.sha256,
                "width": width,
                "height": height,
            },
            "vision_capabilities": {
                "local_ocr": True,
                "silkscreen_text_extraction": True,
                "catalogue_cross_check": True,
                "image_enhancement": "not_enabled_without_validated_decoder",
                "automatic_board_code_guessing": False,
            },
            "image_retained": False,
        })
        return result
