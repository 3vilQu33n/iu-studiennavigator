# tests/unit/test_login_model.py
"""
Unit Tests fuer Login Domain Model (models/login.py)

Testet das Login-Modell:
- Initialisierung und Validierung
- Passwort-Hashing und Verifikation (Argon2)
- Email-Normalisierung
- Status-Methoden
- Serialisierung

HINWEIS: Dies testet models/login.py, NICHT controllers/login.py!
"""
from __future__ import annotations

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch

# Mark this whole module as unit tests
pytestmark = pytest.mark.unit


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def login_class():
    """Importiert Login-Klasse"""
    try:
        from models.login import Login
        return Login
    except ImportError:
        from models import Login
        return Login


@pytest.fixture
def create_login_func():
    """Importiert create_login_for_student Funktion"""
    try:
        from models.login import create_login_for_student
        return create_login_for_student
    except ImportError:
        from models import create_login_for_student
        return create_login_for_student


@pytest.fixture
def valid_password_hash(login_class):
    """Generiert gueltigen Argon2 Password Hash"""
    return login_class.hash_password("TestPassword123!")


@pytest.fixture
def sample_login(login_class, valid_password_hash):
    """Standard-Login fuer Tests"""
    return login_class(
        id=1,
        student_id=100,
        email="test@example.com",
        password_hash=valid_password_hash,
        is_active=1,
        role="student",
        created_at="2025-01-01T10:00:00",
        must_change_password=0,
        last_login=None
    )


@pytest.fixture
def admin_login(login_class, valid_password_hash):
    """Admin-Login fuer Tests"""
    return login_class(
        id=2,
        student_id=200,
        email="admin@example.com",
        password_hash=valid_password_hash,
        is_active=1,
        role="admin",
        created_at="2025-01-01T10:00:00",
        must_change_password=0,
        last_login="2025-06-01T12:00:00"
    )


@pytest.fixture
def inactive_login(login_class, valid_password_hash):
    """Deaktivierter Login fuer Tests"""
    return login_class(
        id=3,
        student_id=300,
        email="inactive@example.com",
        password_hash=valid_password_hash,
        is_active=0,
        role="student"
    )


# ============================================================================
# INITIALIZATION TESTS
# ============================================================================

class TestLoginInit:
    """Tests fuer Login-Initialisierung"""

    def test_init_with_all_fields(self, login_class, valid_password_hash):
        """Initialisierung mit allen Feldern"""
        login = login_class(
            id=1,
            student_id=100,
            email="test@example.com",
            password_hash=valid_password_hash,
            is_active=1,
            role="student",
            created_at="2025-01-01T10:00:00",
            must_change_password=0,
            last_login="2025-06-01T12:00:00"
        )

        assert login.id == 1
        assert login.student_id == 100
        assert login.email == "test@example.com"
        assert login.is_active == 1
        assert login.role == "student"
        assert login.must_change_password == 0
        assert login.last_login == "2025-06-01T12:00:00"

    def test_init_without_id(self, login_class, valid_password_hash):
        """Initialisierung ohne ID (fuer neue Eintraege)"""
        login = login_class(
            id=None,
            student_id=100,
            email="new@example.com",
            password_hash=valid_password_hash
        )

        assert login.id is None

    def test_init_default_is_active(self, login_class, valid_password_hash):
        """is_active ist standardmaessig 1"""
        login = login_class(
            id=None,
            student_id=100,
            email="test@example.com",
            password_hash=valid_password_hash
        )

        assert login.is_active == 1

    def test_init_default_role(self, login_class, valid_password_hash):
        """role ist standardmaessig 'student'"""
        login = login_class(
            id=None,
            student_id=100,
            email="test@example.com",
            password_hash=valid_password_hash
        )

        assert login.role == "student"

    def test_init_default_must_change_password(self, login_class, valid_password_hash):
        """must_change_password ist standardmaessig 0"""
        login = login_class(
            id=None,
            student_id=100,
            email="test@example.com",
            password_hash=valid_password_hash
        )

        assert login.must_change_password == 0

    def test_init_created_at_auto_set(self, login_class, valid_password_hash):
        """created_at wird automatisch gesetzt wenn None"""
        login = login_class(
            id=None,
            student_id=100,
            email="test@example.com",
            password_hash=valid_password_hash,
            created_at=None
        )

        assert login.created_at is not None
        # Sollte ein ISO-Format Datum sein
        datetime.fromisoformat(login.created_at)


# ============================================================================
# EMAIL NORMALIZATION TESTS
# ============================================================================

class TestEmailNormalization:
    """Tests fuer Email-Normalisierung in __post_init__"""

    def test_email_lowercase(self, login_class, valid_password_hash):
        """Email wird zu Kleinbuchstaben konvertiert"""
        login = login_class(
            id=None,
            student_id=100,
            email="TEST@EXAMPLE.COM",
            password_hash=valid_password_hash
        )

        assert login.email == "test@example.com"

    def test_email_stripped(self, login_class, valid_password_hash):
        """Whitespace wird von Email entfernt"""
        login = login_class(
            id=None,
            student_id=100,
            email="  test@example.com  ",
            password_hash=valid_password_hash
        )

        assert login.email == "test@example.com"

    def test_email_mixed_case_and_spaces(self, login_class, valid_password_hash):
        """Email mit gemischter Schreibweise und Spaces"""
        login = login_class(
            id=None,
            student_id=100,
            email="  TeSt@ExAmPlE.CoM  ",
            password_hash=valid_password_hash
        )

        assert login.email == "test@example.com"


# ============================================================================
# VALIDATION TESTS
# ============================================================================

class TestValidation:
    """Tests fuer validate() Methode"""

    def test_validate_valid_login(self, sample_login):
        """Gueltige Login-Daten werfen keine Exception"""
        # Sollte nicht werfen
        sample_login.validate()

    def test_validate_missing_student_id(self, login_class, valid_password_hash):
        """Fehlende student_id wirft ValueError"""
        with pytest.raises(ValueError, match="student_id"):
            login_class(
                id=None,
                student_id=0,  # Ungueltig
                email="test@example.com",
                password_hash=valid_password_hash
            )

    def test_validate_negative_student_id(self, login_class, valid_password_hash):
        """Negative student_id wirft ValueError"""
        with pytest.raises(ValueError, match="student_id"):
            login_class(
                id=None,
                student_id=-1,
                email="test@example.com",
                password_hash=valid_password_hash
            )

    def test_validate_invalid_email_no_at(self, login_class, valid_password_hash):
        """Email ohne @ wirft ValueError"""
        with pytest.raises(ValueError, match="E-Mail"):
            login_class(
                id=None,
                student_id=100,
                email="invalid-email",
                password_hash=valid_password_hash
            )

    def test_validate_invalid_email_no_domain(self, login_class, valid_password_hash):
        """Email ohne Domain wirft ValueError"""
        with pytest.raises(ValueError, match="E-Mail"):
            login_class(
                id=None,
                student_id=100,
                email="test@",
                password_hash=valid_password_hash
            )

    def test_validate_invalid_email_no_dot_in_domain(self, login_class, valid_password_hash):
        """Email ohne Punkt in Domain wirft ValueError"""
        with pytest.raises(ValueError, match="E-Mail"):
            login_class(
                id=None,
                student_id=100,
                email="test@example",
                password_hash=valid_password_hash
            )

    def test_validate_short_password_hash(self, login_class):
        """Zu kurzer password_hash wirft ValueError"""
        with pytest.raises(ValueError, match="password_hash"):
            login_class(
                id=None,
                student_id=100,
                email="test@example.com",
                password_hash="tooshort"
            )

    def test_validate_invalid_role(self, login_class, valid_password_hash):
        """Ungueltige role wirft ValueError"""
        with pytest.raises(ValueError, match="role"):
            login_class(
                id=None,
                student_id=100,
                email="test@example.com",
                password_hash=valid_password_hash,
                role="superuser"  # Ungueltig
            )

    def test_validate_role_student(self, login_class, valid_password_hash):
        """Role 'student' ist gueltig"""
        login = login_class(
            id=None,
            student_id=100,
            email="test@example.com",
            password_hash=valid_password_hash,
            role="student"
        )
        assert login.role == "student"

    def test_validate_role_admin(self, login_class, valid_password_hash):
        """Role 'admin' ist gueltig"""
        login = login_class(
            id=None,
            student_id=100,
            email="test@example.com",
            password_hash=valid_password_hash,
            role="admin"
        )
        assert login.role == "admin"


# ============================================================================
# PASSWORD HASHING TESTS
# ============================================================================

class TestPasswordHashing:
    """Tests fuer Passwort-Hashing"""

    def test_hash_password_returns_string(self, login_class):
        """hash_password() gibt String zurueck"""
        hash_result = login_class.hash_password("TestPassword123!")

        assert isinstance(hash_result, str)

    def test_hash_password_is_argon2(self, login_class):
        """hash_password() erzeugt Argon2 Hash"""
        hash_result = login_class.hash_password("TestPassword123!")

        assert hash_result.startswith("$argon2")

    def test_hash_password_different_for_same_password(self, login_class):
        """Gleiche Passwoerter erzeugen unterschiedliche Hashes (Salt)"""
        hash1 = login_class.hash_password("TestPassword123!")
        hash2 = login_class.hash_password("TestPassword123!")

        # Wegen Salt sollten die Hashes unterschiedlich sein
        assert hash1 != hash2

    def test_hash_password_different_for_different_passwords(self, login_class):
        """Unterschiedliche Passwoerter erzeugen unterschiedliche Hashes"""
        hash1 = login_class.hash_password("Password1")
        hash2 = login_class.hash_password("Password2")

        assert hash1 != hash2


# ============================================================================
# PASSWORD VERIFICATION TESTS
# ============================================================================

class TestPasswordVerification:
    """Tests fuer verify_password() Methode"""

    def test_verify_password_correct(self, login_class):
        """Korrektes Passwort wird verifiziert"""
        password = "TestPassword123!"
        hash_val = login_class.hash_password(password)

        login = login_class(
            id=1,
            student_id=100,
            email="test@example.com",
            password_hash=hash_val
        )

        assert login.verify_password(password) is True

    def test_verify_password_incorrect(self, login_class):
        """Falsches Passwort wird abgelehnt"""
        hash_val = login_class.hash_password("CorrectPassword")

        login = login_class(
            id=1,
            student_id=100,
            email="test@example.com",
            password_hash=hash_val
        )

        assert login.verify_password("WrongPassword") is False

    def test_verify_password_empty(self, sample_login):
        """Leeres Passwort wird abgelehnt"""
        assert sample_login.verify_password("") is False

    def test_verify_password_case_sensitive(self, login_class):
        """Passwort-Verifikation ist case-sensitive"""
        password = "TestPassword"
        hash_val = login_class.hash_password(password)

        login = login_class(
            id=1,
            student_id=100,
            email="test@example.com",
            password_hash=hash_val
        )

        assert login.verify_password("testpassword") is False
        assert login.verify_password("TESTPASSWORD") is False
        assert login.verify_password("TestPassword") is True


# ============================================================================
# STATUS METHODS TESTS
# ============================================================================

class TestStatusMethods:
    """Tests fuer Status-Methoden"""

    def test_is_active_account_true(self, sample_login):
        """is_active_account() ist True wenn is_active=1"""
        assert sample_login.is_active == 1
        assert sample_login.is_active_account() is True

    def test_is_active_account_false(self, inactive_login):
        """is_active_account() ist False wenn is_active=0"""
        assert inactive_login.is_active == 0
        assert inactive_login.is_active_account() is False

    def test_needs_password_change_false(self, sample_login):
        """needs_password_change() ist False wenn must_change_password=0"""
        assert sample_login.must_change_password == 0
        assert sample_login.needs_password_change() is False

    def test_needs_password_change_true(self, login_class, valid_password_hash):
        """needs_password_change() ist True wenn must_change_password=1"""
        login = login_class(
            id=1,
            student_id=100,
            email="test@example.com",
            password_hash=valid_password_hash,
            must_change_password=1
        )

        assert login.needs_password_change() is True

    def test_is_admin_true(self, admin_login):
        """is_admin() ist True fuer Admin-Role"""
        assert admin_login.role == "admin"
        assert admin_login.is_admin() is True

    def test_is_admin_false(self, sample_login):
        """is_admin() ist False fuer Student-Role"""
        assert sample_login.role == "student"
        assert sample_login.is_admin() is False

    def test_is_student_true(self, sample_login):
        """is_student() ist True fuer Student-Role"""
        assert sample_login.role == "student"
        assert sample_login.is_student() is True

    def test_is_student_false(self, admin_login):
        """is_student() ist False fuer Admin-Role"""
        assert admin_login.role == "admin"
        assert admin_login.is_student() is False


# ============================================================================
# UPDATE_LAST_LOGIN TESTS
# ============================================================================

class TestUpdateLastLogin:
    """Tests fuer update_last_login() Methode"""

    def test_update_last_login_sets_timestamp(self, sample_login):
        """update_last_login() setzt Timestamp"""
        assert sample_login.last_login is None

        sample_login.update_last_login()

        assert sample_login.last_login is not None

    def test_update_last_login_is_iso_format(self, sample_login):
        """update_last_login() setzt ISO-Format Timestamp"""
        sample_login.update_last_login()

        # Sollte parsebar sein
        parsed = datetime.fromisoformat(sample_login.last_login)
        assert isinstance(parsed, datetime)

    def test_update_last_login_overwrites_existing(self, admin_login):
        """update_last_login() ueberschreibt existierenden Wert"""
        old_login = admin_login.last_login
        assert old_login is not None

        admin_login.update_last_login()

        assert admin_login.last_login != old_login


# ============================================================================
# TO_DICT TESTS
# ============================================================================

class TestToDict:
    """Tests fuer to_dict() Methode"""

    def test_to_dict_contains_all_fields(self, sample_login):
        """to_dict() enthaelt alle Felder"""
        d = sample_login.to_dict()

        assert 'id' in d
        assert 'student_id' in d
        assert 'email' in d
        assert 'is_active' in d
        assert 'role' in d
        assert 'created_at' in d
        assert 'must_change_password' in d
        assert 'last_login' in d

    def test_to_dict_excludes_password_hash(self, sample_login):
        """to_dict() enthaelt NICHT password_hash (Sicherheit!)"""
        d = sample_login.to_dict()

        assert 'password_hash' not in d

    def test_to_dict_is_active_is_bool(self, sample_login):
        """is_active ist bool in dict"""
        d = sample_login.to_dict()

        assert isinstance(d['is_active'], bool)

    def test_to_dict_must_change_password_is_bool(self, sample_login):
        """must_change_password ist bool in dict"""
        d = sample_login.to_dict()

        assert isinstance(d['must_change_password'], bool)

    def test_to_dict_contains_computed_fields(self, sample_login):
        """to_dict() enthaelt berechnete Felder"""
        d = sample_login.to_dict()

        assert 'needs_password_change' in d
        assert 'is_admin' in d

    def test_to_dict_is_json_serializable(self, sample_login):
        """to_dict() Ergebnis ist JSON-serialisierbar"""
        import json

        d = sample_login.to_dict()

        # Sollte nicht werfen
        json_str = json.dumps(d)
        assert isinstance(json_str, str)


# ============================================================================
# FROM_DB_ROW TESTS
# ============================================================================

class TestFromDbRow:
    """Tests fuer from_db_row() Factory Method"""

    def test_from_db_row_dict(self, login_class, valid_password_hash):
        """from_db_row() funktioniert mit dict"""
        row = {
            'id': 1,
            'student_id': 100,
            'email': 'test@example.com',
            'password_hash': valid_password_hash,
            'is_active': 1,
            'role': 'student',
            'created_at': '2025-01-01T10:00:00',
            'must_change_password': 0,
            'last_login': None
        }

        login = login_class.from_db_row(row)

        assert login.id == 1
        assert login.student_id == 100
        assert login.email == 'test@example.com'
        assert login.is_active == 1
        assert login.role == 'student'

    def test_from_db_row_missing_optional_fields(self, login_class, valid_password_hash):
        """from_db_row() behandelt fehlende optionale Felder"""
        row = {
            'id': 1,
            'student_id': 100,
            'email': 'test@example.com',
            'password_hash': valid_password_hash
            # Keine optionalen Felder
        }

        login = login_class.from_db_row(row)

        assert login.id == 1
        assert login.is_active == 1  # Default
        assert login.role == 'student'  # Default

    def test_from_db_row_sqlite_row_mock(self, login_class, valid_password_hash):
        """from_db_row() funktioniert mit sqlite3.Row-aehnlichem Objekt"""
        data = {
            'id': 2,
            'student_id': 200,
            'email': 'admin@example.com',
            'password_hash': valid_password_hash,
            'is_active': 1,
            'role': 'admin',
            'created_at': '2025-01-01T10:00:00',
            'must_change_password': 1,
            'last_login': '2025-06-01T12:00:00'
        }

        mock_row = MagicMock()
        mock_row.__getitem__ = lambda self, key: data[key]

        login = login_class.from_db_row(mock_row)

        assert login.id == 2
        assert login.role == 'admin'
        assert login.must_change_password == 1

    def test_from_db_row_id_none(self, login_class, valid_password_hash):
        """from_db_row() behandelt None ID"""
        row = {
            'id': None,
            'student_id': 100,
            'email': 'test@example.com',
            'password_hash': valid_password_hash,
            'is_active': 1,
            'role': 'student',
            'created_at': None,
            'must_change_password': 0,
            'last_login': None
        }

        login = login_class.from_db_row(row)

        assert login.id is None


# ============================================================================
# CREATE_LOGIN_FOR_STUDENT TESTS
# ============================================================================

class TestCreateLoginForStudent:
    """Tests fuer create_login_for_student() Helper Function"""

    def test_creates_login_object(self, create_login_func):
        """create_login_for_student() erstellt Login Objekt"""
        login = create_login_func(
            student_id=100,
            email="test@example.com",
            password="TestPassword123!"
        )

        try:
            from models.login import Login
        except ImportError:
            from models import Login

        assert isinstance(login, Login)

    def test_hashes_password(self, create_login_func):
        """create_login_for_student() hasht Passwort"""
        login = create_login_func(
            student_id=100,
            email="test@example.com",
            password="TestPassword123!"
        )

        # Hash sollte Argon2 Format haben
        assert login.password_hash.startswith("$argon2")

    def test_password_verifiable(self, create_login_func):
        """Erstellter Login kann Passwort verifizieren"""
        password = "TestPassword123!"
        login = create_login_func(
            student_id=100,
            email="test@example.com",
            password=password
        )

        assert login.verify_password(password) is True

    def test_default_role_student(self, create_login_func):
        """Standard-Role ist 'student'"""
        login = create_login_func(
            student_id=100,
            email="test@example.com",
            password="TestPassword123!"
        )

        assert login.role == "student"

    def test_custom_role(self, create_login_func):
        """Benutzerdefinierte Role wird gesetzt"""
        login = create_login_func(
            student_id=100,
            email="admin@example.com",
            password="AdminPassword123!",
            role="admin"
        )

        assert login.role == "admin"

    def test_id_is_none(self, create_login_func):
        """ID ist None (noch nicht in DB)"""
        login = create_login_func(
            student_id=100,
            email="test@example.com",
            password="TestPassword123!"
        )

        assert login.id is None

    def test_is_active_true(self, create_login_func):
        """is_active ist 1"""
        login = create_login_func(
            student_id=100,
            email="test@example.com",
            password="TestPassword123!"
        )

        assert login.is_active == 1
        assert login.is_active_account() is True

    def test_must_change_password_false(self, create_login_func):
        """must_change_password ist 0"""
        login = create_login_func(
            student_id=100,
            email="test@example.com",
            password="TestPassword123!"
        )

        assert login.must_change_password == 0

    def test_last_login_none(self, create_login_func):
        """last_login ist None"""
        login = create_login_func(
            student_id=100,
            email="test@example.com",
            password="TestPassword123!"
        )

        assert login.last_login is None

    def test_created_at_set(self, create_login_func):
        """created_at wird gesetzt"""
        login = create_login_func(
            student_id=100,
            email="test@example.com",
            password="TestPassword123!"
        )

        assert login.created_at is not None


# ============================================================================
# STRING REPRESENTATION TESTS
# ============================================================================

class TestStringRepresentation:
    """Tests fuer __str__ und __repr__"""

    def test_str_contains_email(self, sample_login):
        """__str__ enthaelt Email"""
        s = str(sample_login)
        assert "test@example.com" in s

    def test_str_contains_status(self, sample_login):
        """__str__ enthaelt Status"""
        s = str(sample_login)
        assert "aktiv" in s.lower() or "active" in s.lower()

    def test_str_inactive_shows_deaktiviert(self, inactive_login):
        """__str__ zeigt 'deaktiviert' fuer inaktiven Login"""
        s = str(inactive_login)
        assert "deaktiviert" in s.lower() or "inactive" in s.lower()

    def test_repr_contains_class_name(self, sample_login):
        """__repr__ enthaelt Klassennamen"""
        r = repr(sample_login)
        assert "Login" in r

    def test_repr_contains_id(self, sample_login):
        """__repr__ enthaelt ID"""
        r = repr(sample_login)
        assert "id=1" in r

    def test_repr_contains_student_id(self, sample_login):
        """__repr__ enthaelt student_id"""
        r = repr(sample_login)
        assert "student_id=100" in r

    def test_repr_contains_email(self, sample_login):
        """__repr__ enthaelt Email"""
        r = repr(sample_login)
        assert "test@example.com" in r

    def test_repr_contains_role(self, sample_login):
        """__repr__ enthaelt Role"""
        r = repr(sample_login)
        assert "role='student'" in r


# ============================================================================
# EDGE CASES
# ============================================================================

class TestEdgeCases:
    """Tests fuer Randfaelle"""

    def test_very_long_email(self, login_class, valid_password_hash):
        """Sehr lange Email wird behandelt"""
        long_local = "a" * 100
        email = f"{long_local}@example.com"

        login = login_class(
            id=None,
            student_id=100,
            email=email,
            password_hash=valid_password_hash
        )

        assert login.email == email.lower()

    def test_unicode_in_password(self, login_class):
        """Unicode in Passwort wird behandelt"""
        password = "Passwörtñ123!日本語"
        hash_val = login_class.hash_password(password)

        login = login_class(
            id=None,
            student_id=100,
            email="test@example.com",
            password_hash=hash_val
        )

        assert login.verify_password(password) is True

    def test_special_chars_in_email_local(self, login_class, valid_password_hash):
        """Sonderzeichen im Email Local-Part"""
        login = login_class(
            id=None,
            student_id=100,
            email="test.user+tag@example.com",
            password_hash=valid_password_hash
        )

        assert login.email == "test.user+tag@example.com"

    def test_dataclass_equality(self, login_class, valid_password_hash):
        """Dataclass Gleichheit basiert auf Feldern"""
        login1 = login_class(
            id=1,
            student_id=100,
            email="test@example.com",
            password_hash=valid_password_hash,
            is_active=1,
            role="student",
            created_at="2025-01-01T10:00:00",
            must_change_password=0,
            last_login=None
        )

        login2 = login_class(
            id=1,
            student_id=100,
            email="test@example.com",
            password_hash=valid_password_hash,
            is_active=1,
            role="student",
            created_at="2025-01-01T10:00:00",
            must_change_password=0,
            last_login=None
        )

        assert login1 == login2

    def test_dataclass_inequality(self, login_class, valid_password_hash):
        """Unterschiedliche IDs bedeuten Ungleichheit"""
        login1 = login_class(
            id=1,
            student_id=100,
            email="test@example.com",
            password_hash=valid_password_hash
        )

        login2 = login_class(
            id=2,
            student_id=100,
            email="test@example.com",
            password_hash=valid_password_hash
        )

        assert login1 != login2

    def test_subdomain_email(self, login_class, valid_password_hash):
        """Email mit Subdomain funktioniert"""
        login = login_class(
            id=None,
            student_id=100,
            email="user@mail.example.com",
            password_hash=valid_password_hash
        )

        assert login.email == "user@mail.example.com"


# ============================================================================
# COMPOSITION RELATIONSHIP TESTS
# ============================================================================

class TestCompositionRelationship:
    """Tests fuer KOMPOSITION zu Student"""

    def test_student_id_required(self, login_class, valid_password_hash):
        """student_id ist erforderlich (KOMPOSITION)"""
        with pytest.raises(ValueError, match="student_id"):
            login_class(
                id=None,
                student_id=0,
                email="test@example.com",
                password_hash=valid_password_hash
            )

    def test_student_id_must_be_positive(self, login_class, valid_password_hash):
        """student_id muss positiv sein"""
        with pytest.raises(ValueError, match="student_id"):
            login_class(
                id=None,
                student_id=-100,
                email="test@example.com",
                password_hash=valid_password_hash
            )

    def test_login_belongs_to_student(self, sample_login):
        """Login gehoert zu einem Student"""
        assert sample_login.student_id > 0


# ============================================================================
# SECURITY TESTS
# ============================================================================

class TestSecurity:
    """Tests fuer Sicherheitsaspekte"""

    def test_password_hash_not_in_to_dict(self, sample_login):
        """password_hash wird nicht in to_dict() exponiert"""
        d = sample_login.to_dict()
        assert 'password_hash' not in d

    def test_password_hash_not_in_str(self, sample_login):
        """password_hash erscheint nicht in __str__"""
        s = str(sample_login)
        assert "$argon2" not in s
        assert sample_login.password_hash not in s

    def test_password_hash_not_in_repr(self, sample_login):
        """password_hash erscheint nicht in __repr__"""
        r = repr(sample_login)
        assert "$argon2" not in r
        assert sample_login.password_hash not in r

    def test_argon2_hash_format(self, login_class):
        """Argon2 Hash hat korrektes Format"""
        hash_val = login_class.hash_password("TestPassword")

        # Argon2id Format pruefen
        assert hash_val.startswith("$argon2")
        parts = hash_val.split("$")
        assert len(parts) >= 5