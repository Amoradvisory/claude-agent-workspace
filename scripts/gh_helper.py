"""
GitHub workflow helper — Raccourcis pour les operations GH courantes.
Usage:
  python scripts/gh_helper.py status              # Statut du repo
  python scripts/gh_helper.py prs                 # Lister les PRs ouvertes
  python scripts/gh_helper.py issues              # Lister les issues ouvertes
  python scripts/gh_helper.py create-pr "titre"   # Creer une PR
  python scripts/gh_helper.py ci                   # Statut des checks CI
  python scripts/gh_helper.py clone <repo>        # Cloner un repo
  python scripts/gh_helper.py repos               # Lister mes repos
"""
import subprocess
import sys
import json

def run(cmd, timeout=30):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip(), r.stderr.strip(), r.returncode
    except FileNotFoundError:
        return "", "gh CLI non installe", 1
    except subprocess.TimeoutExpired:
        return "", "Timeout", 1

def status():
    out, err, code = run(["gh", "repo", "view", "--json", "name,owner,description,url,defaultBranchRef"])
    if code == 0:
        data = json.loads(out)
        print(f"Repo: {data.get('owner',{}).get('login','')}/{data.get('name','')}")
        print(f"URL: {data.get('url','')}")
        print(f"Branche par defaut: {data.get('defaultBranchRef',{}).get('name','')}")
        print(f"Description: {data.get('description','')}")
    else:
        print(f"[INFO] {err or 'Pas de repo GitHub lie'}")

def list_prs():
    out, _, code = run(["gh", "pr", "list", "--limit", "10"])
    print(out if out else "[OK] Aucune PR ouverte.")

def list_issues():
    out, _, code = run(["gh", "issue", "list", "--limit", "10"])
    print(out if out else "[OK] Aucune issue ouverte.")

def create_pr(title):
    out, err, code = run(["gh", "pr", "create", "--title", title, "--body", f"PR cree automatiquement.\n\nTitre: {title}"])
    print(out if code == 0 else f"[ERREUR] {err}")

def ci_status():
    out, err, code = run(["gh", "pr", "checks"])
    print(out if code == 0 else f"[INFO] {err or 'Pas de PR/checks en cours'}")

def clone(repo):
    out, err, code = run(["gh", "repo", "clone", repo], timeout=120)
    print(f"[OK] Clone: {repo}" if code == 0 else f"[ERREUR] {err}")

def list_repos():
    out, _, code = run(["gh", "repo", "list", "--limit", "15", "--json", "name,isPrivate,updatedAt"])
    if code == 0:
        repos = json.loads(out)
        for r in repos:
            vis = "prive" if r["isPrivate"] else "public"
            print(f"  {r['name']:30s}  [{vis}]  MAJ: {r['updatedAt'][:10]}")
    else:
        print("[INFO] Impossible de lister les repos.")

COMMANDS = {
    "status": lambda a: status(),
    "prs": lambda a: list_prs(),
    "issues": lambda a: list_issues(),
    "create-pr": lambda a: create_pr(a[0]) if a else print("Usage: create-pr 'titre'"),
    "ci": lambda a: ci_status(),
    "clone": lambda a: clone(a[0]) if a else print("Usage: clone <repo>"),
    "repos": lambda a: list_repos(),
}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print("Usage: gh_helper.py <status|prs|issues|create-pr|ci|clone|repos>")
        sys.exit(1)
    COMMANDS[sys.argv[1]](sys.argv[2:])
