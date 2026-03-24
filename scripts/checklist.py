"""
Checklists executables — Affiche et suit les etapes d'un workflow.
Usage:
  python scripts/checklist.py list                # Toutes les checklists
  python scripts/checklist.py run deploy           # Executer une checklist
  python scripts/checklist.py show code_review     # Afficher sans executer
"""
import sys
import os
import json

CHECKLISTS_FILE = os.path.join(os.path.dirname(__file__), "..", "tools", "checklists.json")

def load():
    with open(CHECKLISTS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    data.pop("_meta", None)
    return data

def list_all():
    data = load()
    print("Checklists disponibles:")
    print("-" * 40)
    for name, cl in sorted(data.items()):
        print(f"  {name:15s}  {cl['title']} ({len(cl['steps'])} etapes)")

def show(name):
    data = load()
    if name not in data:
        print(f"Checklist inconnue: {name}")
        list_all()
        return
    cl = data[name]
    print(f"=== {cl['title']} ({len(cl['steps'])} etapes) ===\n")
    for i, step in enumerate(cl["steps"], 1):
        print(f"  {i:2d}. [ ] {step}")

def run_checklist(name):
    data = load()
    if name not in data:
        print(f"Checklist inconnue: {name}")
        list_all()
        return
    cl = data[name]
    print(f"=== {cl['title']} ===\n")
    for i, step in enumerate(cl["steps"], 1):
        print(f"  [{i}/{len(cl['steps'])}] {step}")
    print(f"\n[OK] Checklist '{name}' affichee ({len(cl['steps'])} etapes)")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: checklist.py <list|show|run> [nom]")
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "list":
        list_all()
    elif cmd in ("show", "run") and len(sys.argv) > 2:
        (show if cmd == "show" else run_checklist)(sys.argv[2])
    else:
        list_all()
