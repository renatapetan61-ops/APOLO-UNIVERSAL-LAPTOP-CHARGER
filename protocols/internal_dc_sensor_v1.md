# APOLO Internal DC Sensor Telemetry — Protocol v1 (Draft)

**Status:** message contract only. No physical sensor transport is implemented.

## Trust boundary
The host agent must not treat arbitrary JSON or USB descriptors as an electrical measurement. A future sensor controller must authenticate its identity and message integrity using a provisioned device key. Keys must not be embedded in the Android APK or source repository.

## Message fields
- protocol: apolo-dc-sensor/1
- sensor_id: provisioned hardware identity
- firmware_version: immutable firmware build identifier
- sequence: monotonically increasing sample counter
- sample_time_ms: monotonic timestamp from controller boot
- raw_adc: unsigned raw conversion count
- signed_voltage_mv: signed calibrated differential voltage in millivolts, or null
- polarity: CENTER_POSITIVE, CENTER_NEGATIVE, NO_INPUT, AMBIGUOUS, OUT_OF_RANGE, STALE, SENSOR_FAULT, or CALIBRATION_INVALID
- calibration_id: approved calibration revision
- self_test: PASS or a fault code
- quality: VALID or a fault code
- auth_tag: message authentication tag from the provisioned device key

## Validation rules
1. Reject unknown protocol versions and sensor identities.
2. Verify authentication before using measurement fields.
3. Reject repeated/decreasing sequence numbers.
4. Reject stale timestamps, invalid calibration IDs, failed self-tests, and out-of-range raw values.
5. Require signed voltage and polarity classification to agree.
6. Treat zero/near-zero input as NO_INPUT, never as evidence of intended adapter polarity.
7. Treat missing, malformed, unauthenticated, or contradictory data as unavailable.
8. Protocol is read-only; it has no commands to enable, disable, or control laptop power.

## Illustrative, unauthenticated example
    protocol: apolo-dc-sensor/1
    sensor_id: UNPROVISIONED
    firmware_version: 0.0.0-dev
    sequence: 1
    sample_time_ms: 1000
    raw_adc: 0
    signed_voltage_mv: null
    polarity: NO_INPUT
    calibration_id: NONE
    self_test: NOT_CALIBRATED
    quality: CALIBRATION_INVALID
    auth_tag: null

This is not a valid authenticated measurement and must be rejected in production.
