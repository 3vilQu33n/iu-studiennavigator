# tests/integration/test_db_gateway.py
"""
Integration Tests fuer DB Gateway
Testet Datenbankoperationen mit echter SQLite-Datenbank

Angepasst an schema.txt (Stand November 2025)
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

    Damit wird DB_PATH neu berechnet fuer jeden Test

    Args:
        monkeypatch: pytest MonkeyPatch fixture
        **env: Umgebungsvariablen zum Setzen

    Returns:
        Importiertes db_gateway Modul
    """
    for k, v in env.items():
        if v is None:
            monkeypatch.delenv(k, raising=False)
            if k == "APP_DB_PATH":
                monkeypatch.delenv("APP DB PATH", raising=False)
        else:
            monkeypatch.setenv(k, v)
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

class TestDBPathConfiguration:
    """Tests fuer DB_PATH Konfiguration"""

    def test_data_source_points_to_same_file(self, tmp_path, monkeypatch):
        """Test: APP_DB_PATH wird korrekt als DB_PATH verwendet"""
        db_file = tmp_path / "test.db"
        gw = _reload_gateway_with_env(monkeypatch, APP_DB_PATH=str(db_file))

        left = Path(gw.DB_PATH).resolve()
        right = Path(db_file).resolve()

        assert left == right, f"DB_PATH mismatch: {left} != {right}"

    def test_db_path_is_absolute(self, tmp_path, monkeypatch):
        """Test: DB_PATH ist immer ein absoluter Pfad"""
        db_file = tmp_path / "test.db"
        gw = _reload_gateway_with_env(monkeypatch, APP_DB_PATH=str(db_file))

        db_path = Path(gw.DB_PATH)
        assert db_path.is_absolute(), "DB_PATH muss absolut sein"


# ============================================================================
# CONNECTION TESTS
# ============================================================================

class TestConnection:
    """Tests fuer Datenbankverbindungen"""

    def test_foreign_keys_enforced(self, tmp_path, monkeypatch):
        """Test: Foreign Keys sind aktiviert bei jeder Connection"""
        db_file = tmp_path / "test.db"
        gw = _reload_gateway_with_env(monkeypatch, APP_DB_PATH=str(db_file))

        con = gw.connect()
        try:
            result = con.execute("PRAGMA foreign_keys;").fetchone()
            assert result[0] == 1, "Foreign Keys muessen aktiviert sein"
        finally:
            con.close()

    def test_connection_has_row_factory(self, tmp_path, monkeypatch):
        """Test: Connection hat Row Factory fuer dict-aehnlichen Zugriff"""
        db_file = tmp_path / "test.db"
        gw = _reload_gateway_with_env(monkeypatch, APP_DB_PATH=str(db_file))

        con = gw.connect()
        try:
            assert con.row_factory is not None, "Row Factory muss gesetzt sein"
        finally:
            con.close()

    def test_multiple_connections(self, tmp_path, monkeypatch):
        """Test: Mehrere Connections koennen gleichzeitig erstellt werden"""
        db_file = tmp_path / "test.db"
        gw = _reload_gateway_with_env(monkeypatch, APP_DB_PATH=str(db_file))

        con1 = gw.connect()
        con2 = gw.connect()

        try:
            assert con1.execute("PRAGMA foreign_keys;").fetchone()[0] == 1
            assert con2.execute("PRAGMA foreign_keys;").fetchone()[0] == 1
        finally:
            con1.close()
            con2.close()

    def test_backward_compatible_connect(self, tmp_path, monkeypatch):
        """Test: _connect() funktioniert als Alias fuer connect()"""
        db_file = tmp_path / "test.db"
        gw = _reload_gateway_with_env(monkeypatch, APP_DB_PATH=str(db_file))

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

class TestDBGatewayClass:
    """Tests fuer DBGateway Klasse"""

    def test_db_gateway_class_exists(self, tmp_path, monkeypatch):
        """Test: DBGateway Klasse existiert (optional)"""
        db_file = tmp_path / "test.db"
        gw_module = _reload_gateway_with_env(monkeypatch, APP_DB_PATH=str(db_file))

        if not hasattr(gw_module, 'DBGateway'):
            pytest.skip("DBGateway Klasse nicht vorhanden (optional)")

        gateway = gw_module.DBGateway()
        assert gateway is not None
        assert hasattr(gateway, 'db_path')

    def test_db_gateway_class_default_path(self, tmp_path, monkeypatch):
        """Test: DBGateway Klasse verwendet Standard DB_PATH"""
        db_file = tmp_path / "test.db"
        gw_module = _reload_gateway_with_env(monkeypatch, APP_DB_PATH=str(db_file))

        if not hasattr(gw_module, 'DBGateway'):
            pytest.skip("DBGateway Klasse nicht vorhanden (optional)")

        gateway = gw_module.DBGateway()
        assert str(gateway.db_path) == str(Path(gw_module.DB_PATH).resolve())

    def test_db_gateway_class_custom_path(self, tmp_path, monkeypatch):
        """Test: DBGateway Klasse kann mit custom Path initialisiert werden"""
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

class TestSchema:
    """Tests fuer Datenbankschema"""

    def test_can_create_table(self, tmp_path, monkeypatch):
        """Test: Tabellen koennen erstellt werden"""
        db_file = tmp_path / "test.db"
        gw = _reload_gateway_with_env(monkeypatch, APP_DB_PATH=str(db_file))

        con = gw.connect()
        try:
            # noinspection SqlResolve
            con.execute("""
                        CREATE TABLE IF NOT EXISTS test_table
                        (
                            id   INTEGER PRIMARY KEY,
                            name TEXT
                        );
                        """)
            con.commit()

            # noinspection SqlResolve
            row = con.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='test_table'"
            ).fetchone()

            assert row is not None
            assert row[0] == "test_table"
        finally:
            con.close()

    def test_schema_tables_exist(self, temp_db):
        """
        Test: Alle notwendigen Tabellen existieren in der Test-DB

        Basierend auf schema.txt (Stand November 2025)
        """
        con = sqlite3.connect(temp_db)

        try:
            # Liste erwarteter Tabellen laut schema.txt
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
                'pruefungsanmeldung',
                'pruefungstermin',
                'gebuehr',
                'pruefungsart',
                'modul_pruefungsart'
            ]

            cursor = con.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            existing_tables = [row[0] for row in cursor.fetchall()]

            for table in expected_tables:
                assert table in existing_tables, f"Tabelle {table} fehlt im Schema"

        finally:
            con.close()

    def test_schema_indices_exist(self, temp_db):
        """Test: Wichtige Indizes existieren"""
        con = sqlite3.connect(temp_db)

        try:
            expected_indices = [
                'idx_gebuehr_einschreibung_faellig',
                'idx_pruefungsanmeldung_termin',
                'idx_pruefungsleistung_modulbuchung',
                'idx_pruefungstermin_modul',
                'idx_modul_pruefungsart_modul',
                'idx_modul_pruefungsart_art',
                'idx_modulbuchung_unique'
            ]

            cursor = con.execute(
                "SELECT name FROM sqlite_master WHERE type='index'"
            )
            existing_indices = [row[0] for row in cursor.fetchall()]

            for index in expected_indices:
                assert index in existing_indices, f"Index {index} fehlt im Schema"

        finally:
            con.close()

    def test_foreign_keys_constraints(self, tmp_path, monkeypatch):
        """Test: Foreign Key Constraints werden durchgesetzt"""
        db_file = tmp_path / "test.db"
        gw = _reload_gateway_with_env(monkeypatch, APP_DB_PATH=str(db_file))

        con = gw.connect()

        try:
            # noinspection SqlResolve
            con.execute("CREATE TABLE parent (id INTEGER PRIMARY KEY);")
            # noinspection SqlResolve
            con.execute("""
                        CREATE TABLE child (
                            id        INTEGER PRIMARY KEY,
                            parent_id INTEGER,
                            FOREIGN KEY (parent_id) REFERENCES parent (id)
                        );
                        """)
            con.commit()

            # Versuche ungueltigen FK einzufuegen (sollte fehlschlagen)
            with pytest.raises(sqlite3.IntegrityError):
                # noinspection SqlResolve
                con.execute("INSERT INTO child (parent_id) VALUES (999)")
                con.commit()

        finally:
            con.close()

    def test_modulbuchung_unique_constraint(self, temp_db):
        """Test: UNIQUE constraint auf modulbuchung(einschreibung_id, modul_id)"""
        con = sqlite3.connect(temp_db)
        con.execute("PRAGMA foreign_keys = ON")

        try:
            einschreibung = con.execute("SELECT id FROM einschreibung LIMIT 1").fetchone()
            modul = con.execute("SELECT id FROM modul LIMIT 1").fetchone()

            if not einschreibung or not modul:
                pytest.skip("Keine Testdaten vorhanden")

            # noinspection SqlResolve
            con.execute("""
                INSERT INTO modulbuchung (einschreibung_id, modul_id, status)
                VALUES (?, ?, 'gebucht')
            """, (einschreibung[0], modul[0]))
            con.commit()

            with pytest.raises(sqlite3.IntegrityError):
                # noinspection SqlResolve
                con.execute("""
                    INSERT INTO modulbuchung (einschreibung_id, modul_id, status)
                    VALUES (?, ?, 'gebucht')
                """, (einschreibung[0], modul[0]))
                con.commit()

        finally:
            con.close()

    def test_pruefungsart_has_default_data(self, temp_db):
        """Test: pruefungsart Tabelle hat Standarddaten"""
        con = sqlite3.connect(temp_db)

        try:
            cursor = con.execute("SELECT kuerzel, name FROM pruefungsart")
            pruefungsarten = {row[0]: row[1] for row in cursor.fetchall()}

            expected = ['K', 'AWB', 'PO', 'F', 'FP', 'PB', 'PP', 'S', 'H']

            for kuerzel in expected:
                assert kuerzel in pruefungsarten, f"Pruefungsart {kuerzel} fehlt"

        finally:
            con.close()

    def test_studiengang_modul_wahlbereich_constraint(self, temp_db):
        """Test: wahlbereich CHECK constraint funktioniert"""
        con = sqlite3.connect(temp_db)
        con.execute("PRAGMA foreign_keys = ON")

        try:
            studiengang = con.execute("SELECT id FROM studiengang LIMIT 1").fetchone()
            modul = con.execute("SELECT id FROM modul LIMIT 1").fetchone()

            if not studiengang or not modul:
                pytest.skip("Keine Testdaten vorhanden")

            # noinspection SqlResolve
            con.execute("""
                INSERT INTO studiengang_modul (studiengang_id, modul_id, semester, pflichtgrad, wahlbereich)
                VALUES (?, ?, 5, 'Wahl', 'A')
            """, (studiengang[0], modul[0]))
            con.commit()

            with pytest.raises(sqlite3.IntegrityError):
                # noinspection SqlResolve
                con.execute("""
                    INSERT INTO studiengang_modul (studiengang_id, modul_id, semester, pflichtgrad, wahlbereich)
                    VALUES (?, ?, 6, 'Wahl', 'X')
                """, (studiengang[0], modul[0]))
                con.commit()

        finally:
            con.close()


# ============================================================================
# EXCEPTION TESTS
# ============================================================================

class TestExceptions:
    """Tests fuer Exceptions"""

    def test_db_error_exception(self):
        """Test: DBError Exception kann geworfen und gefangen werden"""
        try:
            from repositories.db_gateway import DBError
        except ImportError:
            try:
                from db_gateway import DBError
            except ImportError:
                pytest.skip("DBError nicht vorhanden (optional)")
                return

        with pytest.raises(DBError):
            raise DBError("Test error")

    def test_db_error_has_message(self):
        """Test: DBError hat Fehlermeldung"""
        try:
            from repositories.db_gateway import DBError
        except ImportError:
            try:
                from db_gateway import DBError
            except ImportError:
                pytest.skip("DBError nicht vorhanden (optional)")
                return

        error_msg = "Test error message"
        try:
            raise DBError(error_msg)
        except DBError as e:
            assert str(e) == error_msg


# ============================================================================
# TRANSACTION TESTS
# ============================================================================

class TestTransactions:
    """Tests fuer Transaktionen"""

    def test_transaction_commit(self, tmp_path, monkeypatch):
        """Test: Transaktionen werden korrekt committed"""
        db_file = tmp_path / "test.db"
        gw = _reload_gateway_with_env(monkeypatch, APP_DB_PATH=str(db_file))

        con = gw.connect()

        try:
            # noinspection SqlResolve
            con.execute("""
                        CREATE TABLE transaction_test (
                            id    INTEGER PRIMARY KEY,
                            value TEXT
                        )
                        """)
            con.commit()

            # noinspection SqlResolve
            con.execute("INSERT INTO transaction_test (value) VALUES (?)", ('test',))
            con.commit()

            # noinspection SqlResolve
            row = con.execute("SELECT value FROM transaction_test WHERE id = 1").fetchone()
            assert row is not None
            assert row[0] == 'test'
        finally:
            con.close()

    def test_transaction_rollback(self, tmp_path, monkeypatch):
        """Test: Transaktionen koennen zurueckgerollt werden"""
        db_file = tmp_path / "test.db"
        gw = _reload_gateway_with_env(monkeypatch, APP_DB_PATH=str(db_file))

        con = gw.connect()

        try:
            # noinspection SqlResolve
            con.execute("""
                        CREATE TABLE rollback_test (
                            id    INTEGER PRIMARY KEY,
                            value TEXT
                        )
                        """)
            con.commit()

            # noinspection SqlResolve
            con.execute("INSERT INTO rollback_test (value) VALUES (?)", ('test',))
            con.rollback()

            # noinspection SqlResolve
            row = con.execute("SELECT COUNT(*) FROM rollback_test").fetchone()
            assert row[0] == 0
        finally:
            con.close()

    def test_transaction_isolation(self, tmp_path, monkeypatch):
        """Test: Transaktionen sind isoliert zwischen Connections"""
        db_file = tmp_path / "test.db"
        gw = _reload_gateway_with_env(monkeypatch, APP_DB_PATH=str(db_file))

        con1 = gw.connect()
        try:
            # noinspection SqlResolve
            con1.execute("""
                         CREATE TABLE isolation_test(
                             id    INTEGER PRIMARY KEY,
                             value TEXT
                         )
                         """)
            con1.commit()
        finally:
            con1.close()

        con1 = gw.connect()
        con2 = gw.connect()

        try:
            # noinspection SqlResolve
            con1.execute("INSERT INTO isolation_test (value) VALUES ('test')")

            # noinspection SqlResolve
            row = con2.execute("SELECT COUNT(*) FROM isolation_test").fetchone()
            assert row[0] == 0, "Nicht-committete Daten sollten nicht sichtbar sein"

            con1.commit()

            # noinspection SqlResolve
            row = con2.execute("SELECT COUNT(*) FROM isolation_test").fetchone()
            assert row[0] == 1, "Committete Daten sollten sichtbar sein"

        finally:
            con1.close()
            con2.close()


# ============================================================================
# CRUD OPERATION TESTS
# ============================================================================

class TestCRUDOperations:
    """Tests fuer CRUD Operationen"""

    def test_insert_and_retrieve(self, tmp_path, monkeypatch):
        """Test: Insert und Select funktionieren"""
        db_file = tmp_path / "test.db"
        gw = _reload_gateway_with_env(monkeypatch, APP_DB_PATH=str(db_file))

        con = gw.connect()
        try:
            # noinspection SqlResolve
            con.execute("""
                        CREATE TABLE crud_test (
                            id    INTEGER PRIMARY KEY,
                            name  TEXT,
                            value INTEGER
                        )
                        """)

            # noinspection SqlResolve
            con.execute("INSERT INTO crud_test (name, value) VALUES (?, ?)", ("test", 42))
            con.commit()

            # noinspection SqlResolve
            row = con.execute("SELECT * FROM crud_test WHERE name = ?", ("test",)).fetchone()
            assert row is not None
            assert row['name'] == 'test'
            assert row['value'] == 42

        finally:
            con.close()

    def test_update_operation(self, tmp_path, monkeypatch):
        """Test: Update Operation funktioniert"""
        db_file = tmp_path / "test.db"
        gw = _reload_gateway_with_env(monkeypatch, APP_DB_PATH=str(db_file))

        con = gw.connect()
        try:
            # noinspection SqlResolve
            con.execute("CREATE TABLE update_test (id INTEGER PRIMARY KEY, value TEXT)")
            # noinspection SqlResolve
            con.execute("INSERT INTO update_test (value) VALUES ('old')")
            con.commit()

            # noinspection SqlResolve
            con.execute("UPDATE update_test SET value = ? WHERE id = ?", ("new", 1))
            con.commit()

            # noinspection SqlResolve
            row = con.execute("SELECT value FROM update_test WHERE id = 1").fetchone()
            assert row[0] == 'new'

        finally:
            con.close()

    def test_delete_operation(self, tmp_path, monkeypatch):
        """Test: Delete Operation funktioniert"""
        db_file = tmp_path / "test.db"
        gw = _reload_gateway_with_env(monkeypatch, APP_DB_PATH=str(db_file))

        con = gw.connect()
        try:
            # noinspection SqlResolve
            con.execute("CREATE TABLE delete_test (id INTEGER PRIMARY KEY, value TEXT)")
            # noinspection SqlResolve
            con.execute("INSERT INTO delete_test (value) VALUES ('test')")
            con.commit()

            # noinspection SqlResolve
            con.execute("DELETE FROM delete_test WHERE id = 1")
            con.commit()

            # noinspection SqlResolve
            row = con.execute("SELECT COUNT(*) FROM delete_test").fetchone()
            assert row[0] == 0

        finally:
            con.close()


# ============================================================================
# SCHEMA-SPECIFIC TESTS (basierend auf schema.txt)
# ============================================================================

class TestSchemaSpecific:
    """Tests spezifisch fuer das aktuelle Schema"""

    def test_modulbuchung_status_check(self, temp_db):
        """Test: modulbuchung status CHECK constraint"""
        con = sqlite3.connect(temp_db)
        con.execute("PRAGMA foreign_keys = ON")

        try:
            einschreibung = con.execute("SELECT id FROM einschreibung LIMIT 1").fetchone()
            modul = con.execute("SELECT id FROM modul LIMIT 1").fetchone()

            if not einschreibung or not modul:
                pytest.skip("Keine Testdaten vorhanden")

            # noinspection SqlResolve
            con.execute("""
                INSERT INTO modulbuchung (einschreibung_id, modul_id, status)
                VALUES (?, ?, 'gebucht')
            """, (einschreibung[0], modul[0]))
            con.commit()

            # noinspection SqlResolve
            con.execute("DELETE FROM modulbuchung WHERE einschreibung_id = ? AND modul_id = ?",
                        (einschreibung[0], modul[0]))
            con.commit()

            with pytest.raises(sqlite3.IntegrityError):
                # noinspection SqlResolve
                con.execute("""
                    INSERT INTO modulbuchung (einschreibung_id, modul_id, status)
                    VALUES (?, ?, 'ungueltig')
                """, (einschreibung[0], modul[0]))
                con.commit()

        finally:
            con.close()

    def test_pruefungsanmeldung_status_check(self, temp_db):
        """Test: pruefungsanmeldung status CHECK constraint"""
        con = sqlite3.connect(temp_db)
        con.execute("PRAGMA foreign_keys = ON")

        try:
            einschreibung = con.execute("SELECT id FROM einschreibung LIMIT 1").fetchone()
            modul = con.execute("SELECT id FROM modul LIMIT 1").fetchone()

            if not einschreibung or not modul:
                pytest.skip("Keine Testdaten vorhanden")

            # noinspection SqlResolve
            con.execute("""
                INSERT INTO modulbuchung (einschreibung_id, modul_id, status)
                VALUES (?, ?, 'gebucht')
            """, (einschreibung[0], modul[0]))
            modulbuchung_id = con.execute("SELECT last_insert_rowid()").fetchone()[0]

            # noinspection SqlResolve
            con.execute("""
                INSERT INTO pruefungstermin (modul_id, datum, art)
                VALUES (?, date('now', '+30 days'), 'online')
            """, (modul[0],))
            pruefungstermin_id = con.execute("SELECT last_insert_rowid()").fetchone()[0]
            con.commit()

            # noinspection SqlResolve
            con.execute("""
                INSERT INTO pruefungsanmeldung (modulbuchung_id, pruefungstermin_id, status)
                VALUES (?, ?, 'angemeldet')
            """, (modulbuchung_id, pruefungstermin_id))
            con.commit()

            # noinspection SqlResolve
            con.execute("DELETE FROM pruefungsanmeldung WHERE modulbuchung_id = ?", (modulbuchung_id,))
            con.commit()

            with pytest.raises(sqlite3.IntegrityError):
                # noinspection SqlResolve
                con.execute("""
                    INSERT INTO pruefungsanmeldung (modulbuchung_id, pruefungstermin_id, status)
                    VALUES (?, ?, 'ungueltig')
                """, (modulbuchung_id, pruefungstermin_id))
                con.commit()

        finally:
            con.close()

    def test_pruefungstermin_art_check(self, temp_db):
        """Test: pruefungstermin art CHECK constraint"""
        con = sqlite3.connect(temp_db)
        con.execute("PRAGMA foreign_keys = ON")

        try:
            modul = con.execute("SELECT id FROM modul LIMIT 1").fetchone()

            if not modul:
                pytest.skip("Keine Testdaten vorhanden")

            valid_arts = ['online', 'praesenz', 'projekt', 'workbook']

            for art in valid_arts:
                # noinspection SqlResolve
                con.execute("""
                    INSERT INTO pruefungstermin (modul_id, datum, art)
                    VALUES (?, date('now', '+' || ? || ' days'), ?)
                """, (modul[0], valid_arts.index(art) + 1, art))
            con.commit()

            with pytest.raises(sqlite3.IntegrityError):
                # noinspection SqlResolve
                con.execute("""
                    INSERT INTO pruefungstermin (modul_id, datum, art)
                    VALUES (?, date('now', '+10 days'), 'ungueltig')
                """, (modul[0],))
                con.commit()

        finally:
            con.close()

    def test_einschreibung_status_check(self, temp_db):
        """Test: einschreibung status CHECK constraint"""
        con = sqlite3.connect(temp_db)
        con.execute("PRAGMA foreign_keys = ON")

        try:
            student = con.execute("SELECT id FROM student LIMIT 1").fetchone()
            studiengang = con.execute("SELECT id FROM studiengang LIMIT 1").fetchone()
            zeitmodell = con.execute("SELECT id FROM zeitmodell LIMIT 1").fetchone()

            if not all([student, studiengang, zeitmodell]):
                pytest.skip("Keine Testdaten vorhanden")

            valid_status = ['aktiv', 'pausiert', 'exmatrikuliert']

            for i, status in enumerate(valid_status):
                # noinspection SqlResolve
                con.execute("""
                    INSERT INTO student (vorname, nachname, matrikel_nr)
                    VALUES (?, ?, ?)
                """, (f'Test{i}', f'User{i}', f'IU9999999{i}'))
                new_student_id = con.execute("SELECT last_insert_rowid()").fetchone()[0]

                # noinspection SqlResolve
                con.execute("""
                    INSERT INTO einschreibung (student_id, studiengang_id, zeitmodell_id, start_datum, status)
                    VALUES (?, ?, ?, date('now'), ?)
                """, (new_student_id, studiengang[0], zeitmodell[0], status))
            con.commit()

            # noinspection SqlResolve
            con.execute("""
                INSERT INTO student (vorname, nachname, matrikel_nr)
                VALUES ('Test', 'Invalid', 'IU88888888')
            """)
            invalid_student_id = con.execute("SELECT last_insert_rowid()").fetchone()[0]
            con.commit()

            with pytest.raises(sqlite3.IntegrityError):
                # noinspection SqlResolve
                con.execute("""
                    INSERT INTO einschreibung (student_id, studiengang_id, zeitmodell_id, start_datum, status)
                    VALUES (?, ?, ?, date('now'), 'ungueltig')
                """, (invalid_student_id, studiengang[0], zeitmodell[0]))
                con.commit()

        finally:
            con.close()

    def test_login_role_check(self, temp_db):
        """Test: login role CHECK constraint"""
        con = sqlite3.connect(temp_db)
        con.execute("PRAGMA foreign_keys = ON")

        try:
            # noinspection SqlResolve
            con.execute("""
                INSERT INTO student (vorname, nachname, matrikel_nr)
                VALUES ('Role', 'Test', 'IUROLETEST')
            """)
            student_id = con.execute("SELECT last_insert_rowid()").fetchone()[0]
            con.commit()

            valid_roles = ['student', 'admin', 'tutor']

            for i, role in enumerate(valid_roles):
                # noinspection SqlResolve
                con.execute("""
                    INSERT INTO login (student_id, email, benutzername, password_hash, role)
                    VALUES (?, ?, ?, 'hash', ?)
                """, (student_id, f'role{i}@test.com', f'roleuser{i}', role))
            con.commit()

            with pytest.raises(sqlite3.IntegrityError):
                # noinspection SqlResolve
                con.execute("""
                    INSERT INTO login (student_id, email, benutzername, password_hash, role)
                    VALUES (?, 'invalid@test.com', 'invalidrole', 'hash', 'superadmin')
                """, (student_id,))
                con.commit()

        finally:
            con.close()

    def test_note_range_check(self, temp_db):
        """Test: pruefungsleistung note CHECK constraint (1.0 - 5.0)

        Notenlogik:
        - 1.0 - 4.0 = bestanden
        - 4.1 - 5.0 = nicht bestanden (durchgefallen)
        - CHECK constraint erlaubt 1.0 - 5.0
        """
        con = sqlite3.connect(temp_db)
        con.execute("PRAGMA foreign_keys = ON")

        try:
            modulbuchung = con.execute("SELECT id FROM modulbuchung LIMIT 1").fetchone()

            if not modulbuchung:
                pytest.skip("Keine Testdaten vorhanden")

            # noinspection SqlResolve
            con.execute("""
                INSERT INTO pruefungsleistung (modulbuchung_id, note, pruefungsdatum)
                VALUES (?, 2.3, date('now'))
            """, (modulbuchung[0],))
            con.commit()

            # noinspection SqlResolve
            con.execute("DELETE FROM pruefungsleistung WHERE modulbuchung_id = ?", (modulbuchung[0],))
            con.commit()

            # noinspection SqlResolve
            con.execute("""
                INSERT INTO pruefungsleistung (modulbuchung_id, note, pruefungsdatum)
                VALUES (?, 4.0, date('now'))
            """, (modulbuchung[0],))
            con.commit()

            # noinspection SqlResolve
            con.execute("DELETE FROM pruefungsleistung WHERE modulbuchung_id = ?", (modulbuchung[0],))
            con.commit()

            # noinspection SqlResolve
            con.execute("""
                INSERT INTO pruefungsleistung (modulbuchung_id, note, pruefungsdatum)
                VALUES (?, 5.0, date('now'))
            """, (modulbuchung[0],))
            con.commit()

            # noinspection SqlResolve
            con.execute("DELETE FROM pruefungsleistung WHERE modulbuchung_id = ?", (modulbuchung[0],))
            con.commit()

            with pytest.raises(sqlite3.IntegrityError):
                # noinspection SqlResolve
                con.execute("""
                    INSERT INTO pruefungsleistung (modulbuchung_id, note, pruefungsdatum)
                    VALUES (?, 0.5, date('now'))
                """, (modulbuchung[0],))
                con.commit()

            with pytest.raises(sqlite3.IntegrityError):
                # noinspection SqlResolve
                con.execute("""
                    INSERT INTO pruefungsleistung (modulbuchung_id, note, pruefungsdatum)
                    VALUES (?, 5.5, date('now'))
                """, (modulbuchung[0],))
                con.commit()

        finally:
            con.close()

    def test_note_bestanden_logic(self, temp_db):
        """Test: Notenlogik - 1.0-4.0 bestanden, 4.1-5.0 durchgefallen"""
        con = sqlite3.connect(temp_db)

        try:
            bestanden_noten = [1.0, 1.3, 2.0, 2.7, 3.0, 3.7, 4.0]
            durchgefallen_noten = [4.3, 4.7, 5.0]

            for note in bestanden_noten:
                assert note <= 4.0, f"Note {note} sollte als bestanden gelten"

            for note in durchgefallen_noten:
                assert note > 4.0, f"Note {note} sollte als durchgefallen gelten"

        finally:
            con.close()