using System.Text.Json;

var payload = new {
    protocol = "apolo-bms-telemetry/1",
    sensor = "pack_temperature",
    value = 25.0,
    unit = "degC",
    source_type = "SIMULATED",
    source_id = "csharp-virtual-sensor",
    timestamp_ms = 0,
    hardware_backed = false,
    output_authorized = false
};
Console.WriteLine(JsonSerializer.Serialize(payload));
