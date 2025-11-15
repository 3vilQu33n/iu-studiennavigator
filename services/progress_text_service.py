# services/progress_text_service.py
from __future__ import annotations
import json
import logging
from pathlib import Path
from typing import Optional
from models import Progress

logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(name)s: %(message)s')


class ProgressTextService:
    """Service für Progress-Text-Generierung

    Lädt progress.json und generiert dynamische Texte basierend auf Progress-Daten.
    """

    def __init__(self, json_path: Optional[Path] = None):
        """
        Args:
            json_path: Pfad zur progress.json (default: ./progress.json)
        """
        if json_path is None:
            json_path = Path(__file__).parent.parent / 'progress.json'

        self.json_path = json_path
        self.texts = self.__load_texts()

    # ========== PUBLIC Methods ==========

    def get_grade_text(self, progress: Progress, lang: str = 'de') -> str:
        """PUBLIC: Generiert Text für Notenstatus

        Args:
            progress: Progress-Objekt
            lang: Sprache ('de' oder 'en')

        Returns:
            Formatierter Text mit Platzhaltern ersetzt
        """
        category = progress.to_dict()['grade_category']

        # Prüfe ob Kategorie existiert
        if category not in self.texts['grade']:
            logger.warning(f"Grade category '{category}' nicht in progress.json gefunden!")
            return "Noch keine Noten" if lang == 'de' else "No grades yet"

        template = self.texts['grade'][category][lang]

        # Platzhalter ersetzen (nur wenn %{value} im Template vorhanden)
        if '%{value}' in template:
            value = f"{progress.durchschnittsnote:.1f}" if progress.durchschnittsnote else "—"
            return template.replace('%{value}', value)
        else:
            # Für 'unknown' Kategorie - kein Platzhalter nötig
            return template

    def get_time_text(self, progress: Progress, lang: str = 'de') -> str:
        """PUBLIC: Generiert Text für Zeitstatus"""
        category = progress.to_dict()['time_category']
        template = self.texts['time'][category][lang]

        # Platzhalter ersetzen
        days = abs(progress.to_dict()['tage_differenz'])
        return template.replace('%{days}', str(days))

    def get_fee_text(self, progress: Progress, lang: str = 'de') -> str:
        """PUBLIC: Generiert Text für Gebührenstatus"""
        category = progress.to_dict()['fee_category']
        template = self.texts['fee'][category][lang]

        # Platzhalter ersetzen
        amount = progress.to_dict()['offene_gebuehren_formatted']
        return template.replace('%{amount}', amount)

    def get_all_texts(self, progress: Progress, lang: str = 'de') -> dict:
        """PUBLIC: Generiert alle Texte auf einmal

        Returns:
            Dictionary mit 'grade', 'time', 'fee', 'category', 'time_status'
        """
        progress_dict = progress.to_dict()

        return {
            'grade': self.get_grade_text(progress, lang),
            'time': self.get_time_text(progress, lang),
            'fee': self.get_fee_text(progress, lang),
            'category': progress_dict['grade_category'],  # Für CSS-Klassen (fast/medium/slow)
            'time_status': progress_dict['time_category']  # Für Icon-Auswahl in dashboard.js
        }

    # ========== PRIVATE Helper Methods ==========

    def __load_texts(self) -> dict:
        """PRIVATE: Lädt progress.json"""
        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"progress.json nicht gefunden: {self.json_path}")
            return self.__get_fallback_texts()
        except json.JSONDecodeError as e:
            logger.error(f"Fehler beim Parsen von progress.json: {e}")
            return self.__get_fallback_texts()

    def __get_fallback_texts(self) -> dict:
        """PRIVATE: Fallback-Texte wenn JSON fehlt"""
        return {
            'grade': {
                'fast': {
                    'de': '📊 %{value} – Stabile Fahrt auf der Überholspur',
                    'en': '📊 %{value} – Cruising in the fast lane'
                },
                'medium': {
                    'de': '📊 %{value} – Voll im Zeitplan',
                    'en': '📊 %{value} – Right on schedule'
                },
                'slow': {
                    'de': '📊 %{value} – Ich schalte einen Gang höher!',
                    'en': '📊 %{value} – Time to shift up a gear!'
                },
                'unknown': {
                    'de': 'Noch keine Noten – Fahrt beginnt!',
                    'en': 'No grades yet – Journey begins!'
                }
            },
            'time': {
                'plus': {
                    'de': '⚡ +%{days} Tage Puffer im Vergleich zum Zeitplan',
                    'en': '⚡ +%{days} days buffer – Cruise mode'
                },
                'minus': {
                    'de': '⚡ -%{days} Tage Verzug – DC-Schnellladen erforderlich!',
                    'en': '⚡ -%{days} days – Floor it!'
                },
                'ahead': {
                    'de': '⚡ +%{days} Tage voraus – Akku vollgeladen!',
                    'en': '⚡ +%{days} days ahead – Battery fully charged!'
                }
            },
            'fee': {
                'zero': {
                    'de': '🔋 Alle Gebühren beglichen',
                    'en': '🔋 All fees paid'
                },
                'open': {
                    'de': '🔋 %{amount} Gebühren offen',
                    'en': '🔋 %{amount} fees outstanding'
                }
            }
        }