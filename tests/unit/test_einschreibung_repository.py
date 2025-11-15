# tests/unit/test_einschreibung_repository.py
"""
Unit Tests fÃƒÂ¼r EinschreibungRepository

Testet CRUD-Operationen und Business-Logik fÃƒÂ¼r Einschreibungen.
"""
import pytest
import sqlite3
from datetime import date
from repositories import EinschreibungRepository
from models import Einschreibung, ValidationError, DatabaseError, NotFoundError


@pytest.fixture
def db_path(tmp_path):
    """Erstellt eine temporÃƒÂ¤re Test-Datenbank"""
    db_file = tmp_path / "test_einschreibung.db"
    return str(db_file)


@pytest.fixture
def setup_db(db_path):
    """Erstellt alle benÃƒÂ¶tigten Tabellen"""
    with sqlite3.connect(db_path) as conn:
        # student Tabelle
        conn.execute("""
                     CREATE TABLE student
                     (
                         id          INTEGER PRIMARY KEY AUTOINCREMENT,
                         vorname     TEXT        NOT NULL,
                         nachname    TEXT        NOT NULL,
                         matrikel_nr TEXT UNIQUE NOT NULL,
                         login_id    INTEGER UNIQUE
                     )
                     """)

        # studiengang Tabelle
        conn.execute("""
                     CREATE TABLE studiengang
                     (
                         id             INTEGER PRIMARY KEY AUTOINCREMENT,
                         name           TEXT    NOT NULL,
                         grad           TEXT    NOT NULL,
                         regel_semester INTEGER NOT NULL
                     )
                     """)

        # zeitmodell Tabelle
        conn.execute("""
                     CREATE TABLE zeitmodell
                     (
                         id           INTEGER PRIMARY KEY AUTOINCREMENT,
                         name         TEXT    NOT NULL UNIQUE,
                         dauer_monate INTEGER NOT NULL,
                         kosten_monat DECIMAL(10,2) NOT NULL
                     )
                     """)

        # einschreibung Tabelle
        conn.execute("""
                     CREATE TABLE einschreibung
                     (
                         id             INTEGER PRIMARY KEY AUTOINCREMENT,
                         student_id     INTEGER NOT NULL,
                         studiengang_id INTEGER NOT NULL,
                         zeitmodell_id  INTEGER NOT NULL,
                         start_datum    TEXT    NOT NULL,
                         exmatrikulations_datum TEXT,
                         status         TEXT    NOT NULL DEFAULT 'aktiv'
                                        CHECK (status IN ('aktiv','pausiert','exmatrikuliert')),
                         FOREIGN KEY (student_id) REFERENCES student (id),
                         FOREIGN KEY (studiengang_id) REFERENCES studiengang (id),
                         FOREIGN KEY (zeitmodell_id) REFERENCES zeitmodell (id)
                     )
                     """)

        # Test-Daten einfÃ¼gen
        conn.execute("""
                     INSERT INTO student (id, matrikel_nr, vorname, nachname, login_id)
                     VALUES (1, 'IU12345', 'Max', 'Mustermann', 1)
                     """)

        conn.execute("""
                     INSERT INTO studiengang (id, name, grad, regel_semester)
                     VALUES (1, 'Informatik', 'B.Sc.', 7)
                     """)

        conn.execute("""
                     INSERT INTO zeitmodell (id, name, dauer_monate, kosten_monat)
                     VALUES (1, 'Vollzeit', 36, 199.00)
                     """)

        conn.commit()
    return db_path


@pytest.fixture
def repo(setup_db):
    """Erstellt EinschreibungRepository Instanz"""
    return EinschreibungRepository(setup_db)


@pytest.fixture
def sample_einschreibung():
    """Erstellt ein Test-Einschreibungs-Objekt"""
    return Einschreibung(
        id=None,
        student_id=1,
        studiengang_id=1,
        zeitmodell_id=1,
        start_datum=date(2024, 3, 1),
        exmatrikulations_datum=None,
        status="aktiv"
    )


# ========== INSERT Tests ==========

def test_insert_valid_einschreibung(repo, sample_einschreibung):
    """Test: GÃƒÂ¼ltige Einschreibung einfÃƒÂ¼gen"""
    einschreibung_id = repo.insert(sample_einschreibung)

    assert isinstance(einschreibung_id, int)
    assert einschreibung_id > 0


def test_insert_returns_new_id(repo, sample_einschreibung):
    """Test: Insert gibt neue ID zurÃƒÂ¼ck"""
    id1 = repo.insert(sample_einschreibung)

    # Zweite Einschreibung
    sample_einschreibung.student_id = 1
    sample_einschreibung.start_datum = date(2025, 1, 1)
    id2 = repo.insert(sample_einschreibung)

    assert id2 > id1


def test_insert_with_all_fields(repo):
    """Test: Insert mit allen Feldern"""
    einschreibung = Einschreibung(
        id=None,
        student_id=1,
        studiengang_id=1,
        zeitmodell_id=1,
        start_datum=date(2024, 3, 1),
        exmatrikulations_datum=date(2026, 3, 1),
        status="exmatrikuliert"
    )

    einschreibung_id = repo.insert(einschreibung)
    loaded = repo.get_by_id(einschreibung_id)

    assert loaded.status == "exmatrikuliert"
    assert loaded.start_datum == date(2024, 3, 1)
    assert loaded.exmatrikulations_datum == date(2026, 3, 1)


def test_insert_invalid_student_fails(repo):
    """Test: Insert mit ungÃƒÂ¼ltiger student_id schlÃƒÂ¤gt fehl"""
    einschreibung = Einschreibung(
        id=None,
        student_id=999,  # Existiert nicht
        studiengang_id=1,
        zeitmodell_id=1,
        start_datum=date(2024, 3, 1),
        exmatrikulations_datum=None,
        status="aktiv"
    )

    with pytest.raises(DatabaseError):
        repo.insert(einschreibung)


# ========== GET_BY_ID Tests ==========

def test_get_by_id_existing(repo, sample_einschreibung):
    """Test: Bestehende Einschreibung laden"""
    einschreibung_id = repo.insert(sample_einschreibung)
    loaded = repo.get_by_id(einschreibung_id)

    assert isinstance(loaded, Einschreibung)
    assert loaded.id == einschreibung_id
    assert loaded.student_id == sample_einschreibung.student_id
    assert loaded.studiengang_id == sample_einschreibung.studiengang_id


def test_get_by_id_not_found(repo):
    """Test: Nicht existierende ID wirft NotFoundError"""
    with pytest.raises(NotFoundError):
        repo.get_by_id(999)


def test_get_by_id_correct_status(repo, sample_einschreibung):
    """Test: Status wird korrekt geladen"""
    sample_einschreibung.status = "pausiert"
    einschreibung_id = repo.insert(sample_einschreibung)
    loaded = repo.get_by_id(einschreibung_id)

    assert loaded.status == "pausiert"


# ========== GET_AKTIVE_BY_STUDENT Tests ==========

def test_get_aktive_by_student_single(repo, sample_einschreibung):
    """Test: Aktive Einschreibung eines Studenten laden"""
    repo.insert(sample_einschreibung)
    aktive = repo.get_aktive_by_student(1)

    assert isinstance(aktive, Einschreibung)
    assert aktive.student_id == 1
    assert aktive.status == "aktiv"


def test_get_aktive_by_student_multiple_returns_latest(repo, sample_einschreibung):
    """Test: Bei mehreren aktiven wird die neueste zurÃƒÂ¼ckgegeben"""
    # Erste Einschreibung
    sample_einschreibung.start_datum = date(2024, 1, 1)
    repo.insert(sample_einschreibung)

    # Zweite Einschreibung (neuer)
    sample_einschreibung.start_datum = date(2024, 6, 1)
    id2 = repo.insert(sample_einschreibung)

    aktive = repo.get_aktive_by_student(1)

    assert aktive.id == id2
    assert aktive.start_datum == date(2024, 6, 1)


def test_get_aktive_by_student_not_found(repo):
    """Test: Keine aktive Einschreibung wirft NotFoundError"""
    with pytest.raises(NotFoundError):
        repo.get_aktive_by_student(999)


def test_get_aktive_ignores_paused_and_exmatrikuliert(repo, sample_einschreibung):
    """Test: Nur aktive Einschreibungen werden gefunden"""
    # Pausierte Einschreibung
    sample_einschreibung.status = "pausiert"
    repo.insert(sample_einschreibung)

    with pytest.raises(NotFoundError):
        repo.get_aktive_by_student(1)


# ========== UPDATE_STATUS Tests ==========

def test_update_status_to_pausiert(repo, sample_einschreibung):
    """Test: Status zu pausiert ÃƒÂ¤ndern"""
    einschreibung_id = repo.insert(sample_einschreibung)
    repo.update_status(einschreibung_id, "pausiert")

    loaded = repo.get_by_id(einschreibung_id)
    assert loaded.status == "pausiert"


def test_update_status_to_exmatrikuliert(repo, sample_einschreibung):
    """Test: Status zu exmatrikuliert ÃƒÂ¤ndern"""
    einschreibung_id = repo.insert(sample_einschreibung)
    repo.update_status(einschreibung_id, "exmatrikuliert")

    loaded = repo.get_by_id(einschreibung_id)
    assert loaded.status == "exmatrikuliert"


def test_update_status_invalid_status(repo, sample_einschreibung):
    """Test: UngÃƒÂ¼ltiger Status wirft ValidationError"""
    einschreibung_id = repo.insert(sample_einschreibung)

    with pytest.raises(ValidationError):
        repo.update_status(einschreibung_id, "ungueltig")


def test_update_status_not_found(repo):
    """Test: Status-Update fÃƒÂ¼r nicht existierende ID wirft NotFoundError"""
    with pytest.raises(NotFoundError):
        repo.update_status(999, "pausiert")


# ========== WECHSEL_ZEITMODELL Tests ==========

def test_wechsel_zeitmodell_valid(repo, setup_db, sample_einschreibung):
    """Test: Zeitmodell wechseln"""
    # Zweites Zeitmodell hinzufÃƒÂ¼gen
    with sqlite3.connect(setup_db) as conn:
        conn.execute("""
                     INSERT INTO zeitmodell (id, name, dauer_monate, kosten_monat)
                     VALUES (2, 14, 4, 119.00)
                     """)
        conn.commit()

    einschreibung_id = repo.insert(sample_einschreibung)
    repo.wechsel_zeitmodell(einschreibung_id, 2)

    loaded = repo.get_by_id(einschreibung_id)
    assert loaded.zeitmodell_id == 2


def test_wechsel_zeitmodell_invalid_id_type(repo, sample_einschreibung):
    """Test: UngÃƒÂ¼ltiger Typ fÃƒÂ¼r zeitmodell_id wirft ValidationError"""
    einschreibung_id = repo.insert(sample_einschreibung)

    with pytest.raises(ValidationError):
        repo.wechsel_zeitmodell(einschreibung_id, "invalid")


def test_wechsel_zeitmodell_negative_id(repo, sample_einschreibung):
    """Test: Negative zeitmodell_id wirft ValidationError"""
    einschreibung_id = repo.insert(sample_einschreibung)

    with pytest.raises(ValidationError):
        repo.wechsel_zeitmodell(einschreibung_id, -1)


def test_wechsel_zeitmodell_not_found(repo):
    """Test: Zeitmodell-Wechsel fÃƒÂ¼r nicht existierende ID wirft NotFoundError"""
    with pytest.raises(NotFoundError):
        repo.wechsel_zeitmodell(999, 2)


# ========== GET_ALL_BY_STUDENT Tests ==========

def test_get_all_by_student_empty(repo):
    """Test: Leere Liste wenn Student keine Einschreibungen hat"""
    result = repo.get_all_by_student(999)

    assert result == []


def test_get_all_by_student_single(repo, sample_einschreibung):
    """Test: Einzel-Einschreibung wird als Liste zurÃƒÂ¼ckgegeben"""
    repo.insert(sample_einschreibung)
    result = repo.get_all_by_student(1)

    assert len(result) == 1
    assert isinstance(result[0], Einschreibung)
    assert result[0].student_id == 1


def test_get_all_by_student_multiple(repo, sample_einschreibung):
    """Test: Mehrere Einschreibungen werden zurÃƒÂ¼ckgegeben"""
    # Erste Einschreibung
    sample_einschreibung.start_datum = date(2024, 1, 1)
    repo.insert(sample_einschreibung)

    # Zweite Einschreibung
    sample_einschreibung.start_datum = date(2024, 6, 1)
    repo.insert(sample_einschreibung)

    result = repo.get_all_by_student(1)

    assert len(result) == 2
    assert all(isinstance(e, Einschreibung) for e in result)


def test_get_all_by_student_sorted_by_date(repo, sample_einschreibung):
    """Test: Einschreibungen werden nach Datum sortiert (neueste zuerst)"""
    # Ãƒâ€žltere Einschreibung
    sample_einschreibung.start_datum = date(2024, 1, 1)
    repo.insert(sample_einschreibung)

    # Neuere Einschreibung
    sample_einschreibung.start_datum = date(2024, 6, 1)
    repo.insert(sample_einschreibung)

    result = repo.get_all_by_student(1)

    assert result[0].start_datum == date(2024, 6, 1)
    assert result[1].start_datum == date(2024, 1, 1)


def test_get_all_by_student_includes_all_statuses(repo, sample_einschreibung):
    """Test: Alle Status-Arten werden zurÃƒÂ¼ckgegeben"""
    # Aktive
    sample_einschreibung.status = "aktiv"
    sample_einschreibung.start_datum = date(2024, 1, 1)
    repo.insert(sample_einschreibung)

    # Pausiert
    sample_einschreibung.status = "pausiert"
    sample_einschreibung.start_datum = date(2024, 3, 1)
    repo.insert(sample_einschreibung)

    # Exmatrikuliert
    sample_einschreibung.status = "exmatrikuliert"
    sample_einschreibung.start_datum = date(2024, 6, 1)
    repo.insert(sample_einschreibung)

    result = repo.get_all_by_student(1)

    assert len(result) == 3
    statuses = [e.status for e in result]
    assert "aktiv" in statuses
    assert "pausiert" in statuses
    assert "exmatrikuliert" in statuses


# ========== Integration Tests ==========

def test_full_lifecycle(repo, sample_einschreibung):
    """Test: VollstÃƒÂ¤ndiger Lebenszyklus einer Einschreibung"""
    # 1. Insert
    einschreibung_id = repo.insert(sample_einschreibung)
    assert einschreibung_id > 0

    # 2. Get by ID
    loaded = repo.get_by_id(einschreibung_id)
    assert loaded.status == "aktiv"

    # 3. Get aktive
    aktive = repo.get_aktive_by_student(1)
    assert aktive.id == einschreibung_id

    # 4. Status ÃƒÂ¤ndern zu pausiert
    repo.update_status(einschreibung_id, "pausiert")
    loaded = repo.get_by_id(einschreibung_id)
    assert loaded.status == "pausiert"

    # 5. Keine aktive mehr vorhanden
    with pytest.raises(NotFoundError):
        repo.get_aktive_by_student(1)

    # 6. Get all zeigt pausierte
    all_einschreibungen = repo.get_all_by_student(1)
    assert len(all_einschreibungen) == 1
    assert all_einschreibungen[0].status == "pausiert"


def test_concurrent_einschreibungen(repo, sample_einschreibung):
    """Test: Mehrere Einschreibungen fÃƒÂ¼r denselben Studenten"""
    # Erste Einschreibung (aktiv)
    sample_einschreibung.start_datum = date(2024, 1, 1)
    sample_einschreibung.status = "aktiv"
    id1 = repo.insert(sample_einschreibung)

    # Zweite Einschreibung (pausiert)
    sample_einschreibung.start_datum = date(2024, 6, 1)
    sample_einschreibung.status = "pausiert"
    id2 = repo.insert(sample_einschreibung)

    # Beide vorhanden
    all_einschreibungen = repo.get_all_by_student(1)
    assert len(all_einschreibungen) == 2

    # Nur die aktive wird gefunden
    aktive = repo.get_aktive_by_student(1)
    assert aktive.id == id1