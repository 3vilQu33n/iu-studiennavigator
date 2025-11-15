# tests/unit/test_einschreibung.py
"""
Unit Tests für Einschreibung Domain Model

Testet die Einschreibung-Klasse aus models/einschreibung.py
"""
import pytest
import sys
from pathlib import Path
from datetime import date

# Füge Project-Root zum Python-Path hinzu
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from models import (
    Einschreibung,
    ValidationError,
    EinschreibungError,
    DatabaseError,
    NotFoundError
)


# ============================================================================
# CREATION & VALIDATION TESTS
# ============================================================================

def test_einschreibung_create_valid():
    """Test: Gültige Einschreibung erstellen"""
    e = Einschreibung(
        id=1,
        student_id=1,
        studiengang_id=2,
        zeitmodell_id=3,
        start_datum=date(2024, 3, 17),
        status="aktiv"
    )

    assert e.id == 1
    assert e.student_id == 1
    assert e.studiengang_id == 2
    assert e.zeitmodell_id == 3
    assert e.start_datum == date(2024, 3, 17)
    assert e.status == "aktiv"


def test_einschreibung_create_with_string_date():
    """Test: Einschreibung mit String-Datum erstellen"""
    e = Einschreibung(
        id=None,
        student_id=1,
        studiengang_id=2,
        zeitmodell_id=3,
        start_datum="2024-03-17",  # String!
        status="aktiv"
    )

    assert isinstance(e.start_datum, date)
    assert e.start_datum == date(2024, 3, 17)


def test_einschreibung_default_status():
    """Test: Default Status ist 'aktiv'"""
    e = Einschreibung(
        id=None,
        student_id=1,
        studiengang_id=2,
        zeitmodell_id=3,
        start_datum=date(2024, 1, 1)
    )

    assert e.status == "aktiv"


def test_einschreibung_invalid_status():
    """Test: Ungültiger Status wirft ValidationError"""
    with pytest.raises(ValidationError):
        Einschreibung(
            id=None,
            student_id=1,
            studiengang_id=2,
            zeitmodell_id=3,
            start_datum=date(2024, 1, 1),
            status="ungültig"  # Nicht erlaubt!
        )


def test_einschreibung_invalid_student_id():
    """Test: Ungültige student_id wirft ValidationError"""
    with pytest.raises(ValidationError):
        Einschreibung(
            id=None,
            student_id=0,  # Ungültig!
            studiengang_id=2,
            zeitmodell_id=3,
            start_datum=date(2024, 1, 1),
            status="aktiv"
        )


def test_einschreibung_invalid_studiengang_id():
    """Test: Ungültige studiengang_id wirft ValidationError"""
    with pytest.raises(ValidationError):
        Einschreibung(
            id=None,
            student_id=1,
            studiengang_id=-1,  # Ungültig!
            zeitmodell_id=3,
            start_datum=date(2024, 1, 1),
            status="aktiv"
        )


def test_einschreibung_invalid_zeitmodell_id():
    """Test: Ungültige zeitmodell_id wirft ValidationError"""
    with pytest.raises(ValidationError):
        Einschreibung(
            id=None,
            student_id=1,
            studiengang_id=2,
            zeitmodell_id=0,  # Ungültig!
            start_datum=date(2024, 1, 1),
            status="aktiv"
        )


def test_einschreibung_invalid_date_string():
    """Test: Ungültiges Datum-String wirft ValidationError"""
    with pytest.raises(ValidationError):
        Einschreibung(
            id=None,
            student_id=1,
            studiengang_id=2,
            zeitmodell_id=3,
            start_datum="invalid-date",  # Ungültig!
            status="aktiv"
        )


# ============================================================================
# STATUS METHODS TESTS
# ============================================================================

def test_is_active():
    """Test: is_active() Methode"""
    e_aktiv = Einschreibung(
        id=1, student_id=1, studiengang_id=2, zeitmodell_id=3,
        start_datum=date(2024, 1, 1), status="aktiv"
    )
    assert e_aktiv.is_active() is True

    e_pausiert = Einschreibung(
        id=2, student_id=1, studiengang_id=2, zeitmodell_id=3,
        start_datum=date(2024, 1, 1), status="pausiert"
    )
    assert e_pausiert.is_active() is False


def test_is_paused():
    """Test: is_paused() Methode"""
    e_pausiert = Einschreibung(
        id=1, student_id=1, studiengang_id=2, zeitmodell_id=3,
        start_datum=date(2024, 1, 1), status="pausiert"
    )
    assert e_pausiert.is_paused() is True

    e_aktiv = Einschreibung(
        id=2, student_id=1, studiengang_id=2, zeitmodell_id=3,
        start_datum=date(2024, 1, 1), status="aktiv"
    )
    assert e_aktiv.is_paused() is False


def test_is_exmatriculated():
    """Test: is_exmatriculated() Methode"""
    e_exmatrikuliert = Einschreibung(
        id=1, student_id=1, studiengang_id=2, zeitmodell_id=3,
        start_datum=date(2024, 1, 1), status="exmatrikuliert"
    )
    assert e_exmatrikuliert.is_exmatriculated() is True

    e_aktiv = Einschreibung(
        id=2, student_id=1, studiengang_id=2, zeitmodell_id=3,
        start_datum=date(2024, 1, 1), status="aktiv"
    )
    assert e_aktiv.is_exmatriculated() is False


# ============================================================================
# DURATION CALCULATION TESTS
# ============================================================================

def test_get_study_duration_months():
    """Test: Studiendauer in Monaten berechnen"""
    e = Einschreibung(
        id=1, student_id=1, studiengang_id=2, zeitmodell_id=3,
        start_datum=date(2024, 1, 1), status="aktiv"
    )

    # 5 Monate später (Jan -> Jun = 5 Monate)
    duration = e.get_study_duration_months(reference_date=date(2024, 6, 15))
    assert duration == 5


def test_get_study_duration_months_same_month():
    """Test: Studiendauer im gleichen Monat = 0"""
    e = Einschreibung(
        id=1, student_id=1, studiengang_id=2, zeitmodell_id=3,
        start_datum=date(2024, 1, 15), status="aktiv"
    )

    duration = e.get_study_duration_months(reference_date=date(2024, 1, 20))
    assert duration == 0


def test_get_study_duration_months_default_today():
    """Test: Studiendauer ohne reference_date verwendet heute"""
    e = Einschreibung(
        id=1, student_id=1, studiengang_id=2, zeitmodell_id=3,
        start_datum=date(2020, 1, 1), status="aktiv"
    )

    duration = e.get_study_duration_months()
    # Sollte > 48 Monate sein (4+ Jahre)
    assert duration > 48


def test_get_study_duration_months_negative_prevented():
    """Test: Negative Studiendauer wird verhindert"""
    e = Einschreibung(
        id=1, student_id=1, studiengang_id=2, zeitmodell_id=3,
        start_datum=date(2024, 6, 1), status="aktiv"
    )

    # Reference date VOR start_datum
    duration = e.get_study_duration_months(reference_date=date(2024, 1, 1))
    assert duration == 0  # Sollte nicht negativ sein!


# ============================================================================
# TO_DICT TESTS
# ============================================================================

def test_to_dict():
    """Test: to_dict() Konvertierung"""
    e = Einschreibung(
        id=42,
        student_id=1,
        studiengang_id=2,
        zeitmodell_id=3,
        start_datum=date(2024, 3, 17),
        status="aktiv"
    )

    data = e.to_dict()

    assert data['id'] == 42
    assert data['student_id'] == 1
    assert data['studiengang_id'] == 2
    assert data['zeitmodell_id'] == 3
    assert data['start_datum'] == "2024-03-17"
    assert data['status'] == "aktiv"
    assert data['is_active'] is True
    assert data['is_paused'] is False
    assert 'study_duration_months' in data


def test_to_dict_pausiert():
    """Test: to_dict() mit Status 'pausiert'"""
    e = Einschreibung(
        id=1, student_id=1, studiengang_id=2, zeitmodell_id=3,
        start_datum=date(2024, 1, 1), status="pausiert"
    )

    data = e.to_dict()

    assert data['is_active'] is False
    assert data['is_paused'] is True


# ============================================================================
# FROM_ROW TESTS
# ============================================================================

def test_from_row_with_dict():
    """Test: from_row() mit Dictionary"""
    row_data = {
        'id': 42,
        'student_id': 1,
        'studiengang_id': 2,
        'zeitmodell_id': 3,
        'start_datum': "2024-03-17",
        'status': 'aktiv'
    }

    e = Einschreibung.from_row(row_data)

    assert e.id == 42
    assert e.student_id == 1
    assert e.studiengang_id == 2
    assert e.zeitmodell_id == 3
    assert e.start_datum == date(2024, 3, 17)
    assert e.status == "aktiv"


def test_from_row_with_date_object():
    """Test: from_row() mit date-Objekt"""
    row_data = {
        'id': 42,
        'student_id': 1,
        'studiengang_id': 2,
        'zeitmodell_id': 3,
        'start_datum': date(2024, 3, 17),  # Bereits date-Objekt!
        'status': 'aktiv'
    }

    e = Einschreibung.from_row(row_data)

    assert e.start_datum == date(2024, 3, 17)


def test_from_row_without_id():
    """Test: from_row() ohne ID (None)"""
    row_data = {
        'id': None,
        'student_id': 1,
        'studiengang_id': 2,
        'zeitmodell_id': 3,
        'start_datum': "2024-03-17",
        'status': 'aktiv'
    }

    e = Einschreibung.from_row(row_data)

    assert e.id is None


def test_from_row_default_status():
    """Test: from_row() ohne Status verwendet 'aktiv' als Default"""
    row_data = {
        'id': 42,
        'student_id': 1,
        'studiengang_id': 2,
        'zeitmodell_id': 3,
        'start_datum': "2024-03-17"
        # Kein 'status'!
    }

    e = Einschreibung.from_row(row_data)

    assert e.status == "aktiv"


def test_from_row_invalid_data():
    """Test: from_row() mit ungültigen Daten wirft ValidationError"""
    row_data = {
        'id': 42,
        'student_id': 0,  # Ungültig!
        'studiengang_id': 2,
        'zeitmodell_id': 3,
        'start_datum': "2024-03-17",
        'status': 'aktiv'
    }

    with pytest.raises(ValidationError):
        Einschreibung.from_row(row_data)


# ============================================================================
# STRING REPRESENTATION TESTS
# ============================================================================

def test_str_representation():
    """Test: __str__() Methode"""
    e = Einschreibung(
        id=1, student_id=42, studiengang_id=2, zeitmodell_id=3,
        start_datum=date(2024, 1, 1), status="aktiv"
    )

    s = str(e)

    assert "Student 42" in s
    assert "aktiv" in s


def test_repr_representation():
    """Test: __repr__() Methode"""
    e = Einschreibung(
        id=1, student_id=42, studiengang_id=2, zeitmodell_id=3,
        start_datum=date(2024, 1, 1), status="aktiv"
    )

    r = repr(e)

    assert "Einschreibung" in r
    assert "id=1" in r
    assert "student_id=42" in r
    assert "studiengang_id=2" in r
    assert "aktiv" in r


# ============================================================================
# EXCEPTION TESTS
# ============================================================================

def test_validation_error_is_einschreibung_error():
    """Test: ValidationError ist Subklasse von EinschreibungError"""
    assert issubclass(ValidationError, EinschreibungError)


def test_database_error_is_einschreibung_error():
    """Test: DatabaseError ist Subklasse von EinschreibungError"""
    assert issubclass(DatabaseError, EinschreibungError)


def test_not_found_error_is_einschreibung_error():
    """Test: NotFoundError ist Subklasse von EinschreibungError"""
    assert issubclass(NotFoundError, EinschreibungError)


def test_validation_error_can_be_raised():
    """Test: ValidationError kann geworfen werden"""
    with pytest.raises(ValidationError) as exc_info:
        raise ValidationError("Test-Fehler")

    assert "Test-Fehler" in str(exc_info.value)


# ============================================================================
# EDGE CASES
# ============================================================================

def test_einschreibung_with_all_statuses():
    """Test: Einschreibung mit allen erlaubten Statuses"""
    for status in ["aktiv", "pausiert", "exmatrikuliert"]:
        e = Einschreibung(
            id=None, student_id=1, studiengang_id=2, zeitmodell_id=3,
            start_datum=date(2024, 1, 1), status=status
        )
        assert e.status == status


def test_einschreibung_validates_on_creation():
    """Test: Validierung wird automatisch bei Erstellung aufgerufen"""
    # Sollte ValidationError werfen weil student_id = 0
    with pytest.raises(ValidationError):
        Einschreibung(
            id=None,
            student_id=0,  # Ungültig!
            studiengang_id=2,
            zeitmodell_id=3,
            start_datum=date(2024, 1, 1)
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])