# AMIS Mobile Camera

## Purpose

AMIS Mobile Camera lets the Android application use the user's own phone camera as the optical capture device for motherboard inspection. It is an alternative to a dedicated internal UVC macro camera; both paths can coexist.

## Implemented Android flow

- CameraX preview using the selected phone camera (rear camera by default).
- Runtime camera permission request.
- Front/rear camera switch.
- Digital zoom control (1x–8x; actual optical/macro capability depends on the phone).
- High-quality still capture, JPEG.
- Local transfer to the notebook host agent at `POST /v1/board-inspection`.
- Maximum upload size 8 MiB, matching the host-agent endpoint.
- Temporary image stored in app cache and deleted after the transfer.
- No cloud image upload by this feature.

The app's Connection screen embeds the AMIS Mobile Camera panel. The user explicitly starts the preview and capture.

## USB / local bridge

The Android app posts to `http://127.0.0.1:8765/v1/board-inspection`. This requires the owner-authorized bridge to be active, for example `adb reverse tcp:8765 tcp:8765` configured from a computer with ADB. A normal USB cable by itself does not automatically create this reverse port mapping. The host agent must be running on the notebook.

The host agent validates the image signature and invokes local Tesseract OCR. If the OCR engine is absent, the result remains UNKNOWN. The Android app displays the JSON result returned by the agent.

## Physical and optical limitations

- A phone camera can inspect the motherboard only when the board markings are in the camera's direct line of sight. It cannot see through the laptop chassis or other opaque parts.
- The user may need to power down, unplug, and have the notebook safely opened by a qualified technician. Do not place a phone or loose object inside an energized notebook.
- Digital zoom does not create optical macro capability. Focus distance, minimum focus, sensor resolution, stabilization, lighting, glare, and working distance vary by phone.
- For very small silkscreen, use a phone with a true macro camera or a clip-on macro lens, stable support, and diffuse lighting.
- Do not let the phone, lens accessory, or support touch the motherboard, battery, exposed conductors, fan, heatsink, or moving parts.
- This feature does not automatically move the camera through the chassis and does not guarantee that every board marking can be read.

## Trust and safety

- OCR output is evidence, not proof. Exact board identification requires an authoritative catalogue match and independent corroboration.
- Never infer an exact board code from blurry or partial text. Preserve UNKNOWN / PROBABLE / CONFLICTING_EVIDENCE states.
- Motherboard inspection does not measure DC jack voltage or polarity and does not authorize power output.
- Images are sent only to the local host agent via the configured bridge; the host agent should remain bound to loopback and should not be exposed to a LAN or public network.
