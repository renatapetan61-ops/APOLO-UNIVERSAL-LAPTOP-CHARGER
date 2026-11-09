#include <iostream>
#include <sstream>
#include <string>
#include <vector>

int main() {
    std::string line;
    if (!std::getline(std::cin, line)) return 2;
    std::stringstream stream(line);
    std::vector<std::string> fields;
    std::string field;
    while (std::getline(stream, field, '\t')) fields.push_back(field);
    bool ok = fields.size() == 6 && fields[0] == "APOLO1" &&
        !fields[1].empty() && !fields[2].empty() &&
        (fields[3] == "HOST_OS" || fields[3] == "PHYSICAL_INTERFACE") &&
        !fields[4].empty() && !fields[5].empty();
    try {
        std::size_t parsed = 0;
        const auto timestamp = std::stoull(fields.at(5), &parsed);
        ok = ok && parsed == fields.at(5).size() && timestamp > 0;
    } catch (...) { ok = false; }
    std::cout << (ok ? "ACCEPTED" : "REJECTED") << '\n';
    return ok ? 0 : 2;
}
