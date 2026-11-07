# APOLO Telemetry Protocol — v1 draft

## Scope and safety

This is a read-only telemetry format for app/simulator integration. It is not a control protocol and must never command a charger, inverter, contactor, MOSFET, balancing circuit, or battery output. A communication timeout, malformed frame, stale sequence, or invalid sensor value means data is unavailable. Hardware protection must remain autonomous and independent of Android, Bluetooth, USB, and network services.

## Binary frame

All multi-byte integers are big-endian. Fixed size: 20 bytes.

| Offset | Size | Field | Encoding |
|---:|---:|---|---|
| 0 | 2 | Magic | ASCII AP (0x41 0x50) |
| 2 | 1 | Protocol version | 0x01 |
| 3 | 2 | Sequence | Unsigned 16-bit, wraps modulo 65536 |
| 5 | 4 | Pack voltage | Unsigned millivolts |
| 9 | 4 | Pack current | Signed two's-complement milliamps |
| 13 | 2 | Temperature | Signed two's-complement centi-degrees Celsius |
| 15 | 1 | State of charge | Integer percent, 0–100 |
| 16 | 2 | Status flags | Reserved in v1 |
| 18 | 2 | CRC | CRC-16/CCITT-FALSE over bytes 0–17 |

CRC: polynomial 0x1021, initial 0xFFFF, no reflection, xor-out 0x0000.

## Decoder validation

The Android decoder rejects wrong frame size, magic, version, CRC, SoC outside 0–100%, voltage above 100 V, current outside ±200 A, and temperature outside −40 to 125 °C. These are parser sanity limits, not pack operating limits or safety thresholds.

## Before hardware integration

A future USB or BLE transport must add device identity, authenticated pairing where appropriate, explicit protocol version negotiation, sequence-gap detection, receive timestamps, stale-data timeout, bounded buffering, and disconnect handling. No transport has been enabled in this release. A laptop USB-A port must never be treated as a charging input.
