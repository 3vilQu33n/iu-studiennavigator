# tests/unit/test_einschreibung_repository.py
"""
Unit Tests fuer EinschreibungRepository (repositories/einschreibung_repository.py)

Testet das EinschreibungRepository:
- insert() - Einschreibung anlegen
- get_by_id() - Einschreibung nach ID laden
- get_aktive_by_student() - Aktive Einschreibung eines Studenten
- get_all_by_student() - Alle Einschreibungen eines Studenten
- update_status() - Status aendern
- wechsel_zeitmodell() - Zeitmodell wechseln
- Fehlerbehandlung (NotFoundError, ValidationError, DatabaseError)
"""
from __future__ import annotations

import pytest
import sqlite3
import tempfile
import os
from datetime import date, timedelta
from unittest.mock import patch, MagicMock

# Mark this whole module as unit tests
pytestmark = pytest.mark.unit


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def einschreibung_repository_class():
    """Importiert EinschreibungRepository-Klasse"""
    try:
        from repositories.einschreibung_repository import EinschreibungRepository
        return EinschreibungRepository
    except ImportError:
        from repositories import EinschreibungRepository
        return EinschreibungRepository


@pytest.fixture
def einschreibung_class():
    """Importiert Einschreibung-Klasse"""
    try:
        from models import Einschreibung
        return Einschreibung
    except ImportError:
        from models.einschreibung import Einschreibung
        return Einschreibung


@pytest.fixture
def not_found_error():
    """Importiert NotFoundError"""
    try:
        from models import NotFoundError
        return NotFoundError
    except ImportError:
        try:
            from models.exceptions import NotFoundError
            return NotFoundError
        except ImportError:
            # Fallback
            class NotFoundError(Exception):
                pass
            return NotFoundError


@pytest.fixture
def validation_error():
    """Importiert ValidationError"""
    try:
        from models import ValidationError
        return ValidationError
    except ImportError:
        try:
            from models.exceptions import ValidationError
            return ValidationError
        except ImportError:
            # Fallback
            class ValidationError(Exception):
                pass
            return ValidationError


@pytest.fixture
def database_error():
    """Importiert DatabaseError"""
    try:
        from models import DatabaseError
        return DatabaseError
    except ImportError:
        try:
            from models.exceptions import DatabaseError
            return DatabaseError
        except ImportError:
            # Fallback
            class DatabaseError(Exception):
                pass
            return DatabaseError


@pytest.fixture
def temp_db():
    """Erstellt temporaere Test-Datenbank mit Schema"""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)

    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON;")

    # Erstelle notwendige Tabellen
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS student (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            matrikel_nr TEXT UNIQUE NOT NULL,
            vorname TEXT NOT NULL,
            nachname TEXT NOT NULL,
            login_id INTEGER
        );

        CREATE TABLE IF NOT EXISTS studiengang (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            grad TEXT NOT NULL,
            regel_semester INTEGER NOT NULL,
            beschreibung TEXT
        );

        CREATE TABLE IF NOT EXISTS zeitmodell (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            monate_pro_semester INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS einschreibung (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            studiengang_id INTEGER NOT NULL,
            zeitmodell_id INTEGER NOT NULL,
            start_datum TEXT NOT NULL,
            exmatrikulations_datum TEXT,
            status TEXT NOT NULL DEFAULT 'aktiv',
            FOREIGN KEY (student_id) REFERENCES student(id),
            FOREIGN KEY (studiengang_id) REFERENCES studiengang(id),
            FOREIGN KEY (zeitmodell_id) REFERENCES zeitmodell(id)
        );

        -- Testdaten einfuegen
        INSERT INTO student (id, matrikel_nr, vorname, nachname) VALUES
            (1, 'IU12345678', 'Max', 'Mustermann'),
            (2, 'IU87654321', 'Erika', 'Musterfrau');

        INSERT INTO studiengang (id, name, grad, regel_semester) VALUES
            (1, 'Informatik', 'B.Sc.', 6),
            (2, 'BWL', 'B.A.', 7);

        INSERT INTO zeitmodell (id, name, monate_pro_semester) VALUES
            (1, 'Vollzeit', 6),
            (2, 'Teilzeit', 12);

        INSERT INTO einschreibung (id, student_id, studiengang_id, zeitmodell_id, start_datum, status) VALUES
            (1, 1, 1, 1, '2024-01-01', 'aktiv'),
            (2, 2, 2, 2, '2023-06-01', 'aktiv'),
            (3, 1, 2, 1, '2020-01-01', 'exmatrikuliert');
    """)
    conn.commit()
    conn.close()

    yield path

    # Cleanup
    try:
        os.unlink(path)
    except OSError:
        pass


@pytest.fixture
def repository(einschreibung_repository_class, temp_db):
    """Erstellt Repository-Instanz mit Test-DB"""
    return einschreibung_repository_class(temp_db)


@pytest.fixture
def sample_einschreibung(einschreibung_class):
    """Erstellt Sample-Einschreibung fuer Tests"""
    return einschreibung_class(
        id=0,  # Wird beim Insert gesetzt
        student_id=1,
        studiengang_id=1,
        zeitmodell_id=1,
        start_datum=date.today(),
        exmatrikulations_datum=None,
        status='aktiv'
    )


# ============================================================================
# INITIALIZATION TESTS
# ============================================================================

class TestEinschreibungRepositoryInit:
    """Tests fuer Repository-Initialisierung"""

    def test_init_with_db_path(self, einschreibung_repository_class, temp_db):
        """Repository kann mit DB-Pfad initialisiert werden"""
        repo = einschreibung_repository_class(temp_db)

        assert repo.db_path == temp_db

    def test_init_stores_db_path(self, einschreibung_repository_class):
        """Repository speichert db_path"""
        repo = einschreibung_repository_class("/path/to/db.sqlite")

        assert repo.db_path == "/path/to/db.sqlite"


# ============================================================================
# INSERT TESTS
# ============================================================================

class TestInsert:
    """Tests fuer insert() Methode"""

    def test_insert_returns_id(self, repository, sample_einschreibung):
        """insert() gibt neue ID zurueck"""
        new_id = repository.insert(sample_einschreibung)

        assert isinstance(new_id, int)
        assert new_id > 0

    def test_insert_creates_record(self, repository, sample_einschreibung):
        """insert() erstellt Datensatz in DB"""
        new_id = repository.insert(sample_einschreibung)

        # Verify by loading
        loaded = repository.get_by_id(new_id)
        assert loaded.student_id == sample_einschreibung.student_id
        assert loaded.studiengang_id == sample_einschreibung.studiengang_id
        assert loaded.status == 'aktiv'

    def test_insert_with_exmatrikulations_datum(self, repository, einschreibung_class):
        """insert() mit Exmatrikulationsdatum"""
        einschreibung = einschreibung_class(
            id=0,
            student_id=2,
            studiengang_id=1,
            zeitmodell_id=2,
            start_datum=date(2023, 1, 1),
            exmatrikulations_datum=date(2024, 12, 31),
            status='exmatrikuliert'
        )

        new_id = repository.insert(einschreibung)
        loaded = repository.get_by_id(new_id)

        assert loaded.exmatrikulations_datum == date(2024, 12, 31)
        assert loaded.status == 'exmatrikuliert'

    def test_insert_increments_id(self, repository, einschreibung_class):
        """insert() inkrementiert IDs"""
        e1 = einschreibung_class(
            id=0,
            student_id=1,
            studiengang_id=1,
            zeitmodell_id=1,
            start_datum=date.today(),
            status='aktiv'
        )
        e2 = einschreibung_class(
            id=0,
            student_id=2,
            studiengang_id=2,
            zeitmodell_id=2,
            start_datum=date.today(),
            status='aktiv'
        )

        id1 = repository.insert(e1)
        id2 = repository.insert(e2)

        assert id2 > id1

    def test_insert_integrity_error_invalid_student(self, repository, einschreibung_class, database_error):
        """insert() wirft DatabaseError bei ungueltigem student_id (FK)"""
        einschreibung = einschreibung_class(
            id=0,
            student_id=999,  # Existiert nicht
            studiengang_id=1,
            zeitmodell_id=1,
            start_datum=date.today(),
            status='aktiv'
        )

        with pytest.raises(database_error):
            repository.insert(einschreibung)


# ============================================================================
# GET_BY_ID TESTS
# ============================================================================

class TestGetById:
    """Tests fuer get_by_id() Methode"""

    def test_get_by_id_existing(self, repository):
        """get_by_id() laedt existierende Einschreibung"""
        einschreibung = repository.get_by_id(1)

        assert einschreibung.id == 1
        assert einschreibung.student_id == 1
        assert einschreibung.studiengang_id == 1
        assert einschreibung.status == 'aktiv'

    def test_get_by_id_returns_einschreibung(self, repository, einschreibung_class):
        """get_by_id() gibt Einschreibung-Objekt zurueck"""
        einschreibung = repository.get_by_id(1)

        assert isinstance(einschreibung, einschreibung_class)

    def test_get_by_id_not_found(self, repository, not_found_error):
        """get_by_id() wirft NotFoundError wenn nicht gefunden"""
        with pytest.raises(not_found_error):
            repository.get_by_id(999)

    def test_get_by_id_correct_data(self, repository):
        """get_by_id() laedt korrekte Daten"""
        einschreibung = repository.get_by_id(2)

        assert einschreibung.id == 2
        assert einschreibung.student_id == 2
        assert einschreibung.studiengang_id == 2
        assert einschreibung.zeitmodell_id == 2
        assert einschreibung.start_datum == date(2023, 6, 1)


# ============================================================================
# GET_AKTIVE_BY_STUDENT TESTS
# ============================================================================

class TestGetAktiveByStudent:
    """Tests fuer get_aktive_by_student() Methode"""

    def test_get_aktive_by_student_existing(self, repository):
        """get_aktive_by_student() findet aktive Einschreibung"""
        einschreibung = repository.get_aktive_by_student(1)

        assert einschreibung.student_id == 1
        assert einschreibung.status == 'aktiv'

    def test_get_aktive_by_student_returns_einschreibung(self, repository, einschreibung_class):
        """get_aktive_by_student() gibt Einschreibung-Objekt zurueck"""
        einschreibung = repository.get_aktive_by_student(1)

        assert isinstance(einschreibung, einschreibung_class)

    def test_get_aktive_by_student_ignores_exmatrikuliert(self, repository, einschreibung_class, temp_db):
        """get_aktive_by_student() ignoriert exmatrikulierte Einschreibungen"""
        # Student 1 hat eine aktive (ID 1) und eine exmatrikulierte (ID 3) Einschreibung
        einschreibung = repository.get_aktive_by_student(1)

        # Sollte die aktive zurueckgeben
        assert einschreibung.status == 'aktiv'
        assert einschreibung.id == 1

    def test_get_aktive_by_student_not_found(self, repository, not_found_error, temp_db):
        """get_aktive_by_student() wirft NotFoundError wenn keine aktive"""
        # Setze alle Einschreibungen von Student 1 auf exmatrikuliert
        conn = sqlite3.connect(temp_db)
        conn.execute("UPDATE einschreibung SET status = 'exmatrikuliert' WHERE student_id = 1")
        conn.commit()
        conn.close()

        with pytest.raises(not_found_error):
            repository.get_aktive_by_student(1)

    def test_get_aktive_by_student_nonexistent_student(self, repository, not_found_error):
        """get_aktive_by_student() wirft NotFoundError fuer nicht existierenden Studenten"""
        with pytest.raises(not_found_error):
            repository.get_aktive_by_student(999)


# ============================================================================
# GET_ALL_BY_STUDENT TESTS
# ============================================================================

class TestGetAllByStudent:
    """Tests fuer get_all_by_student() Methode"""

    def test_get_all_by_student_returns_list(self, repository):
        """get_all_by_student() gibt Liste zurueck"""
        result = repository.get_all_by_student(1)

        assert isinstance(result, list)

    def test_get_all_by_student_correct_count(self, repository):
        """get_all_by_student() gibt alle Einschreibungen zurueck"""
        # Student 1 hat 2 Einschreibungen (aktiv und exmatrikuliert)
        result = repository.get_all_by_student(1)

        assert len(result) == 2

    def test_get_all_by_student_contains_einschreibungen(self, repository, einschreibung_class):
        """get_all_by_student() enthaelt Einschreibung-Objekte"""
        result = repository.get_all_by_student(1)

        for einschreibung in result:
            assert isinstance(einschreibung, einschreibung_class)

    def test_get_all_by_student_empty_for_nonexistent(self, repository):
        """get_all_by_student() gibt leere Liste fuer nicht existierenden Studenten"""
        result = repository.get_all_by_student(999)

        assert result == []

    def test_get_all_by_student_ordered_by_start_datum_desc(self, repository):
        """get_all_by_student() sortiert nach start_datum absteigend"""
        result = repository.get_all_by_student(1)

        # Neueste zuerst
        if len(result) >= 2:
            assert result[0].start_datum >= result[1].start_datum

    def test_get_all_by_student_includes_all_statuses(self, repository):
        """get_all_by_student() enthaelt alle Status"""
        result = repository.get_all_by_student(1)
        statuses = [e.status for e in result]

        assert 'aktiv' in statuses
        assert 'exmatrikuliert' in statuses


# ============================================================================
# UPDATE_STATUS TESTS
# ============================================================================

class TestUpdateStatus:
    """Tests fuer update_status() Methode"""

    def test_update_status_to_pausiert(self, repository):
        """update_status() aendert Status zu 'pausiert'"""
        repository.update_status(1, 'pausiert')

        loaded = repository.get_by_id(1)
        assert loaded.status == 'pausiert'

    def test_update_status_to_exmatrikuliert(self, repository):
        """update_status() aendert Status zu 'exmatrikuliert'"""
        repository.update_status(1, 'exmatrikuliert')

        loaded = repository.get_by_id(1)
        assert loaded.status == 'exmatrikuliert'

    def test_update_status_to_aktiv(self, repository):
        """update_status() aendert Status zu 'aktiv'"""
        # Erst pausieren, dann wieder aktivieren
        repository.update_status(1, 'pausiert')
        repository.update_status(1, 'aktiv')

        loaded = repository.get_by_id(1)
        assert loaded.status == 'aktiv'

    def test_update_status_invalid_raises_error(self, repository, validation_error):
        """update_status() wirft ValidationError bei ungueltigem Status"""
        with pytest.raises(validation_error):
            repository.update_status(1, 'ungueltig')

    def test_update_status_not_found(self, repository, not_found_error):
        """update_status() wirft NotFoundError wenn nicht gefunden"""
        with pytest.raises(not_found_error):
            repository.update_status(999, 'aktiv')

    def test_update_status_empty_string_raises_error(self, repository, validation_error):
        """update_status() wirft ValidationError bei leerem Status"""
        with pytest.raises(validation_error):
            repository.update_status(1, '')


# ============================================================================
# WECHSEL_ZEITMODELL TESTS
# ============================================================================

class TestWechselZeitmodell:
    """Tests fuer wechsel_zeitmodell() Methode"""

    def test_wechsel_zeitmodell_success(self, repository):
        """wechsel_zeitmodell() aendert Zeitmodell"""
        # Wechsel von Vollzeit (1) zu Teilzeit (2)
        repository.wechsel_zeitmodell(1, 2)

        loaded = repository.get_by_id(1)
        assert loaded.zeitmodell_id == 2

    def test_wechsel_zeitmodell_back(self, repository):
        """wechsel_zeitmodell() kann zurueckwechseln"""
        repository.wechsel_zeitmodell(1, 2)
        repository.wechsel_zeitmodell(1, 1)

        loaded = repository.get_by_id(1)
        assert loaded.zeitmodell_id == 1

    def test_wechsel_zeitmodell_invalid_id_zero(self, repository, validation_error):
        """wechsel_zeitmodell() wirft ValidationError bei ID 0"""
        with pytest.raises(validation_error):
            repository.wechsel_zeitmodell(1, 0)

    def test_wechsel_zeitmodell_invalid_id_negative(self, repository, validation_error):
        """wechsel_zeitmodell() wirft ValidationError bei negativer ID"""
        with pytest.raises(validation_error):
            repository.wechsel_zeitmodell(1, -1)

    def test_wechsel_zeitmodell_invalid_id_string(self, repository, validation_error):
        """wechsel_zeitmodell() wirft ValidationError bei String"""
        with pytest.raises(validation_error):
            repository.wechsel_zeitmodell(1, "zwei")

    def test_wechsel_zeitmodell_not_found(self, repository, not_found_error):
        """wechsel_zeitmodell() wirft NotFoundError wenn Einschreibung nicht gefunden"""
        with pytest.raises(not_found_error):
            repository.wechsel_zeitmodell(999, 2)


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

class TestErrorHandling:
    """Tests fuer Fehlerbehandlung"""

    def test_database_error_on_connection_failure(self, einschreibung_repository_class, database_error):
        """DatabaseError bei Verbindungsfehler"""
        repo = einschreibung_repository_class("/nonexistent/path/db.sqlite")

        with pytest.raises((database_error, Exception)):
            repo.get_by_id(1)

    def test_einschreibung_validates_on_creation(self, einschreibung_class):
        """Einschreibung validiert bereits bei Erstellung (nicht erst bei insert)"""
        # Einschreibung mit ungueltigem Status kann gar nicht erstellt werden
        # weil __post_init__ bereits validate() aufruft
        with pytest.raises((ValueError, Exception)):
            einschreibung_class(
                id=0,
                student_id=1,
                studiengang_id=1,
                zeitmodell_id=1,
                start_datum=date.today(),
                status='ungueltig'  # Schlaegt bereits bei Erstellung fehl
            )


# ============================================================================
# PRIVATE METHOD TESTS
# ============================================================================

class TestPrivateMethods:
    """Tests fuer private Hilfsmethoden"""

    def test_get_connection_returns_connection(self, repository):
        """__get_connection() gibt Connection zurueck"""
        # Zugriff auf private Methode fuer Test
        conn = repository._EinschreibungRepository__get_connection()

        assert isinstance(conn, sqlite3.Connection)
        conn.close()

    def test_get_connection_enables_foreign_keys(self, repository):
        """__get_connection() aktiviert Foreign Keys"""
        conn = repository._EinschreibungRepository__get_connection()

        # Pruefe ob FK aktiviert
        result = conn.execute("PRAGMA foreign_keys;").fetchone()
        assert result[0] == 1

        conn.close()


# ============================================================================
# INTEGRATION-LIKE TESTS
# ============================================================================

class TestIntegrationScenarios:
    """Tests fuer typische Nutzungsszenarien"""

    def test_full_lifecycle(self, repository, einschreibung_class):
        """Test: Vollstaendiger Lebenszyklus einer Einschreibung"""
        # 1. Neue Einschreibung erstellen
        neue_einschreibung = einschreibung_class(
            id=0,
            student_id=2,
            studiengang_id=1,
            zeitmodell_id=1,
            start_datum=date.today(),
            status='aktiv'
        )
        new_id = repository.insert(neue_einschreibung)

        # 2. Einschreibung laden
        loaded = repository.get_by_id(new_id)
        assert loaded.status == 'aktiv'

        # 3. Status aendern (pausieren)
        repository.update_status(new_id, 'pausiert')
        loaded = repository.get_by_id(new_id)
        assert loaded.status == 'pausiert'

        # 4. Zeitmodell wechseln
        repository.wechsel_zeitmodell(new_id, 2)
        loaded = repository.get_by_id(new_id)
        assert loaded.zeitmodell_id == 2

        # 5. Status aendern (exmatrikulieren)
        repository.update_status(new_id, 'exmatrikuliert')
        loaded = repository.get_by_id(new_id)
        assert loaded.status == 'exmatrikuliert'

    def test_multiple_einschreibungen_same_student(self, repository, einschreibung_class):
        """Test: Mehrere Einschreibungen fuer gleichen Studenten"""
        # Student 1 hat bereits Einschreibungen
        initial_count = len(repository.get_all_by_student(1))

        # Neue Einschreibung hinzufuegen
        neue = einschreibung_class(
            id=0,
            student_id=1,
            studiengang_id=2,
            zeitmodell_id=2,
            start_datum=date.today(),
            status='aktiv'
        )
        repository.insert(neue)

        # Pruefe ob Anzahl gestiegen
        final_count = len(repository.get_all_by_student(1))
        assert final_count == initial_count + 1

    def test_get_aktive_returns_newest(self, repository, einschreibung_class):
        """Test: get_aktive_by_student() gibt neueste aktive zurueck"""
        # Erstelle neuere aktive Einschreibung fuer Student 2
        neue = einschreibung_class(
            id=0,
            student_id=2,
            studiengang_id=1,
            zeitmodell_id=1,
            start_datum=date.today(),  # Heute (neuer als 2023-06-01)
            status='aktiv'
        )
        new_id = repository.insert(neue)

        # get_aktive_by_student sollte die neueste zurueckgeben
        aktive = repository.get_aktive_by_student(2)
        assert aktive.id == new_id


# ============================================================================
# EDGE CASES
# ============================================================================

class TestEdgeCases:
    """Tests fuer Randfaelle"""

    def test_get_by_id_with_zero(self, repository, not_found_error):
        """get_by_id() mit ID 0 wirft NotFoundError"""
        with pytest.raises(not_found_error):
            repository.get_by_id(0)

    def test_get_by_id_with_negative(self, repository, not_found_error):
        """get_by_id() mit negativer ID wirft NotFoundError"""
        with pytest.raises(not_found_error):
            repository.get_by_id(-1)

    def test_update_status_case_sensitive(self, repository, validation_error):
        """update_status() ist case-sensitive"""
        with pytest.raises(validation_error):
            repository.update_status(1, 'AKTIV')  # Grossgeschrieben

    def test_insert_preserves_date_format(self, repository, einschreibung_class):
        """insert() speichert Datum korrekt"""
        specific_date = date(2025, 6, 15)
        einschreibung = einschreibung_class(
            id=0,
            student_id=1,
            studiengang_id=1,
            zeitmodell_id=1,
            start_datum=specific_date,
            status='aktiv'
        )

        new_id = repository.insert(einschreibung)
        loaded = repository.get_by_id(new_id)

        assert loaded.start_datum == specific_date