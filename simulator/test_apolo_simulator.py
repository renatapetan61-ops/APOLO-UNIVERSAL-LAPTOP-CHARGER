import unittest

from apolo_simulator import SCENARIOS, crc16_ccitt, encode_frame, scenario_report


class SimulatorTests(unittest.TestCase):
    def test_crc_known_check_value(self):
        self.assertEqual(crc16_ccitt(b"123456789"), 0x29B1)

    def test_all_scenarios_emit_twenty_byte_frames(self):
        for scenario in SCENARIOS.values():
            with self.subTest(scenario=scenario.name):
                frame = encode_frame(scenario, 42)
                self.assertEqual(len(frame), 20)
                self.assertEqual(frame[:3], b"AP\x01")
                self.assertEqual(int.from_bytes(frame[18:], "big"), crc16_ccitt(frame[:18]))

    def test_fault_scenario_never_enables_output(self):
        report = scenario_report("fault", 65535)
        self.assertFalse(report["power_output_enabled"])
        self.assertEqual(report["sequence"], 65535)
        self.assertEqual(report["scenario"]["status"], "fault_demo_output_locked")

    def test_rejects_invalid_sequence(self):
        with self.assertRaises(ValueError):
            encode_frame(SCENARIOS["normal"], -1)


if __name__ == "__main__":
    unittest.main()
