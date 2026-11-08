import unittest

from amis_virtual_camera import AMISVirtualCameraCore, MAX_FRAME_BYTES
from amis_vision_engine import AMISMotherboardVisionEngine


class VirtualCameraCoreTests(unittest.TestCase):
    def test_accepts_jpeg_and_generates_frame_metadata(self):
        core = AMISVirtualCameraCore()
        frame = core.ingest(b"\xff\xd8\xff" + b"demo")
        self.assertEqual(frame.media_type, "image/jpeg")
        self.assertEqual(frame.source_id, "android-camerax")
        self.assertEqual(len(frame.sha256), 64)
        self.assertEqual(core.status()["accepted_frames"], 1)

    def test_accepts_alternative_sources(self):
        frame = AMISVirtualCameraCore().ingest(
            b"\x89PNG\r\n\x1a\n" + b"\x00" * 16, source_id="file-import"
        )
        self.assertEqual(frame.source_id, "file-import")

    def test_rejects_invalid_and_oversized_frames(self):
        core = AMISVirtualCameraCore()
        with self.assertRaises(ValueError):
            core.ingest(b"not-image")
        with self.assertRaises(ValueError):
            core.ingest(b"x" * (MAX_FRAME_BYTES + 1))
        self.assertEqual(core.status()["rejected_frames"], 2)

    def test_vision_engine_reports_source_and_never_claims_physical_camera(self):
        frame = AMISVirtualCameraCore().ingest(b"\xff\xd8\xffdemo")
        self.assertEqual(frame.source_id, "android-camerax")
        self.assertEqual(AMISVirtualCameraCore().status()["physical_camera_embedded"], False)


if __name__ == "__main__":
    unittest.main()
