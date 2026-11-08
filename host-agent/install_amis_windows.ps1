#requires -Version 5.1
$ErrorActionPreference = "Stop"
$Root = (Get-Location).Path
$Agent = Join-Path $Root "apolo_host_agent.py"
if (-not (Test-Path $Agent)) { throw "Run this installer from the host-agent directory." }
$Python = (Get-Command py -ErrorAction SilentlyContinue)
if (-not $Python) { throw "Python Launcher (py) not found. Install Python 3.11+ first." }
$Venv = Join-Path $Root ".venv-amis"
if (-not (Test-Path $Venv)) { py -3 -m venv $Venv }
$VenvPython = Join-Path $Venv "Scripts\python.exe"
& $VenvPython -m pip install --upgrade pip
if (Test-Path (Join-Path $Root "requirements-vision.txt")) { & $VenvPython -m pip install -r (Join-Path $Root "requirements-vision.txt") }
& $VenvPython -m py_compile $Agent (Join-Path $Root "amis_hardware_mapper.py") (Join-Path $Root "amis_virtual_camera.py") (Join-Path $Root "amis_vision_engine.py")
$Startup = [Environment]::GetFolderPath("Startup")
$ShortcutPath = Join-Path $Startup "APOLO AMIS Host Agent.lnk"
$Shell = New-Object -ComObject WScript.Shell
$Shortcut = $Shell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $VenvPython
$Shortcut.Arguments = "`"$Agent`""
$Shortcut.WorkingDirectory = $Root
$Shortcut.WindowStyle = 7
$Shortcut.Description = "APOLO AMIS read-only hardware inventory and camera host"
$Shortcut.Save()
Write-Host "AMIS host modules installed for the current Windows user."
Write-Host "The local-only agent will start at next sign-in. Start it now with:"
Write-Host "& `"$VenvPython`" `"$Agent`""
Write-Host "Hardware map JSON: http://127.0.0.1:8765/v1/hardware/map"
Write-Host "Hardware map SVG:  http://127.0.0.1:8765/v1/hardware/map.svg"
Write-Host "This installer does not install a physical camera driver or enable charging."
