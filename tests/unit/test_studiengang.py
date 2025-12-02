# tests/unit/test_studiengang.py
"""
Unit Tests fuer Studiengang Domain Model (models/studiengang.py)

Testet die Studiengang-Klasse:
- Initialisierung und Validierung
- get_full_name() Methode
- is_bachelor() und is_master() Methoden
- get_total_ects_target() Berechnung
- validate() mit ValueError bei ungueltigen Daten
- Serialisierung (to_dict)
- Factory Method (from_row)
- String-Repraesentation

OOP-Konzepte:
- ASSOZIATION von Einschreibung
- KOMPOSITION zu StudiengangModul
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
def studiengang_class():
    """Importiert Studiengang-Klasse"""
    try:
        from models.studiengang import Studiengang
        return Studiengang
    except ImportError:
        from models import Studiengang
        return Studiengang


@pytest.fixture
def bachelor_informatik(studiengang_class):
    """Bachelor Informatik fuer Tests"""
    return studiengang_class(
        id=1,
        name="Informatik",
        grad="B.Sc.",
        regel_semester=6,
        beschreibung="Bachelor of Science in Informatik"
    )


@pytest.fixture
def master_informatik(studiengang_class):
    """Master Informatik fuer Tests"""
    return studiengang_class(
        id=2,
        name="Informatik",
        grad="M.Sc.",
        regel_semester=4,
        beschreibung="Master of Science in Informatik"
    )


@pytest.fixture
def bachelor_bwl(studiengang_class):
    """Bachelor BWL fuer Tests"""
    return studiengang_class(
        id=3,
        name="Betriebswirtschaftslehre",
        grad="B.A.",
        regel_semester=7,
        beschreibung=None
    )


# ============================================================================
# INITIALIZATION TESTS
# ============================================================================

class TestStudiengangInit:
    """Tests fuer Studiengang-Initialisierung"""

    def test_init_with_all_fields(self, studiengang_class):
        """Initialisierung mit allen Feldern"""
        sg = studiengang_class(
            id=1,
            name="Informatik",
            grad="B.Sc.",
            regel_semester=6,
            beschreibung="Beschreibung"
        )

        assert sg.id == 1
        assert sg.name == "Informatik"
        assert sg.grad == "B.Sc."
        assert sg.regel_semester == 6
        assert sg.beschreibung == "Beschreibung"

    def test_init_without_beschreibung(self, studiengang_class):
        """Initialisierung ohne beschreibung (Default: None)"""
        sg = studiengang_class(
            id=1,
            name="Informatik",
            grad="B.Sc.",
            regel_semester=6
        )

        assert sg.beschreibung is None

    def test_init_with_none_beschreibung(self, studiengang_class):
        """Initialisierung mit explizitem None fuer beschreibung"""
        sg = studiengang_class(
            id=1,
            name="Informatik",
            grad="B.Sc.",
            regel_semester=6,
            beschreibung=None
        )

        assert sg.beschreibung is None

    def test_init_calls_validate(self, studiengang_class):
        """__post_init__ ruft validate() auf"""
        # Ungueltige Daten sollten ValueError werfen
        with pytest.raises(ValueError):
            studiengang_class(
                id=1,
                name="",  # Ungueltig
                grad="B.Sc.",
                regel_semester=6
            )

    def test_init_all_bachelor_grades(self, studiengang_class):
        """Initialisierung mit allen Bachelor-Graden"""
        bachelor_grades = ["B.Sc.", "B.A.", "B.Eng."]

        for grad in bachelor_grades:
            sg = studiengang_class(
                id=1,
                name="Test",
                grad=grad,
                regel_semester=6
            )
            assert sg.grad == grad

    def test_init_all_master_grades(self, studiengang_class):
        """Initialisierung mit allen Master-Graden"""
        master_grades = ["M.Sc.", "M.A.", "M.Eng."]

        for grad in master_grades:
            sg = studiengang_class(
                id=1,
                name="Test",
                grad=grad,
                regel_semester=4
            )
            assert sg.grad == grad


# ============================================================================
# VALIDATION TESTS
# ============================================================================

class TestValidate:
    """Tests fuer validate() Methode"""

    def test_validate_valid_data(self, bachelor_informatik):
        """Gueltige Daten validieren erfolgreich"""
        # Sollte keine Exception werfen
        bachelor_informatik.validate()

    def test_validate_empty_name(self, studiengang_class):
        """Leerer Name ist ungueltig"""
        with pytest.raises(ValueError) as exc_info:
            studiengang_class(
                id=1,
                name="",
                grad="B.Sc.",
                regel_semester=6
            )

        assert "name" in str(exc_info.value).lower() or "leer" in str(exc_info.value).lower()

    def test_validate_whitespace_name(self, studiengang_class):
        """Nur Whitespace als Name ist ungueltig"""
        with pytest.raises(ValueError) as exc_info:
            studiengang_class(
                id=1,
                name="   ",
                grad="B.Sc.",
                regel_semester=6
            )

        assert "name" in str(exc_info.value).lower() or "leer" in str(exc_info.value).lower()

    def test_validate_invalid_grad(self, studiengang_class):
        """Ungueltiger Grad wirft ValueError"""
        with pytest.raises(ValueError) as exc_info:
            studiengang_class(
                id=1,
                name="Informatik",
                grad="Ph.D.",  # Ungueltig
                regel_semester=6
            )

        assert "Grad" in str(exc_info.value)
        assert "Ph.D." in str(exc_info.value)

    def test_validate_grad_case_sensitive(self, studiengang_class):
        """Grad ist case-sensitive"""
        with pytest.raises(ValueError):
            studiengang_class(
                id=1,
                name="Informatik",
                grad="b.sc.",  # Kleingeschrieben
                regel_semester=6
            )

    def test_validate_regel_semester_zero(self, studiengang_class):
        """Regelsemester 0 ist ungueltig"""
        with pytest.raises(ValueError) as exc_info:
            studiengang_class(
                id=1,
                name="Informatik",
                grad="B.Sc.",
                regel_semester=0
            )

        assert "Regelsemester" in str(exc_info.value)

    def test_validate_regel_semester_negative(self, studiengang_class):
        """Negatives Regelsemester ist ungueltig"""
        with pytest.raises(ValueError) as exc_info:
            studiengang_class(
                id=1,
                name="Informatik",
                grad="B.Sc.",
                regel_semester=-1
            )

        assert "Regelsemester" in str(exc_info.value)

    def test_validate_regel_semester_too_high(self, studiengang_class):
        """Regelsemester > 14 ist ungueltig"""
        with pytest.raises(ValueError) as exc_info:
            studiengang_class(
                id=1,
                name="Informatik",
                grad="B.Sc.",
                regel_semester=15
            )

        assert "Regelsemester" in str(exc_info.value)
        assert "1 und 14" in str(exc_info.value)

    def test_validate_regel_semester_boundary_1(self, studiengang_class):
        """Regelsemester 1 ist gueltig (untere Grenze)"""
        sg = studiengang_class(
            id=1,
            name="Kurzstudium",
            grad="B.Sc.",
            regel_semester=1
        )

        assert sg.regel_semester == 1

    def test_validate_regel_semester_boundary_14(self, studiengang_class):
        """Regelsemester 14 ist gueltig (obere Grenze)"""
        sg = studiengang_class(
            id=1,
            name="Langstudium",
            grad="M.Sc.",
            regel_semester=14
        )

        assert sg.regel_semester == 14


# ============================================================================
# GET_FULL_NAME TESTS
# ============================================================================

class TestGetFullName:
    """Tests fuer get_full_name() Methode"""

    def test_get_full_name_bachelor(self, bachelor_informatik):
        """get_full_name() fuer Bachelor"""
        assert bachelor_informatik.get_full_name() == "Informatik (B.Sc.)"

    def test_get_full_name_master(self, master_informatik):
        """get_full_name() fuer Master"""
        assert master_informatik.get_full_name() == "Informatik (M.Sc.)"

    def test_get_full_name_ba(self, bachelor_bwl):
        """get_full_name() fuer B.A."""
        assert bachelor_bwl.get_full_name() == "Betriebswirtschaftslehre (B.A.)"

    def test_get_full_name_format(self, studiengang_class):
        """get_full_name() hat korrektes Format"""
        sg = studiengang_class(
            id=1,
            name="Test Studiengang",
            grad="B.Eng.",
            regel_semester=6
        )

        full_name = sg.get_full_name()
        assert "Test Studiengang" in full_name
        assert "(B.Eng.)" in full_name


# ============================================================================
# IS_BACHELOR TESTS
# ============================================================================

class TestIsBachelor:
    """Tests fuer is_bachelor() Methode"""

    def test_is_bachelor_true_bsc(self, bachelor_informatik):
        """is_bachelor() ist True fuer B.Sc."""
        assert bachelor_informatik.grad == "B.Sc."
        assert bachelor_informatik.is_bachelor() is True

    def test_is_bachelor_true_ba(self, bachelor_bwl):
        """is_bachelor() ist True fuer B.A."""
        assert bachelor_bwl.grad == "B.A."
        assert bachelor_bwl.is_bachelor() is True

    def test_is_bachelor_true_beng(self, studiengang_class):
        """is_bachelor() ist True fuer B.Eng."""
        sg = studiengang_class(
            id=1,
            name="Maschinenbau",
            grad="B.Eng.",
            regel_semester=7
        )

        assert sg.is_bachelor() is True

    def test_is_bachelor_false_master(self, master_informatik):
        """is_bachelor() ist False fuer Master"""
        assert master_informatik.grad == "M.Sc."
        assert master_informatik.is_bachelor() is False


# ============================================================================
# IS_MASTER TESTS
# ============================================================================

class TestIsMaster:
    """Tests fuer is_master() Methode"""

    def test_is_master_true_msc(self, master_informatik):
        """is_master() ist True fuer M.Sc."""
        assert master_informatik.grad == "M.Sc."
        assert master_informatik.is_master() is True

    def test_is_master_true_ma(self, studiengang_class):
        """is_master() ist True fuer M.A."""
        sg = studiengang_class(
            id=1,
            name="Kulturmanagement",
            grad="M.A.",
            regel_semester=4
        )

        assert sg.is_master() is True

    def test_is_master_true_meng(self, studiengang_class):
        """is_master() ist True fuer M.Eng."""
        sg = studiengang_class(
            id=1,
            name="Maschinenbau",
            grad="M.Eng.",
            regel_semester=4
        )

        assert sg.is_master() is True

    def test_is_master_false_bachelor(self, bachelor_informatik):
        """is_master() ist False fuer Bachelor"""
        assert bachelor_informatik.grad == "B.Sc."
        assert bachelor_informatik.is_master() is False


# ============================================================================
# GET_TOTAL_ECTS_TARGET TESTS
# ============================================================================

class TestGetTotalEctsTarget:
    """Tests fuer get_total_ects_target() Methode"""

    def test_ects_6_semester(self, bachelor_informatik):
        """ECTS-Ziel fuer 6 Semester = 180"""
        assert bachelor_informatik.regel_semester == 6
        assert bachelor_informatik.get_total_ects_target() == 180

    def test_ects_7_semester(self, bachelor_bwl):
        """ECTS-Ziel fuer 7 Semester = 210"""
        assert bachelor_bwl.regel_semester == 7
        assert bachelor_bwl.get_total_ects_target() == 210

    def test_ects_4_semester(self, master_informatik):
        """ECTS-Ziel fuer 4 Semester = 120"""
        assert master_informatik.regel_semester == 4
        assert master_informatik.get_total_ects_target() == 120

    def test_ects_calculation_formula(self, studiengang_class):
        """ECTS-Berechnung: 30 ECTS pro Semester"""
        for semester in [1, 2, 3, 4, 5, 6, 7, 8]:
            sg = studiengang_class(
                id=1,
                name="Test",
                grad="B.Sc.",
                regel_semester=semester
            )
            expected_ects = semester * 30
            assert sg.get_total_ects_target() == expected_ects


# ============================================================================
# TO_DICT TESTS
# ============================================================================

class TestToDict:
    """Tests fuer to_dict() Methode"""

    def test_to_dict_contains_all_fields(self, bachelor_informatik):
        """to_dict() enthaelt alle Felder"""
        d = bachelor_informatik.to_dict()

        assert 'id' in d
        assert 'name' in d
        assert 'grad' in d
        assert 'regel_semester' in d
        assert 'beschreibung' in d

    def test_to_dict_contains_computed_fields(self, bachelor_informatik):
        """to_dict() enthaelt berechnete Felder"""
        d = bachelor_informatik.to_dict()

        assert 'full_name' in d
        assert 'is_bachelor' in d
        assert 'is_master' in d
        assert 'total_ects_target' in d

    def test_to_dict_correct_values(self, bachelor_informatik):
        """to_dict() enthaelt korrekte Werte"""
        d = bachelor_informatik.to_dict()

        assert d['id'] == 1
        assert d['name'] == "Informatik"
        assert d['grad'] == "B.Sc."
        assert d['regel_semester'] == 6
        assert d['beschreibung'] == "Bachelor of Science in Informatik"

    def test_to_dict_computed_values_bachelor(self, bachelor_informatik):
        """Berechnete Werte fuer Bachelor"""
        d = bachelor_informatik.to_dict()

        assert d['full_name'] == "Informatik (B.Sc.)"
        assert d['is_bachelor'] is True
        assert d['is_master'] is False
        assert d['total_ects_target'] == 180

    def test_to_dict_computed_values_master(self, master_informatik):
        """Berechnete Werte fuer Master"""
        d = master_informatik.to_dict()

        assert d['full_name'] == "Informatik (M.Sc.)"
        assert d['is_bachelor'] is False
        assert d['is_master'] is True
        assert d['total_ects_target'] == 120

    def test_to_dict_beschreibung_none(self, bachelor_bwl):
        """beschreibung None bleibt None"""
        d = bachelor_bwl.to_dict()

        assert d['beschreibung'] is None

    def test_to_dict_is_json_serializable(self, bachelor_informatik):
        """to_dict() Ergebnis ist JSON-serialisierbar"""
        import json

        d = bachelor_informatik.to_dict()

        # Sollte nicht werfen
        json_str = json.dumps(d)
        assert isinstance(json_str, str)

    def test_to_dict_returns_new_dict(self, bachelor_informatik):
        """to_dict() gibt neues Dictionary zurueck"""
        d1 = bachelor_informatik.to_dict()
        d2 = bachelor_informatik.to_dict()

        assert d1 == d2
        assert d1 is not d2


# ============================================================================
# FROM_ROW TESTS
# ============================================================================

class TestFromRow:
    """Tests fuer from_row() Factory Method"""

    def test_from_row_dict(self, studiengang_class):
        """from_row() funktioniert mit dict"""
        row = {
            'id': 1,
            'name': 'Informatik',
            'grad': 'B.Sc.',
            'regel_semester': 6,
            'beschreibung': 'Test Beschreibung'
        }

        sg = studiengang_class.from_row(row)

        assert sg.id == 1
        assert sg.name == 'Informatik'
        assert sg.grad == 'B.Sc.'
        assert sg.regel_semester == 6
        assert sg.beschreibung == 'Test Beschreibung'

    def test_from_row_sqlite_row_mock(self, studiengang_class):
        """from_row() funktioniert mit sqlite3.Row-aehnlichem Objekt"""
        data = {
            'id': 2,
            'name': 'BWL',
            'grad': 'B.A.',
            'regel_semester': 7,
            'beschreibung': None
        }

        mock_row = MagicMock()
        mock_row.__getitem__ = lambda self, key: data[key]
        mock_row.keys = lambda: data.keys()

        sg = studiengang_class.from_row(mock_row)

        assert sg.id == 2
        assert sg.name == 'BWL'
        assert sg.grad == 'B.A.'
        assert sg.regel_semester == 7

    def test_from_row_string_ids(self, studiengang_class):
        """from_row() konvertiert String-IDs zu int"""
        row = {
            'id': '123',
            'name': 'Informatik',
            'grad': 'B.Sc.',
            'regel_semester': '6',
            'beschreibung': None
        }

        mock_row = MagicMock()
        mock_row.__getitem__ = lambda self, key: row[key]
        mock_row.keys = lambda: row.keys()

        sg = studiengang_class.from_row(mock_row)

        assert sg.id == 123
        assert isinstance(sg.id, int)
        assert sg.regel_semester == 6
        assert isinstance(sg.regel_semester, int)

    def test_from_row_validates(self, studiengang_class):
        """from_row() fuehrt Validierung durch"""
        row = {
            'id': '1',
            'name': '',  # Ungueltig
            'grad': 'B.Sc.',
            'regel_semester': '6',
            'beschreibung': None
        }

        mock_row = MagicMock()
        mock_row.__getitem__ = lambda self, key: row[key]
        mock_row.keys = lambda: row.keys()

        with pytest.raises(ValueError):
            studiengang_class.from_row(mock_row)

    def test_from_row_without_beschreibung_key(self, studiengang_class):
        """from_row() behandelt fehlenden beschreibung-Key"""
        data = {
            'id': 1,
            'name': 'Informatik',
            'grad': 'B.Sc.',
            'regel_semester': 6
        }

        mock_row = MagicMock()
        mock_row.__getitem__ = lambda self, key: data[key]
        mock_row.keys = lambda: data.keys()

        sg = studiengang_class.from_row(mock_row)

        assert sg.beschreibung is None


# ============================================================================
# STRING REPRESENTATION TESTS
# ============================================================================

class TestStringRepresentation:
    """Tests fuer __str__ und __repr__"""

    def test_str_contains_full_name(self, bachelor_informatik):
        """__str__ enthaelt vollstaendigen Namen"""
        s = str(bachelor_informatik)
        assert "Informatik (B.Sc.)" in s

    def test_str_contains_semester(self, bachelor_informatik):
        """__str__ enthaelt Semesteranzahl"""
        s = str(bachelor_informatik)
        assert "6 Semester" in s

    def test_str_format(self, bachelor_informatik):
        """__str__ hat korrektes Format"""
        s = str(bachelor_informatik)
        assert s == "Studiengang(Informatik (B.Sc.), 6 Semester)"

    def test_repr_contains_class_name(self, bachelor_informatik):
        """__repr__ enthaelt Klassennamen"""
        r = repr(bachelor_informatik)
        assert "Studiengang" in r

    def test_repr_contains_id(self, bachelor_informatik):
        """__repr__ enthaelt ID"""
        r = repr(bachelor_informatik)
        assert "id=1" in r

    def test_repr_contains_name(self, bachelor_informatik):
        """__repr__ enthaelt Namen"""
        r = repr(bachelor_informatik)
        assert "name='Informatik'" in r

    def test_repr_contains_grad(self, bachelor_informatik):
        """__repr__ enthaelt Grad"""
        r = repr(bachelor_informatik)
        assert "grad='B.Sc.'" in r


# ============================================================================
# DATACLASS TESTS
# ============================================================================

class TestDataclass:
    """Tests fuer Dataclass-Eigenschaften"""

    def test_equality_same_values(self, studiengang_class):
        """Gleiche Werte bedeuten Gleichheit"""
        sg1 = studiengang_class(
            id=1,
            name="Informatik",
            grad="B.Sc.",
            regel_semester=6,
            beschreibung="Test"
        )
        sg2 = studiengang_class(
            id=1,
            name="Informatik",
            grad="B.Sc.",
            regel_semester=6,
            beschreibung="Test"
        )

        assert sg1 == sg2

    def test_inequality_different_id(self, studiengang_class):
        """Unterschiedliche IDs bedeuten Ungleichheit"""
        sg1 = studiengang_class(
            id=1,
            name="Informatik",
            grad="B.Sc.",
            regel_semester=6
        )
        sg2 = studiengang_class(
            id=2,
            name="Informatik",
            grad="B.Sc.",
            regel_semester=6
        )

        assert sg1 != sg2

    def test_inequality_different_grad(self, studiengang_class):
        """Unterschiedliche Grade bedeuten Ungleichheit"""
        sg1 = studiengang_class(
            id=1,
            name="Informatik",
            grad="B.Sc.",
            regel_semester=6
        )
        sg2 = studiengang_class(
            id=1,
            name="Informatik",
            grad="M.Sc.",
            regel_semester=6
        )

        assert sg1 != sg2


# ============================================================================
# EDGE CASES
# ============================================================================

class TestEdgeCases:
    """Tests fuer Randfaelle"""

    def test_very_long_name(self, studiengang_class):
        """Sehr langer Studiengangname"""
        long_name = "A" * 200
        sg = studiengang_class(
            id=1,
            name=long_name,
            grad="B.Sc.",
            regel_semester=6
        )

        assert sg.name == long_name
        assert long_name in sg.get_full_name()

    def test_special_characters_in_name(self, studiengang_class):
        """Sonderzeichen im Namen"""
        sg = studiengang_class(
            id=1,
            name="IT & Management",
            grad="B.Sc.",
            regel_semester=6
        )

        assert sg.name == "IT & Management"
        assert sg.get_full_name() == "IT & Management (B.Sc.)"

    def test_unicode_in_beschreibung(self, studiengang_class):
        """Unicode-Zeichen in Beschreibung"""
        sg = studiengang_class(
            id=1,
            name="Informatik",
            grad="B.Sc.",
            regel_semester=6,
            beschreibung="Studiengang fuer Softwareentwicklung"
        )

        assert "Softwareentwicklung" in sg.beschreibung

    def test_all_valid_grades(self, studiengang_class):
        """Alle gueltigen Grade funktionieren"""
        valid_grades = ["B.Sc.", "B.A.", "B.Eng.", "M.Sc.", "M.A.", "M.Eng."]

        for grad in valid_grades:
            sg = studiengang_class(
                id=1,
                name="Test",
                grad=grad,
                regel_semester=6
            )
            assert sg.grad == grad

    def test_bachelor_master_exclusive(self, studiengang_class):
        """is_bachelor() und is_master() sind exklusiv"""
        valid_grades = ["B.Sc.", "B.A.", "B.Eng.", "M.Sc.", "M.A.", "M.Eng."]

        for grad in valid_grades:
            sg = studiengang_class(
                id=1,
                name="Test",
                grad=grad,
                regel_semester=6
            )

            # Genau einer von beiden muss True sein
            assert sg.is_bachelor() != sg.is_master()


# ============================================================================
# TYPE CHECKING TESTS
# ============================================================================

class TestTypeChecking:
    """Tests fuer Typenpruefung"""

    def test_id_is_int(self, bachelor_informatik):
        """id ist int"""
        assert isinstance(bachelor_informatik.id, int)

    def test_name_is_str(self, bachelor_informatik):
        """name ist str"""
        assert isinstance(bachelor_informatik.name, str)

    def test_grad_is_str(self, bachelor_informatik):
        """grad ist str"""
        assert isinstance(bachelor_informatik.grad, str)

    def test_regel_semester_is_int(self, bachelor_informatik):
        """regel_semester ist int"""
        assert isinstance(bachelor_informatik.regel_semester, int)

    def test_beschreibung_is_str_or_none(self, bachelor_informatik, bachelor_bwl):
        """beschreibung ist str oder None"""
        assert isinstance(bachelor_informatik.beschreibung, str)
        assert bachelor_bwl.beschreibung is None

    def test_get_full_name_returns_str(self, bachelor_informatik):
        """get_full_name() gibt str zurueck"""
        assert isinstance(bachelor_informatik.get_full_name(), str)

    def test_is_bachelor_returns_bool(self, bachelor_informatik):
        """is_bachelor() gibt bool zurueck"""
        assert isinstance(bachelor_informatik.is_bachelor(), bool)

    def test_is_master_returns_bool(self, bachelor_informatik):
        """is_master() gibt bool zurueck"""
        assert isinstance(bachelor_informatik.is_master(), bool)

    def test_get_total_ects_target_returns_int(self, bachelor_informatik):
        """get_total_ects_target() gibt int zurueck"""
        assert isinstance(bachelor_informatik.get_total_ects_target(), int)

    def test_to_dict_returns_dict(self, bachelor_informatik):
        """to_dict() gibt dict zurueck"""
        assert isinstance(bachelor_informatik.to_dict(), dict)