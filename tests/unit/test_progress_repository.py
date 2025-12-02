# tests/unit/test_progress_repository.py
"""
Unit Tests fuer ProgressRepository (repositories/progress_repository.py)

Testet das ProgressRepository:
- get_progress_for_student() - Gesamtfortschritt berechnen
- Notendurchschnitt-Berechnung (nur Studiengangs-Module)
- Modul-Zaehlung (bestanden, gebucht)
- Offene Gebuehren summieren
- Semester-Berechnung (Fortschritt vs. Zeit)

WICHTIG: Unterscheidung der Semester-Berechnungen:
- aktuelles_semester = FORTSCHRITT (basierend auf bestandenen Modulen) -> fuer Pfad-Position
- erwartetes_semester = ZEIT (basierend auf Einschreibedatum + Zeitmodell) -> fuer Progress-Texte

Formel fuer aktuelles_semester:
- (passed_count / 7.0) + 1.0
- Begrenzt auf 1.0 bis 7.0
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
def progress_repository_class():
    """Importiert ProgressRepository-Klasse"""
    try:
        from repositories import ProgressRepository
        return ProgressRepository
    except ImportError:
        from repositories.progress_repository import ProgressRepository
        return ProgressRepository


@pytest.fixture
def progress_class():
    """Importiert Progress-Klasse"""
    try:
        from models.progress import Progress
        return Progress
    except ImportError:
        from models import Progress
        return Progress


@pytest.fixture
def student_class():
    """Importiert Student-Klasse"""
    try:
        from models.student import Student
        return Student
    except ImportError:
        from models import Student
        return Student


@pytest.fixture
def temp_db():
    """Erstellt temporaere Test-Datenbank mit vollstaendigem Schema"""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)

    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON;")

    # Berechne Startdatum (12 Monate in der Vergangenheit)
    start_datum_1 = (date.today() - timedelta(days=365)).isoformat()
    start_datum_2 = (date.today() - timedelta(days=180)).isoformat()

    # Erstelle vollstaendiges Schema
    conn.executescript(f"""
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
            modulbuchung_id INTEGER NOT NULL,
            note REAL,
            pruefungsdatum TEXT,
            versuch INTEGER DEFAULT 1,
            max_versuche INTEGER DEFAULT 3,
            anmeldemodus TEXT DEFAULT 'online',
            thema TEXT,
            FOREIGN KEY (modulbuchung_id) REFERENCES modulbuchung(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS gebuehr (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            einschreibung_id INTEGER NOT NULL,
            art TEXT NOT NULL,
            betrag TEXT NOT NULL,
            faellig_am TEXT NOT NULL,
            bezahlt_am TEXT,
            FOREIGN KEY (einschreibung_id) REFERENCES einschreibung(id)
        );

        -- Testdaten: Studenten
        INSERT INTO student (id, matrikel_nr, vorname, nachname) VALUES
            (1, 'IU12345678', 'Max', 'Mustermann'),
            (2, 'IU87654321', 'Erika', 'Musterfrau');

        -- Testdaten: Studiengang (6 Regelsemester + Bachelorarbeit = 7)
        INSERT INTO studiengang (id, name, grad, regel_semester) VALUES
            (1, 'Informatik', 'B.Sc.', 6);

        -- Testdaten: Zeitmodell (6 Monate pro Semester)
        INSERT INTO zeitmodell (id, name, monate_pro_semester, kosten_monat) VALUES
            (1, 'Vollzeit', 6, 359.00);

        -- Testdaten: Einschreibungen
        INSERT INTO einschreibung (id, student_id, studiengang_id, zeitmodell_id, start_datum, status) VALUES
            (1, 1, 1, 1, '{start_datum_1}', 'aktiv'),
            (2, 2, 1, 1, '{start_datum_2}', 'aktiv');

        -- Testdaten: 14 Module fuer Studiengang (7 pro Semester fuer 2 Semester)
        INSERT INTO modul (id, name, ects) VALUES
            (1, 'Mathematik I', 5),
            (2, 'Programmierung I', 5),
            (3, 'Datenbanken', 5),
            (4, 'Software Engineering', 5),
            (5, 'Algorithmen', 5),
            (6, 'Betriebssysteme', 5),
            (7, 'Netzwerke', 5),
            (8, 'Mathematik II', 5),
            (9, 'Programmierung II', 5),
            (10, 'Webentwicklung', 5),
            (11, 'IT-Sicherheit', 5),
            (12, 'Projektmanagement', 5),
            (13, 'Wahlmodul A', 5),
            (14, 'Wahlmodul B', 5),
            (99, 'Test-Modul (nicht im Studiengang)', 5);

        -- Testdaten: Studiengang-Modul-Zuordnung (14 echte Module)
        INSERT INTO studiengang_modul (studiengang_id, modul_id, semester, pflichtgrad) VALUES
            (1, 1, 1, 'Pflicht'),
            (1, 2, 1, 'Pflicht'),
            (1, 3, 1, 'Pflicht'),
            (1, 4, 1, 'Pflicht'),
            (1, 5, 1, 'Pflicht'),
            (1, 6, 1, 'Pflicht'),
            (1, 7, 1, 'Pflicht'),
            (1, 8, 2, 'Pflicht'),
            (1, 9, 2, 'Pflicht'),
            (1, 10, 2, 'Pflicht'),
            (1, 11, 2, 'Pflicht'),
            (1, 12, 2, 'Pflicht'),
            (1, 13, 2, 'Wahl'),
            (1, 14, 2, 'Wahl');
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
def temp_db_with_progress(temp_db):
    """Test-DB mit Fortschrittsdaten (Buchungen, Noten, Gebuehren)"""
    conn = sqlite3.connect(temp_db)
    conn.execute("PRAGMA foreign_keys = ON;")

    today = date.today()

    conn.executescript(f"""
        -- Student 1: 7 bestandene Module (= Semester 2.0), 2 gebucht, offene Gebuehren
        INSERT INTO modulbuchung (id, einschreibung_id, modul_id, buchungsdatum, status) VALUES
            (1, 1, 1, '{today.isoformat()}', 'bestanden'),
            (2, 1, 2, '{today.isoformat()}', 'bestanden'),
            (3, 1, 3, '{today.isoformat()}', 'bestanden'),
            (4, 1, 4, '{today.isoformat()}', 'bestanden'),
            (5, 1, 5, '{today.isoformat()}', 'bestanden'),
            (6, 1, 6, '{today.isoformat()}', 'bestanden'),
            (7, 1, 7, '{today.isoformat()}', 'bestanden'),
            (8, 1, 8, '{today.isoformat()}', 'gebucht'),
            (9, 1, 9, '{today.isoformat()}', 'gebucht');

        -- Pruefungsleistungen mit Noten (7 bestandene)
        -- Noten: 1.7, 2.0, 2.3, 1.3, 2.7, 3.0, 2.0 = 15.0 / 7 = 2.142857...
        INSERT INTO pruefungsleistung (id, modulbuchung_id, note, pruefungsdatum, versuch) VALUES
            (1, 1, 1.7, '{today.isoformat()}', 1),
            (2, 2, 2.0, '{today.isoformat()}', 1),
            (3, 3, 2.3, '{today.isoformat()}', 1),
            (4, 4, 1.3, '{today.isoformat()}', 1),
            (5, 5, 2.7, '{today.isoformat()}', 1),
            (6, 6, 3.0, '{today.isoformat()}', 1),
            (7, 7, 2.0, '{today.isoformat()}', 1);

        -- Gebuehren: 2 bezahlt, 2 offen (je 359.00)
        INSERT INTO gebuehr (einschreibung_id, art, betrag, faellig_am, bezahlt_am) VALUES
            (1, 'Monatsrate', '359.00', '{(today - timedelta(days=60)).isoformat()}', '{(today - timedelta(days=60)).isoformat()}'),
            (1, 'Monatsrate', '359.00', '{(today - timedelta(days=30)).isoformat()}', '{(today - timedelta(days=30)).isoformat()}'),
            (1, 'Monatsrate', '359.00', '{today.isoformat()}', NULL),
            (1, 'Monatsrate', '359.00', '{(today + timedelta(days=30)).isoformat()}', NULL);

        -- Student 2: keine Buchungen, keine Gebuehren (Neuling)
    """)
    conn.commit()
    conn.close()

    return temp_db


@pytest.fixture
def repository(progress_repository_class, temp_db):
    """Erstellt Repository-Instanz mit Test-DB"""
    return progress_repository_class(temp_db)


@pytest.fixture
def repository_with_progress(progress_repository_class, temp_db_with_progress):
    """Erstellt Repository-Instanz mit Test-DB inkl. Fortschrittsdaten"""
    return progress_repository_class(temp_db_with_progress)


@pytest.fixture
def sample_student(student_class):
    """Erstellt Sample-Student fuer Tests"""
    return student_class(
        id=1,
        matrikel_nr="IU12345678",
        vorname="Max",
        nachname="Mustermann",
        login_id=100
    )


@pytest.fixture
def new_student(student_class):
    """Erstellt neuen Student ohne Fortschritt"""
    return student_class(
        id=2,
        matrikel_nr="IU87654321",
        vorname="Erika",
        nachname="Musterfrau",
        login_id=None
    )


# ============================================================================
# INITIALIZATION TESTS
# ============================================================================

class TestProgressRepositoryInit:
    """Tests fuer Repository-Initialisierung"""

    def test_init_with_db_path(self, progress_repository_class, temp_db):
        """Repository kann mit DB-Pfad initialisiert werden"""
        repo = progress_repository_class(temp_db)

        assert repo.db_path == temp_db

    def test_init_stores_db_path(self, progress_repository_class):
        """Repository speichert db_path"""
        repo = progress_repository_class("/path/to/db.sqlite")

        assert repo.db_path == "/path/to/db.sqlite"


# ============================================================================
# GET_PROGRESS_FOR_STUDENT TESTS
# ============================================================================

class TestGetProgressForStudent:
    """Tests fuer get_progress_for_student() Methode"""

    def test_returns_progress_object(self, repository_with_progress, sample_student, progress_class):
        """get_progress_for_student() gibt Progress-Objekt zurueck"""
        result = repository_with_progress.get_progress_for_student(
            student=sample_student,
            einschreibung_id=1
        )

        assert isinstance(result, progress_class)

    def test_correct_student_id(self, repository_with_progress, sample_student):
        """get_progress_for_student() setzt korrekte student_id"""
        result = repository_with_progress.get_progress_for_student(
            student=sample_student,
            einschreibung_id=1
        )

        assert result.student_id == 1

    def test_calculates_average_grade(self, repository_with_progress, sample_student):
        """get_progress_for_student() berechnet Notendurchschnitt"""
        result = repository_with_progress.get_progress_for_student(
            student=sample_student,
            einschreibung_id=1
        )

        # Noten: 1.7, 2.0, 2.3, 1.3, 2.7, 3.0, 2.0 = 15.0 / 7 = 2.142857...
        assert result.durchschnittsnote is not None
        expected = Decimal('15.0') / Decimal('7')
        assert abs(result.durchschnittsnote - expected) < Decimal('0.01')

    def test_counts_passed_modules(self, repository_with_progress, sample_student):
        """get_progress_for_student() zaehlt bestandene Module"""
        result = repository_with_progress.get_progress_for_student(
            student=sample_student,
            einschreibung_id=1
        )

        # 7 bestandene Module
        assert result.anzahl_bestandene_module == 7

    def test_counts_booked_modules(self, repository_with_progress, sample_student):
        """get_progress_for_student() zaehlt gebuchte Module"""
        result = repository_with_progress.get_progress_for_student(
            student=sample_student,
            einschreibung_id=1
        )

        # 7 bestanden + 2 gebucht = 9 total
        assert result.anzahl_gebuchte_module == 9

    def test_sums_open_fees(self, repository_with_progress, sample_student):
        """get_progress_for_student() summiert offene Gebuehren"""
        result = repository_with_progress.get_progress_for_student(
            student=sample_student,
            einschreibung_id=1
        )

        # 2 offene Gebuehren a 359.00 = 718.00
        assert result.offene_gebuehren == Decimal('718.00')

    def test_calculates_current_semester_from_progress(self, repository_with_progress, sample_student):
        """get_progress_for_student() berechnet aktuelles_semester aus Fortschritt"""
        result = repository_with_progress.get_progress_for_student(
            student=sample_student,
            einschreibung_id=1
        )

        # Formel: (passed_count / 7.0) + 1.0 = (7 / 7.0) + 1.0 = 2.0
        assert result.aktuelles_semester == 2.0

    def test_calculates_expected_semester_from_time(self, repository_with_progress, sample_student):
        """get_progress_for_student() berechnet erwartetes_semester aus Zeit"""
        result = repository_with_progress.get_progress_for_student(
            student=sample_student,
            einschreibung_id=1
        )

        # Einschreibung vor ~12 Monaten, 6 Monate pro Semester = ~Semester 3
        assert result.erwartetes_semester >= 2

    def test_new_student_defaults(self, repository, new_student):
        """get_progress_for_student() fuer neuen Student ohne Fortschritt"""
        result = repository.get_progress_for_student(
            student=new_student,
            einschreibung_id=2
        )

        assert result.durchschnittsnote is None
        assert result.anzahl_bestandene_module == 0
        assert result.anzahl_gebuchte_module == 0
        assert result.offene_gebuehren == Decimal('0')
        # Formel: (0 / 7.0) + 1.0 = 1.0
        assert result.aktuelles_semester == 1.0


# ============================================================================
# AVERAGE GRADE CALCULATION TESTS
# ============================================================================

class TestAverageGradeCalculation:
    """Tests fuer Notendurchschnitt-Berechnung"""

    def test_average_only_passed_modules(self, repository_with_progress, sample_student):
        """Durchschnitt nur von bestandenen Modulen"""
        result = repository_with_progress.get_progress_for_student(
            student=sample_student,
            einschreibung_id=1
        )

        # Nur bestandene Module mit Note werden beruecksichtigt
        assert result.durchschnittsnote is not None

    def test_average_none_without_grades(self, repository, new_student):
        """Durchschnitt ist None ohne Noten"""
        result = repository.get_progress_for_student(
            student=new_student,
            einschreibung_id=2
        )

        assert result.durchschnittsnote is None

    def test_average_is_decimal(self, repository_with_progress, sample_student):
        """Durchschnitt ist Decimal"""
        result = repository_with_progress.get_progress_for_student(
            student=sample_student,
            einschreibung_id=1
        )

        assert isinstance(result.durchschnittsnote, Decimal)

    def test_average_only_studiengang_modules(self, repository_with_progress, sample_student, temp_db_with_progress):
        """Durchschnitt nur von Studiengangs-Modulen (nicht Test-Module)"""
        # Fuege Test-Modul hinzu (modul_id=99, nicht im Studiengang)
        conn = sqlite3.connect(temp_db_with_progress)
        today = date.today()
        conn.execute(f"""
            INSERT INTO modulbuchung (id, einschreibung_id, modul_id, buchungsdatum, status)
            VALUES (100, 1, 99, '{today.isoformat()}', 'bestanden')
        """)
        conn.execute(f"""
            INSERT INTO pruefungsleistung (id, modulbuchung_id, note, pruefungsdatum, versuch)
            VALUES (100, 100, 5.0, '{today.isoformat()}', 1)
        """)
        conn.commit()
        conn.close()

        result = repository_with_progress.get_progress_for_student(
            student=sample_student,
            einschreibung_id=1
        )

        # Note 5.0 sollte NICHT im Durchschnitt sein (Test-Modul nicht im Studiengang)
        # Original: 15.0 / 7 = 2.14
        # Mit 5.0: 20.0 / 8 = 2.5
        assert result.durchschnittsnote < Decimal('2.5')


# ============================================================================
# MODULE COUNTING TESTS
# ============================================================================

class TestModuleCounting:
    """Tests fuer Modul-Zaehlung"""

    def test_passed_count_only_studiengang_modules(self, repository_with_progress, sample_student, temp_db_with_progress):
        """Bestandene Module zaehlt nur Studiengangs-Module"""
        # Fuege Test-Modul hinzu (modul_id=99, nicht im Studiengang)
        conn = sqlite3.connect(temp_db_with_progress)
        today = date.today()
        conn.execute(f"""
            INSERT INTO modulbuchung (id, einschreibung_id, modul_id, buchungsdatum, status)
            VALUES (100, 1, 99, '{today.isoformat()}', 'bestanden')
        """)
        conn.commit()
        conn.close()

        result = repository_with_progress.get_progress_for_student(
            student=sample_student,
            einschreibung_id=1
        )

        # Test-Modul sollte NICHT gezaehlt werden (7 statt 8)
        assert result.anzahl_bestandene_module == 7

    def test_booked_includes_passed(self, repository_with_progress, sample_student):
        """Gebuchte Module enthaelt auch bestandene"""
        result = repository_with_progress.get_progress_for_student(
            student=sample_student,
            einschreibung_id=1
        )

        # gebuchte >= bestandene
        assert result.anzahl_gebuchte_module >= result.anzahl_bestandene_module

    def test_booked_count_only_studiengang_modules(self, repository_with_progress, sample_student, temp_db_with_progress):
        """Gebuchte Module zaehlt nur Studiengangs-Module"""
        # Fuege Test-Modul hinzu (modul_id=99, nicht im Studiengang)
        conn = sqlite3.connect(temp_db_with_progress)
        today = date.today()
        conn.execute(f"""
            INSERT INTO modulbuchung (id, einschreibung_id, modul_id, buchungsdatum, status)
            VALUES (100, 1, 99, '{today.isoformat()}', 'gebucht')
        """)
        conn.commit()
        conn.close()

        result = repository_with_progress.get_progress_for_student(
            student=sample_student,
            einschreibung_id=1
        )

        # Test-Modul sollte NICHT gezaehlt werden (9 statt 10)
        assert result.anzahl_gebuchte_module == 9


# ============================================================================
# OPEN FEES CALCULATION TESTS
# ============================================================================

class TestOpenFeesCalculation:
    """Tests fuer offene Gebuehren-Berechnung"""

    def test_sum_excludes_paid(self, repository_with_progress, sample_student):
        """Offene Gebuehren schliesst bezahlte aus"""
        result = repository_with_progress.get_progress_for_student(
            student=sample_student,
            einschreibung_id=1
        )

        # 4 Gebuehren total, 2 bezahlt, 2 offen = 718.00
        assert result.offene_gebuehren == Decimal('718.00')

    def test_sum_zero_when_all_paid(self, repository_with_progress, sample_student, temp_db_with_progress):
        """Offene Gebuehren ist 0 wenn alle bezahlt"""
        # Markiere alle als bezahlt
        conn = sqlite3.connect(temp_db_with_progress)
        conn.execute("UPDATE gebuehr SET bezahlt_am = date('now') WHERE einschreibung_id = 1")
        conn.commit()
        conn.close()

        result = repository_with_progress.get_progress_for_student(
            student=sample_student,
            einschreibung_id=1
        )

        assert result.offene_gebuehren == Decimal('0')

    def test_sum_is_decimal(self, repository_with_progress, sample_student):
        """Offene Gebuehren ist Decimal"""
        result = repository_with_progress.get_progress_for_student(
            student=sample_student,
            einschreibung_id=1
        )

        assert isinstance(result.offene_gebuehren, Decimal)

    def test_sum_zero_when_no_fees(self, repository, new_student):
        """Offene Gebuehren ist 0 wenn keine Gebuehren"""
        result = repository.get_progress_for_student(
            student=new_student,
            einschreibung_id=2
        )

        assert result.offene_gebuehren == Decimal('0')


# ============================================================================
# SEMESTER CALCULATION TESTS (PROGRESS-BASED)
# ============================================================================

class TestProgressBasedSemesterCalculation:
    """Tests fuer Fortschritts-basierte Semester-Berechnung (aktuelles_semester)

    Formel: (passed_count / 7.0) + 1.0
    Begrenzt auf 1.0 bis 7.0
    """

    def test_formula_0_modules(self, repository, new_student):
        """0 Module -> Semester 1.0"""
        result = repository.get_progress_for_student(
            student=new_student,
            einschreibung_id=2
        )

        # (0 / 7.0) + 1.0 = 1.0
        assert result.aktuelles_semester == 1.0

    def test_formula_7_modules(self, repository_with_progress, sample_student):
        """7 Module -> Semester 2.0"""
        result = repository_with_progress.get_progress_for_student(
            student=sample_student,
            einschreibung_id=1
        )

        # (7 / 7.0) + 1.0 = 2.0
        assert result.aktuelles_semester == 2.0

    def test_formula_14_modules(self, repository_with_progress, sample_student, temp_db_with_progress):
        """14 Module -> Semester 3.0"""
        # Fuege 7 weitere bestandene Module hinzu (Module 8-14)
        conn = sqlite3.connect(temp_db_with_progress)
        today = date.today()
        for i, modul_id in enumerate([8, 9, 10, 11, 12, 13, 14], start=10):
            conn.execute(f"""
                INSERT INTO modulbuchung (id, einschreibung_id, modul_id, buchungsdatum, status)
                VALUES ({i}, 1, {modul_id}, '{today.isoformat()}', 'bestanden')
            """)
            conn.execute(f"""
                INSERT INTO pruefungsleistung (id, modulbuchung_id, note, pruefungsdatum, versuch)
                VALUES ({i}, {i}, 2.0, '{today.isoformat()}', 1)
            """)
        conn.commit()
        conn.close()

        result = repository_with_progress.get_progress_for_student(
            student=sample_student,
            einschreibung_id=1
        )

        # (14 / 7.0) + 1.0 = 3.0
        assert result.aktuelles_semester == 3.0

    def test_minimum_semester_1(self, repository, new_student):
        """Minimum ist Semester 1.0"""
        result = repository.get_progress_for_student(
            student=new_student,
            einschreibung_id=2
        )

        assert result.aktuelles_semester >= 1.0

    def test_maximum_semester_7(self, repository_with_progress, sample_student, temp_db_with_progress):
        """Maximum ist Semester 7.0"""
        # Fuege sehr viele Module hinzu (mehr als moeglich)
        conn = sqlite3.connect(temp_db_with_progress)
        today = date.today()

        # Fuege alle restlichen Studiengangs-Module hinzu und markiere als bestanden
        for i, modul_id in enumerate([8, 9, 10, 11, 12, 13, 14], start=50):
            conn.execute(f"""
                INSERT OR REPLACE INTO modulbuchung (id, einschreibung_id, modul_id, buchungsdatum, status)
                VALUES ({i}, 1, {modul_id}, '{today.isoformat()}', 'bestanden')
            """)
            conn.execute(f"""
                INSERT OR IGNORE INTO pruefungsleistung (id, modulbuchung_id, note, pruefungsdatum, versuch)
                VALUES ({i}, {i}, 2.0, '{today.isoformat()}', 1)
            """)

        conn.commit()
        conn.close()

        result = repository_with_progress.get_progress_for_student(
            student=sample_student,
            einschreibung_id=1
        )

        # Maximum ist 7.0
        assert result.aktuelles_semester <= 7.0

    def test_partial_semester_calculation(self, repository, sample_student, temp_db):
        """Partielle Semester-Berechnung (z.B. 3 Module)"""
        # Fuege 3 bestandene Module hinzu
        conn = sqlite3.connect(temp_db)
        today = date.today()
        for i in range(1, 4):
            conn.execute(f"""
                INSERT INTO modulbuchung (id, einschreibung_id, modul_id, buchungsdatum, status)
                VALUES ({i}, 1, {i}, '{today.isoformat()}', 'bestanden')
            """)
            conn.execute(f"""
                INSERT INTO pruefungsleistung (id, modulbuchung_id, note, pruefungsdatum, versuch)
                VALUES ({i}, {i}, 2.0, '{today.isoformat()}', 1)
            """)
        conn.commit()
        conn.close()

        result = repository.get_progress_for_student(
            student=sample_student,
            einschreibung_id=1
        )

        # (3 / 7.0) + 1.0 = 1.428...
        expected = (3 / 7.0) + 1.0
        assert abs(result.aktuelles_semester - expected) < 0.01


# ============================================================================
# EXPECTED SEMESTER (TIME-BASED) TESTS
# ============================================================================

class TestExpectedSemesterCalculation:
    """Tests fuer Zeit-basierte Semester-Berechnung (erwartetes_semester)"""

    def test_expected_semester_from_time(self, repository_with_progress, sample_student):
        """erwartetes_semester basiert auf Zeit seit Einschreibung"""
        result = repository_with_progress.get_progress_for_student(
            student=sample_student,
            einschreibung_id=1
        )

        # Einschreibung vor ~12 Monaten, 6 Monate pro Semester = ~Semester 3
        assert result.erwartetes_semester >= 2

    def test_expected_semester_new_student(self, repository, new_student):
        """erwartetes_semester fuer neuen Student"""
        result = repository.get_progress_for_student(
            student=new_student,
            einschreibung_id=2
        )

        # Einschreibung vor ~6 Monaten = ~Semester 2
        assert result.erwartetes_semester >= 1

    def test_expected_vs_current_difference(self, repository_with_progress, sample_student):
        """Unterschied zwischen aktuellem und erwartetem Semester"""
        result = repository_with_progress.get_progress_for_student(
            student=sample_student,
            einschreibung_id=1
        )

        # Beide Werte sind vorhanden
        assert result.aktuelles_semester is not None
        assert result.erwartetes_semester is not None


# ============================================================================
# PRIVATE METHOD TESTS
# ============================================================================

class TestPrivateMethods:
    """Tests fuer private Hilfsmethoden"""

    def test_get_connection_returns_connection(self, repository):
        """__get_connection() gibt Connection zurueck"""
        conn = repository._ProgressRepository__get_connection()

        assert isinstance(conn, sqlite3.Connection)
        conn.close()

    def test_get_connection_enables_foreign_keys(self, repository):
        """__get_connection() aktiviert Foreign Keys"""
        conn = repository._ProgressRepository__get_connection()

        result = conn.execute("PRAGMA foreign_keys;").fetchone()
        assert result[0] == 1

        conn.close()


# ============================================================================
# INTEGRATION-LIKE TESTS
# ============================================================================

class TestIntegrationScenarios:
    """Tests fuer typische Nutzungsszenarien"""

    def test_progress_dashboard_data(self, repository_with_progress, sample_student):
        """Test: Dashboard-Daten vollstaendig"""
        result = repository_with_progress.get_progress_for_student(
            student=sample_student,
            einschreibung_id=1
        )

        # Alle Dashboard-relevanten Daten vorhanden
        assert result.student_id is not None
        assert result.durchschnittsnote is not None
        assert result.anzahl_bestandene_module >= 0
        assert result.anzahl_gebuchte_module >= 0
        assert isinstance(result.offene_gebuehren, Decimal)
        assert result.aktuelles_semester >= 1.0
        assert result.erwartetes_semester >= 1.0

    def test_progress_to_dict(self, repository_with_progress, sample_student):
        """Test: Progress kann zu Dictionary konvertiert werden"""
        result = repository_with_progress.get_progress_for_student(
            student=sample_student,
            einschreibung_id=1
        )

        d = result.to_dict()

        assert 'student_id' in d
        assert 'durchschnittsnote' in d
        assert 'anzahl_bestandene_module' in d
        assert 'offene_gebuehren' in d
        assert 'aktuelles_semester' in d
        assert 'erwartetes_semester' in d

    def test_compare_two_students(self, repository_with_progress, sample_student, new_student):
        """Test: Vergleich zweier Studenten"""
        result1 = repository_with_progress.get_progress_for_student(
            student=sample_student,
            einschreibung_id=1
        )
        result2 = repository_with_progress.get_progress_for_student(
            student=new_student,
            einschreibung_id=2
        )

        # Student 1 hat mehr Fortschritt als Student 2
        assert result1.anzahl_bestandene_module > result2.anzahl_bestandene_module
        assert result1.aktuelles_semester > result2.aktuelles_semester


# ============================================================================
# EDGE CASES
# ============================================================================

class TestEdgeCases:
    """Tests fuer Randfaelle"""

    def test_nonexistent_einschreibung(self, repository, sample_student):
        """get_progress_for_student() mit nicht existierender Einschreibung"""
        result = repository.get_progress_for_student(
            student=sample_student,
            einschreibung_id=999
        )

        # Sollte Default-Werte zurueckgeben (keine Fehler)
        assert result.anzahl_bestandene_module == 0
        assert result.aktuelles_semester == 1.0
        # erwartetes_semester hat Fallback auf 1.0
        assert result.erwartetes_semester == 1.0

    def test_single_passed_module(self, repository, sample_student, temp_db):
        """Fortschritt mit nur 1 bestandenem Modul"""
        conn = sqlite3.connect(temp_db)
        today = date.today()
        conn.execute(f"""
            INSERT INTO modulbuchung (einschreibung_id, modul_id, buchungsdatum, status)
            VALUES (1, 1, '{today.isoformat()}', 'bestanden')
        """)
        conn.execute(f"""
            INSERT INTO pruefungsleistung (id, modulbuchung_id, note, pruefungsdatum, versuch)
            VALUES (1, 1, 2.0, '{today.isoformat()}', 1)
        """)
        conn.commit()
        conn.close()

        result = repository.get_progress_for_student(
            student=sample_student,
            einschreibung_id=1
        )

        assert result.anzahl_bestandene_module == 1
        assert result.durchschnittsnote == Decimal('2.0')
        # (1 / 7.0) + 1.0 = 1.142857...
        expected = (1 / 7.0) + 1.0
        assert abs(result.aktuelles_semester - expected) < 0.01

    def test_all_modules_failed(self, repository, sample_student, temp_db):
        """Fortschritt wenn alle Module nicht bestanden"""
        conn = sqlite3.connect(temp_db)
        today = date.today()
        conn.execute(f"""
            INSERT INTO modulbuchung (einschreibung_id, modul_id, buchungsdatum, status)
            VALUES (1, 1, '{today.isoformat()}', 'nicht_bestanden')
        """)
        conn.commit()
        conn.close()

        result = repository.get_progress_for_student(
            student=sample_student,
            einschreibung_id=1
        )

        assert result.anzahl_bestandene_module == 0
        assert result.durchschnittsnote is None
        assert result.aktuelles_semester == 1.0

    def test_very_large_open_fees(self, repository, sample_student, temp_db):
        """Grosse offene Gebuehren"""
        conn = sqlite3.connect(temp_db)
        today = date.today()
        # Fuege 10 offene Gebuehren hinzu
        for i in range(10):
            conn.execute(f"""
                INSERT INTO gebuehr (einschreibung_id, art, betrag, faellig_am, bezahlt_am)
                VALUES (1, 'Monatsrate', '999.99', '{(today - timedelta(days=i*30)).isoformat()}', NULL)
            """)
        conn.commit()
        conn.close()

        result = repository.get_progress_for_student(
            student=sample_student,
            einschreibung_id=1
        )

        # 10 * 999.99 = 9999.90
        assert result.offene_gebuehren == Decimal('9999.90')