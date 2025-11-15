# tests/unit/test_pruefungsleistung.py
"""
Unit Tests für Pruefungsleistung Domain Model

Testet die Pruefungsleistung-Klasse (erbt von Modulbuchung)
aus models/pruefungsleistung.py
"""
import pytest
import sys
from pathlib import Path
from datetime import date
from decimal import Decimal

# Füge Project-Root zum Python-Path hinzu
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from models import Pruefungsleistung


# ============================================================================
# CREATION TESTS
# ============================================================================

def test_pruefungsleistung_create_valid():
    """Test: Gültige Prüfungsleistung erstellen"""
    pl = Pruefungsleistung(
        id=1,
        einschreibung_id=100,
        modul_id=42,
        buchungsdatum=date(2024, 1, 15),
        status="bestanden",
        note=Decimal("2.3"),
        pruefungsdatum=date(2024, 2, 1),
        versuch=1,
        max_versuche=3,
        anmeldemodus="online",
        thema=None
    )

    assert pl.id == 1
    assert pl.einschreibung_id == 100
    assert pl.modul_id == 42
    assert pl.status == "bestanden"
    assert pl.note == Decimal("2.3")
    assert pl.pruefungsdatum == date(2024, 2, 1)
    assert pl.versuch == 1
    assert pl.max_versuche == 3
    assert pl.anmeldemodus == "online"
    assert pl.thema is None


def test_pruefungsleistung_with_float_note():
    """Test: Prüfungsleistung mit float-Note (wird zu Decimal)"""
    pl = Pruefungsleistung(
        id=1,
        einschreibung_id=100,
        modul_id=42,
        buchungsdatum=date(2024, 1, 15),
        status="bestanden",
        note=2.3,  # Float!
        pruefungsdatum=date(2024, 2, 1),
        versuch=1
    )

    assert isinstance(pl.note, Decimal)
    assert pl.note == Decimal("2.3")


def test_pruefungsleistung_without_note():
    """Test: Prüfungsleistung ohne Note (angemeldet aber nicht bewertet)"""
    pl = Pruefungsleistung(
        id=1,
        einschreibung_id=100,
        modul_id=42,
        buchungsdatum=date(2024, 1, 15),
        status="gebucht",
        note=None,
        pruefungsdatum=date(2024, 2, 1),
        versuch=1
    )

    assert pl.note is None
    assert pl.has_grade() is False


def test_pruefungsleistung_with_thema():
    """Test: Prüfungsleistung mit Thema (z.B. Bachelorarbeit)"""
    pl = Pruefungsleistung(
        id=1,
        einschreibung_id=100,
        modul_id=42,
        buchungsdatum=date(2024, 1, 15),
        status="bestanden",
        note=Decimal("1.7"),
        pruefungsdatum=date(2024, 2, 1),
        versuch=1,
        max_versuche=3,
        anmeldemodus="online",
        thema="Implementierung eines REST-APIs mit FastAPI"
    )

    assert pl.thema == "Implementierung eines REST-APIs mit FastAPI"


# ============================================================================
# NOTE & GRADE TESTS
# ============================================================================

def test_has_grade_true():
    """Test: has_grade() für Prüfung mit Note"""
    pl = Pruefungsleistung(
        id=1, einschreibung_id=100, modul_id=42,
        buchungsdatum=date(2024, 1, 15), status="bestanden",
        note=Decimal("2.0"), pruefungsdatum=date(2024, 2, 1), versuch=1
    )

    assert pl.has_grade() is True


def test_has_grade_false():
    """Test: has_grade() für Prüfung ohne Note"""
    pl = Pruefungsleistung(
        id=1, einschreibung_id=100, modul_id=42,
        buchungsdatum=date(2024, 1, 15), status="gebucht",
        note=None, pruefungsdatum=date(2024, 2, 1), versuch=1
    )

    assert pl.has_grade() is False


def test_is_passed_with_good_note():
    """Test: is_passed() überschreibt Basisklasse - Note <= 4.0"""
    pl = Pruefungsleistung(
        id=1, einschreibung_id=100, modul_id=42,
        buchungsdatum=date(2024, 1, 15), status="bestanden",
        note=Decimal("3.7"), pruefungsdatum=date(2024, 2, 1), versuch=1
    )

    assert pl.is_passed() is True


def test_is_passed_with_failing_note():
    """Test: is_passed() für Note > 4.0 (durchgefallen)"""
    pl = Pruefungsleistung(
        id=1, einschreibung_id=100, modul_id=42,
        buchungsdatum=date(2024, 1, 15), status="nicht_bestanden",
        note=Decimal("5.0"), pruefungsdatum=date(2024, 2, 1), versuch=1
    )

    assert pl.is_passed() is False


def test_is_passed_without_note():
    """Test: is_passed() ohne Note = False"""
    pl = Pruefungsleistung(
        id=1, einschreibung_id=100, modul_id=42,
        buchungsdatum=date(2024, 1, 15), status="gebucht",
        note=None, pruefungsdatum=date(2024, 2, 1), versuch=1
    )

    assert pl.is_passed() is False


def test_get_grade_category_sehr_gut():
    """Test: get_grade_category() für Note <= 2.0"""
    pl = Pruefungsleistung(
        id=1, einschreibung_id=100, modul_id=42,
        buchungsdatum=date(2024, 1, 15), status="bestanden",
        note=Decimal("1.3"), pruefungsdatum=date(2024, 2, 1), versuch=1
    )

    assert pl.get_grade_category() == "sehr_gut"


def test_get_grade_category_gut():
    """Test: get_grade_category() für Note 2.1-3.0"""
    pl = Pruefungsleistung(
        id=1, einschreibung_id=100, modul_id=42,
        buchungsdatum=date(2024, 1, 15), status="bestanden",
        note=Decimal("2.7"), pruefungsdatum=date(2024, 2, 1), versuch=1
    )

    assert pl.get_grade_category() == "gut"


def test_get_grade_category_bestanden():
    """Test: get_grade_category() für Note 3.1-4.0"""
    pl = Pruefungsleistung(
        id=1, einschreibung_id=100, modul_id=42,
        buchungsdatum=date(2024, 1, 15), status="bestanden",
        note=Decimal("3.7"), pruefungsdatum=date(2024, 2, 1), versuch=1
    )

    assert pl.get_grade_category() == "bestanden"


def test_get_grade_category_nicht_bestanden():
    """Test: get_grade_category() für Note > 4.0"""
    pl = Pruefungsleistung(
        id=1, einschreibung_id=100, modul_id=42,
        buchungsdatum=date(2024, 1, 15), status="nicht_bestanden",
        note=Decimal("5.0"), pruefungsdatum=date(2024, 2, 1), versuch=1
    )

    assert pl.get_grade_category() == "nicht_bestanden"


def test_get_grade_category_keine_note():
    """Test: get_grade_category() ohne Note"""
    pl = Pruefungsleistung(
        id=1, einschreibung_id=100, modul_id=42,
        buchungsdatum=date(2024, 1, 15), status="gebucht",
        note=None, pruefungsdatum=date(2024, 2, 1), versuch=1
    )

    assert pl.get_grade_category() == "keine_note"


# ============================================================================
# RETRY TESTS
# ============================================================================

def test_can_retry_first_attempt():
    """Test: can_retry() im ersten Versuch"""
    pl = Pruefungsleistung(
        id=1, einschreibung_id=100, modul_id=42,
        buchungsdatum=date(2024, 1, 15), status="nicht_bestanden",
        note=Decimal("5.0"), pruefungsdatum=date(2024, 2, 1),
        versuch=1, max_versuche=3
    )

    assert pl.can_retry() is True


def test_can_retry_second_attempt():
    """Test: can_retry() im zweiten Versuch"""
    pl = Pruefungsleistung(
        id=1, einschreibung_id=100, modul_id=42,
        buchungsdatum=date(2024, 1, 15), status="nicht_bestanden",
        note=Decimal("5.0"), pruefungsdatum=date(2024, 2, 1),
        versuch=2, max_versuche=3
    )

    assert pl.can_retry() is True


def test_cannot_retry_last_attempt():
    """Test: can_retry() im letzten Versuch"""
    pl = Pruefungsleistung(
        id=1, einschreibung_id=100, modul_id=42,
        buchungsdatum=date(2024, 1, 15), status="nicht_bestanden",
        note=Decimal("5.0"), pruefungsdatum=date(2024, 2, 1),
        versuch=3, max_versuche=3
    )

    assert pl.can_retry() is False


# ============================================================================
# TO_DICT TESTS (POLYMORPHIE)
# ============================================================================

def test_to_dict_extends_base():
    """Test: to_dict() erweitert Basisklassen-Dictionary (Polymorphie)"""
    pl = Pruefungsleistung(
        id=1, einschreibung_id=100, modul_id=42,
        buchungsdatum=date(2024, 1, 15), status="bestanden",
        note=Decimal("2.3"), pruefungsdatum=date(2024, 2, 1),
        versuch=1, max_versuche=3, anmeldemodus="online", thema=None
    )

    data = pl.to_dict()

    # Basis-Felder von Modulbuchung
    assert data['id'] == 1
    assert data['einschreibung_id'] == 100
    assert data['modul_id'] == 42
    assert data['status'] == "bestanden"

    # Erweiterte Felder von Pruefungsleistung
    assert data['note'] == 2.3
    assert data['note_formatted'] == "2.30"
    assert data['pruefungsdatum'] == "2024-02-01"
    assert data['versuch'] == 1
    assert data['max_versuche'] == 3
    assert data['anmeldemodus'] == "online"
    assert data['thema'] is None
    assert data['has_grade'] is True
    assert data['can_retry'] is True
    assert data['grade_category'] == "gut"


def test_to_dict_without_note():
    """Test: to_dict() ohne Note"""
    pl = Pruefungsleistung(
        id=1, einschreibung_id=100, modul_id=42,
        buchungsdatum=date(2024, 1, 15), status="gebucht",
        note=None, pruefungsdatum=date(2024, 2, 1), versuch=1
    )

    data = pl.to_dict()

    assert data['note'] is None
    assert data['note_formatted'] == "—"
    assert data['has_grade'] is False


# ============================================================================
# FROM_ROW TESTS
# ============================================================================

def test_from_row():
    """Test: from_row() erstellt Pruefungsleistung aus DB-Row"""
    row_data = {
        'id': 1,
        'einschreibung_id': 100,
        'modul_id': 42,
        'buchungsdatum': date(2024, 1, 15),
        'status': 'bestanden',
        'note': '2.3',
        'pruefungsdatum': date(2024, 2, 1),
        'versuch': 1,
        'max_versuche': 3,
        'anmeldemodus': 'online',
        'thema': None
    }

    pl = Pruefungsleistung.from_row(row_data)

    assert pl.id == 1
    assert pl.note == Decimal("2.3")
    assert pl.versuch == 1


# ============================================================================
# STRING REPRESENTATION TESTS
# ============================================================================

def test_str_representation_with_note():
    """Test: __str__() mit Note"""
    pl = Pruefungsleistung(
        id=1, einschreibung_id=100, modul_id=42,
        buchungsdatum=date(2024, 1, 15), status="bestanden",
        note=Decimal("2.3"), pruefungsdatum=date(2024, 2, 1), versuch=1
    )

    pl_str = str(pl)

    assert "Pruefungsleistung" in pl_str
    assert "42" in pl_str
    assert "2.30" in pl_str


def test_str_representation_without_note():
    """Test: __str__() ohne Note"""
    pl = Pruefungsleistung(
        id=1, einschreibung_id=100, modul_id=42,
        buchungsdatum=date(2024, 1, 15), status="gebucht",
        note=None, pruefungsdatum=date(2024, 2, 1), versuch=1
    )

    pl_str = str(pl)

    assert "keine Note" in pl_str


def test_str_representation_second_attempt():
    """Test: __str__() im zweiten Versuch"""
    pl = Pruefungsleistung(
        id=1, einschreibung_id=100, modul_id=42,
        buchungsdatum=date(2024, 1, 15), status="nicht_bestanden",
        note=Decimal("5.0"), pruefungsdatum=date(2024, 2, 1),
        versuch=2, max_versuche=3
    )

    pl_str = str(pl)

    assert "Versuch 2" in pl_str


def test_repr_representation():
    """Test: __repr__() Methode"""
    pl = Pruefungsleistung(
        id=1, einschreibung_id=100, modul_id=42,
        buchungsdatum=date(2024, 1, 15), status="bestanden",
        note=Decimal("2.3"), pruefungsdatum=date(2024, 2, 1), versuch=1
    )

    pl_repr = repr(pl)

    assert "Pruefungsleistung" in pl_repr
    assert "id=1" in pl_repr
    assert "modul_id=42" in pl_repr
    assert "note=2.3" in pl_repr


if __name__ == "__main__":
    pytest.main([__file__, "-v"])