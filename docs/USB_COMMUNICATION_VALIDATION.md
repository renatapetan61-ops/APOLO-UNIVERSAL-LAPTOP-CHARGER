# APOLO — USB/ADB communication validation

## What the current test proves

The Android **Testar comunicação USB com o notebook** action calls `GET /v1/health`
through the ADB reverse bridge. An HTTP 200 response proves that the phone app can
reach the host agent over the configured ADB data channel. It does not prove USB
power-delivery negotiation, electrical safety, DC jack voltage/polarity, or
physical cable quality under load.

## Required physical setup

1. Use a USB data cable, not a charge-only cable.
2. Connect the Android phone to the notebook and unlock both devices.
3. Enable Android Developer Options and USB debugging, then accept the RSA
   authorization prompt for this notebook.
4. From the APOLO app's **Conexão** screen, export the Windows installer and copy
   it to the notebook.
5. Run the PowerShell installer on the notebook. It downloads the host agent,
   asks for one-time approval through the ADB reverse channel, and starts the
   loopback-only agent.
6. In the app, press **Testar comunicação USB com o notebook**.
7. A successful result must show `agent=READY`, host OS and port 8765. The
   response also includes the ADB reverse list for troubleshooting.

## Windows repair privilege

The normal host agent can run as the logged-in user. The Windows SFC repair action
requires an elevated agent. If the app reports HTTP 403/admin required, close the
agent and run the installer from an Administrator PowerShell session after
reviewing the script. The app still asks for a separate repair confirmation.

## Evidence to record

- Phone model and Android version.
- Notebook model and OS build.
- Whether `adb devices -l` lists the phone as `device`, not `unauthorized`.
- The full JSON returned by `/v1/health`.
- Whether the app can repeatedly reach the endpoint after unplug/replug.
- Any USB disconnects, timeouts or host-agent restarts.

## Not yet physically verified

No physical phone/notebook/cable test is claimed by source-code commits or CI.
GitHub Actions validates code in hosted runners; the real USB test must be
performed with the user's phone and notebook connected. Do not connect or test
the APOLO Power Module output to the notebook during this communication test.
