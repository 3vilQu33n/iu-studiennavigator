# models/modulbuchung.py
from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class Modulbuchung:
    """Domain Model: Modulbuchung (Basisklasse)

    KOMPOSITION: Modulbuchung gehört zu einer Einschreibung
    → Wenn Einschreibung gelöscht wird, werden auch Buchungen gelöscht

    VERERBUNG: Pruefungsleistung erbt von Modulbuchung
    """
    id: int
    einschreibung_id: int  # KOMPOSITION: gehört zu Einschreibung
    modul_id: int
    buchungsdatum: Optional[date]
    status: str  # 'gebucht', 'anerkannt', 'bestanden', 'nicht_bestanden'

    def __post_init__(self):
        """Typ-Konvertierung für Datum"""
        if isinstance(self.buchungsdatum, str):
            self.buchungsdatum = date.fromisoformat(self.buchungsdatum)

    # ========== PUBLIC Methods ==========

    def is_open(self) -> bool:
        """PUBLIC: Prüft ob Buchung noch offen ist"""
        return self.status == 'gebucht'

    def is_passed(self) -> bool:
        """PUBLIC: Prüft ob Modul bestanden wurde"""
        return self.status == 'bestanden'

    def is_recognized(self) -> bool:
        """PUBLIC: Prüft ob Modul anerkannt wurde (ohne Note)"""
        return self.status == 'anerkannt'

    def to_dict(self) -> dict:
        """PUBLIC: Konvertiert zu Dictionary für JSON"""
        return {
            'id': self.id,
            'einschreibung_id': self.einschreibung_id,
            'modul_id': self.modul_id,
            'buchungsdatum': self.buchungsdatum.isoformat() if self.buchungsdatum else None,
            'status': self.status,
            'is_open': self.is_open(),
            'is_passed': self.is_passed(),
            'is_recognized': self.is_recognized()
        }

    @classmethod
    def from_row(cls, row) -> "Modulbuchung":
        """PUBLIC: Factory Method - Erstellt Buchung aus DB-Row

        Verwendet try/except für buchungsdatum da sqlite3.Row kein .get() hat.
        """
        # buchungsdatum kann NULL sein oder als String/date kommen
        try:
            if isinstance(row['buchungsdatum'], date):
                buchungsdatum = row['buchungsdatum']
            elif row['buchungsdatum']:
                buchungsdatum = date.fromisoformat(row['buchungsdatum'])
            else:
                buchungsdatum = None
        except (KeyError, TypeError, ValueError):
            buchungsdatum = None

        return cls(
            id=int(row['id']),
            einschreibung_id=int(row['einschreibung_id']),
            modul_id=int(row['modul_id']),
            buchungsdatum=buchungsdatum,
            status=str(row['status'])
        )

    # ========== String Representation ==========

    def __str__(self) -> str:
        return f"Modulbuchung(Modul {self.modul_id}, Status: {self.status})"

    def __repr__(self) -> str:
        return f"Modulbuchung(id={self.id}, modul_id={self.modul_id}, status='{self.status}')"