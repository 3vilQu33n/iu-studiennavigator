# repositories/modulbuchung_repository.py
from __future__ import annotations
import sqlite3
import logging
from typing import List, Optional
from datetime import date
from models import Modulbuchung, Pruefungsleistung

logger = logging.getLogger(__name__)


class ModulbuchungRepository:
    """Repository für Modulbuchung-Datenbankzugriff

    Verantwortlich für:
    - CRUD-Operationen auf modulbuchung-Tabelle
    - Polymorphe Behandlung von Modulbuchung und Pruefungsleistung
    """

    def __init__(self, db_path: str):
        self.db_path = db_path

    # ========== PUBLIC Methods ==========

    def create(self, buchung: Modulbuchung) -> int:
        """PUBLIC: Erstellt eine neue Modulbuchung

        Args:
            buchung: Modulbuchung-Objekt (kann auch Pruefungsleistung sein)

        Returns:
            ID der neu erstellten Buchung
        """
        try:
            with self.__get_connection() as con:
                cursor = con.execute(
                    """INSERT INTO modulbuchung
                           (einschreibung_id, modul_id, buchungsdatum, status)
                       VALUES (?, ?, ?, ?)""",
                    (buchung.einschreibung_id,
                     buchung.modul_id,
                     buchung.buchungsdatum or date.today(),
                     buchung.status)
                )

                # Wenn es eine Pruefungsleistung ist, erstelle auch den Eintrag in pruefungsleistung
                buchung_id = cursor.lastrowid

                if isinstance(buchung, Pruefungsleistung):
                    self.__create_pruefungsleistung(con, buchung_id, buchung)

                con.commit()
                return buchung_id

        except sqlite3.Error as e:
            logger.exception(f"Fehler beim Erstellen der Modulbuchung: {e}")
            raise

    def get_by_id(self, buchung_id: int) -> Optional[Modulbuchung]:
        """PUBLIC: Lädt eine Modulbuchung anhand der ID

        Returns:
            Modulbuchung oder Pruefungsleistung (polymorphe Rückgabe)
        """
        try:
            with self.__get_connection() as con:
                con.row_factory = sqlite3.Row

                # Prüfe zuerst ob eine Pruefungsleistung existiert
                pl_row = con.execute(
                    """SELECT pl.*,
                              mb.einschreibung_id,
                              mb.modul_id,
                              mb.buchungsdatum,
                              mb.status
                       FROM pruefungsleistung pl
                                JOIN modulbuchung mb ON pl.id = mb.id
                       WHERE pl.id = ?""",
                    (buchung_id,)
                ).fetchone()

                if pl_row:
                    return Pruefungsleistung.from_row(pl_row)

                # Ansonsten normale Modulbuchung
                mb_row = con.execute(
                    """SELECT *
                       FROM modulbuchung
                       WHERE id = ?""",
                    (buchung_id,)
                ).fetchone()

                if mb_row:
                    return Modulbuchung.from_row(mb_row)

                return None

        except sqlite3.Error as e:
            logger.exception(f"Fehler beim Laden der Modulbuchung {buchung_id}: {e}")
            raise

    def get_by_student(self, student_id: int) -> List[Modulbuchung]:
        """PUBLIC: Lädt alle Modulbuchungen eines Studenten

        Returns:
            Liste mit Modulbuchung und/oder Pruefungsleistung-Objekten
        """
        try:
            with self.__get_connection() as con:
                con.row_factory = sqlite3.Row

                rows = con.execute(
                    """SELECT mb.*,
                              pl.note,
                              pl.pruefungsdatum,
                              pl.versuch,
                              pl.max_versuche,
                              pl.anmeldemodus,
                              pl.thema
                       FROM modulbuchung mb
                                JOIN einschreibung e ON mb.einschreibung_id = e.id
                                LEFT JOIN pruefungsleistung pl ON pl.id = mb.id
                       WHERE e.student_id = ?
                       ORDER BY mb.buchungsdatum DESC""",
                    (student_id,)
                ).fetchall()

                result = []
                for row in rows:
                    # Wenn eine Note vorhanden ist, ist es eine Pruefungsleistung
                    if row['note'] is not None:
                        result.append(Pruefungsleistung.from_row(row))
                    else:
                        result.append(Modulbuchung.from_row(row))

                return result

        except sqlite3.Error as e:
            logger.exception(f"Fehler beim Laden der Buchungen für Student {student_id}: {e}")
            raise

    def update_status(self, buchung_id: int, new_status: str) -> bool:
        """PUBLIC: Aktualisiert den Status einer Modulbuchung

        Args:
            buchung_id: ID der Buchung
            new_status: Neuer Status ('gebucht', 'bestanden', etc.)

        Returns:
            True wenn erfolgreich
        """
        try:
            with self.__get_connection() as con:
                con.execute(
                    """UPDATE modulbuchung
                       SET status = ?
                       WHERE id = ?""",
                    (new_status, buchung_id)
                )
                con.commit()
                return True

        except sqlite3.Error as e:
            logger.exception(f"Fehler beim Aktualisieren des Status: {e}")
            raise

    def delete(self, buchung_id: int) -> bool:
        """PUBLIC: Löscht eine Modulbuchung

        KOMPOSITION: Löscht automatisch auch zugehörige Pruefungsleistung
        (durch CASCADE in der DB)
        """
        try:
            with self.__get_connection() as con:
                con.execute("DELETE FROM modulbuchung WHERE id = ?", (buchung_id,))
                con.commit()
                return True

        except sqlite3.Error as e:
            logger.exception(f"Fehler beim Löschen der Buchung {buchung_id}: {e}")
            raise

    def check_if_booked(self, einschreibung_id: int, modul_id: int) -> bool:
        """PUBLIC: Prüft ob ein Modul bereits gebucht wurde

        Returns:
            True wenn bereits gebucht
        """
        try:
            with self.__get_connection() as con:
                row = con.execute(
                    """SELECT id
                       FROM modulbuchung
                       WHERE einschreibung_id = ?
                         AND modul_id = ?""",
                    (einschreibung_id, modul_id)
                ).fetchone()

                return row is not None

        except sqlite3.Error as e:
            logger.exception("Fehler beim Prüfen der Buchung")
            raise

    # ========== PRIVATE Helper Methods ==========

    def __create_pruefungsleistung(
            self,
            con: sqlite3.Connection,
            buchung_id: int,
            pruefung: Pruefungsleistung
    ) -> None:
        """PRIVATE: Erstellt Eintrag in pruefungsleistung-Tabelle"""
        con.execute(
            """INSERT INTO pruefungsleistung
                   (id, note, pruefungsdatum, versuch, max_versuche, anmeldemodus, thema)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (buchung_id,
             float(pruefung.note) if pruefung.note else None,
             pruefung.pruefungsdatum,
             pruefung.versuch,
             pruefung.max_versuche,
             pruefung.anmeldemodus,
             pruefung.thema)
        )

    def __get_connection(self) -> sqlite3.Connection:
        """PRIVATE: Erstellt Datenbankverbindung"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn