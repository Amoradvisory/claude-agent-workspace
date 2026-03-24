"""
Pont systeme — Equivalent du system-server.mjs de Gemini pour Claude Code.
Expose les infos systeme sans MCP, directement appelable.
Usage: python scripts/system_info.py [cpu|ram|disk|battery|processes|all]
"""
import subprocess
import sys
import os
import json

def get_cpu():
    r = subprocess.run(
        ["powershell", "-Command",
         "Get-CimInstance Win32_Processor | Select-Object Name, NumberOfCores, MaxClockSpeed | ConvertTo-Json"],
        capture_output=True, text=True, timeout=10
    )
    return json.loads(r.stdout) if r.returncode == 0 else {"error": r.stderr}

def get_ram():
    r = subprocess.run(
        ["powershell", "-Command",
         "$os = Get-CimInstance Win32_OperatingSystem; "
         "@{TotalGB=[math]::Round($os.TotalVisibleMemorySize/1MB,1); "
         "FreeGB=[math]::Round($os.FreePhysicalMemory/1MB,1); "
         "UsedPercent=[math]::Round(($os.TotalVisibleMemorySize-$os.FreePhysicalMemory)/$os.TotalVisibleMemorySize*100,1)} | ConvertTo-Json"],
        capture_output=True, text=True, timeout=10
    )
    return json.loads(r.stdout) if r.returncode == 0 else {"error": r.stderr}

def get_disk():
    import shutil
    drives = []
    for letter in "CDEFGH":
        path = f"{letter}:/"
        if os.path.exists(path):
            total, used, free = shutil.disk_usage(path)
            drives.append({
                "drive": f"{letter}:",
                "total_gb": round(total / (1024**3), 1),
                "free_gb": round(free / (1024**3), 1),
                "used_percent": round(used / total * 100, 1)
            })
    return drives

def get_battery():
    r = subprocess.run(
        ["powershell", "-Command",
         "Get-CimInstance Win32_Battery | Select-Object EstimatedChargeRemaining, BatteryStatus | ConvertTo-Json"],
        capture_output=True, text=True, timeout=10
    )
    return json.loads(r.stdout) if r.returncode == 0 else {"no_battery": True}

def get_processes(top_n=15):
    r = subprocess.run(
        ["powershell", "-Command",
         f"Get-Process | Sort-Object WorkingSet64 -Descending | Select-Object -First {top_n} Name, Id, "
         "@{N='RAM_MB';E={[math]::Round($_.WorkingSet64/1MB,1)}}, CPU | ConvertTo-Json"],
        capture_output=True, text=True, timeout=10
    )
    return json.loads(r.stdout) if r.returncode == 0 else {"error": r.stderr}

COMMANDS = {
    "cpu": get_cpu,
    "ram": get_ram,
    "disk": get_disk,
    "battery": get_battery,
    "processes": get_processes,
}

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "all"
    if target == "all":
        result = {k: fn() for k, fn in COMMANDS.items()}
    elif target in COMMANDS:
        result = {target: COMMANDS[target]()}
    else:
        result = {"error": f"Commande inconnue: {target}. Dispo: {', '.join(COMMANDS.keys())}, all"}
    print(json.dumps(result, indent=2, ensure_ascii=False))
