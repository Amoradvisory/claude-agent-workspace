"""
Pont Notion rapide — Acces direct via API sans MCP.
Pour des actions simples depuis un script ou une automation.
Usage: python scripts/notion_quick.py search "query"
       python scripts/notion_quick.py list_databases
"""
import sys
import json
import os

def ensure_httpx():
    try:
        import httpx
        return httpx
    except ImportError:
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "httpx", "-q"])
        import httpx
        return httpx

def _get_token():
    """Charge le token depuis .env ou variable d'environnement."""
    token = os.environ.get("NOTION_TOKEN")
    if not token:
        env_path = os.path.join(os.path.dirname(__file__), "..", "configs", ".env")
        if os.path.exists(env_path):
            with open(env_path, "r") as f:
                for line in f:
                    if line.strip().startswith("NOTION_TOKEN="):
                        token = line.strip().split("=", 1)[1].strip()
                        break
    return token

NOTION_VERSION = "2022-06-28"
BASE = "https://api.notion.com/v1"

def _headers():
    token = _get_token()
    if not token:
        raise RuntimeError("NOTION_TOKEN non trouve. Verifier configs/.env")
    return {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }

def search(query):
    httpx = ensure_httpx()
    r = httpx.post(f"{BASE}/search", headers=_headers(), json={"query": query, "page_size": 10}, timeout=15)
    results = r.json().get("results", [])
    out = []
    for item in results:
        title = ""
        if item["object"] == "page":
            props = item.get("properties", {})
            for v in props.values():
                if v.get("type") == "title" and v.get("title"):
                    title = "".join(t.get("plain_text", "") for t in v["title"])
                    break
        elif item["object"] == "database":
            title_list = item.get("title", [])
            title = "".join(t.get("plain_text", "") for t in title_list)
        out.append({"id": item["id"], "type": item["object"], "title": title, "url": item.get("url", "")})
    return out

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: notion_quick.py <search|list_databases> [args]")
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "search" and len(sys.argv) > 2:
        print(json.dumps(search(sys.argv[2]), indent=2, ensure_ascii=False))
    else:
        print(f"Commande: {cmd} - args manquants ou commande inconnue")
