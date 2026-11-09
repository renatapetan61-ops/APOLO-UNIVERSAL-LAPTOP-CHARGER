# APOLO sensor observation contract — 15-language implementation

Every adapter validates a normalized tab-separated record:

`APOLO1<TAB>name<TAB>value<TAB>origin<TAB>source<TAB>epoch_ms`

Only `HOST_OS` and `PHYSICAL_INTERFACE` origins are accepted. The record must
contain a name, value, source and positive millisecond timestamp. `TEST_FIXTURE`
and unknown origins are rejected. The contract validates provenance syntax; it
does not cryptographically authenticate a host, calibrate a sensor, or prove that
a physical measurement is genuine.

Adapters exist in Kotlin, Python, C, C++, Rust, Go, C#, Java, Swift, JavaScript,
TypeScript, PowerShell, Bash, SQL and SystemVerilog. The SQL schema enforces the
same persistence constraints; SystemVerilog implements a deterministic validity
gate. Toolchain CI must pass before describing the entire matrix as verified.
