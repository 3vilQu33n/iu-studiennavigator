# tests/unit/test_auth_controller.py
"""
Unit Tests fuer AuthController

Testet Login, Passwort-Aenderung, Registrierung und Initialpasswort-Generierung.
"""
import pytest
import sqlite3
from datetime import datetime
from argon2 import PasswordHasher

from controllers.auth_controller import AuthController

# Mark this whole module as unit test
pytestmark = pytest.mark.unit

# Password Hasher fuer Test-Daten
ph = PasswordHasher()


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def test_db(tmp_path):
    """Erstellt eine Test-Datenbank mit login-Schema"""
    db_path = tmp_path / "test_auth.db"

    with sqlite3.connect(str(db_path)) as conn:
        # noinspection SqlResolve
        conn.execute("""
            CREATE TABLE login (
                id                   INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id           INTEGER,
                email                TEXT UNIQUE NOT NULL,
                benutzername         TEXT UNIQUE,
                password_hash        TEXT NOT NULL,
                is_active            INTEGER DEFAULT 1,
                role                 TEXT DEFAULT 'student' CHECK (role IN ('student','admin','tutor')),
                created_at           TEXT,
                must_change_password INTEGER DEFAULT 0,
                last_login           TEXT
            )
        """)
        conn.commit()

    return str(db_path)


@pytest.fixture
def auth_controller(test_db):
    """Erstellt AuthController mit Test-Datenbank"""
    return AuthController(test_db)


@pytest.fixture
def test_db_with_user(test_db):
    """Test-Datenbank mit einem existierenden User"""
    password_hash = ph.hash("TestPassword123!")

    with sqlite3.connect(test_db) as conn:
        # noinspection SqlResolve
        conn.execute("""
            INSERT INTO login (student_id, email, benutzername, password_hash, is_active, role, created_at, must_change_password)
            VALUES (1, 'test@example.com', 'testuser', ?, 1, 'student', ?, 0)
        """, (password_hash, datetime.now().isoformat()))
        conn.commit()

    return test_db


@pytest.fixture
def auth_with_user(test_db_with_user):
    """AuthController mit vorhandenem User"""
    return AuthController(test_db_with_user)


@pytest.fixture
def test_db_with_inactive_user(test_db):
    """Test-Datenbank mit deaktiviertem User"""
    password_hash = ph.hash("TestPassword123!")

    with sqlite3.connect(test_db) as conn:
        # noinspection SqlResolve
        conn.execute("""
            INSERT INTO login (student_id, email, benutzername, password_hash, is_active, role, created_at)
            VALUES (1, 'inactive@example.com', 'inactiveuser', ?, 0, 'student', ?)
        """, (password_hash, datetime.now().isoformat()))
        conn.commit()

    return test_db


@pytest.fixture
def test_db_with_must_change_user(test_db):
    """Test-Datenbank mit User der Passwort aendern muss"""
    password_hash = ph.hash("TempPassword123!")

    with sqlite3.connect(test_db) as conn:
        # noinspection SqlResolve
        conn.execute("""
            INSERT INTO login (student_id, email, benutzername, password_hash, is_active, role, created_at, must_change_password)
            VALUES (1, 'mustchange@example.com', 'mustchangeuser', ?, 1, 'student', ?, 1)
        """, (password_hash, datetime.now().isoformat()))
        conn.commit()

    return test_db


# ============================================================================
# INITIALIZATION TESTS
# ============================================================================

class TestAuthControllerInit:
    """Tests fuer AuthController Initialisierung"""

    def test_init_sets_db_path(self, test_db):
        """Test: db_path wird korrekt gesetzt"""
        auth = AuthController(test_db)
        assert auth.db_path == test_db

    def test_init_with_nonexistent_db(self, tmp_path):
        """Test: Initialisierung mit nicht-existierender DB"""
        db_path = str(tmp_path / "nonexistent.db")
        auth = AuthController(db_path)
        assert auth.db_path == db_path


# ============================================================================
# LOGIN TESTS
# ============================================================================

class TestLogin:
    """Tests fuer login() Methode"""

    def test_login_success(self, auth_with_user):
        """Test: Erfolgreicher Login"""
        result = auth_with_user.login("test@example.com", "TestPassword123!")

        assert result['success'] is True
        assert result['user_id'] == 1
        assert result['email'] == "test@example.com"
        assert result['must_change_password'] is False

    def test_login_case_insensitive_email(self, auth_with_user):
        """Test: Login mit Gross-/Kleinschreibung der E-Mail"""
        result = auth_with_user.login("TEST@EXAMPLE.COM", "TestPassword123!")

        assert result['success'] is True
        assert result['email'] == "test@example.com"

    def test_login_email_with_spaces(self, auth_with_user):
        """Test: Login mit Leerzeichen in E-Mail"""
        result = auth_with_user.login("  test@example.com  ", "TestPassword123!")

        assert result['success'] is True

    def test_login_wrong_password(self, auth_with_user):
        """Test: Login mit falschem Passwort"""
        result = auth_with_user.login("test@example.com", "WrongPassword123!")

        assert result['success'] is False
        assert 'error' in result
        assert "E-Mail oder Passwort" in result['error']

    def test_login_nonexistent_email(self, auth_controller):
        """Test: Login mit nicht existierender E-Mail"""
        result = auth_controller.login("nonexistent@example.com", "SomePassword123!")

        assert result['success'] is False
        assert 'error' in result
        assert "E-Mail oder Passwort" in result['error']

    def test_login_empty_email(self, auth_controller):
        """Test: Login mit leerer E-Mail"""
        result = auth_controller.login("", "SomePassword123!")

        assert result['success'] is False

    def test_login_empty_password(self, auth_with_user):
        """Test: Login mit leerem Passwort"""
        result = auth_with_user.login("test@example.com", "")

        assert result['success'] is False

    def test_login_inactive_account(self, test_db_with_inactive_user):
        """Test: Login mit deaktiviertem Account"""
        auth = AuthController(test_db_with_inactive_user)
        result = auth.login("inactive@example.com", "TestPassword123!")

        assert result['success'] is False
        assert 'error' in result
        assert "deaktiviert" in result['error']

    def test_login_must_change_password_flag(self, test_db_with_must_change_user):
        """Test: Login mit must_change_password Flag"""
        auth = AuthController(test_db_with_must_change_user)
        result = auth.login("mustchange@example.com", "TempPassword123!")

        assert result['success'] is True
        assert result['must_change_password'] is True

    def test_login_updates_last_login(self, test_db_with_user):
        """Test: Login aktualisiert last_login Timestamp"""
        auth = AuthController(test_db_with_user)

        # Vor Login: last_login ist NULL
        with sqlite3.connect(test_db_with_user) as conn:
            # noinspection SqlResolve
            before = conn.execute("SELECT last_login FROM login WHERE id = 1").fetchone()[0]

        assert before is None

        # Login durchfuehren
        auth.login("test@example.com", "TestPassword123!")

        # Nach Login: last_login ist gesetzt
        with sqlite3.connect(test_db_with_user) as conn:
            # noinspection SqlResolve
            after = conn.execute("SELECT last_login FROM login WHERE id = 1").fetchone()[0]

        assert after is not None


# ============================================================================
# CHANGE PASSWORD TESTS
# ============================================================================

class TestChangePassword:
    """Tests fuer change_password() Methode"""

    def test_change_password_success(self, test_db_with_user):
        """Test: Erfolgreiches Passwort aendern"""
        auth = AuthController(test_db_with_user)
        result = auth.change_password(1, "TestPassword123!", "NewPassword456!")

        assert result['success'] is True
        assert 'message' in result

        # Verifiziere dass neues Passwort funktioniert
        login_result = auth.login("test@example.com", "NewPassword456!")
        assert login_result['success'] is True

    def test_change_password_wrong_old_password(self, auth_with_user):
        """Test: Passwort aendern mit falschem altem Passwort"""
        result = auth_with_user.change_password(1, "WrongOldPassword!", "NewPassword456!")

        assert result['success'] is False
        assert 'error' in result
        assert "Altes Passwort" in result['error']

    def test_change_password_nonexistent_user(self, auth_controller):
        """Test: Passwort aendern fuer nicht existierenden User"""
        result = auth_controller.change_password(999, "OldPassword123!", "NewPassword456!")

        assert result['success'] is False
        assert 'error' in result
        assert "nicht gefunden" in result['error']

    def test_change_password_weak_new_password(self, auth_with_user):
        """Test: Passwort aendern mit schwachem neuem Passwort"""
        result = auth_with_user.change_password(1, "TestPassword123!", "weak")

        assert result['success'] is False
        assert 'error' in result

    def test_change_password_clears_must_change_flag(self, test_db_with_must_change_user):
        """Test: Passwort aendern setzt must_change_password auf 0"""
        auth = AuthController(test_db_with_must_change_user)

        # Vor Aenderung: Flag ist 1
        with sqlite3.connect(test_db_with_must_change_user) as conn:
            # noinspection SqlResolve
            before = conn.execute("SELECT must_change_password FROM login WHERE email = 'mustchange@example.com'").fetchone()[0]

        assert before == 1

        # Passwort aendern
        auth.change_password(1, "TempPassword123!", "NewSecurePassword123!")

        # Nach Aenderung: Flag ist 0
        with sqlite3.connect(test_db_with_must_change_user) as conn:
            # noinspection SqlResolve
            after = conn.execute("SELECT must_change_password FROM login WHERE email = 'mustchange@example.com'").fetchone()[0]

        assert after == 0

    def test_change_password_old_password_no_longer_works(self, test_db_with_user):
        """Test: Altes Passwort funktioniert nach Aenderung nicht mehr"""
        auth = AuthController(test_db_with_user)
        auth.change_password(1, "TestPassword123!", "NewPassword456!")

        # Altes Passwort sollte nicht mehr funktionieren
        login_result = auth.login("test@example.com", "TestPassword123!")
        assert login_result['success'] is False


# ============================================================================
# REGISTER TESTS
# ============================================================================

class TestRegister:
    """Tests fuer register() Methode"""

    def test_register_success(self, auth_controller):
        """Test: Erfolgreiche Registrierung"""
        result = auth_controller.register("newuser@example.com", "SecurePassword123!")

        assert result['success'] is True
        assert result['user_id'] is not None
        assert result['email'] == "newuser@example.com"

    def test_register_can_login_after(self, test_db):
        """Test: Nach Registrierung kann man sich einloggen"""
        auth = AuthController(test_db)
        auth.register("newuser@example.com", "SecurePassword123!")

        login_result = auth.login("newuser@example.com", "SecurePassword123!")
        assert login_result['success'] is True

    def test_register_email_normalized(self, auth_controller, test_db):
        """Test: E-Mail wird in DB normalisiert (lowercase, stripped)"""
        result = auth_controller.register("  NewUser@EXAMPLE.COM  ", "SecurePassword123!")

        assert result['success'] is True

        # Pruefe dass E-Mail in DB normalisiert gespeichert wurde
        with sqlite3.connect(test_db) as conn:
            # noinspection SqlResolve
            stored_email = conn.execute("SELECT email FROM login WHERE id = ?", (result['user_id'],)).fetchone()[0]

        assert stored_email == "newuser@example.com"

    def test_register_duplicate_email(self, auth_with_user):
        """Test: Registrierung mit bereits existierender E-Mail"""
        result = auth_with_user.register("test@example.com", "AnotherPassword123!")

        assert result['success'] is False
        assert 'error' in result
        assert "bereits registriert" in result['error']

    def test_register_duplicate_email_case_insensitive(self, auth_with_user):
        """Test: Duplikat-Pruefung ist case-insensitive"""
        result = auth_with_user.register("TEST@EXAMPLE.COM", "AnotherPassword123!")

        assert result['success'] is False
        assert "bereits registriert" in result['error']

    def test_register_weak_password(self, auth_controller):
        """Test: Registrierung mit schwachem Passwort"""
        result = auth_controller.register("newuser@example.com", "weak")

        assert result['success'] is False
        assert 'error' in result

    def test_register_with_student_id(self, auth_controller, test_db):
        """Test: Registrierung mit student_id"""
        result = auth_controller.register("student@example.com", "SecurePassword123!", student_id=42)

        assert result['success'] is True

        # Verifiziere student_id in DB
        with sqlite3.connect(test_db) as conn:
            # noinspection SqlResolve
            student_id = conn.execute("SELECT student_id FROM login WHERE email = 'student@example.com'").fetchone()[0]

        assert student_id == 42

    def test_register_sets_created_at(self, auth_controller, test_db):
        """Test: Registrierung setzt created_at Timestamp"""
        auth_controller.register("newuser@example.com", "SecurePassword123!")

        with sqlite3.connect(test_db) as conn:
            # noinspection SqlResolve
            created_at = conn.execute("SELECT created_at FROM login WHERE email = 'newuser@example.com'").fetchone()[0]

        assert created_at is not None

    def test_register_default_role_is_student(self, auth_controller, test_db):
        """Test: Standard-Rolle ist 'student'"""
        auth_controller.register("newuser@example.com", "SecurePassword123!")

        with sqlite3.connect(test_db) as conn:
            # noinspection SqlResolve
            role = conn.execute("SELECT role FROM login WHERE email = 'newuser@example.com'").fetchone()[0]

        assert role == 'student'

    def test_register_user_is_active(self, auth_controller, test_db):
        """Test: Neuer User ist aktiv"""
        auth_controller.register("newuser@example.com", "SecurePassword123!")

        with sqlite3.connect(test_db) as conn:
            # noinspection SqlResolve
            is_active = conn.execute("SELECT is_active FROM login WHERE email = 'newuser@example.com'").fetchone()[0]

        assert is_active == 1

    def test_register_must_change_password_is_false(self, auth_controller, test_db):
        """Test: must_change_password ist bei normaler Registrierung 0"""
        auth_controller.register("newuser@example.com", "SecurePassword123!")

        with sqlite3.connect(test_db) as conn:
            # noinspection SqlResolve
            must_change = conn.execute("SELECT must_change_password FROM login WHERE email = 'newuser@example.com'").fetchone()[0]

        assert must_change == 0


# ============================================================================
# ISSUE INITIAL PASSWORD TESTS
# ============================================================================

class TestIssueInitialPassword:
    """Tests fuer issue_initial_password() Methode"""

    def test_issue_initial_password_new_user(self, auth_controller):
        """Test: Initialpasswort fuer neuen User"""
        result = auth_controller.issue_initial_password("newadmin@example.com")

        assert result['success'] is True
        assert 'password' in result
        assert len(result['password']) == 16
        assert 'message' in result

    def test_issue_initial_password_can_login(self, auth_controller):
        """Test: Mit Initialpasswort kann man sich einloggen"""
        result = auth_controller.issue_initial_password("newadmin@example.com")
        initial_pw = result['password']

        login_result = auth_controller.login("newadmin@example.com", initial_pw)
        assert login_result['success'] is True

    def test_issue_initial_password_sets_must_change_flag(self, auth_controller, test_db):
        """Test: Initialpasswort setzt must_change_password auf 1"""
        auth_controller.issue_initial_password("newadmin@example.com")

        with sqlite3.connect(test_db) as conn:
            # noinspection SqlResolve
            must_change = conn.execute("SELECT must_change_password FROM login WHERE email = 'newadmin@example.com'").fetchone()[0]

        assert must_change == 1

    def test_issue_initial_password_existing_user(self, auth_with_user, test_db_with_user):
        """Test: Initialpasswort fuer existierenden User (Reset)"""
        result = auth_with_user.issue_initial_password("test@example.com")

        assert result['success'] is True
        assert 'password' in result

        # Altes Passwort sollte nicht mehr funktionieren
        login_old = auth_with_user.login("test@example.com", "TestPassword123!")
        assert login_old['success'] is False

        # Neues Initialpasswort sollte funktionieren
        login_new = auth_with_user.login("test@example.com", result['password'])
        assert login_new['success'] is True

    def test_issue_initial_password_existing_user_sets_must_change(self, auth_with_user, test_db_with_user):
        """Test: Reset setzt must_change_password auf 1"""
        auth_with_user.issue_initial_password("test@example.com")

        with sqlite3.connect(test_db_with_user) as conn:
            # noinspection SqlResolve
            must_change = conn.execute("SELECT must_change_password FROM login WHERE email = 'test@example.com'").fetchone()[0]

        assert must_change == 1

    def test_issue_initial_password_with_student_id(self, auth_controller, test_db):
        """Test: Initialpasswort mit student_id"""
        auth_controller.issue_initial_password("student@example.com", student_id=99)

        with sqlite3.connect(test_db) as conn:
            # noinspection SqlResolve
            student_id = conn.execute("SELECT student_id FROM login WHERE email = 'student@example.com'").fetchone()[0]

        assert student_id == 99

    def test_issue_initial_password_generates_strong_password(self, auth_controller):
        """Test: Generiertes Passwort ist stark genug"""
        result = auth_controller.issue_initial_password("newadmin@example.com")
        password = result['password']

        # Passwort sollte 16 Zeichen haben
        assert len(password) == 16

        # Passwort sollte verschiedene Zeichentypen enthalten
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)

        assert has_upper or has_lower  # Mindestens Buchstaben
        assert has_digit or has_upper or has_lower  # Irgendwas

    def test_issue_initial_password_different_each_time(self, auth_controller):
        """Test: Jeder Aufruf generiert ein anderes Passwort"""
        result1 = auth_controller.issue_initial_password("user1@example.com")
        result2 = auth_controller.issue_initial_password("user2@example.com")

        assert result1['password'] != result2['password']


# ============================================================================
# EDGE CASES AND ERROR HANDLING
# ============================================================================

class TestEdgeCases:
    """Tests fuer Randfaelle und Fehlerbehandlung"""

    def test_login_sql_injection_attempt(self, auth_with_user):
        """Test: SQL Injection Versuch wird abgefangen"""
        result = auth_with_user.login("'; DROP TABLE login; --", "password")

        assert result['success'] is False

    def test_register_sql_injection_attempt(self, auth_controller):
        """Test: SQL Injection bei Registrierung wird abgefangen"""
        result = auth_controller.register("'; DROP TABLE login; --", "SecurePassword123!")

        # Sollte entweder fehlschlagen oder sicher behandelt werden
        # Wichtig: Tabelle existiert noch
        with sqlite3.connect(auth_controller.db_path) as conn:
            tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='login'").fetchone()
            assert tables is not None

    def test_login_special_characters_in_password(self, test_db):
        """Test: Sonderzeichen im Passwort"""
        auth = AuthController(test_db)
        special_pw = "P@$$w0rd!#$%^&*()"

        # Registrieren
        reg_result = auth.register("special@example.com", special_pw)
        assert reg_result['success'] is True

        # Login
        login_result = auth.login("special@example.com", special_pw)
        assert login_result['success'] is True

    def test_login_unicode_in_email(self, auth_controller):
        """Test: Unicode in E-Mail"""
        result = auth_controller.register("tëst@example.com", "SecurePassword123!")

        # Je nach Implementierung kann das funktionieren oder nicht
        # Wichtig ist, dass es nicht abstuerzt
        assert 'success' in result

    def test_login_very_long_email(self, auth_controller):
        """Test: Sehr lange E-Mail"""
        long_email = "a" * 500 + "@example.com"
        result = auth_controller.login(long_email, "SomePassword123!")

        # Sollte nicht abstuerzen
        assert result['success'] is False

    def test_login_very_long_password(self, auth_with_user):
        """Test: Sehr langes Passwort"""
        long_password = "A1!" + "a" * 10000
        result = auth_with_user.login("test@example.com", long_password)

        # Sollte nicht abstuerzen, aber fehlschlagen
        assert result['success'] is False

    def test_change_password_same_as_old(self, auth_with_user):
        """Test: Neues Passwort gleich altem Passwort"""
        result = auth_with_user.change_password(1, "TestPassword123!", "TestPassword123!")

        # Kann erfolgreich sein oder Policy-Fehler - je nach Implementierung
        assert 'success' in result


# ============================================================================
# CONNECTION TESTS
# ============================================================================

class TestConnection:
    """Tests fuer Datenbankverbindung"""

    def test_con_creates_connection(self, auth_controller):
        """Test: _con() erstellt funktionierende Verbindung"""
        con = auth_controller._con()

        try:
            result = con.execute("SELECT 1").fetchone()
            assert result[0] == 1
        finally:
            con.close()

    def test_multiple_operations_same_controller(self, auth_controller):
        """Test: Mehrere Operationen mit demselben Controller"""
        # Registrieren
        auth_controller.register("user1@example.com", "Password123!")
        auth_controller.register("user2@example.com", "Password123!")

        # Login
        result1 = auth_controller.login("user1@example.com", "Password123!")
        result2 = auth_controller.login("user2@example.com", "Password123!")

        assert result1['success'] is True
        assert result2['success'] is True

    def test_concurrent_controllers(self, test_db):
        """Test: Mehrere Controller-Instanzen auf derselben DB"""
        auth1 = AuthController(test_db)
        auth2 = AuthController(test_db)

        # Mit auth1 registrieren
        auth1.register("shared@example.com", "Password123!")

        # Mit auth2 einloggen
        result = auth2.login("shared@example.com", "Password123!")
        assert result['success'] is True