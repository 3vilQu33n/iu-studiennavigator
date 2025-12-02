# tests/unit/test_einschreibung.py
"""
Unit Tests fuer Einschreibung Model

Testet Domain Model, Validierung, Konvertierung und Status-Methoden.
"""
import pytest
from datetime import date, timedelta
from unittest.mock import MagicMock

from models.einschreibung import (
    Einschreibung,
    EinschreibungError,
    ValidationError,
    DatabaseError,
    NotFoundError
)

# Mark this whole module as unit test
pytestmark = pytest.mark.unit


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def valid_einschreibung():
    """Gueltige Einschreibung mit Standardwerten"""
    return Einschreibung(
        id=1,
        student_id=1,
        studiengang_id=1,
        zeitmodell_id=1,
        start_datum=date(2024, 1, 1),
        status="aktiv"
    )


@pytest.fixture
def einschreibung_ohne_id():
    """Einschreibung ohne ID (fuer Insert)"""
    return Einschreibung(
        id=None,
        student_id=1,
        studiengang_id=1,
        zeitmodell_id=1,
        start_datum=date(2024, 1, 1),
        status="aktiv"
    )


@pytest.fixture
def pausierte_einschreibung():
    """Pausierte Einschreibung"""
    return Einschreibung(
        id=2,
        student_id=1,
        studiengang_id=1,
        zeitmodell_id=1,
        start_datum=date(2024, 1, 1),
        status="pausiert"
    )


@pytest.fixture
def exmatrikulierte_einschreibung():
    """Exmatrikulierte Einschreibung"""
    return Einschreibung(
        id=3,
        student_id=1,
        studiengang_id=1,
        zeitmodell_id=1,
        start_datum=date(2023, 1, 1),
        exmatrikulations_datum=date(2024, 6, 30),
        status="exmatrikuliert"
    )


# ============================================================================
# INITIALIZATION TESTS
# ============================================================================

class TestEinschreibungInit:
    """Tests fuer Einschreibung Initialisierung"""

    def test_create_valid_einschreibung(self):
        """Test: Gueltige Einschreibung erstellen"""
        einschreibung = Einschreibung(
            id=1,
            student_id=1,
            studiengang_id=1,
            zeitmodell_id=1,
            start_datum=date(2024, 1, 1),
            status="aktiv"
        )

        assert einschreibung.id == 1
        assert einschreibung.student_id == 1
        assert einschreibung.status == "aktiv"

    def test_create_einschreibung_without_id(self):
        """Test: Einschreibung ohne ID (fuer Insert)"""
        einschreibung = Einschreibung(
            id=None,
            student_id=1,
            studiengang_id=1,
            zeitmodell_id=1,
            start_datum=date(2024, 1, 1)
        )

        assert einschreibung.id is None

    def test_default_status_is_aktiv(self):
        """Test: Standard-Status ist 'aktiv'"""
        einschreibung = Einschreibung(
            id=1,
            student_id=1,
            studiengang_id=1,
            zeitmodell_id=1,
            start_datum=date(2024, 1, 1)
        )

        assert einschreibung.status == "aktiv"

    def test_default_exmatrikulations_datum_is_none(self):
        """Test: Standard exmatrikulations_datum ist None"""
        einschreibung = Einschreibung(
            id=1,
            student_id=1,
            studiengang_id=1,
            zeitmodell_id=1,
            start_datum=date(2024, 1, 1)
        )

        assert einschreibung.exmatrikulations_datum is None

    def test_create_with_exmatrikulations_datum(self):
        """Test: Einschreibung mit Exmatrikulationsdatum"""
        einschreibung = Einschreibung(
            id=1,
            student_id=1,
            studiengang_id=1,
            zeitmodell_id=1,
            start_datum=date(2023, 1, 1),
            exmatrikulations_datum=date(2024, 6, 30),
            status="exmatrikuliert"
        )

        assert einschreibung.exmatrikulations_datum == date(2024, 6, 30)


# ============================================================================
# DATE CONVERSION TESTS (in __post_init__)
# ============================================================================

class TestDateConversion:
    """Tests fuer Datum-Konvertierung in __post_init__"""

    def test_start_datum_string_conversion(self):
        """Test: String wird zu date konvertiert"""
        einschreibung = Einschreibung(
            id=1,
            student_id=1,
            studiengang_id=1,
            zeitmodell_id=1,
            start_datum="2024-01-15",
            status="aktiv"
        )

        assert isinstance(einschreibung.start_datum, date)
        assert einschreibung.start_datum == date(2024, 1, 15)

    def test_exmatrikulations_datum_string_conversion(self):
        """Test: exmatrikulations_datum String wird konvertiert"""
        einschreibung = Einschreibung(
            id=1,
            student_id=1,
            studiengang_id=1,
            zeitmodell_id=1,
            start_datum=date(2023, 1, 1),
            exmatrikulations_datum="2024-06-30",
            status="exmatrikuliert"
        )

        assert isinstance(einschreibung.exmatrikulations_datum, date)
        assert einschreibung.exmatrikulations_datum == date(2024, 6, 30)

    def test_invalid_start_datum_string_raises_error(self):
        """Test: Ungueltiger Datum-String wirft ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            Einschreibung(
                id=1,
                student_id=1,
                studiengang_id=1,
                zeitmodell_id=1,
                start_datum="invalid-date",
                status="aktiv"
            )

        assert "start_datum" in str(exc_info.value)

    def test_invalid_exmatrikulations_datum_string_raises_error(self):
        """Test: Ungueltiger exmatrikulations_datum String wirft Error"""
        with pytest.raises(ValidationError) as exc_info:
            Einschreibung(
                id=1,
                student_id=1,
                studiengang_id=1,
                zeitmodell_id=1,
                start_datum=date(2023, 1, 1),
                exmatrikulations_datum="not-a-date",
                status="aktiv"
            )

        assert "exmatrikulations_datum" in str(exc_info.value)


# ============================================================================
# VALIDATION TESTS
# ============================================================================

class TestValidation:
    """Tests fuer validate() Methode"""

    def test_valid_einschreibung_passes(self, valid_einschreibung):
        """Test: Gueltige Einschreibung passiert Validierung"""
        # Sollte keine Exception werfen
        valid_einschreibung.validate()

    def test_invalid_status_raises_error(self):
        """Test: Ungueltiger Status wirft ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            Einschreibung(
                id=1,
                student_id=1,
                studiengang_id=1,
                zeitmodell_id=1,
                start_datum=date(2024, 1, 1),
                status="ungueltig"
            )

        assert "Status" in str(exc_info.value)

    def test_invalid_student_id_zero(self):
        """Test: student_id = 0 wirft ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            Einschreibung(
                id=1,
                student_id=0,
                studiengang_id=1,
                zeitmodell_id=1,
                start_datum=date(2024, 1, 1)
            )

        assert "student_id" in str(exc_info.value)

    def test_invalid_student_id_negative(self):
        """Test: Negative student_id wirft ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            Einschreibung(
                id=1,
                student_id=-1,
                studiengang_id=1,
                zeitmodell_id=1,
                start_datum=date(2024, 1, 1)
            )

        assert "student_id" in str(exc_info.value)

    def test_invalid_studiengang_id(self):
        """Test: Ungueltige studiengang_id wirft ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            Einschreibung(
                id=1,
                student_id=1,
                studiengang_id=0,
                zeitmodell_id=1,
                start_datum=date(2024, 1, 1)
            )

        assert "studiengang_id" in str(exc_info.value)

    def test_invalid_zeitmodell_id(self):
        """Test: Ungueltige zeitmodell_id wirft ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            Einschreibung(
                id=1,
                student_id=1,
                studiengang_id=1,
                zeitmodell_id=-5,
                start_datum=date(2024, 1, 1)
            )

        assert "zeitmodell_id" in str(exc_info.value)


# ============================================================================
# STATUS METHODS TESTS
# ============================================================================

class TestStatusMethods:
    """Tests fuer Status-Pruefmethoden"""

    def test_is_active_true(self, valid_einschreibung):
        """Test: is_active() gibt True fuer aktive Einschreibung"""
        assert valid_einschreibung.is_active() is True

    def test_is_active_false_for_paused(self, pausierte_einschreibung):
        """Test: is_active() gibt False fuer pausierte Einschreibung"""
        assert pausierte_einschreibung.is_active() is False

    def test_is_active_false_for_exmatriculated(self, exmatrikulierte_einschreibung):
        """Test: is_active() gibt False fuer exmatrikulierte Einschreibung"""
        assert exmatrikulierte_einschreibung.is_active() is False

    def test_is_paused_true(self, pausierte_einschreibung):
        """Test: is_paused() gibt True fuer pausierte Einschreibung"""
        assert pausierte_einschreibung.is_paused() is True

    def test_is_paused_false_for_active(self, valid_einschreibung):
        """Test: is_paused() gibt False fuer aktive Einschreibung"""
        assert valid_einschreibung.is_paused() is False

    def test_is_exmatriculated_true(self, exmatrikulierte_einschreibung):
        """Test: is_exmatriculated() gibt True fuer exmatrikulierte"""
        assert exmatrikulierte_einschreibung.is_exmatriculated() is True

    def test_is_exmatriculated_false_for_active(self, valid_einschreibung):
        """Test: is_exmatriculated() gibt False fuer aktive"""
        assert valid_einschreibung.is_exmatriculated() is False

    def test_all_status_methods_mutually_exclusive(self):
        """Test: Nur eine Status-Methode ist True"""
        for status in ["aktiv", "pausiert", "exmatrikuliert"]:
            einschreibung = Einschreibung(
                id=1,
                student_id=1,
                studiengang_id=1,
                zeitmodell_id=1,
                start_datum=date(2024, 1, 1),
                status=status
            )

            status_results = [
                einschreibung.is_active(),
                einschreibung.is_paused(),
                einschreibung.is_exmatriculated()
            ]

            # Genau eine sollte True sein
            assert sum(status_results) == 1


# ============================================================================
# GET_STUDY_DURATION_MONTHS TESTS
# ============================================================================

class TestGetStudyDurationMonths:
    """Tests fuer get_study_duration_months() Methode"""

    def test_duration_zero_same_month(self):
        """Test: 0 Monate wenn Start im gleichen Monat"""
        einschreibung = Einschreibung(
            id=1,
            student_id=1,
            studiengang_id=1,
            zeitmodell_id=1,
            start_datum=date.today().replace(day=1),
            status="aktiv"
        )

        assert einschreibung.get_study_duration_months() == 0

    def test_duration_one_month(self):
        """Test: 1 Monat Differenz"""
        start = date.today().replace(day=1) - timedelta(days=32)
        einschreibung = Einschreibung(
            id=1,
            student_id=1,
            studiengang_id=1,
            zeitmodell_id=1,
            start_datum=start,
            status="aktiv"
        )

        duration = einschreibung.get_study_duration_months()
        assert duration >= 1

    def test_duration_twelve_months(self):
        """Test: 12 Monate (1 Jahr) Differenz"""
        today = date.today()
        start = date(today.year - 1, today.month, 1)

        einschreibung = Einschreibung(
            id=1,
            student_id=1,
            studiengang_id=1,
            zeitmodell_id=1,
            start_datum=start,
            status="aktiv"
        )

        assert einschreibung.get_study_duration_months() == 12

    def test_duration_with_reference_date(self):
        """Test: Dauer mit explizitem Referenzdatum"""
        einschreibung = Einschreibung(
            id=1,
            student_id=1,
            studiengang_id=1,
            zeitmodell_id=1,
            start_datum=date(2024, 1, 1),
            status="aktiv"
        )

        reference = date(2024, 7, 1)
        duration = einschreibung.get_study_duration_months(reference)

        assert duration == 6

    def test_duration_never_negative(self):
        """Test: Dauer ist niemals negativ"""
        # Start in der Zukunft
        future_start = date.today() + timedelta(days=365)
        einschreibung = Einschreibung(
            id=1,
            student_id=1,
            studiengang_id=1,
            zeitmodell_id=1,
            start_datum=future_start,
            status="aktiv"
        )

        assert einschreibung.get_study_duration_months() >= 0


# ============================================================================
# TO_DICT TESTS
# ============================================================================

class TestToDict:
    """Tests fuer to_dict() Methode"""

    def test_to_dict_contains_all_fields(self, valid_einschreibung):
        """Test: to_dict() enthaelt alle Felder"""
        result = valid_einschreibung.to_dict()

        expected_keys = [
            'id', 'student_id', 'studiengang_id', 'zeitmodell_id',
            'start_datum', 'exmatrikulations_datum', 'status',
            'is_active', 'is_paused', 'study_duration_months'
        ]

        for key in expected_keys:
            assert key in result, f"Key '{key}' fehlt in to_dict()"

    def test_to_dict_start_datum_is_iso_string(self, valid_einschreibung):
        """Test: start_datum ist ISO-String"""
        result = valid_einschreibung.to_dict()

        assert result['start_datum'] == "2024-01-01"

    def test_to_dict_exmatrikulations_datum_is_iso_string(self, exmatrikulierte_einschreibung):
        """Test: exmatrikulations_datum ist ISO-String"""
        result = exmatrikulierte_einschreibung.to_dict()

        assert result['exmatrikulations_datum'] == "2024-06-30"

    def test_to_dict_exmatrikulations_datum_none(self, valid_einschreibung):
        """Test: exmatrikulations_datum ist None wenn nicht gesetzt"""
        result = valid_einschreibung.to_dict()

        assert result['exmatrikulations_datum'] is None

    def test_to_dict_is_active_value(self, valid_einschreibung):
        """Test: is_active Wert ist korrekt"""
        result = valid_einschreibung.to_dict()

        assert result['is_active'] is True

    def test_to_dict_is_paused_value(self, pausierte_einschreibung):
        """Test: is_paused Wert ist korrekt"""
        result = pausierte_einschreibung.to_dict()

        assert result['is_paused'] is True
        assert result['is_active'] is False


# ============================================================================
# FROM_ROW TESTS
# ============================================================================

class TestFromRow:
    """Tests fuer from_row() Factory Method"""

    def test_from_row_with_dict(self):
        """Test: from_row() mit Dictionary"""
        row = {
            'id': 1,
            'student_id': 1,
            'studiengang_id': 1,
            'zeitmodell_id': 1,
            'start_datum': '2024-01-01',
            'exmatrikulations_datum': None,
            'status': 'aktiv'
        }

        # MagicMock mit keys() Methode
        mock_row = MagicMock()
        mock_row.__getitem__ = lambda self, key: row[key]
        mock_row.keys.return_value = row.keys()

        einschreibung = Einschreibung.from_row(mock_row)

        assert einschreibung.id == 1
        assert einschreibung.student_id == 1
        assert einschreibung.status == "aktiv"

    def test_from_row_converts_string_dates(self):
        """Test: from_row() konvertiert String-Daten"""
        row = {
            'id': 1,
            'student_id': 1,
            'studiengang_id': 1,
            'zeitmodell_id': 1,
            'start_datum': '2024-03-15',
            'exmatrikulations_datum': '2024-09-30',
            'status': 'exmatrikuliert'
        }

        mock_row = MagicMock()
        mock_row.__getitem__ = lambda self, key: row[key]
        mock_row.keys.return_value = row.keys()

        einschreibung = Einschreibung.from_row(mock_row)

        assert isinstance(einschreibung.start_datum, date)
        assert einschreibung.start_datum == date(2024, 3, 15)
        assert isinstance(einschreibung.exmatrikulations_datum, date)
        assert einschreibung.exmatrikulations_datum == date(2024, 9, 30)

    def test_from_row_handles_date_objects(self):
        """Test: from_row() akzeptiert date-Objekte"""
        row = {
            'id': 1,
            'student_id': 1,
            'studiengang_id': 1,
            'zeitmodell_id': 1,
            'start_datum': date(2024, 1, 1),
            'exmatrikulations_datum': date(2024, 6, 30),
            'status': 'exmatrikuliert'
        }

        mock_row = MagicMock()
        mock_row.__getitem__ = lambda self, key: row[key]
        mock_row.keys.return_value = row.keys()

        einschreibung = Einschreibung.from_row(mock_row)

        assert einschreibung.start_datum == date(2024, 1, 1)

    def test_from_row_default_status(self):
        """Test: from_row() verwendet 'aktiv' wenn status fehlt"""
        row = {
            'id': 1,
            'student_id': 1,
            'studiengang_id': 1,
            'zeitmodell_id': 1,
            'start_datum': '2024-01-01',
            'exmatrikulations_datum': None
            # status fehlt
        }

        mock_row = MagicMock()
        mock_row.__getitem__ = lambda self, key: row[key]
        mock_row.keys.return_value = row.keys()

        einschreibung = Einschreibung.from_row(mock_row)

        assert einschreibung.status == "aktiv"

    def test_from_row_id_none(self):
        """Test: from_row() mit id = None"""
        row = {
            'id': None,
            'student_id': 1,
            'studiengang_id': 1,
            'zeitmodell_id': 1,
            'start_datum': '2024-01-01',
            'exmatrikulations_datum': None,
            'status': 'aktiv'
        }

        mock_row = MagicMock()
        mock_row.__getitem__ = lambda self, key: row[key]
        mock_row.keys.return_value = row.keys()

        einschreibung = Einschreibung.from_row(mock_row)

        assert einschreibung.id is None

    def test_from_row_invalid_data_raises_error(self):
        """Test: from_row() wirft ValidationError bei ungueltigen Daten"""
        row = {
            'id': 1,
            'student_id': -1,  # ungueltig
            'studiengang_id': 1,
            'zeitmodell_id': 1,
            'start_datum': '2024-01-01',
            'exmatrikulations_datum': None,
            'status': 'aktiv'
        }

        mock_row = MagicMock()
        mock_row.__getitem__ = lambda self, key: row[key]
        mock_row.keys.return_value = row.keys()

        with pytest.raises(ValidationError):
            Einschreibung.from_row(mock_row)


# ============================================================================
# STRING REPRESENTATION TESTS
# ============================================================================

class TestStringRepresentation:
    """Tests fuer __str__ und __repr__"""

    def test_str_contains_student_id(self, valid_einschreibung):
        """Test: __str__ enthaelt Student-ID"""
        result = str(valid_einschreibung)

        assert "Student 1" in result

    def test_str_contains_status(self, valid_einschreibung):
        """Test: __str__ enthaelt Status"""
        result = str(valid_einschreibung)

        assert "aktiv" in result

    def test_repr_contains_all_ids(self, valid_einschreibung):
        """Test: __repr__ enthaelt alle IDs"""
        result = repr(valid_einschreibung)

        assert "id=1" in result
        assert "student_id=1" in result
        assert "studiengang_id=1" in result

    def test_repr_contains_status(self, valid_einschreibung):
        """Test: __repr__ enthaelt Status"""
        result = repr(valid_einschreibung)

        assert "status='aktiv'" in result


# ============================================================================
# EXCEPTION TESTS
# ============================================================================

class TestExceptions:
    """Tests fuer Custom Exceptions"""

    def test_einschreibung_error_is_exception(self):
        """Test: EinschreibungError ist Exception"""
        assert issubclass(EinschreibungError, Exception)

    def test_validation_error_is_einschreibung_error(self):
        """Test: ValidationError erbt von EinschreibungError"""
        assert issubclass(ValidationError, EinschreibungError)

    def test_database_error_is_einschreibung_error(self):
        """Test: DatabaseError erbt von EinschreibungError"""
        assert issubclass(DatabaseError, EinschreibungError)

    def test_not_found_error_is_einschreibung_error(self):
        """Test: NotFoundError erbt von EinschreibungError"""
        assert issubclass(NotFoundError, EinschreibungError)

    def test_can_catch_all_with_einschreibung_error(self):
        """Test: Alle Exceptions mit EinschreibungError fangbar"""
        for exc_class in [ValidationError, DatabaseError, NotFoundError]:
            with pytest.raises(EinschreibungError):
                raise exc_class("Test")


# ============================================================================
# EDGE CASES
# ============================================================================

class TestEdgeCases:
    """Tests fuer Randfaelle"""

    def test_dataclass_is_immutable_by_slots(self, valid_einschreibung):
        """Test: Dataclass verwendet slots"""
        assert hasattr(valid_einschreibung, '__slots__') or \
               not hasattr(valid_einschreibung, '__dict__')

    def test_einschreibung_equality(self):
        """Test: Zwei Einschreibungen mit gleichen Werten sind gleich"""
        e1 = Einschreibung(
            id=1, student_id=1, studiengang_id=1, zeitmodell_id=1,
            start_datum=date(2024, 1, 1), status="aktiv"
        )
        e2 = Einschreibung(
            id=1, student_id=1, studiengang_id=1, zeitmodell_id=1,
            start_datum=date(2024, 1, 1), status="aktiv"
        )

        assert e1 == e2

    def test_einschreibung_inequality(self):
        """Test: Einschreibungen mit unterschiedlichen Werten sind ungleich"""
        e1 = Einschreibung(
            id=1, student_id=1, studiengang_id=1, zeitmodell_id=1,
            start_datum=date(2024, 1, 1), status="aktiv"
        )
        e2 = Einschreibung(
            id=2, student_id=1, studiengang_id=1, zeitmodell_id=1,
            start_datum=date(2024, 1, 1), status="aktiv"
        )

        assert e1 != e2

    def test_all_valid_statuses(self):
        """Test: Alle gueltigen Status-Werte"""
        for status in ["aktiv", "pausiert", "exmatrikuliert"]:
            einschreibung = Einschreibung(
                id=1, student_id=1, studiengang_id=1, zeitmodell_id=1,
                start_datum=date(2024, 1, 1), status=status
            )
            assert einschreibung.status == status

    def test_large_ids(self):
        """Test: Grosse IDs werden akzeptiert"""
        einschreibung = Einschreibung(
            id=999999999,
            student_id=888888888,
            studiengang_id=777777777,
            zeitmodell_id=666666666,
            start_datum=date(2024, 1, 1)
        )

        assert einschreibung.id == 999999999

    def test_old_start_datum(self):
        """Test: Sehr altes Startdatum funktioniert"""
        einschreibung = Einschreibung(
            id=1, student_id=1, studiengang_id=1, zeitmodell_id=1,
            start_datum=date(2000, 1, 1), status="aktiv"
        )

        duration = einschreibung.get_study_duration_months()
        assert duration > 200  # Mehr als 16 Jahre