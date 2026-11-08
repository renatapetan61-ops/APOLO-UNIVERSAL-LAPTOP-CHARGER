import json
import tempfile
import unittest
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


if __name__ == "__main__":
    unittest.main()
