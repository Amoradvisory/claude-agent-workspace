"""
Workflow Git rapide — Raccourcis pour les operations courantes.
Usage:
  python scripts/git_quick.py status          # Statut rapide
  python scripts/git_quick.py save "message"  # Add + commit en une commande
  python scripts/git_quick.py log             # 10 derniers commits
  python scripts/git_quick.py changelog       # Genere un changelog depuis les commits
  python scripts/git_quick.py diff            # Diff des changements non commites
"""
import subprocess
import sys
import os
import json
from datetime import datetime

def run(cmd, cwd=None):
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd, timeout=30)
    return r.stdout.strip(), r.stderr.strip(), r.returncode

def status(cwd="."):
    out, _, _ = run(["git", "status", "--short"], cwd)
    if not out:
        print("[OK] Rien a commiter, repertoire de travail propre.")
    else:
        print(out)
        lines = out.strip().split("\n")
        modified = sum(1 for l in lines if l.startswith(" M") or l.startswith("M"))
        added = sum(1 for l in lines if l.startswith("??"))
        print(f"\n  {modified} modifie(s), {added} non suivi(s)")

def save(message, cwd="."):
    run(["git", "add", "-A"], cwd)
    out, err, code = run(["git", "commit", "-m", message], cwd)
    if code == 0:
        print(f"[OK] Commit: {message}")
    else:
        print(f"[!!] Erreur: {err or out}")

def log(cwd=".", n=10):
    out, _, _ = run(["git", "log", f"--oneline", f"-{n}", "--format=%h %s (%ar)"], cwd)
    print(out or "[OK] Aucun commit.")

def changelog(cwd="."):
    out, _, _ = run(["git", "log", "--format=%H|%s|%an|%ai"], cwd)
    if not out:
        print("Aucun commit.")
        return
    lines = out.strip().split("\n")
    md = f"# Changelog\n\nGenere le {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
    current_date = ""
    for line in lines:
        parts = line.split("|", 3)
        if len(parts) < 4:
            continue
        hash_, msg, author, date_str = parts
        day = date_str[:10]
        if day != current_date:
            current_date = day
            md += f"\n## {day}\n"
        md += f"- `{hash_[:7]}` {msg}\n"

    changelog_path = os.path.join(cwd, "CHANGELOG.md")
    with open(changelog_path, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"[OK] Changelog genere: {changelog_path}")

def diff(cwd="."):
    out, _, _ = run(["git", "diff", "--stat"], cwd)
    print(out or "[OK] Aucun changement.")

COMMANDS = {
    "status": lambda args: status(),
    "save": lambda args: save(args[0] if args else "Update"),
    "log": lambda args: log(),
    "changelog": lambda args: changelog(),
    "diff": lambda args: diff(),
}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print("Usage: git_quick.py <status|save|log|changelog|diff> [args]")
        print("  save 'message' : git add -A + commit")
        print("  changelog      : genere CHANGELOG.md depuis l'historique")
        sys.exit(1)
    COMMANDS[sys.argv[1]](sys.argv[2:])
