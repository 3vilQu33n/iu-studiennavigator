# models/einschreibung.py
"""
Domain Model: Einschreibung

AGGREGATION: Student 1 → * Einschreibung
→ Eine Einschreibung gehört zu einem Student, kann aber unabhängig existieren
→ Einschreibungen bleiben nach Student-Löschung erhalten (Archiv, Buchhaltung)

KOMPOSITION: Einschreibung 1 → * Modulbuchung
→ Modulbuchungen gehören zur Einschreibung und werden mit ihr gelöscht
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from typing import Optional, Literal
import logging

logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(name)s: %(message)s')

# Type Alias
Status = Literal["aktiv", "pausiert", "exmatrikuliert"]


# ========== Custom Exceptions ==========

class EinschreibungError(Exception):
    """Allgemeine Fehlerklasse für Einschreibung-Operationen."""
    pass


class ValidationError(EinschreibungError):
    """Validierungsfehler bei Einschreibungs-Daten"""
    pass


class DatabaseError(EinschreibungError):
    """Datenbankfehler bei Einschreibungs-Operationen"""
    pass


class NotFoundError(EinschreibungError):
    """Einschreibung wurde nicht gefunden"""
    pass


# ========== Domain Model ==========

@dataclass(slots=True)
class Einschreibung:
    """Domain Model: Einschreibung

    Repräsentiert die Einschreibung eines Studierenden in einen Studiengang.

    OOP-BEZIEHUNGEN:
    - AGGREGATION zu Student (gehört zu Student, lebt aber unabhängig)
    - AGGREGATION zu Gebuehr (Einschreibung erzeugt Gebühren, die unabhängig leben)
    - KOMPOSITION zu Modulbuchung (Modulbuchungen sterben mit der Einschreibung)
    - ASSOZIATION zu Studiengang (referenziert nur)
    - ASSOZIATION zu Zeitmodell (referenziert nur)

    Attributes:
        id: Primärschlüssel (None beim Insert)
        student_id: FK zum Student (AGGREGATION)
        studiengang_id: FK zum Studiengang (ASSOZIATION)
        zeitmodell_id: FK zum Zeitmodell (ASSOZIATION)
        start_datum: Einschreibungsdatum
        exmatrikulations_datum: Datum der Exmatrikulation (None wenn aktiv/pausiert)
        status: 'aktiv' | 'pausiert' | 'exmatrikuliert'
    """
    id: Optional[int]  # beim Insert None
    student_id: int  # AGGREGATION: gehört zu Student
    studiengang_id: int  # ASSOZIATION: referenziert Studiengang
    zeitmodell_id: int  # ASSOZIATION: referenziert Zeitmodell
    start_datum: date
    exmatrikulations_datum: Optional[date] = None  # None wenn nicht exmatrikuliert
    status: Status = "aktiv"  # aktiv | pausiert | exmatrikuliert

    def __post_init__(self) -> None:
        """Validierung und Typ-Konvertierung nach Initialisierung"""
        # String → Date konvertieren
        if isinstance(self.start_datum, str):
            try:
                self.start_datum = date.fromisoformat(self.start_datum)
            except Exception as e:
                raise ValidationError(f"Ungültiges start_datum: {self.start_datum!r}") from e

        # exmatrikulations_datum konvertieren (falls vorhanden)
        if isinstance(self.exmatrikulations_datum, str):
            try:
                self.exmatrikulations_datum = date.fromisoformat(self.exmatrikulations_datum)
            except Exception as e:
                raise ValidationError(f"Ungültiges exmatrikulations_datum: {self.exmatrikulations_datum!r}") from e

        # Validierung durchführen
        self.validate()

    # ========== PUBLIC Methods ==========

    def is_active(self) -> bool:
        """PUBLIC: Prüft ob Einschreibung aktiv ist"""
        return self.status == "aktiv"

    def is_paused(self) -> bool:
        """PUBLIC: Prüft ob Einschreibung pausiert ist"""
        return self.status == "pausiert"

    def is_exmatriculated(self) -> bool:
        """PUBLIC: Prüft ob Student exmatrikuliert ist"""
        return self.status == "exmatrikuliert"

    def get_study_duration_months(self, reference_date: Optional[date] = None) -> int:
        """PUBLIC: Berechnet Studiendauer in Monaten

        Args:
            reference_date: Referenzdatum (default: heute)

        Returns:
            Anzahl Monate seit Einschreibung
        """
        ref = reference_date or date.today()
        return self.__calculate_months_since_start(ref)

    def validate(self) -> None:
        """PUBLIC: Validiert die Einschreibungs-Daten

        Wird vom Repository vor dem Insert aufgerufen.

        Raises:
            ValidationError: Wenn Daten ungültig sind
        """
        # Status validieren
        if self.status not in ("aktiv", "pausiert", "exmatrikuliert"):
            raise ValidationError(f"Ungültiger Status: {self.status}")

        # Datum validieren
        if not isinstance(self.start_datum, date):
            raise ValidationError("start_datum muss datetime.date sein")

        # IDs validieren
        for name, value in [
            ("student_id", self.student_id),
            ("studiengang_id", self.studiengang_id),
            ("zeitmodell_id", self.zeitmodell_id)
        ]:
            if not isinstance(value, int) or value <= 0:
                raise ValidationError(f"{name} muss eine positive Integer-ID sein")

    def to_dict(self) -> dict:
        """PUBLIC: Konvertiert zu Dictionary (für JSON/Templates)"""
        return {
            'id': self.id,
            'student_id': self.student_id,
            'studiengang_id': self.studiengang_id,
            'zeitmodell_id': self.zeitmodell_id,
            'start_datum': self.start_datum.isoformat(),
            'exmatrikulations_datum': self.exmatrikulations_datum.isoformat() if self.exmatrikulations_datum else None,
            'status': self.status,
            'is_active': self.is_active(),
            'is_paused': self.is_paused(),
            'study_duration_months': self.get_study_duration_months()
        }

    @classmethod
    def from_row(cls, row) -> "Einschreibung":
        """PUBLIC: Factory Method - Erstellt Einschreibung aus DB-Row

        Args:
            row: sqlite3.Row oder dict-ähnliches Objekt

        Returns:
            Einschreibung-Instanz

        Raises:
            ValidationError: Wenn Daten ungültig sind
        """
        try:
            # sqlite3.Row hat keine .get() Methode! Direkt auf Spalten zugreifen
            exmat_datum = None
            if 'exmatrikulations_datum' in row.keys() and row['exmatrikulations_datum']:
                exmat_datum = (row['exmatrikulations_datum'] if isinstance(row['exmatrikulations_datum'], date)
                               else date.fromisoformat(row['exmatrikulations_datum']))

            return cls(
                id=int(row['id']) if row['id'] is not None else None,
                student_id=int(row['student_id']),
                studiengang_id=int(row['studiengang_id']),
                zeitmodell_id=int(row['zeitmodell_id']),
                start_datum=row['start_datum'] if isinstance(row['start_datum'], date)
                else date.fromisoformat(row['start_datum']),
                exmatrikulations_datum=exmat_datum,
                status=str(row['status']) if 'status' in row.keys() else 'aktiv'
            )
        except Exception as e:
            logger.exception("Fehler beim Parsen der Einschreibungs-Row: %s", e)
            raise ValidationError("Fehler beim Parsen der Einschreibung") from e

    # ========== PRIVATE Helper Methods ==========

    def __calculate_months_since_start(self, reference_date: date) -> int:
        """PRIVATE: Berechnet Monate seit Einschreibung

        Args:
            reference_date: Referenzdatum

        Returns:
            Anzahl Monate seit Start
        """
        return max(0, (reference_date.year - self.start_datum.year) * 12
                   + (reference_date.month - self.start_datum.month))

    # ========== String Representation ==========

    def __str__(self) -> str:
        return f"Einschreibung(Student {self.student_id}, Status: {self.status})"

    def __repr__(self) -> str:
        return (f"Einschreibung(id={self.id}, student_id={self.student_id}, "
                f"studiengang_id={self.studiengang_id}, status='{self.status}')")