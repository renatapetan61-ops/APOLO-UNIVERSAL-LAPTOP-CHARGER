package main

import "encoding/json"
import "os"

func main() {
    payload := map[string]interface{}{
        "protocol": "apolo-bms-telemetry/1",
        "sensor": "pack_temperature",
        "value": 25.0,
        "unit": "degC",
        "source_type": "SIMULATED",
        "source_id": "go-virtual-sensor",
        "timestamp_ms": 0,
        "hardware_backed": false,
        "output_authorized": false,
    }
    _ = json.NewEncoder(os.Stdout).Encode(payload)
}
