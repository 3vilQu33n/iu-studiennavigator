# models/modul.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


@dataclass
class Modul:
    """Domain Model: Modul

    Repräsentiert ein Studienmodul.
    """
    id: int
    name: str
    beschreibung: str
    ects: int

    # ========== PUBLIC Methods ==========

    def to_dict(self) -> dict:
        """PUBLIC: Konvertiert zu Dictionary (für JSON/Templates)"""
        return {
            'id': self.id,
            'name': self.name,
            'beschreibung': self.beschreibung,
            'ects': self.ects
        }

    @classmethod
    def from_db_row(cls, row) -> "Modul":
        """PUBLIC: Factory Method - Erstellt Modul aus DB-Row"""
        return cls(
            id=int(row['id']),
            name=str(row['name']),
            beschreibung=str(row['beschreibung']) if row['beschreibung'] else '',
            ects=int(row['ects'])
        )

    # ========== String Representation ==========

    def __str__(self) -> str:
        return f"Modul({self.name}, {self.ects} ECTS)"

    def __repr__(self) -> str:
        return f"Modul(id={self.id}, name='{self.name}', ects={self.ects})"


@dataclass
class ModulBuchung:
    """DTO: Modul mit Buchungsstatus

    Kombiniert Modul-Daten mit Buchungsinformationen eines Studierenden.
    """
    modul: Modul
    status: Optional[str]  # 'gebucht' | 'bestanden' | None
    buchbar: bool
    buchungsdatum: Optional[str]
    note: Optional[float]
    pflichtgrad: str  # 'Pflicht' | 'Wahlpflicht' | 'Wahl'
    semester: int

    # ========== PUBLIC Methods ==========

    def is_passed(self) -> bool:
        """PUBLIC: Prüft ob Modul bestanden wurde"""
        return self.status == 'bestanden'

    def is_booked(self) -> bool:
        """PUBLIC: Prüft ob Modul gebucht wurde"""
        return self.status == 'gebucht'

    def to_dict(self) -> dict:
        """PUBLIC: Konvertiert zu Dictionary (für JSON/Templates)"""
        return {
            'modul_id': self.modul.id,
            'name': self.modul.name,
            'ects': self.modul.ects,
            'status': self.status,
            'buchbar': self.buchbar,
            'buchungsdatum': self.buchungsdatum,
            'note': self.note,
            'pflichtgrad': self.pflichtgrad,
            'semester': self.semester,
            'is_passed': self.is_passed(),
            'is_booked': self.is_booked()
        }

    # ========== String Representation ==========

    def __str__(self) -> str:
        status_str = f"[{self.status}]" if self.status else "[unbuchbar]"
        return f"ModulBuchung({self.modul.name} {status_str})"