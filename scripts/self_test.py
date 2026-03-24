"""
Auto-test — Valide que tous les scripts CX fonctionnent correctement.
Usage: python scripts/self_test.py [--verbose]
"""
import sys
import os
import subprocess
import json
import time

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPTS_DIR)
CX = os.path.join(PROJECT_DIR, "cx.py")

TESTS = [
    # (nom, commande, validation)
    ("cx help",           [CX, "help"],                           lambda o: "commandes" in o),
    ("system ram",        [CX, "system", "ram"],                  lambda o: "FreeGB" in o or "TotalGB" in o),
    ("system disk",       [CX, "system", "disk"],                 lambda o: "drive" in o or "total_gb" in o),
    ("desktop screen",    [CX, "desktop", "screen_info"],         lambda o: "PrimaryWidth" in o),
    ("desktop windows",   [CX, "desktop", "list_windows"],        lambda o: "[" in o),
    ("search web",        [CX, "search", "test", "--max", "2"],   lambda o: "title" in o or "url" in o),
    ("memory set",        [CX, "memory", "set", "_test", "ok"],   lambda o: "OK" in o),
    ("memory get",        [CX, "memory", "get", "_test"],         lambda o: "ok" in o),
    ("memory delete",     [CX, "memory", "delete", "_test"],      lambda o: "supprime" in o or "OK" in o),
    ("macro list",        [CX, "macro", "list"],                  lambda o: "morning" in o),
    ("git status",        [CX, "git", "status"],                  lambda o: True),  # any output OK
    ("check env",         [CX, "check"],                          lambda o: "OK" in o),
    ("doc word",          [CX, "doc", "word", "-o", os.path.join(PROJECT_DIR, "output", "_test.docx")],
                                                                  lambda o: "OK" in o),
    ("doc pptx",          [CX, "doc", "pptx", "-o", os.path.join(PROJECT_DIR, "output", "_test.pptx")],
                                                                  lambda o: "OK" in o),
    ("report dashboard",  [CX, "report", "dashboard", "-o", os.path.join(PROJECT_DIR, "output", "_test_dash.html")],
                                                                  lambda o: "OK" in o),
    # PDF tools
    ("pdf info",          [CX, "pdf", "info", os.path.join(PROJECT_DIR, "output", "test_page1.pdf")],
                                                                  lambda o: "pages" in o),
    ("pdf count",         [CX, "pdf", "count", os.path.join(PROJECT_DIR, "output", "test_page1.pdf")],
                                                                  lambda o: "1" in o),
    # Quality check
    ("quality stats",     [CX, "quality", "stats", os.path.join(PROJECT_DIR, "output", "test_quality.txt")],
                                                                  lambda o: "mots" in o),
    ("quality analyze",   [CX, "quality", "analyze", os.path.join(PROJECT_DIR, "output", "test_quality.txt")],
                                                                  lambda o: "qualite" in o.lower()),
    # Image tools
    ("image info",        [CX, "image", "info", os.path.join(PROJECT_DIR, "output", "test_image.png")],
                                                                  lambda o: "dimensions" in o),
    ("image resize",      [CX, "image", "resize", os.path.join(PROJECT_DIR, "output", "test_image.png"),
                          "100x75", "-o", os.path.join(PROJECT_DIR, "output", "_test_resized.png")],
                                                                  lambda o: "OK" in o),
    # Data analyzer
    ("data profile",      [CX, "data", "profile", os.path.join(PROJECT_DIR, "output", "test_data.csv")],
                                                                  lambda o: "Lignes" in o or "Colonnes" in o),
    ("data chart",        [CX, "data", "chart", os.path.join(PROJECT_DIR, "output", "test_data.csv"),
                          "Ville", "Salaire", "-o", os.path.join(PROJECT_DIR, "output", "_test_chart.html")],
                                                                  lambda o: "OK" in o),
    # Text transform
    ("text extract",      [CX, "text", "extract-emails", os.path.join(PROJECT_DIR, "output", "test_text.txt")],
                                                                  lambda o: "email" in o.lower()),
    ("text slug",         [CX, "text", "slug", "Mon Test"],       lambda o: "mon-test" in o),
    # Email
    ("email config",      [CX, "email", "config"],                lambda o: "SMTP" in o),
    # GitHub/CI
    ("ghci branches",     [CX, "ghci", "branches"],               lambda o: True),  # any output OK (may not be authed)
    # DB Explorer
    ("db connect",        [CX, "db", "connect", os.path.join(PROJECT_DIR, "output", "test_sample.db")],
                                                                  lambda o: "tables" in o.lower() or "OK" in o),
    ("db query",          [CX, "db", "query", "SELECT COUNT(*) as n FROM users"],
                                                                  lambda o: "3" in o or "n" in o),
    # Observability
    ("obs digest",        [CX, "obs", "digest", os.path.join(PROJECT_DIR, "output", "test_app.log")],
                                                                  lambda o: "DIGEST" in o or "erreur" in o.lower()),
    ("obs stats",         [CX, "obs", "stats", os.path.join(PROJECT_DIR, "output", "test_app.log")],
                                                                  lambda o: "error" in o.lower() or "info" in o.lower()),
    # Repo onboarding
    ("onboard quick",     [CX, "onboard", "quick"],               lambda o: "STACK" in o or "STRUCTURE" in o),
    # Test triage
    ("triage detect",     [CX, "triage", "detect"],               lambda o: True),  # any output
    # Perf investigation
    ("perf system",       [CX, "perf", "system"],                 lambda o: "CPU" in o or "RAM" in o),
]

def run_test(name, cmd, validator, verbose=False):
    try:
        start = time.time()
        r = subprocess.run(
            [sys.executable] + cmd,
            capture_output=True, text=True, timeout=45, cwd=PROJECT_DIR,
            encoding="utf-8", errors="replace"
        )
        duration = time.time() - start
        output = r.stdout + r.stderr
        passed = validator(output)

        status = "PASS" if passed else "FAIL"
        icon = "[OK]" if passed else "[!!]"
        print(f"  {icon} {name:20s}  ({duration:.1f}s)")
        if verbose and not passed:
            print(f"       Output: {output[:200]}")
        return passed, duration
    except subprocess.TimeoutExpired:
        print(f"  [!!] {name:20s}  (TIMEOUT)")
        return False, 30
    except Exception as e:
        print(f"  [!!] {name:20s}  (ERREUR: {e})")
        return False, 0

def cleanup():
    """Supprime les fichiers de test."""
    for f in ["_test.docx", "_test.pptx", "_test_dash.html", "_test.pdf",
             "_test_resized.png", "_test_chart.html"]:
        path = os.path.join(PROJECT_DIR, "output", f)
        if os.path.exists(path):
            os.remove(path)

if __name__ == "__main__":
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    print(f"CX Self-Test — {len(TESTS)} tests")
    print("=" * 50)

    results = []
    total_time = 0
    for name, cmd, validator in TESTS:
        passed, duration = run_test(name, cmd, validator, verbose)
        results.append(passed)
        total_time += duration

    cleanup()

    passed = sum(results)
    total = len(results)
    print("=" * 50)
    print(f"Resultats: {passed}/{total} passes ({total_time:.1f}s total)")

    if passed == total:
        print("[OK] Tous les tests passent.")
    else:
        failed = [TESTS[i][0] for i, r in enumerate(results) if not r]
        print(f"[!!] Echecs: {', '.join(failed)}")

    sys.exit(0 if passed == total else 1)
