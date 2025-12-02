# tests/unit/test_dashboard_controller.py
"""
Unit Tests fuer DashboardController

Testet Dashboard-Logik, Semester-Berechnung und Pruefungsdaten.
"""
import pytest
import sqlite3
from datetime import date, timedelta, datetime
from argon2 import PasswordHasher

from controllers.dashboard_controller import DashboardController

# Mark this whole module as unit test
pytestmark = pytest.mark.unit

ph = PasswordHasher()


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def test_db(tmp_path):
    """Erstellt eine Test-Datenbank mit vollstaendigem Schema"""
    db_path = tmp_path / "test_dashboard.db"

    with sqlite3.connect(str(db_path)) as conn:
        conn.execute("PRAGMA foreign_keys = ON;")

        # login Tabelle
        # noinspection SqlResolve
        conn.execute("""
            CREATE TABLE login (
                id                   INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id           INTEGER,
                email                TEXT UNIQUE NOT NULL,
                benutzername         TEXT UNIQUE,
                password_hash        TEXT NOT NULL,
                is_active            INTEGER DEFAULT 1,
                role                 TEXT DEFAULT 'student',
                created_at           TEXT,
                must_change_password INTEGER DEFAULT 0,
                last_login           TEXT
            )
        """)

        # student Tabelle
        # noinspection SqlResolve
        conn.execute("""
            CREATE TABLE student (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                vorname     TEXT NOT NULL,
                nachname    TEXT NOT NULL,
                matrikel_nr TEXT UNIQUE NOT NULL,
                login_id    INTEGER UNIQUE,
                FOREIGN KEY (login_id) REFERENCES login(id)
            )
        """)

        # studiengang Tabelle
        # noinspection SqlResolve
        conn.execute("""
            CREATE TABLE studiengang (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                name           TEXT NOT NULL,
                grad           TEXT NOT NULL,
                regel_semester INTEGER NOT NULL
            )
        """)

        # zeitmodell Tabelle
        # noinspection SqlResolve
        conn.execute("""
            CREATE TABLE zeitmodell (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                name         TEXT NOT NULL UNIQUE,
                dauer_monate INTEGER NOT NULL,
                kosten_monat DECIMAL(10,2) NOT NULL
            )
        """)

        # modul Tabelle
        # noinspection SqlResolve
        conn.execute("""
            CREATE TABLE modul (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                name        TEXT NOT NULL,
                beschreibung TEXT,
                ects        INTEGER NOT NULL
            )
        """)

        # einschreibung Tabelle
        # noinspection SqlResolve
        conn.execute("""
            CREATE TABLE einschreibung (
                id                     INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id             INTEGER NOT NULL,
                studiengang_id         INTEGER NOT NULL,
                zeitmodell_id          INTEGER NOT NULL,
                start_datum            DATE NOT NULL,
                exmatrikulations_datum DATE,
                status                 TEXT NOT NULL DEFAULT 'aktiv'
                    CHECK (status IN ('aktiv', 'pausiert', 'exmatrikuliert')),
                FOREIGN KEY (student_id) REFERENCES student(id),
                FOREIGN KEY (studiengang_id) REFERENCES studiengang(id),
                FOREIGN KEY (zeitmodell_id) REFERENCES zeitmodell(id)
            )
        """)

        # studiengang_modul Tabelle
        # noinspection SqlResolve
        conn.execute("""
            CREATE TABLE studiengang_modul (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                studiengang_id INTEGER NOT NULL,
                modul_id       INTEGER NOT NULL,
                semester       INTEGER NOT NULL CHECK (semester BETWEEN 1 AND 7),
                pflichtgrad    TEXT NOT NULL CHECK (pflichtgrad IN ('Pflicht', 'Wahl')),
                wahlbereich    TEXT CHECK (wahlbereich IS NULL OR wahlbereich IN ('A', 'B', 'C')),
                FOREIGN KEY (studiengang_id) REFERENCES studiengang(id),
                FOREIGN KEY (modul_id) REFERENCES modul(id)
            )
        """)

        # modulbuchung Tabelle
        # noinspection SqlResolve
        conn.execute("""
            CREATE TABLE modulbuchung (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                einschreibung_id INTEGER NOT NULL,
                modul_id         INTEGER NOT NULL,
                buchungsdatum    DATE,
                status           TEXT NOT NULL CHECK (status IN ('gebucht', 'bestanden', 'anerkannt')),
                FOREIGN KEY (einschreibung_id) REFERENCES einschreibung(id),
                FOREIGN KEY (modul_id) REFERENCES modul(id)
            )
        """)

        # pruefungstermin Tabelle
        # noinspection SqlResolve
        conn.execute("""
            CREATE TABLE pruefungstermin (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                modul_id       INTEGER NOT NULL,
                datum          DATE NOT NULL,
                beginn         TIME,
                ende           TIME,
                art            TEXT NOT NULL CHECK (art IN ('online', 'praesenz', 'projekt', 'workbook')),
                ort            TEXT,
                anmeldeschluss DATETIME,
                kapazitaet     INTEGER,
                beschreibung   TEXT,
                FOREIGN KEY (modul_id) REFERENCES modul(id)
            )
        """)

        # pruefungsanmeldung Tabelle
        # noinspection SqlResolve
        conn.execute("""
            CREATE TABLE pruefungsanmeldung (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                modulbuchung_id     INTEGER NOT NULL,
                pruefungstermin_id  INTEGER NOT NULL,
                status              TEXT NOT NULL CHECK (status IN ('angemeldet', 'storniert', 'absolviert'))
                                    DEFAULT 'angemeldet',
                angemeldet_am       DATETIME NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (modulbuchung_id) REFERENCES modulbuchung(id),
                FOREIGN KEY (pruefungstermin_id) REFERENCES pruefungstermin(id)
            )
        """)

        # pruefungsleistung Tabelle
        # noinspection SqlResolve
        conn.execute("""
            CREATE TABLE pruefungsleistung (
                id                    INTEGER PRIMARY KEY AUTOINCREMENT,
                modulbuchung_id       INTEGER NOT NULL,
                pruefungsdatum        DATE,
                note                  DECIMAL(3,1) CHECK(note >= 1.0 AND note <= 5.0),
                versuch               INTEGER DEFAULT 1,
                max_versuche          INTEGER DEFAULT 3,
                anmeldemodus          TEXT,
                thema                 TEXT,
                pruefungsanmeldung_id INTEGER,
                FOREIGN KEY (modulbuchung_id) REFERENCES modulbuchung(id)
            )
        """)

        # gebuehr Tabelle
        # noinspection SqlResolve
        conn.execute("""
            CREATE TABLE gebuehr (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                einschreibung_id INTEGER NOT NULL,
                art              TEXT NOT NULL,
                betrag           DECIMAL(10,2) NOT NULL,
                faellig_am       DATE NOT NULL,
                bezahlt_am       DATE,
                FOREIGN KEY (einschreibung_id) REFERENCES einschreibung(id)
            )
        """)

        conn.commit()

    return str(db_path)


@pytest.fixture
def test_db_with_data(test_db):
    """Test-Datenbank mit Beispieldaten"""
    with sqlite3.connect(test_db) as conn:
        # Studiengang
        # noinspection SqlResolve
        conn.execute("""
            INSERT INTO studiengang (id, name, grad, regel_semester)
            VALUES (1, 'Angewandte KI', 'B.Sc.', 6)
        """)

        # Zeitmodell
        # noinspection SqlResolve
        conn.execute("""
            INSERT INTO zeitmodell (id, name, dauer_monate, kosten_monat)
            VALUES (1, 'Vollzeit', 36, 199.00)
        """)

        # Module fuer Semester 1
        # noinspection SqlResolve
        conn.execute("INSERT INTO modul (id, name, ects) VALUES (1, 'Programmieren mit Python', 5)")
        # noinspection SqlResolve
        conn.execute("INSERT INTO modul (id, name, ects) VALUES (2, 'Mathematik Grundlagen', 5)")
        # noinspection SqlResolve
        conn.execute("INSERT INTO modul (id, name, ects) VALUES (3, 'Einfuehrung KI', 5)")

        # Module dem Studiengang zuordnen (Semester 1)
        # noinspection SqlResolve
        conn.execute("""
            INSERT INTO studiengang_modul (studiengang_id, modul_id, semester, pflichtgrad)
            VALUES (1, 1, 1, 'Pflicht'), (1, 2, 1, 'Pflicht'), (1, 3, 1, 'Pflicht')
        """)

        # Login erstellen
        password_hash = ph.hash("TestPassword123!")
        # noinspection SqlResolve
        conn.execute("""
            INSERT INTO login (id, student_id, email, benutzername, password_hash, is_active)
            VALUES (1, 1, 'test@example.com', 'testuser', ?, 1)
        """, (password_hash,))

        # Student erstellen
        # noinspection SqlResolve
        conn.execute("""
            INSERT INTO student (id, vorname, nachname, matrikel_nr, login_id)
            VALUES (1, 'Max', 'Mustermann', 'IU12345678', 1)
        """)

        # Einschreibung erstellen (vor 6 Monaten)
        start_datum = (date.today() - timedelta(days=180)).isoformat()
        # noinspection SqlResolve
        conn.execute("""
            INSERT INTO einschreibung (id, student_id, studiengang_id, zeitmodell_id, start_datum, status)
            VALUES (1, 1, 1, 1, ?, 'aktiv')
        """, (start_datum,))

        # Eine Modulbuchung
        # noinspection SqlResolve
        conn.execute("""
            INSERT INTO modulbuchung (id, einschreibung_id, modul_id, status, buchungsdatum)
            VALUES (1, 1, 1, 'bestanden', ?)
        """, (date.today().isoformat(),))

        # Pruefungsleistung
        # noinspection SqlResolve
        conn.execute("""
            INSERT INTO pruefungsleistung (modulbuchung_id, note, pruefungsdatum)
            VALUES (1, 1.7, ?)
        """, (date.today().isoformat(),))

        conn.commit()

    return test_db


@pytest.fixture
def test_db_with_exam(test_db_with_data):
    """Test-Datenbank mit anstehender Pruefung"""
    with sqlite3.connect(test_db_with_data) as conn:
        # Weitere Modulbuchung fuer Pruefung
        # noinspection SqlResolve
        conn.execute("""
            INSERT INTO modulbuchung (id, einschreibung_id, modul_id, status)
            VALUES (2, 1, 2, 'gebucht')
        """)

        # Pruefungstermin in der Zukunft
        pruefungsdatum = (date.today() + timedelta(days=14)).isoformat()
        # noinspection SqlResolve
        conn.execute("""
            INSERT INTO pruefungstermin (id, modul_id, datum, beginn, ende, art, ort)
            VALUES (1, 2, ?, '09:00:00', '11:00:00', 'online', 'Online-Klausur')
        """, (pruefungsdatum,))

        # Pruefungsanmeldung
        # noinspection SqlResolve
        conn.execute("""
            INSERT INTO pruefungsanmeldung (modulbuchung_id, pruefungstermin_id, status)
            VALUES (2, 1, 'angemeldet')
        """)

        conn.commit()

    return test_db_with_data


@pytest.fixture
def dashboard_controller(test_db):
    """DashboardController mit leerer Test-DB"""
    return DashboardController(test_db)


@pytest.fixture
def dashboard_with_data(test_db_with_data):
    """DashboardController mit Testdaten"""
    return DashboardController(test_db_with_data)


@pytest.fixture
def dashboard_with_exam(test_db_with_exam):
    """DashboardController mit Pruefungsdaten"""
    return DashboardController(test_db_with_exam)


# ============================================================================
# INITIALIZATION TESTS
# ============================================================================

class TestDashboardControllerInit:
    """Tests fuer DashboardController Initialisierung"""

    def test_init_sets_db_path(self, test_db):
        """Test: db_path wird korrekt gesetzt"""
        controller = DashboardController(test_db)
        assert controller.db_path == test_db

    def test_init_creates_repositories(self, test_db):
        """Test: Repositories werden erstellt"""
        controller = DashboardController(test_db)

        # Private Attribute pruefen (mit name mangling)
        assert hasattr(controller, '_DashboardController__student_repo')
        assert hasattr(controller, '_DashboardController__einschreibung_repo')
        assert hasattr(controller, '_DashboardController__progress_repo')

    def test_init_creates_service(self, test_db):
        """Test: ProgressTextService wird erstellt"""
        controller = DashboardController(test_db)
        assert hasattr(controller, '_DashboardController__progress_text_service')


# ============================================================================
# GET_STUDENT_BY_AUTH_USER TESTS
# ============================================================================

class TestGetStudentByAuthUser:
    """Tests fuer get_student_by_auth_user() Methode"""

    def test_get_student_success(self, dashboard_with_data):
        """Test: Student wird korrekt geladen"""
        result = dashboard_with_data.get_student_by_auth_user(1)

        assert result is not None
        assert result['vorname'] == 'Max'
        assert result['nachname'] == 'Mustermann'
        assert result['matrikel_nr'] == 'IU12345678'

    def test_get_student_nonexistent_login(self, dashboard_with_data):
        """Test: Nicht existierender Login gibt None zurueck"""
        result = dashboard_with_data.get_student_by_auth_user(999)

        assert result is None

    def test_get_student_returns_dict(self, dashboard_with_data):
        """Test: Ergebnis ist ein Dictionary"""
        result = dashboard_with_data.get_student_by_auth_user(1)

        assert isinstance(result, dict)

    def test_get_student_contains_id(self, dashboard_with_data):
        """Test: Ergebnis enthaelt Student-ID"""
        result = dashboard_with_data.get_student_by_auth_user(1)

        assert 'id' in result
        assert result['id'] == 1


# ============================================================================
# GET_DASHBOARD_DATA TESTS
# ============================================================================

class TestGetDashboardData:
    """Tests fuer get_dashboard_data() Methode"""

    def test_dashboard_data_success(self, dashboard_with_data):
        """Test: Dashboard-Daten werden geladen"""
        result = dashboard_with_data.get_dashboard_data(1)

        assert result is not None
        assert 'student' in result
        assert 'student_name' in result
        assert 'current_semester' in result

    def test_dashboard_data_contains_student_info(self, dashboard_with_data):
        """Test: Student-Informationen sind enthalten"""
        result = dashboard_with_data.get_dashboard_data(1)

        assert result['student'] is not None
        assert result['student_id'] == 1
        assert 'Max' in result['student_name']

    def test_dashboard_data_contains_semester(self, dashboard_with_data):
        """Test: Semester-Informationen sind enthalten"""
        result = dashboard_with_data.get_dashboard_data(1)

        assert 'current_semester' in result
        assert 'max_semester' in result
        assert result['current_semester'] >= 1
        assert result['max_semester'] >= 6

    def test_dashboard_data_contains_progress(self, dashboard_with_data):
        """Test: Progress-Texte sind enthalten"""
        result = dashboard_with_data.get_dashboard_data(1)

        assert 'progress_grade' in result
        assert 'progress_time' in result
        assert 'progress_fee' in result
        assert 'grade_category' in result
        assert 'time_status' in result

    def test_dashboard_data_contains_svg(self, dashboard_with_data):
        """Test: SVG-Pfade sind enthalten"""
        result = dashboard_with_data.get_dashboard_data(1)

        assert 'image_svg' in result
        assert result['image_svg'] == 'Infotainment.svg'

    def test_dashboard_data_contains_debug_info(self, dashboard_with_data):
        """Test: Debug-Informationen sind enthalten"""
        result = dashboard_with_data.get_dashboard_data(1)

        assert 'debug_info' in result
        assert 'actual_semester' in result['debug_info']
        assert 'expected_semester' in result['debug_info']

    def test_dashboard_data_nonexistent_login(self, dashboard_with_data):
        """Test: Nicht existierender Login gibt Fallback-Daten"""
        result = dashboard_with_data.get_dashboard_data(999)

        # Sollte Fallback-Daten zurueckgeben, nicht None
        assert result is not None
        assert result['student'] is None
        assert result['student_name'] == 'Unbekannt'

    def test_dashboard_data_fallback_has_all_keys(self, dashboard_with_data):
        """Test: Fallback-Daten haben alle notwendigen Keys"""
        result = dashboard_with_data.get_dashboard_data(999)

        required_keys = [
            'student', 'student_id', 'student_name',
            'current_semester', 'max_semester',
            'progress_grade', 'progress_time', 'progress_fee',
            'grade_category', 'time_status',
            'next_exam', 'image_svg', 'original_image', 'debug_info'
        ]

        for key in required_keys:
            assert key in result, f"Key '{key}' fehlt in Fallback-Daten"

    def test_dashboard_data_max_semester_vollzeit(self, test_db_with_data):
        """Test: max_semester ist 7 fuer Vollzeit"""
        controller = DashboardController(test_db_with_data)
        result = controller.get_dashboard_data(1)

        assert result['max_semester'] == 7

    def test_dashboard_data_max_semester_teilzeit_i(self, test_db_with_data):
        """Test: max_semester ist 8 fuer Teilzeit I"""
        # Aendere Zeitmodell zu Teilzeit I
        with sqlite3.connect(test_db_with_data) as conn:
            # noinspection SqlResolve
            conn.execute("""
                INSERT INTO zeitmodell (id, name, dauer_monate, kosten_monat)
                VALUES (2, 'Teilzeit I', 48, 149.00)
            """)
            # noinspection SqlResolve
            conn.execute("UPDATE einschreibung SET zeitmodell_id = 2 WHERE id = 1")
            conn.commit()

        controller = DashboardController(test_db_with_data)
        result = controller.get_dashboard_data(1)

        assert result['max_semester'] == 8


# ============================================================================
# GET_NEXT_EXAM TESTS
# ============================================================================

class TestGetNextExam:
    """Tests fuer get_next_exam() Methode"""

    def test_next_exam_exists(self, dashboard_with_exam):
        """Test: Naechste Pruefung wird gefunden"""
        result = dashboard_with_exam.get_next_exam(1)

        assert result is not None
        assert 'modul_name' in result
        assert 'datum' in result
        assert 'tage_bis_pruefung' in result

    def test_next_exam_modul_name(self, dashboard_with_exam):
        """Test: Modul-Name ist korrekt"""
        result = dashboard_with_exam.get_next_exam(1)

        assert result['modul_name'] == 'Mathematik Grundlagen'

    def test_next_exam_tage_bis(self, dashboard_with_exam):
        """Test: Tage bis Pruefung werden berechnet"""
        result = dashboard_with_exam.get_next_exam(1)

        # Sollte ca. 14 Tage sein
        assert result['tage_bis_pruefung'] >= 13
        assert result['tage_bis_pruefung'] <= 15

    def test_next_exam_art(self, dashboard_with_exam):
        """Test: Pruefungsart ist enthalten"""
        result = dashboard_with_exam.get_next_exam(1)

        assert result['art'] == 'online'

    def test_next_exam_zeit(self, dashboard_with_exam):
        """Test: Zeitangaben sind formatiert"""
        result = dashboard_with_exam.get_next_exam(1)

        assert result['beginn'] == '09:00'
        assert result['ende'] == '11:00'

    def test_next_exam_ort(self, dashboard_with_exam):
        """Test: Ort ist enthalten"""
        result = dashboard_with_exam.get_next_exam(1)

        assert result['ort'] == 'Online-Klausur'

    def test_next_exam_no_exam(self, dashboard_with_data):
        """Test: Keine Pruefung angemeldet gibt None"""
        result = dashboard_with_data.get_next_exam(1)

        assert result is None

    def test_next_exam_nonexistent_login(self, dashboard_with_exam):
        """Test: Nicht existierender Login gibt None"""
        result = dashboard_with_exam.get_next_exam(999)

        assert result is None

    def test_next_exam_past_exam_ignored(self, test_db_with_data):
        """Test: Vergangene Pruefungen werden ignoriert"""
        with sqlite3.connect(test_db_with_data) as conn:
            # Modulbuchung
            # noinspection SqlResolve
            conn.execute("""
                INSERT INTO modulbuchung (id, einschreibung_id, modul_id, status)
                VALUES (2, 1, 2, 'gebucht')
            """)

            # Pruefungstermin in der VERGANGENHEIT
            pruefungsdatum = (date.today() - timedelta(days=7)).isoformat()
            # noinspection SqlResolve
            conn.execute("""
                INSERT INTO pruefungstermin (id, modul_id, datum, art)
                VALUES (1, 2, ?, 'online')
            """, (pruefungsdatum,))

            # Pruefungsanmeldung
            # noinspection SqlResolve
            conn.execute("""
                INSERT INTO pruefungsanmeldung (modulbuchung_id, pruefungstermin_id, status)
                VALUES (2, 1, 'angemeldet')
            """)
            conn.commit()

        controller = DashboardController(test_db_with_data)
        result = controller.get_next_exam(1)

        # Vergangene Pruefung sollte nicht zurueckgegeben werden
        assert result is None

    def test_next_exam_storniert_ignored(self, test_db_with_data):
        """Test: Stornierte Pruefungen werden ignoriert"""
        with sqlite3.connect(test_db_with_data) as conn:
            # Modulbuchung
            # noinspection SqlResolve
            conn.execute("""
                INSERT INTO modulbuchung (id, einschreibung_id, modul_id, status)
                VALUES (2, 1, 2, 'gebucht')
            """)

            # Pruefungstermin
            pruefungsdatum = (date.today() + timedelta(days=14)).isoformat()
            # noinspection SqlResolve
            conn.execute("""
                INSERT INTO pruefungstermin (id, modul_id, datum, art)
                VALUES (1, 2, ?, 'online')
            """, (pruefungsdatum,))

            # Stornierte Pruefungsanmeldung
            # noinspection SqlResolve
            conn.execute("""
                INSERT INTO pruefungsanmeldung (modulbuchung_id, pruefungstermin_id, status)
                VALUES (2, 1, 'storniert')
            """)
            conn.commit()

        controller = DashboardController(test_db_with_data)
        result = controller.get_next_exam(1)

        assert result is None


# ============================================================================
# GET_CURRENT_SEMESTER TESTS
# ============================================================================

class TestGetCurrentSemester:
    """Tests fuer get_current_semester() Methode"""

    def test_current_semester_returns_int(self, dashboard_with_data):
        """Test: Ergebnis ist ein Integer"""
        result = dashboard_with_data.get_current_semester(1)

        assert isinstance(result, int)

    def test_current_semester_valid_range(self, dashboard_with_data):
        """Test: Semester ist im gueltigen Bereich (1-7)"""
        result = dashboard_with_data.get_current_semester(1)

        assert result >= 1
        assert result <= 7

    def test_current_semester_nonexistent_login(self, dashboard_with_data):
        """Test: Nicht existierender Login gibt None"""
        result = dashboard_with_data.get_current_semester(999)

        assert result is None

    def test_current_semester_no_einschreibung(self, test_db):
        """Test: Keine Einschreibung gibt None (Exception wird gefangen)"""
        # Student ohne Einschreibung erstellen
        with sqlite3.connect(test_db) as conn:
            password_hash = ph.hash("TestPassword123!")
            # noinspection SqlResolve
            conn.execute("""
                INSERT INTO login (id, student_id, email, password_hash, is_active)
                VALUES (1, 1, 'test@example.com', ?, 1)
            """, (password_hash,))
            # noinspection SqlResolve
            conn.execute("""
                INSERT INTO student (id, vorname, nachname, matrikel_nr, login_id)
                VALUES (1, 'Test', 'User', 'IU99999999', 1)
            """)
            conn.commit()

        controller = DashboardController(test_db)
        result = controller.get_current_semester(1)

        # Repository wirft NotFoundError, Controller faengt ab und gibt None zurueck
        assert result is None

    def test_current_semester_with_progress(self, test_db_with_data):
        """Test: Semester steigt mit Fortschritt"""
        # Student hat 1 von 3 Modulen bestanden
        controller = DashboardController(test_db_with_data)
        result = controller.get_current_semester(1)

        # Mit 1/3 Modulen bestanden sollte noch Semester 1 sein
        assert result == 1


# ============================================================================
# CALCULATE SEMESTER BY PROGRESS TESTS (Private Method)
# ============================================================================

class TestCalculateSemesterByProgress:
    """Tests fuer __calculate_semester_by_progress() Methode"""

    def test_position_starts_at_one(self, test_db_with_data):
        """Test: Position startet bei 1.0"""
        # Entferne die bestandene Modulbuchung
        with sqlite3.connect(test_db_with_data) as conn:
            # noinspection SqlResolve
            conn.execute("DELETE FROM pruefungsleistung")
            # noinspection SqlResolve
            conn.execute("UPDATE modulbuchung SET status = 'gebucht'")
            conn.commit()

        controller = DashboardController(test_db_with_data)
        # Private Methode aufrufen
        result = controller._DashboardController__calculate_semester_by_progress(1, 1)

        # Ohne bestandene Module sollte Position ca. 1.0 sein
        assert result >= 1.0
        assert result < 2.0

    def test_position_increases_with_progress(self, test_db_with_data):
        """Test: Position steigt mit Fortschritt"""
        # Alle Module bestehen
        with sqlite3.connect(test_db_with_data) as conn:
            # Module 2 und 3 auch bestehen
            # noinspection SqlResolve
            conn.execute("""
                INSERT INTO modulbuchung (einschreibung_id, modul_id, status)
                VALUES (1, 2, 'bestanden'), (1, 3, 'bestanden')
            """)
            conn.commit()

        controller = DashboardController(test_db_with_data)
        result = controller._DashboardController__calculate_semester_by_progress(1, 1)

        # Mit allen Modulen aus Semester 1 bestanden sollte Position >= 2.0 sein
        assert result >= 2.0

    def test_position_max_is_seven(self, test_db_with_data):
        """Test: Position ist maximal 7.0"""
        controller = DashboardController(test_db_with_data)
        result = controller._DashboardController__calculate_semester_by_progress(1, 1)

        assert result <= 7.0

    def test_position_partial_progress(self, test_db_with_data):
        """Test: Teilfortschritt wird korrekt berechnet"""
        controller = DashboardController(test_db_with_data)
        result = controller._DashboardController__calculate_semester_by_progress(1, 1)

        # Mit 1/3 Modulen bestanden sollte Position ca. 1.33 sein
        assert result > 1.0
        assert result < 2.0


# ============================================================================
# EDGE CASES
# ============================================================================

class TestEdgeCases:
    """Tests fuer Randfaelle"""

    def test_empty_database(self, dashboard_controller):
        """Test: Leere Datenbank verursacht keinen Crash"""
        result = dashboard_controller.get_dashboard_data(1)

        # Sollte Fallback-Daten zurueckgeben
        assert result is not None
        assert result['student'] is None

    def test_student_without_login(self, test_db):
        """Test: Student ohne Login-Verknuepfung"""
        with sqlite3.connect(test_db) as conn:
            # noinspection SqlResolve
            conn.execute("""
                INSERT INTO student (id, vorname, nachname, matrikel_nr)
                VALUES (1, 'Orphan', 'Student', 'IU00000000')
            """)
            conn.commit()

        controller = DashboardController(test_db)
        result = controller.get_student_by_auth_user(1)

        # Kein Student mit dieser login_id
        assert result is None

    def test_multiple_calls_same_controller(self, dashboard_with_data):
        """Test: Mehrere Aufrufe mit demselben Controller"""
        result1 = dashboard_with_data.get_dashboard_data(1)
        result2 = dashboard_with_data.get_dashboard_data(1)

        assert result1['student_id'] == result2['student_id']
        assert result1['student_name'] == result2['student_name']

    def test_concurrent_controllers(self, test_db_with_data):
        """Test: Mehrere Controller auf derselben DB"""
        controller1 = DashboardController(test_db_with_data)
        controller2 = DashboardController(test_db_with_data)

        result1 = controller1.get_student_by_auth_user(1)
        result2 = controller2.get_student_by_auth_user(1)

        assert result1['id'] == result2['id']


# ============================================================================
# ZEITMODELL TESTS
# ============================================================================

class TestZeitmodell:
    """Tests fuer verschiedene Zeitmodelle"""

    def test_vollzeit_max_semester(self, test_db_with_data):
        """Test: Vollzeit hat max_semester 7"""
        controller = DashboardController(test_db_with_data)
        result = controller.get_dashboard_data(1)

        assert result['max_semester'] == 7

    def test_teilzeit_i_max_semester(self, test_db_with_data):
        """Test: Teilzeit I hat max_semester 8"""
        with sqlite3.connect(test_db_with_data) as conn:
            # noinspection SqlResolve
            conn.execute("""
                INSERT INTO zeitmodell (id, name, dauer_monate, kosten_monat)
                VALUES (2, 'Teilzeit I', 48, 149.00)
            """)
            # noinspection SqlResolve
            conn.execute("UPDATE einschreibung SET zeitmodell_id = 2")
            conn.commit()

        controller = DashboardController(test_db_with_data)
        result = controller.get_dashboard_data(1)

        assert result['max_semester'] == 8

    def test_teilzeit_ii_max_semester(self, test_db_with_data):
        """Test: Teilzeit II hat max_semester 10"""
        with sqlite3.connect(test_db_with_data) as conn:
            # noinspection SqlResolve
            conn.execute("""
                INSERT INTO zeitmodell (id, name, dauer_monate, kosten_monat)
                VALUES (3, 'Teilzeit II', 72, 119.00)
            """)
            # noinspection SqlResolve
            conn.execute("UPDATE einschreibung SET zeitmodell_id = 3")
            conn.commit()

        controller = DashboardController(test_db_with_data)
        result = controller.get_dashboard_data(1)

        assert result['max_semester'] == 10