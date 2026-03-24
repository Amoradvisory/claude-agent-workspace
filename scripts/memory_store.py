"""
Memoire persistante — Stockage cle-valeur JSON inter-sessions.
Replique le memory MCP de Codex/Gemini.
Usage:
  python scripts/memory_store.py get <cle>
  python scripts/memory_store.py set <cle> <valeur>
  python scripts/memory_store.py list
  python scripts/memory_store.py delete <cle>
  python scripts/memory_store.py search <terme>
"""
import sys
import os
import json
from datetime import datetime

MEMORY_FILE = os.path.join(os.path.dirname(__file__), "..", "memory", "store.json")

def _load():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def _save(data):
    os.makedirs(os.path.dirname(MEMORY_FILE), exist_ok=True)
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def get(key):
    data = _load()
    if key in data:
        entry = data[key]
        print(f"[{key}] = {entry['value']}")
        print(f"  (mis a jour: {entry['updated']})")
    else:
        print(f"Cle '{key}' non trouvee.")

def set_val(key, value):
    data = _load()
    data[key] = {
        "value": value,
        "created": data.get(key, {}).get("created", datetime.now().isoformat()),
        "updated": datetime.now().isoformat(),
    }
    _save(data)
    print(f"[OK] {key} = {value}")

def list_all():
    data = _load()
    if not data:
        print("Memoire vide.")
        return
    print(f"Memoire ({len(data)} entrees):")
    print("-" * 50)
    for key, entry in sorted(data.items()):
        val = str(entry["value"])
        if len(val) > 60:
            val = val[:57] + "..."
        print(f"  {key:20s}  {val}")

def delete(key):
    data = _load()
    if key in data:
        del data[key]
        _save(data)
        print(f"[OK] '{key}' supprime.")
    else:
        print(f"Cle '{key}' non trouvee.")

def search(term):
    data = _load()
    results = {k: v for k, v in data.items()
               if term.lower() in k.lower() or term.lower() in str(v["value"]).lower()}
    if not results:
        print(f"Aucun resultat pour '{term}'.")
        return
    print(f"{len(results)} resultat(s) pour '{term}':")
    for key, entry in results.items():
        print(f"  [{key}] = {entry['value']}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: memory_store.py <get|set|list|delete|search> [args]")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "list":
        list_all()
    elif cmd == "get" and len(sys.argv) > 2:
        get(sys.argv[2])
    elif cmd == "set" and len(sys.argv) > 3:
        set_val(sys.argv[2], " ".join(sys.argv[3:]))
    elif cmd == "delete" and len(sys.argv) > 2:
        delete(sys.argv[2])
    elif cmd == "search" and len(sys.argv) > 2:
        search(sys.argv[2])
    else:
        print("Usage: memory_store.py <get|set|list|delete|search> [args]")
