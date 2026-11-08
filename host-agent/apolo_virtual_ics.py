"""Four independently executable APOLO virtual controller modules.

All inputs are software observations from the host OS. They are not physical
sensors and cannot measure voltage/current/temperature without a real interface.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import platform


@dataclass(frozen=True)
class VirtualSensorObservation:
    name: str
    value: str
    source: str
    origin: str = "HOST_OS"
    observed_at: str = ""


class VirtualSensorEngine:
    def collect(self, findings: list[dict]) -> list[VirtualSensorObservation]:
        now = datetime.now(timezone.utc).isoformat()
        observations = [
            VirtualSensorObservation("host_os", platform.system(), "platform.system()", observed_at=now),
            VirtualSensorObservation("host_release", platform.release(), "platform.release()", observed_at=now),
            VirtualSensorObservation("finding_count", str(len(findings)), "APOLO diagnostic engine", observed_at=now),
        ]
        for finding in findings:
            observations.append(VirtualSensorObservation(
                "diagnostic_finding", str(finding.get("code", "UNKNOWN")),
                str(finding.get("source", "unknown")), observed_at=now
            ))
        return observations


class ApoloBmsIc:
    chip_id = "APOLO-BMS-IC"

    def execute(self, observations: list[VirtualSensorObservation]) -> dict:
        battery_items = [o for o in observations if "battery" in o.name.lower()]
        return {"id": self.chip_id, "state": "EXECUTED",
                "processed_observations": len(battery_items),
                "result": "NO_BATTERY_SENSOR_CHANNEL_EXPOSED" if not battery_items else "BATTERY_EVIDENCE_RECEIVED",
                "notes": ["Não estima tensão, corrente, temperatura nem SoC sem dados fornecidos por sensores/controladores reais."]}


class ApoloChargeIc:
    chip_id = "APOLO-CHARGE-IC"

    def execute(self, observations: list[VirtualSensorObservation]) -> dict:
        power_items = [o for o in observations if any(x in o.name.lower() for x in ("power", "adapter", "charge"))]
        return {"id": self.chip_id, "state": "EXECUTED",
                "processed_observations": len(power_items),
                "result": "POWER_TELEMETRY_NOT_EXPOSED" if not power_items else "POWER_EVIDENCE_RECEIVED",
                "notes": ["Analisa telemetria do host; não controla conversores nem habilita carregamento."]}


class ApoloSafetyIc:
    chip_id = "APOLO-SAFETY-IC"

    def execute(self, observations: list[VirtualSensorObservation], findings: list[dict]) -> dict:
        severe = sum(1 for item in findings if item.get("severity") in ("critical", "high"))
        return {"id": self.chip_id, "state": "EXECUTED",
                "processed_observations": len(observations),
                "result": "REVIEW_REQUIRED" if severe else "NO_CRITICAL_FINDING_CONFIRMED",
                "notes": [f"{severe} achado(s) crítico(s)/alto(s) requerem revisão." if severe else "Nenhum achado crítico/alto foi confirmado pelas fontes consultadas.",
                          "Este controlador virtual não substitui proteção elétrica física."]}


class ApoloUsbPdIc:
    chip_id = "APOLO-USB-PD-IC"

    def execute(self, observations: list[VirtualSensorObservation]) -> dict:
        usb_items = [o for o in observations if "usb" in o.name.lower()]
        return {"id": self.chip_id, "state": "EXECUTED",
                "processed_observations": len(usb_items),
                "result": "PD_CONTRACT_NOT_AVAILABLE",
                "notes": ["O agente não negocia USB Power Delivery; apenas poderá analisar evidências USB disponibilizadas pelo host."]}


class ApoloVirtualIcRuntime:
    def __init__(self) -> None:
        self.sensors = VirtualSensorEngine()
        self.chips = (ApoloBmsIc(), ApoloChargeIc(), ApoloSafetyIc(), ApoloUsbPdIc())

    def execute(self, findings: list[dict]) -> dict:
        observations = self.sensors.collect(findings)
        results = []
        for chip in self.chips:
            if isinstance(chip, ApoloSafetyIc):
                results.append(chip.execute(observations, findings))
            else:
                results.append(chip.execute(observations))
        return {
            "runtime": "APOLO-VIRTUAL-IC-RUNTIME/1",
            "sensor_mode": "VIRTUAL_SOFTWARE_OBSERVATIONS",
            "observation_count": len(observations),
            "physical_sensor_measurements": False,
            "chips": results,
        }
