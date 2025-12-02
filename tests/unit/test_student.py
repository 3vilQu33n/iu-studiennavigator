# tests/unit/test_student.py
"""
Unit Tests fuer Student Domain Model (models/student.py)

Testet die Student-Klasse:
- Initialisierung und Validierung
- get_full_name() Methode
- calculate_semester() mit Einschreibung
- validate() Validierungslogik
- Serialisierung (to_dict)
- Factory Method (from_db_row)
- String-Repraesentation

OOP-Konzepte:
- KOMPOSITION zu Login (login_id)
- AGGREGATION zu Einschreibung
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock

# Mark this whole module as unit tests
pytestmark = pytest.mark.unit


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def student_class():
    """Importiert Student-Klasse"""
    try:
        from models.student import Student
        return Student
    except ImportError:
        from models import Student
        return Student


@pytest.fixture
def sample_student(student_class):
    """Standard-Student fuer Tests"""
    return student_class(
        id=1,
        matrikel_nr="IU12345678",
        vorname="Max",
        nachname="Mustermann",
        login_id=100
    )


@pytest.fixture
def student_ohne_login(student_class):
    """Student ohne Login fuer Tests"""
    return student_class(
        id=2,
        matrikel_nr="IU87654321",
        vorname="Erika",
        nachname="Musterfrau",
        login_id=None
    )


@pytest.fixture
def mock_einschreibung():
    """Mock-Einschreibung fuer calculate_semester() Tests"""
    mock = MagicMock()
    return mock


# ============================================================================
# INITIALIZATION TESTS
# ============================================================================

class TestStudentInit:
    """Tests fuer Student-Initialisierung"""

    def test_init_with_all_fields(self, student_class):
        """Initialisierung mit allen Feldern"""
        student = student_class(
            id=1,
            matrikel_nr="IU12345678",
            vorname="Max",
            nachname="Mustermann",
            login_id=100
        )

        assert student.id == 1
        assert student.matrikel_nr == "IU12345678"
        assert student.vorname == "Max"
        assert student.nachname == "Mustermann"
        assert student.login_id == 100

    def test_init_without_login_id(self, student_class):
        """Initialisierung ohne login_id (Default: None)"""
        student = student_class(
            id=1,
            matrikel_nr="IU12345678",
            vorname="Max",
            nachname="Mustermann"
        )

        assert student.login_id is None

    def test_init_with_none_login_id(self, student_class):
        """Initialisierung mit explizitem None fuer login_id"""
        student = student_class(
            id=1,
            matrikel_nr="IU12345678",
            vorname="Max",
            nachname="Mustermann",
            login_id=None
        )

        assert student.login_id is None

    def test_init_various_matrikel_formats(self, student_class):
        """Verschiedene Matrikelnummer-Formate"""
        formats = [
            "IU12345678",
            "IU98765432",
            "12345678",
            "ABCDE12345"
        ]

        for matrikel in formats:
            student = student_class(
                id=1,
                matrikel_nr=matrikel,
                vorname="Test",
                nachname="Student"
            )
            assert student.matrikel_nr == matrikel


# ============================================================================
# GET_FULL_NAME TESTS
# ============================================================================

class TestGetFullName:
    """Tests fuer get_full_name() Methode"""

    def test_get_full_name_standard(self, sample_student):
        """get_full_name() gibt vollstaendigen Namen zurueck"""
        assert sample_student.get_full_name() == "Max Mustermann"

    def test_get_full_name_single_names(self, student_class):
        """get_full_name() mit einfachen Namen"""
        student = student_class(
            id=1,
            matrikel_nr="IU12345",
            vorname="Anna",
            nachname="Schmidt"
        )

        assert student.get_full_name() == "Anna Schmidt"

    def test_get_full_name_with_umlauts(self, student_class):
        """get_full_name() mit Umlauten"""
        student = student_class(
            id=1,
            matrikel_nr="IU12345",
            vorname="Juergen",
            nachname="Mueller"
        )

        assert student.get_full_name() == "Juergen Mueller"

    def test_get_full_name_compound_names(self, student_class):
        """get_full_name() mit zusammengesetzten Namen"""
        student = student_class(
            id=1,
            matrikel_nr="IU12345",
            vorname="Anna-Maria",
            nachname="von der Heide"
        )

        assert student.get_full_name() == "Anna-Maria von der Heide"


# ============================================================================
# CALCULATE_SEMESTER TESTS
# ============================================================================

class TestCalculateSemester:
    """Tests fuer calculate_semester() Methode"""

    def test_calculate_semester_first(self, sample_student, mock_einschreibung):
        """Erstes Semester (0-5 Monate)"""
        mock_einschreibung.get_study_duration_months.return_value = 0
        assert sample_student.calculate_semester(mock_einschreibung) == 1

        mock_einschreibung.get_study_duration_months.return_value = 5
        assert sample_student.calculate_semester(mock_einschreibung) == 1

    def test_calculate_semester_second(self, sample_student, mock_einschreibung):
        """Zweites Semester (6-11 Monate)"""
        mock_einschreibung.get_study_duration_months.return_value = 6
        assert sample_student.calculate_semester(mock_einschreibung) == 2

        mock_einschreibung.get_study_duration_months.return_value = 11
        assert sample_student.calculate_semester(mock_einschreibung) == 2

    def test_calculate_semester_third(self, sample_student, mock_einschreibung):
        """Drittes Semester (12-17 Monate)"""
        mock_einschreibung.get_study_duration_months.return_value = 12
        assert sample_student.calculate_semester(mock_einschreibung) == 3

        mock_einschreibung.get_study_duration_months.return_value = 17
        assert sample_student.calculate_semester(mock_einschreibung) == 3

    def test_calculate_semester_sixth(self, sample_student, mock_einschreibung):
        """Sechstes Semester (30-35 Monate)"""
        mock_einschreibung.get_study_duration_months.return_value = 30
        assert sample_student.calculate_semester(mock_einschreibung) == 6

        mock_einschreibung.get_study_duration_months.return_value = 35
        assert sample_student.calculate_semester(mock_einschreibung) == 6

    def test_calculate_semester_seventh(self, sample_student, mock_einschreibung):
        """Siebtes Semester (36+ Monate)"""
        mock_einschreibung.get_study_duration_months.return_value = 36
        assert sample_student.calculate_semester(mock_einschreibung) == 7

    def test_calculate_semester_boundary(self, sample_student, mock_einschreibung):
        """Grenzwerte zwischen Semestern"""
        # Genau 6 Monate = 2. Semester
        mock_einschreibung.get_study_duration_months.return_value = 6
        assert sample_student.calculate_semester(mock_einschreibung) == 2

        # Genau 12 Monate = 3. Semester
        mock_einschreibung.get_study_duration_months.return_value = 12
        assert sample_student.calculate_semester(mock_einschreibung) == 3


# ============================================================================
# VALIDATE TESTS
# ============================================================================

class TestValidate:
    """Tests fuer validate() Methode"""

    def test_validate_valid_student(self, sample_student):
        """Gueltiger Student validiert erfolgreich"""
        is_valid, error = sample_student.validate()

        assert is_valid is True
        assert error == ""

    def test_validate_empty_matrikel(self, student_class):
        """Leere Matrikelnummer ist ungueltig"""
        student = student_class(
            id=1,
            matrikel_nr="",
            vorname="Max",
            nachname="Mustermann"
        )

        is_valid, error = student.validate()

        assert is_valid is False
        assert "Matrikelnummer" in error

    def test_validate_short_matrikel(self, student_class):
        """Zu kurze Matrikelnummer ist ungueltig"""
        student = student_class(
            id=1,
            matrikel_nr="IU12",  # Nur 4 Zeichen
            vorname="Max",
            nachname="Mustermann"
        )

        is_valid, error = student.validate()

        assert is_valid is False
        assert "5 Zeichen" in error

    def test_validate_matrikel_exactly_5_chars(self, student_class):
        """Matrikelnummer mit genau 5 Zeichen ist gueltig"""
        student = student_class(
            id=1,
            matrikel_nr="IU123",  # Genau 5 Zeichen
            vorname="Max",
            nachname="Mustermann"
        )

        is_valid, error = student.validate()

        assert is_valid is True
        assert error == ""

    def test_validate_empty_vorname(self, student_class):
        """Leerer Vorname ist ungueltig"""
        student = student_class(
            id=1,
            matrikel_nr="IU12345678",
            vorname="",
            nachname="Mustermann"
        )

        is_valid, error = student.validate()

        assert is_valid is False
        assert "Vor- und Nachname" in error

    def test_validate_empty_nachname(self, student_class):
        """Leerer Nachname ist ungueltig"""
        student = student_class(
            id=1,
            matrikel_nr="IU12345678",
            vorname="Max",
            nachname=""
        )

        is_valid, error = student.validate()

        assert is_valid is False
        assert "Vor- und Nachname" in error

    def test_validate_both_names_empty(self, student_class):
        """Beide Namen leer ist ungueltig"""
        student = student_class(
            id=1,
            matrikel_nr="IU12345678",
            vorname="",
            nachname=""
        )

        is_valid, error = student.validate()

        assert is_valid is False

    def test_validate_returns_tuple(self, sample_student):
        """validate() gibt Tuple zurueck"""
        result = sample_student.validate()

        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], bool)
        assert isinstance(result[1], str)


# ============================================================================
# TO_DICT TESTS
# ============================================================================

class TestToDict:
    """Tests fuer to_dict() Methode"""

    def test_to_dict_contains_all_fields(self, sample_student):
        """to_dict() enthaelt alle Felder"""
        d = sample_student.to_dict()

        assert 'id' in d
        assert 'matrikel_nr' in d
        assert 'vorname' in d
        assert 'nachname' in d
        assert 'full_name' in d
        assert 'login_id' in d

    def test_to_dict_correct_values(self, sample_student):
        """to_dict() enthaelt korrekte Werte"""
        d = sample_student.to_dict()

        assert d['id'] == 1
        assert d['matrikel_nr'] == "IU12345678"
        assert d['vorname'] == "Max"
        assert d['nachname'] == "Mustermann"
        assert d['full_name'] == "Max Mustermann"
        assert d['login_id'] == 100

    def test_to_dict_full_name_computed(self, sample_student):
        """full_name wird korrekt berechnet"""
        d = sample_student.to_dict()

        assert d['full_name'] == sample_student.get_full_name()

    def test_to_dict_login_id_none(self, student_ohne_login):
        """login_id None bleibt None"""
        d = student_ohne_login.to_dict()

        assert d['login_id'] is None

    def test_to_dict_is_json_serializable(self, sample_student):
        """to_dict() Ergebnis ist JSON-serialisierbar"""
        import json

        d = sample_student.to_dict()

        # Sollte nicht werfen
        json_str = json.dumps(d)
        assert isinstance(json_str, str)

    def test_to_dict_returns_new_dict(self, sample_student):
        """to_dict() gibt neues Dictionary zurueck"""
        d1 = sample_student.to_dict()
        d2 = sample_student.to_dict()

        assert d1 == d2
        assert d1 is not d2


# ============================================================================
# FROM_DB_ROW TESTS
# ============================================================================

class TestFromDbRow:
    """Tests fuer from_db_row() Factory Method"""

    def test_from_db_row_dict(self, student_class):
        """from_db_row() funktioniert mit dict"""
        row = {
            'id': 1,
            'matrikel_nr': 'IU12345678',
            'vorname': 'Max',
            'nachname': 'Mustermann',
            'login_id': 100
        }

        student = student_class.from_db_row(row)

        assert student.id == 1
        assert student.matrikel_nr == 'IU12345678'
        assert student.vorname == 'Max'
        assert student.nachname == 'Mustermann'
        assert student.login_id == 100

    def test_from_db_row_without_login_id(self, student_class):
        """from_db_row() behandelt fehlende login_id"""
        row = {
            'id': 1,
            'matrikel_nr': 'IU12345678',
            'vorname': 'Max',
            'nachname': 'Mustermann'
        }

        mock_row = MagicMock()

        def getitem(key):
            if key in row:
                return row[key]
            raise KeyError(key)

        mock_row.__getitem__ = lambda self, key: getitem(key)

        student = student_class.from_db_row(mock_row)

        assert student.login_id is None

    def test_from_db_row_with_none_login_id(self, student_class):
        """from_db_row() behandelt None login_id"""
        row = {
            'id': 1,
            'matrikel_nr': 'IU12345678',
            'vorname': 'Max',
            'nachname': 'Mustermann',
            'login_id': None
        }

        student = student_class.from_db_row(row)

        assert student.login_id is None

    def test_from_db_row_sqlite_row_mock(self, student_class):
        """from_db_row() funktioniert mit sqlite3.Row-aehnlichem Objekt"""
        data = {
            'id': 2,
            'matrikel_nr': 'IU87654321',
            'vorname': 'Erika',
            'nachname': 'Musterfrau',
            'login_id': 200
        }

        mock_row = MagicMock()
        mock_row.__getitem__ = lambda self, key: data[key]

        student = student_class.from_db_row(mock_row)

        assert student.id == 2
        assert student.matrikel_nr == 'IU87654321'
        assert student.vorname == 'Erika'
        assert student.nachname == 'Musterfrau'
        assert student.login_id == 200

    def test_from_db_row_string_ids(self, student_class):
        """from_db_row() konvertiert String-IDs zu int"""
        row = {
            'id': '123',
            'matrikel_nr': 'IU12345678',
            'vorname': 'Max',
            'nachname': 'Mustermann',
            'login_id': '456'
        }

        student = student_class.from_db_row(row)

        assert student.id == 123
        assert isinstance(student.id, int)
        assert student.login_id == 456
        assert isinstance(student.login_id, int)


# ============================================================================
# STRING REPRESENTATION TESTS
# ============================================================================

class TestStringRepresentation:
    """Tests fuer __str__ und __repr__"""

    def test_str_contains_matrikel(self, sample_student):
        """__str__ enthaelt Matrikelnummer"""
        s = str(sample_student)
        assert "IU12345678" in s

    def test_str_contains_full_name(self, sample_student):
        """__str__ enthaelt vollstaendigen Namen"""
        s = str(sample_student)
        assert "Max Mustermann" in s

    def test_str_format(self, sample_student):
        """__str__ hat korrektes Format"""
        s = str(sample_student)
        assert s == "Student(IU12345678, Max Mustermann)"

    def test_repr_contains_class_name(self, sample_student):
        """__repr__ enthaelt Klassennamen"""
        r = repr(sample_student)
        assert "Student" in r

    def test_repr_contains_id(self, sample_student):
        """__repr__ enthaelt ID"""
        r = repr(sample_student)
        assert "id=1" in r

    def test_repr_contains_matrikel(self, sample_student):
        """__repr__ enthaelt Matrikelnummer"""
        r = repr(sample_student)
        assert "matrikel_nr='IU12345678'" in r

    def test_repr_contains_name(self, sample_student):
        """__repr__ enthaelt Namen"""
        r = repr(sample_student)
        assert "name='Max Mustermann'" in r


# ============================================================================
# COMPOSITION RELATIONSHIP TESTS
# ============================================================================

class TestCompositionRelationship:
    """Tests fuer KOMPOSITION zu Login"""

    def test_login_id_is_part_of_student(self, sample_student):
        """login_id ist Teil des Student"""
        assert hasattr(sample_student, 'login_id')
        assert sample_student.login_id == 100

    def test_student_can_exist_without_login(self, student_ohne_login):
        """Student kann ohne Login existieren (vor Login-Erstellung)"""
        assert student_ohne_login.login_id is None
        # Student ist trotzdem gueltig
        is_valid, _ = student_ohne_login.validate()
        assert is_valid is True

    def test_login_id_in_to_dict(self, sample_student):
        """login_id erscheint in to_dict()"""
        d = sample_student.to_dict()
        assert 'login_id' in d
        assert d['login_id'] == 100


# ============================================================================
# DATACLASS TESTS
# ============================================================================

class TestDataclass:
    """Tests fuer Dataclass-Eigenschaften"""

    def test_equality_same_values(self, student_class):
        """Gleiche Werte bedeuten Gleichheit"""
        s1 = student_class(
            id=1,
            matrikel_nr="IU12345678",
            vorname="Max",
            nachname="Mustermann",
            login_id=100
        )
        s2 = student_class(
            id=1,
            matrikel_nr="IU12345678",
            vorname="Max",
            nachname="Mustermann",
            login_id=100
        )

        assert s1 == s2

    def test_inequality_different_id(self, student_class):
        """Unterschiedliche IDs bedeuten Ungleichheit"""
        s1 = student_class(
            id=1,
            matrikel_nr="IU12345678",
            vorname="Max",
            nachname="Mustermann"
        )
        s2 = student_class(
            id=2,
            matrikel_nr="IU12345678",
            vorname="Max",
            nachname="Mustermann"
        )

        assert s1 != s2

    def test_inequality_different_matrikel(self, student_class):
        """Unterschiedliche Matrikelnummern bedeuten Ungleichheit"""
        s1 = student_class(
            id=1,
            matrikel_nr="IU12345678",
            vorname="Max",
            nachname="Mustermann"
        )
        s2 = student_class(
            id=1,
            matrikel_nr="IU87654321",
            vorname="Max",
            nachname="Mustermann"
        )

        assert s1 != s2


# ============================================================================
# EDGE CASES
# ============================================================================

class TestEdgeCases:
    """Tests fuer Randfaelle"""

    def test_very_long_matrikel(self, student_class):
        """Sehr lange Matrikelnummer"""
        long_matrikel = "IU" + "1" * 100
        student = student_class(
            id=1,
            matrikel_nr=long_matrikel,
            vorname="Max",
            nachname="Mustermann"
        )

        assert student.matrikel_nr == long_matrikel
        is_valid, _ = student.validate()
        assert is_valid is True

    def test_very_long_names(self, student_class):
        """Sehr lange Namen"""
        long_name = "A" * 200
        student = student_class(
            id=1,
            matrikel_nr="IU12345",
            vorname=long_name,
            nachname=long_name
        )

        assert student.vorname == long_name
        assert student.nachname == long_name
        assert student.get_full_name() == f"{long_name} {long_name}"

    def test_special_characters_in_names(self, student_class):
        """Sonderzeichen in Namen"""
        student = student_class(
            id=1,
            matrikel_nr="IU12345",
            vorname="Jean-Pierre",
            nachname="O'Connor-Smith"
        )

        assert student.get_full_name() == "Jean-Pierre O'Connor-Smith"

    def test_whitespace_in_names(self, student_class):
        """Whitespace in Namen wird beibehalten"""
        student = student_class(
            id=1,
            matrikel_nr="IU12345",
            vorname="  Max  ",
            nachname="  Mustermann  "
        )

        # Whitespace wird beibehalten
        assert student.get_full_name() == "  Max     Mustermann  "

    def test_large_id(self, student_class):
        """Grosse ID"""
        student = student_class(
            id=999999999,
            matrikel_nr="IU12345",
            vorname="Max",
            nachname="Mustermann"
        )

        assert student.id == 999999999

    def test_large_login_id(self, student_class):
        """Grosse Login-ID"""
        student = student_class(
            id=1,
            matrikel_nr="IU12345",
            vorname="Max",
            nachname="Mustermann",
            login_id=999999999
        )

        assert student.login_id == 999999999


# ============================================================================
# TYPE CHECKING TESTS
# ============================================================================

class TestTypeChecking:
    """Tests fuer Typenpruefung"""

    def test_id_is_int(self, sample_student):
        """id ist int"""
        assert isinstance(sample_student.id, int)

    def test_matrikel_nr_is_str(self, sample_student):
        """matrikel_nr ist str"""
        assert isinstance(sample_student.matrikel_nr, str)

    def test_vorname_is_str(self, sample_student):
        """vorname ist str"""
        assert isinstance(sample_student.vorname, str)

    def test_nachname_is_str(self, sample_student):
        """nachname ist str"""
        assert isinstance(sample_student.nachname, str)

    def test_login_id_is_int_or_none(self, sample_student, student_ohne_login):
        """login_id ist int oder None"""
        assert isinstance(sample_student.login_id, int)
        assert student_ohne_login.login_id is None

    def test_get_full_name_returns_str(self, sample_student):
        """get_full_name() gibt str zurueck"""
        assert isinstance(sample_student.get_full_name(), str)

    def test_validate_returns_tuple(self, sample_student):
        """validate() gibt tuple zurueck"""
        result = sample_student.validate()
        assert isinstance(result, tuple)

    def test_to_dict_returns_dict(self, sample_student):
        """to_dict() gibt dict zurueck"""
        assert isinstance(sample_student.to_dict(), dict)

    def test_calculate_semester_returns_int(self, sample_student, mock_einschreibung):
        """calculate_semester() gibt int zurueck"""
        mock_einschreibung.get_study_duration_months.return_value = 12
        result = sample_student.calculate_semester(mock_einschreibung)
        assert isinstance(result, int)