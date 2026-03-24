"""
Script d'installation des dépendances manquantes courantes.
Usage: python scripts/install_deps.py
"""
import subprocess
import sys

REQUIRED_PACKAGES = [
    "requests",
    "httpx",
    "pandas",
    "openpyxl",
    "python-docx",
    "python-pptx",
    "reportlab",
    "PyPDF2",
    "Pillow",
    "beautifulsoup4",
    "lxml",
    "pyyaml",
    "rich",
    "typer",
    "jinja2",
]

def check_and_install():
    missing = []
    for pkg in REQUIRED_PACKAGES:
        import_name = pkg.replace("-", "_").lower()
        try:
            __import__(import_name)
        except ImportError:
            missing.append(pkg)

    if not missing:
        print("[OK] Toutes les dependances sont deja installees.")
        return

    print(f"[+] Installation de {len(missing)} packages manquants : {', '.join(missing)}")
    subprocess.check_call([sys.executable, "-m", "pip", "install", *missing, "-q"])
    print("[OK] Installation terminee.")

if __name__ == "__main__":
    check_and_install()
