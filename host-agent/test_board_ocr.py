import json
import tempfile
import unittest
import subprocess
from unittest.mock import patch
from pathlib import Path

from board_ocr import MAX_IMAGE_BYTES, _image_type, _normalize, _parse_tsv, _code_seen, inspect_image


class BoardOcrTests(unittest.TestCase):
    def test_image_signatures(self):
        self.assertEqual(_image_type(b"\xff\xd8\xffabc"), "jpeg")
        self.assertEqual(_image_type(b"\x89PNG\r\n\x1a\nabc"), "png")
        self.assertEqual(_image_type(b"RIFFxxxxWEBPabc"), "webp")
        self.assertIsNone(_image_type(b"not an image"))

    def test_normalization(self):
        self.assertEqual(_normalize("DA0ZQMB6F0 REV: 1.0"), "DA0ZQMB6F0REV10")

    def test_rejects_oversized_image(self):
        result = inspect_image(b"x" * (MAX_IMAGE_BYTES + 1), {}, Path("missing.json"))
        self.assertEqual(result["image_quality"], "INVALID_SIZE")

    def test_rejects_unknown_format(self):
        result = inspect_image(b"plain text", {}, Path("missing.json"))
        self.assertEqual(result["image_quality"], "UNSUPPORTED_FORMAT")

    def test_empty_catalogue_never_confirms(self):
        with tempfile.TemporaryDirectory() as tmp:
            catalogue = Path(tmp) / "catalogue.json"
            catalogue.write_text(json.dumps({"boards": []}), encoding="utf-8")
            # A valid image header is sufficient to reach the optional OCR engine.
            result = inspect_image(b"\x89PNG\r\n\x1a\n" + b"x" * 16, {}, catalogue)
            self.assertIn(result["result"], ("UNKNOWN",))
            self.assertIsNone(result.get("exact_board_code"))

    def test_tsv_parser_preserves_line_text_and_confidence(self):
        tsv = "level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\tleft\ttop\twidth\theight\tconf\ttext\n" \
              "5\t1\t1\t1\t1\t1\t0\t0\t10\t10\t92.5\tDA0ZQMB6F0\n"
        candidates = _parse_tsv(tsv)
        self.assertEqual(candidates[0]["normalized_text"], "DA0ZQMB6F0")
        self.assertEqual(candidates[0]["mean_ocr_confidence"], 92.5)
        self.assertTrue(_code_seen("DA0ZQMB6F0", candidates[0]))

    def test_catalogue_matching_is_exact_not_fuzzy(self):
        candidate = {"normalized_text": "DA0ZQMB6F0REV10", "tokens": ["DA0ZQMB6F0", "REV10"]}
        self.assertTrue(_code_seen("DA0ZQMB6F0", candidate))
        self.assertFalse(_code_seen("DA0ZQMB6", candidate))
        self.assertFalse(_code_seen("ZQMB6F0", candidate))

    def test_ocr_pipeline_uses_exact_catalogue_match_without_claiming_confirmation(self):
        try:
            from PIL import Image
        except ImportError:
            self.skipTest("Pillow is optional")
        import io
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            image_buffer = io.BytesIO()
            Image.new("RGB", (320, 120), "white").save(image_buffer, format="PNG")
            image = image_buffer.getvalue()
            catalogue = root / "catalogue.json"
            catalogue.write_text(json.dumps({"boards": [{
                "id": "verified-board-1", "code": "DA0ZQMB6F0",
                "manufacturer": "Example OEM", "revision": "1.0"
            }]}), encoding="utf-8")
            header = "level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\tleft\ttop\twidth\theight\tconf\ttext\n"
            row = "5\t1\t1\t1\t1\t1\t0\t0\t100\t20\t96.0\tDA0ZQMB6F0\n"
            fake = subprocess.CompletedProcess(["tesseract"], 0, header + row, "")
            with patch("board_ocr.subprocess.run", return_value=fake) as run:
                result = inspect_image(
                    image, {"raw_fields": {"manufacturer": "Different OEM"}}, catalogue
                )
            self.assertEqual(result["result"], "PROBABLE")
            self.assertIsNone(result["exact_board_code"])
            self.assertEqual(result["catalogue_matches"][0]["code"], "DA0ZQMB6F0")
            self.assertTrue(result["preprocessing_available"])
            self.assertGreaterEqual(run.call_count, 2)


if __name__ == "__main__":
    unittest.main()
