# APOLO Virtual IC — implementation contract

## Scope

The four APOLO ICs are software-only virtual controllers embedded in the APOLO Android application and its authorized notebook host agent. They are not silicon, FPGA bitstreams, kernel drivers, or physical sensors. The word "IC" is the product name for an isolated software controller with its own state, inputs, outputs, validation rules, and tests.

## Runtime implemented in this branch

- Android: `ApoloVirtualChips.kt` defines four independent Kotlin controller modules and an observation provenance gate.
- Notebook host: `host-agent/apolo_virtual_ics.py` implements the four independently executable controller classes and their virtual sensor engine.
- Diagnostics: `host-agent/apolo_diagnostics.py` gathers read-only, OS-exposed evidence and executes the virtual IC runtime.
- Transport: `POST /v1/diagnostics/run`, `GET /v1/health`, and the consent-gated Windows repair endpoint are exposed by the loopback-only host agent. The owner-authorized ADB reverse bridge makes them reachable from the phone.
- UI: `RepairScreen.kt` starts the requested diagnostic operation and displays the final report in an Android app dialog. The notebook does not display the report.
- Tests: Python unit tests cover diagnostics and repair authorization; Android unit tests cover controller isolation and observation provenance; CI compiles/runs all 15 observation-contract adapters.

## Four virtual controllers

| Controller | Software responsibility |
|---|---|
| APOLO-BMS IC | Evaluate battery evidence exposed by the host; never invent cell readings or state of charge |
| APOLO-CHARGE IC | Evaluate host-provided power/adapter telemetry; never switch or regulate electrical power |
| APOLO-SAFETY IC | Apply fail-closed software policy to observations and diagnostic findings |
| APOLO-USB-PD IC | Evaluate USB capability evidence; never claim a PD contract without protocol evidence |

The virtual sensor engine is software. It can classify, validate, timestamp and correlate observations from Windows WMI/CIM, Linux sysfs/procfs/journal, or other explicitly supported host interfaces. It cannot measure voltage, current, temperature, or signals hidden from the operating system. Physical measurements require a physical sensor interface; no such measurement is claimed by this branch.

## Diagnostic and report contract

The report is returned to the Android app and displayed only in the app's final pop-up. It contains:

1. total errors/findings found;
2. descriptions and evidence sources;
3. errors corrected, with verified postconditions only;
4. errors not corrected and reasons;
5. prevention recommendations.

The diagnostic scan remains read-only and reports zero corrections. It now collects additional OS-backed telemetry where available: CPU utilization, memory availability, GPU identity/driver/status, storage status/free space, thermal-zone/hwmon values, PCI driver associations, and SMBIOS/baseboard evidence. Missing readings are marked unavailable rather than fabricated. A single Windows system-file repair workflow is available after an explicit in-app confirmation: SFC verify-only, SFC scan-and-repair if corruption is found, and a post-repair verify-only check. The action is available only on Windows and requires the host agent to be elevated as Administrator. The app counts a correction only when the post-check confirms a clean integrity state. This is not a general-purpose driver, firmware, malware or physical hardware repair facility. The report's "found" count is the count of evidence-backed findings and repair-action findings, not a claim that every possible notebook fault was discovered.

## Fifteen-language engineering plan

The 15-language target is assigned by responsibility, not by duplicating the same algorithm in 15 syntaxes:

1. Kotlin — Android application and on-device virtual IC runtime.
2. Python — notebook diagnostic engine and initial host-side IC runtime.
3. Rust — strict telemetry/provenance parser and safety-critical software policy core.
4. C — low-level host sensor-interface adapters where OS APIs expose data.
5. C++ — native platform and device-enumeration adapters.
6. Go — standalone cross-platform host-agent service.
7. C# — Windows service and WMI integration.
8. Java — JVM interoperability and protocol SDK.
9. Swift — future macOS host companion.
10. JavaScript — UI tooling and report presentation utilities.
11. TypeScript — typed application/agent API contracts.
12. PowerShell — Windows installation and diagnostics orchestration.
13. Bash — Linux installation and service orchestration.
14. SQL — local diagnostic history and audit records.
15. SystemVerilog — optional executable digital-logic model for research/testing, not a physical sensor and not an Android ASIC.

The 15-language observation-contract adapter source set is now present under `sensor-contract/`. It implements a common tab-separated record validator and a cross-language test harness. Kotlin is integrated in the Android source tree; Python remains the host-side orchestration language. The C, C++, Rust, Go, C#, Java, Swift, JavaScript, TypeScript, PowerShell, Bash, SQL and SystemVerilog adapters are independently executable contract gates, not separate hardware drivers. GitHub Actions compiles and runs the matrix and rejects `TEST_FIXTURE` input. Do not claim these adapters directly access physical sensors: they validate normalized observations supplied by an OS interface or a separately validated physical interface.

## Safety and honesty invariants

- Virtual sensor data must carry origin, source and timestamp.
- Test fixtures are never presented as live notebook measurements.
- No USB cable transfers executable code into individual motherboard components.
- The host agent operates with least privilege and only after explicit owner installation/authorization.
- Diagnostic actions remain read-only until an individual repair action has a narrow allowlist, explicit user consent, backup/rollback strategy where applicable, and a verifiable postcondition.
- The virtual chips cannot repair physical damage or replace electrical protection hardware.
- No power output is authorized by virtual sensor readings or software controller state.
