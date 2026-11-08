#include <iostream>

int main() {
    std::cout << R"({"protocol":"apolo-bms-telemetry/1","sensor":"pack_temperature","value":25.0,"unit":"degC","source_type":"SIMULATED","source_id":"cpp-virtual-sensor","timestamp_ms":0,"hardware_backed":false,"output_authorized":false})" << std::endl;
    return 0;
}
