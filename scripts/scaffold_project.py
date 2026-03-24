"""
Scaffolding de projet — Cree une structure de projet complete.
Usage:
  python scripts/scaffold_project.py mon_projet --lang python
  python scripts/scaffold_project.py mon_app --lang node
  python scripts/scaffold_project.py mon_site --lang web
"""
import os
import sys
import argparse
import json
import subprocess

TEMPLATES = {
    "python": {
        "dirs": ["src", "tests", "docs"],
        "files": {
            "src/__init__.py": "",
            "src/main.py": '"""Point d\'entree principal."""\n\ndef main():\n    print("Hello!")\n\nif __name__ == "__main__":\n    main()\n',
            "tests/__init__.py": "",
            "tests/test_main.py": 'from src.main import main\n\ndef test_main():\n    main()  # Should not raise\n',
            "requirements.txt": "# Dependances du projet\n",
            ".gitignore": "__pycache__/\n*.pyc\n.venv/\nvenv/\n.env\ndist/\n*.egg-info/\n",
        },
        "init_cmd": None,
    },
    "node": {
        "dirs": ["src", "tests", "public"],
        "files": {
            "src/index.js": 'console.log("Hello!");\n',
            "tests/index.test.js": 'const assert = require("assert");\nassert.ok(true, "Basic test passes");\nconsole.log("Tests OK");\n',
            ".gitignore": "node_modules/\n.env\ndist/\n*.log\n",
        },
        "init_cmd": ["npm", "init", "-y"],
    },
    "web": {
        "dirs": ["css", "js", "img"],
        "files": {
            "index.html": '<!DOCTYPE html>\n<html lang="fr">\n<head>\n  <meta charset="UTF-8">\n  <meta name="viewport" content="width=device-width, initial-scale=1.0">\n  <title>Mon Site</title>\n  <link rel="stylesheet" href="css/style.css">\n</head>\n<body>\n  <h1>Mon Site</h1>\n  <script src="js/app.js"></script>\n</body>\n</html>\n',
            "css/style.css": "* { margin: 0; padding: 0; box-sizing: border-box; }\nbody { font-family: system-ui, sans-serif; padding: 2rem; }\n",
            "js/app.js": 'console.log("App loaded");\n',
            ".gitignore": "node_modules/\n.env\n",
        },
        "init_cmd": None,
    },
}

def scaffold(name, lang, base_dir="."):
    template = TEMPLATES.get(lang)
    if not template:
        print(f"Langue inconnue: {lang}. Disponibles: {', '.join(TEMPLATES.keys())}")
        sys.exit(1)

    project_dir = os.path.join(base_dir, name)
    if os.path.exists(project_dir):
        print(f"Le dossier {project_dir} existe deja.")
        sys.exit(1)

    # Creer les dossiers
    os.makedirs(project_dir, exist_ok=True)
    for d in template["dirs"]:
        os.makedirs(os.path.join(project_dir, d), exist_ok=True)

    # Creer les fichiers
    for filepath, content in template["files"].items():
        full = os.path.join(project_dir, filepath)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as f:
            f.write(content)

    # Creer README
    with open(os.path.join(project_dir, "README.md"), "w", encoding="utf-8") as f:
        f.write(f"# {name}\n\nProjet {lang} cree automatiquement.\n")

    # Init commande (npm init, etc.)
    if template["init_cmd"]:
        subprocess.run(template["init_cmd"], cwd=project_dir, capture_output=True)

    # Git init
    subprocess.run(["git", "init"], cwd=project_dir, capture_output=True)
    subprocess.run(["git", "add", "-A"], cwd=project_dir, capture_output=True)
    subprocess.run(["git", "commit", "-m", "Initial scaffold"], cwd=project_dir, capture_output=True)

    print(f"[OK] Projet '{name}' ({lang}) cree dans {project_dir}")
    print(f"     Structure: {', '.join(template['dirs'])}")
    print(f"     Fichiers: {len(template['files'])} + README.md + .gitignore")
    print(f"     Git: initialise avec premier commit")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("name", help="Nom du projet")
    parser.add_argument("--lang", "-l", default="python", choices=TEMPLATES.keys())
    parser.add_argument("--dir", "-d", default=".", help="Dossier parent")
    args = parser.parse_args()
    scaffold(args.name, args.lang, args.dir)
