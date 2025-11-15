# tests/unit/test_studiengang_modul.py
"""
Unit Tests für StudiengangModul Domain Model

Testet die StudiengangModul-Klasse aus models/studiengang_modul.py
"""
import pytest
import sys
from pathlib import Path

# Füge Project-Root zum Python-Path hinzu
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from models import StudiengangModul


# ============================================================================
# CREATION & VALIDATION TESTS
# ============================================================================

def test_studiengang_modul_create_valid_pflicht():
    """Test: Gültiges Pflichtmodul erstellen"""
    sm = StudiengangModul(
        studiengang_id=1,
        modul_id=10,
        semester=3,
        pflichtgrad="Pflicht"
    )

    assert sm.studiengang_id == 1
    assert sm.modul_id == 10
    assert sm.semester == 3
    assert sm.pflichtgrad == "Pflicht"


def test_studiengang_modul_create_valid_wahlpflicht():
    """Test: Gültiges Wahlpflichtmodul erstellen"""
    sm = StudiengangModul(
        studiengang_id=1,
        modul_id=20,
        semester=5,
        pflichtgrad="Wahlpflicht"
    )

    assert sm.pflichtgrad == "Wahlpflicht"


def test_studiengang_modul_create_valid_wahl():
    """Test: Gültiges Wahlmodul erstellen"""
    sm = StudiengangModul(
        studiengang_id=1,
        modul_id=30,
        semester=6,
        pflichtgrad="Wahl"
    )

    assert sm.pflichtgrad == "Wahl"


def test_studiengang_modul_all_valid_pflichtgrade():
    """Test: Alle erlaubten Pflichtgrade"""
    valid_pflichtgrade = ["Pflicht", "Wahlpflicht", "Wahl"]

    for pflichtgrad in valid_pflichtgrade:
        sm = StudiengangModul(
            studiengang_id=1,
            modul_id=10,
            semester=3,
            pflichtgrad=pflichtgrad
        )
        assert sm.pflichtgrad == pflichtgrad


def test_studiengang_modul_invalid_studiengang_id_raises():
    """Test: Ungültige studiengang_id wirft ValueError"""
    with pytest.raises(ValueError, match="studiengang_id muss positiv sein"):
        StudiengangModul(
            studiengang_id=0,  # Ungültig!
            modul_id=10,
            semester=3,
            pflichtgrad="Pflicht"
        )


def test_studiengang_modul_invalid_modul_id_raises():
    """Test: Ungültige modul_id wirft ValueError"""
    with pytest.raises(ValueError, match="modul_id muss positiv sein"):
        StudiengangModul(
            studiengang_id=1,
            modul_id=-5,  # Ungültig!
            semester=3,
            pflichtgrad="Pflicht"
        )


def test_studiengang_modul_invalid_semester_too_low_raises():
    """Test: Semester < 1 wirft ValueError"""
    with pytest.raises(ValueError, match="muss zwischen 1 und 14 liegen"):
        StudiengangModul(
            studiengang_id=1,
            modul_id=10,
            semester=0,  # Zu niedrig!
            pflichtgrad="Pflicht"
        )


def test_studiengang_modul_invalid_semester_too_high_raises():
    """Test: Semester > 14 wirft ValueError"""
    with pytest.raises(ValueError, match="muss zwischen 1 und 14 liegen"):
        StudiengangModul(
            studiengang_id=1,
            modul_id=10,
            semester=15,  # Zu hoch!
            pflichtgrad="Pflicht"
        )


def test_studiengang_modul_invalid_pflichtgrad_raises():
    """Test: Ungültiger Pflichtgrad wirft ValueError"""
    with pytest.raises(ValueError, match="Ungültiger Pflichtgrad"):
        StudiengangModul(
            studiengang_id=1,
            modul_id=10,
            semester=3,
            pflichtgrad="Optional"  # Ungültig!
        )


# ============================================================================
# PUBLIC METHOD TESTS
# ============================================================================

def test_is_pflicht_true():
    """Test: is_pflicht() gibt True für Pflichtmodul"""
    sm = StudiengangModul(
        studiengang_id=1,
        modul_id=10,
        semester=3,
        pflichtgrad="Pflicht"
    )

    assert sm.is_pflicht() is True
    assert sm.is_wahlpflicht() is False
    assert sm.is_wahl() is False


def test_is_wahlpflicht_true():
    """Test: is_wahlpflicht() gibt True für Wahlpflichtmodul"""
    sm = StudiengangModul(
        studiengang_id=1,
        modul_id=20,
        semester=5,
        pflichtgrad="Wahlpflicht"
    )

    assert sm.is_pflicht() is False
    assert sm.is_wahlpflicht() is True
    assert sm.is_wahl() is False


def test_is_wahl_true():
    """Test: is_wahl() gibt True für Wahlmodul"""
    sm = StudiengangModul(
        studiengang_id=1,
        modul_id=30,
        semester=6,
        pflichtgrad="Wahl"
    )

    assert sm.is_pflicht() is False
    assert sm.is_wahlpflicht() is False
    assert sm.is_wahl() is True


def test_is_mandatory_pflicht():
    """Test: is_mandatory() gibt True für Pflichtmodul"""
    sm = StudiengangModul(
        studiengang_id=1,
        modul_id=10,
        semester=3,
        pflichtgrad="Pflicht"
    )

    assert sm.is_mandatory() is True


def test_is_mandatory_wahlpflicht():
    """Test: is_mandatory() gibt True für Wahlpflichtmodul"""
    sm = StudiengangModul(
        studiengang_id=1,
        modul_id=20,
        semester=5,
        pflichtgrad="Wahlpflicht"
    )

    assert sm.is_mandatory() is True


def test_is_mandatory_wahl_false():
    """Test: is_mandatory() gibt False für Wahlmodul"""
    sm = StudiengangModul(
        studiengang_id=1,
        modul_id=30,
        semester=6,
        pflichtgrad="Wahl"
    )

    assert sm.is_mandatory() is False


# ============================================================================
# TO_DICT TESTS
# ============================================================================

def test_to_dict_pflicht():
    """Test: to_dict() für Pflichtmodul"""
    sm = StudiengangModul(
        studiengang_id=1,
        modul_id=10,
        semester=3,
        pflichtgrad="Pflicht"
    )

    data = sm.to_dict()

    assert data['studiengang_id'] == 1
    assert data['modul_id'] == 10
    assert data['semester'] == 3
    assert data['pflichtgrad'] == "Pflicht"
    assert data['is_pflicht'] is True
    assert data['is_wahlpflicht'] is False
    assert data['is_wahl'] is False
    assert data['is_mandatory'] is True


def test_to_dict_wahlpflicht():
    """Test: to_dict() für Wahlpflichtmodul"""
    sm = StudiengangModul(
        studiengang_id=1,
        modul_id=20,
        semester=5,
        pflichtgrad="Wahlpflicht"
    )

    data = sm.to_dict()

    assert data['pflichtgrad'] == "Wahlpflicht"
    assert data['is_pflicht'] is False
    assert data['is_wahlpflicht'] is True
    assert data['is_wahl'] is False
    assert data['is_mandatory'] is True


def test_to_dict_wahl():
    """Test: to_dict() für Wahlmodul"""
    sm = StudiengangModul(
        studiengang_id=1,
        modul_id=30,
        semester=6,
        pflichtgrad="Wahl"
    )

    data = sm.to_dict()

    assert data['pflichtgrad'] == "Wahl"
    assert data['is_pflicht'] is False
    assert data['is_wahlpflicht'] is False
    assert data['is_wahl'] is True
    assert data['is_mandatory'] is False


# ============================================================================
# FROM_ROW TESTS
# ============================================================================

def test_from_row_basic():
    """Test: from_row() mit Dictionary"""
    row_data = {
        'studiengang_id': 1,
        'modul_id': 10,
        'semester': 3,
        'pflichtgrad': 'Pflicht'
    }

    sm = StudiengangModul.from_row(row_data)

    assert sm.studiengang_id == 1
    assert sm.modul_id == 10
    assert sm.semester == 3
    assert sm.pflichtgrad == "Pflicht"


def test_from_row_wahlpflicht():
    """Test: from_row() für Wahlpflichtmodul"""
    row_data = {
        'studiengang_id': 2,
        'modul_id': 20,
        'semester': 5,
        'pflichtgrad': 'Wahlpflicht'
    }

    sm = StudiengangModul.from_row(row_data)

    assert sm.pflichtgrad == "Wahlpflicht"
    assert sm.is_wahlpflicht() is True


def test_from_row_wahl():
    """Test: from_row() für Wahlmodul"""
    row_data = {
        'studiengang_id': 3,
        'modul_id': 30,
        'semester': 6,
        'pflichtgrad': 'Wahl'
    }

    sm = StudiengangModul.from_row(row_data)

    assert sm.pflichtgrad == "Wahl"
    assert sm.is_wahl() is True


# ============================================================================
# EDGE CASE TESTS
# ============================================================================

def test_studiengang_modul_first_semester():
    """Test: Modul im ersten Semester"""
    sm = StudiengangModul(
        studiengang_id=1,
        modul_id=10,
        semester=1,
        pflichtgrad="Pflicht"
    )

    assert sm.semester == 1


def test_studiengang_modul_last_semester():
    """Test: Modul im letzten Semester (14)"""
    sm = StudiengangModul(
        studiengang_id=1,
        modul_id=10,
        semester=14,
        pflichtgrad="Pflicht"
    )

    assert sm.semester == 14


def test_studiengang_modul_typical_bachelor_semesters():
    """Test: Typische Bachelor-Semester (1-7)"""
    for sem in range(1, 8):
        sm = StudiengangModul(
            studiengang_id=1,
            modul_id=10,
            semester=sem,
            pflichtgrad="Pflicht"
        )
        assert sm.semester == sem


# ============================================================================
# STRING REPRESENTATION TESTS
# ============================================================================

def test_str_representation():
    """Test: __str__() Methode"""
    sm = StudiengangModul(
        studiengang_id=1,
        modul_id=42,
        semester=3,
        pflichtgrad="Pflicht"
    )

    s = str(sm)

    assert "StudiengangModul" in s
    assert "Studiengang 1" in s
    assert "Modul 42" in s
    assert "Sem 3" in s
    assert "Pflicht" in s


def test_repr_representation():
    """Test: __repr__() Methode"""
    sm = StudiengangModul(
        studiengang_id=1,
        modul_id=42,
        semester=3,
        pflichtgrad="Wahlpflicht"
    )

    r = repr(sm)

    assert "StudiengangModul" in r
    assert "studiengang_id=1" in r
    assert "modul_id=42" in r
    assert "semester=3" in r
    assert "pflichtgrad='Wahlpflicht'" in r


if __name__ == "__main__":
    pytest.main([__file__, "-v"])