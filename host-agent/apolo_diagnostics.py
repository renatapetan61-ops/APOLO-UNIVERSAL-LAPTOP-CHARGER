"""Evidence-backed, read-only APOLO diagnostics plus one consent-gated Windows repair.

All telemetry is sourced from host OS interfaces. Missing interfaces are reported
as unavailable, never replaced with invented sensor readings.
"""
from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

from apolo_virtual_ics import ApoloVirtualIcRuntime


def _run(args: list[str], timeout: int = 12) -> str | None:
    try:
        result = subprocess.run(args, capture_output=True, text=True,
                                timeout=timeout, check=False)
        output = (result.stdout or "").strip()
        return output if result.returncode == 0 or output else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def _finding(code: str, title: str, detail: str, severity: str,
             source: str, recommendation: str) -> dict:
    return {"code": code, "title": title, "detail": detail,
            "severity": severity, "source": source,
            "recommendation": recommendation, "status": "FOUND"}


def _linux_cpu_percent() -> float | None:
    def sample() -> tuple[int, int] | None:
        try:
            fields = Path("/proc/stat").read_text().splitlines()[0].split()[1:]
            values = [int(value) for value in fields]
            idle = values[3] + (values[4] if len(values) > 4 else 0)
            return sum(values), idle
        except (OSError, ValueError, IndexError):
            return None
    first = sample()
    if not first:
        return None
    time.sleep(0.12)
    second = sample()
    if not second:
        return None
    total = second[0] - first[0]
    idle = second[1] - first[1]
    return round(max(0.0, min(100.0, (1 - idle / total) * 100)), 1) if total > 0 else None


def _linux_checks() -> tuple[list[dict], dict]:
    findings: list[dict] = []
    telemetry: dict = {"source": "Linux procfs/sysfs and optional system utilities",
                       "cpu": {}, "memory": {}, "gpu": [], "storage": [],
                       "temperatures": [], "motherboard": {}, "drivers": []}
    telemetry["cpu"]["model"] = None
    try:
        for line in Path("/proc/cpuinfo").read_text().splitlines():
            if line.lower().startswith(("model name", "hardware")) and ":" in line:
                telemetry["cpu"]["model"] = line.split(":", 1)[1].strip()
                break
    except OSError:
        pass
    telemetry["cpu"]["utilization_percent"] = _linux_cpu_percent()
    if telemetry["cpu"]["utilization_percent"] is not None and telemetry["cpu"]["utilization_percent"] >= 98:
        findings.append(_finding("CPU_HIGH_UTILIZATION", "Uso de CPU muito elevado",
            f"Utilização observada: {telemetry['cpu']['utilization_percent']}% durante a amostra.",
            "warning", "/proc/stat", "Identifique processos que consomem CPU e repita a medição após alguns minutos."))

    try:
        values = {}
        for line in Path("/proc/meminfo").read_text().splitlines():
            key, _, rest = line.partition(":")
            if key in ("MemAvailable", "MemTotal"):
                values[key] = int(rest.strip().split()[0])
        if values.get("MemTotal") and values.get("MemAvailable") is not None:
            total_kb, available_kb = values["MemTotal"], values["MemAvailable"]
            percent = round(available_kb / total_kb * 100, 1)
            telemetry["memory"] = {"total_kb": total_kb, "available_kb": available_kb,
                                   "available_percent": percent, "source": "/proc/meminfo"}
            if percent < 5:
                findings.append(_finding("MEMORY_PRESSURE", "Memória disponível muito baixa",
                    f"{percent}% da memória total disponível.", "warning", "/proc/meminfo",
                    "Feche aplicativos que não estiver usando e investigue processos com consumo elevado."))
    except (OSError, ValueError, IndexError):
        telemetry["memory"]["available"] = "UNAVAILABLE"

    try:
        usage = shutil.disk_usage("/")
        percent = round(usage.free / usage.total * 100, 1) if usage.total else 0
        telemetry["storage"].append({"mount": "/", "total_bytes": usage.total,
                                     "free_bytes": usage.free, "free_percent": percent,
                                     "source": "shutil.disk_usage"})
        if percent < 5:
            findings.append(_finding("DISK_ROOT_LOW_SPACE", "Pouco espaço livre na partição raiz",
                f"{percent}% livre em /.", "warning", "shutil.disk_usage(/)",
                "Revise arquivos pessoais e faça backup antes de remover dados."))
    except OSError:
        pass

    for hwmon in Path("/sys/class/hwmon").glob("hwmon*"):
        name_path = hwmon / "name"
        try:
            chip = name_path.read_text().strip() or hwmon.name
        except OSError:
            chip = hwmon.name
        for input_path in hwmon.glob("temp*_input"):
            try:
                raw = int(input_path.read_text().strip())
                celsius = round(raw / 1000, 1)
                label_path = input_path.with_name(input_path.name.replace("_input", "_label"))
                label = label_path.read_text().strip() if label_path.exists() else input_path.stem
                item = {"chip": chip, "label": label, "celsius": celsius,
                        "source": str(input_path)}
                telemetry["temperatures"].append(item)
                if celsius >= 90:
                    findings.append(_finding("THERMAL_HIGH", "Temperatura elevada reportada pelo hardware",
                        f"{chip}/{label}: {celsius} °C.", "warning", str(input_path),
                        "Verifique ventilação, ventoinhas e acúmulo de poeira; não abra o equipamento ligado."))
            except (OSError, ValueError):
                continue

    supplies = []
    try:
        for entry in Path("/sys/class/power_supply").iterdir():
            kind_path = entry / "type"
            try:
                kind = kind_path.read_text().strip()
            except OSError:
                continue
            item = {"name": entry.name, "type": kind}
            for key in ("status", "capacity", "voltage_now", "current_now", "power_now", "online", "technology"):
                try:
                    item[key] = (entry / key).read_text().strip()
                except OSError:
                    pass
            supplies.append(item)
    except OSError:
        pass
    telemetry["battery"] = [item for item in supplies if item.get("type") == "Battery"]
    telemetry["power_adapter"] = [item for item in supplies if item.get("type") in ("Mains", "USB", "USB_C")]
    typec = Path("/sys/class/typec")
    try:
        telemetry["usb_typec"] = sorted(path.name for path in typec.iterdir())
    except OSError:
        telemetry["usb_typec"] = []
    usb_devices = Path("/sys/bus/usb/devices")
    try:
        telemetry["usb_devices"] = sorted(path.name for path in usb_devices.iterdir())
    except OSError:
        telemetry["usb_devices"] = []

    dmi = {}
    for key, filename in (("board_vendor", "board_vendor"), ("board_name", "board_name"),
                          ("board_version", "board_version"), ("system_vendor", "sys_vendor"),
                          ("system_model", "product_name"), ("bios_version", "bios_version")):
        path = Path("/sys/class/dmi/id") / filename
        try:
            dmi[key] = path.read_text().strip()
        except OSError:
            dmi[key] = None
    telemetry["motherboard"] = {"fields": dmi, "source": "SMBIOS via /sys/class/dmi/id",
                                "identity_verified": False}
    pci_root = Path("/sys/bus/pci/devices")
    try:
        for device in pci_root.iterdir():
            driver_link = device / "driver"
            driver = driver_link.resolve().name if driver_link.exists() else None
            modalias = None
            try:
                modalias = (device / "modalias").read_text().strip()
            except OSError:
                pass
            class_code = None
            try:
                class_code = (device / "class").read_text().strip()
            except OSError:
                pass
            item = {"pci_id": device.name, "class_code": class_code,
                    "driver": driver, "modalias": modalias}
            telemetry["drivers"].append(item)
            driver_relevant = bool(class_code and class_code.lower().startswith(("0x01", "0x02", "0x03", "0x04")))
            if not driver and driver_relevant:
                findings.append(_finding("PCI_DRIVER_MISSING", "Controlador PCI sem driver associado",
                    f"Dispositivo {device.name}; classe={class_code}; modalias={modalias or 'indisponível'}.",
                    "warning", str(device / "driver"),
                    "Confirme o fabricante e instale um driver compatível obtido de fonte oficial."))
    except OSError:
        pass

    lsblk = _run(["lsblk", "-J", "-o", "NAME,MODEL,SIZE,TYPE,MOUNTPOINTS"], 8)
    if lsblk:
        try:
            telemetry["storage_devices"] = json.loads(lsblk).get("blockdevices", [])
        except json.JSONDecodeError:
            telemetry["storage_devices"] = []
    telemetry["smart"] = []
    if shutil.which("smartctl"):
        try:
            block_devices = [item.name for item in Path("/sys/block").iterdir()
                             if not item.name.startswith(("loop", "ram", "zram"))][:4]
        except OSError:
            block_devices = []
        for name in block_devices:
            output = _run(["smartctl", "-H", "-j", f"/dev/{name}"], 8)
            if not output:
                continue
            try:
                smart = json.loads(output)
                passed = smart.get("smart_status", {}).get("passed")
                record = {"device": f"/dev/{name}", "passed": passed, "source": "smartctl -H -j"}
                telemetry["smart"].append(record)
                if passed is False:
                    findings.append(_finding("DISK_SMART_FAILED", "SMART reportou falha no armazenamento",
                        f"/dev/{name}: o autoteste SMART informa estado não aprovado.", "critical",
                        "smartctl -H -j", "Faça backup imediatamente e procure assistência para substituir a unidade."))
            except (json.JSONDecodeError, AttributeError):
                continue
    lspci = _run(["lspci", "-nn"], 8)
    if lspci:
        telemetry["pci_devices"] = lspci.splitlines()
        telemetry["gpu"] = [line for line in lspci.splitlines()
                            if any(word in line.lower() for word in ("vga", "3d controller", "display controller"))]
    journal = _run(["journalctl", "-p", "err", "-n", "20", "--no-pager"], 8)
    if journal:
        lines = [line for line in journal.splitlines() if line.strip()]
        if lines:
            findings.append(_finding("SYSTEM_ERROR_LOG_ENTRIES", "Eventos de erro registrados pelo sistema",
                f"{len(lines)} linha(s) recente(s) no journal; exigem análise contextual.", "info",
                "journalctl -p err -n 20", "Correlacione os eventos com horário, serviço e dispositivo antes de alterar o sistema."))
    return findings, telemetry


def _windows_checks() -> tuple[list[dict], dict]:
    findings: list[dict] = []
    telemetry: dict = {"source": "Windows CIM/WMI and filesystem APIs"}
    script = r"""
    $cpu=Get-CimInstance Win32_Processor | Select-Object -First 1 Name,LoadPercentage,NumberOfCores,NumberOfLogicalProcessors
    $os=Get-CimInstance Win32_OperatingSystem
    $gpu=@(Get-CimInstance Win32_VideoController | ForEach-Object {@{name=$_.Name;driver_version=$_.DriverVersion;status=$_.Status;video_processor=$_.VideoProcessor}})
    $disks=@(Get-CimInstance Win32_DiskDrive | ForEach-Object {@{model=$_.Model;status=$_.Status;firmware=$_.FirmwareRevision;device=$_.DeviceID}})
    $physicalDisks=@(Get-PhysicalDisk -ErrorAction SilentlyContinue | ForEach-Object {@{name=$_.FriendlyName;health=$_.HealthStatus;operational=@($_.OperationalStatus);media=$_.MediaType;size=$_.Size}})
    $board=Get-CimInstance Win32_BaseBoard
    $bios=Get-CimInstance Win32_BIOS
    $bad=@(Get-CimInstance Win32_PnPEntity -ErrorAction SilentlyContinue | Where-Object {$_.ConfigManagerErrorCode -ne $null -and $_.ConfigManagerErrorCode -ne 0} | Select-Object -First 80 Name,PNPDeviceID,ConfigManagerErrorCode)
    $temps=@(Get-CimInstance -Namespace root/wmi -ClassName MSAcpi_ThermalZoneTemperature -ErrorAction SilentlyContinue | Select-Object InstanceName,CurrentTemperature)
    $batteries=@(Get-CimInstance Win32_Battery -ErrorAction SilentlyContinue | Select-Object Name,Status,BatteryStatus,EstimatedChargeRemaining,DesignVoltage)
    $usb=@(Get-CimInstance Win32_USBController -ErrorAction SilentlyContinue | Select-Object Name,Status,PNPDeviceID)
    [pscustomobject]@{
      cpu=@{name=$cpu.Name;load_percent=$cpu.LoadPercentage;cores=$cpu.NumberOfCores;logical_processors=$cpu.NumberOfLogicalProcessors}
      memory=@{total_bytes=$os.TotalVisibleMemorySize*1024;free_bytes=$os.FreePhysicalMemory*1024}
      gpus=$gpu;disks=$disks;physical_disks=$physicalDisks;bad_devices=$bad;temperatures=$temps
      battery=$batteries;usb_devices=$usb
      motherboard=@{manufacturer=$board.Manufacturer;product=$board.Product;version=$board.Version;bios_vendor=$bios.Manufacturer;bios_version=($bios.SMBIOSBIOSVersion -join ' ')}
    } | ConvertTo-Json -Depth 6 -Compress
    """
    output = _run(["powershell", "-NoProfile", "-NonInteractive", "-Command", script], 25)
    if not output:
        output = _run(["pwsh", "-NoProfile", "-NonInteractive", "-Command", script], 25)
    if output:
        try:
            data = json.loads(output)
            telemetry.update({key: data.get(key) for key in
                              ("cpu", "memory", "gpus", "disks", "physical_disks", "temperatures", "motherboard", "battery", "usb_devices")})
            for device in data.get("bad_devices") or []:
                code = device.get("ConfigManagerErrorCode")
                name = device.get("Name") or "Dispositivo sem nome"
                findings.append(_finding(f"PNP_CONFIG_{code}", f"Problema no dispositivo: {name}",
                    f"Windows ConfigManagerErrorCode={code}; PNP={device.get('PNPDeviceID') or 'indisponível'}.",
                    "warning", "WMI Win32_PnPEntity.ConfigManagerErrorCode",
                    "Confirme o hardware e instale driver oficial compatível; não use pacotes desconhecidos."))
            cpu = data.get("cpu") or {}
            load = cpu.get("load_percent")
            if isinstance(load, (int, float)) and load >= 98:
                findings.append(_finding("CPU_HIGH_UTILIZATION", "Uso de CPU muito elevado",
                    f"Win32_Processor reportou {load}% de utilização.", "warning",
                    "WMI Win32_Processor.LoadPercentage", "Investigue processos de alto consumo e repita a medição."))
            mem = data.get("memory") or {}
            total, free = mem.get("total_bytes"), mem.get("free_bytes")
            if isinstance(total, (int, float)) and total > 0 and isinstance(free, (int, float)):
                percent = free / total * 100
                telemetry["memory"]["free_percent"] = round(percent, 1)
                if percent < 5:
                    findings.append(_finding("MEMORY_PRESSURE", "Memória disponível muito baixa",
                        f"{percent:.1f}% de memória física livre.", "warning",
                        "WMI Win32_OperatingSystem.FreePhysicalMemory",
                        "Feche aplicativos desnecessários e investigue processos com consumo elevado."))
            for disk in data.get("disks") or []:
                status = str(disk.get("status") or "").lower()
                if status and status not in ("ok", "unknown"):
                    findings.append(_finding("DISK_REPORTED_UNHEALTHY", "Disco reportou estado não saudável",
                        f"{disk.get('model')}: status {disk.get('status')}.", "warning",
                        "WMI Win32_DiskDrive.Status",
                        "Faça backup imediato e verifique SMART com ferramenta oficial do fabricante."))
            for disk in data.get("physical_disks") or []:
                health = str(disk.get("health") or "").lower()
                operational = " ".join(str(x) for x in (disk.get("operational") or [])).lower()
                if health and health not in ("healthy", "unknown") or any(
                    token in operational for token in ("lost communication", "failed", "unhealthy")
                ):
                    findings.append(_finding("PHYSICAL_DISK_HEALTH_WARNING", "Disco físico reportou alerta de saúde",
                        f"{disk.get('name')}: health={disk.get('health')}; operational={operational}.",
                        "critical", "Get-PhysicalDisk", "Faça backup imediato e execute diagnóstico SMART do fabricante."))
            for gpu in data.get("gpus") or []:
                status = str(gpu.get("status") or "").lower()
                if status and status != "ok":
                    findings.append(_finding("GPU_DRIVER_OR_DEVICE_STATUS", "GPU reportou estado anormal",
                        f"{gpu.get('name')}: status {gpu.get('status')}; driver {gpu.get('driver_version')}.",
                        "warning", "WMI Win32_VideoController",
                        "Consulte o Gerenciador de Dispositivos e o driver oficial do fabricante."))
            for temp in data.get("temperatures") or []:
                raw = temp.get("CurrentTemperature")
                if isinstance(raw, (int, float)) and raw > 0:
                    celsius = round(raw / 10 - 273.15, 1)
                    temp["celsius"] = celsius
                    if celsius >= 90:
                        findings.append(_finding("THERMAL_HIGH", "Zona térmica reportou temperatura elevada",
                            f"{temp.get('InstanceName')}: {celsius} °C.", "warning",
                            "WMI root/wmi MSAcpi_ThermalZoneTemperature",
                            "Verifique ventilação e refrigeração; sensores ACPI podem não representar CPU/GPU."))
        except (json.JSONDecodeError, TypeError, AttributeError):
            telemetry["collection_error"] = "Resposta CIM não pôde ser interpretada."
            findings.append(_finding("WINDOWS_TELEMETRY_PARSE_ERROR", "Telemetria Windows indisponível",
                "O resultado CIM não pôde ser interpretado.", "info", "PowerShell/CIM",
                "Verifique PowerShell e permissões de consulta WMI."))
    else:
        telemetry["collection_error"] = "PowerShell/CIM indisponível."
        findings.append(_finding("WINDOWS_TELEMETRY_UNAVAILABLE", "Telemetria Windows indisponível",
            "PowerShell/CIM não respondeu; nenhum defeito foi presumido.", "info", "PowerShell/CIM",
            "Verifique a disponibilidade do PowerShell e das consultas WMI."))

    root = os.environ.get("SystemDrive", "C:") + "\\"
    try:
        usage = shutil.disk_usage(root)
        percent = round(usage.free / usage.total * 100, 1) if usage.total else 0
        telemetry["system_disk"] = {"mount": root, "total_bytes": usage.total,
                                    "free_bytes": usage.free, "free_percent": percent,
                                    "source": "shutil.disk_usage"}
        if percent < 5:
            findings.append(_finding("SYSTEM_DISK_LOW_SPACE", "Pouco espaço livre no disco do sistema",
                f"{percent}% livre em {root}.", "warning", "shutil.disk_usage",
                "Revise arquivos e faça backup antes de liberar espaço."))
    except OSError:
        pass
    return findings, telemetry


def _mac_checks() -> tuple[list[dict], dict]:
    telemetry = {"source": "macOS sysctl/system_profiler", "cpu": {}, "memory": {},
                 "gpu": [], "storage": [], "motherboard": {}}
    findings: list[dict] = []
    mem = _run(["sysctl", "-n", "hw.memsize"], 5)
    if mem and mem.isdigit():
        telemetry["memory"]["total_bytes"] = int(mem)
    profile = _run(["system_profiler", "SPHardwareDataType", "SPDisplaysDataType",
                    "SPStorageDataType", "-json"], 25)
    if profile:
        try:
            data = json.loads(profile)
            telemetry["system_profiler"] = data
        except json.JSONDecodeError:
            telemetry["system_profiler"] = "unparseable"
    return findings, telemetry


def _repair_guidance(findings: list[dict]) -> list[dict]:
    """Map detected failure classes to safe, evidence-based next actions."""
    guidance = {
        "CPU_HIGH_UTILIZATION": ("PROCESS_TRIAGE", "Identifique processos com alto consumo; não encerre processos do sistema automaticamente."),
        "MEMORY_PRESSURE": ("MEMORY_TRIAGE", "Identifique aplicativos que consomem memória; não altere arquivo de paginação automaticamente."),
        "DISK_ROOT_LOW_SPACE": ("STORAGE_CLEANUP_REVIEW", "Faça backup e revise arquivos temporários/pessoais antes de excluir qualquer dado."),
        "SYSTEM_DISK_LOW_SPACE": ("STORAGE_CLEANUP_REVIEW", "Faça backup e use a limpeza oficial do Windows; nenhuma exclusão automática será feita."),
        "DISK_SMART_FAILED": ("STORAGE_REPLACEMENT_REVIEW", "Priorize backup e substituição da unidade; não execute reparo intensivo que possa agravar falha física."),
        "PHYSICAL_DISK_HEALTH_WARNING": ("STORAGE_VENDOR_DIAGNOSTIC", "Faça backup e use diagnóstico oficial do fabricante; não tente reparar setores automaticamente."),
        "DISK_REPORTED_UNHEALTHY": ("STORAGE_VENDOR_DIAGNOSTIC", "Faça backup e valide SMART/diagnóstico oficial antes de qualquer reparo."),
        "THERMAL_HIGH": ("THERMAL_COOLING_INSPECTION", "Desligue se houver superaquecimento persistente; verifique ventilação e refrigeração com o equipamento desenergizado."),
        "PCI_DRIVER_MISSING": ("OFFICIAL_DRIVER_REVIEW", "Identifique o hardware e obtenha driver assinado no site do fabricante; instalação automática permanece bloqueada."),
        "GPU_DRIVER_OR_DEVICE_STATUS": ("GPU_VENDOR_DIAGNOSTIC", "Confirme o código no Gerenciador de Dispositivos e use driver oficial compatível."),
        "SYSTEM_ERROR_LOG_ENTRIES": ("EVENT_CORRELATION", "Correlacione os eventos com horário e dispositivo; logs isolados não justificam alteração automática."),
    }
    plans = []
    for finding in findings:
        code = str(finding.get("code", "UNKNOWN"))
        action, instruction = guidance.get(code, ("MANUAL_REVIEW", finding.get("recommendation", "Revisão técnica necessária.")))
        plans.append({
            "finding_code": code,
            "action": action,
            "status": "GUIDANCE_ONLY",
            "automatic_repair": False,
            "requires_user_consent": True,
            "instruction": instruction,
        })
    return plans


def run_diagnostics() -> dict:
    system = platform.system()
    if system == "Windows":
        findings, telemetry = _windows_checks()
    elif system == "Linux":
        findings, telemetry = _linux_checks()
    elif system == "Darwin":
        findings, telemetry = _mac_checks()
    else:
        findings, telemetry = [], {"source": "platform APIs", "availability": "unsupported platform"}
    virtual_runtime = ApoloVirtualIcRuntime().execute(findings, telemetry)
    corrected: list[dict] = []
    actionable = [item for item in findings if item.get("severity") != "info"]
    observations = [item for item in findings if item.get("severity") == "info"]
    return {
        "protocol": "apolo-diagnostic-report/2",
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "host": {"system": system, "release": platform.release(),
                 "architecture": platform.machine(), "hostname": platform.node()},
        "virtual_ic_runtime": virtual_runtime,
        "chips": {item["id"]: item for item in virtual_runtime["chips"]},
        "sensors": {"source": telemetry.get("source", "host operating system"),
                    "mode": "VIRTUAL_SOFTWARE_SENSORS",
                    "physical_measurements_available": False,
                    "telemetry": telemetry,
                    "note": "Sensores virtuais analisam dados reais expostos pelo sistema operacional; não substituem sensores elétricos físicos."},
        "summary": {"found": len(actionable), "corrected": 0, "not_corrected": len(actionable)},
        "findings": actionable, "observations": observations,
        "corrected": corrected, "not_corrected": actionable,
        "repair_policy": {"mode": "CONSENT_REQUIRED",
                          "available_actions": ["WINDOWS_COMPONENT_STORE_AND_SFC_REPAIR"] if system == "Windows" else [],
                          "reason": "DISM e SFC no Windows exigem confirmação explícita, privilégios adequados e verificação posterior; outras classes permanecem em diagnóstico até haver procedimento seguro específico."},
        "repair_plans": _repair_guidance(actionable),
        "recommendations": [item["recommendation"] for item in findings] or
            ["Nenhum problema foi confirmado pelas interfaces consultadas. Isso não prova ausência de defeitos."],
        "limitations": [
            "CPU/GPU/temperatura/disco/placa-mãe só são avaliados quando o firmware e o sistema operacional expõem dados utilizáveis.",
            "A leitura ACPI de temperatura não é necessariamente a temperatura da CPU ou GPU.",
            "A identidade SMBIOS/WMI não comprova fisicamente o modelo da placa-mãe.",
            "Não identifica trilhas rompidas, componentes queimados ou defeitos elétricos ocultos.",
        ],
    }


def _windows_is_admin() -> bool:
    if platform.system() != "Windows":
        return False
    try:
        import ctypes
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except (AttributeError, OSError):
        return False


def run_windows_system_file_repair(confirmed: bool) -> dict:
    """Repair Windows component store and protected files after app consent/admin check.

    DISM and SFC commands are fixed (no caller-supplied command execution). A repair
    is counted only when a clean post-check confirms the relevant subsystem.
    """
    if not confirmed:
        raise PermissionError("Ação recusada: confirmação explícita do usuário não recebida.")
    if platform.system() != "Windows":
        raise RuntimeError("Esta ação só está disponível no Windows.")
    if not _windows_is_admin():
        raise PermissionError("O agente precisa ser iniciado como Administrador para reparar componentes do Windows.")

    stages: list[dict] = []
    dism_scan = _run(["DISM", "/Online", "/Cleanup-Image", "/ScanHealth"], timeout=1800)
    if dism_scan is None:
        raise RuntimeError("A verificação DISM do armazenamento de componentes não pôde ser executada.")
    scan_lower = dism_scan.casefold()
    repairable = ("component store is repairable" in scan_lower or
                  "o armazenamento de componentes pode ser reparado" in scan_lower or
                  "o repositório de componentes pode ser reparado" in scan_lower)
    not_repairable = ("component store cannot be repaired" in scan_lower or
                      "o armazenamento de componentes não pode ser reparado" in scan_lower)
    clean_store = ("no component store corruption detected" in scan_lower or
                   "nenhuma corrupção do armazenamento de componentes foi detectada" in scan_lower or
                   "nenhuma corrupção no repositório de componentes foi detectada" in scan_lower)
    stages.append({"stage": "DISM_SCANHEALTH", "status":
                   "REPAIRABLE" if repairable else "UNREPAIRABLE" if not_repairable else
                   "CLEAN" if clean_store else "INDETERMINATE",
                   "output": dism_scan[-1200:]})

    dism_repaired = False
    if repairable:
        restore = _run(["DISM", "/Online", "/Cleanup-Image", "/RestoreHealth"], timeout=3600)
        if restore is None:
            return {"action": "WINDOWS_COMPONENT_STORE_AND_SFC_REPAIR", "status": "UNRESOLVED",
                    "verified": False, "corrected_count": 0, "stages": stages,
                    "message": "DISM identificou corrupção reparável, mas RestoreHealth não concluiu."}
        post_dism = _run(["DISM", "/Online", "/Cleanup-Image", "/ScanHealth"], timeout=1800)
        post_clean = bool(post_dism and (
            "no component store corruption detected" in post_dism.casefold() or
            "nenhuma corrupção do armazenamento de componentes foi detectada" in post_dism.casefold() or
            "nenhuma corrupção no repositório de componentes foi detectada" in post_dism.casefold()))
        stages.extend([
            {"stage": "DISM_RESTOREHEALTH", "status": "EXECUTED", "output": restore[-1200:]},
            {"stage": "DISM_POSTCHECK", "status": "CLEAN" if post_clean else "NOT_CONFIRMED",
             "output": (post_dism or "Verificação posterior indisponível.")[-1200:]}
        ])
        if not post_clean:
            return {"action": "WINDOWS_COMPONENT_STORE_AND_SFC_REPAIR", "status": "UNRESOLVED",
                    "verified": False, "corrected_count": 0, "stages": stages,
                    "message": "O armazenamento de componentes continua sem verificação limpa. O APOLO não contará o reparo como concluído."}
        dism_repaired = True
    elif not_repairable:
        return {"action": "WINDOWS_COMPONENT_STORE_AND_SFC_REPAIR", "status": "UNRESOLVED",
                "verified": False, "corrected_count": 0, "stages": stages,
                "message": "DISM informou que o armazenamento de componentes não pode ser reparado automaticamente."}

    before = _run(["sfc", "/verifyonly"], timeout=1200)
    if before is None:
        raise RuntimeError("A verificação inicial SFC não pôde ser executada.")
    lower_before = before.casefold()
    no_issues = ("did not find any integrity violations" in lower_before or
                 "não encontrou nenhuma violação de integridade" in lower_before)
    if no_issues:
        return {"action": "WINDOWS_COMPONENT_STORE_AND_SFC_REPAIR",
                "status": "VERIFIED_REPAIRED" if dism_repaired else "NOT_NEEDED",
                "verified": True, "corrected_count": 1 if dism_repaired else 0,
                "stages": stages + [{"stage": "SFC_VERIFYONLY", "status": "CLEAN", "output": before[-1200:]}],
                "message": "DISM/SFC concluíram as verificações; a integridade foi confirmada."}

    repair = _run(["sfc", "/scannow"], timeout=2400)
    if repair is None:
        raise RuntimeError("O Verificador de Arquivos do Sistema não concluiu.")
    verify = _run(["sfc", "/verifyonly"], timeout=1200)
    if verify is None:
        return {"action": "WINDOWS_COMPONENT_STORE_AND_SFC_REPAIR", "status": "UNVERIFIED",
                "verified": False, "corrected_count": 0, "stages": stages,
                "message": "SFC foi executado, mas a verificação posterior não pôde ser concluída.",
                "repair_output": repair[-1200:]}
    lower_verify = verify.casefold()
    verified = ("did not find any integrity violations" in lower_verify or
                "não encontrou nenhuma violação de integridade" in lower_verify)
    repaired_phrase = ("successfully repaired" in repair.casefold() or
                       "reparou com êxito" in repair.casefold() or
                       "repaired them" in repair.casefold())
    sfc_repaired = verified and repaired_phrase
    stages.extend([
        {"stage": "SFC_SCANNOW", "status": "REPAIR_REPORTED" if repaired_phrase else "NO_REPAIR_CONFIRMATION",
         "output": repair[-1200:]},
        {"stage": "SFC_POSTCHECK", "status": "CLEAN" if verified else "NOT_CLEAN",
         "output": verify[-1200:]}
    ])
    changed_and_verified = sfc_repaired or (dism_repaired and verified)
    return {"action": "WINDOWS_COMPONENT_STORE_AND_SFC_REPAIR",
            "status": "VERIFIED_REPAIRED" if changed_and_verified else
                      "VERIFIED_CLEAN" if verified else "UNRESOLVED",
            "verified": verified, "corrected_count": 1 if changed_and_verified else 0,
            "stages": stages,
            "message": "A verificação posterior confirmou a integridade." if verified else
                       "A verificação posterior ainda encontrou problemas ou não confirmou a integridade."}
