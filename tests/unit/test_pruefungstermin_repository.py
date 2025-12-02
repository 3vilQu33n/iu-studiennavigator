# tests/unit/test_pruefungstermin_repository.py
"""
Unit Tests fuer PruefungsterminRepository (repositories/pruefungstermin_repository.py)

Testet das PruefungsterminRepository:
- find_by_id() - Termin nach ID laden
- find_by_modul() - Alle Termine fuer ein Modul
- find_verfuegbare_termine() - Verfuegbare Termine (komplexe Logik)
- create() - Neuen Termin erstellen
- update() - Termin aktualisieren
- delete() - Termin loeschen

Besonderer Fokus auf find_verfuegbare_termine():
- Nur Termine in der Zukunft
- Nur Termine vor Anmeldeschluss
- Kapazitaetspruefung
"""
from __future__ import annotations

import pytest
import sqlite3
import tempfile
import os
from datetime import date, time, datetime, timedelta

# Mark this whole module as unit tests
pytestmark = pytest.mark.unit


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def pruefungstermin_repository_class():
    """Importiert PruefungsterminRepository-Klasse"""
    try:
        from repositories import PruefungsterminRepository
        return PruefungsterminRepository
    except ImportError:
        from repositories.pruefungstermin_repository import PruefungsterminRepository
        return PruefungsterminRepository


@pytest.fixture
def pruefungstermin_class():
    """Importiert Pruefungstermin-Klasse"""
    try:
        from models import Pruefungstermin
        return Pruefungstermin
    except ImportError:
        from models.pruefungstermin import Pruefungstermin
        return Pruefungstermin


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
        CREATE TABLE IF NOT EXISTS modul (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            ects INTEGER NOT NULL,
            beschreibung TEXT
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

        CREATE TABLE IF NOT EXISTS modulbuchung (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            einschreibung_id INTEGER NOT NULL,
            modul_id INTEGER NOT NULL,
            buchungsdatum TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'gebucht'
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

        -- Testdaten: Module
        INSERT INTO modul (id, name, ects) VALUES
            (1, 'Mathematik I', 5),
            (2, 'Programmierung I', 5),
            (3, 'Datenbanken', 5);
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
def temp_db_with_termine(temp_db):
    """Test-DB mit vorhandenen Pruefungsterminen"""
    conn = sqlite3.connect(temp_db)
    conn.execute("PRAGMA foreign_keys = ON;")

    today = date.today()
    future_30 = (today + timedelta(days=30)).isoformat()
    future_60 = (today + timedelta(days=60)).isoformat()
    future_90 = (today + timedelta(days=90)).isoformat()
    past_30 = (today - timedelta(days=30)).isoformat()

    # Anmeldeschluss in der Zukunft
    anmeldeschluss_future = (datetime.now() + timedelta(days=7)).isoformat()
    # Anmeldeschluss in der Vergangenheit
    anmeldeschluss_past = (datetime.now() - timedelta(days=1)).isoformat()

    conn.executescript(f"""
        -- Termine fuer Modul 1 (Mathematik)
        INSERT INTO pruefungstermin (id, modul_id, datum, beginn, ende, art, ort, anmeldeschluss, kapazitaet, beschreibung) VALUES
            (1, 1, '{future_30}', '09:00', '11:00', 'online', NULL, '{anmeldeschluss_future}', 100, 'Online-Klausur'),
            (2, 1, '{future_60}', '14:00', '16:00', 'praesenz', 'Raum A101', '{anmeldeschluss_future}', 50, 'Praesenz-Klausur'),
            (3, 1, '{past_30}', '10:00', '12:00', 'online', NULL, NULL, NULL, 'Vergangener Termin');

        -- Termine fuer Modul 2 (Programmierung)
        INSERT INTO pruefungstermin (id, modul_id, datum, beginn, ende, art, kapazitaet) VALUES
            (4, 2, '{future_30}', '10:00', '12:00', 'online', 80),
            (5, 2, '{future_90}', '09:00', '11:00', 'projekt', NULL);

        -- Termin mit abgelaufenem Anmeldeschluss
        INSERT INTO pruefungstermin (id, modul_id, datum, beginn, ende, art, anmeldeschluss) VALUES
            (6, 1, '{future_60}', '10:00', '12:00', 'online', '{anmeldeschluss_past}');

        -- Termin mit voller Kapazitaet (wird spaeter gefuellt)
        INSERT INTO pruefungstermin (id, modul_id, datum, beginn, ende, art, kapazitaet, anmeldeschluss) VALUES
            (7, 3, '{future_30}', '14:00', '16:00', 'online', 2, '{anmeldeschluss_future}');

        -- Modulbuchungen fuer Kapazitaetstests
        INSERT INTO modulbuchung (id, einschreibung_id, modul_id, buchungsdatum, status) VALUES
            (1, 1, 3, '{today.isoformat()}', 'gebucht'),
            (2, 2, 3, '{today.isoformat()}', 'gebucht'),
            (3, 3, 3, '{today.isoformat()}', 'gebucht');

        -- 2 Anmeldungen fuer Termin 7 (voll)
        INSERT INTO pruefungsanmeldung (modulbuchung_id, pruefungstermin_id, status, angemeldet_am) VALUES
            (1, 7, 'angemeldet', '{datetime.now().isoformat()}'),
            (2, 7, 'angemeldet', '{datetime.now().isoformat()}');
    """)
    conn.commit()
    conn.close()

    return temp_db


@pytest.fixture
def repository(pruefungstermin_repository_class, temp_db):
    """Erstellt Repository-Instanz mit Test-DB"""
    return pruefungstermin_repository_class(temp_db)


@pytest.fixture
def repository_with_termine(pruefungstermin_repository_class, temp_db_with_termine):
    """Erstellt Repository-Instanz mit Test-DB inkl. Termine"""
    return pruefungstermin_repository_class(temp_db_with_termine)


@pytest.fixture
def sample_termin(pruefungstermin_class):
    """Erstellt Sample-Pruefungstermin fuer Tests"""
    return pruefungstermin_class(
        id=0,
        modul_id=1,
        datum=date.today() + timedelta(days=30),
        beginn=time(9, 0),
        ende=time(11, 0),
        art='online',
        ort=None,
        anmeldeschluss=datetime.now() + timedelta(days=7),
        kapazitaet=100,
        beschreibung='Test-Klausur'
    )


# ============================================================================
# INITIALIZATION TESTS
# ============================================================================

class TestPruefungsterminRepositoryInit:
    """Tests fuer Repository-Initialisierung"""

    def test_init_with_db_path(self, pruefungstermin_repository_class, temp_db):
        """Repository kann mit DB-Pfad initialisiert werden"""
        repo = pruefungstermin_repository_class(temp_db)

        assert repo.db_path == temp_db

    def test_init_stores_db_path(self, pruefungstermin_repository_class):
        """Repository speichert db_path"""
        repo = pruefungstermin_repository_class("/path/to/db.sqlite")

        assert repo.db_path == "/path/to/db.sqlite"


# ============================================================================
# FIND_BY_ID TESTS
# ============================================================================

class TestFindById:
    """Tests fuer find_by_id() Methode"""

    def test_find_by_id_existing(self, repository_with_termine, pruefungstermin_class):
        """find_by_id() laedt existierenden Termin"""
        result = repository_with_termine.find_by_id(1)

        assert result is not None
        assert isinstance(result, pruefungstermin_class)
        assert result.id == 1

    def test_find_by_id_correct_data(self, repository_with_termine):
        """find_by_id() laedt korrekte Daten"""
        result = repository_with_termine.find_by_id(1)

        assert result.modul_id == 1
        assert result.art == 'online'
        assert result.kapazitaet == 100
        assert result.beschreibung == 'Online-Klausur'

    def test_find_by_id_praesenz(self, repository_with_termine):
        """find_by_id() laedt Praesenz-Termin mit Ort"""
        result = repository_with_termine.find_by_id(2)

        assert result.art == 'praesenz'
        assert result.ort == 'Raum A101'

    def test_find_by_id_not_found(self, repository):
        """find_by_id() gibt None zurueck wenn nicht gefunden"""
        result = repository.find_by_id(999)

        assert result is None

    def test_find_by_id_loads_times(self, repository_with_termine):
        """find_by_id() laedt beginn und ende"""
        result = repository_with_termine.find_by_id(1)

        assert result.beginn is not None
        assert result.ende is not None


# ============================================================================
# FIND_BY_MODUL TESTS
# ============================================================================

class TestFindByModul:
    """Tests fuer find_by_modul() Methode"""

    def test_find_by_modul_returns_list(self, repository_with_termine):
        """find_by_modul() gibt Liste zurueck"""
        result = repository_with_termine.find_by_modul(1)

        assert isinstance(result, list)

    def test_find_by_modul_correct_count(self, repository_with_termine):
        """find_by_modul() gibt alle Termine zurueck"""
        # Modul 1 hat 4 Termine (ID 1, 2, 3, 6)
        result = repository_with_termine.find_by_modul(1)

        assert len(result) == 4

    def test_find_by_modul_ordered_by_datum(self, repository_with_termine):
        """find_by_modul() sortiert nach Datum aufsteigend"""
        result = repository_with_termine.find_by_modul(1)

        if len(result) >= 2:
            # Aufsteigend sortiert
            for i in range(len(result) - 1):
                assert result[i].datum <= result[i + 1].datum

    def test_find_by_modul_empty(self, repository):
        """find_by_modul() gibt leere Liste wenn keine Termine"""
        result = repository.find_by_modul(999)

        assert result == []

    def test_find_by_modul_includes_past(self, repository_with_termine):
        """find_by_modul() enthaelt auch vergangene Termine"""
        result = repository_with_termine.find_by_modul(1)

        # Termin 3 ist in der Vergangenheit
        past_termine = [t for t in result if t.datum < date.today()]
        assert len(past_termine) >= 1


# ============================================================================
# FIND_VERFUEGBARE_TERMINE TESTS
# ============================================================================

class TestFindVerfuegbareTermine:
    """Tests fuer find_verfuegbare_termine() Methode - komplexe Logik"""

    def test_find_verfuegbare_returns_list(self, repository_with_termine):
        """find_verfuegbare_termine() gibt Liste zurueck"""
        result = repository_with_termine.find_verfuegbare_termine(1)

        assert isinstance(result, list)

    def test_find_verfuegbare_excludes_past(self, repository_with_termine):
        """find_verfuegbare_termine() schliesst vergangene Termine aus"""
        result = repository_with_termine.find_verfuegbare_termine(1)

        today = date.today()
        for termin in result:
            assert termin.datum >= today

    def test_find_verfuegbare_excludes_expired_anmeldeschluss(self, repository_with_termine):
        """find_verfuegbare_termine() schliesst Termine mit abgelaufenem Anmeldeschluss aus"""
        result = repository_with_termine.find_verfuegbare_termine(1)

        # Termin 6 hat abgelaufenen Anmeldeschluss
        termin_ids = [t.id for t in result]
        assert 6 not in termin_ids

    def test_find_verfuegbare_includes_no_anmeldeschluss(self, repository_with_termine):
        """find_verfuegbare_termine() enthaelt Termine ohne Anmeldeschluss"""
        result = repository_with_termine.find_verfuegbare_termine(2)

        # Termin 5 hat keinen Anmeldeschluss (NULL)
        termin_ids = [t.id for t in result]
        assert 5 in termin_ids

    def test_find_verfuegbare_excludes_full_capacity(self, repository_with_termine):
        """find_verfuegbare_termine() schliesst volle Termine aus"""
        result = repository_with_termine.find_verfuegbare_termine(3)

        # Termin 7 hat Kapazitaet 2 und 2 Anmeldungen (voll)
        termin_ids = [t.id for t in result]
        assert 7 not in termin_ids

    def test_find_verfuegbare_includes_unlimited_capacity(self, repository_with_termine):
        """find_verfuegbare_termine() enthaelt Termine ohne Kapazitaetslimit"""
        result = repository_with_termine.find_verfuegbare_termine(2)

        # Termin 5 hat keine Kapazitaet (NULL = unbegrenzt)
        termin_ids = [t.id for t in result]
        assert 5 in termin_ids

    def test_find_verfuegbare_ordered_by_datum(self, repository_with_termine):
        """find_verfuegbare_termine() sortiert nach Datum aufsteigend"""
        result = repository_with_termine.find_verfuegbare_termine(1)

        if len(result) >= 2:
            for i in range(len(result) - 1):
                assert result[i].datum <= result[i + 1].datum

    def test_find_verfuegbare_empty_for_nonexistent_modul(self, repository):
        """find_verfuegbare_termine() gibt leere Liste fuer nicht existierendes Modul"""
        result = repository.find_verfuegbare_termine(999)

        assert result == []


# ============================================================================
# CREATE TESTS
# ============================================================================

class TestCreate:
    """Tests fuer create() Methode"""

    def test_create_returns_id(self, repository, sample_termin):
        """create() gibt neue ID zurueck"""
        new_id = repository.create(sample_termin)

        assert isinstance(new_id, int)
        assert new_id > 0

    def test_create_stores_data(self, repository, sample_termin):
        """create() speichert Daten korrekt"""
        new_id = repository.create(sample_termin)

        loaded = repository.find_by_id(new_id)
        assert loaded is not None
        assert loaded.modul_id == sample_termin.modul_id
        assert loaded.art == 'online'
        assert loaded.kapazitaet == 100

    def test_create_with_praesenz(self, repository, pruefungstermin_class):
        """create() speichert Praesenz-Termin mit Ort"""
        termin = pruefungstermin_class(
            id=0,
            modul_id=1,
            datum=date.today() + timedelta(days=30),
            beginn=time(14, 0),
            ende=time(16, 0),
            art='praesenz',
            ort='Raum B202',
            anmeldeschluss=None,
            kapazitaet=30,
            beschreibung='Praesenzklausur'
        )

        new_id = repository.create(termin)
        loaded = repository.find_by_id(new_id)

        assert loaded.art == 'praesenz'
        assert loaded.ort == 'Raum B202'

    def test_create_with_projekt(self, repository, pruefungstermin_class):
        """create() speichert Projekt-Termin"""
        termin = pruefungstermin_class(
            id=0,
            modul_id=2,
            datum=date.today() + timedelta(days=60),
            beginn=None,
            ende=None,
            art='projekt',
            ort=None,
            anmeldeschluss=None,
            kapazitaet=None,
            beschreibung='Projektabgabe'
        )

        new_id = repository.create(termin)
        loaded = repository.find_by_id(new_id)

        assert loaded.art == 'projekt'
        assert loaded.beginn is None
        assert loaded.ende is None

    def test_create_increments_id(self, repository, pruefungstermin_class):
        """create() inkrementiert IDs"""
        t1 = pruefungstermin_class(
            id=0,
            modul_id=1,
            datum=date.today() + timedelta(days=30),
            beginn=time(9, 0),
            ende=time(11, 0),
            art='online',
            ort=None,
            anmeldeschluss=None,
            kapazitaet=None,
            beschreibung=None
        )
        t2 = pruefungstermin_class(
            id=0,
            modul_id=2,
            datum=date.today() + timedelta(days=60),
            beginn=time(14, 0),
            ende=time(16, 0),
            art='online',
            ort=None,
            anmeldeschluss=None,
            kapazitaet=None,
            beschreibung=None
        )

        id1 = repository.create(t1)
        id2 = repository.create(t2)

        assert id2 > id1


# ============================================================================
# UPDATE TESTS
# ============================================================================

class TestUpdate:
    """Tests fuer update() Methode"""

    def test_update_success(self, repository_with_termine):
        """update() aktualisiert Termin erfolgreich"""
        termin = repository_with_termine.find_by_id(1)
        termin.kapazitaet = 200
        termin.beschreibung = 'Aktualisierte Beschreibung'

        result = repository_with_termine.update(termin)

        assert result is True

        loaded = repository_with_termine.find_by_id(1)
        assert loaded.kapazitaet == 200
        assert loaded.beschreibung == 'Aktualisierte Beschreibung'

    def test_update_art(self, repository_with_termine):
        """update() kann Art aendern"""
        termin = repository_with_termine.find_by_id(1)
        termin.art = 'praesenz'
        termin.ort = 'Neuer Raum'

        repository_with_termine.update(termin)

        loaded = repository_with_termine.find_by_id(1)
        assert loaded.art == 'praesenz'
        assert loaded.ort == 'Neuer Raum'

    def test_update_datum(self, repository_with_termine):
        """update() kann Datum aendern"""
        termin = repository_with_termine.find_by_id(1)
        new_datum = date.today() + timedelta(days=100)
        termin.datum = new_datum

        repository_with_termine.update(termin)

        loaded = repository_with_termine.find_by_id(1)
        assert loaded.datum == new_datum

    def test_update_returns_true(self, repository_with_termine):
        """update() gibt True zurueck"""
        termin = repository_with_termine.find_by_id(1)
        termin.kapazitaet = 50

        result = repository_with_termine.update(termin)

        assert result is True


# ============================================================================
# DELETE TESTS
# ============================================================================

class TestDelete:
    """Tests fuer delete() Methode"""

    def test_delete_success(self, repository_with_termine):
        """delete() loescht Termin erfolgreich"""
        # Termin existiert
        before = repository_with_termine.find_by_id(1)
        assert before is not None

        # Loeschen
        result = repository_with_termine.delete(1)
        assert result is True

        # Termin existiert nicht mehr
        after = repository_with_termine.find_by_id(1)
        assert after is None

    def test_delete_returns_true(self, repository_with_termine):
        """delete() gibt True zurueck"""
        result = repository_with_termine.delete(1)

        assert result is True

    def test_delete_reduces_modul_termine(self, repository_with_termine):
        """delete() reduziert Anzahl der Termine fuer Modul"""
        # Vorher
        before = len(repository_with_termine.find_by_modul(1))

        # Loeschen
        repository_with_termine.delete(1)

        # Nachher
        after = len(repository_with_termine.find_by_modul(1))

        assert after == before - 1


# ============================================================================
# PRIVATE METHOD TESTS
# ============================================================================

class TestPrivateMethods:
    """Tests fuer private Hilfsmethoden"""

    def test_get_connection_returns_connection(self, repository):
        """__get_connection() gibt Connection zurueck"""
        conn = repository._PruefungsterminRepository__get_connection()

        assert isinstance(conn, sqlite3.Connection)
        conn.close()

    def test_get_connection_enables_foreign_keys(self, repository):
        """__get_connection() aktiviert Foreign Keys"""
        conn = repository._PruefungsterminRepository__get_connection()

        result = conn.execute("PRAGMA foreign_keys;").fetchone()
        assert result[0] == 1

        conn.close()


# ============================================================================
# INTEGRATION-LIKE TESTS
# ============================================================================

class TestIntegrationScenarios:
    """Tests fuer typische Nutzungsszenarien"""

    def test_full_termin_lifecycle(self, repository, pruefungstermin_class):
        """Test: Vollstaendiger Termin-Lebenszyklus"""
        # 1. Termin erstellen
        termin = pruefungstermin_class(
            id=0,
            modul_id=1,
            datum=date.today() + timedelta(days=30),
            beginn=time(9, 0),
            ende=time(11, 0),
            art='online',
            ort=None,
            anmeldeschluss=datetime.now() + timedelta(days=7),
            kapazitaet=100,
            beschreibung='Neue Klausur'
        )
        termin_id = repository.create(termin)

        # 2. Laden und pruefen
        loaded = repository.find_by_id(termin_id)
        assert loaded.beschreibung == 'Neue Klausur'

        # 3. Aktualisieren
        loaded.kapazitaet = 150
        repository.update(loaded)

        # 4. Pruefen
        updated = repository.find_by_id(termin_id)
        assert updated.kapazitaet == 150

        # 5. Loeschen
        repository.delete(termin_id)
        assert repository.find_by_id(termin_id) is None

    def test_modul_pruefungstermine_overview(self, repository_with_termine):
        """Test: Uebersicht aller Termine fuer ein Modul"""
        # Alle Termine laden
        alle = repository_with_termine.find_by_modul(1)

        # Verfuegbare Termine laden
        verfuegbar = repository_with_termine.find_verfuegbare_termine(1)

        # Verfuegbare sollten Teilmenge von allen sein
        verfuegbar_ids = {t.id for t in verfuegbar}
        alle_ids = {t.id for t in alle}

        assert verfuegbar_ids.issubset(alle_ids)

    def test_capacity_workflow(self, repository_with_termine, temp_db_with_termine):
        """Test: Kapazitaets-Workflow"""
        # Termin 7 ist voll (Kapazitaet 2, 2 Anmeldungen)
        verfuegbar = repository_with_termine.find_verfuegbare_termine(3)
        assert 7 not in [t.id for t in verfuegbar]

        # Storniere eine Anmeldung
        conn = sqlite3.connect(temp_db_with_termine)
        conn.execute("UPDATE pruefungsanmeldung SET status = 'storniert' WHERE modulbuchung_id = 1")
        conn.commit()
        conn.close()

        # Jetzt sollte Termin 7 verfuegbar sein
        verfuegbar_after = repository_with_termine.find_verfuegbare_termine(3)
        assert 7 in [t.id for t in verfuegbar_after]


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

    def test_create_with_string_dates(self, repository, pruefungstermin_class):
        """create() funktioniert mit String-Datumswerten"""
        termin = pruefungstermin_class(
            id=0,
            modul_id=1,
            datum='2025-12-15',  # String statt date
            beginn='09:00',  # String statt time
            ende='11:00',  # String statt time
            art='online',
            ort=None,
            anmeldeschluss='2025-12-10T12:00:00',  # String statt datetime
            kapazitaet=50,
            beschreibung='String-Datum Test'
        )

        new_id = repository.create(termin)
        loaded = repository.find_by_id(new_id)

        assert loaded is not None
        assert loaded.beschreibung == 'String-Datum Test'

    def test_termin_ohne_zeitfenster(self, repository, pruefungstermin_class):
        """Termin ohne beginn/ende (z.B. Projekt)"""
        termin = pruefungstermin_class(
            id=0,
            modul_id=1,
            datum=date.today() + timedelta(days=30),
            beginn=None,
            ende=None,
            art='projekt',
            ort=None,
            anmeldeschluss=None,
            kapazitaet=None,
            beschreibung='Projektabgabe ohne Zeitfenster'
        )

        new_id = repository.create(termin)
        loaded = repository.find_by_id(new_id)

        assert loaded.beginn is None
        assert loaded.ende is None
        assert loaded.hat_zeitfenster() is False

    def test_termin_mit_grosser_kapazitaet(self, repository, pruefungstermin_class):
        """Termin mit sehr grosser Kapazitaet"""
        termin = pruefungstermin_class(
            id=0,
            modul_id=1,
            datum=date.today() + timedelta(days=30),
            beginn=time(9, 0),
            ende=time(11, 0),
            art='online',
            ort=None,
            anmeldeschluss=None,
            kapazitaet=10000,
            beschreibung='Grosse Online-Klausur'
        )

        new_id = repository.create(termin)
        loaded = repository.find_by_id(new_id)

        assert loaded.kapazitaet == 10000

    def test_verschiedene_pruefungsarten(self, repository, pruefungstermin_class):
        """Verschiedene Pruefungsarten speichern"""
        arten = ['online', 'praesenz', 'projekt', 'workbook']

        for art in arten:
            termin = pruefungstermin_class(
                id=0,
                modul_id=1,
                datum=date.today() + timedelta(days=30),
                beginn=time(9, 0) if art != 'projekt' else None,
                ende=time(11, 0) if art != 'projekt' else None,
                art=art,
                ort='Raum A1' if art == 'praesenz' else None,
                anmeldeschluss=None,
                kapazitaet=None,
                beschreibung=f'{art}-Pruefung'
            )

            new_id = repository.create(termin)
            loaded = repository.find_by_id(new_id)

            assert loaded.art == art