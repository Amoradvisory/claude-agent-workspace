"""
Controle qualite de contenu — Relecture, stats, validation.
Usage:
  python scripts/quality_check.py analyze fichier.txt     # Analyse complete
  python scripts/quality_check.py stats fichier.txt        # Statistiques
  python scripts/quality_check.py duplicates fichier.txt   # Lignes doublons
  python scripts/quality_check.py normalize fichier.txt    # Nettoyage espaces/format
"""
import sys
import os
import re
import json
import argparse
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import safe, log_info

@safe
def read_text(path):
    """Lit un fichier texte (txt, md, csv, json, py, etc.)."""
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()

@safe
def stats(text, path=""):
    """Statistiques detaillees d'un texte."""
    lines = text.split("\n")
    words = text.split()
    chars = len(text)
    chars_no_space = len(text.replace(" ", "").replace("\n", ""))
    sentences = len(re.findall(r"[.!?]+", text))
    paragraphs = len(re.split(r"\n\s*\n", text))
    unique_words = len(set(w.lower().strip(".,;:!?()[]\"'") for w in words))

    # Mots les plus frequents (hors mots courts)
    word_counts = Counter(w.lower().strip(".,;:!?()[]\"'") for w in words if len(w) > 3)
    top_words = word_counts.most_common(10)

    # Lisibilite (approximation Flesch pour le francais)
    avg_words_per_sentence = len(words) / max(sentences, 1)
    avg_syllables = sum(max(1, len(re.findall(r"[aeiouyAEIOUY]", w))) for w in words) / max(len(words), 1)
    flesch = 207 - 1.015 * avg_words_per_sentence - 73.6 * avg_syllables

    result = {
        "fichier": os.path.basename(path),
        "lignes": len(lines),
        "mots": len(words),
        "mots_uniques": unique_words,
        "caracteres": chars,
        "caracteres_sans_espaces": chars_no_space,
        "phrases": sentences,
        "paragraphes": paragraphs,
        "moy_mots_par_phrase": round(avg_words_per_sentence, 1),
        "lisibilite_flesch": round(max(0, min(100, flesch)), 1),
        "top_10_mots": [{"mot": w, "freq": c} for w, c in top_words],
    }

    # Niveau de lisibilite
    if flesch >= 70:
        result["niveau"] = "Facile"
    elif flesch >= 50:
        result["niveau"] = "Moyen"
    elif flesch >= 30:
        result["niveau"] = "Difficile"
    else:
        result["niveau"] = "Tres difficile"

    return result

@safe
def analyze(text, path=""):
    """Analyse qualite complete."""
    s = stats(text, path)
    issues = []

    lines = text.split("\n")

    # Lignes trop longues
    long_lines = [(i+1, len(l)) for i, l in enumerate(lines) if len(l) > 120]
    if long_lines:
        issues.append(f"{len(long_lines)} ligne(s) > 120 caracteres")

    # Espaces doubles
    double_spaces = len(re.findall(r"  +", text))
    if double_spaces:
        issues.append(f"{double_spaces} double(s) espace(s)")

    # Lignes vides consecutives
    triple_blank = len(re.findall(r"\n\n\n+", text))
    if triple_blank:
        issues.append(f"{triple_blank} bloc(s) de lignes vides excessifs")

    # Espaces en fin de ligne
    trailing = sum(1 for l in lines if l != l.rstrip())
    if trailing:
        issues.append(f"{trailing} ligne(s) avec espaces en fin")

    # Tabs melanges avec espaces
    has_tabs = "\t" in text
    has_spaces_indent = any(l.startswith("    ") for l in lines)
    if has_tabs and has_spaces_indent:
        issues.append("Melange tabs et espaces pour l'indentation")

    # Mots repetes consecutifs
    repeated = re.findall(r"\b(\w+)\s+\1\b", text, re.IGNORECASE)
    if repeated:
        issues.append(f"{len(repeated)} mot(s) repete(s) consecutivement: {', '.join(list(set(repeated))[:5])}")

    s["problemes"] = issues
    s["score_qualite"] = max(0, 100 - len(issues) * 10)
    return s

@safe
def find_duplicates(text):
    """Trouve les lignes en doublon."""
    lines = text.strip().split("\n")
    counts = Counter(l.strip() for l in lines if l.strip())
    dupes = {line: count for line, count in counts.items() if count > 1}
    return dupes

@safe
def normalize(text, output_path=None):
    """Normalise le texte : espaces, lignes vides, trailing."""
    # Supprimer espaces en fin de ligne
    text = re.sub(r"[ \t]+$", "", text, flags=re.MULTILINE)
    # Supprimer doubles espaces
    text = re.sub(r"  +", " ", text)
    # Max 2 lignes vides consecutives
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Supprimer espace en debut/fin
    text = text.strip() + "\n"

    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"[OK] Normalise -> {output_path}")
    return text

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Controle qualite de contenu")
    parser.add_argument("action", choices=["analyze", "stats", "duplicates", "normalize"])
    parser.add_argument("file")
    parser.add_argument("--output", "-o", default=None)
    args = parser.parse_args()

    text = read_text(args.file)
    if text is None:
        print(f"[ERREUR] Impossible de lire: {args.file}")
        sys.exit(1)

    if args.action == "stats":
        result = stats(text, args.file)
        for k, v in result.items():
            if k == "top_10_mots":
                print(f"  {'top_mots':25s}: {', '.join(str(w['mot']) + '(' + str(w['freq']) + ')' for w in v)}")
            else:
                print(f"  {k:25s}: {v}")
    elif args.action == "analyze":
        result = analyze(text, args.file)
        print(f"\n=== Analyse qualite: {os.path.basename(args.file)} ===\n")
        print(f"  Mots: {result['mots']} | Phrases: {result['phrases']} | Paragraphes: {result['paragraphes']}")
        print(f"  Lisibilite: {result['lisibilite_flesch']}/100 ({result['niveau']})")
        print(f"  Score qualite: {result['score_qualite']}/100")
        if result["problemes"]:
            print(f"\n  Problemes ({len(result['problemes'])}):")
            for p in result["problemes"]:
                print(f"    - {p}")
        else:
            print(f"\n  [OK] Aucun probleme detecte")
    elif args.action == "duplicates":
        dupes = find_duplicates(text)
        if dupes:
            print(f"{len(dupes)} ligne(s) en doublon:")
            for line, count in sorted(dupes.items(), key=lambda x: -x[1])[:20]:
                preview = line[:60] + "..." if len(line) > 60 else line
                print(f"  x{count}: {preview}")
        else:
            print("[OK] Aucun doublon.")
    elif args.action == "normalize":
        normalize(text, args.output or args.file)
