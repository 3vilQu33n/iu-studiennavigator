# tests/unit/test_gebuehr.py
"""
Unit Tests für Gebuehr Domain Model

Testet die Gebuehr-Klasse aus models/gebuehr.py
"""
import pytest
from datetime import date, timedelta
from decimal import Decimal
import sys
from pathlib import Path

# Füge Project-Root zum Python-Path hinzu
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from models import Gebuehr


# ============================================================================
# CREATION & VALIDATION TESTS
# ============================================================================

def test_gebuehr_create_valid():
    """Test: Gültige Gebühr erstellen"""
    g = Gebuehr(
        id=1,
        einschreibung_id=10,
        art="Monatsrate",
        betrag=Decimal("299.00"),
        faellig_am=date(2024, 3, 1)
    )

    assert g.id == 1
    assert g.einschreibung_id == 10
    assert g.art == "Monatsrate"
    assert g.betrag == Decimal("299.00")
    assert g.faellig_am == date(2024, 3, 1)
    assert g.bezahlt_am is None


def test_gebuehr_create_with_payment():
    """Test: Gebühr mit Zahlungsdatum erstellen"""
    g = Gebuehr(
        id=1,
        einschreibung_id=10,
        art="Monatsrate",
        betrag=Decimal("299.00"),
        faellig_am=date(2024, 3, 1),
        bezahlt_am=date(2024, 2, 28)
    )

    assert g.bezahlt_am == date(2024, 2, 28)


def test_gebuehr_create_with_float_betrag():
    """Test: Gebühr mit Float-Betrag (wird zu Decimal konvertiert)"""
    g = Gebuehr(
        id=1,
        einschreibung_id=10,
        art="Semestergebühr",
        betrag=199.99,  # Float!
        faellig_am=date(2024, 3, 1)
    )

    assert isinstance(g.betrag, Decimal)
    assert g.betrag == Decimal("199.99")


def test_gebuehr_create_with_string_dates():
    """Test: Gebühr mit String-Datumsangaben"""
    g = Gebuehr(
        id=1,
        einschreibung_id=10,
        art="Prüfungsgebühr",
        betrag=Decimal("80.00"),
        faellig_am="2024-03-15",  # String!
        bezahlt_am="2024-03-14"  # String!
    )

    assert isinstance(g.faellig_am, date)
    assert isinstance(g.bezahlt_am, date)
    assert g.faellig_am == date(2024, 3, 15)
    assert g.bezahlt_am == date(2024, 3, 14)


def test_gebuehr_allowed_art():
    """Test: Alle erlaubten Gebührenarten"""
    allowed_types = ["Monatsrate", "Semestergebühr", "Prüfungsgebühr", "Einschreibegebühr"]

    for art_type in allowed_types:
        g = Gebuehr(
            id=1,
            einschreibung_id=10,
            art=art_type,
            betrag=Decimal("100.00"),
            faellig_am=date(2024, 3, 1)
        )
        assert g.art == art_type


def test_gebuehr_invalid_art_warning():
    """Test: Warnung bei unbekannter Gebührenart (keine Exception!)"""
    # Sollte KEINE Exception werfen, nur loggen
    g = Gebuehr(
        id=1,
        einschreibung_id=10,
        art="Unbekannte Art",  # Nicht in ALLOWED_ART
        betrag=Decimal("100.00"),
        faellig_am=date(2024, 3, 1)
    )

    assert g.art == "Unbekannte Art"  # Wird trotzdem gesetzt


def test_gebuehr_negative_betrag_raises():
    """Test: Negativer Betrag wirft ValueError"""
    with pytest.raises(ValueError, match="negativ"):
        Gebuehr(
            id=1,
            einschreibung_id=10,
            art="Monatsrate",
            betrag=Decimal("-100.00"),  # Negativ!
            faellig_am=date(2024, 3, 1)
        )


def test_gebuehr_invalid_betrag_raises():
    """Test: Ungültiger Betrag wirft ValueError"""
    with pytest.raises(ValueError, match="Ungültiger Betrag"):
        Gebuehr(
            id=1,
            einschreibung_id=10,
            art="Monatsrate",
            betrag="not-a-number",  # Ungültig!
            faellig_am=date(2024, 3, 1)
        )


def test_gebuehr_invalid_date_raises():
    """Test: Ungültiges Datum wirft ValueError"""
    with pytest.raises(ValueError, match="Ungültiges Datum"):
        Gebuehr(
            id=1,
            einschreibung_id=10,
            art="Monatsrate",
            betrag=Decimal("100.00"),
            faellig_am="not-a-date"  # Ungültig!
        )


# ============================================================================
# PAYMENT STATUS TESTS
# ============================================================================

def test_is_paid_true():
    """Test: is_paid() gibt True zurück wenn bezahlt"""
    g = Gebuehr(
        id=1,
        einschreibung_id=10,
        art="Monatsrate",
        betrag=Decimal("299.00"),
        faellig_am=date(2024, 3, 1),
        bezahlt_am=date(2024, 2, 28)
    )

    assert g.is_paid() is True


def test_is_paid_false():
    """Test: is_paid() gibt False zurück wenn nicht bezahlt"""
    g = Gebuehr(
        id=1,
        einschreibung_id=10,
        art="Monatsrate",
        betrag=Decimal("299.00"),
        faellig_am=date(2024, 3, 1)
    )

    assert g.is_paid() is False


def test_mark_as_paid_default_today():
    """Test: mark_as_paid() setzt Datum auf heute"""
    g = Gebuehr(
        id=1,
        einschreibung_id=10,
        art="Monatsrate",
        betrag=Decimal("299.00"),
        faellig_am=date(2024, 3, 1)
    )

    assert g.is_paid() is False

    g.mark_as_paid()

    assert g.is_paid() is True
    assert g.bezahlt_am == date.today()


def test_mark_as_paid_custom_date():
    """Test: mark_as_paid() mit benutzerdefiniertem Datum"""
    g = Gebuehr(
        id=1,
        einschreibung_id=10,
        art="Monatsrate",
        betrag=Decimal("299.00"),
        faellig_am=date(2024, 3, 1)
    )

    payment_date = date(2024, 2, 25)
    g.mark_as_paid(payment_date)

    assert g.is_paid() is True
    assert g.bezahlt_am == payment_date


# ============================================================================
# OVERDUE TESTS
# ============================================================================

def test_is_overdue_true():
    """Test: is_overdue() gibt True bei überfälliger Gebühr"""
    g = Gebuehr(
        id=1,
        einschreibung_id=10,
        art="Monatsrate",
        betrag=Decimal("299.00"),
        faellig_am=date(2024, 1, 1)  # Vergangenheit
    )

    # Referenzdatum: 1 Monat später
    ref_date = date(2024, 2, 1)

    assert g.is_overdue(ref_date) is True


def test_is_overdue_false_not_due_yet():
    """Test: is_overdue() gibt False wenn noch nicht fällig"""
    g = Gebuehr(
        id=1,
        einschreibung_id=10,
        art="Monatsrate",
        betrag=Decimal("299.00"),
        faellig_am=date(2024, 12, 31)  # Zukunft
    )

    ref_date = date(2024, 6, 1)

    assert g.is_overdue(ref_date) is False


def test_is_overdue_false_already_paid():
    """Test: is_overdue() gibt False wenn bereits bezahlt"""
    g = Gebuehr(
        id=1,
        einschreibung_id=10,
        art="Monatsrate",
        betrag=Decimal("299.00"),
        faellig_am=date(2024, 1, 1),
        bezahlt_am=date(2024, 1, 15)  # Bezahlt!
    )

    ref_date = date(2024, 6, 1)

    assert g.is_overdue(ref_date) is False


def test_get_days_overdue_positive():
    """Test: get_days_overdue() berechnet Tage korrekt"""
    g = Gebuehr(
        id=1,
        einschreibung_id=10,
        art="Monatsrate",
        betrag=Decimal("299.00"),
        faellig_am=date(2024, 1, 1)
    )

    ref_date = date(2024, 1, 31)  # 30 Tage später

    assert g.get_days_overdue(ref_date) == 30


def test_get_days_overdue_zero_not_overdue():
    """Test: get_days_overdue() gibt 0 zurück wenn nicht überfällig"""
    g = Gebuehr(
        id=1,
        einschreibung_id=10,
        art="Monatsrate",
        betrag=Decimal("299.00"),
        faellig_am=date(2024, 12, 31)
    )

    ref_date = date(2024, 6, 1)

    assert g.get_days_overdue(ref_date) == 0


def test_get_days_overdue_zero_already_paid():
    """Test: get_days_overdue() gibt 0 zurück wenn bezahlt"""
    g = Gebuehr(
        id=1,
        einschreibung_id=10,
        art="Monatsrate",
        betrag=Decimal("299.00"),
        faellig_am=date(2024, 1, 1),
        bezahlt_am=date(2024, 1, 15)
    )

    ref_date = date(2024, 6, 1)

    assert g.get_days_overdue(ref_date) == 0


# ============================================================================
# DUE SOON TESTS
# ============================================================================

def test_is_due_soon_true():
    """Test: is_due_soon() gibt True wenn bald fällig"""
    g = Gebuehr(
        id=1,
        einschreibung_id=10,
        art="Monatsrate",
        betrag=Decimal("299.00"),
        faellig_am=date(2024, 6, 5)
    )

    ref_date = date(2024, 6, 1)  # 4 Tage vorher

    assert g.is_due_soon(days_ahead=7, reference_date=ref_date) is True


def test_is_due_soon_false_too_far():
    """Test: is_due_soon() gibt False wenn zu weit in der Zukunft"""
    g = Gebuehr(
        id=1,
        einschreibung_id=10,
        art="Monatsrate",
        betrag=Decimal("299.00"),
        faellig_am=date(2024, 6, 20)
    )

    ref_date = date(2024, 6, 1)  # 19 Tage vorher

    assert g.is_due_soon(days_ahead=7, reference_date=ref_date) is False


def test_is_due_soon_false_already_paid():
    """Test: is_due_soon() gibt False wenn bereits bezahlt"""
    g = Gebuehr(
        id=1,
        einschreibung_id=10,
        art="Monatsrate",
        betrag=Decimal("299.00"),
        faellig_am=date(2024, 6, 5),
        bezahlt_am=date(2024, 6, 1)
    )

    ref_date = date(2024, 6, 1)

    assert g.is_due_soon(reference_date=ref_date) is False


def test_get_days_until_due_positive():
    """Test: get_days_until_due() berechnet Tage bis Fälligkeit"""
    g = Gebuehr(
        id=1,
        einschreibung_id=10,
        art="Monatsrate",
        betrag=Decimal("299.00"),
        faellig_am=date(2024, 6, 15)
    )

    ref_date = date(2024, 6, 1)  # 14 Tage vorher

    assert g.get_days_until_due(ref_date) == 14


def test_get_days_until_due_negative():
    """Test: get_days_until_due() gibt negative Zahl bei Überfälligkeit"""
    g = Gebuehr(
        id=1,
        einschreibung_id=10,
        art="Monatsrate",
        betrag=Decimal("299.00"),
        faellig_am=date(2024, 6, 1)
    )

    ref_date = date(2024, 6, 15)  # 14 Tage später

    assert g.get_days_until_due(ref_date) == -14


# ============================================================================
# FORMATTING TESTS
# ============================================================================

def test_get_formatted_amount_basic():
    """Test: get_formatted_amount() formatiert Betrag deutsch"""
    g = Gebuehr(
        id=1,
        einschreibung_id=10,
        art="Monatsrate",
        betrag=Decimal("299.00"),
        faellig_am=date(2024, 6, 1)
    )

    assert g.get_formatted_amount() == "299,00 €"


def test_get_formatted_amount_thousands():
    """Test: get_formatted_amount() mit Tausender-Trennzeichen"""
    g = Gebuehr(
        id=1,
        einschreibung_id=10,
        art="Semestergebühr",
        betrag=Decimal("1234.56"),
        faellig_am=date(2024, 6, 1)
    )

    assert g.get_formatted_amount() == "1.234,56 €"


def test_get_status_text_paid():
    """Test: get_status_text() gibt 'Bezahlt' zurück"""
    g = Gebuehr(
        id=1,
        einschreibung_id=10,
        art="Monatsrate",
        betrag=Decimal("299.00"),
        faellig_am=date(2024, 6, 1),
        bezahlt_am=date(2024, 5, 30)
    )

    assert g.get_status_text() == "Bezahlt"


def test_get_status_text_overdue():
    """Test: get_status_text() gibt 'Überfällig (X Tage)' zurück"""
    g = Gebuehr(
        id=1,
        einschreibung_id=10,
        art="Monatsrate",
        betrag=Decimal("299.00"),
        faellig_am=date(2024, 6, 1)
    )

    ref_date = date(2024, 6, 11)  # 10 Tage später

    status = g.get_status_text(ref_date)
    assert "Überfällig" in status
    assert "10 Tage" in status


def test_get_status_text_due_soon():
    """Test: get_status_text() gibt 'Fällig in X Tagen' zurück"""
    g = Gebuehr(
        id=1,
        einschreibung_id=10,
        art="Monatsrate",
        betrag=Decimal("299.00"),
        faellig_am=date(2024, 6, 10)
    )

    ref_date = date(2024, 6, 5)  # 5 Tage vorher

    status = g.get_status_text(ref_date)
    assert "Fällig in" in status
    assert "5 Tagen" in status


def test_get_status_text_open():
    """Test: get_status_text() gibt 'Offen' zurück"""
    g = Gebuehr(
        id=1,
        einschreibung_id=10,
        art="Monatsrate",
        betrag=Decimal("299.00"),
        faellig_am=date(2024, 12, 31)  # Weit in der Zukunft
    )

    ref_date = date(2024, 6, 1)

    assert g.get_status_text(ref_date) == "Offen"


# ============================================================================
# TO_DICT TESTS
# ============================================================================

def test_to_dict_unpaid():
    """Test: to_dict() mit unbezahlter Gebühr"""
    g = Gebuehr(
        id=42,
        einschreibung_id=10,
        art="Monatsrate",
        betrag=Decimal("299.00"),
        faellig_am=date(2024, 6, 1)
    )

    data = g.to_dict()

    assert data['id'] == 42
    assert data['einschreibung_id'] == 10
    assert data['art'] == "Monatsrate"
    assert data['betrag'] == 299.0
    assert data['betrag_formatted'] == "299,00 €"
    assert data['faellig_am'] == "2024-06-01"
    assert data['bezahlt_am'] is None
    assert data['is_paid'] is False


def test_to_dict_paid():
    """Test: to_dict() mit bezahlter Gebühr"""
    g = Gebuehr(
        id=1,
        einschreibung_id=10,
        art="Monatsrate",
        betrag=Decimal("299.00"),
        faellig_am=date(2024, 6, 1),
        bezahlt_am=date(2024, 5, 30)
    )

    data = g.to_dict()

    assert data['bezahlt_am'] == "2024-05-30"
    assert data['is_paid'] is True


# ============================================================================
# FROM_ROW TESTS
# ============================================================================

def test_from_row_basic():
    """Test: from_row() mit Dictionary"""
    row_data = {
        'id': 42,
        'einschreibung_id': 10,
        'art': 'Monatsrate',
        'betrag': '299.00',
        'faellig_am': date(2024, 6, 1),
        'bezahlt_am': None
    }

    g = Gebuehr.from_row(row_data)

    assert g.id == 42
    assert g.einschreibung_id == 10
    assert g.art == "Monatsrate"
    assert g.betrag == Decimal("299.00")
    assert g.faellig_am == date(2024, 6, 1)
    assert g.bezahlt_am is None


def test_from_row_with_payment():
    """Test: from_row() mit Zahlungsdatum"""
    row_data = {
        'id': 1,
        'einschreibung_id': 10,
        'art': 'Monatsrate',
        'betrag': '299.00',
        'faellig_am': date(2024, 6, 1),
        'bezahlt_am': date(2024, 5, 30)
    }

    g = Gebuehr.from_row(row_data)

    assert g.bezahlt_am == date(2024, 5, 30)
    assert g.is_paid() is True


def test_from_row_with_string_dates():
    """Test: from_row() mit String-Datumsangaben"""
    row_data = {
        'id': 1,
        'einschreibung_id': 10,
        'art': 'Prüfungsgebühr',
        'betrag': '80.00',
        'faellig_am': '2024-06-15',  # String!
        'bezahlt_am': '2024-06-14'  # String!
    }

    g = Gebuehr.from_row(row_data)

    assert isinstance(g.faellig_am, date)
    assert isinstance(g.bezahlt_am, date)
    assert g.faellig_am == date(2024, 6, 15)
    assert g.bezahlt_am == date(2024, 6, 14)


# ============================================================================
# STRING REPRESENTATION TESTS
# ============================================================================

def test_str_representation_unpaid():
    """Test: __str__() für unbezahlte Gebühr"""
    g = Gebuehr(
        id=1,
        einschreibung_id=10,
        art="Monatsrate",
        betrag=Decimal("299.00"),
        faellig_am=date(2024, 6, 1)
    )

    s = str(g)

    assert "Monatsrate" in s
    assert "299,00 €" in s
    assert "offen" in s


def test_str_representation_paid():
    """Test: __str__() für bezahlte Gebühr"""
    g = Gebuehr(
        id=1,
        einschreibung_id=10,
        art="Semestergebühr",
        betrag=Decimal("199.00"),
        faellig_am=date(2024, 6, 1),
        bezahlt_am=date(2024, 5, 30)
    )

    s = str(g)

    assert "Semestergebühr" in s
    assert "199,00 €" in s
    assert "bezahlt" in s


def test_repr_representation():
    """Test: __repr__() Methode"""
    g = Gebuehr(
        id=42,
        einschreibung_id=10,
        art="Monatsrate",
        betrag=Decimal("299.00"),
        faellig_am=date(2024, 6, 1)
    )

    r = repr(g)

    assert "Gebuehr" in r
    assert "id=42" in r
    assert "art='Monatsrate'" in r
    assert "betrag=" in r
    assert "is_paid=" in r


if __name__ == "__main__":
    pytest.main([__file__, "-v"])