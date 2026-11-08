# USB host-agent bridge (experimental, read-only)

## What this adds

`apolo_host_agent.py` is a small standard-library Python companion for a
Windows, Linux, or macOS laptop. It exposes operating-system identity metadata
on loopback at `127.0.0.1:8765/v1/identity`. The intended cable workflow is:

1. The owner enables Android USB debugging and authorizes their own phone.
2. The owner starts the host agent on the laptop.
3. The owner runs `adb reverse tcp:8765 tcp:8765` on the laptop.
4. An Android-side APOLO client may query `http://127.0.0.1:8765/v1/identity`.

This uses a normal USB data cable as a transport only after the user enables
and authorizes ADB. A cable alone does not grant an Android app access to the
laptop's host-side USB controllers or arbitrary hardware registers. The host
agent must be installed and running; it is not automatically present.

## Critical electrical boundary

The agent intentionally returns:

- `dc_jack_voltage_v: null`
- `dc_jack_polarity: "UNMEASURED"`
- `dc_measurement_available: false`
- `charging_authorized: false`

Laptop operating systems generally do not expose a physical DC barrel-jack
center-pin-to-sleeve voltage measurement or its polarity. AC-adapter-present
status, battery state, model strings, USB VID/PID, BIOS data, and vendor
specifications are not a live electrical measurement of the jack.

No software-only technique over a common USB cable can safely or universally
measure those contacts. To obtain a real measurement, the APOLO Power Module
needs a purpose-designed, electrically isolated, current-limited measurement
front end connected to the relevant DC contacts, with protection against
miswiring, transients, and accidental output enable. That hardware must be
engineered and validated before any power output is enabled.

## Security

- The server binds only to loopback; do not expose it to a LAN or public network.
- The endpoint is read-only and must never authorize charging.
- OS-reported model strings are untrusted claims, not cryptographic proof.
- A future authenticated protocol needs explicit key provisioning and
  challenge-response. Never embed a shared secret in the Android APK.
- ADB debugging grants powerful access. Disable it when finished and do not
  authorize unknown computers.

## Run

```sh
python3 host-agent/apolo_host_agent.py
```

In a second terminal on the laptop, after the phone has authorized ADB:

```sh
adb reverse tcp:8765 tcp:8765
```

The endpoint can then be checked from the Android device at
`http://127.0.0.1:8765/v1/identity`. This is an experimental host-side
identity bridge, not a DC sensor and not a charging controller.
