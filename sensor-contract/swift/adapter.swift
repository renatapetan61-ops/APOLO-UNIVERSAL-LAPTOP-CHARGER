import Foundation

let line = readLine() ?? ""
let f = line.components(separatedBy: "\t")
let timestamp = f.count == 6 ? UInt64(f[5]) ?? 0 : 0
let ok = f.count == 6 && f[0] == "APOLO1" && !f[1].isEmpty && !f[2].isEmpty &&
  (f[3] == "HOST_OS" || f[3] == "PHYSICAL_INTERFACE") &&
  !f[4].isEmpty && timestamp > 0
print(ok ? "ACCEPTED" : "REJECTED")
if !ok { exit(2) }
