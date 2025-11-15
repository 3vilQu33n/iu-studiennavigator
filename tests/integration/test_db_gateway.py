# tests/integration/test_db_gateway.py
"""
Integration Tests für DB Gateway
Testet Datenbankoperationen mit echter SQLite-Datenbank
"""
from __future__ import annotations

import importlib
import sys
from pathlib import Path
import sqlite3
import pytest

# Mark this whole module as integration
pytestmark = pytest.mark.integration


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _reload_gateway_with_env(monkeypatch: pytest.MonkeyPatch, **env):
    """
    Re-import db_gateway mit neuen Umgebungsvariablen

    Damit wird DB_PATH neu berechnet für jeden Test

    Args:
        monkeypatch: pytest MonkeyPatch fixture
        **env: Umgebungsvariablen zum Setzen

    Returns:
        Importiertes db_gateway Modul
    """
    for k, v in env.items():
        if v is None:
            monkeypatch.delenv(k, raising=False)
            # Auch alte Schreibweisen entfernen
            if k == "APP_DB_PATH":
                monkeypatch.delenv("APP DB PATH", raising=False)
        else:
            monkeypatch.setenv(k, v)
            # Beide Schreibweisen setzen für Kompatibilität
            if k == "APP_DB_PATH":
                monkeypatch.setenv("APP DB PATH", v)

    # Fresh import erzwingen
    sys.modules.pop("repositories.db_gateway", None)
    sys.modules.pop("db_gateway", None)

    try:
        return importlib.import_module("repositories.db_gateway")
    except ModuleNotFoundError:
        return importlib.import_module("db_gateway")


# ============================================================================
# DB_PATH CONFIGURATION TESTS
# ============================================================================

def test_data_source_points_to_same_file(tmp_path, monkeypatch):
    """
    Test: APP_DB_PATH wird korrekt als DB_PATH verwendet
    """
    db_file = tmp_path / "test.db"
    gw = _reload_gateway_with_env(monkeypatch, APP_DB_PATH=str(db_file))

    left = Path(gw.DB_PATH).resolve()
    right = Path(db_file).resolve()

    assert left == right, f"DB_PATH mismatch: {left} != {right}"


def test_db_path_is_absolute(tmp_path, monkeypatch):
    """
    Test: DB_PATH ist immer ein absoluter Pfad
    """
    db_file = tmp_path / "test.db"
    gw = _reload_gateway_with_env(monkeypatch, APP_DB_PATH=str(db_file))

    db_path = Path(gw.DB_PATH)
    assert db_path.is_absolute(), "DB_PATH muss absolut sein"


# ============================================================================
# CONNECTION TESTS
# ============================================================================

def test_foreign_keys_enforced(tmp_path, monkeypatch):
    """
    Test: Foreign Keys sind aktiviert bei jeder Connection
    """
    db_file = tmp_path / "test.db"
    gw = _reload_gateway_with_env(monkeypatch, APP_DB_PATH=str(db_file))

    con = gw.connect()
    try:
        result = con.execute("PRAGMA foreign_keys;").fetchone()
        assert result[0] == 1, "Foreign Keys müssen aktiviert sein"
    finally:
        con.close()


def test_connection_has_row_factory(tmp_path, monkeypatch):
    """
    Test: Connection hat Row Factory für dict-ähnlichen Zugriff
    """
    db_file = tmp_path / "test.db"
    gw = _reload_gateway_with_env(monkeypatch, APP_DB_PATH=str(db_file))

    con = gw.connect()
    try:
        assert con.row_factory is not None, "Row Factory muss gesetzt sein"
    finally:
        con.close()


def test_multiple_connections(tmp_path, monkeypatch):
    """
    Test: Mehrere Connections können gleichzeitig erstellt werden
    """
    db_file = tmp_path / "test.db"
    gw = _reload_gateway_with_env(monkeypatch, APP_DB_PATH=str(db_file))

    con1 = gw.connect()
    con2 = gw.connect()

    try:
        # Beide Connections sollten funktionieren
        assert con1.execute("PRAGMA foreign_keys;").fetchone()[0] == 1
        assert con2.execute("PRAGMA foreign_keys;").fetchone()[0] == 1
    finally:
        con1.close()
        con2.close()


def test_backward_compatible_connect(tmp_path, monkeypatch):
    """
    Test: _connect() funktioniert als Alias für connect()
    """
    db_file = tmp_path / "test.db"
    gw = _reload_gateway_with_env(monkeypatch, APP_DB_PATH=str(db_file))

    # Prüfe ob _connect existiert
    if not hasattr(gw, '_connect'):
        pytest.skip("_connect() nicht vorhanden (optional)")

    con = gw._connect()
    try:
        assert con.execute("PRAGMA foreign_keys;").fetchone()[0] == 1
        assert con.row_factory is not None
    finally:
        con.close()


# ============================================================================
# DBGateway CLASS TESTS
# ============================================================================

def test_db_gateway_class_exists(tmp_path, monkeypatch):
    """
    Test: DBGateway Klasse existiert (optional)
    """
    db_file = tmp_path / "test.db"
    gw_module = _reload_gateway_with_env(monkeypatch, APP_DB_PATH=str(db_file))

    if not hasattr(gw_module, 'DBGateway'):
        pytest.skip("DBGateway Klasse nicht vorhanden (optional)")

    # Teste dass Klasse instantiiert werden kann
    gateway = gw_module.DBGateway()
    assert gateway is not None
    assert hasattr(gateway, 'db_path')


def test_db_gateway_class_default_path(tmp_path, monkeypatch):
    """
    Test: DBGateway Klasse verwendet Standard DB_PATH
    """
    db_file = tmp_path / "test.db"
    gw_module = _reload_gateway_with_env(monkeypatch, APP_DB_PATH=str(db_file))

    if not hasattr(gw_module, 'DBGateway'):
        pytest.skip("DBGateway Klasse nicht vorhanden (optional)")

    gateway = gw_module.DBGateway()
    assert str(gateway.db_path) == str(Path(gw_module.DB_PATH).resolve())


def test_db_gateway_class_custom_path(tmp_path, monkeypatch):
    """
    Test: DBGateway Klasse kann mit custom Path initialisiert werden
    """
    db_file = tmp_path / "test.db"
    gw_module = _reload_gateway_with_env(monkeypatch, APP_DB_PATH=str(db_file))

    if not hasattr(gw_module, 'DBGateway'):
        pytest.skip("DBGateway Klasse nicht vorhanden (optional)")

    custom_db = tmp_path / "custom.db"
    gateway = gw_module.DBGateway(custom_db)
    assert gateway.db_path == custom_db.resolve()


# ============================================================================
# SCHEMA TESTS
# ============================================================================

def test_can_create_table(tmp_path, monkeypatch):
    """
    Test: Tabellen können erstellt werden
    """
    db_file = tmp_path / "test.db"
    gw = _reload_gateway_with_env(monkeypatch, APP_DB_PATH=str(db_file))

    con = gw.connect()
    try:
        con.execute("""
                    CREATE TABLE IF NOT EXISTS test_table
                    (
                        id   INTEGER PRIMARY KEY,
                        name TEXT
                    );
                    """)
        con.commit()

        row = con.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='test_table'"
        ).fetchone()

        assert row is not None
        assert row[0] == "test_table"
    finally:
        con.close()


def test_schema_tables_exist(temp_db):
    """
    Test: Alle notwendigen Tabellen existieren in der Test-DB

    Verwendet temp_db Fixture aus conftest.py
    """
    con = sqlite3.connect(temp_db)

    try:
        # Liste erwarteter Tabellen
        expected_tables = [
            'login',
            'student',
            'studiengang',
            'modul',
            'zeitmodell',
            'studiengang_modul',
            'einschreibung',
            'modulbuchung',
            'pruefungsleistung',
            'gebuehr'
        ]

        cursor = con.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        existing_tables = [row[0] for row in cursor.fetchall()]

        for table in expected_tables:
            assert table in existing_tables, f"Tabelle {table} fehlt im Schema"

    finally:
        con.close()


def test_foreign_key_constraints_work(tmp_path, monkeypatch):
    """
    Test: Foreign Key Constraints werden tatsächlich durchgesetzt
    """
    db_file = tmp_path / "test.db"
    gw = _reload_gateway_with_env(monkeypatch, APP_DB_PATH=str(db_file))

    con = gw.connect()
    try:
        # Erstelle zwei Tabellen mit FK-Beziehung
        con.execute("""
                    CREATE TABLE parent
                    (
                        id   INTEGER PRIMARY KEY,
                        name TEXT
                    );
                    """)
        # noinspection SqlResolve
        con.execute("""
                    CREATE TABLE child
                    (
                        id        INTEGER PRIMARY KEY,
                        parent_id INTEGER,
                        FOREIGN KEY (parent_id) REFERENCES parent (id)
                    );
                    """)
        con.commit()

        # Versuche ungültigen FK einzufügen (sollte fehlschlagen)
        with pytest.raises(sqlite3.IntegrityError):
            # noinspection SqlResolve
            con.execute("INSERT INTO child (parent_id) VALUES (999)")
            con.commit()

    finally:
        con.close()


# ============================================================================
# EXCEPTION TESTS
# ============================================================================

def test_db_error_exception():
    """
    Test: DBError Exception kann geworfen und gefangen werden
    """
    try:
        from repositories.db_gateway import DBError
    except ImportError:
        try:
            from db_gateway import DBError
        except ImportError:
            pytest.skip("DBError nicht vorhanden (optional)")

    with pytest.raises(DBError):
        raise DBError("Test error")


def test_db_error_has_message():
    """
    Test: DBError hat Fehlermeldung
    """
    try:
        from repositories.db_gateway import DBError
    except ImportError:
        try:
            from db_gateway import DBError
        except ImportError:
            pytest.skip("DBError nicht vorhanden (optional)")

    error_msg = "Test error message"
    try:
        raise DBError(error_msg)
    except DBError as e:
        assert str(e) == error_msg


# ============================================================================
# TRANSACTION TESTS
# ============================================================================

def test_transaction_commit(tmp_path, monkeypatch):
    """
    Test: Transaktionen werden korrekt committed
    """
    db_file = tmp_path / "test.db"
    gw = _reload_gateway_with_env(monkeypatch, APP_DB_PATH=str(db_file))

    con = gw.connect()

    try:
        # Erstelle Test-Tabelle
        con.execute("""
                    CREATE TABLE transaction_test
                    (
                        id    INTEGER PRIMARY KEY,
                        value TEXT
                    )
                    """)
        con.commit()

        # Insert mit commit
        # noinspection SqlResolve
        con.execute("INSERT INTO transaction_test (value) VALUES (?)", ('test',))
        con.commit()

        # Prüfe ob Daten persistiert sind
        # noinspection SqlResolve
        row = con.execute("SELECT value FROM transaction_test WHERE id = 1").fetchone()
        assert row is not None
        assert row[0] == 'test'
    finally:
        con.close()


def test_transaction_rollback(tmp_path, monkeypatch):
    """
    Test: Transaktionen können zurückgerollt werden
    """
    db_file = tmp_path / "test.db"
    gw = _reload_gateway_with_env(monkeypatch, APP_DB_PATH=str(db_file))

    con = gw.connect()

    try:
        # Erstelle Test-Tabelle
        con.execute("""
                    CREATE TABLE rollback_test
                    (
                        id    INTEGER PRIMARY KEY,
                        value TEXT
                    )
                    """)
        con.commit()

        # Insert ohne commit
        # noinspection SqlResolve
        con.execute("INSERT INTO rollback_test (value) VALUES (?)", ('test',))
        con.rollback()

        # Prüfe dass Daten NICHT persistiert sind
        # noinspection SqlResolve
        row = con.execute("SELECT COUNT(*) FROM rollback_test").fetchone()
        assert row[0] == 0
    finally:
        con.close()


def test_transaction_isolation(tmp_path, monkeypatch):
    """
    Test: Transaktionen sind isoliert zwischen Connections
    """
    db_file = tmp_path / "test.db"
    gw = _reload_gateway_with_env(monkeypatch, APP_DB_PATH=str(db_file))

    # Setup: Erstelle Tabelle
    con1 = gw.connect()
    try:
        con1.execute("""
                     CREATE TABLE isolation_test
                     (
                         id    INTEGER PRIMARY KEY,
                         value TEXT
                     )
                     """)
        con1.commit()
    finally:
        con1.close()

    # Test: Zwei Connections
    con1 = gw.connect()
    con2 = gw.connect()

    try:
        # Con1: Insert ohne commit
        # noinspection SqlResolve
        con1.execute("INSERT INTO isolation_test (value) VALUES ('test')")

        # Con2: Sollte Daten NICHT sehen (nicht committed)
        # noinspection SqlResolve
        row = con2.execute("SELECT COUNT(*) FROM isolation_test").fetchone()
        assert row[0] == 0, "Nicht-committete Daten sollten nicht sichtbar sein"

        # Con1: Commit
        con1.commit()

        # Con2: Jetzt sollten Daten sichtbar sein
        # noinspection SqlResolve
        row = con2.execute("SELECT COUNT(*) FROM isolation_test").fetchone()
        assert row[0] == 1, "Committete Daten sollten sichtbar sein"

    finally:
        con1.close()
        con2.close()


# ============================================================================
# CRUD OPERATION TESTS
# ============================================================================

def test_insert_and_retrieve(tmp_path, monkeypatch):
    """
    Test: Insert und Select funktionieren
    """
    db_file = tmp_path / "test.db"
    gw = _reload_gateway_with_env(monkeypatch, APP_DB_PATH=str(db_file))

    con = gw.connect()
    try:
        # Erstelle Tabelle
        con.execute("""
                    CREATE TABLE crud_test
                    (
                        id    INTEGER PRIMARY KEY,
                        name  TEXT,
                        value INTEGER
                    )
                    """)

        # Insert
        # noinspection SqlResolve
        con.execute("INSERT INTO crud_test (name, value) VALUES (?, ?)", ("test", 42))
        con.commit()

        # Retrieve
        # noinspection SqlResolve
        row = con.execute("SELECT * FROM crud_test WHERE name = ?", ("test",)).fetchone()
        assert row is not None
        assert row['name'] == 'test'
        assert row['value'] == 42

    finally:
        con.close()


def test_update_operation(tmp_path, monkeypatch):
    """
    Test: Update Operation funktioniert
    """
    db_file = tmp_path / "test.db"
    gw = _reload_gateway_with_env(monkeypatch, APP_DB_PATH=str(db_file))

    con = gw.connect()
    try:
        # Setup
        con.execute("CREATE TABLE update_test (id INTEGER PRIMARY KEY, value TEXT)")
        # noinspection SqlResolve
        con.execute("INSERT INTO update_test (value) VALUES ('old')")
        con.commit()

        # Update
        # noinspection SqlResolve
        con.execute("UPDATE update_test SET value = ? WHERE id = ?", ("new", 1))
        con.commit()

        # Verify
        # noinspection SqlResolve
        row = con.execute("SELECT value FROM update_test WHERE id = 1").fetchone()
        assert row[0] == 'new'

    finally:
        con.close()


def test_delete_operation(tmp_path, monkeypatch):
    """
    Test: Delete Operation funktioniert
    """
    db_file = tmp_path / "test.db"
    gw = _reload_gateway_with_env(monkeypatch, APP_DB_PATH=str(db_file))

    con = gw.connect()
    try:
        # Setup
        con.execute("CREATE TABLE delete_test (id INTEGER PRIMARY KEY, value TEXT)")
        # noinspection SqlResolve
        con.execute("INSERT INTO delete_test (value) VALUES ('test')")
        con.commit()

        # Delete
        # noinspection SqlResolve
        con.execute("DELETE FROM delete_test WHERE id = 1")
        con.commit()

        # Verify
        # noinspection SqlResolve
        row = con.execute("SELECT COUNT(*) FROM delete_test").fetchone()
        assert row[0] == 0

    finally:
        con.close()