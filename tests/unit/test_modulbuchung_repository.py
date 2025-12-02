# tests/unit/test_modulbuchung_repository.py
"""
Unit Tests fuer ModulbuchungRepository (repositories/modulbuchung_repository.py)

Testet das ModulbuchungRepository:
- create() - Modulbuchung/Pruefungsleistung anlegen (POLYMORPHIE)
- get_by_id() - Modulbuchung nach ID laden (polymorphe Rueckgabe)
- get_by_student() - Alle Buchungen eines Studenten
- update_status() - Status aktualisieren
- delete() - Buchung loeschen (CASCADE)
- check_if_booked() - Pruefen ob Modul gebucht
- validate_wahlmodul_booking() - Wahlmodul-Validierung
- get_wahlmodul_status() - Wahlmodul-Uebersicht

OOP-Konzepte:
- VERERBUNG: Pruefungsleistung erbt von Modulbuchung
- POLYMORPHIE: create() und get_by_id() behandeln beide Typen
"""
from __future__ import annotations

import pytest
import sqlite3
import tempfile
import os
from datetime import date, timedelta
from decimal import Decimal

# Mark this whole module as unit tests
pytestmark = pytest.mark.unit


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def modulbuchung_repository_class():
    """Importiert ModulbuchungRepository-Klasse"""
    try:
        from repositories import ModulbuchungRepository
        return ModulbuchungRepository
    except ImportError:
        from repositories.modulbuchung_repository import ModulbuchungRepository
        return ModulbuchungRepository


@pytest.fixture
def modulbuchung_class():
    """Importiert Modulbuchung-Klasse"""
    try:
        from models import Modulbuchung
        return Modulbuchung
    except ImportError:
        from models.modulbuchung import Modulbuchung
        return Modulbuchung


@pytest.fixture
def pruefungsleistung_class():
    """Importiert Pruefungsleistung-Klasse"""
    try:
        from models import Pruefungsleistung
        return Pruefungsleistung
    except ImportError:
        from models.pruefungsleistung import Pruefungsleistung
        return Pruefungsleistung


@pytest.fixture
def temp_db():
    """Erstellt temporaere Test-Datenbank mit vollstaendigem Schema"""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)

    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON;")

    # Erstelle vollstaendiges Schema
    conn.executescript("""
        -- Basis-Tabellen
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
            monate_pro_semester INTEGER NOT NULL,
            kosten_monat REAL NOT NULL DEFAULT 0.0
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

        CREATE TABLE IF NOT EXISTS modul (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            ects INTEGER NOT NULL,
            beschreibung TEXT
        );

        CREATE TABLE IF NOT EXISTS studiengang_modul (
            studiengang_id INTEGER NOT NULL,
            modul_id INTEGER NOT NULL,
            semester INTEGER NOT NULL,
            pflichtgrad TEXT NOT NULL DEFAULT 'Pflicht',
            wahlbereich TEXT,
            PRIMARY KEY (studiengang_id, modul_id),
            FOREIGN KEY (studiengang_id) REFERENCES studiengang(id),
            FOREIGN KEY (modul_id) REFERENCES modul(id)
        );

        CREATE TABLE IF NOT EXISTS modulbuchung (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            einschreibung_id INTEGER NOT NULL,
            modul_id INTEGER NOT NULL,
            buchungsdatum TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'gebucht',
            FOREIGN KEY (einschreibung_id) REFERENCES einschreibung(id),
            FOREIGN KEY (modul_id) REFERENCES modul(id)
        );

        CREATE TABLE IF NOT EXISTS pruefungsleistung (
            id INTEGER PRIMARY KEY,
            modulbuchung_id INTEGER,
            note REAL,
            pruefungsdatum TEXT,
            versuch INTEGER DEFAULT 1,
            max_versuche INTEGER DEFAULT 3,
            anmeldemodus TEXT DEFAULT 'online',
            thema TEXT,
            FOREIGN KEY (id) REFERENCES modulbuchung(id) ON DELETE CASCADE,
            FOREIGN KEY (modulbuchung_id) REFERENCES modulbuchung(id) ON DELETE CASCADE
        );

        -- Testdaten: Studenten
        INSERT INTO student (id, matrikel_nr, vorname, nachname) VALUES
            (1, 'IU12345678', 'Max', 'Mustermann'),
            (2, 'IU87654321', 'Erika', 'Musterfrau');

        -- Testdaten: Studiengang
        INSERT INTO studiengang (id, name, grad, regel_semester) VALUES
            (1, 'Informatik', 'B.Sc.', 6);

        -- Testdaten: Zeitmodell
        INSERT INTO zeitmodell (id, name, monate_pro_semester, kosten_monat) VALUES
            (1, 'Vollzeit', 6, 359.00);

        -- Testdaten: Einschreibungen
        INSERT INTO einschreibung (id, student_id, studiengang_id, zeitmodell_id, start_datum, status) VALUES
            (1, 1, 1, 1, '2024-01-01', 'aktiv'),
            (2, 2, 1, 1, '2024-01-01', 'aktiv');

        -- Testdaten: Module (Pflicht und Wahl)
        INSERT INTO modul (id, name, ects) VALUES
            (1, 'Mathematik I', 5),
            (2, 'Programmierung I', 5),
            (3, 'Datenbanken', 5),
            (10, 'Wahlmodul A1', 5),
            (11, 'Wahlmodul A2', 5),
            (20, 'Wahlmodul B1', 5),
            (21, 'Wahlmodul B2', 5),
            (30, 'Wahlmodul C1', 5),
            (31, 'Wahlmodul C2', 5);

        -- Testdaten: Studiengang-Modul-Zuordnung
        INSERT INTO studiengang_modul (studiengang_id, modul_id, semester, pflichtgrad, wahlbereich) VALUES
            (1, 1, 1, 'Pflicht', NULL),
            (1, 2, 1, 'Pflicht', NULL),
            (1, 3, 2, 'Pflicht', NULL),
            (1, 10, 5, 'Wahl', 'A'),
            (1, 11, 5, 'Wahl', 'A'),
            (1, 20, 6, 'Wahl', 'B'),
            (1, 21, 6, 'Wahl', 'B'),
            (1, 30, 6, 'Wahl', 'C'),
            (1, 31, 6, 'Wahl', 'C');
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
def temp_db_with_bookings(temp_db):
    """Test-DB mit vorhandenen Buchungen"""
    conn = sqlite3.connect(temp_db)
    conn.execute("PRAGMA foreign_keys = ON;")

    today = date.today()

    conn.executescript(f"""
        -- Modulbuchungen fuer Student 1
        INSERT INTO modulbuchung (id, einschreibung_id, modul_id, buchungsdatum, status) VALUES
            (1, 1, 1, '{today.isoformat()}', 'gebucht'),
            (2, 1, 2, '{today.isoformat()}', 'bestanden'),
            (3, 1, 10, '{today.isoformat()}', 'gebucht');

        -- Pruefungsleistung fuer Modulbuchung 2 (bestanden)
        INSERT INTO pruefungsleistung (id, modulbuchung_id, note, pruefungsdatum, versuch, max_versuche, anmeldemodus) VALUES
            (2, 2, 2.0, '{today.isoformat()}', 1, 3, 'online');

        -- Modulbuchung fuer Student 2
        INSERT INTO modulbuchung (id, einschreibung_id, modul_id, buchungsdatum, status) VALUES
            (4, 2, 1, '{today.isoformat()}', 'gebucht');
    """)
    conn.commit()
    conn.close()

    return temp_db


@pytest.fixture
def repository(modulbuchung_repository_class, temp_db):
    """Erstellt Repository-Instanz mit Test-DB"""
    return modulbuchung_repository_class(temp_db)


@pytest.fixture
def repository_with_bookings(modulbuchung_repository_class, temp_db_with_bookings):
    """Erstellt Repository-Instanz mit Test-DB inkl. Buchungen"""
    return modulbuchung_repository_class(temp_db_with_bookings)


@pytest.fixture
def sample_modulbuchung(modulbuchung_class):
    """Erstellt Sample-Modulbuchung fuer Tests"""
    return modulbuchung_class(
        id=0,
        einschreibung_id=1,
        modul_id=3,
        buchungsdatum=date.today(),
        status='gebucht'
    )


@pytest.fixture
def sample_pruefungsleistung(pruefungsleistung_class):
    """Erstellt Sample-Pruefungsleistung fuer Tests"""
    return pruefungsleistung_class(
        id=0,
        einschreibung_id=1,
        modul_id=3,
        buchungsdatum=date.today(),
        status='bestanden',
        note=Decimal('2.3'),
        pruefungsdatum=date.today(),
        versuch=1,
        max_versuche=3,
        anmeldemodus='online',
        thema=None
    )


# ============================================================================
# INITIALIZATION TESTS
# ============================================================================

class TestModulbuchungRepositoryInit:
    """Tests fuer Repository-Initialisierung"""

    def test_init_with_db_path(self, modulbuchung_repository_class, temp_db):
        """Repository kann mit DB-Pfad initialisiert werden"""
        repo = modulbuchung_repository_class(temp_db)

        assert repo.db_path == temp_db

    def test_init_stores_db_path(self, modulbuchung_repository_class):
        """Repository speichert db_path"""
        repo = modulbuchung_repository_class("/path/to/db.sqlite")

        assert repo.db_path == "/path/to/db.sqlite"


# ============================================================================
# CREATE TESTS
# ============================================================================

class TestCreate:
    """Tests fuer create() Methode"""

    def test_create_modulbuchung_returns_id(self, repository, sample_modulbuchung):
        """create() gibt neue ID zurueck"""
        new_id = repository.create(sample_modulbuchung)

        assert isinstance(new_id, int)
        assert new_id > 0

    def test_create_modulbuchung_stores_data(self, repository, sample_modulbuchung):
        """create() speichert Modulbuchung korrekt"""
        new_id = repository.create(sample_modulbuchung)

        loaded = repository.get_by_id(new_id)
        assert loaded is not None
        assert loaded.einschreibung_id == sample_modulbuchung.einschreibung_id
        assert loaded.modul_id == sample_modulbuchung.modul_id
        assert loaded.status == 'gebucht'

    def test_create_pruefungsleistung_polymorphic(self, repository, sample_pruefungsleistung, pruefungsleistung_class):
        """create() behandelt Pruefungsleistung polymorphisch"""
        new_id = repository.create(sample_pruefungsleistung)

        loaded = repository.get_by_id(new_id)
        assert loaded is not None
        assert isinstance(loaded, pruefungsleistung_class)
        assert loaded.note == Decimal('2.3')

    def test_create_pruefungsleistung_stores_all_fields(self, repository, pruefungsleistung_class):
        """create() speichert alle Pruefungsleistung-Felder"""
        pruefung = pruefungsleistung_class(
            id=0,
            einschreibung_id=1,
            modul_id=3,
            buchungsdatum=date.today(),
            status='bestanden',
            note=Decimal('1.7'),
            pruefungsdatum=date(2025, 6, 15),
            versuch=2,
            max_versuche=3,
            anmeldemodus='praesenz',
            thema='Testthema'
        )

        new_id = repository.create(pruefung)
        loaded = repository.get_by_id(new_id)

        assert loaded.note == Decimal('1.7')
        assert loaded.pruefungsdatum == date(2025, 6, 15)
        assert loaded.versuch == 2
        assert loaded.max_versuche == 3
        assert loaded.anmeldemodus == 'praesenz'
        assert loaded.thema == 'Testthema'

    def test_create_increments_id(self, repository, modulbuchung_class):
        """create() inkrementiert IDs"""
        b1 = modulbuchung_class(
            id=0,
            einschreibung_id=1,
            modul_id=1,
            buchungsdatum=date.today(),
            status='gebucht'
        )
        b2 = modulbuchung_class(
            id=0,
            einschreibung_id=1,
            modul_id=2,
            buchungsdatum=date.today(),
            status='gebucht'
        )

        id1 = repository.create(b1)
        id2 = repository.create(b2)

        assert id2 > id1

    def test_create_uses_today_as_default_buchungsdatum(self, repository, modulbuchung_class):
        """create() verwendet heute als Default fuer buchungsdatum"""
        buchung = modulbuchung_class(
            id=0,
            einschreibung_id=1,
            modul_id=3,
            buchungsdatum=None,  # Kein Datum
            status='gebucht'
        )

        new_id = repository.create(buchung)
        loaded = repository.get_by_id(new_id)

        assert loaded.buchungsdatum == date.today()


# ============================================================================
# GET_BY_ID TESTS
# ============================================================================

class TestGetById:
    """Tests fuer get_by_id() Methode"""

    def test_get_by_id_modulbuchung(self, repository_with_bookings, modulbuchung_class):
        """get_by_id() laedt Modulbuchung"""
        loaded = repository_with_bookings.get_by_id(1)

        assert loaded is not None
        assert isinstance(loaded, modulbuchung_class)
        assert loaded.id == 1
        assert loaded.modul_id == 1

    def test_get_by_id_pruefungsleistung_polymorphic(self, repository_with_bookings, pruefungsleistung_class):
        """get_by_id() gibt Pruefungsleistung zurueck wenn vorhanden (POLYMORPHIE)"""
        loaded = repository_with_bookings.get_by_id(2)

        assert loaded is not None
        assert isinstance(loaded, pruefungsleistung_class)
        assert loaded.note == Decimal('2.0')

    def test_get_by_id_not_found(self, repository):
        """get_by_id() gibt None zurueck wenn nicht gefunden"""
        result = repository.get_by_id(999)

        assert result is None

    def test_get_by_id_correct_status(self, repository_with_bookings):
        """get_by_id() laedt korrekten Status"""
        gebucht = repository_with_bookings.get_by_id(1)
        bestanden = repository_with_bookings.get_by_id(2)

        assert gebucht.status == 'gebucht'
        assert bestanden.status == 'bestanden'


# ============================================================================
# GET_BY_STUDENT TESTS
# ============================================================================

class TestGetByStudent:
    """Tests fuer get_by_student() Methode"""

    def test_get_by_student_returns_list(self, repository_with_bookings):
        """get_by_student() gibt Liste zurueck"""
        result = repository_with_bookings.get_by_student(1)

        assert isinstance(result, list)

    def test_get_by_student_correct_count(self, repository_with_bookings):
        """get_by_student() gibt korrekte Anzahl zurueck"""
        # Student 1 hat 3 Buchungen
        result = repository_with_bookings.get_by_student(1)

        assert len(result) == 3

    def test_get_by_student_polymorphic_results(self, repository_with_bookings, modulbuchung_class, pruefungsleistung_class):
        """get_by_student() gibt polymorphe Objekte zurueck"""
        result = repository_with_bookings.get_by_student(1)

        # Sollte mindestens eine Pruefungsleistung enthalten
        has_pruefungsleistung = any(isinstance(b, pruefungsleistung_class) for b in result)
        has_modulbuchung = any(isinstance(b, modulbuchung_class) and not isinstance(b, pruefungsleistung_class) for b in result)

        assert has_pruefungsleistung
        assert has_modulbuchung

    def test_get_by_student_empty_for_new_student(self, repository):
        """get_by_student() gibt leere Liste fuer Student ohne Buchungen"""
        result = repository.get_by_student(999)

        assert result == []

    def test_get_by_student_ordered_by_buchungsdatum_desc(self, repository_with_bookings):
        """get_by_student() sortiert nach buchungsdatum absteigend"""
        result = repository_with_bookings.get_by_student(1)

        if len(result) >= 2:
            # Neueste zuerst
            assert result[0].buchungsdatum >= result[-1].buchungsdatum


# ============================================================================
# UPDATE_STATUS TESTS
# ============================================================================

class TestUpdateStatus:
    """Tests fuer update_status() Methode"""

    def test_update_status_success(self, repository_with_bookings):
        """update_status() aendert Status erfolgreich"""
        result = repository_with_bookings.update_status(1, 'bestanden')

        assert result is True

        loaded = repository_with_bookings.get_by_id(1)
        assert loaded.status == 'bestanden'

    def test_update_status_to_verschiedene_status(self, repository_with_bookings):
        """update_status() kann verschiedene Status setzen"""
        for status in ['gebucht', 'bestanden', 'nicht_bestanden', 'anerkannt']:
            repository_with_bookings.update_status(1, status)
            loaded = repository_with_bookings.get_by_id(1)
            assert loaded.status == status

    def test_update_status_returns_true(self, repository_with_bookings):
        """update_status() gibt True zurueck"""
        result = repository_with_bookings.update_status(1, 'bestanden')

        assert result is True


# ============================================================================
# DELETE TESTS
# ============================================================================

class TestDelete:
    """Tests fuer delete() Methode"""

    def test_delete_success(self, repository_with_bookings):
        """delete() loescht Buchung erfolgreich"""
        # Buchung existiert
        before = repository_with_bookings.get_by_id(1)
        assert before is not None

        # Loeschen
        result = repository_with_bookings.delete(1)
        assert result is True

        # Buchung existiert nicht mehr
        after = repository_with_bookings.get_by_id(1)
        assert after is None

    def test_delete_cascades_to_pruefungsleistung(self, repository_with_bookings):
        """delete() loescht auch Pruefungsleistung (CASCADE)"""
        # Buchung 2 hat Pruefungsleistung
        before = repository_with_bookings.get_by_id(2)
        assert before is not None
        assert before.note is not None

        # Loeschen
        repository_with_bookings.delete(2)

        # Beide weg
        after = repository_with_bookings.get_by_id(2)
        assert after is None

    def test_delete_returns_true(self, repository_with_bookings):
        """delete() gibt True zurueck"""
        result = repository_with_bookings.delete(1)

        assert result is True


# ============================================================================
# CHECK_IF_BOOKED TESTS
# ============================================================================

class TestCheckIfBooked:
    """Tests fuer check_if_booked() Methode"""

    def test_check_if_booked_true(self, repository_with_bookings):
        """check_if_booked() gibt True wenn gebucht"""
        # Modul 1 ist von Einschreibung 1 gebucht
        result = repository_with_bookings.check_if_booked(
            einschreibung_id=1,
            modul_id=1
        )

        assert result is True

    def test_check_if_booked_false(self, repository_with_bookings):
        """check_if_booked() gibt False wenn nicht gebucht"""
        # Modul 3 ist nicht von Einschreibung 1 gebucht
        result = repository_with_bookings.check_if_booked(
            einschreibung_id=1,
            modul_id=3
        )

        assert result is False

    def test_check_if_booked_different_einschreibung(self, repository_with_bookings):
        """check_if_booked() unterscheidet Einschreibungen"""
        # Modul 2 ist nur von Einschreibung 1 gebucht, nicht von 2
        result = repository_with_bookings.check_if_booked(
            einschreibung_id=2,
            modul_id=2
        )

        assert result is False


# ============================================================================
# VALIDATE_WAHLMODUL_BOOKING TESTS
# ============================================================================

class TestValidateWahlmodulBooking:
    """Tests fuer validate_wahlmodul_booking() Methode"""

    def test_validate_allows_new_wahlmodul(self, repository):
        """validate_wahlmodul_booking() erlaubt neues Wahlmodul"""
        is_valid, error = repository.validate_wahlmodul_booking(
            einschreibung_id=1,
            modul_id=10,  # Wahlmodul A1
            studiengang_id=1
        )

        assert is_valid is True
        assert error == ""

    def test_validate_blocks_already_booked(self, repository_with_bookings):
        """validate_wahlmodul_booking() blockiert bereits gebuchtes Modul"""
        # Modul 10 ist bereits gebucht (siehe temp_db_with_bookings)
        is_valid, error = repository_with_bookings.validate_wahlmodul_booking(
            einschreibung_id=1,
            modul_id=10,
            studiengang_id=1
        )

        assert is_valid is False
        assert "bereits gebucht" in error

    def test_validate_blocks_same_wahlbereich(self, repository_with_bookings):
        """validate_wahlmodul_booking() blockiert zweites Modul im gleichen Wahlbereich"""
        # Student 1 hat Wahlmodul A1 (modul_id=10) gebucht
        # Versuch Wahlmodul A2 (modul_id=11) zu buchen sollte fehlschlagen
        is_valid, error = repository_with_bookings.validate_wahlmodul_booking(
            einschreibung_id=1,
            modul_id=11,  # Wahlmodul A2, auch Bereich A
            studiengang_id=1
        )

        assert is_valid is False
        assert "Wahlbereich A" in error

    def test_validate_allows_different_wahlbereich(self, repository_with_bookings):
        """validate_wahlmodul_booking() erlaubt Modul in anderem Wahlbereich"""
        # Student 1 hat Wahlmodul A1 gebucht
        # Wahlmodul B1 sollte erlaubt sein
        is_valid, error = repository_with_bookings.validate_wahlmodul_booking(
            einschreibung_id=1,
            modul_id=20,  # Wahlmodul B1
            studiengang_id=1
        )

        assert is_valid is True
        assert error == ""

    def test_validate_allows_pflichtmodul(self, repository):
        """validate_wahlmodul_booking() erlaubt Pflichtmodul ohne Einschraenkung"""
        is_valid, error = repository.validate_wahlmodul_booking(
            einschreibung_id=1,
            modul_id=1,  # Mathematik I (Pflicht)
            studiengang_id=1
        )

        assert is_valid is True
        assert error == ""

    def test_validate_returns_tuple(self, repository):
        """validate_wahlmodul_booking() gibt Tuple zurueck"""
        result = repository.validate_wahlmodul_booking(
            einschreibung_id=1,
            modul_id=10,
            studiengang_id=1
        )

        assert isinstance(result, tuple)
        assert len(result) == 2


# ============================================================================
# GET_WAHLMODUL_STATUS TESTS
# ============================================================================

class TestGetWahlmodulStatus:
    """Tests fuer get_wahlmodul_status() Methode"""

    def test_get_wahlmodul_status_returns_dict(self, repository):
        """get_wahlmodul_status() gibt Dictionary zurueck"""
        result = repository.get_wahlmodul_status(
            einschreibung_id=1,
            studiengang_id=1
        )

        assert isinstance(result, dict)

    def test_get_wahlmodul_status_contains_all_bereiche(self, repository):
        """get_wahlmodul_status() enthaelt alle Wahlbereiche"""
        result = repository.get_wahlmodul_status(
            einschreibung_id=1,
            studiengang_id=1
        )

        assert 'A' in result
        assert 'B' in result
        assert 'C' in result

    def test_get_wahlmodul_status_structure(self, repository):
        """get_wahlmodul_status() hat korrekte Struktur"""
        result = repository.get_wahlmodul_status(
            einschreibung_id=1,
            studiengang_id=1
        )

        for bereich in ['A', 'B', 'C']:
            assert 'semester' in result[bereich]
            assert 'modul' in result[bereich]
            assert 'gebucht' in result[bereich]

    def test_get_wahlmodul_status_shows_booked(self, repository_with_bookings):
        """get_wahlmodul_status() zeigt gebuchte Module"""
        result = repository_with_bookings.get_wahlmodul_status(
            einschreibung_id=1,
            studiengang_id=1
        )

        # Student 1 hat Wahlmodul A1 gebucht
        assert result['A']['gebucht'] is True
        assert result['A']['modul'] == 'Wahlmodul A1'

    def test_get_wahlmodul_status_shows_not_booked(self, repository_with_bookings):
        """get_wahlmodul_status() zeigt nicht gebuchte Bereiche"""
        result = repository_with_bookings.get_wahlmodul_status(
            einschreibung_id=1,
            studiengang_id=1
        )

        # Student 1 hat B und C nicht gebucht
        assert result['B']['gebucht'] is False
        assert result['B']['modul'] is None
        assert result['C']['gebucht'] is False
        assert result['C']['modul'] is None

    def test_get_wahlmodul_status_empty_for_new_student(self, repository):
        """get_wahlmodul_status() zeigt alle leer fuer neuen Studenten"""
        result = repository.get_wahlmodul_status(
            einschreibung_id=2,
            studiengang_id=1
        )

        for bereich in ['A', 'B', 'C']:
            assert result[bereich]['gebucht'] is False
            assert result[bereich]['modul'] is None


# ============================================================================
# PRIVATE METHOD TESTS
# ============================================================================

class TestPrivateMethods:
    """Tests fuer private Hilfsmethoden"""

    def test_get_connection_returns_connection(self, repository):
        """__get_connection() gibt Connection zurueck"""
        conn = repository._ModulbuchungRepository__get_connection()

        assert isinstance(conn, sqlite3.Connection)
        conn.close()

    def test_get_connection_enables_foreign_keys(self, repository):
        """__get_connection() aktiviert Foreign Keys"""
        conn = repository._ModulbuchungRepository__get_connection()

        result = conn.execute("PRAGMA foreign_keys;").fetchone()
        assert result[0] == 1

        conn.close()


# ============================================================================
# POLYMORPHISM TESTS (OOP)
# ============================================================================

class TestPolymorphism:
    """Tests fuer polymorphes Verhalten (VERERBUNG/POLYMORPHIE)"""

    def test_create_accepts_both_types(self, repository, sample_modulbuchung, sample_pruefungsleistung):
        """create() akzeptiert Modulbuchung und Pruefungsleistung"""
        id1 = repository.create(sample_modulbuchung)
        id2 = repository.create(sample_pruefungsleistung)

        assert id1 > 0
        assert id2 > 0

    def test_get_by_id_returns_correct_type(self, repository, sample_modulbuchung, sample_pruefungsleistung,
                                            modulbuchung_class, pruefungsleistung_class):
        """get_by_id() gibt korrekten Typ zurueck"""
        id1 = repository.create(sample_modulbuchung)
        id2 = repository.create(sample_pruefungsleistung)

        loaded1 = repository.get_by_id(id1)
        loaded2 = repository.get_by_id(id2)

        # loaded1 sollte Modulbuchung sein (nicht Pruefungsleistung)
        assert isinstance(loaded1, modulbuchung_class)
        # loaded2 sollte Pruefungsleistung sein
        assert isinstance(loaded2, pruefungsleistung_class)

    def test_pruefungsleistung_inherits_from_modulbuchung(self, sample_pruefungsleistung, modulbuchung_class):
        """Pruefungsleistung erbt von Modulbuchung"""
        assert isinstance(sample_pruefungsleistung, modulbuchung_class)


# ============================================================================
# INTEGRATION-LIKE TESTS
# ============================================================================

class TestIntegrationScenarios:
    """Tests fuer typische Nutzungsszenarien"""

    def test_full_booking_lifecycle(self, repository, modulbuchung_class, pruefungsleistung_class):
        """Test: Vollstaendiger Buchungs-Lebenszyklus"""
        # 1. Modulbuchung erstellen
        buchung = modulbuchung_class(
            id=0,
            einschreibung_id=1,
            modul_id=3,
            buchungsdatum=date.today(),
            status='gebucht'
        )
        buchung_id = repository.create(buchung)

        # 2. Status pruefen
        loaded = repository.get_by_id(buchung_id)
        assert loaded.status == 'gebucht'

        # 3. Status aktualisieren
        repository.update_status(buchung_id, 'bestanden')
        loaded = repository.get_by_id(buchung_id)
        assert loaded.status == 'bestanden'

    def test_wahlmodul_workflow(self, repository, modulbuchung_class):
        """Test: Wahlmodul-Buchungs-Workflow"""
        # 1. Validierung vor Buchung
        is_valid, _ = repository.validate_wahlmodul_booking(
            einschreibung_id=1,
            modul_id=10,  # Wahlmodul A1
            studiengang_id=1
        )
        assert is_valid is True

        # 2. Buchung erstellen
        buchung = modulbuchung_class(
            id=0,
            einschreibung_id=1,
            modul_id=10,
            buchungsdatum=date.today(),
            status='gebucht'
        )
        repository.create(buchung)

        # 3. Status pruefen
        status = repository.get_wahlmodul_status(
            einschreibung_id=1,
            studiengang_id=1
        )
        assert status['A']['gebucht'] is True

        # 4. Zweites A-Modul sollte blockiert sein
        is_valid, _ = repository.validate_wahlmodul_booking(
            einschreibung_id=1,
            modul_id=11,  # Wahlmodul A2
            studiengang_id=1
        )
        assert is_valid is False


# ============================================================================
# EDGE CASES
# ============================================================================

class TestEdgeCases:
    """Tests fuer Randfaelle"""

    def test_get_by_id_with_zero(self, repository):
        """get_by_id() mit ID 0 gibt None zurueck"""
        result = repository.get_by_id(0)

        assert result is None

    def test_get_by_id_with_negative(self, repository):
        """get_by_id() mit negativer ID gibt None zurueck"""
        result = repository.get_by_id(-1)

        assert result is None

    def test_check_if_booked_nonexistent_einschreibung(self, repository):
        """check_if_booked() mit nicht existierender Einschreibung"""
        result = repository.check_if_booked(
            einschreibung_id=999,
            modul_id=1
        )

        assert result is False

    def test_check_if_booked_nonexistent_modul(self, repository):
        """check_if_booked() mit nicht existierendem Modul"""
        result = repository.check_if_booked(
            einschreibung_id=1,
            modul_id=999
        )

        assert result is False