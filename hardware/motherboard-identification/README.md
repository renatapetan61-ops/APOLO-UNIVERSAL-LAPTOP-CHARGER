# APOLO Motherboard Identification Sensor (AMIS)

**Status: concept and software/hardware requirements only. No camera board has been fabricated, tested, or installed.**

## Objective

Identify the exact motherboard manufacturer, board code, PCB revision, and visible silkscreen markings without requiring the owner to take and upload a photograph. The system combines read-only firmware inventory with an optional optical inspection module. It must never guess a board identity.

## Two independent identification channels

### Channel A — electronic inventory (no added sensor required)

The existing APOLO Host Agent reads fields exposed by the operating system and firmware:
- SMBIOS/DMI system manufacturer, product name and version;
- baseboard manufacturer, product and version;
- BIOS vendor, version and date;
- CPU architecture and model;
- battery and power-supply telemetry exposed by the OS.

The agent should preserve the original source and raw values. These fields can be absent, generic, overridden by firmware, or refer to a system SKU rather than the PCB silkscreen. They are clues, not proof of the exact PCB revision.

### Channel B — optical silkscreen reader (requires physical line of sight)

A future optical module may contain:
- macro-capable camera sensor with fixed-focus or autofocus optics appropriate to the measured working distance;
- diffuse, controllable white illumination to reduce glare and shadows;
- optional cross-polarized illumination/optics if reflective shielding makes glare unavoidable;
- embedded image processor or MCU for capture control;
- authenticated USB or other isolated data link to the host agent;
- mechanically restrained mount that cannot touch or obstruct fans, heatsinks, battery cells, hinges, or moving parts.

The camera must have a direct optical path to the motherboard silkscreen. A camera hidden under an opaque keyboard, shield, or chassis panel cannot read markings through those materials. No optical sensor can identify a printed code if it cannot see it. The owner need not take a photo, but a qualified technician may still need to expose the board and position the module during installation.

## Processing pipeline

1. Capture several frames with controlled illumination and exposure.
2. Detect text regions and perspective distortion.
3. Run OCR locally on the embedded processor or trusted host.
4. Normalize candidate strings while retaining the exact raw OCR output.
5. Search a curated motherboard-code catalogue; do not use fuzzy matching alone to claim identity.
6. Cross-check optical candidates against DMI/SMBIOS, BIOS, and known board revisions.
7. Return one of: CONFIRMED, PROBABLE, CONFLICTING_EVIDENCE, or UNKNOWN.
8. Include evidence, confidence, capture timestamp, image quality, OCR engine/version, and catalogue revision.

The app must display the literal marking and the source that produced it. OCR confidence is not proof. A CONFIRMED result requires an exact catalogue match and independent corroboration, or human technical review.

## Suggested data contract

- protocol: apolo-board-id/1
- capture_id: unique capture identifier
- sensor_id: provisioned optical module identity
- captured_at: timestamp
- image_quality: PASS / BLUR / LOW_LIGHT / OCCLUDED / NO_LINE_OF_SIGHT
- ocr_candidates: array of raw text, normalized text, and OCR confidence
- dmi_evidence: raw baseboard manufacturer/product/version fields
- catalogue_match: exact catalogue record ID or null
- result: CONFIRMED / PROBABLE / CONFLICTING_EVIDENCE / UNKNOWN
- evidence_hash: digest of the retained evidence bundle
- auth_tag: device-authenticated message tag

Do not upload motherboard images or identifiers to a cloud service by default. Local processing is preferred. If remote processing is ever added, it requires explicit owner consent and a documented retention policy.

## Mechanical and electrical safety

- Do not attach a camera, cable, or bracket over a battery pouch, cell, fan, heatsink, hinge, or ventilation opening.
- Do not drill, cut, sand, scrape, or solder the motherboard or chassis to fit the sensor.
- Do not connect the optical module to unknown motherboard pads or power rails.
- Power the optical module from a separately validated, current-limited supply or approved interface designed for the host.
- Ensure the module cannot short conductive surfaces or detach into a fan.
- Installation and inspection inside the laptop must be performed by a qualified technician after disconnecting AC and isolating the battery according to the service procedure.
- If no safe line of sight or mounting point exists, use a technician-operated external macro inspection tool. Do not force an internal installation.

## Current project status

- OS/firmware inventory: existing read-only host agent implementation.
- Optical sensor hardware: not designed to a purchasable BOM; no board fabricated.
- Camera transport and authenticated capture protocol: not implemented.
- OCR and motherboard catalogue: not implemented.
- Exact Positivo Unique TV S2065 motherboard code/revision: UNKNOWN.
- DC jack polarity: UNMEASURED.
- Laptop power output: remains blocked.

## Next engineering gates

1. Extend host inventory output with explicit raw SMBIOS baseboard fields and provenance.
2. Implement a local OCR proof-of-concept against sample images of known board markings.
3. Select camera/optics only after measuring the physical working distance and confirming a safe line of sight on the exact chassis.
4. Build and bench-test a standalone optical module before any laptop installation.
5. Create a versioned catalogue with authoritative references and board-revision distinctions.
6. Integrate authenticated results into the host agent and Android app.
