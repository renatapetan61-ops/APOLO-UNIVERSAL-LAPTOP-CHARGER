# Android-to-Windows AMIS bootstrap and approval

## User flow

1. Open APOLO Charger on Android and connect the phone to the Windows notebook with a USB data cable.
2. On the Connection screen, tap **Preparar instalador Windows** and save `install_amis_windows.ps1`.
3. Enable USB file transfer (MTP) if prompted and copy the script to the Windows notebook.
4. On Windows, open PowerShell in the copied file's folder and run `./install_amis_windows.ps1`.
5. The script downloads the repository archive to a temporary folder, checks for Python 3.11+ and configures the official Android Platform Tools. It does not yet install the AMIS Host Agent.
6. Enable USB debugging on Android and accept the RSA authorization dialog for this Windows computer.
7. The Windows installer creates an ADB reverse tunnel on port 8766 and starts the temporary approval server bound only to 127.0.0.1. The PowerShell window displays a six-digit, one-time code and waits up to five minutes.
8. In APOLO Charger, enter that code in **Código de autorização do Windows** and tap **Confirmar e autorizar instalação no notebook**.
9. The app sends the one-time approval over the ADB USB reverse tunnel. Only after a valid approval does the PowerShell installer copy and install the Host Agent, create its per-user startup shortcut and start it.
10. The app can then use the ADB reverse tunnel on port 8765 to check the running AMIS agent.

## Security boundaries

- The Android button is an application-level one-time approval, not a Windows UAC elevation or an OS permission grant. The script must first be launched by the user in Windows.
- The temporary approval service binds only to loopback, uses a random six-digit code, constant-time comparison and a five-minute timeout. The ADB bridge requires the Android user to approve the RSA key.
- The agent installation is per-user under `%LOCALAPPDATA%\APOLO\AMIS`; it does not install a kernel driver, change firmware, or write to motherboard components.
- If the code expires or ADB authorization fails, the script stops before installing the Host Agent.
- This flow does not authorize electrical output or prove that the notebook can safely be charged. Hardware power delivery remains separately disabled pending validated voltage, polarity, connector and independent protection circuitry.
- USB cable must support data. Windows needs Python 3.11+ and internet access for GitHub and Google's official Android Platform Tools.
