# APOLO BMS Virtual Sensor Adapters

These seven programs are **test fixtures**, not hardware drivers. Each emits the same JSON contract:
- protocol: apolo-bms-telemetry/1
- source_type: SIMULATED
- hardware_backed: false
- output_authorized: false

A real sensor adapter must be separately implemented, authenticated, calibrated, timestamped, range-checked, and reviewed. Never convert a virtual reading into a physical measurement or an output authorization.

Run examples:
- Rust: rustc rust/src/main.rs -o /tmp/apolo-rust && /tmp/apolo-rust
- Python: python python/sensor.py
- Go: go run go/main.go
- Ruby: ruby ruby/sensor.rb
- C: cc c/sensor.c -o /tmp/apolo-c && /tmp/apolo-c
- C++: c++ -std=c++17 cpp/sensor.cpp -o /tmp/apolo-cpp && /tmp/apolo-cpp
- C#: dotnet run --project csharp
