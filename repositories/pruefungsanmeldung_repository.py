# repositories/pruefungsanmeldung_repository.py
from __future__ import annotations
import sqlite3
import logging
from typing import List, Optional
from datetime import datetime
from models import Pruefungsanmeldung

logger = logging.getLogger(__name__)


class PruefungsanmeldungRepository:
    """Repository für Pruefungsanmeldung-Datenbankzugriff

    Verantwortlich für:
    - CRUD-Operationen auf pruefungsanmeldung-Tabelle
    - Statusverwaltung von Anmeldungen
    - Kapazitätsprüfung
    """

    def __init__(self, db_path: str):
        self.db_path = db_path

    # ========== PUBLIC Methods ==========

    def find_by_id(self, anmeldung_id: int) -> Optional[Pruefungsanmeldung]:
        """PUBLIC: Lädt eine Prüfungsanmeldung anhand der ID

        Args:
            anmeldung_id: ID der Prüfungsanmeldung

        Returns:
            Pruefungsanmeldung-Objekt oder None
        """
        try:
            with self.__get_connection() as con:
                con.row_factory = sqlite3.Row

                row = con.execute(
                    """SELECT *
                       FROM pruefungsanmeldung
                       WHERE id = ?""",
                    (anmeldung_id,)
                ).fetchone()

                if row:
                    return Pruefungsanmeldung.from_row(row)

                return None

        except sqlite3.Error as e:
            logger.exception(f"Fehler beim Laden der Prüfungsanmeldung {anmeldung_id}: {e}")
            raise

    def find_by_modulbuchung(self, modulbuchung_id: int) -> Optional[Pruefungsanmeldung]:
        """PUBLIC: Lädt Prüfungsanmeldung für eine Modulbuchung

        Args:
            modulbuchung_id: ID der Modulbuchung

        Returns:
            Pruefungsanmeldung-Objekt oder None
        """
        try:
            with self.__get_connection() as con:
                con.row_factory = sqlite3.Row

                row = con.execute(
                    """SELECT *
                       FROM pruefungsanmeldung
                       WHERE modulbuchung_id = ?
                       ORDER BY angemeldet_am DESC
                       LIMIT 1""",
                    (modulbuchung_id,)
                ).fetchone()

                if row:
                    return Pruefungsanmeldung.from_row(row)

                return None

        except sqlite3.Error as e:
            logger.exception(f"Fehler beim Laden der Anmeldung für Modulbuchung {modulbuchung_id}: {e}")
            raise

    def find_by_student(self, einschreibung_id: int) -> List[Pruefungsanmeldung]:
        """PUBLIC: Lädt alle Prüfungsanmeldungen eines Studenten

        Args:
            einschreibung_id: ID der Einschreibung

        Returns:
            Liste von Pruefungsanmeldung-Objekten
        """
        try:
            with self.__get_connection() as con:
                con.row_factory = sqlite3.Row

                rows = con.execute(
                    """SELECT pa.*
                       FROM pruefungsanmeldung pa
                                JOIN modulbuchung mb ON pa.modulbuchung_id = mb.id
                       WHERE mb.einschreibung_id = ?
                       ORDER BY pa.angemeldet_am DESC""",
                    (einschreibung_id,)
                ).fetchall()

                return [Pruefungsanmeldung.from_row(row) for row in rows]

        except sqlite3.Error as e:
            logger.exception(f"Fehler beim Laden der Anmeldungen für Student {einschreibung_id}: {e}")
            raise

    def find_by_termin(self, termin_id: int) -> List[Pruefungsanmeldung]:
        """PUBLIC: Lädt alle Anmeldungen für einen Prüfungstermin

        Args:
            termin_id: ID des Prüfungstermins

        Returns:
            Liste von Pruefungsanmeldung-Objekten
        """
        try:
            with self.__get_connection() as con:
                con.row_factory = sqlite3.Row

                rows = con.execute(
                    """SELECT *
                       FROM pruefungsanmeldung
                       WHERE pruefungstermin_id = ?
                       ORDER BY angemeldet_am ASC""",
                    (termin_id,)
                ).fetchall()

                return [Pruefungsanmeldung.from_row(row) for row in rows]

        except sqlite3.Error as e:
            logger.exception(f"Fehler beim Laden der Anmeldungen für Termin {termin_id}: {e}")
            raise

    def create(self, anmeldung: Pruefungsanmeldung) -> int:
        """PUBLIC: Erstellt eine neue Prüfungsanmeldung

        Args:
            anmeldung: Pruefungsanmeldung-Objekt

        Returns:
            ID der neu erstellten Anmeldung
        """
        try:
            with self.__get_connection() as con:
                # Setze angemeldet_am auf jetzt, falls nicht gesetzt
                angemeldet_am = anmeldung.angemeldet_am or datetime.now()

                cursor = con.execute(
                    """INSERT INTO pruefungsanmeldung
                           (modulbuchung_id, pruefungstermin_id, status, angemeldet_am)
                       VALUES (?, ?, ?, ?)""",
                    (anmeldung.modulbuchung_id,
                     anmeldung.pruefungstermin_id,
                     anmeldung.status,
                     angemeldet_am)
                )
                con.commit()
                return cursor.lastrowid

        except sqlite3.Error as e:
            logger.exception(f"Fehler beim Erstellen der Prüfungsanmeldung: {e}")
            raise

    def update_status(self, anmeldung_id: int, status: str) -> bool:
        """PUBLIC: Aktualisiert den Status einer Prüfungsanmeldung

        Args:
            anmeldung_id: ID der Anmeldung
            status: Neuer Status ('angemeldet', 'storniert', 'absolviert')

        Returns:
            True wenn erfolgreich
        """
        try:
            with self.__get_connection() as con:
                con.execute(
                    """UPDATE pruefungsanmeldung
                       SET status = ?
                       WHERE id = ?""",
                    (status, anmeldung_id)
                )
                con.commit()
                return True

        except sqlite3.Error as e:
            logger.exception(f"Fehler beim Aktualisieren des Status: {e}")
            raise

    def stornieren(self, anmeldung_id: int) -> bool:
        """PUBLIC: Storniert eine Prüfungsanmeldung

        Setzt den Status auf 'storniert'.

        Args:
            anmeldung_id: ID der Anmeldung

        Returns:
            True wenn erfolgreich
        """
        return self.update_status(anmeldung_id, 'storniert')

    def anzahl_anmeldungen_fuer_termin(self, termin_id: int) -> int:
        """PUBLIC: Zählt aktive Anmeldungen für einen Termin

        Zählt nur Anmeldungen mit status='angemeldet'.

        Args:
            termin_id: ID des Prüfungstermins

        Returns:
            Anzahl aktiver Anmeldungen
        """
        try:
            with self.__get_connection() as con:
                row = con.execute(
                    """SELECT COUNT(*) as count
                       FROM pruefungsanmeldung
                       WHERE pruefungstermin_id = ?
                         AND status = 'angemeldet'""",
                    (termin_id,)
                ).fetchone()

                return row[0] if row else 0

        except sqlite3.Error as e:
            logger.exception(f"Fehler beim Zählen der Anmeldungen für Termin {termin_id}: {e}")
            raise

    def hat_aktive_anmeldung(self, modulbuchung_id: int) -> bool:
        """PUBLIC: Prüft ob eine aktive Anmeldung für Modulbuchung existiert

        Args:
            modulbuchung_id: ID der Modulbuchung

        Returns:
            True wenn aktive Anmeldung existiert
        """
        try:
            with self.__get_connection() as con:
                row = con.execute(
                    """SELECT id
                       FROM pruefungsanmeldung
                       WHERE modulbuchung_id = ?
                         AND status = 'angemeldet'
                       LIMIT 1""",
                    (modulbuchung_id,)
                ).fetchone()

                return row is not None

        except sqlite3.Error as e:
            logger.exception("Fehler beim Prüfen der aktiven Anmeldung")
            raise

    # ========== PRIVATE Helper Methods ==========

    def __get_connection(self) -> sqlite3.Connection:
        """PRIVATE: Erstellt Datenbankverbindung"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn