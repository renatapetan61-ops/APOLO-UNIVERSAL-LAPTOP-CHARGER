# APOLO Charger — Development Status

## Implemented in software

- Android application shell using Kotlin and Jetpack Compose.
- Five navigation areas: dashboard, battery, BMS, connectivity, and about.
- Local deterministic simulator with Normal, Warning, and Fault scenarios.
- Synthetic values visibly identified as simulated, with outputs explicitly blocked.
- Read-only telemetry frame decoder with length, magic, version, CRC, and sanity checks.
- Unit tests for valid frames and malformed/corrupted frames.
- GitHub Actions workflow runs unit tests, assembles a debug APK, and uploads the APK as a 14-day artifact.

## Not implemented or validated

- No physical Power Module, battery pack, BMS board, sensors, contactors, fuse assembly, or power converters are connected.
- No USB serial/accessory or Bluetooth LE hardware transport is implemented.
- No firmware for a real BMS or power stage is included.
- No charging output, USB-C PD negotiation, laptop connector detection, or power-control function is available.
- No APK has been tested on a physical Android device.
- No electrical, thermal, EMC, transport, battery, or product-safety certification has been completed.

## Release gate

Do not enable or connect power outputs until qualified engineers complete the electrical design, independent protection architecture, fault-injection testing, thermal testing, enclosure review, and applicable certification. Android software is monitoring/UI only and must never be the primary safety layer.
