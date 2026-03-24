"""
Analyse de donnees — Profile, compare, pivot, filter, summary, chart.
Usage:
  python scripts/data_analyzer.py profile data.csv
  python scripts/data_analyzer.py summary data.csv
  python scripts/data_analyzer.py compare file1.csv file2.csv
  python scripts/data_analyzer.py filter data.csv "colonne > 100"
  python scripts/data_analyzer.py sort data.csv colonne [--desc]
  python scripts/data_analyzer.py group data.csv colonne [--agg sum|mean|count]
  python scripts/data_analyzer.py pivot data.csv index columns values
  python scripts/data_analyzer.py chart data.csv colonne_x colonne_y [--type bar|line|pie] -o chart.html
  python scripts/data_analyzer.py head data.csv [--rows 20]
  python scripts/data_analyzer.py columns data.csv
"""
import sys
import os
import json
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import ensure, safe, log_info, OUTPUT_DIR

ensure("pandas")
ensure("openpyxl")
import pandas as pd


def _load(path):
    """Charge CSV ou Excel automatiquement."""
    ext = os.path.splitext(path)[1].lower()
    if ext in (".xlsx", ".xls"):
        return pd.read_excel(path)
    elif ext == ".json":
        return pd.read_json(path)
    elif ext == ".tsv":
        return pd.read_csv(path, sep="\t")
    else:
        # CSV with auto-detect separator
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            sample = f.read(2000)
        sep = ";" if sample.count(";") > sample.count(",") else ","
        return pd.read_csv(path, sep=sep, encoding="utf-8")


@safe
def profile_data(path):
    """Profil complet d'un dataset."""
    df = _load(path)
    n_rows, n_cols = df.shape
    print(f"\n=== Profil: {os.path.basename(path)} ===\n")
    print(f"  Lignes: {n_rows:,} | Colonnes: {n_cols}")
    print(f"  Taille memoire: {df.memory_usage(deep=True).sum() / 1024:.1f} KB")
    print()

    for col in df.columns:
        dtype = str(df[col].dtype)
        nulls = df[col].isnull().sum()
        unique = df[col].nunique()
        null_pct = (nulls / n_rows * 100) if n_rows > 0 else 0

        line = f"  {col:25s}  type={dtype:10s}  uniques={unique:6d}  nulls={nulls}({null_pct:.0f}%)"

        if pd.api.types.is_numeric_dtype(df[col]):
            stats = df[col].describe()
            line += f"  min={stats['min']:.2f}  max={stats['max']:.2f}  mean={stats['mean']:.2f}"
        elif pd.api.types.is_string_dtype(df[col]):
            top = df[col].value_counts().head(3)
            top_str = ", ".join(f"{v}({c})" for v, c in top.items())
            line += f"  top=[{top_str}]"

        print(line)

    # Doublons
    dupes = df.duplicated().sum()
    if dupes > 0:
        print(f"\n  [!] {dupes} ligne(s) en doublon ({dupes/n_rows*100:.1f}%)")
    else:
        print(f"\n  [OK] Aucun doublon")

    return {"lignes": n_rows, "colonnes": n_cols, "doublons": dupes}

@safe
def summary_data(path):
    """Resume statistique rapide."""
    df = _load(path)
    print(f"\n=== Resume: {os.path.basename(path)} ({df.shape[0]} x {df.shape[1]}) ===\n")

    numeric = df.select_dtypes(include="number")
    if not numeric.empty:
        desc = numeric.describe().round(2)
        print(desc.to_string())
    else:
        print("  Aucune colonne numerique.")

    cat = df.select_dtypes(include=["object", "category"])
    if not cat.empty:
        print(f"\n  Colonnes texte ({len(cat.columns)}):")
        for col in cat.columns:
            top = df[col].value_counts().head(3)
            print(f"    {col}: {', '.join(f'{v}({c})' for v, c in top.items())}")

@safe
def compare_data(path1, path2):
    """Compare deux fichiers de donnees."""
    df1 = _load(path1)
    df2 = _load(path2)
    name1 = os.path.basename(path1)
    name2 = os.path.basename(path2)

    print(f"\n=== Comparaison ===\n")
    print(f"  {'':20s}  {name1:>15s}  {name2:>15s}")
    print(f"  {'Lignes':20s}  {df1.shape[0]:15d}  {df2.shape[0]:15d}")
    print(f"  {'Colonnes':20s}  {df1.shape[1]:15d}  {df2.shape[1]:15d}")

    cols1 = set(df1.columns)
    cols2 = set(df2.columns)
    common = cols1 & cols2
    only1 = cols1 - cols2
    only2 = cols2 - cols1

    print(f"\n  Colonnes communes: {len(common)}")
    if only1:
        print(f"  Uniquement dans {name1}: {', '.join(only1)}")
    if only2:
        print(f"  Uniquement dans {name2}: {', '.join(only2)}")

    # Compare values on common columns if same row count
    if df1.shape[0] == df2.shape[0] and common:
        diffs = {}
        for col in common:
            try:
                diff_count = (df1[col] != df2[col]).sum()
                if diff_count > 0:
                    diffs[col] = diff_count
            except Exception:
                pass
        if diffs:
            print(f"\n  Differences par colonne:")
            for col, count in sorted(diffs.items(), key=lambda x: -x[1]):
                print(f"    {col}: {count} valeur(s) differente(s)")
        else:
            print(f"\n  [OK] Contenus identiques sur les colonnes communes")

@safe
def filter_data(path, expression, output=None):
    """Filtre les donnees avec une expression."""
    df = _load(path)
    try:
        filtered = df.query(expression)
    except Exception as e:
        print(f"[ERREUR] Expression invalide: {e}")
        print(f"  Colonnes disponibles: {', '.join(df.columns)}")
        return

    print(f"[OK] {len(filtered)}/{len(df)} lignes correspondent a '{expression}'")
    if len(filtered) <= 30:
        print(filtered.to_string(index=False))
    else:
        print(filtered.head(20).to_string(index=False))
        print(f"  ... et {len(filtered) - 20} autres lignes")

    if output:
        ext = os.path.splitext(output)[1].lower()
        if ext == ".xlsx":
            filtered.to_excel(output, index=False)
        else:
            filtered.to_csv(output, index=False)
        print(f"[OK] Resultat sauvegarde -> {output}")

@safe
def sort_data(path, column, desc=False, output=None):
    """Trie les donnees par colonne."""
    df = _load(path)
    if column not in df.columns:
        print(f"[ERREUR] Colonne '{column}' introuvable. Disponibles: {', '.join(df.columns)}")
        return
    sorted_df = df.sort_values(column, ascending=not desc)
    print(f"[OK] Trie par '{column}' ({'DESC' if desc else 'ASC'})")
    print(sorted_df.head(20).to_string(index=False))
    if output:
        sorted_df.to_csv(output, index=False)
        print(f"[OK] -> {output}")

@safe
def group_data(path, column, agg="count"):
    """Groupe par colonne avec aggregation."""
    df = _load(path)
    if column not in df.columns:
        print(f"[ERREUR] Colonne '{column}' introuvable. Disponibles: {', '.join(df.columns)}")
        return

    numeric_cols = df.select_dtypes(include="number").columns.tolist()

    if agg == "count":
        result = df.groupby(column).size().reset_index(name="count").sort_values("count", ascending=False)
    elif agg in ("sum", "mean", "min", "max", "std") and numeric_cols:
        result = getattr(df.groupby(column)[numeric_cols], agg)().reset_index().round(2)
    else:
        result = df.groupby(column).size().reset_index(name="count")

    print(f"\n=== Group by '{column}' ({agg}) ===\n")
    print(result.head(30).to_string(index=False))
    return result

@safe
def pivot_data(path, index_col, columns_col, values_col, output=None):
    """Tableau croise dynamique."""
    df = _load(path)
    for col in [index_col, columns_col, values_col]:
        if col not in df.columns:
            print(f"[ERREUR] Colonne '{col}' introuvable. Disponibles: {', '.join(df.columns)}")
            return

    pivot = pd.pivot_table(df, index=index_col, columns=columns_col, values=values_col,
                           aggfunc="sum", fill_value=0)
    print(f"\n=== Pivot: {index_col} x {columns_col} (valeurs: {values_col}) ===\n")
    print(pivot.round(2).to_string())

    if output:
        pivot.to_excel(output) if output.endswith(".xlsx") else pivot.to_csv(output)
        print(f"[OK] -> {output}")

@safe
def chart_data(path, x_col, y_col=None, chart_type="bar", output=None):
    """Genere un graphique HTML interactif."""
    df = _load(path)
    if x_col not in df.columns:
        print(f"[ERREUR] Colonne '{x_col}' introuvable. Disponibles: {', '.join(df.columns)}")
        return

    # Preparer les donnees
    if y_col and y_col in df.columns:
        labels = df[x_col].astype(str).tolist()
        values = df[y_col].tolist()
        title = f"{y_col} par {x_col}"
    else:
        # Auto: value_counts
        vc = df[x_col].value_counts().head(20)
        labels = vc.index.astype(str).tolist()
        values = vc.values.tolist()
        title = f"Distribution de {x_col}"
        y_col = "count"

    # Generer HTML avec Chart.js (CDN)
    colors = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6',
              '#1abc9c', '#e67e22', '#34495e', '#16a085', '#c0392b'] * 5

    chart_config = {
        "bar": "bar",
        "line": "line",
        "pie": "pie",
        "doughnut": "doughnut",
        "horizontal": "bar",
    }
    ctype = chart_config.get(chart_type, "bar")

    options_extra = ""
    if chart_type == "horizontal":
        options_extra = "indexAxis: 'y',"

    html = f"""<!DOCTYPE html>
<html><head>
<meta charset="utf-8">
<title>{title}</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
<style>
  body {{ font-family: 'Segoe UI', sans-serif; background: #1a1a2e; color: #e0e0e0;
         display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; }}
  .container {{ background: #16213e; border-radius: 12px; padding: 30px; width: 90%; max-width: 900px;
                box-shadow: 0 8px 32px rgba(0,0,0,0.3); }}
  h2 {{ text-align: center; color: #00d2ff; margin-bottom: 20px; }}
  canvas {{ max-height: 500px; }}
</style>
</head><body>
<div class="container">
  <h2>{title}</h2>
  <canvas id="chart"></canvas>
</div>
<script>
new Chart(document.getElementById('chart'), {{
  type: '{ctype}',
  data: {{
    labels: {json.dumps(labels[:50])},
    datasets: [{{
      label: '{y_col}',
      data: {json.dumps(values[:50])},
      backgroundColor: {json.dumps(colors[:len(values)])},
      borderColor: '#00d2ff',
      borderWidth: 1
    }}]
  }},
  options: {{
    {options_extra}
    responsive: true,
    plugins: {{
      legend: {{ labels: {{ color: '#e0e0e0' }} }},
      title: {{ display: false }}
    }},
    scales: {{
      x: {{ ticks: {{ color: '#aaa' }}, grid: {{ color: '#333' }} }},
      y: {{ ticks: {{ color: '#aaa' }}, grid: {{ color: '#333' }} }}
    }}
  }}
}});
</script>
</body></html>"""

    out = output or os.path.join(OUTPUT_DIR, "chart.html")
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)

    log_info(f"Chart {chart_type}: {x_col} vs {y_col} -> {out}")
    print(f"[OK] Graphique {chart_type} genere -> {out}")
    return out

@safe
def head_data(path, rows=20):
    """Affiche les premieres lignes."""
    df = _load(path)
    print(f"\n=== {os.path.basename(path)} ({df.shape[0]}x{df.shape[1]}) — {rows} premieres lignes ===\n")
    print(df.head(rows).to_string(index=False))

@safe
def columns_data(path):
    """Liste les colonnes avec types."""
    df = _load(path)
    print(f"\n=== Colonnes: {os.path.basename(path)} ({len(df.columns)}) ===\n")
    for i, col in enumerate(df.columns, 1):
        dtype = str(df[col].dtype)
        nulls = df[col].isnull().sum()
        sample = str(df[col].dropna().iloc[0])[:40] if not df[col].dropna().empty else "N/A"
        print(f"  {i:3d}. {col:25s}  {dtype:10s}  nulls={nulls:5d}  ex: {sample}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyse de donnees")
    parser.add_argument("action", choices=[
        "profile", "summary", "compare", "filter", "sort",
        "group", "pivot", "chart", "head", "columns"
    ])
    parser.add_argument("file", help="Fichier de donnees (CSV, Excel, JSON)")
    parser.add_argument("params", nargs="*", help="Parametres supplementaires")
    parser.add_argument("--output", "-o", default=None)
    parser.add_argument("--desc", action="store_true")
    parser.add_argument("--agg", default="count", choices=["count", "sum", "mean", "min", "max", "std"])
    parser.add_argument("--type", default="bar", dest="chart_type")
    parser.add_argument("--rows", type=int, default=20)
    args = parser.parse_args()

    if args.action == "profile":
        profile_data(args.file)
    elif args.action == "summary":
        summary_data(args.file)
    elif args.action == "compare":
        if not args.params:
            print("[ERREUR] Fichier de comparaison requis")
            sys.exit(1)
        compare_data(args.file, args.params[0])
    elif args.action == "filter":
        if not args.params:
            print("[ERREUR] Expression de filtre requise (ex: 'age > 30')")
            sys.exit(1)
        filter_data(args.file, args.params[0], args.output)
    elif args.action == "sort":
        col = args.params[0] if args.params else None
        if not col:
            print("[ERREUR] Colonne de tri requise")
            sys.exit(1)
        sort_data(args.file, col, args.desc, args.output)
    elif args.action == "group":
        col = args.params[0] if args.params else None
        if not col:
            print("[ERREUR] Colonne de groupement requise")
            sys.exit(1)
        group_data(args.file, col, args.agg)
    elif args.action == "pivot":
        if len(args.params) < 3:
            print("[ERREUR] Requis: index columns values")
            sys.exit(1)
        pivot_data(args.file, args.params[0], args.params[1], args.params[2], args.output)
    elif args.action == "chart":
        x = args.params[0] if args.params else None
        y = args.params[1] if len(args.params) > 1 else None
        if not x:
            # Auto: first column
            df = _load(args.file)
            x = df.columns[0]
        chart_data(args.file, x, y, args.chart_type, args.output)
    elif args.action == "head":
        head_data(args.file, args.rows)
    elif args.action == "columns":
        columns_data(args.file)
