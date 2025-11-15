# tests/unit/test_studiengang.py
"""
Unit Tests für Studiengang Domain Model

Testet die Studiengang-Klasse aus models/studiengang.py
"""
import pytest
import sys
from pathlib import Path

# Füge Project-Root zum Python-Path hinzu
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from models import Studiengang


# ============================================================================
# CREATION & VALIDATION TESTS
# ============================================================================

def test_studiengang_create_valid_bachelor():
    """Test: Gültigen Bachelor-Studiengang erstellen"""
    s = Studiengang(
        id=1,
        name="Informatik",
        grad="B.Sc.",
        regel_semester=6
    )

    assert s.id == 1
    assert s.name == "Informatik"
    assert s.grad == "B.Sc."
    assert s.regel_semester == 6
    assert s.beschreibung is None


def test_studiengang_create_valid_master():
    """Test: Gültigen Master-Studiengang erstellen"""
    s = Studiengang(
        id=2,
        name="Data Science",
        grad="M.Sc.",
        regel_semester=4,
        beschreibung="Master-Studiengang mit Fokus auf KI"
    )

    assert s.id == 2
    assert s.name == "Data Science"
    assert s.grad == "M.Sc."
    assert s.regel_semester == 4
    assert s.beschreibung == "Master-Studiengang mit Fokus auf KI"


def test_studiengang_all_valid_grades():
    """Test: Alle erlaubten Abschlussgrade"""
    valid_grades = ["B.Sc.", "B.A.", "B.Eng.", "M.Sc.", "M.A.", "M.Eng."]

    for idx, grad in enumerate(valid_grades, start=1):
        s = Studiengang(
            id=idx,
            name=f"Studiengang {idx}",
            grad=grad,
            regel_semester=6
        )
        assert s.grad == grad


def test_studiengang_invalid_grad_raises():
    """Test: Ungültiger Grad wirft ValueError"""
    with pytest.raises(ValueError, match="Ungültiger Grad"):
        Studiengang(
            id=1,
            name="Informatik",
            grad="Diplom",  # Ungültig!
            regel_semester=6
        )


def test_studiengang_empty_name_raises():
    """Test: Leerer Name wirft ValueError"""
    with pytest.raises(ValueError, match="darf nicht leer sein"):
        Studiengang(
            id=1,
            name="",  # Leer!
            grad="B.Sc.",
            regel_semester=6
        )


def test_studiengang_whitespace_name_raises():
    """Test: Name nur aus Whitespace wirft ValueError"""
    with pytest.raises(ValueError, match="darf nicht leer sein"):
        Studiengang(
            id=1,
            name="   ",  # Nur Leerzeichen!
            grad="B.Sc.",
            regel_semester=6
        )


def test_studiengang_regel_semester_too_low_raises():
    """Test: Regelsemester < 1 wirft ValueError"""
    with pytest.raises(ValueError, match="muss zwischen 1 und 14 liegen"):
        Studiengang(
            id=1,
            name="Informatik",
            grad="B.Sc.",
            regel_semester=0  # Zu niedrig!
        )


def test_studiengang_regel_semester_too_high_raises():
    """Test: Regelsemester > 14 wirft ValueError"""
    with pytest.raises(ValueError, match="muss zwischen 1 und 14 liegen"):
        Studiengang(
            id=1,
            name="Informatik",
            grad="B.Sc.",
            regel_semester=15  # Zu hoch!
        )


# ============================================================================
# PUBLIC METHOD TESTS
# ============================================================================

def test_get_full_name():
    """Test: get_full_name() gibt Namen mit Grad zurück"""
    s = Studiengang(
        id=1,
        name="Informatik",
        grad="B.Sc.",
        regel_semester=6
    )

    assert s.get_full_name() == "Informatik (B.Sc.)"


def test_is_bachelor_true():
    """Test: is_bachelor() gibt True für Bachelor-Studiengänge"""
    bachelor_grades = ["B.Sc.", "B.A.", "B.Eng."]

    for grad in bachelor_grades:
        s = Studiengang(
            id=1,
            name="Test",
            grad=grad,
            regel_semester=6
        )
        assert s.is_bachelor() is True
        assert s.is_master() is False


def test_is_master_true():
    """Test: is_master() gibt True für Master-Studiengänge"""
    master_grades = ["M.Sc.", "M.A.", "M.Eng."]

    for grad in master_grades:
        s = Studiengang(
            id=1,
            name="Test",
            grad=grad,
            regel_semester=4
        )
        assert s.is_master() is True
        assert s.is_bachelor() is False


def test_get_total_ects_target_bachelor():
    """Test: get_total_ects_target() für 6-semestriges Bachelor"""
    s = Studiengang(
        id=1,
        name="Informatik",
        grad="B.Sc.",
        regel_semester=6
    )

    # 6 Semester * 30 ECTS = 180 ECTS
    assert s.get_total_ects_target() == 180


def test_get_total_ects_target_bachelor_7_semester():
    """Test: get_total_ects_target() für 7-semestriges Bachelor"""
    s = Studiengang(
        id=1,
        name="Maschinenbau",
        grad="B.Eng.",
        regel_semester=7
    )

    # 7 Semester * 30 ECTS = 210 ECTS
    assert s.get_total_ects_target() == 210


def test_get_total_ects_target_master():
    """Test: get_total_ects_target() für 4-semestriges Master"""
    s = Studiengang(
        id=1,
        name="Data Science",
        grad="M.Sc.",
        regel_semester=4
    )

    # 4 Semester * 30 ECTS = 120 ECTS
    assert s.get_total_ects_target() == 120


# ============================================================================
# TO_DICT TESTS
# ============================================================================

def test_to_dict_basic():
    """Test: to_dict() Konvertierung"""
    s = Studiengang(
        id=42,
        name="Informatik",
        grad="B.Sc.",
        regel_semester=6,
        beschreibung="Toller Studiengang"
    )

    data = s.to_dict()

    assert data['id'] == 42
    assert data['name'] == "Informatik"
    assert data['grad'] == "B.Sc."
    assert data['regel_semester'] == 6
    assert data['beschreibung'] == "Toller Studiengang"
    assert data['full_name'] == "Informatik (B.Sc.)"
    assert data['is_bachelor'] is True
    assert data['is_master'] is False
    assert data['total_ects_target'] == 180


def test_to_dict_without_description():
    """Test: to_dict() ohne Beschreibung"""
    s = Studiengang(
        id=1,
        name="Informatik",
        grad="B.Sc.",
        regel_semester=6
    )

    data = s.to_dict()

    assert data['beschreibung'] is None


def test_to_dict_master():
    """Test: to_dict() für Master-Studiengang"""
    s = Studiengang(
        id=1,
        name="Data Science",
        grad="M.Sc.",
        regel_semester=4
    )

    data = s.to_dict()

    assert data['is_bachelor'] is False
    assert data['is_master'] is True
    assert data['total_ects_target'] == 120


# ============================================================================
# FROM_ROW TESTS
# ============================================================================

def test_from_row_basic():
    """Test: from_row() mit Dictionary"""
    row_data = {
        'id': 42,
        'name': 'Informatik',
        'grad': 'B.Sc.',
        'regel_semester': 6,
        'beschreibung': 'Toller Studiengang'
    }

    s = Studiengang.from_row(row_data)

    assert s.id == 42
    assert s.name == "Informatik"
    assert s.grad == "B.Sc."
    assert s.regel_semester == 6
    assert s.beschreibung == "Toller Studiengang"


def test_from_row_without_description():
    """Test: from_row() ohne Beschreibung"""
    row_data = {
        'id': 1,
        'name': 'Informatik',
        'grad': 'B.Sc.',
        'regel_semester': 6
    }

    s = Studiengang.from_row(row_data)

    assert s.beschreibung is None


def test_from_row_master():
    """Test: from_row() für Master-Studiengang"""
    row_data = {
        'id': 2,
        'name': 'Data Science',
        'grad': 'M.Sc.',
        'regel_semester': 4,
        'beschreibung': 'Master mit KI-Fokus'
    }

    s = Studiengang.from_row(row_data)

    assert s.id == 2
    assert s.name == "Data Science"
    assert s.grad == "M.Sc."
    assert s.regel_semester == 4
    assert s.is_master() is True


# ============================================================================
# STRING REPRESENTATION TESTS
# ============================================================================

def test_str_representation():
    """Test: __str__() Methode"""
    s = Studiengang(
        id=1,
        name="Informatik",
        grad="B.Sc.",
        regel_semester=6
    )

    s_str = str(s)

    assert "Studiengang" in s_str
    assert "Informatik (B.Sc.)" in s_str
    assert "6 Semester" in s_str


def test_repr_representation():
    """Test: __repr__() Methode"""
    s = Studiengang(
        id=42,
        name="Informatik",
        grad="B.Sc.",
        regel_semester=6
    )

    s_repr = repr(s)

    assert "Studiengang" in s_repr
    assert "id=42" in s_repr
    assert "name='Informatik'" in s_repr
    assert "grad='B.Sc.'" in s_repr


if __name__ == "__main__":
    pytest.main([__file__, "-v"])