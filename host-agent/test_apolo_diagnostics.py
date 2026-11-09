import unittest
from unittest.mock import patch

import apolo_diagnostics


class ApoloDiagnosticsTests(unittest.TestCase):
    def test_report_has_four_executed_software_chips_and_sensor_provenance(self):
        with patch.object(apolo_diagnostics.platform, "system", return_value="Unknown"):
            report = apolo_diagnostics.run_diagnostics()
        self.assertEqual(report["protocol"], "apolo-diagnostic-report/2")
        self.assertEqual(len(report["chips"]), 4)
        self.assertTrue(all(chip["state"] == "EXECUTED" for chip in report["chips"].values()))
        self.assertEqual(report["sensors"]["mode"], "VIRTUAL_SOFTWARE_SENSORS")
        self.assertFalse(report["sensors"]["physical_measurements_available"])

    def test_no_repair_is_claimed_by_diagnostic_scan(self):
        with patch.object(apolo_diagnostics.platform, "system", return_value="Unknown"):
            report = apolo_diagnostics.run_diagnostics()
        self.assertEqual(report["summary"]["corrected"], 0)
        self.assertEqual(report["repair_policy"]["mode"], "CONSENT_REQUIRED")

    def test_linux_checks_return_telemetry_and_findings(self):
        with patch.object(apolo_diagnostics.platform, "system", return_value="Linux"), \
             patch.object(apolo_diagnostics, "_linux_checks", return_value=(
                 [{"code": "TEST", "title": "Test", "detail": "evidence", "severity": "warning",
                   "source": "unit-test", "recommendation": "review", "status": "FOUND"}],
                 {"source": "test-procfs", "cpu": {"utilization_percent": 1.0}}
             )):
            report = apolo_diagnostics.run_diagnostics()
        self.assertEqual(report["summary"]["found"], 1)
        self.assertEqual(report["sensors"]["telemetry"]["source"], "test-procfs")

    def test_repair_requires_explicit_confirmation(self):
        with patch.object(apolo_diagnostics.platform, "system", return_value="Windows"):
            with self.assertRaises(PermissionError):
                apolo_diagnostics.run_windows_system_file_repair(False)

    def test_repair_is_not_available_on_other_platforms(self):
        with patch.object(apolo_diagnostics.platform, "system", return_value="Linux"):
            with self.assertRaises(RuntimeError):
                apolo_diagnostics.run_windows_system_file_repair(True)


if __name__ == "__main__":
    unittest.main()
