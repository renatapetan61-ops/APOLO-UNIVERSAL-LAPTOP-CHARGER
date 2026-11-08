import json

print(json.dumps({
    "protocol": "apolo-bms-telemetry/1",
    "sensor": "pack_temperature",
    "value": 25.0,
    "unit": "degC",
    "source_type": "SIMULATED",
    "source_id": "python-virtual-sensor",
    "timestamp_ms": 0,
    "hardware_backed": False,
    "output_authorized": False,
}, separators=(",", ":")))
