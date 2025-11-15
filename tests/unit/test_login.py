# tests/unit/test_login_model.py
"""
Unit Tests für models/login.py (Domain Model)

Testet das Login Domain Model mit Argon2 Password Hashing.
HINWEIS: Separate Tests für utils/login.py in test_login_utils.py
"""
import pytest
from datetime import datetime
from models import Login, create_login_for_student
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

# Argon2 Password Hasher für Tests
ph = PasswordHasher()


@pytest.fixture
def valid_login_data():
    """Gültige Login-Daten für Tests"""
    return {
        'id': None,
        'student_id': 1,
        'email': 'test@example.com',
        'password_hash': ph.hash('TestPassword123!'),
        'is_active': 1,
        'role': 'student',
        'created_at': datetime.now().isoformat(),
        'must_change_password': 0,
        'last_login': None
    }


@pytest.fixture
def sample_login(valid_login_data):
    """Erstellt ein Test-Login-Objekt"""
    return Login(**valid_login_data)


# ========== Initialization Tests ==========

def test_login_init_with_all_fields(valid_login_data):
    """Test: Login-Objekt mit allen Feldern erstellen"""
    login = Login(**valid_login_data)

    assert login.student_id == 1
    assert login.email == 'test@example.com'
    assert login.is_active == 1
    assert login.role == 'student'
    assert login.must_change_password == 0


def test_login_init_with_id():
    """Test: Login mit bestehender ID"""
    login = Login(
        id=42,
        student_id=1,
        email='test@example.com',
        password_hash=ph.hash('Password123!'),
        is_active=1,
        role='student'
    )

    assert login.id == 42


def test_login_init_sets_created_at_if_none():
    """Test: created_at wird automatisch gesetzt wenn None"""
    login = Login(
        id=None,
        student_id=1,
        email='test@example.com',
        password_hash=ph.hash('Password123!'),
        is_active=1,
        role='student',
        created_at=None
    )

    assert login.created_at is not None
    assert isinstance(login.created_at, str)


def test_login_post_init_normalizes_email():
    """Test: __post_init__ normalisiert E-Mail"""
    login = Login(
        id=None,
        student_id=1,
        email='  TEST@EXAMPLE.COM  ',
        password_hash=ph.hash('Password123!'),
        is_active=1,
        role='student'
    )

    assert login.email == 'test@example.com'


# ========== Email Validation Tests ==========

def test_login_email_valid(valid_login_data):
    """Test: Gültige E-Mail wird akzeptiert"""
    login = Login(**valid_login_data)

    assert login.email == 'test@example.com'


def test_login_email_invalid_no_at(valid_login_data):
    """Test: E-Mail ohne @ wirft ValueError"""
    valid_login_data['email'] = 'invalid.email.com'

    with pytest.raises(ValueError) as exc_info:
        Login(**valid_login_data)

    assert 'E-Mail' in str(exc_info.value)


def test_login_email_empty(valid_login_data):
    """Test: Leere E-Mail wirft ValueError"""
    valid_login_data['email'] = ''

    with pytest.raises(ValueError):
        Login(**valid_login_data)


def test_login_email_no_domain(valid_login_data):
    """Test: E-Mail ohne Domain wirft ValueError"""
    valid_login_data['email'] = 'test@'

    with pytest.raises(ValueError):
        Login(**valid_login_data)


def test_login_email_no_dot_in_domain(valid_login_data):
    """Test: E-Mail ohne Punkt in Domain wirft ValueError"""
    valid_login_data['email'] = 'test@domain'

    with pytest.raises(ValueError):
        Login(**valid_login_data)


def test_login_email_normalization():
    """Test: E-Mail wird normalisiert (lowercase, stripped)"""
    login = Login(
        id=None,
        student_id=1,
        email='  TEST.User@EXAMPLE.COM  ',
        password_hash=ph.hash('Password123!'),
        is_active=1,
        role='student'
    )

    assert login.email == 'test.user@example.com'


# ========== student_id Validation Tests (KOMPOSITION) ==========

def test_login_student_id_required(valid_login_data):
    """Test: student_id ist erforderlich (KOMPOSITION)"""
    valid_login_data['student_id'] = None

    with pytest.raises(ValueError) as exc_info:
        Login(**valid_login_data)

    assert 'student_id' in str(exc_info.value) or 'KOMPOSITION' in str(exc_info.value)


def test_login_student_id_must_be_positive(valid_login_data):
    """Test: student_id muss positiv sein"""
    valid_login_data['student_id'] = 0

    with pytest.raises(ValueError):
        Login(**valid_login_data)


def test_login_student_id_negative(valid_login_data):
    """Test: student_id darf nicht negativ sein"""
    valid_login_data['student_id'] = -1

    with pytest.raises(ValueError):
        Login(**valid_login_data)


# ========== password_hash Validation Tests ==========

def test_login_password_hash_required(valid_login_data):
    """Test: password_hash ist erforderlich"""
    valid_login_data['password_hash'] = ''

    with pytest.raises(ValueError):
        Login(**valid_login_data)


def test_login_password_hash_too_short(valid_login_data):
    """Test: password_hash muss mindestens 20 Zeichen haben"""
    valid_login_data['password_hash'] = 'tooshort'

    with pytest.raises(ValueError) as exc_info:
        Login(**valid_login_data)

    assert 'password_hash' in str(exc_info.value)


def test_login_password_hash_argon2_format():
    """Test: Argon2 Hash wird akzeptiert"""
    login = Login(
        id=None,
        student_id=1,
        email='test@example.com',
        password_hash=ph.hash('SecurePassword123!'),
        is_active=1,
        role='student'
    )

    assert login.password_hash.startswith('$argon2')


# ========== Role Validation Tests ==========

def test_login_role_student(valid_login_data):
    """Test: Rolle 'student' ist gültig"""
    valid_login_data['role'] = 'student'

    login = Login(**valid_login_data)

    assert login.role == 'student'


def test_login_role_admin(valid_login_data):
    """Test: Rolle 'admin' ist gültig"""
    valid_login_data['role'] = 'admin'

    login = Login(**valid_login_data)

    assert login.role == 'admin'


def test_login_role_invalid(valid_login_data):
    """Test: Ungültige Rolle wirft ValueError"""
    valid_login_data['role'] = 'superuser'

    with pytest.raises(ValueError) as exc_info:
        Login(**valid_login_data)

    assert 'role' in str(exc_info.value).lower()


def test_login_role_case_sensitive(valid_login_data):
    """Test: Rolle ist case-sensitive"""
    valid_login_data['role'] = 'STUDENT'

    with pytest.raises(ValueError):
        Login(**valid_login_data)


def test_login_role_empty(valid_login_data):
    """Test: Leere Rolle wirft ValueError"""
    valid_login_data['role'] = ''

    with pytest.raises(ValueError):
        Login(**valid_login_data)


# ========== Password Verification Tests ==========

def test_verify_password_correct(sample_login):
    """Test: verify_password() mit korrektem Passwort"""
    result = sample_login.verify_password('TestPassword123!')

    assert result is True


def test_verify_password_incorrect(sample_login):
    """Test: verify_password() mit falschem Passwort"""
    result = sample_login.verify_password('WrongPassword123!')

    assert result is False


def test_verify_password_empty(sample_login):
    """Test: verify_password() mit leerem Passwort"""
    result = sample_login.verify_password('')

    assert result is False


def test_verify_password_none(sample_login):
    """Test: verify_password() mit None"""
    # Je nach Implementation kann Exception geworfen werden
    try:
        result = sample_login.verify_password(None)
        assert result is False
    except (AttributeError, TypeError):
        # Acceptable if None is not handled
        pass


def test_verify_password_with_unicode(valid_login_data):
    """Test: verify_password() mit Unicode-Passwort"""
    password = 'Pässwört123!'
    valid_login_data['password_hash'] = ph.hash(password)

    login = Login(**valid_login_data)

    assert login.verify_password(password) is True
    assert login.verify_password('WrongPassword123!') is False


# ========== hash_password() Tests ==========

def test_hash_password_returns_string():
    """Test: hash_password() gibt String zurück"""
    hashed = Login.hash_password('TestPassword123!')

    assert isinstance(hashed, str)


def test_hash_password_is_argon2():
    """Test: hash_password() erzeugt Argon2 Hash"""
    hashed = Login.hash_password('TestPassword123!')

    assert hashed.startswith('$argon2')


def test_hash_password_different_for_same_password():
    """Test: hash_password() erzeugt unterschiedliche Hashes (Salt)"""
    hash1 = Login.hash_password('TestPassword123!')
    hash2 = Login.hash_password('TestPassword123!')

    assert hash1 != hash2


def test_hash_password_verifiable():
    """Test: Gehashtes Passwort kann verifiziert werden"""
    password = 'TestPassword123!'
    hashed = Login.hash_password(password)

    # Manuell mit PasswordHasher verifizieren
    ph.verify(hashed, password)  # Wirft Exception wenn falsch


# ========== is_active_account() Tests ==========

def test_is_active_account_true(sample_login):
    """Test: is_active_account() gibt True für aktiven Account"""
    sample_login.is_active = 1

    assert sample_login.is_active_account() is True


def test_is_active_account_false(sample_login):
    """Test: is_active_account() gibt False für deaktivierten Account"""
    sample_login.is_active = 0

    assert sample_login.is_active_account() is False


# ========== needs_password_change() Tests ==========

def test_needs_password_change_false(sample_login):
    """Test: needs_password_change() gibt False wenn nicht erforderlich"""
    sample_login.must_change_password = 0

    assert sample_login.needs_password_change() is False


def test_needs_password_change_true(sample_login):
    """Test: needs_password_change() gibt True wenn erforderlich"""
    sample_login.must_change_password = 1

    assert sample_login.needs_password_change() is True


# ========== Role Check Tests ==========

def test_is_admin_true(sample_login):
    """Test: is_admin() gibt True für Admin"""
    sample_login.role = 'admin'

    assert sample_login.is_admin() is True


def test_is_admin_false(sample_login):
    """Test: is_admin() gibt False für Student"""
    sample_login.role = 'student'

    assert sample_login.is_admin() is False


def test_is_student_true(sample_login):
    """Test: is_student() gibt True für Student"""
    sample_login.role = 'student'

    assert sample_login.is_student() is True


def test_is_student_false(sample_login):
    """Test: is_student() gibt False für Admin"""
    sample_login.role = 'admin'

    assert sample_login.is_student() is False


# ========== update_last_login() Tests ==========

def test_update_last_login_sets_timestamp(sample_login):
    """Test: update_last_login() setzt Timestamp"""
    assert sample_login.last_login is None

    sample_login.update_last_login()

    assert sample_login.last_login is not None
    assert isinstance(sample_login.last_login, str)


def test_update_last_login_updates_timestamp(sample_login):
    """Test: update_last_login() aktualisiert bestehenden Timestamp"""
    old_time = '2024-01-01T00:00:00'
    sample_login.last_login = old_time

    sample_login.update_last_login()

    assert sample_login.last_login != old_time


# ========== to_dict() Tests ==========

def test_to_dict_contains_all_fields(sample_login):
    """Test: to_dict() enthält alle wichtigen Felder"""
    result = sample_login.to_dict()

    assert 'id' in result
    assert 'student_id' in result
    assert 'email' in result
    assert 'is_active' in result
    assert 'role' in result
    assert 'created_at' in result
    assert 'must_change_password' in result
    assert 'last_login' in result


def test_to_dict_excludes_password_hash(sample_login):
    """Test: to_dict() enthält KEIN password_hash (Sicherheit!)"""
    result = sample_login.to_dict()

    assert 'password_hash' not in result


def test_to_dict_converts_is_active_to_bool(sample_login):
    """Test: to_dict() konvertiert is_active zu bool"""
    sample_login.is_active = 1
    result = sample_login.to_dict()

    assert result['is_active'] is True
    assert isinstance(result['is_active'], bool)


def test_to_dict_includes_computed_fields(sample_login):
    """Test: to_dict() enthält berechnete Felder"""
    result = sample_login.to_dict()

    assert 'needs_password_change' in result
    assert 'is_admin' in result


def test_to_dict_with_must_change_password(sample_login):
    """Test: to_dict() konvertiert must_change_password zu bool"""
    sample_login.must_change_password = 1
    result = sample_login.to_dict()

    assert result['must_change_password'] is True
    assert isinstance(result['must_change_password'], bool)


# ========== from_db_row() Tests ==========

def test_from_db_row_with_all_fields():
    """Test: from_db_row() mit allen Feldern"""
    class MockRow:
        def __getitem__(self, key):
            data = {
                'id': 1,
                'student_id': 42,
                'email': 'test@example.com',
                'password_hash': ph.hash('Password123!'),
                'is_active': 1,
                'role': 'student',
                'created_at': '2024-01-01T00:00:00',
                'must_change_password': 0,
                'last_login': None
            }
            return data[key]

    login = Login.from_db_row(MockRow())

    assert login.id == 1
    assert login.student_id == 42
    assert login.email == 'test@example.com'
    assert login.is_active == 1
    assert login.role == 'student'


def test_from_db_row_with_missing_optional_fields():
    """Test: from_db_row() mit fehlenden optionalen Feldern"""
    class MockRow:
        def __getitem__(self, key):
            required = {
                'id': None,
                'student_id': 1,
                'email': 'test@example.com',
                'password_hash': ph.hash('Password123!')
            }
            if key in required:
                return required[key]
            raise KeyError(key)

    login = Login.from_db_row(MockRow())

    assert login.id is None
    assert login.student_id == 1
    assert login.email == 'test@example.com'
    assert login.is_active == 1  # Default
    assert login.role == 'student'  # Default


# ========== create_login_for_student() Tests ==========

def test_create_login_for_student_default_role():
    """Test: create_login_for_student() mit Standard-Rolle"""
    login = create_login_for_student(
        student_id=1,
        email='new@example.com',
        password='SecurePassword123!'
    )

    assert login.student_id == 1
    assert login.email == 'new@example.com'
    assert login.role == 'student'
    assert login.is_active == 1
    assert login.id is None  # Noch nicht in DB


def test_create_login_for_student_custom_role():
    """Test: create_login_for_student() mit Admin-Rolle"""
    login = create_login_for_student(
        student_id=1,
        email='admin@example.com',
        password='AdminPassword123!',
        role='admin'
    )

    assert login.role == 'admin'


def test_create_login_for_student_hashes_password():
    """Test: create_login_for_student() hasht Passwort"""
    password = 'PlainTextPassword123!'
    login = create_login_for_student(
        student_id=1,
        email='test@example.com',
        password=password
    )

    assert login.password_hash != password
    assert login.password_hash.startswith('$argon2')
    assert login.verify_password(password) is True


def test_create_login_for_student_sets_defaults():
    """Test: create_login_for_student() setzt Default-Werte"""
    login = create_login_for_student(
        student_id=1,
        email='test@example.com',
        password='Password123!'
    )

    assert login.is_active == 1
    assert login.must_change_password == 0
    assert login.last_login is None
    assert login.created_at is not None


# ========== String Representation Tests ==========

def test_str_representation(sample_login):
    """Test: __str__() gibt lesbaren String zurück"""
    sample_login.is_active = 1
    str_repr = str(sample_login)

    assert 'Login' in str_repr
    assert 'test@example.com' in str_repr
    assert 'aktiv' in str_repr


def test_str_representation_inactive(sample_login):
    """Test: __str__() zeigt deaktivierten Status"""
    sample_login.is_active = 0
    str_repr = str(sample_login)

    assert 'deaktiviert' in str_repr


def test_repr_representation(sample_login):
    """Test: __repr__() gibt Debug-String zurück"""
    repr_str = repr(sample_login)

    assert 'Login' in repr_str
    assert 'student_id=1' in repr_str
    assert 'test@example.com' in repr_str


# ========== Private Methods Tests ==========

def test_private_get_email_domain(sample_login):
    """Test: __get_email_domain() extrahiert Domain"""
    domain = sample_login._Login__get_email_domain()

    assert domain == 'example.com'


def test_private_is_password_hash_argon2(sample_login):
    """Test: __is_password_hash_argon2() erkennt Argon2"""
    is_argon2 = sample_login._Login__is_password_hash_argon2()

    assert is_argon2 is True


def test_private_calculate_account_age_days(sample_login):
    """Test: __calculate_account_age_days() berechnet Alter"""
    age = sample_login._Login__calculate_account_age_days()

    assert isinstance(age, int)
    assert age >= 0


def test_private_has_logged_in_before_false(sample_login):
    """Test: __has_logged_in_before() gibt False wenn noch nie eingeloggt"""
    sample_login.last_login = None

    has_logged_in = sample_login._Login__has_logged_in_before()

    assert has_logged_in is False


def test_private_has_logged_in_before_true(sample_login):
    """Test: __has_logged_in_before() gibt True wenn schon eingeloggt"""
    sample_login.last_login = datetime.now().isoformat()

    has_logged_in = sample_login._Login__has_logged_in_before()

    assert has_logged_in is True


# ========== Integration Tests ==========

def test_full_login_lifecycle():
    """Test: Vollständiger Login-Lifecycle"""
    # 1. Login erstellen
    login = create_login_for_student(
        student_id=1,
        email='user@example.com',
        password='SecurePassword123!'
    )
    assert login.is_active_account() is True

    # 2. Passwort verifizieren
    assert login.verify_password('SecurePassword123!') is True
    assert login.verify_password('WrongPassword') is False

    # 3. Login durchführen
    login.update_last_login()
    assert login.last_login is not None

    # 4. to_dict
    login_dict = login.to_dict()
    assert 'password_hash' not in login_dict

    # 5. Deaktivieren
    login.is_active = 0
    assert login.is_active_account() is False


def test_admin_vs_student_roles():
    """Test: Admin vs Student Unterscheidung"""
    student = create_login_for_student(
        student_id=1,
        email='student@example.com',
        password='Password123!',
        role='student'
    )

    admin = create_login_for_student(
        student_id=2,
        email='admin@example.com',
        password='Password123!',
        role='admin'
    )

    assert student.is_student() is True
    assert student.is_admin() is False

    assert admin.is_admin() is True
    assert admin.is_student() is False


# ========== Edge Cases ==========

def test_login_with_very_long_email():
    """Test: Login mit sehr langer E-Mail"""
    long_email = 'a' * 100 + '@' + 'b' * 100 + '.com'

    login = Login(
        id=None,
        student_id=1,
        email=long_email,
        password_hash=ph.hash('Password123!'),
        is_active=1,
        role='student'
    )

    assert len(login.email) > 200


def test_login_with_special_chars_in_email():
    """Test: Login mit Sonderzeichen in E-Mail"""
    login = Login(
        id=None,
        student_id=1,
        email='user+tag@example.com',
        password_hash=ph.hash('Password123!'),
        is_active=1,
        role='student'
    )

    assert login.email == 'user+tag@example.com'


def test_password_verification_after_hash_update():
    """Test: Passwort-Verifikation nach Hash-Update"""
    login = create_login_for_student(
        student_id=1,
        email='test@example.com',
        password='OldPassword123!'
    )

    # Passwort ändern
    new_password = 'NewPassword123!'
    login.password_hash = Login.hash_password(new_password)

    # Altes Passwort funktioniert nicht mehr
    assert login.verify_password('OldPassword123!') is False

    # Neues Passwort funktioniert
    assert login.verify_password(new_password) is True