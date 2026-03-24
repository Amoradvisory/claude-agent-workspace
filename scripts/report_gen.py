"""
Generateur de rapports — HTML et PDF depuis templates Jinja2.
Usage:
  python scripts/report_gen.py html --title "Mon rapport" --data data.json --output rapport.html
  python scripts/report_gen.py pdf  --title "Mon rapport" --data data.json --output rapport.pdf
  python scripts/report_gen.py dashboard --output output/dashboard.html
"""
import sys
import os
import json
import argparse
from datetime import datetime

def ensure(pkg, imp=None):
    try:
        return __import__(imp or pkg.replace("-","_"))
    except ImportError:
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg, "-q"])
        return __import__(imp or pkg.replace("-","_"))

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{ title }}</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: 'Segoe UI', system-ui, sans-serif; background: #f5f5f5; color: #333; padding: 2rem; }
  .container { max-width: 900px; margin: 0 auto; background: white; border-radius: 12px; padding: 2rem; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
  h1 { color: #1a1a2e; margin-bottom: 0.5rem; }
  .meta { color: #666; font-size: 0.9rem; margin-bottom: 2rem; border-bottom: 1px solid #eee; padding-bottom: 1rem; }
  h2 { color: #16213e; margin: 1.5rem 0 0.8rem; }
  table { width: 100%; border-collapse: collapse; margin: 1rem 0; }
  th { background: #1a1a2e; color: white; padding: 0.7rem; text-align: left; }
  td { padding: 0.6rem 0.7rem; border-bottom: 1px solid #eee; }
  tr:hover { background: #f8f9fa; }
  .metric { display: inline-block; background: #e8f4f8; border-radius: 8px; padding: 1rem 1.5rem; margin: 0.5rem; text-align: center; }
  .metric .value { font-size: 1.8rem; font-weight: bold; color: #1a1a2e; }
  .metric .label { font-size: 0.85rem; color: #666; }
  .section { margin: 1.5rem 0; }
  ul { padding-left: 1.5rem; }
  li { margin: 0.3rem 0; }
  .footer { margin-top: 2rem; padding-top: 1rem; border-top: 1px solid #eee; font-size: 0.8rem; color: #999; }
</style>
</head>
<body>
<div class="container">
  <h1>{{ title }}</h1>
  <div class="meta">Genere le {{ date }} | {{ subtitle }}</div>
  {% if metrics %}
  <div class="section">
    <h2>Metriques</h2>
    {% for m in metrics %}
    <div class="metric">
      <div class="value">{{ m.value }}</div>
      <div class="label">{{ m.label }}</div>
    </div>
    {% endfor %}
  </div>
  {% endif %}
  {% if table_data %}
  <div class="section">
    <h2>{{ table_title or 'Donnees' }}</h2>
    <table>
      <tr>{% for h in table_headers %}<th>{{ h }}</th>{% endfor %}</tr>
      {% for row in table_data %}
      <tr>{% for cell in row %}<td>{{ cell }}</td>{% endfor %}</tr>
      {% endfor %}
    </table>
  </div>
  {% endif %}
  {% if sections %}
  {% for s in sections %}
  <div class="section">
    <h2>{{ s.title }}</h2>
    {% if s.type == 'list' %}
    <ul>{% for item in s.items %}<li>{{ item }}</li>{% endfor %}</ul>
    {% elif s.type == 'text' %}
    <p>{{ s.content }}</p>
    {% endif %}
  </div>
  {% endfor %}
  {% endif %}
  <div class="footer">Rapport genere automatiquement par CX Report Generator</div>
</div>
</body>
</html>"""

DASHBOARD_TEMPLATE = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<title>CX Dashboard</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: 'Segoe UI', sans-serif; background: #0d1117; color: #c9d1d9; padding: 1.5rem; }
  h1 { color: #58a6ff; margin-bottom: 1rem; }
  .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1rem; }
  .card { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 1.2rem; }
  .card h3 { color: #58a6ff; margin-bottom: 0.8rem; font-size: 0.95rem; }
  .stat { font-size: 1.6rem; font-weight: bold; color: #f0f6fc; }
  .label { font-size: 0.8rem; color: #8b949e; margin-top: 0.2rem; }
  .bar { height: 8px; background: #21262d; border-radius: 4px; margin-top: 0.5rem; overflow: hidden; }
  .bar-fill { height: 100%; border-radius: 4px; }
  .green { background: #3fb950; }
  .yellow { background: #d29922; }
  .red { background: #f85149; }
  .footer { margin-top: 1.5rem; text-align: center; font-size: 0.75rem; color: #484f58; }
  table { width: 100%; border-collapse: collapse; }
  td, th { padding: 0.4rem 0.6rem; text-align: left; border-bottom: 1px solid #21262d; font-size: 0.85rem; }
  th { color: #8b949e; }
</style>
</head>
<body>
<h1>CX System Dashboard</h1>
<div class="grid">
  <div class="card">
    <h3>RAM</h3>
    <div class="stat">{{ ram_used }}%</div>
    <div class="label">{{ ram_free }} GB libres / {{ ram_total }} GB</div>
    <div class="bar"><div class="bar-fill {{ 'green' if ram_used < 60 else 'yellow' if ram_used < 85 else 'red' }}" style="width:{{ ram_used }}%"></div></div>
  </div>
  <div class="card">
    <h3>Disque C:</h3>
    <div class="stat">{{ disk_used }}%</div>
    <div class="label">{{ disk_free }} GB libres / {{ disk_total }} GB</div>
    <div class="bar"><div class="bar-fill {{ 'green' if disk_used < 70 else 'yellow' if disk_used < 90 else 'red' }}" style="width:{{ disk_used }}%"></div></div>
  </div>
  <div class="card">
    <h3>Ecran</h3>
    <div class="stat">{{ screen_w }}x{{ screen_h }}</div>
    <div class="label">{{ monitor_count }} moniteur(s)</div>
  </div>
  <div class="card">
    <h3>Scripts CX</h3>
    <div class="stat">{{ script_count }}</div>
    <div class="label">scripts disponibles</div>
  </div>
</div>
<br>
<div class="card">
  <h3>Top processus (RAM)</h3>
  <table>
    <tr><th>Processus</th><th>PID</th><th>RAM (MB)</th></tr>
    {% for p in processes %}
    <tr><td>{{ p.Name }}</td><td>{{ p.Id }}</td><td>{{ p.RAM_MB }}</td></tr>
    {% endfor %}
  </table>
</div>
<div class="footer">Genere le {{ date }} par CX Dashboard</div>
</body>
</html>"""

def load_data(path):
    if not path:
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def render_html(title, data, output, subtitle=""):
    jinja2 = ensure("jinja2")
    from jinja2 import Template
    tmpl = Template(HTML_TEMPLATE)
    html = tmpl.render(
        title=title,
        date=datetime.now().strftime("%Y-%m-%d %H:%M"),
        subtitle=subtitle or "",
        **data
    )
    with open(output, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[OK] Rapport HTML: {output}")

def render_dashboard(output):
    jinja2 = ensure("jinja2")
    from jinja2 import Template
    # Collect live data
    sys.path.insert(0, SCRIPTS)
    import importlib.util

    def load_script(name):
        spec = importlib.util.spec_from_file_location(name.replace(".py",""), os.path.join(SCRIPTS, name))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    si = load_script("system_info.py")
    ram = si.get_ram()
    disk_data = si.get_disk()
    procs = si.get_processes(10)

    dc = load_script("desktop_control.py")
    screen = json.loads(dc.screen_info())

    disk_c = next((d for d in disk_data if d["drive"] == "C:"), {"total_gb": 0, "free_gb": 0, "used_percent": 0})
    script_count = len([f for f in os.listdir(SCRIPTS) if f.endswith(".py")])

    tmpl = Template(DASHBOARD_TEMPLATE)
    html = tmpl.render(
        date=datetime.now().strftime("%Y-%m-%d %H:%M"),
        ram_used=ram.get("UsedPercent", 0),
        ram_free=ram.get("FreeGB", 0),
        ram_total=ram.get("TotalGB", 0),
        disk_used=disk_c.get("used_percent", 0),
        disk_free=disk_c.get("free_gb", 0),
        disk_total=disk_c.get("total_gb", 0),
        screen_w=screen.get("PrimaryWidth", "?"),
        screen_h=screen.get("PrimaryHeight", "?"),
        monitor_count=screen.get("MonitorCount", 1),
        script_count=script_count,
        processes=procs if isinstance(procs, list) else [],
    )
    with open(output, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[OK] Dashboard: {output}")

SCRIPTS = os.path.dirname(os.path.abspath(__file__))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["html", "pdf", "dashboard"])
    parser.add_argument("--title", "-t", default="Rapport")
    parser.add_argument("--data", "-d", default=None, help="Fichier JSON de donnees")
    parser.add_argument("--output", "-o", default="output/rapport.html")
    parser.add_argument("--subtitle", "-s", default="")
    args = parser.parse_args()

    if args.action == "dashboard":
        render_dashboard(args.output)
    elif args.action == "html":
        data = load_data(args.data)
        render_html(args.title, data, args.output, args.subtitle)
    elif args.action == "pdf":
        print("[INFO] PDF: generation via HTML intermediaire + navigateur")
        data = load_data(args.data)
        html_path = args.output.replace(".pdf", ".html")
        render_html(args.title, data, html_path, args.subtitle)
        print(f"[OK] HTML genere: {html_path} (ouvrir dans le navigateur pour imprimer en PDF)")
