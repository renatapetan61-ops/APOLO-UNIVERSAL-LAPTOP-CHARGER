# AMIS — dual-source camera and real-board inspection

## One integrated pipeline

```text
Android phone camera (CameraX) --HTTP/ADB reverse--+
                                                    +--> AMIS Virtual Camera Core
Windows/Linux UVC endoscope --OpenCV capture--------+             |
                                                                  v
                                                   AMIS Motherboard Vision Engine
                                                                  |
                                             OCR + exact catalogue match + provenance
                                                                  |
                                                    inspection result (not charging auth)
```

Both image sources are accepted by the same frame-ingestion and vision pipeline.
They remain separately identified by source ID and frame hash. Results from two
frames are evidence from two captures, not stereo/depth reconstruction and not
proof that the camera can see through a closed opaque chassis.

## Windows virtual webcam relay (optional)

The optional `amis_virtual_webcam.py` relays frames from a real UVC camera to a
Windows virtual webcam device using `pyvirtualcam`. It does not generate a
procedural tunnel and never labels synthetic pixels as a motherboard photograph.

Install Python 3.11+ and the dependencies:

```powershell
py -m pip install opencv-python numpy pyvirtualcam
```

Install and enable one compatible virtual-camera driver:
- OBS Studio: install OBS, open it, then choose **Start Virtual Camera**.
- Unity Capture: install the Unity Capture DirectShow virtual-camera driver from
  its official project/release source and reboot if its installer requests it.

Run from the host-agent directory:

```powershell
py amis_virtual_webcam.py --device 0 --width 1280 --height 720 --fps 30 --backend obs --amis-url http://127.0.0.1:8765/v1/virtual-camera/frames
```

For Unity Capture, replace `obs` with `unitycapture`. If the selected backend
is not installed/enabled, the program reports an error instead of fabricating a
camera device. Select the resulting virtual camera in a Windows application
such as Camera or OBS. The virtual webcam is a video relay for conferencing and
inspection preview; the AMIS OCR pipeline still receives the original camera
frames through the host agent.

## Android phone camera

1. Run `python apolo_host_agent.py` on the notebook.
2. Connect the Android phone by USB and authorize USB debugging on both devices.
3. Run `adb reverse tcp:8765 tcp:8765` on the computer.
4. In APOLO Charger, allow camera permission and open **AMIS Mobile Camera**.
5. Tap **Conectar AMIS**, then capture a real, focused image.
6. The image is sent to `127.0.0.1:8765/v1/virtual-camera/frames`; the host
   validates it and runs local OCR. The temporary Android cache file is deleted.

If the host runs on another machine without an ADB reverse bridge, configure a
secure authenticated transport before exposing any network interface. The
agent currently binds only to loopback.

## Physical access is required

Neither software camera nor fisheye/tunnel rendering can image through an opaque
notebook case, metal shield, keyboard deck, or motherboard. To inspect a board,
the real optical sensor must have a safe line of sight: for example, the notebook
must be opened using the manufacturer's service procedure, or a compatible
endoscope must enter an existing service opening without contacting energized
components. Do not force a probe into vents or ports, and do not work inside a
powered notebook.

A virtual webcam can carry a real endoscope's frames to Windows applications.
It cannot turn a software-generated tunnel into a photograph of the user's
motherboard. Synthetic demonstration images must never enter the identification
or electrical authorization path.

## Evidence and charging gate

- OCR candidates retain source/frame provenance and are cross-checked against
  the curated board catalogue.
- Empty catalogue or unreadable inscriptions produce `UNKNOWN`.
- Exact OCR match without independent corroboration is only `PROBABLE`.
- Camera/OCR results do not measure DC-jack voltage or polarity.
- Charging authorization remains denied until connector, polarity, voltage,
  current limits, hardware protection and electrical validation are independently
  established. The software BMS is not a substitute for physical protections.

## Play Protect and APK installation

The debug APK produced by CI is a development build signed with a debug key.
Google Play Protect can warn or block it because the app/developer is not known
or the package has not been distributed through a recognized channel. That
warning is not fixed by changing the app icon, package name, or target SDK.

For normal distribution, create a release build signed with a private release
keystore whose credentials remain outside Git (for example, protected CI
secrets), then distribute through a trusted channel such as Google Play with
Play App Signing. Never commit a keystore or passwords. For a personally built
debug APK, inspect the source and artifact provenance; if Android offers a
`More details` / `Install anyway` option, use it only if you trust the build.
Do not disable Play Protect globally to install an unverified APK.
