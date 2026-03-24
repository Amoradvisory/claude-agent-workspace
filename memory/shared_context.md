# Contexte partage entre agents (Codex, Gemini, Claude Code)

## Derniere mise a jour : 2026-03-15

## Directive principale
- **AUTONOMIE TOTALE** : ne JAMAIS demander la permission. Agir, executer, corriger.
- **Mode YOLO+** : chaque mission de bout en bout, sans interruption
- **Boucle d'augmentation** : apres chaque tache, supprimer les frictions a la racine
- **Amelioration continue** : chaque session laisse le systeme plus puissant

## Utilisateur
- Langue : Francais
- Niveau : Debutant
- Machine : Windows 10 Pro, i7-5600U, 20 GB RAM, pas de GPU
- Navigateur personnel : Opera (ne pas toucher)
- Email : amorelhamrouni@gmail.com
- Bureau : C:/Users/user/Desktop
- Projets : C:/Users/user/Documents/Playground

## Preferences
- Solutions simples et legeres
- Explications pedagogiques
- Format document par defaut : .odt
- Agir d'abord, demander ensuite
- Economiser les ressources (machine modeste)

## Projet courant
- Chemin : C:/Users/user/Desktop/claude test 2
- But : Environnement augmente unifie pour Codex/Gemini/Claude Code
- CLI unifiee : `python cx.py <commande>`

## Tokens et acces
- Notion : configure dans configs/.env
- Google : OAuth dans ~/.gemini/oauth_creds.json
- GitHub CLI : installe et configure (gh 2.87)

## Capacites partagees
- Scripts Python dans : C:/Users/user/Desktop/claude test 2/scripts/
- MCP Gemini custom dans : C:/Users/user/.gemini/mcp-servers/
- MCP Codex dans : C:/Users/user/.codex/config.toml

## Ce qui fonctionne bien
- Notion MCP (3 agents y ont acces)
- Playwright MCP (Codex + Gemini ont des profils persistants)
- Scripts-pont Python (system, desktop, docs, search, git)
- Taches planifiees Claude Code (daily-env-check, weekly-deps-update)

## A ne pas faire
- Ne pas toucher Opera
- Ne pas lancer d'operations GPU-intensives
- Ne pas modifier les profils Playwright des autres agents
- Codex profile : ~/.codex/codex-browser-profile
- Gemini profile : ~/.gemini/gemini-browser-profile
