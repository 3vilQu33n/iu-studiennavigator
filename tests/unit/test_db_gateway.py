# tests/unit/test_db_gateway.py
"""
Unit Tests fuer DB Gateway

Testet Logik isoliert mit gemockten Abhaengigkeiten.
Keine echte Datenbank-Schema-Validierung (das ist in integration/test_db_gateway.py).
"""
from __future__ import annotations

import importlib
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import sqlite3
import pytest

# Mark this whole module as unit tests
pytestmark = pytest.mark.unit


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _reload_gateway_module(monkeypatch: pytest.MonkeyPatch, **env):
    """
    Re-import db_gateway mit neuen Umgebungsvariablen.

    Entfernt alle relevanten Env-Variablen und setzt nur die uebergebenen.
    """
    # Alle bekannten DB-Env-Variablen entfernen
    env_candidates = ("APP_DB_PATH", "APP DB PATH", "APP_DB", "DB_PATH")
    for key in env_candidates:
        monkeypatch.delenv(key, raising=False)

    # Gewuenschte Variablen setzen
    for k, v in env.items():
        if v is not None:
            monkeypatch.setenv(k, v)

    # Fresh import erzwingen
    sys.modules.pop("repositories.db_gateway", None)
    sys.modules.pop("db_gateway", None)

    try:
        return importlib.import_module("repositories.db_gateway")
    except ModuleNotFoundError:
        return importlib.import_module("db_gateway")


# ============================================================================
# _resolve_db_path() UNIT TESTS
# ============================================================================

class TestResolveDbPath:
    """Tests fuer die Pfad-Aufloesungslogik"""

    def test_app_db_path_has_highest_priority(self, tmp_path, monkeypatch):
        """APP_DB_PATH hat hoechste Prioritaet vor anderen Env-Variablen"""
        db1 = tmp_path / "priority1.db"
        db2 = tmp_path / "priority2.db"
        db3 = tmp_path / "priority3.db"

        gw = _reload_gateway_module(monkeypatch,
                                    APP_DB_PATH=str(db1),
                                    APP_DB=str(db2),
                                    DB_PATH=str(db3))

        assert gw.DB_PATH == db1.resolve()

    def test_app_db_fallback(self, tmp_path, monkeypatch):
        """APP_DB wird verwendet, wenn APP_DB_PATH nicht gesetzt"""
        db_file = tmp_path / "app_db.db"

        gw = _reload_gateway_module(monkeypatch, APP_DB=str(db_file))

        assert gw.DB_PATH == db_file.resolve()

    def test_db_path_fallback(self, tmp_path, monkeypatch):
        """DB_PATH wird verwendet, wenn andere Variablen nicht gesetzt"""
        db_file = tmp_path / "db_path.db"

        gw = _reload_gateway_module(monkeypatch, DB_PATH=str(db_file))

        assert gw.DB_PATH == db_file.resolve()

    def test_tilde_expansion(self, tmp_path, monkeypatch):
        """Pfade mit ~ werden korrekt expandiert"""
        expanded_path = tmp_path / "expanded.db"

        with patch('pathlib.Path.expanduser') as mock_expand:
            mock_expand.return_value = expanded_path
            gw = _reload_gateway_module(monkeypatch, APP_DB_PATH="~/test.db")

            # DB_PATH sollte resolved sein
            assert gw.DB_PATH.is_absolute()

    def test_relative_path_becomes_absolute(self, tmp_path, monkeypatch):
        """Relative Pfade werden zu absoluten Pfaden aufgeloest"""
        gw = _reload_gateway_module(monkeypatch, APP_DB_PATH="relative/path/test.db")

        assert gw.DB_PATH.is_absolute()

    def test_fallback_to_project_root(self, monkeypatch):
        """Ohne Env-Variablen: Fallback auf dashboard.db im Projekt-Root"""
        gw = _reload_gateway_module(monkeypatch)  # Keine Env-Variablen

        # Sollte auf dashboard.db enden
        assert gw.DB_PATH.name == "dashboard.db"
        assert gw.DB_PATH.is_absolute()


# ============================================================================
# DBError UNIT TESTS
# ============================================================================

class TestDBError:
    """Tests fuer die DBError Exception-Klasse"""

    def test_inherits_from_runtime_error(self):
        """DBError erbt von RuntimeError"""
        try:
            from repositories.db_gateway import DBError
        except ImportError:
            from db_gateway import DBError

        assert issubclass(DBError, RuntimeError)

    def test_error_message_preserved(self):
        """Fehlermeldung wird korrekt gespeichert"""
        try:
            from repositories.db_gateway import DBError
        except ImportError:
            from db_gateway import DBError

        msg = "Datenbankfehler aufgetreten"
        error = DBError(msg)
        assert str(error) == msg

    def test_can_be_caught_as_runtime_error(self):
        """DBError kann als RuntimeError gefangen werden"""
        try:
            from repositories.db_gateway import DBError
        except ImportError:
            from db_gateway import DBError

        with pytest.raises(RuntimeError):
            raise DBError("test")


# ============================================================================
# connect() UNIT TESTS
# ============================================================================

class TestConnect:
    """Tests fuer die connect() Funktion"""

    def test_raises_db_error_on_sqlite_error(self, tmp_path, monkeypatch):
        """connect() wirft DBError bei SQLite-Fehlern"""
        gw = _reload_gateway_module(monkeypatch, APP_DB_PATH=str(tmp_path / "test.db"))

        with patch('sqlite3.connect') as mock_connect:
            mock_connect.side_effect = sqlite3.Error("Connection failed")

            with pytest.raises(gw.DBError) as exc_info:
                gw.connect()

            assert "Connection failed" in str(exc_info.value)

    def test_sets_row_factory(self, tmp_path, monkeypatch):
        """connect() setzt row_factory auf sqlite3.Row"""
        db_file = tmp_path / "test.db"
        gw = _reload_gateway_module(monkeypatch, APP_DB_PATH=str(db_file))

        con = gw.connect()
        try:
            assert con.row_factory == sqlite3.Row
        finally:
            con.close()

    def test_enables_foreign_keys(self, tmp_path, monkeypatch):
        """connect() aktiviert Foreign Key Constraints"""
        db_file = tmp_path / "test.db"
        gw = _reload_gateway_module(monkeypatch, APP_DB_PATH=str(db_file))

        con = gw.connect()
        try:
            result = con.execute("PRAGMA foreign_keys;").fetchone()
            assert result[0] == 1
        finally:
            con.close()

    def test_returns_connection_object(self, tmp_path, monkeypatch):
        """connect() gibt sqlite3.Connection zurueck"""
        db_file = tmp_path / "test.db"
        gw = _reload_gateway_module(monkeypatch, APP_DB_PATH=str(db_file))

        con = gw.connect()
        try:
            assert isinstance(con, sqlite3.Connection)
        finally:
            con.close()

    def test_connection_is_usable(self, tmp_path, monkeypatch):
        """Verbindung kann SQL ausfuehren"""
        db_file = tmp_path / "test.db"
        gw = _reload_gateway_module(monkeypatch, APP_DB_PATH=str(db_file))

        con = gw.connect()
        try:
            con.execute("CREATE TABLE test_table (id INTEGER PRIMARY KEY)")
            con.execute("INSERT INTO test_table (id) VALUES (1)")
            result = con.execute("SELECT id FROM test_table").fetchone()
            assert result[0] == 1
        finally:
            con.close()

    def test_schema_init_failure_does_not_raise(self, tmp_path, monkeypatch):
        """Fehler in init_pruefung_schema wird ignoriert"""
        db_file = tmp_path / "test.db"
        gw = _reload_gateway_module(monkeypatch, APP_DB_PATH=str(db_file))

        # Setze init_pruefung_schema auf eine fehlschlagende Funktion
        original_init = gw.init_pruefung_schema

        def failing_init(conn):
            raise Exception("Schema init failed")

        try:
            gw.init_pruefung_schema = failing_init

            # Sollte NICHT fehlschlagen
            con = gw.connect()
            con.close()
        finally:
            # Wiederherstellen
            gw.init_pruefung_schema = original_init


# ============================================================================
# _connect() ALIAS UNIT TESTS
# ============================================================================

class TestConnectAlias:
    """Tests fuer den _connect() Rueckwaertskompatibilitaets-Alias"""

    def test_alias_exists(self, tmp_path, monkeypatch):
        """_connect existiert als Alias"""
        db_file = tmp_path / "test.db"
        gw = _reload_gateway_module(monkeypatch, APP_DB_PATH=str(db_file))

        assert hasattr(gw, '_connect')
        assert callable(gw._connect)

    def test_alias_returns_same_type(self, tmp_path, monkeypatch):
        """_connect() gibt gleichen Verbindungstyp zurueck wie connect()"""
        db_file = tmp_path / "test.db"
        gw = _reload_gateway_module(monkeypatch, APP_DB_PATH=str(db_file))

        con1 = gw.connect()
        con2 = gw._connect()

        try:
            assert type(con1) == type(con2)
        finally:
            con1.close()
            con2.close()

    def test_alias_has_same_row_factory(self, tmp_path, monkeypatch):
        """_connect() setzt ebenfalls row_factory"""
        db_file = tmp_path / "test.db"
        gw = _reload_gateway_module(monkeypatch, APP_DB_PATH=str(db_file))

        con = gw._connect()
        try:
            assert con.row_factory == sqlite3.Row
        finally:
            con.close()


# ============================================================================
# DBGateway CLASS UNIT TESTS
# ============================================================================

class TestDBGatewayClass:
    """Unit Tests fuer die DBGateway Klasse"""

    def test_class_exists(self, tmp_path, monkeypatch):
        """DBGateway Klasse existiert"""
        gw = _reload_gateway_module(monkeypatch, APP_DB_PATH=str(tmp_path / "test.db"))

        assert hasattr(gw, 'DBGateway')

    def test_default_path_is_module_db_path(self, tmp_path, monkeypatch):
        """DBGateway() ohne Argument verwendet DB_PATH des Moduls"""
        db_file = tmp_path / "test.db"
        gw = _reload_gateway_module(monkeypatch, APP_DB_PATH=str(db_file))

        if not hasattr(gw, 'DBGateway'):
            pytest.skip("DBGateway Klasse nicht vorhanden")

        gateway = gw.DBGateway()
        assert gateway.db_path == gw.DB_PATH

    def test_custom_path_override(self, tmp_path, monkeypatch):
        """DBGateway() mit Argument ueberschreibt DB_PATH"""
        db_file = tmp_path / "default.db"
        custom_file = tmp_path / "custom.db"

        gw = _reload_gateway_module(monkeypatch, APP_DB_PATH=str(db_file))

        if not hasattr(gw, 'DBGateway'):
            pytest.skip("DBGateway Klasse nicht vorhanden")

        gateway = gw.DBGateway(custom_file)
        assert gateway.db_path == custom_file.resolve()
        assert gateway.db_path != gw.DB_PATH

    def test_string_path_converted_to_path_object(self, tmp_path, monkeypatch):
        """String-Pfad wird zu Path-Objekt konvertiert"""
        gw = _reload_gateway_module(monkeypatch, APP_DB_PATH=str(tmp_path / "test.db"))

        if not hasattr(gw, 'DBGateway'):
            pytest.skip("DBGateway Klasse nicht vorhanden")

        gateway = gw.DBGateway(str(tmp_path / "string_path.db"))
        assert isinstance(gateway.db_path, Path)

    def test_execute_method_exists(self, tmp_path, monkeypatch):
        """_execute Methode existiert"""
        gw = _reload_gateway_module(monkeypatch, APP_DB_PATH=str(tmp_path / "test.db"))

        if not hasattr(gw, 'DBGateway'):
            pytest.skip("DBGateway Klasse nicht vorhanden")

        gateway = gw.DBGateway()
        assert hasattr(gateway, '_execute')
        assert callable(gateway._execute)

    def test_execute_creates_table(self, tmp_path, monkeypatch):
        """_execute kann Tabellen erstellen"""
        db_file = tmp_path / "test.db"
        gw = _reload_gateway_module(monkeypatch, APP_DB_PATH=str(db_file))

        if not hasattr(gw, 'DBGateway'):
            pytest.skip("DBGateway Klasse nicht vorhanden")

        gateway = gw.DBGateway(db_file)
        gateway._execute("CREATE TABLE test (id INTEGER PRIMARY KEY)")

        # Pruefe ob Tabelle existiert
        con = sqlite3.connect(db_file)
        try:
            result = con.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='test'"
            ).fetchone()
            assert result is not None
        finally:
            con.close()

    def test_execute_commits_automatically(self, tmp_path, monkeypatch):
        """_execute fuehrt automatisch commit aus"""
        db_file = tmp_path / "test.db"
        gw = _reload_gateway_module(monkeypatch, APP_DB_PATH=str(db_file))

        if not hasattr(gw, 'DBGateway'):
            pytest.skip("DBGateway Klasse nicht vorhanden")

        gateway = gw.DBGateway(db_file)

        # Erstelle Tabelle und fuege Daten ein
        gateway._execute("CREATE TABLE commit_test (id INTEGER PRIMARY KEY, val TEXT)")
        gateway._execute("INSERT INTO commit_test (val) VALUES (?)", ("test",))

        # Neue Connection sollte Daten sehen (war committed)
        con = sqlite3.connect(db_file)
        try:
            row = con.execute("SELECT val FROM commit_test").fetchone()
            assert row is not None
            assert row[0] == "test"
        finally:
            con.close()

    def test_execute_returns_cursor(self, tmp_path, monkeypatch):
        """_execute gibt Cursor-Objekt zurueck"""
        db_file = tmp_path / "test.db"
        gw = _reload_gateway_module(monkeypatch, APP_DB_PATH=str(db_file))

        if not hasattr(gw, 'DBGateway'):
            pytest.skip("DBGateway Klasse nicht vorhanden")

        gateway = gw.DBGateway(db_file)
        cursor = gateway._execute("CREATE TABLE cursor_test (id INTEGER)")

        assert isinstance(cursor, sqlite3.Cursor)


# ============================================================================
# PARAMETER VALIDATION TESTS
# ============================================================================

class TestParameterValidation:
    """Tests fuer Parametervalidierung"""

    def test_execute_with_tuple_params(self, tmp_path, monkeypatch):
        """_execute akzeptiert Tuple-Parameter"""
        db_file = tmp_path / "test.db"
        gw = _reload_gateway_module(monkeypatch, APP_DB_PATH=str(db_file))

        if not hasattr(gw, 'DBGateway'):
            pytest.skip("DBGateway Klasse nicht vorhanden")

        gateway = gw.DBGateway(db_file)
        gateway._execute("CREATE TABLE param_test (id INTEGER, val TEXT)")

        # Tuple-Parameter
        cursor = gateway._execute("INSERT INTO param_test VALUES (?, ?)", (1, "test"))
        assert cursor is not None

    def test_execute_with_list_params(self, tmp_path, monkeypatch):
        """_execute akzeptiert List-Parameter"""
        db_file = tmp_path / "test.db"
        gw = _reload_gateway_module(monkeypatch, APP_DB_PATH=str(db_file))

        if not hasattr(gw, 'DBGateway'):
            pytest.skip("DBGateway Klasse nicht vorhanden")

        gateway = gw.DBGateway(db_file)
        gateway._execute("CREATE TABLE list_test (id INTEGER, val TEXT)")

        # List-Parameter
        cursor = gateway._execute("INSERT INTO list_test VALUES (?, ?)", [1, "test"])
        assert cursor is not None

    def test_execute_with_empty_params(self, tmp_path, monkeypatch):
        """_execute funktioniert ohne Parameter"""
        db_file = tmp_path / "test.db"
        gw = _reload_gateway_module(monkeypatch, APP_DB_PATH=str(db_file))

        if not hasattr(gw, 'DBGateway'):
            pytest.skip("DBGateway Klasse nicht vorhanden")

        gateway = gw.DBGateway(db_file)
        cursor = gateway._execute("CREATE TABLE no_param_test (id INTEGER)")

        assert cursor is not None


# ============================================================================
# LOGGING UNIT TESTS
# ============================================================================

class TestLogging:
    """Tests fuer Logging-Verhalten"""

    def test_logger_exists(self, tmp_path, monkeypatch):
        """Logger ist konfiguriert"""
        gw = _reload_gateway_module(monkeypatch, APP_DB_PATH=str(tmp_path / "test.db"))

        assert hasattr(gw, 'logger')

    def test_logger_has_name(self, tmp_path, monkeypatch):
        """Logger hat korrekten Namen"""
        gw = _reload_gateway_module(monkeypatch, APP_DB_PATH=str(tmp_path / "test.db"))

        # Logger-Name sollte Modul-Name enthalten
        assert gw.logger.name in ('repositories.db_gateway', 'db_gateway')


# ============================================================================
# EDGE CASE UNIT TESTS
# ============================================================================

class TestEdgeCases:
    """Tests fuer Randfaelle"""

    def test_empty_env_variable_ignored(self, tmp_path, monkeypatch):
        """Leere Umgebungsvariable wird ignoriert"""
        monkeypatch.setenv("APP_DB_PATH", "")

        # Sollte nicht crashen, sondern Fallback verwenden
        gw = _reload_gateway_module(monkeypatch)
        assert gw.DB_PATH is not None

    def test_whitespace_only_env_variable(self, tmp_path, monkeypatch):
        """Nur-Whitespace Umgebungsvariable wird behandelt"""
        monkeypatch.setenv("APP_DB_PATH", "   ")

        # Sollte nicht crashen
        gw = _reload_gateway_module(monkeypatch)
        assert gw.DB_PATH is not None

    def test_none_db_path_in_gateway_class(self, tmp_path, monkeypatch):
        """DBGateway(None) verwendet Standard-DB_PATH"""
        db_file = tmp_path / "test.db"
        gw = _reload_gateway_module(monkeypatch, APP_DB_PATH=str(db_file))

        if not hasattr(gw, 'DBGateway'):
            pytest.skip("DBGateway Klasse nicht vorhanden")

        gateway = gw.DBGateway(None)
        assert gateway.db_path == gw.DB_PATH

    def test_connection_can_be_used_as_context_manager(self, tmp_path, monkeypatch):
        """Connection kann als Context Manager verwendet werden"""
        db_file = tmp_path / "test.db"
        gw = _reload_gateway_module(monkeypatch, APP_DB_PATH=str(db_file))

        # sqlite3.Connection unterstuetzt Context Manager
        con = gw.connect()
        with con:
            con.execute("CREATE TABLE ctx_test (id INTEGER)")
        con.close()

    def test_multiple_connections_independent(self, tmp_path, monkeypatch):
        """Mehrere Verbindungen sind unabhaengig"""
        db_file = tmp_path / "test.db"
        gw = _reload_gateway_module(monkeypatch, APP_DB_PATH=str(db_file))

        con1 = gw.connect()
        con2 = gw.connect()

        try:
            # Beide sollten funktionieren
            con1.execute("CREATE TABLE multi_test (id INTEGER)")
            con1.commit()

            result = con2.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='multi_test'"
            ).fetchone()
            assert result is not None
        finally:
            con1.close()
            con2.close()

    def test_db_path_is_path_object(self, tmp_path, monkeypatch):
        """DB_PATH ist ein Path-Objekt"""
        db_file = tmp_path / "test.db"
        gw = _reload_gateway_module(monkeypatch, APP_DB_PATH=str(db_file))

        assert isinstance(gw.DB_PATH, Path)


# ============================================================================
# DB_PATH MODULE VARIABLE TESTS
# ============================================================================

class TestDBPathVariable:
    """Tests fuer die DB_PATH Modul-Variable"""

    def test_db_path_is_exported(self, tmp_path, monkeypatch):
        """DB_PATH ist als Modul-Variable verfuegbar"""
        gw = _reload_gateway_module(monkeypatch, APP_DB_PATH=str(tmp_path / "test.db"))

        assert hasattr(gw, 'DB_PATH')

    def test_db_path_is_absolute(self, tmp_path, monkeypatch):
        """DB_PATH ist immer absolut"""
        gw = _reload_gateway_module(monkeypatch, APP_DB_PATH=str(tmp_path / "test.db"))

        assert gw.DB_PATH.is_absolute()

    def test_db_path_is_resolved(self, tmp_path, monkeypatch):
        """DB_PATH ist resolved (keine .. oder .)"""
        gw = _reload_gateway_module(monkeypatch,
                                    APP_DB_PATH=str(tmp_path / "subdir" / ".." / "test.db"))

        # Sollte keine '..' mehr enthalten
        assert ".." not in str(gw.DB_PATH)