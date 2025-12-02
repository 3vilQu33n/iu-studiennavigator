# tests/unit/test_studiengang_modul.py
"""
Unit Tests fuer StudiengangModul Domain Model (models/studiengang_modul.py)

Testet die StudiengangModul-Klasse (Assoziationsklasse):
- Initialisierung und Validierung
- Pflichtgrad-Methoden (is_pflicht, is_wahlpflicht, is_wahl, is_mandatory)
- validate() mit ValueError bei ungueltigen Daten
- Serialisierung (to_dict)
- Factory Method (from_row)
- String-Repraesentation

OOP-Konzepte:
- KOMPOSITION zu Studiengang (studiengang_id)
- ASSOZIATION zu Modul (modul_id)
- Assoziationsklasse fuer M:N-Beziehung
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
def studiengang_modul_class():
    """Importiert StudiengangModul-Klasse"""
    try:
        from models.studiengang_modul import StudiengangModul
        return StudiengangModul
    except ImportError:
        from models import StudiengangModul
        return StudiengangModul


@pytest.fixture
def pflicht_modul(studiengang_modul_class):
    """Pflichtmodul fuer Tests"""
    return studiengang_modul_class(
        studiengang_id=1,
        modul_id=10,
        semester=1,
        pflichtgrad="Pflicht"
    )


@pytest.fixture
def wahlpflicht_modul(studiengang_modul_class):
    """Wahlpflichtmodul fuer Tests"""
    return studiengang_modul_class(
        studiengang_id=1,
        modul_id=20,
        semester=5,
        pflichtgrad="Wahlpflicht"
    )


@pytest.fixture
def wahl_modul(studiengang_modul_class):
    """Wahlmodul fuer Tests"""
    return studiengang_modul_class(
        studiengang_id=1,
        modul_id=30,
        semester=6,
        pflichtgrad="Wahl"
    )


# ============================================================================
# INITIALIZATION TESTS
# ============================================================================

class TestStudiengangModulInit:
    """Tests fuer StudiengangModul-Initialisierung"""

    def test_init_with_all_fields(self, studiengang_modul_class):
        """Initialisierung mit allen Feldern"""
        sm = studiengang_modul_class(
            studiengang_id=1,
            modul_id=10,
            semester=3,
            pflichtgrad="Pflicht"
        )

        assert sm.studiengang_id == 1
        assert sm.modul_id == 10
        assert sm.semester == 3
        assert sm.pflichtgrad == "Pflicht"

    def test_init_pflicht(self, studiengang_modul_class):
        """Initialisierung mit Pflichtgrad 'Pflicht'"""
        sm = studiengang_modul_class(
            studiengang_id=1,
            modul_id=10,
            semester=1,
            pflichtgrad="Pflicht"
        )

        assert sm.pflichtgrad == "Pflicht"

    def test_init_wahlpflicht(self, studiengang_modul_class):
        """Initialisierung mit Pflichtgrad 'Wahlpflicht'"""
        sm = studiengang_modul_class(
            studiengang_id=1,
            modul_id=10,
            semester=5,
            pflichtgrad="Wahlpflicht"
        )

        assert sm.pflichtgrad == "Wahlpflicht"

    def test_init_wahl(self, studiengang_modul_class):
        """Initialisierung mit Pflichtgrad 'Wahl'"""
        sm = studiengang_modul_class(
            studiengang_id=1,
            modul_id=10,
            semester=6,
            pflichtgrad="Wahl"
        )

        assert sm.pflichtgrad == "Wahl"

    def test_init_calls_validate(self, studiengang_modul_class):
        """__post_init__ ruft validate() auf"""
        # Ungueltige Daten sollten ValueError werfen
        with pytest.raises(ValueError):
            studiengang_modul_class(
                studiengang_id=0,  # Ungueltig
                modul_id=10,
                semester=1,
                pflichtgrad="Pflicht"
            )


# ============================================================================
# VALIDATION TESTS
# ============================================================================

class TestValidate:
    """Tests fuer validate() Methode"""

    def test_validate_valid_data(self, pflicht_modul):
        """Gueltige Daten validieren erfolgreich"""
        # Sollte keine Exception werfen
        pflicht_modul.validate()

    def test_validate_studiengang_id_zero(self, studiengang_modul_class):
        """studiengang_id = 0 ist ungueltig"""
        with pytest.raises(ValueError) as exc_info:
            studiengang_modul_class(
                studiengang_id=0,
                modul_id=10,
                semester=1,
                pflichtgrad="Pflicht"
            )

        assert "studiengang_id" in str(exc_info.value)
        assert "positiv" in str(exc_info.value)

    def test_validate_studiengang_id_negative(self, studiengang_modul_class):
        """Negative studiengang_id ist ungueltig"""
        with pytest.raises(ValueError) as exc_info:
            studiengang_modul_class(
                studiengang_id=-1,
                modul_id=10,
                semester=1,
                pflichtgrad="Pflicht"
            )

        assert "studiengang_id" in str(exc_info.value)

    def test_validate_modul_id_zero(self, studiengang_modul_class):
        """modul_id = 0 ist ungueltig"""
        with pytest.raises(ValueError) as exc_info:
            studiengang_modul_class(
                studiengang_id=1,
                modul_id=0,
                semester=1,
                pflichtgrad="Pflicht"
            )

        assert "modul_id" in str(exc_info.value)
        assert "positiv" in str(exc_info.value)

    def test_validate_modul_id_negative(self, studiengang_modul_class):
        """Negative modul_id ist ungueltig"""
        with pytest.raises(ValueError) as exc_info:
            studiengang_modul_class(
                studiengang_id=1,
                modul_id=-5,
                semester=1,
                pflichtgrad="Pflicht"
            )

        assert "modul_id" in str(exc_info.value)

    def test_validate_semester_zero(self, studiengang_modul_class):
        """Semester 0 ist ungueltig"""
        with pytest.raises(ValueError) as exc_info:
            studiengang_modul_class(
                studiengang_id=1,
                modul_id=10,
                semester=0,
                pflichtgrad="Pflicht"
            )

        assert "Semester" in str(exc_info.value)

    def test_validate_semester_negative(self, studiengang_modul_class):
        """Negatives Semester ist ungueltig"""
        with pytest.raises(ValueError) as exc_info:
            studiengang_modul_class(
                studiengang_id=1,
                modul_id=10,
                semester=-1,
                pflichtgrad="Pflicht"
            )

        assert "Semester" in str(exc_info.value)

    def test_validate_semester_too_high(self, studiengang_modul_class):
        """Semester > 14 ist ungueltig"""
        with pytest.raises(ValueError) as exc_info:
            studiengang_modul_class(
                studiengang_id=1,
                modul_id=10,
                semester=15,
                pflichtgrad="Pflicht"
            )

        assert "Semester" in str(exc_info.value)
        assert "1 und 14" in str(exc_info.value)

    def test_validate_semester_boundary_1(self, studiengang_modul_class):
        """Semester 1 ist gueltig (untere Grenze)"""
        sm = studiengang_modul_class(
            studiengang_id=1,
            modul_id=10,
            semester=1,
            pflichtgrad="Pflicht"
        )

        assert sm.semester == 1

    def test_validate_semester_boundary_14(self, studiengang_modul_class):
        """Semester 14 ist gueltig (obere Grenze, Master)"""
        sm = studiengang_modul_class(
            studiengang_id=1,
            modul_id=10,
            semester=14,
            pflichtgrad="Pflicht"
        )

        assert sm.semester == 14

    def test_validate_invalid_pflichtgrad(self, studiengang_modul_class):
        """Ungueltiger Pflichtgrad wirft ValueError"""
        with pytest.raises(ValueError) as exc_info:
            studiengang_modul_class(
                studiengang_id=1,
                modul_id=10,
                semester=1,
                pflichtgrad="ungueltig"
            )

        assert "Pflichtgrad" in str(exc_info.value)
        assert "ungueltig" in str(exc_info.value)

    def test_validate_pflichtgrad_case_sensitive(self, studiengang_modul_class):
        """Pflichtgrad ist case-sensitive"""
        with pytest.raises(ValueError):
            studiengang_modul_class(
                studiengang_id=1,
                modul_id=10,
                semester=1,
                pflichtgrad="pflicht"  # Kleingeschrieben
            )

        with pytest.raises(ValueError):
            studiengang_modul_class(
                studiengang_id=1,
                modul_id=10,
                semester=1,
                pflichtgrad="PFLICHT"  # Grossgeschrieben
            )


# ============================================================================
# IS_PFLICHT TESTS
# ============================================================================

class TestIsPflicht:
    """Tests fuer is_pflicht() Methode"""

    def test_is_pflicht_true(self, pflicht_modul):
        """is_pflicht() ist True bei Pflichtgrad 'Pflicht'"""
        assert pflicht_modul.pflichtgrad == "Pflicht"
        assert pflicht_modul.is_pflicht() is True

    def test_is_pflicht_false_wahlpflicht(self, wahlpflicht_modul):
        """is_pflicht() ist False bei Pflichtgrad 'Wahlpflicht'"""
        assert wahlpflicht_modul.pflichtgrad == "Wahlpflicht"
        assert wahlpflicht_modul.is_pflicht() is False

    def test_is_pflicht_false_wahl(self, wahl_modul):
        """is_pflicht() ist False bei Pflichtgrad 'Wahl'"""
        assert wahl_modul.pflichtgrad == "Wahl"
        assert wahl_modul.is_pflicht() is False


# ============================================================================
# IS_WAHLPFLICHT TESTS
# ============================================================================

class TestIsWahlpflicht:
    """Tests fuer is_wahlpflicht() Methode"""

    def test_is_wahlpflicht_true(self, wahlpflicht_modul):
        """is_wahlpflicht() ist True bei Pflichtgrad 'Wahlpflicht'"""
        assert wahlpflicht_modul.pflichtgrad == "Wahlpflicht"
        assert wahlpflicht_modul.is_wahlpflicht() is True

    def test_is_wahlpflicht_false_pflicht(self, pflicht_modul):
        """is_wahlpflicht() ist False bei Pflichtgrad 'Pflicht'"""
        assert pflicht_modul.pflichtgrad == "Pflicht"
        assert pflicht_modul.is_wahlpflicht() is False

    def test_is_wahlpflicht_false_wahl(self, wahl_modul):
        """is_wahlpflicht() ist False bei Pflichtgrad 'Wahl'"""
        assert wahl_modul.pflichtgrad == "Wahl"
        assert wahl_modul.is_wahlpflicht() is False


# ============================================================================
# IS_WAHL TESTS
# ============================================================================

class TestIsWahl:
    """Tests fuer is_wahl() Methode"""

    def test_is_wahl_true(self, wahl_modul):
        """is_wahl() ist True bei Pflichtgrad 'Wahl'"""
        assert wahl_modul.pflichtgrad == "Wahl"
        assert wahl_modul.is_wahl() is True

    def test_is_wahl_false_pflicht(self, pflicht_modul):
        """is_wahl() ist False bei Pflichtgrad 'Pflicht'"""
        assert pflicht_modul.pflichtgrad == "Pflicht"
        assert pflicht_modul.is_wahl() is False

    def test_is_wahl_false_wahlpflicht(self, wahlpflicht_modul):
        """is_wahl() ist False bei Pflichtgrad 'Wahlpflicht'"""
        assert wahlpflicht_modul.pflichtgrad == "Wahlpflicht"
        assert wahlpflicht_modul.is_wahl() is False


# ============================================================================
# IS_MANDATORY TESTS
# ============================================================================

class TestIsMandatory:
    """Tests fuer is_mandatory() Methode"""

    def test_is_mandatory_true_pflicht(self, pflicht_modul):
        """is_mandatory() ist True bei Pflichtgrad 'Pflicht'"""
        assert pflicht_modul.is_mandatory() is True

    def test_is_mandatory_true_wahlpflicht(self, wahlpflicht_modul):
        """is_mandatory() ist True bei Pflichtgrad 'Wahlpflicht'"""
        assert wahlpflicht_modul.is_mandatory() is True

    def test_is_mandatory_false_wahl(self, wahl_modul):
        """is_mandatory() ist False bei Pflichtgrad 'Wahl'"""
        assert wahl_modul.is_mandatory() is False


# ============================================================================
# TO_DICT TESTS
# ============================================================================

class TestToDict:
    """Tests fuer to_dict() Methode"""

    def test_to_dict_contains_all_fields(self, pflicht_modul):
        """to_dict() enthaelt alle Felder"""
        d = pflicht_modul.to_dict()

        assert 'studiengang_id' in d
        assert 'modul_id' in d
        assert 'semester' in d
        assert 'pflichtgrad' in d

    def test_to_dict_contains_computed_fields(self, pflicht_modul):
        """to_dict() enthaelt berechnete Felder"""
        d = pflicht_modul.to_dict()

        assert 'is_pflicht' in d
        assert 'is_wahlpflicht' in d
        assert 'is_wahl' in d
        assert 'is_mandatory' in d

    def test_to_dict_correct_values_pflicht(self, pflicht_modul):
        """to_dict() enthaelt korrekte Werte fuer Pflichtmodul"""
        d = pflicht_modul.to_dict()

        assert d['studiengang_id'] == 1
        assert d['modul_id'] == 10
        assert d['semester'] == 1
        assert d['pflichtgrad'] == "Pflicht"
        assert d['is_pflicht'] is True
        assert d['is_wahlpflicht'] is False
        assert d['is_wahl'] is False
        assert d['is_mandatory'] is True

    def test_to_dict_correct_values_wahlpflicht(self, wahlpflicht_modul):
        """to_dict() enthaelt korrekte Werte fuer Wahlpflichtmodul"""
        d = wahlpflicht_modul.to_dict()

        assert d['pflichtgrad'] == "Wahlpflicht"
        assert d['is_pflicht'] is False
        assert d['is_wahlpflicht'] is True
        assert d['is_wahl'] is False
        assert d['is_mandatory'] is True

    def test_to_dict_correct_values_wahl(self, wahl_modul):
        """to_dict() enthaelt korrekte Werte fuer Wahlmodul"""
        d = wahl_modul.to_dict()

        assert d['pflichtgrad'] == "Wahl"
        assert d['is_pflicht'] is False
        assert d['is_wahlpflicht'] is False
        assert d['is_wahl'] is True
        assert d['is_mandatory'] is False

    def test_to_dict_is_json_serializable(self, pflicht_modul):
        """to_dict() Ergebnis ist JSON-serialisierbar"""
        import json

        d = pflicht_modul.to_dict()

        # Sollte nicht werfen
        json_str = json.dumps(d)
        assert isinstance(json_str, str)

    def test_to_dict_returns_new_dict(self, pflicht_modul):
        """to_dict() gibt neues Dictionary zurueck"""
        d1 = pflicht_modul.to_dict()
        d2 = pflicht_modul.to_dict()

        assert d1 == d2
        assert d1 is not d2


# ============================================================================
# FROM_ROW TESTS
# ============================================================================

class TestFromRow:
    """Tests fuer from_row() Factory Method"""

    def test_from_row_dict(self, studiengang_modul_class):
        """from_row() funktioniert mit dict"""
        row = {
            'studiengang_id': 1,
            'modul_id': 10,
            'semester': 3,
            'pflichtgrad': 'Pflicht'
        }

        sm = studiengang_modul_class.from_row(row)

        assert sm.studiengang_id == 1
        assert sm.modul_id == 10
        assert sm.semester == 3
        assert sm.pflichtgrad == 'Pflicht'

    def test_from_row_all_pflichtgrade(self, studiengang_modul_class):
        """from_row() funktioniert mit allen Pflichtgraden"""
        for pflichtgrad in ["Pflicht", "Wahlpflicht", "Wahl"]:
            row = {
                'studiengang_id': 1,
                'modul_id': 10,
                'semester': 1,
                'pflichtgrad': pflichtgrad
            }

            sm = studiengang_modul_class.from_row(row)
            assert sm.pflichtgrad == pflichtgrad

    def test_from_row_sqlite_row_mock(self, studiengang_modul_class):
        """from_row() funktioniert mit sqlite3.Row-aehnlichem Objekt"""
        data = {
            'studiengang_id': 2,
            'modul_id': 20,
            'semester': 5,
            'pflichtgrad': 'Wahlpflicht'
        }

        mock_row = MagicMock()
        mock_row.__getitem__ = lambda self, key: data[key]

        sm = studiengang_modul_class.from_row(mock_row)

        assert sm.studiengang_id == 2
        assert sm.modul_id == 20
        assert sm.semester == 5
        assert sm.pflichtgrad == 'Wahlpflicht'

    def test_from_row_string_ids(self, studiengang_modul_class):
        """from_row() konvertiert String-IDs zu int"""
        row = {
            'studiengang_id': '123',
            'modul_id': '456',
            'semester': '3',
            'pflichtgrad': 'Pflicht'
        }

        sm = studiengang_modul_class.from_row(row)

        assert sm.studiengang_id == 123
        assert isinstance(sm.studiengang_id, int)
        assert sm.modul_id == 456
        assert isinstance(sm.modul_id, int)
        assert sm.semester == 3
        assert isinstance(sm.semester, int)

    def test_from_row_validates(self, studiengang_modul_class):
        """from_row() fuehrt Validierung durch"""
        row = {
            'studiengang_id': '0',  # Ungueltig
            'modul_id': '10',
            'semester': '1',
            'pflichtgrad': 'Pflicht'
        }

        with pytest.raises(ValueError):
            studiengang_modul_class.from_row(row)


# ============================================================================
# STRING REPRESENTATION TESTS
# ============================================================================

class TestStringRepresentation:
    """Tests fuer __str__ und __repr__"""

    def test_str_contains_studiengang_id(self, pflicht_modul):
        """__str__ enthaelt studiengang_id"""
        s = str(pflicht_modul)
        assert "Studiengang 1" in s

    def test_str_contains_modul_id(self, pflicht_modul):
        """__str__ enthaelt modul_id"""
        s = str(pflicht_modul)
        assert "Modul 10" in s

    def test_str_contains_semester(self, pflicht_modul):
        """__str__ enthaelt Semester"""
        s = str(pflicht_modul)
        assert "Sem 1" in s

    def test_str_contains_pflichtgrad(self, pflicht_modul):
        """__str__ enthaelt Pflichtgrad"""
        s = str(pflicht_modul)
        assert "Pflicht" in s

    def test_repr_contains_class_name(self, pflicht_modul):
        """__repr__ enthaelt Klassennamen"""
        r = repr(pflicht_modul)
        assert "StudiengangModul" in r

    def test_repr_contains_studiengang_id(self, pflicht_modul):
        """__repr__ enthaelt studiengang_id"""
        r = repr(pflicht_modul)
        assert "studiengang_id=1" in r

    def test_repr_contains_modul_id(self, pflicht_modul):
        """__repr__ enthaelt modul_id"""
        r = repr(pflicht_modul)
        assert "modul_id=10" in r

    def test_repr_contains_semester(self, pflicht_modul):
        """__repr__ enthaelt semester"""
        r = repr(pflicht_modul)
        assert "semester=1" in r

    def test_repr_contains_pflichtgrad(self, pflicht_modul):
        """__repr__ enthaelt pflichtgrad"""
        r = repr(pflicht_modul)
        assert "pflichtgrad='Pflicht'" in r


# ============================================================================
# OOP RELATIONSHIP TESTS
# ============================================================================

class TestOopRelationships:
    """Tests fuer OOP-Beziehungen"""

    def test_komposition_zu_studiengang(self, pflicht_modul):
        """studiengang_id ist Teil der Komposition"""
        assert hasattr(pflicht_modul, 'studiengang_id')
        assert pflicht_modul.studiengang_id > 0

    def test_assoziation_zu_modul(self, pflicht_modul):
        """modul_id ist Referenz fuer Assoziation"""
        assert hasattr(pflicht_modul, 'modul_id')
        assert pflicht_modul.modul_id > 0

    def test_multiple_module_same_studiengang(self, studiengang_modul_class):
        """Mehrere Module koennen zum gleichen Studiengang gehoeren"""
        sm1 = studiengang_modul_class(
            studiengang_id=1,
            modul_id=10,
            semester=1,
            pflichtgrad="Pflicht"
        )
        sm2 = studiengang_modul_class(
            studiengang_id=1,
            modul_id=20,
            semester=2,
            pflichtgrad="Pflicht"
        )

        assert sm1.studiengang_id == sm2.studiengang_id
        assert sm1.modul_id != sm2.modul_id


# ============================================================================
# DATACLASS TESTS
# ============================================================================

class TestDataclass:
    """Tests fuer Dataclass-Eigenschaften"""

    def test_equality_same_values(self, studiengang_modul_class):
        """Gleiche Werte bedeuten Gleichheit"""
        sm1 = studiengang_modul_class(
            studiengang_id=1,
            modul_id=10,
            semester=1,
            pflichtgrad="Pflicht"
        )
        sm2 = studiengang_modul_class(
            studiengang_id=1,
            modul_id=10,
            semester=1,
            pflichtgrad="Pflicht"
        )

        assert sm1 == sm2

    def test_inequality_different_studiengang(self, studiengang_modul_class):
        """Unterschiedliche studiengang_id bedeutet Ungleichheit"""
        sm1 = studiengang_modul_class(
            studiengang_id=1,
            modul_id=10,
            semester=1,
            pflichtgrad="Pflicht"
        )
        sm2 = studiengang_modul_class(
            studiengang_id=2,
            modul_id=10,
            semester=1,
            pflichtgrad="Pflicht"
        )

        assert sm1 != sm2

    def test_inequality_different_modul(self, studiengang_modul_class):
        """Unterschiedliche modul_id bedeutet Ungleichheit"""
        sm1 = studiengang_modul_class(
            studiengang_id=1,
            modul_id=10,
            semester=1,
            pflichtgrad="Pflicht"
        )
        sm2 = studiengang_modul_class(
            studiengang_id=1,
            modul_id=20,
            semester=1,
            pflichtgrad="Pflicht"
        )

        assert sm1 != sm2


# ============================================================================
# EDGE CASES
# ============================================================================

class TestEdgeCases:
    """Tests fuer Randfaelle"""

    def test_all_semesters(self, studiengang_modul_class):
        """Alle gueltigen Semester (1-14) funktionieren"""
        for semester in range(1, 15):
            sm = studiengang_modul_class(
                studiengang_id=1,
                modul_id=10,
                semester=semester,
                pflichtgrad="Pflicht"
            )
            assert sm.semester == semester

    def test_large_ids(self, studiengang_modul_class):
        """Grosse IDs werden korrekt behandelt"""
        sm = studiengang_modul_class(
            studiengang_id=999999,
            modul_id=888888,
            semester=7,
            pflichtgrad="Pflicht"
        )

        assert sm.studiengang_id == 999999
        assert sm.modul_id == 888888

    def test_pflichtgrad_methods_exclusive(self, studiengang_modul_class):
        """Nur eine Pflichtgrad-Methode kann True sein"""
        for pflichtgrad, expected_method in [
            ("Pflicht", "is_pflicht"),
            ("Wahlpflicht", "is_wahlpflicht"),
            ("Wahl", "is_wahl")
        ]:
            sm = studiengang_modul_class(
                studiengang_id=1,
                modul_id=10,
                semester=1,
                pflichtgrad=pflichtgrad
            )

            results = {
                "is_pflicht": sm.is_pflicht(),
                "is_wahlpflicht": sm.is_wahlpflicht(),
                "is_wahl": sm.is_wahl()
            }

            assert results[expected_method] is True
            for method, result in results.items():
                if method != expected_method:
                    assert result is False


# ============================================================================
# TYPE CHECKING TESTS
# ============================================================================

class TestTypeChecking:
    """Tests fuer Typenpruefung"""

    def test_studiengang_id_is_int(self, pflicht_modul):
        """studiengang_id ist int"""
        assert isinstance(pflicht_modul.studiengang_id, int)

    def test_modul_id_is_int(self, pflicht_modul):
        """modul_id ist int"""
        assert isinstance(pflicht_modul.modul_id, int)

    def test_semester_is_int(self, pflicht_modul):
        """semester ist int"""
        assert isinstance(pflicht_modul.semester, int)

    def test_pflichtgrad_is_str(self, pflicht_modul):
        """pflichtgrad ist str"""
        assert isinstance(pflicht_modul.pflichtgrad, str)

    def test_is_pflicht_returns_bool(self, pflicht_modul):
        """is_pflicht() gibt bool zurueck"""
        assert isinstance(pflicht_modul.is_pflicht(), bool)

    def test_is_wahlpflicht_returns_bool(self, pflicht_modul):
        """is_wahlpflicht() gibt bool zurueck"""
        assert isinstance(pflicht_modul.is_wahlpflicht(), bool)

    def test_is_wahl_returns_bool(self, pflicht_modul):
        """is_wahl() gibt bool zurueck"""
        assert isinstance(pflicht_modul.is_wahl(), bool)

    def test_is_mandatory_returns_bool(self, pflicht_modul):
        """is_mandatory() gibt bool zurueck"""
        assert isinstance(pflicht_modul.is_mandatory(), bool)

    def test_to_dict_returns_dict(self, pflicht_modul):
        """to_dict() gibt dict zurueck"""
        assert isinstance(pflicht_modul.to_dict(), dict)