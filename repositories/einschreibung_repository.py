# repositories/einschreibung_repository.py
from __future__ import annotations
import sqlite3
import logging
from typing import Optional
from models import (
    Einschreibung,
    Status,
    EinschreibungError,
    ValidationError,
    DatabaseError,
    NotFoundError
)

logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(name)s: %(message)s')


class EinschreibungRepository:
    """Repository für Einschreibungs-Datenbankzugriff

    Alle Methoden sind PUBLIC, da sie vom Controller aufgerufen werden.
    Private Hilfsmethoden bekommen __ Prefix.
    """

    def __init__(self, db_path: str):
        self.db_path = db_path

    # ========== PUBLIC Repository Methods ==========

    def insert(self, einschreibung: Einschreibung) -> int:
        """PUBLIC: Legt eine Einschreibung an und gibt die neue ID zurück"""
        try:
            einschreibung.validate()

            with self.__get_connection() as conn:
                cur = conn.execute(
                    """
                    INSERT INTO einschreibung (student_id, studiengang_id, zeitmodell_id, start_datum, exmatrikulations_datum, status)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        einschreibung.student_id,
                        einschreibung.studiengang_id,
                        einschreibung.zeitmodell_id,
                        einschreibung.start_datum.isoformat(),
                        einschreibung.exmatrikulations_datum.isoformat() if einschreibung.exmatrikulations_datum else None,
                        einschreibung.status
                    ),
                )
                conn.commit()
                return int(cur.lastrowid)

        except sqlite3.IntegrityError as err:
            logger.exception("Integritätsfehler beim Insert einschreibung: %s", err)
            raise DatabaseError(f"Integritätsfehler beim Anlegen: {err}") from err
        except sqlite3.Error as err:
            logger.exception("DB-Fehler beim Insert einschreibung: %s", err)
            raise DatabaseError(f"DB-Fehler beim Anlegen: {err}") from err

    def get_by_id(self, einschreibung_id: int) -> Einschreibung:
        """PUBLIC: Holt Einschreibung anhand der ID"""
        try:
            with self.__get_connection() as conn:
                conn.row_factory = sqlite3.Row
                row = conn.execute(
                    "SELECT * FROM einschreibung WHERE id = ?",
                    (einschreibung_id,)
                ).fetchone()

                if not row:
                    raise NotFoundError(f"Einschreibung {einschreibung_id} nicht gefunden")

                return Einschreibung.from_row(row)

        except sqlite3.Error as err:
            logger.exception("DB-Fehler beim Laden einschreibung: %s", err)
            raise DatabaseError(f"DB-Fehler beim Laden: {err}") from err

    def get_aktive_by_student(self, student_id: int) -> Einschreibung:
        """PUBLIC: Holt aktive Einschreibung eines Studierenden"""
        try:
            with self.__get_connection() as conn:
                conn.row_factory = sqlite3.Row
                row = conn.execute(
                    """
                    SELECT *
                    FROM einschreibung
                    WHERE student_id = ?
                      AND status = 'aktiv'
                    ORDER BY start_datum DESC
                    LIMIT 1
                    """,
                    (student_id,),
                ).fetchone()

                if not row:
                    raise NotFoundError(f"Keine aktive Einschreibung für Student {student_id} gefunden")

                return Einschreibung.from_row(row)

        except sqlite3.Error as err:
            logger.exception("DB-Fehler bei Abfrage aktive Einschreibung: %s", err)
            raise DatabaseError(f"DB-Fehler bei Abfrage: {err}") from err

    def update_status(self, einschreibung_id: int, neuer_status: Status) -> None:
        """PUBLIC: Ändert den Status einer Einschreibung"""
        if neuer_status not in ("aktiv", "pausiert", "exmatrikuliert"):
            raise ValidationError("Ungültiger Status")

        try:
            with self.__get_connection() as conn:
                cur = conn.execute(
                    "UPDATE einschreibung SET status = ? WHERE id = ?",
                    (neuer_status, einschreibung_id)
                )

                if cur.rowcount == 0:
                    raise NotFoundError(f"Einschreibung {einschreibung_id} nicht gefunden")

                conn.commit()

        except sqlite3.Error as err:
            logger.exception("DB-Fehler beim Status-Update: %s", err)
            raise DatabaseError(f"DB-Fehler beim Status-Update: {err}") from err

    def wechsel_zeitmodell(self, einschreibung_id: int, neues_zeitmodell_id: int) -> None:
        """PUBLIC: Wechselt das Zeitmodell einer Einschreibung"""
        if not isinstance(neues_zeitmodell_id, int) or neues_zeitmodell_id <= 0:
            raise ValidationError("neues_zeitmodell_id muss eine positive Integer-ID sein")

        try:
            with self.__get_connection() as conn:
                cur = conn.execute(
                    "UPDATE einschreibung SET zeitmodell_id = ? WHERE id = ?",
                    (neues_zeitmodell_id, einschreibung_id)
                )

                if cur.rowcount == 0:
                    raise NotFoundError(f"Einschreibung {einschreibung_id} nicht gefunden")

                conn.commit()

        except sqlite3.Error as err:
            logger.exception("DB-Fehler beim Zeitmodell-Wechsel: %s", err)
            raise DatabaseError(f"DB-Fehler beim Zeitmodell-Wechsel: {err}") from err

    def get_all_by_student(self, student_id: int) -> list[Einschreibung]:
        """PUBLIC: Holt alle Einschreibungen eines Studierenden"""
        try:
            with self.__get_connection() as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute(
                    """
                    SELECT *
                    FROM einschreibung
                    WHERE student_id = ?
                    ORDER BY start_datum DESC
                    """,
                    (student_id,),
                ).fetchall()

                return [Einschreibung.from_row(row) for row in rows]

        except sqlite3.Error as err:
            logger.exception("DB-Fehler beim Laden aller Einschreibungen: %s", err)
            raise DatabaseError(f"DB-Fehler beim Laden: {err}") from err

    # ========== PRIVATE Helper Methods ==========

    def __get_connection(self) -> sqlite3.Connection:
        """PRIVATE: Erstellt Datenbankverbindung"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn