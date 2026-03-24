"""
Transformations de texte — Resume, extraction, nettoyage, recherche-remplacement.
Usage:
  python scripts/text_transform.py extract-emails fichier.txt
  python scripts/text_transform.py extract-urls fichier.txt
  python scripts/text_transform.py extract-phones fichier.txt
  python scripts/text_transform.py extract-dates fichier.txt
  python scripts/text_transform.py summarize fichier.txt [--sentences 5]
  python scripts/text_transform.py replace fichier.txt "ancien" "nouveau" [-o output.txt]
  python scripts/text_transform.py regex-replace fichier.txt "pattern" "replacement" [-o output.txt]
  python scripts/text_transform.py case fichier.txt upper|lower|title|capitalize
  python scripts/text_transform.py slug "Mon Titre de Page"
  python scripts/text_transform.py count fichier.txt [--word "mot"]
  python scripts/text_transform.py lines fichier.txt [--unique] [--sort] [--reverse]
  python scripts/text_transform.py template template.txt data.json -o output.txt
"""
import sys
import os
import re
import json
import argparse
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import safe, log_info, OUTPUT_DIR


def _read(path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()

def _write(text, path):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"[OK] Ecrit -> {path}")


@safe
def extract_emails(path):
    """Extrait toutes les adresses email."""
    text = _read(path)
    emails = list(set(re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)))
    emails.sort()
    print(f"[OK] {len(emails)} email(s) trouve(s):")
    for e in emails:
        print(f"  {e}")
    return emails

@safe
def extract_urls(path):
    """Extrait toutes les URLs."""
    text = _read(path)
    urls = list(set(re.findall(r"https?://[^\s<>\"']+", text)))
    urls.sort()
    print(f"[OK] {len(urls)} URL(s) trouvee(s):")
    for u in urls:
        print(f"  {u}")
    return urls

@safe
def extract_phones(path):
    """Extrait les numeros de telephone (formats FR et internationaux)."""
    text = _read(path)
    patterns = [
        r"(?:\+33|0033|0)\s*[1-9](?:[\s.-]*\d{2}){4}",  # FR
        r"\+\d{1,3}[\s.-]?\d{1,4}[\s.-]?\d{1,4}[\s.-]?\d{1,9}",  # International
        r"\b\d{2}[\s.-]\d{2}[\s.-]\d{2}[\s.-]\d{2}[\s.-]\d{2}\b",  # FR compact
    ]
    phones = set()
    for pat in patterns:
        phones.update(re.findall(pat, text))
    phones = sorted(phones)
    print(f"[OK] {len(phones)} numero(s) trouve(s):")
    for p in phones:
        print(f"  {p.strip()}")
    return phones

@safe
def extract_dates(path):
    """Extrait les dates (formats courants)."""
    text = _read(path)
    patterns = [
        r"\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}",  # 01/02/2026, 1-2-26
        r"\d{4}[/-]\d{1,2}[/-]\d{1,2}",  # 2026-01-02
        r"\d{1,2}\s+(?:janvier|fevrier|mars|avril|mai|juin|juillet|aout|septembre|octobre|novembre|decembre)\s+\d{4}",  # FR
        r"\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+\d{4}",  # EN
    ]
    dates = set()
    for pat in patterns:
        dates.update(re.findall(pat, text, re.IGNORECASE))
    dates = sorted(dates)
    print(f"[OK] {len(dates)} date(s) trouvee(s):")
    for d in dates:
        print(f"  {d}")
    return dates

@safe
def summarize_text(path, n_sentences=5):
    """Resume extractif par frequence de mots."""
    text = _read(path)
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    if len(sentences) <= n_sentences:
        print(text)
        return text

    # Score chaque phrase par frequence des mots
    words = re.findall(r'\b\w{4,}\b', text.lower())
    freq = Counter(words)
    # Normaliser
    max_freq = max(freq.values()) if freq else 1

    scored = []
    for i, sent in enumerate(sentences):
        sent_words = re.findall(r'\b\w{4,}\b', sent.lower())
        score = sum(freq.get(w, 0) / max_freq for w in sent_words)
        # Bonus pour les premieres phrases
        if i < 3:
            score *= 1.3
        scored.append((score, i, sent))

    # Prendre les N meilleures, dans l'ordre original
    best = sorted(scored, key=lambda x: -x[0])[:n_sentences]
    best = sorted(best, key=lambda x: x[1])

    summary = " ".join(s[2] for s in best)
    print(f"=== Resume ({n_sentences} phrases / {len(sentences)} originales) ===\n")
    print(summary)
    return summary

@safe
def replace_text(path, old, new, output=None, use_regex=False):
    """Recherche et remplacement (texte ou regex)."""
    text = _read(path)
    if use_regex:
        new_text, count = re.subn(old, new, text)
    else:
        count = text.count(old)
        new_text = text.replace(old, new)

    out = output or path
    _write(new_text, out)
    print(f"[OK] {count} remplacement(s): '{old}' -> '{new}'")
    return count

@safe
def change_case(path, mode, output=None):
    """Change la casse du texte."""
    text = _read(path)
    modes = {
        "upper": text.upper(),
        "lower": text.lower(),
        "title": text.title(),
        "capitalize": text.capitalize(),
        "swapcase": text.swapcase(),
    }
    if mode not in modes:
        print(f"[ERREUR] Mode inconnu: {mode}. Disponibles: {', '.join(modes)}")
        return
    result = modes[mode]
    if output:
        _write(result, output)
    else:
        print(result[:2000])
    return result

@safe
def slugify(text):
    """Convertit un texte en slug URL-friendly."""
    import unicodedata
    # Normaliser les accents
    text = unicodedata.normalize("NFKD", text).encode("ASCII", "ignore").decode("ASCII")
    text = re.sub(r"[^\w\s-]", "", text.lower())
    text = re.sub(r"[\s_]+", "-", text.strip())
    text = re.sub(r"-+", "-", text).strip("-")
    print(text)
    return text

@safe
def count_text(path, word=None):
    """Comptage mots, lignes, caracteres, ou occurrences d'un mot."""
    text = _read(path)
    if word:
        count = len(re.findall(re.escape(word), text, re.IGNORECASE))
        print(f"'{word}' : {count} occurrence(s)")
        return count
    else:
        lines = text.split("\n")
        words = text.split()
        chars = len(text)
        print(f"  Lignes    : {len(lines):,}")
        print(f"  Mots      : {len(words):,}")
        print(f"  Caracteres: {chars:,}")
        # Top 10 mots
        word_freq = Counter(w.lower().strip(".,;:!?()[]\"'") for w in words if len(w) > 3)
        if word_freq:
            print(f"\n  Top 10 mots:")
            for w, c in word_freq.most_common(10):
                print(f"    {w:20s} {c}")
        return {"lignes": len(lines), "mots": len(words), "caracteres": chars}

@safe
def process_lines(path, unique=False, sort=False, reverse=False, output=None):
    """Operations sur les lignes (unique, tri, reverse)."""
    text = _read(path)
    lines = text.strip().split("\n")
    original = len(lines)

    if unique:
        seen = set()
        new_lines = []
        for l in lines:
            if l not in seen:
                seen.add(l)
                new_lines.append(l)
        lines = new_lines

    if sort:
        lines.sort()

    if reverse:
        lines.reverse()

    result = "\n".join(lines) + "\n"
    if output:
        _write(result, output)
    else:
        for l in lines[:50]:
            print(l)
        if len(lines) > 50:
            print(f"  ... et {len(lines) - 50} autres lignes")

    if unique:
        removed = original - len(lines)
        print(f"[OK] {removed} doublon(s) supprime(s) ({original} -> {len(lines)} lignes)")

    return result

@safe
def template_render(template_path, data_path, output=None):
    """Applique un template Jinja2 avec des donnees JSON."""
    try:
        from jinja2 import Template
    except ImportError:
        from _common import ensure
        ensure("jinja2")
        from jinja2 import Template

    tmpl_text = _read(template_path)
    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    template = Template(tmpl_text)
    result = template.render(**data)

    if output:
        _write(result, output)
    else:
        print(result[:3000])
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Transformations de texte")
    parser.add_argument("action", choices=[
        "extract-emails", "extract-urls", "extract-phones", "extract-dates",
        "summarize", "replace", "regex-replace", "case", "slug",
        "count", "lines", "template"
    ])
    parser.add_argument("file", help="Fichier texte ou texte direct")
    parser.add_argument("params", nargs="*")
    parser.add_argument("--output", "-o", default=None)
    parser.add_argument("--sentences", "-n", type=int, default=5)
    parser.add_argument("--word", "-w", default=None)
    parser.add_argument("--unique", action="store_true")
    parser.add_argument("--sort", action="store_true")
    parser.add_argument("--reverse", action="store_true")
    args = parser.parse_args()

    if args.action == "extract-emails":
        extract_emails(args.file)
    elif args.action == "extract-urls":
        extract_urls(args.file)
    elif args.action == "extract-phones":
        extract_phones(args.file)
    elif args.action == "extract-dates":
        extract_dates(args.file)
    elif args.action == "summarize":
        summarize_text(args.file, args.sentences)
    elif args.action == "replace":
        if len(args.params) < 2:
            print("[ERREUR] Requis: ancien nouveau")
            sys.exit(1)
        replace_text(args.file, args.params[0], args.params[1], args.output)
    elif args.action == "regex-replace":
        if len(args.params) < 2:
            print("[ERREUR] Requis: pattern replacement")
            sys.exit(1)
        replace_text(args.file, args.params[0], args.params[1], args.output, use_regex=True)
    elif args.action == "case":
        if not args.params:
            print("[ERREUR] Mode requis: upper|lower|title|capitalize")
            sys.exit(1)
        change_case(args.file, args.params[0], args.output)
    elif args.action == "slug":
        slugify(args.file)
    elif args.action == "count":
        count_text(args.file, args.word)
    elif args.action == "lines":
        process_lines(args.file, args.unique, args.sort, args.reverse, args.output)
    elif args.action == "template":
        if not args.params:
            print("[ERREUR] Fichier JSON de donnees requis")
            sys.exit(1)
        template_render(args.file, args.params[0], args.output)
