#!/usr/bin/env bash
set -euo pipefail
IFS=$'\\t' read -r version name value origin source timestamp || { echo REJECTED; exit 2; }
if [[ "$version" == "APOLO1" && -n "$name" && -n "$value" &&
      ( "$origin" == "HOST_OS" || "$origin" == "PHYSICAL_INTERFACE" ) &&
      -n "$source" && "$timestamp" =~ ^[0-9]+$ && "$timestamp" -gt 0 ]]; then
  echo ACCEPTED
else
  echo REJECTED
  exit 2
fi
