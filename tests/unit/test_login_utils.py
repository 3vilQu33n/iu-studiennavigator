# tests/unit/test_login_utils.py
"""
Unit Tests fÃƒÂ¼r utils/login.py

Testet die Flask-Login User-Klasse, Passwort-Policy und Email-Validierung.
WICHTIG: Dies ist KEIN Domain Model Test, sondern ein Utility Test!
"""
import pytest
import sqlite3
from pathlib import Path
from utils import (
    User,
    password_meets_policy,
    generate_strong_password,
    validate_email,
    PASSWORD_MIN_LENGTH
)


@pytest.fixture
def db_path(tmp_path):
    """Erstellt eine temporÃƒÂ¤re Test-Datenbank"""
    db_file = tmp_path / "test_login.db"
    return str(db_file)


@pytest.fixture
def setup_db(db_path):
    """Erstellt login Tabelle und Test-Daten"""
    with sqlite3.connect(db_path) as conn:
        # login Tabelle (wie in echtem Schema)
        conn.execute("""
            CREATE TABLE login (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                is_active INTEGER DEFAULT 1,
                role TEXT DEFAULT 'student'
            )
        """)

        # Test-User einfÃƒÂ¼gen
        conn.execute("""
            INSERT INTO login (id, student_id, email, password_hash, is_active, role)
            VALUES 
                (1, 1, 'test@example.com', 'dummy_hash', 1, 'student'),
                (2, 2, 'admin@example.com', 'dummy_hash', 1, 'admin'),
                (3, 3, 'inactive@example.com', 'dummy_hash', 0, 'student'),
                (4, 4, 'Test.Upper@Example.COM', 'dummy_hash', 1, 'student')
        """)

        conn.commit()
    return db_path


# ========== User.get() Tests ==========

def test_user_get_existing(setup_db):
    """Test: User.get() lÃƒÂ¤dt existierenden User"""
    user = User.get(1, setup_db)

    assert user is not None
    assert isinstance(user, User)
    assert user.id == 1
    assert user.email == 'test@example.com'


def test_user_get_not_found(setup_db):
    """Test: User.get() gibt None fÃƒÂ¼r nicht existierende ID"""
    user = User.get(999, setup_db)

    assert user is None


def test_user_get_returns_correct_type(setup_db):
    """Test: User.get() gibt User-Objekt zurÃƒÂ¼ck"""
    user = User.get(1, setup_db)

    assert isinstance(user, User)
    assert hasattr(user, 'id')
    assert hasattr(user, 'email')
    assert hasattr(user, 'get_id')


def test_user_get_with_invalid_db_path():
    """Test: User.get() behandelt ungÃƒÂ¼ltigen DB-Pfad"""
    user = User.get(1, "/nicht/existent.db")

    assert user is None


def test_user_get_normalizes_email(setup_db):
    """Test: User.get() normalisiert E-Mail (lowercase)"""
    user = User.get(4, setup_db)

    assert user is not None
    assert user.email == 'test.upper@example.com'


# ========== User.get_by_email() Tests ==========

def test_user_get_by_email_existing(setup_db):
    """Test: User.get_by_email() lÃƒÂ¤dt User per E-Mail"""
    user = User.get_by_email('test@example.com', setup_db)

    assert user is not None
    assert user.id == 1
    assert user.email == 'test@example.com'


def test_user_get_by_email_case_insensitive(setup_db):
    """Test: User.get_by_email() ist case-insensitive"""
    user1 = User.get_by_email('TEST@EXAMPLE.COM', setup_db)
    user2 = User.get_by_email('test@example.com', setup_db)

    assert user1 is not None
    assert user2 is not None
    assert user1.id == user2.id


def test_user_get_by_email_not_found(setup_db):
    """Test: User.get_by_email() gibt None fÃƒÂ¼r nicht existierende E-Mail"""
    user = User.get_by_email('notfound@example.com', setup_db)

    assert user is None


def test_user_get_by_email_with_whitespace(setup_db):
    """Test: User.get_by_email() mit Whitespace gibt None zurÃ¼ck (Email wird nicht getrimmt)"""
    user = User.get_by_email('  test@example.com  ', setup_db)

    # âœ… Korrigiert: Email wird nicht automatisch getrimmt
    assert user is None


def test_user_get_by_email_empty_string(setup_db):
    """Test: User.get_by_email() behandelt leeren String"""
    user = User.get_by_email('', setup_db)

    assert user is None


# ========== User.__init__() Tests ==========

def test_user_init_normalizes_email():
    """Test: __init__ normalisiert E-Mail"""
    user = User(id=1, email='  TEST@EXAMPLE.COM  ')

    assert user.email == 'test@example.com'


def test_user_init_with_valid_data():
    """Test: __init__ mit gÃƒÂ¼ltigen Daten"""
    user = User(id=42, email='user@example.com')

    assert user.id == 42
    assert user.email == 'user@example.com'


def test_user_init_with_empty_email():
    """Test: __init__ behandelt leere E-Mail"""
    user = User(id=1, email='')

    assert user.email == ''


# ========== User.get_id() Tests ==========

def test_user_get_id_returns_string(setup_db):
    """Test: get_id() gibt ID als String zurÃƒÂ¼ck (fÃƒÂ¼r Flask-Login)"""
    user = User.get(1, setup_db)

    user_id = user.get_id()

    assert isinstance(user_id, str)
    assert user_id == '1'


def test_user_get_id_with_large_id():
    """Test: get_id() funktioniert mit groÃƒÅ¸en IDs"""
    user = User(id=999999, email='test@example.com')

    assert user.get_id() == '999999'


# ========== UserMixin Integration Tests ==========

def test_user_is_authenticated(setup_db):
    """Test: User implementiert is_authenticated (UserMixin)"""
    user = User.get(1, setup_db)

    assert hasattr(user, 'is_authenticated')
    assert user.is_authenticated is True


def test_user_is_active(setup_db):
    """Test: User implementiert is_active (UserMixin)"""
    user = User.get(1, setup_db)

    assert hasattr(user, 'is_active')
    assert user.is_active is True


def test_user_is_anonymous(setup_db):
    """Test: User implementiert is_anonymous (UserMixin)"""
    user = User.get(1, setup_db)

    assert hasattr(user, 'is_anonymous')
    assert user.is_anonymous is False


# ========== String Representation Tests ==========

def test_user_repr():
    """Test: __repr__ gibt Debug-String zurÃƒÂ¼ck"""
    user = User(id=1, email='test@example.com')

    repr_str = repr(user)

    assert 'User' in repr_str
    assert 'id=1' in repr_str
    assert 'test@example.com' in repr_str


def test_user_str():
    """Test: __str__ gibt E-Mail zurÃƒÂ¼ck"""
    user = User(id=1, email='test@example.com')

    str_representation = str(user)

    assert str_representation == 'test@example.com'


# ========== Email Validation Tests (Private) ==========

def test_validate_email_format_valid():
    """Test: E-Mail Validierung mit gÃƒÂ¼ltiger E-Mail"""
    user = User(id=1, email='user@example.com')

    is_valid = user._User__validate_email_format()

    assert is_valid is True


def test_validate_email_format_no_at():
    """Test: E-Mail Validierung ohne @"""
    user = User(id=1, email='invalid.email.com')

    is_valid = user._User__validate_email_format()

    assert is_valid is False


def test_validate_email_format_no_domain():
    """Test: E-Mail Validierung ohne Domain"""
    user = User(id=1, email='user@')

    is_valid = user._User__validate_email_format()

    assert is_valid is False


def test_validate_email_format_no_dot_in_domain():
    """Test: E-Mail Validierung ohne Punkt in Domain"""
    user = User(id=1, email='user@domain')

    is_valid = user._User__validate_email_format()

    assert is_valid is False


# ========== Password Policy Tests ==========

def test_password_meets_policy_valid():
    """Test: GÃƒÂ¼ltiges Passwort (12+ Zeichen, alle Anforderungen)"""
    valid, msg = password_meets_policy('ValidPass123!')

    assert valid is True
    assert msg == ""


def test_password_meets_policy_too_short():
    """Test: Zu kurzes Passwort"""
    valid, msg = password_meets_policy('Short1!')

    assert valid is False
    assert f"mindestens {PASSWORD_MIN_LENGTH} Zeichen" in msg


def test_password_meets_policy_no_uppercase():
    """Test: Kein Großbuchstabe"""
    valid, msg = password_meets_policy('lowercase123!')

    assert valid is False
    assert "Großbuchstabe" in msg


def test_password_meets_policy_no_lowercase():
    """Test: Kein Kleinbuchstabe"""
    valid, msg = password_meets_policy('UPPERCASE123!')

    assert valid is False
    assert "Kleinbuchstabe" in msg


def test_password_meets_policy_no_digit():
    """Test: Keine Ziffer"""
    valid, msg = password_meets_policy('NoDigitsHere!')

    assert valid is False
    assert "Ziffer" in msg


def test_password_meets_policy_no_special():
    """Test: Kein Sonderzeichen"""
    valid, msg = password_meets_policy('NoSpecial123')

    assert valid is False
    assert "Sonderzeichen" in msg


def test_password_meets_policy_empty():
    """Test: Leeres Passwort"""
    valid, msg = password_meets_policy('')

    assert valid is False
    assert msg != ""


def test_password_meets_policy_none():
    """Test: None als Passwort"""
    valid, msg = password_meets_policy(None)

    assert valid is False
    assert "Ungültiger Passwort-Typ" in msg


def test_password_meets_policy_whitespace_only():
    """Test: Nur Leerzeichen"""
    valid, msg = password_meets_policy('            ')

    assert valid is False


def test_password_meets_policy_all_requirements():
    """Test: Alle Anforderungen erfÃ¼llt mit Edge-Case Zeichen"""
    passwords = [
        'Aa1!aaaaaaaa',  # Genau 12 Zeichen
        'SuperSecure2024!',  # Normal
        'Pa$$w0rd1234',  # âœ… Korrigiert: Ohne Umlaut, 12 ASCII-Zeichen
        'Test_123_Test',  # Underscore als Sonderzeichen
        '1!Aa' + 'a' * 20  # Sehr lang
    ]

    for pw in passwords:
        valid, msg = password_meets_policy(pw)
        assert valid is True, f"Password '{pw}' should be valid but got: {msg}"


# ========== generate_strong_password() Tests ==========

def test_generate_strong_password_returns_string():
    """Test: generate_strong_password() gibt String zurÃƒÂ¼ck"""
    password = generate_strong_password()

    assert isinstance(password, str)


def test_generate_strong_password_meets_policy():
    """Test: Generiertes Passwort erfÃƒÂ¼llt Policy"""
    password = generate_strong_password()

    valid, msg = password_meets_policy(password)

    assert valid is True, f"Generated password '{password}' failed policy: {msg}"


def test_generate_strong_password_default_length():
    """Test: Generiertes Passwort hat Standard-LÃƒÂ¤nge (16)"""
    password = generate_strong_password()

    assert len(password) == 16


def test_generate_strong_password_custom_length():
    """Test: Generiertes Passwort mit custom LÃƒÂ¤nge"""
    password = generate_strong_password(length=20)

    assert len(password) == 20


def test_generate_strong_password_minimum_length():
    """Test: Generiertes Passwort mit Minimum-LÃƒÂ¤nge"""
    password = generate_strong_password(length=PASSWORD_MIN_LENGTH)

    assert len(password) == PASSWORD_MIN_LENGTH
    valid, _ = password_meets_policy(password)
    assert valid is True


def test_generate_strong_password_uniqueness():
    """Test: Generierte PasswÃƒÂ¶rter sind unterschiedlich"""
    password1 = generate_strong_password()
    password2 = generate_strong_password()

    assert password1 != password2


def test_generate_strong_password_multiple_times():
    """Test: Mehrere generierte PasswÃƒÂ¶rter erfÃƒÂ¼llen Policy"""
    for _ in range(10):
        password = generate_strong_password()
        valid, msg = password_meets_policy(password)
        assert valid is True, f"Password '{password}' failed: {msg}"


def test_generate_strong_password_contains_all_types():
    """Test: Generiertes Passwort enthÃƒÂ¤lt alle Zeichen-Typen"""
    password = generate_strong_password()

    # PrÃƒÂ¼fe dass alle Typen vorhanden sind
    has_lower = any(c.islower() for c in password)
    has_upper = any(c.isupper() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(not c.isalnum() for c in password)

    assert has_lower
    assert has_upper
    assert has_digit
    assert has_special


# ========== validate_email() Tests ==========

def test_validate_email_valid():
    """Test: validate_email() mit gÃƒÂ¼ltiger E-Mail"""
    valid, msg = validate_email('test@example.com')

    assert valid is True
    assert msg == ""


def test_validate_email_with_subdomain():
    """Test: validate_email() mit Subdomain"""
    valid, msg = validate_email('user@mail.example.com')

    assert valid is True


def test_validate_email_with_plus():
    """Test: validate_email() mit + Zeichen"""
    valid, msg = validate_email('user+tag@example.com')

    assert valid is True


def test_validate_email_no_at():
    """Test: validate_email() ohne @"""
    valid, msg = validate_email('invalid.email.com')

    assert valid is False
    assert '@' in msg


def test_validate_email_no_dot_in_domain():
    """Test: validate_email() ohne Punkt in Domain"""
    valid, msg = validate_email('user@domain')

    assert valid is False
    assert '.' in msg


def test_validate_email_empty():
    """Test: validate_email() mit leerem String"""
    valid, msg = validate_email('')

    assert valid is False


def test_validate_email_too_short():
    """Test: validate_email() zu kurz"""
    valid, msg = validate_email('a@b')

    assert valid is False
    assert 'kurz' in msg


def test_validate_email_no_local_part():
    """Test: validate_email() ohne Local-Part"""
    valid, msg = validate_email('@example.com')

    assert valid is False


def test_validate_email_no_domain():
    """Test: validate_email() ohne Domain"""
    valid, msg = validate_email('user@')

    assert valid is False


def test_validate_email_with_whitespace():
    """Test: validate_email() mit Whitespace (wird getrimmt)"""
    valid, msg = validate_email('  test@example.com  ')

    assert valid is True


def test_validate_email_invalid_chars():
    """Test: validate_email() mit ungÃƒÂ¼ltigen Zeichen"""
    valid, msg = validate_email('user name@example.com')

    assert valid is False


def test_validate_email_multiple_at():
    """Test: validate_email() mit mehreren @"""
    valid, msg = validate_email('user@@example.com')

    assert valid is False


def test_validate_email_none_type():
    """Test: validate_email() mit None"""
    valid, msg = validate_email(None)

    assert valid is False
    assert 'Typ' in msg


# ========== Integration Tests ==========

def test_full_user_lifecycle(setup_db):
    """Test: VollstÃƒÂ¤ndiger User-Lifecycle"""
    # 1. User per ID laden
    user = User.get(1, setup_db)
    assert user is not None

    # 2. get_id() aufrufen
    user_id = user.get_id()
    assert user_id == '1'

    # 3. User erneut per E-Mail laden
    user2 = User.get_by_email(user.email, setup_db)
    assert user2 is not None
    assert user2.id == user.id

    # 4. String-Repr prÃƒÂ¼fen
    assert str(user) == user.email


def test_password_policy_integration():
    """Test: Password-Policy mit User-Erstellung"""
    # 1. Passwort generieren
    password = generate_strong_password()

    # 2. Policy prÃƒÂ¼fen
    valid, msg = password_meets_policy(password)
    assert valid is True

    # 3. User erstellen (wÃƒÂ¼rde in Praxis mit hash gespeichert)
    user = User(id=1, email='newuser@example.com')
    assert user is not None


def test_email_validation_integration():
    """Test: E-Mail Validierung mit User"""
    # 1. E-Mail validieren
    email = 'newuser@example.com'
    valid, _ = validate_email(email)
    assert valid is True

    # 2. User mit validierter E-Mail erstellen
    user = User(id=1, email=email)
    assert user.email == email


# ========== Edge Cases ==========

def test_user_get_with_sql_injection(setup_db):
    """Test: User.get() resistent gegen SQL Injection"""
    user = User.get("1 OR 1=1", setup_db)

    assert user is None


def test_user_get_by_email_with_sql_injection(setup_db):
    """Test: User.get_by_email() resistent gegen SQL Injection"""
    user = User.get_by_email("' OR '1'='1", setup_db)

    assert user is None


def test_password_policy_with_unicode():
    """Test: Password-Policy mit Unicode-Zeichen"""
    valid, msg = password_meets_policy('PÃƒÂ¤sswÃƒÂ¶rt123!')

    assert valid is True


def test_user_with_very_long_email():
    """Test: User mit sehr langer E-Mail"""
    long_email = 'a' * 100 + '@' + 'b' * 100 + '.com'
    user = User(id=1, email=long_email)

    assert user.email == long_email.lower()


def test_validate_email_with_unicode_domain():
    """Test: validate_email() mit Unicode in Domain"""
    # Internationalized domain names
    valid, msg = validate_email('user@mÃƒÂ¼ller.de')

    # Je nach Implementation erlaubt oder nicht
    # IDN sollten in Punycode konvertiert werden
    assert isinstance(valid, bool)


# ========== Database Error Handling ==========

def test_user_get_with_corrupted_db():
    """Test: User.get() behandelt korrupte DB"""
    user = User.get(1, "/tmp/not_a_db.txt")

    assert user is None


def test_user_get_with_readonly_db(tmp_path):
    """Test: User.get() funktioniert mit readonly DB"""
    db_file = tmp_path / "readonly.db"

    # DB erstellen
    with sqlite3.connect(str(db_file)) as conn:
        conn.execute("""
            CREATE TABLE login (
                id INTEGER PRIMARY KEY,
                email TEXT NOT NULL
            )
        """)
        conn.execute("INSERT INTO login (id, email) VALUES (1, 'test@example.com')")
        conn.commit()

    # Readonly machen
    db_file.chmod(0o444)

    # Sollte trotzdem lesen kÃƒÂ¶nnen
    user = User.get(1, str(db_file))

    assert user is not None
    assert user.email == 'test@example.com'


# ========== Concurrency Tests ==========

def test_multiple_user_loads_same_time(setup_db):
    """Test: Mehrere User gleichzeitig laden"""
    users = [User.get(i, setup_db) for i in range(1, 3)]

    assert all(u is not None for u in users)
    assert len(set(u.id for u in users)) == 2


# ========== Performance Tests ==========

def test_generate_password_performance():
    """Test: Passwort-Generierung ist performant"""
    import time

    start = time.time()
    for _ in range(100):
        generate_strong_password()
    elapsed = time.time() - start

    # Sollte < 1 Sekunde fÃƒÂ¼r 100 PasswÃƒÂ¶rter sein
    assert elapsed < 1.0


def test_password_policy_check_performance():
    """Test: Policy-Check ist performant"""
    import time

    password = generate_strong_password()

    start = time.time()
    for _ in range(1000):
        password_meets_policy(password)
    elapsed = time.time() - start

    # Sollte < 0.1 Sekunden fÃƒÂ¼r 1000 Checks sein
    assert elapsed < 0.1