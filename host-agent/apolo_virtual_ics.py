"""Four independently executable APOLO virtual controller modules.

The controllers receive normalized, provenance-tagged OS observations. They are
software only: they do not drive electrical actuators or replace physical sensors.
"""
from __future__ import annotations

from dataclasses import dataclass
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
    def __init__(self) -> None:
        self.contract_stats = {"accepted": 0, "rejected": 0}

    @staticmethod
    def _valid_contract(item: VirtualSensorObservation) -> bool:
        """Runtime gate matching the APOLO1 six-field multilingual contract."""
        fields = (item.name, item.value, item.origin, item.source, item.observed_at)
        if not all(isinstance(value, str) and value.strip() for value in fields):
            return False
        if item.origin not in {"HOST_OS", "PHYSICAL_INTERFACE"}:
            return False
        if any("\t" in value or "\n" in value or "\r" in value for value in fields):
            return False
        try:
            observed = datetime.fromisoformat(item.observed_at.replace("Z", "+00:00"))
            return observed.timestamp() > 0
        except (ValueError, OverflowError):
            return False

    def collect(self, findings: list[dict], telemetry: dict | None = None) -> list[VirtualSensorObservation]:
        now = datetime.now(timezone.utc).isoformat()
        observations = [
            VirtualSensorObservation("host_os", platform.system(), "platform.system()", observed_at=now),
            VirtualSensorObservation("host_release", platform.release(), "platform.release()", observed_at=now),
            VirtualSensorObservation("finding_count", str(len(findings)), "APOLO diagnostic engine", observed_at=now),
        ]

        def flatten(value, prefix: str, source: str):
            if isinstance(value, dict):
                for key, child in value.items():
                    flatten(child, f"{prefix}.{key}" if prefix else str(key), source)
            elif isinstance(value, (list, tuple)):
                for index, child in enumerate(value):
                    flatten(child, f"{prefix}[{index}]", source)
            elif value is not None and isinstance(value, (str, int, float, bool)):
                observations.append(VirtualSensorObservation(
                    prefix, str(value), source, origin="HOST_OS", observed_at=now
                ))

        if telemetry:
            source = str(telemetry.get("source", "host operating system"))
            flatten(telemetry, "telemetry", source)
        for finding in findings:
            observations.append(VirtualSensorObservation(
                "diagnostic_finding", str(finding.get("code", "UNKNOWN")),
                str(finding.get("source", "unknown")), observed_at=now
            ))
        accepted = [item for item in observations if self._valid_contract(item)]
        self.contract_stats = {"accepted": len(accepted),
                               "rejected": len(observations) - len(accepted)}
        return accepted


class ApoloBmsIc:
    chip_id = "APOLO-BMS-IC"

    def execute(self, observations: list[VirtualSensorObservation]) -> dict:
        items = [o for o in observations if "battery" in o.name.lower()]
        return {"id": self.chip_id, "state": "EXECUTED",
                "processed_observations": len(items),
                "result": "BATTERY_EVIDENCE_RECEIVED" if items else "NO_BATTERY_SENSOR_CHANNEL_EXPOSED",
                "notes": ["Avalia somente dados de bateria realmente expostos pelo sistema operacional.",
                          "Não estima tensão de célula, corrente, temperatura ou SoC sem fonte correspondente."]}


class ApoloChargeIc:
    chip_id = "APOLO-CHARGE-IC"

    def execute(self, observations: list[VirtualSensorObservation]) -> dict:
        items = [o for o in observations if any(x in o.name.lower() for x in ("power", "adapter", "charge"))]
        return {"id": self.chip_id, "state": "EXECUTED",
                "processed_observations": len(items),
                "result": "POWER_TELEMETRY_RECEIVED" if items else "POWER_TELEMETRY_NOT_EXPOSED",
                "notes": ["Analisa telemetria do host; não controla conversores nem habilita carregamento."]}


class ApoloSafetyIc:
    chip_id = "APOLO-SAFETY-IC"

    def execute(self, observations: list[VirtualSensorObservation], findings: list[dict]) -> dict:
        severe = sum(1 for item in findings if item.get("severity") in ("critical", "high"))
        return {"id": self.chip_id, "state": "EXECUTED",
                "processed_observations": len(observations),
                "result": "REVIEW_REQUIRED" if severe else "NO_CRITICAL_FINDING_CONFIRMED",
                "notes": [f"{severe} achado(s) crítico(s)/alto(s) requerem revisão." if severe else
                          "Nenhum achado crítico/alto foi confirmado pelas fontes consultadas.",
                          "Este controlador virtual não substitui proteção elétrica física."]}


class ApoloUsbPdIc:
    chip_id = "APOLO-USB-PD-IC"

    def execute(self, observations: list[VirtualSensorObservation]) -> dict:
        items = [o for o in observations if "usb" in o.name.lower() or "typec" in o.name.lower()]
        return {"id": self.chip_id, "state": "EXECUTED",
                "processed_observations": len(items),
                "result": "USB_HOST_EVIDENCE_RECEIVED" if items else "USB_PD_CONTRACT_NOT_AVAILABLE",
                "notes": ["Analisa inventário USB exposto pelo host; não negocia nem confirma contrato USB Power Delivery."]}


class ApoloVirtualIcRuntime:
    def __init__(self) -> None:
        self.sensors = VirtualSensorEngine()
        self.chips = (ApoloBmsIc(), ApoloChargeIc(), ApoloSafetyIc(), ApoloUsbPdIc())

    def execute(self, findings: list[dict], telemetry: dict | None = None) -> dict:
        observations = self.sensors.collect(findings, telemetry)
        results = []
        for chip in self.chips:
            if isinstance(chip, ApoloSafetyIc):
                results.append(chip.execute(observations, findings))
            else:
                results.append(chip.execute(observations))
        return {
            "runtime": "APOLO-VIRTUAL-IC-RUNTIME/2",
            "sensor_mode": "VIRTUAL_SOFTWARE_OBSERVATIONS",
            "observation_count": len(observations),
            "observation_contract": {
                "protocol": "APOLO1",
                "runtime_validator": "Python canonical gate",
                "accepted": self.sensors.contract_stats["accepted"],
                "rejected": self.sensors.contract_stats["rejected"],
                "multilingual_adapters": "15-language compatibility validators are compiled/tested in CI; they are not all launched as host processes",
            },
            "physical_sensor_measurements": False,
            "chips": results,
        }
