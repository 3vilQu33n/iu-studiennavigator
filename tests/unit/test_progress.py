# tests/unit/test_progress.py
"""
Unit Tests fuer Progress Domain Model (models/progress.py)

Testet die Progress-Klasse:
- Initialisierung und Typ-Konvertierung
- calculate_overall_status() - Gesamt-Status
- get_completion_percentage() - Fortschritts-Prozentsatz
- to_dict() - Serialisierung inkl. privater Berechnungen
- String-Repraesentation
"""
from __future__ import annotations

import pytest
from decimal import Decimal

# Mark this whole module as unit tests
pytestmark = pytest.mark.unit


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def progress_class():
    """Importiert Progress-Klasse"""
    try:
        from models.progress import Progress
        return Progress
    except ImportError:
        from models import Progress
        return Progress


@pytest.fixture
def excellent_progress(progress_class):
    """Exzellenter Fortschritt (alle Kriterien erfuellt)"""
    return progress_class(
        student_id=1,
        durchschnittsnote=Decimal("1.7"),
        anzahl_bestandene_module=20,
        anzahl_gebuchte_module=22,
        offene_gebuehren=Decimal("0"),
        aktuelles_semester=3.5,
        erwartetes_semester=3.5
    )


@pytest.fixture
def good_progress(progress_class):
    """Guter Fortschritt (Note und Zeit ok, aber offene Gebuehren)"""
    return progress_class(
        student_id=2,
        durchschnittsnote=Decimal("2.3"),
        anzahl_bestandene_module=15,
        anzahl_gebuchte_module=18,
        offene_gebuehren=Decimal("199.00"),
        aktuelles_semester=3.0,
        erwartetes_semester=3.0
    )


@pytest.fixture
def okay_progress(progress_class):
    """Okay Fortschritt (nur eines der Kriterien erfuellt)

    Fuer 'okay' muss grade_ok ODER time_ok True sein, aber nicht beide.
    Hier: grade_ok=True (Note 2.0 <= 2.5), time_ok=False (weit hinter Zeitplan)
    """
    return progress_class(
        student_id=3,
        durchschnittsnote=Decimal("2.0"),  # Gute Note (grade_ok=True)
        anzahl_bestandene_module=10,
        anzahl_gebuchte_module=12,
        offene_gebuehren=Decimal("500.00"),
        aktuelles_semester=1.0,
        erwartetes_semester=3.0  # Weit hinter Zeitplan (time_ok=False, -360 Tage)
    )


@pytest.fixture
def critical_progress(progress_class):
    """Kritischer Fortschritt (keine Kriterien erfuellt)"""
    return progress_class(
        student_id=4,
        durchschnittsnote=Decimal("3.8"),  # Schlechte Note
        anzahl_bestandene_module=5,
        anzahl_gebuchte_module=8,
        offene_gebuehren=Decimal("1000.00"),
        aktuelles_semester=1.0,
        erwartetes_semester=3.0  # Weit hinter Zeitplan
    )


@pytest.fixture
def no_grade_progress(progress_class):
    """Fortschritt ohne Note (noch keine Pruefung)"""
    return progress_class(
        student_id=5,
        durchschnittsnote=None,
        anzahl_bestandene_module=0,
        anzahl_gebuchte_module=5,
        offene_gebuehren=Decimal("0"),
        aktuelles_semester=1.0,
        erwartetes_semester=1.0
    )


# ============================================================================
# INITIALIZATION TESTS
# ============================================================================

class TestProgressInit:
    """Tests fuer Progress-Initialisierung"""

    def test_init_with_all_fields(self, progress_class):
        """Initialisierung mit allen Feldern"""
        p = progress_class(
            student_id=1,
            durchschnittsnote=Decimal("2.0"),
            anzahl_bestandene_module=10,
            anzahl_gebuchte_module=12,
            offene_gebuehren=Decimal("199.00"),
            aktuelles_semester=2.5,
            erwartetes_semester=2.0
        )

        assert p.student_id == 1
        assert p.durchschnittsnote == Decimal("2.0")
        assert p.anzahl_bestandene_module == 10
        assert p.anzahl_gebuchte_module == 12
        assert p.offene_gebuehren == Decimal("199.00")
        assert p.aktuelles_semester == 2.5
        assert p.erwartetes_semester == 2.0

    def test_init_with_none_note(self, progress_class):
        """Initialisierung mit None als Durchschnittsnote"""
        p = progress_class(
            student_id=1,
            durchschnittsnote=None,
            anzahl_bestandene_module=0,
            anzahl_gebuchte_module=3,
            offene_gebuehren=Decimal("0"),
            aktuelles_semester=1.0,
            erwartetes_semester=1.0
        )

        assert p.durchschnittsnote is None

    def test_init_zero_modules(self, progress_class):
        """Initialisierung ohne Module"""
        p = progress_class(
            student_id=1,
            durchschnittsnote=None,
            anzahl_bestandene_module=0,
            anzahl_gebuchte_module=0,
            offene_gebuehren=Decimal("0"),
            aktuelles_semester=1.0,
            erwartetes_semester=1.0
        )

        assert p.anzahl_bestandene_module == 0
        assert p.anzahl_gebuchte_module == 0


# ============================================================================
# TYPE CONVERSION TESTS
# ============================================================================

class TestTypeConversion:
    """Tests fuer Typ-Konvertierung in __post_init__"""

    def test_note_from_float(self, progress_class):
        """Float-Note wird zu Decimal konvertiert"""
        p = progress_class(
            student_id=1,
            durchschnittsnote=2.3,  # float
            anzahl_bestandene_module=10,
            anzahl_gebuchte_module=12,
            offene_gebuehren=Decimal("0"),
            aktuelles_semester=2.0,
            erwartetes_semester=2.0
        )

        assert isinstance(p.durchschnittsnote, Decimal)
        assert p.durchschnittsnote == Decimal("2.3")

    def test_note_from_string(self, progress_class):
        """String-Note wird zu Decimal konvertiert"""
        p = progress_class(
            student_id=1,
            durchschnittsnote="1.7",  # string
            anzahl_bestandene_module=10,
            anzahl_gebuchte_module=12,
            offene_gebuehren=Decimal("0"),
            aktuelles_semester=2.0,
            erwartetes_semester=2.0
        )

        assert isinstance(p.durchschnittsnote, Decimal)
        assert p.durchschnittsnote == Decimal("1.7")

    def test_note_from_int(self, progress_class):
        """Integer-Note wird zu Decimal konvertiert"""
        p = progress_class(
            student_id=1,
            durchschnittsnote=2,  # int
            anzahl_bestandene_module=10,
            anzahl_gebuchte_module=12,
            offene_gebuehren=Decimal("0"),
            aktuelles_semester=2.0,
            erwartetes_semester=2.0
        )

        assert isinstance(p.durchschnittsnote, Decimal)
        assert p.durchschnittsnote == Decimal("2")

    def test_fees_from_float(self, progress_class):
        """Float-Gebuehren werden zu Decimal konvertiert"""
        p = progress_class(
            student_id=1,
            durchschnittsnote=Decimal("2.0"),
            anzahl_bestandene_module=10,
            anzahl_gebuchte_module=12,
            offene_gebuehren=199.99,  # float
            aktuelles_semester=2.0,
            erwartetes_semester=2.0
        )

        assert isinstance(p.offene_gebuehren, Decimal)
        assert p.offene_gebuehren == Decimal("199.99")

    def test_fees_from_string(self, progress_class):
        """String-Gebuehren werden zu Decimal konvertiert"""
        p = progress_class(
            student_id=1,
            durchschnittsnote=Decimal("2.0"),
            anzahl_bestandene_module=10,
            anzahl_gebuchte_module=12,
            offene_gebuehren="500.00",  # string
            aktuelles_semester=2.0,
            erwartetes_semester=2.0
        )

        assert isinstance(p.offene_gebuehren, Decimal)
        assert p.offene_gebuehren == Decimal("500.00")

    def test_fees_from_int(self, progress_class):
        """Integer-Gebuehren werden zu Decimal konvertiert"""
        p = progress_class(
            student_id=1,
            durchschnittsnote=Decimal("2.0"),
            anzahl_bestandene_module=10,
            anzahl_gebuchte_module=12,
            offene_gebuehren=0,  # int
            aktuelles_semester=2.0,
            erwartetes_semester=2.0
        )

        assert isinstance(p.offene_gebuehren, Decimal)
        assert p.offene_gebuehren == Decimal("0")


# ============================================================================
# CALCULATE_OVERALL_STATUS TESTS
# ============================================================================

class TestCalculateOverallStatus:
    """Tests fuer calculate_overall_status() Methode"""

    def test_excellent_status(self, excellent_progress):
        """Status 'excellent' wenn alle Kriterien erfuellt"""
        assert excellent_progress.calculate_overall_status() == 'excellent'

    def test_good_status(self, good_progress):
        """Status 'good' wenn Note und Zeit ok, aber offene Gebuehren"""
        assert good_progress.calculate_overall_status() == 'good'

    def test_okay_status(self, okay_progress):
        """Status 'okay' wenn nur ein Kriterium erfuellt"""
        assert okay_progress.calculate_overall_status() == 'okay'

    def test_critical_status(self, critical_progress):
        """Status 'critical' wenn kein Kriterium erfuellt"""
        assert critical_progress.calculate_overall_status() == 'critical'

    def test_excellent_with_none_note(self, no_grade_progress):
        """Status 'excellent' mit None-Note (wird als ok behandelt)"""
        assert no_grade_progress.calculate_overall_status() == 'excellent'

    def test_status_grade_boundary_2_5(self, progress_class):
        """Grenze bei Note 2.5"""
        # Note 2.5 ist noch ok
        p1 = progress_class(
            student_id=1,
            durchschnittsnote=Decimal("2.5"),
            anzahl_bestandene_module=10,
            anzahl_gebuchte_module=12,
            offene_gebuehren=Decimal("0"),
            aktuelles_semester=2.0,
            erwartetes_semester=2.0
        )
        assert p1.calculate_overall_status() == 'excellent'

        # Note 2.6 ist nicht mehr ok
        p2 = progress_class(
            student_id=1,
            durchschnittsnote=Decimal("2.6"),
            anzahl_bestandene_module=10,
            anzahl_gebuchte_module=12,
            offene_gebuehren=Decimal("0"),
            aktuelles_semester=2.0,
            erwartetes_semester=2.0
        )
        # Grade not ok, but time ok -> 'okay'
        assert p2.calculate_overall_status() == 'okay'

    def test_status_time_boundary(self, progress_class):
        """Grenze bei Zeit (+/- 30 Tage)"""
        # Innerhalb von 30 Tagen ist ok
        p1 = progress_class(
            student_id=1,
            durchschnittsnote=Decimal("2.0"),
            anzahl_bestandene_module=10,
            anzahl_gebuchte_module=12,
            offene_gebuehren=Decimal("0"),
            aktuelles_semester=2.0,
            erwartetes_semester=2.1  # Kleine Differenz
        )
        assert p1.calculate_overall_status() == 'excellent'

        # Ausserhalb von 30 Tagen
        p2 = progress_class(
            student_id=1,
            durchschnittsnote=Decimal("2.0"),
            anzahl_bestandene_module=10,
            anzahl_gebuchte_module=12,
            offene_gebuehren=Decimal("0"),
            aktuelles_semester=1.0,
            erwartetes_semester=3.0  # Grosse Differenz
        )
        # Grade ok but time not ok -> 'okay'
        assert p2.calculate_overall_status() == 'okay'


# ============================================================================
# GET_COMPLETION_PERCENTAGE TESTS
# ============================================================================

class TestGetCompletionPercentage:
    """Tests fuer get_completion_percentage() Methode"""

    def test_zero_modules_completed(self, progress_class):
        """0% bei keinen bestandenen Modulen"""
        p = progress_class(
            student_id=1,
            durchschnittsnote=None,
            anzahl_bestandene_module=0,
            anzahl_gebuchte_module=5,
            offene_gebuehren=Decimal("0"),
            aktuelles_semester=1.0,
            erwartetes_semester=1.0
        )

        assert p.get_completion_percentage() == 0.0

    def test_half_completed(self, progress_class):
        """~50% bei halber Modulzahl"""
        p = progress_class(
            student_id=1,
            durchschnittsnote=Decimal("2.0"),
            anzahl_bestandene_module=25,
            anzahl_gebuchte_module=30,
            offene_gebuehren=Decimal("0"),
            aktuelles_semester=4.0,
            erwartetes_semester=4.0
        )

        # 25 von 49 = ~51%
        percentage = p.get_completion_percentage()
        assert 50.0 <= percentage <= 52.0

    def test_all_completed(self, progress_class):
        """100% bei allen bestandenen Modulen"""
        p = progress_class(
            student_id=1,
            durchschnittsnote=Decimal("1.5"),
            anzahl_bestandene_module=49,
            anzahl_gebuchte_module=49,
            offene_gebuehren=Decimal("0"),
            aktuelles_semester=7.0,
            erwartetes_semester=7.0
        )

        assert p.get_completion_percentage() == 100.0

    def test_max_100_percent(self, progress_class):
        """Maximal 100% (auch bei mehr als total_modules)"""
        p = progress_class(
            student_id=1,
            durchschnittsnote=Decimal("1.5"),
            anzahl_bestandene_module=60,  # Mehr als 49
            anzahl_gebuchte_module=60,
            offene_gebuehren=Decimal("0"),
            aktuelles_semester=7.0,
            erwartetes_semester=7.0
        )

        assert p.get_completion_percentage() == 100.0

    def test_custom_total_modules(self, progress_class):
        """Benutzerdefinierte Gesamtzahl Module"""
        p = progress_class(
            student_id=1,
            durchschnittsnote=Decimal("2.0"),
            anzahl_bestandene_module=10,
            anzahl_gebuchte_module=12,
            offene_gebuehren=Decimal("0"),
            aktuelles_semester=2.0,
            erwartetes_semester=2.0
        )

        # 10 von 20 = 50%
        assert p.get_completion_percentage(total_modules=20) == 50.0

    def test_zero_total_modules(self, progress_class):
        """0% bei total_modules=0 (Division by Zero vermeiden)"""
        p = progress_class(
            student_id=1,
            durchschnittsnote=Decimal("2.0"),
            anzahl_bestandene_module=10,
            anzahl_gebuchte_module=12,
            offene_gebuehren=Decimal("0"),
            aktuelles_semester=2.0,
            erwartetes_semester=2.0
        )

        assert p.get_completion_percentage(total_modules=0) == 0.0

    def test_negative_total_modules(self, progress_class):
        """0% bei negativen total_modules"""
        p = progress_class(
            student_id=1,
            durchschnittsnote=Decimal("2.0"),
            anzahl_bestandene_module=10,
            anzahl_gebuchte_module=12,
            offene_gebuehren=Decimal("0"),
            aktuelles_semester=2.0,
            erwartetes_semester=2.0
        )

        assert p.get_completion_percentage(total_modules=-10) == 0.0


# ============================================================================
# TO_DICT TESTS
# ============================================================================

class TestToDict:
    """Tests fuer to_dict() Methode"""

    def test_to_dict_contains_all_fields(self, excellent_progress):
        """to_dict() enthaelt alle Felder"""
        d = excellent_progress.to_dict()

        assert 'student_id' in d
        assert 'durchschnittsnote' in d
        assert 'anzahl_bestandene_module' in d
        assert 'anzahl_gebuchte_module' in d
        assert 'offene_gebuehren' in d
        assert 'aktuelles_semester' in d
        assert 'erwartetes_semester' in d

    def test_to_dict_contains_computed_fields(self, excellent_progress):
        """to_dict() enthaelt berechnete Felder"""
        d = excellent_progress.to_dict()

        assert 'durchschnittsnote_formatted' in d
        assert 'grade_category' in d
        assert 'offene_gebuehren_formatted' in d
        assert 'fee_category' in d
        assert 'tage_differenz' in d
        assert 'time_category' in d
        assert 'is_on_schedule' in d
        assert 'overall_status' in d
        assert 'completion_percentage' in d

    def test_to_dict_note_is_float(self, excellent_progress):
        """durchschnittsnote ist float in dict"""
        d = excellent_progress.to_dict()

        assert isinstance(d['durchschnittsnote'], float)
        assert d['durchschnittsnote'] == 1.7

    def test_to_dict_note_none(self, no_grade_progress):
        """durchschnittsnote None bleibt None"""
        d = no_grade_progress.to_dict()

        assert d['durchschnittsnote'] is None

    def test_to_dict_note_formatted(self, excellent_progress):
        """durchschnittsnote_formatted ist formatierter String"""
        d = excellent_progress.to_dict()

        assert d['durchschnittsnote_formatted'] == "1.70"

    def test_to_dict_note_formatted_none(self, no_grade_progress):
        """durchschnittsnote_formatted bei None"""
        d = no_grade_progress.to_dict()

        # Sollte Dash oder aehnliches sein
        assert d['durchschnittsnote_formatted'] in ["–", "-", "—", "â€"]

    def test_to_dict_fees_is_float(self, good_progress):
        """offene_gebuehren ist float in dict"""
        d = good_progress.to_dict()

        assert isinstance(d['offene_gebuehren'], float)
        assert d['offene_gebuehren'] == 199.0

    def test_to_dict_fees_formatted(self, good_progress):
        """offene_gebuehren_formatted ist formatierter String"""
        d = good_progress.to_dict()

        # Deutsches Format mit Euro-Zeichen
        formatted = d['offene_gebuehren_formatted']
        assert "199" in formatted
        assert "€" in formatted or "EUR" in formatted or "â‚¬" in formatted

    def test_to_dict_grade_category_fast(self, progress_class):
        """grade_category 'fast' bei Note <= 2.0"""
        p = progress_class(
            student_id=1,
            durchschnittsnote=Decimal("1.5"),
            anzahl_bestandene_module=10,
            anzahl_gebuchte_module=12,
            offene_gebuehren=Decimal("0"),
            aktuelles_semester=2.0,
            erwartetes_semester=2.0
        )
        d = p.to_dict()
        assert d['grade_category'] == 'fast'

    def test_to_dict_grade_category_medium(self, progress_class):
        """grade_category 'medium' bei Note 2.0-3.0"""
        p = progress_class(
            student_id=1,
            durchschnittsnote=Decimal("2.5"),
            anzahl_bestandene_module=10,
            anzahl_gebuchte_module=12,
            offene_gebuehren=Decimal("0"),
            aktuelles_semester=2.0,
            erwartetes_semester=2.0
        )
        d = p.to_dict()
        assert d['grade_category'] == 'medium'

    def test_to_dict_grade_category_slow(self, progress_class):
        """grade_category 'slow' bei Note > 3.0"""
        p = progress_class(
            student_id=1,
            durchschnittsnote=Decimal("3.5"),
            anzahl_bestandene_module=10,
            anzahl_gebuchte_module=12,
            offene_gebuehren=Decimal("0"),
            aktuelles_semester=2.0,
            erwartetes_semester=2.0
        )
        d = p.to_dict()
        assert d['grade_category'] == 'slow'

    def test_to_dict_grade_category_unknown(self, no_grade_progress):
        """grade_category 'unknown' bei None-Note"""
        d = no_grade_progress.to_dict()
        assert d['grade_category'] == 'unknown'

    def test_to_dict_fee_category_zero(self, excellent_progress):
        """fee_category 'zero' bei keine offenen Gebuehren"""
        d = excellent_progress.to_dict()
        assert d['fee_category'] == 'zero'

    def test_to_dict_fee_category_open(self, good_progress):
        """fee_category 'open' bei offenen Gebuehren"""
        d = good_progress.to_dict()
        assert d['fee_category'] == 'open'

    def test_to_dict_time_category_plus(self, progress_class):
        """time_category 'plus' wenn voraus"""
        p = progress_class(
            student_id=1,
            durchschnittsnote=Decimal("2.0"),
            anzahl_bestandene_module=10,
            anzahl_gebuchte_module=12,
            offene_gebuehren=Decimal("0"),
            aktuelles_semester=3.0,
            erwartetes_semester=2.0  # Voraus
        )
        d = p.to_dict()
        assert d['time_category'] == 'plus'

    def test_to_dict_time_category_minus(self, progress_class):
        """time_category 'minus' wenn hinterher"""
        p = progress_class(
            student_id=1,
            durchschnittsnote=Decimal("2.0"),
            anzahl_bestandene_module=10,
            anzahl_gebuchte_module=12,
            offene_gebuehren=Decimal("0"),
            aktuelles_semester=2.0,
            erwartetes_semester=3.0  # Hinterher
        )
        d = p.to_dict()
        assert d['time_category'] == 'minus'

    def test_to_dict_is_on_schedule_true(self, excellent_progress):
        """is_on_schedule ist True wenn im Zeitplan"""
        d = excellent_progress.to_dict()
        assert d['is_on_schedule'] is True

    def test_to_dict_is_on_schedule_false(self, critical_progress):
        """is_on_schedule ist False wenn nicht im Zeitplan"""
        d = critical_progress.to_dict()
        assert d['is_on_schedule'] is False

    def test_to_dict_tage_differenz(self, progress_class):
        """tage_differenz wird korrekt berechnet"""
        p = progress_class(
            student_id=1,
            durchschnittsnote=Decimal("2.0"),
            anzahl_bestandene_module=10,
            anzahl_gebuchte_module=12,
            offene_gebuehren=Decimal("0"),
            aktuelles_semester=3.0,
            erwartetes_semester=2.0  # 1 Semester voraus = 180 Tage
        )
        d = p.to_dict()
        assert d['tage_differenz'] == 180

    def test_to_dict_is_json_serializable(self, excellent_progress):
        """to_dict() Ergebnis ist JSON-serialisierbar"""
        import json

        d = excellent_progress.to_dict()

        # Sollte nicht werfen
        json_str = json.dumps(d)
        assert isinstance(json_str, str)


# ============================================================================
# STRING REPRESENTATION TESTS
# ============================================================================

class TestStringRepresentation:
    """Tests fuer __str__ und __repr__"""

    def test_str_contains_student_id(self, excellent_progress):
        """__str__ enthaelt Student-ID"""
        s = str(excellent_progress)
        assert "1" in s

    def test_str_contains_note(self, excellent_progress):
        """__str__ enthaelt Note"""
        s = str(excellent_progress)
        assert "1.70" in s or "1.7" in s

    def test_str_contains_semester(self, excellent_progress):
        """__str__ enthaelt Semester"""
        s = str(excellent_progress)
        assert "3.5" in s

    def test_str_with_none_note(self, no_grade_progress):
        """__str__ mit None-Note zeigt Dash"""
        s = str(no_grade_progress)
        # Sollte Dash oder aehnliches zeigen
        assert "–" in s or "-" in s or "—" in s or "None" in s or "â€" in s

    def test_repr_contains_class_name(self, excellent_progress):
        """__repr__ enthaelt Klassennamen"""
        r = repr(excellent_progress)
        assert "Progress" in r

    def test_repr_contains_student_id(self, excellent_progress):
        """__repr__ enthaelt student_id"""
        r = repr(excellent_progress)
        assert "student_id=1" in r

    def test_repr_contains_note(self, excellent_progress):
        """__repr__ enthaelt Note"""
        r = repr(excellent_progress)
        assert "note=" in r

    def test_repr_contains_semester(self, excellent_progress):
        """__repr__ enthaelt Semester"""
        r = repr(excellent_progress)
        assert "semester=" in r

    def test_repr_contains_fees(self, excellent_progress):
        """__repr__ enthaelt Gebuehren"""
        r = repr(excellent_progress)
        assert "fees=" in r


# ============================================================================
# EDGE CASES
# ============================================================================

class TestEdgeCases:
    """Tests fuer Randfaelle"""

    def test_very_good_note(self, progress_class):
        """Sehr gute Note 1.0"""
        p = progress_class(
            student_id=1,
            durchschnittsnote=Decimal("1.0"),
            anzahl_bestandene_module=49,
            anzahl_gebuchte_module=49,
            offene_gebuehren=Decimal("0"),
            aktuelles_semester=7.0,
            erwartetes_semester=7.0
        )

        assert p.calculate_overall_status() == 'excellent'
        d = p.to_dict()
        assert d['grade_category'] == 'fast'

    def test_failing_note(self, progress_class):
        """Durchfallnote 5.0"""
        p = progress_class(
            student_id=1,
            durchschnittsnote=Decimal("5.0"),
            anzahl_bestandene_module=0,
            anzahl_gebuchte_module=5,
            offene_gebuehren=Decimal("1000.00"),
            aktuelles_semester=1.0,
            erwartetes_semester=3.0
        )

        assert p.calculate_overall_status() == 'critical'
        d = p.to_dict()
        assert d['grade_category'] == 'slow'

    def test_large_fees(self, progress_class):
        """Sehr grosse offene Gebuehren"""
        p = progress_class(
            student_id=1,
            durchschnittsnote=Decimal("2.0"),
            anzahl_bestandene_module=10,
            anzahl_gebuchte_module=12,
            offene_gebuehren=Decimal("99999.99"),
            aktuelles_semester=2.0,
            erwartetes_semester=2.0
        )

        d = p.to_dict()
        assert d['fee_category'] == 'open'
        # Formatierung sollte funktionieren
        assert len(d['offene_gebuehren_formatted']) > 0

    def test_zero_fees(self, progress_class):
        """Keine offenen Gebuehren"""
        p = progress_class(
            student_id=1,
            durchschnittsnote=Decimal("2.0"),
            anzahl_bestandene_module=10,
            anzahl_gebuchte_module=12,
            offene_gebuehren=Decimal("0"),
            aktuelles_semester=2.0,
            erwartetes_semester=2.0
        )

        d = p.to_dict()
        assert d['fee_category'] == 'zero'
        assert d['offene_gebuehren'] == 0.0

    def test_far_ahead_of_schedule(self, progress_class):
        """Weit vor dem Zeitplan"""
        p = progress_class(
            student_id=1,
            durchschnittsnote=Decimal("1.5"),
            anzahl_bestandene_module=30,
            anzahl_gebuchte_module=32,
            offene_gebuehren=Decimal("0"),
            aktuelles_semester=5.0,
            erwartetes_semester=2.0  # 3 Semester voraus
        )

        d = p.to_dict()
        assert d['time_category'] == 'plus'
        assert d['tage_differenz'] == 540  # 3 * 180 Tage

    def test_far_behind_schedule(self, progress_class):
        """Weit hinter dem Zeitplan"""
        p = progress_class(
            student_id=1,
            durchschnittsnote=Decimal("3.0"),
            anzahl_bestandene_module=5,
            anzahl_gebuchte_module=8,
            offene_gebuehren=Decimal("500.00"),
            aktuelles_semester=1.0,
            erwartetes_semester=5.0  # 4 Semester hinterher
        )

        d = p.to_dict()
        assert d['time_category'] == 'minus'
        assert d['tage_differenz'] == -720  # -4 * 180 Tage

    def test_exactly_on_schedule_boundary(self, progress_class):
        """Genau an der Zeitplan-Grenze (30 Tage)"""
        # 30 Tage = 30/180 = 0.1666... Semester
        p = progress_class(
            student_id=1,
            durchschnittsnote=Decimal("2.0"),
            anzahl_bestandene_module=10,
            anzahl_gebuchte_module=12,
            offene_gebuehren=Decimal("0"),
            aktuelles_semester=2.0,
            erwartetes_semester=2.0
        )

        d = p.to_dict()
        assert d['is_on_schedule'] is True

    def test_float_semester_values(self, progress_class):
        """Gleitkomma-Semesterwerte"""
        p = progress_class(
            student_id=1,
            durchschnittsnote=Decimal("2.0"),
            anzahl_bestandene_module=10,
            anzahl_gebuchte_module=12,
            offene_gebuehren=Decimal("0"),
            aktuelles_semester=2.75,
            erwartetes_semester=2.25
        )

        d = p.to_dict()
        assert d['aktuelles_semester'] == 2.75
        assert d['erwartetes_semester'] == 2.25


# ============================================================================
# DATACLASS TESTS
# ============================================================================

class TestDataclass:
    """Tests fuer Dataclass-Eigenschaften"""

    def test_equality_same_values(self, progress_class):
        """Gleiche Werte bedeuten Gleichheit"""
        p1 = progress_class(
            student_id=1,
            durchschnittsnote=Decimal("2.0"),
            anzahl_bestandene_module=10,
            anzahl_gebuchte_module=12,
            offene_gebuehren=Decimal("100"),
            aktuelles_semester=2.0,
            erwartetes_semester=2.0
        )
        p2 = progress_class(
            student_id=1,
            durchschnittsnote=Decimal("2.0"),
            anzahl_bestandene_module=10,
            anzahl_gebuchte_module=12,
            offene_gebuehren=Decimal("100"),
            aktuelles_semester=2.0,
            erwartetes_semester=2.0
        )

        assert p1 == p2

    def test_inequality_different_student_id(self, progress_class):
        """Unterschiedliche student_id bedeutet Ungleichheit"""
        p1 = progress_class(
            student_id=1,
            durchschnittsnote=Decimal("2.0"),
            anzahl_bestandene_module=10,
            anzahl_gebuchte_module=12,
            offene_gebuehren=Decimal("100"),
            aktuelles_semester=2.0,
            erwartetes_semester=2.0
        )
        p2 = progress_class(
            student_id=2,  # Andere ID
            durchschnittsnote=Decimal("2.0"),
            anzahl_bestandene_module=10,
            anzahl_gebuchte_module=12,
            offene_gebuehren=Decimal("100"),
            aktuelles_semester=2.0,
            erwartetes_semester=2.0
        )

        assert p1 != p2


# ============================================================================
# TYPE CHECKING TESTS
# ============================================================================

class TestTypeChecking:
    """Tests fuer Typenpruefung"""

    def test_student_id_is_int(self, excellent_progress):
        """student_id ist int"""
        assert isinstance(excellent_progress.student_id, int)

    def test_durchschnittsnote_is_decimal_or_none(self, excellent_progress, no_grade_progress):
        """durchschnittsnote ist Decimal oder None"""
        assert isinstance(excellent_progress.durchschnittsnote, Decimal)
        assert no_grade_progress.durchschnittsnote is None

    def test_anzahl_bestandene_module_is_int(self, excellent_progress):
        """anzahl_bestandene_module ist int"""
        assert isinstance(excellent_progress.anzahl_bestandene_module, int)

    def test_anzahl_gebuchte_module_is_int(self, excellent_progress):
        """anzahl_gebuchte_module ist int"""
        assert isinstance(excellent_progress.anzahl_gebuchte_module, int)

    def test_offene_gebuehren_is_decimal(self, excellent_progress):
        """offene_gebuehren ist Decimal"""
        assert isinstance(excellent_progress.offene_gebuehren, Decimal)

    def test_aktuelles_semester_is_float(self, excellent_progress):
        """aktuelles_semester ist float"""
        assert isinstance(excellent_progress.aktuelles_semester, float)

    def test_erwartetes_semester_is_float(self, excellent_progress):
        """erwartetes_semester ist float"""
        assert isinstance(excellent_progress.erwartetes_semester, float)

    def test_calculate_overall_status_returns_str(self, excellent_progress):
        """calculate_overall_status() gibt str zurueck"""
        assert isinstance(excellent_progress.calculate_overall_status(), str)

    def test_get_completion_percentage_returns_float(self, excellent_progress):
        """get_completion_percentage() gibt float zurueck"""
        assert isinstance(excellent_progress.get_completion_percentage(), float)

    def test_to_dict_returns_dict(self, excellent_progress):
        """to_dict() gibt dict zurueck"""
        assert isinstance(excellent_progress.to_dict(), dict)