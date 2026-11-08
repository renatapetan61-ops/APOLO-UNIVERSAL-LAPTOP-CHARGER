import unittest
from unittest.mock import patch
from amis_camera import discover_cameras


class CameraDiscoveryTests(unittest.TestCase):
    @patch("amis_camera.platform.system", return_value="Linux")
    @patch("amis_camera.Path.glob", return_value=[])
    def test_no_camera_is_explicit(self, _glob, _system):
        result = discover_cameras()
        self.assertEqual(result["status"], "CAMERA_NOT_FOUND")
        self.assertEqual(result["devices"], [])

    @patch("amis_camera.platform.system", return_value="Linux")
    @patch("amis_camera.Path.glob")
    def test_detects_video_node_without_claiming_macro(self, glob, _system):
        class FakeNode:
            name = "video2"
            def __str__(self): return "/dev/video2"
        glob.return_value = [FakeNode()]
        with patch("amis_camera.Path.read_text", side_effect=OSError):
            result = discover_cameras()
        self.assertEqual(result["status"], "CAMERA_FOUND")
        self.assertFalse(result["devices"][0].get("macro_capability_verified", False))


if __name__ == "__main__":
    unittest.main()
