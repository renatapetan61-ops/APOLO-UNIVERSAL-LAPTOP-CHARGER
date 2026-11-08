import json
import tempfile
import unittest
from pathlib import Path

from board_ocr import MAX_IMAGE_BYTES, _image_type, _normalize, inspect_image


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


if __name__ == "__main__":
    unittest.main()
