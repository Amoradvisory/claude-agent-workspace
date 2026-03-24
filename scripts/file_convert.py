"""
Convertisseur de fichiers etendu — 15 conversions supportees.
Usage: python scripts/file_convert.py <input> <format_sortie>
Formats: csv, xlsx, json, html, pdf, md, tsv, xml, yaml
"""
import sys
import os
import json
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import ensure, safe, log_info

# === Conversions tabulaires ===
@safe
def csv_to_xlsx(inp, out):
    pd = ensure("pandas"); ensure("openpyxl")
    pd.read_csv(inp).to_excel(out, index=False)
    print(f"[OK] {inp} -> {out}")

@safe
def xlsx_to_csv(inp, out):
    pd = ensure("pandas"); ensure("openpyxl")
    pd.read_excel(inp).to_csv(out, index=False)
    print(f"[OK] {inp} -> {out}")

@safe
def json_to_csv(inp, out):
    pd = ensure("pandas")
    with open(inp, "r", encoding="utf-8") as f:
        data = json.load(f)
    df = pd.json_normalize(data) if isinstance(data, list) else pd.json_normalize([data])
    df.to_csv(out, index=False)
    print(f"[OK] {inp} -> {out}")

@safe
def csv_to_json(inp, out):
    pd = ensure("pandas")
    df = pd.read_csv(inp)
    df.to_json(out, orient="records", force_ascii=False, indent=2)
    print(f"[OK] {inp} -> {out}")

@safe
def xlsx_to_json(inp, out):
    pd = ensure("pandas"); ensure("openpyxl")
    df = pd.read_excel(inp)
    df.to_json(out, orient="records", force_ascii=False, indent=2)
    print(f"[OK] {inp} -> {out}")

@safe
def json_to_xlsx(inp, out):
    pd = ensure("pandas"); ensure("openpyxl")
    with open(inp, "r", encoding="utf-8") as f:
        data = json.load(f)
    df = pd.json_normalize(data) if isinstance(data, list) else pd.json_normalize([data])
    df.to_excel(out, index=False)
    print(f"[OK] {inp} -> {out}")

@safe
def csv_to_tsv(inp, out):
    pd = ensure("pandas")
    pd.read_csv(inp).to_csv(out, sep="\t", index=False)
    print(f"[OK] {inp} -> {out}")

@safe
def tsv_to_csv(inp, out):
    pd = ensure("pandas")
    pd.read_csv(inp, sep="\t").to_csv(out, index=False)
    print(f"[OK] {inp} -> {out}")

# === Conversions documents ===
@safe
def md_to_html(inp, out):
    with open(inp, "r", encoding="utf-8") as f:
        md_text = f.read()
    # Simple markdown to HTML
    lines = md_text.split("\n")
    html_lines = []
    for line in lines:
        if line.startswith("### "):
            html_lines.append(f"<h3>{line[4:]}</h3>")
        elif line.startswith("## "):
            html_lines.append(f"<h2>{line[3:]}</h2>")
        elif line.startswith("# "):
            html_lines.append(f"<h1>{line[2:]}</h1>")
        elif line.startswith("- "):
            html_lines.append(f"<li>{line[2:]}</li>")
        elif line.startswith("**") and line.endswith("**"):
            html_lines.append(f"<p><strong>{line[2:-2]}</strong></p>")
        elif line.strip() == "":
            html_lines.append("<br>")
        else:
            html_lines.append(f"<p>{line}</p>")

    body = "\n".join(html_lines)
    title = os.path.splitext(os.path.basename(inp))[0]
    html = f"""<!DOCTYPE html>
<html lang="fr"><head><meta charset="UTF-8"><title>{title}</title>
<style>body{{font-family:'Segoe UI',sans-serif;max-width:800px;margin:2rem auto;padding:0 1rem;color:#333;line-height:1.6}}
h1{{color:#1a1a2e}}h2{{color:#16213e}}h3{{color:#0f3460}}table{{border-collapse:collapse;width:100%}}
th,td{{border:1px solid #ddd;padding:8px}}li{{margin:4px 0}}</style></head>
<body>{body}</body></html>"""
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[OK] {inp} -> {out}")

@safe
def csv_to_html(inp, out):
    pd = ensure("pandas")
    df = pd.read_csv(inp)
    title = os.path.splitext(os.path.basename(inp))[0]
    html = f"""<!DOCTYPE html>
<html lang="fr"><head><meta charset="UTF-8"><title>{title}</title>
<style>body{{font-family:'Segoe UI',sans-serif;padding:2rem}}
table{{border-collapse:collapse;width:100%}}th{{background:#1a1a2e;color:#fff;padding:10px}}
td{{padding:8px;border-bottom:1px solid #eee}}tr:hover{{background:#f5f5f5}}</style></head>
<body><h1>{title}</h1>{df.to_html(index=False, classes='data')}</body></html>"""
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[OK] {inp} -> {out}")

@safe
def xlsx_to_html(inp, out):
    pd = ensure("pandas"); ensure("openpyxl")
    df = pd.read_excel(inp)
    title = os.path.splitext(os.path.basename(inp))[0]
    html = f"""<!DOCTYPE html>
<html lang="fr"><head><meta charset="UTF-8"><title>{title}</title>
<style>body{{font-family:'Segoe UI',sans-serif;padding:2rem}}
table{{border-collapse:collapse;width:100%}}th{{background:#1a1a2e;color:#fff;padding:10px}}
td{{padding:8px;border-bottom:1px solid #eee}}tr:hover{{background:#f5f5f5}}</style></head>
<body><h1>{title}</h1>{df.to_html(index=False)}</body></html>"""
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[OK] {inp} -> {out}")

@safe
def json_to_yaml(inp, out):
    yaml = ensure("pyyaml", "yaml")
    with open(inp, "r", encoding="utf-8") as f:
        data = json.load(f)
    import yaml as yaml_mod
    with open(out, "w", encoding="utf-8") as f:
        yaml_mod.dump(data, f, allow_unicode=True, default_flow_style=False)
    print(f"[OK] {inp} -> {out}")

@safe
def yaml_to_json(inp, out):
    yaml = ensure("pyyaml", "yaml")
    import yaml as yaml_mod
    with open(inp, "r", encoding="utf-8") as f:
        data = yaml_mod.safe_load(f)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"[OK] {inp} -> {out}")

# === Registre de conversions ===
CONVERTERS = {
    # Tabulaire
    ("csv", "xlsx"): csv_to_xlsx,
    ("xlsx", "csv"): xlsx_to_csv,
    ("json", "csv"): json_to_csv,
    ("csv", "json"): csv_to_json,
    ("xlsx", "json"): xlsx_to_json,
    ("json", "xlsx"): json_to_xlsx,
    ("csv", "tsv"): csv_to_tsv,
    ("tsv", "csv"): tsv_to_csv,
    # Documents
    ("md", "html"): md_to_html,
    ("csv", "html"): csv_to_html,
    ("xlsx", "html"): xlsx_to_html,
    # Data
    ("json", "yaml"): json_to_yaml,
    ("json", "yml"): json_to_yaml,
    ("yaml", "json"): yaml_to_json,
    ("yml", "json"): yaml_to_json,
}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=f"Convertisseur ({len(CONVERTERS)} conversions)")
    parser.add_argument("input", help="Fichier source")
    parser.add_argument("format", help="Format cible")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"[ERREUR] Fichier non trouve: {args.input}")
        sys.exit(1)

    src_ext = os.path.splitext(args.input)[1].lstrip(".").lower()
    dst_ext = args.format.lstrip(".").lower()
    output = os.path.splitext(args.input)[0] + "." + dst_ext

    key = (src_ext, dst_ext)
    if key in CONVERTERS:
        CONVERTERS[key](args.input, output)
        log_info(f"Conversion: {args.input} -> {output}")
    else:
        print(f"[ERREUR] Conversion {src_ext} -> {dst_ext} non supportee")
        print(f"Supportees ({len(CONVERTERS)}):")
        for k in sorted(CONVERTERS.keys()):
            print(f"  {k[0]:5s} -> {k[1]}")
