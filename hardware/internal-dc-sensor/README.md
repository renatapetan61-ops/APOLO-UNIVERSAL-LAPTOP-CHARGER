# APOLO Internal DC Jack Sensor — Hardware Design Package

**Status: engineering specification / prototype not built. Do not manufacture or connect to a laptop yet.**

## Purpose
Provide a physically measured, read-only observation of voltage present across the laptop DC input contacts. A dedicated embedded controller reports signed voltage to the APOLO host agent. Android is only the display and policy client.

## Target integration
Initial target: Positivo Unique TV S2065. Exact motherboard part number, PCB revision, DC jack pinout, input protection topology, and test points are **not verified**. This package intentionally defines no solder point, connector pin number, resistor value, PCB footprint, or installation procedure. Design must be based on the exact board revision and reliable service documentation. Never connect by trial and error or insert the sensor in series with the laptop power path.

## Functional block architecture
Laptop DC jack contacts (parallel observation only) → protected high-impedance differential front-end → independent over-voltage protection → ADC with known reference and diagnostics → embedded MCU / secure identity → isolated communication interface → APOLO host agent → Android app.

## Measurement semantics
- Measure signed voltage between two verified DC input nets.
- Report raw ADC counts, calibrated signed volts, sample timestamp, calibration revision, sensor identity, firmware version, self-test status, and measurement quality.
- Report NO_INPUT when differential voltage is below a validated threshold.
- Report AMBIGUOUS, STALE, OUT_OF_RANGE, SENSOR_FAULT, or CALIBRATION_INVALID as appropriate.
- Never infer intended adapter polarity when no voltage is present.
- Sensor is observational only; it must not switch, regulate, interrupt, or authorize laptop power.

## Safety requirements before schematic release
1. Confirm jack contacts and net names from the exact S2065 board revision and reliable service documentation.
2. Establish maximum normal and credible fault voltage, transients, ESD environment, ground relationship, and creepage/clearance constraints.
3. Select a measurement front-end whose input impedance and fault behavior cannot materially load or damage the laptop input.
4. Add independently validated input current limiting and over-voltage protection.
5. Ensure a single sensor failure cannot short the DC input, bridge contacts, or interrupt existing protection.
6. Validate galvanic isolation or document a safe common-ground strategy for communications.
7. Use watchdog, brownout handling, startup self-test, ADC reference diagnostics, and fail-silent behavior.
8. Test first on a current-limited isolated bench source and dummy load, never on the motherboard.
9. Require qualified engineering review of schematic, PCB, thermal behavior, EMC, and failure analysis before installation.

## What this package does not claim
- No physical sensor board fabricated or tested.
- No S2065 jack pinout or polarity confirmed.
- No actual laptop voltage measured.
- No firmware approved to drive a power switch.
- No software-only or USB-only method reads DC jack contacts.

## Planned hardware deliverables
Exact-board-revision net map; reviewed schematic and BOM; PCB layout with test points and isolation boundary; MCU firmware with authenticated messages; calibration fixture and record; bench validation and fault-injection report.
