# models/progress.py
from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass
class Progress:
    """Domain Model: Studienfortschritt

    Fast alle Methoden sind private.
    Nur to_dict(), calculate_overall_status() und get_completion_percentage() sind public.
    """
    student_id: int
    durchschnittsnote: Optional[Decimal]
    anzahl_bestandene_module: int
    anzahl_gebuchte_module: int
    offene_gebuehren: Decimal
    aktuelles_semester: float
    erwartetes_semester: float

    def __post_init__(self):
        """Typ-Konvertierung"""
        if self.durchschnittsnote is not None and not isinstance(self.durchschnittsnote, Decimal):
            self.durchschnittsnote = Decimal(str(self.durchschnittsnote))

        if not isinstance(self.offene_gebuehren, Decimal):
            self.offene_gebuehren = Decimal(str(self.offene_gebuehren))

    # ========== PUBLIC Methods (minimal!) ==========

    def calculate_overall_status(self) -> str:
        """PUBLIC: Berechnet Gesamt-Status

        Returns:
            'excellent', 'good', 'okay', 'critical'
        """
        grade_ok = self.durchschnittsnote is None or self.durchschnittsnote <= Decimal('2.5')
        time_ok = self.__is_on_schedule()
        fees_ok = not self.__has_open_fees()

        if grade_ok and time_ok and fees_ok:
            return 'excellent'
        elif grade_ok and time_ok:
            return 'good'
        elif grade_ok or time_ok:
            return 'okay'
        else:
            return 'critical'

    def get_completion_percentage(self, total_modules: int = 49) -> float:
        """PUBLIC: Berechnet Abschluss-Prozentsatz

        Args:
            total_modules: Gesamtzahl Module im Studiengang

        Returns:
            Prozentsatz (0.0 bis 100.0)
        """
        if total_modules <= 0:
            return 0.0
        return min(100.0, (self.anzahl_bestandene_module / total_modules) * 100)

    def to_dict(self) -> dict:
        """PUBLIC: Konvertiert zu Dictionary (für JSON/Templates)"""
        return {
            'student_id': self.student_id,
            'durchschnittsnote': float(self.durchschnittsnote) if self.durchschnittsnote else None,
            'durchschnittsnote_formatted': f"{self.durchschnittsnote:.2f}" if self.durchschnittsnote else "—",
            'grade_category': self.__get_grade_category(),
            'anzahl_bestandene_module': self.anzahl_bestandene_module,
            'anzahl_gebuchte_module': self.anzahl_gebuchte_module,
            'offene_gebuehren': float(self.offene_gebuehren),
            'offene_gebuehren_formatted': self.__get_open_fees_formatted(),
            'fee_category': self.__get_fee_category(),
            'aktuelles_semester': self.aktuelles_semester,
            'erwartetes_semester': self.erwartetes_semester,
            'tage_differenz': self.__calculate_days_difference(),
            'time_category': self.__get_time_category(),
            'is_on_schedule': self.__is_on_schedule(),
            'overall_status': self.calculate_overall_status(),
            'completion_percentage': self.get_completion_percentage()
        }

    # ========== PRIVATE Methods ==========

    def __get_grade_category(self) -> str:
        """PRIVATE: Kategorisiert Notendurchschnitt"""
        if self.durchschnittsnote is None:
            return 'unknown'

        if self.durchschnittsnote <= Decimal('2.0'):
            return 'fast'
        elif self.durchschnittsnote <= Decimal('3.0'):
            return 'medium'
        else:
            return 'slow'

    def __has_passing_grade(self) -> bool:
        """PRIVATE: Prüft ob Durchschnitt im grünen Bereich ist"""
        if self.durchschnittsnote is None:
            return True
        return self.durchschnittsnote <= Decimal('4.0')

    def __calculate_semester_difference(self) -> float:
        """PRIVATE: Berechnet Differenz zwischen aktuellem und erwartetem Semester"""
        return self.aktuelles_semester - self.erwartetes_semester

    def __calculate_days_difference(self) -> int:
        """PRIVATE: Berechnet Zeit-Differenz in Tagen"""
        semester_diff = self.__calculate_semester_difference()
        return int(semester_diff * 180)

    def __get_time_category(self) -> str:
        """PRIVATE: Kategorisiert Zeitstatus"""
        return 'plus' if self.__calculate_days_difference() >= 0 else 'minus'

    def __is_on_schedule(self) -> bool:
        """PRIVATE: Prüft ob Student im Zeitplan ist"""
        days_diff = self.__calculate_days_difference()
        return -30 <= days_diff <= 30

    def __has_open_fees(self) -> bool:
        """PRIVATE: Prüft ob offene Gebühren existieren"""
        return self.offene_gebuehren > Decimal('0')

    def __get_fee_category(self) -> str:
        """PRIVATE: Kategorisiert Gebührenstatus"""
        return 'zero' if not self.__has_open_fees() else 'open'

    def __get_open_fees_formatted(self) -> str:
        """PRIVATE: Gibt offene Gebühren formatiert zurück"""
        amount_str = f"{self.offene_gebuehren:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        return f"{amount_str} €"

    # ========== String Representation ==========

    def __str__(self) -> str:
        note = f"{self.durchschnittsnote:.2f}" if self.durchschnittsnote else "—"
        return f"Progress(Student {self.student_id}, Note: {note}, Sem: {self.aktuelles_semester:.1f})"

    def __repr__(self) -> str:
        return (f"Progress(student_id={self.student_id}, "
                f"note={self.durchschnittsnote}, semester={self.aktuelles_semester:.1f}, "
                f"fees={self.offene_gebuehren})")