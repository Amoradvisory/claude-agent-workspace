Add-Type @"
using System;
using System.Runtime.InteropServices;
public class Win32 {
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
}
"@

$p = Get-Process msedge | Where-Object { $_.MainWindowHandle -ne 0 } | Select-Object -First 1
if ($p) {
    [Win32]::ShowWindow($p.MainWindowHandle, 9)
    [Win32]::SetForegroundWindow($p.MainWindowHandle)
    Write-Host "Edge brought to front"
} else {
    Write-Host "No Edge window with a visible handle found. Launching Edge..."
    Start-Process msedge
}
