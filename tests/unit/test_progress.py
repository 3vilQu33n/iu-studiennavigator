# tests/unit/test_progress.py
"""
Unit Tests für Progress Domain Model

Testet die Progress-Klasse aus models/progress.py
"""
import pytest
from decimal import Decimal
import sys
from pathlib import Path

# Füge Project-Root zum Python-Path hinzu
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from models import Progress


# ============================================================================
# CREATION & VALIDATION TESTS
# ============================================================================

def test_progress_create_valid():
    """Test: Gültigen Progress erstellen"""
    p = Progress(
        student_id=1,
        durchschnittsnote=Decimal("2.5"),
        anzahl_bestandene_module=10,
        anzahl_gebuchte_module=12,
        offene_gebuehren=Decimal("0.00"),
        aktuelles_semester=3.0,
        erwartetes_semester=3.0
    )

    assert p.student_id == 1
    assert p.durchschnittsnote == Decimal("2.5")
    assert p.anzahl_bestandene_module == 10
    assert p.anzahl_gebuchte_module == 12
    assert p.offene_gebuehren == Decimal("0.00")
    assert p.aktuelles_semester == 3.0
    assert p.erwartetes_semester == 3.0


def test_progress_create_without_grade():
    """Test: Progress ohne Durchschnittsnote (None)"""
    p = Progress(
        student_id=1,
        durchschnittsnote=None,  # Noch keine Noten!
        anzahl_bestandene_module=0,
        anzahl_gebuchte_module=5,
        offene_gebuehren=Decimal("0.00"),
        aktuelles_semester=1.0,
        erwartetes_semester=1.0
    )

    assert p.durchschnittsnote is None


def test_progress_create_with_float_values():
    """Test: Progress mit Float-Werten (werden zu Decimal konvertiert)"""
    p = Progress(
        student_id=1,
        durchschnittsnote=2.5,  # Float!
        anzahl_bestandene_module=10,
        anzahl_gebuchte_module=12,
        offene_gebuehren=299.00,  # Float!
        aktuelles_semester=3.0,
        erwartetes_semester=3.0
    )

    assert isinstance(p.durchschnittsnote, Decimal)
    assert isinstance(p.offene_gebuehren, Decimal)
    assert p.durchschnittsnote == Decimal("2.5")
    assert p.offene_gebuehren == Decimal("299.00")


def test_progress_create_with_open_fees():
    """Test: Progress mit offenen Gebühren"""
    p = Progress(
        student_id=1,
        durchschnittsnote=Decimal("2.0"),
        anzahl_bestandene_module=10,
        anzahl_gebuchte_module=12,
        offene_gebuehren=Decimal("598.00"),  # 2 Monate offen
        aktuelles_semester=3.0,
        erwartetes_semester=3.0
    )

    assert p.offene_gebuehren == Decimal("598.00")


# ============================================================================
# OVERALL STATUS TESTS
# ============================================================================

def test_calculate_overall_status_excellent():
    """Test: calculate_overall_status() gibt 'excellent' zurück"""
    p = Progress(
        student_id=1,
        durchschnittsnote=Decimal("1.5"),  # Gute Note
        anzahl_bestandene_module=10,
        anzahl_gebuchte_module=12,
        offene_gebuehren=Decimal("0.00"),  # Keine Gebühren
        aktuelles_semester=3.0,
        erwartetes_semester=3.0  # Im Zeitplan
    )

    assert p.calculate_overall_status() == 'excellent'


def test_calculate_overall_status_good():
    """Test: calculate_overall_status() gibt 'good' zurück"""
    p = Progress(
        student_id=1,
        durchschnittsnote=Decimal("2.0"),  # OK Note
        anzahl_bestandene_module=10,
        anzahl_gebuchte_module=12,
        offene_gebuehren=Decimal("299.00"),  # Offene Gebühren
        aktuelles_semester=3.0,
        erwartetes_semester=3.0  # Im Zeitplan
    )

    assert p.calculate_overall_status() == 'good'


def test_calculate_overall_status_okay():
    """Test: Status ist 'okay' wenn Note gut aber Zeit schlecht ist"""
    p = Progress(
        student_id=1,
        durchschnittsnote=Decimal('2.3'),  # ✅ okay (≤ 2.5)
        anzahl_bestandene_module=20,
        anzahl_gebuchte_module=30,
        offene_gebuehren=Decimal('100.0'),
        aktuelles_semester=3.0,
        erwartetes_semester=5.0  # ❌ weit hinterher
    )
    assert p.calculate_overall_status() == 'okay'


def test_calculate_overall_status_critical():
    """Test: calculate_overall_status() gibt 'critical' zurück"""
    p = Progress(
        student_id=1,
        durchschnittsnote=Decimal("3.8"),  # Schlechte Note
        anzahl_bestandene_module=3,
        anzahl_gebuchte_module=12,
        offene_gebuehren=Decimal("897.00"),  # Viele Gebühren
        aktuelles_semester=4.0,
        erwartetes_semester=2.0  # Weit hinterher
    )

    assert p.calculate_overall_status() == 'critical'


def test_calculate_overall_status_no_grade():
    """Test: calculate_overall_status() ohne Note (noch keine Prüfungen)"""
    p = Progress(
        student_id=1,
        durchschnittsnote=None,  # Noch keine Noten!
        anzahl_bestandene_module=0,
        anzahl_gebuchte_module=5,
        offene_gebuehren=Decimal("0.00"),
        aktuelles_semester=1.0,
        erwartetes_semester=1.0
    )

    # Ohne Note wird als "gut" gewertet
    assert p.calculate_overall_status() == 'excellent'


# ============================================================================
# COMPLETION PERCENTAGE TESTS
# ============================================================================

def test_get_completion_percentage_basic():
    """Test: get_completion_percentage() berechnet Prozentsatz korrekt"""
    p = Progress(
        student_id=1,
        durchschnittsnote=Decimal("2.0"),
        anzahl_bestandene_module=24,  # Hälfte von 49
        anzahl_gebuchte_module=30,
        offene_gebuehren=Decimal("0.00"),
        aktuelles_semester=3.0,
        erwartetes_semester=3.0
    )

    # 24 von 49 = ~49%
    percentage = p.get_completion_percentage(total_modules=49)
    assert 48.9 <= percentage <= 49.1


def test_get_completion_percentage_zero():
    """Test: get_completion_percentage() gibt 0% zurück am Anfang"""
    p = Progress(
        student_id=1,
        durchschnittsnote=None,
        anzahl_bestandene_module=0,
        anzahl_gebuchte_module=5,
        offene_gebuehren=Decimal("0.00"),
        aktuelles_semester=1.0,
        erwartetes_semester=1.0
    )

    assert p.get_completion_percentage() == 0.0


def test_get_completion_percentage_complete():
    """Test: get_completion_percentage() gibt 100% zurück bei Abschluss"""
    p = Progress(
        student_id=1,
        durchschnittsnote=Decimal("1.5"),
        anzahl_bestandene_module=49,  # Alle Module!
        anzahl_gebuchte_module=49,
        offene_gebuehren=Decimal("0.00"),
        aktuelles_semester=7.0,
        erwartetes_semester=7.0
    )

    assert p.get_completion_percentage(total_modules=49) == 100.0


def test_get_completion_percentage_over_100_capped():
    """Test: get_completion_percentage() wird bei 100% gekappt"""
    p = Progress(
        student_id=1,
        durchschnittsnote=Decimal("1.5"),
        anzahl_bestandene_module=55,  # Mehr als nötig (z.B. Wahlmodule)
        anzahl_gebuchte_module=55,
        offene_gebuehren=Decimal("0.00"),
        aktuelles_semester=7.0,
        erwartetes_semester=7.0
    )

    # Sollte bei 100% gekappt werden
    assert p.get_completion_percentage(total_modules=49) == 100.0


def test_get_completion_percentage_custom_total():
    """Test: get_completion_percentage() mit benutzerdefiniertem Total"""
    p = Progress(
        student_id=1,
        durchschnittsnote=Decimal("2.0"),
        anzahl_bestandene_module=15,
        anzahl_gebuchte_module=20,
        offene_gebuehren=Decimal("0.00"),
        aktuelles_semester=3.0,
        erwartetes_semester=3.0
    )

    # 15 von 30 = 50%
    assert p.get_completion_percentage(total_modules=30) == 50.0


def test_get_completion_percentage_invalid_total():
    """Test: get_completion_percentage() mit ungültigem Total gibt 0% zurück"""
    p = Progress(
        student_id=1,
        durchschnittsnote=Decimal("2.0"),
        anzahl_bestandene_module=10,
        anzahl_gebuchte_module=12,
        offene_gebuehren=Decimal("0.00"),
        aktuelles_semester=3.0,
        erwartetes_semester=3.0
    )

    # Total 0 oder negativ → 0%
    assert p.get_completion_percentage(total_modules=0) == 0.0
    assert p.get_completion_percentage(total_modules=-5) == 0.0


# ============================================================================
# TO_DICT TESTS
# ============================================================================

def test_to_dict_with_grade():
    """Test: to_dict() mit Durchschnittsnote"""
    p = Progress(
        student_id=42,
        durchschnittsnote=Decimal("2.5"),
        anzahl_bestandene_module=10,
        anzahl_gebuchte_module=12,
        offene_gebuehren=Decimal("0.00"),
        aktuelles_semester=3.0,
        erwartetes_semester=3.0
    )

    data = p.to_dict()

    assert data['student_id'] == 42
    assert data['durchschnittsnote'] == 2.5
    assert data['durchschnittsnote_formatted'] == "2.50"
    assert data['anzahl_bestandene_module'] == 10
    assert data['anzahl_gebuchte_module'] == 12
    assert data['offene_gebuehren'] == 0.0
    assert data['aktuelles_semester'] == 3.0
    assert data['erwartetes_semester'] == 3.0
    assert data['overall_status'] == 'excellent'


def test_to_dict_without_grade():
    """Test: to_dict() ohne Durchschnittsnote"""
    p = Progress(
        student_id=1,
        durchschnittsnote=None,
        anzahl_bestandene_module=0,
        anzahl_gebuchte_module=5,
        offene_gebuehren=Decimal("0.00"),
        aktuelles_semester=1.0,
        erwartetes_semester=1.0
    )

    data = p.to_dict()

    assert data['durchschnittsnote'] is None
    assert data['durchschnittsnote_formatted'] == "—"
    assert data['grade_category'] == 'unknown'


def test_to_dict_with_open_fees():
    """Test: to_dict() mit offenen Gebühren"""
    p = Progress(
        student_id=1,
        durchschnittsnote=Decimal("2.0"),
        anzahl_bestandene_module=10,
        anzahl_gebuchte_module=12,
        offene_gebuehren=Decimal("598.00"),
        aktuelles_semester=3.0,
        erwartetes_semester=3.0
    )

    data = p.to_dict()

    assert data['offene_gebuehren'] == 598.0
    assert data['offene_gebuehren_formatted'] == "598,00 €"
    assert data['fee_category'] == 'open'


def test_to_dict_ahead_of_schedule():
    """Test: to_dict() wenn Student voraus ist"""
    p = Progress(
        student_id=1,
        durchschnittsnote=Decimal("1.5"),
        anzahl_bestandene_module=15,
        anzahl_gebuchte_module=18,
        offene_gebuehren=Decimal("0.00"),
        aktuelles_semester=2.0,  # Erwartet: 3.0
        erwartetes_semester=3.0  # Ist aber erst bei 2.0
    )

    data = p.to_dict()

    assert data['tage_differenz'] == 180  # 1 Semester = 180 Tage
    assert data['time_category'] == 'plus'
    assert data['is_on_schedule'] is False  # Zu weit voraus


def test_to_dict_behind_schedule():
    """Test: to_dict() wenn Student hinterher ist"""
    p = Progress(
        student_id=1,
        durchschnittsnote=Decimal("2.5"),
        anzahl_bestandene_module=5,
        anzahl_gebuchte_module=12,
        offene_gebuehren=Decimal("0.00"),
        aktuelles_semester=4.0,  # Erwartet: 3.0
        erwartetes_semester=3.0  # Ist aber schon bei 4.0
    )

    data = p.to_dict()

    assert data['tage_differenz'] == -180  # 1 Semester = 180 Tage
    assert data['time_category'] == 'minus'
    assert data['is_on_schedule'] is False  # Zu weit hinterher


def test_to_dict_on_schedule():
    """Test: to_dict() wenn Student im Zeitplan ist"""
    p = Progress(
        student_id=1,
        durchschnittsnote=Decimal("2.0"),
        anzahl_bestandene_module=10,
        anzahl_gebuchte_module=12,
        offene_gebuehren=Decimal("0.00"),
        aktuelles_semester=3.0,
        erwartetes_semester=3.0
    )

    data = p.to_dict()

    assert data['tage_differenz'] == 0
    assert data['is_on_schedule'] is True


def test_to_dict_completion_percentage():
    """Test: to_dict() enthält completion_percentage"""
    p = Progress(
        student_id=1,
        durchschnittsnote=Decimal("2.0"),
        anzahl_bestandene_module=24,  # Hälfte
        anzahl_gebuchte_module=30,
        offene_gebuehren=Decimal("0.00"),
        aktuelles_semester=3.0,
        erwartetes_semester=3.0
    )

    data = p.to_dict()

    # Sollte ~49% sein (24 von 49 Standard-Module)
    assert 48.0 <= data['completion_percentage'] <= 50.0


# ============================================================================
# STRING REPRESENTATION TESTS
# ============================================================================

def test_str_representation_with_grade():
    """Test: __str__() mit Durchschnittsnote"""
    p = Progress(
        student_id=42,
        durchschnittsnote=Decimal("2.5"),
        anzahl_bestandene_module=10,
        anzahl_gebuchte_module=12,
        offene_gebuehren=Decimal("0.00"),
        aktuelles_semester=3.0,
        erwartetes_semester=3.0
    )

    s = str(p)

    assert "Progress" in s
    assert "Student 42" in s
    assert "2.50" in s
    assert "3.0" in s


def test_str_representation_without_grade():
    """Test: __str__() ohne Durchschnittsnote"""
    p = Progress(
        student_id=1,
        durchschnittsnote=None,
        anzahl_bestandene_module=0,
        anzahl_gebuchte_module=5,
        offene_gebuehren=Decimal("0.00"),
        aktuelles_semester=1.0,
        erwartetes_semester=1.0
    )

    s = str(p)

    assert "Progress" in s
    assert "Student 1" in s
    assert "—" in s  # Em Dash für keine Note


def test_repr_representation():
    """Test: __repr__() Methode"""
    p = Progress(
        student_id=42,
        durchschnittsnote=Decimal("2.5"),
        anzahl_bestandene_module=10,
        anzahl_gebuchte_module=12,
        offene_gebuehren=Decimal("598.00"),
        aktuelles_semester=3.5,
        erwartetes_semester=3.0
    )

    r = repr(p)

    assert "Progress" in r
    assert "student_id=42" in r
    assert "note=" in r
    assert "semester=3.5" in r
    assert "fees=" in r


if __name__ == "__main__":
    pytest.main([__file__, "-v"])