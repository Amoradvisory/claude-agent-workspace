"""
Module commun — Fonctions partagees par tous les scripts CX.
Import: from scripts._common import ensure, safe, log, PROJECT_DIR, SCRIPTS_DIR, OUTPUT_DIR
"""
import sys
import os
import json
import traceback
from datetime import datetime
from functools import wraps

# === Chemins globaux ===
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPTS_DIR)
OUTPUT_DIR = os.path.join(PROJECT_DIR, "output")
MEMORY_DIR = os.path.join(PROJECT_DIR, "memory")
CONFIGS_DIR = os.path.join(PROJECT_DIR, "configs")
LOG_FILE = os.path.join(MEMORY_DIR, "activity.log")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(MEMORY_DIR, exist_ok=True)

# === Auto-install de dependances ===
def ensure(pkg, import_name=None):
    """Installe un package s'il est absent et le retourne."""
    name = import_name or pkg.replace("-", "_")
    try:
        return __import__(name)
    except ImportError:
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg, "-q"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return __import__(name)

# === Logging structure ===
def log(level, message, context=None):
    """Log structure dans activity.log + stdout."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{ts}] [{level.upper():5s}] {message}"
    if context:
        entry += f" | {json.dumps(context, ensure_ascii=False, default=str)}"

    # Fichier
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(entry + "\n")
    except Exception:
        pass

    # Console (si erreur ou info)
    if level.upper() in ("ERROR", "WARN"):
        print(entry, file=sys.stderr)

def log_info(msg, ctx=None):
    log("INFO", msg, ctx)

def log_error(msg, ctx=None):
    log("ERROR", msg, ctx)

def log_warn(msg, ctx=None):
    log("WARN", msg, ctx)

# === Wrapper de securite ===
def safe(func):
    """Decorateur qui attrape les erreurs et les log proprement."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyboardInterrupt:
            print("\n[STOP] Interrompu.")
            sys.exit(0)
        except Exception as e:
            log_error(f"{func.__name__} a echoue: {e}", {"args": str(args)[:200]})
            print(f"[ERREUR] {func.__name__}: {e}")
            if os.environ.get("CX_DEBUG"):
                traceback.print_exc()
            return None
    return wrapper

# === Sortie JSON propre (gere cp1252 Windows) ===
def print_json(data, indent=2):
    """Affiche du JSON en gerant l'encodage Windows."""
    output = json.dumps(data, indent=indent, ensure_ascii=False, default=str)
    try:
        sys.stdout.buffer.write(output.encode("utf-8", errors="replace"))
        sys.stdout.buffer.write(b"\n")
    except Exception:
        print(output)

# === Chargement de tokens ===
def get_token(name):
    """Recupere un token depuis env ou configs/.env."""
    val = os.environ.get(name)
    if val:
        return val
    env_path = os.path.join(CONFIGS_DIR, ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith(f"{name}="):
                    return line.split("=", 1)[1].strip()
    return None

# === Utilitaires fichiers ===
def output_path(filename):
    """Genere un chemin dans output/."""
    return os.path.join(OUTPUT_DIR, filename)

def read_json(path):
    """Lit un fichier JSON."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def write_json(path, data):
    """Ecrit un fichier JSON."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)
