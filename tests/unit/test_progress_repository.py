# repositories/progress_repository.py
from __future__ import annotations
import sqlite3
import logging
from typing import Optional
from decimal import Decimal
from models.progress import Progress
from models.student import Student

logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(name)s: %(message)s')


class ProgressRepository:
    """Repository fÃ¼r Fortschritts-Datenbankzugriff

    Aggregiert Daten aus mehreren Tabellen (modulbuchung, pruefungsleistung, gebuehr)
    und erstellt daraus Progress-Objekte.
    """

    def __init__(self, db_path: str):
        self.db_path = db_path

    # ========== PUBLIC Repository Methods ==========

    def get_progress_for_student(
            self,
            student: Student,
            einschreibung_id: int
    ) -> Progress:
        """PUBLIC: Berechnet den Gesamtfortschritt eines Studierenden

        Args:
            student: Student-Objekt (fÃ¼r Semester-Berechnung)
            einschreibung_id: ID der aktiven Einschreibung

        Returns:
            Progress-Objekt mit allen Kennzahlen
        """
        try:
            with self.__get_connection() as conn:
                # 1. Notendurchschnitt berechnen
                avg_note = self.__calculate_average_grade(conn, einschreibung_id)

                # 2. Anzahl Module zÃ¤hlen
                passed_count = self.__count_passed_modules(conn, einschreibung_id)
                booked_count = self.__count_booked_modules(conn, einschreibung_id)

                # 3. Offene Gebühren summieren
                open_fees = self.__sum_open_fees(conn, einschreibung_id)

                # 4. Aktuelles Semester berechnen - dafür Einschreibung laden
                einschreibung = self.__load_einschreibung(conn, einschreibung_id)
                if einschreibung:
                    from models.einschreibung import Einschreibung
                    # Einschreibungs-Objekt erstellen
                    einschreibung_obj = Einschreibung.from_row(einschreibung)
                    current_semester = student.calculate_semester(einschreibung_obj)
                else:
                    logger.warning(f"Keine Einschreibung mit ID {einschreibung_id} gefunden")
                    current_semester = 1  # Fallback

                # 5. Erwartetes Semester berechnen
                expected_semester = self.__calculate_expected_semester(
                    conn, einschreibung_id, current_semester
                )

                return Progress(
                    student_id=student.id,
                    durchschnittsnote=avg_note,
                    anzahl_bestandene_module=passed_count,
                    anzahl_gebuchte_module=booked_count,
                    offene_gebuehren=open_fees,
                    aktuelles_semester=current_semester,
                    erwartetes_semester=expected_semester
                )

        except sqlite3.Error as err:
            logger.exception("DB-Fehler beim Berechnen des Fortschritts: %s", err)
            raise

    # ========== PRIVATE Helper Methods ==========

    def __get_connection(self) -> sqlite3.Connection:
        """PRIVATE: Erstellt Datenbankverbindung"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def __calculate_average_grade(
            self,
            conn: sqlite3.Connection,
            einschreibung_id: int
    ) -> Optional[Decimal]:
        """PRIVATE: Berechnet Notendurchschnitt (nur Studiengangs-Module)

        Nur bestandene Module mit Note werden berÃ¼cksichtigt.
        WICHTIG: BerÃ¼cksichtigt nur Module die zum Studiengang gehÃ¶ren.
        """
        row = conn.execute(
            """
            SELECT AVG(pl.note) as avg_note
            FROM pruefungsleistung pl
                     JOIN modulbuchung mb ON mb.id = pl.modulbuchung_id
                     JOIN einschreibung e ON mb.einschreibung_id = e.id
                     JOIN studiengang_modul sgm ON sgm.modul_id = mb.modul_id
                AND sgm.studiengang_id = e.studiengang_id
            WHERE mb.einschreibung_id = ?
              AND mb.status = 'bestanden'
              AND pl.note IS NOT NULL
            """,
            (einschreibung_id,)
        ).fetchone()

        if row and row[0] is not None:
            return Decimal(str(row[0]))
        return None

    def __count_passed_modules(
            self,
            conn: sqlite3.Connection,
            einschreibung_id: int
    ) -> int:
        """PRIVATE: ZÃ¤hlt bestandene Module (nur echte Studiengangs-Module)

        WICHTIG: ZÃ¤hlt nur Module die zum Studiengang gehÃ¶ren (in studiengang_modul),
        nicht Test-Module oder andere Module auÃŸerhalb des Studiengangs.
        """
        row = conn.execute(
            """
            SELECT COUNT(*) as count
            FROM modulbuchung mb
                     JOIN einschreibung e ON mb.einschreibung_id = e.id
                     JOIN studiengang_modul sgm ON sgm.modul_id = mb.modul_id
                AND sgm.studiengang_id = e.studiengang_id
            WHERE mb.einschreibung_id = ?
              AND mb.status = 'bestanden'
            """,
            (einschreibung_id,)
        ).fetchone()

        return int(row[0]) if row else 0

    def __count_booked_modules(
            self,
            conn: sqlite3.Connection,
            einschreibung_id: int
    ) -> int:
        """PRIVATE: ZÃ¤hlt gebuchte Module (inkl. bestanden, nur Studiengangs-Module)

        WICHTIG: ZÃ¤hlt nur Module die zum Studiengang gehÃ¶ren (in studiengang_modul),
        nicht Test-Module oder andere Module auÃŸerhalb des Studiengangs.
        """
        row = conn.execute(
            """
            SELECT COUNT(*) as count
            FROM modulbuchung mb
                     JOIN einschreibung e ON mb.einschreibung_id = e.id
                     JOIN studiengang_modul sgm ON sgm.modul_id = mb.modul_id
                AND sgm.studiengang_id = e.studiengang_id
            WHERE mb.einschreibung_id = ?
              AND mb.status IN ('gebucht', 'bestanden')
            """,
            (einschreibung_id,)
        ).fetchone()

        return int(row[0]) if row else 0

    def __sum_open_fees(
            self,
            conn: sqlite3.Connection,
            einschreibung_id: int
    ) -> Decimal:
        """PRIVATE: Summiert offene GebÃ¼hren"""
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

    def __calculate_expected_semester(
            self,
            conn: sqlite3.Connection,
            einschreibung_id: int,
            current_semester: float
    ) -> float:
        """PRIVATE: Berechnet erwartetes Semester basierend auf bestandenen Modulen

        Logik:
        - Semester 1-6: RegulÃ¤re Module (~7 Module pro Semester)
        - Semester 7: Bachelorarbeit (Abschlusssemester)
        - Berechnung: (48 Module / 7 Semester = ~6.86 â‰ˆ 7 Module pro Semester)

        WICHTIG: ZÃ¤hlt nur echte Studiengangs-Module (48), keine Test-Module!
        """
        passed_count = self.__count_passed_modules(conn, einschreibung_id)

        # Durchschnitt: 48 Module Ã¼ber 7 Semester = ~6.86 â‰ˆ 7 Module pro Semester
        modules_per_semester = 7.0
        expected = (passed_count / modules_per_semester) + 1.0

        # Begrenze auf 1.0 bis 7.0 (7 Semester inkl. Bachelorarbeit)
        return max(1.0, min(7.0, expected))

    def __load_einschreibung(
            self,
            conn: sqlite3.Connection,
            einschreibung_id: int
    ) -> Optional[sqlite3.Row]:
        """PRIVATE: Lädt Einschreibungs-Daten aus der Datenbank

        Args:
            conn: Datenbankverbindung
            einschreibung_id: ID der Einschreibung

        Returns:
            sqlite3.Row mit Einschreibungsdaten oder None
        """
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            """
            SELECT id, student_id, studiengang_id, zeitmodell_id, 
                   start_datum, status
            FROM einschreibung
            WHERE id = ?
            """,
            (einschreibung_id,)
        ).fetchone()
        return row