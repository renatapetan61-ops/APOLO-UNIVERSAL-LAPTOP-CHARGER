// APOLO AMIS client for Go. Talks only to the local host agent.
package main
import ("bytes"; "encoding/json"; "fmt"; "io"; "net/http"; "time")
const baseURL = "http://127.0.0.1:8765"
func call(path, method string) (map[string]any, error) {
 req, err := http.NewRequest(method, baseURL+path, bytes.NewReader(nil)); if err != nil { return nil, err }
 req.Header.Set("Cache-Control", "no-store")
 resp, err := (&http.Client{Timeout: 35*time.Second}).Do(req); if err != nil { return nil, err }; defer resp.Body.Close()
 body, err := io.ReadAll(io.LimitReader(resp.Body, 2<<20)); if err != nil { return nil, err }
 if resp.StatusCode < 200 || resp.StatusCode >= 300 { return nil, fmt.Errorf("host agent HTTP %d: %s", resp.StatusCode, string(body)) }
 var result map[string]any; if err := json.Unmarshal(body, &result); err != nil { return nil, err }; return result, nil
}
func main() {
 d, err := call("/v1/camera", http.MethodGet); if err != nil { panic(err) }; fmt.Printf("Camera discovery: %#v\\n", d)
 c, err := call("/v1/camera/capture", http.MethodPost); if err != nil { panic(err) }; b, _ := json.MarshalIndent(c, "", "  "); fmt.Println(string(b))
}
