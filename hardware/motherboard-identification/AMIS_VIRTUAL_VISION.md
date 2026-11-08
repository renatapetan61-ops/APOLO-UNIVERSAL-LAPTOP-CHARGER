# AMIS Virtual Vision Architecture

## Components

### AMIS Virtual Camera Core
A source-independent software camera abstraction. It accepts image frames from the Android CameraX client, a future authenticated camera adapter, or an explicitly imported image source. It validates JPEG/PNG/WebP signatures and an 8 MiB limit, assigns a frame ID and timestamp, computes SHA-256 evidence metadata, and passes the frame to the vision engine. Frame bytes remain in memory only and are discarded after processing.

This is not a physical camera and cannot create optical information. A real camera or existing image is required. The Android phone camera is the initial live source. The notebook host agent must be running and the owner-authorized USB/ADB reverse bridge must be configured; an ordinary USB cable alone does not establish this bridge.

### AMIS Motherboard Vision Engine
A separate local processing component. It invokes Tesseract TSV in two recognition modes (PSM 11 and PSM 6), preserves raw and normalized text candidates, checks exact token/line matches against the curated board catalogue, and cross-checks the baseboard manufacturer evidence exposed by the operating system. When Pillow is installed, it also creates an in-memory 2x grayscale, autocontrast and sharpened variant for a second OCR pass. Processing is bounded by a total timeout. Matching is exact only; fuzzy or substring guesses are deliberately excluded. It returns CONFIRMED, PROBABLE, CONFLICTING_EVIDENCE, or UNKNOWN. It never infers a board code from an incomplete or fuzzy match.

## HTTP interface (loopback only)

- `GET /v1/virtual-camera/status`: virtual source state and last-frame metadata.
- `POST /v1/virtual-camera/frames`: ingest a frame for local OCR. Headers: `Content-Type: image/jpeg|image/png|image/webp`; optional `X-AMIS-Source` (default `android-camerax`). Response is the vision-engine result.
- Existing `POST /v1/board-inspection` remains compatible with the Android CameraX app and routes through both components.
- `GET /v1/inventory` remains the read-only OS/firmware inventory endpoint.

The host agent binds only to 127.0.0.1. The image is not written to disk or uploaded to a cloud service by these components. The OCR implementation may create a temporary local file for Tesseract and removes it when processing finishes.

## Optical limitations

The phone camera can photograph the motherboard only with direct line of sight. If the laptop is closed or the board is hidden by an opaque chassis, keyboard, shield, or other component, the virtual camera cannot see through it. A qualified technician may need to safely expose the board and position the phone. Digital zoom is not optical macro focus; lighting, focus distance, resolution, glare, and stability determine whether tiny silkscreen can be read.

## Current limits / safety gates

- No physical camera is fabricated, embedded, or automatically mounted by this software.
- No camera can take a real motherboard photograph without a real camera/image source.
- Catalogue is intentionally empty until authoritative, technician-verified board records are available; exact Positivo Unique TV S2065 PCB code/revision remains UNKNOWN.
- OCR text and hashes are evidence, not proof of identity.
- No motherboard electrical probing, DC jack polarity measurement, or charging authorization is performed by AMIS.
- Optional enhancement requires Pillow: install with `python -m pip install -r requirements-vision.txt` from `host-agent/`. Tesseract must separately be installed on the notebook. Without Pillow, the original image is still processed.
- No remote network listener, cloud upload, persistent image storage, or background capture is introduced.
