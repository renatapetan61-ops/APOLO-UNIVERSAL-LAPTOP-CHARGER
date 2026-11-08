import unittest

from apolo_virtual_ics import ApoloVirtualIcRuntime


class VirtualIcRuntimeTests(unittest.TestCase):
    def test_all_four_independent_chips_execute(self):
        result = ApoloVirtualIcRuntime().execute([])
        self.assertEqual(result["runtime"], "APOLO-VIRTUAL-IC-RUNTIME/1")
        self.assertEqual(len(result["chips"]), 4)
        self.assertEqual({item["id"] for item in result["chips"]}, {
            "APOLO-BMS-IC", "APOLO-CHARGE-IC", "APOLO-SAFETY-IC", "APOLO-USB-PD-IC"
        })
        self.assertTrue(all(item["state"] == "EXECUTED" for item in result["chips"]))

    def test_safety_chip_flags_high_severity_findings(self):
        finding = {"code": "X", "severity": "critical", "source": "test"}
        result = ApoloVirtualIcRuntime().execute([finding])
        safety = next(item for item in result["chips"] if item["id"] == "APOLO-SAFETY-IC")
        self.assertEqual(safety["result"], "REVIEW_REQUIRED")

    def test_runtime_never_claims_physical_sensor_measurements(self):
        result = ApoloVirtualIcRuntime().execute([])
        self.assertFalse(result["physical_sensor_measurements"])


if __name__ == "__main__":
    unittest.main()
