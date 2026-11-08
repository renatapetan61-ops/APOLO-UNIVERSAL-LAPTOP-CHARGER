import unittest
from unittest.mock import patch

import apolo_diagnostics


class ApoloDiagnosticsTests(unittest.TestCase):
    def test_report_has_four_executed_software_chips_and_virtual_sensor_provenance(self):
        with patch.object(apolo_diagnostics.platform, "system", return_value="Unknown"):
            report = apolo_diagnostics.run_diagnostics()
        self.assertEqual(report["protocol"], "apolo-diagnostic-report/1")
        self.assertEqual(len(report["chips"]), 4)
        self.assertTrue(all(chip["state"] == "EXECUTED" for chip in report["chips"].values()))
        self.assertEqual(report["sensors"]["mode"], "VIRTUAL_SOFTWARE_SENSORS")
        self.assertFalse(report["sensors"]["physical_measurements_available"])

    def test_no_repair_is_claimed_without_a_verified_action(self):
        with patch.object(apolo_diagnostics.platform, "system", return_value="Unknown"):
            report = apolo_diagnostics.run_diagnostics()
        self.assertEqual(report["summary"]["corrected"], 0)
        self.assertEqual(report["repair_policy"]["mode"], "READ_ONLY")
        self.assertEqual(report["summary"]["found"], len(report["findings"]))

    def test_linux_checks_only_add_evidence_backed_findings(self):
        with patch.object(apolo_diagnostics.platform, "system", return_value="Linux"), \
             patch.object(apolo_diagnostics, "_linux_checks", return_value=[
                 {"code": "TEST", "title": "Teste", "detail": "evidência", "severity": "info",
                  "source": "unit-test", "recommendation": "revisar", "status": "FOUND"}
             ]):
            report = apolo_diagnostics.run_diagnostics()
        self.assertEqual(report["summary"]["found"], 1)
        self.assertEqual(report["findings"][0]["source"], "unit-test")


if __name__ == "__main__":
    unittest.main()
