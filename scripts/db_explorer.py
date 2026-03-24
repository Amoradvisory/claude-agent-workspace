"""
Database Explorer — Exploration read-only de bases de donnees.
Supporte: SQLite (natif), PostgreSQL (psycopg2), MySQL (mysql-connector), MSSQL (pyodbc).
Strictement READ-ONLY — aucune mutation autorisee.

Usage:
  python scripts/db_explorer.py connect <path.db>                    # SQLite
  python scripts/db_explorer.py connect "postgresql://user:pass@host/db"  # PostgreSQL
  python scripts/db_explorer.py connect "mysql://user:pass@host/db"       # MySQL
  python scripts/db_explorer.py schema [<table>]                     # Schema complet ou d'une table
  python scripts/db_explorer.py tables                               # Lister les tables
  python scripts/db_explorer.py columns <table>                      # Colonnes d'une table
  python scripts/db_explorer.py indexes <table>                      # Index d'une table
  python scripts/db_explorer.py sample <table> [--rows 10]           # Echantillon de donnees
  python scripts/db_explorer.py count <table>                        # Nombre de lignes
  python scripts/db_explorer.py query "SELECT ..." [--limit 100]     # Requete SQL read-only
  python scripts/db_explorer.py explain "SELECT ..."                 # Plan d'execution
  python scripts/db_explorer.py relations [<table>]                  # Foreign keys / relations
  python scripts/db_explorer.py stats <table>                        # Statistiques colonnes
  python scripts/db_explorer.py diagnose                             # Diagnostic (tables sans PK, index manquants)
"""
import sys
import os
import re
import json
import sqlite3
import argparse
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import safe, log_info, log_error, CONFIGS_DIR

# Stocke la connexion active
_DB_CONFIG_FILE = os.path.join(CONFIGS_DIR, "db_connection.json")

# ============= MUTATION GUARD =============
FORBIDDEN_KEYWORDS = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|REPLACE|GRANT|REVOKE|"
    r"MERGE|EXEC|EXECUTE|CALL|SET|COMMIT|ROLLBACK|SAVEPOINT|LOCK|UNLOCK)\b",
    re.IGNORECASE
)

def _check_readonly(sql):
    """Refuse toute requete non-SELECT."""
    stripped = sql.strip().rstrip(";")
    # Remove comments
    stripped = re.sub(r"--.*$", "", stripped, flags=re.MULTILINE)
    stripped = re.sub(r"/\*.*?\*/", "", stripped, flags=re.DOTALL)

    if FORBIDDEN_KEYWORDS.search(stripped):
        raise PermissionError(f"[BLOQUE] Requete en mutation detectee. Mode READ-ONLY strictement applique.\n  SQL: {sql[:100]}")

    # Only allow SELECT, EXPLAIN, PRAGMA, SHOW, DESCRIBE, WITH
    first_word = stripped.split()[0].upper() if stripped.split() else ""
    allowed = ("SELECT", "EXPLAIN", "PRAGMA", "SHOW", "DESCRIBE", "DESC", "WITH", "ANALYZE")
    if first_word not in allowed:
        raise PermissionError(f"[BLOQUE] Seules les requetes en lecture sont autorisees (SELECT, EXPLAIN, PRAGMA, SHOW).\n  Detecte: {first_word}")

# ============= CONNECTION =============

class DBConnection:
    def __init__(self):
        self.conn = None
        self.db_type = None  # sqlite, postgresql, mysql
        self.db_path = None

    def connect(self, uri):
        """Connecte a la base."""
        if uri.endswith(".db") or uri.endswith(".sqlite") or uri.endswith(".sqlite3") or os.path.isfile(uri):
            return self._connect_sqlite(uri)
        elif uri.startswith("postgresql://") or uri.startswith("postgres://"):
            return self._connect_pg(uri)
        elif uri.startswith("mysql://"):
            return self._connect_mysql(uri)
        elif uri.startswith("mssql://") or uri.startswith("odbc://"):
            return self._connect_mssql(uri)
        else:
            # Try as SQLite path
            return self._connect_sqlite(uri)

    def _connect_sqlite(self, path):
        if not os.path.exists(path):
            print(f"[ERREUR] Fichier introuvable: {path}")
            return False
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        # Force read-only via PRAGMA
        self.conn.execute("PRAGMA query_only = ON")
        self.db_type = "sqlite"
        self.db_path = path
        size_kb = os.path.getsize(path) / 1024
        print(f"[OK] Connecte SQLite: {path} ({size_kb:.1f} KB)")
        self._save_config(path)
        return True

    def _connect_pg(self, uri):
        try:
            import psycopg2
        except ImportError:
            print("[!!] psycopg2 non installe. Installation...")
            os.system(f"{sys.executable} -m pip install psycopg2-binary -q")
            import psycopg2
        self.conn = psycopg2.connect(uri)
        self.conn.set_session(readonly=True, autocommit=True)
        self.db_type = "postgresql"
        self.db_path = uri
        print(f"[OK] Connecte PostgreSQL (read-only)")
        self._save_config(uri)
        return True

    def _connect_mysql(self, uri):
        try:
            import mysql.connector
        except ImportError:
            print("[!!] mysql-connector non installe. Installation...")
            os.system(f"{sys.executable} -m pip install mysql-connector-python -q")
            import mysql.connector
        # Parse URI: mysql://user:pass@host:port/db
        m = re.match(r"mysql://(\w+):(.+)@([\w.-]+)(?::(\d+))?/(\w+)", uri)
        if not m:
            print("[ERREUR] Format URI invalide: mysql://user:pass@host:port/db")
            return False
        self.conn = mysql.connector.connect(
            user=m.group(1), password=m.group(2),
            host=m.group(3), port=int(m.group(4) or 3306),
            database=m.group(5)
        )
        self.db_type = "mysql"
        self.db_path = uri
        print(f"[OK] Connecte MySQL (read-only enforce cote client)")
        self._save_config(uri)
        return True

    def _connect_mssql(self, uri):
        try:
            import pyodbc
        except ImportError:
            print("[!!] pyodbc non installe. Installez: pip install pyodbc")
            return False
        self.conn = pyodbc.connect(uri)
        self.db_type = "mssql"
        self.db_path = uri
        print(f"[OK] Connecte MSSQL (read-only enforce cote client)")
        self._save_config(uri)
        return True

    def _save_config(self, uri):
        os.makedirs(os.path.dirname(_DB_CONFIG_FILE) or ".", exist_ok=True)
        config = {"uri": uri, "type": self.db_type, "connected_at": datetime.now().isoformat()}
        with open(_DB_CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=2)

    def _load_last(self):
        """Reconnecte depuis la derniere config."""
        if self.conn:
            return True
        if os.path.exists(_DB_CONFIG_FILE):
            with open(_DB_CONFIG_FILE) as f:
                config = json.load(f)
            return self.connect(config["uri"])
        print("[ERREUR] Aucune connexion active. Utilisez: db connect <path_or_uri>")
        return False

    def execute(self, sql, params=None):
        """Execute une requete read-only."""
        _check_readonly(sql)
        if not self._load_last():
            return []
        cursor = self.conn.cursor()
        cursor.execute(sql, params or ())
        try:
            rows = cursor.fetchall()
            if self.db_type == "sqlite":
                cols = [d[0] for d in cursor.description] if cursor.description else []
                return [dict(zip(cols, row)) for row in rows]
            elif cursor.description:
                cols = [d[0] for d in cursor.description]
                return [dict(zip(cols, row)) for row in rows]
            return rows
        except Exception:
            return []


db = DBConnection()

# ============= COMMANDS =============

@safe
def cmd_connect(uri):
    if db.connect(uri):
        # Show quick info
        cmd_tables()

@safe
def cmd_tables():
    if not db._load_last(): return
    if db.db_type == "sqlite":
        rows = db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    elif db.db_type == "postgresql":
        rows = db.execute("SELECT table_name as name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name")
    elif db.db_type == "mysql":
        rows = db.execute("SHOW TABLES")
    else:
        rows = db.execute("SELECT TABLE_NAME as name FROM INFORMATION_SCHEMA.TABLES")

    print(f"\n=== Tables ({len(rows)}) ===\n")
    for r in rows:
        name = list(r.values())[0] if isinstance(r, dict) else r[0]
        # Count rows
        try:
            count = db.execute(f"SELECT COUNT(*) as n FROM \"{name}\"")[0].get("n", "?")
        except Exception:
            count = "?"
        print(f"  {name:40s}  {count:>10} lignes")

@safe
def cmd_columns(table):
    if not db._load_last(): return
    if db.db_type == "sqlite":
        rows = db.execute(f"PRAGMA table_info(\"{table}\")")
        print(f"\n=== Colonnes: {table} ({len(rows)}) ===\n")
        for r in rows:
            pk = " [PK]" if r.get("pk") else ""
            null = " NOT NULL" if r.get("notnull") else ""
            default = f" DEFAULT={r['dflt_value']}" if r.get("dflt_value") else ""
            print(f"  {r['name']:30s}  {r['type']:15s}{pk}{null}{default}")
    elif db.db_type == "postgresql":
        rows = db.execute(f"""SELECT column_name, data_type, is_nullable, column_default
                             FROM information_schema.columns
                             WHERE table_name = '{table}' ORDER BY ordinal_position""")
        print(f"\n=== Colonnes: {table} ({len(rows)}) ===\n")
        for r in rows:
            null = "" if r.get("is_nullable") == "YES" else " NOT NULL"
            default = f" DEFAULT={r['column_default']}" if r.get("column_default") else ""
            print(f"  {r['column_name']:30s}  {r['data_type']:15s}{null}{default}")
    else:
        rows = db.execute(f"DESCRIBE `{table}`")
        print(f"\n=== Colonnes: {table} ===\n")
        for r in rows:
            print(f"  {r}")

@safe
def cmd_indexes(table):
    if not db._load_last(): return
    if db.db_type == "sqlite":
        rows = db.execute(f"PRAGMA index_list(\"{table}\")")
        print(f"\n=== Index: {table} ({len(rows)}) ===\n")
        for idx in rows:
            name = idx.get("name", "?")
            unique = " [UNIQUE]" if idx.get("unique") else ""
            cols = db.execute(f"PRAGMA index_info(\"{name}\")")
            col_names = ", ".join(c.get("name", "?") for c in cols)
            print(f"  {name:30s}  ({col_names}){unique}")
    elif db.db_type == "postgresql":
        rows = db.execute(f"""SELECT indexname, indexdef FROM pg_indexes
                             WHERE tablename = '{table}'""")
        print(f"\n=== Index: {table} ({len(rows)}) ===\n")
        for r in rows:
            print(f"  {r.get('indexname', '?')}")
            print(f"    {r.get('indexdef', '')}")

@safe
def cmd_schema(table=None):
    if not db._load_last(): return
    if table:
        cmd_columns(table)
        cmd_indexes(table)
        return

    # Full schema dump
    if db.db_type == "sqlite":
        rows = db.execute("SELECT sql FROM sqlite_master WHERE sql IS NOT NULL ORDER BY type, name")
        print(f"\n=== Schema complet ===\n")
        for r in rows:
            print(r.get("sql", ""))
            print()

@safe
def cmd_sample(table, rows=10):
    if not db._load_last(): return
    data = db.execute(f"SELECT * FROM \"{table}\" LIMIT {rows}")
    if not data:
        print(f"[OK] Table '{table}' est vide.")
        return
    print(f"\n=== Echantillon: {table} ({rows} lignes) ===\n")
    # Format as table
    cols = list(data[0].keys())
    widths = {c: max(len(str(c)), max(len(str(r.get(c, "")))[:40] for r in data)) for c in cols}
    header = "  ".join(f"{c:{widths[c]}s}" for c in cols)
    print(f"  {header}")
    print(f"  {'-' * len(header)}")
    for row in data:
        line = "  ".join(f"{str(row.get(c,''))[:40]:{widths[c]}s}" for c in cols)
        print(f"  {line}")

@safe
def cmd_count(table):
    if not db._load_last(): return
    data = db.execute(f"SELECT COUNT(*) as n FROM \"{table}\"")
    n = data[0].get("n", "?") if data else "?"
    print(f"  {table}: {n:,} lignes" if isinstance(n, int) else f"  {table}: {n} lignes")

@safe
def cmd_query(sql, limit=100):
    """Execute une requete SQL read-only."""
    if not db._load_last(): return
    # Add LIMIT if not present
    if "LIMIT" not in sql.upper() and limit:
        sql = sql.rstrip(";") + f" LIMIT {limit}"

    try:
        data = db.execute(sql)
    except PermissionError as e:
        print(str(e))
        return

    if not data:
        print("[OK] Aucun resultat.")
        return

    cols = list(data[0].keys())
    print(f"\n  ({len(data)} ligne(s))\n")
    # Header
    widths = {}
    for c in cols:
        max_w = max(len(str(c)), max((len(str(r.get(c, ""))[:50]) for r in data[:50]), default=0))
        widths[c] = min(max_w, 50)
    header = "  ".join(f"{c:{widths[c]}s}" for c in cols)
    print(f"  {header}")
    print(f"  {'=' * len(header)}")
    for row in data:
        line = "  ".join(f"{str(row.get(c,''))[:50]:{widths[c]}s}" for c in cols)
        print(f"  {line}")

@safe
def cmd_explain(sql):
    """Plan d'execution."""
    if not db._load_last(): return
    _check_readonly(sql)

    if db.db_type == "sqlite":
        plan = db.execute(f"EXPLAIN QUERY PLAN {sql}")
    elif db.db_type == "postgresql":
        plan = db.execute(f"EXPLAIN ANALYZE {sql}")
    else:
        plan = db.execute(f"EXPLAIN {sql}")

    print(f"\n=== Plan d'execution ===\n")
    for row in plan:
        if isinstance(row, dict):
            vals = " | ".join(f"{v}" for v in row.values())
            print(f"  {vals}")
        else:
            print(f"  {row}")

@safe
def cmd_relations(table=None):
    """Foreign keys / relations."""
    if not db._load_last(): return

    if db.db_type == "sqlite":
        if table:
            fks = db.execute(f"PRAGMA foreign_key_list(\"{table}\")")
            print(f"\n=== Relations: {table} ({len(fks)} FK) ===\n")
            for fk in fks:
                print(f"  {table}.{fk.get('from','?')} -> {fk.get('table','?')}.{fk.get('to','?')}")
        else:
            tables = db.execute("SELECT name FROM sqlite_master WHERE type='table'")
            print(f"\n=== Toutes les relations ===\n")
            for t in tables:
                name = t.get("name", "")
                fks = db.execute(f"PRAGMA foreign_key_list(\"{name}\")")
                for fk in fks:
                    print(f"  {name}.{fk.get('from','?')} -> {fk.get('table','?')}.{fk.get('to','?')}")
    elif db.db_type == "postgresql":
        sql = """SELECT tc.table_name, kcu.column_name,
                        ccu.table_name AS foreign_table, ccu.column_name AS foreign_column
                 FROM information_schema.table_constraints tc
                 JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
                 JOIN information_schema.constraint_column_usage ccu ON tc.constraint_name = ccu.constraint_name
                 WHERE tc.constraint_type = 'FOREIGN KEY'"""
        if table:
            sql += f" AND tc.table_name = '{table}'"
        rows = db.execute(sql)
        print(f"\n=== Relations {'de ' + table if table else 'completes'} ({len(rows)} FK) ===\n")
        for r in rows:
            print(f"  {r['table_name']}.{r['column_name']} -> {r['foreign_table']}.{r['foreign_column']}")

@safe
def cmd_stats(table):
    """Statistiques par colonne."""
    if not db._load_last(): return
    if db.db_type == "sqlite":
        cols_info = db.execute(f"PRAGMA table_info(\"{table}\")")
    else:
        cmd_columns(table)
        return

    count_row = db.execute(f"SELECT COUNT(*) as n FROM \"{table}\"")
    total = count_row[0].get("n", 0) if count_row else 0

    print(f"\n=== Stats: {table} ({total} lignes) ===\n")
    for col_info in cols_info:
        name = col_info.get("name", "?")
        ctype = col_info.get("type", "?").upper()

        nulls = db.execute(f"SELECT COUNT(*) as n FROM \"{table}\" WHERE \"{name}\" IS NULL")[0].get("n", 0)
        distinct = db.execute(f"SELECT COUNT(DISTINCT \"{name}\") as n FROM \"{table}\"")[0].get("n", 0)

        line = f"  {name:25s}  type={ctype:12s}  distinct={distinct:8d}  nulls={nulls}"

        if ctype in ("INTEGER", "REAL", "FLOAT", "DOUBLE", "NUMERIC", "INT", "BIGINT"):
            stats = db.execute(f"SELECT MIN(\"{name}\") as mn, MAX(\"{name}\") as mx, AVG(\"{name}\") as av FROM \"{table}\"")
            if stats:
                s = stats[0]
                line += f"  min={s.get('mn','?')}  max={s.get('mx','?')}  avg={s.get('av','?')}"
        elif ctype in ("TEXT", "VARCHAR", "CHAR"):
            top = db.execute(f"SELECT \"{name}\", COUNT(*) as c FROM \"{table}\" WHERE \"{name}\" IS NOT NULL GROUP BY \"{name}\" ORDER BY c DESC LIMIT 3")
            if top:
                top_str = ", ".join(f"{r.get(name,'?')}({r.get('c',0)})" for r in top)
                line += f"  top=[{top_str}]"

        print(line)

@safe
def cmd_diagnose():
    """Diagnostic : tables sans PK, colonnes sans index, tables vides."""
    if not db._load_last(): return
    print(f"\n=== Diagnostic DB ({db.db_type}) ===\n")

    issues = []

    if db.db_type == "sqlite":
        tables = db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        for t in tables:
            name = t.get("name", "")
            if name.startswith("sqlite_"):
                continue

            # Check PK
            cols = db.execute(f"PRAGMA table_info(\"{name}\")")
            has_pk = any(c.get("pk", 0) for c in cols)
            if not has_pk:
                issues.append(f"  [!!] {name}: pas de cle primaire")

            # Check indexes
            indexes = db.execute(f"PRAGMA index_list(\"{name}\")")
            if not indexes and len(cols) > 3:
                issues.append(f"  [?]  {name}: aucun index ({len(cols)} colonnes)")

            # Check empty
            count = db.execute(f"SELECT COUNT(*) as n FROM \"{name}\"")[0].get("n", 0)
            if count == 0:
                issues.append(f"  [--] {name}: table vide")

            # Check wide tables
            if len(cols) > 20:
                issues.append(f"  [?]  {name}: {len(cols)} colonnes (table large)")

    if issues:
        print(f"  {len(issues)} probleme(s) detecte(s):\n")
        for issue in issues:
            print(issue)
    else:
        print("  [OK] Aucun probleme detecte.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DB Explorer — Read-Only")
    parser.add_argument("action", choices=[
        "connect", "tables", "columns", "indexes", "schema",
        "sample", "count", "query", "explain", "relations",
        "stats", "diagnose"
    ])
    parser.add_argument("args", nargs="*")
    parser.add_argument("--rows", type=int, default=10)
    parser.add_argument("--limit", type=int, default=100)
    parsed = parser.parse_args()

    action = parsed.action
    extra = parsed.args

    if action == "connect":
        if not extra:
            print("[ERREUR] URI ou chemin requis")
            sys.exit(1)
        cmd_connect(extra[0])
    elif action == "tables":
        cmd_tables()
    elif action == "columns" and extra:
        cmd_columns(extra[0])
    elif action == "indexes" and extra:
        cmd_indexes(extra[0])
    elif action == "schema":
        cmd_schema(extra[0] if extra else None)
    elif action == "sample" and extra:
        cmd_sample(extra[0], parsed.rows)
    elif action == "count" and extra:
        cmd_count(extra[0])
    elif action == "query" and extra:
        cmd_query(extra[0], parsed.limit)
    elif action == "explain" and extra:
        cmd_explain(extra[0])
    elif action == "relations":
        cmd_relations(extra[0] if extra else None)
    elif action == "stats" and extra:
        cmd_stats(extra[0])
    elif action == "diagnose":
        cmd_diagnose()
    else:
        parser.print_help()
