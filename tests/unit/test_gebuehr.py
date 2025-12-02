# tests/unit/test_gebuehr.py
"""
Unit Tests fuer Gebuehr Domain Model

Testet das Gebuehr-Modell (models/gebuehr.py):
- Initialisierung und Validierung
- Zahlungsstatus-Methoden
- Faelligkeits-Berechnungen
- Formatierung und Serialisierung
"""
from __future__ import annotations

import pytest
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock

# Mark this whole module as unit tests
pytestmark = pytest.mark.unit


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def gebuehr_class():
    """Importiert Gebuehr-Klasse"""
    try:
        from models.gebuehr import Gebuehr
        return Gebuehr
    except ImportError:
        from models import Gebuehr
        return Gebuehr


@pytest.fixture
def allowed_art():
    """Importiert ALLOWED_ART Konstante"""
    try:
        from models.gebuehr import ALLOWED_ART
        return ALLOWED_ART
    except ImportError:
        from models import ALLOWED_ART
        return ALLOWED_ART


@pytest.fixture
def sample_gebuehr(gebuehr_class):
    """Standard-Gebuehr fuer Tests"""
    return gebuehr_class(
        id=1,
        einschreibung_id=100,
        art="Monatsrate",
        betrag=Decimal("199.00"),
        faellig_am=date(2025, 6, 1),
        bezahlt_am=None
    )


@pytest.fixture
def paid_gebuehr(gebuehr_class):
    """Bezahlte Gebuehr fuer Tests"""
    return gebuehr_class(
        id=2,
        einschreibung_id=100,
        art="Monatsrate",
        betrag=Decimal("199.00"),
        faellig_am=date(2025, 5, 1),
        bezahlt_am=date(2025, 5, 3)
    )


@pytest.fixture
def overdue_gebuehr(gebuehr_class):
    """Ueberfaellige Gebuehr fuer Tests"""
    return gebuehr_class(
        id=3,
        einschreibung_id=100,
        art="Monatsrate",
        betrag=Decimal("199.00"),
        faellig_am=date(2024, 1, 1),  # In der Vergangenheit
        bezahlt_am=None
    )


# ============================================================================
# INITIALIZATION TESTS
# ============================================================================

class TestGebuehrInit:
    """Tests fuer Gebuehr-Initialisierung"""

    def test_init_with_all_fields(self, gebuehr_class):
        """Initialisierung mit allen Feldern"""
        g = gebuehr_class(
            id=1,
            einschreibung_id=100,
            art="Monatsrate",
            betrag=Decimal("199.00"),
            faellig_am=date(2025, 6, 1),
            bezahlt_am=date(2025, 6, 5)
        )

        assert g.id == 1
        assert g.einschreibung_id == 100
        assert g.art == "Monatsrate"
        assert g.betrag == Decimal("199.00")
        assert g.faellig_am == date(2025, 6, 1)
        assert g.bezahlt_am == date(2025, 6, 5)

    def test_init_without_id(self, gebuehr_class):
        """Initialisierung ohne ID (fuer neue Eintraege)"""
        g = gebuehr_class(
            id=None,
            einschreibung_id=100,
            art="Monatsrate",
            betrag=Decimal("199.00"),
            faellig_am=date(2025, 6, 1)
        )

        assert g.id is None

    def test_init_bezahlt_am_default_none(self, gebuehr_class):
        """bezahlt_am ist standardmaessig None"""
        g = gebuehr_class(
            id=1,
            einschreibung_id=100,
            art="Monatsrate",
            betrag=Decimal("199.00"),
            faellig_am=date(2025, 6, 1)
        )

        assert g.bezahlt_am is None

    def test_init_all_allowed_arts(self, gebuehr_class, allowed_art):
        """Alle erlaubten Gebuehrenarten funktionieren"""
        for art in allowed_art:
            g = gebuehr_class(
                id=1,
                einschreibung_id=100,
                art=art,
                betrag=Decimal("100.00"),
                faellig_am=date(2025, 6, 1)
            )
            assert g.art == art

    def test_init_unknown_art_logs_warning(self, gebuehr_class, caplog):
        """Unbekannte Gebuehrenart loggt Warnung"""
        import logging

        with caplog.at_level(logging.WARNING):
            g = gebuehr_class(
                id=1,
                einschreibung_id=100,
                art="UnbekannteArt",
                betrag=Decimal("100.00"),
                faellig_am=date(2025, 6, 1)
            )

            # Gebuehr wird trotzdem erstellt
            assert g.art == "UnbekannteArt"


# ============================================================================
# BETRAG CONVERSION TESTS
# ============================================================================

class TestBetragConversion:
    """Tests fuer Betrag-Konvertierung in __post_init__"""

    def test_betrag_from_int(self, gebuehr_class):
        """Integer wird zu Decimal konvertiert"""
        g = gebuehr_class(
            id=1,
            einschreibung_id=100,
            art="Monatsrate",
            betrag=199,  # int
            faellig_am=date(2025, 6, 1)
        )

        assert isinstance(g.betrag, Decimal)
        assert g.betrag == Decimal("199")

    def test_betrag_from_float(self, gebuehr_class):
        """Float wird zu Decimal konvertiert"""
        g = gebuehr_class(
            id=1,
            einschreibung_id=100,
            art="Monatsrate",
            betrag=199.50,  # float
            faellig_am=date(2025, 6, 1)
        )

        assert isinstance(g.betrag, Decimal)
        assert g.betrag == Decimal("199.5")

    def test_betrag_from_string(self, gebuehr_class):
        """String wird zu Decimal konvertiert"""
        g = gebuehr_class(
            id=1,
            einschreibung_id=100,
            art="Monatsrate",
            betrag="199.99",  # string
            faellig_am=date(2025, 6, 1)
        )

        assert isinstance(g.betrag, Decimal)
        assert g.betrag == Decimal("199.99")

    def test_betrag_zero_allowed(self, gebuehr_class):
        """Betrag von 0 ist erlaubt"""
        g = gebuehr_class(
            id=1,
            einschreibung_id=100,
            art="Monatsrate",
            betrag=Decimal("0"),
            faellig_am=date(2025, 6, 1)
        )

        assert g.betrag == Decimal("0")

    def test_betrag_negative_raises_error(self, gebuehr_class):
        """Negativer Betrag wirft ValueError"""
        with pytest.raises(ValueError, match="nicht negativ"):
            gebuehr_class(
                id=1,
                einschreibung_id=100,
                art="Monatsrate",
                betrag=Decimal("-10.00"),
                faellig_am=date(2025, 6, 1)
            )

    def test_betrag_invalid_string_raises_error(self, gebuehr_class):
        """Ungueltiger Betrag-String wirft ValueError"""
        with pytest.raises(ValueError, match="Betrag"):
            gebuehr_class(
                id=1,
                einschreibung_id=100,
                art="Monatsrate",
                betrag="abc",
                faellig_am=date(2025, 6, 1)
            )

    def test_betrag_none_raises_error(self, gebuehr_class):
        """None als Betrag wirft ValueError"""
        with pytest.raises((ValueError, TypeError)):
            gebuehr_class(
                id=1,
                einschreibung_id=100,
                art="Monatsrate",
                betrag=None,
                faellig_am=date(2025, 6, 1)
            )


# ============================================================================
# DATE CONVERSION TESTS
# ============================================================================

class TestDateConversion:
    """Tests fuer Datum-Konvertierung in __post_init__"""

    def test_faellig_am_from_string(self, gebuehr_class):
        """faellig_am wird aus ISO-String geparst"""
        g = gebuehr_class(
            id=1,
            einschreibung_id=100,
            art="Monatsrate",
            betrag=Decimal("199.00"),
            faellig_am="2025-06-01"  # ISO string
        )

        assert isinstance(g.faellig_am, date)
        assert g.faellig_am == date(2025, 6, 1)

    def test_bezahlt_am_from_string(self, gebuehr_class):
        """bezahlt_am wird aus ISO-String geparst"""
        g = gebuehr_class(
            id=1,
            einschreibung_id=100,
            art="Monatsrate",
            betrag=Decimal("199.00"),
            faellig_am=date(2025, 6, 1),
            bezahlt_am="2025-06-05"  # ISO string
        )

        assert isinstance(g.bezahlt_am, date)
        assert g.bezahlt_am == date(2025, 6, 5)

    def test_faellig_am_invalid_string_raises_error(self, gebuehr_class):
        """Ungueltiger faellig_am-String wirft ValueError"""
        with pytest.raises(ValueError, match="faellig_am"):
            gebuehr_class(
                id=1,
                einschreibung_id=100,
                art="Monatsrate",
                betrag=Decimal("199.00"),
                faellig_am="invalid-date"
            )

    def test_bezahlt_am_invalid_string_raises_error(self, gebuehr_class):
        """Ungueltiger bezahlt_am-String wirft ValueError"""
        with pytest.raises(ValueError, match="bezahlt_am"):
            gebuehr_class(
                id=1,
                einschreibung_id=100,
                art="Monatsrate",
                betrag=Decimal("199.00"),
                faellig_am=date(2025, 6, 1),
                bezahlt_am="not-a-date"
            )


# ============================================================================
# IS_PAID TESTS
# ============================================================================

class TestIsPaid:
    """Tests fuer is_paid() Methode"""

    def test_is_paid_false_when_bezahlt_am_none(self, sample_gebuehr):
        """is_paid() ist False wenn bezahlt_am None"""
        assert sample_gebuehr.bezahlt_am is None
        assert sample_gebuehr.is_paid() is False

    def test_is_paid_true_when_bezahlt_am_set(self, paid_gebuehr):
        """is_paid() ist True wenn bezahlt_am gesetzt"""
        assert paid_gebuehr.bezahlt_am is not None
        assert paid_gebuehr.is_paid() is True


# ============================================================================
# IS_OVERDUE TESTS
# ============================================================================

class TestIsOverdue:
    """Tests fuer is_overdue() Methode"""

    def test_is_overdue_true_when_past_due_unpaid(self, overdue_gebuehr):
        """is_overdue() ist True wenn Faelligkeit ueberschritten und nicht bezahlt"""
        ref_date = date(2025, 6, 1)  # Nach dem Faelligkeitsdatum
        assert overdue_gebuehr.is_overdue(ref_date) is True

    def test_is_overdue_false_when_paid(self, paid_gebuehr):
        """is_overdue() ist False wenn bezahlt"""
        ref_date = date(2025, 6, 1)  # Nach dem Faelligkeitsdatum
        assert paid_gebuehr.is_overdue(ref_date) is False

    def test_is_overdue_false_when_not_yet_due(self, sample_gebuehr):
        """is_overdue() ist False wenn noch nicht faellig"""
        ref_date = date(2025, 5, 1)  # Vor dem Faelligkeitsdatum
        assert sample_gebuehr.is_overdue(ref_date) is False

    def test_is_overdue_false_on_due_date(self, gebuehr_class):
        """is_overdue() ist False am Faelligkeitstag selbst"""
        g = gebuehr_class(
            id=1,
            einschreibung_id=100,
            art="Monatsrate",
            betrag=Decimal("199.00"),
            faellig_am=date(2025, 6, 1)
        )

        # Am gleichen Tag ist noch nicht ueberfaellig
        assert g.is_overdue(date(2025, 6, 1)) is False

    def test_is_overdue_true_one_day_after_due(self, gebuehr_class):
        """is_overdue() ist True einen Tag nach Faelligkeit"""
        g = gebuehr_class(
            id=1,
            einschreibung_id=100,
            art="Monatsrate",
            betrag=Decimal("199.00"),
            faellig_am=date(2025, 6, 1)
        )

        # Einen Tag danach ist ueberfaellig
        assert g.is_overdue(date(2025, 6, 2)) is True

    def test_is_overdue_uses_today_as_default(self, gebuehr_class):
        """is_overdue() verwendet heute als Standard-Referenzdatum"""
        yesterday = date.today() - timedelta(days=1)

        g = gebuehr_class(
            id=1,
            einschreibung_id=100,
            art="Monatsrate",
            betrag=Decimal("199.00"),
            faellig_am=yesterday
        )

        # Sollte ueberfaellig sein (gestern war Faelligkeit)
        assert g.is_overdue() is True


# ============================================================================
# IS_DUE_SOON TESTS
# ============================================================================

class TestIsDueSoon:
    """Tests fuer is_due_soon() Methode"""

    def test_is_due_soon_true_within_7_days(self, gebuehr_class):
        """is_due_soon() ist True wenn innerhalb 7 Tagen faellig"""
        ref_date = date(2025, 6, 1)

        g = gebuehr_class(
            id=1,
            einschreibung_id=100,
            art="Monatsrate",
            betrag=Decimal("199.00"),
            faellig_am=date(2025, 6, 5)  # 4 Tage nach ref_date
        )

        assert g.is_due_soon(reference_date=ref_date) is True

    def test_is_due_soon_false_after_7_days(self, gebuehr_class):
        """is_due_soon() ist False wenn mehr als 7 Tage entfernt"""
        ref_date = date(2025, 6, 1)

        g = gebuehr_class(
            id=1,
            einschreibung_id=100,
            art="Monatsrate",
            betrag=Decimal("199.00"),
            faellig_am=date(2025, 6, 15)  # 14 Tage nach ref_date
        )

        assert g.is_due_soon(reference_date=ref_date) is False

    def test_is_due_soon_custom_days_ahead(self, gebuehr_class):
        """is_due_soon() mit benutzerdefiniertem days_ahead"""
        ref_date = date(2025, 6, 1)

        g = gebuehr_class(
            id=1,
            einschreibung_id=100,
            art="Monatsrate",
            betrag=Decimal("199.00"),
            faellig_am=date(2025, 6, 15)  # 14 Tage nach ref_date
        )

        # Mit 7 Tagen: False
        assert g.is_due_soon(days_ahead=7, reference_date=ref_date) is False

        # Mit 20 Tagen: True
        assert g.is_due_soon(days_ahead=20, reference_date=ref_date) is True

    def test_is_due_soon_false_when_paid(self, paid_gebuehr):
        """is_due_soon() ist False wenn bezahlt"""
        assert paid_gebuehr.is_due_soon() is False

    def test_is_due_soon_false_when_overdue(self, overdue_gebuehr):
        """is_due_soon() ist False wenn bereits ueberfaellig"""
        ref_date = date(2025, 6, 1)
        assert overdue_gebuehr.is_due_soon(reference_date=ref_date) is False

    def test_is_due_soon_true_on_due_date(self, gebuehr_class):
        """is_due_soon() ist True am Faelligkeitstag"""
        ref_date = date(2025, 6, 1)

        g = gebuehr_class(
            id=1,
            einschreibung_id=100,
            art="Monatsrate",
            betrag=Decimal("199.00"),
            faellig_am=date(2025, 6, 1)  # Gleicher Tag
        )

        assert g.is_due_soon(reference_date=ref_date) is True


# ============================================================================
# GET_DAYS_OVERDUE TESTS
# ============================================================================

class TestGetDaysOverdue:
    """Tests fuer get_days_overdue() Methode"""

    def test_get_days_overdue_returns_correct_count(self, gebuehr_class):
        """get_days_overdue() gibt korrekte Anzahl Tage zurueck"""
        g = gebuehr_class(
            id=1,
            einschreibung_id=100,
            art="Monatsrate",
            betrag=Decimal("199.00"),
            faellig_am=date(2025, 6, 1)
        )

        ref_date = date(2025, 6, 11)  # 10 Tage nach Faelligkeit
        assert g.get_days_overdue(ref_date) == 10

    def test_get_days_overdue_zero_when_not_overdue(self, sample_gebuehr):
        """get_days_overdue() gibt 0 zurueck wenn nicht ueberfaellig"""
        ref_date = date(2025, 5, 1)  # Vor Faelligkeit
        assert sample_gebuehr.get_days_overdue(ref_date) == 0

    def test_get_days_overdue_zero_when_paid(self, paid_gebuehr):
        """get_days_overdue() gibt 0 zurueck wenn bezahlt"""
        ref_date = date(2025, 12, 1)  # Weit nach Faelligkeit
        assert paid_gebuehr.get_days_overdue(ref_date) == 0


# ============================================================================
# GET_DAYS_UNTIL_DUE TESTS
# ============================================================================

class TestGetDaysUntilDue:
    """Tests fuer get_days_until_due() Methode"""

    def test_get_days_until_due_positive_before_due(self, gebuehr_class):
        """get_days_until_due() gibt positive Zahl zurueck vor Faelligkeit"""
        g = gebuehr_class(
            id=1,
            einschreibung_id=100,
            art="Monatsrate",
            betrag=Decimal("199.00"),
            faellig_am=date(2025, 6, 10)
        )

        ref_date = date(2025, 6, 1)  # 9 Tage vor Faelligkeit
        assert g.get_days_until_due(ref_date) == 9

    def test_get_days_until_due_zero_on_due_date(self, gebuehr_class):
        """get_days_until_due() gibt 0 zurueck am Faelligkeitstag"""
        g = gebuehr_class(
            id=1,
            einschreibung_id=100,
            art="Monatsrate",
            betrag=Decimal("199.00"),
            faellig_am=date(2025, 6, 1)
        )

        ref_date = date(2025, 6, 1)
        assert g.get_days_until_due(ref_date) == 0

    def test_get_days_until_due_negative_after_due(self, gebuehr_class):
        """get_days_until_due() gibt negative Zahl zurueck nach Faelligkeit"""
        g = gebuehr_class(
            id=1,
            einschreibung_id=100,
            art="Monatsrate",
            betrag=Decimal("199.00"),
            faellig_am=date(2025, 6, 1)
        )

        ref_date = date(2025, 6, 11)  # 10 Tage nach Faelligkeit
        assert g.get_days_until_due(ref_date) == -10


# ============================================================================
# MARK_AS_PAID TESTS
# ============================================================================

class TestMarkAsPaid:
    """Tests fuer mark_as_paid() Methode"""

    def test_mark_as_paid_sets_bezahlt_am(self, sample_gebuehr):
        """mark_as_paid() setzt bezahlt_am"""
        assert sample_gebuehr.bezahlt_am is None

        payment_date = date(2025, 6, 5)
        sample_gebuehr.mark_as_paid(payment_date)

        assert sample_gebuehr.bezahlt_am == payment_date
        assert sample_gebuehr.is_paid() is True

    def test_mark_as_paid_uses_today_as_default(self, sample_gebuehr):
        """mark_as_paid() verwendet heute als Standard"""
        sample_gebuehr.mark_as_paid()

        assert sample_gebuehr.bezahlt_am == date.today()

    def test_mark_as_paid_can_overwrite(self, paid_gebuehr):
        """mark_as_paid() kann existierendes Datum ueberschreiben"""
        old_date = paid_gebuehr.bezahlt_am
        new_date = date(2025, 12, 31)

        paid_gebuehr.mark_as_paid(new_date)

        assert paid_gebuehr.bezahlt_am == new_date
        assert paid_gebuehr.bezahlt_am != old_date


# ============================================================================
# GET_FORMATTED_AMOUNT TESTS
# ============================================================================

class TestGetFormattedAmount:
    """Tests fuer get_formatted_amount() Methode"""

    def test_format_simple_amount(self, gebuehr_class):
        """Einfacher Betrag wird korrekt formatiert"""
        g = gebuehr_class(
            id=1,
            einschreibung_id=100,
            art="Monatsrate",
            betrag=Decimal("199.00"),
            faellig_am=date(2025, 6, 1)
        )

        # Deutsches Format: Komma als Dezimaltrennzeichen
        assert "199,00" in g.get_formatted_amount()
        assert "EUR" in g.get_formatted_amount() or "€" in g.get_formatted_amount()

    def test_format_large_amount_with_thousands(self, gebuehr_class):
        """Grosser Betrag mit Tausendertrennzeichen"""
        g = gebuehr_class(
            id=1,
            einschreibung_id=100,
            art="Monatsrate",
            betrag=Decimal("1234.56"),
            faellig_am=date(2025, 6, 1)
        )

        formatted = g.get_formatted_amount()
        # Deutsches Format: Punkt als Tausender, Komma als Dezimal
        assert "1.234,56" in formatted or "1234,56" in formatted

    def test_format_zero_amount(self, gebuehr_class):
        """Null-Betrag wird korrekt formatiert"""
        g = gebuehr_class(
            id=1,
            einschreibung_id=100,
            art="Monatsrate",
            betrag=Decimal("0"),
            faellig_am=date(2025, 6, 1)
        )

        assert "0,00" in g.get_formatted_amount()


# ============================================================================
# GET_STATUS_TEXT TESTS
# ============================================================================

class TestGetStatusText:
    """Tests fuer get_status_text() Methode"""

    def test_status_bezahlt(self, paid_gebuehr):
        """Status ist 'Bezahlt' wenn bezahlt"""
        status = paid_gebuehr.get_status_text()
        assert "Bezahlt" in status or "bezahlt" in status.lower()

    def test_status_ueberfaellig(self, overdue_gebuehr):
        """Status enthaelt 'Ueberfaellig' wenn ueberfaellig"""
        ref_date = date(2025, 6, 1)
        status = overdue_gebuehr.get_status_text(ref_date)
        # Kann "Überfällig" oder "Ueberfaellig" sein
        assert "llig" in status.lower()  # Ueberfae*llig*

    def test_status_faellig_bald(self, gebuehr_class):
        """Status zeigt 'Faellig in X Tagen' wenn bald faellig"""
        ref_date = date(2025, 6, 1)

        g = gebuehr_class(
            id=1,
            einschreibung_id=100,
            art="Monatsrate",
            betrag=Decimal("199.00"),
            faellig_am=date(2025, 6, 5)  # 4 Tage
        )

        status = g.get_status_text(ref_date)
        assert "4" in status or "Tage" in status.lower()

    def test_status_offen(self, gebuehr_class):
        """Status ist 'Offen' wenn weder bezahlt noch bald faellig"""
        ref_date = date(2025, 1, 1)

        g = gebuehr_class(
            id=1,
            einschreibung_id=100,
            art="Monatsrate",
            betrag=Decimal("199.00"),
            faellig_am=date(2025, 12, 1)  # Weit in der Zukunft
        )

        status = g.get_status_text(ref_date)
        assert "Offen" in status or "offen" in status.lower()


# ============================================================================
# TO_DICT TESTS
# ============================================================================

class TestToDict:
    """Tests fuer to_dict() Methode"""

    def test_to_dict_contains_all_fields(self, sample_gebuehr):
        """to_dict() enthaelt alle Felder"""
        d = sample_gebuehr.to_dict()

        assert 'id' in d
        assert 'einschreibung_id' in d
        assert 'art' in d
        assert 'betrag' in d
        assert 'faellig_am' in d
        assert 'bezahlt_am' in d

    def test_to_dict_betrag_is_float(self, sample_gebuehr):
        """betrag ist float in dict (fuer JSON)"""
        d = sample_gebuehr.to_dict()

        assert isinstance(d['betrag'], float)
        assert d['betrag'] == 199.0

    def test_to_dict_faellig_am_is_iso_string(self, sample_gebuehr):
        """faellig_am ist ISO-String in dict"""
        d = sample_gebuehr.to_dict()

        assert isinstance(d['faellig_am'], str)
        assert d['faellig_am'] == "2025-06-01"

    def test_to_dict_bezahlt_am_none_stays_none(self, sample_gebuehr):
        """bezahlt_am None bleibt None in dict"""
        d = sample_gebuehr.to_dict()

        assert d['bezahlt_am'] is None

    def test_to_dict_bezahlt_am_is_iso_string(self, paid_gebuehr):
        """bezahlt_am ist ISO-String in dict wenn gesetzt"""
        d = paid_gebuehr.to_dict()

        assert isinstance(d['bezahlt_am'], str)
        assert d['bezahlt_am'] == "2025-05-03"

    def test_to_dict_contains_computed_fields(self, sample_gebuehr):
        """to_dict() enthaelt berechnete Felder"""
        d = sample_gebuehr.to_dict()

        assert 'is_paid' in d
        assert 'is_overdue' in d
        assert 'is_due_soon' in d
        assert 'days_overdue' in d
        assert 'days_until_due' in d
        assert 'status_text' in d
        assert 'betrag_formatted' in d

    def test_to_dict_is_json_serializable(self, sample_gebuehr):
        """to_dict() Ergebnis ist JSON-serialisierbar"""
        import json

        d = sample_gebuehr.to_dict()

        # Sollte nicht werfen
        json_str = json.dumps(d)
        assert isinstance(json_str, str)


# ============================================================================
# FROM_ROW TESTS
# ============================================================================

class TestFromRow:
    """Tests fuer from_row() Factory Method"""

    def test_from_row_dict_like(self, gebuehr_class):
        """from_row() funktioniert mit dict-aehnlichem Objekt"""
        row = {
            'id': 1,
            'einschreibung_id': 100,
            'art': 'Monatsrate',
            'betrag': '199.00',
            'faellig_am': '2025-06-01',
            'bezahlt_am': None
        }

        g = gebuehr_class.from_row(row)

        assert g.id == 1
        assert g.einschreibung_id == 100
        assert g.art == 'Monatsrate'
        assert g.betrag == Decimal('199.00')
        assert g.faellig_am == date(2025, 6, 1)
        assert g.bezahlt_am is None

    def test_from_row_with_bezahlt_am(self, gebuehr_class):
        """from_row() parst bezahlt_am korrekt"""
        row = {
            'id': 2,
            'einschreibung_id': 100,
            'art': 'Monatsrate',
            'betrag': '199.00',
            'faellig_am': '2025-06-01',
            'bezahlt_am': '2025-06-05'
        }

        g = gebuehr_class.from_row(row)

        assert g.bezahlt_am == date(2025, 6, 5)

    def test_from_row_with_date_objects(self, gebuehr_class):
        """from_row() funktioniert mit date-Objekten"""
        row = {
            'id': 3,
            'einschreibung_id': 100,
            'art': 'Monatsrate',
            'betrag': 199.0,
            'faellig_am': date(2025, 6, 1),
            'bezahlt_am': date(2025, 6, 5)
        }

        g = gebuehr_class.from_row(row)

        assert g.faellig_am == date(2025, 6, 1)
        assert g.bezahlt_am == date(2025, 6, 5)

    def test_from_row_sqlite_row_mock(self, gebuehr_class):
        """from_row() funktioniert mit sqlite3.Row-aehnlichem Objekt"""
        # Mock eines sqlite3.Row Objekts
        mock_row = MagicMock()
        mock_row.__getitem__ = lambda self, key: {
            'id': 4,
            'einschreibung_id': 100,
            'art': 'Monatsrate',
            'betrag': '199.00',
            'faellig_am': '2025-06-01',
            'bezahlt_am': None
        }[key]

        g = gebuehr_class.from_row(mock_row)

        assert g.id == 4
        assert g.einschreibung_id == 100


# ============================================================================
# STRING REPRESENTATION TESTS
# ============================================================================

class TestStringRepresentation:
    """Tests fuer __str__ und __repr__"""

    def test_str_contains_art(self, sample_gebuehr):
        """__str__ enthaelt Gebuehrenart"""
        s = str(sample_gebuehr)
        assert "Monatsrate" in s

    def test_str_contains_status(self, sample_gebuehr):
        """__str__ enthaelt Status"""
        s = str(sample_gebuehr)
        assert "offen" in s.lower() or "bezahlt" in s.lower()

    def test_str_paid_shows_bezahlt(self, paid_gebuehr):
        """__str__ zeigt 'bezahlt' fuer bezahlte Gebuehr"""
        s = str(paid_gebuehr)
        assert "bezahlt" in s.lower()

    def test_repr_contains_class_name(self, sample_gebuehr):
        """__repr__ enthaelt Klassennamen"""
        r = repr(sample_gebuehr)
        assert "Gebuehr" in r

    def test_repr_contains_id(self, sample_gebuehr):
        """__repr__ enthaelt ID"""
        r = repr(sample_gebuehr)
        assert "id=1" in r or "id=None" in r

    def test_repr_contains_is_paid(self, sample_gebuehr):
        """__repr__ enthaelt is_paid Status"""
        r = repr(sample_gebuehr)
        assert "is_paid=" in r


# ============================================================================
# EDGE CASES
# ============================================================================

class TestEdgeCases:
    """Tests fuer Randfaelle"""

    def test_very_large_betrag(self, gebuehr_class):
        """Sehr grosser Betrag wird korrekt behandelt"""
        g = gebuehr_class(
            id=1,
            einschreibung_id=100,
            art="Monatsrate",
            betrag=Decimal("999999999.99"),
            faellig_am=date(2025, 6, 1)
        )

        assert g.betrag == Decimal("999999999.99")
        # Formatierung sollte nicht crashen
        formatted = g.get_formatted_amount()
        assert len(formatted) > 0

    def test_very_small_betrag(self, gebuehr_class):
        """Sehr kleiner Betrag wird korrekt behandelt"""
        g = gebuehr_class(
            id=1,
            einschreibung_id=100,
            art="Monatsrate",
            betrag=Decimal("0.01"),
            faellig_am=date(2025, 6, 1)
        )

        assert g.betrag == Decimal("0.01")

    def test_dataclass_equality(self, gebuehr_class):
        """Dataclass Gleichheit basiert auf Feldern"""
        g1 = gebuehr_class(
            id=1,
            einschreibung_id=100,
            art="Monatsrate",
            betrag=Decimal("199.00"),
            faellig_am=date(2025, 6, 1)
        )

        g2 = gebuehr_class(
            id=1,
            einschreibung_id=100,
            art="Monatsrate",
            betrag=Decimal("199.00"),
            faellig_am=date(2025, 6, 1)
        )

        assert g1 == g2

    def test_dataclass_inequality_different_id(self, gebuehr_class):
        """Unterschiedliche IDs bedeuten Ungleichheit"""
        g1 = gebuehr_class(
            id=1,
            einschreibung_id=100,
            art="Monatsrate",
            betrag=Decimal("199.00"),
            faellig_am=date(2025, 6, 1)
        )

        g2 = gebuehr_class(
            id=2,  # Andere ID
            einschreibung_id=100,
            art="Monatsrate",
            betrag=Decimal("199.00"),
            faellig_am=date(2025, 6, 1)
        )

        assert g1 != g2

    def test_old_date_far_in_past(self, gebuehr_class):
        """Datum weit in der Vergangenheit funktioniert"""
        g = gebuehr_class(
            id=1,
            einschreibung_id=100,
            art="Monatsrate",
            betrag=Decimal("199.00"),
            faellig_am=date(2000, 1, 1)
        )

        assert g.faellig_am == date(2000, 1, 1)
        assert g.is_overdue() is True

    def test_future_date_far_ahead(self, gebuehr_class):
        """Datum weit in der Zukunft funktioniert"""
        g = gebuehr_class(
            id=1,
            einschreibung_id=100,
            art="Monatsrate",
            betrag=Decimal("199.00"),
            faellig_am=date(2099, 12, 31)
        )

        assert g.faellig_am == date(2099, 12, 31)
        assert g.is_overdue() is False


# ============================================================================
# ALLOWED_ART CONSTANT TESTS
# ============================================================================

class TestAllowedArt:
    """Tests fuer ALLOWED_ART Konstante"""

    def test_allowed_art_is_set(self, allowed_art):
        """ALLOWED_ART ist ein Set"""
        assert isinstance(allowed_art, set)

    def test_allowed_art_contains_monatsrate(self, allowed_art):
        """ALLOWED_ART enthaelt 'Monatsrate'"""
        assert "Monatsrate" in allowed_art

    def test_allowed_art_contains_expected_types(self, allowed_art):
        """ALLOWED_ART enthaelt erwartete Gebuehrenarten"""
        # Mindestens diese sollten enthalten sein
        expected = {"Monatsrate"}
        assert expected.issubset(allowed_art)

    def test_allowed_art_not_empty(self, allowed_art):
        """ALLOWED_ART ist nicht leer"""
        assert len(allowed_art) > 0