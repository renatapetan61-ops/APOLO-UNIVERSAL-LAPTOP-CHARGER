require "json"

puts JSON.generate({
  protocol: "apolo-bms-telemetry/1",
  sensor: "pack_temperature",
  value: 25.0,
  unit: "degC",
  source_type: "SIMULATED",
  source_id: "ruby-virtual-sensor",
  timestamp_ms: 0,
  hardware_backed: false,
  output_authorized: false
})
