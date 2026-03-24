"""
Client API REST universel — Pour appeler n'importe quelle API en une commande.
Usage:
  python scripts/api_client.py GET https://api.example.com/data
  python scripts/api_client.py POST https://api.example.com/items --json '{"name":"test"}'
  python scripts/api_client.py GET https://api.example.com/data --header "Authorization: Bearer xxx"
  python scripts/api_client.py GET https://api.example.com/data -o output/result.json
"""
import sys
import os
import json
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import ensure, safe, print_json, log_info, output_path

@safe
def api_call(method, url, headers=None, body=None, output=None, timeout=30):
    httpx = ensure("httpx")

    parsed_headers = {}
    if headers:
        for h in headers:
            if ":" in h:
                k, v = h.split(":", 1)
                parsed_headers[k.strip()] = v.strip()

    kwargs = {
        "method": method.upper(),
        "url": url,
        "headers": parsed_headers,
        "timeout": timeout,
        "follow_redirects": True,
    }

    if body:
        try:
            parsed = json.loads(body)
            kwargs["json"] = parsed
        except json.JSONDecodeError:
            kwargs["content"] = body

    resp = httpx.request(**kwargs)

    result = {
        "status": resp.status_code,
        "headers": dict(resp.headers),
        "url": str(resp.url),
    }

    # Parse response body
    content_type = resp.headers.get("content-type", "")
    if "json" in content_type:
        try:
            result["body"] = resp.json()
        except Exception:
            result["body"] = resp.text
    else:
        result["body"] = resp.text[:5000]
        if len(resp.text) > 5000:
            result["truncated"] = True
            result["total_length"] = len(resp.text)

    log_info(f"API {method.upper()} {url}", {"status": resp.status_code})

    if output:
        with open(output, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"[OK] Sauvegarde: {output}")
    else:
        # Afficher seulement le body pour un usage pipeline
        if isinstance(result["body"], (dict, list)):
            print_json(result["body"])
        else:
            print(result["body"][:3000])

    return result

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Client API REST universel")
    parser.add_argument("method", choices=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "get", "post", "put", "patch", "delete", "head"])
    parser.add_argument("url")
    parser.add_argument("--header", "-H", action="append", default=[], help="Header (ex: 'Authorization: Bearer xxx')")
    parser.add_argument("--json", "--body", "-d", dest="body", default=None, help="Corps JSON")
    parser.add_argument("--output", "-o", default=None, help="Fichier de sortie")
    parser.add_argument("--timeout", "-t", type=int, default=30)
    args = parser.parse_args()

    api_call(args.method, args.url, args.header, args.body, args.output, args.timeout)
