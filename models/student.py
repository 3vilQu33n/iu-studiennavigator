# models/student.py
"""
Domain Model: Student

KOMPOSITION: Student 1 â†’â—† 1 Login
â†’ Jeder Student hat genau einen Login (fÃ¼r das System)
â†’ Login gehÃ¶rt zum Student und stirbt mit ihm

AGGREGATION: Student 1 â†’â—‡ * Einschreibung
â†’ Student hat Einschreibungen, die unabhÃ¤ngig weiter existieren kÃ¶nnen

BEREINIGT: email und start_datum entfernt
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING

# TYPE_CHECKING: Imports nur fÃ¼r Type Hints, nicht zur Laufzeit
# Verhindert zirkulÃ¤re Import-Probleme
if TYPE_CHECKING:
    from einschreibung import Einschreibung


@dataclass
class Student:
    """Domain Model: Student

    ReprÃ¤sentiert einen Studierenden.

    OOP-BEZIEHUNGEN:
    - KOMPOSITION zu Login (Student besitzt Login, Login stirbt mit Student)
    - AGGREGATION zu Einschreibung (Student hat Einschreibungen, die unabhÃ¤ngig leben)

    ENCAPSULATION:
    - PUBLIC: get_full_name(), calculate_semester(), validate(), to_dict(), from_db_row()
    - PRIVATE: __get_display_name()

    Alle Hilfsmethoden sind private (__double_underscore).
    Nur die wichtigsten public-Methoden sind ohne Underscore.

    Attributes:
        id: PrimÃ¤rschlÃ¼ssel
        matrikel_nr: Matrikelnummer (eindeutig)
        vorname: Vorname
        nachname: Nachname
        login_id: FK zum Login (KOMPOSITION - Login gehÃ¶rt zu Student!)
    """
    id: int
    matrikel_nr: str
    vorname: str
    nachname: str
    login_id: Optional[int] = None  # KOMPOSITION: Login gehÃ¶rt zu Student

    # ========== PUBLIC Methods (minimal!) ==========

    def get_full_name(self) -> str:
        """PUBLIC: Gibt vollstÃ¤ndigen Namen zurÃ¼ck"""
        return f"{self.vorname} {self.nachname}"

    def calculate_semester(self, einschreibung: 'Einschreibung') -> int:
        """PUBLIC: Berechnet aktuelles Semester basierend auf Einschreibung

        Args:
            einschreibung: Einschreibungs-Objekt mit start_datum

        Returns:
            Aktuelles Semester (1-basiert)

        Example:
            >>> from models import Einschreibung
            >>> from datetime import date
            >>>
            >>> student = Student(id=1, matrikel_nr="IU12345",
            ...                   vorname="Max", nachname="Muster")
            >>> einschreibung = Einschreibung(
            ...     id=1, student_id=1, studiengang_id=1, zeitmodell_id=1,
            ...     start_datum=date(2024, 1, 1), status='aktiv'
            ... )
            >>>
            >>> # Nach 8 Monaten (September 2024)
            >>> semester = student.calculate_semester(einschreibung)
            >>> print(semester)  # Ausgabe: 2
        """
        months = einschreibung.get_study_duration_months()
        return (months // 6) + 1  # 6 Monate = 1 Semester

    def validate(self) -> tuple[bool, str]:
        """PUBLIC: Validiert Student-Daten

        Returns:
            Tuple aus (is_valid: bool, error_message: str)
        """
        if not self.matrikel_nr or len(self.matrikel_nr) < 5:
            return False, "Matrikelnummer muss mindestens 5 Zeichen haben"

        if not self.vorname or not self.nachname:
            return False, "Vor- und Nachname sind erforderlich"

        return True, ""

    def to_dict(self) -> dict:
        """PUBLIC: Konvertiert zu Dictionary (fÃ¼r JSON/Templates)"""
        return {
            'id': self.id,
            'matrikel_nr': self.matrikel_nr,
            'vorname': self.vorname,
            'nachname': self.nachname,
            'full_name': self.get_full_name(),
            'login_id': self.login_id
        }

    @classmethod
    def from_db_row(cls, row) -> 'Student':
        """PUBLIC: Factory Method - Erstellt Student aus DB-Row

        WICHTIG: sqlite3.Row hat KEINE .get() Methode!
        Stattdessen verwenden wir row['spalte'] mit try/except.

        Args:
            row: sqlite3.Row Objekt aus DB-Query

        Returns:
            Student-Objekt

        Raises:
            KeyError: Wenn erforderliche Spalten fehlen
        """
        # login_id kann NULL sein, daher try/except
        try:
            login_id = int(row['login_id']) if row['login_id'] else None
        except (KeyError, TypeError):
            login_id = None

        return cls(
            id=int(row['id']),
            matrikel_nr=str(row['matrikel_nr']),
            vorname=str(row['vorname']),
            nachname=str(row['nachname']),
            login_id=login_id
        )

    # ========== PRIVATE Helper Methods ==========

    def __get_display_name(self) -> str:
        """PRIVATE: Gibt Anzeigename zurÃ¼ck"""
        return self.vorname.title()

    # ========== String Representation ==========

    def __str__(self) -> str:
        return f"Student({self.matrikel_nr}, {self.get_full_name()})"

    def __repr__(self) -> str:
        return (f"Student(id={self.id}, matrikel_nr='{self.matrikel_nr}', "
                f"name='{self.get_full_name()}')")