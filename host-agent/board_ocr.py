#!/usr/bin/env python3
"""Local motherboard silkscreen OCR with optional conservative preprocessing."""
from __future__ import annotations

import io
import json
import re
import subprocess
import tempfile
from pathlib import Path

MAX_IMAGE_BYTES = 8 * 1024 * 1024
ALLOWED_SIGNATURES = (b"\xff\xd8\xff", b"\x89PNG\r\n\x1a\n", b"RIFF")


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
        return [item for item in entries if isinstance(item, dict)] if isinstance(entries, list) else []
    except (OSError, json.JSONDecodeError, AttributeError):
        return []


def _image_variants(image: bytes) -> list[tuple[str, bytes]]:
    """Return original and an optional 2x grayscale/high-contrast variant."""
    variants = [("original", image)]
    try:
        from PIL import Image, ImageEnhance, ImageFilter, ImageOps
        with Image.open(io.BytesIO(image)) as opened:
            opened.load()
            if opened.width < 1 or opened.height < 1 or opened.width * opened.height > 40_000_000:
                return variants
            gray = ImageOps.grayscale(opened)
            gray = ImageOps.autocontrast(gray)
            scale = min(3, max(2, 1600 // max(1, gray.width)))
            if gray.width * gray.height * scale * scale <= 40_000_000:
                gray = gray.resize((gray.width * scale, gray.height * scale), Image.Resampling.LANCZOS)
            gray = ImageEnhance.Contrast(gray).enhance(1.6)
            gray = gray.filter(ImageFilter.UnsharpMask(radius=1.5, percent=160, threshold=3))
            output = io.BytesIO()
            gray.save(output, format="PNG", optimize=True)
            enhanced = output.getvalue()
            if enhanced and enhanced != image:
                variants.append(("enhanced-2x-grayscale", enhanced))
    except (ImportError, OSError, ValueError, SyntaxError):
        pass
    return variants


def _parse_tsv(tsv: str) -> list[dict]:
    lines: dict[tuple[str, str, str], list[tuple[str, float]]] = {}
    for row in tsv.splitlines()[1:]:
        cols = row.split("\t")
        if len(cols) < 12 or not cols[11].strip():
            continue
        try:
            confidence = float(cols[10])
        except ValueError:
            continue
        if confidence < 0:
            continue
        key = (cols[1], cols[2], cols[4])
        lines.setdefault(key, []).append((cols[11].strip(), confidence))
    candidates = []
    for (page, block, line), words in lines.items():
        raw = " ".join(word for word, _ in words)
        normalized = _normalize(raw)
        if normalized:
            candidates.append({
                "raw_text": raw, "normalized_text": normalized,
                "tokens": [_normalize(word) for word, _ in words if _normalize(word)],
                "mean_ocr_confidence": round(sum(conf for _, conf in words) / len(words), 2),
                "page": int(page), "block": int(block), "line": int(line),
            })
    return candidates


def _code_seen(code: str, candidate: dict) -> bool:
    normalized = _normalize(code)
    if not normalized:
        return False
    # Exact normalized line or exact OCR token only; no fuzzy/substring matches.
    return normalized == candidate.get("normalized_text") or normalized in candidate.get("tokens", [])


def inspect_image(image: bytes, electronic_evidence: dict,
                  catalogue_path: Path, timeout: int = 20) -> dict:
    """Run local Tesseract OCR on original and optional enhanced image variants."""
    if not image or len(image) > MAX_IMAGE_BYTES:
        return {"result": "UNKNOWN", "image_quality": "INVALID_SIZE",
                "reason": "Image must be between 1 byte and 8 MiB"}
    kind = _image_type(image)
    if kind is None:
        return {"result": "UNKNOWN", "image_quality": "UNSUPPORTED_FORMAT",
                "reason": "Only JPEG, PNG and WebP images are accepted"}

    all_candidates: dict[tuple[str, str], dict] = {}
    used_variants = []
    variants = _image_variants(image)
    with tempfile.TemporaryDirectory(prefix="apolo-amis-") as tmp:
        root = Path(tmp)
        try:
            for variant_name, variant_data in variants:
                source = root / (variant_name + (".png" if variant_name != "original" else "." + kind))
                source.write_bytes(variant_data)
                for psm in ("11", "6"):
                    proc = subprocess.run(
                        ["tesseract", str(source), "stdout", "--psm", psm, "tsv"],
                        capture_output=True, text=True, timeout=max(1, min(timeout, 60)), check=False,
                    )
                    if proc.returncode == 0:
                        used_variants.append(variant_name + "/psm-" + psm)
                        for candidate in _parse_tsv(proc.stdout):
                            key = (candidate["normalized_text"], candidate["raw_text"])
                            previous = all_candidates.get(key)
                            if previous is None or candidate["mean_ocr_confidence"] > previous["mean_ocr_confidence"]:
                                candidate["preprocessing"] = variant_name
                                candidate["psm"] = psm
                                all_candidates[key] = candidate
        except FileNotFoundError:
            return {"result": "UNKNOWN", "image_quality": "OCR_ENGINE_MISSING",
                    "reason": "Install Tesseract OCR on the host to enable local OCR"}
        except subprocess.TimeoutExpired:
            return {"result": "UNKNOWN", "image_quality": "OCR_TIMEOUT",
                    "reason": "OCR exceeded the time limit"}
        except OSError:
            return {"result": "UNKNOWN", "image_quality": "OCR_FAILED",
                    "reason": "Could not create or process the temporary OCR image"}

    candidates = list(all_candidates.values())
    catalogue = _read_catalogue(catalogue_path)
    matches, seen = [], set()
    for candidate in candidates:
        for board in catalogue:
            code = board.get("code")
            if not isinstance(code, str) or not code.strip() or not _code_seen(code, candidate):
                continue
            key = (board.get("id"), code)
            if key not in seen:
                seen.add(key)
                matches.append({"catalogue_id": board.get("id"), "code": code,
                                "manufacturer": board.get("manufacturer"),
                                "revision": board.get("revision")})

    raw_fields = electronic_evidence.get("raw_fields", {}) if isinstance(electronic_evidence, dict) else {}
    electronic_board_manufacturer = raw_fields.get("manufacturer") if isinstance(raw_fields, dict) else None
    electronic_board_token = _normalize(str(electronic_board_manufacturer or ""))
    corroborated = bool(matches) and bool(electronic_board_token) and any(
        _normalize(str(m.get("manufacturer") or "")) == electronic_board_token for m in matches
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
        "protocol": "apolo-board-id/2",
        "result": status,
        "image_quality": "OCR_TEXT_FOUND" if candidates else "NO_TEXT_DETECTED",
        "ocr_engine": "Tesseract TSV",
        "ocr_passes": used_variants,
        "preprocessing_available": len(variants) > 1,
        "ocr_candidates": candidates,
        "catalogue_matches": matches,
        "electronic_evidence": electronic_evidence,
        "cross_check": {
            "electronic_fields_present": any(value not in (None, "") for value in raw_fields.values()) if isinstance(raw_fields, dict) else False,
            "exact_catalogue_match_count": len(matches),
            "manufacturer_corroborated": corroborated,
        },
        "exact_board_code": matches[0]["code"] if status == "CONFIRMED" else None,
        "image_retained": False,
        "note": "OCR is evidence, not proof. No fuzzy match is used; an empty catalogue cannot confirm a board.",
    }
