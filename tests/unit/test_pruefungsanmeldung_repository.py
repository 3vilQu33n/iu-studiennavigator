# tests/unit/test_pruefungsanmeldung_repository.py
"""
Unit Tests fuer PruefungsanmeldungRepository (repositories/pruefungsanmeldung_repository.py)

Testet das PruefungsanmeldungRepository:
- find_by_id() - Anmeldung nach ID laden
- find_by_modulbuchung() - Anmeldung fuer Modulbuchung laden
- find_by_student() - Alle Anmeldungen eines Studenten
- find_by_termin() - Alle Anmeldungen fuer einen Termin
- create() - Neue Anmeldung erstellen
- update_status() - Status aktualisieren
- stornieren() - Anmeldung stornieren
- anzahl_anmeldungen_fuer_termin() - Aktive Anmeldungen zaehlen
- hat_aktive_anmeldung() - Pruefen ob aktive Anmeldung existiert
"""
from __future__ import annotations

import pytest
import sqlite3
import tempfile
import os
from datetime import date, datetime, timedelta

# Mark this whole module as unit tests
pytestmark = pytest.mark.unit


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def pruefungsanmeldung_repository_class():
    """Importiert PruefungsanmeldungRepository-Klasse"""
    try:
        from repositories import PruefungsanmeldungRepository
        return PruefungsanmeldungRepository
    except ImportError:
        from repositories.pruefungsanmeldung_repository import PruefungsanmeldungRepository
        return PruefungsanmeldungRepository


@pytest.fixture
def pruefungsanmeldung_class():
    """Importiert Pruefungsanmeldung-Klasse"""
    try:
        from models import Pruefungsanmeldung
        return Pruefungsanmeldung
    except ImportError:
        from models.pruefungsanmeldung import Pruefungsanmeldung
        return Pruefungsanmeldung


@pytest.fixture
def temp_db():
    """Erstellt temporaere Test-Datenbank mit vollstaendigem Schema"""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)

    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON;")

    today = date.today()

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

        CREATE TABLE IF NOT EXISTS modulbuchung (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            einschreibung_id INTEGER NOT NULL,
            modul_id INTEGER NOT NULL,
            buchungsdatum TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'gebucht',
            FOREIGN KEY (einschreibung_id) REFERENCES einschreibung(id),
            FOREIGN KEY (modul_id) REFERENCES modul(id)
        );

        CREATE TABLE IF NOT EXISTS pruefungstermin (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            modul_id INTEGER NOT NULL,
            datum TEXT NOT NULL,
            beginn TEXT,
            ende TEXT,
            art TEXT NOT NULL DEFAULT 'online',
            ort TEXT,
            anmeldeschluss TEXT,
            kapazitaet INTEGER,
            beschreibung TEXT,
            FOREIGN KEY (modul_id) REFERENCES modul(id)
        );

        CREATE TABLE IF NOT EXISTS pruefungsanmeldung (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            modulbuchung_id INTEGER NOT NULL,
            pruefungstermin_id INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'angemeldet',
            angemeldet_am TEXT NOT NULL,
            FOREIGN KEY (modulbuchung_id) REFERENCES modulbuchung(id),
            FOREIGN KEY (pruefungstermin_id) REFERENCES pruefungstermin(id)
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
            (3, 'Datenbanken', 5);

        -- Testdaten: Modulbuchungen
        INSERT INTO modulbuchung (id, einschreibung_id, modul_id, buchungsdatum, status) VALUES
            (1, 1, 1, '{today.isoformat()}', 'gebucht'),
            (2, 1, 2, '{today.isoformat()}', 'gebucht'),
            (3, 2, 1, '{today.isoformat()}', 'gebucht');

        -- Testdaten: Pruefungstermine
        INSERT INTO pruefungstermin (id, modul_id, datum, beginn, ende, art, kapazitaet) VALUES
            (1, 1, '{(today + timedelta(days=30)).isoformat()}', '09:00', '11:00', 'online', 100),
            (2, 1, '{(today + timedelta(days=60)).isoformat()}', '14:00', '16:00', 'praesenz', 50),
            (3, 2, '{(today + timedelta(days=45)).isoformat()}', '10:00', '12:00', 'online', 80);
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
def temp_db_with_anmeldungen(temp_db):
    """Test-DB mit vorhandenen Pruefungsanmeldungen"""
    conn = sqlite3.connect(temp_db)
    conn.execute("PRAGMA foreign_keys = ON;")

    now = datetime.now()
    yesterday = now - timedelta(days=1)
    last_week = now - timedelta(days=7)

    conn.executescript(f"""
        -- Anmeldungen fuer Student 1
        INSERT INTO pruefungsanmeldung (id, modulbuchung_id, pruefungstermin_id, status, angemeldet_am) VALUES
            (1, 1, 1, 'angemeldet', '{now.isoformat()}'),
            (2, 2, 3, 'angemeldet', '{yesterday.isoformat()}');

        -- Anmeldung fuer Student 2
        INSERT INTO pruefungsanmeldung (id, modulbuchung_id, pruefungstermin_id, status, angemeldet_am) VALUES
            (3, 3, 1, 'angemeldet', '{last_week.isoformat()}');

        -- Stornierte Anmeldung
        INSERT INTO pruefungsanmeldung (id, modulbuchung_id, pruefungstermin_id, status, angemeldet_am) VALUES
            (4, 1, 2, 'storniert', '{last_week.isoformat()}');
    """)
    conn.commit()
    conn.close()

    return temp_db


@pytest.fixture
def repository(pruefungsanmeldung_repository_class, temp_db):
    """Erstellt Repository-Instanz mit Test-DB"""
    return pruefungsanmeldung_repository_class(temp_db)


@pytest.fixture
def repository_with_anmeldungen(pruefungsanmeldung_repository_class, temp_db_with_anmeldungen):
    """Erstellt Repository-Instanz mit Test-DB inkl. Anmeldungen"""
    return pruefungsanmeldung_repository_class(temp_db_with_anmeldungen)


@pytest.fixture
def sample_anmeldung(pruefungsanmeldung_class):
    """Erstellt Sample-Pruefungsanmeldung fuer Tests"""
    return pruefungsanmeldung_class(
        id=0,
        modulbuchung_id=1,
        pruefungstermin_id=1,
        status='angemeldet',
        angemeldet_am=datetime.now()
    )


# ============================================================================
# INITIALIZATION TESTS
# ============================================================================

class TestPruefungsanmeldungRepositoryInit:
    """Tests fuer Repository-Initialisierung"""

    def test_init_with_db_path(self, pruefungsanmeldung_repository_class, temp_db):
        """Repository kann mit DB-Pfad initialisiert werden"""
        repo = pruefungsanmeldung_repository_class(temp_db)

        assert repo.db_path == temp_db

    def test_init_stores_db_path(self, pruefungsanmeldung_repository_class):
        """Repository speichert db_path"""
        repo = pruefungsanmeldung_repository_class("/path/to/db.sqlite")

        assert repo.db_path == "/path/to/db.sqlite"


# ============================================================================
# FIND_BY_ID TESTS
# ============================================================================

class TestFindById:
    """Tests fuer find_by_id() Methode"""

    def test_find_by_id_existing(self, repository_with_anmeldungen, pruefungsanmeldung_class):
        """find_by_id() laedt existierende Anmeldung"""
        result = repository_with_anmeldungen.find_by_id(1)

        assert result is not None
        assert isinstance(result, pruefungsanmeldung_class)
        assert result.id == 1

    def test_find_by_id_correct_data(self, repository_with_anmeldungen):
        """find_by_id() laedt korrekte Daten"""
        result = repository_with_anmeldungen.find_by_id(1)

        assert result.modulbuchung_id == 1
        assert result.pruefungstermin_id == 1
        assert result.status == 'angemeldet'

    def test_find_by_id_not_found(self, repository):
        """find_by_id() gibt None zurueck wenn nicht gefunden"""
        result = repository.find_by_id(999)

        assert result is None

    def test_find_by_id_storniert(self, repository_with_anmeldungen):
        """find_by_id() laedt auch stornierte Anmeldungen"""
        result = repository_with_anmeldungen.find_by_id(4)

        assert result is not None
        assert result.status == 'storniert'


# ============================================================================
# FIND_BY_MODULBUCHUNG TESTS
# ============================================================================

class TestFindByModulbuchung:
    """Tests fuer find_by_modulbuchung() Methode"""

    def test_find_by_modulbuchung_existing(self, repository_with_anmeldungen, pruefungsanmeldung_class):
        """find_by_modulbuchung() laedt Anmeldung fuer Modulbuchung"""
        result = repository_with_anmeldungen.find_by_modulbuchung(1)

        assert result is not None
        assert isinstance(result, pruefungsanmeldung_class)
        assert result.modulbuchung_id == 1

    def test_find_by_modulbuchung_returns_latest(self, repository_with_anmeldungen):
        """find_by_modulbuchung() gibt neueste Anmeldung zurueck"""
        # Modulbuchung 1 hat 2 Anmeldungen (ID 1 und 4)
        result = repository_with_anmeldungen.find_by_modulbuchung(1)

        # ID 1 ist neuer (angemeldet heute vs. storniert letzte Woche)
        assert result.id == 1

    def test_find_by_modulbuchung_not_found(self, repository):
        """find_by_modulbuchung() gibt None wenn keine Anmeldung"""
        result = repository.find_by_modulbuchung(999)

        assert result is None


# ============================================================================
# FIND_BY_STUDENT TESTS
# ============================================================================

class TestFindByStudent:
    """Tests fuer find_by_student() Methode"""

    def test_find_by_student_returns_list(self, repository_with_anmeldungen):
        """find_by_student() gibt Liste zurueck"""
        result = repository_with_anmeldungen.find_by_student(1)

        assert isinstance(result, list)

    def test_find_by_student_correct_count(self, repository_with_anmeldungen):
        """find_by_student() gibt alle Anmeldungen zurueck"""
        # Student 1 (einschreibung_id=1) hat 3 Anmeldungen (ID 1, 2, 4)
        result = repository_with_anmeldungen.find_by_student(1)

        assert len(result) == 3

    def test_find_by_student_ordered_by_date_desc(self, repository_with_anmeldungen):
        """find_by_student() sortiert nach angemeldet_am absteigend"""
        result = repository_with_anmeldungen.find_by_student(1)

        if len(result) >= 2:
            # Neueste zuerst
            assert result[0].angemeldet_am >= result[-1].angemeldet_am

    def test_find_by_student_empty(self, repository):
        """find_by_student() gibt leere Liste wenn keine Anmeldungen"""
        result = repository.find_by_student(999)

        assert result == []

    def test_find_by_student_other_student(self, repository_with_anmeldungen):
        """find_by_student() gibt nur Anmeldungen des Studenten zurueck"""
        # Student 2 (einschreibung_id=2) hat 1 Anmeldung
        result = repository_with_anmeldungen.find_by_student(2)

        assert len(result) == 1
        assert result[0].id == 3


# ============================================================================
# FIND_BY_TERMIN TESTS
# ============================================================================

class TestFindByTermin:
    """Tests fuer find_by_termin() Methode"""

    def test_find_by_termin_returns_list(self, repository_with_anmeldungen):
        """find_by_termin() gibt Liste zurueck"""
        result = repository_with_anmeldungen.find_by_termin(1)

        assert isinstance(result, list)

    def test_find_by_termin_correct_count(self, repository_with_anmeldungen):
        """find_by_termin() gibt alle Anmeldungen fuer Termin zurueck"""
        # Termin 1 hat 2 Anmeldungen (ID 1 und 3)
        result = repository_with_anmeldungen.find_by_termin(1)

        assert len(result) == 2

    def test_find_by_termin_ordered_by_date_asc(self, repository_with_anmeldungen):
        """find_by_termin() sortiert nach angemeldet_am aufsteigend"""
        result = repository_with_anmeldungen.find_by_termin(1)

        if len(result) >= 2:
            # Aelteste zuerst
            assert result[0].angemeldet_am <= result[-1].angemeldet_am

    def test_find_by_termin_empty(self, repository):
        """find_by_termin() gibt leere Liste wenn keine Anmeldungen"""
        result = repository.find_by_termin(999)

        assert result == []


# ============================================================================
# CREATE TESTS
# ============================================================================

class TestCreate:
    """Tests fuer create() Methode"""

    def test_create_returns_id(self, repository, sample_anmeldung):
        """create() gibt neue ID zurueck"""
        new_id = repository.create(sample_anmeldung)

        assert isinstance(new_id, int)
        assert new_id > 0

    def test_create_stores_data(self, repository, sample_anmeldung):
        """create() speichert Daten korrekt"""
        new_id = repository.create(sample_anmeldung)

        loaded = repository.find_by_id(new_id)
        assert loaded is not None
        assert loaded.modulbuchung_id == sample_anmeldung.modulbuchung_id
        assert loaded.pruefungstermin_id == sample_anmeldung.pruefungstermin_id
        assert loaded.status == 'angemeldet'

    def test_create_sets_angemeldet_am(self, repository, pruefungsanmeldung_class):
        """create() setzt angemeldet_am wenn nicht gesetzt"""
        anmeldung = pruefungsanmeldung_class(
            id=0,
            modulbuchung_id=1,
            pruefungstermin_id=1,
            status='angemeldet',
            angemeldet_am=None
        )

        new_id = repository.create(anmeldung)
        loaded = repository.find_by_id(new_id)

        assert loaded.angemeldet_am is not None

    def test_create_increments_id(self, repository, pruefungsanmeldung_class):
        """create() inkrementiert IDs"""
        a1 = pruefungsanmeldung_class(
            id=0,
            modulbuchung_id=1,
            pruefungstermin_id=1,
            status='angemeldet',
            angemeldet_am=datetime.now()
        )
        a2 = pruefungsanmeldung_class(
            id=0,
            modulbuchung_id=2,
            pruefungstermin_id=3,
            status='angemeldet',
            angemeldet_am=datetime.now()
        )

        id1 = repository.create(a1)
        id2 = repository.create(a2)

        assert id2 > id1


# ============================================================================
# UPDATE_STATUS TESTS
# ============================================================================

class TestUpdateStatus:
    """Tests fuer update_status() Methode"""

    def test_update_status_success(self, repository_with_anmeldungen):
        """update_status() aendert Status erfolgreich"""
        result = repository_with_anmeldungen.update_status(1, 'absolviert')

        assert result is True

        loaded = repository_with_anmeldungen.find_by_id(1)
        assert loaded.status == 'absolviert'

    def test_update_status_various_values(self, repository_with_anmeldungen):
        """update_status() kann verschiedene Status setzen"""
        for status in ['angemeldet', 'storniert', 'absolviert']:
            repository_with_anmeldungen.update_status(1, status)
            loaded = repository_with_anmeldungen.find_by_id(1)
            assert loaded.status == status

    def test_update_status_returns_true(self, repository_with_anmeldungen):
        """update_status() gibt True zurueck"""
        result = repository_with_anmeldungen.update_status(1, 'storniert')

        assert result is True


# ============================================================================
# STORNIEREN TESTS
# ============================================================================

class TestStornieren:
    """Tests fuer stornieren() Methode"""

    def test_stornieren_success(self, repository_with_anmeldungen):
        """stornieren() setzt Status auf 'storniert'"""
        result = repository_with_anmeldungen.stornieren(1)

        assert result is True

        loaded = repository_with_anmeldungen.find_by_id(1)
        assert loaded.status == 'storniert'

    def test_stornieren_returns_true(self, repository_with_anmeldungen):
        """stornieren() gibt True zurueck"""
        result = repository_with_anmeldungen.stornieren(1)

        assert result is True

    def test_stornieren_reduces_aktive_count(self, repository_with_anmeldungen):
        """stornieren() reduziert Anzahl aktiver Anmeldungen"""
        # Vorher
        before = repository_with_anmeldungen.anzahl_anmeldungen_fuer_termin(1)

        # Stornieren
        repository_with_anmeldungen.stornieren(1)

        # Nachher
        after = repository_with_anmeldungen.anzahl_anmeldungen_fuer_termin(1)

        assert after == before - 1


# ============================================================================
# ANZAHL_ANMELDUNGEN_FUER_TERMIN TESTS
# ============================================================================

class TestAnzahlAnmeldungenFuerTermin:
    """Tests fuer anzahl_anmeldungen_fuer_termin() Methode"""

    def test_anzahl_returns_int(self, repository_with_anmeldungen):
        """anzahl_anmeldungen_fuer_termin() gibt int zurueck"""
        result = repository_with_anmeldungen.anzahl_anmeldungen_fuer_termin(1)

        assert isinstance(result, int)

    def test_anzahl_correct_count(self, repository_with_anmeldungen):
        """anzahl_anmeldungen_fuer_termin() zaehlt korrekt"""
        # Termin 1 hat 2 aktive Anmeldungen (ID 1 und 3)
        result = repository_with_anmeldungen.anzahl_anmeldungen_fuer_termin(1)

        assert result == 2

    def test_anzahl_excludes_storniert(self, repository_with_anmeldungen):
        """anzahl_anmeldungen_fuer_termin() schliesst stornierte aus"""
        # Termin 2 hat nur 1 Anmeldung (ID 4), die storniert ist
        result = repository_with_anmeldungen.anzahl_anmeldungen_fuer_termin(2)

        assert result == 0

    def test_anzahl_zero_for_empty(self, repository):
        """anzahl_anmeldungen_fuer_termin() gibt 0 wenn keine Anmeldungen"""
        result = repository.anzahl_anmeldungen_fuer_termin(999)

        assert result == 0


# ============================================================================
# HAT_AKTIVE_ANMELDUNG TESTS
# ============================================================================

class TestHatAktiveAnmeldung:
    """Tests fuer hat_aktive_anmeldung() Methode"""

    def test_hat_aktive_true(self, repository_with_anmeldungen):
        """hat_aktive_anmeldung() gibt True wenn aktive Anmeldung existiert"""
        # Modulbuchung 1 hat aktive Anmeldung (ID 1)
        result = repository_with_anmeldungen.hat_aktive_anmeldung(1)

        assert result is True

    def test_hat_aktive_false_keine(self, repository):
        """hat_aktive_anmeldung() gibt False wenn keine Anmeldung"""
        result = repository.hat_aktive_anmeldung(1)

        assert result is False

    def test_hat_aktive_false_storniert(self, repository_with_anmeldungen):
        """hat_aktive_anmeldung() gibt False wenn nur stornierte"""
        # Storniere die aktive Anmeldung fuer Modulbuchung 1
        repository_with_anmeldungen.stornieren(1)

        # Jetzt sollte nur die stornierte (ID 4) uebrig sein
        # Aber ID 4 war bereits storniert und gehoert zu Termin 2
        # Wir brauchen eine Modulbuchung die NUR stornierte hat

        # Modulbuchung 3 hat nur eine aktive Anmeldung
        repository_with_anmeldungen.stornieren(3)
        result = repository_with_anmeldungen.hat_aktive_anmeldung(3)

        assert result is False


# ============================================================================
# PRIVATE METHOD TESTS
# ============================================================================

class TestPrivateMethods:
    """Tests fuer private Hilfsmethoden"""

    def test_get_connection_returns_connection(self, repository):
        """__get_connection() gibt Connection zurueck"""
        conn = repository._PruefungsanmeldungRepository__get_connection()

        assert isinstance(conn, sqlite3.Connection)
        conn.close()

    def test_get_connection_enables_foreign_keys(self, repository):
        """__get_connection() aktiviert Foreign Keys"""
        conn = repository._PruefungsanmeldungRepository__get_connection()

        result = conn.execute("PRAGMA foreign_keys;").fetchone()
        assert result[0] == 1

        conn.close()


# ============================================================================
# INTEGRATION-LIKE TESTS
# ============================================================================

class TestIntegrationScenarios:
    """Tests fuer typische Nutzungsszenarien"""

    def test_full_anmeldung_lifecycle(self, repository, pruefungsanmeldung_class):
        """Test: Vollstaendiger Anmeldungs-Lebenszyklus"""
        # 1. Anmeldung erstellen
        anmeldung = pruefungsanmeldung_class(
            id=0,
            modulbuchung_id=1,
            pruefungstermin_id=1,
            status='angemeldet',
            angemeldet_am=datetime.now()
        )
        anmeldung_id = repository.create(anmeldung)

        # 2. Pruefen ob aktiv
        assert repository.hat_aktive_anmeldung(1) is True

        # 3. Stornieren
        repository.stornieren(anmeldung_id)

        # 4. Pruefen ob nicht mehr aktiv
        assert repository.hat_aktive_anmeldung(1) is False

    def test_kapazitaetspruefung_workflow(self, repository, pruefungsanmeldung_class):
        """Test: Kapazitaetspruefung Workflow"""
        # 1. Anzahl pruefen (0)
        count_before = repository.anzahl_anmeldungen_fuer_termin(1)
        assert count_before == 0

        # 2. Anmeldung erstellen
        anmeldung = pruefungsanmeldung_class(
            id=0,
            modulbuchung_id=1,
            pruefungstermin_id=1,
            status='angemeldet',
            angemeldet_am=datetime.now()
        )
        repository.create(anmeldung)

        # 3. Anzahl erhoet sich
        count_after = repository.anzahl_anmeldungen_fuer_termin(1)
        assert count_after == count_before + 1

    def test_student_anmeldungen_uebersicht(self, repository_with_anmeldungen):
        """Test: Studenten-Anmeldungen Uebersicht"""
        # Alle Anmeldungen fuer Student 1 laden
        anmeldungen = repository_with_anmeldungen.find_by_student(1)

        # 3 Anmeldungen insgesamt
        assert len(anmeldungen) == 3

        # Status-Verteilung pruefen
        aktiv = sum(1 for a in anmeldungen if a.status == 'angemeldet')
        storniert = sum(1 for a in anmeldungen if a.status == 'storniert')

        assert aktiv == 2
        assert storniert == 1


# ============================================================================
# EDGE CASES
# ============================================================================

class TestEdgeCases:
    """Tests fuer Randfaelle"""

    def test_find_by_id_zero(self, repository):
        """find_by_id() mit ID 0 gibt None zurueck"""
        result = repository.find_by_id(0)

        assert result is None

    def test_find_by_id_negative(self, repository):
        """find_by_id() mit negativer ID gibt None zurueck"""
        result = repository.find_by_id(-1)

        assert result is None

    def test_multiple_anmeldungen_same_modulbuchung(self, repository, pruefungsanmeldung_class):
        """Mehrere Anmeldungen fuer gleiche Modulbuchung (verschiedene Termine)"""
        # Erste Anmeldung
        a1 = pruefungsanmeldung_class(
            id=0,
            modulbuchung_id=1,
            pruefungstermin_id=1,
            status='angemeldet',
            angemeldet_am=datetime.now() - timedelta(days=1)
        )
        repository.create(a1)

        # Zweite Anmeldung (anderer Termin, spaeter)
        a2 = pruefungsanmeldung_class(
            id=0,
            modulbuchung_id=1,
            pruefungstermin_id=2,
            status='angemeldet',
            angemeldet_am=datetime.now()
        )
        repository.create(a2)

        # find_by_modulbuchung gibt neueste zurueck
        result = repository.find_by_modulbuchung(1)
        assert result.pruefungstermin_id == 2

    def test_anmeldung_mit_vergangenem_datum(self, repository, pruefungsanmeldung_class):
        """Anmeldung mit Datum in der Vergangenheit"""
        past_date = datetime(2020, 1, 1, 10, 0, 0)
        anmeldung = pruefungsanmeldung_class(
            id=0,
            modulbuchung_id=1,
            pruefungstermin_id=1,
            status='angemeldet',
            angemeldet_am=past_date
        )

        new_id = repository.create(anmeldung)
        loaded = repository.find_by_id(new_id)

        # Datum sollte gespeichert sein
        assert loaded.angemeldet_am is not None