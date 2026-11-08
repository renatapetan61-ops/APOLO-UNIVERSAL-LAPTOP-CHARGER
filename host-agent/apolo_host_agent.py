#!/usr/bin/env python3
"""APOLO read-only host inventory agent (Windows/Linux/macOS).

Collects OS/firmware/hardware inventory and power/battery telemetry exposed by
the OS. It never probes electrical pins, changes power settings, or authorizes
charging. DC barrel-jack voltage and polarity remain UNMEASURED unless a
separate, validated isolated measurement front-end supplies authenticated data.
"""
from __future__ import annotations

import json
import os
import platform
import re
import socket
import subprocess
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from amis_camera import discover_cameras, capture_frame
from amis_virtual_camera import AMISVirtualCameraCore
from amis_vision_engine import AMISMotherboardVisionEngine
from amis_hardware_mapper import map_components, render_svg
from apolo_diagnostics import run_diagnostics

HOST, PORT = "127.0.0.1", 8765
PROTOCOL = "apolo-host-agent/4"
VIRTUAL_CAMERA = AMISVirtualCameraCore()
VISION_ENGINE = AMISMotherboardVisionEngine()


def read_text(path: str) -> str | None:
    try:
        value = Path(path).read_text(errors="replace").strip()
        return value or None
    except (OSError, PermissionError):
        return None


def run_readonly(args: list[str], timeout: int = 8) -> str | None:
    try:
        p = subprocess.run(args, capture_output=True, text=True,
                           timeout=timeout, check=False)
        return p.stdout.strip() if p.returncode == 0 and p.stdout.strip() else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def linux_inventory() -> dict:
    dmi = {
        "manufacturer": read_text("/sys/class/dmi/id/sys_vendor"),
        "product_name": read_text("/sys/class/dmi/id/product_name"),
        "product_version": read_text("/sys/class/dmi/id/product_version"),
        "board_manufacturer": read_text("/sys/class/dmi/id/board_vendor"),
        "board_name": read_text("/sys/class/dmi/id/board_name"),
        "bios_vendor": read_text("/sys/class/dmi/id/bios_vendor"),
        "bios_version": read_text("/sys/class/dmi/id/bios_version"),
        "bios_date": read_text("/sys/class/dmi/id/bios_date"),
        "product_uuid": read_text("/sys/class/dmi/id/product_uuid"),
    }
    batteries, adapters = [], []
    root = Path("/sys/class/power_supply")
    try:
        entries = list(root.iterdir())
    except OSError:
        entries = []
    for entry in entries:
        typ = read_text(str(entry / "type"))
        item = {"name": entry.name, "type": typ}
        for key in ("manufacturer", "model_name", "technology", "status",
                    "capacity", "voltage_now", "current_now", "power_now",
                    "energy_now", "energy_full", "online"):
            val = read_text(str(entry / key))
            if val is not None:
                item[key] = val
        if typ == "Battery":
            batteries.append(item)
        elif typ in ("Mains", "USB", "USB_C"):
            adapters.append(item)
    cpu_model = None
    cpuinfo = read_text("/proc/cpuinfo") or ""
    for line in cpuinfo.splitlines():
        if line.lower().startswith(("model name", "hardware")) and ":" in line:
            cpu_model = line.split(":", 1)[1].strip()
            break
    mem_total = None
    meminfo = read_text("/proc/meminfo") or ""
    for line in meminfo.splitlines():
        if line.startswith("MemTotal:"):
            mem_total = line.split(":", 1)[1].strip()
            break
    pci_text = run_readonly(["lspci"], timeout=5) or ""
    storage = []
    try:
        for dev in Path("/sys/block").iterdir():
            if dev.name.startswith(("loop", "ram", "zram")):
                continue
            storage.append({"name": dev.name, "model": read_text(str(dev / "device/model"))})
    except OSError:
        pass
    return {"firmware_hardware": dmi, "batteries": batteries,
            "power_supplies": adapters, "cpu_model": cpu_model,
            "memory_total": mem_total, "pci_devices": pci_text.splitlines(),
            "storage_devices": storage}


def windows_inventory() -> dict:
    script = r"""
    $cs=Get-CimInstance Win32_ComputerSystem
    $bios=Get-CimInstance Win32_BIOS
    $bb=Get-CimInstance Win32_BaseBoard
    $cpu=Get-CimInstance Win32_Processor | Select-Object -First 1
    $bat=Get-CimInstance Win32_Battery | Select-Object Name,DeviceID,Status,
      BatteryStatus,EstimatedChargeRemaining,DesignVoltage,PNPDeviceID
    $gpu=Get-CimInstance Win32_VideoController | Select-Object Name,DriverVersion
    $mem=Get-CimInstance Win32_ComputerSystem
    $disk=Get-CimInstance Win32_DiskDrive | Select-Object Model,Size,DeviceID
    $pnp=Get-CimInstance Win32_PnPEntity | Where-Object {$_.PNPClass -in @('System','USB','SCSIAdapter','HDC','Display')} | Select-Object -First 80 Name,PNPDeviceID
    [pscustomobject]@{
      computer=@{manufacturer=$cs.Manufacturer;model=$cs.Model;systemType=$cs.SystemType}
      bios=@{manufacturer=$bios.Manufacturer;version=($bios.SMBIOSBIOSVersion -join ' ');serial=$bios.SerialNumber;releaseDate=$bios.ReleaseDate}
      baseboard=@{manufacturer=$bb.Manufacturer;product=$bb.Product;version=$bb.Version}
      cpu=@{name=$cpu.Name;cores=$cpu.NumberOfCores;logicalProcessors=$cpu.NumberOfLogicalProcessors}
      batteries=@($bat)
      gpus=@($gpu)
      memory=@{total_gb=[math]::Round($mem.TotalPhysicalMemory/1GB,2)}
      disks=@($disk | ForEach-Object {@{model=$_.Model;size_gb=[math]::Round($_.Size/1GB,2);name=$_.DeviceID}})
      controllers=@($pnp | ForEach-Object {@{name=$_.Name;device_id=$_.PNPDeviceID}})
    } | ConvertTo-Json -Depth 6 -Compress
    """
    out = run_readonly(["powershell", "-NoProfile", "-NonInteractive",
                        "-Command", script], timeout=15)
    if not out:
        out = run_readonly(["pwsh", "-NoProfile", "-NonInteractive",
                            "-Command", script], timeout=15)
    if out:
        try:
            return json.loads(out)
        except json.JSONDecodeError:
            pass
    return {"inventory_error": "CIM inventory unavailable or not permitted"}


def mac_inventory() -> dict:
    out = run_readonly(["system_profiler", "SPHardwareDataType",
                        "SPPowerDataType", "-json"], timeout=20)
    if out:
        try:
            return json.loads(out)
        except json.JSONDecodeError:
            pass
    return {"inventory_error": "system_profiler unavailable"}



def board_identity_evidence(inventory: dict) -> dict:
    """Preserve raw electronic board identity clues and their provenance."""
    if platform.system() == "Linux":
        raw = inventory.get("firmware_hardware", {})
        fields = {
            "manufacturer": raw.get("board_manufacturer"),
            "product": raw.get("board_name"),
            "version": raw.get("product_version"),
            "system_manufacturer": raw.get("manufacturer"),
            "system_model": raw.get("product_name"),
            "bios_vendor": raw.get("bios_vendor"),
            "bios_version": raw.get("bios_version"),
        }
    elif platform.system() == "Windows":
        board = inventory.get("baseboard", {})
        computer = inventory.get("computer", {})
        bios = inventory.get("bios", {})
        fields = {
            "manufacturer": board.get("manufacturer"),
            "product": board.get("product"),
            "version": board.get("version"),
            "system_manufacturer": computer.get("manufacturer"),
            "system_model": computer.get("model"),
            "bios_vendor": bios.get("manufacturer"),
            "bios_version": bios.get("version"),
        }
    else:
        fields = {"note": "Platform-specific baseboard mapping unavailable"}
    return {
        "source": "OS/SMBIOS/WMI; informational, not cryptographic proof",
        "raw_fields": fields,
        "exact_board_code": None,
        "result": "UNKNOWN",
    }


def snapshot() -> dict:
    system = platform.system()
    result = {
        "protocol": PROTOCOL,
        "system": system,
        "system_release": platform.release(),
        "machine_architecture": platform.machine(),
        "hostname": socket.gethostname(),
        "identity_source": "operating-system-and-firmware-inventory",
        "inventory": {},
        "dc_jack_voltage_v": None,
        "dc_jack_polarity": "UNMEASURED",
        "dc_measurement_available": False,
        "charging_authorized": False,
        "electrical_measurement_note":
            "OS inventory and adapter-present telemetry are not a measurement "
            "of voltage or polarity at the physical DC jack.",
        "limitations": [
            "Some fields require administrator privileges or vendor drivers",
            "OS-reported identity is not cryptographic proof of physical identity",
            "Battery/AC adapter telemetry does not expose DC jack pin polarity",
            "A validated isolated measurement circuit is required for real DC readings"
        ],
    }
    if system == "Linux":
        result["inventory"] = linux_inventory()
    elif system == "Windows":
        result["inventory"] = windows_inventory()
    elif system == "Darwin":
        result["inventory"] = mac_inventory()
    else:
        result["inventory"] = {"note": "Unsupported OS; basic platform data only"}
    result["motherboard_electronic_evidence"] = board_identity_evidence(result["inventory"])
    result["hardware_map"] = map_components(system, result["inventory"])
    return result


def amis_status() -> dict:
    """Describe the complete camera-to-vision pipeline without claiming a camera is connected."""
    return {
        "protocol": "amis-integrated-pipeline/2",
        "status": "READY_FOR_IMAGE_SOURCE",
        "components": {
            "hardware_mapper": {"protocol": "amis-hardware-map/1", "status": "READ_ONLY_INVENTORY_AND_SVG_READY"},
            "virtual_camera_core": VIRTUAL_CAMERA.status(),
            "motherboard_vision_engine": {
                "protocol": VISION_ENGINE.PROTOCOL,
                "local_ocr": True,
                "catalogue_cross_check": True,
                "requires_real_image_frame": True,
            },
        },
        "hardware_mapping": {
            "json_endpoint": "GET /v1/hardware/map",
            "svg_endpoint": "GET /v1/hardware/map.svg",
            "physical_coordinates": "UNKNOWN_UNLESS_VERIFIED",
        },
        "image_sources": {
            "android_camera": {
                "transport": "HTTP POST /v1/virtual-camera/frames",
                "connection": "owner-authorized ADB reverse bridge or same-host loopback",
                "status": "CLIENT_ENDPOINT_AVAILABLE; phone camera must be opened by the Android app",
            },
            "android_camera_x": {
                "transport": "HTTP POST /v1/virtual-camera/frames",
                "status": "LEGACY_ALIAS; same Android CameraX source",
            },
            "usb_uvc_camera": {
                "transport": "host-local OpenCV capture via /v1/camera/capture",
                "discovery": discover_cameras(),
                "status": "DETECTED_ONLY_IF_ENUMERATED; physical optical access still required",
            },
            "shared_pipeline": {
                "core": "AMIS Virtual Camera Core",
                "vision": "AMIS Motherboard Vision Engine",
                "accepts_multiple_sources": True,
                "fusion_policy": "per-frame OCR with source provenance; no false stereo/depth reconstruction",
            },
        },
        "inspection_requirements": {
            "real_camera_required": True,
            "direct_line_of_sight_to_motherboard_required": True,
            "opaque_chassis_transparency": False,
            "catalogue_identity_confirmation_required": True,
        },
        "charging": {
            "authorization": "DENIED",
            "dc_jack_voltage": None,
            "dc_jack_polarity": "UNMEASURED",
        },
    }


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == "/v1/diagnostics/run":
            payload = run_diagnostics()
            body = json.dumps(payload, separators=(",", ":"), default=str).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)
            return
        if self.path == "/v1/camera/capture":
            image_data, source_info = capture_frame()
            if image_data is None:
                body = json.dumps(source_info, separators=(",", ":")).encode()
                self.send_response(503)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(body)
                return
            try:
                frame = VIRTUAL_CAMERA.ingest(image_data, source_id="uvc-camera-0")
                result = VISION_ENGINE.inspect(frame, snapshot().get("motherboard_electronic_evidence", {}), Path(__file__).with_name("board_catalogue.json"))
                result["physical_source"] = source_info
                result["hardware_map_summary"] = snapshot().get("hardware_map", {})
                body = json.dumps(result, separators=(",", ":"), default=str).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(body)
            except (ValueError, OSError):
                self.send_error(400)
            return
        if self.path not in ("/v1/board-inspection", "/v1/virtual-camera/frames"):
            self.send_error(404)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length < 1 or length > 8 * 1024 * 1024:
                self.send_error(413)
                return
            image_data = self.rfile.read(length)
            if len(image_data) != length:
                self.send_error(400)
                return
            source_id = self.headers.get("X-AMIS-Source", "android-camerax")
            frame = VIRTUAL_CAMERA.ingest(image_data, source_id=source_id)
            evidence = snapshot().get("motherboard_electronic_evidence", {})
            result = VISION_ENGINE.inspect(
                frame, evidence, Path(__file__).with_name("board_catalogue.json")
            )
            result["hardware_map_summary"] = snapshot().get("hardware_map", {})
            body = json.dumps(result, separators=(",", ":"), default=str).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)
        except ValueError as exc:
            self.send_error(400, str(exc))
        except OSError:
            self.send_error(500)

    def do_GET(self):
        if self.path == "/v1/amis/status":
            payload = amis_status()
        elif self.path == "/v1/virtual-camera/status":
            payload = VIRTUAL_CAMERA.status()
        elif self.path == "/v1/camera":
            payload = discover_cameras()
        elif self.path == "/v1/inventory":
            payload = snapshot()
        elif self.path == "/v1/hardware/map":
            payload = snapshot().get("hardware_map", {})
        elif self.path == "/v1/hardware/map.svg":
            svg = render_svg(snapshot().get("hardware_map", {}))
            self.send_response(200)
            self.send_header("Content-Type", "image/svg+xml; charset=utf-8")
            self.send_header("Content-Length", str(len(svg)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(svg)
            return
        else:
            self.send_error(404)
            return
        body = json.dumps(payload, separators=(",", ":"), default=str).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_):
        pass


def enable_authorized_adb_reverse() -> str:
    """Expose this loopback-only agent to Android only when ADB is already authorized."""
    try:
        result = subprocess.run(["adb", "reverse", f"tcp:{PORT}", f"tcp:{PORT}"],
                                capture_output=True, text=True, timeout=8, check=False)
        if result.returncode == 0:
            return "ADB reverse ativo; Android pode acessar 127.0.0.1:8765."
        detail = (result.stderr or result.stdout or "dispositivo não autorizado").strip()
        return f"ADB reverse indisponível: {detail[:240]}"
    except FileNotFoundError:
        return "ADB não encontrado. Instale Android Platform Tools e autorize a depuração USB no telefone."
    except (OSError, subprocess.TimeoutExpired) as exc:
        return f"Não foi possível configurar ADB reverse: {exc}"


if __name__ == "__main__":
    print(f"APOLO read-only inventory agent: http://{HOST}:{PORT}/v1/inventory")
    print(enable_authorized_adb_reverse())
    print("DC jack voltage/polarity: UNMEASURED; charging authorization: DENIED")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
