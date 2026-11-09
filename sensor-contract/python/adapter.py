#!/usr/bin/env python3
"""Validate one APOLO1 tab-separated sensor observation from stdin."""
import sys

def validate(line: str) -> bool:
    fields = line.rstrip("\n").split("\t")
    if len(fields) != 6:
        return False
    version, name, value, origin, source, timestamp = fields
    return (version == "APOLO1" and bool(name.strip()) and bool(value.strip())
            and origin in {"HOST_OS", "PHYSICAL_INTERFACE"}
            and bool(source.strip()) and timestamp.isdigit() and int(timestamp) > 0)

if __name__ == "__main__":
    raw = sys.stdin.readline()
    accepted = validate(raw)
    print("ACCEPTED" if accepted else "REJECTED")
    raise SystemExit(0 if accepted else 2)
