# tests/unit/test_progress_text_service.py
"""
Unit Tests fÃ¼r ProgressTextService

Testet die Text-Generierung basierend auf Progress-Daten.
"""
import pytest
import json
from pathlib import Path
from decimal import Decimal
from datetime import date
from services import ProgressTextService
from models import Progress


@pytest.fixture
def sample_progress():
    """Erstellt ein Test-Progress-Objekt"""
    return Progress(
        student_id=1,
        durchschnittsnote=Decimal('2.0'),
        anzahl_bestandene_module=10,
        anzahl_gebuchte_module=15,
        offene_gebuehren=Decimal('199.00'),
        aktuelles_semester=2.5,  # ✅ Korrigiert: Student ist in Sem 2.5
        erwartetes_semester=3.0  # ✅ Sollte in Sem 3 sein → 0.5 Sem voraus = +90 Tage
    )


@pytest.fixture
def temp_progress_json(tmp_path):
    """Erstellt eine temporÃ¤re progress.json"""
    json_content = {
        "grade": {
            "fast": {
                "de": "ðŸ“Š %{value} â€“ Stabile Fahrt auf der Ãœberholspur",
                "en": "ðŸ“Š %{value} â€“ Cruising in the fast lane"
            },
            "medium": {
                "de": "ðŸ“Š %{value} â€“ Voll im Zeitplan",
                "en": "ðŸ“Š %{value} â€“ Right on schedule"
            },
            "slow": {
                "de": "ðŸ“Š %{value} â€“ Ich schalte einen Gang hÃ¶her!",
                "en": "ðŸ“Š %{value} â€“ Time to shift up a gear!"
            },
            "unknown": {
                "de": "ðŸ“Š Noch keine Noten",
                "en": "ðŸ“Š No grades yet"
            }
        },
        "time": {
            "plus": {
                "de": "âš¡ +%{days} Tage Puffer im Vergleich zum Zeitplan",
                "en": "âš¡ +%{days} days buffer â€“ Cruise mode"
            },
            "minus": {
                "de": "âš¡ -%{days} Tage Verzug â€“ DC-Schnellladen erforderlich!",
                "en": "âš¡ -%{days} days â€“ Floor it!"
            },
            "ahead": {
                "de": "âš¡ +%{days} Tage voraus â€“ Akku vollgeladen!",
                "en": "âš¡ +%{days} days ahead â€“ Battery fully charged!"
            }
        },
        "fee": {
            "zero": {
                "de": "ðŸ”‹ Alle GebÃ¼hren beglichen",
                "en": "ðŸ”‹ All fees paid"
            },
            "open": {
                "de": "ðŸ”‹ %{amount} GebÃ¼hren offen",
                "en": "ðŸ”‹ %{amount} fees outstanding"
            }
        }
    }

    json_file = tmp_path / "progress.json"
    json_file.write_text(json.dumps(json_content, ensure_ascii=False, indent=2))
    return json_file


# ========== Initialization Tests ==========

def test_init_with_default_path():
    """Test: Service initialisiert mit Standard-Pfad"""
    service = ProgressTextService()
    assert service.json_path is not None
    assert service.texts is not None


def test_init_with_custom_path(temp_progress_json):
    """Test: Service initialisiert mit custom Pfad"""
    service = ProgressTextService(json_path=temp_progress_json)
    assert service.json_path == temp_progress_json
    assert 'grade' in service.texts
    assert 'time' in service.texts
    assert 'fee' in service.texts


def test_init_with_missing_json():
    """Test: Service verwendet Fallback wenn JSON fehlt"""
    service = ProgressTextService(json_path=Path("/nicht/existent.json"))

    # Fallback-Texte sollten geladen sein
    assert service.texts is not None
    assert 'grade' in service.texts
    assert 'fast' in service.texts['grade']


# ========== Grade Text Tests ==========

def test_get_grade_text_fast(temp_progress_json, sample_progress):
    """Test: Grade-Text fÃ¼r 'fast' Kategorie"""
    sample_progress.durchschnittsnote = Decimal('1.5')
    service = ProgressTextService(json_path=temp_progress_json)

    text = service.get_grade_text(sample_progress, 'de')

    assert "1.5" in text
    assert "Ãœberholspur" in text


def test_get_grade_text_medium(temp_progress_json, sample_progress):
    """Test: Grade-Text fÃ¼r 'medium' Kategorie"""
    sample_progress.durchschnittsnote = Decimal('2.5')
    service = ProgressTextService(json_path=temp_progress_json)

    text = service.get_grade_text(sample_progress, 'de')

    assert "2.5" in text
    assert "Zeitplan" in text


def test_get_grade_text_slow(temp_progress_json, sample_progress):
    """Test: Grade-Text fÃ¼r 'slow' Kategorie"""
    sample_progress.durchschnittsnote = Decimal('3.5')
    service = ProgressTextService(json_path=temp_progress_json)

    text = service.get_grade_text(sample_progress, 'de')

    assert "3.5" in text
    assert "Gang hÃ¶her" in text


def test_get_grade_text_unknown(temp_progress_json, sample_progress):
    """Test: Grade-Text ohne Noten"""
    sample_progress.durchschnittsnote = None
    service = ProgressTextService(json_path=temp_progress_json)

    text = service.get_grade_text(sample_progress, 'de')

    assert "Noch keine Noten" in text


def test_get_grade_text_english(temp_progress_json, sample_progress):
    """Test: Grade-Text auf Englisch"""
    sample_progress.durchschnittsnote = Decimal('1.5')
    service = ProgressTextService(json_path=temp_progress_json)

    text = service.get_grade_text(sample_progress, 'en')

    assert "1.5" in text
    assert "fast lane" in text


# ========== Time Text Tests ==========

def test_get_time_text_ahead(temp_progress_json, sample_progress):
    """Test: Time-Text wenn voraus"""
    # aktuelles_semester=3, erwartet=2.5 â†’ 0.5 Semester = ~60 Tage voraus
    service = ProgressTextService(json_path=temp_progress_json)

    text = service.get_time_text(sample_progress, 'de')

    assert "Tage voraus" in text or "Tage Puffer" in text


def test_get_time_text_behind(temp_progress_json, sample_progress):
    """Test: Time-Text wenn im Verzug"""
    sample_progress.aktuelles_semester = 4
    sample_progress.erwartetes_semester = 3.0
    service = ProgressTextService(json_path=temp_progress_json)

    text = service.get_time_text(sample_progress, 'de')

    assert "Verzug" in text or "days" in text


def test_get_time_text_english(temp_progress_json, sample_progress):
    """Test: Time-Text auf Englisch"""
    service = ProgressTextService(json_path=temp_progress_json)

    text = service.get_time_text(sample_progress, 'en')

    assert "days" in text


# ========== Fee Text Tests ==========

def test_get_fee_text_zero(temp_progress_json, sample_progress):
    """Test: Fee-Text ohne offene GebÃ¼hren"""
    sample_progress.offene_gebuehren = Decimal('0')
    service = ProgressTextService(json_path=temp_progress_json)

    text = service.get_fee_text(sample_progress, 'de')

    assert "beglichen" in text or "paid" in text


def test_get_fee_text_open(temp_progress_json, sample_progress):
    """Test: Fee-Text mit offenen GebÃ¼hren"""
    sample_progress.offene_gebuehren = Decimal('199.00')
    service = ProgressTextService(json_path=temp_progress_json)

    text = service.get_fee_text(sample_progress, 'de')

    assert "199,00" in text or "199.00" in text
    assert "offen" in text or "outstanding" in text


def test_get_fee_text_english(temp_progress_json, sample_progress):
    """Test: Fee-Text auf Englisch"""
    sample_progress.offene_gebuehren = Decimal('199.00')
    service = ProgressTextService(json_path=temp_progress_json)

    text = service.get_fee_text(sample_progress, 'en')

    assert "outstanding" in text


# ========== get_all_texts Tests ==========

def test_get_all_texts_complete(temp_progress_json, sample_progress):
    """Test: Alle Texte auf einmal generieren"""
    service = ProgressTextService(json_path=temp_progress_json)

    result = service.get_all_texts(sample_progress, 'de')

    assert 'grade' in result
    assert 'time' in result
    assert 'fee' in result
    assert 'category' in result
    assert 'time_status' in result


def test_get_all_texts_category_correct(temp_progress_json, sample_progress):
    """Test: Kategorie wird korrekt zurÃ¼ckgegeben"""
    sample_progress.durchschnittsnote = Decimal('1.5')
    service = ProgressTextService(json_path=temp_progress_json)

    result = service.get_all_texts(sample_progress, 'de')

    assert result['category'] == 'fast'


def test_get_all_texts_time_status(temp_progress_json, sample_progress):
    """Test: Time-Status wird korrekt zurÃ¼ckgegeben"""
    service = ProgressTextService(json_path=temp_progress_json)

    result = service.get_all_texts(sample_progress, 'de')

    assert result['time_status'] in ['plus', 'minus', 'ahead']


# ========== Integration Tests ==========

def test_full_workflow_excellent_student(temp_progress_json):
    """Test: Kompletter Workflow fÃ¼r exzellenten Studenten"""
    # Sehr guter Student
    progress = Progress(
        student_id=1,
        durchschnittsnote=Decimal('1.3'),
        anzahl_bestandene_module=20,
        anzahl_gebuchte_module=25,
        offene_gebuehren=Decimal('0'),
        aktuelles_semester=3,
        erwartetes_semester=4.0
    )

    service = ProgressTextService(json_path=temp_progress_json)
    result = service.get_all_texts(progress, 'de')

    # Grade: fast
    assert result['category'] == 'fast'
    assert "1.3" in result['grade']

    # Fees: zero
    assert "beglichen" in result['fee']

    # Zeit: ahead
    assert "Tage voraus" in result['time'] or "Puffer" in result['time']


def test_full_workflow_struggling_student(temp_progress_json):
    """Test: Kompletter Workflow fÃ¼r Studenten mit Schwierigkeiten"""
    # Student mit Problemen
    progress = Progress(
        student_id=1,
        durchschnittsnote=Decimal('3.7'),
        anzahl_bestandene_module=5,
        anzahl_gebuchte_module=10,
        offene_gebuehren=Decimal('598.00'),
        aktuelles_semester=4,
        erwartetes_semester=2.5
    )

    service = ProgressTextService(json_path=temp_progress_json)
    result = service.get_all_texts(progress, 'de')

    # Grade: slow
    assert result['category'] == 'slow'
    assert "3.7" in result['grade']

    # Fees: open
    assert "598" in result['fee']

    # Zeit: behind
    assert "Verzug" in result['time']


# ========== Edge Cases ==========

def test_placeholder_replacement_correct(temp_progress_json, sample_progress):
    """Test: Platzhalter werden korrekt ersetzt"""
    service = ProgressTextService(json_path=temp_progress_json)

    grade_text = service.get_grade_text(sample_progress, 'de')

    # Platzhalter sollte nicht mehr im Text sein
    assert '%{value}' not in grade_text
    assert "2.0" in grade_text


def test_handles_none_gracefully(temp_progress_json, sample_progress):
    """Test: Service behandelt None-Werte korrekt"""
    sample_progress.durchschnittsnote = None
    service = ProgressTextService(json_path=temp_progress_json)

    # Sollte nicht crashen
    text = service.get_grade_text(sample_progress, 'de')
    assert text is not None