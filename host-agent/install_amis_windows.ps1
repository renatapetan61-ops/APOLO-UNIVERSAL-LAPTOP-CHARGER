#requires -Version 5.1
$ErrorActionPreference = "Stop"
$RepoZip = "https://github.com/renatapetan61-ops/APOLO-UNIVERSAL-LAPTOP-CHARGER/archive/refs/heads/main.zip"
$InstallRoot = Join-Path $env:LOCALAPPDATA "APOLO\AMIS"
$ZipPath = Join-Path $env:TEMP "apolo-amis-main.zip"
$ExtractRoot = Join-Path $env:TEMP ("apolo-amis-" + [guid]::NewGuid().ToString("N"))
Write-Host "APOLO AMIS — instalador do agente do notebook"
Write-Host "Este processo instala módulos locais de inventário e inspeção."
Write-Host "Não instala drivers de câmera, não altera firmware e NÃO habilita saída elétrica."
Write-Host "Será necessário confirmar a instalação nesta janela do Windows."
$confirm = Read-Host "Digite INSTALAR para continuar"
if ($confirm -cne "INSTALAR") { Write-Host "Instalação cancelada."; exit 0 }
$Python = Get-Command py -ErrorAction SilentlyContinue
if (-not $Python) { throw "Python 3.11+ com o Python Launcher (py) é necessário. Instale-o e execute novamente." }
New-Item -ItemType Directory -Force -Path $InstallRoot | Out-Null
try {
    Write-Host "Baixando o pacote oficial do repositório por HTTPS..."
    Invoke-WebRequest -Uri $RepoZip -OutFile $ZipPath -UseBasicParsing
    Expand-Archive -LiteralPath $ZipPath -DestinationPath $ExtractRoot -Force
    $SourceRoot = Get-ChildItem -LiteralPath $ExtractRoot -Directory | Select-Object -First 1
    if (-not $SourceRoot) { throw "Pacote do repositório vazio." }
    $SourceAgent = Join-Path $SourceRoot.FullName "host-agent"
    if (-not (Test-Path (Join-Path $SourceAgent "apolo_host_agent.py"))) { throw "Host Agent não encontrado no pacote." }
    if (Test-Path $InstallRoot) {
        Get-ChildItem -LiteralPath $InstallRoot -Force | Remove-Item -Recurse -Force
    }
    Copy-Item -Path (Join-Path $SourceAgent "*") -Destination $InstallRoot -Recurse -Force
} finally {
    Remove-Item -LiteralPath $ZipPath -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $ExtractRoot -Recurse -Force -ErrorAction SilentlyContinue
}
$Agent = Join-Path $InstallRoot "apolo_host_agent.py"
$Venv = Join-Path $InstallRoot ".venv-amis"
if (-not (Test-Path $Venv)) { py -3 -m venv $Venv }
$VenvPython = Join-Path $Venv "Scripts\python.exe"
& $VenvPython -m pip install --upgrade pip
if (Test-Path (Join-Path $InstallRoot "requirements-vision.txt")) { & $VenvPython -m pip install -r (Join-Path $InstallRoot "requirements-vision.txt") }
if (Test-Path (Join-Path $InstallRoot "requirements-virtual-webcam.txt")) { & $VenvPython -m pip install -r (Join-Path $InstallRoot "requirements-virtual-webcam.txt") }
& $VenvPython -m py_compile $Agent (Join-Path $InstallRoot "amis_hardware_mapper.py") (Join-Path $InstallRoot "amis_virtual_camera.py") (Join-Path $InstallRoot "amis_vision_engine.py")
if ($LASTEXITCODE -ne 0) { throw "Falha na verificação de sintaxe dos módulos AMIS." }
$Startup = [Environment]::GetFolderPath("Startup")
$ShortcutPath = Join-Path $Startup "APOLO AMIS Host Agent.lnk"
$Shell = New-Object -ComObject WScript.Shell
$Shortcut = $Shell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $VenvPython
$Shortcut.Arguments = "`"$Agent`""
$Shortcut.WorkingDirectory = $InstallRoot
$Shortcut.WindowStyle = 7
$Shortcut.Description = "APOLO AMIS read-only hardware inventory and camera host"
$Shortcut.Save()
Write-Host "Instalação concluída. Iniciando o Host Agent agora..."
$Process = Start-Process -FilePath $VenvPython -ArgumentList "`"$Agent`"" -WorkingDirectory $InstallRoot -PassThru
Start-Sleep -Seconds 2
try {
    $status = Invoke-RestMethod -Uri "http://127.0.0.1:8765/v1/hardware/map" -TimeoutSec 5
    Write-Host ("AMIS ativo. Componentes mapeados: " + $status.node_count)
} catch {
    Write-Warning "O agente foi iniciado, mas o endpoint ainda não respondeu. Verifique a janela/processo Python."
}
Write-Host "Instalado em: $InstallRoot"
Write-Host "Mapa SVG: http://127.0.0.1:8765/v1/hardware/map.svg"
Write-Host "A instalação não autoriza nem executa carregamento elétrico."
