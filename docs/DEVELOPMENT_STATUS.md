# APOLO Charger — Development Status

## Implemented in software

- Android application shell using Kotlin and Jetpack Compose.
- Five navigation areas: dashboard, battery, BMS, connectivity, and about.
- Local Android simulator with Normal, Warning, and Fault scenarios.
- Standalone Python simulator that generates protocol v1 telemetry frames for all three scenarios.
- Synthetic values visibly identified as simulated, with outputs explicitly blocked.
- Read-only telemetry frame decoder with length, magic, version, CRC, and sanity checks.
- Kotlin unit tests for valid frames and malformed/corrupted frames.
- Python tests for frame size, CRC check value, scenario safety flag, and sequence validation.
- GitHub Actions runs Python and Android unit tests, assembles the debug APK, and uploads the APK as a 14-day artifact.

## Not implemented or validated

- The internal BMS software model and Power Module software policy exist in Kotlin, but no physical Power Module, battery pack, sensors, switching/protection components, or power converters are connected.
- No USB serial/accessory or Bluetooth LE hardware transport is implemented.
- The internal BMS software core includes profile validation, telemetry freshness checks, cell-voltage/current/temperature status evaluation, and a basic coulomb-counting SoC estimate.
- The Power Module software model evaluates laptop output requests but intentionally denies all real hardware activation.
- No embedded firmware, physical sensing, or hardware control is implemented; the current BMS is a software domain model, not an operating battery controller.
- No charging output, USB-C PD negotiation, laptop connector detection, or power-control function is available.
- No APK has been tested on a physical Android device.
- No electrical, thermal, EMC, transport, battery, or product-safety certification has been completed.

## Release gate

Do not enable or connect power outputs until qualified engineers complete the electrical design, independent protection architecture, fault-injection testing, thermal testing, enclosure review, and applicable certification. Android software is monitoring/UI only and must never be the primary safety layer.
