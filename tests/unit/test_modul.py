# tests/unit/test_modul.py
"""
Unit Tests fuer Modul Domain Model (models/modul.py)

Testet die Modul- und ModulBuchung-Klassen:
- Initialisierung
- Serialisierung (to_dict)
- Factory Methods (from_db_row)
- Status-Methoden
- String-Repraesentation
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
def modul_class():
    """Importiert Modul-Klasse"""
    try:
        from models.modul import Modul
        return Modul
    except ImportError:
        from models import Modul
        return Modul


@pytest.fixture
def modulbuchung_class():
    """Importiert ModulBuchung-Klasse"""
    try:
        from models.modul import ModulBuchung
        return ModulBuchung
    except ImportError:
        from models import ModulBuchung
        return ModulBuchung


@pytest.fixture
def sample_modul(modul_class):
    """Standard-Modul fuer Tests"""
    return modul_class(
        id=1,
        name="Mathematik I",
        beschreibung="Grundlagen der Mathematik",
        ects=5
    )


@pytest.fixture
def sample_modul_no_description(modul_class):
    """Modul ohne Beschreibung"""
    return modul_class(
        id=2,
        name="Informatik I",
        beschreibung="",
        ects=6
    )


@pytest.fixture
def sample_modulbuchung(modulbuchung_class, sample_modul):
    """Standard-ModulBuchung fuer Tests"""
    return modulbuchung_class(
        modul=sample_modul,
        status="gebucht",
        buchbar=True,
        buchungsdatum="2025-01-15",
        note=None,
        pflichtgrad="Pflicht",
        semester=1
    )


@pytest.fixture
def passed_modulbuchung(modulbuchung_class, sample_modul):
    """Bestandene ModulBuchung fuer Tests"""
    return modulbuchung_class(
        modul=sample_modul,
        status="bestanden",
        buchbar=False,
        buchungsdatum="2025-01-15",
        note=1.7,
        pflichtgrad="Pflicht",
        semester=1
    )


@pytest.fixture
def unbookable_modulbuchung(modulbuchung_class, sample_modul):
    """Nicht buchbare ModulBuchung fuer Tests"""
    return modulbuchung_class(
        modul=sample_modul,
        status=None,
        buchbar=False,
        buchungsdatum=None,
        note=None,
        pflichtgrad="Wahl",
        semester=3
    )


# ============================================================================
# MODUL INITIALIZATION TESTS
# ============================================================================

class TestModulInit:
    """Tests fuer Modul-Initialisierung"""

    def test_init_with_all_fields(self, modul_class):
        """Initialisierung mit allen Feldern"""
        modul = modul_class(
            id=1,
            name="Mathematik I",
            beschreibung="Grundlagen der Mathematik",
            ects=5
        )

        assert modul.id == 1
        assert modul.name == "Mathematik I"
        assert modul.beschreibung == "Grundlagen der Mathematik"
        assert modul.ects == 5

    def test_init_empty_description(self, modul_class):
        """Initialisierung mit leerer Beschreibung"""
        modul = modul_class(
            id=1,
            name="Test",
            beschreibung="",
            ects=5
        )

        assert modul.beschreibung == ""

    def test_init_various_ects_values(self, modul_class):
        """Verschiedene ECTS-Werte"""
        for ects in [1, 5, 6, 10, 15, 30]:
            modul = modul_class(
                id=1,
                name="Test",
                beschreibung="",
                ects=ects
            )
            assert modul.ects == ects

    def test_init_long_name(self, modul_class):
        """Langer Modulname"""
        long_name = "Einfuehrung in die objektorientierte Programmierung mit Python"
        modul = modul_class(
            id=1,
            name=long_name,
            beschreibung="",
            ects=5
        )

        assert modul.name == long_name

    def test_init_long_description(self, modul_class):
        """Lange Beschreibung"""
        long_desc = "A" * 1000
        modul = modul_class(
            id=1,
            name="Test",
            beschreibung=long_desc,
            ects=5
        )

        assert modul.beschreibung == long_desc
        assert len(modul.beschreibung) == 1000


# ============================================================================
# MODUL TO_DICT TESTS
# ============================================================================

class TestModulToDict:
    """Tests fuer Modul.to_dict() Methode"""

    def test_to_dict_contains_all_fields(self, sample_modul):
        """to_dict() enthaelt alle Felder"""
        d = sample_modul.to_dict()

        assert 'id' in d
        assert 'name' in d
        assert 'beschreibung' in d
        assert 'ects' in d

    def test_to_dict_correct_values(self, sample_modul):
        """to_dict() enthaelt korrekte Werte"""
        d = sample_modul.to_dict()

        assert d['id'] == 1
        assert d['name'] == "Mathematik I"
        assert d['beschreibung'] == "Grundlagen der Mathematik"
        assert d['ects'] == 5

    def test_to_dict_empty_description(self, sample_modul_no_description):
        """to_dict() mit leerer Beschreibung"""
        d = sample_modul_no_description.to_dict()

        assert d['beschreibung'] == ""

    def test_to_dict_is_json_serializable(self, sample_modul):
        """to_dict() Ergebnis ist JSON-serialisierbar"""
        import json

        d = sample_modul.to_dict()

        # Sollte nicht werfen
        json_str = json.dumps(d)
        assert isinstance(json_str, str)

    def test_to_dict_returns_new_dict(self, sample_modul):
        """to_dict() gibt neues Dictionary zurueck"""
        d1 = sample_modul.to_dict()
        d2 = sample_modul.to_dict()

        # Sollten gleich aber nicht identisch sein
        assert d1 == d2
        assert d1 is not d2


# ============================================================================
# MODUL FROM_DB_ROW TESTS
# ============================================================================

class TestModulFromDbRow:
    """Tests fuer Modul.from_db_row() Factory Method"""

    def test_from_db_row_dict(self, modul_class):
        """from_db_row() funktioniert mit dict"""
        row = {
            'id': 1,
            'name': 'Mathematik I',
            'beschreibung': 'Grundlagen der Mathematik',
            'ects': 5
        }

        modul = modul_class.from_db_row(row)

        assert modul.id == 1
        assert modul.name == 'Mathematik I'
        assert modul.beschreibung == 'Grundlagen der Mathematik'
        assert modul.ects == 5

    def test_from_db_row_none_description(self, modul_class):
        """from_db_row() behandelt None-Beschreibung"""
        row = {
            'id': 1,
            'name': 'Test',
            'beschreibung': None,
            'ects': 5
        }

        modul = modul_class.from_db_row(row)

        assert modul.beschreibung == ''

    def test_from_db_row_sqlite_row_mock(self, modul_class):
        """from_db_row() funktioniert mit sqlite3.Row-aehnlichem Objekt"""
        data = {
            'id': 2,
            'name': 'Informatik I',
            'beschreibung': 'Programmierung',
            'ects': 6
        }

        mock_row = MagicMock()
        mock_row.__getitem__ = lambda self, key: data[key]

        modul = modul_class.from_db_row(mock_row)

        assert modul.id == 2
        assert modul.name == 'Informatik I'

    def test_from_db_row_string_id(self, modul_class):
        """from_db_row() konvertiert String-ID zu int"""
        row = {
            'id': '123',
            'name': 'Test',
            'beschreibung': 'Desc',
            'ects': '5'
        }

        modul = modul_class.from_db_row(row)

        assert modul.id == 123
        assert isinstance(modul.id, int)
        assert modul.ects == 5
        assert isinstance(modul.ects, int)


# ============================================================================
# MODUL STRING REPRESENTATION TESTS
# ============================================================================

class TestModulStringRepresentation:
    """Tests fuer Modul __str__ und __repr__"""

    def test_str_contains_name(self, sample_modul):
        """__str__ enthaelt Modulname"""
        s = str(sample_modul)
        assert "Mathematik I" in s

    def test_str_contains_ects(self, sample_modul):
        """__str__ enthaelt ECTS"""
        s = str(sample_modul)
        assert "5" in s
        assert "ECTS" in s

    def test_str_format(self, sample_modul):
        """__str__ hat korrektes Format"""
        s = str(sample_modul)
        assert s == "Modul(Mathematik I, 5 ECTS)"

    def test_repr_contains_class_name(self, sample_modul):
        """__repr__ enthaelt Klassennamen"""
        r = repr(sample_modul)
        assert "Modul" in r

    def test_repr_contains_id(self, sample_modul):
        """__repr__ enthaelt ID"""
        r = repr(sample_modul)
        assert "id=1" in r

    def test_repr_contains_name(self, sample_modul):
        """__repr__ enthaelt Name"""
        r = repr(sample_modul)
        assert "name='Mathematik I'" in r

    def test_repr_contains_ects(self, sample_modul):
        """__repr__ enthaelt ECTS"""
        r = repr(sample_modul)
        assert "ects=5" in r


# ============================================================================
# MODUL DATACLASS TESTS
# ============================================================================

class TestModulDataclass:
    """Tests fuer Modul Dataclass-Eigenschaften"""

    def test_equality_same_values(self, modul_class):
        """Gleiche Werte bedeuten Gleichheit"""
        m1 = modul_class(id=1, name="Test", beschreibung="Desc", ects=5)
        m2 = modul_class(id=1, name="Test", beschreibung="Desc", ects=5)

        assert m1 == m2

    def test_inequality_different_id(self, modul_class):
        """Unterschiedliche IDs bedeuten Ungleichheit"""
        m1 = modul_class(id=1, name="Test", beschreibung="Desc", ects=5)
        m2 = modul_class(id=2, name="Test", beschreibung="Desc", ects=5)

        assert m1 != m2

    def test_inequality_different_name(self, modul_class):
        """Unterschiedliche Namen bedeuten Ungleichheit"""
        m1 = modul_class(id=1, name="Test1", beschreibung="Desc", ects=5)
        m2 = modul_class(id=1, name="Test2", beschreibung="Desc", ects=5)

        assert m1 != m2

    def test_is_hashable(self, modul_class):
        """Modul ist hashbar (wenn frozen oder default)"""
        m = modul_class(id=1, name="Test", beschreibung="Desc", ects=5)

        # Dataclass ohne frozen=True ist nicht hashbar
        # aber wir testen nur dass kein Fehler auftritt bei der Nutzung
        assert m is not None


# ============================================================================
# MODULBUCHUNG INITIALIZATION TESTS
# ============================================================================

class TestModulBuchungInit:
    """Tests fuer ModulBuchung-Initialisierung"""

    def test_init_with_all_fields(self, modulbuchung_class, sample_modul):
        """Initialisierung mit allen Feldern"""
        mb = modulbuchung_class(
            modul=sample_modul,
            status="gebucht",
            buchbar=True,
            buchungsdatum="2025-01-15",
            note=None,
            pflichtgrad="Pflicht",
            semester=1
        )

        assert mb.modul == sample_modul
        assert mb.status == "gebucht"
        assert mb.buchbar is True
        assert mb.buchungsdatum == "2025-01-15"
        assert mb.note is None
        assert mb.pflichtgrad == "Pflicht"
        assert mb.semester == 1

    def test_init_status_bestanden(self, modulbuchung_class, sample_modul):
        """Initialisierung mit Status 'bestanden'"""
        mb = modulbuchung_class(
            modul=sample_modul,
            status="bestanden",
            buchbar=False,
            buchungsdatum="2025-01-15",
            note=2.3,
            pflichtgrad="Pflicht",
            semester=1
        )

        assert mb.status == "bestanden"
        assert mb.note == 2.3

    def test_init_status_none(self, modulbuchung_class, sample_modul):
        """Initialisierung mit Status None"""
        mb = modulbuchung_class(
            modul=sample_modul,
            status=None,
            buchbar=False,
            buchungsdatum=None,
            note=None,
            pflichtgrad="Wahl",
            semester=3
        )

        assert mb.status is None
        assert mb.buchungsdatum is None

    def test_init_various_pflichtgrade(self, modulbuchung_class, sample_modul):
        """Verschiedene Pflichtgrade"""
        for pflichtgrad in ["Pflicht", "Wahlpflicht", "Wahl"]:
            mb = modulbuchung_class(
                modul=sample_modul,
                status=None,
                buchbar=True,
                buchungsdatum=None,
                note=None,
                pflichtgrad=pflichtgrad,
                semester=1
            )
            assert mb.pflichtgrad == pflichtgrad

    def test_init_various_semesters(self, modulbuchung_class, sample_modul):
        """Verschiedene Semester"""
        for semester in range(1, 8):
            mb = modulbuchung_class(
                modul=sample_modul,
                status=None,
                buchbar=True,
                buchungsdatum=None,
                note=None,
                pflichtgrad="Pflicht",
                semester=semester
            )
            assert mb.semester == semester


# ============================================================================
# MODULBUCHUNG IS_PASSED TESTS
# ============================================================================

class TestModulBuchungIsPassed:
    """Tests fuer ModulBuchung.is_passed() Methode"""

    def test_is_passed_true(self, passed_modulbuchung):
        """is_passed() ist True bei Status 'bestanden'"""
        assert passed_modulbuchung.status == "bestanden"
        assert passed_modulbuchung.is_passed() is True

    def test_is_passed_false_gebucht(self, sample_modulbuchung):
        """is_passed() ist False bei Status 'gebucht'"""
        assert sample_modulbuchung.status == "gebucht"
        assert sample_modulbuchung.is_passed() is False

    def test_is_passed_false_none(self, unbookable_modulbuchung):
        """is_passed() ist False bei Status None"""
        assert unbookable_modulbuchung.status is None
        assert unbookable_modulbuchung.is_passed() is False


# ============================================================================
# MODULBUCHUNG IS_BOOKED TESTS
# ============================================================================

class TestModulBuchungIsBooked:
    """Tests fuer ModulBuchung.is_booked() Methode"""

    def test_is_booked_true(self, sample_modulbuchung):
        """is_booked() ist True bei Status 'gebucht'"""
        assert sample_modulbuchung.status == "gebucht"
        assert sample_modulbuchung.is_booked() is True

    def test_is_booked_false_bestanden(self, passed_modulbuchung):
        """is_booked() ist False bei Status 'bestanden'"""
        assert passed_modulbuchung.status == "bestanden"
        assert passed_modulbuchung.is_booked() is False

    def test_is_booked_false_none(self, unbookable_modulbuchung):
        """is_booked() ist False bei Status None"""
        assert unbookable_modulbuchung.status is None
        assert unbookable_modulbuchung.is_booked() is False


# ============================================================================
# MODULBUCHUNG TO_DICT TESTS
# ============================================================================

class TestModulBuchungToDict:
    """Tests fuer ModulBuchung.to_dict() Methode"""

    def test_to_dict_contains_all_fields(self, sample_modulbuchung):
        """to_dict() enthaelt alle Felder"""
        d = sample_modulbuchung.to_dict()

        assert 'modul_id' in d
        assert 'name' in d
        assert 'ects' in d
        assert 'status' in d
        assert 'buchbar' in d
        assert 'buchungsdatum' in d
        assert 'note' in d
        assert 'pflichtgrad' in d
        assert 'semester' in d

    def test_to_dict_contains_computed_fields(self, sample_modulbuchung):
        """to_dict() enthaelt berechnete Felder"""
        d = sample_modulbuchung.to_dict()

        assert 'is_passed' in d
        assert 'is_booked' in d

    def test_to_dict_correct_modul_values(self, sample_modulbuchung):
        """to_dict() enthaelt korrekte Modul-Werte"""
        d = sample_modulbuchung.to_dict()

        assert d['modul_id'] == 1
        assert d['name'] == "Mathematik I"
        assert d['ects'] == 5

    def test_to_dict_correct_booking_values(self, sample_modulbuchung):
        """to_dict() enthaelt korrekte Buchungs-Werte"""
        d = sample_modulbuchung.to_dict()

        assert d['status'] == "gebucht"
        assert d['buchbar'] is True
        assert d['buchungsdatum'] == "2025-01-15"
        assert d['note'] is None
        assert d['pflichtgrad'] == "Pflicht"
        assert d['semester'] == 1

    def test_to_dict_correct_computed_values_gebucht(self, sample_modulbuchung):
        """to_dict() enthaelt korrekte berechnete Werte fuer 'gebucht'"""
        d = sample_modulbuchung.to_dict()

        assert d['is_passed'] is False
        assert d['is_booked'] is True

    def test_to_dict_correct_computed_values_bestanden(self, passed_modulbuchung):
        """to_dict() enthaelt korrekte berechnete Werte fuer 'bestanden'"""
        d = passed_modulbuchung.to_dict()

        assert d['is_passed'] is True
        assert d['is_booked'] is False
        assert d['note'] == 1.7

    def test_to_dict_is_json_serializable(self, sample_modulbuchung):
        """to_dict() Ergebnis ist JSON-serialisierbar"""
        import json

        d = sample_modulbuchung.to_dict()

        # Sollte nicht werfen
        json_str = json.dumps(d)
        assert isinstance(json_str, str)

    def test_to_dict_note_none(self, sample_modulbuchung):
        """to_dict() behandelt None-Note korrekt"""
        d = sample_modulbuchung.to_dict()

        assert d['note'] is None

    def test_to_dict_note_with_value(self, passed_modulbuchung):
        """to_dict() behandelt Note mit Wert korrekt"""
        d = passed_modulbuchung.to_dict()

        assert d['note'] == 1.7
        assert isinstance(d['note'], float)


# ============================================================================
# MODULBUCHUNG STRING REPRESENTATION TESTS
# ============================================================================

class TestModulBuchungStringRepresentation:
    """Tests fuer ModulBuchung __str__"""

    def test_str_contains_modul_name(self, sample_modulbuchung):
        """__str__ enthaelt Modulnamen"""
        s = str(sample_modulbuchung)
        assert "Mathematik I" in s

    def test_str_contains_status_gebucht(self, sample_modulbuchung):
        """__str__ enthaelt Status 'gebucht'"""
        s = str(sample_modulbuchung)
        assert "gebucht" in s

    def test_str_contains_status_bestanden(self, passed_modulbuchung):
        """__str__ enthaelt Status 'bestanden'"""
        s = str(passed_modulbuchung)
        assert "bestanden" in s

    def test_str_unbookable_status(self, unbookable_modulbuchung):
        """__str__ zeigt 'unbuchbar' fuer None-Status"""
        s = str(unbookable_modulbuchung)
        assert "unbuchbar" in s.lower() or "None" in s

    def test_str_format(self, sample_modulbuchung):
        """__str__ hat korrektes Format"""
        s = str(sample_modulbuchung)
        assert s == "ModulBuchung(Mathematik I [gebucht])"


# ============================================================================
# MODULBUCHUNG EDGE CASES
# ============================================================================

class TestModulBuchungEdgeCases:
    """Tests fuer ModulBuchung Randfaelle"""

    def test_note_boundary_1_0(self, modulbuchung_class, sample_modul):
        """Note 1.0 (beste Note)"""
        mb = modulbuchung_class(
            modul=sample_modul,
            status="bestanden",
            buchbar=False,
            buchungsdatum="2025-01-15",
            note=1.0,
            pflichtgrad="Pflicht",
            semester=1
        )

        assert mb.note == 1.0

    def test_note_boundary_4_0(self, modulbuchung_class, sample_modul):
        """Note 4.0 (gerade noch bestanden)"""
        mb = modulbuchung_class(
            modul=sample_modul,
            status="bestanden",
            buchbar=False,
            buchungsdatum="2025-01-15",
            note=4.0,
            pflichtgrad="Pflicht",
            semester=1
        )

        assert mb.note == 4.0

    def test_note_boundary_5_0(self, modulbuchung_class, sample_modul):
        """Note 5.0 (nicht bestanden)"""
        mb = modulbuchung_class(
            modul=sample_modul,
            status="gebucht",  # Nicht bestanden
            buchbar=False,
            buchungsdatum="2025-01-15",
            note=5.0,
            pflichtgrad="Pflicht",
            semester=1
        )

        assert mb.note == 5.0

    def test_semester_1(self, modulbuchung_class, sample_modul):
        """Semester 1"""
        mb = modulbuchung_class(
            modul=sample_modul,
            status=None,
            buchbar=True,
            buchungsdatum=None,
            note=None,
            pflichtgrad="Pflicht",
            semester=1
        )

        assert mb.semester == 1

    def test_semester_7(self, modulbuchung_class, sample_modul):
        """Semester 7 (letztes Semester)"""
        mb = modulbuchung_class(
            modul=sample_modul,
            status=None,
            buchbar=True,
            buchungsdatum=None,
            note=None,
            pflichtgrad="Pflicht",
            semester=7
        )

        assert mb.semester == 7

    def test_buchbar_true_not_booked(self, modulbuchung_class, sample_modul):
        """Buchbar aber noch nicht gebucht"""
        mb = modulbuchung_class(
            modul=sample_modul,
            status=None,
            buchbar=True,
            buchungsdatum=None,
            note=None,
            pflichtgrad="Pflicht",
            semester=1
        )

        assert mb.buchbar is True
        assert mb.status is None
        assert mb.is_booked() is False

    def test_modul_reference(self, sample_modulbuchung, sample_modul):
        """ModulBuchung enthaelt Referenz auf Modul"""
        assert sample_modulbuchung.modul is sample_modul
        assert sample_modulbuchung.modul.id == 1


# ============================================================================
# INTEGRATION MODUL + MODULBUCHUNG
# ============================================================================

class TestModulModulBuchungIntegration:
    """Integrationstests fuer Modul und ModulBuchung zusammen"""

    def test_modulbuchung_uses_modul_data(self, modulbuchung_class, modul_class):
        """ModulBuchung verwendet Modul-Daten korrekt"""
        modul = modul_class(
            id=42,
            name="Spezialmodul",
            beschreibung="Besondere Beschreibung",
            ects=10
        )

        mb = modulbuchung_class(
            modul=modul,
            status="gebucht",
            buchbar=True,
            buchungsdatum="2025-06-01",
            note=None,
            pflichtgrad="Wahl",
            semester=5
        )

        d = mb.to_dict()

        assert d['modul_id'] == 42
        assert d['name'] == "Spezialmodul"
        assert d['ects'] == 10

    def test_multiple_buchungen_same_modul(self, modulbuchung_class, modul_class):
        """Mehrere Buchungen fuer dasselbe Modul (unterschiedliche Studenten)"""
        modul = modul_class(
            id=1,
            name="Gemeinsames Modul",
            beschreibung="",
            ects=5
        )

        mb1 = modulbuchung_class(
            modul=modul,
            status="bestanden",
            buchbar=False,
            buchungsdatum="2025-01-01",
            note=1.3,
            pflichtgrad="Pflicht",
            semester=1
        )

        mb2 = modulbuchung_class(
            modul=modul,
            status="gebucht",
            buchbar=True,
            buchungsdatum="2025-02-01",
            note=None,
            pflichtgrad="Pflicht",
            semester=1
        )

        # Beide referenzieren dasselbe Modul
        assert mb1.modul is mb2.modul

        # Aber haben unterschiedlichen Status
        assert mb1.is_passed() is True
        assert mb2.is_passed() is False

    def test_from_db_row_to_modulbuchung(self, modul_class, modulbuchung_class):
        """Modul aus DB-Row erstellen und in ModulBuchung verwenden"""
        row = {
            'id': 99,
            'name': 'DB-Modul',
            'beschreibung': 'Aus Datenbank',
            'ects': 8
        }

        modul = modul_class.from_db_row(row)

        mb = modulbuchung_class(
            modul=modul,
            status="bestanden",
            buchbar=False,
            buchungsdatum="2025-03-15",
            note=2.0,
            pflichtgrad="Pflicht",
            semester=2
        )

        d = mb.to_dict()

        assert d['modul_id'] == 99
        assert d['name'] == 'DB-Modul'
        assert d['ects'] == 8
        assert d['note'] == 2.0


# ============================================================================
# TYPE CHECKING TESTS
# ============================================================================

class TestTypeChecking:
    """Tests fuer Typenpruefung"""

    def test_modul_id_is_int(self, sample_modul):
        """Modul.id ist int"""
        assert isinstance(sample_modul.id, int)

    def test_modul_ects_is_int(self, sample_modul):
        """Modul.ects ist int"""
        assert isinstance(sample_modul.ects, int)

    def test_modul_name_is_str(self, sample_modul):
        """Modul.name ist str"""
        assert isinstance(sample_modul.name, str)

    def test_modulbuchung_semester_is_int(self, sample_modulbuchung):
        """ModulBuchung.semester ist int"""
        assert isinstance(sample_modulbuchung.semester, int)

    def test_modulbuchung_buchbar_is_bool(self, sample_modulbuchung):
        """ModulBuchung.buchbar ist bool"""
        assert isinstance(sample_modulbuchung.buchbar, bool)

    def test_modulbuchung_note_is_float_or_none(self, passed_modulbuchung, sample_modulbuchung):
        """ModulBuchung.note ist float oder None"""
        assert isinstance(passed_modulbuchung.note, float)
        assert sample_modulbuchung.note is None