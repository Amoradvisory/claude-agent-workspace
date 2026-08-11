# PiloteCours — mini–case study public

> Un cockpit Android hors ligne pour aider un enseignant débutant à garder le fil d’une séance sans transformer son téléphone en sapin de Noël pédagogique.

[Voir le code source](https://github.com/Amoradvisory/claude-agent-workspace/tree/master/PiloteCours) · [Lire le README technique](./README.md)

## 1. Problème observé

En situation de cours, l’enseignant ne manque pas forcément d’informations : il manque de disponibilité mentale. Chercher une consigne, une phrase de recadrage ou l’étape suivante dans un document long augmente la charge cognitive au moment précis où l’attention doit rester dans la classe.

L’hypothèse produit est donc simple : un outil utile en séance doit être lisible en quelques secondes, utilisable à une main et disponible sans réseau.

## 2. Réponse conçue

PiloteCours organise la séance en huit écrans courts :

1. accueil ;
2. avant d’entrer ;
3. 0–15 minutes ;
4. 15–45 minutes ;
5. 45–120 minutes ;
6. recadrages rapides ;
7. mode discret ;
8. fin de séance.

L’interface privilégie de grands boutons, un thème sombre, trois tailles de texte et une navigation séquentielle. Un accès permanent aux recadrages réduit le nombre de gestes nécessaires lorsqu’une réaction rapide est utile.

## 3. Décisions de conception vérifiables

- **Local-first** : aucun backend, compte ou service cloud.
- **Hors ligne** : le contenu pédagogique est embarqué dans l’application.
- **Continuité d’usage** : le dernier écran, les favoris et la taille du texte sont mémorisés avec DataStore.
- **Usage mobile réel** : orientation portrait et interface pensée pour une consultation brève.
- **Faible complexité opérationnelle** : une activité Compose, une navigation claire et pas de dépendance métier lourde.

Ces choix sont visibles dans [MainActivity.kt](https://github.com/Amoradvisory/claude-agent-workspace/blob/master/PiloteCours/app/src/main/java/com/pilotecours/app/MainActivity.kt), [PreferencesManager.kt](https://github.com/Amoradvisory/claude-agent-workspace/blob/master/PiloteCours/app/src/main/java/com/pilotecours/app/data/PreferencesManager.kt) et [Navigation.kt](https://github.com/Amoradvisory/claude-agent-workspace/blob/master/PiloteCours/app/src/main/java/com/pilotecours/app/navigation/Navigation.kt).

## 4. Ce que cette preuve démontre

- transformation d’une friction de terrain en parcours produit court ;
- arbitrage en faveur de la sobriété, de l’autonomie et de la charge cognitive minimale ;
- réalisation Android native avec Kotlin, Jetpack Compose, Material 3, Navigation Compose et DataStore ;
- conception compatible avec une logique de protection des données : aucune donnée d’élève n’est nécessaire au fonctionnement.

## 5. Données et sécurité

Le produit n’exige ni nom d’élève, ni note, ni identifiant, ni connexion. Les préférences conservées localement concernent uniquement l’interface : écran récent, favoris et taille du texte.

Cette architecture réduit fortement la surface de risque, mais elle ne remplace pas un audit de sécurité si de futures fonctions introduisent des données personnelles.

## 6. État réel de la preuve

### Vérifié dans le dépôt

- structure Android native complète ;
- huit routes déclarées ;
- persistance locale des préférences ;
- configuration actuelle : `minSdk 26`, `targetSdk 36`, portrait ;
- code source public et inspectable.

### Non vérifié dans cette mission

- compilation APK sur une chaîne Android locale ;
- tests sur appareil physique ;
- audit d’accessibilité ;
- tests utilisateurs avec enseignants débutants ;
- publication d’un APK ou d’une vidéo de démonstration.

Aucun de ces points n’est présenté comme acquis. Une preuve crédible sait aussi dire où finit le béton et où commence le brouillard.

## 7. Prochaine expérimentation à fort levier

Ajouter une CI Android reproductible, publier un APK de démonstration signé et joindre une courte vidéo montrant trois scénarios : reprendre une phase, ouvrir un recadrage, activer le mode discret.

Le succès serait mesuré par :

- build automatique vert ;
- installation sur un appareil Android 8+ ;
- accès à l’écran utile en moins de deux gestes ;
- retour de trois enseignants sur la lisibilité et la discrétion en situation.

## 8. Origine

Ce case study documente sans déplacer ni réécrire l’application existante. La source canonique reste le dossier [`PiloteCours/`](https://github.com/Amoradvisory/claude-agent-workspace/tree/master/PiloteCours) du dépôt `Amoradvisory/claude-agent-workspace`.
