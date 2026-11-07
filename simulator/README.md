# APOLO Simulator

The Android app includes an in-process deterministic demonstration simulator:

- Normal — nominal illustrative telemetry.
- Warning — illustrative low state of charge and elevated temperature.
- Fault — illustrative critical state and output-blocked message.

All values are synthetic. They do not represent a real battery, cannot validate a BMS, and must not be used to select operating thresholds. The simulator does not communicate with or control hardware.

The read-only v1 telemetry decoder has unit tests under android/app/src/test. A standalone hardware simulator/service and integration transport remain future work.
