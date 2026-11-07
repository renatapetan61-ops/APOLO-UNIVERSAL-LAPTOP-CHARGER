# APOLO Internal BMS and Power Module Software Architecture

## Product interpretation

The APOLO BMS is an original software subsystem inside the APOLO Power Module. It is not intended to be a separately purchased BMS product or a separate user-facing board. The Android app is its companion interface.

The software implementation is being developed from zero in the Android/Kotlin codebase. It contains:
- battery profile model;
- sensor snapshot model;
- telemetry freshness and plausibility checks;
- normal, warning, critical, invalid-data and unconfigured states;
- minimum/maximum cell-voltage evaluation using an explicitly supplied engineering profile;
- temperature and current status evaluation;
- a basic coulomb-counting SoC estimator;
- fail-closed software output decision model.

## Important engineering boundary

Software cannot physically interrupt battery current. A real battery pack still requires independent electrical protection, appropriately rated switching/protection components, fusing, temperature sensing and validated electrical design. These are not a second BMS product; they are physical safety mechanisms required by the battery itself. The internal APOLO BMS software supervises and reports but cannot replace them.

No universal cell limits are hard-coded as production values. Limits must be selected and validated for the exact cell model, pack topology, operating conditions and applicable standards by qualified battery engineers.

## Power Module software

The software model describes a conceptual 1,500 Wh LiFePO4 module and up to 240 W output target. It can evaluate requested output profiles but denies all physical output activation in this release. USB-A data is never treated as a laptop power output.

## Current implementation status

- Internal BMS domain logic: implemented as software model.
- Telemetry validation and fail-closed status assessment: implemented.
- SoC coulomb-counting estimate: implemented as a basic software estimate, not calibrated gauge.
- Power Module profile and output request policy: implemented in software.
- Physical battery, sensors, switching, conversion, connectors and enclosure: not built.
- Hardware communication and real telemetry: not implemented.
- Product-level safety validation and certification: not completed.

The Android app and these software modules are not yet capable of charging a laptop. They are the software foundation for a future validated Power Module.
