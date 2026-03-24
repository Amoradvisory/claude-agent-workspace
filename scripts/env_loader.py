"""
Chargeur de variables d'environnement depuis configs/.env
Import: from scripts.env_loader import load_env, get_token
"""
import os

ENV_PATH = os.path.join(os.path.dirname(__file__), "..", "configs", ".env")

def load_env(path=None):
    """Charge les variables depuis .env dans os.environ."""
    path = path or ENV_PATH
    if not os.path.exists(path):
        return {}
    loaded = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, val = line.split("=", 1)
                key, val = key.strip(), val.strip()
                if val:
                    os.environ[key] = val
                    loaded[key] = val
    return loaded

def get_token(name):
    """Recupere un token depuis l'env ou .env."""
    val = os.environ.get(name)
    if not val:
        load_env()
        val = os.environ.get(name)
    return val

if __name__ == "__main__":
    loaded = load_env()
    for k in loaded:
        masked = loaded[k][:8] + "..." if len(loaded[k]) > 8 else loaded[k]
        print(f"  {k} = {masked}")
    print(f"[OK] {len(loaded)} variables chargees")
