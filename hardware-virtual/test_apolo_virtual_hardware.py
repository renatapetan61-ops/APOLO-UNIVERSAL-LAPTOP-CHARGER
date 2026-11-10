import unittest
from apolo_virtual_hardware import ApoloVirtualHardwareBoard, Register, VirtualI2CBus, VirtualI2CDevice, VirtualBMS, VirtualUsbPdController

class VirtualHardwareTests(unittest.TestCase):
    def test_i2c_enumeration(self):
        self.assertEqual([x["address"] for x in ApoloVirtualHardwareBoard().i2c.scan()],[0x40,0x41])
    def test_i2c_collision_rejected(self):
        bus=VirtualI2CBus(); bus.attach(VirtualI2CDevice(0x40,"a"))
        with self.assertRaises(ValueError): bus.attach(VirtualI2CDevice(0x40,"b"))
    def test_read_only_register(self):
        d=VirtualI2CDevice(0x40,"x",{0:Register(0,"STATUS",1)})
        with self.assertRaises(PermissionError): d.write(0,2)
    def test_bms_overtemperature(self):
        b=VirtualBMS(); b.update(temperatures_c=[25]*15+[61])
        self.assertIn("CELL_OVERTEMPERATURE",b.evaluate()["faults"])
    def test_safety_latches_and_never_enables(self):
        board=ApoloVirtualHardwareBoard(); report=board.safety.evaluate(board.bms.evaluate(),bus_voltage_v=61)
        self.assertIn("BUS_OVERVOLTAGE",report["latched_faults"]); self.assertFalse(report["output_enable"])
    def test_power_stage_is_non_energizing(self):
        r=ApoloVirtualHardwareBoard().power_stage.calculate(input_voltage_v=48,target_voltage_v=19,load_current_a=3.42)
        self.assertEqual(r["hypothetical_power_w"],64.98); self.assertFalse(r["switching"]); self.assertFalse(r["output_enable"])
    def test_pd_is_simulated_only(self):
        pd=VirtualUsbPdController()
        r=pd.negotiate(requested_voltage_v=20,requested_current_a=3)
        self.assertEqual(r["state"],"SIMULATED_CONTRACT"); self.assertFalse(r["physical_negotiation"])
        self.assertEqual(pd.negotiate(requested_voltage_v=28,requested_current_a=3)["state"],"REJECTED")
    def test_snapshot_labels_emulation(self):
        r=ApoloVirtualHardwareBoard().snapshot()
        self.assertFalse(r["physical_hardware_present"]); self.assertFalse(r["power_output_enabled"])

if __name__=="__main__": unittest.main()
