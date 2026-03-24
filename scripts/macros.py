"""
Systeme de macros — Enchainements nommes de commandes CX.
Usage:
  python scripts/macros.py run <nom_macro>      # Executer une macro
  python scripts/macros.py list                  # Lister les macros
  python scripts/macros.py add <nom> <commandes> # Ajouter une macro custom
"""
import sys
import os
import json
import subprocess

SCRIPTS = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(SCRIPTS)
CX = os.path.join(PROJECT, "cx.py")
MACROS_FILE = os.path.join(PROJECT, "configs", "macros.json")

# Macros predefinies
BUILTIN_MACROS = {
    "morning": {
        "desc": "Check matinal : systeme + git + disque",
        "steps": [
            ["system", "ram"],
            ["system", "disk"],
            ["git", "status"],
        ]
    },
    "health": {
        "desc": "Diagnostic complet du systeme",
        "steps": [
            ["check"],
            ["system", "all"],
            ["desktop", "screen_info"],
        ]
    },
    "save": {
        "desc": "Sauvegarde rapide : git add + commit + status",
        "steps": [
            ["git", "save", "Auto-save"],
            ["git", "status"],
        ]
    },
    "cleanup": {
        "desc": "Nettoyage : supprimer __pycache__, .pyc, fichiers tmp",
        "steps": [
            ["_shell", "powershell", "-Command",
             "Get-ChildItem -Recurse -Directory -Name '__pycache__' | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue; "
             "Get-ChildItem -Recurse -Filter '*.pyc' | Remove-Item -Force -ErrorAction SilentlyContinue; "
             "Write-Host '[OK] Nettoyage termine'"],
        ]
    },
    "report": {
        "desc": "Generer le dashboard systeme",
        "steps": [
            ["_script", "report_gen.py", "dashboard", "--output", "output/dashboard.html"],
        ]
    },
}

def load_custom_macros():
    if os.path.exists(MACROS_FILE):
        with open(MACROS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_custom_macros(macros):
    with open(MACROS_FILE, "w", encoding="utf-8") as f:
        json.dump(macros, f, indent=2, ensure_ascii=False)

def get_all_macros():
    all_m = dict(BUILTIN_MACROS)
    all_m.update(load_custom_macros())
    return all_m

def run_macro(name):
    macros = get_all_macros()
    if name not in macros:
        print(f"Macro inconnue: {name}")
        list_macros()
        return

    macro = macros[name]
    print(f"[MACRO] {name} : {macro['desc']}")
    print("=" * 50)

    for i, step in enumerate(macro["steps"]):
        print(f"\n--- Etape {i+1}: {' '.join(step)} ---")
        try:
            if step[0] == "_shell":
                subprocess.run(step[1:], cwd=PROJECT, timeout=30)
            elif step[0] == "_script":
                subprocess.run([sys.executable, os.path.join(SCRIPTS, step[1])] + step[2:],
                             cwd=PROJECT, timeout=60)
            else:
                subprocess.run([sys.executable, CX] + step, cwd=PROJECT, timeout=60)
        except subprocess.TimeoutExpired:
            print(f"[TIMEOUT] Etape {i+1} a expire")
        except Exception as e:
            print(f"[ERREUR] Etape {i+1}: {e}")

    print(f"\n[OK] Macro '{name}' terminee")

def list_macros():
    macros = get_all_macros()
    print("Macros disponibles:")
    print("-" * 40)
    for name, macro in sorted(macros.items()):
        builtin = " (builtin)" if name in BUILTIN_MACROS else ""
        print(f"  {name:12s}  {macro['desc']}{builtin}")

def add_macro(name, desc, steps_str):
    custom = load_custom_macros()
    steps = [s.strip().split() for s in steps_str.split(";")]
    custom[name] = {"desc": desc, "steps": steps}
    save_custom_macros(custom)
    print(f"[OK] Macro '{name}' ajoutee ({len(steps)} etapes)")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: macros.py <run|list|add> [args]")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "list":
        list_macros()
    elif cmd == "run" and len(sys.argv) > 2:
        run_macro(sys.argv[2])
    elif cmd == "add" and len(sys.argv) > 4:
        add_macro(sys.argv[2], sys.argv[3], sys.argv[4])
    else:
        print("Usage: macros.py run <nom> | list | add <nom> <desc> <'cmd1;cmd2;cmd3'>")
