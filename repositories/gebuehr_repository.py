# repositories/gebuehr_repository.py
from __future__ import annotations
import sqlite3
import logging
from typing import Optional, List
from datetime import date
from decimal import Decimal
from models import Gebuehr

logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(name)s: %(message)s')


class GebuehrRepository:
    """Repository für Gebühren-Datenbankzugriff

    PUBLIC Methoden werden vom Controller aufgerufen.
    PRIVATE Methoden (__) sind interne Helfer.
    """

    def __init__(self, db_path: str):
        self.db_path = db_path

    # ========== PUBLIC Repository Methods ==========

    def insert(self, gebuehr: Gebuehr) -> int:
        """PUBLIC: Legt eine neue Gebühr an"""
        try:
            with self.__get_connection() as conn:
                cur = conn.execute(
                    """
                    INSERT INTO gebuehr (einschreibung_id, art, betrag, faellig_am, bezahlt_am)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        gebuehr.einschreibung_id,
                        gebuehr.art,
                        str(gebuehr.betrag),
                        gebuehr.faellig_am.isoformat(),
                        gebuehr.bezahlt_am.isoformat() if gebuehr.bezahlt_am else None
                    ),
                )
                conn.commit()
                return int(cur.lastrowid)

        except sqlite3.Error as err:
            logger.exception("DB-Fehler beim Insert gebuehr: %s", err)
            raise

    def get_by_id(self, gebuehr_id: int) -> Optional[Gebuehr]:
        """PUBLIC: Holt Gebühr anhand der ID"""
        try:
            with self.__get_connection() as conn:
                conn.row_factory = sqlite3.Row
                row = conn.execute(
                    "SELECT * FROM gebuehr WHERE id = ?",
                    (gebuehr_id,)
                ).fetchone()

                if not row:
                    return None

                return Gebuehr.from_row(row)

        except sqlite3.Error as err:
            logger.exception("DB-Fehler beim Laden gebuehr: %s", err)
            raise

    def get_by_einschreibung(self, einschreibung_id: int) -> List[Gebuehr]:
        """PUBLIC: Holt alle Gebühren einer Einschreibung"""
        try:
            with self.__get_connection() as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute(
                    """
                    SELECT *
                    FROM gebuehr
                    WHERE einschreibung_id = ?
                    ORDER BY faellig_am DESC
                    """,
                    (einschreibung_id,)
                ).fetchall()

                return [Gebuehr.from_row(row) for row in rows]

        except sqlite3.Error as err:
            logger.exception("DB-Fehler beim Laden der Gebühren: %s", err)
            raise

    def get_open_fees_by_einschreibung(self, einschreibung_id: int) -> List[Gebuehr]:
        """PUBLIC: Holt alle offenen Gebühren einer Einschreibung"""
        try:
            with self.__get_connection() as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute(
                    """
                    SELECT *
                    FROM gebuehr
                    WHERE einschreibung_id = ?
                      AND bezahlt_am IS NULL
                    ORDER BY faellig_am ASC
                    """,
                    (einschreibung_id,)
                ).fetchall()

                return [Gebuehr.from_row(row) for row in rows]

        except sqlite3.Error as err:
            logger.exception("DB-Fehler beim Laden offener Gebühren: %s", err)
            raise

    def calculate_total_open_fees(self, einschreibung_id: int) -> Decimal:
        """PUBLIC: Berechnet Summe aller offenen Gebühren"""
        try:
            with self.__get_connection() as conn:
                row = conn.execute(
                    """
                    SELECT SUM(betrag) as total
                    FROM gebuehr
                    WHERE einschreibung_id = ?
                      AND bezahlt_am IS NULL
                    """,
                    (einschreibung_id,)
                ).fetchone()

                total = row[0] if row and row[0] else 0
                return Decimal(str(total))

        except sqlite3.Error as err:
            logger.exception("DB-Fehler beim Berechnen offener Gebühren: %s", err)
            raise

    def mark_as_paid(
            self,
            gebuehr_id: int,
            payment_date: Optional[date] = None
    ) -> bool:
        """PUBLIC: Markiert eine Gebühr als bezahlt

        Args:
            gebuehr_id: ID der Gebühr
            payment_date: Zahlungsdatum (default: heute)

        Returns:
            True wenn erfolgreich, False wenn Gebühr nicht gefunden
        """
        try:
            paid_date = payment_date or date.today()

            with self.__get_connection() as conn:
                cur = conn.execute(
                    "UPDATE gebuehr SET bezahlt_am = ? WHERE id = ?",
                    (paid_date.isoformat(), gebuehr_id)
                )
                conn.commit()
                return cur.rowcount > 0

        except sqlite3.Error as err:
            logger.exception("DB-Fehler beim Markieren als bezahlt: %s", err)
            raise

    def get_overdue_fees_by_einschreibung(self, einschreibung_id: int) -> List[Gebuehr]:
        """PUBLIC: Holt alle überfälligen Gebühren"""
        try:
            with self.__get_connection() as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute(
                    """
                    SELECT *
                    FROM gebuehr
                    WHERE einschreibung_id = ?
                      AND bezahlt_am IS NULL
                      AND faellig_am < date('now')
                    ORDER BY faellig_am ASC
                    """,
                    (einschreibung_id,)
                ).fetchall()

                return [Gebuehr.from_row(row) for row in rows]

        except sqlite3.Error as err:
            logger.exception("DB-Fehler beim Laden überfälliger Gebühren: %s", err)
            raise

    def ensure_monthly_fees(self) -> int:
        """PUBLIC: Erzeugt Gebühreneinträge idempotent

        Generiert automatisch Monatsraten für alle aktiven Einschreibungen.
        Vergangene Monate werden als bezahlt markiert, der aktuelle Monat bleibt offen.

        Returns:
            Anzahl der neu eingefügten Datensätze
        """
        inserted = 0
        try:
            with self.__get_connection() as con:
                # Vergangene Monate – automatisch bezahlt
                con.executescript("""
                                  WITH RECURSIVE m(einschr_id, zeitmodell_id, monat)
                                                     AS (SELECT id, zeitmodell_id, date(strftime('%Y-%m-01', start_datum))
                                                         FROM einschreibung
                                                         WHERE status = 'aktiv'
                                                         UNION ALL
                                                         SELECT einschr_id, zeitmodell_id, date(monat, '+1 month')
                                                         FROM m
                                                         WHERE date(monat, '+1 month') < date('now', 'start of month'))
                                  INSERT
                                  OR
                                  IGNORE
                                  INTO gebuehr (einschreibung_id, art, betrag, faellig_am, bezahlt_am)
                                  SELECT m.einschr_id, 'Monatsrate', z.kosten_monat, m.monat, m.monat
                                  FROM m
                                           JOIN zeitmodell z ON z.id = m.zeitmodell_id;
                                  """)
                inserted += con.total_changes

                # Aktueller Monat – offen
                con.executescript("""
                                  INSERT OR IGNORE INTO gebuehr (einschreibung_id, art, betrag, faellig_am)
                                  SELECT e.id, 'Monatsrate', z.kosten_monat, date('now', 'start of month')
                                  FROM einschreibung e
                                           JOIN zeitmodell z ON z.id = e.zeitmodell_id
                                  WHERE e.status = 'aktiv';
                                  """)
                inserted += con.total_changes

            return inserted
        except sqlite3.Error as err:
            logger.exception("Fehler beim Erzeugen der Gebühren: %s", err)
            raise

    # ========== PRIVATE Helper Methods ==========

    def __get_connection(self) -> sqlite3.Connection:
        """PRIVATE: Erstellt Datenbankverbindung"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn