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
    """Repository für Fortschritts-Datenbankzugriff

    Aggregiert Daten aus mehreren Tabellen (modulbuchung, pruefungsleistung, gebuehr)
    und erstellt daraus Progress-Objekte.

    WICHTIG: Unterscheidung der Semester-Berechnungen:
    - aktuelles_semester = FORTSCHRITT (basierend auf bestandenen Modulen) → für Pfad-Position
    - erwartetes_semester = ZEIT (basierend auf Einschreibedatum + Zeitmodell) → für Progress-Texte
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
            student: Student-Objekt (für Semester-Berechnung)
            einschreibung_id: ID der aktiven Einschreibung

        Returns:
            Progress-Objekt mit allen Kennzahlen
        """
        try:
            with self.__get_connection() as conn:
                # 1. Notendurchschnitt berechnen
                avg_note = self.__calculate_average_grade(conn, einschreibung_id)

                # 2. Anzahl Module zählen
                passed_count = self.__count_passed_modules(conn, einschreibung_id)
                booked_count = self.__count_booked_modules(conn, einschreibung_id)

                # 3. Offene Gebühren summieren
                open_fees = self.__sum_open_fees(conn, einschreibung_id)

                # 4. ✅ AKTUELLES SEMESTER = FORTSCHRITT (wo ist der Student mit Modulen?)
                # Berechnet basierend auf Anzahl bestandener Module
                # → Wird für PFAD-POSITION verwendet
                current_semester = self.__calculate_progress_based_semester(conn, einschreibung_id)

                # 5. ✅ ERWARTETES SEMESTER = ZEIT (wo sollte der Student zeitlich sein?)
                # Berechnet basierend auf Einschreibedatum + Zeitmodell
                # → Wird für PROGRESS-TEXTE verwendet
                einschreibung = self.__load_einschreibung(conn, einschreibung_id)
                if einschreibung:
                    from models.einschreibung import Einschreibung
                    einschreibung_obj = Einschreibung.from_row(einschreibung)
                    expected_semester = student.calculate_semester(einschreibung_obj)
                else:
                    logger.warning(f"Keine Einschreibung mit ID {einschreibung_id} gefunden")
                    expected_semester = 1.0  # Fallback

                logger.info(f"📊 Progress: IST={current_semester:.1f} (Module), SOLL={expected_semester:.1f} (Zeit)")

                return Progress(
                    student_id=student.id,
                    durchschnittsnote=avg_note,
                    anzahl_bestandene_module=passed_count,
                    anzahl_gebuchte_module=booked_count,
                    offene_gebuehren=open_fees,
                    aktuelles_semester=current_semester,  # ✅ Fortschritt (für Pfad)
                    erwartetes_semester=expected_semester  # ✅ Zeit (für Texte)
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

    @staticmethod
    def __calculate_average_grade(
            conn: sqlite3.Connection,
            einschreibung_id: int
    ) -> Optional[Decimal]:
        """PRIVATE: Berechnet Notendurchschnitt (nur Studiengangs-Module)

        Nur bestandene Module mit Note werden berücksichtigt.
        WICHTIG: Berücksichtigt nur Module die zum Studiengang gehören.
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

    @staticmethod
    def __count_passed_modules(
            conn: sqlite3.Connection,
            einschreibung_id: int
    ) -> int:
        """PRIVATE: Zählt bestandene Module (nur echte Studiengangs-Module)

        WICHTIG: Zählt nur Module die zum Studiengang gehören (in studiengang_modul),
        nicht Test-Module oder andere Module außerhalb des Studiengangs.
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

    @staticmethod
    def __count_booked_modules(
            conn: sqlite3.Connection,
            einschreibung_id: int
    ) -> int:
        """PRIVATE: Zählt gebuchte Module (inkl. bestanden, nur Studiengangs-Module)

        WICHTIG: Zählt nur Module die zum Studiengang gehören (in studiengang_modul),
        nicht Test-Module oder andere Module außerhalb des Studiengangs.
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

    @staticmethod
    def __sum_open_fees(
            conn: sqlite3.Connection,
            einschreibung_id: int
    ) -> Decimal:
        """PRIVATE: Summiert offene Gebühren"""
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

    def __calculate_progress_based_semester(
            self,
            conn: sqlite3.Connection,
            einschreibung_id: int
    ) -> float:
        """PRIVATE: Berechnet FORTSCHRITTS-Semester basierend auf bestandenen Modulen

        Dies ist das AKTUELLE Semester für die Pfad-Position!

        Logik:
        - Semester 1-6: Reguläre Module (~7 Module pro Semester)
        - Semester 7: Bachelorarbeit (Abschlusssemester)
        - Berechnung: (48 Module / 7 Semester = ~6.86 ≈ 7 Module pro Semester)

        WICHTIG: Zählt nur echte Studiengangs-Module (48), keine Test-Module!

        Args:
            conn: Datenbankverbindung
            einschreibung_id: ID der Einschreibung

        Returns:
            Fortschritts-Semester als float (1.0 bis 7.0)
        """
        passed_count = self.__count_passed_modules(conn, einschreibung_id)

        # Durchschnitt: 48 Module über 7 Semester = ~6.86 ≈ 7 Module pro Semester
        modules_per_semester = 7.0
        progress_semester = (passed_count / modules_per_semester) + 1.0

        # Begrenze auf 1.0 bis 7.0 (7 Semester inkl. Bachelorarbeit)
        return max(1.0, min(7.0, progress_semester))

    @staticmethod
    def __load_einschreibung(
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
            SELECT id,
                   student_id,
                   studiengang_id,
                   zeitmodell_id,
                   start_datum,
                   status
            FROM einschreibung
            WHERE id = ?
            """,
            (einschreibung_id,)
        ).fetchone()
        return row