#!/usr/bin/env python3
"""Cross-language contract smoke tests. Binaries are compiled by the CI workflow."""
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GOOD = "APOLO1\tcpu_load\t12.5\tHOST_OS\t/proc/stat\t1731170000000\n"
BAD = "APOLO1\tcpu_load\t12.5\tTEST_FIXTURE\tunit-test\t1731170000000\n"

def run(name, command, expect=0):
    result = subprocess.run(command, input=GOOD if expect == 0 else BAD,
                            text=True, capture_output=True, cwd=ROOT)
    if result.returncode != expect:
        raise AssertionError(f"{name}: exit {result.returncode}, expected {expect}; {result.stdout} {result.stderr}")
    expected = "ACCEPTED" if expect == 0 else "REJECTED"
    if expected not in result.stdout:
        raise AssertionError(f"{name}: missing {expected}: {result.stdout}")
    print(f"PASS {name}: {expected}")

run("Python", [sys.executable, "sensor-contract/python/adapter.py"])\nrun("Python fixture rejection", [sys.executable, "sensor-contract/python/adapter.py"], 2)
run("C", ["/tmp/apolo-contract-c"])\nrun("C fixture rejection", ["/tmp/apolo-contract-c"], 2)
run("C++", ["/tmp/apolo-contract-cpp"])\nrun("C++ fixture rejection", ["/tmp/apolo-contract-cpp"], 2)
run("Rust", ["/tmp/apolo-contract-rust"])\nrun("Rust fixture rejection", ["/tmp/apolo-contract-rust"], 2)
run("Go", ["go", "run", "sensor-contract/go/adapter.go"])\nrun("Go fixture rejection", ["go", "run", "sensor-contract/go/adapter.go"], 2)
run("C#", ["dotnet", "run", "--project", "/tmp/apolo-contract-csharp", "--no-build"])\nrun("C# fixture rejection", ["dotnet", "run", "--project", "/tmp/apolo-contract-csharp", "--no-build"], 2)
run("Java", ["java", "-cp", "/tmp/apolo-contract-java", "Adapter"])\nrun("Java fixture rejection", ["java", "-cp", "/tmp/apolo-contract-java", "Adapter"], 2)
run("Swift", ["/tmp/apolo-contract-swift"])\nrun("Swift fixture rejection", ["/tmp/apolo-contract-swift"], 2)
run("JavaScript", ["node", "sensor-contract/javascript/adapter.js"])\nrun("JavaScript fixture rejection", ["node", "sensor-contract/javascript/adapter.js"], 2)
run("TypeScript", ["node", "/tmp/apolo-contract-ts/adapter.js"])\nrun("TypeScript fixture rejection", ["node", "/tmp/apolo-contract-ts/adapter.js"], 2)
run("PowerShell", ["pwsh", "-NoProfile", "-File", "sensor-contract/powershell/adapter.ps1"])\nrun("PowerShell fixture rejection", ["pwsh", "-NoProfile", "-File", "sensor-contract/powershell/adapter.ps1"], 2)
run("Bash", ["bash", "sensor-contract/bash/adapter.sh"])\nrun("Bash fixture rejection", ["bash", "sensor-contract/bash/adapter.sh"], 2)

db = sqlite3.connect(":memory:")
db.executescript((ROOT / "sensor-contract/sql/schema.sql").read_text())
db.execute("INSERT INTO sensor_observations(name,value,origin,source,observed_at_ms) VALUES(?,?,?,?,?)",
           ("cpu_load", "12.5", "HOST_OS", "/proc/stat", 1731170000000))
try:
    db.execute("INSERT INTO sensor_observations(name,value,origin,source,observed_at_ms) VALUES(?,?,?,?,?)",
               ("cpu_load", "12.5", "TEST_FIXTURE", "unit-test", 1731170000000))
    raise AssertionError("SQL accepted TEST_FIXTURE origin")
except sqlite3.IntegrityError:
    print("PASS SQL: TEST_FIXTURE rejected")

sv = subprocess.run(["vvp", "/tmp/apolo-contract-sv"], text=True, capture_output=True)
if sv.returncode != 0 or "SYSTEMVERILOG_GATE_PASS" not in sv.stdout:
    raise AssertionError(f"SystemVerilog failed: {sv.stdout} {sv.stderr}")
print("PASS SystemVerilog: validity gate")
