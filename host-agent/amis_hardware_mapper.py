"""AMIS Hardware Mapper: read-only OS inventory and schematic SVG rendering.

The generated SVG is a logical inventory map, not an X-ray or a verified
physical-layout drawing. Physical coordinates remain unknown unless supplied
by an independently verified service-manual/catalogue source.
"""
from __future__ import annotations

import html
from datetime import datetime, timezone


def _add(items, category, label, detail=None, evidence="OS inventory"):
    if label and str(label).strip():
        items.append({
            "id": f"node-{len(items)+1}",
            "category": category,
            "label": str(label).strip()[:120],
            "detail": str(detail).strip()[:180] if detail else None,
            "evidence": evidence,
            "physical_location": "UNKNOWN",
        })


def map_components(system: str, inventory: dict) -> dict:
    nodes = []
    if system == "Windows":
        computer = inventory.get("computer", {})
        board = inventory.get("baseboard", {})
        cpu = inventory.get("cpu", {})
        gpu_list = inventory.get("gpus", [])
        memory = inventory.get("memory", {})
        disks = inventory.get("disks", [])
        batteries = inventory.get("batteries", [])
        controllers = inventory.get("controllers", [])
        _add(nodes, "system", computer.get("model"), computer.get("manufacturer"))
        _add(nodes, "motherboard", board.get("product") or board.get("manufacturer"),
             board.get("version"), "Windows CIM Win32_BaseBoard")
        _add(nodes, "cpu", cpu.get("name"), f"cores={cpu.get('cores')}; logical={cpu.get('logicalProcessors')}")
        for g in gpu_list:
            _add(nodes, "gpu", g.get("name"), g.get("driver"))
        _add(nodes, "memory", memory.get("total_gb"), "Installed physical memory (GiB)")
        for d in disks:
            _add(nodes, "storage", d.get("model") or d.get("name"), d.get("size"))
        for b in batteries:
            _add(nodes, "battery", b.get("name"), b.get("status"))
        for d in controllers:
            _add(nodes, "controller", d.get("name"), d.get("device_id"), "Windows PnP inventory")
    elif system == "Linux":
        dmi = inventory.get("firmware_hardware", {})
        _add(nodes, "system", dmi.get("product_name"), dmi.get("manufacturer"))
        _add(nodes, "motherboard", dmi.get("board_name") or dmi.get("board_manufacturer"),
             dmi.get("product_version"), "Linux DMI sysfs")
        _add(nodes, "cpu", inventory.get("cpu_model"), inventory.get("cpu_cores"))
        _add(nodes, "memory", inventory.get("memory_total"), "MemTotal from /proc/meminfo")
        for g in inventory.get("pci_devices", []):
            kind = "gpu" if any(t in g.lower() for t in ("vga", "3d controller", "display controller")) else "controller"
            _add(nodes, kind, g, evidence="lspci")
        for d in inventory.get("storage_devices", []):
            _add(nodes, "storage", d.get("name"), d.get("model"), "sysfs block inventory")
        for b in inventory.get("batteries", []):
            _add(nodes, "battery", b.get("name"), b.get("status"))
    else:
        _add(nodes, "system", inventory.get("SPHardwareDataType"), "macOS system_profiler data")
    return {
        "protocol": "amis-hardware-map/1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": "read-only operating-system inventory",
        "node_count": len(nodes),
        "nodes": nodes,
        "edges": [
            {"from": n["id"], "to": "node-1", "relationship": "system-associated"}
            for n in nodes[1:]
        ] if nodes else [],
        "physical_layout": "NOT_DETERMINED",
        "motherboard_position": "UNKNOWN_UNLESS_SERVICE_DATA_OR_REAL_IMAGE_CONFIRMS",
        "limitations": [
            "This is a logical component inventory, not a physical x-ray.",
            "OS APIs do not provide reliable x/y positions of parts inside the chassis.",
            "Unreported components are omitted rather than guessed.",
            "Motherboard identification from DMI/SMBIOS is evidence, not proof.",
        ],
    }


def render_svg(mapping: dict) -> bytes:
    nodes = mapping.get("nodes", [])
    width, row_h, top = 960, 88, 120
    height = max(300, top + max(1, len(nodes)) * row_h + 80)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#101820"/>',
        '<text x="40" y="48" fill="#ffffff" font-size="26" font-family="Arial" font-weight="bold">AMIS — Mapa lógico de hardware</text>',
        '<text x="40" y="78" fill="#b8c7d1" font-size="14" font-family="Arial">Inventário do sistema operacional • posições físicas não verificadas</text>',
        '<rect x="40" y="96" width="880" height="54" rx="10" fill="#263746" stroke="#6d8798"/>',
        '<text x="60" y="129" fill="#ffffff" font-size="18" font-family="Arial">NOTEBOOK / SISTEMA</text>',
    ]
    if not nodes:
        parts.append('<text x="60" y="205" fill="#ffd27d" font-size="18" font-family="Arial">Nenhum componente identificável foi retornado pelo sistema.</text>')
    for i, node in enumerate(nodes):
        y = top + i * row_h
        label = html.escape(str(node.get("label", "Desconhecido")))
        detail = html.escape(str(node.get("detail") or "Detalhes não informados"))
        category = html.escape(str(node.get("category", "component")).upper())
        parts.extend([
            f'<path d="M480 150 V{y+34}" stroke="#58758a" stroke-width="2" fill="none"/>',
            f'<rect x="90" y="{y}" width="780" height="68" rx="10" fill="#1d2b36" stroke="#5d7d91"/>',
            f'<text x="112" y="{y+24}" fill="#80d4c4" font-size="12" font-family="Arial">{category}</text>',
            f'<text x="112" y="{y+47}" fill="#ffffff" font-size="17" font-family="Arial">{label}</text>',
            f'<text x="560" y="{y+39}" fill="#b8c7d1" font-size="13" font-family="Arial">{detail}</text>',
        ])
    footer_y = height - 24
    parts.append(f'<text x="40" y="{footer_y}" fill="#ffd27d" font-size="12" font-family="Arial">AVISO: diagrama lógico; não representa posições internas verificadas nem imagem fotográfica.</text>')
    parts.append("</svg>")
    return "".join(parts).encode("utf-8")
