#!/usr/bin/env python3
# tasks/generate_fees.py
"""
Task zum Generieren von Monatsgebühren

Dieses Script generiert automatisch Monatsgebühren für alle aktiven Einschreibungen.
- Vergangene Monate werden als bezahlt markiert
- Der aktuelle Monat bleibt offen
- Kann mehrfach ausgeführt werden (idempotent)

Usage:
    python tasks/generate_fees.py

Oder als Cronjob (täglich um 0:00 Uhr):
    0 0 * * * cd /path/to/dashboardProject && python tasks/generate_fees.py
"""

import sys
from pathlib import Path
import logging

# Füge das Parent-Verzeichnis zum Python-Path hinzu
sys.path.insert(0, str(Path(__file__).parent.parent))

from repositories import GebuehrRepository

# Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Datenbank-Pfad
DB_PATH = Path(__file__).parent.parent / 'dashboard.db'


def generate_monthly_fees():
    """Generiert fehlende Monatsgebühren für alle aktiven Einschreibungen

    Returns:
        int: Anzahl der neu generierten Gebühren
    """
    try:
        if not DB_PATH.exists():
            logger.error(f"❌ Datenbank nicht gefunden: {DB_PATH}")
            return 0

        logger.info(f"📊 Starte Gebühren-Generierung für: {DB_PATH}")

        repo = GebuehrRepository(str(DB_PATH))
        inserted = repo.ensure_monthly_fees()

        if inserted > 0:
            logger.info(f"✅ {inserted} neue Monatsgebühren generiert")
        else:
            logger.info(f"ℹ️  Keine neuen Gebühren erforderlich (alle aktuell)")

        return inserted

    except Exception as e:
        logger.exception(f"❌ Fehler beim Generieren der Gebühren: {e}")
        raise


if __name__ == '__main__':
    try:
        count = generate_monthly_fees()
        logger.info(f"🎉 Task erfolgreich abgeschlossen! ({count} Gebühren generiert)")
        sys.exit(0)
    except Exception:
        logger.error("💥 Task fehlgeschlagen!")
        sys.exit(1)