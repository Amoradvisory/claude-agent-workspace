"""
Test Triage — Reproduire, classifier et diagnostiquer les tests en echec.
Usage:
  python scripts/test_triage.py run [<path>] [--cmd "pytest"]       # Lancer les tests et trier
  python scripts/test_triage.py rerun <test_id> [--times 3]         # Re-executer un test N fois (flaky?)
  python scripts/test_triage.py isolate <test_id>                   # Trouver la commande minimale
  python scripts/test_triage.py report [<path>]                     # Rapport de triage complet
  python scripts/test_triage.py detect [<path>]                     # Auto-detecter le framework de test

Auto-detect: pytest, jest, vitest, go test, cargo test, unittest, mocha, rspec
"""
import sys
import os
import re
import json
import subprocess
import argparse
import time
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import safe, log_info, log_error, OUTPUT_DIR

# ============= TEST FRAMEWORK DETECTION =============

def detect_test_framework(root):
    """Detecte le framework de test."""
    root = os.path.abspath(root)
    frameworks = []

    # Python
    if os.path.exists(os.path.join(root, "pytest.ini")) or \
       os.path.exists(os.path.join(root, "setup.cfg")) or \
       os.path.exists(os.path.join(root, "pyproject.toml")):
        # Check for pytest config
        for f in ["pyproject.toml", "setup.cfg", "pytest.ini"]:
            path = os.path.join(root, f)
            if os.path.exists(path):
                with open(path, "r", errors="replace") as fh:
                    if "pytest" in fh.read():
                        frameworks.append({"name": "pytest", "cmd": "pytest -v", "lang": "Python"})
                        break
    if os.path.exists(os.path.join(root, "tests")) or os.path.exists(os.path.join(root, "test")):
        if not any(f["name"] == "pytest" for f in frameworks):
            # Check if pytest is importable
            r = subprocess.run([sys.executable, "-c", "import pytest"], capture_output=True)
            if r.returncode == 0:
                frameworks.append({"name": "pytest", "cmd": "pytest -v", "lang": "Python"})
            else:
                frameworks.append({"name": "unittest", "cmd": f"{sys.executable} -m unittest discover -v", "lang": "Python"})

    # Node.js
    pkg_path = os.path.join(root, "package.json")
    if os.path.exists(pkg_path):
        with open(pkg_path, "r", errors="replace") as f:
            try:
                pkg = json.load(f)
            except Exception:
                pkg = {}
        deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
        scripts = pkg.get("scripts", {})

        if "vitest" in deps or "vitest" in scripts.get("test", ""):
            frameworks.append({"name": "vitest", "cmd": "npx vitest run", "lang": "JavaScript"})
        elif "jest" in deps or "@jest" in str(deps):
            frameworks.append({"name": "jest", "cmd": "npx jest --verbose", "lang": "JavaScript"})
        elif "mocha" in deps:
            frameworks.append({"name": "mocha", "cmd": "npx mocha", "lang": "JavaScript"})
        elif "test" in scripts:
            frameworks.append({"name": "npm-test", "cmd": "npm test", "lang": "JavaScript"})

    # Go
    if os.path.exists(os.path.join(root, "go.mod")):
        frameworks.append({"name": "go-test", "cmd": "go test ./... -v", "lang": "Go"})

    # Rust
    if os.path.exists(os.path.join(root, "Cargo.toml")):
        frameworks.append({"name": "cargo-test", "cmd": "cargo test", "lang": "Rust"})

    # Ruby
    if os.path.exists(os.path.join(root, "Gemfile")):
        gemfile = ""
        with open(os.path.join(root, "Gemfile"), "r", errors="replace") as f:
            gemfile = f.read()
        if "rspec" in gemfile:
            frameworks.append({"name": "rspec", "cmd": "bundle exec rspec", "lang": "Ruby"})

    return frameworks


# ============= TEST EXECUTION & PARSING =============

def _run_tests(cmd, cwd, timeout=300):
    """Execute les tests et capture la sortie."""
    try:
        start = time.time()
        r = subprocess.run(
            cmd, shell=True, capture_output=True, text=True,
            timeout=timeout, cwd=cwd, encoding="utf-8", errors="replace"
        )
        duration = time.time() - start
        return {
            "stdout": r.stdout,
            "stderr": r.stderr,
            "returncode": r.returncode,
            "duration": duration,
            "command": cmd,
        }
    except subprocess.TimeoutExpired:
        return {"stdout": "", "stderr": "TIMEOUT", "returncode": -1, "duration": timeout, "command": cmd}
    except Exception as e:
        return {"stdout": "", "stderr": str(e), "returncode": -1, "duration": 0, "command": cmd}


def _parse_pytest(output):
    """Parse la sortie pytest."""
    results = {"passed": [], "failed": [], "errors": [], "skipped": [], "warnings": []}

    for line in output.split("\n"):
        # PASSED/FAILED lines
        if " PASSED" in line:
            m = re.match(r"(.+?)\s+PASSED", line)
            if m:
                results["passed"].append(m.group(1).strip())
        elif " FAILED" in line:
            m = re.match(r"(.+?)\s+FAILED", line)
            if m:
                results["failed"].append(m.group(1).strip())
        elif " ERROR" in line:
            m = re.match(r"(.+?)\s+ERROR", line)
            if m:
                results["errors"].append(m.group(1).strip())
        elif " SKIPPED" in line:
            results["skipped"].append(line.strip())

    # Extract failure details
    failure_blocks = re.findall(r"_{5,} (.+?) _{5,}\n(.*?)(?=_{5,}|\Z)", output, re.DOTALL)
    failure_details = {}
    for name, body in failure_blocks:
        failure_details[name.strip()] = body.strip()[:500]

    # Summary line
    summary = re.search(r"=+ (.+?) =+\s*$", output, re.MULTILINE)

    return results, failure_details, summary.group(1) if summary else ""


def _parse_jest(output):
    """Parse la sortie Jest/Vitest."""
    results = {"passed": [], "failed": [], "errors": [], "skipped": []}

    for line in output.split("\n"):
        line = line.strip()
        if line.startswith("✓") or line.startswith("√") or "PASS" in line:
            results["passed"].append(line)
        elif line.startswith("✕") or line.startswith("×") or "FAIL" in line:
            results["failed"].append(line)
        elif "skip" in line.lower():
            results["skipped"].append(line)

    return results, {}, ""


def _parse_generic(output):
    """Parse generique."""
    results = {"passed": [], "failed": [], "errors": [], "skipped": []}

    for line in output.split("\n"):
        lower = line.lower()
        if "pass" in lower and ("test" in lower or "spec" in lower):
            results["passed"].append(line.strip())
        elif "fail" in lower and ("test" in lower or "spec" in lower or "assert" in lower):
            results["failed"].append(line.strip())
        elif "error" in lower or "panic" in lower:
            results["errors"].append(line.strip())
        elif "skip" in lower:
            results["skipped"].append(line.strip())

    return results, {}, ""


# ============= CLASSIFICATION =============

def classify_failure(test_name, detail, rerun_results=None):
    """Classifie un echec: flaky, env, regression."""
    classification = "regression"  # default
    confidence = "medium"
    hints = []

    detail_lower = detail.lower() if detail else ""

    # Flaky detection
    if rerun_results:
        pass_count = sum(1 for r in rerun_results if r)
        fail_count = len(rerun_results) - pass_count
        if pass_count > 0 and fail_count > 0:
            classification = "flaky"
            confidence = "high"
            hints.append(f"Passe {pass_count}/{len(rerun_results)} fois — test intermittent")

    # Environment problems
    env_patterns = [
        (r"connection refused", "Connexion refusee — service non demarre?"),
        (r"timeout|timed out", "Timeout — service lent ou indisponible?"),
        (r"permission denied", "Permission refusee — droits insuffisants"),
        (r"no such file|file not found|not found", "Fichier manquant — config ou fixture?"),
        (r"port.*in use|address.*in use", "Port deja utilise"),
        (r"out of memory|oom", "Memoire insuffisante"),
        (r"database.*not.*exist|relation.*does not exist", "Base de donnees non initialisee?"),
        (r"migration", "Probleme de migration DB?"),
        (r"import error|module.*not found|cannot find module", "Dependance manquante"),
    ]
    for pattern, hint in env_patterns:
        if re.search(pattern, detail_lower):
            classification = "environment"
            hints.append(hint)

    return {
        "classification": classification,
        "confidence": confidence,
        "hints": hints,
    }


# ============= COMMANDS =============

@safe
def cmd_detect(path):
    """Auto-detecte le framework de test."""
    frameworks = detect_test_framework(os.path.abspath(path))
    if frameworks:
        print(f"\n=== Frameworks detectes ({len(frameworks)}) ===\n")
        for fw in frameworks:
            print(f"  [{fw['lang']}] {fw['name']}")
            print(f"    Commande: {fw['cmd']}")
    else:
        print("[INFO] Aucun framework de test detecte.")
    return frameworks

@safe
def cmd_run(path, cmd=None):
    """Lance les tests et trie les resultats."""
    root = os.path.abspath(path)

    # Auto-detect if no command
    if not cmd:
        frameworks = detect_test_framework(root)
        if not frameworks:
            print("[ERREUR] Aucun framework detecte. Utilisez --cmd pour specifier la commande.")
            return
        cmd = frameworks[0]["cmd"]
        fw_name = frameworks[0]["name"]
    else:
        fw_name = "custom"

    print(f"\n=== Test Run: {cmd} ===\n")

    result = _run_tests(cmd, root)

    if result["returncode"] == -1 and result["stderr"] == "TIMEOUT":
        print("[!!] TIMEOUT — Les tests ont depasse la limite de 5 minutes")
        return

    output = result["stdout"] + "\n" + result["stderr"]

    # Parse based on framework
    if "pytest" in fw_name:
        results, details, summary = _parse_pytest(output)
    elif fw_name in ("jest", "vitest"):
        results, details, summary = _parse_jest(output)
    else:
        results, details, summary = _parse_generic(output)

    # Display results
    n_passed = len(results["passed"])
    n_failed = len(results["failed"])
    n_errors = len(results["errors"])
    n_skipped = len(results["skipped"])
    total = n_passed + n_failed + n_errors

    print(f"  Resultats: {n_passed} passes, {n_failed} echecs, {n_errors} erreurs, {n_skipped} ignores")
    print(f"  Duree: {result['duration']:.1f}s")
    print(f"  Code retour: {result['returncode']}")

    if n_failed == 0 and n_errors == 0:
        print(f"\n  [OK] Tous les tests passent!")
        return

    # Triage des echecs
    print(f"\n  === TRIAGE DES ECHECS ({n_failed + n_errors}) ===\n")

    all_failures = results["failed"] + results["errors"]
    for test in all_failures:
        detail = details.get(test, "")
        classification = classify_failure(test, detail)

        icon = {"regression": "[BUG]", "environment": "[ENV]", "flaky": "[~]"}
        print(f"  {icon.get(classification['classification'], '[?]')} {test}")
        print(f"       Type: {classification['classification']} (confiance: {classification['confidence']})")
        if classification["hints"]:
            for h in classification["hints"]:
                print(f"       -> {h}")
        if detail:
            # Show first few lines of detail
            for line in detail.split("\n")[:5]:
                print(f"       {line}")
        print()

    # Recommendations
    print("  === ACTIONS RECOMMANDEES ===\n")
    env_count = sum(1 for t in all_failures if classify_failure(t, details.get(t, ""))["classification"] == "environment")
    reg_count = sum(1 for t in all_failures if classify_failure(t, details.get(t, ""))["classification"] == "regression")

    if env_count > 0:
        print(f"  1. {env_count} echec(s) lies a l'environnement — verifiez les services/configs requis")
    if reg_count > 0:
        print(f"  2. {reg_count} regression(s) probables — verifiez les changements recents")
    print(f"  3. Re-executez les echecs individuellement: cx triage rerun <test_id> --times 3")
    print(f"  4. Commande minimale: cx triage isolate <test_id>")

@safe
def cmd_rerun(test_id, times=3, cmd=None):
    """Re-execute un test N fois pour detecter le flaky."""
    if not cmd:
        frameworks = detect_test_framework(".")
        if not frameworks:
            print("[ERREUR] Framework non detecte. Utilisez --cmd")
            return
        base_cmd = frameworks[0]["cmd"]
        fw_name = frameworks[0]["name"]
    else:
        base_cmd = cmd
        fw_name = "custom"

    # Build specific test command
    if "pytest" in fw_name:
        specific_cmd = f"pytest -v {test_id}"
    elif fw_name in ("jest", "vitest"):
        specific_cmd = f"npx {fw_name} run -t \"{test_id}\""
    elif "go" in fw_name:
        specific_cmd = f"go test -run {test_id} -v ./..."
    else:
        specific_cmd = f"{base_cmd} {test_id}"

    print(f"\n=== Rerun: {test_id} ({times}x) ===")
    print(f"  Commande: {specific_cmd}\n")

    results = []
    for i in range(times):
        r = _run_tests(specific_cmd, ".", timeout=60)
        passed = r["returncode"] == 0
        results.append(passed)
        icon = "[OK]" if passed else "[!!]"
        print(f"  Run #{i+1}: {icon}  ({r['duration']:.1f}s)")

    pass_count = sum(results)
    fail_count = times - pass_count

    print(f"\n  Resultats: {pass_count}/{times} passes")

    if pass_count == times:
        print("  -> Test STABLE (passe a chaque fois)")
    elif fail_count == times:
        print("  -> Test CASSE (echoue a chaque fois) — probablement une vraie regression")
    else:
        print(f"  -> Test FLAKY (intermittent) — passe {pass_count}/{times} fois")
        print("     Actions: marquer comme flaky, ajouter retry, ou investiguer la cause racine")

@safe
def cmd_isolate(test_id, cmd=None):
    """Trouve la commande de reproduction minimale."""
    frameworks = detect_test_framework(".")
    if not cmd and frameworks:
        fw = frameworks[0]
    elif cmd:
        fw = {"name": "custom", "cmd": cmd}
    else:
        print("[ERREUR] Framework non detecte.")
        return

    print(f"\n=== Isolate: {test_id} ===\n")

    commands = []
    if "pytest" in fw["name"]:
        commands = [
            f"pytest -v {test_id}",
            f"pytest -v -x {test_id}",
            f"pytest -v --no-header {test_id}",
            f"pytest -v -p no:cacheprovider {test_id}",
        ]
    elif fw["name"] in ("jest", "vitest"):
        commands = [
            f"npx {fw['name']} run -t \"{test_id}\"",
            f"npx {fw['name']} run --no-cache -t \"{test_id}\"",
        ]
    elif "go" in fw["name"]:
        commands = [
            f"go test -run {test_id} -v ./...",
            f"go test -run {test_id} -count=1 -v ./...",
        ]
    else:
        commands = [f"{fw['cmd']} {test_id}"]

    print("  Commandes de reproduction minimales:\n")
    for i, c in enumerate(commands, 1):
        r = _run_tests(c, ".", timeout=60)
        icon = "[OK]" if r["returncode"] == 0 else "[!!]"
        print(f"  {i}. {icon} {c}")
        print(f"       ({r['duration']:.1f}s, code={r['returncode']})")
        if r["returncode"] != 0:
            # Show last error lines
            err_lines = (r["stdout"] + r["stderr"]).strip().split("\n")
            for line in err_lines[-5:]:
                if line.strip():
                    print(f"       {line.strip()}")
        print()

    print("  [TIP] Copiez la commande la plus courte qui reproduit l'echec.")

@safe
def cmd_report(path):
    """Rapport de triage complet."""
    root = os.path.abspath(path)
    frameworks = detect_test_framework(root)

    print(f"\n{'='*60}")
    print(f"  TEST TRIAGE REPORT")
    print(f"  {root}")
    print(f"{'='*60}\n")

    if not frameworks:
        print("  [INFO] Aucun framework de test detecte.")
        return

    for fw in frameworks:
        print(f"\n  --- {fw['name']} ({fw['lang']}) ---")
        print(f"  Commande: {fw['cmd']}\n")

        result = _run_tests(fw["cmd"], root)
        output = result["stdout"] + "\n" + result["stderr"]

        if "pytest" in fw["name"]:
            results, details, summary = _parse_pytest(output)
        else:
            results, details, summary = _parse_generic(output)

        n_passed = len(results["passed"])
        n_failed = len(results["failed"])
        n_errors = len(results["errors"])

        print(f"  Passes: {n_passed} | Echecs: {n_failed} | Erreurs: {n_errors}")
        print(f"  Duree: {result['duration']:.1f}s")

        if n_failed + n_errors == 0:
            print("  [OK] Tout passe!")
        else:
            for test in results["failed"] + results["errors"]:
                detail = details.get(test, "")
                cl = classify_failure(test, detail)
                print(f"\n  [{cl['classification'].upper()}] {test}")
                for h in cl["hints"]:
                    print(f"    -> {h}")

    print(f"\n{'='*60}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test Triage")
    parser.add_argument("action", choices=["run", "rerun", "isolate", "report", "detect"])
    parser.add_argument("target", nargs="?", default=".")
    parser.add_argument("--cmd", default=None)
    parser.add_argument("--times", type=int, default=3)
    parsed = parser.parse_args()

    if parsed.action == "detect":
        cmd_detect(parsed.target)
    elif parsed.action == "run":
        cmd_run(parsed.target, parsed.cmd)
    elif parsed.action == "rerun":
        cmd_rerun(parsed.target, parsed.times, parsed.cmd)
    elif parsed.action == "isolate":
        cmd_isolate(parsed.target, parsed.cmd)
    elif parsed.action == "report":
        cmd_report(parsed.target)
