# tests/unit/test_modulbuchung.py
"""
Unit Tests fuer Modulbuchung Domain Model (models/modulbuchung.py)

Testet die Modulbuchung-Klasse:
- Initialisierung und Validierung
- Datum-Konvertierung
- Status-Methoden (is_open, is_passed, is_recognized)
- Serialisierung (to_dict)
- Factory Method (from_row)
- String-Repraesentation

HINWEIS: Modulbuchung ist die BASISKLASSE fuer Pruefungsleistung (VERERBUNG)
"""
from __future__ import annotations

import pytest
from datetime import date
from unittest.mock import MagicMock

# Mark this whole module as unit tests
pytestmark = pytest.mark.unit


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def modulbuchung_class():
    """Importiert Modulbuchung-Klasse"""
    try:
        from models.modulbuchung import Modulbuchung
        return Modulbuchung
    except ImportError:
        from models import Modulbuchung
        return Modulbuchung


@pytest.fixture
def sample_buchung(modulbuchung_class):
    """Standard-Modulbuchung (gebucht) fuer Tests"""
    return modulbuchung_class(
        id=1,
        einschreibung_id=100,
        modul_id=10,
        buchungsdatum=date(2025, 1, 15),
        status="gebucht"
    )


@pytest.fixture
def passed_buchung(modulbuchung_class):
    """Bestandene Modulbuchung fuer Tests"""
    return modulbuchung_class(
        id=2,
        einschreibung_id=100,
        modul_id=11,
        buchungsdatum=date(2025, 1, 15),
        status="bestanden"
    )


@pytest.fixture
def recognized_buchung(modulbuchung_class):
    """Anerkannte Modulbuchung fuer Tests"""
    return modulbuchung_class(
        id=3,
        einschreibung_id=100,
        modul_id=12,
        buchungsdatum=None,  # Anerkannte Module haben oft kein Buchungsdatum
        status="anerkannt"
    )


@pytest.fixture
def failed_buchung(modulbuchung_class):
    """Nicht bestandene Modulbuchung fuer Tests"""
    return modulbuchung_class(
        id=4,
        einschreibung_id=100,
        modul_id=13,
        buchungsdatum=date(2025, 1, 15),
        status="nicht_bestanden"
    )


# ============================================================================
# INITIALIZATION TESTS
# ============================================================================

class TestModulbuchungInit:
    """Tests fuer Modulbuchung-Initialisierung"""

    def test_init_with_all_fields(self, modulbuchung_class):
        """Initialisierung mit allen Feldern"""
        mb = modulbuchung_class(
            id=1,
            einschreibung_id=100,
            modul_id=10,
            buchungsdatum=date(2025, 1, 15),
            status="gebucht"
        )

        assert mb.id == 1
        assert mb.einschreibung_id == 100
        assert mb.modul_id == 10
        assert mb.buchungsdatum == date(2025, 1, 15)
        assert mb.status == "gebucht"

    def test_init_with_none_buchungsdatum(self, modulbuchung_class):
        """Initialisierung mit None als Buchungsdatum"""
        mb = modulbuchung_class(
            id=1,
            einschreibung_id=100,
            modul_id=10,
            buchungsdatum=None,
            status="anerkannt"
        )

        assert mb.buchungsdatum is None

    def test_init_status_gebucht(self, modulbuchung_class):
        """Initialisierung mit Status 'gebucht'"""
        mb = modulbuchung_class(
            id=1,
            einschreibung_id=100,
            modul_id=10,
            buchungsdatum=date(2025, 1, 15),
            status="gebucht"
        )

        assert mb.status == "gebucht"

    def test_init_status_bestanden(self, modulbuchung_class):
        """Initialisierung mit Status 'bestanden'"""
        mb = modulbuchung_class(
            id=1,
            einschreibung_id=100,
            modul_id=10,
            buchungsdatum=date(2025, 1, 15),
            status="bestanden"
        )

        assert mb.status == "bestanden"

    def test_init_status_anerkannt(self, modulbuchung_class):
        """Initialisierung mit Status 'anerkannt'"""
        mb = modulbuchung_class(
            id=1,
            einschreibung_id=100,
            modul_id=10,
            buchungsdatum=None,
            status="anerkannt"
        )

        assert mb.status == "anerkannt"

    def test_init_status_nicht_bestanden(self, modulbuchung_class):
        """Initialisierung mit Status 'nicht_bestanden'"""
        mb = modulbuchung_class(
            id=1,
            einschreibung_id=100,
            modul_id=10,
            buchungsdatum=date(2025, 1, 15),
            status="nicht_bestanden"
        )

        assert mb.status == "nicht_bestanden"


# ============================================================================
# DATE CONVERSION TESTS
# ============================================================================

class TestDateConversion:
    """Tests fuer Datum-Konvertierung in __post_init__"""

    def test_string_date_converted(self, modulbuchung_class):
        """ISO-String wird zu date konvertiert"""
        mb = modulbuchung_class(
            id=1,
            einschreibung_id=100,
            modul_id=10,
            buchungsdatum="2025-01-15",  # String
            status="gebucht"
        )

        assert isinstance(mb.buchungsdatum, date)
        assert mb.buchungsdatum == date(2025, 1, 15)

    def test_date_object_unchanged(self, modulbuchung_class):
        """date-Objekt bleibt unveraendert"""
        original_date = date(2025, 6, 1)
        mb = modulbuchung_class(
            id=1,
            einschreibung_id=100,
            modul_id=10,
            buchungsdatum=original_date,
            status="gebucht"
        )

        assert mb.buchungsdatum is original_date

    def test_none_date_unchanged(self, modulbuchung_class):
        """None bleibt None"""
        mb = modulbuchung_class(
            id=1,
            einschreibung_id=100,
            modul_id=10,
            buchungsdatum=None,
            status="anerkannt"
        )

        assert mb.buchungsdatum is None

    def test_various_date_formats(self, modulbuchung_class):
        """Verschiedene Datumsformate"""
        dates = [
            ("2025-01-01", date(2025, 1, 1)),
            ("2025-12-31", date(2025, 12, 31)),
            ("2020-06-15", date(2020, 6, 15)),
        ]

        for date_str, expected in dates:
            mb = modulbuchung_class(
                id=1,
                einschreibung_id=100,
                modul_id=10,
                buchungsdatum=date_str,
                status="gebucht"
            )
            assert mb.buchungsdatum == expected


# ============================================================================
# IS_OPEN TESTS
# ============================================================================

class TestIsOpen:
    """Tests fuer is_open() Methode"""

    def test_is_open_true_when_gebucht(self, sample_buchung):
        """is_open() ist True bei Status 'gebucht'"""
        assert sample_buchung.status == "gebucht"
        assert sample_buchung.is_open() is True

    def test_is_open_false_when_bestanden(self, passed_buchung):
        """is_open() ist False bei Status 'bestanden'"""
        assert passed_buchung.status == "bestanden"
        assert passed_buchung.is_open() is False

    def test_is_open_false_when_anerkannt(self, recognized_buchung):
        """is_open() ist False bei Status 'anerkannt'"""
        assert recognized_buchung.status == "anerkannt"
        assert recognized_buchung.is_open() is False

    def test_is_open_false_when_nicht_bestanden(self, failed_buchung):
        """is_open() ist False bei Status 'nicht_bestanden'"""
        assert failed_buchung.status == "nicht_bestanden"
        assert failed_buchung.is_open() is False


# ============================================================================
# IS_PASSED TESTS
# ============================================================================

class TestIsPassed:
    """Tests fuer is_passed() Methode"""

    def test_is_passed_true_when_bestanden(self, passed_buchung):
        """is_passed() ist True bei Status 'bestanden'"""
        assert passed_buchung.status == "bestanden"
        assert passed_buchung.is_passed() is True

    def test_is_passed_false_when_gebucht(self, sample_buchung):
        """is_passed() ist False bei Status 'gebucht'"""
        assert sample_buchung.status == "gebucht"
        assert sample_buchung.is_passed() is False

    def test_is_passed_false_when_anerkannt(self, recognized_buchung):
        """is_passed() ist False bei Status 'anerkannt'"""
        assert recognized_buchung.status == "anerkannt"
        assert recognized_buchung.is_passed() is False

    def test_is_passed_false_when_nicht_bestanden(self, failed_buchung):
        """is_passed() ist False bei Status 'nicht_bestanden'"""
        assert failed_buchung.status == "nicht_bestanden"
        assert failed_buchung.is_passed() is False


# ============================================================================
# IS_RECOGNIZED TESTS
# ============================================================================

class TestIsRecognized:
    """Tests fuer is_recognized() Methode"""

    def test_is_recognized_true_when_anerkannt(self, recognized_buchung):
        """is_recognized() ist True bei Status 'anerkannt'"""
        assert recognized_buchung.status == "anerkannt"
        assert recognized_buchung.is_recognized() is True

    def test_is_recognized_false_when_gebucht(self, sample_buchung):
        """is_recognized() ist False bei Status 'gebucht'"""
        assert sample_buchung.status == "gebucht"
        assert sample_buchung.is_recognized() is False

    def test_is_recognized_false_when_bestanden(self, passed_buchung):
        """is_recognized() ist False bei Status 'bestanden'"""
        assert passed_buchung.status == "bestanden"
        assert passed_buchung.is_recognized() is False

    def test_is_recognized_false_when_nicht_bestanden(self, failed_buchung):
        """is_recognized() ist False bei Status 'nicht_bestanden'"""
        assert failed_buchung.status == "nicht_bestanden"
        assert failed_buchung.is_recognized() is False


# ============================================================================
# TO_DICT TESTS
# ============================================================================

class TestToDict:
    """Tests fuer to_dict() Methode"""

    def test_to_dict_contains_all_fields(self, sample_buchung):
        """to_dict() enthaelt alle Felder"""
        d = sample_buchung.to_dict()

        assert 'id' in d
        assert 'einschreibung_id' in d
        assert 'modul_id' in d
        assert 'buchungsdatum' in d
        assert 'status' in d

    def test_to_dict_contains_computed_fields(self, sample_buchung):
        """to_dict() enthaelt berechnete Felder"""
        d = sample_buchung.to_dict()

        assert 'is_open' in d
        assert 'is_passed' in d
        assert 'is_recognized' in d

    def test_to_dict_correct_values(self, sample_buchung):
        """to_dict() enthaelt korrekte Werte"""
        d = sample_buchung.to_dict()

        assert d['id'] == 1
        assert d['einschreibung_id'] == 100
        assert d['modul_id'] == 10
        assert d['status'] == "gebucht"

    def test_to_dict_buchungsdatum_is_iso_string(self, sample_buchung):
        """buchungsdatum ist ISO-String in dict"""
        d = sample_buchung.to_dict()

        assert isinstance(d['buchungsdatum'], str)
        assert d['buchungsdatum'] == "2025-01-15"

    def test_to_dict_buchungsdatum_none(self, recognized_buchung):
        """buchungsdatum None bleibt None"""
        d = recognized_buchung.to_dict()

        assert d['buchungsdatum'] is None

    def test_to_dict_computed_values_gebucht(self, sample_buchung):
        """Berechnete Werte fuer 'gebucht'"""
        d = sample_buchung.to_dict()

        assert d['is_open'] is True
        assert d['is_passed'] is False
        assert d['is_recognized'] is False

    def test_to_dict_computed_values_bestanden(self, passed_buchung):
        """Berechnete Werte fuer 'bestanden'"""
        d = passed_buchung.to_dict()

        assert d['is_open'] is False
        assert d['is_passed'] is True
        assert d['is_recognized'] is False

    def test_to_dict_computed_values_anerkannt(self, recognized_buchung):
        """Berechnete Werte fuer 'anerkannt'"""
        d = recognized_buchung.to_dict()

        assert d['is_open'] is False
        assert d['is_passed'] is False
        assert d['is_recognized'] is True

    def test_to_dict_is_json_serializable(self, sample_buchung):
        """to_dict() Ergebnis ist JSON-serialisierbar"""
        import json

        d = sample_buchung.to_dict()

        # Sollte nicht werfen
        json_str = json.dumps(d)
        assert isinstance(json_str, str)

    def test_to_dict_returns_new_dict(self, sample_buchung):
        """to_dict() gibt neues Dictionary zurueck"""
        d1 = sample_buchung.to_dict()
        d2 = sample_buchung.to_dict()

        assert d1 == d2
        assert d1 is not d2


# ============================================================================
# FROM_ROW TESTS
# ============================================================================

class TestFromRow:
    """Tests fuer from_row() Factory Method"""

    def test_from_row_dict(self, modulbuchung_class):
        """from_row() funktioniert mit dict"""
        row = {
            'id': 1,
            'einschreibung_id': 100,
            'modul_id': 10,
            'buchungsdatum': '2025-01-15',
            'status': 'gebucht'
        }

        mb = modulbuchung_class.from_row(row)

        assert mb.id == 1
        assert mb.einschreibung_id == 100
        assert mb.modul_id == 10
        assert mb.buchungsdatum == date(2025, 1, 15)
        assert mb.status == 'gebucht'

    def test_from_row_date_object(self, modulbuchung_class):
        """from_row() funktioniert mit date-Objekt"""
        row = {
            'id': 1,
            'einschreibung_id': 100,
            'modul_id': 10,
            'buchungsdatum': date(2025, 6, 1),
            'status': 'bestanden'
        }

        mb = modulbuchung_class.from_row(row)

        assert mb.buchungsdatum == date(2025, 6, 1)

    def test_from_row_none_buchungsdatum(self, modulbuchung_class):
        """from_row() behandelt None buchungsdatum"""
        row = {
            'id': 1,
            'einschreibung_id': 100,
            'modul_id': 10,
            'buchungsdatum': None,
            'status': 'anerkannt'
        }

        mb = modulbuchung_class.from_row(row)

        assert mb.buchungsdatum is None

    def test_from_row_sqlite_row_mock(self, modulbuchung_class):
        """from_row() funktioniert mit sqlite3.Row-aehnlichem Objekt"""
        data = {
            'id': 2,
            'einschreibung_id': 200,
            'modul_id': 20,
            'buchungsdatum': '2025-03-01',
            'status': 'bestanden'
        }

        mock_row = MagicMock()
        mock_row.__getitem__ = lambda self, key: data[key]

        mb = modulbuchung_class.from_row(mock_row)

        assert mb.id == 2
        assert mb.einschreibung_id == 200
        assert mb.modul_id == 20
        assert mb.status == 'bestanden'

    def test_from_row_missing_buchungsdatum(self, modulbuchung_class):
        """from_row() behandelt fehlendes buchungsdatum (KeyError)"""
        # Simuliere einen Row ohne buchungsdatum-Key
        data = {
            'id': 1,
            'einschreibung_id': 100,
            'modul_id': 10,
            'status': 'anerkannt'
        }

        mock_row = MagicMock()

        def getitem(key):
            if key == 'buchungsdatum':
                raise KeyError('buchungsdatum')
            return data[key]

        mock_row.__getitem__ = lambda self, key: getitem(key)

        mb = modulbuchung_class.from_row(mock_row)

        assert mb.buchungsdatum is None

    def test_from_row_string_ids(self, modulbuchung_class):
        """from_row() konvertiert String-IDs zu int"""
        row = {
            'id': '123',
            'einschreibung_id': '456',
            'modul_id': '789',
            'buchungsdatum': '2025-01-15',
            'status': 'gebucht'
        }

        mb = modulbuchung_class.from_row(row)

        assert mb.id == 123
        assert isinstance(mb.id, int)
        assert mb.einschreibung_id == 456
        assert isinstance(mb.einschreibung_id, int)
        assert mb.modul_id == 789
        assert isinstance(mb.modul_id, int)


# ============================================================================
# STRING REPRESENTATION TESTS
# ============================================================================

class TestStringRepresentation:
    """Tests fuer __str__ und __repr__"""

    def test_str_contains_modul_id(self, sample_buchung):
        """__str__ enthaelt Modul-ID"""
        s = str(sample_buchung)
        assert "10" in s

    def test_str_contains_status(self, sample_buchung):
        """__str__ enthaelt Status"""
        s = str(sample_buchung)
        assert "gebucht" in s

    def test_str_format(self, sample_buchung):
        """__str__ hat korrektes Format"""
        s = str(sample_buchung)
        assert s == "Modulbuchung(Modul 10, Status: gebucht)"

    def test_str_different_status(self, passed_buchung):
        """__str__ zeigt unterschiedliche Status"""
        s = str(passed_buchung)
        assert "bestanden" in s

    def test_repr_contains_class_name(self, sample_buchung):
        """__repr__ enthaelt Klassennamen"""
        r = repr(sample_buchung)
        assert "Modulbuchung" in r

    def test_repr_contains_id(self, sample_buchung):
        """__repr__ enthaelt ID"""
        r = repr(sample_buchung)
        assert "id=1" in r

    def test_repr_contains_modul_id(self, sample_buchung):
        """__repr__ enthaelt modul_id"""
        r = repr(sample_buchung)
        assert "modul_id=10" in r

    def test_repr_contains_status(self, sample_buchung):
        """__repr__ enthaelt Status"""
        r = repr(sample_buchung)
        assert "status='gebucht'" in r


# ============================================================================
# DATACLASS TESTS
# ============================================================================

class TestDataclass:
    """Tests fuer Dataclass-Eigenschaften"""

    def test_equality_same_values(self, modulbuchung_class):
        """Gleiche Werte bedeuten Gleichheit"""
        mb1 = modulbuchung_class(
            id=1,
            einschreibung_id=100,
            modul_id=10,
            buchungsdatum=date(2025, 1, 15),
            status="gebucht"
        )
        mb2 = modulbuchung_class(
            id=1,
            einschreibung_id=100,
            modul_id=10,
            buchungsdatum=date(2025, 1, 15),
            status="gebucht"
        )

        assert mb1 == mb2

    def test_inequality_different_id(self, modulbuchung_class):
        """Unterschiedliche IDs bedeuten Ungleichheit"""
        mb1 = modulbuchung_class(
            id=1,
            einschreibung_id=100,
            modul_id=10,
            buchungsdatum=date(2025, 1, 15),
            status="gebucht"
        )
        mb2 = modulbuchung_class(
            id=2,
            einschreibung_id=100,
            modul_id=10,
            buchungsdatum=date(2025, 1, 15),
            status="gebucht"
        )

        assert mb1 != mb2

    def test_inequality_different_status(self, modulbuchung_class):
        """Unterschiedliche Status bedeuten Ungleichheit"""
        mb1 = modulbuchung_class(
            id=1,
            einschreibung_id=100,
            modul_id=10,
            buchungsdatum=date(2025, 1, 15),
            status="gebucht"
        )
        mb2 = modulbuchung_class(
            id=1,
            einschreibung_id=100,
            modul_id=10,
            buchungsdatum=date(2025, 1, 15),
            status="bestanden"
        )

        assert mb1 != mb2


# ============================================================================
# COMPOSITION RELATIONSHIP TESTS
# ============================================================================

class TestCompositionRelationship:
    """Tests fuer KOMPOSITION zu Einschreibung"""

    def test_einschreibung_id_required(self, modulbuchung_class):
        """einschreibung_id ist Teil der Buchung"""
        mb = modulbuchung_class(
            id=1,
            einschreibung_id=100,
            modul_id=10,
            buchungsdatum=date(2025, 1, 15),
            status="gebucht"
        )

        assert mb.einschreibung_id == 100

    def test_multiple_buchungen_same_einschreibung(self, modulbuchung_class):
        """Mehrere Buchungen koennen zur gleichen Einschreibung gehoeren"""
        mb1 = modulbuchung_class(
            id=1,
            einschreibung_id=100,
            modul_id=10,
            buchungsdatum=date(2025, 1, 15),
            status="gebucht"
        )
        mb2 = modulbuchung_class(
            id=2,
            einschreibung_id=100,
            modul_id=11,
            buchungsdatum=date(2025, 1, 15),
            status="bestanden"
        )

        assert mb1.einschreibung_id == mb2.einschreibung_id


# ============================================================================
# EDGE CASES
# ============================================================================

class TestEdgeCases:
    """Tests fuer Randfaelle"""

    def test_large_ids(self, modulbuchung_class):
        """Grosse IDs werden korrekt behandelt"""
        mb = modulbuchung_class(
            id=999999999,
            einschreibung_id=888888888,
            modul_id=777777777,
            buchungsdatum=date(2025, 1, 15),
            status="gebucht"
        )

        assert mb.id == 999999999
        assert mb.einschreibung_id == 888888888
        assert mb.modul_id == 777777777

    def test_old_date(self, modulbuchung_class):
        """Altes Datum wird korrekt behandelt"""
        mb = modulbuchung_class(
            id=1,
            einschreibung_id=100,
            modul_id=10,
            buchungsdatum=date(2000, 1, 1),
            status="bestanden"
        )

        assert mb.buchungsdatum == date(2000, 1, 1)

    def test_future_date(self, modulbuchung_class):
        """Zukuenftiges Datum wird korrekt behandelt"""
        mb = modulbuchung_class(
            id=1,
            einschreibung_id=100,
            modul_id=10,
            buchungsdatum=date(2099, 12, 31),
            status="gebucht"
        )

        assert mb.buchungsdatum == date(2099, 12, 31)

    def test_status_case_sensitive(self, modulbuchung_class):
        """Status ist case-sensitive"""
        mb1 = modulbuchung_class(
            id=1,
            einschreibung_id=100,
            modul_id=10,
            buchungsdatum=date(2025, 1, 15),
            status="gebucht"
        )

        mb2 = modulbuchung_class(
            id=2,
            einschreibung_id=100,
            modul_id=10,
            buchungsdatum=date(2025, 1, 15),
            status="Gebucht"  # Grossbuchstabe
        )

        # Bei case-sensitive Status waere 'Gebucht' nicht als 'gebucht' erkannt
        assert mb1.is_open() is True
        assert mb2.is_open() is False  # 'Gebucht' != 'gebucht'


# ============================================================================
# STATUS TRANSITIONS (Informational)
# ============================================================================

class TestStatusTransitions:
    """Tests fuer Status-Uebergaenge (informativ)"""

    def test_all_status_values(self, modulbuchung_class):
        """Alle Status-Werte werden akzeptiert"""
        statuses = ["gebucht", "bestanden", "anerkannt", "nicht_bestanden"]

        for status in statuses:
            mb = modulbuchung_class(
                id=1,
                einschreibung_id=100,
                modul_id=10,
                buchungsdatum=date(2025, 1, 15),
                status=status
            )
            assert mb.status == status

    def test_status_methods_exclusive(self, modulbuchung_class):
        """Status-Methoden sind exklusiv (nur eine kann True sein)"""
        statuses_and_methods = [
            ("gebucht", "is_open"),
            ("bestanden", "is_passed"),
            ("anerkannt", "is_recognized"),
        ]

        for status, expected_method in statuses_and_methods:
            mb = modulbuchung_class(
                id=1,
                einschreibung_id=100,
                modul_id=10,
                buchungsdatum=date(2025, 1, 15),
                status=status
            )

            # Nur die erwartete Methode sollte True sein
            results = {
                "is_open": mb.is_open(),
                "is_passed": mb.is_passed(),
                "is_recognized": mb.is_recognized()
            }

            assert results[expected_method] is True
            for method, result in results.items():
                if method != expected_method:
                    assert result is False, f"{method} should be False for status '{status}'"


# ============================================================================
# TYPE CHECKING TESTS
# ============================================================================

class TestTypeChecking:
    """Tests fuer Typenpruefung"""

    def test_id_is_int(self, sample_buchung):
        """id ist int"""
        assert isinstance(sample_buchung.id, int)

    def test_einschreibung_id_is_int(self, sample_buchung):
        """einschreibung_id ist int"""
        assert isinstance(sample_buchung.einschreibung_id, int)

    def test_modul_id_is_int(self, sample_buchung):
        """modul_id ist int"""
        assert isinstance(sample_buchung.modul_id, int)

    def test_buchungsdatum_is_date_or_none(self, sample_buchung, recognized_buchung):
        """buchungsdatum ist date oder None"""
        assert isinstance(sample_buchung.buchungsdatum, date)
        assert recognized_buchung.buchungsdatum is None

    def test_status_is_str(self, sample_buchung):
        """status ist str"""
        assert isinstance(sample_buchung.status, str)

    def test_is_open_returns_bool(self, sample_buchung):
        """is_open() gibt bool zurueck"""
        assert isinstance(sample_buchung.is_open(), bool)

    def test_is_passed_returns_bool(self, sample_buchung):
        """is_passed() gibt bool zurueck"""
        assert isinstance(sample_buchung.is_passed(), bool)

    def test_is_recognized_returns_bool(self, sample_buchung):
        """is_recognized() gibt bool zurueck"""
        assert isinstance(sample_buchung.is_recognized(), bool)

    def test_to_dict_returns_dict(self, sample_buchung):
        """to_dict() gibt dict zurueck"""
        assert isinstance(sample_buchung.to_dict(), dict)