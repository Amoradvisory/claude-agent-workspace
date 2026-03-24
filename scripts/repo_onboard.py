"""
Repo Onboarding — Detection automatique de stack, entrypoints, conventions.
Usage:
  python scripts/repo_onboard.py [<path>]              # Analyse le repo courant ou specifie
  python scripts/repo_onboard.py scan [<path>]         # Scan complet
  python scripts/repo_onboard.py quick [<path>]        # Resume rapide
  python scripts/repo_onboard.py commands [<path>]     # Commandes utiles detectees

Detecte automatiquement :
  - Langages et frameworks (Python/Node/Go/Rust/Java/Ruby/PHP/.NET/Web)
  - Package managers et dependances
  - Points d'entree (main, index, app, server...)
  - Scripts de build, test, lint, dev
  - CI/CD (GitHub Actions, GitLab CI, Jenkins, CircleCI)
  - Docker / Docker Compose
  - Conventions (monorepo, tests, docs, config)
"""
import sys
import os
import json
import glob
import re
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import safe, log_info

# ============= DETECTORS =============

def _exists(root, *paths):
    """Check if any of the paths exist."""
    for p in paths:
        full = os.path.join(root, p)
        if os.path.exists(full):
            return full
        # Try glob
        matches = glob.glob(os.path.join(root, p))
        if matches:
            return matches[0]
    return None

def _read_json(path):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return json.load(f)
    except Exception:
        return {}

def _read_text(path, max_lines=50):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read(5000)
    except Exception:
        return ""

def _count_files(root, pattern):
    return len(glob.glob(os.path.join(root, "**", pattern), recursive=True))


def detect_stack(root):
    """Detecte la stack technologique."""
    stack = {
        "languages": [],
        "frameworks": [],
        "package_managers": [],
        "databases": [],
        "ci_cd": [],
        "containers": [],
        "other": [],
    }

    # === PYTHON ===
    if _exists(root, "requirements.txt", "setup.py", "pyproject.toml", "Pipfile", "setup.cfg"):
        stack["languages"].append("Python")
        if _exists(root, "Pipfile"):
            stack["package_managers"].append("pipenv")
        if _exists(root, "pyproject.toml"):
            toml = _read_text(_exists(root, "pyproject.toml"))
            if "poetry" in toml:
                stack["package_managers"].append("poetry")
            if "hatch" in toml:
                stack["package_managers"].append("hatch")
            stack["package_managers"].append("pip/pyproject")
        if _exists(root, "requirements.txt"):
            stack["package_managers"].append("pip")
        # Frameworks
        for dep_file in ["requirements.txt", "pyproject.toml", "setup.py"]:
            path = _exists(root, dep_file)
            if path:
                content = _read_text(path)
                if "django" in content.lower():
                    stack["frameworks"].append("Django")
                if "flask" in content.lower():
                    stack["frameworks"].append("Flask")
                if "fastapi" in content.lower():
                    stack["frameworks"].append("FastAPI")
                if "celery" in content.lower():
                    stack["other"].append("Celery")
                if "sqlalchemy" in content.lower():
                    stack["databases"].append("SQLAlchemy")
                if "pytest" in content.lower():
                    stack["other"].append("pytest")

    # === NODE.JS ===
    if _exists(root, "package.json"):
        stack["languages"].append("JavaScript/TypeScript")
        pkg = _read_json(_exists(root, "package.json"))
        deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}

        if _exists(root, "yarn.lock"):
            stack["package_managers"].append("yarn")
        elif _exists(root, "pnpm-lock.yaml"):
            stack["package_managers"].append("pnpm")
        elif _exists(root, "bun.lockb"):
            stack["package_managers"].append("bun")
        else:
            stack["package_managers"].append("npm")

        if "next" in deps:
            stack["frameworks"].append("Next.js")
        if "react" in deps:
            stack["frameworks"].append("React")
        if "vue" in deps:
            stack["frameworks"].append("Vue.js")
        if "svelte" in deps:
            stack["frameworks"].append("Svelte")
        if "express" in deps:
            stack["frameworks"].append("Express")
        if "nestjs" in str(deps):
            stack["frameworks"].append("NestJS")
        if "typescript" in deps:
            stack["languages"][-1] = "TypeScript"
        if "prisma" in str(deps):
            stack["databases"].append("Prisma")
        if "jest" in deps or "@jest" in str(deps):
            stack["other"].append("Jest")
        if "vitest" in deps:
            stack["other"].append("Vitest")
        if "eslint" in deps:
            stack["other"].append("ESLint")
        if "prettier" in deps:
            stack["other"].append("Prettier")

    # === GO ===
    if _exists(root, "go.mod"):
        stack["languages"].append("Go")
        stack["package_managers"].append("go modules")

    # === RUST ===
    if _exists(root, "Cargo.toml"):
        stack["languages"].append("Rust")
        stack["package_managers"].append("cargo")

    # === JAVA ===
    if _exists(root, "pom.xml"):
        stack["languages"].append("Java")
        stack["package_managers"].append("Maven")
    if _exists(root, "build.gradle", "build.gradle.kts"):
        if "Java" not in stack["languages"]:
            stack["languages"].append("Java/Kotlin")
        stack["package_managers"].append("Gradle")

    # === RUBY ===
    if _exists(root, "Gemfile"):
        stack["languages"].append("Ruby")
        stack["package_managers"].append("Bundler")
        gemfile = _read_text(_exists(root, "Gemfile"))
        if "rails" in gemfile.lower():
            stack["frameworks"].append("Rails")

    # === PHP ===
    if _exists(root, "composer.json"):
        stack["languages"].append("PHP")
        stack["package_managers"].append("Composer")
        composer = _read_text(_exists(root, "composer.json"))
        if "laravel" in composer.lower():
            stack["frameworks"].append("Laravel")

    # === .NET ===
    if _exists(root, "*.csproj", "*.sln"):
        stack["languages"].append("C#/.NET")
        stack["package_managers"].append("NuGet")

    # === CI/CD ===
    if _exists(root, ".github/workflows"):
        stack["ci_cd"].append("GitHub Actions")
    if _exists(root, ".gitlab-ci.yml"):
        stack["ci_cd"].append("GitLab CI")
    if _exists(root, "Jenkinsfile"):
        stack["ci_cd"].append("Jenkins")
    if _exists(root, ".circleci"):
        stack["ci_cd"].append("CircleCI")
    if _exists(root, ".travis.yml"):
        stack["ci_cd"].append("Travis CI")

    # === Containers ===
    if _exists(root, "Dockerfile"):
        stack["containers"].append("Docker")
    if _exists(root, "docker-compose.yml", "docker-compose.yaml", "compose.yml"):
        stack["containers"].append("Docker Compose")
    if _exists(root, "*.k8s.yml", "k8s/", "kubernetes/"):
        stack["containers"].append("Kubernetes")

    # === Databases ===
    if _exists(root, "*.db", "*.sqlite", "*.sqlite3"):
        stack["databases"].append("SQLite")
    if _exists(root, "prisma/schema.prisma"):
        if "Prisma" not in stack["databases"]:
            stack["databases"].append("Prisma")

    return stack


def detect_entrypoints(root):
    """Detecte les points d'entree."""
    entries = []
    candidates = [
        "main.py", "app.py", "server.py", "index.py", "manage.py", "wsgi.py", "asgi.py",
        "src/main.py", "src/app.py", "src/index.py",
        "index.js", "index.ts", "app.js", "app.ts", "server.js", "server.ts",
        "src/index.js", "src/index.ts", "src/main.ts", "src/app.ts",
        "main.go", "cmd/main.go", "src/main.rs",
        "Program.cs", "Startup.cs",
    ]

    for c in candidates:
        path = _exists(root, c)
        if path:
            entries.append(os.path.relpath(path, root))

    # package.json main/bin
    pkg_path = _exists(root, "package.json")
    if pkg_path:
        pkg = _read_json(pkg_path)
        if pkg.get("main"):
            entries.append(f"[package.json main] {pkg['main']}")
        if pkg.get("bin"):
            entries.append(f"[package.json bin] {pkg['bin']}")

    return entries


def detect_commands(root):
    """Detecte les commandes utiles."""
    commands = {}

    # package.json scripts
    pkg_path = _exists(root, "package.json")
    if pkg_path:
        pkg = _read_json(pkg_path)
        scripts = pkg.get("scripts", {})
        pm = "yarn" if _exists(root, "yarn.lock") else "pnpm" if _exists(root, "pnpm-lock.yaml") else "npm"
        for name, cmd in scripts.items():
            prefix = f"{pm} run " if pm != "npm" else f"npm run "
            if name in ("start", "dev", "test", "build", "lint"):
                prefix = f"{pm} " if name in ("start", "test") and pm == "npm" else prefix
            commands[f"{prefix}{name}"] = cmd[:80]

    # Makefile
    if _exists(root, "Makefile"):
        content = _read_text(_exists(root, "Makefile"))
        targets = re.findall(r"^([a-zA-Z_][\w-]*)\s*:", content, re.MULTILINE)
        for t in targets[:20]:
            if not t.startswith("."):
                commands[f"make {t}"] = ""

    # Python
    if _exists(root, "manage.py"):
        commands["python manage.py runserver"] = "Django dev server"
        commands["python manage.py test"] = "Django tests"
        commands["python manage.py migrate"] = "Django migrations"

    if _exists(root, "pyproject.toml"):
        toml = _read_text(_exists(root, "pyproject.toml"))
        if "pytest" in toml:
            commands["pytest"] = "Run tests"
        if "[tool.ruff]" in toml or "ruff" in toml:
            commands["ruff check ."] = "Lint"

    if _exists(root, "tox.ini"):
        commands["tox"] = "Run test environments"

    # Go
    if _exists(root, "go.mod"):
        commands["go build ./..."] = "Build"
        commands["go test ./..."] = "Tests"
        commands["go vet ./..."] = "Lint"

    # Rust
    if _exists(root, "Cargo.toml"):
        commands["cargo build"] = "Build"
        commands["cargo test"] = "Tests"
        commands["cargo clippy"] = "Lint"

    # Docker
    if _exists(root, "docker-compose.yml", "docker-compose.yaml", "compose.yml"):
        commands["docker compose up"] = "Start services"
        commands["docker compose down"] = "Stop services"

    return commands


def detect_structure(root):
    """Analyse la structure du projet."""
    info = {
        "total_files": 0,
        "total_dirs": 0,
        "top_dirs": [],
        "has_tests": False,
        "has_docs": False,
        "has_ci": False,
        "has_docker": False,
        "is_monorepo": False,
        "readme": None,
        "license": None,
        "config_files": [],
    }

    # Top-level dirs
    for item in sorted(os.listdir(root)):
        full = os.path.join(root, item)
        if os.path.isdir(full) and not item.startswith(".") and item not in ("node_modules", "__pycache__", ".git", "venv", ".venv"):
            info["top_dirs"].append(item)
            info["total_dirs"] += 1

    # File counts (quick)
    for _, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in (".git", "node_modules", "__pycache__", "venv", ".venv", ".next", "dist", "build")]
        info["total_files"] += len(files)
        info["total_dirs"] += len(dirs)

    info["has_tests"] = bool(_exists(root, "tests/", "test/", "__tests__/", "spec/", "*_test.go"))
    info["has_docs"] = bool(_exists(root, "docs/", "doc/", "documentation/"))
    info["has_ci"] = bool(_exists(root, ".github/workflows", ".gitlab-ci.yml", "Jenkinsfile"))
    info["has_docker"] = bool(_exists(root, "Dockerfile"))
    info["is_monorepo"] = bool(_exists(root, "packages/", "apps/", "lerna.json", "pnpm-workspace.yaml", "turbo.json"))
    info["readme"] = _exists(root, "README.md", "README.rst", "README.txt", "readme.md")
    info["license"] = _exists(root, "LICENSE", "LICENSE.md", "LICENCE")

    # Config files
    config_files = [".eslintrc*", ".prettierrc*", "tsconfig.json", ".editorconfig",
                    "ruff.toml", "mypy.ini", ".flake8", "tox.ini", "jest.config*",
                    "vitest.config*", "webpack.config*", "vite.config*", "next.config*"]
    for pat in config_files:
        found = glob.glob(os.path.join(root, pat))
        info["config_files"].extend(os.path.basename(f) for f in found)

    return info


@safe
def onboard(root, quick=False):
    """Analyse complete du repo."""
    root = os.path.abspath(root)
    print(f"\n{'='*60}")
    print(f"  REPO ONBOARDING: {os.path.basename(root)}")
    print(f"  {root}")
    print(f"{'='*60}\n")

    # 1. Stack
    stack = detect_stack(root)
    print("  [1] STACK DETECTEE\n")
    for category, items in stack.items():
        if items:
            print(f"  {category:18s}: {', '.join(items)}")
    if not any(stack.values()):
        print("  Aucune stack reconnue.")

    # 2. Structure
    structure = detect_structure(root)
    print(f"\n  [2] STRUCTURE\n")
    print(f"  Fichiers  : {structure['total_files']:,}")
    print(f"  Dossiers  : {structure['total_dirs']:,}")
    print(f"  Top dirs  : {', '.join(structure['top_dirs'][:15])}")
    badges = []
    if structure["has_tests"]: badges.append("tests")
    if structure["has_docs"]: badges.append("docs")
    if structure["has_ci"]: badges.append("CI/CD")
    if structure["has_docker"]: badges.append("Docker")
    if structure["is_monorepo"]: badges.append("MONOREPO")
    if structure["readme"]: badges.append("README")
    if structure["license"]: badges.append("LICENSE")
    if badges:
        print(f"  Presence  : {' | '.join(badges)}")
    if structure["config_files"]:
        print(f"  Configs   : {', '.join(structure['config_files'][:10])}")

    if quick:
        return

    # 3. Entrypoints
    entries = detect_entrypoints(root)
    print(f"\n  [3] POINTS D'ENTREE ({len(entries)})\n")
    for e in entries:
        print(f"  -> {e}")
    if not entries:
        print("  Aucun point d'entree standard detecte.")

    # 4. Commands
    commands = detect_commands(root)
    print(f"\n  [4] COMMANDES UTILES ({len(commands)})\n")
    for cmd, desc in commands.items():
        desc_str = f"  # {desc}" if desc else ""
        print(f"  $ {cmd}{desc_str}")
    if not commands:
        print("  Aucune commande detectee.")

    # 5. Git info
    print(f"\n  [5] GIT\n")
    import subprocess
    try:
        r = subprocess.run(["git", "log", "--oneline", "-5"], capture_output=True, text=True, cwd=root)
        if r.returncode == 0:
            print(f"  Derniers commits:")
            for line in r.stdout.strip().split("\n"):
                print(f"    {line}")
        r2 = subprocess.run(["git", "branch", "--show-current"], capture_output=True, text=True, cwd=root)
        if r2.returncode == 0:
            print(f"  Branche: {r2.stdout.strip()}")
        r3 = subprocess.run(["git", "remote", "-v"], capture_output=True, text=True, cwd=root)
        if r3.returncode == 0 and r3.stdout.strip():
            print(f"  Remote: {r3.stdout.strip().split(chr(10))[0]}")
    except Exception:
        print("  Git non disponible.")

    # 6. Quick README summary
    if structure.get("readme"):
        content = _read_text(structure["readme"])
        first_lines = content.strip().split("\n")[:10]
        print(f"\n  [6] README (apercu)\n")
        for l in first_lines:
            print(f"  {l}")

    print(f"\n{'='*60}")
    print(f"  Onboarding termine. {len(stack.get('languages',[]))} langage(s), {len(entries)} entrypoint(s), {len(commands)} commande(s).")
    print(f"{'='*60}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Repo Onboarding")
    parser.add_argument("action", nargs="?", default="scan", choices=["scan", "quick", "commands"])
    parser.add_argument("path", nargs="?", default=".")
    parsed = parser.parse_args()

    if parsed.action == "quick":
        onboard(parsed.path, quick=True)
    elif parsed.action == "commands":
        root = os.path.abspath(parsed.path)
        commands = detect_commands(root)
        print(f"\n=== Commandes: {os.path.basename(root)} ===\n")
        for cmd, desc in commands.items():
            print(f"  $ {cmd}  {'# '+desc if desc else ''}")
    else:
        onboard(parsed.path)
