"""
Performance Investigation — Diagnostic structure de performance backend/frontend.
Usage:
  python scripts/perf_investigate.py profile <url|script>    # Profile HTTP ou script Python
  python scripts/perf_investigate.py http <url> [--count 20] # Benchmark HTTP detaille
  python scripts/perf_investigate.py script <file.py>        # Profile script Python (cProfile)
  python scripts/perf_investigate.py memory <file.py>        # Analyse memoire
  python scripts/perf_investigate.py system                  # Etat systeme (CPU/RAM/IO)
  python scripts/perf_investigate.py hotspots <file.py>      # Detecter hot paths
  python scripts/perf_investigate.py diagnose <url>          # Diagnostic complet endpoint
  python scripts/perf_investigate.py compare <url1> <url2>   # Comparer perf de 2 endpoints
  python scripts/perf_investigate.py report <url|file>       # Rapport complet avec recommandations

Produit des diagnostics structures avec hypotheses, mesures et pistes d'optimisation.
"""
import sys
import os
import re
import json
import time
import argparse
import subprocess
import cProfile
import pstats
import io
from collections import defaultdict
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import safe, log_info, OUTPUT_DIR


def _timed_requests(url, count=10, timeout=10):
    """Mesure les latences HTTP."""
    import requests

    results = []
    for i in range(count):
        try:
            start = time.time()
            resp = requests.get(url, timeout=timeout)
            duration = (time.time() - start) * 1000
            results.append({
                "status": resp.status_code,
                "latency_ms": round(duration, 1),
                "size_bytes": len(resp.content),
                "ok": resp.ok,
                "headers": dict(resp.headers),
            })
        except Exception as e:
            results.append({
                "status": 0,
                "latency_ms": -1,
                "size_bytes": 0,
                "ok": False,
                "error": str(e),
            })
    return results


def _percentiles(values):
    """Calcule p50, p95, p99."""
    if not values:
        return {}
    s = sorted(values)
    n = len(s)
    return {
        "min": round(s[0], 1),
        "p50": round(s[int(n * 0.5)], 1),
        "p75": round(s[int(n * 0.75)], 1),
        "p90": round(s[int(n * 0.9)], 1) if n > 1 else round(s[-1], 1),
        "p95": round(s[int(n * 0.95)], 1) if n > 1 else round(s[-1], 1),
        "p99": round(s[int(n * 0.99)], 1) if n > 1 else round(s[-1], 1),
        "max": round(s[-1], 1),
        "avg": round(sum(s) / n, 1),
        "count": n,
    }


def _system_snapshot():
    """Capture l'etat systeme."""
    info = {}
    try:
        # CPU via PowerShell
        r = subprocess.run(
            ["powershell", "-Command",
             "Get-CimInstance Win32_Processor | Select-Object LoadPercentage | ConvertTo-Json"],
            capture_output=True, text=True, timeout=10
        )
        if r.returncode == 0:
            cpu = json.loads(r.stdout)
            info["cpu_percent"] = cpu.get("LoadPercentage", "?")
    except Exception:
        pass

    try:
        # RAM
        r = subprocess.run(
            ["powershell", "-Command",
             "Get-CimInstance Win32_OperatingSystem | Select-Object TotalVisibleMemorySize,FreePhysicalMemory | ConvertTo-Json"],
            capture_output=True, text=True, timeout=10
        )
        if r.returncode == 0:
            mem = json.loads(r.stdout)
            total = mem.get("TotalVisibleMemorySize", 0) / 1024 / 1024
            free = mem.get("FreePhysicalMemory", 0) / 1024 / 1024
            info["ram_total_gb"] = round(total, 1)
            info["ram_free_gb"] = round(free, 1)
            info["ram_used_pct"] = round((1 - free/total) * 100, 1) if total > 0 else 0
    except Exception:
        pass

    try:
        # Top processes by CPU
        r = subprocess.run(
            ["powershell", "-Command",
             "Get-Process | Sort-Object CPU -Descending | Select-Object -First 5 Name,CPU,WorkingSet | ConvertTo-Json"],
            capture_output=True, text=True, timeout=10
        )
        if r.returncode == 0:
            info["top_processes"] = json.loads(r.stdout)
    except Exception:
        pass

    return info


@safe
def cmd_http(url, count=20):
    """Benchmark HTTP detaille."""
    import requests

    print(f"\n=== HTTP Benchmark: {url} ===")
    print(f"  Requetes: {count}\n")

    results = _timed_requests(url, count)
    latencies = [r["latency_ms"] for r in results if r["ok"]]
    errors = [r for r in results if not r["ok"]]

    if not latencies:
        print("[!!] Toutes les requetes ont echoue.")
        for e in errors[:3]:
            print(f"  Erreur: {e.get('error', 'unknown')}")
        return

    p = _percentiles(latencies)
    sizes = [r["size_bytes"] for r in results if r["ok"]]

    print(f"  Latences (ms):")
    print(f"    p50  : {p['p50']:8.1f} ms")
    print(f"    p75  : {p['p75']:8.1f} ms")
    print(f"    p90  : {p['p90']:8.1f} ms")
    print(f"    p95  : {p['p95']:8.1f} ms")
    print(f"    p99  : {p['p99']:8.1f} ms")
    print(f"    avg  : {p['avg']:8.1f} ms")
    print(f"    min  : {p['min']:8.1f} ms")
    print(f"    max  : {p['max']:8.1f} ms")

    print(f"\n  Taille reponse: {sizes[0]:,} bytes" if sizes else "")
    print(f"  Erreurs: {len(errors)}/{count}")

    # Response analysis
    first_ok = next((r for r in results if r["ok"]), None)
    if first_ok:
        headers = first_ok.get("headers", {})
        print(f"\n  Headers interessants:")
        for h in ["Server", "X-Response-Time", "X-Cache", "Cache-Control",
                   "Content-Encoding", "Vary", "X-Powered-By"]:
            if h.lower() in {k.lower(): k for k in headers}:
                key = {k.lower(): k for k in headers}.get(h.lower(), h)
                print(f"    {key}: {headers.get(key, 'N/A')}")

    # Verdict
    print(f"\n  Diagnostic:")
    if p["p95"] < 100:
        print(f"  [OK] Excellente performance (p95={p['p95']}ms < 100ms)")
    elif p["p95"] < 300:
        print(f"  [OK] Bonne performance (p95={p['p95']}ms < 300ms)")
    elif p["p95"] < 1000:
        print(f"  [!]  Performance acceptable (p95={p['p95']}ms < 1s)")
    else:
        print(f"  [!!] Performance degradee (p95={p['p95']}ms > 1s)")

    if p["max"] > p["p95"] * 3:
        print(f"  [!]  Outliers detectes: max ({p['max']}ms) >> p95 ({p['p95']}ms)")

    variance = p["max"] - p["min"]
    if variance > p["avg"] * 2:
        print(f"  [!]  Haute variance ({variance:.0f}ms) — performance instable")

@safe
def cmd_script(filepath):
    """Profile un script Python avec cProfile."""
    print(f"\n=== Profile: {filepath} ===\n")

    profiler = cProfile.Profile()
    try:
        profiler.enable()
        start = time.time()
        exec(compile(open(filepath, "r").read(), filepath, "exec"), {"__name__": "__main__"})
        duration = time.time() - start
        profiler.disable()
    except Exception as e:
        profiler.disable()
        print(f"[ERREUR] {e}")
        duration = time.time() - start

    print(f"  Duree totale: {duration:.3f}s\n")

    # Top 20 functions by cumulative time
    s = io.StringIO()
    ps = pstats.Stats(profiler, stream=s).sort_stats("cumulative")
    ps.print_stats(20)

    print("  Top 20 fonctions (temps cumulatif):\n")
    for line in s.getvalue().split("\n"):
        if line.strip():
            print(f"  {line}")

    # Recommendations
    print(f"\n  Recommandations:")
    stats_list = []
    for func, (cc, nc, tt, ct, callers) in profiler.stats.items():
        stats_list.append({"func": f"{func[0]}:{func[1]}:{func[2]}", "cumtime": ct, "tottime": tt, "calls": nc})

    stats_list.sort(key=lambda x: -x["cumtime"])
    hotspots = stats_list[:5]

    for i, hs in enumerate(hotspots, 1):
        if hs["cumtime"] > duration * 0.1:
            print(f"  {i}. [{hs['cumtime']:.3f}s / {hs['cumtime']/duration*100:.0f}%] {hs['func']}")
            if hs["calls"] > 1000:
                print(f"     -> {hs['calls']} appels — reduire le nombre d'appels?")

@safe
def cmd_memory(filepath):
    """Analyse l'utilisation memoire d'un script."""
    print(f"\n=== Memory Analysis: {filepath} ===\n")

    # Check if tracemalloc is available
    code = f"""
import tracemalloc
import sys
tracemalloc.start()

# Execute the script
exec(open(r"{filepath}", "r").read())

snapshot = tracemalloc.take_snapshot()
stats = snapshot.statistics("lineno")

print("Top 15 allocations memoire:")
print("=" * 60)
total = 0
for stat in stats[:15]:
    size_kb = stat.size / 1024
    total += stat.size
    print(f"  {{size_kb:8.1f}} KB  {{stat}}")

print(f"\\nTotal top 15: {{total/1024:.1f}} KB")
current, peak = tracemalloc.get_traced_memory()
print(f"Memoire courante: {{current/1024:.1f}} KB")
print(f"Memoire pic: {{peak/1024:.1f}} KB")
tracemalloc.stop()
"""

    r = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True, text=True, timeout=60,
        encoding="utf-8", errors="replace"
    )

    if r.returncode == 0:
        print(r.stdout)
    else:
        print(f"[ERREUR] {r.stderr[:500]}")

    # Recommendations
    print(f"\n  Recommandations:")
    print(f"  - Si le pic depasse 100MB: cherchez les grandes listes/dicts en memoire")
    print(f"  - Utilisez des generateurs au lieu de listes pour les grands datasets")
    print(f"  - Liberez les references inutiles avec 'del'")

@safe
def cmd_system():
    """Etat systeme actuel."""
    print(f"\n=== Etat Systeme ===\n")

    info = _system_snapshot()

    if "cpu_percent" in info:
        print(f"  CPU         : {info['cpu_percent']}%")
    if "ram_total_gb" in info:
        print(f"  RAM totale  : {info['ram_total_gb']} GB")
        print(f"  RAM libre   : {info['ram_free_gb']} GB")
        print(f"  RAM utilisee: {info['ram_used_pct']}%")

    if "top_processes" in info:
        print(f"\n  Top processus (CPU):")
        procs = info["top_processes"]
        if isinstance(procs, dict):
            procs = [procs]
        for p in procs[:5]:
            cpu = p.get("CPU", 0)
            mem_mb = p.get("WorkingSet", 0) / 1024 / 1024
            print(f"    {p.get('Name','?'):25s}  CPU={cpu:.0f}  RAM={mem_mb:.0f}MB")

    # Verdict
    if info.get("ram_used_pct", 0) > 90:
        print(f"\n  [!!] RAM critique ({info['ram_used_pct']}%) — performance degradee probable")
    elif info.get("ram_used_pct", 0) > 75:
        print(f"\n  [!]  RAM elevee ({info['ram_used_pct']}%) — surveiller")

    if info.get("cpu_percent", 0) > 80:
        print(f"  [!!] CPU charge ({info['cpu_percent']}%) — ralentissements possibles")

@safe
def cmd_hotspots(filepath):
    """Detecte les hot paths dans un fichier Python."""
    print(f"\n=== Hotspots: {filepath} ===\n")

    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    issues = []

    for i, line in enumerate(lines, 1):
        stripped = line.strip()

        # Nested loops
        indent = len(line) - len(line.lstrip())
        if re.match(r"\s*for\s+", line) and indent >= 8:
            issues.append((i, "NESTED_LOOP", "Boucle imbriquee profonde — O(n^2+) possible", line.strip()))

        # N+1 patterns
        if re.search(r"\bfor\b.*\b(query|execute|fetch|find|get|select)\b", stripped, re.IGNORECASE):
            issues.append((i, "N+1", "Requete dans une boucle — N+1 probable", stripped))

        # String concatenation in loop
        if re.search(r"\+=\s*[\"']", stripped) or re.search(r"\+=\s*str\(", stripped):
            issues.append((i, "STRING_CONCAT", "Concatenation de string dans boucle — utilisez join()", stripped))

        # Global imports in functions
        if stripped.startswith("import ") and indent > 0:
            issues.append((i, "LAZY_IMPORT", "Import dans une fonction — overhead a chaque appel", stripped))

        # Sleep
        if "time.sleep" in stripped or "sleep(" in stripped:
            issues.append((i, "SLEEP", "sleep() detecte — blocking call", stripped))

        # Large list comprehension
        if re.search(r"\[.{50,}\]", stripped):
            issues.append((i, "LARGE_COMPREHENSION", "Grande comprehension — generateur possible?", stripped[:80]))

    if issues:
        print(f"  {len(issues)} hotspot(s) potentiel(s):\n")
        for line_num, category, desc, code in issues:
            print(f"  L{line_num:4d} [{category}] {desc}")
            print(f"        {code[:80]}")
            print()
    else:
        print("  [OK] Aucun hotspot evident detecte.")

    # File stats
    print(f"\n  Stats fichier:")
    print(f"    Lignes: {len(lines)}")
    functions = sum(1 for l in lines if l.strip().startswith("def "))
    classes = sum(1 for l in lines if l.strip().startswith("class "))
    print(f"    Fonctions: {functions}")
    print(f"    Classes: {classes}")

@safe
def cmd_diagnose(url):
    """Diagnostic complet d'un endpoint."""
    import requests

    print(f"\n{'='*60}")
    print(f"  PERFORMANCE DIAGNOSIS: {url}")
    print(f"{'='*60}\n")

    # 1. System state
    print("  [1] ETAT SYSTEME\n")
    info = _system_snapshot()
    print(f"  CPU: {info.get('cpu_percent', '?')}%  |  RAM: {info.get('ram_used_pct', '?')}%")

    # 2. Warm-up request
    print(f"\n  [2] WARM-UP\n")
    try:
        start = time.time()
        resp = requests.get(url, timeout=15)
        warmup = (time.time() - start) * 1000
        print(f"  Premier appel: {warmup:.0f}ms (status={resp.status_code}, size={len(resp.content)}B)")
    except Exception as e:
        print(f"  [!!] Echec: {e}")
        return

    # 3. Benchmark
    print(f"\n  [3] BENCHMARK (20 requetes)\n")
    results = _timed_requests(url, 20)
    latencies = [r["latency_ms"] for r in results if r["ok"]]
    p = _percentiles(latencies) if latencies else {}

    if p:
        print(f"  p50={p['p50']}ms  p95={p['p95']}ms  p99={p['p99']}ms  avg={p['avg']}ms")
        print(f"  min={p['min']}ms  max={p['max']}ms")

    # 4. Response analysis
    print(f"\n  [4] ANALYSE REPONSE\n")
    if resp:
        ct = resp.headers.get("Content-Type", "?")
        encoding = resp.headers.get("Content-Encoding", "none")
        cache = resp.headers.get("Cache-Control", "none")
        print(f"  Content-Type: {ct}")
        print(f"  Encoding: {encoding}")
        print(f"  Cache-Control: {cache}")
        print(f"  Taille: {len(resp.content):,} bytes")

    # 5. Hypotheses & Recommendations
    print(f"\n  [5] DIAGNOSTIC\n")
    hypotheses = []

    if p.get("p95", 0) > 1000:
        hypotheses.append(("CRITIQUE", "Latence p95 > 1s — goulot d'etranglement majeur"))
    elif p.get("p95", 0) > 300:
        hypotheses.append(("DEGRADE", "Latence p95 > 300ms — optimisation recommandee"))

    if warmup > p.get("avg", 0) * 3 and warmup > 500:
        hypotheses.append(("COLD_START", f"Cold start ({warmup:.0f}ms >> avg {p.get('avg',0):.0f}ms) — prewarming?"))

    variance = p.get("max", 0) - p.get("min", 0)
    if variance > p.get("avg", 1) * 3:
        hypotheses.append(("INSTABLE", f"Haute variance ({variance:.0f}ms) — GC? contention? throttling?"))

    if encoding == "none" and len(resp.content) > 10000:
        hypotheses.append(("NO_COMPRESSION", f"Pas de compression ({len(resp.content):,}B) — activer gzip/brotli"))

    if cache == "none":
        hypotheses.append(("NO_CACHE", "Pas de cache HTTP — ajouter Cache-Control si possible"))

    if info.get("ram_used_pct", 0) > 85:
        hypotheses.append(("RAM_PRESSURE", f"RAM a {info['ram_used_pct']}% — swap possible = latence"))

    if info.get("cpu_percent", 0) > 70:
        hypotheses.append(("CPU_PRESSURE", f"CPU a {info['cpu_percent']}% — surcharge possible"))

    if hypotheses:
        for severity, msg in hypotheses:
            icon = "[!!]" if severity in ("CRITIQUE", "RAM_PRESSURE", "CPU_PRESSURE") else "[!]"
            print(f"  {icon} [{severity}] {msg}")
    else:
        print("  [OK] Aucun probleme de performance evident.")

    # 6. Actions
    print(f"\n  [6] ACTIONS RECOMMANDEES\n")
    actions = []
    if any(h[0] == "CRITIQUE" for h in hypotheses):
        actions.append("Profiler le backend (DB queries, CPU-intensive ops)")
    if any(h[0] == "NO_COMPRESSION" for h in hypotheses):
        actions.append("Activer gzip/brotli dans le reverse proxy ou l'app")
    if any(h[0] == "NO_CACHE" for h in hypotheses):
        actions.append("Ajouter Cache-Control: max-age=... pour les ressources statiques")
    if any(h[0] == "COLD_START" for h in hypotheses):
        actions.append("Prewarmer le service apres deploy, ou garder les connexions DB ouvertes")
    if any(h[0] == "INSTABLE" for h in hypotheses):
        actions.append("Investiguer GC pauses, contention threads, ou throttling cloud")
    if any(h[0] == "RAM_PRESSURE" for h in hypotheses):
        actions.append("Reduire l'empreinte memoire ou augmenter la RAM")

    if not actions:
        actions.append("Performance acceptable — monitorer en continu")

    for i, a in enumerate(actions, 1):
        print(f"  {i}. {a}")

    print(f"\n{'='*60}")

@safe
def cmd_compare(url1, url2, count=10):
    """Compare les performances de 2 endpoints."""
    import requests

    print(f"\n=== Comparaison Performance ===\n")
    print(f"  A: {url1}")
    print(f"  B: {url2}")
    print(f"  Requetes: {count} chacun\n")

    results_a = _timed_requests(url1, count)
    results_b = _timed_requests(url2, count)

    lat_a = [r["latency_ms"] for r in results_a if r["ok"]]
    lat_b = [r["latency_ms"] for r in results_b if r["ok"]]

    p_a = _percentiles(lat_a) if lat_a else {}
    p_b = _percentiles(lat_b) if lat_b else {}

    print(f"  {'Metrique':10s}  {'A':>10s}  {'B':>10s}  {'Diff':>10s}")
    print(f"  {'-'*45}")

    for metric in ["p50", "p95", "p99", "avg", "min", "max"]:
        va = p_a.get(metric, 0)
        vb = p_b.get(metric, 0)
        diff = vb - va
        sign = "+" if diff > 0 else ""
        better = "<- mieux" if diff > 0 else "mieux ->" if diff < 0 else ""
        print(f"  {metric:10s}  {va:8.1f}ms  {vb:8.1f}ms  {sign}{diff:7.1f}ms  {better}")

    size_a = results_a[0].get("size_bytes", 0) if results_a and results_a[0].get("ok") else 0
    size_b = results_b[0].get("size_bytes", 0) if results_b and results_b[0].get("ok") else 0
    print(f"\n  Taille A: {size_a:,}B  |  Taille B: {size_b:,}B")

    # Verdict
    if p_a.get("p95", 0) < p_b.get("p95", 0):
        ratio = p_b["p95"] / p_a["p95"] if p_a["p95"] > 0 else 0
        print(f"\n  -> A est {ratio:.1f}x plus rapide (p95)")
    elif p_b.get("p95", 0) < p_a.get("p95", 0):
        ratio = p_a["p95"] / p_b["p95"] if p_b["p95"] > 0 else 0
        print(f"\n  -> B est {ratio:.1f}x plus rapide (p95)")
    else:
        print(f"\n  -> Performance equivalente")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Performance Investigation")
    parser.add_argument("action", choices=[
        "http", "script", "memory", "system", "hotspots",
        "diagnose", "compare", "report"
    ])
    parser.add_argument("target", nargs="?", default=None)
    parser.add_argument("target2", nargs="?", default=None)
    parser.add_argument("--count", "-c", type=int, default=20)
    parsed = parser.parse_args()

    a = parsed.action
    t = parsed.target

    if a == "http" and t:
        cmd_http(t, parsed.count)
    elif a == "script" and t:
        cmd_script(t)
    elif a == "memory" and t:
        cmd_memory(t)
    elif a == "system":
        cmd_system()
    elif a == "hotspots" and t:
        cmd_hotspots(t)
    elif a == "diagnose" and t:
        cmd_diagnose(t)
    elif a == "compare" and t and parsed.target2:
        cmd_compare(t, parsed.target2, parsed.count)
    elif a == "report" and t:
        # Report = diagnose
        if t.startswith("http"):
            cmd_diagnose(t)
        else:
            cmd_hotspots(t)
            cmd_script(t)
    else:
        parser.print_help()
