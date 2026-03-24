"""
CX — Point d'entree unifie de l'environnement augmente.
Un seul fichier pour acceder a toutes les capacites.

Usage:  python cx.py <commande> [args...]

=== COMMANDES ===
  system     cpu|ram|disk|battery|processes|all     Info systeme
  desktop    list_windows|focus|screenshot|...      Controle desktop
  search     "query" [--instant] [--max N]          Recherche web DuckDuckGo
  fetch      <url> [-o fichier]                     Telecharger page web
  read       <fichier> [--pages 1-3]                Lire document (PDF/Excel/CSV)
  info       <fichier>                              Metadonnees document
  convert    <fichier> <format>                     Convertir fichier
  batch      convert|read|info <pattern> [--to fmt] Operations multi-fichiers
  scaffold   <nom> --lang python|node|web           Creer projet
  git        status|save|log|changelog|diff         Operations Git
  gh         status|prs|issues|ci|repos|clone       GitHub
  notion     search "query"                         Notion
  doc        word|pptx --title "..." -o fichier     Generer Word/PowerPoint
  report     html|dashboard -o fichier              Generer rapport HTML
  pdf        merge|split|watermark|info|count        Outils PDF avances
  image      info|resize|compress|watermark|convert  Outils image
  data       profile|summary|chart|filter|pivot      Analyse donnees
  text       extract-emails|summarize|replace|slug   Transformations texte
  quality    analyze|stats|duplicates|normalize      Controle qualite contenu
  email      send|template|test|config               Envoi emails SMTP
  ghci       pr-list|pr-diff|checks|runs|failures   GitHub/CI avance
  db         connect|tables|query|schema|diagnose    DB Explorer read-only
  obs        logs|errors|stats|health|latency|digest Observability
  onboard    [scan|quick|commands] [<path>]          Repo onboarding
  triage     run|rerun|isolate|report|detect         Test triage
  perf       http|script|system|diagnose|compare     Investigation performance
  macro      run|list|add                           Macros (enchainements)
  memory     get|set|list|delete|search             Memoire persistante
  check      (diagnostic environnement)
  deps       (installer dependances manquantes)
  help       (cette aide)
"""
import sys
import os
import subprocess

SCRIPTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scripts")

COMMANDS = {
    # --- Core ---
    "system":   ("system_info.py",      "Info systeme (CPU/RAM/disk/battery/processes)"),
    "desktop":  ("desktop_control.py",  "Controle desktop (fenetres/clipboard/keys/ecran)"),
    "check":    ("system_check.py",     "Diagnostic complet environnement"),
    "deps":     ("install_deps.py",     "Installer dependances manquantes"),
    # --- Web ---
    "search":   ("web_search.py",       "Recherche web DuckDuckGo"),
    "fetch":    ("web_fetch.py",        "Telecharger page web"),
    # --- Documents ---
    "read":     ("doc_reader.py",       "Lire document (PDF/Excel/CSV)"),
    "info":     ("doc_reader.py",       "Metadonnees document"),
    "convert":  ("file_convert.py",     "Convertir fichiers"),
    "batch":    ("batch_process.py",    "Operations multi-fichiers"),
    "doc":      ("doc_gen.py",          "Generer Word/PowerPoint"),
    "report":   ("report_gen.py",       "Generer rapport/dashboard HTML"),
    # --- Projet ---
    "scaffold": ("scaffold_project.py", "Creer un nouveau projet"),
    "git":      ("git_quick.py",        "Operations Git rapides"),
    "gh":       ("gh_helper.py",        "GitHub (PRs/issues/CI/repos)"),
    "notion":   ("notion_quick.py",     "Acces Notion"),
    # --- Automation ---
    "macro":    ("macros.py",           "Macros (enchainements nommes)"),
    "memory":   ("memory_store.py",     "Memoire persistante cle-valeur"),
    # --- API ---
    "api":      ("api_client.py",      "Client API REST universel"),
    # --- PDF ---
    "pdf":      ("pdf_tools.py",      "Outils PDF (merge/split/watermark/info)"),
    # --- Images ---
    "image":    ("image_tools.py",    "Outils image (resize/compress/watermark/convert/crop)"),
    # --- Donnees ---
    "data":     ("data_analyzer.py",  "Analyse donnees (profile/summary/chart/filter/pivot)"),
    # --- Texte ---
    "text":     ("text_transform.py", "Transformations texte (extract/summarize/replace/slug)"),
    # --- Email ---
    "email":    ("email_sender.py",   "Envoi emails SMTP (send/template/config)"),
    # --- GitHub/CI ---
    "ghci":     ("gh_ci.py",         "GitHub/CI avance (PRs/diffs/checks/runs/logs)"),
    # --- Database ---
    "db":       ("db_explorer.py",   "Explorateur DB read-only (SQLite/PG/MySQL)"),
    # --- Observability ---
    "obs":      ("observability.py", "Observability (logs/erreurs/latence/Sentry/metriques)"),
    # --- Skills ---
    "onboard":  ("repo_onboard.py",  "Repo onboarding (stack/entrypoints/commandes)"),
    "triage":   ("test_triage.py",   "Test triage (run/rerun/isolate/classify)"),
    "perf":     ("perf_investigate.py", "Investigation performance (http/profile/diagnose)"),
    # --- Qualite ---
    "quality":  ("quality_check.py",  "Controle qualite contenu (stats/analyze/duplicates)"),
    "test":     ("self_test.py",       "Auto-test de tous les scripts"),
    "checklist":("checklist.py",       "Checklists de workflows"),
    "snippet":  ("snippet.py",         "Snippets de code reutilisables"),
}

# Commandes qui ont besoin d'un prefixe d'action
PREFIX_COMMANDS = {
    "read": "read",
    "info": "info",
}

def show_help():
    print("CX - Super Codex - Point d'entree unifie")
    print("=" * 50)
    categories = {
        "SYSTEME":    ["system", "desktop", "check", "deps"],
        "WEB":        ["search", "fetch"],
        "DOCUMENTS":  ["read", "info", "convert", "batch", "doc", "report", "pdf", "image"],
        "DONNEES":    ["data"],
        "TEXTE":      ["text", "quality"],
        "EMAIL":      ["email"],
        "PROJET":     ["scaffold", "git", "gh", "ghci", "notion"],
        "DATABASE":   ["db"],
        "OBSERVABILITY": ["obs"],
        "SKILLS":     ["onboard", "triage", "perf"],
        "AUTOMATION": ["macro", "memory"],
        "API":        ["api"],
        "QUALITE":    ["test", "checklist", "snippet"],
    }
    for cat, cmds in categories.items():
        print(f"\n  [{cat}]")
        for c in cmds:
            if c in COMMANDS:
                _, desc = COMMANDS[c]
                print(f"    cx {c:10s}  {desc}")
    print(f"\n  Total: {len(COMMANDS)} commandes")
    print("\nExemples:")
    print("  python cx.py system ram")
    print("  python cx.py search 'python tutorials'")
    print("  python cx.py read rapport.pdf --pages 1-5")
    print("  python cx.py batch convert *.csv --to xlsx")
    print("  python cx.py doc word --title 'Rapport' -o rapport.docx")
    print("  python cx.py macro run morning")
    print("  python cx.py memory set projet 'Super Codex'")
    print("  python cx.py gh repos")

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] in ("help", "-h", "--help"):
        show_help()
        sys.exit(0)

    cmd = sys.argv[1]
    if cmd not in COMMANDS:
        print(f"Commande inconnue: {cmd}")
        show_help()
        sys.exit(1)

    script, _ = COMMANDS[cmd]
    script_path = os.path.join(SCRIPTS_DIR, script)

    # Construire les args
    args = sys.argv[2:]
    if cmd in PREFIX_COMMANDS:
        args = [PREFIX_COMMANDS[cmd]] + args

    try:
        result = subprocess.run([sys.executable, script_path] + args, timeout=300)
        sys.exit(result.returncode)
    except subprocess.TimeoutExpired:
        print(f"[TIMEOUT] La commande '{cmd}' a depasse le temps limite (5 min)")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n[STOP] Interrompu.")
        sys.exit(0)
    except Exception as e:
        print(f"[ERREUR] {e}")
        sys.exit(1)
