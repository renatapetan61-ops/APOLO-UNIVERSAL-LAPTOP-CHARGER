"""APOLO hardware-emulation layer. Synthetic only; never energizes outputs."""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

class DeviceState(str, Enum):
    READY="READY"
    FAULT_LATCHED="FAULT_LATCHED"

@dataclass
class Register:
    address: int
    name: str
    value: int = 0
    writable: bool = False
    mask: int = 0xFFFFFFFF
    def write(self, value: int) -> None:
        if not self.writable:
            raise PermissionError(f"register {self.name} is read-only")
        if value < 0 or value > self.mask:
            raise ValueError("value outside register mask")
        self.value = value

@dataclass
class VirtualI2CDevice:
    address: int
    name: str
    registers: dict[int, Register] = field(default_factory=dict)
    def read(self, register: int) -> int:
        if register not in self.registers: raise KeyError(register)
        return self.registers[register].value
    def write(self, register: int, value: int) -> None:
        if register not in self.registers: raise KeyError(register)
        self.registers[register].write(value)

class VirtualI2CBus:
    def __init__(self): self.devices = {}
    def attach(self, device):
        if not 0x08 <= device.address <= 0x77: raise ValueError("invalid 7-bit I2C address")
        if device.address in self.devices: raise ValueError("I2C address collision")
        self.devices[device.address] = device
    def scan(self):
        return [{"address": a, "name": d.name} for a,d in sorted(self.devices.items())]

class VirtualBMS:
    """Synthetic 16S LiFePO4 training model; not a battery monitor."""
    def __init__(self):
        self.voltages_v = [3.2] * 16
        self.temperatures_c = [25.0] * 16
        self.current_a = 0.0
    def update(self, *, voltages_v=None, temperatures_c=None, current_a=None):
        if voltages_v is not None:
            if len(voltages_v) != 16: raise ValueError("expected 16 cell voltages")
            self.voltages_v = [float(v) for v in voltages_v]
        if temperatures_c is not None:
            if len(temperatures_c) != 16: raise ValueError("expected 16 temperatures")
            self.temperatures_c = [float(v) for v in temperatures_c]
        if current_a is not None: self.current_a = float(current_a)
    def evaluate(self):
        faults = []
        if any(v < 2.50 or v > 3.65 for v in self.voltages_v): faults.append("CELL_VOLTAGE_OUT_OF_MODEL_RANGE")
        if any(t >= 60 for t in self.temperatures_c): faults.append("CELL_OVERTEMPERATURE")
        if abs(self.current_a) > 100: faults.append("CURRENT_LIMIT_EXCEEDED")
        return {"device":"APOLO-VIRTUAL-BMS-16S",
                "state":DeviceState.FAULT_LATCHED.value if faults else DeviceState.READY.value,
                "cell_count":16,"cell_voltages_v":self.voltages_v,
                "pack_voltage_v":round(sum(self.voltages_v),4),"current_a":self.current_a,
                "max_temperature_c":max(self.temperatures_c),"faults":faults,
                "data_origin":"SYNTHETIC_SIMULATION"}

class VirtualSafetyController:
    """Latched software safety model; output-enable is hard-disabled."""
    def __init__(self): self.latched_faults = []
    def evaluate(self, bms_report, *, bus_voltage_v=0.0, output_current_a=0.0,
                 board_temperature_c=25.0, injected_faults=None):
        faults = list(bms_report.get("faults", []))
        if bus_voltage_v > 60: faults.append("BUS_OVERVOLTAGE")
        if output_current_a > 15: faults.append("OUTPUT_OVERCURRENT")
        if board_temperature_c >= 85: faults.append("BOARD_OVERTEMPERATURE")
        self.latched_faults = sorted(set(self.latched_faults + faults + (injected_faults or [])))
        return {"device":"APOLO-VIRTUAL-SAFETY",
                "state":DeviceState.FAULT_LATCHED.value if self.latched_faults else DeviceState.READY.value,
                "latched_faults":self.latched_faults,"output_enable":False,
                "output_inhibit_reason":"SIMULATOR_NEVER_ENERGIZES_OUTPUT",
                "reset_required":bool(self.latched_faults)}

class VirtualPowerStage:
    """Computes a hypothetical operating point; no switching or voltage output."""
    def calculate(self, *, input_voltage_v, target_voltage_v, load_current_a):
        if min(input_voltage_v,target_voltage_v,load_current_a) < 0: raise ValueError("negative input")
        return {"device":"APOLO-VIRTUAL-POWER-STAGE","input_voltage_v":input_voltage_v,
                "requested_output_voltage_v":target_voltage_v,
                "requested_load_current_a":load_current_a,
                "hypothetical_power_w":round(target_voltage_v*load_current_a,3),
                "switching":False,"output_enable":False,"data_origin":"CALCULATED_SIMULATION"}

class VirtualUsbPdController:
    """PD policy-engine model; no CC pins, PHY or physical negotiation."""
    SUPPORTED = {5:(0.5,3.0),9:(0.5,3.0),15:(0.5,3.0),20:(0.5,5.0)}
    def negotiate(self, *, requested_voltage_v, requested_current_a):
        limits = self.SUPPORTED.get(requested_voltage_v)
        if limits is None or not limits[0] <= requested_current_a <= limits[1]:
            return {"device":"APOLO-VIRTUAL-USB-PD","state":"REJECTED","contract":None,"physical_negotiation":False}
        return {"device":"APOLO-VIRTUAL-USB-PD","state":"SIMULATED_CONTRACT",
                "contract":{"voltage_v":requested_voltage_v,"current_a":requested_current_a,
                            "power_w":requested_voltage_v*requested_current_a},
                "physical_negotiation":False,"data_origin":"SYNTHETIC_SIMULATION"}

class ApoloVirtualHardwareBoard:
    def __init__(self):
        self.i2c = VirtualI2CBus()
        self.i2c.attach(VirtualI2CDevice(0x40,"APOLO-VIRTUAL-BMS",{
            0:Register(0,"DEVICE_ID",0xA016),1:Register(1,"STATUS",0)}))
        self.i2c.attach(VirtualI2CDevice(0x41,"APOLO-VIRTUAL-SAFETY",{
            0:Register(0,"DEVICE_ID",0x5AFE),1:Register(1,"FAULT_FLAGS",0)}))
        self.bms,self.safety,self.power_stage,self.usb_pd = VirtualBMS(),VirtualSafetyController(),VirtualPowerStage(),VirtualUsbPdController()
    def snapshot(self):
        bms = self.bms.evaluate()
        return {"board":"APOLO-VIRTUAL-HARDWARE-BOARD/1","mode":"HARDWARE_EMULATION",
                "bus":{"type":"I2C","devices":self.i2c.scan()},"bms":bms,
                "safety":self.safety.evaluate(bms),"power_output_enabled":False,
                "physical_hardware_present":False,
                "warning":"Emulation only: no physical measurement, switching or power output."}
