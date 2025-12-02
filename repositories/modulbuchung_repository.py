# repositories/modulbuchung_repository.py
from __future__ import annotations
import sqlite3
import logging
from typing import List, Optional
from datetime import date
from models import Modulbuchung, Pruefungsleistung

logger = logging.getLogger(__name__)


class ModulbuchungRepository:
    """Repository fÃ¼r Modulbuchung-Datenbankzugriff

    Verantwortlich fÃ¼r:
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
        """PUBLIC: LÃ¤dt eine Modulbuchung anhand der ID

        Returns:
            Modulbuchung oder Pruefungsleistung (polymorphe RÃ¼ckgabe)
        """
        try:
            with self.__get_connection() as con:
                con.row_factory = sqlite3.Row

                # PrÃ¼fe zuerst ob eine Pruefungsleistung existiert
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
        """PUBLIC: LÃ¤dt alle Modulbuchungen eines Studenten

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
            logger.exception(f"Fehler beim Laden der Buchungen fÃ¼r Student {student_id}: {e}")
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
        """PUBLIC: LÃ¶scht eine Modulbuchung

        KOMPOSITION: LÃ¶scht automatisch auch zugehÃ¶rige Pruefungsleistung
        (durch CASCADE in der DB)
        """
        try:
            with self.__get_connection() as con:
                con.execute("DELETE FROM modulbuchung WHERE id = ?", (buchung_id,))
                con.commit()
                return True

        except sqlite3.Error as e:
            logger.exception(f"Fehler beim LÃ¶schen der Buchung {buchung_id}: {e}")
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

    def validate_wahlmodul_booking(
            self,
            einschreibung_id: int,
            modul_id: int,
            studiengang_id: int
    ) -> tuple[bool, str]:
        """PUBLIC: Validiert ob ein Wahlmodul gebucht werden darf

        Regeln:
        - Jedes Modul darf nur einmal gebucht werden (egal welcher Wahlbereich)
        - Pro Wahlbereich darf nur 1 Modul gebucht werden
        - Semester 5, Wahlbereich A: max 1 Modul
        - Semester 6, Wahlbereich B: max 1 Modul
        - Semester 6, Wahlbereich C: max 1 Modul

        Args:
            einschreibung_id: ID der Einschreibung
            modul_id: ID des zu buchenden Moduls
            studiengang_id: ID des Studiengangs

        Returns:
            Tuple (ist_erlaubt, fehlermeldung)
            - (True, "") wenn Buchung erlaubt
            - (False, "Fehlermeldung") wenn nicht erlaubt
        """
        try:
            with self.__get_connection() as con:
                con.row_factory = sqlite3.Row

                # 1. Prüfe ob Modul bereits gebucht
                if self.check_if_booked(einschreibung_id, modul_id):
                    return (False, "Dieses Modul wurde bereits gebucht.")

                # 2. Hole Wahlbereich des zu buchenden Moduls
                modul_info = con.execute(
                    """SELECT sm.semester, sm.wahlbereich, m.name
                       FROM studiengang_modul sm
                       JOIN modul m ON m.id = sm.modul_id
                       WHERE sm.modul_id = ?
                         AND sm.studiengang_id = ?
                         AND sm.wahlbereich IS NOT NULL""",
                    (modul_id, studiengang_id)
                ).fetchone()

                # Kein Wahlmodul -> keine Einschränkung
                if not modul_info:
                    return (True, "")

                wahlbereich = modul_info['wahlbereich']
                semester = modul_info['semester']
                modul_name = modul_info['name']

                # 3. Prüfe ob im gleichen Wahlbereich bereits ein Modul gebucht ist
                bereits_gebucht = con.execute(
                    """SELECT m.name
                       FROM modulbuchung mb
                       JOIN studiengang_modul sm ON sm.modul_id = mb.modul_id
                                                AND sm.studiengang_id = ?
                       JOIN modul m ON m.id = mb.modul_id
                       WHERE mb.einschreibung_id = ?
                         AND sm.wahlbereich = ?
                         AND sm.semester = ?""",
                    (studiengang_id, einschreibung_id, wahlbereich, semester)
                ).fetchone()

                if bereits_gebucht:
                    return (False,
                            f"Im Wahlbereich {wahlbereich} (Semester {semester}) "
                            f"wurde bereits '{bereits_gebucht['name']}' gebucht. "
                            f"Pro Wahlbereich ist nur 1 Modul erlaubt.")

                return (True, "")

        except sqlite3.Error as e:
            logger.exception("Fehler bei Wahlmodul-Validierung")
            raise

    def get_wahlmodul_status(self, einschreibung_id: int, studiengang_id: int) -> dict:
        """PUBLIC: Gibt Übersicht über gebuchte Wahlmodule zurück

        Returns:
            Dict mit Struktur:
            {
                'A': {'semester': 5, 'modul': 'Modulname' oder None, 'gebucht': True/False},
                'B': {'semester': 6, 'modul': 'Modulname' oder None, 'gebucht': True/False},
                'C': {'semester': 6, 'modul': 'Modulname' oder None, 'gebucht': True/False}
            }
        """
        try:
            with self.__get_connection() as con:
                con.row_factory = sqlite3.Row

                # Hole alle gebuchten Wahlmodule
                rows = con.execute(
                    """SELECT sm.wahlbereich, sm.semester, m.name
                       FROM modulbuchung mb
                       JOIN studiengang_modul sm ON sm.modul_id = mb.modul_id
                                                AND sm.studiengang_id = ?
                       JOIN modul m ON m.id = mb.modul_id
                       WHERE mb.einschreibung_id = ?
                         AND sm.wahlbereich IS NOT NULL
                       ORDER BY sm.semester, sm.wahlbereich""",
                    (studiengang_id, einschreibung_id)
                ).fetchall()

                # Initialisiere Status
                status = {
                    'A': {'semester': 5, 'modul': None, 'gebucht': False},
                    'B': {'semester': 6, 'modul': None, 'gebucht': False},
                    'C': {'semester': 6, 'modul': None, 'gebucht': False}
                }

                for row in rows:
                    bereich = row['wahlbereich']
                    if bereich in status:
                        status[bereich]['modul'] = row['name']
                        status[bereich]['gebucht'] = True

                return status

        except sqlite3.Error as e:
            logger.exception("Fehler beim Laden des Wahlmodul-Status")
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