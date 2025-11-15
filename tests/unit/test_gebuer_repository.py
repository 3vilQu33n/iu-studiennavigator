# tests/unit/test_gebuehr_repository.py
"""
Unit Tests fÃ¼r GebuehrRepository

Testet CRUD-Operationen, Zahlungslogik und Berechnungen fÃ¼r GebÃ¼hren.
"""
import pytest
import sqlite3
from datetime import date, timedelta
from decimal import Decimal
from repositories.gebuehr_repository import GebuehrRepository
from models.gebuehr import Gebuehr


@pytest.fixture
def db_path(tmp_path):
    """Erstellt eine temporÃ¤re Test-Datenbank"""
    db_file = tmp_path / "test_gebuehr.db"
    return str(db_file)


@pytest.fixture
def setup_db(db_path):
    """Erstellt alle benÃ¶tigten Tabellen"""
    with sqlite3.connect(db_path) as conn:
        # einschreibung Tabelle
        conn.execute("""
                     CREATE TABLE einschreibung
                     (
                         id             INTEGER PRIMARY KEY AUTOINCREMENT,
                         student_id     INTEGER NOT NULL,
                         studiengang_id INTEGER NOT NULL,
                         zeitmodell_id  INTEGER NOT NULL,
                         start_datum    TEXT    NOT NULL,
                         status         TEXT    NOT NULL DEFAULT 'aktiv'
                     )
                     """)

        # gebuehr Tabelle
        conn.execute("""
                     CREATE TABLE gebuehr
                     (
                         id               INTEGER PRIMARY KEY AUTOINCREMENT,
                         einschreibung_id INTEGER NOT NULL,
                         art              TEXT    NOT NULL,
                         betrag           REAL    NOT NULL,
                         faellig_am       TEXT    NOT NULL,
                         bezahlt_am       TEXT,
                         FOREIGN KEY (einschreibung_id) REFERENCES einschreibung (id),
                         UNIQUE (einschreibung_id, art, faellig_am)
                     )
                     """)

        # zeitmodell Tabelle (fÃ¼r ensure_monthly_fees)
        conn.execute("""
                     CREATE TABLE zeitmodell
                     (
                         id           INTEGER PRIMARY KEY AUTOINCREMENT,
                         name         TEXT NOT NULL,
                         kosten_monat REAL NOT NULL
                     )
                     """)

        # Test-Daten einfÃ¼gen
        conn.execute("""
                     INSERT INTO zeitmodell (id, name, kosten_monat)
                     VALUES (1, 'Vollzeit', 199.00)
                     """)

        conn.execute("""
                     INSERT INTO einschreibung (id, student_id, studiengang_id, zeitmodell_id, start_datum, status)
                     VALUES (1, 1, 1, 1, '2024-03-01', 'aktiv')
                     """)

        conn.commit()
    return db_path


@pytest.fixture
def repo(setup_db):
    """Erstellt GebuehrRepository Instanz"""
    return GebuehrRepository(setup_db)


@pytest.fixture
def sample_gebuehr():
    """Erstellt ein Test-GebÃ¼hren-Objekt"""
    return Gebuehr(
        id=None,
        einschreibung_id=1,
        art="StudiengebÃ¼hr",
        betrag=Decimal("199.00"),
        faellig_am=date(2024, 6, 1),
        bezahlt_am=None
    )


# ========== INSERT Tests ==========

def test_insert_valid_gebuehr(repo, sample_gebuehr):
    """Test: GÃ¼ltige GebÃ¼hr einfÃ¼gen"""
    gebuehr_id = repo.insert(sample_gebuehr)

    assert isinstance(gebuehr_id, int)
    assert gebuehr_id > 0


def test_insert_returns_new_id(repo, sample_gebuehr):
    """Test: Insert gibt neue ID zurÃ¼ck"""
    id1 = repo.insert(sample_gebuehr)

    # Zweite GebÃ¼hr
    sample_gebuehr.faellig_am = date(2024, 7, 1)
    id2 = repo.insert(sample_gebuehr)

    assert id2 > id1


def test_insert_with_payment_date(repo):
    """Test: Insert mit Zahlungsdatum"""
    gebuehr = Gebuehr(
        id=None,
        einschreibung_id=1,
        art="StudiengebÃ¼hr",
        betrag=Decimal("199.00"),
        faellig_am=date(2024, 6, 1),
        bezahlt_am=date(2024, 5, 25)
    )

    gebuehr_id = repo.insert(gebuehr)
    loaded = repo.get_by_id(gebuehr_id)

    assert loaded.bezahlt_am == date(2024, 5, 25)


def test_insert_decimal_precision(repo):
    """Test: Decimal-BetrÃ¤ge bleiben prÃ¤zise"""
    gebuehr = Gebuehr(
        id=None,
        einschreibung_id=1,
        art="StudiengebÃ¼hr",
        betrag=Decimal("199.99"),
        faellig_am=date(2024, 6, 1),
        bezahlt_am=None
    )

    gebuehr_id = repo.insert(gebuehr)
    loaded = repo.get_by_id(gebuehr_id)

    assert loaded.betrag == Decimal("199.99")


# ========== GET_BY_ID Tests ==========

def test_get_by_id_existing(repo, sample_gebuehr):
    """Test: Bestehende GebÃ¼hr laden"""
    gebuehr_id = repo.insert(sample_gebuehr)
    loaded = repo.get_by_id(gebuehr_id)

    assert isinstance(loaded, Gebuehr)
    assert loaded.id == gebuehr_id
    assert loaded.einschreibung_id == sample_gebuehr.einschreibung_id
    assert loaded.art == sample_gebuehr.art
    assert loaded.betrag == sample_gebuehr.betrag


def test_get_by_id_not_found(repo):
    """Test: Nicht existierende ID gibt None zurÃ¼ck"""
    result = repo.get_by_id(999)

    assert result is None


def test_get_by_id_correct_dates(repo, sample_gebuehr):
    """Test: DatÃ¼mer werden korrekt geladen"""
    gebuehr_id = repo.insert(sample_gebuehr)
    loaded = repo.get_by_id(gebuehr_id)

    assert loaded.faellig_am == date(2024, 6, 1)
    assert loaded.bezahlt_am is None


# ========== GET_BY_EINSCHREIBUNG Tests ==========

def test_get_by_einschreibung_empty(repo):
    """Test: Leere Liste wenn keine GebÃ¼hren vorhanden"""
    result = repo.get_by_einschreibung(999)

    assert result == []


def test_get_by_einschreibung_single(repo, sample_gebuehr):
    """Test: Einzelne GebÃ¼hr wird als Liste zurÃ¼ckgegeben"""
    repo.insert(sample_gebuehr)
    result = repo.get_by_einschreibung(1)

    assert len(result) == 1
    assert isinstance(result[0], Gebuehr)
    assert result[0].einschreibung_id == 1


def test_get_by_einschreibung_multiple(repo, sample_gebuehr):
    """Test: Mehrere GebÃ¼hren werden zurÃ¼ckgegeben"""
    # Erste GebÃ¼hr
    sample_gebuehr.faellig_am = date(2024, 6, 1)
    repo.insert(sample_gebuehr)

    # Zweite GebÃ¼hr
    sample_gebuehr.faellig_am = date(2024, 7, 1)
    repo.insert(sample_gebuehr)

    result = repo.get_by_einschreibung(1)

    assert len(result) == 2
    assert all(isinstance(g, Gebuehr) for g in result)


def test_get_by_einschreibung_sorted_by_date(repo, sample_gebuehr):
    """Test: GebÃ¼hren werden nach Datum sortiert (neueste zuerst)"""
    # Ã„ltere GebÃ¼hr
    sample_gebuehr.faellig_am = date(2024, 6, 1)
    repo.insert(sample_gebuehr)

    # Neuere GebÃ¼hr
    sample_gebuehr.faellig_am = date(2024, 8, 1)
    repo.insert(sample_gebuehr)

    result = repo.get_by_einschreibung(1)

    assert result[0].faellig_am == date(2024, 8, 1)
    assert result[1].faellig_am == date(2024, 6, 1)


# ========== GET_OPEN_FEES Tests ==========

def test_get_open_fees_empty(repo):
    """Test: Leere Liste wenn keine offenen GebÃ¼hren"""
    result = repo.get_open_fees_by_einschreibung(1)

    assert result == []


def test_get_open_fees_only_unpaid(repo, sample_gebuehr):
    """Test: Nur unbezahlte GebÃ¼hren werden zurÃ¼ckgegeben"""
    # Offene GebÃ¼hr
    sample_gebuehr.faellig_am = date(2024, 6, 1)
    sample_gebuehr.bezahlt_am = None
    repo.insert(sample_gebuehr)

    # Bezahlte GebÃ¼hr
    sample_gebuehr.faellig_am = date(2024, 5, 1)
    sample_gebuehr.bezahlt_am = date(2024, 5, 15)
    repo.insert(sample_gebuehr)

    result = repo.get_open_fees_by_einschreibung(1)

    assert len(result) == 1
    assert result[0].bezahlt_am is None


def test_get_open_fees_sorted_ascending(repo, sample_gebuehr):
    """Test: Offene GebÃ¼hren sortiert nach FÃ¤lligkeit (Ã¤lteste zuerst)"""
    # Neuere offene GebÃ¼hr
    sample_gebuehr.faellig_am = date(2024, 8, 1)
    repo.insert(sample_gebuehr)

    # Ã„ltere offene GebÃ¼hr
    sample_gebuehr.faellig_am = date(2024, 6, 1)
    repo.insert(sample_gebuehr)

    result = repo.get_open_fees_by_einschreibung(1)

    assert result[0].faellig_am == date(2024, 6, 1)
    assert result[1].faellig_am == date(2024, 8, 1)


# ========== CALCULATE_TOTAL_OPEN_FEES Tests ==========

def test_calculate_total_zero(repo):
    """Test: Summe ist 0 wenn keine offenen GebÃ¼hren"""
    total = repo.calculate_total_open_fees(1)

    assert total == Decimal("0")


def test_calculate_total_single(repo, sample_gebuehr):
    """Test: Summe einer offenen GebÃ¼hr"""
    repo.insert(sample_gebuehr)
    total = repo.calculate_total_open_fees(1)

    assert total == Decimal("199.00")


def test_calculate_total_multiple(repo, sample_gebuehr):
    """Test: Summe mehrerer offener GebÃ¼hren"""
    # Erste GebÃ¼hr
    sample_gebuehr.betrag = Decimal("199.00")
    sample_gebuehr.faellig_am = date(2024, 6, 1)
    repo.insert(sample_gebuehr)

    # Zweite GebÃ¼hr
    sample_gebuehr.betrag = Decimal("75.00")
    sample_gebuehr.faellig_am = date(2024, 7, 1)
    repo.insert(sample_gebuehr)

    total = repo.calculate_total_open_fees(1)

    assert total == Decimal("274.00")


def test_calculate_total_ignores_paid(repo, sample_gebuehr):
    """Test: Bezahlte GebÃ¼hren werden nicht summiert"""
    # Offene GebÃ¼hr
    sample_gebuehr.betrag = Decimal("199.00")
    sample_gebuehr.faellig_am = date(2024, 6, 1)
    sample_gebuehr.bezahlt_am = None
    repo.insert(sample_gebuehr)

    # Bezahlte GebÃ¼hr
    sample_gebuehr.betrag = Decimal("199.00")
    sample_gebuehr.faellig_am = date(2024, 5, 1)
    sample_gebuehr.bezahlt_am = date(2024, 5, 15)
    repo.insert(sample_gebuehr)

    total = repo.calculate_total_open_fees(1)

    assert total == Decimal("199.00")


# ========== MARK_AS_PAID Tests ==========

def test_mark_as_paid_success(repo, sample_gebuehr):
    """Test: GebÃ¼hr als bezahlt markieren"""
    gebuehr_id = repo.insert(sample_gebuehr)
    result = repo.mark_as_paid(gebuehr_id, date(2024, 5, 25))

    assert result is True

    loaded = repo.get_by_id(gebuehr_id)
    assert loaded.bezahlt_am == date(2024, 5, 25)


def test_mark_as_paid_not_found(repo):
    """Test: Nicht existierende ID gibt False zurÃ¼ck"""
    result = repo.mark_as_paid(999, date(2024, 5, 25))

    assert result is False


def test_mark_as_paid_default_today(repo, sample_gebuehr):
    """Test: Standard-Zahlungsdatum ist heute"""
    gebuehr_id = repo.insert(sample_gebuehr)
    repo.mark_as_paid(gebuehr_id)

    loaded = repo.get_by_id(gebuehr_id)
    assert loaded.bezahlt_am == date.today()


def test_mark_as_paid_removes_from_open_fees(repo, sample_gebuehr):
    """Test: Bezahlte GebÃ¼hr taucht nicht mehr bei offenen auf"""
    gebuehr_id = repo.insert(sample_gebuehr)

    # Vor Zahlung
    open_before = repo.get_open_fees_by_einschreibung(1)
    assert len(open_before) == 1

    # Zahlung
    repo.mark_as_paid(gebuehr_id, date(2024, 5, 25))

    # Nach Zahlung
    open_after = repo.get_open_fees_by_einschreibung(1)
    assert len(open_after) == 0


# ========== GET_OVERDUE_FEES Tests ==========

def test_get_overdue_fees_empty(repo):
    """Test: Leere Liste wenn keine Ã¼berfÃ¤lligen GebÃ¼hren"""
    result = repo.get_overdue_fees_by_einschreibung(1)

    assert result == []


def test_get_overdue_fees_only_past(repo, sample_gebuehr):
    """Test: Nur vergangene offene GebÃ¼hren werden zurÃ¼ckgegeben"""
    # ÃœberfÃ¤llige GebÃ¼hr (gestern)
    sample_gebuehr.faellig_am = date.today() - timedelta(days=1)
    sample_gebuehr.bezahlt_am = None
    repo.insert(sample_gebuehr)

    # ZukÃ¼nftige GebÃ¼hr
    sample_gebuehr.faellig_am = date.today() + timedelta(days=30)
    sample_gebuehr.bezahlt_am = None
    repo.insert(sample_gebuehr)

    result = repo.get_overdue_fees_by_einschreibung(1)

    assert len(result) == 1
    assert result[0].faellig_am < date.today()


def test_get_overdue_ignores_paid(repo, sample_gebuehr):
    """Test: Bezahlte GebÃ¼hren werden nicht als Ã¼berfÃ¤llig angezeigt"""
    # ÃœberfÃ¤llige aber bezahlte GebÃ¼hr
    sample_gebuehr.faellig_am = date.today() - timedelta(days=30)
    sample_gebuehr.bezahlt_am = date.today() - timedelta(days=25)
    repo.insert(sample_gebuehr)

    result = repo.get_overdue_fees_by_einschreibung(1)

    assert len(result) == 0


def test_get_overdue_sorted_ascending(repo, sample_gebuehr):
    """Test: ÃœberfÃ¤llige GebÃ¼hren sortiert nach FÃ¤lligkeit (Ã¤lteste zuerst)"""
    # Neuere Ã¼berfÃ¤llige GebÃ¼hr
    sample_gebuehr.faellig_am = date.today() - timedelta(days=10)
    repo.insert(sample_gebuehr)

    # Ã„ltere Ã¼berfÃ¤llige GebÃ¼hr
    sample_gebuehr.faellig_am = date.today() - timedelta(days=60)
    repo.insert(sample_gebuehr)

    result = repo.get_overdue_fees_by_einschreibung(1)

    assert result[0].faellig_am < result[1].faellig_am


# ========== Integration Tests ==========

def test_full_payment_lifecycle(repo, sample_gebuehr):
    """Test: VollstÃ¤ndiger Zahlungszyklus"""
    # 1. GebÃ¼hr einfÃ¼gen
    gebuehr_id = repo.insert(sample_gebuehr)

    # 2. In offenen GebÃ¼hren vorhanden
    open_fees = repo.get_open_fees_by_einschreibung(1)
    assert len(open_fees) == 1

    # 3. Total berechnen
    total = repo.calculate_total_open_fees(1)
    assert total == Decimal("199.00")

    # 4. Als bezahlt markieren
    repo.mark_as_paid(gebuehr_id, date(2024, 5, 25))

    # 5. Nicht mehr in offenen GebÃ¼hren
    open_after = repo.get_open_fees_by_einschreibung(1)
    assert len(open_after) == 0

    # 6. Total ist jetzt 0
    total_after = repo.calculate_total_open_fees(1)
    assert total_after == Decimal("0")


def test_mixed_fees_scenario(repo, sample_gebuehr):
    """Test: Gemischtes Szenario mit verschiedenen Gebühren-Status"""
    # 1. Offene Gebühr (noch nicht fällig)
    sample_gebuehr.art = "Offen"
    sample_gebuehr.faellig_am = date.today() + timedelta(days=30)  # ✅ In der Zukunft
    sample_gebuehr.bezahlt_am = None
    repo.insert(sample_gebuehr)

    # 2. Bezahlte Gebühr
    sample_gebuehr.art = "Bezahlt"
    sample_gebuehr.faellig_am = date(2024, 5, 1)
    sample_gebuehr.bezahlt_am = date(2024, 5, 15)
    repo.insert(sample_gebuehr)

    # 3. Überfällige Gebühr
    sample_gebuehr.art = "Überfällig"
    sample_gebuehr.faellig_am = date.today() - timedelta(days=30)  # ✅ In der Vergangenheit
    sample_gebuehr.bezahlt_am = None
    repo.insert(sample_gebuehr)

    # Validierungen
    all_fees = repo.get_by_einschreibung(1)
    assert len(all_fees) == 3

    open_fees = repo.get_open_fees_by_einschreibung(1)
    assert len(open_fees) == 2  # Offen + Überfällig

    overdue_fees = repo.get_overdue_fees_by_einschreibung(1)
    assert len(overdue_fees) == 1  # ✅ Nur die überfällige

    total = repo.calculate_total_open_fees(1)
    assert total == Decimal("398.00")  # 2 x 199


def test_multiple_einschreibungen_isolated(repo, setup_db, sample_gebuehr):
    """Test: GebÃ¼hren sind pro Einschreibung isoliert"""
    # Zweite Einschreibung hinzufÃ¼gen
    with sqlite3.connect(setup_db) as conn:
        conn.execute("""
                     INSERT INTO einschreibung (id, student_id, studiengang_id, zeitmodell_id, start_datum, status)
                     VALUES (2, 2, 1, 1, '2024-06-01', 'aktiv')
                     """)
        conn.commit()

    # GebÃ¼hren fÃ¼r Einschreibung 1
    sample_gebuehr.einschreibung_id = 1
    repo.insert(sample_gebuehr)

    # GebÃ¼hren fÃ¼r Einschreibung 2
    sample_gebuehr.einschreibung_id = 2
    repo.insert(sample_gebuehr)

    # Validierung: Getrennte GebÃ¼hren
    fees1 = repo.get_by_einschreibung(1)
    fees2 = repo.get_by_einschreibung(2)

    assert len(fees1) == 1
    assert len(fees2) == 1
    assert fees1[0].einschreibung_id == 1
    assert fees2[0].einschreibung_id == 2