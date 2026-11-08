# APOLO Internal Sensor and Embedded Agent Roadmap

## Goal
Move DC-jack polarity detection from OS-only assumptions to genuine physical measurement performed by an embedded sensor controller in a professionally designed internal hardware assembly.

## Components and responsibilities

| Component | Responsibility | Current status |
|---|---|---|
| DC jack sensor front-end | Observe signed voltage across verified DC input contacts | Not built |
| Embedded controller | Sample ADC, self-test, timestamp, classify and authenticate | Not built |
| Sensor communication link | Deliver authenticated read-only telemetry | Not implemented |
| Host agent | Collect OS inventory and consume authenticated sensor telemetry | OS inventory implemented; sensor link pending |
| Android app | Display inventory, measured voltage, polarity and faults | Sensor integration pending |
| Power Module/BMS | Enforce independent battery/output protections | Software model only; no real output authorization |

## Installation model
Firmware runs on a dedicated microcontroller in the sensor assembly. It is not installed inside passive connector contacts or individual motherboard components. The physical sensor connects in parallel to verified DC input nets using a reviewed, protected measurement interface. The controller communicates with the host agent over a dedicated authenticated interface.

If board-level integration is unsafe or the exact motherboard revision cannot be verified, use an external inline measurement adapter designed for the connector instead of modifying the motherboard.

## Staged implementation
1. Identify exact motherboard model and PCB revision; obtain boardview/schematic/service documentation.
2. Verify connector nets and electrical envelope without guessing.
3. Complete schematic, BOM, PCB, isolation analysis and failure-mode review.
4. Build standalone sensor prototype and validate it on a current-limited bench source.
5. Implement MCU firmware, calibration, secure provisioning and authenticated telemetry.
6. Extend host agent to consume only authenticated sensor messages.
7. Extend Android UI to display actual signed voltage and quality state.
8. Validate on a sacrificial test fixture before any laptop installation.

## Fail-closed behavior
Until a validated sensor is physically connected and calibrated, display UNMEASURED. With no input voltage display NO_INPUT, not guessed polarity. Any authentication, calibration, freshness, range, or self-test failure must display a fault and must never authorize APOLO power output.

## S2065-specific blocker
The project knows the adapter target rating reported by the owner (19 V, 3.42 A), but does not have verified motherboard revision, jack pinout, schematic, boardview, or a physical measurement. Adapter rating is not proof of DC jack polarity or connector dimensions.
