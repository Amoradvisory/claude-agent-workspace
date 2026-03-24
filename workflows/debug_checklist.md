# Workflow : Debug systématique

## Checklist
1. **Reproduire** — Peut-on reproduire le bug de façon fiable ?
2. **Isoler** — Quel composant est en cause ? (logs, stack trace)
3. **Hypothèse** — Formuler 2-3 causes possibles
4. **Tester** — Vérifier chaque hypothèse (print, breakpoint, test unitaire)
5. **Corriger** — Appliquer le fix minimal
6. **Vérifier** — Le bug est-il résolu sans régression ?
7. **Documenter** — Noter dans memory/log.md

## Outils utiles
- `python -m pdb script.py` — debugger interactif
- `rich.traceback` — stack traces lisibles
- `pytest --tb=short` — tests rapides
