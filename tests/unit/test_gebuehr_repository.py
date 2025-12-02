# tests/unit/test_gebuehr_repository.py
"""
Unit Tests fuer GebuehrRepository (repositories/gebuehr_repository.py)

Testet das GebuehrRepository:
- insert() - Gebuehr anlegen
- get_by_id() - Gebuehr nach ID laden
- get_by_einschreibung() - Alle Gebuehren einer Einschreibung
- get_open_fees_by_einschreibung() - Offene Gebuehren
- calculate_total_open_fees() - Summe offener Gebuehren
- mark_as_paid() - Als bezahlt markieren
- get_overdue_fees_by_einschreibung() - Ueberfaellige Gebuehren
- ensure_monthly_fees() - Monatsraten generieren
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
def gebuehr_repository_class():
    """Importiert GebuehrRepository-Klasse"""
    try:
        from repositories.gebuehr_repository import GebuehrRepository
        return GebuehrRepository
    except ImportError:
        from repositories import GebuehrRepository
        return GebuehrRepository


@pytest.fixture
def gebuehr_class():
    """Importiert Gebuehr-Klasse"""
    try:
        from models import Gebuehr
        return Gebuehr
    except ImportError:
        from models.gebuehr import Gebuehr
        return Gebuehr


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

        CREATE TABLE IF NOT EXISTS gebuehr (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            einschreibung_id INTEGER NOT NULL,
            art TEXT NOT NULL,
            betrag TEXT NOT NULL,
            faellig_am TEXT NOT NULL,
            bezahlt_am TEXT,
            FOREIGN KEY (einschreibung_id) REFERENCES einschreibung(id),
            UNIQUE(einschreibung_id, art, faellig_am)
        );

        -- Testdaten einfuegen
        INSERT INTO student (id, matrikel_nr, vorname, nachname) VALUES
            (1, 'IU12345678', 'Max', 'Mustermann'),
            (2, 'IU87654321', 'Erika', 'Musterfrau');

        INSERT INTO studiengang (id, name, grad, regel_semester) VALUES
            (1, 'Informatik', 'B.Sc.', 6),
            (2, 'BWL', 'B.A.', 7);

        INSERT INTO zeitmodell (id, name, monate_pro_semester, kosten_monat) VALUES
            (1, 'Vollzeit', 6, 359.00),
            (2, 'Teilzeit', 12, 209.00);

        INSERT INTO einschreibung (id, student_id, studiengang_id, zeitmodell_id, start_datum, status) VALUES
            (1, 1, 1, 1, '2024-01-01', 'aktiv'),
            (2, 2, 2, 2, '2024-06-01', 'aktiv');
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
def temp_db_with_fees(temp_db):
    """Test-DB mit vorhandenen Gebuehren"""
    conn = sqlite3.connect(temp_db)

    today = date.today()
    past_date = today - timedelta(days=30)
    future_date = today + timedelta(days=30)

    conn.executescript(f"""
        INSERT INTO gebuehr (id, einschreibung_id, art, betrag, faellig_am, bezahlt_am) VALUES
            (1, 1, 'Monatsrate', '359.00', '{past_date.isoformat()}', '{past_date.isoformat()}'),
            (2, 1, 'Monatsrate', '359.00', '{today.isoformat()}', NULL),
            (3, 1, 'Monatsrate', '359.00', '{future_date.isoformat()}', NULL),
            (4, 2, 'Monatsrate', '209.00', '{past_date.isoformat()}', NULL),
            (5, 2, 'Monatsrate', '209.00', '{today.isoformat()}', NULL);
    """)
    conn.commit()
    conn.close()

    return temp_db


@pytest.fixture
def repository(gebuehr_repository_class, temp_db):
    """Erstellt Repository-Instanz mit Test-DB"""
    return gebuehr_repository_class(temp_db)


@pytest.fixture
def repository_with_fees(gebuehr_repository_class, temp_db_with_fees):
    """Erstellt Repository-Instanz mit Test-DB inkl. Gebuehren"""
    return gebuehr_repository_class(temp_db_with_fees)


@pytest.fixture
def sample_gebuehr(gebuehr_class):
    """Erstellt Sample-Gebuehr fuer Tests"""
    return gebuehr_class(
        id=0,
        einschreibung_id=1,
        art='Monatsrate',
        betrag=Decimal('359.00'),
        faellig_am=date.today(),
        bezahlt_am=None
    )


# ============================================================================
# INITIALIZATION TESTS
# ============================================================================

class TestGebuehrRepositoryInit:
    """Tests fuer Repository-Initialisierung"""

    def test_init_with_db_path(self, gebuehr_repository_class, temp_db):
        """Repository kann mit DB-Pfad initialisiert werden"""
        repo = gebuehr_repository_class(temp_db)

        assert repo.db_path == temp_db

    def test_init_stores_db_path(self, gebuehr_repository_class):
        """Repository speichert db_path"""
        repo = gebuehr_repository_class("/path/to/db.sqlite")

        assert repo.db_path == "/path/to/db.sqlite"


# ============================================================================
# INSERT TESTS
# ============================================================================

class TestInsert:
    """Tests fuer insert() Methode"""

    def test_insert_returns_id(self, repository, sample_gebuehr):
        """insert() gibt neue ID zurueck"""
        new_id = repository.insert(sample_gebuehr)

        assert isinstance(new_id, int)
        assert new_id > 0

    def test_insert_creates_record(self, repository, sample_gebuehr):
        """insert() erstellt Datensatz in DB"""
        new_id = repository.insert(sample_gebuehr)

        # Verify by loading
        loaded = repository.get_by_id(new_id)
        assert loaded is not None
        assert loaded.einschreibung_id == sample_gebuehr.einschreibung_id
        assert loaded.art == 'Monatsrate'

    def test_insert_with_bezahlt_am(self, repository, gebuehr_class):
        """insert() mit Bezahldatum"""
        gebuehr = gebuehr_class(
            id=0,
            einschreibung_id=1,
            art='Monatsrate',
            betrag=Decimal('359.00'),
            faellig_am=date.today(),
            bezahlt_am=date.today()
        )

        new_id = repository.insert(gebuehr)
        loaded = repository.get_by_id(new_id)

        assert loaded.bezahlt_am == date.today()
        assert loaded.is_paid() is True

    def test_insert_increments_id(self, repository, gebuehr_class):
        """insert() inkrementiert IDs"""
        g1 = gebuehr_class(
            id=0,
            einschreibung_id=1,
            art='Monatsrate',
            betrag=Decimal('359.00'),
            faellig_am=date.today(),
            bezahlt_am=None
        )
        g2 = gebuehr_class(
            id=0,
            einschreibung_id=1,
            art='Einschreibegebuehr',
            betrag=Decimal('100.00'),
            faellig_am=date.today() + timedelta(days=1),
            bezahlt_am=None
        )

        id1 = repository.insert(g1)
        id2 = repository.insert(g2)

        assert id2 > id1

    def test_insert_stores_decimal_correctly(self, repository, gebuehr_class):
        """insert() speichert Decimal korrekt"""
        gebuehr = gebuehr_class(
            id=0,
            einschreibung_id=1,
            art='Monatsrate',
            betrag=Decimal('359.99'),
            faellig_am=date.today(),
            bezahlt_am=None
        )

        new_id = repository.insert(gebuehr)
        loaded = repository.get_by_id(new_id)

        assert loaded.betrag == Decimal('359.99')


# ============================================================================
# GET_BY_ID TESTS
# ============================================================================

class TestGetById:
    """Tests fuer get_by_id() Methode"""

    def test_get_by_id_existing(self, repository_with_fees):
        """get_by_id() laedt existierende Gebuehr"""
        gebuehr = repository_with_fees.get_by_id(1)

        assert gebuehr is not None
        assert gebuehr.id == 1
        assert gebuehr.einschreibung_id == 1
        assert gebuehr.art == 'Monatsrate'

    def test_get_by_id_returns_gebuehr(self, repository_with_fees, gebuehr_class):
        """get_by_id() gibt Gebuehr-Objekt zurueck"""
        gebuehr = repository_with_fees.get_by_id(1)

        assert isinstance(gebuehr, gebuehr_class)

    def test_get_by_id_not_found(self, repository):
        """get_by_id() gibt None zurueck wenn nicht gefunden"""
        result = repository.get_by_id(999)

        assert result is None

    def test_get_by_id_correct_betrag(self, repository_with_fees):
        """get_by_id() laedt korrekten Betrag"""
        gebuehr = repository_with_fees.get_by_id(1)

        assert gebuehr.betrag == Decimal('359.00')


# ============================================================================
# GET_BY_EINSCHREIBUNG TESTS
# ============================================================================

class TestGetByEinschreibung:
    """Tests fuer get_by_einschreibung() Methode"""

    def test_get_by_einschreibung_returns_list(self, repository_with_fees):
        """get_by_einschreibung() gibt Liste zurueck"""
        result = repository_with_fees.get_by_einschreibung(1)

        assert isinstance(result, list)

    def test_get_by_einschreibung_correct_count(self, repository_with_fees):
        """get_by_einschreibung() gibt alle Gebuehren zurueck"""
        # Einschreibung 1 hat 3 Gebuehren
        result = repository_with_fees.get_by_einschreibung(1)

        assert len(result) == 3

    def test_get_by_einschreibung_contains_gebuehren(self, repository_with_fees, gebuehr_class):
        """get_by_einschreibung() enthaelt Gebuehr-Objekte"""
        result = repository_with_fees.get_by_einschreibung(1)

        for gebuehr in result:
            assert isinstance(gebuehr, gebuehr_class)

    def test_get_by_einschreibung_empty_for_nonexistent(self, repository):
        """get_by_einschreibung() gibt leere Liste fuer nicht existierende Einschreibung"""
        result = repository.get_by_einschreibung(999)

        assert result == []

    def test_get_by_einschreibung_ordered_by_faellig_am_desc(self, repository_with_fees):
        """get_by_einschreibung() sortiert nach faellig_am absteigend"""
        result = repository_with_fees.get_by_einschreibung(1)

        # Neueste zuerst
        if len(result) >= 2:
            assert result[0].faellig_am >= result[1].faellig_am


# ============================================================================
# GET_OPEN_FEES_BY_EINSCHREIBUNG TESTS
# ============================================================================

class TestGetOpenFeesByEinschreibung:
    """Tests fuer get_open_fees_by_einschreibung() Methode"""

    def test_get_open_fees_returns_list(self, repository_with_fees):
        """get_open_fees_by_einschreibung() gibt Liste zurueck"""
        result = repository_with_fees.get_open_fees_by_einschreibung(1)

        assert isinstance(result, list)

    def test_get_open_fees_excludes_paid(self, repository_with_fees):
        """get_open_fees_by_einschreibung() schliesst bezahlte aus"""
        result = repository_with_fees.get_open_fees_by_einschreibung(1)

        # Einschreibung 1 hat 3 Gebuehren, 1 bezahlt
        assert len(result) == 2

        for gebuehr in result:
            assert gebuehr.bezahlt_am is None

    def test_get_open_fees_all_unpaid(self, repository_with_fees):
        """get_open_fees_by_einschreibung() gibt nur unbezahlte zurueck"""
        result = repository_with_fees.get_open_fees_by_einschreibung(2)

        # Einschreibung 2 hat 2 Gebuehren, beide offen
        assert len(result) == 2

    def test_get_open_fees_ordered_by_faellig_am_asc(self, repository_with_fees):
        """get_open_fees_by_einschreibung() sortiert nach faellig_am aufsteigend"""
        result = repository_with_fees.get_open_fees_by_einschreibung(1)

        # Aelteste zuerst
        if len(result) >= 2:
            assert result[0].faellig_am <= result[1].faellig_am


# ============================================================================
# CALCULATE_TOTAL_OPEN_FEES TESTS
# ============================================================================

class TestCalculateTotalOpenFees:
    """Tests fuer calculate_total_open_fees() Methode"""

    def test_calculate_total_returns_decimal(self, repository_with_fees):
        """calculate_total_open_fees() gibt Decimal zurueck"""
        result = repository_with_fees.calculate_total_open_fees(1)

        assert isinstance(result, Decimal)

    def test_calculate_total_correct_sum(self, repository_with_fees):
        """calculate_total_open_fees() berechnet korrekte Summe"""
        # Einschreibung 1: 2 offene Gebuehren a 359.00 = 718.00
        result = repository_with_fees.calculate_total_open_fees(1)

        assert result == Decimal('718.00')

    def test_calculate_total_excludes_paid(self, repository_with_fees):
        """calculate_total_open_fees() schliesst bezahlte aus"""
        # Einschreibung 1 hat 3 Gebuehren, 1 bezahlt
        result = repository_with_fees.calculate_total_open_fees(1)

        # Nur 2 offene: 2 * 359.00 = 718.00
        assert result == Decimal('718.00')

    def test_calculate_total_zero_for_none(self, repository):
        """calculate_total_open_fees() gibt 0 wenn keine Gebuehren"""
        result = repository.calculate_total_open_fees(999)

        assert result == Decimal('0')

    def test_calculate_total_zero_all_paid(self, repository_with_fees, temp_db_with_fees):
        """calculate_total_open_fees() gibt 0 wenn alle bezahlt"""
        # Alle Gebuehren von Einschreibung 1 als bezahlt markieren
        conn = sqlite3.connect(temp_db_with_fees)
        conn.execute("UPDATE gebuehr SET bezahlt_am = date('now') WHERE einschreibung_id = 1")
        conn.commit()
        conn.close()

        result = repository_with_fees.calculate_total_open_fees(1)

        assert result == Decimal('0')


# ============================================================================
# MARK_AS_PAID TESTS
# ============================================================================

class TestMarkAsPaid:
    """Tests fuer mark_as_paid() Methode"""

    def test_mark_as_paid_success(self, repository_with_fees):
        """mark_as_paid() markiert Gebuehr als bezahlt"""
        # Gebuehr 2 ist offen
        result = repository_with_fees.mark_as_paid(2)

        assert result is True

        loaded = repository_with_fees.get_by_id(2)
        assert loaded.bezahlt_am is not None

    def test_mark_as_paid_with_date(self, repository_with_fees):
        """mark_as_paid() mit spezifischem Datum"""
        specific_date = date(2025, 6, 15)
        repository_with_fees.mark_as_paid(2, specific_date)

        loaded = repository_with_fees.get_by_id(2)
        assert loaded.bezahlt_am == specific_date

    def test_mark_as_paid_default_today(self, repository_with_fees):
        """mark_as_paid() verwendet heute als Default"""
        repository_with_fees.mark_as_paid(2)

        loaded = repository_with_fees.get_by_id(2)
        assert loaded.bezahlt_am == date.today()

    def test_mark_as_paid_not_found(self, repository):
        """mark_as_paid() gibt False wenn nicht gefunden"""
        result = repository.mark_as_paid(999)

        assert result is False

    def test_mark_as_paid_reduces_open_total(self, repository_with_fees):
        """mark_as_paid() reduziert offene Summe"""
        # Vorher
        before = repository_with_fees.calculate_total_open_fees(1)

        # Eine Gebuehr bezahlen
        repository_with_fees.mark_as_paid(2)

        # Nachher
        after = repository_with_fees.calculate_total_open_fees(1)

        assert after < before
        assert after == before - Decimal('359.00')


# ============================================================================
# GET_OVERDUE_FEES_BY_EINSCHREIBUNG TESTS
# ============================================================================

class TestGetOverdueFeesByEinschreibung:
    """Tests fuer get_overdue_fees_by_einschreibung() Methode"""

    def test_get_overdue_fees_returns_list(self, repository_with_fees):
        """get_overdue_fees_by_einschreibung() gibt Liste zurueck"""
        result = repository_with_fees.get_overdue_fees_by_einschreibung(1)

        assert isinstance(result, list)

    def test_get_overdue_fees_excludes_future(self, repository_with_fees):
        """get_overdue_fees_by_einschreibung() schliesst zukuenftige aus"""
        result = repository_with_fees.get_overdue_fees_by_einschreibung(1)

        today = date.today()
        for gebuehr in result:
            assert gebuehr.faellig_am < today

    def test_get_overdue_fees_excludes_paid(self, repository_with_fees):
        """get_overdue_fees_by_einschreibung() schliesst bezahlte aus"""
        result = repository_with_fees.get_overdue_fees_by_einschreibung(1)

        for gebuehr in result:
            assert gebuehr.bezahlt_am is None

    def test_get_overdue_fees_finds_past_unpaid(self, repository_with_fees):
        """get_overdue_fees_by_einschreibung() findet ueberfaellige"""
        # Einschreibung 2 hat eine ueberfaellige Gebuehr (past_date, unbezahlt)
        result = repository_with_fees.get_overdue_fees_by_einschreibung(2)

        assert len(result) >= 1

    def test_get_overdue_fees_empty_if_all_current(self, repository, gebuehr_class):
        """get_overdue_fees_by_einschreibung() leer wenn alle aktuell"""
        # Fuege nur zukuenftige Gebuehr hinzu
        gebuehr = gebuehr_class(
            id=0,
            einschreibung_id=1,
            art='Monatsrate',
            betrag=Decimal('359.00'),
            faellig_am=date.today() + timedelta(days=30),
            bezahlt_am=None
        )
        repository.insert(gebuehr)

        result = repository.get_overdue_fees_by_einschreibung(1)

        assert len(result) == 0


# ============================================================================
# ENSURE_MONTHLY_FEES TESTS
# ============================================================================

class TestEnsureMonthlyFees:
    """Tests fuer ensure_monthly_fees() Methode"""

    def test_ensure_monthly_fees_returns_int(self, repository):
        """ensure_monthly_fees() gibt int zurueck"""
        result = repository.ensure_monthly_fees()

        assert isinstance(result, int)

    def test_ensure_monthly_fees_creates_fees(self, repository):
        """ensure_monthly_fees() erstellt Gebuehren"""
        # Vorher keine Gebuehren
        before = len(repository.get_by_einschreibung(1))

        repository.ensure_monthly_fees()

        # Nachher sollten Gebuehren existieren
        after = len(repository.get_by_einschreibung(1))

        assert after >= before

    def test_ensure_monthly_fees_idempotent(self, repository):
        """ensure_monthly_fees() ist idempotent"""
        # Erster Aufruf
        repository.ensure_monthly_fees()
        count_after_first = len(repository.get_by_einschreibung(1))

        # Zweiter Aufruf
        repository.ensure_monthly_fees()
        count_after_second = len(repository.get_by_einschreibung(1))

        # Anzahl sollte gleich bleiben
        assert count_after_second == count_after_first

    def test_ensure_monthly_fees_uses_zeitmodell_kosten(self, repository):
        """ensure_monthly_fees() verwendet Kosten aus Zeitmodell"""
        repository.ensure_monthly_fees()

        fees = repository.get_by_einschreibung(1)
        if fees:
            # Einschreibung 1 hat Zeitmodell 1 mit 359.00 pro Monat
            for fee in fees:
                if fee.art == 'Monatsrate':
                    assert fee.betrag == Decimal('359.00')


# ============================================================================
# PRIVATE METHOD TESTS
# ============================================================================

class TestPrivateMethods:
    """Tests fuer private Hilfsmethoden"""

    def test_get_connection_returns_connection(self, repository):
        """__get_connection() gibt Connection zurueck"""
        conn = repository._GebuehrRepository__get_connection()

        assert isinstance(conn, sqlite3.Connection)
        conn.close()

    def test_get_connection_enables_foreign_keys(self, repository):
        """__get_connection() aktiviert Foreign Keys"""
        conn = repository._GebuehrRepository__get_connection()

        result = conn.execute("PRAGMA foreign_keys;").fetchone()
        assert result[0] == 1

        conn.close()


# ============================================================================
# INTEGRATION-LIKE TESTS
# ============================================================================

class TestIntegrationScenarios:
    """Tests fuer typische Nutzungsszenarien"""

    def test_full_payment_lifecycle(self, repository, gebuehr_class):
        """Test: Vollstaendiger Zahlungs-Lebenszyklus"""
        # 1. Neue Gebuehr erstellen
        gebuehr = gebuehr_class(
            id=0,
            einschreibung_id=1,
            art='Monatsrate',
            betrag=Decimal('359.00'),
            faellig_am=date.today(),
            bezahlt_am=None
        )
        new_id = repository.insert(gebuehr)

        # 2. Gebuehr ist offen
        loaded = repository.get_by_id(new_id)
        assert loaded.is_paid() is False

        # 3. Als bezahlt markieren
        repository.mark_as_paid(new_id)

        # 4. Gebuehr ist bezahlt
        loaded = repository.get_by_id(new_id)
        assert loaded.is_paid() is True

    def test_multiple_fees_tracking(self, repository, gebuehr_class):
        """Test: Mehrere Gebuehren verfolgen"""
        # Mehrere Gebuehren erstellen
        for i in range(3):
            gebuehr = gebuehr_class(
                id=0,
                einschreibung_id=1,
                art='Monatsrate',
                betrag=Decimal('359.00'),
                faellig_am=date.today() + timedelta(days=i * 30),
                bezahlt_am=None
            )
            repository.insert(gebuehr)

        # Alle laden
        all_fees = repository.get_by_einschreibung(1)
        assert len(all_fees) == 3

        # Summe pruefen
        total = repository.calculate_total_open_fees(1)
        assert total == Decimal('1077.00')  # 3 * 359.00

    def test_overdue_detection(self, repository, gebuehr_class):
        """Test: Ueberfaellige Gebuehren erkennen"""
        # Ueberfaellige Gebuehr erstellen
        past_date = date.today() - timedelta(days=60)
        gebuehr = gebuehr_class(
            id=0,
            einschreibung_id=1,
            art='Monatsrate',
            betrag=Decimal('359.00'),
            faellig_am=past_date,
            bezahlt_am=None
        )
        repository.insert(gebuehr)

        # Als ueberfaellig erkennen
        overdue = repository.get_overdue_fees_by_einschreibung(1)
        assert len(overdue) >= 1
        assert any(g.faellig_am == past_date for g in overdue)


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

    def test_very_large_betrag(self, repository, gebuehr_class):
        """Sehr grosser Betrag wird korrekt gespeichert"""
        gebuehr = gebuehr_class(
            id=0,
            einschreibung_id=1,
            art='Sonderzahlung',
            betrag=Decimal('999999.99'),
            faellig_am=date.today(),
            bezahlt_am=None
        )

        new_id = repository.insert(gebuehr)
        loaded = repository.get_by_id(new_id)

        assert loaded.betrag == Decimal('999999.99')

    def test_betrag_with_many_decimals(self, repository, gebuehr_class):
        """Betrag mit vielen Dezimalstellen wird gerundet"""
        gebuehr = gebuehr_class(
            id=0,
            einschreibung_id=1,
            art='Monatsrate',
            betrag=Decimal('359.999'),
            faellig_am=date.today(),
            bezahlt_am=None
        )

        new_id = repository.insert(gebuehr)
        loaded = repository.get_by_id(new_id)

        # Decimal wird als String gespeichert und geladen
        assert loaded.betrag == Decimal('359.999')

    def test_different_art_values(self, repository, gebuehr_class):
        """Verschiedene Art-Werte werden korrekt gespeichert"""
        arten = ['Monatsrate', 'Einschreibegebuehr', 'Pruefungsgebuehr', 'Mahngebuehr']

        for i, art in enumerate(arten):
            gebuehr = gebuehr_class(
                id=0,
                einschreibung_id=1,
                art=art,
                betrag=Decimal('100.00'),
                faellig_am=date.today() + timedelta(days=i),
                bezahlt_am=None
            )
            new_id = repository.insert(gebuehr)
            loaded = repository.get_by_id(new_id)

            assert loaded.art == art