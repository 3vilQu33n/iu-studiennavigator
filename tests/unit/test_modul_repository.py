# tests/unit/test_modul_repository.py
"""
Unit Tests fuer ModulRepository (repositories/modul_repository.py)

Testet das ModulRepository und ModulDTO:
- ModulDTO: to_dict(), is_wahlmodul()
- get_modules_for_semester() - Module eines Semesters mit Buchungsstatus
- get_gebuchte_wahlmodule() - Bereits gebuchte Wahlmodule
- get_available_wahlmodule() - Verfuegbare Wahlmodule
- Fehlerbehandlung und Edge Cases
"""
from __future__ import annotations

import pytest
import sqlite3
import tempfile
import os
from datetime import date

# Mark this whole module as unit tests
pytestmark = pytest.mark.unit


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def modul_repository_class():
    """Importiert ModulRepository-Klasse"""
    try:
        from repositories.modul_repository import ModulRepository
        return ModulRepository
    except ImportError:
        from repositories import ModulRepository
        return ModulRepository


@pytest.fixture
def modul_dto_class():
    """Importiert ModulDTO-Klasse"""
    try:
        from repositories import ModulDTO
        return ModulDTO
    except ImportError:
        from repositories.modul_repository import ModulDTO
        return ModulDTO


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
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            modulbuchung_id INTEGER NOT NULL,
            note REAL,
            pruefungsdatum TEXT,
            versuch INTEGER DEFAULT 1,
            FOREIGN KEY (modulbuchung_id) REFERENCES modulbuchung(id)
        );

        CREATE TABLE IF NOT EXISTS pruefungsart (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kuerzel TEXT NOT NULL UNIQUE,
            anzeigename TEXT NOT NULL,
            hat_unterteilung INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS modul_pruefungsart (
            modul_id INTEGER NOT NULL,
            pruefungsart_id INTEGER NOT NULL,
            ist_standard INTEGER DEFAULT 0,
            reihenfolge INTEGER DEFAULT 0,
            PRIMARY KEY (modul_id, pruefungsart_id),
            FOREIGN KEY (modul_id) REFERENCES modul(id),
            FOREIGN KEY (pruefungsart_id) REFERENCES pruefungsart(id)
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

        -- Testdaten: Module
        INSERT INTO modul (id, name, ects) VALUES
            (1, 'Mathematik I', 5),
            (2, 'Programmierung I', 5),
            (3, 'Datenbanken', 5),
            (4, 'Software Engineering', 5),
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
            (1, 4, 2, 'Pflicht', NULL),
            (1, 10, 5, 'Wahl', 'A'),
            (1, 11, 5, 'Wahl', 'A'),
            (1, 20, 5, 'Wahl', 'B'),
            (1, 21, 5, 'Wahl', 'B'),
            (1, 30, 6, 'Wahl', 'C'),
            (1, 31, 6, 'Wahl', 'C');

        -- Testdaten: Pruefungsarten
        INSERT INTO pruefungsart (id, kuerzel, anzeigename, hat_unterteilung) VALUES
            (1, 'KLAUSUR', 'Klausur', 1),
            (2, 'PORTFOLIO', 'Portfolio', 0),
            (3, 'WORKBOOK', 'Advanced Workbook', 0);

        -- Testdaten: Modul-Pruefungsarten-Zuordnung
        INSERT INTO modul_pruefungsart (modul_id, pruefungsart_id, ist_standard, reihenfolge) VALUES
            (1, 1, 1, 1),
            (2, 1, 1, 1),
            (2, 2, 0, 2),
            (3, 1, 1, 1),
            (4, 3, 1, 1);

        -- Testdaten: Modulbuchungen (Student 1)
        INSERT INTO modulbuchung (id, einschreibung_id, modul_id, buchungsdatum, status) VALUES
            (1, 1, 1, '2024-01-15', 'gebucht'),
            (2, 1, 2, '2024-01-15', 'bestanden'),
            (3, 1, 10, '2024-06-01', 'gebucht');

        -- Testdaten: Pruefungsleistungen
        INSERT INTO pruefungsleistung (id, modulbuchung_id, note, pruefungsdatum, versuch) VALUES
            (1, 2, 2.0, '2024-03-15', 1);
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
def repository(modul_repository_class, temp_db):
    """Erstellt Repository-Instanz mit Test-DB"""
    return modul_repository_class(temp_db)


@pytest.fixture
def sample_modul_dto(modul_dto_class):
    """Erstellt Sample-ModulDTO fuer Tests"""
    return modul_dto_class(
        modul_id=1,
        name="Mathematik I",
        ects=5,
        pflichtgrad="Pflicht",
        semester=1,
        status="offen",
        buchbar=True,
        note=None,
        wahlbereich=None,
        erlaubte_pruefungsarten=[
            {'wert': 'klausur', 'anzeigename': 'Klausur', 'hat_unterteilung': True, 'ist_standard': True}
        ]
    )


@pytest.fixture
def wahl_modul_dto(modul_dto_class):
    """Erstellt Wahlmodul-DTO fuer Tests"""
    return modul_dto_class(
        modul_id=10,
        name="Wahlmodul A1",
        ects=5,
        pflichtgrad="Wahl",
        semester=5,
        status="offen",
        buchbar=True,
        note=None,
        wahlbereich="A",
        erlaubte_pruefungsarten=[]
    )


# ============================================================================
# MODUL_DTO TESTS
# ============================================================================

class TestModulDTOInit:
    """Tests fuer ModulDTO-Initialisierung"""

    def test_init_with_all_fields(self, modul_dto_class):
        """Initialisierung mit allen Feldern"""
        dto = modul_dto_class(
            modul_id=1,
            name="Test Modul",
            ects=5,
            pflichtgrad="Pflicht",
            semester=1,
            status="offen",
            buchbar=True,
            note=2.3,
            wahlbereich="A",
            erlaubte_pruefungsarten=[{'wert': 'klausur'}]
        )

        assert dto.modul_id == 1
        assert dto.name == "Test Modul"
        assert dto.ects == 5
        assert dto.pflichtgrad == "Pflicht"
        assert dto.semester == 1
        assert dto.status == "offen"
        assert dto.buchbar is True
        assert dto.note == 2.3
        assert dto.wahlbereich == "A"
        assert len(dto.erlaubte_pruefungsarten) == 1

    def test_init_with_defaults(self, modul_dto_class):
        """Initialisierung mit Default-Werten"""
        dto = modul_dto_class(
            modul_id=1,
            name="Test",
            ects=5,
            pflichtgrad="Pflicht",
            semester=1,
            status="offen",
            buchbar=True
        )

        assert dto.note is None
        assert dto.wahlbereich is None
        assert dto.erlaubte_pruefungsarten is None


class TestModulDTOToDict:
    """Tests fuer ModulDTO.to_dict() Methode"""

    def test_to_dict_contains_all_fields(self, sample_modul_dto):
        """to_dict() enthaelt alle Felder"""
        d = sample_modul_dto.to_dict()

        assert 'modul_id' in d
        assert 'name' in d
        assert 'ects' in d
        assert 'pflichtgrad' in d
        assert 'semester' in d
        assert 'status' in d
        assert 'buchbar' in d
        assert 'note' in d
        assert 'wahlbereich' in d
        assert 'erlaubte_pruefungsarten' in d

    def test_to_dict_correct_values(self, sample_modul_dto):
        """to_dict() enthaelt korrekte Werte"""
        d = sample_modul_dto.to_dict()

        assert d['modul_id'] == 1
        assert d['name'] == "Mathematik I"
        assert d['ects'] == 5
        assert d['pflichtgrad'] == "Pflicht"
        assert d['semester'] == 1
        assert d['status'] == "offen"
        assert d['buchbar'] is True

    def test_to_dict_note_float_conversion(self, modul_dto_class):
        """to_dict() konvertiert Note zu float"""
        dto = modul_dto_class(
            modul_id=1,
            name="Test",
            ects=5,
            pflichtgrad="Pflicht",
            semester=1,
            status="bestanden",
            buchbar=False,
            note=2.3
        )

        d = dto.to_dict()
        assert d['note'] == 2.3
        assert isinstance(d['note'], float)

    def test_to_dict_note_none(self, sample_modul_dto):
        """to_dict() gibt None fuer fehlende Note"""
        d = sample_modul_dto.to_dict()
        assert d['note'] is None

    def test_to_dict_erlaubte_pruefungsarten_empty_list(self, modul_dto_class):
        """to_dict() gibt leere Liste wenn keine Pruefungsarten"""
        dto = modul_dto_class(
            modul_id=1,
            name="Test",
            ects=5,
            pflichtgrad="Pflicht",
            semester=1,
            status="offen",
            buchbar=True,
            erlaubte_pruefungsarten=None
        )

        d = dto.to_dict()
        assert d['erlaubte_pruefungsarten'] == []

    def test_to_dict_is_json_serializable(self, sample_modul_dto):
        """to_dict() Ergebnis ist JSON-serialisierbar"""
        import json

        d = sample_modul_dto.to_dict()
        json_str = json.dumps(d)
        assert isinstance(json_str, str)


class TestModulDTOIsWahlmodul:
    """Tests fuer ModulDTO.is_wahlmodul() Methode"""

    def test_is_wahlmodul_true(self, wahl_modul_dto):
        """is_wahlmodul() ist True wenn wahlbereich gesetzt"""
        assert wahl_modul_dto.wahlbereich == "A"
        assert wahl_modul_dto.is_wahlmodul() is True

    def test_is_wahlmodul_false(self, sample_modul_dto):
        """is_wahlmodul() ist False wenn wahlbereich None"""
        assert sample_modul_dto.wahlbereich is None
        assert sample_modul_dto.is_wahlmodul() is False

    def test_is_wahlmodul_all_bereiche(self, modul_dto_class):
        """is_wahlmodul() funktioniert fuer alle Wahlbereiche"""
        for bereich in ['A', 'B', 'C']:
            dto = modul_dto_class(
                modul_id=1,
                name="Test",
                ects=5,
                pflichtgrad="Wahl",
                semester=5,
                status="offen",
                buchbar=True,
                wahlbereich=bereich
            )
            assert dto.is_wahlmodul() is True


# ============================================================================
# REPOSITORY INITIALIZATION TESTS
# ============================================================================

class TestModulRepositoryInit:
    """Tests fuer Repository-Initialisierung"""

    def test_init_with_db_path(self, modul_repository_class, temp_db):
        """Repository kann mit DB-Pfad initialisiert werden"""
        repo = modul_repository_class(temp_db)

        assert repo.db_path == temp_db

    def test_init_stores_db_path(self, modul_repository_class):
        """Repository speichert db_path"""
        repo = modul_repository_class("/path/to/db.sqlite")

        assert repo.db_path == "/path/to/db.sqlite"


# ============================================================================
# GET_MODULES_FOR_SEMESTER TESTS
# ============================================================================

class TestGetModulesForSemester:
    """Tests fuer get_modules_for_semester() Methode"""

    def test_returns_list(self, repository):
        """get_modules_for_semester() gibt Liste zurueck"""
        result = repository.get_modules_for_semester(
            studiengang_id=1,
            semester=1,
            student_id=1
        )

        assert isinstance(result, list)

    def test_returns_modul_dtos(self, repository, modul_dto_class):
        """get_modules_for_semester() gibt ModulDTO-Objekte zurueck"""
        result = repository.get_modules_for_semester(
            studiengang_id=1,
            semester=1,
            student_id=1
        )

        for module in result:
            assert isinstance(module, modul_dto_class)

    def test_correct_count_semester_1(self, repository):
        """get_modules_for_semester() gibt korrekte Anzahl fuer Semester 1"""
        result = repository.get_modules_for_semester(
            studiengang_id=1,
            semester=1,
            student_id=1
        )

        # Semester 1 hat 2 Module (Mathematik I, Programmierung I)
        assert len(result) == 2

    def test_correct_count_semester_2(self, repository):
        """get_modules_for_semester() gibt korrekte Anzahl fuer Semester 2"""
        result = repository.get_modules_for_semester(
            studiengang_id=1,
            semester=2,
            student_id=1
        )

        # Semester 2 hat 2 Module (Datenbanken, Software Engineering)
        assert len(result) == 2

    def test_empty_for_nonexistent_semester(self, repository):
        """get_modules_for_semester() gibt leere Liste fuer nicht existierendes Semester"""
        result = repository.get_modules_for_semester(
            studiengang_id=1,
            semester=99,
            student_id=1
        )

        assert result == []

    def test_status_gebucht(self, repository):
        """get_modules_for_semester() zeigt Status 'gebucht' korrekt"""
        result = repository.get_modules_for_semester(
            studiengang_id=1,
            semester=1,
            student_id=1
        )

        # Mathematik I (modul_id=1) ist gebucht
        mathe = next((m for m in result if m.modul_id == 1), None)
        assert mathe is not None
        assert mathe.status == 'gebucht'
        assert mathe.buchbar is False

    def test_status_bestanden_with_note(self, repository):
        """get_modules_for_semester() zeigt Status 'bestanden' mit Note"""
        result = repository.get_modules_for_semester(
            studiengang_id=1,
            semester=1,
            student_id=1
        )

        # Programmierung I (modul_id=2) ist bestanden mit Note 2.0
        prog = next((m for m in result if m.modul_id == 2), None)
        assert prog is not None
        assert prog.status == 'bestanden'
        assert prog.note == 2.0
        assert prog.buchbar is False

    def test_status_offen(self, repository):
        """get_modules_for_semester() zeigt Status 'offen' fuer nicht gebuchte"""
        result = repository.get_modules_for_semester(
            studiengang_id=1,
            semester=2,
            student_id=1
        )

        # Semester 2 Module sind nicht gebucht
        for module in result:
            assert module.status == 'offen'
            assert module.buchbar is True

    def test_includes_erlaubte_pruefungsarten(self, repository):
        """get_modules_for_semester() enthaelt erlaubte Pruefungsarten"""
        result = repository.get_modules_for_semester(
            studiengang_id=1,
            semester=1,
            student_id=1
        )

        for module in result:
            assert module.erlaubte_pruefungsarten is not None
            assert isinstance(module.erlaubte_pruefungsarten, list)

    def test_pruefungsarten_structure(self, repository):
        """get_modules_for_semester() Pruefungsarten haben korrekte Struktur"""
        result = repository.get_modules_for_semester(
            studiengang_id=1,
            semester=1,
            student_id=1
        )

        # Programmierung I hat 2 Pruefungsarten (Klausur, Portfolio)
        prog = next((m for m in result if m.modul_id == 2), None)
        assert prog is not None

        if prog.erlaubte_pruefungsarten:
            for pa in prog.erlaubte_pruefungsarten:
                assert 'wert' in pa
                assert 'anzeigename' in pa
                assert 'hat_unterteilung' in pa

    def test_wahlmodule_have_wahlbereich(self, repository):
        """get_modules_for_semester() zeigt Wahlbereich fuer Wahlmodule"""
        result = repository.get_modules_for_semester(
            studiengang_id=1,
            semester=5,
            student_id=1
        )

        # Semester 5 hat Wahlmodule in Bereich A und B
        for module in result:
            assert module.wahlbereich in ['A', 'B']
            assert module.is_wahlmodul() is True


# ============================================================================
# GET_GEBUCHTE_WAHLMODULE TESTS
# ============================================================================

class TestGetGebuchteWahlmodule:
    """Tests fuer get_gebuchte_wahlmodule() Methode"""

    def test_returns_dict(self, repository):
        """get_gebuchte_wahlmodule() gibt Dictionary zurueck"""
        result = repository.get_gebuchte_wahlmodule(
            student_id=1,
            studiengang_id=1
        )

        assert isinstance(result, dict)

    def test_contains_all_wahlbereiche(self, repository):
        """get_gebuchte_wahlmodule() enthaelt alle Wahlbereiche"""
        result = repository.get_gebuchte_wahlmodule(
            student_id=1,
            studiengang_id=1
        )

        assert 'A' in result
        assert 'B' in result
        assert 'C' in result
        assert 'gebuchte_modul_ids' in result

    def test_gebuchte_modul_ids_is_list(self, repository):
        """get_gebuchte_wahlmodule() gebuchte_modul_ids ist Liste"""
        result = repository.get_gebuchte_wahlmodule(
            student_id=1,
            studiengang_id=1
        )

        assert isinstance(result['gebuchte_modul_ids'], list)

    def test_finds_gebuchte_wahlmodule(self, repository):
        """get_gebuchte_wahlmodule() findet gebuchte Wahlmodule"""
        # Student 1 hat Wahlmodul A1 (modul_id=10) gebucht
        result = repository.get_gebuchte_wahlmodule(
            student_id=1,
            studiengang_id=1
        )

        assert result['A'] is not None
        assert result['A']['modul_id'] == 10
        assert result['A']['name'] == 'Wahlmodul A1'

    def test_not_gebuchte_are_none(self, repository):
        """get_gebuchte_wahlmodule() nicht gebuchte sind None"""
        result = repository.get_gebuchte_wahlmodule(
            student_id=1,
            studiengang_id=1
        )

        # Student 1 hat kein Wahlmodul B oder C gebucht
        assert result['B'] is None
        assert result['C'] is None

    def test_empty_for_new_student(self, repository):
        """get_gebuchte_wahlmodule() leer fuer Student ohne Wahlmodule"""
        result = repository.get_gebuchte_wahlmodule(
            student_id=2,  # Student 2 hat keine Wahlmodule gebucht
            studiengang_id=1
        )

        assert result['A'] is None
        assert result['B'] is None
        assert result['C'] is None
        assert result['gebuchte_modul_ids'] == []


# ============================================================================
# GET_AVAILABLE_WAHLMODULE TESTS
# ============================================================================

class TestGetAvailableWahlmodule:
    """Tests fuer get_available_wahlmodule() Methode"""

    def test_returns_list(self, repository):
        """get_available_wahlmodule() gibt Liste zurueck"""
        result = repository.get_available_wahlmodule(
            studiengang_id=1,
            wahlbereich='A'
        )

        assert isinstance(result, list)

    def test_correct_count_wahlbereich_a(self, repository):
        """get_available_wahlmodule() gibt korrekte Anzahl fuer Bereich A"""
        result = repository.get_available_wahlmodule(
            studiengang_id=1,
            wahlbereich='A'
        )

        # Bereich A hat 2 Module
        assert len(result) == 2

    def test_module_structure(self, repository):
        """get_available_wahlmodule() Module haben korrekte Struktur"""
        result = repository.get_available_wahlmodule(
            studiengang_id=1,
            wahlbereich='A'
        )

        for module in result:
            assert 'modul_id' in module
            assert 'name' in module
            assert 'ects' in module

    def test_excludes_module_ids(self, repository):
        """get_available_wahlmodule() schliesst angegebene Module aus"""
        result = repository.get_available_wahlmodule(
            studiengang_id=1,
            wahlbereich='A',
            exclude_modul_ids=[10]  # Schliesse Wahlmodul A1 aus
        )

        # Nur Wahlmodul A2 sollte uebrig sein
        assert len(result) == 1
        assert result[0]['modul_id'] == 11

    def test_empty_if_all_excluded(self, repository):
        """get_available_wahlmodule() leer wenn alle ausgeschlossen"""
        result = repository.get_available_wahlmodule(
            studiengang_id=1,
            wahlbereich='A',
            exclude_modul_ids=[10, 11]
        )

        assert result == []

    def test_sorted_by_name(self, repository):
        """get_available_wahlmodule() sortiert nach Namen"""
        result = repository.get_available_wahlmodule(
            studiengang_id=1,
            wahlbereich='A'
        )

        if len(result) >= 2:
            names = [m['name'] for m in result]
            assert names == sorted(names)

    def test_empty_for_nonexistent_wahlbereich(self, repository):
        """get_available_wahlmodule() leer fuer nicht existierenden Bereich"""
        result = repository.get_available_wahlmodule(
            studiengang_id=1,
            wahlbereich='X'  # Existiert nicht
        )

        assert result == []


# ============================================================================
# PRIVATE METHOD TESTS
# ============================================================================

class TestPrivateMethods:
    """Tests fuer private Hilfsmethoden"""

    def test_get_connection_returns_connection(self, repository):
        """__get_connection() gibt Connection zurueck"""
        conn = repository._ModulRepository__get_connection()

        assert isinstance(conn, sqlite3.Connection)
        conn.close()

    def test_get_connection_enables_foreign_keys(self, repository):
        """__get_connection() aktiviert Foreign Keys"""
        conn = repository._ModulRepository__get_connection()

        result = conn.execute("PRAGMA foreign_keys;").fetchone()
        assert result[0] == 1

        conn.close()


# ============================================================================
# INTEGRATION-LIKE TESTS
# ============================================================================

class TestIntegrationScenarios:
    """Tests fuer typische Nutzungsszenarien"""

    def test_semester_overview_workflow(self, repository):
        """Test: Semester-Uebersicht Workflow"""
        # 1. Lade Module fuer Semester 1
        semester_1 = repository.get_modules_for_semester(
            studiengang_id=1,
            semester=1,
            student_id=1
        )

        # 2. Pruefe verschiedene Status
        status_count = {}
        for module in semester_1:
            status_count[module.status] = status_count.get(module.status, 0) + 1

        assert 'gebucht' in status_count or 'bestanden' in status_count

    def test_wahlmodul_selection_workflow(self, repository):
        """Test: Wahlmodul-Auswahl Workflow"""
        # 1. Lade bereits gebuchte Wahlmodule
        gebuchte = repository.get_gebuchte_wahlmodule(
            student_id=1,
            studiengang_id=1
        )

        # 2. Lade verfuegbare Module fuer Bereich B (nicht gebucht)
        verfuegbar_b = repository.get_available_wahlmodule(
            studiengang_id=1,
            wahlbereich='B',
            exclude_modul_ids=gebuchte['gebuchte_modul_ids']
        )

        # Student 1 hat kein B-Modul, also alle B-Module verfuegbar
        assert len(verfuegbar_b) == 2

    def test_complete_student_progress(self, repository):
        """Test: Vollstaendiger Studienfortschritt"""
        # Lade alle Semester
        all_modules = []
        for semester in range(1, 7):
            modules = repository.get_modules_for_semester(
                studiengang_id=1,
                semester=semester,
                student_id=1
            )
            all_modules.extend(modules)

        # Pruefe dass Module geladen wurden
        assert len(all_modules) > 0

        # Zaehle Status
        bestanden = sum(1 for m in all_modules if m.status == 'bestanden')
        gebucht = sum(1 for m in all_modules if m.status == 'gebucht')
        offen = sum(1 for m in all_modules if m.status == 'offen')

        assert bestanden >= 0
        assert gebucht >= 0
        assert offen >= 0


# ============================================================================
# EDGE CASES
# ============================================================================

class TestEdgeCases:
    """Tests fuer Randfaelle"""

    def test_nonexistent_studiengang(self, repository):
        """get_modules_for_semester() leer fuer nicht existierenden Studiengang"""
        result = repository.get_modules_for_semester(
            studiengang_id=999,
            semester=1,
            student_id=1
        )

        assert result == []

    def test_nonexistent_student(self, repository):
        """get_modules_for_semester() zeigt alle als offen fuer neuen Studenten"""
        result = repository.get_modules_for_semester(
            studiengang_id=1,
            semester=1,
            student_id=999  # Existiert nicht
        )

        # Module sollten geladen werden, aber alle 'offen' sein
        for module in result:
            assert module.status == 'offen'

    def test_fallback_pruefungsart_for_missing(self, repository, temp_db):
        """Fallback auf Klausur wenn keine Pruefungsarten definiert"""
        # Fuege Modul ohne Pruefungsarten hinzu
        conn = sqlite3.connect(temp_db)
        conn.execute("INSERT INTO modul (id, name, ects) VALUES (100, 'Ohne Pruefungsart', 5)")
        conn.execute("INSERT INTO studiengang_modul (studiengang_id, modul_id, semester, pflichtgrad) VALUES (1, 100, 3, 'Pflicht')")
        conn.commit()
        conn.close()

        result = repository.get_modules_for_semester(
            studiengang_id=1,
            semester=3,
            student_id=1
        )

        # Modul sollte Klausur als Fallback haben
        modul = next((m for m in result if m.modul_id == 100), None)
        assert modul is not None
        assert len(modul.erlaubte_pruefungsarten) >= 1
        assert modul.erlaubte_pruefungsarten[0]['wert'] == 'klausur'