"""
Processeur batch — Operations sur plusieurs fichiers en une commande.
Usage:
  python scripts/batch_process.py convert *.csv --to xlsx
  python scripts/batch_process.py read *.pdf --summary
  python scripts/batch_process.py info *.xlsx
  python scripts/batch_process.py rename "*.tmp" --pattern "backup_{n}.txt"
"""
import sys
import os
import glob
import argparse
import json
import traceback

SCRIPTS = os.path.dirname(os.path.abspath(__file__))

def safe_import(script_name):
    """Import dynamique d'un script du dossier scripts/."""
    import importlib.util
    path = os.path.join(SCRIPTS, script_name)
    spec = importlib.util.spec_from_file_location(script_name.replace(".py",""), path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def batch_convert(files, to_format):
    converter = safe_import("file_convert.py")
    results = {"ok": [], "errors": []}
    for f in files:
        try:
            src_ext = os.path.splitext(f)[1].lstrip(".").lower()
            key = (src_ext, to_format.lower())
            if key in converter.CONVERTERS:
                output = os.path.splitext(f)[0] + "." + to_format
                converter.CONVERTERS[key](f, output)
                results["ok"].append(f)
            else:
                results["errors"].append({"file": f, "error": f"Conversion {src_ext}->{to_format} non supportee"})
        except Exception as e:
            results["errors"].append({"file": f, "error": str(e)})
    return results

def batch_read(files, summary=False):
    reader = safe_import("doc_reader.py")
    results = {}
    for f in files:
        try:
            ext = os.path.splitext(f)[1].lower()
            if ext in reader.READERS:
                handler = reader.READERS[ext]["read"]
                if ext == ".pdf":
                    text = handler(f, pages="1-3" if summary else None)
                else:
                    text = handler(f, max_rows=20 if summary else 100)
                results[f] = text[:500] + "..." if summary and len(str(text)) > 500 else text
            else:
                results[f] = f"[Format non supporte: {ext}]"
        except Exception as e:
            results[f] = f"[Erreur: {e}]"
    return results

def batch_info(files):
    reader = safe_import("doc_reader.py")
    results = {}
    for f in files:
        try:
            ext = os.path.splitext(f)[1].lower()
            if ext in reader.READERS:
                results[f] = reader.READERS[ext]["info"](f)
            else:
                results[f] = {"error": f"Format non supporte: {ext}"}
        except Exception as e:
            results[f] = {"error": str(e)}
    return results

def batch_rename(files, pattern):
    results = {"renamed": [], "errors": []}
    for i, f in enumerate(files):
        try:
            dirname = os.path.dirname(f)
            ext = os.path.splitext(f)[1]
            new_name = pattern.replace("{n}", str(i+1)).replace("{ext}", ext).replace("{name}", os.path.splitext(os.path.basename(f))[0])
            new_path = os.path.join(dirname, new_name) if dirname else new_name
            os.rename(f, new_path)
            results["renamed"].append({"from": f, "to": new_path})
        except Exception as e:
            results["errors"].append({"file": f, "error": str(e)})
    return results

def expand_files(patterns):
    """Expanse les globs en liste de fichiers."""
    files = []
    for p in patterns:
        matched = glob.glob(p)
        if matched:
            files.extend(matched)
        elif os.path.exists(p):
            files.append(p)
    return sorted(set(files))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Processeur batch")
    parser.add_argument("action", choices=["convert", "read", "info", "rename"])
    parser.add_argument("files", nargs="+", help="Fichiers ou patterns glob")
    parser.add_argument("--to", default=None, help="Format cible (pour convert)")
    parser.add_argument("--pattern", default=None, help="Pattern de renommage")
    parser.add_argument("--summary", action="store_true", help="Mode resume (pour read)")
    args = parser.parse_args()

    files = expand_files(args.files)
    if not files:
        print(f"Aucun fichier trouve pour: {args.files}")
        sys.exit(1)

    print(f"[BATCH] {len(files)} fichier(s) trouves")

    if args.action == "convert":
        if not args.to:
            print("--to requis pour convert")
            sys.exit(1)
        result = batch_convert(files, args.to)
    elif args.action == "read":
        result = batch_read(files, args.summary)
    elif args.action == "info":
        result = batch_info(files)
    elif args.action == "rename":
        if not args.pattern:
            print("--pattern requis pour rename")
            sys.exit(1)
        result = batch_rename(files, args.pattern)

    output = json.dumps(result, indent=2, ensure_ascii=False, default=str)
    sys.stdout.buffer.write(output.encode("utf-8", errors="replace"))
    sys.stdout.buffer.write(b"\n")
