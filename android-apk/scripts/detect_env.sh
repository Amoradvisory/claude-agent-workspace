#!/bin/bash
# Detect Android build environment
# Outputs: SDK_PATH, COMPILE_SDK, BUILD_TOOLS, GRADLE_BIN

set -e

# --- Android SDK ---
SDK_PATH=""
for candidate in \
    "$LOCALAPPDATA/Android/Sdk" \
    "$HOME/AppData/Local/Android/Sdk" \
    "C:/Users/user/AppData/Local/Android/Sdk" \
    "$ANDROID_HOME" \
    "$ANDROID_SDK_ROOT"; do
    if [ -d "$candidate/platforms" ] 2>/dev/null; then
        SDK_PATH="$candidate"
        break
    fi
done

if [ -z "$SDK_PATH" ]; then
    echo "ERROR: Android SDK not found"
    exit 1
fi
echo "SDK_PATH=$SDK_PATH"

# --- Detect highest compileSdk ---
COMPILE_SDK=0
for dir in "$SDK_PATH/platforms"/android-*; do
    if [ -d "$dir" ]; then
        level=$(basename "$dir" | sed 's/android-//' | sed 's/\..*//')
        if [ "$level" -gt "$COMPILE_SDK" ] 2>/dev/null; then
            COMPILE_SDK=$level
        fi
    fi
done
echo "COMPILE_SDK=$COMPILE_SDK"

# --- Detect build-tools ---
BUILD_TOOLS=$(ls "$SDK_PATH/build-tools/" 2>/dev/null | sort -V | tail -1)
echo "BUILD_TOOLS=$BUILD_TOOLS"

# --- Find cached Gradle binary ---
GRADLE_BIN=""

# Check PATH first
if command -v gradle &>/dev/null; then
    GRADLE_BIN=$(command -v gradle)
else
    # Search cached distributions
    for dist_dir in "$HOME/.gradle/wrapper/dists"/gradle-*/; do
        found=$(find "$dist_dir" -name "gradle" -o -name "gradle.bat" 2>/dev/null | head -1)
        if [ -n "$found" ]; then
            GRADLE_BIN="$found"
            break
        fi
    done
fi

if [ -n "$GRADLE_BIN" ]; then
    echo "GRADLE_BIN=$GRADLE_BIN"
else
    echo "GRADLE_BIN=NOT_FOUND"
fi

# --- Java ---
JAVA_PATH=$(which java 2>/dev/null || echo "NOT_FOUND")
echo "JAVA_PATH=$JAVA_PATH"

if [ "$JAVA_PATH" != "NOT_FOUND" ]; then
    JAVA_VERSION=$(java -version 2>&1 | head -1)
    echo "JAVA_VERSION=$JAVA_VERSION"
fi

echo "---"
echo "Environment detection complete."
