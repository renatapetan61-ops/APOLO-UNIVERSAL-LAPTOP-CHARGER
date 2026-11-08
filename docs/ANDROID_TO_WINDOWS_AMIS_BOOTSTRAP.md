# Android-to-Windows AMIS bootstrap

## Intended user flow

1. Install/open APOLO Charger on Android.
2. Connect the phone to the Windows notebook with a USB data cable.
3. In APOLO Charger, open **Conexão** and tap **Preparar instalador Windows**.
4. Save `install_amis_windows.ps1` to the phone using the Android document picker.
5. Change the phone's USB mode to **File transfer (MTP)** if Android asks, then copy the saved script to the Windows notebook.
6. On Windows, open PowerShell in the copied file's folder and run:
   ```powershell
   .\install_amis_windows.ps1
   ```
7. Review the script prompt and type `INSTALAR` only if you approve. The script downloads the repository and official Android Platform Tools over HTTPS, installs the local Python agent in the current user's LocalAppData, and starts it.
8. Enable Android USB debugging and accept the RSA authorization prompt for this computer. The agent attempts `adb reverse tcp:8765 tcp:8765` when it starts.
9. Return to APOLO Charger and tap **Conectar e verificar agente AMIS no notebook**. If the reverse bridge is authorized, the app should receive the agent's AMIS status.
10. The camera inspection upload endpoint is then reachable through the reverse bridge.

## Why the Android app does not silently run the PowerShell file

A normal Android application cannot execute a Windows PowerShell script on a PC merely because a USB cable is attached. In this cable arrangement, Windows is normally the USB host and Android is the MTP/ADB device. Android must not assume permission to write arbitrary files to Windows or start arbitrary Windows processes. The implementation therefore exports the installer, asks the user to copy it, and requires an explicit confirmation in PowerShell. The subsequent ADB bridge also requires the user to enable USB debugging and approve the computer's RSA key.

## Requirements and limitations

- USB cable must support data, not charging-only.
- Windows notebook must have Python 3.11+ with the `py` launcher.
- The installer requires internet access to download the GitHub source archive and Google's official Android Platform Tools.
- ADB reverse works only after USB debugging is enabled and the Android authorization dialog is accepted.
- If USB debugging cannot be enabled, the app can still export the installer, but phone-to-agent live communication over the cable will not be available through ADB.
- The agent binds to `127.0.0.1:8765`; it is not exposed to the LAN.
- The installer does not flash firmware, alter motherboard components, install kernel camera drivers, or authorize electrical output.
- Installing the agent is not the same as physically charging the laptop. Power output remains blocked until a separately engineered and validated power module, connector, polarity, sensor and independent protections exist.
