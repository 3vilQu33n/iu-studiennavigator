# db_gateway.py
from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from contextlib import closing
from datetime import date
import logging

# ------------------------------------------------------------
# Optional: Prüfungs-Schema beim Start/Connect sicherstellen
# ------------------------------------------------------------
try:
    # Option C: Schema der Prüfungen beim Start sicherstellen (idempotent)
    from models.pruefung import init_pruefung_schema  # type: ignore
except Exception:  # Modul fehlt oder Importfehler -> ignorieren
    init_pruefung_schema = None  # Fallback: tut nichts, falls Modul fehlt

# ------------------------------------------------------------
# Logging
# ------------------------------------------------------------
logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(name)s: %(message)s')


# ------------------------------------------------------------
# Fehlerklasse
# ------------------------------------------------------------
class DBError(RuntimeError):
    """Datenbankbezogener Fehler im Gateway."""


# ------------------------------------------------------------
# Pfad-Auflösung (respektiert APP_DB_PATH) – stabil für Tests
# ------------------------------------------------------------

def _resolve_db_path() -> Path:
    """Ermittle den Pfad zur SQLite-Datei.

    Respektiert mehrere mögliche Umgebungsvariablen (robust gegen Tippfehler):
    - APP_DB_PATH   (bevorzugt)
    - APP DB PATH   (historischer/tippfehlerhafter Name mit Leerzeichen)
    - APP_DB
    - DB_PATH

    Gibt immer einen absolut/normalisierten Pfad zurück, damit Vergleiche in
    Tests stabil sind (z.B. bzgl. /private/var… vs. /var… auf macOS).
    """
    env_candidates = ("APP_DB_PATH", "APP DB PATH", "APP_DB", "DB_PATH")
    for key in env_candidates:
        env_val = os.getenv(key)
        if env_val:
            try:
                p = Path(env_val).expanduser().resolve()
                logger.debug("DB path from %s -> %s", key, p)
                return p
            except Exception as e:
                logger.warning("Ignoriere ungültigen %s=%r (%s)", key, env_val, e)

    # ✅ KORRIGIERT: Fallback: dashboard.db im PROJEKT-ROOT (nicht in repositories/)
    # __file__ = .../repositories/db_gateway.py
    # parent = .../repositories/
    # parent.parent = .../dashboardProject/
    project_root = Path(__file__).parent.parent
    p = (project_root / "dashboard.db").resolve()

    logger.debug("DB path fallback -> %s", p)
    if not p.exists():
        logger.warning("dashboard.db nicht gefunden in: %s", p)

    return p


# Öffentlicher, in Tests benutzter Pfad
DB_PATH: Path = _resolve_db_path()


# ------------------------------------------------------------
# Verbindungs-Helfer
# ------------------------------------------------------------

def connect() -> sqlite3.Connection:
    """Erzeuge eine neue DB-Verbindung mit Foreign-Key-Checks u. Row-Factory.

    Ruft `init_pruefung_schema(conn)` auf, wenn das Prüfungsmodul verfügbar ist
    (idempotent), sodass abhängige Tabellen/FKs vorhanden sind.
    """
    try:
        con = sqlite3.connect(DB_PATH)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys = ON;")
        if init_pruefung_schema is not None:
            try:
                init_pruefung_schema(con)
            except Exception as e:  # Schema-Init soll Tests nicht abbrechen
                logger.warning("Init Prüfungs-Schema fehlgeschlagen (ignoriert): %s", e)
        return con
    except sqlite3.Error as e:
        logger.exception("Konnte Datenbank nicht öffnen: %s", e)
        raise DBError(str(e))


# Rückwärtskompatibler Name (einige Tests/Module nutzen _connect)
def _connect() -> sqlite3.Connection:
    return connect()


# ------------------------------------------------------------
# Optionales, OO-orientiertes Mini-Gateway (falls andernorts genutzt)
# ------------------------------------------------------------
class DBGateway:
    def __init__(self, db_path: os.PathLike | str | None = None):
        # Erlaubt overrides, standardmäßig der global aufgelöste DB_PATH
        self.db_path: Path = Path(db_path).expanduser().resolve() if db_path else DB_PATH

    def _execute(self, sql: str, params: tuple | list = ()) -> sqlite3.Cursor:
        with closing(sqlite3.connect(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("PRAGMA foreign_keys = ON;")
            if init_pruefung_schema is not None:
                try:
                    init_pruefung_schema(conn)
                except Exception as e:
                    logger.warning("Init Prüfungs-Schema fehlgeschlagen (ignoriert): %s", e)
            cur.execute(sql, params)
            conn.commit()
            return cur