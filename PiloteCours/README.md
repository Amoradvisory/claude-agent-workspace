# PiloteCours

> Application Android hors ligne de pilotage de séance pour enseignant débutant.

PiloteCours sert de repère discret pendant le cours : l’étape du moment, les formulations utiles et les recadrages restent accessibles en quelques secondes sur un téléphone Android.

## Preuve publique

- [Mini–case study : problème, décisions, sécurité, limites et prochaine expérimentation](./CASE_STUDY.md)
- [Code de l’application](./app/src/main/java/com/pilotecours/app)
- [Configuration Android](./app/build.gradle.kts)

## Fonctionnalités vérifiables

- huit écrans : accueil, avant d’entrer, trois phases de séance, recadrages, mode discret et fin de séance ;
- contenu embarqué et fonctionnement sans backend ;
- accès permanent aux recadrages ;
- trois tailles de texte ;
- mémorisation locale du dernier écran, des favoris et de la taille du texte ;
- navigation précédent/suivant entre les phases ;
- thème sombre, portrait et grands contrôles tactiles.

## Garde-fou données

L’application ne demande aucune donnée d’élève et n’utilise ni compte, ni cloud, ni authentification. Seules des préférences d’interface sont conservées localement avec DataStore.

## Stack

- Kotlin ;
- Jetpack Compose ;
- Material 3 ;
- Navigation Compose ;
- DataStore Preferences ;
- Android `minSdk 26`, `targetSdk 36`.

## Ouvrir le projet

Prérequis :

- Android Studio récent ;
- JDK 17 ;
- Android SDK 36.

Étapes :

1. ouvrir Android Studio ;
2. choisir **File → Open** ;
3. sélectionner le dossier `PiloteCours/` ;
4. attendre la synchronisation Gradle.

## Construire un APK de debug

Depuis Android Studio : **Build → Build Bundle(s) / APK(s) → Build APK(s)**.

Depuis un terminal, si le Gradle Wrapper est disponible :

```bash
./gradlew assembleDebug
```

L’APK est alors attendu dans `app/build/outputs/apk/debug/app-debug.apk`.

## Structure

```text
PiloteCours/
├── app/
│   ├── build.gradle.kts
│   └── src/main/
│       ├── AndroidManifest.xml
│       └── java/com/pilotecours/app/
│           ├── MainActivity.kt
│           ├── data/PreferencesManager.kt
│           ├── navigation/Navigation.kt
│           └── ui/
│               ├── components/
│               ├── screens/
│               └── theme/
├── build.gradle.kts
├── settings.gradle.kts
└── CASE_STUDY.md
```

## État de validation

Le code source et sa configuration ont été inspectés lors de la mission ENSEIGNANT IA EXPERT du 11 août 2026. La compilation Android, les tests sur appareil et la publication d’un APK n’ont pas été exécutés pendant cette mission ; ils restent la prochaine étape de preuve.
