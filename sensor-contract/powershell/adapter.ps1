$line = [Console]::In.ReadLine()
$f = $line.Split([char]9)
$timestamp = [long]0
$ok = $f.Count -eq 6 -and $f[0] -eq "APOLO1" -and
  -not [string]::IsNullOrWhiteSpace($f[1]) -and
  -not [string]::IsNullOrWhiteSpace($f[2]) -and
  $f[3] -in @("HOST_OS", "PHYSICAL_INTERFACE") -and
  -not [string]::IsNullOrWhiteSpace($f[4]) -and
  [long]::TryParse($f[5], [ref]$timestamp) -and $timestamp -gt 0
if ($ok) { "ACCEPTED"; exit 0 } else { "REJECTED"; exit 2 }
