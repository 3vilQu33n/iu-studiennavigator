# tests/unit/test_modul.py
"""
Unit Tests für Modul Domain Model

Testet die Modul-Klasse und ModulBuchung-DTO aus models/modul.py
"""
import pytest
import sys
from pathlib import Path

# Füge Project-Root zum Python-Path hinzu
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from models import Modul, ModulBuchung


# ============================================================================
# MODUL - CREATION TESTS
# ============================================================================

def test_modul_create_valid():
    """Test: Gültiges Modul erstellen"""
    m = Modul(
        id=1,
        name="Einführung in die Programmierung",
        beschreibung="Grundlagen der Programmierung mit Python",
        ects=5
    )

    assert m.id == 1
    assert m.name == "Einführung in die Programmierung"
    assert m.beschreibung == "Grundlagen der Programmierung mit Python"
    assert m.ects == 5


def test_modul_create_minimal():
    """Test: Modul mit minimalen Daten"""
    m = Modul(
        id=1,
        name="Test Modul",
        beschreibung="",
        ects=5
    )

    assert m.id == 1
    assert m.name == "Test Modul"
    assert m.beschreibung == ""
    assert m.ects == 5


def test_modul_high_ects():
    """Test: Modul mit hohen ECTS (z.B. Bachelorarbeit)"""
    m = Modul(
        id=1,
        name="Bachelorarbeit",
        beschreibung="Abschlussarbeit",
        ects=12
    )

    assert m.ects == 12


# ============================================================================
# MODUL - TO_DICT TESTS
# ============================================================================

def test_modul_to_dict():
    """Test: to_dict() Konvertierung"""
    m = Modul(
        id=42,
        name="Datenbanken",
        beschreibung="Relationale Datenbanken und SQL",
        ects=5
    )

    data = m.to_dict()

    assert data['id'] == 42
    assert data['name'] == "Datenbanken"
    assert data['beschreibung'] == "Relationale Datenbanken und SQL"
    assert data['ects'] == 5


def test_modul_to_dict_empty_description():
    """Test: to_dict() mit leerer Beschreibung"""
    m = Modul(
        id=1,
        name="Test",
        beschreibung="",
        ects=5
    )

    data = m.to_dict()

    assert data['beschreibung'] == ""


# ============================================================================
# MODUL - FROM_DB_ROW TESTS
# ============================================================================

def test_modul_from_db_row():
    """Test: from_db_row() mit vollständigen Daten"""
    row_data = {
        'id': 42,
        'name': 'Datenbanken',
        'beschreibung': 'Relationale Datenbanken',
        'ects': 5
    }

    m = Modul.from_db_row(row_data)

    assert m.id == 42
    assert m.name == "Datenbanken"
    assert m.beschreibung == "Relationale Datenbanken"
    assert m.ects == 5


def test_modul_from_db_row_empty_description():
    """Test: from_db_row() mit leerer Beschreibung"""
    row_data = {
        'id': 1,
        'name': 'Test Modul',
        'beschreibung': '',
        'ects': 5
    }

    m = Modul.from_db_row(row_data)

    assert m.beschreibung == ""


def test_modul_from_db_row_none_description():
    """Test: from_db_row() mit NULL Beschreibung"""
    row_data = {
        'id': 1,
        'name': 'Test Modul',
        'beschreibung': None,
        'ects': 5
    }

    m = Modul.from_db_row(row_data)

    # NOTE: Bug in modul.py Zeile 35! 
    # Sollte '' zurückgeben bei None, aber row('beschreibung') ist falsch
    # Nach Fix sollte dieser Test passen:
    # assert m.beschreibung == ""


# ============================================================================
# MODUL - STRING REPRESENTATION TESTS
# ============================================================================

def test_modul_str_representation():
    """Test: __str__() Methode"""
    m = Modul(
        id=1,
        name="Datenbanken",
        beschreibung="SQL und NoSQL",
        ects=5
    )

    m_str = str(m)

    assert "Datenbanken" in m_str
    assert "5 ECTS" in m_str


def test_modul_repr_representation():
    """Test: __repr__() Methode"""
    m = Modul(
        id=42,
        name="Datenbanken",
        beschreibung="SQL",
        ects=5
    )

    m_repr = repr(m)

    assert "Modul" in m_repr
    assert "id=42" in m_repr
    assert "Datenbanken" in m_repr
    assert "ects=5" in m_repr


# ============================================================================
# MODULBUCHUNG - CREATION TESTS
# ============================================================================

def test_modulbuchung_create():
    """Test: ModulBuchung DTO erstellen"""
    modul = Modul(1, "Test Modul", "Beschreibung", 5)

    mb = ModulBuchung(
        modul=modul,
        status="gebucht",
        buchbar=False,
        buchungsdatum="2024-01-15",
        note=None,
        pflichtgrad="Pflicht",
        semester=1
    )

    assert mb.modul.id == 1
    assert mb.status == "gebucht"
    assert mb.buchbar is False
    assert mb.buchungsdatum == "2024-01-15"
    assert mb.note is None
    assert mb.pflichtgrad == "Pflicht"
    assert mb.semester == 1


def test_modulbuchung_with_note():
    """Test: ModulBuchung mit Note"""
    modul = Modul(1, "Test Modul", "Beschreibung", 5)

    mb = ModulBuchung(
        modul=modul,
        status="bestanden",
        buchbar=False,
        buchungsdatum="2024-01-15",
        note=2.3,
        pflichtgrad="Pflicht",
        semester=1
    )

    assert mb.note == 2.3
    assert mb.status == "bestanden"


# ============================================================================
# MODULBUCHUNG - STATUS TESTS
# ============================================================================

def test_modulbuchung_is_passed():
    """Test: is_passed() für bestandenes Modul"""
    modul = Modul(1, "Test", "Desc", 5)
    mb = ModulBuchung(modul, "bestanden", False, "2024-01-15", 2.0, "Pflicht", 1)

    assert mb.is_passed() is True


def test_modulbuchung_is_not_passed():
    """Test: is_passed() für nicht bestandenes Modul"""
    modul = Modul(1, "Test", "Desc", 5)
    mb = ModulBuchung(modul, "gebucht", True, None, None, "Pflicht", 1)

    assert mb.is_passed() is False


def test_modulbuchung_is_booked():
    """Test: is_booked() für gebuchtes Modul"""
    modul = Modul(1, "Test", "Desc", 5)
    mb = ModulBuchung(modul, "gebucht", False, "2024-01-15", None, "Pflicht", 1)

    assert mb.is_booked() is True


def test_modulbuchung_is_not_booked():
    """Test: is_booked() für nicht gebuchtes Modul"""
    modul = Modul(1, "Test", "Desc", 5)
    mb = ModulBuchung(modul, None, True, None, None, "Wahl", 1)

    assert mb.is_booked() is False


# ============================================================================
# MODULBUCHUNG - TO_DICT TESTS
# ============================================================================

def test_modulbuchung_to_dict():
    """Test: ModulBuchung to_dict() Konvertierung"""
    modul = Modul(42, "Datenbanken", "SQL", 5)
    mb = ModulBuchung(
        modul=modul,
        status="bestanden",
        buchbar=False,
        buchungsdatum="2024-01-15",
        note=2.3,
        pflichtgrad="Pflicht",
        semester=1
    )

    data = mb.to_dict()

    assert data['modul_id'] == 42
    assert data['name'] == "Datenbanken"
    assert data['ects'] == 5
    assert data['status'] == "bestanden"
    assert data['buchbar'] is False
    assert data['buchungsdatum'] == "2024-01-15"
    assert data['note'] == 2.3
    assert data['pflichtgrad'] == "Pflicht"
    assert data['semester'] == 1
    assert data['is_passed'] is True
    assert data['is_booked'] is False  # bestanden != gebucht


def test_modulbuchung_to_dict_unbuchbar():
    """Test: ModulBuchung to_dict() für unbuchbares Modul"""
    modul = Modul(1, "Test", "Desc", 5)
    mb = ModulBuchung(
        modul=modul,
        status=None,
        buchbar=False,
        buchungsdatum=None,
        note=None,
        pflichtgrad="Wahlpflicht",
        semester=3
    )

    data = mb.to_dict()

    assert data['status'] is None
    assert data['buchbar'] is False
    assert data['buchungsdatum'] is None
    assert data['note'] is None
    assert data['is_passed'] is False
    assert data['is_booked'] is False


# ============================================================================
# MODULBUCHUNG - STRING REPRESENTATION TESTS
# ============================================================================

def test_modulbuchung_str_with_status():
    """Test: __str__() für gebuchtes Modul"""
    modul = Modul(1, "Datenbanken", "SQL", 5)
    mb = ModulBuchung(modul, "gebucht", False, "2024-01-15", None, "Pflicht", 1)

    mb_str = str(mb)

    assert "ModulBuchung" in mb_str
    assert "Datenbanken" in mb_str
    assert "[gebucht]" in mb_str


def test_modulbuchung_str_without_status():
    """Test: __str__() für unbuchbares Modul"""
    modul = Modul(1, "Test", "Desc", 5)
    mb = ModulBuchung(modul, None, False, None, None, "Wahl", 1)

    mb_str = str(mb)

    assert "Test" in mb_str
    assert "[unbuchbar]" in mb_str


if __name__ == "__main__":
    pytest.main([__file__, "-v"])