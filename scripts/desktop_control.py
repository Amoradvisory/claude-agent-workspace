"""
Pont desktop complet — Equivalent du desktop-server.mjs de Gemini.
Controle fenetres, clipboard, clavier, souris, ecran Windows.
Usage: python scripts/desktop_control.py <command> [args...]
Commands:
  list_windows                    Liste les fenetres visibles
  focus <title>                   Met une fenetre au premier plan
  screenshot [path]               Capture d'ecran
  open <app>                      Ouvrir une application
  close <pid>                     Fermer un processus
  clipboard_read                  Lire le presse-papiers
  clipboard_write <text>          Ecrire dans le presse-papiers
  sendkeys <keys>                 Envoyer des touches clavier
  screen_info                     Info ecran (resolution, souris)
  minimize <title>                Minimiser une fenetre
  maximize <title>                Maximiser une fenetre
"""
import subprocess
import sys
import json

def ps(script, timeout=10):
    r = subprocess.run(["powershell", "-Command", script],
                       capture_output=True, text=True, timeout=timeout)
    return r.stdout.strip()

def list_windows():
    out = ps("Get-Process | Where-Object {$_.MainWindowTitle -ne ''} | "
             "Select-Object Id, ProcessName, MainWindowTitle | ConvertTo-Json")
    return json.loads(out) if out else []

def focus_window(title_pattern):
    return ps(f"""
Add-Type @"
using System; using System.Runtime.InteropServices;
public class W {{ [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
[DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int c); }}
"@
$p = Get-Process | Where-Object {{ $_.MainWindowTitle -match '{title_pattern}' }} | Select-Object -First 1
if ($p) {{ [W]::ShowWindow($p.MainWindowHandle, 9); [W]::SetForegroundWindow($p.MainWindowHandle); "OK: $($p.MainWindowTitle)" }}
else {{ "NOT_FOUND" }}
""")

def window_action(title_pattern, action):
    """action: 6=minimize, 9=restore, 3=maximize"""
    codes = {"minimize": 6, "maximize": 3, "restore": 9}
    code = codes.get(action, 9)
    return ps(f"""
Add-Type @"
using System; using System.Runtime.InteropServices;
public class W {{ [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int c); }}
"@
$p = Get-Process | Where-Object {{ $_.MainWindowTitle -match '{title_pattern}' }} | Select-Object -First 1
if ($p) {{ [W]::ShowWindow($p.MainWindowHandle, {code}); "{action}: $($p.MainWindowTitle)" }}
else {{ "NOT_FOUND" }}
""")

def take_screenshot(path="output/screenshot.png"):
    return ps(f"""
Add-Type -AssemblyName System.Windows.Forms
$bounds = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
$bmp = New-Object System.Drawing.Bitmap($bounds.Width, $bounds.Height)
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.CopyFromScreen($bounds.Location, [System.Drawing.Point]::Empty, $bounds.Size)
$bmp.Save('{path.replace(chr(92), "/")}')
$g.Dispose(); $bmp.Dispose()
"Saved to {path}"
""", timeout=15)

def open_app(app_name):
    subprocess.Popen(["start", app_name], shell=True)
    return f"Launched: {app_name}"

def close_process(pid):
    subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True)
    return f"Killed PID: {pid}"

def clipboard_read():
    return ps("Get-Clipboard")

def clipboard_write(text):
    ps(f"Set-Clipboard -Value '{text}'")
    return f"Clipboard set ({len(text)} chars)"

def sendkeys(keys):
    """Envoie des touches. Ex: 'Hello', '{ENTER}', '%{F4}' (Alt+F4)"""
    return ps(f"""
Add-Type -AssemblyName System.Windows.Forms
[System.Windows.Forms.SendKeys]::SendWait('{keys}')
"Keys sent: {keys}"
""")

def screen_info():
    return ps("""
Add-Type -AssemblyName System.Windows.Forms
$s = [System.Windows.Forms.Screen]::PrimaryScreen
$cursor = [System.Windows.Forms.Cursor]::Position
$screens = [System.Windows.Forms.Screen]::AllScreens
@{
    PrimaryWidth = $s.Bounds.Width
    PrimaryHeight = $s.Bounds.Height
    WorkAreaWidth = $s.WorkingArea.Width
    WorkAreaHeight = $s.WorkingArea.Height
    CursorX = $cursor.X
    CursorY = $cursor.Y
    MonitorCount = $screens.Count
} | ConvertTo-Json
""")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]
    args = sys.argv[2:]

    dispatch = {
        "list_windows":    lambda: print(json.dumps(list_windows(), indent=2, ensure_ascii=False)),
        "focus":           lambda: print(focus_window(args[0])) if args else print("Usage: focus <title>"),
        "screenshot":      lambda: print(take_screenshot(args[0] if args else "output/screenshot.png")),
        "open":            lambda: print(open_app(args[0])) if args else print("Usage: open <app>"),
        "close":           lambda: print(close_process(args[0])) if args else print("Usage: close <pid>"),
        "clipboard_read":  lambda: print(clipboard_read()),
        "clipboard_write": lambda: print(clipboard_write(" ".join(args))) if args else print("Usage: clipboard_write <text>"),
        "sendkeys":        lambda: print(sendkeys(args[0])) if args else print("Usage: sendkeys <keys>"),
        "screen_info":     lambda: print(screen_info()),
        "minimize":        lambda: print(window_action(args[0], "minimize")) if args else print("Usage: minimize <title>"),
        "maximize":        lambda: print(window_action(args[0], "maximize")) if args else print("Usage: maximize <title>"),
    }

    if cmd in dispatch:
        dispatch[cmd]()
    else:
        print(f"Commande inconnue: {cmd}")
        print(__doc__)
