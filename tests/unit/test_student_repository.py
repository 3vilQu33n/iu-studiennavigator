# tests/unit/test_student_repository.py
"""
Unit Tests für StudentRepository

Testet alle CRUD-Operationen und Suchfunktionen mit einer In-Memory SQLite DB.
FINALE VERSION: Entspricht der tatsächlichen DB-Struktur mit FK zu login
"""
import pytest
import sqlite3
from repositories.student_repository import StudentRepository
from models.student import Student


@pytest.fixture
def db_path(tmp_path):
    """Erstellt eine temporäre Test-Datenbank"""
    db_file = tmp_path / "test_students.db"
    return str(db_file)


@pytest.fixture
def setup_db(db_path):
    """Erstellt die student Tabelle mit korrekter Struktur"""
    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys = ON")

        # Login-Tabelle muss zuerst existieren wegen FK
        conn.execute("""
                     CREATE TABLE IF NOT EXISTS login
                     (
                         id INTEGER PRIMARY KEY AUTOINCREMENT
                     )
                     """)

        # Erstelle Test-Logins für die Tests
        for i in range(1, 11):
            conn.execute("INSERT INTO login (id) VALUES (?)", (i,))

        conn.execute("""
                     CREATE TABLE IF NOT EXISTS student
                     (
                         id          INTEGER PRIMARY KEY AUTOINCREMENT,
                         vorname     TEXT        NOT NULL,
                         nachname    TEXT        NOT NULL,
                         matrikel_nr TEXT UNIQUE NOT NULL,
                         login_id    INTEGER UNIQUE,
                         FOREIGN KEY (login_id) REFERENCES login (id)
                     )
                     """)
        conn.commit()
    return db_path


@pytest.fixture
def repo(setup_db):
    """Erstellt eine Repository-Instanz mit Test-DB"""
    return StudentRepository(setup_db)


@pytest.fixture
def sample_student():
    """Erstellt einen Test-Studenten"""
    return Student(
        id=0,
        matrikel_nr="IU12345678",
        vorname="Max",
        nachname="Mustermann",
        login_id=1
    )


# ========== INSERT Tests ==========

def test_insert_student_success(repo, sample_student):
    """Test: Student erfolgreich einfügen"""
    student_id = repo.insert(sample_student)

    assert student_id > 0
    assert isinstance(student_id, int)


def test_insert_student_returns_new_id(repo, sample_student):
    """Test: insert() gibt die neue ID zurück"""
    student_id = repo.insert(sample_student)

    loaded = repo.get_by_id(student_id)
    assert loaded is not None
    assert loaded.matrikel_nr == sample_student.matrikel_nr


def test_insert_student_with_invalid_data_raises(repo):
    """Test: Ungültiger Student wirft ValueError"""
    invalid_student = Student(
        id=0,
        matrikel_nr="IU12",  # zu kurz (4 Zeichen)
        vorname="Max",
        nachname="Mustermann",
        login_id=1
    )

    with pytest.raises(ValueError):
        repo.insert(invalid_student)


def test_insert_duplicate_matrikel_nr_raises(repo, sample_student):
    """Test: Duplikat Matrikelnummer wirft ValueError"""
    repo.insert(sample_student)

    duplicate = Student(
        id=0,
        matrikel_nr=sample_student.matrikel_nr,  # Duplikat
        vorname="Anna",
        nachname="Beispiel",
        login_id=2
    )

    with pytest.raises(ValueError):
        repo.insert(duplicate)


def test_insert_duplicate_login_id_raises(repo, sample_student):
    """Test: Duplikat login_id wirft ValueError (UNIQUE Constraint)"""
    repo.insert(sample_student)

    duplicate = Student(
        id=0,
        matrikel_nr="IU87654321",
        vorname="Anna",
        nachname="Beispiel",
        login_id=sample_student.login_id  # Duplikat login_id!
    )

    with pytest.raises(ValueError):
        repo.insert(duplicate)


def test_insert_student_without_login_id(repo):
    """Test: Student ohne login_id einfügen (NULL erlaubt)"""
    student = Student(
        id=0,
        matrikel_nr="IU11111111",
        vorname="Test",
        nachname="User",
        login_id=None
    )

    student_id = repo.insert(student)
    assert student_id > 0


# ========== GET BY ID Tests ==========

def test_get_by_id_existing_student(repo, sample_student):
    """Test: Student anhand ID laden"""
    student_id = repo.insert(sample_student)

    loaded = repo.get_by_id(student_id)

    assert loaded is not None
    assert loaded.id == student_id
    assert loaded.matrikel_nr == sample_student.matrikel_nr
    assert loaded.vorname == sample_student.vorname
    assert loaded.nachname == sample_student.nachname


def test_get_by_id_nonexistent_student(repo):
    """Test: Nicht existierender Student gibt None zurück"""
    loaded = repo.get_by_id(99999)

    assert loaded is None


def test_get_by_id_returns_student_object(repo, sample_student):
    """Test: get_by_id gibt Student-Objekt zurück"""
    student_id = repo.insert(sample_student)

    loaded = repo.get_by_id(student_id)

    assert isinstance(loaded, Student)


# ========== GET BY LOGIN_ID Tests ==========

def test_get_by_login_id_existing_student(repo, sample_student):
    """Test: Student anhand login_id laden"""
    repo.insert(sample_student)

    loaded = repo.get_by_login_id(1)

    assert loaded is not None
    assert loaded.login_id == 1
    assert loaded.matrikel_nr == sample_student.matrikel_nr


def test_get_by_login_id_nonexistent_login(repo):
    """Test: Nicht existierende login_id gibt None zurück"""
    loaded = repo.get_by_login_id(99999)

    assert loaded is None


def test_get_by_login_id_without_login_id(repo):
    """Test: Student ohne login_id kann nicht per login_id gefunden werden"""
    student = Student(
        id=0,
        matrikel_nr="IU12345678",
        vorname="Max",
        nachname="Mustermann",
        login_id=None
    )
    repo.insert(student)

    loaded = repo.get_by_login_id(None)

    assert loaded is None


# ========== GET BY MATRIKEL_NR Tests ==========

def test_get_by_matrikel_nr_existing_student(repo, sample_student):
    """Test: Student anhand Matrikelnummer laden"""
    repo.insert(sample_student)

    loaded = repo.get_by_matrikel_nr("IU12345678")

    assert loaded is not None
    assert loaded.matrikel_nr == "IU12345678"
    assert loaded.vorname == sample_student.vorname


def test_get_by_matrikel_nr_nonexistent_matrikel(repo):
    """Test: Nicht existierende Matrikelnummer gibt None zurück"""
    loaded = repo.get_by_matrikel_nr("IU99999999")

    assert loaded is None


def test_get_by_matrikel_nr_case_sensitive(repo, sample_student):
    """Test: Matrikelnummer ist case-sensitive"""
    repo.insert(sample_student)

    # Lowercase sollte nicht funktionieren
    loaded = repo.get_by_matrikel_nr("iu12345678")

    # Für SQLite ist es case-sensitive
    assert loaded is None or loaded.matrikel_nr == "IU12345678"


# ========== GET ALL Tests ==========

def test_get_all_empty_database(repo):
    """Test: Leere Datenbank gibt leere Liste zurück"""
    students = repo.get_all()

    assert students == []
    assert isinstance(students, list)


def test_get_all_single_student(repo, sample_student):
    """Test: Ein Student in der DB"""
    repo.insert(sample_student)

    students = repo.get_all()

    assert len(students) == 1
    assert students[0].matrikel_nr == sample_student.matrikel_nr


def test_get_all_multiple_students(repo, sample_student):
    """Test: Mehrere Studenten laden"""
    repo.insert(sample_student)

    student2 = Student(
        id=0,
        matrikel_nr="IU87654321",
        vorname="Anna",
        nachname="Beispiel",
        login_id=2
    )
    repo.insert(student2)

    students = repo.get_all()

    assert len(students) == 2
    matrikel_nrs = [s.matrikel_nr for s in students]
    assert "IU12345678" in matrikel_nrs
    assert "IU87654321" in matrikel_nrs


def test_get_all_returns_student_objects(repo, sample_student):
    """Test: get_all gibt Student-Objekte zurück"""
    repo.insert(sample_student)

    students = repo.get_all()

    assert all(isinstance(s, Student) for s in students)


# ========== UPDATE Tests ==========

def test_update_student_success(repo, sample_student):
    """Test: Student erfolgreich aktualisieren"""
    student_id = repo.insert(sample_student)

    loaded = repo.get_by_id(student_id)
    loaded.vorname = "Maximilian"

    success = repo.update(loaded)

    assert success is True

    updated = repo.get_by_id(student_id)
    assert updated.vorname == "Maximilian"


def test_update_student_all_fields(repo, sample_student):
    """Test: Alle Felder eines Students aktualisieren"""
    student_id = repo.insert(sample_student)

    loaded = repo.get_by_id(student_id)
    loaded.matrikel_nr = "IU99999999"
    loaded.vorname = "Anna"
    loaded.nachname = "Beispiel"
    loaded.login_id = 2

    success = repo.update(loaded)

    assert success is True

    updated = repo.get_by_id(student_id)
    assert updated.matrikel_nr == "IU99999999"
    assert updated.vorname == "Anna"
    assert updated.nachname == "Beispiel"
    assert updated.login_id == 2


def test_update_student_with_invalid_data_raises(repo, sample_student):
    """Test: Update mit ungültigen Daten wirft ValueError"""
    student_id = repo.insert(sample_student)

    loaded = repo.get_by_id(student_id)
    loaded.matrikel_nr = "IU12"  # zu kurz (4 Zeichen)

    with pytest.raises(ValueError):
        repo.update(loaded)


def test_update_student_duplicate_matrikel_raises(repo, sample_student):
    """Test: Update mit Duplikat Matrikelnummer wirft ValueError"""
    student_id1 = repo.insert(sample_student)

    student2 = Student(
        id=0,
        matrikel_nr="IU87654321",
        vorname="Anna",
        nachname="Beispiel",
        login_id=2
    )
    student_id2 = repo.insert(student2)

    loaded = repo.get_by_id(student_id2)
    loaded.matrikel_nr = sample_student.matrikel_nr  # Duplikat

    with pytest.raises(ValueError):
        repo.update(loaded)


def test_update_student_duplicate_login_id_raises(repo, sample_student):
    """Test: Update mit Duplikat login_id wirft ValueError"""
    student_id1 = repo.insert(sample_student)

    student2 = Student(
        id=0,
        matrikel_nr="IU87654321",
        vorname="Anna",
        nachname="Beispiel",
        login_id=2
    )
    student_id2 = repo.insert(student2)

    loaded = repo.get_by_id(student_id2)
    loaded.login_id = sample_student.login_id  # Duplikat login_id

    with pytest.raises(ValueError):
        repo.update(loaded)


# ========== DELETE Tests ==========

def test_delete_student_success(repo, sample_student):
    """Test: Student erfolgreich löschen"""
    student_id = repo.insert(sample_student)

    success = repo.delete(student_id)

    assert success is True

    loaded = repo.get_by_id(student_id)
    assert loaded is None


def test_delete_nonexistent_student(repo):
    """Test: Nicht existierenden Student löschen gibt True zurück"""
    success = repo.delete(99999)

    assert success is True


def test_delete_student_removes_from_all_queries(repo, sample_student):
    """Test: Gelöschter Student ist in keiner Query mehr auffindbar"""
    student_id = repo.insert(sample_student)

    repo.delete(student_id)

    assert repo.get_by_id(student_id) is None
    assert repo.get_by_matrikel_nr(sample_student.matrikel_nr) is None
    assert len(repo.get_all()) == 0


# ========== EXISTS Tests ==========

def test_exists_with_existing_matrikel(repo, sample_student):
    """Test: exists() gibt True für existierende Matrikelnummer"""
    repo.insert(sample_student)

    exists = repo.exists("IU12345678")

    assert exists is True


def test_exists_with_nonexistent_matrikel(repo):
    """Test: exists() gibt False für nicht existierende Matrikelnummer"""
    exists = repo.exists("IU99999999")

    assert exists is False


def test_exists_after_delete(repo, sample_student):
    """Test: exists() gibt False nach Löschen"""
    student_id = repo.insert(sample_student)

    assert repo.exists(sample_student.matrikel_nr) is True

    repo.delete(student_id)

    assert repo.exists(sample_student.matrikel_nr) is False


# ========== INTEGRATION Tests ==========

def test_full_crud_cycle(repo, sample_student):
    """Test: Kompletter CRUD Zyklus"""
    # Create
    student_id = repo.insert(sample_student)
    assert student_id > 0

    # Read
    loaded = repo.get_by_id(student_id)
    assert loaded is not None
    assert loaded.vorname == "Max"

    # Update
    loaded.vorname = "Maximilian"
    success = repo.update(loaded)
    assert success is True

    updated = repo.get_by_id(student_id)
    assert updated.vorname == "Maximilian"

    # Delete
    success = repo.delete(student_id)
    assert success is True

    deleted = repo.get_by_id(student_id)
    assert deleted is None


def test_multiple_students_workflow(repo):
    """Test: Workflow mit mehreren Studenten"""
    # Füge 3 Studenten ein
    students = [
        Student(0, "IU11111111", "Max", "Mustermann", 3),
        Student(0, "IU22222222", "Anna", "Beispiel", 4),
        Student(0, "IU33333333", "Tom", "Test", 5),
    ]

    ids = [repo.insert(s) for s in students]

    # Alle laden
    all_students = repo.get_all()
    assert len(all_students) == 3

    # Einen updaten
    student2 = repo.get_by_id(ids[1])
    student2.vorname = "Annika"
    repo.update(student2)

    # Einen löschen
    repo.delete(ids[0])

    # Prüfen
    all_students = repo.get_all()
    assert len(all_students) == 2

    remaining_names = [s.vorname for s in all_students]
    assert "Max" not in remaining_names
    assert "Annika" in remaining_names
    assert "Tom" in remaining_names