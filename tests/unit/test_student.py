# tests/unit/test_student.py
"""
Unit Tests für Student Domain Model

Testet die Student-Klasse aus models/student.py
BEREINIGT: email und eingeschrieben_seit entfernt
"""
import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from models import Student


# ============================================================================
# CREATION & VALIDATION TESTS
# ============================================================================

def test_student_create_valid():
    """Test: Gültigen Student erstellen"""
    s = Student(
        id=1,
        matrikel_nr="IU12345",
        vorname="Max",
        nachname="Mustermann",
        login_id=10
    )

    assert s.id == 1
    assert s.matrikel_nr == "IU12345"
    assert s.vorname == "Max"
    assert s.nachname == "Mustermann"
    assert s.login_id == 10


def test_student_without_login_id():
    """Test: Student ohne login_id (optional)"""
    s = Student(
        id=1,
        matrikel_nr="IU12345",
        vorname="Max",
        nachname="Mustermann"
    )

    assert s.login_id is None


# ============================================================================
# VALIDATION TESTS
# ============================================================================

def test_validate_valid_student():
    """Test: Validierung erfolgreich für gültigen Student"""
    s = Student(
        id=1,
        matrikel_nr="IU12345",
        vorname="Max",
        nachname="Mustermann"
    )

    valid, msg = s.validate()

    assert valid is True
    assert msg == ""


def test_validate_matrikel_nr_too_short():
    """Test: Validierung schlägt fehl bei zu kurzer Matrikelnummer"""
    s = Student(
        id=1,
        matrikel_nr="IU1",  # Nur 3 Zeichen!
        vorname="Max",
        nachname="Mustermann"
    )

    valid, msg = s.validate()

    assert valid is False
    assert "mindestens 5 zeichen" in msg.lower()


def test_validate_missing_vorname():
    """Test: Validierung schlägt fehl bei fehlendem Vornamen"""
    s = Student(
        id=1,
        matrikel_nr="IU12345",
        vorname="",  # Leer!
        nachname="Mustermann"
    )

    valid, msg = s.validate()

    assert valid is False
    assert "nachname" in msg.lower()


# ============================================================================
# PUBLIC METHODS TESTS
# ============================================================================

def test_get_full_name():
    """Test: get_full_name() gibt vollständigen Namen zurück"""
    s = Student(
        id=1,
        matrikel_nr="IU12345",
        vorname="Max",
        nachname="Mustermann"
    )

    assert s.get_full_name() == "Max Mustermann"


# ============================================================================
# TO_DICT TESTS
# ============================================================================

def test_to_dict():
    """Test: to_dict() Konvertierung"""
    s = Student(
        id=42,
        matrikel_nr="IU12345",
        vorname="Max",
        nachname="Mustermann",
        login_id=10
    )

    data = s.to_dict()

    assert data['id'] == 42
    assert data['matrikel_nr'] == "IU12345"
    assert data['vorname'] == "Max"
    assert data['nachname'] == "Mustermann"
    assert data['full_name'] == "Max Mustermann"
    assert data['login_id'] == 10


def test_to_dict_without_login_id():
    """Test: to_dict() ohne login_id"""
    s = Student(
        id=1,
        matrikel_nr="IU12345",
        vorname="Max",
        nachname="Mustermann"
    )

    data = s.to_dict()

    assert data['login_id'] is None


# ============================================================================
# FROM_DB_ROW TESTS
# ============================================================================

def test_from_db_row_with_dict():
    """Test: from_db_row() mit Dictionary"""
    row_data = {
        'id': 42,
        'matrikel_nr': 'IU12345',
        'vorname': 'Max',
        'nachname': 'Mustermann',
        'login_id': 10
    }

    s = Student.from_db_row(row_data)

    assert s.id == 42
    assert s.matrikel_nr == "IU12345"
    assert s.vorname == "Max"
    assert s.nachname == "Mustermann"
    assert s.login_id == 10


def test_from_db_row_without_login_id():
    """Test: from_db_row() ohne login_id (NULL)"""
    row_data = {
        'id': 1,
        'matrikel_nr': 'IU12345',
        'vorname': 'Max',
        'nachname': 'Mustermann',
        'login_id': None  # NULL!
    }

    s = Student.from_db_row(row_data)

    assert s.login_id is None


# ============================================================================
# STRING REPRESENTATION TESTS
# ============================================================================

def test_str_representation():
    """Test: __str__() Methode"""
    s = Student(
        id=1,
        matrikel_nr="IU12345",
        vorname="Max",
        nachname="Mustermann"
    )

    s_str = str(s)

    assert "IU12345" in s_str
    assert "Max Mustermann" in s_str


def test_repr_representation():
    """Test: __repr__() Methode"""
    s = Student(
        id=1,
        matrikel_nr="IU12345",
        vorname="Max",
        nachname="Mustermann"
    )

    s_repr = repr(s)

    assert "Student" in s_repr
    assert "id=1" in s_repr
    assert "IU12345" in s_repr
    assert "Max Mustermann" in s_repr


if __name__ == "__main__":
    pytest.main([__file__, "-v"])