# models/studiengang.py
"""
Domain Model: Studiengang

ASSOZIATION: Einschreibung → Studiengang
→ Einschreibungen referenzieren einen Studiengang

KOMPOSITION: Studiengang 1 → * StudiengangModul
→ StudiengangModul gehört zum Studiengang und stirbt mit ihm
→ Definiert welche Module in welchem Semester belegt werden
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Literal

# Type Alias für Abschlussgrad
Grad = Literal["B.Sc.", "B.A.", "B.Eng.", "M.Sc.", "M.A.", "M.Eng."]


@dataclass
class Studiengang:
    """Domain Model: Studiengang

    Repräsentiert einen Studiengang mit Abschluss und Regelsemestern.

    OOP-BEZIEHUNGEN:
    - ASSOZIATION von Einschreibung (wird nur referenziert)
    - KOMPOSITION zu StudiengangModul (Zuordnung Modul ↔ Semester stirbt mit Studiengang)

    Attributes:
        id: Primärschlüssel
        name: Name des Studiengangs (z.B. "Informatik")
        grad: Abschlussgrad (B.Sc., B.A., M.Sc., etc.)
        regel_semester: Anzahl Regelsemester (meist 6 oder 7)
        beschreibung: Optionale Beschreibung des Studiengangs
    """
    id: int
    name: str
    grad: str  # B.Sc., B.A., B.Eng., M.Sc., M.A., M.Eng.
    regel_semester: int
    beschreibung: Optional[str] = None

    def __post_init__(self):
        """Validierung nach Initialisierung"""
        self.validate()

    # ========== PUBLIC Methods ==========

    def get_full_name(self) -> str:
        """PUBLIC: Gibt vollständigen Namen mit Grad zurück

        Returns:
            z.B. "Informatik (B.Sc.)"
        """
        return f"{self.name} ({self.grad})"

    def is_bachelor(self) -> bool:
        """PUBLIC: Prüft ob es sich um einen Bachelor-Studiengang handelt"""
        return self.grad.startswith("B.")

    def is_master(self) -> bool:
        """PUBLIC: Prüft ob es sich um einen Master-Studiengang handelt"""
        return self.grad.startswith("M.")

    def get_total_ects_target(self) -> int:
        """PUBLIC: Berechnet Soll-ECTS basierend auf Regelsemestern

        Returns:
            Anzahl ECTS (30 pro Semester)
        """
        return self.regel_semester * 30

    def validate(self) -> None:
        """PUBLIC: Validiert Studiengang-Daten

        Raises:
            ValueError: Wenn Daten ungültig sind
        """
        # Name validieren
        if not self.name or len(self.name.strip()) == 0:
            raise ValueError("Studiengangname darf nicht leer sein")

        # Grad validieren
        valid_grades = ["B.Sc.", "B.A.", "B.Eng.", "M.Sc.", "M.A.", "M.Eng."]
        if self.grad not in valid_grades:
            raise ValueError(f"Ungültiger Grad: {self.grad} (erlaubt: {', '.join(valid_grades)})")

        # Regelsemester validieren
        if self.regel_semester < 1 or self.regel_semester > 14:
            raise ValueError(f"Regelsemester muss zwischen 1 und 14 liegen (ist: {self.regel_semester})")

    def to_dict(self) -> dict:
        """PUBLIC: Konvertiert zu Dictionary (für JSON/Templates)"""
        return {
            'id': self.id,
            'name': self.name,
            'grad': self.grad,
            'regel_semester': self.regel_semester,
            'beschreibung': self.beschreibung,
            'full_name': self.get_full_name(),
            'is_bachelor': self.is_bachelor(),
            'is_master': self.is_master(),
            'total_ects_target': self.get_total_ects_target()
        }

    @classmethod
    def from_row(cls, row) -> "Studiengang":
        """PUBLIC: Factory Method - Erstellt Studiengang aus DB-Row"""
        # sqlite3.Row: Direkter Zugriff auf Spalten, keine .get() Methode
        return cls(
            id=int(row['id']),
            name=str(row['name']),
            grad=str(row['grad']),
            regel_semester=int(row['regel_semester']),
            beschreibung=row['beschreibung'] if 'beschreibung' in row.keys() else None
        )

    # ========== String Representation ==========

    def __str__(self) -> str:
        return f"Studiengang({self.get_full_name()}, {self.regel_semester} Semester)"

    def __repr__(self) -> str:
        return f"Studiengang(id={self.id}, name='{self.name}', grad='{self.grad}')"