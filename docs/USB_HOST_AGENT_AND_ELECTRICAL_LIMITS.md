# APOLO host inventory agent and USB bridge

## What the agent can inspect

`host-agent/apolo_host_agent.py` is a read-only Python companion for Windows,
Linux and macOS. It collects information exposed by the host OS and firmware:
manufacturer/model, motherboard, BIOS, CPU, battery status and selected power
supply telemetry. Availability varies by OS, driver and permissions.

- Linux: reads DMI and `/sys/class/power_supply`.
- Windows: queries read-only CIM/WMI classes through PowerShell.
- macOS: queries `system_profiler` hardware and power reports.

The JSON endpoint is `http://127.0.0.1:8765/v1/inventory`.

## USB connection

1. Install/run the agent on the laptop.
2. Enable Android USB debugging only if the owner chooses to use ADB, and
   authorize the phone on the laptop.
3. On the laptop, run `adb reverse tcp:8765 tcp:8765`.
4. The Android APOLO app can then query
   `http://127.0.0.1:8765/v1/inventory`.

A plain cable alone does not install or run an agent and does not grant
arbitrary access to the laptop. ADB is an explicitly enabled, powerful
developer interface. Disable USB debugging when it is no longer needed.

## What it cannot measure

The agent always reports DC jack voltage as null, polarity as
`UNMEASURED`, measurement availability as false, and charging authorization
as false. AC-adapter-present state, battery telemetry, firmware strings,
model databases and vendor specifications are not live electrical
measurements of the DC jack.

No OS command or ordinary USB data cable can universally reveal the voltage
between the physical center contact and sleeve of a barrel jack, or which
contact is positive. That requires an engineered, isolated and protected
measurement front-end connected to those contacts, with ADC telemetry and
independent hardware interlocks. The measurement system must be designed and
validated before any power output is enabled.

## Security and trust

- The service binds only to loopback and is read-only.
- OS inventory is useful evidence but is not cryptographic proof of device identity.
- Battery/adapter information may be absent or inaccurate due to firmware/drivers.
- Do not expose this endpoint to a LAN or public network.
- Do not embed shared secrets in the Android APK.
- Inventory data never authorizes charging.

## Run

```sh
python3 host-agent/apolo_host_agent.py
```

Then, in a second terminal on the laptop (with authorized ADB):

```sh
adb reverse tcp:8765 tcp:8765
```

This agent is a real read-only OS inventory collector. It is not a DC
electrical sensor or a charging controller.
