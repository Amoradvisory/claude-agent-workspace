# Reference rapide — Commandes CX

## CLI unifiee : `python cx.py <commande>`

### Systeme
```bash
python cx.py system ram              # Memoire disponible
python cx.py system disk             # Espace disque
python cx.py system all              # Tout
python cx.py check                   # Diagnostic complet
```

### Desktop Windows
```bash
python cx.py desktop list_windows    # Fenetres ouvertes
python cx.py desktop focus Chrome    # Focus une fenetre
python cx.py desktop screenshot      # Capture d'ecran
python cx.py desktop clipboard_read  # Lire presse-papiers
python cx.py desktop screen_info     # Resolution, curseur
python cx.py desktop minimize Codex  # Minimiser fenetre
```

### Web
```bash
python cx.py search "python tutorial"    # Recherche DuckDuckGo
python cx.py search "paris" --instant    # Reponse instantanee
python cx.py fetch https://example.com   # Telecharger page
python cx.py fetch https://... -o f.html # Sauvegarder
```

### Documents
```bash
python cx.py info rapport.pdf            # Metadonnees PDF
python cx.py read rapport.pdf            # Lire le texte
python cx.py read rapport.pdf --pages 1-3 # Pages specifiques
python cx.py read data.xlsx --sheet Ventes # Feuille Excel
python cx.py convert data.csv xlsx       # Convertir
```

### Projet
```bash
python cx.py scaffold mon_app --lang python  # Nouveau projet Python
python cx.py scaffold site --lang web        # Nouveau site web
python cx.py scaffold api --lang node        # Nouveau projet Node
```

### Git
```bash
python cx.py git status              # Statut rapide
python cx.py git save "message"      # Add + commit
python cx.py git log                 # Derniers commits
python cx.py git changelog           # Generer CHANGELOG.md
python cx.py git diff                # Voir les changements
```

### Notion
```bash
python cx.py notion search "projet"  # Chercher dans Notion
```

### Maintenance
```bash
python cx.py deps                    # Installer dependances manquantes
python cx.py check                   # Diagnostic complet
```
