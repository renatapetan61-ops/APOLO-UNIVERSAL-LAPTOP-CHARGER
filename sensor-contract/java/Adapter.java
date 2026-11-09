import java.io.BufferedReader;
import java.io.InputStreamReader;

public final class Adapter {
  public static void main(String[] args) throws Exception {
    String line = new BufferedReader(new InputStreamReader(System.in)).readLine();
    String[] f = line == null ? new String[0] : line.split("\\t", -1);
    boolean ok = f.length == 6 && f[0].equals("APOLO1") && !f[1].isBlank() &&
      !f[2].isBlank() && (f[3].equals("HOST_OS") || f[3].equals("PHYSICAL_INTERFACE")) &&
      !f[4].isBlank();
    try { ok = ok && Long.parseLong(f[5]) > 0; } catch (Exception e) { ok = false; }
    System.out.println(ok ? "ACCEPTED" : "REJECTED");
    if (!ok) System.exit(2);
  }
}
