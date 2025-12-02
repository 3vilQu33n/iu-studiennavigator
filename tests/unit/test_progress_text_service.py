# tests/unit/test_progress_text_service.py
"""
Unit Tests fuer ProgressTextService (services/progress_text_service.py)

Testet den ProgressTextService:
- __init__() - Initialisierung mit optionalem JSON-Pfad
- get_grade_text() - Text fuer Notenstatus
- get_time_text() - Text fuer Zeitstatus
- get_fee_text() - Text fuer Gebuehrenstatus
- get_all_texts() - Alle Texte auf einmal
- __load_texts() - Laden der JSON
- __get_fallback_texts() - Fallback-Texte wenn JSON fehlt

Besondere Aspekte:
- Platzhalter-Ersetzung (%{value}, %{days}, %{amount})
- Kategorien (fast/medium/slow/unknown, plus/minus/ahead, zero/open)
- Sprachunterstuetzung (de, en)
- Fallback bei fehlender/fehlerhafter JSON
"""
from __future__ import annotations

import pytest
import json
import tempfile
import os
from pathlib import Path
from decimal import Decimal
from unittest.mock import MagicMock, patch

# Mark this whole module as unit tests
pytestmark = pytest.mark.unit


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def progress_text_service_class():
    """Importiert ProgressTextService-Klasse"""
    try:
        from services import ProgressTextService
        return ProgressTextService
    except ImportError:
        from services.progress_text_service import ProgressTextService
        return ProgressTextService


@pytest.fixture
def progress_class():
    """Importiert Progress-Klasse"""
    try:
        from models import Progress
        return Progress
    except ImportError:
        from models.progress import Progress
        return Progress


@pytest.fixture
def sample_json_content():
    """Sample progress.json Inhalt"""
    return {
        'grade': {
            'fast': {
                'de': 'Durchschnitt %{value} - Ueberholspur',
                'en': 'Average %{value} - Fast lane'
            },
            'medium': {
                'de': 'Durchschnitt %{value} - Im Zeitplan',
                'en': 'Average %{value} - On schedule'
            },
            'slow': {
                'de': 'Durchschnitt %{value} - Gang hoeher schalten',
                'en': 'Average %{value} - Shift up'
            },
            'unknown': {
                'de': 'Noch keine Noten',
                'en': 'No grades yet'
            }
        },
        'time': {
            'plus': {
                'de': '+%{days} Tage Puffer',
                'en': '+%{days} days buffer'
            },
            'minus': {
                'de': '-%{days} Tage Verzug',
                'en': '-%{days} days behind'
            },
            'ahead': {
                'de': '+%{days} Tage voraus',
                'en': '+%{days} days ahead'
            }
        },
        'fee': {
            'zero': {
                'de': 'Alle Gebuehren beglichen',
                'en': 'All fees paid'
            },
            'open': {
                'de': '%{amount} offen',
                'en': '%{amount} outstanding'
            }
        }
    }


@pytest.fixture
def temp_json_file(sample_json_content):
    """Erstellt temporaere progress.json"""
    fd, path = tempfile.mkstemp(suffix='.json')
    os.close(fd)

    with open(path, 'w', encoding='utf-8') as f:
        json.dump(sample_json_content, f, ensure_ascii=False)

    yield Path(path)

    # Cleanup
    try:
        os.unlink(path)
    except OSError:
        pass


@pytest.fixture
def service(progress_text_service_class, temp_json_file):
    """Erstellt Service-Instanz mit Test-JSON"""
    return progress_text_service_class(json_path=temp_json_file)


@pytest.fixture
def mock_progress_fast():
    """Mock Progress mit 'fast' grade_category"""
    mock = MagicMock()
    mock.durchschnittsnote = Decimal('1.8')
    mock.to_dict.return_value = {
        'grade_category': 'fast',
        'time_category': 'plus',
        'fee_category': 'zero',
        'tage_differenz': 15,
        'offene_gebuehren_formatted': '0,00 EUR'
    }
    return mock


@pytest.fixture
def mock_progress_medium():
    """Mock Progress mit 'medium' grade_category"""
    mock = MagicMock()
    mock.durchschnittsnote = Decimal('2.3')
    mock.to_dict.return_value = {
        'grade_category': 'medium',
        'time_category': 'plus',
        'fee_category': 'open',
        'tage_differenz': 5,
        'offene_gebuehren_formatted': '359,00 EUR'
    }
    return mock


@pytest.fixture
def mock_progress_slow():
    """Mock Progress mit 'slow' grade_category"""
    mock = MagicMock()
    mock.durchschnittsnote = Decimal('3.5')
    mock.to_dict.return_value = {
        'grade_category': 'slow',
        'time_category': 'minus',
        'fee_category': 'open',
        'tage_differenz': -10,
        'offene_gebuehren_formatted': '718,00 EUR'
    }
    return mock


@pytest.fixture
def mock_progress_unknown():
    """Mock Progress mit 'unknown' grade_category (keine Noten)"""
    mock = MagicMock()
    mock.durchschnittsnote = None
    mock.to_dict.return_value = {
        'grade_category': 'unknown',
        'time_category': 'ahead',
        'fee_category': 'zero',
        'tage_differenz': 30,
        'offene_gebuehren_formatted': '0,00 EUR'
    }
    return mock


# ============================================================================
# INITIALIZATION TESTS
# ============================================================================

class TestProgressTextServiceInit:
    """Tests fuer Service-Initialisierung"""

    def test_init_with_json_path(self, progress_text_service_class, temp_json_file):
        """Service kann mit JSON-Pfad initialisiert werden"""
        service = progress_text_service_class(json_path=temp_json_file)

        assert service.json_path == temp_json_file

    def test_init_loads_texts(self, progress_text_service_class, temp_json_file):
        """Service laedt Texte bei Initialisierung"""
        service = progress_text_service_class(json_path=temp_json_file)

        assert service.texts is not None
        assert 'grade' in service.texts
        assert 'time' in service.texts
        assert 'fee' in service.texts

    def test_init_default_path(self, progress_text_service_class):
        """Service verwendet default Pfad wenn nicht angegeben"""
        # Das koennte fehlschlagen wenn keine progress.json existiert
        # aber sollte Fallback-Texte laden
        service = progress_text_service_class()

        assert service.json_path is not None
        assert service.texts is not None

    def test_init_nonexistent_file_uses_fallback(self, progress_text_service_class):
        """Service verwendet Fallback bei nicht existierender Datei"""
        service = progress_text_service_class(json_path=Path('/nonexistent/path.json'))

        # Fallback-Texte sollten geladen sein
        assert 'grade' in service.texts
        assert 'fast' in service.texts['grade']


# ============================================================================
# GET_GRADE_TEXT TESTS
# ============================================================================

class TestGetGradeText:
    """Tests fuer get_grade_text() Methode"""

    def test_grade_text_fast_de(self, service, mock_progress_fast):
        """get_grade_text() generiert 'fast' Text auf Deutsch"""
        result = service.get_grade_text(mock_progress_fast, lang='de')

        assert '1.8' in result
        assert 'Ueberholspur' in result

    def test_grade_text_fast_en(self, service, mock_progress_fast):
        """get_grade_text() generiert 'fast' Text auf Englisch"""
        result = service.get_grade_text(mock_progress_fast, lang='en')

        assert '1.8' in result
        assert 'Fast lane' in result

    def test_grade_text_medium(self, service, mock_progress_medium):
        """get_grade_text() generiert 'medium' Text"""
        result = service.get_grade_text(mock_progress_medium, lang='de')

        assert '2.3' in result
        assert 'Zeitplan' in result

    def test_grade_text_slow(self, service, mock_progress_slow):
        """get_grade_text() generiert 'slow' Text"""
        result = service.get_grade_text(mock_progress_slow, lang='de')

        assert '3.5' in result
        assert 'Gang' in result or 'hoeher' in result

    def test_grade_text_unknown_no_placeholder(self, service, mock_progress_unknown):
        """get_grade_text() fuer 'unknown' hat keinen Platzhalter"""
        result = service.get_grade_text(mock_progress_unknown, lang='de')

        assert 'Noch keine Noten' in result
        assert '%{value}' not in result

    def test_grade_text_replaces_placeholder(self, service, mock_progress_fast):
        """get_grade_text() ersetzt %{value} Platzhalter"""
        result = service.get_grade_text(mock_progress_fast, lang='de')

        assert '%{value}' not in result

    def test_grade_text_unknown_category_fallback(self, service):
        """get_grade_text() mit unbekannter Kategorie gibt Fallback"""
        mock = MagicMock()
        mock.durchschnittsnote = None
        mock.to_dict.return_value = {'grade_category': 'nonexistent'}

        result = service.get_grade_text(mock, lang='de')

        assert 'Noch keine Noten' in result


# ============================================================================
# GET_TIME_TEXT TESTS
# ============================================================================

class TestGetTimeText:
    """Tests fuer get_time_text() Methode"""

    def test_time_text_plus(self, service, mock_progress_fast):
        """get_time_text() generiert 'plus' Text"""
        result = service.get_time_text(mock_progress_fast, lang='de')

        assert '15' in result
        assert 'Puffer' in result

    def test_time_text_minus(self, service, mock_progress_slow):
        """get_time_text() generiert 'minus' Text"""
        result = service.get_time_text(mock_progress_slow, lang='de')

        assert '10' in result  # abs(-10) = 10
        assert 'Verzug' in result

    def test_time_text_ahead(self, service, mock_progress_unknown):
        """get_time_text() generiert 'ahead' Text"""
        result = service.get_time_text(mock_progress_unknown, lang='de')

        assert '30' in result
        assert 'voraus' in result

    def test_time_text_replaces_days_placeholder(self, service, mock_progress_fast):
        """get_time_text() ersetzt %{days} Platzhalter"""
        result = service.get_time_text(mock_progress_fast, lang='de')

        assert '%{days}' not in result

    def test_time_text_uses_absolute_value(self, service, mock_progress_slow):
        """get_time_text() verwendet absoluten Wert fuer Tage (abs())"""
        # tage_differenz ist -10, abs() macht daraus 10
        # Das Template '-%{days} Tage Verzug' fuegt das Minus hinzu
        # Ergebnis: '-10 Tage Verzug' (Minus aus Template + 10 aus abs())
        result = service.get_time_text(mock_progress_slow, lang='de')

        assert '10' in result
        assert 'Verzug' in result
        # Das Minus kommt aus dem Template, nicht aus dem Wert
        # Wichtig: abs(-10) = 10, Template fuegt '-' hinzu

    def test_time_text_english(self, service, mock_progress_fast):
        """get_time_text() funktioniert auf Englisch"""
        result = service.get_time_text(mock_progress_fast, lang='en')

        assert '15' in result
        assert 'buffer' in result


# ============================================================================
# GET_FEE_TEXT TESTS
# ============================================================================

class TestGetFeeText:
    """Tests fuer get_fee_text() Methode"""

    def test_fee_text_zero(self, service, mock_progress_fast):
        """get_fee_text() generiert 'zero' Text"""
        result = service.get_fee_text(mock_progress_fast, lang='de')

        assert 'beglichen' in result

    def test_fee_text_open(self, service, mock_progress_medium):
        """get_fee_text() generiert 'open' Text mit Betrag"""
        result = service.get_fee_text(mock_progress_medium, lang='de')

        assert '359,00 EUR' in result
        assert 'offen' in result

    def test_fee_text_replaces_amount_placeholder(self, service, mock_progress_medium):
        """get_fee_text() ersetzt %{amount} Platzhalter"""
        result = service.get_fee_text(mock_progress_medium, lang='de')

        assert '%{amount}' not in result

    def test_fee_text_english(self, service, mock_progress_medium):
        """get_fee_text() funktioniert auf Englisch"""
        result = service.get_fee_text(mock_progress_medium, lang='en')

        assert '359,00 EUR' in result
        assert 'outstanding' in result


# ============================================================================
# GET_ALL_TEXTS TESTS
# ============================================================================

class TestGetAllTexts:
    """Tests fuer get_all_texts() Methode"""

    def test_get_all_texts_returns_dict(self, service, mock_progress_fast):
        """get_all_texts() gibt Dictionary zurueck"""
        result = service.get_all_texts(mock_progress_fast, lang='de')

        assert isinstance(result, dict)

    def test_get_all_texts_contains_all_keys(self, service, mock_progress_fast):
        """get_all_texts() enthaelt alle erwarteten Keys"""
        result = service.get_all_texts(mock_progress_fast, lang='de')

        assert 'grade' in result
        assert 'time' in result
        assert 'fee' in result
        assert 'category' in result
        assert 'time_status' in result

    def test_get_all_texts_grade_content(self, service, mock_progress_fast):
        """get_all_texts() 'grade' hat korrekten Inhalt"""
        result = service.get_all_texts(mock_progress_fast, lang='de')

        assert '1.8' in result['grade']

    def test_get_all_texts_time_content(self, service, mock_progress_fast):
        """get_all_texts() 'time' hat korrekten Inhalt"""
        result = service.get_all_texts(mock_progress_fast, lang='de')

        assert '15' in result['time']

    def test_get_all_texts_fee_content(self, service, mock_progress_fast):
        """get_all_texts() 'fee' hat korrekten Inhalt"""
        result = service.get_all_texts(mock_progress_fast, lang='de')

        assert 'beglichen' in result['fee']

    def test_get_all_texts_category(self, service, mock_progress_fast):
        """get_all_texts() 'category' ist grade_category"""
        result = service.get_all_texts(mock_progress_fast, lang='de')

        assert result['category'] == 'fast'

    def test_get_all_texts_time_status(self, service, mock_progress_fast):
        """get_all_texts() 'time_status' ist time_category"""
        result = service.get_all_texts(mock_progress_fast, lang='de')

        assert result['time_status'] == 'plus'

    def test_get_all_texts_english(self, service, mock_progress_fast):
        """get_all_texts() funktioniert auf Englisch"""
        result = service.get_all_texts(mock_progress_fast, lang='en')

        assert 'Fast lane' in result['grade']
        assert 'buffer' in result['time']


# ============================================================================
# PRIVATE METHOD TESTS
# ============================================================================

class TestPrivateMethods:
    """Tests fuer private Hilfsmethoden"""

    def test_load_texts_returns_dict(self, progress_text_service_class, temp_json_file):
        """__load_texts() gibt Dictionary zurueck"""
        service = progress_text_service_class(json_path=temp_json_file)

        assert isinstance(service.texts, dict)

    def test_load_texts_structure(self, progress_text_service_class, temp_json_file):
        """__load_texts() laedt korrekte Struktur"""
        service = progress_text_service_class(json_path=temp_json_file)

        assert 'grade' in service.texts
        assert 'fast' in service.texts['grade']
        assert 'de' in service.texts['grade']['fast']
        assert 'en' in service.texts['grade']['fast']

    def test_get_fallback_texts_structure(self, progress_text_service_class):
        """__get_fallback_texts() hat korrekte Struktur"""
        service = progress_text_service_class(json_path=Path('/nonexistent.json'))

        # Fallback-Texte sollten geladen sein
        assert 'grade' in service.texts
        assert 'time' in service.texts
        assert 'fee' in service.texts

        # Alle Kategorien vorhanden
        assert 'fast' in service.texts['grade']
        assert 'medium' in service.texts['grade']
        assert 'slow' in service.texts['grade']
        assert 'unknown' in service.texts['grade']


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

class TestErrorHandling:
    """Tests fuer Fehlerbehandlung"""

    def test_invalid_json_uses_fallback(self, progress_text_service_class):
        """Service verwendet Fallback bei ungueltigem JSON"""
        # Erstelle Datei mit ungueltigem JSON
        fd, path = tempfile.mkstemp(suffix='.json')
        os.close(fd)

        with open(path, 'w') as f:
            f.write("{ invalid json }")

        try:
            service = progress_text_service_class(json_path=Path(path))

            # Fallback-Texte sollten geladen sein
            assert 'grade' in service.texts
            assert 'fast' in service.texts['grade']
        finally:
            os.unlink(path)

    def test_missing_file_uses_fallback(self, progress_text_service_class):
        """Service verwendet Fallback bei fehlender Datei"""
        service = progress_text_service_class(json_path=Path('/does/not/exist.json'))

        # Fallback-Texte sollten geladen sein
        assert 'grade' in service.texts

    def test_fallback_texts_are_complete(self, progress_text_service_class):
        """Fallback-Texte haben alle nötigen Kategorien"""
        service = progress_text_service_class(json_path=Path('/nonexistent.json'))

        # Grade
        for cat in ['fast', 'medium', 'slow', 'unknown']:
            assert cat in service.texts['grade']
            assert 'de' in service.texts['grade'][cat]
            assert 'en' in service.texts['grade'][cat]

        # Time
        for cat in ['plus', 'minus', 'ahead']:
            assert cat in service.texts['time']
            assert 'de' in service.texts['time'][cat]
            assert 'en' in service.texts['time'][cat]

        # Fee
        for cat in ['zero', 'open']:
            assert cat in service.texts['fee']
            assert 'de' in service.texts['fee'][cat]
            assert 'en' in service.texts['fee'][cat]


# ============================================================================
# INTEGRATION-LIKE TESTS
# ============================================================================

class TestIntegrationScenarios:
    """Tests fuer typische Nutzungsszenarien"""

    def test_dashboard_text_generation(self, service, mock_progress_fast):
        """Test: Dashboard-Text-Generierung"""
        texts = service.get_all_texts(mock_progress_fast, lang='de')

        # Alle Texte sollten vorhanden und formatiert sein
        assert texts['grade'] != ''
        assert texts['time'] != ''
        assert texts['fee'] != ''

        # Keine Platzhalter mehr
        assert '%{' not in texts['grade']
        assert '%{' not in texts['time']
        assert '%{' not in texts['fee']

    def test_bilingual_support(self, service, mock_progress_medium):
        """Test: Zweisprachige Unterstuetzung"""
        texts_de = service.get_all_texts(mock_progress_medium, lang='de')
        texts_en = service.get_all_texts(mock_progress_medium, lang='en')

        # Unterschiedliche Sprachen
        assert texts_de['grade'] != texts_en['grade']
        assert texts_de['time'] != texts_en['time']
        assert texts_de['fee'] != texts_en['fee']

        # Gleiche Kategorien
        assert texts_de['category'] == texts_en['category']
        assert texts_de['time_status'] == texts_en['time_status']

    def test_all_progress_states(self, service, mock_progress_fast, mock_progress_medium,
                                  mock_progress_slow, mock_progress_unknown):
        """Test: Alle Progress-Zustaende"""
        for mock in [mock_progress_fast, mock_progress_medium,
                     mock_progress_slow, mock_progress_unknown]:
            texts = service.get_all_texts(mock, lang='de')

            # Alle Keys vorhanden
            assert 'grade' in texts
            assert 'time' in texts
            assert 'fee' in texts
            assert 'category' in texts
            assert 'time_status' in texts


# ============================================================================
# EDGE CASES
# ============================================================================

class TestEdgeCases:
    """Tests fuer Randfaelle"""

    def test_none_durchschnittsnote(self, service, mock_progress_unknown):
        """Test mit durchschnittsnote = None"""
        # unknown Kategorie hat keinen %{value} Platzhalter
        result = service.get_grade_text(mock_progress_unknown, lang='de')

        assert result is not None
        assert '%{value}' not in result

    def test_zero_tage_differenz(self, service):
        """Test mit tage_differenz = 0"""
        mock = MagicMock()
        mock.durchschnittsnote = Decimal('2.0')
        mock.to_dict.return_value = {
            'grade_category': 'medium',
            'time_category': 'plus',
            'fee_category': 'zero',
            'tage_differenz': 0,
            'offene_gebuehren_formatted': '0,00 EUR'
        }

        result = service.get_time_text(mock, lang='de')

        assert '0' in result

    def test_large_fee_amount(self, service):
        """Test mit grossem Gebuehrenbetrag"""
        mock = MagicMock()
        mock.durchschnittsnote = Decimal('2.5')
        mock.to_dict.return_value = {
            'grade_category': 'medium',
            'time_category': 'minus',
            'fee_category': 'open',
            'tage_differenz': -30,
            'offene_gebuehren_formatted': '15.732,00 EUR'
        }

        result = service.get_fee_text(mock, lang='de')

        assert '15.732,00 EUR' in result

    def test_special_characters_in_amount(self, service):
        """Test mit Sonderzeichen im Betrag"""
        mock = MagicMock()
        mock.durchschnittsnote = Decimal('2.0')
        mock.to_dict.return_value = {
            'grade_category': 'medium',
            'time_category': 'plus',
            'fee_category': 'open',
            'tage_differenz': 5,
            'offene_gebuehren_formatted': '1.234,56 €'
        }

        result = service.get_fee_text(mock, lang='de')

        assert '1.234,56 €' in result