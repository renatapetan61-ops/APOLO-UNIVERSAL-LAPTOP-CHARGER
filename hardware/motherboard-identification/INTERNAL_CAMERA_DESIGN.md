# AMIS Internal Macro Camera — Engineering Design Gate

**Status: software control clients and preliminary architecture only. No camera hardware has been fabricated, selected, installed, or validated.**

## Intended workflow
1. Owner installs the APOLO Host Agent on a supported notebook OS.
2. A qualified technician installs a separate macro-camera module only after confirming safe mounting, working distance, field of view, focus range, and host interface.
3. The module connects to a documented internal USB 2.0/3.x interface or purpose-built bridge. Do not assume the laptop webcam connector is USB: many use MIPI CSI-2 or proprietary pinouts.
4. The owner-authorized USB/ADB bridge exposes the local host agent to Android.
5. Android requests camera enumeration. The agent reports devices without claiming macro capability.
6. After explicit user action, the agent captures a frame, runs local OCR, cross-checks the catalogue and electronic evidence, and returns a confidence state.
7. Results remain UNKNOWN unless evidence meets confirmation rules.

The USB cable used to transfer/install software cannot physically install the camera. It carries data after a compatible camera module has been physically mounted and connected.

## Physical module (not yet selected)
The eventual module should use USB Video Class (UVC) only if the chosen host interface and OS support it. Required design inputs:
- exact chassis and motherboard layout/revision;
- measured camera-to-silkscreen working distance;
- minimum character height and required resolving power;
- focus range, field of view, depth of field, mechanical envelope;
- safe location clear of battery, fan, heatsink, hinge, keyboard travel, and airflow;
- host connector voltage/current limits and validated power budget;
- thermal, EMI/ESD, strain relief, and serviceability constraints.

Macro lens, focus control, and illumination controller are separate physical capabilities. UVC enumeration proves none of them. Illumination must be current-limited and independently validated.

## Four-language software layout
The camera sensor and low-level firmware are not meaningfully implemented four times in four general-purpose languages. The project provides interoperable host-agent clients:
- Python: amis-sdk/python/amis_client.py
- Go: amis-sdk/go/main.go
- Rust: amis-sdk/rust/
- Ruby: amis-sdk/ruby/amis_client.rb

All clients call GET /v1/camera for enumeration and POST /v1/camera/capture for one frame plus local OCR. Python remains the current capture backend through OpenCV on Linux-style camera indices. Go, Rust, and Ruby are API clients, not camera drivers or firmware. The backend does not yet provide per-camera challenge-response; loopback/ADB is not device authentication.

## Data and privacy
- Capture is explicit, never continuous by default.
- Process images locally and do not retain them by default.
- Do not send images to cloud services without separate informed consent.
- Return raw OCR candidates and provenance; do not silently replace markings with guessed part numbers.
- Catalogue remains empty until authoritative board evidence exists.

## Safety and installation
- A qualified technician must inspect the exact notebook and isolate AC and battery according to its service procedure before internal work.
- No drilling, cutting, sanding, improvised soldering, or connection to unknown motherboard pads.
- Never mount above or against pouch cells, fans, heatsinks, hinges, or ventilation paths.
- If no safe optical path exists, use an external technician-operated macro camera. Do not force internal installation.
- Optical identification does not measure DC jack voltage/polarity and cannot authorize charging.

## Release gates
1. Select a camera only after chassis inspection and optical measurements.
2. Build and bench-test the module outside the notebook.
3. Validate UVC enumeration, focus, illumination, thermal behavior, and image quality.
4. Implement per-device key provisioning, nonce challenge-response, signed capture metadata, and replay protection.
5. Test OCR with permissioned images covering blur, glare, low light, and oblique angles.
6. Integrate camera state and reviewed identification evidence into Android.
7. Have a qualified technician validate the installed module and document mounting/service procedures.
