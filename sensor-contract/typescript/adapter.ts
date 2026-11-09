import * as fs from "node:fs";
const line = fs.readFileSync(0, "utf8").split(/\\r?\\n/, 1)[0];
const f = line.split("\\t");
const ok: boolean = f.length === 6 && f[0] === "APOLO1" && !!f[1].trim() &&
  !!f[2].trim() && (f[3] === "HOST_OS" || f[3] === "PHYSICAL_INTERFACE") &&
  !!f[4].trim() && /^[0-9]+$/.test(f[5]) && BigInt(f[5]) > 0n;
console.log(ok ? "ACCEPTED" : "REJECTED");
if (!ok) process.exit(2);
