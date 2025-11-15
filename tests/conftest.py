# tests/conftest.py
"""Pytest Fixtures - ECHTES Schema aus dashboard.db + Model Fixtures"""
import os
import sys
import tempfile
import sqlite3
from pathlib import Path
from datetime import date
from decimal import Decimal

import pytest

# FÃ¼ge Projekt-Root zum Python-Path hinzu
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# ============================================================================
# IMPORTS fÃ¼r Model Fixtures
# ============================================================================

from models.student import Student
from models.modul import Modul, ModulBuchung
from models.modulbuchung import Modulbuchung
from models.pruefungsleistung import Pruefungsleistung
from models.gebuehr import Gebuehr
from models.einschreibung import Einschreibung
from models.progress import Progress
from models.studiengang import Studiengang
from models.studiengang_modul import StudiengangModul


# ============================================================================
# DATABASE FIXTURES
# ============================================================================

@pytest.fixture
def temp_db():
    """Erstellt temporÃ¤re Test-Datenbank mit ECHTEM Schema"""
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)

    os.environ['APP_DB_PATH'] = db_path

    # Initialisiere Schema
    _init_real_schema(db_path)

    yield db_path

    # Cleanup
    try:
        os.unlink(db_path)
    except:
        pass

    if 'APP_DB_PATH' in os.environ:
        del os.environ['APP_DB_PATH']


def _init_real_schema(db_path: str):
    """Initialisiert Schema basierend auf ECHTER dashboard.db"""
    con = sqlite3.connect(db_path)
    con.execute("PRAGMA foreign_keys = ON;")

    # Login Tabelle
    con.execute("""
                CREATE TABLE login
                (
                    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id           INTEGER NOT NULL,
                    email                TEXT    NOT NULL UNIQUE,
                    benutzername         TEXT    NOT NULL UNIQUE,
                    password_hash        TEXT    NOT NULL,
                    is_active            INTEGER DEFAULT 1,
                    role                 TEXT    DEFAULT 'student' CHECK (role IN ('student', 'admin', 'tutor')),
                    created_at           TEXT,
                    must_change_password INTEGER DEFAULT 0,
                    last_login           TEXT,
                    FOREIGN KEY (student_id) REFERENCES student (id) ON DELETE CASCADE
                )
                """)

    # Student Tabelle
    con.execute("""
                CREATE TABLE student
                (
                    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                    matrikel_nr         TEXT UNIQUE NOT NULL,
                    vorname             TEXT        NOT NULL,
                    nachname            TEXT        NOT NULL,
                    email               TEXT        NOT NULL,
                    start_datum DATE        NOT NULL,
                    login_id            INTEGER,
                    FOREIGN KEY (login_id) REFERENCES login (id) ON DELETE CASCADE
                )
                """)

    # Studiengang Tabelle
    con.execute("""
                CREATE TABLE studiengang
                (
                    id             INTEGER PRIMARY KEY AUTOINCREMENT,
                    name           TEXT    NOT NULL,
                    grad           TEXT    NOT NULL,
                    regel_semester INTEGER NOT NULL
                )
                """)

    # Modul Tabelle
    con.execute("""
                CREATE TABLE modul
                (
                    id           INTEGER PRIMARY KEY AUTOINCREMENT,
                    name         TEXT    NOT NULL,
                    beschreibung TEXT,
                    ects         INTEGER NOT NULL
                )
                """)

    # Zeitmodell Tabelle
    con.execute("""
                CREATE TABLE zeitmodell
                (
                    id           INTEGER PRIMARY KEY AUTOINCREMENT,
                    name         TEXT           NOT NULL UNIQUE,
                    dauer_monate INTEGER        NOT NULL,
                    kosten_monat DECIMAL(10, 2) NOT NULL
                )
                """)

    # Einschreibung Tabelle
    con.execute("""
                CREATE TABLE einschreibung
                (
                    id             INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id     INTEGER NOT NULL,
                    studiengang_id INTEGER NOT NULL,
                    zeitmodell_id  INTEGER NOT NULL,
                    start_datum    DATE    NOT NULL,
                    status         TEXT    DEFAULT 'aktiv' CHECK (status IN ('aktiv', 'pausiert', 'exmatrikuliert')),
                    FOREIGN KEY (student_id) REFERENCES student (id) ON DELETE CASCADE,
                    FOREIGN KEY (studiengang_id) REFERENCES studiengang (id),
                    FOREIGN KEY (zeitmodell_id) REFERENCES zeitmodell (id)
                )
                """)

    # Studiengang_Modul Tabelle
    con.execute("""
                CREATE TABLE studiengang_modul
                (
                    studiengang_id INTEGER NOT NULL,
                    modul_id       INTEGER NOT NULL,
                    semester       INTEGER NOT NULL,
                    pflichtgrad    TEXT    NOT NULL CHECK (pflichtgrad IN ('Pflicht', 'Wahl')),
                    PRIMARY KEY (studiengang_id, modul_id, semester),
                    FOREIGN KEY (studiengang_id) REFERENCES studiengang (id) ON DELETE CASCADE,
                    FOREIGN KEY (modul_id) REFERENCES modul (id) ON DELETE CASCADE
                )
                """)

    # Modulbuchung Tabelle
    con.execute("""
                CREATE TABLE modulbuchung
                (
                    id               INTEGER PRIMARY KEY AUTOINCREMENT,
                    einschreibung_id INTEGER NOT NULL,
                    modul_id         INTEGER NOT NULL,
                    buchungsdatum    DATE,
                    status           TEXT DEFAULT 'gebucht' CHECK (status IN ('gebucht', 'anerkannt', 'bestanden', 'nicht_bestanden')),
                    FOREIGN KEY (einschreibung_id) REFERENCES einschreibung (id) ON DELETE CASCADE,
                    FOREIGN KEY (modul_id) REFERENCES modul (id)
                )
                """)

    # Pruefungsleistung Tabelle
    con.execute("""
                CREATE TABLE pruefungsleistung
                (
                    id               INTEGER PRIMARY KEY AUTOINCREMENT,
                    modulbuchung_id  INTEGER        NOT NULL,
                    pruefungsdatum   DATE,
                    note             DECIMAL(2, 1),
                    versuch          INTEGER DEFAULT 1,
                    max_versuche     INTEGER DEFAULT 3,
                    anmeldemodus     TEXT    DEFAULT 'online' CHECK (anmeldemodus IN ('online', 'praesenz')),
                    thema            TEXT,
                    FOREIGN KEY (modulbuchung_id) REFERENCES modulbuchung (id) ON DELETE CASCADE
                )
                """)

    # Gebuehr Tabelle
    con.execute("""
                CREATE TABLE gebuehr
                (
                    id               INTEGER PRIMARY KEY AUTOINCREMENT,
                    einschreibung_id INTEGER      NOT NULL,
                    art              TEXT         NOT NULL,
                    betrag           DECIMAL(8,2) NOT NULL,
                    faellig_am       DATE         NOT NULL,
                    bezahlt_am       DATE,
                    FOREIGN KEY (einschreibung_id) REFERENCES einschreibung (id) ON DELETE CASCADE
                )
                """)

    # Pruefungsanmeldung Tabelle (Legacy/Test?)
    con.execute("""
                CREATE TABLE pruefungsanmeldung
                (
                    id                INTEGER PRIMARY KEY AUTOINCREMENT,
                    modulbuchung_id   INTEGER NOT NULL,
                    pruefungstermin_id INTEGER,
                    status            TEXT DEFAULT 'angemeldet' CHECK (status IN ('angemeldet', 'abgemeldet', 'erschienen', 'nicht_erschienen')),
                    angemeldet_am     DATETIME,
                    FOREIGN KEY (modulbuchung_id) REFERENCES modulbuchung (id) ON DELETE CASCADE
                )
                """)

    # Pruefungstermin Tabelle (Legacy/Test?)
    con.execute("""
                CREATE TABLE pruefungstermin
                (
                    id               INTEGER PRIMARY KEY AUTOINCREMENT,
                    modul_id         INTEGER NOT NULL,
                    datum            DATE NOT NULL,
                    beginn           TIME,
                    ende             TIME,
                    art              TEXT CHECK (art IN ('Klausur', 'MÃ¼ndlich', 'Hausarbeit', 'Projekt')),
                    anmeldeschluss   DATE,
                    kapazitaet       INTEGER,
                    FOREIGN KEY (modul_id) REFERENCES modul (id)
                )
                """)

    con.commit()
    con.close()


@pytest.fixture
def db_with_data(temp_db):
    """Test-DB mit Beispieldaten gefÃ¼llt"""
    con = sqlite3.connect(temp_db)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON;")

    # Studiengang einfÃ¼gen
    con.execute("""
        INSERT INTO studiengang (name, grad, regel_semester)
        VALUES ('Informatik', 'B.Sc.', 6)
    """)

    # Zeitmodell einfÃ¼gen
    con.execute("""
        INSERT INTO zeitmodell (name, dauer_monate, kosten_monat)
        VALUES ('Vollzeit 36 Monate', 36, 299.00)
    """)

    # Student einfÃ¼gen
    con.execute("""
        INSERT INTO student (matrikel_nr, vorname, nachname, email, start_datum)
        VALUES ('IU12345', 'Max', 'Mustermann', 'max.mustermann@iu.org', '2024-01-01')
    """)

    # Login einfÃ¼gen
    con.execute("""
        INSERT INTO login (student_id, email, benutzername, password_hash, is_active, role)
        VALUES (1, 'max.mustermann@iu.org', 'max.mustermann', 
                '$argon2id$v=19$m=65536,t=3,p=4$test', 1, 'student')
    """)

    # Einschreibung einfÃ¼gen
    con.execute("""
        INSERT INTO einschreibung (student_id, studiengang_id, zeitmodell_id, start_datum, status)
        VALUES (1, 1, 1, '2024-01-01', 'aktiv')
    """)

    # Module einfÃ¼gen
    con.execute("""
        INSERT INTO modul (name, beschreibung, ects)
        VALUES 
            ('EinfÃ¼hrung in die Programmierung', 'Python Grundlagen', 5),
            ('Datenbanken', 'SQL und NoSQL', 5),
            ('Webtechnologien', 'HTML, CSS, JavaScript', 5)
    """)

    # Studiengang-Modul Zuordnung
    con.execute("""
        INSERT INTO studiengang_modul (studiengang_id, modul_id, semester, pflichtgrad)
        VALUES 
            (1, 1, 1, 'Pflicht'),
            (1, 2, 2, 'Pflicht'),
            (1, 3, 3, 'Wahlpflicht')
    """)

    # Modulbuchung einfÃ¼gen
    con.execute("""
        INSERT INTO modulbuchung (einschreibung_id, modul_id, buchungsdatum, status)
        VALUES (1, 1, '2024-01-15', 'bestanden')
    """)

    # PrÃ¼fungsleistung einfÃ¼gen
    con.execute("""
        INSERT INTO pruefungsleistung (modulbuchung_id, pruefungsdatum, note, versuch, anmeldemodus)
        VALUES (1, '2024-02-01', 2.3, 1, 'online')
    """)

    # GebÃ¼hr einfÃ¼gen
    con.execute("""
        INSERT INTO gebuehr (einschreibung_id, art, betrag, faellig_am, bezahlt_am)
        VALUES (1, 'Monatsrate', 299.00, '2024-02-01', '2024-01-25')
    """)

    con.commit()

    yield (con, temp_db)

    con.close()


@pytest.fixture
def app(temp_db):
    """Flask App mit Test-DB"""
    # Setze ENV variable BEVOR app importiert wird
    os.environ['APP_DB_PATH'] = temp_db

    # Importiere app (wird neu geladen wenn schon importiert)
    import importlib
    if 'app' in sys.modules:
        importlib.reload(sys.modules['app'])

    from app import app as flask_app

    flask_app.config.update({
        'TESTING': True,
        'SECRET_KEY': 'test-secret-key',
        'WTF_CSRF_ENABLED': False,
        'SESSION_TYPE': 'filesystem',
    })

    yield flask_app


@pytest.fixture
def client(app):
    """Flask Test Client"""
    return app.test_client()


@pytest.fixture
def authenticated_client(client, db_with_data):
    """Authentifizierter Test Client (als Max Mustermann)"""
    with client.session_transaction() as session:
        session['user_id'] = 1
        session['student_id'] = 1
        session['email'] = 'max.mustermann@iu.org'

    yield client

    with client.session_transaction() as session:
        session.clear()


@pytest.fixture
def app_client(temp_db):
    """Flask Client + DB Path (fÃ¼r alte Integration Tests)

    Returns: (client, db_path) tuple

    KRITISCH: Patcht auth_ctrl damit es die Test-DB verwendet!
    """
    # Setze ENV variable BEVOR app importiert wird
    os.environ['APP_DB_PATH'] = temp_db

    # Importiere app (wird neu geladen wenn schon importiert)
    import importlib
    if 'app' in sys.modules:
        importlib.reload(sys.modules['app'])

    from app import app as flask_app

    flask_app.config.update({
        'TESTING': True,
        'SECRET_KEY': 'test-secret-key',
        'WTF_CSRF_ENABLED': False,
        'SESSION_TYPE': 'filesystem',
    })

    # KRITISCH: Patche auth_ctrl damit es Test-DB verwendet statt hardcoded dashboard.db
    try:
        from controllers.auth_controller import AuthController
        import app as app_module
        app_module.auth_ctrl = AuthController(temp_db)
        print(f"âœ… auth_ctrl gepatcht mit Test-DB: {temp_db}")
    except Exception as e:
        print(f"âš ï¸ Konnte auth_ctrl nicht patchen: {e}")

    client = flask_app.test_client()

    yield (client, temp_db)

    # Cleanup Sessions
    with client.session_transaction() as session:
        session.clear()


# ============================================================================
# UTILITY FIXTURES
# ============================================================================

@pytest.fixture
def db_connection(temp_db):
    """Direkte DB-Connection fÃ¼r Tests"""
    con = sqlite3.connect(temp_db)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON;")

    yield con

    con.close()


# ============================================================================
# MODEL FIXTURES (NEU!)
# ============================================================================

@pytest.fixture
def sample_student():
    """Beispiel-Student fÃ¼r Unit Tests"""
    return Student(
        id=1,
        matrikel_nr="IU12345",
        vorname="Max",
        nachname="Mustermann",
        email="max.mustermann@example.com",
        start_datum=date(2024, 1, 1),
        login_id=10
    )


@pytest.fixture
def sample_modul():
    """Beispiel-Modul fÃ¼r Unit Tests"""
    return Modul(
        id=1,
        name="EinfÃ¼hrung in die Programmierung",
        beschreibung="Grundlagen der Programmierung mit Python",
        ects=5
    )


@pytest.fixture
def sample_modulbuchung():
    """Beispiel-Modulbuchung fÃ¼r Unit Tests"""
    return Modulbuchung(
        id=1,
        einschreibung_id=100,
        modul_id=42,
        buchungsdatum=date(2024, 1, 15),
        status="gebucht"
    )


@pytest.fixture
def sample_pruefungsleistung():
    """Beispiel-PrÃ¼fungsleistung fÃ¼r Unit Tests"""
    return Pruefungsleistung(
        id=1,
        einschreibung_id=100,
        modul_id=42,
        buchungsdatum=date(2024, 1, 15),
        status="bestanden",
        note=Decimal("2.3"),
        pruefungsdatum=date(2024, 2, 1),
        versuch=1,
        max_versuche=3,
        anmeldemodus="online",
        thema=None
    )


@pytest.fixture
def sample_gebuehr():
    """Beispiel-GebÃ¼hr fÃ¼r Unit Tests"""
    return Gebuehr(
        id=1,
        einschreibung_id=100,
        art="Monatsrate",
        betrag=Decimal("299.00"),
        faellig_am=date(2024, 2, 1),
        bezahlt_am=None
    )


@pytest.fixture
def sample_einschreibung():
    """Beispiel-Einschreibung fÃ¼r Unit Tests"""
    return Einschreibung(
        id=1,
        student_id=1,
        studiengang_id=1,
        zeitmodell_id=1,
        start_datum=date(2024, 1, 1),
        status="aktiv"
    )


@pytest.fixture
def sample_studiengang():
    """Beispiel-Studiengang fÃ¼r Unit Tests"""
    return Studiengang(
        id=1,
        name="Informatik",
        grad="B.Sc.",
        regel_semester=6,
        beschreibung="Bachelor of Science Informatik"
    )


@pytest.fixture
def sample_progress():
    """Beispiel-Progress fÃ¼r Unit Tests"""
    return Progress(
        student_id=1,
        durchschnittsnote=Decimal("2.3"),
        anzahl_bestandene_module=10,
        anzahl_gebuchte_module=12,
        offene_gebuehren=Decimal("299.00"),
        aktuelles_semester=2.5,
        erwartetes_semester=2.0
    )


@pytest.fixture
def sample_dates():
    """HÃ¤ufig verwendete Test-Daten"""
    return {
        'today': date.today(),
        'enrollment_date': date(2024, 1, 1),
        'exam_date': date(2024, 2, 1),
        'payment_due': date(2024, 2, 15),
    }


@pytest.fixture
def sample_notes():
    """Beispiel-Noten fÃ¼r Tests"""
    return {
        'sehr_gut': Decimal("1.3"),
        'gut': Decimal("2.3"),
        'befriedigend': Decimal("3.0"),
        'bestanden': Decimal("4.0"),
        'durchgefallen': Decimal("5.0"),
    }


# ============================================================================
# PYTEST CONFIGURATION
# ============================================================================

def pytest_configure(config):
    """Pytest Hook: Registriere Custom Markers"""
    config.addinivalue_line("markers", "unit: Unit tests (fast, isolated)")
    config.addinivalue_line("markers", "integration: Integration tests (slower, uses DB)")
    config.addinivalue_line("markers", "slow: Slow running tests")
    config.addinivalue_line("markers", "db: Database related tests")