#!/usr/bin/env python3
"""Local, optional motherboard silkscreen OCR. No network upload or image retention."""
from __future__ import annotations

import json
import re
import subprocess
import tempfile
from pathlib import Path

MAX_IMAGE_BYTES = 8 * 1024 * 1024
ALLOWED_SIGNATURES = (
    b"\xff\xd8\xff",                         # JPEG
    b"\x89PNG\r\n\x1a\n",                 # PNG
    b"RIFF",                                    # WebP container (validated below)
)


def _image_type(data: bytes) -> str | None:
    if data.startswith(ALLOWED_SIGNATURES[0]):
        return "jpeg"
    if data.startswith(ALLOWED_SIGNATURES[1]):
        return "png"
    if data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return "webp"
    return None


def _normalize(value: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", value.upper())


def _read_catalogue(path: Path) -> list[dict]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        entries = data.get("boards", [])
        return entries if isinstance(entries, list) else []
    except (OSError, json.JSONDecodeError, AttributeError):
        return []


def inspect_image(image: bytes, electronic_evidence: dict,
                  catalogue_path: Path, timeout: int = 20) -> dict:
    """Run Tesseract TSV OCR on an uploaded image held only in a temp file."""
    if not image or len(image) > MAX_IMAGE_BYTES:
        return {"result": "UNKNOWN", "image_quality": "INVALID_SIZE",
                "reason": "Image must be between 1 byte and 8 MiB"}
    kind = _image_type(image)
    if kind is None:
        return {"result": "UNKNOWN", "image_quality": "UNSUPPORTED_FORMAT",
                "reason": "Only JPEG, PNG and WebP images are accepted"}

    with tempfile.TemporaryDirectory(prefix="apolo-amis-") as tmp:
        source = Path(tmp) / ("capture." + kind)
        source.write_bytes(image)
        try:
            proc = subprocess.run(
                ["tesseract", str(source), "stdout", "--psm", "11", "tsv"],
                capture_output=True, text=True, timeout=timeout, check=False,
            )
        except FileNotFoundError:
            return {"result": "UNKNOWN", "image_quality": "OCR_ENGINE_MISSING",
                    "reason": "Install Tesseract OCR on the host to enable local OCR"}
        except subprocess.TimeoutExpired:
            return {"result": "UNKNOWN", "image_quality": "OCR_TIMEOUT",
                    "reason": "OCR exceeded the time limit"}
    if proc.returncode != 0:
        return {"result": "UNKNOWN", "image_quality": "OCR_FAILED",
                "reason": "Tesseract could not process the image"}

    lines: dict[tuple[str, str, str], list[str]] = {}
    for row in proc.stdout.splitlines()[1:]:
        cols = row.split("\t")
        if len(cols) < 12 or not cols[11].strip():
            continue
        try:
            conf = float(cols[10])
        except ValueError:
            continue
        if conf < 0:
            continue
        key = (cols[1], cols[2], cols[4])
        lines.setdefault(key, []).append((cols[11].strip(), conf))
    candidates = []
    for (page, block, line), words in lines.items():
        raw = " ".join(word for word, _ in words)
        normalized = _normalize(raw)
        if normalized:
            candidates.append({
                "raw_text": raw, "normalized_text": normalized,
                "mean_ocr_confidence": round(
                    sum(conf for _, conf in words) / max(1, len(words)), 2),
                "page": int(page), "block": int(block), "line": int(line),
            })

    catalogue = _read_catalogue(catalogue_path)
    matches = []
    seen = set()
    for candidate in candidates:
        for board in catalogue:
            code = board.get("code")
            if not isinstance(code, str) or not code.strip():
                continue
            if _normalize(code) == candidate["normalized_text"]:
                key = (board.get("id"), code)
                if key not in seen:
                    seen.add(key)
                    matches.append({"catalogue_id": board.get("id"),
                                    "code": code,
                                    "manufacturer": board.get("manufacturer"),
                                    "revision": board.get("revision")})

    raw_fields = electronic_evidence.get("raw_fields", {})
    # Corroboration must come from the baseboard manufacturer field only;
    # system vendor or BIOS vendor matches are not independent board evidence.
    electronic_board_manufacturer = raw_fields.get("manufacturer")
    electronic_board_token = _normalize(str(electronic_board_manufacturer or ""))
    corroborated = bool(matches) and bool(electronic_board_token) and any(
        _normalize(str(m.get("manufacturer") or "")) == electronic_board_token
        for m in matches
    )
    if len(matches) > 1:
        status = "CONFLICTING_EVIDENCE"
    elif len(matches) == 1 and corroborated:
        status = "CONFIRMED"
    elif len(matches) == 1:
        status = "PROBABLE"
    else:
        status = "UNKNOWN"

    return {
        "protocol": "apolo-board-id/1",
        "result": status,
        "image_quality": "OCR_TEXT_FOUND" if candidates else "NO_TEXT_DETECTED",
        "ocr_engine": "Tesseract TSV",
        "ocr_candidates": candidates,
        "catalogue_matches": matches,
        "electronic_evidence": electronic_evidence,
        "cross_check": {
            "electronic_fields_present": any(value not in (None, "") for value in raw_fields.values()),
            "exact_catalogue_match_count": len(matches),
            "manufacturer_corroborated": corroborated,
        },
        "exact_board_code": matches[0]["code"] if status == "CONFIRMED" else None,
        "image_retained": False,
        "note": "OCR confidence alone is not proof; empty catalogue means no board can be confirmed.",
    }
