# AMIS internal camera — installation and software contract

## What USB installation can and cannot do

The APOLO installer can transfer and install host-agent software over a data-capable USB connection (or an owner-authorized ADB bridge). It cannot physically place a camera, lens, LED, cable, or bracket inside the notebook. Those are physical components and must already be installed by a qualified technician.

The camera is an optional hardware accessory belonging to the AMIS subsystem. The host agent can discover a compatible camera, capture a frame on an explicit owner request, and pass the frame to local OCR. If no camera is present, the agent reports `CAMERA_NOT_FOUND`; it must not simulate a capture or infer motherboard markings.

## Supported first prototype

- Camera interface: UVC-compatible USB camera, only after its connector, power budget, dimensions, focus distance, and driver support are verified.
- Host capture: Python `amis_camera.py` using OpenCV, installed separately with `python -m pip install -r host-agent/requirements-camera.txt`.
- Discovery: `GET /v1/camera`.
- Explicit capture and local OCR: `POST /v1/camera/capture`.
- Android controls: Connection screen buttons request discovery and capture through the owner-authorized local ADB reverse bridge.
- OCR: local Tesseract engine; missing engine returns `UNKNOWN` rather than guessing.
- Image handling: frame is processed in memory/temp storage and is not retained by the agent.

A UVC device appearing in the operating system does not prove macro focus, sufficient resolution, controllable illumination, or a view of the motherboard. Those properties require optical and mechanical bench validation on the actual notebook chassis.

## Installation sequence

1. Inspect the exact notebook revision and service manual; disconnect external power and isolate the battery using the approved service procedure.
2. A qualified technician identifies a safe mounting position and a verified camera connection. Do not assume an internal USB header or 5 V rail exists.
3. Confirm the lens has direct line of sight to the intended silkscreen area and can focus at the measured working distance.
4. Confirm the module and cable cannot contact battery cells, exposed conductors, fans, heatsinks, hinges, or ventilation paths.
5. Bench-test camera enumeration, image sharpness, glare, lighting, thermal behavior, and cable retention before closing the chassis.
6. Install the host-agent software over USB only after the physical module is installed and connected.
7. Install optional OpenCV and Tesseract dependencies on the notebook host. Start the agent and establish only an owner-authorized data bridge.
8. In the Android app, request camera discovery, inspect the returned device, and explicitly request a capture. Review OCR candidates and cross-check against electronic evidence.
9. Keep the result `UNKNOWN`, `PROBABLE`, or `CONFLICTING_EVIDENCE` unless exact catalogue evidence and independent corroboration justify `CONFIRMED`.

## Language boundaries

- Python: host-agent integration, UVC capture orchestration, local OCR pipeline, and API. This is the implemented prototype.
- Rust: preferred future firmware for a dedicated camera/illumination controller MCU, once a specific sensor and controller board are selected. No MCU firmware is claimed to exist yet.
- Go: optional future signed installer/service manager if cross-platform deployment complexity justifies a second host binary. It is not required for image capture.
- Ruby: not included in the capture path. It would duplicate existing responsibilities without improving camera access, latency, or safety; adding it now would enlarge the runtime and maintenance surface.

The four languages should not all implement the same camera driver. The hardware protocol and authenticated message format should be language-neutral and versioned.

## Security and privacy gates

- Camera capture is initiated by an explicit user action; no background or continuous recording.
- No cloud upload by default; no image archive by default.
- Keep the agent bound to loopback. Do not expose port 8765 to the LAN or internet.
- ADB reverse must be enabled and authorized by the notebook owner. Revoke USB debugging authorization and disable debugging after the maintenance session.
- Device-level camera authentication, nonce challenge-response, and replay protection are still pending. Until implemented, the camera is not cryptographically authenticated; loopback/ADB transport is not a substitute for device identity.
- Camera capture and motherboard identification never authorize laptop charging or alter BMS/power-module safety state.

## Current hardware status

No internal macro camera has been purchased, fabricated, mounted, or tested in the Positivo Unique TV S2065. The exact motherboard silkscreen code and safe camera mounting point remain unknown. Do not claim physical installation or identification until a real module is fitted and validated.
