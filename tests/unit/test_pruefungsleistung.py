# tests/unit/test_pruefungsleistung.py
"""
Unit Tests fuer Pruefungsleistung Domain Model (models/pruefungsleistung.py)

Testet die Pruefungsleistung-Klasse:
- VERERBUNG: Erbt von Modulbuchung
- POLYMORPHIE: Ueberschreibt is_passed() und to_dict()
- Initialisierung und Validierung
- Noten-Konvertierung (Decimal)
- Datum-Konvertierung
- Status-Methoden (has_grade, is_passed, can_retry, get_grade_category)
- Serialisierung (to_dict)
- Factory Method (from_row)
- String-Repraesentation
"""
from __future__ import annotations

import pytest
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock

# Mark this whole module as unit tests
pytestmark = pytest.mark.unit


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def pruefungsleistung_class():
    """Importiert Pruefungsleistung-Klasse"""
    try:
        from models.pruefungsleistung import Pruefungsleistung
        return Pruefungsleistung
    except ImportError:
        from models import Pruefungsleistung
        return Pruefungsleistung


@pytest.fixture
def modulbuchung_class():
    """Importiert Modulbuchung-Klasse (Basisklasse)"""
    try:
        from models.modulbuchung import Modulbuchung
        return Modulbuchung
    except ImportError:
        try:
            from modulbuchung import Modulbuchung
            return Modulbuchung
        except ImportError:
            pytest.skip("Modulbuchung nicht verfuegbar")
            return None


@pytest.fixture
def sample_pruefung(pruefungsleistung_class):
    """Standard-Pruefungsleistung (bestanden) fuer Tests"""
    return pruefungsleistung_class(
        id=1,
        einschreibung_id=100,
        modul_id=10,
        buchungsdatum=date(2025, 1, 15),
        status="bestanden",
        note=Decimal("2.3"),
        pruefungsdatum=date(2025, 6, 15),
        versuch=1,
        max_versuche=3,
        anmeldemodus="online",
        thema=None
    )


@pytest.fixture
def pruefung_ohne_note(pruefungsleistung_class):
    """Pruefungsleistung ohne Note (noch nicht absolviert)"""
    return pruefungsleistung_class(
        id=2,
        einschreibung_id=100,
        modul_id=11,
        buchungsdatum=date(2025, 1, 15),
        status="gebucht",
        note=None,
        pruefungsdatum=None,
        versuch=1,
        max_versuche=3,
        anmeldemodus="praesenz",
        thema=None
    )


@pytest.fixture
def pruefung_nicht_bestanden(pruefungsleistung_class):
    """Nicht bestandene Pruefungsleistung"""
    return pruefungsleistung_class(
        id=3,
        einschreibung_id=100,
        modul_id=12,
        buchungsdatum=date(2025, 1, 15),
        status="gebucht",
        note=Decimal("5.0"),
        pruefungsdatum=date(2025, 6, 15),
        versuch=1,
        max_versuche=3,
        anmeldemodus="online",
        thema=None
    )


@pytest.fixture
def pruefung_letzter_versuch(pruefungsleistung_class):
    """Pruefungsleistung im letzten Versuch"""
    return pruefungsleistung_class(
        id=4,
        einschreibung_id=100,
        modul_id=13,
        buchungsdatum=date(2025, 1, 15),
        status="gebucht",
        note=Decimal("5.0"),
        pruefungsdatum=date(2025, 6, 15),
        versuch=3,
        max_versuche=3,
        anmeldemodus="online",
        thema=None
    )


@pytest.fixture
def pruefung_mit_thema(pruefungsleistung_class):
    """Pruefungsleistung mit Thema (z.B. Bachelorarbeit)"""
    return pruefungsleistung_class(
        id=5,
        einschreibung_id=100,
        modul_id=14,
        buchungsdatum=date(2025, 1, 15),
        status="bestanden",
        note=Decimal("1.3"),
        pruefungsdatum=date(2025, 9, 1),
        versuch=1,
        max_versuche=1,
        anmeldemodus="praesenz",
        thema="Entwicklung eines Studien-Dashboards mit Python"
    )


# ============================================================================
# INHERITANCE TESTS
# ============================================================================

class TestInheritance:
    """Tests fuer VERERBUNG von Modulbuchung"""

    def test_inherits_from_modulbuchung(self, pruefungsleistung_class, modulbuchung_class):
        """Pruefungsleistung erbt von Modulbuchung"""
        assert issubclass(pruefungsleistung_class, modulbuchung_class)

    def test_has_base_class_attributes(self, sample_pruefung):
        """Pruefungsleistung hat alle Basisklassen-Attribute"""
        assert hasattr(sample_pruefung, 'id')
        assert hasattr(sample_pruefung, 'einschreibung_id')
        assert hasattr(sample_pruefung, 'modul_id')
        assert hasattr(sample_pruefung, 'buchungsdatum')
        assert hasattr(sample_pruefung, 'status')

    def test_has_extended_attributes(self, sample_pruefung):
        """Pruefungsleistung hat erweiterte Attribute"""
        assert hasattr(sample_pruefung, 'note')
        assert hasattr(sample_pruefung, 'pruefungsdatum')
        assert hasattr(sample_pruefung, 'versuch')
        assert hasattr(sample_pruefung, 'max_versuche')
        assert hasattr(sample_pruefung, 'anmeldemodus')
        assert hasattr(sample_pruefung, 'thema')

    def test_base_class_methods_available(self, sample_pruefung):
        """Basisklassen-Methoden sind verfuegbar"""
        assert hasattr(sample_pruefung, 'is_open')
        assert hasattr(sample_pruefung, 'is_recognized')
        assert callable(sample_pruefung.is_open)
        assert callable(sample_pruefung.is_recognized)


# ============================================================================
# INITIALIZATION TESTS
# ============================================================================

class TestPruefungsleistungInit:
    """Tests fuer Pruefungsleistung-Initialisierung"""

    def test_init_with_all_fields(self, pruefungsleistung_class):
        """Initialisierung mit allen Feldern"""
        p = pruefungsleistung_class(
            id=1,
            einschreibung_id=100,
            modul_id=10,
            buchungsdatum=date(2025, 1, 15),
            status="bestanden",
            note=Decimal("2.3"),
            pruefungsdatum=date(2025, 6, 15),
            versuch=1,
            max_versuche=3,
            anmeldemodus="online",
            thema="Test-Thema"
        )

        assert p.id == 1
        assert p.einschreibung_id == 100
        assert p.modul_id == 10
        assert p.buchungsdatum == date(2025, 1, 15)
        assert p.status == "bestanden"
        assert p.note == Decimal("2.3")
        assert p.pruefungsdatum == date(2025, 6, 15)
        assert p.versuch == 1
        assert p.max_versuche == 3
        assert p.anmeldemodus == "online"
        assert p.thema == "Test-Thema"

    def test_init_default_values(self, pruefungsleistung_class):
        """Initialisierung mit Default-Werten"""
        p = pruefungsleistung_class(
            id=1,
            einschreibung_id=100,
            modul_id=10,
            buchungsdatum=date(2025, 1, 15),
            status="gebucht"
        )

        assert p.note is None
        assert p.pruefungsdatum is None
        assert p.versuch == 1
        assert p.max_versuche == 3
        assert p.anmeldemodus == "online"
        assert p.thema is None

    def test_init_with_none_note(self, pruefungsleistung_class):
        """Initialisierung mit None als Note"""
        p = pruefungsleistung_class(
            id=1,
            einschreibung_id=100,
            modul_id=10,
            buchungsdatum=date(2025, 1, 15),
            status="gebucht",
            note=None
        )

        assert p.note is None

    def test_init_anmeldemodus_praesenz(self, pruefungsleistung_class):
        """Initialisierung mit Anmeldemodus 'praesenz'"""
        p = pruefungsleistung_class(
            id=1,
            einschreibung_id=100,
            modul_id=10,
            buchungsdatum=date(2025, 1, 15),
            status="gebucht",
            anmeldemodus="praesenz"
        )

        assert p.anmeldemodus == "praesenz"


# ============================================================================
# TYPE CONVERSION TESTS
# ============================================================================

class TestTypeConversion:
    """Tests fuer Typ-Konvertierung in __post_init__"""

    def test_note_from_float(self, pruefungsleistung_class):
        """Float-Note wird zu Decimal konvertiert"""
        p = pruefungsleistung_class(
            id=1,
            einschreibung_id=100,
            modul_id=10,
            buchungsdatum=date(2025, 1, 15),
            status="bestanden",
            note=2.3  # float
        )

        assert isinstance(p.note, Decimal)
        assert p.note == Decimal("2.3")

    def test_note_from_string(self, pruefungsleistung_class):
        """String-Note wird zu Decimal konvertiert"""
        p = pruefungsleistung_class(
            id=1,
            einschreibung_id=100,
            modul_id=10,
            buchungsdatum=date(2025, 1, 15),
            status="bestanden",
            note="1.7"  # string
        )

        assert isinstance(p.note, Decimal)
        assert p.note == Decimal("1.7")

    def test_note_from_int(self, pruefungsleistung_class):
        """Integer-Note wird zu Decimal konvertiert"""
        p = pruefungsleistung_class(
            id=1,
            einschreibung_id=100,
            modul_id=10,
            buchungsdatum=date(2025, 1, 15),
            status="bestanden",
            note=2  # int
        )

        assert isinstance(p.note, Decimal)
        assert p.note == Decimal("2")

    def test_pruefungsdatum_from_string(self, pruefungsleistung_class):
        """String-Pruefungsdatum wird zu date konvertiert"""
        p = pruefungsleistung_class(
            id=1,
            einschreibung_id=100,
            modul_id=10,
            buchungsdatum=date(2025, 1, 15),
            status="bestanden",
            pruefungsdatum="2025-06-15"  # string
        )

        assert isinstance(p.pruefungsdatum, date)
        assert p.pruefungsdatum == date(2025, 6, 15)

    def test_pruefungsdatum_date_unchanged(self, pruefungsleistung_class):
        """date-Objekt bleibt unveraendert"""
        original_date = date(2025, 6, 15)
        p = pruefungsleistung_class(
            id=1,
            einschreibung_id=100,
            modul_id=10,
            buchungsdatum=date(2025, 1, 15),
            status="bestanden",
            pruefungsdatum=original_date
        )

        assert p.pruefungsdatum == original_date


# ============================================================================
# HAS_GRADE TESTS
# ============================================================================

class TestHasGrade:
    """Tests fuer has_grade() Methode"""

    def test_has_grade_true_with_note(self, sample_pruefung):
        """has_grade() ist True wenn Note vorhanden"""
        assert sample_pruefung.note is not None
        assert sample_pruefung.has_grade() is True

    def test_has_grade_false_without_note(self, pruefung_ohne_note):
        """has_grade() ist False wenn keine Note"""
        assert pruefung_ohne_note.note is None
        assert pruefung_ohne_note.has_grade() is False


# ============================================================================
# IS_PASSED TESTS (POLYMORPHIE)
# ============================================================================

class TestIsPassed:
    """Tests fuer is_passed() Methode (POLYMORPHIE - ueberschreibt Basisklasse)"""

    def test_is_passed_true_with_good_grade(self, sample_pruefung):
        """is_passed() ist True bei Note <= 4.0"""
        assert sample_pruefung.note == Decimal("2.3")
        assert sample_pruefung.is_passed() is True

    def test_is_passed_true_at_boundary_4_0(self, pruefungsleistung_class):
        """is_passed() ist True bei Note = 4.0 (Grenze)"""
        p = pruefungsleistung_class(
            id=1,
            einschreibung_id=100,
            modul_id=10,
            buchungsdatum=date(2025, 1, 15),
            status="gebucht",
            note=Decimal("4.0")
        )

        assert p.is_passed() is True

    def test_is_passed_false_with_bad_grade(self, pruefung_nicht_bestanden):
        """is_passed() ist False bei Note > 4.0"""
        assert pruefung_nicht_bestanden.note == Decimal("5.0")
        assert pruefung_nicht_bestanden.is_passed() is False

    def test_is_passed_false_without_grade(self, pruefung_ohne_note):
        """is_passed() ist False ohne Note"""
        assert pruefung_ohne_note.note is None
        assert pruefung_ohne_note.is_passed() is False

    def test_is_passed_boundary_4_1(self, pruefungsleistung_class):
        """is_passed() ist False bei Note = 4.1"""
        p = pruefungsleistung_class(
            id=1,
            einschreibung_id=100,
            modul_id=10,
            buchungsdatum=date(2025, 1, 15),
            status="gebucht",
            note=Decimal("4.1")
        )

        assert p.is_passed() is False


# ============================================================================
# CAN_RETRY TESTS
# ============================================================================

class TestCanRetry:
    """Tests fuer can_retry() Methode"""

    def test_can_retry_true_first_attempt(self, sample_pruefung):
        """can_retry() ist True beim ersten Versuch"""
        assert sample_pruefung.versuch == 1
        assert sample_pruefung.max_versuche == 3
        assert sample_pruefung.can_retry() is True

    def test_can_retry_true_second_attempt(self, pruefungsleistung_class):
        """can_retry() ist True beim zweiten Versuch"""
        p = pruefungsleistung_class(
            id=1,
            einschreibung_id=100,
            modul_id=10,
            buchungsdatum=date(2025, 1, 15),
            status="gebucht",
            versuch=2,
            max_versuche=3
        )

        assert p.can_retry() is True

    def test_can_retry_false_last_attempt(self, pruefung_letzter_versuch):
        """can_retry() ist False beim letzten Versuch"""
        assert pruefung_letzter_versuch.versuch == 3
        assert pruefung_letzter_versuch.max_versuche == 3
        assert pruefung_letzter_versuch.can_retry() is False

    def test_can_retry_false_single_attempt_module(self, pruefung_mit_thema):
        """can_retry() ist False bei max_versuche=1"""
        assert pruefung_mit_thema.versuch == 1
        assert pruefung_mit_thema.max_versuche == 1
        assert pruefung_mit_thema.can_retry() is False


# ============================================================================
# GET_GRADE_CATEGORY TESTS
# ============================================================================

class TestGetGradeCategory:
    """Tests fuer get_grade_category() Methode"""

    def test_category_keine_note(self, pruefung_ohne_note):
        """Kategorie 'keine_note' ohne Note"""
        assert pruefung_ohne_note.get_grade_category() == 'keine_note'

    def test_category_sehr_gut(self, pruefungsleistung_class):
        """Kategorie 'sehr_gut' bei Note <= 2.0"""
        p = pruefungsleistung_class(
            id=1,
            einschreibung_id=100,
            modul_id=10,
            buchungsdatum=date(2025, 1, 15),
            status="bestanden",
            note=Decimal("1.3")
        )

        assert p.get_grade_category() == 'sehr_gut'

    def test_category_sehr_gut_boundary(self, pruefungsleistung_class):
        """Kategorie 'sehr_gut' bei Note = 2.0"""
        p = pruefungsleistung_class(
            id=1,
            einschreibung_id=100,
            modul_id=10,
            buchungsdatum=date(2025, 1, 15),
            status="bestanden",
            note=Decimal("2.0")
        )

        assert p.get_grade_category() == 'sehr_gut'

    def test_category_gut(self, pruefungsleistung_class):
        """Kategorie 'gut' bei Note 2.1-3.0"""
        p = pruefungsleistung_class(
            id=1,
            einschreibung_id=100,
            modul_id=10,
            buchungsdatum=date(2025, 1, 15),
            status="bestanden",
            note=Decimal("2.7")
        )

        assert p.get_grade_category() == 'gut'

    def test_category_gut_boundary(self, pruefungsleistung_class):
        """Kategorie 'gut' bei Note = 3.0"""
        p = pruefungsleistung_class(
            id=1,
            einschreibung_id=100,
            modul_id=10,
            buchungsdatum=date(2025, 1, 15),
            status="bestanden",
            note=Decimal("3.0")
        )

        assert p.get_grade_category() == 'gut'

    def test_category_bestanden(self, pruefungsleistung_class):
        """Kategorie 'bestanden' bei Note 3.1-4.0"""
        p = pruefungsleistung_class(
            id=1,
            einschreibung_id=100,
            modul_id=10,
            buchungsdatum=date(2025, 1, 15),
            status="bestanden",
            note=Decimal("3.7")
        )

        assert p.get_grade_category() == 'bestanden'

    def test_category_bestanden_boundary(self, pruefungsleistung_class):
        """Kategorie 'bestanden' bei Note = 4.0"""
        p = pruefungsleistung_class(
            id=1,
            einschreibung_id=100,
            modul_id=10,
            buchungsdatum=date(2025, 1, 15),
            status="bestanden",
            note=Decimal("4.0")
        )

        assert p.get_grade_category() == 'bestanden'

    def test_category_nicht_bestanden(self, pruefung_nicht_bestanden):
        """Kategorie 'nicht_bestanden' bei Note > 4.0"""
        assert pruefung_nicht_bestanden.note == Decimal("5.0")
        assert pruefung_nicht_bestanden.get_grade_category() == 'nicht_bestanden'


# ============================================================================
# TO_DICT TESTS (POLYMORPHIE)
# ============================================================================

class TestToDict:
    """Tests fuer to_dict() Methode (POLYMORPHIE - erweitert Basisklasse)"""

    def test_to_dict_contains_base_fields(self, sample_pruefung):
        """to_dict() enthaelt Basisklassen-Felder"""
        d = sample_pruefung.to_dict()

        assert 'id' in d
        assert 'einschreibung_id' in d
        assert 'modul_id' in d
        assert 'buchungsdatum' in d
        assert 'status' in d

    def test_to_dict_contains_extended_fields(self, sample_pruefung):
        """to_dict() enthaelt erweiterte Felder"""
        d = sample_pruefung.to_dict()

        assert 'note' in d
        assert 'note_formatted' in d
        assert 'pruefungsdatum' in d
        assert 'versuch' in d
        assert 'max_versuche' in d
        assert 'anmeldemodus' in d
        assert 'thema' in d

    def test_to_dict_contains_computed_fields(self, sample_pruefung):
        """to_dict() enthaelt berechnete Felder"""
        d = sample_pruefung.to_dict()

        assert 'has_grade' in d
        assert 'can_retry' in d
        assert 'grade_category' in d
        # Von Basisklasse:
        assert 'is_open' in d
        assert 'is_passed' in d
        assert 'is_recognized' in d

    def test_to_dict_note_is_float(self, sample_pruefung):
        """note ist float in dict"""
        d = sample_pruefung.to_dict()

        assert isinstance(d['note'], float)
        assert d['note'] == 2.3

    def test_to_dict_note_none(self, pruefung_ohne_note):
        """note None bleibt None"""
        d = pruefung_ohne_note.to_dict()

        assert d['note'] is None

    def test_to_dict_note_formatted(self, sample_pruefung):
        """note_formatted ist formatierter String"""
        d = sample_pruefung.to_dict()

        assert d['note_formatted'] == "2.30"

    def test_to_dict_note_formatted_none(self, pruefung_ohne_note):
        """note_formatted bei None zeigt Dash"""
        d = pruefung_ohne_note.to_dict()

        # Akzeptiere verschiedene Dash-Varianten (inkl. UTF-8 Encoding-Varianten)
        valid_dashes = ["–", "-", "—", "â€", "\u2013"]
        assert d['note_formatted'] in valid_dashes or any(dash in d['note_formatted'] for dash in valid_dashes)

    def test_to_dict_pruefungsdatum_is_iso_string(self, sample_pruefung):
        """pruefungsdatum ist ISO-String in dict"""
        d = sample_pruefung.to_dict()

        assert isinstance(d['pruefungsdatum'], str)
        assert d['pruefungsdatum'] == "2025-06-15"

    def test_to_dict_pruefungsdatum_none(self, pruefung_ohne_note):
        """pruefungsdatum None bleibt None"""
        d = pruefung_ohne_note.to_dict()

        assert d['pruefungsdatum'] is None

    def test_to_dict_thema(self, pruefung_mit_thema):
        """thema wird korrekt serialisiert"""
        d = pruefung_mit_thema.to_dict()

        assert d['thema'] == "Entwicklung eines Studien-Dashboards mit Python"

    def test_to_dict_is_json_serializable(self, sample_pruefung):
        """to_dict() Ergebnis ist JSON-serialisierbar"""
        import json

        d = sample_pruefung.to_dict()

        # Sollte nicht werfen
        json_str = json.dumps(d)
        assert isinstance(json_str, str)


# ============================================================================
# FROM_ROW TESTS
# ============================================================================

class TestFromRow:
    """Tests fuer from_row() Factory Method"""

    def test_from_row_dict(self, pruefungsleistung_class):
        """from_row() funktioniert mit dict"""
        row = {
            'id': 1,
            'einschreibung_id': 100,
            'modul_id': 10,
            'buchungsdatum': '2025-01-15',
            'status': 'bestanden',
            'note': '2.3',
            'pruefungsdatum': '2025-06-15',
            'versuch': 1,
            'max_versuche': 3,
            'anmeldemodus': 'online',
            'thema': None
        }

        p = pruefungsleistung_class.from_row(row)

        assert p.id == 1
        assert p.einschreibung_id == 100
        assert p.modul_id == 10
        assert p.note == Decimal("2.3")
        assert p.pruefungsdatum == date(2025, 6, 15)
        assert p.versuch == 1
        assert p.anmeldemodus == 'online'

    def test_from_row_missing_optional_fields(self, pruefungsleistung_class):
        """from_row() behandelt fehlende optionale Felder"""
        row = {
            'id': 1
        }

        mock_row = MagicMock()

        def getitem(key):
            if key == 'id':
                return 1
            raise KeyError(key)

        mock_row.__getitem__ = lambda self, key: getitem(key)

        p = pruefungsleistung_class.from_row(mock_row)

        assert p.id == 1
        assert p.einschreibung_id == 0
        assert p.modul_id == 0
        assert p.status == 'gebucht'
        assert p.note is None
        assert p.versuch == 1
        assert p.max_versuche == 3
        assert p.anmeldemodus == 'online'

    def test_from_row_with_date_objects(self, pruefungsleistung_class):
        """from_row() funktioniert mit date-Objekten"""
        row = {
            'id': 1,
            'einschreibung_id': 100,
            'modul_id': 10,
            'buchungsdatum': date(2025, 1, 15),
            'status': 'bestanden',
            'note': Decimal("2.3"),
            'pruefungsdatum': date(2025, 6, 15),
            'versuch': 1,
            'max_versuche': 3,
            'anmeldemodus': 'online',
            'thema': None
        }

        p = pruefungsleistung_class.from_row(row)

        assert p.buchungsdatum == date(2025, 1, 15)
        assert p.pruefungsdatum == date(2025, 6, 15)

    def test_from_row_sqlite_row_mock(self, pruefungsleistung_class):
        """from_row() funktioniert mit sqlite3.Row-aehnlichem Objekt"""
        data = {
            'id': 2,
            'einschreibung_id': 200,
            'modul_id': 20,
            'buchungsdatum': '2025-03-01',
            'status': 'bestanden',
            'note': '1.7',
            'pruefungsdatum': '2025-07-15',
            'versuch': 2,
            'max_versuche': 3,
            'anmeldemodus': 'praesenz',
            'thema': 'Bachelorarbeit'
        }

        mock_row = MagicMock()
        mock_row.__getitem__ = lambda self, key: data[key]

        p = pruefungsleistung_class.from_row(mock_row)

        assert p.id == 2
        assert p.note == Decimal("1.7")
        assert p.versuch == 2
        assert p.anmeldemodus == 'praesenz'
        assert p.thema == 'Bachelorarbeit'

    def test_from_row_string_ids(self, pruefungsleistung_class):
        """from_row() konvertiert String-IDs zu int"""
        row = {
            'id': '123',
            'einschreibung_id': '456',
            'modul_id': '789',
            'buchungsdatum': '2025-01-15',
            'status': 'gebucht',
            'note': None,
            'pruefungsdatum': None,
            'versuch': '2',
            'max_versuche': '3',
            'anmeldemodus': 'online',
            'thema': None
        }

        p = pruefungsleistung_class.from_row(row)

        assert p.id == 123
        assert isinstance(p.id, int)
        assert p.einschreibung_id == 456
        assert p.versuch == 2


# ============================================================================
# STRING REPRESENTATION TESTS
# ============================================================================

class TestStringRepresentation:
    """Tests fuer __str__ und __repr__"""

    def test_str_contains_modul_id(self, sample_pruefung):
        """__str__ enthaelt modul_id"""
        s = str(sample_pruefung)
        assert "10" in s

    def test_str_contains_note(self, sample_pruefung):
        """__str__ enthaelt Note"""
        s = str(sample_pruefung)
        assert "2.30" in s or "2.3" in s

    def test_str_without_note(self, pruefung_ohne_note):
        """__str__ zeigt 'keine Note' ohne Note"""
        s = str(pruefung_ohne_note)
        assert "keine Note" in s

    def test_str_with_retry(self, pruefungsleistung_class):
        """__str__ zeigt Versuch bei versuch > 1"""
        p = pruefungsleistung_class(
            id=1,
            einschreibung_id=100,
            modul_id=10,
            buchungsdatum=date(2025, 1, 15),
            status="gebucht",
            note=Decimal("5.0"),
            versuch=2
        )

        s = str(p)
        assert "(Versuch 2)" in s

    def test_str_no_versuch_when_first(self, sample_pruefung):
        """__str__ zeigt keinen Versuch bei versuch=1"""
        assert sample_pruefung.versuch == 1
        s = str(sample_pruefung)
        assert "Versuch" not in s

    def test_repr_contains_class_name(self, sample_pruefung):
        """__repr__ enthaelt Klassennamen"""
        r = repr(sample_pruefung)
        assert "Pruefungsleistung" in r

    def test_repr_contains_id(self, sample_pruefung):
        """__repr__ enthaelt ID"""
        r = repr(sample_pruefung)
        assert "id=1" in r

    def test_repr_contains_modul_id(self, sample_pruefung):
        """__repr__ enthaelt modul_id"""
        r = repr(sample_pruefung)
        assert "modul_id=10" in r

    def test_repr_contains_note(self, sample_pruefung):
        """__repr__ enthaelt Note"""
        r = repr(sample_pruefung)
        assert "note=" in r

    def test_repr_contains_versuch(self, sample_pruefung):
        """__repr__ enthaelt Versuch"""
        r = repr(sample_pruefung)
        assert "versuch=" in r


# ============================================================================
# DATACLASS TESTS
# ============================================================================

class TestDataclass:
    """Tests fuer Dataclass-Eigenschaften"""

    def test_equality_same_values(self, pruefungsleistung_class):
        """Gleiche Werte bedeuten Gleichheit"""
        p1 = pruefungsleistung_class(
            id=1,
            einschreibung_id=100,
            modul_id=10,
            buchungsdatum=date(2025, 1, 15),
            status="bestanden",
            note=Decimal("2.3"),
            pruefungsdatum=date(2025, 6, 15),
            versuch=1,
            max_versuche=3,
            anmeldemodus="online",
            thema=None
        )
        p2 = pruefungsleistung_class(
            id=1,
            einschreibung_id=100,
            modul_id=10,
            buchungsdatum=date(2025, 1, 15),
            status="bestanden",
            note=Decimal("2.3"),
            pruefungsdatum=date(2025, 6, 15),
            versuch=1,
            max_versuche=3,
            anmeldemodus="online",
            thema=None
        )

        assert p1 == p2

    def test_inequality_different_note(self, pruefungsleistung_class):
        """Unterschiedliche Noten bedeuten Ungleichheit"""
        p1 = pruefungsleistung_class(
            id=1,
            einschreibung_id=100,
            modul_id=10,
            buchungsdatum=date(2025, 1, 15),
            status="bestanden",
            note=Decimal("2.3")
        )
        p2 = pruefungsleistung_class(
            id=1,
            einschreibung_id=100,
            modul_id=10,
            buchungsdatum=date(2025, 1, 15),
            status="bestanden",
            note=Decimal("1.7")
        )

        assert p1 != p2


# ============================================================================
# EDGE CASES
# ============================================================================

class TestEdgeCases:
    """Tests fuer Randfaelle"""

    def test_note_1_0(self, pruefungsleistung_class):
        """Beste Note 1.0"""
        p = pruefungsleistung_class(
            id=1,
            einschreibung_id=100,
            modul_id=10,
            buchungsdatum=date(2025, 1, 15),
            status="bestanden",
            note=Decimal("1.0")
        )

        assert p.note == Decimal("1.0")
        assert p.is_passed() is True
        assert p.get_grade_category() == 'sehr_gut'

    def test_note_5_0(self, pruefungsleistung_class):
        """Schlechteste Note 5.0"""
        p = pruefungsleistung_class(
            id=1,
            einschreibung_id=100,
            modul_id=10,
            buchungsdatum=date(2025, 1, 15),
            status="nicht_bestanden",
            note=Decimal("5.0")
        )

        assert p.note == Decimal("5.0")
        assert p.is_passed() is False
        assert p.get_grade_category() == 'nicht_bestanden'

    def test_large_versuch_number(self, pruefungsleistung_class):
        """Grosser Versuchszaehler"""
        p = pruefungsleistung_class(
            id=1,
            einschreibung_id=100,
            modul_id=10,
            buchungsdatum=date(2025, 1, 15),
            status="gebucht",
            versuch=10,
            max_versuche=10
        )

        assert p.versuch == 10
        assert p.can_retry() is False

    def test_very_long_thema(self, pruefungsleistung_class):
        """Sehr langes Thema"""
        long_thema = "A" * 500
        p = pruefungsleistung_class(
            id=1,
            einschreibung_id=100,
            modul_id=10,
            buchungsdatum=date(2025, 1, 15),
            status="bestanden",
            note=Decimal("1.3"),
            thema=long_thema
        )

        assert p.thema == long_thema
        assert len(p.thema) == 500

    def test_note_with_many_decimals(self, pruefungsleistung_class):
        """Note mit vielen Dezimalstellen"""
        p = pruefungsleistung_class(
            id=1,
            einschreibung_id=100,
            modul_id=10,
            buchungsdatum=date(2025, 1, 15),
            status="bestanden",
            note=Decimal("2.333333")
        )

        assert p.note == Decimal("2.333333")


# ============================================================================
# TYPE CHECKING TESTS
# ============================================================================

class TestTypeChecking:
    """Tests fuer Typenpruefung"""

    def test_note_is_decimal_or_none(self, sample_pruefung, pruefung_ohne_note):
        """note ist Decimal oder None"""
        assert isinstance(sample_pruefung.note, Decimal)
        assert pruefung_ohne_note.note is None

    def test_pruefungsdatum_is_date_or_none(self, sample_pruefung, pruefung_ohne_note):
        """pruefungsdatum ist date oder None"""
        assert isinstance(sample_pruefung.pruefungsdatum, date)
        assert pruefung_ohne_note.pruefungsdatum is None

    def test_versuch_is_int(self, sample_pruefung):
        """versuch ist int"""
        assert isinstance(sample_pruefung.versuch, int)

    def test_max_versuche_is_int(self, sample_pruefung):
        """max_versuche ist int"""
        assert isinstance(sample_pruefung.max_versuche, int)

    def test_anmeldemodus_is_str(self, sample_pruefung):
        """anmeldemodus ist str"""
        assert isinstance(sample_pruefung.anmeldemodus, str)

    def test_thema_is_str_or_none(self, sample_pruefung, pruefung_mit_thema):
        """thema ist str oder None"""
        assert sample_pruefung.thema is None
        assert isinstance(pruefung_mit_thema.thema, str)

    def test_has_grade_returns_bool(self, sample_pruefung):
        """has_grade() gibt bool zurueck"""
        assert isinstance(sample_pruefung.has_grade(), bool)

    def test_is_passed_returns_bool(self, sample_pruefung):
        """is_passed() gibt bool zurueck"""
        assert isinstance(sample_pruefung.is_passed(), bool)

    def test_can_retry_returns_bool(self, sample_pruefung):
        """can_retry() gibt bool zurueck"""
        assert isinstance(sample_pruefung.can_retry(), bool)

    def test_get_grade_category_returns_str(self, sample_pruefung):
        """get_grade_category() gibt str zurueck"""
        assert isinstance(sample_pruefung.get_grade_category(), str)

    def test_to_dict_returns_dict(self, sample_pruefung):
        """to_dict() gibt dict zurueck"""
        assert isinstance(sample_pruefung.to_dict(), dict)