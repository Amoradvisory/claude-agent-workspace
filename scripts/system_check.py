"""
Diagnostic rapide de l'environnement.
Usage: python scripts/system_check.py
"""
import subprocess
import shutil
import sys

def check(name, cmd):
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        version = result.stdout.strip().split("\n")[0]
        print(f"  [OK] {name}: {version}")
        return True
    except Exception:
        print(f"  [!!] {name}: NON DISPONIBLE")
        return False

def check_python_pkg(pkg):
    try:
        mod = __import__(pkg.replace("-", "_"))
        ver = getattr(mod, "__version__", "installed")
        print(f"  [OK] {pkg}: {ver}")
        return True
    except ImportError:
        print(f"  [!!] {pkg}: MANQUANT")
        return False

print("=== RUNTIMES ===")
check("Python", [sys.executable, "--version"])
check("Node", ["node", "--version"])
check("Git", ["git", "--version"])
check("GH CLI", ["gh", "--version"])

print("\n=== PACKAGES PYTHON ===")
packages = [
    "anthropic", "requests", "httpx", "pandas", "openpyxl",
    "docx", "pptx", "PIL", "bs4", "yaml", "rich", "jinja2",
    "reportlab", "PyPDF2", "claude_agent_sdk",
]
ok = sum(check_python_pkg(p) for p in packages)
print(f"\n  {ok}/{len(packages)} packages disponibles")

print("\n=== PACKAGES NPM GLOBAL ===")
check("npm globals", ["npm", "list", "-g", "--depth=0"])

print("\n=== ESPACE DISQUE ===")
total, used, free = shutil.disk_usage("C:/")
print(f"  Total: {total // (1024**3)} GB | Libre: {free // (1024**3)} GB")

print("\n[OK] Diagnostic termine.")
