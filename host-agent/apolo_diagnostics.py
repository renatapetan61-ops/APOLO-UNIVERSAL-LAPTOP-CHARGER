"""APOLO diagnostic engine: read-only checks against evidence exposed by the host OS.

This module deliberately does not invent sensor readings or perform destructive
repairs. Every finding records its source and evidence. A repair is counted only
when a separately implemented action returns a verifiable postcondition.
"""
from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from apolo_virtual_ics import ApoloVirtualIcRuntime


def _run(args: list[str], timeout: int = 12) -> str | None:
    try:
        result = subprocess.run(args, capture_output=True, text=True,
                                timeout=timeout, check=False)
        return result.stdout.strip() if result.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def _finding(code: str, title: str, detail: str, severity: str,
             source: str, recommendation: str) -> dict:
    return {
        "code": code, "title": title, "detail": detail,
        "severity": severity, "source": source,
        "recommendation": recommendation,
        "status": "FOUND",
    }


def _linux_checks() -> list[dict]:
    findings: list[dict] = []
    try:
        usage = shutil.disk_usage("/")
        free_percent = usage.free / usage.total * 100 if usage.total else 0
        if free_percent < 5:
            findings.append(_finding(
                "DISK_ROOT_LOW_SPACE", "Pouco espaço livre na partição raiz",
                f"{free_percent:.1f}% livre em /", "warning",
                "shutil.disk_usage(/)",
                "Revise arquivos pessoais e pacotes; faça backup antes de remover dados."
            ))
    except OSError:
        pass

    mem = Path("/proc/meminfo")
    try:
        values = {}
        for line in mem.read_text().splitlines():
            key, _, rest = line.partition(":")
            if key in ("MemAvailable", "MemTotal"):
                values[key] = int(rest.strip().split()[0])
        if values.get("MemTotal") and values.get("MemAvailable") is not None:
            available = values["MemAvailable"] / values["MemTotal"] * 100
            if available < 5:
                findings.append(_finding(
                    "MEMORY_PRESSURE", "Memória disponível muito baixa",
                    f"{available:.1f}% da memória total disponível",
                    "warning", "/proc/meminfo",
                    "Feche aplicativos que não estiver usando e verifique processos com consumo elevado."
                ))
    except (OSError, ValueError, IndexError):
        pass

    journal = _run(["journalctl", "-p", "err", "-n", "30", "--no-pager"], 8)
    if journal:
        lines = [line for line in journal.splitlines() if line.strip()]
        if lines:
            findings.append(_finding(
                "SYSTEM_ERROR_LOG_ENTRIES", "Eventos de erro registrados pelo sistema",
                f"{len(lines)} linha(s) de erro recente(s) disponíveis no journal. Consulte os detalhes antes de atribuir causa.",
                "info", "journalctl -p err -n 30",
                "Analise os eventos e correlacione horários, serviços e dispositivos antes de alterar o sistema."
            ))
    return findings


def _windows_checks() -> list[dict]:
    findings: list[dict] = []
    script = r"""
    $bad = @(Get-CimInstance Win32_PnPEntity -ErrorAction SilentlyContinue |
      Where-Object { $_.ConfigManagerErrorCode -ne $null -and $_.ConfigManagerErrorCode -ne 0 } |
      Select-Object -First 80 Name,PNPDeviceID,ConfigManagerErrorCode)
    if ($bad.Count -eq 0) { '[]' } else { ConvertTo-Json -InputObject @($bad) -Depth 4 -Compress }
    """
    output = _run(["powershell", "-NoProfile", "-NonInteractive",
                   "-Command", script], 18) or _run(
        ["pwsh", "-NoProfile", "-NonInteractive", "-Command", script], 18)
    if output:
        try:
            devices = json.loads(output)
            if isinstance(devices, dict):
                devices = [devices]
            for device in devices or []:
                code = device.get("ConfigManagerErrorCode")
                name = device.get("Name") or "Dispositivo sem nome"
                findings.append(_finding(
                    f"PNP_CONFIG_{code}", f"Problema no dispositivo: {name}",
                    f"Windows ConfigManagerErrorCode={code}; identificador={device.get('PNPDeviceID') or 'indisponível'}",
                    "warning", "WMI Win32_PnPEntity.ConfigManagerErrorCode",
                    "Identifique o fabricante e o driver correto. Não instale drivers de origem desconhecida."
                ))
        except (json.JSONDecodeError, TypeError):
            findings.append(_finding(
                "PNP_SCAN_UNAVAILABLE", "Não foi possível interpretar a verificação de dispositivos",
                "O Windows não retornou uma resposta WMI válida.", "info",
                "PowerShell/CIM", "Execute novamente com as permissões necessárias."
            ))
    else:
        findings.append(_finding(
            "PNP_SCAN_UNAVAILABLE", "Verificação de dispositivos indisponível",
            "PowerShell/CIM não respondeu; nenhum erro de dispositivo foi presumido.",
            "info", "PowerShell/CIM",
            "Verifique a disponibilidade do PowerShell e das consultas WMI."
        ))

    try:
        root = os.environ.get("SystemDrive", "C:") + "\\"
        usage = shutil.disk_usage(root)
        free_percent = usage.free / usage.total * 100 if usage.total else 0
        if free_percent < 5:
            findings.append(_finding(
                "SYSTEM_DISK_LOW_SPACE", "Pouco espaço livre no disco do sistema",
                f"{free_percent:.1f}% livre em {root}", "warning",
                "shutil.disk_usage", "Revise arquivos e faça backup antes de liberar espaço."
            ))
    except OSError:
        pass
    return findings


def run_diagnostics() -> dict:
    """Run evidence-backed, non-destructive host checks and return app-ready report."""
    system = platform.system()
    if system == "Windows":
        findings = _windows_checks()
    elif system == "Linux":
        findings = _linux_checks()
    else:
        findings = []

    # Execute four independent virtual controllers over OS-derived evidence.
    # No repair is claimed: no approved, verifiable mutation actions exist yet.
    corrected: list[dict] = []
    virtual_runtime = ApoloVirtualIcRuntime().execute(findings)
    return {
        "protocol": "apolo-diagnostic-report/1",
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "host": {
            "system": system,
            "release": platform.release(),
            "architecture": platform.machine(),
            "hostname": platform.node(),
        },
        "virtual_ic_runtime": virtual_runtime,
        "chips": {item["id"]: item for item in virtual_runtime["chips"]},
        "sensors": {
            "source": "host-operating-system",
            "mode": "VIRTUAL_SOFTWARE_SENSORS",
            "physical_measurements_available": False,
            "note": "Sensores virtuais processam somente dados realmente expostos pelo sistema operacional; não medem sinais elétricos da placa."
        },
        "summary": {
            "found": len(findings),
            "corrected": len(corrected),
            "not_corrected": len(findings) - len(corrected),
        },
        "findings": findings,
        "corrected": corrected,
        "not_corrected": findings,
        "repair_policy": {
            "mode": "READ_ONLY",
            "reason": "Nenhuma ação de alteração do sistema foi habilitada sem regra de segurança, autorização e pós-condição verificável.",
        },
        "recommendations": [
            item["recommendation"] for item in findings
        ] or ["Nenhum problema foi confirmado pelas verificações disponíveis. Mantenha o sistema e os drivers atualizados e faça backups regulares."],
        "limitations": [
            "A inspeção cobre somente informações expostas pelo sistema operacional.",
            "Não identifica todos os defeitos de hardware ou da placa-mãe.",
            "Não altera drivers, firmware, arquivos ou configurações nesta versão.",
            "A ausência de achados não prova que o notebook esteja livre de defeitos.",
        ],
    }
