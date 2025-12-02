# tests/unit/test_pruefungsanmeldung.py
"""
Unit Tests fuer Pruefungsanmeldung Domain Model (models/pruefungsanmeldung.py)

Testet die Pruefungsanmeldung-Klasse:
- Initialisierung und Validierung
- Datum-Konvertierung
- Status-Methoden (ist_aktiv, ist_storniert, ist_absolviert, kann_storniert_werden)
- Serialisierung (to_dict)
- Factory Method (from_row)
- String-Repraesentation
"""
from __future__ import annotations

import pytest
from datetime import datetime
from unittest.mock import MagicMock

# Mark this whole module as unit tests
pytestmark = pytest.mark.unit


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def pruefungsanmeldung_class():
    """Importiert Pruefungsanmeldung-Klasse"""
    try:
        from models.pruefungsanmeldung import Pruefungsanmeldung
        return Pruefungsanmeldung
    except ImportError:
        from models import Pruefungsanmeldung
        return Pruefungsanmeldung


@pytest.fixture
def sample_anmeldung(pruefungsanmeldung_class):
    """Standard-Pruefungsanmeldung (angemeldet) fuer Tests"""
    return pruefungsanmeldung_class(
        id=1,
        modulbuchung_id=100,
        pruefungstermin_id=10,
        status="angemeldet",
        angemeldet_am=datetime(2025, 6, 1, 10, 0, 0)
    )


@pytest.fixture
def stornierte_anmeldung(pruefungsanmeldung_class):
    """Stornierte Pruefungsanmeldung fuer Tests"""
    return pruefungsanmeldung_class(
        id=2,
        modulbuchung_id=101,
        pruefungstermin_id=11,
        status="storniert",
        angemeldet_am=datetime(2025, 5, 15, 9, 30, 0)
    )


@pytest.fixture
def absolvierte_anmeldung(pruefungsanmeldung_class):
    """Absolvierte Pruefungsanmeldung fuer Tests"""
    return pruefungsanmeldung_class(
        id=3,
        modulbuchung_id=102,
        pruefungstermin_id=12,
        status="absolviert",
        angemeldet_am=datetime(2025, 4, 1, 8, 0, 0)
    )


# ============================================================================
# INITIALIZATION TESTS
# ============================================================================

class TestPruefungsanmeldungInit:
    """Tests fuer Pruefungsanmeldung-Initialisierung"""

    def test_init_with_all_fields(self, pruefungsanmeldung_class):
        """Initialisierung mit allen Feldern"""
        anmeldung = pruefungsanmeldung_class(
            id=1,
            modulbuchung_id=100,
            pruefungstermin_id=10,
            status="angemeldet",
            angemeldet_am=datetime(2025, 6, 1, 10, 0, 0)
        )

        assert anmeldung.id == 1
        assert anmeldung.modulbuchung_id == 100
        assert anmeldung.pruefungstermin_id == 10
        assert anmeldung.status == "angemeldet"
        assert anmeldung.angemeldet_am == datetime(2025, 6, 1, 10, 0, 0)

    def test_init_default_status(self, pruefungsanmeldung_class):
        """Standard-Status ist 'angemeldet'"""
        anmeldung = pruefungsanmeldung_class(
            id=1,
            modulbuchung_id=100,
            pruefungstermin_id=10
        )

        assert anmeldung.status == "angemeldet"

    def test_init_auto_angemeldet_am(self, pruefungsanmeldung_class):
        """angemeldet_am wird automatisch gesetzt wenn None"""
        before = datetime.now()

        anmeldung = pruefungsanmeldung_class(
            id=1,
            modulbuchung_id=100,
            pruefungstermin_id=10,
            angemeldet_am=None
        )

        after = datetime.now()

        assert anmeldung.angemeldet_am is not None
        assert before <= anmeldung.angemeldet_am <= after

    def test_init_status_angemeldet(self, pruefungsanmeldung_class):
        """Initialisierung mit Status 'angemeldet'"""
        anmeldung = pruefungsanmeldung_class(
            id=1,
            modulbuchung_id=100,
            pruefungstermin_id=10,
            status="angemeldet"
        )

        assert anmeldung.status == "angemeldet"

    def test_init_status_storniert(self, pruefungsanmeldung_class):
        """Initialisierung mit Status 'storniert'"""
        anmeldung = pruefungsanmeldung_class(
            id=1,
            modulbuchung_id=100,
            pruefungstermin_id=10,
            status="storniert"
        )

        assert anmeldung.status == "storniert"

    def test_init_status_absolviert(self, pruefungsanmeldung_class):
        """Initialisierung mit Status 'absolviert'"""
        anmeldung = pruefungsanmeldung_class(
            id=1,
            modulbuchung_id=100,
            pruefungstermin_id=10,
            status="absolviert"
        )

        assert anmeldung.status == "absolviert"


# ============================================================================
# DATE CONVERSION TESTS
# ============================================================================

class TestDateConversion:
    """Tests fuer Datum-Konvertierung in __post_init__"""

    def test_string_datetime_converted(self, pruefungsanmeldung_class):
        """ISO-String wird zu datetime konvertiert"""
        anmeldung = pruefungsanmeldung_class(
            id=1,
            modulbuchung_id=100,
            pruefungstermin_id=10,
            angemeldet_am="2025-06-01T10:30:00"  # String
        )

        assert isinstance(anmeldung.angemeldet_am, datetime)
        assert anmeldung.angemeldet_am == datetime(2025, 6, 1, 10, 30, 0)

    def test_datetime_object_unchanged(self, pruefungsanmeldung_class):
        """datetime-Objekt bleibt unveraendert"""
        original_dt = datetime(2025, 6, 1, 10, 0, 0)
        anmeldung = pruefungsanmeldung_class(
            id=1,
            modulbuchung_id=100,
            pruefungstermin_id=10,
            angemeldet_am=original_dt
        )

        assert anmeldung.angemeldet_am == original_dt

    def test_none_gets_current_datetime(self, pruefungsanmeldung_class):
        """None wird durch aktuelles Datum ersetzt"""
        before = datetime.now()

        anmeldung = pruefungsanmeldung_class(
            id=1,
            modulbuchung_id=100,
            pruefungstermin_id=10,
            angemeldet_am=None
        )

        after = datetime.now()

        assert anmeldung.angemeldet_am is not None
        assert before <= anmeldung.angemeldet_am <= after

    def test_various_iso_formats(self, pruefungsanmeldung_class):
        """Verschiedene ISO-Datetime-Formate"""
        formats = [
            ("2025-06-01T10:30:00", datetime(2025, 6, 1, 10, 30, 0)),
            ("2025-12-31T23:59:59", datetime(2025, 12, 31, 23, 59, 59)),
            ("2025-01-01T00:00:00", datetime(2025, 1, 1, 0, 0, 0)),
        ]

        for date_str, expected in formats:
            anmeldung = pruefungsanmeldung_class(
                id=1,
                modulbuchung_id=100,
                pruefungstermin_id=10,
                angemeldet_am=date_str
            )
            assert anmeldung.angemeldet_am == expected


# ============================================================================
# IST_AKTIV TESTS
# ============================================================================

class TestIstAktiv:
    """Tests fuer ist_aktiv() Methode"""

    def test_ist_aktiv_true_when_angemeldet(self, sample_anmeldung):
        """ist_aktiv() ist True bei Status 'angemeldet'"""
        assert sample_anmeldung.status == "angemeldet"
        assert sample_anmeldung.ist_aktiv() is True

    def test_ist_aktiv_false_when_storniert(self, stornierte_anmeldung):
        """ist_aktiv() ist False bei Status 'storniert'"""
        assert stornierte_anmeldung.status == "storniert"
        assert stornierte_anmeldung.ist_aktiv() is False

    def test_ist_aktiv_false_when_absolviert(self, absolvierte_anmeldung):
        """ist_aktiv() ist False bei Status 'absolviert'"""
        assert absolvierte_anmeldung.status == "absolviert"
        assert absolvierte_anmeldung.ist_aktiv() is False


# ============================================================================
# IST_STORNIERT TESTS
# ============================================================================

class TestIstStorniert:
    """Tests fuer ist_storniert() Methode"""

    def test_ist_storniert_true_when_storniert(self, stornierte_anmeldung):
        """ist_storniert() ist True bei Status 'storniert'"""
        assert stornierte_anmeldung.status == "storniert"
        assert stornierte_anmeldung.ist_storniert() is True

    def test_ist_storniert_false_when_angemeldet(self, sample_anmeldung):
        """ist_storniert() ist False bei Status 'angemeldet'"""
        assert sample_anmeldung.status == "angemeldet"
        assert sample_anmeldung.ist_storniert() is False

    def test_ist_storniert_false_when_absolviert(self, absolvierte_anmeldung):
        """ist_storniert() ist False bei Status 'absolviert'"""
        assert absolvierte_anmeldung.status == "absolviert"
        assert absolvierte_anmeldung.ist_storniert() is False


# ============================================================================
# IST_ABSOLVIERT TESTS
# ============================================================================

class TestIstAbsolviert:
    """Tests fuer ist_absolviert() Methode"""

    def test_ist_absolviert_true_when_absolviert(self, absolvierte_anmeldung):
        """ist_absolviert() ist True bei Status 'absolviert'"""
        assert absolvierte_anmeldung.status == "absolviert"
        assert absolvierte_anmeldung.ist_absolviert() is True

    def test_ist_absolviert_false_when_angemeldet(self, sample_anmeldung):
        """ist_absolviert() ist False bei Status 'angemeldet'"""
        assert sample_anmeldung.status == "angemeldet"
        assert sample_anmeldung.ist_absolviert() is False

    def test_ist_absolviert_false_when_storniert(self, stornierte_anmeldung):
        """ist_absolviert() ist False bei Status 'storniert'"""
        assert stornierte_anmeldung.status == "storniert"
        assert stornierte_anmeldung.ist_absolviert() is False


# ============================================================================
# KANN_STORNIERT_WERDEN TESTS
# ============================================================================

class TestKannStorniertWerden:
    """Tests fuer kann_storniert_werden() Methode"""

    def test_kann_storniert_werden_true_when_angemeldet(self, sample_anmeldung):
        """kann_storniert_werden() ist True bei Status 'angemeldet'"""
        assert sample_anmeldung.ist_aktiv() is True
        assert sample_anmeldung.kann_storniert_werden() is True

    def test_kann_storniert_werden_false_when_storniert(self, stornierte_anmeldung):
        """kann_storniert_werden() ist False bei Status 'storniert'"""
        assert stornierte_anmeldung.ist_aktiv() is False
        assert stornierte_anmeldung.kann_storniert_werden() is False

    def test_kann_storniert_werden_false_when_absolviert(self, absolvierte_anmeldung):
        """kann_storniert_werden() ist False bei Status 'absolviert'"""
        assert absolvierte_anmeldung.ist_aktiv() is False
        assert absolvierte_anmeldung.kann_storniert_werden() is False


# ============================================================================
# TO_DICT TESTS
# ============================================================================

class TestToDict:
    """Tests fuer to_dict() Methode"""

    def test_to_dict_contains_all_fields(self, sample_anmeldung):
        """to_dict() enthaelt alle Felder"""
        d = sample_anmeldung.to_dict()

        assert 'id' in d
        assert 'modulbuchung_id' in d
        assert 'pruefungstermin_id' in d
        assert 'status' in d
        assert 'angemeldet_am' in d

    def test_to_dict_contains_computed_fields(self, sample_anmeldung):
        """to_dict() enthaelt berechnete Felder"""
        d = sample_anmeldung.to_dict()

        assert 'ist_aktiv' in d
        assert 'ist_storniert' in d
        assert 'ist_absolviert' in d
        assert 'kann_storniert_werden' in d

    def test_to_dict_correct_values(self, sample_anmeldung):
        """to_dict() enthaelt korrekte Werte"""
        d = sample_anmeldung.to_dict()

        assert d['id'] == 1
        assert d['modulbuchung_id'] == 100
        assert d['pruefungstermin_id'] == 10
        assert d['status'] == "angemeldet"

    def test_to_dict_angemeldet_am_is_iso_string(self, sample_anmeldung):
        """angemeldet_am ist ISO-String in dict"""
        d = sample_anmeldung.to_dict()

        assert isinstance(d['angemeldet_am'], str)
        assert d['angemeldet_am'] == "2025-06-01T10:00:00"

    def test_to_dict_computed_values_angemeldet(self, sample_anmeldung):
        """Berechnete Werte fuer 'angemeldet'"""
        d = sample_anmeldung.to_dict()

        assert d['ist_aktiv'] is True
        assert d['ist_storniert'] is False
        assert d['ist_absolviert'] is False
        assert d['kann_storniert_werden'] is True

    def test_to_dict_computed_values_storniert(self, stornierte_anmeldung):
        """Berechnete Werte fuer 'storniert'"""
        d = stornierte_anmeldung.to_dict()

        assert d['ist_aktiv'] is False
        assert d['ist_storniert'] is True
        assert d['ist_absolviert'] is False
        assert d['kann_storniert_werden'] is False

    def test_to_dict_computed_values_absolviert(self, absolvierte_anmeldung):
        """Berechnete Werte fuer 'absolviert'"""
        d = absolvierte_anmeldung.to_dict()

        assert d['ist_aktiv'] is False
        assert d['ist_storniert'] is False
        assert d['ist_absolviert'] is True
        assert d['kann_storniert_werden'] is False

    def test_to_dict_is_json_serializable(self, sample_anmeldung):
        """to_dict() Ergebnis ist JSON-serialisierbar"""
        import json

        d = sample_anmeldung.to_dict()

        # Sollte nicht werfen
        json_str = json.dumps(d)
        assert isinstance(json_str, str)

    def test_to_dict_returns_new_dict(self, sample_anmeldung):
        """to_dict() gibt neues Dictionary zurueck"""
        d1 = sample_anmeldung.to_dict()
        d2 = sample_anmeldung.to_dict()

        assert d1 == d2
        assert d1 is not d2


# ============================================================================
# FROM_ROW TESTS
# ============================================================================

class TestFromRow:
    """Tests fuer from_row() Factory Method"""

    def test_from_row_dict(self, pruefungsanmeldung_class):
        """from_row() funktioniert mit dict"""
        row = {
            'id': 1,
            'modulbuchung_id': 100,
            'pruefungstermin_id': 10,
            'status': 'angemeldet',
            'angemeldet_am': '2025-06-01T10:30:00'
        }

        anmeldung = pruefungsanmeldung_class.from_row(row)

        assert anmeldung.id == 1
        assert anmeldung.modulbuchung_id == 100
        assert anmeldung.pruefungstermin_id == 10
        assert anmeldung.status == 'angemeldet'
        assert anmeldung.angemeldet_am == datetime(2025, 6, 1, 10, 30, 0)

    def test_from_row_datetime_object(self, pruefungsanmeldung_class):
        """from_row() funktioniert mit datetime-Objekt"""
        row = {
            'id': 1,
            'modulbuchung_id': 100,
            'pruefungstermin_id': 10,
            'status': 'angemeldet',
            'angemeldet_am': datetime(2025, 6, 1, 10, 30, 0)
        }

        anmeldung = pruefungsanmeldung_class.from_row(row)

        assert anmeldung.angemeldet_am == datetime(2025, 6, 1, 10, 30, 0)

    def test_from_row_missing_status(self, pruefungsanmeldung_class):
        """from_row() behandelt fehlenden status (default: 'angemeldet')"""
        data = {
            'id': 1,
            'modulbuchung_id': 100,
            'pruefungstermin_id': 10,
            'angemeldet_am': '2025-06-01T10:30:00'
        }

        mock_row = MagicMock()

        def getitem(key):
            if key == 'status':
                raise KeyError('status')
            return data[key]

        mock_row.__getitem__ = lambda self, key: getitem(key)

        anmeldung = pruefungsanmeldung_class.from_row(mock_row)

        assert anmeldung.status == 'angemeldet'

    def test_from_row_missing_angemeldet_am(self, pruefungsanmeldung_class):
        """from_row() behandelt fehlendes angemeldet_am"""
        data = {
            'id': 1,
            'modulbuchung_id': 100,
            'pruefungstermin_id': 10,
            'status': 'angemeldet'
        }

        mock_row = MagicMock()

        def getitem(key):
            if key == 'angemeldet_am':
                raise KeyError('angemeldet_am')
            return data[key]

        mock_row.__getitem__ = lambda self, key: getitem(key)

        anmeldung = pruefungsanmeldung_class.from_row(mock_row)

        # angemeldet_am wird in __post_init__ auf datetime.now() gesetzt
        assert anmeldung.angemeldet_am is not None

    def test_from_row_none_angemeldet_am(self, pruefungsanmeldung_class):
        """from_row() behandelt None angemeldet_am"""
        row = {
            'id': 1,
            'modulbuchung_id': 100,
            'pruefungstermin_id': 10,
            'status': 'angemeldet',
            'angemeldet_am': None
        }

        anmeldung = pruefungsanmeldung_class.from_row(row)

        # angemeldet_am wird in __post_init__ auf datetime.now() gesetzt
        assert anmeldung.angemeldet_am is not None

    def test_from_row_sqlite_row_mock(self, pruefungsanmeldung_class):
        """from_row() funktioniert mit sqlite3.Row-aehnlichem Objekt"""
        data = {
            'id': 2,
            'modulbuchung_id': 200,
            'pruefungstermin_id': 20,
            'status': 'storniert',
            'angemeldet_am': '2025-05-15T09:30:00'
        }

        mock_row = MagicMock()
        mock_row.__getitem__ = lambda self, key: data[key]

        anmeldung = pruefungsanmeldung_class.from_row(mock_row)

        assert anmeldung.id == 2
        assert anmeldung.modulbuchung_id == 200
        assert anmeldung.status == 'storniert'

    def test_from_row_string_ids(self, pruefungsanmeldung_class):
        """from_row() konvertiert String-IDs zu int"""
        row = {
            'id': '123',
            'modulbuchung_id': '456',
            'pruefungstermin_id': '789',
            'status': 'angemeldet',
            'angemeldet_am': '2025-06-01T10:30:00'
        }

        anmeldung = pruefungsanmeldung_class.from_row(row)

        assert anmeldung.id == 123
        assert isinstance(anmeldung.id, int)
        assert anmeldung.modulbuchung_id == 456
        assert isinstance(anmeldung.modulbuchung_id, int)
        assert anmeldung.pruefungstermin_id == 789
        assert isinstance(anmeldung.pruefungstermin_id, int)


# ============================================================================
# STRING REPRESENTATION TESTS
# ============================================================================

class TestStringRepresentation:
    """Tests fuer __str__ und __repr__"""

    def test_str_contains_status(self, sample_anmeldung):
        """__str__ enthaelt Status"""
        s = str(sample_anmeldung)
        assert "angemeldet" in s

    def test_str_contains_modulbuchung_id(self, sample_anmeldung):
        """__str__ enthaelt modulbuchung_id"""
        s = str(sample_anmeldung)
        assert "100" in s

    def test_str_contains_termin_id(self, sample_anmeldung):
        """__str__ enthaelt pruefungstermin_id"""
        s = str(sample_anmeldung)
        assert "10" in s

    def test_str_different_status(self, stornierte_anmeldung):
        """__str__ zeigt unterschiedliche Status"""
        s = str(stornierte_anmeldung)
        assert "storniert" in s

    def test_repr_contains_class_name(self, sample_anmeldung):
        """__repr__ enthaelt Klassennamen"""
        r = repr(sample_anmeldung)
        assert "Pruefungsanmeldung" in r

    def test_repr_contains_id(self, sample_anmeldung):
        """__repr__ enthaelt ID"""
        r = repr(sample_anmeldung)
        assert "id=1" in r

    def test_repr_contains_modulbuchung_id(self, sample_anmeldung):
        """__repr__ enthaelt modulbuchung_id"""
        r = repr(sample_anmeldung)
        assert "modulbuchung_id=100" in r

    def test_repr_contains_termin_id(self, sample_anmeldung):
        """__repr__ enthaelt termin_id"""
        r = repr(sample_anmeldung)
        assert "termin_id=10" in r

    def test_repr_contains_status(self, sample_anmeldung):
        """__repr__ enthaelt Status"""
        r = repr(sample_anmeldung)
        assert "status=angemeldet" in r


# ============================================================================
# DATACLASS TESTS
# ============================================================================

class TestDataclass:
    """Tests fuer Dataclass-Eigenschaften"""

    def test_equality_same_values(self, pruefungsanmeldung_class):
        """Gleiche Werte bedeuten Gleichheit"""
        dt = datetime(2025, 6, 1, 10, 0, 0)

        a1 = pruefungsanmeldung_class(
            id=1,
            modulbuchung_id=100,
            pruefungstermin_id=10,
            status="angemeldet",
            angemeldet_am=dt
        )
        a2 = pruefungsanmeldung_class(
            id=1,
            modulbuchung_id=100,
            pruefungstermin_id=10,
            status="angemeldet",
            angemeldet_am=dt
        )

        assert a1 == a2

    def test_inequality_different_id(self, pruefungsanmeldung_class):
        """Unterschiedliche IDs bedeuten Ungleichheit"""
        dt = datetime(2025, 6, 1, 10, 0, 0)

        a1 = pruefungsanmeldung_class(
            id=1,
            modulbuchung_id=100,
            pruefungstermin_id=10,
            status="angemeldet",
            angemeldet_am=dt
        )
        a2 = pruefungsanmeldung_class(
            id=2,
            modulbuchung_id=100,
            pruefungstermin_id=10,
            status="angemeldet",
            angemeldet_am=dt
        )

        assert a1 != a2

    def test_inequality_different_status(self, pruefungsanmeldung_class):
        """Unterschiedliche Status bedeuten Ungleichheit"""
        dt = datetime(2025, 6, 1, 10, 0, 0)

        a1 = pruefungsanmeldung_class(
            id=1,
            modulbuchung_id=100,
            pruefungstermin_id=10,
            status="angemeldet",
            angemeldet_am=dt
        )
        a2 = pruefungsanmeldung_class(
            id=1,
            modulbuchung_id=100,
            pruefungstermin_id=10,
            status="storniert",
            angemeldet_am=dt
        )

        assert a1 != a2


# ============================================================================
# STATUS TRANSITIONS (Informational)
# ============================================================================

class TestStatusTransitions:
    """Tests fuer Status-Werte"""

    def test_all_status_values(self, pruefungsanmeldung_class):
        """Alle Status-Werte werden akzeptiert"""
        statuses = ["angemeldet", "storniert", "absolviert"]

        for status in statuses:
            anmeldung = pruefungsanmeldung_class(
                id=1,
                modulbuchung_id=100,
                pruefungstermin_id=10,
                status=status
            )
            assert anmeldung.status == status

    def test_status_methods_exclusive(self, pruefungsanmeldung_class):
        """Status-Methoden sind exklusiv (nur eine kann True sein)"""
        statuses_and_methods = [
            ("angemeldet", "ist_aktiv"),
            ("storniert", "ist_storniert"),
            ("absolviert", "ist_absolviert"),
        ]

        for status, expected_method in statuses_and_methods:
            anmeldung = pruefungsanmeldung_class(
                id=1,
                modulbuchung_id=100,
                pruefungstermin_id=10,
                status=status
            )

            # Nur die erwartete Methode sollte True sein
            results = {
                "ist_aktiv": anmeldung.ist_aktiv(),
                "ist_storniert": anmeldung.ist_storniert(),
                "ist_absolviert": anmeldung.ist_absolviert()
            }

            assert results[expected_method] is True
            for method, result in results.items():
                if method != expected_method:
                    assert result is False, f"{method} should be False for status '{status}'"


# ============================================================================
# EDGE CASES
# ============================================================================

class TestEdgeCases:
    """Tests fuer Randfaelle"""

    def test_large_ids(self, pruefungsanmeldung_class):
        """Grosse IDs werden korrekt behandelt"""
        anmeldung = pruefungsanmeldung_class(
            id=999999999,
            modulbuchung_id=888888888,
            pruefungstermin_id=777777777,
            status="angemeldet"
        )

        assert anmeldung.id == 999999999
        assert anmeldung.modulbuchung_id == 888888888
        assert anmeldung.pruefungstermin_id == 777777777

    def test_old_datetime(self, pruefungsanmeldung_class):
        """Altes Datum wird korrekt behandelt"""
        old_dt = datetime(2020, 1, 1, 0, 0, 0)

        anmeldung = pruefungsanmeldung_class(
            id=1,
            modulbuchung_id=100,
            pruefungstermin_id=10,
            angemeldet_am=old_dt
        )

        assert anmeldung.angemeldet_am == old_dt

    def test_future_datetime(self, pruefungsanmeldung_class):
        """Zukuenftiges Datum wird korrekt behandelt"""
        future_dt = datetime(2099, 12, 31, 23, 59, 59)

        anmeldung = pruefungsanmeldung_class(
            id=1,
            modulbuchung_id=100,
            pruefungstermin_id=10,
            angemeldet_am=future_dt
        )

        assert anmeldung.angemeldet_am == future_dt

    def test_status_case_sensitive(self, pruefungsanmeldung_class):
        """Status ist case-sensitive"""
        a1 = pruefungsanmeldung_class(
            id=1,
            modulbuchung_id=100,
            pruefungstermin_id=10,
            status="angemeldet"
        )

        a2 = pruefungsanmeldung_class(
            id=2,
            modulbuchung_id=100,
            pruefungstermin_id=10,
            status="Angemeldet"  # Grossbuchstabe
        )

        # Bei case-sensitive Status waere 'Angemeldet' nicht als 'angemeldet' erkannt
        assert a1.ist_aktiv() is True
        assert a2.ist_aktiv() is False  # 'Angemeldet' != 'angemeldet'


# ============================================================================
# TYPE CHECKING TESTS
# ============================================================================

class TestTypeChecking:
    """Tests fuer Typenpruefung"""

    def test_id_is_int(self, sample_anmeldung):
        """id ist int"""
        assert isinstance(sample_anmeldung.id, int)

    def test_modulbuchung_id_is_int(self, sample_anmeldung):
        """modulbuchung_id ist int"""
        assert isinstance(sample_anmeldung.modulbuchung_id, int)

    def test_pruefungstermin_id_is_int(self, sample_anmeldung):
        """pruefungstermin_id ist int"""
        assert isinstance(sample_anmeldung.pruefungstermin_id, int)

    def test_status_is_str(self, sample_anmeldung):
        """status ist str"""
        assert isinstance(sample_anmeldung.status, str)

    def test_angemeldet_am_is_datetime(self, sample_anmeldung):
        """angemeldet_am ist datetime"""
        assert isinstance(sample_anmeldung.angemeldet_am, datetime)

    def test_ist_aktiv_returns_bool(self, sample_anmeldung):
        """ist_aktiv() gibt bool zurueck"""
        assert isinstance(sample_anmeldung.ist_aktiv(), bool)

    def test_ist_storniert_returns_bool(self, sample_anmeldung):
        """ist_storniert() gibt bool zurueck"""
        assert isinstance(sample_anmeldung.ist_storniert(), bool)

    def test_ist_absolviert_returns_bool(self, sample_anmeldung):
        """ist_absolviert() gibt bool zurueck"""
        assert isinstance(sample_anmeldung.ist_absolviert(), bool)

    def test_kann_storniert_werden_returns_bool(self, sample_anmeldung):
        """kann_storniert_werden() gibt bool zurueck"""
        assert isinstance(sample_anmeldung.kann_storniert_werden(), bool)

    def test_to_dict_returns_dict(self, sample_anmeldung):
        """to_dict() gibt dict zurueck"""
        assert isinstance(sample_anmeldung.to_dict(), dict)