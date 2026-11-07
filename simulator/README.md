# APOLO Simulator

The Android app includes an in-process deterministic demonstration simulator:

- Normal — nominal illustrative telemetry.
- Warning — illustrative low state of charge and elevated temperature.
- Fault — illustrative critical state and output-blocked message.

A standalone Python generator creates matching v1 binary telemetry frames for test fixtures and protocol development:

```bash
python simulator/apolo_simulator.py --scenario normal --sequence 1
python simulator/apolo_simulator.py --scenario warning --sequence 2
python simulator/apolo_simulator.py --scenario fault --sequence 3
python -m unittest discover -s simulator -p "test_*.py" -v
```

All values are synthetic. They do not represent a real battery, cannot validate a BMS, and must not be used to select operating thresholds. The simulator does not communicate with or control hardware. It always reports that power output is disabled.
