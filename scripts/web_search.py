"""
Recherche web locale — Replique search-server.mjs (DuckDuckGo).
Usage:
  python scripts/web_search.py "query"              # Recherche web
  python scripts/web_search.py --instant "query"    # Reponse instantanee
"""
import sys
import argparse
import json
import re

def ensure(pkg, imp=None):
    try:
        return __import__(imp or pkg.replace("-","_"))
    except ImportError:
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg, "-q"])
        return __import__(imp or pkg.replace("-","_"))

def strip_html(text):
    """Nettoie les tags HTML et decode les entites."""
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    text = text.replace("&quot;", '"').replace("&#x27;", "'").replace("&nbsp;", " ")
    return text.strip()

def web_search(query, max_results=8):
    """Recherche DuckDuckGo via HTML parsing."""
    httpx = ensure("httpx")
    bs4 = ensure("beautifulsoup4", "bs4")
    from bs4 import BeautifulSoup

    url = "https://html.duckduckgo.com/html/"
    resp = httpx.post(url, data={"q": query}, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }, timeout=15, follow_redirects=True)

    soup = BeautifulSoup(resp.text, "html.parser")
    results = []
    for r in soup.select(".result")[:max_results]:
        title_el = r.select_one(".result__a")
        snippet_el = r.select_one(".result__snippet")
        if not title_el:
            continue
        href = title_el.get("href", "")
        # DuckDuckGo encodes URLs, try to extract
        if "uddg=" in href:
            from urllib.parse import unquote, parse_qs, urlparse
            parsed = urlparse(href)
            params = parse_qs(parsed.query)
            href = unquote(params.get("uddg", [href])[0])

        results.append({
            "title": strip_html(title_el.get_text()),
            "url": href,
            "snippet": strip_html(snippet_el.get_text()) if snippet_el else "",
        })
    return results

def instant_answer(query):
    """DuckDuckGo Instant Answer API."""
    httpx = ensure("httpx")
    resp = httpx.get("https://api.duckduckgo.com/", params={
        "q": query, "format": "json", "no_html": "1", "skip_disambig": "1"
    }, timeout=10)
    data = resp.json()
    result = {
        "heading": data.get("Heading", ""),
        "abstract": data.get("AbstractText", ""),
        "source": data.get("AbstractSource", ""),
        "url": data.get("AbstractURL", ""),
        "answer": data.get("Answer", ""),
        "definition": data.get("Definition", ""),
    }
    # Related topics
    topics = data.get("RelatedTopics", [])[:5]
    result["related"] = [
        {"text": strip_html(t.get("Text", "")), "url": t.get("FirstURL", "")}
        for t in topics if isinstance(t, dict) and t.get("Text")
    ]
    return result

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("query", nargs="?")
    parser.add_argument("--instant", action="store_true", help="Utiliser l'API instant answer")
    parser.add_argument("--max", type=int, default=8, help="Nombre max de resultats")
    args = parser.parse_args()

    if not args.query:
        print("Usage: web_search.py 'query' [--instant] [--max N]")
        sys.exit(1)

    if args.instant:
        result = instant_answer(args.query)
    else:
        result = web_search(args.query, args.max)

    output = json.dumps(result, indent=2, ensure_ascii=False)
    sys.stdout.buffer.write(output.encode("utf-8", errors="replace"))
    sys.stdout.buffer.write(b"\n")
