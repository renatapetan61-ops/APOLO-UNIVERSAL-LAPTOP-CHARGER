package main

import (
  "bufio"
  "fmt"
  "os"
  "strconv"
  "strings"
)

func valid(line string) bool {
  f := strings.Split(strings.TrimRight(line, "\\r\\n"), "\\t")
  if len(f) != 6 || f[0] != "APOLO1" || strings.TrimSpace(f[1]) == "" ||
    strings.TrimSpace(f[2]) == "" || (f[3] != "HOST_OS" && f[3] != "PHYSICAL_INTERFACE") ||
    strings.TrimSpace(f[4]) == "" { return false }
  n, err := strconv.ParseUint(f[5], 10, 64)
  return err == nil && n > 0
}
func main() {
  scanner := bufio.NewScanner(os.Stdin)
  if !scanner.Scan() { fmt.Println("REJECTED"); os.Exit(2) }
  if valid(scanner.Text()) { fmt.Println("ACCEPTED"); return }
  fmt.Println("REJECTED"); os.Exit(2)
}
