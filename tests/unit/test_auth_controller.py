# tests/unit/test_auth_controller.py
"""
Unit Tests für AuthController

Testet die AuthController-Klasse mit echten Funktionen aber Mocks für DB.
"""
import pytest
import sys
from pathlib import Path

# Füge Project-Root zum Python-Path hinzu
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# AuthController aus controllers/ importieren
from controllers import AuthController


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def temp_test_db(tmp_path):
    """Erstellt temporäre Test-DB mit Schema"""
    import sqlite3

    db_path = tmp_path / "test_auth.db"

    con = sqlite3.connect(str(db_path))
    con.execute("PRAGMA foreign_keys = ON;")

    # Minimales Schema für Tests (OHNE benutzername - wird nicht verwendet!)
    con.execute("""
                CREATE TABLE student
                (
                    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                    matrikel_nr         TEXT UNIQUE NOT NULL,
                    vorname             TEXT        NOT NULL,
                    nachname            TEXT        NOT NULL,
                    email               TEXT        NOT NULL,
                    eingeschrieben_seit DATE        NOT NULL,
                    login_id            INTEGER
                )
                """)

    con.execute("""
                CREATE TABLE login
                (
                    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id           INTEGER NOT NULL,
                    email                TEXT    NOT NULL UNIQUE,
                    password_hash        TEXT    NOT NULL,
                    is_active            INTEGER DEFAULT 1,
                    role                 TEXT    DEFAULT 'student',
                    created_at           TEXT,
                    must_change_password INTEGER DEFAULT 0,
                    last_login           TEXT,
                    FOREIGN KEY (student_id) REFERENCES student (id) ON DELETE CASCADE
                )
                """)

    con.commit()
    con.close()

    yield str(db_path)


@pytest.fixture
def auth_ctrl(temp_test_db):
    """AuthController mit Test-DB"""
    return AuthController(temp_test_db)


# ============================================================================
# TESTS
# ============================================================================

def test_auth_controller_initialization(temp_test_db):
    """Test: AuthController kann initialisiert werden"""
    ctrl = AuthController(temp_test_db)
    assert ctrl.db_path == temp_test_db


def test_register_new_user(auth_ctrl, temp_test_db):
    """Test: Neuen User registrieren"""
    import sqlite3

    # Erstelle Student first (wird für FK benötigt)
    with sqlite3.connect(temp_test_db) as con:
        cur = con.execute("""
                          INSERT INTO student (matrikel_nr, vorname, nachname, email, eingeschrieben_seit)
                          VALUES ('IU12345', 'Test', 'User', 'test@example.com', '2024-01-01')
                          """)
        student_id = cur.lastrowid
        con.commit()

    # Registriere User mit LANGEM Passwort (>= 12 Zeichen!)
    result = auth_ctrl.register(
        email="test@example.com",
        password="SuperSicher123!",  # 16 Zeichen ✓
        student_id=student_id
    )

    assert result['success'] is True, f"Registrierung fehlgeschlagen: {result.get('error')}"
    assert 'user_id' in result
    assert result['email'] == "test@example.com"


def test_register_duplicate_email(auth_ctrl, temp_test_db):
    """Test: Registrierung mit existierender Email schlägt fehl"""
    import sqlite3

    # Erstelle Student
    with sqlite3.connect(temp_test_db) as con:
        cur = con.execute("""
                          INSERT INTO student (matrikel_nr, vorname, nachname, email, eingeschrieben_seit)
                          VALUES ('IU12345', 'Test', 'User', 'test@example.com', '2024-01-01')
                          """)
        student_id = cur.lastrowid
        con.commit()

    # Erste Registrierung mit LANGEM Passwort (>= 12 Zeichen!)
    auth_ctrl.register("test@example.com", "TestPassword123!", student_id)

    # Zweite Registrierung (sollte fehlschlagen)
    result = auth_ctrl.register("test@example.com", "DifferentPass456!", student_id)

    assert result['success'] is False
    assert 'bereits registriert' in result['error'].lower()


def test_login_success(auth_ctrl, temp_test_db):
    """Test: Erfolgreicher Login"""
    import sqlite3

    # Setup: Erstelle Student und registriere User
    with sqlite3.connect(temp_test_db) as con:
        cur = con.execute("""
                          INSERT INTO student (matrikel_nr, vorname, nachname, email, eingeschrieben_seit)
                          VALUES ('IU12345', 'Test', 'User', 'test@example.com', '2024-01-01')
                          """)
        student_id = cur.lastrowid
        con.commit()

    password = "TestPassword123!"  # 16 Zeichen ✓
    auth_ctrl.register("test@example.com", password, student_id)

    # Login
    result = auth_ctrl.login("test@example.com", password)

    assert result['success'] is True, f"Login fehlgeschlagen: {result.get('error')}"
    assert result['email'] == "test@example.com"
    assert 'user_id' in result


def test_login_wrong_password(auth_ctrl, temp_test_db):
    """Test: Login mit falschem Passwort schlägt fehl"""
    import sqlite3

    # Setup
    with sqlite3.connect(temp_test_db) as con:
        cur = con.execute("""
                          INSERT INTO student (matrikel_nr, vorname, nachname, email, eingeschrieben_seit)
                          VALUES ('IU12345', 'Test', 'User', 'test@example.com', '2024-01-01')
                          """)
        student_id = cur.lastrowid
        con.commit()

    auth_ctrl.register("test@example.com", "CorrectPassword123!", student_id)

    # Login mit falschem Passwort
    result = auth_ctrl.login("test@example.com", "WrongPassword")

    assert result['success'] is False
    assert 'passwort' in result['error'].lower()


def test_login_nonexistent_user(auth_ctrl):
    """Test: Login mit nicht existierendem User"""
    result = auth_ctrl.login("nonexistent@example.com", "SomePassword123!")

    assert result['success'] is False
    assert 'e-mail' in result['error'].lower() or 'passwort' in result['error'].lower()


def test_change_password_success(auth_ctrl, temp_test_db):
    """Test: Passwort erfolgreich ändern"""
    import sqlite3

    # Setup
    with sqlite3.connect(temp_test_db) as con:
        cur = con.execute("""
                          INSERT INTO student (matrikel_nr, vorname, nachname, email, eingeschrieben_seit)
                          VALUES ('IU12345', 'Test', 'User', 'test@example.com', '2024-01-01')
                          """)
        student_id = cur.lastrowid
        con.commit()

    old_password = "OldPassword123!"  # 16 Zeichen ✓
    new_password = "NewPassword123!"  # 16 Zeichen ✓

    reg_result = auth_ctrl.register("test@example.com", old_password, student_id)
    assert reg_result['success'] is True, f"Registrierung fehlgeschlagen: {reg_result.get('error')}"
    user_id = reg_result['user_id']

    # Passwort ändern
    result = auth_ctrl.change_password(user_id, old_password, new_password)

    assert result['success'] is True, f"Passwort-Änderung fehlgeschlagen: {result.get('error')}"

    # Teste ob neues Passwort funktioniert
    login_result = auth_ctrl.login("test@example.com", new_password)
    assert login_result['success'] is True


def test_change_password_wrong_old_password(auth_ctrl, temp_test_db):
    """Test: Passwort ändern mit falschem alten Passwort"""
    import sqlite3

    # Setup
    with sqlite3.connect(temp_test_db) as con:
        cur = con.execute("""
                          INSERT INTO student (matrikel_nr, vorname, nachname, email, eingeschrieben_seit)
                          VALUES ('IU12345', 'Test', 'User', 'test@example.com', '2024-01-01')
                          """)
        student_id = cur.lastrowid
        con.commit()

    password = "OldPassword123!"  # 16 Zeichen ✓
    reg_result = auth_ctrl.register("test@example.com", password, student_id)
    assert reg_result['success'] is True, f"Registrierung fehlgeschlagen: {reg_result.get('error')}"
    user_id = reg_result['user_id']

    # Passwort ändern mit falschem alten Passwort
    result = auth_ctrl.change_password(user_id, "WrongOldPassword!", "NewPassword123!")

    assert result['success'] is False
    assert 'nicht korrekt' in result['error'].lower() or 'falsch' in result['error'].lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])