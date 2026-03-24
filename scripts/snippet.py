"""
Gestionnaire de snippets — Acces rapide aux patterns de code reutilisables.
Usage:
  python scripts/snippet.py list                  # Toutes les categories
  python scripts/snippet.py list python            # Snippets Python
  python scripts/snippet.py get python read_csv    # Afficher un snippet
  python scripts/snippet.py copy python http_get   # Copier dans le clipboard
  python scripts/snippet.py add python <nom> <code> # Ajouter un snippet
"""
import sys
import os
import json
import subprocess

SNIPPETS_FILE = os.path.join(os.path.dirname(__file__), "..", "tools", "snippets.json")

def load():
    with open(SNIPPETS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    data.pop("_meta", None)
    return data

def save(data):
    meta = {"_meta": {"description": "Bibliotheque de snippets reutilisables", "usage": "python cx.py snippet <nom>"}}
    meta.update(data)
    with open(SNIPPETS_FILE, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)

def list_snippets(category=None):
    data = load()
    if category:
        if category in data:
            print(f"[{category}] {len(data[category])} snippets:")
            for name in sorted(data[category].keys()):
                preview = data[category][name].split("\n")[0][:60]
                print(f"  {name:20s}  {preview}")
        else:
            print(f"Categorie inconnue: {category}. Dispo: {', '.join(data.keys())}")
    else:
        for cat, snippets in sorted(data.items()):
            print(f"[{cat}] {len(snippets)} snippets: {', '.join(sorted(snippets.keys()))}")

def get_snippet(category, name):
    data = load()
    if category in data and name in data[category]:
        print(f"# === {category}/{name} ===")
        print(data[category][name])
    else:
        print(f"Snippet non trouve: {category}/{name}")

def copy_snippet(category, name):
    data = load()
    if category in data and name in data[category]:
        code = data[category][name]
        subprocess.run(["powershell", "-Command", f"Set-Clipboard -Value '{code}'"],
                      capture_output=True, timeout=5)
        print(f"[OK] Copie dans le clipboard: {category}/{name}")
    else:
        print(f"Snippet non trouve: {category}/{name}")

def add_snippet(category, name, code):
    data = load()
    if category not in data:
        data[category] = {}
    data[category][name] = code
    save(data)
    print(f"[OK] Snippet ajoute: {category}/{name}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: snippet.py <list|get|copy|add> [category] [name] [code]")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "list":
        list_snippets(sys.argv[2] if len(sys.argv) > 2 else None)
    elif cmd == "get" and len(sys.argv) > 3:
        get_snippet(sys.argv[2], sys.argv[3])
    elif cmd == "copy" and len(sys.argv) > 3:
        copy_snippet(sys.argv[2], sys.argv[3])
    elif cmd == "add" and len(sys.argv) > 4:
        add_snippet(sys.argv[2], sys.argv[3], " ".join(sys.argv[4:]))
    else:
        print("Usage: snippet.py <list|get|copy|add> [args]")
