# APOLO Virtual Hardware Board

A hardware-emulation layer with a virtual board, I2C address enumeration and register maps, a 16S BMS model, a latched safety supervisor, a non-energizing power-stage calculator and a USB-PD policy-engine model.

All values are synthetic inputs or calculations. This is not a QEMU guest device model, physical sensor, BMS, independent protection circuit, USB-C PD PHY, converter, charger or certified design. It does not access GPIO/I2C hardware and cannot energize an output. The output-enable and switching paths remain false.

A physical product still requires reviewed schematics, component selection, PCB, isolated/appropriate analog measurement front ends, independent protection, fuse, thermal design, MCU firmware, calibration, fault-injection testing and qualified laboratory validation. Never connect a simulated 19 V output to a notebook.

Run tests from repository root:
python3 -m unittest discover -s hardware-virtual -v

Next: expose this snapshot through Host Agent with provenance labels, add an Android hardware-emulation screen, and only then consider a separate QEMU device model if guest-OS enumeration is required.
