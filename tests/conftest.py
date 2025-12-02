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

# Fuege Projekt-Root zum Python-Path hinzu
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# ============================================================================
# IMPORTS fuer Model Fixtures
# Package-Struktur: models/, controllers/, repositories/, services/, utils/
# ============================================================================

from models import Student
from models import Modul
from models import Modulbuchung
from models import Pruefungsleistung
from models import Gebuehr
from models import Einschreibung
from models import Progress
from models import Studiengang
from models import StudiengangModul


# ============================================================================
# DATABASE FIXTURES
# ============================================================================

@pytest.fixture
def temp_db():
    """Erstellt temporaere Test-Datenbank mit ECHTEM Schema"""
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
    """Initialisiert Schema basierend auf ECHTER dashboard.db (Stand November 2025)"""
    con = sqlite3.connect(db_path)
    con.execute("PRAGMA foreign_keys = ON;")

    # ============================================
    # TABELLEN (in korrekter Reihenfolge wegen FK)
    # ============================================

    # 1. Login Tabelle
    con.execute("""
        CREATE TABLE login (
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

    # 2. Student Tabelle
    con.execute("""
        CREATE TABLE student (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            vorname     TEXT NOT NULL,
            nachname    TEXT NOT NULL,
            matrikel_nr TEXT UNIQUE NOT NULL,
            login_id    INTEGER UNIQUE,
            FOREIGN KEY (login_id) REFERENCES login (id)
        )
    """)

    # 3. Studiengang Tabelle
    con.execute("""
        CREATE TABLE studiengang (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            name           TEXT    NOT NULL,
            grad           TEXT    NOT NULL,
            regel_semester INTEGER NOT NULL
        )
    """)

    # 4. Modul Tabelle
    con.execute("""
        CREATE TABLE modul (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            name         TEXT    NOT NULL,
            beschreibung TEXT,
            ects         INTEGER NOT NULL
        )
    """)

    # 5. Zeitmodell Tabelle
    con.execute("""
        CREATE TABLE zeitmodell (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            name         TEXT           NOT NULL UNIQUE,
            dauer_monate INTEGER        NOT NULL,
            kosten_monat DECIMAL(10, 2) NOT NULL
        )
    """)

    # 6. Einschreibung Tabelle
    con.execute("""
        CREATE TABLE einschreibung (
            id                     INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id             INTEGER NOT NULL,
            studiengang_id         INTEGER NOT NULL,
            zeitmodell_id          INTEGER NOT NULL,
            start_datum            DATE    NOT NULL,
            exmatrikulations_datum DATE,
            status                 TEXT    DEFAULT 'aktiv' CHECK (status IN ('aktiv', 'pausiert', 'exmatrikuliert')),
            FOREIGN KEY (student_id) REFERENCES student (id) ON DELETE CASCADE,
            FOREIGN KEY (studiengang_id) REFERENCES studiengang (id),
            FOREIGN KEY (zeitmodell_id) REFERENCES zeitmodell (id)
        )
    """)

    # 7. Studiengang_Modul Tabelle (mit Wahlbereich!)
    con.execute("""
        CREATE TABLE studiengang_modul (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            studiengang_id INTEGER NOT NULL,
            modul_id       INTEGER NOT NULL,
            semester       INTEGER NOT NULL CHECK (semester BETWEEN 1 AND 7),
            pflichtgrad    TEXT    NOT NULL CHECK (pflichtgrad IN ('Pflicht', 'Wahl')),
            wahlbereich    TEXT    CHECK (wahlbereich IS NULL OR wahlbereich IN ('A', 'B', 'C')),
            FOREIGN KEY (studiengang_id) REFERENCES studiengang (id) ON DELETE CASCADE,
            FOREIGN KEY (modul_id) REFERENCES modul (id) ON DELETE CASCADE,
            UNIQUE(studiengang_id, modul_id, semester, wahlbereich)
        )
    """)

    # 8. Modulbuchung Tabelle
    con.execute("""
        CREATE TABLE modulbuchung (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            einschreibung_id INTEGER NOT NULL,
            modul_id         INTEGER NOT NULL,
            buchungsdatum    DATE,
            status           TEXT NOT NULL CHECK (status IN ('gebucht', 'bestanden', 'anerkannt')),
            FOREIGN KEY (einschreibung_id) REFERENCES einschreibung (id) ON DELETE CASCADE,
            FOREIGN KEY (modul_id) REFERENCES modul (id)
        )
    """)

    # 8b. UNIQUE INDEX fuer Modulbuchung
    con.execute("""
        CREATE UNIQUE INDEX idx_modulbuchung_unique
        ON modulbuchung(einschreibung_id, modul_id)
    """)

    # 9. Pruefungstermin Tabelle (VOR Pruefungsanmeldung wegen FK!)
    con.execute("""
        CREATE TABLE pruefungstermin (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            modul_id       INTEGER NOT NULL,
            datum          DATE    NOT NULL,
            beginn         TIME,
            ende           TIME,
            art            TEXT    NOT NULL CHECK (art IN ('online', 'praesenz', 'projekt', 'workbook')),
            ort            TEXT,
            anmeldeschluss DATETIME,
            kapazitaet     INTEGER,
            beschreibung   TEXT,
            FOREIGN KEY (modul_id) REFERENCES modul (id)
        )
    """)

    # 9b. Index fuer Pruefungstermin
    con.execute("""
        CREATE INDEX idx_pruefungstermin_modul ON pruefungstermin(modul_id, datum)
    """)

    # 10. Pruefungsanmeldung Tabelle
    con.execute("""
        CREATE TABLE pruefungsanmeldung (
            id                 INTEGER PRIMARY KEY AUTOINCREMENT,
            modulbuchung_id    INTEGER  NOT NULL UNIQUE,
            pruefungstermin_id INTEGER  NOT NULL,
            status             TEXT     NOT NULL CHECK (status IN ('angemeldet', 'storniert', 'absolviert')) DEFAULT 'angemeldet',
            angemeldet_am      DATETIME NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (modulbuchung_id) REFERENCES modulbuchung (id) ON DELETE CASCADE,
            FOREIGN KEY (pruefungstermin_id) REFERENCES pruefungstermin (id)
        )
    """)

    # 10b. Index fuer Pruefungsanmeldung
    con.execute("""
        CREATE INDEX idx_pruefungsanmeldung_termin
        ON pruefungsanmeldung(pruefungstermin_id, status)
    """)

    # 11. Pruefungsleistung Tabelle
    con.execute("""
        CREATE TABLE pruefungsleistung (
            id                    INTEGER PRIMARY KEY AUTOINCREMENT,
            modulbuchung_id       INTEGER NOT NULL,
            pruefungsdatum        DATE,
            note                  DECIMAL(3, 1) CHECK (note >= 1.0 AND note <= 5.0),
            versuch               INTEGER DEFAULT 1,
            max_versuche          INTEGER DEFAULT 3,
            anmeldemodus          TEXT,
            thema                 TEXT,
            pruefungsanmeldung_id INTEGER REFERENCES pruefungsanmeldung(id),
            FOREIGN KEY (modulbuchung_id) REFERENCES modulbuchung (id) ON DELETE CASCADE
        )
    """)

    # 11b. Index fuer Pruefungsleistung
    con.execute("""
        CREATE INDEX idx_pruefungsleistung_modulbuchung 
        ON pruefungsleistung(modulbuchung_id)
    """)

    # 12. Gebuehr Tabelle
    con.execute("""
        CREATE TABLE gebuehr (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            einschreibung_id INTEGER        NOT NULL,
            art              TEXT           NOT NULL,
            betrag           DECIMAL(10, 2) NOT NULL,
            faellig_am       DATE           NOT NULL,
            bezahlt_am       DATE,
            FOREIGN KEY (einschreibung_id) REFERENCES einschreibung (id) ON DELETE CASCADE
        )
    """)

    # 12b. Unique Index fuer Gebuehren-Idempotenz
    con.execute("""
        CREATE UNIQUE INDEX idx_gebuehr_einschreibung_faellig
        ON gebuehr (einschreibung_id, faellig_am)
    """)

    # 13. Pruefungsart Tabelle (NEU!)
    con.execute("""
        CREATE TABLE pruefungsart (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            kuerzel          TEXT    NOT NULL UNIQUE,
            name             TEXT    NOT NULL,
            anzeigename      TEXT    NOT NULL,
            hat_unterteilung BOOLEAN DEFAULT FALSE,
            beschreibung     TEXT
        )
    """)

    # 14. Modul_Pruefungsart Tabelle (NEU!)
    con.execute("""
        CREATE TABLE modul_pruefungsart (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            modul_id        INTEGER NOT NULL,
            pruefungsart_id INTEGER NOT NULL,
            ist_standard    BOOLEAN DEFAULT FALSE,
            reihenfolge     INTEGER DEFAULT 0,
            FOREIGN KEY (modul_id) REFERENCES modul (id) ON DELETE CASCADE,
            FOREIGN KEY (pruefungsart_id) REFERENCES pruefungsart (id) ON DELETE RESTRICT,
            UNIQUE(modul_id, pruefungsart_id)
        )
    """)

    # 14b. Indizes fuer Modul_Pruefungsart
    con.execute("CREATE INDEX idx_modul_pruefungsart_modul ON modul_pruefungsart(modul_id)")
    con.execute("CREATE INDEX idx_modul_pruefungsart_art ON modul_pruefungsart(pruefungsart_id)")

    # ============================================
    # STANDARD-PRUEFUNGSARTEN einfuegen
    # ============================================
    con.executemany("""
        INSERT INTO pruefungsart (kuerzel, name, anzeigename, hat_unterteilung, beschreibung)
        VALUES (?, ?, ?, ?, ?)
    """, [
        ('K', 'Klausur', 'Klausur', True, 'Schriftliche Pruefung (online oder Praesenz)'),
        ('AWB', 'Advanced Workbook', 'Advanced Workbook', False, 'Erweitertes Arbeitsheft'),
        ('PO', 'Portfolio', 'Portfolio', False, 'Sammlung von Arbeitsproben'),
        ('F', 'Fallstudie', 'Fallstudie', False, 'Analyse eines Praxisfalls'),
        ('FP', 'Fachpraesentation', 'Fachpraesentation', False, 'Muendliche Praesentation'),
        ('PB', 'Projektbericht', 'Projektbericht', False, 'Schriftlicher Projektbericht'),
        ('PP', 'Projektpraesentation', 'Projektpraesentation', False, 'Praesentation eines Projekts'),
        ('S', 'Seminararbeit', 'Seminararbeit', False, 'Wissenschaftliche Seminararbeit'),
        ('H', 'Hausarbeit', 'Hausarbeit', False, 'Schriftliche Hausarbeit'),
    ])

    con.commit()
    con.close()


@pytest.fixture
def db_with_data(temp_db):
    """Test-DB mit Beispieldaten gefuellt"""
    con = sqlite3.connect(temp_db)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON;")

    # Studiengang einfuegen
    con.execute("""
        INSERT INTO studiengang (name, grad, regel_semester)
        VALUES ('Angewandte Kuenstliche Intelligenz', 'B.Sc.', 7)
    """)

    # Zeitmodell einfuegen
    con.execute("""
        INSERT INTO zeitmodell (name, dauer_monate, kosten_monat)
        VALUES ('Vollzeit', 36, 199.00)
    """)

    # Module einfuegen (Pflicht + Wahlmodule)
    con.execute("""
        INSERT INTO modul (name, beschreibung, ects)
        VALUES ('Einfuehrung in die Programmierung', 'Grundlagen der Programmierung mit Python', 5)
    """)
    con.execute("""
        INSERT INTO modul (name, beschreibung, ects)
        VALUES ('Digitale Signalverarbeitung', 'Wahlmodul Bereich A', 10)
    """)
    con.execute("""
        INSERT INTO modul (name, beschreibung, ects)
        VALUES ('Psychologie der MCI', 'Wahlmodul Bereich B', 10)
    """)

    # Studiengang_Modul Zuordnungen
    con.execute("""
        INSERT INTO studiengang_modul (studiengang_id, modul_id, semester, pflichtgrad, wahlbereich)
        VALUES (1, 1, 1, 'Pflicht', NULL)
    """)
    con.execute("""
        INSERT INTO studiengang_modul (studiengang_id, modul_id, semester, pflichtgrad, wahlbereich)
        VALUES (1, 2, 5, 'Wahl', 'A')
    """)
    con.execute("""
        INSERT INTO studiengang_modul (studiengang_id, modul_id, semester, pflichtgrad, wahlbereich)
        VALUES (1, 3, 6, 'Wahl', 'B')
    """)

    # Student einfuegen (ohne login_id erstmal)
    con.execute("""
        INSERT INTO student (vorname, nachname, matrikel_nr)
        VALUES ('Max', 'Mustermann', 'IU12345678')
    """)

    # Login einfuegen
    con.execute("""
        INSERT INTO login (student_id, email, benutzername, password_hash)
        VALUES (1, 'max.mustermann@iu.org', 'max.mustermann', 'hashed_password_here')
    """)

    # Student mit Login verknuepfen
    con.execute("UPDATE student SET login_id = 1 WHERE id = 1")

    # Einschreibung
    con.execute("""
        INSERT INTO einschreibung (student_id, studiengang_id, zeitmodell_id, start_datum, status)
        VALUES (1, 1, 1, '2024-01-01', 'aktiv')
    """)

    # Modulbuchung
    con.execute("""
        INSERT INTO modulbuchung (einschreibung_id, modul_id, buchungsdatum, status)
        VALUES (1, 1, '2024-01-15', 'gebucht')
    """)

    # Pruefungstermin
    con.execute("""
        INSERT INTO pruefungstermin (modul_id, datum, art, ort)
        VALUES (1, '2024-03-15', 'online', 'Online-Pruefung')
    """)

    # Modul-Pruefungsart Zuordnung
    con.execute("""
        INSERT INTO modul_pruefungsart (modul_id, pruefungsart_id, ist_standard, reihenfolge)
        VALUES (1, 1, TRUE, 1)
    """)

    con.commit()
    con.close()

    return temp_db


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
    """Flask Client + DB Path (fuer alte Integration Tests)

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
        from controllers import AuthController
        import app as app_module
        app_module.auth_ctrl = AuthController(temp_db)
        print(f"auth_ctrl gepatcht mit Test-DB: {temp_db}")
    except Exception as e:
        print(f"Konnte auth_ctrl nicht patchen: {e}")

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
    """Direkte DB-Connection fuer Tests"""
    con = sqlite3.connect(temp_db)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON;")

    yield con

    con.close()


# ============================================================================
# MODEL FIXTURES
# ============================================================================

@pytest.fixture
def sample_student():
    """Beispiel-Student fuer Unit Tests"""
    return Student(
        id=1,
        matrikel_nr="IU12345678",
        vorname="Max",
        nachname="Mustermann",
        login_id=10
    )


@pytest.fixture
def sample_modul():
    """Beispiel-Modul fuer Unit Tests"""
    return Modul(
        id=1,
        name="Einfuehrung in die Programmierung",
        beschreibung="Grundlagen der Programmierung mit Python",
        ects=5
    )


@pytest.fixture
def sample_modulbuchung():
    """Beispiel-Modulbuchung fuer Unit Tests"""
    return Modulbuchung(
        id=1,
        einschreibung_id=100,
        modul_id=42,
        buchungsdatum=date(2024, 1, 15),
        status="gebucht"
    )


@pytest.fixture
def sample_pruefungsleistung():
    """Beispiel-Pruefungsleistung fuer Unit Tests"""
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
    """Beispiel-Gebuehr fuer Unit Tests"""
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
    """Beispiel-Einschreibung fuer Unit Tests"""
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
    """Beispiel-Studiengang fuer Unit Tests"""
    return Studiengang(
        id=1,
        name="Angewandte Kuenstliche Intelligenz",
        grad="B.Sc.",
        regel_semester=7,
        beschreibung="Bachelor of Science Angewandte KI"
    )


@pytest.fixture
def sample_progress():
    """Beispiel-Progress fuer Unit Tests"""
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
def sample_studiengang_modul():
    """Beispiel-StudiengangModul fuer Unit Tests"""
    return StudiengangModul(
        id=1,
        studiengang_id=1,
        modul_id=1,
        semester=1,
        pflichtgrad="Pflicht",
        wahlbereich=None
    )


@pytest.fixture
def sample_wahlmodul():
    """Beispiel-Wahlmodul (Bereich A) fuer Unit Tests"""
    return StudiengangModul(
        id=2,
        studiengang_id=1,
        modul_id=2,
        semester=5,
        pflichtgrad="Wahl",
        wahlbereich="A"
    )


@pytest.fixture
def sample_dates():
    """Haeufig verwendete Test-Daten"""
    return {
        'today': date.today(),
        'enrollment_date': date(2024, 1, 1),
        'exam_date': date(2024, 2, 1),
        'payment_due': date(2024, 2, 15),
    }


@pytest.fixture
def sample_notes():
    """Beispiel-Noten fuer Tests"""
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