# tests/unit/test_pruefungstermin.py
"""
Unit Tests fuer Pruefungstermin Domain Model (models/pruefungstermin.py)

Testet die Pruefungstermin-Klasse:
- Initialisierung und Validierung
- Typ-Konvertierung (date, time, datetime)
- Pruefungsart-Methoden (ist_online_pruefung, ist_praesenz_pruefung, ist_projekt)
- Status-Methoden (hat_zeitfenster, hat_kapazitaet, ist_anmeldeschluss_vorbei, ist_in_zukunft)
- Serialisierung (to_dict)
- Factory Method (from_row)
- String-Repraesentation
"""
from __future__ import annotations

import pytest
from datetime import date, time, datetime, timedelta
from unittest.mock import MagicMock

# Mark this whole module as unit tests
pytestmark = pytest.mark.unit


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def pruefungstermin_class():
    """Importiert Pruefungstermin-Klasse"""
    try:
        from models.pruefungstermin import Pruefungstermin
        return Pruefungstermin
    except ImportError:
        from models import Pruefungstermin
        return Pruefungstermin


@pytest.fixture
def online_termin(pruefungstermin_class):
    """Online-Pruefungstermin fuer Tests"""
    return pruefungstermin_class(
        id=1,
        modul_id=10,
        datum=date.today() + timedelta(days=30),
        beginn=time(10, 0),
        ende=time(12, 0),
        art="online",
        ort=None,
        anmeldeschluss=datetime.now() + timedelta(days=14),
        kapazitaet=None,
        beschreibung="Online-Klausur"
    )


@pytest.fixture
def praesenz_termin(pruefungstermin_class):
    """Praesenz-Pruefungstermin fuer Tests"""
    return pruefungstermin_class(
        id=2,
        modul_id=11,
        datum=date.today() + timedelta(days=45),
        beginn=time(9, 0),
        ende=time(11, 30),
        art="praesenz",
        ort="Muenchen, Raum A101",
        anmeldeschluss=datetime.now() + timedelta(days=21),
        kapazitaet=50,
        beschreibung="Praesenzklausur"
    )


@pytest.fixture
def projekt_termin(pruefungstermin_class):
    """Projekt-Pruefungstermin fuer Tests"""
    return pruefungstermin_class(
        id=3,
        modul_id=12,
        datum=date.today() + timedelta(days=60),
        beginn=None,
        ende=None,
        art="projekt",
        ort=None,
        anmeldeschluss=None,
        kapazitaet=None,
        beschreibung="Projektarbeit"
    )


@pytest.fixture
def workbook_termin(pruefungstermin_class):
    """Workbook-Pruefungstermin fuer Tests"""
    return pruefungstermin_class(
        id=4,
        modul_id=13,
        datum=date.today() + timedelta(days=90),
        beginn=None,
        ende=None,
        art="workbook",
        ort=None,
        anmeldeschluss=None,
        kapazitaet=None,
        beschreibung="Advanced Workbook"
    )


@pytest.fixture
def vergangener_termin(pruefungstermin_class):
    """Vergangener Pruefungstermin fuer Tests"""
    return pruefungstermin_class(
        id=5,
        modul_id=14,
        datum=date.today() - timedelta(days=30),
        beginn=time(10, 0),
        ende=time(12, 0),
        art="online",
        ort=None,
        anmeldeschluss=datetime.now() - timedelta(days=44),
        kapazitaet=None,
        beschreibung="Vergangene Pruefung"
    )


# ============================================================================
# INITIALIZATION TESTS
# ============================================================================

class TestPruefungsterminInit:
    """Tests fuer Pruefungstermin-Initialisierung"""

    def test_init_with_all_fields(self, pruefungstermin_class):
        """Initialisierung mit allen Feldern"""
        termin = pruefungstermin_class(
            id=1,
            modul_id=10,
            datum=date(2025, 7, 15),
            beginn=time(10, 0),
            ende=time(12, 0),
            art="online",
            ort="Online",
            anmeldeschluss=datetime(2025, 7, 1, 23, 59),
            kapazitaet=100,
            beschreibung="Testbeschreibung"
        )

        assert termin.id == 1
        assert termin.modul_id == 10
        assert termin.datum == date(2025, 7, 15)
        assert termin.beginn == time(10, 0)
        assert termin.ende == time(12, 0)
        assert termin.art == "online"
        assert termin.ort == "Online"
        assert termin.anmeldeschluss == datetime(2025, 7, 1, 23, 59)
        assert termin.kapazitaet == 100
        assert termin.beschreibung == "Testbeschreibung"

    def test_init_default_values(self, pruefungstermin_class):
        """Initialisierung mit Default-Werten"""
        termin = pruefungstermin_class(
            id=1,
            modul_id=10,
            datum=date(2025, 7, 15)
        )

        assert termin.beginn is None
        assert termin.ende is None
        assert termin.art == "online"
        assert termin.ort is None
        assert termin.anmeldeschluss is None
        assert termin.kapazitaet is None
        assert termin.beschreibung is None

    def test_init_art_online(self, pruefungstermin_class):
        """Initialisierung mit Art 'online'"""
        termin = pruefungstermin_class(
            id=1,
            modul_id=10,
            datum=date(2025, 7, 15),
            art="online"
        )

        assert termin.art == "online"

    def test_init_art_praesenz(self, pruefungstermin_class):
        """Initialisierung mit Art 'praesenz'"""
        termin = pruefungstermin_class(
            id=1,
            modul_id=10,
            datum=date(2025, 7, 15),
            art="praesenz"
        )

        assert termin.art == "praesenz"

    def test_init_art_projekt(self, pruefungstermin_class):
        """Initialisierung mit Art 'projekt'"""
        termin = pruefungstermin_class(
            id=1,
            modul_id=10,
            datum=date(2025, 7, 15),
            art="projekt"
        )

        assert termin.art == "projekt"

    def test_init_art_workbook(self, pruefungstermin_class):
        """Initialisierung mit Art 'workbook'"""
        termin = pruefungstermin_class(
            id=1,
            modul_id=10,
            datum=date(2025, 7, 15),
            art="workbook"
        )

        assert termin.art == "workbook"


# ============================================================================
# TYPE CONVERSION TESTS
# ============================================================================

class TestTypeConversion:
    """Tests fuer Typ-Konvertierung in __post_init__"""

    def test_datum_from_string(self, pruefungstermin_class):
        """ISO-String wird zu date konvertiert"""
        termin = pruefungstermin_class(
            id=1,
            modul_id=10,
            datum="2025-07-15"  # String
        )

        assert isinstance(termin.datum, date)
        assert termin.datum == date(2025, 7, 15)

    def test_datum_date_unchanged(self, pruefungstermin_class):
        """date-Objekt bleibt unveraendert"""
        original_date = date(2025, 7, 15)
        termin = pruefungstermin_class(
            id=1,
            modul_id=10,
            datum=original_date
        )

        assert termin.datum == original_date

    def test_beginn_from_string(self, pruefungstermin_class):
        """ISO-String wird zu time konvertiert"""
        termin = pruefungstermin_class(
            id=1,
            modul_id=10,
            datum=date(2025, 7, 15),
            beginn="10:30"  # String
        )

        assert isinstance(termin.beginn, time)
        assert termin.beginn == time(10, 30)

    def test_beginn_from_string_with_seconds(self, pruefungstermin_class):
        """ISO-String mit Sekunden wird zu time konvertiert"""
        termin = pruefungstermin_class(
            id=1,
            modul_id=10,
            datum=date(2025, 7, 15),
            beginn="10:30:45"  # String mit Sekunden
        )

        assert isinstance(termin.beginn, time)
        assert termin.beginn == time(10, 30, 45)

    def test_ende_from_string(self, pruefungstermin_class):
        """ISO-String wird zu time konvertiert"""
        termin = pruefungstermin_class(
            id=1,
            modul_id=10,
            datum=date(2025, 7, 15),
            ende="12:00"  # String
        )

        assert isinstance(termin.ende, time)
        assert termin.ende == time(12, 0)

    def test_anmeldeschluss_from_string(self, pruefungstermin_class):
        """ISO-String wird zu datetime konvertiert"""
        termin = pruefungstermin_class(
            id=1,
            modul_id=10,
            datum=date(2025, 7, 15),
            anmeldeschluss="2025-07-01T23:59:00"  # String
        )

        assert isinstance(termin.anmeldeschluss, datetime)
        assert termin.anmeldeschluss == datetime(2025, 7, 1, 23, 59)

    def test_none_values_unchanged(self, pruefungstermin_class):
        """None-Werte bleiben None"""
        termin = pruefungstermin_class(
            id=1,
            modul_id=10,
            datum=date(2025, 7, 15),
            beginn=None,
            ende=None,
            anmeldeschluss=None
        )

        assert termin.beginn is None
        assert termin.ende is None
        assert termin.anmeldeschluss is None


# ============================================================================
# IST_ONLINE_PRUEFUNG TESTS
# ============================================================================

class TestIstOnlinePruefung:
    """Tests fuer ist_online_pruefung() Methode"""

    def test_ist_online_true(self, online_termin):
        """ist_online_pruefung() ist True bei Art 'online'"""
        assert online_termin.art == "online"
        assert online_termin.ist_online_pruefung() is True

    def test_ist_online_false_praesenz(self, praesenz_termin):
        """ist_online_pruefung() ist False bei Art 'praesenz'"""
        assert praesenz_termin.art == "praesenz"
        assert praesenz_termin.ist_online_pruefung() is False

    def test_ist_online_false_projekt(self, projekt_termin):
        """ist_online_pruefung() ist False bei Art 'projekt'"""
        assert projekt_termin.art == "projekt"
        assert projekt_termin.ist_online_pruefung() is False

    def test_ist_online_false_workbook(self, workbook_termin):
        """ist_online_pruefung() ist False bei Art 'workbook'"""
        assert workbook_termin.art == "workbook"
        assert workbook_termin.ist_online_pruefung() is False


# ============================================================================
# IST_PRAESENZ_PRUEFUNG TESTS
# ============================================================================

class TestIstPraesenzPruefung:
    """Tests fuer ist_praesenz_pruefung() Methode"""

    def test_ist_praesenz_true(self, praesenz_termin):
        """ist_praesenz_pruefung() ist True bei Art 'praesenz'"""
        assert praesenz_termin.art == "praesenz"
        assert praesenz_termin.ist_praesenz_pruefung() is True

    def test_ist_praesenz_false_online(self, online_termin):
        """ist_praesenz_pruefung() ist False bei Art 'online'"""
        assert online_termin.art == "online"
        assert online_termin.ist_praesenz_pruefung() is False

    def test_ist_praesenz_false_projekt(self, projekt_termin):
        """ist_praesenz_pruefung() ist False bei Art 'projekt'"""
        assert projekt_termin.art == "projekt"
        assert projekt_termin.ist_praesenz_pruefung() is False


# ============================================================================
# IST_PROJEKT TESTS
# ============================================================================

class TestIstProjekt:
    """Tests fuer ist_projekt() Methode"""

    def test_ist_projekt_true_projekt(self, projekt_termin):
        """ist_projekt() ist True bei Art 'projekt'"""
        assert projekt_termin.art == "projekt"
        assert projekt_termin.ist_projekt() is True

    def test_ist_projekt_true_workbook(self, workbook_termin):
        """ist_projekt() ist True bei Art 'workbook'"""
        assert workbook_termin.art == "workbook"
        assert workbook_termin.ist_projekt() is True

    def test_ist_projekt_false_online(self, online_termin):
        """ist_projekt() ist False bei Art 'online'"""
        assert online_termin.art == "online"
        assert online_termin.ist_projekt() is False

    def test_ist_projekt_false_praesenz(self, praesenz_termin):
        """ist_projekt() ist False bei Art 'praesenz'"""
        assert praesenz_termin.art == "praesenz"
        assert praesenz_termin.ist_projekt() is False


# ============================================================================
# HAT_ZEITFENSTER TESTS
# ============================================================================

class TestHatZeitfenster:
    """Tests fuer hat_zeitfenster() Methode"""

    def test_hat_zeitfenster_true(self, online_termin):
        """hat_zeitfenster() ist True wenn beginn und ende gesetzt"""
        assert online_termin.beginn is not None
        assert online_termin.ende is not None
        assert online_termin.hat_zeitfenster() is True

    def test_hat_zeitfenster_false_keine_zeiten(self, projekt_termin):
        """hat_zeitfenster() ist False ohne Zeiten"""
        assert projekt_termin.beginn is None
        assert projekt_termin.ende is None
        assert projekt_termin.hat_zeitfenster() is False

    def test_hat_zeitfenster_false_nur_beginn(self, pruefungstermin_class):
        """hat_zeitfenster() ist False wenn nur beginn gesetzt"""
        termin = pruefungstermin_class(
            id=1,
            modul_id=10,
            datum=date(2025, 7, 15),
            beginn=time(10, 0),
            ende=None
        )

        assert termin.hat_zeitfenster() is False

    def test_hat_zeitfenster_false_nur_ende(self, pruefungstermin_class):
        """hat_zeitfenster() ist False wenn nur ende gesetzt"""
        termin = pruefungstermin_class(
            id=1,
            modul_id=10,
            datum=date(2025, 7, 15),
            beginn=None,
            ende=time(12, 0)
        )

        assert termin.hat_zeitfenster() is False


# ============================================================================
# HAT_KAPAZITAET TESTS
# ============================================================================

class TestHatKapazitaet:
    """Tests fuer hat_kapazitaet() Methode"""

    def test_hat_kapazitaet_true(self, praesenz_termin):
        """hat_kapazitaet() ist True wenn kapazitaet gesetzt"""
        assert praesenz_termin.kapazitaet is not None
        assert praesenz_termin.hat_kapazitaet() is True

    def test_hat_kapazitaet_false(self, online_termin):
        """hat_kapazitaet() ist False ohne kapazitaet"""
        assert online_termin.kapazitaet is None
        assert online_termin.hat_kapazitaet() is False


# ============================================================================
# IST_ANMELDESCHLUSS_VORBEI TESTS
# ============================================================================

class TestIstAnmeldeschlussVorbei:
    """Tests fuer ist_anmeldeschluss_vorbei() Methode"""

    def test_anmeldeschluss_vorbei_true(self, vergangener_termin):
        """ist_anmeldeschluss_vorbei() ist True wenn Schluss in Vergangenheit"""
        assert vergangener_termin.anmeldeschluss < datetime.now()
        assert vergangener_termin.ist_anmeldeschluss_vorbei() is True

    def test_anmeldeschluss_vorbei_false(self, online_termin):
        """ist_anmeldeschluss_vorbei() ist False wenn Schluss in Zukunft"""
        assert online_termin.anmeldeschluss > datetime.now()
        assert online_termin.ist_anmeldeschluss_vorbei() is False

    def test_anmeldeschluss_vorbei_false_ohne_schluss(self, projekt_termin):
        """ist_anmeldeschluss_vorbei() ist False ohne Anmeldeschluss"""
        assert projekt_termin.anmeldeschluss is None
        assert projekt_termin.ist_anmeldeschluss_vorbei() is False


# ============================================================================
# IST_IN_ZUKUNFT TESTS
# ============================================================================

class TestIstInZukunft:
    """Tests fuer ist_in_zukunft() Methode"""

    def test_ist_in_zukunft_true(self, online_termin):
        """ist_in_zukunft() ist True wenn Datum in Zukunft"""
        assert online_termin.datum >= date.today()
        assert online_termin.ist_in_zukunft() is True

    def test_ist_in_zukunft_false(self, vergangener_termin):
        """ist_in_zukunft() ist False wenn Datum in Vergangenheit"""
        assert vergangener_termin.datum < date.today()
        assert vergangener_termin.ist_in_zukunft() is False

    def test_ist_in_zukunft_true_heute(self, pruefungstermin_class):
        """ist_in_zukunft() ist True wenn Datum heute ist"""
        termin = pruefungstermin_class(
            id=1,
            modul_id=10,
            datum=date.today()
        )

        assert termin.ist_in_zukunft() is True


# ============================================================================
# TO_DICT TESTS
# ============================================================================

class TestToDict:
    """Tests fuer to_dict() Methode"""

    def test_to_dict_contains_all_fields(self, online_termin):
        """to_dict() enthaelt alle Felder"""
        d = online_termin.to_dict()

        assert 'id' in d
        assert 'modul_id' in d
        assert 'datum' in d
        assert 'beginn' in d
        assert 'ende' in d
        assert 'art' in d
        assert 'ort' in d
        assert 'anmeldeschluss' in d
        assert 'kapazitaet' in d
        assert 'beschreibung' in d

    def test_to_dict_contains_computed_fields(self, online_termin):
        """to_dict() enthaelt berechnete Felder"""
        d = online_termin.to_dict()

        assert 'ist_online' in d
        assert 'ist_praesenz' in d
        assert 'ist_projekt' in d
        assert 'hat_zeitfenster' in d
        assert 'anmeldeschluss_vorbei' in d
        assert 'ist_in_zukunft' in d

    def test_to_dict_correct_values(self, online_termin):
        """to_dict() enthaelt korrekte Werte"""
        d = online_termin.to_dict()

        assert d['id'] == 1
        assert d['modul_id'] == 10
        assert d['art'] == "online"

    def test_to_dict_datum_is_iso_string(self, online_termin):
        """datum ist ISO-String in dict"""
        d = online_termin.to_dict()

        assert isinstance(d['datum'], str)
        # Pruefe ISO-Format
        date.fromisoformat(d['datum'])

    def test_to_dict_beginn_is_iso_string(self, online_termin):
        """beginn ist ISO-String in dict"""
        d = online_termin.to_dict()

        assert isinstance(d['beginn'], str)
        # Pruefe ISO-Format
        time.fromisoformat(d['beginn'])

    def test_to_dict_ende_is_iso_string(self, online_termin):
        """ende ist ISO-String in dict"""
        d = online_termin.to_dict()

        assert isinstance(d['ende'], str)
        # Pruefe ISO-Format
        time.fromisoformat(d['ende'])

    def test_to_dict_beginn_none(self, projekt_termin):
        """beginn None bleibt None"""
        d = projekt_termin.to_dict()

        assert d['beginn'] is None

    def test_to_dict_anmeldeschluss_is_iso_string(self, online_termin):
        """anmeldeschluss ist ISO-String in dict"""
        d = online_termin.to_dict()

        assert isinstance(d['anmeldeschluss'], str)
        # Pruefe ISO-Format
        datetime.fromisoformat(d['anmeldeschluss'])

    def test_to_dict_computed_values_online(self, online_termin):
        """Berechnete Werte fuer Online-Termin"""
        d = online_termin.to_dict()

        assert d['ist_online'] is True
        assert d['ist_praesenz'] is False
        assert d['ist_projekt'] is False
        assert d['hat_zeitfenster'] is True

    def test_to_dict_computed_values_praesenz(self, praesenz_termin):
        """Berechnete Werte fuer Praesenz-Termin"""
        d = praesenz_termin.to_dict()

        assert d['ist_online'] is False
        assert d['ist_praesenz'] is True
        assert d['ist_projekt'] is False

    def test_to_dict_computed_values_projekt(self, projekt_termin):
        """Berechnete Werte fuer Projekt-Termin"""
        d = projekt_termin.to_dict()

        assert d['ist_online'] is False
        assert d['ist_praesenz'] is False
        assert d['ist_projekt'] is True
        assert d['hat_zeitfenster'] is False

    def test_to_dict_is_json_serializable(self, online_termin):
        """to_dict() Ergebnis ist JSON-serialisierbar"""
        import json

        d = online_termin.to_dict()

        # Sollte nicht werfen
        json_str = json.dumps(d)
        assert isinstance(json_str, str)


# ============================================================================
# FROM_ROW TESTS
# ============================================================================

class TestFromRow:
    """Tests fuer from_row() Factory Method"""

    def test_from_row_dict(self, pruefungstermin_class):
        """from_row() funktioniert mit dict"""
        row = {
            'id': 1,
            'modul_id': 10,
            'datum': '2025-07-15',
            'beginn': '10:00',
            'ende': '12:00',
            'art': 'online',
            'ort': 'Online',
            'anmeldeschluss': '2025-07-01T23:59:00',
            'kapazitaet': 100,
            'beschreibung': 'Testklausur'
        }

        termin = pruefungstermin_class.from_row(row)

        assert termin.id == 1
        assert termin.modul_id == 10
        assert termin.datum == date(2025, 7, 15)
        assert termin.beginn == time(10, 0)
        assert termin.ende == time(12, 0)
        assert termin.art == 'online'
        assert termin.ort == 'Online'
        assert termin.anmeldeschluss == datetime(2025, 7, 1, 23, 59)
        assert termin.kapazitaet == 100
        assert termin.beschreibung == 'Testklausur'

    def test_from_row_with_date_objects(self, pruefungstermin_class):
        """from_row() funktioniert mit date/time-Objekten"""
        row = {
            'id': 1,
            'modul_id': 10,
            'datum': date(2025, 7, 15),
            'beginn': time(10, 0),
            'ende': time(12, 0),
            'art': 'praesenz',
            'ort': 'Muenchen',
            'anmeldeschluss': datetime(2025, 7, 1, 23, 59),
            'kapazitaet': 50,
            'beschreibung': None
        }

        termin = pruefungstermin_class.from_row(row)

        assert termin.datum == date(2025, 7, 15)
        assert termin.beginn == time(10, 0)
        assert termin.ende == time(12, 0)
        assert termin.anmeldeschluss == datetime(2025, 7, 1, 23, 59)

    def test_from_row_missing_optional_fields(self, pruefungstermin_class):
        """from_row() behandelt fehlende optionale Felder"""
        row = {
            'id': 1,
            'modul_id': 10,
            'datum': '2025-07-15'
        }

        mock_row = MagicMock()

        def getitem(key):
            if key in row:
                return row[key]
            raise KeyError(key)

        mock_row.__getitem__ = lambda self, key: getitem(key)

        termin = pruefungstermin_class.from_row(mock_row)

        assert termin.id == 1
        assert termin.modul_id == 10
        assert termin.beginn is None
        assert termin.ende is None
        assert termin.art == 'online'
        assert termin.ort is None
        assert termin.anmeldeschluss is None
        assert termin.kapazitaet is None
        assert termin.beschreibung is None

    def test_from_row_none_values(self, pruefungstermin_class):
        """from_row() behandelt None-Werte"""
        row = {
            'id': 1,
            'modul_id': 10,
            'datum': '2025-07-15',
            'beginn': None,
            'ende': None,
            'art': 'projekt',
            'ort': None,
            'anmeldeschluss': None,
            'kapazitaet': None,
            'beschreibung': None
        }

        termin = pruefungstermin_class.from_row(row)

        assert termin.beginn is None
        assert termin.ende is None
        assert termin.ort is None
        assert termin.anmeldeschluss is None
        assert termin.kapazitaet is None
        assert termin.beschreibung is None

    def test_from_row_sqlite_row_mock(self, pruefungstermin_class):
        """from_row() funktioniert mit sqlite3.Row-aehnlichem Objekt"""
        data = {
            'id': 2,
            'modul_id': 20,
            'datum': '2025-08-01',
            'beginn': '09:30',
            'ende': '11:30',
            'art': 'praesenz',
            'ort': 'Berlin',
            'anmeldeschluss': '2025-07-15T18:00:00',
            'kapazitaet': 30,
            'beschreibung': 'Klausur'
        }

        mock_row = MagicMock()
        mock_row.__getitem__ = lambda self, key: data[key]

        termin = pruefungstermin_class.from_row(mock_row)

        assert termin.id == 2
        assert termin.modul_id == 20
        assert termin.ort == 'Berlin'
        assert termin.kapazitaet == 30

    def test_from_row_string_ids(self, pruefungstermin_class):
        """from_row() konvertiert String-IDs zu int"""
        row = {
            'id': '123',
            'modul_id': '456',
            'datum': '2025-07-15',
            'beginn': None,
            'ende': None,
            'art': 'online',
            'ort': None,
            'anmeldeschluss': None,
            'kapazitaet': '100',
            'beschreibung': None
        }

        termin = pruefungstermin_class.from_row(row)

        assert termin.id == 123
        assert isinstance(termin.id, int)
        assert termin.modul_id == 456
        assert isinstance(termin.modul_id, int)
        assert termin.kapazitaet == 100
        assert isinstance(termin.kapazitaet, int)


# ============================================================================
# STRING REPRESENTATION TESTS
# ============================================================================

class TestStringRepresentation:
    """Tests fuer __str__ und __repr__"""

    def test_str_contains_art(self, online_termin):
        """__str__ enthaelt Art"""
        s = str(online_termin)
        assert "online" in s

    def test_str_contains_datum(self, online_termin):
        """__str__ enthaelt Datum"""
        s = str(online_termin)
        # Datum sollte im String enthalten sein
        assert str(online_termin.datum) in s

    def test_str_contains_zeitfenster(self, online_termin):
        """__str__ enthaelt Zeitfenster"""
        s = str(online_termin)
        assert "10:00" in s
        assert "12:00" in s

    def test_str_ohne_zeitfenster(self, projekt_termin):
        """__str__ zeigt 'ohne Zeit' ohne Zeitfenster"""
        s = str(projekt_termin)
        assert "ohne Zeit" in s

    def test_repr_contains_class_name(self, online_termin):
        """__repr__ enthaelt Klassennamen"""
        r = repr(online_termin)
        assert "Pruefungstermin" in r

    def test_repr_contains_id(self, online_termin):
        """__repr__ enthaelt ID"""
        r = repr(online_termin)
        assert "id=1" in r

    def test_repr_contains_modul_id(self, online_termin):
        """__repr__ enthaelt modul_id"""
        r = repr(online_termin)
        assert "modul_id=10" in r

    def test_repr_contains_datum(self, online_termin):
        """__repr__ enthaelt Datum"""
        r = repr(online_termin)
        assert "datum=" in r

    def test_repr_contains_art(self, online_termin):
        """__repr__ enthaelt Art"""
        r = repr(online_termin)
        assert "art=online" in r


# ============================================================================
# DATACLASS TESTS
# ============================================================================

class TestDataclass:
    """Tests fuer Dataclass-Eigenschaften"""

    def test_equality_same_values(self, pruefungstermin_class):
        """Gleiche Werte bedeuten Gleichheit"""
        t1 = pruefungstermin_class(
            id=1,
            modul_id=10,
            datum=date(2025, 7, 15),
            beginn=time(10, 0),
            ende=time(12, 0),
            art="online"
        )
        t2 = pruefungstermin_class(
            id=1,
            modul_id=10,
            datum=date(2025, 7, 15),
            beginn=time(10, 0),
            ende=time(12, 0),
            art="online"
        )

        assert t1 == t2

    def test_inequality_different_id(self, pruefungstermin_class):
        """Unterschiedliche IDs bedeuten Ungleichheit"""
        t1 = pruefungstermin_class(
            id=1,
            modul_id=10,
            datum=date(2025, 7, 15)
        )
        t2 = pruefungstermin_class(
            id=2,
            modul_id=10,
            datum=date(2025, 7, 15)
        )

        assert t1 != t2

    def test_inequality_different_datum(self, pruefungstermin_class):
        """Unterschiedliche Daten bedeuten Ungleichheit"""
        t1 = pruefungstermin_class(
            id=1,
            modul_id=10,
            datum=date(2025, 7, 15)
        )
        t2 = pruefungstermin_class(
            id=1,
            modul_id=10,
            datum=date(2025, 7, 16)
        )

        assert t1 != t2


# ============================================================================
# EDGE CASES
# ============================================================================

class TestEdgeCases:
    """Tests fuer Randfaelle"""

    def test_midnight_times(self, pruefungstermin_class):
        """Mitternachtszeiten werden korrekt behandelt"""
        termin = pruefungstermin_class(
            id=1,
            modul_id=10,
            datum=date(2025, 7, 15),
            beginn=time(0, 0),
            ende=time(23, 59, 59)
        )

        assert termin.beginn == time(0, 0)
        assert termin.ende == time(23, 59, 59)

    def test_large_kapazitaet(self, pruefungstermin_class):
        """Grosse Kapazitaet wird korrekt behandelt"""
        termin = pruefungstermin_class(
            id=1,
            modul_id=10,
            datum=date(2025, 7, 15),
            kapazitaet=10000
        )

        assert termin.kapazitaet == 10000
        assert termin.hat_kapazitaet() is True

    def test_very_long_description(self, pruefungstermin_class):
        """Sehr lange Beschreibung wird korrekt behandelt"""
        long_desc = "A" * 1000
        termin = pruefungstermin_class(
            id=1,
            modul_id=10,
            datum=date(2025, 7, 15),
            beschreibung=long_desc
        )

        assert termin.beschreibung == long_desc
        assert len(termin.beschreibung) == 1000

    def test_unicode_ort(self, pruefungstermin_class):
        """Unicode-Zeichen im Ort werden korrekt behandelt"""
        termin = pruefungstermin_class(
            id=1,
            modul_id=10,
            datum=date(2025, 7, 15),
            ort="Muenchen, Koenigsplatz 1"
        )

        assert "Muenchen" in termin.ort

    def test_far_future_date(self, pruefungstermin_class):
        """Weit in der Zukunft liegendes Datum"""
        termin = pruefungstermin_class(
            id=1,
            modul_id=10,
            datum=date(2099, 12, 31)
        )

        assert termin.datum == date(2099, 12, 31)
        assert termin.ist_in_zukunft() is True


# ============================================================================
# TYPE CHECKING TESTS
# ============================================================================

class TestTypeChecking:
    """Tests fuer Typenpruefung"""

    def test_id_is_int(self, online_termin):
        """id ist int"""
        assert isinstance(online_termin.id, int)

    def test_modul_id_is_int(self, online_termin):
        """modul_id ist int"""
        assert isinstance(online_termin.modul_id, int)

    def test_datum_is_date(self, online_termin):
        """datum ist date"""
        assert isinstance(online_termin.datum, date)

    def test_beginn_is_time_or_none(self, online_termin, projekt_termin):
        """beginn ist time oder None"""
        assert isinstance(online_termin.beginn, time)
        assert projekt_termin.beginn is None

    def test_ende_is_time_or_none(self, online_termin, projekt_termin):
        """ende ist time oder None"""
        assert isinstance(online_termin.ende, time)
        assert projekt_termin.ende is None

    def test_art_is_str(self, online_termin):
        """art ist str"""
        assert isinstance(online_termin.art, str)

    def test_anmeldeschluss_is_datetime_or_none(self, online_termin, projekt_termin):
        """anmeldeschluss ist datetime oder None"""
        assert isinstance(online_termin.anmeldeschluss, datetime)
        assert projekt_termin.anmeldeschluss is None

    def test_kapazitaet_is_int_or_none(self, praesenz_termin, online_termin):
        """kapazitaet ist int oder None"""
        assert isinstance(praesenz_termin.kapazitaet, int)
        assert online_termin.kapazitaet is None

    def test_ist_online_pruefung_returns_bool(self, online_termin):
        """ist_online_pruefung() gibt bool zurueck"""
        assert isinstance(online_termin.ist_online_pruefung(), bool)

    def test_ist_praesenz_pruefung_returns_bool(self, online_termin):
        """ist_praesenz_pruefung() gibt bool zurueck"""
        assert isinstance(online_termin.ist_praesenz_pruefung(), bool)

    def test_ist_projekt_returns_bool(self, online_termin):
        """ist_projekt() gibt bool zurueck"""
        assert isinstance(online_termin.ist_projekt(), bool)

    def test_hat_zeitfenster_returns_bool(self, online_termin):
        """hat_zeitfenster() gibt bool zurueck"""
        assert isinstance(online_termin.hat_zeitfenster(), bool)

    def test_hat_kapazitaet_returns_bool(self, online_termin):
        """hat_kapazitaet() gibt bool zurueck"""
        assert isinstance(online_termin.hat_kapazitaet(), bool)

    def test_ist_anmeldeschluss_vorbei_returns_bool(self, online_termin):
        """ist_anmeldeschluss_vorbei() gibt bool zurueck"""
        assert isinstance(online_termin.ist_anmeldeschluss_vorbei(), bool)

    def test_ist_in_zukunft_returns_bool(self, online_termin):
        """ist_in_zukunft() gibt bool zurueck"""
        assert isinstance(online_termin.ist_in_zukunft(), bool)

    def test_to_dict_returns_dict(self, online_termin):
        """to_dict() gibt dict zurueck"""
        assert isinstance(online_termin.to_dict(), dict)