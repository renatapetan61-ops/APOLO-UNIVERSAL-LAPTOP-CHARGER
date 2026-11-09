using System;
using System.Linq;

var line = Console.ReadLine() ?? "";
var f = line.Split('\t');
var ok = f.Length == 6 && f[0] == "APOLO1" &&
    !string.IsNullOrWhiteSpace(f[1]) && !string.IsNullOrWhiteSpace(f[2]) &&
    (f[3] == "HOST_OS" || f[3] == "PHYSICAL_INTERFACE") &&
    !string.IsNullOrWhiteSpace(f[4]) &&
    ulong.TryParse(f[5], out var timestamp) && timestamp > 0;
Console.WriteLine(ok ? "ACCEPTED" : "REJECTED");
return ok ? 0 : 2;
