# tests/unit/test_utils_login.py
"""
Unit Tests fuer utils/login.py

Testet:
- User-Klasse (Flask-Login Integration)
  - __init__() - Initialisierung
  - get() - User aus DB laden
  - get_by_email() - User per Email laden
  - get_id() - ID fuer Flask-Login
  - __normalize_email() - Email-Normalisierung
  - __repr__(), __str__() - String-Repräsentationen

- Passwort-Policy
  - password_meets_policy() - Anforderungen pruefen
  - PASSWORD_MIN_LENGTH Konstante

- Passwort-Generator
  - generate_strong_password() - Sicheres Passwort generieren

- Email-Validierung
  - validate_email() - Email-Format pruefen
"""
from __future__ import annotations

import pytest
import sqlite3
import tempfile
import os
import re
from pathlib import Path

# Mark this whole module as unit tests
pytestmark = pytest.mark.unit


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def login_module():
    """Importiert das login-Modul aus utils"""
    try:
        from utils.login import (
            User, password_meets_policy, generate_strong_password,
            validate_email, PASSWORD_MIN_LENGTH
        )
        return {
            'User': User,
            'password_meets_policy': password_meets_policy,
            'generate_strong_password': generate_strong_password,
            'validate_email': validate_email,
            'PASSWORD_MIN_LENGTH': PASSWORD_MIN_LENGTH
        }
    except ImportError:
        from utils import (
            User, password_meets_policy, generate_strong_password,
            validate_email, PASSWORD_MIN_LENGTH
        )
        return {
            'User': User,
            'password_meets_policy': password_meets_policy,
            'generate_strong_password': generate_strong_password,
            'validate_email': validate_email,
            'PASSWORD_MIN_LENGTH': PASSWORD_MIN_LENGTH
        }


@pytest.fixture
def user_class(login_module):
    """Gibt User-Klasse zurueck"""
    return login_module['User']


@pytest.fixture
def password_meets_policy_func(login_module):
    """Gibt password_meets_policy Funktion zurueck"""
    return login_module['password_meets_policy']


@pytest.fixture
def generate_strong_password_func(login_module):
    """Gibt generate_strong_password Funktion zurueck"""
    return login_module['generate_strong_password']


@pytest.fixture
def validate_email_func(login_module):
    """Gibt validate_email Funktion zurueck"""
    return login_module['validate_email']


@pytest.fixture
def password_min_length(login_module):
    """Gibt PASSWORD_MIN_LENGTH zurueck"""
    return login_module['PASSWORD_MIN_LENGTH']


@pytest.fixture
def temp_db():
    """Erstellt temporaere Test-Datenbank mit login-Tabelle"""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)

    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON;")

    conn.executescript("""
        CREATE TABLE IF NOT EXISTS login (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            passwort_hash TEXT NOT NULL
        );

        INSERT INTO login (id, email, passwort_hash) VALUES
            (1, 'max.mustermann@example.com', 'hash1'),
            (2, 'Erika.Musterfrau@EXAMPLE.COM', 'hash2'),
            (3, 'test@domain.org', 'hash3');
    """)
    conn.commit()
    conn.close()

    yield path

    # Cleanup
    try:
        os.unlink(path)
    except OSError:
        pass


# ============================================================================
# USER CLASS TESTS
# ============================================================================

class TestUserInit:
    """Tests fuer User.__init__()"""

    def test_init_with_id_and_email(self, user_class):
        """User kann mit id und email initialisiert werden"""
        user = user_class(id=1, email='test@example.com')

        assert user.id == 1
        assert user.email == 'test@example.com'

    def test_init_normalizes_email_lowercase(self, user_class):
        """User normalisiert Email zu lowercase"""
        user = user_class(id=1, email='TEST@EXAMPLE.COM')

        assert user.email == 'test@example.com'

    def test_init_normalizes_email_strips_whitespace(self, user_class):
        """User entfernt Whitespace von Email"""
        user = user_class(id=1, email='  test@example.com  ')

        assert user.email == 'test@example.com'

    def test_init_handles_non_string_email(self, user_class):
        """User behandelt non-string Email gracefully"""
        user = user_class(id=1, email=None)

        assert user.email == ''


class TestUserGet:
    """Tests fuer User.get() statische Methode"""

    def test_get_existing_user(self, user_class, temp_db):
        """get() laedt existierenden User"""
        user = user_class.get(1, temp_db)

        assert user is not None
        assert user.id == 1
        assert user.email == 'max.mustermann@example.com'

    def test_get_returns_user_instance(self, user_class, temp_db):
        """get() gibt User-Instanz zurueck"""
        user = user_class.get(1, temp_db)

        assert isinstance(user, user_class)

    def test_get_nonexistent_user(self, user_class, temp_db):
        """get() gibt None fuer nicht existierenden User"""
        user = user_class.get(999, temp_db)

        assert user is None

    def test_get_invalid_db_path(self, user_class):
        """get() gibt None bei ungueltigem DB-Pfad"""
        user = user_class.get(1, '/nonexistent/path.db')

        assert user is None

    def test_get_normalizes_email(self, user_class, temp_db):
        """get() normalisiert geladene Email"""
        # User 2 hat uppercase Email in DB
        user = user_class.get(2, temp_db)

        assert user.email == 'erika.musterfrau@example.com'


class TestUserGetByEmail:
    """Tests fuer User.get_by_email() statische Methode"""

    def test_get_by_email_existing(self, user_class, temp_db):
        """get_by_email() laedt User per Email"""
        user = user_class.get_by_email('max.mustermann@example.com', temp_db)

        assert user is not None
        assert user.id == 1

    def test_get_by_email_case_insensitive(self, user_class, temp_db):
        """get_by_email() ist case-insensitive"""
        user = user_class.get_by_email('MAX.MUSTERMANN@EXAMPLE.COM', temp_db)

        assert user is not None
        assert user.id == 1

    def test_get_by_email_nonexistent(self, user_class, temp_db):
        """get_by_email() gibt None fuer nicht existierende Email"""
        user = user_class.get_by_email('unknown@example.com', temp_db)

        assert user is None

    def test_get_by_email_invalid_db_path(self, user_class):
        """get_by_email() gibt None bei ungueltigem DB-Pfad"""
        user = user_class.get_by_email('test@example.com', '/nonexistent/path.db')

        assert user is None


class TestUserGetId:
    """Tests fuer User.get_id() (Flask-Login)"""

    def test_get_id_returns_string(self, user_class):
        """get_id() gibt String zurueck"""
        user = user_class(id=42, email='test@example.com')

        result = user.get_id()

        assert isinstance(result, str)

    def test_get_id_correct_value(self, user_class):
        """get_id() gibt korrekte ID zurueck"""
        user = user_class(id=123, email='test@example.com')

        assert user.get_id() == '123'


class TestUserStringMethods:
    """Tests fuer User.__repr__() und __str__()"""

    def test_repr_format(self, user_class):
        """__repr__() hat korrektes Format"""
        user = user_class(id=1, email='test@example.com')

        result = repr(user)

        assert 'User' in result
        assert 'id=1' in result
        assert 'test@example.com' in result

    def test_str_returns_email(self, user_class):
        """__str__() gibt Email zurueck"""
        user = user_class(id=1, email='test@example.com')

        result = str(user)

        assert result == 'test@example.com'


class TestUserMixin:
    """Tests fuer Flask-Login UserMixin Integration"""

    def test_user_is_authenticated(self, user_class):
        """User.is_authenticated ist True (von UserMixin)"""
        user = user_class(id=1, email='test@example.com')

        assert user.is_authenticated is True

    def test_user_is_active(self, user_class):
        """User.is_active ist True (von UserMixin)"""
        user = user_class(id=1, email='test@example.com')

        assert user.is_active is True

    def test_user_is_anonymous(self, user_class):
        """User.is_anonymous ist False (von UserMixin)"""
        user = user_class(id=1, email='test@example.com')

        assert user.is_anonymous is False


# ============================================================================
# PASSWORD POLICY TESTS
# ============================================================================

class TestPasswordMeetsPolicy:
    """Tests fuer password_meets_policy() Funktion"""

    def test_valid_password(self, password_meets_policy_func):
        """Gueltiges Passwort wird akzeptiert"""
        valid, msg = password_meets_policy_func('SecurePass123!')

        assert valid is True
        assert msg == ''

    def test_too_short(self, password_meets_policy_func, password_min_length):
        """Zu kurzes Passwort wird abgelehnt"""
        short_pw = 'Ab1!' + 'x' * (password_min_length - 5)  # Zu kurz

        valid, msg = password_meets_policy_func(short_pw)

        assert valid is False
        assert 'Zeichen' in msg

    def test_missing_lowercase(self, password_meets_policy_func):
        """Passwort ohne Kleinbuchstabe wird abgelehnt"""
        valid, msg = password_meets_policy_func('SECUREPASS123!')

        assert valid is False
        assert 'Kleinbuchstabe' in msg

    def test_missing_uppercase(self, password_meets_policy_func):
        """Passwort ohne Grossbuchstabe wird abgelehnt"""
        valid, msg = password_meets_policy_func('securepass123!')

        assert valid is False
        assert 'Großbuchstabe' in msg or 'GroÃŸbuchstabe' in msg

    def test_missing_digit(self, password_meets_policy_func):
        """Passwort ohne Ziffer wird abgelehnt"""
        valid, msg = password_meets_policy_func('SecurePassword!')

        assert valid is False
        assert 'Ziffer' in msg

    def test_missing_special_char(self, password_meets_policy_func):
        """Passwort ohne Sonderzeichen wird abgelehnt"""
        valid, msg = password_meets_policy_func('SecurePassword123')

        assert valid is False
        assert 'Sonderzeichen' in msg

    def test_multiple_missing_requirements(self, password_meets_policy_func):
        """Mehrere fehlende Anforderungen werden gemeldet"""
        valid, msg = password_meets_policy_func('abc')  # Zu kurz, keine Grossbuchstaben, keine Ziffern, keine Sonderzeichen

        assert valid is False
        # Sollte mehrere Probleme melden
        assert msg.count(',') >= 1 or 'nicht erfüllt' in msg or 'nicht erfÃ¼llt' in msg

    def test_invalid_type(self, password_meets_policy_func):
        """Nicht-String wird abgelehnt"""
        valid, msg = password_meets_policy_func(12345)

        assert valid is False

    def test_none_password(self, password_meets_policy_func):
        """None wird abgelehnt"""
        valid, msg = password_meets_policy_func(None)

        assert valid is False

    def test_exact_minimum_length(self, password_meets_policy_func, password_min_length):
        """Passwort mit exakter Mindestlaenge wird akzeptiert"""
        # Erstelle Passwort mit exakter Mindestlaenge
        pw = 'Aa1!' + 'x' * (password_min_length - 4)

        valid, msg = password_meets_policy_func(pw)

        assert valid is True


# ============================================================================
# PASSWORD GENERATOR TESTS
# ============================================================================

class TestGenerateStrongPassword:
    """Tests fuer generate_strong_password() Funktion"""

    def test_default_length(self, generate_strong_password_func):
        """Generiert Passwort mit Default-Laenge 16"""
        pw = generate_strong_password_func()

        assert len(pw) == 16

    def test_custom_length(self, generate_strong_password_func):
        """Generiert Passwort mit angegebener Laenge"""
        pw = generate_strong_password_func(length=20)

        assert len(pw) == 20

    def test_minimum_length_enforced(self, generate_strong_password_func, password_min_length):
        """Mindestlaenge wird erzwungen"""
        pw = generate_strong_password_func(length=5)  # Zu kurz

        assert len(pw) >= password_min_length

    def test_meets_policy(self, generate_strong_password_func, password_meets_policy_func):
        """Generiertes Passwort erfuellt Policy"""
        for _ in range(10):  # Mehrfach testen
            pw = generate_strong_password_func()
            valid, msg = password_meets_policy_func(pw)

            assert valid is True, f"Passwort '{pw}' erfuellt Policy nicht: {msg}"

    def test_contains_lowercase(self, generate_strong_password_func):
        """Generiertes Passwort enthaelt Kleinbuchstaben"""
        pw = generate_strong_password_func()

        assert any(c.islower() for c in pw)

    def test_contains_uppercase(self, generate_strong_password_func):
        """Generiertes Passwort enthaelt Grossbuchstaben"""
        pw = generate_strong_password_func()

        assert any(c.isupper() for c in pw)

    def test_contains_digit(self, generate_strong_password_func):
        """Generiertes Passwort enthaelt Ziffern"""
        pw = generate_strong_password_func()

        assert any(c.isdigit() for c in pw)

    def test_contains_special_char(self, generate_strong_password_func):
        """Generiertes Passwort enthaelt Sonderzeichen"""
        pw = generate_strong_password_func()

        assert any(not c.isalnum() for c in pw)

    def test_randomness(self, generate_strong_password_func):
        """Generierte Passwoerter sind unterschiedlich"""
        passwords = [generate_strong_password_func() for _ in range(10)]

        # Alle sollten unterschiedlich sein
        assert len(set(passwords)) == 10

    def test_no_obvious_patterns(self, generate_strong_password_func):
        """Generierte Passwoerter haben keine offensichtlichen Muster"""
        pw = generate_strong_password_func()

        # Nicht alle Zeichen gleich
        assert len(set(pw)) > 1

        # Nicht nur Buchstaben am Anfang, Zahlen am Ende
        first_half = pw[:len(pw)//2]
        second_half = pw[len(pw)//2:]

        # Beide Haelften sollten gemischt sein
        assert any(c.isdigit() for c in first_half) or any(c.isalpha() for c in second_half)


# ============================================================================
# EMAIL VALIDATION TESTS
# ============================================================================

class TestValidateEmail:
    """Tests fuer validate_email() Funktion"""

    def test_valid_email_simple(self, validate_email_func):
        """Einfache gueltige Email wird akzeptiert"""
        valid, msg = validate_email_func('test@example.com')

        assert valid is True
        assert msg == ''

    def test_valid_email_with_subdomain(self, validate_email_func):
        """Email mit Subdomain wird akzeptiert"""
        valid, msg = validate_email_func('user@mail.example.com')

        assert valid is True

    def test_valid_email_with_plus(self, validate_email_func):
        """Email mit + wird akzeptiert"""
        valid, msg = validate_email_func('user+tag@example.com')

        assert valid is True

    def test_valid_email_with_dots(self, validate_email_func):
        """Email mit Punkten im Local-Part wird akzeptiert"""
        valid, msg = validate_email_func('first.last@example.com')

        assert valid is True

    def test_invalid_no_at(self, validate_email_func):
        """Email ohne @ wird abgelehnt"""
        valid, msg = validate_email_func('invalid')

        assert valid is False
        assert '@' in msg

    def test_invalid_no_local_part(self, validate_email_func):
        """Email ohne Local-Part wird abgelehnt"""
        valid, msg = validate_email_func('@example.com')

        assert valid is False

    def test_invalid_no_domain(self, validate_email_func):
        """Email ohne Domain wird abgelehnt"""
        valid, msg = validate_email_func('user@')

        assert valid is False

    def test_invalid_no_dot_in_domain(self, validate_email_func):
        """Email ohne Punkt in Domain wird abgelehnt"""
        valid, msg = validate_email_func('user@domain')

        assert valid is False

    def test_invalid_too_short(self, validate_email_func):
        """Zu kurze Email wird abgelehnt"""
        valid, msg = validate_email_func('a@b')

        assert valid is False

    def test_invalid_type(self, validate_email_func):
        """Nicht-String wird abgelehnt"""
        valid, msg = validate_email_func(12345)

        assert valid is False

    def test_invalid_none(self, validate_email_func):
        """None wird abgelehnt"""
        valid, msg = validate_email_func(None)

        assert valid is False

    def test_strips_whitespace(self, validate_email_func):
        """Whitespace wird entfernt"""
        valid, msg = validate_email_func('  test@example.com  ')

        assert valid is True

    def test_various_valid_emails(self, validate_email_func):
        """Verschiedene gueltige Email-Formate"""
        valid_emails = [
            'simple@example.com',
            'very.common@example.com',
            'disposable.style.email.with+symbol@example.com',
            'other.email-with-hyphen@example.com',
            'fully-qualified-domain@example.com',
            'user.name+tag+sorting@example.com',
            'x@example.com',
            'example-indeed@strange-example.com',
            'example@s.example',
        ]

        for email in valid_emails:
            valid, msg = validate_email_func(email)
            assert valid is True, f"Email '{email}' sollte gueltig sein: {msg}"

    def test_various_invalid_emails(self, validate_email_func):
        """Verschiedene ungueltige Email-Formate"""
        invalid_emails = [
            '',
            'plainaddress',
            '@no-local-part.com',
            'missing-domain@.com',
            'missing-tld@domain',
            'two@@at.com',
        ]

        for email in invalid_emails:
            valid, msg = validate_email_func(email)
            assert valid is False, f"Email '{email}' sollte ungueltig sein"


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestIntegration:
    """Integration-Tests fuer zusammenhaengende Funktionalitaet"""

    def test_user_login_workflow(self, user_class, temp_db):
        """Test: User-Login Workflow"""
        # 1. User per Email laden
        user = user_class.get_by_email('max.mustermann@example.com', temp_db)
        assert user is not None

        # 2. ID fuer Session pruefen
        user_id = user.get_id()
        assert user_id == '1'

        # 3. User per ID wiederladen (Session-Restore)
        restored_user = user_class.get(int(user_id), temp_db)
        assert restored_user is not None
        assert restored_user.email == user.email

    def test_password_generation_and_validation(self, generate_strong_password_func, password_meets_policy_func):
        """Test: Passwort generieren und validieren"""
        # Generiere Passwort
        pw = generate_strong_password_func(length=16)

        # Validiere
        valid, msg = password_meets_policy_func(pw)

        assert valid is True
        assert len(pw) == 16


# ============================================================================
# EDGE CASES
# ============================================================================

class TestEdgeCases:
    """Tests fuer Randfaelle"""

    def test_user_with_special_chars_in_email(self, user_class):
        """User mit Sonderzeichen in Email"""
        user = user_class(id=1, email='user+tag@example.com')

        assert user.email == 'user+tag@example.com'

    def test_empty_email(self, user_class):
        """User mit leerer Email"""
        user = user_class(id=1, email='')

        assert user.email == ''

    def test_very_long_password(self, generate_strong_password_func, password_meets_policy_func):
        """Sehr langes Passwort"""
        pw = generate_strong_password_func(length=100)

        assert len(pw) == 100

        valid, msg = password_meets_policy_func(pw)
        assert valid is True

    def test_password_with_unicode(self, password_meets_policy_func):
        """Passwort mit Unicode-Zeichen"""
        # Unicode-Sonderzeichen zaehlen als Sonderzeichen
        pw = 'SecurePass123Ü'

        valid, msg = password_meets_policy_func(pw)

        # Sollte gueltig sein (Ü ist Sonderzeichen)
        assert valid is True

    def test_email_with_numbers(self, validate_email_func):
        """Email mit Zahlen"""
        valid, msg = validate_email_func('user123@example456.com')

        assert valid is True

    def test_email_with_hyphen_in_domain(self, validate_email_func):
        """Email mit Bindestrich in Domain"""
        valid, msg = validate_email_func('user@my-domain.com')

        assert valid is True

    def test_concurrent_user_loading(self, user_class, temp_db):
        """Mehrere User gleichzeitig laden"""
        user1 = user_class.get(1, temp_db)
        user2 = user_class.get(2, temp_db)
        user3 = user_class.get(3, temp_db)

        assert user1.id == 1
        assert user2.id == 2
        assert user3.id == 3

        # Alle unterschiedlich
        assert user1.email != user2.email != user3.email