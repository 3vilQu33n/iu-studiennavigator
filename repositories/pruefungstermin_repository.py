# repositories/pruefungstermin_repository.py
from __future__ import annotations
import sqlite3
import logging
from typing import List, Optional
from datetime import datetime
from models import Pruefungstermin

logger = logging.getLogger(__name__)


class PruefungsterminRepository:
    """Repository für Pruefungstermin-Datenbankzugriff

    Verantwortlich für:
    - CRUD-Operationen auf pruefungstermin-Tabelle
    - Abfragen verfügbarer Termine
    """

    def __init__(self, db_path: str):
        self.db_path = db_path

    # ========== PUBLIC Methods ==========

    def find_by_id(self, termin_id: int) -> Optional[Pruefungstermin]:
        """PUBLIC: Lädt einen Prüfungstermin anhand der ID

        Args:
            termin_id: ID des Prüfungstermins

        Returns:
            Pruefungstermin-Objekt oder None
        """
        try:
            with self.__get_connection() as con:
                con.row_factory = sqlite3.Row

                row = con.execute(
                    """SELECT *
                       FROM pruefungstermin
                       WHERE id = ?""",
                    (termin_id,)
                ).fetchone()

                if row:
                    return Pruefungstermin.from_row(row)

                return None

        except sqlite3.Error as e:
            logger.exception(f"Fehler beim Laden des Prüfungstermins {termin_id}: {e}")
            raise

    def find_by_modul(self, modul_id: int) -> List[Pruefungstermin]:
        """PUBLIC: Lädt alle Prüfungstermine für ein Modul

        Args:
            modul_id: ID des Moduls

        Returns:
            Liste von Pruefungstermin-Objekten
        """
        try:
            with self.__get_connection() as con:
                con.row_factory = sqlite3.Row

                rows = con.execute(
                    """SELECT *
                       FROM pruefungstermin
                       WHERE modul_id = ?
                       ORDER BY datum ASC, beginn ASC""",
                    (modul_id,)
                ).fetchall()

                return [Pruefungstermin.from_row(row) for row in rows]

        except sqlite3.Error as e:
            logger.exception(f"Fehler beim Laden der Prüfungstermine für Modul {modul_id}: {e}")
            raise

    def find_verfuegbare_termine(self, modul_id: int) -> List[Pruefungstermin]:
        """PUBLIC: Lädt verfügbare Prüfungstermine für ein Modul

        Berücksichtigt:
        - Nur Termine in der Zukunft
        - Nur Termine vor Anmeldeschluss
        - Kapazität (falls vorhanden)

        Args:
            modul_id: ID des Moduls

        Returns:
            Liste verfügbarer Pruefungstermin-Objekte
        """
        try:
            with self.__get_connection() as con:
                con.row_factory = sqlite3.Row

                # Aktuelles Datum/Zeit
                jetzt = datetime.now().isoformat()

                rows = con.execute(
                    """SELECT pt.*,
                              COUNT(pa.id) as anmeldungen_count
                       FROM pruefungstermin pt
                                LEFT JOIN pruefungsanmeldung pa
                                          ON pt.id = pa.pruefungstermin_id
                                              AND pa.status = 'angemeldet'
                       WHERE pt.modul_id = ?
                         AND pt.datum >= DATE('now')
                         AND (pt.anmeldeschluss IS NULL OR pt.anmeldeschluss >= ?)
                       GROUP BY pt.id
                       HAVING (pt.kapazitaet IS NULL OR anmeldungen_count < pt.kapazitaet)
                       ORDER BY pt.datum ASC, pt.beginn ASC""",
                    (modul_id, jetzt)
                ).fetchall()

                return [Pruefungstermin.from_row(row) for row in rows]

        except sqlite3.Error as e:
            logger.exception(f"Fehler beim Laden verfügbarer Termine für Modul {modul_id}: {e}")
            raise

    def create(self, termin: Pruefungstermin) -> int:
        """PUBLIC: Erstellt einen neuen Prüfungstermin

        Args:
            termin: Pruefungstermin-Objekt

        Returns:
            ID des neu erstellten Termins
        """
        try:
            with self.__get_connection() as con:
                cursor = con.execute(
                    """INSERT INTO pruefungstermin
                       (modul_id, datum, beginn, ende, art, ort,
                        anmeldeschluss, kapazitaet, beschreibung)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (termin.modul_id,
                     termin.datum,
                     termin.beginn,
                     termin.ende,
                     termin.art,
                     termin.ort,
                     termin.anmeldeschluss,
                     termin.kapazitaet,
                     termin.beschreibung)
                )
                con.commit()
                return cursor.lastrowid

        except sqlite3.Error as e:
            logger.exception(f"Fehler beim Erstellen des Prüfungstermins: {e}")
            raise

    def update(self, termin: Pruefungstermin) -> bool:
        """PUBLIC: Aktualisiert einen Prüfungstermin

        Args:
            termin: Pruefungstermin-Objekt mit aktualisierter ID

        Returns:
            True wenn erfolgreich
        """
        try:
            with self.__get_connection() as con:
                con.execute(
                    """UPDATE pruefungstermin
                       SET modul_id       = ?,
                           datum          = ?,
                           beginn         = ?,
                           ende           = ?,
                           art            = ?,
                           ort            = ?,
                           anmeldeschluss = ?,
                           kapazitaet     = ?,
                           beschreibung   = ?
                       WHERE id = ?""",
                    (termin.modul_id,
                     termin.datum,
                     termin.beginn,
                     termin.ende,
                     termin.art,
                     termin.ort,
                     termin.anmeldeschluss,
                     termin.kapazitaet,
                     termin.beschreibung,
                     termin.id)
                )
                con.commit()
                return True

        except sqlite3.Error as e:
            logger.exception(f"Fehler beim Aktualisieren des Prüfungstermins {termin.id}: {e}")
            raise

    def delete(self, termin_id: int) -> bool:
        """PUBLIC: Löscht einen Prüfungstermin

        Args:
            termin_id: ID des zu löschenden Termins

        Returns:
            True wenn erfolgreich
        """
        try:
            with self.__get_connection() as con:
                con.execute(
                    "DELETE FROM pruefungstermin WHERE id = ?",
                    (termin_id,)
                )
                con.commit()
                return True

        except sqlite3.Error as e:
            logger.exception(f"Fehler beim Löschen des Prüfungstermins {termin_id}: {e}")
            raise

    # ========== PRIVATE Helper Methods ==========

    def __get_connection(self) -> sqlite3.Connection:
        """PRIVATE: Erstellt Datenbankverbindung"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn