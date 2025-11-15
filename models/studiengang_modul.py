# models/studiengang_modul.py
"""
Domain Model: StudiengangModul (Assoziationsklasse)

KOMPOSITION: Studiengang 1 → * StudiengangModul
→ StudiengangModul gehört zum Studiengang
→ Wenn Studiengang gelöscht wird, werden auch StudiengangModule gelöscht

ASSOZIATION: Modul 1 → * StudiengangModul
→ Module werden nur referenziert und leben unabhängig
→ Ein Modul kann in mehreren Studiengängen vorkommen

ZWECK: Definiert welche Module in welchem Semester und mit welchem Pflichtgrad
       in einem Studiengang belegt werden müssen.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Literal

# Type Alias für Pflichtgrad
Pflichtgrad = Literal["Pflicht", "Wahlpflicht", "Wahl"]


@dataclass
class StudiengangModul:
    """Domain Model: StudiengangModul (Assoziationsklasse)

    Verknüpft Studiengänge mit Modulen und definiert:
    - In welchem Semester das Modul vorgesehen ist
    - Ob es Pflicht, Wahlpflicht oder Wahl ist

    OOP-BEZIEHUNGEN:
    - KOMPOSITION zu Studiengang (gehört zum Studiengang, stirbt mit ihm)
    - ASSOZIATION zu Modul (referenziert nur, Modul lebt unabhängig)

    TUTOR-FEEDBACK:
    "StudiengangModul sieht nach einer Assoziationsklasse aus"
    → Korrekt! Das ist eine Assoziationsklasse die die M:N-Beziehung
      zwischen Studiengang und Modul auflöst.

    Attributes:
        studiengang_id: FK zum Studiengang (KOMPOSITION)
        modul_id: FK zum Modul (ASSOZIATION)
        semester: Vorgesehenes Fachsemester (1-7)
        pflichtgrad: 'Pflicht' | 'Wahlpflicht' | 'Wahl'
    """
    studiengang_id: int  # KOMPOSITION: gehört zu Studiengang
    modul_id: int  # ASSOZIATION: referenziert Modul
    semester: int  # Vorgesehenes Fachsemester
    pflichtgrad: str  # 'Pflicht' | 'Wahlpflicht' | 'Wahl'

    def __post_init__(self):
        """Validierung nach Initialisierung"""
        self.validate()

    # ========== PUBLIC Methods ==========

    def is_pflicht(self) -> bool:
        """PUBLIC: Prüft ob Modul ein Pflichtmodul ist"""
        return self.pflichtgrad == "Pflicht"

    def is_wahlpflicht(self) -> bool:
        """PUBLIC: Prüft ob Modul ein Wahlpflichtmodul ist"""
        return self.pflichtgrad == "Wahlpflicht"

    def is_wahl(self) -> bool:
        """PUBLIC: Prüft ob Modul ein Wahlmodul ist"""
        return self.pflichtgrad == "Wahl"

    def is_mandatory(self) -> bool:
        """PUBLIC: Prüft ob Modul verpflichtend ist (Pflicht oder Wahlpflicht)"""
        return self.is_pflicht() or self.is_wahlpflicht()

    def validate(self) -> None:
        """PUBLIC: Validiert StudiengangModul-Daten

        Raises:
            ValueError: Wenn Daten ungültig sind
        """
        # IDs validieren
        if self.studiengang_id <= 0:
            raise ValueError("studiengang_id muss positiv sein")

        if self.modul_id <= 0:
            raise ValueError("modul_id muss positiv sein")

        # Semester validieren (1-14, da auch Master möglich)
        if self.semester < 1 or self.semester > 14:
            raise ValueError(f"Semester muss zwischen 1 und 14 liegen (ist: {self.semester})")

        # Pflichtgrad validieren
        valid_pflichtgrade = ["Pflicht", "Wahlpflicht", "Wahl"]
        if self.pflichtgrad not in valid_pflichtgrade:
            raise ValueError(
                f"Ungültiger Pflichtgrad: {self.pflichtgrad} "
                f"(erlaubt: {', '.join(valid_pflichtgrade)})"
            )

    def to_dict(self) -> dict:
        """PUBLIC: Konvertiert zu Dictionary (für JSON/Templates)"""
        return {
            'studiengang_id': self.studiengang_id,
            'modul_id': self.modul_id,
            'semester': self.semester,
            'pflichtgrad': self.pflichtgrad,
            'is_pflicht': self.is_pflicht(),
            'is_wahlpflicht': self.is_wahlpflicht(),
            'is_wahl': self.is_wahl(),
            'is_mandatory': self.is_mandatory()
        }

    @classmethod
    def from_row(cls, row) -> "StudiengangModul":
        """PUBLIC: Factory Method - Erstellt StudiengangModul aus DB-Row"""
        return cls(
            studiengang_id=int(row['studiengang_id']),
            modul_id=int(row['modul_id']),
            semester=int(row['semester']),
            pflichtgrad=str(row['pflichtgrad'])
        )

    # ========== String Representation ==========

    def __str__(self) -> str:
        return f"StudiengangModul(Studiengang {self.studiengang_id}, Modul {self.modul_id}, Sem {self.semester}, {self.pflichtgrad})"

    def __repr__(self) -> str:
        return (f"StudiengangModul(studiengang_id={self.studiengang_id}, "
                f"modul_id={self.modul_id}, semester={self.semester}, "
                f"pflichtgrad='{self.pflichtgrad}')")