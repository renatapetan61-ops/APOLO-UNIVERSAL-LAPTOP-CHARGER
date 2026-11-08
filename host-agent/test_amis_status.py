import unittest

from apolo_host_agent import amis_status


class AmisIntegratedStatusTests(unittest.TestCase):
    def test_camera_and_vision_are_reported_as_one_pipeline(self):
        payload = amis_status()
        self.assertEqual(payload["protocol"], "amis-integrated-pipeline/2")
        self.assertIn("virtual_camera_core", payload["components"])
        self.assertIn("motherboard_vision_engine", payload["components"])
        self.assertIn("android_camera_x", payload["image_sources"])
        self.assertIn("usb_uvc_camera", payload["image_sources"])
        self.assertTrue(payload["inspection_requirements"]["direct_line_of_sight_to_motherboard_required"])

    def test_status_never_claims_optical_access_or_authorizes_charging(self):
        payload = amis_status()
        self.assertFalse(payload["inspection_requirements"]["opaque_chassis_transparency"])
        self.assertEqual(payload["charging"]["authorization"], "DENIED")
        self.assertIsNone(payload["charging"]["dc_jack_voltage"])


if __name__ == "__main__":
    unittest.main()
