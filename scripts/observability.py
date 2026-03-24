"""
Observability — Lecture de logs, erreurs, traces, metriques.
Compatible: fichiers log, Sentry API, endpoints health/metrics.

Usage:
  python scripts/observability.py logs <path> [--level error|warn] [--last 100] [--grep "pattern"]
  python scripts/observability.py tail <path> [--lines 50]
  python scripts/observability.py errors <path>                      # Extraire uniquement les erreurs
  python scripts/observability.py stats <path>                       # Stats par niveau de log
  python scripts/observability.py timeline <path>                    # Timeline erreurs par heure
  python scripts/observability.py sentry [--project <slug>]          # Derniers events Sentry
  python scripts/observability.py health <url>                       # Check endpoint health
  python scripts/observability.py latency <url> [--count 10]         # Mesurer latences (p50/p95/p99)
  python scripts/observability.py metrics <url>                      # Lire /metrics Prometheus
  python scripts/observability.py correlate <path> --after "timestamp" --before "timestamp"
  python scripts/observability.py digest <path>                      # Resume intelligent des logs

Prerequis variables d'env (optionnel):
  SENTRY_TOKEN  — pour l'acces Sentry API
  SENTRY_ORG    — organisation Sentry
"""
import sys
import os
import re
import json
import time
import argparse
from datetime import datetime, timedelta
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import safe, log_info, log_error, CONFIGS_DIR, OUTPUT_DIR

# Log level patterns
LEVEL_PATTERNS = {
    "error":   re.compile(r"\b(ERROR|FATAL|CRITICAL|PANIC|EXCEPTION)\b", re.IGNORECASE),
    "warn":    re.compile(r"\b(WARN|WARNING)\b", re.IGNORECASE),
    "info":    re.compile(r"\b(INFO)\b", re.IGNORECASE),
    "debug":   re.compile(r"\b(DEBUG|TRACE|VERBOSE)\b", re.IGNORECASE),
}

# Timestamp patterns
TS_PATTERNS = [
    re.compile(r"(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2})"),  # ISO
    re.compile(r"(\d{2}/\w{3}/\d{4}:\d{2}:\d{2}:\d{2})"),       # Apache
    re.compile(r"(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})"),       # Syslog
]

def _classify_line(line):
    """Determine le niveau de log d'une ligne."""
    for level, pat in LEVEL_PATTERNS.items():
        if pat.search(line):
            return level
    return "other"

def _extract_timestamp(line):
    """Extrait un timestamp d'une ligne de log."""
    for pat in TS_PATTERNS:
        m = pat.search(line)
        if m:
            return m.group(1)
    return None

def _read_log(path, last=None):
    """Lit un fichier de log."""
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()
    if last:
        lines = lines[-last:]
    return lines


@safe
def cmd_logs(path, level=None, last=None, grep=None):
    """Affiche les logs filtre par niveau et/ou pattern."""
    lines = _read_log(path, last)
    filtered = []

    for line in lines:
        line = line.rstrip()
        if not line:
            continue
        if level and _classify_line(line) != level:
            continue
        if grep and not re.search(grep, line, re.IGNORECASE):
            continue
        filtered.append(line)

    print(f"\n=== Logs: {os.path.basename(path)} ({len(filtered)}/{len(lines)} lignes) ===")
    if level:
        print(f"  Filtre: level={level}")
    if grep:
        print(f"  Filtre: grep={grep}")
    print()

    for line in filtered[-200:]:
        lvl = _classify_line(line)
        if lvl == "error":
            print(f"  [!!] {line}")
        elif lvl == "warn":
            print(f"  [!]  {line}")
        else:
            print(f"       {line}")

    if len(filtered) > 200:
        print(f"\n  ... {len(filtered) - 200} lignes supplementaires")

@safe
def cmd_tail(path, lines=50):
    """Affiche les dernieres lignes."""
    data = _read_log(path, last=lines)
    print(f"\n=== Tail: {os.path.basename(path)} ({lines} dernieres lignes) ===\n")
    for line in data:
        print(f"  {line.rstrip()}")

@safe
def cmd_errors(path, last=None):
    """Extrait uniquement les erreurs et exceptions."""
    lines = _read_log(path, last)
    errors = []
    in_stack = False
    current_error = []

    for line in lines:
        line = line.rstrip()
        lvl = _classify_line(line)

        if lvl == "error" or "Traceback" in line or "Exception" in line:
            if current_error and not in_stack:
                errors.append("\n".join(current_error))
                current_error = []
            current_error.append(line)
            in_stack = "Traceback" in line
        elif in_stack and (line.startswith(" ") or line.startswith("\t") or not line):
            current_error.append(line)
        else:
            if current_error:
                errors.append("\n".join(current_error))
                current_error = []
            in_stack = False

    if current_error:
        errors.append("\n".join(current_error))

    print(f"\n=== Erreurs: {os.path.basename(path)} — {len(errors)} erreur(s) ===\n")
    for i, err in enumerate(errors[-20:], 1):
        print(f"  --- Erreur #{i} ---")
        for line in err.split("\n"):
            print(f"  {line}")
        print()

    if len(errors) > 20:
        print(f"  ... et {len(errors) - 20} erreurs plus anciennes")

@safe
def cmd_stats(path):
    """Statistiques par niveau de log."""
    lines = _read_log(path)
    counts = Counter()
    for line in lines:
        lvl = _classify_line(line.rstrip())
        counts[lvl] += 1

    total = len(lines)
    print(f"\n=== Stats: {os.path.basename(path)} ({total} lignes) ===\n")

    order = ["error", "warn", "info", "debug", "other"]
    for lvl in order:
        count = counts.get(lvl, 0)
        pct = (count / total * 100) if total > 0 else 0
        bar = "#" * int(pct / 2)
        icon = "[!!]" if lvl == "error" else "[!]" if lvl == "warn" else "[i]" if lvl == "info" else "[.]"
        print(f"  {icon} {lvl:8s}  {count:8d}  ({pct:5.1f}%)  {bar}")

    # Error rate
    error_count = counts.get("error", 0)
    if error_count > 0:
        print(f"\n  Taux d'erreur: {error_count/total*100:.2f}%")

@safe
def cmd_timeline(path):
    """Timeline des erreurs par heure."""
    lines = _read_log(path)
    hourly = defaultdict(lambda: {"error": 0, "warn": 0, "info": 0, "total": 0})

    for line in lines:
        line = line.rstrip()
        ts = _extract_timestamp(line)
        if ts:
            # Extract hour
            hour_match = re.search(r"(\d{2}):\d{2}:\d{2}", ts)
            date_match = re.search(r"(\d{4}-\d{2}-\d{2})", ts)
            if hour_match:
                hour = hour_match.group(1)
                date = date_match.group(1) if date_match else "?"
                key = f"{date} {hour}h"
                lvl = _classify_line(line)
                hourly[key]["total"] += 1
                if lvl in hourly[key]:
                    hourly[key][lvl] += 1

    if not hourly:
        print("[INFO] Aucun timestamp detecte dans les logs.")
        return

    print(f"\n=== Timeline erreurs/heures ===\n")
    print(f"  {'Heure':18s}  {'Err':>6s}  {'Warn':>6s}  {'Info':>6s}  {'Total':>6s}  Graphe")
    for key in sorted(hourly.keys()):
        h = hourly[key]
        bar_e = "!" * min(h["error"], 30)
        bar_w = "?" * min(h["warn"] // 5, 20)
        print(f"  {key:18s}  {h['error']:6d}  {h['warn']:6d}  {h['info']:6d}  {h['total']:6d}  {bar_e}{bar_w}")

@safe
def cmd_sentry(project=None):
    """Derniers evenements Sentry."""
    try:
        from env_loader import load_env
        env = load_env()
    except Exception:
        env = {}

    token = env.get("SENTRY_TOKEN") or os.environ.get("SENTRY_TOKEN")
    org = env.get("SENTRY_ORG") or os.environ.get("SENTRY_ORG")

    if not token:
        print("[!!] SENTRY_TOKEN non configure.")
        print("  Ajoutez dans configs/.env:")
        print("    SENTRY_TOKEN=votre_token_sentry")
        print("    SENTRY_ORG=votre_org")
        print("\n  Pour obtenir un token: https://sentry.io/settings/account/api/auth-tokens/")
        return

    import requests
    headers = {"Authorization": f"Bearer {token}"}
    base = "https://sentry.io/api/0"

    if project:
        url = f"{base}/projects/{org}/{project}/issues/?query=is:unresolved&sort=date&limit=10"
    else:
        url = f"{base}/organizations/{org}/issues/?query=is:unresolved&sort=date&limit=10"

    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        issues = resp.json()

        print(f"\n=== Sentry — {len(issues)} issue(s) non resolue(s) ===\n")
        for issue in issues:
            count = issue.get("count", "?")
            users = issue.get("userCount", "?")
            last = issue.get("lastSeen", "")[:19]
            print(f"  [{issue.get('level','?').upper():5s}] {issue.get('title','?')[:70]}")
            print(f"          {count} events, {users} users, last: {last}")
            print(f"          {issue.get('permalink', '')}")
            print()

    except requests.HTTPError as e:
        print(f"[ERREUR] Sentry API: {e}")
    except Exception as e:
        print(f"[ERREUR] {e}")

@safe
def cmd_health(url):
    """Check endpoint health."""
    import requests
    try:
        start = time.time()
        resp = requests.get(url, timeout=10)
        duration = (time.time() - start) * 1000

        print(f"\n=== Health Check: {url} ===\n")
        print(f"  Status     : {resp.status_code} {'[OK]' if resp.ok else '[!!]'}")
        print(f"  Latence    : {duration:.0f} ms")
        print(f"  Taille     : {len(resp.content)} bytes")
        print(f"  Content-Type: {resp.headers.get('Content-Type', 'N/A')}")

        # Try to parse JSON health response
        try:
            data = resp.json()
            if isinstance(data, dict):
                for k, v in list(data.items())[:10]:
                    print(f"  {k:15s}: {v}")
        except Exception:
            pass

    except requests.ConnectionError:
        print(f"[!!] Connexion refusee: {url}")
    except requests.Timeout:
        print(f"[!!] Timeout (>10s): {url}")
    except Exception as e:
        print(f"[ERREUR] {e}")

@safe
def cmd_latency(url, count=10):
    """Mesure les latences (p50, p95, p99)."""
    import requests

    latencies = []
    errors = 0
    print(f"\n=== Latence: {url} ({count} requetes) ===\n")

    for i in range(count):
        try:
            start = time.time()
            resp = requests.get(url, timeout=10)
            duration = (time.time() - start) * 1000
            latencies.append(duration)
            status = "[OK]" if resp.ok else f"[{resp.status_code}]"
            print(f"  #{i+1:3d}  {duration:8.1f} ms  {status}")
        except Exception as e:
            errors += 1
            print(f"  #{i+1:3d}  ERREUR: {e}")

    if not latencies:
        print("[!!] Toutes les requetes ont echoue.")
        return

    latencies.sort()
    n = len(latencies)

    p50 = latencies[int(n * 0.5)]
    p95 = latencies[int(n * 0.95)] if n > 1 else latencies[-1]
    p99 = latencies[int(n * 0.99)] if n > 1 else latencies[-1]
    avg = sum(latencies) / n
    mn = min(latencies)
    mx = max(latencies)

    print(f"\n  --- Resultats ---")
    print(f"  Requetes   : {n} OK / {errors} erreurs")
    print(f"  p50        : {p50:.1f} ms")
    print(f"  p95        : {p95:.1f} ms")
    print(f"  p99        : {p99:.1f} ms")
    print(f"  Moyenne    : {avg:.1f} ms")
    print(f"  Min        : {mn:.1f} ms")
    print(f"  Max        : {mx:.1f} ms")

    # Qualite
    if p95 < 200:
        print(f"\n  [OK] Excellente performance (p95 < 200ms)")
    elif p95 < 500:
        print(f"\n  [OK] Performance acceptable (p95 < 500ms)")
    elif p95 < 1000:
        print(f"\n  [!]  Performance degradee (p95 < 1s)")
    else:
        print(f"\n  [!!] Performance critique (p95 > 1s)")

@safe
def cmd_metrics(url):
    """Lit un endpoint /metrics Prometheus."""
    import requests
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        lines = resp.text.split("\n")

        metrics = {}
        for line in lines:
            if line.startswith("#") or not line.strip():
                continue
            parts = line.split(" ")
            if len(parts) >= 2:
                name = parts[0]
                value = parts[1]
                metrics[name] = value

        print(f"\n=== Metrics: {url} ({len(metrics)} metriques) ===\n")
        for name, value in sorted(metrics.items())[:50]:
            print(f"  {name:50s}  {value}")

        if len(metrics) > 50:
            print(f"\n  ... et {len(metrics) - 50} metriques supplementaires")

    except Exception as e:
        print(f"[ERREUR] {e}")

@safe
def cmd_correlate(path, after=None, before=None):
    """Correle les evenements dans une fenetre temporelle."""
    lines = _read_log(path)
    window = []

    for line in lines:
        line = line.rstrip()
        ts = _extract_timestamp(line)
        if ts:
            include = True
            if after and ts < after:
                include = False
            if before and ts > before:
                include = False
            if include:
                window.append((ts, _classify_line(line), line))

    print(f"\n=== Correlation: {len(window)} evenements ===")
    if after:
        print(f"  Apres:  {after}")
    if before:
        print(f"  Avant:  {before}")
    print()

    for ts, lvl, line in window[-100:]:
        icon = "[!!]" if lvl == "error" else "[!]" if lvl == "warn" else "    "
        print(f"  {icon} {line}")

@safe
def cmd_digest(path):
    """Resume intelligent des logs."""
    lines = _read_log(path)
    total = len(lines)

    # Classify
    counts = Counter()
    error_types = Counter()
    first_ts = None
    last_ts = None

    for line in lines:
        line = line.rstrip()
        lvl = _classify_line(line)
        counts[lvl] += 1

        ts = _extract_timestamp(line)
        if ts:
            if not first_ts:
                first_ts = ts
            last_ts = ts

        if lvl == "error":
            # Extract error type
            for pat in [r"(\w+Error)", r"(\w+Exception)", r"(\w+Fault)", r"(FATAL: .{0,40})"]:
                m = re.search(pat, line)
                if m:
                    error_types[m.group(1)] += 1
                    break

    print(f"\n{'='*50}")
    print(f"  DIGEST: {os.path.basename(path)}")
    print(f"{'='*50}\n")

    print(f"  Periode    : {first_ts or '?'} -> {last_ts or '?'}")
    print(f"  Total      : {total:,} lignes")
    print(f"  Erreurs    : {counts.get('error', 0):,} ({counts.get('error', 0)/total*100:.1f}%)" if total else "")
    print(f"  Warnings   : {counts.get('warn', 0):,}")
    print(f"  Info       : {counts.get('info', 0):,}")

    if error_types:
        print(f"\n  Top erreurs:")
        for err_type, count in error_types.most_common(10):
            print(f"    {err_type:40s}  x{count}")

    # Verdict
    error_rate = counts.get("error", 0) / total * 100 if total > 0 else 0
    print(f"\n  Verdict:")
    if error_rate > 10:
        print(f"  [!!] CRITIQUE — Taux d'erreur {error_rate:.1f}% (>10%)")
    elif error_rate > 2:
        print(f"  [!]  DEGRADE — Taux d'erreur {error_rate:.1f}% (>2%)")
    elif error_rate > 0:
        print(f"  [OK] ACCEPTABLE — Taux d'erreur {error_rate:.1f}%")
    else:
        print(f"  [OK] SAIN — Aucune erreur detectee")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Observability — Logs, erreurs, metriques")
    parser.add_argument("action", choices=[
        "logs", "tail", "errors", "stats", "timeline",
        "sentry", "health", "latency", "metrics",
        "correlate", "digest"
    ])
    parser.add_argument("target", nargs="?", default=None, help="Fichier de log ou URL")
    parser.add_argument("--level", "-l", default=None, choices=["error", "warn", "info", "debug"])
    parser.add_argument("--last", type=int, default=None)
    parser.add_argument("--lines", type=int, default=50)
    parser.add_argument("--grep", "-g", default=None)
    parser.add_argument("--project", "-p", default=None)
    parser.add_argument("--count", "-c", type=int, default=10)
    parser.add_argument("--after", default=None)
    parser.add_argument("--before", default=None)
    parsed = parser.parse_args()

    a = parsed.action
    t = parsed.target

    if a == "logs" and t:
        cmd_logs(t, parsed.level, parsed.last, parsed.grep)
    elif a == "tail" and t:
        cmd_tail(t, parsed.lines)
    elif a == "errors" and t:
        cmd_errors(t, parsed.last)
    elif a == "stats" and t:
        cmd_stats(t)
    elif a == "timeline" and t:
        cmd_timeline(t)
    elif a == "sentry":
        cmd_sentry(parsed.project)
    elif a == "health" and t:
        cmd_health(t)
    elif a == "latency" and t:
        cmd_latency(t, parsed.count)
    elif a == "metrics" and t:
        cmd_metrics(t)
    elif a == "correlate" and t:
        cmd_correlate(t, parsed.after, parsed.before)
    elif a == "digest" and t:
        cmd_digest(t)
    else:
        parser.print_help()
