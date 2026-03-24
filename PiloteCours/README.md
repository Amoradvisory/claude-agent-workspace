# Pilote Cours

Application Android de pilotage de cours pour enseignant debutant.
Cockpit de seance consultable en un coup d'oeil depuis un telephone Android.

## Fonctionnalites

- **8 ecrans** : Accueil, Avant d'entrer, 0-15 min, 15-45 min, 45-120 min, Recadrages rapides, Mode discret, Fin de seance
- **Tout le contenu embarque** : phrases de classe, recadrages, rappels de posture
- **Mode discret** : ecran ultra-epure pour consultation rapide
- **Recadrages rapides** : acces 1 clic, appui long = plein ecran
- **Bouton Urgence** : acces permanent aux recadrages depuis n'importe quel ecran
- **3 tailles de police** : normale, grande, tres grande
- **Memorisation** : dernier ecran consulte + favoris
- **Navigation sequentielle** : precedent/suivant entre les phases du cours
- **100% hors ligne** : aucune connexion requise
- **Mode sombre** : fond sombre, contraste eleve, lecture discrete

## Prerequis

- **Android Studio** Hedgehog (2023.1) ou plus recent
- **JDK 17** (inclus dans Android Studio)
- **Android SDK 34** (installe automatiquement par Android Studio)

## Ouverture du projet

1. Ouvrir Android Studio
2. File > Open
3. Selectionner le dossier `PiloteCours/`
4. Attendre la synchronisation Gradle (premiere fois : telechargement des dependances)

## Generer le Gradle Wrapper (si necessaire)

Si le projet n'a pas de `gradlew` :
1. Ouvrir un terminal dans le dossier du projet
2. Executer : `gradle wrapper --gradle-version 8.4`

Ou simplement ouvrir le projet dans Android Studio qui regenere le wrapper automatiquement.

## Build APK debug

### Depuis Android Studio
1. Menu Build > Build Bundle(s) / APK(s) > Build APK(s)
2. L'APK se trouve dans `app/build/outputs/apk/debug/app-debug.apk`

### Depuis le terminal
```bash
./gradlew assembleDebug
```
L'APK se trouve dans `app/build/outputs/apk/debug/app-debug.apk`

## Installation sur Android

### Via USB
1. Activer le mode developpeur sur le telephone (Parametres > A propos > tapoter 7x sur "Numero de build")
2. Activer le debogage USB
3. Brancher le telephone
4. Depuis Android Studio : Run > Run 'app'

### Via APK directement
1. Copier `app-debug.apk` sur le telephone
2. Ouvrir le fichier APK depuis un gestionnaire de fichiers
3. Autoriser l'installation depuis cette source si demande
4. Installer

## Structure de l'application

```
app/src/main/java/com/pilotecours/app/
├── MainActivity.kt              # Activite unique, navigation, preferences
├── data/
│   └── PreferencesManager.kt    # Persistance locale (DataStore)
├── navigation/
│   └── Navigation.kt            # Routes et ecrans
├── ui/
│   ├── components/
│   │   └── Components.kt        # Composants reutilisables (cartes, barres, dialogs)
│   ├── screens/
│   │   ├── HomeScreen.kt        # Ecran d'accueil / hub
│   │   ├── AvantEntrerScreen.kt # Posture avant le cours
│   │   ├── Phase0_15Screen.kt   # Entree + presentation
│   │   ├── Phase15_45Screen.kt  # Fonctionnement + reflexion
│   │   ├── Phase45_120Screen.kt # Coeur de seance
│   │   ├── RecadragesScreen.kt  # Phrases de recadrage (appui long = plein ecran)
│   │   ├── ModeDiscretScreen.kt # Mode ultra-epure
│   │   └── FinSeanceScreen.kt   # Conclusion
│   └── theme/
│       ├── Color.kt             # Palette sombre
│       ├── Theme.kt             # Theme Material 3
│       └── Type.kt              # Typographie
```

## Technologies

- Kotlin
- Jetpack Compose
- Material 3
- Navigation Compose
- DataStore Preferences
- Aucune dependance externe lourde
- Aucun backend / cloud / authentification

## Cible

- minSdk 26 (Android 8.0+)
- targetSdk 34
- Portrait uniquement
- Optimise pour usage a une main
