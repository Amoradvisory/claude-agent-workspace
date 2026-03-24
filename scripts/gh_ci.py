"""
GitHub/CI MCP — Lecture approfondie des PRs, commits, branches, diffs, checks CI.
Usage:
  python scripts/gh_ci.py pr-list [--state open|closed|all] [--limit 20]
  python scripts/gh_ci.py pr-view <number>           # Detail complet d'une PR
  python scripts/gh_ci.py pr-diff <number>            # Diff d'une PR
  python scripts/gh_ci.py pr-reviews <number>         # Review comments
  python scripts/gh_ci.py pr-files <number>           # Fichiers modifies
  python scripts/gh_ci.py checks [<ref>]              # Checks CI du commit/PR
  python scripts/gh_ci.py check-log <run_id>          # Logs d'un run CI
  python scripts/gh_ci.py runs [--limit 10]           # Dernieres executions CI
  python scripts/gh_ci.py run-view <run_id>           # Detail d'un run
  python scripts/gh_ci.py run-log <run_id>            # Telecharger logs complets
  python scripts/gh_ci.py branches [--limit 20]       # Lister les branches
  python scripts/gh_ci.py commits [--limit 15] [--branch main]  # Derniers commits
  python scripts/gh_ci.py diff <ref1> [<ref2>]        # Diff entre refs
  python scripts/gh_ci.py blame <file> [--line 10-20] # Git blame via GH
  python scripts/gh_ci.py failures                    # Resume des echecs CI recents

Prerequis: gh auth login (GitHub CLI authentifie)
"""
import subprocess
import sys
import json
import os
import re
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import safe, log_info, log_error

def _gh(args, timeout=60):
    """Execute une commande gh et retourne (stdout, stderr, returncode)."""
    try:
        r = subprocess.run(
            ["gh"] + args,
            capture_output=True, text=True, timeout=timeout,
            encoding="utf-8", errors="replace"
        )
        return r.stdout.strip(), r.stderr.strip(), r.returncode
    except FileNotFoundError:
        return "", "gh CLI non installe. Installez: https://cli.github.com/", 1
    except subprocess.TimeoutExpired:
        return "", "Timeout (>60s)", 1

def _gh_json(args, timeout=60):
    """Execute gh et parse le JSON."""
    out, err, code = _gh(args, timeout)
    if code != 0:
        return None, err
    try:
        return json.loads(out), None
    except json.JSONDecodeError:
        return out, None

def _check_auth():
    """Verifie l'authentification GH."""
    _, err, code = _gh(["auth", "status"])
    if code != 0:
        print("[!!] GitHub non authentifie.")
        print("     Executez: gh auth login")
        print("     Puis reessayez.")
        return False
    return True

# --- PR Operations ---

@safe
def pr_list(state="open", limit=20):
    """Liste les PRs."""
    if not _check_auth(): return
    fields = "number,title,author,state,createdAt,updatedAt,headRefName,baseRefName,additions,deletions,changedFiles"
    data, err = _gh_json(["pr", "list", "--state", state, "--limit", str(limit), "--json", fields])
    if err:
        print(f"[INFO] {err}")
        return

    if not data:
        print(f"[OK] Aucune PR ({state})")
        return

    print(f"\n=== PRs ({state}) — {len(data)} resultats ===\n")
    for pr in data:
        author = pr.get("author", {}).get("login", "?")
        adds = pr.get("additions", 0)
        dels = pr.get("deletions", 0)
        files = pr.get("changedFiles", 0)
        print(f"  #{pr['number']:5d}  {pr['title'][:60]:60s}  [{author}]")
        print(f"         {pr['headRefName']} -> {pr['baseRefName']}  +{adds}/-{dels} ({files} fichiers)  {pr['state']}")

@safe
def pr_view(number):
    """Detail complet d'une PR."""
    if not _check_auth(): return
    fields = "number,title,body,author,state,createdAt,updatedAt,mergedAt,closedAt,headRefName,baseRefName,additions,deletions,changedFiles,reviewDecision,labels,milestone,assignees,reviews"
    data, err = _gh_json(["pr", "view", str(number), "--json", fields])
    if err:
        print(f"[ERREUR] {err}")
        return

    print(f"\n=== PR #{data['number']}: {data['title']} ===\n")
    author = data.get("author", {}).get("login", "?")
    print(f"  Auteur     : {author}")
    print(f"  Etat       : {data['state']}")
    print(f"  Branche    : {data['headRefName']} -> {data['baseRefName']}")
    print(f"  Cree       : {data['createdAt'][:19]}")
    print(f"  MAJ        : {data['updatedAt'][:19]}")
    if data.get("mergedAt"):
        print(f"  Merge      : {data['mergedAt'][:19]}")
    print(f"  Changements: +{data.get('additions',0)}/-{data.get('deletions',0)} ({data.get('changedFiles',0)} fichiers)")
    print(f"  Decision   : {data.get('reviewDecision', 'N/A')}")

    labels = [l.get("name", "") for l in data.get("labels", [])]
    if labels:
        print(f"  Labels     : {', '.join(labels)}")

    assignees = [a.get("login", "") for a in data.get("assignees", [])]
    if assignees:
        print(f"  Assignes   : {', '.join(assignees)}")

    reviews = data.get("reviews", [])
    if reviews:
        print(f"\n  Reviews ({len(reviews)}):")
        for rev in reviews[-5:]:
            reviewer = rev.get("author", {}).get("login", "?")
            state = rev.get("state", "?")
            print(f"    [{state}] {reviewer} — {rev.get('submittedAt', '')[:19]}")

    if data.get("body"):
        print(f"\n  Description:\n  {'  '.join(data['body'][:500].split(chr(10)))}")

@safe
def pr_diff(number):
    """Diff d'une PR."""
    if not _check_auth(): return
    out, err, code = _gh(["pr", "diff", str(number)], timeout=30)
    if code != 0:
        print(f"[ERREUR] {err}")
        return
    # Afficher un resume + les premieres lignes
    lines = out.split("\n")
    files_changed = [l for l in lines if l.startswith("diff --git")]
    print(f"\n=== Diff PR #{number} — {len(files_changed)} fichier(s) ===\n")

    # Afficher fichiers modifies
    for f in files_changed:
        parts = f.split(" b/")
        fname = parts[-1] if len(parts) > 1 else f
        print(f"  M {fname}")

    # Stats par fichier
    print(f"\n--- Diff (troncature a 200 lignes) ---\n")
    for line in lines[:200]:
        print(line)
    if len(lines) > 200:
        print(f"\n  ... {len(lines) - 200} lignes supplementaires (utilisez gh pr diff {number} pour le diff complet)")

@safe
def pr_reviews(number):
    """Comments de review d'une PR."""
    if not _check_auth(): return
    data, err = _gh_json(["api", f"repos/{{owner}}/{{repo}}/pulls/{number}/comments",
                          "--jq", ".[].body"], timeout=30)
    # Fallback: use pr view
    out, err2, code = _gh(["pr", "view", str(number), "--comments"], timeout=30)
    if code == 0:
        print(f"\n=== Reviews/Comments PR #{number} ===\n")
        print(out[:3000] if out else "[OK] Aucun commentaire")
    else:
        print(f"[INFO] {err2 or err}")

@safe
def pr_files(number):
    """Fichiers modifies dans une PR."""
    if not _check_auth(): return
    data, err = _gh_json(["pr", "view", str(number), "--json", "files"])
    if err:
        print(f"[ERREUR] {err}")
        return
    files = data.get("files", [])
    print(f"\n=== Fichiers PR #{number} — {len(files)} fichier(s) ===\n")
    total_add, total_del = 0, 0
    for f in files:
        adds = f.get("additions", 0)
        dels = f.get("deletions", 0)
        total_add += adds
        total_del += dels
        print(f"  {f.get('path', '?'):60s}  +{adds}/-{dels}")
    print(f"\n  Total: +{total_add}/-{total_del}")

# --- CI/CD Operations ---

@safe
def ci_checks(ref=None):
    """Checks CI d'un commit ou de la PR courante."""
    if not _check_auth(): return
    cmd = ["pr", "checks"]
    if ref:
        cmd = ["pr", "checks", ref]

    out, err, code = _gh(cmd)
    if code == 0:
        print(f"\n=== Checks CI ===\n")
        print(out)
    else:
        # Try run list as fallback
        print(f"[INFO] {err or 'Pas de checks PR. Tentative via workflow runs...'}")
        ci_runs(limit=5)

@safe
def ci_runs(limit=10):
    """Dernieres executions de workflows CI."""
    if not _check_auth(): return
    data, err = _gh_json(["run", "list", "--limit", str(limit), "--json",
                          "databaseId,name,status,conclusion,headBranch,event,createdAt,updatedAt"])
    if err:
        print(f"[INFO] {err}")
        return

    if not data:
        print("[OK] Aucune execution CI trouvee.")
        return

    print(f"\n=== Dernieres executions CI ({len(data)}) ===\n")
    for run in data:
        status = run.get("conclusion") or run.get("status", "?")
        icon = "[OK]" if status == "success" else "[!!]" if status in ("failure", "cancelled") else "[..]"
        branch = run.get("headBranch", "?")
        print(f"  {icon} #{run['databaseId']}  {run['name'][:40]:40s}  [{status}]  {branch}  {run.get('createdAt','')[:19]}")

@safe
def ci_run_view(run_id):
    """Detail d'un run CI."""
    if not _check_auth(): return
    out, err, code = _gh(["run", "view", str(run_id)])
    if code == 0:
        print(out)
    else:
        print(f"[ERREUR] {err}")

@safe
def ci_run_log(run_id):
    """Telecharge et affiche les logs d'un run CI (echecs seulement)."""
    if not _check_auth(): return
    out, err, code = _gh(["run", "view", str(run_id), "--log-failed"], timeout=120)
    if code == 0:
        lines = out.split("\n")
        print(f"\n=== Logs echecs Run #{run_id} ({len(lines)} lignes) ===\n")
        # Afficher les lignes d'erreur en priorite
        error_lines = [l for l in lines if any(kw in l.lower() for kw in ["error", "fail", "exception", "assert", "panic"])]
        if error_lines:
            print("--- Lignes d'erreur cles ---")
            for l in error_lines[:50]:
                print(f"  {l}")
            print(f"\n--- Contexte complet (200 dernieres lignes) ---")
        for l in lines[-200:]:
            print(l)
    else:
        # Fallback: all logs
        out2, err2, code2 = _gh(["run", "view", str(run_id), "--log"], timeout=120)
        if code2 == 0:
            lines = out2.split("\n")
            print(f"[INFO] Pas de logs d'echec specifiques. Logs complets ({len(lines)} lignes, dernieres 100):")
            for l in lines[-100:]:
                print(l)
        else:
            print(f"[ERREUR] {err2 or err}")

@safe
def ci_failures():
    """Resume des echecs CI recents."""
    if not _check_auth(): return
    data, err = _gh_json(["run", "list", "--limit", "30", "--json",
                          "databaseId,name,status,conclusion,headBranch,event,createdAt"])
    if err:
        print(f"[INFO] {err}")
        return

    failures = [r for r in (data or []) if r.get("conclusion") in ("failure", "cancelled")]
    if not failures:
        print("[OK] Aucun echec CI dans les 30 derniers runs.")
        return

    print(f"\n=== Echecs CI recents — {len(failures)}/{len(data)} runs ===\n")
    # Group by workflow name
    by_name = {}
    for f in failures:
        name = f.get("name", "?")
        by_name.setdefault(name, []).append(f)

    for name, runs in by_name.items():
        print(f"  {name} — {len(runs)} echec(s)")
        for r in runs[:3]:
            print(f"    #{r['databaseId']}  [{r['conclusion']}]  {r['headBranch']}  {r['createdAt'][:19]}")
        if len(runs) > 3:
            print(f"    ... et {len(runs) - 3} autres")

    print(f"\n  [TIP] Utilisez 'cx ghci run-log <run_id>' pour voir les logs d'un echec")

# --- Branch & Commit Operations ---

@safe
def list_branches(limit=20):
    """Liste les branches du repo."""
    if not _check_auth(): return
    out, err, code = _gh(["api", "repos/{owner}/{repo}/branches", "--jq",
                          f".[:{ limit}][] | .name"], timeout=30)
    if code == 0 and out:
        branches = out.split("\n")
        print(f"\n=== Branches ({len(branches)}) ===\n")
        for b in branches:
            print(f"  {b}")
    else:
        # Fallback git
        r = subprocess.run(["git", "branch", "-a"], capture_output=True, text=True)
        print(r.stdout if r.returncode == 0 else f"[INFO] {err}")

@safe
def list_commits(limit=15, branch=None):
    """Derniers commits."""
    if not _check_auth(): return
    cmd = ["log", "--oneline", f"-{limit}"]
    if branch:
        cmd.append(branch)
    r = subprocess.run(["git"] + cmd, capture_output=True, text=True)
    if r.returncode == 0:
        print(f"\n=== Derniers commits ({limit}) ===\n")
        print(r.stdout)
    else:
        print(f"[ERREUR] {r.stderr}")

@safe
def diff_refs(ref1, ref2=None):
    """Diff entre deux refs."""
    cmd = ["git", "diff", ref1]
    if ref2:
        cmd.append(ref2)
    cmd.append("--stat")
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode == 0:
        print(f"\n=== Diff {ref1}{'..'+ref2 if ref2 else ''} ===\n")
        print(r.stdout)
    else:
        print(f"[ERREUR] {r.stderr}")

@safe
def blame_file(filepath, line_range=None):
    """Git blame via GH."""
    cmd = ["git", "blame", filepath]
    if line_range:
        cmd.extend(["-L", line_range])
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if r.returncode == 0:
        print(r.stdout[:3000])
    else:
        print(f"[ERREUR] {r.stderr}")


COMMANDS = {
    "pr-list":    "pr_list",
    "pr-view":    "pr_view",
    "pr-diff":    "pr_diff",
    "pr-reviews": "pr_reviews",
    "pr-files":   "pr_files",
    "checks":     "ci_checks",
    "runs":       "ci_runs",
    "run-view":   "ci_run_view",
    "run-log":    "ci_run_log",
    "failures":   "ci_failures",
    "branches":   "list_branches",
    "commits":    "list_commits",
    "diff":       "diff_refs",
    "blame":      "blame_file",
}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GitHub/CI MCP — Lecture avancee")
    parser.add_argument("action", choices=list(COMMANDS.keys()),
                       help="Action a executer")
    parser.add_argument("args", nargs="*", help="Arguments supplementaires")
    parser.add_argument("--state", default="open")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--branch", default=None)
    parser.add_argument("--line", default=None)
    parsed = parser.parse_args()

    action = parsed.action
    extra = parsed.args

    if action == "pr-list":
        pr_list(parsed.state, parsed.limit)
    elif action == "pr-view" and extra:
        pr_view(extra[0])
    elif action == "pr-diff" and extra:
        pr_diff(extra[0])
    elif action == "pr-reviews" and extra:
        pr_reviews(extra[0])
    elif action == "pr-files" and extra:
        pr_files(extra[0])
    elif action == "checks":
        ci_checks(extra[0] if extra else None)
    elif action == "runs":
        ci_runs(parsed.limit)
    elif action == "run-view" and extra:
        ci_run_view(extra[0])
    elif action == "run-log" and extra:
        ci_run_log(extra[0])
    elif action == "failures":
        ci_failures()
    elif action == "branches":
        list_branches(parsed.limit)
    elif action == "commits":
        list_commits(parsed.limit, parsed.branch)
    elif action == "diff" and extra:
        diff_refs(extra[0], extra[1] if len(extra) > 1 else None)
    elif action == "blame" and extra:
        blame_file(extra[0], parsed.line)
    else:
        parser.print_help()
