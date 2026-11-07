"""Read-only APOLO telemetry simulator; never connects to power hardware."""
from __future__ import annotations

import argparse
import json
import struct
from dataclasses import asdict, dataclass

MAGIC = b"AP"
PROTOCOL_VERSION = 1


@dataclass(frozen=True)
class Scenario:
    name: str
    voltage_mv: int
    current_ma: int
    temperature_centi_c: int
    state_of_charge: int
    status_flags: int
    status: str


SCENARIOS = {
    "normal": Scenario("normal", 51_200, 0, 2_500, 78, 0, "normal_demo"),
    "warning": Scenario("warning", 48_000, 0, 4_800, 18, 1, "warning_demo"),
    "fault": Scenario("fault", 44_000, 0, 6_200, 8, 3, "fault_demo_output_locked"),
}


def crc16_ccitt(data: bytes) -> int:
    """CRC-16/CCITT-FALSE: poly 0x1021, init 0xFFFF, xorout 0."""
    crc = 0xFFFF
    for value in data:
        crc ^= value << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if crc & 0x8000 else (crc << 1) & 0xFFFF
    return crc


def encode_frame(scenario: Scenario, sequence: int = 0) -> bytes:
    if not 0 <= sequence <= 0xFFFF:
        raise ValueError("sequence must be an unsigned 16-bit integer")
    if not 0 <= scenario.state_of_charge <= 100:
        raise ValueError("SoC must be between 0 and 100")
    payload = struct.pack(
        ">2sBHIihBH",
        MAGIC,
        PROTOCOL_VERSION,
        sequence,
        scenario.voltage_mv,
        scenario.current_ma,
        scenario.temperature_centi_c,
        scenario.state_of_charge,
        scenario.status_flags,
    )
    return payload + struct.pack(">H", crc16_ccitt(payload))


def scenario_report(name: str, sequence: int = 0) -> dict:
    scenario = SCENARIOS[name]
    return {
        "source": "SIMULATOR",
        "scenario": asdict(scenario),
        "sequence": sequence,
        "frame_hex": encode_frame(scenario, sequence).hex(),
        "power_output_enabled": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", choices=sorted(SCENARIOS), default="normal")
    parser.add_argument("--sequence", type=int, default=0)
    args = parser.parse_args()
    print(json.dumps(scenario_report(args.scenario, args.sequence), indent=2))


if __name__ == "__main__":
    main()
