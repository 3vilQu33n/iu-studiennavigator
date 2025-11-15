# tests/unit/test_modulbuchung.py
"""
Unit Tests für Modulbuchung Domain Model

Testet die Modulbuchung-Klasse aus models/modulbuchung.py
"""
import pytest
import sys
from pathlib import Path
from datetime import date

# Füge Project-Root zum Python-Path hinzu
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from models import Modulbuchung


# ============================================================================
# CREATION TESTS
# ============================================================================

def test_modulbuchung_create_valid():
    """Test: Gültige Modulbuchung erstellen"""
    mb = Modulbuchung(
        id=1,
        einschreibung_id=100,
        modul_id=42,
        buchungsdatum=date(2024, 1, 15),
        status="gebucht"
    )

    assert mb.id == 1
    assert mb.einschreibung_id == 100
    assert mb.modul_id == 42
    assert mb.buchungsdatum == date(2024, 1, 15)
    assert mb.status == "gebucht"


def test_modulbuchung_create_with_string_date():
    """Test: Modulbuchung mit String-Datum erstellen"""
    mb = Modulbuchung(
        id=1,
        einschreibung_id=100,
        modul_id=42,
        buchungsdatum="2024-01-15",  # String!
        status="gebucht"
    )

    assert isinstance(mb.buchungsdatum, date)
    assert mb.buchungsdatum == date(2024, 1, 15)


def test_modulbuchung_without_date():
    """Test: Modulbuchung ohne Datum (NULL)"""
    mb = Modulbuchung(
        id=1,
        einschreibung_id=100,
        modul_id=42,
        buchungsdatum=None,
        status="gebucht"
    )

    assert mb.buchungsdatum is None


# ============================================================================
# STATUS TESTS
# ============================================================================

def test_is_open():
    """Test: is_open() für gebuchtes Modul"""
    mb = Modulbuchung(1, 100, 42, date(2024, 1, 15), "gebucht")

    assert mb.is_open() is True


def test_is_not_open():
    """Test: is_open() für bestandenes Modul"""
    mb = Modulbuchung(1, 100, 42, date(2024, 1, 15), "bestanden")

    assert mb.is_open() is False


def test_is_passed():
    """Test: is_passed() für bestandenes Modul"""
    mb = Modulbuchung(1, 100, 42, date(2024, 1, 15), "bestanden")

    assert mb.is_passed() is True


def test_is_not_passed():
    """Test: is_passed() für gebuchtes Modul"""
    mb = Modulbuchung(1, 100, 42, date(2024, 1, 15), "gebucht")

    assert mb.is_passed() is False


def test_is_recognized():
    """Test: is_recognized() für anerkanntes Modul"""
    mb = Modulbuchung(1, 100, 42, date(2024, 1, 15), "anerkannt")

    assert mb.is_recognized() is True


def test_is_not_recognized():
    """Test: is_recognized() für reguläres Modul"""
    mb = Modulbuchung(1, 100, 42, date(2024, 1, 15), "bestanden")

    assert mb.is_recognized() is False


# ============================================================================
# TO_DICT TESTS
# ============================================================================

def test_to_dict():
    """Test: to_dict() Konvertierung"""
    mb = Modulbuchung(
        id=1,
        einschreibung_id=100,
        modul_id=42,
        buchungsdatum=date(2024, 1, 15),
        status="bestanden"
    )

    data = mb.to_dict()

    assert data['id'] == 1
    assert data['einschreibung_id'] == 100
    assert data['modul_id'] == 42
    assert data['buchungsdatum'] == "2024-01-15"
    assert data['status'] == "bestanden"
    assert data['is_open'] is False
    assert data['is_passed'] is True
    assert data['is_recognized'] is False


def test_to_dict_without_date():
    """Test: to_dict() ohne Buchungsdatum"""
    mb = Modulbuchung(
        id=1,
        einschreibung_id=100,
        modul_id=42,
        buchungsdatum=None,
        status="gebucht"
    )

    data = mb.to_dict()

    assert data['buchungsdatum'] is None


# ============================================================================
# FROM_ROW TESTS
# ============================================================================

def test_from_row_with_date():
    """Test: from_row() mit Date-Objekt"""
    row_data = {
        'id': 1,
        'einschreibung_id': 100,
        'modul_id': 42,
        'buchungsdatum': date(2024, 1, 15),
        'status': 'gebucht'
    }

    mb = Modulbuchung.from_row(row_data)

    assert mb.id == 1
    assert mb.einschreibung_id == 100
    assert mb.modul_id == 42
    assert mb.buchungsdatum == date(2024, 1, 15)
    assert mb.status == "gebucht"


def test_from_row_with_string_date():
    """Test: from_row() mit String-Datum"""
    row_data = {
        'id': 1,
        'einschreibung_id': 100,
        'modul_id': 42,
        'buchungsdatum': '2024-01-15',
        'status': 'gebucht'
    }

    mb = Modulbuchung.from_row(row_data)

    assert isinstance(mb.buchungsdatum, date)
    assert mb.buchungsdatum == date(2024, 1, 15)


def test_from_row_without_date():
    """Test: from_row() ohne Datum (NULL)"""
    row_data = {
        'id': 1,
        'einschreibung_id': 100,
        'modul_id': 42,
        'buchungsdatum': None,
        'status': 'gebucht'
    }

    mb = Modulbuchung.from_row(row_data)

    assert mb.buchungsdatum is None


# ============================================================================
# STRING REPRESENTATION TESTS
# ============================================================================

def test_str_representation():
    """Test: __str__() Methode"""
    mb = Modulbuchung(1, 100, 42, date(2024, 1, 15), "bestanden")

    mb_str = str(mb)

    assert "Modulbuchung" in mb_str
    assert "42" in mb_str
    assert "bestanden" in mb_str


def test_repr_representation():
    """Test: __repr__() Methode"""
    mb = Modulbuchung(1, 100, 42, date(2024, 1, 15), "gebucht")

    mb_repr = repr(mb)

    assert "Modulbuchung" in mb_repr
    assert "id=1" in mb_repr
    assert "modul_id=42" in mb_repr
    assert "gebucht" in mb_repr


if __name__ == "__main__":
    pytest.main([__file__, "-v"])