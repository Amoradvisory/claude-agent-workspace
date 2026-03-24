"""
Utilitaire de récupération web rapide.
Usage: python scripts/web_fetch.py <url> [--output fichier.html]
"""
import sys
import argparse

def fetch(url: str, output: str | None = None):
    try:
        import httpx
    except ImportError:
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "httpx", "-q"])
        import httpx

    resp = httpx.get(url, follow_redirects=True, timeout=30)
    resp.raise_for_status()

    if output:
        with open(output, "w", encoding="utf-8") as f:
            f.write(resp.text)
        print(f"✅ Sauvegardé dans {output} ({len(resp.text)} caractères)")
    else:
        print(resp.text[:5000])
    return resp.text

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    parser.add_argument("--output", "-o", default=None)
    args = parser.parse_args()
    fetch(args.url, args.output)
