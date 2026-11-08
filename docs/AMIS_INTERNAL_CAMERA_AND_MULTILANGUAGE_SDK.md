# AMIS internal camera and multi-language SDK

The workflow has three parts: Host Agent software on the notebook; a physical internal macro camera separately mounted and connected by a qualified technician; and the Android controller requesting discovery/capture through the owner-authorized bridge.

Installing the Host Agent over USB does not install a physical camera. USB is a transport, not a mechanism for placing hardware inside the chassis. The selected camera may need a dedicated internal USB interface or bridge. Existing webcam connectors may be MIPI CSI-2 or proprietary and must not be connected without verified pinout and electrical specifications.

API client examples are provided in Python, Go, Rust, and Ruby. They call the same local host-agent endpoints; they are not four separate camera drivers. Current capture is Python/OpenCV and is only supported for Linux-style camera indices. Windows/macOS enumeration does not imply capture support. Macro optics and controllable lighting remain unverified hardware requirements.

See hardware/motherboard-identification/INTERNAL_CAMERA_DESIGN.md for physical design gates and safety constraints.
