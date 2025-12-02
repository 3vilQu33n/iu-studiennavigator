# tests/unit/test_student_repository.py
"""
Unit Tests fuer StudentRepository (repositories/student_repository.py)

Testet das StudentRepository:
- get_by_id() - Student nach ID laden
- get_by_login_id() - Student nach login_id laden (KOMPOSITION)
- get_by_matrikel_nr() - Student nach Matrikelnummer laden
- get_all() - Alle Studenten laden
- insert() - Neuen Studenten anlegen
- update() - Studenten aktualisieren
- delete() - Studenten loeschen
- exists() - Existenz pruefen

Besondere Aspekte:
- UNIQUE Constraints auf matrikel_nr und login_id
- FOREIGN KEY auf login_id (KOMPOSITION zu Login)
- Validierung vor Insert/Update mit student.validate() -> (bool, str)
- Bei DB-Fehlern: get-Methoden geben None/[] zurueck, insert/update werfen Exceptions
"""
from __future__ import annotations

import pytest
import sqlite3
import tempfile
import os

# Mark this whole module as unit tests
pytestmark = pytest.mark.unit


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def student_repository_class():
    """Importiert StudentRepository-Klasse"""
    try:
        from repositories import StudentRepository
        return StudentRepository
    except ImportError:
        from repositories.student_repository import StudentRepository
        return StudentRepository


@pytest.fixture
def student_class():
    """Importiert Student-Klasse"""
    try:
        from models import Student
        return Student
    except ImportError:
        from models.student import Student
        return Student


@pytest.fixture
def temp_db():
    """Erstellt temporaere Test-Datenbank mit vollstaendigem Schema"""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)

    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON;")

    # Erstelle Schema mit Login-Tabelle (wegen FK)
    conn.executescript("""
        -- Login-Tabelle zuerst (wegen FK)
        CREATE TABLE IF NOT EXISTS login (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            benutzername TEXT UNIQUE NOT NULL,
            passwort_hash TEXT NOT NULL
        );

        -- Student-Tabelle mit UNIQUE Constraints
        CREATE TABLE IF NOT EXISTS student (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vorname TEXT NOT NULL,
            nachname TEXT NOT NULL,
            matrikel_nr TEXT UNIQUE NOT NULL,
            login_id INTEGER UNIQUE,
            FOREIGN KEY (login_id) REFERENCES login(id)
        );

        -- Test-Logins einfuegen
        INSERT INTO login (id, benutzername, passwort_hash) VALUES
            (1, 'max.mustermann', 'hash1'),
            (2, 'erika.musterfrau', 'hash2'),
            (3, 'peter.pan', 'hash3'),
            (4, 'unused.login', 'hash4');
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
def temp_db_with_students(temp_db):
    """Test-DB mit vorhandenen Studenten"""
    conn = sqlite3.connect(temp_db)
    conn.execute("PRAGMA foreign_keys = ON;")

    conn.executescript("""
        INSERT INTO student (id, vorname, nachname, matrikel_nr, login_id) VALUES
            (1, 'Max', 'Mustermann', 'IU12345678', 1),
            (2, 'Erika', 'Musterfrau', 'IU87654321', 2),
            (3, 'Peter', 'Pan', 'IU11111111', NULL);
    """)
    conn.commit()
    conn.close()

    return temp_db


@pytest.fixture
def repository(student_repository_class, temp_db):
    """Erstellt Repository-Instanz mit Test-DB"""
    return student_repository_class(temp_db)


@pytest.fixture
def repository_with_students(student_repository_class, temp_db_with_students):
    """Erstellt Repository-Instanz mit Test-DB inkl. Studenten"""
    return student_repository_class(temp_db_with_students)


@pytest.fixture
def sample_student(student_class):
    """Erstellt Sample-Student fuer Tests"""
    return student_class(
        id=0,
        matrikel_nr="IU99999999",
        vorname="Test",
        nachname="Student",
        login_id=3  # Existiert in temp_db
    )


# ============================================================================
# INITIALIZATION TESTS
# ============================================================================

class TestStudentRepositoryInit:
    """Tests fuer Repository-Initialisierung"""

    def test_init_with_db_path(self, student_repository_class, temp_db):
        """Repository kann mit DB-Pfad initialisiert werden"""
        repo = student_repository_class(temp_db)

        # db_path ist private, aber Repository funktioniert
        assert repo is not None

    def test_init_stores_db_path(self, student_repository_class):
        """Repository speichert db_path (privat)"""
        repo = student_repository_class("/path/to/db.sqlite")

        # Zugriff auf privates Attribut
        assert repo._StudentRepository__db_path == "/path/to/db.sqlite"


# ============================================================================
# GET_BY_ID TESTS
# ============================================================================

class TestGetById:
    """Tests fuer get_by_id() Methode"""

    def test_get_by_id_existing(self, repository_with_students, student_class):
        """get_by_id() laedt existierenden Studenten"""
        result = repository_with_students.get_by_id(1)

        assert result is not None
        assert isinstance(result, student_class)
        assert result.id == 1

    def test_get_by_id_correct_data(self, repository_with_students):
        """get_by_id() laedt korrekte Daten"""
        result = repository_with_students.get_by_id(1)

        assert result.vorname == 'Max'
        assert result.nachname == 'Mustermann'
        assert result.matrikel_nr == 'IU12345678'
        assert result.login_id == 1

    def test_get_by_id_not_found(self, repository):
        """get_by_id() gibt None zurueck wenn nicht gefunden"""
        result = repository.get_by_id(999)

        assert result is None

    def test_get_by_id_student_without_login(self, repository_with_students):
        """get_by_id() laedt Student ohne login_id"""
        result = repository_with_students.get_by_id(3)

        assert result is not None
        assert result.vorname == 'Peter'
        assert result.login_id is None


# ============================================================================
# GET_BY_LOGIN_ID TESTS
# ============================================================================

class TestGetByLoginId:
    """Tests fuer get_by_login_id() Methode (KOMPOSITION)"""

    def test_get_by_login_id_existing(self, repository_with_students, student_class):
        """get_by_login_id() laedt Student mit login_id"""
        result = repository_with_students.get_by_login_id(1)

        assert result is not None
        assert isinstance(result, student_class)
        assert result.login_id == 1

    def test_get_by_login_id_correct_student(self, repository_with_students):
        """get_by_login_id() laedt korrekten Studenten"""
        result = repository_with_students.get_by_login_id(2)

        assert result.vorname == 'Erika'
        assert result.nachname == 'Musterfrau'
        assert result.matrikel_nr == 'IU87654321'

    def test_get_by_login_id_not_found(self, repository_with_students):
        """get_by_login_id() gibt None wenn kein Student mit login_id"""
        # login_id 4 existiert, aber kein Student hat sie
        result = repository_with_students.get_by_login_id(4)

        assert result is None

    def test_get_by_login_id_nonexistent(self, repository):
        """get_by_login_id() gibt None fuer nicht existierende login_id"""
        result = repository.get_by_login_id(999)

        assert result is None


# ============================================================================
# GET_BY_MATRIKEL_NR TESTS
# ============================================================================

class TestGetByMatrikelNr:
    """Tests fuer get_by_matrikel_nr() Methode"""

    def test_get_by_matrikel_nr_existing(self, repository_with_students, student_class):
        """get_by_matrikel_nr() laedt Student mit Matrikelnummer"""
        result = repository_with_students.get_by_matrikel_nr('IU12345678')

        assert result is not None
        assert isinstance(result, student_class)
        assert result.matrikel_nr == 'IU12345678'

    def test_get_by_matrikel_nr_correct_student(self, repository_with_students):
        """get_by_matrikel_nr() laedt korrekten Studenten"""
        result = repository_with_students.get_by_matrikel_nr('IU87654321')

        assert result.vorname == 'Erika'
        assert result.nachname == 'Musterfrau'
        assert result.id == 2

    def test_get_by_matrikel_nr_not_found(self, repository):
        """get_by_matrikel_nr() gibt None wenn nicht gefunden"""
        result = repository.get_by_matrikel_nr('INVALID123')

        assert result is None

    def test_get_by_matrikel_nr_case_sensitive(self, repository_with_students):
        """get_by_matrikel_nr() ist case-sensitive"""
        # Kleinbuchstaben sollten nicht gefunden werden
        result = repository_with_students.get_by_matrikel_nr('iu12345678')

        assert result is None


# ============================================================================
# GET_ALL TESTS
# ============================================================================

class TestGetAll:
    """Tests fuer get_all() Methode"""

    def test_get_all_returns_list(self, repository_with_students):
        """get_all() gibt Liste zurueck"""
        result = repository_with_students.get_all()

        assert isinstance(result, list)

    def test_get_all_correct_count(self, repository_with_students):
        """get_all() gibt alle Studenten zurueck"""
        result = repository_with_students.get_all()

        assert len(result) == 3

    def test_get_all_contains_students(self, repository_with_students, student_class):
        """get_all() enthaelt Student-Objekte"""
        result = repository_with_students.get_all()

        for student in result:
            assert isinstance(student, student_class)

    def test_get_all_empty(self, repository):
        """get_all() gibt leere Liste wenn keine Studenten"""
        result = repository.get_all()

        assert result == []


# ============================================================================
# INSERT TESTS
# ============================================================================

class TestInsert:
    """Tests fuer insert() Methode"""

    def test_insert_returns_id(self, repository, sample_student):
        """insert() gibt neue ID zurueck"""
        new_id = repository.insert(sample_student)

        assert isinstance(new_id, int)
        assert new_id > 0

    def test_insert_stores_data(self, repository, sample_student):
        """insert() speichert Daten korrekt"""
        new_id = repository.insert(sample_student)

        loaded = repository.get_by_id(new_id)
        assert loaded is not None
        assert loaded.vorname == sample_student.vorname
        assert loaded.nachname == sample_student.nachname
        assert loaded.matrikel_nr == sample_student.matrikel_nr

    def test_insert_increments_id(self, repository, student_class):
        """insert() inkrementiert IDs"""
        s1 = student_class(
            id=0,
            matrikel_nr="IU00000001",
            vorname="Test1",
            nachname="Student1",
            login_id=None
        )
        s2 = student_class(
            id=0,
            matrikel_nr="IU00000002",
            vorname="Test2",
            nachname="Student2",
            login_id=None
        )

        id1 = repository.insert(s1)
        id2 = repository.insert(s2)

        assert id2 > id1

    def test_insert_validates_student(self, repository, student_class):
        """insert() validiert Student vor Insert via student.validate()"""
        # Student mit leerem Vornamen (wird von validate() abgelehnt)
        invalid_student = student_class(
            id=0,
            matrikel_nr="IU99999999",
            vorname="",  # Leer - ungueltig
            nachname="Student",
            login_id=None
        )

        with pytest.raises(ValueError):
            repository.insert(invalid_student)

    def test_insert_duplicate_matrikel_nr_raises(self, repository_with_students, student_class):
        """insert() wirft ValueError bei doppelter Matrikelnummer"""
        duplicate = student_class(
            id=0,
            matrikel_nr="IU12345678",  # Existiert bereits
            vorname="Neu",
            nachname="Student",
            login_id=None
        )

        with pytest.raises(ValueError) as exc_info:
            repository_with_students.insert(duplicate)

        assert "Matrikelnummer" in str(exc_info.value)
        assert "existiert bereits" in str(exc_info.value)

    def test_insert_duplicate_login_id_raises(self, repository_with_students, student_class):
        """insert() wirft ValueError bei doppelter login_id"""
        duplicate = student_class(
            id=0,
            matrikel_nr="IU99999999",
            vorname="Neu",
            nachname="Student",
            login_id=1  # Bereits von Max verwendet
        )

        with pytest.raises(ValueError) as exc_info:
            repository_with_students.insert(duplicate)

        assert "Login-ID" in str(exc_info.value)
        assert "bereits vergeben" in str(exc_info.value)

    def test_insert_nonexistent_login_id_raises(self, repository, student_class):
        """insert() wirft ValueError bei nicht existierender login_id (FK)"""
        student = student_class(
            id=0,
            matrikel_nr="IU99999999",
            vorname="Test",
            nachname="Student",
            login_id=999  # Existiert nicht
        )

        with pytest.raises(ValueError) as exc_info:
            repository.insert(student)

        assert "Login-ID" in str(exc_info.value)
        assert "existiert nicht" in str(exc_info.value)

    def test_insert_with_null_login_id(self, repository, student_class):
        """insert() erlaubt NULL fuer login_id"""
        student = student_class(
            id=0,
            matrikel_nr="IU99999999",
            vorname="Ohne",
            nachname="Login",
            login_id=None
        )

        new_id = repository.insert(student)
        loaded = repository.get_by_id(new_id)

        assert loaded.login_id is None


# ============================================================================
# UPDATE TESTS
# ============================================================================

class TestUpdate:
    """Tests fuer update() Methode"""

    def test_update_success(self, repository_with_students):
        """update() aktualisiert Student erfolgreich"""
        student = repository_with_students.get_by_id(1)
        student.vorname = 'Maximilian'

        result = repository_with_students.update(student)

        assert result is True

        loaded = repository_with_students.get_by_id(1)
        assert loaded.vorname == 'Maximilian'

    def test_update_nachname(self, repository_with_students):
        """update() kann Nachnamen aendern"""
        student = repository_with_students.get_by_id(1)
        student.nachname = 'Muster'

        repository_with_students.update(student)

        loaded = repository_with_students.get_by_id(1)
        assert loaded.nachname == 'Muster'

    def test_update_validates_student(self, repository_with_students):
        """update() validiert Student vor Update via student.validate()"""
        student = repository_with_students.get_by_id(1)
        student.vorname = ''  # Leer - ungueltig

        with pytest.raises(ValueError):
            repository_with_students.update(student)

    def test_update_duplicate_matrikel_nr_raises(self, repository_with_students):
        """update() wirft ValueError bei doppelter Matrikelnummer"""
        student = repository_with_students.get_by_id(1)
        student.matrikel_nr = 'IU87654321'  # Gehoert zu Erika

        with pytest.raises(ValueError) as exc_info:
            repository_with_students.update(student)

        assert "Matrikelnummer" in str(exc_info.value)
        assert "existiert bereits" in str(exc_info.value)

    def test_update_duplicate_login_id_raises(self, repository_with_students):
        """update() wirft ValueError bei doppelter login_id"""
        student = repository_with_students.get_by_id(1)
        student.login_id = 2  # Gehoert zu Erika

        with pytest.raises(ValueError) as exc_info:
            repository_with_students.update(student)

        assert "Login-ID" in str(exc_info.value)
        assert "bereits vergeben" in str(exc_info.value)

    def test_update_nonexistent_login_id_raises(self, repository_with_students):
        """update() wirft ValueError bei nicht existierender login_id (FK)"""
        student = repository_with_students.get_by_id(1)
        student.login_id = 999  # Existiert nicht

        with pytest.raises(ValueError) as exc_info:
            repository_with_students.update(student)

        assert "Login-ID" in str(exc_info.value)
        assert "existiert nicht" in str(exc_info.value)

    def test_update_returns_true(self, repository_with_students):
        """update() gibt True zurueck"""
        student = repository_with_students.get_by_id(1)
        student.vorname = 'Max'  # Gleich, aber Update sollte funktionieren

        result = repository_with_students.update(student)

        assert result is True


# ============================================================================
# DELETE TESTS
# ============================================================================

class TestDelete:
    """Tests fuer delete() Methode"""

    def test_delete_success(self, repository_with_students):
        """delete() loescht Student erfolgreich"""
        # Student existiert
        before = repository_with_students.get_by_id(1)
        assert before is not None

        # Loeschen
        result = repository_with_students.delete(1)
        assert result is True

        # Student existiert nicht mehr
        after = repository_with_students.get_by_id(1)
        assert after is None

    def test_delete_returns_true(self, repository_with_students):
        """delete() gibt True zurueck"""
        result = repository_with_students.delete(1)

        assert result is True

    def test_delete_reduces_count(self, repository_with_students):
        """delete() reduziert Anzahl der Studenten"""
        before = len(repository_with_students.get_all())

        repository_with_students.delete(1)

        after = len(repository_with_students.get_all())
        assert after == before - 1

    def test_delete_nonexistent_returns_true(self, repository):
        """delete() gibt True zurueck auch wenn Student nicht existiert"""
        # SQLite loescht 0 Zeilen, aber kein Fehler
        result = repository.delete(999)

        assert result is True


# ============================================================================
# EXISTS TESTS
# ============================================================================

class TestExists:
    """Tests fuer exists() Methode"""

    def test_exists_true(self, repository_with_students):
        """exists() gibt True wenn Student existiert"""
        result = repository_with_students.exists('IU12345678')

        assert result is True

    def test_exists_false(self, repository):
        """exists() gibt False wenn Student nicht existiert"""
        result = repository.exists('INVALID123')

        assert result is False

    def test_exists_case_sensitive(self, repository_with_students):
        """exists() ist case-sensitive"""
        result = repository_with_students.exists('iu12345678')

        assert result is False


# ============================================================================
# PRIVATE METHOD TESTS
# ============================================================================

class TestPrivateMethods:
    """Tests fuer private Hilfsmethoden"""

    def test_get_connection_returns_connection(self, repository):
        """__get_connection() gibt Connection zurueck"""
        conn = repository._StudentRepository__get_connection()

        assert isinstance(conn, sqlite3.Connection)
        conn.close()

    def test_get_connection_enables_foreign_keys(self, repository):
        """__get_connection() aktiviert Foreign Keys"""
        conn = repository._StudentRepository__get_connection()

        result = conn.execute("PRAGMA foreign_keys;").fetchone()
        assert result[0] == 1

        conn.close()

    def test_get_connection_sets_row_factory(self, repository):
        """__get_connection() setzt Row Factory auf sqlite3.Row"""
        conn = repository._StudentRepository__get_connection()

        assert conn.row_factory == sqlite3.Row

        conn.close()

    def test_db_path_is_private(self, student_repository_class, temp_db):
        """db_path ist privates Attribut (__db_path)"""
        repo = student_repository_class(temp_db)

        # Direkter Zugriff auf db_path sollte fehlschlagen
        assert not hasattr(repo, 'db_path')

        # Zugriff ueber Name-Mangling funktioniert
        assert repo._StudentRepository__db_path == temp_db


# ============================================================================
# DB ERROR HANDLING TESTS
# ============================================================================

class TestDbErrorHandling:
    """Tests fuer DB-Fehlerbehandlung"""

    def test_get_by_id_returns_none_on_error(self, student_repository_class):
        """get_by_id() gibt None bei DB-Fehler zurueck"""
        repo = student_repository_class("/nonexistent/path.db")

        # Sollte None zurueckgeben, nicht Exception werfen
        result = repo.get_by_id(1)
        assert result is None

    def test_get_by_login_id_returns_none_on_error(self, student_repository_class):
        """get_by_login_id() gibt None bei DB-Fehler zurueck"""
        repo = student_repository_class("/nonexistent/path.db")

        result = repo.get_by_login_id(1)
        assert result is None

    def test_get_by_matrikel_nr_returns_none_on_error(self, student_repository_class):
        """get_by_matrikel_nr() gibt None bei DB-Fehler zurueck"""
        repo = student_repository_class("/nonexistent/path.db")

        result = repo.get_by_matrikel_nr("IU12345678")
        assert result is None

    def test_get_all_returns_empty_list_on_error(self, student_repository_class):
        """get_all() gibt leere Liste bei DB-Fehler zurueck"""
        repo = student_repository_class("/nonexistent/path.db")

        result = repo.get_all()
        assert result == []

    def test_exists_returns_false_on_error(self, student_repository_class):
        """exists() gibt False bei DB-Fehler zurueck"""
        repo = student_repository_class("/nonexistent/path.db")

        result = repo.exists("IU12345678")
        assert result is False

    def test_delete_returns_false_on_error(self, student_repository_class):
        """delete() gibt False bei DB-Fehler zurueck"""
        repo = student_repository_class("/nonexistent/path.db")

        result = repo.delete(1)
        assert result is False


# ============================================================================
# INTEGRATION-LIKE TESTS
# ============================================================================

class TestIntegrationScenarios:
    """Tests fuer typische Nutzungsszenarien"""

    def test_full_student_lifecycle(self, repository, student_class):
        """Test: Vollstaendiger Student-Lebenszyklus"""
        # 1. Student erstellen
        student = student_class(
            id=0,
            matrikel_nr="IU99999999",
            vorname="Neu",
            nachname="Student",
            login_id=3
        )
        student_id = repository.insert(student)

        # 2. Laden und pruefen
        loaded = repository.get_by_id(student_id)
        assert loaded.vorname == 'Neu'

        # 3. Aktualisieren
        loaded.vorname = 'Aktualisiert'
        repository.update(loaded)

        # 4. Pruefen
        updated = repository.get_by_id(student_id)
        assert updated.vorname == 'Aktualisiert'

        # 5. Loeschen
        repository.delete(student_id)
        assert repository.get_by_id(student_id) is None

    def test_login_composition_workflow(self, repository_with_students):
        """Test: Login-KOMPOSITION Workflow"""
        # 1. Student ueber login_id finden
        student = repository_with_students.get_by_login_id(1)
        assert student is not None
        assert student.vorname == 'Max'

        # 2. Gleicher Student ueber ID
        same_student = repository_with_students.get_by_id(student.id)
        assert same_student.login_id == 1

    def test_matrikel_unique_constraint(self, repository, student_class):
        """Test: Matrikelnummer UNIQUE Constraint"""
        # Ersten Student anlegen
        s1 = student_class(
            id=0,
            matrikel_nr="IU11111111",
            vorname="Erster",
            nachname="Student",
            login_id=None
        )
        repository.insert(s1)

        # Zweiten mit gleicher Matrikelnummer sollte fehlschlagen
        s2 = student_class(
            id=0,
            matrikel_nr="IU11111111",  # Doppelt
            vorname="Zweiter",
            nachname="Student",
            login_id=None
        )

        with pytest.raises(ValueError):
            repository.insert(s2)


# ============================================================================
# EDGE CASES
# ============================================================================

class TestEdgeCases:
    """Tests fuer Randfaelle"""

    def test_get_by_id_zero(self, repository):
        """get_by_id() mit ID 0 gibt None zurueck"""
        result = repository.get_by_id(0)

        assert result is None

    def test_get_by_id_negative(self, repository):
        """get_by_id() mit negativer ID gibt None zurueck"""
        result = repository.get_by_id(-1)

        assert result is None

    def test_student_with_unicode_name(self, repository, student_class):
        """Student mit Unicode-Namen (Umlaute)"""
        student = student_class(
            id=0,
            matrikel_nr="IU99999999",
            vorname="Müller",
            nachname="Schröder",
            login_id=None
        )

        new_id = repository.insert(student)
        loaded = repository.get_by_id(new_id)

        assert loaded.vorname == "Müller"
        assert loaded.nachname == "Schröder"

    def test_student_with_long_name(self, repository, student_class):
        """Student mit langem Namen"""
        long_name = "A" * 100
        student = student_class(
            id=0,
            matrikel_nr="IU99999999",
            vorname=long_name,
            nachname=long_name,
            login_id=None
        )

        new_id = repository.insert(student)
        loaded = repository.get_by_id(new_id)

        assert loaded.vorname == long_name
        assert loaded.nachname == long_name

    def test_multiple_students_null_login(self, repository, student_class):
        """Mehrere Studenten mit NULL login_id"""
        # NULL ist bei UNIQUE erlaubt (mehrfach)
        for i in range(3):
            student = student_class(
                id=0,
                matrikel_nr=f"IU0000000{i}",
                vorname=f"Student{i}",
                nachname="Ohne Login",
                login_id=None
            )
            repository.insert(student)

        all_students = repository.get_all()
        null_login_count = sum(1 for s in all_students if s.login_id is None)

        assert null_login_count == 3